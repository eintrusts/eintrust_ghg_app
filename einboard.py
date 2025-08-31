import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import calendar
import io

# --- Page Config ---
st.set_page_config(page_title="EinTrust GHG Dashboard", page_icon="🌍", layout="wide")

# --- Custom Theme CSS ---
st.markdown("""
<style>
.stApp { background-color: #121212; color: #e0e0e0; }
.sidebar .sidebar-content { background-color: #1e1e1e; }
h1, h2, h3, h4 { color: #ffffff; }
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---
st.sidebar.image("https://github.com/eintrusts.png", use_container_width=True)  # EinTrust logo
st.sidebar.header("➕ Add Activity Data")

# --- Initialize Session State ---
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["Date", "Activity", "Scope", "Emissions (kgCO2e)"])

if "archive" not in st.session_state:
    st.session_state.archive = None

# --- Auto Archive & Reset (April Cycle) ---
current_month = datetime.now().month
if current_month == 4 and "last_reset" not in st.session_state:
    if not st.session_state.data.empty:
        output = io.StringIO()
        st.session_state.data.to_csv(output, index=False)
        st.session_state.archive = output.getvalue()
        st.session_state.data = pd.DataFrame(columns=["Date", "Activity", "Scope", "Emissions (kgCO2e)"])
    st.session_state.last_reset = datetime.now().year

# --- Manual Archive & Reset ---
if st.sidebar.button("📦 Archive & Reset"):
    if not st.session_state.data.empty:
        output = io.StringIO()
        st.session_state.data.to_csv(output, index=False)
        st.session_state.archive = output.getvalue()
        st.session_state.data = pd.DataFrame(columns=["Date", "Activity", "Scope", "Emissions (kgCO2e)"])
        st.sidebar.success("Data archived and reset successfully!")

# --- Archive Download ---
if st.session_state.archive:
    st.sidebar.download_button("⬇️ Download Last Archive", st.session_state.archive, file_name="emissions_archive.csv")

# --- Add Entry ---
with st.sidebar.form("entry_form", clear_on_submit=True):
    date = st.date_input("Date", datetime.today())
    activity = st.text_input("Activity")
    scope = st.selectbox("Scope", ["Scope 1", "Scope 2", "Scope 3"])
    emissions = st.number_input("Emissions (kgCO2e)", min_value=0.0, step=0.1)
    submitted = st.form_submit_button("Add Entry")

    if submitted:
        new_entry = pd.DataFrame([[date, activity, scope, emissions]],
                                 columns=["Date", "Activity", "Scope", "Emissions (kgCO2e)"])
        st.session_state.data = pd.concat([st.session_state.data, new_entry], ignore_index=True)
        st.sidebar.success("Entry added successfully!")

# --- Main Dashboard ---
st.title("🌍 EinTrust GHG Dashboard")
st.markdown("Estimate Scope 1, 2, and 3 emissions for your net zero journey.")

if st.session_state.data.empty:
    st.info("No data available. Please add activities from the sidebar.")
else:
    df = st.session_state.data.copy()
    df["Date"] = pd.to_datetime(df["Date"])

    # --- Emission Breakdown by Scope ---
    st.subheader("📊 Emission Breakdown by Scope")
    breakdown = df.groupby("Scope")["Emissions (kgCO2e)"].sum().reset_index()
    fig_breakdown = px.pie(breakdown, names="Scope", values="Emissions (kgCO2e)",
                           color="Scope",
                           color_discrete_map={
                               "Scope 1": "#FF6B6B",
                               "Scope 2": "#4ECDC4",
                               "Scope 3": "#FFD93D"
                           })
    st.plotly_chart(fig_breakdown, use_container_width=True)

    # --- Emissions Trend Over Time (Stacked Monthly Apr→Mar) ---
    st.subheader("📈 Emissions Trend Over Time (Monthly — Apr→Mar)")
    df["YearMonth"] = df["Date"].dt.to_period("M")
    df_grouped = df.groupby(["YearMonth", "Scope"])["Emissions (kgCO2e)"].sum().reset_index()
    df_grouped["YearMonth"] = df_grouped["YearMonth"].astype(str)

    fig_trend = px.bar(df_grouped, x="YearMonth", y="Emissions (kgCO2e)", color="Scope",
                       color_discrete_map={
                           "Scope 1": "#FF6B6B",
                           "Scope 2": "#4ECDC4",
                           "Scope 3": "#FFD93D"
                       },
                       barmode="stack")
    fig_trend.update_layout(xaxis_title="Month", yaxis_title="Emissions (kgCO2e)")
    st.plotly_chart(fig_trend, use_container_width=True)

    # --- Emissions Log (Bottom) ---
    st.subheader("📜 Emissions Log")
    st.dataframe(df.sort_values("Date", ascending=False), use_container_width=True)
