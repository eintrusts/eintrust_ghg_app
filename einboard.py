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
.kpi-value { font-size: 20px; font-weight:700; }
.kpi-label { font-size: 12px; color: #cfd8dc; }
.stDataFrame { color: #e6edf3; }
.sidebar .stButton>button { background:#198754; color:white }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Utilities
# ---------------------------
MONTH_ORDER = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]
SCOPE_COLORS = {"Scope 1":"#1E3A8A","Scope 2":"#84CC16","Scope 3":"#FACC15"}
ACTUAL_COLOR = {"Scope 1":"#1E3A8A","Scope 2":"#84CC16","Scope 3":"#FACC15"}
FORECAST_COLOR = {"Scope 1":"#60A5FA","Scope 2":"#D9F99D","Scope 3":"#FEF08A"}

def format_indian(n: float) -> str:
    try:
        x = int(round(float(n)))
    except:
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
    return ("-" if x<0 else "") + res

def get_cycle_bounds(today: date):
    if today.month < 4:
        start = date(today.year-1,4,1)
        end = date(today.year,3,31)
    else:
        start = date(today.year,4,1)
        end = date(today.year+1,3,31)
    return start,end

# ---------------------------
# Load emission factors
# ---------------------------
try:
    emission_factors = pd.read_csv("emission_factors.csv")
except FileNotFoundError:
    emission_factors = pd.DataFrame(columns=["scope","category","activity","unit","emission_factor"])
    st.sidebar.warning("emission_factors.csv not found — add it to use prefilled activities.")

# ---------------------------
# Session state initialization
# ---------------------------
for key in ["emissions_log","emissions_summary","archive_csv","last_reset_year","last_archive_name"]:
    if key not in st.session_state:
        if key=="emissions_summary":
            st.session_state[key] = {"Scope 1":0.0,"Scope 2":0.0,"Scope 3":0.0}
        else:
            st.session_state[key] = None if key!="emissions_log" else []

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
            df_archive.to_csv(buf,index=False)
            prev_cycle_start = date(cycle_start.year-1,4,1)
            prev_cycle_end = date(prev_cycle_start.year+1,3,31)
            fname = f"emissions_Apr{prev_cycle_start.year}_Mar{prev_cycle_end.year}.csv"
            st.session_state.archive_csv = buf.getvalue()
            st.session_state.last_archive_name = fname
        st.session_state.emissions_log=[]
        st.session_state.emissions_summary={"Scope 1":0.0,"Scope 2":0.0,"Scope 3":0.0}
        st.session_state.last_reset_year=today.year

# ---------------------------
# Sidebar — Add Activity Data
# ---------------------------
st.sidebar.header("Add Activity Data")
add_mode = st.sidebar.checkbox("Add Entry Mode", value=False)

if add_mode:
    if not emission_factors.empty:
        selected_scope = st.sidebar.selectbox("Select Scope", emission_factors["scope"].dropna().unique())
        filtered_df = emission_factors[emission_factors["scope"]==selected_scope]
        if selected_scope=="Scope 3":
            selected_category = st.sidebar.selectbox("Select Scope 3 Category", filtered_df["category"].dropna().unique())
            category_df = filtered_df[filtered_df["category"]==selected_category]
            selected_activity = st.sidebar.selectbox("Select Activity", category_df["activity"].dropna().unique())
            activity_df = category_df[category_df["activity"]==selected_activity]
        else:
            selected_category="-"
            selected_activity = st.sidebar.selectbox("Select Activity", filtered_df["activity"].dropna().unique())
            activity_df = filtered_df[filtered_df["activity"]==selected_activity]
        unit = str(activity_df["unit"].values[0]) if not activity_df.empty else "-"
        ef = float(activity_df["emission_factor"].values[0]) if not activity_df.empty else 0.0
        quantity = st.sidebar.number_input(f"Enter quantity ({unit})", min_value=0.0, format="%.4f")
        st.sidebar.markdown(f"**Quantity (formatted):** {format_indian(quantity)} {unit}")
        if st.sidebar.button("Add Entry") and quantity>0 and ef>0:
            emissions = quantity*ef
            st.session_state.emissions_log.append({
                "Timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Scope":selected_scope,"Category":selected_category,
                "Activity":selected_activity,"Quantity":quantity,"Unit":unit,
                "Emission Factor":ef,"Emissions (tCO₂e)":emissions
            })
            summary={"Scope 1":0.0,"Scope 2":0.0,"Scope 3":0.0}
            for e in st.session_state.emissions_log:
                summary[e["Scope"]]+=e["Emissions (tCO₂e)"]
            st.session_state.emissions_summary=summary
            st.sidebar.success("Entry added.")
    else:
        a_scope = st.sidebar.selectbox("Scope (manual)", ["Scope 1","Scope 2","Scope 3"])
        a_activity = st.sidebar.text_input("Activity (manual)")
        a_unit = st.sidebar.text_input("Unit (manual)", value="-")
        a_ef = st.sidebar.number_input("Emission factor (manual, tCO2e/unit)", min_value=0.0, format="%.6f")
        a_qty = st.sidebar.number_input(f"Quantity ({a_unit})", min_value=0.0, format="%.4f")
        st.sidebar.markdown(f"**Quantity (formatted):** {format_indian(a_qty)} {a_unit}")
        if st.sidebar.button("Add Manual Entry") and a_qty>0 and a_ef>0:
            emissions = a_qty*a_ef
            st.session_state.emissions_log.append({
                "Timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Scope":a_scope,"Category":"-","Activity":a_activity,
                "Quantity":a_qty,"Unit":a_unit,"Emission Factor":a_ef,
                "Emissions (tCO₂e)":emissions
            })
            summary={"Scope 1":0.0,"Scope 2":0.0,"Scope 3":0.0}
            for e in st.session_state.emissions_log:
                summary[e["Scope"]]+=e["Emissions (tCO₂e)"]
            st.session_state.emissions_summary=summary
            st.sidebar.success("Manual entry added.")

# ---------------------------
# Main Dashboard
# ---------------------------
st.title("🌍 EinTrust GHG Dashboard")
st.markdown("Estimate Scope 1, 2 and 3 emissions for net zero journey.")

# KPIs
s1,s2,s3 = st.session_state.emissions_summary.get("Scope 1",0.0), st.session_state.emissions_summary.get("Scope 2",0.0), st.session_state.emissions_summary.get("Scope 3",0.0)
total = s1+s2+s3
c1,c2,c3,c4 = st.columns(4)
with c1: st.markdown(f"<div class='kpi'><div class='kpi-value'>{format_indian(total)}</div><div class='kpi-label'>Total Emissions (tCO₂e)</div></div>",unsafe_allow_html=True)
with c2: st.markdown(f"<div class='kpi'><div class='kpi-value'>{format_indian(s1)}</div><div class='kpi-label'>Scope 1 (tCO₂e)</div></div>",unsafe_allow_html=True)
with c3: st.markdown(f"<div class='kpi'><div class='kpi-value'>{format_indian(s2)}</div><div class='kpi-label'>Scope 2 (tCO₂e)</div></div>",unsafe_allow_html=True)
with c4: st.markdown(f"<div class='kpi'><div class='kpi-value'>{format_indian(s3)}</div><div class='kpi-label'>Scope 3 (tCO₂e)</div></div>",unsafe_allow_html=True)

# Convert log to df
if st.session_state.emissions_log:
    df = pd.DataFrame(st.session_state.emissions_log)
else:
    df = pd.DataFrame(columns=["Timestamp","Scope","Category","Activity","Quantity","Unit","Emission Factor","Emissions (tCO₂e)"])

# ---------------------------
# Pie chart: Emission Breakdown by Scope
# ---------------------------
pie_df = pd.DataFrame([{"Scope":"Scope 1","Emissions (tCO₂e)":s1},
                       {"Scope":"Scope 2","Emissions (tCO₂e)":s2},
                       {"Scope":"Scope 3","Emissions (tCO₂e)":s3}])
fig_pie = px.pie(pie_df, names="Scope", values="Emissions (tCO₂e)", hole=0.45,
                 color="Scope", color_discrete_map=SCOPE_COLORS,
                 template="plotly_dark",
                 hover_data={"Emissions (tCO₂e)":":,.2f"})
fig_pie.update_traces(textinfo='percent+label', hovertemplate="%{label}: %{value:,.2f} tCO₂e")
st.plotly_chart(fig_pie, use_container_width=True)

# ---------------------------
# Stacked Bar: Emissions Trend (Monthly)
# ---------------------------
if not df.empty:
    df["Month"] = pd.to_datetime(df["Timestamp"]).dt.month_name().str[:3]
    monthly_df = df.groupby(["Month","Scope"],as_index=False)["Emissions (tCO₂e)"].sum()
    for m in MONTH_ORDER:
        if m not in monthly_df["Month"].unique():
            for sc in ["Scope 1","Scope 2","Scope 3"]:
                monthly_df = pd.concat([monthly_df, pd.DataFrame([{"Month":m,"Scope":sc,"Emissions (tCO₂e)":0.0}])],ignore_index=True)
    monthly_df["Month"] = pd.Categorical(monthly_df["Month"], categories=MONTH_ORDER, ordered=True)
    monthly_df = monthly_df.sort_values("Month")
    fig_bar = px.bar(monthly_df, x="Month", y="Emissions (tCO₂e)", color="Scope",
                     color_discrete_map=SCOPE_COLORS, template="plotly_dark",
                     text_auto=False, hover_data={"Emissions (tCO₂e)":":,.2f"})
    fig_bar.update_layout(barmode='stack')
    st.plotly_chart(fig_bar, use_container_width=True)

# ---------------------------
# Actual vs Forecast (per Scope)
# ---------------------------
forecast_df = pd.DataFrame({"Month":MONTH_ORDER})
for sc in ["Scope 1","Scope 2","Scope 3"]:
    forecast_df[f"{sc}_forecast"] = 0.0 if sc not in df["Scope"].unique() else df[df["Scope"]==sc].groupby(df["Month"])["Emissions (tCO₂e)"].sum().reindex(MONTH_ORDER, fill_value=0).values
fig_line = px.line(template="plotly_dark")
for sc in ["Scope 1","Scope 2","Scope 3"]:
    # Actual
    if sc in df["Scope"].unique():
        actual = df[df["Scope"]==sc].groupby(df["Month"])["Emissions (tCO₂e)"].sum().reindex(MONTH_ORDER, fill_value=0)
    else:
        actual = pd.Series([0]*len(MONTH_ORDER), index=MONTH_ORDER)
    fig_line.add_scatter(x=MONTH_ORDER, y=actual.values, mode='lines+markers',
                         name=f"{sc} Actual", line=dict(color=ACTUAL_COLOR[sc], width=3))
    # Forecast
    forecast = forecast_df[f"{sc}_forecast"]
    fig_line.add_scatter(x=MONTH_ORDER, y=forecast.values, mode='lines+markers',
                         name=f"{sc} Forecast", line=dict(color=FORECAST_COLOR[sc], width=3, dash='dot'))
fig_line.update_layout(yaxis_title="Emissions (tCO₂e)")
st.plotly_chart(fig_line, use_container_width=True)

# ---------------------------
# Emissions Log
# ---------------------------
st.subheader("Emissions Log")
st.dataframe(df)
