import json
from pathlib import Path

import streamlit as st

from src.finmemo_crew.main import run_for_ticker
from src.finmemo_crew.ui_service import (
    build_agent_status,
    extract_pipeline_details,
    load_handoff_traces,
    parse_memo_metadata,
)

st.set_page_config(
    page_title="FinMemo Crew · AI Investment Research",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom Styling inspired by modern fintech terminals (Fiscal.ai, Koyfin)
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3.5rem;
        max-width: 1200px;
    }
    .hero-title {
        font-size: 2.5rem;
        font-weight: 800;
        letter-spacing: -0.025em;
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.15rem;
    }
    .hero-subtitle {
        color: #94a3b8;
        font-size: 1rem;
        margin-bottom: 1.25rem;
    }
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 12px;
        margin: 1rem 0;
    }
    .kpi-card {
        background: rgba(15, 23, 42, 0.65);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 12px;
        padding: 14px 16px;
        backdrop-filter: blur(8px);
    }
    .kpi-label {
        color: #94a3b8;
        font-size: 0.78rem;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    .kpi-value {
        color: #f8fafc;
        font-size: 1.35rem;
        font-weight: 700;
    }
    .kpi-sub {
        color: #64748b;
        font-size: 0.75rem;
        margin-top: 3px;
    }
    .badge-pill {
        display: inline-flex;
        align-items: center;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-high {
        background: rgba(239, 68, 68, 0.15);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    .badge-medium {
        background: rgba(245, 158, 11, 0.15);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    .badge-low {
        background: rgba(59, 130, 246, 0.15);
        color: #60a5fa;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }
    .badge-success {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .risk-card {
        background: rgba(30, 41, 59, 0.45);
        border: 1px solid rgba(148, 163, 184, 0.12);
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 10px;
    }
    .timeline-node {
        border-left: 2px solid #38bdf8;
        padding-left: 16px;
        margin-bottom: 16px;
        position: relative;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header Section
st.markdown(
    """
    <div style='text-align: center;'>
        <div class='hero-title'>FinMemo Crew</div>
        <div class='hero-subtitle'>Autonomous multi-agent equity research & verification workstation</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Crew Architecture Expander
with st.expander("ℹ️ Multi-Agent Architecture & Pipeline", expanded=False):
    st.caption("A deterministic 5-stage research pipeline with built-in verification and schema enforcement:")
    agents = build_agent_status()
    cols = st.columns(len(agents))
    for col, ag in zip(cols, agents):
        with col:
            st.markdown(f"**{ag['avatar']} {ag['name']}**")
            st.caption(ag["role"])

# Quick Ticker Chips & Control Bar
if "ticker_input" not in st.session_state:
    st.session_state["ticker_input"] = "AAPL"

popular_tickers = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA"]

with st.container(border=True):
    # Quick select row
    chip_cols = st.columns([1] * len(popular_tickers) + [3])
    for idx, sym in enumerate(popular_tickers):
        with chip_cols[idx]:
            if st.button(sym, key=f"chip_{sym}", use_container_width=True):
                st.session_state["ticker_input"] = sym
                st.rerun()

    # Input and Action row
    col_input, col_action = st.columns([3, 1], vertical_alignment="bottom")
    with col_input:
        current_val = st.session_state["ticker_input"]
        typed_ticker = st.text_input(
            "Target Equity Ticker",
            value=current_val,
            max_chars=10,
            placeholder="e.g. AAPL, MSFT, NVDA",
            help="Enter a stock ticker symbol to launch autonomous research pipeline.",
        )
    with col_action:
        run_button = st.button("🚀 Run Analysis", type="primary", use_container_width=True)

memo_path = Path("output/investment_memo_draft.md")
critique_path = Path("output/critique_report.json")
handoff_traces = load_handoff_traces()
pipeline_details = extract_pipeline_details(handoff_traces)

# Execution trigger
if run_button:
    clean_ticker = typed_ticker.strip().upper()
    if not clean_ticker:
        st.warning("Please specify a valid stock ticker symbol.")
    else:
        st.session_state["ticker_input"] = clean_ticker
        with st.spinner(f"AI agents are gathering data, analyzing quant metrics, and stress-testing {clean_ticker}..."):
            try:
                result = run_for_ticker(clean_ticker)
                st.success(f"Research and verification pipeline finished for **{result['ticker']}**")
                # Reload outputs after run
                handoff_traces = load_handoff_traces()
                pipeline_details = extract_pipeline_details(handoff_traces)
            except Exception as exc:
                st.error(f"Execution encountered an error: {exc}")

# Display results if available
if memo_path.exists() or critique_path.exists():
    memo_text = memo_path.read_text(encoding="utf-8") if memo_path.exists() else ""
    metadata = parse_memo_metadata(memo_text)

    critique_data = {}
    if critique_path.exists():
        try:
            critique_data = json.loads(critique_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    # Top-Level KPI Summary Banner (Inspired by Koyfin & Fiscal.ai)
    st.divider()

    company_name = metadata.get("company_name", "Analyzed Company")
    ticker_display = metadata.get("ticker", typed_ticker)
    sector_info = metadata.get("sector", "")
    industry_info = metadata.get("industry", "")
    sub_title = f"{sector_info} · {industry_info}" if industry_info else sector_info

    col_title, col_export = st.columns([3, 1], vertical_alignment="center")
    with col_title:
        st.subheader(f"{ticker_display} · {company_name}")
        if sub_title:
            st.caption(sub_title)
    with col_export:
        if memo_text:
            st.download_button(
                label="📥 Export Memo (.md)",
                data=memo_text,
                file_name=f"{ticker_display}_Investment_Memo.md",
                mime="text/markdown",
                use_container_width=True,
            )

    # 4 Quick KPI metric cards
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    with kpi_col1:
        price_val = metadata.get("current_price", "N/A")
        market_cap_val = metadata.get("market_cap", "N/A")
        st.markdown(
            f"""
            <div class='kpi-card'>
                <div class='kpi-label'>Current Price</div>
                <div class='kpi-value'>{price_val}</div>
                <div class='kpi-sub'>Market Cap: {market_cap_val}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi_col2:
        quant_verdict = pipeline_details["quant_analysis"].get("valuation_verdict", "Available in Report")
        if len(quant_verdict) > 28:
            quant_verdict = quant_verdict[:25] + "..."
        st.markdown(
            f"""
            <div class='kpi-card'>
                <div class='kpi-label'>Valuation Verdict</div>
                <div class='kpi-value' style='font-size:1.1rem;'>{quant_verdict}</div>
                <div class='kpi-sub'>Quantitative Analyst</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi_col3:
        overall_risk = pipeline_details["risk_assessment"].get("overall_risk_level", "Medium").capitalize()
        risk_class = "badge-high" if overall_risk.lower() == "high" else ("badge-medium" if overall_risk.lower() == "medium" else "badge-low")
        st.markdown(
            f"""
            <div class='kpi-card'>
                <div class='kpi-label'>Overall Risk Profile</div>
                <div class='kpi-value'><span class='badge-pill {risk_class}'>{overall_risk} Risk</span></div>
                <div class='kpi-sub'>{len(pipeline_details['risk_assessment'].get('flags', []))} Identified Risk Factors</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi_col4:
        verification_passed = critique_data.get("verification_passed", False)
        status_badge = "<span class='badge-pill badge-success'>✅ Passed</span>" if verification_passed else "<span class='badge-pill badge-high'>⚠️ Issues Flagged</span>"
        total_issues = len(critique_data.get("unsupported_claims", [])) + len(critique_data.get("missing_considerations", [])) + len(critique_data.get("logical_issues", []))
        st.markdown(
            f"""
            <div class='kpi-card'>
                <div class='kpi-label'>Audit & Critique</div>
                <div class='kpi-value'>{status_badge}</div>
                <div class='kpi-sub'>{total_issues} Discrepancies Flagged</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 5-Tab Analytical Workstation
    tab_memo, tab_quant, tab_risk, tab_critique, tab_trace = st.tabs([
        "📑 Investment Memo",
        "📊 Quantitative Deep-Dive",
        "⚠️ Risk Matrix",
        "🛡️ Verification Audit",
        "⚡ Multi-Agent Trace",
    ])

    # TAB 1: Investment Memo
    with tab_memo:
        if memo_text:
            st.markdown(memo_text)
        else:
            st.info("No memo content found.")

    # TAB 2: Quantitative Deep-Dive
    with tab_quant:
        quant = pipeline_details.get("quant_analysis", {})
        if quant:
            st.markdown("### 📊 Quantitative & Valuation Analysis")
            if "valuation_verdict" in quant:
                st.info(f"**Valuation Verdict:** {quant['valuation_verdict']}")

            q_col1, q_col2 = st.columns(2)
            with q_col1:
                with st.container(border=True):
                    st.markdown("#### Valuation Ratios")
                    st.write(quant.get("valuation_ratios_summary", "No valuation ratios available."))

                with st.container(border=True):
                    st.markdown("#### Margin Analysis")
                    st.write(quant.get("margin_analysis", "No margin analysis available."))

            with q_col2:
                with st.container(border=True):
                    st.markdown("#### Growth Trends")
                    st.write(quant.get("growth_trend_analysis", "No growth trend available."))

                with st.container(border=True):
                    st.markdown("#### Sector Comparison")
                    st.write(quant.get("sector_comparison", "No sector comparison available."))
        else:
            st.info("Run the research crew to view detailed quantitative breakdowns.")

    # TAB 3: Risk Matrix
    with tab_risk:
        risk_data = pipeline_details.get("risk_assessment", {})
        flags = risk_data.get("flags", [])
        if flags:
            st.markdown(f"### ⚠️ Identified Material Risk Factors ({len(flags)})")
            for flag in flags:
                severity = flag.get("severity", "medium").lower()
                sev_class = "badge-high" if severity == "high" else ("badge-medium" if severity == "medium" else "badge-low")
                category = flag.get("category", "General").capitalize()

                st.markdown(
                    f"""
                    <div class='risk-card'>
                        <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;'>
                            <strong>{category} Risk</strong>
                            <span class='badge-pill {sev_class}'>{severity.upper()}</span>
                        </div>
                        <p style='margin-bottom:6px; color:#e2e8f0; font-size:0.92rem;'>{flag.get('description', '')}</p>
                        <div style='color:#94a3b8; font-size:0.8rem;'><strong>Evidence:</strong> {flag.get('evidence', 'N/A')}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("Run the research crew to view categorized risk flags.")

    # TAB 4: Verification Audit
    with tab_critique:
        if critique_data:
            passed = critique_data.get("verification_passed", False)
            notes = critique_data.get("notes", "No notes available.")

            if passed:
                st.success(f"**Verification Passed**: {notes}")
            else:
                st.warning(f"**Critic Flagged Discrepancies**: {notes}")

            unsupported = critique_data.get("unsupported_claims", [])
            missing = critique_data.get("missing_considerations", [])
            logical = critique_data.get("logical_issues", [])

            if unsupported:
                st.error("**Unsupported Claims in Memo:**\n" + "\n".join(f"- {c}" for c in unsupported))
            if missing:
                st.warning("**Missing Considerations:**\n" + "\n".join(f"- {m}" for m in missing))
            if logical:
                st.error("**Logical Contradictions:**\n" + "\n".join(f"- {l}" for l in logical))

            if not unsupported and not missing and not logical and passed:
                st.markdown("✨ *All claims in the investment memo are fully grounded in collected data with zero contradictions.*")

            with st.expander("🔍 Inspect Full Critique JSON"):
                st.json(critique_data)
        else:
            st.info("No verification critique report has been generated yet.")

    # TAB 5: Multi-Agent Trace
    with tab_trace:
        if handoff_traces:
            st.markdown("### ⚡ Autonomous Agent Handoff Log")
            st.caption("Audit trail of chronological handoffs between agents:")
            for trace in handoff_traces:
                agent = trace.get("agent", "Agent").strip()
                timestamp = trace.get("timestamp", "")
                task_desc = trace.get("task_description", "")

                with st.expander(f"🤖 {agent} — {timestamp[:19] if timestamp else ''}", expanded=False):
                    st.markdown(f"**Task Prompt:** {task_desc}")
                    st.markdown("**Output Preview:**")
                    preview = trace.get("output_preview", "")
                    if preview.strip().startswith("{") or preview.strip().startswith("```json"):
                        st.code(preview[:500] + ("..." if len(preview) > 500 else ""), language="json")
                    else:
                        st.code(preview[:500] + ("..." if len(preview) > 500 else ""), language="markdown")
        else:
            st.info("No agent handoff logs recorded yet.")
else:
    st.info("Select or enter a ticker symbol above and click **Run Analysis** to launch the AI research crew.")
