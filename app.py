import streamlit as st
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from ui import TEAL, SLATE_800

st.set_page_config(page_title="Exposure Dashboard", layout="wide", initial_sidebar_state="expanded")

# Define pages
page_sentiment = st.Page("pages/1_sentiment.py", title="Sentiment & Breadth", icon="📊")
page_sectors = st.Page("pages/2_sectors.py", title="Sector Rotation", icon="🔄")
page_seasonality = st.Page("pages/3_seasonality.py", title="Seasonality Hunter", icon="🏹")

pg = st.navigation([page_sentiment, page_sectors, page_seasonality])

# Global Sidebar
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
    
    # Seasonality Ticker - Initialize in session state if not present
    if "ticker_input" not in st.session_state:
        st.session_state["ticker_input"] = "TSLA"
        
    st.session_state["ticker_input"] = st.text_input("Seasonality Ticker", value=st.session_state["ticker_input"]).upper().strip()

    st.divider()
    st.markdown(f"<div style='font-size:.75rem;color:#94a3b8'>Last refresh: {datetime.now().strftime('%H:%M:%S')}</div>", unsafe_allow_html=True)

pg.run()
