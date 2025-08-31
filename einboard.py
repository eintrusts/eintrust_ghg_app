import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
import plotly.express as px

# ---------------------------
# Page Config
# ---------------------------
st.set_page_config(page_title="EinTrust Dashboard", page_icon="🌍", layout="wide")
st.title("🌍 EinTrust GHG Dashboard & Data Entry")

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
    "Diesel Generator": "Liters",
    "Petrol Generator": "Liters",
    "LPG Boiler": "Liters",
    "Coal Boiler": "kg",
    "Biomass Furnace": "kg",
    "Diesel Vehicle": "Liters",
    "Petrol Car": "Liters",
    "CNG Vehicle": "m³",
    "Diesel Forklift": "Liters",
    "Petrol Two-Wheeler": "Liters",
    "Cement Production": "Tonnes",
    "Steel Production": "Tonnes",
    "Brick Kiln": "Tonnes",
    "Textile Processing": "Tonnes",
    "Chemical Manufacturing": "Tonnes",
    "Food Processing": "Tonnes",
    "Refrigerant (HFC/HCFC)": "kg",
    "Methane (CH₄)": "kg",
    "SF₆": "kg",
    "Grid Electricity": "kWh",
    "Diesel Generator Electricity": "kWh",
    "Purchased Steam": "Tonnes",
    "Purchased Cooling": "kWh"
}

SCOPE_COLORS = {"Scope 1": "#81c784", "Scope 2": "#4db6ac", "Scope 3": "#aed581"}

# -----------------------------
# Initialize Session State
# -----------------------------
if 'entries' not in st.session_state:
    st.session_state.entries = pd.DataFrame(columns=["Scope","Activity","Sub-Activity","Specific Item","Quantity","Unit"])

# -----------------------------
# Sidebar Navigation
# -----------------------------
with st.sidebar:
    st.image("https://github.com/eintrusts/eintrust_ghg_app/raw/main/EinTrust%20%20logo.png", use_container_width=True)
    st.markdown("---")
    if st.button("Home"):
        st.session_state.page = "Home"

    env_exp = st.expander("Environment", expanded=True)
    with env_exp:
        if st.button("GHG"):
            st.session_state.page = "GHG"
        if st.button("Energy"):
            st.session_state.page = "Energy"
        if st.button("Water"):
            st.session_state.page = "Water"
        if st.button("Waste"):
            st.session_state.page = "Waste"
        if st.button("Biodiversity"):
            st.session_state.page = "Biodiversity"

    social_exp = st.expander("Social")
    with social_exp:
        if st.button("Employee"):
            st.session_state.page = "Employee"
        if st.button("Health & Safety"):
            st.session_state.page = "Health & Safety"
        if st.button("CSR"):
            st.session_state.page = "CSR"

    gov_exp = st.expander("Governance")
    with gov_exp:
        if st.button("Board"):
            st.session_state.page = "Board"
        if st.button("Policies"):
            st.session_state.page = "Policies"
        if st.button("Compliance"):
            st.session_state.page = "Compliance"
        if st.button("Risk Management"):
            st.session_state.page = "Risk Management"

# -----------------------------
# Utilities
# -----------------------------
def format_indian(n: float) -> str:
    try:
        x = int(round(float(n)))
    except Exception:
        return "0"
    s = str(abs(x))
    if len(s) <= 3:
        res = s
    else:
        res = s[-3:]
        s = s[:-3]
        while len(s) > 2:
            res = s[-2:] + "," + res
            s = s[:-2]
        if s:
            res = s + "," + res
    return ("-" if x < 0 else "") + res

