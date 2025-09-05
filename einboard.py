import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------
# Session State Initialization
# ---------------------------
if "sdg_engagement" not in st.session_state:
    st.session_state.sdg_engagement = {i: 0 for i in range(1, 18)}

# ---------------------------
# Constants
# ---------------------------
SDG_LIST = [
    "No Poverty", "Zero Hunger", "Good Health and Well-being", "Quality Education",
    "Gender Equality", "Clean Water and Sanitation", "Affordable and Clean Energy",
    "Decent Work and Economic Growth", "Industry, Innovation and Infrastructure",
    "Reduced Inequalities", "Sustainable Cities and Communities",
    "Responsible Consumption and Production", "Climate Action", "Life Below Water",
    "Life on Land", "Peace, Justice and Strong Institutions", "Partnerships for the Goals"
]
SDG_COLORS = [
    "#e5243b", "#dda63a", "#4c9f38", "#c5192d", "#ff3a21", "#26bde2",
    "#fcc30b", "#a21942", "#fd6925", "#dd1367", "#fd9d24", "#bf8b2e",
    "#3f7e44", "#0a97d9", "#56c02b", "#00689d", "#19486a"
]

# ---------------------------
# Environment Pages
# ---------------------------
def render_ghg_dashboard():
    st.title("GHG Dashboard")
    st.session_state["ghg_scope1"] = st.number_input("Scope 1 Emissions (tCO2e)", 0)
    st.session_state["ghg_scope2"] = st.number_input("Scope 2 Emissions (tCO2e)", 0)
    st.session_state["ghg_scope3"] = st.number_input("Scope 3 Emissions (tCO2e)", 0)

def render_energy_dashboard():
    st.title("Energy Dashboard")
    st.session_state["energy_consumption"] = st.number_input("Total Energy Consumption (MWh)", 0)

def render_water_dashboard():
    st.title("Water Dashboard")
    st.session_state["water_usage"] = st.number_input("Water Usage (ML)", 0)

def render_waste_dashboard():
    st.title("Waste Dashboard")
    st.session_state["waste_generated"] = st.number_input("Waste Generated (tons)", 0)

