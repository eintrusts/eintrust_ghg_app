# einboard.py
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
.kpi:hover { transform: scale(1.03); box-shadow: 0 8px 20px rgba(0,0,0,0.6); }
.kpi-value { font-size: 28px; font-weight: 700; color: #ffffff; margin-bottom: 5px; }
.kpi-unit { font-size: 16px; font-weight: 500; color: #cfd8dc; margin-bottom: 5px; }
.kpi-label { font-size: 14px; color: #cfd8dc; letter-spacing: 0.5px; }
.sdg-card { border-radius: 10px; padding: 15px; margin: 8px; display: inline-block; width: 100%; min-height: 110px; text-align: left; color: white; }
.sdg-number { font-weight: 700; font-size: 20px; }
.sdg-name { font-size: 16px; margin-bottom: 5px; }
.sdg-percent { font-size: 14px; }
@media (min-width: 768px) { .sdg-card { width: 220px; display: inline-block; } }
.sidebar .stButton>button { width: 100%; }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Utilities
# ---------------------------
def fmt_num(x):
    try:
        return f"{float(x):,.2f}"
    except Exception:
        return str(x)

# ---------------------------
# Sidebar & Navigation
# ---------------------------
if "page" not in st.session_state:
    st.session_state.page = "Home"

def sidebar_button(label):
    active = st.session_state.page == label
    if st.button(label, key=f"btn_{label}"):
        st.session_state.page = label

with st.sidebar:
    st.image("https://github.com/eintrusts/eintrust_ghg_app/blob/main/EinTrust%20%20(2).png?raw=true", use_container_width=True)
    st.markdown("---")
    sidebar_button("Home")
    env = st.expander("Environment", expanded=True)
    with env:
        sidebar_button("GHG")
        sidebar_button("Energy")
        sidebar_button("Water")
        sidebar_button("Waste")
        sidebar_button("Biodiversity")
    soc = st.expander("Social", expanded=False)
    with soc:
        sidebar_button("Employee")
        sidebar_button("Health & Safety")
        sidebar_button("CSR")
    gov = st.expander("Governance", expanded=False)
    with gov:
        sidebar_button("Board")
        sidebar_button("Policies")
        sidebar_button("Compliance")
        sidebar_button("Risk Management")
    sidebar_button("SDG")
    reports = st.expander("Reports", expanded=False)
    with reports:
        sidebar_button("BRSR")
        sidebar_button("GRI")
        sidebar_button("CDP")
        sidebar_button("TCFD")
    st.markdown("---")
    sidebar_button("Settings")
    sidebar_button("Log Out")

# ---------------------------
# Initialize Session DataFrames
# ---------------------------
if "entries" not in st.session_state:
    st.session_state.entries = pd.DataFrame(columns=[
        "Timestamp","Scope","Activity","Category","Sub-Activity","Specific Item",
        "Quantity","Unit","Emission Factor (kgCO2e/unit)","Emissions_kgCO2e"
    ])

if "renewable_entries" not in st.session_state:
    st.session_state.renewable_entries = pd.DataFrame(columns=[
        "Source","Location","Month","Energy_kWh","CO2e_kg","Type"
    ])

if "sdg_engagement" not in st.session_state:
    st.session_state.sdg_engagement = {i:0 for i in range(1,18)}

# ---------------------------
# Constants: Scope Activities (GHG Protocol 15 categories)
# ---------------------------
months = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]

SCOPE_ACTIVITIES = {
    "Scope 1": {
        "Stationary Combustion": ["Diesel Generator","LPG Boiler","Coal Boiler","Biomass Furnace"],
        "Mobile Combustion": ["Diesel Vehicle","Petrol Car","CNG Vehicle","Diesel Forklift","Petrol Two-Wheeler"],
        "Process Emissions": ["Cement Production","Steel Production","Chemical Processes"],
        "Fugitive Emissions": ["Refrigerant (HFC/HCFC)","Methane (CH4)"]
    },
    "Scope 2": {
        "Electricity": ["Grid Electricity","Purchased Renewable Electricity"],
        "Steam/Heat/Cooling": ["Purchased Steam","Purchased Cooling"]
    },
    "Scope 3": {
        # GHG Protocol 15 Categories (listed for user-friendly selection)
        "Purchased goods & services": None,
        "Capital goods": None,
        "Fuel- and energy-related activities (not included in Scope 1 or 2)": None,
        "Upstream transportation & distribution": None,
        "Waste generated in operations": None,
        "Business travel": None,
        "Employee commuting": None,
        "Upstream leased assets": None,
        "Downstream transportation & distribution": None,
        "Processing of sold products": None,
        "Use of sold products": None,
        "End-of-life treatment of sold products": None,
        "Downstream leased assets": None,
        "Franchises": None,
        "Investments": None
    }
}

# ---------------------------
# Default Emission Factors (kg CO2e per unit)
# NOTE: These are example default values included to get the app working.
# Replace these with official, up-to-date national/sector factors (BEIS/DEFRA, EPA, IEA, country-specific grid factors, or supplier-specific factors).
# ---------------------------
DEFAULT_EF = {
    # fuels (kg CO2e per liter unless indicated)
    "Diesel (L)": 2.68,         # diesel litres -> kg CO2e (example)
    "Petrol (L)": 2.31,         # petrol litres -> kg CO2e (example)
    "LPG (L)": 1.51,
    "CNG (kg or m3)": 2.02,
    "Coal (kg)": 2.42,
    "Biomass (kg)": 0.0,
    # electricity
    "Grid Electricity (kWh)": 0.82,   # placeholder; replace with national grid factor (kgCO2e/kWh)
    "Purchased Renewable Electricity (kWh)": 0.0,
    # transport (kg CO2e per passenger-km or per vehicle-km depending on use)
    "Car - petrol (km)": 0.192,   # example: 0.192 kgCO2e/km
    "Car - diesel (km)": 0.171,
    "Bus (km)": 0.103,
    "Train (km)": 0.041,
    "Air - short haul (kg per passenger-km)": 0.254,  # placeholders
    "Air - long haul (kg per passenger-km)": 0.195,
    # refrigerants / fugitive (kg CO2e per kg of refrigerant based on GWP)
    "HFC (kg)": 1430.0,   # example: HFC-134a GWP ~1430 -> kg CO2e per kg
    # product/process - per tonne or per unit
    "Cement (t)": 800.0,   # kg CO2e per tonne (example, substitute accurate factors)
    "Steel (t)": 1850.0,
    # waste
    "Waste - landfill (t)": 120.0,
    "Waste - recycling (t)": 50.0,
    # default per-flight factor (if user prefers)
    "Flight - per_flight_short": 200.0,
    "Flight - per_flight_long": 1000.0
}

# ---------------------------
# Helper: get emission factor
# ---------------------------
def get_emission_factor_for_entry(scope, activity, category, sub_activity, specific_item):
    """
    Return an emission factor (kg CO2e per unit) for the chosen inputs.
    This function uses DEFAULT_EF as fallback. In a production app you should
    replace / augment this with a lookup against an authoritative EF dataset (e.g. BEIS/DEFRA,
    EPA, IEA or supplier-specific factors).
    """
    # Basic mapping heuristics:
    key_map = {
        "Diesel Generator": "Diesel (L)",
        "Diesel Vehicle": "Diesel (L)",
        "Petrol Generator": "Petrol (L)",
        "Petrol Car": "Car - petrol (km)",
        "Grid Electricity": "Grid Electricity (kWh)",
        "Purchased Renewable Electricity": "Purchased Renewable Electricity (kWh)",
        "LPG Boiler": "LPG (L)",
        "CNG Vehicle": "CNG (kg or m3)",
        "Coal Boiler": "Coal (kg)",
        "Biomass Furnace": "Biomass (kg)",
        "Cement Production": "Cement (t)",
        "Steel Production": "Steel (t)",
        "Refrigerant (HFC/HCFC)": "HFC (kg)",
        "Air Travel": "Air - short haul (kg per passenger-km)"  # default, can be refined
    }
    # Try keys in order
    candidates = []
    if specific_item:
        candidates.append(specific_item)
    if sub_activity:
        candidates.append(sub_activity)
    if category:
        candidates.append(category)
    if activity:
        candidates.append(activity)

    for c in candidates:
        if c in key_map:
            k = key_map[c]
            if k in DEFAULT_EF:
                return float(DEFAULT_EF[k])
    # fallback: try direct key presence
    for k in [f"{sub_activity}", f"{specific_item}"]:
        if k in DEFAULT_EF:
            return float(DEFAULT_EF[k])
    # ultimate fallback: 0
    return 0.0

# ---------------------------
# KPI Calculation (for GHG)
# ---------------------------
def calculate_ghg_kpis():
    df = st.session_state.entries
    out = {"Total (tCO2e)": 0.0, "Scope 1 (tCO2e)": 0.0, "Scope 2 (tCO2e)": 0.0, "Scope 3 (tCO2e)": 0.0}
    if df.empty:
        return out
    # ensure Emissions_kgCO2e column exists; if not, try to compute
    if "Emissions_kgCO2e" not in df.columns or df["Emissions_kgCO2e"].isnull().any():
        # compute where possible
        def compute_row(r):
            try:
                return float(r.get("Quantity", 0.0)) * float(r.get("Emission Factor (kgCO2e/unit)", 0.0))
            except Exception:
                return 0.0
        df["Emissions_kgCO2e"] = df.apply(compute_row, axis=1)
    total_kg = df["Emissions_kgCO2e"].sum()
    out["Total (tCO2e)"] = total_kg / 1000.0
    for s in ["Scope 1","Scope 2","Scope 3"]:
        ssum = df[df["Scope"] == s]["Emissions_kgCO2e"].sum()
        out[f"{s} (tCO2e)"] = ssum / 1000.0
    return out

# ---------------------------
# Render GHG Dashboard (with KPIs)
# ---------------------------
def render_ghg_dashboard(include_data=True, show_chart=True):
    st.subheader("GHG Emissions")

    # show KPIs on both Home and GHG pages
    kpis = calculate_ghg_kpis()
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='kpi'><div class='kpi-value'>{fmt_num(kpis['Total (tCO2e)'])}</div><div class='kpi-label'>Total Emissions (tCO₂e)</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='kpi'><div class='kpi-value'>{fmt_num(kpis['Scope 1 (tCO2e)'])}</div><div class='kpi-label'>Scope 1 (tCO₂e)</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='kpi'><div class='kpi-value'>{fmt_num(kpis['Scope 2 (tCO2e)'])}</div><div class='kpi-label'>Scope 2 (tCO₂e)</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='kpi'><div class='kpi-value'>{fmt_num(kpis['Scope 3 (tCO2e)'])}</div><div class='kpi-label'>Scope 3 (tCO₂e)</div></div>", unsafe_allow_html=True)

    if include_data:
        st.markdown("### Add / Upload GHG Activity")
        col1, col2 = st.columns([2,3])
        with col1:
            scope = st.selectbox("Scope", ["Scope 1","Scope 2","Scope 3"])
            activity = st.selectbox("Activity / Group", list(SCOPE_ACTIVITIES[scope].keys()))
            if scope != "Scope 3":
                sub_activity = st.selectbox("Sub-Activity", SCOPE_ACTIVITIES[scope][activity])
            else:
                # For Scope 3 categories there isn't a fixed sub-activity list in this simple UI
                sub_activity = st.selectbox("Scope 3 Category", list(SCOPE_ACTIVITIES["Scope 3"].keys()))
            specific_item = st.text_input("Specific Item (optional)")
        with col2:
            unit = st.text_input("Unit (e.g., L, kWh, km, tonnes)", value="")
            quantity = st.number_input("Quantity", min_value=0.0, format="%.4f")
            # fetch EF from defaults (heuristic) and allow override
            guessed_ef = get_emission_factor_for_entry(scope, activity, None, sub_activity, specific_item)
            ef = st.number_input("Emission Factor (kg CO₂e per unit)", value=float(guessed_ef), format="%.6f")
            st.markdown("<small style='color:#cfd8dc'>Note: replace emission factors with authoritative national or supplier data (BEIS/DEFRA, EPA, IEA, Climatiq, or supplier-specific).</small>", unsafe_allow_html=True)

        if st.button("Add Entry"):
            emissions_kg = quantity * ef
            new_row = {
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Scope": scope,
                "Activity": activity,
                "Category": sub_activity if scope!="Scope 3" else sub_activity,
                "Sub-Activity": sub_activity if scope!="Scope 3" else "",
                "Specific Item": specific_item,
                "Quantity": quantity,
                "Unit": unit,
                "Emission Factor (kgCO2e/unit)": ef,
                "Emissions_kgCO2e": emissions_kg
            }
            st.session_state.entries = pd.concat([st.session_state.entries, pd.DataFrame([new_row])], ignore_index=True)
            st.success("Entry added.")
            st.experimental_rerun()

        st.markdown("#### Upload file (CSV/Excel) with columns matching the entries DataFrame (Timestamp optional).")
        uploaded = st.file_uploader("Upload CSV/XLS/XLSX", type=["csv","xls","xlsx"])
        if uploaded:
            try:
                if uploaded.name.endswith(".csv"):
                    df_up = pd.read_csv(uploaded)
                else:
                    df_up = pd.read_excel(uploaded)
                # Ensure required columns exist or attempt minimal mapping
                expected_cols = set(["Scope","Activity","Quantity","Unit"])
                if expected_cols.issubset(set(df_up.columns)):
                    # compute emissions if emission factor column exists or if user supplied mapping
                    if "Emission Factor (kgCO2e/unit)" in df_up.columns:
                        df_up["Emissions_kgCO2e"] = df_up["Quantity"] * df_up["Emission Factor (kgCO2e/unit)"]
                    else:
                        df_up["Emission Factor (kgCO2e/unit)"] = df_up.apply(
                            lambda r: get_emission_factor_for_entry(
                                r.get("Scope",""), r.get("Activity",""), None, r.get("Category","") or r.get("Sub-Activity",""), r.get("Specific Item","")
                            ), axis=1
                        )
                        df_up["Emissions_kgCO2e"] = df_up["Quantity"] * df_up["Emission Factor (kgCO2e/unit)"]
                    # add timestamp if missing
                    if "Timestamp" not in df_up.columns:
                        df_up["Timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    # align columns
                    cols_to_keep = ["Timestamp","Scope","Activity","Category","Sub-Activity","Specific Item","Quantity","Unit","Emission Factor (kgCO2e/unit)","Emissions_kgCO2e"]
                    for c in cols_to_keep:
                        if c not in df_up.columns:
                            df_up[c] = ""
                    df_up = df_up[cols_to_keep]
                    st.session_state.entries = pd.concat([st.session_state.entries, df_up], ignore_index=True)
                    st.success("File uploaded and entries added.")
                    st.experimental_rerun()
                else:
                    st.error(f"Uploaded file missing required columns: {expected_cols - set(df_up.columns)}")
            except Exception as e:
                st.error(f"Error reading uploaded file: {e}")

    # show table + download
    if not st.session_state.entries.empty:
        st.markdown("### Emissions Log")
        df_display = st.session_state.entries.copy()
        # format numbers
        df_display["Quantity"] = df_display["Quantity"].apply(lambda x: fmt_num(x) if x!="" else "")
        df_display["Emission Factor (kgCO2e/unit)"] = df_display["Emission Factor (kgCO2e/unit)"].apply(lambda x: fmt_num(x) if x!="" else "")
        df_display["Emissions_kgCO2e"] = df_display["Emissions_kgCO2e"].apply(lambda x: fmt_num(x) if x!="" else "")
        st.dataframe(df_display, use_container_width=True)
        csv = st.session_state.entries.to_csv(index=False).encode("utf-8")
        st.download_button("Download Emissions Log CSV", csv, "emissions_log.csv", "text/csv")

    # optional trend chart by month & scope
    if show_chart and not st.session_state.entries.empty:
        dfc = st.session_state.entries.copy()
        dfc["Timestamp"] = pd.to_datetime(dfc["Timestamp"], errors="coerce")
        dfc = dfc.dropna(subset=["Timestamp"])
        dfc["Month"] = dfc["Timestamp"].dt.strftime("%b")
        # order months Apr->Mar (financial cycle)
        month_order = months
        dfc["Month"] = pd.Categorical(dfc["Month"], categories=month_order, ordered=True)
        trend = dfc.groupby(["Month","Scope"])["Emissions_kgCO2e"].sum().reset_index()
        if not trend.empty:
            trend["Emissions_tCO2e"] = trend["Emissions_kgCO2e"] / 1000.0
            fig = px.bar(trend, x="Month", y="Emissions_tCO2e", color="Scope", barmode="stack", template="plotly_dark")
            fig.update_layout(paper_bgcolor="#0d1117", plot_bgcolor="#0d1117", yaxis_title="tCO₂e")
            st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# Energy Dashboard (keeps previous behavior)
# ---------------------------
def render_energy_dashboard(include_input=True, show_chart=True):
    st.subheader("Energy")
    df = st.session_state.entries.copy()
    # compute energy-related rows (if present) using emission factors if unit is kWh or known fuel
    energy_rows = []
    for _, r in df.iterrows():
        sub = str(r.get("Sub-Activity","")) or str(r.get("Category",""))
        qty = r.get("Quantity", 0.0)
        unit = r.get("Unit","")
        ef = r.get("Emission Factor (kgCO2e/unit)", 0.0) or 0.0
        # if unit is kWh -> treat as electricity
        energy_kwh = 0.0
        if unit and "kwh" in unit.lower():
            energy_kwh = float(qty)
        elif sub in ["Diesel Generator","Diesel Vehicle"]:
            # approximate calorific conversion example (not exact) used earlier / placeholder
            # For simplicity, we won't convert volume to kWh here unless the user provides kWh
            energy_kwh = 0.0
        energy_rows.append({"Scope": r.get("Scope"), "Source": sub, "Energy_kWh": energy_kwh, "CO2e_kg": qty * ef})
    energy_df = pd.DataFrame(energy_rows)
    if not energy_df.empty:
        total_kwh = energy_df["Energy_kWh"].sum()
        total_co2kg = energy_df["CO2e_kg"].sum()
    else:
        total_kwh = 0.0
        total_co2kg = 0.0

    c1,c2 = st.columns(2)
    c1.markdown(f"<div class='kpi'><div class='kpi-value'>{int(total_kwh):,}</div><div class='kpi-label'>Estimated Energy (kWh)</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='kpi'><div class='kpi-value'>{fmt_num(total_co2kg/1000.0)}</div><div class='kpi-label'>Energy CO₂e (tCO₂e)</div></div>", unsafe_allow_html=True)

    if show_chart and not energy_df.empty and energy_df["Energy_kWh"].sum() > 0:
        monthly = energy_df.groupby("Source")["Energy_kWh"].sum().reset_index()
        fig = px.bar(monthly, x="Source", y="Energy_kWh", title="Energy by Source (kWh)", template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

    if include_input:
        st.subheader("Add Renewable Energy (monthlyized from annual input)")
        num_entries = st.number_input("Number of renewable energy entries", min_value=1, max_value=12, value=1)
        renewable_list = []
        for i in range(int(num_entries)):
            col1,col2,col3 = st.columns([2,3,3])
            with col1:
                src = st.selectbox(f"Source {i+1}", ["Solar","Wind","Biogas","Purchased Green Energy"], key=f"res_src_{i}")
            with col2:
                loc = st.text_input(f"Location {i+1}", "", key=f"res_loc_{i}")
            with col3:
                annual = st.number_input(f"Annual Energy (kWh) {i+1}", min_value=0.0, key=f"res_ann_{i}")
            monthly = annual / 12.0
            for m in months:
                renewable_list.append({"Source": src, "Location": loc, "Month": m, "Energy_kWh": monthly, "CO2e_kg": 0.0, "Type": "Renewable"})
        if renewable_list and st.button("Add Renewable Energy Entries"):
            newdf = pd.DataFrame(renewable_list)
            st.session_state.renewable_entries = pd.concat([st.session_state.renewable_entries, newdf], ignore_index=True)
            st.success("Renewable entries added.")
            st.experimental_rerun()

# ---------------------------
# SDG Dashboard (no sliders)
# ---------------------------
def render_sdg_dashboard():
    st.title("Sustainable Development Goals (SDGs)")
    st.subheader("Company Engagement by SDG (set engagement % below)")
    # Instead of sliders (user requested no slider), we'll show numeric inputs for engagement %
    cols = st.columns(4)
    idx = 0
    for sdg_num, sdg_name in enumerate([
        "No Poverty","Zero Hunger","Good Health & Wellbeing","Quality Education","Gender Equality",
        "Clean Water & Sanitation","Affordable & Clean Energy","Decent Work & Economic Growth","Industry, Innovation & Infrastructure",
        "Reduced Inequalities","Sustainable Cities & Communities","Responsible Consumption & Production","Climate Action","Life Below Water",
        "Life on Land","Peace, Justice & Strong Institutions","Partnerships for the Goals"
    ], start=1):
        col = cols[(idx % 4)]
        current = st.session_state.sdg_engagement.get(sdg_num, 0)
        val = col.number_input(f"SDG {sdg_num}: {sdg_name}", min_value=0, max_value=100, value=current, key=f"sdg_input_{sdg_num}")
        st.session_state.sdg_engagement[sdg_num] = int(val)
        # show a small card
        col.markdown(
            f"<div class='sdg-card' style='background:#333'>{'<div class=\"sdg-number\">SDG '+str(sdg_num)+'</div>'}<div class='sdg-name'>{sdg_name}</div><div class='sdg-percent'>Engagement: {int(val)}%</div></div>",
            unsafe_allow_html=True
        )
        idx += 1
        if (idx % 4) == 0:
            cols = st.columns(4)

# ---------------------------
# Render Pages
# ---------------------------
if st.session_state.page == "Home":
    st.title("EinTrust Sustainability Dashboard")
    # Show KPIs only (compact)
    render_ghg_dashboard(include_data=False, show_chart=False)
elif st.session_state.page == "GHG":
    render_ghg_dashboard(include_data=True, show_chart=True)
elif st.session_state.page == "Energy":
    render_energy_dashboard(include_input=True, show_chart=True)
elif st.session_state.page == "SDG":
    render_sdg_dashboard()
else:
    st.subheader(f"{st.session_state.page} section")
    st.info("This section is under development. Please select other pages from the sidebar.")
