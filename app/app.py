"""
app.py — Metro Manila Transportation Trend Dashboard
Styled with pink/purple glassmorphism UI inspired by uTask design
Run: streamlit run app/app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os, sqlite3

st.set_page_config(
    page_title="Metro Manila Transportation Dashboard",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC_DIR = os.path.join(BASE_DIR, "data", "processed")
DB_PATH  = os.path.join(BASE_DIR, "data", "metro_manila.db")

# ── Theme toggle ──────────────────────────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

# ── CSS ───────────────────────────────────────────────────────────────────────
def get_css(dark):
    bg_main    = "#13111C" if dark else "#F5F0FF"
    bg_sidebar = "#1A1628" if dark else "#FFFFFF"
    bg_card    = "rgba(255,255,255,0.05)" if dark else "rgba(255,255,255,0.85)"
    border_c   = "rgba(255,255,255,0.08)" if dark else "rgba(180,130,255,0.2)"
    text_main  = "#F0EAF8" if dark else "#1A1030"
    text_muted = "#9B89B4" if dark else "#7B6A94"
    tab_bg     = "rgba(255,255,255,0.04)" if dark else "rgba(180,130,255,0.08)"
    tab_active = "linear-gradient(135deg,#C850C0,#8A2BE2)" if dark else "linear-gradient(135deg,#C850C0,#8A2BE2)"
    input_bg   = "rgba(255,255,255,0.06)" if dark else "rgba(180,130,255,0.1)"

    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=DM+Sans:wght@300;400;500&display=swap');

/* ── Root reset ── */
html, body, [class*="css"] {{
    font-family: 'DM Sans', sans-serif;
    color: {text_main};
}}

/* ── App background ── */
.stApp {{
    background: {bg_main};
    background-image: radial-gradient(ellipse at 20% 0%, rgba(200,80,192,0.12) 0%, transparent 60%),
                      radial-gradient(ellipse at 80% 100%, rgba(138,43,226,0.10) 0%, transparent 60%);
}}

/* ── Sidebar ── */
[data-testid="stSidebar"] {{
    background: {bg_sidebar} !important;
    border-right: 1px solid {border_c};
}}
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown h1,
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 {{
    color: {text_main} !important;
}}

/* ── Hide default streamlit chrome ── */
#MainMenu, footer, header {{ visibility: hidden; }}
.block-container {{ padding: 1.5rem 2rem 2rem 2rem !important; }}

/* ── Metric cards ── */
.card {{
    background: {bg_card};
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid {border_c};
    border-radius: 20px;
    padding: 1.3rem 1.5rem;
    margin-bottom: 1rem;
    transition: transform 0.2s, box-shadow 0.2s;
    position: relative;
    overflow: hidden;
}}
.card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: var(--accent, linear-gradient(90deg,#C850C0,#8A2BE2));
    border-radius: 20px 20px 0 0;
}}
.card:hover {{ transform: translateY(-3px); box-shadow: 0 12px 40px rgba(200,80,192,0.15); }}
.card-label {{ font-size: 0.78rem; font-weight: 500; color: {text_muted}; text-transform: uppercase; letter-spacing: 0.08em; margin: 0; }}
.card-value {{ font-family: 'Outfit', sans-serif; font-size: 2rem; font-weight: 700; margin: 0.3rem 0 0.1rem; line-height: 1; }}
.card-sub   {{ font-size: 0.78rem; color: {text_muted}; margin: 0; }}
.card-icon  {{ position: absolute; right: 1.2rem; top: 1.2rem; font-size: 1.8rem; opacity: 0.25; }}

/* ── Section headers ── */
.sec-header {{
    font-family: 'Outfit', sans-serif;
    font-size: 1rem;
    font-weight: 600;
    color: {text_main};
    margin: 0 0 0.8rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}}
.sec-header::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: {border_c};
    margin-left: 0.5rem;
}}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {{
    gap: 0.4rem;
    background: {tab_bg};
    padding: 0.3rem;
    border-radius: 14px;
    border: 1px solid {border_c};
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 10px;
    padding: 0.5rem 1.2rem;
    font-family: 'DM Sans', sans-serif;
    font-weight: 500;
    font-size: 0.9rem;
    color: {text_muted};
    background: transparent;
    border: none;
    transition: all 0.2s;
}}
.stTabs [aria-selected="true"] {{
    background: {tab_active} !important;
    color: white !important;
    box-shadow: 0 4px 15px rgba(200,80,192,0.35);
}}
.stTabs [data-baseweb="tab-panel"] {{
    padding-top: 1.2rem;
}}

/* ── Slider ── */
.stSlider [data-baseweb="slider"] {{ padding: 0; }}

/* ── Dataframe ── */
.stDataFrame {{ border-radius: 12px; overflow: hidden; border: 1px solid {border_c}; }}

/* ── Sidebar nav items ── */
.nav-item {{
    display: flex;
    align-items: center;
    gap: 0.7rem;
    padding: 0.65rem 1rem;
    border-radius: 12px;
    margin: 0.2rem 0;
    cursor: pointer;
    font-size: 0.9rem;
    font-weight: 500;
    color: {text_muted};
    transition: all 0.2s;
}}
.nav-item:hover {{ background: rgba(200,80,192,0.1); color: {text_main}; }}
.nav-item.active {{
    background: linear-gradient(135deg,rgba(200,80,192,0.25),rgba(138,43,226,0.15));
    color: #C850C0;
    border: 1px solid rgba(200,80,192,0.2);
}}

/* ── Pill badge ── */
.badge {{
    display: inline-block;
    padding: 0.15rem 0.6rem;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    background: linear-gradient(135deg,#C850C0,#8A2BE2);
    color: white;
}}

/* ── Logo ── */
.logo-wrap {{
    display: flex;
    align-items: center;
    gap: 0.8rem;
    padding: 0.5rem 0 1.2rem;
    border-bottom: 1px solid {border_c};
    margin-bottom: 1rem;
}}
.logo-icon {{
    width: 38px; height: 38px;
    background: linear-gradient(135deg,#C850C0,#8A2BE2);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.2rem;
}}
.logo-text {{
    font-family: 'Outfit', sans-serif;
    font-weight: 700;
    font-size: 1.1rem;
    color: {text_main};
    line-height: 1.1;
}}
.logo-sub {{
    font-size: 0.72rem;
    color: {text_muted};
}}

/* ── Page title ── */
.page-title {{
    font-family: 'Outfit', sans-serif;
    font-size: 1.6rem;
    font-weight: 700;
    color: {text_main};
    margin: 0 0 0.2rem;
}}
.page-sub {{
    font-size: 0.85rem;
    color: {text_muted};
    margin: 0 0 1.5rem;
}}

/* ── Toggle button ── */
.stButton button {{
    background: linear-gradient(135deg,#C850C0,#8A2BE2) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    padding: 0.4rem 1rem !important;
    transition: all 0.2s !important;
}}
.stButton button:hover {{
    opacity: 0.9 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(200,80,192,0.4) !important;
}}
</style>
"""

