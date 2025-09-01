import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ---------------------------
# Page Config & CSS
# ---------------------------
st.set_page_config(page_title="EinTrust Sustainability Dashboard", page_icon="🌍", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }
.stApp { background-color: #0d1117; color: #e6edf3; }
.kpi { background: linear-gradient(145deg, #12131a, #1a1b22); padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.5); margin-bottom: 10px; min-height: 120px; display: flex; flex-direction: column; justify-content: center; align-items: center; transition: transform 0.2s, box-shadow 0.2s; }
.kpi:hover { transform: scale(1.05); box-shadow: 0 8px 20px rgba(0,0,0,0.6); }
.kpi-value { font-size: 28px; font-weight: 700; color: #ffffff; margin-bottom: 5px; }
.kpi-unit { font-size: 16px; font-weight: 500; color: #cfd8dc; margin-bottom: 5px; }
.kpi-label { font-size: 14px; color: #cfd8dc; letter-spacing: 0.5px; }
.sdg-card { border-radius: 10px; padding: 15px; margin: 8px; display: inline-block; width: 100%; min-height: 110px; text-align: left; color: white; }
.sdg-number { font-weight: 700; font-size: 20px; }
.sdg-name { font-size: 16px; margin-bottom: 5px; }
.sdg-percent { font-size: 14px; }
.sidebar-logo { width: 150px; }
.expander-scroll { max-height: 300px; overflow-y: auto; }
@media (min-width: 768px) { .sdg-card { width: 220px; display: inline-block; } }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Utilities
# ---------------------------
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
    return ("-" if x < 0 else "") + res

# ---------------------------
# Sidebar & Navigation
# ---------------------------
if "page" not in st.session_state:
    st.session_state.page = "Home"

def sidebar_button(label):
    active = st.session_state.page == label
    if st.button(label, key=label):
        st.session_state.page = label
    st.markdown(f"""
    <style>
    div.stButton > button[key="{label}"] {{
        all: unset; cursor: pointer; padding: 0.4rem; text-align: left; border-radius: 0.3rem; margin-bottom: 0.2rem;
        background-color: {'forestgreen' if active else '#12131a'}; color: {'white' if active else '#e6edf3'}; font-size: 16px;
    }}
    div.stButton > button[key="{label}"]:hover {{
        background-color: {'forestgreen' if active else '#1a1b22'};
    }}
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.image("https://github.com/eintrusts/eintrust_ghg_app/blob/main/EinTrust%20%20(2).png?raw=true", width=150)
    st.markdown("---")
    
    sidebar_button("Home")

    env_exp = st.expander("Environment", expanded=True)
    with env_exp:
        st.markdown('<div class="expander-scroll">', unsafe_allow_html=True)
        sidebar_button("GHG")
        sidebar_button("Energy")
        sidebar_button("Water")
        sidebar_button("Waste")
        sidebar_button("Biodiversity")
        st.markdown('</div>', unsafe_allow_html=True)

    social_exp = st.expander("Social")
    with social_exp:
        st.markdown('<div class="expander-scroll">', unsafe_allow_html=True)
        sidebar_button("Employee")
        sidebar_button("Health & Safety")
        sidebar_button("CSR")
        st.markdown('</div>', unsafe_allow_html=True)

    gov_exp = st.expander("Governance")
    with gov_exp:
        st.markdown('<div class="expander-scroll">', unsafe_allow_html=True)
        sidebar_button("Board")
        sidebar_button("Policies")
        sidebar_button("Compliance")
        sidebar_button("Risk Management")
        st.markdown('</div>', unsafe_allow_html=True)

    sidebar_button("SDG")

    reports_exp = st.expander("Reports")
    with reports_exp:
        st.markdown('<div class="expander-scroll">', unsafe_allow_html=True)
        sidebar_button("BRSR")
        sidebar_button("GRI")
        sidebar_button("CDP")
        sidebar_button("TCFD")
        st.markdown('</div>', unsafe_allow_html=True)

    sidebar_button("Settings")
    sidebar_button("Log Out")

# ---------------------------
# Initialize Data
# ---------------------------
if "entries" not in st.session_state:
    st.session_state.entries = pd.DataFrame(columns=["Scope","Activity","Sub-Activity","Specific Item","Quantity","Unit"])
if "renewable_entries" not in st.session_state:
    st.session_state.renewable_entries = pd.DataFrame(columns=["Source","Location","Month","Energy_kWh","CO2e_kg","Type"])
if "sdg_engagement" not in st.session_state:
    st.session_state.sdg_engagement = {i:0 for i in range(1,18)}

# ---------------------------
# Constants
# ---------------------------
scope_activities = {
    "Scope 1": {"Stationary Combustion": {"Diesel Generator":"Generator running on diesel","Petrol Generator":"Generator running on petrol"},
                "Mobile Combustion":{"Diesel Vehicle":"Truck/van running on diesel"}},
    "Scope 2": {"Electricity Consumption":{"Grid Electricity":"Electricity from grid"}},
    "Scope 3": {"Business Travel":{"Air Travel": None}}
}
units_dict = {"Diesel Generator": "Liters", "Petrol Generator": "Liters", "Diesel Vehicle": "Liters", "Grid Electricity": "kWh", "Air Travel":"km"}
months = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]
SCOPE_COLORS = {"Scope 1": "#81c784", "Scope 2": "#4db6ac", "Scope 3": "#aed581"}
ENERGY_COLORS = {"Fossil": "#f39c12", "Renewable": "#2ecc71"}
SDG_LIST = ["No Poverty","Zero Hunger","Good Health & Wellbeing","Quality Education","Gender Equality",
            "Clean Water & Sanitation","Affordable & Clean Energy","Decent Work & Economic Growth","Industry, Innovation & Infrastructure",
            "Reduced Inequalities","Sustainable Cities & Communities","Responsible Consumption & Production","Climate Action","Life Below Water",
            "Life on Land","Peace, Justice & Strong Institutions","Partnerships for the Goals"]
SDG_COLORS = ["#e5243b","#dda63a","#4c9f38","#c5192d","#ff3a21","#26bde2","#fcc30b","#a21942","#fd6925","#dd1367","#fd9d24",
              "#bf8b2e","#3f7e44","#0a97d9","#56c02b","#00689d","#19486a"]

# Emission factors (kg CO2e per unit)
emission_factors = {
    "Diesel Generator": 2.68,
    "Petrol Generator": 2.31,
    "Diesel Vehicle": 2.68,
    "Grid Electricity": 0.82,
    "Air Travel": 0.25
}

# ---------------------------
# GHG Dashboard
# ---------------------------
def calculate_kpis():
    df = st.session_state.entries
    summary = {"Scope 1":0.0,"Scope 2":0.0,"Scope 3":0.0,"Total Quantity":0.0,"Unit":"tCO₂e"}
    if not df.empty:
        df["CO2e_kg"] = df.apply(lambda row: row["Quantity"] * emission_factors.get(row["Sub-Activity"],0), axis=1)
        for scope in ["Scope 1","Scope 2","Scope 3"]:
            summary[scope] = df[df["Scope"]==scope]["CO2e_kg"].sum()/1000  # tCO2e
        summary["Total Quantity"] = df["CO2e_kg"].sum()/1000
    return summary

def render_ghg_dashboard(include_data=True, show_chart=True):
    st.subheader("GHG Emissions")
    kpis = calculate_kpis()
    c1,c2,c3,c4 = st.columns(4)
    for col,label,value,color in zip([c1,c2,c3,c4], ["Total Quantity","Scope 1","Scope 2","Scope 3"],
                                    [kpis['Total Quantity'],kpis['Scope 1'],kpis['Scope 2'],kpis['Scope 3']],
                                    ["#ffffff",SCOPE_COLORS['Scope 1'],SCOPE_COLORS['Scope 2'],SCOPE_COLORS['Scope 3']]):
        col.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{color}'>{format_indian(value)}</div><div class='kpi-unit'>{kpis['Unit']}</div><div class='kpi-label'>{label.lower()}</div></div>", unsafe_allow_html=True)

    if show_chart and not st.session_state.entries.empty:
        df = st.session_state.entries.copy()
        df["CO2e_kg"] = df.apply(lambda row: row["Quantity"] * emission_factors.get(row["Sub-Activity"],0), axis=1)
        if "Month" not in df.columns:
            df["Month"] = np.random.choice(months, len(df))
        df["Month"] = pd.Categorical(df["Month"], categories=months, ordered=True)
        monthly_trend = df.groupby(["Month","Scope"])["CO2e_kg"].sum().reset_index()
        st.subheader("Monthly GHG Emissions (tCO₂e)")
        fig = px.bar(monthly_trend, x="Month", y="CO2e_kg", color="Scope", barmode="stack", color_discrete_map=SCOPE_COLORS)
        st.plotly_chart(fig, use_container_width=True)

    # --- Data Entry Form ---
    if include_data:
        scope = st.selectbox("Select Scope", list(scope_activities.keys()))
        activity = st.selectbox("Select Activity", list(scope_activities[scope].keys()))
        sub_options = scope_activities[scope][activity]
        sub_activity = st.selectbox("Select Sub-Activity", list(sub_options.keys()))
        st.info(sub_options[sub_activity])
        unit = units_dict.get(sub_activity, "Number")
        quantity = st.number_input(f"Enter quantity ({unit})", min_value=0.0, format="%.2f")
        if st.button("Add Entry"):
            new_entry = {"Scope":scope,"Activity":activity,"Sub-Activity":sub_activity,"Specific Item":"",
                         "Quantity":quantity,"Unit":unit}
            st.session_state.entries = pd.concat([st.session_state.entries, pd.DataFrame([new_entry])], ignore_index=True)
            st.success("GHG entry added!")
            st.experimental_rerun()

    if not st.session_state.entries.empty:
        st.subheader("All entries")
        display_df = st.session_state.entries.copy()
        display_df["CO2e_kg"] = display_df.apply(lambda row: row["Quantity"] * emission_factors.get(row["Sub-Activity"],0), axis=1)
        display_df["Quantity"] = display_df["CO2e_kg"]/1000  # tCO2e
        display_df["Quantity"] = display_df["Quantity"].apply(lambda x: format_indian(x))
        st.dataframe(display_df[["Scope","Activity","Sub-Activity","Quantity","Unit"]])
        csv = display_df[["Scope","Activity","Sub-Activity","Quantity","Unit"]].to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", csv, "ghg_entries.csv", "text/csv")

# ---------------------------
# Energy Dashboard (unchanged)
# ---------------------------
def render_energy_dashboard(include_input=True, show_chart=True):
    st.subheader("Energy")
    df = st.session_state.entries.copy()
    
    calorific_values = {"Diesel":35.8,"Petrol":34.2,"LPG":46.1,"CNG":48,"Coal":24,"Biomass":15}
    emission_factors_energy = {"Diesel":2.68,"Petrol":2.31,"LPG":1.51,"CNG":2.02,"Coal":2.42,"Biomass":0.0,
                               "Electricity":0.82,"Solar":0.0,"Wind":0.0,"Purchased Green Energy":0.0,"Biogas":0.0}
    
    scope1_2_data = df[df["Scope"].isin(["Scope 1","Scope 2"])].copy()
    
    if not scope1_2_data.empty:
        def compute_energy(row):
            fuel = row["Sub-Activity"]
            qty = row["Quantity"]
            energy_kwh = qty if fuel=="Grid Electricity" else (qty*calorific_values.get(fuel,0))/3.6
            co2e = qty * emission_factors_energy.get(fuel,0)
            return pd.Series([energy_kwh, co2e])
        scope1_2_data[["Energy_kWh","CO2e_kg"]] = scope1_2_data.apply(compute_energy, axis=1)
        scope1_2_data["Type"]="Fossil"
        scope1_2_data["Month"] = np.random.choice(months, len(scope1_2_data))
    
    all_energy = pd.concat([scope1_2_data.rename(columns={"Sub-Activity":"Fuel"}), st.session_state.renewable_entries], ignore_index=True) if not st.session_state.renewable_entries.empty else scope1_2_data
    
    total_energy = all_energy.groupby("Type")["Energy_kWh"].sum().to_dict() if not all_energy.empty else {}
    fossil_energy = total_energy.get("Fossil",0)
    renewable_energy = total_energy.get("Renewable",0)
    total_sum = fossil_energy + renewable_energy
    
    c1,c2,c3 = st.columns(3)
    for col,label,value,color in zip([c1,c2,c3],
                                     ["Total Energy (kWh)","Fossil Energy (kWh)","Renewable Energy (kWh)"],
                                     [total_sum,fossil_energy,renewable_energy],
                                     ["#ffffff",ENERGY_COLORS["Fossil"],ENERGY_COLORS["Renewable"]]):
        col.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{color}'>{int(value):,}</div><div class='kpi-unit'>kWh</div><div class='kpi-label'>{label.lower()}</div></div>", unsafe_allow_html=True)
    
    if show_chart and not all_energy.empty:
        all_energy["Month"] = pd.Categorical(all_energy.get("Month", months[0]), categories=months, ordered=True)
        monthly_trend = all_energy.groupby(["Month","Type"])["Energy_kWh"].sum().reset_index()
        st.subheader("Monthly Energy Consumption (kWh)")
        fig = px.bar(monthly_trend, x="Month", y="Energy_KWh", color="Type", barmode="stack", color_discrete_map=ENERGY_COLORS)
        st.plotly_chart(fig, use_container_width=True)
    
    if include_input:
        st.subheader("Add Renewable Energy Entry")
        num_entries = st.number_input("Number of renewable energy entries", min_value=1, max_value=10, value=1)
        renewable_list = []
        for i in range(int(num_entries)):
            col1,col2,col3 = st.columns([2,3,3])
            with col1:
                source = st.selectbox(f"Source {i+1}", ["Solar","Wind","Biogas","Purchased Green Energy"], key=f"src{i}")
            with col2:
                location = st.text_input(f"Location {i+1}", "", key=f"loc{i}")
            with col3:
                annual_energy = st.number_input(f"Annual Energy kWh {i+1}", min_value=0.0, key=f"annual_{i}")
            monthly_energy = annual_energy / 12
            for m in months:
                renewable_list.append({"Source":source,"Location":location,"Month":m,"Energy_kWh":monthly_energy,"Type":"Renewable","CO2e_kg":monthly_energy*emission_factors_energy.get(source,0)})
        if renewable_list and st.button("Add Renewable Energy Entries"):
            new_entries_df = pd.DataFrame(renewable_list)
            st.session_state.renewable_entries = pd.concat([st.session_state.renewable_entries, new_entries_df], ignore_index=True)
            st.success(f"{len(new_entries_df)} entries added!")
            st.experimental_rerun()

# ---------------------------
# SDG Dashboard (unchanged)
# ---------------------------
def render_sdg_dashboard():
    st.title("Sustainable Development Goals (SDGs)")
    st.subheader("Company Engagement by SDG")
    num_cols = 4
    rows = (len(SDG_LIST)+num_cols-1)//num_cols
    idx=0
    for r in range(rows):
        cols = st.columns(num_cols)
        for c in range(num_cols):
            if idx>=len(SDG_LIST): break
            sdg_name = SDG_LIST[idx]
            sdg_color = SDG_COLORS[idx]
            sdg_number = idx+1
            engagement = st.session_state.sdg_engagement.get(sdg_number,0)
            engagement = cols[c].slider(f"Engagement % - SDG {sdg_number}",0,100,value=engagement,key=f"sdg{sdg_number}")
            st.session_state.sdg_engagement[sdg_number] = engagement
            cols[c].markdown(f"<div class='sdg-card' style='background-color:{sdg_color}'><div class='sdg-number'>SDG {sdg_number}</div><div class='sdg-name'>{sdg_name}</div><div class='sdg-percent'>Engagement: {engagement}%</div></div>", unsafe_allow_html=True)
            idx+=1

# ---------------------------
# Render Pages
# ---------------------------
if st.session_state.page=="Home":
    st.title("EinTrust Sustainability Dashboard")
    render_ghg_dashboard(include_data=False, show_chart=False)
    render_energy_dashboard(include_input=False, show_chart=False)
elif st.session_state.page=="GHG":
    render_ghg_dashboard(include_data=True, show_chart=True)
elif st.session_state.page=="Energy":
    render_energy_dashboard(include_input=True, show_chart=True)
elif st.session_state.page=="SDG":
    render_sdg_dashboard()
else:
    st.subheader(f"{st.session_state.page} section")
    st.info("This section is under development. Please select other pages from sidebar.")
