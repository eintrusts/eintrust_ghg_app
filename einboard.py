# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ---------------------------
# Page Config & Colors
# ---------------------------
st.set_page_config(page_title="EinTrust Sustainability Dashboard", page_icon="🌍", layout="wide")

PRIMARY_BG = "#0d1117"
CARD_BG = "#12131a"
ACCENT = "#2ecc71"      # green for positive / renewable
ACCENT2 = "#f39c12"     # orange for fossil
TEXT = "#e6edf3"
MUTED = "#cfd8dc"
ENERGY_COLORS = {"Fossil": ACCENT2, "Renewable": ACCENT}

# ---------------------------
# CSS
# ---------------------------
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
html, body, [class*="css"] {{ font-family: 'Roboto', sans-serif; }}
.stApp {{ background-color: {PRIMARY_BG}; color: {TEXT}; }}
.kpi {{ background: linear-gradient(145deg, {CARD_BG}, #1a1b22); padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.5); margin-bottom: 10px; min-height: 110px; display:flex; flex-direction:column; justify-content:center; align-items:center; transition: transform .12s; }}
.kpi-value {{ font-size: 28px; font-weight: 700; color: {TEXT}; margin-bottom: 5px; }}
.kpi-unit {{ font-size: 14px; font-weight: 600; color: {MUTED}; margin-bottom: 5px; }}
.kpi-label {{ font-size: 12px; color: {MUTED}; letter-spacing: 0.4px; }}
.sdg-card {{ border-radius: 10px; padding: 12px; margin: 6px; display:inline-block; width: 100%; min-height: 90px; text-align:left; color: white; }}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Session State Initialization
# ---------------------------
if "page" not in st.session_state:
    st.session_state.page = "Home"

# entries: manual GHG entries (master)
if "entries" not in st.session_state:
    st.session_state.entries = pd.DataFrame(columns=[
        "Scope","Activity","Sub-Activity","Specific Item","Quantity","Unit","Emissions_kgCO2e"
    ])

# renewable entries (monthly breakdown)
if "renewable_entries" not in st.session_state:
    st.session_state.renewable_entries = pd.DataFrame(columns=["Source","Location","Month","Energy_kWh","CO2e_kg","Type"])

# water / sdg placeholders
if "sdg_engagement" not in st.session_state:
    st.session_state.sdg_engagement = {i:0 for i in range(1,18)}
if "water_data" not in st.session_state:
    st.session_state.water_data = pd.DataFrame(columns=["Location","Source","Month","Quantity_m3","Cost_INR"])
if "advanced_water_data" not in st.session_state:
    st.session_state.advanced_water_data = pd.DataFrame(columns=[
        "Location","Month","Rainwater_Harvested_m3","Water_Recycled_m3","Treatment_Before_Discharge","STP_ETP_Capacity_kL_day"
    ])

# ---------------------------
# Lookups & Factors
# ---------------------------
months = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]

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
            "Brick Kiln": "CO₂ from brick firing"
        },
        "Fugitive Emissions": {
            "Refrigerant (HFC/HCFC)": "Gas leak from AC/refrigerator",
            "Methane (CH₄)": "Methane leaks from storage/pipelines"
        }
    },
    "Scope 2": {
        "Electricity Consumption": {
            "Grid Electricity": "Electricity bought from grid",
            "Diesel Generator Electricity": "Electricity generated on-site with diesel"
        }
    },
    "Scope 3": {
        "1 Purchased goods & services": {
            "Raw Materials": ["Cement","Steel","Chemicals","Textile","Paper"],
            "Packaging": ["Cardboard","Plastics","Glass"],
            "Office Supplies": ["Stationery"]
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
    "Diesel Generator": "Liters","Petrol Generator":"Liters","LPG Boiler":"Liters","Coal Boiler":"kg","Biomass Furnace":"kg",
    "Diesel Vehicle":"Liters","Petrol Car":"Liters","CNG Vehicle":"m³","Diesel Forklift":"Liters","Petrol Two-Wheeler":"Liters",
    "Cement":"Tonnes","Steel":"Tonnes","Chemicals":"Tonnes","Textile":"Tonnes","Cardboard":"kg","Plastics":"kg","Glass":"kg","Paper":"kg",
    "Grid Electricity":"kWh","Diesel Generator Electricity":"kWh"
}

# emission factors (starter). Units chosen to match units_dict where possible
emission_factors = {
    "Diesel": 2.68,   # kg CO2e per liter
    "Petrol": 2.31,
    "LPG": 1.51,
    "CNG": 2.02,      # per m3 approx
    "Coal": 2.42,     # per kg approx
    "Electricity": 0.82,  # kg CO2e per kWh (India avg)
    "Cement": 900.0, "Steel": 1850.0, "Textile": 300.0, "Chemicals": 1200.0,
    "Cardboard": 0.9, "Plastics": 1.7, "Glass": 0.95, "Paper": 1.2,
    "Air Travel (domestic average)": 250.0,
    "Train per km": 0.05, "Taxi per km": 0.12, "TwoWheeler per km": 0.05, "Car per km": 0.12,
    "Landfill per kg": 1.0, "Recycling per kg": 0.3, "Composting per kg": 0.2,
    "Product use kWh": 0.82
}

# calorific values for rough energy conversion (MJ per kg or L depending)
calorific_values = {"Diesel":35.8,"Petrol":34.2,"LPG":46.1,"CNG":48,"Coal":24,"Biomass":15}

# ---------------------------
# Helper Functions
# ---------------------------
def calculate_emissions(scope, activity, sub_activity, specific_item, quantity, unit):
    """Return emissions in kg CO2e and a flag if factor missing."""
    missing_factor = False
    emissions = 0.0

    key_specific = (specific_item or "").strip()
    key_sub = (sub_activity or "").strip()
    key_act = (activity or "").strip()

    try:
        qty = float(quantity)
    except Exception:
        qty = 0.0

    # Scope 1 & 2 logic
    if scope in ["Scope 1","Scope 2"]:
        fuel_key = None
        if "Electricity" in key_sub or unit.lower() == "kwh":
            fuel_key = "Electricity"
        elif "Diesel" in key_sub:
            fuel_key = "Diesel"
        elif "Petrol" in key_sub:
            fuel_key = "Petrol"
        elif "LPG" in key_sub:
            fuel_key = "LPG"
        elif "CNG" in key_sub:
            fuel_key = "CNG"
        elif "Coal" in key_sub:
            fuel_key = "Coal"
        elif "Biomass" in key_sub:
            fuel_key = "Biomass"

        if fuel_key:
            factor = emission_factors.get(fuel_key)
            if factor is not None:
                emissions = qty * factor
            else:
                missing_factor = True
        else:
            # fallback: if emission provided already (user may enter emissions in quantity field)
            missing_factor = True

    else:
        # Scope 3 heuristics
        if key_specific and key_specific in emission_factors:
            emissions = qty * emission_factors[key_specific]
        elif key_sub in ["Air Travel"]:
            factor = emission_factors.get("Air Travel (domestic average)")
            if factor:
                emissions = qty * factor
            else:
                missing_factor = True
        elif key_sub in ["Train Travel"]:
            factor = emission_factors.get("Train per km")
            if factor:
                emissions = qty * factor
            else:
                missing_factor = True
        elif key_sub in ["Taxi/Car Rental","Cars/Vans"]:
            factor = emission_factors.get("Car per km")
            if factor:
                emissions = qty * factor
            else:
                missing_factor = True
        elif key_sub in ["Two-Wheelers"]:
            factor = emission_factors.get("TwoWheeler per km") or emission_factors.get("TwoWheeler per km") or emission_factors.get("TwoWheeler per km")
            if factor:
                emissions = qty * factor
            else:
                missing_factor = True
        elif key_sub in ["Landfill","Recycling","Composting"]:
            mapping = {"Landfill":"Landfill per kg","Recycling":"Recycling per kg","Composting":"Composting per kg"}
            factor = emission_factors.get(mapping.get(key_sub))
            if factor:
                emissions = qty * factor
            else:
                missing_factor = True
        elif unit and unit.lower() in ["kwh"]:
            factor = emission_factors.get("Product use kWh")
            if factor:
                emissions = qty * factor
            else:
                missing_factor = True
        elif key_specific in emission_factors:
            emissions = qty * emission_factors.get(key_specific)
        else:
            missing_factor = True

    return float(round(emissions, 3)), missing_factor

def ghg_kpis(df_entries: pd.DataFrame):
    """Return dict with totals for total, scope1, scope2, scope3 (kgCO2e)"""
    if df_entries is None or df_entries.empty:
        return {"total":0.0,"scope1":0.0,"scope2":0.0,"scope3":0.0}
    total = df_entries["Emissions_kgCO2e"].astype(float).sum()
    scope1 = df_entries[df_entries["Scope"]=="Scope 1"]["Emissions_kgCO2e"].astype(float).sum()
    scope2 = df_entries[df_entries["Scope"]=="Scope 2"]["Emissions_kgCO2e"].astype(float).sum()
    scope3 = df_entries[df_entries["Scope"]=="Scope 3"]["Emissions_kgCO2e"].astype(float).sum()
    return {"total":round(total,3),"scope1":round(scope1,3),"scope2":round(scope2,3),"scope3":round(scope3,3)}

def build_energy_rows_from_entries(df_entries: pd.DataFrame):
    """
    Convert Scope1/Scope2 GHG manual entries to an energy-like dataframe with:
    Location, Fuel, Quantity, Energy_kWh, CO2e_kg, Type, Month
    """
    rows = []
    if df_entries is None or df_entries.empty:
        return pd.DataFrame(columns=["Location","Fuel","Quantity","Energy_kWh","CO2e_kg","Type","Month"])
    for _, r in df_entries[df_entries["Scope"].isin(["Scope 1","Scope 2"])].iterrows():
        sub = r.get("Sub-Activity","")
        qty = float(r.get("Quantity",0) or 0)
        unit = r.get("Unit","")
        co2e = float(r.get("Emissions_kgCO2e",0) or 0)
        energy_kwh = 0.0
        # electricity
        if "Electricity" in sub or unit.lower() == "kwh":
            energy_kwh = qty
        else:
            # map fuel to calorific value -> convert to kWh (MJ -> kWh: divide by 3.6)
            if "Diesel" in sub and "Diesel" in calorific_values:
                energy_kwh = (qty * calorific_values["Diesel"]) / 3.6
            elif "Petrol" in sub and "Petrol" in calorific_values:
                energy_kwh = (qty * calorific_values["Petrol"]) / 3.6
            elif "LPG" in sub and "LPG" in calorific_values:
                energy_kwh = (qty * calorific_values["LPG"]) / 3.6
            elif "Coal" in sub and "Coal" in calorific_values:
                energy_kwh = (qty * calorific_values["Coal"]) / 3.6
            else:
                # unknown fuel: leave energy_kwh = 0 but keep CO2e for KPIs
                energy_kwh = 0.0
        typ = "Fossil" if co2e > 0 and not ("Renewable" in sub or "Biogas" in sub) else "Renewable"
        rows.append({
            "Location": r.get("Specific Item","").strip() or "Unknown",
            "Fuel": sub or r.get("Activity",""),
            "Quantity": qty,
            "Energy_kWh": energy_kwh,
            "CO2e_kg": co2e,
            "Type": typ,
            "Month": np.random.choice(months)
        })
    return pd.DataFrame(rows)

# ---------------------------
# Render: Sidebar & Navigation
# ---------------------------
def sidebar_button(label):
    active = st.session_state.page == label
    if st.button(label, key=f"btn_{label}"):
        st.session_state.page = label
    st.markdown(f"""
    <style>
    div.stButton > button[key="btn_{label}"] {{
        all: unset; cursor: pointer; padding: 0.45rem; text-align:left; border-radius:0.3rem; margin-bottom:0.2rem;
        background-color: {'#154f24' if active else CARD_BG}; color: {'white' if active else TEXT}; font-size:15px;
    }}
    div.stButton > button[key="btn_{label}"]:hover {{ background-color: {'#1a6b34' if active else '#1a1b22'}; }}
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
# GHG Dashboard
# ---------------------------
def render_ghg_dashboard():
    st.title("GHG Emissions")

    # top KPIs from manual entries
    kpis = ghg_kpis(st.session_state.entries)
    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{TEXT}'>{kpis['total']:,}</div><div class='kpi-unit'>kg CO₂e</div><div class='kpi-label'>Total Emissions (All Scopes)</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{ACCENT2}'>{kpis['scope1']:,}</div><div class='kpi-unit'>kg CO₂e</div><div class='kpi-label'>Scope 1 Emissions</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{ACCENT2}'>{kpis['scope2']:,}</div><div class='kpi-unit'>kg CO₂e</div><div class='kpi-label'>Scope 2 Emissions</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{ACCENT}'>{kpis['scope3']:,}</div><div class='kpi-unit'>kg CO₂e</div><div class='kpi-label'>Scope 3 Emissions</div></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Add / Record GHG Entry (manual)")

    scope = st.selectbox("Select Scope", ["Scope 1","Scope 2","Scope 3"], index=0, key="ghg_scope")

    if scope != "Scope 3":
        activity = st.selectbox("Select Activity", list(scope_activities[scope].keys()), key="ghg_activity")
        sub_options = scope_activities[scope][activity]
        sub_activity = st.selectbox("Select Sub-Activity", list(sub_options.keys()), key="ghg_sub")
        st.info(sub_options[sub_activity])
        specific_item = st.text_input("Specific Item / Location (optional)", value="", key="ghg_specific")
    else:
        activity = st.selectbox("Select Scope 3 Category", list(scope_activities["Scope 3"].keys()), key="ghg_activity3")
        sub_dict = scope_activities["Scope 3"][activity]
        sub_activity = st.selectbox("Select Sub-Category", list(sub_dict.keys()), key="ghg_sub3")
        specific_item = ""
        if isinstance(sub_dict[sub_activity], list):
            specific_item = st.selectbox("Select Specific Item", sub_dict[sub_activity], key="ghg_specific3")
        else:
            specific_item = st.text_input("Specific Item (optional)", value="", key="ghg_specific3_txt")

    # Unit autofill heuristics
    if scope != "Scope 3":
        unit_default = units_dict.get(sub_activity, "")
    else:
        if sub_activity in ["Air Travel"]:
            unit_default = "Number of flights"
        elif sub_activity in ["Train Travel","Taxi/Car Rental","Cars/Vans","Two-Wheelers","Public Transport","Incoming Transport","Third-party Logistics","Distribution to Customers","Retail/Distributor Transport"]:
            unit_default = "km traveled"
        elif sub_activity in ["Landfill","Recycling","Composting"]:
            unit_default = "kg"
        else:
            unit_default = "kg / Tonnes / kWh"

    unit = st.text_input("Unit", value=unit_default, key="ghg_unit")
    quantity = st.number_input(f"Quantity ({unit})", min_value=0.0, format="%.3f", key="ghg_qty")

    if st.button("Add Entry", key="add_entry_button"):
        emissions, missing = calculate_emissions(scope, activity, sub_activity, specific_item, quantity, unit)
        if missing:
            st.warning("Emission factor not found in library — emissions recorded as 0. You can later edit or provide a custom factor.")
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
        st.success("GHG manual entry saved and emissions calculated (if factor available).")
        # no rerun; energy KPIs will reflect the new entry on next render

    st.markdown("---")
    st.subheader("All GHG Entries (manual)")
    if st.session_state.entries.empty:
        st.info("No GHG entries recorded yet.")
    else:
        df_display = st.session_state.entries.copy()
        df_display["Quantity"] = df_display["Quantity"].apply(lambda x: f"{float(x):,.3f}")
        df_display["Emissions_kgCO2e"] = df_display["Emissions_kgCO2e"].apply(lambda x: f"{float(x):,.3f}")
        st.dataframe(df_display, use_container_width=True)
        csv = st.session_state.entries.to_csv(index=False).encode('utf-8')
        st.download_button("Download GHG Entries as CSV", csv, "ghg_entries_with_emissions.csv", "text/csv")

# ---------------------------
# Energy Dashboard
# ---------------------------
def render_energy_dashboard():
st.title("⚡ Energy Dashboard")


# Load stored entries
if "energy_entries" not in st.session_state:
st.session_state.energy_entries = pd.DataFrame(columns=[
"Location", "Fuel", "Quantity", "Energy_kWh", "CO2e_kg", "Type", "Month"
])


energy_from_entries = st.session_state.energy_entries


# Handle renew DataFrame safely
if "renew" in st.session_state:
renew = st.session_state.renew.copy()
expected_cols = ["Location", "Fuel", "Quantity", "Energy_kWh", "CO2e_kg", "Type", "Month"]
renew = renew.reindex(columns=expected_cols)
else:
renew = pd.DataFrame(columns=["Location", "Fuel", "Quantity", "Energy_kWh", "CO2e_kg", "Type", "Month"])


# Combine datasets
all_energy = pd.concat([energy_from_entries, renew], ignore_index=True, sort=False)


# KPI Summary
total_energy = all_energy["Energy_kWh"].sum() if not all_energy.empty else 0
fossil_energy = all_energy.loc[all_energy["Type"] == "Fossil", "Energy_kWh"].sum()
renewable_energy = all_energy.loc[all_energy["Type"] == "Renewable", "Energy_kWh"].sum()


st.markdown("### 🔑 Energy KPIs")
col1, col2, col3 = st.columns(3)
col1.metric("Total Energy (kWh)", f"{total_energy:,.0f}")
col2.metric("Fossil Fuels (kWh)", f"{fossil_energy:,.0f}")
col3.metric("Renewables (kWh)", f"{renewable_energy:,.0f}")


# Monthly trend chart
if not all_energy.empty:
monthly_trend = all_energy.groupby(["Month", "Type"], as_index=False)["Energy_kWh"].sum()
fig = px.bar(monthly_trend, x="Month", y="Energy_kWh", color="Type",
barmode="group", title="Monthly Energy Consumption by Type")
st.plotly_chart(fig, use_container_width=True)


# Data input form
st.markdown("### ➕ Add Energy Entry")
with st.form("energy_form", clear_on_submit=True):
location = st.text_input("Location")
fuel = st.text_input("Fuel Type")
quantity = st.number_input("Quantity (liters/kg/m3)", min_value=0.0, step=0.1)
energy_kwh = st.number_input("Energy (kWh)", min_value=0.0, step=0.1)
co2e = st.number_input("CO2e (kg)", min_value=0.0, step=0.1)
energy_type = st.selectbox("Type", ["Fossil", "Renewable"])
month = st.selectbox("Month", [
"January", "February", "March", "April", "May", "June",
"July", "August", "September", "October", "November", "December"
])
submitted = st.form_submit_button("Add Entry")


if submitted:
new_entry = pd.DataFrame([{
"Location": location,
"Fuel": fuel,
"Quantity": quantity,
"Energy_kWh": energy_kwh,
"CO2e_kg": co2e,
"Type": energy_type,
"Month": month
}])
st.session_state.energy_entries = pd.concat(
[st.session_state.energy_entries, new_entry], ignore_index=True
)
st.success("Energy entry added successfully!")


# Show all entries
st.markdown("### 📋 All Energy Entries")
if not all_energy.empty:
st.dataframe(all_energy)
else:
st.info("No energy data available yet.")

    # KPIs
    total_energy_kwh = all_energy["Energy_kWh"].astype(float).sum() if not all_energy.empty else 0.0
    total_co2e = all_energy["CO2e_kg"].astype(float).sum() if not all_energy.empty else 0.0
    fossil_energy = all_energy[all_energy["Type"]=="Fossil"]["Energy_kWh"].astype(float).sum() if not all_energy.empty else 0.0
    renewable_energy = all_energy[all_energy["Type"]=="Renewable"]["Energy_kWh"].astype(float).sum() if not all_energy.empty else 0.0

    c1,c2,c3 = st.columns(3)
    c1.markdown(f"<div class='kpi'><div class='kpi-value'>{int(total_energy_kwh):,}</div><div class='kpi-unit'>kWh</div><div class='kpi-label'>Total Energy (estimated)</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{ACCENT2}'>{int(fossil_energy):,}</div><div class='kpi-unit'>kWh</div><div class='kpi-label'>Fossil Energy</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{ACCENT}'>{int(renewable_energy):,}</div><div class='kpi-unit'>kWh</div><div class='kpi-label'>Renewable Energy</div></div>", unsafe_allow_html=True)

    st.markdown(f"**Estimated CO₂e from energy rows:** {total_co2e:,.2f} kg CO₂e (this is derived from manual GHG entries and renewables' CO2e).")

    # Monthly trend chart
    if not all_energy.empty:
        monthly_trend = all_energy.groupby(["Month","Type"])["Energy_kWh"].sum().reset_index()
        st.subheader("Monthly Energy Consumption (kWh)")
        fig = px.bar(monthly_trend, x="Month", y="Energy_kWh", color="Type", barmode="stack", color_discrete_map=ENERGY_COLORS)
        st.plotly_chart(fig, use_container_width=True)

    # Add renewable entries
    st.markdown("---")
    st.subheader("Add Renewable Energy (annual -> monthly breakdown)")
    with st.form("renewable_form", clear_on_submit=True):
        source = st.selectbox("Source", ["Solar","Wind","Biogas","Purchased Green Energy"])
        location = st.text_input("Location")
        annual_energy = st.number_input("Annual Energy (kWh)", min_value=0.0, format="%.2f")
        submitted = st.form_submit_button("Add Renewable")
        if submitted:
            monthly_energy = annual_energy/12.0 if annual_energy else 0.0
            rows = []
            for m in months:
                rows.append({
                    "Source": source,
                    "Location": location,
                    "Month": m,
                    "Energy_kWh": monthly_energy,
                    "CO2e_kg": round(monthly_energy * emission_factors.get("Electricity",0) * 0.0,3),  # assume zero grid CO2e for "green" (user can edit)
                    "Type": "Renewable"
                })
            st.session_state.renewable_entries = pd.concat([st.session_state.renewable_entries, pd.DataFrame(rows)], ignore_index=True)
            st.success(f"Added renewable energy (monthly breakdown). {len(rows)} rows appended.")

    st.markdown("---")
    st.subheader("Energy Data (combined)")
    if all_energy.empty:
        st.info("No energy data available. Add GHG entries (Scope 1/2) or renewable entries.")
    else:
        ego = all_energy.copy()
        ego["Energy_kWh"] = ego["Energy_kWh"].apply(lambda x: float(x or 0.0))
        ego["CO2e_kg"] = ego["CO2e_kg"].apply(lambda x: float(x or 0.0))
        ego_display = ego[["Location","Fuel","Quantity","Energy_kWh","CO2e_kg","Type","Month"]].fillna("")
        ego_display["Energy_kWh"] = ego_display["Energy_kWh"].apply(lambda x: f"{float(x):,.2f}")
        ego_display["CO2e_kg"] = ego_display["CO2e_kg"].apply(lambda x: f"{float(x):,.2f}")
        st.dataframe(ego_display, use_container_width=True)

# ---------------------------
# SDG Dashboard (simple)
# ---------------------------
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

def render_sdg_dashboard():
    st.title("Sustainable Development Goals (SDGs)")
    num_cols = 4
    idx = 0
    for _ in range((len(SDG_LIST)+num_cols-1)//num_cols):
        cols = st.columns(num_cols)
        for c in range(num_cols):
            if idx >= len(SDG_LIST): break
            sdg_name = SDG_LIST[idx]
            sdg_color = SDG_COLORS[idx]
            sdg_number = idx + 1
            engagement = st.session_state.sdg_engagement.get(sdg_number, 0)
            val = cols[c].slider(f"Engagement % - SDG {sdg_number}", 0, 100, value=engagement, key=f"sdg{sdg_number}")
            st.session_state.sdg_engagement[sdg_number] = val
            cols[c].markdown(f"<div class='sdg-card' style='background-color:{sdg_color}'><div style='font-weight:700'>SDG {sdg_number}</div><div>{sdg_name}</div><div style='margin-top:6px'>Engagement: {val}%</div></div>", unsafe_allow_html=True)
            idx += 1

# ---------------------------
# Pages: Home + others
# ---------------------------
if st.session_state.page == "Home":
    st.title("EinTrust Sustainability Dashboard — Home")
    # show GHG KPIs (same as on GHG page) and a snapshot energy KPI
    kpis = ghg_kpis(st.session_state.entries)
    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{TEXT}'>{kpis['total']:,}</div><div class='kpi-unit'>kg CO₂e</div><div class='kpi-label'>Total Emissions</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{ACCENT2}'>{kpis['scope1']:,}</div><div class='kpi-unit'>kg CO₂e</div><div class='kpi-label'>Scope 1</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{ACCENT2}'>{kpis['scope2']:,}</div><div class='kpi-unit'>kg CO₂e</div><div class='kpi-label'>Scope 2</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{ACCENT}'>{kpis['scope3']:,}</div><div class='kpi-unit'>kg CO₂e</div><div class='kpi-label'>Scope 3</div></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Quick Energy Snapshot (from manual GHG + renewables)")
    # compute quick energy numbers
    energy_from_entries = build_energy_rows_from_entries(st.session_state.entries)
    renew = st.session_state.renewable_entries.copy() if not st.session_state.renewable_entries.empty else pd.DataFrame()
    all_energy = pd.concat([energy_from_entries, renew], ignore_index=True, sort=False) if not energy_from_entries.empty or not renew.empty else pd.DataFrame()
    total_energy_kwh = all_energy["Energy_kWh"].astype(float).sum() if not all_energy.empty else 0.0
    total_co2e = all_energy["CO2e_kg"].astype(float).sum() if not all_energy.empty and "CO2e_kg" in all_energy.columns else 0.0
    st.metric("Estimated Total Energy (kWh)", f"{int(total_energy_kwh):,}")
    st.metric("Estimated Energy-related CO₂e (kg)", f"{total_co2e:,.0f}")

    st.markdown("Use the sidebar to go to GHG or Energy pages for detailed data entry and charts.")

elif st.session_state.page == "GHG":
    render_ghg_dashboard()

elif st.session_state.page == "Energy":
    render_energy_dashboard()

elif st.session_state.page == "Water":
    st.title("Water")
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
    st.info("Detailed water entry UI available in previous versions; kept concise here.")

elif st.session_state.page == "SDG":
    render_sdg_dashboard()

else:
    st.subheader(f"{st.session_state.page} section")
    st.info("This section is under development. Please select other pages from sidebar.")
