import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import interp1d
import time, random, datetime
from scipy.ndimage import gaussian_filter

# --- Streamlit Page Configuration ---
st.set_page_config(layout="wide", page_title="Nano-Swarm EOR Command Center", page_icon="🌌")

# --- Cinematic & Futuristic Styling ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Roboto+Mono:wght@300;400;700&display=swap');

    :root {
        --primary-color: #00ffcc; /* Neon Green */
        --secondary-color: #00ccff; /* Neon Blue */
        --background-dark: #0a0a1a;
        --background-medium: #1a1a3a;
        --text-light: #e0e0e0;
        --text-dark: #0a0a1a;
        --error-color: #ff4d4d;
        --warning-color: #ffd166;
    }

    body {
        background-color: var(--background-dark);
        color: var(--text-light);
        font-family: 'Roboto Mono', monospace;
        margin: 0;
        padding: 0;
    }

    .stApp {
        background-color: var(--background-dark);
        padding: 1rem;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Orbitron', sans-serif;
        color: var(--primary-color);
        text-shadow: 0 0 5px rgba(0,255,204,0.5);
    }

    /* Header Styling */
    .stMarkdown h1 {
        text-align: center;
        font-size: 3.5em;
        margin-bottom: 0.5em;
        background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 15px rgba(0,255,204,0.7), 0 0 25px rgba(0,204,255,0.5);
    }
    .stMarkdown p {
        text-align: center;
        color: var(--text-light);
        font-size: 1.1em;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        justify-content: center;
        margin-bottom: 20px;
    }
    .stTabs [data-baseweb="tab-list"] button {
        background-color: var(--background-medium);
        border-radius: 10px 10px 0 0;
        border: 1px solid var(--primary-color);
        color: var(--text-light);
        padding: 12px 25px;
        font-size: 1.1rem;
        font-weight: bold;
        transition: all 0.3s ease-in-out;
        box-shadow: 0 0 10px rgba(0,255,204,0.3);
    }
    .stTabs [data-baseweb="tab-list"] button:hover {
        background-color: var(--primary-color);
        color: var(--text-dark);
        box-shadow: 0 0 20px var(--primary-color);
        transform: translateY(-3px);
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: var(--primary-color);
        color: var(--text-dark);
        border-bottom: 3px solid var(--background-dark);
        box-shadow: 0 0 25px var(--primary-color);
    }

    /* Card Styling */
    .card {
        background: linear-gradient(145deg, rgba(0,255,204,0.15), rgba(0,100,200,0.15));
        border: 1px solid var(--primary-color);
        border-radius: 15px;
        padding: 25px;
        box-shadow: 0 0 30px rgba(0,255,204,0.4);
        text-align: center;
        margin-bottom: 20px;
        transition: all 0.4s ease-in-out;
        backdrop-filter: blur(5px); /* Glassmorphism effect */
    }
    .card:hover {
        transform: translateY(-7px) scale(1.02);
        box-shadow: 0 0 45px rgba(0,255,204,0.8);
        border-color: var(--secondary-color);
    }
    .card h3 {
        color: var(--primary-color);
        font-family: 'Orbitron', sans-serif;
        margin-bottom: 10px;
        font-size: 1.5em;
    }
    .card p {
        font-size: 2.5em;
        font-weight: bold;
        color: var(--text-light);
        margin-top: 5px;
    }

    /* Log Console Styling */
    .log-console {
        background-color: var(--background-medium);
        border: 1px solid var(--primary-color);
        border-radius: 10px;
        padding: 15px;
        max-height: 350px;
        overflow-y: auto;
        font-size: 0.9em;
        box-shadow: 0 0 20px rgba(0,255,204,0.3);
    }
    .log-green {color: var(--primary-color);}
    .log-red {color: var(--error-color);}
    .log-yellow {color: var(--warning-color);}

    /* Custom Production Lift Display */
    .production-lift-display {
        background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'Orbitron', sans-serif;
        font-size: 4.5em; /* Even larger text */
        font-weight: 700;
        text-align: center;
        text-shadow: 0 0 20px rgba(0,255,204,0.8), 0 0 30px rgba(0,204,255,0.6);
        margin-top: 30px;
        margin-bottom: 30px;
        animation: neon-glow 1.5s ease-in-out infinite alternate;
    }
    @keyframes neon-glow {
        from { text-shadow: 0 0 10px var(--primary-color), 0 0 20px var(--secondary-color); }
        to { text-shadow: 0 0 20px var(--primary-color), 0 0 30px var(--secondary-color), 0 0 40px var(--primary-color); }
    }

    /* Streamlit Widget Overrides */
    .stSlider > div > div > div[data-testid="stThumbValue"] {
        background-color: var(--primary-color);
        border: 1px solid var(--primary-color);
    }
    .stSlider > div > div > div[data-testid="stTrack"] > div {
        background-color: var(--primary-color);
    }
    .stButton > button {
        background-color: var(--background-medium);
        color: var(--primary-color);
        border: 1px solid var(--primary-color);
        border-radius: 8px;
        padding: 10px 20px;
        font-family: 'Orbitron', sans-serif;
        transition: all 0.3s ease-in-out;
        box-shadow: 0 0 10px rgba(0,255,204,0.3);
    }
    .stButton > button:hover {
        background-color: var(--primary-color);
        color: var(--text-dark);
        box-shadow: 0 0 20px var(--primary-color);
        transform: translateY(-2px);
    }
    .stNumberInput > div > div > input {
        background-color: var(--background-medium);
        color: var(--text-light);
        border: 1px solid var(--primary-color);
        border-radius: 8px;
    }
    .stMetric > div > div:first-child {
        color: var(--primary-color);
        font-family: 'Orbitron', sans-serif;
    }
    .stMetric > div > div:last-child > div:first-child {
        color: var(--text-light);
        font-size: 2.5em;
        font-weight: bold;
    }
    .stAlert {
        background-color: rgba(0,255,204,0.1);
        border-left: 5px solid var(--primary-color);
        color: var(--text-light);
    }
    .stProgress > div > div > div > div {
        background-color: var(--primary-color);
    }
    .stSelectbox > div > div > div {
        background-color: var(--background-medium);
        color: var(--text-light);
        border: 1px solid var(--primary-color);
        border-radius: 8px;
    }
    .stSelectbox > div > div > div > div[data-baseweb="select"] {
        background-color: var(--background-medium);
        color: var(--text-light);
    }
