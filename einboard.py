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
        st.experimental_rerun()
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
if "water_entries" not in st.session_state:
    st.session_state.water_entries = pd.DataFrame(columns=["Location","Source","Month","Quantity_m3","Cost_INR"])

# ---------------------------
# Constants
# ---------------------------
months = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]
SCOPE_COLORS = {"Scope 1": "#81c784", "Scope 2": "#4db6ac", "Scope 3": "#aed581"}
ENERGY_COLORS = {"Fossil": "#f39c12", "Renewable": "#2ecc71"}
WATER_COLOR = "#3498db"

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

# ---------------------------
# Energy Dashboard
# ---------------------------
def render_energy_dashboard(include_input=True, show_chart=True):
    st.subheader("Energy")
    df = st.session_state.entries
    calorific_values = {"Diesel": 35.8,"Petrol": 34.2,"LPG":46.1,"CNG":48,"Coal":24,"Biomass":15}
    emission_factors = {"Diesel":2.68,"Petrol":2.31,"LPG":1.51,"CNG":2.02,"Coal":2.42,"Biomass":0.0,
                        "Electricity":0.82,"Solar":0.0,"Wind":0.0,"Purchased Green Energy":0.0,"Biogas":0.0}

    scope1_2_data = df[df["Scope"].isin(["Scope 1","Scope 2"])].copy() if not df.empty else pd.DataFrame()
    if not scope1_2_data.empty:
        def compute_energy(row):
            fuel = row["Sub-Activity"]
            qty = row["Quantity"]
            if fuel=="Grid Electricity": energy_kwh = qty
            else: energy_kwh = (qty * calorific_values.get(fuel,0))/3.6
            co2e = qty * emission_factors.get(fuel,0)
            return pd.Series([energy_kwh, co2e])
        scope1_2_data[["Energy_kWh","CO2e_kg"]] = scope1_2_data.apply(compute_energy, axis=1)
        scope1_2_data["Type"]="Fossil"
        scope1_2_data["Month"] = np.random.choice(months, len(scope1_2_data))
    all_energy = pd.concat([scope1_2_data.rename(columns={"Sub-Activity":"Fuel"}), st.session_state.renewable_entries], ignore_index=True) if not st.session_state.renewable_entries.empty else scope1_2_data

    # KPI Cards
    total_energy = all_energy.groupby("Type")["Energy_kWh"].sum().to_dict() if not all_energy.empty else {}
    fossil_energy = total_energy.get("Fossil",0)
    renewable_energy = total_energy.get("Renewable",0)
    total_sum = fossil_energy + renewable_energy
    c1,c2,c3 = st.columns(3)
    for col, label, value, color in zip(
        [c1,c2,c3],
        ["Total Energy (kWh)","Fossil Energy (kWh)","Renewable Energy (kWh)"],
        [total_sum,fossil_energy,renewable_energy],
        ["#ffffff",ENERGY_COLORS["Fossil"],ENERGY_COLORS["Renewable"]]
    ):
        col.markdown(f"""
        <div class='kpi'>
            <div class='kpi-value' style='color:{color}'>{value:,.0f}</div>
            <div class='kpi-unit'>kWh</div>
            <div class='kpi-label'>{label.lower()}</div>
        </div>
        """, unsafe_allow_html=True)

    if show_chart and not all_energy.empty:
        all_energy["Month"] = pd.Categorical(all_energy.get("Month", months[0]), categories=months, ordered=True)
        monthly_trend = all_energy.groupby(["Month","Type"])["Energy_kWh"].sum().reset_index()
        st.subheader("Monthly Energy Consumption (kWh)")
        fig = px.bar(monthly_trend, x="Month", y="Energy_kWh", color="Type", barmode="stack",
                     color_discrete_map=ENERGY_COLORS)
        st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# Water Dashboard (Full Integration)
