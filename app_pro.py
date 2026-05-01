import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import interp1d
import time, random, datetime
from scipy.ndimage import gaussian_filter
from math import exp

# --- Streamlit Page Configuration ---
st.set_page_config(layout="wide", page_title="Nano-Swarm EOR: Final Industry Version", page_icon="🚀")

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
COLOR_NANO_PROCESSING = "gold"
COLOR_PROCESSED_TRAIL = "rgba(0,255,204,0.2)"

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
        # Standardized file names for GitHub compatibility
        pvto_df = pd.read_excel("PVTO.xlsx")
        rel_perm_df = pd.read_excel("water-oil Relative permeability.xlsx")
        cap_press_df = pd.read_excel("capillary pressure.xlsx")
        pro_df = pd.read_excel("Pro.xlsx", skiprows=8)

        # Clean and prepare PVTO data
        pvto_df.columns = [col.strip().lower().replace(' ', '_') for col in pvto_df.columns]
        pvto_df = pvto_df.dropna(subset=['pressure', 'oil_viscosity']).sort_values('pressure')
        visc_interp = interp1d(pvto_df['pressure'], pvto_df['oil_viscosity'], fill_value="extrapolate", bounds_error=False)

        # Clean and prepare Relative Permeability data
        rel_perm_df.columns = [col.strip().lower() for col in rel_perm_df.columns]
        # Flexible column detection for Relative Permeability
        sw_col_rel = [c for c in rel_perm_df.columns if 'sw' in c][0]
        kro_col = [c for c in rel_perm_df.columns if 'kro' in c][0]
        krw_col = [c for c in rel_perm_df.columns if 'krw' in c][0]
        rel_perm_df = rel_perm_df.dropna(subset=[sw_col_rel, kro_col, krw_col]).sort_values(sw_col_rel)
        kro_interp = interp1d(rel_perm_df[sw_col_rel], rel_perm_df[kro_col], fill_value="extrapolate", bounds_error=False)
        krw_interp = interp1d(rel_perm_df[sw_col_rel], rel_perm_df[krw_col], fill_value="extrapolate", bounds_error=False)

        # Clean and prepare Capillary Pressure data
        cap_press_df.columns = [col.strip().lower() for col in cap_press_df.columns]
        # Flexible column detection for Capillary Pressure
        sw_col_pc = [c for c in cap_press_df.columns if 'sw' in c][0]
        pc_col = [c for c in cap_press_df.columns if 'pc' in c or 'pressure' in c][0]
        cap_press_df = cap_press_df.dropna(subset=[sw_col_pc, pc_col]).sort_values(sw_col_pc)
        pc_interp = interp1d(cap_press_df[sw_col_pc], cap_press_df[pc_col], fill_value="extrapolate", bounds_error=False)

        # Clean and prepare Production data
        pro_df.columns = pro_df.iloc[0].str.strip().str.lower()
        pro_df = pro_df[1:].reset_index(drop=True)
        
        # Flexible column detection for Production Data
        date_col = [c for c in pro_df.columns if 'day' in c or 'date' in c or 'time' in c][0]
        oil_col = [c for c in pro_df.columns if 'oil' in c][0]
        
        try:
            pro_df['date'] = pd.to_datetime(pro_df[date_col], format='%d %m %Y %H %M %S', errors='coerce')
        except:
            pro_df['date'] = pd.to_datetime(pro_df[date_col], errors='coerce')
            
        pro_df['oil'] = pd.to_numeric(pro_df[oil_col], errors='coerce')
        pro_df = pro_df.dropna(subset=['oil', 'date'])

        return visc_interp, kro_interp, krw_interp, pc_interp, pro_df
    except Exception as e:
        st.error(f"Critical Data Loading Error: Please ensure all Excel files (PVTO.xlsx, water-oil Relative permeability.xlsx, capillary pressure.xlsx, Pro.xlsx) are present in the same directory. Error: {e}")
        st.stop()

visc_interp, kro_interp, krw_interp, pc_interp, pro_data = load_data()

