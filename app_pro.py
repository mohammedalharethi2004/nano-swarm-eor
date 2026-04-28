import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from scipy.interpolate import interp1d

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Nano-Swarm EOR Advanced Pro", page_icon="🛢️", layout="wide")

# --- 2. محرك تحميل البيانات (النسخة الصارمة ضد الأخطاء) ---
@st.cache_data
def load_and_clean_data():
    try:
        pvto = pd.read_excel("PVTO.xlsx")
        w_oil = pd.read_excel("water-oil Relative permeability.xlsx")
        cap = pd.read_excel("capillary pressure.xlsx")
        pro = pd.read_excel("Pro.xlsx", skiprows=8)

        for df in [pvto, w_oil, cap, pro]:
            df.columns = df.columns.str.strip().str.lower()

        # تنظيف صارم
        pvto['pressure'] = pd.to_numeric(pvto['pressure'], errors='coerce')
        pvto['oil viscosity'] = pd.to_numeric(pvto['oil viscosity'], errors='coerce')
        w_oil['sw'] = pd.to_numeric(w_oil['sw'], errors='coerce')
        w_oil['kro'] = pd.to_numeric(w_oil['kro'], errors='coerce')
        cap['sw'] = pd.to_numeric(cap['sw'], errors='coerce')
        cap['pcow (psi)'] = pd.to_numeric(cap['pcow (psi)'], errors='coerce')

        pvto.dropna(inplace=True); w_oil.dropna(inplace=True); cap.dropna(inplace=True)
        pvto.sort_values('pressure', inplace=True); w_oil.sort_values('sw', inplace=True); cap.sort_values('sw', inplace=True)

        return interp1d(pvto['pressure'], pvto['oil viscosity'], kind='linear', fill_value="extrapolate"), \
               interp1d(w_oil['sw'], w_oil['kro'], kind='linear', fill_value="extrapolate"), \
               interp1d(cap['sw'], cap['pcow (psi)'], kind='linear', fill_value="extrapolate"), pro
    except Exception as e:
        st.error(f"خطأ في تحميل البيانات: {e}")
        return None, None, None, None

# --- 3. كلاسات المحاكاة (Engine) ---
class Reservoir:
    def __init__(self, size=20):
        self.size = size
        self.grid = np.random.rand(size, size) * 0.5 
    
    def get_flow(self, pressure, sw, visc_func, kro_func, pcow_func):
        mu = max(float(visc_func(pressure)), 1e-6)
        kr = float(kro_func(sw))
        pc = float(pcow_func(sw))
        return (np.mean(self.grid) * kr * ((pressure - pc)/1000)) / mu

class SwarmAgent:
    def __init__(self, size):
        self.x, self.y = np.random.randint(0, size), np.random.randint(0, size)

    def move(self, grid, pheromones):
        # منطق الحركة المعتمد على البيئة
        self.x = np.clip(self.x + np.random.randint(-1, 2), 0, grid.shape[0]-1)
        self.y = np.clip(self.y + np.random.randint(-1, 2), 0, grid.shape[1]-1)

# --- 4. واجهة المستخدم المتكاملة ---
st.title("🛢️ Nano-Swarm EOR: Advanced Simulation")

visc, kro, pcow, pro_data = load_and_clean_data()

if visc is not None:
    # Sidebar - لوحة التحكم
    st.sidebar.header("⚙️ Control Panel")
    n_agents = st.sidebar.slider("عدد وكلاء السرب (Agents)", 10, 100, 50)
    p_init = st.sidebar.slider("ضغط المكمن (PSI)", 500, 3000, 1500)
    sw_init = st.sidebar.slider("تشبع الماء (Sw)", 0.25, 0.8, 0.4)
    
    # تهيئة الـ State
    if 'res' not in st.session_state:
        st.session_state.res = Reservoir()
        st.session_state.swarm = [SwarmAgent(20) for _ in range(n_agents)]
        st.session_state.ph = np.zeros((20, 20))

    # العمليات
    prod = st.session_state.res.get_flow(p_init, sw_init, visc, kro, pcow)
    
    # العرض (Dashboard)
    c1, c2, c3 = st.columns(3)
    c1.metric("الإنتاج (STB/D)", f"{prod:.4f}")
    c2.metric("عدد الوكلاء", n_agents)
    c3.metric("حالة المكمن", "Active")

    tab1, tab2 = st.tabs(["خريطة المحاكاة (Swarm)", "بيانات المكمن (Data)"])
    
    with tab1:
        # تحديث السرب
        for agent in st.session_state.swarm:
            agent.move(st.session_state.res.grid, st.session_state.ph)
        
        fig = px.imshow(st.session_state.res.grid, color_continuous_scale='RdBu_r')
        st.plotly_chart(fig, use_container_width=True)
        
    with tab2:
        st.write("ملخص بيانات الإنتاج المحملة:")
        st.dataframe(pro_data.head())
        
else:
    st.error("فشل تحميل البيانات. تأكد من مسارات الملفات!")
