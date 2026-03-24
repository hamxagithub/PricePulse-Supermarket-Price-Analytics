"""
Streamlit theme and CSS styling for the dashboard.
Dark glassmorphism aesthetic with Inter font and Plotly dark template.
"""
import streamlit as st


def apply_theme():
    """Apply custom dark glassmorphism theme to Streamlit app."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

    /* ── CSS Variables ───────────────────────────────────── */
    :root {
        --bg-primary: #0f1016;
        --bg-secondary: #171821;
        --bg-card: rgba(23, 24, 33, 0.65);
        --bg-card-hover: rgba(30, 32, 45, 0.85);
        --glass-border: rgba(255, 255, 255, 0.08);
        --glass-border-hover: rgba(108, 92, 231, 0.4);
        --glass-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        
        --text-primary: #f8f9fa;
        --text-secondary: #adb5bd;
        --text-muted: #6c757d;

        --accent-1: #8c7ae6;
        --accent-2: #00cec9;
        --accent-gradient: linear-gradient(135deg, #8c7ae6 0%, #00cec9 100%);
        --glow-shadow: 0 0 20px rgba(140, 122, 230, 0.3);
    }

    /* ── Base Styles ─────────────────────────────────────── */
    .stApp {
        background: radial-gradient(circle at 15% 50%, rgba(140, 122, 230, 0.08), transparent 25%),
                    radial-gradient(circle at 85% 30%, rgba(0, 206, 201, 0.08), transparent 25%),
                    var(--bg-primary) !important;
        font-family: 'Outfit', -apple-system, sans-serif !important;
        color: var(--text-primary) !important;
    }

    .main .block-container {
        padding: 3rem 4rem !important;
        max-width: 1500px !important;
    }

    /* ── Sidebar ─────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: rgba(23, 24, 33, 0.8) !important;
        border-right: 1px solid var(--glass-border) !important;
        backdrop-filter: blur(20px) !important;
    }

    [data-testid="stSidebar"] div[data-testid="stText"] {
        font-family: 'Outfit', sans-serif !important;
    }

    /* ── Headers ─────────────────────────────────────────── */
    h1, h2, h3, h4, h5 {
        font-family: 'Outfit', sans-serif !important;
        color: var(--text-primary) !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
    }

    h1 {
        background: var(--accent-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.8rem !important;
        margin-bottom: 0.2rem !important;
        padding-bottom: 0.5rem !important;
    }

    h3 {
        font-size: 1.4rem !important;
        color: var(--text-primary) !important;
        border-bottom: 1px solid var(--glass-border);
        padding-bottom: 0.5rem;
        margin-top: 1.5rem !important;
        margin-bottom: 1rem !important;
    }

    /* ── Metric Cards ────────────────────────────────────── */
    [data-testid="stMetric"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 20px !important;
        padding: 1.5rem !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        box-shadow: var(--glass-shadow) !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        position: relative;
        overflow: hidden;
    }

    [data-testid="stMetric"]::before {
        content: '';
        position: absolute;
        top: 0; left: 0; width: 100%; height: 4px;
        background: var(--accent-gradient);
        opacity: 0.7;
        transition: opacity 0.3s ease;
    }

    [data-testid="stMetric"]:hover {
        transform: translateY(-5px) !important;
        background: var(--bg-card-hover) !important;
        border-color: var(--glass-border-hover) !important;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5), var(--glow-shadow) !important;
    }

    [data-testid="stMetric"]:hover::before {
        opacity: 1;
    }

    [data-testid="stMetric"] label {
        color: var(--text-secondary) !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }

    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: var(--text-primary) !important;
        font-weight: 800 !important;
        font-size: 2.2rem !important;
        letter-spacing: -0.03em !important;
        margin-top: 0.5rem !important;
    }

    /* ── Tabs ────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px !important;
        background: transparent !important;
        border-bottom: 1px solid var(--glass-border) !important;
        padding-bottom: 2px !important;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: var(--text-secondary) !important;
        border-radius: 8px 8px 0 0 !important;
        font-weight: 600 !important;
        padding: 0.8rem 1.5rem !important;
        transition: all 0.2s ease !important;
        border: 1px solid transparent !important;
        border-bottom: none !important;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: var(--text-primary) !important;
        background: rgba(255,255,255,0.03) !important;
    }

    .stTabs [aria-selected="true"] {
        background: var(--bg-card) !important;
        color: var(--accent-2) !important;
        border: 1px solid var(--glass-border) !important;
        border-bottom: none !important;
        box-shadow: 0 -4px 15px rgba(0,0,0,0.2) !important;
    }

    /* ── Selectbox / Inputs ────────────────────────────── */
    [data-baseweb="select"] > div,
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        background: var(--bg-card) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
        padding: 0.2rem 0.5rem !important;
        transition: all 0.2s ease !important;
        backdrop-filter: blur(10px) !important;
    }

    [data-baseweb="select"] > div:hover,
    .stTextInput > div > div > input:focus {
        border-color: var(--accent-1) !important;
        box-shadow: 0 0 0 1px var(--accent-1) !important;
    }

    /* ── DataFrames / Tables ─────────────────────────────── */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--glass-border) !important;
        border-radius: 16px !important;
        overflow: hidden !important;
        box-shadow: var(--glass-shadow) !important;
    }
    
    [data-testid="stDataFrame"] > div {
        background: var(--bg-card) !important;
    }

    /* ── Buttons ─────────────────────────────────────────── */
    .stButton > button {
        background: var(--accent-gradient) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        padding: 0.6rem 2rem !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        font-family: 'Outfit', sans-serif !important;
        letter-spacing: 0.5px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(140, 122, 230, 0.5) !important;
        filter: brightness(1.1) !important;
    }

    /* ── Expander ────────────────────────────────────────── */
    .streamlit-expanderHeader {
        background: var(--bg-card) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        padding: 1rem 1.2rem !important;
        transition: all 0.2s ease !important;
    }
    
    .streamlit-expanderHeader:hover {
        background: var(--bg-card-hover) !important;
        border-color: var(--glass-border-hover) !important;
    }

    /* ── Divider ─────────────────────────────────────────── */
    hr {
        border-color: var(--glass-border) !important;
        margin: 2.5rem 0 !important;
    }

    /* ── Plotly Charts Container ─────────────────────────── */
    [data-testid="stPlotlyChart"] {
        background: var(--bg-card) !important;
        border-radius: 20px !important;
        border: 1px solid var(--glass-border) !important;
        padding: 1rem !important;
        box-shadow: var(--glass-shadow) !important;
        backdrop-filter: blur(12px) !important;
        transition: transform 0.3s ease !important;
    }
    
    [data-testid="stPlotlyChart"]:hover {
        border-color: rgba(255, 255, 255, 0.15) !important;
    }

    /* ── Custom Cards in Store Comparison ────────────────── */
    div[style*="background:rgba(20,20,35,0.85)"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 20px !important;
        padding: 2rem !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        box-shadow: var(--glass-shadow) !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    }

    div[style*="background:rgba(20,20,35,0.85)"]:hover {
        transform: translateY(-5px) !important;
        background: var(--bg-card-hover) !important;
        border-color: var(--glass-border-hover) !important;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5), var(--glow-shadow) !important;
    }
    
    /* ── Scrollbar ───────────────────────────────────────── */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: var(--bg-primary); }
    ::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.15); border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.25); }

    </style>
    """, unsafe_allow_html=True)


