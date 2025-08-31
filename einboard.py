import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import plotly.express as px

# ---------------------------
# Config & Dark Theme
# ---------------------------
st.set_page_config(page_title="EinTrust Dashboard", page_icon="🌍", layout="wide")
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
}
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
def format_indian(n):
    try:
        x = int(round(float(n)))
    except:
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
# Session State
# ---------------------------
if "entries" not in st.session_state:
    st.session_state.entries = pd.DataFrame(columns=["Scope","Activity","Sub-Activity","Specific Item","Quantity","Unit"])
if "renewable_entries" not in st.session_state:
    st.session_state.renewable_entries = pd.DataFrame(columns=["Source","Location","Month","Energy_kWh","CO2e_kg","Type"])
if "page" not in st.session_state:
    st.session_state.page = "Home"

# ---------------------------
# Constants
# ---------------------------
months = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]
calorific_values = {"Diesel":35.8,"Petrol":34.2,"LPG":46.1,"CNG":48,"Coal":24,"Biomass":15}
emission_factors = {"Diesel":2.68,"Petrol":2.31,"LPG":1.51,"CNG":2.02,"Coal":2.42,"Biomass":0.0,"Electricity":0.82,
                    "Solar":0.0,"Wind":0.0,"Purchased Green Energy":0.0,"Biogas":0.0}

# ---------------------------
# Sidebar
# ---------------------------
with st.sidebar:
    st.image("https://github.com/eintrusts/eintrust_ghg_app/raw/main/EinTrust%20%20logo.png", use_container_width=True)
    st.markdown("---")
    
    if st.button("Home"): st.session_state.page="Home"

    env_exp = st.expander("Environment", expanded=True)
    with env_exp:
        if st.button("GHG"): st.session_state.page="GHG"
        if st.button("Energy"): st.session_state.page="Energy"
        if st.button("Water"): st.session_state.page="Water"
        if st.button("Waste"): st.session_state.page="Waste"
        if st.button("Biodiversity"): st.session_state.page="Biodiversity"

    social_exp = st.expander("Social", expanded=False)
    with social_exp:
        if st.button("Employee"): st.session_state.page="Employee"
        if st.button("Health & Safety"): st.session_state.page="Health & Safety"
        if st.button("CSR"): st.session_state.page="CSR"

    gov_exp = st.expander("Governance", expanded=False)
    with gov_exp:
        if st.button("Board"): st.session_state.page="Board"
        if st.button("Policies"): st.session_state.page="Policies"
        if st.button("Compliance"): st.session_state.page="Compliance"
        if st.button("Risk Management"): st.session_state.page="Risk Management"

# ---------------------------
# Scope activities
# ---------------------------
scope_activities = {
    "Scope 1": {"Stationary Combustion": {"Diesel Generator":"Generator running on diesel","Petrol Generator":"Generator running on petrol"},
                "Mobile Combustion": {"Diesel Vehicle":"Truck/van running on diesel"}},
    "Scope 2": {"Electricity Consumption": {"Grid Electricity":"Electricity from grid"}},
    "Scope 3": {"Business Travel": {"Air Travel": None}}
}
units_dict = {"Diesel Generator":"Liters","Petrol Generator":"Liters","Diesel Vehicle":"Liters","Grid Electricity":"kWh"}

# ---------------------------
# KPI Calculation Functions
# ---------------------------
def calculate_ghg_kpis():
    df = st.session_state.entries
    summary = {"Scope 1":0,"Scope 2":0,"Scope 3":0,"Total":0,"Unit":"tCO₂e"}
    if not df.empty:
        for scope in ["Scope 1","Scope 2","Scope 3"]:
            summary[scope] = df[df["Scope"]==scope]["Quantity"].sum()
        summary["Total"] = df["Quantity"].sum()
    return summary

def calculate_energy_kpis():
    # Fossil energy from GHG page
    df = st.session_state.entries
    fossil_energy = 0
    fossil_co2e = 0
    if not df.empty:
        for fuel in ["Diesel Generator","Petrol Generator","Diesel Vehicle"]:
            if fuel in df["Sub-Activity"].values:
                fuel_df = df[df["Sub-Activity"]==fuel]
                fossil_energy += (fuel_df["Quantity"]*calorific_values.get(fuel,0)/3.6).sum()
                fossil_co2e += (fuel_df["Quantity"]*emission_factors.get(fuel,0)).sum()
    renewable_df = st.session_state.renewable_entries
    renewable_energy = renewable_df["Energy_kWh"].sum() if not renewable_df.empty else 0
    renewable_co2e = renewable_df["CO2e_kg"].sum() if not renewable_df.empty else 0
    return {"Total":fossil_energy+renewable_energy,"Fossil":fossil_energy,"Renewable":renewable_energy,
            "TotalCO2e":fossil_co2e+renewable_co2e,"FossilCO2e":fossil_co2e,"RenewableCO2e":renewable_co2e,"Unit":"kWh"}

