import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data import compute_sector_data
from ui import load_css, TEAL, SLATE_800, SLATE_600, PLOTLY_LAYOUT, signal_color, style_signal_cell
from locales import t

load_css()

st.title(t("sectors"))

st.markdown(f"""
<div style="margin-bottom:1rem">
    <span style="font-size:1.2rem;font-weight:700;color:{SLATE_800}">{t('sector_radar')}</span>
    <span style="margin-left:12px;font-size:.85rem;color:#94a3b8">{t('sector_radar_desc')}</span>
</div>
""", unsafe_allow_html=True)

with st.spinner(t("loading_sectors")):
    sectors = compute_sector_data()

# Sort sectors from most positive to most negative (descending)
# With Plotly autorange="reversed", the first element (most positive) will appear at the top.
sectors.sort(key=lambda s: s.pct_vs_sma20, reverse=True)

bar_colors = []
for s in sectors:
    if s.pct_vs_sma20 > 0.03:
        bar_colors.append("#22c55e")
    elif s.pct_vs_sma20 < -0.03:
        bar_colors.append("#ef4444")
    else:
        bar_colors.append("#94a3b8")

sfig = go.Figure(go.Bar(
    y=[f"{s.name} ({s.etf})" for s in sectors],
    x=[s.pct_vs_sma20 * 100 for s in sectors],
    marker_color=bar_colors,
    text=[f"{s.pct_vs_sma20:.1%}" for s in sectors],
    textposition="outside",
    orientation="h",
))
sfig.update_layout(
    title=t("sector_vs_sma20"),
    xaxis_title="% vs SMA 20", yaxis_title="",
    height=450, **PLOTLY_LAYOUT,
)
sfig.update_yaxes(autorange="reversed")
sfig.add_vline(x=3, line_dash="dash", line_color="#22c55e", opacity=0.5)
sfig.add_vline(x=-3, line_dash="dash", line_color="#ef4444", opacity=0.5)
st.plotly_chart(sfig, use_container_width=True)

sector_rows = []
sector_cmap: dict[str, dict[str, str]] = {}
for s in sectors:
    sv = s.signal.value
    sector_rows.append({
        "sector": s.name, 
        "etf": s.etf,
        "price": s.price,
        "day": s.perf_day, 
        "1w": s.perf_1w,
        "2w": s.perf_2w, 
        "3w": s.perf_3w,
        "signal": t(sv),
    })
    sector_cmap[t(sv)] = signal_color(s.signal)

df_s = pd.DataFrame(sector_rows)

# Professional Column Configuration
sec_column_config = {
    "sector": st.column_config.TextColumn(t("Sector"), width="medium"),
    "etf": st.column_config.TextColumn(t("ETF"), width="small"),
    "price": st.column_config.NumberColumn(t("Price"), format="$%.2f", width="small"),
    "day": st.column_config.NumberColumn(t("Day"), format="%.2%"),
    "1w": st.column_config.NumberColumn(t("1 Week"), format="%.2%"),
    "2w": st.column_config.NumberColumn(t("2 Weeks"), format="%.2%"),
    "3w": st.column_config.NumberColumn(t("3 Weeks"), format="%.2%"),
    "signal": st.column_config.TextColumn(t("Signal"), width="small"),
}

def _color_perf(val: object) -> str:
    if not isinstance(val, (int, float)):
        return ""
    if val > 0:
        return "color: #166534; font-weight: 600"
    if val < 0:
        return "color: #991b1b; font-weight: 600"
    return ""

perf_keys = ["day", "1w", "2w", "3w"]
styled_s = (
    df_s.style
    .map(_color_perf, subset=perf_keys)
    .map(lambda v: style_signal_cell(v, sector_cmap) if v in sector_cmap else "", subset=["signal"])
)

st.dataframe(
    styled_s, 
    use_container_width=True, 
    hide_index=True,
    column_config=sec_column_config
)
