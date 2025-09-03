# einboard.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, date

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
.sdg-percent { font-size: 14px; color: rgba(255,255,255,0.9); }
@media (min-width: 768px) { .sdg-card { width: 220px; display: inline-block; } }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Utilities
# ---------------------------

def format_number(v, digits=2):
    """Format float with comma thousands and given decimals."""
    try:
        return f"{v:,.{digits}f}"
    except Exception:
        return str(v)

months = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]

def current_fy_month():
    """Return current month label in Apr→Mar cycle. If today's month not in labels (shouldn't happen), return Apr."""
    m = datetime.now().strftime("%b")
    if m in months:
        return m
    return "Apr"

# ---------------------------
# Emission factors (Indian SME oriented defaults)
# - Where India-specific reliable values are known we include them.
# - For many Scope 3 sub-categories placeholders are provided (0.0 or approximate).
# - NOTE: Replace placeholder values with MoEFCC / CEA / other official references when available.
# ---------------------------
# Units: EF expressed as kg CO2e per unit (unit depends on mapping key)
DEFAULT_EF = {
    # Scope 1 (fuel per liter or kg)
    "Diesel (L)": 2.68,            # kg CO2e per liter — commonly used India avg
    "Petrol (L)": 2.31,
    "LPG (kg_or_L)": 1.51,         # unit mixing — approximate per litre/kg; replace with proper mapping
    "CNG (m3)": 2.02,              # placeholder per m3
    "Coal (kg)": 2.42,             # per kg
    "Biomass (kg)": 0.0,           # often considered biogenic (0) — confirm per application
    # Electricity
    "Grid Electricity (kWh)": 0.82,  # India grid average (approx). Replace with year-specific grid emission factor when possible.
    # Refrigerant leakage (kg of refrigerant -> kg CO2e) (GWP needs to be looked up; placeholders)
    "HFC-134a (kg)": 1430.0,       # example GWP for HFC-134a; convert to kgCO2e/kg refrigerant leaked
    # Scope 3 placeholders (per unit)
    # Purchased goods & services (per tonne or per unit) — placeholders:
    "Cement (tonne)": 900.0,       # kg CO2e per tonne of cement (placeholder)
    "Steel (tonne)": 1850.0,       # kg CO2e per tonne of steel (placeholder)
    "Chemicals (tonne)": 1000.0,   # placeholder
    "Textile (tonne)": 1500.0,     # placeholder
    "Packaging/Cardboard (kg)": 1.5,
    "Packaging/Plastics (kg)": 3.0,
    "Office Paper (kg)": 1.2,
    # Business travel / transport
    "Air Travel (flight)": 250.0,  # placeholder per flight (short-haul avg) — better to use distance-based factors
    "Train Travel (km)": 0.05,     # kgCO2e per passenger-km (placeholder)
    "Taxi (km)": 0.18,             # placeholder
    "Employee Commuting (km)": 0.12, # placeholder per person-km
    # Waste
    "Landfill (kg_waste)": 0.5,     # placeholder kgCO2e per kg waste
    "Recycling (kg_waste)": 0.05,
    # Transportation (freight)
    "Truck Freight (tkm)": 0.12,    # kgCO2e per tonne-km (placeholder)
    "Third-party Logistics (tkm)": 0.12,
    # Use of sold products / end-of-life
    "Use of Product (unit)": 0.0,   # placeholder
    "End-of-Life Recycling (kg)": 0.02,
    # Electricity: purchased green energy (assumed zero)
    "Purchased Green (kWh)": 0.0
}

