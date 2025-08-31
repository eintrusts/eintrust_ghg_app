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
.kpi { background: linear-gradient(145deg, #12131a, #1a1b22); padding: 20px; border-radius: 12px;
      text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.5); margin-bottom: 10px;
      min-height: 120px; display: flex; flex-direction: column; justify-content: center; align-items: center;
      transition: transform 0.2s, box-shadow 0.2s; }
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

months = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]
SCOPE_COLORS = {"Scope 1": "#81c784", "Scope 2": "#4db6ac", "Scope 3": "#aed581"}
ENERGY_COLORS = {"Fossil": "#f39c12", "Renewable": "#2ecc71"}

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

def render_ghg_dashboard():
    st.subheader("GHG Emissions Dashboard")
    kpis = calculate_kpis()
    c1,c2,c3,c4 = st.columns(4)
    for col,label,value,color in zip([c1,c2,c3,c4],
                                     ["Total Quantity","Scope 1","Scope 2","Scope 3"],
                                     [kpis['Total Quantity'],kpis['Scope 1'],kpis['Scope 2'],kpis['Scope 3']],
                                     ["#ffffff",SCOPE_COLORS['Scope 1'],SCOPE_COLORS['Scope 2'],SCOPE_COLORS['Scope 3']]):
        col.markdown(f"""
        <div class='kpi'>
            <div class='kpi-value' style='color:{color}'>{format_indian(value)}</div>
            <div class='kpi-unit'>{kpis['Unit']}</div>
            <div class='kpi-label'>{label.lower()}</div>
        </div>
        """, unsafe_allow_html=True)

    # Monthly Trends
    if not st.session_state.entries.empty:
        df = st.session_state.entries.copy()
        df["Month"] = pd.Categorical(df.get("Month", months[0]), categories=months, ordered=True)
        monthly_trend = df.groupby(["Month","Scope"])["Quantity"].sum().reset_index()
        st.subheader("Monthly GHG Emissions")
        fig = px.bar(monthly_trend, x="Month", y="Quantity", color="Scope", barmode="stack",
                     color_discrete_map=SCOPE_COLORS)
        st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# Energy Dashboard
# ---------------------------
def render_energy_dashboard():
    st.subheader("Energy Dashboard")
    df = st.session_state.entries.copy()
    df_renew = st.session_state.renewable_entries.copy()

    # Add Energy_kWh column if missing
    if "Energy_kWh" not in df.columns:
        df["Energy_kWh"] = 0
        df["Type"] = "Fossil"
        df.rename(columns={"Sub-Activity":"Fuel"}, inplace=True)
    if not df_renew.empty and "Energy_kWh" not in df_renew.columns:
        df_renew["Energy_kWh"] = 0

    all_energy = pd.concat([df, df_renew], ignore_index=True) if not df_renew.empty else df.copy()

    # Monthly Trends
    if not all_energy.empty and "Energy_kWh" in all_energy.columns and all_energy["Energy_kWh"].sum() > 0:
        all_energy["Month"] = pd.Categorical(all_energy.get("Month", months[0]), categories=months, ordered=True)
        monthly_trend = all_energy.groupby(["Month","Type"])["Energy_kWh"].sum().reset_index()
        st.subheader("Monthly Energy Consumption")
        fig = px.bar(monthly_trend, x="Month", y="Energy_kWh", color="Type", barmode="stack",
                     color_discrete_map=ENERGY_COLORS)
        st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# Water Dashboard
# ---------------------------
def render_water_dashboard():
    st.subheader("💧 Water Dashboard")
    water_df = st.session_state.water_data.copy()
    adv_df = st.session_state.advanced_water_data.copy()

    # KPI cards
    total_water = water_df["Quantity_m3"].sum()
    total_cost = water_df["Cost_INR"].sum()
    recycled_water = adv_df["Water_Recycled_m3"].sum()
    rainwater = adv_df["Rainwater_Harvested_m3"].sum()
    treatment_coverage = adv_df["Treatment_Before_Discharge"].value_counts().get("Yes",0)
    avg_stp_capacity = adv_df["STP_ETP_Capacity_kL_day"].mean() if not adv_df.empty else 0

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Total Water Used (m³)", f"{total_water:,.0f}")
    c2.metric("Estimated Cost (INR)", f"₹ {total_cost:,.0f}")
    c3.metric("Recycled Water (m³)", f"{recycled_water:,.0f}")
    c4.metric("Rainwater Harvested (m³)", f"{rainwater:,.0f}")
    c5.metric("Locations with Treatment", f"{treatment_coverage}")
    st.metric("Average STP/ETP Capacity (kL/day)", f"{avg_stp_capacity:,.1f}")

    # Monthly trends
    if not water_df.empty:
        monthly_trend = water_df.groupby(["Month","Source"])["Quantity_m3"].sum().reset_index()
        monthly_trend["Month"] = pd.Categorical(monthly_trend["Month"], categories=months, ordered=True)
        st.subheader("Monthly Water Usage by Source")
        fig1 = px.line(monthly_trend, x="Month", y="Quantity_m3", color="Source", markers=True,
                       labels={"Quantity_m3":"Water (m³)"})
        st.plotly_chart(fig1, use_container_width=True)
    if not adv_df.empty:
        adv_monthly = adv_df.groupby("Month")[["Rainwater_Harvested_m3","Water_Recycled_m3"]].sum().reset_index()
        adv_monthly["Month"] = pd.Categorical(adv_monthly["Month"], categories=months, ordered=True)
        st.subheader("Monthly Rainwater & Recycled Water")
        fig2 = px.line(adv_monthly, x="Month", y=["Rainwater_Harvested_m3","Water_Recycled_m3"],
                       markers=True, labels={"value":"Water (m³)","variable":"Type"})
        st.plotly_chart(fig2, use_container_width=True)

# ---------------------------
# Render Pages
# ---------------------------
if st.session_state.page == "Home":
    st.title("EinTrust Sustainability Dashboard")
    render_ghg_dashboard()
    render_energy_dashboard()
    render_water_dashboard()
elif st.session_state.page == "GHG":
    render_ghg_dashboard()
elif st.session_state.page == "Energy":
    render_energy_dashboard()
elif st.session_state.page == "Water":
    render_water_dashboard()
else:
    st.subheader(f"{st.session_state.page} section")
    st.info("This section is under development. Please select other pages from sidebar.")
