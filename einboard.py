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
MONTH_ORDER = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]

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

def get_cycle_bounds(today: date):
    if today.month < 4:
        start = date(today.year - 1, 4, 1)
        end = date(today.year, 3, 31)
    else:
        start = date(today.year, 4, 1)
        end = date(today.year + 1, 3, 31)
    return start, end

# ---------------------------
# Load emission factors
# ---------------------------
try:
    emission_factors = pd.read_csv("emission_factors.csv")
except FileNotFoundError:
    emission_factors = pd.DataFrame(columns=["scope","category","activity","unit","emission_factor"])
    st.sidebar.warning("emission_factors.csv not found — add it to use prefilled activities.")

# ---------------------------
# Session state
# ---------------------------
if "emissions_log" not in st.session_state:
    st.session_state.emissions_log = []
if "emissions_summary" not in st.session_state:
    st.session_state.emissions_summary = {"Scope 1": 0.0, "Scope 2": 0.0, "Scope 3": 0.0}
if "page" not in st.session_state:
    st.session_state.page = "Home"

# ---------------------------
# Sidebar - fixed using selectbox
# ---------------------------
with st.sidebar:
    st.image("https://github.com/eintrusts/eintrust_ghg_app/raw/main/EinTrust%20%20logo.png", use_container_width=True)
    st.markdown("---")
    
    page_options = ["Home", "GHG", "Energy", "Water", "Waste", "Biodiversity",
                    "Employee", "Health & Safety", "CSR",
                    "Board", "Policies", "Compliance", "Risk Management"]
    
    selected_page = st.selectbox("Select Page", page_options, index=page_options.index(st.session_state.page))
    st.session_state.page = selected_page

# ---------------------------
# Main Content
# ---------------------------
st.title("🌍 EinTrust Dashboard")

# ---------------------------
# GHG Dashboard rendering
# ---------------------------
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

    # ---------------------------
    # Manual Entry for GHG Page
    # ---------------------------
    if include_data:
        import numpy as np

        st.subheader("➕ Add Activity Data")
        # Scope selection
        scope_options = emission_factors["scope"].dropna().unique() if not emission_factors.empty else ["Scope 1","Scope 2","Scope 3"]
        selected_scope = st.selectbox("Select Scope", scope_options)

        # Category / Activity selection
        filtered_df = emission_factors[emission_factors["scope"]==selected_scope] if not emission_factors.empty else pd.DataFrame()
        if selected_scope == "Scope 3":
            category_options = filtered_df["category"].dropna().unique() if not filtered_df.empty else ["Purchased Goods & Services","Business Travel","Employee Commuting","Waste Generated"]
            selected_category = st.selectbox("Select Scope 3 Category", category_options)
        else:
            selected_category = "-"

        # Activity selection
        activity_options = filtered_df["activity"].dropna().unique() if not filtered_df.empty else ["Activity A","Activity B"]
        selected_activity = st.selectbox("Select Activity", activity_options)

        # Emission factor
        if not filtered_df.empty:
            activity_df = filtered_df[filtered_df["activity"]==selected_activity]
            if not activity_df.empty:
                unit = str(activity_df["unit"].values[0])
                ef = float(activity_df["emission_factor"].values[0])
            else:
                unit = "-"
                ef = 0.0
        else:
            unit = "-"
            ef = 0.0

        quantity = st.number_input(f"Enter quantity ({unit})", min_value=0.0, format="%.4f")

        # ---------------------------
        # File upload for cross-verification only
        # ---------------------------
        st.subheader("Optional: Upload CSV / Excel / PDF for cross-verification")
        uploaded_file = st.file_uploader("Upload CSV/XLS/XLSX/PDF", type=["csv","xls","xlsx","pdf"])
        if uploaded_file:
            st.info("File uploaded for cross-verification. Data from file will NOT affect the dashboard KPIs.")

        # ---------------------------
        # Add Entry
        # ---------------------------
        if st.button("Add Manual Entry") and quantity > 0 and ef > 0:
            emissions = quantity * ef
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
            summary = {"Scope 1":0.0,"Scope 2":0.0,"Scope 3":0.0}
            for e in st.session_state.emissions_log:
                summary[e["Scope"]] += e["Emissions (tCO₂e)"]
            st.session_state.emissions_summary = summary
            st.success("Entry added successfully!")

        # ---------------------------
        # Display Emissions Log
        # ---------------------------
        st.subheader("📜 Emissions Log")
        if st.session_state.emissions_log:
            log_df = pd.DataFrame(st.session_state.emissions_log).sort_values("Timestamp", ascending=False).reset_index(drop=True)
            st.dataframe(log_df, use_container_width=True)
            st.download_button("📥 Download Current Log (CSV)", data=log_df.to_csv(index=False), file_name="emissions_log_current.csv", mime="text/csv")
        else:
            st.info("No emission log data yet. Add entries above.")

# ---------------------------
# Render Pages
# ---------------------------
if st.session_state.page == "Home":
    render_ghg_dashboard(include_data=False)   # Only KPIs, no Add Activity
elif st.session_state.page == "GHG":
    render_ghg_dashboard(include_data=True)    # Full GHG page
else:
    st.subheader(f"{st.session_state.page} Section")
    st.info("This section is under development. Please select other pages from sidebar.")
