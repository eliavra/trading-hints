import streamlit as st
from models import Signal

TEAL = "#0d9488"
SLATE_800 = "#1e293b"
SLATE_600 = "#475569"
SLATE_100 = "#f1f5f9"

SIGNAL_COLORS: dict[str, dict[str, str]] = {
    "red": {"bg": "#fee2e2", "fg": "#991b1b"},
    "green": {"bg": "#dcfce7", "fg": "#166534"},
    "yellow": {"bg": "#fef9c3", "fg": "#854d0e"},
}

RED_SIGNALS = {
    Signal.OVERBOUGHT, Signal.RED_LIGHT, Signal.WEAK_BEAR,
    Signal.EUPHORIA, Signal.DIVERGENCE, Signal.SELLING,
    Signal.COLD, Signal.BEARISH,
}
GREEN_SIGNALS = {
    Signal.OVERSOLD, Signal.GREEN_LIGHT, Signal.STRONG_BULL,
    Signal.FEAR, Signal.HEALTHY, Signal.BUYING,
    Signal.HOT, Signal.BULLISH,
}

PLOTLY_LAYOUT = dict(
    paper_bgcolor="white",
    plot_bgcolor="#f8fafc",
    font=dict(family="Inter, sans-serif", color=SLATE_600),
    title_font=dict(size=15, color=SLATE_800),
    margin=dict(t=45, b=40, l=50, r=20),
    xaxis=dict(gridcolor="#e2e8f0"),
    yaxis=dict(gridcolor="#e2e8f0"),
)

def load_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body { font-family: 'Inter', sans-serif; }
    h1, h2, h3, h4, h5, h6, p, label, .card, .metric-value { font-family: 'Inter', sans-serif !important; }
    .material-icons, .material-symbols-rounded { font-family: 'Material Symbols Rounded' !important; }

    /* header bar */
    header[data-testid="stHeader"] { background: white; border-bottom: 1px solid #e2e8f0; }

    /* sidebar */
    section[data-testid="stSidebar"] {
        background: white; border-right: 1px solid #e2e8f0;
    }
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 { color: #1e293b; }

    /* card helper */
    .card {
        background: white; border: 1px solid #e2e8f0; border-radius: 1rem;
        padding: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,.04);
    }
    .card-title { font-size: 1rem; font-weight: 700; color: #1e293b; margin-bottom: .75rem; }
    .card:hover { transform: translateY(-1px); transition: all .15s; }

    /* metric overrides */
    div[data-testid="stMetric"] {
        background: white; border: 1px solid #e2e8f0; border-radius: .75rem;
        padding: 1rem 1.25rem; box-shadow: 0 1px 2px rgba(0,0,0,.03);
    }
    div[data-testid="stMetric"] label { color: #64748b !important; font-size: .8rem; }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] { 
        color: #0f172a; font-weight: 700; white-space: normal !important; overflow-wrap: anywhere; line-height: 1.2; 
    }

    /* signal badge */
    .signal-badge {
        display: inline-block; padding: 4px 14px; border-radius: 9999px;
        font-weight: 700; font-size: .8rem; letter-spacing: .02em;
    }

    /* dataframe tweaks */
    div[data-testid="stDataFrame"] th { background-color: #f8fafc !important; }

    /* plotly bg */
    .js-plotly-plot .plotly .main-svg { border-radius: .75rem; }
    </style>
    """, unsafe_allow_html=True)

def signal_color(sig: Signal) -> dict[str, str]:
    if sig in RED_SIGNALS:
        return SIGNAL_COLORS["red"]
    if sig in GREEN_SIGNALS:
        return SIGNAL_COLORS["green"]
    return SIGNAL_COLORS["yellow"]

def signal_badge(sig: Signal) -> str:
    c = signal_color(sig)
    return f"<span class='signal-badge' style='background:{c['bg']};color:{c['fg']}'>{sig.value}</span>"

def style_signal_cell(val: str, cmap: dict[str, dict[str, str]]) -> str:
    c = cmap.get(val, SIGNAL_COLORS["yellow"])
    return f"background-color: {c['bg']}; color: {c['fg']}; font-weight: 700; border-radius: 4px"
