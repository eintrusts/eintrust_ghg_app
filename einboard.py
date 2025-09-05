# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import date

# ---------------------------
# Page Config & CSS
# ---------------------------
st.set_page_config(page_title="EinTrust Sustainability Dashboard", page_icon="🌍", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }
.stApp { background-color: #0d1117; color: #e6edf3; }
.kpi { background: linear-gradient(145deg, #12131a, #1a1b22); padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.5); margin-bottom: 10px; min-height: 120px; display: flex; flex-direction: column; justify-content: center; align-items: center; transition: transform 0.2s, box-shadow 0.2s; }
.kpi:hover { transform: scale(1.03); box-shadow: 0 8px 20px rgba(0,0,0,0.6); }
.kpi-value { font-size: 28px; font-weight: 700; color: #ffffff; margin-bottom: 5px; }
.kpi-unit { font-size: 16px; font-weight: 500; color: #cfd8dc; margin-bottom: 5px; }
.kpi-label { font-size: 14px; color: #cfd8dc; letter-spacing: 0.5px; }
.sdg-card { border-radius: 10px; padding: 15px; margin: 8px; display: inline-block; width: 100%; min-height: 110px; text-align: left; color: white; }
.sdg-number { font-weight: 700; font-size: 20px; }
.sdg-name { font-size: 16px; margin-bottom: 5px; }
.sdg-percent { font-size: 14px; }
.small-muted { color: #9aa7b2; font-size:12px; }
@media (min-width: 768px) { .sdg-card { width: 220px; display: inline-block; } }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Sidebar & Navigation
# ---------------------------
if "page" not in st.session_state:
    st.session_state.page = "Home"

def sidebar_button(label):
    active = st.session_state.page == label
    if st.button(label, key=label):
        st.session_state.page = label
    st.markdown(f"""
    <style>
    div.stButton > button[key="{label}"] {{
        all: unset; cursor: pointer; padding: 0.4rem; text-align: left; border-radius: 0.3rem; margin-bottom: 0.2rem;
        background-color: {'forestgreen' if active else '#12131a'}; color: {'white' if active else '#e6edf3'}; font-size: 16px;
    }}
    div.stButton > button[key="{label}"]:hover {{
        background-color: {'forestgreen' if active else '#1a1b22'};
    }}
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.image("https://github.com/eintrusts/eintrust_ghg_app/blob/main/EinTrust%20%20(2).png?raw=true", use_container_width=True)
    st.markdown("---")
    sidebar_button("Home")

    env_exp = st.expander("Environment", expanded=True)
    with env_exp:
        sidebar_button("GHG")
        sidebar_button("Energy")
        sidebar_button("Water")
        sidebar_button("Waste")
        sidebar_button("Biodiversity")
        sidebar_button("SDG")

    social_exp = st.expander("Social")
    with social_exp:
        sidebar_button("Employee")
        sidebar_button("Diversity & Inclusion")
        sidebar_button("Community")

    gov_exp = st.expander("Governance")
    with gov_exp:
        sidebar_button("Board")
        sidebar_button("Policies")
        sidebar_button("Compliance")
        sidebar_button("Risk Management")

    sidebar_button("Reports")
    reports_exp = st.expander("Reports (quick links)", expanded=False)
    with reports_exp:
        sidebar_button("BRSR")
        sidebar_button("CDP")
        sidebar_button("GRI")
        sidebar_button("TCFD")

    sidebar_button("Settings")
    sidebar_button("Log Out")

# ---------------------------
# Session State DataFrames / Stores
# ---------------------------
# Keep existing GHG/Energy stores intact
if "entries" not in st.session_state:
    st.session_state.entries = pd.DataFrame(columns=[
        "Scope","Activity","Sub-Activity","Specific Item","Quantity","Unit","Emissions_kgCO2e"
    ])
if "renewable_entries" not in st.session_state:
    st.session_state.renewable_entries = pd.DataFrame(columns=["Source","Location","Month","Energy_kWh","CO2e_kg","Type"])
if "sdg_engagement" not in st.session_state:
    st.session_state.sdg_engagement = {i:0 for i in range(1,18)}
if "water_data" not in st.session_state:
    st.session_state.water_data = pd.DataFrame(columns=["Location","Source","Month","Quantity_m3","Cost_INR"])
if "advanced_water_data" not in st.session_state:
    st.session_state.advanced_water_data = pd.DataFrame(columns=[
        "Location","Month","Rainwater_Harvested_m3","Water_Recycled_m3","Treatment_Before_Discharge","STP_ETP_Capacity_kL_day"
    ])

# Additional data stores for Social & Governance & Waste & Biodiversity & CSR
if "waste_data" not in st.session_state:
    st.session_state.waste_data = pd.DataFrame(columns=["Location","Waste_Type","Quantity_kg","Treatment","Emissions_kgCO2e"])
if "biodiversity_data" not in st.session_state:
    st.session_state.biodiversity_data = pd.DataFrame(columns=["Project","Location","Area_ha","Species_Protected","Status","Notes"])
if "employee_data" not in st.session_state:
    st.session_state.employee_data = pd.DataFrame(columns=["Employee_ID","Name","Department","Role","Joining_Date","FT_PT","Gender"])
if "diversity_data" not in st.session_state:
    st.session_state.diversity_data = pd.DataFrame(columns=["Metric","Value","Notes"])
if "community_data" not in st.session_state:
    st.session_state.community_data = pd.DataFrame(columns=["Project","Beneficiary","Spend_INR","Start_Date","End_Date","Outcome"])
if "board_data" not in st.session_state:
    st.session_state.board_data = pd.DataFrame(columns=["Name","Role","Start_Date","End_Date","Independence","Gender","Notes"])
if "policy_list" not in st.session_state:
    st.session_state.policy_list = pd.DataFrame(columns=["Policy_Name","Category","Effective_Date","Owner","Status","Link"])
if "compliance_records" not in st.session_state:
    st.session_state.compliance_records = pd.DataFrame(columns=["Regulation","Due_Date","Status","Responsible","Notes"])
if "risk_register" not in st.session_state:
    st.session_state.risk_register = pd.DataFrame(columns=["Risk_ID","Title","Category","Likelihood","Impact","Mitigation","Owner","Status"])

# ---------------------------
# Constants & Helpers (kept consistent)
# ---------------------------
months = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]
ENERGY_COLORS = {"Fossil": "#f39c12", "Renewable": "#2ecc71"}
SDG_LIST = [
    "No Poverty","Zero Hunger","Good Health & Wellbeing","Quality Education","Gender Equality",
    "Clean Water & Sanitation","Affordable & Clean Energy","Decent Work & Economic Growth","Industry, Innovation & Infrastructure",
    "Reduced Inequalities","Sustainable Cities & Communities","Responsible Consumption & Production","Climate Action","Life Below Water",
    "Life on Land","Peace, Justice & Strong Institutions","Partnerships for the Goals"
]
SDG_COLORS = [
    "#e5243b","#dda63a","#4c9f38","#c5192d","#ff3a21","#26bde2","#fcc30b","#a21942","#fd6925","#dd1367","#fd9d24",
    "#bf8b2e","#3f7e44","#0a97d9","#56c02b","#00689d","#19486a"
]

# A small helper to sum emissions from stored dataframes
def total_emissions_scope1_2():
    # sum Emissions_kgCO2e in entries that are Scope 1 or 2
    df = st.session_state.entries
    if df.empty:
        return 0.0
    return df[df["Scope"].isin(["Scope 1","Scope 2"])]["Emissions_kgCO2e"].astype(float).sum()

def total_emissions_scope3():
    df = st.session_state.entries
    if df.empty:
        return 0.0
    return df[df["Scope"]=="Scope 3"]["Emissions_kgCO2e"].astype(float).sum()

def total_energy_consumption_kwh():
    # combine energy rows from entries and renewable_entries
    # using same logic as original energy rendering: if unit kWh treat as energy
    energy = 0.0
    df = st.session_state.entries
    if not df.empty:
        # pick rows where Unit contains kWh
        energy += df[df["Unit"].str.lower().str.contains("kwh", na=False)]["Quantity"].astype(float).sum()
    if "renewable_entries" in st.session_state and not st.session_state.renewable_entries.empty:
        energy += st.session_state.renewable_entries["Energy_kWh"].astype(float).sum()
    return energy

def total_water_m3():
    df = st.session_state.water_data
    if df.empty:
        return 0.0
    return df["Quantity_m3"].astype(float).sum()

def total_waste_kg():
    df = st.session_state.waste_data
    if df.empty:
        return 0.0
    return df["Quantity_kg"].astype(float).sum()

# ---------------------------
# GHG Dashboard (kept intact)
# ---------------------------
# For brevity the calculate_emissions and scope_activities constants are simplified versions
# but logic retained from earlier. We'll keep the UI exactly as you had earlier for GHG and Energy.
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
        },
        "Process Emissions": {
            "Cement Production": "CO₂ from cement making",
            "Steel Production": "CO₂ from steel processing",
            "Brick Kiln": "CO₂ from brick firing",
            "Textile Processing": "Emissions from dyeing/fabric processing",
            "Chemical Manufacturing": "Emissions from chemical reactions",
            "Food Processing": "Emissions from cooking/heating"
        },
        "Fugitive Emissions": {
            "Refrigerant (HFC/HCFC)": "Gas leak from AC/refrigerator",
            "Methane (CH₄)": "Methane leaks from storage/pipelines",
            "SF₆": "Gas leak from electrical equipment"
        }
    },
    "Scope 2": {
        "Electricity Consumption": {
            "Grid Electricity": "Electricity bought from grid",
            "Diesel Generator Electricity": "Electricity generated on-site with diesel"
        },
        "Steam / Heat": {"Purchased Steam": "Steam bought from external supplier"},
        "Cooling / Chilled Water": {"Purchased Cooling": "Cooling bought from supplier"}
    },
    "Scope 3": {
        "1 Purchased goods & services": {
            "Raw Materials": ["Cement","Steel","Chemicals","Textile","Paper"],
            "Packaging": ["Cardboard","Plastics","Glass"],
            "Office Supplies": ["Paper","Ink","Stationery"]
        },
        "2 Capital goods": {"Machinery & Equipment": None, "Buildings & Infrastructure": None},
        "3 Fuel- and energy-related activities (not included in Scope 1 or 2)": {"T&D Losses": None, "Fuel Production": None},
        "4 Upstream transportation & distribution": {"Incoming Transport": None, "Third-party Logistics": None},
        "5 Waste generated in operations": {"Landfill": None, "Recycling": None, "Composting": None},
        "6 Business travel": {"Air Travel": None, "Train Travel": None, "Taxi/Car Rental": None},
        "7 Employee commuting": {"Two-Wheelers": None, "Cars/Vans": None, "Public Transport": None},
        "8 Upstream leased assets": {"Leased Offices": None, "Leased Warehouses": None},
        "9 Downstream transportation & distribution": {"Distribution to Customers": None, "Retail/Distributor Transport": None},
        "10 Processing of sold products": {"Product Assembly": None},
        "11 Use of sold products": {"Product Use (Energy)": None},
        "12 End-of-life treatment of sold products": {"Recycling": None, "Landfill": None},
        "13 Downstream leased assets": {"Leased Operations": None},
        "14 Franchises": {"Franchise Operations": None},
        "15 Investments": {"Investments (Financial)": None}
    }
}

units_dict = {
    "Grid Electricity":"kWh","Diesel Generator":"Liters","Petrol Generator":"Liters","CNG Vehicle":"m³",
    "Cement":"Tonnes","Steel":"Tonnes","Cardboard":"kg","Plastics":"kg","Paper":"kg","Air Travel":"Number of flights",
    "Train Travel":"km traveled","Taxi/Car Rental":"km traveled","Two-Wheelers":"km traveled","Cars/Vans":"km traveled",
    "Landfill":"kg","Recycling":"kg","Composting":"kg","Product Use (Energy)":"kWh"
}

emission_factors = {
    "Diesel":2.68,"Petrol":2.31,"LPG":1.51,"CNG":2.02,"Coal":2.42,"Electricity":0.82,
    "Cement":900.0,"Steel":1850.0,"Textile":300.0,"Chemicals":1200.0,
    "Cardboard":0.9,"Plastics":1.7,"Glass":0.95,"Paper":1.2,
    "Air Travel (domestic average)":250.0,"Train per km":0.05,"Taxi per km":0.12,"TwoWheeler per km":0.05,"Car per km":0.12,
    "Landfill per kg":1.0,"Recycling per kg":0.3,"Composting per kg":0.2,"Product use kWh":0.82
}

def calculate_emissions(scope, activity, sub_activity, specific_item, quantity, unit):
    missing_factor = False
    emissions = 0.0
    key_specific = (specific_item or "").strip()
    key_sub = (sub_activity or "").strip()

    if scope in ["Scope 1","Scope 2"]:
        fuel_key = None
        if key_sub in ["Grid Electricity","Diesel Generator Electricity"]:
            fuel_key = "Electricity"
        elif "Diesel" in key_sub:
            fuel_key = "Diesel"
        elif "Petrol" in key_sub:
            fuel_key = "Petrol"
        elif "LPG" in key_sub:
            fuel_key = "LPG"
        elif "Coal" in key_sub:
            fuel_key = "Coal"
        if fuel_key:
            factor = emission_factors.get(fuel_key)
            if factor is not None:
                emissions = float(quantity) * factor
            else:
                missing_factor = True
        else:
            if unit and unit.lower() in ["kwh"]:
                factor = emission_factors.get("Electricity")
                if factor is not None:
                    emissions = float(quantity) * factor
                else:
                    missing_factor = True
            else:
                missing_factor = True
    else:
        if key_specific and key_specific in emission_factors:
            emissions = float(quantity) * emission_factors[key_specific]
        else:
            if key_sub in ["Air Travel"]:
                factor = emission_factors.get("Air Travel (domestic average)")
                if factor:
                    emissions = float(quantity) * factor
                else:
                    missing_factor = True
            elif key_sub in ["Train Travel"]:
                factor = emission_factors.get("Train per km")
                if factor:
                    emissions = float(quantity) * factor
                else:
                    missing_factor = True
            elif key_sub in ["Taxi/Car Rental","Cars/Vans"]:
                factor = emission_factors.get("Car per km")
                if factor:
                    emissions = float(quantity) * factor
                else:
                    missing_factor = True
            elif key_sub in ["Two-Wheelers"]:
                factor = emission_factors.get("TwoWheeler per km")
                if factor:
                    emissions = float(quantity) * factor
                else:
                    missing_factor = True
            elif key_sub in ["Landfill","Recycling","Composting"]:
                mapping = {"Landfill":"Landfill per kg","Recycling":"Recycling per kg","Composting":"Composting per kg"}
                factor = emission_factors.get(mapping.get(key_sub))
                if factor:
                    emissions = float(quantity) * factor
                else:
                    missing_factor = True
            elif unit and unit.lower() in ["kwh"]:
                factor = emission_factors.get("Product use kWh")
                if factor:
                    emissions = float(quantity) * factor
                else:
                    missing_factor = True
            else:
                missing_factor = True

    return emissions, missing_factor

def render_ghg_dashboard(include_data=True, show_chart=True):
    st.subheader("GHG Emissions")

    if include_data:
        scope = st.selectbox("Select Scope", ["Scope 1","Scope 2","Scope 3"], index=0)

        if scope != "Scope 3":
            activity = st.selectbox("Select Activity", list(scope_activities[scope].keys()))
            sub_options = scope_activities[scope][activity]
            sub_activity = st.selectbox("Select Sub-Activity", list(sub_options.keys()))
            st.info(sub_options[sub_activity])
            specific_item = ""
        else:
            activity = st.selectbox("Select Scope 3 Category", list(scope_activities["Scope 3"].keys()))
            sub_dict = scope_activities["Scope 3"][activity]
            sub_activity = st.selectbox("Select Sub-Category", list(sub_dict.keys()))
            specific_item = ""
            if isinstance(sub_dict[sub_activity], list):
                specific_item = st.selectbox("Select Specific Item", sub_dict[sub_activity])
            else:
                specific_item = st.text_input("Specific Item (optional — e.g. 'Branded Paper 80gsm')", value="")

        if scope != "Scope 3":
            unit = units_dict.get(sub_activity, "")
        else:
            if sub_activity in ["Air Travel"]:
                unit = "Number of flights"
            elif sub_activity in ["Train Travel","Taxi/Car Rental","Cars/Vans","Two-Wheelers","Public Transport","Incoming Transport","Third-party Logistics","Distribution to Customers","Retail/Distributor Transport"]:
                unit = "km traveled"
            elif sub_activity in ["Cement Production","Raw Materials","Packaging","Processing of sold products","Use of sold products"]:
                unit = units_dict.get(specific_item, "kg / Tonnes")
            elif sub_activity in ["Landfill","Recycling","Composting","End-of-life treatment"]:
                unit = "kg"
            else:
                unit = "kg / Tonnes"

        quantity = st.number_input(f"Enter Quantity ({unit})", min_value=0.0, format="%.3f")

        if st.button("Add Entry"):
            emissions, missing = calculate_emissions(scope, activity, sub_activity, specific_item, quantity, unit)
            if missing:
                st.warning("Emission factor for this item was not found in the default library; recorded emissions as 0. Provide a custom factor later or upload supplier-specific factor.")
            entry = {
                "Scope": scope,
                "Activity": activity,
                "Sub-Activity": sub_activity,
                "Specific Item": specific_item,
                "Quantity": quantity,
                "Unit": unit,
                "Emissions_kgCO2e": round(float(emissions),3)
            }
            st.session_state.entries = pd.concat([st.session_state.entries, pd.DataFrame([entry])], ignore_index=True)
            st.success("GHG entry added and emissions calculated (if factor available).")

        st.subheader("Optional: Upload File")
        uploaded_file = st.file_uploader("Upload CSV/XLS/XLSX", type=["csv","xls","xlsx"])
        if uploaded_file:
            try:
                if uploaded_file.name.endswith(".csv"):
                    df_file = pd.read_csv(uploaded_file)
                else:
                    df_file = pd.read_excel(uploaded_file)
                needed = {"Scope","Activity","Sub-Activity","Quantity","Unit"}
                if not needed.issubset(set(df_file.columns)):
                    st.error(f"Uploaded file must contain columns: {needed}")
                else:
                    df_file = df_file.fillna("")
                    emissions_list = []
                    for _, r in df_file.iterrows():
                        emissions, missing = calculate_emissions(r["Scope"], r["Activity"], r["Sub-Activity"], r.get("Specific Item",""), r["Quantity"], r["Unit"])
                        emissions_list.append(round(float(emissions),3))
                    df_file["Emissions_kgCO2e"] = emissions_list
                    # ensure columns match
                    cols = ["Scope","Activity","Sub-Activity","Specific Item","Quantity","Unit","Emissions_kgCO2e"]
                    df_file = df_file[cols]
                    st.session_state.entries = pd.concat([st.session_state.entries, df_file], ignore_index=True)
                    st.success("File uploaded and emissions computed (where factor was available).")
            except Exception as e:
                st.error(f"Error reading file: {e}")

    if not st.session_state.entries.empty:
        st.subheader("All GHG Entries")
        display_df = st.session_state.entries.copy()
        display_df["Quantity"] = display_df["Quantity"].astype(float).apply(lambda x: f"{float(x):,.3f}")
        display_df["Emissions_kgCO2e"] = display_df["Emissions_kgCO2e"].astype(float).apply(lambda x: f"{float(x):,.3f}")
        st.dataframe(display_df, use_container_width=True)
        csv = st.session_state.entries.to_csv(index=False).encode('utf-8')
        st.download_button("Download GHG Entries as CSV", csv, "ghg_entries_with_emissions.csv", "text/csv")

# ---------------------------
# Energy Dashboard (kept intact)
# ---------------------------
def render_energy_dashboard(include_input=True, show_chart=True):
    st.subheader("Energy")
    df = st.session_state.entries.copy()

    calorific_values = {"Diesel":35.8,"Petrol":34.2,"LPG":46.1,"CNG":48,"Coal":24,"Biomass":15}
    emission_factors_local = emission_factors  # reuse

    scope1_2_data = pd.DataFrame()
    if not df.empty:
        scope1_2_df = df[df["Scope"].isin(["Scope 1","Scope 2"])].copy()
        energy_rows = []
        for _, r in scope1_2_df.iterrows():
            sub = r["Sub-Activity"]
            qty = float(r["Quantity"])
            unit = r["Unit"]
            energy_kwh = 0.0
            if "Electricity" in sub or (isinstance(unit,str) and unit.lower()=="kwh"):
                energy_kwh = qty
                co2e = qty * emission_factors_local.get("Electricity",0)
            else:
                if "Diesel" in sub:
                    energy_kwh = (qty * calorific_values["Diesel"]) / 3.6
                    co2e = qty * emission_factors_local.get("Diesel",0)
                elif "Petrol" in sub:
                    energy_kwh = (qty * calorific_values["Petrol"]) / 3.6
                    co2e = qty * emission_factors_local.get("Petrol",0)
                elif "LPG" in sub:
                    energy_kwh = (qty * calorific_values["LPG"]) / 3.6
                    co2e = qty * emission_factors_local.get("LPG",0)
                elif "Coal" in sub:
                    energy_kwh = (qty * calorific_values["Coal"]) / 3.6
                    co2e = qty * emission_factors_local.get("Coal",0)
                else:
                    energy_kwh = 0.0
                    co2e = float(r.get("Emissions_kgCO2e",0.0))
            energy_rows.append({
                "Location": r.get("Specific Item","").strip() or "Unknown Location",
                "Fuel": sub,
                "Quantity": qty,
                "Energy_kWh": energy_kwh,
                "CO2e_kg": co2e,
                "Type": "Fossil" if co2e>0 else "Unknown",
                "Month": np.random.choice(months)
            })
        if energy_rows:
            scope1_2_data = pd.DataFrame(energy_rows)

    all_energy = pd.concat([scope1_2_data, st.session_state.renewable_entries], ignore_index=True) if not st.session_state.renewable_entries.empty else scope1_2_data
    if not all_energy.empty and "Month" in all_energy:
        all_energy["Month"] = pd.Categorical(all_energy["Month"], categories=months, ordered=True)

    total_energy = all_energy.groupby("Type")["Energy_kWh"].sum().to_dict() if not all_energy.empty else {}
    fossil_energy = total_energy.get("Fossil",0)
    renewable_energy = total_energy.get("Renewable",0)
    total_sum = fossil_energy + renewable_energy

    c1,c2,c3 = st.columns(3)
    for col,label,value,color in zip(
        [c1,c2,c3],
        ["Total Energy (kWh)","Fossil Energy (kWh)","Renewable Energy (kWh)"],
        [total_sum,fossil_energy,renewable_energy],
        ["#ffffff",ENERGY_COLORS["Fossil"],ENERGY_COLORS["Renewable"]]
    ):
        col.markdown(
            f"<div class='kpi'><div class='kpi-value' style='color:{color}'>{int(value):,}</div>"
            f"<div class='kpi-unit'>kWh</div><div class='kpi-label'>{label.lower()}</div></div>",
            unsafe_allow_html=True
        )

    if show_chart and not all_energy.empty:
        monthly_trend = all_energy.groupby(["Month","Type"])["Energy_kWh"].sum().reset_index()
        st.subheader("Monthly Energy Consumption (kWh)")
        fig = px.bar(monthly_trend, x="Month", y="Energy_kWh", color="Type", barmode="stack", color_discrete_map=ENERGY_COLORS)
        st.plotly_chart(fig, use_container_width=True)

    if include_input:
        st.subheader("Add Renewable Energy")
        num_entries = st.number_input("Number of renewable energy entries", min_value=1, max_value=10, value=1)
        renewable_list = []
        for i in range(int(num_entries)):
            col1,col2,col3 = st.columns([2,3,3])
            with col1:
                source = st.selectbox(f"Source {i+1}", ["Solar","Wind","Biogas","Purchased Green Energy"], key=f"src{i}")
            with col2:
                location = st.text_input(f"Location {i+1}", "", key=f"loc{i}")
            with col3:
                annual_energy = st.number_input(f"Annual Energy kWh {i+1}", min_value=0.0, key=f"annual_{i}")
            monthly_energy = annual_energy/12 if annual_energy else 0.0
            for m in months:
                renewable_list.append({
                    "Source":source,"Location":location,"Month":m,
                    "Energy_kWh":monthly_energy,"Type":"Renewable",
                    "CO2e_kg":monthly_energy * emission_factors.get(source,0)
                })
        if renewable_list and st.button("Add Renewable Energy Entries"):
            new_entries_df = pd.DataFrame(renewable_list)
            st.session_state.renewable_entries = pd.concat([st.session_state.renewable_entries, new_entries_df], ignore_index=True)
            st.success(f"{len(new_entries_df)} monthly rows added (from annual inputs).")
            st.experimental_rerun()

# ---------------------------
# Environment: Water, Waste, Biodiversity, SDG
# ---------------------------
def render_water_page():
    st.title("Water — Data & KPIs")
    with st.form("water_entry_form"):
        st.subheader("Add water usage record")
        loc = st.text_input("Location / Facility")
        source = st.selectbox("Source", ["Municipal", "Borewell", "Tankers", "Recycled", "Rainwater Harvested"])
        month = st.selectbox("Month", months)
        qty = st.number_input("Quantity (m³)", min_value=0.0, format="%.3f")
        cost = st.number_input("Cost (INR)", min_value=0.0, format="%.2f")
        submitted = st.form_submit_button("Add Water Record")
        if submitted:
            row = {"Location":loc,"Source":source,"Month":month,"Quantity_m3":qty,"Cost_INR":cost}
            st.session_state.water_data = pd.concat([st.session_state.water_data, pd.DataFrame([row])], ignore_index=True)
            st.success("Water record added")

    st.markdown("### Summary")
    df = st.session_state.water_data
    total_water = df["Quantity_m3"].astype(float).sum() if not df.empty else 0
    total_cost = df["Cost_INR"].astype(float).sum() if not df.empty else 0
    st.metric("Total Water Used (m³)", f"{total_water:,.2f}")
    st.metric("Estimated Cost (INR)", f"₹ {total_cost:,.2f}")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.download_button("Download water data CSV", df.to_csv(index=False).encode('utf-8'), "water_data.csv", "text/csv")

def render_waste_page():
    st.title("Waste — Data & KPIs")
    with st.form("waste_entry_form"):
        st.subheader("Add waste record")
        loc = st.text_input("Location / Facility")
        wtype = st.selectbox("Waste Type", ["Municipal Solid Waste","Hazardous","E-waste","Industrial","Organic"])
        qty = st.number_input("Quantity (kg)", min_value=0.0, format="%.2f")
        treatment = st.selectbox("Treatment Method", ["Landfill","Incineration","Recycling","Composting","Anaerobic Digestion"])
        est_em = 0.0
        if treatment == "Landfill":
            est_em = qty * emission_factors.get("Landfill per kg", 1.0)
        elif treatment == "Recycling":
            est_em = qty * emission_factors.get("Recycling per kg", 0.3)
        elif treatment == "Composting":
            est_em = qty * emission_factors.get("Composting per kg", 0.2)
        submitted = st.form_submit_button("Add Waste Record")
        if submitted:
            row = {"Location":loc,"Waste_Type":wtype,"Quantity_kg":qty,"Treatment":treatment,"Emissions_kgCO2e":round(est_em,3)}
            st.session_state.waste_data = pd.concat([st.session_state.waste_data, pd.DataFrame([row])], ignore_index=True)
            st.success("Waste record added")

    st.markdown("### Summary")
    df = st.session_state.waste_data
    total_waste = df["Quantity_kg"].astype(float).sum() if not df.empty else 0
    total_waste_em = df["Emissions_kgCO2e"].astype(float).sum() if not df.empty else 0
    st.metric("Total Waste (kg)", f"{total_waste:,.2f}")
    st.metric("Estimated Waste Emissions (kgCO2e)", f"{total_waste_em:,.2f}")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.download_button("Download waste data CSV", df.to_csv(index=False).encode('utf-8'), "waste_data.csv", "text/csv")

def render_biodiversity_page():
    st.title("Biodiversity — Projects & Monitoring")
    with st.form("biodiv_form"):
        st.subheader("Add biodiversity project")
        proj = st.text_input("Project name")
        loc = st.text_input("Location")
        area = st.number_input("Area (ha)", min_value=0.0, format="%.3f")
        species = st.text_area("Key species protected (comma separated)")
        status = st.selectbox("Status", ["Planned","Ongoing","Completed","Monitoring"])
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Add Project")
        if submitted:
            row = {"Project":proj,"Location":loc,"Area_ha":area,"Species_Protected":species,"Status":status,"Notes":notes}
            st.session_state.biodiversity_data = pd.concat([st.session_state.biodiversity_data, pd.DataFrame([row])], ignore_index=True)
            st.success("Biodiversity project added")

    df = st.session_state.biodiversity_data
    st.markdown("### Projects")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.download_button("Download biodiversity CSV", df.to_csv(index=False).encode('utf-8'), "biodiversity.csv", "text/csv")
    else:
        st.info("No projects recorded yet.")

def render_sdg_dashboard():
    st.title("Sustainable Development Goals (SDGs)")
    num_cols = 4
    rows = (len(SDG_LIST) + num_cols - 1) // num_cols
    idx = 0
    for _ in range(rows):
        cols = st.columns(num_cols)
        for c in range(num_cols):
            if idx >= len(SDG_LIST):
                break
            sdg_name = SDG_LIST[idx]
            sdg_color = SDG_COLORS[idx]
            sdg_number = idx + 1
            engagement = st.session_state.sdg_engagement.get(sdg_number, 0)
            engagement = cols[c].slider(
                f"Engagement % - SDG {sdg_number}", 0, 100, value=engagement, key=f"sdg{sdg_number}"
            )
            st.session_state.sdg_engagement[sdg_number] = engagement
            cols[c].markdown(
                f"<div class='sdg-card' style='background-color:{sdg_color}'>"
                f"<div class='sdg-number'>SDG {sdg_number}</div>"
                f"<div class='sdg-name'>{sdg_name}</div>"
                f"<div class='sdg-percent'>Engagement: {engagement}%</div>"
                f"</div>",
                unsafe_allow_html=True
            )
            idx += 1

# ---------------------------
# Social: Employees, Diversity & Community
# ---------------------------
def render_employee_page():
    st.title("Employee — Basic HR Data")
    with st.form("employee_form"):
        st.subheader("Add employee")
        emp_id = st.text_input("Employee ID")
        name = st.text_input("Name")
        dept = st.text_input("Department")
        role = st.text_input("Role")
        joining = st.date_input("Joining Date", value=date.today())
        ftpt = st.selectbox("Full-time / Part-time", ["Full-time","Part-time","Contract"])
        gender = st.selectbox("Gender", ["Male","Female","Other","Prefer not to say"])
        submitted = st.form_submit_button("Add Employee")
        if submitted:
            row = {"Employee_ID":emp_id,"Name":name,"Department":dept,"Role":role,"Joining_Date":str(joining),"FT_PT":ftpt,"Gender":gender}
            st.session_state.employee_data = pd.concat([st.session_state.employee_data, pd.DataFrame([row])], ignore_index=True)
            st.success("Employee added")

    df = st.session_state.employee_data
    st.markdown("### Employee List")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.download_button("Download employee CSV", df.to_csv(index=False).encode('utf-8'), "employee_data.csv", "text/csv")
        st.metric("Total Employees", f"{df.shape[0]}")
        # diversity quick KPIs
        gender_counts = df["Gender"].value_counts().to_dict()
        st.write("Gender breakdown:", gender_counts)
    else:
        st.info("No employee records yet.")

def render_diversity_page():
    st.title("Diversity & Inclusion — Metrics")
    with st.form("diversity_form"):
        st.subheader("Add a diversity metric")
        metric = st.selectbox("Metric", ["Female %", "Women in leadership %", "Disabled employees %", "Other"])
        value = st.number_input("Value (%)", min_value=0.0, max_value=100.0, format="%.2f")
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Add Metric")
        if submitted:
            row = {"Metric":metric,"Value":value,"Notes":notes}
            st.session_state.diversity_data = pd.concat([st.session_state.diversity_data, pd.DataFrame([row])], ignore_index=True)
            st.success("Metric added")

    df = st.session_state.diversity_data
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.download_button("Download diversity CSV", df.to_csv(index=False).encode('utf-8'), "diversity.csv", "text/csv")
    else:
        st.info("No diversity metrics yet.")

def render_community_page():
    st.title("Community — CSR & Community Projects")
    with st.form("community_form"):
        st.subheader("Add community project")
        proj = st.text_input("Project Name")
        ben = st.text_input("Beneficiary / Location")
        spend = st.number_input("Spend (INR)", min_value=0.0, format="%.2f")
        start = st.date_input("Start Date", value=date.today())
        end = st.date_input("End Date", value=date.today())
        outcome = st.text_area("Outcome / Notes")
        submitted = st.form_submit_button("Add CSR Project")
        if submitted:
            row = {"Project":proj,"Beneficiary":ben,"Spend_INR":spend,"Start_Date":str(start),"End_Date":str(end),"Outcome":outcome}
            st.session_state.community_data = pd.concat([st.session_state.community_data, pd.DataFrame([row])], ignore_index=True)
            st.success("Community project added")

    df = st.session_state.community_data
    total_spend = df["Spend_INR"].astype(float).sum() if not df.empty else 0
    st.metric("Total Community Spend (INR)", f"₹ {total_spend:,.2f}")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.download_button("Download community CSV", df.to_csv(index=False).encode('utf-8'), "community.csv", "text/csv")

# ---------------------------
# Governance: Board, Policies, Compliance, Risk
# ---------------------------
def render_board_page():
    st.title("Board — Membership")
    with st.form("board_form"):
        name = st.text_input("Member Name")
        role = st.text_input("Role / Title")
        start = st.date_input("Start Date", value=date.today())
        end = st.date_input("End Date (if any)", value=date.today())
        indep = st.selectbox("Independence", ["Independent","Non-independent"])
        gender = st.selectbox("Gender", ["Male","Female","Other","Prefer not to say"])
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Add Board Member")
        if submitted:
            row = {"Name":name,"Role":role,"Start_Date":str(start),"End_Date":str(end),"Independence":indep,"Gender":gender,"Notes":notes}
            st.session_state.board_data = pd.concat([st.session_state.board_data, pd.DataFrame([row])], ignore_index=True)
            st.success("Board member added")

    df = st.session_state.board_data
    st.markdown("### Board Members")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.download_button("Download board CSV", df.to_csv(index=False).encode('utf-8'), "board_data.csv", "text/csv")
        # quick KPI: percent independent
        total = df.shape[0]
        indep_count = df[df["Independence"]=="Independent"].shape[0]
        pct = (indep_count/total*100) if total else 0
        st.metric("Independent directors (%)", f"{pct:.1f}%")
    else:
        st.info("No board members recorded yet.")

def render_policies_page():
    st.title("Policies — Register")
    with st.form("policy_form"):
        name = st.text_input("Policy Name")
        cat = st.selectbox("Category", ["Environmental","Social","Governance","Health & Safety","Other"])
        eff = st.date_input("Effective Date", value=date.today())
        owner = st.text_input("Policy Owner")
        status = st.selectbox("Status", ["Draft","Approved","Under review","Archived"])
        link = st.text_input("Document Link (optional)")
        submitted = st.form_submit_button("Add Policy")
        if submitted:
            row = {"Policy_Name":name,"Category":cat,"Effective_Date":str(eff),"Owner":owner,"Status":status,"Link":link}
            st.session_state.policy_list = pd.concat([st.session_state.policy_list, pd.DataFrame([row])], ignore_index=True)
            st.success("Policy added")

    df = st.session_state.policy_list
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.download_button("Download policies CSV", df.to_csv(index=False).encode('utf-8'), "policies.csv", "text/csv")
    else:
        st.info("No policies recorded yet.")

def render_compliance_page():
    st.title("Compliance — Tracker")
    with st.form("compliance_form"):
        regulation = st.text_input("Regulation / Requirement")
        due = st.date_input("Due Date", value=date.today())
        status = st.selectbox("Status", ["Compliant","Non-compliant","In progress","Not applicable"])
        person = st.text_input("Responsible Person")
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Add Record")
        if submitted:
            row = {"Regulation":regulation,"Due_Date":str(due),"Status":status,"Responsible":person,"Notes":notes}
            st.session_state.compliance_records = pd.concat([st.session_state.compliance_records, pd.DataFrame([row])], ignore_index=True)
            st.success("Compliance record added")

    df = st.session_state.compliance_records
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.download_button("Download compliance CSV", df.to_csv(index=False).encode('utf-8'), "compliance.csv", "text/csv")
    else:
        st.info("No compliance records yet.")

def render_risk_management_page():
    st.title("Risk Management — Register")
    with st.form("risk_form"):
        rid = st.text_input("Risk ID")
        title = st.text_input("Title / Short description")
        cat = st.selectbox("Category", ["Strategic","Operational","Financial","Compliance","Environmental","Health & Safety","Other"])
        likelihood = st.selectbox("Likelihood", ["Low","Medium","High"])
        impact = st.selectbox("Impact", ["Low","Medium","High","Severe"])
        mitigation = st.text_area("Mitigation measures")
        owner = st.text_input("Owner")
        status = st.selectbox("Status", ["Open","Mitigated","Closed"])
        submitted = st.form_submit_button("Add Risk")
        if submitted:
            row = {"Risk_ID":rid,"Title":title,"Category":cat,"Likelihood":likelihood,"Impact":impact,"Mitigation":mitigation,"Owner":owner,"Status":status}
            st.session_state.risk_register = pd.concat([st.session_state.risk_register, pd.DataFrame([row])], ignore_index=True)
            st.success("Risk added")

    df = st.session_state.risk_register
    total_risks = df.shape[0] if not df.empty else 0
    open_risks = df[df["Status"]!="Closed"].shape[0] if not df.empty else 0
    st.metric("Total risks recorded", f"{total_risks}")
    st.metric("Open risks", f"{open_risks}")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.download_button("Download risk register CSV", df.to_csv(index=False).encode('utf-8'), "risk_register.csv", "text/csv")

# ---------------------------
# Reports: BRSR, CDP, GRI, TCFD
# Each report reads from session_state and displays relevant KPIs automatically
# ---------------------------
def render_brsr_report():
    st.title("BRSR — Business Responsibility & Sustainability Report (KPIs)")
    # Environment KPIs
    scope1_2 = total_emissions_scope1_2() / 1000.0  # convert kg -> tonnes? earlier units were kg, show tCO2e
    scope3 = total_emissions_scope3() / 1000.0
    total_ghg_t = (scope1_2 + scope3)

    energy_kwh = total_energy_consumption_kwh()
    water_m3 = total_water_m3()
    waste_kg = total_waste_kg()

    st.subheader("Environment")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Scope1+2 (tCO2e)", f"{scope1_2:,.2f}")
    c2.metric("Scope3 (tCO2e)", f"{scope3:,.2f}")
    c3.metric("Total GHG (tCO2e)", f"{total_ghg_t:,.2f}")
    c4.metric("Energy (kWh)", f"{energy_kwh:,.0f}")

    c5,c6 = st.columns(2)
    c5.metric("Water (m³)", f"{water_m3:,.0f}")
    c6.metric("Waste (kg)", f"{waste_kg:,.0f}")

    st.subheader("Social")
    employees = st.session_state.employee_data.shape[0] if not st.session_state.employee_data.empty else 0
    total_csr_spend = st.session_state.community_data["Spend_INR"].astype(float).sum() if not st.session_state.community_data.empty else 0
    st.metric("Employees", f"{employees}")
    st.metric("Community / CSR Spend (INR)", f"₹ {total_csr_spend:,.2f}")

    st.subheader("Governance")
    board_total = st.session_state.board_data.shape[0] if not st.session_state.board_data.empty else 0
    board_indep = st.session_state.board_data[st.session_state.board_data["Independence"]=="Independent"].shape[0] if not st.session_state.board_data.empty else 0
    pct_indep = (board_indep/board_total*100) if board_total else 0
    st.metric("Board size", f"{board_total}")
    st.metric("Independent directors (%)", f"{pct_indep:.1f}%")

    st.markdown("---")
    st.markdown("**Notes:** KPIs above are auto-calculated from user inputs across Environment, Social and Governance pages.")

def render_cdp_report():
    st.title("CDP — Climate (Auto KPIs)")
    st.subheader("Emissions & Energy")
    s1_2 = total_emissions_scope1_2() / 1000.0
    s3 = total_emissions_scope3() / 1000.0
    total_t = s1_2 + s3
    st.metric("Scope1+2 (tCO2e)", f"{s1_2:,.2f}")
    st.metric("Scope3 (tCO2e)", f"{s3:,.2f}")
    st.metric("Total Emissions (tCO2e)", f"{total_t:,.2f}")

    energy_kwh = total_energy_consumption_kwh()
    st.metric("Total Energy (kWh)", f"{energy_kwh:,.0f}")

    # Simple CDP-style risk indicators from risk register
    st.subheader("Climate-related risks (from Risk Register)")
    df = st.session_state.risk_register
    if not df.empty:
        clim_risks = df[df["Category"].str.lower().str.contains("environment|climate|environmental", na=False)]
        st.markdown(f"Risks flagged as climate/environmental: {clim_risks.shape[0]}")
        if not clim_risks.empty:
            st.dataframe(clim_risks, use_container_width=True)
    else:
        st.info("No risks recorded yet; CDP shows risk exposure from the Risk Register.")

def render_gri_report():
    st.title("GRI — General Reporting Initiative (KPIs)")
    st.subheader("Environmental (energy, emissions, water, waste)")
    energy_kwh = total_energy_consumption_kwh()
    ghg_kg = (total_emissions_scope1_2() + total_emissions_scope3())
    water_m3 = total_water_m3()
    waste_kg = total_waste_kg()

    st.metric("Energy (kWh)", f"{energy_kwh:,.0f}")
    st.metric("Total GHG (kgCO2e)", f"{ghg_kg:,.0f}")
    st.metric("Water (m³)", f"{water_m3:,.0f}")
    st.metric("Waste (kg)", f"{waste_kg:,.0f}")

    st.subheader("Social")
    st.metric("Employee count", f"{st.session_state.employee_data.shape[0] if not st.session_state.employee_data.empty else 0}")
    if not st.session_state.diversity_data.empty:
        st.markdown("Diversity metrics:")
        st.dataframe(st.session_state.diversity_data, use_container_width=True)
    else:
        st.info("No diversity metrics recorded yet.")

    st.subheader("Governance")
    st.markdown("Policies register:")
    if not st.session_state.policy_list.empty:
        st.dataframe(st.session_state.policy_list, use_container_width=True)
    else:
        st.info("No policies recorded yet.")

def render_tcfd_report():
    st.title("TCFD — Task Force on Climate-related Financial Disclosures (KPIs)")
    st.subheader("Governance")
    # show board + risk management mapping
    st.markdown("Board & oversight")
    if not st.session_state.board_data.empty:
        st.dataframe(st.session_state.board_data[["Name","Role","Independence"]], use_container_width=True)
    else:
        st.info("No board info recorded.")

    st.subheader("Strategy & Risk Management")
    st.markdown("Top climate/environmental risks from Risk Register (if any):")
    df = st.session_state.risk_register
    if not df.empty:
        clim = df[df["Category"].str.lower().str.contains("environment|climate|environmental", na=False)]
        if not clim.empty:
            st.dataframe(clim, use_container_width=True)
        else:
            st.info("No climate-related risk entries found in risk register.")
    else:
        st.info("No risks recorded yet.")

    st.subheader("Metrics & Targets")
    s1_2 = total_emissions_scope1_2()/1000.0
    s3 = total_emissions_scope3()/1000.0
    st.metric("Scope1+2 (tCO2e)", f"{s1_2:,.2f}")
    st.metric("Scope3 (tCO2e)", f"{s3:,.2f}")

# Router for Reports
def render_reports_router(selected=None):
    st.title("Reports")
    if selected is None:
        selected = st.selectbox("Select Report framework", ["BRSR","CDP","GRI","TCFD"])
    if selected == "BRSR":
        render_brsr_report()
    elif selected == "CDP":
        render_cdp_report()
    elif selected == "GRI":
        render_gri_report()
    elif selected == "TCFD":
        render_tcfd_report()

# ---------------------------
# Main page router (keeps Home, GHG, Energy as requested)
# ---------------------------
if st.session_state.page == "Home":
    st.title("EinTrust Sustainability Dashboard")
    st.markdown("Welcome — use the sidebar to navigate. GHG and Energy quick panels are shown below.")
    # Keep GHG/Energy rendering on Home but without data input
    render_ghg_dashboard(include_data=False, show_chart=False)
    render_energy_dashboard(include_input=False, show_chart=False)

elif st.session_state.page == "GHG":
    render_ghg_dashboard(include_data=True, show_chart=True)

elif st.session_state.page == "Energy":
    render_energy_dashboard(include_input=True, show_chart=True)

elif st.session_state.page == "Water":
    render_water_page()

elif st.session_state.page == "Waste":
    render_waste_page()

elif st.session_state.page == "Biodiversity":
    render_biodiversity_page()

elif st.session_state.page == "SDG":
    render_sdg_dashboard()

elif st.session_state.page == "Employee":
    render_employee_page()

elif st.session_state.page == "Diversity & Inclusion":
    render_diversity_page()

elif st.session_state.page == "Community":
    render_community_page()

elif st.session_state.page == "Board":
    render_board_page()

elif st.session_state.page == "Policies":
    render_policies_page()

elif st.session_state.page == "Compliance":
    render_compliance_page()

elif st.session_state.page == "Risk Management":
    render_risk_management_page()

elif st.session_state.page == "Reports":
    render_reports_router()

elif st.session_state.page == "BRSR":
    render_brsr_report()

elif st.session_state.page == "CDP":
    render_cdp_report()

elif st.session_state.page == "GRI":
    render_gri_report()

elif st.session_state.page == "TCFD":
    render_tcfd_report()

else:
    st.subheader(f"{st.session_state.page} section")
    st.info("This section is under development. Please select other pages from sidebar.")
