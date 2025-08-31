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

.kpi, .entry-block {
    background: linear-gradient(145deg, #12131a, #1a1b22);
    padding: 15px; border-radius: 12px; text-align: center;
    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    margin-bottom: 10px;
}
.kpi:hover, .entry-block:hover { transform: scale(1.02); box-shadow: 0 6px 18px rgba(0,0,0,0.5); }

.sdg-block {
    padding: 15px; border-radius: 12px; text-align: center;
    margin-bottom: 10px; transition: transform 0.2s, box-shadow 0.2s;
}
.sdg-block:hover { transform: scale(1.03); box-shadow: 0 6px 18px rgba(0,0,0,0.5); }
.sdg-number { font-size: 20px; font-weight: 700; color: #fff; margin-bottom: 5px; }
.sdg-name { font-size: 16px; font-weight: 600; color: #ffffff; margin-bottom: 5px; }
.sdg-progress { font-size: 14px; color: #cfd8dc; margin-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Session State Initialization
# ---------------------------
if "page" not in st.session_state:
    st.session_state.page = "Home"

for key in ["entries","renewable_entries","water_entries","waste_entries","biodiversity_entries",
            "employee_entries","health_safety_entries","csr_entries","governance_entries"]:
    if key not in st.session_state:
        st.session_state[key] = pd.DataFrame()

# ---------------------------
# Sidebar & Navigation
# ---------------------------
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
# SDG Dashboard
# ---------------------------
SDG_LIST = [
    "No Poverty", "Zero Hunger", "Good Health & Wellbeing", "Quality Education", "Gender Equality",
    "Clean Water & Sanitation", "Affordable & Clean Energy", "Decent Work & Economic Growth",
    "Industry, Innovation & Infrastructure", "Reduced Inequalities", "Sustainable Cities & Communities",
    "Responsible Consumption & Production", "Climate Action", "Life Below Water", "Life on Land",
    "Peace, Justice & Strong Institutions", "Partnerships for the Goals"
]
SDG_COLORS = [
    "#E5243B","#DDA63A","#4C9F38","#C5192D","#FF3A21","#26BDE2","#FCC30B",
    "#A21942","#FD6925","#DD1367","#FD9D24","#BF8B2E","#3F7E44","#0A97D9",
    "#56C02B","#00689D","#19486A"
]

def calculate_sdg_engagement():
    sdg_engagement = {sdg:0 for sdg in SDG_LIST}
    # Environment
    total_renewable = st.session_state.renewable_entries["Energy_kWh"].sum() if not st.session_state.renewable_entries.empty else 0
    total_fossil = st.session_state.entries["Quantity"].sum() if not st.session_state.entries.empty else 0
    total_water = st.session_state.water_entries["Quantity"].sum() if not st.session_state.water_entries.empty else 0
    total_waste = st.session_state.waste_entries["Quantity"].sum() if not st.session_state.waste_entries.empty else 0
    total_biodiversity = len(st.session_state.biodiversity_entries)
    # Social
    total_employee = len(st.session_state.employee_entries)
    total_hs = len(st.session_state.health_safety_entries)
    total_csr = len(st.session_state.csr_entries)
    # Governance
    total_governance = len(st.session_state.governance_entries)
    # Mapping logic
    sdg_engagement["Affordable & Clean Energy"] = min(100, total_renewable/100000*100)
    sdg_engagement["Responsible Consumption & Production"] = min(100, total_fossil/50000*50 + total_waste/20000*50)
    sdg_engagement["Climate Action"] = min(100, total_fossil/50000*50 + total_renewable/100000*50)
    sdg_engagement["Clean Water & Sanitation"] = min(100, total_water/50000*100)
    sdg_engagement["Life on Land"] = min(100, total_biodiversity*10)
    sdg_engagement["Good Health & Wellbeing"] = min(100, total_hs*5)
    sdg_engagement["Decent Work & Economic Growth"] = min(100, total_employee*5)
    sdg_engagement["Peace, Justice & Strong Institutions"] = min(100, total_governance*5)
    sdg_engagement["Sustainable Cities & Communities"] = min(100, total_csr*5)
    sdg_engagement["Partnerships for the Goals"] = min(100, total_csr*5)
    return sdg_engagement

def render_sdg_dashboard():
    st.title("Sustainable Development Goals (SDGs)")
    st.subheader("Company Engagement on All 17 SDGs")
    sdg_engagement = calculate_sdg_engagement()
    cols_per_row = 3
    for i in range(0, len(SDG_LIST), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, sdg in enumerate(SDG_LIST[i:i+cols_per_row]):
            idx = i+j
            progress = sdg_engagement.get(sdg,0)
            color = SDG_COLORS[idx % len(SDG_COLORS)]
            with cols[j]:
                st.markdown(f"""
                <div class='sdg-block' style='background-color:{color}'>
                    <div class='sdg-number'>SDG {idx+1}</div>
                    <div class='sdg-name'>{sdg}</div>
                    <div class='sdg-progress'>Engagement: {progress:.2f}%</div>
                    <progress max="100" value="{progress}" style="width:100%"></progress>
                </div>
                """, unsafe_allow_html=True)

# ---------------------------
# GHG & Energy Dashboards (original)
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
        ["Total Quantity","Scope 1","Scope 2","Scope 3"],
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
        monthly_trend = df.groupby(["Month"])["Quantity"].sum().reset_index()
        st.subheader("Monthly GHG Emissions")
        fig = px.bar(monthly_trend, x="Month", y="Quantity", color_discrete_sequence=["#4db6ac"])
        st.plotly_chart(fig, use_container_width=True)
    if include_data:
        st.subheader("Add GHG Entry")
        with st.form("ghg_form"):
            scope = st.selectbox("Scope", ["Scope 1","Scope 2","Scope 3"])
            activity = st.text_input("Activity")
            sub_activity = st.text_input("Sub-Activity")
            quantity = st.number_input("Quantity", min_value=0.0)
            submitted = st.form_submit_button("Add Entry")
            if submitted:
                new_entry = {"Scope":scope,"Activity":activity,"Sub-Activity":sub_activity,"Quantity":quantity,"Unit":"tCO₂e"}
                st.session_state.entries = pd.concat([st.session_state.entries, pd.DataFrame([new_entry])], ignore_index=True)
                st.success("GHG entry added successfully!")

def render_energy_dashboard():
    st.subheader("Energy Dashboard")
    st.info("Energy dashboard under construction. Add renewable energy entries below.")
    with st.form("energy_form"):
        source = st.selectbox("Source", ["Solar","Wind","Biogas","Purchased Green Energy"])
        energy_kwh = st.number_input("Energy (kWh)", min_value=0.0)
        submitted = st.form_submit_button("Add Entry")
        if submitted:
            new_entry = {"Source":source,"Energy_kWh":energy_kwh,"Type":"Renewable"}
            st.session_state.renewable_entries = pd.concat([st.session_state.renewable_entries, pd.DataFrame([new_entry])], ignore_index=True)
            st.success("Energy entry added successfully!")

# ---------------------------
# Input Forms for other dashboards
# ---------------------------
def render_entries_form(df_key, fields, title):
    st.subheader(title)
    with st.form(key=f"{df_key}_form"):
        entry = {}
        for field, ftype in fields.items():
            if ftype=="text":
                entry[field] = st.text_input(field)
            elif ftype=="number":
                entry[field] = st.number_input(field, min_value=0.0)
        submitted = st.form_submit_button("Add Entry")
        if submitted:
            st.session_state[df_key] = pd.concat([st.session_state[df_key], pd.DataFrame([entry])], ignore_index=True)
            st.success("Entry added successfully!")

# ---------------------------
# Render pages
# ---------------------------
if st.session_state.page == "Home":
    st.title("EinTrust Sustainability Dashboard")
    st.info("Select a section from sidebar to explore.")
elif st.session_state.page == "GHG":
    render_ghg_dashboard()
elif st.session_state.page == "Energy":
    render_energy_dashboard()
elif st.session_state.page == "Water":
    render_entries_form("water_entries", {"Activity":"text","Quantity":"number"},"Water Entries")
elif st.session_state.page == "Waste":
    render_entries_form("waste_entries", {"Waste Type":"text","Quantity":"number"},"Waste Entries")
elif st.session_state.page == "Biodiversity":
    render_entries_form("biodiversity_entries", {"Project":"text"},"Biodiversity Projects")
elif st.session_state.page == "Employee":
    render_entries_form("employee_entries", {"Employee Name":"text"},"Employee Records")
elif st.session_state.page == "Health & Safety":
    render_entries_form("health_safety_entries", {"Safety Activity":"text"},"Health & Safety Records")
elif st.session_state.page == "CSR":
    render_entries_form("csr_entries", {"CSR Activity":"text"},"CSR Activities")
elif st.session_state.page in ["Board","Policies","Compliance","Risk Management"]:
    render_entries_form("governance_entries", {"Activity":"text"},f"{st.session_state.page} Entries")
elif st.session_state.page == "SDG":
    render_sdg_dashboard()
else:
    st.subheader(f"{st.session_state.page} section")
    st.info("This section is under development. Please select other pages from sidebar.")
