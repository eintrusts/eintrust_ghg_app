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
@media (min-width: 768px) { .sdg-card { width: 220px; display: inline-block; } }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Constants
# ---------------------------
months = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]
SCOPE_COLORS = {"Scope 1": "#81c784", "Scope 2": "#4db6ac", "Scope 3": "#aed581"}
ENERGY_COLORS = {"Fossil": "#f39c12", "Renewable": "#2ecc71"}
SDG_LIST = ["No Poverty","Zero Hunger","Good Health & Wellbeing","Quality Education","Gender Equality",
            "Clean Water & Sanitation","Affordable & Clean Energy","Decent Work & Economic Growth","Industry, Innovation & Infrastructure",
            "Reduced Inequalities","Sustainable Cities & Communities","Responsible Consumption & Production","Climate Action","Life Below Water",
            "Life on Land","Peace, Justice & Strong Institutions","Partnerships for the Goals"]
SDG_COLORS = ["#e5243b","#dda63a","#4c9f38","#c5192d","#ff3a21","#26bde2","#fcc30b","#a21942","#fd6925","#dd1367","#fd9d24",
              "#bf8b2e","#3f7e44","#0a97d9","#56c02b","#00689d","#19486a"]

calorific_values = {"Diesel":35.8,"Petrol":34.2,"LPG":46.1,"CNG":48,"Coal":24,"Biomass":15}
emission_factors = {"Diesel":2.68,"Petrol":2.31,"LPG":1.51,"CNG":2.02,"Coal":2.42,"Biomass":0.0,
                    "Electricity":0.82,"Solar":0.0,"Wind":0.0,"Purchased Green Energy":0.0,"Biogas":0.0}

# ---------------------------
# Session State Init
# ---------------------------
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "entries" not in st.session_state:
    st.session_state.entries = pd.DataFrame(columns=["Scope","Activity","Sub-Activity","Specific Item","Quantity","Unit"])
if "renewable_entries" not in st.session_state:
    st.session_state.renewable_entries = pd.DataFrame(columns=["Source","Location","Month","Energy_kWh","CO2e_kg","Type"])
if "sdg_engagement" not in st.session_state:
    st.session_state.sdg_engagement = {i:0 for i in range(1,18)}

# ---------------------------
# Sidebar
# ---------------------------
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
    st.image("https://github.com/eintrusts/eintrust_ghg_app/blob/main/EinTrust%20%20(2).png?raw=true", use_column_width=True)
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
    st.markdown("---")
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
# GHG Dashboard with Input Form
# ---------------------------
def render_ghg_dashboard():
    st.subheader("GHG Emissions Data Entry")

    # Form for manual entry
    scope = st.selectbox("Select Scope", ["Scope 1","Scope 2","Scope 3"])
    activity = st.text_input("Activity")
    sub_activity = st.text_input("Sub-Activity")
    specific_item = st.text_input("Specific Item (optional)")
    unit = st.text_input("Unit")
    quantity = st.number_input("Enter quantity", min_value=0.0, format="%.2f")

    if st.button("Add Manual Entry"):
        new_entry = {"Scope":scope,"Activity":activity,"Sub-Activity":sub_activity,
                     "Specific Item":specific_item,"Quantity":quantity,"Unit":unit}
        st.session_state.entries = pd.concat([st.session_state.entries, pd.DataFrame([new_entry])], ignore_index=True)
        st.success("Entry added successfully!")

    # File upload
    st.subheader("Optional: Upload CSV / Excel File")
    uploaded_file = st.file_uploader("Upload CSV/XLS/XLSX", type=["csv","xls","xlsx"])
    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".csv"):
                df_file = pd.read_csv(uploaded_file)
            else:
                df_file = pd.read_excel(uploaded_file)
            st.session_state.entries = pd.concat([st.session_state.entries, df_file], ignore_index=True)
            st.success("File uploaded successfully! Preview below.")
        except Exception as e:
            st.error(f"Error reading file: {e}")

    if not st.session_state.entries.empty:
        st.subheader("All Entries")
        st.dataframe(st.session_state.entries)
        csv = st.session_state.entries.to_csv(index=False).encode('utf-8')
        st.download_button("Download All Entries as CSV", csv, "ghg_entries.csv", "text/csv")

    # Chart
    if not st.session_state.entries.empty:
        df = st.session_state.entries.copy()
        if "Month" not in df.columns:
            df["Month"] = np.random.choice(months, len(df))
        df["Month"] = pd.Categorical(df["Month"], categories=months, ordered=True)
        monthly_trend = df.groupby(["Month","Scope"])["Quantity"].sum().reset_index()
        st.subheader("Monthly GHG Emissions")
        fig = px.bar(monthly_trend, x="Month", y="Quantity", color="Scope", barmode="stack", color_discrete_map=SCOPE_COLORS)
        st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# Energy Dashboard (Detailed)
