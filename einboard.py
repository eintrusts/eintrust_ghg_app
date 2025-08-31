import streamlit as st
import pandas as pd
import numpy as np

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

.sdg-block {
    padding: 15px; border-radius: 12px; text-align: center;
    margin-bottom: 10px; transition: transform 0.2s, box-shadow 0.2s;
}
.sdg-block:hover { transform: scale(1.03); box-shadow: 0 6px 18px rgba(0,0,0,0.5); }
.sdg-number { font-size: 20px; font-weight: 700; color: #fff; margin-bottom: 5px; }
.sdg-name { font-size: 16px; font-weight: 600; color: #ffffff; margin-bottom: 5px; }
.sdg-progress { font-size: 14px; color: #cfd8dc; margin-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Initialize session state
# ---------------------------
if "page" not in st.session_state:
    st.session_state.page = "Home"

# Placeholder dataframes for inputs
for key in ["entries", "renewable_entries", "water_entries", "waste_entries", "biodiversity_entries",
            "employee_entries", "health_safety_entries", "csr_entries", "governance_entries"]:
    if key not in st.session_state:
        st.session_state[key] = pd.DataFrame()

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
# SDG Constants
# ---------------------------
SDG_LIST = [
    "No Poverty", "Zero Hunger", "Good Health & Wellbeing", "Quality Education", "Gender Equality",
    "Clean Water & Sanitation", "Affordable & Clean Energy", "Decent Work & Economic Growth",
    "Industry, Innovation & Infrastructure", "Reduced Inequalities", "Sustainable Cities & Communities",
    "Responsible Consumption & Production", "Climate Action", "Life Below Water", "Life on Land",
    "Peace, Justice & Strong Institutions", "Partnerships for the Goals"
]
SDG_COLORS = [
    "#E5243B","#DDA63A","#4C9F38","#C5192D","#FF3A21","#26BDE2","#FCC30B",
    "#A21942","#FD6925","#DD1367","#FD9D24","#BF8B2E","#3F7E44","#0A97D9",
    "#56C02B","#00689D","#19486A"
]

# ---------------------------
# Calculate SDG Engagement dynamically
# ---------------------------
def calculate_sdg_engagement():
    sdg_engagement = {sdg:0 for sdg in SDG_LIST}

    # --- Environment ---
    total_renewable = st.session_state.renewable_entries["Energy_kWh"].sum() if not st.session_state.renewable_entries.empty else 0
    total_fossil = st.session_state.entries["Quantity"].sum() if not st.session_state.entries.empty else 0
    total_water = st.session_state.water_entries["Quantity"].sum() if not st.session_state.water_entries.empty else 0
    total_waste = st.session_state.waste_entries["Quantity"].sum() if not st.session_state.waste_entries.empty else 0
    total_biodiversity = len(st.session_state.biodiversity_entries) if not st.session_state.biodiversity_entries.empty else 0

    # --- Social ---
    total_employee = len(st.session_state.employee_entries)
    total_hs = len(st.session_state.health_safety_entries)
    total_csr = len(st.session_state.csr_entries)

    # --- Governance ---
    total_governance = len(st.session_state.governance_entries)

    # Assign % engagement to SDGs (example logic)
    sdg_engagement["Affordable & Clean Energy"] = min(100, total_renewable/100000*100)
    sdg_engagement["Responsible Consumption & Production"] = min(100, total_fossil/50000*100 + total_waste/20000*50)
    sdg_engagement["Climate Action"] = min(100, total_fossil/50000*50 + total_renewable/100000*50)
    sdg_engagement["Clean Water & Sanitation"] = min(100, total_water/50000*100)
    sdg_engagement["Life on Land"] = min(100, total_biodiversity*10)
    sdg_engagement["Good Health & Wellbeing"] = min(100, total_hs*5)
    sdg_engagement["Decent Work & Economic Growth"] = min(100, total_employee*5)
    sdg_engagement["Peace, Justice & Strong Institutions"] = min(100, total_governance*5)
    sdg_engagement["Sustainable Cities & Communities"] = min(100, total_csr*5)
    sdg_engagement["Partnerships for the Goals"] = min(100, total_csr*5)
    # other SDGs remain 0 or can be enhanced later

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
            idx = i+j
            progress = sdg_engagement.get(sdg,0)
            color = SDG_COLORS[idx % len(SDG_COLORS)]
            with cols[j]:
                st.markdown(f"""
                <div class='sdg-block' style='background-color:{color}'>
                    <div class='sdg-number'>SDG {idx+1}</div>
                    <div class='sdg-name'>{sdg}</div>
                    <div class='sdg-progress'>Engagement: {progress:.2f}%</div>
                    <progress max="100" value="{progress}" style="width:100%"></progress>
                </div>
                """, unsafe_allow_html=True)

# ---------------------------
# Placeholder pages
# ---------------------------
def render_placeholder(name):
    st.subheader(f"{name} Dashboard (Under Development)")

# ---------------------------
# Render pages
# ---------------------------
if st.session_state.page == "Home":
    st.title("EinTrust Sustainability Dashboard")
    st.info("Select a section from sidebar to explore.")
elif st.session_state.page == "GHG":
    render_placeholder("GHG")
elif st.session_state.page == "Energy":
    render_placeholder("Energy")
elif st.session_state.page == "Water":
    render_placeholder("Water")
elif st.session_state.page == "Waste":
    render_placeholder("Waste")
elif st.session_state.page == "Biodiversity":
    render_placeholder("Biodiversity")
elif st.session_state.page == "Employee":
    render_placeholder("Employee")
elif st.session_state.page == "Health & Safety":
    render_placeholder("Health & Safety")
elif st.session_state.page == "CSR":
    render_placeholder("CSR")
elif st.session_state.page in ["Board","Policies","Compliance","Risk Management"]:
    render_placeholder(st.session_state.page)
elif st.session_state.page == "SDG":
    render_sdg_dashboard()
else:
    st.subheader(f"{st.session_state.page} section")
    st.info("This section is under development. Please select other pages from sidebar.")
