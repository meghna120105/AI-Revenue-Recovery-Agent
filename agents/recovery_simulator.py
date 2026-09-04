"""
recovery_simulator.py
----------------------
Simulates running the AI Recovery Agent's bounded, gated recovery workflow
across a batch of failed transactions and produces:

  1. A full timestamped AUDIT TRAIL - one row per outreach action taken,
     with the action, the channel, the probability used, and a plain
     language reason.
  2. STOPPING RULES enforced (compliance-by-design), not just described:
       - "Do Not Retry Immediately" cases are never contacted at all.
       - A case stops being contacted the instant it is recovered.
       - Every case is capped at `max_attempts` touches; if still
         unrecovered it is logged as stopped-per-policy, not retried
         forever.
  3. An ESCALATION LADDER: automated action -> personalized message ->
     human agent, mirroring how a real ops team would triage.
  4. A batch-level SUMMARY of money actually recovered in the run, so the
     app shows a measured outcome across the batch rather than only a
     per-transaction recommendation.

The probability of recovery at each stage is derived from the same
transparent recovery_score / ML probability already computed upstream in
analyzer.py and recovery_model.py - so this simulation is grounded in the
same explainable signals shown elsewhere in the app, not an arbitrary
random number.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

MAX_ATTEMPTS_DEFAULT = 3

# Diminishing returns per extra touch on the SAME case (contact fatigue),
# with a small bump on the final attempt because it's a human agent.
STAGE_DECAY = [1.00, 0.55, 0.30]
FINAL_STAGE_BOOST = 0.05

ESCALATION_CHANNEL = {
    1: "Automated",
    2: "Automated / Personalized",
    3: "Human Agent",
}


def _stage_action(stage: int, recommended_action: str) -> str:
    """Map an escalation stage to a concrete action label."""
    if stage == 1:
        return recommended_action
    if stage == 2:
        if recommended_action != "Send Personalized Recovery Message":
            return "Send Personalized Recovery Message"
        return "Offer Customer Support"
    return "Escalate to Human Agent"


def run_recovery_simulation(
    df: pd.DataFrame,
    max_attempts: int = MAX_ATTEMPTS_DEFAULT,
    seed: int = 42,
    start_time: "pd.Timestamp | None" = None,
) -> tuple[pd.DataFrame, dict]:
    """
    Run the bounded recovery workflow across every Failed transaction in df.

    Parameters
    ----------
    df : pd.DataFrame
        Must already have gone through analyze_failed_transactions() and
        decide_for_dataframe() (i.e. have recovery_score, priority,
        recommended_action, action_explanation columns), and optionally
        ml_recovery_probability.
    max_attempts : int
        Hard cap on outreach touches per case (stopping rule).
    seed : int
        Random seed - same seed always reproduces the same run, so the
        "measured" numbers are stable and explainable in a demo.
    start_time : pd.Timestamp, optional
        Simulated clock start. Defaults to today at 9am.

    Returns
    -------
    (audit_trail_df, summary_dict)
    """
    failed_df = df[df["payment_status"] == "Failed"].copy()

    if start_time is None:
        start_time = pd.Timestamp.now().normalize() + pd.Timedelta(hours=9)

    # Work High Priority (and higher value) first - mirrors real triage order.
    priority_order = {"High Priority": 0, "Medium Priority": 1, "Low Priority": 2}
    failed_df["_p"] = failed_df["priority"].map(priority_order).fillna(3)
    failed_df = failed_df.sort_values(["_p", "amount"], ascending=[True, False])

    rows: list[dict] = []
    clock = start_time
    recovered_amount = 0.0
    recovered_count = 0
    stopped_immediately = 0
    attempted_count = 0

    for _, row in failed_df.iterrows():
        txn_id = row["transaction_id"]
        rng = np.random.default_rng(seed + (abs(hash(txn_id)) % 1_000_000))

        base_prob = row.get("ml_recovery_probability")
        if base_prob is None or pd.isna(base_prob):
            base_prob = (row.get("recovery_score") or 0) / 100.0
        base_prob = float(base_prob)

        # --- Stopping rule 1: policy says don't contact this case at all ---
        if row.get("recommended_action") == "Do Not Retry Immediately":
            clock += pd.Timedelta(minutes=int(rng.integers(2, 8)))
            rows.append({
                "timestamp": clock,
                "transaction_id": txn_id,
                "customer_name": row["customer_name"],
                "amount": row["amount"],
                "priority": row.get("priority") or "Low Priority",
                "stage": 0,
                "channel": "N/A",
                "action": "Stand Down (Policy Rule)",
                "probability_used": None,
                "outcome": "Stopped - Not Contacted",
                "reason": (
                    "Guardrail: too many prior retries or low recovery odds, so the "
                    "agent withholds contact instead of spamming the customer."
                ),
            })
            stopped_immediately += 1
            continue

        attempted_count += 1
        recovered_this_case = False

        for stage in range(1, max_attempts + 1):
            action = _stage_action(stage, row.get("recommended_action", "Send Payment Reminder"))
            decay = STAGE_DECAY[min(stage - 1, len(STAGE_DECAY) - 1)]
            boost = FINAL_STAGE_BOOST if stage == max_attempts else 0.0
            prob = float(min(0.95, base_prob * decay + boost))

            roll = rng.random()
            recovered = roll < prob

            # Compliance cooldown between touches (no same-day re-spam).
            clock += pd.Timedelta(hours=int(rng.integers(20, 48)))

            if recovered:
                outcome = "Recovered"
            elif stage < max_attempts:
                outcome = "No Response - Escalating"
            else:
                outcome = "Stopped - Max Attempts (Policy Rule)"

            rows.append({
                "timestamp": clock,
                "transaction_id": txn_id,
                "customer_name": row["customer_name"],
                "amount": row["amount"],
                "priority": row.get("priority") or "Medium Priority",
                "stage": stage,
                "channel": ESCALATION_CHANNEL.get(stage, "Human Agent"),
                "action": action,
                "probability_used": round(prob, 3),
                "outcome": outcome,
                "reason": row.get("action_explanation", ""),
            })

            if recovered:
                recovered_this_case = True
                recovered_amount += float(row["amount"])
                recovered_count += 1
                break  # Stopping rule 2: never re-contact a recovered case.

    audit_df = pd.DataFrame(rows)
    if not audit_df.empty:
        audit_df = audit_df.sort_values("timestamp").reset_index(drop=True)

    total_failed_value = float(failed_df["amount"].sum())
    human_escalations = int((audit_df["channel"] == "Human Agent").sum()) if len(audit_df) else 0

    summary = {
        "total_failed_cases": int(len(failed_df)),
        "cases_stopped_immediately": int(stopped_immediately),
        "cases_attempted": int(attempted_count),
        "cases_recovered": int(recovered_count),
        "recovered_amount": float(recovered_amount),
        "total_failed_value": total_failed_value,
        "batch_recovery_rate": round((recovered_count / attempted_count * 100), 1) if attempted_count else 0.0,
        "value_recovery_rate": round((recovered_amount / total_failed_value * 100), 1) if total_failed_value else 0.0,
        "total_outreach_actions": int(len(audit_df)),
        "cases_escalated_to_human": human_escalations,
        "avg_actions_per_case": round(len(audit_df) / attempted_count, 2) if attempted_count else 0.0,
    }
    return audit_df, summary