# ---------------------------
def render_energy_dashboard():
    st.title("⚡ Energy & CO₂e Dashboard")
    df = st.session_state.entries.copy()

    if not df.empty:
        def compute_energy(row):
            fuel = row["Sub-Activity"]
            qty = row["Quantity"]
            if fuel == "Grid Electricity":
                energy_kwh = qty
            else:
                energy_kwh = (qty * calorific_values.get(fuel.split()[0],0))/3.6
            co2e = qty * emission_factors.get(fuel.split()[0],0)
            return pd.Series([energy_kwh, co2e])
        df[["Energy_kWh","CO2e_kg"]] = df.apply(compute_energy, axis=1)
        df["Type"] = "Fossil"
    else:
        df = pd.DataFrame(columns=["Location","Month","Energy_kWh","CO2e_kg","Type"])

    # Renewable inputs
    st.subheader("Add Renewable Energy (Annual)")
    num_entries = st.number_input("Number of renewable energy entries", min_value=1, max_value=5, value=1)
    renewable_list = []
    for i in range(int(num_entries)):
        col1,col2,col3 = st.columns([2,3,3])
        with col1:
            source = st.selectbox(f"Source {i+1}", ["Solar","Wind","Biogas","Purchased Green Energy"], key=f"src{i}")
        with col2:
            location = st.text_input(f"Location {i+1}", "", key=f"loc{i}")
        with col3:
            annual_energy = st.number_input(f"Annual Energy kWh {i+1}", min_value=0.0, key=f"annual_{i}")
        monthly_energy = annual_energy/12
        for m in months:
            renewable_list.append({"Source":source,"Location":location,"Month":m,"Energy_kWh":monthly_energy,
                                   "Type":"Renewable","CO2e_kg":monthly_energy*emission_factors.get(source,0)})
    renewable_df = pd.DataFrame(renewable_list)

    all_energy = pd.concat([df, renewable_df], ignore_index=True)
    all_energy["Month"] = pd.Categorical(all_energy["Month"], categories=months, ordered=True)

    total_energy = all_energy.groupby("Type")["Energy_kWh"].sum().to_dict()
    fossil_energy = total_energy.get("Fossil",0)
    renewable_energy = total_energy.get("Renewable",0)

    col1,col2,col3 = st.columns(3)
    col1.metric("Fossil Energy (kWh)", f"{fossil_energy:,.0f}")
    col2.metric("Renewable Energy (kWh)", f"{renewable_energy:,.0f}")
    col3.metric("Total Energy (kWh)", f"{fossil_energy+renewable_energy:,.0f}")

    if not all_energy.empty:
        monthly_trend = all_energy.groupby(["Month","Type"]).sum().reset_index()
        st.subheader("Monthly Energy Consumption")
        fig = px.bar(monthly_trend, x="Month", y="Energy_kWh", color="Type", barmode="stack", color_discrete_map=ENERGY_COLORS)
        st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# SDG Dashboard
# ---------------------------
def render_sdg_dashboard():
    st.title("🎯 SDG Dashboard")
    fossil, renewable = 0, 0
    if not st.session_state.entries.empty:
        fossil = st.session_state.entries["Quantity"].sum()
    if not st.session_state.renewable_entries.empty:
        renewable = st.session_state.renewable_entries["Energy_kWh"].sum()

    col1,col2 = st.columns(2)
    col1.metric("Total GHG Emissions (tCO₂e)", f"{fossil:,.0f}")
    col2.metric("Total Renewable Energy (kWh)", f"{renewable:,.0f}")

    st.subheader("Engagement with SDGs")
    idx=0
    for i,(sdg_name,sdg_color) in enumerate(zip(SDG_LIST,SDG_COLORS), start=1):
        col = st.columns(3)[idx%3]
        with col:
            engagement = st.slider(f"SDG {i}: {sdg_name}",0,100,st.session_state.sdg_engagement[i], key=f"sdg{i}")
            st.session_state.sdg_engagement[i]=engagement
            st.markdown(f"<div class='sdg-card' style='background-color:{sdg_color}'><div class='sdg-number'>SDG {i}</div><div class='sdg-name'>{sdg_name}</div><div class='sdg-percent'>Engagement: {engagement}%</div></div>", unsafe_allow_html=True)
        idx+=1

# ---------------------------
# Page Routing
# ---------------------------
if st.session_state.page=="Home":
    st.title("EinTrust Sustainability Dashboard")
    st.info("Welcome! Select a section from the sidebar.")
elif st.session_state.page=="GHG":
    render_ghg_dashboard()
elif st.session_state.page=="Energy":
    render_energy_dashboard()
elif st.session_state.page=="SDG":
    render_sdg_dashboard()
else:
    st.subheader(f"{st.session_state.page} section")
    st.info("This section is under development.")
