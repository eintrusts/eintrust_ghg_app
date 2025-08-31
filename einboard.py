import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------
# Page Config
# ---------------------------
st.set_page_config(page_title="EinTrust Sustainability Dashboard", page_icon="🌍", layout="wide")

# ---------------------------
# Months and Colors
# ---------------------------
months = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]
SCOPE_COLORS = {"Scope 1": "#81c784", "Scope 2": "#4db6ac", "Scope 3": "#aed581"}
ENERGY_COLORS = {"Fossil": "#f39c12", "Renewable": "#2ecc71"}

# ---------------------------
# Session State Initialization
# ---------------------------
if "ghg_entries" not in st.session_state:
    st.session_state.ghg_entries = pd.DataFrame(columns=["Scope","Activity","Sub-Activity","Quantity","Unit","Month"])
if "energy_entries" not in st.session_state:
    st.session_state.energy_entries = pd.DataFrame(columns=["Source","Type","Energy_kWh","CO2e_kg","Month"])
if "water_entries" not in st.session_state:
    st.session_state.water_entries = pd.DataFrame(columns=[
        "Location","Source","Month","Quantity_m3","Cost_INR",
        "Rainwater_Harvested_m3","Water_Recycled_m3","Treatment_Before_Discharge","STP_ETP_Capacity_kL_day"
    ])

if "page" not in st.session_state:
    st.session_state.page = "Home"

# ---------------------------
# Sidebar Navigation
# ---------------------------
def sidebar_button(label):
    if st.button(label):
        st.session_state.page = label

with st.sidebar:
    st.image("https://github.com/eintrusts/eintrust_ghg_app/blob/main/EinTrust%20%20(2).png?raw=true", use_container_width=True)
    st.markdown("---")
    sidebar_button("Home")
    st.markdown("### Environment")
    sidebar_button("GHG")
    sidebar_button("Energy")
    sidebar_button("Water")

# ---------------------------
# KPI Functions
# ---------------------------
def ghg_kpis():
    df = st.session_state.ghg_entries
    total = df["Quantity"].sum() if not df.empty else 0
    scope1 = df[df["Scope"]=="Scope 1"]["Quantity"].sum() if not df.empty else 0
    scope2 = df[df["Scope"]=="Scope 2"]["Quantity"].sum() if not df.empty else 0
    scope3 = df[df["Scope"]=="Scope 3"]["Quantity"].sum() if not df.empty else 0
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total GHG (tCO2e)", f"{total:,.2f}")
    c2.metric("Scope 1", f"{scope1:,.2f}")
    c3.metric("Scope 2", f"{scope2:,.2f}")
    c4.metric("Scope 3", f"{scope3:,.2f}")

def energy_kpis():
    df = st.session_state.energy_entries
    total = df["Energy_kWh"].sum() if not df.empty else 0
    fossil = df[df["Type"]=="Fossil"]["Energy_kWh"].sum() if not df.empty else 0
    renewable = df[df["Type"]=="Renewable"]["Energy_kWh"].sum() if not df.empty else 0
    c1,c2,c3 = st.columns(3)
    c1.metric("Total Energy (kWh)", f"{total:,.0f}")
    c2.metric("Fossil Energy", f"{fossil:,.0f}")
    c3.metric("Renewable Energy", f"{renewable:,.0f}")

def water_kpis():
    df = st.session_state.water_entries
    total_water = df["Quantity_m3"].sum() if not df.empty else 0
    total_cost = df["Cost_INR"].sum() if not df.empty else 0
    recycled_water = df["Water_Recycled_m3"].sum() if not df.empty else 0
    rainwater = df["Rainwater_Harvested_m3"].sum() if not df.empty else 0
    st1,st2,st3,st4 = st.columns(4)
    st1.metric("Total Water (m³)", f"{total_water:,.0f}")
    st2.metric("Total Cost (INR)", f"₹ {total_cost:,.0f}")
    st3.metric("Recycled Water (m³)", f"{recycled_water:,.0f}")
    st4.metric("Rainwater Harvested (m³)", f"{rainwater:,.0f}")

# ---------------------------
# Monthly Charts
# ---------------------------
def ghg_chart():
    df = st.session_state.ghg_entries
    if not df.empty:
        df["Month"] = pd.Categorical(df["Month"], categories=months, ordered=True)
        monthly = df.groupby(["Month","Scope"])["Quantity"].sum().reset_index()
        fig = px.bar(monthly, x="Month", y="Quantity", color="Scope", barmode="stack", color_discrete_map=SCOPE_COLORS)
        st.plotly_chart(fig, use_container_width=True)

def energy_chart():
    df = st.session_state.energy_entries
    if not df.empty:
        df["Month"] = pd.Categorical(df["Month"], categories=months, ordered=True)
        monthly = df.groupby(["Month","Type"])["Energy_kWh"].sum().reset_index()
        fig = px.bar(monthly, x="Month", y="Energy_kWh", color="Type", barmode="stack", color_discrete_map=ENERGY_COLORS)
        st.plotly_chart(fig, use_container_width=True)

