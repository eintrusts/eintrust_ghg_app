import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date

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
# Sidebar
# ---------------------------
with st.sidebar:
    st.image("https://github.com/eintrusts/eintrust_ghg_app/raw/main/EinTrust%20%20logo.png", use_container_width=True)
    st.markdown("---")
    if st.button("Home"):
        st.session_state.page = "Home"

    # Environment dropdown
    env_exp = st.expander("Environment", expanded=True)
    with env_exp:
        if st.button("GHG"):
            st.session_state.page = "GHG"
        if st.button("Energy"):
            st.session_state.page = "Energy"
        if st.button("Water"):
            st.session_state.page = "Water"
        if st.button("Waste"):
            st.session_state.page = "Waste"
        if st.button("Biodiversity"):
            st.session_state.page = "Biodiversity"

    # Social dropdown
    social_exp = st.expander("Social", expanded=False)
    with social_exp:
        if st.button("Employee"):
            st.session_state.page = "Employee"
        if st.button("Health & Safety"):
            st.session_state.page = "Health & Safety"
        if st.button("CSR"):
            st.session_state.page = "CSR"

    # Governance dropdown
    gov_exp = st.expander("Governance", expanded=False)
    with gov_exp:
        if st.button("Board"):
            st.session_state.page = "Board"
        if st.button("Policies"):
            st.session_state.page = "Policies"
        if st.button("Compliance"):
            st.session_state.page = "Compliance"
        if st.button("Risk Management"):
            st.session_state.page = "Risk Management"

# ---------------------------
# Main Content
# ---------------------------
st.title("🌍 EinTrust Dashboard")

# ---------------------------
# GHG Manual Entry Data Setup
# ---------------------------
scope_activities = {
    "Scope 1": {
        "Stationary Combustion": {
            "Diesel Generator": "Generator running on diesel for electricity",
            "Petrol Generator": "Generator running on petrol for electricity",
            "LPG Boiler": "Boiler or stove using LPG",
            "Coal Boiler": "Boiler/furnace burning coal",
            "Biomass Furnace": "Furnace burning wood/agricultural residue"
        },
        "Mobile Combustion": {
            "Diesel Vehicle": "Truck/van running on diesel",
            "Petrol Car": "Car/van running on petrol",
            "CNG Vehicle": "Bus or delivery vehicle running on CNG",
            "Diesel Forklift": "Forklift running on diesel",
            "Petrol Two-Wheeler": "Scooter or bike running on petrol"
        }
    },
    "Scope 2": {
        "Electricity Consumption": {"Grid Electricity": "Electricity bought from grid"},
        "Steam / Heat": {"Purchased Steam": "Steam bought externally"},
    },
    "Scope 3": {
        "Purchased Goods & Services": {
            "Raw Materials": ["Cement", "Steel", "Chemicals", "Textile"],
            "Packaging Materials": ["Cardboard", "Plastics", "Glass"]
        },
        "Business Travel": {"Air Travel": None, "Train Travel": None}
    }
}

units_dict = {
    "Diesel Generator": "Liters",
    "Petrol Generator": "Liters",
    "LPG Boiler": "Liters",
    "Coal Boiler": "kg",
    "Biomass Furnace": "kg",
    "Diesel Vehicle": "Liters",
    "Petrol Car": "Liters",
    "CNG Vehicle": "m³",
    "Diesel Forklift": "Liters",
    "Petrol Two-Wheeler": "Liters",
    "Grid Electricity": "kWh",
    "Purchased Steam": "Tonnes"
}

if 'entries' not in st.session_state:
    st.session_state.entries = pd.DataFrame(columns=["Scope","Activity","Sub-Activity","Specific Item","Quantity","Unit"])

# ---------------------------
# Manual Entry
# ---------------------------
scope = st.selectbox("Select Scope", ["Scope 1", "Scope 2", "Scope 3"])
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
    elif sub_activity in ["Train Travel"]:
        unit = "km traveled"
    else:
        unit = "kg / Tonnes"

quantity = st.number_input(f"Enter Quantity ({unit})", min_value=0.0, format="%.2f")

# -----------------------------
# File Upload for Cross Verification
# -----------------------------
st.subheader("Optional: Upload File for Cross Verification")
uploaded_file = st.file_uploader("Upload CSV / XLS / XLSX / PDF (Internal Only)", 
                                 type=["csv","xls","xlsx","pdf"])
if uploaded_file:
    if uploaded_file.name.endswith(".pdf"):
        st.info("PDF uploaded for internal verification. Results will not be affected.")
    else:
        try:
            if uploaded_file.name.endswith(".csv"):
                df_file = pd.read_csv(uploaded_file)
            else:
                df_file = pd.read_excel(uploaded_file)
            st.info("File uploaded for internal verification. Results will not be affected.")
        except Exception as e:
            st.error(f"Error reading file: {e}")

# -----------------------------
# Add Manual Entry
# -----------------------------
if st.button("Add Manual Entry"):
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

# -----------------------------
# Display Entries Table
# -----------------------------
if not st.session_state.entries.empty:
    st.subheader("All Entries")
    display_df = st.session_state.entries.copy()
    display_df["Quantity"] = display_df["Quantity"].apply(lambda x: f"{x:,.2f}")
    st.dataframe(display_df)

    def convert_df(df):
        return df.to_csv(index=False).encode('utf-8')

    csv = convert_df(st.session_state.entries)
    st.download_button("Download All Entries as CSV", csv, "ghg_entries.csv", "text/csv")

# ---------------------------
# Render Pages
# ---------------------------
def render_ghg_dashboard():
    st.subheader("🌱 GHG Emissions Dashboard")
    st.markdown("Manual entries only. Charts and trends are disabled on this page.")

if st.session_state.page == "Home":
    st.subheader("🌱 GHG Emissions Dashboard")
    st.markdown("Home page: shows KPIs only (no Add Activity, no charts).")
elif st.session_state.page == "GHG":
    render_ghg_dashboard()
else:
    st.subheader(f"{st.session_state.page} Section")
    st.info("This section is under development. Please select other pages from sidebar.")
