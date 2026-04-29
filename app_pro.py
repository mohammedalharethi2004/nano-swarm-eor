import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import interp1d
from datetime import datetime
import time

st.set_page_config(layout="wide", page_title="Nano-Swarm Command Center")

# ================= STYLE =================
st.markdown("""
<style>
body {background-color:#0b0f17; color:white;}

.kpi-card {
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(12px);
    border:1px solid rgba(0,255,255,0.3);
    border-radius:15px;
    padding:15px;
    text-align:center;
    box-shadow:0 0 20px rgba(0,255,255,0.3);
    transition:0.3s;
}
.kpi-card:hover {
    box-shadow:0 0 30px gold;
    transform: scale(1.05);
}
</style>
""", unsafe_allow_html=True)

# ================= DATA =================
@st.cache_data
def load_all():
    pvto = pd.read_excel("PVTO.xlsx")
    rel = pd.read_excel("water-oil Relative permeability.xlsx")
    cap = pd.read_excel("capillary pressure.xlsx")
    pro = pd.read_excel("Pro.xlsx", skiprows=8)

    for df in [pvto, rel, cap, pro]:
        df.columns = df.columns.str.strip().str.lower()

    pvto['pressure'] = pd.to_numeric(pvto['pressure'], errors='coerce')
    pvto['oil viscosity'] = pd.to_numeric(pvto['oil viscosity'], errors='coerce')

    rel['sw'] = pd.to_numeric(rel['sw'], errors='coerce')
    rel['kro'] = pd.to_numeric(rel['kro'], errors='coerce')

    cap['sw'] = pd.to_numeric(cap['sw'], errors='coerce')
    cap['pcow (psi)'] = pd.to_numeric(cap['pcow (psi)'], errors='coerce')

    pvto.dropna(inplace=True)
    rel.dropna(inplace=True)
    cap.dropna(inplace=True)

    pvto.sort_values('pressure', inplace=True)
    rel.sort_values('sw', inplace=True)
    cap.sort_values('sw', inplace=True)

    visc = interp1d(pvto['pressure'], pvto['oil viscosity'], fill_value="extrapolate")
    kro = interp1d(rel['sw'], rel['kro'], fill_value="extrapolate")
    pc = interp1d(cap['sw'], cap['pcow (psi)'], fill_value="extrapolate")

    return visc, kro, pc, pro

visc_func, kro_func, pc_func, pro_data = load_all()

# ================= MODEL =================
class Reservoir:
    def __init__(self):
        self.grid = np.random.rand(25,25)
        self.initial = self.grid.copy()
        self.kro_map = np.ones((25,25))
        self.pc_map = np.ones((25,25))

    def production(self, p):
        mu = float(visc_func(p))
        sw_avg = np.mean(self.grid)
        kro_avg = float(kro_func(sw_avg)) * np.mean(self.kro_map)
        pc_avg = float(pc_func(sw_avg)) * np.mean(self.pc_map)
        return max((kro_avg * (p - pc_avg)/1000)/(mu+1e-6),0)

class Nano:
    def __init__(self):
        self.x = np.random.randint(0,25)
        self.y = np.random.randint(0,25)

    def move(self, grid):
        gx, gy = np.gradient(grid)
        self.x = int(np.clip(self.x + gx[self.x,self.y],0,24))
        self.y = int(np.clip(self.y + gy[self.x,self.y],0,24))

# ================= SESSION =================
if "res" not in st.session_state:
    st.session_state.res = Reservoir()
    st.session_state.nano = [Nano() for _ in range(30)]
    st.session_state.logs = []
    st.session_state.nano_series = []
    st.session_state.base_series = []

res = st.session_state.res

# ================= TABS =================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard",
    "🌍 Subsurface",
    "🤖 Control",
    "📈 Analytics",
    "💰 Economics"
])

