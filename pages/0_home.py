import streamlit as st
from data import compute_market_breadth, compute_sector_data
from ui import load_css, SLATE_800, SLATE_600
from locales import t

load_css()

st.title(t("market_overview"))
st.markdown(f"<div style='font-size:1.1rem;color:{SLATE_600};margin-bottom:2rem;'>{t('market_overview_desc')}</div>", unsafe_allow_html=True)

with st.spinner(t("Loading market snapshot...")):
    breadth = compute_market_breadth()
    sectors = compute_sector_data()

# 1. High level metrics
st.markdown(f"<h3 style='color:{SLATE_800};'>{t('current_state')}</h3>", unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)

col1.metric(t("fear_greed_score"), f"{breadth.fear_greed_score:.0f}/100", help=t("fear_greed_score_help"))
col2.metric(t("vix"), f"{breadth.vix:.1f}", help=t("vix_help"))

trend_6m = breadth.ad_data.get("6M", {}).get("trend", "N/A")
col3.metric(t("ad_trend"), trend_6m, help=t("ad_trend_help"))

hot_sectors = [s for s in sectors if s.pct_vs_sma20 > 0.03]
hot_sectors.sort(key=lambda s: s.pct_vs_sma20, reverse=True)
top_sector = f"{hot_sectors[0].name} ({hot_sectors[0].etf})" if hot_sectors else "None"
col4.metric(t("leading_sector"), top_sector, help=t("leading_sector_help"))

st.divider()

# 2. Navigation Links
st.markdown(f"<h3 style='color:{SLATE_800};margin-bottom:1rem;'>{t('analysis_modules')}</h3>", unsafe_allow_html=True)

c1, c2 = st.columns(2)

with c1:
    with st.container(border=True):
        st.page_link("pages/1_sentiment.py", label=f"**{t('sentiment')}**", icon="📊")
        st.markdown(f"<div style='font-size:0.85rem;color:{SLATE_600};margin-top:0.5rem;'>{t('sentiment_desc')}</div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.page_link("pages/2_sectors.py", label=f"**{t('sectors')}**", icon="🔄")
        st.markdown(f"<div style='font-size:0.85rem;color:{SLATE_600};margin-top:0.5rem;'>{t('sectors_desc')}</div>", unsafe_allow_html=True)

with c2:
    with st.container(border=True):
        st.page_link("pages/4_risk.py", label=f"**{t('risk')}**", icon="⚡")
        st.markdown(f"<div style='font-size:0.85rem;color:{SLATE_600};margin-top:0.5rem;'>{t('risk_desc')}</div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.page_link("pages/3_seasonality.py", label=f"**{t('seasonality')}**", icon="🏹")
        st.markdown(f"<div style='font-size:0.85rem;color:{SLATE_600};margin-top:0.5rem;'>{t('seasonality_desc')}</div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.page_link("pages/5_about.py", label=f"**{t('about')}**", icon="ℹ️")
        st.markdown(f"<div style='font-size:0.85rem;color:{SLATE_600};margin-top:0.5rem;'>View version information and provide feedback.</div>", unsafe_allow_html=True)
