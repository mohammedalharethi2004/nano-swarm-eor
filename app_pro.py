import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from scipy.interpolate import interp1d

st.set_page_config(page_title="Nano-Swarm EOR Pro", layout="wide")

st.title("🛢️ Nano-Swarm EOR Industrial Prototype")

# --- 1. رفع الملفات يدوياً (الحل المضمون) ---
st.sidebar.header("📥 ارفع ملفات البيانات")
pvto_file = st.sidebar.file_uploader("ارفع ملف PVTO.xlsx - Sheet1.csv", type=['csv'])
wo_rel_file = st.sidebar.file_uploader("ارفع ملف Water-Oil Permeability", type=['csv'])
por_file = st.sidebar.file_uploader("ارفع ملف Pro.xlsx - Por.csv", type=['csv'])

# --- 2. محرك تحميل البيانات الذكي ---
@st.cache_data
def process_data(pvto_f, wo_f):
    pvto = pd.read_csv(pvto_f)
    wo_rel = pd.read_csv(wo_f)
    pvto.columns = pvto.columns.str.strip().str.lower()
    wo_rel.columns = wo_rel.columns.str.strip().str.lower()
    
    visc_func = interp1d(pvto['pressure'], pvto['oil viscosity'], kind='linear', fill_value="extrapolate")
    kro_func = interp1d(wo_rel['sw'], wo_rel['kro'], kind='linear', fill_value="extrapolate")
    return visc_func, kro_func

# --- 3. الكلاسات ---
class Reservoir:
    def __init__(self, visc_func, kro_func):
        self.visc_func = visc_func
        self.kro_func = kro_func
        self.grid = np.random.uniform(0.15, 0.35, (20, 20)) 
        
    def get_darcy_production(self, pressure, sw):
        mu = max(float(self.visc_func(pressure)), 1e-6)
        kr = float(self.kro_func(sw))
        return (np.mean(self.grid) * kr * pressure) / mu

# --- 4. منطق التشغيل ---
if pvto_file and wo_rel_file:
    visc_func, kro_func = process_data(pvto_file, wo_rel_file)
    
    if 'res' not in st.session_state:
        st.session_state.res = Reservoir(visc_func, kro_func)
    
    # تحكم الواجهة
    pressure = st.sidebar.slider("ضغط المكمن (PSI)", 500, 3000, 1500)
    sw = st.sidebar.slider("تشبع الماء (Sw)", 0.25, 0.8, 0.4)
    
    prod = st.session_state.res.get_darcy_production(pressure, sw)
    st.metric("الإنتاج المحسوب", f"{prod:.4f}")
    
    if por_file:
        prod_data = pd.read_csv(por_file)
        st.write("بيانات الإنتاج:", prod_data.head())
        st.line_chart(prod_data.head(50))
else:
    st.info("⚠️ يرجى رفع الملفات من القائمة الجانبية لبدء المحاكاة.")