# ================= DASHBOARD =================
with tab1:
    st.title("🛢️ Command Overview")

    pressure = st.slider("Pressure",500,3000,1500)

    base_prod = pro_data.select_dtypes(include=np.number).mean().mean()
    nano_prod = res.production(pressure)
    lift = (nano_prod-base_prod)/base_prod*100 if base_prod>0 else 0

    c1,c2,c3,c4 = st.columns(4)

    c1.markdown(f"<div class='kpi-card'>Traditional<br>{base_prod:.2f}</div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='kpi-card'>Nano<br>{nano_prod:.2f}</div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='kpi-card'>Lift<br>{lift:.2f}%</div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='kpi-card'>Bots<br>{len(st.session_state.nano)}</div>", unsafe_allow_html=True)

# ================= SUBSURFACE =================
with tab2:
    st.title("🌍 Subsurface Live View")

    chart = st.empty()

    wells = pro_data.columns[:5]
    wx = np.linspace(0,24,len(wells))
    wy = np.linspace(0,24,len(wells))

    for _ in range(15):
        colors = []

        for i,n in enumerate(st.session_state.nano):
            n.move(res.grid)
            sw = res.grid[n.x,n.y]

            if sw > 0.6:
                res.kro_map[n.x,n.y] *= 1.05
                res.pc_map[n.x,n.y] *= 0.95
                colors.append("gold")

                st.session_state.logs.append(
                    f"[{datetime.now().strftime('%H:%M:%S')}] Nano-{i}: Injecting at ({n.x},{n.y})"
                )
            else:
                colors.append("cyan")

        xs = [n.x for n in st.session_state.nano]
        ys = [n.y for n in st.session_state.nano]

        fig = go.Figure()
        fig.add_trace(go.Surface(z=res.grid, opacity=0.8))

        fig.add_trace(go.Scatter3d(
            x=xs, y=ys,
            z=[res.grid[x,y] for x,y in zip(xs,ys)],
            mode='markers',
            marker=dict(size=5, color=colors)
        ))

        fig.add_trace(go.Scatter3d(
            x=wx, y=wy, z=[1]*len(wells),
            mode='text',
            text=wells
        ))

        chart.plotly_chart(fig, use_container_width=True)
        time.sleep(0.2)

# ================= CONTROL =================
with tab3:
    st.title("🤖 Swarm Control")

    mode = st.radio("Mode", ["Auto","Manual"])
    tx = st.slider("Target X",0,24,12)
    ty = st.slider("Target Y",0,24,12)

    if st.button("Apply"):
        if mode=="Manual":
            for n in st.session_state.nano:
                n.x += np.sign(tx - n.x)
                n.y += np.sign(ty - n.y)

# ================= ANALYTICS =================
with tab4:
    st.title("📈 Production Lift (Live)")

    base_val = pro_data.select_dtypes(include=np.number).mean().mean()
    nano_val = res.production(1500)

    st.session_state.base_series.append(base_val)
    st.session_state.nano_series.append(nano_val)

    fig = go.Figure()
    fig.add_trace(go.Scatter(y=st.session_state.base_series, name="Traditional", line=dict(dash='dash')))
    fig.add_trace(go.Scatter(y=st.session_state.nano_series, name="Nano", line=dict(color='cyan')))

    fig.update_layout(template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    st.metric("Live Lift %", f"{(nano_val-base_val)/base_val*100:.2f}%")

# ================= ECON =================
with tab5:
    st.title("💰 Economic Hub")

    oil_price = st.number_input("Oil Price",50,150,80)
    cost = st.number_input("Nano Cost",1000,20000,5000)

    production = res.production(1500)
    revenue = production * oil_price
    npv = revenue - cost

    st.metric("Revenue", f"${revenue:.2f}")
    st.metric("NPV", f"${npv:.2f}")

    df = pd.DataFrame({
        "Production":[production],
        "Revenue":[revenue],
        "NPV":[npv]
    })

    st.download_button("📥 Export Report", df.to_csv(), "report.csv")

# ================= LOG =================
st.markdown("### 🧠 Event Console")
for log in st.session_state.logs[-10:]:
    st.text(log)

# ================= STATUS =================
st.markdown("---")
st.markdown(f"""
⚡ Energy: {np.random.randint(50,100)}% |
🧠 CPU: {np.random.randint(10,90)}% |
🌐 System: ONLINE
""")
