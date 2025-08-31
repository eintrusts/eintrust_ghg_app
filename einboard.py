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
.kpi { background: linear-gradient(145deg, #12131a, #1a1b22); padding: 20px; border-radius: 12px; text-align: center;
       box-shadow: 0 4px 12px rgba(0,0,0,0.5); margin-bottom: 10px; min-height: 120px;
       display: flex; flex-direction: column; justify-content: center; align-items: center;
       transition: transform 0.2s, box-shadow 0.2s; }
.kpi:hover { transform: scale(1.05); box-shadow: 0 8px 20px rgba(0,0,0,0.6); }
.kpi-value { font-size: 28px; font-weight: 700; color: #ffffff; margin-bottom: 5px; }
.kpi-unit { font-size: 16px; font-weight: 500; color: #cfd8dc; margin-bottom: 5px; }
.kpi-label { font-size: 14px; color: #cfd8dc; letter-spacing: 0.5px; }
.sdg-card { border-radius: 10px; padding: 15px; margin: 8px; display: inline-block; width: 100%;
            min-height: 110px; text-align: left; color: white; }
.sdg-number { font-weight: 700; font-size: 20px; }
.sdg-name { font-size: 16px; margin-bottom: 5px; }
.sdg-percent { font-size: 14px; }
@media (min-width: 768px) { .sdg-card { width: 220px; display: inline-block; } }
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
        if s:
            res = s + "," + res
    return ("-" if x < 0 else "") + res

months = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]

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
        all: unset; cursor: pointer; padding: 0.4rem; text-align: left;
        border-radius: 0.3rem; margin-bottom: 0.2rem;
        background-color: {'forestgreen' if active else '#12131a'};
        color: {'white' if active else '#e6edf3'};
        font-size: 16px;
    }}
    div.stButton > button[key="{label}"]:hover {{
        background-color: {'forestgreen' if active else '#1a1b22'};
    }}
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.image("https://github.com/eintrusts/eintrust_ghg_app/blob/main/EinTrust%20%20(2).png?raw=true", use_container_width=True)
    st.markdown("---")
    sidebar_button("Home")
    env_exp = st.expander("Environment", expanded=True)
    with env_exp:
        sidebar_button("GHG")
        sidebar_button("Energy")
        sidebar_button("Water")
    social_exp = st.expander("Social", expanded=False)
    with social_exp:
        sidebar_button("Employee")
        sidebar_button("Health & Safety")
        sidebar_button("CSR")
    gov_exp = st.expander("Governance", expanded=False)
    with gov_exp:
        sidebar_button("Board")
        sidebar_button("Policies")
        sidebar_button("Compliance")
        sidebar_button("Risk Management")
    st.markdown("---")
    sidebar_button("SDG")

# ---------------------------
# Initialize Data
# ---------------------------
if "ghg_entries" not in st.session_state:
    st.session_state.ghg_entries = pd.DataFrame(columns=["Scope","Activity","Sub-Activity","Specific Item","Quantity","Unit","Month"])
if "renewable_entries" not in st.session_state:
    st.session_state.renewable_entries = pd.DataFrame(columns=["Source","Location","Month","Energy_kWh","CO2e_kg","Type"])
if "water_entries" not in st.session_state:
    st.session_state.water_entries = pd.DataFrame(columns=["Freshwater_kL","Recycled_kL","Rainwater_kL","STP_ETP_kL","Month"])
if "sdg_engagement" not in st.session_state:
    st.session_state.sdg_engagement = {i:0 for i in range(1,18)}

# ---------------------------
# Constants
# ---------------------------
SCOPE_COLORS = {"Scope 1":"#81c784","Scope 2":"#4db6ac","Scope 3":"#aed581"}
ENERGY_COLORS = {"Fossil":"#f39c12","Renewable":"#2ecc71"}
SDG_LIST = [
    "No Poverty","Zero Hunger","Good Health & Wellbeing","Quality Education","Gender Equality",
    "Clean Water & Sanitation","Affordable & Clean Energy","Decent Work & Economic Growth",
    "Industry, Innovation & Infrastructure","Reduced Inequalities","Sustainable Cities & Communities",
    "Responsible Consumption & Production","Climate Action","Life Below Water","Life on Land",
    "Peace, Justice & Strong Institutions","Partnerships for the Goals"
]
SDG_COLORS = [
    "#e5243b","#dda63a","#4c9f38","#c5192d","#ff3a21","#26bde2","#fcc30b","#a21942","#fd6925",
    "#dd1367","#fd9d24","#bf8b2e","#3f7e44","#0a97d9","#56c02b","#00689d","#19486a"
]

# Fossil energy emission factors
EMISSION_FACTORS = {"Diesel":2.68,"Petrol":2.31,"LPG":1.51,"CNG":2.02,"Coal":2.42,"Biomass":0.0,"Electricity":0.82,"Solar":0.0,"Wind":0.0,"Purchased Green Energy":0.0,"Biogas":0.0}

# ---------------------------
# Functions for KPIs and automatic linking
# ---------------------------
def calculate_ghg_kpis():
    df = st.session_state.ghg_entries
    summary = {"Scope 1":0.0,"Scope 2":0.0,"Scope 3":0.0,"Total Quantity":0.0,"Unit":"tCO₂e"}
    if not df.empty:
        for scope in ["Scope 1","Scope 2","Scope 3"]:
            summary[scope] = df[df["Scope"]==scope]["Quantity"].sum()
        summary["Total Quantity"] = df["Quantity"].sum()
    return summary

def calculate_energy_kpis():
    # Fossil from GHG + renewable entries
    fossil_kwh = 0
    for idx,row in st.session_state.ghg_entries.iterrows():
        if row["Sub-Activity"] in ["Diesel Generator","Petrol Generator","Diesel Vehicle"]:
            fossil_kwh += row["Quantity"]*10  # Assume 1 unit = 10 kWh equivalent
    renewable_kwh = st.session_state.renewable_entries["Energy_kWh"].sum() if not st.session_state.renewable_entries.empty else 0
    return {"Fossil":fossil_kwh,"Renewable":renewable_kwh,"Total":fossil_kwh+renewable_kwh}

def calculate_water_kpis():
    df = st.session_state.water_entries
    summary = {"Freshwater":0.0,"Recycled":0.0,"Rainwater":0.0,"STP_ETP":0.0}
    if not df.empty:
        summary["Freshwater"] = df["Freshwater_kL"].sum()
        summary["Recycled"] = df["Recycled_kL"].sum()
        summary["Rainwater"] = df["Rainwater_kL"].sum()
        summary["STP_ETP"] = df["STP_ETP_kL"].sum()
    return summary

def update_sdg_from_data():
    # Simple automatic SDG contributions
    # GHG → SDG 7, 13
    # Energy → SDG 7, 13
    # Water → SDG 6
    for i in range(1,18):
        st.session_state.sdg_engagement[i]=0
    if not st.session_state.ghg_entries.empty:
        st.session_state.sdg_engagement[7] = 20
        st.session_state.sdg_engagement[13] = 20
    if not st.session_state.renewable_entries.empty:
        st.session_state.sdg_engagement[7] = max(st.session_state.sdg_engagement[7], 50)
        st.session_state.sdg_engagement[13] = max(st.session_state.sdg_engagement[13], 50)
    if not st.session_state.water_entries.empty:
        st.session_state.sdg_engagement[6] = 50

# ---------------------------
# Rendering Dashboards
# ---------------------------
def render_home():
    st.title("EinTrust Sustainability Dashboard")
    update_sdg_from_data()
    
    # GHG KPIs
    ghg_kpis = calculate_ghg_kpis()
    c1,c2,c3,c4 = st.columns(4)
    for col,label,value,color in zip([c1,c2,c3,c4],
                                     ["Total Quantity","Scope 1","Scope 2","Scope 3"],
                                     [ghg_kpis["Total Quantity"],ghg_kpis["Scope 1"],ghg_kpis["Scope 2"],ghg_kpis["Scope 3"]],
                                     ["#ffffff",SCOPE_COLORS["Scope 1"],SCOPE_COLORS["Scope 2"],SCOPE_COLORS["Scope 3"]]):
        col.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{color}'>{format_indian(value)}</div><div class='kpi-unit'>{ghg_kpis['Unit']}</div><div class='kpi-label'>{label.lower()}</div></div>", unsafe_allow_html=True)

    # Energy KPIs
    energy_kpis = calculate_energy_kpis()
    c1,c2,c3 = st.columns(3)
    for col,label,value,color in zip([c1,c2,c3],
                                     ["Total Energy (kWh)","Fossil Energy (kWh)","Renewable Energy (kWh)"],
                                     [energy_kpis["Total"],energy_kpis["Fossil"],energy_kpis["Renewable"]],
                                     ["#ffffff",ENERGY_COLORS["Fossil"],ENERGY_COLORS["Renewable"]]):
        col.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{color}'>{int(value):,}</div><div class='kpi-unit'>kWh</div><div class='kpi-label'>{label.lower()}</div></div>", unsafe_allow_html=True)

    # Water KPIs
    water_kpis = calculate_water_kpis()
    c1,c2,c3,c4 = st.columns(4)
    for col,label,value,color in zip([c1,c2,c3,c4],
                                     ["Freshwater","Recycled","Rainwater","STP/ETP Capacity"],
                                     [water_kpis["Freshwater"],water_kpis["Recycled"],water_kpis["Rainwater"],water_kpis["STP_ETP"]],
                                     ["#1f77b4","#2ca02c","#ff7f0e","#9467bd"]):
        col.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{color}'>{int(value):,}</div><div class='kpi-unit'>kL</div><div class='kpi-label'>{label.lower()}</div></div>", unsafe_allow_html=True)

    # Optional charts (GHG)
    if not st.session_state.ghg_entries.empty:
        df = st.session_state.ghg_entries.copy()
        df["Month"] = pd.Categorical(df["Month"], categories=months, ordered=True)
        monthly_trend = df.groupby(["Month"])["Quantity"].sum().reset_index()
        st.subheader("Monthly GHG Emissions")
        fig = px.bar(monthly_trend, x="Month", y="Quantity")
        st.plotly_chart(fig, use_container_width=True)

    # Optional charts (Energy)
    if not (st.session_state.renewable_entries.empty and st.session_state.ghg_entries.empty):
        energy_df = pd.DataFrame()
        # Fossil energy from GHG
        fossil_list = []
        for idx,row in st.session_state.ghg_entries.iterrows():
            if row["Sub-Activity"] in ["Diesel Generator","Petrol Generator","Diesel Vehicle"]:
                fossil_list.append({"Month":row["Month"],"Type":"Fossil","Energy_kWh":row["Quantity"]*10})
        fossil_df = pd.DataFrame(fossil_list)
        if not st.session_state.renewable_entries.empty:
            renewable_df = st.session_state.renewable_entries.copy()
            energy_df = pd.concat([fossil_df,renewable_df],ignore_index=True)
        else:
            energy_df = fossil_df
        energy_df["Month"] = pd.Categorical(energy_df["Month"], categories=months, ordered=True)
        monthly_trend = energy_df.groupby(["Month","Type"])["Energy_kWh"].sum().reset_index()
        st.subheader("Monthly Energy Consumption")
        fig = px.bar(monthly_trend, x="Month", y="Energy_kWh", color="Type", barmode="stack", color_discrete_map=ENERGY_COLORS)
        st.plotly_chart(fig, use_container_width=True)

    # Optional charts (Water)
    if not st.session_state.water_entries.empty:
        df = st.session_state.water_entries.copy()
        df["Month"] = pd.Categorical(df["Month"], categories=months, ordered=True)
        monthly_trend = df.groupby("Month")[["Freshwater_kL","Recycled_kL","Rainwater_kL"]].sum().reset_index()
        st.subheader("Monthly Water Usage")
        fig = px.bar(monthly_trend, x="Month", y=["Freshwater_kL","Recycled_kL","Rainwater_kL"], barmode="stack")
        st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# Render GHG Page
# ---------------------------
def render_ghg():
    st.subheader("Add GHG Entry")
    scope = st.selectbox("Scope", ["Scope 1","Scope 2","Scope 3"])
    activity = st.text_input("Activity")
    sub_activity = st.text_input("Sub-Activity")
    specific_item = st.text_input("Specific Item")
    unit = st.text_input("Unit", "tCO2e")
    quantity = st.number_input("Quantity", min_value=0.0)
    month = st.selectbox("Month", months)
    if st.button("Add GHG Entry"):
        new_entry = {"Scope":scope,"Activity":activity,"Sub-Activity":sub_activity,"Specific Item":specific_item,
                     "Quantity":quantity,"Unit":unit,"Month":month}
        st.session_state.ghg_entries = pd.concat([st.session_state.ghg_entries, pd.DataFrame([new_entry])], ignore_index=True)
        st.success("GHG entry added!")
        st.experimental_rerun()
    if not st.session_state.ghg_entries.empty:
        st.subheader("All GHG Entries")
        st.dataframe(st.session_state.ghg_entries)
        csv = st.session_state.ghg_entries.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "ghg_entries.csv","text/csv")

