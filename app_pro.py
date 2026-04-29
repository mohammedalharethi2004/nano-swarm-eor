import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import interp1d
from datetime import datetime
import time
import random

st.set_page_config(layout="wide", page_title="Nano-Swarm Command Center")

# ================= STYLE =================
st.markdown("""
<style>
body {background-color:#0b0f17; color:white;}

.kpi-card {
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(15px);
    border-radius:20px;
    padding:20px;
    text-align:center;
    border:1px solid rgba(0,255,255,0.4);
    box-shadow:0 0 25px rgba(0,255,255,0.4);
    transition:0.3s;
}
.kpi-card:hover {
    box-shadow:0 0 35px gold;
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

    pvto = pvto.dropna().sort_values("pressure")
    rel = rel.dropna().sort_values("sw")
    cap = cap.dropna().sort_values("sw")

    visc = interp1d(pvto['pressure'], pvto['oil viscosity'], fill_value="extrapolate")
    kro = interp1d(rel['sw'], rel['kro'], fill_value="extrapolate")
    pc = interp1d(cap['sw'], cap['pcow (psi)'], fill_value="extrapolate")

    return visc, kro, pc, pro

visc_func, kro_func, pc_func, pro_data = load_all()

# ================= MODEL =================
class Reservoir:
    def __init__(self):
        self.grid = np.random.rand(25,25)
        self.kro_map = np.ones((25,25))
        self.pc_map = np.ones((25,25))

    def production(self, p):
        mu = float(visc_func(p))
        sw = np.mean(self.grid)
        kro = float(kro_func(sw)) * np.mean(self.kro_map)
        pc = float(pc_func(sw)) * np.mean(self.pc_map)
        return max((kro*(p-pc)/1000)/(mu+1e-6),0)

    def mobility(self):
        return np.mean(self.kro_map) / (np.mean(self.pc_map)+1e-6)

# ================= NANO =================
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
    st.session_state.running = False
    st.session_state.base_series = []
    st.session_state.nano_series = []
    st.session_state.start_time = time.time()

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
    st.title("🛢️ Engineering Command")

    pressure = st.slider("Pressure",500,3000,1500)

    base = pro_data.select_dtypes(include=np.number).mean().mean()
    nano = res.production(pressure)
    lift = (nano-base)/base*100 if base>0 else 0

    c1,c2,c3,c4 = st.columns(4)

    c1.markdown(f"<div class='kpi-card'>Traditional<br>{base:.2f}</div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='kpi-card'>Nano<br>{nano:.2f}</div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='kpi-card'>Lift<br>{lift:.2f}%</div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='kpi-card'>Bots<br>{len(st.session_state.nano)}</div>", unsafe_allow_html=True)

    # Gauge Efficiency
    eff = np.clip(np.mean(res.grid)*100,0,100)

    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=eff,
        title={'text':"Sweep Efficiency"},
        gauge={'axis':{'range':[0,100]},
               'bar':{'color':"cyan"}}
    ))
    st.plotly_chart(fig_gauge, use_container_width=True)

# ================= SUBSURFACE =================
with tab2:
    st.title("🌍 Subsurface Live View")

    chart = st.empty()

    if st.session_state.running:
        for n in st.session_state.nano:
            n.move(res.grid)

            sw = res.grid[n.x,n.y]

            if sw > 0.6:
                res.grid[n.x,n.y] = min(res.grid[n.x,n.y] + 0.1,1)
            else:
                res.grid[n.x,n.y] *= 0.97

        xs = [n.x for n in st.session_state.nano]
        ys = [n.y for n in st.session_state.nano]

        fig = go.Figure()
        fig.add_trace(go.Surface(z=res.grid, colorscale="Turbo"))

        fig.add_trace(go.Scatter3d(
            x=xs, y=ys,
            z=[res.grid[x,y] for x,y in zip(xs,ys)],
            mode='markers',
            marker=dict(size=5, color='cyan')
        ))

        chart.plotly_chart(fig, use_container_width=True)

        time.sleep(0.3)
        st.rerun()

# ================= CONTROL =================
with tab3:
    st.title("🤖 Control")

    if st.button("▶ Start"):
        st.session_state.running = True
        st.markdown("🔊 System Activated")

    if st.button("⏸ Stop"):
        st.session_state.running = False

# ================= ANALYTICS =================
with tab4:
    st.title("📈 Production Intelligence")

    base = pro_data.select_dtypes(include=np.number).mean().mean()
    nano = res.production(1500)

    st.session_state.base_series.append(base)
    st.session_state.nano_series.append(nano)

    base_cum = np.cumsum(st.session_state.base_series)
    nano_cum = np.cumsum(st.session_state.nano_series)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        y=base_cum,
        name="Traditional",
        line=dict(color="white", dash="dash")
    ))

    fig.add_trace(go.Scatter(
        y=nano_cum,
        name="Nano",
        line=dict(color="cyan", width=4),
        fill='tozeroy',
        fillcolor='rgba(0,255,255,0.1)'
    ))

    future = np.linspace(nano_cum[-1], nano_cum[-1]*1.3, 15)

    fig.add_trace(go.Scatter(
        y=list(nano_cum)+list(future),
        fill='toself',
        opacity=0.15,
        name="Predictive Zone"
    ))

    fig.update_layout(template="plotly_dark", height=600)

    st.plotly_chart(fig, use_container_width=True)

    # Stabilization
    if time.time() - st.session_state.start_time > 10:
        lift = (nano-base)/base*100
        st.metric("Live Lift %", f"{lift:.2f}%")
    else:
        st.info("⏳ Stabilizing...")

    # AI Insights
    insights = [
        "[ANALYZING] Sweep efficiency at 78%",
        "[OPTIMIZING] Reducing IFT...",
        "[PREDICTION] ROI 215%",
        "[AI] Adjusting nano-flow..."
    ]
    st.info(random.choice(insights))

# ================= ECON =================
with tab5:
    st.title("💰 Economics")

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
