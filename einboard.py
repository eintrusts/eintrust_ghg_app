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

html, body, [class*="css"] {
    font-family: 'Roboto', sans-serif;
}

.stApp { background-color: #0d1117; color: #e6edf3; }

/* KPI boxes */
.kpi {
    background: linear-gradient(145deg, #12131a, #1a1b22);
    padding: 20px;
    border-radius: 12px;
    text-align: center;
    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    margin-bottom: 10px;
    min-height: 120px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    transition: transform 0.2s, box-shadow 0.2s;
}
.kpi:hover {
    transform: scale(1.05);
    box-shadow: 0 8px 20px rgba(0,0,0,0.6);
}
.kpi-value {
    font-size: 28px;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 5px;
}
.kpi-unit {
    font-size: 16px;
    font-weight: 500;
    color: #cfd8dc;
    margin-bottom: 5px;
}
.kpi-label {
    font-size: 14px;
    color: #cfd8dc;
    letter-spacing: 0.5px;
}

/* Dataframe styling */
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

with st.sidebar:
    st.image("https://github.com/eintrusts/eintrust_ghg_app/raw/main/EinTrust%20%20logo.png", use_container_width=True)
    st.markdown("---")
    
    if st.button("Home"):
        st.session_state.page = "Home"

    env_exp = st.expander("Environment", expanded=True)
    with env_exp:
        if st.button("GHG"):
            st.session_state.page = "GHG"
        if st.button("Energy"):
            st.session_state.page = "Energy"
        if st.button("Water"):
            st.session_state.page = "Water"
        if st.button("Waste"):
            st.session_state.page = "Waste"
        if st.button("Biodiversity"):
            st.session_state.page = "Biodiversity"

    social_exp = st.expander("Social", expanded=False)
    with social_exp:
        if st.button("Employee"):
            st.session_state.page = "Employee"
        if st.button("Health & Safety"):
            st.session_state.page = "Health & Safety"
        if st.button("CSR"):
            st.session_state.page = "CSR"

    gov_exp = st.expander("Governance", expanded=False)
    with gov_exp:
        if st.button("Board"):
            st.session_state.page = "Board"
        if st.button("Policies"):
            st.session_state.page = "Policies"
        if st.button("Compliance"):
            st.session_state.page = "Compliance"
        if st.button("Risk Management"):
            st.session_state.page = "Risk Management"

# ---------------------------
# GHG Dashboard
# ---------------------------
if "entries" not in st.session_state:
    st.session_state.entries = pd.DataFrame(columns=["Scope","Activity","Sub-Activity","Specific Item","Quantity","Unit"])

def calculate_kpis():
    df = st.session_state.entries
    summary = {"Scope 1": 0.0, "Scope 2": 0.0, "Scope 3": 0.0, "Total Quantity": 0.0, "Unit": "tCO₂e"}
    if not df.empty:
        for scope in ["Scope 1","Scope 2","Scope 3"]:
            summary[scope] = df[df["Scope"]==scope]["Quantity"].sum()
        summary["Total Quantity"] = df["Quantity"].sum()
    return summary

def render_ghg_results():
    st.subheader("GHG Emissions Results")
    kpis = calculate_kpis()
    SCOPE_COLORS = {"Scope 1": "#81c784", "Scope 2": "#4db6ac", "Scope 3": "#aed581"}
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

# ---------------------------
# Energy & CO2e Dashboard
# ---------------------------
def render_energy_results():
    st.subheader("⚡ Energy & CO₂e Results (Financial Year Apr→Mar)")
    
    calorific_values = {"Diesel": 35.8,"Petrol": 34.2,"LPG":46.1,"CNG":48,"Coal":24,"Biomass":15}
    emission_factors = {"Diesel":2.68,"Petrol":2.31,"LPG":1.51,"CNG":2.02,"Coal":2.42,"Biomass":0.0,
                        "Electricity":0.82,"Solar":0.0,"Wind":0.0,"Purchased Green Energy":0.0,"Biogas":0.0}
    months = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]

    if not st.session_state.entries.empty:
        df = st.session_state.entries.copy()
        scope1_2_data = df[df["Scope"].isin(["Scope 1","Scope 2"])].copy()
        if not scope1_2_data.empty:
            def compute_energy(row):
                fuel = row["Sub-Activity"]
                qty = row["Quantity"]
                if fuel=="Grid Electricity":
                    energy_kwh = qty
                else:
                    energy_kwh = (qty * calorific_values.get(fuel,0))/3.6
                co2e = qty * emission_factors.get(fuel,0)
                return pd.Series([energy_kwh, co2e])
            scope1_2_data[["Energy_kWh","CO2e_kg"]] = scope1_2_data.apply(compute_energy, axis=1)
            scope1_2_data["Type"]="Fossil"
    else:
        scope1_2_data = pd.DataFrame(columns=["Type","Energy_kWh","CO2e_kg","Month"])

    # Combine all energy types (assuming renewable already added)
    all_energy = scope1_2_data.copy()
    if not all_energy.empty:
        all_energy["Month"] = pd.Categorical(months*len(all_energy)//12, categories=months, ordered=True)
    
    # KPI Cards
    total_energy = all_energy.groupby("Type")["Energy_kWh"].sum().to_dict() if not all_energy.empty else {}
    total_co2e = all_energy.groupby("Type")["CO2e_kg"].sum().to_dict() if not all_energy.empty else {}
    fossil_energy = total_energy.get("Fossil",0)
    renewable_energy = total_energy.get("Renewable",0)
    fossil_co2e = total_co2e.get("Fossil",0)
    renewable_co2e = total_co2e.get("Renewable",0)
    
    c1, c2, c3 = st.columns(3)
    for col, label, value, delta in zip(
        [c1,c2,c3],
        ["Fossil Energy (kWh)","Renewable Energy (kWh)","Total Energy (kWh)"],
        [fossil_energy, renewable_energy, fossil_energy+renewable_energy],
        [f"{fossil_co2e:,.0f} kg CO₂e", f"{renewable_co2e:,.0f} kg CO₂e", f"{fossil_co2e+renewable_co2e:,.0f} kg CO₂e"]
    ):
        col.markdown(f"""
        <div class='kpi'>
            <div class='kpi-value'>{value:,.0f}</div>
            <div class='kpi-unit'>kWh</div>
            <div class='kpi-label'>{label.lower()}</div>
            <div style='color:#cfd8dc;font-size:14px;margin-top:5px;'>{delta}</div>
        </div>
        """, unsafe_allow_html=True)

    # Monthly trends
    if not all_energy.empty:
        monthly_trend = all_energy.groupby(["Month","Type"]).sum().reset_index()
        st.subheader("Monthly Energy Consumption (kWh)")
        fig1 = px.line(monthly_trend, x="Month", y="Energy_kWh", color="Type", markers=True)
        st.plotly_chart(fig1, use_container_width=True)
        
        st.subheader("Monthly CO₂e Emissions (kg)")
        fig2 = px.line(monthly_trend, x="Month", y="CO2e_kg", color="Type", markers=True)
        st.plotly_chart(fig2, use_container_width=True)

# ---------------------------
# Render Pages
# ---------------------------
if st.session_state.page == "Home":
    st.title("🌍 Welcome to EinTrust Dashboard")
    st.info("Below are the latest GHG and Energy results.")
    render_ghg_results()
    render_energy_results()
elif st.session_state.page == "GHG":
    render_ghg_results()
elif st.session_state.page == "Energy":
    render_energy_results()
else:
    st.subheader(f"{st.session_state.page} section")
    st.info("This section is under development. Please select other pages from sidebar.")
