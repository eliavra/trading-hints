import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from ui import load_css, TEAL, SLATE_800, SLATE_600, PLOTLY_LAYOUT

load_css()

st.title("Institutional Flow Analysis")

with st.sidebar:
    st.markdown(f"<div style='font-weight:700;color:{SLATE_800};margin-bottom:0.5rem'>Flow Filters</div>", unsafe_allow_html=True)
    market_view = st.selectbox("Select Index", ["S&P 500", "NASDAQ 100"])
    min_premium = st.slider("Min Whale Premium ($)", 100_000, 10_000_000, 1_000_000, step=100_000)

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown(f"""
    <div class="card" style="height:100%; display:flex; flex-direction:column; justify-content:center; align-items:center; text-align:center;">
        <span class="material-symbols-rounded" style="font-size:3rem; color:#94a3b8; margin-bottom:1rem;">query_stats</span>
        <div style="font-weight:700;color:{SLATE_800};margin-bottom:.5rem">Live Options Flow</div>
        <p style="font-size:.85rem;color:{SLATE_600};line-height:1.6">
            Detailed flow metrics and sweep analysis will populate here.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="margin-bottom:1rem">
        <span style="font-size:1.2rem;font-weight:700;color:{SLATE_800}">Top Net Impact</span>
        <span style="margin-left:12px;font-size:.85rem;color:#94a3b8">Bullish vs Bearish Premium</span>
    </div>
    """, unsafe_allow_html=True)
    
    # --- Data Logic (Placeholder for Flow API results) ---
    data = {
        'Ticker': ['NVDA', 'BABA', 'MRVL', 'TLT', 'LITE', 'META', 'MSFT', 'AMD', 'QQQ', 'TSLA', 'SNDK'],
        'Net_Premium': [22.5e6, 8.2e6, 7.5e6, 5.1e6, 4.8e6, 2.5e6, -4.1e6, -6.2e6, -7.5e6, -10.8e6, -11.5e6]
    }
    df = pd.DataFrame(data)
    
    # Filter based on absolute premium meeting the slider threshold
    df = df[df['Net_Premium'].abs() >= min_premium].sort_values(by='Net_Premium', ascending=True)
    
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
