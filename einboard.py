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

.kpi {
    background: linear-gradient(145deg, #12131a, #1a1b22);
    padding: 20px; border-radius: 12px; text-align: center;
    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    margin-bottom: 10px; min-height: 120px;
    display: flex; flex-direction: column; justify-content: center; align-items: center;
    transition: transform 0.2s, box-shadow 0.2s;
}
.kpi:hover { transform: scale(1.05); box-shadow: 0 8px 20px rgba(0,0,0,0.6); }
.kpi-value { font-size: 28px; font-weight: 700; color: #ffffff; margin-bottom: 5px; }
.kpi-unit { font-size: 16px; font-weight: 500; color: #cfd8dc; margin-bottom: 5px; }
.kpi-label { font-size: 14px; color: #cfd8dc; letter-spacing: 0.5px; }
.stDataFrame { color: #e6edf3; font-family: 'Roboto', sans-serif; }

.sdg-block {
    background: linear-gradient(145deg, #12131a, #1a1b22);
    padding: 15px; border-radius: 12px; text-align: center;
    margin-bottom: 10px; transition: transform 0.2s, box-shadow 0.2s;
}
.sdg-block:hover { transform: scale(1.03); box-shadow: 0 6px 18px rgba(0,0,0,0.5); }
.sdg-name { font-size: 16px; font-weight: 600; color: #ffffff; margin-bottom: 5px; }
.sdg-progress { font-size: 14px; color: #cfd8dc; margin-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Utilities
# ---------------------------
def format_indian(n: float) -> str:
    try:
        x = int(round(float(n)))
    except Exception:
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
# Sidebar & Navigation
# ---------------------------
if "page" not in st.session_state:
    st.session_state.page = "Home"

def sidebar_button(label):
    active = st.session_state.page == label
    if st.button(label, key=label):
        st.session_state.page = label
    st.markdown(f"""
    <style>
    div.stButton > button[key="{label}"] {{
        all: unset; cursor: pointer; padding: 0.4rem; text-align: left;
        border-radius: 0.3rem; margin-bottom: 0.2rem;
        background-color: {'forestgreen' if active else '#12131a'};
        color: {'white' if active else '#e6edf3'};
        font-size: 16px;
    }}
    div.stButton > button[key="{label}"]:hover {{
        background-color: {'forestgreen' if active else '#1a1b22'};
    }}
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
# Initialize Data
# ---------------------------
if "entries" not in st.session_state:
    st.session_state.entries = pd.DataFrame(columns=["Scope","Activity","Sub-Activity","Specific Item","Quantity","Unit"])
if "renewable_entries" not in st.session_state:
    st.session_state.renewable_entries = pd.DataFrame(columns=["Source","Location","Month","Energy_kWh","CO2e_kg","Type"])

# ---------------------------
# Constants
# ---------------------------
SDG_LIST = [
    "No Poverty", "Zero Hunger", "Good Health & Wellbeing", "Quality Education", "Gender Equality",
    "Clean Water & Sanitation", "Affordable & Clean Energy", "Decent Work & Economic Growth",
    "Industry, Innovation & Infrastructure", "Reduced Inequalities", "Sustainable Cities & Communities",
    "Responsible Consumption & Production", "Climate Action", "Life Below Water", "Life on Land",
    "Peace, Justice & Strong Institutions", "Partnerships for the Goals"
]

# ---------------------------
# SDG Engagement Calculation
# ---------------------------
def calculate_sdg_engagement():
    sdg_engagement = {sdg:0 for sdg in SDG_LIST}

    # SDG 7: Affordable & Clean Energy
    renewable_df = st.session_state.renewable_entries
    total_renewable_energy = renewable_df["Energy_kWh"].sum() if not renewable_df.empty else 0
    benchmark_renewable = 100000
    sdg_engagement["Affordable & Clean Energy"] = min(100, (total_renewable_energy / benchmark_renewable)*100)

    # SDG 12: Responsible Consumption & Production
    fossil_energy = st.session_state.entries[st.session_state.entries["Scope"].isin(["Scope 1","Scope 2"])]["Quantity"].sum() if not st.session_state.entries.empty else 0
    benchmark_fossil = 50000
    sdg_engagement["Responsible Consumption & Production"] = min(100, (fossil_energy / benchmark_fossil)*100)

    # SDG 13: Climate Action
    total_ghg = st.session_state.entries["Quantity"].sum() if not st.session_state.entries.empty else 0
    benchmark_ghg = 10000
    sdg_engagement["Climate Action"] = min(100, (total_ghg / benchmark_ghg)*100)

    return sdg_engagement

# ---------------------------
# Render SDG Dashboard
# ---------------------------
def render_sdg_dashboard():
    st.title("Sustainable Development Goals (SDGs)")
    st.subheader("Company Engagement on All 17 SDGs")

    sdg_engagement = calculate_sdg_engagement()
    cols_per_row = 3
    for i in range(0, len(SDG_LIST), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, sdg in enumerate(SDG_LIST[i:i+cols_per_row]):
            with cols[j]:
                progress = sdg_engagement[sdg]
                st.markdown(f"""
                <div class='sdg-block'>
                    <div class='sdg-name'>{sdg}</div>
                    <div class='sdg-progress'>Engagement: {progress:.2f}%</div>
                    <progress max="100" value="{progress}" style="width:100%"></progress>
                </div>
                """, unsafe_allow_html=True)

# ---------------------------
# Placeholder functions for GHG and Energy dashboards
# ---------------------------
def render_ghg_dashboard():
    st.subheader("GHG Dashboard (Under Development)")

def render_energy_dashboard():
    st.subheader("Energy Dashboard (Under Development)")

# ---------------------------
# Render Pages
# ---------------------------
if st.session_state.page == "Home":
    st.title("EinTrust Sustainability Dashboard")
    st.info("Select a section from sidebar to explore.")
elif st.session_state.page == "GHG":
    render_ghg_dashboard()
elif st.session_state.page == "Energy":
    render_energy_dashboard()
elif st.session_state.page == "SDG":
    render_sdg_dashboard()
else:
    st.subheader(f"{st.session_state.page} section")
    st.info("This section is under development. Please select other pages from sidebar.")
