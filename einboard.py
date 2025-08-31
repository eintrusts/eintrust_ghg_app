import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, date

# ---------------------------
# Config & Dark Theme CSS
# ---------------------------
st.set_page_config(page_title="EinTrust Dashboard", page_icon="🌍", layout="wide")

st.markdown("""
<style>
.stApp { background-color: #0d1117; color: #e6edf3; }
.kpi { background: #12131a; padding: 14px; border-radius: 10px; }
.kpi-value { font-size: 20px; color: #81c784; font-weight:700; }
.kpi-label { font-size: 12px; color: #cfd8dc; }
.stDataFrame { color: #e6edf3; }
.sidebar .stButton>button { background:#198754; color:white; margin-bottom:5px; width:100%; }
</style>
""", unsafe_allow_html=True)

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
        }
    },
    "Scope 2": {
        "Electricity Consumption": {"Grid Electricity": "Electricity bought from grid",
                                    "Diesel Generator Electricity": "Electricity generated on-site with diesel"},
        "Steam / Heat": {"Purchased Steam": "Steam bought from external supplier"}
    },
    "Scope 3": {
        "Purchased Goods & Services": {
            "Raw Materials": ["Cement", "Steel", "Chemicals", "Textile"],
            "Packaging Materials": ["Cardboard", "Plastics", "Glass"]
        },
        "Business Travel": {"Air Travel": None, "Train Travel": None},
        "Employee Commuting": {"Two-Wheelers": None, "Cars / Vans": None}
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
    "Grid Electricity": "kWh",
    "Diesel Generator Electricity": "kWh",
    "Purchased Steam": "Tonnes"
}

SCOPE_COLORS = {"Scope 1": "#81c784", "Scope 2": "#4db6ac", "Scope 3": "#aed581"}

# ---------------------------
# Initialize Session State
# ---------------------------
if 'entries' not in st.session_state:
    st.session_state.entries = pd.DataFrame(columns=["Scope","Activity","Sub-Activity","Specific Item","Quantity","Unit","Date"])
if "page" not in st.session_state:
    st.session_state.page = "Home"

# ---------------------------
# Sidebar
# ---------------------------
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

    social_exp = st.expander("Social", expanded=False)
    with social_exp:
        if st.button("Employee"):
            st.session_state.page = "Employee"
        if st.button("Health & Safety"):
            st.session_state.page = "Health & Safety"

    gov_exp = st.expander("Governance", expanded=False)
    with gov_exp:
        if st.button("Board"):
            st.session_state.page = "Board"
        if st.button("Policies"):
            st.session_state.page = "Policies"

# ---------------------------
# Functions
# ---------------------------
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

def render_dashboard(df_entries):
    st.subheader("🌱 GHG Emissions Dashboard")
    if df_entries.empty:
        st.info("No manual entries yet.")
        return

    # Total KPIs
    s1 = df_entries[df_entries["Scope"]=="Scope 1"]["Quantity"].sum()
    s2 = df_entries[df_entries["Scope"]=="Scope 2"]["Quantity"].sum()
    s3 = df_entries[df_entries["Scope"]=="Scope 3"]["Quantity"].sum()
    total = s1 + s2 + s3

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='kpi'><div class='kpi-value' style='color:white'>{format_indian(total)}</div><div class='kpi-label'>Total Emissions</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{SCOPE_COLORS['Scope 1']}'>{format_indian(s1)}</div><div class='kpi-label'>Scope 1</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{SCOPE_COLORS['Scope 2']}'>{format_indian(s2)}</div><div class='kpi-label'>Scope 2</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{SCOPE_COLORS['Scope 3']}'>{format_indian(s3)}</div><div class='kpi-label'>Scope 3</div></div>", unsafe_allow_html=True)

    # Monthly Trend
    df_entries["Month"] = pd.to_datetime(df_entries["Date"]).dt.to_period("M").astype(str)
    trend_df = df_entries.groupby(["Month","Scope"])["Quantity"].sum().reset_index()
    fig = px.bar(trend_df, x="Month", y="Quantity", color="Scope", color_discrete_map=SCOPE_COLORS,
                 text="Quantity", template="plotly_dark")
    fig.update_layout(paper_bgcolor="#0d1117", font_color="#e6edf3", barmode="stack", yaxis_title="Emissions")
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# Main Content
# ---------------------------
st.title("🌍 Indian SME GHG Data Entry")

if st.session_state.page in ["Home", "GHG"]:
    if st.session_state.page == "GHG":
        # -----------------------------
        # Scope Selection
        # -----------------------------
        scope = st.selectbox("Select Scope", ["Scope 1", "Scope 2", "Scope 3"])
        activity = st.selectbox("Select Activity / Category", list(scope_activities[scope].keys()))
        sub_options = scope_activities[scope][activity]
        if scope != "Scope 3":
            sub_activity = st.selectbox("Select Sub-Activity", list(sub_options.keys()))
            st.info(sub_options[sub_activity])
        else:
            sub_activity = st.selectbox("Select Sub-Category", list(sub_options.keys()))
        specific_item = None
        if scope == "Scope 3":
            items = scope_activities[scope][activity][sub_activity]
            if items is not None:
                specific_item = st.selectbox("Select Specific Item", items)

        # Quantity and Date
        unit = units_dict.get(sub_activity, "kg") if scope!="Scope 3" else "kg / Tonnes / km"
        quantity = st.number_input(f"Enter Quantity ({unit})", min_value=0.0, format="%.2f")
        entry_date = st.date_input("Select Entry Date", value=date.today())

        # File Upload / Bill
        uploaded_file = st.file_uploader("Upload Bill / File (CSV/XLS/XLSX/PDF)", type=["csv","xls","xlsx","pdf"])

        # Add Entry Button
        if st.button("Add Manual Entry") and quantity>0:
            new_entry = {
                "Scope": scope,
                "Activity": activity,
                "Sub-Activity": sub_activity,
                "Specific Item": specific_item if specific_item else "",
                "Quantity": quantity,
                "Unit": unit,
                "Date": entry_date
            }
            st.session_state.entries = pd.concat([st.session_state.entries, pd.DataFrame([new_entry])], ignore_index=True)
            st.success("Entry added successfully!")

    render_dashboard(st.session_state.entries)

else:
    st.subheader(f"{st.session_state.page} Section")
    st.info("This section is under development. Please select other pages from sidebar.")
