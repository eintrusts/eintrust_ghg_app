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
    # initialize Employee DataFrame with all fields
    fields = [
        "Permanent Employees","Temporary Employees","Age <30","Age 30-50","Age >50",
        "Employees from marginalized communities","Persons with Disabilities",
        "Women in Leadership","Policy on Diversity and Inclusion","Average Tenure of Employees",
        "Employee Turnover Rate","Type of Trainings","Number of Employees Trained",
        "Total Training Hours","Employee Engagement Survey Done?",
        "Parental Leave Policy","Benefits Provided (PF/Health Insurance/Paid Leave)"
    ]
    rows = []
    for f in fields:
        rows.append({"Field": f,"Male":0,"Female":0,"Total":0,"Information":"","Relevant Frameworks":""})
    st.session_state.employee_data = pd.DataFrame(rows)

# ---------------------------
# Employee Page
# ---------------------------
def render_employee_dashboard():
    st.title("Employee Data & Workforce Profile")
    df = st.session_state.employee_data.copy()

    st.subheader("Enter Male/Female counts and additional info")
    for idx, row in df.iterrows():
        cols = st.columns(5)
        cols[0].markdown(f"**{row['Field']}**")
        male_val = cols[1].number_input("Male", min_value=0, value=int(row["Male"]), key=f"{row['Field']}_M")
        female_val = cols[2].number_input("Female", min_value=0, value=int(row["Female"]), key=f"{row['Field']}_F")
        total_val = male_val + female_val
        cols[3].markdown(f"**Total: {total_val}**")
        info_val = cols[4].text_input("Information", value=row["Information"], key=f"{row['Field']}_Info")
        df.at[idx,"Male"]=male_val
        df.at[idx,"Female"]=female_val
        df.at[idx,"Total"]=total_val
        df.at[idx,"Information"]=info_val

    st.session_state.employee_data = df
    st.dataframe(df)

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Employee Data CSV", csv, "employee_data.csv", "text/csv")

# ---------------------------
# Placeholder / Perfect existing pages
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
    for col, label, value in zip([c1,c2,c3,c4],["Total Quantity","Scope 1","Scope 2","Scope 3"],
                                 [kpis['Total Quantity'],kpis['Scope 1'],kpis['Scope 2'],kpis['Scope 3']]):
        col.markdown(f"""
        <div class='kpi'>
            <div class='kpi-value'>{format_indian(value)}</div>
            <div class='kpi-unit'>{kpis['Unit']}</div>
            <div class='kpi-label'>{label.lower()}</div>
        </div>
        """, unsafe_allow_html=True)
    st.info("GHG Dashboard content continues here...")  # placeholder

def render_energy_dashboard(include_input=True, show_chart=True):
    st.subheader("Energy Dashboard placeholder")
    st.info("Energy dashboard content here...")  # placeholder

def render_sdg_dashboard():
    st.subheader("SDG Dashboard placeholder")
    st.info("SDG content here...")  # placeholder

# ---------------------------
# Render Pages
# ---------------------------
if st.session_state.page == "Home":
    st.title("EinTrust Sustainability Dashboard")
    render_ghg_dashboard(include_data=False, show_chart=False)
    render_energy_dashboard(include_input=False, show_chart=False)
elif st.session_state.page == "GHG":
    render_ghg_dashboard(include_data=True, show_chart=True)
elif st.session_state.page == "Energy":
    render_energy_dashboard(include_input=True, show_chart=True)
elif st.session_state.page == "Employee":
    render_employee_dashboard()
elif st.session_state.page == "SDG":
    render_sdg_dashboard()
else:
    st.subheader(f"{st.session_state.page} section")
    st.info("This section is under development. Please select other pages from sidebar.")
