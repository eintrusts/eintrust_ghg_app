import streamlit as st
import pandas as pd
import numpy as np

# ---------------------------
# Config & Dark Theme CSS
# ---------------------------
st.set_page_config(page_title="EinTrust Sustainability Dashboard", page_icon="🌍", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }
.stApp { background-color: #0d1117; color: #e6edf3; }

.kpi { background: linear-gradient(145deg, #12131a, #1a1b22); padding: 20px; border-radius: 12px; text-align: center; 
       box-shadow: 0 4px 12px rgba(0,0,0,0.5); margin-bottom: 10px; min-height: 120px;
       display: flex; flex-direction: column; justify-content: center; align-items: center; 
       transition: transform 0.2s, box-shadow 0.2s;}
.kpi:hover { transform: scale(1.05); box-shadow: 0 8px 20px rgba(0,0,0,0.6); }
.kpi-value { font-size: 28px; font-weight: 700; color: #ffffff; margin-bottom: 5px; }
.kpi-unit { font-size: 16px; font-weight: 500; color: #cfd8dc; margin-bottom: 5px; }
.kpi-label { font-size: 14px; color: #cfd8dc; letter-spacing: 0.5px; }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Sidebar & Navigation
# ---------------------------
if "page" not in st.session_state:
    st.session_state.page = "Home"

def sidebar_button(label):
    active = st.session_state.page == label
    if st.button(label, key=label):
        st.session_state.page = label

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
# Employee Page
# ---------------------------
def render_employee_dashboard():
    st.title("Employee Information & Workforce Profile")
    
    # Initialize session state dataframe
    if "employee_data" not in st.session_state:
        sections = [
            ("Workforce Profile", ["Permanent Employees","Temporary Employees"]),
            ("Age-wise Distribution", ["<30","30-50",">50"]),
            ("Diversity & Inclusion", ["Employees from marginalized communities","Persons with Disabilities","Women in Leadership","Policy on Diversity and Inclusion"]),
            ("Retention & Turnover", ["Average Tenure","Employee Turnover Rate"]),
            ("Training & Development", ["Type of Trainings","Number of Employees Trained","Total Training Hours"]),
            ("Employee Welfare & Engagement", ["Employee Engagement Survey Done?","Parental Leave Policy","Benefits Provided"])
        ]
        rows = []
        for section, fields in sections:
            for field in fields:
                rows.append({
                    "Section": section,
                    "Field": field,
                    "Male": 0,
                    "Female": 0,
                    "Total": 0,
                    "Information": "",
                    "Relevant Frameworks": ""
                })
        st.session_state.employee_data = pd.DataFrame(rows)
    
    df = st.session_state.employee_data.copy()

    # Group by section
    sections = df['Section'].unique()
    for section in sections:
        st.subheader(section)
        sub_df = df[df['Section']==section]
        for idx, row in sub_df.iterrows():
            cols = st.columns(6)
            cols[0].markdown(f"**{row['Field']}**")
            male_val = cols[1].number_input("Male", min_value=0, value=int(row["Male"]), key=f"{row['Field']}_M")
            female_val = cols[2].number_input("Female", min_value=0, value=int(row["Female"]), key=f"{row['Field']}_F")
            total_val = male_val + female_val
            cols[3].markdown(f"**Total: {total_val}**")
            info_val = cols[4].text_input("Information", value=row["Information"], key=f"{row['Field']}_Info")
            framework_val = cols[5].text_input("Relevant Frameworks", value=row["Relevant Frameworks"], key=f"{row['Field']}_Frameworks")
            df.at[idx,"Male"]=male_val
            df.at[idx,"Female"]=female_val
            df.at[idx,"Total"]=total_val
            df.at[idx,"Information"]=info_val
            df.at[idx,"Relevant Frameworks"]=framework_val

    st.session_state.employee_data = df
    st.dataframe(df)
    
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Employee Data CSV", csv, "employee_data.csv", "text/csv")

# ---------------------------
# Dummy placeholders for other pages
# ---------------------------
def render_home(): st.subheader("Home page")
def render_ghg(): st.subheader("GHG page")
def render_energy(): st.subheader("Energy page")
def render_sdg(): st.subheader("SDG page")

# ---------------------------
# Render Pages
# ---------------------------
if st.session_state.page=="Home":
    render_home()
elif st.session_state.page=="GHG":
    render_ghg()
elif st.session_state.page=="Energy":
    render_energy()
elif st.session_state.page=="Employee":
    render_employee_dashboard()
elif st.session_state.page=="SDG":
    render_sdg()
else:
    st.info(f"{st.session_state.page} page under development")
