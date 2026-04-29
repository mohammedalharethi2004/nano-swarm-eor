import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import interp1d
import time, random, datetime

st.set_page_config(layout="wide", page_title="Energy Command Center - Live Demo", page_icon="⚡")

# ================= THEME & STYLING =================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Roboto+Mono:wght@300;400;700&display=swap');

    body {
        background: #0a0a1a;
        color: #e0e0e0;
        font-family: 'Roboto Mono', monospace;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Orbitron', sans-serif;
        color: #00ffcc;
    }

    .stApp {
        background-color: #0a0a1a;
    }

    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.2rem;
        font-weight: bold;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }

    .stTabs [data-baseweb="tab-list"] button {
        background-color: #1a1a3a;
        border-radius: 8px 8px 0 0;
        border: 1px solid #00ffcc;
        color: #e0e0e0;
        padding: 10px 20px;
        transition: all 0.3s ease-in-out;
    }

    .stTabs [data-baseweb="tab-list"] button:hover {
        background-color: #00ffcc;
        color: #0a0a1a;
        box-shadow: 0 0 15px #00ffcc;
    }

    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: #00ffcc;
        color: #0a0a1a;
        border-bottom: 3px solid #0a0a1a;
        box-shadow: 0 0 20px #00ffcc;
    }

    .card {
        background: linear-gradient(145deg, rgba(0,255,204,0.1), rgba(0,100,200,0.1));
        border: 1px solid #00ffcc;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 0 25px rgba(0,255,204,0.5);
        text-align: center;
        margin-bottom: 20px;
        transition: all 0.3s ease-in-out;
    }

    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 0 35px rgba(0,255,204,0.8);
    }

    .card h3 {
        color: #00ffcc;
        font-family: 'Orbitron', sans-serif;
        margin-bottom: 10px;
    }

    .card p {
        font-size: 2.2em;
        font-weight: bold;
        color: #e0e0e0;
    }

    .log-green {color:#00ff9c;}
    .log-red {color:#ff4d4d;}
    .log-yellow {color:#ffd166;}

    .stSlider > div > div > div[data-testid="stThumbValue"] {
        background-color: #00ffcc;
        border: 1px solid #00ffcc;
    }
    .stSlider > div > div > div[data-testid="stTrack"] > div {
        background-color: #00ffcc;
    }
    .stButton > button {
        background-color: #1a1a3a;
        color: #00ffcc;
        border: 1px solid #00ffcc;
        border-radius: 8px;
        padding: 10px 20px;
        font-family: 'Orbitron', sans-serif;
        transition: all 0.3s ease-in-out;
    }
    .stButton > button:hover {
        background-color: #00ffcc;
        color: #0a0a1a;
        box-shadow: 0 0 15px #00ffcc;
    }
    .stNumberInput > div > div > input {
        background-color: #1a1a3a;
        color: #e0e0e0;
        border: 1px solid #00ffcc;
        border-radius: 8px;
    }
    .stMetric > div > div:first-child {
        color: #00ffcc;
        font-family: 'Orbitron', sans-serif;
    }
    .stMetric > div > div:last-child > div:first-child {
        color: #e0e0e0;
        font-size: 2.5em;
        font-weight: bold;
    }
    .stAlert {
        background-color: rgba(0,255,204,0.1);
        border-left: 5px solid #00ffcc;
        color: #e0e0e0;
    }
    .production-lift-display {
        background: linear-gradient(90deg, #00ffcc, #00ccff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'Orbitron', sans-serif;
        font-size: 3.5em;
        font-weight: 700;
        text-align: center;
        text-shadow: 0 0 15px rgba(0,255,204,0.7), 0 0 25px rgba(0,204,255,0.5);
        margin-top: 20px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ================= DATA =================
@st.cache_data
def load_data():
    try:
        pvto = pd.read_excel("PVTO.xlsx")
        rel = pd.read_excel("water-oil Relative permeability.xlsx")
        cap = pd.read_excel("capillary pressure.xlsx")
        pro = pd.read_excel("Pro.xlsx", skiprows=8)

        for df in [pvto, rel, cap, pro]:
            df.columns = df.columns.str.strip().str.lower()

        pvto = pvto.dropna().sort_values("pressure")
        rel = rel.dropna().sort_values("sw")
        cap = cap.dropna().sort_values("sw")

        visc_func = interp1d(pvto["pressure"], pvto["oil viscosity"], fill_value="extrapolate")
        kro_func = interp1d(rel["sw"], rel["kro"], fill_value="extrapolate")
        pc_func = interp1d(cap["sw"], cap["pcow (psi)"], fill_value="extrapolate")

        return visc_func, kro_func, pc_func, pro
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()

visc, kro, pc, pro = load_data()

# ================= MODEL =================
class Reservoir:
    def __init__(self, grid_size=25):
        self.grid_size = grid_size
        self.grid = np.full((grid_size, grid_size), 0.3)
        self.nano_concentration_grid = np.zeros((grid_size, grid_size))
        self.permeability_enhancement_factor = 0.005

    def update_nano_effect(self, nano_particles):
        self.nano_concentration_grid = np.zeros((self.grid_size, self.grid_size))
        for n in nano_particles:
            self.nano_concentration_grid[n.x, n.y] += 1
        from scipy.ndimage import gaussian_filter
        self.nano_concentration_grid = gaussian_filter(self.nano_concentration_grid, sigma=1)
        self.nano_concentration_grid = np.clip(self.nano_concentration_grid, 0, 5)

    def production(self, p, nano_particles):
        self.update_nano_effect(nano_particles)
        effective_sw_grid = np.clip(self.grid - (self.nano_concentration_grid * 0.01), 0.01, 0.99)
        avg_effective_sw = np.mean(effective_sw_grid)
        avg_effective_sw = np.clip(avg_effective_sw, 0.01, 0.99) 
        mu = float(visc(p))
        base_kro = kro(avg_effective_sw)
        enhanced_kro = np.clip(base_kro * (1 + np.mean(self.nano_concentration_grid) * self.permeability_enhancement_factor), 0.01, 0.8)
        return (float(enhanced_kro) * (p - float(pc(avg_effective_sw))) / 1000) / (mu + 1e-6)

class Nano:
    def __init__(self, grid_size=25):
        self.grid_size = grid_size
        self.x = np.random.randint(0, grid_size)
        self.y = np.random.randint(0, grid_size)

    def move(self, reservoir_grid, dx=0, dy=0):
        gx, gy = np.gradient(reservoir_grid)
        move_factor = 0.05
        random_walk_strength = 0.5
        new_x = self.x - (gx[self.x, self.y] * move_factor) + (random.uniform(-random_walk_strength, random_walk_strength))
        new_y = self.y - (gy[self.x, self.y] * move_factor) + (random.uniform(-random_walk_strength, random_walk_strength))
        self.x = int(np.clip(new_x, 0, self.grid_size - 1))
        self.y = int(np.clip(new_y, 0, self.grid_size - 1))

# ================= SESSION =================
if "res" not in st.session_state:
    st.session_state.res = Reservoir()
    st.session_state.nano = [Nano() for _ in range(100)]
    st.session_state.logs=[]
    st.session_state.run=False
    st.session_state.dx=0
    st.session_state.dy=0
    st.session_state.series=[]
    st.session_state.base_series=[]
    st.session_state.production_history = []
    st.session_state.current_pressure = 1500
    st.session_state.production_lift_percentage = 0.0

res = st.session_state.res

# ================= HEADER =================
st.markdown("<h1 style='text-align: center; color: #00ffcc;'>⚡ Energy Command Center ⚡</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #e0e0e0;'>Advanced Nano-Enhanced Oil Recovery Simulation - Live Demo</p>", unsafe_allow_html=True)
st.markdown("--- ")

# ================= TABS =================
tabs = st.tabs(["Dashboard","Subsurface Digital Twin","Mission Control","AI Analytics","Economics & ROI","Field Operations Map"])

# ================= DASHBOARD =================
with tabs[0]:
    st.markdown("<h2 style='color: #00ffcc;'>Operational Overview</h2>", unsafe_allow_html=True)
    p_slider = st.slider("Simulated Reservoir Pressure (psi)", 500, 3000, st.session_state.current_pressure)
    st.session_state.current_pressure = p_slider

    base_production_val = pro.select_dtypes(include=np.number).mean().mean()
    nano_production_val = res.production(st.session_state.current_pressure, st.session_state.nano)
    
    st.session_state.production_history.append(nano_production_val)
    st.session_state.base_series.append(base_production_val)
    st.session_state.series.append(nano_production_val)

    c1,c2,c3 = st.columns(3)
    with c1:
        st.markdown(f"<div class='card'><h3>Traditional Production</h3><p>{base_production_val:.2f} bbl/day</p></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='card'><h3>Nano-Enhanced Production</h3><p>{nano_production_val:.2f} bbl/day</p></div>", unsafe_allow_html=True)
    with c3:
        lift_percentage = ((nano_production_val - base_production_val) / base_production_val * 100) if base_production_val != 0 else 0
        st.session_state.production_lift_percentage = lift_percentage
        st.markdown(f"<div class='card'><h3>Production Lift</h3><p>{lift_percentage:+.2f}%</p></div>", unsafe_allow_html=True)

    fig_gauge = go.Figure(go.Indicator(mode="gauge+number+delta", value=nano_production_val,
        title={'text':"Total Production (bbl/day)", 'font': {'size': 20, 'color': '#e0e0e0'}},
        delta = {'reference': st.session_state.production_history[-2] if len(st.session_state.production_history) > 1 else base_production_val},
        gauge={
            'axis':{'range':[0, max(1,nano_production_val*1.5)], 'tickcolor':'#e0e0e0'},
            'bar':{'color':'#00ffcc'},
            'bgcolor':'#1a1a3a',
            'steps':[
                {'range':[0, base_production_val], 'color':'#3a3a5a'},
                {'range':[base_production_val, max(1,nano_production_val*1.5)], 'color':'#00cc99'}
            ],
            'threshold':{'line':{'color':'#ff4d4d', 'width':4}, 'value': base_production_val}
        }
    ))
    fig_gauge.update_layout(height=300, margin=dict(l=10,r=10,t=50,b=10), font={'color': '#e0e0e0', 'family': 'Roboto Mono'})
    st.plotly_chart(fig_gauge, use_container_width=True)

# ================= SUBSURFACE =================
with tabs[1]:
    st.markdown("<h2 style='color: #00ffcc;'>Subsurface Digital Twin</h2>", unsafe_allow_html=True)
    chart_placeholder = st.empty()

    if st.session_state.run:
        for n in st.session_state.nano:
            n.move(res.grid, st.session_state.dx, st.session_state.dy)
        res.update_nano_effect(st.session_state.nano)
        display_grid = np.clip(res.grid - (res.nano_concentration_grid * 0.05), 0.01, 0.99)
        xs=[n.x for n in st.session_state.nano]; ys=[n.y for n in st.session_state.nano]; zs=[display_grid[x,y] for x,y in zip(xs,ys)]

        fig_subsurface = go.Figure()
        fig_subsurface.add_trace(go.Surface(z=display_grid, colorscale="Turbo", opacity=0.8))
        fig_subsurface.add_trace(go.Scatter3d(x=xs,y=ys,z=zs, mode='markers', marker=dict(size=4, color='cyan')))
        fig_subsurface.update_layout(scene=dict(bgcolor='#0a0a1a'), height=700, paper_bgcolor='#0a0a1a', font=dict(color='#e0e0e0'))
        chart_placeholder.plotly_chart(fig_subsurface, use_container_width=True)
        time.sleep(0.1); st.rerun()
    else:
        st.info("Simulation is paused. Press 'START SIMULATION' in Mission Control.")
        fig_static = go.Figure(go.Surface(z=res.grid, colorscale="Turbo"))
        fig_static.update_layout(scene=dict(bgcolor='#0a0a1a'), height=700, paper_bgcolor='#0a0a1a')
        chart_placeholder.plotly_chart(fig_static, use_container_width=True)

# ================= CONTROL =================
with tabs[2]:
    st.markdown("<h2 style='color: #00ffcc;'>Mission Control</h2>", unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        if st.button("▶ START SIMULATION"):
            st.session_state.run=True
            st.session_state.logs.append(("INFO","System Simulation Initiated"))
    with c2:
        if st.button("🛑 EMERGENCY STOP"):
            st.session_state.run=False
            st.session_state.logs.append(("ERROR","Emergency Stop Activated"))

# ================= AI ANALYTICS =================
with tabs[3]:
    st.markdown("<h2 style='color: #00ffcc;'>AI-Powered Production Analytics</h2>", unsafe_allow_html=True)
    st.markdown(f"<div class='production-lift-display'>Nano Lift: {st.session_state.production_lift_percentage:+.2f}%</div>", unsafe_allow_html=True)
    
    if len(st.session_state.series) > 1:
        y_nano = np.array(st.session_state.series); y_base = np.array(st.session_state.base_series); x = np.arange(len(y_nano))
        fig_analytics = go.Figure()
        fig_analytics.add_trace(go.Scatter(x=x, y=y_nano, name="Nano-Enhanced", line=dict(color="#00ffcc", width=4)))
        fig_analytics.add_trace(go.Scatter(x=x, y=y_base, name="Traditional", line=dict(dash='dash', color='#e0e0e0')))
        fig_analytics.update_layout(height=600, template="plotly_dark", paper_bgcolor='#0a0a1a', plot_bgcolor='#1a1a3a')
        st.plotly_chart(fig_analytics, use_container_width=True)

# ================= LOG / EVENT CONSOLE =================
st.markdown("--- ")
st.markdown("<h2 style='color: #00ffcc;'>🧠 System Event Console</h2>", unsafe_allow_html=True)
log_html = "<div style='background-color: #1a1a3a; border: 1px solid #00ffcc; border-radius: 8px; padding: 15px;'>"
for t, msg in reversed(st.session_state.logs[-10:]):
    color = "#ff4d4d" if t == "ERROR" else "#00ffcc"
    log_html += f"<p style='color:{color};'>[{t}] {msg}</p>"
log_html += "</div>"
st.markdown(log_html, unsafe_allow_html=True)
