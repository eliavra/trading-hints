import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from data import compute_seasonality
from ui import load_css, TEAL, SLATE_800, SLATE_600, PLOTLY_LAYOUT, signal_color, signal_badge

load_css()

st.title("Seasonality Hunter")

col_search, _ = st.columns([1, 3])
with col_search:
    ticker_input = st.text_input("Lookup Symbol", value="SPY", placeholder="AAPL, TSLA, BTC-USD").upper().strip()

if not ticker_input:
    st.warning("Please enter a ticker symbol to analyze.")
else:
    with st.spinner(f"Loading 10y data for {ticker_input}..."):
        result = compute_seasonality(ticker_input)

    if not result.monthly:
        st.error(f"No data found for {ticker_input}")
    else:
        cm = result.monthly[datetime.now().month - 1]
        sc = signal_color(result.signal)

        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:1.5rem;margin-bottom:1.5rem;flex-wrap:wrap">
            <span style="font-size:1.3rem;font-weight:700;color:{SLATE_800}">Seasonality — {ticker_input}</span>
            {signal_badge(result.signal)}
        </div>
        """, unsafe_allow_html=True)

        sm1, sm2, sm3, sm4 = st.columns(4)
        sm1.metric("Current Month", result.current_month)
        sm2.metric("Avg Return", f"{cm.avg_return:.2%}")
        sm3.metric("Win Rate", f"{cm.win_rate:.0%}")
        sm4.metric("Std Dev", f"{cm.std_dev:.2%}")

        chart_col, insight_col = st.columns([2, 1])

        with chart_col:
            bar_c = ["#0d9488" if r.avg_return >= 0 else "#ef4444" for r in result.monthly]
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=[r.label for r in result.monthly],
                y=[r.avg_return * 100 for r in result.monthly],
                marker_color=bar_c,
                text=[f"{r.avg_return:.2%}" for r in result.monthly],
                textposition="outside", name="Avg Return %",
            ))
            fig.add_trace(go.Scatter(
                x=[r.label for r in result.monthly],
                y=[r.win_rate * 100 for r in result.monthly],
                mode="lines+markers", name="Win Rate %",
                line=dict(color="#f59e0b", width=2),
                marker=dict(size=6), yaxis="y2",
            ))
            fig.update_layout(
                title=f"Monthly Seasonality (10yr) — {ticker_input}",
                yaxis_title="Avg Return %",
                yaxis2=dict(title="Win Rate %", overlaying="y", side="right", range=[0, 100], gridcolor="rgba(0,0,0,0)"),
                height=420, legend=dict(orientation="h", y=-0.15),
                **PLOTLY_LAYOUT,
            )
            st.plotly_chart(fig, use_container_width=True)

        with insight_col:
            best = max(result.monthly, key=lambda r: r.avg_return)
            worst = min(result.monthly, key=lambda r: r.avg_return)
            most_consistent = max(result.monthly, key=lambda r: r.win_rate)

            st.markdown(f"""
            <div class="card" style="background:#fffbeb;border-color:#fde68a;height:100%">
                <div style="font-weight:700;color:#92400e;margin-bottom:.75rem">Seasonal Insights</div>
                <ul style="font-size:.85rem;color:#78350f;line-height:2;padding-right:1rem">
                    <li><b>{best.label}</b> is the strongest month ({best.avg_return:.2%} avg, {best.win_rate:.0%} hit rate)</li>
                    <li><b>{worst.label}</b> is the weakest month ({worst.avg_return:.2%} avg)</li>
                    <li><b>{most_consistent.label}</b> has the highest consistency ({most_consistent.win_rate:.0%} win rate)</li>
                    <li>Current month <b>{result.current_month}</b>: {cm.avg_return:.2%} avg return</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        monthly_rows = [{
            "#": r.period, "Month": r.label,
            "Avg Return": f"{r.avg_return:.2%}", "Win Rate": f"{r.win_rate:.0%}",
            "Std Dev": f"{r.std_dev:.2%}", "Min": f"{r.min_return:.2%}", "Max": f"{r.max_return:.2%}",
        } for r in result.monthly]
        st.dataframe(pd.DataFrame(monthly_rows), use_container_width=True, hide_index=True)

        with st.expander("Weekly Seasonality"):
            weekly_rows = [{
                "Week": r.period, "Avg Return": f"{r.avg_return:.2%}",
                "Win Rate": f"{r.win_rate:.0%}", "Std Dev": f"{r.std_dev:.2%}",
                "Min": f"{r.min_return:.2%}", "Max": f"{r.max_return:.2%}",
            } for r in result.weekly]
            st.dataframe(pd.DataFrame(weekly_rows), use_container_width=True, hide_index=True)
