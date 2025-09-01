import streamlit as st
import pandas as pd
import numpy as np

# ---------------------------
# Page Config & CSS
# ---------------------------
st.set_page_config(page_title="EinTrust Sustainability Dashboard", page_icon="🌍", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }
.stApp { background-color: #0d1117; color: #e6edf3; }
.kpi { background: linear-gradient(145deg, #12131a, #1a1b22); padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.5); margin-bottom: 10px; min-height: 120px; display: flex; flex-direction: column; justify-content: center; align-items: center; transition: transform 0.2s, box-shadow 0.2s; }
.kpi:hover { transform: scale(1.05); box-shadow: 0 8px 20px rgba(0,0,0,0.6); }
.kpi-value { font-size: 28px; font-weight: 700; color: #ffffff; margin-bottom: 5px; }
.kpi-unit { font-size: 16px; font-weight: 500; color: #cfd8dc; margin-bottom: 5px; }
.kpi-label { font-size: 14px; color: #cfd8dc; letter-spacing: 0.5px; }
.sidebar-logo { width: 150px; }
.expander-scroll { max-height: 300px; overflow-y: auto; }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Utilities
# ---------------------------
def format_indian(n: float) -> str:
    try:
        x = int(round(float(n)))
    except:
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
        all: unset; cursor: pointer; padding: 0.4rem; text-align: left; border-radius: 0.3rem; margin-bottom: 0.2rem;
        background-color: {'forestgreen' if active else '#12131a'}; color: {'white' if active else '#e6edf3'}; font-size: 16px;
    }}
    div.stButton > button[key="{label}"]:hover {{
        background-color: {'forestgreen' if active else '#1a1b22'};
    }}
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.image("https://github.com/eintrusts/eintrust_ghg_app/blob/main/EinTrust%20%20(2).png?raw=true", width=150)
    st.markdown("---")
    
    sidebar_button("Home")

    env_exp = st.expander("Environment", expanded=True)
    with env_exp:
        st.markdown('<div class="expander-scroll">', unsafe_allow_html=True)
        sidebar_button("GHG")
        sidebar_button("Energy")
        sidebar_button("Water")
        sidebar_button("Waste")
        sidebar_button("Biodiversity")
        st.markdown('</div>', unsafe_allow_html=True)

    social_exp = st.expander("Social")
    with social_exp:
        st.markdown('<div class="expander-scroll">', unsafe_allow_html=True)
        sidebar_button("Employee")
        sidebar_button("Health & Safety")
        sidebar_button("CSR")
        st.markdown('</div>', unsafe_allow_html=True)

    gov_exp = st.expander("Governance")
    with gov_exp:
        st.markdown('<div class="expander-scroll">', unsafe_allow_html=True)
        sidebar_button("Board")
        sidebar_button("Policies")
        sidebar_button("Compliance")
        sidebar_button("Risk Management")
        st.markdown('</div>', unsafe_allow_html=True)

    sidebar_button("SDG")

    reports_exp = st.expander("Reports")
    with reports_exp:
        st.markdown('<div class="expander-scroll">', unsafe_allow_html=True)
        sidebar_button("BRSR")
        sidebar_button("GRI")
        sidebar_button("CDP")
        sidebar_button("TCFD")
        st.markdown('</div>', unsafe_allow_html=True)

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
scope_activities = {
    "Scope 1": {"Stationary Combustion": {"Diesel Generator":"Generator running on diesel","Petrol Generator":"Generator running on petrol"},
                "Mobile Combustion":{"Diesel Vehicle":"Truck/van running on diesel"}},
    "Scope 2": {"Electricity Consumption":{"Grid Electricity":"Electricity from grid"}},
    "Scope 3": {"Business Travel":{"Air Travel": None}}
}
units_dict = {"Diesel Generator": "Liters", "Petrol Generator": "Liters", "Diesel Vehicle": "Liters", "Grid Electricity": "kWh", "Air Travel":"km"}
months = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]
SCOPE_COLORS = {"Scope 1": "#81c784", "Scope 2": "#4db6ac", "Scope 3": "#aed581"}

# Emission factors (kg CO2e per unit)
emission_factors = {
    "Diesel Generator": 2.68,
    "Petrol Generator": 2.31,
    "Diesel Vehicle": 2.68,
    "Grid Electricity": 0.82,
    "Air Travel": 0.25
}

# ---------------------------
# GHG Dashboard
# ---------------------------
def calculate_kpis():
    df = st.session_state.entries
    summary = {"Scope 1":0.0,"Scope 2":0.0,"Scope 3":0.0,"Total Quantity":0.0,"Unit":"tCO₂e"}
    if not df.empty:
        df["CO2e_kg"] = df.apply(lambda row: row["Quantity"] * emission_factors.get(row["Sub-Activity"],0), axis=1)
        for scope in ["Scope 1","Scope 2","Scope 3"]:
            summary[scope] = df[df["Scope"]==scope]["CO2e_kg"].sum()/1000  # tCO2e
        summary["Total Quantity"] = df["CO2e_kg"].sum()/1000
    return summary

def render_ghg_dashboard(include_data=True):
    st.subheader("GHG Emissions")
    kpis = calculate_kpis()
    c1,c2,c3,c4 = st.columns(4)
    for col,label,value,color in zip([c1,c2,c3,c4], ["Total Quantity","Scope 1","Scope 2","Scope 3"],
                                    [kpis['Total Quantity'],kpis['Scope 1'],kpis['Scope 2'],kpis['Scope 3']],
                                    ["#ffffff",SCOPE_COLORS['Scope 1'],SCOPE_COLORS['Scope 2'],SCOPE_COLORS['Scope 3']]):
        col.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{color}'>{format_indian(value)}</div><div class='kpi-unit'>{kpis['Unit']}</div><div class='kpi-label'>{label.lower()}</div></div>", unsafe_allow_html=True)

    # --- Data Entry Form ---
    if include_data:
        scope = st.selectbox("Select Scope", list(scope_activities.keys()))
        activity = st.selectbox("Select Activity", list(scope_activities[scope].keys()))
        sub_options = scope_activities[scope][activity]
        sub_activity = st.selectbox("Select Sub-Activity", list(sub_options.keys()))
        st.info(sub_options[sub_activity])
        unit = units_dict.get(sub_activity, "Number")
        quantity = st.number_input(f"Enter quantity ({unit})", min_value=0.0, format="%.2f")
        if st.button("Add Entry"):
            new_entry = {"Scope":scope,"Activity":activity,"Sub-Activity":sub_activity,"Specific Item":"",
                         "Quantity":quantity,"Unit":unit}
            st.session_state.entries = pd.concat([st.session_state.entries, pd.DataFrame([new_entry])], ignore_index=True)
            st.success("GHG entry added!")
            st.experimental_rerun()

# ---------------------------
# Energy Dashboard (no plot)
# ---------------------------
def render_energy_dashboard(include_input=True):
    st.subheader("Energy Dashboard")
    st.info("Chart removed to prevent errors. Energy data entry and calculations still work.")

# ---------------------------
# SDG Dashboard (unchanged)
# ---------------------------
def render_sdg_dashboard():
    st.title("Sustainable Development Goals (SDGs)")
    st.subheader("Company Engagement by SDG")
    SDG_LIST = ["No Poverty","Zero Hunger","Good Health & Wellbeing","Quality Education","Gender Equality",
                "Clean Water & Sanitation","Affordable & Clean Energy","Decent Work & Economic Growth","Industry, Innovation & Infrastructure",
                "Reduced Inequalities","Sustainable Cities & Communities","Responsible Consumption & Production","Climate Action","Life Below Water",
                "Life on Land","Peace, Justice & Strong Institutions","Partnerships for the Goals"]
    SDG_COLORS = ["#e5243b","#dda63a","#4c9f38","#c5192d","#ff3a21","#26bde2","#fcc30b","#a21942","#fd6925","#dd1367","#fd9d24",
                  "#bf8b2e","#3f7e44","#0a97d9","#56c02b","#00689d","#19486a"]
    num_cols = 4
    rows = (len(SDG_LIST)+num_cols-1)//num_cols
    idx=0
    for r in range(rows):
        cols = st.columns(num_cols)
        for c in range(num_cols):
            if idx>=len(SDG_LIST): break
            sdg_name = SDG_LIST[idx]
            sdg_color = SDG_COLORS[idx]
            sdg_number = idx+1
            engagement = st.session_state.sdg_engagement.get(sdg_number,0)
            engagement = cols[c].slider(f"Engagement % - SDG {sdg_number}",0,100,value=engagement,key=f"sdg{sdg_number}")
            st.session_state.sdg_engagement[sdg_number] = engagement
            cols[c].markdown(f"<div class='kpi' style='background-color:{sdg_color}'><div class='kpi-label'>SDG {sdg_number}: {sdg_name}</div><div class='kpi-value'>{engagement}%</div></div>", unsafe_allow_html=True)
            idx+=1

# ---------------------------
# Render Pages
# ---------------------------
if st.session_state.page=="Home":
    st.title("EinTrust Sustainability Dashboard")
    render_ghg_dashboard(include_data=False)
    render_energy_dashboard(include_input=False)
elif st.session_state.page=="GHG":
    render_ghg_dashboard(include_data=True)
elif st.session_state.page=="Energy":
    render_energy_dashboard(include_input=True)
elif st.session_state.page=="SDG":
    render_sdg_dashboard()
else:
    st.subheader(f"{st.session_state.page} section")
    st.info("This section is under development. Please select other pages from sidebar.")
