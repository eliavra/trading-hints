import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from ui import load_css, TEAL, SLATE_800, SLATE_600, PLOTLY_LAYOUT
from data import compute_options_flow

load_css()

st.title("Institutional Flow Analysis")

WATCHLIST = ['SPY', 'QQQ', 'NVDA', 'TSLA', 'AAPL', 'AMD', 'META', 'MSFT', 'AMZN', 'GOOGL', 'BRK-B', 'SMCI', 'PLTR', 'AVGO', 'COIN']

with st.sidebar:
    st.markdown(f"<div style='font-weight:700;color:{SLATE_800};margin-bottom:0.5rem'>Flow Filters</div>", unsafe_allow_html=True)
    min_premium = st.slider("Min Net Impact Threshold ($M)", 0.0, 100.0, 5.0, step=1.0) * 1_000_000

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown(f"""
    <div class="card" style="height:100%; display:flex; flex-direction:column; justify-content:center; align-items:center; text-align:center;">
        <span class="material-symbols-rounded" style="font-size:3rem; color:#94a3b8; margin-bottom:1rem;">query_stats</span>
        <div style="font-weight:700;color:{SLATE_800};margin-bottom:.5rem">Live Options Flow</div>
        <p style="font-size:.85rem;color:{SLATE_600};line-height:1.6">
            Analyzing near-term options chain for 15 mega-cap & high-beta targets. <br>
            <i>(SPY, QQQ, NVDA, TSLA, AAPL, etc.)</i>
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="margin-bottom:1rem">
        <span style="font-size:1.2rem;font-weight:700;color:{SLATE_800}">Top Net Impact (Front Month)</span>
        <span style="margin-left:12px;font-size:.85rem;color:#94a3b8">Bullish vs Bearish Premium</span>
    </div>
    """, unsafe_allow_html=True)
    
    with st.spinner("Scanning live option chains (this takes ~10-15 seconds)..."):
        df = compute_options_flow(WATCHLIST, max_expirations=1)
    
    if df.empty:
        st.warning("No options flow data available at this time.")
    else:
        # Filter based on absolute premium meeting the slider threshold
        df = df[df['Net_Premium'].abs() >= min_premium].sort_values(by='Net_Premium', ascending=True)
        
        if df.empty:
            st.info(f"No tickers meet the ${min_premium/1e6:.1f}M threshold.")
        else:
            # Apply SaaS unified colors
            df['Color'] = ['#ef4444' if x < 0 else '#22c55e' for x in df['Net_Premium']]
            
            # --- Create Plotly Figure ---
            fig = go.Figure(go.Bar(
                y=df['Ticker'],
                x=df['Net_Premium'],
                orientation='h',
                marker_color=df['Color'],
                text=[f"${x/1e6:.1f}M" for x in df['Net_Premium']],
                textposition='outside',
                cliponaxis=False
            ))

            # Apply our unified light theme PLOTLY_LAYOUT
            custom_layout = PLOTLY_LAYOUT.copy()
            custom_layout.update(
                margin=dict(l=0, r=40, t=20, b=0),
                xaxis=dict(showgrid=True, gridcolor='#e2e8f0', zerolinecolor='#94a3b8', title=""),
                yaxis=dict(showgrid=False),
                height=450
            )
            fig.update_layout(**custom_layout)
            
            st.plotly_chart(fig, use_container_width=True)
