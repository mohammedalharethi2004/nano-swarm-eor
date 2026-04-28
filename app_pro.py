import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from scipy.interpolate import interp1d

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Nano-Swarm EOR Pro", page_icon="🛢️", layout="wide")

# --- 2. محرك تحميل وتجهيز البيانات (Engine) ---
@st.cache_data
def load_and_clean_data():
    try:
        # قراءة الملفات
        pvto = pd.read_excel("PVTO.xlsx")
        w_oil = pd.read_excel("water-oil Relative permeability.xlsx")
        cap = pd.read_excel("capillary pressure.xlsx")
        pro = pd.read_excel("Pro.xlsx", skiprows=8)

        # توحيد أسماء الأعمدة (إزالة المسافات وتحويلها لأحرف صغيرة)
        for df in [pvto, w_oil, cap, pro]:
            df.columns = df.columns.str.strip().str.lower()

        # تنظيف البيانات (الخطوة التي تمنع ظهور خطأ argsort)
        # 1. تحويل كل شيء لأرقام
        pvto['pressure'] = pd.to_numeric(pvto['pressure'], errors='coerce')
        pvto['oil viscosity'] = pd.to_numeric(pvto['oil viscosity'], errors='coerce')
        
        w_oil['sw'] = pd.to_numeric(w_oil['sw'], errors='coerce')
        w_oil['kro'] = pd.to_numeric(w_oil['kro'], errors='coerce')
        
        cap['sw'] = pd.to_numeric(cap['sw'], errors='coerce')
        cap['pcow (psi)'] = pd.to_numeric(cap['pcow (psi)'], errors='coerce')

        # 2. حذف الصفوف الفارغة (NaN)
        pvto.dropna(subset=['pressure', 'oil viscosity'], inplace=True)
        w_oil.dropna(subset=['sw', 'kro'], inplace=True)
        cap.dropna(subset=['sw', 'pcow (psi)'], inplace=True)

        # 3. ترتيب البيانات تصاعدياً (شرط أساسي لـ interp1d)
        pvto.sort_values('pressure', inplace=True)
        w_oil.sort_values('sw', inplace=True)
        cap.sort_values('sw', inplace=True)

        # بناء دوال الاستكمال الرياضي
        visc_func = interp1d(pvto['pressure'], pvto['oil viscosity'], kind='linear', fill_value="extrapolate")
        kro_func = interp1d(w_oil['sw'], w_oil['kro'], kind='linear', fill_value="extrapolate")
        pcow_func = interp1d(cap['sw'], cap['pcow (psi)'], kind='linear', fill_value="extrapolate")
        
        return visc_func, kro_func, pcow_func, pro
    
    except Exception as e:
        st.error(f"خطأ في معالجة البيانات: {e}")
        return None, None, None, None

# --- تحميل البيانات ---
visc_func, kro_func, pcow_func, pro_data = load_and_clean_data()

# --- 3. كلاسات المحاكاة ---
class Reservoir:
    def __init__(self):
        self.grid = np.random.rand(20, 20) * 0.5 
        
    def get_production(self, pressure, sw):
        if visc_func is None: return 0
        mu = max(float(visc_func(pressure)), 1e-6)
        kr = float(kro_func(sw))
        pc = float(pcow_func(sw))
        k = np.mean(self.grid)
        return (k * kr * ((pressure - pc)/1000)) / mu

# --- 4. الواجهة (UI) ---
st.title("🛢️ Nano-Swarm EOR Industrial Prototype")

if visc_func is not None:
    col1, col2 = st.columns(2)
    pressure = col1.slider("ضغط المكمن (PSI)", 500, 3000, 1500)
    sw = col2.slider("تشبع الماء (Sw)", 0.25, 0.8, 0.4)

    res = Reservoir()
    prod = res.get_production(pressure, sw)
    
    st.metric("معدل الإنتاج المحسوب", f"{prod:.4f} STB/Day")
    
    fig = px.imshow(res.grid, title="خريطة توزيع الضغط في المكمن")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("جاري التحميل أو بانتظار تحديث الملفات...")
