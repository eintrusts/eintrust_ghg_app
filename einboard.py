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

months = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]
SCOPE_COLORS = {"Scope 1": "#81c784", "Scope 2": "#4db6ac", "Scope 3": "#aed581"}
ENERGY_COLORS = {"Fossil": "#f39c12", "Renewable": "#2ecc71"}
SDG_LIST = ["No Poverty","Zero Hunger","Good Health & Wellbeing","Quality Education","Gender Equality",
            "Clean Water & Sanitation","Affordable & Clean Energy","Decent Work & Economic Growth","Industry, Innovation & Infrastructure",
            "Reduced Inequalities","Sustainable Cities & Communities","Responsible Consumption & Production","Climate Action","Life Below Water",
            "Life on Land","Peace, Justice & Strong Institutions","Partnerships for the Goals"]
SDG_COLORS = ["#e5243b","#dda63a","#4c9f38","#c5192d","#ff3a21","#26bde2","#fcc30b","#a21942","#fd6925","#dd1367","#fd9d24",
              "#bf8b2e","#3f7e44","#0a97d9","#56c02b","#00689d","#19486a"]

# ---------------------------
# Session State Init
# ---------------------------
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "entries" not in st.session_state:
    st.session_state.entries = pd.DataFrame(columns=["Scope","Activity","Sub-Activity","Specific Item","Quantity","Unit"])
if "renewable_entries" not in st.session_state:
    st.session_state.renewable_entries = pd.DataFrame(columns=["Source","Location","Month","Energy_kWh","CO2e_kg","Type"])
if "water_entries" not in st.session_state:
    st.session_state.water_entries = pd.DataFrame(columns=["Location","Month","Freshwater_kL","Recycled_kL","Rainwater_kL","STP_ETP_kL"])
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
    st.image("https://github.com/eintrusts/eintrust_ghg_app/blob/main/EinTrust%20%20(2).png?raw=true", use_container_width=True)
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

# ---------------------------
# GHG Dashboard
# ---------------------------
def calculate_kpis():
    df = st.session_state.entries
    summary = {"Scope 1":0.0,"Scope 2":0.0,"Scope 3":0.0,"Total Quantity":0.0,"Unit":"tCO₂e"}
    if not df.empty:
        for scope in ["Scope 1","Scope 2","Scope 3"]:
            summary[scope] = df[df["Scope"]==scope]["Quantity"].sum()
        summary["Total Quantity"] = df["Quantity"].sum()
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
        if "Month" not in df.columns:
            df["Month"] = np.random.choice(months, len(df))
        df["Month"] = pd.Categorical(df["Month"], categories=months, ordered=True)
        monthly_trend = df.groupby(["Month","Scope"])["Quantity"].sum().reset_index()
        st.subheader("Monthly GHG Emissions")
        fig = px.bar(monthly_trend, x="Month", y="Quantity", color="Scope", barmode="stack", color_discrete_map=SCOPE_COLORS)
        st.plotly_chart(fig, use_container_width=True)
    
    if include_data:
        scope_options = ["Scope 1","Scope 2","Scope 3"]
        scope = st.selectbox("Select Scope", scope_options)
        activity = st.text_input("Activity")
        sub_activity = st.text_input("Sub-Activity")
        unit = st.text_input("Unit", "tCO₂e")
        quantity = st.number_input(f"Quantity ({unit})", min_value=0.0, format="%.2f")
        if st.button("Add GHG Entry"):
            new_entry = {"Scope":scope,"Activity":activity,"Sub-Activity":sub_activity,"Specific Item":"","Quantity":quantity,"Unit":unit}
            st.session_state.entries = pd.concat([st.session_state.entries, pd.DataFrame([new_entry])], ignore_index=True)
            st.success("Entry added!")
            st.experimental_rerun()
    
    if not st.session_state.entries.empty:
        st.subheader("All GHG Entries")
        df = st.session_state.entries.copy()
        df["Quantity"] = df["Quantity"].apply(lambda x: format_indian(x))
        st.dataframe(df)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", csv, "ghg_entries.csv", "text/csv")

# ---------------------------
# Energy Dashboard
# ---------------------------
def render_energy_dashboard(include_input=True, show_chart=True):
    st.subheader("Energy")
    df_fossil = st.session_state.entries.copy() if not st.session_state.entries.empty else pd.DataFrame()
    df_renew = st.session_state.renewable_entries.copy() if not st.session_state.renewable_entries.empty else pd.DataFrame()
    
    total_fossil = df_fossil["Quantity"].sum() if not df_fossil.empty else 0
    total_renew = df_renew["Energy_kWh"].sum() if not df_renew.empty else 0
    total_energy = total_fossil + total_renew
    
    c1,c2,c3 = st.columns(3)
    for col,label,value,color in zip([c1,c2,c3],["Total Energy (kWh)","Fossil Energy (kWh)","Renewable Energy (kWh)"],
                                    [total_energy,total_fossil,total_renew],
                                    ["#ffffff",ENERGY_COLORS["Fossil"],ENERGY_COLORS["Renewable"]]):
        col.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{color}'>{format_indian(value)}</div><div class='kpi-unit'>kWh</div><div class='kpi-label'>{label.lower()}</div></div>", unsafe_allow_html=True)
    
    if show_chart and (not df_fossil.empty or not df_renew.empty):
        df_fossil["Month"] = pd.Categorical(df_fossil.get("Month",months[0]), categories=months, ordered=True)
        df_renew["Month"] = pd.Categorical(df_renew.get("Month",months[0]), categories=months, ordered=True)
        df_all = pd.concat([df_fossil.rename(columns={"Quantity":"Energy_kWh"}), df_renew], ignore_index=True)
        monthly_trend = df_all.groupby(["Month","Type"])["Energy_kWh"].sum().reset_index()
        st.subheader("Monthly Energy Consumption (kWh)")
        fig = px.bar(monthly_trend, x="Month", y="Energy_kWh", color="Type", barmode="stack", color_discrete_map=ENERGY_COLORS)
        st.plotly_chart(fig, use_container_width=True)
    
    if include_input:
        st.subheader("Add Renewable Energy Entry")
        source = st.selectbox("Source", ["Solar","Wind","Biogas","Purchased Green Energy"])
        location = st.text_input("Location")
        annual_energy = st.number_input("Annual Energy (kWh)", min_value=0.0)
        if st.button("Add Renewable Entry"):
            monthly_energy = annual_energy/12
            new_entries = []
            for m in months:
                new_entries.append({"Source":source,"Location":location,"Month":m,"Energy_kWh":monthly_energy,"CO2e_kg":0,"Type":"Renewable"})
            st.session_state.renewable_entries = pd.concat([st.session_state.renewable_entries, pd.DataFrame(new_entries)], ignore_index=True)
            st.success("Renewable energy entry added!")
            st.experimental_rerun()

