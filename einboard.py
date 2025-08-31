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
with st.sidebar:
    st.image("https://github.com/eintrusts/eintrust_ghg_app/raw/main/EinTrust%20%20logo.png", use_container_width=True)
    st.markdown("---")
    
    if st.button("Home"):
        st.session_state.page = "Home"
    
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
    
    social_exp = st.expander("Social", expanded=False)
    with social_exp:
        if st.button("Employee"):
            st.session_state.page = "Employee"
        if st.button("Health & Safety"):
            st.session_state.page = "Health & Safety"
        if st.button("CSR"):
            st.session_state.page = "CSR"
    
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

    # Pie Chart
    st.subheader("📊 Emission Breakdown by Scope")
    df_log = pd.DataFrame(st.session_state.emissions_log)
    if not df_log.empty:
        pie_df = df_log.groupby("Scope", sort=False)["Emissions (tCO₂e)"].sum().reindex(["Scope 1", "Scope 2", "Scope 3"]).fillna(0).reset_index()
        fig_pie = px.pie(
            pie_df,
            names="Scope",
            values="Emissions (tCO₂e)",
            hole=0.45,
            color="Scope",
            color_discrete_map=SCOPE_COLORS,
            template="plotly_dark"
        )
        fig_pie.update_layout(paper_bgcolor="#0d1117", font_color="#e6edf3")
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No emission data available for the pie chart.")

    # Monthly Trend
    st.subheader("📈 Emissions Trend Over Time (Monthly)")
    if not df_log.empty:
        df_log["Timestamp"] = pd.to_datetime(df_log["Timestamp"], errors="coerce")
        df_log = df_log.dropna(subset=["Timestamp"])
        cycle_start, cycle_end = get_cycle_bounds(date.today())
        df_cycle = df_log[(df_log["Timestamp"].dt.date >= cycle_start) & (df_log["Timestamp"].dt.date <= cycle_end)].copy()
        if df_cycle.empty:
            st.info("No entries in the current Apr–Mar cycle yet.")
        else:
            df_cycle["MonthLabel"] = pd.Categorical(df_cycle["Timestamp"].dt.strftime("%b"), categories=MONTH_ORDER, ordered=True)
            stacked = df_cycle.groupby(["MonthLabel", "Scope"])["Emissions (tCO₂e)"].sum().reset_index()
            pivot = stacked.pivot(index="MonthLabel", columns="Scope", values="Emissions (tCO₂e)").reindex(MONTH_ORDER).fillna(0)
            pivot = pivot.reset_index()
            melt = pivot.melt(id_vars=["MonthLabel"], var_name="Scope", value_name="Emissions (tCO₂e)")

            fig_bar = px.bar(
                melt,
                x="MonthLabel",
                y="Emissions (tCO₂e)",
                color="Scope",
                color_discrete_map=SCOPE_COLORS,
                barmode="stack",
                template="plotly_dark"
            )
            fig_bar.update_layout(paper_bgcolor="#0d1117", font_color="#e6edf3", xaxis_title="", yaxis_title="Emissions (tCO₂e)")
            st.plotly_chart(fig_bar, use_container_width=True)

    # -----------------------------
    # NEW: Indian SME GHG Data Entry
    # -----------------------------
    if include_data:
        st.subheader("➕ Add Activity Data (Indian SME GHG)")
        import numpy as np

        # Helper Dictionaries
        scope_activities = {
            "Scope 1": {
                "Stationary Combustion": {
                    "Diesel Generator": "Generator running on diesel for electricity",
                    "Petrol Generator": "Generator running on petrol for electricity",
                    "LPG Boiler": "Boiler or stove using LPG",
                    "Coal Boiler": "Boiler/furnace burning coal",
                    "Biomass Furnace": "Furnace burning wood/agricultural residue"
                },
                "Mobile Combustion": {
                    "Diesel Vehicle": "Truck/van running on diesel",
                    "Petrol Car": "Car/van running on petrol",
                    "CNG Vehicle": "Bus or delivery vehicle running on CNG",
                    "Diesel Forklift": "Forklift running on diesel",
                    "Petrol Two-Wheeler": "Scooter or bike running on petrol"
                },
                "Process Emissions": {
                    "Cement Production": "CO₂ from cement making",
                    "Steel Production": "CO₂ from steel processing",
                    "Brick Kiln": "CO₂ from brick firing",
                    "Textile Processing": "Emissions from dyeing/fabric processing",
                    "Chemical Manufacturing": "Emissions from chemical reactions",
                    "Food Processing": "Emissions from cooking/heating"
                },
                "Fugitive Emissions": {
                    "Refrigerant (HFC/HCFC)": "Gas leak from AC/refrigerator",
                    "Methane (CH₄)": "Methane leaks from storage/pipelines",
                    "SF₆": "Gas leak from electrical equipment"
                }
            },
            "Scope 2": {
                "Electricity Consumption": {"Grid Electricity": "Electricity bought from grid",
                                            "Diesel Generator Electricity": "Electricity generated on-site with diesel"},
                "Steam / Heat": {"Purchased Steam": "Steam bought from external supplier"},
                "Cooling / Chilled Water": {"Purchased Cooling": "Cooling bought from supplier"}
            },
            "Scope 3": {
                "Purchased Goods & Services": {
                    "Raw Materials": ["Cement", "Steel", "Chemicals", "Textile"],
                    "Packaging Materials": ["Cardboard", "Plastics", "Glass"],
                    "Office Supplies": ["Paper", "Ink", "Stationery"],
                    "Purchased Services": ["Printing", "Logistics", "Cleaning", "IT"]
                },
                "Business Travel": {
                    "Air Travel": None,
                    "Train Travel": None,
                    "Taxi / Cab / Auto": None
                },
                "Employee Commuting": {
                    "Two-Wheelers": None,
                    "Cars / Vans": None,
                    "Public Transport": None
                },
                "Waste Generated": {
                    "Landfill": None,
                    "Recycling": None,
                    "Composting / Biogas": None
                },
                "Upstream Transportation & Distribution": {
                    "Incoming Goods Transport": None,
                    "Third-party Logistics": None
                },
                "Downstream Transportation & Distribution": {
                    "Delivery to Customers": None,
                    "Retail / Distributor Transport": None
                },
                "Use of Sold Products": {"Product Use": None},
                "End-of-Life Treatment": {"Recycling / Landfill": None}
            }
        }

        units_dict = {
            "Diesel Generator": "Liters",
            "Petrol Generator": "Liters",
            "LPG Boiler": "Liters",
            "Coal Boiler": "kg",
            "Biomass Furnace": "kg",
            "Diesel Vehicle": "Liters",
            "Petrol Car": "Liters",
            "CNG Vehicle": "m³",
            "Diesel Forklift": "Liters",
            "Petrol Two-Wheeler": "Liters",
            "Cement Production": "Tonnes",
            "Steel Production": "Tonnes",
            "Brick Kiln": "Tonnes",
            "Textile Processing": "Tonnes",
            "Chemical Manufacturing": "Tonnes",
            "Food Processing": "Tonnes",
            "Refrigerant (HFC/HCFC)": "kg",
            "Methane (CH₄)": "kg",
            "SF₆": "kg",
            "Grid Electricity": "kWh",
            "Diesel Generator Electricity": "kWh",
            "Purchased Steam": "Tonnes",
            "Purchased Cooling": "kWh"
        }

        # Initialize Session State
        if 'entries' not in st.session_state:
            st.session_state.entries = pd.DataFrame(columns=["Scope","Activity","Sub-Activity","Specific Item","Quantity","Unit"])

        # Scope Selection
        scope_sel = st.selectbox("Select Scope", ["Scope 1", "Scope 2", "Scope 3"])

        # Activity Selection
        activity_sel = st.selectbox("Select Activity / Category", list(scope_activities[scope_sel].keys()))

        # Sub-Activity Selection
        sub_options = scope_activities[scope_sel][activity_sel]
        if scope_sel != "Scope 3":
            sub_activity_sel = st.selectbox("Select Sub-Activity", list(sub_options.keys()))
            st.info(sub_options[sub_activity_sel])
        else:
            sub_activity_sel = st.selectbox("Select Sub-Category", list(sub_options.keys()))

        # Specific Item for Scope 3
        specific_item_sel = None
        if scope_sel == "Scope 3":
            items = scope_activities[scope_sel][activity_sel][sub_activity_sel]
            if items is not None:
                specific_item_sel = st.selectbox("Select Specific Item", items)

        # Quantity Input
        unit_sel = None
        if scope_sel != "Scope 3":
            unit_sel = units_dict.get(sub_activity_sel, "")
        else:
            if sub_activity_sel in ["Air Travel"]:
                unit_sel = "Number of flights"
            elif sub_activity_sel in ["Train Travel","Taxi / Cab / Auto","Two-Wheelers","Cars / Vans","Public Transport","Incoming Goods Transport","Third-party Logistics","Delivery to Customers","Retail / Distributor Transport"]:
                unit_sel = "km traveled"
            else:
                unit_sel = "kg / Tonnes"

        quantity_sel = st.number_input(f"Enter Quantity ({unit_sel})", min_value=0.0, format="%.2f")

        # Add Manual Entry
        if st.button("Add Manual Entry"):
            new_entry = {
                "Scope": scope_sel,
                "Activity": activity_sel,
                "Sub-Activity": sub_activity_sel,
                "Specific Item": specific_item_sel if specific_item_sel else "",
                "Quantity": quantity_sel,
                "Unit": unit_sel
            }
            st.session_state.entries = pd.concat([st.session_state.entries, pd.DataFrame([new_entry])], ignore_index=True)
            st.success("Entry added successfully!")

        # Display Entries Table
        if not st.session_state.entries.empty:
            st.subheader("All Entries")
            display_df = st.session_state.entries.copy()
            display_df["Quantity"] = display_df["Quantity"].apply(lambda x: f"{x:,.2f}")
            st.dataframe(display_df)

        # Optional: Download CSV
        def convert_df(df):
            return df.to_csv(index=False).encode('utf-8')

        if not st.session_state.entries.empty:
            csv = convert_df(st.session_state.entries)
            st.download_button("Download All Entries as CSV", csv, "ghg_entries.csv", "text/csv")

# ---------------------------
# Render pages
# ---------------------------
if st.session_state.page == "Home":
    render_ghg_dashboard(include_data=False)  # Home shows only charts and KPIs
elif st.session_state.page == "GHG":
    render_ghg_dashboard(include_data=True)   # GHG page shows full dashboard with Indian SME GHG entry
else:
    st.subheader(f"{st.session_state.page} Section")
    st.info("This section is under development. Please select other pages from sidebar.")
