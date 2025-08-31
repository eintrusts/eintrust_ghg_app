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

# ---------------------------
# Initialize Data
# ---------------------------
if "ghg_entries" not in st.session_state:
    st.session_state.ghg_entries = pd.DataFrame(columns=["Scope","Activity","Sub-Activity","Specific Item","Quantity","Unit"])
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
SCOPE_COLORS = {"Scope 1": "#81c784", "Scope 2": "#4db6ac", "Scope 3": "#aed581"}
ENERGY_COLORS = {"Fossil": "#f39c12", "Renewable": "#2ecc71"}
WATER_COLORS = {"Usage": "#3498db", "Recycled": "#2ecc71", "Rainwater": "#9b59b6"}

# ---------------------------
# GHG Dashboard
# ---------------------------
def calculate_ghg_kpis():
    df = st.session_state.ghg_entries
    summary = {"Scope 1": 0.0, "Scope 2": 0.0, "Scope 3": 0.0, "Total": 0.0, "Unit": "tCO₂e"}
    if not df.empty:
        for scope in ["Scope 1","Scope 2","Scope 3"]:
            summary[scope] = df[df["Scope"]==scope]["Quantity"].sum()
        summary["Total"] = df["Quantity"].sum()
    return summary

def render_ghg_dashboard():
    st.subheader("GHG Emissions")
    kpis = calculate_ghg_kpis()
    c1, c2, c3, c4 = st.columns(4)
    for col, label, value, color in zip(
        [c1,c2,c3,c4],
        ["Total","Scope 1","Scope 2","Scope 3"],
        [kpis["Total"], kpis["Scope 1"], kpis["Scope 2"], kpis["Scope 3"]],
        ["#ffffff", SCOPE_COLORS["Scope 1"], SCOPE_COLORS["Scope 2"], SCOPE_COLORS["Scope 3"]]
    ):
        col.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{color}'>{format_indian(value)}</div><div class='kpi-unit'>{kpis['Unit']}</div><div class='kpi-label'>{label}</div></div>", unsafe_allow_html=True)
    if not st.session_state.ghg_entries.empty:
        df = st.session_state.ghg_entries.copy()
        if "Month" not in df.columns:
            df["Month"] = np.random.choice(months, len(df))
        df["Month"] = pd.Categorical(df["Month"], categories=months, ordered=True)
        monthly_trend = df.groupby(["Month","Scope"])["Quantity"].sum().reset_index()
        st.subheader("Monthly GHG Emissions")
        fig = px.bar(monthly_trend, x="Month", y="Quantity", color="Scope", barmode="stack", color_discrete_map=SCOPE_COLORS)
        st.plotly_chart(fig, use_container_width=True)
        st.subheader("All entries")
        st.dataframe(df)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download GHG CSV", csv, "ghg_entries.csv", "text/csv")