# Short mapping helpers: map common sub-activity or specific item names to EF keys & units
EF_LOOKUP = {
    # fuels
    "Diesel Generator": ("Diesel (L)", "L"),
    "Diesel Vehicle": ("Diesel (L)", "L"),
    "Petrol Generator": ("Petrol (L)", "L"),
    "Petrol Car": ("Petrol (L)", "L"),
    "LPG Boiler": ("LPG (kg_or_L)", "kg_or_L"),
    "CNG Vehicle": ("CNG (m3)", "m3"),
    "Coal Boiler": ("Coal (kg)", "kg"),
    "Biomass Furnace": ("Biomass (kg)", "kg"),
    "Grid Electricity": ("Grid Electricity (kWh)", "kWh"),
    "Purchased Green Energy": ("Purchased Green (kWh)", "kWh"),
    # common Scope 3 items
    "Cement": ("Cement (tonne)", "tonne"),
    "Steel": ("Steel (tonne)", "tonne"),
    "Chemicals": ("Chemicals (tonne)", "tonne"),
    "Textile": ("Textile (tonne)", "tonne"),
    "Cardboard": ("Packaging/Cardboard (kg)", "kg"),
    "Plastics": ("Packaging/Plastics (kg)", "kg"),
    "Paper": ("Office Paper (kg)", "kg"),
    # travel
    "Air Travel": ("Air Travel (flight)", "flight"),
    "Train Travel": ("Train Travel (km)", "km"),
    "Taxi / Cab / Auto": ("Taxi (km)", "km"),
    # waste
    "Landfill": ("Landfill (kg_waste)", "kg"),
    "Recycling": ("Recycling (kg_waste)", "kg"),
    # freight
    "Incoming Goods Transport": ("Truck Freight (tkm)", "tkm"),
    "Third-party Logistics": ("Third-party Logistics (tkm)", "tkm"),
}

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
# Initialize Data (session)
# ---------------------------
if "entries" not in st.session_state:
    st.session_state.entries = pd.DataFrame(columns=[
        "Scope","Activity","Sub-Activity","Specific Item","Quantity","Unit","Month","Timestamp","Emissions_kgCO2e"
    ])
if "renewable_entries" not in st.session_state:
    st.session_state.renewable_entries = pd.DataFrame(columns=["Source","Location","Month","Energy_kWh","CO2e_kg","Type"])
if "sdg_engagement" not in st.session_state:
    st.session_state.sdg_engagement = {i: 0 for i in range(1, 18)}

# ---------------------------
# Scope activities (including all 15 Scope 3 categories per GHG Protocol)
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
        }
    },
    "Scope 2": {
        "Electricity Consumption": {
            "Grid Electricity": "Electricity bought from grid",
            "Purchased Green Energy": "Energy attribute certificates / green energy purchases"
        }
    },
    "Scope 3": {
        # 15 categories (GHG Protocol) mapped simply for easy selection
        "Purchased Goods & Services": {
            "Raw Materials": ["Cement","Steel","Chemicals","Textile"],
            "Packaging Materials": ["Cardboard","Plastics","Glass"],
            "Office Supplies": ["Paper","Ink","Stationery"],
            "Purchased Services": ["Printing","Logistics","Cleaning","IT"]
        },
        "Capital Goods": {"Machinery": None, "Buildings": None},
        "Fuel- and Energy-Related Activities (not included in Scope 1 or 2)": {"Extraction & Production": None},
        "Upstream Transportation & Distribution": {"Incoming Goods Transport": None, "Third-party Logistics": None},
        "Waste Generated in Operations": {"Landfill": None, "Recycling": None, "Composting / Biogas": None},
        "Business Travel": {"Air Travel": None, "Train Travel": None, "Taxi / Cab / Auto": None},
        "Employee Commuting": {"Two-Wheelers": None, "Cars / Vans": None, "Public Transport": None},
        "Upstream Leased Assets": {"Leased Building Energy": None},
        "Downstream Transportation & Distribution": {"Delivery to Customers": None, "Retail / Distributor Transport": None},
        "Processing of Sold Products": {"Processing": None},
        "Use of Sold Products": {"Product Use": None},
        "End-of-Life Treatment of Sold Products": {"Recycling / Landfill": None},
        "Downstream Leased Assets": {"Leased Asset Use": None},
        "Franchises": {"Franchise Operations": None},
        "Investments": {"Investments": None}
    }
}

