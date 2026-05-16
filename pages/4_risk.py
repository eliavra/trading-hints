import streamlit as st
import plotly.graph_objects as go
from data import compute_market_breadth
from ui import load_css, TEAL, SLATE_800, SLATE_600, PLOTLY_LAYOUT, create_gauge_chart
from locales import t

load_css()

st.title(t("risk"))
st.markdown(f"<div style='font-size:1.1rem;color:{SLATE_600};margin-bottom:2rem;'>{t('risk_desc')}</div>", unsafe_allow_html=True)

with st.spinner(t("Calculating risk metrics...")):
    breadth = compute_market_breadth()

c1, c2, c3 = st.columns(3)
c1.metric(t("vix") + " (30-Day)", f"{breadth.vix:.2f}", help=t("vix_help"))
c2.metric("VIX3M (90-Day)", f"{breadth.vix_3m:.2f}", help=t("VIX3M represents expected 90-day market volatility."))
c3.metric(t("spy_atr"), f"{breadth.spy_atr_pct:.2f}%", help=t("spy_atr_help"))

st.markdown(f"<h3 style='color:{SLATE_800};margin-top:2rem;'>{t('vix_term_structure')}</h3>", unsafe_allow_html=True)
term_col, info_col = st.columns([2, 1])

with term_col:
    # We plot the simple VIX curve
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[t("1 Month (VIX)"), t("3 Months (VIX3M)"), t("6 Months (VIX6M)")],
        y=[breadth.vix, breadth.vix_3m, breadth.vix_6m],
        mode="lines+markers",
        line=dict(color="#ef4444" if breadth.vix > breadth.vix_3m else TEAL, width=3),
        marker=dict(size=10)
    ))
    
    status = t("backwardation") if breadth.vix > breadth.vix_3m else t("contango")
    fig.update_layout(
        title=f"{t('Volatility Curve')}: {status}",
        yaxis_title=t("Expected Volatility"),
        height=350, **PLOTLY_LAYOUT
    )
    st.plotly_chart(fig, use_container_width=True)

with info_col:
    st.markdown(f"""
    <div class="card" style="height:100%">
        <div style="font-weight:700;color:{TEAL};margin-bottom:.5rem">{t('Term Structure Meaning')}</div>
        <p style="font-size:.85rem;color:{SLATE_600};line-height:1.6">
            {t('vix_term_structure_desc')}
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown(f"<h3 style='color:{SLATE_800};margin-top:2rem;'>{t('advanced_breadth')}</h3>", unsafe_allow_html=True)

b1, b2 = st.columns(2)

with b1:
    mco_steps = [
        dict(range=[-100, -50], color="#ef4444"),  # Oversold (Red)
        dict(range=[-50, 0], color="#fca5a5"),     # Negative (Light Red)
        dict(range=[0, 50], color="#86efac"),      # Positive (Light Green)
        dict(range=[50, 100], color="#22c55e"),    # Overbought (Green)
    ]
    mco_gauge = create_gauge_chart(
        value=breadth.mcclellan_osc,
        title=t("mco"),
        steps=mco_steps, min_val=-100, max_val=100
    )
    st.plotly_chart(mco_gauge, use_container_width=True)
    
    st.markdown(f"""
    <div class="card">
        <p style="font-size:.85rem;color:{SLATE_600};line-height:1.6;margin:0">
            <b>{t('Meaning')}:</b> {t('mco_desc')}
        </p>
    </div>
    """, unsafe_allow_html=True)

with b2:
    hl_steps = [
        dict(range=[0, 20], color="#ef4444"),    # Strong Bear (Red)
        dict(range=[20, 50], color="#fca5a5"),   # Weak Bear (Light Red)
        dict(range=[50, 80], color="#86efac"),   # Weak Bull (Light Green)
        dict(range=[80, 100], color="#22c55e"),  # Strong Bull (Green)
    ]
    hl_gauge = create_gauge_chart(
        value=breadth.high_low_ratio,
        title=t("hl_index"),
        steps=hl_steps, min_val=0, max_val=100
    )
    st.plotly_chart(hl_gauge, use_container_width=True)
    
    st.markdown(f"""
    <div class="card">
        <p style="font-size:.85rem;color:#475569;line-height:1.6;margin:0">
            <b>{t('Meaning')}:</b> {t('hl_index_desc')}
        </p>
    </div>
    """, unsafe_allow_html=True)
