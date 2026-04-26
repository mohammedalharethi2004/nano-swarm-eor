import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from scipy.interpolate import interp1d

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Nano-Swarm EOR Pro", layout="wide")

# --- 2. محرك تحميل البيانات (آمن ومصحح) ---
@st.cache_data
def load_and_interpolate():
    try:
        # تحميل البيانات الحقيقية التي وفرتها
        pvto = pd.read_csv("PVTO.xlsx - Sheet1.csv")
        rel_perm = pd.read_csv("Data.xlsx - Water-Oil Relative Permeability.csv")
        
        # تنظيف الأسماء
        pvto.columns = pvto.columns.str.strip().str.lower()
        rel_perm.columns = rel_perm.columns.str.strip().str.lower()
        
        # إنشاء دوال الـ Interpolation
        visc_func = interp1d(pvto['pressure'], pvto['oil viscosity'], kind='linear', fill_value="extrapolate")
        kro_func = interp1d(rel_perm['sw'], rel_perm['kro'], kind='linear', fill_value="extrapolate")
        
        return visc_func, kro_func
    except Exception as e:
        st.error(f"خطأ في تحميل الملفات: {e}")
        st.stop()

# --- 3. كلاس المكمن (يستقبل الدوال كمدخلات لحل مشكلة الـ NameError) ---
class Reservoir:
    def __init__(self, visc_func, kro_func):
        self.visc_func = visc_func
        self.kro_func = kro_func
        # توليد شبكة مكمن وهمية 20x20 لأن الملفات الحقيقية لا تحتوي إحداثيات شبكة
        self.grid = np.random.uniform(0.15, 0.35, (20, 20)) 
        
    def get_darcy_production(self, pressure, sw):
        try:
            mu = max(float(self.visc_func(pressure)), 1e-6)
            kr = float(self.kro_func(sw))
            k = np.mean(self.grid) # استخدام متوسط المسامية
            dp = pressure / 1000
            q = (k * kr * 1 * dp) / mu
            return float(q)
        except: return 0

# --- 4. كلاس السرب ---
class SwarmAgent:
    def __init__(self, size_x, size_y):
        self.x = np.random.randint(0, size_x)
        self.y = np.random.randint(0, size_y)

    def move(self, oil_grid, pheromone_grid):
        score_grid = oil_grid + (pheromone_grid * 0.5)
        padded = np.pad(score_grid, pad_width=1, mode='constant', constant_values=0)
        px, py = self.x + 1, self.y + 1
        local = padded[px-1:px+2, py-1:py+2]
        idx = np.argmax(local)
        self.x = np.clip(self.x + (idx // 3) - 1, 0, oil_grid.shape[0]-1)
        self.y = np.clip(self.y + (idx % 3) - 1, 0, oil_grid.shape[1]-1)

# --- 5. تهيئة البيانات ---
visc_func, kro_func = load_and_interpolate()

# --- 6. الواجهة الرئيسية ---
st.title("🛢️ Nano-Swarm EOR Industrial Prototype")

with st.sidebar:
    st.header("إعدادات التحكم")
    pressure = st.slider("ضغط المكمن (PSI)", 500, 3000, 1500)
    sw = st.slider("تشبع الماء (Sw)", 0.25, 0.8, 0.4)
    if st.button("إعادة تعيين المحاكاة"):
        st.session_state.res = Reservoir(visc_func, kro_func)
        st.session_state.swarm = [SwarmAgent(20, 20) for _ in range(20)]
        st.session_state.ph_grid = np.zeros((20, 20))
        st.rerun()

# تهيئة الـ State
if 'res' not in st.session_state:
    st.session_state.res = Reservoir(visc_func, kro_func)
    st.session_state.swarm = [SwarmAgent(20, 20) for _ in range(20)]
    st.session_state.ph_grid = np.zeros((20, 20))

# --- 7. المحاكاة ---
without_swarm = st.session_state.res.get_darcy_production(pressure, sw)
mu = max(float(visc_func(pressure)), 1e-6)

# حركة السرب
for bot in st.session_state.swarm:
    bot.move(st.session_state.res.grid, st.session_state.ph_grid)
    effect = 0.01 * (1 / mu)
    x, y = bot.x, bot.y
    st.session_state.res.grid[x, y] = max(st.session_state.res.grid[x, y] - effect, 0)
    st.session_state.ph_grid[x, y] += 0.1

st.session_state.ph_grid *= 0.95
with_swarm = st.session_state.res.get_darcy_production(pressure, sw)

# --- 8. النتائج ---
col1, col2, col3 = st.columns(3)
col1.metric("الإنتاج الأساسي", f"{without_swarm:.4f}")
col2.metric("الإنتاج المحسن", f"{with_swarm:.4f}")
improvement = ((with_swarm - without_swarm) / without_swarm * 100) if without_swarm != 0 else 0
col3.metric("نسبة التحسن (KPI)", f"{improvement:.2f}%")

st.plotly_chart(px.imshow(st.session_state.res.grid, title="خريطة المسامية (Porosity Map) - محاكاة السرب"), use_container_width=True)
