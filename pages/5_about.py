import streamlit as st
from ui import load_css, SLATE_800, SLATE_600, TEAL
from locales import t

load_css()

st.title(t("about"))

st.markdown(f"""
<div class="card">
    <h3 style='color:{SLATE_800};'>{t('app_title')}</h3>
    <p style='color:{SLATE_600}; line-height:1.6;'>
        {t('about_desc')}
    </p>
    <div style='margin-top:1.5rem; padding-top:1rem; border-top:1px solid #e2e8f0;'>
        <p><b>{t('version')}:</b> 1.0.0</p>
        <p><b>{t('repository')}:</b> <a href="https://github.com/eliavra/trading-hints" target="_blank" style="color:{TEAL}; text-decoration:none;">github.com/eliavra/trading-hints</a></p>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"<h3 style='color:{SLATE_800}; margin-top:2rem;'>{t('feedback')}</h3>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown(f"""
    <div style='display:flex; align-items:center; gap:1.5rem;'>
        <span class="material-symbols-rounded" style="font-size:3rem; color:{TEAL};">chat_bubble</span>
        <div>
            <p style='color:{SLATE_600}; margin:0;'>{t('feedback_desc')}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
