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

.sdg-card {
    border-radius: 10px; padding: 15px; margin: 8px;
    display: inline-block; width: 100%; min-height: 110px;
    text-align: left; color: white;
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
    
    st.markdown("---")
    sidebar_button("SDG")

# ---------------------------
# Initialize Data
# ---------------------------
if "entries" not in st.session_state:
    st.session_state.entries = pd.DataFrame(columns=["Scope","Activity","Sub-Activity","Specific Item","Quantity","Unit"])
if "renewable_entries" not in st.session_state:
    st.session_state.renewable_entries = pd.DataFrame(columns=["Source","Location","Month","Energy_kWh","CO2e_kg","Type"])
if "sdg_engagement" not in st.session_state:
    st.session_state.sdg_engagement = {i:0 for i in range(1,18)}
if "employee_data" not in st.session_state:
    st.session_state.employee_data = {}

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

SDG_LIST = [
    "No Poverty", "Zero Hunger", "Good Health & Wellbeing", "Quality Education", "Gender Equality",
    "Clean Water & Sanitation", "Affordable & Clean Energy", "Decent Work & Economic Growth",
    "Industry, Innovation & Infrastructure", "Reduced Inequalities", "Sustainable Cities & Communities",
    "Responsible Consumption & Production", "Climate Action", "Life Below Water", "Life on Land",
    "Peace, Justice & Strong Institutions", "Partnerships for the Goals"
]

SDG_COLORS = [
    "#e5243b","#dda63a","#4c9f38","#c5192d","#ff3a21","#26bde2","#fcc30b","#a21942","#fd6925",
    "#dd1367","#fd9d24","#bf8b2e","#3f7e44","#0a97d9","#56c02b","#00689d","#19486a"
]

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
