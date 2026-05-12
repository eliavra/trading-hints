from __future__ import annotations

from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from data import compute_market_breadth, compute_seasonality, compute_sector_data
from models import Signal

st.set_page_config(page_title="Exposure Dashboard", layout="wide", initial_sidebar_state="expanded")

# ---------------------------------------------------------------------------
# Theme / CSS
# ---------------------------------------------------------------------------
TEAL = "#0d9488"
SLATE_800 = "#1e293b"
SLATE_600 = "#475569"
SLATE_100 = "#f1f5f9"

SIGNAL_COLORS: dict[str, dict[str, str]] = {
    "red": {"bg": "#fee2e2", "fg": "#991b1b"},
    "green": {"bg": "#dcfce7", "fg": "#166534"},
    "yellow": {"bg": "#fef9c3", "fg": "#854d0e"},
}

RED_SIGNALS = {
    Signal.OVERBOUGHT, Signal.RED_LIGHT, Signal.WEAK_BEAR,
    Signal.EUPHORIA, Signal.DIVERGENCE, Signal.SELLING,
    Signal.COLD, Signal.BEARISH,
}
GREEN_SIGNALS = {
    Signal.OVERSOLD, Signal.GREEN_LIGHT, Signal.STRONG_BULL,
    Signal.FEAR, Signal.HEALTHY, Signal.BUYING,
    Signal.HOT, Signal.BULLISH,
}

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* header bar */
header[data-testid="stHeader"] { background: white; border-bottom: 1px solid #e2e8f0; }

/* sidebar */
section[data-testid="stSidebar"] {
    background: white; border-right: 1px solid #e2e8f0;
}
section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 { color: #1e293b; }

/* card helper */
.card {
    background: white; border: 1px solid #e2e8f0; border-radius: 1rem;
    padding: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,.04);
}
.card-title { font-size: 1rem; font-weight: 700; color: #1e293b; margin-bottom: .75rem; }
.card:hover { transform: translateY(-1px); transition: all .15s; }

/* metric overrides */
div[data-testid="stMetric"] {
    background: white; border: 1px solid #e2e8f0; border-radius: .75rem;
    padding: 1rem 1.25rem; box-shadow: 0 1px 2px rgba(0,0,0,.03);
}
div[data-testid="stMetric"] label { color: #64748b !important; font-size: .8rem; }
div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #0f172a; font-weight: 700; }

/* tabs restyle */
button[data-baseweb="tab"] {
    font-weight: 600 !important; color: #64748b !important;
    border-bottom: 3px solid transparent !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #0d9488 !important; border-bottom: 3px solid #0d9488 !important;
}

/* signal badge */
.signal-badge {
    display: inline-block; padding: 4px 14px; border-radius: 9999px;
    font-weight: 700; font-size: .8rem; letter-spacing: .02em;
}

/* dataframe tweaks */
div[data-testid="stDataFrame"] th { background-color: #f8fafc !important; }

/* plotly bg */
.js-plotly-plot .plotly .main-svg { border-radius: .75rem; }
</style>
""", unsafe_allow_html=True)

PLOTLY_LAYOUT = dict(
    paper_bgcolor="white",
    plot_bgcolor="#f8fafc",
    font=dict(family="Inter, sans-serif", color=SLATE_600),
    title_font=dict(size=15, color=SLATE_800),
    margin=dict(t=45, b=40, l=50, r=20),
    xaxis=dict(gridcolor="#e2e8f0"),
    yaxis=dict(gridcolor="#e2e8f0"),
)


def signal_color(sig: Signal) -> dict[str, str]:
    if sig in RED_SIGNALS:
        return SIGNAL_COLORS["red"]
    if sig in GREEN_SIGNALS:
        return SIGNAL_COLORS["green"]
    return SIGNAL_COLORS["yellow"]


def signal_badge(sig: Signal) -> str:
    c = signal_color(sig)
    return f"<span class='signal-badge' style='background:{c['bg']};color:{c['fg']}'>{sig.value}</span>"


def style_signal_cell(val: str, cmap: dict[str, dict[str, str]]) -> str:
    c = cmap.get(val, SIGNAL_COLORS["yellow"])
    return f"background-color: {c['bg']}; color: {c['fg']}; font-weight: 700; border-radius: 4px"


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:1.5rem">
        <div style="width:36px;height:36px;background:{TEAL};border-radius:8px;display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:1.1rem">Q</div>
        <div>
            <div style="font-weight:700;color:{SLATE_800};font-size:1rem;line-height:1.2">Exposure Manager</div>
            <div style="font-size:.75rem;color:#94a3b8">Interactive Dashboard</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    refresh_interval = st.selectbox("Auto-refresh", ["Off", "1 min", "5 min", "15 min"], index=0)
    interval_map = {"Off": 0, "1 min": 60_000, "5 min": 300_000, "15 min": 900_000}
    if interval_map[refresh_interval]:
        st_autorefresh(interval=interval_map[refresh_interval], key="auto_refresh")

    st.divider()
    ticker_input = st.text_input("Seasonality Ticker", value="TSLA").upper().strip()

    st.divider()
    st.markdown(f"<div style='font-size:.75rem;color:#94a3b8'>Last refresh: {datetime.now().strftime('%H:%M:%S')}</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_breadth, tab_sectors, tab_season = st.tabs([
    "Sentiment & Breadth",
    "Sector Rotation",
    "Seasonality Hunter",
])

# ========================== Sentiment & Breadth ============================
TIMEFRAME_CONFIG = {
    "Short Term": {
        "field": "pct_above_sma20",
        "title": "% Stocks Above SMA 20",
        "low": 20, "high": 85,
        "calc": "Percentage of S&P 500 stocks trading above their 20-day Simple Moving Average.",
        "usage": "Above 85% — overbought, reduce longs / tighten stops. Below 20% — oversold, look for long entries. Between 70-85% — be selective.",
    },
    "Medium Term": {
        "field": "pct_above_sma50",
        "title": "% Stocks Above SMA 50",
        "low": 30, "high": 85,
        "calc": "Percentage of S&P 500 stocks trading above their 50-day Simple Moving Average.",
        "usage": "The classic range for significant corrections. 85% is a red light — reduce exposure. Below 30% — green light, increase exposure.",
    },
    "Long Term": {
        "field": "pct_above_sma200",
        "title": "% Stocks Above SMA 200",
        "low": 40, "high": 80,
        "calc": "Percentage of S&P 500 stocks trading above their 200-day Simple Moving Average.",
        "usage": "Defines Bull vs Bear market. Above 80% — strong bull, stay long. Below 40% — weak / bear, go defensive. Below 60% — tighten stops.",
    },
}

with tab_breadth:
    with st.spinner("Loading S&P 500 data..."):
        breadth = compute_market_breadth()

    mc1, mc2, mc3, mc4, mc5 = st.columns(5)
    mc1.metric("% > SMA 20", f"{breadth.pct_above_sma20:.1f}%")
    mc2.metric("% > SMA 50", f"{breadth.pct_above_sma50:.1f}%")
    mc3.metric("% > SMA 200", f"{breadth.pct_above_sma200:.1f}%")
    mc4.metric("Fear/Greed", f"{breadth.fear_greed_score:.0f}/100")
    mc5.metric("VIX", f"{breadth.vix:.1f}")

    # --- Timeframe toggle ---
    tf = st.radio("Timeframe", list(TIMEFRAME_CONFIG.keys()), horizontal=True, label_visibility="collapsed")
    cfg = TIMEFRAME_CONFIG[tf]
    current_val = getattr(breadth, cfg["field"])

    chart_col, info_col = st.columns([2, 1])

    with chart_col:
        gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=current_val,
            number={"suffix": "%", "font": {"size": 48, "color": SLATE_800}},
            title={"text": cfg["title"], "font": {"size": 15, "color": SLATE_600}},
            gauge=dict(
                axis=dict(range=[0, 100], tickwidth=1, tickcolor=SLATE_600),
                bar=dict(color=TEAL),
                bgcolor="white",
                steps=[
                    dict(range=[0, cfg["low"]], color="#dcfce7"),
                    dict(range=[cfg["low"], cfg["high"]], color="#f1f5f9"),
                    dict(range=[cfg["high"], 100], color="#fee2e2"),
                ],
                threshold=dict(
                    line=dict(color="#ef4444", width=3),
                    thickness=0.8,
                    value=current_val,
                ),
            ),
        ))
        gauge.update_layout(height=300, margin=dict(t=50, b=10, l=40, r=40), paper_bgcolor="white")
        st.plotly_chart(gauge, use_container_width=True)

    with info_col:
        st.markdown(f"""
        <div class="card" style="height:100%">
            <div style="font-weight:700;color:{TEAL};margin-bottom:.5rem">How to Calculate</div>
            <p style="font-size:.85rem;color:{SLATE_600};line-height:1.6;margin-bottom:1rem">{cfg['calc']}</p>
            <div style="font-weight:700;color:{TEAL};margin-bottom:.5rem">Operative Meaning</div>
            <p style="font-size:.85rem;color:{SLATE_600};line-height:1.6">{cfg['usage']}</p>
            <div style="margin-top:1rem;padding-top:.75rem;border-top:1px solid #e2e8f0">
                <span style="font-size:.8rem;color:#94a3b8">Oversold zone: &lt;{cfg['low']}%</span><br>
                <span style="font-size:.8rem;color:#94a3b8">Overbought zone: &gt;{cfg['high']}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # --- Full indicators table ---
    st.markdown("<div class='card-title' style='margin-top:1.5rem'>All Breadth Indicators</div>", unsafe_allow_html=True)
    rows = []
    color_map: dict[str, dict[str, str]] = {}
    for ind in breadth.indicators:
        sv = ind.signal.value
        rows.append({"Indicator": ind.name, "Value": ind.value, "Signal": sv, "Action": ind.action})
        color_map[sv] = signal_color(ind.signal)
    df_b = pd.DataFrame(rows)
    styled = df_b.style.map(lambda v: style_signal_cell(v, color_map) if v in color_map else "", subset=["Signal"])
    st.dataframe(styled, use_container_width=True, hide_index=True)

    # --- A/D Line chart ---
    if breadth.ad_line and breadth.ad_line_dates:
        ad_fig = go.Figure(go.Scatter(
            x=breadth.ad_line_dates, y=breadth.ad_line,
            mode="lines", line=dict(color=TEAL, width=2),
            fill="tozeroy", fillcolor="rgba(13,148,136,0.06)",
        ))
        ad_fig.update_layout(
            title=f"Cumulative Advance-Decline Line (Trend: {breadth.ad_line_trend})",
            xaxis_title="", yaxis_title="Cumulative Net Advances",
            height=340, **PLOTLY_LAYOUT,
        )
        st.plotly_chart(ad_fig, use_container_width=True)

# ========================== Sector Rotation ================================
with tab_sectors:
    st.markdown(f"""
    <div style="margin-bottom:1rem">
        <span style="font-size:1.2rem;font-weight:700;color:{SLATE_800}">Sector Rotation Radar</span>
        <span style="margin-left:12px;font-size:.85rem;color:#94a3b8">% deviation from 20-day SMA — red/green flags mark extremes</span>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("Loading sector data..."):
        sectors = compute_sector_data()

    bar_colors = []
    for s in sectors:
        if s.pct_vs_sma20 > 0.03:
            bar_colors.append("#22c55e")
        elif s.pct_vs_sma20 < -0.03:
            bar_colors.append("#ef4444")
        else:
            bar_colors.append("#94a3b8")

    sfig = go.Figure(go.Bar(
        y=[s.name for s in sectors],
        x=[s.pct_vs_sma20 * 100 for s in sectors],
        marker_color=bar_colors,
        text=[f"{s.pct_vs_sma20:.1%}" for s in sectors],
        textposition="outside",
        orientation="h",
    ))
    sfig.update_layout(
        title="Sector % vs SMA 20",
        xaxis_title="% vs SMA 20", yaxis_title="",
        height=450, **PLOTLY_LAYOUT,
    )
    sfig.update_yaxes(autorange="reversed")
    sfig.add_vline(x=3, line_dash="dash", line_color="#22c55e", opacity=0.5)
    sfig.add_vline(x=-3, line_dash="dash", line_color="#ef4444", opacity=0.5)
    st.plotly_chart(sfig, use_container_width=True)

    sector_rows = []
    sector_cmap: dict[str, dict[str, str]] = {}
    for s in sectors:
        sv = s.signal.value
        sector_rows.append({
            "Sector": s.name, "ETF": s.etf,
            "Price": f"${s.price:.2f}",
            "Day": s.perf_day, "1 Week": s.perf_1w,
            "2 Weeks": s.perf_2w, "3 Weeks": s.perf_3w,
            "Signal": sv,
        })
        sector_cmap[sv] = signal_color(s.signal)

    df_s = pd.DataFrame(sector_rows)

    def _color_perf(val: object) -> str:
        if not isinstance(val, (int, float)):
            return ""
        if val > 0:
            return "color: #166534; font-weight: 600"
        if val < 0:
            return "color: #991b1b; font-weight: 600"
        return ""

    perf_cols = ["Day", "1 Week", "2 Weeks", "3 Weeks"]
    styled_s = (
        df_s.style
        .format({c: "{:+.2%}" for c in perf_cols})
        .map(_color_perf, subset=perf_cols)
        .map(lambda v: style_signal_cell(v, sector_cmap) if v in sector_cmap else "", subset=["Signal"])
    )
    st.dataframe(styled_s, use_container_width=True, hide_index=True)

# ========================== Seasonality ====================================
with tab_season:
    if not ticker_input:
        st.warning("Enter a ticker in the sidebar.")
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
