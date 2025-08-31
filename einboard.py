import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import requests
from io import BytesIO

# --- Page Config ---
st.set_page_config(page_title="EinTrust GHG Dashboard", page_icon="🌍", layout="wide")

# --- Dark Theme Styling ---
st.markdown("""
    <style>
    .stApp {background-color: #121212; color: #e0e0e0;}
    h1, h2, h3, h4, h5, h6 {color: #ffffff;}
    .stMetric {background-color: #1e1e1e; padding: 10px; border-radius: 10px;}
    </style>
""", unsafe_allow_html=True)

# --- Sidebar with Logo ---
st.sidebar.title("EinTrust GHG Dashboard")

# Add EinTrust logo from GitHub
logo_url = "https://avatars.githubusercontent.com/u/179835251?s=200&v=4"
try:
    response = requests.get(logo_url)
    if response.status_code == 200:
        logo = BytesIO(response.content)
        st.sidebar.image(logo, use_container_width=True)
    else:
        st.sidebar.write("🔗 Logo not available")
except:
    st.sidebar.write("⚠️ Error loading logo")

st.sidebar.markdown("---")

# --- Initialize Session State ---
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["Date", "Activity", "Scope", "Emissions (tCO2e)"])

if "archive" not in st.session_state:
    st.session_state.archive = None

# --- Add Data Form (Sidebar) ---
with st.sidebar.form("data_entry", clear_on_submit=True):
    st.subheader("➕ Add Activity Data")
    activity = st.text_input("Activity Description")
    scope = st.selectbox("Scope", ["Scope 1", "Scope 2", "Scope 3"])
    emissions = st.number_input("Emissions (tCO2e)", min_value=0.0, step=0.01)
    submitted = st.form_submit_button("Add Entry")

    if submitted and activity and emissions > 0:
        new_entry = {
            "Date": datetime.now(),
            "Activity": activity,
            "Scope": scope,
            "Emissions (tCO2e)": emissions
        }
        st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_entry])], ignore_index=True)
        st.sidebar.success("✅ Entry added!")

# --- Archive & Reset ---
if st.sidebar.button("📦 Archive & Reset"):
    if not st.session_state.data.empty:
        st.session_state.archive = st.session_state.data.copy()
        st.session_state.data = pd.DataFrame(columns=["Date", "Activity", "Scope", "Emissions (tCO2e)"])
        st.sidebar.success("📂 Data archived & reset!")

# --- Download Archived Data ---
if st.session_state.archive is not None:
    csv = st.session_state.archive.to_csv(index=False).encode("utf-8")
    st.sidebar.download_button("⬇️ Download Last Archive", csv, "emissions_archive.csv", "text/csv")

# --- Dashboard Title ---
st.title("🌍 EinTrust GHG Dashboard")

if not st.session_state.data.empty:
    df = st.session_state.data.copy()

    # Convert numbers to Indian system
    def format_num(num):
        return f"{num:,.0f}".replace(",", "X").replace("X", ",").replace(",", "X").replace("X", ",")

    total_emissions = df["Emissions (tCO2e)"].sum()
    scope1 = df[df["Scope"] == "Scope 1"]["Emissions (tCO2e)"].sum()
    scope2 = df[df["Scope"] == "Scope 2"]["Emissions (tCO2e)"].sum()
    scope3 = df[df["Scope"] == "Scope 3"]["Emissions (tCO2e)"].sum()

    # --- Key Indicators ---
    st.subheader("📊 Key Emission Indicators")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Emissions", format_num(total_emissions))
    col2.metric("Scope 1", format_num(scope1))
    col3.metric("Scope 2", format_num(scope2))
    col4.metric("Scope 3", format_num(scope3))

    # --- Emission Breakdown by Scope ---
    st.subheader("📌 Emission Breakdown by Scope")
    fig_pie = px.pie(df, names="Scope", values="Emissions (tCO2e)",
                     color="Scope",
                     color_discrete_map={"Scope 1": "#ff6b6b", "Scope 2": "#4ecdc4", "Scope 3": "#ffe66d"})
    st.plotly_chart(fig_pie, use_container_width=True)

    # --- Emissions Trend (Apr–Mar, stacked) ---
    st.subheader("📈 Emissions Trend Over Time (Monthly — Apr→Mar)")
    df["Month"] = df["Date"].dt.strftime("%b")
    df["Year"] = df["Date"].dt.year

    # Reorder Apr–Mar
    month_order = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]
    df["Month"] = pd.Categorical(df["Month"], categories=month_order, ordered=True)

    monthly_trend = df.groupby(["Year", "Month", "Scope"])["Emissions (tCO2e)"].sum().reset_index()
    fig_area = px.area(monthly_trend, x="Month", y="Emissions (tCO2e)", color="Scope",
                       color_discrete_map={"Scope 1": "#ff6b6b", "Scope 2": "#4ecdc4", "Scope 3": "#ffe66d"},
                       groupnorm=None)
    st.plotly_chart(fig_area, use_container_width=True)

    # --- Emissions Log ---
    st.subheader("📑 Emissions Log")
    st.dataframe(df[["Date", "Activity", "Scope", "Emissions (tCO2e)"]], use_container_width=True)

else:
    st.info("No emissions data available. Please add activity data from the sidebar.")
