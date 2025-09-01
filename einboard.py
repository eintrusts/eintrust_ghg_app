import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ---------------------------
# Config & Theme
# ---------------------------
st.set_page_config(page_title="EinTrust ESG Dashboard", page_icon="🌍", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
html, body, [class*="css"]  {
    font-family: 'Roboto', sans-serif;
    color: #f0f2f6;
    background-color: #0e1117;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Helper Functions
# ---------------------------
def init_session_state(section):
    if section not in st.session_state:
        st.session_state[section] = pd.DataFrame()

def add_entry(section, entry):
    st.session_state[section] = pd.concat([
        st.session_state[section], pd.DataFrame([entry])
    ], ignore_index=True)

def render_section(section_name, kpis, form_fields):
    init_session_state(section_name)

    st.subheader("📊 KPI Summary")
    if st.session_state[section_name].empty:
        st.info("No data yet. Please add entries.")
    else:
        kpi_cols = st.columns(len(kpis))
        for i, (kpi, func) in enumerate(kpis.items()):
            with kpi_cols[i]:
                st.metric(kpi, func(st.session_state[section_name]))

    st.subheader("📈 Monthly Trend")
    if st.session_state[section_name].empty:
        st.info("No data available.")
    else:
        df = st.session_state[section_name]
        if "Month" in df.columns and len(df) > 0:
            trend = df.groupby("Month").sum().reset_index()
            fig = px.line(trend, x="Month", y=trend.columns[1:], markers=True)
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("➕ Input Form")
    with st.form(f"form_{section_name}"):
        entry = {}
        entry["Date"] = datetime.today().strftime('%Y-%m-%d')
        entry["Month"] = st.selectbox("Month", [
            "April","May","June","July","August","September","October","November","December","January","February","March"
        ])
        for field in form_fields:
            entry[field] = st.number_input(field, min_value=0.0, step=1.0)
        submitted = st.form_submit_button("Add Entry")
        if submitted:
            add_entry(section_name, entry)
            st.success("Entry added successfully!")

    st.subheader("📂 All Entries")
    if st.session_state[section_name].empty:
        st.info("No entries yet.")
    else:
        st.dataframe(st.session_state[section_name], use_container_width=True)
        st.download_button(
            label="Download CSV",
            data=st.session_state[section_name].to_csv(index=False).encode('utf-8'),
            file_name=f"{section_name}_data.csv",
            mime="text/csv"
        )

# ---------------------------
# Home Page
# ---------------------------
def render_home():
    st.title("🌍 EinTrust ESG Dashboard")
    st.write("Overview of ESG KPIs across Environment, Social, and Governance.")

    env_sections = ["Energy", "Water", "Waste"]
    social_sections = ["Diversity", "HealthSafety"]
    gov_sections = ["Compliance", "Ethics"]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Environment")
        for sec in env_sections:
            init_session_state(sec)
            st.metric(f"{sec} Entries", len(st.session_state[sec]))

    with col2:
        st.subheader("Social")
        for sec in social_sections:
            init_session_state(sec)
            st.metric(f"{sec} Entries", len(st.session_state[sec]))

    with col3:
        st.subheader("Governance")
        for sec in gov_sections:
            init_session_state(sec)
            st.metric(f"{sec} Entries", len(st.session_state[sec]))

# ---------------------------
# Sidebar Navigation
# ---------------------------
menu = st.sidebar.radio("Navigation", [
    "Home",
    "Environment - Energy",
    "Environment - Water",
    "Environment - Waste",
    "Social - Diversity",
    "Social - Health & Safety",
    "Governance - Compliance",
    "Governance - Ethics"
])

# ---------------------------
# Render Pages
# ---------------------------
if menu == "Home":
    render_home()

elif menu == "Environment - Energy":
    render_section(
        "Energy",
        {"Total Energy (kWh)": lambda df: df["Energy (kWh)"].sum()},
        ["Energy (kWh)"]
    )

elif menu == "Environment - Water":
    render_section(
        "Water",
        {"Total Water (kL)": lambda df: df["Water (kL)"].sum()},
        ["Water (kL)", "Rainwater Harvested (kL)", "Recycled (kL)", "Treatment Capacity (kL/day)"]
    )

elif menu == "Environment - Waste":
    render_section(
        "Waste",
        {"Total Waste (kg)": lambda df: df["Waste (kg)"].sum()},
        ["Waste (kg)", "Recycled Waste (kg)", "Disposed Waste (kg)"]
    )

elif menu == "Social - Diversity":
    render_section(
        "Diversity",
        {"Total Employees": lambda df: df["Employees"].sum()},
        ["Employees", "Women Employees"]
    )

elif menu == "Social - Health & Safety":
    render_section(
        "HealthSafety",
        {"Total Incidents": lambda df: df["Incidents"].sum()},
        ["Incidents", "Training Hours"]
    )

elif menu == "Governance - Compliance":
    render_section(
        "Compliance",
        {"Total Cases": lambda df: df["Cases"].sum()},
        ["Cases"]
    )

elif menu == "Governance - Ethics":
    render_section(
        "Ethics",
        {"Ethics Cases": lambda df: df["Cases"].sum()},
        ["Cases"]
    )
