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
# Sidebar & Navigation (dynamic)
# ---------------------------
if "page" not in st.session_state:
    st.session_state.page = "Home"

# Page structure for dynamic generation
sidebar_structure = {
    "Home": [],
    "Environment": ["GHG","Energy","Water","Waste","Biodiversity"],
    "Social": ["Employee","Health & Safety","CSR"],
    "Governance": ["Board","Policies","Compliance","Risk Management"]
}

def render_sidebar(structure):
    st.image("https://github.com/eintrusts/eintrust_ghg_app/blob/main/EinTrust%20%20(2).png?raw=true", use_container_width=True)
    st.markdown("---")
    for section, pages in structure.items():
        if section != "Home":
            exp = st.expander(section, expanded=(section=="Environment"))
            with exp:
                for page_name in pages:
                    active = st.session_state.page == page_name
                    if st.button(page_name, key=page_name):
                        st.session_state.page = page_name
                        st.experimental_rerun()
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
    # Home button separately on top
    active = st.session_state.page == "Home"
    if st.button("Home", key="Home"):
        st.session_state.page = "Home"
        st.experimental_rerun()
    st.markdown(f"""
    <style>
    div.stButton > button[key="Home"] {{
        all: unset; cursor: pointer; padding: 0.4rem; text-align: left;
        border-radius: 0.3rem; margin-bottom: 0.2rem;
        background-color: {'forestgreen' if active else '#12131a'};
        color: {'white' if active else '#e6edf3'};
        font-size: 16px;
    }}
    div.stButton > button[key="Home"]:hover {{
        background-color: {'forestgreen' if active else '#1a1b22'};
    }}
    </style>
    """, unsafe_allow_html=True)

# Render sidebar dynamically
with st.sidebar:
    render_sidebar(sidebar_structure)

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
# (Keep all previous logic for calculate_kpis(), render_ghg_dashboard(), render_energy_dashboard() here exactly as before)
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