def render_emission_trends():
    if st.session_state.entries.empty:
        st.info("No emissions data yet.")
        return

    df = st.session_state.entries.copy()
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0)
    trend_df = df.groupby("Scope")["Quantity"].sum().reset_index()

    # Stacked bar chart
    fig = px.bar(trend_df, x="Scope", y="Quantity", color="Scope", color_discrete_map=SCOPE_COLORS,
                 text="Quantity", template="plotly_dark")
    fig.update_layout(paper_bgcolor="#0d1117", font_color="#e6edf3", showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# Page Rendering
# -----------------------------
if 'page' not in st.session_state:
    st.session_state.page = "Home"

if st.session_state.page in ["Home", "GHG"]:
    st.subheader("🌱 GHG Emissions Dashboard")
    render_emission_trends()

    if st.session_state.page == "GHG":
        # -----------------------------
        # Scope Selection
        # -----------------------------
        scope = st.selectbox("Select Scope", ["Scope 1", "Scope 2", "Scope 3"])

        # -----------------------------
        # Activity Selection
        # -----------------------------
        activity = st.selectbox("Select Activity / Category", list(scope_activities[scope].keys()))

        # -----------------------------
        # Sub-Activity Selection
        # -----------------------------
        sub_options = scope_activities[scope][activity]
        if scope != "Scope 3":
            sub_activity = st.selectbox("Select Sub-Activity", list(sub_options.keys()))
            st.info(sub_options[sub_activity])
        else:
            sub_activity = st.selectbox("Select Sub-Category", list(sub_options.keys()))

        # -----------------------------
        # Specific Item for Scope 3
        # -----------------------------
        specific_item = None
        if scope == "Scope 3":
            items = scope_activities[scope][activity][sub_activity]
            if items is not None:
                specific_item = st.selectbox("Select Specific Item", items)

        # -----------------------------
        # Quantity Input
        # -----------------------------
        unit = None
        if scope != "Scope 3":
            unit = units_dict.get(sub_activity, "")
        else:
            if sub_activity in ["Air Travel"]:
                unit = "Number of flights"
            elif sub_activity in ["Train Travel","Taxi / Cab / Auto","Two-Wheelers","Cars / Vans","Public Transport",
                                  "Incoming Goods Transport","Third-party Logistics","Delivery to Customers","Retail / Distributor Transport"]:
                unit = "km traveled"
            else:
                unit = "kg / Tonnes"

        quantity = st.number_input(f"Enter Quantity ({unit})", min_value=0.0, format="%.2f")

        # -----------------------------
        # Upload Bill / File (CSV/XLS/XLSX/PDF)
        # -----------------------------
        uploaded_file = st.file_uploader("Upload Bill or File (CSV/XLS/XLSX/PDF)", type=["csv","xls","xlsx","pdf"])

        # -----------------------------
        # Add Manual Entry
        # -----------------------------
        if st.button("Add Manual Entry"):
            new_entry = {
                "Scope": scope,
                "Activity": activity,
                "Sub-Activity": sub_activity,
                "Specific Item": specific_item if specific_item else "",
                "Quantity": quantity,
                "Unit": unit
            }
            st.session_state.entries = pd.concat([st.session_state.entries, pd.DataFrame([new_entry])], ignore_index=True)
            st.success("Entry added successfully!")

            # Optional: save uploaded file with entry
            if uploaded_file:
                st.info(f"Uploaded file: {uploaded_file.name}")

        # -----------------------------
        # Display Entries Table
        # -----------------------------
        if not st.session_state.entries.empty:
            st.subheader("All Entries")
            display_df = st.session_state.entries.copy()
            display_df["Quantity"] = display_df["Quantity"].apply(lambda x: f"{x:,.2f}")
            st.dataframe(display_df)

            # -----------------------------
            # Download CSV
            # -----------------------------
            csv = display_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download All Entries as CSV", csv, "ghg_entries.csv", "text/csv")

# -----------------------------
# Placeholder Pages for Social & Governance
# -----------------------------
elif st.session_state.page in ["Employee","Health & Safety","CSR","Board","Policies","Compliance","Risk Management"]:
    st.subheader(f"{st.session_state.page} Dashboard")
    st.info("Dashboard will be implemented here in future. No data yet.")
