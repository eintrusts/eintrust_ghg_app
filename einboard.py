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

months = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]
SCOPE_COLORS = {"Scope 1": "#81c784", "Scope 2": "#4db6ac", "Scope 3": "#aed581"}
ENERGY_COLORS = {"Fossil": "#f39c12", "Renewable": "#2ecc71"}
WATER_COLORS = {"Municipal": "#3498db", "Groundwater": "#9b59b6", "Recycled": "#2ecc71", "Other": "#e74c3c"}

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
if "ghg_entries" not in st.session_state:
    st.session_state.ghg_entries = pd.DataFrame(columns=["Scope","Activity","Sub-Activity","Specific Item","Quantity","Unit","Month"])
if "energy_entries" not in st.session_state:
    st.session_state.energy_entries = pd.DataFrame(columns=["Source","Location","Month","Energy_kWh","CO2e_kg","Type"])
if "water_entries" not in st.session_state:
    st.session_state.water_entries = pd.DataFrame(columns=[
        "Location","Source","Month","Quantity_m3","Cost_INR",
        "Rainwater_Harvested_m3","Water_Recycled_m3","Treatment_Before_Discharge","STP_ETP_Capacity_kL_day"
    ])

# ---------------------------
# GHG Dashboard
# ---------------------------
def render_ghg_dashboard():
    st.subheader("GHG Emissions")
    df = st.session_state.ghg_entries
    total = df["Quantity"].sum() if not df.empty else 0
    scope1 = df[df["Scope"]=="Scope 1"]["Quantity"].sum() if not df.empty else 0
    scope2 = df[df["Scope"]=="Scope 2"]["Quantity"].sum() if not df.empty else 0
    scope3 = df[df["Scope"]=="Scope 3"]["Quantity"].sum() if not df.empty else 0
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.markdown(f"<div class='kpi'><div class='kpi-value'>{format_indian(total)}</div><div class='kpi-unit'>tCO₂e</div><div class='kpi-label'>Total</div></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{SCOPE_COLORS['Scope 1']}'>{format_indian(scope1)}</div><div class='kpi-unit'>tCO₂e</div><div class='kpi-label'>Scope 1</div></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{SCOPE_COLORS['Scope 2']}'>{format_indian(scope2)}</div><div class='kpi-unit'>tCO₂e</div><div class='kpi-label'>Scope 2</div></div>", unsafe_allow_html=True)
    with c4: st.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{SCOPE_COLORS['Scope 3']}'>{format_indian(scope3)}</div><div class='kpi-unit'>tCO₂e</div><div class='kpi-label'>Scope 3</div></div>", unsafe_allow_html=True)

    if not df.empty:
        df["Month"] = pd.Categorical(df["Month"], categories=months, ordered=True)
        monthly_trend = df.groupby(["Month","Scope"])["Quantity"].sum().reset_index()
        st.subheader("Monthly GHG Emissions")
        fig = px.bar(monthly_trend, x="Month", y="Quantity", color="Scope", barmode="stack", color_discrete_map=SCOPE_COLORS)
        st.plotly_chart(fig, use_container_width=True)

    if st.button("Add Dummy Entry for Demo GHG"):
        new_entry = {"Scope":"Scope 1","Activity":"Stationary Combustion","Sub-Activity":"Diesel Generator",
                     "Specific Item":"Generator","Quantity":100,"Unit":"Liters","Month":months[0]}
        st.session_state.ghg_entries = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        st.experimental_rerun()

    if not df.empty:
        st.subheader("All GHG Entries")
        st.dataframe(df)
        st.download_button("Download GHG Data", df.to_csv(index=False).encode('utf-8'), "ghg_entries.csv","text/csv")

