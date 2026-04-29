import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import interp1d
import time, random, datetime

st.set_page_config(layout="wide")

# ================= THEME =================
st.markdown("""
<style>
body {background:#0b0f17; color:white; font-family: 'Roboto Mono', monospace;}

.card {
    background:rgba(255,255,255,0.05);
    border:1px solid cyan;
    border-radius:15px;
    padding:15px;
    box-shadow:0 0 20px cyan;
}
.log-green {color:#00ff9c;}
.log-red {color:#ff4d4d;}
.log-yellow {color:#ffd166;}
</style>
""", unsafe_allow_html=True)

# ================= DATA =================
@st.cache_data
def load():
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

visc, kro, pc, pro = load()

# ================= MODEL =================
class Reservoir:
    def __init__(self):
        self.grid = np.random.rand(25,25)

    def production(self,p):
        mu = float(visc(p))
        sw = np.mean(self.grid)
        return (float(kro(sw))*(p-float(pc(sw)))/1000)/(mu+1e-6)

class Nano:
    def __init__(self):
        self.x = np.random.randint(0,25)
        self.y = np.random.randint(0,25)

    def move(self,grid,dx=0,dy=0):
        gx, gy = np.gradient(grid)
        self.x = int(np.clip(self.x + gx[self.x,self.y] + dx,0,24))
        self.y = int(np.clip(self.y + gy[self.x,self.y] + dy,0,24))

# ================= SESSION =================
if "res" not in st.session_state:
    st.session_state.res = Reservoir()
    st.session_state.nano = [Nano() for _ in range(30)]
    st.session_state.logs=[]
    st.session_state.run=False
    st.session_state.dx=0
    st.session_state.dy=0
    st.session_state.start=time.time()
    st.session_state.series=[]

res = st.session_state.res

# ================= TABS =================
tabs = st.tabs(["Dashboard","Subsurface","Control","Analytics","Economics","Field Map"])

# ================= DASHBOARD =================
with tabs[0]:
    st.title("⚡ Energy Command Dashboard")

    p = st.slider("Pressure",500,3000,1500)

    base = pro.select_dtypes(include=np.number).mean().mean()
    nano = res.production(p)

    c1,c2,c3 = st.columns(3)
    c1.markdown(f"<div class='card'>Traditional<br>{base:.2f}</div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='card'>Nano<br>{nano:.2f}</div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='card'>Lift<br>{((nano-base)/base*100):.2f}%</div>", unsafe_allow_html=True)

    # SCADA Gauges
    fig = go.Figure(go.Indicator(mode="gauge+number",value=nano,
        title={'text':"Total Production"},
        gauge={'axis':{'range':[0, max(1,nano*2)]}}))
    st.plotly_chart(fig, use_container_width=True)

    st.write(f"🕒 Time: {datetime.datetime.now()}")
    st.write(f"⚡ CPU: {random.randint(10,80)}%")

# ================= SUBSURFACE =================
with tabs[1]:
    st.title("🌍 Digital Twin")

    chart = st.empty()

    if st.session_state.run:
        for n in st.session_state.nano:
            n.move(res.grid, st.session_state.dx, st.session_state.dy)

        xs=[n.x for n in st.session_state.nano]
        ys=[n.y for n in st.session_state.nano]

        fig=go.Figure()
        fig.add_trace(go.Surface(z=res.grid, colorscale="Turbo"))
        fig.add_trace(go.Scatter3d(x=xs,y=ys,z=[res.grid[x,y] for x,y in zip(xs,ys)],
                                  mode='markers',
                                  marker=dict(size=5,color='cyan')))
        chart.plotly_chart(fig, use_container_width=True)

        time.sleep(0.3)
        st.rerun()

# ================= CONTROL =================
with tabs[2]:
    st.title("🎮 Mission Control")

    c1,c2,c3 = st.columns(3)

    # Health Monitor
    for col,title,val in zip([c1,c2,c3],
        ["Signal","Battery","Connectivity"],
        [random.randint(60,100),random.randint(50,100),random.randint(70,100)]):

        fig = go.Figure(go.Indicator(mode="gauge",value=val,
            title={'text':title},
            gauge={'axis':{'range':[0,100]}}))
        col.plotly_chart(fig)

    # Manual Joystick
    st.subheader("Manual Control")
    col1,col2,col3 = st.columns(3)
    if col2.button("↑"): st.session_state.dx=-1
    if col1.button("←"): st.session_state.dy=-1
    if col3.button("→"): st.session_state.dy=1
    if st.button("↓"): st.session_state.dx=1

    # E-STOP
    if st.button("🛑 EMERGENCY STOP"):
        st.session_state.run=False
        st.session_state.logs.append(("ERROR","Emergency Stop Activated"))

    if st.button("▶ START"):
        st.session_state.run=True
        st.session_state.logs.append(("INFO","System Started"))

# ================= ANALYTICS =================
with tabs[3]:
    st.title("📈 AI Analytics")

    base = pro.select_dtypes(include=np.number).mean().mean()
    nano = res.production(1500)

    st.session_state.series.append(nano)

    y=np.array(st.session_state.series)
    x=np.arange(len(y))

    slope = (y[-1]-y[-5])/5 if len(y)>5 else 0
    future = [y[-1]+slope*i for i in range(1,10)]

    fig=go.Figure()

    fig.add_trace(go.Scatter(y=y,name="Nano",line=dict(color="cyan",width=4)))
    fig.add_trace(go.Scatter(y=[base]*len(y),name="Traditional",
                            line=dict(dash='dash',color='white')))

    # Prediction + Confidence
    upper=[f*1.1 for f in future]
    lower=[f*0.9 for f in future]

    fig.add_trace(go.Scatter(y=future,name="AI Prediction",line=dict(color="gold")))
    fig.add_trace(go.Scatter(y=upper,opacity=0.2,showlegend=False))
    fig.add_trace(go.Scatter(y=lower,fill='tonexty',opacity=0.2,name="Confidence"))

    fig.update_layout(height=600, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    st.info(random.choice([
        "[AI] Analyzing patterns...",
        "[AI] Optimizing flow...",
        "[AI] Predicting ROI..."
    ]))

# ================= ECON =================
with tabs[4]:
    st.title("💰 Economics")

    oil = st.number_input("Oil Price",50,150,80)
    cost = st.number_input("Cost",1000,20000,5000)

    prod = res.production(1500)
    revenue = prod*oil
    npv = revenue-cost

    st.metric("Revenue",f"${revenue:.2f}")
    st.metric("NPV",f"${npv:.2f}")

    df = pd.DataFrame({"Production":[prod],"NPV":[npv]})
    st.download_button("Export",df.to_csv(),"report.csv")

# ================= FIELD MAP =================
with tabs[5]:
    st.title("🗺️ Field Map")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=np.random.rand(10),y=np.random.rand(10),
                             mode='markers',name="Wells"))
    st.plotly_chart(fig, use_container_width=True)

# ================= LOG =================
st.markdown("### 🧠 Event Console")
for t,msg in st.session_state.logs[-10:]:
    if t=="ERROR":
        st.markdown(f"<span class='log-red'>{msg}</span>",unsafe_allow_html=True)
    elif t=="INFO":
        st.markdown(f"<span class='log-green'>{msg}</span>",unsafe_allow_html=True)
    else:
        st.markdown(f"<span class='log-yellow'>{msg}</span>",unsafe_allow_html=True)
