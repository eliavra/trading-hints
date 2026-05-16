import streamlit as st
import plotly.graph_objects as go
from data import compute_market_breadth
from ui import load_css, TEAL, SLATE_800, SLATE_600, PLOTLY_LAYOUT

load_css()

st.title("Volatility & Risk")
st.markdown(f"<div style='font-size:1.1rem;color:{SLATE_600};margin-bottom:2rem;'>Institutional risk management metrics including VIX Term Structure and Average True Range (ATR).</div>", unsafe_allow_html=True)

with st.spinner("Calculating risk metrics..."):
    breadth = compute_market_breadth()

c1, c2, c3 = st.columns(3)
c1.metric("VIX (30-Day)", f"{breadth.vix:.2f}")
c2.metric("VIX3M (90-Day)", f"{breadth.vix_3m:.2f}")
c3.metric("SPY ATR (14-Day)", f"{breadth.spy_atr_pct:.2f}%")

st.markdown(f"<h3 style='color:{SLATE_800};margin-top:2rem;'>VIX Term Structure</h3>", unsafe_allow_html=True)
term_col, info_col = st.columns([2, 1])

with term_col:
    # We plot the simple VIX curve
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=["1 Month (VIX)", "3 Months (VIX3M)", "6 Months (VIX6M)"],
        y=[breadth.vix, breadth.vix_3m, breadth.vix_6m],
        mode="lines+markers",
        line=dict(color="#ef4444" if breadth.vix > breadth.vix_3m else TEAL, width=3),
        marker=dict(size=10)
    ))
    
    status = "BACKWARDATION (Panic)" if breadth.vix > breadth.vix_3m else "CONTANGO (Normal)"
    fig.update_layout(
        title=f"Volatility Curve: {status}",
        yaxis_title="Expected Volatility",
        height=350, **PLOTLY_LAYOUT
    )
    st.plotly_chart(fig, use_container_width=True)

with info_col:
    st.markdown(f"""
    <div class="card" style="height:100%">
        <div style="font-weight:700;color:{TEAL};margin-bottom:.5rem">Term Structure Meaning</div>
        <p style="font-size:.85rem;color:{SLATE_600};line-height:1.6">
            In a healthy market, short-term volatility (VIX) is lower than long-term volatility (VIX3M/VIX6M) because the future is less certain. This is called <b>Contango</b>. <br><br>
            When short-term VIX spikes above 3M VIX, the market is in <b>Backwardation</b>. This indicates immediate, severe structural panic and often correlates with market bottoms.
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown(f"<h3 style='color:{SLATE_800};margin-top:2rem;'>Advanced Breadth Filters</h3>", unsafe_allow_html=True)

b1, b2 = st.columns(2)

with b1:
    st.markdown(f"""
    <div class="card">
        <div style="font-size:1.5rem;font-weight:700;color:{SLATE_800};margin-bottom:0.5rem">{breadth.mcclellan_osc:.1f}</div>
        <div style="font-weight:700;color:{TEAL};margin-bottom:.5rem">McClellan Oscillator (MCO)</div>
        <p style="font-size:.85rem;color:{SLATE_600};line-height:1.6">
            Measures the difference between 19-day and 39-day EMA of advancing minus declining issues. <br>
            <i>Above +50: Overbought</i><br>
            <i>Below -50: Oversold</i>
        </p>
    </div>
    """, unsafe_allow_html=True)

with b2:
    st.markdown(f"""
    <div class="card">
        <div style="font-size:1.5rem;font-weight:700;color:{SLATE_800};margin-bottom:0.5rem">{breadth.high_low_ratio:.1f}%</div>
        <div style="font-weight:700;color:{TEAL};margin-bottom:.5rem">High-Low Ratio</div>
        <p style="font-size:.85rem;color:{SLATE_600};line-height:1.6">
            New 52-Week Highs divided by total new extremes (Highs + Lows). <br>
            <i>Above 80%: Strong Uptrend</i><br>
            <i>Below 20%: Strong Downtrend</i>
        </p>
    </div>
    """, unsafe_allow_html=True)
