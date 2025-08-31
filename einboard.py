import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
import io
import plotly.express as px

# ---------------------------
# Config & Dark Theme CSS
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
MONTHS = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]

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
if "energy_entries" not in st.session_state:
    st.session_state.energy_entries = pd.DataFrame(columns=["Source","Location","Month","Energy_kWh","CO2e_kg","Type"])

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
# Scope activities for GHG
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

# ---------------------------
# Energy constants
# ---------------------------
calorific_values = {  # MJ/unit
    "Diesel": 35.8,
    "Petrol": 34.2,
    "LPG": 46.1,
    "CNG": 48,
    "Coal": 24,
    "Biomass": 15
}
emission_factors = {  # kg CO2e/unit
    "Diesel": 2.68,
    "Petrol": 2.31,
    "LPG": 1.51,
    "CNG": 2.02,
    "Coal": 2.42,
    "Biomass": 0.0,
    "Electricity": 0.82,
    "Solar": 0.0,
    "Wind": 0.0,
    "Purchased Green Energy": 0.0,
    "Biogas": 0.0
}

# ---------------------------
# Helper functions
# ---------------------------
def calculate_ghg_kpis():
    df = st.session_state.entries
    summary = {"Scope 1": 0.0, "Scope 2": 0.0, "Scope 3": 0.0, "Total": 0.0, "Unit": "tCO₂e"}
    if not df.empty:
        for scope in ["Scope 1","Scope 2","Scope 3"]:
            summary[scope] = df[df["Scope"]==scope]["Quantity"].sum()
        summary["Total"] = df["Quantity"].sum()
    return summary

def render_kpis(kpis, title="", colors=None):
    st.subheader(title)
    c1, c2, c3, c4 = st.columns(4)
    labels = ["Total","Scope 1","Scope 2","Scope 3"]
    for col, label in zip([c1,c2,c3,c4], labels):
        value = format_indian(kpis.get(label,0))
        color = colors.get(label,"#ffffff") if colors else "#ffffff"
        unit = kpis.get("Unit","")
        col.markdown(f"""
        <div class='kpi'>
            <div class='kpi-value' style='color:{color}'>{value}</div>
            <div class='kpi-unit'>{unit}</div>
            <div class='kpi-label'>{label.lower()}</div>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------
# GHG Dashboard
# ---------------------------
def render_ghg_dashboard(include_data=True):
    kpis = calculate_ghg_kpis()
    colors = {"Total":"#ffffff","Scope 1":"#81c784","Scope 2":"#4db6ac","Scope 3":"#aed581"}
    render_kpis(kpis,"GHG emissions dashboard",colors)

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
# Energy Dashboard
# ---------------------------
def render_energy_dashboard(include_entry=True):
    # Fetch fossil fuel data from GHG entries
    fossil_entries = st.session_state.entries.copy()
    fossil_entries = fossil_entries[fossil_entries["Scope"].isin(["Scope 1","Scope 2"])]
    fossil_list = []
    for _, row in fossil_entries.iterrows():
        fuel = row.get("Sub-Activity","")
        qty = row["Quantity"]
        if fuel in calorific_values:
            energy_kwh = (qty * calorific_values[fuel])/3.6
        elif fuel=="Grid Electricity":
            energy_kwh = qty
        else:
            energy_kwh = qty
        co2e = qty * emission_factors.get(fuel,0)
        for m in MONTHS:
            fossil_list.append({"Source":fuel,"Location":"N/A","Month":m,"Energy_kWh":energy_kwh/12,"CO2e_kg":co2e/12,"Type":"Fossil"})
    
    # Combine with renewable entries
    renewable_df = st.session_state.energy_entries.copy()
    all_energy = pd.concat([pd.DataFrame(fossil_list), renewable_df], ignore_index=True) if not renewable_df.empty else pd.DataFrame(fossil_list)
    
    # KPIs
    total_energy = all_energy.groupby("Type")["Energy_kWh"].sum().to_dict()
    energy_kpis = {"Total": sum(total_energy.values()),"Fossil":total_energy.get("Fossil",0),"Renewable":total_energy.get("Renewable",0),"Unit":"kWh"}
    colors = {"Total":"#ffffff","Fossil":"#f06292","Renewable":"#4db6ac"}
    render_kpis(energy_kpis,"Energy Consumption",colors)
    
    # Monthly trend (stacked bar)
    if not all_energy.empty:
        monthly_trend = all_energy.groupby(["Month","Type"])["Energy_kWh"].sum().reset_index()
        monthly_trend["Month"] = pd.Categorical(monthly_trend["Month"], categories=MONTHS, ordered=True)
        fig = px.bar(monthly_trend, x="Month", y="Energy_kWh", color="Type", barmode="stack",
                     labels={"Energy_kWh":"Energy (kWh)","Month":"Month"}, title="Monthly Energy Consumption (Fossil & Renewable)")
        st.plotly_chart(fig,use_container_width=True)
    
    # Entry form for renewable
    if include_entry:
        st.subheader("Add Renewable Energy (Annual) per Location & Source")
        num_entries = st.number_input("Number of renewable energy entries to add", min_value=1, max_value=20, value=1)
        renewable_list = []
        for i in range(int(num_entries)):
            col1, col2, col3 = st.columns([2,3,3])
            with col1:
                source = st.selectbox(f"Source {i+1}", ["Solar","Wind","Biogas","Purchased Green Energy"], key=f"src{i}")
            with col2:
                location = st.text_input(f"Location {i+1}", "", key=f"loc{i}")
            with col3:
                annual_energy = st.number_input(f"Annual Energy kWh {i+1}", min_value=0.0, key=f"annual_{i}")
            monthly_energy = annual_energy/12
            for m in MONTHS:
                renewable_list.append({"Source":source,"Location":location,"Month":m,"Energy_kWh":monthly_energy,"CO2e_kg":monthly_energy*emission_factors.get(source,0),"Type":"Renewable"})
        if renewable_list:
            st.session_state.energy_entries = pd.concat([st.session_state.energy_entries, pd.DataFrame(renewable_list)], ignore_index=True)
            st.success("Renewable entries added!")

# ---------------------------
# Page Rendering
# ---------------------------
st.title("🌍 EinTrust Sustainability Dashboard")

if st.session_state.page=="Home":
    render_ghg_dashboard(include_data=False)
    render_energy_dashboard(include_entry=False)
elif st.session_state.page=="GHG":
    render_ghg_dashboard(include_data=True)
elif st.session_state.page=="Energy":
    render_energy_dashboard(include_entry=True)
else:
    st.subheader(f"{st.session_state.page} section")
    st.info("This section is under development. Please select other pages from sidebar.")
