"""
app.py
------
AI Revenue Recovery Agent - Streamlit Command Center

Entry point for the application. Run with:
    streamlit run app.py
"""

import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from agents.analyzer import analyze_failed_transactions
from agents.decision_agent import decide_for_dataframe
from agents.message_generator import generate_recovery_message
from agents.recovery_simulator import run_recovery_simulation
from models.recovery_model import RecoveryModel
from utils.data_processor import apply_filters, compute_summary_metrics, load_data

# --------------------------------------------------------------------------
# Page config
# --------------------------------------------------------------------------

st.set_page_config(
    page_title="Revenue Recovery Command Center",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

PLOTLY_TEMPLATE = "plotly_dark"
ACCENT = "#8b5cf6"       # violet
ACCENT_2 = "#22d3ee"     # cyan
ACCENT_3 = "#f472b6"     # pink
GOOD = "#34d399"         # green
WARN = "#fbbf24"         # amber
BAD = "#fb7185"          # red
COLOR_SEQ = [ACCENT, ACCENT_2, ACCENT_3, GOOD, WARN, "#818cf8", "#facc15"]

# --------------------------------------------------------------------------
# Global styling
# --------------------------------------------------------------------------

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&family=Inter:wght@400;500;600&display=swap');

        html, body, [class*="css"]  {
            font-family: 'Inter', sans-serif;
        }
        h1, h2, h3, .hero-title {
            font-family: 'Sora', sans-serif !important;
        }

        .stApp {
            background:
                radial-gradient(circle at 10% 0%, rgba(139,92,246,0.14), transparent 45%),
                radial-gradient(circle at 90% 10%, rgba(34,211,238,0.10), transparent 40%),
                #0b0f1a;
        }

        section[data-testid="stSidebar"] {
            background: #0e1322;
            border-right: 1px solid rgba(255,255,255,0.06);
        }

        /* ---- Hero banner ---- */
        .hero-banner {
            background: linear-gradient(120deg, rgba(139,92,246,0.35), rgba(34,211,238,0.18) 55%, rgba(244,114,182,0.20));
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 18px;
            padding: 26px 30px;
            margin-bottom: 22px;
            position: relative;
            overflow: hidden;
        }
        .hero-eyebrow {
            text-transform: uppercase;
            letter-spacing: 0.14em;
            font-size: 0.72rem;
            font-weight: 600;
            color: #c4b5fd;
            margin-bottom: 6px;
        }
        .hero-title {
            font-size: 1.9rem;
            font-weight: 800;
            color: #f8f7ff;
            margin: 0 0 4px 0;
        }
        .hero-sub {
            color: #b9bfd6;
            font-size: 0.95rem;
            max-width: 700px;
        }
        .hero-big-number {
            font-size: 2.6rem;
            font-weight: 800;
            background: linear-gradient(90deg, #a78bfa, #67e8f9);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        /* ---- KPI cards ---- */
        .kpi-card {
            background: rgba(255,255,255,0.035);
            border: 1px solid rgba(255,255,255,0.08);
            border-left: 3px solid var(--accent, #8b5cf6);
            border-radius: 14px;
            padding: 14px 16px 12px 16px;
            height: 100%;
        }
        .kpi-icon { font-size: 1.1rem; opacity: 0.85; }
        .kpi-label {
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 0.68rem;
            font-weight: 600;
            color: #9aa1bb;
            margin-top: 4px;
        }
        .kpi-value {
            font-size: 1.55rem;
            font-weight: 700;
            color: #f4f4fb;
            margin-top: 2px;
        }
        .kpi-sub {
            font-size: 0.74rem;
            color: #8b91ab;
            margin-top: 2px;
        }

        /* ---- Panels / explain boxes ---- */
        .glass-panel {
            background: rgba(255,255,255,0.035);
            border: 1px solid rgba(255,255,255,0.08);
            border-left: 4px solid #8b5cf6;
            padding: 14px 18px;
            border-radius: 10px;
            font-size: 0.92rem;
            color: #d9dcee;
            margin-bottom: 10px;
        }
        .glass-panel.action { border-left-color: #22d3ee; }
        .glass-panel.stop { border-left-color: #fb7185; }

        /* ---- Badges / pills ---- */
        .badge {
            display: inline-block;
            padding: 3px 11px;
            border-radius: 999px;
            font-size: 0.72rem;
            font-weight: 600;
            letter-spacing: 0.02em;
        }
        .badge-yellow { background: rgba(251,191,36,0.15); color: #fbbf24; border: 1px solid rgba(251,191,36,0.35);}
        .badge-violet { background: rgba(139,92,246,0.18); color: #c4b5fd; border: 1px solid rgba(139,92,246,0.4);}
        .badge-green { background: rgba(52,211,153,0.15); color: #34d399; border: 1px solid rgba(52,211,153,0.35);}
        .badge-red { background: rgba(251,113,133,0.15); color: #fb7185; border: 1px solid rgba(251,113,133,0.35);}
        .badge-cyan { background: rgba(34,211,238,0.15); color: #22d3ee; border: 1px solid rgba(34,211,238,0.35);}

        .priority-high { color: #fb7185; font-weight: 700; }
        .priority-medium { color: #fbbf24; font-weight: 700; }
        .priority-low { color: #34d399; font-weight: 700; }

        div[data-testid="stMetric"] {
            background: rgba(255,255,255,0.035);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 12px 16px 4px 16px;
        }

        .section-label {
            text-transform: uppercase;
            letter-spacing: 0.1em;
            font-size: 0.75rem;
            font-weight: 700;
            color: #a1a8c3;
            margin: 22px 0 8px 0;
        }

        hr { border-color: rgba(255,255,255,0.08); }
    </style>
    """,
    unsafe_allow_html=True,
)

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "payments.csv")


# --------------------------------------------------------------------------
# Cached data loading + analysis pipeline
# --------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def get_analyzed_data(path: str) -> pd.DataFrame:
    """Load raw data, then run it through the rule-based analyzer + decision agent."""
    df = load_data(path)
    df = analyze_failed_transactions(df)

    recovery_probabilities = None
    if RecoveryModel.model_exists():
        try:
            model = RecoveryModel.load()
            failed_mask = df["payment_status"] == "Failed"
            probs = model.predict_proba(df.loc[failed_mask])
            recovery_probabilities = pd.Series(probs, index=df.loc[failed_mask].index)
        except Exception:
            recovery_probabilities = None

    df = decide_for_dataframe(df, recovery_probabilities)

    if recovery_probabilities is not None:
        df["ml_recovery_probability"] = recovery_probabilities.reindex(df.index)
    else:
        df["ml_recovery_probability"] = None

    return df


@st.cache_data(show_spinner=False)
def get_simulation(df: pd.DataFrame, max_attempts: int, seed: int):
    return run_recovery_simulation(df, max_attempts=max_attempts, seed=seed)


# --------------------------------------------------------------------------
# Small UI helpers
# --------------------------------------------------------------------------

def priority_badge(priority: str) -> str:
    if priority == "High Priority":
        return f'<span class="priority-high">🔴 {priority}</span>'
    elif priority == "Medium Priority":
        return f'<span class="priority-medium">🟠 {priority}</span>'
    elif priority == "Low Priority":
        return f'<span class="priority-low">🟢 {priority}</span>'
    return priority or "-"


def format_inr(value: float) -> str:
    return f"₹{value:,.0f}"


def kpi_card(col, icon: str, label: str, value: str, sub: str = "", accent: str = ACCENT):
    with col:
        st.markdown(
            f"""
            <div class="kpi-card" style="--accent:{accent}">
                <div class="kpi-icon">{icon}</div>
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
                <div class="kpi-sub">{sub}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def outcome_badge(outcome: str) -> str:
    if outcome == "Recovered":
        return '<span class="badge badge-green">✅ Recovered</span>'
    if "Escalating" in outcome:
        return '<span class="badge badge-cyan">↗ Escalating</span>'
    if "Not Contacted" in outcome:
        return '<span class="badge badge-yellow">⏸ Not Contacted</span>'
    if "Stopped" in outcome:
        return '<span class="badge badge-red">🛑 Stopped</span>'
    return f'<span class="badge badge-violet">{outcome}</span>'


def apply_dark_layout(fig, title=None, height=None):
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#d9dcee"),
        title=dict(text=title, font=dict(family="Sora, sans-serif", size=15)) if title else None,
        margin=dict(t=50, l=10, r=10, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    if height:
        fig.update_layout(height=height)
    return fig


# --------------------------------------------------------------------------
# Load data (with a friendly error if missing)
# --------------------------------------------------------------------------

if not os.path.exists(DATA_PATH):
    st.error(
        "No dataset found at data/payments.csv.\n\n"
        "Run `python data/generate_data.py` from the project root to generate the synthetic demo dataset."
    )
    st.stop()

df = get_analyzed_data(DATA_PATH)
model_ready = RecoveryModel.model_exists()

# --------------------------------------------------------------------------
# Sidebar navigation + filters
# --------------------------------------------------------------------------

st.sidebar.markdown(
    """
    <div style="padding: 4px 0 14px 0;">
        <div style="font-family:'Sora',sans-serif; font-size:1.15rem; font-weight:800; color:#f4f4fb;">
            🧠 Revenue Recovery
        </div>
        <div style="font-size:0.78rem; color:#9aa1bb;">AI Agent Command Center</div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    '<span class="badge badge-yellow">SYNTHETIC DEMO DATA</span> '
    '<span class="badge badge-violet">RAZORPAY BUILDATHON 2026</span>',
    unsafe_allow_html=True,
)
st.sidebar.markdown("<br>", unsafe_allow_html=True)

page = st.sidebar.radio(
    "Navigate",
    [
        "🎯 Command Center",
        "🔎 Transaction Explorer",
        "🤖 AI Recovery Center",
        "🧪 Recovery Simulator",
        "📈 Analytics",
    ],
)

st.sidebar.markdown("---")
st.sidebar.subheader("Filters")

min_date = df["transaction_date"].min().date()
max_date = df["transaction_date"].max().date()
date_range = st.sidebar.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

status_options = ["All"] + sorted(df["payment_status"].unique().tolist())
status_sel = st.sidebar.multiselect("Payment status", status_options, default=["All"])

method_options = ["All"] + sorted(df["payment_method"].unique().tolist())
method_sel = st.sidebar.multiselect("Payment method", method_options, default=["All"])

reason_options = ["All"] + sorted(df["failure_reason"].dropna().unique().tolist())
reason_sel = st.sidebar.multiselect("Failure reason", reason_options, default=["All"])

priority_options = ["All"] + sorted(df["priority"].dropna().unique().tolist())
priority_sel = st.sidebar.multiselect("Priority", priority_options, default=["All"])

segment_options = ["All"] + sorted(df["customer_segment"].unique().tolist())
segment_sel = st.sidebar.multiselect("Customer segment", segment_options, default=["All"])

category_sel, city_sel = ["All"], ["All"]
if "merchant_category" in df.columns:
    category_options = ["All"] + sorted(df["merchant_category"].unique().tolist())
    category_sel = st.sidebar.multiselect("Merchant category", category_options, default=["All"])
if "city" in df.columns:
    city_options = ["All"] + sorted(df["city"].unique().tolist())
    city_sel = st.sidebar.multiselect("City", city_options, default=["All"])

filtered_df = apply_filters(
    df,
    date_range=date_range if isinstance(date_range, tuple) else None,
    payment_status=status_sel,
    payment_method=method_sel,
    failure_reason=reason_sel,
    priority=priority_sel,
    customer_segment=segment_sel,
    merchant_category=category_sel,
    city=city_sel,
)

st.sidebar.markdown("---")
if model_ready:
    st.sidebar.markdown('<span class="badge badge-green">✅ ML Model Loaded</span>', unsafe_allow_html=True)
else:
    st.sidebar.warning(
        "ML recovery model not trained yet.\n\nRun `python models/train_model.py` to enable "
        "ML-based recovery probability. The app works fine without it (rule-based scoring only)."
    )

# ==========================================================================
# PAGE: COMMAND CENTER
# ==========================================================================

if page == "🎯 Command Center":
    metrics = compute_summary_metrics(filtered_df)

    st.markdown(
        f"""
        <div class="hero-banner">
            <div class="hero-eyebrow">AI REVENUE RECOVERY AGENT · LIVE OVERVIEW</div>
            <div class="hero-title">Revenue Recovery Command Center</div>
            <div class="hero-sub">
                Every failed payment triaged, explained, and routed to a bounded recovery action —
                nothing black-box, every score is auditable.
            </div>
            <div style="margin-top:14px;">
                <span class="hero-big-number">{format_inr(metrics['potential_recoverable_revenue'])}</span>
                <span style="color:#b9bfd6; font-size:0.9rem;"> &nbsp;estimated recoverable across
                {metrics['failed_transactions']:,} failed transactions</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    kpi_card(c1, "💳", "Total Transactions", f"{metrics['total_transactions']:,}", accent=ACCENT_2)
    kpi_card(c2, "✅", "Successful Payments", f"{metrics['successful_transactions']:,}", accent=GOOD)
    kpi_card(c3, "⚠️", "Failed Payments", f"{metrics['failed_transactions']:,}", accent=BAD)
    kpi_card(c4, "💰", "Failed Revenue", format_inr(metrics["failed_revenue"]), accent=WARN)
    kpi_card(c5, "📈", "Recovery Rate", f"{metrics['recovery_rate']}%",
             sub="of failed revenue estimated recoverable", accent=ACCENT)

    st.markdown('<div class="section-label">Payment Performance</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        status_counts = filtered_df["payment_status"].value_counts().reset_index()
        status_counts.columns = ["status", "count"]
        fig = px.pie(status_counts, names="status", values="count", hole=0.55,
                     color="status", color_discrete_map={"Success": GOOD, "Failed": BAD})
        apply_dark_layout(fig, "Payment Success vs Failure")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        failed_only = filtered_df[filtered_df["payment_status"] == "Failed"]
        reason_counts = failed_only["failure_reason"].value_counts().reset_index()
        reason_counts.columns = ["failure_reason", "count"]
        fig = px.bar(reason_counts, x="failure_reason", y="count",
                     color="count", color_continuous_scale=["#3b1f6e", ACCENT_3])
        fig.update_layout(xaxis_title="", yaxis_title="Count")
        apply_dark_layout(fig, "Failure Reasons")
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        rev_by_method = filtered_df.groupby("payment_method")["amount"].sum().reset_index()
        fig = px.bar(rev_by_method.sort_values("amount", ascending=False), x="payment_method", y="amount",
                     color="amount", color_continuous_scale=["#134e4a", ACCENT_2])
        fig.update_layout(xaxis_title="", yaxis_title="Revenue (₹)")
        apply_dark_layout(fig, "Revenue by Payment Method")
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        priority_counts = failed_only["priority"].value_counts().reset_index()
        priority_counts.columns = ["priority", "count"]
        fig = px.pie(priority_counts, names="priority", values="count", hole=0.55,
                     color="priority",
                     color_discrete_map={"High Priority": BAD, "Medium Priority": WARN, "Low Priority": GOOD})
        apply_dark_layout(fig, "Recovery Priority Distribution")
        st.plotly_chart(fig, use_container_width=True)

    seg_col, cat_col = st.columns(2)
    with seg_col:
        seg_failed_rev = failed_only.groupby("customer_segment")["amount"].sum().reset_index()
        fig = px.bar(seg_failed_rev.sort_values("amount", ascending=False), x="customer_segment", y="amount",
                     color="amount", color_continuous_scale=["#5b1a3a", ACCENT_3])
        fig.update_layout(xaxis_title="", yaxis_title="Failed Revenue (₹)")
        apply_dark_layout(fig, "Failed Revenue by Customer Segment")
        st.plotly_chart(fig, use_container_width=True)

    with cat_col:
        if "merchant_category" in failed_only.columns:
            cat_failed_rev = failed_only.groupby("merchant_category")["amount"].sum().reset_index()
            fig = px.bar(cat_failed_rev.sort_values("amount", ascending=False), x="merchant_category", y="amount",
                         color="amount", color_continuous_scale=["#0f3d3e", ACCENT_2])
            fig.update_layout(xaxis_title="", yaxis_title="Failed Revenue (₹)")
            apply_dark_layout(fig, "Failed Revenue by Merchant Category")
            st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-label">Failed Transactions</div>', unsafe_allow_html=True)
    display_cols = ["transaction_id", "customer_name", "amount", "payment_method", "failure_reason",
                     "priority", "recovery_score", "recommended_action"]
    st.dataframe(
        failed_only[display_cols].sort_values("recovery_score", ascending=False),
        use_container_width=True, hide_index=True,
    )

# ==========================================================================
# PAGE: TRANSACTION EXPLORER
# ==========================================================================

elif page == "🔎 Transaction Explorer":
    st.markdown(
        """
        <div class="hero-banner">
            <div class="hero-eyebrow">DRILL-DOWN</div>
            <div class="hero-title">Transaction Explorer</div>
            <div class="hero-sub">Browse every transaction and drill into a specific one for full AI analysis.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    view_cols = ["transaction_id", "customer_name", "amount", "payment_method", "payment_status",
                 "failure_reason", "priority", "recovery_score", "recommended_action"]
    st.dataframe(filtered_df[view_cols], use_container_width=True, hide_index=True, height=350)

    st.markdown('<div class="section-label">Transaction Detail</div>', unsafe_allow_html=True)

    failed_ids = filtered_df.loc[filtered_df["payment_status"] == "Failed", "transaction_id"].tolist()
    if not failed_ids:
        st.info("No failed transactions in the current filter selection.")
    else:
        selected_id = st.selectbox("Select a failed transaction to inspect", failed_ids)
        row = filtered_df.loc[filtered_df["transaction_id"] == selected_id].iloc[0]

        colA, colB = st.columns(2)
        with colA:
            st.markdown("#### 👤 Customer Information")
            st.write(f"**Name:** {row['customer_name']}")
            st.write(f"**Customer ID:** {row['customer_id']}")
            st.write(f"**Segment:** {row['customer_segment']}")
            st.write(f"**History:** {row['customer_history']}")

        with colB:
            st.markdown("#### 💳 Transaction Information")
            st.write(f"**Transaction ID:** {row['transaction_id']}")
            st.write(f"**Amount:** {format_inr(row['amount'])} ({row['currency']})")
            st.write(f"**Payment Method:** {row['payment_method']}")
            st.write(f"**Date:** {row['transaction_date']}")
            st.write(f"**Retry Count:** {row['retry_count']}")

        st.markdown("#### 🧠 Failure & Recovery Analysis")
        st.write(f"**Failure Reason:** {row['failure_reason']}")
        st.markdown(f"**Priority:** {priority_badge(row['priority'])}", unsafe_allow_html=True)
        st.write(f"**Recovery Score:** {row['recovery_score']} / 100")
        if pd.notna(row.get("ml_recovery_probability")):
            st.write(f"**ML Recovery Probability:** {row['ml_recovery_probability'] * 100:.1f}%")

        st.markdown(f'<div class="glass-panel">🧠 <b>AI Analysis:</b> {row["priority_explanation"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="glass-panel action">🤖 <b>Recommended Action — {row["recommended_action"]}:</b> {row["action_explanation"]}</div>', unsafe_allow_html=True)

        st.markdown("#### ✨ Recovery Message")
        msg_key = f"msg_{selected_id}"
        if st.button("✨ Generate AI Recovery Message", key=f"gen_{selected_id}"):
            with st.spinner("Generating personalized message..."):
                result = generate_recovery_message(
                    customer_name=row["customer_name"],
                    amount=row["amount"],
                    failure_reason=row["failure_reason"],
                    action=row["recommended_action"],
                    currency=row["currency"],
                    segment=row["customer_segment"],
                )
                st.session_state[msg_key] = result

        if msg_key in st.session_state:
            result = st.session_state[msg_key]
            provider_names = {"groq": "Groq (Llama)", "gemini": "Gemini", "openai": "OpenAI"}
            provider_label = provider_names.get(result.get("provider"), "LLM")
            mode_label = f"🧠 Generated by {provider_label}" if result["mode"] == "llm" else "📋 Generated from template (fallback mode)"
            st.success(result["message"])
            st.caption(mode_label)
            if result.get("error"):
                st.caption(f"LLM call failed, used fallback. Details: {result['error']}")

# ==========================================================================
# PAGE: AI RECOVERY CENTER
# ==========================================================================

elif page == "🤖 AI Recovery Center":
    st.markdown(
        """
        <div class="hero-banner">
            <div class="hero-eyebrow">TRIAGE & OUTREACH</div>
            <div class="hero-title">AI Recovery Center</div>
            <div class="hero-sub">High-priority cases and AI-recommended recovery actions, ready for outreach.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    failed_df = filtered_df[filtered_df["payment_status"] == "Failed"].copy()
    high_priority = failed_df[failed_df["priority"] == "High Priority"].sort_values("recovery_score", ascending=False)

    m1, m2, m3 = st.columns(3)
    kpi_card(m1, "🔴", "High-Priority Cases", f"{len(high_priority):,}", accent=BAD)
    kpi_card(m2, "💰", "High-Priority Recoverable Value", format_inr(high_priority["amount"].sum()), accent=WARN)
    kpi_card(m3, "🎯", "Avg. Recovery Score",
             f"{high_priority['recovery_score'].mean():.1f}" if len(high_priority) else "-", accent=ACCENT)

    st.markdown('<div class="section-label">High-Priority Recovery Cases</div>', unsafe_allow_html=True)
    st.dataframe(
        high_priority[["transaction_id", "customer_name", "amount", "failure_reason",
                        "recovery_score", "recommended_action"]],
        use_container_width=True, hide_index=True,
    )

    st.markdown('<div class="section-label">AI Recommendations Breakdown</div>', unsafe_allow_html=True)
    action_counts = failed_df["recommended_action"].value_counts().reset_index()
    action_counts.columns = ["recommended_action", "count"]
    fig = px.bar(action_counts.sort_values("count", ascending=True), x="count", y="recommended_action",
                 orientation="h", color="count", color_continuous_scale=["#3b1f6e", ACCENT])
    fig.update_layout(yaxis_title="", xaxis_title="Number of transactions")
    apply_dark_layout(fig, "Recommended Actions Across All Failed Transactions")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-label">Batch Message Generation</div>', unsafe_allow_html=True)
    st.caption("Generate recovery messages for the top High-Priority cases in one click.")

    n_available = len(high_priority)

    if n_available == 0:
        st.info("No High-Priority cases in the current filter selection — nothing to generate messages for.")
        top_n = 0
    elif n_available == 1:
        st.caption("Only 1 High-Priority case in the current filter selection.")
        top_n = 1
    else:
        slider_max = min(10, n_available)
        default_n = min(3, slider_max)
        top_n = st.slider("How many top cases to generate messages for?", 1, slider_max, default_n)

    if top_n > 0 and st.button("Generate messages for top cases"):
        top_cases = high_priority.head(top_n)
        for _, row in top_cases.iterrows():
            with st.spinner(f"Generating message for {row['customer_name']}..."):
                result = generate_recovery_message(
                    customer_name=row["customer_name"],
                    amount=row["amount"],
                    failure_reason=row["failure_reason"],
                    action=row["recommended_action"],
                    currency=row["currency"],
                    segment=row["customer_segment"],
                )
            with st.expander(f"{row['customer_name']} — {row['transaction_id']} ({format_inr(row['amount'])})"):
                st.write(f"**Action:** {row['recommended_action']}")
                st.info(result["message"])
                provider_names = {"groq": "Groq (Llama)", "gemini": "Gemini", "openai": "OpenAI"}
                provider_label = provider_names.get(result.get("provider"), "LLM")
                st.caption(f"🧠 {provider_label}-generated" if result["mode"] == "llm" else "📋 Template fallback")

# ==========================================================================
# PAGE: RECOVERY SIMULATOR  (new)
# ==========================================================================

elif page == "🧪 Recovery Simulator":
    st.markdown(
        """
        <div class="hero-banner">
            <div class="hero-eyebrow">BATCH RUN · MEASURED OUTCOME</div>
            <div class="hero-title">Recovery Simulator & Audit Trail</div>
            <div class="hero-sub">
                Runs the AI agent's bounded recovery workflow across the whole batch of failed transactions —
                with an escalation ladder (automated → personalized → human agent), hard stopping rules,
                and a full timestamped audit trail. Every ₹ below is a measured outcome of the simulated run,
                not a guess.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    ctrl1, ctrl2, ctrl3 = st.columns([1.2, 1, 1])
    with ctrl1:
        max_attempts = st.slider("Max outreach attempts per case (stopping rule)", 1, 5, 3)
    with ctrl2:
        if "sim_seed" not in st.session_state:
            st.session_state["sim_seed"] = 42
        st.metric("Simulation seed", st.session_state["sim_seed"])
    with ctrl3:
        st.write("")
        st.write("")
        if st.button("🔁 Re-run with new random seed"):
            st.session_state["sim_seed"] += 1

    with st.spinner("Running bounded recovery workflow across the batch..."):
        audit_df, summary = get_simulation(filtered_df, max_attempts, st.session_state["sim_seed"])

    st.markdown('<div class="section-label">Measured Outcome — This Run</div>', unsafe_allow_html=True)
    r1, r2, r3, r4, r5 = st.columns(5)
    kpi_card(r1, "💰", "Amount Recovered", format_inr(summary["recovered_amount"]),
             sub=f"of {format_inr(summary['total_failed_value'])} at risk", accent=GOOD)
    kpi_card(r2, "✅", "Cases Recovered", f"{summary['cases_recovered']:,} / {summary['cases_attempted']:,}",
             sub=f"{summary['batch_recovery_rate']}% of attempted cases", accent=ACCENT)
    kpi_card(r3, "🧑‍💼", "Escalated to Human", f"{summary['cases_escalated_to_human']:,}",
             sub="handed off per escalation ladder", accent=ACCENT_3)
    kpi_card(r4, "🛑", "Stopped by Policy", f"{summary['cases_stopped_immediately']:,}",
             sub="never contacted — guardrail", accent=BAD)
    kpi_card(r5, "📜", "Outreach Actions Logged", f"{summary['total_outreach_actions']:,}",
             sub=f"avg {summary['avg_actions_per_case']} per case", accent=ACCENT_2)

    st.markdown("<br>", unsafe_allow_html=True)
    fcol, gcol = st.columns([1, 1])

    with fcol:
        fig = go.Figure(go.Funnel(
            y=["Failed Cases", "Attempted (policy allowed)", "Recovered"],
            x=[summary["total_failed_cases"], summary["cases_attempted"], summary["cases_recovered"]],
            marker=dict(color=[ACCENT, ACCENT_2, GOOD]),
            textinfo="value+percent initial",
        ))
        apply_dark_layout(fig, "Recovery Funnel — This Batch", height=380)
        st.plotly_chart(fig, use_container_width=True)

    with gcol:
        if len(audit_df):
            rec_by_stage = (
                audit_df[audit_df["outcome"] == "Recovered"]
                .groupby("channel")["amount"].sum().reset_index()
                .sort_values("amount", ascending=True)
            )
            fig = px.bar(rec_by_stage, x="amount", y="channel", orientation="h",
                         color="amount", color_continuous_scale=["#134e4a", GOOD])
            fig.update_layout(xaxis_title="Recovered ₹", yaxis_title="")
            apply_dark_layout(fig, "Recovered Revenue by Escalation Channel", height=380)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No outreach actions logged for the current filter selection.")

    st.markdown('<div class="section-label">Compliant Escalation & Stopping Rules</div>', unsafe_allow_html=True)
    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        st.markdown(
            '<div class="glass-panel">🪜 <b>Escalation ladder:</b> Stage 1 automated action → '
            'Stage 2 personalized message → final stage handed to a human agent. Nothing skips straight to a human.</div>',
            unsafe_allow_html=True,
        )
    with sc2:
        st.markdown(
            '<div class="glass-panel action">⏱ <b>Cooldown:</b> Each re-attempt is spaced 20–48 simulated hours apart — '
            'no same-day re-spam of a customer.</div>',
            unsafe_allow_html=True,
        )
    with sc3:
        st.markdown(
            f'<div class="glass-panel stop">🛑 <b>Hard stop:</b> Capped at {max_attempts} touches per case, and a case '
            'is never contacted again once recovered or once policy says "Do Not Retry Immediately."</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-label">Audit Trail</div>', unsafe_allow_html=True)
    st.caption("Every action the agent took in this run — fully explainable, timestamped, and exportable.")

    outcome_filter = st.multiselect(
        "Filter by outcome",
        sorted(audit_df["outcome"].unique().tolist()) if len(audit_df) else [],
        default=[],
    )
    audit_view = audit_df.copy()
    if outcome_filter:
        audit_view = audit_view[audit_view["outcome"].isin(outcome_filter)]

    if len(audit_view):
        display_audit = audit_view[[
            "timestamp", "transaction_id", "customer_name", "amount", "priority",
            "stage", "channel", "action", "probability_used", "outcome",
        ]].copy()
        display_audit["timestamp"] = display_audit["timestamp"].dt.strftime("%Y-%m-%d %H:%M")
        display_audit["amount"] = display_audit["amount"].apply(format_inr)
        st.dataframe(display_audit, use_container_width=True, hide_index=True, height=380)

        csv_bytes = audit_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download full audit trail (CSV)",
            data=csv_bytes,
            file_name="recovery_audit_trail.csv",
            mime="text/csv",
        )
    else:
        st.info("No audit rows match the current outcome filter.")

# ==========================================================================
# PAGE: ANALYTICS
# ==========================================================================

elif page == "📈 Analytics":
    st.markdown(
        """
        <div class="hero-banner">
            <div class="hero-eyebrow">DEEP DIVE</div>
            <div class="hero-title">Analytics</div>
            <div class="hero-sub">Deeper revenue recovery estimation and model performance.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    metrics = compute_summary_metrics(filtered_df)

    st.markdown('<div class="section-label">Revenue Recovery Estimation</div>', unsafe_allow_html=True)
    est_df = pd.DataFrame(
        {
            "Metric": [
                "Total Transaction Value", "Successful Revenue", "Failed Revenue",
                "Potential Recoverable Revenue", "High-Priority Recoverable Revenue", "Recovery Rate",
            ],
            "Value": [
                format_inr(metrics["total_value"]), format_inr(metrics["successful_revenue"]),
                format_inr(metrics["failed_revenue"]), format_inr(metrics["potential_recoverable_revenue"]),
                format_inr(metrics["high_priority_recoverable_revenue"]), f"{metrics['recovery_rate']}%",
            ],
        }
    )
    st.table(est_df)

    st.markdown('<div class="section-label">Recovery Rate Trend (by day)</div>', unsafe_allow_html=True)
    daily = filtered_df.copy()
    daily["date"] = daily["transaction_date"].dt.date
    daily_failed = daily[daily["payment_status"] == "Failed"].groupby("date")["amount"].sum()
    daily_recoverable = (
        daily[daily["payment_status"] == "Failed"]
        .assign(recoverable=lambda d: d["amount"] * (d["recovery_score"].fillna(0) / 100))
        .groupby("date")["recoverable"].sum()
    )
    trend = pd.DataFrame({"Failed Revenue": daily_failed, "Recoverable Revenue": daily_recoverable}).fillna(0).reset_index()
    if len(trend):
        fig = px.line(trend, x="date", y=["Failed Revenue", "Recoverable Revenue"],
                       color_discrete_sequence=[BAD, GOOD])
        apply_dark_layout(fig, "Failed vs Recoverable Revenue Over Time")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data in the current filter range to plot a trend.")

    st.markdown('<div class="section-label">ML Model Performance</div>', unsafe_allow_html=True)
    if model_ready:
        try:
            model = RecoveryModel.load()
            importances = model.feature_importances().head(10)
            fig = px.bar(importances[::-1], orientation="h", color_discrete_sequence=[ACCENT])
            fig.update_layout(yaxis_title="", xaxis_title="Importance", showlegend=False)
            apply_dark_layout(fig, "Top Feature Importances (Recovery Likelihood Model)")
            st.plotly_chart(fig, use_container_width=True)
            st.caption(
                "This RandomForest model was trained on historical failed transactions to predict the "
                "probability that a retry/follow-up will succeed. Run `python models/train_model.py` "
                "to retrain and see evaluation metrics (accuracy, precision, recall, ROC-AUC) in the terminal."
            )
        except Exception as exc:
            st.warning(f"Could not load model details: {exc}")
    else:
        st.info("Train the model with `python models/train_model.py` to see feature importance here.")

st.markdown("---")
st.caption(
    "⚠️ All transaction and customer data shown is synthetically generated for demonstration purposes only. "
    "This project is not officially affiliated with or connected to Razorpay's live payment systems."
)
