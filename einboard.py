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
.kpi:hover { transform: scale(1.05); box-shadow: 0 8px 20px rgba(0,0,0,0.6); }
.kpi-value { font-size: 28px; font-weight: 700; color: #ffffff; margin-bottom: 5px; }
.kpi-unit { font-size: 16px; font-weight: 500; color: #cfd8dc; margin-bottom: 5px; }
.kpi-label { font-size: 14px; color: #cfd8dc; letter-spacing: 0.5px; }

.sdg-card {
    border-radius: 10px;
    padding: 15px;
    margin: 8px;
    display: inline-block;
    width: 100%;
    min-height: 110px;
    text-align: left;
    color: white;
}
.sdg-number { font-weight: 700; font-size: 20px; }
.sdg-name { font-size: 16px; margin-bottom: 5px; }
.sdg-percent { font-size: 14px; }
@media (min-width: 768px) {
    .sdg-card { width: 220px; display: inline-block; }
}
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
            all: unset; cursor: pointer; padding: 0.4rem;
            text-align: left; border-radius: 0.3rem;
            margin-bottom: 0.2rem;
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
# Initialize Data
# ---------------------------
if "entries" not in st.session_state:
    st.session_state.entries = pd.DataFrame(columns=["Scope","Activity","Sub-Activity","Specific Item","Quantity","Unit"])
if "renewable_entries" not in st.session_state:
    st.session_state.renewable_entries = pd.DataFrame(columns=["Source","Location","Month","Energy_kWh","CO2e_kg","Type"])
if "sdg_engagement" not in st.session_state:
    st.session_state.sdg_engagement = {i:0 for i in range(1,18)}

# ---------------------------
# Constants
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

# ---------------------------
# KPI Function
# ---------------------------
def render_ghg_kpis():
    df = st.session_state.entries.copy()
    if df.empty:
        st.info("No GHG data available yet.")
        return
    # Aggregate by scope
    totals = df.groupby("Scope")["Quantity"].sum().to_dict()
    scope1 = totals.get("Scope 1", 0)
    scope2 = totals.get("Scope 2", 0)
    scope3 = totals.get("Scope 3", 0)
    total = scope1 + scope2 + scope3

    c1,c2,c3,c4 = st.columns(4)
    for col, label, value in zip(
        [c1,c2,c3,c4],
        ["Total Emissions","Scope 1 Emissions","Scope 2 Emissions","Scope 3 Emissions"],
        [total, scope1, scope2, scope3]
    ):
        col.markdown(
            f"<div class='kpi'><div class='kpi-value'>{value:,.2f}</div>"
            f"<div class='kpi-unit'>tCO₂e</div><div class='kpi-label'>{label}</div></div>",
            unsafe_allow_html=True
        )

# ---------------------------
# GHG Dashboard
# ---------------------------
def render_ghg_dashboard(include_data=True, show_chart=True):
    st.subheader("GHG Emissions Overview")
    render_ghg_kpis()

    df = st.session_state.entries.copy()
    if show_chart and not df.empty:
        df["Month"] = np.random.choice(months, len(df))  # placeholder
        monthly = df.groupby(["Month","Scope"])["Quantity"].sum().reset_index()
        st.subheader("Monthly GHG Emissions (tCO₂e)")
        fig = px.bar(monthly, x="Month", y="Quantity", color="Scope", barmode="stack")
        st.plotly_chart(fig, use_container_width=True)

    if include_data:
        st.subheader("Add New Entry")
        scope = st.selectbox("Select Scope", ["Scope 1","Scope 2","Scope 3"])
        activity = st.text_input("Activity")
        sub_activity = st.text_input("Sub-Activity")
        specific_item = st.text_input("Specific Item")
        unit = st.text_input("Unit")
        quantity = st.number_input("Quantity", min_value=0.0, format="%.2f")

        if st.button("Add Entry"):
            new_entry = {
                "Scope": scope,
                "Activity": activity,
                "Sub-Activity": sub_activity,
                "Specific Item": specific_item,
                "Quantity": quantity,
                "Unit": unit
            }
            st.session_state.entries = pd.concat([st.session_state.entries, pd.DataFrame([new_entry])], ignore_index=True)
            st.success("Entry added successfully!")

        if not st.session_state.entries.empty:
            st.subheader("All Entries")
            st.dataframe(st.session_state.entries, use_container_width=True)

# ---------------------------
# Energy Dashboard
# ---------------------------
def render_energy_dashboard(include_input=True, show_chart=True):
    st.subheader("Energy")
    df = st.session_state.entries.copy()
    if not df.empty:
        df_energy = df.copy()
        df_energy["Energy_kWh"] = df_energy["Quantity"] * 1.5  # dummy conversion
        df_energy["Type"] = np.where(df_energy["Scope"].isin(["Scope 1","Scope 2"]), "Fossil", "Renewable")
        df_energy["Month"] = np.random.choice(months, len(df_energy))
        total_energy = df_energy.groupby("Type")["Energy_kWh"].sum().to_dict()
        fossil = total_energy.get("Fossil",0)
        renewable = total_energy.get("Renewable",0)
        total = fossil+renewable

        c1,c2,c3 = st.columns(3)
        for col,label,value,color in zip(
            [c1,c2,c3],
            ["Total Energy (kWh)","Fossil Energy (kWh)","Renewable Energy (kWh)"],
            [total,fossil,renewable],
            ["#ffffff",ENERGY_COLORS["Fossil"],ENERGY_COLORS["Renewable"]]
        ):
            col.markdown(
                f"<div class='kpi'><div class='kpi-value' style='color:{color}'>{int(value):,}</div>"
                f"<div class='kpi-unit'>kWh</div><div class='kpi-label'>{label.lower()}</div></div>",
                unsafe_allow_html=True
            )

        if show_chart:
            monthly_trend = df_energy.groupby(["Month","Type"])["Energy_kWh"].sum().reset_index()
            st.subheader("Monthly Energy Consumption (kWh)")
            fig = px.bar(monthly_trend, x="Month", y="Energy_kWh", color="Type", barmode="stack", color_discrete_map=ENERGY_COLORS)
            st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# SDG Dashboard
# ---------------------------
def render_sdg_dashboard():
    st.title("Sustainable Development Goals (SDGs)")
    st.subheader("Company Engagement by SDG")
    num_cols = 4
    rows = (len(SDG_LIST) + num_cols - 1) // num_cols
    idx = 0
    for _ in range(rows):
        cols = st.columns(num_cols)
        for c in range(num_cols):
            if idx >= len(SDG_LIST): break
            sdg_name = SDG_LIST[idx]
            sdg_color = SDG_COLORS[idx]
            sdg_number = idx + 1
            engagement = st.session_state.sdg_engagement.get(sdg_number, 0)
            engagement = cols[c].slider(
                f"Engagement % - SDG {sdg_number}", 0, 100, value=engagement, key=f"sdg{sdg_number}"
            )
            st.session_state.sdg_engagement[sdg_number] = engagement
            cols[c].markdown(
                f"<div class='sdg-card' style='background-color:{sdg_color}'>"
                f"<div class='sdg-number'>SDG {sdg_number}</div>"
                f"<div class='sdg-name'>{sdg_name}</div>"
                f"<div class='sdg-percent'>Engagement: {engagement}%</div>"
                f"</div>", unsafe_allow_html=True
            )
            idx += 1

# ---------------------------
# Render Pages
# ---------------------------
if st.session_state.page == "Home":
    st.title("EinTrust Sustainability Dashboard")
    render_ghg_dashboard(include_data=False, show_chart=True)
    render_energy_dashboard(include_input=False, show_chart=True)
elif st.session_state.page == "GHG":
    render_ghg_dashboard(include_data=True, show_chart=True)
elif st.session_state.page == "Energy":
    render_energy_dashboard(include_input=True, show_chart=True)
elif st.session_state.page == "SDG":
    render_sdg_dashboard()
else:
    st.subheader(f"{st.session_state.page} section")
    st.info("This section is under development. Please select other pages from sidebar.")