# ---------------------------
# Render Energy Page
# ---------------------------
def render_energy():
    st.subheader("Add Renewable Energy Entry")
    source = st.selectbox("Source", ["Solar","Wind","Biogas","Purchased Green Energy"])
    location = st.text_input("Location")
    annual_energy = st.number_input("Annual Energy (kWh)", min_value=0.0)
    month = st.selectbox("Month", months)
    if st.button("Add Renewable Energy Entry"):
        monthly_energy = annual_energy/12
        new_entry = {"Source":source,"Location":location,"Month":month,"Energy_kWh":monthly_energy,"CO2e_kg":0,"Type":"Renewable"}
        st.session_state.renewable_entries = pd.concat([st.session_state.renewable_entries,pd.DataFrame([new_entry])], ignore_index=True)
        st.success("Energy entry added!")
        st.experimental_rerun()
    # Show all energy entries
    energy_df = pd.DataFrame()
    # Fossil from GHG
    fossil_list = []
    for idx,row in st.session_state.ghg_entries.iterrows():
        if row["Sub-Activity"] in ["Diesel Generator","Petrol Generator","Diesel Vehicle"]:
            fossil_list.append({"Month":row["Month"],"Type":"Fossil","Energy_kWh":row["Quantity"]*10})
    fossil_df = pd.DataFrame(fossil_list)
    if not st.session_state.renewable_entries.empty:
        energy_df = pd.concat([fossil_df,st.session_state.renewable_entries],ignore_index=True)
    else:
        energy_df = fossil_df
    if not energy_df.empty:
        st.subheader("All Energy Entries")
        st.dataframe(energy_df)
        csv = energy_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "energy_entries.csv","text/csv")

