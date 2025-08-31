import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import numpy as np

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
# Session State
# ---------------------------
if "emissions_log" not in st.session_state:
    st.session_state.emissions_log = []
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

    # Environment dropdown
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

    # Social dropdown
    social_exp = st.expander("Social", expanded=False)
    with social_exp:
        if st.button("Employee"):
            st.session_state.page = "Employee"
        if st.button("Health & Safety"):
            st.session_state.page = "Health & Safety"
        if st.button("CSR"):
            st.session_state.page = "CSR"

    # Governance dropdown
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

SCOPE_COLORS = {"Scope 1": "#81c784", "Scope 2": "#4db6ac", "Scope 3": "#aed581"}

def render_home_dashboard():
    s1 = st.session_state.emissions_summary.get("Scope 1", 0.0)
    s2 = st.session_state.emissions_summary.get("Scope 2", 0.0)
    s3 = st.session_state.emissions_summary.get("Scope 3", 0.0)
    total = s1 + s2 + s3

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='kpi'><div class='kpi-value' style='color:white'>{format_indian(total)}</div><div class='kpi-label'>Total Emissions (tCO₂e)</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{SCOPE_COLORS['Scope 1']}'>{format_indian(s1)}</div><div class='kpi-label'>Scope 1 (tCO₂e)</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{SCOPE_COLORS['Scope 2']}'>{format_indian(s2)}</div><div class='kpi-label'>Scope 2 (tCO₂e)</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{SCOPE_COLORS['Scope 3']}'>{format_indian(s3)}</div><div class='kpi-label'>Scope 3 (tCO₂e)</div></div>", unsafe_allow_html=True)

def render_ghg_dashboard():
    # KPIs same as home
    s1 = st.session_state.emissions_summary.get("Scope 1", 0.0)
    s2 = st.session_state.emissions_summary.get("Scope 2", 0.0)
    s3 = st.session_state.emissions_summary.get("Scope 3", 0.0)
    total = s1 + s2 + s3

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='kpi'><div class='kpi-value' style='color:white'>{format_indian(total)}</div><div class='kpi-label'>Total Emissions (tCO₂e)</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{SCOPE_COLORS['Scope 1']}'>{format_indian(s1)}</div><div class='kpi-label'>Scope 1 (tCO₂e)</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{SCOPE_COLORS['Scope 2']}'>{format_indian(s2)}</div><div class='kpi-label'>Scope 2 (tCO₂e)</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{SCOPE_COLORS['Scope 3']}'>{format_indian(s3)}</div><div class='kpi-label'>Scope 3 (tCO₂e)</div></div>", unsafe_allow_html=True)

    st.subheader("📊 Emission Breakdown & Trend (Monthly)")
    df_log = pd.DataFrame(st.session_state.emissions_log)
    if not df_log.empty:
        # Pie
        pie_df = df_log.groupby("Scope", sort=False)["Quantity"].sum().reindex(["Scope 1","Scope 2","Scope 3"]).fillna(0).reset_index()
        fig_pie = px.pie(pie_df, names="Scope", values="Quantity", color="Scope", color_discrete_map=SCOPE_COLORS, hole=0.45, template="plotly_dark")
        # Monthly trend
        df_log["Timestamp"] = pd.to_datetime(df_log.get("Timestamp", pd.Series([datetime.now()] * len(df_log))))
        df_log["MonthLabel"] = pd.Categorical(df_log["Timestamp"].dt.strftime("%b"), categories=MONTH_ORDER, ordered=True)
        trend_df = df_log.groupby(["MonthLabel","Scope"])["Quantity"].sum().reset_index()
        fig_bar = px.bar(trend_df, x="MonthLabel", y="Quantity", color="Scope", barmode="stack", color_discrete_map=SCOPE_COLORS, template="plotly_dark")
        st.plotly_chart(fig_pie, use_container_width=True)
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No data yet for breakdown & trend charts.")

    st.subheader("➕ Add Activity Data (Indian SME GHG)")
    
    # -----------------------------
    # Upload File Option
    # -----------------------------
    uploaded_file = st.file_uploader("Upload Bill / File (CSV/XLS/XLSX)", type=["csv","xls","xlsx"])
    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".csv"):
                df_file = pd.read_csv(uploaded_file)
            else:
                df_file = pd.read_excel(uploaded_file)
            st.session_state.emissions_log.extend(df_file.to_dict("records"))
            st.success("File uploaded successfully!")
        except Exception as e:
            st.error(f"Error reading file: {e}")

    # -----------------------------
    # Manual GHG Entry Form
    # -----------------------------
    scope_activities = {
        "Scope 1": {"Stationary Combustion": {"Diesel Generator":"Generator running on diesel","Petrol Generator":"Generator running on petrol"},"Mobile Combustion":{"Diesel Vehicle":"Truck/van"}} ,
        "Scope 2": {"Electricity Consumption":{"Grid Electricity":"From grid"}},
        "Scope 3": {"Purchased Goods & Services":{"Raw Materials":["Cement","Steel"]}}
    }
    units_dict = {"Diesel Generator":"Liters","Petrol Generator":"Liters","Diesel Vehicle":"Liters","Grid Electricity":"kWh","Cement":"Tonnes","Steel":"Tonnes"}

    if 'entries' not in st.session_state:
        st.session_state.entries = pd.DataFrame(columns=["Scope","Activity","Sub-Activity","Specific Item","Quantity","Unit","Timestamp"])
    
    scope_sel = st.selectbox("Select Scope", list(scope_activities.keys()))
    activity_sel = st.selectbox("Select Activity / Category", list(scope_activities[scope_sel].keys()))
    sub_options = scope_activities[scope_sel][activity_sel]
    if isinstance(sub_options, dict):
        sub_activity_sel = st.selectbox("Select Sub-Activity", list(sub_options.keys()))
        specific_item_sel = None
    else:
        sub_activity_sel = st.selectbox("Select Sub-Category", list(sub_options.keys()))
        specific_item_sel = st.selectbox("Select Specific Item", sub_options[sub_activity_sel])
    
    unit = units_dict.get(sub_activity_sel if specific_item_sel is None else specific_item_sel, "")
    quantity = st.number_input(f"Enter Quantity ({unit})", min_value=0.0, format="%.2f")
    
    if st.button("Add Entry"):
        new_entry = {"Scope":scope_sel,"Activity":activity_sel,"Sub-Activity":sub_activity_sel,"Specific Item":specific_item_sel if specific_item_sel else "",
                     "Quantity":quantity,"Unit":unit,"Timestamp":datetime.now()}
        st.session_state.entries = pd.concat([st.session_state.entries,pd.DataFrame([new_entry])], ignore_index=True)
        st.session_state.emissions_log.append(new_entry)
        st.success("Entry added!")

    # Show entries table
    if not st.session_state.entries.empty:
        st.subheader("All Entries")
        display_df = st.session_state.entries.copy()
        display_df["Quantity"] = display_df["Quantity"].apply(lambda x: f"{x:,.2f}")
        st.dataframe(display_df)
        csv = display_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download All Entries as CSV", csv, "ghg_entries.csv", "text/csv")

# ---------------------------
# Render pages
# ---------------------------
if st.session_state.page == "Home":
    render_home_dashboard()
elif st.session_state.page == "GHG":
    render_ghg_dashboard()
else:
    st.subheader(f"{st.session_state.page} Section")
    st.info("This section is under development. You can expand functionality in the future.")
