import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from data import fetch_tv_breadth_data, fetch_historical_sectors, fetch_vix, fetch_ticker_history
from calculations import (
    compute_breadth_metrics, 
    compute_fear_greed_score, 
    compute_ad_line, 
    compute_sector_metrics,
    compute_seasonality
)

# 1. Page Configuration
st.set_page_config(page_title="Exposure Manager | Quantitative Dashboard", layout="wide", page_icon="📊")

# 2. Custom UI Styling (Design System)
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        /* Global Typography */
        html, body, [class*="st-"] {
            font-family: 'Inter', sans-serif;
            background-color: #f8fafc;
        }
        
        /* Sidebar Logo & Branding */
        .sidebar-logo {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 0 20px 0;
        }
        .logo-box {
            background: #0d9488;
            color: white;
            width: 36px;
            height: 36px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 20px;
        }
        .brand-name {
            font-weight: 700;
            font-size: 20px;
            color: #1e293b;
        }

        /* Card System */
        .card {
            background: white;
            padding: 24px;
            border-radius: 16px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
            transition: transform 0.2s ease;
        }
        .card:hover {
            transform: translateY(-1px);
        }

        /* Metric Styling */
        [data-testid="stMetric"] {
            background: white;
            padding: 16px;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
        }

        /* Tab Styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            font-weight: 500;
            color: #64748b;
        }
        .stTabs [aria-selected="true"] {
            color: #0d9488 !important;
            border-bottom: 2px solid #0d9488 !important;
        }

        /* Signal Badges */
        .signal-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .status-hot { background: #dcfce7; color: #166534; }
        .status-cold { background: #fee2e2; color: #991b1b; }
        .status-neutral { background: #f1f5f9; color: #475569; }
    </style>
""", unsafe_allow_html=True)

# 3. Sidebar Configuration
with st.sidebar:
    st.markdown("""
        <div class="sidebar-logo">
            <div class="logo-box">Q</div>
            <div class="brand-name">Exposure Manager</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    refresh_interval = st.select_slider(
        "Auto-refresh Interval",
        options=[1, 5, 15, 30, 60],
        value=5,
        help="Minutes between automatic data updates."
    )
    
    st_autorefresh(interval=refresh_interval * 60 * 1000, key="datarefresh")
    
    st.markdown("### Global Controls")
    if st.button("🔄 Manual Refresh"):
        st.cache_data.clear()
        st.rerun()
    
    st.divider()
    st.info("Market data via TradingView Scanner & Yahoo Finance.")

# 4. Global Plotly Layout
PLOTLY_LAYOUT = dict(
    template="plotly_white",
    font=dict(family="Inter, sans-serif"),
    margin=dict(l=20, r=20, t=40, b=20),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    xaxis=dict(gridcolor='#e2e8f0'),
    yaxis=dict(gridcolor='#e2e8f0')
)

# 5. Data Engine
@st.cache_data(ttl=300)
def get_dashboard_data():
    tv_data = fetch_tv_breadth_data()
    sector_hist = fetch_historical_sectors(6)
    vix = fetch_vix()
    return tv_data, sector_hist, vix

tv_df, sector_df, vix_val = get_dashboard_data()

# 6. Main Tabs
tab1, tab2, tab3 = st.tabs(["📊 Sentiment & Breadth", "🔄 Sector Rotation", "🏹 Seasonality Hunter"])

with tab1:
    breadth = compute_breadth_metrics(tv_df)
    fg_score = compute_fear_greed_score(breadth)
    ad_df = compute_ad_line(sector_df)
    
    # Status Header
    status_label = "HEALTHY" if fg_score > 60 else ("OVERSOLD" if fg_score < 35 else "NEUTRAL")
    status_class = "status-hot" if status_label == "HEALTHY" else ("status-cold" if status_label == "OVERSOLD" else "status-neutral")
    
    st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 24px;">
            <h2 style="margin:0;">Market Sentiment</h2>
            <span class="signal-badge {status_class}">{status_label}</span>
        </div>
    """, unsafe_allow_html=True)

    # Metrics Row
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Fear/Greed Index", f"{fg_score}", delta=None)
    m2.metric("VIX Index", f"{vix_val:.2f}", delta=None, delta_color="inverse")
    m3.metric("Net New Highs", breadth.get('nh_nl', 0))
    m4.metric("Vol Up/Down", f"{breadth.get('vol_ratio', 1.0):.2f}")
    m5.metric("% > SMA 50", f"{breadth.get('sma50_pct', 0):.1f}%")

    # Main Chart Row
    c1, c2 = st.columns([2.5, 1])
    
    with c1:
        st.subheader("Cumulative Advance/Decline Line")
        if not ad_df.empty:
            fig_ad = go.Figure()
            fig_ad.add_trace(go.Scatter(x=ad_df.index, y=ad_df['ad_line'], name="A/D Line", line=dict(color='#0d9488', width=2.5)))
            fig_ad.add_trace(go.Scatter(x=ad_df.index, y=ad_df['ad_sma'], name="10D SMA", line=dict(color='#f59e0b', width=1.5, dash='dot')))
            fig_ad.update_layout(**PLOTLY_LAYOUT, height=450)
            st.plotly_chart(fig_ad, use_container_width=True)
            
    with c2:
        st.subheader("Breadth Analysis")
        breadth_table = pd.DataFrame({
            "Metric": ["Price > SMA 20", "Price > SMA 50", "Price > SMA 200"],
            "Market %": [f"{breadth.get('sma20_pct'):.1f}%", f"{breadth.get('sma50_pct'):.1f}%", f"{breadth.get('sma200_pct'):.1f}%"]
        })
        st.table(breadth_table)
        
        # Gauge Chart for Fear/Greed
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = fg_score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Sentiment Gauge", 'font': {'size': 16}},
            gauge = {
                'axis': {'range': [0, 100], 'tickwidth': 1},
                'bar': {'color': "#0d9488"},
                'steps': [
                    {'range': [0, 30], 'color': "#fee2e2"},
                    {'range': [30, 70], 'color': "#f1f5f9"},
                    {'range': [70, 100], 'color': "#dcfce7"}
                ],
            }
        ))
        fig_gauge.update_layout(template="plotly_white", margin=dict(l=10, r=10, t=40, b=10), height=250)
        st.plotly_chart(fig_gauge, use_container_width=True)

with tab2:
    st.header("Sector Rotation Engine")
    if not sector_df.empty:
        sector_metrics = compute_sector_metrics(tv_df, sector_df)
        
        # Table Styling
        def style_sectors(df):
            return df.style.format("{:.2f}%", subset=['Dist SMA20 %', '1D %', '1W %', '2W %', '3W %'])\
                     .map(lambda x: 'background-color: #dcfce7; color: #166534' if x == "HOT" else 
                                 ('background-color: #fee2e2; color: #991b1b' if x == "COLD" else ''), subset=['Status'])

        st.dataframe(style_sectors(sector_metrics), use_container_width=True, height=450)
        
        # Rotation Scatter
        st.subheader("Relative Momentum Matrix")
        fig_rot = px.scatter(
            sector_metrics, x="3W %", y="1W %", text=sector_metrics.index,
            size=sector_metrics["Dist SMA20 %"].abs() + 10,
            color="Dist SMA20 %", color_continuous_scale="RdYlGn",
            labels={"Dist SMA20 %": "Dist to SMA20 (%)", "3W %": "3-Week Return", "1W %": "1-Week Return"}
        )
        fig_rot.add_hline(y=0, line_dash="dash", line_color="#94a3b8")
        fig_rot.add_vline(x=0, line_dash="dash", line_color="#94a3b8")
        fig_rot.update_layout(**PLOTLY_LAYOUT, height=550)
        st.plotly_chart(fig_rot, use_container_width=True)

with tab3:
    st.header("Seasonality Explorer")
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        col_search, col_info = st.columns([1, 2])
        with col_search:
            season_ticker = st.text_input("Lookup Symbol", value="SPY", placeholder="AAPL, TSLA, BTC-USD").upper()
        with col_info:
            st.markdown(f"**Analyzing:** {season_ticker} | **Window:** 10 Years Weekly Data")
        st.markdown('</div>', unsafe_allow_html=True)
    
    if season_ticker:
        hist = fetch_ticker_history(season_ticker)
        if not hist.empty:
            stats = compute_seasonality(hist)
            
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Monthly Historical Returns")
                m_df = stats['monthly'].reset_index()
                fig_m = px.bar(m_df, x='Month', y='Avg Return', color='Win Rate',
                              color_continuous_scale='RdYlGn', labels={'Avg Return': 'Avg Return (%)'})
                fig_m.update_layout(**PLOTLY_LAYOUT)
                st.plotly_chart(fig_m, use_container_width=True)
                
            with c2:
                st.subheader("Weekly Probability of Profit")
                w_df = stats['weekly'].reset_index()
                fig_w = px.line(w_df, x='Week', y='Win Rate', line_shape='spline', line=dict(color='#0d9488', width=3))
                fig_w.add_hline(y=50, line_dash="dash", line_color="#94a3b8")
                fig_w.update_layout(**PLOTLY_LAYOUT)
                st.plotly_chart(fig_w, use_container_width=True)
                
            st.subheader("Statistical Raw Data")
            st.dataframe(stats['monthly'].style.format("{:.2f}%"), use_container_width=True)
        else:
            st.error("Invalid symbol or data unavailable for this ticker.")
