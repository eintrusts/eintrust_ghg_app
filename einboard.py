import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ---------------------------
# Config & Dark Theme CSS
# ---------------------------
st.set_page_config(page_title="EinTrust Sustainability Dashboard", page_icon="🌍", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }
.stApp { background-color: #0d1117; color: #e6edf3; }

.kpi {
    background: linear-gradient(145deg, #12131a, #1a1b22);
    padding: 20px; border-radius: 12px; text-align: center;
    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    margin-bottom: 10px; min-height: 120px;
    display: flex; flex-direction: column; justify-content: center; align-items: center;
    transition: transform 0.2s, box-shadow 0.2s;
}
.kpi:hover { transform: scale(1.05); box-shadow: 0 8px 20px rgba(0,0,0,0.6); }
.kpi-value { font-size: 28px; font-weight: 700; color: #ffffff; margin-bottom: 5px; }
.kpi-unit { font-size: 16px; font-weight: 500; color: #cfd8dc; margin-bottom: 5px; }
.kpi-label { font-size: 14px; color: #cfd8dc; letter-spacing: 0.5px; }
.stDataFrame { color: #e6edf3; font-family: 'Roboto', sans-serif; }
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
        all: unset; cursor: pointer; padding: 0.4rem; text-align: left;
        border-radius: 0.3rem; margin-bottom: 0.2rem;
        background-color: {'forestgreen' if active else '#12131a'};
        color: {'white' if active else '#e6edf3'};
        font-size: 16px;
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

    social_exp = st.expander("Social", expanded=False)
    with social_exp:
        sidebar_button("Employee")
        sidebar_button("Health & Safety")
        sidebar_button("CSR")

    gov_exp = st.expander("Governance", expanded=False)
    with gov_exp:
        sidebar_button("Board")
        sidebar_button("Policies")
        sidebar_button("Compliance")
        sidebar_button("Risk Management")

# ---------------------------
# Initialize Data
# ---------------------------
if "entries" not in st.session_state:
    st.session_state.entries = pd.DataFrame(columns=["Scope","Activity","Sub-Activity","Specific Item","Quantity","Unit"])
if "renewable_entries" not in st.session_state:
    st.session_state.renewable_entries = pd.DataFrame(columns=["Source","Location","Month","Energy_kWh","CO2e_kg","Type"])
if "water_data" not in st.session_state:
    st.session_state.water_data = pd.DataFrame(columns=["Location","Source","Month","Quantity_m3","Cost_INR"])
if "advanced_water_data" not in st.session_state:
    st.session_state.advanced_water_data = pd.DataFrame(columns=[
        "Location","Month","Rainwater_Harvested_m3","Water_Recycled_m3",
        "Treatment_Before_Discharge","STP_ETP_Capacity_kL_day"
    ])

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

SCOPE_COLORS = {"Scope 1": "#81c784", "Scope 2": "#4db6ac", "Scope 3": "#aed581"}
ENERGY_COLORS = {"Fossil": "#f39c12", "Renewable": "#2ecc71"}

# ---------------------------
# GHG Dashboard
# ---------------------------
def calculate_kpis():
    df = st.session_state.entries
    summary = {"Scope 1": 0.0, "Scope 2": 0.0, "Scope 3": 0.0, "Total Quantity": 0.0, "Unit": "tCO₂e"}
    if not df.empty:
        for scope in ["Scope 1","Scope 2","Scope 3"]:
            summary[scope] = df[df["Scope"]==scope]["Quantity"].sum()
        summary["Total Quantity"] = df["Quantity"].sum()
    return summary

def render_ghg_dashboard(include_data=True, show_chart=True):
    st.subheader("GHG Emissions")
    kpis = calculate_kpis()
    c1, c2, c3, c4 = st.columns(4)
    for col, label, value, color in zip(
        [c1, c2, c3, c4], 
        ["Total Quantity", "Scope 1", "Scope 2", "Scope 3"],
        [kpis['Total Quantity'], kpis['Scope 1'], kpis['Scope 2'], kpis['Scope 3']],
        ["#ffffff", SCOPE_COLORS['Scope 1'], SCOPE_COLORS['Scope 2'], SCOPE_COLORS['Scope 3']]
    ):
        col.markdown(f"""
        <div class='kpi'>
            <div class='kpi-value' style='color:{color}'>{format_indian(value)}</div>
            <div class='kpi-unit'>{kpis['Unit']}</div>
            <div class='kpi-label'>{label.lower()}</div>
        </div>
        """, unsafe_allow_html=True)

    if show_chart and not st.session_state.entries.empty:
        df = st.session_state.entries.copy()
        if "Month" not in df.columns:
            df["Month"] = np.random.choice(months, len(df))
        df["Month"] = pd.Categorical(df["Month"], categories=months, ordered=True)
        monthly_trend = df.groupby(["Month","Scope"])["Quantity"].sum().reset_index()
        st.subheader("Monthly GHG Emissions")
        fig = px.bar(monthly_trend, x="Month", y="Quantity", color="Scope", barmode="stack",
                     color_discrete_map=SCOPE_COLORS)
        st.plotly_chart(fig, use_container_width=True)

    if include_data:
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

        unit = units_dict.get(sub_activity, "Number of flights" if sub_activity=="Air Travel" else "km / kg / tonnes")
        quantity = st.number_input(f"Enter quantity ({unit})", min_value=0.0, format="%.2f")
        uploaded_file = st.file_uploader("Upload CSV/XLS/XLSX/PDF for cross verification (optional)", type=["csv","xls","xlsx","pdf"])

        if st.button("Add Entry"):
            new_entry = {
                "Scope": scope,
                "Activity": activity,
                "Sub-Activity": sub_activity,
                "Specific Item": specific_item if specific_item else "",
                "Quantity": quantity,
                "Unit": unit
            }
            st.session_state.entries = pd.concat([st.session_state.entries, pd.DataFrame([new_entry])], ignore_index=True)
            st.success("GHG entry added successfully!")
            st.experimental_rerun()

        if not st.session_state.entries.empty:
            st.subheader("All entries")
            display_df = st.session_state.entries.copy()
            display_df["Quantity"] = display_df["Quantity"].apply(lambda x: format_indian(x))
            st.dataframe(display_df)
            csv = display_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download all entries as CSV", csv, "ghg_entries.csv", "text/csv")

# ---------------------------
# Energy Dashboard
# ---------------------------
def render_energy_dashboard(include_input=True, show_chart=True):
    st.subheader("Energy")
    df = st.session_state.entries
    calorific_values = {"Diesel": 35.8,"Petrol": 34.2,"LPG":46.1,"CNG":48,"Coal":24.0,"Electricity":0.0}
    
    # -----------------------------
    # Energy KPI cards
    # -----------------------------
    if not df.empty:
        energy_total = df[df['Unit'].isin(["kWh","Liters","kg"])]['Quantity'].sum()
    else:
        energy_total = 0

    c1, c2 = st.columns(2)
    c1.markdown(f"<div class='kpi'><div class='kpi-value'>{format_indian(energy_total)}</div><div class='kpi-unit'>kWh / L / kg</div><div class='kpi-label'>Total Energy</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='kpi'><div class='kpi-value'>-</div><div class='kpi-unit'>-</div><div class='kpi-label'>Renewable / Fossil Split</div></div>", unsafe_allow_html=True)

# ---------------------------
# Water Dashboard
# ---------------------------
def render_water_dashboard():
    st.title("💧 Water Consumption & Management Dashboard (Apr→Mar)")

    water_df = st.session_state.water_data.copy()
    adv_df = st.session_state.advanced_water_data.copy()

    # -----------------------------
    # KPI Cards
    # -----------------------------
    total_water = water_df["Quantity_m3"].sum()
    total_cost = water_df["Cost_INR"].sum()
    recycled_water = adv_df["Water_Recycled_m3"].sum()
    rainwater = adv_df["Rainwater_Harvested_m3"].sum()
    treatment_coverage = adv_df["Treatment_Before_Discharge"].value_counts().get("Yes",0)
    avg_stp_capacity = adv_df["STP_ETP_Capacity_kL_day"].mean() if not adv_df.empty else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Water Used (m³)", f"{total_water:,.0f}")
    col2.metric("Estimated Cost (INR)", f"₹ {total_cost:,.0f}")
    col3.metric("Recycled Water (m³)", f"{recycled_water:,.0f}")
    col4.metric("Rainwater Harvested (m³)", f"{rainwater:,.0f}")
    col5.metric("Locations with Treatment", f"{treatment_coverage}")
    st.metric("Average STP/ETP Capacity (kL/day)", f"{avg_stp_capacity:,.1f}")

    # -----------------------------
    # Monthly Trends
    # -----------------------------
    if not water_df.empty:
        monthly_trend = water_df.groupby(["Month","Source"]).sum().reset_index()
        monthly_trend["Month"] = pd.Categorical(monthly_trend["Month"], categories=months, ordered=True)
        st.subheader("Monthly Water Usage (m³) by Source")
        fig1 = px.line(monthly_trend, x="Month", y="Quantity_m3", color="Source", markers=True,
                       labels={"Quantity_m3":"Water (m³)"})
        st.plotly_chart(fig1, use_container_width=True)

    if not adv_df.empty:
        adv_monthly = adv_df.groupby("Month")[["Rainwater_Harvested_m3","Water_Recycled_m3"]].sum().reset_index()
        adv_monthly["Month"] = pd.Categorical(adv_monthly["Month"], categories=months, ordered=True)
        st.subheader("Monthly Rainwater & Recycled Water (m³)")
        fig2 = px.line(adv_monthly, x="Month", y=["Rainwater_Harvested_m3","Water_Recycled_m3"],
                       markers=True, labels={"value":"Water (m³)","variable":"Type"})
        st.plotly_chart(fig2, use_container_width=True)

    # -----------------------------
    # Location-wise analysis
    # -----------------------------
    if not water_df.empty:
        location_trend = water_df.groupby(["Location","Source"]).sum().reset_index()
        st.subheader("Water Usage by Location")
        fig3 = px.bar(location_trend, x="Location", y="Quantity_m3", color="Source", barmode="stack")
        st.plotly_chart(fig3, use_container_width=True)

    if not adv_df.empty:
        st.subheader("STP/ETP Capacity by Location (kL/day)")
        stp_trend = adv_df.groupby("Location")["STP_ETP_Capacity_kL_day"].sum().reset_index()
        fig4 = px.bar(stp_trend, x="Location", y="STP_ETP_Capacity_kL_day", labels={"STP_ETP_Capacity_kL_day":"Capacity (kL/day)"})
        st.plotly_chart(fig4, use_container_width=True)

    # -----------------------------
    # Data Entry Section
    # -----------------------------
    st.subheader("Add Water Data Entry")

    with st.expander("Basic Water Entry"):
        col1, col2, col3, col4 = st.columns(4)
        with col1: location = st.text_input("Location", key="water_loc")
        with col2: source = st.selectbox("Source", ["Municipal","Groundwater","Borewell","Other"], key="water_src")
        with col3: month = st.selectbox("Month", months, key="water_month")
        with col4: quantity = st.number_input("Quantity (m³)", min_value=0.0, format="%.2f", key="water_qty")
        cost = st.number_input("Cost (INR)", min_value=0.0, format="%.2f", key="water_cost")
        if st.button("Add Water Entry"):
            new_entry = {"Location": location, "Source": source, "Month": month,
                         "Quantity_m3": quantity, "Cost_INR": cost}
            st.session_state.water_data = pd.concat([st.session_state.water_data, pd.DataFrame([new_entry])], ignore_index=True)
            st.success("Water entry added successfully!")
            st.experimental_rerun()

    with st.expander("Advanced Water Details"):
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1: adv_location = st.text_input("Location", key="adv_loc")
        with col2: adv_month = st.selectbox("Month", months, key="adv_month")
        with col3: rainwater = st.number_input("Rainwater Harvested (m³)", min_value=0.0, key="adv_rain")
        with col4: recycled = st.number_input("Water Recycled (m³)", min_value=0.0, key="adv_recycled")
        with col5: treatment = st.selectbox("Treatment Before Discharge", ["Yes","No"], key="adv_treatment")
        stp_capacity = st.number_input("STP/ETP Capacity (kL/day)", min_value=0.0, key="adv_stp")
        if st.button("Add Advanced Water Entry"):
            adv_entry = {"Location": adv_location, "Month": adv_month,
                         "Rainwater_Harvested_m3": rainwater,
                         "Water_Recycled_m3": recycled,
                         "Treatment_Before_Discharge": treatment,
                         "STP_ETP_Capacity_kL_day": stp_capacity}
            st.session_state.advanced_water_data = pd.concat([st.session_state.advanced_water_data, pd.DataFrame([adv_entry])], ignore_index=True)
            st.success("Advanced water entry added successfully!")
            st.experimental_rerun()

    # -----------------------------
    # File Upload
    # -----------------------------
    st.subheader("Bulk Upload Water Data")
    uploaded_file = st.file_uploader("Upload CSV/XLSX for water data", type=["csv","xlsx"])
    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".csv"):
                df_uploaded = pd.read_csv(uploaded_file)
            else:
                df_uploaded = pd.read_excel(uploaded_file)
            st.session_state.water_data = pd.concat([st.session_state.water_data, df_uploaded], ignore_index=True)
            st.success(f"{len(df_uploaded)} water records uploaded successfully!")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Failed to upload: {e}")

    # -----------------------------
    # Download Entries
    # -----------------------------
    if not st.session_state.water_data.empty:
        csv = st.session_state.water_data.to_csv(index=False).encode('utf-8')
        st.download_button("Download Water Data CSV", csv, "water_data.csv", "text/csv")
    if not st.session_state.advanced_water_data.empty:
        csv_adv = st.session_state.advanced_water_data.to_csv(index=False).encode('utf-8')
        st.download_button("Download Advanced Water Data CSV", csv_adv, "advanced_water_data.csv", "text/csv")

# ---------------------------
# Page Routing
# ---------------------------
if st.session_state.page == "Home":
    st.title("🌍 EinTrust Sustainability Dashboard")
    st.write("Use the sidebar to navigate between GHG, Energy, Water, and other dashboards.")
elif st.session_state.page == "GHG":
    render_ghg_dashboard()
elif st.session_state.page == "Energy":
    render_energy_dashboard()
elif st.session_state.page == "Water":
    render_water_dashboard()
else:
    st.info("Page under development")
