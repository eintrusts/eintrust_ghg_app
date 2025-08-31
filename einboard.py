import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io

# --- Page Config ---
st.set_page_config(page_title="EinTrust GHG Dashboard", page_icon="🌍", layout="wide")

# --- Dark Theme CSS ---
st.markdown("""
<style>
.stApp { background-color: #121212; color: #ffffff; }
.sidebar .sidebar-content { background-color: #1E1E1E; }
</style>
""", unsafe_allow_html=True)

# --- Initialize session state ---
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["Date", "Activity", "Scope", "Emissions (kg CO2e)"])
if "archive" not in st.session_state:
    st.session_state.archive = {}

# --- Sidebar ---
st.sidebar.image("https://eintrusts.com/wp-content/uploads/2024/07/eintrust-logo.png", use_column_width=True)
st.sidebar.header("Add Activity Data")
activity = st.sidebar.text_input("Activity Description")
scope = st.sidebar.selectbox("Scope", ["Scope 1", "Scope 2", "Scope 3"])
emission_value = st.sidebar.number_input("Emissions (kg CO2e)", min_value=0.0, step=0.1)
if st.sidebar.button("Add Entry"):
    new_entry = pd.DataFrame({
        "Date": [datetime.now()],
        "Activity": [activity],
        "Scope": [scope],
        "Emissions (kg CO2e)": [emission_value]
    })
    st.session_state.data = pd.concat([st.session_state.data, new_entry], ignore_index=True)
    st.sidebar.success("Entry added successfully!")

# --- Archive & Reset ---
def archive_and_reset():
    year = datetime.now().year - 1 if datetime.now().month < 4 else datetime.now().year
    st.session_state.archive[year] = st.session_state.data.copy()
    st.session_state.data = pd.DataFrame(columns=["Date", "Activity", "Scope", "Emissions (kg CO2e)"])

# Auto reset every April
if datetime.now().month == 4 and not st.session_state.data.empty:
    archive_and_reset()

# Manual archive
if st.sidebar.button("Archive & Reset"):
    archive_and_reset()
    st.sidebar.success("Data archived & reset!")

# Download latest archive
if st.session_state.archive:
    latest_year = max(st.session_state.archive.keys())
    buffer = io.StringIO()
    st.session_state.archive[latest_year].to_csv(buffer, index=False)
    st.sidebar.download_button(
        label=f"Download {latest_year} Archive",
        data=buffer.getvalue(),
        file_name=f"emissions_archive_{latest_year}.csv",
        mime="text/csv"
    )

# --- Main Dashboard ---
st.title("🌍 EinTrust GHG Dashboard")

# Key Indicators
if not st.session_state.data.empty:
    total = st.session_state.data["Emissions (kg CO2e)"].sum()
    scope1 = st.session_state.data.loc[st.session_state.data["Scope"]=="Scope 1", "Emissions (kg CO2e)"].sum()
    scope2 = st.session_state.data.loc[st.session_state.data["Scope"]=="Scope 2", "Emissions (kg CO2e)"].sum()
    scope3 = st.session_state.data.loc[st.session_state.data["Scope"]=="Scope 3", "Emissions (kg CO2e)"].sum()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Emissions", f"{total:,.0f}".replace(",", ","))
    col2.metric("Scope 1", f"{scope1:,.0f}".replace(",", ","))
    col3.metric("Scope 2", f"{scope2:,.0f}".replace(",", ","))
    col4.metric("Scope 3", f"{scope3:,.0f}".replace(",", ","))

    # Emission Breakdown Pie
    fig_pie = px.pie(st.session_state.data, names="Scope", values="Emissions (kg CO2e)",
                     title="Emission Breakdown by Scope",
                     color="Scope",
                     color_discrete_map={"Scope 1":"#FF6B6B", "Scope 2":"#4ECDC4", "Scope 3":"#FFD93D"})
    st.plotly_chart(fig_pie, use_container_width=True)

    # Monthly Trend Apr–Mar
    df = st.session_state.data.copy()
    df["Month"] = df["Date"].apply(lambda x: (x.month, x.strftime("%b")))
    df["Year"] = df["Date"].dt.year
    fiscal_year = df["Year"].max() if datetime.now().month >= 4 else df["Year"].max()-1
    df = df[df["Year"] >= fiscal_year]
    df["FiscalMonth"] = df["Date"].dt.month.apply(lambda m: (m-4)%12+1)
    month_map = {1:"Apr",2:"May",3:"Jun",4:"Jul",5:"Aug",6:"Sep",7:"Oct",8:"Nov",9:"Dec",10:"Jan",11:"Feb",12:"Mar"}
    df["MonthName"] = df["FiscalMonth"].map(month_map)
    monthly = df.groupby(["MonthName","Scope"], sort=False)["Emissions (kg CO2e)"].sum().reset_index()
    fig_bar = px.bar(monthly, x="MonthName", y="Emissions (kg CO2e)", color="Scope",
                     title="Emissions Trend Over Time (Monthly — Apr→Mar)",
                     color_discrete_map={"Scope 1":"#FF6B6B", "Scope 2":"#4ECDC4", "Scope 3":"#FFD93D"},
                     barmode="stack")
    st.plotly_chart(fig_bar, use_container_width=True)

    # Emissions Log
    st.subheader("Emissions Log")
    st.dataframe(st.session_state.data, use_container_width=True)
