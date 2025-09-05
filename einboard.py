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
.kpi { background: linear-gradient(145deg, #12131a, #1a1b22); padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.5); margin-bottom: 10px; min-height: 120px; display: flex; flex-direction: column; justify-content: center; align-items: center; transition: transform 0.2s, box-shadow 0.2s; }
.kpi:hover { transform: scale(1.05); box-shadow: 0 8px 20px rgba(0,0,0,0.6); }
.kpi-value { font-size: 28px; font-weight: 700; color: #ffffff; margin-bottom: 5px; }
.kpi-unit { font-size: 16px; font-weight: 500; color: #cfd8dc; margin-bottom: 5px; }
.kpi-label { font-size: 14px; color: #cfd8dc; letter-spacing: 0.5px; }
.sdg-card { border-radius: 10px; padding: 15px; margin: 8px; display: inline-block; width: 100%; min-height: 110px; text-align: left; color: white; }
.sdg-number { font-weight: 700; font-size: 20px; }
.sdg-name { font-size: 16px; margin-bottom: 5px; }
.sdg-percent { font-size: 14px; }
@media (min-width: 768px) { .sdg-card { width: 220px; display: inline-block; } }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Sidebar Navigation
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
# Initialize Data Stores
# ---------------------------
if "entries" not in st.session_state:
    st.session_state.entries = pd.DataFrame(columns=[
        "Scope","Activity","Sub-Activity","Specific Item","Quantity","Unit","Emissions_kgCO2e"
    ])
if "renewable_entries" not in st.session_state:
    st.session_state.renewable_entries = pd.DataFrame(columns=["Source","Location","Month","Energy_kWh","CO2e_kg","Type"])
if "sdg_engagement" not in st.session_state:
    st.session_state.sdg_engagement = {i:0 for i in range(1,18)}

# Environment
if "water_data" not in st.session_state:
    st.session_state.water_data = pd.DataFrame(columns=["Location","Source","Month","Quantity_m3","Cost_INR"])
if "advanced_water_data" not in st.session_state:
    st.session_state.advanced_water_data = pd.DataFrame(columns=[
        "Location","Month","Rainwater_Harvested_m3","Water_Recycled_m3","Treatment_Before_Discharge","STP_ETP_Capacity_kL_day"
    ])
if "waste_data" not in st.session_state:
    st.session_state.waste_data = pd.DataFrame(columns=["Type","Quantity_kg","Disposal_Method","Emissions_kgCO2e"])
if "biodiversity_data" not in st.session_state:
    st.session_state.biodiversity_data = pd.DataFrame(columns=["Project","Species_Impacted","Area_ha","Status"])

# Social
if "employee_data" not in st.session_state:
    st.session_state.employee_data = pd.DataFrame(columns=["Department","Total_Employees","Permanent","Contractual"])
if "health_data" not in st.session_state:
    st.session_state.health_data = pd.DataFrame(columns=["Activity","Total_Participants","Incidents"])
if "csr_data" not in st.session_state:
    st.session_state.csr_data = pd.DataFrame(columns=["Project","Budget_INR","Beneficiaries"])

# Governance
if "board_data" not in st.session_state:
    st.session_state.board_data = pd.DataFrame(columns=["Independent","Meetings","Committees"])
if "policy_data" not in st.session_state:
    st.session_state.policy_data = pd.DataFrame(columns=["Policy_Name","Implemented"])
if "compliance_data" not in st.session_state:
    st.session_state.compliance_data = pd.DataFrame(columns=["Regulation","Status"])
if "risk_data" not in st.session_state:
    st.session_state.risk_data = pd.DataFrame(columns=["Risk_Type","Mitigation_Status"])

# ---------------------------
# GHG & Energy pages (unchanged)
# ---------------------------
# Include your previous GHG and Energy pages code here as-is
# ...

# ---------------------------
# Environment Input Pages
# ---------------------------
def render_water_page():
    st.subheader("Water Management")
    df = st.session_state.water_data
    st.metric("Total Water Used (m³)", f"{df['Quantity_m3'].sum():,.0f}" if not df.empty else 0)
    
    with st.form("water_form"):
        location = st.text_input("Location")
        source = st.text_input("Source")
        month = st.selectbox("Month", ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"])
        quantity = st.number_input("Quantity (m³)", min_value=0.0)
        cost = st.number_input("Cost (INR)", min_value=0.0)
        submitted = st.form_submit_button("Add Water Entry")
        if submitted:
            entry = {"Location":location,"Source":source,"Month":month,"Quantity_m3":quantity,"Cost_INR":cost}
            st.session_state.water_data = pd.concat([st.session_state.water_data,pd.DataFrame([entry])],ignore_index=True)
    
    if not st.session_state.water_data.empty:
        st.subheader("Water Entries")
        st.dataframe(st.session_state.water_data, use_container_width=True)

def render_waste_page():
    st.subheader("Waste Management")
    df = st.session_state.waste_data
    with st.form("waste_form"):
        wtype = st.text_input("Waste Type")
        qty = st.number_input("Quantity (kg)", min_value=0.0)
        method = st.selectbox("Disposal Method", ["Landfill","Recycling","Composting"])
        submitted = st.form_submit_button("Add Waste Entry")
        if submitted:
            emissions = qty * {"Landfill":1.0,"Recycling":0.3,"Composting":0.2}[method]
            entry = {"Type":wtype,"Quantity_kg":qty,"Disposal_Method":method,"Emissions_kgCO2e":emissions}
            st.session_state.waste_data = pd.concat([st.session_state.waste_data,pd.DataFrame([entry])],ignore_index=True)
    if not st.session_state.waste_data.empty:
        st.subheader("Waste Entries")
        st.dataframe(st.session_state.waste_data, use_container_width=True)

def render_biodiversity_page():
    st.subheader("Biodiversity Projects")
    df = st.session_state.biodiversity_data
    with st.form("bio_form"):
        project = st.text_input("Project Name")
        species = st.text_input("Species Impacted")
        area = st.number_input("Area (ha)", min_value=0.0)
        status = st.selectbox("Status", ["Ongoing","Completed","Planned"])
        submitted = st.form_submit_button("Add Biodiversity Entry")
        if submitted:
            entry = {"Project":project,"Species_Impacted":species,"Area_ha":area,"Status":status}
            st.session_state.biodiversity_data = pd.concat([st.session_state.biodiversity_data,pd.DataFrame([entry])],ignore_index=True)
    if not st.session_state.biodiversity_data.empty:
        st.subheader("Biodiversity Entries")
        st.dataframe(st.session_state.biodiversity_data, use_container_width=True)

# ---------------------------
# Social Input Pages
# ---------------------------
def render_employee_page():
    st.subheader("Employee Data")
    with st.form("employee_form"):
        dept = st.text_input("Department")
        total = st.number_input("Total Employees", min_value=0)
        perm = st.number_input("Permanent", min_value=0)
        contract = st.number_input("Contractual", min_value=0)
        submitted = st.form_submit_button("Add Employee Data")
        if submitted:
            entry = {"Department":dept,"Total_Employees":total,"Permanent":perm,"Contractual":contract}
            st.session_state.employee_data = pd.concat([st.session_state.employee_data,pd.DataFrame([entry])],ignore_index=True)
    if not st.session_state.employee_data.empty:
        st.subheader("Employee Entries")
        st.dataframe(st.session_state.employee_data, use_container_width=True)

def render_health_page():
    st.subheader("Health & Safety")
    with st.form("health_form"):
        activity = st.text_input("Activity")
        participants = st.number_input("Total Participants", min_value=0)
        incidents = st.number_input("Incidents", min_value=0)
        submitted = st.form_submit_button("Add Health Entry")
        if submitted:
            entry = {"Activity":activity,"Total_Participants":participants,"Incidents":incidents}
            st.session_state.health_data = pd.concat([st.session_state.health_data,pd.DataFrame([entry])],ignore_index=True)
    if not st.session_state.health_data.empty:
        st.subheader("Health Entries")
        st.dataframe(st.session_state.health_data, use_container_width=True)

def render_csr_page():
    st.subheader("CSR Projects")
    with st.form("csr_form"):
        project = st.text_input("Project Name")
        budget = st.number_input("Budget (INR)", min_value=0.0)
        beneficiaries = st.number_input("Beneficiaries", min_value=0)
        submitted = st.form_submit_button("Add CSR Entry")
        if submitted:
            entry = {"Project":project,"Budget_INR":budget,"Beneficiaries":beneficiaries}
            st.session_state.csr_data = pd.concat([st.session_state.csr_data,pd.DataFrame([entry])],ignore_index=True)
    if not st.session_state.csr_data.empty:
        st.subheader("CSR Entries")
        st.dataframe(st.session_state.csr_data, use_container_width=True)

# ---------------------------
# Governance Input Pages
# ---------------------------
def render_board_page():
    st.subheader("Board Information")
    with st.form("board_form"):
        independent = st.number_input("Independent Board Members", min_value=0)
        meetings = st.number_input("Meetings Held", min_value=0)
        committees = st.number_input("Committees Formed", min_value=0)
        submitted = st.form_submit_button("Add Board Entry")
        if submitted:
            entry = {"Independent":independent,"Meetings":meetings,"Committees":committees}
            st.session_state.board_data = pd.concat([st.session_state.board_data,pd.DataFrame([entry])],ignore_index=True)
    if not st.session_state.board_data.empty:
        st.subheader("Board Entries")
        st.dataframe(st.session_state.board_data, use_container_width=True)

def render_policy_page():
    st.subheader("Policies")
    with st.form("policy_form"):
        name = st.text_input("Policy Name")
        implemented = st.selectbox("Implemented", ["Yes","No"])
        submitted = st.form_submit_button("Add Policy Entry")
        if submitted:
            entry = {"Policy_Name":name,"Implemented":implemented}
            st.session_state.policy_data = pd.concat([st.session_state.policy_data,pd.DataFrame([entry])],ignore_index=True)
    if not st.session_state.policy_data.empty:
        st.subheader("Policy Entries")
        st.dataframe(st.session_state.policy_data, use_container_width=True)

def render_compliance_page():
    st.subheader("Compliance")
    with st.form("compliance_form"):
        regulation = st.text_input("Regulation")
        status = st.selectbox("Status", ["Compliant","Non-Compliant"])
        submitted = st.form_submit_button("Add Compliance Entry")
        if submitted:
            entry = {"Regulation":regulation,"Status":status}
            st.session_state.compliance_data = pd.concat([st.session_state.compliance_data,pd.DataFrame([entry])],ignore_index=True)
    if not st.session_state.compliance_data.empty:
        st.subheader("Compliance Entries")
        st.dataframe(st.session_state.compliance_data, use_container_width=True)

def render_risk_page():
    st.subheader("Risk Management")
    with st.form("risk_form"):
        risk_type = st.text_input("Risk Type")
        mitigation = st.selectbox("Mitigation Status", ["Implemented","Planned","None"])
        submitted = st.form_submit_button("Add Risk Entry")
        if submitted:
            entry = {"Risk_Type":risk_type,"Mitigation_Status":mitigation}
            st.session_state.risk_data = pd.concat([st.session_state.risk_data,pd.DataFrame([entry])],ignore_index=True)
    if not st.session_state.risk_data.empty:
        st.subheader("Risk Entries")
        st.dataframe(st.session_state.risk_data, use_container_width=True)

# ---------------------------
# Report Pages
# ---------------------------
def generate_report_df():
    report = {}
    # BRSR KPIs example mapping
    report["BRSR"] = {
        "Environment: Total Water Used (m³)": st.session_state.water_data['Quantity_m3'].sum() if not st.session_state.water_data.empty else 0,
        "Environment: Total Waste (kg)": st.session_state.waste_data['Quantity_kg'].sum() if not st.session_state.waste_data.empty else 0,
        "Social: Total Employees": st.session_state.employee_data['Total_Employees'].sum() if not st.session_state.employee_data.empty else 0,
        "Governance: Independent Board Members": st.session_state.board_data['Independent'].sum() if not st.session_state.board_data.empty else 0
    }
    # GRI, CDP, TCFD mapping similar
    report["GRI"] = report["BRSR"].copy()
    report["CDP"] = report["BRSR"].copy()
    report["TCFD"] = report["BRSR"].copy()
    return report

def export_pdf(report_name, df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"{report_name} Report", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    for k, v in df.items():
        pdf.cell(0, 8, f"{k}: {v}", ln=True)
    pdf_file = f"{report_name}.pdf"
    pdf.output(pdf_file)
    st.success(f"{report_name} PDF exported!")

def render_report_page(report_name):
    st.subheader(f"{report_name} Report")
    report_data = generate_report_df()[report_name]
    st.table(pd.DataFrame(list(report_data.items()), columns=["KPI","Value"]))
    if st.button(f"Export {report_name} PDF"):
        export_pdf(report_name, report_data)

# ---------------------------
# Main Page Router
# ---------------------------
page = st.session_state.page

if page == "Home":
    st.title("EinTrust Sustainability Dashboard")
    st.markdown("Welcome! Use the sidebar to navigate through Environmental, Social, Governance sections, SDG, and Reports.")
elif page == "Water":
    render_water_page()
elif page == "Waste":
    render_waste_page()
elif page == "Biodiversity":
    render_biodiversity_page()
elif page == "Employee":
    render_employee_page()
elif page == "Health & Safety":
    render_health_page()
elif page == "CSR":
    render_csr_page()
elif page == "Board":
    render_board_page()
elif page == "Policies":
    render_policy_page()
elif page == "Compliance":
    render_compliance_page()
elif page == "Risk Management":
    render_risk_page()
elif page in ["BRSR","GRI","CDP","TCFD"]:
    render_report_page(page)
else:
    st.write("Page not implemented yet.")

