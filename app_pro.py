import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from scipy.interpolate import interp1d

st.set_page_config(page_title="Nano-Swarm EOR Pro", layout="wide")
st.title("🛢️ Nano-Swarm EOR Industrial Prototype")

# --- 1. القائمة الجانبية لرفع الملفات (هذا الحل يغنيك عن وضع الملفات في مجلدات السيرفر) ---
st.sidebar.header("📥 ارفع ملفات البيانات")
pvto_file = st.sidebar.file_uploader("ارفع ملف PVTO (Sheet1.csv)", type=['csv'])
wo_rel_file = st.sidebar.file_uploader("ارفع ملف Water-Oil Rel Perm", type=['csv'])
prod_file = st.sidebar.file_uploader("ارفع ملف الإنتاج (Pro.xlsx - Por.csv)", type=['csv'])

# --- 2. معالجة البيانات (تعمل فقط عند رفع الملفات) ---
@st.cache_data
def process_data(pvto_f, wo_f):
    pvto = pd.read_csv(pvto_f)
    wo_rel = pd.read_csv(wo_f)
    # تنظيف الأسماء
    pvto.columns = pvto.columns.str.strip().str.lower()
    wo_rel.columns = wo_rel.columns.str.strip().str.lower()
    
    # دوال التحويل
    visc_func = interp1d(pvto['pressure'], pvto['oil viscosity'], kind='linear', fill_value="extrapolate")
    kro_func = interp1d(wo_rel['sw'], wo_rel['kro'], kind='linear', fill_value="extrapolate")
    return visc_func, kro_func

# --- 3. المنطق الأساسي ---
if pvto_file and wo_rel_file:
    visc_func, kro_func = process_data(pvto_file, wo_rel_file)
    
    # تحكم الواجهة
    col1, col2 = st.columns(2)
    with col1:
        pressure = st.slider("ضغط المكمن (PSI)", 500, 3000, 1500)
    with col2:
        sw = st.slider("تشبع الماء (Sw)", 0.25, 0.8, 0.4)
    
    # حساب الإنتاج
    mu = max(float(visc_func(pressure)), 1e-6)
    kr = float(kro_func(sw))
    prod = (kr * pressure) / mu
    
    st.metric("معدل الإنتاج المحسوب", f"{prod:.4f} bbl/day")
    
    # عرض ملف الإنتاج إذا رفعته
    if prod_file:
        prod_df = pd.read_csv(prod_file)
        st.subheader("تحليل بيانات الإنتاج")
        st.line_chart(prod_df.head(100)) # عرض أول 100 سجل

else:
    st.info("⚠️ يرجى رفع الملفات الثلاثة (PVTO, Water-Oil, Pro.xlsx) من القائمة الجانبية لبدء المحاكاة.")
