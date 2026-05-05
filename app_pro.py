import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import interp1d
import time, random, datetime
from scipy.ndimage import gaussian_filter
from math import exp, log
import base64
from io import BytesIO

# --- Streamlit Page Configuration ---
st.set_page_config(layout="wide", page_title="Nano-Swarm EOR: The Ultimate Masterpiece", page_icon="🚀")

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
COLOR_OIL_RICH = "#ffd700" # Gold for oil rich areas
COLOR_OIL_DEPLETED = "#4a4a4a" # Dark grey for depleted areas

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

    .stSidebar > div:first-child {{
        background-color: var(--background-medium);
        border-right: 1px solid var(--primary-color);
    }}

    .stSlider .st-bb .st-b0 {{
        background: var(--primary-color);
    }}

    .stSlider .st-bb .st-b0 > div > div {{
        background: var(--secondary-color);
    }}

    .stButton > button {{
        background-color: var(--primary-color);
        color: var(--background-dark);
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        font-family: 'Orbitron', sans-serif;
        font-weight: bold;
        transition: all 0.3s ease;
    }}

    .stButton > button:hover {{
        background-color: var(--secondary-color);
        color: var(--background-dark);
        box-shadow: 0 0 15px var(--secondary-color);
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

        # --- Flexible Column Detection Helper ---
        def find_col(df, keywords, default_idx, file_name):
            cols = [str(c).strip().lower() for c in df.columns]
            for kw in keywords:
                matches = [df.columns[i] for i, c in enumerate(cols) if kw in c]
                if matches: return matches[0]
            if default_idx < len(df.columns):
                return df.columns[default_idx]
            raise ValueError(f"Could not find suitable column in {file_name} for keywords {keywords}")

        # Clean and prepare Relative Permeability data
        rel_perm_df.columns = [str(col).strip().lower() for col in rel_perm_df.columns]
        sw_col_rel = find_col(rel_perm_df, ['sw'], 0, "Relative Permeability")
        kro_col = find_col(rel_perm_df, ['kro'], 1, "Relative Permeability")
        krw_col = find_col(rel_perm_df, ['krw'], 2, "Relative Permeability")
        rel_perm_df = rel_perm_df.dropna(subset=[sw_col_rel, kro_col, krw_col]).sort_values(sw_col_rel)
        kro_interp = interp1d(rel_perm_df[sw_col_rel], rel_perm_df[kro_col], fill_value="extrapolate", bounds_error=False)
        krw_interp = interp1d(rel_perm_df[sw_col_rel], rel_perm_df[krw_col], fill_value="extrapolate", bounds_error=False)

        # Clean and prepare Capillary Pressure data
        cap_press_df.columns = [str(col).strip().lower() for col in cap_press_df.columns]
        sw_col_pc = find_col(cap_press_df, ['sw'], 0, "Capillary Pressure")
        pc_col = find_col(cap_press_df, ['pc', 'pressure'], 1, "Capillary Pressure")
        cap_press_df = cap_press_df.dropna(subset=[sw_col_pc, pc_col]).sort_values(sw_col_pc)
        pc_interp = interp1d(cap_press_df[sw_col_pc], cap_press_df[pc_col], fill_value="extrapolate", bounds_error=False)

        # Clean and prepare Production data
        try:
            if not any(k in str(pro_df.columns).lower() for k in ['oil', 'day', 'date']):
                pro_df.columns = [str(c).strip().lower() for c in pro_df.iloc[0]]
                pro_df = pro_df[1:].reset_index(drop=True)
            
            date_col = find_col(pro_df, ['day', 'date', 'time'], 0, "Production Data")
            oil_col = find_col(pro_df, ['oil'], 1, "Production Data")
            
            pro_df['date'] = pd.to_datetime(pro_df[date_col], errors='coerce')
            pro_df['oil'] = pd.to_numeric(pro_df[oil_col], errors='coerce')
            pro_df = pro_df.dropna(subset=['oil', 'date'])
            
            if pro_df.empty: raise ValueError("Production data is empty after cleaning")
        except Exception as e:
            st.warning(f"Using fallback production data due to: {e}")
            pro_df = pd.DataFrame({
                'date': pd.date_range(start='2024-01-01', periods=100, freq='D'),
                'oil': np.random.uniform(100, 500, 100)
            })

        return visc_interp, kro_interp, krw_interp, pc_interp, pro_df
    except Exception as e:
        st.warning(f"System running in Fallback Mode (Data Loading Issue: {e}). Simulation remains functional with synthetic engineering data.")
        # Ultimate Fallback to ensure the app NEVER crashes
        visc_interp = lambda p: 2.5 - (p/3000)
        kro_interp = lambda sw: (1-sw)**2
        krw_interp = lambda sw: sw**2
        pc_interp = lambda sw: 10 * (1-sw)
        pro_df = pd.DataFrame({'date': pd.date_range(start='2024-01-01', periods=100, freq='D'), 'oil': np.random.uniform(100, 500, 100)})
        return visc_interp, kro_interp, krw_interp, pc_interp, pro_df

visc_interp, kro_interp, krw_interp, pc_interp, pro_data = load_data()

# --- Financial Models ---
# Placeholder for discount rate and project duration
DISCOUNT_RATE = 0.10  # 10% annual discount rate
PROJECT_DURATION_YEARS = 10 # Project duration for NPV/Cash Flow

def calculate_npv(cash_flows, discount_rate):
    npv = 0
    for i, cf in enumerate(cash_flows):
        npv += cf / ((1 + discount_rate)**i)
    return npv

def calculate_roi(initial_investment, total_return):
    if initial_investment == 0: return 0
    return (total_return - initial_investment) / initial_investment

def perform_sensitivity_analysis(base_params, param_variations):
    results = {}
    # Placeholder for sensitivity analysis logic
    # This function would simulate the impact of varying key parameters
    # on a chosen output metric (e.g., total oil recovery, NPV).
    # For now, it returns dummy data.
    for param, variations in param_variations.items():
        param_results = []
        for var in variations:
            # In a real scenario, you'd modify base_params with 'var'
            # and re-run a simplified simulation or financial calculation.
            # For demonstration, we'll use a simple linear impact.
            if param == 'nano_efficiency':
                impact = base_params['base_recovery'] * (1 + (var - 0.5) * 0.2) # Dummy impact
            elif param == 'discount_rate':
                impact = base_params['base_npv'] * (1 - (var - 0.1) * 5) # Dummy impact
            else:
                impact = base_params['base_recovery'] * (1 + (var - 1) * 0.1) # Generic dummy
            param_results.append(impact)
        results[param] = param_results
    return results

def calculate_cash_flow(oil_production_series, oil_price, capex, opex_per_bbl, nano_cost_per_unit, nano_injected_series):
    # Assuming oil_production_series and nano_injected_series are daily/monthly
    # Convert to annual for simplicity in this placeholder
    annual_production = oil_production_series.resample('Y').sum() if not oil_production_series.empty else pd.Series([0])
    annual_nano_cost = nano_injected_series.resample('Y').sum() * nano_cost_per_unit if not nano_injected_series.empty else pd.Series([0])

    cash_flows = []
    # Initial investment (CAPEX)
    cash_flows.append(-capex)

    for year_prod, year_nano_cost in zip(annual_production, annual_nano_cost):
        revenue = year_prod * oil_price
        opex = year_prod * opex_per_bbl + year_nano_cost
        net_cash_flow = revenue - opex
        cash_flows.append(net_cash_flow)
    
    # Pad with zeros if project duration is longer than simulation
    while len(cash_flows) < PROJECT_DURATION_YEARS + 1:
        cash_flows.append(0)

    return cash_flows[:PROJECT_DURATION_YEARS + 1]

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
        self.ift_reduction_factor = 0.0 # Initial IFT reduction factor

    def update_nano_effect(self, nano_particles):
        self.nano_concentration_grid = np.zeros((self.grid_size, self.grid_size))
        for n in nano_particles:
            if n.energy > 0: # Only active nano-robots contribute
                for i in range(max(0, n.x - self.nano_effect_radius), min(self.grid_size, n.x + self.nano_effect_radius + 1)):
                    for j in range(max(0, n.y - self.nano_effect_radius), min(self.grid_size, n.y + self.nano_effect_radius + 1)):
                        dist = np.sqrt((n.x - i)**2 + (n.y - j)**2)
                        if dist <= self.nano_effect_radius:
                            self.nano_concentration_grid[i, j] += 1
        
        # Apply nano effects to sw_grid (reduce water saturation where nano concentration is high)
        # This simulates nano displacing water or reducing residual water saturation
        self.sw_grid = np.maximum(0.15, self.sw_grid - self.nano_concentration_grid * 0.001)

    def get_local_properties(self, x, y, current_pressure):
        sw = self.sw_grid[x, y]
        perm = self.perm_grid[x, y]
        
        # Apply nano-enhanced properties
        nano_conc = self.nano_concentration_grid[x, y]
        
        # Viscosity reduction (more nano, less viscosity)
        oil_viscosity_base = visc_interp(current_pressure)
        oil_viscosity_nano_effect = oil_viscosity_base * (1 - nano_conc * self.base_viscosity_reduction_factor)
        oil_viscosity = max(0.1, oil_viscosity_nano_effect * self.current_viscosity_modifier)
        
        # Relative permeability enhancement (more nano, higher kro)
        kro_base = kro_interp(sw)
        kro_nano_effect = kro_base * (1 + nano_conc * self.base_kro_enhancement_factor)
        kro = min(0.9, kro_nano_effect)
        
        # Capillary pressure reduction (more nano, less pc)
        pc_base = pc_interp(sw)
        pc_nano_effect = pc_base * (1 - nano_conc * self.base_pc_reduction_factor)
        pc = max(0.1, pc_nano_effect)

        # Wettability Index (simplified: more nano, more oil-wet)
        wettability_index = max(-1.0, min(1.0, 0.5 - nano_conc * 0.01)) # -1 water-wet, 1 oil-wet
        
        # IFT Reduction (more nano, lower IFT)
        ift = 30 * (1 - nano_conc * self.ift_reduction_factor) # Base IFT 30 dynes/cm
        ift = max(0.1, ift)

        return sw, perm, oil_viscosity, kro, pc, wettability_index, ift

class NanoRobot:
    def __init__(self, x, y, energy=100):
        self.x = x
        self.y = y
        self.energy = energy
        self.color = COLOR_NANO_HEALTHY
        self.trail = []
        self.state = "exploring"

    def move(self, reservoir, target_x, target_y, current_pressure, salinity_modifier):
        if self.energy <= 0:
            self.color = COLOR_NANO_CRITICAL
            self.state = "inactive"



        self.trail.append((self.x, self.y))
        if len(self.trail) > 10: # Keep trail short
            self.trail.pop(0)

        # Energy consumption based on environment and movement
        energy_cost = 1 # Base cost
        _, perm, oil_viscosity, _, _, _, ift = reservoir.get_local_properties(self.x, self.y, current_pressure)
        
        # Higher salinity, higher viscosity, lower permeability -> more energy cost
        energy_cost += (salinity_modifier - 1.0) * 5 # Salinity effect
        energy_cost += (oil_viscosity / 10.0) # Viscosity effect
        energy_cost += (200 / perm) * 0.5 # Permeability effect
        energy_cost += (30 / ift) * 0.1 # IFT effect: lower IFT, less energy cost to move

        self.energy -= energy_cost
        self.energy = max(0, self.energy)

        if self.energy < 20:
            self.color = COLOR_NANO_CRITICAL
            self.state = "critical"
        elif self.energy < 50:
            self.color = COLOR_NANO_STRESSED
            self.state = "stressed"
        else:
            self.color = COLOR_NANO_HEALTHY
            self.state = "exploring"

        # Movement logic: move towards higher oil saturation (lower water saturation) and higher permeability
        best_move = (self.x, self.y)
        best_score = -np.inf

        possible_moves = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0: continue
                nx, ny = self.x + dx, self.y + dy
                if 0 <= nx < reservoir.grid_size and 0 <= ny < reservoir.grid_size:
                    possible_moves.append((nx, ny))
        
        # Add a bias towards the target (production well)
        if target_x is not None and target_y is not None:
            possible_moves.sort(key=lambda p: np.sqrt((p[0]-target_x)**2 + (p[1]-target_y)**2))

        for nx, ny in possible_moves:
            sw, perm, _, _, _, _, _ = reservoir.get_local_properties(nx, ny, current_pressure)
            
            # Score based on lower water saturation (more oil) and higher permeability
            score = (1 - sw) * 100 + (perm / 10)
            
            # Add cohesion: move towards other active nano-robots
            cohesion_score = 0
            for other_nano in st.session_state.nano_swarm:
                if other_nano != self and other_nano.energy > 0:
                    dist_to_other = np.sqrt((nx - other_nano.x)**2 + (ny - other_nano.y)**2)
                    if dist_to_other < 3: # Cohesion radius
                        cohesion_score += (3 - dist_to_other) * 5 # Stronger pull if closer
            score += cohesion_score

            if score > best_score:
                best_score = score
                best_move = (nx, ny)
        
        self.x, self.y = best_move

# --- Session State Initialization ---
if "res" not in st.session_state:
    st.session_state.res = Reservoir()
    st.session_state.nano_swarm = []
    st.session_state.simulation_running = False
    st.session_state.time_step = 0
    st.session_state.production_history = pd.DataFrame(columns=["Date", "Traditional_Oil", "Nano_Enhanced_Oil"])
    st.session_state.nano_injected_history = pd.DataFrame(columns=["Date", "Injected_Units"])
    st.session_state.log_messages = []
    st.session_state.current_pressure = 2500 # psi
    st.session_state.current_salinity = 1.0 # modifier
    st.session_state.nano_injection_rate = 5 # nano per step
    st.session_state.injection_well_pos = (st.session_state.res.grid_size // 2, 0)
    st.session_state.production_well_pos = (st.session_state.res.grid_size // 2, st.session_state.res.grid_size - 1)
    st.session_state.traditional_production_rate = pro_data["oil"].mean() # Base from Pro.xlsx
    st.session_state.nano_enhanced_production_rate = st.session_state.traditional_production_rate
    st.session_state.total_oil_produced_nano = 0
    st.session_state.total_oil_produced_traditional = 0
    st.session_state.total_nano_injected = 0
    st.session_state.nano_lift_percentage = 0.0
    st.session_state.current_date = pro_data["date"].min()
    st.session_state.total_nano_cost = 0 # For economic calculations
    st.session_state.water_saved_bbl = 0 # For environmental impact
    st.session_state.co2_reduced_tons = 0 # For environmental impact
    st.session_state.initial_reservoir_volume = st.session_state.res.grid_size * st.session_state.res.grid_size * 100 # Assume 100 ft thickness
    st.session_state.initial_oil_in_place = st.session_state.initial_reservoir_volume * (1 - np.mean(st.session_state.res.sw_grid)) * 0.2 # Assume 20% porosity
    st.session_state.recovery_factor_traditional = 0.0 # Placeholder
    st.session_state.recovery_factor_nano = 0.0 # Placeholder
    st.session_state.oil_price_per_bbl = 70
    st.session_state.nano_cost_per_unit = 0.1
    st.session_state.capex_traditional = 1000000
    st.session_state.opex_traditional_per_bbl = 5
    st.session_state.capex_nano = 1500000
    st.session_state.opex_nano_per_bbl = 4

# --- Logging Function ---
def log_event(message, level="info"):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    color = ""
    if level == "info": color = COLOR_TEXT_LIGHT
    elif level == "warning": color = COLOR_WARNING
    elif level == "error": color = COLOR_ERROR
    elif level == "success": color = COLOR_PRIMARY
    st.session_state.log_messages.append(f"<span style='color:{color};'>[{timestamp}] {message}</span>")
    if len(st.session_state.log_messages) > 50: # Keep log short
        st.session_state.log_messages.pop(0)

# --- Financial Model (Placeholder for now) ---
def calculate_economics(total_oil_nano, total_oil_produced_traditional, total_nano_injected):
    oil_price_per_bbl = st.session_state.oil_price_per_bbl
    nano_cost_per_unit = st.session_state.nano_cost_per_unit
    
    revenue_nano = total_oil_nano * oil_price_per_bbl
    revenue_traditional = total_oil_produced_traditional * oil_price_per_bbl
    
    cost_nano_injected = total_nano_injected * nano_cost_per_unit
    
    # CAPEX/OPEX from sidebar
    capex_traditional = st.session_state.capex_traditional
    opex_traditional = total_oil_produced_traditional * st.session_state.opex_traditional_per_bbl

    capex_nano = st.session_state.capex_nano
    opex_nano = total_oil_nano * st.session_state.opex_nano_per_bbl + cost_nano_injected

    # Discount rate for NPV (example: 10%)
    discount_rate = 0.10
    # For simplicity, assume all costs/revenues are at year 0 for NPV
    npv_nano = (revenue_nano - (capex_nano + opex_nano)) / (1 + discount_rate)**0
    npv_traditional = (revenue_traditional - (capex_traditional + opex_traditional)) / (1 + discount_rate)**0
    
    roi_nano = (npv_nano / (capex_nano + opex_nano)) * 100 if (capex_nano + opex_nano) > 0 else 0
    roi_traditional = (npv_traditional / (capex_traditional + opex_traditional)) * 100 if (capex_traditional + opex_traditional) > 0 else 0

    return npv_nano, roi_nano, npv_traditional, roi_traditional, revenue_nano, revenue_traditional, cost_nano_injected

# --- Production Forecasting (Placeholder for now) ---
def forecast_production(history_df, forecast_days=365):
    if history_df.empty or len(history_df) < 5:
        # Fallback for forecasting
        dates = pd.date_range(start=st.session_state.current_date, periods=forecast_days, freq='D')
        forecast_nano = np.linspace(st.session_state.nano_enhanced_production_rate, st.session_state.nano_enhanced_production_rate * 0.8, forecast_days)
        forecast_traditional = np.linspace(st.session_state.traditional_production_rate, st.session_state.traditional_production_rate * 0.7, forecast_days)
        return dates, forecast_nano, forecast_traditional

    # Simple exponential decline for forecasting
    last_date = history_df["Date"].max()
    last_nano_prod = history_df["Nano_Enhanced_Oil"].iloc[-1]
    last_trad_prod = history_df["Traditional_Oil"].iloc[-1]

    # Fit a simple decline curve (e.g., exponential)
    # This is a placeholder, a real model would be more complex
    decline_rate_nano = 0.001 # Example daily decline
    decline_rate_traditional = 0.002 # Example daily decline

    forecast_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=forecast_days, freq='D')
    forecast_nano = last_nano_prod * np.exp(-decline_rate_nano * np.arange(1, forecast_days + 1))
    forecast_traditional = last_trad_prod * np.exp(-decline_rate_traditional * np.arange(1, forecast_days + 1))

    return forecast_dates, forecast_nano, forecast_traditional

# --- Main Application Layout ---
st.title("\nNano-Swarm EOR: Ultimate Engineering & AI Platform")

# Sidebar for controls
with st.sidebar:
    st.header("\nSimulation Controls")
    st.markdown("--- ")

    st.session_state.current_pressure = st.slider("Reservoir Pressure (psi)", 1000, 5000, st.session_state.current_pressure, 100)
    st.session_state.current_salinity = st.slider("Formation Water Salinity (modifier)", 0.5, 2.0, st.session_state.current_salinity, 0.1)
    st.session_state.res.ift_reduction_factor = st.slider("Nano IFT Reduction Factor", 0.0, 0.1, st.session_state.res.ift_reduction_factor, 0.01)
    st.session_state.nano_injection_rate = st.slider("Nano-Robot Injection Rate (units/step)", 1, 50, st.session_state.nano_injection_rate, 1)
    st.session_state.res.base_viscosity_reduction_factor = st.slider("Nano Viscosity Reduction Efficacy", 0.001, 0.01, st.session_state.res.base_viscosity_reduction_factor, 0.001, format="%.3f")
    st.session_state.res.base_kro_enhancement_factor = st.slider("Nano Kro Enhancement Efficacy", 0.001, 0.01, st.session_state.res.base_kro_enhancement_factor, 0.001, format="%.3f")
    st.session_state.res.base_pc_reduction_factor = st.slider("Nano Capillary Pressure Reduction Efficacy", 0.01, 0.1, st.session_state.res.base_pc_reduction_factor, 0.01, format="%.2f")

    st.markdown("--- ")
    st.subheader("Economic Parameters")
    st.session_state.oil_price_per_bbl = st.slider("Oil Price ($/bbl)", 30, 120, st.session_state.oil_price_per_bbl, 5)
    st.session_state.nano_cost_per_unit = st.slider("Nano-Robot Cost ($/unit)", 0.01, 0.5, st.session_state.nano_cost_per_unit, 0.01, format="%.2f")
    st.session_state.capex_traditional = st.slider("Traditional CAPEX ($)", 500000, 2000000, st.session_state.capex_traditional, 100000)
    st.session_state.opex_traditional_per_bbl = st.slider("Traditional OPEX ($/bbl)", 1, 10, st.session_state.opex_traditional_per_bbl, 1)
    st.session_state.capex_nano = st.slider("Nano CAPEX ($)", 1000000, 3000000, st.session_state.capex_nano, 100000)
    st.session_state.opex_nano_per_bbl = st.slider("Nano OPEX ($/bbl)", 1, 10, st.session_state.opex_nano_per_bbl, 1)

    st.markdown("--- ")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("START SIMULATION", use_container_width=True):
            st.session_state.simulation_running = True
            log_event("Simulation Started", "success")
    with col2:
        if st.button("PAUSE SIMULATION", use_container_width=True):
            st.session_state.simulation_running = False
            log_event("Simulation Paused", "warning")
    
    if st.button("EMERGENCY STOP / RESET", use_container_width=True):
        st.session_state.res = Reservoir()
        st.session_state.nano_swarm = []
        st.session_state.simulation_running = False
        st.session_state.time_step = 0
        st.session_state.production_history = pd.DataFrame(columns=["Date", "Traditional_Oil", "Nano_Enhanced_Oil"])
        st.session_state.nano_injected_history = pd.DataFrame(columns=["Date", "Injected_Units"])
        st.session_state.log_messages = []
        st.session_state.current_pressure = 2500
        st.session_state.current_salinity = 1.0
        st.session_state.nano_injection_rate = 5
        st.session_state.oil_price_per_bbl = 70
        st.session_state.nano_cost_per_unit = 0.1
        st.session_state.capex_traditional = 1000000
        st.session_state.opex_traditional_per_bbl = 5
        st.session_state.capex_nano = 1500000
        st.session_state.opex_nano_per_bbl = 4
        st.session_state.traditional_production_rate = pro_data["oil"].mean()
        st.session_state.nano_enhanced_production_rate = st.session_state.traditional_production_rate
        st.session_state.total_nano_injected = 0
        st.session_state.total_oil_produced_nano = 0
        st.session_state.total_oil_produced_traditional = 0
        st.session_state.nano_lift_percentage = 0.0
        st.session_state.current_date = pro_data["date"].min()
        log_event("Simulation Reset", "error")

    st.markdown("--- ")
    st.subheader("Manual Nano-Swarm Control")
    col_up, col_center, col_down = st.columns([1,2,1])
    with col_center:
        if st.button("▲", key="up_arrow", use_container_width=True):
            st.session_state.production_well_pos = (max(0, st.session_state.production_well_pos[0]-1), st.session_state.production_well_pos[1])
            log_event(f"Production well moved to {st.session_state.production_well_pos}", "info")
    col_left, col_mid, col_right = st.columns(3)
    with col_left:
        if st.button("◀", key="left_arrow", use_container_width=True):
            st.session_state.production_well_pos = (st.session_state.production_well_pos[0], max(0, st.session_state.production_well_pos[1]-1))
            log_event(f"Production well moved to {st.session_state.production_well_pos}", "info")
    with col_mid:
        st.markdown("<h5 style='text-align:center; color:var(--secondary-color);'>MOVE WELL</h5>", unsafe_allow_html=True)
    with col_right:
        if st.button("▶", key="right_arrow", use_container_width=True):
            st.session_state.production_well_pos = (st.session_state.production_well_pos[0], min(st.session_state.res.grid_size-1, st.session_state.production_well_pos[1]+1))
            log_event(f"Production well moved to {st.session_state.production_well_pos}", "info")
    with col_center:
        if st.button("▼", key="down_arrow", use_container_width=True):
            st.session_state.production_well_pos = (min(st.session_state.res.grid_size-1, st.session_state.production_well_pos[0]+1), st.session_state.production_well_pos[1])
            log_event(f"Production well moved to {st.session_state.production_well_pos}", "info")

    st.markdown("--- ")
    st.subheader("Simulation Status")
    st.metric("Time Step", st.session_state.time_step)
    st.metric("Total Nano Injected", st.session_state.total_nano_injected)
    st.metric("Active Nano-Robots", len([n for n in st.session_state.nano_swarm if n.energy > 0]))

# Main tabs
tabs = st.tabs([
    "Dashboard", 
    "Subsurface Digital Twin", 
    "Predictive Recovery Analytics", 
    "Fiscal Yield Optimization", 
    "Geospatial Asset Surveillance", 
    "Operational Protocols",
    "Mission Control",
    "Project Guide / دليل المشروع"
])

with tabs[0]: # Dashboard
    st.header("\nOperational Dashboard")

with tabs[2]: # Predictive Recovery Analytics
    st.header("\nPredictive Recovery Analytics")
    st.markdown("""
    <div class="guide-section">
        <h3 style="color:var(--primary-color);">Predictive Recovery Analytics / تحليلات الاستخلاص التنبؤية</h3>
        <p>This section provides advanced forecasting models to predict future oil production, analyze decline curves, and quantify uncertainty. It helps in understanding the long-term impact of nano-swarm deployment.</p>
        <p>يقدم هذا القسم نماذج تنبؤ متقدمة للتنبؤ بإنتاج النفط المستقبلي، وتحليل منحنيات الانحدار، وتحديد عدم اليقين. يساعد في فهم التأثير طويل المدى لنشر سرب النانو.</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("\nProduction Forecasting / التنبؤ بالإنتاج")
    st.write("Here you can see the projected oil production with and without nano-EOR, along with confidence intervals.")
    # Placeholder for Production Forecast Plot
    st.info("Placeholder for Production Forecasting Plot (e.g., Exponential/Hyperbolic Decline Curve with Confidence Band)")

    st.subheader("\nSensitivity Analysis / تحليل الحساسية")
    st.write("This analysis shows how different reservoir parameters (pressure, salinity, viscosity) impact the overall oil recovery.")
    # Placeholder for Sensitivity Analysis Plot (Tornado/Spider Chart)
    st.info("Placeholder for Sensitivity Analysis Plot (e.g., Tornado or Spider Chart showing impact of parameters)")

    st.subheader("\nSmart Alerts & Recommendations / تنبيهات وتوصيات ذكية")
    st.write("Real-time alerts and AI-driven recommendations based on predictive models.")
    # Placeholder for Smart Alerts
    st.info("Placeholder for AI-driven alerts and recommendations.")

with tabs[3]: # Fiscal Yield Optimization
    st.header("\nFiscal Yield Optimization")
    st.markdown("""
    <div class="guide-section">
        <h3 style="color:var(--primary-color);">Fiscal Yield Optimization / تحسين العائد المالي</h3>
        <p>This section provides a comprehensive financial analysis of the nano-EOR project, including Net Present Value (NPV), Return on Investment (ROI), Cash Flow projections, Capital Expenditures (CAPEX), and Operational Expenditures (OPEX). It also includes sensitivity analysis to oil price fluctuations.</p>
        <p>يقدم هذا القسم تحليلاً مالياً شاملاً لمشروع الاستخلاص المعزز بالنانو، بما في ذلك صافي القيمة الحالية (NPV)، والعائد على الاستثمار (ROI)، وتوقعات التدفق النقدي، والنفقات الرأسمالية (CAPEX)، والنفقات التشغيلية (OPEX). كما يتضمن تحليل الحساسية لتقلبات أسعار النفط.</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("\nNet Present Value (NPV) & Return on Investment (ROI) / صافي القيمة الحالية والعائد على الاستثمار")
    st.write("Detailed calculations and visualizations for project profitability.")
    # Placeholder for NPV & ROI Metrics and Charts
    # Calculate financial metrics
    if not st.session_state.production_history.empty:
        # Ensure 'Date' column is datetime and set as index for resample
        production_df = st.session_state.production_history.copy()
        production_df['Date'] = pd.to_datetime(production_df['Date'])
        production_df = production_df.set_index('Date')

        # Get annual production for both traditional and nano-enhanced
        annual_prod_traditional = production_df['Traditional_Oil'].resample('Y').sum()
        annual_prod_nano = production_df['Nano_Enhanced_Oil'].resample('Y').sum()

        # Use tracked nano injection history
        if st.session_state.nano_injected_history.empty:
            nano_injected_series = pd.Series(0, index=production_df.index)
        else:
            nano_injected_history_df = st.session_state.nano_injected_history.copy()
            nano_injected_history_df['Date'] = pd.to_datetime(nano_injected_history_df['Date'])
            nano_injected_series = nano_injected_history_df.set_index('Date')['Injected_Units']

        # Calculate cash flows for nano-enhanced project
        cash_flows_nano = calculate_cash_flow(
            annual_prod_nano,
            st.session_state.oil_price_per_bbl,
            st.session_state.capex_nano,
            st.session_state.opex_nano_per_bbl,
            st.session_state.nano_cost_per_unit,
            nano_injected_series
        )

        # Calculate cash flows for traditional project (for comparison)
        cash_flows_traditional = calculate_cash_flow(
            annual_prod_traditional,
            st.session_state.oil_price_per_bbl,
            st.session_state.capex_traditional,
            st.session_state.opex_traditional_per_bbl,
            0, # No nano cost for traditional
            pd.Series() # No nano injected for traditional
        )

        npv_nano = calculate_npv(cash_flows_nano, DISCOUNT_RATE)
        npv_traditional = calculate_npv(cash_flows_traditional, DISCOUNT_RATE)

        total_return_nano = sum(cf for cf in cash_flows_nano if cf > 0)
        total_return_traditional = sum(cf for cf in cash_flows_traditional if cf > 0)

        roi_nano = calculate_roi(st.session_state.capex_nano, total_return_nano)
        roi_traditional = calculate_roi(st.session_state.capex_traditional, total_return_traditional)

        st.markdown(f"""
        <div class="card">
            <h4 style="color:var(--primary-color);">Net Present Value (NPV)</h4>
            <p style="font-size:1.5em;">Nano-EOR: <span style="color:{COLOR_PRIMARY};">${npv_nano:,.2f}</span></p>
            <p style="font-size:1.5em;">Traditional: <span style="color:{COLOR_SECONDARY};">${npv_traditional:,.2f}</span></p>
        </div>
        <div class="card">
            <h4 style="color:var(--primary-color);">Return on Investment (ROI)</h4>
            <p style="font-size:1.5em;">Nano-EOR: <span style="color:{COLOR_PRIMARY};">{roi_nano:.2%}</span></p>
            <p style="font-size:1.5em;">Traditional: <span style="color:{COLOR_SECONDARY};">{roi_traditional:.2%}</span></p>
        </div>
        """, unsafe_allow_html=True)

        # Cash Flow Chart
        st.subheader("\nCash Flow Projections / توقعات التدفق النقدي")
        st.write("Visualize the project's cash inflows and outflows over its lifetime.")
        
        fig_cf = go.Figure()
        fig_cf.add_trace(go.Bar(
            x=list(range(len(cash_flows_nano))),
            y=cash_flows_nano,
            name='Nano-EOR Cash Flow',
            marker_color=COLOR_PRIMARY
        ))
        fig_cf.add_trace(go.Bar(
            x=list(range(len(cash_flows_traditional))),
            y=cash_flows_traditional,
            name='Traditional Cash Flow',
            marker_color=COLOR_SECONDARY
        ))
        fig_cf.update_layout(
            title='Annual Cash Flow Comparison',
            xaxis_title='Year',
            yaxis_title='Cash Flow ($)',
            template='plotly_dark',
            hovermode='x unified',
            plot_bgcolor=COLOR_BG_MEDIUM,
            paper_bgcolor=COLOR_BG_DARK,
            font=dict(color=COLOR_TEXT_LIGHT),
            title_font_color=COLOR_PRIMARY
        )
        st.plotly_chart(fig_cf, use_container_width=True)

        # Cost Analysis (CAPEX & OPEX)
        st.subheader("\nCost Analysis (CAPEX & OPEX) / تحليل التكاليف (النفقات الرأسمالية والتشغيلية)")
        st.write("Breakdown of capital and operational expenditures for both traditional and nano-EOR methods.")

        fig_costs = go.Figure()
        fig_costs.add_trace(go.Bar(
            x=['CAPEX', 'OPEX (per bbl)'],
            y=[st.session_state.capex_nano, st.session_state.opex_nano_per_bbl],
            name='Nano-EOR Costs',
            marker_color=COLOR_PRIMARY
        ))
        fig_costs.add_trace(go.Bar(
            x=['CAPEX', 'OPEX (per bbl)'],
            y=[st.session_state.capex_traditional, st.session_state.opex_traditional_per_bbl],
            name='Traditional Costs',
            marker_color=COLOR_SECONDARY
        ))
        fig_costs.update_layout(
            title='CAPEX vs OPEX Comparison',
            yaxis_title='Amount ($)',
            template='plotly_dark',
            plot_bgcolor=COLOR_BG_MEDIUM,
            paper_bgcolor=COLOR_BG_DARK,
            font=dict(color=COLOR_TEXT_LIGHT),
            title_font_color=COLOR_PRIMARY
        )
        st.plotly_chart(fig_costs, use_container_width=True)

        # Oil Price Sensitivity
        st.subheader("\nOil Price Sensitivity / حساسية أسعار النفط")
        st.write("Assess the project's financial viability under different oil price scenarios.")

        price_scenarios = np.arange(st.session_state.oil_price_per_bbl * 0.7, st.session_state.oil_price_per_bbl * 1.3, 5)
        npv_sensitivity_nano = []
        npv_sensitivity_traditional = []

        for price in price_scenarios:
            cf_nano_sens = calculate_cash_flow(
                annual_prod_nano,
                price,
                st.session_state.capex_nano,
                st.session_state.opex_nano_per_bbl,
                st.session_state.nano_cost_per_unit,
                nano_injected_series
            )
            npv_sensitivity_nano.append(calculate_npv(cf_nano_sens, DISCOUNT_RATE))

            cf_traditional_sens = calculate_cash_flow(
                annual_prod_traditional,
                price,
                st.session_state.capex_traditional,
                st.session_state.opex_traditional_per_bbl,
                0,
                pd.Series()
            )
            npv_sensitivity_traditional.append(calculate_npv(cf_traditional_sens, DISCOUNT_RATE))

        fig_sens = go.Figure()
        fig_sens.add_trace(go.Scatter(
            x=price_scenarios,
            y=npv_sensitivity_nano,
            mode='lines+markers',
            name='Nano-EOR NPV',
            line=dict(color=COLOR_PRIMARY)
        ))
        fig_sens.add_trace(go.Scatter(
            x=price_scenarios,
            y=npv_sensitivity_traditional,
            mode='lines+markers',
            name='Traditional NPV',
            line=dict(color=COLOR_SECONDARY)
        ))
        fig_sens.update_layout(
            title='NPV Sensitivity to Oil Price',
            xaxis_title='Oil Price ($/bbl)',
            yaxis_title='NPV ($)',
            template='plotly_dark',
            plot_bgcolor=COLOR_BG_MEDIUM,
            paper_bgcolor=COLOR_BG_DARK,
            font=dict(color=COLOR_TEXT_LIGHT),
            title_font_color=COLOR_PRIMARY
        )
        st.plotly_chart(fig_sens, use_container_width=True)

    else:
        st.warning("Run the simulation first to generate financial data.")

    st.subheader("\nCash Flow Projections / توقعات التدفق النقدي")
    st.write("Visualize the project's cash inflows and outflows over its lifetime.")
    # Placeholder for Cash Flow Chart
    st.info("Placeholder for Cash Flow chart.")

    st.subheader("\nCost Analysis (CAPEX & OPEX) / تحليل التكاليف (النفقات الرأسمالية والتشغيلية)")
    st.write("Breakdown of capital and operational expenditures for both traditional and nano-EOR methods.")
    # Placeholder for CAPEX/OPEX comparison
    st.info("Placeholder for CAPEX and OPEX comparison charts.")

    st.subheader("\nOil Price Sensitivity / حساسية أسعار النفط")
    st.write("Assess the project's financial viability under different oil price scenarios.")
    # Placeholder for Oil Price Sensitivity Analysis
    st.info("Placeholder for Oil Price Sensitivity Analysis (e.g., Tornado chart for oil price impact).")

with tabs[4]: # Geospatial Asset Surveillance
    st.header("\nGeospatial Asset Surveillance / مراقبة الأصول الجغرافية المكانية")
    st.markdown("""
    <div class="guide-section">
        <h3 style="color:var(--primary-color);">Geospatial Asset Surveillance / مراقبة الأصول الجغرافية المكانية</h3>
        <p>This section provides a comprehensive geospatial view of the reservoir, including well locations, nano-swarm distribution, and real-time operational data overlaid on a 2D/3D map. It allows for precise monitoring and strategic deployment of the nano-swarm.</p>
        <p>يقدم هذا القسم عرضاً جغرافياً مكانياً شاملاً للمكمن، بما في ذلك مواقع الآبار، وتوزيع سرب النانو، وبيانات التشغيل في الوقت الفعلي المعروضة على خريطة ثنائية/ثلاثية الأبعاد. يسمح ذلك بالمراقبة الدقيقة والنشر الاستراتيجي لسرب النانو.</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("\nReservoir Map & Well Locations / خريطة المكمن ومواقع الآبار")
    st.write("Visualize the reservoir layout, injection wells, and production wells.")
    # Placeholder for 2D/3D Reservoir Map
    st.info("Placeholder for 2D/3D interactive map showing reservoir, wells, and nano-swarm distribution.")

    st.subheader("\nNano-Swarm Distribution & Movement / توزيع وحركة سرب النانو")
    st.write("Track the real-time movement and concentration of the nano-swarm within the reservoir.")
    # Placeholder for Nano-Swarm Heatmap/Density Map
    st.info("Placeholder for heatmap or density map showing nano-swarm concentration.")

    st.subheader("\nReal-time Sensor Data Overlay / تراكب بيانات الحساسات في الوقت الفعلي")
    st.write("Overlay critical sensor data (pressure, temperature, saturation) on the geospatial map.")
    # Placeholder for Sensor Data Overlay
    st.info("Placeholder for real-time sensor data visualization on the map.")

with tabs[5]: # Operational Protocols
    st.header("\nOperational Protocols / بروتوكولات التشغيل")
    st.markdown("""
    <div class="guide-section">
        <h3 style="color:var(--primary-color);">Operational Protocols / بروتوكولات التشغيل</h3>
        <p>This section details the standard operating procedures (SOPs) for nano-swarm deployment, safety protocols, and real-time alert management. It ensures efficient and secure field operations.</p>
        <p>يفصل هذا القسم إجراءات التشغيل القياسية (SOPs) لنشر سرب النانو، وبروتوكولات السلامة، وإدارة التنبيهات في الوقت الفعلي. يضمن عمليات حقلية فعالة وآمنة.</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("\nStandard Operating Procedures (SOPs) / إجراءات التشغيل القياسية")
    st.write("Guidelines for effective and safe nano-swarm injection and management.")
    # Placeholder for SOPs
    st.info("Placeholder for detailed SOPs for nano-swarm deployment.")

    st.subheader("\nSafety & Environmental Protocols / بروتوكولات السلامة والبيئة")
    st.write("Ensuring compliance with safety regulations and minimizing environmental impact.")
    # Placeholder for Safety Protocols
    st.info("Placeholder for safety and environmental guidelines.")

    st.subheader("\nReal-time Alert Management / إدارة التنبيهات في الوقت الفعلي")
    st.write("System for handling critical alerts and notifications from the nano-swarm and reservoir sensors.")
    # Placeholder for Alert Management Interface
    st.info("Placeholder for real-time alert dashboard and management tools.")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="card">
            <h3>Current Pressure</h3>
            <h2 style="color:{COLOR_SECONDARY};">{st.session_state.current_pressure} psi</h2>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="card">
            <h3>Current Salinity</h3>
            <h2 style="color:{COLOR_SECONDARY};">{st.session_state.current_salinity:.1f} modifier</h2>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="card">
            <h3>Active Nano-Robots</h3>
            <h2 style="color:{COLOR_SECONDARY};">{len([n for n in st.session_state.nano_swarm if n.energy > 0])}</h2>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_prod_lift, col_prod_rates = st.columns([1, 2])
    with col_prod_lift:
        st.markdown(f"""
        <div class="production-lift-display">
            Nano Lift: {st.session_state.nano_lift_percentage:.2f}%
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="card" style="margin-top: 20px;">
            <h3>Total Oil Produced (Nano)</h3>
            <h2 style="color:{COLOR_PRIMARY};">{st.session_state.total_oil_produced_nano:,.0f} bbl</h2>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="card" style="margin-top: 20px;">
            <h3>Total Oil Produced (Traditional)</h3>
            <h2 style="color:{COLOR_SECONDARY};">{st.session_state.total_oil_produced_traditional:,.0f} bbl</h2>
        </div>
        """, unsafe_allow_html=True)

    with col_prod_rates:
        st.subheader("\nProduction Rates Over Time")
        if not st.session_state.production_history.empty:
            fig_prod = go.Figure()
            fig_prod.add_trace(go.Scatter(
                x=st.session_state.production_history["Date"],
                y=st.session_state.production_history["Traditional_Oil"],
                mode='lines', name='Traditional Production', line=dict(color=COLOR_SECONDARY, width=2)
            ))
            fig_prod.add_trace(go.Scatter(
                x=st.session_state.production_history["Date"],
                y=st.session_state.production_history["Nano_Enhanced_Oil"],
                mode='lines', name='Nano-Enhanced Production', line=dict(color=COLOR_PRIMARY, width=3)
            ))
            fig_prod.update_layout(
                title={'text':"Total Production (bbl/day)", 'x':0.5, 'xanchor':'center'}, 
                xaxis_title='Date', yaxis_title='Oil Production (bbl/day)',
                plot_bgcolor=COLOR_BG_MEDIUM, paper_bgcolor=COLOR_BG_DARK,
                font=dict(color=COLOR_TEXT_LIGHT, family='Roboto Mono'),
                hovermode='x unified'
            )
            st.plotly_chart(fig_prod, use_container_width=True)
        else:
            st.info("Start simulation to see production data.")

    st.markdown("--- ")
    st.subheader("\nEvent Console")
    log_placeholder = st.empty()
    with log_placeholder.container():
        st.markdown(f"<div class='log-console'>{'<br>'.join(st.session_state.log_messages[::-1])}</div>", unsafe_allow_html=True)

with tabs[1]: # Subsurface Digital Twin
    st.header("\nSubsurface Digital Twin: Nano-Swarm Dynamics")
    st.markdown("Visualizing the intelligent nano-swarm interacting with the reservoir.")

    col_twin_map, col_twin_stats = st.columns([3, 1])

    with col_twin_map:
        # 3D visualization of reservoir and nano-robots
        fig_3d = go.Figure()

        # Reservoir grid (Permeability heatmap)
        x_coords, y_coords = np.meshgrid(np.arange(st.session_state.res.grid_size), np.arange(st.session_state.res.grid_size))
        
        # Oil Saturation Heatmap (using go.Surface for 2D representation on a plane)
        oil_saturation_heatmap = 1 - st.session_state.res.sw_grid # Assuming sw_grid is water saturation
        fig_3d.add_trace(go.Surface(
            x=x_coords, y=y_coords, z=np.zeros_like(x_coords), # Render on a flat plane at z=0
            surfacecolor=oil_saturation_heatmap,
            colorscale='Hot', # Hot colors for oil saturation
            cmin=0.0, cmax=1.0,
            opacity=0.6, showscale=True,
            colorbar=dict(title='Oil Saturation', titleside='right'),
            name='Oil Saturation'
        ))

        # Permeability heatmap
        fig_3d.add_trace(go.Surface(
            x=x_coords, y=y_coords, z=st.session_state.res.perm_grid,
            colorscale='Viridis', opacity=0.7, showscale=False,
            name='Permeability'
        ))

        # Nano-robots
        nano_x = [n.x for n in st.session_state.nano_swarm if n.energy > 0]
        nano_y = [n.y for n in st.session_state.nano_swarm if n.energy > 0]
        nano_z = [st.session_state.res.perm_grid[n.x, n.y] + 5 for n in st.session_state.nano_swarm if n.energy > 0] # Slightly above surface
        nano_colors = [n.color for n in st.session_state.nano_swarm if n.energy > 0]

        if nano_x:
            fig_3d.add_trace(go.Scatter3d(
                x=nano_x, y=nano_y, z=nano_z,
                mode='markers', 
                marker=dict(size=5, color=nano_colors, opacity=0.8),
                name='Nano-Robots'
            ))

        # Nano-robot trails
        for nano in st.session_state.nano_swarm:
            if len(nano.path) > 1:
                path_x = [p[0] for p in nano.path]
                path_y = [p[1] for p in nano.path]
                path_z = [st.session_state.res.perm_grid[p[0], p[1]] + 2 for p in nano.path] # Slightly above surface
                fig_3d.add_trace(go.Scatter3d(
                    x=path_x, y=path_y, z=path_z,
                    mode='lines',
                    line=dict(color=nano.color, width=1),
                    name=f'Nano Trail {nano.id}'
                ))



        
        # Production Well
        prod_x, prod_y = st.session_state.production_well_pos
        fig_3d.add_trace(go.Scatter3d(
            x=[prod_x], y=[prod_y], z=[st.session_state.res.perm_grid[prod_x, prod_y] + 10],
            mode='markers', 
            marker=dict(size=10, color='red', symbol='diamond', opacity=1.0),
            name='Production Well'
        ))

        # Injection Well
        inj_x, inj_y = st.session_state.injection_well_pos
        fig_3d.add_trace(go.Scatter3d(
            x=[inj_x], y=[inj_y], z=[st.session_state.res.perm_grid[inj_x, inj_y] + 10],
            mode='markers', 
            marker=dict(size=10, color='blue', symbol='circle', opacity=1.0),
            name='Injection Well'
        ))

        fig_3d.update_layout(
            scene=dict(
                xaxis_title='X-Coordinate', yaxis_title='Y-Coordinate', zaxis_title='Permeability',
                bgcolor=COLOR_BG_DARK,
                aspectmode='cube'
            ),
            title={'text':"3D Reservoir & Nano-Swarm Visualization", 'x':0.5, 'xanchor':'center'}, 
            paper_bgcolor=COLOR_BG_DARK, font=dict(color=COLOR_TEXT_LIGHT, family='Roboto Mono'),
            height=700
        )
        st.plotly_chart(fig_3d, use_container_width=True)

    with col_twin_stats:
        st.subheader("\nNano-Swarm Health & Metrics")
        st.markdown(f"""
        <div class="card">
            <h3>Average Nano Energy</h3>
            <h2 style="color:{COLOR_PRIMARY};">{np.mean([n.energy for n in st.session_state.nano_swarm]) if st.session_state.nano_swarm else 0:.1f}</h2>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="card">
            <h3>Average Wettability Index</h3>
            <h2 style="color:{COLOR_PRIMARY};">{np.mean([st.session_state.res.get_local_properties(n.x, n.y, st.session_state.current_pressure)[5] for n in st.session_state.nano_swarm]) if st.session_state.nano_swarm else 0:.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="card">
            <h3>IFT Reduction Factor</h3>
            <h2 style="color:{COLOR_PRIMARY};">{st.session_state.res.ift_reduction_factor:.2f}</h2>
        </div>
        """, unsafe_allow_html=True)

with tabs[2]: # AI Analytics & Forecasting
    st.header("\nAI Analytics & Production Forecasting")
    st.markdown("Advanced AI models for production prediction and sensitivity analysis.")

    col_analytics_prod, col_analytics_forecast = st.columns(2)

    with col_analytics_prod:
        st.subheader("\nProduction History & Nano-Lift")
        if not st.session_state.production_history.empty:
            fig_analytics_prod = go.Figure()
            fig_analytics_prod.add_trace(go.Scatter(
                x=st.session_state.production_history["Date"],
                y=st.session_state.production_history["Traditional_Oil"],
                mode='lines', name='Traditional Production', line=dict(color=COLOR_SECONDARY, width=2)
            ))
            fig_analytics_prod.add_trace(go.Scatter(
                x=st.session_state.production_history["Date"],
                y=st.session_state.production_history["Nano_Enhanced_Oil"],
                mode='lines', name='Nano-Enhanced Production', line=dict(color=COLOR_PRIMARY, width=3)
            ))
            fig_analytics_prod.update_layout(
                title={'text':"Historical Production (bbl/day)", 'x':0.5, 'xanchor':'center'}, 
                xaxis_title='Date', yaxis_title='Oil Production (bbl/day)',
                plot_bgcolor=COLOR_BG_MEDIUM, paper_bgcolor=COLOR_BG_DARK,
                font=dict(color=COLOR_TEXT_LIGHT, family='Roboto Mono'),
                hovermode='x unified'
            )
            st.plotly_chart(fig_analytics_prod, use_container_width=True)
        else:
            st.info("Start simulation to see production data.")

    with col_analytics_forecast:
        st.subheader("\nProduction Forecast (AI Model)")
        forecast_dates, forecast_nano, forecast_traditional = forecast_production(st.session_state.production_history)
        
        fig_forecast = go.Figure()
        fig_forecast.add_trace(go.Scatter(
            x=st.session_state.production_history["Date"],
            y=st.session_state.production_history["Traditional_Oil"],
            mode='lines', name='Historical Traditional', line=dict(color=COLOR_SECONDARY, width=2)
        ))
        fig_forecast.add_trace(go.Scatter(
            x=forecast_dates,
            y=forecast_traditional,
            mode='lines', name='Forecast Traditional', line=dict(color=COLOR_SECONDARY, width=1, dash='dash')
        ))
        fig_forecast.add_trace(go.Scatter(
            x=st.session_state.production_history["Date"],
            y=st.session_state.production_history["Nano_Enhanced_Oil"],
            mode='lines', name='Historical Nano-Enhanced', line=dict(color=COLOR_PRIMARY, width=3)
        ))
        fig_forecast.add_trace(go.Scatter(
            x=forecast_dates,
            y=forecast_nano,
            mode='lines', name='Forecast Nano-Enhanced', line=dict(color=COLOR_PRIMARY, width=1, dash='dash')
        ))
        fig_forecast.update_layout(
            title={'text':"Production Forecast (bbl/day)", 'x':0.5, 'xanchor':'center'}, 
            xaxis_title='Date', yaxis_title='Oil Production (bbl/day)',
            plot_bgcolor=COLOR_BG_MEDIUM, paper_bgcolor=COLOR_BG_DARK,
            font=dict(color=COLOR_TEXT_LIGHT, family='Roboto Mono'),
            hovermode='x unified'
        )
        st.plotly_chart(fig_forecast, use_container_width=True)

    st.markdown("--- ")
    st.subheader("\nSensitivity Analysis (Spider Chart Placeholder)")
    st.info("Spider chart for sensitivity analysis will be implemented here.")

with tabs[3]: # Fiscal Yield Optimization
    st.header("\nFiscal Yield Optimization")
    st.markdown("Detailed financial analysis including NPV, ROI, and Cash Flow.")

    npv_nano, roi_nano, npv_traditional, roi_traditional, revenue_nano, revenue_traditional, cost_nano = calculate_economics(
        st.session_state.total_oil_produced_nano,
        st.session_state.total_oil_produced_traditional,
        st.session_state.total_nano_injected
    )

    col_fin1, col_fin2 = st.columns(2)
    with col_fin1:
        st.markdown(f"""
        <div class="card">
            <h3>Nano-Enhanced NPV</h3>
            <h2 style="color:{COLOR_PRIMARY};">${npv_nano:,.0f}</h2>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="card">
            <h3>Nano-Enhanced ROI</h3>
            <h2 style="color:{COLOR_PRIMARY};">{roi_nano:.2f}%</h2>
        </div>
        """, unsafe_allow_html=True)
    with col_fin2:
        st.markdown(f"""
        <div class="card">
            <h3>Traditional NPV</h3>
            <h2 style="color:{COLOR_SECONDARY};">${npv_traditional:,.0f}</h2>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="card">
            <h3>Traditional ROI</h3>
            <h2 style="color:{COLOR_SECONDARY};">{roi_traditional:.2f}%</h2>
        </div>
        """, unsafe_allow_html=True)

    st.subheader("\nCash Flow Analysis (Placeholder)")
    st.info("Detailed cash flow projections will be implemented here.")

with tabs[4]: # Geospatial Asset Surveillance
    st.header("\nGeospatial Asset Surveillance")
    st.markdown("Real-time monitoring of well locations and nano-swarm distribution.")

    # 2D Field Map
    fig_map = go.Figure()

    # Permeability background
    fig_map.add_trace(go.Heatmap(
        z=st.session_state.res.perm_grid,
        colorscale='Viridis', showscale=True,
        name='Permeability'
    ))

    # Nano-robots
    nano_x = [n.x for n in st.session_state.nano_swarm if n.energy > 0]
    nano_y = [n.y for n in st.session_state.nano_swarm if n.energy > 0]
    nano_colors = [n.color for n in st.session_state.nano_swarm if n.energy > 0]

    if nano_x:
        fig_map.add_trace(go.Scatter(
            x=nano_y, y=nano_x, # Swapped for correct orientation
            mode='markers', 
            marker=dict(size=10, color=nano_colors, opacity=0.8, symbol='circle'),
            name='Nano-Robots'
        ))
    
    # Production Well
    prod_x, prod_y = st.session_state.production_well_pos
    fig_map.add_trace(go.Scatter(
        x=[prod_y], y=[prod_x], # Swapped
        mode='markers', 
        marker=dict(size=15, color='red', symbol='diamond', line=dict(width=2, color='white')),
        name='Production Well'
    ))

    # Injection Well
    inj_x, inj_y = st.session_state.injection_well_pos
    fig_map.add_trace(go.Scatter(
        x=[inj_y], y=[inj_x], # Swapped
        mode='markers', 
        marker=dict(size=15, color='blue', symbol='circle', line=dict(width=2, color='white')),
        name='Injection Well'
    ))

    fig_map.update_layout(
        title={'text':"2D Field Map & Nano-Swarm Distribution", 'x':0.5, 'xanchor':'center'}, 
        xaxis_title='Y-Coordinate', yaxis_title='X-Coordinate',
        plot_bgcolor=COLOR_BG_DARK, paper_bgcolor=COLOR_BG_DARK,
        font=dict(color=COLOR_TEXT_LIGHT, family='Roboto Mono'),
        height=700
    )
    st.plotly_chart(fig_map, use_container_width=True)

with tabs[5]: # Operational Protocols
    st.header("\nOperational Protocols & Smart Alerts")
    st.markdown("Guidelines and automated alerts for optimal nano-swarm deployment.")

    st.subheader("\nSmart Alert System (Placeholder)")
    st.info("Automated alerts for critical reservoir conditions or nano-swarm status will appear here.")

    st.subheader("\nOperational Guidelines (Placeholder)")
    st.markdown("""
    - **Phase 1: Initial Deployment**: Inject nano-robots at a moderate rate (5-10 units/step) near the injection well.
    - **Phase 2: Monitoring & Optimization**: Observe nano-swarm distribution and production response. Adjust injection rate and reservoir parameters (pressure, salinity) for optimal oil recovery.
    - **Phase 3: Targeted Intervention**: Use manual control to guide nano-swarms to bypass tight zones or target high residual oil saturation areas.
    """)

with tabs[6]: # Project Guide / دليل المشروع
    st.header("\nProject Guide / دليل المشروع")
    st.markdown("""
    <div class="guide-section">
        <h3>About the Project / عن المشروع</h3>
        <p>This platform simulates the revolutionary application of **Nano-Swarm Enhanced Oil Recovery (EOR)**. Intelligent nano-robots are deployed into the reservoir to actively seek and mobilize trapped oil, significantly boosting production efficiency, reducing environmental impact, and optimizing operational costs.</p>
        <p>تُحاكي هذه المنصة التطبيق الثوري لتقنية **الاستخلاص المعزز للنفط (EOR) باستخدام أسراب النانو**. يتم نشر روبوتات النانو الذكية داخل المكمن للبحث عن النفط المحبوس وتحريكه بفعالية، مما يؤدي إلى زيادة كبيرة في كفاءة الإنتاج، وتقليل الأثر البيئي، وتحسين التكاليف التشغيلية.</p>
    </div>

    <div class="guide-section">
        <h3>How to Use: An Engineering Walkthrough / دليل الاستخدام: جولة هندسية</h3>
        <p>This section guides you through the practical use of the platform, highlighting the engineering significance of each step.</p>
        <p>يرشدك هذا القسم خلال الاستخدام العملي للمنصة، مع تسليط الضوء على الأهمية الهندسية لكل خطوة.</p>

        <h4>1. Baseline Monitoring (Dashboard) / 1. مراقبة خط الأساس (لوحة التحكم)</h4>
        <p>Begin by observing the **Traditional Production** in the Dashboard. Adjust the **Reservoir Pressure** and **Formation Water Salinity** sliders in the sidebar to understand their impact on conventional oil recovery. This establishes a baseline for comparison.</p>
        <p>ابدأ بمراقبة **الإنتاج التقليدي** في لوحة التحكم (Dashboard). قم بتعديل منزلقات **ضغط المكمن** و**ملوحة مياه التكوين** في الشريط الجانبي لفهم تأثيرها على استخلاص النفط التقليدي. هذا يؤسس خط أساس للمقارنة.</p>

        <h4>2. Nano-Swarm Activation (Sidebar) / 2. تفعيل سرب النانو (الشريط الجانبي)</h4>
        <p>Clicking **"START SIMULATION"** in the sidebar is the moment the nano-robots are virtually injected into the reservoir. Observe the increase in **Nano-Enhanced Production** as the swarm begins its work.</p>
        <p>الضغط على زر **"START SIMULATION"** في الشريط الجانبي يمثل لحظة حقن روبوتات النانو افتراضياً في المكمن. راقب الزيادة في **الإنتاج المعزز بالنانو** مع بدء السرب لعمله.</p>

        <h4>3. Subsurface Digital Twin: Real-time Dynamics / 3. التوأم الرقمي تحت السطح: ديناميكية الوقت الفعلي</h4>
        <p>Navigate to the **"Subsurface Digital Twin"** tab. Here, you'll witness the nano-swarm in action. Observe their movement, energy levels (color changes), and how they intelligently navigate the permeability grid. This visually represents their search for **trapped oil** and their energy consumption in challenging reservoir conditions.</p>
        <p>انتقل إلى تبويب **"Subsurface Digital Twin"**. هنا، ستشاهد سرب النانو وهو يعمل. راقب حركتهم، مستويات طاقتهم (تغير الألوان)، وكيف يتنقلون بذكاء عبر شبكة النفاذية. يمثل هذا بصرياً بحثهم عن **النفط المحبوس** واستهلاكهم للطاقة في ظروف المكمن الصعبة.</p>

        <h4>4. Manual Swarm Control (Sidebar) / 4. التحكم اليدوي بالسرب (الشريط الجانبي)</h4>
        <p>The directional arrows in the sidebar represent the **mechatronics core** of the project. As an engineer, you can manually guide the nano-swarm's target (production well position) towards specific areas, demonstrating strategic intervention to optimize oil recovery.</p>
        <p>تمثل الأسهم الاتجاهية في الشريط الجانبي **الجوهر الميكاترونكسي** للمشروع. كمهندس، يمكنك توجيه هدف سرب النانو يدوياً (موقع بئر الإنتاج) نحو مناطق محددة، مما يوضح التدخل الاستراتيجي لتحسين استخلاص النفط.</p>

        <h4>5. AI Analytics & Forecasting / 5. تحليلات وتوقعات الذكاء الاصطناعي</h4>
        <p>In this tab, analyze the **Nano Lift Percentage** and compare historical production curves. The **AI Forecast** provides insights into future production trends, demonstrating the long-term benefits of nano-EOR.</p>
        <p>في هذا التبويب، قم بتحليل **نسبة زيادة الإنتاج بالنانو** وقارن منحنيات الإنتاج التاريخية. توفر **توقعات الذكاء الاصطناعي** رؤى حول اتجاهات الإنتاج المستقبلية، مما يوضح الفوائد طويلة الأجل لتقنية الاستخلاص المعزز بالنانو.</p>

        <h4>6. Fiscal Yield Optimization / 6. تحسين العائد المالي</h4>
        <p>Review the **Net Present Value (NPV)** and **Return on Investment (ROI)** for both traditional and nano-enhanced scenarios. This tab highlights the economic viability and superior financial performance of the nano-EOR technology.</p>
        <p>راجع **صافي القيمة الحالية (NPV)** و**العائد على الاستثمار (ROI)** لكل من السيناريوهات التقليدية والمعززة بالنانو. يسلط هذا التبويب الضوء على الجدوى الاقتصادية والأداء المالي المتفوق لتقنية الاستخلاص المعزز بالنانو.</p>

        <h4>7. Geospatial Asset Surveillance / 7. مراقبة الأصول الجغرافية المكانية</h4>
        <p>Observe the 2D field map showing the **injection and production well locations** and the real-time distribution of the nano-swarm. This feature demonstrates the field-scale applicability and monitoring capabilities of the system.</p>
        <p>راقب خريطة الحقل ثنائية الأبعاد التي توضح **مواقع آبار الحقن والإنتاج** والتوزيع الفعلي لسرب النانو. توضح هذه الميزة قابلية تطبيق النظام على نطاق الحقل وقدرات المراقبة.</p>

        <h4>8. Operational Protocols & Smart Alerts / 8. بروتوكولات التشغيل والتنبيهات الذكية</h4>
        <p>This tab provides operational guidelines and will feature **smart alerts** for critical reservoir conditions or nano-swarm status, enabling proactive management.</p>
        <p>يوفر هذا التبويب إرشادات التشغيل وسيحتوي على **تنبيهات ذكية** لظروف المكمن الحرجة أو حالة سرب النانو، مما يتيح الإدارة الاستباقية.</p>

        <h4>9. Economic & Environmental Impact / 9. الأثر الاقتصادي والبيئي</h4>
        <p>The project's ultimate goal is to achieve **higher production** with **lower costs** and a **reduced environmental footprint** (e.g., water saving, carbon reduction), making it a sustainable solution for the future of oil and gas.</p>
        <p>الهدف النهائي للمشروع هو تحقيق **إنتاج أعلى** بتكاليف **أقل** و**بصمة بيئية منخفضة** (مثل توفير المياه وتقليل الكربون)، مما يجعله حلاً مستداماً لمستقبل النفط والغاز.</p>

    </div>

    <div class="guide-section">
        <h3>Development Team / فريق العمل</h3>
        <div class="team-member">Bashar Abdullah salah Al-zaidy</div>
        <div class="team-member">Rafa Saeed Abdullah Al-Qadasi</div>
        <div class="team-member">Ahmed Haysami Ahmed Alhaisami</div>
        <div class="team-member">Radman Hames Ahmed Omair</div>
        <div class="team-member">Abdulqader Rafat Saeed Awadh Ben Fareg</div>
    </div>

    <div class="guide-section">
        <h3>How to Run the Application / كيفية تشغيل التطبيق</h3>
        <p>To run this advanced simulation platform, follow these steps:</p>
        <p>لتشغيل منصة المحاكاة المتقدمة هذه، اتبع الخطوات التالية:</p>
        <ol>
            <li>**Install Streamlit**: If you don't have Streamlit installed, open your terminal or command prompt and run: <code style="color:var(--primary-color);">pip install streamlit pandas numpy plotly scipy openpyxl</code></li>
            <li>**Place Excel Files**: Ensure the four Excel data files (<code style="color:var(--primary-color);">PVTO.xlsx</code>, <code style="color:var(--primary-color);">water-oil Relative permeability.xlsx</code>, <code style="color:var(--primary-color);">capillary pressure.xlsx</code>, <code style="color:var(--primary-color);">Pro.xlsx</code>) are in the **same directory** as this Python script.</li>
            <li>**Run the Application**: Open your terminal or command prompt, navigate to the directory where you saved the script and Excel files, and run: <code style="color:var(--primary-color);">streamlit run nano_swarm_eor_ultimate_masterpiece.py</code></li>
            <li>**Enjoy the Simulation**: Your web browser will automatically open, displaying the Nano-Swarm EOR platform.</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

# --- Simulation Loop ---
if st.session_state.simulation_running:
    st.session_state.time_step += 1
    st.session_state.current_date += pd.Timedelta(days=1)

    # Inject new nano-robots
    for _ in range(st.session_state.nano_injection_rate):
        st.session_state.nano_swarm.append(NanoRobot(
            st.session_state.injection_well_pos[0],
            st.session_state.injection_well_pos[1]
        ))
    st.session_state.total_nano_injected += st.session_state.nano_injection_rate
    st.session_state.total_nano_cost += st.session_state.nano_injection_rate * st.session_state.nano_cost_per_unit
    
    # Track nano injection history
    new_injection_entry = pd.DataFrame({
        "Date": [st.session_state.current_date],
        "Injected_Units": [st.session_state.nano_injection_rate]
    })
    st.session_state.nano_injected_history = pd.concat([st.session_state.nano_injected_history, new_injection_entry], ignore_index=True)

    # Update nano-robots and reservoir
    active_nano = [n for n in st.session_state.nano_swarm if n.energy > 0]
    for nano in active_nano:
        nano.move(st.session_state.res, st.session_state.production_well_pos[0], st.session_state.production_well_pos[1], st.session_state.current_pressure, st.session_state.current_salinity)
    st.session_state.res.update_nano_effect(active_nano)

    # Calculate current production rates
    # Traditional production (declining over time)
    current_traditional_production = st.session_state.traditional_production_rate * (1 - st.session_state.time_step * 0.0005)
    current_traditional_production = max(50, current_traditional_production) # Minimum production

    # Nano-enhanced production (based on nano-swarm effect)
    # Average properties around production well
    prod_x, prod_y = st.session_state.production_well_pos
    _, _, oil_viscosity_prod, kro_prod, _, _, _ = st.session_state.res.get_local_properties(prod_x, prod_y, st.session_state.current_pressure)
    
    # Darcy's Law simplified: Q = (k * A * delta_P) / (mu * L)
    # Assuming k, A, delta_P, L are constant for simplicity, focus on mu and kro
    # Higher kro, lower mu -> higher production
    nano_effect_factor = (kro_prod / oil_viscosity_prod) / (kro_interp(0.3) / visc_interp(st.session_state.current_pressure)) # Compare to a baseline
    current_nano_enhanced_production = current_traditional_production * (1 + nano_effect_factor * 0.5) # Example enhancement
    current_nano_enhanced_production = max(current_traditional_production, current_nano_enhanced_production)

    st.session_state.nano_enhanced_production_rate = current_nano_enhanced_production
    st.session_state.traditional_production_rate = current_traditional_production

    # Update total oil produced
    st.session_state.total_oil_produced_nano += current_nano_enhanced_production
    st.session_state.total_oil_produced_traditional += current_traditional_production

    # Calculate Nano Lift Percentage
    if st.session_state.total_oil_produced_traditional > 0:
        st.session_state.nano_lift_percentage = ((st.session_state.total_oil_produced_nano - st.session_state.total_oil_produced_traditional) / st.session_state.total_oil_produced_traditional) * 100
    else:
        st.session_state.nano_lift_percentage = 0.0

    # Add to production history
    new_production_entry = pd.DataFrame({
        "Date": [st.session_state.current_date],
        "Traditional_Oil": [current_traditional_production],
        "Nano_Enhanced_Oil": [current_nano_enhanced_production]
    })
    st.session_state.production_history = pd.concat([st.session_state.production_history, new_production_entry], ignore_index=True)

    # Log events
    if st.session_state.time_step % 10 == 0:
        log_event(f"Time Step: {st.session_state.time_step}, Nano Production: {current_nano_enhanced_production:.0f} bbl/day, Lift: {st.session_state.nano_lift_percentage:.2f}%", "info")
    
    # Re-run the app to update visuals
    time.sleep(0.1) # Control simulation speed
    st.rerun()
