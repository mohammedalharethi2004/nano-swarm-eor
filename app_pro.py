import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import interp1d
import time, random, datetime
from scipy.ndimage import gaussian_filter

# --- Streamlit Page Configuration ---
st.set_page_config(layout="wide", page_title="Nano-Swarm EOR Command Center", page_icon="🌌")

# --- Define Constants for Colors (Python-accessible) ---
COLOR_PRIMARY = "#00ffcc"
COLOR_SECONDARY = "#00ccff"
COLOR_BG_DARK = "#0a0a1a"
COLOR_BG_MEDIUM = "#1a1a3a"
COLOR_TEXT_LIGHT = "#e0e0e0"
COLOR_ERROR = "#ff4d4d"
COLOR_WARNING = "#ffd166"

# --- Cinematic & Futuristic Styling ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Roboto+Mono:wght@300;400;700&display=swap');

    :root {{
        --primary-color: {COLOR_PRIMARY};
        --secondary-color: {COLOR_SECONDARY};
        --background-dark: {COLOR_BG_DARK};
        --background-medium: {COLOR_BG_MEDIUM};
        --text-light: {COLOR_TEXT_LIGHT};
        --error-color: {COLOR_ERROR};
        --warning-color: {COLOR_WARNING};
    }}

    body {{
        background-color: var(--background-dark);
        color: var(--text-light);
        font-family: 'Roboto Mono', monospace;
    }}

    .stApp {{
        background-color: var(--background-dark);
    }}

    h1, h2, h3, h4, h5, h6 {{
        font-family: 'Orbitron', sans-serif;
        color: var(--primary-color);
        text-shadow: 0 0 5px rgba(0,255,204,0.5);
    }}

    .stMarkdown h1 {{
        text-align: center;
        font-size: 3.5em;
        background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 15px rgba(0,255,204,0.7), 0 0 25px rgba(0,204,255,0.5);
    }}

    .stTabs [data-baseweb="tab-list"] button {{
        background-color: var(--background-medium);
        border: 1px solid var(--primary-color);
        color: var(--text-light);
        padding: 12px 25px;
        font-weight: bold;
        transition: all 0.3s ease-in-out;
    }}

    .stTabs [data-baseweb="tab-list"] button:hover {{
        background-color: var(--primary-color);
        color: #0a0a1a;
        box-shadow: 0 0 20px var(--primary-color);
    }}

    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
        background-color: var(--primary-color);
        color: #0a0a1a;
        box-shadow: 0 0 25px var(--primary-color);
    }}

    .card {{
        background: linear-gradient(145deg, rgba(0,255,204,0.15), rgba(0,100,200,0.15));
        border: 1px solid var(--primary-color);
        border-radius: 15px;
        padding: 25px;
        box-shadow: 0 0 30px rgba(0,255,204,0.4);
        text-align: center;
        margin-bottom: 20px;
        backdrop-filter: blur(5px);
    }}

    .production-lift-display {{
        background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'Orbitron', sans-serif;
        font-size: 4.5em;
        font-weight: 700;
        text-align: center;
        text-shadow: 0 0 20px rgba(0,255,204,0.8), 0 0 30px rgba(0,204,255,0.6);
        animation: neon-glow 1.5s ease-in-out infinite alternate;
    }}

    @keyframes neon-glow {{
        from {{ text-shadow: 0 0 10px var(--primary-color), 0 0 20px var(--secondary-color); }}
        to {{ text-shadow: 0 0 20px var(--primary-color), 0 0 30px var(--secondary-color), 0 0 40px var(--primary-color); }}
    }}

    .log-console {{
        background-color: var(--background-medium);
        border: 1px solid var(--primary-color);
        border-radius: 10px;
        padding: 15px;
        max-height: 350px;
        overflow-y: auto;
    }}
