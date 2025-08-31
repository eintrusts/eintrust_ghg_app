import streamlit as st
import pandas as pd
import plotly.express as px

# --- Page Config ---
st.set_page_config(page_title="EinTrust ESG Dashboard", page_icon="🌍", layout="wide")

# --- Sidebar Tabs ---
tab = st.sidebar.radio("Navigation", ["Input Data", "Dashboard"])

# --- Load Emission Factors ---
try:
    emission_factors = pd.read_csv("emission_factors.csv")
except:
    st.error("⚠️ emission_factors.csv not found. Please upload it.")

# --- Data Store in Session ---
if "ghg_data" not in st.session_state:
    st.session_state.ghg_data = pd.DataFrame(columns=["Category", "Activity", "Amount", "Unit", "Scope", "Emissions (tCO2e)"])

# --- Input Data Tab ---
if tab == "Input Data":
    st.title("🌍 Input GHG Activity Data")

    with st.form("ghg_form"):
        category = st.selectbox("Select Category", ["Fuel", "Electricity", "Travel"])
        activity = st.text_input("Activity Name (e.g., Diesel, Grid Electricity, Flight)")
        amount = st.number_input("Amount Consumed", min_value=0.0, step=0.1)
        unit = st.text_input("Unit (e.g., Litre, kWh, km)")
        scope = st.selectbox("Scope", ["Scope 1", "Scope 2", "Scope 3"])

        # Lookup emission factor
        ef = 0
        if "emission_factors" in locals():
            match = emission_factors[emission_factors["Activity"].str.lower() == activity.lower()]
            if not match.empty:
                ef = match["EF"].values[0]  # Emission factor
        emissions = amount * ef

        submitted = st.form_submit_button("Add Entry")

        if submitted:
            new_entry = {
                "Category": category,
                "Activity": activity,
                "Amount": amount,
                "Unit": unit,
                "Scope": scope,
                "Emissions (tCO2e)": emissions
            }
            st.session_state.ghg_data = pd.concat([st.session_state.ghg_data, pd.DataFrame([new_entry])], ignore_index=True)
            st.success("✅ Entry added!")

    st.subheader("Current GHG Data")
    st.dataframe(st.session_state.ghg_data)

# --- Dashboard Tab ---
elif tab == "Dashboard":
    st.title("📊 ESG Dashboard")

    if st.session_state.ghg_data.empty:
        st.warning("No data yet. Please add activity data in the Input tab.")
    else:
        df = st.session_state.ghg_data

        # --- KPI cards ---
        total_emissions = df["Emissions (tCO2e)"].sum()
        scope1 = df[df["Scope"]=="Scope 1"]["Emissions (tCO2e)"].sum()
        scope2 = df[df["Scope"]=="Scope 2"]["Emissions (tCO2e)"].sum()
        scope3 = df[df["Scope"]=="Scope 3"]["Emissions (tCO2e)"].sum()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Emissions", f"{total_emissions:.2f} tCO2e")
        col2.metric("Scope 1", f"{scope1:.2f} tCO2e")
        col3.metric("Scope 2", f"{scope2:.2f} tCO2e")
        col4.metric("Scope 3", f"{scope3:.2f} tCO2e")

        # --- Pie chart: Scope breakdown ---
        scope_summary = df.groupby("Scope")["Emissions (tCO2e)"].sum().reset_index()
        fig1 = px.pie(scope_summary, values="Emissions (tCO2e)", names="Scope", title="GHG Emissions by Scope")
        st.plotly_chart(fig1, use_container_width=True)

        # --- Bar chart: Category emissions ---
        category_summary = df.groupby("Category")["Emissions (tCO2e)"].sum().reset_index()
        fig2 = px.bar(category_summary, x="Category", y="Emissions (tCO2e)", title="Emissions by Category", text_auto=True)
        st.plotly_chart(fig2, use_container_width=True)

        # --- Placeholder for ESG Metrics ---
        st.subheader("🌱 ESG Metrics (Summary)")
        col1, col2, col3 = st.columns(3)
        col1.metric("Energy Consumed", "Coming Soon")
        col2.metric("Water Usage", "Coming Soon")
        col3.metric("CSR Spend", "Coming Soon")