# ---------------------------
# Render Water Page
# ---------------------------
def render_water():
    st.subheader("Add Water Entry")
    month = st.selectbox("Month", months)
    freshwater = st.number_input("Freshwater used (kL)", min_value=0.0)
    recycled = st.number_input("Water recycled (kL)", min_value=0.0)
    rainwater = st.number_input("Rainwater harvested (kL)", min_value=0.0)
    stp = st.number_input("STP/ETP Capacity (kL/day)", min_value=0.0)
    if st.button("Add Water Entry"):
        new_entry = {"Month":month,"Freshwater_kL":freshwater,"Recycled_kL":recycled,
                     "Rainwater_kL":rainwater,"STP_ETP_kL":stp}
        st.session_state.water_entries = pd.concat([st.session_state.water_entries,pd.DataFrame([new_entry])], ignore_index=True)
        st.success("Water entry added!")
        st.experimental_rerun()
    if not st.session_state.water_entries.empty:
        st.subheader("All Water Entries")
        st.dataframe(st.session_state.water_entries)
        csv = st.session_state.water_entries.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "water_entries.csv","text/csv")

# ---------------------------
# Render SDG Page
# ---------------------------
def render_sdg():
    st.title("Sustainable Development Goals (SDGs)")
    update_sdg_from_data()
    num_cols = 4
    rows = (len(SDG_LIST)+num_cols-1)//num_cols
    idx = 0
    for r in range(rows):
        cols = st.columns(num_cols)
        for c in range(num_cols):
            if idx>=len(SDG_LIST):
                break
            sdg_name = SDG_LIST[idx]
            sdg_color = SDG_COLORS[idx]
            sdg_number = idx+1
            engagement = st.session_state.sdg_engagement.get(sdg_number,0)
            engagement = cols[c].slider(f"Engagement % - SDG {sdg_number}",0,100,value=engagement,key=f"sdg{sdg_number}")
            st.session_state.sdg_engagement[sdg_number]=engagement
            cols[c].markdown(f"<div class='sdg-card' style='background-color:{sdg_color}'><div class='sdg-number'>SDG {sdg_number}</div><div class='sdg-name'>{sdg_name}</div><div class='sdg-percent'>Engagement: {engagement}%</div></div>", unsafe_allow_html=True)
            idx+=1

# ---------------------------
# Render Pages
# ---------------------------
if st.session_state.page=="Home":
    render_home()
elif st.session_state.page=="GHG":
    render_ghg()
elif st.session_state.page=="Energy":
    render_energy()
elif st.session_state.page=="Water":
    render_water()
elif st.session_state.page=="SDG":
    render_sdg()
else:
    st.subheader(f"{st.session_state.page} section")
    st.info("This section is under development. Please select other pages from sidebar.")
