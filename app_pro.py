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

    def mobility_ratio(self):
        sw = np.mean(self.grid)
        mu_oil = float(visc_func(1500))
        mu_water = 0.5  # افتراضي
        kr = float(kro_func(sw))
        return (kr/mu_water) / (1/mu_oil)

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
    st.title("🛢️ Command Overview")

    pressure = st.slider("Pressure",500,3000,1500)

    base_prod = pro_data.select_dtypes(include=np.number).mean().mean()
    nano_prod = res.production(pressure)
    lift = (nano_prod-base_prod)/base_prod*100 if base_prod>0 else 0

    mobility = res.mobility_ratio()
    water_cut = np.mean(res.grid)

    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(f"<div class='kpi-card'>Traditional<br>{base_prod:.2f}</div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='kpi-card'>Nano<br>{nano_prod:.2f}</div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='kpi-card'>Lift<br>{lift:.2f}%</div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='kpi-card'>Mobility M<br>{mobility:.2f}</div>", unsafe_allow_html=True)

    st.metric("Water Cut Reduction", f"{(1-water_cut)*100:.2f}%")

# ================= SUBSURFACE =================
with tab2:
    st.title("🌍 Subsurface Live View")

    chart = st.empty()
    insight_box = st.empty()

    if st.session_state.running:

        for i,n in enumerate(st.session_state.nano):
            n.move(res.grid)

            sw = res.grid[n.x,n.y]

            # تأثير بصري + فيزيائي
            if sw > 0.6:
                res.grid[n.x,n.y] = min(res.grid[n.x,n.y] + 0.05,1)  # اخضرار
                res.kro_map[n.x,n.y] *= 1.05
                res.pc_map[n.x,n.y] *= 0.95

                st.session_state.logs.append(
                    f"[PHYSICS] Reducing IFT at ({n.x},{n.y})"
                )
            else:
                res.grid[n.x,n.y] *= 0.99

        xs = [n.x for n in st.session_state.nano]
        ys = [n.y for n in st.session_state.nano]

        fig = go.Figure()
        fig.add_trace(go.Surface(z=res.grid, colorscale='Viridis'))

        fig.add_trace(go.Scatter3d(
            x=xs, y=ys,
            z=[res.grid[x,y] for x,y in zip(xs,ys)],
            mode='markers',
            marker=dict(size=5, color='cyan')
        ))

        chart.plotly_chart(fig, use_container_width=True)

        insights = np.random.choice([
            "Optimizing sweep efficiency",
            "Targeting bypassed oil zones",
            "Recovery factor increasing",
            "Swarm adapting to reservoir"
        ])
        insight_box.info(f"🧠 {insights}")

        time.sleep(0.3)
        st.rerun()

# ================= CONTROL =================
with tab3:
    st.title("🤖 Control")

    if st.button("▶ Start"):
        st.session_state.running = True

    if st.button("⏸ Stop"):
        st.session_state.running = False

# ================= ANALYTICS =================
with tab4:
    st.title("📈 Production Analytics")

    base = pro_data.select_dtypes(include=np.number).mean().mean()
    nano = res.production(1500)

    st.session_state.base_series.append(base)
    st.session_state.nano_series.append(nano)

    base_cum = np.cumsum(st.session_state.base_series)
    nano_cum = np.cumsum(st.session_state.nano_series)

    fig = go.Figure()
    fig.add_trace(go.Scatter(y=base_cum, name="Traditional", line=dict(dash='dash', color='gray')))
    fig.add_trace(go.Scatter(y=nano_cum, name="Nano", line=dict(color='cyan')))

    # Forecast Zone
    future = np.linspace(nano_cum[-1], nano_cum[-1]*1.2, 10)
    fig.add_trace(go.Scatter(y=list(nano_cum)+list(future),
                             fill='toself',
                             opacity=0.1,
                             name="Predictive Zone"))

    fig.update_layout(template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    # منع lift بالبداية
    elapsed = time.time() - st.session_state.start_time
    if elapsed > 10:
        lift = (nano-base)/base*100
        st.metric("Live Lift %", f"{lift:.2f}%")
    else:
        st.info("⏳ Stabilizing simulation...")

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
