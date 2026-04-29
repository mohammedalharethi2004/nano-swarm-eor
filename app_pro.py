import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import interp1d
import time

st.set_page_config(layout="wide", page_title="Nano-Swarm AI EOR")

# ================= DATA =================
@st.cache_data
def load_data():
    pvto = pd.read_excel("PVTO.xlsx")
    rel = pd.read_excel("water-oil Relative permeability.xlsx")

    pvto.columns = pvto.columns.str.strip().str.lower()
    rel.columns = rel.columns.str.strip().str.lower()

    pvto['pressure'] = pd.to_numeric(pvto['pressure'], errors='coerce')
    pvto['oil viscosity'] = pd.to_numeric(pvto['oil viscosity'], errors='coerce')
    rel['sw'] = pd.to_numeric(rel['sw'], errors='coerce')
    rel['kro'] = pd.to_numeric(rel['kro'], errors='coerce')

    pvto = pvto.dropna().sort_values('pressure')
    rel = rel.dropna().sort_values('sw')

    visc = interp1d(pvto['pressure'], pvto['oil viscosity'], fill_value="extrapolate")
    kro = interp1d(rel['sw'], rel['kro'], fill_value="extrapolate")

    return visc, kro

visc_func, kro_func = load_data()

# ================= MODEL =================
class Reservoir:
    def __init__(self):
        self.grid = np.random.rand(25,25)
        self.viscosity_map = np.ones((25,25))

    def production(self, p, sw):
        mu = float(visc_func(p)) * np.mean(self.viscosity_map)
        kr = float(kro_func(sw))
        return (np.mean(self.grid)*kr*p/1000)/(mu+1e-6)

class Nano:
    def __init__(self):
        self.x = np.random.randint(0,25)
        self.y = np.random.randint(0,25)

    def move_auto(self, grid):
        gx, gy = np.gradient(grid)
        self.x = int(np.clip(self.x + gx[self.x,self.y],0,24))
        self.y = int(np.clip(self.y + gy[self.x,self.y],0,24))

    def move_manual(self, target):
        tx, ty = target
        self.x += np.sign(tx - self.x)
        self.y += np.sign(ty - self.y)
        self.x = int(np.clip(self.x,0,24))
        self.y = int(np.clip(self.y,0,24))

# ================= SESSION =================
if "res" not in st.session_state:
    st.session_state.res = Reservoir()
    st.session_state.nano = [Nano() for _ in range(25)]
    st.session_state.history = []
    st.session_state.logs = []
    st.session_state.phase = 0

res = st.session_state.res

# ================= UI =================
col1, col2, col3 = st.columns([1,2,1])

# ===== CONTROL =====
with col1:
    st.header("⚙️ Control")

    pressure = st.slider("Pressure",500,3000,1500)
    sw = st.slider("Sw",0.2,0.8,0.4)

    mode = st.radio("Mode", ["Auto","Manual"])

    target_x = st.number_input("Target X",0,24,12)
    target_y = st.number_input("Target Y",0,24,12)

    oil_price = st.number_input("Oil Price",50,150,80)
    cost = st.number_input("Nano Cost",1000,10000,3000)

    run = st.button("▶ Start")
    reset = st.button("🔄 Reset")

# ===== CORE =====
with col2:
    st.title("🛢️ Nano-Swarm Core Engine")

    progress = st.progress(st.session_state.phase/4)

    chart = st.empty()
    heat = st.empty()

    if run:
        for step in range(20):

            # phases
            st.session_state.phase = min(4, st.session_state.phase + 0.05)
            progress.progress(st.session_state.phase/4)

            for i,n in enumerate(st.session_state.nano):

                if mode=="Auto":
                    n.move_auto(res.grid)
                else:
                    n.move_manual((target_x,target_y))

                # chemical effect (reduce viscosity)
                res.viscosity_map[n.x,n.y] *= 0.97
                res.grid[n.x,n.y] *= 1.02

                # communication
                for other in st.session_state.nano:
                    if abs(other.x-n.x)<2 and abs(other.y-n.y)<2:
                        other.x, other.y = n.x, n.y

                # logs
                if np.random.rand()>0.95:
                    st.session_state.logs.append(
                        f"Nano-{i} detected oil at ({n.x},{n.y})"
                    )

            prod = res.production(pressure,sw)
            st.session_state.history.append(prod)

            # 3D
            fig3d = go.Figure(data=[go.Surface(z=res.grid)])
            chart.plotly_chart(fig3d, use_container_width=True)

            # Heatmap + Nano tracking
            xs = [n.x for n in st.session_state.nano]
            ys = [n.y for n in st.session_state.nano]

            fig = go.Figure()
            fig.add_trace(go.Heatmap(z=res.grid))
            fig.add_trace(go.Scatter(x=ys, y=xs, mode='markers',
                                     marker=dict(color='red', size=6)))
            heat.plotly_chart(fig, use_container_width=True)

            time.sleep(0.2)

# ===== ANALYTICS =====
with col3:
    st.header("📊 Analytics")

    base = res.production(pressure,sw)
    nano_prod = base if len(st.session_state.history)==0 else st.session_state.history[-1]

    improvement = ((nano_prod-base)/base)*100 if base>0 else 0

    revenue = nano_prod * oil_price
    npv = revenue - cost

    st.metric("Base", f"{base:.3f}")
    st.metric("Nano", f"{nano_prod:.3f}")
    st.metric("Δ%", f"{improvement:.2f}")
    st.metric("NPV", f"{npv:.2f}")

    # trend
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=st.session_state.history))
    st.plotly_chart(fig, use_container_width=True)

# ===== LOG CONSOLE =====
st.subheader("🧠 Incident Console")

for log in st.session_state.logs[-10:]:
    st.text(log)

# ===== EXPORT =====
df = pd.DataFrame({"Production": st.session_state.history})
st.download_button("📥 Export CSV", df.to_csv(), "report.csv")

# ===== STATUS =====
st.markdown("---")
st.markdown(f"""
⚡ Energy: {np.random.randint(50,100)}% |
🧠 CPU: {np.random.randint(10,90)}% |
🌐 Status: {"RUNNING" if run else "IDLE"}
""")
