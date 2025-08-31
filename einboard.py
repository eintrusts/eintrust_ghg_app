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
    st.session_state.employee_data = pd.DataFrame(columns=[
        "Category","Sub-Category","Male","Female","Total","Unit/Note"
    ])

# ---------------------------
# Constants
# ---------------------------
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
# Employee Dashboard
# ---------------------------
def render_employee_dashboard():
    st.subheader("Employee Data")
    
    df = st.session_state.employee_data.copy()
    st.info("Fill employee data. Total = Male + Female. All data saved in session.")

    categories = [
        "Workforce Profile","Age-wise Distribution","Diversity & Inclusion",
        "Retention & Turnover","Training & Development","Employee Welfare & Engagement"
    ]
    
    for cat in categories:
        with st.expander(cat, expanded=True):
            sub_cat = st.text_input(f"Sub-Category under {cat}", key=f"sub_{cat}")
            male = st.number_input(f"Male count ({cat})", min_value=0, key=f"male_{cat}")
            female = st.number_input(f"Female count ({cat})", min_value=0, key=f"female_{cat}")
            total = male + female
            unit = st.text_input(f"Unit/Note ({cat})", key=f"unit_{cat}")
            
            if st.button(f"Add/Update {cat}"):
                idx = df[df["Category"]==cat].index
                if len(idx)>0:
                    df.loc[idx[0], ["Sub-Category","Male","Female","Total","Unit/Note"]] = [sub_cat, male, female, total, unit]
                else:
                    df = pd.concat([df, pd.DataFrame([{
                        "Category": cat, "Sub-Category": sub_cat,
                        "Male": male, "Female": female, "Total": total,
                        "Unit/Note": unit
                    }])], ignore_index=True)
                
                st.session_state.employee_data = df
                st.success(f"{cat} updated successfully!")

    if not df.empty:
        st.subheader("All Employee Data")
        st.dataframe(df)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Employee Data as CSV", csv, "employee_data.csv","text/csv")

# ---------------------------
# Render Pages
# ---------------------------
if st.session_state.page == "Home":
    st.title("EinTrust Sustainability Dashboard")
    st.info("Select pages from the sidebar to navigate.")
elif st.session_state.page == "GHG":
    st.subheader("GHG Dashboard")
    st.info("GHG dashboard under development...")
elif st.session_state.page == "Energy":
    st.subheader("Energy Dashboard")
    st.info("Energy dashboard under development...")
elif st.session_state.page == "Employee":
    render_employee_dashboard()
elif st.session_state.page == "SDG":
    st.subheader("SDG Dashboard")
    st.info("SDG dashboard under development...")
else:
    st.subheader(f"{st.session_state.page} section")
    st.info("This section is under development. Please select other pages from sidebar.")
