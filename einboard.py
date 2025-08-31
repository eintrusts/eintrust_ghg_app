import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from PIL import Image
import requests
from io import BytesIO
import time

# --- Page Config ---
st.set_page_config(page_title="EinTrust GHG Dashboard", page_icon="🌍", layout="wide")

# --- Custom CSS for Dark Energy-Saving Theme + Sidebar Cards + Glowing Active Tab ---
st.markdown("""
<style>
.stApp { background-color: #121212; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #d3d3d3; }
[data-testid="stSidebar"] { background-color: #1a1a1a; padding-top: 20px; }
.sidebar-button { background-color: #1f1f1f; color: #228B22; font-weight: bold; border-radius: 8px; padding: 10px 15px; margin-bottom: 10px; text-align: center; cursor: pointer; transition: all 0.3s ease; }
.sidebar-button:hover { background-color: #228B22; color: #ffffff; }
.sidebar-button.active { background-color: #4169E1; color: white; box-shadow: 0 0 15px #4169E1; animation: glow 1.5s infinite alternate; }
@keyframes glow { from { box-shadow: 0 0 10px #4169E1; } to { box-shadow: 0 0 25px #4169E1; } }
h1,h2,h3,.stMarkdown h1,.stMarkdown h2,.stMarkdown h3 { color: #4169E1; font-weight: 700; }
.card, .metric-card, .chart-card, .table-card { background-color: #1f1f1f; border-radius: 10px; padding: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); margin-bottom: 20px; }
.metric-card { text-align: center; color: #ffffff; transition: transform 0.3s; }
.metric-card h2 { margin: 5px 0; color: #4169E1; }
.metric-card p { margin: 0; color: #228B22; font-size: 18px; }
.chart-card, .table-card { padding: 20px; }
.table-card table { color: #d3d3d3; border-collapse: collapse; width: 100%; }
.table-card th { background-color: #228B22; color: white; padding: 8px; text-align: left; }
.table-card td { padding: 8px; text-align: left; }
.table-card tr:hover { background-color: #2a2a2a; }
</style>
""", unsafe_allow_html=True)

# --- Sidebar: GitHub Logo ---
GITHUB_PROFILE_PHOTO_URL = "https://github.com/eintrusts.png"
try:
    response = requests.get(GITHUB_PROFILE_PHOTO_URL)
    response.raise_for_status()
    img = Image.open(BytesIO(response.content))
    st.sidebar.image(img, use_container_width=True)
except:
    st.sidebar.write("Logo not available")

# --- Sidebar Tabs ---
tab = st.sidebar.radio("Navigation", ["Dashboard", "Profile"], index=0)

# --- Session State ---
if "emissions_summary" not in st.session_state:
    st.session_state.emissions_summary = {"Scope 1":0, "Scope 2":0, "Scope 3":0}
if "emissions_log" not in st.session_state:
    st.session_state.emissions_log = []

# --- Load Emission Factors ---
try:
    emission_factors = pd.read_csv("emission_factors.csv")
except FileNotFoundError:
    emission_factors = pd.DataFrame(columns=["scope","category","activity","unit","emission_factor"])
    st.warning("Emission factors file not found. Dashboard will work, but no emissions can be calculated.")

# --- Profile Tab ---
if tab == "Profile":
    st.title("EinTrust GHG Dashboard - Company Profile")
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.text_input("Company Name", value="EinTrust", disabled=True)
    st.text_input("Username", value="eintrusts", disabled=True)
    photo_file = st.file_uploader("Upload Company Logo / Photo", type=["png","jpg","jpeg"])
    if photo_file:
        img_profile = Image.open(photo_file)
        st.image(img_profile, width=200)
    st.markdown("</div>", unsafe_allow_html=True)

