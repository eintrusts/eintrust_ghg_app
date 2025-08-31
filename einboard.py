import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ---------------------------
# Config & CSS
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
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Utilities
# ---------------------------
months = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]

SCOPE_COLORS = {"Scope 1": "#81c784", "Scope 2": "#4db6ac", "Scope 3": "#aed581"}
ENERGY_COLORS = {"Fossil": "#f39c12", "Renewable": "#2ecc71"}

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
# Session State Initialization
# ---------------------------
if "ghg_entries" not in st.session_state:
    st.session_state.ghg_entries = pd.DataFrame(columns=["Scope","Activity","Sub-Activity","Quantity","Unit","Month"])
if "energy_entries" not in st.session_state:
    st.session_state.energy_entries = pd.DataFrame(columns=["Source","Type","Energy_kWh","CO2e_kg","Month"])
if "water_entries" not in st.session_state:
    st.session_state.water_entries = pd.DataFrame(columns=[
        "Location","Source","Month","Quantity_m3","Cost_INR",
        "Rainwater_Harvested_m3","Water_Recycled_m3","Treatment_Before_Discharge","STP_ETP_Capacity_kL_day"
    ])

# ---------------------------
# Sidebar Navigation
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

# ---------------------------
# GHG Dashboard + Input Form
# ---------------------------
def render_ghg_dashboard():
    st.subheader("GHG Emissions Dashboard")
    # --- Input Form ---
    with st.expander("Add GHG Entry"):
        with st.form("ghg_form"):
            scope = st.selectbox("Scope", ["Scope 1","Scope 2","Scope 3"])
            activity = st.text_input("Activity (e.g., Stationary Combustion)")
            sub_activity = st.text_input("Sub-Activity (e.g., Diesel Generator)")
            quantity = st.number_input("Quantity", min_value=0.0, format="%.2f")
            unit = st.text_input("Unit (e.g., tCO2e)")
            month = st.selectbox("Month", months)
            submit = st.form_submit_button("Add Entry")
            if submit:
                st.session_state.ghg_entries.loc[len(st.session_state.ghg_entries)] = [scope, activity, sub_activity, quantity, unit, month]
                st.success("GHG entry added successfully!")

    # --- KPIs ---
    df = st.session_state.ghg_entries
    total = df["Quantity"].sum() if not df.empty else 0
    scope1 = df[df["Scope"]=="Scope 1"]["Quantity"].sum() if not df.empty else 0
    scope2 = df[df["Scope"]=="Scope 2"]["Quantity"].sum() if not df.empty else 0
    scope3 = df[df["Scope"]=="Scope 3"]["Quantity"].sum() if not df.empty else 0
    c1, c2, c3, c4 = st.columns(4)
    for col, label, value, color in zip(
        [c1, c2, c3, c4],
        ["Total", "Scope 1", "Scope 2", "Scope 3"],
        [total, scope1, scope2, scope3],
        ["#ffffff", SCOPE_COLORS["Scope 1"], SCOPE_COLORS["Scope 2"], SCOPE_COLORS["Scope 3"]]
    ):
        col.markdown(f"""
        <div class='kpi'>
            <div class='kpi-value' style='color:{color}'>{format_indian(value)}</div>
            <div class='kpi-unit'>tCO2e</div>
            <div class='kpi-label'>{label}</div>
        </div>
        """, unsafe_allow_html=True)

    # --- Chart ---
    if not df.empty:
        df["Month"] = pd.Categorical(df["Month"], categories=months, ordered=True)
        monthly = df.groupby(["Month","Scope"])["Quantity"].sum().reset_index()
        st.subheader("Monthly GHG Emissions")
        fig = px.bar(monthly, x="Month", y="Quantity", color="Scope", barmode="stack", color_discrete_map=SCOPE_COLORS)
        st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# Energy Dashboard + Input Form
