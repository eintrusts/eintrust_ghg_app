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
# Initialize Data
# ---------------------------
if "entries" not in st.session_state:
    st.session_state.entries = pd.DataFrame(columns=["Scope","Activity","Sub-Activity","Specific Item","Quantity","Unit"])
if "renewable_entries" not in st.session_state:
    st.session_state.renewable_entries = pd.DataFrame(columns=["Source","Location","Month","Energy_kWh","CO2e_kg","Type"])
if "sdg_engagement" not in st.session_state:
    st.session_state.sdg_engagement = {i:0 for i in range(1,18)}

months = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]
ENERGY_COLORS = {"Fossil": "#f39c12", "Renewable": "#2ecc71"}

# ---------------------------
# GHG KPI Dashboard
# ---------------------------
def render_ghg_kpis():
    df = st.session_state.entries.copy()
    if df.empty:
        st.info("No GHG data available yet.")
        return

    total_qty = df["Quantity"].sum()
    scope1 = df[df["Scope"]=="Scope 1"]["Quantity"].sum()
    scope2 = df[df["Scope"]=="Scope 2"]["Quantity"].sum()
    scope3 = df[df["Scope"]=="Scope 3"]["Quantity"].sum()

    c1,c2,c3,c4 = st.columns(4)
    for col,label,value in zip([c1,c2,c3,c4],["Total Emissions","Scope 1","Scope 2","Scope 3"],[total_qty,scope1,scope2,scope3]):
        col.markdown(
            f"<div class='kpi'><div class='kpi-value'>{value:,.2f}</div><div class='kpi-unit'>Units</div><div class='kpi-label'>{label}</div></div>",
            unsafe_allow_html=True
        )

# ---------------------------
# GHG Dashboard (Full: KPI + Data Entry + Entries)
# ---------------------------
def render_ghg_dashboard():
    st.subheader("GHG Emissions Dashboard")
    render_ghg_kpis()

    st.subheader("Add Data Entry")
    scope = st.selectbox("Select Scope", ["Scope 1","Scope 2","Scope 3"])
    activity = st.text_input("Activity")
    sub_activity = st.text_input("Sub-Activity")
    specific_item = st.text_input("Specific Item", "")
    quantity = st.number_input("Quantity", min_value=0.0, format="%.2f")
    unit = st.text_input("Unit")

    if st.button("Add Entry"):
        new_entry = {"Scope":scope,"Activity":activity,"Sub-Activity":sub_activity,"Specific Item":specific_item,"Quantity":quantity,"Unit":unit}
        st.session_state.entries = pd.concat([st.session_state.entries, pd.DataFrame([new_entry])], ignore_index=True)
        st.success("Entry added successfully!")

    if not st.session_state.entries.empty:
        st.subheader("All Entries")
        st.dataframe(st.session_state.entries, use_container_width=True)
        csv = st.session_state.entries.to_csv(index=False).encode("utf-8")
        st.download_button("Download Entries", csv, "ghg_entries.csv", "text/csv")

# ---------------------------
# Energy Dashboard
# ---------------------------
def render_energy_dashboard():
    st.subheader("Energy Dashboard (Summary)")
    if st.session_state.renewable_entries.empty:
        st.info("No energy data available yet.")
    else:
        st.dataframe(st.session_state.renewable_entries.head(), use_container_width=True)

# ---------------------------
# SDG Dashboard
# ---------------------------
def render_sdg_dashboard():
    st.title("Sustainable Development Goals (SDGs)")
    num_cols = 4
    idx = 0
    for _ in range((len(st.session_state.sdg_engagement)+num_cols-1)//num_cols):
        cols = st.columns(num_cols)
        for c in cols:
            if idx >= len(st.session_state.sdg_engagement):
                break
            sdg_number = idx+1
            engagement = st.session_state.sdg_engagement[sdg_number]
            engagement = c.slider(f"Engagement % - SDG {sdg_number}",0,100,value=engagement,key=f"sdg{sdg_number}")
            st.session_state.sdg_engagement[sdg_number]=engagement
            c.markdown(f"<div class='sdg-card' style='background-color:#333'><div class='sdg-number'>SDG {sdg_number}</div><div class='sdg-percent'>Engagement: {engagement}%</div></div>",unsafe_allow_html=True)
            idx+=1

# ---------------------------
# Render Pages
# ---------------------------
if st.session_state.page == "Home":
    st.title("EinTrust Sustainability Dashboard")
    st.subheader("GHG KPI Summary")
    render_ghg_kpis()
    st.subheader("Energy KPI Summary")
    render_energy_dashboard()

elif st.session_state.page == "GHG":
    render_ghg_dashboard()

elif st.session_state.page == "Energy":
    render_energy_dashboard()

elif st.session_state.page == "SDG":
    render_sdg_dashboard()

else:
    st.subheader(f"{st.session_state.page} section")
    st.info("This section is under development. Please select other pages from sidebar.")
