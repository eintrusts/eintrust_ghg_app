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

.sidebar-button {
    width: 100%; padding: 0.4rem; border-radius: 0.3rem; text-align: left; margin-bottom: 0.2rem;
    color: #e6edf3; background-color: #12131a; border: none; font-size: 16px;
}
.sidebar-button:hover { background-color: #1a1b22; }
.sidebar-button-active { background-color: forestgreen; color: white; }
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

def sidebar_button(label, page_name):
    active = st.session_state.page == page_name
    btn_color = "sidebar-button-active" if active else "sidebar-button"
    if st.button(label, key=page_name):
        st.session_state.page = page_name
        st.experimental_rerun()
    # Apply CSS for button highlight
    st.markdown(f"""
    <style>
    div.stButton > button[key="{page_name}"] {{
        all: unset; cursor: pointer; padding: 0.4rem; text-align: left;
        border-radius: 0.3rem; margin-bottom: 0.2rem;
        background-color: {'forestgreen' if active else '#12131a'};
        color: {'white' if active else '#e6edf3'};
        font-size: 16px;
    }}
    div.stButton > button[key="{page_name}"]:hover {{
        background-color: {'forestgreen' if active else '#1a1b22'};
    }}
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.image("https://github.com/eintrusts/eintrust_ghg_app/blob/main/EinTrust%20%20(2).png?raw=true", use_container_width=True)
    st.markdown("---")

    sidebar_button("Home","Home")

    env_exp = st.expander("Environment", expanded=True)
    with env_exp:
        for name in ["GHG","Energy","Water","Waste","Biodiversity"]:
            sidebar_button(name,name)

    social_exp = st.expander("Social", expanded=False)
    with social_exp:
        for name in ["Employee","Health & Safety","CSR"]:
            sidebar_button(name,name)

    gov_exp = st.expander("Governance", expanded=False)
    with gov_exp:
        for name in ["Board","Policies","Compliance","Risk Management"]:
            sidebar_button(name,name)

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
scope_activities = {
    "Scope 1": {"Stationary Combustion": {"Diesel Generator": "Generator running on diesel",
                                          "Petrol Generator": "Generator running on petrol"},
                "Mobile Combustion": {"Diesel Vehicle": "Truck/van running on diesel"}},
    "Scope 2": {"Electricity Consumption": {"Grid Electricity": "Electricity from grid"}},
    "Scope 3": {"Business Travel": {"Air Travel": None}}
}

units_dict = {"Diesel Generator": "Liters", "Petrol Generator": "Liters", "Diesel Vehicle": "Liters",
              "Grid Electricity": "kWh"}

months = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]

SCOPE_COLORS = {"Scope 1": "#81c784", "Scope 2": "#4db6ac", "Scope 3": "#aed581"}
ENERGY_COLORS = {"Fossil": "#f39c12", "Renewable": "#2ecc71"}

# ---------------------------
# GHG & Energy dashboard functions
# (Keep all your previous logic unchanged)
# ---------------------------
# calculate_kpis(), render_ghg_dashboard(), render_energy_dashboard() ...
# (Copy all previous GHG and Energy dashboard functions here exactly as before)
# ---------------------------

# ---------------------------
# Render Pages
# ---------------------------
if st.session_state.page == "Home":
    st.title("EinTrust Sustainability Dashboard")
    render_ghg_dashboard(include_data=False, show_chart=False)
    render_energy_dashboard(include_input=False, show_chart=False)
elif st.session_state.page == "GHG":
    render_ghg_dashboard(include_data=True, show_chart=True)
elif st.session_state.page == "Energy":
    render_energy_dashboard(include_input=True, show_chart=True)
else:
    st.subheader(f"{st.session_state.page} section")
    st.info("This section is under development. Please select other pages from sidebar.")
