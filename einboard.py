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
.kpi-value { font-size: 20px; color: #81c784; font-weight:700; }
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
# Sidebar
# ---------------------------
def set_page(p):
    st.session_state.page = p

with st.sidebar:
    st.image("https://github.com/eintrusts/eintrust_ghg_app/raw/main/EinTrust%20%20logo.png", use_container_width=True)
    st.markdown("---")

    if st.button("Home"): set_page("Home")

    # Environment dropdown
    env_exp = st.expander("Environment", expanded=True)
    with env_exp:
        if st.button("GHG"): set_page("GHG")
        if st.button("Energy"): set_page("Energy")
        if st.button("Water"): set_page("Water")
        if st.button("Waste"): set_page("Waste")
        if st.button("Biodiversity"): set_page("Biodiversity")

    # Social dropdown
    social_exp = st.expander("Social", expanded=False)
    with social_exp:
        if st.button("Employee"): set_page("Employee")
        if st.button("Health & Safety"): set_page("Health & Safety")
        if st.button("CSR"): set_page("CSR")

    # Governance dropdown
    gov_exp = st.expander("Governance", expanded=False)
    with gov_exp:
        if st.button("Board"): set_page("Board")
        if st.button("Policies"): set_page("Policies")
        if st.button("Compliance"): set_page("Compliance")
        if st.button("Risk Management"): set_page("Risk Management")

# ---------------------------
# Main Content
# ---------------------------
st.title("🌍 EinTrust Dashboard")

def render_ghg_dashboard(include_data=True, show_activity=True):
    st.subheader("🌱 GHG Emissions Dashboard")
    st.markdown("Estimate Scope 1, 2, and 3 emissions for net zero journey.")

    # KPIs
    s1 = st.session_state.emissions_summary.get("Scope 1", 0.0)
    s2 = st.session_state.emissions_summary.get("Scope 2", 0.0)
    s3 = st.session_state.emissions_summary.get("Scope 3", 0.0)
    total = s1 + s2 + s3

    SCOPE_COLORS = {"Scope 1": "#81c784", "Scope 2": "#4db6ac", "Scope 3": "#aed581"}

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='kpi'><div class='kpi-value' style='color:white'>{format_indian(total)}</div><div class='kpi-label'>Total Emissions (tCO₂e)</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{SCOPE_COLORS['Scope 1']}'>{format_indian(s1)}</div><div class='kpi-label'>Scope 1 (tCO₂e)</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{SCOPE_COLORS['Scope 2']}'>{format_indian(s2)}</div><div class='kpi-label'>Scope 2 (tCO₂e)</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{SCOPE_COLORS['Scope 3']}'>{format_indian(s3)}</div><div class='kpi-label'>Scope 3 (tCO₂e)</div></div>", unsafe_allow_html=True)

    # Pie Chart
    st.subheader("📊 Emission Breakdown by Scope")
    df_log = pd.DataFrame(st.session_state.emissions_log)
    if not df_log.empty:
        pie_df = df_log.groupby("Scope", sort=False)["Emissions (tCO₂e)"].sum().reindex(["Scope 1", "Scope 2", "Scope 3"]).fillna(0).reset_index()
        fig_pie = px.pie(pie_df, names="Scope", values="Emissions (tCO₂e)", hole=0.45,
                         color="Scope", color_discrete_map=SCOPE_COLORS, template="plotly_dark")
        fig_pie.update_layout(paper_bgcolor="#0d1117", font_color="#e6edf3")
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No data to show in breakdown.")

    # Monthly Trend
    st.subheader("📈 Emissions Trend Over Time (Monthly)")
    if not df_log.empty:
        df_log["Timestamp"] = pd.to_datetime(df_log["Timestamp"], errors="coerce")
        df_log = df_log.dropna(subset=["Timestamp"])
        cycle_start, cycle_end = get_cycle_bounds(date.today())
        df_cycle = df_log[(df_log["Timestamp"].dt.date >= cycle_start) & (df_log["Timestamp"].dt.date <= cycle_end)].copy()
        if not df_cycle.empty:
            df_cycle["MonthLabel"] = pd.Categorical(df_cycle["Timestamp"].dt.strftime("%b"), categories=MONTH_ORDER, ordered=True)
            stacked = df_cycle.groupby(["MonthLabel", "Scope"])["Emissions (tCO₂e)"].sum().reset_index()
            pivot = stacked.pivot(index="MonthLabel", columns="Scope", values="Emissions (tCO₂e)").reindex(MONTH_ORDER).fillna(0)
            pivot = pivot.reset_index()
            melt = pivot.melt(id_vars=["MonthLabel"], var_name="Scope", value_name="Emissions (tCO₂e)")

            fig_bar = px.bar(melt, x="MonthLabel", y="Emissions (tCO₂e)", color="Scope",
                             color_discrete_map=SCOPE_COLORS, barmode="stack", template="plotly_dark")
            fig_bar.update_layout(paper_bgcolor="#0d1117", font_color="#e6edf3", xaxis_title="", yaxis_title="Emissions (tCO₂e)")
            st.plotly_chart(fig_bar, use_container_width=True)

    if show_activity and include_data:
        # Add Activity Data and Log
        st.subheader("➕ Add Activity Data")
        # ... (same Add Activity Data code as before)
        st.subheader("📜 Emissions Log")
        if st.session_state.emissions_log:
            log_df = pd.DataFrame(st.session_state.emissions_log).sort_values("Timestamp", ascending=False).reset_index(drop=True)
            st.dataframe(log_df, use_container_width=True)
            st.download_button("📥 Download Current Log (CSV)", data=log_df.to_csv(index=False), file_name="emissions_log_current.csv", mime="text/csv")
        else:
            st.info("No emission log data yet. Add entries above.")

# ---------------------------
# Render pages
# ---------------------------
if st.session_state.page == "Home":
    render_ghg_dashboard(include_data=False, show_activity=False)  # Home: KPI + Pie + Trend
elif st.session_state.page == "GHG":
    render_ghg_dashboard(include_data=True, show_activity=True)    # GHG: full dashboard
else:
    st.subheader(f"{st.session_state.page} Section")
    st.info("This section is under development. Please select other pages from sidebar.")
