import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import interp1d
import time

st.set_page_config(layout="wide", page_title="Nano-Swarm EOR ULTIMATE")

# ================== تحميل البيانات ==================
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

# ================== المكمن ==================
class Reservoir:
    def __init__(self):
        self.grid = np.random.rand(20,20)*0.2+0.15
        self.initial = self.grid.copy()

    def production(self, p, sw):
        mu = max(float(visc_func(p)),1e-6)
        kr = float(kro_func(sw))
        k = np.mean(self.grid)
        return (k * kr * p/1000)/mu

# ================== النانو ==================
class Nano:
    def __init__(self):
        self.x = np.random.randint(0,20)
        self.y = np.random.randint(0,20)

    def move(self, grid):
        gx, gy = np.gradient(grid)
        self.x = int(np.clip(self.x + gx[self.x,self.y],0,19))
        self.y = int(np.clip(self.y + gy[self.x,self.y],0,19))

# ================== Sidebar ==================
with st.sidebar:
    st.header("⚙️ التحكم")

    pressure = st.slider("Pressure",500,3000,1500)
    sw = st.slider("Water Saturation",0.2,0.8,0.4)
    speed = st.slider("Speed",0.1,1.0,0.3)

    oil_price = st.number_input("Oil Price ($)",50,150,80)
    nano_cost = st.number_input("Nano Cost ($)",1000,100000,20000)

    years = st.slider("Project Years",1,10,5)
    discount = st.slider("Discount Rate %",1,20,10)/100

    start = st.button("▶️ Start")
    stop = st.button("⏸ Stop")
    reset = st.button("🔄 Reset")

# ================== Session ==================
if 'res' not in st.session_state:
    st.session_state.res = Reservoir()
    st.session_state.nano = [Nano() for _ in range(20)]
    st.session_state.run = False
    st.session_state.history = []

if start:
    st.session_state.run = True
if stop:
    st.session_state.run = False
if reset:
    st.session_state.res = Reservoir()
    st.session_state.nano = [Nano() for _ in range(20)]
    st.session_state.history = []

res = st.session_state.res

# ================== Tabs ==================
tab1, tab2, tab3 = st.tabs(["🛢️ Simulation", "📊 Comparison", "💰 Economics"])

# ================== Simulation ==================
with tab1:
    st.subheader("Live Nano Simulation")

    base = res.production(pressure, sw)

    chart = st.empty()
    graph = st.empty()

    for _ in range(40):
        if not st.session_state.run:
            break

        for n in st.session_state.nano:
            n.move(res.grid)
            res.grid[n.x,n.y] *= 1.02

        prod = res.production(pressure, sw)
        st.session_state.history.append(prod)

        fig = go.Figure(data=[go.Surface(z=res.grid)])
        chart.plotly_chart(fig, use_container_width=True, key="live3d")

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(y=st.session_state.history))
        graph.plotly_chart(fig2, use_container_width=True, key="prod_chart")

        time.sleep(speed)

    enhanced = res.production(pressure, sw)

    c1,c2,c3 = st.columns(3)
    c1.metric("Base",f"{base:.3f}")
    c2.metric("Enhanced",f"{enhanced:.3f}")
    c3.metric("Improvement %",f"{(enhanced-base)/base*100:.2f}%")

# ================== Comparison ==================
with tab2:
    st.subheader("Interactive Comparison")

    slider = st.slider("Compare Before/After",0.0,1.0,0.5)

    combined = (1-slider)*res.initial + slider*res.grid

    fig = go.Figure(data=go.Heatmap(z=combined))
    st.plotly_chart(fig, use_container_width=True)

# ================== Economics ==================
with tab3:
    st.subheader("Economic Analysis")

    prod = res.production(pressure, sw)
    revenue = prod * oil_price
    profit = revenue - nano_cost

    # NPV حقيقي
    cashflows = []
    for year in range(1, years+1):
        discounted = profit / ((1+discount)**year)
        cashflows.append(discounted)

    npv = sum(cashflows)
    roi = (profit/nano_cost)*100 if nano_cost!=0 else 0

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Revenue",f"${revenue:.2f}")
    c2.metric("Profit",f"${profit:.2f}")
    c3.metric("ROI %",f"{roi:.2f}%")
    c4.metric("NPV",f"${npv:.2f}")

    df = pd.DataFrame({
        "Revenue":[revenue],
        "Profit":[profit],
        "NPV":[npv]
    })

    st.download_button("📥 Download Report", df.to_csv(), "report.csv")
