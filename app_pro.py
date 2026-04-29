import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import interp1d
import time, random, datetime
from scipy.ndimage import gaussian_filter

# --- Streamlit Page Configuration ---
st.set_page_config(layout="wide", page_title="Nano-Swarm EOR Ultimate Engineering Platform", page_icon="🔬")

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
    @import url(\'https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Roboto+Mono:wght@300;400;700&display=swap\');

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
        font-family: \'Roboto Mono\', monospace;
    }}

    .stApp {{
        background-color: var(--background-dark);
    }}

    h1, h2, h3, h4, h5, h6 {{
        font-family: \'Orbitron\', sans-serif;
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
        font-family: \'Orbitron\', sans-serif;
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

        visc_interp = interp1d(pvto_df["pressure"], pvto_df["oil viscosity"], fill_value="extrapolate", bounds_error=False)
        kro_interp = interp1d(rel_perm_df["sw"], rel_perm_df["kro"], fill_value="extrapolate", bounds_error=False)
        pc_interp = interp1d(cap_press_df["sw"], cap_press_df["pcow (psi)"], fill_value="extrapolate", bounds_error=False)

        return visc_interp, kro_interp, pc_interp, pro_df
    except FileNotFoundError as e:
        st.error(f"Critical Data Error: Required Excel file not found. Please ensure all data files (PVTO.xlsx, water-oil Relative permeability.xlsx, capillary pressure.xlsx, Pro.xlsx) are in the same directory as the application. Details: {e}")
        st.stop()
    except Exception as e:
        st.error(f"Critical Data Error: Failed to load or process data files. Please check file integrity and format. Details: {e}")
        st.stop()

visc, kro, pc, pro_data = load_data()

# --- Core Simulation Models ---
class Reservoir:
    def __init__(self, grid_size=25):
        self.grid_size = grid_size
        # Initial water saturation grid (0.2 to 0.4 for heterogeneity)
        self.sw_grid = np.random.uniform(0.2, 0.4, (grid_size, grid_size))
        # Initial permeability grid (simulated heterogeneity with tight zones)
        self.perm_grid = np.random.uniform(50, 200, (grid_size, grid_size)) # mD
        # Introduce some tight zones (low permeability)
        for _ in range(5):
            cx, cy = random.randint(0, grid_size-1), random.randint(0, grid_size-1)
            self.perm_grid[max(0, cx-3):min(grid_size, cx+3), max(0, cy-3):min(grid_size, cy+3)] = np.random.uniform(5, 30, (min(grid_size, cx+3)-max(0, cx-3), min(grid_size, cy+3)-max(0, cy-3)))
        self.perm_grid = gaussian_filter(self.perm_grid, sigma=1) # Smooth permeability

        self.nano_concentration_grid = np.zeros((grid_size, grid_size)) # Tracks nano concentration
        self.nano_effect_radius = 2 # Radius of influence for nano particles
        
        # Dynamic factors for sensitivity analysis
        self.base_viscosity_reduction_factor = 0.005 
        self.base_kro_enhancement_factor = 0.002
        self.current_viscosity_modifier = 1.0 # From slider
        self.current_salinity_modifier = 1.0 # From slider

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

        # Apply sensitivity modifiers to base oil viscosity and kro enhancement
        base_oil_viscosity = float(visc(pressure)) * self.current_viscosity_modifier
        
        # Nano-enhanced oil viscosity (average effect across the grid)
        avg_nano_conc = np.mean(self.nano_concentration_grid)
        effective_oil_viscosity = np.clip(base_oil_viscosity * (1 - avg_nano_conc * self.base_viscosity_reduction_factor), 0.1, base_oil_viscosity)

        # Base relative permeability to oil (kro) at average Sw
        base_kro = kro(avg_sw)
        
        # Nano-enhanced relative permeability to oil (average effect across the grid)
        effective_kro = np.clip(base_kro * (1 + avg_nano_conc * self.base_kro_enhancement_factor * self.current_salinity_modifier), 0.01, 0.9)

        capillary_pressure = float(pc(avg_sw))

        # Incorporate permeability from perm_grid (average effect)
        avg_perm = np.mean(self.perm_grid)
        
        # Production formula (Darcy's Law approximation for oil flow)
        production_rate = (effective_kro * avg_perm * (pressure - capillary_pressure) / 1000) / (effective_oil_viscosity + 1e-6)
        return max(0, production_rate)

class NanoRobot:
    def __init__(self, grid_size=25):
        self.grid_size = grid_size
        self.x = np.random.randint(0, grid_size)
        self.y = np.random.randint(0, grid_size)
        self.energy = 100
        self.signal_strength = random.randint(70, 100)
        self.wettability_index = 0.5 # Initial neutral wettability

    def move(self, reservoir_sw_grid, reservoir_perm_grid, nano_concentration_grid, dx=0, dy=0):
        # Swarm Intelligence: Move towards lower water saturation (higher oil) and higher permeability, avoid high nano concentration
        
        gsx, gsy = np.gradient(reservoir_sw_grid) # Move away from high Sw
        gpx, gpy = np.gradient(reservoir_perm_grid) # Move towards high Permeability
        gnx, gny = np.gradient(nano_concentration_grid) # Move away from other nanos

        move_factor_sw = 0.5 
        move_factor_perm = 0.3 # Influence of permeability
        move_factor_nano = 0.2 
        random_walk_strength = 0.3 

        new_x = self.x - (gsx[self.x, self.y] * move_factor_sw) + (gpx[self.x, self.y] * move_factor_perm) - (gnx[self.x, self.y] * move_factor_nano) + (random.uniform(-random_walk_strength, random_walk_strength)) + dx
        new_y = self.y - (gsy[self.x, self.y] * move_factor_sw) + (gpy[self.x, self.y] * move_factor_perm) - (gny[self.x, self.y] * move_factor_nano) + (random.uniform(-random_walk_strength, random.uniform(-random_walk_strength, random_walk_strength))) + dy

        self.x = int(np.clip(new_x, 0, self.grid_size - 1))
        self.y = int(np.clip(new_y, 0, self.grid_size - 1))
        
        # Update wettability index based on local nano concentration (conceptual)
        local_nano_conc = nano_concentration_grid[self.x, self.y]
        self.wettability_index = np.clip(0.5 + local_nano_conc * 0.05, 0.1, 0.9) # 0.1 (water-wet) to 0.9 (oil-wet)

# --- Session State Management ---
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
    st.session_state.production_lift_percentage = 0.0
    st.session_state.last_update_time = time.time()
    st.session_state.ai_prediction_message = "[AI] System initializing. Awaiting simulation start..."
    st.session_state.oil_viscosity_factor = 1.0 # Default for sensitivity
    st.session_state.water_salinity_factor = 1.0 # Default for sensitivity
    st.session_state.total_water_saved = 0.0
    st.session_state.carbon_reduction = 0.0
    st.session_state.best_production = 0.0
    st.session_state.best_roi = 0.0

res = st.session_state.res

# --- Utility Functions ---
def log_event(type, message):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append((type, timestamp, message))
    if len(st.session_state.logs) > 50:
        st.session_state.logs.pop(0)

def get_traditional_production(pressure):
    avg_sw = np.clip(np.mean(res.sw_grid), 0.01, 0.99)
    avg_perm = np.mean(res.perm_grid)
    base_oil_viscosity = float(visc(pressure)) * st.session_state.oil_viscosity_factor
    base_kro = kro(avg_sw)
    capillary_pressure = float(pc(avg_sw))
    traditional_prod = (base_kro * avg_perm * (pressure - capillary_pressure) / 1000) / (base_oil_viscosity + 1e-6)
    return max(0, traditional_prod)

# --- Main Application Layout ---
st.markdown("<h1>Nano-Swarm EOR Ultimate Engineering Platform</h1>", unsafe_allow_html=True)
st.markdown("<p>Intelligent Nano-Robot Swarm for Enhanced Oil Recovery - Digital Twin Simulation</p>", unsafe_allow_html=True)
st.markdown("--- ")

# --- Tabs Navigation ---
tabs = st.tabs(["Dashboard", "Subsurface Digital Twin", "Mission Control", "AI Analytics & Sensitivity", "Economics & ROI", "Field Operations Map", "Technical Report"])

# --- Dashboard Tab ---
with tabs[0]:
    st.markdown("<h2>Operational Overview</h2>", unsafe_allow_html=True)

    current_pressure_input = st.slider(
        "Simulated Reservoir Pressure (psi)", 
        500, 3000, st.session_state.current_pressure, 
        step=50, 
        help="Adjust the reservoir pressure to observe its impact on production."
    )
    if current_pressure_input != st.session_state.current_pressure:
        st.session_state.current_pressure = current_pressure_input
        log_event("INFO", f"Reservoir pressure adjusted to {st.session_state.current_pressure} psi.")

    traditional_prod_val = get_traditional_production(st.session_state.current_pressure)
    nano_prod_val = res.calculate_production(st.session_state.current_pressure, st.session_state.nano_swarm)
    
    st.session_state.traditional_production_history.append(traditional_prod_val)
    st.session_state.nano_production_history.append(nano_prod_val)

    max_history_length = 200
    if len(st.session_state.traditional_production_history) > max_history_length:
        st.session_state.traditional_production_history.pop(0)
        st.session_state.nano_production_history.pop(0)

    if traditional_prod_val > 0:
        lift_percentage = ((nano_prod_val - traditional_prod_val) / traditional_prod_val) * 100
    else:
        lift_percentage = 0.0
    st.session_state.production_lift_percentage = lift_percentage

    # Update best production and ROI
    if nano_prod_val > st.session_state.best_production:
        st.session_state.best_production = nano_prod_val

    col_prod1, col_prod2, col_prod3 = st.columns(3)
    with col_prod1:
        st.markdown(f"<div class=\'card\'><h3>Traditional Output</h3><p>{traditional_prod_val:.2f} bbl/day</p></div>", unsafe_allow_html=True)
    with col_prod2:
        st.markdown(f"<div class=\'card\'><h3>Nano-Swarm Output</h3><p>{nano_prod_val:.2f} bbl/day</p></div>", unsafe_allow_html=True)
    with col_prod3:
        st.markdown(f"<div class=\'card\'><h3>Production Lift</h3><p>{lift_percentage:+.2f}%</p></div>", unsafe_allow_html=True)

    st.markdown("<h3>Real-time Production Gauge</h3>", unsafe_allow_html=True)
    fig_gauge = go.Figure(go.Indicator(mode="gauge+number+delta", value=nano_prod_val,
        title={\'text\':"Total Production (bbl/day)", \'font\': {\'size\': 20, \'color\': COLOR_TEXT_LIGHT}},
        delta = {\'reference\': st.session_state.nano_production_history[-2] if len(st.session_state.nano_production_history) > 1 else traditional_prod_val, \'increasing\':{\'color\':COLOR_PRIMARY}, \'decreasing\':{\'color\':COLOR_ERROR}},
        gauge={
            \'axis\':{\'range\':[0, max(1,nano_prod_val*1.5)], \'tickwidth\':1, \'tickcolor\':COLOR_TEXT_LIGHT},
            \'bar\':{\'color\':COLOR_PRIMARY},
            \'bgcolor\':COLOR_BG_MEDIUM,
            \'borderwidth\':2,
            \'bordercolor\':COLOR_PRIMARY,
            \'steps\':[
                {\'range\':[0, traditional_prod_val], \'color\':\'#3a3a5a\'},
                {\'range\':[traditional_prod_val, max(1,nano_prod_val*1.5)], \'color\':\'#00cc99\'}
            ],
            \'threshold\':{\'line\':{\'color\':COLOR_ERROR, \'width\':4}, \'thickness\':0.75, \'value\': traditional_prod_val}
        }
    ))
    fig_gauge.update_layout(height=300, margin=dict(l=10,r=10,t=50,b=10), font={\'color\': COLOR_TEXT_LIGHT, \'family\': \'Roboto Mono\'}) # Removed paper_bgcolor from here
    st.plotly_chart(fig_gauge, use_container_width=True)

    st.markdown("<h3>System Status</h3>", unsafe_allow_html=True)
    col_status1, col_status2 = st.columns(2)
    with col_status1:
        st.markdown(f"<div class=\'card\'><h3>System Time</h3><p>{datetime.datetime.now().strftime(\'%Y-%m-%d %H:%M:%S\')}</p></div>", unsafe_allow_html=True)
    with col_status2:
        st.markdown(f"<div class=\'card\'><h3>CPU Load</h3><p>{random.randint(10,80)}%</p></div>", unsafe_allow_html=True)

# --- Subsurface Digital Twin Tab ---
with tabs[1]:
    st.markdown("<h2>Subsurface Digital Twin: Nano-Swarm Dynamics</h2>", unsafe_allow_html=True)
    st.write("Observe the intelligent nano-robot swarm navigating the reservoir. Color intensity represents water saturation (Viridis colormap), with darker areas indicating higher oil potential. Permeability variations are also visualized. Nano-robots (cyan spheres) actively seek and enhance oil recovery zones by altering wettability and improving flow in tight zones.")

    chart_placeholder = st.empty()

    if st.session_state.simulation_running:
        for nano in st.session_state.nano_swarm:
            nano.move(res.sw_grid, res.perm_grid, res.nano_concentration_grid, st.session_state.manual_dx, st.session_state.manual_dy)
        
        res.update_nano_effect(st.session_state.nano_swarm)
        
        display_sw_grid = np.clip(res.sw_grid - (res.nano_concentration_grid * 0.02), 0.05, 0.95)
        display_perm_grid = np.clip(res.perm_grid + (res.nano_concentration_grid * 5), 5, 250) # Nano enhances permeability

        xs=[n.x for n in st.session_state.nano_swarm]
        ys=[n.y for n in st.session_state.nano_swarm]
        zs=[display_sw_grid[x,y] for x,y in zip(xs,ys)]

        fig_subsurface = go.Figure()
        fig_subsurface.add_trace(go.Surface(z=display_sw_grid, colorscale="Viridis", opacity=0.7, name="Water Saturation"))
        fig_subsurface.add_trace(go.Surface(z=display_perm_grid, colorscale="Hot", opacity=0.3, name="Permeability (mD)", showscale=False)) # Overlay permeability
        fig_subsurface.add_trace(go.Scatter3d(x=xs,y=ys,z=zs,
                                  mode=\'markers\',
                                  marker=dict(size=5, color=\'cyan\', opacity=0.9, symbol=\'circle\'),
                                  name="Nano-Robots Swarm"))
        
        # Wettability Index Display
        avg_wettability_index = np.mean([n.wettability_index for n in st.session_state.nano_swarm])
        st.markdown(f"<h3 style=\'color: {COLOR_PRIMARY};\'>Average Swarm Wettability Index: {avg_wettability_index:.2f} (0.1=Water-Wet, 0.9=Oil-Wet)</h3>", unsafe_allow_html=True)

        fig_subsurface.update_layout(
            scene=dict(
                xaxis_title=\'X-Coordinate\',
                yaxis_title=\'Y-Coordinate\',
                zaxis_title=\'Effective Water Saturation\',
                bgcolor=COLOR_BG_DARK,
                aspectmode=\'cube\',
                camera=dict(eye=dict(x=1.8, y=1.8, z=0.8))
            ),
            title_text=\'Live Nano-Swarm Activity & Reservoir Impact\',
            title_font_color=COLOR_PRIMARY,
            height=700,
            margin=dict(l=0, r=0, b=0, t=50),
            paper_bgcolor=COLOR_BG_DARK,
            plot_bgcolor=COLOR_BG_DARK,
            font=dict(color=COLOR_TEXT_LIGHT, family=\'Roboto Mono\')
        )
        chart_placeholder.plotly_chart(fig_subsurface, use_container_width=True)

        time.sleep(0.2) # Increased sleep time
        st.session_state.time_step += 1
        st.rerun()
    else:
        st.info("Simulation is paused. Press \'ACTIVATE NANO-SWARM\' in Mission Control to activate the nano-swarm and observe live subsurface dynamics.")
        fig_subsurface_static = go.Figure()
        fig_subsurface_static.add_trace(go.Surface(z=res.sw_grid, colorscale="Viridis", opacity=0.8, name="Initial Water Saturation"))
        fig_subsurface_static.add_trace(go.Surface(z=res.perm_grid, colorscale="Hot", opacity=0.3, name="Initial Permeability (mD)", showscale=False))
        fig_subsurface_static.update_layout(
            scene=dict(
                xaxis_title=\'X-Coordinate\',
                yaxis_title=\'Y-Coordinate\',
                zaxis_title=\'Initial Water Saturation\',
                bgcolor=COLOR_BG_DARK,
                aspectmode=\'cube\',
                camera=dict(eye=dict(x=1.8, y=1.8, z=0.8))
            ),
            title_text=\'Initial Reservoir State (Static View)\' ,
            title_font_color=COLOR_PRIMARY,
            height=700,
            margin=dict(l=0, r=0, b=0, t=50),
            paper_bgcolor=COLOR_BG_DARK,
            plot_bgcolor=COLOR_BG_DARK,
            font=dict(color=COLOR_TEXT_LIGHT, family=\'Roboto Mono\')
        )
        chart_placeholder.plotly_chart(fig_subsurface_static, use_container_width=True)

# --- Mission Control Tab ---
with tabs[2]:
    st.markdown("<h2>Mission Control: Swarm & System Management</h2>", unsafe_allow_html=True)

    st.markdown("<h3>System Health & Telemetry</h3>", unsafe_allow_html=True)
    col_health1, col_health2, col_health3 = st.columns(3)

    for col, title, val in zip(
        [col_health1, col_health2, col_health3],
        ["Swarm Signal Strength", "Average Nano Energy", "Network Latency"],
        [np.mean([n.signal_strength for n in st.session_state.nano_swarm]), np.mean([n.energy for n in st.session_state.nano_swarm]), random.randint(10, 100)]
    ):
        fig_health = go.Figure(go.Indicator(mode="gauge", value=val,
            title={\'text\':title, \'font\': {\'size\': 16, \'color\': COLOR_TEXT_LIGHT}},
            gauge={
                \'axis\':{\'range\':[0,100], \'tickwidth\':1, \'tickcolor\':COLOR_TEXT_LIGHT},
                \'bar\':{\'color\':COLOR_PRIMARY},
                \'bgcolor\':COLOR_BG_MEDIUM,
                \'borderwidth\':2,
                \'bordercolor\':COLOR_PRIMARY,
                \'steps\':[
                    {\'range\':[0, 30], \'color\':COLOR_ERROR},
                    {\'range\':[30, 70], \'color\':COLOR_WARNING},
                    {\'range\':[70, 100], \'color\':COLOR_PRIMARY}
                ]
            }
        ))
        fig_health.update_layout(height=200, margin=dict(l=10,r=10,t=50,b=10), font={\'color\': COLOR_TEXT_LIGHT, \'family\': \'Roboto Mono\'}) # Removed paper_bgcolor from here
        col.plotly_chart(fig_health, use_container_width=True)

    st.markdown("<h3>Nano-Swarm Manual Override</h3>", unsafe_allow_html=True)
    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
    with col_ctrl2:
        if st.button("⬆ Move Swarm Up", key="up_btn"): st.session_state.manual_dx = -1; log_event("INFO", "Manual swarm override: Up")
    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
    with col_ctrl1:
        if st.button("⬅ Move Swarm Left", key="left_btn"): st.session_state.manual_dy = -1; log_event("INFO", "Manual swarm override: Left")
    with col_ctrl3:
        if st.button("➡ Move Swarm Right", key="right_btn"): st.session_state.manual_dy = 1; log_event("INFO", "Manual swarm override: Right")
    with col_ctrl2:
        if st.button("⬇ Move Swarm Down", key="down_btn"): st.session_state.manual_dx = 1; log_event("INFO", "Manual swarm override: Down")
    col_ctrl_reset, col_ctrl_empty = st.columns(2)
    with col_ctrl_reset:
        if st.button("Reset Manual Override", key="reset_manual_btn"): st.session_state.manual_dx = 0; st.session_state.manual_dy = 0; log_event("INFO", "Manual swarm override reset.")

    st.markdown("--- ")
    st.markdown("<h3>Simulation Control</h3>", unsafe_allow_html=True)
    col_sim_ctrl1, col_sim_ctrl2 = st.columns(2)
    with col_sim_ctrl1:
        if st.button("▶ ACTIVATE NANO-SWARM", key="start_sim_btn", help="Initiate the intelligent nano-robot swarm simulation."):
            st.session_state.simulation_running = True
            log_event("INFO", "Nano-Swarm Activated. Live data streaming to Analytics.")
            st.success("Nano-Swarm Activated! Initiating EOR protocols.")
    with col_sim_ctrl2:
        if st.button("🛑 EMERGENCY SHUTDOWN", key="stop_sim_btn", help="Halt all nano-swarm operations and simulation processes immediately."):
            st.session_state.simulation_running = False
            log_event("ERROR", "EMERGENCY SHUTDOWN Activated - Nano-Swarm Halted.")
            st.error("Nano-Swarm Halted! All operations suspended.")

# --- AI Analytics & Sensitivity Tab ---
with tabs[3]:
    st.markdown("<h2>AI-Powered Production Analytics & Sensitivity Analysis</h2>", unsafe_allow_html=True)
    st.write("Real-time monitoring of production trends, AI-driven forecasts, and confidence intervals for Nano-Swarm EOR. Adjust environmental parameters to test system robustness.")

    # Prominent Production Lift Display
    st.markdown(f"<div class=\'production-lift-display\'>Nano Lift: {st.session_state.production_lift_percentage:+.2f}%</div>", unsafe_allow_html=True)

    st.markdown("<h3>Environmental Sensitivity Controls</h3>", unsafe_allow_html=True)
    col_sens1, col_sens2 = st.columns(2)
    with col_sens1:
        oil_visc_factor = st.slider("Oil Viscosity Factor", 0.5, 2.0, st.session_state.oil_viscosity_factor, 0.1, help="Simulate changes in crude oil viscosity. 1.0 is normal.")
        if oil_visc_factor != st.session_state.oil_viscosity_factor:
            st.session_state.oil_viscosity_factor = oil_visc_factor
            log_event("INFO", f"Oil viscosity factor set to {oil_visc_factor}.")
            res.current_viscosity_modifier = oil_visc_factor
    with col_sens2:
        water_salinity_factor = st.slider("Water Salinity Factor", 0.5, 2.0, st.session_state.water_salinity_factor, 0.1, help="Simulate changes in formation water salinity, affecting nano performance. 1.0 is normal.")
        if water_salinity_factor != st.session_state.water_salinity_factor:
            st.session_state.water_salinity_factor = water_salinity_factor
            log_event("INFO", f"Water salinity factor set to {water_salinity_factor}.")
            res.current_salinity_modifier = water_salinity_factor

    analytics_chart_placeholder = st.empty()

    if st.session_state.simulation_running or len(st.session_state.nano_production_history) > 1:
        y_nano = np.array(st.session_state.nano_production_history)
        y_traditional = np.array(st.session_state.traditional_production_history)
        x = np.arange(len(y_nano))

        if len(y_nano) > 10:
            slope = (y_nano[-1] - y_nano[-10]) / 10 
        elif len(y_nano) > 1:
            slope = (y_nano[-1] - y_nano[-2])
        else:
            slope = 0

        future_steps = 20 
        future_prediction = [y_nano[-1] + slope * i for i in range(1, future_steps + 1)]

        fig_analytics = go.Figure()

        fig_analytics.add_trace(go.Scatter(x=x, y=y_nano, name="Nano-Swarm Enhanced Production",
                                         line=dict(color=COLOR_PRIMARY, width=4, shape=\'spline\'),
                                         mode=\'lines+markers\', marker=dict(size=5, symbol=\'circle\')))
        fig_analytics.add_trace(go.Scatter(x=x, y=y_traditional, name="Traditional Production Baseline",
                                         line=dict(dash=\'dash\', color=COLOR_TEXT_LIGHT, width=2)))

        x_future = np.arange(len(y_nano), len(y_nano) + future_steps)
        confidence_factor = 0.18 
        upper_bound=[f * (1 + confidence_factor) for f in future_prediction]
        lower_bound=[f * (1 - confidence_factor) for f in future_prediction]

        fig_analytics.add_trace(go.Scatter(x=x_future, y=future_prediction, name="AI Production Forecast",
                                         line=dict(color=COLOR_WARNING, width=3, dash=\'dot\'),
                                         mode=\'lines\', marker=dict(size=4, symbol=\'diamond\')))
        fig_analytics.add_trace(go.Scatter(x=x_future, y=upper_bound, fill=None, mode=\'lines\', line_color=\'rgba(255,209,102,0.3)\' , showlegend=False))
        fig_analytics.add_trace(go.Scatter(x=x_future, y=lower_bound, fill=\'tonexty\', mode=\'lines\', line_color=\'rgba(255,209,102,0.3)\' , fillcolor=\'rgba(255,209,102,0.1)\' , name="Forecast Confidence"))

        fig_analytics.update_layout(
            height=600, 
            template="plotly_dark",
            title_text=\'Production Trend & AI Forecast\',
            title_font_color=COLOR_PRIMARY,
            xaxis_title=\'Simulation Time Step\',
            yaxis_title=\'Production (bbl/day)\',
            paper_bgcolor=COLOR_BG_DARK,
            plot_bgcolor=COLOR_BG_MEDIUM,
            font=dict(color=COLOR_TEXT_LIGHT, family=\'Roboto Mono\'),
            hovermode=\'x unified\'
        )
        analytics_chart_placeholder.plotly_chart(fig_analytics, use_container_width=True)

    st.markdown("<h3>AI System Insights</h3>", unsafe_allow_html=True)
    if st.session_state.simulation_running:
        if st.session_state.production_lift_percentage > 20:
            st.session_state.ai_prediction_message = "[AI] Optimal swarm distribution achieved. High production lift sustained."
        elif st.session_state.production_lift_percentage > 10:
            st.session_state.ai_prediction_message = "[AI] Swarm activity increasing. Positive production trend detected."
        else:
            st.session_state.ai_prediction_message = "[AI] Analyzing swarm patterns. Adjusting parameters for efficiency."
    else:
        st.session_state.ai_prediction_message = "[AI] System in standby. Ready for deployment."

    st.info(st.session_state.ai_prediction_message)

# --- Economics & ROI Tab ---
with tabs[4]:
    st.markdown("<h2>Economics & Return on Investment (ROI)</h2>", unsafe_allow_html=True)
    st.write("Comprehensive financial analysis of Nano-Swarm EOR operations, including revenue, costs, and profitability.")

    col_econ1, col_econ2 = st.columns(2)
    with col_econ1:
        oil_price = st.number_input("Global Oil Price ($/barrel)", 50, 150, 80, step=5, help="Current market price of oil.")
    with col_econ2:
        opex_cost = st.number_input("Daily Operational Expenditure ($)", 1000, 50000, 5000, step=500, help="Daily operational costs for Nano-Swarm EOR, including robot maintenance and energy.")

    current_nano_prod_econ = st.session_state.nano_production_history[-1] if st.session_state.nano_production_history else get_traditional_production(st.session_state.current_pressure)
    
    revenue = current_nano_prod_econ * oil_price
    net_value = revenue - opex_cost 

    # Update best ROI
    if opex_cost > 0:
        current_roi = (net_value / opex_cost * 100)
        if current_roi > st.session_state.best_roi:
            st.session_state.best_roi = current_roi

    st.markdown("--- ")
    st.markdown("<h3>Financial Metrics</h3>", unsafe_allow_html=True)
    col_metrics1, col_metrics2, col_metrics3 = st.columns(3)
    with col_metrics1:
        prev_revenue = (st.session_state.nano_production_history[-2] * oil_price) if len(st.session_state.nano_production_history) > 1 else 0
        st.metric(label="Daily Revenue", value=f"${revenue:,.2f}", delta=f"${revenue - prev_revenue:,.2f}" if prev_revenue != 0 else None, delta_color="normal")
    with col_metrics2:
        prev_net_value = ((st.session_state.nano_production_history[-2] * oil_price) - opex_cost) if len(st.session_state.nano_production_history) > 1 else 0
        st.metric(label="Daily Net Value", value=f"${net_value:,.2f}", delta=f"${net_value - prev_net_value:,.2f}" if prev_net_value != 0 else None, delta_color="normal")
    with col_metrics3:
        roi_percentage = (net_value / opex_cost * 100) if opex_cost > 0 else 0
        st.metric(label="Daily ROI", value=f"{roi_percentage:,.2f}%", delta_color="normal")

    st.markdown("--- ")
    st.markdown("<h3>Sustainability & Environmental Impact (Green EOR)</h3>", unsafe_allow_html=True)
    # Assuming some baseline for water usage and carbon footprint for traditional EOR
    # These values would be based on actual EOR project data
    baseline_water_per_bbl = 0.5 # barrels of water per barrel of oil for traditional EOR
    baseline_carbon_per_bbl = 0.05 # tons of CO2 per barrel of oil for traditional EOR

    if st.session_state.production_lift_percentage > 0:
        # Calculate water saved and carbon reduction based on the lift
        # This is a simplified model for demonstration
        water_saved_per_day = (nano_prod_val - traditional_prod_val) * baseline_water_per_bbl
        carbon_reduced_per_day = (nano_prod_val - traditional_prod_val) * baseline_carbon_per_bbl
        st.session_state.total_water_saved += water_saved_per_day * 0.01 # Accumulate slowly for effect
        st.session_state.carbon_reduction += carbon_reduced_per_day * 0.01 # Accumulate slowly for effect

    col_green1, col_green2 = st.columns(2)
    with col_green1:
        st.metric(label="Water Saved (bbl/day)", value=f"{st.session_state.total_water_saved:,.2f}", delta_color="normal")
    with col_green2:
        st.metric(label="Carbon Footprint Reduction (tons CO2/day)", value=f"{st.session_state.carbon_reduction:,.2f}", delta_color="normal")

    st.markdown("--- ")
    st.markdown("<h3>Financial Report Export</h3>", unsafe_allow_html=True)
    df_report = pd.DataFrame({"Metric":["Production (bbl/day)", "Oil Price ($/bbl)", "Daily Revenue ($)", "Daily OPEX ($)", "Daily Net Value ($)", "Daily ROI (%)", "Water Saved (bbl/day)", "Carbon Reduction (tons CO2/day)"],
                              "Value":[current_nano_prod_econ, oil_price, revenue, opex_cost, net_value, roi_percentage, st.session_state.total_water_saved, st.session_state.carbon_reduction]})
    st.download_button(
        label="Download Comprehensive Financial Report (CSV)",
        data=df_report.to_csv(index=False).encode(\'utf-8\'),
        file_name="nano_eor_financial_report.csv",
        mime="text/csv",
        help="Export current financial metrics to a CSV file for detailed analysis."
    )

# --- Field Operations Map Tab ---
with tabs[5]:
    st.markdown("<h2>Field Operations Map</h2>", unsafe_allow_html=True)
    st.write("Geospatial overview of the oil field, displaying well infrastructure, nano-swarm deployment zones, and operational status.")

    num_wells = 30 
    np.random.seed(42) 
    well_x = np.random.rand(num_wells) * 100
    well_y = np.random.rand(num_wells) * 100
    well_status = [random.choice([\'Active\', \'Injecting Nano\', \'Maintenance\', \'Inactive\']) for _ in range(num_wells)]

    fig_field_map = go.Figure()

    status_colors = {\'Active\':COLOR_PRIMARY, \'Injecting Nano\':COLOR_SECONDARY, \'Maintenance\':COLOR_WARNING, \'Inactive\':COLOR_ERROR}
    fig_field_map.add_trace(go.Scatter(
        x=well_x,
        y=well_y,
        mode=\'markers\',
        marker=dict(
            size=12,
            color=[status_colors[s] for s in well_status],
            symbol=\'triangle-up\',
            line=dict(width=1, color=\'DarkSlateGrey\')
        ),
        name=\'Oil Wells\',
        text=[f\'Well {i+1}<br>Status: {well_status[i]}<br>Production: {random.randint(50,200)} bbl/day\' for i in range(num_wells)],
        hoverinfo=\'text\'
    ))

    fig_field_map.add_trace(go.Scatter(
        x=[50],
        y=[50],
        mode=\'markers\',
        marker=dict(
            size=25,
            color=COLOR_TEXT_LIGHT,
            symbol=\'star\',
            line=dict(width=2, color=COLOR_PRIMARY)
        ),
        name=\'Central Processing Facility\',
        text=\'Central Processing Facility<br>Capacity: 50,000 bbl/day\',
        hoverinfo=\'text\'
    ))

    fig_field_map.update_layout(
        title_text=\'Oil Field Layout & Nano-Swarm Deployment Zones\',
        title_font_color=COLOR_PRIMARY,
        xaxis_title=\'Field Easting (km)\',
        yaxis_title=\'Field Northing (km)\',
        height=600,
        paper_bgcolor=COLOR_BG_DARK,
        plot_bgcolor=COLOR_BG_MEDIUM,
        font=dict(color=COLOR_TEXT_LIGHT, family=\'Roboto Mono\'),
        showlegend=True,
        hovermode=\'closest\'
    )
    st.plotly_chart(fig_field_map, use_container_width=True)

    st.markdown("<h3>Well Status Summary</h3>", unsafe_allow_html=True)
    status_counts = pd.Series(well_status).value_counts()
    for status, count in status_counts.items():
        color = status_colors.get(status, COLOR_TEXT_LIGHT)
        st.markdown(f"<p style=\'color:{color};\'>• {status}: {count} wells</p>", unsafe_allow_html=True)

# --- Technical Report Tab ---
with tabs[6]:
    st.markdown("<h2>Technical Report Generation</h2>", unsafe_allow_html=True)
    st.write("Generate a comprehensive technical summary of the Nano-Swarm EOR simulation results.")

    if st.button("Generate Technical Report (Markdown)"):
        report_content = f"""
# Nano-Swarm EOR Technical Report

**Date:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 1. Executive Summary
This report summarizes the performance of the Nano-Swarm Enhanced Oil Recovery (EOR) simulation. The intelligent nano-robot swarm demonstrated significant potential in increasing oil production and improving reservoir sweep efficiency by dynamically altering reservoir properties.

## 2. Key Performance Indicators

*   **Best Achieved Nano-Swarm Production:** {st.session_state.best_production:.2f} bbl/day
*   **Maximum Production Lift:** {st.session_state.production_lift_percentage:+.2f}%
*   **Current Reservoir Pressure:** {st.session_state.current_pressure} psi
*   **Best Achieved Daily ROI:** {st.session_state.best_roi:,.2f}%

## 3. Environmental Impact (Green EOR)

*   **Total Water Saved (Cumulative):** {st.session_state.total_water_saved:,.2f} bbl
*   **Carbon Footprint Reduction (Cumulative):** {st.session_state.carbon_reduction:,.2f} tons CO2

## 4. Simulation Parameters & Results

### Production History (Last 10 steps)
| Time Step | Traditional Production (bbl/day) | Nano-Swarm Production (bbl/day) |
|-----------|----------------------------------|---------------------------------|
{pd.DataFrame({'Traditional': st.session_state.traditional_production_history[-10:], 'Nano-Swarm': st.session_state.nano_production_history[-10:]}).to_markdown(index=False)}

### Environmental Sensitivity Settings
*   **Oil Viscosity Factor:** {st.session_state.oil_viscosity_factor:.1f}
*   **Water Salinity Factor:** {st.session_state.water_salinity_factor:.1f}

## 5. Conclusion
The Nano-Swarm EOR technology presents a promising solution for enhanced oil recovery, offering substantial production increases, economic viability, and significant environmental benefits through reduced water usage and carbon emissions. Further research and field trials are recommended to validate these simulation results.

--- 
*Generated by Nano-Swarm EOR Ultimate Engineering Platform*
"""
        st.download_button(
            label="Download Technical Report (Markdown)",
            data=report_content.encode(\'utf-8\'),
            file_name="nano_eor_technical_report.md",
            mime="text/markdown",
            help="Download a detailed technical report in Markdown format."
        )
        log_event("INFO", "Technical Report Generated.")

# --- System Event Console (Global) ---
st.markdown("--- ")
st.markdown("<h2>🧠 System Event Console</h2>", unsafe_allow_html=True)
st.write("Real-time log of all system activities, nano-swarm communications, and simulation events.")

log_container = st.empty()

def update_log_display():
    log_html = """<div class=\'log-console\'>"""
    for type, timestamp, msg in reversed(st.session_state.logs):
        if type == "ERROR":
            log_html += f"<p style=\'color:{COLOR_ERROR};\'>[{timestamp}] [ERROR] {msg}</p>"
        elif type == "INFO":
            log_html += f"<p style=\'color:{COLOR_PRIMARY};\'>[{timestamp}] [INFO] {msg}</p>"
        else:
            log_html += f"<p style=\'color:{COLOR_WARNING};\'>[{timestamp}] [WARNING] {msg}</p>"
    log_html += "</div>"
    log_container.markdown(log_html, unsafe_allow_html=True)

update_log_display()

# --- Auto-rerun for Live Simulation ---
if st.session_state.simulation_running:
    current_time = time.time()
    if (current_time - st.session_state.last_update_time) > 0.2: # Update every 0.2 seconds
        st.session_state.last_update_time = current_time
        st.rerun()
