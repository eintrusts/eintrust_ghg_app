import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import io
import numpy as np

# --- Page Config & CSS ---
st.set_page_config(page_title="EinTrust GHG Dashboard", page_icon="🌍", layout="wide")
st.markdown("""
    <style>
      .stApp { background-color: #0d1117; color: #e6edf3; }
      .sidebar .stButton>button { background-color: #198754; color: white; }
      .kpi { background: #12131a; padding: 14px; border-radius: 10px; }
      .kpi-value { font-size: 20px; color: #81c784; font-weight:700; }
      .kpi-label { font-size: 12px; color: #cfd8dc; }
      .stDataFrame { color: #e6edf3; }
    </style>
""", unsafe_allow_html=True)

# --- Helper Utilities ---
MONTH_ORDER = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]
def format_indian(n):
    try:
        x = int(round(n))
    except:
        return "0"
    s = str(abs(x))
    if len(s) <= 3:
        res = s
    else:
        res = s[-3:]
        s = s[:-3]
        while len(s) > 2:
            res = s[-2:]+","+res; s=s[:-2]
        res = s+","+res
    return ("-" if x<0 else "") + res

def get_cycle_bounds(today):
    if today.month < 4:
        start = date(today.year-1,4,1)
        end   = date(today.year,3,31)
    else:
        start = date(today.year,4,1)
        end   = date(today.year+1,3,31)
    return start, end

# --- Load emission factors (original logic) ---
try:
    emission_factors = pd.read_csv("emission_factors.csv")
except FileNotFoundError:
    emission_factors = pd.DataFrame(columns=["scope","category","activity","unit","emission_factor"])
    st.sidebar.warning("emission_factors.csv not found.")

# --- Session State Initialization ---
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

# --- Auto-archive on April 1 ---
today = date.today()
cycle_start, cycle_end = get_cycle_bounds(today)
if today.month == 4 and today.day == 1:
    if st.session_state.last_reset_year != today.year:
        if st.session_state.emissions_log:
            df = pd.DataFrame(st.session_state.emissions_log)
            buf = io.StringIO()
            df.to_csv(buf, index=False)
            prev_start = date(cycle_start.year-1,4,1)
            prev_end = date(prev_start.year+1,3,31)
            fname = f"emissions_Apr{prev_start.year}_Mar{prev_end.year}.csv"
            st.session_state.archive_csv = buf.getvalue()
            st.session_state.last_archive_name = fname
        st.session_state.emissions_log = []
        st.session_state.emissions_summary = {"Scope 1":0.0, "Scope 2":0.0, "Scope 3":0.0}
        st.session_state.last_reset_year = today.year

# --- Sidebar with Logo & Entry Form ---
st.sidebar.image("https://avatars.githubusercontent.com/u/138943242?s=400&v=4", use_column_width=True)
st.sidebar.header("➕ Add Activity Data")
add_mode = st.sidebar.checkbox("Add Entry Mode", value=False)

# Original logic maintained
selected_scope = None; selected_category = "-"; selected_activity = None
unit = "-"; ef = 0.0

if add_mode and not emission_factors.empty:
    scope_options = emission_factors["scope"].dropna().unique()
    selected_scope = st.sidebar.selectbox("Select Scope", scope_options)
    filtered = emission_factors[emission_factors["scope"]==selected_scope]
    if selected_scope=="Scope 3":
        categories = filtered["category"].dropna().unique()
        selected_category = st.sidebar.selectbox("Select Category", categories)
        filtered = filtered[filtered["category"]==selected_category]
    selected_activity = st.sidebar.selectbox("Select Activity", filtered["activity"].dropna().unique())
    activity_df = filtered[filtered["activity"]==selected_activity]
    if not activity_df.empty:
        unit = activity_df["unit"].values[0]
        ef = float(activity_df["emission_factor"].values[0])
    quantity = st.sidebar.number_input(f"Quantity ({unit})", min_value=0.0, format="%.4f")
    if st.sidebar.button("Add Entry") and quantity>0 and ef>0:
        emissions = quantity*ef
        entry = {
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Scope": selected_scope,
            "Category": selected_category,
            "Activity": selected_activity,
            "Quantity": quantity,
            "Unit": unit,
            "Emission Factor": ef,
            "Emissions (tCO₂e)": emissions
        }
        st.session_state.emissions_log.append(entry)
        summ = {"Scope 1":0.0, "Scope 2":0.0, "Scope 3":0.0}
        for e in st.session_state.emissions_log:
            summ[e["Scope"]]+= e["Emissions (tCO₂e)"]
        st.session_state.emissions_summary = summ
        st.sidebar.success("Entry added.")

if add_mode and emission_factors.empty:
    st.sidebar.info("No emission_factors.csv. Use manual entry below.")
    a_scope = st.sidebar.selectbox("Scope", ["Scope 1","Scope 2","Scope 3"])
    a_activity = st.sidebar.text_input("Activity")
    a_unit = st.sidebar.text_input("Unit", value="-")
    a_ef = st.sidebar.number_input("Emission factor (tCO₂e per unit)", min_value=0.0, format="%.6f")
    a_qty = st.sidebar.number_input("Quantity", min_value=0.0, format="%.4f")
    if st.sidebar.button("Add Manual Entry") and a_qty>0 and a_ef>0:
        emissions = a_qty*a_ef
        entry = {
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Scope": a_scope,
            "Category": "-",
            "Activity": a_activity,
            "Quantity": a_qty,
            "Unit": a_unit,
            "Emission Factor": a_ef,
            "Emissions (tCO₂e)": emissions
        }
        st.session_state.emissions_log.append(entry)
        summ = {"Scope 1":0.0, "Scope 2":0.0, "Scope 3":0.0}
        for e in st.session_state.emissions_log:
            summ[e["Scope"]]+= e["Emissions (tCO₂e)"]
        st.session_state.emissions_summary = summ
        st.sidebar.success("Manual entry added.")

