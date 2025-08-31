import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ---------------------------
# CONFIG & CSS
# ---------------------------
st.set_page_config(page_title="EinTrust Sustainability Dashboard", page_icon="🌍", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }
.stApp { background-color: #0d1117; color: #e6edf3; }

.kpi {
    background: linear-gradient(145deg, #12131a, #1a1b22);
    padding: 20px; border-radius: 12px; text-align: center;
    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    margin-bottom: 10px; min-height: 120px;
    display: flex; flex-direction: column; justify-content: center; align-items: center;
    transition: transform 0.2s, box-shadow 0.2s;
}
.kpi:hover { transform: scale(1.05); box-shadow: 0 8px 20px rgba(0,0,0,0.6); }
.kpi-value { font-size: 28px; font-weight: 700; color: #ffffff; margin-bottom: 5px; }
.kpi-unit { font-size: 16px; font-weight: 500; color: #cfd8dc; margin-bottom: 5px; }
.kpi-label { font-size: 14px; color: #cfd8dc; letter-spacing: 0.5px; }
.stDataFrame { color: #e6edf3; font-family: 'Roboto', sans-serif; }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# UTILS
# ---------------------------
def format_indian(n: float) -> str:
    try:
        x = int(round(float(n)))
    except:
        return "0"
    s = str(abs(x))
    if len(s) <= 3: res = s
    else:
        res = s[-3:]
        s = s[:-3]
        while len(s) > 2:
            res = s[-2:] + "," + res
            s = s[:-2]
        if s: res = s + "," + res
    return ("-" if x < 0 else "") + res

months = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]

SCOPE_COLORS = {"Scope 1": "#81c784", "Scope 2": "#4db6ac", "Scope 3": "#aed581"}
ENERGY_COLORS = {"Fossil": "#f39c12", "Renewable": "#2ecc71"}
WATER_COLORS = {"Municipal":"#3498db","Groundwater":"#9b59b6","Recycled":"#2ecc71","Other":"#e74c3c"}

# ---------------------------
# SESSION STATE INIT
# ---------------------------
for key in ["ghg_entries","renewable_entries","water_data","advanced_water_data"]:
    if key not in st.session_state:
        st.session_state[key] = pd.DataFrame()

if "page" not in st.session_state:
    st.session_state.page = "Home"

# ---------------------------
# SIDEBAR
# ---------------------------
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
        sidebar_button("Waste")
        sidebar_button("Biodiversity")
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

# ---------------------------
# DASHBOARDS
# ---------------------------
# GHG DASHBOARD
def render_ghg_dashboard():
    st.subheader("GHG Emissions")
    df = st.session_state.ghg_entries
    # KPIs
    total_scope1 = df[df["Scope"]=="Scope 1"]["Quantity"].sum() if not df.empty else 0
    total_scope2 = df[df["Scope"]=="Scope 2"]["Quantity"].sum() if not df.empty else 0
    total_scope3 = df[df["Scope"]=="Scope 3"]["Quantity"].sum() if not df.empty else 0
    total_all = total_scope1+total_scope2+total_scope3
    c1,c2,c3,c4 = st.columns(4)
    for col,label,val,color in zip([c1,c2,c3,c4],
                                   ["Total","Scope 1","Scope 2","Scope 3"],
                                   [total_all,total_scope1,total_scope2,total_scope3],
                                   ["#ffffff",SCOPE_COLORS["Scope 1"],SCOPE_COLORS["Scope 2"],SCOPE_COLORS["Scope 3"]]):
        col.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{color}'>{format_indian(val)}</div><div class='kpi-unit'>tCO₂e</div><div class='kpi-label'>{label}</div></div>",unsafe_allow_html=True)
    # Monthly trend
    if not df.empty:
        df["Month"] = pd.Categorical(df.get("Month", months[0]), categories=months, ordered=True)
        monthly = df.groupby(["Month","Scope"])["Quantity"].sum().reset_index()
        fig = px.bar(monthly, x="Month", y="Quantity", color="Scope", barmode="stack", color_discrete_map=SCOPE_COLORS)
        st.plotly_chart(fig, use_container_width=True)
    # Entry form
    st.subheader("Add GHG Entry")
    scope = st.selectbox("Scope", ["Scope 1","Scope 2","Scope 3"], key="ghg_scope")
    activity = st.text_input("Activity / Sub-Activity", key="ghg_act")
    quantity = st.number_input("Quantity (tCO₂e)", min_value=0.0, key="ghg_qty")
    month = st.selectbox("Month", months, key="ghg_month")
    if st.button("Add GHG Entry"):
        new = pd.DataFrame([{"Scope":scope,"Activity":activity,"Quantity":quantity,"Month":month}])
        st.session_state.ghg_entries = pd.concat([st.session_state.ghg_entries,new],ignore_index=True)
        st.success("GHG entry added!")
        st.experimental_rerun()
    if not st.session_state.ghg_entries.empty:
        st.download_button("Download GHG CSV", st.session_state.ghg_entries.to_csv(index=False).encode('utf-8'), "ghg_data.csv")

# ENERGY DASHBOARD
def render_energy_dashboard():
    st.subheader("Energy Dashboard")
    df = st.session_state.renewable_entries
    # KPIs
    total_fossil = df[df["Type"]=="Fossil"]["Energy_kWh"].sum() if not df.empty else 0
    total_renew = df[df["Type"]=="Renewable"]["Energy_kWh"].sum() if not df.empty else 0
    total_all = total_fossil + total_renew
    c1,c2,c3 = st.columns(3)
    for col,label,val,color in zip([c1,c2,c3],
                                   ["Total","Fossil","Renewable"],
                                   [total_all,total_fossil,total_renew],
                                   ["#ffffff",ENERGY_COLORS["Fossil"],ENERGY_COLORS["Renewable"]]):
        col.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{color}'>{format_indian(val)}</div><div class='kpi-unit'>kWh</div><div class='kpi-label'>{label}</div></div>",unsafe_allow_html=True)
    # Monthly trend
    if not df.empty:
        df["Month"] = pd.Categorical(df.get("Month", months[0]), categories=months, ordered=True)
        monthly = df.groupby(["Month","Type"])["Energy_kWh"].sum().reset_index()
        fig = px.bar(monthly, x="Month", y="Energy_kWh", color="Type", barmode="stack", color_discrete_map=ENERGY_COLORS)
        st.plotly_chart(fig, use_container_width=True)
    # Entry form
    st.subheader("Add Renewable Energy Entry")
    source = st.selectbox("Source", ["Solar","Wind","Biogas","Purchased Green Energy"], key="ene_src")
    location = st.text_input("Location", key="ene_loc")
    annual_energy = st.number_input("Annual Energy kWh", min_value=0.0, key="ene_qty")
    if st.button("Add Energy Entry"):
        monthly_energy = annual_energy / 12
        new_list = [{"Source":source,"Location":location,"Month":m,"Energy_kWh":monthly_energy,"Type":"Renewable"} for m in months]
        st.session_state.renewable_entries = pd.concat([st.session_state.renewable_entries,pd.DataFrame(new_list)],ignore_index=True)
        st.success("Energy entry added!")
        st.experimental_rerun()
    if not st.session_state.renewable_entries.empty:
        st.download_button("Download Energy CSV", st.session_state.renewable_entries.to_csv(index=False).encode('utf-8'), "energy_data.csv")

# WATER DASHBOARD
def render_water_dashboard():
    st.subheader("Water Dashboard")
    df = st.session_state.water_data
    adv = st.session_state.advanced_water_data
    # KPIs
    total_water = df["Quantity_m3"].sum() if not df.empty else 0
    total_cost = df["Cost_INR"].sum() if not df.empty else 0
    recycled = adv["Water_Recycled_m3"].sum() if not adv.empty else 0
    rain = adv["Rainwater_Harvested_m3"].sum() if not adv.empty else 0
    c1,c2,c3,c4 = st.columns(4)
    for col,label,val,color in zip([c1,c2,c3,c4],
                                   ["Total Water Used","Estimated Cost","Recycled Water","Rainwater Harvested"],
                                   [total_water,total_cost,recycled,rain],
                                   ["#ffffff","#ffffff",WATER_COLORS["Recycled"],WATER_COLORS["Municipal"]]):
        col.metric(label,value=f"{val:,.0f}")
    # Monthly trend
    if not df.empty:
        df["Month"] = pd.Categorical(df.get("Month", months[0]), categories=months, ordered=True)
        monthly = df.groupby(["Month","Source"])["Quantity_m3"].sum().reset_index()
        fig = px.line(monthly,x="Month",y="Quantity_m3",color="Source",color_discrete_map=WATER_COLORS,markers=True)
        st.plotly_chart(fig,use_container_width=True)
    # Entry form
    st.subheader("Add Water Entry")
    location = st.text_input("Location", key="wat_loc")
    source = st.selectbox("Source", ["Municipal","Groundwater","Recycled","Other"], key="wat_src")
    annual_qty = st.number_input("Annual Quantity m³", min_value=0.0, key="wat_qty")
    cost = st.number_input("Total Cost INR", min_value=0.0, key="wat_cost")
    if st.button("Add Water Entry"):
        monthly_qty = annual_qty/12
        new_list = [{"Location":location,"Source":source,"Month":m,"Quantity_m3":monthly_qty,"Cost_INR":cost/12} for m in months]
        st.session_state.water_data = pd.concat([st.session_state.water_data,pd.DataFrame(new_list)],ignore_index=True)
        st.success("Water entry added!")
        st.experimental_rerun()
    if not st.session_state.water_data.empty:
        st.download_button("Download Water CSV", st.session_state.water_data.to_csv(index=False).encode('utf-8'), "water_data.csv")

# ---------------------------
# PAGE RENDERING
# ---------------------------
if st.session_state.page == "Home":
    st.title("EinTrust Sustainability Dashboard 🌍")
    st.subheader("GHG Summary")
    if not st.session_state.ghg_entries.empty:
        st.dataframe(st.session_state.ghg_entries)
    else:
        st.info("No GHG entries yet.")
    st.subheader("Energy Summary")
    if not st.session_state.renewable_entries.empty:
        st.dataframe(st.session_state.renewable_entries)
    else:
        st.info("No Energy entries yet.")
    st.subheader("Water Summary")
    if not st.session_state.water_data.empty:
        st.dataframe(st.session_state.water_data)
    else:
        st.info("No Water entries yet.")

elif st.session_state.page == "GHG":
    render_ghg_dashboard()
elif st.session_state.page == "Energy":
    render_energy_dashboard()
elif st.session_state.page == "Water":
    render_water_dashboard()
else:
    st.subheader(f"{st.session_state.page} page")
    st.info("This section is under development.")

