import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data import compute_market_breadth
from ui import load_css, TEAL, SLATE_800, SLATE_600, PLOTLY_LAYOUT, signal_color, style_signal_cell, create_gauge_chart
from locales import t

load_css()

st.title(t("sentiment"))
st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)

TIMEFRAME_CONFIG = {
    t("short_term"): {
        "field": "pct_above_sma20",
        "title": t("% Stocks Above SMA 20"),
        "low": 20, "high": 85,
        "calc": t("Percentage of S&P 500 stocks trading above their 20-day Simple Moving Average."),
        "usage": t("Above 85% — overbought, reduce longs / tighten stops. Below 20% — oversold, look for long entries. Between 70-85% — be selective."),
    },
    t("medium_term"): {
        "field": "pct_above_sma50",
        "title": t("% Stocks Above SMA 50"),
        "low": 30, "high": 85,
        "calc": t("Percentage of S&P 500 stocks trading above their 50-day Simple Moving Average."),
        "usage": t("The classic range for significant corrections. 85% is a red light — reduce exposure. Below 30% — green light, increase exposure."),
    },
    t("long_term"): {
        "field": "pct_above_sma200",
        "title": t("% Stocks Above SMA 200"),
        "low": 40, "high": 80,
        "calc": t("Percentage of S&P 500 stocks trading above their 200-day Simple Moving Average."),
        "usage": t("Defines Bull vs Bear market. Above 80% — strong bull, stay long. Below 40% — weak / bear, go defensive. Below 60% — tighten stops."),
    },
}

with st.spinner(t("Loading S&P 500 data...")):
    breadth = compute_market_breadth()

mc1, mc2, mc3, mc4, mc5 = st.columns(5)
mc1.metric(t("% > SMA 20"), f"{breadth.pct_above_sma20:.1f}%", help=t("pct_above_sma20_help"))
mc2.metric(t("% > SMA 50"), f"{breadth.pct_above_sma50:.1f}%", help=t("pct_above_sma50_help"))
mc3.metric(t("% > SMA 200"), f"{breadth.pct_above_sma200:.1f}%", help=t("pct_above_sma200_help"))
mc4.metric(t("fear_greed_score"), f"{breadth.fear_greed_score:.0f}/100", help=t("fear_greed_score_help"))
mc5.metric(t("vix"), f"{breadth.vix:.1f}", help=t("vix_help"))

st.markdown(f"<h3 style='color:{SLATE_800};margin-top:2rem;'>{t('core_sentiment')}</h3>", unsafe_allow_html=True)
fg_col, sma_col = st.columns(2)

with fg_col:
    # Spacer to align with the radio buttons in the right column
    st.markdown("<div style='height: 70px;'></div>", unsafe_allow_html=True)
    
    # 5-zone Fear & Greed gauge (matching standard infographic)
    fg_steps = [
        dict(range=[0, 20], color="#ef4444"),    # Extreme Fear (Red)
        dict(range=[20, 40], color="#fca5a5"),   # Fear (Light Red)
        dict(range=[40, 60], color="#e2e8f0"),   # Neutral (Grey)
        dict(range=[60, 80], color="#86efac"),   # Greed (Light Green)
        dict(range=[80, 100], color="#22c55e"),  # Extreme Greed (Green)
    ]
    fg_gauge = create_gauge_chart(
        value=breadth.fear_greed_score, 
        title=t("fear_greed_score"), 
        steps=fg_steps, min_val=0, max_val=100
    )
    st.plotly_chart(fg_gauge, use_container_width=True)
    
    st.markdown(f"""
    <div class="card">
        <div style="font-weight:700;color:{TEAL};margin-bottom:.5rem">{t('indicator_meaning')}</div>
        <p style="font-size:.85rem;color:{SLATE_600};line-height:1.6;margin:0">
            {t('fg_indicator_desc')}<br>
            <b>0-20: {t('extreme_fear')}</b><br>
            <b>80-100: {t('extreme_greed')}</b>
        </p>
    </div>
    """, unsafe_allow_html=True)