# ---------------------------
# Energy Dashboard
# ---------------------------
def render_energy_dashboard():
    st.subheader("Energy Dashboard")
    df = st.session_state.ghg_entries
    calorific_values = {"Diesel":35.8,"Petrol":34.2}
    emission_factors = {"Diesel":2.68,"Petrol":2.31,"Electricity":0.82,"Solar":0.0,"Wind":0.0}
    df_energy = df[df["Scope"].isin(["Scope 1","Scope 2"])].copy() if not df.empty else pd.DataFrame()
    if not df_energy.empty:
        df_energy["Energy_kWh"] = df_energy.apply(lambda r: r["Quantity"]*calorific_values.get(r["Sub-Activity"],1)/3.6 if r["Sub-Activity"] in calorific_values else 0, axis=1)
        df_energy["CO2e_kg"] = df_energy.apply(lambda r: r["Quantity"]*emission_factors.get(r["Sub-Activity"],0), axis=1)
        df_energy["Type"]="Fossil"
        df_energy["Month"] = np.random.choice(months, len(df_energy))
    all_energy = pd.concat([df_energy.rename(columns={"Sub-Activity":"Fuel"}), st.session_state.renewable_entries], ignore_index=True) if not st.session_state.renewable_entries.empty else df_energy
    total_energy = all_energy.groupby("Type")["Energy_kWh"].sum().to_dict() if not all_energy.empty else {}
    c1,c2,c3 = st.columns(3)
    for col,label,value,color in zip([c1,c2,c3],["Total Energy","Fossil","Renewable"],[sum(total_energy.values()), total_energy.get("Fossil",0), total_energy.get("Renewable",0)], ["#ffffff", ENERGY_COLORS["Fossil"], ENERGY_COLORS["Renewable"]]):
        col.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{color}'>{value:,.0f}</div><div class='kpi-unit'>kWh</div><div class='kpi-label'>{label}</div></div>", unsafe_allow_html=True)
    if not all_energy.empty:
        all_energy["Month"] = pd.Categorical(all_energy.get("Month", months[0]), categories=months, ordered=True)
        monthly_trend = all_energy.groupby(["Month","Type"])["Energy_kWh"].sum().reset_index()
        st.subheader("Monthly Energy Consumption (kWh)")
        fig = px.bar(monthly_trend, x="Month", y="Energy_kWh", color="Type", barmode="stack", color_discrete_map=ENERGY_COLORS)
        st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# Water Dashboard
# ---------------------------
def render_water_dashboard():
    st.subheader("💧 Water Consumption & Management (Apr→Mar)")

    # Add Water Entry
    st.markdown("### Add Water Entry")
    with st.form("water_form"):
        loc = st.text_input("Location")
        source = st.selectbox("Source", ["Municipal", "Groundwater", "Rainwater Harvested", "Recycled"])
        qty = st.number_input("Annual Quantity (m³)", min_value=0.0)
        cost = st.number_input("Annual Cost (INR)", min_value=0.0)
        rain = st.number_input("Rainwater Harvested (m³)", min_value=0.0)
        recycled = st.number_input("Water Recycled (m³)", min_value=0.0)
        treatment = st.selectbox("Treatment Before Discharge", ["Yes","No"])
        stp = st.number_input("STP/ETP Capacity (kL/day)", min_value=0.0)
        submit = st.form_submit_button("Add Entry")
        if submit:
            # Split annual quantity into 12 months
            for m in months:
                st.session_state.water_data = pd.concat([st.session_state.water_data,pd.DataFrame([{
                    "Location": loc,"Source": source,"Month": m,"Quantity_m3": qty/12,"Cost_INR": cost/12
                }])], ignore_index=True)
                st.session_state.advanced_water_data = pd.concat([st.session_state.advanced_water_data,pd.DataFrame([{
                    "Location": loc,"Month": m,"Rainwater_Harvested_m3": rain/12,
                    "Water_Recycled_m3": recycled/12,"Treatment_Before_Discharge": treatment,
                    "STP_ETP_Capacity_kL_day": stp
                }])], ignore_index=True)
            st.success("Water entry added successfully!")
            st.experimental_rerun()

    # KPIs
    wdf = st.session_state.water_data
    advdf = st.session_state.advanced_water_data
    total_water = wdf["Quantity_m3"].sum() if not wdf.empty else 0
    total_cost = wdf["Cost_INR"].sum() if not wdf.empty else 0
    total_rain = advdf["Rainwater_Harvested_m3"].sum() if not advdf.empty else 0
    total_recycled = advdf["Water_Recycled_m3"].sum() if not advdf.empty else 0
    treatment_count = advdf["Treatment_Before_Discharge"].value_counts().get("Yes",0)
    avg_stp = advdf["STP_ETP_Capacity_kL_day"].mean() if not advdf.empty else 0
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Total Water Used (m³)", f"{total_water:,.0f}")
    c2.metric("Estimated Cost (INR)", f"₹ {total_cost:,.0f}")
    c3.metric("Recycled Water (m³)", f"{total_recycled:,.0f}")
    c4.metric("Rainwater Harvested (m³)", f"{total_rain:,.0f}")
    c5.metric("Locations with Treatment", f"{treatment_count}")
    st.metric("Average STP/ETP Capacity (kL/day)", f"{avg_stp:,.1f}")

    # Monthly Trends
    if not wdf.empty:
        monthly = wdf.groupby(["Month","Source"])["Quantity_m3"].sum().reset_index()
        monthly["Month"] = pd.Categorical(monthly["Month"], categories=months, ordered=True)
        st.subheader("Monthly Water Usage by Source")
        fig = px.line(monthly, x="Month", y="Quantity_m3", color="Source", markers=True, color_discrete_map=WATER_COLORS)
        st.plotly_chart(fig, use_container_width=True)

    if not advdf.empty:
        adv_monthly = advdf.groupby("Month")[["Rainwater_Harvested_m3","Water_Recycled_m3"]].sum().reset_index()
        adv_monthly["Month"] = pd.Categorical(adv_monthly["Month"], categories=months, ordered=True)
        st.subheader("Monthly Rainwater & Recycled Water")
        fig2 = px.line(adv_monthly, x="Month", y=["Rainwater_Harvested_m3","Water_Recycled_m3"], markers=True, color_discrete_sequence=[WATER_COLORS["Rainwater"], WATER_COLORS["Recycled"]])
        st.plotly_chart(fig2, use_container_width=True)

    # Download CSV
    if not wdf.empty:
        csv = pd.concat([wdf, advdf], axis=1).to_csv(index=False).encode("utf-8")
        st.download_button("Download Water Data CSV", csv, "water_entries.csv", "text/csv")

