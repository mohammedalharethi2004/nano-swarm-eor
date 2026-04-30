import streamlit as st
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
import plotly.graph_objects as go

# دالة ذكية لتنظيف أسماء الأعمدة والبحث عن العمود الصحيح
def get_col(df, keywords):
    for col in df.columns:
        if any(key.lower() in col.lower() for key in keywords):
            return col
    return None

@st.cache_data
def load_data():
    try:
        # تحميل الملفات
        pvto_df = pd.read_excel("PVTO.xlsx")
        rel_perm_df = pd.read_excel("water-oil Relative permeability.xlsx")
        cap_press_df = pd.read_excel("capillary pressure.xlsx")
        pro_df = pd.read_excel("Pro.xlsx", skiprows=8)

        # تحويل البيانات لأرقام وحذف النصوص (لضمان عدم ظهور خطأ float vs str)
        for df in [pvto_df, rel_perm_df, cap_press_df, pro_df]:
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df.dropna(how='all', inplace=True)

        # 1. معالجة PVTO
        p_col = get_col(pvto_df, ['pressure', 'press'])
        v_col = get_col(pvto_df, ['viscosity', 'visc'])
        pvto_df = pvto_df.dropna(subset=[p_col, v_col]).sort_values(p_col)
        visc_interp = interp1d(pvto_df[p_col], pvto_df[v_col], fill_value="extrapolate")

        # 2. معالجة Relative Permeability
        sw_rel_col = get_col(rel_perm_df, ['sw', 'water'])
        kro_col = get_col(rel_perm_df, ['kro', 'oil'])
        krw_col = get_col(rel_perm_df, ['krw', 'water_rel'])
        rel_perm_df = rel_perm_df.dropna(subset=[sw_rel_col]).sort_values(sw_rel_col)
        kro_interp = interp1d(rel_perm_df[sw_rel_col], rel_perm_df[kro_col], fill_value="extrapolate")
        krw_interp = interp1d(rel_perm_df[sw_rel_col], rel_perm_df[krw_col], fill_value="extrapolate")

        # 3. معالجة Capillary Pressure (حل مشكلة الخطأ الأخير)
        sw_cap_col = get_col(cap_press_df, ['sw', 'water'])
        pc_col = get_col(cap_press_df, ['pc', 'psi', 'press'])
        cap_press_df = cap_press_df.dropna(subset=[sw_cap_col, pc_col]).sort_values(sw_cap_col)
        pc_interp = interp1d(cap_press_df[sw_cap_col], cap_press_df[pc_col], fill_value="extrapolate")

        return visc_interp, kro_interp, krw_interp, pc_interp, pro_df
    
    except Exception as e:
        st.error(f"Critical Data Loading Error: تأكد من وجود الملفات وصحة الأعمدة. التفاصيل: {e}")
        return None, None, None, None, None

# استدعاء الدالة
visc_interp, kro_interp, krw_interp, pc_interp, pro_df = load_data()

if pro_df is not None:
    st.success("✅ تم تحميل جميع البيانات بنجاح!")
    # هنا يكمل باقي كود الـ Dashboard الخاص بك...
