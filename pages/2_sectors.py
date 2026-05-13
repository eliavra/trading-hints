import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data import compute_sector_data
from ui import load_css, TEAL, SLATE_800, SLATE_600, PLOTLY_LAYOUT, signal_color, style_signal_cell

load_css()

st.title("Sector Rotation")

st.markdown(f"""
<div style="margin-bottom:1rem">
    <span style="font-size:1.2rem;font-weight:700;color:{SLATE_800}">Sector Rotation Radar</span>
    <span style="margin-left:12px;font-size:.85rem;color:#94a3b8">% deviation from 20-day SMA — red/green flags mark extremes</span>
</div>
""", unsafe_allow_html=True)

with st.spinner("Loading sector data..."):
    sectors = compute_sector_data()

# Sort sectors from least to most (ascending)
# Since Plotly autorange="reversed" is used, the first element (least) will appear at the top.
sectors.sort(key=lambda s: s.pct_vs_sma20, reverse=False)

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
    title="Sector % vs SMA 20",
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
        "Sector": s.name, "ETF": s.etf,
        "Price": f"${s.price:.2f}",
        "Day": s.perf_day, "1 Week": s.perf_1w,
        "2 Weeks": s.perf_2w, "3 Weeks": s.perf_3w,
        "Signal": sv,
    })
    sector_cmap[sv] = signal_color(s.signal)

df_s = pd.DataFrame(sector_rows)

def _color_perf(val: object) -> str:
    if not isinstance(val, (int, float)):
        return ""
    if val > 0:
        return "color: #166534; font-weight: 600"
    if val < 0:
        return "color: #991b1b; font-weight: 600"
    return ""

perf_cols = ["Day", "1 Week", "2 Weeks", "3 Weeks"]
styled_s = (
    df_s.style
    .format({c: "{:+.2%}" for c in perf_cols})
    .map(_color_perf, subset=perf_cols)
    .map(lambda v: style_signal_cell(v, sector_cmap) if v in sector_cmap else "", subset=["Signal"])
)
st.dataframe(styled_s, use_container_width=True, hide_index=True)
