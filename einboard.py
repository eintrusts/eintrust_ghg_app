import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import plotly.express as px

# ---------------------------
# Config & Dark Theme with professional look
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
    transform: scale(1.05);
    box-shadow: 0 8px 20px rgba(0,0,0,0.6);
}
.kpi-value { font-size: 28px; font-weight: 700; color: #ffffff; margin-bottom: 5px; }
.kpi-unit { font-size: 16px; font-weight: 500; color: #cfd8dc; margin-bottom: 5px; }
.kpi-label { font-size: 14px; color: #cfd8dc; letter-spacing: 0.5px; }

.stDataFrame { color: #e6edf3; font-family: 'Roboto', sans-serif; }

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
if "energy_data" not in st.session_state:
    st.session_state.energy_data = pd.DataFrame(columns=["Type","Fuel_Source","Energy_kWh","CO2e_kg","Month","Location"])

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

emission_factors_energy = {  # kg CO2e/unit
    "Diesel": 2.68, "Petrol": 2.31, "LPG": 1.51, "CNG": 2.02, "Coal": 2.42, "Biomass": 0.0,
    "Electricity": 0.82, "Solar":0.0, "Wind":0.0, "Purchased Green Energy":0.0, "Biogas":0.0
}

energy_colors = {"Fossil":"#f06292","Renewable":"#4db6ac","Total":"#ffffff"}

# ---------------------------
# Helper functions
# ---------------------------
def update_energy_from_ghg():
    """Update energy_data based on GHG entries for fossil fuels & grid electricity"""
    df = st.session_state.entries
    energy_list = []
    for idx, row in df.iterrows():
        month_list = months
        qty = row["Quantity"]
        fuel = row["Sub-Activity"]
        if fuel=="Grid Electricity":
            etype = "Fossil"
            energy_kwh = qty
            co2e = qty * emission_factors_energy.get("Electricity",0)
        else:
            etype = "Fossil"
            energy_kwh = qty  # Assuming quantity in liters
            co2e = qty * emission_factors_energy.get(fuel.split()[0],0)
        for m in month_list:
            energy_list.append({"Type":etype,"Fuel_Source":fuel,"Energy_kWh":energy_kwh/12,
                                "CO2e_kg":co2e/12,"Month":m,"Location":"NA"})
    st.session_state.energy_data = pd.DataFrame(energy_list)

def render_kpis(kpi_dict, title, colors=None):
    st.markdown(f"### {title}")
    cols = st.columns(len(kpi_dict))
    for col, (label, value) in zip(cols, kpi_dict.items()):
        color = colors[label] if colors else "#ffffff"
        col.markdown(f"""
            <div class='kpi'>
                <div class='kpi-value' style='color:{color}'>{format_indian(value)}</div>
                <div class='kpi-unit'>kWh / kg CO₂e</div>
                <div class='kpi-label'>{label.lower()}</div>
            </div>
        """, unsafe_allow_html=True)

def render_ghg_dashboard(include_data=True):
    st.subheader("GHG emissions dashboard")
    df = st.session_state.entries
    total = df["Quantity"].sum() if not df.empty else 0
    scope1 = df[df["Scope"]=="Scope 1"]["Quantity"].sum() if not df.empty else 0
    scope2 = df[df["Scope"]=="Scope 2"]["Quantity"].sum() if not df.empty else 0
    scope3 = df[df["Scope"]=="Scope 3"]["Quantity"].sum() if not df.empty else 0
    kpis = {"Total Quantity":total,"Scope 1":scope1,"Scope 2":scope2,"Scope 3":scope3}
    render_kpis(kpis,"GHG Emissions",{"Scope 1":"#81c784","Scope 2":"#4db6ac","Scope 3":"#aed581","Total Quantity":"#ffffff"})
    
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
        unit = units_dict.get(sub_activity,"Number of flights" if sub_activity=="Air Travel" else "km / kg / tonnes")
        quantity = st.number_input(f"Enter quantity ({unit})", min_value=0.0, format="%.2f")
        uploaded_file = st.file_uploader("Upload CSV/XLS/XLSX/PDF (optional)", type=["csv","xls","xlsx","pdf"])
        if st.button("Add entry"):
            new_entry = {"Scope":scope,"Activity":activity,"Sub-Activity":sub_activity,
                         "Specific Item":specific_item if specific_item else "",
                         "Quantity":quantity,"Unit":unit}
            st.session_state.entries = pd.concat([st.session_state.entries,pd.DataFrame([new_entry])],ignore_index=True)
            st.success("Entry added successfully!")
            update_energy_from_ghg()
        if not st.session_state.entries.empty:
            st.subheader("All entries")
            display_df = st.session_state.entries.copy()
            display_df["Quantity"] = display_df["Quantity"].apply(lambda x: format_indian(x))
            st.dataframe(display_df)
            csv = display_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download all entries as CSV", csv, "ghg_entries.csv","text/csv")

def render_energy_dashboard(include_entry=True):
    st.subheader("Energy dashboard")
    df = st.session_state.energy_data
    if df.empty:
        st.info("No energy data available. Add entries from GHG page or below.")
        df = pd.DataFrame(columns=["Type","Fuel_Source","Energy_kWh","CO2e_kg","Month","Location"])
    # KPIs
    total_energy = df["Energy_kWh"].sum()
    fossil_energy = df[df["Type"]=="Fossil"]["Energy_kWh"].sum()
    renewable_energy = df[df["Type"]=="Renewable"]["Energy_kWh"].sum()
    kpi_dict = {"Total":total_energy,"Fossil":fossil_energy,"Renewable":renewable_energy}
    render_kpis(kpi_dict,"Energy Consumption",energy_colors)
    
    # Monthly Trend stacked bar
    monthly = df.groupby(["Month","Type"])["Energy_kWh"].sum().reset_index()
    if not monthly.empty:
        fig = px.bar(monthly, x="Month", y="Energy_kWh", color="Type", barmode="stack",
                     labels={"Energy_kWh":"Energy (kWh)"}, color_discrete_map={"Fossil":"#f06292","Renewable":"#4db6ac"})
        st.plotly_chart(fig,use_container_width=True)
    
    if include_entry:
        st.subheader("Add renewable energy entries")
        num_entries = st.number_input("Number of renewable energy entries", min_value=1,max_value=20,value=1)
        renewable_list=[]
        for i in range(int(num_entries)):
            col1,col2,col3 = st.columns([2,3,3])
            with col1:
                source = st.selectbox(f"Source {i+1}", ["Solar","Wind","Biogas","Purchased Green Energy"], key=f"src{i}")
            with col2:
                location = st.text_input(f"Location {i+1}", "", key=f"loc{i}")
            with col3:
                annual_energy = st.number_input(f"Annual Energy kWh {i+1}", min_value=0.0, key=f"annual_{i}")
            monthly_energy = annual_energy/12
            for m in months:
                renewable_list.append({"Type":"Renewable","Fuel_Source":source,"Energy_kWh":monthly_energy,
                                       "CO2e_kg":monthly_energy*emission_factors_energy.get(source,0),
                                       "Month":m,"Location":location})
        if renewable_list:
            st.session_state.energy_data = pd.concat([st.session_state.energy_data,pd.DataFrame(renewable_list)],ignore_index=True)
        if renewable_list:
            renewable_summary = pd.DataFrame(renewable_list).groupby(["Source","Location"]).sum().reset_index()
            st.dataframe(renewable_summary)
            csv_renew = pd.DataFrame(renewable_list).to_csv(index=False).encode('utf-8')
            st.download_button("Download renewable entries", csv_renew,"renewable_entries.csv","text/csv")

# ---------------------------
# Render pages
# ---------------------------
st.title("🌍 EinTrust Sustainability Dashboard")

update_energy_from_ghg()

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
