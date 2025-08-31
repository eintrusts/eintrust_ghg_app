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
if "entries" not in st.session_state:
    st.session_state.entries = pd.DataFrame(columns=["Scope","Activity","Sub-Activity","Specific Item","Quantity","Unit","Timestamp"])
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

def render_trend_chart():
    df_log = pd.DataFrame(st.session_state.emissions_log)
    if not df_log.empty:
        df_log["Timestamp"] = pd.to_datetime(df_log.get("Timestamp", pd.Series([datetime.now()] * len(df_log))))
        df_log["MonthLabel"] = pd.Categorical(df_log["Timestamp"].dt.strftime("%b"), categories=MONTH_ORDER, ordered=True)
        trend_df = df_log.groupby(["MonthLabel","Scope"])["Quantity"].sum().reset_index()
        fig_bar = px.bar(trend_df, x="MonthLabel", y="Quantity", color="Scope", barmode="stack",
                         color_discrete_map=SCOPE_COLORS, template="plotly_dark")
        fig_bar.update_layout(paper_bgcolor="#0d1117", font_color="#e6edf3",
                              yaxis_title="Quantity", xaxis_title="")
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No data yet for trend chart.")

def render_home_dashboard():
    # KPIs
    s1 = sum([e.get("Quantity",0) for e in st.session_state.emissions_log if e.get("Scope")=="Scope 1"])
    s2 = sum([e.get("Quantity",0) for e in st.session_state.emissions_log if e.get("Scope")=="Scope 2"])
    s3 = sum([e.get("Quantity",0) for e in st.session_state.emissions_log if e.get("Scope")=="Scope 3"])
    total = s1+s2+s3
    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(f"<div class='kpi'><div class='kpi-value' style='color:white'>{format_indian(total)}</div><div class='kpi-label'>Total Emissions</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{SCOPE_COLORS['Scope 1']}'>{format_indian(s1)}</div><div class='kpi-label'>Scope 1</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{SCOPE_COLORS['Scope 2']}'>{format_indian(s2)}</div><div class='kpi-label'>Scope 2</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{SCOPE_COLORS['Scope 3']}'>{format_indian(s3)}</div><div class='kpi-label'>Scope 3</div></div>", unsafe_allow_html=True)
    
    st.subheader("📈 Emissions Trend Over Time (Monthly)")
    render_trend_chart()

def render_ghg_dashboard():
    # KPIs
    s1 = sum([e.get("Quantity",0) for e in st.session_state.emissions_log if e.get("Scope")=="Scope 1"])
    s2 = sum([e.get("Quantity",0) for e in st.session_state.emissions_log if e.get("Scope")=="Scope 2"])
    s3 = sum([e.get("Quantity",0) for e in st.session_state.emissions_log if e.get("Scope")=="Scope 3"])
    total = s1+s2+s3
    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(f"<div class='kpi'><div class='kpi-value' style='color:white'>{format_indian(total)}</div><div class='kpi-label'>Total Emissions</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{SCOPE_COLORS['Scope 1']}'>{format_indian(s1)}</div><div class='kpi-label'>Scope 1</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{SCOPE_COLORS['Scope 2']}'>{format_indian(s2)}</div><div class='kpi-label'>Scope 2</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{SCOPE_COLORS['Scope 3']}'>{format_indian(s3)}</div><div class='kpi-label'>Scope 3</div></div>", unsafe_allow_html=True)
    
    st.subheader("📈 Emissions Trend & Breakdown Over Time (Stacked)")
    render_trend_chart()

    # Add Activity Data
    st.subheader("➕ Add Activity Data")
    scope_sel = st.selectbox("Select Scope", ["Scope 1","Scope 2","Scope 3"])
    activity_sel = st.text_input("Activity / Category")
    sub_activity_sel = st.text_input("Sub-Activity / Sub-Category")
    specific_item_sel = st.text_input("Specific Item (if any)")
    unit = st.text_input("Unit (e.g., kg, kWh, Tonnes)")
    quantity = st.number_input(f"Enter Quantity ({unit})", min_value=0.0, format="%.2f")
    
    # Upload Bill / File (after quantity)
    uploaded_file = st.file_uploader("Upload Bill / File (CSV, XLS, XLSX, PDF)", type=["csv","xls","xlsx","pdf"])
    
    if st.button("Add Entry") and quantity>0:
        new_entry = {"Scope":scope_sel,"Activity":activity_sel,"Sub-Activity":sub_activity_sel,
                     "Specific Item":specific_item_sel,"Quantity":quantity,"Unit":unit,"Timestamp":datetime.now()}
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