# ---------------------------
# Emissions calculation helper
# ---------------------------
def calculate_emissions(scope, activity, sub_activity, specific_item, quantity, unit):
    """
    Try to find an emission factor for this entry and compute emissions (kg CO2e).
    Priority: specific_item -> sub_activity -> activity -> scope-level -> fallback placeholder/0.
    Returns (emissions_kg, missing_flag)
    missing_flag True if no EF found and emissions = 0 (placeholder).
    """
    missing = False
    emissions = 0.0

    # 1) Try exact specific_item mapping if provided
    key_candidate = None
    if specific_item:
        # direct key if in EF_LOOKUP
        if specific_item in EF_LOOKUP:
            ef_key, ef_unit = EF_LOOKUP[specific_item]
            ef = DEFAULT_EF.get(ef_key)
            if ef is not None:
                # if unit matches expectation, multiply directly
                emissions = float(quantity) * float(ef)
                return emissions, False
        # Try variations (e.g., "Cement" etc.)
        if str(specific_item) in DEFAULT_EF:
            ef = DEFAULT_EF.get(str(specific_item))
            if ef is not None:
                emissions = float(quantity) * float(ef)
                return emissions, False

    # 2) Try sub_activity mapping via EF_LOOKUP
    if sub_activity in EF_LOOKUP:
        ef_key, ef_unit = EF_LOOKUP[sub_activity]
        ef = DEFAULT_EF.get(ef_key)
        if ef is not None:
            # handle per-unit types: if ef_unit is 'tkm' require quantity in tonne-km, etc.
            emissions = float(quantity) * float(ef)
            return emissions, False

    # 3) Try mapping by activity name
    if activity in EF_LOOKUP:
        ef_key, ef_unit = EF_LOOKUP[activity]
        ef = DEFAULT_EF.get(ef_key)
        if ef is not None:
            emissions = float(quantity) * float(ef)
            return emissions, False

    # 4) Try generic fallbacks for well-known units
    # Recognize common unit strings for fuels and electricity
    if isinstance(unit, str):
        u = unit.lower()
        if "lit" in u or "l" == u.strip():
            # assume diesel/petrol context from sub_activity or activity
            # prefer Diesel if sub_activity contains Diesel else Petrol if contains Petrol
            if "diesel" in sub_activity.lower() or "diesel" in activity.lower():
                ef = DEFAULT_EF.get("Diesel (L)")
                emissions = float(quantity) * (ef if ef else 0.0)
                return emissions, ef is None
            if "petrol" in sub_activity.lower() or "petrol" in activity.lower():
                ef = DEFAULT_EF.get("Petrol (L)")
                emissions = float(quantity) * (ef if ef else 0.0)
                return emissions, ef is None
            # fallback unknown fuel
        if "kwh" in u:
            ef = DEFAULT_EF.get("Grid Electricity (kWh)")
            emissions = float(quantity) * (ef if ef else 0.0)
            return emissions, ef is None
        if "tonne" in u or "ton" in u:
            # try to map specific_item to commodity EFs
            if specific_item and specific_item in DEFAULT_EF:
                ef = DEFAULT_EF.get(specific_item)
                emissions = float(quantity) * (ef if ef else 0.0)
                return emissions, ef is None

    # 5) Try to map some Scope-3 common names
    if specific_item in ["Cement","Steel","Chemicals","Textile"]:
        ef_key, _ = EF_LOOKUP.get(specific_item, (None, None))
        if ef_key:
            ef = DEFAULT_EF.get(ef_key)
            if ef:
                emissions = float(quantity) * float(ef)
                return emissions, False

    # 6) Last resort: attempt to infer from sub_activity token words
    lowered = (sub_activity or "").lower() + " " + (activity or "").lower()
    if "electric" in lowered:
        ef = DEFAULT_EF.get("Grid Electricity (kWh)")
        if ef is not None:
            emissions = float(quantity) * ef
            return emissions, False

    # If reached here, EF not found — return 0 with missing flag
    missing = True
    return 0.0, missing