# ── Plotly Template ───────────────────────────────────────────
PLOTLY_COLORS = [
    "#6c5ce7",  # Purple
    "#00cec9",  # Teal
    "#fd79a8",  # Pink
    "#fdcb6e",  # Yellow
    "#55efc4",  # Mint
    "#74b9ff",  # Blue
    "#e17055",  # Coral
    "#a29bfe",  # Light purple
    "#81ecec",  # Light teal
    "#fab1a0",  # Light coral
]

PLOTLY_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#e8eaed"),
    margin=dict(l=40, r=20, t=50, b=40),
    legend=dict(
        bgcolor="rgba(20,20,35,0.7)",
        bordercolor="rgba(255,255,255,0.08)",
        borderwidth=1,
        font=dict(size=11),
    ),
    colorway=PLOTLY_COLORS,
)


def styled_plotly(fig):
    """Apply consistent styling to a Plotly figure."""
    fig.update_layout(**PLOTLY_LAYOUT)
    fig.update_xaxes(
        gridcolor="rgba(255,255,255,0.05)",
        zerolinecolor="rgba(255,255,255,0.08)",
    )
    fig.update_yaxes(
        gridcolor="rgba(255,255,255,0.05)",
        zerolinecolor="rgba(255,255,255,0.08)",
    )
    return fig
