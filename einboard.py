import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from PIL import Image
import requests
from io import BytesIO

# --- Page Config ---
st.set_page_config(page_title="EinTrust GHG Dashboard", page_icon="🌍", layout="wide")

# --- Custom CSS for colors and background ---
st.markdown(
    """
    <style>
    /* Set off-white background */
    .stApp {
        background-color: #fefcf5;
    }
    /* Royal blue headings */
    .stHeader, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #4169E1;
    }
    /* Forest green normal text */
    .stText, .stMarkdown p, .stTextInput>div>div>input {
        color: #228B22;
    }
    /* Sidebar background */
    .css-1d391kg {  /* sidebar container */
        background-color: #fefcf5;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Einboard")
st.markdown("Estimate Scope 1, 2, and 3 emissions for net zero journey.")

# --- Sidebar: GitHub Profile Photo Only ---
GITHUB_PROFILE_PHOTO_URL = "https://github.com/eintrusts.png"
try:
    response = requests.get(GITHUB_PROFILE_PHOTO_URL)
    response.raise_for_status()
    img = Image.open(BytesIO(response.content))
    st.sidebar.image(img, use_container_width=True)
except Exception as e:
    st.sidebar.write("Logo not available:", e)

# --- Load Emission Factors ---
try:
    emission_factors = pd.read_csv("emission_factors.csv")
except FileNotFoundError:
    emission_factors = pd.DataFrame(columns=["scope","category","activity","unit","emission_factor"])
    st.warning("Emission factors file not found. Dashboard will work, but no emissions can be calculated.")

# --- Session State ---
if "emissions_summary" not in st.session_state:
    st.session_state.emissions_summary = {"Scope 1":0, "Scope 2":0, "Scope 3":0}
if "emissions_log" not in st.session_state:
    st.session_state.emissions_log = []

# --- Sidebar Input ---
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

        # Update summary
        summary = {"Scope 1":0,"Scope 2":0,"Scope 3":0}
        for e in st.session_state.emissions_log:
            summary[e["Scope"]] += e["Emissions (tCO₂e)"]
        st.session_state.emissions_summary = summary

# --- Main Dashboard ---
col1, col2 = st.columns([1,2])

with col1:
    st.subheader("📅 Latest Emission Entry")
    if st.session_state.emissions_log:
        latest = st.session_state.emissions_log[-1]
        for k,v in latest.items():
            st.markdown(f"- {k}: {v}")
    else:
        st.info("No data yet. Add from sidebar.")

with col2:
    st.subheader("📊 Emission Breakdown by Scope")
    chart_df = pd.DataFrame.from_dict(st.session_state.emissions_summary, orient="index", columns=["Emissions"])
    chart_df = chart_df.reset_index().rename(columns={"index":"Scope"})
    chart_df = chart_df[chart_df["Emissions"]>0]

    if not chart_df.empty:
        fig = px.pie(chart_df, names="Scope", values="Emissions",
                     color_discrete_sequence=px.colors.sequential.Purples_r, hole=0.45)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data to show chart.")

# --- Emission Log ---
if st.session_state.emissions_log:
    st.subheader("📂 Emissions Log")
    log_df = pd.DataFrame(st.session_state.emissions_log)
    log_df.index = range(1,len(log_df)+1)

    selected_rows = st.multiselect("Select rows to delete", options=log_df.index.tolist(), default=[])
    if st.button("Delete Selected Rows") and selected_rows:
        log_df = log_df.drop(index=selected_rows)
        st.session_state.emissions_log = log_df.to_dict(orient="records")

        summary = {"Scope 1":0,"Scope 2":0,"Scope 3":0}
        for e in st.session_state.emissions_log:
            summary[e["Scope"]] += e["Emissions (tCO₂e)"]
        st.session_state.emissions_summary = summary

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
    st.dataframe(final_df, use_container_width=True)
else:
    st.info("No emission log data yet.")
