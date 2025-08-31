import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px

# ---------------------------
# Page Config
# ---------------------------
st.set_page_config(page_title="EinTrust Dashboard", page_icon="🌍", layout="wide")

# ---------------------------
# Initialize Session State
# ---------------------------
if "entries" not in st.session_state:
    st.session_state.entries = pd.DataFrame(columns=[
        "Scope", "Activity", "Sub-Activity", "Specific Item", "Quantity", "Unit", "Date"
    ])
if "page" not in st.session_state:
    st.session_state.page = "Home"

# ---------------------------
# Helper Dictionaries
# ---------------------------
scope_activities = {
    "Scope 1": {"Stationary Combustion": {"Diesel Generator": "Generator running on diesel",
                                          "Petrol Generator": "Generator running on petrol"},
                "Mobile Combustion": {"Diesel Vehicle": "Truck/van running on diesel"}},
    "Scope 2": {"Electricity Consumption": {"Grid Electricity": "Electricity bought from grid"}},
    "Scope 3": {"Purchased Goods & Services": {"Raw Materials": ["Cement", "Steel"]}}
}

units_dict = {
    "Diesel Generator": "Liters", "Petrol Generator": "Liters",
    "Diesel Vehicle": "Liters", "Grid Electricity": "kWh",
    "Cement": "Tonnes", "Steel": "Tonnes"
}

# ---------------------------
# Sidebar
# ---------------------------
with st.sidebar:
    st.title("EinTrust")
    st.button("Home", on_click=lambda: st.session_state.update({"page": "Home"}))
    with st.expander("Environment", expanded=True):
        st.button("GHG", on_click=lambda: st.session_state.update({"page": "GHG"}))
    with st.expander("Social"):
        st.button("Employee", on_click=lambda: st.session_state.update({"page": "Employee"}))
    with st.expander("Governance"):
        st.button("Policies", on_click=lambda: st.session_state.update({"page": "Policies"}))

# ---------------------------
# Helper Functions
# ---------------------------
def format_indian(n):
    try:
        return "{:,.2f}".format(float(n))
    except:
        return n

def render_dashboard(df_entries):
    st.subheader("🌱 GHG Emissions Dashboard")
    if df_entries.empty or "Date" not in df_entries.columns:
        st.info("No manual entries yet.")
        return

    df = df_entries.copy()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])
    df["Month"] = df["Date"].dt.to_period("M").astype(str)

    # KPI totals
    s1 = df[df["Scope"]=="Scope 1"]["Quantity"].sum()
    s2 = df[df["Scope"]=="Scope 2"]["Quantity"].sum()
    s3 = df[df["Scope"]=="Scope 3"]["Quantity"].sum()
    total = s1 + s2 + s3

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Emissions", format_indian(total))
    c2.metric("Scope 1", format_indian(s1))
    c3.metric("Scope 2", format_indian(s2))
    c4.metric("Scope 3", format_indian(s3))

    # Stacked bar chart
    trend_df = df.groupby(["Month","Scope"])["Quantity"].sum().reset_index()
    fig = px.bar(trend_df, x="Month", y="Quantity", color="Scope", barmode="stack", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# Main Pages
# ---------------------------
page = st.session_state.page
if page == "Home":
    render_dashboard(st.session_state.entries)

elif page == "GHG":
    st.subheader("🌍 Add GHG Entry")
    scope = st.selectbox("Select Scope", ["Scope 1", "Scope 2", "Scope 3"])
    activity = st.selectbox("Select Activity / Category", list(scope_activities[scope].keys()))
    sub_options = scope_activities[scope][activity]
    
    if scope != "Scope 3":
        sub_activity = st.selectbox("Select Sub-Activity", list(sub_options.keys()))
        st.info(sub_options[sub_activity])
        specific_item = None
    else:
        sub_activity = st.selectbox("Select Sub-Category", list(sub_options.keys()))
        items = sub_options[sub_activity]
        specific_item = st.selectbox("Select Specific Item", items) if items is not None else None

    unit = units_dict.get(specific_item or sub_activity, "")
    quantity = st.number_input(f"Enter Quantity ({unit})", min_value=0.0, format="%.2f")
    date = st.date_input("Date of Entry", datetime.today())

    uploaded_file = st.file_uploader("Upload Bill / File (CSV/XLS/XLSX/PDF)", type=["csv","xls","xlsx","pdf"])

    if st.button("Add Manual Entry"):
        new_entry = {
            "Scope": scope,
            "Activity": activity,
            "Sub-Activity": sub_activity,
            "Specific Item": specific_item or "",
            "Quantity": quantity,
            "Unit": unit,
            "Date": date
        }
        st.session_state.entries = pd.concat([st.session_state.entries, pd.DataFrame([new_entry])], ignore_index=True)
        st.success("Manual entry added!")

    if not st.session_state.entries.empty:
        st.subheader("All Manual Entries")
        display_df = st.session_state.entries.copy()
        display_df["Quantity"] = display_df["Quantity"].apply(format_indian)
        st.dataframe(display_df)

        csv = display_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Entries as CSV", csv, "ghg_entries.csv", "text/csv")
