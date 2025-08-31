import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io

# --- Page Config ---
st.set_page_config(page_title="EinTrust GHG Dashboard", page_icon="🌍", layout="wide")

# --- Custom Dark Theme ---
st.markdown("""
    <style>
        .stApp {background-color: #121212; color: #E0E0E0;}
        .stMetric {background-color: #1E1E1E; border-radius: 12px; padding: 10px;}
        .stButton>button {background-color: #1DB954; color: white; border-radius: 8px;}
    </style>
""", unsafe_allow_html=True)

# --- Session State Setup ---
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["Date", "Scope 1", "Scope 2", "Scope 3"])

if "archive" not in st.session_state:
    st.session_state.archive = None

# --- Utility Functions ---
def format_indian(num):
    return "{:,}".format(int(num)).replace(",", "_").replace("_", ",")

# Define Apr–Mar cycle boundaries
current_year = datetime.now().year
current_month = datetime.now().month
if current_month < 4:
    cycle_start = datetime(current_year - 1, 4, 1)
    cycle_end = datetime(current_year, 3, 31)
else:
    cycle_start = datetime(current_year, 4, 1)
    cycle_end = datetime(current_year + 1, 3, 31)

# Auto-reset every April 1st
today = datetime.now().date()
if today == datetime(today.year, 4, 1).date() and not st.session_state.archive:
    if not st.session_state.data.empty:
        output = io.StringIO()
        st.session_state.data.to_csv(output, index=False)
        st.session_state.archive = output.getvalue()
    st.session_state.data = pd.DataFrame(columns=["Date", "Scope 1", "Scope 2", "Scope 3"])

# --- Sidebar: Data Entry ---
st.sidebar.header("Add Emission Entry")
date = st.sidebar.date_input("Date", datetime.today())
scope1 = st.sidebar.number_input("Scope 1 Emissions", min_value=0.0, step=1.0)
scope2 = st.sidebar.number_input("Scope 2 Emissions", min_value=0.0, step=1.0)
scope3 = st.sidebar.number_input("Scope 3 Emissions", min_value=0.0, step=1.0)

if st.sidebar.button("Add Entry"):
    new_entry = pd.DataFrame([[date, scope1, scope2, scope3]], columns=["Date", "Scope 1", "Scope 2", "Scope 3"])
    st.session_state.data = pd.concat([st.session_state.data, new_entry], ignore_index=True)

# Manual Archive & Reset
if st.sidebar.button("Archive & Reset Now"):
    if not st.session_state.data.empty:
        output = io.StringIO()
        st.session_state.data.to_csv(output, index=False)
        st.session_state.archive = output.getvalue()
    st.session_state.data = pd.DataFrame(columns=["Date", "Scope 1", "Scope 2", "Scope 3"])

# --- Main Dashboard ---
st.title("🌍 EinTrust GHG Dashboard")
st.markdown("Track Scope 1, 2, and 3 emissions across Apr–Mar cycles.")

# Show archive download if available
if st.session_state.archive:
    st.download_button("⬇️ Download Last Cycle Archive (CSV)",
                       data=st.session_state.archive,
                       file_name=f"emissions_Apr{cycle_start.year}_Mar{cycle_end.year}.csv",
                       mime="text/csv")

if st.session_state.data.empty:
    st.info("No emission data available. Add entries from the sidebar.")
else:
    df = st.session_state.data.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df = df[(df["Date"] >= cycle_start) & (df["Date"] <= cycle_end)]

    # Key Metrics
    total_scope1 = df["Scope 1"].sum()
    total_scope2 = df["Scope 2"].sum()
    total_scope3 = df["Scope 3"].sum()
    total_emissions = total_scope1 + total_scope2 + total_scope3

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Scope 1 Emissions", format_indian(total_scope1))
    col2.metric("Scope 2 Emissions", format_indian(total_scope2))
    col3.metric("Scope 3 Emissions", format_indian(total_scope3))
    col4.metric("Total Emissions", format_indian(total_emissions))

    # Monthly Aggregation Apr–Mar
    df["Month"] = df["Date"].dt.strftime("%b")
    monthly = df.groupby("Month")["Scope 1", "Scope 2", "Scope 3"].sum().reset_index()

    # Ensure Apr–Mar order
    month_order = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
    monthly["Month"] = pd.Categorical(monthly["Month"], categories=month_order, ordered=True)
    monthly = monthly.sort_values("Month")

    # Trend Chart
    fig = px.bar(monthly, x="Month", y=["Scope 1", "Scope 2", "Scope 3"],
                 barmode="stack", title="Emissions Trend Over Time (Monthly Apr–Mar)",
                 labels={"value": "Emissions", "variable": "Scope"})
    fig.update_layout(paper_bgcolor="#121212", plot_bgcolor="#121212", font_color="#E0E0E0")
    st.plotly_chart(fig, use_container_width=True)