# ---------------------------
def render_water_dashboard(include_input=True, show_chart=True):
    st.subheader("💧 Water Consumption Dashboard (Apr → Mar)")
    df = st.session_state.water_entries

    # ---------------------------
    # KPI Cards
    # ---------------------------
    total_water = df["Quantity_m3"].sum() if not df.empty else 0
    total_cost = df["Cost_INR"].sum() if not df.empty else 0
    recycled_water = df[df["Source"]=="Recycled"]["Quantity_m3"].sum() if not df.empty else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Water Used (m³)", f"{total_water:,.2f}")
    c2.metric("Estimated Cost (INR)", f"₹ {total_cost:,.0f}")
    c3.metric("Recycled/Other Water (m³)", f"{recycled_water:,.2f}")

    # ---------------------------
    # Monthly Trend Chart
    # ---------------------------
    if not df.empty:
        monthly_trend = df.groupby(["Month","Source"])["Quantity_m3"].sum().reset_index()
        monthly_trend["Month"] = pd.Categorical(monthly_trend["Month"], categories=months, ordered=True)
        st.subheader("Monthly Water Usage (m³)")
        fig1 = px.line(monthly_trend, x="Month", y="Quantity_m3", color="Source", markers=True,
                       labels={"Quantity_m3":"Water (m³)"}, title="Monthly Water Usage by Source")
        st.plotly_chart(fig1, use_container_width=True)

        # ---------------------------
        # Location-wise Chart
        # ---------------------------
        location_trend = df.groupby(["Location","Source"])["Quantity_m3"].sum().reset_index()
        st.subheader("Water Usage by Location")
        fig2 = px.bar(location_trend, x="Location", y="Quantity_m3", color="Source", barmode="stack",
                      labels={"Quantity_m3":"Water (m³)"})
        st.plotly_chart(fig2, use_container_width=True)

    # ---------------------------
    # Data Entry Section
    # ---------------------------
    st.subheader("Add Water Consumption Data")
    num_entries = st.number_input("Number of entries to add", min_value=1, max_value=20, value=1)
    new_entries = []
    for i in range(int(num_entries)):
        col1, col2, col3, col4 = st.columns([3,3,2,2])
        with col1:
            location = st.text_input(f"Location {i+1}", "", key=f"loc{i}")
        with col2:
            source = st.selectbox(f"Source {i+1}", ["Municipal","Groundwater","Recycled","Other"], key=f"src{i}")
        with col3:
            quantity = st.number_input(f"Quantity (m³) {i+1}", min_value=0.0, key=f"qty{i}")
        with col4:
            cost = st.number_input(f"Cost (INR) {i+1}", min_value=0.0, key=f"cost{i}")
        month = st.selectbox(f"Month {i+1}", months, key=f"month{i}")
        new_entries.append({"Location":location,"Source":source,"Month":month,"Quantity_m3":quantity,"Cost_INR":cost})

    if new_entries:
        new_df = pd.DataFrame(new_entries)
        st.session_state.water_entries = pd.concat([df,new_df], ignore_index=True)

    # ---------------------------
    # CSV Upload
    # ---------------------------
    st.subheader("Or Upload CSV File")
    uploaded_file = st.file_uploader("Upload water consumption CSV", type=["csv"])
    if uploaded_file:
        file_df = pd.read_csv(uploaded_file)
        required_cols = ["Location","Source","Month","Quantity_m3","Cost_INR"]
        if all(col in file_df.columns for col in required_cols):
            st.session_state.water_entries = pd.concat([df,file_df[required_cols]], ignore_index=True)
            st.success("File uploaded successfully!")
        else:
            st.error(f"CSV must contain columns: {required_cols}")

    # ---------------------------
    # Download CSV
    # ---------------------------
    st.subheader("Download Water Consumption Data")
    def convert_df(df):
        return df.to_csv(index=False).encode('utf-8')
    csv = convert_df(st.session_state.water_entries)
    st.download_button("Download CSV", csv, "water_consumption_data.csv", "text/csv")

# ---------------------------
# Render Pages
# ---------------------------
if st.session_state.page == "Home":
    st.title("EinTrust Sustainability Dashboard")
    render_ghg_dashboard(include_data=False, show_chart=False)
    render_energy_dashboard(include_input=False, show_chart=False)
    render_water_dashboard(include_input=False, show_chart=False)
elif st.session_state.page == "GHG":
    render_ghg_dashboard(include_data=True, show_chart=True)
elif st.session_state.page == "Energy":
    render_energy_dashboard(include_input=True, show_chart=True)
elif st.session_state.page == "Water":
    render_water_dashboard(include_input=True, show_chart=True)
else:
    st.subheader(f"{st.session_state.page} section")
    st.info("This section is under development. Please select other pages from sidebar.")
