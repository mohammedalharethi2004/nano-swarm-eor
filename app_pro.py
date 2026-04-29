import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import interp1d
import time, random, datetime

st.set_page_config(layout="wide", page_title="Energy Command Center", page_icon="⚡")

# ================= THEME & STYLING =================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Roboto+Mono:wght@300;400;700&display=swap');

    body {
        background: #0a0a1a; /* Darker, more futuristic background */
        color: #e0e0e0; /* Lighter text for contrast */
        font-family: 'Roboto Mono', monospace;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Orbitron', sans-serif; /* Futuristic font for titles */
        color: #00ffcc; /* Neon green for titles */
    }

    .stApp {
        background-color: #0a0a1a;
    }

    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.2rem;
        font-weight: bold;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 24px; /* Space out tabs */
    }

    .stTabs [data-baseweb="tab-list"] button {
        background-color: #1a1a3a; /* Darker tab background */
        border-radius: 8px 8px 0 0;
        border: 1px solid #00ffcc; /* Neon border */
        color: #e0e0e0;
        padding: 10px 20px;
        transition: all 0.3s ease-in-out;
    }

    .stTabs [data-baseweb="tab-list"] button:hover {
        background-color: #00ffcc; /* Neon hover effect */
        color: #0a0a1a;
        box-shadow: 0 0 15px #00ffcc;
    }

    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: #00ffcc; /* Active tab neon */
        color: #0a0a1a;
        border-bottom: 3px solid #0a0a1a; /* Hide bottom border for active tab */
        box-shadow: 0 0 20px #00ffcc;
    }

    .card {
        background: linear-gradient(145deg, rgba(0,255,204,0.1), rgba(0,100,200,0.1)); /* Gradient background */
        border: 1px solid #00ffcc; /* Neon border */
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 0 25px rgba(0,255,204,0.5); /* Glowing shadow */
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

    /* Streamlit specific overrides */
    .stSlider > div > div > div[data-testid="stThumbValue"] {
        background-color: #00ffcc; /* Slider thumb color */
        border: 1px solid #00ffcc;
    }
    .stSlider > div > div > div[data-testid="stTrack"] > div {
        background-color: #00ffcc; /* Slider track color */
    }
    .stButton > button {
        background-color: #1a1a3a; /* Button background */
        color: #00ffcc; /* Button text color */
        border: 1px solid #00ffcc;
        border-radius: 8px;
        padding: 10px 20px;
        font-family: 'Orbitron', sans-serif;
        transition: all 0.3s ease-in-out;
    }
    .stButton > button:hover {
        background-color: #00ffcc; /* Button hover background */
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
        color: #00ffcc; /* Metric label color */
        font-family: 'Orbitron', sans-serif;
    }
    .stMetric > div > div:last-child > div:first-child {
        color: #e0e0e0; /* Metric value color */
        font-size: 2.5em;
        font-weight: bold;
    }
    .stAlert {
        background-color: rgba(0,255,204,0.1);
        border-left: 5px solid #00ffcc;
        color: #e0e0e0;
    }
    .stAlert > div > div > div > p {
        color: #e0e0e0;
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

        visc = interp1d(pvto['pressure'], pvto['oil viscosity'], fill_value="extrapolate")
        kro = interp1d(rel['sw'], rel['kro'], fill_value="extrapolate")
        pc = interp1d(cap['sw'], cap['pcow (psi)'], fill_value="extrapolate")

        return visc, kro, pc, pro
    except FileNotFoundError:
        st.error("Error: One or more data files (PVTO.xlsx, water-oil Relative permeability.xlsx, capillary pressure.xlsx, Pro.xlsx) not found. Please ensure they are in the same directory as the app.")
        st.stop()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()

visc, kro, pc, pro = load_data()

# ================= MODEL =================
class Reservoir:
    def __init__(self):
        self.grid = np.random.rand(25,25) * 100 # Scale grid for better visualization

    def production(self,p):
        mu = float(visc(p))
        sw = np.mean(self.grid) / 100 # Adjust for scaled grid
        # Ensure sw is within the range of kro and pc interpolation
        sw = np.clip(sw, 0.01, 0.99) 
        return (float(kro(sw))*(p-float(pc(sw)))/1000)/(mu+1e-6)

class Nano:
    def __init__(self):
        self.x = np.random.randint(0,25)
        self.y = np.random.randint(0,25)

    def move(self,grid,dx=0,dy=0):
        # Normalize gradient for smoother movement and prevent extreme jumps
        gx, gy = np.gradient(grid)
        # Apply a small factor to gradient to control movement speed
        self.x = int(np.clip(self.x + gx[self.x,self.y]*0.1 + dx,0,24))
        self.y = int(np.clip(self.y + gy[self.x,self.y]*0.1 + dy,0,24))

# ================= SESSION =================
if "res" not in st.session_state:
    st.session_state.res = Reservoir()
    st.session_state.nano = [Nano() for _ in range(50)] # More nano particles for richer visualization
    st.session_state.logs=[]
    st.session_state.run=False
    st.session_state.dx=0
    st.session_state.dy=0
    st.session_state.start=time.time()
    st.session_state.series=[]
    st.session_state.pressure_history = []
    st.session_state.production_history = []

res = st.session_state.res

# ================= HEADER =================
st.markdown("<h1 style='text-align: center; color: #00ffcc;'>⚡ Energy Command Center ⚡</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #e0e0e0;'>Advanced Nano-Enhanced Oil Recovery Simulation</p>", unsafe_allow_html=True)
st.markdown("--- ")

# ================= TABS =================
tabs = st.tabs(["Dashboard","Subsurface Digital Twin","Mission Control","AI Analytics","Economics & ROI","Field Operations Map"])

# ================= DASHBOARD =================
with tabs[0]:
    st.markdown("<h2 style='color: #00ffcc;'>Operational Overview</h2>", unsafe_allow_html=True)

    p = st.slider("Simulated Reservoir Pressure (psi)", 500, 3000, 1500, help="Adjust the reservoir pressure to observe its impact on production.")
    st.session_state.pressure_history.append(p)

    base_production = pro.select_dtypes(include=np.number).mean().mean()
    nano_production = res.production(p)
    st.session_state.production_history.append(nano_production)

    c1,c2,c3 = st.columns(3)
    with c1:
        st.markdown(f"<div class='card'><h3>Traditional Production</h3><p>{base_production:.2f} bbl/day</p></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='card'><h3>Nano-Enhanced Production</h3><p>{nano_production:.2f} bbl/day</p></div>", unsafe_allow_html=True)
    with c3:
        lift_percentage = ((nano_production - base_production) / base_production * 100) if base_production != 0 else 0
        st.markdown(f"<div class='card'><h3>Production Lift</h3><p>{lift_percentage:.2f}%</p></div>", unsafe_allow_html=True)

    st.markdown("<h3 style='color: #00ffcc;'>Real-time Production Gauge</h3>", unsafe_allow_html=True)
    fig_gauge = go.Figure(go.Indicator(mode="gauge+number+delta", value=nano_production,
        title={'text':"Total Production (bbl/day)", 'font': {'size': 20, 'color': '#e0e0e0'}},
        delta = {'reference': st.session_state.production_history[-2] if len(st.session_state.production_history) > 1 else base_production, 'increasing':{'color':'#00ffcc'}, 'decreasing':{'color':'#ff4d4d'}},
        gauge={
            'axis':{'range':[0, max(1,nano_production*1.5)], 'tickwidth':1, 'tickcolor':'#e0e0e0'},
            'bar':{'color':'#00ffcc'},
            'bgcolor':'#1a1a3a',
            'borderwidth':2,
            'bordercolor':'#00ffcc',
            'steps':[
                {'range':[0, base_production], 'color':'#3a3a5a'},
                {'range':[base_production, max(1,nano_production*1.5)], 'color':'#00cc99'}
            ],
            'threshold':{'line':{'color':'#ff4d4d', 'width':4}, 'thickness':0.75, 'value': base_production}
        }
    ))
    fig_gauge.update_layout(height=300, margin=dict(l=10,r=10,t=50,b=10), font={'color': '#e0e0e0', 'family': 'Roboto Mono'})
    st.plotly_chart(fig_gauge, use_container_width=True)

    st.markdown("<h3 style='color: #00ffcc;'>System Status</h3>", unsafe_allow_html=True)
    col_status1, col_status2 = st.columns(2)
    with col_status1:
        st.markdown(f"<div class='card'><h3>System Time</h3><p>{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p></div>", unsafe_allow_html=True)
    with col_status2:
        st.markdown(f"<div class='card'><h3>CPU Load</h3><p>{random.randint(10,80)}%</p></div>", unsafe_allow_html=True)

# ================= SUBSURFACE =================
with tabs[1]:
    st.markdown("<h2 style='color: #00ffcc;'>Subsurface Digital Twin: Nano Particle Dynamics</h2>", unsafe_allow_html=True)
    st.write("Visualize the 3D reservoir grid and the movement of nano particles within it. The color intensity represents reservoir properties.")

    chart_placeholder = st.empty()

    if st.session_state.run:
        for n in st.session_state.nano:
            n.move(res.grid, st.session_state.dx, st.session_state.dy)

        xs=[n.x for n in st.session_state.nano]
        ys=[n.y for n in st.session_state.nano]
        zs=[res.grid[x,y] for x,y in zip(xs,ys)]

        fig_subsurface = go.Figure()
        fig_subsurface.add_trace(go.Surface(z=res.grid, colorscale="Turbo", opacity=0.8, name="Reservoir Grid"))
        fig_subsurface.add_trace(go.Scatter3d(x=xs,y=ys,z=zs,
                                  mode='markers',
                                  marker=dict(size=4, color='cyan', opacity=0.9, symbol='circle'),
                                  name="Nano Particles"))
        
        fig_subsurface.update_layout(
            scene=dict(
                xaxis_title='X-Coordinate',
                yaxis_title='Y-Coordinate',
                zaxis_title='Reservoir Property',
                bgcolor='#0a0a1a',
                aspectmode='cube'
            ),
            title_text='Nano Particle Movement in Reservoir',
            title_font_color='#00ffcc',
            height=700,
            margin=dict(l=0, r=0, b=0, t=50),
            paper_bgcolor='#0a0a1a',
            plot_bgcolor='#0a0a1a',
            font=dict(color='#e0e0e0', family='Roboto Mono')
        )
        chart_placeholder.plotly_chart(fig_subsurface, use_container_width=True)

        time.sleep(0.2) # Slightly faster update
        st.rerun()
    else:
        st.info("Simulation is paused. Press 'START' in Mission Control to begin nano particle movement.")
        # Display a static initial view of the subsurface
        fig_subsurface_static = go.Figure()
        fig_subsurface_static.add_trace(go.Surface(z=res.grid, colorscale="Turbo", opacity=0.8, name="Reservoir Grid"))
        fig_subsurface_static.update_layout(
            scene=dict(
                xaxis_title='X-Coordinate',
                yaxis_title='Y-Coordinate',
                zaxis_title='Reservoir Property',
                bgcolor='#0a0a1a',
                aspectmode='cube'
            ),
            title_text='Initial Reservoir State',
            title_font_color='#00ffcc',
            height=700,
            margin=dict(l=0, r=0, b=0, t=50),
            paper_bgcolor='#0a0a1a',
            plot_bgcolor='#0a0a1a',
            font=dict(color='#e0e0e0', family='Roboto Mono')
        )
        chart_placeholder.plotly_chart(fig_subsurface_static, use_container_width=True)

# ================= CONTROL =================
with tabs[2]:
    st.markdown("<h2 style='color: #00ffcc;'>Mission Control: System & Nano Management</h2>", unsafe_allow_html=True)

    st.markdown("<h3 style='color: #00ffcc;'>System Health Monitors</h3>", unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)

    # Health Monitor Gauges
    for col,title,val in zip([c1,c2,c3],
        ["Signal Strength","Battery Level","Network Connectivity"],
        [random.randint(60,100),random.randint(50,100),random.randint(70,100)]):

        fig_health = go.Figure(go.Indicator(mode="gauge",value=val,
            title={'text':title, 'font': {'size': 16, 'color': '#e0e0e0'}},
            gauge={
                'axis':{'range':[0,100], 'tickwidth':1, 'tickcolor':'#e0e0e0'},
                'bar':{'color':'#00ffcc'},
                'bgcolor':'#1a1a3a',
                'borderwidth':2,
                'bordercolor':'#00ffcc',
                'steps':[
                    {'range':[0, 30], 'color':'#ff4d4d'},
                    {'range':[30, 70], 'color':'#ffd166'},
                    {'range':[70, 100], 'color':'#00ffcc'}
                ]
            }
        ))
        fig_health.update_layout(height=200, margin=dict(l=10,r=10,t=50,b=10), font={'color': '#e0e0e0', 'family': 'Roboto Mono'})
        col.plotly_chart(fig_health, use_container_width=True)

    st.markdown("<h3 style='color: #00ffcc;'>Nano Particle Manual Override</h3>", unsafe_allow_html=True)
    col_ctrl1,col_ctrl2,col_ctrl3 = st.columns(3)
    with col_ctrl2:
        if st.button("⬆ Move Up", key="up_btn"): st.session_state.dx=-1
    col_ctrl1,col_ctrl2,col_ctrl3 = st.columns(3)
    with col_ctrl1:
        if st.button("⬅ Move Left", key="left_btn"): st.session_state.dy=-1
    with col_ctrl3:
        if st.button("➡ Move Right", key="right_btn"): st.session_state.dy=1
    with col_ctrl2:
        if st.button("⬇ Move Down", key="down_btn"): st.session_state.dx=1
    
    st.markdown("--- ")
    st.markdown("<h3 style='color: #00ffcc;'>Simulation Control</h3>", unsafe_allow_html=True)
    col_sim_ctrl1, col_sim_ctrl2 = st.columns(2)
    with col_sim_ctrl1:
        if st.button("▶ START SIMULATION", key="start_sim_btn", help="Initiate the nano particle simulation."):
            st.session_state.run=True
            st.session_state.logs.append(("INFO","System Simulation Initiated"))
            st.success("Simulation Started!")
    with col_sim_ctrl2:
        if st.button("🛑 EMERGENCY STOP", key="stop_sim_btn", help="Halt all simulation processes immediately."):
            st.session_state.run=False
            st.session_state.logs.append(("ERROR","Emergency Stop Activated - Simulation Halted"))
            st.error("Simulation Halted!")

# ================= ANALYTICS =================
with tabs[3]:
    st.markdown("<h2 style='color: #00ffcc;'>AI-Powered Production Analytics</h2>", unsafe_allow_html=True)
    st.write("Monitor real-time production trends, AI predictions, and confidence intervals.")

    base_production = pro.select_dtypes(include=np.number).mean().mean()
    current_nano_production = res.production(st.session_state.pressure_history[-1] if st.session_state.pressure_history else 1500)

    st.session_state.series.append(current_nano_production)

    y=np.array(st.session_state.series)
    x=np.arange(len(y))

    # Enhanced Prediction Logic (simple linear extrapolation for now, can be replaced with ML model)
    if len(y) > 10:
        # Use last 10 points for a more stable slope calculation
        slope = (y[-1]-y[-10])/10 
    elif len(y) > 1:
        slope = (y[-1]-y[-2]) # Use last 2 points if not enough for 10
    else:
        slope = 0

    future_steps = 15 # Predict further into the future
    future = [y[-1]+slope*i for i in range(1,future_steps+1)]

    fig_analytics = go.Figure()

    fig_analytics.add_trace(go.Scatter(x=x, y=y, name="Nano-Enhanced Production",
                                     line=dict(color="#00ffcc", width=4, shape='spline'),
                                     mode='lines+markers', marker=dict(size=5, symbol='circle')))
    fig_analytics.add_trace(go.Scatter(x=x, y=[base_production]*len(y), name="Traditional Production Baseline",
                                     line=dict(dash='dash', color='#e0e0e0', width=2)))

    # Prediction + Confidence
    x_future = np.arange(len(y), len(y) + future_steps)
    confidence_factor = 0.15 # Increased confidence band
    upper=[f*(1+confidence_factor) for f in future]
    lower=[f*(1-confidence_factor) for f in future]

    fig_analytics.add_trace(go.Scatter(x=x_future, y=future, name="AI Prediction",
                                     line=dict(color="#ffd166", width=3, dash='dot'),
                                     mode='lines', marker=dict(size=4, symbol='diamond')))
    fig_analytics.add_trace(go.Scatter(x=x_future, y=upper, fill=None, mode='lines', line_color='rgba(255,209,102,0.3)', showlegend=False))
    fig_analytics.add_trace(go.Scatter(x=x_future, y=lower, fill='tonexty', mode='lines', line_color='rgba(255,209,102,0.3)', fillcolor='rgba(255,209,102,0.1)', name="Confidence Interval"))

    fig_analytics.update_layout(
        height=600, 
        template="plotly_dark",
        title_text='Production Trend & AI Forecast',
        title_font_color='#00ffcc',
        xaxis_title='Time Step',
        yaxis_title='Production (bbl/day)',
        paper_bgcolor='#0a0a1a',
        plot_bgcolor='#1a1a3a',
        font=dict(color='#e0e0e0', family='Roboto Mono'),
        hovermode='x unified'
    )
    st.plotly_chart(fig_analytics, use_container_width=True)

    st.markdown("<h3 style='color: #00ffcc;'>AI Insights</h3>", unsafe_allow_html=True)
    st.info(random.choice([
        "[AI System] Analyzing subsurface fluid dynamics for optimal nano-particle distribution.",
        "[AI System] Predicting future production rates based on current simulation parameters and historical data.",
        "[AI System] Optimizing injection strategies to maximize oil recovery and minimize operational costs.",
        "[AI System] Detecting anomalies in reservoir behavior and recommending corrective actions."
    ]))

# ================= ECONOMICS =================
with tabs[4]:
    st.markdown("<h2 style='color: #00ffcc;'>Economics & Return on Investment (ROI)</h2>", unsafe_allow_html=True)
    st.write("Evaluate the financial viability of nano-enhanced oil recovery operations.")

    col_econ1, col_econ2 = st.columns(2)
    with col_econ1:
        oil_price = st.number_input("Global Oil Price ($/barrel)", 50, 150, 80, step=5, help="Current market price of oil.")
    with col_econ2:
        opex_cost = st.number_input("Operational Expenditure ($/day)", 1000, 50000, 5000, step=500, help="Daily operational costs for nano-EOR.")

    current_prod_econ = res.production(st.session_state.pressure_history[-1] if st.session_state.pressure_history else 1500)
    
    revenue = current_prod_econ * oil_price
    net_present_value = revenue - opex_cost # Simplified NPV for daily calculation

    st.markdown("--- ")
    st.markdown("<h3 style='color: #00ffcc;'>Financial Metrics</h3>", unsafe_allow_html=True)
    col_metrics1, col_metrics2 = st.columns(2)
    with col_metrics1:
        st.metric(label="Daily Revenue", value=f"${revenue:,.2f}", delta=f"${revenue - (st.session_state.production_history[-2] * oil_price if len(st.session_state.production_history) > 1 else 0):,.2f}" if len(st.session_state.production_history) > 1 else None, delta_color="normal")
    with col_metrics2:
        st.metric(label="Daily Net Value", value=f"${net_present_value:,.2f}", delta=f"${net_present_value - ((st.session_state.production_history[-2] * oil_price) - opex_cost if len(st.session_state.production_history) > 1 else 0):,.2f}" if len(st.session_state.production_history) > 1 else None, delta_color="normal")

    st.markdown("--- ")
    st.markdown("<h3 style='color: #00ffcc;'>Financial Report Export</h3>", unsafe_allow_html=True)
    df_report = pd.DataFrame({"Metric":["Production (bbl/day)", "Oil Price ($/bbl)", "Daily Revenue ($)", "Daily OPEX ($)", "Daily Net Value ($)"],
                              "Value":[current_prod_econ, oil_price, revenue, opex_cost, net_present_value]})
    st.download_button(
        label="Download Financial Report (CSV)",
        data=df_report.to_csv(index=False).encode('utf-8'),
        file_name="nano_eor_financial_report.csv",
        mime="text/csv",
        help="Export current financial metrics to a CSV file."
    )

# ================= FIELD MAP =================
with tabs[5]:
    st.markdown("<h2 style='color: #00ffcc;'>Field Operations Map</h2>", unsafe_allow_html=True)
    st.write("Overview of the oil field, showing well locations and potential areas for nano-EOR deployment.")

    # Enhanced Field Map with simulated well clusters and a central facility
    num_wells = 25
    np.random.seed(42) # for reproducibility
    well_x = np.random.rand(num_wells) * 100
    well_y = np.random.rand(num_wells) * 100
    well_status = [random.choice(['Active', 'Inactive', 'Maintenance']) for _ in range(num_wells)]

    fig_field_map = go.Figure()

    # Add well locations
    fig_field_map.add_trace(go.Scatter(
        x=well_x,
        y=well_y,
        mode='markers',
        marker=dict(
            size=10,
            color=[{'Active':'#00ffcc', 'Inactive':'#ffd166', 'Maintenance':'#ff4d4d'}[s] for s in well_status],
            symbol='triangle-up',
            line=dict(width=1, color='DarkSlateGrey')
        ),
        name='Oil Wells',
        text=[f'Well {i+1}<br>Status: {well_status[i]}' for i in range(num_wells)],
        hoverinfo='text'
    ))

    # Add a central processing facility
    fig_field_map.add_trace(go.Scatter(
        x=[50],
        y=[50],
        mode='markers',
        marker=dict(
            size=20,
            color='#e0e0e0',
            symbol='star',
            line=dict(width=2, color='#00ffcc')
        ),
        name='Central Facility',
        text='Central Processing Facility',
        hoverinfo='text'
    ))

    fig_field_map.update_layout(
        title_text='Oil Field Layout & Well Status',
        title_font_color='#00ffcc',
        xaxis_title='Field Easting (km)',
        yaxis_title='Field Northing (km)',
        height=600,
        paper_bgcolor='#0a0a1a',
        plot_bgcolor='#1a1a3a',
        font=dict(color='#e0e0e0', family='Roboto Mono'),
        showlegend=True
    )
    st.plotly_chart(fig_field_map, use_container_width=True)

    st.markdown("<h3 style='color: #00ffcc;'>Well Status Summary</h3>", unsafe_allow_html=True)
    status_counts = pd.Series(well_status).value_counts()
    for status, count in status_counts.items():
        color = {'Active':'#00ffcc', 'Inactive':'#ffd166', 'Maintenance':'#ff4d4d'}.get(status, '#e0e0e0')
        st.markdown(f"<p style='color:{color};'>• {status}: {count} wells</p>", unsafe_allow_html=True)

# ================= LOG / EVENT CONSOLE =================
st.markdown("--- ")
st.markdown("<h2 style='color: #00ffcc;'>🧠 System Event Console</h2>", unsafe_allow_html=True)
st.write("Real-time log of system activities and simulation events.")

log_container = st.empty()

def update_log_display():
    log_html = """<div style='background-color: #1a1a3a; border: 1px solid #00ffcc; border-radius: 8px; padding: 15px; max-height: 300px; overflow-y: auto;'>"""
    for t, msg in reversed(st.session_state.logs[-20:]): # Display last 20 logs, newest first
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        if t == "ERROR":
            log_html += f"<p style='color:#ff4d4d;'>[{timestamp}] [ERROR] {msg}</p>"
        elif t == "INFO":
            log_html += f"<p style='color:#00ffcc;'>[{timestamp}] [INFO] {msg}</p>"
        else:
            log_html += f"<p style='color:#ffd166;'>[{timestamp}] [WARNING] {msg}</p>"
    log_html += "</div>"
    log_container.markdown(log_html, unsafe_allow_html=True)

update_log_display()

# Auto-update log if simulation is running
if st.session_state.run:
    time.sleep(0.1) # Small delay to allow log updates to be visible
    st.rerun()
