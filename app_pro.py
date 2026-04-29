import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import interp1d
import time

st.set_page_config(layout="wide", page_title="Nano-Swarm Command Center")

# ================== تحميل البيانات (مُصحّح) ==================
@st.cache_data
def load_data():
    try:
        pvto = pd.read_excel("PVTO.xlsx")
        rel = pd.read_excel("water-oil Relative permeability.xlsx")

        # تنظيف أسماء الأعمدة
        pvto.columns = pvto.columns.str.strip().str.lower()
        rel.columns = rel.columns.str.strip().str.lower()

        # تحويل إلى أرقام
        pvto['pressure'] = pd.to_numeric(pvto['pressure'], errors='coerce')
        pvto['oil viscosity'] = pd.to_numeric(pvto['oil viscosity'], errors='coerce')

        rel['sw'] = pd.to_numeric(rel['sw'], errors='coerce')
        rel['kro'] = pd.to_numeric(rel['kro'], errors='coerce')

        # حذف القيم الفارغة
        pvto.dropna(subset=['pressure', 'oil viscosity'], inplace=True)
        rel.dropna(subset=['sw', 'kro'], inplace=True)

        # ترتيب
        pvto.sort_values('pressure', inplace=True)
        rel.sort_values('sw', inplace=True)

        # إزالة التكرار
        pvto.drop_duplicates(subset=['pressure'], inplace=True)
        rel.drop_duplicates(subset=['sw'], inplace=True)

        visc = interp1d(pvto['pressure'], pvto['oil viscosity'], fill_value="extrapolate")
        kro = interp1d(rel['sw'], rel['kro'], fill_value="extrapolate")

        return visc, kro

    except Exception as e:
        st.error(f"خطأ في البيانات: {e}")
        return None, None

visc_func, kro_func = load_data()

# ================== المكمن ==================
class Reservoir:
    def __init__(self):
        self.grid = np.random.rand(20,20)*0.2+0.15
        self.initial = self.grid.copy()

    def production(self, p, sw):
        if visc_func is None:
            return 0
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
    st.title("⚙️ Control Panel")

    pressure = st.slider("Pressure",500,3000,1500)
    sw = st.slider("Water Saturation",0.2,0.8,0.4)
    speed = st.slider("Speed",0.1,1.0,0.3)

    oil_price = st.number_input("Oil Price ($)",50,150,80)
    nano_cost = st.number_input("Nano Cost ($)",1000,100000,20000)

    start = st.button("▶ Start")
    stop = st.button("⏸ Stop")
    reset = st.button("🔄 Reset")

# ================== Session ==================
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

# ================== Header ==================
st.title("🛢️ Nano-Swarm Engineering Command Center")

# ================== KPIs ==================
base = res.production(pressure, sw)

c1,c2,c3,c4 = st.columns(4)
c1.metric("Nano Bots", len(st.session_state.nano))
c2.metric("Base Production", f"{base:.3f}")
c3.metric("Reservoir Quality", f"{np.mean(res.grid):.3f}")
c4.metric("Status", "ACTIVE" if st.session_state.run else "IDLE")

# ================== Layout ==================
col_left, col_right = st.columns([2,1])

# ===== Simulation =====
with col_left:
    chart3d = st.empty()
    heatmap = st.empty()

    for _ in range(40):
        if not st.session_state.run:
            break

        for n in st.session_state.nano:
            n.move(res.grid)
            res.grid[n.x,n.y] *= 1.03

        prod = res.production(pressure, sw)
        st.session_state.history.append(prod)

        fig3d = go.Figure(data=[go.Surface(z=res.grid)])
        chart3d.plotly_chart(fig3d, use_container_width=True, key="3d_unique")

        fig2 = go.Figure(data=go.Heatmap(z=res.grid))
        heatmap.plotly_chart(fig2, use_container_width=True, key="heat_unique")

        time.sleep(speed)

# ===== Analytics =====
with col_right:
    st.subheader("📈 Production Trend")

    fig = go.Figure()
    fig.add_trace(go.Scatter(y=st.session_state.history))
    st.plotly_chart(fig, use_container_width=True, key="trend_unique")

    st.subheader("💰 Economics")

    enhanced = res.production(pressure, sw)

    revenue = enhanced * oil_price
    profit = revenue - nano_cost
    roi = (profit/nano_cost)*100 if nano_cost!=0 else 0

    st.metric("Revenue", f"${revenue:.2f}")
    st.metric("Profit", f"${profit:.2f}")
    st.metric("ROI", f"{roi:.2f}%")

# ================== Comparison ==================
st.subheader("🆚 Before vs After")

slider = st.slider("Compare",0.0,1.0,0.5)
combined = (1-slider)*res.initial + slider*res.grid

fig_compare = go.Figure(data=go.Heatmap(z=combined))
st.plotly_chart(fig_compare, use_container_width=True, key="compare_unique")