# ---------------------------
# Home Dashboard
# ---------------------------
def render_home_dashboard():
    st.title("🌱 EinTrust Sustainability Dashboard")
    st.info("Overview of GHG, Energy, and Water KPIs")
    ghg = calculate_ghg_kpis()
    total_energy = st.session_state.renewable_entries["Energy_kWh"].sum() + st.session_state.ghg_entries["Quantity"].sum() if not st.session_state.ghg_entries.empty else 0
    wdf = st.session_state.water_data
    advdf = st.session_state.advanced_water_data
    total_water = wdf["Quantity_m3"].sum() if not wdf.empty else 0
    total_recycled = advdf["Water_Recycled_m3"].sum() if not advdf.empty else 0
    total_rain = advdf["Rainwater_Harvested_m3"].sum() if not advdf.empty else 0

    c1,c2,c3,c4,c5,c6,c7 = st.columns(7)
    c1.markdown(f"<div class='kpi'><div class='kpi-value'>{format_indian(ghg['Total'])}</div><div class='kpi-label'>Total GHG tCO₂e</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='kpi'><div class='kpi-value'>{format_indian(ghg['Scope 1'])}</div><div class='kpi-label'>Scope 1 tCO₂e</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='kpi'><div class='kpi-value'>{format_indian(ghg['Scope 2'])}</div><div class='kpi-label'>Scope 2 tCO₂e</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='kpi'><div class='kpi-value'>{format_indian(ghg['Scope 3'])}</div><div class='kpi-label'>Scope 3 tCO₂e</div></div>", unsafe_allow_html=True)
    c5.markdown(f"<div class='kpi'><div class='kpi-value'>{format_indian(total_energy)}</div><div class='kpi-label'>Total Energy kWh</div></div>", unsafe_allow_html=True)
    c6.markdown(f"<div class='kpi'><div class='kpi-value'>{format_indian(total_water)}</div><div class='kpi-label'>Water Used m³</div></div>", unsafe_allow_html=True)
    c7.markdown(f"<div class='kpi'><div class='kpi-value'>{format_indian(total_recycled)}</div><div class='kpi-label'>Water Recycled m³</div></div>", unsafe_allow_html=True)

# ---------------------------
# Page Routing
# ---------------------------
if st.session_state.page == "Home":
    render_home_dashboard()
elif st.session_state.page == "GHG":
    render_ghg_dashboard()
elif st.session_state.page == "Energy":
    render_energy_dashboard()
elif st.session_state.page == "Water":
    render_water_dashboard()
else:
    st.warning("Page under development.")
