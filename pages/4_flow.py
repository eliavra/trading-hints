import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from ui import load_css, TEAL, SLATE_800, SLATE_600, PLOTLY_LAYOUT
from data import compute_options_flow, get_sp500_tickers, get_nasdaq100_tickers

load_css()

st.title("Institutional Flow Analysis")

with st.sidebar:
    st.markdown(f"<div style='font-weight:700;color:{SLATE_800};margin-bottom:0.5rem'>Flow Filters</div>", unsafe_allow_html=True)
    market_view = st.selectbox("Select Index", ["S&P 500", "NASDAQ 100"])
    # Dropdown for threshold
    threshold_options = [0.0, 1.0, 5.0, 10.0, 25.0, 50.0, 100.0]
    min_premium_val = st.selectbox(
        "Min Net Impact Threshold", 
        threshold_options, 
        index=0, 
        format_func=lambda x: f"${x}M"
    )
    min_premium = min_premium_val * 1_000_000

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown(f"""
    <div class="card" style="height:100%; display:flex; flex-direction:column; justify-content:center; align-items:center; text-align:center;">
        <span class="material-symbols-rounded" style="font-size:3rem; color:#94a3b8; margin-bottom:1rem;">query_stats</span>
        <div style="font-weight:700;color:{SLATE_800};margin-bottom:.5rem">Live Options Flow</div>
        <p style="font-size:.85rem;color:{SLATE_600};line-height:1.6">
            Analyzing near-term options chain for the full index to find the top 10 extreme option volume targets.<br>
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
    
    # Get tickers based on selection
    if market_view == "S&P 500":
        watch_tickers = get_sp500_tickers()
    else:
        watch_tickers = get_nasdaq100_tickers()

    with st.spinner(f"Scanning live option chains for {len(watch_tickers)} tickers (takes ~15 seconds)..."):
        df = compute_options_flow(watch_tickers, max_expirations=1)
    
    if df is None or df.empty:
        st.warning("No options flow data available at this time.")
    else:
        # Filter based on absolute premium meeting the dropdown threshold
        df = df[df['Net_Premium'].abs() >= min_premium]
        
        # Rank by Volume/OI Ratio to find true unusual options activity independent of market cap
        df = df.nlargest(10, 'Vol_OI_Ratio')
        
        # Sort by Net_Premium for displaying the chart correctly (least to most for Plotly horizontal bars)
        df = df.sort_values(by='Net_Premium', ascending=True)
        
        if df.empty:
            st.info(f"No tickers meet the ${min_premium_val}M threshold.")
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
            
            st.markdown(f"<div style='margin-top:1.5rem;font-weight:700;color:{SLATE_800};margin-bottom:.5rem'>Unusual Flow Data (Top 10 by Vol/OI)</div>", unsafe_allow_html=True)
            
            # Format the dataframe for display
            disp_df = df[['Ticker', 'Net_Premium', 'Vol_OI_Ratio', 'Total_Volume', 'Total_OI']].copy()
            
            # Sort descending by Vol_OI_Ratio for the table
            disp_df = disp_df.sort_values(by='Vol_OI_Ratio', ascending=False)
            
            styled_df = disp_df.style.format({
                'Net_Premium': "${:,.0f}",
                'Vol_OI_Ratio': "{:.2f}x",
                'Total_Volume': "{:,.0f}",
                'Total_OI': "{:,.0f}"
            }).map(lambda x: 'color: #22c55e; font-weight: 600' if x > 0 else 'color: #ef4444; font-weight: 600', subset=['Net_Premium'])
            
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
