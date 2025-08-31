import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
import io

# ---------------------------
# Config & Dark Theme CSS
# ---------------------------
st.set_page_config(page_title="EinTrust Dashboard", page_icon="🌍", layout="wide")
st.markdown("""
<style>
  .stApp { background-color: #0d1117; color: #e6edf3; }
  .kpi { background: #12131a; padding: 14px; border-radius: 10px; }
  .kpi-value { font-size: 20px; font-weight:700; }
  .kpi-label { font-size: 12px; color: #cfd8dc; }
  .stDataFrame { color: #e6edf3; }
  .sidebar .stButton>button { background:#198754; color:white; margin-bottom:5px; width:100%; }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Utilities
# ---------------------------
MONTH_ORDER = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]

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

def get_cycle_bounds(today: date):
    if today.month < 4:
        start = date(today.year - 1, 4, 1)
        end = date(today.year, 3, 31)
    else:
        start = date(today.year, 4, 1)
        end = date(today.year + 1, 3, 31)
    return start, end

# ---------------------------
# Load emission factors
# ---------------------------
try:
    emission_factors = pd.read_csv("emission_factors.csv")
except FileNotFoundError:
    emission_factors = pd.DataFrame(columns=["scope","category","activity","unit","emission_factor"])
    st.sidebar.warning("emission_factors.csv not found — add it to use prefilled activities.")

# ---------------------------
# Session state
# ---------------------------
if "emissions_log" not in st.session_state:
    st.session_state.emissions_log = []
if "emissions_summary" not in st.session_state:
    st.session_state.emissions_summary = {"Scope 1": 0.0, "Scope 2": 0.0, "Scope 3": 0.0}
if "page" not in st.session_state:
    st.session_state.page = "Home"

# ---------------------------
# Sidebar (Fixed)
# ---------------------------
with st.sidebar:
    st.image("https://github.com/eintrusts/eintrust_ghg_app/raw/main/EinTrust%20%20logo.png", use_container_width=True)
    st.markdown("---")
    
    # Home button
    if st.button("Home", key="btn_home"):
        st.session_state.page = "Home"

    # Environment dropdown
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

    # Social dropdown
    social_exp = st.expander("Social", expanded=False)
    with social_exp:
        if st.button("Employee", key="btn_employee"):
            st.session_state.page = "Employee"
        if st.button("Health & Safety", key="btn_hs"):
            st.session_state.page = "Health & Safety"
        if st.button("CSR", key="btn_csr"):
            st.session_state.page = "CSR"

    # Governance dropdown
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
# Main Content
# ---------------------------
st.title("🌍 EinTrust Sustainability Dashboard")

# ---------------------------
# GHG Manual Entry Data
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

if 'entries' not in st.session_state:
    st.session_state.entries = pd.DataFrame(columns=["Scope","Activity","Sub-Activity","Specific Item","Quantity","Unit"])

def render_ghg_dashboard(include_data=True):
    st.subheader("GHG Emissions Dashboard")
    st.markdown("Estimate Scope 1, 2, and 3 emissions for net zero journey.")

    # KPIs
    s1 = st.session_state.emissions_summary.get("Scope 1", 0.0)
    s2 = st.session_state.emissions_summary.get("Scope 2", 0.0)
    s3 = st.session_state.emissions_summary.get("Scope 3", 0.0)
    total = s1 + s2 + s3

    SCOPE_COLORS = {"Scope 1": "#81c784", "Scope 2": "#4db6ac", "Scope 3": "#aed581"}

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"<div class='kpi'><div class='kpi-value' style='color:white'>{format_indian(total)}</div><div class='kpi-label'>Total Emissions (tCO₂e)</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{SCOPE_COLORS['Scope 1']}'>{format_indian(s1)}</div><div class='kpi-label'>Scope 1 (tCO₂e)</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{SCOPE_COLORS['Scope 2']}'>{format_indian(s2)}</div><div class='kpi-label'>Scope 2 (tCO₂e)</div></div>", unsafe_allow_html=True)
    with c4:
        st.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{SCOPE_COLORS['Scope 3']}'>{format_indian(s3)}</div><div class='kpi-label'>Scope 3 (tCO₂e)</div></div>", unsafe_allow_html=True)

    if include_data:
        st.subheader("➕ Add Manual Activity Data")

        # Scope selection
        scope = st.selectbox("Select Scope", list(scope_activities.keys()))
        activity = st.selectbox("Select Activity / Category", list(scope_activities[scope].keys()))
        sub_options = scope_activities[scope][activity]

        if scope != "Scope 3":
            sub_activity = st.selectbox("Select Sub-Activity", list(sub_options.keys()))
            st.info(sub_options[sub_activity])
        else:
            sub_activity = st.selectbox("Select Sub-Category", list(sub_options.keys()))

        specific_item = None
        if scope == "Scope 3":
            items = scope_activities[scope][activity][sub_activity]
            if items is not None:
                specific_item = st.selectbox("Select Specific Item", items)

        unit = None
        if scope != "Scope 3":
            unit = units_dict.get(sub_activity, "")
        else:
            if sub_activity in ["Air Travel"]:
                unit = "Number of flights"
            else:
                unit = "km / kg / Tonnes"

        quantity = st.number_input(f"Enter Quantity ({unit})", min_value=0.0, format="%.2f")

        # File upload for cross-verification
        st.subheader("Optional: Upload File")
        uploaded_file = st.file_uploader("Upload CSV/XLS/XLSX/PDF", type=["csv","xls","xlsx","pdf"])

        # Add Manual Entry
        if st.button("Add Entry"):
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

        # Display Entries
        if not st.session_state.entries.empty:
            st.subheader("All Entries")
            display_df = st.session_state.entries.copy()
            display_df["Quantity"] = display_df["Quantity"].apply(lambda x: f"{x:,.2f}")
            st.dataframe(display_df)

            # Download CSV
            def convert_df(df):
                return df.to_csv(index=False).encode('utf-8')
            csv = convert_df(st.session_state.entries)
            st.download_button("Download All Entries as CSV", csv, "ghg_entries.csv", "text/csv")

# ---------------------------
# Render pages
# ---------------------------
if st.session_state.page == "Home":
    render_ghg_dashboard(include_data=False)   # Home: only KPIs
elif st.session_state.page == "GHG":
    render_ghg_dashboard(include_data=True)    # GHG: full manual entry
else:
    st.subheader(f"{st.session_state.page} Section")
    st.info("This section is under development. Please select other pages from sidebar.")
