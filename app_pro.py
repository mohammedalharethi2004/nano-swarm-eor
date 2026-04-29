import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import time
from datetime import datetime

st.set_page_config(layout="wide", page_title="Nano-Swarm Command Center")

# ================= STYLE =================
st.markdown("""
<style>
body {background-color:#0b0f17; color:white;}
.kpi {
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(10px);
    border:1px solid rgba(0,255,255,0.3);
    border-radius:12px;
    padding:10px;
    text-align:center;
    box-shadow:0 0 10px rgba(0,255,255,0.3);
}
.title {color:#00f0ff; font-size:32px;}
</style>
""", unsafe_allow_html=True)

# ================= MODEL =================
class Reservoir:
    def __init__(self):
        self.grid = np.random.rand(25,25)
        self.initial = self.grid.copy()

class Nano:
    def __init__(self):
        self.x = np.random.randint(0,25)
        self.y = np.random.randint(0,25)
        self.active = False

    def move(self, grid):
        gx, gy = np.gradient(grid)
        self.x = int(np.clip(self.x + gx[self.x,self.y],0,24))
        self.y = int(np.clip(self.y + gy[self.x,self.y],0,24))

# ================= SESSION =================
if "res" not in st.session_state:
    st.session_state.res = Reservoir()
    st.session_state.nano = [Nano() for _ in range(30)]
    st.session_state.logs = []
    st.session_state.history = []

res = st.session_state.res

# ================= SIDEBAR =================
page = st.sidebar.radio("Navigation", [
    "Dashboard",
    "Subsurface Live View",
    "Nano Control",
    "Analytics",
    "Economic Hub"
])

# ================= DASHBOARD =================
if page == "Dashboard":
    st.markdown('<div class="title">🛢️ Command Overview</div>', unsafe_allow_html=True)

    base = np.mean(res.grid)
    bots = len(st.session_state.nano)
    quality = np.mean(res.grid)

    c1,c2,c3 = st.columns(3)
    c1.markdown(f"<div class='kpi'>Pressure<br>{base:.2f}</div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='kpi'>Bots<br>{bots}</div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='kpi'>Quality<br>{quality:.2f}</div>", unsafe_allow_html=True)

# ================= LIVE VIEW =================
elif page == "Subsurface Live View":

    st.title("🌍 Subsurface Monitoring")

    chart = st.empty()

    for _ in range(30):
        for i,n in enumerate(st.session_state.nano):
            n.move(res.grid)

            # sensing
            if res.grid[n.x,n.y] > 0.7:
                n.active = True
                st.session_state.logs.append(
                    f"[{datetime.now().strftime('%H:%M:%S')}] Nano {i}: Oil detected at ({n.x},{n.y})"
                )

            # treatment effect
            if n.active:
                res.grid[n.x,n.y] *= 1.02

        # plotting
        xs = [n.x for n in st.session_state.nano]
        ys = [n.y for n in st.session_state.nano]
        colors = ["gold" if n.active else "cyan" for n in st.session_state.nano]

        fig = go.Figure()

        fig.add_trace(go.Surface(z=res.grid, colorscale='Viridis'))

        fig.add_trace(go.Scatter3d(
            x=xs, y=ys, z=[res.grid[x,y] for x,y in zip(xs,ys)],
            mode='markers',
            marker=dict(size=5, color=colors)
        ))

        chart.plotly_chart(fig, use_container_width=True)
        time.sleep(0.2)

# ================= CONTROL =================
elif page == "Nano Control":

    st.title("🤖 Swarm Control Panel")

    mode = st.radio("Mode", ["Auto","Manual"])

    tx = st.slider("Target X",0,24,12)
    ty = st.slider("Target Y",0,24,12)

    if st.button("Apply"):
        for n in st.session_state.nano:
            if mode=="Manual":
                n.x += np.sign(tx - n.x)
                n.y += np.sign(ty - n.y)

# ================= ANALYTICS =================
elif page == "Analytics":

    st.title("📊 Production Analytics")

    base = np.mean(res.initial)
    current = np.mean(res.grid)

    st.session_state.history.append(current)

    fig = go.Figure()
    fig.add_trace(go.Scatter(y=st.session_state.history, name="Nano"))
    fig.add_hline(y=base, line_dash="dash", name="Base")

    st.plotly_chart(fig, use_container_width=True)

    st.metric("Improvement %", f"{(current-base)/base*100:.2f}%")

# ================= ECON =================
elif page == "Economic Hub":

    st.title("💰 Economic Analysis")

    oil_price = st.number_input("Oil Price",50,150,80)
    cost = st.number_input("Cost",1000,10000,3000)

    production = np.mean(res.grid)

    revenue = production * oil_price
    npv = revenue - cost

    st.metric("Revenue", f"${revenue:.2f}")
    st.metric("NPV", f"${npv:.2f}")

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
