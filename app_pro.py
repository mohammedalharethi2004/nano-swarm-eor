import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import interp1d
import time

st.set_page_config(layout="wide", page_title="Nano-Swarm Command Center")

# ================= STYLE =================
st.markdown("""
<style>
.big-title {font-size:40px; font-weight:bold; color:#00f0ff;}
.card {
    background-color:#111;
    padding:15px;
    border-radius:15px;
    text-align:center;
}
</style>
""", unsafe_allow_html=True)

# ================= LOAD DATA =================
@st.cache_data
def load_data():
    pvto = pd.read_excel("PVTO.xlsx")
    rel = pd.read_excel("water-oil Relative permeability.xlsx")

    pvto.columns = pvto.columns.str.strip().str.lower()
    rel.columns = rel.columns.str.strip().str.lower()

    visc = interp1d(pvto['pressure'], pvto['oil viscosity'], fill_value="extrapolate")
    kro = interp1d(rel['sw'], rel['kro'], fill_value="extrapolate")

    return visc, kro

visc_func, kro_func = load_data()

# ================= RESERVOIR =================
class Reservoir:
    def __init__(self):
        self.grid = np.random.rand(20,20)*0.2+0.15
        self.initial = self.grid.copy()

    def production(self, p, sw):
        mu = max(float(visc_func(p)),1e-6)
        kr = float(kro_func(sw))
        k = np.mean(self.grid)
        return (k * kr * p/1000)/mu

# ================= NANO =================
class Nano:
    def __init__(self):
        self.x = np.random.randint(0,20)
        self.y = np.random.randint(0,20)

    def move(self, grid):
        gx, gy = np.gradient(grid)
        self.x = int(np.clip(self.x + gx[self.x,self.y],0,19))
        self.y = int(np.clip(self.y + gy[self.x,self.y],0,19))

# ================= SIDEBAR =================
with st.sidebar:
    st.title("⚙️ Control Panel")

    pressure = st.slider("Pressure",500,3000,1500)
    sw = st.slider("Water Saturation",0.2,0.8,0.4)
    speed = st.slider("Simulation Speed",0.1,1.0,0.3)

    oil_price = st.number_input("Oil Price",50,150,80)
    nano_cost = st.number_input("Nano Cost",1000,100000,20000)

    start = st.button("▶ Start")
    stop = st.button("⏸ Stop")
    reset = st.button("🔄 Reset")

# ================= SESSION =================
if 'res' not in st.session_state:
    st.session_state.res = Reservoir()
    st.session_state.nano = [Nano() for _ in range(30)]
    st.session_state.run = False
    st.session_state.history = []

if start:
    st.session_state.run = True
if stop:
    st.session_state.run = False
if reset:
    st.session_state.res = Reservoir()
    st.session_state.nano = [Nano() for _ in range(30)]
    st.session_state.history = []

res = st.session_state.res

# ================= HEADER =================
st.markdown('<div class="big-title">🛢️ Nano-Swarm Engineering Command</div>', unsafe_allow_html=True)

# ================= KPIs =================
base = res.production(pressure, sw)

c1,c2,c3,c4 = st.columns(4)

with c1:
    st.metric("Active Nano Bots", len(st.session_state.nano))
with c2:
    st.metric("Base Production", f"{base:.3f}")
with c3:
    st.metric("Reservoir Quality", f"{np.mean(res.grid):.3f}")
with c4:
    st.metric("System Status", "ACTIVE" if st.session_state.run else "IDLE")

# ================= MAIN LAYOUT =================
col_left, col_right = st.columns([2,1])

# ===== LEFT: 3D + HEATMAP =====
with col_left:

    chart3d = st.empty()
    heatmap = st.empty()

    for _ in range(50):
        if not st.session_state.run:
            break

        for n in st.session_state.nano:
            n.move(res.grid)
            res.grid[n.x,n.y] *= 1.03

        prod = res.production(pressure, sw)
        st.session_state.history.append(prod)

        fig3d = go.Figure(data=[go.Surface(z=res.grid)])
        chart3d.plotly_chart(fig3d, use_container_width=True, key="3d")

        fig2 = go.Figure(data=go.Heatmap(z=res.grid))
        heatmap.plotly_chart(fig2, use_container_width=True, key="heat")

        time.sleep(speed)

# ===== RIGHT: ANALYTICS =====
with col_right:

    st.subheader("📈 Production Trend")

    fig = go.Figure()
    fig.add_trace(go.Scatter(y=st.session_state.history, mode='lines'))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("💰 Economics")

    enhanced = res.production(pressure, sw)

    revenue = enhanced * oil_price
    profit = revenue - nano_cost
    roi = (profit/nano_cost)*100 if nano_cost!=0 else 0

    st.metric("Revenue", f"${revenue:.2f}")
    st.metric("Profit", f"${profit:.2f}")
    st.metric("ROI", f"{roi:.2f}%")

# ================= COMPARISON =================
st.subheader("🆚 Before vs After")

slider = st.slider("Compare",0.0,1.0,0.5)
combined = (1-slider)*res.initial + slider*res.grid

fig_compare = go.Figure(data=go.Heatmap(z=combined))
st.plotly_chart(fig_compare, use_container_width=True)
