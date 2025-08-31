import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ---------------------------
# Config & Dark Theme CSS
# ---------------------------
st.set_page_config(page_title="EinTrust Sustainability Dashboard", page_icon="🌍", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }
.stApp { background-color: #0d1117; color: #e6edf3; }
.kpi { background: linear-gradient(145deg, #12131a, #1a1b22); padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.5); margin-bottom: 10px; min-height: 120px; display: flex; flex-direction: column; justify-content: center; align-items: center; transition: transform 0.2s, box-shadow 0.2s; }
.kpi:hover { transform: scale(1.05); box-shadow: 0 8px 20px rgba(0,0,0,0.6); }
.kpi-value { font-size: 28px; font-weight: 700; color: #ffffff; margin-bottom: 5px; }
.kpi-unit { font-size: 16px; font-weight: 500; color: #cfd8dc; margin-bottom: 5px; }
.kpi-label { font-size: 14px; color: #cfd8dc; letter-spacing: 0.5px; }
.sdg-card { border-radius: 10px; padding: 15px; margin: 8px; display: inline-block; width: 100%; min-height: 110px; text-align: left; color: white; }
.sdg-number { font-weight: 700; font-size: 20px; }
.sdg-name { font-size: 16px; margin-bottom: 5px; }
.sdg-percent { font-size: 14px; }
@media (min-width: 768px) { .sdg-card { width: 220px; display: inline-block; } }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Utilities
# ---------------------------
def format_indian(n: float) -> str:
    try:
        x = int(round(float(n)))
    except:
        return "0"
    s = str(abs(x))
    if len(s) <= 3:
        res = s
    else:
        res = s[-3:]
        s = s[:-3]
        while len(s) > 2:
            res = s[-2:] + "," + res
            s = s[:-2]
        if s:
            res = s + "," + res
    return ("-" if x < 0 else "") + res

# ---------------------------
# Initialize Session State
# ---------------------------
if "page" not in st.session_state:
    st.session_state.page = "Home"

if "entries" not in st.session_state:
    st.session_state.entries = pd.DataFrame(columns=["Scope","Activity","Sub-Activity","Specific Item","Quantity","Unit","Month"])

if "renewable_entries" not in st.session_state:
    st.session_state.renewable_entries = pd.DataFrame(columns=["Source","Location","Month","Energy_kWh","CO2e_kg","Type"])

if "water_entries" not in st.session_state:
    st.session_state.water_entries = pd.DataFrame(columns=["Month","Freshwater_kL","Recycled_kL","Rainwater_kL","STP_ETP_kL"])

if "sdg_engagement" not in st.session_state:
    st.session_state.sdg_engagement = {i:0 for i in range(1,18)}

# ---------------------------
# Constants
# ---------------------------
months = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]
SCOPE_COLORS = {"Scope 1": "#81c784", "Scope 2": "#4db6ac", "Scope 3": "#aed581"}
ENERGY_COLORS = {"Fossil": "#f39c12", "Renewable": "#2ecc71"}
SDG_LIST = [
    "No Poverty", "Zero Hunger", "Good Health & Wellbeing", "Quality Education",
    "Gender Equality", "Clean Water & Sanitation", "Affordable & Clean Energy",
    "Decent Work & Economic Growth", "Industry, Innovation & Infrastructure",
    "Reduced Inequalities", "Sustainable Cities & Communities", "Responsible Consumption & Production",
    "Climate Action", "Life Below Water", "Life on Land", "Peace, Justice & Strong Institutions",
    "Partnerships for the Goals"
]
SDG_COLORS = [ "#e5243b","#dda63a","#4c9f38","#c5192d","#ff3a21","#26bde2","#fcc30b","#a21942","#fd6925",
               "#dd1367","#fd9d24","#bf8b2e","#3f7e44","#0a97d9","#56c02b","#00689d","#19486a" ]

# ---------------------------
# Sidebar & Navigation
# ---------------------------
def sidebar_button(label):
    active = st.session_state.page == label
    if st.button(label, key=label):
        st.session_state.page = label
    st.markdown(f"""
    <style>
    div.stButton > button[key="{label}"] {{
        all: unset; cursor: pointer; padding: 0.4rem; text-align: left; border-radius: 0.3rem; margin-bottom: 0.2rem;
        background-color: {'forestgreen' if active else '#12131a'}; color: {'white' if active else '#e6edf3'}; font-size: 16px;
    }}
    div.stButton > button[key="{label}"]:hover {{ background-color: {'forestgreen' if active else '#1a1b22'}; }}
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.image("https://github.com/eintrusts/eintrust_ghg_app/blob/main/EinTrust%20%20(2).png?raw=true", use_container_width=True)
    st.markdown("---")
    sidebar_button("Home")
    env_exp = st.expander("Environment", expanded=True)
    with env_exp:
        sidebar_button("GHG")
        sidebar_button("Energy")
        sidebar_button("Water")
        sidebar_button("Waste")
        sidebar_button("Biodiversity")
    social_exp = st.expander("Social", expanded=False)
    with social_exp:
        sidebar_button("Employee")
        sidebar_button("Health & Safety")
        sidebar_button("CSR")
    gov_exp = st.expander("Governance", expanded=False)
    with gov_exp:
        sidebar_button("Board")
        sidebar_button("Policies")
        sidebar_button("Compliance")
        sidebar_button("Risk Management")
    st.markdown("---")
    sidebar_button("SDG")

# ---------------------------
# Functions to Update SDG automatically
# ---------------------------
def update_sdg_from_data():
    # Simple example: map GHG, Energy, Water usage to SDGs
    # You can customize mapping as needed
    st.session_state.sdg_engagement[6] = min(100, int(st.session_state.water_entries["Freshwater_kL"].sum()/1000) if not st.session_state.water_entries.empty else 0)
    st.session_state.sdg_engagement[7] = min(100, int((st.session_state.entries["Quantity"].sum() + st.session_state.renewable_entries["Energy_kWh"].sum())/10000) if not st.session_state.entries.empty else 0)
    st.session_state.sdg_engagement[12] = min(100, int(st.session_state.water_entries["Recycled_kL"].sum()/500) if not st.session_state.water_entries.empty else 0)
    st.session_state.sdg_engagement[13] = min(100, int(st.session_state.entries["Quantity"].sum()/1000) if not st.session_state.entries.empty else 0)

# ---------------------------
# Render Home Page (KPIs + Charts only)
# ---------------------------
def render_home():
    st.title("EinTrust Sustainability Dashboard")
    
    # --- GHG KPIs ---
    df = st.session_state.entries
    total_ghg = df["Quantity"].sum() if not df.empty else 0
    scope1 = df[df["Scope"]=="Scope 1"]["Quantity"].sum() if not df.empty else 0
    scope2 = df[df["Scope"]=="Scope 2"]["Quantity"].sum() if not df.empty else 0
    scope3 = df[df["Scope"]=="Scope 3"]["Quantity"].sum() if not df.empty else 0
    st.subheader("GHG Emissions")
    c1,c2,c3,c4 = st.columns(4)
    for col, label, value, color in zip([c1,c2,c3,c4],
                                       ["Total Quantity","Scope 1","Scope 2","Scope 3"],
                                       [total_ghg,scope1,scope2,scope3],
                                       ["#ffffff",SCOPE_COLORS["Scope 1"],SCOPE_COLORS["Scope 2"],SCOPE_COLORS["Scope 3"]]):
        col.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{color}'>{format_indian(value)}</div><div class='kpi-unit'>tCO₂e</div><div class='kpi-label'>{label.lower()}</div></div>",unsafe_allow_html=True)
    
    # --- Energy KPIs ---
    fossil_energy = st.session_state.entries["Quantity"].sum() if not df.empty else 0
    renewable_energy = st.session_state.renewable_entries["Energy_kWh"].sum() if not st.session_state.renewable_entries.empty else 0
    total_energy = fossil_energy + renewable_energy
    st.subheader("Energy")
    c1,c2,c3 = st.columns(3)
    for col,label,value,color in zip([c1,c2,c3],
                                     ["Total Energy (kWh)","Fossil Energy (kWh)","Renewable Energy (kWh)"],
                                     [total_energy,fossil_energy,renewable_energy],
                                     ["#ffffff",ENERGY_COLORS["Fossil"],ENERGY_COLORS["Renewable"]]):
        col.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{color}'>{format_indian(value)}</div><div class='kpi-unit'>kWh</div><div class='kpi-label'>{label.lower()}</div></div>",unsafe_allow_html=True)
    
    # --- Water KPIs ---
    total_fresh = st.session_state.water_entries["Freshwater_kL"].sum() if not st.session_state.water_entries.empty else 0
    total_recycled = st.session_state.water_entries["Recycled_kL"].sum() if not st.session_state.water_entries.empty else 0
    total_rain = st.session_state.water_entries["Rainwater_kL"].sum() if not st.session_state.water_entries.empty else 0
    st.subheader("Water")
    c1,c2,c3 = st.columns(3)
    for col,label,value in zip([c1,c2,c3],
                               ["Freshwater Used (kL)","Water Recycled (kL)","Rainwater Harvested (kL)"],
                               [total_fresh,total_recycled,total_rain]):
        col.markdown(f"<div class='kpi'><div class='kpi-value'>{format_indian(value)}</div><div class='kpi-unit'>kL</div><div class='kpi-label'>{label}</div></div>",unsafe_allow_html=True)
    
# ---------------------------
# Render GHG Page (with Input Form)
# ---------------------------
def render_ghg():
    st.title("GHG Emissions")
    # --- existing GHG form code here ---
    st.info("GHG form and results go here (retain your original input form and table).")

# ---------------------------
# Render Energy Page (with Input Form)
# ---------------------------
def render_energy():
    st.title("Energy")
    # --- existing Energy form code here ---
    st.info("Energy form and results go here (retain your original input form and table).")

# ---------------------------
# Render Water Page (with Input Form)
# ---------------------------
def render_water():
    st.title("Water Management")
    st.info("Water form and results go here (retain your original input form and table).")

# ---------------------------
# Render SDG Page
# ---------------------------
def render_sdg():
    st.title("Sustainable Development Goals (SDGs)")
    update_sdg_from_data()
    num_cols = 4
    rows = (len(SDG_LIST)+num_cols-1)//num_cols
    idx = 0
    for r in range(rows):
        cols = st.columns(num_cols)
        for c in range(num_cols):
            if idx>=len(SDG_LIST):
                break
            sdg_name = SDG_LIST[idx]
            sdg_color = SDG_COLORS[idx]
            sdg_number = idx+1
            engagement = st.session_state.sdg_engagement.get(sdg_number,0)
            engagement = cols[c].slider(f"Engagement % - SDG {sdg_number}",0,100,value=engagement,key=f"sdg{sdg_number}")
            st.session_state.sdg_engagement[sdg_number]=engagement
            cols[c].markdown(f"<div class='sdg-card' style='background-color:{sdg_color}'><div class='sdg-number'>SDG {sdg_number}</div><div class='sdg-name'>{sdg_name}</div><div class='sdg-percent'>Engagement: {engagement}%</div></div>", unsafe_allow_html=True)
            idx+=1

# ---------------------------
# Render Pages
# ---------------------------
if st.session_state.page=="Home":
    render_home()
elif st.session_state.page=="GHG":
    render_ghg()
elif st.session_state.page=="Energy":
    render_energy()
elif st.session_state.page=="Water":
    render_water()
elif st.session_state.page=="SDG":
    render_sdg()
else:
    st.subheader(f"{st.session_state.page} section")
    st.info("This section is under development. Please select other pages from sidebar.")