# ---------------------------
# Render KPI Boxes
# ---------------------------
def render_kpis(kpis, title="GHG Emissions", colors=None):
    st.subheader(title)
    col_labels = list(kpis.keys())[:-1]  # exclude 'Unit'
    col1, col2, col3, col4 = st.columns(4)
    for col,label in zip([col1,col2,col3,col4],col_labels):
        color = colors[label] if colors else "#ffffff"
        value = kpis[label]
        unit = kpis["Unit"]
        col.markdown(f"""
            <div class='kpi'>
                <div class='kpi-value' style='color:{color}'>{format_indian(value)}</div>
                <div class='kpi-unit'>{unit}</div>
                <div class='kpi-label'>{label.lower()}</div>
            </div>
        """, unsafe_allow_html=True)

# ---------------------------
# Render GHG Dashboard
# ---------------------------
def render_ghg_dashboard(include_data=True):
    ghg_kpis = calculate_ghg_kpis()
    render_kpis(ghg_kpis,"GHG Emissions",{"Scope 1":"#81c784","Scope 2":"#4db6ac","Scope 3":"#aed581","Total":"#ffffff"})

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
        uploaded_file = st.file_uploader("Upload CSV/XLS/XLSX/PDF for cross verification (optional)", type=["csv","xls","xlsx","pdf"])

        if st.button("Add entry"):
            new_entry = {"Scope":scope,"Activity":activity,"Sub-Activity":sub_activity,"Specific Item":specific_item if specific_item else "",
                         "Quantity":quantity,"Unit":unit}
            st.session_state.entries = pd.concat([st.session_state.entries, pd.DataFrame([new_entry])], ignore_index=True)
            st.success("Entry added successfully!")

        if not st.session_state.entries.empty:
            st.subheader("All entries")
            display_df = st.session_state.entries.copy()
            display_df["Quantity"] = display_df["Quantity"].apply(lambda x: format_indian(x))
            st.dataframe(display_df)
            csv = display_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download all entries as CSV", csv, "ghg_entries.csv", "text/csv")

# ---------------------------
# Render Energy Dashboard
# ---------------------------
def render_energy_dashboard(include_entry=True):
    energy_kpis = calculate_energy_kpis()
    render_kpis(energy_kpis,"Energy Consumption",{"Fossil":"#f06292","Renewable":"#4db6ac","Total":"#ffffff"})

    # Monthly trend for Energy
    # Fossil fuel from GHG entries
    fossil_df = pd.DataFrame()
    if not st.session_state.entries.empty:
        fossil_list=[]
        for fuel in ["Diesel Generator","Petrol Generator","Diesel Vehicle"]:
            if fuel in st.session_state.entries["Sub-Activity"].values:
                fuel_df = st.session_state.entries[st.session_state.entries["Sub-Activity"]==fuel]
                for idx,row in fuel_df.iterrows():
                    monthly_energy = (row["Quantity"]*calorific_values.get(fuel,0)/3.6)/12
                    for m in months:
                        fossil_list.append({"Month":m,"Type":"Fossil","Energy_kWh":monthly_energy})
        fossil_df = pd.DataFrame(fossil_list)

    renewable_df = st.session_state.renewable_entries.copy() if not st.session_state.renewable_entries.empty else pd.DataFrame(columns=["Month","Type","Energy_kWh"])
    monthly_df = pd.concat([fossil_df[["Month","Type","Energy_kWh"]], renewable_df[["Month","Type","Energy_kWh"]]], ignore_index=True)
    if not monthly_df.empty:
        monthly_df["Month"] = pd.Categorical(monthly_df["Month"], categories=months, ordered=True)
        monthly_sum = monthly_df.groupby(["Month","Type"]).sum().reset_index()
        st.subheader("Monthly Energy Trend")
        fig = px.bar(monthly_sum, x="Month", y="Energy_kWh", color="Type", barmode="stack", labels={"Energy_kWh":"Energy (kWh)"})
        st.plotly_chart(fig,use_container_width=True)

    # Renewable energy entry
    if include_entry:
        st.subheader("Add Renewable Energy (Annual)")
        num_entries = st.number_input("Number of renewable energy entries",1,10,1)
        renewable_list=[]
        for i in range(int(num_entries)):
            col1,col2,col3 = st.columns([2,3,3])
            with col1:
                source = st.selectbox(f"Source",["Solar","Wind","Biogas","Purchased Green Energy"],key=f"src{i}")
            with col2:
                location = st.text_input("Location", "", key=f"loc{i}")
            with col3:
                annual_energy = st.number_input("Annual Energy (kWh)", min_value=0.0,key=f"annual{i}")
            monthly_energy = annual_energy/12
            for m in months:
                renewable_list.append({"Source":source,"Location":location,"Month":m,"Energy_kWh":monthly_energy,"CO2e_kg":monthly_energy*emission_factors.get(source,0),"Type":"Renewable"})
        if renewable_list:
            st.session_state.renewable_entries = pd.concat([st.session_state.renewable_entries,pd.DataFrame(renewable_list)],ignore_index=True)

        if not st.session_state.renewable_entries.empty:
            st.subheader("Renewable Energy Table")
            df_disp = st.session_state.renewable_entries.groupby(["Source","Location"]).sum().reset_index()
            st.dataframe(df_disp[["Source","Location","Energy_kWh","CO2e_kg"]])
            csv = df_disp[["Source","Location","Energy_kWh","CO2e_kg"]].to_csv(index=False).encode('utf-8')
            st.download_button("Download Renewable Energy CSV", csv, "renewable_energy.csv", "text/csv")

# ---------------------------
# Render pages
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
