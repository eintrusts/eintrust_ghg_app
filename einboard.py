import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date

# ---------------------------
# Config & Dark Theme CSS
# ---------------------------
st.set_page_config(page_title="EinTrust Dashboard", page_icon="🌍", layout="wide")

st.markdown("""
<style>
  .stApp { background-color: #0d1117; color: #e6edf3; }
  .kpi { background: #12131a; padding: 14px; border-radius: 10px; }
  .kpi-value { font-size: 20px; font-weight:700; }
  .kpi-label { font-size: 12px; color: #cfd8dc; }
  .stDataFrame { color: #e6edf3; }
  .sidebar .stButton>button { background:#198754; color:white; margin-bottom:5px; width:100%; }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Utilities
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

# ---------------------------
# Session state
# ---------------------------
if "emissions_summary" not in st.session_state:
    st.session_state.emissions_summary = {"Scope 1": 0.0, "Scope 2": 0.0, "Scope 3": 0.0}
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
        if st.button("Water"):
            st.session_state.page = "Water"
        if st.button("Waste"):
            st.session_state.page = "Waste"
        if st.button("Biodiversity"):
            st.session_state.page = "Biodiversity"
    
    social_exp = st.expander("Social", expanded=False)
    with social_exp:
        if st.button("Employee"):
            st.session_state.page = "Employee"
        if st.button("Health & Safety"):
            st.session_state.page = "Health & Safety"
        if st.button("CSR"):
            st.session_state.page = "CSR"
    
    gov_exp = st.expander("Governance", expanded=False)
    with gov_exp:
        if st.button("Board"):
            st.session_state.page = "Board"
        if st.button("Policies"):
            st.session_state.page = "Policies"
        if st.button("Compliance"):
            st.session_state.page = "Compliance"
        if st.button("Risk Management"):
            st.session_state.page = "Risk Management"

# ---------------------------
# Main Content
# ---------------------------
st.title("🌍 EinTrust Dashboard")

def render_ghg_dashboard(include_data=True):
    st.subheader("🌱 GHG Emissions Dashboard")
    st.markdown("Estimate Scope 1, 2, and 3 emissions for net zero journey.")

    # KPIs
    s1 = st.session_state.emissions_summary.get("Scope 1", 0.0)
    s2 = st.session_state.emissions_summary.get("Scope 2", 0.0)
    s3 = st.session_state.emissions_summary.get("Scope 3", 0.0)
    total = s1 + s2 + s3

    SCOPE_COLORS = {"Scope 1": "#81c784", "Scope 2": "#4db6ac", "Scope 3": "#aed581"}

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"<div class='kpi'><div class='kpi-value' style='color:white'>{format_indian(total)}</div><div class='kpi-label'>Total Emissions (tCO₂e)</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{SCOPE_COLORS['Scope 1']}'>{format_indian(s1)}</div><div class='kpi-label'>Scope 1 (tCO₂e)</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{SCOPE_COLORS['Scope 2']}'>{format_indian(s2)}</div><div class='kpi-label'>Scope 2 (tCO₂e)</div></div>", unsafe_allow_html=True)
    with c4:
        st.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{SCOPE_COLORS['Scope 3']}'>{format_indian(s3)}</div><div class='kpi-label'>Scope 3 (tCO₂e)</div></div>", unsafe_allow_html=True)

    if include_data:
        st.subheader("➕ Add Activity Data (Indian SME GHG)")

        # Initialize Session State
        if 'entries' not in st.session_state:
            st.session_state.entries = pd.DataFrame(columns=["Scope","Activity","Sub-Activity","Specific Item","Quantity","Unit"])

        # Dummy dictionaries for activities
        scope_activities = {
            "Scope 1": {"Stationary Combustion": {"Diesel Generator": "DG"}},
            "Scope 2": {"Electricity Consumption": {"Grid Electricity": "Grid"}},
            "Scope 3": {"Business Travel": {"Air Travel": None}}
        }
        units_dict = {"Diesel Generator":"Liters","Grid Electricity":"kWh","Air Travel":"Number of flights"}

        # Selections
        scope_sel = st.selectbox("Select Scope", ["Scope 1","Scope 2","Scope 3"])
        activity_sel = st.selectbox("Select Activity / Category", list(scope_activities[scope_sel].keys()))
        sub_activity_sel = st.selectbox("Select Sub-Activity / Sub-Category", list(scope_activities[scope_sel][activity_sel].keys()))
        specific_item_sel = None
        if scope_sel == "Scope 3":
            items = scope_activities[scope_sel][activity_sel][sub_activity_sel]
            if items is not None:
                specific_item_sel = st.selectbox("Select Specific Item", items)
        unit_sel = units_dict.get(sub_activity_sel, "Unit")
        quantity_sel = st.number_input(f"Enter Quantity ({unit_sel})", min_value=0.0, format="%.2f")

        # -----------------------------
        # File Upload for Cross Verification
        # -----------------------------
        st.subheader("Optional: Upload File for Cross Verification")
        uploaded_file = st.file_uploader("Upload CSV/XLS/XLSX (Internal Only)", type=["csv","xls","xlsx"])
        if uploaded_file:
            try:
                if uploaded_file.name.endswith(".csv"):
                    df_file = pd.read_csv(uploaded_file)
                else:
                    df_file = pd.read_excel(uploaded_file)
                st.info("File uploaded for internal verification. Results will not be affected.")
            except Exception as e:
                st.error(f"Error reading file: {e}")

        # Add Manual Entry
        if st.button("Add Manual Entry"):
            new_entry = {
                "Scope": scope_sel,
                "Activity": activity_sel,
                "Sub-Activity": sub_activity_sel,
                "Specific Item": specific_item_sel if specific_item_sel else "",
                "Quantity": quantity_sel,
                "Unit": unit_sel
            }
            st.session_state.entries = pd.concat([st.session_state.entries, pd.DataFrame([new_entry])], ignore_index=True)
            st.success("Entry added successfully!")

        # Display Entries Table
        if not st.session_state.entries.empty:
            st.subheader("All Manual Entries")
            display_df = st.session_state.entries.copy()
            display_df["Quantity"] = display_df["Quantity"].apply(lambda x: f"{x:,.2f}")
            st.dataframe(display_df)

            # Download
            csv = display_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download All Entries as CSV", csv, "ghg_entries.csv", "text/csv")

# ---------------------------
# Render pages
# ---------------------------
if st.session_state.page == "Home":
    render_ghg_dashboard(include_data=False)
elif st.session_state.page == "GHG":
    render_ghg_dashboard(include_data=True)
else:
    st.subheader(f"{st.session_state.page} Section")
    st.info("This section is under development. Please select other pages from sidebar.")
