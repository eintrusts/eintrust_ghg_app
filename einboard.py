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
    "Scope 1": {
        "Stationary Combustion": {
            "Diesel Generator": "Generator running on diesel for electricity",
            "Petrol Generator": "Generator running on petrol for electricity",
            "LPG Boiler": "Boiler or stove using LPG",
            "Coal Boiler": "Boiler/furnace burning coal",
            "Biomass Furnace": "Furnace burning wood/agricultural residue"
        },
        "Mobile Combustion": {
            "Diesel Vehicle": "Truck/van running on diesel",
            "Petrol Car": "Car/van running on petrol",
            "CNG Vehicle": "Bus or delivery vehicle running on CNG",
            "Diesel Forklift": "Forklift running on diesel",
            "Petrol Two-Wheeler": "Scooter or bike running on petrol"
        },
        "Process Emissions": {
            "Cement Production": "CO₂ from cement making",
            "Steel Production": "CO₂ from steel processing",
            "Brick Kiln": "CO₂ from brick firing",
            "Textile Processing": "Emissions from dyeing/fabric processing",
            "Chemical Manufacturing": "Emissions from chemical reactions",
            "Food Processing": "Emissions from cooking/heating"
        },
        "Fugitive Emissions": {
            "Refrigerant (HFC/HCFC)": "Gas leak from AC/refrigerator",
            "Methane (CH₄)": "Methane leaks from storage/pipelines",
            "SF₆": "Gas leak from electrical equipment"
        }
    },
    "Scope 2": {
        "Electricity Consumption": {"Grid Electricity": "Electricity bought from grid",
                                    "Diesel Generator Electricity": "Electricity generated on-site with diesel"},
        "Steam / Heat": {"Purchased Steam": "Steam bought from external supplier"},
        "Cooling / Chilled Water": {"Purchased Cooling": "Cooling bought from supplier"}
    },
    "Scope 3": {
        "Purchased Goods & Services": {
            "Raw Materials": ["Cement", "Steel", "Chemicals", "Textile"],
            "Packaging Materials": ["Cardboard", "Plastics", "Glass"],
            "Office Supplies": ["Paper", "Ink", "Stationery"],
            "Purchased Services": ["Printing", "Logistics", "Cleaning", "IT"]
        },
        "Business Travel": {
            "Air Travel": None,
            "Train Travel": None,
            "Taxi / Cab / Auto": None
        },
        "Employee Commuting": {
            "Two-Wheelers": None,
            "Cars / Vans": None,
            "Public Transport": None
        },
        "Waste Generated": {
            "Landfill": None,
            "Recycling": None,
            "Composting / Biogas": None
        },
        "Upstream Transportation & Distribution": {
            "Incoming Goods Transport": None,
            "Third-party Logistics": None
        },
        "Downstream Transportation & Distribution": {
            "Delivery to Customers": None,
            "Retail / Distributor Transport": None
        },
        "Use of Sold Products": {"Product Use": None},
        "End-of-Life Treatment": {"Recycling / Landfill": None}
    }
}

units_dict = {
    "Diesel Generator": "Liters", "Petrol Generator": "Liters", "LPG Boiler": "Liters", 
    "Coal Boiler": "kg", "Biomass Furnace": "kg", "Diesel Vehicle": "Liters", 
    "Petrol Car": "Liters", "CNG Vehicle": "m³", "Diesel Forklift": "Liters", 
    "Petrol Two-Wheeler": "Liters", "Cement Production": "Tonnes", "Steel Production": "Tonnes",
    "Brick Kiln": "Tonnes", "Textile Processing": "Tonnes", "Chemical Manufacturing": "Tonnes",
    "Food Processing": "Tonnes", "Refrigerant (HFC/HCFC)": "kg", "Methane (CH₄)": "kg",
    "SF₆": "kg", "Grid Electricity": "kWh", "Diesel Generator Electricity": "kWh",
    "Purchased Steam": "Tonnes", "Purchased Cooling": "kWh"
}

# ---------------------------
# Sidebar
# ---------------------------
with st.sidebar:
    st.image("https://github.com/eintrusts/eintrust_ghg_app/raw/main/EinTrust%20%20logo.png", use_container_width=True)
    st.markdown("---")

    st.button("Home", on_click=lambda: st.session_state.update({"page": "Home"}))

    with st.expander("Environment", expanded=True):
        st.button("GHG", on_click=lambda: st.session_state.update({"page": "GHG"}))
        st.button("Energy", on_click=lambda: st.session_state.update({"page": "Energy"}))
        st.button("Water", on_click=lambda: st.session_state.update({"page": "Water"}))
        st.button("Waste", on_click=lambda: st.session_state.update({"page": "Waste"}))
        st.button("Biodiversity", on_click=lambda: st.session_state.update({"page": "Biodiversity"}))

    with st.expander("Social", expanded=False):
        st.button("Employee", on_click=lambda: st.session_state.update({"page": "Employee"}))
        st.button("Health & Safety", on_click=lambda: st.session_state.update({"page": "Health & Safety"}))
        st.button("CSR", on_click=lambda: st.session_state.update({"page": "CSR"}))

    with st.expander("Governance", expanded=False):
        st.button("Board", on_click=lambda: st.session_state.update({"page": "Board"}))
        st.button("Policies", on_click=lambda: st.session_state.update({"page": "Policies"}))
        st.button("Compliance", on_click=lambda: st.session_state.update({"page": "Compliance"}))
        st.button("Risk Management", on_click=lambda: st.session_state.update({"page": "Risk Management"}))

# ---------------------------
# Helper Functions
# ---------------------------
def format_indian(n):
    try:
        n = float(n)
        return "{:,.2f}".format(n)
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

    # Stacked bar chart (Month x Scope)
    trend_df = df.groupby(["Month","Scope"])["Quantity"].sum().reset_index()
    fig = px.bar(trend_df, x="Month", y="Quantity", color="Scope", barmode="stack", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# Main Pages
# ---------------------------
st.title("🌍 EinTrust Dashboard")
page = st.session_state.page

if page == "Home":
    render_dashboard(st.session_state.entries)
elif page == "GHG":
    # Manual Entry
    scope = st.selectbox("Select Scope", ["Scope 1",
