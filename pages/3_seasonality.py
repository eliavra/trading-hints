import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from data import compute_seasonality
from ui import load_css, TEAL, SLATE_800, SLATE_600, PLOTLY_LAYOUT, signal_color, signal_badge
from locales import t

load_css()

st.title(t("seasonality"))

col_search, _ = st.columns([1, 3])
with col_search:
    ticker_input = st.text_input(t("lookup_symbol"), value="SPY", placeholder="AAPL, TSLA, BTC-USD").upper().strip()

if not ticker_input:
    st.warning(t("Please enter a ticker symbol to analyze."))
else:
    with st.spinner(f"{t('loading_seasonality')} {ticker_input}..."):
        result = compute_seasonality(ticker_input)

    if not result.monthly:
        st.error(f"{t('No data found for')} {ticker_input}")
    else:
        cm = result.monthly[datetime.now().month - 1]
        sc = signal_color(result.signal)

        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:1.5rem;margin-bottom:1.5rem;flex-wrap:wrap">
            <span style="font-size:1.3rem;font-weight:700;color:{SLATE_800}">{t('seasonality')} — {ticker_input}</span>
            {signal_badge(result.signal)}
        </div>
        """, unsafe_allow_html=True)

        sm1, sm2, sm3, sm4 = st.columns(4)
        sm1.metric(t("current_month_label"), t(result.current_month))
        sm2.metric(t("avg_return_label"), f"{cm.avg_return:.2%}")
        sm3.metric(t("win_rate_label"), f"{cm.win_rate:.0%}")
        sm4.metric(t("std_dev_label"), f"{cm.std_dev:.2%}")

        chart_col, insight_col = st.columns([2, 1])

        with chart_col:
            bar_c = ["#0d9488" if r.avg_return >= 0 else "#ef4444" for r in result.monthly]
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=[t(r.label) for r in result.monthly],
                y=[r.avg_return * 100 for r in result.monthly],
                marker_color=bar_c,
                text=[f"{r.avg_return:.2%}" for r in result.monthly],
                textposition="outside", name=t("avg_return_label") + " %",
            ))
            fig.add_trace(go.Scatter(
                x=[t(r.label) for r in result.monthly],
                y=[r.win_rate * 100 for r in result.monthly],
                mode="lines+markers", name=t("win_rate_label") + " %",
                line=dict(color="#f59e0b", width=2),
                marker=dict(size=6), yaxis="y2",
            ))
            fig.update_layout(
                title=f"{t('monthly_seasonality_title')} — {ticker_input}",
                yaxis_title=t("avg_return_label") + " %",
                yaxis2=dict(title=t("win_rate_label") + " %", overlaying="y", side="right", range=[0, 100], gridcolor="rgba(0,0,0,0)"),
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
                <div style="font-weight:700;color:#92400e;margin-bottom:.75rem">{t('seasonal_insights_title')}</div>
                <ul style="font-size:.85rem;color:#78350f;line-height:2;padding-right:1rem">
                    <li><b>{t(best.label)}</b> {t('strongest_month_desc')} ({best.avg_return:.2%} {t('avg_return_label').lower()}, {best.win_rate:.0%} {t('win_rate_label').lower()})</li>
                    <li><b>{t(worst.label)}</b> {t('weakest_month_desc')} ({worst.avg_return:.2%} {t('avg_return_label').lower()})</li>
                    <li><b>{t(most_consistent.label)}</b> {t('consistency_desc')} ({most_consistent.win_rate:.0%} {t('win_rate_label').lower()})</li>
                    <li>{t('current_month_desc')} <b>{t(result.current_month)}</b>: {cm.avg_return:.2%} {t('avg_return_label').lower()}</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        monthly_rows = [{
            "#": r.period, t("Month"): t(r.label),
            t("Avg Return"): f"{r.avg_return:.2%}", t("Win Rate"): f"{r.win_rate:.0%}",
            t("Std Dev"): f"{r.std_dev:.2%}", t("Min"): f"{r.min_return:.2%}", t("Max"): f"{r.max_return:.2%}",
        } for r in result.monthly]
        st.dataframe(pd.DataFrame(monthly_rows), use_container_width=True, hide_index=True)

        with st.expander(t("weekly_seasonality_title")):
            weekly_rows = [{
                t("Week"): r.period, t("Avg Return"): f"{r.avg_return:.2%}",
                t("Win Rate"): f"{r.win_rate:.0%}", t("Std Dev"): f"{r.std_dev:.2%}",
                t("Min"): f"{r.min_return:.2%}", t("Max"): f"{r.max_return:.2%}",
            } for r in result.weekly]
            st.dataframe(pd.DataFrame(weekly_rows), use_container_width=True, hide_index=True)
