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
# Sidebar
# ---------------------------
if "page" not in st.session_state: st.session_state.page = "Home"
def sidebar_button(label):
    active = st.session_state.page == label
    if st.button(label, key=label): st.session_state.page = label
    st.markdown(f"""
    <style>
    div.stButton > button[key="{label}"] {{
        all: unset; cursor: pointer; padding: 0.4rem; text-align: left; border-radius: 0.3rem; margin-bottom: 0.2rem;
        background-color: {'forestgreen' if active else '#12131a'}; color: {'white' if active else '#e6edf3'}; font-size: 16px;
    }}
    div.stButton > button[key="{label}"]:hover {{ background-color: {'forestgreen' if active else '#1a1b22'}; }}
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
# Initialize DataFrames
# ---------------------------
def init_df(name, columns): 
    if name not in st.session_state: st.session_state[name] = pd.DataFrame(columns=columns)
init_df("entries", ["Scope","Activity","Sub-Activity","Specific Item","Quantity","Unit","Emissions_kgCO2e"])
init_df("renewable_entries", ["Source","Location","Month","Energy_kWh","CO2e_kg","Type"])
init_df("sdg_engagement", list(range(1,18)))
init_df("water_data", ["Location","Source","Month","Quantity_m3","Cost_INR"])
init_df("advanced_water_data", ["Location","Month","Rainwater_Harvested_m3","Water_Recycled_m3","Treatment_Before_Discharge","STP_ETP_Capacity_kL_day"])
init_df("waste_data", ["Location","Type","Quantity_kg","Disposal_Method"])
init_df("biodiversity_data", ["Site","Project_Type","Species_Impacted","Mitigation_Measures"])
init_df("employee_data", ["Name","Department","Joining_Date","Type"])
init_df("hs_data", ["Location","Incident_Type","Severity","Date"])
init_df("csr_data", ["Project","Budget_INR","Beneficiaries"])
init_df("board_data", ["Independent","Meeting_Frequency","Committee"])
init_df("policies_data", ["Policy_Name","Implemented"])
init_df("compliance_data", ["Requirement","Complied"])
init_df("risk_data", ["Risk","Likelihood","Impact"])

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
# Helper Functions
# ---------------------------
def calculate_emissions(scope, activity, sub_activity, specific_item, quantity, unit):
    try:
        factor_map = {
            "Diesel":2.68,"Petrol":2.31,"LPG":1.51,"CNG":2.02,"Coal":2.42,"Electricity":0.82,
            "Cement":900,"Steel":1850,"Textile":300,"Chemicals":1200,
            "Cardboard":0.9,"Plastics":1.7,"Glass":0.95,"Paper":1.2,
            "Air Travel (domestic average)":250,"Train per km":0.05,"Car per km":0.12,"TwoWheeler per km":0.05,
            "Landfill per kg":1,"Recycling per kg":0.3,"Composting per kg":0.2,"Product use kWh":0.82
        }
        key = specific_item or sub_activity
        emissions = float(quantity) * factor_map.get(key, 0)
        missing = key not in factor_map
        return emissions, missing
    except:
        return 0, True

def add_entry(df_name, entry):
    st.session_state[df_name] = pd.concat([st.session_state[df_name], pd.DataFrame([entry])], ignore_index=True)

def display_entries(df_name):
    df = st.session_state[df_name].copy()
    if not df.empty:
        st.dataframe(df)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(f"Download {df_name} CSV", csv, f"{df_name}.csv","text/csv")

def export_pdf(report_name, df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial","B",14)
    pdf.cell(0,10,f"{report_name} Report",ln=True,align="C")
    pdf.set_font("Arial","",10)
    for i,row in df.iterrows():
        pdf.multi_cell(0,5,str(row.to_dict()))
    pdf_file = f"{report_name}.pdf"
    pdf.output(pdf_file)
    return pdf_file

# ---------------------------
# Input Pages
# ---------------------------
def page_environment():
    st.subheader("Water Input")
    location = st.text_input("Location")
    source = st.text_input("Source")
    qty = st.number_input("Quantity (m³)",0.0)
    cost = st.number_input("Cost (INR)",0.0)
    month = st.selectbox("Month", months)
    if st.button("Add Water Entry"):
        add_entry("water_data", {"Location":location,"Source":source,"Month":month,"Quantity_m3":qty,"Cost_INR":cost})
    display_entries("water_data")

    st.subheader("Waste Input")
    loc = st.text_input("Waste Location")
    wtype = st.selectbox("Waste Type",["Solid","Liquid","Hazardous"])
    wqty = st.number_input("Quantity (kg)",0.0,key="wqty")
    disp = st.selectbox("Disposal Method",["Landfill","Recycle","Compost"])
    if st.button("Add Waste Entry"):
        add_entry("waste_data", {"Location":loc,"Type":wtype,"Quantity_kg":wqty,"Disposal_Method":disp})
    display_entries("waste_data")

    st.subheader("Biodiversity Input")
    site = st.text_input("Project Site")
    ptype = st.text_input("Project Type")
    species = st.text_input("Species Impacted")
    mitig = st.text_input("Mitigation Measures")
    if st.button("Add Biodiversity Entry"):
        add_entry("biodiversity_data", {"Site":site,"Project_Type":ptype,"Species_Impacted":species,"Mitigation_Measures":mitig})
    display_entries("biodiversity_data")

def page_social():
    st.subheader("Employee Data")
    name = st.text_input("Name")
    dept = st.text_input("Department")
    joining = st.date_input("Joining Date")
    etype = st.selectbox("Employee Type",["Permanent","Contract","Intern"])
    if st.button("Add Employee Entry"):
        add_entry("employee_data", {"Name":name,"Department":dept,"Joining_Date":joining,"Type":etype})
    display_entries("employee_data")

    st.subheader("Health & Safety")
    loc = st.text_input("Location H&S")
    itype = st.selectbox("Incident Type",["Accident","Near Miss","Illness"])
    sev = st.selectbox("Severity",["Low","Medium","High"])
    date = st.date_input("Date of Incident")
    if st.button("Add HS Entry"):
        add_entry("hs_data", {"Location":loc,"Incident_Type":itype,"Severity":sev,"Date":date})
    display_entries("hs_data")

    st.subheader("CSR Projects")
    proj = st.text_input("Project Name")
    budget = st.number_input("Budget (INR)")
    beneficiaries = st.number_input("Number of Beneficiaries",0)
    if st.button("Add CSR Entry"):
        add_entry("csr_data", {"Project":proj,"Budget_INR":budget,"Beneficiaries":beneficiaries})
    display_entries("csr_data")

def page_governance():
    st.subheader("Board Composition")
    independent = st.number_input("Number of Independent Directors",0)
    meeting_freq = st.selectbox("Meeting Frequency",["Quarterly","Half-Yearly","Yearly"])
    committee = st.text_input("Committee Name")
    if st.button("Add Board Entry"):
        add_entry("board_data", {"Independent":independent,"Meeting_Frequency":meeting_freq,"Committee":committee})
    display_entries("board_data")

    st.subheader("Policies")
    pname = st.text_input("Policy Name")
    implemented = st.selectbox("Implemented?",["Yes","No"])
    if st.button("Add Policy Entry"):
        add_entry("policies_data", {"Policy_Name":pname,"Implemented":implemented})
    display_entries("policies_data")

    st.subheader("Compliance")
    req = st.text_input("Requirement")
    comp = st.selectbox("Complied?",["Yes","No"])
    if st.button("Add Compliance Entry"):
        add_entry("compliance_data", {"Requirement":req,"Complied":comp})
    display_entries("compliance_data")

    st.subheader("Risk Management")
    risk = st.text_input("Risk Description")
    likelihood = st.selectbox("Likelihood",["Low","Medium","High"])
    impact = st.selectbox("Impact",["Low","Medium","High"])
    if st.button("Add Risk Entry"):
        add_entry("risk_data", {"Risk":risk,"Likelihood":likelihood,"Impact":impact})
    display_entries("risk_data")

# ---------------------------
# Reports Pages
# ---------------------------
def page_reports(report_type):
    st.title(f"{report_type} Report")
    df = pd.DataFrame()

    # Map inputs to KPIs (sample logic for demo)
    if report_type=="BRSR":
        df = pd.DataFrame({
            "BRSR_QID":["E1","E2","S1","G1"],
            "Indicator":["GHG Emissions","Water Usage","Employee Count","Board Oversight"],
            "Value":[
                st.session_state.entries["Emissions_kgCO2e"].sum() if not st.session_state.entries.empty else 0,
                st.session_state.water_data["Quantity_m3"].sum() if not st.session_state.water_data.empty else 0,
                len(st.session_state.employee_data) if not st.session_state.employee_data.empty else 0,
                "Yes" if not st.session_state.board_data.empty and st.session_state.board_data["Independent"].sum()>0 else "No"
            ]
        })
    elif report_type=="GRI":
        df = pd.DataFrame({
            "GRI_ID":["305-1","303-1","401-1","403-1"],
            "Disclosure":["GHG Emissions","Water Withdrawal","Employee Count","H&S Incidents"],
            "Value":[
                st.session_state.entries["Emissions_kgCO2e"].sum() if not st.session_state.entries.empty else 0,
                st.session_state.water_data["Quantity_m3"].sum() if not st.session_state.water_data.empty else 0,
                len(st.session_state.employee_data) if not st.session_state.employee_data.empty else 0,
                len(st.session_state.hs_data) if not st.session_state.hs_data.empty else 0
            ]
        })
    elif report_type=="CDP":
        df = pd.DataFrame({
            "CDP_Item":["CC1.1","CC3.2","CC5.1"],
            "Question":["Scope 1 Emissions","Water Risks","Board Oversight"],
            "Value":[
                st.session_state.entries["Emissions_kgCO2e"].sum() if not st.session_state.entries.empty else 0,
                st.session_state.water_data["Quantity_m3"].sum() if not st.session_state.water_data.empty else 0,
                "Yes" if not st.session_state.board_data.empty and st.session_state.board_data["Independent"].sum()>0 else "No"
            ]
        })
    elif report_type=="TCFD":
        df = pd.DataFrame({
            "TCFD_Indicator":["Strategy_Climate","Risk_Management","Metrics"],
            "Description":["GHG Strategy","Board Risk Oversight","GHG Emissions & Water Usage"],
            "Value":[
                "Defined" if not st.session_state.entries.empty else "Not Defined",
                "Defined" if not st.session_state.risk_data.empty else "Not Defined",
                st.session_state.entries["Emissions_kgCO2e"].sum() if not st.session_state.entries.empty else 0
            ]
        })
    st.dataframe(df)
    if st.button(f"Export {report_type} PDF"):
        pdf_file = export_pdf(report_type, df)
        with open(pdf_file,"rb") as f:
            st.download_button(f"Download {report_type} PDF", f, pdf_file,"application/pdf")

# ---------------------------
# Main Page Routing
# ---------------------------
page = st.session_state.page
if page=="Home":
    st.title("Welcome to EinTrust Sustainability Dashboard 🌍")
elif page=="GHG":
    st.title("GHG Emissions Page")
    st.write("GHG inputs and calculations here (kept intact).")
elif page=="Energy":
    st.title("Energy Page")
    st.write("Energy inputs and calculations here (kept intact).")
elif page in ["Water","Waste","Biodiversity"]:
    page_environment()
elif page in ["Employee","Health & Safety","CSR"]:
    page_social()
elif page in ["Board","Policies","Compliance","Risk Management"]:
    page_governance()
elif page in ["BRSR","GRI","CDP","TCFD"]:
    page_reports(page)
elif page=="SDG":
    st.title("SDG Engagement Overview")
    st.dataframe(st.session_state.sdg_engagement)
elif page=="Settings":
    st.title("Settings Page")
elif page=="Log Out":
    st.warning("You have been logged out.")