# ---------------------------
def render_energy_dashboard():
    st.subheader("Energy Dashboard")
    # --- Input Form ---
    with st.expander("Add Energy Entry"):
        with st.form("energy_form"):
            source = st.text_input("Energy Source (e.g., Grid Electricity, Solar)")
            type_ = st.selectbox("Type", ["Fossil","Renewable"])
            energy_kwh = st.number_input("Energy Consumed (kWh)", min_value=0.0, format="%.2f")
            co2e_kg = st.number_input("CO2e (kg)", min_value=0.0, format="%.2f")
            month = st.selectbox("Month", months)
            submit = st.form_submit_button("Add Entry")
            if submit:
                st.session_state.energy_entries.loc[len(st.session_state.energy_entries)] = [source, type_, energy_kwh, co2e_kg, month]
                st.success("Energy entry added successfully!")

    # --- KPIs ---
    df = st.session_state.energy_entries
    total = df["Energy_kWh"].sum() if not df.empty else 0
    fossil = df[df["Type"]=="Fossil"]["Energy_kWh"].sum() if not df.empty else 0
    renewable = df[df["Type"]=="Renewable"]["Energy_kWh"].sum() if not df.empty else 0
    c1, c2, c3 = st.columns(3)
    for col, label, value, color in zip(
        [c1,c2,c3],
        ["Total Energy","Fossil Energy","Renewable Energy"],
        [total, fossil, renewable],
        ["#ffffff", ENERGY_COLORS["Fossil"], ENERGY_COLORS["Renewable"]]
    ):
        col.markdown(f"""
        <div class='kpi'>
            <div class='kpi-value' style='color:{color}'>{value:,.0f}</div>
            <div class='kpi-unit'>kWh</div>
            <div class='kpi-label'>{label}</div>
        </div>
        """, unsafe_allow_html=True)

    # --- Chart ---
    if not df.empty:
        df["Month"] = pd.Categorical(df["Month"], categories=months, ordered=True)
        monthly = df.groupby(["Month","Type"])["Energy_kWh"].sum().reset_index()
        st.subheader("Monthly Energy Consumption (kWh)")
        fig = px.bar(monthly, x="Month", y="Energy_kWh", color="Type", barmode="stack", color_discrete_map=ENERGY_COLORS)
        st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# Water Dashboard + Input Form
# ---------------------------
def render_water_dashboard():
    st.subheader("Water Dashboard")
    # --- Input Form ---
    with st.expander("Add Water Entry"):
        with st.form("water_form"):
            location = st.text_input("Location")
            source = st.text_input("Water Source (e.g., Municipal, Borewell)")
            month = st.selectbox("Month", months)
            quantity = st.number_input("Quantity (m³)", min_value=0.0, format="%.2f")
            cost = st.number_input("Cost (INR)", min_value=0.0, format="%.2f")
            rainwater = st.number_input("Rainwater Harvested (m³)", min_value=0.0, format="%.2f")
            recycled = st.number_input("Water Recycled (m³)", min_value=0.0, format="%.2f")
            treatment = st.selectbox("Treatment Before Discharge?", ["Yes","No"])
            stp_capacity = st.number_input("STP/ETP Capacity (kL/day)", min_value=0.0, format="%.2f")
            submit = st.form_submit_button("Add Entry")
            if submit:
                st.session_state.water_entries.loc[len(st.session_state.water_entries)] = [
                    location, source, month, quantity, cost, rainwater, recycled, treatment, stp_capacity
                ]
                st.success("Water entry added successfully!")

    # --- KPIs ---
    df = st.session_state.water_entries
    total_water = df["Quantity_m3"].sum() if not df.empty else 0
    total_cost = df["Cost_INR"].sum() if not df.empty else 0
    recycled_water = df["Water_Recycled_m3"].sum() if not df.empty else 0
    rainwater = df["Rainwater_Harvested_m3"].sum() if not df.empty else 0
    treatment_count = df[df["Treatment_Before_Discharge"]=="Yes"].shape[0] if not df.empty else 0
    avg_stp = df["STP_ETP_Capacity_kL_day"].mean() if not df.empty else 0
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Total Water (m³)", f"{total_water:,.0f}")
    c2.metric("Total Cost (INR)", f"₹ {total_cost:,.0f}")
    c3.metric("Recycled Water (m³)", f"{recycled_water:,.0f}")
    c4.metric("Rainwater Harvested (m³)", f"{rainwater:,.0f}")
    c5.metric("Treatment Locations", f"{treatment_count}")
    st.metric("Avg STP/ETP Capacity (kL/day)", f"{avg_stp:,.1f}")

    # --- Charts ---
    if not df.empty:
        df["Month"] = pd.Categorical(df["Month"], categories=months, ordered=True)
        monthly = df.groupby(["Month","Source"])["Quantity_m3"].sum().reset_index()
        st.subheader("Monthly Water Usage by Source (m³)")
        fig = px.line(monthly, x="Month", y="Quantity_m3", color="Source", markers=True)
        st.plotly_chart(fig, use_container_width=True)

        monthly_adv = df.groupby("Month")[["Rainwater_Harvested_m3","Water_Recycled_m3"]].sum().reset_index()
        st.subheader("Monthly Rainwater & Recycled Water (m³)")
        fig2 = px.line(monthly_adv, x="Month", y=["Rainwater_Harvested_m3","Water_Recycled_m3"], markers=True)
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