# Manual Archive & Reset
st.sidebar.markdown("---")
if st.sidebar.button("Archive & Reset Now"):
    if st.session_state.emissions_log:
        df = pd.DataFrame(st.session_state.emissions_log)
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        prev_start = date(cycle_start.year-1,4,1)
        prev_end = date(prev_start.year+1,3,31)
        fname = f"emissions_Apr{prev_start.year}_Mar{prev_end.year}.csv"
        st.session_state.archive_csv = buf.getvalue()
        st.session_state.last_archive_name = fname
    st.session_state.emissions_log = []
    st.session_state.emissions_summary = {"Scope 1":0.0, "Scope 2":0.0, "Scope 3":0.0}
    st.sidebar.success("Archived & reset.")

if st.session_state.archive_csv:
    st.sidebar.download_button(
        "⬇️ Download Last Cycle Archive (CSV)",
        data=st.session_state.archive_csv,
        file_name=st.session_state.last_archive_name or "emissions_archive.csv",
        mime="text/csv",
    )

# --- Main Dashboard ---
st.title("🌍 EinTrust GHG Dashboard")
st.markdown("Apr–Mar cycle • Dark energy-saving theme • No entry messages here")

# Key Indicators
s1 = st.session_state.emissions_summary.get("Scope 1",0.0)
s2 = st.session_state.emissions_summary.get("Scope 2",0.0)
s3 = st.session_state.emissions_summary.get("Scope 3",0.0)
total = s1+s2+s3
c1,c2,c3,c4 = st.columns(4)
c1.markdown(f"<div class='kpi'><div class='kpi-value'>{format_indian(total)}</div><div class='kpi-label'>Total Emissions</div></div>", unsafe_allow_html=True)
c2.markdown(f"<div class='kpi'><div class='kpi-value'>{format_indian(s1)}</div><div class='kpi-label'>Scope 1</div></div>", unsafe_allow_html=True)
c3.markdown(f"<div class='kpi'><div class='kpi-value'>{format_indian(s2)}</div><div class='kpi-label'>Scope 2</div></div>", unsafe_allow_html=True)
c4.markdown(f"<div class='kpi'><div class='kpi-value'>{format_indian(s3)}</div><div class='kpi-label'>Scope 3</div></div>", unsafe_allow_html=True)

# Pie chart breakdown
st.subheader("Emission Breakdown by Scope")
df_log = pd.DataFrame(st.session_state.emissions_log)
if df_log.empty:
    st.info("No data yet. Add entries via sidebar.")
else:
    palette = px.colors.qualitative.Dark24
    cmap = {"Scope 1":palette[0], "Scope 2":palette[1], "Scope 3":palette[2]}
    pie_df = df_log.groupby("Scope", sort=False)["Emissions (tCO₂e)"].sum().reset_index()
    fig_pie = px.pie(pie_df, names="Scope", values="Emissions (tCO₂e)", hole=0.45,
                     color="Scope", color_discrete_map=cmap, template="plotly_dark")
    fig_pie.update_layout(paper_bgcolor="#0d1117", font_color="#e6edf3")
    st.plotly_chart(fig_pie, use_container_width=True)

    # Trend chart
    st.subheader("Emissions Trend Over Time (Monthly — Apr→Mar)")
    df_log["Timestamp"] = pd.to_datetime(df_log["Timestamp"])
    df_cycle = df_log[(df_log["Timestamp"].dt.date >= cycle_start) & (df_log["Timestamp"].dt.date <= cycle_end)]
    if df_cycle.empty:
        st.info("No entries in current cycle.")
    else:
        df_cycle["MonthName"] = df_cycle["Timestamp"].dt.strftime("%b")
        df_cycle["MonthName"] = pd.Categorical(df_cycle["MonthName"], categories=MONTH_ORDER, ordered=True)
        stack = df_cycle.groupby(["MonthName","Scope"])["Emissions (tCO₂e)"].sum().reset_index()
        pivot = stack.pivot(index="MonthName", columns="Scope", values="Emissions (tCO₂e)").reindex(MONTH_ORDER, fill_value=0)
        melt = pivot.reset_index().melt(id_vars="MonthName", var_name="Scope", value_name="Emissions")
        fig_bar = px.bar(melt, x="MonthName", y="Emissions", color="Scope",
                         color_discrete_map=cmap, barmode="stack", template="plotly_dark")
        fig_bar.update_layout(paper_bgcolor="#0d1117", font_color="#e6edf3", xaxis_title="", yaxis_title="Emissions (tCO₂e)")
        st.plotly_chart(fig_bar, use_container_width=True)

# Emissions Log at bottom
st.subheader("Emissions Log")
if df_log.empty:
    st.info("No emission log data yet.")
else:
    df_log = df_log.sort_values("Timestamp", ascending=False).reset_index(drop=True)
    st.dataframe(df_log, use_container_width=True)
    st.download_button("📥 Download Current Log (CSV)",
                       data=df_log.to_csv(index=False), file_name="emissions_log_current.csv",
                       mime="text/csv")
