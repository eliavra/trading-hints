import streamlit as st
from data import compute_market_breadth, compute_sector_data
from ui import load_css, SLATE_800, SLATE_600

load_css()

st.title("Market Overview")
st.markdown(f"<div style='font-size:1.1rem;color:{SLATE_600};margin-bottom:2rem;'>High-level summary of current market conditions. Select a module below for deep-dive analysis.</div>", unsafe_allow_html=True)

with st.spinner("Loading market snapshot..."):
    breadth = compute_market_breadth()
    sectors = compute_sector_data()

# 1. High level metrics
st.markdown(f"<h3 style='color:{SLATE_800};'>Current State</h3>", unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)

col1.metric("Fear/Greed Score", f"{breadth.fear_greed_score:.0f}/100")
col2.metric("VIX", f"{breadth.vix:.1f}")

trend_6m = breadth.ad_data.get("6M", {}).get("trend", "N/A")
col3.metric("A/D Trend (6M)", trend_6m)

hot_sectors = [s for s in sectors if s.pct_vs_sma20 > 0.03]
hot_sectors.sort(key=lambda s: s.pct_vs_sma20, reverse=True)
top_sector = f"{hot_sectors[0].name} ({hot_sectors[0].etf})" if hot_sectors else "None"
col4.metric("Leading Sector", top_sector)

st.divider()

# 2. Navigation Links
st.markdown(f"<h3 style='color:{SLATE_800};margin-bottom:1rem;'>Analysis Modules</h3>", unsafe_allow_html=True)

c1, c2 = st.columns(2)

with c1:
    with st.container(border=True):
        st.page_link("pages/1_sentiment.py", label="**Sentiment & Breadth**", icon="📊")
        st.markdown(f"<div style='font-size:0.85rem;color:{SLATE_600};margin-top:0.5rem;'>Analyze internal market health via moving averages, net highs/lows, and advance-decline lines.</div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.page_link("pages/2_sectors.py", label="**Sector Rotation**", icon="🔄")
        st.markdown(f"<div style='font-size:0.85rem;color:{SLATE_600};margin-top:0.5rem;'>Track capital flows across the 11 S&P 500 sectors to identify emerging trends and exhaustion.</div>", unsafe_allow_html=True)

with c2:
    with st.container(border=True):
        st.page_link("pages/4_risk.py", label="**Volatility & Risk**", icon="⚡")
        st.markdown(f"<div style='font-size:0.85rem;color:{SLATE_600};margin-top:0.5rem;'>Monitor institutional risk metrics like the VIX Term Structure, SPY ATR, and McClellan Oscillator.</div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.page_link("pages/3_seasonality.py", label="**Seasonality Hunter**", icon="🏹")
        st.markdown(f"<div style='font-size:0.85rem;color:{SLATE_600};margin-top:0.5rem;'>Investigate 10-year historical win rates and expected returns for any ticker.</div>", unsafe_allow_html=True)
