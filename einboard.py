import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import plotly.express as px

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
# Session state
# ---------------------------
if "entries" not in st.session_state:
    st.session_state.entries = pd.DataFrame(columns=["Scope","Activity","Sub-Activity","Specific Item","Quantity","Unit"])
if "energy_entries" not in st.session_state:
    st.session_state.energy_entries = pd.DataFrame(columns=["Source","Location","Month","Energy_kWh","CO2e_kg","Type"])
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
# GHG module
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

def calculate_kpis():
    df = st.session_state.entries
    summary = {"Scope 1": 0.0, "Scope 2": 0.0, "Scope 3": 0.0, "Total Quantity": 0.0, "Unit": "tCO₂e"}
    if not df.empty:
        for scope in ["Scope 1","Scope 2","Scope 3"]:
            summary[scope] = df[df["Scope"]==scope]["Quantity"].sum()
        summary["Total Quantity"] = df["Quantity"].sum()
    return summary

def render_kpis(kpis, title="", colors=None):
    cols = st.columns(len(kpis)-1)
    for col,label in zip(cols,list(kpis.keys())[:-1]):
        value = kpis[label]
        color = colors.get(label, "#ffffff") if colors else "#ffffff"
        col.markdown(f"""
        <div class='kpi'>
            <div class='kpi-value' style='color:{color}'>{format_indian(value)}</div>
            <div class='kpi-unit'>{kpis['Unit']}</div>
            <div class='kpi-label'>{label.lower()}</div>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------
# Energy module
# ---------------------------
months = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]
emission_factors_energy = {"Diesel":2.68,"Petrol":2.31,"LPG":1.51,"CNG":2.02,"Coal":2.42,
                           "Electricity":0.82,"Solar":0.0,"Wind":0.0,"Purchased Green Energy":0.0,"Biogas":0.0}

def get_energy_kpis():
    df = st.session_state.energy_entries
    total = df["Energy_kWh"].sum() if not df.empty else 0
    fossil = df[df["Type"]=="Fossil"]["Energy_kWh"].sum() if not df.empty else 0
    renewable = df[df["Type"]=="Renewable"]["Energy_kWh"].sum() if not df.empty else 0
    return {"Total":total,"Fossil":fossil,"Renewable":renewable,"Unit":"kWh"}

def render_energy_dashboard(include_entry=True):
    st.subheader("Energy & CO₂e dashboard")
    
    energy_kpis = get_energy_kpis()
    render_kpis(energy_kpis,"Energy consumption",{"Total":"#ffffff","Fossil":"#f06292","Renewable":"#4db6ac"})
    
    if include_entry:
        st.subheader("Add renewable energy entry (annual)")
        num_entries = st.number_input("Number of entries to add",1,10,1)
        renewable_list = []
        for i in range(int(num_entries)):
            col1,col2,col3 = st.columns([2,3,3])
            with col1:
                source = st.selectbox(f"Source {i+1}", ["Solar","Wind","Biogas","Purchased Green Energy"], key=f"src{i}")
            with col2:
                location = st.text_input(f"Location {i+1}", "", key=f"loc{i}")
            with col3:
                annual_energy = st.number_input(f"Annual energy kWh {i+1}",0.0,key=f"annual{i}")
            monthly_energy = annual_energy/12
            for m in months:
                st.session_state.energy_entries = pd.concat([st.session_state.energy_entries,
                    pd.DataFrame([{"Source":source,"Location":location,"Month":m,"Energy_kWh":monthly_energy,
                                   "CO2e_kg":monthly_energy*emission_factors_energy.get(source,0),
                                   "Type":"Renewable"}])],ignore_index=True)
        
        # Monthly trend with fossil & renewable
        df = st.session_state.energy_entries.copy()
        if not df.empty:
            df_trend = df.groupby(["Month","Type"]).sum().reset_index()
            df_trend["Month"] = pd.Categorical(df_trend["Month"], categories=months, ordered=True)
            st.subheader("Monthly energy trend (kWh)")
            fig = px.bar(df_trend, x="Month", y="Energy_kWh", color="Type", barmode="stack",
                         color_discrete_map={"Fossil":"#f06292","Renewable":"#4db6ac"})
            st.plotly_chart(fig,use_container_width=True)

# ---------------------------
# Combine fossil fuel from GHG to energy_entries
# ---------------------------
def update_energy_from_ghg():
    df = st.session_state.entries
    for _,row in df.iterrows():
        # Only fuels in units_dict (Diesel Generator, etc.)
        fuel_name = row["Sub-Activity"]
        if fuel_name in ["Diesel Generator","Petrol Generator","Diesel Vehicle","Grid Electricity"]:
            unit = row["Unit"]
            qty = row["Quantity"]
            co2e = qty * emission_factors_energy.get("Diesel" if "Diesel" in fuel_name else "Petrol",0) if "Generator" in fuel_name or "Vehicle" in fuel_name else qty*0.82
            st.session_state.energy_entries = pd.concat([st.session_state.energy_entries,
                pd.DataFrame([{"Source":fuel_name,"Location":"Default","Month":m,"Energy_kWh":qty if "Electricity" in fuel_name else 0,
                               "CO2e_kg":co2e,"Type":"Fossil"} for m in months])],ignore_index=True)

# ---------------------------
# Render pages
# ---------------------------
update_energy_from_ghg()

if st.session_state.page=="Home":
    st.subheader("Home dashboard")
    render_kpis(calculate_kpis(),"GHG",{"Total Quantity":"#ffffff","Scope 1":"#81c784","Scope 2":"#4db6ac","Scope 3":"#aed581"})
    render_energy_dashboard(include_entry=False)
elif st.session_state.page=="GHG":
    render_kpis(calculate_kpis(),"GHG",{"Total Quantity":"#ffffff","Scope 1":"#81c784","Scope 2":"#4db6ac","Scope 3":"#aed581"})
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
    quantity = st.number_input(f"Enter quantity ({unit})",min_value=0.0,format="%.2f")
    uploaded_file = st.file_uploader("Upload CSV/XLS/XLSX/PDF for cross verification (optional)", type=["csv","xls","xlsx","pdf"])
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
        st.download_button("Download all entries as CSV",csv,"ghg_entries.csv","text/csv")
elif st.session_state.page=="Energy":
    render_energy_dashboard(include_entry=True)
else:
    st.subheader(f"{st.session_state.page} section")
    st.info("This section is under development. Please select other pages from sidebar.")