</style>
""", unsafe_allow_html=True)

# --- Data Loading ---
@st.cache_data
def load_data():
    try:
        pvto_df = pd.read_excel("PVTO.xlsx")
        rel_perm_df = pd.read_excel("water-oil Relative permeability.xlsx")
        cap_press_df = pd.read_excel("capillary pressure.xlsx")
        pro_df = pd.read_excel("Pro.xlsx", skiprows=8)

        for df in [pvto_df, rel_perm_df, cap_press_df, pro_df]:
            df.columns = df.columns.str.strip().str.lower()

        pvto_df = pvto_df.dropna().sort_values("pressure")
        rel_perm_df = rel_perm_df.dropna().sort_values("sw")
        cap_press_df = cap_press_df.dropna().sort_values("sw")

        visc_interp = interp1d(pvto_df["pressure"], pvto_df["oil viscosity"], fill_value="extrapolate")
        kro_interp = interp1d(rel_perm_df["sw"], rel_perm_df["kro"], fill_value="extrapolate")
        pc_interp = interp1d(cap_press_df["sw"], cap_press_df["pcow (psi)"], fill_value="extrapolate")

        return visc_interp, kro_interp, pc_interp, pro_df
    except Exception as e:
        st.error(f"Critical Data Error: {e}")
        st.stop()

visc, kro, pc, pro_data = load_data()

# --- Simulation Models ---
class Reservoir:
    def __init__(self, grid_size=25):
        self.grid_size = grid_size
        self.sw_grid = np.random.uniform(0.2, 0.4, (grid_size, grid_size))
        self.nano_concentration_grid = np.zeros((grid_size, grid_size))
        self.viscosity_reduction_factor = 0.005
        self.kro_enhancement_factor = 0.002

    def update_nano_effect(self, nano_particles):
        self.nano_concentration_grid = np.zeros((self.grid_size, self.grid_size))
        for n in nano_particles:
            self.nano_concentration_grid[n.x, n.y] += 1
        self.nano_concentration_grid = gaussian_filter(self.nano_concentration_grid, sigma=1.5)
        self.nano_concentration_grid = np.clip(self.nano_concentration_grid, 0, 10)

    def calculate_production(self, pressure, nano_particles):
        self.update_nano_effect(nano_particles)
        avg_sw = np.clip(np.mean(self.sw_grid), 0.01, 0.99)
        base_oil_viscosity = float(visc(pressure))
        avg_nano_conc = np.mean(self.nano_concentration_grid)
        effective_oil_viscosity = np.clip(base_oil_viscosity * (1 - avg_nano_conc * self.viscosity_reduction_factor), 0.1, base_oil_viscosity)
        base_kro = kro(avg_sw)
        effective_kro = np.clip(base_kro * (1 + avg_nano_conc * self.kro_enhancement_factor), 0.01, 0.9)
        capillary_pressure = float(pc(avg_sw))
        return max(0, (effective_kro * (pressure - capillary_pressure) / 1000) / (effective_oil_viscosity + 1e-6))

class NanoRobot:
    def __init__(self, grid_size=25):
        self.grid_size = grid_size
        self.x = np.random.randint(0, grid_size)
        self.y = np.random.randint(0, grid_size)
        self.signal_strength = random.randint(70, 100)

    def move(self, reservoir_sw_grid, nano_concentration_grid, dx=0, dy=0):
        gsx, gsy = np.gradient(reservoir_sw_grid)
        gnx, gny = np.gradient(nano_concentration_grid)
        new_x = self.x - (gsx[self.x, self.y] * 0.5) - (gnx[self.x, self.y] * 0.2) + random.uniform(-0.3, 0.3) + dx
        new_y = self.y - (gsy[self.x, self.y] * 0.5) - (gny[self.x, self.y] * 0.2) + random.uniform(-0.3, 0.3) + dy
        self.x = int(np.clip(new_x, 0, self.grid_size - 1))
        self.y = int(np.clip(new_y, 0, self.grid_size - 1))

# --- Session State ---
if "res" not in st.session_state:
    st.session_state.res = Reservoir()
    st.session_state.nano_swarm = [NanoRobot() for _ in range(150)]
    st.session_state.logs = []
    st.session_state.simulation_running = False
    st.session_state.nano_production_history = []
    st.session_state.traditional_production_history = []
    st.session_state.current_pressure = 1500

res = st.session_state.res

# --- Dashboard ---
st.markdown("<h1>Nano-Swarm EOR Command Center</h1>", unsafe_allow_html=True)
tabs = st.tabs(["Dashboard", "Subsurface Digital Twin", "Mission Control", "AI Analytics", "Economics & ROI", "Field Map"])

with tabs[0]:
    st.markdown("<h2>Operational Overview</h2>", unsafe_allow_html=True)
    st.session_state.current_pressure = st.slider("Reservoir Pressure (psi)", 500, 3000, st.session_state.current_pressure)
    
    trad_prod = max(0, (kro(np.clip(np.mean(res.sw_grid), 0.01, 0.99)) * (st.session_state.current_pressure - pc(np.clip(np.mean(res.sw_grid), 0.01, 0.99))) / 1000) / (visc(st.session_state.current_pressure) + 1e-6))
    nano_prod = res.calculate_production(st.session_state.current_pressure, st.session_state.nano_swarm)
    
    st.session_state.traditional_production_history.append(trad_prod)
    st.session_state.nano_production_history.append(nano_prod)

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='card'><h3>Traditional</h3><p>{trad_prod:.2f}</p></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='card'><h3>Nano-Swarm</h3><p>{nano_prod:.2f}</p></div>", unsafe_allow_html=True)
    lift = ((nano_prod - trad_prod) / trad_prod * 100) if trad_prod > 0 else 0
    c3.markdown(f"<div class='card'><h3>Lift</h3><p>{lift:+.2f}%</p></div>", unsafe_allow_html=True)

    fig_gauge = go.Figure(go.Indicator(mode="gauge+number+delta", value=nano_prod,
        title={'text':"Total Production", 'font': {'color': COLOR_TEXT_LIGHT}},
        delta = {'reference': st.session_state.nano_production_history[-2] if len(st.session_state.nano_production_history) > 1 else trad_prod},
        gauge={
            'axis':{'range':[0, max(1,nano_prod*1.5)], 'tickcolor': COLOR_TEXT_LIGHT},
            'bar':{'color': COLOR_PRIMARY},
            'bgcolor': COLOR_BG_MEDIUM,
            'steps':[{'range':[0, trad_prod], 'color':'#3a3a5a'}, {'range':[trad_prod, max(1,nano_prod*1.5)], 'color':'#00cc99'}],
            'threshold':{'line':{'color': COLOR_ERROR, 'width':4}, 'value': trad_prod}
        }
    ))
    fig_gauge.update_layout(height=300, paper_bgcolor=COLOR_BG_DARK, font={'color': COLOR_TEXT_LIGHT})
    st.plotly_chart(fig_gauge, use_container_width=True)

with tabs[1]:
    st.markdown("<h2>Subsurface Digital Twin</h2>", unsafe_allow_html=True)
    chart_placeholder = st.empty()
    if st.session_state.simulation_running:
        for n in st.session_state.nano_swarm: n.move(res.sw_grid, res.nano_concentration_grid)
        res.update_nano_effect(st.session_state.nano_swarm)
        display_grid = np.clip(res.sw_grid - (res.nano_concentration_grid * 0.02), 0.05, 0.95)
        xs=[n.x for n in st.session_state.nano_swarm]; ys=[n.y for n in st.session_state.nano_swarm]; zs=[display_grid[x,y] for x,y in zip(xs,ys)]
        fig = go.Figure()
        fig.add_trace(go.Surface(z=display_grid, colorscale="Viridis", opacity=0.7))
        fig.add_trace(go.Scatter3d(x=xs, y=ys, z=zs, mode='markers', marker=dict(size=5, color='cyan')))
        fig.update_layout(scene=dict(bgcolor=COLOR_BG_DARK), height=700, paper_bgcolor=COLOR_BG_DARK, font=dict(color=COLOR_TEXT_LIGHT))
        chart_placeholder.plotly_chart(fig, use_container_width=True)
        time.sleep(0.1); st.rerun()
    else:
        st.info("Simulation paused.")

with tabs[2]:
    st.markdown("<h2>Mission Control</h2>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    for col, title, val in zip([c1, c2, c3], ["Signal", "Energy", "Latency"], [90, 85, 20]):
        fig = go.Figure(go.Indicator(mode="gauge+number", value=val, title={'text':title, 'font':{'color': COLOR_TEXT_LIGHT}},
            gauge={'axis':{'range':[0,100], 'tickcolor': COLOR_TEXT_LIGHT}, 'bar':{'color': COLOR_PRIMARY}, 'bgcolor': COLOR_BG_MEDIUM}))
        fig.update_layout(height=200, paper_bgcolor=COLOR_BG_DARK, font={'color': COLOR_TEXT_LIGHT})
        col.plotly_chart(fig, use_container_width=True)
    if st.button("▶ ACTIVATE NANO-SWARM"): st.session_state.simulation_running = True
    if st.button("🛑 EMERGENCY SHUTDOWN"): st.session_state.simulation_running = False

with tabs[3]:
    st.markdown(f"<div class='production-lift-display'>Nano Lift: {lift:+.2f}%</div>", unsafe_allow_html=True)
    if len(st.session_state.nano_production_history) > 1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=st.session_state.nano_production_history, name="Nano-Swarm", line=dict(color=COLOR_PRIMARY, width=4)))
        fig.add_trace(go.Scatter(y=st.session_state.traditional_production_history, name="Traditional", line=dict(dash='dash', color=COLOR_TEXT_LIGHT)))
        fig.update_layout(height=600, template="plotly_dark", paper_bgcolor=COLOR_BG_DARK, plot_bgcolor=COLOR_BG_MEDIUM)
        st.plotly_chart(fig, use_container_width=True)

with tabs[5]:
    st.markdown("<h2>Field Operations Map</h2>", unsafe_allow_html=True)
    fig = go.Figure(go.Scatter(x=np.random.rand(20)*100, y=np.random.rand(20)*100, mode='markers', marker=dict(size=12, color=COLOR_PRIMARY, symbol='triangle-up')))
    fig.update_layout(height=600, paper_bgcolor=COLOR_BG_DARK, plot_bgcolor=COLOR_BG_MEDIUM, font=dict(color=COLOR_TEXT_LIGHT))
    st.plotly_chart(fig, use_container_width=True)