# ---------------------------
# GHG Dashboard (NEW structure requested)
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
        df["Month"] = df.get("Month", "")
        df["Month"] = df["Month"].replace("", np.nan)
        df["Month"] = df["Month"].fillna(current_fy_month())
        # Ensure Month is categorical ordered
        df["Month"] = pd.Categorical(df["Month"], categories=months, ordered=True)
        # Group by Month & Scope
        monthly = df.groupby(["Month","Scope"])["Emissions_kgCO2e"].sum().reset_index()
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
        unit = None
        # try common units from units mapping/EF lookup
        if specific_item and specific_item in EF_LOOKUP:
            unit = EF_LOOKUP[specific_item][1]
        elif sub_activity in EF_LOOKUP:
            unit = EF_LOOKUP[sub_activity][1]
        elif activity in EF_LOOKUP:
            unit = EF_LOOKUP[activity][1]
        if unit is None:
            # fallback guesses
            unit = "kg / Tonnes"

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
                st.warning("Emission factor not found for this entry. Emissions recorded as 0. Please replace placeholder EFs with official MoEFCC/CEA values if available.")
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
# Energy Dashboard (kept as before)
# ---------------------------
def render_energy_dashboard(include_input=True, show_chart=True):
    st.subheader("Energy")
    df = st.session_state.entries.copy()

    calorific_values = {"Diesel":35.8,"Petrol":34.2,"LPG":46.1,"CNG":48,"Coal":24,"Biomass":15}
    emission_factors = {"Diesel":2.68,"Petrol":2.31,"LPG":1.51,"CNG":2.02,"Coal":2.42,"Biomass":0.0,
                        "Electricity":0.82,"Solar":0.0,"Wind":0.0,"Purchased Green Energy":0.0,"Biogas":0.0}

    scope1_2_data = df[df["Scope"].isin(["Scope 1","Scope 2"])].copy()

    if not scope1_2_data.empty:
        def compute_energy(row):
            fuel = row["Sub-Activity"]
            qty = row["Quantity"]
            energy_kwh = qty if fuel=="Grid Electricity" else (qty*calorific_values.get(fuel,0))/3.6
            co2e = qty * emission_factors.get(fuel,0)
            return pd.Series([energy_kwh, co2e])
        scope1_2_data[["Energy_kWh","CO2e_kg"]] = scope1_2_data.apply(compute_energy, axis=1)
        scope1_2_data["Type"] = "Fossil"
        scope1_2_data["Month"] = np.random.choice(months, len(scope1_2_data))

    all_energy = (
        pd.concat([scope1_2_data.rename(columns={"Sub-Activity":"Fuel"}), st.session_state.renewable_entries], ignore_index=True)
        if not st.session_state.renewable_entries.empty else scope1_2_data
    )

    total_energy = all_energy.groupby("Type")["Energy_kWh"].sum().to_dict() if not all_energy.empty else {}
    fossil_energy = total_energy.get("Fossil",0)
    renewable_energy = total_energy.get("Renewable",0)
    total_sum = fossil_energy + renewable_energy

    c1,c2,c3 = st.columns(3)
    for col,label,value,color in zip(
        [c1,c2,c3],
        ["Total Energy (kWh)","Fossil Energy (kWh)","Renewable Energy (kWh)"],
        [total_sum,fossil_energy,renewable_energy],
        ["#ffffff","#f39c12","#2ecc71"]
    ):
        col.markdown(
            f"<div class='kpi'><div class='kpi-value' style='color:{color}'>{int(value):,}</div>"
            f"<div class='kpi-unit'>kWh</div><div class='kpi-label'>{label.lower()}</div></div>",
            unsafe_allow_html=True
        )

    if show_chart and not all_energy.empty:
        all_energy["Month"] = pd.Categorical(all_energy.get("Month", months[0]), categories=months, ordered=True)
        monthly_trend = all_energy.groupby(["Month","Type"])["Energy_kWh"].sum().reset_index()
        st.subheader("Monthly Energy Consumption (kWh)")
        fig = px.bar(monthly_trend, x="Month", y="Energy_kWh", color="Type", barmode="stack", color_discrete_map={"Fossil":"#f39c12","Renewable":"#2ecc71"})
        st.plotly_chart(fig, use_container_width=True)

    if include_input:
        st.subheader("Add Renewable Energy Entry")
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
            monthly_energy = annual_energy / 12 if annual_energy else 0.0
            for m in months:
                renewable_list.append({
                    "Source":source,"Location":location,"Month":m,
                    "Energy_kWh":monthly_energy,"Type":"Renewable",
                    "CO2e_kg":monthly_energy*emission_factors.get(source,0)
                })
        if renewable_list and st.button("Add Renewable Energy Entries"):
            new_entries_df = pd.DataFrame(renewable_list)
            st.session_state.renewable_entries = pd.concat([st.session_state.renewable_entries, new_entries_df], ignore_index=True)
            st.success(f"{len(new_entries_df)} entries added!")
            st.experimental_rerun()