# ---------------------------
# Water Dashboard
# ---------------------------
def render_water_dashboard():
    st.subheader("Water")
    # --- KPIs ---
    df = st.session_state.water_entries
    total_fresh = df["Freshwater_kL"].sum() if not df.empty else 0
    total_recycled = df["Recycled_kL"].sum() if not df.empty else 0
    total_rain = df["Rainwater_kL"].sum() if not df.empty else 0
    c1,c2,c3 = st.columns(3)
    for col,label,value in zip([c1,c2,c3],["Freshwater Used","Water Recycled","Rainwater Harvested"],[total_fresh,total_recycled,total_rain]):
        col.markdown(f"<div class='kpi'><div class='kpi-value'>{format_indian(value)}</div><div class='kpi-unit'>kL</div><div class='kpi-label'>{label}</div></div>", unsafe_allow_html=True)
    
    # --- Input ---
    st.subheader("Add Water Entry")
    location = st.text_input("Location")
    freshwater = st.number_input("Freshwater used (kL)", min_value=0.0)
    recycled = st.number_input("Water recycled (kL)", min_value=0.0)
    rain = st.number_input("Rainwater harvested (kL)", min_value=0.0)
    stp_capacity = st.number_input("STP/ETP Capacity (kL/day)", min_value=0.0)
    if st.button("Add Water Entry"):
        new_entry = {"Location":location,"Month":np.random.choice(months),"Freshwater_kL":freshwater,"Recycled_kL":recycled,
                     "Rainwater_kL":rain,"STP_ETP_kL":stp_capacity}
        st.session_state.water_entries = pd.concat([st.session_state.water_entries, pd.DataFrame([new_entry])], ignore_index=True)
        st.success("Water entry added!")
        st.experimental_rerun()
    
    # --- Chart & Table ---
    if not df.empty:
        df["Month"] = pd.Categorical(df["Month"], categories=months, ordered=True)
        monthly_trend = df.groupby("Month")[["Freshwater_kL","Recycled_kL","Rainwater_kL"]].sum().reset_index()
        st.subheader("Monthly Water Usage (kL)")
        fig = px.bar(monthly_trend, x="Month", y=["Freshwater_kL","Recycled_kL","Rainwater_kL"],
                     barmode="stack", labels={"value":"kL","variable":"Water Type"})
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("All Water Entries")
        st.dataframe(df)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", csv, "water_entries.csv", "text/csv")

# ---------------------------
# SDG Dashboard
# ---------------------------
def render_sdg_dashboard():
    st.title("Sustainable Development Goals (SDGs)")
    st.subheader("Company Engagement by SDG")
    num_cols = 4
    rows = (len(SDG_LIST)+num_cols-1)//num_cols
    idx = 0
    for r in range(rows):
        cols = st.columns(num_cols)
        for c in range(num_cols):
            if idx >= len(SDG_LIST): break
            sdg_name = SDG_LIST[idx]
            sdg_color = SDG_COLORS[idx]
            sdg_number = idx + 1
            engagement = st.session_state.sdg_engagement.get(sdg_number,0)
            engagement = cols[c].slider(f"Engagement % - SDG {sdg_number}", 0, 100, value=engagement, key=f"sdg{sdg_number}")
            st.session_state.sdg_engagement[sdg_number] = engagement
            cols[c].markdown(f"<div class='sdg-card' style='background-color:{sdg_color}'><div class='sdg-number'>SDG {sdg_number}</div><div class='sdg-name'>{sdg_name}</div><div class='sdg-percent'>Engagement: {engagement}%</div></div>", unsafe_allow_html=True)
            idx +=1

# ---------------------------
# Render Pages
# ---------------------------
if st.session_state.page=="Home":
    st.title("EinTrust Sustainability Dashboard")
    render_ghg_dashboard(include_data=False, show_chart=False)
    render_energy_dashboard(include_input=False, show_chart=False)
    render_water_dashboard()
elif st.session_state.page=="GHG":
    render_ghg_dashboard(include_data=True, show_chart=True)
elif st.session_state.page=="Energy":
    render_energy_dashboard(include_input=True, show_chart=True)
elif st.session_state.page=="Water":
    render_water_dashboard()
elif st.session_state.page=="SDG":
    render_sdg_dashboard()
else:
    st.subheader(f"{st.session_state.page} section")
    st.info("This section is under development.")
