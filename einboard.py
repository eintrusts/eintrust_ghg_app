# app.py
# Complete rewritten app with full Scope-3 15 categories + emissions calc
# (GHG and Energy pages are preserved exactly as provided)
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

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
# Sidebar & Navigation (unchanged behaviour)
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
# Initialize Data (entries now include Emissions)
# ---------------------------
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

# initialize other dataframes for added pages
if "waste_data" not in st.session_state:
    st.session_state.waste_data = pd.DataFrame(columns=["Location","Waste_Type","Month","Quantity_kg","Treatment","Emissions_kgCO2e"])
if "biodiversity_data" not in st.session_state:
    st.session_state.biodiversity_data = pd.DataFrame(columns=["Site","Impact_Type","Area_ha","Mitigation","Notes"])
if "employee_data" not in st.session_state:
    st.session_state.employee_data = pd.DataFrame(columns=["Year","Total_Employees","New_Hires","Attrition_rate","Training_Hours"])
if "hs_data" not in st.session_state:
    st.session_state.hs_data = pd.DataFrame(columns=["Site","Incidents","Lost_Time_Days","Near_Misses","Safety_Training_Hours"])
if "csr_data" not in st.session_state:
    st.session_state.csr_data = pd.DataFrame(columns=["Project","Spend_INR","Beneficiaries","Year"])
if "board_data" not in st.session_state:
    st.session_state.board_data = pd.DataFrame(columns=["Board_Size","Independent_Directors","Gender_Diversity","Meetings_per_year"])
if "policy_data" not in st.session_state:
    st.session_state.policy_data = pd.DataFrame(columns=["Policy_Name","Implemented","Last_Review_Date","Notes"])
if "compliance_data" not in st.session_state:
    st.session_state.compliance_data = pd.DataFrame(columns=["Regulation","Status","Notes","Last_Reviewed"])
if "risk_data" not in st.session_state:
    st.session_state.risk_data = pd.DataFrame(columns=["Risk","Category","Likelihood","Impact","Mitigation","Owner"])

# ---------------------------
# Constants and lookups
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
    # Full set of GHG Protocol Scope 3 categories (15)
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

# units used for auto-filling unit dropdowns
units_dict = {
    # Scope1 & 2 common
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
    "Cement Production": "Tonnes",
    "Steel Production": "Tonnes",
    "Brick Kiln": "Tonnes",
    "Textile Processing": "Tonnes",
    "Chemical Manufacturing": "Tonnes",
    "Food Processing": "Tonnes",
    "Refrigerant (HFC/HCFC)": "kg",
    "Methane (CH₄)": "kg",
    "SF₆": "kg",
    "Grid Electricity": "kWh",
    "Diesel Generator Electricity": "kWh",
    "Purchased Steam": "Tonnes",
    "Purchased Cooling": "kWh",
    # Scope 3 examples
    "Cement": "Tonnes",
    "Steel": "Tonnes",
    "Chemicals": "Tonnes",
    "Textile": "Tonnes",
    "Cardboard": "kg",
    "Plastics": "kg",
    "Glass": "kg",
    "Paper": "kg",
    "Incoming Transport": "km traveled",
    "Third-party Logistics": "km traveled",
    "Air Travel": "Number of flights",
    "Train Travel": "km traveled",
    "Taxi/Car Rental": "km traveled",
    "Two-Wheelers": "km traveled",
    "Cars/Vans": "km traveled",
    "Public Transport": "km traveled",
    "Landfill": "kg",
    "Recycling": "kg",
    "Composting": "kg",
    "Product Use (Energy)": "kWh"
}

