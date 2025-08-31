import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import io
import numpy as np

# ---------------------------
# Config & Dark Theme CSS
# ---------------------------
st.set_page_config(page_title="EinTrust GHG Dashboard", page_icon="🌍", layout="wide")

st.markdown("""
<style>
  .stApp { background-color: #0d1117; color: #e6edf3; }
  .kpi { background: #12131a; padding: 14px; border-radius: 10px; text-align:center; }
  .kpi-value { font-size: 22px; font-weight:700; }
  .kpi-label { font-size: 12px; color: #cfd8dc; }
  .stDataFrame { color: #e6edf3; }
  .sidebar .stButton>button { background:#198754; color:white }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Utilities
# ---------------------------
MONTH_ORDER = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]

SCOPE_COLORS = {
    "Scope 1": "#4CAF50",  # Green
    "Scope 2": "#2196F3",  # Blue
    "Scope 3": "#FFC107"   # Amber
}

FORECAST_COLORS = {
    "Scope 1": "#81C784",
    "Scope 2": "#64B5F6",
    "Scope 3": "#FFD54F"
}

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
if "emissions_log" not in st.session_state: st.session_state.emissions_log = []
if "emissions_summary" not in st.session_state: st.session_state.emissions_summary = {"Scope 1":0.0,"Scope 2":0.0,"Scope 3":0.0}
if "archive_csv" not in st.session_state: st.session_state.archive_csv = None
if "last_reset_year" not in st.session_state: st.session_state.last_reset_year = None
if "last_archive_name" not in st.session_state: st.session_state.last_archive_name = None

# ---------------------------
# Auto-archive on April 1
# ---------------------------
today = date.today()
cycle_start, cycle_end = get_cycle_bounds(today)
if today.month == 4 and today.day == 1 and st.session_state.last_reset_year != today.year:
    if st.session_state.emissions_log:
        df_archive = pd.DataFrame(st.session_state.emissions_log)
        buf = io.StringIO()
        df_archive.to_csv(buf, index=False)
        fname = f"emissions_Apr{cycle_start.year-1}_Mar{cycle_start.year}.csv"
        st.session_state.archive_csv = buf.getvalue()
        st.session_state.last_archive_name = fname
    st.session_state.emissions_log = []
    st.session_state.emissions_summary = {"Scope 1":0.0,"Scope 2":0.0,"Scope 3":0.0}
    st.session_state.last_reset_year = today.year

# ---------------------------
# Sidebar — Add Activity
# ---------------------------
st.sidebar.header("Add Activity Data")
add_mode = st.sidebar.checkbox("Add Entry Mode", value=False)

if add_mode:
    # Select Scope
    scope_options = ["Scope 1","Scope 2","Scope 3"]
    selected_scope = st.sidebar.selectbox("Select Scope", scope_options)
    
    if not emission_factors.empty:
        df_scope = emission_factors[emission_factors["scope"]==selected_scope]
        if selected_scope=="Scope 3":
            categories = df_scope["category"].dropna().unique()
            selected_category = st.sidebar.selectbox("Select Scope 3 Category", categories)
            df_cat = df_scope[df_scope["category"]==selected_category]
        else:
            selected_category = "-"
            df_cat = df_scope

        activities = df_cat["activity"].dropna().unique()
        selected_activity = st.sidebar.selectbox("Select Activity", activities)
        act_row = df_cat[df_cat["activity"]==selected_activity]
        unit = act_row["unit"].values[0] if not act_row.empty else "-"
        ef = float(act_row["emission_factor"].values[0]) if not act_row.empty else 0.0
    else:
        selected_category = "-"
        selected_activity = st.sidebar.text_input("Activity (manual)")
        unit = st.sidebar.text_input("Unit (manual)", value="-")
        ef = st.sidebar.number_input("Emission factor (tCO2e/unit)", min_value=0.0, format="%.6f")

    qty = st.sidebar.number_input(f"Quantity ({unit})", min_value=0.0, format="%.4f", step=1.0)
    if st.sidebar.button("Add Entry") and qty>0 and ef>0:
        emissions = qty*ef
        st.session_state.emissions_log.append({
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Scope": selected_scope,
            "Category": selected_category,
            "Activity": selected_activity,
            "Quantity": qty,
            "Unit": unit,
            "Emission Factor": ef,
            "Emissions (tCO₂e)": emissions
        })
        # Update summary
        summary = {"Scope 1":0.0,"Scope 2":0.0,"Scope 3":0.0}
        for e in st.session_state.emissions_log: summary[e["Scope"]] += e["Emissions (tCO₂e)"]
        st.session_state.emissions_summary = summary
        st.sidebar.success("Entry added.")

# ---------------------------
# Manual Archive
# ---------------------------
st.sidebar.markdown("---")
if st.sidebar.button("🗂️ Archive & Reset Now"):
    if st.session_state.emissions_log:
        df_arch = pd.DataFrame(st.session_state.emissions_log)
        buf = io.StringIO()
        df_arch.to_csv(buf,index=False)
        fname = f"emissions_Apr{cycle_start.year-1}_Mar{cycle_start.year}.csv"
        st.session_state.archive_csv = buf.getvalue()
        st.session_state.last_archive_name = fname
    st.session_state.emissions_log=[]
    st.session_state.emissions_summary={"Scope 1":0.0,"Scope 2":0.0,"Scope 3":0.0}
    st.sidebar.success("Archived & reset completed.")

if st.session_state.archive_csv:
    st.download_button("⬇️ Download Last Cycle Archive (CSV)", st.session_state.archive_csv, st.session_state.last_archive_name or "emissions_archive.csv","text/csv")

# ---------------------------
# Main dashboard
# ---------------------------
st.title("🌍 EinTrust GHG Dashboard")
st.markdown("Estimate Scope 1, 2 and 3 emissions for net zero journey.")

# KPIs
s1,s2,s3 = st.session_state.emissions_summary["Scope 1"], st.session_state.emissions_summary["Scope 2"], st.session_state.emissions_summary["Scope 3"]
total = s1+s2+s3

c1,c2,c3,c4 = st.columns(4)
with c1:
    st.markdown(f"<div class='kpi'><div class='kpi-value' style='color:white'>{format_indian(total)}</div><div class='kpi-label'>Total Emissions (tCO₂e)</div></div>", unsafe_allow_html=True)
with c2:
    st.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{SCOPE_COLORS['Scope 1']}'>{format_indian(s1)}</div><div class='kpi-label'>Scope 1 (tCO₂e)</div></div>", unsafe_allow_html=True)
with c3:
    st.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{SCOPE_COLORS['Scope 2']}'>{format_indian(s2)}</div><div class='kpi-label'>Scope 2 (tCO₂e)</div></div>", unsafe_allow_html=True)
with c4:
    st.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{SCOPE_COLORS['Scope 3']}'>{format_indian(s3)}</div><div class='kpi-label'>Scope 3 (tCO₂e)</div></div>", unsafe_allow_html=True)

# ---------------------------
# Emission Breakdown Pie
# ---------------------------
st.subheader("📊 GHG Emissions - Breakdown by Scope")
df_log = pd.DataFrame(st.session_state.emissions_log)
if not df_log.empty:
    pie_df = df_log.groupby("Scope")["Emissions (tCO₂e)"].sum().reindex(["Scope 1","Scope 2","Scope 3"]).fillna(0).reset_index()
    fig_pie = px.pie(pie_df, names="Scope", values="Emissions (tCO₂e)", hole=0.45,
                     color="Scope", color_discrete_map=SCOPE_COLORS, template="plotly_dark",
                     hover_data=["Emissions (tCO₂e)"])
    fig_pie.update_traces(hovertemplate='%{label}: %{value:,} tCO₂e<br>%{percent}')
    fig_pie.update_layout(paper_bgcolor="#0d1117", font_color="#e6edf3")
    st.plotly_chart(fig_pie, use_container_width=True)
else:
    st.info("No data to show in breakdown. Add entries from sidebar.")

# ---------------------------
# Emissions Trend Over Time
# ---------------------------
st.subheader("📈 Emissions Trend Over Time (Monthly) - Actual vs Forecast")
if not df_log.empty:
    df_log["Timestamp"] = pd.to_datetime(df_log["Timestamp"], errors="coerce")
    df_log = df_log.dropna(subset=["Timestamp"])
    df_cycle = df_log[(df_log["Timestamp"].dt.date>=cycle_start)&(df_log["Timestamp"].dt.date<=cycle_end)].copy()
    df_cycle["MonthLabel"] = pd.Categorical(df_cycle["Timestamp"].dt.strftime("%b"), categories=MONTH_ORDER, ordered=True)
    stacked = df_cycle.groupby(["MonthLabel","Scope"])["Emissions (tCO₂e)"].sum().reset_index()
    pivot = stacked.pivot(index="MonthLabel", columns="Scope", values="Emissions (tCO₂e)").reindex(MONTH_ORDER).fillna(0)
    pivot = pivot.reset_index()
    
    # Forecast
    forecast_df = pd.DataFrame({"MonthLabel": MONTH_ORDER})
    for sc in ["Scope 1","Scope 2","Scope 3"]:
        y = pivot[sc].values.astype(float)
        x = np.arange(len(y))
        observed = np.where(y>0)[0]
        if len(observed)>=2:
            coef = np.polyfit(observed, y[observed],1)
            forecast = np.polyval(coef, x)
            forecast_vals = [np.nan if i<=observed.max() else max(0,float(forecast[i])) for i in range(len(x))]
        else:
            forecast_vals = [np.nan]*len(x)
        forecast_df[sc] = forecast_vals
    
    # Plot actual stacked bar
    melt = pivot.melt(id_vars=["MonthLabel"], var_name="Scope", value_name="Emissions")
    fig_bar = px.bar(melt, x="MonthLabel", y="Emissions", color="Scope", color_discrete_map=SCOPE_COLORS,
                     template="plotly_dark", barmode="stack", hover_data={"Emissions":":,.2f"})
    
    # Add forecast lines
    for sc in ["Scope 1","Scope 2","Scope 3"]:
        fig_bar.add_scatter(x=forecast_df["MonthLabel"], y=forecast_df[sc], mode="lines+markers",
                            name=f"{sc} Forecast", line=dict(color=FORECAST_COLORS[sc], dash="dot"),
                            hovertemplate=f"{sc} Forecast: %{{y:,.2f}} tCO₂e<br>%{{x}}")
    
    fig_bar.update_layout(paper_bgcolor="#0d1117", font_color="#e6edf3", xaxis_title="", yaxis_title="Emissions (tCO₂e)")
    st.plotly_chart(fig_bar, use_container_width=True)
else:
    st.info("No data for trend. Add entries from sidebar.")

# ---------------------------
# Emissions Log
# ---------------------------
st.subheader("📜 Emissions Log")
if st.session_state.emissions_log:
    log_df = pd.DataFrame(st.session_state.emissions_log).sort_values("Timestamp", ascending=False).reset_index(drop=True)
    st.dataframe(log_df, use_container_width=True)
    st.download_button("📥 Download Current Log (CSV)", log_df.to_csv(index=False), "emissions_log_current.csv", "text/csv")
else:
    st.info("No emission log data yet. Add entries from the sidebar.")
