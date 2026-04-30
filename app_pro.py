import streamlit as st
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. إعدادات الصفحة
st.set_page_config(page_title="Nano-Swarm Core", layout="wide")

# تصميم الواجهة (CSS) لجعلها تبدو احترافية
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #4e5d6c; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛢️ Nano-Swarm Core Simulator")
st.markdown("---")

# --- دالة البحث الذكي عن الأعمدة ---
def get_col(df, keywords):
    for col in df.columns:
        if any(key.lower() in str(col).lower() for key in keywords):
            return col
    return None

# --- دالة تحميل ومعالجة البيانات ---
@st.cache_data
def load_data():
    try:
        pvto_df = pd.read_excel("PVTO.xlsx")
        rel_perm_df = pd.read_excel("water-oil Relative permeability.xlsx")
        cap_press_df = pd.read_excel("capillary pressure.xlsx")
        pro_df = pd.read_excel("Pro.xlsx", skiprows=8)

        # تحويل قسري للأرقام لتجنب أي نصوص مختبئة
        for df in [pvto_df, rel_perm_df, cap_press_df, pro_df]:
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df.dropna(how='all', inplace=True)

        # تجهيز الانتربولشن (Interp)
        p_col = get_col(pvto_df, ['pressure', 'press'])
        v_col = get_col(pvto_df, ['viscosity', 'visc'])
        visc_interp = interp1d(pvto_df[p_col], pvto_df[v_col], fill_value="extrapolate")

        sw_rel_col = get_col(rel_perm_df, ['sw', 'water'])
        kro_col = get_col(rel_perm_df, ['kro', 'oil'])
        krw_col = get_col(rel_perm_df, ['krw', 'water_rel'])
        kro_interp = interp1d(rel_perm_df[sw_rel_col], rel_perm_df[kro_col], fill_value="extrapolate")
        krw_interp = interp1d(rel_perm_df[sw_rel_col], rel_perm_df[krw_col], fill_value="extrapolate")

        sw_cap_col = get_col(cap_press_df, ['sw', 'water'])
        pc_col = get_col(cap_press_df, ['pc', 'psi', 'press'])
        pc_interp = interp1d(cap_press_df[sw_cap_col], cap_press_df[pc_col], fill_value="extrapolate")

        return visc_interp, kro_interp, krw_interp, pc_interp, pro_df, rel_perm_df, cap_press_df
    except Exception as e:
        st.error(f"خطأ في قراءة البيانات: {e}")
        return None, None, None, None, None, None, None

# تنفيذ التحميل
visc_interp, kro_interp, krw_interp, pc_interp, pro_df, rel_df, cap_df = load_data()

if pro_df is not None:
    # --- Sidebar ---
    st.sidebar.header("Simulation Settings")
    p_slider = st.sidebar.slider("Pressure (psi)", 500, 5000, 2500)
    sw_slider = st.sidebar.slider("Water Saturation (Sw)", 0.0, 1.0, 0.4)
    nano_mode = st.sidebar.toggle("Activate Nano-Swarm Particles")

    # --- النتائج السريعة (Metrics) ---
    res_visc = float(visc_interp(p_slider))
    res_kro = float(kro_interp(sw_slider))
    if nano_mode:
        res_visc *= 0.75 # تقليل اللزوجة بنسبة 25%
        res_kro *= 1.15 # زيادة النفاذية

    c1, c2, c3 = st.columns(3)
    c1.metric("Calculated Viscosity", f"{res_visc:.3f} cP")
    c2.metric("Oil Permeability (Kro)", f"{res_kro:.3f}")
    c3.metric("Capillary Pressure", f"{float(pc_interp(sw_slider)):.2f} psi")

    # --- الرسوم البيانية (Charts) ---
    st.markdown("### Reservoir Performance Analysis")
    tab1, tab2 = st.tabs(["Production Trends", "Relative Permeability & PC"])

    with tab1:
        fig_prod = go.Figure()
        # عرض عمود الإنتاج من ملف Pro
        oil_col = get_col(pro_df, ['oil', 'prod'])
        if oil_col:
            fig_prod.add_trace(go.Scatter(y=pro_df[oil_col], mode='lines+markers', name='Oil Rate', line=dict(color='#00ff00')))
            fig_prod.update_layout(title="Daily Oil Production History", template="plotly_dark")
            st.plotly_chart(fig_prod, use_container_width=True)

    with tab2:
        # رسم منحنيات النفاذية النسبية والضغط الشعري جنباً إلى جنب
        fig_curves = make_subplots(specs=[[{"secondary_y": True}]])
        sw_vals = np.linspace(rel_df.iloc[:,0].min(), rel_df.iloc[:,0].max(), 50)
        
        fig_curves.add_trace(go.Scatter(x=sw_vals, y=kro_interp(sw_vals), name="Kro (Oil)", line=dict(color='green')))
        fig_curves.add_trace(go.Scatter(x=sw_vals, y=krw_interp(sw_vals), name="Krw (Water)", line=dict(color='blue')))
        fig_curves.add_trace(go.Scatter(x=sw_vals, y=pc_interp(sw_vals), name="Pc (Capillary)", line=dict(dash='dash', color='red')), secondary_y=True)
        
        fig_curves.update_layout(title="Relative Permeability & Capillary Pressure Curves", template="plotly_dark")
        st.plotly_chart(fig_curves, use_container_width=True)

    st.success("البرنامج يعمل الآن بكامل طاقته العلمية والرسومية ✅")