with sma_col:
    # --- Timeframe toggle ---
    tf = st.radio(t("interactive_sma"), list(TIMEFRAME_CONFIG.keys()), horizontal=True)
    cfg = TIMEFRAME_CONFIG[tf]
    current_val = getattr(breadth, cfg["field"])

    sma_steps = [
        dict(range=[0, cfg["low"]], color="#dcfce7"),     # Oversold (Green Zone)
        dict(range=[cfg["low"], cfg["high"]], color="#f1f5f9"), # Neutral (Grey Zone)
        dict(range=[cfg["high"], 100], color="#fee2e2"),    # Overbought (Red Zone)
    ]
    sma_gauge = create_gauge_chart(
        value=current_val, 
        title=cfg["title"], 
        steps=sma_steps, min_val=0, max_val=100, suffix="%"
    )
    st.plotly_chart(sma_gauge, use_container_width=True)

    st.markdown(f"""
    <div class="card">
        <div style="font-weight:700;color:{TEAL};margin-bottom:.5rem">{t('operative_meaning')}</div>
        <p style="font-size:.85rem;color:{SLATE_600};line-height:1.6;margin:0">
            {cfg['usage']}<br>
            <span style="color:#94a3b8">{t('oversold')}: &lt;{cfg['low']}% | {t('overbought')}: &gt;{cfg['high']}%</span>
        </p>
    </div>
    """, unsafe_allow_html=True)

# --- Full indicators table ---
st.markdown(f"<div class='card-title' style='margin-top:1.5rem'>{t('all_indicators')}</div>", unsafe_allow_html=True)

rows = []
color_map: dict[str, dict[str, str]] = {}
for ind in breadth.indicators:
    sv = ind.signal.value
    val_str = str(ind.value) if not isinstance(ind.value, float) else f"{ind.value:.2f}"
    
    # Use consistent keys for the dataframe
    rows.append({
        "indicator": t(ind.name),
        "value": val_str,
        "signal": t(sv),
        "action": t(ind.action),
        "description": t(ind.description)
    })
    color_map[t(sv)] = signal_color(ind.signal)

df_b = pd.DataFrame(rows)

# Professional Column Configuration
column_config = {
    "indicator": st.column_config.TextColumn(t("indicator"), width="medium"),
    "value": st.column_config.TextColumn(t("value"), width="small"),
    "signal": st.column_config.TextColumn(t("signal"), width="small"),
    "action": st.column_config.TextColumn(t("action"), width="medium"),
    "description": st.column_config.TextColumn(t("description"), width="large"),
}

styled = df_b.style.map(
    lambda v: style_signal_cell(v, color_map) if v in color_map else "", 
    subset=["signal"]
)

st.dataframe(
    styled,
    use_container_width=True,
    hide_index=True,
    column_config=column_config
)

# --- A/D Line chart ---
if breadth.ad_data:
    ad_period = st.radio(t("ad_timeframe"), list(breadth.ad_data.keys()), index=2, horizontal=True) # default 6M
    current_ad = breadth.ad_data[ad_period]
    ad_line = current_ad["ad_line"]
    ad_dates = current_ad["ad_dates"]
    ad_trend = current_ad["trend"]
    
    ad_fig = go.Figure(go.Scatter(
        x=ad_dates, y=ad_line,
        mode="lines", line=dict(color=TEAL, width=2),
        fill="tozeroy", fillcolor="rgba(13,148,136,0.06)",
    ))
    ad_fig.update_layout(
        title=f"{t('ad_line_title')} ({t('trend')}: {t(ad_trend)})",
        xaxis_title="", yaxis_title=t("Cumulative Net Advances"),
        height=340, **PLOTLY_LAYOUT,
    )
    st.plotly_chart(ad_fig, use_container_width=True)
