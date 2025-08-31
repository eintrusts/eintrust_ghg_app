import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import plotly.express as px

# ---------------------------
# Config & Dark Theme CSS
# ---------------------------
st.set_page_config(page_title="EinTrust Dashboard", page_icon="🌍", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }
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
    transform: scale(1.03);
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
.stSelectbox, .stNumberInput, .stFileUploader, .stDownloadButton { font-family: 'Roboto', sans-serif; }
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
# Session state
# ---------------------------
if "entries" not in st.session_state:
    st.session_state.entries = pd.DataFrame(columns=["Scope","Activity","Sub-Activity","Specific Item","Quantity","Unit"])
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "renewable_list" not in st.session_state:
    st.session_state.renewable_list = []

# ---------------------------
# Sidebar
# ---------------------------
with st.sidebar:
    st.image("https://github.com/eintrusts/eintrust_ghg_app/raw/main/EinTrust%20%20logo.png", use_container_width=True)
    st.markdown("---")
    
    if st.button("Home", key="btn_home"): st.session_state.page = "Home"
    
    env_exp = st.expander("Environment", expanded=True)
    with env_exp:
        if st.button("GHG", key="btn_ghg"): st.session_state.page = "GHG"
        if st.button("Energy", key="btn_energy"): st.session_state.page = "Energy"
        if st.button("Water", key="btn_water"): st.session_state.page = "Water"
        if st.button("Waste", key="btn_waste"): st.session_state.page = "Waste"
        if st.button("Biodiversity", key="btn_bio"): st.session_state.page = "Biodiversity"

    social_exp = st.expander("Social", expanded=False)
    with social_exp:
        if st.button("Employee", key="btn_employee"): st.session_state.page = "Employee"
        if st.button("Health & Safety", key="btn_hs"): st.session_state.page = "Health & Safety"
        if st.button("CSR", key="btn_csr"): st.session_state.page = "CSR"

    gov_exp = st.expander("Governance", expanded=False)
    with gov_exp:
        if st.button("Board", key="btn_board"): st.session_state.page = "Board"
        if st.button("Policies", key="btn_policies"): st.session_state.page = "Policies"
        if st.button("Compliance", key="btn_compliance"): st.session_state.page = "Compliance"
        if st.button("Risk Management", key="btn_risk"): st.session_state.page = "Risk Management"

# ---------------------------
# Scope / Units
# ---------------------------
scope_activities = {
    "Scope 1": {"Stationary Combustion": {"Diesel Generator": "Generator running on diesel",
                                          "Petrol Generator": "Generator running on petrol"},
                "Mobile Combustion": {"Diesel Vehicle": "Truck/van running on diesel"}},
    "Scope 2": {"Electricity Consumption": {"Grid Electricity": "Electricity from grid"}},
    "Scope 3": {"Business Travel": {"Air Travel": None}}
}
units_dict = {"Diesel Generator": "Liters", "Petrol Generator": "Liters", "Diesel Vehicle": "Liters", "Grid Electricity": "kWh"}

# ---------------------------
# Energy Constants
# ---------------------------
calorific_values = {  # MJ/unit
    "Diesel": 35.8, "Petrol": 34.2, "LPG": 46.1, "CNG": 48, "Coal": 24, "Biomass": 15
}
emission_factors_energy = {  # kg CO2e/unit
    "Diesel": 2.68, "Petrol": 2.31, "LPG": 1.51, "CNG": 2.02, "Coal": 2.42, "Biomass": 0.0,
    "Electricity": 0.82, "Solar": 0.0, "Wind": 0.0, "Purchased Green Energy": 0.0, "Biogas": 0.0
}
months = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]

# ---------------------------
# Functions
# ---------------------------
def calculate_ghg_kpis():
    df = st.session_state.entries
    summary = {"Scope 1":0.0,"Scope 2":0.0,"Scope 3":0.0,"Total Quantity":0.0,"Unit":"tCO₂e"}
    if not df.empty:
        for scope in ["Scope 1","Scope 2","Scope 3"]:
            summary[scope] = df[df["Scope"]==scope]["Quantity"].sum()
        summary["Total Quantity"] = df["Quantity"].sum()
    return summary

def render_kpis(kpi_dict, title, colors=None):
    st.subheader(title)
    cols = st.columns(len(kpi_dict))
    for col, (label, value) in zip(cols, kpi_dict.items()):
        color = colors[label] if colors else "#ffffff"
        col.markdown(f"""
        <div class='kpi'>
            <div class='kpi-value' style='color:{color}'>{format_indian(value)}</div>
            <div class='kpi-unit'>tCO₂e</div>
            <div class='kpi-label'>{label.lower()}</div>
        </div>
        """, unsafe_allow_html=True)