</style>
""", unsafe_allow_html=True)

# --- Data Loading and Interpolation ---
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
        # Initial permeability grid (simulated heterogeneity)
        self.perm_grid = np.random.uniform(50, 200, (grid_size, grid_size)) # mD
        
        self.nano_concentration_grid = np.zeros((grid_size, grid_size)) # Tracks nano concentration
        self.nano_effect_radius = 2 # Radius of influence for nano particles
        self.viscosity_reduction_factor = 0.005 # How much nano reduces viscosity locally per unit concentration
        self.kro_enhancement_factor = 0.002 # How much nano improves kro locally per unit concentration

    def update_nano_effect(self, nano_particles):
        # Reset nano concentration for current step
        self.nano_concentration_grid = np.zeros((self.grid_size, self.grid_size))
        for n in nano_particles:
            # Apply nano concentration in a small radius around each nano
            for i in range(max(0, n.x - self.nano_effect_radius), min(self.grid_size, n.x + self.nano_effect_radius + 1)):
                for j in range(max(0, n.y - self.nano_effect_radius), min(self.grid_size, n.y + self.nano_effect_radius + 1)):
                    dist = np.sqrt((n.x - i)**2 + (n.y - j)**2)
                    if dist <= self.nano_effect_radius:
                        self.nano_concentration_grid[i, j] += (self.nano_effect_radius - dist) / self.nano_effect_radius # Inverse distance weighting
        
        # Smooth the concentration grid to simulate diffusion
        self.nano_concentration_grid = gaussian_filter(self.nano_concentration_grid, sigma=1.5)
        self.nano_concentration_grid = np.clip(self.nano_concentration_grid, 0, 10) # Cap concentration

    def calculate_production(self, pressure, nano_particles):
        self.update_nano_effect(nano_particles)

        # Calculate effective oil viscosity and relative permeability across the grid
        # Nano-robots reduce oil viscosity and increase relative permeability to oil
        
        # Average Sw for interpolation (can be made more complex)
        avg_sw = np.mean(self.sw_grid)
        avg_sw = np.clip(avg_sw, 0.01, 0.99) # Ensure within interpolation bounds

        # Base oil viscosity at current pressure
        base_oil_viscosity = float(visc(pressure))
        
        # Nano-enhanced oil viscosity (average effect across the grid)
        # Higher nano concentration -> lower effective viscosity
        avg_nano_conc = np.mean(self.nano_concentration_grid)
        effective_oil_viscosity = np.clip(base_oil_viscosity * (1 - avg_nano_conc * self.viscosity_reduction_factor), 0.1, base_oil_viscosity) # Viscosity cannot be zero or negative

        # Base relative permeability to oil (kro) at average Sw
        base_kro = kro(avg_sw)
        
        # Nano-enhanced relative permeability to oil (average effect across the grid)
        # Higher nano concentration -> higher effective kro
        effective_kro = np.clip(base_kro * (1 + avg_nano_conc * self.kro_enhancement_factor), 0.01, 0.9) # kro cannot exceed 1

        # Capillary pressure at average Sw
        capillary_pressure = float(pc(avg_sw))

        # Production formula (Darcy's Law approximation for oil flow)
        # Q_oil = (k_eff * A * (P_res - P_well - P_cap)) / (mu_oil * B_oil)
        # Simplified for simulation: Production proportional to (kro * (P - Pc)) / mu_oil
        production_rate = (effective_kro * (pressure - capillary_pressure) / 1000) / (effective_oil_viscosity + 1e-6)
        return max(0, production_rate) # Production cannot be negative

class NanoRobot:
    def __init__(self, grid_size=25):
        self.grid_size = grid_size
        self.x = np.random.randint(0, grid_size)
        self.y = np.random.randint(0, grid_size)
        self.energy = 100 # For future features like battery life
        self.signal_strength = random.randint(70, 100) # Simulated signal

    def move(self, reservoir_sw_grid, nano_concentration_grid, dx=0, dy=0):
        # Swarm Intelligence: Move towards lower water saturation (higher oil) and avoid high nano concentration
        
        # Gradient of water saturation (move away from high Sw)
        gsx, gsy = np.gradient(reservoir_sw_grid)
        
        # Gradient of nano concentration (move away from other nanos to spread out)
        gnx, gny = np.gradient(nano_concentration_grid)

        # Combined movement vector
        move_factor_sw = 0.5 # Stronger pull towards oil
        move_factor_nano = 0.2 # Weaker repulsion from other nanos
        random_walk_strength = 0.3 # Some random exploration

        new_x = self.x - (gsx[self.x, self.y] * move_factor_sw) - (gnx[self.x, self.y] * move_factor_nano) + (random.uniform(-random_walk_strength, random_walk_strength))
        new_y = self.y - (gsy[self.x, self.y] * move_factor_sw) - (gny[self.x, self.y] * move_factor_nano) + (random.uniform(-random_walk_strength, random.uniform(-random_walk_strength, random_walk_strength)))

        self.x = int(np.clip(new_x, 0, self.grid_size - 1))
        self.y = int(np.clip(new_y, 0, self.grid_size - 1))

# --- Session State Management ---
if "res" not in st.session_state:
    st.session_state.res = Reservoir()
    st.session_state.nano_swarm = [NanoRobot() for _ in range(150)] # More nano-robots for richer swarm behavior
    st.session_state.logs = []
    st.session_state.simulation_running = False
    st.session_state.manual_dx = 0
    st.session_state.manual_dy = 0
    st.session_state.time_step = 0
    st.session_state.nano_production_history = []
    st.session_state.traditional_production_history = []
    st.session_state.current_pressure = 1500 # Default pressure
    st.session_state.production_lift_percentage = 0.0
    st.session_state.last_update_time = time.time()
    st.session_state.ai_prediction_message = "[AI] System initializing. Awaiting simulation start..."

res = st.session_state.res

# --- Utility Functions ---
def log_event(type, message):
    timestamp = datetime.datetime.now().strftime('%H:%M:%S')
    st.session_state.logs.append((type, timestamp, message))
    if len(st.session_state.logs) > 50: # Keep log clean
        st.session_state.logs.pop(0)

def get_traditional_production(pressure):
    # Simplified traditional production (no nano effect)
    avg_sw = np.mean(res.sw_grid)
    avg_sw = np.clip(avg_sw, 0.01, 0.99)
    base_oil_viscosity = float(visc(pressure))
    base_kro = kro(avg_sw)
    capillary_pressure = float(pc(avg_sw))
    traditional_prod = (base_kro * (pressure - capillary_pressure) / 1000) / (base_oil_viscosity + 1e-6)
    return max(0, traditional_prod)

# --- Main Application Layout ---
st.markdown("<h1>Nano-Swarm EOR Command Center</h1>", unsafe_allow_html=True)
st.markdown("<p>Intelligent Nano-Robot Swarm for Enhanced Oil Recovery - Digital Twin Simulation</p>", unsafe_allow_html=True)
st.markdown("--- ")

# --- Tabs Navigation ---
tabs = st.tabs(["Dashboard", "Subsurface Digital Twin", "Mission Control", "AI Analytics", "Economics & ROI", "Field Operations Map"])

# --- Dashboard Tab ---
with tabs[0]:
    st.markdown("<h2>Operational Overview</h2>", unsafe_allow_html=True)

    # Pressure Slider
    current_pressure_input = st.slider(
        "Simulated Reservoir Pressure (psi)", 
        500, 3000, st.session_state.current_pressure, 
        step=50, 
        help="Adjust the reservoir pressure to observe its impact on production."
    )
    if current_pressure_input != st.session_state.current_pressure:
        st.session_state.current_pressure = current_pressure_input
        log_event("INFO", f"Reservoir pressure adjusted to {st.session_state.current_pressure} psi.")

    # Calculate production values
    traditional_prod_val = get_traditional_production(st.session_state.current_pressure)
    nano_prod_val = res.calculate_production(st.session_state.current_pressure, st.session_state.nano_swarm)
    
    # Update history for live plots and metrics
    st.session_state.traditional_production_history.append(traditional_prod_val)
    st.session_state.nano_production_history.append(nano_prod_val)

    # Trim history to avoid excessive memory usage and keep plots responsive
    max_history_length = 200
    if len(st.session_state.traditional_production_history) > max_history_length:
        st.session_state.traditional_production_history.pop(0)
        st.session_state.nano_production_history.pop(0)

    # Production Lift Calculation
    if traditional_prod_val > 0:
        lift_percentage = ((nano_prod_val - traditional_prod_val) / traditional_prod_val) * 100
    else:
        lift_percentage = 0.0
    st.session_state.production_lift_percentage = lift_percentage

    # Display Production Cards
    col_prod1, col_prod2, col_prod3 = st.columns(3)
    with col_prod1:
        st.markdown(f"<div class=\'card\'><h3>Traditional Output</h3><p>{traditional_prod_val:.2f} bbl/day</p></div>", unsafe_allow_html=True)
    with col_prod2:
        st.markdown(f"<div class=\'card\'><h3>Nano-Swarm Output</h3><p>{nano_prod_val:.2f} bbl/day</p></div>", unsafe_allow_html=True)
    with col_prod3:
        st.markdown(f"<div class=\'card\'><h3>Production Lift</h3><p>{lift_percentage:+.2f}%</p></div>", unsafe_allow_html=True)

    st.markdown("<h3>Real-time Production Gauge</h3>", unsafe_allow_html=True)
    fig_gauge = go.Figure(go.Indicator(mode="gauge+number+delta", value=nano_prod_val,
        title={'text':"Total Production (bbl/day)", 'font': {'size': 20, 'color': var(--text-light)}},
        delta = {'reference': st.session_state.nano_production_history[-2] if len(st.session_state.nano_production_history) > 1 else traditional_prod_val, 'increasing':{'color':var(--primary-color)}, 'decreasing':{'color':var(--error-color)}},
        gauge={
            'axis':{'range':[0, max(1,nano_prod_val*1.5)], 'tickwidth':1, 'tickcolor':var(--text-light)},
            'bar':{'color':var(--primary-color)},
            'bgcolor':var(--background-medium),
            'borderwidth':2,
            'bordercolor':var(--primary-color),
            'steps':[
                {'range':[0, traditional_prod_val], 'color':'#3a3a5a'},
                {'range':[traditional_prod_val, max(1,nano_prod_val*1.5)], 'color':'#00cc99'}
            ],
            'threshold':{'line':{'color':var(--error-color), 'width':4}, 'thickness':0.75, 'value': traditional_prod_val}
        }
    ))
    fig_gauge.update_layout(height=300, margin=dict(l=10,r=10,t=50,b=10), font={'color': var(--text-light), 'family': 'Roboto Mono'})
    st.plotly_chart(fig_gauge, use_container_width=True)

    st.markdown("<h3>System Status</h3>", unsafe_allow_html=True)
    col_status1, col_status2 = st.columns(2)
    with col_status1:
        st.markdown(f"<div class=\'card\'><h3>System Time</h3><p>{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p></div>", unsafe_allow_html=True)
    with col_status2:
        st.markdown(f"<div class=\'card\'><h3>CPU Load</h3><p>{random.randint(10,80)}%</p></div>", unsafe_allow_html=True)

# --- Subsurface Digital Twin Tab ---
with tabs[1]:
    st.markdown("<h2>Subsurface Digital Twin: Nano-Swarm Dynamics</h2>", unsafe_allow_html=True)
    st.write("Observe the intelligent nano-robot swarm navigating the reservoir. Color intensity represents water saturation, with darker areas indicating higher oil potential. Nano-robots (cyan spheres) actively seek and enhance oil recovery zones.")

    chart_placeholder = st.empty()

    if st.session_state.simulation_running:
        # Update nano-robot positions based on swarm intelligence
        for nano in st.session_state.nano_swarm:
            nano.move(res.sw_grid, res.nano_concentration_grid, st.session_state.manual_dx, st.session_state.manual_dy)
        
        # Update reservoir properties based on nano-swarm concentration
        res.update_nano_effect(st.session_state.nano_swarm)
        
        # Visualization grid: show effective water saturation (lower = more oil)
        display_sw_grid = np.clip(res.sw_grid - (res.nano_concentration_grid * 0.02), 0.05, 0.95) # Nano reduces effective Sw

        xs=[n.x for n in st.session_state.nano_swarm]
        ys=[n.y for n in st.session_state.nano_swarm]
        zs=[display_sw_grid[x,y] for x,y in zip(xs,ys)] # Z-coordinate from the display grid

        fig_subsurface = go.Figure()
        fig_subsurface.add_trace(go.Surface(z=display_sw_grid, colorscale="Viridis", opacity=0.7, name="Water Saturation"))
        fig_subsurface.add_trace(go.Scatter3d(x=xs,y=ys,z=zs,
                                  mode='markers',
                                  marker=dict(size=5, color='cyan', opacity=0.9, symbol='circle'),
                                  name="Nano-Robots Swarm"))
        
        fig_subsurface.update_layout(
            scene=dict(
                xaxis_title='X-Coordinate',
                yaxis_title='Y-Coordinate',
                zaxis_title='Effective Water Saturation',
                bgcolor=var(--background-dark),
                aspectmode='cube',
                camera=dict(eye=dict(x=1.8, y=1.8, z=0.8)) # Cinematic camera angle
            ),
            title_text='Live Nano-Swarm Activity & Reservoir Impact',
            title_font_color=var(--primary-color),
            height=700,
            margin=dict(l=0, r=0, b=0, t=50),
            paper_bgcolor=var(--background-dark),
            plot_bgcolor=var(--background-dark),
            font=dict(color=var(--text-light), family='Roboto Mono')
        )
        chart_placeholder.plotly_chart(fig_subsurface, use_container_width=True)

        time.sleep(0.08) # Faster update for live feel
        st.session_state.time_step += 1
        st.rerun()
    else:
        st.info("Simulation is paused. Press 'START SIMULATION' in Mission Control to activate the nano-swarm and observe live subsurface dynamics.")
        # Display a static initial view of the subsurface
        fig_subsurface_static = go.Figure()
        fig_subsurface_static.add_trace(go.Surface(z=res.sw_grid, colorscale="Viridis", opacity=0.8, name="Initial Water Saturation"))
        fig_subsurface_static.update_layout(
            scene=dict(
                xaxis_title='X-Coordinate',
                yaxis_title='Y-Coordinate',
                zaxis_title='Initial Water Saturation',
                bgcolor=var(--background-dark),
                aspectmode='cube',
                camera=dict(eye=dict(x=1.8, y=1.8, z=0.8))
            ),
            title_text='Initial Reservoir State (Static View)',
            title_font_color=var(--primary-color),
            height=700,
            margin=dict(l=0, r=0, b=0, t=50),
            paper_bgcolor=var(--background-dark),
            plot_bgcolor=var(--background-dark),
            font=dict(color=var(--text-light), family='Roboto Mono')
        )
        chart_placeholder.plotly_chart(fig_subsurface_static, use_container_width=True)

# --- Mission Control Tab ---
with tabs[2]:
    st.markdown("<h2>Mission Control: Swarm & System Management</h2>", unsafe_allow_html=True)

    st.markdown("<h3>System Health & Telemetry</h3>", unsafe_allow_html=True)
    col_health1, col_health2, col_health3 = st.columns(3)

    # Health Monitor Gauges
    for col, title, val in zip(
        [col_health1, col_health2, col_health3],
        ["Swarm Signal Strength", "Average Nano Energy", "Network Latency"],
        [np.mean([n.signal_strength for n in st.session_state.nano_swarm]), np.mean([n.energy for n in st.session_state.nano_swarm]), random.randint(10, 100)]
    ):
        fig_health = go.Figure(go.Indicator(mode="gauge", value=val,
            title={'text':title, 'font': {'size': 16, 'color': var(--text-light)}},
            gauge={
                'axis':{'range':[0,100], 'tickwidth':1, 'tickcolor':var(--text-light)},
                'bar':{'color':var(--primary-color)},
                'bgcolor':var(--background-medium),
                'borderwidth':2,
                'bordercolor':var(--primary-color),
                'steps':[
                    {'range':[0, 30], 'color':var(--error-color)},
                    {'range':[30, 70], 'color':var(--warning-color)},
                    {'range':[70, 100], 'color':var(--primary-color)}
                ]
            }
        ))
        fig_health.update_layout(height=200, margin=dict(l=10,r=10,t=50,b=10), font={'color': var(--text-light), 'family': 'Roboto Mono'})
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

# --- AI Analytics Tab ---
with tabs[3]:
    st.markdown("<h2>AI-Powered Production Analytics</h2>", unsafe_allow_html=True)
    st.write("Real-time monitoring of production trends, AI-driven forecasts, and confidence intervals for Nano-Swarm EOR.")

    # Prominent Production Lift Display
    st.markdown(f"<div class=\'production-lift-display\'>Nano Lift: {st.session_state.production_lift_percentage:+.2f}%</div>", unsafe_allow_html=True)

    analytics_chart_placeholder = st.empty()

    # Live Plotting Logic
    if st.session_state.simulation_running or len(st.session_state.nano_production_history) > 1:
        y_nano = np.array(st.session_state.nano_production_history)
        y_traditional = np.array(st.session_state.traditional_production_history)
        x = np.arange(len(y_nano))

        # AI Prediction Logic (simple linear extrapolation for now, can be replaced with ML model)
        if len(y_nano) > 10:
            slope = (y_nano[-1] - y_nano[-10]) / 10 
        elif len(y_nano) > 1:
            slope = (y_nano[-1] - y_nano[-2])
        else:
            slope = 0

        future_steps = 20 # Predict further into the future
        future_prediction = [y_nano[-1] + slope * i for i in range(1, future_steps + 1)]

        fig_analytics = go.Figure()

        fig_analytics.add_trace(go.Scatter(x=x, y=y_nano, name="Nano-Swarm Enhanced Production",
                                         line=dict(color=var(--primary-color), width=4, shape='spline'),
                                         mode='lines+markers', marker=dict(size=5, symbol='circle')))
        fig_analytics.add_trace(go.Scatter(x=x, y=y_traditional, name="Traditional Production Baseline",
                                         line=dict(dash='dash', color=var(--text-light), width=2)))

        # Prediction + Confidence
        x_future = np.arange(len(y_nano), len(y_nano) + future_steps)
        confidence_factor = 0.18 # Increased confidence band for cinematic effect
        upper_bound=[f * (1 + confidence_factor) for f in future_prediction]
        lower_bound=[f * (1 - confidence_factor) for f in future_prediction]

        fig_analytics.add_trace(go.Scatter(x=x_future, y=future_prediction, name="AI Production Forecast",
                                         line=dict(color=var(--warning-color), width=3, dash='dot'),
                                         mode='lines', marker=dict(size=4, symbol='diamond')))
        fig_analytics.add_trace(go.Scatter(x=x_future, y=upper_bound, fill=None, mode='lines', line_color='rgba(255,209,102,0.3)', showlegend=False))
        fig_analytics.add_trace(go.Scatter(x=x_future, y=lower_bound, fill='tonexty', mode='lines', line_color='rgba(255,209,102,0.3)', fillcolor='rgba(255,209,102,0.1)', name="Forecast Confidence"))

        fig_analytics.update_layout(
            height=600, 
            template="plotly_dark",
            title_text='Production Trend & AI Forecast',
            title_font_color=var(--primary-color),
            xaxis_title='Simulation Time Step',
            yaxis_title='Production (bbl/day)',
            paper_bgcolor=var(--background-dark),
            plot_bgcolor=var(--background-medium),
            font=dict(color=var(--text-light), family='Roboto Mono'),
            hovermode='x unified'
        )
        analytics_chart_placeholder.plotly_chart(fig_analytics, use_container_width=True)

    st.markdown("<h3>AI System Insights</h3>", unsafe_allow_html=True)
    # Dynamic AI messages based on simulation state
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
    net_value = revenue - opex_cost # Simplified daily net value

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
    st.markdown("<h3>Financial Report Export</h3>", unsafe_allow_html=True)
    df_report = pd.DataFrame({"Metric":["Production (bbl/day)", "Oil Price ($/bbl)", "Daily Revenue ($)", "Daily OPEX ($)", "Daily Net Value ($)", "Daily ROI (%)"],
                              "Value":[current_nano_prod_econ, oil_price, revenue, opex_cost, net_value, roi_percentage]})
    st.download_button(
        label="Download Comprehensive Financial Report (CSV)",
        data=df_report.to_csv(index=False).encode('utf-8'),
        file_name="nano_eor_financial_report.csv",
        mime="text/csv",
        help="Export current financial metrics to a CSV file for detailed analysis."
    )

# --- Field Operations Map Tab ---
with tabs[5]:
    st.markdown("<h2>Field Operations Map</h2>", unsafe_allow_html=True)
    st.write("Geospatial overview of the oil field, displaying well infrastructure, nano-swarm deployment zones, and operational status.")

    num_wells = 30 # More wells for a richer map
    np.random.seed(42) # for reproducibility
    well_x = np.random.rand(num_wells) * 100
    well_y = np.random.rand(num_wells) * 100
    well_status = [random.choice(['Active', 'Injecting Nano', 'Maintenance', 'Inactive']) for _ in range(num_wells)]

    fig_field_map = go.Figure()

    # Add well locations with dynamic colors based on status
    status_colors = {'Active':var(--primary-color), 'Injecting Nano':var(--secondary-color), 'Maintenance':var(--warning-color), 'Inactive':var(--error-color)}
    fig_field_map.add_trace(go.Scatter(
        x=well_x,
        y=well_y,
        mode='markers',
        marker=dict(
            size=12,
            color=[status_colors[s] for s in well_status],
            symbol='triangle-up',
            line=dict(width=1, color='DarkSlateGrey')
        ),
        name='Oil Wells',
        text=[f'Well {i+1}<br>Status: {well_status[i]}<br>Production: {random.randint(50,200)} bbl/day' for i in range(num_wells)],
        hoverinfo='text'
    ))

    # Add a central processing facility
    fig_field_map.add_trace(go.Scatter(
        x=[50],
        y=[50],
        mode='markers',
        marker=dict(
            size=25,
            color=var(--text-light),
            symbol='star',
            line=dict(width=2, color=var(--primary-color))
        ),
        name='Central Processing Facility',
        text='Central Processing Facility<br>Capacity: 50,000 bbl/day',
        hoverinfo='text'
    ))

    fig_field_map.update_layout(
        title_text='Oil Field Layout & Nano-Swarm Deployment Zones',
        title_font_color=var(--primary-color),
        xaxis_title='Field Easting (km)',
        yaxis_title='Field Northing (km)',
        height=600,
        paper_bgcolor=var(--background-dark),
        plot_bgcolor=var(--background-medium),
        font=dict(color=var(--text-light), family='Roboto Mono'),
        showlegend=True,
        hovermode='closest'
    )
    st.plotly_chart(fig_field_map, use_container_width=True)

    st.markdown("<h3>Well Status Summary</h3>", unsafe_allow_html=True)
    status_counts = pd.Series(well_status).value_counts()
    for status, count in status_counts.items():
        color = status_colors.get(status, var(--text-light))
        st.markdown(f"<p style=\'color:{color};\'>• {status}: {count} wells</p>", unsafe_allow_html=True)

# --- System Event Console (Global) ---
st.markdown("--- ")
st.markdown("<h2>🧠 System Event Console</h2>", unsafe_allow_html=True)
st.write("Real-time log of all system activities, nano-swarm communications, and simulation events.")

log_container = st.empty()

def update_log_display():
    log_html = """<div class=\'log-console\'>"""
    for type, timestamp, msg in reversed(st.session_state.logs):
        if type == "ERROR":
            log_html += f"<p class=\'log-red\'>[{timestamp}] [ERROR] {msg}</p>"
        elif type == "INFO":
            log_html += f"<p class=\'log-green\'>[{timestamp}] [INFO] {msg}</p>"
        else:
            log_html += f"<p class=\'log-yellow\'>[{timestamp}] [WARNING] {msg}</p>"
    log_html += "</div>"
    log_container.markdown(log_html, unsafe_allow_html=True)

update_log_display()

# --- Auto-rerun for Live Simulation ---
if st.session_state.simulation_running:
    # Control update frequency
    current_time = time.time()
    if (current_time - st.session_state.last_update_time) > 0.1: # Update every 0.1 seconds
        st.session_state.last_update_time = current_time
        st.rerun()
