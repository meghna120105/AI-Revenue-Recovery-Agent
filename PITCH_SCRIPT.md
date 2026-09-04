# 5-Minute Demo Script — AI Revenue Recovery Agent

*Razorpay AI Buildathon 2026 — Track 3: AI Revenue Recovery*

---

## Before you start (30 seconds of setup, not part of the 5 minutes)

- Open the app, go to **🧪 Recovery Simulator** once and let it run so the
  numbers are "warm" and cached — you don't want your first live click to
  be a slow spinner.
- Reset all sidebar filters to "All" so you're presenting the full dataset
  (1,500 transactions), not a narrowed-down view.
- Have one specific transaction in mind for the Transaction Explorer step
  (any High-Priority one — sort by recovery score, pick the top row).
- Know the track's bar by heart, because you're going to answer it on
  screen: *"Don't just identify the problem. Show measured money
  recovered across a batch, with compliant escalation, stopping rules,
  and an audit trail."*

---

## [0:00–0:30] Hook + Problem

"Every business running online payments loses revenue not because
customers don't want to pay — a network blip, an expired card,
insufficient funds — these get treated identically today: ignored, or
hit with the same generic retry. That's revenue leakage that's
completely avoidable, and it happens the same way whether the payment
is a food delivery order or a SaaS subscription renewal.

We built the **AI Revenue Recovery Agent**: it scores every failed
payment, decides if and how it's worth recovering, runs a bounded
outreach workflow, and proves — with numbers, not a demo trick — how
much of that revenue it actually got back."

---

## [0:30–1:00] Command Center (live demo)

*[Land on 🎯 Command Center]*

"This is running on a synthetic dataset modeled after a real
multi-merchant platform — 1,500 transactions over 6 months, across
five verticals: e-commerce, food delivery, ride-hailing, SaaS, and
travel — including a simulated festive-sale traffic spike, because
that's when payment failures actually cluster in the real world.

At a glance: total transactions, failed revenue, and this headline
number — **potential recoverable revenue** — which isn't a guess, it's
the output of an explainable scoring pipeline underneath."

---

## [1:00–1:45] The AI pipeline (Transaction Explorer)

*[Click 🔎 Transaction Explorer, select your pre-picked transaction]*

"One failed transaction. Three things happen automatically:

First, a transparent **Recovery Priority Score** — amount, how
recoverable this failure reason typically is, customer segment and
history, retry count. You can see exactly why this scored what it did.

Second, a **RandomForest model** trained on historical outcomes gives
an actual recovery probability — not a guess, a learned number.

Third, the **Decision Agent** combines both and recommends a specific
action with a one-line justification. Nothing black-box."

*[Click 'Generate AI Recovery Message']*

"And here's a personalized outreach message, generated live — powered
by a free-tier LLM, with an automatic template fallback if the API
call ever fails, so this never blocks."

---

## [1:45–2:15] AI Recovery Center

*[Click 🤖 AI Recovery Center]*

"This is the ops view — every High-Priority case ranked, and one click
to batch-generate outreach messages for the top of the queue. This is
what a recovery team would actually open every morning."

---

## [2:15–4:00] Recovery Simulator — the centerpiece

*[Click 🧪 Recovery Simulator]*

"This page exists to answer the bar directly: **measured money
recovered across a batch, with compliant escalation, stopping rules,
and an audit trail.**

This isn't a mockup — it actually runs the recovery workflow across
every failed transaction in the dataset. Watch the escalation ladder:
stage one is an automated action, stage two personalizes the message,
and only the final stage escalates to a human agent — nothing skips
straight to a person.

Here's the measured outcome of this run: **[read the 'Amount
Recovered' KPI card out loud]** recovered out of **[total at risk]**,
across **[cases recovered]** of **[cases attempted]** cases — that's a
**[X]% recovery rate**, plus **[Y]** cases escalated to a human, and
**[Z]** cases the agent never even contacted because policy said not
to.

That last number matters as much as the recovery number — this agent
is bounded. It won't spam a customer forever: capped attempts, 20–48
hour cooldowns between touches, and it stops the instant a case is
recovered or flagged 'do not retry.'"

*[Scroll to the funnel chart]*

"This funnel shows exactly where cases drop off — failed, attempted,
recovered — and the audit trail below is every single action the agent
took, timestamped, with the probability it used and the outcome —
fully exportable as CSV. That's the full loop: detect, decide, act,
prove it."

*[Optional, if you have 15 extra seconds: click 'Re-run with new random seed']*

"And it's reproducible — same inputs, same measured result, every
time, unless we deliberately re-roll it."

---

## [4:00–4:30] Analytics

*[Click 📈 Analytics]*

"Behind all of this is a real trained model, not just rules — feature
importances, and proper train/test evaluation: accuracy, precision,
recall, ROC-AUC, all logged when you retrain it."

---

## [4:30–5:00] Close

"To be clear — this runs on fully synthetic, clearly-labeled demo data
and isn't connected to Razorpay's live systems. But the architecture
is built to plug in: swap the synthetic feed for a real failed-payment
webhook stream, and the same pipeline — score, decide, escalate, stop,
prove — works unchanged.

The core idea: **stop treating every failed payment the same way, and
stop guessing at how much you recovered.** Score it, act on it within
hard limits, and measure it. Thank you."

---

## If you only have 3 minutes (cut-down version)

Skip Transaction Explorer and AI Recovery Center. Run:
**Hook (20s) → Command Center (20s) → Recovery Simulator (2:00) →
Close (20s)**. The Simulator is the single strongest section — if
you're cutting anything, protect that.

---

### Anticipated Q&A

**Q: Is this connected to real Razorpay data?**
A: No — synthetic demo data only, clearly labeled throughout the app
(sidebar badge, footer disclaimer). The architecture is designed so a
real payment-failure feed could be plugged in later without changing
the pipeline.

**Q: How do you know the "amount recovered" number is real and not
just made up?**
A: It's the output of an actual simulated run, not a hardcoded figure —
click "Re-run with new random seed" and the numbers change because a
new batch of outcomes gets simulated. Each outcome is drawn from the
same recovery-probability signal shown elsewhere in the app (the
priority score / ML probability), so it's grounded, not arbitrary.

**Q: What stops this from just re-contacting the same customer forever?**
A: Three hard rules, enforced in code, not just described: a max
attempt cap per case, a cooldown window between attempts, and an
immediate stop the moment a case is recovered or flagged "do not
retry." All visible in the audit trail.

**Q: Why RandomForest and not a deep learning model?**
A: Interpretability. Feature importances let us explain *why* the
model predicts a given recovery probability — important for a
finance-adjacent decision, and appropriate given the dataset size.

**Q: What happens if the LLM API is down or the key is missing?**
A: The message generator automatically falls back to a template engine
that still varies wording per transaction — the app never breaks or
blocks on the LLM call. It supports three interchangeable providers
(Groq, Gemini, OpenAI) so a missing or rate-limited key on one doesn't
take down the demo.

**Q: How is the priority score different from the ML model?**
A: The priority score answers "how much is this worth recovering" (a
transparent business formula). The ML model answers "how likely is a
retry to actually work" (a learned probability from historical
outcomes). The Decision Agent combines both, and the Simulator uses
that same combined signal to drive its outcomes.
