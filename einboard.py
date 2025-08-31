import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os

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
    
    # SDG button **outside Governance expander** so always visible
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

SDG_ICONS = {
    "No Poverty": "sdg_icons/01_no_poverty.png",
    "Zero Hunger": "sdg_icons/02_zero_hunger.png",
    "Good Health & Wellbeing": "sdg_icons/03_good_health_and_wellbeing.png",
    "Quality Education": "sdg_icons/04_quality_education.png",
    "Gender Equality": "sdg_icons/05_gender_equality.png",
    "Clean Water & Sanitation": "sdg_icons/06_clean_water_and_sanitation.png",
    "Affordable & Clean Energy": "sdg_icons/07_affordable_and_clean_energy.png",
    "Decent Work & Economic Growth": "sdg_icons/08_decent_work_and_economic_growth.png",
    "Industry, Innovation & Infrastructure": "sdg_icons/09_industry_innovation_and_infrastructure.png",
    "Reduced Inequalities": "sdg_icons/10_reduced_inequalities.png",
    "Sustainable Cities & Communities": "sdg_icons/11_sustainable_cities_and_communities.png",
    "Responsible Consumption & Production": "sdg_icons/12_responsible_consumption_and_production.png",
    "Climate Action": "sdg_icons/13_climate_action.png",
    "Life Below Water": "sdg_icons/14_life_below_water.png",
    "Life on Land": "sdg_icons/15_life_on_land.png",
    "Peace, Justice & Strong Institutions": "sdg_icons/16_peace_justice_and_strong_institutions.png",
    "Partnerships for the Goals": "sdg_icons/17_partnerships_for_the_goals.png"
}

# ---------------------------
# SDG Engagement Calculation
# ---------------------------
def calculate_sdg_engagement():
    # Placeholder logic for SDG engagement calculation
    # Replace with actual logic based on your data
    sdg_engagement = {sdg: np.random.uniform(0, 100) for sdg in SDG_LIST}
    return sdg_engagement

# ---------------------------
# Render SDG Dashboard
# ---------------------------
def render_sdg_dashboard():
    st.title("Sustainable Development Goals (SDGs)")
    st.subheader("All 17 SDGs")

    sdg_engagement = calculate_sdg_engagement()

    for sdg, icon_path in SDG_ICONS.items():
        col1, col2 = st.columns([1, 4])
        with col1:
            st.image(icon_path, width=50)
        with col2:
            st.markdown(f"**{sdg}**")
            progress = sdg_engagement[sdg]
            st.progress(progress / 100)
            st.write(f"Engagement: {progress:.2f}%")

# ---------------------------
# Render Pages
# ---------------------------
if st.session_state.page == "Home":
    st.title("EinTrust Sustainability Dashboard")
    render_sdg_dashboard()
elif st.session_state.page == "GHG":
    # Placeholder for GHG dashboard
    st.subheader("GHG Dashboard")
elif st.session_state.page == "Energy":
    # Placeholder for Energy dashboard
    st.subheader("Energy Dashboard")
elif st.session_state.page == "SDG":
    render_sdg_dashboard()
else:
    st.subheader(f"{st.session_state.page} section")
    st.info("This section is under development. Please select other pages from sidebar.")