def render_sdg_dashboard():
    st.title("Sustainable Development Goals (SDGs)")
    num_cols = 4
    rows = (len(SDG_LIST) + num_cols - 1) // num_cols
    idx = 0
    for _ in range(rows):
        cols = st.columns(num_cols)
        for c in range(num_cols):
            if idx < len(SDG_LIST):
                sdg_name = SDG_LIST[idx]
                sdg_num = idx + 1
                color = SDG_COLORS[idx]
                engagement = st.session_state.sdg_engagement.get(sdg_num, 0)
                with cols[c]:
                    st.markdown(
                        f"""
                        <div style="background-color:{color}; padding:15px; border-radius:10px; text-align:center; color:white;">
                            <h4>SDG {sdg_num}</h4>
                            <p>{sdg_name}</p>
                            <b>Engagement: {engagement}%</b>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    if st.button(f"Increase {sdg_name}", key=f"sdg_btn_{sdg_num}"):
                        st.session_state.sdg_engagement[sdg_num] = min(100, engagement + 10)
                        st.experimental_rerun()
                idx += 1

# ---------------------------
# Social Pages
# ---------------------------
def render_employees_dashboard():
    st.title("Employees Dashboard")
    st.session_state["employee_count"] = st.number_input("Total Employees", 0)
    st.session_state["training_hours"] = st.number_input("Avg Training Hours per Employee", 0.0)
    st.session_state["attrition_rate"] = st.slider("Attrition Rate (%)", 0, 100, 0)

def render_diversity_dashboard():
    st.title("Diversity & Inclusion Dashboard")
    st.session_state["women_percentage"] = st.slider("% Women Employees", 0, 100, 0)
    st.session_state["diverse_hires"] = st.number_input("New Diverse Hires", 0)

def render_community_dashboard():
    st.title("Community Dashboard")
    st.session_state["community_spend"] = st.number_input("CSR Spend on Community (₹ Lakhs)", 0.0)

# ---------------------------
# Governance Pages
# ---------------------------
def render_board_dashboard():
    st.title("Board Structure")
    st.session_state["board_size"] = st.number_input("Total Board Members", 0)
    st.session_state["independent_directors"] = st.number_input("Independent Directors", 0)
    st.session_state["board_oversight"] = st.checkbox("Board Oversees Climate Risks?")

def render_ethics_dashboard():
    st.title("Ethics & Compliance")
    st.session_state["anti_corruption_policies"] = st.checkbox("Anti-Corruption Policy in Place?")
    st.session_state["code_of_conduct"] = st.checkbox("Code of Conduct Implemented?")

def render_risk_dashboard():
    st.title("Risk Management")
    st.session_state["risk_process"] = st.checkbox("Risk Management Process Exists?")
    st.session_state["climate_risks"] = st.text_area("Climate Risks Identified", "")

# ---------------------------
# Mapping Rules
# ---------------------------
BRSR_MAP = {
    "Principle 6 - GHG Emissions (tCO2e)": lambda s: s.get("ghg_scope1", 0) + s.get("ghg_scope2", 0),
    "Principle 6 - Energy Consumption (MWh)": lambda s: s.get("energy_consumption", 0),
    "Principle 6 - Water Usage (ML)": lambda s: s.get("water_usage", 0),
    "Principle 6 - Waste Generated (tons)": lambda s: s.get("waste_generated", 0),
    "Principle 3 - Employee Count": lambda s: s.get("employee_count", 0),
    "Principle 3 - Training Hours per Employee": lambda s: s.get("training_hours", 0),
    "Principle 3 - Attrition Rate (%)": lambda s: s.get("attrition_rate", 0),
    "Principle 1 - Board Independence (%)": lambda s: (s.get("independent_directors", 0)/s.get("board_size", 1))*100
}

CDP_MAP = {
    "Scope 1 Emissions (tCO2e)": lambda s: s.get("ghg_scope1", 0),
    "Scope 2 Emissions (tCO2e)": lambda s: s.get("ghg_scope2", 0),
    "Scope 3 Emissions (tCO2e)": lambda s: s.get("ghg_scope3", 0),
    "Total Energy Consumption (MWh)": lambda s: s.get("energy_consumption", 0),
    "Climate Risks Identified": lambda s: s.get("climate_risks", "Not Reported")
}

GRI_MAP = {
    "GRI 305 - GHG Emissions (tCO2e)": lambda s: s.get("ghg_scope1", 0) + s.get("ghg_scope2", 0) + s.get("ghg_scope3", 0),
    "GRI 302 - Energy Consumption (MWh)": lambda s: s.get("energy_consumption", 0),
    "GRI 303 - Water Usage (ML)": lambda s: s.get("water_usage", 0),
    "GRI 401 - Total Employees": lambda s: s.get("employee_count", 0),
    "GRI 405 - % Women Employees": lambda s: s.get("women_percentage", 0)
}

TCFD_MAP = {
    "Governance - Board Oversight": lambda s: "Yes" if s.get("board_oversight", False) else "No",
    "Strategy - Climate Risks Identified": lambda s: s.get("climate_risks", "Not Reported"),
    "Risk Management - Process Exists": lambda s: "Yes" if s.get("risk_process", False) else "No",
    "Metrics - Scope 1+2 Emissions (tCO2e)": lambda s: s.get("ghg_scope1", 0) + s.get("ghg_scope2", 0),
    "Metrics - Energy Consumption (MWh)": lambda s: s.get("energy_consumption", 0)
}

# ---------------------------
# Report Pages
# ---------------------------
def render_report(mapping, title):
    st.subheader(title)
    for kpi, formula in mapping.items():
        value = formula(st.session_state)
        st.metric(kpi, value if value != "" else "Not Reported")

def render_reports():
    st.title("Reports")
    report_type = st.selectbox("Select Framework", ["BRSR", "CDP", "GRI", "TCFD"])
    if report_type == "BRSR":
        render_report(BRSR_MAP, "BRSR Report - KPIs")
    elif report_type == "CDP":
        render_report(CDP_MAP, "CDP Report - KPIs")
    elif report_type == "GRI":
        render_report(GRI_MAP, "GRI Report - KPIs")
    elif report_type == "TCFD":
        render_report(TCFD_MAP, "TCFD Report - KPIs")

# ---------------------------
# Router
# ---------------------------
def main():
    st.sidebar.title("Navigation")
    section = st.sidebar.radio("Section", ["Home", "Environment", "Social", "Governance", "Reports"])

    if section == "Home":
        st.title("Sustainability Dashboard")
        st.write("Welcome! Navigate through ESG sections and auto-generate reports.")

    elif section == "Environment":
        page = st.sidebar.radio("Environment Pages", ["GHG", "Energy", "Water", "Waste", "SDG"])
        if page == "GHG": render_ghg_dashboard()
        elif page == "Energy": render_energy_dashboard()
        elif page == "Water": render_water_dashboard()
        elif page == "Waste": render_waste_dashboard()
        elif page == "SDG": render_sdg_dashboard()

    elif section == "Social":
        page = st.sidebar.radio("Social Pages", ["Employees", "Diversity & Inclusion", "Community"])
        if page == "Employees": render_employees_dashboard()
        elif page == "Diversity & Inclusion": render_diversity_dashboard()
        elif page == "Community": render_community_dashboard()

    elif section == "Governance":
        page = st.sidebar.radio("Governance Pages", ["Board", "Ethics", "Risk Management"])
        if page == "Board": render_board_dashboard()
        elif page == "Ethics": render_ethics_dashboard()
        elif page == "Risk Management": render_risk_dashboard()

    elif section == "Reports":
        render_reports()

if __name__ == "__main__":
    main()