def get_energy_from_ghg():
    """Extract fossil fuel energy from GHG entries for Energy dashboard"""
    df = st.session_state.entries
    if df.empty: return pd.DataFrame(columns=["Fuel_Source","Month","Energy_kWh","CO2e_kg"])
    records = []
    for _, row in df.iterrows():
        fuel = row["Sub-Activity"]
        qty = row["Quantity"]
        if fuel in calorific_values:
            energy_kwh = (qty * calorific_values[fuel])/3.6
            co2e = qty * emission_factors_energy.get(fuel,0)
            for m in months:
                records.append({"Fuel_Source":fuel,"Month":m,"Energy_kWh":energy_kwh/12,"CO2e_kg":co2e/12})
    return pd.DataFrame(records)

def render_ghg_dashboard(include_data=True):
    kpis = calculate_ghg_kpis()
    colors = {"Total Quantity":"#ffffff","Scope 1":"#81c784","Scope 2":"#4db6ac","Scope 3":"#aed581"}
    render_kpis(kpis,"GHG emissions dashboard",colors)
    
    if include_data:
        st.subheader("Add activity data")
        scope = st.selectbox("Select scope", list(scope_activities.keys()))
        activity = st.selectbox("Select activity / category", list(scope_activities[scope].keys()))
        sub_options = scope_activities[scope][activity]

        if scope!="Scope 3":
            sub_activity = st.selectbox("Select sub-activity", list(sub_options.keys()))
            st.info(sub_options[sub_activity])
        else:
            sub_activity = st.selectbox("Select sub-category", list(sub_options.keys()))

        specific_item = None
        if scope=="Scope 3":
            items = scope_activities[scope][activity][sub_activity]
            if items is not None:
                specific_item = st.selectbox("Select specific item", items)

        unit = units_dict.get(sub_activity,"Number of flights" if sub_activity=="Air Travel" else "km / kg / tonnes")
        quantity = st.number_input(f"Enter quantity ({unit})", min_value=0.0, format="%.2f")
        uploaded_file = st.file_uploader("Upload CSV/XLS/XLSX/PDF (optional)", type=["csv","xls","xlsx","pdf"])

        if st.button("Add entry"):
            new_entry = {"Scope":scope,"Activity":activity,"Sub-Activity":sub_activity,
                         "Specific Item":specific_item if specific_item else "",
                         "Quantity":quantity,"Unit":unit}
            st.session_state.entries = pd.concat([st.session_state.entries,pd.DataFrame([new_entry])],ignore_index=True)
            st.success("Entry added successfully!")
            st.experimental_rerun()

        if not st.session_state.entries.empty:
            st.subheader("All entries")
            display_df = st.session_state.entries.copy()
            display_df["Quantity"] = display_df["Quantity"].apply(lambda x: format_indian(x))
            st.dataframe(display_df)
            csv = display_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download all entries as CSV", csv, "ghg_entries.csv","text/csv")

def render_energy_dashboard(include_entry=True):
    st.subheader("Energy dashboard")
    # -------------------
    # Fossil energy from GHG
    fossil_df = get_energy_from_ghg()
    # -------------------
    # Renewable energy from session state
    renewable_df = pd.DataFrame(st.session_state.renewable_list)
    all_energy = pd.concat([fossil_df,renewable_df],ignore_index=True) if not renewable_df.empty else fossil_df
    if all_energy.empty: all_energy = pd.DataFrame(columns=["Fuel_Source","Month","Energy_kWh","CO2e_kg"])
    
    # KPI totals
    total_energy = all_energy["Energy_kWh"].sum()
    fossil_energy = fossil_df["Energy_kWh"].sum() if not fossil_df.empty else 0
    renewable_energy = renewable_df["Energy_kWh"].sum() if not renewable_df.empty else 0
    total_co2e = all_energy["CO2e_kg"].sum()
    fossil_co2e = fossil_df["CO2e_kg"].sum() if not fossil_df.empty else 0
    renewable_co2e = renewable_df["CO2e_kg"].sum() if not renewable_df.empty else 0
    
    kpis = {"Total":"Total Energy","Fossil":"Fossil Energy","Renewable":"Renewable Energy"}
    kpi_values = {"Total":total_energy,"Fossil":fossil_energy,"Renewable":renewable_energy}
    colors = {"Total":"#ffffff","Fossil":"#f06292","Renewable":"#4db6ac"}
    
    cols = st.columns(3)
    for col,label in zip(cols,["Total","Fossil","Renewable"]):
        col.markdown(f"""
        <div class='kpi'>
            <div class='kpi-value' style='color:{colors[label]}'>{format_indian(kpi_values[label])}</div>
            <div class='kpi-unit'>kWh</div>
            <div class='kpi-label'>{kpis[label].lower()}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Monthly trend stacked bar
    if not all_energy.empty:
        monthly_trend = all_energy.groupby(["Month","Fuel_Source"]).sum().reset_index()
        fig = px.bar(monthly_trend,
