import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import io

# ---------------------------
# Page Config & Dark Theme
# ---------------------------
st.set_page_config(page_title="EinTrust GHG Dashboard", page_icon="🌍", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #e6edf3; }
    .kpi { background: #12131a; padding: 14px; border-radius: 10px; margin-bottom:10px; }
    .kpi-value { font-size: 20px; color: #81c784; font-weight:700; }
    .kpi-label { font-size: 12px; color: #cfd8dc; }
    .stDataFrame { color: #e6edf3; }
    .sidebar .stButton>button { background:#198754; color:white }
    </style>
""", unsafe_allow_html=True)

# ---------------------------
# Sidebar Logo
# ---------------------------
st.sidebar.image("https://raw.githubusercontent.com/eintrusts/eintrust/main/profile_photo.png", width=150)

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

def get_cycle_bounds(today: date):
    if today.month < 4:
        start = date(today.year - 1, 4, 1)
        end = date(today.year, 3, 31)
    else:
        start = date(today.year, 4, 1)
        end = date(today.year + 1, 3, 31)
    return start, end

# ---------------------------
# Load Emission Factors
# ---------------------------
try:
    emission_factors = pd.read_csv("emission_factors.csv")
except FileNotFoundError:
    emission_factors = pd.DataFrame(columns=["scope","category","activity","unit","emission_factor"])
    st.sidebar.warning("emission_factors.csv not found — add it to use prefilled activities.")

# ---------------------------
# Session State
# ---------------------------
if "emissions_log" not in st.session_state:
    st.session_state.emissions_log = []
if "emissions_summary" not in st.session_state:
    st.session_state.emissions_summary = {"Scope 1":0.0, "Scope 2":0.0, "Scope 3":0.0}
if "archive_csv" not in st.session_state:
    st.session_state.archive_csv = None
if "last_reset_year" not in st.session_state:
    st.session_state.last_reset_year = None
if "last_archive_name" not in st.session_state:
    st.session_state.last_archive_name = None

# ---------------------------
# Auto-archive on April 1
# ---------------------------
today = date.today()
cycle_start, cycle_end = get_cycle_bounds(today)
if today.month==4 and today.day==1:
    if st.session_state.last_reset_year != today.year:
        if st.session_state.emissions_log:
            df_archive = pd.DataFrame(st.session_state.emissions_log)
            buf = io.StringIO()
            df_archive.to_csv(buf, index=False)
            prev_cycle_start = date(cycle_start.year-1,4,1)
            prev_cycle_end = date(prev_cycle_start.year+1,3,31)
            fname = f"emissions_Apr{prev_cycle_start.year}_Mar{prev_cycle_end.year}.csv"
            st.session_state.archive_csv = buf.getvalue()
            st.session_state.last_archive_name = fname
        st.session_state.emissions_log = []
        st.session_state.emissions_summary = {"Scope 1":0.0, "Scope 2":0.0, "Scope 3":0.0}
        st.session_state.last_reset_year = today.year

# ---------------------------
# Sidebar: Add Activity Data
# ---------------------------
st.sidebar.header("➕ Add Activity Data")
add_mode = st.sidebar.checkbox("Add Entry Mode", value=False)

selected_scope = None
selected_category = "-"
selected_activity = None
unit = "-"
ef = 0.0

if add_mode and not emission_factors.empty:
    scope_options = emission_factors["scope"].dropna().unique()
    selected_scope = st.sidebar.selectbox("Select Scope", scope_options)
    filtered_df = emission_factors[emission_factors["scope"]==selected_scope]

    if selected_scope=="Scope 3":
        category_options = filtered_df["category"].dropna().unique()
        selected_category = st.sidebar.selectbox("Select Scope 3 Category", category_options)
        category_df = filtered_df[filtered_df["category"]==selected_category]
        activity_options = category_df["activity"].dropna().unique()
        selected_activity = st.sidebar.selectbox("Select Activity", activity_options)
        activity_df = category_df[category_df["activity"]==selected_activity]
    else:
        selected_category = "-"
        activity_options = filtered_df["activity"].dropna().unique()
        selected_activity = st.sidebar.selectbox("Select Activity", activity_options)
        activity_df = filtered_df[filtered_df["activity"]==selected_activity]

    if not activity_df.empty:
        unit = str(activity_df["unit"].values[0])
        ef = float(activity_df["emission_factor"].values[0])
    else:
        unit = "-"
        ef = 0.0

    quantity = st.sidebar.number_input(f"Enter quantity ({unit})", min_value=0.0, format="%.4f")

    if st.sidebar.button("Add Entry") and quantity>0 and ef>0 and selected_scope and selected_activity:
        emissions = quantity*ef
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
            summary[e["Scope"]]+=e["Emissions (tCO₂e)"]
        st.session_state.emissions_summary = summary
        st.sidebar.success("Entry added.")

# ---------------------------
# Main Header
# ---------------------------
st.title("🌍 EinTrust GHG Dashboard")
st.markdown("Estimate Scope 1, 2 and 3 emissions. Apr–Mar cycle. Dark energy-saving theme.")

# ---------------------------
# Manual Archive & Reset
# ---------------------------
st.sidebar.markdown("---")
if st.sidebar.button("🗂️ Archive & Reset Now"):
    if st.session_state.emissions_log:
        df_arch = pd.DataFrame(st.session_state.emissions_log)
        buf = io.StringIO()
        df_arch.to_csv(buf,index=False)
        prev_cycle_start = cycle_start.replace(year=cycle_start.year-1)
        prev_cycle_end = prev_cycle_start.replace(year=prev_cycle_start.year+1,month=3,day=31)
        fname = f"emissions_Apr{prev_cycle_start.year}_Mar{prev_cycle_end.year}.csv"
        st.session_state.archive_csv = buf.getvalue()
        st.session_state.last_archive_name = fname
    st.session_state.emissions_log = []
    st.session_state.emissions_summary = {"Scope 1":0.0,"Scope 2":0.0,"Scope 3":0.0}
    st.sidebar.success("Archived & reset completed.")

if st.session_state.archive_csv:
    st.download_button(
        "⬇️ Download Last Cycle Archive (CSV)",
        data=st.session_state.archive_csv,
        file_name=st.session_state.last_archive_name or "emissions_archive.csv",
        mime="text/csv"
    )

# ---------------------------
# KPIs
# ---------------------------
st.subheader("📊 Scope-wise Emissions Summary")
kpi_cols = st.columns(3)
for idx, scope in enumerate(["Scope 1","Scope 2","Scope 3"]):
    kpi_cols[idx].markdown(f'<div class="kpi"><div class="kpi-label">{scope}</div><div class="kpi-value">{format_indian(st.session_state.emissions_summary[scope])} tCO₂e</div></div>', unsafe_allow_html=True)

# ---------------------------
# Pie Chart
# ---------------------------
if st.session_state.emissions_log:
    df_log = pd.DataFrame(st.session_state.emissions_log)
    pie_chart = px.pie(df_log, names="Scope", values="Emissions (tCO₂e)", title="Scope-wise Emission Contribution")
    st.plotly_chart(pie_chart, use_container_width=True)

# ---------------------------
# Trend Chart
# ---------------------------
if st.session_state.emissions_log:
    df_log["Timestamp"] = pd.to_datetime(df_log["Timestamp"])
    trend_df = df_log.groupby([pd.Grouper(key="Timestamp", freq="M"),"Scope"])["Emissions (tCO₂e)"].sum().reset_index()
    trend_chart = px.line(trend_df, x="Timestamp", y="Emissions (tCO₂e)", color="Scope", markers=True, title="Emission Trend Over Time")
    st.plotly_chart(trend_chart, use_container_width=True)

# ---------------------------
# Log Table
# ---------------------------
st.subheader("📝 Emissions Log")
if st.session_state.emissions_log:
    df_log_display = pd.DataFrame(st.session_state.emissions_log)
    st.dataframe(df_log_display)
else:
    st.info("No entries added yet.")
