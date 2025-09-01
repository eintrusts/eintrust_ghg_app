import streamlit as st
import pandas as pd
import plotly.express as px
from io import StringIO

# ---------------------------
# Config & Theme
# ---------------------------
st.set_page_config(page_title="EinTrust ESG Dashboard", page_icon="🌍", layout="wide")

# ---------------------------
# Initialize Session State for Data Storage
# ---------------------------
if "environment_data" not in st.session_state:
    st.session_state.environment_data = pd.DataFrame(columns=["Month", "Rainwater Harvested (KL)", "Water Recycled (KL)", "Treatment Capacity (KL/day)"])

if "social_data" not in st.session_state:
    st.session_state.social_data = pd.DataFrame(columns=["Month", "Training Hours", "Employees Covered", "Safety Incidents"])

if "governance_data" not in st.session_state:
    st.session_state.governance_data = pd.DataFrame(columns=["Month", "Board Meetings", "Policies Updated", "Audits Conducted"])

# ---------------------------
# Helper: Add New Entry
# ---------------------------
def add_entry(df_name, new_row):
    st.session_state[df_name] = pd.concat([st.session_state[df_name], pd.DataFrame([new_row])], ignore_index=True)

# ---------------------------
# KPI Summary Function
# ---------------------------
def show_kpis(df, kpi_mapping):
    cols = st.columns(len(kpi_mapping))
    for i, (label, column) in enumerate(kpi_mapping.items()):
        if not df.empty:
            value = df[column].sum()
        else:
            value = 0
        cols[i].metric(label, value)

# ---------------------------
# Data Section Template
# ---------------------------
def section(name, df_name, kpi_mapping, form_fields):
    df = st.session_state[df_name]

    st.subheader(f"{name} – KPI Summary")
    show_kpis(df, kpi_mapping)

    st.subheader(f"{name} – Monthly Trend")
    if not df.empty:
        fig = px.line(df, x="Month", y=list(kpi_mapping.values()), markers=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data yet.")

    st.subheader(f"{name} – Add New Entry")
    with st.form(f"form_{df_name}"):
        inputs = {}
        inputs["Month"] = st.selectbox("Month", [
            "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"
        ])
        for field, dtype in form_fields.items():
            if dtype == "int":
                inputs[field] = st.number_input(field, min_value=0, step=1)
            elif dtype == "float":
                inputs[field] = st.number_input(field, min_value=0.0, step=0.1)
        submitted = st.form_submit_button("Add Entry")
        if submitted:
            add_entry(df_name, inputs)
            st.success("Entry added successfully!")

    st.subheader(f"{name} – All Entries")
    st.dataframe(df, use_container_width=True)
    if not df.empty:
        csv = df.to_csv(index=False)
        st.download_button("Download CSV", csv, f"{name.lower()}_data.csv", "text/csv")

# ---------------------------
# Sidebar Navigation
# ---------------------------
menu = st.sidebar.radio("Navigation", ["Home", "Environment", "Social", "Governance"])

# ---------------------------
# Home Page
# ---------------------------
if menu == "Home":
    st.title("🌍 EinTrust ESG Dashboard")
    st.markdown("#### Overall KPI Summary")

    env_df = st.session_state.environment_data
    soc_df = st.session_state.social_data
    gov_df = st.session_state.governance_data

    cols = st.columns(3)
    cols[0].metric("Total Rainwater Harvested (KL)", env_df["Rainwater Harvested (KL)"].sum() if not env_df.empty else 0)
    cols[0].metric("Total Water Recycled (KL)", env_df["Water Recycled (KL)"].sum() if not env_df.empty else 0)

    cols[1].metric("Total Training Hours", soc_df["Training Hours"].sum() if not soc_df.empty else 0)
    cols[1].metric("Employees Covered", soc_df["Employees Covered"].sum() if not soc_df.empty else 0)

    cols[2].metric("Board Meetings Held", gov_df["Board Meetings"].sum() if not gov_df.empty else 0)
    cols[2].metric("Audits Conducted", gov_df["Audits Conducted"].sum() if not gov_df.empty else 0)

# ---------------------------
# Environment Section
# ---------------------------
elif menu == "Environment":
    section(
        "Environment",
        "environment_data",
        {"Rainwater Harvested (KL)": "Rainwater Harvested (KL)",
         "Water Recycled (KL)": "Water Recycled (KL)",
         "Treatment Capacity (KL/day)": "Treatment Capacity (KL/day)"},
        {"Rainwater Harvested (KL)": "float",
         "Water Recycled (KL)": "float",
         "Treatment Capacity (KL/day)": "float"}
    )

# ---------------------------
# Social Section
# ---------------------------
elif menu == "Social":
    section(
        "Social",
        "social_data",
        {"Training Hours": "Training Hours",
         "Employees Covered": "Employees Covered",
         "Safety Incidents": "Safety Incidents"},
        {"Training Hours": "int",
         "Employees Covered": "int",
         "Safety Incidents": "int"}
    )

# ---------------------------
# Governance Section
# ---------------------------
elif menu == "Governance":
    section(
        "Governance",
        "governance_data",
        {"Board Meetings": "Board Meetings",
         "Policies Updated": "Policies Updated",
         "Audits Conducted": "Audits Conducted"},
        {"Board Meetings": "int",
         "Policies Updated": "int",
         "Audits Conducted": "int"}
    )
