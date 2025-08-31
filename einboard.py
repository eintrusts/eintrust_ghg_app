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
    display: inline-block; width: 100%; min-height: 150px;
    text-align: left; color: white;
}
.sdg-number { font-weight: 700; font-size: 20px; }
.sdg-name { font-size: 16px; margin-bottom: 5px; }
.sdg-percent { font-size: 14px; margin-bottom: 10px; }
.sdg-slider { width: 100%; }

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

# ---------------------------
# Constants
# ---------------------------
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
# SDG Dashboard
# ---------------------------
def render_sdg_dashboard():
    st.title("Sustainable Development Goals (SDGs)")
    st.subheader("Company Engagement by SDG")

    num_cols = 4
    rows = (len(SDG_LIST) + num_cols - 1) // num_cols
    idx = 0
    for r in range(rows):
        cols = st.columns(num_cols)
        for c in range(num_cols):
            if idx >= len(SDG_LIST):
                break
            sdg_name = SDG_LIST[idx]
            sdg_color = SDG_COLORS[idx]
            sdg_number = idx + 1

            engagement = st.session_state.sdg_engagement.get(sdg_number, 0)
            with cols[c]:
                st.markdown(f"""
                <div class='sdg-card' style='background-color:{sdg_color}'>
                    <div class='sdg-number'>SDG {sdg_number}</div>
                    <div class='sdg-name'>{sdg_name}</div>
                    <div class='sdg-percent'>Engagement: {engagement}%</div>
                </div>
                """, unsafe_allow_html=True)
                engagement = st.slider("", 0, 100, value=engagement, key=f"sdg{sdg_number}", label_visibility="collapsed")
                st.session_state.sdg_engagement[sdg_number] = engagement
            idx += 1

# ---------------------------
# Employee Page
# ---------------------------
def render_employee_page():
    st.title("Employee Information")
    
    st.markdown("### Workforce Profile")
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    with col1: st.write("Number of Employees")
    with col2: permanent_male = st.number_input("Permanent Male", min_value=0, value=0, key="perm_male")
    with col3: permanent_female = st.number_input("Permanent Female", min_value=0, value=0, key="perm_female")
    with col4: temporary_male = st.number_input("Temporary Male", min_value=0, value=0, key="temp_male")
    with col5: temporary_female = st.number_input("Temporary Female", min_value=0, value=0, key="temp_female")
    with col6: total_male = permanent_male + temporary_male; st.write(f"Total Male: {total_male}")
    with col7: total_female = permanent_female + temporary_female; st.write(f"Total Female: {total_female}")
    
    st.markdown("### Age-wise Distribution")
    age_col1, age_col2, age_col3, age_col4, age_col5, age_col6, age_col7 = st.columns(7)
    with age_col1: st.write("<30")
    with age_col2: under30_male = st.number_input("Under 30 Male", min_value=0, value=0, key="u30_male")
    with age_col3: under30_female = st.number_input("Under 30 Female", min_value=0, value=0, key="u30_female")
    with age_col4: age30_50_male = st.number_input("30-50 Male", min_value=0, value=0, key="30_50_male")
    with age_col5: age30_50_female = st.number_input("30-50 Female", min_value=0, value=0, key="30_50_female")
    with age_col6: above50_male = st.number_input(">50 Male", min_value=0, value=0, key="above50_male")
    with age_col7: above50_female = st.number_input(">50 Female", min_value=0, value=0, key="above50_female")
    
    st.markdown("### Diversity and Inclusion")
    div_male = st.number_input("Employees from marginalized communities Male", min_value=0, value=0, key="div_male")
    div_female = st.number_input("Employees from marginalized communities Female", min_value=0, value=0, key="div_female")
    st.write(f"Total: {div_male + div_female}")
    
    pwd_male = st.number_input("Persons with Disabilities Male", min_value=0, value=0, key="pwd_male")
    pwd_female = st.number_input("Persons with Disabilities Female", min_value=0, value=0, key="pwd_female")
    st.write(f"Total: {pwd_male + pwd_female}")
    
    women_leadership = st.number_input("Women in Leadership", min_value=0, value=0, key="women_leadership")
    policy_diversity = st.text_input("Policy on Diversity & Inclusion (Upload/Link)", value="", key="policy_diversity")
    
    st.markdown("### Retention & Turnover")
    avg_tenure = st.number_input("Average Tenure of Employees (years)", min_value=0.0, value=0.0, key="avg_tenure")
    turnover_rate = st.number_input("Employee Turnover Rate (%)", min_value=0.0, value=0.0, key="turnover_rate")
    
    st.markdown("### Training & Development")
    training_type = st.text_input("Type of Trainings Provided", value="", key="training_type")
    trained_male = st.number_input("Number of Employees Trained Male", min_value=0, value=0, key="trained_male")
    trained_female = st.number_input("Number of Employees Trained Female", min_value=0, value=0, key="trained_female")
    st.write(f"Total Trained: {trained_male + trained_female}")
    total_training_hours = st.number_input("Total Training Hours", min_value=0, value=0, key="total_training_hours")
    
    st.markdown("### Employee Welfare & Engagement")
    engagement_survey = st.checkbox("Employee Engagement Survey Done?", key="eng_survey")
    parental_leave = st.checkbox("Parental Leave Policy in Place?", key="parental_leave")
    
    st.markdown("### Benefits Provided")
    pf_male = st.checkbox("PF/Retirement Benefit Male", key="pf_male")
    pf_female = st.checkbox("PF/Retirement Benefit Female", key="pf_female")
    health_male = st.checkbox("Health Insurance Male", key="health_male")
    health_female = st.checkbox("Health Insurance Female", key="health_female")
    paid_leave_male = st.checkbox("Paid Leave Male", key="paid_leave_male")
    paid_leave_female = st.checkbox("Paid Leave Female", key="paid_leave_female")

# ---------------------------
# Render Pages
# ---------------------------
if st.session_state.page == "Home":
    st.title("EinTrust Sustainability Dashboard")
elif st.session_state.page == "GHG":
    st.subheader("GHG Emissions page under construction")
elif st.session_state.page == "Energy":
    st.subheader("Energy page under construction")
elif st.session_state.page == "Employee":
    render_employee_page()
elif st.session_state.page == "SDG":
    render_sdg_dashboard()
else:
    st.subheader(f"{st.session_state.page} section")
    st.info("This section is under development. Please select other pages from sidebar.")
