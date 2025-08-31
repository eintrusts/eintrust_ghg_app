import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ---------------------------
# Config & Dark Theme CSS
# ---------------------------
st.set_page_config(page_title="EinTrust Sustainability Dashboard", page_icon="🌍", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');

html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }
.stApp { background-color: #0d1117; color: #e6edf3; }

.kpi {
    background: linear-gradient(145deg, #12131a, #1a1b22);
    padding: 20px;
    border-radius: 12px;
    text-align: center;
    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    margin-bottom: 10px;
    min-height: 120px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    transition: transform 0.2s, box-shadow 0.2s;
}
.kpi:hover {
    transform: scale(1.05);
    box-shadow: 0 8px 20px rgba(0,0,0,0.6);
}
.kpi-value { font-size: 28px; font-weight: 700; color: #ffffff; margin-bottom: 5px; }
.kpi-unit { font-size: 16px; font-weight: 500; color: #cfd8dc; margin-bottom: 5px; }
.kpi-label { font-size: 14px; color: #cfd8dc; letter-spacing: 0.5px; }

.stDataFrame { color: #e6edf3; font-family: 'Roboto', sans-serif; }
.sidebar .stButton>button { background:#198754; color:white; margin-bottom:5px; width:100%; font-family: 'Roboto', sans-serif; }
.stSelectbox, .stNumberInput, .stFileUploader, .stDownloadButton { font-family: 'Roboto', sans-serif; }
</style>
""", unsafe_allow_html=True)

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
        if s: res = s + "," + res
    return ("-" if x < 0 else "") + res

# ---------------------------
# Sidebar & Navigation
# ---------------------------
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "entries" not in st.session_state:
    st.session_state.entries = pd.DataFrame(columns=["Scope","Activity","Sub-Activity","Specific Item","Quantity","Unit"])

with st.sidebar:
    st.image("https://github.com/eintrusts/eintrust_ghg_app/raw/main/EinTrust%20%20logo.png", use_container_width=True)
    st.markdown("---")
    
    if st.button("Home"):
        st.session_state.page = "Home"
    env_exp = st.expander("Environment", expanded=True)
    with env_exp:
        if st.button("GHG"): st.session_state.page = "GHG"
        if st.button("Energy"): st.session_state.page = "Energy"

# ---------------------------
# Scope Activities / Units
# ---------------------------
scope_activities = {
    "Scope 1": {"Stationary Combustion": {"Diesel Generator": "Generator running on diesel",
                                          "Petrol Generator": "Generator running on petrol"},
                "Mobile Combustion": {"Diesel Vehicle": "Truck/van running on diesel"}},
    "Scope 2": {"Electricity Consumption": {"Grid Electricity": "Electricity from grid"}},
    "Scope 3": {"Business Travel": {"Air Travel": None}}
}
units_dict = {"Diesel Generator": "Liters", "Petrol Generator": "Liters", "Diesel Vehicle": "Liters",
              "Grid Electricity": "kWh"}

# ---------------------------
# GHG Dashboard Functions
# ---------------------------
def calculate_kpis():
    df = st.session_state.entries
    summary = {"Scope 1":0.0,"Scope 2":0.0,"Scope 3":0.0,"Total Quantity":0.0,"Unit":"tCO₂e"}
    if not df.empty:
        for scope in ["Scope 1","Scope 2","Scope 3"]:
            summary[scope] = df[df["Scope"]==scope]["Quantity"].sum()
        summary["Total Quantity"] = df["Quantity"].sum()
    return summary

def render_ghg_kpis():
    kpis = calculate_kpis()
    SCOPE_COLORS = {"Scope 1":"#81c784","Scope 2":"#4db6ac","Scope 3":"#aed581"}
    c1,c2,c3,c4 = st.columns(4)
    for col,label,value,color in zip([c1,c2,c3,c4],
                                     ["Total Quantity","Scope 1","Scope 2","Scope 3"],
                                     [kpis['Total Quantity'], kpis['Scope 1'], kpis['Scope 2'], kpis['Scope 3']],
                                     ["#ffffff", SCOPE_COLORS['Scope 1'], SCOPE_COLORS['Scope 2'], SCOPE_COLORS['Scope 3']]):
        col.markdown(f"""
        <div class='kpi'>
            <div class='kpi-value' style='color:{color}'>{format_indian(value)}</div>
            <div class='kpi-unit'>{kpis['Unit']}</div>
            <div class='kpi-label'>{label.lower()}</div>
        </div>
        """, unsafe_allow_html=True)

def render_ghg_data_entry():
    st.subheader("Add activity data")
    scope = st.selectbox("Select scope", list(scope_activities.keys()))
    activity = st.selectbox("Select activity / category", list(scope_activities[scope].keys()))
    sub_options = scope_activities[scope][activity]
    if scope != "Scope 3":
        sub_activity = st.selectbox("Select sub-activity", list(sub_options.keys()))
        st.info(sub_options[sub_activity])
    else:
        sub_activity = st.selectbox("Select sub-category", list(sub_options.keys()))
    specific_item = None
    if scope=="Scope 3":
        items = scope_activities[scope][activity][sub_activity]
        if items is not None:
            specific_item = st.selectbox("Select specific item", items)
    unit = units_dict.get(sub_activity, "Number of flights" if sub_activity=="Air Travel" else "km / kg / tonnes")
    quantity = st.number_input(f"Enter quantity ({unit})", min_value=0.0, format="%.2f")
    if st.button("Add entry"):
        new_entry = {"Scope":scope,"Activity":activity,"Sub-Activity":sub_activity,
                     "Specific Item":specific_item if specific_item else "",
                     "Quantity":quantity,"Unit":unit}
        st.session_state.entries = pd.concat([st.session_state.entries,pd.DataFrame([new_entry])], ignore_index=True)
        st.success("Entry added successfully!")
        st.experimental_rerun()
    if not st.session_state.entries.empty:
        st.subheader("All entries")
        display_df = st.session_state.entries.copy()
        display_df["Quantity"] = display_df["Quantity"].apply(lambda x: format_indian(x))
        st.dataframe(display_df)
        csv = display_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download all entries as CSV", csv, "ghg_entries.csv", "text/csv")

# ---------------------------
# Energy Dashboard Functions
# ---------------------------
calorific_values = {"Diesel":35.8,"Petrol":34.2,"LPG":46.1,"CNG":48,"Coal":24,"Biomass":15}
emission_factors = {"Diesel":2.68,"Petrol":2.31,"LPG":1.51,"CNG":2.02,"Coal":2.42,"Biomass":0.0,
                    "Electricity":0.82,"Solar":0.0,"Wind":0.0,"Purchased Green Energy":0.0,"Biogas":0.0}
months = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]

def get_energy_df():
    # Scope 1 & 2 fossil energy from GHG entries
    if not st.session_state.entries.empty:
        df = st.session_state.entries.copy()
        scope1_2_data = df[df["Scope"].isin(["Scope 1","Scope 2"])].copy()
        if not scope1_2_data.empty:
            def compute_energy(row):
                fuel = row["Sub-Activity"]
                qty = row["Quantity"]
                if fuel=="Grid Electricity":
                    energy_kwh = qty
                else:
                    energy_kwh = (qty*calorific_values.get(fuel,0))/3.6
                co2e = qty*emission_factors.get(fuel,0)
                return pd.Series([energy_kwh, co2e])
            scope1_2_data[["Energy_kWh","CO2e_kg"]] = scope1_2_data.apply(compute_energy, axis=1)
            scope1_2_data["Type"]="Fossil"
    else:
        scope1_2_data = pd.DataFrame(columns=["Location","Month","Energy_kWh","CO2e_kg","Type","Sub-Activity"])
    return scope1_2_data

def render_energy_dashboard(top_only=False):
    st.subheader("Energy & CO₂e Overview")
    fossil_df = get_energy_df()
    renewable_df = st.session_state.get("renewable_df", pd.DataFrame())
    all_energy = pd.concat([fossil_df.rename(columns={"Sub-Activity":"Fuel"}), renewable_df], ignore_index=True) if not renewable_df.empty else fossil_df
    if all_energy.empty: st.info("No energy data yet."); return

    # Stacked bar Energy by type
    location_trend = all_energy.groupby(["Type"]).sum().reset_index()
    fig = px.bar(location_trend, x="Type", y="Energy_kWh", color="Type", text="Energy_kWh")
    st.plotly_chart(fig, use_container_width=True)

    if top_only: return

    # Add renewable energy entries
    st.subheader("Add Renewable Energy (Annual) per Location & Source")
    num_entries = st.number_input("Number of renewable energy entries", min_value=1,max_value=20,value=1)
    renewable_list=[]
    for i in range(int(num_entries)):
        col1,col2,col3 = st.columns([2,3,3])
        with col1: source=st.selectbox(f"Source {i+1}", ["Solar","Wind","Biogas","Purchased Green Energy"], key=f"src{i}")
        with col2: location=st.text_input(f"Location {i+1}", "", key=f"loc{i}")
        with col3: annual_energy=st.number_input(f"Annual Energy kWh {i+1}", min_value=0.0, key=f"annual_{i}")
        monthly_energy = annual_energy/12
        for m in months:
            renewable_list.append({"Source":source,"Location":location,"Month":m,
                                   "Energy_kWh":monthly_energy,"Type":"Renewable",
                                   "CO2e_kg":monthly_energy*emission_factors.get(source,0)})
    if renewable_list:
        st.session_state["renewable_df"] = pd.DataFrame(renewable_list)

# ---------------------------
# Render Pages
# ---------------------------
if st.session_state.page == "Home":
    st.title("🌍 EinTrust Dashboard — Overview")
    render_ghg_kpis()
    render_energy_dashboard(top_only=True)
elif st.session_state.page == "GHG":
    render_ghg_kpis()
    render_ghg_data_entry()
elif st.session_state.page == "Energy":
    render_energy_dashboard(top_only=False)
else:
    st.subheader(f"{st.session_state.page} section")
    st.info("This section is under development. Please select other pages from sidebar.")
