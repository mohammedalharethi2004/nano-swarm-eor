import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from scipy.interpolate import interp1d

st.set_page_config(page_title="Nano-Swarm EOR Pro", page_icon="🛢️", layout="wide")

# --- تحميل البيانات ---
@st.cache_data
def load_and_clean_data():
    try:
        pvto = pd.read_excel("PVTO.xlsx")
        w_oil = pd.read_excel("water-oil Relative permeability.xlsx")
        cap = pd.read_excel("capillary pressure.xlsx")
        pro = pd.read_excel("Pro.xlsx", skiprows=8)

        for df in [pvto, w_oil, cap, pro]:
            df.columns = df.columns.str.strip().str.lower()

        pvto['pressure'] = pd.to_numeric(pvto['pressure'], errors='coerce')
        pvto['oil viscosity'] = pd.to_numeric(pvto['oil viscosity'], errors='coerce')

        w_oil['sw'] = pd.to_numeric(w_oil['sw'], errors='coerce')
        w_oil['kro'] = pd.to_numeric(w_oil['kro'], errors='coerce')

        cap['sw'] = pd.to_numeric(cap['sw'], errors='coerce')
        cap['pcow (psi)'] = pd.to_numeric(cap['pcow (psi)'], errors='coerce')

        pvto.dropna(inplace=True)
        w_oil.dropna(inplace=True)
        cap.dropna(inplace=True)

        pvto.sort_values('pressure', inplace=True)
        w_oil.sort_values('sw', inplace=True)
        cap.sort_values('sw', inplace=True)

        visc_func = interp1d(pvto['pressure'], pvto['oil viscosity'], fill_value="extrapolate")
        kro_func = interp1d(w_oil['sw'], w_oil['kro'], fill_value="extrapolate")
        pcow_func = interp1d(cap['sw'], cap['pcow (psi)'], fill_value="extrapolate")

        return visc_func, kro_func, pcow_func
    
    except Exception as e:
        st.error(f"خطأ في البيانات: {e}")
        return None, None, None

visc_func, kro_func, pcow_func = load_and_clean_data()

# --- المكمن ---
class Reservoir:
    def __init__(self):
        self.grid = np.random.rand(20, 20) * 0.3 + 0.1

    def production(self, pressure, sw):
        mu = max(float(visc_func(pressure)), 1e-6)
        kr = float(kro_func(sw))
        pc = float(pcow_func(sw))
        k = np.mean(self.grid)
        return (k * kr * ((pressure - pc)/1000)) / mu

# --- النانو ---
class Nano:
    def __init__(self, size):
        self.x = np.random.randint(0, size)
        self.y = np.random.randint(0, size)

    def move(self, grid, pher):
        score = grid + pher * 0.6
        i, j = np.unravel_index(np.argmax(score), score.shape)
        self.x, self.y = i, j

# --- UI ---
st.title("🛢️ Nano-Swarm EOR Industrial Dashboard")

if visc_func is None:
    st.stop()

# Sidebar
with st.sidebar:
    st.header("⚙️ التحكم")
    pressure = st.slider("Pressure", 500, 3000, 1500)
    sw = st.slider("Water Saturation", 0.25, 0.8, 0.4)
    mode = st.radio("Mode", ["Auto", "Manual"])
    nano_count = st.slider("عدد النانو", 5, 50, 20)

    start = st.button("▶️ Inject Nano")
    stop = st.button("⏸ Stop")
    reset = st.button("🔄 Reset")

# session
if 'res' not in st.session_state:
    st.session_state.res = Reservoir()
    st.session_state.nano = [Nano(20) for _ in range(20)]
    st.session_state.pher = np.zeros((20,20))
    st.session_state.running = False

if start:
    st.session_state.running = True

if stop:
    st.session_state.running = False

if reset:
    st.session_state.res = Reservoir()
    st.session_state.nano = [Nano(20) for _ in range(nano_count)]
    st.session_state.pher = np.zeros((20,20))

res = st.session_state.res
pher = st.session_state.pher

# الإنتاج الأساسي
base_prod = res.production(pressure, sw)

# تشغيل النانو
if st.session_state.running:
    for bot in st.session_state.nano:
        bot.move(res.grid, pher)

        # تأثير النانو
        res.grid[bot.x, bot.y] = max(res.grid[bot.x, bot.y] - 0.01, 0)
        pher[bot.x, bot.y] += 0.2

    pher *= 0.95

enhanced_prod = res.production(pressure, sw)

# عرض النتائج
col1, col2, col3 = st.columns(3)

col1.metric("Base Production", f"{base_prod:.4f}")
col2.metric("Nano Production", f"{enhanced_prod:.4f}")

improve = ((enhanced_prod - base_prod)/base_prod*100) if base_prod != 0 else 0
col3.metric("Improvement %", f"{improve:.2f}%")

# الخريطة
fig = px.imshow(res.grid, title="Reservoir + Nano Activity")
st.plotly_chart(fig, use_container_width=True)
