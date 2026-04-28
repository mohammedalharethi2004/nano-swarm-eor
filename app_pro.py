import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import interp1d
import time

st.set_page_config(page_title="Nano-Swarm EOR Ultimate", layout="wide")

# ================= تحميل البيانات =================
@st.cache_data
def load_data():
    pvto = pd.read_excel("PVTO.xlsx")
    rel = pd.read_excel("water-oil Relative permeability.xlsx")
    cap = pd.read_excel("capillary pressure.xlsx")

    for df in [pvto, rel, cap]:
        df.columns = df.columns.str.strip().str.lower()

    pvto['pressure'] = pd.to_numeric(pvto['pressure'], errors='coerce')
    pvto['oil viscosity'] = pd.to_numeric(pvto['oil viscosity'], errors='coerce')

    rel['sw'] = pd.to_numeric(rel['sw'], errors='coerce')
    rel['kro'] = pd.to_numeric(rel['kro'], errors='coerce')

    cap['sw'] = pd.to_numeric(cap['sw'], errors='coerce')
    cap['pcow (psi)'] = pd.to_numeric(cap['pcow (psi)'], errors='coerce')

    pvto.dropna(inplace=True)
    rel.dropna(inplace=True)
    cap.dropna(inplace=True)

    visc = interp1d(pvto['pressure'], pvto['oil viscosity'], fill_value="extrapolate")
    kro = interp1d(rel['sw'], rel['kro'], fill_value="extrapolate")
    pcow = interp1d(cap['sw'], cap['pcow (psi)'], fill_value="extrapolate")

    return visc, kro, pcow

visc_func, kro_func, pcow_func = load_data()

# ================= المكمن =================
class Reservoir:
    def __init__(self):
        self.grid = np.random.rand(20,20)*0.25+0.15
        self.initial = self.grid.copy()

    def production(self, p, sw):
        mu = max(float(visc_func(p)),1e-6)
        kr = float(kro_func(sw))
        pc = float(pcow_func(sw))
        k = np.mean(self.grid)
        return (k*kr*((p-pc)/1000))/mu

# ================= النانو =================
class Nano:
    def __init__(self):
        self.x = np.random.randint(0,20)
        self.y = np.random.randint(0,20)
        self.visits = 0

    def move(self, grid, pher):
        score = grid + pher*0.7
        i,j = np.unravel_index(np.argmax(score), score.shape)
        self.x,self.y = i,j
        self.visits += 1

# ================= UI =================
st.title("🛢️ Nano-Swarm EOR Industrial Ultimate Dashboard")

# Sidebar
with st.sidebar:
    st.header("⚙️ التحكم")

    pressure = st.slider("Pressure (psi)",500,3000,1500)
    sw = st.slider("Water Saturation",0.25,0.8,0.4)
    speed = st.slider("Simulation Speed",0.1,1.0,0.3)
    nano_count = st.slider("Nano Bots",5,50,20)

    start = st.button("▶️ Inject Nano")
    stop = st.button("⏸ Stop")
    reset = st.button("🔄 Reset")

# ================= Session =================
if 'res' not in st.session_state:
    st.session_state.res = Reservoir()
    st.session_state.nano = [Nano() for _ in range(20)]
    st.session_state.pher = np.zeros((20,20))
    st.session_state.run = False
    st.session_state.history = []

if start:
    st.session_state.run = True

if stop:
    st.session_state.run = False

if reset:
    st.session_state.res = Reservoir()
    st.session_state.nano = [Nano() for _ in range(nano_count)]
    st.session_state.pher = np.zeros((20,20))
    st.session_state.history = []

res = st.session_state.res
pher = st.session_state.pher

# ================= الإنتاج =================
base_prod = res.production(pressure, sw)

chart = st.empty()
graph = st.empty()

# ================= المحاكاة =================
for _ in range(40):
    if not st.session_state.run:
        break

    for bot in st.session_state.nano:
        bot.move(res.grid, pher)

        # تأثير شبه واقعي
        res.grid[bot.x, bot.y] *= 1.03  # زيادة permeability
        pher[bot.x, bot.y] += 0.2

    pher *= 0.95

    prod = res.production(pressure, sw)
    st.session_state.history.append(prod)

    # ===== خريطة =====
    fig = go.Figure(data=go.Heatmap(z=res.grid))

    xs = [n.x for n in st.session_state.nano]
    ys = [n.y for n in st.session_state.nano]

    fig.add_trace(go.Scatter(
        x=ys,y=xs,
        mode='markers',
        marker=dict(color='red',size=7),
        name="Nano Bots"
    ))

    chart.plotly_chart(fig,use_container_width=True)

    # ===== رسم الإنتاج =====
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(y=st.session_state.history,name="Production"))

    graph.plotly_chart(fig2,use_container_width=True)

    time.sleep(speed)

# ================= النتائج =================
enhanced = res.production(pressure, sw)
improve = ((enhanced-base_prod)/base_prod*100) if base_prod!=0 else 0

c1,c2,c3 = st.columns(3)
c1.metric("Base Production",f"{base_prod:.4f}")
c2.metric("Nano Production",f"{enhanced:.4f}")
c3.metric("Improvement %",f"{improve:.2f}%")

# ================= التحليل =================
st.subheader("🧠 Reservoir Insights")

active = np.sum(res.grid > np.mean(res.initial))
avg = np.mean(res.grid)
maxv = np.max(res.grid)

a,b,c = st.columns(3)
a.metric("Active Cells",active)
b.metric("Avg Porosity",f"{avg:.3f}")
c.metric("Max Zone",f"{maxv:.3f}")

# ================= مقارنة =================
st.subheader("📊 Before vs After")

col1,col2 = st.columns(2)

with col1:
    st.write("Before")
    st.plotly_chart(go.Figure(data=go.Heatmap(z=res.initial)))

with col2:
    st.write("After")
    st.plotly_chart(go.Figure(data=go.Heatmap(z=res.grid)))

# ================= مواقع النانو =================
st.subheader("📍 Nano Tracking")

positions = [(n.x,n.y,n.visits) for n in st.session_state.nano]
df = pd.DataFrame(positions,columns=["X","Y","Visits"])
st.dataframe(df)
