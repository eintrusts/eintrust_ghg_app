import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# ---------------------------
# Page Config & CSS
# ---------------------------
st.set_page_config(page_title="EinTrust Sustainability Dashboard", page_icon="🌍", layout="wide")

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }
.stApp { background-color: #0d1117; color: #e6edf3; }

.kpi { background: linear-gradient(145deg, #12131a, #1a1b22); padding: 20px; border-radius: 12px; text-align: center;
      box-shadow: 0 4px 12px rgba(0,0,0,0.5); margin-bottom: 10px; min-height: 120px;
      display: flex; flex-direction: column; justify-content: center; align-items: center;
      transition: transform 0.2s, box-shadow 0.2s; }
.kpi:hover { transform: scale(1.05); box-shadow: 0 8px 20px rgba(0,0,0,0.6); }
.kpi-value { font-size: 28px; font-weight: 700; color: #ffffff; margin-bottom: 5px; }
.kpi-unit { font-size: 16px; font-weight: 500; color: #cfd8dc; margin-bottom: 5px; }
.kpi-label { font-size: 14px; color: #cfd8dc; letter-spacing: 0.5px; }

.sdg-card { border-radius: 10px; padding: 15px; margin: 8px; display: inline-block; width: 100%; min-height: 110px; text-align: left; color: white; }
.sdg-number { font-weight: 700; font-size: 20px; }
.sdg-name { font-size: 16px; margin-bottom: 5px; }
.sdg-percent { font-size: 14px; }

@media (min-width: 768px) { .sdg-card { width: 220px; display: inline-block; } }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------
# Sidebar & Navigation
# ---------------------------
if "page" not in st.session_state:
    st.session_state.page = "Home"


def sidebar_button(label: str):
    """Render a sidebar button (keeps session_state.page)."""
    active = st.session_state.page == label
    if st.button(label, key=f"btn_{label}"):
        st.session_state.page = label
    # small CSS tweak for look (best-effort)
    st.markdown(
        f"""
    <style>
    div.stButton > button[key="btn_{label}"] {{
        all: unset; cursor: pointer; padding: 0.4rem; text-align: left; border-radius: 0.3rem; margin-bottom: 0.2rem;
        background-color: {'forestgreen' if active else '#12131a'}; color: {'white' if active else '#e6edf3'}; font-size: 16px;
    }}
    div.stButton > button[key="btn_{label}"]:hover {{
        background-color: {'forestgreen' if active else '#1a1b22'};
    }}
    </style>
    """,
        unsafe_allow_html=True,
    )


with st.sidebar:
    st.image(
        "https://github.com/eintrusts/eintrust_ghg_app/blob/main/EinTrust%20%20(2).png?raw=true",
        use_container_width=True,
    )
    st.markdown("---")
    sidebar_button("Home")

    env_exp = st.expander("Environment", expanded=True)
    with env_exp:
        sidebar_button("GHG")
        sidebar_button("Energy")
        sidebar_button("Water")
        sidebar_button("Waste")
        sidebar_button("Biodiversity")

    social_exp = st.expander("Social")
    with social_exp:
        sidebar_button("Employee")
        sidebar_button("Health & Safety")
        sidebar_button("CSR")

    gov_exp = st.expander("Governance")
    with gov_exp:
        sidebar_button("Board")
        sidebar_button("Policies")
        sidebar_button("Compliance")
        sidebar_button("Risk Management")

    sidebar_button("SDG")

    reports_exp = st.expander("Reports")
    with reports_exp:
        sidebar_button("BRSR")
        sidebar_button("GRI")
        sidebar_button("CDP")
        sidebar_button("TCFD")

    sidebar_button("Settings")
    sidebar_button("Log Out")

# ---------------------------
# Initialize Data
# ---------------------------
if "entries" not in st.session_state:
    st.session_state.entries = pd.DataFrame(
        columns=["Scope", "Activity", "Sub-Activity", "Specific Item", "Quantity", "Unit"]
    )
if "renewable_entries" not in st.session_state:
    st.session_state.renewable_entries = pd.DataFrame(
        columns=["Source", "Location", "Month", "Energy_kWh", "CO2e_kg", "Type"]
    )
if "sdg_engagement" not in st.session_state:
    st.session_state.sdg_engagement = {i: 0 for i in range(1, 18)}

# ---------------------------
# Constants
# ---------------------------
scope_activities = {
    "Scope 1": {
        "Stationary Combustion": {
            "Diesel Generator": "Generator running on diesel for electricity",
            "Petrol Generator": "Generator running on petrol for electricity",
            "LPG Boiler": "Boiler or stove using LPG",
            "Coal Boiler": "Boiler/furnace burning coal",
            "Biomass Furnace": "Furnace burning wood/agricultural residue",
        },
        "Mobile Combustion": {
            "Diesel Vehicle": "Truck/van running on diesel",
            "Petrol Car": "Car/van running on petrol",
            "CNG Vehicle": "Bus or delivery vehicle running on CNG",
            "Diesel Forklift": "Forklift running on diesel",
            "Petrol Two-Wheeler": "Scooter or bike running on petrol",
        },
        "Process Emissions": {
            "Cement Production": "CO₂ from cement making",
            "Steel Production": "CO₂ from steel processing",
            "Brick Kiln": "CO₂ from brick firing",
            "Textile Processing": "Emissions from dyeing/fabric processing",
            "Chemical Manufacturing": "Emissions from chemical reactions",
            "Food Processing": "Emissions from cooking/heating",
        },
        "Fugitive Emissions": {
            "Refrigerant (HFC/HCFC)": "Gas leak from AC/refrigerator",
            "Methane (CH₄)": "Methane leaks from storage/pipelines",
            "SF₆": "Gas leak from electrical equipment",
        },
    },
    "Scope 2": {
        "Electricity Consumption": {
            "Grid Electricity": "Electricity bought from grid",
            "Diesel Generator Electricity": "Electricity generated on-site with diesel",
        },
        "Steam / Heat": {"Purchased Steam": "Steam bought from external supplier"},
        "Cooling / Chilled Water": {"Purchased Cooling": "Cooling bought from supplier"},
    },
    "Scope 3": {
        "Purchased Goods & Services": {
            "Raw Materials": ["Cement", "Steel", "Chemicals", "Textile"],
            "Packaging Materials": ["Cardboard", "Plastics", "Glass"],
            "Office Supplies": ["Paper", "Ink", "Stationery"],
            "Purchased Services": ["Printing", "Logistics", "Cleaning", "IT"],
        },
        "Business Travel": {"Air Travel": None, "Train Travel": None, "Taxi / Cab / Auto": None},
        "Employee Commuting": {"Two-Wheelers": None, "Cars / Vans": None, "Public Transport": None},
        "Waste Generated": {"Landfill": None, "Recycling": None, "Composting / Biogas": None},
        "Upstream Transportation & Distribution": {"Incoming Goods Transport": None, "Third-party Logistics": None},
        "Downstream Transportation & Distribution": {"Delivery to Customers": None, "Retail / Distributor Transport": None},
        "Use of Sold Products": {"Product Use": None},
        "End-of-Life Treatment": {"Recycling / Landfill": None},
    },
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
    "Purchased Cooling": "kWh",
}

months = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
ENERGY_COLORS = {"Fossil": "#f39c12", "Renewable": "#2ecc71"}
SDG_LIST = [
    "No Poverty",
    "Zero Hunger",
    "Good Health & Wellbeing",
    "Quality Education",
    "Gender Equality",
    "Clean Water & Sanitation",
    "Affordable & Clean Energy",
    "Decent Work & Economic Growth",
    "Industry, Innovation & Infrastructure",
    "Reduced Inequalities",
    "Sustainable Cities & Communities",
    "Responsible Consumption & Production",
    "Climate Action",
    "Life Below Water",
    "Life on Land",
    "Peace, Justice & Strong Institutions",
    "Partnerships for the Goals",
]
SDG_COLORS = [
    "#e5243b",
    "#dda63a",
    "#4c9f38",
    "#c5192d",
    "#ff3a21",
    "#26bde2",
    "#fcc30b",
    "#a21942",
    "#fd6925",
    "#dd1367",
    "#fd9d24",
    "#bf8b2e",
    "#3f7e44",
    "#0a97d9",
    "#56c02b",
    "#00689d",
    "#19486a",
]

# ---------------------------
# Helper: GHG KPIs
# ---------------------------
def calculate_ghg_kpis(entries_df: pd.DataFrame):
    """Return dict with Total, Scope1, Scope2, Scope3 sums based on Quantity column.
    If Quantity isn't numeric, attempt to coerce; treat NaN as 0."""
    df = entries_df.copy()
    if "Quantity" not in df.columns:
        return {"Total Emissions": 0.0, "Scope 1": 0.0, "Scope 2": 0.0, "Scope 3": 0.0}
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0.0)
    s1 = df.loc[df["Scope"] == "Scope 1", "Quantity"].sum()
    s2 = df.loc[df["Scope"] == "Scope 2", "Quantity"].sum()
    s3 = df.loc[df["Scope"] == "Scope 3", "Quantity"].sum()
    total = s1 + s2 + s3
    return {"Total Emissions": total, "Scope 1": s1, "Scope 2": s2, "Scope 3": s3}


def _render_kpi_cards(kpis: dict):
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(
        f"<div class='kpi'><div class='kpi-value'>{kpis['Total Emissions']:,}</div>"
        f"<div class='kpi-unit'>tCO₂e</div><div class='kpi-label'>Total Emissions</div></div>",
        unsafe_allow_html=True,
    )
    c2.markdown(
        f"<div class='kpi'><div class='kpi-value' style='color:#81c784'>{kpis['Scope 1']:,}</div>"
        f"<div class='kpi-unit'>tCO₂e</div><div class='kpi-label'>Scope 1</div></div>",
        unsafe_allow_html=True,
    )
    c3.markdown(
        f"<div class='kpi'><div class='kpi-value' style='color:#4db6ac'>{kpis['Scope 2']:,}</div>"
        f"<div class='kpi-unit'>tCO₂e</div><div class='kpi-label'>Scope 2</div></div>",
        unsafe_allow_html=True,
    )
    c4.markdown(
        f"<div class='kpi'><div class='kpi-value' style='color:#aed581'>{kpis['Scope 3']:,}</div>"
        f"<div class='kpi-unit'>tCO₂e</div><div class='kpi-label'>Scope 3</div></div>",
        unsafe_allow_html=True,
    )


# ---------------------------
# GHG Dashboard (Integrated Data Entry + Charts)
# ---------------------------
def render_ghg_dashboard(include_data: bool = True, show_chart: bool = True):
    st.subheader("GHG Emissions")

    # Show KPI cards (always)
    kpis = calculate_ghg_kpis(st.session_state.entries)
    _render_kpi_cards(kpis)

    # Chart: breakdown pie + monthly trend (if data exists)
    if show_chart and not st.session_state.entries.empty:
        df = st.session_state.entries.copy()
        df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0.0)
        # Pie
        pie_df = (
            df.groupby("Scope", sort=False)["Quantity"].sum().reindex(["Scope 1", "Scope 2", "Scope 3"]).fillna(0).reset_index()
        )
        st.subheader("📊 Emission Breakdown by Scope")
        fig_pie = px.pie(pie_df, names="Scope", values="Quantity", hole=0.45, template="plotly_dark")
        fig_pie.update_layout(paper_bgcolor="#0d1117", font_color="#e6edf3")
        st.plotly_chart(fig_pie, use_container_width=True)

        # Monthly trend (if Month column exists or we can simulate)
        st.subheader("📈 Monthly Emissions Trend (Apr → Mar)")
        if "Month" not in df.columns:
            # create a random-ish month assignment for visualization only
            df["Month"] = np.random.choice(months, len(df))
        df["Month"] = pd.Categorical(df["Month"], categories=months, ordered=True)
        stacked = df.groupby(["Month", "Scope"])["Quantity"].sum().reset_index()
        if not stacked.empty:
            fig_bar = px.bar(stacked, x="Month", y="Quantity", color="Scope", barmode="stack", template="plotly_dark")
            fig_bar.update_layout(paper_bgcolor="#0d1117", font_color="#e6edf3", xaxis_title="", yaxis_title="tCO₂e")
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No monthly data available for trend chart.")

    # Data entry form (only when include_data=True)
    if include_data:
        st.markdown("---")
        st.subheader("➕ Add / Import GHG Entries")

        with st.form("ghg_manual_form", clear_on_submit=False):
            col1, col2 = st.columns(2)
            with col1:
                scope = st.selectbox("Scope", ["Scope 1", "Scope 2", "Scope 3"])
                activity = st.selectbox("Activity / Category", list(scope_activities[scope].keys()))
            with col2:
                sub_options = scope_activities[scope][activity]
                if scope != "Scope 3":
                    sub_activity = st.selectbox("Sub-Activity", list(sub_options.keys()))
                    st.info(sub_options[sub_activity])
                else:
                    sub_activity = st.selectbox("Sub-Category", list(sub_options.keys()))

                specific_item = ""
                if scope == "Scope 3":
                    items = scope_activities[scope][activity][sub_activity]
                    if items is not None:
                        specific_item = st.selectbox("Specific Item", items)

            # determine unit
            if scope != "Scope 3":
                unit = units_dict.get(sub_activity, "")
            else:
                if sub_activity in ["Air Travel"]:
                    unit = "Number of flights"
                elif sub_activity in [
                    "Train Travel",
                    "Taxi / Cab / Auto",
                    "Two-Wheelers",
                    "Cars / Vans",
                    "Public Transport",
                    "Incoming Goods Transport",
                    "Third-party Logistics",
                    "Delivery to Customers",
                    "Retail / Distributor Transport",
                ]:
                    unit = "km traveled"
                else:
                    unit = "kg / Tonnes"

            quantity = st.number_input(f"Quantity ({unit})", min_value=0.0, format="%.2f", value=0.0)
            submitted = st.form_submit_button("Add Manual Entry")
            if submitted:
                new_entry = {
                    "Scope": scope,
                    "Activity": activity,
                    "Sub-Activity": sub_activity,
                    "Specific Item": specific_item if specific_item else "",
                    "Quantity": float(quantity),
                    "Unit": unit,
                }
                st.session_state.entries = pd.concat(
                    [st.session_state.entries, pd.DataFrame([new_entry])], ignore_index=True
                )
                st.success("Entry added successfully!")
                st.experimental_rerun()

        st.markdown("**Or** upload a CSV/Excel file with columns matching the entries table (Scope, Activity, Sub-Activity, Specific Item, Quantity, Unit).")
        uploaded_file = st.file_uploader("Upload CSV/XLS/XLSX", type=["csv", "xls", "xlsx"])
        if uploaded_file:
            try:
                if uploaded_file.name.lower().endswith(".csv"):
                    df_file = pd.read_csv(uploaded_file)
                else:
                    df_file = pd.read_excel(uploaded_file)
                # ensure columns exist and Quantity is numeric
                if "Quantity" in df_file.columns:
                    df_file["Quantity"] = pd.to_numeric(df_file["Quantity"], errors="coerce").fillna(0.0)
                st.session_state.entries = pd.concat([st.session_state.entries, df_file], ignore_index=True)
                st.success("File uploaded and appended to entries.")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Could not read uploaded file: {e}")

    # Display entries table
    if not st.session_state.entries.empty:
        st.markdown("---")
        st.subheader("📜 All GHG Entries")
        display_df = st.session_state.entries.copy()
        display_df["Quantity"] = pd.to_numeric(display_df["Quantity"], errors="coerce").fillna(0.0)
        st.dataframe(display_df, use_container_width=True)
        csv = display_df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download GHG Entries (CSV)", csv, "ghg_entries.csv", "text/csv")
    else:
        st.info("No GHG entries yet. Add entries using the form or upload a file.")

# ---------------------------
# Energy Dashboard
# ---------------------------
def render_energy_dashboard(include_input: bool = True, show_chart: bool = True):
    st.subheader("Energy")
    df = st.session_state.entries.copy()
    # calorific & emission factor lookups (example)
    calorific_values = {"Diesel": 35.8, "Petrol": 34.2, "LPG": 46.1, "CNG": 48, "Coal": 24, "Biomass": 15}
    emission_factors = {
        "Diesel": 2.68,
        "Petrol": 2.31,
        "LPG": 1.51,
        "CNG": 2.02,
        "Coal": 2.42,
        "Biomass": 0.0,
        "Electricity": 0.82,
        "Solar": 0.0,
        "Wind": 0.0,
        "Purchased Green Energy": 0.0,
        "Biogas": 0.0,
    }

    scope1_2_data = df[df["Scope"].isin(["Scope 1", "Scope 2"])].copy()
    if not scope1_2_data.empty:
        # ensure numeric
        scope1_2_data["Quantity"] = pd.to_numeric(scope1_2_data["Quantity"], errors="coerce").fillna(0.0)

        def compute_energy(row):
            fuel = row["Sub-Activity"]
            qty = row["Quantity"]
            if str(fuel).lower() in ["grid electricity", "grid"]:
                energy_kwh = qty
            else:
                energy_kwh = (qty * calorific_values.get(fuel, 0)) / 3.6
            co2e = qty * emission_factors.get(fuel, 0)
            return pd.Series([energy_kwh, co2e])

        scope1_2_data[["Energy_kWh", "CO2e_kg"]] = scope1_2_data.apply(compute_energy, axis=1)
        scope1_2_data["Type"] = "Fossil"
        if "Month" not in scope1_2_data.columns:
            scope1_2_data["Month"] = np.random.choice(months, len(scope1_2_data))

    all_energy = (
        pd.concat([scope1_2_data.rename(columns={"Sub-Activity": "Fuel"}), st.session_state.renewable_entries], ignore_index=True)
        if not st.session_state.renewable_entries.empty
        else scope1_2_data
    )

    total_energy = all_energy.groupby("Type")["Energy_kWh"].sum().to_dict() if not all_energy.empty else {}
    fossil_energy = total_energy.get("Fossil", 0)
    renewable_energy = total_energy.get("Renewable", 0)
    total_sum = fossil_energy + renewable_energy

    c1, c2, c3 = st.columns(3)
    for col, label, value, color in zip(
        [c1, c2, c3],
        ["Total Energy (kWh)", "Fossil Energy (kWh)", "Renewable Energy (kWh)"],
        [total_sum, fossil_energy, renewable_energy],
        ["#ffffff", ENERGY_COLORS["Fossil"], ENERGY_COLORS["Renewable"]],
    ):
        col.markdown(
            f"<div class='kpi'><div class='kpi-value' style='color:{color}'>{int(value):,}</div>"
            f"<div class='kpi-unit'>kWh</div><div class='kpi-label'>{label.lower()}</div></div>",
            unsafe_allow_html=True,
        )

    if show_chart and not all_energy.empty:
        all_energy["Month"] = pd.Categorical(all_energy.get("Month", months[0]), categories=months, ordered=True)
        monthly_trend = all_energy.groupby(["Month", "Type"])["Energy_kWh"].sum().reset_index()
        st.subheader("Monthly Energy Consumption (kWh)")
        fig = px.bar(monthly_trend, x="Month", y="Energy_kWh", color="Type", barmode="stack", color_discrete_map=ENERGY_COLORS)
        st.plotly_chart(fig, use_container_width=True)

    if include_input:
        st.subheader("Add Renewable Energy Entry")
        num_entries = st.number_input("Number of renewable energy entries", min_value=1, max_value=10, value=1)
        renewable_list = []
        for i in range(int(num_entries)):
            col1, col2, col3 = st.columns([2, 3, 3])
            with col1:
                source = st.selectbox(f"Source {i+1}", ["Solar", "Wind", "Biogas", "Purchased Green Energy"], key=f"src{i}")
            with col2:
                location = st.text_input(f"Location {i+1}", "", key=f"loc{i}")
            with col3:
                annual_energy = st.number_input(f"Annual Energy kWh {i+1}", min_value=0.0, key=f"annual_{i}")
            monthly_energy = annual_energy / 12 if annual_energy else 0.0
            for m in months:
                renewable_list.append(
                    {
                        "Source": source,
                        "Location": location,
                        "Month": m,
                        "Energy_kWh": monthly_energy,
                        "Type": "Renewable",
                        "CO2e_kg": monthly_energy * emission_factors.get(source, 0),
                    }
                )
        if renewable_list and st.button("Add Renewable Energy Entries"):
            new_entries_df = pd.DataFrame(renewable_list)
            st.session_state.renewable_entries = pd.concat([st.session_state.renewable_entries, new_entries_df], ignore_index=True)
            st.success(f"{len(new_entries_df)} entries added!")
            st.experimental_rerun()

# ---------------------------
# SDG Dashboard (NO SLIDERS)
# ---------------------------
def render_sdg_dashboard():
    st.title("Sustainable Development Goals (SDGs)")
    st.subheader("Company Engagement by SDG (edit % using number inputs)")

    num_cols = 4
    rows = (len(SDG_LIST) + num_cols - 1) // num_cols
    idx = 0
    for _ in range(rows):
        cols = st.columns(num_cols)
        for c in range(num_cols):
            if idx >= len(SDG_LIST):
                break
            sdg_name = SDG_LIST[idx]
            sdg_color = SDG_COLORS[idx]
            sdg_number = idx + 1
            # use number_input instead of slider
            val = st.session_state.sdg_engagement.get(sdg_number, 0)
            new_val = cols[c].number_input(f"SDG {sdg_number} %", min_value=0, max_value=100, value=val, key=f"sdg_input_{sdg_number}")
            st.session_state.sdg_engagement[sdg_number] = int(new_val)
            cols[c].markdown(
                f"<div class='sdg-card' style='background-color:{sdg_color}'>"
                f"<div class='sdg-number'>SDG {sdg_number}</div>"
                f"<div class='sdg-name'>{sdg_name}</div>"
                f"<div class='sdg-percent'>Engagement: {int(new_val)}%</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
            idx += 1

# ---------------------------
# Render Pages
# ---------------------------
st.title("EinTrust Sustainability Dashboard")

if st.session_state.page == "Home":
    # On Home show KPI summary and compact charts (no entry forms)
    render_ghg_dashboard(include_data=False, show_chart=True)
    st.markdown("---")
    render_energy_dashboard(include_input=False, show_chart=False)

elif st.session_state.page == "GHG":
    render_ghg_dashboard(include_data=True, show_chart=True)

elif st.session_state.page == "Energy":
    render_energy_dashboard(include_input=True, show_chart=True)

elif st.session_state.page == "SDG":
    render_sdg_dashboard()

else:
    st.subheader(f"{st.session_state.page} section")
    st.info("This section is under development. Please select other pages from sidebar.")