# --- Core Simulation Models ---
class Reservoir:
    def __init__(self, grid_size=25):
        self.grid_size = grid_size
        self.sw_grid = np.random.uniform(0.2, 0.4, (grid_size, grid_size)) # Initial water saturation
        self.perm_grid = np.random.uniform(50, 200, (grid_size, grid_size)) # Permeability
        
        # Introduce tight zones (low permeability areas)
        for _ in range(5):
            cx, cy = random.randint(0, grid_size-1), random.randint(0, grid_size-1)
            self.perm_grid[max(0, cx-3):min(grid_size, cx+3), max(0, cy-3):min(grid_size, cy+3)] = np.random.uniform(5, 30, (min(grid_size, cx+3)-max(0, cx-3), min(grid_size, cy+3)-max(0, cy-3)))
        self.perm_grid = gaussian_filter(self.perm_grid, sigma=1)
        
        self.nano_concentration_grid = np.zeros((grid_size, grid_size))
        self.processed_grid = np.zeros((grid_size, grid_size)) # To show processed areas
        self.nano_effect_radius = 2
        self.base_viscosity_reduction_factor = 0.005 
        self.base_kro_enhancement_factor = 0.002
        self.base_pc_reduction_factor = 0.05 # Nano effect on capillary pressure
        self.current_viscosity_modifier = 1.0
        self.current_salinity_modifier = 1.0
        self.current_pressure_modifier = 1.0

    def update_nano_effect(self, nano_particles):
        self.nano_concentration_grid = np.zeros((self.grid_size, self.grid_size))
        for n in nano_particles:
            if n.energy > 0: # Only active nano-robots contribute
                for i in range(max(0, n.x - self.nano_effect_radius), min(self.grid_size, n.x + self.nano_effect_radius + 1)):
                    for j in range(max(0, n.y - self.nano_effect_radius), min(self.grid_size, n.y + self.nano_effect_radius + 1)):
                        dist = np.sqrt((n.x - i)**2 + (n.y - j)**2)
                        if dist <= self.nano_effect_radius:
                            self.nano_concentration_grid[i, j] += (self.nano_effect_radius - dist) / self.nano_effect_radius
                            self.processed_grid[i, j] = 1 # Mark as processed
        self.nano_concentration_grid = gaussian_filter(self.nano_concentration_grid, sigma=1.5)
        self.nano_concentration_grid = np.clip(self.nano_concentration_grid, 0, 10)

    def calculate_production(self, pressure, nano_particles):
        self.update_nano_effect(nano_particles)
        avg_sw = np.clip(np.mean(self.sw_grid), 0.01, 0.99)
        
        # Oil Viscosity (mu_o) from PVTO data
        base_oil_viscosity = float(visc_interp(pressure)) * self.current_viscosity_modifier
        
        avg_nano_conc = np.mean(self.nano_concentration_grid)
        
        # Nano effect on oil viscosity
        effective_oil_viscosity = np.clip(base_oil_viscosity * (1 - avg_nano_conc * self.base_viscosity_reduction_factor), 0.05, base_oil_viscosity)
        
        # Relative Permeability (kro, krw) from data
        base_kro = kro_interp(avg_sw)
        base_krw = krw_interp(avg_sw)
        
        # Nano effect on kro (reducing Sor)
        effective_kro = np.clip(base_kro * (1 + avg_nano_conc * self.base_kro_enhancement_factor * self.current_salinity_modifier), 0.01, 0.99)
        
        # Capillary Pressure (Pc) from data
        base_capillary_pressure = float(pc_interp(avg_sw))
        
        # Nano effect on Pc (IFT reduction)
        effective_capillary_pressure = np.clip(base_capillary_pressure * (1 - avg_nano_conc * self.base_pc_reduction_factor), 0.01, base_capillary_pressure)
        
        avg_perm = np.mean(self.perm_grid)
        
        # Mobility Ratio (M) calculation
        # M = (k_rw / mu_w) / (k_ro / mu_o) -- assuming mu_w is constant for simplicity
        mu_w = 0.5 # cP, assumed water viscosity
        mobility_oil = effective_kro / effective_oil_viscosity
        mobility_water = base_krw / mu_w
        mobility_ratio = mobility_water / mobility_oil if mobility_oil > 0 else float('inf')

        # Production calculation (Darcy's Law approximation)
        production_rate = max(0, (effective_kro * avg_perm * (pressure - effective_capillary_pressure) / 1000) / (effective_oil_viscosity + 1e-6))
        
        return production_rate, mobility_ratio

class NanoRobot:
    def __init__(self, grid_size=25):
        self.grid_size = grid_size
        self.x = np.random.randint(0, grid_size)
        self.y = np.random.randint(0, grid_size)
        self.energy = 100
        self.signal_strength = random.randint(70, 100)
        self.wettability_index = 0.5 # Initial wettability
        self.is_processing_oil = False # New state for processing oil

    def move(self, reservoir, current_pressure, oil_viscosity_factor, water_salinity_factor, dx=0, dy=0, mode='auto'):
        # Energy cost based on reservoir conditions
        energy_cost = 0.1 + (oil_viscosity_factor - 1.0) * 0.5 + (water_salinity_factor - 1.0) * 0.3 + (3000 - current_pressure) / 1000 * 0.2
        self.energy = np.clip(self.energy - energy_cost, 0, 100)
        
        if self.energy <= 0: 
            self.is_processing_oil = False
            return # Robot is out of energy

        current_sw = reservoir.sw_grid[self.x, self.y]
        current_perm = reservoir.perm_grid[self.x, self.y]
        current_nano_conc = reservoir.nano_concentration_grid[self.x, self.y]

        if mode == 'manual':
            new_x = self.x + dx
            new_y = self.y + dy
        else: # Auto mode (Swarm Intelligence)
            # Move towards higher oil saturation (lower water saturation) and higher permeability
            gsx, gsy = np.gradient(reservoir.sw_grid) # Gradient of water saturation
            gpx, gpy = np.gradient(reservoir.perm_grid) # Gradient of permeability
            gnx, gny = np.gradient(reservoir.nano_concentration_grid) # Gradient of nano concentration

            # Prioritize moving away from high water saturation, towards high perm, and less crowded nano areas
            move_x = -gsx[self.x, self.y] * 0.5 + gpx[self.x, self.y] * 0.3 - gnx[self.x, self.y] * 0.2
            move_y = -gsy[self.x, self.y] * 0.5 + gpy[self.x, self.y] * 0.3 - gny[self.x, self.y] * 0.2
            
            # Add some random walk to avoid getting stuck
            move_x += random.uniform(-0.3, 0.3)
            move_y += random.uniform(-0.3, 0.3)
            
            speed = self.energy / 100.0 # Slower when energy is low
            new_x = self.x + move_x * speed
            new_y = self.y + move_y * speed

        self.x = int(np.clip(new_x, 0, self.grid_size - 1))
        self.y = int(np.clip(new_y, 0, self.grid_size - 1))
        
        # Update wettability based on nano concentration
        self.wettability_index = np.clip(0.5 + current_nano_conc * 0.05, 0.1, 0.9) # 0.1 (oil-wet) to 0.9 (water-wet)

        # Check if processing oil (e.g., if in an oil-rich zone and active)
        if current_sw < 0.5 and self.energy > 20: # If water saturation is low (oil-rich)
            self.is_processing_oil = True
        else:
            self.is_processing_oil = False

