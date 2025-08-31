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
MONTH_ORDER = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]

SCOPE_COLORS = {"Scope 1": "#76c7c0", "Scope 2": "#f6c85f", "Scope 3": "#f28e2c"}
ACTUAL_COLOR = {"Scope 1": "#76c7c0", "Scope 2": "#f6c85f", "Scope 3": "#f28e2c"}
FORECAST_COLOR = {"Scope 1": "#4ca6a0", "Scope 2": "#d9b44a", "Scope 3": "#e07b1f"}

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
# Session state initialization
# ---------------------------
if "emissions_log" not in st.session_state:
    st.session_state.emissions_log = []
if "emissions_summary" not in st.session_state:
    st.session_state.emissions_summary = {"Scope 1": 0.0, "Scope 2": 0.0, "Scope 3": 0.0}
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
if today.month == 4 and today.day == 1:
    if st.session_state.last_reset_year != today.year:
        if st.session_state.emissions_log:
            df_archive = pd.DataFrame(st.session_state.emissions_log)
            buf = io.StringIO()
            df_archive.to_csv(buf, index=False)
            prev_cycle_start = date(cycle_start.year - 1, 4, 1)
            prev_cycle_end = date(prev_cycle_start.year + 1, 3, 31)
            fname = f"emissions_Apr{prev_cycle_start.year}_Mar{prev_cycle_end.year}.csv"
            st.session_state.archive_csv = buf.getvalue()
            st.session_state.last_archive_name = fname
        st.session_state.emissions_log = []
        st.session_state.emissions_summary = {"Scope 1": 0.0, "Scope 2": 0.0, "Scope 3": 0.0}
        st.session_state.last_reset_year = today.year

# ---------------------------
# Sidebar — Add Activity Data
# ---------------------------
st.sidebar.header("Add Activity Data")
add_mode = st.sidebar.checkbox("Add Entry Mode", value=False)

if add_mode:
    # Use emission factors if available
    if not emission_factors.empty:
        scope_options = emission_factors["scope"].dropna().unique()
        selected_scope = st.sidebar.selectbox("Select Scope", scope_options)
        filtered_df = emission_factors[emission_factors["scope"] == selected_scope]

        if selected_scope == "Scope 3":
            category_options = filtered_df["category"].dropna().unique()
            selected_category = st.sidebar.selectbox("Select Scope 3 Category", category_options)
            category_df = filtered_df[filtered_df["category"] == selected_category]
            activity_options = category_df["activity"].dropna().unique()
            selected_activity = st.sidebar.selectbox("Select Activity", activity_options)
            activity_df = category_df[category_df["activity"] == selected_activity]
        else:
            selected_category = "-"
            activity_options = filtered_df["activity"].dropna().unique()
            selected_activity = st.sidebar.selectbox("Select Activity", activity_options)
            activity_df = filtered_df[filtered_df["activity"] == selected_activity]

        if not activity_df.empty:
            unit = str(activity_df["unit"].values[0])
            ef = float(activity_df["emission_factor"].values[0])
        else:
            unit = "-"
            ef = 0.0

        quantity = st.sidebar.number_input(f"Enter quantity ({unit})", min_value=0.0, format="%.4f", step=1.0)

        if st.sidebar.button("Add Entry") and quantity > 0 and ef > 0:
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
            # Update summary
            summary = {"Scope 1": 0.0, "Scope 2": 0.0, "Scope 3": 0.0}
            for e in st.session_state.emissions_log:
                summary[e["Scope"]] += e["Emissions (tCO₂e)"]
            st.session_state.emissions_summary = summary
            st.sidebar.success("Entry added.")