st.markdown(get_css(st.session_state.dark_mode), unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load(fname):
    return pd.read_csv(os.path.join(PROC_DIR, fname))

incidents_monthly     = load("incidents_monthly.csv")
incidents_by_city     = load("incidents_by_city.csv")
incidents_by_type     = load("incidents_by_type.csv")
peak_heatmap          = load("peak_heatmap.csv")
peak_hourly           = load("peak_hourly.csv")
peak_locations        = load("peak_locations.csv")
ridership_annual      = load("ridership_annual.csv")
ridership_seasonality = load("ridership_seasonality.csv")
ridership_yoy         = load("ridership_yoy.csv")
ridership_recent      = load("ridership_recent.csv")

# ── Plot theme ────────────────────────────────────────────────────────────────
DARK = st.session_state.dark_mode
PT   = "plotly_dark" if DARK else "plotly_white"
PBGA = "rgba(0,0,0,0)"
PLOT_MARGIN = dict(t=15, b=40, l=10, r=10)
PINK  = "#C850C0"
PURPLE= "#8A2BE2"
BLUE  = "#4A9EFF"
TEAL  = "#2ECFB1"
GRAD  = [PINK, PURPLE]

def chart_layout(fig, h=300):
    fig.update_layout(
        height=h, template=PT,
        paper_bgcolor=PBGA, plot_bgcolor=PBGA,
        margin=PLOT_MARGIN,
        font=dict(family="DM Sans", size=12),
        legend=dict(orientation="h", y=1.12, font=dict(size=11)),
        xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)" if DARK else "rgba(0,0,0,0.05)"),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)" if DARK else "rgba(0,0,0,0.05)"),
    )
    return fig