# --- Session State Initialization ---
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
    st.session_state.nano_mode = 'auto' # 'auto' or 'manual'
    st.session_state.total_water_saved = 0.0
    st.session_state.carbon_reduction = 0.0
    st.session_state.best_production = 0.0
    st.session_state.best_roi = 0.0
    st.session_state.last_update_time = time.time()
    st.session_state.injection_well_loc = (5, 5)
    st.session_state.production_well_loc = (20, 20)
    st.session_state.cash_flow_history = []
    st.session_state.npv_history = []
    st.session_state.initial_investment = 1000000 # Example initial investment
    st.session_state.discount_rate = 0.1 # 10% discount rate
    st.session_state.current_npv = -st.session_state.initial_investment
    st.session_state.total_net_profit = -st.session_state.initial_investment
    st.session_state.simulation_time_days = 0

res = st.session_state.res

def log_event(type, message):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append((type, timestamp, message))
    if len(st.session_state.logs) > 50: st.session_state.logs.pop(0)

# --- Dashboard ---
st.markdown("<h1>Nano-Swarm EOR: Final Industry Version</h1>", unsafe_allow_html=True)
tabs = st.tabs(["Dashboard", "Subsurface Digital Twin", "Mission Control", "AI Analytics & Sensitivity", "Economics & ROI", "Field Map", "Technical Report", "Project Guide / دليل المشروع"])

with tabs[0]:
    st.markdown("<h2>Operational Overview</h2>", unsafe_allow_html=True)
    st.session_state.current_pressure = st.slider("Reservoir Pressure (psi)", 500, 3000, st.session_state.current_pressure)
    
    # Calculate traditional production
    trad_prod_rate, _ = res.calculate_production(st.session_state.current_pressure, []) # No nano-swarm for traditional
    st.session_state.traditional_production_history.append(trad_prod_rate)

    # Calculate nano-swarm production
    nano_prod_rate, mobility_ratio = res.calculate_production(st.session_state.current_pressure, st.session_state.nano_swarm)
    st.session_state.nano_production_history.append(nano_prod_rate)

    if nano_prod_rate > st.session_state.best_production: st.session_state.best_production = nano_prod_rate
    lift = ((nano_prod_rate - trad_prod_rate) / trad_prod_rate * 100) if trad_prod_rate > 0 else 0
    
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='card'><h3>Traditional Production</h3><p>{trad_prod_rate:.2f} bbl/day</p></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='card'><h3>Nano-Swarm Production</h3><p>{nano_prod_rate:.2f} bbl/day</p></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='card'><h3>Production Lift</h3><p>{lift:+.2f}%</p></div>", unsafe_allow_html=True)
    
    fig = go.Figure(go.Indicator(mode="gauge+number+delta", value=nano_prod_rate, title={'text':"Total Production (bbl/day)", 'font':{'color':COLOR_TEXT_LIGHT}},
        delta={'reference': st.session_state.nano_production_history[-2] if len(st.session_state.nano_production_history) > 1 else trad_prod_rate},
        gauge={'axis':{'range':[0, max(1,nano_prod_rate*1.5)], 'tickcolor':COLOR_TEXT_LIGHT}, 'bar':{'color':COLOR_PRIMARY}, 'bgcolor':COLOR_BG_MEDIUM,
               'steps':[{'range':[0, trad_prod_rate], 'color':'#3a3a5a'}, {'range':[trad_prod_rate, max(1,nano_prod_rate*1.5)], 'color':'#00cc99'}],
               'threshold':{'line':{'color':COLOR_ERROR, 'width':4}, 'value': trad_prod_rate}}))
    fig.update_layout(height=300, paper_bgcolor=COLOR_BG_DARK, font={'color':COLOR_TEXT_LIGHT})
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown(f"<h3 style='color: {COLOR_SECONDARY};'>Mobility Ratio (M): {mobility_ratio:.2f}</h3>", unsafe_allow_html=True)
    if mobility_ratio < 1: log_event("SUCCESS", f"Mobility Ratio improved to {mobility_ratio:.2f}")
    else: log_event("WARNING", f"Mobility Ratio is {mobility_ratio:.2f} (sub-optimal)")

