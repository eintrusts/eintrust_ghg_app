import streamlit as st
import pandas as pd
import plotly.express as px

# --- Page Config ---
st.set_page_config(page_title="EinTrust ESG Dashboard", page_icon="🌍", layout="wide")

# --- Sidebar Tabs ---
menu = st.sidebar.radio("Navigation", ["Input Data", "ESG Dashboard"])

# --- Load Emission Factors ---
emission_factors = pd.read_csv("emission_factors.csv")

# Storage for user inputs
if "activity_data" not in st.session_state:
    st.session_state["activity_data"] = []

# ---------------- Input Data ----------------
if menu == "Input Data":
    st.title("GHG Activity Data Entry")

    st.subheader("Add Activity")
    activity = st.selectbox("Activity Type", ["Fuel", "Electricity", "Water", "Waste", "Travel"])
    quantity = st.number_input("Quantity", min_value=0.0, step=0.1)
    unit = st.text_input("Unit (e.g., liters, kWh, m3, kg, km)")

    if st.button("Add Entry"):
        st.session_state["activity_data"].append({"Activity": activity, "Quantity": quantity, "Unit": unit})
        st.success("Activity added!")

    if st.session_state["activity_data"]:
        st.dataframe(pd.DataFrame(st.session_state["activity_data"]))

# ---------------- ESG Dashboard ----------------
if menu == "ESG Dashboard":
    st.title("ESG Dashboard")

    if not st.session_state["activity_data"]:
        st.warning("Please input some data first!")
    else:
        df = pd.DataFrame(st.session_state["activity_data"])

        # --- Dummy GHG calc (replace with EF * qty from CSV) ---
        df["Emissions (tCO2e)"] = df["Quantity"] * 0.1  

        # --- GHG Charts ---
        st.subheader("🌍 GHG Emissions Breakdown")
        scope_pie = px.pie(df, values="Emissions (tCO2e)", names="Activity", title="By Category")
        st.plotly_chart(scope_pie, use_container_width=True)

        bar_chart = px.bar(df, x="Activity", y="Emissions (tCO2e)", title="Emissions by Activity")
        st.plotly_chart(bar_chart, use_container_width=True)

        # --- ESG Metrics (auto-classified) ---
        st.subheader("📊 ESG Metrics Overview")

        col1, col2, col3 = st.columns(3)
        col1.metric("Energy Use (kWh)", df[df["Activity"]=="Electricity"]["Quantity"].sum())
        col2.metric("Water Use (m³)", df[df["Activity"]=="Water"]["Quantity"].sum())
        col3.metric("Waste (kg)", df[df["Activity"]=="Waste"]["Quantity"].sum())

        col4, col5 = st.columns(2)
        col4.metric("Travel (km)", df[df["Activity"]=="Travel"]["Quantity"].sum())
        col5.metric("Fuel Use (liters)", df[df["Activity"]=="Fuel"]["Quantity"].sum())
