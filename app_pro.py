import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import interp1d
import time, random, datetime
from scipy.ndimage import gaussian_filter

# --- Streamlit Page Configuration ---
st.set_page_config(layout="wide", page_title="Nano-Swarm EOR Masterpiece - Final Edition", page_icon="🚀")

# --- Define Constants for Colors (Python-accessible) ---
COLOR_PRIMARY = "#00ffcc"  # Neon Green
COLOR_SECONDARY = "#00ccff" # Neon Blue
COLOR_BG_DARK = "#0a0a1a"
COLOR_BG_MEDIUM = "#1a1a3a"
COLOR_TEXT_LIGHT = "#e0e0e0"
COLOR_ERROR = "#ff4d4d"
COLOR_WARNING = "#ffd166"
COLOR_NANO_HEALTHY = "cyan"
COLOR_NANO_STRESSED = "orange"
COLOR_NANO_CRITICAL = "red"

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

    .guide-section {{
        background: rgba(26, 26, 58, 0.6);
        border-left: 5px solid var(--primary-color);
        padding: 20px;
        margin-bottom: 20px;
        border-radius: 0 15px 15px 0;
    }}

    .team-member {{
        font-family: 'Orbitron', sans-serif;
        font-size: 1.2em;
        color: var(--secondary-color);
        margin: 10px 0;
        padding: 10px;
        border-bottom: 1px solid rgba(0, 204, 255, 0.2);
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

        visc_interp = interp1d(pvto_df["pressure"], pvto_df["oil viscosity"], fill_value="extrapolate", bounds_error=False)
        kro_interp = interp1d(rel_perm_df["sw"], rel_perm_df["kro"], fill_value="extrapolate", bounds_error=False)
        pc_interp = interp1d(cap_press_df["sw"], cap_press_df["pcow (psi)"], fill_value="extrapolate", bounds_error=False)

        return visc_interp, kro_interp, pc_interp, pro_df
    except Exception as e:
        st.error(f"Critical Data Error: {e}")
        st.stop()

visc, kro, pc, pro_data = load_data()

# --- Core Simulation Models ---
class Reservoir:
    def __init__(self, grid_size=25):
        self.grid_size = grid_size
        self.sw_grid = np.random.uniform(0.2, 0.4, (grid_size, grid_size))
        self.perm_grid = np.random.uniform(50, 200, (grid_size, grid_size))
        for _ in range(5):
            cx, cy = random.randint(0, grid_size-1), random.randint(0, grid_size-1)
            self.perm_grid[max(0, cx-3):min(grid_size, cx+3), max(0, cy-3):min(grid_size, cy+3)] = np.random.uniform(5, 30, (min(grid_size, cx+3)-max(0, cx-3), min(grid_size, cy+3)-max(0, cy-3)))
        self.perm_grid = gaussian_filter(self.perm_grid, sigma=1)
        self.nano_concentration_grid = np.zeros((grid_size, grid_size))
        self.nano_effect_radius = 2
        self.base_viscosity_reduction_factor = 0.005 
        self.base_kro_enhancement_factor = 0.002
        self.current_viscosity_modifier = 1.0
        self.current_salinity_modifier = 1.0

    def update_nano_effect(self, nano_particles):
        self.nano_concentration_grid = np.zeros((self.grid_size, self.grid_size))
        for n in nano_particles:
            for i in range(max(0, n.x - self.nano_effect_radius), min(self.grid_size, n.x + self.nano_effect_radius + 1)):
                for j in range(max(0, n.y - self.nano_effect_radius), min(self.grid_size, n.y + self.nano_effect_radius + 1)):
                    dist = np.sqrt((n.x - i)**2 + (n.y - j)**2)
                    if dist <= self.nano_effect_radius:
                        self.nano_concentration_grid[i, j] += (self.nano_effect_radius - dist) / self.nano_effect_radius
        self.nano_concentration_grid = gaussian_filter(self.nano_concentration_grid, sigma=1.5)
        self.nano_concentration_grid = np.clip(self.nano_concentration_grid, 0, 10)

    def calculate_production(self, pressure, nano_particles):
        self.update_nano_effect(nano_particles)
        avg_sw = np.clip(np.mean(self.sw_grid), 0.01, 0.99)
        base_oil_viscosity = float(visc(pressure)) * self.current_viscosity_modifier
        avg_nano_conc = np.mean(self.nano_concentration_grid)
        effective_oil_viscosity = np.clip(base_oil_viscosity * (1 - avg_nano_conc * self.base_viscosity_reduction_factor), 0.1, base_oil_viscosity)
        base_kro = kro(avg_sw)
        effective_kro = np.clip(base_kro * (1 + avg_nano_conc * self.base_kro_enhancement_factor * self.current_salinity_modifier), 0.01, 0.9)
        capillary_pressure = float(pc(avg_sw))
        avg_perm = np.mean(self.perm_grid)
        return max(0, (effective_kro * avg_perm * (pressure - capillary_pressure) / 1000) / (effective_oil_viscosity + 1e-6))

class NanoRobot:
    def __init__(self, grid_size=25):
        self.grid_size = grid_size
        self.x = np.random.randint(0, grid_size)
        self.y = np.random.randint(0, grid_size)
        self.energy = 100
        self.signal_strength = random.randint(70, 100)
        self.wettability_index = 0.5

    def move(self, reservoir_sw_grid, reservoir_perm_grid, nano_concentration_grid, current_pressure, oil_viscosity_factor, water_salinity_factor, dx=0, dy=0):
        energy_cost = 0.1 + (oil_viscosity_factor - 1.0) * 0.5 + (water_salinity_factor - 1.0) * 0.3 + (3000 - current_pressure) / 1000 * 0.2
        self.energy = np.clip(self.energy - energy_cost, 0, 100)
        if self.energy <= 0: return
        gsx, gsy = np.gradient(reservoir_sw_grid)
        gpx, gpy = np.gradient(reservoir_perm_grid)
        gnx, gny = np.gradient(nano_concentration_grid)
        speed = self.energy / 100.0
        new_x = self.x - (gsx[self.x, self.y] * 0.5 * speed) + (gpx[self.x, self.y] * 0.3 * speed) - (gnx[self.x, self.y] * 0.2 * speed) + (random.uniform(-0.3, 0.3) * speed) + dx
        new_y = self.y - (gsy[self.x, self.y] * 0.5 * speed) + (gpy[self.x, self.y] * 0.3 * speed) - (gny[self.x, self.y] * 0.2 * speed) + (random.uniform(-0.3, 0.3) * speed) + dy
        self.x = int(np.clip(new_x, 0, self.grid_size - 1))
        self.y = int(np.clip(new_y, 0, self.grid_size - 1))
        self.wettability_index = np.clip(0.5 + nano_concentration_grid[self.x, self.y] * 0.05, 0.1, 0.9)

# --- Session State ---
if "res" not in st.session_state:
    st.session_state.res = Reservoir()
    st.session_state.nano_swarm = [NanoRobot() for _ in range(150)]
    st.session_state.logs = []
    st.session_state.simulation_running = False
    st.session_state.manual_dx = 0
    st.session_state.manual_dy = 0
    st.session_state.time_step = 0
    st.session_state.nano_production_history = []
    st.session_state.traditional_production_history = []
    st.session_state.current_pressure = 1500
    st.session_state.oil_viscosity_factor = 1.0
    st.session_state.water_salinity_factor = 1.0
    st.session_state.total_water_saved = 0.0
    st.session_state.carbon_reduction = 0.0
    st.session_state.best_production = 0.0
    st.session_state.best_roi = 0.0
    st.session_state.last_update_time = time.time()
    st.session_state.injection_well_loc = (5, 5)
    st.session_state.production_well_loc = (20, 20)

res = st.session_state.res

def log_event(type, message):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append((type, timestamp, message))
    if len(st.session_state.logs) > 50: st.session_state.logs.pop(0)

# --- Dashboard ---
st.markdown("<h1>Nano-Swarm EOR Masterpiece - Final Edition</h1>", unsafe_allow_html=True)
tabs = st.tabs(["Dashboard", "Subsurface Digital Twin", "Mission Control", "AI Analytics & Sensitivity", "Economics & ROI", "Field Map", "Technical Report", "Project Guide / دليل المشروع"])

with tabs[0]:
    st.markdown("<h2>Operational Overview</h2>", unsafe_allow_html=True)
    st.session_state.current_pressure = st.slider("Reservoir Pressure (psi)", 500, 3000, st.session_state.current_pressure)
    trad_prod = max(0, (kro(np.clip(np.mean(res.sw_grid), 0.01, 0.99)) * np.mean(res.perm_grid) * (st.session_state.current_pressure - pc(np.clip(np.mean(res.sw_grid), 0.01, 0.99))) / 1000) / (visc(st.session_state.current_pressure) * st.session_state.oil_viscosity_factor + 1e-6))
    nano_prod = res.calculate_production(st.session_state.current_pressure, st.session_state.nano_swarm)
    st.session_state.traditional_production_history.append(trad_prod)
    st.session_state.nano_production_history.append(nano_prod)
    if nano_prod > st.session_state.best_production: st.session_state.best_production = nano_prod
    lift = ((nano_prod - trad_prod) / trad_prod * 100) if trad_prod > 0 else 0
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='card'><h3>Traditional</h3><p>{trad_prod:.2f}</p></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='card'><h3>Nano-Swarm</h3><p>{nano_prod:.2f}</p></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='card'><h3>Lift</h3><p>{lift:+.2f}%</p></div>", unsafe_allow_html=True)
    fig = go.Figure(go.Indicator(mode="gauge+number+delta", value=nano_prod, title={'text':"Total Production", 'font':{'color':COLOR_TEXT_LIGHT}},
        delta={'reference': st.session_state.nano_production_history[-2] if len(st.session_state.nano_production_history) > 1 else trad_prod},
        gauge={'axis':{'range':[0, max(1,nano_prod*1.5)], 'tickcolor':COLOR_TEXT_LIGHT}, 'bar':{'color':COLOR_PRIMARY}, 'bgcolor':COLOR_BG_MEDIUM,
               'steps':[{'range':[0, trad_prod], 'color':'#3a3a5a'}, {'range':[trad_prod, max(1,nano_prod*1.5)], 'color':'#00cc99'}],
               'threshold':{'line':{'color':COLOR_ERROR, 'width':4}, 'value': trad_prod}}))
    fig.update_layout(height=300, paper_bgcolor=COLOR_BG_DARK, font={'color':COLOR_TEXT_LIGHT})
    st.plotly_chart(fig, use_container_width=True)

with tabs[1]:
    st.markdown("<h2>Subsurface Digital Twin</h2>", unsafe_allow_html=True)
    chart_placeholder = st.empty()
    if st.session_state.simulation_running:
        for n in st.session_state.nano_swarm: n.move(res.sw_grid, res.perm_grid, res.nano_concentration_grid, st.session_state.current_pressure, st.session_state.oil_viscosity_factor, st.session_state.water_salinity_factor, st.session_state.manual_dx, st.session_state.manual_dy)
        res.update_nano_effect(st.session_state.nano_swarm)
        display_sw = np.clip(res.sw_grid - (res.nano_concentration_grid * 0.02), 0.05, 0.95)
        display_perm = np.clip(res.perm_grid + (res.nano_concentration_grid * 5), 5, 250)
        xs=[n.x for n in st.session_state.nano_swarm]; ys=[n.y for n in st.session_state.nano_swarm]; zs=[display_sw[x,y] for x,y in zip(xs,ys)]
        colors = [COLOR_NANO_HEALTHY if n.energy > 70 else COLOR_NANO_STRESSED if n.energy > 30 else COLOR_NANO_CRITICAL for n in st.session_state.nano_swarm]
        fig = go.Figure()
        fig.add_trace(go.Surface(z=display_sw, colorscale="Viridis", opacity=0.7))
        fig.add_trace(go.Surface(z=display_perm, colorscale="Hot", opacity=0.3, showscale=False))
        fig.add_trace(go.Scatter3d(x=xs, y=ys, z=zs, mode='markers', marker=dict(size=5, color=colors)))
        st.markdown(f"<h3 style='color: {COLOR_PRIMARY};'>Avg Wettability: {np.mean([n.wettability_index for n in st.session_state.nano_swarm]):.2f}</h3>", unsafe_allow_html=True)
        fig.update_layout(scene=dict(bgcolor=COLOR_BG_DARK), height=700, paper_bgcolor=COLOR_BG_DARK, font=dict(color=COLOR_TEXT_LIGHT))
        chart_placeholder.plotly_chart(fig, use_container_width=True)
        if st.session_state.time_step % 25 == 0: log_event("INFO", f"Swarm status: Avg Energy {np.mean([n.energy for n in st.session_state.nano_swarm]):.1f}%")
        st.session_state.time_step += 1; time.sleep(0.2); st.rerun()
    else:
        st.info("Simulation paused.")

with tabs[2]:
    st.markdown("<h2>Mission Control</h2>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    for col, title, val in zip([c1, c2, c3], ["Signal", "Energy", "Latency"], [90, np.mean([n.energy for n in st.session_state.nano_swarm]), 20]):
        fig = go.Figure(go.Indicator(mode="gauge+number", value=val, title={'text':title, 'font':{'color':COLOR_TEXT_LIGHT}},
            gauge={'axis':{'range':[0,100], 'tickcolor':COLOR_TEXT_LIGHT}, 'bar':{'color':COLOR_PRIMARY}, 'bgcolor':COLOR_BG_MEDIUM}))
        fig.update_layout(height=200, paper_bgcolor=COLOR_BG_DARK, font={'color':COLOR_TEXT_LIGHT})
        col.plotly_chart(fig, use_container_width=True)
    c1, c2, c3 = st.columns(3)
    with c2:
        if st.button("⬆ Up"): st.session_state.manual_dx = -1; log_event("INFO", "Manual: Up")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("⬅ Left"): st.session_state.manual_dy = -1; log_event("INFO", "Manual: Left")
    with c3:
        if st.button("➡ Right"): st.session_state.manual_dy = 1; log_event("INFO", "Manual: Right")
    with c2:
        if st.button("⬇ Down"): st.session_state.manual_dx = 1; log_event("INFO", "Manual: Down")
    if st.button("Reset Override"): st.session_state.manual_dx = 0; st.session_state.manual_dy = 0
    if st.button("▶ ACTIVATE NANO-SWARM"): st.session_state.simulation_running = True; log_event("INFO", "Swarm Activated")
    if st.button("🛑 EMERGENCY SHUTDOWN"): st.session_state.simulation_running = False; log_event("ERROR", "Emergency Shutdown")

with tabs[3]:
    st.markdown(f"<div class='production-lift-display'>Nano Lift: {lift:+.2f}%</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    st.session_state.oil_viscosity_factor = c1.slider("Oil Viscosity", 0.5, 2.0, st.session_state.oil_viscosity_factor)
    st.session_state.water_salinity_factor = c2.slider("Salinity", 0.5, 2.0, st.session_state.water_salinity_factor)
    res.current_viscosity_modifier = st.session_state.oil_viscosity_factor
    res.current_salinity_modifier = st.session_state.water_salinity_factor
    if len(st.session_state.nano_production_history) > 1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=st.session_state.nano_production_history, name="Nano-Swarm", line=dict(color=COLOR_PRIMARY, width=4)))
        fig.add_trace(go.Scatter(y=st.session_state.traditional_production_history, name="Traditional", line=dict(dash='dash', color=COLOR_TEXT_LIGHT)))
        fig.update_layout(height=400, template="plotly_dark", paper_bgcolor=COLOR_BG_DARK, plot_bgcolor=COLOR_BG_MEDIUM)
        st.plotly_chart(fig, use_container_width=True)
    fig_sens = go.Figure(go.Bar(x=[0.8, 0.95, 0.7, 0.6, 0.85], y=["Pressure", "Nano Conc.", "Viscosity", "Salinity", "Perm."], orientation='h', marker_color=COLOR_PRIMARY))
    fig_sens.update_layout(title="Sensitivity Analysis", height=300, paper_bgcolor=COLOR_BG_DARK, plot_bgcolor=COLOR_BG_MEDIUM, font={'color':COLOR_TEXT_LIGHT})
    st.plotly_chart(fig_sens, use_container_width=True)

with tabs[4]:
    st.markdown("<h2>Economics & Sustainability</h2>", unsafe_allow_html=True)
    oil_price = st.number_input("Oil Price ($/bbl)", 50, 150, 80)
    opex = st.number_input("Daily OPEX ($)", 1000, 50000, 5000)
    rev = nano_prod * oil_price
    net = rev - opex
    roi = (net / opex * 100) if opex > 0 else 0
    if roi > st.session_state.best_roi: st.session_state.best_roi = roi
    c1, c2, c3 = st.columns(3)
    c1.metric("Revenue", f"${rev:,.2f}")
    c2.metric("Net Value", f"${net:,.2f}")
    c3.metric("ROI", f"{roi:,.2f}%")
    if lift > 0:
        st.session_state.total_water_saved += (nano_prod - trad_prod) * 0.5 * 0.01
        st.session_state.carbon_reduction += (nano_prod - trad_prod) * 0.05 * 0.01
    c1, c2 = st.columns(2)
    c1.metric("Water Saved (bbl)", f"{st.session_state.total_water_saved:,.2f}")
    c2.metric("CO2 Reduction (tons)", f"{st.session_state.carbon_reduction:,.2f}")

with tabs[5]:
    st.markdown("<h2>Field Operations Map</h2>", unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_trace(go.Heatmap(z=res.nano_concentration_grid, colorscale="Plasma"))
    fig.add_trace(go.Scatter(x=[st.session_state.injection_well_loc[0]], y=[st.session_state.injection_well_loc[1]], mode='markers', marker=dict(size=15, color=COLOR_SECONDARY, symbol='triangle-up'), name="Injection"))
    fig.add_trace(go.Scatter(x=[st.session_state.production_well_loc[0]], y=[st.session_state.production_well_loc[1]], mode='markers', marker=dict(size=15, color=COLOR_PRIMARY, symbol='star'), name="Production"))
    fig.update_layout(height=600, paper_bgcolor=COLOR_BG_DARK, plot_bgcolor=COLOR_BG_MEDIUM, font={'color':COLOR_TEXT_LIGHT})
    st.plotly_chart(fig, use_container_width=True)

with tabs[6]:
    st.markdown("<h2>Technical Report</h2>", unsafe_allow_html=True)
    if st.button("Generate Report"):
        report = f"# Nano-Swarm EOR Report\n\n**Best Production:** {st.session_state.best_production:.2f} bbl/day\n**Max Lift:** {lift:+.2f}%\n**Avg Energy:** {np.mean([n.energy for n in st.session_state.nano_swarm]):.1f}%"
        st.download_button("Download Report", report, "report.md")

with tabs[7]:
    st.markdown("<h2>Project Guide / دليل المشروع</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class='guide-section'>
        <h3>About the Project / عن المشروع</h3>
        <p><b>English:</b> This project simulates an intelligent Nano-Robot Swarm for Enhanced Oil Recovery (EOR). The swarm navigates the reservoir to identify trapped oil, reduce viscosity, and alter rock wettability, significantly increasing production efficiency while reducing environmental impact.</p>
        <p><b>العربية:</b> يهدف هذا المشروع إلى محاكاة سرب من الروبوتات النانوية الذكية لتحسين استخراج النفط. يقوم السرب بالتنقل داخل المكمن لتحديد أماكن النفط المحبوس، وتقليل اللزوجة، وتغيير بللية الصخور، مما يرفع كفاءة الإنتاج بشكل كبير مع تقليل الآثار البيئية.</p>
    </div>
    
    <div class='guide-section'>
        <h3>How to Run / طريقة التشغيل</h3>
        <p><b>English:</b> 1. Install dependencies: <code>pip install streamlit pandas numpy plotly scipy openpyxl</code>. 2. Place Excel files (PVTO, Rel-Perm, Capillary, Pro) in the same folder. 3. Run: <code>streamlit run [filename].py</code>.</p>
        <p><b>العربية:</b> 1. تثبيت المكتبات المطلوبة. 2. وضع ملفات الإكسل الأربعة في نفس مجلد الكود. 3. تشغيل الأمر <code>streamlit run [filename].py</code> في الطرفية.</p>
    </div>
    
    <div class='guide-section'>
        <h3>Key Features / المميزات الفخمة</h3>
        <ul>
            <li><b>Digital Twin:</b> 3D real-time subsurface visualization.</li>
            <li><b>Mission Control:</b> Full swarm management and manual override.</li>
            <li><b>AI Analytics:</b> Predictive forecasting and sensitivity analysis.</li>
            <li><b>ROI Calculations:</b> Real-time economic and sustainability metrics.</li>
        </ul>
    </div>
    
    <div class='guide-section'>
        <h3>Development Team / فريق العمل</h3>
        <div class='team-member'>• Bashar Abdullah salah Al-zaidy</div>
        <div class='team-member'>• Rafa Saeed Abdullah Al-Qadasi</div>
        <div class='team-member'>• Ahmed Haysami Ahmed Alhaisami</div>
        <div class='team-member'>• Radman Hames Ahmed Omair</div>
        <div class='team-member'>• Abdulqader Rafat Saeed Awadh Ben Fareg</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.markdown("<h2>🧠 System Event Console</h2>", unsafe_allow_html=True)
log_container = st.empty()
log_html = "<div class='log-console'>"
for msg in reversed(st.session_state.logs[-20:]):
    log_html += f"<p style='color:{COLOR_PRIMARY};'>[{msg[1]}] {msg[2]}</p>"
log_html += "</div>"
log_container.markdown(log_html, unsafe_allow_html=True)
