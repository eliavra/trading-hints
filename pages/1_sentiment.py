import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data import compute_market_breadth
from ui import load_css, TEAL, SLATE_800, SLATE_600, PLOTLY_LAYOUT, signal_color, style_signal_cell, create_gauge_chart

load_css()

st.title("Sentiment & Breadth")
st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)

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
mc1.metric("% > SMA 20", f"{breadth.pct_above_sma20:.1f}%", help="Percentage of S&P 500 stocks trading above their 20-day Simple Moving Average (Short-term trend).")
mc2.metric("% > SMA 50", f"{breadth.pct_above_sma50:.1f}%", help="Percentage of S&P 500 stocks trading above their 50-day Simple Moving Average (Medium-term trend).")
mc3.metric("% > SMA 200", f"{breadth.pct_above_sma200:.1f}%", help="Percentage of S&P 500 stocks trading above their 200-day Simple Moving Average (Long-term trend).")
mc4.metric("Fear/Greed", f"{breadth.fear_greed_score:.0f}/100", help="A composite score (0-100) combining SMAs, new highs/lows, and volume breadth. Above 75 is Overbought, below 25 is Oversold.")
mc5.metric("VIX", f"{breadth.vix:.1f}", help="The CBOE Volatility Index (Fear Gauge). Values above 25-30 typically indicate market panic.")

st.markdown(f"<h3 style='color:{SLATE_800};margin-top:2rem;'>Core Sentiment</h3>", unsafe_allow_html=True)
fg_col, sma_col = st.columns(2)

with fg_col:
    # Spacer to align with the radio buttons in the right column
    st.markdown("<div style='height: 70px;'></div>", unsafe_allow_html=True)
    
    # 5-zone Fear & Greed gauge (matching standard infographic)
    fg_steps = [
        dict(range=[0, 20], color="#ef4444"),    # Extreme Fear (Red)
        dict(range=[20, 40], color="#fca5a5"),   # Fear (Light Red)
        dict(range=[40, 60], color="#e2e8f0"),   # Neutral (Grey)
        dict(range=[60, 80], color="#86efac"),   # Greed (Light Green)
        dict(range=[80, 100], color="#22c55e"),  # Extreme Greed (Green)
    ]
    fg_gauge = create_gauge_chart(
        value=breadth.fear_greed_score, 
        title="Fear & Greed Index", 
        steps=fg_steps, min_val=0, max_val=100
    )
    st.plotly_chart(fg_gauge, use_container_width=True)
    
    st.markdown(f"""
    <div class="card">
        <div style="font-weight:700;color:{TEAL};margin-bottom:.5rem">Indicator Meaning</div>
        <p style="font-size:.85rem;color:{SLATE_600};line-height:1.6;margin:0">
            A composite momentum score from 0-100 aggregating moving averages, extremes, and volume.<br>
            <b>0-20: Extreme Fear</b> (potential buy zone)<br>
            <b>80-100: Extreme Greed</b> (potential sell zone)
        </p>
    </div>
    """, unsafe_allow_html=True)

with sma_col:
    # --- Timeframe toggle ---
    tf = st.radio("Interactive SMA Trend", list(TIMEFRAME_CONFIG.keys()), horizontal=True)
    cfg = TIMEFRAME_CONFIG[tf]
    current_val = getattr(breadth, cfg["field"])

    sma_steps = [
        dict(range=[0, cfg["low"]], color="#dcfce7"),     # Oversold (Green Zone)
        dict(range=[cfg["low"], cfg["high"]], color="#f1f5f9"), # Neutral (Grey Zone)
        dict(range=[cfg["high"], 100], color="#fee2e2"),    # Overbought (Red Zone)
    ]
    sma_gauge = create_gauge_chart(
        value=current_val, 
        title=cfg["title"], 
        steps=sma_steps, min_val=0, max_val=100, suffix="%"
    )
    st.plotly_chart(sma_gauge, use_container_width=True)

    st.markdown(f"""
    <div class="card">
        <div style="font-weight:700;color:{TEAL};margin-bottom:.5rem">Operative Meaning</div>
        <p style="font-size:.85rem;color:{SLATE_600};line-height:1.6;margin:0">
            {cfg['usage']}<br>
            <span style="color:#94a3b8">Oversold: &lt;{cfg['low']}% | Overbought: &gt;{cfg['high']}%</span>
        </p>
    </div>
    """, unsafe_allow_html=True)

# --- Full indicators table ---
st.markdown("<div class='card-title' style='margin-top:1.5rem'>All Breadth Indicators</div>", unsafe_allow_html=True)
rows = []
color_map: dict[str, dict[str, str]] = {}
for ind in breadth.indicators:
    sv = ind.signal.value
    val_str = str(ind.value) if not isinstance(ind.value, float) else f"{ind.value:.2f}"
    rows.append({"Indicator": ind.name, "Value": val_str, "Signal": sv, "Action": ind.action, "Description": ind.description})
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
