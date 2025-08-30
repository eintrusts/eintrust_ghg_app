import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- Page config ---
st.set_page_config(page_title="EinTrust", page_icon="🌏", layout="wide")
st.title("Einboard")
st.markdown("Estimate Scope 1, 2, and 3 emissions using activity data and emission factors.")

# --- Load emission factors ---
try:
    emission_factors = pd.read_csv("emission_factors.csv")
except FileNotFoundError:
    st.error("emission_factors.csv not found in the same folder.")
    emission_factors = pd.DataFrame(columns=["scope","category","activity","unit","emission_factor","cost_per_unit_inr"])

# --- Session state ---
if "emissions_log" not in st.session_state:
    st.session_state.emissions_log = []

def update_summary():
    summary = {"Scope 1":{"emissions":0,"cost":0},
               "Scope 2":{"emissions":0,"cost":0},
               "Scope 3":{"emissions":0,"cost":0}}
    for e in st.session_state.emissions_log:
        summary[e["Scope"]]["emissions"] += e["Emissions (tCO2e)"]
        summary[e["Scope"]]["cost"] += e["Cost (INR)"]
    st.session_state.summary = summary

# --- Sidebar Navigation ---
nav_choice = st.sidebar.radio("Navigation", ["Dashboard", "Input CSV"], index=1)

# --- CSV Upload ---
if nav_choice == "Input CSV":
    st.header("Upload Activity Data")
    st.markdown("CSV columns required: Scope, Category, Activity, Quantity")
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        required_cols = {"Scope","Category","Activity","Quantity"}
        if not required_cols.issubset(df.columns):
            st.error(f"CSV must have columns: {required_cols}")
        else:
            for _, row in df.iterrows():
                scope = row["Scope"]
                category = row.get("Category","-")
                activity = row["Activity"]
                quantity = float(row["Quantity"])
                ef_df = emission_factors[(emission_factors["scope"]==scope)&(emission_factors["activity"]==activity)]
                if scope=="Scope 3":
                    ef_df = ef_df[ef_df["category"]==category]
                if not ef_df.empty:
                    ef = ef_df["emission_factor"].values[0]
                    unit = ef_df["unit"].values[0]
                    cost_unit = ef_df["cost_per_unit_inr"].values[0]
                    emissions = quantity*ef
                    cost = quantity*cost_unit
                    st.session_state.emissions_log.append({
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Scope": scope,
                        "Category": category,
                        "Activity": activity,
                        "Quantity": quantity,
                        "Unit": unit,
                        "Emission Factor": ef,
                        "Emissions (tCO2e)": emissions,
                        "Cost (INR)": cost
                    })
                else:
                    st.warning(f"No emission factor found for Activity: {activity}, Scope: {scope}, Category: {category}")
            update_summary()
            st.success("CSV processed successfully!")

# --- Dashboard ---
else:
    with st.expander("📄 View Emission Factors Table"):
        st.dataframe(emission_factors)

    st.sidebar.header("Add Activity Entry")
    scope_options = emission_factors["scope"].dropna().unique()
    selected_scope = st.sidebar.selectbox("Select Scope", scope_options)
    filtered_df = emission_factors[emission_factors["scope"]==selected_scope]

    if selected_scope=="Scope 3":
        category_options = filtered_df["category"].dropna().unique()
        selected_category = st.sidebar.selectbox("Select Scope 3 Category", category_options)
        category_df = filtered_df[filtered_df["category"]==selected_category]
        activity_options = category_df["activity"].dropna().unique()
    else:
        selected_category = "-"
        activity_options = filtered_df["activity"].dropna().unique()

    selected_activity = st.sidebar.selectbox("Select Activity", activity_options)
    activity_df = filtered_df if selected_scope!="Scope 3" else category_df[category_df["activity"]==selected_activity]

    if not activity_df.empty:
        ef = activity_df["emission_factor"].values[0]
        unit = activity_df["unit"].values[0]
        cost_unit = activity_df["cost_per_unit_inr"].values[0]
    else:
        ef, unit, cost_unit = 0, "-", 0

    quantity = st.sidebar.number_input(f"Enter Quantity ({unit})", min_value=0.0, format="%.4f")
    if st.sidebar.button("Add Entry") and quantity>0 and ef>0:
        emissions = quantity*ef
        cost = quantity*cost_unit
        st.session_state.emissions_log.append({
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Scope": selected_scope,
            "Category": selected_category,
            "Activity": selected_activity,
            "Quantity": quantity,
            "Unit": unit,
            "Emission Factor": ef,
            "Emissions (tCO2e)": emissions,
            "Cost (INR)": cost
        })
        update_summary()

    st.subheader("📊 Emission Summary")
    if st.session_state.emissions_log:
        chart_df = pd.DataFrame([{"Scope":k,"Emissions":v["emissions"],"Cost (INR)":v["cost"]} for k,v in st.session_state.summary.items()])
        chart_df = chart_df[chart_df["Emissions"]>0]
        if not chart_df.empty:
            fig = px.pie(chart_df, names="Scope", values="Emissions", hole=0.4, title="Emissions by Scope")
            st.plotly_chart(fig, use_container_width=True)
        st.dataframe(chart_df, use_container_width=True)
    else:
        st.info("No emissions data yet. Add from sidebar or upload CSV.")
