import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from scipy.interpolate import interp1d

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Nano-Swarm EOR Pro", layout="wide")

# --- 2. محرك تحميل البيانات (Excel Engine) ---
@st.cache_data
def load_and_interpolate():
    # تحميل الملفات
    # ملاحظة: إذا كانت الملفات الأخرى (PVTO, Data) تحتوي أيضاً على أسطر زائدة، 
    # أضف إليها header=6 كما فعلنا مع Pro.xlsx
    pvto = pd.read_excel("PVTO.xlsx")
    rel_perm = pd.read_excel("Data.xlsx")
    # تحميل Pro.xlsx مع تجاوز أول 6 أسطر
    por_data = pd.read_excel("Pro.xlsx", header=6)
    
    # تنظيف أسماء الأعمدة (تعديل جوهري لتجنب KeyError)
    pvto.columns = pvto.columns.str.strip().str.lower()
    rel_perm.columns = rel_perm.columns.str.strip().str.lower()
    por_data.columns = por_data.columns.str.strip().str.lower()

    # التحقق من وجود الأعمدة
    required_pvto = ['pressure', 'oil viscosity']
    required_rel = ['sw', 'kro']
    required_por = ['x', 'y', 'porosity']

    for col in required_pvto:
        if col not in pvto.columns:
            st.error(f"❌ عمود ناقص في PVTO.xlsx: {col}. الأعمدة الموجودة: {pvto.columns.tolist()}")
            st.stop()

    for col in required_rel:
        if col not in rel_perm.columns:
            st.error(f"❌ عمود ناقص في Data.xlsx: {col}. الأعمدة الموجودة: {rel_perm.columns.tolist()}")
            st.stop()

    for col in required_por:
        if col not in por_data.columns:
            st.error(f"❌ عمود ناقص في Pro.xlsx: {col}. الأعمدة الموجودة: {por_data.columns.tolist()}")
            st.stop()

    # إنشاء دوال interpolation
    visc_func = interp1d(
        pvto['pressure'],
        pvto['oil viscosity'],
        kind='linear',
        fill_value="extrapolate"
    )

    kro_func = interp1d(
        rel_perm['sw'],
        rel_perm['kro'],
        kind='linear',
        fill_value="extrapolate"
    )
    
    return visc_func, kro_func, por_data

# استدعاء الدالة
visc_func, kro_func, por_data = load_and_interpolate()

# --- 3. كلاس المكمن ---
class Reservoir:
    def __init__(self):
        try:
            grid_data = por_data.pivot_table(
                values='porosity',
                index='y',
                columns='x'
            )
        except Exception as e:
            st.error(f"❌ خطأ في بناء شبكة المكمن (Grid): {e}")
            st.stop()

        grid_data = grid_data.fillna(0)

        if grid_data.empty:
            st.error("❌ بيانات المكمن فارغة")
            st.stop()

        self.grid = grid_data.values
        
    def get_darcy_production(self, pressure, sw):
        mu = max(float(visc_func(pressure)), 1e-6)
        kr = float(kro_func(sw))
        k = np.mean(self.grid)

        dp = pressure / 1000
        A, L = 1, 1 
        
        q = (k * kr * A * dp) / mu
        return float(q)

# --- 4. كلاس السرب ---
class SwarmAgent:
    def __init__(self, size_x, size_y):
        self.x = np.random.randint(0, size_x)
        self.y = np.random.randint(0, size_y)

    def move(self, oil_grid, pheromone_grid):
        score_grid = oil_grid + (pheromone_grid * 0.5)
        padded = np.pad(score_grid, pad_width=1, mode='constant', constant_values=0)

        px, py = self.x + 1, self.y + 1
        local = padded[px-1:px+2, py-1:py+2]

        idx = np.argmax(local)

        self.x = np.clip(self.x + (idx // 3) - 1, 0, oil_grid.shape[0]-1)
        self.y = np.clip(self.y + (idx % 3) - 1, 0, oil_grid.shape[1]-1)

# --- 5. الواجهة ---
st.title("🛢️ Nano-Swarm EOR Industrial Prototype")

with st.sidebar:
    pressure = st.slider("ضغط المكمن (PSI)", 500, 3000, 1500)
    sw = st.slider("تشبع الماء (Sw)", 0.25, 0.8, 0.4)

    if st.button("إعادة تعيين المحاكاة"):
        st.session_state.res = Reservoir()
        st.session_state.swarm = [SwarmAgent(20, 20) for _ in range(20)]
        st.session_state.ph_grid = np.zeros((20, 20))
        st.rerun()

# تهيئة
if 'res' not in st.session_state:
    st.session_state.res = Reservoir()
    st.session_state.swarm = [SwarmAgent(20, 20) for _ in range(20)]
    st.session_state.ph_grid = np.zeros((20, 20))

# --- 6. المحاكاة ---
without_swarm = st.session_state.res.get_darcy_production(pressure, sw)
mu = max(float(visc_func(pressure)), 1e-6)

for bot in st.session_state.swarm:
    bot.move(st.session_state.res.grid, st.session_state.ph_grid)

    effect = 0.01 * (1 / mu)

    x, y = bot.x, bot.y

    st.session_state.res.grid[x, y] = max(
        st.session_state.res.grid[x, y] - effect, 0
    )

    st.session_state.ph_grid[x, y] += 0.1

# تقليل الفيرومونات
st.session_state.ph_grid *= 0.95

with_swarm = st.session_state.res.get_darcy_production(pressure, sw)

# --- 7. النتائج ---
col1, col2, col3 = st.columns(3)

col1.metric("الإنتاج الأساسي", f"{without_swarm:.4f}")
col2.metric("الإنتاج المحسن", f"{with_swarm:.4f}")

improvement = 0
if without_swarm != 0:
    improvement = ((with_swarm - without_swarm) / without_swarm) * 100

col3.metric("نسبة التحسن (KPI)", f"{improvement:.2f}%")

# --- 8. الرسم ---
st.plotly_chart(
    px.imshow(
        st.session_state.res.grid,
        title="خريطة المكمن - توزيع النفط والمسامية"
    ),
    use_container_width=True
)

