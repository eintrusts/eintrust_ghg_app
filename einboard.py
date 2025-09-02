# EinTrust Sustainability Dashboard - FULL app (GHG page restructured)
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

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
# Initialize / persist session dataframes
# ---------------------------
if "entries" not in st.session_state:
    st.session_state.entries = pd.DataFrame(columns=[
        "Scope","Activity","Sub-Activity","Specific Item","Quantity","Unit","Month","Timestamp","Emissions_kgCO2e"
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

# ---------------------------
# Constants / Lookups
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

# Activities mapping (Scope 1, 2 and full 15 scope3 categories)
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

# Units lookup
units_dict = {
    "Diesel Generator":"Liters","Petrol Generator":"Liters","LPG Boiler":"Liters","Coal Boiler":"kg","Biomass Furnace":"kg",
    "Diesel Vehicle":"Liters","Petrol Car":"Liters","CNG Vehicle":"m³","Diesel Forklift":"Liters","Petrol Two-Wheeler":"Liters",
    "Cement":"Tonnes","Steel":"Tonnes","Chemicals":"Tonnes","Textile":"Tonnes","Paper":"kg",
    "Cardboard":"kg","Plastics":"kg","Glass":"kg",
    "Grid Electricity":"kWh","Diesel Generator Electricity":"kWh","Purchased Steam":"Tonnes","Purchased Cooling":"kWh",
    "Air Travel":"Number of flights","Train Travel":"km traveled","Taxi/Car Rental":"km traveled",
    "Two-Wheelers":"km traveled","Cars/Vans":"km traveled","Public Transport":"km traveled",
    "Landfill":"kg","Recycling":"kg","Composting":"kg","Product Use (Energy)":"kWh"
}

# Starter emission factors (kg CO2e per unit). Replace with your official factors later.
emission_factors = {
    "Diesel":2.68,"Petrol":2.31,"LPG":1.51,"CNG":2.02,"Coal":2.42,"Electricity":0.82,
    "Cement":900.0,"Steel":1850.0,"Textile":300.0,"Chemicals":1200.0,"Paper":1.2,
    "Cardboard":0.9,"Plastics":1.7,"Glass":0.95,
    "Air Travel (domestic average)":250.0,"Train per km":0.05,"Taxi per km":0.12,
    "TwoWheeler per km":0.05,"Car per km":0.12,
    "Landfill per kg":1.0,"Recycling per kg":0.3,"Composting per kg":0.2,
    "Product use kWh":0.82
}

# ---------------------------
# Helpers
# ---------------------------
def format_number(x, dp=0):
    try:
        if dp==0:
            return f"{int(round(x)):,}"
        else:
            return f"{x:,.{dp}f}"
    except:
        return x

def current_fy_month():
    # return nearest FY month name (Apr-Mar). We'll default to current calendar month mapped to FY label
    m = datetime.now().month
    # map 1->Jan etc., return corresponding label from months list
    labels = {
        1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"
    }
    return labels.get(m, "Apr")

def calculate_emissions(scope, activity, sub_activity, specific_item, quantity, unit):
    """Return (emissions_kg, missing_flag)"""
    missing = False
    emissions = 0.0
    q = float(quantity) if quantity not in [None,"","nan"] else 0.0
    key_specific = (specific_item or "").strip()
    key_sub = (sub_activity or "").strip()
    # Scope 1 & 2
    if scope in ["Scope 1","Scope 2"]:
        fuel_key = None
        if "Electricity" in key_sub or (unit and unit.lower()=="kwh"):
            fuel_key = "Electricity"
        elif "Diesel" in key_sub:
            fuel_key = "Diesel"
        elif "Petrol" in key_sub:
            fuel_key = "Petrol"
        elif "LPG" in key_sub:
            fuel_key = "LPG"
        elif "Coal" in key_sub:
            fuel_key = "Coal"
        elif "CNG" in key_sub:
            fuel_key = "CNG"
        if fuel_key and fuel_key in emission_factors:
            emissions = q * emission_factors[fuel_key]
        else:
            missing = True
    else:
        # Scope 3 heuristics
        if key_specific in emission_factors:
            emissions = q * emission_factors[key_specific]
        elif key_sub in ["Air Travel"]:
            fact = emission_factors.get("Air Travel (domestic average)")
            if fact:
                emissions = q * fact
            else:
                missing = True
        elif key_sub in ["Train Travel"]:
            fact = emission_factors.get("Train per km")
            if fact:
                emissions = q * fact
            else:
                missing = True
        elif key_sub in ["Taxi/Car Rental","Cars/Vans"]:
            fact = emission_factors.get("Car per km")
            if fact:
                emissions = q * fact
            else:
                missing = True
        elif key_sub in ["Two-Wheelers"]:
            fact = emission_factors.get("TwoWheeler per km")
            if fact:
                emissions = q * fact
            else:
                missing = True
        elif key_sub in ["Landfill","Recycling","Composting"]:
            mapk = {"Landfill":"Landfill per kg","Recycling":"Recycling per kg","Composting":"Composting per kg"}
            fact = emission_factors.get(mapk.get(key_sub))
            if fact:
                emissions = q * fact
            else:
                missing = True
        elif unit and unit.lower()=="kwh":
            fact = emission_factors.get("Product use kWh")
            if fact:
                emissions = q * fact
            else:
                missing = True
        else:
            # try specific item mapping
            for candidate in [key_specific, key_sub, activity]:
                if candidate in emission_factors:
                    emissions = q * emission_factors[candidate]
                    break
            else:
                missing = True

    return float(emissions), missing

# ---------------------------
# GHG Page (restructured)
# ---------------------------
def render_ghg_dashboard():
    st.title("GHG Emissions")

    # Top KPI Summary (also used on Home)
    st.subheader("KPI Summary")
    # compute totals from session_state.entries
    df = st.session_state.entries.copy()
    # ensure emissions column exists
    if "Emissions_kgCO2e" not in df.columns:
        df["Emissions_kgCO2e"] = 0.0
    # sum by scope
    s1 = df[df["Scope"]=="Scope 1"]["Emissions_kgCO2e"].sum() if not df.empty else 0.0
    s2 = df[df["Scope"]=="Scope 2"]["Emissions_kgCO2e"].sum() if not df.empty else 0.0
    s3 = df[df["Scope"]=="Scope 3"]["Emissions_kgCO2e"].sum() if not df.empty else 0.0
    total_kg = s1 + s2 + s3
    # convert to tonnes for display
    total_t = total_kg / 1000.0
    s1_t = s1 / 1000.0
    s2_t = s2 / 1000.0
    s3_t = s3 / 1000.0

    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(f"<div class='kpi'><div class='kpi-value'>{format_number(total_t,3)}</div><div class='kpi-unit'>t CO₂e</div><div class='kpi-label'>Total Emissions</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='kpi'><div class='kpi-value'>{format_number(s1_t,3)}</div><div class='kpi-unit'>t CO₂e</div><div class='kpi-label'>Scope 1</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='kpi'><div class='kpi-value'>{format_number(s2_t,3)}</div><div class='kpi-unit'>t CO₂e</div><div class='kpi-label'>Scope 2</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='kpi'><div class='kpi-value'>{format_number(s3_t,3)}</div><div class='kpi-unit'>t CO₂e</div><div class='kpi-label'>Scope 3</div></div>", unsafe_allow_html=True)

    st.markdown("---")

    # Monthly Trends (Apr -> Mar) - line chart for Scope1/2/3 and Total
    st.subheader("Monthly Emissions Trend (Apr → Mar)")
    if df.empty:
        st.info("No GHG entries yet. Add entries below to populate monthly trends.")
    else:
        # If Month missing in some rows, fill with current fy month
        df["Month"] = df["Month"].replace("", np.nan)
        df["Month"] = df["Month"].fillna(current_fy_month())
        # Ensure Month is categorical ordered
        df["Month"] = pd.Categorical(df["Month"], categories=months, ordered=True)
        # Group by Month & Scope
        monthly = df.groupby(["Month","Scope"])["Emissions_kgCO2e"].sum().reset_index()
        # add Total per month
        total_month = df.groupby(["Month"])["Emissions_kgCO2e"].sum().reset_index().rename(columns={"Emissions_kgCO2e":"Total_kg"})
        # pivot for plotting
        monthly_pivot = monthly.pivot(index="Month", columns="Scope", values="Emissions_kgCO2e").fillna(0)
        monthly_plot = monthly_pivot.copy()
        monthly_plot["Total"] = monthly_plot.sum(axis=1)
        monthly_plot = monthly_plot.reset_index().melt(id_vars="Month", var_name="Category", value_name="Emissions_kg")
        # convert to tonnes
        monthly_plot["Emissions_t"] = monthly_plot["Emissions_kg"] / 1000.0
        fig = px.line(monthly_plot, x="Month", y="Emissions_t", color="Category", markers=True,
                      labels={"Emissions_t":"t CO₂e"}, title="Monthly Emissions (t CO₂e) by Scope")
        fig.update_layout(xaxis={'categoryorder':'array', 'categoryarray':months})
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Input form (manual entry + file upload)
    st.subheader("Add GHG Entry")

    with st.form("ghg_manual_form", clear_on_submit=False):
        scope = st.selectbox("Scope", ["Scope 1","Scope 2","Scope 3"])
        if scope != "Scope 3":
            activity = st.selectbox("Activity", list(scope_activities[scope].keys()))
            sub_activity = st.selectbox("Sub-Activity", list(scope_activities[scope][activity].keys()))
            st.info(scope_activities[scope][activity][sub_activity])
            specific_item = st.text_input("Specific Item (optional)", value="")
        else:
            activity = st.selectbox("Scope 3 Category", list(scope_activities["Scope 3"].keys()))
            sub_activity = st.selectbox("Sub-Category", list(scope_activities["Scope 3"][activity].keys()))
            if isinstance(scope_activities["Scope 3"][activity][sub_activity], list):
                specific_item = st.selectbox("Specific Item (choose from list)", scope_activities["Scope 3"][activity][sub_activity])
            else:
                specific_item = st.text_input("Specific Item (optional)", value="")

        # auto unit
        unit = units_dict.get(specific_item, units_dict.get(sub_activity, "kg / Tonnes"))
        quantity = st.number_input(f"Quantity ({unit})", min_value=0.0, format="%.3f")
        month = st.selectbox("Month (financial year Apr→Mar)", months, index=0 if current_fy_month()=="Apr" else months.index(current_fy_month()))
        submitted = st.form_submit_button("Add Entry")

        if submitted:
            emissions, missing = calculate_emissions(scope, activity, sub_activity, specific_item, quantity, unit)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            entry = {
                "Scope": scope,
                "Activity": activity,
                "Sub-Activity": sub_activity,
                "Specific Item": specific_item,
                "Quantity": quantity,
                "Unit": unit,
                "Month": month,
                "Timestamp": timestamp,
                "Emissions_kgCO2e": round(float(emissions),3)
            }
            st.session_state.entries = pd.concat([st.session_state.entries, pd.DataFrame([entry])], ignore_index=True)
            if missing:
                st.warning("Emission factor not found for this entry. Emissions recorded as 0. You can upload custom emission factors or edit later.")
            else:
                st.success("Entry added with emissions calculated.")

    st.markdown("**Or upload a CSV/XLSX file** with columns: `Scope,Activity,Sub-Activity,Specific Item,Quantity,Unit,Month` (Month optional).")
    uploaded = st.file_uploader("Upload CSV/XLS/XLSX", type=["csv","xls","xlsx"])
    if uploaded:
        try:
            if uploaded.name.endswith(".csv"):
                file_df = pd.read_csv(uploaded)
            else:
                file_df = pd.read_excel(uploaded)
            required = {"Scope","Activity","Sub-Activity","Quantity","Unit"}
            if not required.issubset(set(file_df.columns)):
                st.error(f"Upload must include columns: {required}")
            else:
                file_df = file_df.fillna("")
                rows = []
                for _, r in file_df.iterrows():
                    q = r["Quantity"]
                    month_val = r.get("Month") if "Month" in r and r["Month"]!="" else current_fy_month()
                    emissions, missing = calculate_emissions(r["Scope"], r["Activity"], r["Sub-Activity"], r.get("Specific Item",""), q, r["Unit"])
                    rows.append({
                        "Scope": r["Scope"],
                        "Activity": r["Activity"],
                        "Sub-Activity": r["Sub-Activity"],
                        "Specific Item": r.get("Specific Item",""),
                        "Quantity": q,
                        "Unit": r["Unit"],
                        "Month": month_val,
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Emissions_kgCO2e": round(float(emissions),3)
                    })
                if rows:
                    st.session_state.entries = pd.concat([st.session_state.entries, pd.DataFrame(rows)], ignore_index=True)
                    st.success(f"Uploaded {len(rows)} rows. Emissions computed where factors available.")
        except Exception as e:
            st.error(f"Error reading file: {e}")

    st.markdown("---")

    # All entries table with timestamp (most recent first)
    st.subheader("All Entries (most recent first)")
    if st.session_state.entries.empty:
        st.info("No entries yet.")
    else:
        display = st.session_state.entries.copy()
        # show emissions in tonnes with formatting
        display["Emissions_tCO2e"] = display["Emissions_kgCO2e"].astype(float) / 1000.0
        display["Emissions_tCO2e"] = display["Emissions_tCO2e"].map(lambda x: format_number(x,3))
        display["Quantity"] = display["Quantity"].map(lambda x: format_number(float(x),3))
        # sort by Timestamp desc
        display = display.sort_values("Timestamp", ascending=False)
        st.dataframe(display[["Timestamp","Scope","Activity","Sub-Activity","Specific Item","Quantity","Unit","Month","Emissions_tCO2e"]], use_container_width=True)

        csv = st.session_state.entries.to_csv(index=False).encode('utf-8')
        st.download_button("Download All Entries (with emissions)", csv, "ghg_entries_with_emissions.csv", "text/csv")

# ---------------------------
# Home page: show KPI summary (from GHG) and small overview
# ---------------------------
def render_home():
    st.title("EinTrust Sustainability Dashboard - Home")
    # reuse KPI summary
    df = st.session_state.entries.copy()
    if "Emissions_kgCO2e" not in df.columns:
        df["Emissions_kgCO2e"] = 0.0
    s1 = df[df["Scope"]=="Scope 1"]["Emissions_kgCO2e"].sum() if not df.empty else 0.0
    s2 = df[df["Scope"]=="Scope 2"]["Emissions_kgCO2e"].sum() if not df.empty else 0.0
    s3 = df[df["Scope"]=="Scope 3"]["Emissions_kgCO2e"].sum() if not df.empty else 0.0
    total_t = (s1+s2+s3)/1000.0
    c1,c2 = st.columns([2,3])
    c1.markdown(f"<div class='kpi'><div class='kpi-value'>{format_number(total_t,3)}</div><div class='kpi-unit'>t CO₂e</div><div class='kpi-label'>Total Emissions (all scopes)</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='kpi'><div class='kpi-value'>{format_number((s1/1000.0),3)}</div><div class='kpi-unit'>t CO₂e</div><div class='kpi-label'>Scope 1</div></div>", unsafe_allow_html=True)
    st.markdown("Use the sidebar to go to GHG to add entries or see detailed charts.")

# ---------------------------
# Energy / Water / SDG pages (kept as before, read session_state)
# ---------------------------
def render_energy():
    st.subheader("Energy")
    # reuse previous energy logic but simpler: show totals if exist
    # build energy from entries and renewable_entries (if present)
    df = st.session_state.entries.copy()
    calorific_values = {"Diesel":35.8,"Petrol":34.2,"LPG":46.1,"CNG":48,"Coal":24,"Biomass":15}
    energy_rows = []
    if not df.empty:
        for _, r in df[df["Scope"].isin(["Scope 1","Scope 2"])].iterrows():
            sub = r["Sub-Activity"]
            qty = float(r["Quantity"])
            if "Electricity" in sub or r["Unit"].lower()=="kwh":
                energy_kwh = qty
                co2e = float(r.get("Emissions_kgCO2e",0.0))
            else:
                if "Diesel" in sub:
                    energy_kwh = (qty * calorific_values["Diesel"]) / 3.6
                    co2e = float(r.get("Emissions_kgCO2e",0.0))
                elif "Petrol" in sub:
                    energy_kwh = (qty * calorific_values["Petrol"]) / 3.6
                    co2e = float(r.get("Emissions_kgCO2e",0.0))
                else:
                    energy_kwh = 0.0
                    co2e = float(r.get("Emissions_kgCO2e",0.0))
            energy_rows.append({"Location":r.get("Specific Item","Unknown"), "Energy_kWh": energy_kwh, "CO2e_kg": co2e, "Type":"Fossil", "Month": r.get("Month", current_fy_month())})
    renewable = st.session_state.renewable_entries.copy() if not st.session_state.renewable_entries.empty else pd.DataFrame()
    all_energy = pd.concat([pd.DataFrame(energy_rows), renewable], ignore_index=True) if not renewable.empty or energy_rows else pd.DataFrame()
    if not all_energy.empty:
        all_energy["Month"] = pd.Categorical(all_energy["Month"], categories=months, ordered=True)
        monthly_trend = all_energy.groupby(["Month","Type"])["Energy_kWh"].sum().reset_index()
        st.subheader("Monthly Energy (kWh)")
        fig = px.line(monthly_trend, x="Month", y="Energy_kWh", color="Type", markers=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No energy data available. Add GHG entries or renewable inputs.")

def render_water():
    st.subheader("Water")
    water_df = st.session_state.water_data.copy()
    adv_df = st.session_state.advanced_water_data.copy()
    total_water = water_df["Quantity_m3"].sum() if not water_df.empty else 0
    total_cost = water_df["Cost_INR"].sum() if not water_df.empty else 0
    recycled = adv_df["Water_Recycled_m3"].sum() if not adv_df.empty else 0
    rain = adv_df["Rainwater_Harvested_m3"].sum() if not adv_df.empty else 0
    st.metric("Total Water Used (m³)", format_number(total_water))
    st.metric("Estimated Cost (INR)", f"₹ {format_number(total_cost)}")
    st.metric("Recycled Water (m³)", format_number(recycled))
    st.metric("Rainwater Harvested (m³)", format_number(rain))
    st.info("Detailed Water page available under the Water menu.")

def render_sdg():
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
            engagement = cols[c].slider(f"Engagement % - SDG {sdg_number}", 0, 100, value=engagement, key=f"sdg{sdg_number}")
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
# Render pages
# ---------------------------
if st.session_state.page == "Home":
    render_home()

elif st.session_state.page == "GHG":
    render_ghg_dashboard()

elif st.session_state.page == "Energy":
    render_energy()

elif st.session_state.page == "Water":
    render_water()

elif st.session_state.page == "SDG":
    render_sdg()

else:
    st.subheader(f"{st.session_state.page} section")
    st.info("This section is under development. Please select other pages from sidebar.")