# Manual entries if no CSV
if add_mode and emission_factors.empty:
    a_scope = st.sidebar.selectbox("Scope (manual)", ["Scope 1", "Scope 2", "Scope 3"])
    a_activity = st.sidebar.text_input("Activity (manual)")
    a_unit = st.sidebar.text_input("Unit (manual)", value="-")
    a_ef = st.sidebar.number_input("Emission factor (manual, tCO2e per unit)", min_value=0.0, format="%.6f")
    a_qty = st.sidebar.number_input(f"Quantity ({a_unit})", min_value=0.0, format="%.4f")
    if st.sidebar.button("Add Manual Entry") and a_qty > 0 and a_ef > 0:
        emissions = a_qty * a_ef
        new_entry = {
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Scope": a_scope,
            "Category": "-",
            "Activity": a_activity,
            "Quantity": a_qty,
            "Unit": a_unit,
            "Emission Factor": a_ef,
            "Emissions (tCO₂e)": emissions
        }
        st.session_state.emissions_log.append(new_entry)
        summary = {"Scope 1": 0.0, "Scope 2": 0.0, "Scope 3": 0.0}
        for e in st.session_state.emissions_log:
            summary[e["Scope"]] += e["Emissions (tCO₂e)"]
        st.session_state.emissions_summary = summary
        st.sidebar.success("Manual entry added.")

# ---------------------------
# Main Dashboard
# ---------------------------
st.title("🌍 EinTrust GHG Dashboard")
st.markdown("Estimate Scope 1, 2 and 3 emissions for net zero journey.")

# ---------------------------
# Manual Archive & Reset
# ---------------------------
st.sidebar.markdown("---")
if st.sidebar.button("🗂️ Archive & Reset Now"):
    if st.session_state.emissions_log:
        df_arch = pd.DataFrame(st.session_state.emissions_log)
        buf = io.StringIO()
        df_arch.to_csv(buf, index=False)
        prev_cycle_start = cycle_start.replace(year=cycle_start.year - 1)
        prev_cycle_end = prev_cycle_start.replace(year=prev_cycle_start.year + 1, month=3, day=31)
        fname = f"emissions_Apr{prev_cycle_start.year}_Mar{prev_cycle_end.year}.csv"
        st.session_state.archive_csv = buf.getvalue()
        st.session_state.last_archive_name = fname
    st.session_state.emissions_log = []
    st.session_state.emissions_summary = {"Scope 1": 0.0, "Scope 2": 0.0, "Scope 3": 0.0}
    st.sidebar.success("Archived & reset completed.")

if st.session_state.archive_csv:
    st.download_button(
        "⬇️ Download Last Cycle Archive (CSV)",
        data=st.session_state.archive_csv,
        file_name=st.session_state.last_archive_name or "emissions_archive.csv",
        mime="text/csv",
    )

# ---------------------------
# KPIs
# ---------------------------
st.subheader("📊 GHG Emissions")
s1 = st.session_state.emissions_summary.get("Scope 1",0.0)
s2 = st.session_state.emissions_summary.get("Scope 2",0.0)
s3 = st.session_state.emissions_summary.get("Scope 3",0.0)
total = s1+s2+s3

c1,c2,c3,c4 = st.columns(4)
c1.markdown(f"<div class='kpi'><div class='kpi-value' style='color:white'>{format_indian(total)}</div><div class='kpi-label'>Total Emissions (tCO₂e)</div></div>",unsafe_allow_html=True)
c2.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{SCOPE_COLORS['Scope 1']}'>{format_indian(s1)}</div><div class='kpi-label'>Scope 1 (tCO₂e)</div></div>",unsafe_allow_html=True)
c3.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{SCOPE_COLORS['Scope 2']}'>{format_indian(s2)}</div><div class='kpi-label'>Scope 2 (tCO₂e)</div></div>",unsafe_allow_html=True)
c4.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{SCOPE_COLORS['Scope 3']}'>{format_indian(s3)}</div><div class='kpi-label'>Scope 3 (tCO₂e)</div></div>",unsafe_allow_html=True)