def fmt_hour(h):
    h = int(h)
    if h == 0:  return "12 AM"
    if h < 12:  return f"{h} AM"
    if h == 12: return "12 PM"
    return f"{h-12} PM"

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="logo-wrap">
        <div class="logo-icon">🚦</div>
        <div>
            <div class="logo-text">MM Transit</div>
            <div class="logo-sub">Analytics Dashboard</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="nav-item active">📊 &nbsp; Dashboard</div>
    <div class="nav-item">🚗 &nbsp; Traffic Incidents</div>
    <div class="nav-item">🕐 &nbsp; Peak Hours</div>
    <div class="nav-item">🚇 &nbsp; MRT-3 Ridership</div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    dark_label = "☀️ Light Mode" if DARK else "🌙 Dark Mode"
    if st.button(dark_label, use_container_width=True):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="padding:0.8rem 1rem; background:rgba(200,80,192,0.08); border-radius:14px; border:1px solid rgba(200,80,192,0.15);">
        <div style="font-size:0.75rem; font-weight:600; color:#C850C0; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:0.5rem;">Data Sources</div>
        <div style="font-size:0.8rem; color:#9B89B4; line-height:1.7;">
            🚗 MMDA Incidents<br>2018 – 2020 · 17,312 rows<br><br>
            🚇 MRT-3 Ridership<br>1999 – 2025 · 8,999 rows
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="font-size:0.75rem; color:#9B89B4; text-align:center; line-height:1.8;">
        Built by <strong style="color:#C850C0;">Lea Nikka F. Perez</strong><br>
        PUP CpE · Big Data<br>
        Python · SQL · Streamlit · Plotly
    </div>
    """, unsafe_allow_html=True)

# ── Main content ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-title">Metro Manila Transportation Dashboard</div>
<div class="page-sub">Real-time insights on traffic incidents and MRT-3 ridership trends across Metro Manila</div>
""", unsafe_allow_html=True)

# ── Global KPI row ────────────────────────────────────────────────────────────
total_inc   = int(incidents_monthly["Total_Incidents"].sum())
total_acc   = int(incidents_monthly["Accidents"].sum())
peak_year_r = int(ridership_annual.loc[ridership_annual["Annual_Total"].idxmax(), "Year"])
peak_ann    = ridership_annual["Annual_Total"].max()
peak_hr_val = int(peak_hourly.loc[peak_hourly["Incidents"].idxmax(), "Hour"])

k1, k2, k3, k4 = st.columns(4)
cards = [
    (k1, "#C850C0", "🚨", "Total Incidents", f"{total_inc:,}", "MMDA 2018–2020"),
    (k2, "#8A2BE2", "💥", "Vehicular Accidents", f"{total_acc:,}", f"{total_acc/total_inc*100:.1f}% of incidents"),
    (k3, "#4A9EFF", "🚇", "MRT Peak Year", str(peak_year_r), f"{peak_ann/1e6:.1f}M annual riders"),
    (k4, "#2ECFB1", "🕐", "Busiest Hour", fmt_hour(peak_hr_val), "Most incidents recorded"),
]
for col, color, icon, label, value, sub in cards:
    with col:
        st.markdown(f"""
        <div class="card" style="--accent: linear-gradient(90deg,{color},{PURPLE});">
            <div class="card-icon">{icon}</div>
            <p class="card-label">{label}</p>
            <p class="card-value" style="color:{color}">{value}</p>
            <p class="card-sub">{sub}</p>
        </div>
        """, unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "🚗  Traffic Volume & Incidents",
    "🕐  Peak Hour Analysis",
    "🚇  MRT-3 Ridership Trends",
])