# ---------------------------
# SDG Dashboard (no sliders per request)
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
    st.subheader("Company Engagement by SDG (set % values below)")
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
            # no slider: use numeric input 0-100
            current_val = st.session_state.sdg_engagement.get(sdg_number, 0)
            val = cols[c].number_input(f"SDG {sdg_number} - {sdg_name}", min_value=0, max_value=100, value=current_val, key=f"sdgnum{sdg_number}")
            st.session_state.sdg_engagement[sdg_number] = val
            cols[c].markdown(
                f"<div class='sdg-card' style='background-color:{sdg_color}'>"
                f"<div class='sdg-number'>SDG {sdg_number}</div>"
                f"<div class='sdg-name'>{sdg_name}</div>"
                f"<div class='sdg-percent'>Engagement: {val}%</div>"
                f"</div>",
                unsafe_allow_html=True
            )
            idx += 1

# ---------------------------
# Render Pages
# ---------------------------
if st.session_state.page == "Home":
    st.title("EinTrust Sustainability Dashboard")
    # KPI summary on Home as well (call same GHG KPI logic but do not show the whole GHG page input)
    # We'll show KPI cards and compact energy summary (no inputs)
    # Compute KPIs
    df_home = st.session_state.entries.copy()
    if "Emissions_kgCO2e" not in df_home.columns:
        df_home["Emissions_kgCO2e"] = 0.0
    s1 = df_home[df_home["Scope"]=="Scope 1"]["Emissions_kgCO2e"].sum() if not df_home.empty else 0.0
    s2 = df_home[df_home["Scope"]=="Scope 2"]["Emissions_kgCO2e"].sum() if not df_home.empty else 0.0
    s3 = df_home[df_home["Scope"]=="Scope 3"]["Emissions_kgCO2e"].sum() if not df_home.empty else 0.0
    total_kg = s1 + s2 + s3
    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(f"<div class='kpi'><div class='kpi-value'>{format_number(total_kg/1000.0,3)}</div><div class='kpi-unit'>t CO₂e</div><div class='kpi-label'>Total Emissions</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='kpi'><div class='kpi-value'>{format_number(s1/1000.0,3)}</div><div class='kpi-unit'>t CO₂e</div><div class='kpi-label'>Scope 1</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='kpi'><div class='kpi-value'>{format_number(s2/1000.0,3)}</div><div class='kpi-unit'>t CO₂e</div><div class='kpi-label'>Scope 2</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='kpi'><div class='kpi-value'>{format_number(s3/1000.0,3)}</div><div class='kpi-unit'>t CO₂e</div><div class='kpi-label'>Scope 3</div></div>", unsafe_allow_html=True)

    # Compact charts: show small energy and emissions trends if available
    render_energy_dashboard(include_input=False, show_chart=False)

elif st.session_state.page == "GHG":
    render_ghg_dashboard()

elif st.session_state.page == "Energy":
    render_energy_dashboard(include_input=True, show_chart=True)

elif st.session_state.page == "SDG":
    render_sdg_dashboard()

else:
    st.subheader(f"{st.session_state.page} section")
    st.info("This section is under development. Please select other pages from sidebar.")