# --- Dashboard Tab ---
else:
    st.title("EinTrust GHG Dashboard")

    # Sidebar Activity Input
    st.sidebar.header("➕ Add Activity Data")
    add_mode = st.sidebar.checkbox("Add Entry Mode", value=False)
    if add_mode and not emission_factors.empty:
        scope_options = emission_factors["scope"].dropna().unique()
        selected_scope = st.sidebar.selectbox("Select Scope", scope_options)
        filtered_df = emission_factors[emission_factors["scope"]==selected_scope]

        if selected_scope=="Scope 3":
            category_options = filtered_df["category"].dropna().unique()
            selected_category = st.sidebar.selectbox("Select Scope 3 Category", category_options)
            category_df = filtered_df[filtered_df["category"]==selected_category]
            activity_options = category_df["activity"].dropna().unique()
            selected_activity = st.sidebar.selectbox("Select Activity", activity_options)
            activity_df = category_df[category_df["activity"]==selected_activity]
        else:
            selected_category = "-"
            activity_options = filtered_df["activity"].dropna().unique()
            selected_activity = st.sidebar.selectbox("Select Activity", activity_options)
            activity_df = filtered_df[filtered_df["activity"]==selected_activity]

        if not activity_df.empty:
            unit = activity_df["unit"].values[0]
            ef = activity_df["emission_factor"].values[0]
        else:
            unit = "-"
            ef = 0

        quantity = st.sidebar.number_input(f"Enter quantity ({unit})", min_value=0.0, format="%.4f")

        if st.sidebar.button("Add Entry") and quantity>0 and ef>0:
            emissions = quantity*ef
            new_entry = {
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Scope": selected_scope,
                "Category": selected_category,
                "Activity": selected_activity,
                "Quantity": quantity,
                "Unit": unit,
                "Emission Factor": ef,
                "Emissions (tCO₂e)": emissions
            }
            st.session_state.emissions_log.append(new_entry)
            summary = {"Scope 1":0,"Scope 2":0,"Scope 3":0}
            for e in st.session_state.emissions_log:
                summary[e["Scope"]] += e["Emissions (tCO₂e)"]
            st.session_state.emissions_summary = summary

    # --- Animated Metric Cards ---
    st.subheader("📊 Emissions Summary")
    col1, col2, col3 = st.columns(3)
    for i, scope in enumerate(["Scope 1", "Scope 2", "Scope 3"]):
        with [col1, col2, col3][i]:
            placeholder = st.empty()
            target = st.session_state.emissions_summary.get(scope,0)
            value = 0
            for _ in range(30):
                value += target / 30
                placeholder.markdown(f"<div class='metric-card'><h2>{scope}</h2><p>{value:.2f} tCO₂e</p></div>", unsafe_allow_html=True)
                time.sleep(0.03)

    # Latest Entry
    st.subheader("📅 Latest Emission Entry")
    if st.session_state.emissions_log:
        latest = st.session_state.emissions_log[-1]
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        for k,v in latest.items():
            st.markdown(f"**{k}:** {v}")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No data yet. Add from sidebar.")

    # Pie Chart with Animation
    st.subheader("📈 Emission Breakdown by Scope")
    chart_df = pd.DataFrame.from_dict(st.session_state.emissions_summary, orient="index", columns=["Emissions"])
    chart_df = chart_df.reset_index().rename(columns={"index":"Scope"})
    chart_df = chart_df[chart_df["Emissions"]>0]

    if not chart_df.empty:
        colors = ['#4169E1', '#228B22', '#1F3A93']
        fig_placeholder = st.empty()
        # Animated pie chart
        for frac in range(1, 101, 5):
            chart_df["Emissions_frac"] = chart_df["Emissions"] * frac / 100
            fig = px.pie(chart_df, names="Scope", values="Emissions_frac",
                         color="Scope", color_discrete_sequence=colors, hole=0.45)
            fig.update_traces(textinfo='percent+label', textfont_size=14)
            fig_placeholder.plotly_chart(fig, use_container_width=True)
            time.sleep(0.03)
    else:
        st.info("No data to show chart.")

    # Emission Log Table
    if st.session_state.emissions_log:
        st.subheader("📂 Emissions Log")
        log_df = pd.DataFrame(st.session_state.emissions_log)
        log_df.index = range(1,len(log_df)+1)

        total_row = pd.DataFrame([{
            "Timestamp":"-",
            "Scope":"Total",
            "Category":"-",
            "Activity":"-",
            "Quantity":log_df["Quantity"].sum(),
            "Unit":"",
            "Emission Factor":"-",
            "Emissions (tCO₂e)":log_df["Emissions (tCO₂e)"].sum()
        }])
        final_df = pd.concat([log_df,total_row], ignore_index=True)
        final_df.index = range(1,len(final_df)+1)

        st.markdown("<div class='table-card'>", unsafe_allow_html=True)
        st.dataframe(final_df, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No emission log data yet.")