# ---------------------------
# Energy Dashboard
# ---------------------------
def render_energy_dashboard():
    st.subheader("Energy")
    df = st.session_state.energy_entries
    total_energy = df["Energy_kWh"].sum() if not df.empty else 0
    fossil_energy = df[df["Type"]=="Fossil"]["Energy_kWh"].sum() if not df.empty else 0
    renewable_energy = df[df["Type"]=="Renewable"]["Energy_kWh"].sum() if not df.empty else 0
    c1,c2,c3 = st.columns(3)
    with c1: st.markdown(f"<div class='kpi'><div class='kpi-value'>{total_energy:,.0f}</div><div class='kpi-unit'>kWh</div><div class='kpi-label'>Total Energy</div></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{ENERGY_COLORS['Fossil']}'>{fossil_energy:,.0f}</div><div class='kpi-unit'>kWh</div><div class='kpi-label'>Fossil</div></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{ENERGY_COLORS['Renewable']}'>{renewable_energy:,.0f}</div><div class='kpi-unit'>kWh</div><div class='kpi-label'>Renewable</div></div>", unsafe_allow_html=True)

    if not df.empty:
        df["Month"] = pd.Categorical(df["Month"], categories=months, ordered=True)
        monthly_trend = df.groupby(["Month","Type"])["Energy_kWh"].sum().reset_index()
        st.subheader("Monthly Energy Consumption")
        fig = px.bar(monthly_trend, x="Month", y="Energy_KWh", color="Type", barmode="stack", color_discrete_map=ENERGY_COLORS)
        st.plotly_chart(fig, use_container_width=True)

    if st.button("Add Dummy Entry for Demo Energy"):
        new_entry = {"Source":"Solar","Location":"Site A","Month":months[0],"Energy_kWh":500,"CO2e_kg":0,"Type":"Renewable"}
        st.session_state.energy_entries = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        st.experimental_rerun()

    if not df.empty:
        st.subheader("All Energy Entries")
        st.dataframe(df)
        st.download_button("Download Energy Data", df.to_csv(index=False).encode('utf-8'), "energy_entries.csv","text/csv")

# ---------------------------
# Water Dashboard
# ---------------------------
def render_water_dashboard():
    st.subheader("💧 Water Dashboard")
    df = st.session_state.water_entries
    if df.empty:
        df = pd.DataFrame(columns=[
            "Location","Source","Month","Quantity_m3","Cost_INR",
            "Rainwater_Harvested_m3","Water_Recycled_m3","Treatment_Before_Discharge","STP_ETP_Capacity_kL_day"
        ])
    total_water = df["Quantity_m3"].sum()
    total_cost = df["Cost_INR"].sum()
    recycled_water = df["Water_Recycled_m3"].sum()
    rainwater = df["Rainwater_Harvested_m3"].sum()
    treatment_coverage = df["Treatment_Before_Discharge"].value_counts().get("Yes",0)
    avg_stp_capacity = df["STP_ETP_Capacity_kL_day"].mean() if not df.empty else 0
    col1,col2,col3,col4,col5 = st.columns(5)
    col1.metric("Total Water Used (m³)", f"{total_water:,.0f}")
    col2.metric("Estimated Cost (INR)", f"₹ {total_cost:,.0f}")
    col3.metric("Recycled Water (m³)", f"{recycled_water:,.0f}")
    col4.metric("Rainwater Harvested (m³)", f"{rainwater:,.0f}")
    col5.metric("Locations with Treatment", f"{treatment_coverage}")
    st.metric("Average STP/ETP Capacity (kL/day)", f"{avg_stp_capacity:,.1f}")

    if not df.empty:
        df["Month"] = pd.Categorical(df["Month"], categories=months, ordered=True)
        monthly_trend = df.groupby(["Month","Source"])["Quantity_m3"].sum().reset_index()
        st.subheader("Monthly Water Usage by Source")
        fig = px.line(monthly_trend, x="Month", y="Quantity_m3", color="Source", markers=True)
        st.plotly_chart(fig, use_container_width=True)

    if st.button("Add Dummy Entry for Demo Water"):
        new_entry = {"Location":"Site A","Source":"Municipal","Month":months[0],
                     "Quantity_m3":1000,"Cost_INR":5000,"Rainwater_Harvested_m3":100,
                     "Water_Recycled_m3":50,"Treatment_Before_Discharge":"Yes","STP_ETP_Capacity_kL_day":50}
        st.session_state.water_entries = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        st.experimental_rerun()

    if not df.empty:
        st.subheader("All Water Entries")
        st.dataframe(df)
        st.download_button("Download Water Data", df.to_csv(index=False).encode('utf-8'), "water_entries.csv","text/csv")

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
    st.subheader(f"{st.session_state.page} section under development.")