def water_chart():
    df = st.session_state.water_entries
    if not df.empty:
        df["Month"] = pd.Categorical(df["Month"], categories=months, ordered=True)
        monthly = df.groupby(["Month","Source"])["Quantity_m3"].sum().reset_index()
        fig = px.line(monthly, x="Month", y="Quantity_m3", color="Source", markers=True)
        st.plotly_chart(fig, use_container_width=True)
        adv = df.groupby("Month")[["Rainwater_Harvested_m3","Water_Recycled_m3"]].sum().reset_index()
        fig2 = px.line(adv, x="Month", y=["Rainwater_Harvested_m3","Water_Recycled_m3"], markers=True)
        st.plotly_chart(fig2, use_container_width=True)

# ---------------------------
# Entry Forms
# ---------------------------
def ghg_form():
    with st.expander("Add GHG Entry"):
        with st.form("ghg_form"):
            scope = st.selectbox("Scope", ["Scope 1","Scope 2","Scope 3"])
            activity = st.text_input("Activity")
            sub_activity = st.text_input("Sub-Activity")
            quantity = st.number_input("Quantity", min_value=0.0, format="%.2f")
            unit = st.text_input("Unit (e.g., tCO2e)")
            month = st.selectbox("Month", months)
            submit = st.form_submit_button("Add Entry")
            if submit:
                st.session_state.ghg_entries.loc[len(st.session_state.ghg_entries)] = [scope, activity, sub_activity, quantity, unit, month]
                st.success("GHG entry added successfully!")

def energy_form():
    with st.expander("Add Energy Entry"):
        with st.form("energy_form"):
            source = st.text_input("Energy Source")
            type_ = st.selectbox("Type", ["Fossil","Renewable"])
            energy_kwh = st.number_input("Energy (kWh)", min_value=0.0, format="%.2f")
            co2e_kg = st.number_input("CO2e (kg)", min_value=0.0, format="%.2f")
            month = st.selectbox("Month", months)
            submit = st.form_submit_button("Add Entry")
            if submit:
                st.session_state.energy_entries.loc[len(st.session_state.energy_entries)] = [source, type_, energy_kwh, co2e_kg, month]
                st.success("Energy entry added successfully!")

def water_form():
    with st.expander("Add Water Entry"):
        with st.form("water_form"):
            location = st.text_input("Location")
            source = st.text_input("Water Source")
            month = st.selectbox("Month", months)
            quantity = st.number_input("Quantity (m³)", min_value=0.0, format="%.2f")
            cost = st.number_input("Cost (INR)", min_value=0.0, format="%.2f")
            rainwater = st.number_input("Rainwater Harvested (m³)", min_value=0.0, format="%.2f")
            recycled = st.number_input("Water Recycled (m³)", min_value=0.0, format="%.2f")
            treatment = st.selectbox("Treatment Before Discharge?", ["Yes","No"])
            stp_capacity = st.number_input("STP/ETP Capacity (kL/day)", min_value=0.0, format="%.2f")
            submit = st.form_submit_button("Add Entry")
            if submit:
                st.session_state.water_entries.loc[len(st.session_state.water_entries)] = [
                    location, source, month, quantity, cost, rainwater, recycled, treatment, stp_capacity
                ]
                st.success("Water entry added successfully!")

# ---------------------------
# Display All Entries with CSV Download
# ---------------------------
def display_entries(df, filename):
    if not df.empty:
        st.dataframe(df)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, file_name=filename, mime="text/csv")

# ---------------------------
# Render Pages
# ---------------------------
if st.session_state.page == "Home":
    st.title("EinTrust Sustainability Dashboard - Summary")
    st.subheader("GHG Emissions")
    ghg_kpis()
    st.subheader("Energy")
    energy_kpis()
    st.subheader("Water")
    water_kpis()

elif st.session_state.page == "GHG":
    st.title("GHG Dashboard")
    ghg_kpis()
    st.subheader("Monthly Trends")
    ghg_chart()
    ghg_form()
    st.subheader("All GHG Entries")
    display_entries(st.session_state.ghg_entries, "ghg_entries.csv")

elif st.session_state.page == "Energy":
    st.title("Energy Dashboard")
    energy_kpis()
    st.subheader("Monthly Trends")
    energy_chart()
    energy_form()
    st.subheader("All Energy Entries")
    display_entries(st.session_state.energy_entries, "energy_entries.csv")

elif st.session_state.page == "Water":
    st.title("Water Dashboard")
    water_kpis()
    st.subheader("Monthly Trends")
    water_chart()
    water_form()
    st.subheader("All Water Entries")
    display_entries(st.session_state.water_entries, "water_entries.csv")
