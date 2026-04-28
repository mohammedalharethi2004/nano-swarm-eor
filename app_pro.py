import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from scipy.interpolate import interp1d

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Nano-Swarm EOR Pro", page_icon="🛢️", layout="wide")

# --- 2. محرك تحميل البيانات (Data Engineering Pipeline) ---
@st.cache_data
def load_and_prepare_data():
    """تحميل وتنظيف ملفات الإكسل مع ضمان الجودة"""
    try:
        pvto = pd.read_excel("PVTO.xlsx")
        w_oil = pd.read_excel("water-oil Relative permeability.xlsx")
        cap = pd.read_excel("capillary pressure.xlsx")
        pro = pd.read_excel("Pro.xlsx", skiprows=8)
        
        # تنظيف العناوين
        for df in [pvto, w_oil, cap, pro]:
            df.columns = df.columns.str.strip().str.lower()
            
        return pvto, w_oil, cap, pro
    except Exception as e:
        st.error(f"خطأ في تحميل ملفات البيانات: {e}")
        return None, None, None, None

# --- 3. المنطق الرياضي (Physics Engine) ---
class Reservoir:
    def __init__(self, size=20):
        self.size = size
        self.grid = np.random.rand(size, size) * 0.5 
        
    def calculate_flow(self, pressure, sw, visc_f, kro_f, pc_f):
        mu = max(float(visc_f(pressure)), 1e-6)
        kr = float(kro_f(sw))
        pc = float(pc_f(sw))
        k = np.mean(self.grid)
        flow = (k * kr * ((pressure - pc)/1000)) / mu
        return flow

class SwarmAgent:
    def __init__(self, size):
        self.x = np.random.randint(0, size)
        self.y = np.random.randint(0, size)

    def update_position(self, oil_grid, pheromone_grid):
        # منطق تحرك السرب
        score = oil_grid + (pheromone_grid * 0.5)
        # (هنا يمكن إضافة خوارزمية البحث المتقدمة الخاصة بك)
        self.x = np.clip(self.x + np.random.randint(-1, 2), 0, oil_grid.shape[0]-1)
        self.y = np.clip(self.y + np.random.randint(-1, 2), 0, oil_grid.shape[1]-1)

# --- 4. واجهة المستخدم (GUI) ---
st.title("🛢️ Nano-Swarm EOR Industrial Prototype")
st.markdown("---")

# تحميل البيانات
pvto, w_oil, cap, pro = load_and_prepare_data()

if pvto is not None:
    # إنشاء دوال الاستكمال (Interpolation)
    visc_func = interp1d(pvto['pressure'], pvto['oil viscosity'], kind='linear', fill_value="extrapolate")
    kro_func = interp1d(w_oil['sw'], w_oil['kro'], kind='linear', fill_value="extrapolate")
    pcow_func = interp1d(cap['sw'], cap['pcow (psi)'], kind='linear', fill_value="extrapolate")

    # Sidebar للتحكم
    st.sidebar.header("⚙️ معايير المحاكاة")
    p_input = st.sidebar.slider("ضغط المكمن (PSI)", 500, 3000, 1500)
    sw_input = st.sidebar.slider("تشبع الماء (Sw)", 0.25, 0.8, 0.4)
    iterations = st.sidebar.number_input("عدد تكرارات السرب", 10, 100, 50)

    # تهيئة الكائنات
    if 'res' not in st.session_state:
        st.session_state.res = Reservoir()
        st.session_state.swarm = [SwarmAgent(20) for _ in range(10)]

    # تنفيذ الحسابات
    res = st.session_state.res
    production = res.calculate_flow(p_input, sw_input, visc_func, kro_func, pcow_func)

    # عرض النتائج في واجهة منظمة
    col1, col2, col3 = st.columns(3)
    col1.metric("معدل الإنتاج الحالي", f"{production:.4f} STB/D")
    col2.metric("حالة المكمن", "مستقر")
    col3.metric("عدد الوكلاء", len(st.session_state.swarm))

    # الرسوم البيانية
    tab1, tab2 = st.tabs(["خريطة المكمن", "تحليل البيانات"])
    
    with tab1:
        fig = px.imshow(res.grid, color_continuous_scale='Viridis', title="توزيع الطور في المكمن")
        st.plotly_chart(fig, use_container_width=True)
        
    with tab2:
        st.write("ملخص بيانات الإنتاج (Pro.xlsx):")
        st.dataframe(pro.head(10))

else:
    st.warning("⚠️ يرجى التأكد من وجود ملفات الإكسل في المجلد!")

# --- 5. تذييل الصفحة ---
st.markdown("---")
st.caption("تم التطوير بواسطة: مهندس الميكاترونيكس - نظام المحاكاة المتطور للسرب النانوي")
