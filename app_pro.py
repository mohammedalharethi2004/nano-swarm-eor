import streamlit as st
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 1. إعدادات الصفحة والواجهة (نفس تصميم المبرمج) ---
st.set_page_config(page_title="Nano-Swarm Core", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #4e5d6c; }
    h1, h2, h3 { color: #00d4ff; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛢️ Nano-Swarm Core: Advanced Reservoir Simulator")
st.write("Mechatronics Engineering Graduation Project")
st.markdown("---")

# --- 2. دالة البحث الذكي (لحل مشكلة أسماء الأعمدة المفقودة) ---
def find_column(df, keywords):
    for col in df.columns:
        if any(key.lower() in str(col).lower() for key in keywords):
            return col
    return None

# --- 3. دالة تحميل البيانات الكاملة (بكل تعديلات الإصلاح) ---
@st.cache_data
def load_all_reservoir_data():
    try:
        # قراءة الملفات الأربعة الأساسية
        pvto = pd.read_excel("PVTO.xlsx")
        rel_perm = pd.read_excel("water-oil Relative permeability.xlsx")
        cap_press = pd.read_excel("capillary pressure.xlsx")
        pro_history = pd.read_excel("Pro.xlsx", skiprows=8)

        # تنظيف آلي لجميع الملفات من أي نصوص (مثل psi, cP) لضمان عدم انهيار الكود
        for data in [pvto, rel_perm, cap_press, pro_history]:
            for column in data.columns:
                data[column] = pd.to_numeric(data[column], errors='coerce')
            data.dropna(how='all', inplace=True)

        # تجهيز دوال الانتربولشن (نفس حسابات المبرمج)
        # PVTO
        p_col = find_column(pvto, ['pressure', 'press'])
        v_col = find_column(pvto, ['viscosity', 'visc'])
        visc_func = interp1d(pvto[p_col], pvto[v_col], fill_value="extrapolate")

        # Relative Permeability
        sw_col = find_column(rel_perm, ['sw', 'water'])
        kro_col = find_column(rel_perm, ['kro', 'oil'])
        krw_col = find_column(rel_perm, ['krw', 'water_rel'])
        kro_func = interp1d(rel_perm[sw_col], rel_perm[kro_col], fill_value="extrapolate")
        krw_func = interp1d(rel_perm[sw_col], rel_perm[krw_col], fill_value="extrapolate")

        # Capillary Pressure
        sw_c_col = find_column(cap_press, ['sw', 'water'])
        pc_col = find_column(cap_press, ['pc', 'psi', 'press'])
        pc_func = interp1d(cap_press[sw_c_col], cap_press[pc_col], fill_value="extrapolate")

        return visc_func, kro_func, krw_func, pc_func, pro_history, rel_perm, cap_press
    
    except Exception as e:
        st.error(f"❌ حدث خطأ في تحميل البيانات: {e}")
        return None

# --- 4. تنفيذ التحميل ---
data_package = load_all_reservoir_data()

if data_package:
    visc_f, kro_f, krw_f, pc_f, pro_df, raw_rel, raw_cap = data_package

    # --- 5. لوحة التحكم الجانبية (Sidebar) ---
    st.sidebar.header("🕹️ Simulation Controls")
    target_pressure = st.sidebar.slider("Reservoir Pressure (psi)", 
                                        float(pro_df.iloc[:,1].min() if not pro_df.empty else 500), 
                                        5000.0, 2500.0)
    target_sw = st.sidebar.slider("Water Saturation (Sw)", 0.0, 1.0, 0.35)
    
    st.sidebar.markdown("---")
    nano_swarm = st.sidebar.toggle("Enable Nano-Swarm Core", value=False)
    
    # --- 6. الحسابات الفيزيائية (المنطق الرياضي للمبرمج) ---
    viscosity = float(visc_f(target_pressure))
    kro_val = float(kro_f(target_sw))
    krw_val = float(krw_f(target_sw))
    pc_val = float(pc_f(target_sw))

    # تأثير النانو (إضافة مشروعك)
    if nano_swarm:
        viscosity *= 0.8  # تحسين السيولة
        kro_val *= 1.2    # تحسين تدفق الزيت
        st.sidebar.info("🚀 Nano-Swarm Active: Viscosity Reduced & Kro Enhanced")

    # --- 7. عرض النتائج الرئيسية (Metrics) ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Viscosity (cP)", f"{viscosity:.3f}")
    col2.metric("Kro (Oil)", f"{kro_val:.3f}")
    col3.metric("Krw (Water)", f"{krw_val:.3f}")
    col4.metric("Pc (psi)", f"{pc_val:.2f}")

    # --- 8. الرسوم البيانية الكاملة ---
    st.markdown("### 📊 Reservoir Diagnostic Charts")
    
    tab1, tab2, tab3 = st.tabs(["Production History", "Relative Permeability", "Capillary Pressure"])

    with tab1:
        # رسم بيانات الإنتاج من ملف Pro
        fig1 = go.Figure()
        oil_p_col = find_column(pro_df, ['oil', 'prod'])
        if oil_p_col:
            fig1.add_trace(go.Scatter(y=pro_df[oil_p_col], name="Oil Production", line=dict(color='#00ff00', width=3)))
            fig1.update_layout(title="Historical Oil Production Rate", template="plotly_dark", height=400)
            st.plotly_chart(fig1, use_container_width=True)

    with tab2:
        # رسم منحنيات النفاذية (Kro & Krw)
        fig2 = go.Figure()
        sw_range = np.linspace(0.2, 0.9, 50)
        fig2.add_trace(go.Scatter(x=sw_range, y=kro_f(sw_range), name="Kro (Oil)", line=dict(color='green')))
        fig2.add_trace(go.Scatter(x=sw_range, y=krw_f(sw_range), name="Krw (Water)", line=dict(color='blue')))
        fig2.update_layout(title="Relative Permeability Curves", xaxis_title="Sw", template="plotly_dark", height=400)
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        # رسم الضغط الشعري
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=sw_range, y=pc_f(sw_range), name="Pc", line=dict(color='red', dash='dot')))
        fig3.update_layout(title="Capillary Pressure Curve", xaxis_title="Sw", yaxis_title="Pc (psi)", template="plotly_dark", height=400)
        st.plotly_chart(fig3, use_container_width=True)

    st.success("✅ Nano-Swarm Core System is Online and Stable")
else:
    st.error("⚠️ فشل في تشغيل النظام. يرجى التأكد من رفع ملفات الإكسل الأربعة في المجلد الرئيسي.")
