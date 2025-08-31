import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
import io

# ---------------------------
# Config & Dark Theme CSS with professional dashboard look
# ---------------------------
st.set_page_config(page_title="EinTrust Dashboard", page_icon="🌍", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Roboto', sans-serif;
}

.stApp { background-color: #0d1117; color: #e6edf3; }

/* KPI boxes */
.kpi {
    background: linear-gradient(145deg, #12131a, #1a1b22);
    padding: 20px;
    border-radius: 12px;
    text-align: center;
    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    margin-bottom: 10px;
    min-height: 120px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    transition: transform 0.2s, box-shadow 0.2s;
}
.kpi:hover {
    transform: scale(1.05);
    box-shadow: 0 8px 20px rgba(0,0,0,0.6);
}
.kpi-value {
    font-size: 28px;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 5px;
}
.kpi-unit {
    font-size: 16px;
    font-weight: 500;
    color: #cfd8dc;
    margin-bottom: 5px;
}
.kpi-label {
    font-size: 14px;
    color: #cfd8dc;
    letter-spacing: 0.5px;
}

/* Dataframe styling */
.stDataFrame { color: #e6edf3; font-family: 'Roboto', sans-serif; }

/* Sidebar buttons */
.sidebar .stButton>button { 
    background:#198754; color:white; margin-bottom:5px; width:100%; font-family: 'Roboto', sans-serif; 
}
.stSelectbox, .stNumberInput, .stFileUploader, .stDownloadButton {
    font-family: 'Roboto', sans-serif;
}
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
# Load emission factors (optional)
# ---------------------------
try:
    emission_factors = pd.read_csv("emission_factors.csv")
except FileNotFoundError:
    emission_factors = pd.DataFrame(columns=["scope","category","activity","unit","emission_factor"])
    st.sidebar.warning("emission_factors.csv not found — add it to use prefilled activities.")

# ---------------------------
# Session state
# ---------------------------
if "entries" not in st.session_state:
    st.session_state.entries = pd.DataFrame(columns=["Scope","Activity","Sub-Activity","Specific Item","Quantity","Unit"])
if "page" not in st.session_state:
    st.session_state.page = "Home"

# ---------------------------
# Sidebar
# ---------------------------
with st.sidebar:
    st.image("https://github.com/eintrusts/eintrust_ghg_app/raw/main/EinTrust%20%20logo.png", use_container_width=True)
    st.markdown("---")
    
    if st.button("Home", key="btn_home"):
        st.session_state.page = "Home"

    env_exp = st.expander("Environment", expanded=True)
    with env_exp:
        if st.button("GHG", key="btn_ghg"):
            st.session_state.page = "GHG"
        if st.button("Energy", key="btn_energy"):
            st.session_state.page = "Energy"
        if st.button("Water", key="btn_water"):
            st.session_state.page = "Water"
        if st.button("Waste", key="btn_waste"):
            st.session_state.page = "Waste"
        if st.button("Biodiversity", key="btn_bio"):
            st.session_state.page = "Biodiversity"

    social_exp = st.expander("Social", expanded=False)
    with social_exp:
        if st.button("Employee", key="btn_employee"):
            st.session_state.page = "Employee"
        if st.button("Health & Safety", key="btn_hs"):
            st.session_state.page = "Health & Safety"
        if st.button("CSR", key="btn_csr"):
            st.session_state.page = "CSR"

    gov_exp = st.expander("Governance", expanded=False)
    with gov_exp:
        if st.button("Board", key="btn_board"):
            st.session_state.page = "Board"
        if st.button("Policies", key="btn_policies"):
            st.session_state.page = "Policies"
        if st.button("Compliance", key="btn_compliance"):
            st.session_state.page = "Compliance"
        if st.button("Risk Management", key="btn_risk"):
            st.session_state.page = "Risk Management"

# ---------------------------
# Main content
# ---------------------------
st.title("🌍 EinTrust Sustainability Dashboard")

scope_activities = {
    "Scope 1": {"Stationary Combustion": {"Diesel Generator": "Generator running on diesel",
                                          "Petrol Generator": "Generator running on petrol"},
                "Mobile Combustion": {"Diesel Vehicle": "Truck/van running on diesel"}},
    "Scope 2": {"Electricity Consumption": {"Grid Electricity": "Electricity from grid"}},
    "Scope 3": {"Business Travel": {"Air Travel": None}}
}

units_dict = {"Diesel Generator": "Liters", "Petrol Generator": "Liters", "Diesel Vehicle": "Liters",
              "Grid Electricity": "kWh"}

# ---------------------------
# Functions
# ---------------------------
def calculate_kpis():
    df = st.session_state.entries
    summary = {"Scope 1": 0.0, "Scope 2": 0.0, "Scope 3": 0.0, "Total Quantity": 0.0, "Unit": "tCO₂e"}
    if not df.empty:
        for scope in ["Scope 1","Scope 2","Scope 3"]:
            summary[scope] = df[df["Scope"]==scope]["Quantity"].sum()
        summary["Total Quantity"] = df["Quantity"].sum()
    return summary

def render_ghg_dashboard(include_data=True):
    st.subheader("GHG emissions dashboard")
    
    kpis = calculate_kpis()
    SCOPE_COLORS = {"Scope 1": "#81c784", "Scope 2": "#4db6ac", "Scope 3": "#aed581"}

    c1, c2, c3, c4 = st.columns(4)
    for col, label, value, color in zip(
        [c1, c2, c3, c4], 
        ["Total Quantity", "Scope 1", "Scope 2", "Scope 3"],
        [kpis['Total Quantity'], kpis['Scope 1'], kpis['Scope 2'], kpis['Scope 3']],
        ["#ffffff", SCOPE_COLORS['Scope 1'], SCOPE_COLORS['Scope 2'], SCOPE_COLORS['Scope 3']]
    ):
        col.markdown(f"""
        <div class='kpi'>
            <div class='kpi-value' style='color:{color}'>{format_indian(value)}</div>
            <div class='kpi-unit'>{kpis['Unit']}</div>
            <div class='kpi-label'>{label.lower()}</div>
        </div>
        """, unsafe_allow_html=True)

    if include_data:
        st.subheader("Add activity data")
        scope = st.selectbox("Select scope", list(scope_activities.keys()))
        activity = st.selectbox("Select activity / category", list(scope_activities[scope].keys()))
        sub_options = scope_activities[scope][activity]

        if scope != "Scope 3":
            sub_activity = st.selectbox("Select sub-activity", list(sub_options.keys()))
            st.info(sub_options[sub_activity])
        else:
            sub_activity = st.selectbox("Select sub-category", list(sub_options.keys()))

        specific_item = None
        if scope == "Scope 3":
            items = scope_activities[scope][activity][sub_activity]
            if items is not None:
                specific_item = st.selectbox("Select specific item", items)

        unit = units_dict.get(sub_activity, "Number of flights" if sub_activity=="Air Travel" else "km / kg / tonnes")
        quantity = st.number_input(f"Enter quantity ({unit})", min_value=0.0, format="%.2f")
        uploaded_file = st.file_uploader("Upload CSV/XLS/XLSX/PDF for cross verification (optional)", type=["csv","xls","xlsx","pdf"])

        if st.button("Add entry"):
            new_entry = {
                "Scope": scope,
                "Activity": activity,
                "Sub-Activity": sub_activity,
                "Specific Item": specific_item if specific_item else "",
                "Quantity": quantity,
                "Unit": unit
            }
            st.session_state.entries = pd.concat([st.session_state.entries, pd.DataFrame([new_entry])], ignore_index=True)
            st.success("Entry added successfully!")
            st.experimental_rerun()

        if not st.session_state.entries.empty:
            st.subheader("All entries")
            display_df = st.session_state.entries.copy()
            display_df["Quantity"] = display_df["Quantity"].apply(lambda x: format_indian(x))
            st.dataframe(display_df)
            csv = display_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download all entries as CSV", csv, "ghg_entries.csv", "text/csv")

# ---------------------------
# Render pages
# ---------------------------
if st.session_state.page == "Home":
    render_ghg_dashboard(include_data=False)
elif st.session_state.page == "GHG":
    render_ghg_dashboard(include_data=True)
else:
    st.subheader(f"{st.session_state.page} section")
    st.info("This section is under development. Please select other pages from sidebar.")
