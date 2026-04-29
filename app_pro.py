import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from scipy.interpolate import interp1d
import time

st.set_page_config(layout="wide", page_title="Nano Command Center")

# ------------------ STYLE ------------------
st.markdown("""
<style>
body {
    background-color: #0b0f17;
}
.kpi-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(0,255,255,0.2);
    padding: 15px;
    border-radius: 15px;
    text-align:center;
    box-shadow: 0 0 15px rgba(0,255,255,0.2);
}
</style>
""", unsafe_allow_html=True)

# ------------------ DATA ------------------
@st.cache_data
def load():
    pvto = pd.read_excel("PVTO.xlsx")
    rel = pd.read_excel("water-oil Relative permeability.xlsx")

    pvto.columns = pvto.columns.str.strip().str.lower()
    rel.columns = rel.columns.str.strip().str.lower()

    pvto['pressure'] = pd.to_numeric(pvto['pressure'], errors='coerce')
    pvto['oil viscosity'] = pd.to_numeric(pvto['oil viscosity'], errors='coerce')
    rel['sw'] = pd.to_numeric(rel['sw'], errors='coerce')
    rel['kro'] = pd.to_numeric(rel['kro'], errors='coerce')

    pvto = pvto.dropna().sort_values('pressure')
    rel = rel.dropna().sort_values('sw')

    visc = interp1d(pvto['pressure'], pvto['oil viscosity'], fill_value="extrapolate")
    kro = interp1d(rel['sw'], rel['kro'], fill_value="extrapolate")

    return visc, kro

visc_func, kro_func = load()

# ------------------ MODEL ------------------
class Reservoir:
    def __init__(self):
        self.grid = np.random.rand(25,25)

    def production(self, pressure, sw):
        mu = float(visc_func(pressure))
        kr = float(kro_func(sw))
        k = np.mean(self.grid)
        return (k * kr * pressure/1000) / (mu + 1e-6)

class Nano:
    def __init__(self):
        self.x = np.random.randint(0,25)
        self.y = np.random.randint(0,25)

    def move(self, grid):
        dx, dy = np.random.choice([-1,0,1]), np.random.choice([-1,0,1])
        self.x = np.clip(self.x+dx,0,24)
        self.y = np.clip(self.y+dy,0,24)
        grid[self.x,self.y] *= 0.97

# ------------------ STATE ------------------
if "res" not in st.session_state:
    st.session_state.res = Reservoir()
    st.session_state.nano = [Nano() for _ in range(30)]
    st.session_state.history = []

# ------------------ LAYOUT ------------------
left, mid, right = st.columns([1,2,1])

# ---------- LEFT CONTROL ----------
with left:
    st.header("⚙️ Control")
    pressure = st.slider("Pressure",500,3000,1500)
    sw = st.slider("Water Saturation",0.2,0.8,0.4)
    oil_price = st.number_input("Oil Price",50,150,80)
    cost = st.number_input("Nano Cost",1000,10000,3000)

    run = st.button("▶ Start")
    reset = st.button("🔄 Reset")

# ---------- CORE ----------
with mid:
    st.title("🛢️ Nano-Swarm Command Center")

    base = st.session_state.res.production(pressure, sw)

    if run:
        for n in st.session_state.nano:
            n.move(st.session_state.res.grid)

    nano_prod = st.session_state.res.production(pressure, sw)
    improvement = ((nano_prod-base)/base)*100 if base>0 else 0

    st.session_state.history.append(nano_prod)

    # KPI
    k1,k2,k3 = st.columns(3)
    k1.markdown(f"<div class='kpi-card'>Base<br>{base:.3f}</div>", unsafe_allow_html=True)
    k2.markdown(f"<div class='kpi-card'>Nano<br>{nano_prod:.3f}</div>", unsafe_allow_html=True)
    k3.markdown(f"<div class='kpi-card'>Δ%<br>{improvement:.2f}%</div>", unsafe_allow_html=True)

    # 3D
    fig3d = go.Figure(data=[go.Surface(z=st.session_state.res.grid)])
    fig3d.update_layout(template="plotly_dark", height=300)
    st.plotly_chart(fig3d, use_container_width=True)

    # Heatmap
    fig2 = px.imshow(st.session_state.res.grid, color_continuous_scale="Blues")
    fig2.update_layout(template="plotly_dark")
    st.plotly_chart(fig2, use_container_width=True)

    # Streaming chart
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(y=st.session_state.history, mode='lines'))
    fig_line.update_layout(template="plotly_dark", height=200)
    st.plotly_chart(fig_line, use_container_width=True)

# ---------- RIGHT ----------
with right:
    st.header("📊 Analytics")

    revenue = nano_prod * oil_price
    npv = revenue - cost

    st.metric("Revenue", f"{revenue:.2f}")
    st.metric("NPV", f"{npv:.2f}")

    # Gauge
    gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pressure,
        title={'text': "Pressure"},
        gauge={'axis': {'range': [0,3000]}}
    ))
    gauge.update_layout(template="plotly_dark", height=250)
    st.plotly_chart(gauge)

    # Alerts
    st.subheader("🚨 Alerts")
    if improvement > 5:
        st.success("Production improving")
    else:
        st.warning("Low improvement")

# ---------- STATUS ----------
st.markdown("---")
st.markdown("⚡ System Active | CPU: 32% | Nano Bots: Active")