# ---------------------------
# Emission Breakdown by Scope (Pie)
# ---------------------------
df = pd.DataFrame(st.session_state.emissions_log)
pie_df = df.groupby("Scope")["Emissions (tCO₂e)"].sum().reindex(["Scope 1","Scope 2","Scope 3"],fill_value=0).reset_index()
fig_pie = px.pie(pie_df,names="Scope",values="Emissions (tCO₂e)",hole=0.45,
                 color="Scope", color_discrete_map=SCOPE_COLORS, template="plotly_dark")
fig_pie.update_traces(textinfo='percent+label', hovertemplate="%{label}: %{value:,.2f} tCO₂e")
st.subheader("🧩 Emission Breakdown by Scope")
st.plotly_chart(fig_pie,use_container_width=True)

# ---------------------------
# Stacked Bar: Emissions Trend Monthly
# ---------------------------
if not df.empty:
    df["MonthLabel"] = pd.Categorical(pd.to_datetime(df["Timestamp"]).dt.strftime("%b"), categories=MONTH_ORDER, ordered=True)
    stacked=[]
    for m in MONTH_ORDER:
        for sc in ["Scope 1","Scope 2","Scope 3"]:
            val=df[(df["MonthLabel"]==m)&(df["Scope"]==sc)]["Emissions (tCO₂e)"].sum()
            stacked.append({"MonthLabel":m,"Scope":sc,"Emissions (tCO₂e)":val})
    stacked_df=pd.DataFrame(stacked)
    fig_bar=px.bar(stacked_df,x="MonthLabel",y="Emissions (tCO₂e)",color="Scope",barmode="stack",
                   color_discrete_map=SCOPE_COLORS,template="plotly_dark")
    st.subheader("📈 Emissions Trend Over Time (Monthly)")
    st.plotly_chart(fig_bar,use_container_width=True)

# ---------------------------
# Actual vs Forecast per Scope
# ---------------------------
fig_line = px.line(template="plotly_dark")
for sc in ["Scope 1","Scope 2","Scope 3"]:
    actual = df[df["Scope"]==sc].groupby("MonthLabel")["Emissions (tCO₂e)"].sum().reindex(MONTH_ORDER, fill_value=0)
    observed = np.where(actual.values>0)[0]
    if len(observed) >= 2:
        coef = np.polyfit(observed, actual.values[observed],1)
        forecast = np.polyval(coef, np.arange(len(MONTH_ORDER)))
        forecast_vals = [np.nan if i<=observed.max() else max(0,forecast[i]) for i in range(len(MONTH_ORDER))]
    else:
        forecast_vals = [np.nan]*12
    fig_line.add_scatter(
        x=MONTH_ORDER, y=actual.values, mode="lines+markers", name=f"{sc} Actual",
        line=dict(color=ACTUAL_COLOR[sc], width=3),
        hovertemplate=f"{sc} Actual: %{y:,.2f} tCO₂e<br>%{{x}}"
    )
    fig_line.add_scatter(
        x=MONTH_ORDER, y=forecast_vals, mode="lines+markers", name=f"{sc} Forecast",
        line=dict(color=FORECAST_COLOR[sc], width=3,dash="dot"),
        hovertemplate=f"{sc} Forecast: %{y:,.2f} tCO₂e<br>%{{x}}",
        visible="legendonly"
    )
fig_line.update_layout(yaxis_title="Emissions (tCO₂e)", legend_title_text="Scope & Type")
st.subheader("📊 Actual vs Forecast per Scope")
st.plotly_chart(fig_line,use_container_width=True)

# ---------------------------
# Emissions Log at Bottom
# ---------------------------
st.subheader("📜 Emissions Log")
if df.empty:
    st.info("No emission log data yet. Add entries from sidebar.")
else:
    st.dataframe(df, use_container_width=True)
    st.download_button(
        "📥 Download Current Log (CSV)",
        data=df.to_csv(index=False),
        file_name="emissions_log_current.csv",
        mime="text/csv"
    )
