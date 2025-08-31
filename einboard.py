import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import io
import numpy as np

# =============================================================
# EinTrust GHG Dashboard — Apr–Mar Cycle, Dark Theme, Archive
# Keeps your original activity data entry (scope/category/activity)
# Adds: Apr–Mar auto-reset + manual archive, monthly trend (Apr→Mar),
# Indian numbering, KPIs with Total, NO delete & NO latest-entry card
# =============================================================

# --- Page Config ---
st.set_page_config(page_title="EinTrust GHG Dashboard", page_icon="🌍", layout="wide")

# --- Dark Energy-Saving Theme (CSS) ---
st.markdown(
    """
    <style>
      .stApp{ background:#0d1117; color:#e6edf3; }
      .kpi-card{ background:#161b22; padding:16px; border-radius:14px; box-shadow:0 2px 10px rgba(0,0,0,.35); }
      .kpi-value{ font-size:22px; font-weight:700; color:#81c784; }
      .kpi-label{ font-size:13px; opacity:.9; }
      .section{ color:#e6edf3; }
      .stDataFrame{ color:#e6edf3; }
      .stDownloadButton>button, .stButton>button{ background:#198754; color:white; border-radius:10px; border:0; padding:8px 14px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Utilities ---
MONTH_ORDER = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]
MONTH_TO_NUM = {m:i+4 if i<9 else i-8 for i,m in enumerate(MONTH_ORDER)}  # Apr=4,...,Dec=12,Jan=1,...


def format_indian(n: float) -> str:
    try:
        x = float(n)
    except (TypeError, ValueError):
        return "0"
    neg = x < 0
    x = abs(int(round(x)))
    s = str(x)
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
    return ("-" if neg else "") + res


def get_cycle_bounds(today: date):
    if today.month < 4:  # Jan–Mar -> current cycle started last Apr
        start = date(today.year - 1, 4, 1)
        end = date(today.year, 3, 31)
    else:  # Apr–Dec -> current cycle ends next Mar
        start = date(today.year, 4, 1)
        end = date(today.year + 1, 3, 31)
    return start, end


# --- Load Emission Factors (unchanged logic) ---
try:
    emission_factors = pd.read_csv("emission_factors.csv")
except FileNotFoundError:
    emission_factors = pd.DataFrame(columns=["scope","category","activity","unit","emission_factor"])
    st.warning("Emission factors file not found. Dashboard will work, but no emissions can be calculated.")

# --- Session State ---
if "emissions_summary" not in st.session_state:
    st.session_state.emissions_summary = {"Scope 1":0.0, "Scope 2":0.0, "Scope 3":0.0}
if "emissions_log" not in st.session_state:
    st.session_state.emissions_log = []  # list of dicts
if "last_reset_year" not in st.session_state:
    st.session_state.last_reset_year = None  # used for April 1 auto-reset guard
if "archive_csv" not in st.session_state:
    st.session_state.archive_csv = None  # in-memory CSV (string)


# --- Automatic April 1 Reset & Archive (in-memory) ---

def archive_and_reset(now_dt: datetime, reason: str = "auto"):
    # archive current log to CSV in-memory (if any rows), then clear state
    if st.session_state.emissions_log:
        df = pd.DataFrame(st.session_state.emissions_log)
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        st.session_state.archive_csv = buf.getvalue()
    # reset log & summary
    st.session_state.emissions_log = []
    st.session_state.emissions_summary = {"Scope 1":0.0, "Scope 2":0.0, "Scope 3":0.0}
    st.session_state.last_reset_year = now_dt.year


_today = datetime.now().date()
cycle_start, cycle_end = get_cycle_bounds(_today)
# Auto-trigger only once per year on April 1
if _today.month == 4 and _today.day == 1:
    if st.session_state.last_reset_year != _today.year:
        archive_and_reset(datetime.now(), reason="auto")


# --- Sidebar: Add Activity Data (ORIGINAL LOGIC KEPT) ---
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

    if selected_scope == "Scope 3":
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

    quantity = st.sidebar.number_input(f"Enter quantity ({unit})", min_value=0.0, format="%.4f")

    if st.sidebar.button("Add Entry") and quantity>0 and ef>0 and selected_scope and selected_activity:
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
        # update summary
        summary = {"Scope 1":0.0, "Scope 2":0.0, "Scope 3":0.0}
        for e in st.session_state.emissions_log:
            summary[e["Scope"]] += e["Emissions (tCO₂e)"]
        st.session_state.emissions_summary = summary
        st.success("Entry added.")

# Manual Archive & Reset (in-memory)
st.sidebar.markdown("---")
if st.sidebar.button("🗂️ Archive & Reset Now"):
    archive_and_reset(datetime.now(), reason="manual")
    st.sidebar.success("Archived current cycle and reset.")

# Show archive download (latest only)
if st.session_state.archive_csv:
    # Name archive for the previous cycle relative to 'today'
    prev_end = cycle_start.replace(year=cycle_start.year if cycle_start.month==4 else cycle_start.year) - pd.Timedelta(days=1)
    # But simpler: label by Apr(start)-Mar(end) of LAST completed cycle
    last_cycle_start = date(cycle_start.year-1 if _today.month>=4 else cycle_start.year-1, 4, 1)
    last_cycle_end = date(last_cycle_start.year+1, 3, 31)
    fname = f"emissions_Apr{last_cycle_start.year}_Mar{last_cycle_end.year}.csv"
    st.download_button("⬇️ Download Last Cycle Archive (CSV)", data=st.session_state.archive_csv, file_name=fname, mime="text/csv")

# --- Main ---
st.title("🌍 EinTrust GHG Dashboard")
st.markdown("Estimate Scope 1, 2, and 3 emissions for your net-zero journey. (Apr–Mar cycle)")

# === KPI Cards ===
st.subheader("📊 Key Emission Indicators")
col1, col2, col3, col4 = st.columns(4)
for i, scope in enumerate(["Scope 1","Scope 2","Scope 3"]):
    val = st.session_state.emissions_summary.get(scope, 0.0)
    with [col1,col2,col3][i]:
        st.markdown(f"<div class='kpi-card'><div class='kpi-value'>{format_indian(val)}</div><div class='kpi-label'>{scope} Emissions (tCO₂e)</div></div>", unsafe_allow_html=True)
with col4:
    total_val = sum(st.session_state.emissions_summary.values())
    st.markdown(f"<div class='kpi-card'><div class='kpi-value'>{format_indian(total_val)}</div><div class='kpi-label'>Total Emissions (tCO₂e)</div></div>", unsafe_allow_html=True)

# === Pie (by Scope) ===
st.subheader("🧩 Emission Breakdown by Scope")
chart_df = pd.DataFrame.from_dict(st.session_state.emissions_summary, orient="index", columns=["Emissions"]).reset_index().rename(columns={"index":"Scope"})
chart_df = chart_df[chart_df["Emissions"]>0]
if not chart_df.empty:
    fig = px.pie(chart_df, names="Scope", values="Emissions", hole=0.45, color_discrete_sequence=px.colors.sequential.Teal_r)
    fig.update_layout(paper_bgcolor="#0d1117", font_color="#e6edf3")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No data to chart yet.")

# === Emission Log Table (NO delete; hide latest-entry card) ===
if st.session_state.emissions_log:
    st.subheader("📂 Emissions Log")
    log_df = pd.DataFrame(st.session_state.emissions_log)
    log_df.index = range(1,len(log_df)+1)

    # Add total row
    total_row = pd.DataFrame([{
        "Timestamp":"-",
        "Scope":"Total",
        "Category":"-",
        "Activity":"-",
        "Quantity": log_df["Quantity"].sum() if "Quantity" in log_df else 0,
        "Unit":"",
        "Emission Factor":"-",
        "Emissions (tCO₂e)": log_df["Emissions (tCO₂e)"].sum()
    }])
    final_df = pd.concat([log_df, total_row], ignore_index=True)
    final_df.index = range(1,len(final_df)+1)
    st.dataframe(final_df, use_container_width=True)

    # Download current log
    st.download_button("📥 Download Current Log (CSV)", data=final_df.to_csv(index=False), file_name="emissions_log_current.csv", mime="text/csv")
else:
    st.info("No emission log data yet. Add from sidebar.")

# === Monthly Trend (Apr→Mar), with Forecast to March ===
if st.session_state.emissions_log:
    st.subheader("📈 Emissions Trend Over Time (Monthly — Apr→Mar)")
    df = pd.DataFrame(st.session_state.emissions_log)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
    df = df.dropna(subset=["Timestamp"])  # keep valid timestamps

    # Filter only current cycle entries
    df_cycle = df[(df["Timestamp"].dt.date >= cycle_start) & (df["Timestamp"].dt.date <= cycle_end)].copy()

    # Build monthly totals per scope & total
    if not df_cycle.empty:
        df_cycle["Month"] = df_cycle["Timestamp"].dt.month
        # Map to Apr→Mar labels
        df_cycle["MonLabel"] = df_cycle["Timestamp"].dt.strftime("%b")
        monthly = df_cycle.groupby("MonLabel")["Emissions (tCO₂e)"].sum().reindex(MONTH_ORDER).fillna(0).reset_index()
        monthly = monthly.rename(columns={"MonLabel":"Month", "Emissions (tCO₂e)":"Total Emissions"})

        # Also stacked by scope (for stacked bar)
        by_scope = df_cycle.pivot_table(index="MonLabel", columns="Scope", values="Emissions (tCO₂e)", aggfunc="sum").reindex(MONTH_ORDER).fillna(0)
        by_scope = by_scope.reset_index().rename(columns={"MonLabel":"Month"})

        # Forecast to March (simple linear fit on months with data)
        # x as month index 0..11 in Apr→Mar order
        y = monthly["Total Emissions"].values.astype(float)
        x = np.arange(len(MONTH_ORDER))
        # find available months (non-zero or any entries)
        observed_idx = np.where(~np.isnan(y) & (y>=0))[0]
        if observed_idx.size >= 2:
            coef = np.polyfit(observed_idx, y[observed_idx], 1)  # linear
            forecast_y = np.polyval(coef, x)
            # Only keep forecast for months after the last observed month until March
            last_obs = observed_idx[y[observed_idx]>0].max() if (y[observed_idx]>0).any() else observed_idx.max()
            forecast_mask = x > last_obs
            forecast_vals = np.where(forecast_mask, np.maximum(0, forecast_y), np.nan)
            forecast_df = pd.DataFrame({"Month": MONTH_ORDER, "Forecast": forecast_vals})
        else:
            forecast_df = pd.DataFrame({"Month": MONTH_ORDER, "Forecast": [np.nan]*12})

        # Stacked bar for scopes
        bar_df = by_scope.melt(id_vars=["Month"], var_name="Scope", value_name="Emissions")
        fig_bar = px.bar(bar_df, x="Month", y="Emissions", color="Scope", barmode="stack")
        fig_bar.update_layout(title="Stacked Emissions by Scope (Apr→Mar)", paper_bgcolor="#0d1117", plot_bgcolor="#0d1117", font_color="#e6edf3")
        st.plotly_chart(fig_bar, use_container_width=True)

        # Line for total + dashed forecast
        line_df = monthly.copy()
        fig_line = px.line(line_df, x="Month", y="Total Emissions", markers=True)
        if forecast_df["Forecast"].notna().any():
            fig_line.add_scatter(x=forecast_df["Month"], y=forecast_df["Forecast"], mode="lines+markers", name="Forecast", line=dict(dash="dash"))
        fig_line.update_layout(title="Total Emissions (Apr→Mar) with Forecast to March", paper_bgcolor="#0d1117", plot_bgcolor="#0d1117", font_color="#e6edf3")
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("No entries in the current Apr–Mar cycle yet.")
