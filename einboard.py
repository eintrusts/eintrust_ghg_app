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
# Employee Dashboard (fixed keys)
# ---------------------------
def render_employee_dashboard():
    st.title("Employee Data & ESG Reporting")

    # --- Workforce Profile ---
    st.subheader("Workforce Profile")
    st.markdown("**Number of Employees** (Permanent / Temporary / Total) – BRSR, GRI 2-7, SASB")
    if "num_employees" not in st.session_state.employee_data:
        st.session_state.employee_data["num_employees"] = pd.DataFrame({
            "": ["Male", "Female", "Total"],
            "Permanent": [0,0,0],
            "Temporary": [0,0,0],
            "Total": [0,0,0]
        })
    st.session_state.employee_data["num_employees"] = st.data_editor(
        st.session_state.employee_data["num_employees"], key="num_employees_editor"
    )

    st.markdown("**Age-wise Distribution** (<30 / 30-50 / >50) – BRSR, GRI 2-7")
    if "age_distribution" not in st.session_state.employee_data:
        st.session_state.employee_data["age_distribution"] = pd.DataFrame({
            "Age Group": ["<30","30-50",">50"],
            "Male": [0,0,0],
            "Female": [0,0,0]
        })
    st.session_state.employee_data["age_distribution"] = st.data_editor(
        st.session_state.employee_data["age_distribution"], key="age_distribution_editor"
    )

    st.markdown("**Diversity and Inclusion**")
    st.markdown("Employees from marginalized communities – BRSR P5, GRI 405")
    if "marginalized" not in st.session_state.employee_data:
        st.session_state.employee_data["marginalized"] = pd.DataFrame({
            "": ["Male","Female","Total"], "Count":[0,0,0]
        })
    st.session_state.employee_data["marginalized"] = st.data_editor(
        st.session_state.employee_data["marginalized"], key="marginalized_editor"
    )

    st.markdown("Persons with Disabilities – BRSR P5")
    if "pwd" not in st.session_state.employee_data:
        st.session_state.employee_data["pwd"] = pd.DataFrame({
            "": ["Male","Female","Total"], "Count":[0,0,0]
        })
    st.session_state.employee_data["pwd"] = st.data_editor(
        st.session_state.employee_data["pwd"], key="pwd_editor"
    )

    st.markdown("Women in Leadership – BRSR P5, GRI 405")
    if "women_leadership" not in st.session_state.employee_data:
        st.session_state.employee_data["women_leadership"] = pd.DataFrame({"Position":["Total"],"Count":[0]})
    st.session_state.employee_data["women_leadership"] = st.data_editor(
        st.session_state.employee_data["women_leadership"], key="women_leadership_editor"
    )

    st.markdown("Policy on Diversity and Inclusion – BRSR P5, GRI 405")
    st.text_input("Upload / Share link of Policy Here", key="diversity_policy")

    # --- Retention & Turnover ---
    st.subheader("Retention & Turnover")
    st.text_input("Average Tenure of Employees", key="avg_tenure")
    st.text_input("Employee Turnover Rate", key="turnover_rate")

    # --- Training & Development ---
    st.subheader("Training and Development")
    st.text_input("Type of Trainings", key="training_type")
    if "employees_trained" not in st.session_state.employee_data:
        st.session_state.employee_data["employees_trained"] = pd.DataFrame({
            "": ["Male","Female","Total"], "Count":[0,0,0]
        })
    st.session_state.employee_data["employees_trained"] = st.data_editor(
        st.session_state.employee_data["employees_trained"], key="employees_trained_editor"
    )
    st.text_input("Total Training Hours", key="training_hours")

    # --- Employee Welfare & Engagement ---
    st.subheader("Employee Welfare & Engagement")
    st.selectbox("Employee Engagement Survey Done?", ["Yes","No"], key="engagement_survey")
    st.text_input("Parental Leave Policy", key="parental_leave")
    if "benefits" not in st.session_state.employee_data:
        st.session_state.employee_data["benefits"] = pd.DataFrame({
            "Benefit":["PF/Retirement Benefit","Health Insurance","Paid Leave Benefits"],
            "Male":[0,0,0],
            "Female":[0,0,0]
        })
    st.session_state.employee_data["benefits"] = st.data_editor(
        st.session_state.employee_data["benefits"], key="benefits_editor"
    )