# TAB 1

with tab1:
    c1, c2 = st.columns([2, 1])

    with c1:
        st.markdown('<div class="sec-header">📈 Monthly Incident Trend</div>', unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=incidents_monthly["YearMonth"], y=incidents_monthly["Accidents"],
            name="Accidents", fill="tozeroy",
            line=dict(color=PINK, width=2.5),
            fillcolor=f"rgba(200,80,192,0.12)"
        ))
        fig.add_trace(go.Scatter(
            x=incidents_monthly["YearMonth"], y=incidents_monthly["Stalled"],
            name="Stalled Vehicles", fill="tozeroy",
            line=dict(color=BLUE, width=2.5),
            fillcolor="rgba(74,158,255,0.10)"
        ))
        chart_layout(fig, 300)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown('<div class="sec-header">🍩 Incident Types</div>', unsafe_allow_html=True)
        fig2 = px.pie(
            incidents_by_type, values="Count", names="Incident_Category",
            hole=0.6,
            color_discrete_sequence=[PINK, PURPLE, BLUE, TEAL]
        )
        fig2.update_traces(textposition="outside", textinfo="percent+label",
                           marker=dict(line=dict(color=PBGA, width=2)))
        fig2.update_layout(
            height=300, template=PT,
            paper_bgcolor=PBGA, margin=dict(t=15,b=15,l=0,r=0),
            font=dict(family="DM Sans"),
            showlegend=False,
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<div class="sec-header">🏙️ Incidents by City (Top 10)</div>', unsafe_allow_html=True)
    top10 = incidents_by_city.head(10)
    fig3 = px.bar(
        top10, x="City", y="Total_Incidents",
        color="Accidents",
        color_continuous_scale=[[0, PURPLE], [1, PINK]],
        text="Total_Incidents",
        labels={"Total_Incidents": "Total Incidents"}
    )
    fig3.update_traces(textposition="outside", textfont=dict(size=11), marker_line_width=0)
    fig3.update_coloraxes(colorbar=dict(title="Accidents", thickness=12, len=0.7))
    chart_layout(fig3, 340)
    st.plotly_chart(fig3, use_container_width=True)

# TAB 2
with tab2:
    low_hr = int(peak_hourly.loc[peak_hourly["Incidents"].idxmin(), "Hour"])
    busiest_loc = peak_locations.iloc[0]["Location"]

    k1, k2, k3 = st.columns(3)
    for col, color, icon, label, value, sub in [
        (k1, PINK,   "⚡", "Busiest Hour",    fmt_hour(peak_hr_val), f"{int(peak_hourly['Incidents'].max()):,} incidents"),
        (k2, TEAL,   "🌙", "Quietest Hour",   fmt_hour(low_hr),      "Fewest incidents recorded"),
        (k3, PURPLE, "📍", "Top Hotspot",     busiest_loc[:22]+"…" if len(busiest_loc)>22 else busiest_loc, peak_locations.iloc[0]["City"]),
    ]:
        with col:
            st.markdown(f"""
            <div class="card" style="--accent:linear-gradient(90deg,{color},{PURPLE});">
                <div class="card-icon">{icon}</div>
                <p class="card-label">{label}</p>
                <p class="card-value" style="color:{color}; font-size:1.5rem">{value}</p>
                <p class="card-sub">{sub}</p>
            </div>""", unsafe_allow_html=True)

    st.markdown('<div class="sec-header">🔥 Incident Heatmap — Hour × Day of Week</div>', unsafe_allow_html=True)
    day_order  = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    heat_pivot = peak_heatmap.pivot(index="DayOfWeek", columns="Hour", values="Incidents").reindex(day_order)
    fig4 = px.imshow(
        heat_pivot,
        color_continuous_scale=[[0,"#1A1628"],[0.3, PURPLE],[0.7, PINK],[1,"#FFD6F5"]],
        labels=dict(x="Hour", y="", color="Incidents"),
        aspect="auto"
    )
    fig4.update_xaxes(tickvals=list(range(0,24,2)), ticktext=[fmt_hour(h) for h in range(0,24,2)], tickangle=-30)
    fig4.update_layout(
        height=320, template=PT, paper_bgcolor=PBGA,
        margin=dict(t=15,b=50,l=10,r=10), font=dict(family="DM Sans"),
        coloraxis_colorbar=dict(thickness=12, len=0.8, title="")
    )
    st.plotly_chart(fig4, use_container_width=True)

    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown('<div class="sec-header">⏱️ Incidents by Hour</div>', unsafe_allow_html=True)
        fig5 = go.Figure()
        fig5.add_trace(go.Bar(
            x=peak_hourly["Hour"], y=peak_hourly["Incidents"],
            marker=dict(
                color=peak_hourly["Incidents"],
                colorscale=[[0, PURPLE],[1, PINK]],
                line=dict(width=0)
            ),
            text=peak_hourly["Incidents"], textposition="outside"
        ))
        for rush in [(6,9),(17,20)]:
            fig5.add_vrect(x0=rush[0]-0.5, x1=rush[1]-0.5,
                           fillcolor=f"rgba(200,80,192,0.09)", layer="below", line_width=0,
                           annotation_text="Rush Hour", annotation_position="top left",
                           annotation_font_color=PINK, annotation_font_size=10)
        fig5.update_xaxes(tickvals=list(range(0,24,2)), ticktext=[fmt_hour(h) for h in range(0,24,2)], tickangle=-30)
        chart_layout(fig5, 300)
        st.plotly_chart(fig5, use_container_width=True)

    with c2:
        st.markdown('<div class="sec-header">📍 Top Hotspot Locations</div>', unsafe_allow_html=True)
        fig6 = px.bar(
            peak_locations.head(10), x="Incidents", y="Location",
            orientation="h",
            color="Incidents",
            color_continuous_scale=[[0, PURPLE],[1, PINK]],
        )
        fig6.update_layout(
            height=300, template=PT, paper_bgcolor=PBGA, plot_bgcolor=PBGA,
            margin=dict(t=15,b=15,l=0,r=10), font=dict(family="DM Sans"),
            yaxis=dict(autorange="reversed"), coloraxis_showscale=False
        )
        st.plotly_chart(fig6, use_container_width=True)

# TAB 3
with tab3:
    yr_min = int(ridership_annual["Year"].min())
    yr_max = int(ridership_annual["Year"].max())
    year_range = st.slider("Filter year range", yr_min, yr_max, (2010, 2025))

    ra = ridership_annual[ridership_annual["Year"].between(*year_range)]
    rr = ridership_recent[ridership_recent["Year"].between(max(year_range[0],2019), year_range[1])]

    peak_yr   = ra.loc[ra["Annual_Total"].idxmax()]
    latest    = ra.iloc[-1]
    covid_pre = ridership_annual[ridership_annual["Year"]==2019]["Annual_Total"].values
    covid_val = ridership_annual[ridership_annual["Year"]==2020]["Annual_Total"].values
    covid_txt = f"{(1-covid_val[0]/covid_pre[0])*100:.0f}% drop vs 2019" if len(covid_pre) and len(covid_val) else "N/A"

    k1, k2, k3, k4 = st.columns(4)
    for col, color, icon, label, value, sub in [
        (k1, PINK,   "🏆", "Peak Year",       str(int(peak_yr["Year"])),      f"{peak_yr['Annual_Total']/1e6:.1f}M total riders"),
        (k2, TEAL,   "📅", "Avg Daily Riders", f"{latest['Avg_Daily']:,.0f}",  f"In {int(latest['Year'])}"),
        (k3, PURPLE, "😷", "COVID Impact",     "2020",                         covid_txt),
        (k4, BLUE,   "📆", "Years of Data",    "26 yrs",                       "1999 – 2025"),
    ]:
        with col:
            st.markdown(f"""
            <div class="card" style="--accent:linear-gradient(90deg,{color},{PURPLE});">
                <div class="card-icon">{icon}</div>
                <p class="card-label">{label}</p>
                <p class="card-value" style="color:{color}">{value}</p>
                <p class="card-sub">{sub}</p>
            </div>""", unsafe_allow_html=True)

    st.markdown('<div class="sec-header">📊 Annual Ridership & Year-over-Year Growth</div>', unsafe_allow_html=True)
    yoy_f = ridership_yoy[ridership_yoy["Year"].between(*year_range)]
    fig7  = make_subplots(specs=[[{"secondary_y": True}]])
    fig7.add_trace(go.Bar(
        x=ra["Year"], y=ra["Annual_Total"]/1e6,
        name="Annual (M)", marker=dict(
            color=ra["Annual_Total"],
            colorscale=[[0,PURPLE],[1,PINK]], line=dict(width=0)
        ), opacity=0.9
    ), secondary_y=False)
    fig7.add_trace(go.Scatter(
        x=yoy_f["Year"], y=yoy_f["YoY_Growth_Pct"],
        name="YoY Growth %", mode="lines+markers",
        line=dict(color=TEAL, width=2.5, dash="dot"),
        marker=dict(size=7, color=TEAL)
    ), secondary_y=True)
    fig7.update_yaxes(title_text="Riders (Millions)", secondary_y=False,
                      gridcolor="rgba(255,255,255,0.05)" if DARK else "rgba(0,0,0,0.05)")
    fig7.update_yaxes(title_text="YoY Growth %", secondary_y=True, showgrid=False)
    fig7.add_hline(y=0, secondary_y=True, line_dash="dot", line_color="rgba(200,200,200,0.3)")
    if year_range[0] <= 2020 <= year_range[1]:
        fig7.add_vrect(x0=2019.5, x1=2021.5, fillcolor="rgba(200,80,192,0.07)",
                       layer="below", line_width=0,
                       annotation_text="COVID-19", annotation_font_color=PINK,
                       annotation_position="top left", annotation_font_size=11)
    fig7.update_layout(
        height=360, template=PT, paper_bgcolor=PBGA, plot_bgcolor=PBGA,
        margin=PLOT_MARGIN, font=dict(family="DM Sans"),
        legend=dict(orientation="h", y=1.1)
    )
    st.plotly_chart(fig7, use_container_width=True)

    c1, c2 = st.columns([1,2])
    with c1:
        st.markdown('<div class="sec-header">🗓️ Monthly Seasonality</div>', unsafe_allow_html=True)
        fig8 = px.bar(
            ridership_seasonality, x="Month_Name", y="Avg_Monthly",
            color="Avg_Monthly",
            color_continuous_scale=[[0,PURPLE],[1,PINK]],
        )
        fig8.update_layout(coloraxis_showscale=False, xaxis_tickangle=-45)
        chart_layout(fig8, 300)
        st.plotly_chart(fig8, use_container_width=True)

    with c2:
        st.markdown('<div class="sec-header">📉 COVID Recovery (2019–Present)</div>', unsafe_allow_html=True)
        fig9 = px.line(
            rr, x="YearMonth", y="Total_Ridership",
            color="Year",
            color_discrete_sequence=px.colors.sequential.Plasma_r,
            markers=False
        )
        if year_range[0] <= 2020 <= year_range[1]:
            fig9.add_vrect(x0="2020-03", x1="2021-06",
                           fillcolor="rgba(200,80,192,0.08)", layer="below", line_width=0,
                           annotation_text="Lockdown", annotation_font_color=PINK,
                           annotation_position="top left")
        fig9.update_layout(xaxis_tickangle=-45)
        chart_layout(fig9, 300)
        st.plotly_chart(fig9, use_container_width=True)

    with st.expander("📄 View Raw Annual Data"):
        st.dataframe(
            ra[["Year","Annual_Total","Avg_Daily"]].assign(
                Annual_Total=lambda d: d["Annual_Total"].map("{:,.0f}".format),
                Avg_Daily=lambda d: d["Avg_Daily"].map("{:,.0f}".format),
            ).rename(columns={"Annual_Total":"Annual Riders","Avg_Daily":"Avg Daily Riders"}),
            use_container_width=True
        )
        