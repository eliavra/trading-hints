import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data import compute_market_breadth
from ui import load_css, TEAL, SLATE_800, SLATE_600, PLOTLY_LAYOUT, signal_color, style_signal_cell, create_gauge_chart

load_css()

st.title("Sentiment & Breadth")

with st.spinner("Loading S&P 500 data..."):
    breadth = compute_market_breadth()

mc1, mc2, mc3, mc4, mc5 = st.columns(5)
mc1.metric("% > SMA 20", f"{breadth.pct_above_sma20:.1f}%", help="Percentage of S&P 500 stocks trading above their 20-day Simple Moving Average (Short-term trend).")
mc2.metric("% > SMA 50", f"{breadth.pct_above_sma50:.1f}%", help="Percentage of S&P 500 stocks trading above their 50-day Simple Moving Average (Medium-term trend).")
mc3.metric("% > SMA 200", f"{breadth.pct_above_sma200:.1f}%", help="Percentage of S&P 500 stocks trading above their 200-day Simple Moving Average (Long-term trend).")
mc4.metric("Fear/Greed", f"{breadth.fear_greed_score:.0f}/100", help="A composite score (0-100) combining SMAs, new highs/lows, and volume breadth. Above 75 is Overbought, below 25 is Oversold.")
mc5.metric("VIX", f"{breadth.vix:.1f}", help="The CBOE Volatility Index (Fear Gauge). Values above 25-30 typically indicate market panic.")

chart_col, info_col = st.columns([2, 1])

with chart_col:
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

with info_col:
    st.markdown(f"""
    <div class="card" style="height:100%">
        <div style="font-weight:700;color:{TEAL};margin-bottom:.5rem">Indicator Meaning</div>
        <p style="font-size:.85rem;color:{SLATE_600};line-height:1.6">
            The Fear & Greed index is a composite momentum score from 0-100. It aggregates the internal breadth metrics (Moving Averages, New Highs/Lows, and Volume Ratio) to determine if the market is overextended.<br><br>
            <b>0-20: Extreme Fear</b> (Oversold, potential buy zone)<br>
            <b>20-40: Fear</b><br>
            <b>40-60: Neutral</b><br>
            <b>60-80: Greed</b><br>
            <b>80-100: Extreme Greed</b> (Overbought, potential sell zone)
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
