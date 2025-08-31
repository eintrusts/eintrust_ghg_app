import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io

# --- Page Config ---
st.set_page_config(page_title="EinTrust GHG Dashboard", page_icon="🌍", layout="wide")

# --- Custom CSS for Dark Professional Theme ---
st.markdown("""
    <style>
        /* Main App Dark Theme */
        .stApp { background-color: #121212; color: #E0E0E0; }
        h1, h2, h3, h4, h5 { color: #FFFFFF; }
        .stSidebar { background-color: #1E1E1E; }
        .stButton>button { border-radius: 10px; padding: 0.6em 1em; }
        .stDownloadButton>button { border-radius: 10px; padding: 0.6em 1em; }
    </style>
""", unsafe_allow_html=True)

# --- Sidebar ---
st.sidebar.image("https://github.com/eintrusts.png", use_container_width=True)
st.sidebar.title("EinTrust GHG Dashboard")

# --- Session States ---
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["Date", "Activity", "Scope", "Emissions (tCO2e)"])

if "archive" not in st.session_state:
    st.session_state.archive = None

if "message" not in st.session_state:
    st.session_state.message = ""

# --- Function to Reset Data ---
def reset_data():
    if not st.session_state.data.empty:
        # Archive current data as CSV in memory
        output = io.StringIO()
        st.session_state.data.to_csv(output, index=False)
        st.session_state.archive = output.getvalue()
    # Reset data
    st.session_state.data = pd.DataFrame(columns=["Date", "Activity", "Scope", "Emissions (tCO2e)"])

# --- Auto Reset Every April ---
current_month = datetime.now().month
if current_month == 4 and not st.session_state.data.empty:
    reset_data()

# --- Sidebar: Add New Activity ---
st.sidebar.subheader("➕ Add Activity Data")
with st.sidebar.form("entry_form", clear_on_submit=True):
    activity = st.text_input("Activity")
    scope = st.selectbox("Scope", ["Scope 1", "Scope 2", "Scope 3"])
    emissions = st.number_input("Emissions (tCO2e)", min_value=0.0, step=0.01, format="%.2f")
    submitted = st.form_submit_button("Add Entry")

    if submitted and activity and emissions > 0:
        new_entry = pd.DataFrame([{
            "Date": datetime.now(),
            "Activity": activity,
            "Scope": scope,
            "Emissions (tCO2e)": emissions
        }])
        st.session_state.data = pd.concat([st.session_state.data, new_entry], ignore_index=True)
        st.session_state.message = f"✅ Entry for *{activity}* added successfully!"

# Show sidebar message only
if st.session_state.message:
    st.sidebar.success(st.session_state.message)
    st.session_state.message = ""  # Clear after showing once

# --- Sidebar: Manual Archive & Reset ---
st.sidebar.subheader("🗄 Archive & Reset")
if st.sidebar.button("Archive & Reset Now"):
    reset_data()
    st.sidebar.success("✅ Data archived and reset successfully!")

# Download button if archive exists
if st.session_state.archive:
    st.sidebar.download_button(
        label="⬇ Download Last Archive (CSV)",
        data=st.session_state.archive,
        file_name="emissions_archive.csv",
        mime="text/csv"
    )

# --- Main Dashboard ---
st.title("🌍 EinTrust GHG Dashboard")
st.markdown("Track Scope 1, 2, and 3 emissions for your Net Zero journey (Apr → Mar cycle).")

# --- Emission Breakdown by Scope ---
if not st.session_state.data.empty:
    st.subheader("📊 Emission Breakdown by Scope")
    scope_totals = st.session_state.data.groupby("Scope")["Emissions (tCO2e)"].sum().reset_index()

    fig_scope = px.pie(
        scope_totals,
        names="Scope",
        values="Emissions (tCO2e)",
        color="Scope",
        color_discrete_map={
            "Scope 1": "#1f77b4",
            "Scope 2": "#ff7f0e",
            "Scope 3": "#2ca02c"
        },
        hole=0.4
    )
    fig_scope.update_layout(
        showlegend=True,
        legend_title="Scope",
        paper_bgcolor="#121212",
        plot_bgcolor="#121212",
        font_color="white"
    )
    st.plotly_chart(fig_scope, use_container_width=True)

    # --- Emissions Trend Over Time (Apr → Mar) ---
    st.subheader("📈 Emissions Trend Over Time (Monthly — Apr → Mar)")
    df = st.session_state.data.copy()
    df["Month"] = df["Date"].dt.strftime("%b")

    # Reorder months in Apr–Mar cycle
    month_order = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]
    df["Month"] = pd.Categorical(df["Month"], categories=month_order, ordered=True)

    monthly = df.groupby(["Month", "Scope"])["Emissions (tCO2e)"].sum().reset_index()

    fig_trend = px.bar(
        monthly,
        x="Month",
        y="Emissions (tCO2e)",
        color="Scope",
        color_discrete_map={
            "Scope 1": "#1f77b4",
            "Scope 2": "#ff7f0e",
            "Scope 3": "#2ca02c"
        },
        barmode="stack"
    )
    fig_trend.update_layout(
        xaxis=dict(categoryorder="array", categoryarray=month_order),
        paper_bgcolor="#121212",
        plot_bgcolor="#121212",
        font_color="white"
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    # --- Emissions Log (Bottom) ---
    st.subheader("📜 Emissions Log")
    st.dataframe(st.session_state.data, use_container_width=True)
else:
    st.info("No emissions data available. Please add activities from the sidebar.")