# Basic emission factors (starter). Units: kg CO2e per unit (unit matches units_dict)
emission_factors = {
    # fuels
    "Diesel": 2.68,   # kg CO2e per liter
    "Petrol": 2.31,
    "LPG": 1.51,
    "CNG": 2.02,      # per m3 approx
    "Coal": 2.42,     # per kg approx
    "Electricity": 0.82,  # kg CO2e per kWh (India avg)
    # Scope 1 process defaults (per tonne)
    "Cement": 900.0,     # kg CO2e per tonne (example)
    "Steel": 1850.0,     # kg CO2e per tonne (example)
    "Textile": 300.0,
    "Chemicals": 1200.0,
    # packaging / materials (per kg)
    "Cardboard": 0.9,   # kg CO2e per kg
    "Plastics": 1.7,
    "Glass": 0.95,
    "Paper": 1.2,
    # travel
    "Air Travel (domestic average)": 250.0, # per flight approx
    "Train per km": 0.05,
    "Taxi per km": 0.12,
    "TwoWheeler per km": 0.05,
    "Car per km": 0.12,
    # waste
    "Landfill per kg": 1.0,
    "Recycling per kg": 0.3,
    "Composting per kg": 0.2,
    # product use
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
# Helper: emission calculation for an arbitrary entry
# ---------------------------
def calculate_emissions(scope, activity, sub_activity, specific_item, quantity, unit):
    """
    Return emissions in kg CO2e for a single entry.
    Logic:
      - For Scope 1 & 2, try to derive factor from sub_activity or activity (common fuels).
      - For Scope 3, check specific_item first, then sub_activity, then activity with heuristic mapping.
      - If factor not found, return 0 and a flag to indicate missing factor.
    """
    missing_factor = False
    emissions = 0.0

    # Normalize keys slightly
    key_specific = (specific_item or "").strip()
    key_sub = (sub_activity or "").strip()
    key_act = (activity or "").strip()

    # Scope 1 & 2 common fuels
    # Map keywords to emission_factors keys
    if scope in ["Scope 1","Scope 2"]:
        # check sub_activity match to fuel
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
        # compute
        if fuel_key:
            factor = emission_factors.get(fuel_key)
            if factor is not None:
                emissions = float(quantity) * factor
            else:
                missing_factor = True
        else:
            # fallback: if unit is kWh and electricity factor exists
            if unit and unit.lower() in ["kwh","kwh"]:
                factor = emission_factors.get("Electricity")
                if factor is not None:
                    emissions = float(quantity) * factor
                else:
                    missing_factor = True
            else:
                missing_factor = True

    else:
        # Scope 3 heuristics
        # 1) check exact specific_item in emission_factors
        if key_specific and key_specific in emission_factors:
            emissions = float(quantity) * emission_factors[key_specific]
        else:
            # Map common possibilities
            if key_specific in ["Cement","Steel","Textile","Chemicals","Paper","Cardboard","Plastics","Glass"]:
                factor = emission_factors.get(key_specific)
                if factor:
                    emissions = float(quantity) * factor
                else:
                    missing_factor = True
            elif key_sub in ["Air Travel"]:
                # if unit is "Number of flights" - use per-flight factor
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
                    factor = emission_factors.get("TwoWheeler per km")
                    if factor:
                        emissions = float(quantity) * factor
                    else:
                        missing_factor = True
            elif key_sub in ["Landfill","Recycling","Composting"]:
                # units expected kg
                mapping = {"Landfill":"Landfill per kg","Recycling":"Recycling per kg","Composting":"Composting per kg"}
                factor = emission_factors.get(mapping.get(key_sub))
                if factor:
                    emissions = float(quantity) * factor
                else:
                    missing_factor = True
            elif unit and unit.lower() in ["kwh"]:
                # product use energy
                factor = emission_factors.get("Product use kWh")
                if factor:
                    emissions = float(quantity) * factor
                else:
                    missing_factor = True
            else:
                missing_factor = True

    return emissions, missing_factor

# ---------------------------
# GHG Dashboard
# ---------------------------
def render_ghg_dashboard(include_data=True, show_chart=True):
    st.subheader("GHG Emissions")

    if include_data:
        # Scope selection
        scope = st.selectbox("Select Scope", ["Scope 1","Scope 2","Scope 3"], index=0)

        if scope != "Scope 3":
            # For Scope1/2 use existing activity mapping
            activity = st.selectbox("Select Activity", list(scope_activities[scope].keys()))
            sub_options = scope_activities[scope][activity]
            sub_activity = st.selectbox("Select Sub-Activity", list(sub_options.keys()))
            # show explanation
            st.info(sub_options[sub_activity])
            specific_item = ""
        else:
            # Scope 3 - show the 15 categories
            activity = st.selectbox("Select Scope 3 Category", list(scope_activities["Scope 3"].keys()))
            sub_dict = scope_activities["Scope 3"][activity]
            sub_activity = st.selectbox("Select Sub-Category", list(sub_dict.keys()))
            # if sub_dict[sub_activity] is list -> let user pick specific item
            specific_item = ""
            if isinstance(sub_dict[sub_activity], list):
                specific_item = st.selectbox("Select Specific Item", sub_dict[sub_activity])
            else:
                # allow user to optionally type a specific item (for examples or supplier-specific)
                specific_item = st.text_input("Specific Item (optional — e.g. 'Branded Paper 80gsm')", value="")

        # Unit auto-fill
        if scope != "Scope 3":
            unit = units_dict.get(sub_activity, "")
        else:
            # Scope3 units heuristics
            if sub_activity in ["Air Travel"]:
                unit = "Number of flights"
            elif sub_activity in ["Train Travel","Taxi/Car Rental","Cars/Vans","Two-Wheelers","Public Transport","Incoming Transport","Third-party Logistics","Distribution to Customers","Retail/Distributor Transport"]:
                unit = "km traveled"
            elif sub_activity in ["Cement Production","Raw Materials","Packaging","Processing of sold products","Use of sold products"]:
                # let specific_item determine unit if available, else default tonnes or kg
                unit = units_dict.get(specific_item, "kg / Tonnes")
            elif sub_activity in ["Landfill","Recycling","Composting","End-of-life treatment"]:
                unit = "kg"
            else:
                unit = "kg / Tonnes"

        quantity = st.number_input(f"Enter Quantity ({unit})", min_value=0.0, format="%.3f")

        # Add manual entry -> compute emissions immediately
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

        # File upload
        st.subheader("Optional: Upload File")
        uploaded_file = st.file_uploader("Upload CSV/XLS/XLSX/PDF", type=["csv","xls","xlsx","pdf"])
        if uploaded_file:
            try:
                if uploaded_file.name.endswith(".csv"):
                    df_file = pd.read_csv(uploaded_file)
                else:
                    df_file = pd.read_excel(uploaded_file)
                # validate
                needed = {"Scope","Activity","Sub-Activity","Quantity","Unit"}
                if not needed.issubset(set(df_file.columns)):
                    st.error(f"Uploaded file must contain columns: {needed}")
                else:
                    # compute emissions per row
                    df_file = df_file.fillna("")
                    emissions_list = []
                    for _, r in df_file.iterrows():
                        emissions, missing = calculate_emissions(r["Scope"], r["Activity"], r["Sub-Activity"], r.get("Specific Item",""), r["Quantity"], r["Unit"])
                        emissions_list.append(round(float(emissions),3))
                    df_file["Emissions_kgCO2e"] = emissions_list
                    st.session_state.entries = pd.concat([st.session_state.entries, df_file[st.session_state.entries.columns]], ignore_index=True)
                    st.success("File uploaded and emissions computed (where factor was available).")
            except Exception as e:
                st.error(f"Error reading file: {e}")

    # Show entries and totals
    if not st.session_state.entries.empty:
        st.subheader("All GHG Entries")
        display_df = st.session_state.entries.copy()
        display_df["Quantity"] = display_df["Quantity"].apply(lambda x: f"{float(x):,.3f}")
        display_df["Emissions_kgCO2e"] = display_df["Emissions_kgCO2e"].apply(lambda x: f"{float(x):,.3f}")
        st.dataframe(display_df, use_container_width=True)
        csv = st.session_state.entries.to_csv(index=False).encode('utf-8')
        st.download_button("Download GHG Entries as CSV", csv, "ghg_entries_with_emissions.csv", "text/csv")

# ---------------------------
# Energy Dashboard
# ---------------------------
def render_energy_dashboard(include_input=True, show_chart=True):
    st.subheader("Energy")
    df = st.session_state.entries.copy()

    calorific_values = {"Diesel":35.8,"Petrol":34.2,"LPG":46.1,"CNG":48,"Coal":24,"Biomass":15}
    emission_factors_local = emission_factors  # reuse

    # Build scope1_2_data from entries where unit is energy/fuel
    scope1_2_data = pd.DataFrame()
    if not df.empty:
        scope1_2_df = df[df["Scope"].isin(["Scope 1","Scope 2"])].copy()
        # Try to convert Sub-Activity to energy_kwh and co2 using same logic as calculate_emissions
        energy_rows = []
        for _, r in scope1_2_df.iterrows():
            sub = r["Sub-Activity"]
            qty = float(r["Quantity"])
            unit = r["Unit"]
            energy_kwh = 0.0
            # If electricity
            if "Electricity" in sub or unit.lower()=="kwh":
                energy_kwh = qty
                co2e = qty * emission_factors_local.get("Electricity",0)
            else:
                # match fuel word
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
                    # fallback: set energy 0 and try to compute co2 from stored Emissions_kgCO2e if present
                    energy_kwh = 0.0
                    co2e = float(r.get("Emissions_kgCO2e",0.0))
            energy_rows.append({
                "Location": r.get("Specific Item","").strip() or "Unknown Location",
                "Fuel": sub,
                "Quantity": qty,
                "Energy_kWh": energy_kwh,
                "CO2e_kg": co2e,
                "Type": "Fossil" if co2e>0 else "Unknown",
                "Month": np.random.choice(months)  # if you have month from entries you can use it
            })
        if energy_rows:
            scope1_2_data = pd.DataFrame(energy_rows)

    # Combine with renewables
    all_energy = pd.concat([scope1_2_data, st.session_state.renewable_entries], ignore_index=True) if not st.session_state.renewable_entries.empty else scope1_2_data
    if not all_energy.empty and "Month" in all_energy:
        all_energy["Month"] = pd.Categorical(all_energy["Month"], categories=months, ordered=True)

    # KPIs
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

    # Charts
    if show_chart and not all_energy.empty:
        monthly_trend = all_energy.groupby(["Month","Type"])["Energy_kWh"].sum().reset_index()
        st.subheader("Monthly Energy Consumption (kWh)")
        fig = px.bar(monthly_trend, x="Month", y="Energy_kWh", color="Type", barmode="stack", color_discrete_map=ENERGY_COLORS)
        st.plotly_chart(fig, use_container_width=True)

    # Add renewable entries (annual)
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
            # spread evenly across FY months
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
# SDG Dashboard
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
# Additional Pages (Environment / Social / Governance Inputs)
# These pages add data to session_state dataframes and session_state keys
# ---------------------------

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Water Dashboard", layout="wide")

st.title("💧 Water Consumption Dashboard")

# ----- SESSION STATE INITIALIZATION -----
if 'water_data' not in st.session_state:
    st.session_state['water_data'] = []

# ----- FILTER SELECTION -----
st.subheader("Filter Water Data")
filter_option = st.selectbox("Select Data to Display:", ["All Entries", "Annual Only", "Monthly Only"])

# Prepare filtered dataframe
if len(st.session_state['water_data']) > 0:
    df_all = pd.DataFrame(st.session_state['water_data'])
    if filter_option == "Annual Only":
        df_plot = df_all[df_all['frequency'] == "Annual"]
    elif filter_option == "Monthly Only":
        df_plot = df_all[df_all['frequency'] == "Monthly"]
    else:
        df_plot = df_all.copy()
else:
    df_all = pd.DataFrame()
    df_plot = pd.DataFrame()

# ----- KPI BLOCKS -----
st.subheader("Key Performance Indicators (KPIs)")

def kpi_card(title, value, color, tooltip):
    st.markdown(
        f"""
        <div style="
            background-color:{color};
            padding:20px;
            border-radius:10px;
            text-align:center;
            color:white;
            font-size:22px;
            font-weight:bold;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.2);
            margin-bottom:10px;
            " title="{tooltip}">
            {title}<br><span style='font-size:28px'>{value}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

if not df_plot.empty:
    total_water = df_plot['water_consumption'].sum()
    avg_water = df_plot['water_consumption'].mean()
    max_water = df_plot['water_consumption'].max()
    
    # Count entries
    total_entries = len(df_plot)
    annual_entries = len(df_plot[df_plot['frequency']=='Annual'])
    monthly_entries = len(df_plot[df_plot['frequency']=='Monthly'])
else:
    total_water = 0
    avg_water = 0
    max_water = 0
    total_entries = 0
    annual_entries = 0
    monthly_entries = 0

# Highlight peak if unusually high (>1.5× avg)
peak_color = "#d62728" if max_water > 1.5*avg_water and avg_water>0 else "#2ca02c"

kpi_cols = st.columns(3)
with kpi_cols[0]:
    kpi_card("Total Water (m³)", f"{total_water:.2f}", "#1f77b4", f"Total {total_entries} entries")
with kpi_cols[1]:
    kpi_card("Average Consumption (m³)", f"{avg_water:.2f}", "#ff7f0e", f"Annual: {annual_entries}, Monthly: {monthly_entries}")
with kpi_cols[2]:
    kpi_card("Peak Consumption (m³)", f"{max_water:.2f}", peak_color, "Peak value of all entries")

st.markdown("---")

# ----- CHART -----
st.subheader("Water Consumption Trend")
if not df_plot.empty:
    df_plot['label'] = df_plot.apply(
        lambda x: x['timestamp'] if x['frequency']=='Annual' else f"{x['month']} ({x['timestamp'][:10]})",
        axis=1
    )
    
    fig = px.line(
        df_plot,
        x='label',
        y='water_consumption',
        markers=True,
        title="Water Consumption Over Time",
        labels={"label":"Entry (Date / Month)", "water_consumption":"Water Consumption (m³)"}
    )
    
    # Highlight peaks in chart
    peak_index = df_plot['water_consumption'].idxmax() if not df_plot.empty else None
    fig.update_traces(line=dict(color="#00BFFF", width=3), marker=dict(size=8))
    if peak_index is not None:
        fig.add_scatter(
            x=[df_plot.loc[peak_index, 'label']],
            y=[df_plot.loc[peak_index, 'water_consumption']],
            mode='markers+text',
            marker=dict(color='red', size=12),
            text=["Peak!"],
            textposition="top center",
            showlegend=False
        )
    fig.update_layout(xaxis_tickangle=-45, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No data available for this selection.")

st.markdown("---")

# ----- DATA INPUT FORM -----
st.subheader("Add Water Data Entry")
with st.form("water_input_form"):
    frequency = st.selectbox("Select Frequency", ["Annual", "Monthly"])
    
    month = None
    if frequency == "Monthly":
        month = st.selectbox("Select Month", [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ])
    
    water_consumption = st.number_input("Enter Water Consumption (m³)", min_value=0.0, step=0.1)
    
    submitted = st.form_submit_button("Submit Entry")
    
    if submitted:
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "frequency": frequency,
            "month": month,
            "water_consumption": water_consumption
        }
        st.session_state['water_data'].append(entry)
        st.success("Water data entry added successfully!")
        st.experimental_rerun()  # Refresh to update KPIs and chart automatically

st.markdown("---")

# ----- DATA TABLE AND DOWNLOAD -----
st.subheader("All Water Data Entries")
if not df_all.empty:
    st.dataframe(df_all)
    
    csv = df_all.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download All Entries as CSV",
        data=csv,
        file_name='water_data_entries.csv',
        mime='text/csv'
    )
else:
    st.info("No entries yet. Please add data above.")


# Waste page
def render_waste_page():
    st.subheader("Waste - Input")
    with st.form("waste_form", clear_on_submit=False):
        loc = st.text_input("Location / Site", key="w_loc")
        wtype = st.selectbox("Waste Type", ["Hazardous","Non-Hazardous","E-waste","Organic"])
        month = st.selectbox("Month", months, key="w_month")
        qty = st.number_input("Quantity (kg)", min_value=0.0, value=0.0)
        treatment = st.selectbox("Treatment", ["Landfill","Recycling","Incineration","Composting"])
        # optional compute approximate emissions
        est_em = 0.0
        if treatment == "Landfill":
            est_em = qty * emission_factors.get("Landfill per kg", 0)
        elif treatment == "Recycling":
            est_em = qty * emission_factors.get("Recycling per kg", 0)
        elif treatment == "Composting":
            est_em = qty * emission_factors.get("Composting per kg", 0)
        submit = st.form_submit_button("Add Waste Record")
        if submit:
            row = {"Location":loc,"Waste_Type":wtype,"Month":month,"Quantity_kg":qty,"Treatment":treatment,"Emissions_kgCO2e":round(est_em,3)}
            st.session_state.waste_data = pd.concat([st.session_state.waste_data, pd.DataFrame([row])], ignore_index=True)
            st.success("Waste record added.")

    if not st.session_state.waste_data.empty:
        st.write("Waste records")
        st.dataframe(st.session_state.waste_data)

# Biodiversity page
def render_biodiversity_page():
    st.subheader("Biodiversity - Input")
    with st.form("bio_form", clear_on_submit=False):
        site = st.text_input("Site Name")
        impact = st.selectbox("Impact Type", ["Habitat loss","Fragmentation","Pollution","Invasive species","Other"])
        area = st.number_input("Area affected (ha)", min_value=0.0, value=0.0)
        mitigation = st.text_area("Mitigation Measures")
        notes = st.text_area("Notes/Observations")
        submitted = st.form_submit_button("Add Biodiversity Record")
        if submitted:
            row = {"Site":site,"Impact_Type":impact,"Area_ha":area,"Mitigation":mitigation,"Notes":notes}
            st.session_state.biodiversity_data = pd.concat([st.session_state.biodiversity_data, pd.DataFrame([row])], ignore_index=True)
            st.success("Biodiversity record added.")

# Employee page
def render_employee_page():
    st.subheader("Employee - Input")
    with st.form("emp_form", clear_on_submit=False):
        year = st.number_input("Year", min_value=2000, max_value=2100, value=2024)
        total = st.number_input("Total Employees", min_value=0, value=0)
        hires = st.number_input("New Hires", min_value=0, value=0)
        attr = st.slider("Attrition Rate (%)", 0, 100, 0)
        training = st.number_input("Avg Training Hours per Employee", min_value=0.0, value=0.0)
        sub = st.form_submit_button("Add Employee Record")
        if sub:
            row = {"Year":year,"Total_Employees":total,"New_Hires":hires,"Attrition_rate":attr,"Training_Hours":training}
            st.session_state.employee_data = pd.concat([st.session_state.employee_data, pd.DataFrame([row])], ignore_index=True)
            st.success("Employee record added.")

# Health & Safety page
def render_health_safety_page():
    st.subheader("Health & Safety - Input")
    with st.form("hs_form", clear_on_submit=False):
        site = st.text_input("Site")
        incidents = st.number_input("Workplace Incidents (count)", min_value=0, value=0)
        lti = st.number_input("Lost Time Injury Days", min_value=0, value=0)
        near = st.number_input("Near Misses", min_value=0, value=0)
        safe_training = st.number_input("Safety Training Hours", min_value=0.0, value=0.0)
        submit = st.form_submit_button("Add H&S Record")
        if submit:
            row = {"Site":site,"Incidents":incidents,"Lost_Time_Days":lti,"Near_Misses":near,"Safety_Training_Hours":safe_training}
            st.session_state.hs_data = pd.concat([st.session_state.hs_data, pd.DataFrame([row])], ignore_index=True)
            st.success("H&S record added.")

# CSR page
def render_csr_page():
    st.subheader("CSR - Input")
    with st.form("csr_form", clear_on_submit=False):
        project = st.text_input("Project Name")
        spend = st.number_input("Spend (INR)", min_value=0.0, value=0.0)
        beneficiaries = st.number_input("Beneficiaries (count)", min_value=0, value=0)
        year = st.number_input("Year", min_value=2000, max_value=2100, value=2024)
        submit = st.form_submit_button("Add CSR Record")
        if submit:
            row = {"Project":project,"Spend_INR":spend,"Beneficiaries":beneficiaries,"Year":year}
            st.session_state.csr_data = pd.concat([st.session_state.csr_data, pd.DataFrame([row])], ignore_index=True)
            st.success("CSR record added.")

# Board page
def render_board_page():
    st.subheader("Board - Input")
    with st.form("board_form", clear_on_submit=False):
        board_size = st.number_input("Board Size", min_value=0, value=0)
        ind_dirs = st.number_input("Independent Directors", min_value=0, value=0)
        gender_div = st.slider("% Women on Board", 0, 100, 0)
        meetings = st.number_input("Meetings per year", min_value=0, value=0)
        submit = st.form_submit_button("Add Board Record")
        if submit:
            row = {"Board_Size":board_size,"Independent_Directors":ind_dirs,"Gender_Diversity":gender_div,"Meetings_per_year":meetings}
            st.session_state.board_data = pd.concat([st.session_state.board_data, pd.DataFrame([row])], ignore_index=True)
            st.success("Board record added.")

# Policies page
def render_policies_page():
    st.subheader("Policies - Input")
    with st.form("policy_form", clear_on_submit=False):
        pname = st.text_input("Policy Name")
        impl = st.checkbox("Implemented")
        review = st.date_input("Last Review Date")
        notes = st.text_area("Notes")
        submit = st.form_submit_button("Add Policy")
        if submit:
            row = {"Policy_Name":pname,"Implemented":impl,"Last_Review_Date":str(review),"Notes":notes}
            st.session_state.policy_data = pd.concat([st.session_state.policy_data, pd.DataFrame([row])], ignore_index=True)
            st.success("Policy added.")

# Compliance page
def render_compliance_page():
    st.subheader("Compliance - Input")
    with st.form("compliance_form", clear_on_submit=False):
        regulation = st.text_input("Regulation / Standard")
        status = st.selectbox("Status", ["Compliant","Non-compliant","Partial"])
        notes = st.text_area("Notes")
        last = st.date_input("Last Reviewed")
        submit = st.form_submit_button("Add Compliance Record")
        if submit:
            row = {"Regulation":regulation,"Status":status,"Notes":notes,"Last_Reviewed":str(last)}
            st.session_state.compliance_data = pd.concat([st.session_state.compliance_data, pd.DataFrame([row])], ignore_index=True)
            st.success("Compliance record added.")

# Risk Management page
def render_risk_management_page():
    st.subheader("Risk Management - Input")
    with st.form("risk_form", clear_on_submit=False):
        risk = st.text_input("Risk")
        category = st.selectbox("Category", ["Climate","Operational","Financial","Regulatory","Reputational","Other"])
        likelihood = st.selectbox("Likelihood", ["Low","Medium","High"])
        impact = st.selectbox("Impact", ["Low","Medium","High"])
        mitigation = st.text_area("Mitigation Measures")
        owner = st.text_input("Owner / Responsible")
        submit = st.form_submit_button("Add Risk")
        if submit:
            row = {"Risk":risk,"Category":category,"Likelihood":likelihood,"Impact":impact,"Mitigation":mitigation,"Owner":owner}
            st.session_state.risk_data = pd.concat([st.session_state.risk_data, pd.DataFrame([row])], ignore_index=True)
            st.success("Risk added.")

# ---------------------------
# Reports - Mapping rules and renderers
# ---------------------------

def compute_ghg_summaries():
    """Compute scope totals from st.session_state.entries DataFrame and return dict in tonnes (tCO2e)."""
    df = st.session_state.entries
    # entries Emissions_kgCO2e column is kg, convert to tonnes
    totals = {"scope1_t":0.0,"scope2_t":0.0,"scope3_t":0.0,"total_t":0.0}
    if not df.empty:
        # ensure numeric
        df2 = df.copy()
        df2["Emissions_kgCO2e"] = pd.to_numeric(df2["Emissions_kgCO2e"], errors="coerce").fillna(0.0)
        s1 = df2[df2["Scope"]=="Scope 1"]["Emissions_kgCO2e"].sum()
        s2 = df2[df2["Scope"]=="Scope 2"]["Emissions_kgCO2e"].sum()
        s3 = df2[df2["Scope"]=="Scope 3"]["Emissions_kgCO2e"].sum()
        totals["scope1_t"] = round(s1 / 1000.0, 3)
        totals["scope2_t"] = round(s2 / 1000.0, 3)
        totals["scope3_t"] = round(s3 / 1000.0, 3)
        totals["total_t"] = round((s1 + s2 + s3) / 1000.0, 3)
    return totals

# Mapping dictionaries - map report KPI labels to functions that pull data from session_state
def _safe_get(key, default=0):
    return st.session_state.get(key, default)

BRSR_MAP = {
    # Environment - Principle 6 examples
    "P6 - Scope1 Emissions (tCO2e)": lambda: compute_ghg_summaries()["scope1_t"],
    "P6 - Scope2 Emissions (tCO2e)": lambda: compute_ghg_summaries()["scope2_t"],
    "P6 - Scope3 Emissions (tCO2e)": lambda: compute_ghg_summaries()["scope3_t"],
    "P6 - Total Emissions (tCO2e)": lambda: compute_ghg_summaries()["total_t"],
    "P6 - Energy (kWh)": lambda: int(_safe_get("renewable_entries", pd.DataFrame()).get("Energy_kWh", pd.Series([])).sum() if isinstance(_safe_get("renewable_entries", pd.DataFrame()), pd.DataFrame) else 0),
    "P6 - Water Usage (m3)": lambda: float(st.session_state.water_data["Quantity_m3"].sum() if not st.session_state.water_data.empty else 0),
    "P6 - Waste (kg)": lambda: float(st.session_state.waste_data["Quantity_kg"].sum() if not st.session_state.waste_data.empty else 0),
    # Social - Principle 3 examples
    "P3 - Total Employees": lambda: int(st.session_state.employee_data["Total_Employees"].astype(float).max() if not st.session_state.employee_data.empty else _safe_get("employee_count",0)),
    "P3 - Training Hours per Employee (avg)": lambda: float(st.session_state.employee_data["Training_Hours"].mean() if not st.session_state.employee_data.empty else _safe_get("training_hours",0.0)),
    "P3 - Attrition Rate (%)": lambda: float(st.session_state.employee_data["Attrition_rate"].mean() if not st.session_state.employee_data.empty else _safe_get("attrition_rate",0.0)),
    # Governance - Principle 1 examples
    "P1 - Board Independence (%)": lambda: (int(st.session_state.board_data["Independent_Directors"].max())/int(st.session_state.board_data["Board_Size"].max())*100) if (not st.session_state.board_data.empty and st.session_state.board_data["Board_Size"].max()>0) else ( (_safe_get("independent_directors",0)/_safe_get("board_size",1))*100 ),
}

CDP_MAP = {
    "Scope 1 (tCO2e)": lambda: compute_ghg_summaries()["scope1_t"],
    "Scope 2 (tCO2e)": lambda: compute_ghg_summaries()["scope2_t"],
    "Scope 3 (tCO2e)": lambda: compute_ghg_summaries()["scope3_t"],
    "Total Energy (kWh)": lambda: int((st.session_state.renewable_entries["Energy_kWh"].sum() if not st.session_state.renewable_entries.empty else 0) + 0), # energy from renewables + scope1_2 energy mapping if available
    "Climate Risks": lambda: (_safe_get("risk_data", pd.DataFrame()).shape[0] if isinstance(_safe_get("risk_data", pd.DataFrame()), pd.DataFrame) else 0)
}

GRI_MAP = {
    "GRI 305 - Total GHG Emissions (tCO2e)": lambda: compute_ghg_summaries()["total_t"],
    "GRI 302 - Energy Consumption (kWh)": lambda: int(st.session_state.renewable_entries["Energy_kWh"].sum() if not st.session_state.renewable_entries.empty else 0),
    "GRI 303 - Water Withdrawal (m3)": lambda: float(st.session_state.water_data["Quantity_m3"].sum() if not st.session_state.water_data.empty else 0),
    "GRI 306 - Waste Generated (kg)": lambda: float(st.session_state.waste_data["Quantity_kg"].sum() if not st.session_state.waste_data.empty else 0),
    "GRI 401 - Number of Employees": lambda: int(st.session_state.employee_data["Total_Employees"].max() if not st.session_state.employee_data.empty else _safe_get("employee_count",0)),
    "GRI 405 - % of female employees": lambda: float((_safe_get("women_percentage",0.0)))
}

TCFD_MAP = {
    "Governance - Board Oversight of Climate": lambda: "Yes" if ( (not st.session_state.board_data.empty and st.session_state.board_data["Meetings_per_year"].max()>0) or _safe_get("board_oversight", False) ) else "No",
    "Strategy - Climate Risks count": lambda: int(st.session_state.risk_data.shape[0]) if not st.session_state.risk_data.empty else 0,
    "Risk Management - Process exists": lambda: "Yes" if (not st.session_state.risk_data.empty or _safe_get("risk_process", False)) else "No",
    "Metrics - Scope1+2 (tCO2e)": lambda: round(compute_ghg_summaries()["scope1_t"] + compute_ghg_summaries()["scope2_t"], 3),
    "Metrics - Energy Consumption (kWh)": lambda: int(st.session_state.renewable_entries["Energy_kWh"].sum() if not st.session_state.renewable_entries.empty else 0)
}

def render_report_page(mapping, title):
    st.subheader(title)
    # compute some derived fields first (so GHG entries reflect)
    ghg_totals = compute_ghg_summaries()
    # show KPIs using mapping
    for kpi, func in mapping.items():
        try:
            value = func()
        except Exception as e:
            value = f"Error: {e}"
        st.metric(kpi, value)

# ---------------------------
# Render Pages (router)
# Keep Home, GHG, Energy as-is (unchanged)
# ---------------------------
if st.session_state.page == "Home":
    st.title("EinTrust Sustainability Dashboard")
    # Render GHG (but don't include data input on Home per your earlier code)
    render_ghg_dashboard(include_data=False, show_chart=False)
    render_energy_dashboard(include_input=False, show_chart=False)

elif st.session_state.page == "GHG":
    # EXACT original GHG page (unchanged logic)
    render_ghg_dashboard(include_data=True, show_chart=True)

elif st.session_state.page == "Energy":
    # EXACT original Energy page (unchanged logic)
    render_energy_dashboard(include_input=True, show_chart=True)

# New Environment pages (inputs) - these do not change GHG/Energy code
elif st.session_state.page == "Water":
    # keep the water page simple - reuse previously discussed advanced water structure
    st.subheader("Water")
    # show basic water KPI and data entry using session_state.water_data and advanced_water_data
    water_df = st.session_state.water_data.copy()
    adv_df = st.session_state.advanced_water_data.copy()
    total_water = water_df["Quantity_m3"].sum() if not water_df.empty else 0
    total_cost = water_df["Cost_INR"].sum() if not water_df.empty else 0
    recycled = adv_df["Water_Recycled_m3"].sum() if not adv_df.empty else 0
    rain = adv_df["Rainwater_Harvested_m3"].sum() if not adv_df.empty else 0
    st.metric("Total Water Used (m³)", f"{total_water:,.0f}")
    st.metric("Estimated Cost (INR)", f"₹ {total_cost:,.0f}")
    st.metric("Recycled Water (m³)", f"{recycled:,.0f}")
    st.metric("Rainwater Harvested (m³)", f"{rain:,.0f}")
    st.info("Open Water page in previous conversation steps for detailed entry UI (kept simple here).")
    st.markdown("---")
    render_water_input_page()

elif st.session_state.page == "Waste":
    st.subheader("Waste")
    render_waste_page()

elif st.session_state.page == "Biodiversity":
    st.subheader("Biodiversity")
    render_biodiversity_page()

# Social pages
elif st.session_state.page == "Employee":
    st.subheader("Employee")
    render_employee_page()
    if not st.session_state.employee_data.empty:
        st.markdown("Employee historical records:")
        st.dataframe(st.session_state.employee_data.tail(10))

elif st.session_state.page == "Health & Safety":
    st.subheader("Health & Safety")
    render_health_safety_page()
    if not st.session_state.hs_data.empty:
        st.markdown("H&S records:")
        st.dataframe(st.session_state.hs_data.tail(10))

elif st.session_state.page == "CSR":
    st.subheader("CSR")
    render_csr_page()
    if not st.session_state.csr_data.empty:
        st.markdown("CSR records:")
        st.dataframe(st.session_state.csr_data.tail(10))

# Governance pages
elif st.session_state.page == "Board":
    st.subheader("Board")
    render_board_page()
    if not st.session_state.board_data.empty:
        st.dataframe(st.session_state.board_data.tail(5))

elif st.session_state.page == "Policies":
    st.subheader("Policies")
    render_policies_page()
    if not st.session_state.policy_data.empty:
        st.dataframe(st.session_state.policy_data.tail(10))

elif st.session_state.page == "Compliance":
    st.subheader("Compliance")
    render_compliance_page()
    if not st.session_state.compliance_data.empty:
        st.dataframe(st.session_state.compliance_data.tail(10))

elif st.session_state.page == "Risk Management":
    st.subheader("Risk Management")
    render_risk_management_page()
    if not st.session_state.risk_data.empty:
        st.dataframe(st.session_state.risk_data.tail(10))

elif st.session_state.page == "SDG":
    render_sdg_dashboard()

# Reports pages - map to BRSR, GRI, CDP, TCFD
elif st.session_state.page in ["BRSR","GRI","CDP","TCFD"]:
    # Show report appropriate to the sidebar selection
    if st.session_state.page == "BRSR":
        render_report_page(BRSR_MAP, "BRSR - Auto-mapped KPIs")
    elif st.session_state.page == "GRI":
        render_report_page(GRI_MAP, "GRI - Auto-mapped KPIs")
    elif st.session_state.page == "CDP":
        render_report_page(CDP_MAP, "CDP - Auto-mapped KPIs")
    elif st.session_state.page == "TCFD":
        render_report_page(TCFD_MAP, "TCFD - Auto-mapped KPIs")

else:
    st.subheader(f"{st.session_state.page} section")
    st.info("This section is under development. Please select other pages from sidebar.")
