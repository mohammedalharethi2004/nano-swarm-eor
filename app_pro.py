import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import interp1d
import time, random, datetime
from scipy.ndimage import gaussian_filter

# ================== CONFIG ==================
st.set_page_config(layout="wide", page_title="Nano-Swarm EOR", page_icon="🚀")

# ================== SMART DATA LOADER ==================
@st.cache_data
def load_data():
    import re

    def clean_columns(df):
        df.columns = [str(col).strip().lower().replace(" ", "_") for col in df.columns]
        return df

    def find_column(df, keywords):
        for col in df.columns:
            for key in keywords:
                if key in col:
                    return col
        return None

    def clean_numeric(series):
        return pd.to_numeric(
            series.astype(str).str.replace(r"[^\d\.\-]", "", regex=True),
            errors="coerce"
        )

    try:
        pvto_df = clean_columns(pd.read_excel("PVTO.xlsx"))
        rel_perm_df = clean_columns(pd.read_excel("water-oil Relative permeability.xlsx"))
        cap_press_df = clean_columns(pd.read_excel("capillary pressure.xlsx"))
        pro_df = pd.read_excel("Pro.xlsx", skiprows=8)

        # ==== PVTO ====
        p_col = find_column(pvto_df, ["pressure"])
        mu_col = find_column(pvto_df, ["viscosity"])

        pvto_df[p_col] = clean_numeric(pvto_df[p_col])
        pvto_df[mu_col] = clean_numeric(pvto_df[mu_col])

        pvto_df = pvto_df.dropna().sort_values(p_col)

        visc_interp = interp1d(pvto_df[p_col], pvto_df[mu_col], fill_value="extrapolate", bounds_error=False)

        # ==== REL PERM ====
        sw = find_column(rel_perm_df, ["sw"])
        kro = find_column(rel_perm_df, ["kro"])
        krw = find_column(rel_perm_df, ["krw"])

        for c in [sw, kro, krw]:
            rel_perm_df[c] = clean_numeric(rel_perm_df[c])

        rel_perm_df = rel_perm_df.dropna().sort_values(sw)

        kro_interp = interp1d(rel_perm_df[sw], rel_perm_df[kro], fill_value="extrapolate", bounds_error=False)
        krw_interp = interp1d(rel_perm_df[sw], rel_perm_df[krw], fill_value="extrapolate", bounds_error=False)

        # ==== CAP PRESS ====
        sw2 = find_column(cap_press_df, ["sw"])
        pc = find_column(cap_press_df, ["pc"])

        cap_press_df[sw2] = clean_numeric(cap_press_df[sw2])
        cap_press_df[pc] = clean_numeric(cap_press_df[pc])

        cap_press_df = cap_press_df.dropna().sort_values(sw2)

        pc_interp = interp1d(cap_press_df[sw2], cap_press_df[pc], fill_value="extrapolate", bounds_error=False)

        # ==== PRODUCTION ====
        pro_df.columns = pro_df.iloc[0].astype(str).str.lower()
        pro_df = pro_df[1:].reset_index(drop=True)

        oil_col = find_column(pro_df, ["oil"])
        pro_df["oil"] = clean_numeric(pro_df[oil_col])

        pro_df = pro_df.dropna(subset=["oil"])

        return visc_interp, kro_interp, krw_interp, pc_interp, pro_df

    except Exception as e:
        st.error(f"Data Error: {e}")
        st.stop()


visc_interp, kro_interp, krw_interp, pc_interp, pro_data = load_data()

# ================== SIMULATION ==================
class Reservoir:
    def __init__(self, size=25):
        self.size = size
        self.sw = np.random.uniform(0.2, 0.4, (size, size))
        self.perm = np.random.uniform(50, 200, (size, size))
        self.nano = np.zeros((size, size))

    def update(self, swarm):
        self.nano *= 0
        for n in swarm:
            self.nano[n.x, n.y] += 1

    def production(self, pressure, swarm):
        self.update(swarm)

        avg_sw = np.mean(self.sw)
        avg_perm = np.mean(self.perm)

        mu = float(visc_interp(pressure))
        kro = float(kro_interp(avg_sw))
        pc = float(pc_interp(avg_sw))

        nano_effect = np.mean(self.nano)

        mu *= (1 - nano_effect * 0.01)
        kro *= (1 + nano_effect * 0.005)
        pc *= (1 - nano_effect * 0.01)

        prod = max(0, kro * avg_perm * (pressure - pc) / (mu + 1e-6))

        return prod


class Nano:
    def __init__(self, size):
        self.x = np.random.randint(0, size)
        self.y = np.random.randint(0, size)

    def move(self, size):
        self.x = np.clip(self.x + random.randint(-1,1), 0, size-1)
        self.y = np.clip(self.y + random.randint(-1,1), 0, size-1)


# ================== STATE ==================
if "res" not in st.session_state:
    st.session_state.res = Reservoir()
    st.session_state.swarm = [Nano(25) for _ in range(100)]
    st.session_state.run = False
    st.session_state.history = []

res = st.session_state.res

# ================== UI ==================
st.title("🚀 Nano-Swarm EOR Simulator")

pressure = st.slider("Pressure", 500, 3000, 1500)

if st.button("▶ Start"):
    st.session_state.run = True

if st.button("⛔ Stop"):
    st.session_state.run = False

# ================== LOOP ==================
if st.session_state.run:
    for n in st.session_state.swarm:
        n.move(res.size)

prod = res.production(pressure, st.session_state.swarm)
st.session_state.history.append(prod)

# ================== OUTPUT ==================
st.metric("Production", f"{prod:.2f} bbl/day")

fig = go.Figure()
fig.add_trace(go.Scatter(y=st.session_state.history, name="Production"))
st.plotly_chart(fig, use_container_width=True)
