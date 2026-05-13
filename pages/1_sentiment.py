import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data import compute_market_breadth
from ui import load_css, TEAL, SLATE_800, SLATE_600, PLOTLY_LAYOUT, signal_color, style_signal_cell

load_css()

st.title("Sentiment & Breadth")

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
    val_str = str(ind.value) if not isinstance(ind.value, float) else f"{ind.value:.2f}"
    rows.append({"Indicator": ind.name, "Value": val_str, "Signal": sv, "Action": ind.action})
    color_map[sv] = signal_color(ind.signal)
df_b = pd.DataFrame(rows)
styled = df_b.style.map(lambda v: style_signal_cell(v, color_map) if v in color_map else "", subset=["Signal"])
st.dataframe(styled, use_container_width=True, hide_index=True)

# --- A/D Line chart ---
if breadth.ad_data:
    ad_period = st.radio("A/D Line Timeframe", list(breadth.ad_data.keys()), index=2, horizontal=True) # default 6M
    current_ad = breadth.ad_data[ad_period]
    ad_line = current_ad["ad_line"]
    ad_dates = current_ad["ad_dates"]
    ad_trend = current_ad["trend"]
    
    ad_fig = go.Figure(go.Scatter(
        x=ad_dates, y=ad_line,
        mode="lines", line=dict(color=TEAL, width=2),
        fill="tozeroy", fillcolor="rgba(13,148,136,0.06)",
    ))
    ad_fig.update_layout(
        title=f"Cumulative Advance-Decline Line (Trend: {ad_trend})",
        xaxis_title="", yaxis_title="Cumulative Net Advances",
        height=340, **PLOTLY_LAYOUT,
    )
    st.plotly_chart(ad_fig, use_container_width=True)
