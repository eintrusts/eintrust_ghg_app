import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
import io
import plotly.express as px

# ---------------------------
# Config & Dark Theme CSS
# ---------------------------
st.set_page_config(page_title="EinTrust Dashboard", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }
.stApp { background-color: #0d1117; color: #e6edf3; }

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
.kpi:hover { transform: scale(1.05); box-shadow: 0 8px 20px rgba(0,0,0,0.6); }
.kpi-value { font-size: 28px; font-weight: 700; color: #ffffff; margin-bottom: 5px; }
.kpi-unit { font-size: 16px; font-weight: 500; color: #cfd8dc; margin-bottom: 5px; }
.kpi-label { font-size: 14px; color: #cfd8dc; letter-spacing: 0.5px; }

.stDataFrame { color: #e6edf3; font-family: 'Roboto', sans-serif; }
.sidebar .stButton>button { background:#198754; color:white; margin-bottom:5px; width:100%; font-family: 'Roboto', sans-serif; }
.stSelectbox, .stNumberInput, .stFileUploader, .stDownloadButton { font-family: 'Roboto', sans-serif; }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Utilities
# ---------------------------
def format_indian(n: float) -> str:
    try:
        x = int(round(float(n)))
    except:
        return "0"
    s = str(abs(x))
    if len(s) <= 3: res = s
    else:
        res = s[-3:]
        s = s[:-3]
        while len(s) > 2:
            res = s[-2:] + "," + res
            s = s[:-2]
        if s: res = s + "," + res
    return ("-" if x < 0 else "") + res

MONTHS = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]

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
if "renewable_list" not in st.session_state:
    st.session_state.renewable_list = []
if "page" not in st.session_state:
    st.session_state.page = "Home"

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
# Main title
# ---------------------------
st.title("EinTrust Sustainability Dashboard")

# ---------------------------
# KPI renderer
# ---------------------------
def render_kpis(kpi_dict, title, colors=None, unit="tCO₂e"):
    st.subheader(title)
    cols = st.columns(len(kpi_dict))
    for col, (label,value) in zip(cols,kpi_dict.items()):
        color = colors.get(label, "#ffffff") if colors else "#ffffff"
        col.markdown(f"""
        <div class='kpi'>
            <div class='kpi-value' style='color:{color}'>{format_indian(value)}</div>
            <div class='kpi-unit'>{unit}</div>
            <div class='kpi-label'>{label.lower()}</div>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------
# Scope setup
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
# GHG KPI computation
# ---------------------------
def compute_ghg_kpis():
    df = st.session_state.entries
    kpis = {"Total":0.0, "Scope 1":0.0, "Scope 2":0.0, "Scope 3":0.0}
    if not df.empty:
        for scope in ["Scope 1","Scope 2","Scope 3"]:
            kpis[scope] = df[df["Scope"]==scope]["Quantity"].sum()
        kpis["Total"] = df["Quantity"].sum()
    return kpis

# ---------------------------
# Energy KPI computation
# ---------------------------
CAL_VALUES = {"Diesel":35.8,"Petrol":34.2,"LPG":46.1,"CNG":48,"Coal":24,"Biomass":15}
EM_FACTORS = {"Diesel":2.68,"Petrol":2.31,"LPG":1.51,"CNG":2.02,"Coal":2.42,"Biomass":0.0,
              "Electricity":0.82,"Solar":0.0,"Wind":0.0,"Purchased Green Energy":0.0,"Biogas":0.0}

def compute_energy_kpis():
    # Fossil from GHG entries
    df = st.session_state.entries
    fossil = df[df["Scope"].isin(["Scope 1","Scope 2"])].copy()
    fossil["CO2e_kg"] = fossil.apply(lambda r: r["Quantity"]*EM_FACTORS.get(r["Sub-Activity"],0), axis=1)
    fossil_energy = fossil["Quantity"].sum()
    fossil_co2e = fossil["CO2e_kg"].sum()
    # Renewable
    renewable = pd.DataFrame(st.session_state.renewable_list)
    renewable_energy = renewable["Energy_kWh"].sum() if not renewable.empty else 0
    renewable_co2e = renewable["CO2e_kg"].sum() if not renewable.empty else 0
    total_energy = fossil_energy + renewable_energy
    total_co2e = fossil_co2e + renewable_co2e
    return {"Total":total_energy,"Fossil":fossil_energy,"Renewable":renewable_energy}, \
           {"Total":total_co2e,"Fossil":fossil_co2e,"Renewable":renewable_co2e}, fossil, renewable

# ---------------------------
# Render GHG page
# ---------------------------
def render_ghg_dashboard(include_data=True):
    colors = {"Total":"#ffffff","Scope 1":"#f06292","Scope 2":"#4db6ac","Scope 3":"#aed581"}
    kpis = compute_ghg_kpis()
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
        if scope=="Scope 3":
            items = sub_options[sub_activity]
            if items: specific_item = st.selectbox("Select specific item", items)

        unit = units_dict.get(sub_activity,"Number of flights" if sub_activity=="Air Travel" else "km / kg / tonnes")
        quantity = st.number_input(f"Enter quantity ({unit})", min_value=0.0, format="%.2f")
        uploaded_file = st.file_uploader("Upload CSV/XLS/XLSX/PDF for cross verification (optional)", type=["csv","xls","xlsx","pdf"])

        if st.button("Add entry"):
            new_entry = {"Scope":scope,"Activity":activity,"Sub-Activity":sub_activity,"Specific Item":specific_item if specific_item else "",
                         "Quantity":quantity,"Unit":unit}
            st.session_state.entries = pd.concat([st.session_state.entries,pd.DataFrame([new_entry])], ignore_index=True)
            st.success("Entry added successfully!")
            st.experimental_rerun()

        if not st.session_state.entries.empty:
            st.subheader("All entries")
            display_df = st.session_state.entries.copy()
            display_df["Quantity"] = display_df["Quantity"].apply(format_indian)
            st.dataframe(display_df)
            csv = display_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download all entries as CSV", csv, "ghg_entries.csv", "text/csv")

# ---------------------------
# Render Energy page
# ---------------------------
def render_energy_dashboard(include_entry=True):
    colors = {"Total":"#ffffff","Fossil":"#f06292","Renewable":"#4db6ac"}
    energy_kpis, co2e_kpis, fossil_df, renewable_df = compute_energy_kpis()
    render_kpis(energy_kpis,"Energy Consumption",colors,unit="kWh")
    render_kpis(co2e_kpis,"CO₂e Emissions",colors,unit="kg")

    # Monthly trend
    fossil_df = fossil_df.copy()
    fossil_df["Month"] = pd.Categorical(fossil_df["Unit"], categories=MONTHS, ordered=True)
    renewable_df = renewable_df.copy()
    renewable_df["Month"] = pd.Categorical(renewable_df["Month"] if "Month" in renewable_df else MONTHS[0], categories=MONTHS, ordered=True)
    if not fossil_df.empty or not renewable_df.empty:
        monthly_trend = pd.DataFrame()
        if not fossil_df.empty:
            monthly_trend = fossil_df.groupby("Sub-Activity")[["Quantity"]].sum().reset_index()
            monthly_trend.rename(columns={"Quantity":"Fossil"}, inplace=True)
        if not renewable_df.empty:
            monthly_trend["Renewable"] = renewable_df["Energy_kWh"].sum()
        st.subheader("Monthly Energy Consumption Trend")
        fig = px.bar(monthly_trend, x=monthly_trend.index, y=["Fossil","Renewable"], barmode="stack",
                     labels={"value":"Energy (kWh)","index":"Month"})
        st.plotly_chart(fig, use_container_width=True)

    if include_entry:
        st.subheader("Add Renewable Energy Entry")
        col1,col2,col3 = st.columns([2,2,2])
        with col1: source = st.selectbox("Source", ["Solar","Wind","Biogas","Purchased Green Energy"])
        with col2: location = st.text_input("Location","")
        with col3: annual_energy = st.number_input("Annual Energy kWh", min_value=0.0)
        if st.button("Add Renewable Energy Entry"):
            monthly_energy = annual_energy/12
            for m in MONTHS:
                st.session_state.renewable_list.append({"Source":source,"Location":location,"Month":m,"Energy_kWh":monthly_energy,
                                                         "Type":"Renewable","CO2e_kg":monthly_energy*EM_FACTORS.get(source,0)})
            st.success("Renewable entry added!")
            st.experimental_rerun()

# ---------------------------
# Render Home
# ---------------------------
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