with tabs[1]:
    st.markdown("<h2>Subsurface Digital Twin</h2>", unsafe_allow_html=True)
    chart_placeholder = st.empty()
    if st.session_state.simulation_running:
        for n in st.session_state.nano_swarm: 
            n.move(res, st.session_state.current_pressure, st.session_state.oil_viscosity_factor, st.session_state.water_salinity_factor, st.session_state.manual_dx, st.session_state.manual_dy, st.session_state.nano_mode)
        res.update_nano_effect(st.session_state.nano_swarm)
        
        # Display grids
        display_sw = np.clip(res.sw_grid - (res.nano_concentration_grid * 0.02), 0.05, 0.95)
        display_perm = np.clip(res.perm_grid + (res.nano_concentration_grid * 5), 5, 250)
        
        # Nano-robot positions and colors based on energy/processing state
        xs=[n.x for n in st.session_state.nano_swarm]; ys=[n.y for n in st.session_state.nano_swarm]; zs=[display_sw[x,y] for x,y in zip(xs,ys)]
        colors = []
        for n in st.session_state.nano_swarm:
            if n.is_processing_oil: colors.append(COLOR_NANO_PROCESSING) # Gold when processing oil
            elif n.energy > 70: colors.append(COLOR_NANO_HEALTHY)
            elif n.energy > 30: colors.append(COLOR_NANO_STRESSED)
            else: colors.append(COLOR_NANO_CRITICAL)

        fig = go.Figure()
        
        # Processed trail (green neon)
        processed_x, processed_y = np.where(res.processed_grid == 1)
        if len(processed_x) > 0:
            fig.add_trace(go.Scatter3d(x=processed_x, y=processed_y, z=np.zeros_like(processed_x), mode='markers', 
                                       marker=dict(size=3, color=COLOR_PROCESSED_TRAIL, opacity=0.5), name='Processed Area'))

        fig.add_trace(go.Surface(z=display_sw, colorscale="Viridis", opacity=0.7, name='Water Saturation'))
        fig.add_trace(go.Surface(z=display_perm, colorscale="Hot", opacity=0.3, showscale=False, name='Permeability'))
        fig.add_trace(go.Scatter3d(x=xs, y=ys, z=zs, mode='markers', 
                                   marker=dict(size=5, color=colors, line=dict(width=1, color='black')), name='Nano-Robots'))
        
        st.markdown(f"<h3 style='color: {COLOR_PRIMARY};'>Avg Wettability Index: {np.mean([n.wettability_index for n in st.session_state.nano_swarm]):.2f}</h3>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='color: {COLOR_PRIMARY};'>Avg Nano-Robot Energy: {np.mean([n.energy for n in st.session_state.nano_swarm]):.1f}%</h3>", unsafe_allow_html=True)

        fig.update_layout(scene=dict(bgcolor=COLOR_BG_DARK, 
                                     xaxis_title='X-Coordinate', yaxis_title='Y-Coordinate', zaxis_title='Saturation/Permeability'), 
                          height=700, paper_bgcolor=COLOR_BG_DARK, font=dict(color=COLOR_TEXT_LIGHT))
        chart_placeholder.plotly_chart(fig, use_container_width=True)
        
        # Log events based on swarm state
        avg_energy = np.mean([n.energy for n in st.session_state.nano_swarm])
        if st.session_state.time_step % 25 == 0: 
            log_event("INFO", f"Swarm status: Avg Energy {avg_energy:.1f}%, Avg Wettability {np.mean([n.wettability_index for n in st.session_state.nano_swarm]):.2f}")
        if avg_energy < 30: log_event("WARNING", "Swarm energy critically low! Consider adjusting reservoir conditions.")
        if np.mean([n.is_processing_oil for n in st.session_state.nano_swarm]) > 0.5: log_event("SUCCESS", "Nano-swarm actively processing trapped oil.")

        st.session_state.time_step += 1
        st.session_state.simulation_time_days += 1 # Increment simulation days
        time.sleep(0.2)
        st.rerun()
    else:
        st.info("Simulation paused. Press 'ACTIVATE NANO-SWARM' to begin.")

