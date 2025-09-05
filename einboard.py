# streamlit_app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# ---------------------------
# Page Config & CSS (kept theme)
# ---------------------------
st.set_page_config(page_title="EinTrust Sustainability Dashboard", page_icon="🌍", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }
.stApp { background-color: #0d1117; color: #e6edf3; }
.kpi { background: linear-gradient(145deg, #12131a, #1a1b22); padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.5); margin-bottom: 10px; min-height: 120px; display: flex; flex-direction: column; justify-content: center; align-items: center; transition: transform 0.2s, box-shadow 0.2s; }
.kpi:hover { transform: scale(1.05); box-shadow: 0 8px 20px rgba(0,0,0,0.6); }
.kpi-value { font-size: 28px; font-weight: 700; color: #ffffff; margin-bottom: 5px; }
.kpi-unit { font-size: 16px; font-weight: 500; color: #cfd8dc; margin-bottom: 5px; }
.kpi-label { font-size: 14px; color: #cfd8dc; letter-spacing: 0.5px; }
.sdg-card { border-radius: 10px; padding: 15px; margin: 8px; display: inline-block; width: 100%; min-height: 110px; text-align: left; color: white; }
.sdg-number { font-weight: 700; font-size: 20px; }
.sdg-name { font-size: 16px; margin-bottom: 5px; }
.sdg-percent { font-size: 14px; }
@media (min-width: 768px) { .sdg-card { width: 220px; display: inline-block; } }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Sidebar & Navigation (keep behaviour like original)
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
    
    social_exp = st.expander("Social")
    with social_exp:
        sidebar_button("Employee")
        sidebar_button("Health & Safety")
        sidebar_button("CSR")
    
    gov_exp = st.expander("Governance")
    with gov_exp:
        sidebar_button("Board")
        sidebar_button("Policies")
        sidebar_button("Compliance")
        sidebar_button("Risk Management")
    
    sidebar_button("SDG")
    
    reports_exp = st.expander("Reports")
    with reports_exp:
        sidebar_button("BRSR")
        sidebar_button("GRI")
        sidebar_button("CDP")
        sidebar_button("TCFD")
    
    sidebar_button("Settings")
    sidebar_button("Log Out")

# ---------------------------
# Initialize Data structures
# ---------------------------
if "entries" not in st.session_state:
    # core GHG entries table (keeps original format and used by GHG page)
    st.session_state.entries = pd.DataFrame(columns=[
        "Scope","Activity","Sub-Activity","Specific Item","Quantity","Unit","Emissions_kgCO2e"
    ])

# renewable energy monthly entries (keeps original usage)
if "renewable_entries" not in st.session_state:
    st.session_state.renewable_entries = pd.DataFrame(columns=["Source","Location","Month","Energy_kWh","CO2e_kg","Type"])

# SDG simple engagement store (keeps original)
if "sdg_engagement" not in st.session_state:
    st.session_state.sdg_engagement = {i:0 for i in range(1,18)}

# Water and advanced water
if "water_data" not in st.session_state:
    st.session_state.water_data = pd.DataFrame(columns=["Location","Source","Month","Quantity_m3","Cost_INR"])
if "advanced_water_data" not in st.session_state:
    st.session_state.advanced_water_data = pd.DataFrame(columns=[
        "Location","Month","Rainwater_Harvested_m3","Water_Recycled_m3","Treatment_Before_Discharge","STP_ETP_Capacity_kL_day"
    ])

# Other environment/social/governance entries as dataframes
pages_to_init = {
    "waste_data": ["Location","Month","WasteType","Quantity_kg","DisposalMethod"],
    "biodiversity_data": ["Site","Month","Action","Area_ha","Notes"],
    "employee_data": ["EmployeeID","Role","Gender","HiringDate","TrainingHours","AttritionFlag"],
    "hs_data": ["Location","Month","IncidentCount","LostTimeInjuries","NearMisses"],
    "csr_data": ["Project","StartDate","Beneficiaries","Cost_INR","OutcomeNotes"],
    "board_data": ["BoardMember","Role","Independent","Gender","TenureYears"],
    "policies_data": ["PolicyName","AdoptedDate","Scope","Status"],
    "compliance_data": ["Regulation","Compliant(Y/N)","Notes","LastAuditDate"],
    "risk_data": ["Risk","Category","Likelihood","Impact","Mitigation","Owner"]
}
for key, cols in pages_to_init.items():
    if key not in st.session_state:
        st.session_state[key] = pd.DataFrame(columns=cols)

# ---------------------------
# Constants, lookups & emission factors (kept from original)
# ---------------------------
# (For brevity: reuse original long constants & calculate_emissions/energy logic)
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
        "2 Capital goods": {
            "Machinery & Equipment": None,
            "Buildings & Infrastructure": None
        },
        "3 Fuel- and energy-related activities (not included in Scope 1 or 2)": {
            "T&D Losses": None,
            "Fuel Production": None
        },
        "4 Upstream transportation & distribution": {
            "Incoming Transport": None,
            "Third-party Logistics": None
        },
        "5 Waste generated in operations": {
            "Landfill": None,
            "Recycling": None,
            "Composting": None
        },
        "6 Business travel": {
            "Air Travel": None,
            "Train Travel": None,
            "Taxi/Car Rental": None
        },
        "7 Employee commuting": {
            "Two-Wheelers": None,
            "Cars/Vans": None,
            "Public Transport": None
        },
        "8 Upstream leased assets": {
            "Leased Offices": None,
            "Leased Warehouses": None
        },
        "9 Downstream transportation & distribution": {
            "Distribution to Customers": None,
            "Retail/Distributor Transport": None
        },
        "10 Processing of sold products": {
            "Product Assembly": None
        },
        "11 Use of sold products": {
            "Product Use (Energy)": None
        },
        "12 End-of-life treatment of sold products": {
            "Recycling": None,
            "Landfill": None
        },
        "13 Downstream leased assets": {
            "Leased Operations": None
        },
        "14 Franchises": {
            "Franchise Operations": None
        },
        "15 Investments": {
            "Investments (Financial)": None
        }
    }
}

units_dict = {
    "Diesel Generator": "Liters","Petrol Generator": "Liters","LPG Boiler": "Liters","Coal Boiler": "kg","Biomass Furnace": "kg",
    "Diesel Vehicle": "Liters","Petrol Car": "Liters","CNG Vehicle": "m³","Diesel Forklift": "Liters","Petrol Two-Wheeler": "Liters",
    "Cement Production": "Tonnes","Steel Production": "Tonnes","Brick Kiln": "Tonnes","Textile Processing": "Tonnes",
    "Chemical Manufacturing": "Tonnes","Food Processing": "Tonnes","Refrigerant (HFC/HCFC)": "kg","Methane (CH₄)": "kg","SF₆": "kg",
    "Grid Electricity": "kWh","Diesel Generator Electricity": "kWh","Purchased Steam": "Tonnes","Purchased Cooling": "kWh",
    "Cement": "Tonnes","Steel": "Tonnes","Chemicals": "Tonnes","Textile": "Tonnes","Cardboard": "kg","Plastics": "kg","Glass": "kg",
    "Paper": "kg","Incoming Transport": "km traveled","Third-party Logistics": "km traveled","Air Travel": "Number of flights",
    "Train Travel": "km traveled","Taxi/Car Rental": "km traveled","Two-Wheelers": "km traveled","Cars/Vans": "km traveled",
    "Public Transport": "km traveled","Landfill": "kg","Recycling": "kg","Composting": "kg","Product Use (Energy)": "kWh"
}

emission_factors = {
    "Diesel": 2.68, "Petrol": 2.31, "LPG": 1.51, "CNG": 2.02, "Coal": 2.42, "Electricity": 0.82,
    "Cement": 900.0, "Steel": 1850.0, "Textile": 300.0, "Chemicals": 1200.0,
    "Cardboard": 0.9, "Plastics": 1.7, "Glass": 0.95, "Paper": 1.2,
    "Air Travel (domestic average)": 250.0, "Train per km": 0.05, "Taxi per km": 0.12,
    "TwoWheeler per km": 0.05, "Car per km": 0.12,
    "Landfill per kg": 1.0, "Recycling per kg": 0.3, "Composting per kg": 0.2,
    "Product use kWh": 0.82
}

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

# ---------------------------
# Helper: emission calculation (kept logic)
# ---------------------------
def calculate_emissions(scope, activity, sub_activity, specific_item, quantity, unit):
    missing_factor = False
    emissions = 0.0
    key_specific = (specific_item or "").strip()
    key_sub = (sub_activity or "").strip()
    key_act = (activity or "").strip()

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
        elif "Biomass" in key_sub:
            fuel_key = "Biomass"
        if fuel_key:
            factor = emission_factors.get(fuel_key)
            if factor is not None:
                emissions = float(quantity) * factor
            else:
                missing_factor = True
        else:
            if unit and unit.lower() in ["kwh","kwh"]:
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
            if key_specific in ["Cement","Steel","Textile","Chemicals","Paper","Cardboard","Plastics","Glass"]:
                factor = emission_factors.get(key_specific)
                if factor:
                    emissions = float(quantity) * factor
                else:
                    missing_factor = True
            elif key_sub in ["Air Travel"]:
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

# ---------------------------
# GHG Dashboard (preserve as-is but integrated)
# ---------------------------
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
        uploaded_file = st.file_uploader("Upload CSV/XLS/XLSX/PDF", type=["csv","xls","xlsx","pdf"])
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
                    # keep columns aligned to st.session_state.entries
                    for col in st.session_state.entries.columns:
                        if col not in df_file.columns:
                            df_file[col] = ""
                    st.session_state.entries = pd.concat([st.session_state.entries, df_file[st.session_state.entries.columns]], ignore_index=True)
                    st.success("File uploaded and emissions computed (where factor was available).")
            except Exception as e:
                st.error(f"Error reading file: {e}")

    # Show entries and totals
    if not st.session_state.entries.empty:
        st.subheader("All GHG Entries")
        display_df = st.session_state.entries.copy()
        # ensure numeric formatting where possible
        def safe_float(x):
            try:
                return f"{float(x):,.3f}"
            except:
                return x
        display_df["Quantity"] = display_df["Quantity"].apply(lambda x: safe_float(x))
        display_df["Emissions_kgCO2e"] = display_df["Emissions_kgCO2e"].apply(lambda x: safe_float(x))
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
            try:
                qty = float(r["Quantity"])
            except:
                qty = 0.0
            unit = r["Unit"]
            energy_kwh = 0.0
            if "Electricity" in sub or (isinstance(unit, str) and unit.lower()=="kwh"):
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
# Other Environment / Social / Governance Pages
# Each follows: KPIs -> Input Form -> All Entries
# ---------------------------
def render_water_page():
    st.subheader("Water")
    df = st.session_state.water_data.copy()
    total_water = df["Quantity_m3"].sum() if not df.empty else 0
    total_cost = df["Cost_INR"].sum() if not df.empty else 0
    st.markdown("<div class='kpi'><div class='kpi-value'>{:,}</div><div class='kpi-unit'>m³</div><div class='kpi-label'>Total Water Used</div></div>".format(int(total_water)), unsafe_allow_html=True)
    st.markdown("<div class='kpi'><div class='kpi-value'>₹ {:,}</div><div class='kpi-unit'></div><div class='kpi-label'>Estimated Cost</div></div>".format(int(total_cost)), unsafe_allow_html=True)

    st.subheader("Input Form")
    with st.form("water_input"):
        location = st.text_input("Location")
        source = st.selectbox("Source", ["Municipal","Groundwater","Tanker","Recycled"])
        month = st.selectbox("Month", months)
        qty = st.number_input("Quantity (m³)", min_value=0.0, format="%.3f")
        cost = st.number_input("Cost (INR)", min_value=0.0, format="%.2f")
        submitted = st.form_submit_button("Add Water Entry")
        if submitted:
            new = {"Location":location,"Source":source,"Month":month,"Quantity_m3":qty,"Cost_INR":cost}
            st.session_state.water_data = pd.concat([st.session_state.water_data, pd.DataFrame([new])], ignore_index=True)
            st.success("Water entry added.")

    st.subheader("All Water Entries")
    st.dataframe(st.session_state.water_data, use_container_width=True)

def render_waste_page():
    st.subheader("Waste")
    df = st.session_state.waste_data.copy()
    total_waste = df["Quantity_kg"].sum() if not df.empty else 0
    st.markdown("<div class='kpi'><div class='kpi-value'>{:,} kg</div><div class='kpi-unit'></div><div class='kpi-label'>Total Waste Generated</div></div>".format(int(total_waste)), unsafe_allow_html=True)

    st.subheader("Input Form")
    with st.form("waste_input"):
        location = st.text_input("Location")
        month = st.selectbox("Month", months)
        wtype = st.selectbox("Waste Type", ["Hazardous","Non-Hazardous","E-waste","Organic"])
        qty = st.number_input("Quantity (kg)", min_value=0.0, format="%.3f")
        method = st.selectbox("Disposal Method", ["Landfill","Incineration","Recycling","Composting"])
        submitted = st.form_submit_button("Add Waste Entry")
        if submitted:
            new = {"Location":location,"Month":month,"WasteType":wtype,"Quantity_kg":qty,"DisposalMethod":method}
            st.session_state.waste_data = pd.concat([st.session_state.waste_data, pd.DataFrame([new])], ignore_index=True)
            st.success("Waste entry added.")

    st.subheader("All Waste Entries")
    st.dataframe(st.session_state.waste_data, use_container_width=True)

def render_biodiversity_page():
    st.subheader("Biodiversity")
    df = st.session_state.biodiversity_data.copy()
    total_actions = len(df) if not df.empty else 0
    st.markdown("<div class='kpi'><div class='kpi-value'>{}</div><div class='kpi-unit'></div><div class='kpi-label'>Actions / Projects</div></div>".format(total_actions), unsafe_allow_html=True)

    st.subheader("Input Form")
    with st.form("bio_input"):
        site = st.text_input("Site Name")
        month = st.selectbox("Month", months)
        action = st.text_input("Action (e.g., Tree planting)")
        area = st.number_input("Area (ha)", min_value=0.0, format="%.3f")
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Add Biodiversity Entry")
        if submitted:
            new = {"Site":site,"Month":month,"Action":action,"Area_ha":area,"Notes":notes}
            st.session_state.biodiversity_data = pd.concat([st.session_state.biodiversity_data, pd.DataFrame([new])], ignore_index=True)
            st.success("Biodiversity entry added.")

    st.subheader("All Biodiversity Entries")
    st.dataframe(st.session_state.biodiversity_data, use_container_width=True)

def render_employee_page():
    st.subheader("Employee")
    df = st.session_state.employee_data.copy()
    emp_count = df.shape[0]
    total_training = df["TrainingHours"].sum() if "TrainingHours" in df.columns else 0
    attrition = df["AttritionFlag"].sum() if "AttritionFlag" in df.columns else 0
    st.markdown("<div class='kpi'><div class='kpi-value'>{}</div><div class='kpi-unit'></div><div class='kpi-label'>Employee Count</div></div>".format(emp_count), unsafe_allow_html=True)
    st.markdown("<div class='kpi'><div class='kpi-value'>{:.1f}</div><div class='kpi-unit'>hrs</div><div class='kpi-label'>Training Hours</div></div>".format(total_training), unsafe_allow_html=True)

    st.subheader("Input Form")
    with st.form("emp_input"):
        empid = st.text_input("Employee ID")
        role = st.text_input("Role")
        gender = st.selectbox("Gender", ["Male","Female","Other"])
        hire = st.date_input("Hiring Date")
        training = st.number_input("Training Hours", min_value=0.0, format="%.2f")
        attr = st.checkbox("Attrited (Yes)")
        submitted = st.form_submit_button("Add Employee Record")
        if submitted:
            new = {"EmployeeID":empid,"Role":role,"Gender":gender,"HiringDate":str(hire),"TrainingHours":training,"AttritionFlag":1 if attr else 0}
            st.session_state.employee_data = pd.concat([st.session_state.employee_data, pd.DataFrame([new])], ignore_index=True)
            st.success("Employee record added.")

    st.subheader("All Employee Entries")
    st.dataframe(st.session_state.employee_data, use_container_width=True)

def render_health_safety_page():
    st.subheader("Health & Safety")
    df = st.session_state.hs_data.copy()
    incidents = df["IncidentCount"].sum() if not df.empty else 0
    lti = df["LostTimeInjuries"].sum() if not df.empty else 0
    st.markdown("<div class='kpi'><div class='kpi-value'>{}</div><div class='kpi-unit'></div><div class='kpi-label'>Incidents</div></div>".format(int(incidents)), unsafe_allow_html=True)
    st.markdown("<div class='kpi'><div class='kpi-value'>{}</div><div class='kpi-unit'></div><div class='kpi-label'>Lost Time Injuries</div></div>".format(int(lti)), unsafe_allow_html=True)

    st.subheader("Input Form")
    with st.form("hs_input"):
        location = st.text_input("Location")
        month = st.selectbox("Month", months)
        incidents = st.number_input("Incident Count", min_value=0, step=1)
        lti = st.number_input("Lost Time Injuries", min_value=0, step=1)
        near = st.number_input("Near Misses", min_value=0, step=1)
        submitted = st.form_submit_button("Add H&S Entry")
        if submitted:
            new = {"Location":location,"Month":month,"IncidentCount":incidents,"LostTimeInjuries":lti,"NearMisses":near}
            st.session_state.hs_data = pd.concat([st.session_state.hs_data, pd.DataFrame([new])], ignore_index=True)
            st.success("H&S entry added.")

    st.subheader("All H&S Entries")
    st.dataframe(st.session_state.hs_data, use_container_width=True)

def render_csr_page():
    st.subheader("CSR")
    df = st.session_state.csr_data.copy()
    projects = df.shape[0]
    st.markdown("<div class='kpi'><div class='kpi-value'>{}</div><div class='kpi-unit'></div><div class='kpi-label'>CSR Projects</div></div>".format(projects), unsafe_allow_html=True)

    st.subheader("Input Form")
    with st.form("csr_input"):
        project = st.text_input("Project Name")
        start = st.date_input("Start Date")
        beneficiaries = st.number_input("Beneficiaries (approx)", min_value=0, step=1)
        cost = st.number_input("Cost (INR)", min_value=0.0, format="%.2f")
        notes = st.text_area("Outcome / Notes")
        submitted = st.form_submit_button("Add CSR Project")
        if submitted:
            new = {"Project":project,"StartDate":str(start),"Beneficiaries":beneficiaries,"Cost_INR":cost,"OutcomeNotes":notes}
            st.session_state.csr_data = pd.concat([st.session_state.csr_data, pd.DataFrame([new])], ignore_index=True)
            st.success("CSR project added.")

    st.subheader("All CSR Entries")
    st.dataframe(st.session_state.csr_data, use_container_width=True)

def render_board_page():
    st.subheader("Board")
    df = st.session_state.board_data.copy()
    size = df.shape[0]
    indep = df["Independent"].sum() if "Independent" in df.columns else 0
    st.markdown("<div class='kpi'><div class='kpi-value'>{}</div><div class='kpi-unit'></div><div class='kpi-label'>Board Size</div></div>".format(size), unsafe_allow_html=True)
    st.markdown("<div class='kpi'><div class='kpi-value'>{}</div><div class='kpi-unit'></div><div class='kpi-label'>Independent Directors</div></div>".format(int(indep)), unsafe_allow_html=True)

    st.subheader("Input Form")
    with st.form("board_input"):
        name = st.text_input("Board Member Name")
        role = st.text_input("Role")
        indep_flag = st.checkbox("Independent?")
        gender = st.selectbox("Gender", ["Male","Female","Other"])
        tenure = st.number_input("Tenure (years)", min_value=0.0, format="%.1f")
        submitted = st.form_submit_button("Add Board Member")
        if submitted:
            new = {"BoardMember":name,"Role":role,"Independent":1 if indep_flag else 0,"Gender":gender,"TenureYears":tenure}
            st.session_state.board_data = pd.concat([st.session_state.board_data, pd.DataFrame([new])], ignore_index=True)
            st.success("Board member added.")

    st.subheader("All Board Entries")
    st.dataframe(st.session_state.board_data, use_container_width=True)

def render_policies_page():
    st.subheader("Policies")
    df = st.session_state.policies_data.copy()
    st.markdown("<div class='kpi'><div class='kpi-value'>{}</div><div class='kpi-unit'></div><div class='kpi-label'>Policies Recorded</div></div>".format(df.shape[0]), unsafe_allow_html=True)

    st.subheader("Input Form")
    with st.form("policies_input"):
        pname = st.text_input("Policy Name")
        adopted = st.date_input("Adopted Date")
        scope = st.text_input("Scope (e.g., Company-wide)")
        status = st.selectbox("Status", ["Draft","Adopted","Under Review"])
        submitted = st.form_submit_button("Add Policy")
        if submitted:
            new = {"PolicyName":pname,"AdoptedDate":str(adopted),"Scope":scope,"Status":status}
            st.session_state.policies_data = pd.concat([st.session_state.policies_data, pd.DataFrame([new])], ignore_index=True)
            st.success("Policy added.")

    st.subheader("All Policies")
    st.dataframe(st.session_state.policies_data, use_container_width=True)

def render_compliance_page():
    st.subheader("Compliance")
    df = st.session_state.compliance_data.copy()
    st.markdown("<div class='kpi'><div class='kpi-value'>{}</div><div class='kpi-unit'></div><div class='kpi-label'>Compliance Items</div></div>".format(df.shape[0]), unsafe_allow_html=True)

    st.subheader("Input Form")
    with st.form("compliance_input"):
        regulation = st.text_input("Regulation / Standard")
        compliant = st.selectbox("Compliant?", ["Yes","No","Partial"])
        notes = st.text_area("Notes")
        last_audit = st.date_input("Last Audit Date")
        submitted = st.form_submit_button("Add Compliance Record")
        if submitted:
            new = {"Regulation":regulation,"Compliant(Y/N)":compliant,"Notes":notes,"LastAuditDate":str(last_audit)}
            st.session_state.compliance_data = pd.concat([st.session_state.compliance_data, pd.DataFrame([new])], ignore_index=True)
            st.success("Compliance record added.")

    st.subheader("All Compliance Entries")
    st.dataframe(st.session_state.compliance_data, use_container_width=True)

def render_risk_page():
    st.subheader("Risk Management")
    df = st.session_state.risk_data.copy()
    st.markdown("<div class='kpi'><div class='kpi-value'>{}</div><div class='kpi-unit'></div><div class='kpi-label'>Risks Logged</div></div>".format(df.shape[0]), unsafe_allow_html=True)

    st.subheader("Input Form")
    with st.form("risk_input"):
        risk = st.text_input("Risk Description")
        category = st.selectbox("Category", ["Strategic","Operational","Financial","Compliance","Environmental"])
        likelihood = st.selectbox("Likelihood", ["Low","Medium","High"])
        impact = st.selectbox("Impact", ["Low","Medium","High"])
        mitigation = st.text_area("Mitigation Measures")
        owner = st.text_input("Owner")
        submitted = st.form_submit_button("Add Risk")
        if submitted:
            new = {"Risk":risk,"Category":category,"Likelihood":likelihood,"Impact":impact,"Mitigation":mitigation,"Owner":owner}
            st.session_state.risk_data = pd.concat([st.session_state.risk_data, pd.DataFrame([new])], ignore_index=True)
            st.success("Risk record added.")

    st.subheader("All Risk Entries")
    st.dataframe(st.session_state.risk_data, use_container_width=True)

# ---------------------------
# Helper: PDF export for reports
# ---------------------------
def generate_pdf_bytes(title, rows):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf)
    styles = getSampleStyleSheet()
    story = [Paragraph(title, styles['Title']), Spacer(1,12)]
    # table header and rows
    data = [["Indicator","Value"]]
    for k,v in rows.items():
        data.append([k, str(v)])
    table = Table(data, colWidths=[300,200])
    tbl_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#333333")),
        ('TEXTCOLOR',(0,0),(-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND',(0,1),(-1,-1), colors.HexColor("#111214")),
        ('TEXTCOLOR',(0,1),(-1,-1), colors.white),
    ])
    table.setStyle(tbl_style)
    story.append(table)
    story.append(Spacer(1,12))
    doc.build(story)
    buf.seek(0)
    return buf.getvalue()

# ---------------------------
# Mapping rules: map inputs to BRSR / GRI / CDP / TCFD items
# These are illustrative and connect to session_state dataframes and GHG entries.
# ---------------------------
def kpi_total_scope(scope_label):
    # compute total emissions (kg CO2e) for a given scope label from st.session_state.entries
    try:
        df = st.session_state.entries
        if df.empty:
            return 0.0
        df2 = df[df["Scope"] == scope_label]
        return float(df2["Emissions_kgCO2e"].astype(float).sum() / 1000.0)  # convert kg -> tonne
    except Exception:
        return 0.0

def kpi_energy_total_mwh():
    try:
        # sum energy_kwh from renewables + attempt derive from entries (Scope1/2) if available (convert kWh->MWh)
        renew = st.session_state.renewable_entries.copy() if not st.session_state.renewable_entries.empty else pd.DataFrame()
        renew_kwh = renew["Energy_kWh"].sum() if not renew.empty else 0.0
        # try to estimate energy from scope1/2 entries in entries
        df = st.session_state.entries.copy() if not st.session_state.entries.empty else pd.DataFrame()
        energy_kwh = 0.0
        if not df.empty:
            # crude heuristic: if unit is kWh treat quantity as kWh
            kwh_rows = df[df["Unit"].str.lower()=="kwh"]
            if not kwh_rows.empty:
                energy_kwh += kwh_rows["Quantity"].astype(float).sum()
        total_kwh = renew_kwh + energy_kwh
        return total_kwh / 1000.0
    except Exception:
        return 0.0

def kpi_water_ml():
    try:
        df = st.session_state.water_data.copy() if not st.session_state.water_data.empty else pd.DataFrame()
        if df.empty:
            return 0.0
        total_m3 = df["Quantity_m3"].astype(float).sum()
        return total_m3 / 1000.0
    except Exception:
        return 0.0

# Mapping dictionaries (example question/disclosure-level mappings)
def build_brsr_rows():
    s = st.session_state
    rows = {}
    rows["P6 Q1: Total GHG Emissions (tCO2e) - Scope1"] = round(kpi_total_scope("Scope 1"),3)
    rows["P6 Q1: Total GHG Emissions (tCO2e) - Scope2"] = round(kpi_total_scope("Scope 2"),3)
    rows["P6 Q1: Total GHG Emissions (tCO2e) - Scope3"] = round(kpi_total_scope("Scope 3"),3)
    rows["P6 Q2: Energy Consumption (MWh)"] = round(kpi_energy_total_mwh(),3)
    rows["P6 Q3: Water Consumption (ML)"] = round(kpi_water_ml(),3)
    rows["P6 Q4: Waste (tons)"] = round(st.session_state.waste_data["Quantity_kg"].sum()/1000.0 if not st.session_state.waste_data.empty else 0.0,3)
    rows["P3 Q1: Employees"] = st.session_state.employee_data.shape[0] if not st.session_state.employee_data.empty else 0
    rows["P1 Q1: % Independent Directors"] = round((st.session_state.board_data["Independent"].sum() / max(1, st.session_state.board_data.shape[0]) * 100) if not st.session_state.board_data.empty else 0.0,2)
    return rows

def build_cdp_rows():
    rows = {}
    rows["C6.1 Scope1 (tCO2e)"] = round(kpi_total_scope("Scope 1"),3)
    rows["C6.2 Scope2 (tCO2e)"] = round(kpi_total_scope("Scope 2"),3)
    rows["C6.3 Scope3 (tCO2e)"] = round(kpi_total_scope("Scope 3"),3)
    rows["C8.2 Energy (MWh)"] = round(kpi_energy_total_mwh(),3)
    rows["C2.3 Risk Management Process"] = "Yes" if not st.session_state.risk_data.empty else "No"
    return rows

def build_gri_rows():
    rows = {}
    rows["305-1 Direct (Scope 1) (tCO2e)"] = round(kpi_total_scope("Scope 1"),3)
    rows["305-2 Indirect (Scope 2) (tCO2e)"] = round(kpi_total_scope("Scope 2"),3)
    rows["305-3 Other Indirect (Scope 3) (tCO2e)"] = round(kpi_total_scope("Scope 3"),3)
    rows["302-1 Energy (MWh)"] = round(kpi_energy_total_mwh(),3)
    rows["303-1 Water (ML)"] = round(kpi_water_ml(),3)
    rows["401-1 Employee Count"] = st.session_state.employee_data.shape[0] if not st.session_state.employee_data.empty else 0
    rows["405-1 % Women Employees"] = round((st.session_state.employee_data["Gender"].value_counts().get("Female",0)/max(1,st.session_state.employee_data.shape[0])*100) if not st.session_state.employee_data.empty else 0.0,2)
    return rows

def build_tcfd_rows():
    rows = {}
    rows["Governance: Board Oversight of Climate"] = "Yes" if st.session_state.board_data["Independent"].sum() > 0 if not st.session_state.board_data.empty else False else "No"
    rows["Strategy: Climate Risks Present"] = "Yes" if not st.session_state.risk_data.empty else "No"
    rows["Risk Mgmt: Formal Process"] = "Yes" if not st.session_state.risk_data.empty else "No"
    rows["Metrics: Scope1+2 (tCO2e)"] = round(kpi_total_scope("Scope 1")+kpi_total_scope("Scope 2"),3)
    rows["Metrics: Energy (MWh)"] = round(kpi_energy_total_mwh(),3)
    return rows

# ---------------------------
# Reports Pages (BRSR, CDP, GRI, TCFD)
# Each shows KPI section first, then Export PDF button
# ---------------------------
def render_reports():
    st.title("Reports")
    tab1, tab2, tab3, tab4 = st.tabs(["BRSR", "CDP", "GRI", "TCFD"])
    with tab1:
        st.header("BRSR (KPI mapping)")
        brsr = build_brsr_rows()
        for k,v in brsr.items():
            st.metric(k, v)
        pdf_bytes = generate_pdf_bytes("BRSR Report", brsr)
        st.download_button("Export BRSR PDF", data=pdf_bytes, file_name="BRSR_Report.pdf", mime="application/pdf")
    with tab2:
        st.header("CDP (KPI mapping)")
        cdp = build_cdp_rows()
        for k,v in cdp.items():
            st.metric(k, v)
        pdf_bytes = generate_pdf_bytes("CDP Report", cdp)
        st.download_button("Export CDP PDF", data=pdf_bytes, file_name="CDP_Report.pdf", mime="application/pdf")
    with tab3:
        st.header("GRI (KPI mapping)")
        gri = build_gri_rows()
        for k,v in gri.items():
            st.metric(k, v)
        pdf_bytes = generate_pdf_bytes("GRI Report", gri)
        st.download_button("Export GRI PDF", data=pdf_bytes, file_name="GRI_Report.pdf", mime="application/pdf")
    with tab4:
        st.header("TCFD (KPI mapping)")
        tcfd = build_tcfd_rows()
        for k,v in tcfd.items():
            st.metric(k, v)
        pdf_bytes = generate_pdf_bytes("TCFD Report", tcfd)
        st.download_button("Export TCFD PDF", data=pdf_bytes, file_name="TCFD_Report.pdf", mime="application/pdf")

# ---------------------------
# SDG Dashboard (kept simple)
# ---------------------------
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
# Page Router: keep Home/GHG/Energy pages intact
# Add the rest pages below
# ---------------------------
def render_home():
    st.title("EinTrust Sustainability Dashboard")
    st.markdown("Welcome to the consolidated sustainability dashboard. Use the sidebar to navigate.")
    # show small preview KPIs from GHG & Energy
    st.subheader("Quick KPIs")
    s1 = kpi_total_scope("Scope 1")
    s2 = kpi_total_scope("Scope 2")
    s3 = kpi_total_scope("Scope 3")
    energy_mwh = kpi_energy_total_mwh()
    st.metric("Scope 1 Emissions (tCO2e)", round(s1,3))
    st.metric("Scope 2 Emissions (tCO2e)", round(s2,3))
    st.metric("Scope 3 Emissions (tCO2e)", round(s3,3))
    st.metric("Total Energy (MWh)", round(energy_mwh,3))
    st.info("Use the GHG and Energy pages for detailed input. All other pages follow KPI -> Input -> Entries pattern.")

# ---------------------------
# Map sidebar label to page function
# ---------------------------
page_map = {
    "Home": render_home,
    "GHG": lambda: render_ghg_dashboard(include_data=True, show_chart=True),
    "Energy": lambda: render_energy_dashboard(include_input=True, show_chart=True),
    "Water": render_water_page,
    "Waste": render_waste_page,
    "Biodiversity": render_biodiversity_page,
    "Employee": render_employee_page,
    "Health & Safety": render_health_safety_page,
    "CSR": render_csr_page,
    "Board": render_board_page,
    "Policies": render_policies_page,
    "Compliance": render_compliance_page,
    "Risk Management": render_risk_page,
    "SDG": render_sdg_dashboard,
    "BRSR": render_reports,  # when user clicks BRSR in sidebar, show full Reports (tabbed)
    "GRI": render_reports,
    "CDP": render_reports,
    "TCFD": render_reports,
    "Reports": render_reports,
    "Settings": lambda: st.info("Settings page (placeholder)"),
    "Log Out": lambda: st.info("Log out (placeholder)")
}

# ---------------------------
# Main
# ---------------------------
def main():
    # find page in st.session_state.page (sidebar buttons set it)
    page = st.session_state.page if "page" in st.session_state else "Home"
    # fallback: make sure Home appears when nothing matches
    if page not in page_map:
        page = "Home"
    page_map[page]()

if __name__ == "__main__":
    main()