with tabs[2]:
    st.markdown("<h2>Mission Control</h2>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    for col, title, val in zip([c1, c2, c3], ["Signal", "Avg Energy", "Latency"], [90, np.mean([n.energy for n in st.session_state.nano_swarm]), 20]):
        fig = go.Figure(go.Indicator(mode="gauge+number", value=val, title={'text':title, 'font':{'color':COLOR_TEXT_LIGHT}},
            gauge={'axis':{'range':[0,100], 'tickcolor':COLOR_TEXT_LIGHT}, 'bar':{'color':COLOR_PRIMARY}, 'bgcolor':COLOR_BG_MEDIUM}))
        fig.update_layout(height=200, paper_bgcolor=COLOR_BG_DARK, font={'color':COLOR_TEXT_LIGHT})
        col.plotly_chart(fig, use_container_width=True)
    
    st.markdown("<h3>Swarm Control Mode</h3>", unsafe_allow_html=True)
    st.session_state.nano_mode = st.radio("Select Nano-Swarm Control Mode:", ('auto', 'manual'), index=0 if st.session_state.nano_mode == 'auto' else 1, horizontal=True)

    if st.session_state.nano_mode == 'manual':
        st.markdown("<h3>Manual Swarm Navigation</h3>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c2:
            if st.button("⬆ Move Up"): st.session_state.manual_dx = -1; log_event("INFO", "Manual: Up")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("⬅ Move Left"): st.session_state.manual_dy = -1; log_event("INFO", "Manual: Left")
        with c3:
            if st.button("➡ Move Right"): st.session_state.manual_dy = 1; log_event("INFO", "Manual: Right")
        with c2:
            if st.button("⬇ Move Down"): st.session_state.manual_dx = 1; log_event("INFO", "Manual: Down")
        if st.button("Reset Manual Override"): st.session_state.manual_dx = 0; st.session_state.manual_dy = 0; log_event("INFO", "Manual override reset.")
    else:
        st.info("Nano-Swarm is in AUTO mode. Robots navigate autonomously based on reservoir conditions.")

    st.markdown("<h3>Simulation Control</h3>", unsafe_allow_html=True)
    col_start, col_stop = st.columns(2)
    with col_start:
        if st.button("▶ ACTIVATE NANO-SWARM"): 
            st.session_state.simulation_running = True
            log_event("SUCCESS", "Nano-Swarm Activated. Commencing EOR operations.")
    with col_stop:
        if st.button("🛑 EMERGENCY SHUTDOWN"): 
            st.session_state.simulation_running = False
            log_event("ERROR", "Emergency Shutdown initiated. Swarm operations halted.")

with tabs[3]:
    st.markdown(f"<div class='production-lift-display'>Nano Lift: {lift:+.2f}%</div>", unsafe_allow_html=True)
    st.markdown("<h2>AI Analytics & Sensitivity</h2>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    st.session_state.oil_viscosity_factor = c1.slider("Oil Viscosity Modifier", 0.5, 2.0, st.session_state.oil_viscosity_factor, help="Adjusts the base oil viscosity. Higher value means more viscous oil.")
    st.session_state.water_salinity_factor = c2.slider("Water Salinity Modifier", 0.5, 2.0, st.session_state.water_salinity_factor, help="Adjusts the impact of salinity on nano-swarm efficiency. Higher value means more challenging conditions.")
    res.current_viscosity_modifier = st.session_state.oil_viscosity_factor
    res.current_salinity_modifier = st.session_state.water_salinity_factor
    
    if len(st.session_state.nano_production_history) > 1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=st.session_state.nano_production_history, name="Nano-Swarm Production", line=dict(color=COLOR_PRIMARY, width=4)))
        fig.add_trace(go.Scatter(y=st.session_state.traditional_production_history, name="Traditional Production", line=dict(dash='dash', color=COLOR_TEXT_LIGHT)))
        
        # Predictive Forecast Zone
        if st.session_state.simulation_running and len(st.session_state.nano_production_history) > 10:
            # Simple linear extrapolation for forecast
            last_n_points = st.session_state.nano_production_history[-10:]
            x_vals = np.arange(len(last_n_points))
            y_vals = np.array(last_n_points)
            slope, intercept = np.polyfit(x_vals, y_vals, 1)
            
            forecast_length = 20 # Forecast for next 20 steps
            forecast_x = np.arange(len(st.session_state.nano_production_history), len(st.session_state.nano_production_history) + forecast_length)
            forecast_y = slope * np.arange(forecast_length) + intercept + y_vals[-1]
            
            # Confidence Band (simple +/- 5% of forecast)
            upper_band = forecast_y * 1.05
            lower_band = forecast_y * 0.95

            fig.add_trace(go.Scatter(x=forecast_x, y=forecast_y, mode='lines', name='Forecast', line=dict(color=COLOR_SECONDARY, dash='dot')))
            fig.add_trace(go.Scatter(x=forecast_x, y=upper_band, mode='lines', line=dict(width=0), showlegend=False))
            fig.add_trace(go.Scatter(x=forecast_x, y=lower_band, mode='lines', fill='tonexty', fillcolor='rgba(0,204,255,0.1)', line=dict(width=0), name='Confidence Band'))

        fig.update_layout(title='Production Trend & Forecast', height=400, template="plotly_dark", 
                          paper_bgcolor=COLOR_BG_DARK, plot_bgcolor=COLOR_BG_MEDIUM, font={'color':COLOR_TEXT_LIGHT},
                          xaxis_title='Simulation Time (Days)', yaxis_title='Oil Production (bbl/day)')
        st.plotly_chart(fig, use_container_width=True)
    
    # Sensitivity Analysis (Tornado Chart)
    st.markdown("<h3>Sensitivity Analysis (Impact on Production Lift)</h3>", unsafe_allow_html=True)
    # Example values for sensitivity, these would ideally come from a more complex model
    sensitivity_data = {
        "Factor": ["Reservoir Pressure", "Nano Conc. Effect", "Oil Viscosity", "Water Salinity", "Permeability"],
        "Impact": [0.8, 0.95, -0.7, -0.6, 0.85] # Positive impact for higher values, negative for lower
    }
    sens_df = pd.DataFrame(sensitivity_data).sort_values('Impact', ascending=True)

    fig_sens = go.Figure(go.Bar(x=sens_df['Impact'], y=sens_df['Factor'], orientation='h', marker_color=COLOR_PRIMARY))
    fig_sens.update_layout(height=300, paper_bgcolor=COLOR_BG_DARK, plot_bgcolor=COLOR_BG_MEDIUM, font={'color':COLOR_TEXT_LIGHT},
                           xaxis_title='Relative Impact', yaxis_title='Factor')
    st.plotly_chart(fig_sens, use_container_width=True)

with tabs[4]:
    st.markdown("<h2>Economics & Sustainability</h2>", unsafe_allow_html=True)
    oil_price = st.number_input("Oil Price ($/bbl)", 50, 150, 80, key='oil_price_input')
    opex_daily = st.number_input("Daily Operational Expenditure ($)", 1000, 50000, 5000, key='opex_daily_input')
    
    # Calculate daily revenue, net profit
    daily_revenue = nano_prod_rate * oil_price
    daily_net_profit = daily_revenue - opex_daily
    st.session_state.total_net_profit += daily_net_profit

    # Cash Flow calculation
    st.session_state.cash_flow_history.append(daily_net_profit)
    
    # NPV calculation
    # NPV = Sum (Cash Flow_t / (1 + r)^t) - Initial Investment
    cash_flows = np.array(st.session_state.cash_flow_history)
    time_periods = np.arange(1, len(cash_flows) + 1)
    discounted_cash_flows = cash_flows / (1 + st.session_state.discount_rate)**time_periods
    st.session_state.current_npv = np.sum(discounted_cash_flows) - st.session_state.initial_investment
    
    roi = (st.session_state.total_net_profit / st.session_state.initial_investment * 100) if st.session_state.initial_investment > 0 else 0
    if roi > st.session_state.best_roi: st.session_state.best_roi = roi
    
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='card'><h3>Daily Revenue</h3><p>${daily_revenue:,.2f}</p></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='card'><h3>Daily Net Profit</h3><p>${daily_net_profit:,.2f}</p></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='card'><h3>Total Net Profit</h3><p>${st.session_state.total_net_profit:,.2f}</p></div>", unsafe_allow_html=True)

    c4, c5, c6 = st.columns(3)
    c4.markdown(f"<div class='card'><h3>ROI</h3><p>{roi:,.2f}%</p></div>", unsafe_allow_html=True)
    c5.markdown(f"<div class='card'><h3>Current NPV</h3><p>${st.session_state.current_npv:,.2f}</p></div>", unsafe_allow_html=True)
    c6.markdown(f"<div class='card'><h3>Simulation Days</h3><p>{st.session_state.simulation_time_days}</p></div>", unsafe_allow_html=True)

    if lift > 0:
        st.session_state.total_water_saved += (nano_prod_rate - trad_prod_rate) * 0.5 * 0.01 # Example factor
        st.session_state.carbon_reduction += (nano_prod_rate - trad_prod_rate) * 0.05 * 0.01 # Example factor
    c1, c2 = st.columns(2)
    c1.markdown(f"<div class='card'><h3>Water Saved (bbl)</h3><p>{st.session_state.total_water_saved:,.2f}</p></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='card'><h3>CO2 Reduction (tons)</h3><p>{st.session_state.carbon_reduction:,.2f}</p></div>", unsafe_allow_html=True)

with tabs[5]:
    st.markdown("<h2>Field Operations Map</h2>", unsafe_allow_html=True)
    fig = go.Figure()
    
    # Permeability background
    fig.add_trace(go.Heatmap(z=res.perm_grid, colorscale="Greys", showscale=False, name='Permeability Background'))

    # Nano concentration overlay
    fig.add_trace(go.Heatmap(z=res.nano_concentration_grid, colorscale="Plasma", opacity=0.5, name='Nano Concentration'))

    # Injection Well
    fig.add_trace(go.Scatter(x=[st.session_state.injection_well_loc[0]], y=[st.session_state.injection_well_loc[1]], 
                             mode='markers', marker=dict(size=20, color=COLOR_SECONDARY, symbol='triangle-up', line=dict(width=2, color='white')), 
                             name="Injection Well", text=["Injection Well"], hoverinfo='text'))
    # Production Well
    fig.add_trace(go.Scatter(x=[st.session_state.production_well_loc[0]], y=[st.session_state.production_well_loc[1]], 
                             mode='markers', marker=dict(size=20, color=COLOR_PRIMARY, symbol='star', line=dict(width=2, color='white')), 
                             name="Production Well", text=["Production Well"], hoverinfo='text'))
    
    # Nano-swarm path (simple representation)
    if st.session_state.simulation_running:
        swarm_x = [n.x for n in st.session_state.nano_swarm if n.energy > 0]
        swarm_y = [n.y for n in st.session_state.nano_swarm if n.energy > 0]
        if len(swarm_x) > 0:
            fig.add_trace(go.Scatter(x=swarm_x, y=swarm_y, mode='markers', 
                                     marker=dict(size=8, color=COLOR_NANO_HEALTHY, symbol='circle', opacity=0.7), 
                                     name='Active Nano-Swarm'))

    fig.update_layout(height=600, paper_bgcolor=COLOR_BG_DARK, plot_bgcolor=COLOR_BG_MEDIUM, font={'color':COLOR_TEXT_LIGHT},
                      xaxis_title='Reservoir X-Coordinate', yaxis_title='Reservoir Y-Coordinate', 
                      title='Field Operations Map: Swarm Distribution & Well Locations')
    st.plotly_chart(fig, use_container_width=True)

with tabs[6]:
    st.markdown("<h2>Technical Report</h2>", unsafe_allow_html=True)
    if st.button("Generate Full Technical Report (PDF/Markdown)"):
        report_content = f"""
# Nano-Swarm EOR Final Industry Report

## Executive Summary
This report details the performance and economic viability of the Nano-Swarm Enhanced Oil Recovery (EOR) system. The simulation demonstrates significant improvements in oil production, economic returns, and environmental sustainability compared to traditional methods.

## Key Performance Indicators
- **Best Achieved Production (Nano-Swarm):** {st.session_state.best_production:.2f} bbl/day
- **Maximum Production Lift:** {lift:+.2f}%
- **Current Net Present Value (NPV):** ${st.session_state.current_npv:,.2f}
- **Return on Investment (ROI):** {roi:,.2f}%
- **Total Water Saved:** {st.session_state.total_water_saved:,.2f} bbl
- **Total CO2 Reduction:** {st.session_state.carbon_reduction:,.2f} tons
- **Average Nano-Robot Energy:** {np.mean([n.energy for n in st.session_state.nano_swarm]):.1f}%
- **Average Wettability Index:** {np.mean([n.wettability_index for n in st.session_state.nano_swarm]):.2f}
- **Current Mobility Ratio (M):** {mobility_ratio:.2f}

## Comparative Analysis: Traditional vs. Nano-Swarm EOR
| Metric                   | Traditional EOR       | Nano-Swarm EOR        | Improvement |
| :----------------------- | :-------------------- | :-------------------- | :---------- |
| **Oil Production (bbl/day)** | {trad_prod_rate:.2f}  | {nano_prod_rate:.2f}  | {lift:+.2f}% |
| **Oil Viscosity (cP)**   | {float(visc_interp(st.session_state.current_pressure)):.2f} | {float(visc_interp(st.session_state.current_pressure) * (1 - np.mean(res.nano_concentration_grid) * res.base_viscosity_reduction_factor)):.2f} | {((float(visc_interp(st.session_state.current_pressure) * (1 - np.mean(res.nano_concentration_grid) * res.base_viscosity_reduction_factor)) - float(visc_interp(st.session_state.current_pressure))) / float(visc_interp(st.session_state.current_pressure)) * 100):+.2f}% |
| **Capillary Pressure (psi)** | {float(pc_interp(np.mean(res.sw_grid))):.2f} | {float(pc_interp(np.mean(res.sw_grid)) * (1 - np.mean(res.nano_concentration_grid) * res.base_pc_reduction_factor)):.2f} | {((float(pc_interp(np.mean(res.sw_grid)) * (1 - np.mean(res.nano_concentration_grid) * res.base_pc_reduction_factor)) - float(pc_interp(np.mean(res.sw_grid)))) / float(pc_interp(np.mean(res.sw_grid))) * 100):+.2f}% |
| **Mobility Ratio (M)**   | N/A                   | {mobility_ratio:.2f}  | {("Improved" if mobility_ratio < 1 else "")}|

## Economic Projections
- **Initial Investment:** ${st.session_state.initial_investment:,.2f}
- **Daily Revenue (Nano-Swarm):** ${daily_revenue:,.2f}
- **Daily OPEX:** ${opex_daily:,.2f}
- **Total Net Profit (Accumulated):** ${st.session_state.total_net_profit:,.2f}

## Environmental Impact
- **Water Savings:** {st.session_state.total_water_saved:,.2f} bbl
- **CO2 Emission Reduction:** {st.session_state.carbon_reduction:,.2f} tons

## Conclusion
The Nano-Swarm EOR system presents a compelling case for next-generation oil recovery, offering superior production efficiency, robust economic returns, and significant environmental benefits.
"""
        st.download_button("Download Full Report (Markdown)", report_content, "nano_swarm_eor_report.md", mime="text/markdown")
        st.info("Report generated successfully. You can copy the content or download it as a Markdown file.")
        st.markdown(report_content)

with tabs[7]:
    st.markdown("<h2>Engineering User Guide / دليل المستخدم الهندسي</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class='guide-section'>
        <h3>1. Pre-Injection Baseline / مرحلة ما قبل الحقن</h3>
        <p><b>English:</b> Start by observing the <b>Traditional Production</b> in the Dashboard. Adjust the <b>Reservoir Pressure</b> slider to see how conventional recovery performs under different conditions. This establishes your baseline for comparison.</p>
        <p><b>العربية:</b> ابدأ بمراقبة <b>الإنتاج التقليدي</b> في لوحة التحكم. قم بتغيير <b>ضغط المكمن</b> لملاحظة أداء الاستخراج التقليدي في ظروف مختلفة، مما يضع مرجعاً أساسياً للمقارنة.</p>
    </div>
    
    <div class='guide-section'>
        <h3>2. Swarm Activation (Injection) / تفعيل السرب (لحظة الحقن)</h3>
        <p><b>English:</b> Navigate to <b>Mission Control</b> and press <b>ACTIVATE NANO-SWARM</b>. This simulates the physical injection of nano-robots into the reservoir. Watch the <b>Event Console</b> for real-time deployment logs.</p>
        <p><b>العربية:</b> انتقل إلى <b>Mission Control</b> واضغط على <b>ACTIVATE NANO-SWARM</b>. هذا يحاكي عملية حقن الروبوتات فعلياً في المكمن. راقب <b>كونسول الأحداث</b> لمتابعة سجلات الإطلاق اللحظية.</p>
    </div>
    
    <div class='guide-section'>
        <h3>3. Subsurface Monitoring / المراقبة تحت السطحية</h3>
        <p><b>English:</b> In the <b>Digital Twin</b> tab, observe the swarm's behavior. The movement reflects the search for <b>trapped oil</b>. Color changes (Cyan to Red) indicate energy consumption and the physical effort to <b>reduce viscosity</b> and alter <b>wettability</b>. Gold-colored robots are actively processing oil, and green trails show processed areas.</p>
        <p><b>العربية:</b> في تبويب <b>Digital Twin</b>، راقب سلوك السرب. تعكس الحركة عملية البحث عن <b>النفط المحبوس</b>، بينما تشير تغيرات الألوان (من السماوي للأحمر) إلى استهلاك الطاقة والجهد الفيزيائي لـ <b>تقليل اللزوجة</b> وتغيير <b>بللية الصخور</b>. الروبوتات ذات اللون الذهبي تعالج النفط بنشاط، والمسارات الخضراء تظهر المناطق المعالجة.</p>
    </div>
    
    <div class='guide-section'>
        <h3>4. Mechatronics Control / التحكم الميكاترونكسي</h3>
        <p><b>English:</b> Use the <b>Directional Buttons</b> in Mission Control to manually guide the swarm. This demonstrates the mechatronics core of the project, allowing engineers to steer the robots toward production wells or tight zones. You can switch between 'Auto' and 'Manual' modes.</p>
        <p><b>العربية:</b> استخدم <b>أزرار الاتجاهات</b> في Mission Control لتوجيه السرب يدوياً. هذا يبرز جوهر الميكاترونكس في المشروع، حيث يتيح للمهندس توجيه الروبوتات نحو آبار الإنتاج أو المناطق الصعبة. يمكنك التبديل بين وضعي 'تلقائي' و 'يدوي'.</p>
    </div>
    
    <div class='guide-section'>
        <h3>5. Economic & Environmental Impact / الأثر الاقتصادي والبيئي</h3>
        <p><b>English:</b> Finally, analyze the <b>Economics & ROI</b>. Observe how the <b>Nano Lift</b> translates into revenue, while simultaneously monitoring <b>Water Saving</b> and <b>Carbon Reduction</b>, achieving the project's ultimate goal of sustainable EOR. Track <b>NPV</b> and <b>Cash Flow</b> for financial viability.</p>
        <p><b>العربية:</b> أخيراً، قم بتحليل <b>الجانب الاقتصادي</b>. لاحظ كيف تترجم زيادة الإنتاج إلى أرباح، مع مراقبة <b>توفير المياه</b> و<b>تقليل الكربون</b>، لتحقيق الهدف النهائي للمشروع في الاستخراج المستدام. تتبع <b>صافي القيمة الحالية (NPV)</b> و<b>التدفق النقدي</b> للتحقق من الجدوى المالية.</p>
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
for type, timestamp, message in reversed(st.session_state.logs[-20:]):
    color = COLOR_PRIMARY if type == "INFO" else COLOR_WARNING if type == "WARNING" else COLOR_ERROR if type == "ERROR" else COLOR_PRIMARY
    log_html += f"<p style='color:{color};'>[{timestamp}] {message}</p>"
log_html += "</div>"
log_container.markdown(log_html, unsafe_allow_html=True)
