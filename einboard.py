import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
import plotly.express as px

# ---------------------------
# Config & Dark Theme
# ---------------------------
st.set_page_config(page_title="EinTrust Dashboard", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }
.stApp { background-color: #0d1117; color: #e6edf3; }

.kpi { background: linear-gradient(145deg, #12131a, #1a1b22); padding: 20px; border-radius: 12px;
      text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.5); margin-bottom: 10px; min-height: 120px;
      display: flex; flex-direction: column; justify-content: center; align-items: center;
      transition: transform 0.2s, box-shadow 0.2s;}
.kpi:hover { transform: scale(1.05); box-shadow: 0 8px 20px rgba(0,0,0,0.6);}
.kpi-value { font-size: 28px; font-weight: 700; color: #ffffff; margin-bottom: 5px;}
.kpi-unit { font-size: 16px; font-weight: 500; color: #cfd8dc; margin-bottom: 5px;}
.kpi-label { font-size: 14px; color: #cfd8dc; letter-spacing: 0.5px;}
</style>
""", unsafe_allow_html=True)

MONTHS = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]

# ---------------------------
# Session state
# ---------------------------
if "entries" not in st.session_state:
    st.session_state.entries = pd.DataFrame(columns=["Scope","Activity","Sub-Activity","Specific Item","Quantity","Unit"])
if "renewable_list" not in st.session_state:
    st.session_state.renewable_list = []
if "page" not in st.session_state:
    st.session_state.page = "Home"

# ---------------------------
# Sidebar
# ---------------------------
with st.sidebar:
    st.title("EinTrust Dashboard")
    if st.button("Home"): st.session_state.page = "Home"
    if st.button("GHG"): st.session_state.page = "GHG"
    if st.button("Energy"): st.session_state.page = "Energy"

# ---------------------------
# Utilities
# ---------------------------
def format_indian(n: float) -> str:
    try: x = int(round(float(n)))
    except: return "0"
    s = str(abs(x))
    if len(s) <= 3: res = s
    else:
        res = s[-3:]; s=s[:-3]
        while len(s) > 2: res = s[-2:]+","+res; s=s[:-2]
        if s: res = s+","+res
    return ("-" if x<0 else "")+res

def render_kpis(kpi_dict, title, colors=None, unit="tCO₂e"):
    st.subheader(title)
    cols = st.columns(len(kpi_dict))
    for col,(label,value) in zip(cols,kpi_dict.items()):
        color = colors.get(label,"#ffffff") if colors else "#ffffff"
        col.markdown(f"""
        <div class='kpi'>
            <div class='kpi-value' style='color:{color}'>{format_indian(value)}</div>
            <div class='kpi-unit'>{unit}</div>
            <div class='kpi-label'>{label}</div>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------
# Compute GHG
# ---------------------------
def compute_ghg_kpis():
    df = st.session_state.entries
    kpis = {"Total":0.0,"Scope 1":0.0,"Scope 2":0.0,"Scope 3":0.0}
    if not df.empty:
        for scope in ["Scope 1","Scope 2","Scope 3"]:
            kpis[scope] = df[df["Scope"]==scope]["Quantity"].sum()
        kpis["Total"] = df["Quantity"].sum()
    return kpis

# ---------------------------
# Compute Energy
# ---------------------------
EM_FACTORS = {"Diesel":2.68,"Petrol":2.31,"LPG":1.51,"CNG":2.02,"Coal":2.42,"Biomass":0.0,
              "Electricity":0.82,"Solar":0.0,"Wind":0.0,"Purchased Green Energy":0.0,"Biogas":0.0}

def compute_energy_kpis():
    df = st.session_state.entries
    fossil = df.copy() if not df.empty else pd.DataFrame(columns=["Sub-Activity","Quantity"])
    fossil_energy = fossil["Quantity"].sum() if not fossil.empty else 0
    fossil_co2e = (fossil["Quantity"]*fossil["Sub-Activity"].map(EM_FACTORS).fillna(0)).sum() if not fossil.empty else 0
    renewable = pd.DataFrame(st.session_state.renewable_list)
    renewable_energy = renewable["Energy_kWh"].sum() if not renewable.empty else 0
    renewable_co2e = renewable["CO2e_kg"].sum() if not renewable.empty else 0
    total_energy = fossil_energy + renewable_energy
    total_co2e = fossil_co2e + renewable_co2e
    return {"Total":total_energy,"Fossil":fossil_energy,"Renewable":renewable_energy}, \
           {"Total":total_co2e,"Fossil":fossil_co2e,"Renewable":renewable_co2e}, fossil, renewable

# ---------------------------
# Render GHG page
# ---------------------------
def render_ghg_dashboard():
    colors = {"Total":"#ffffff","Scope 1":"#f06292","Scope 2":"#4db6ac","Scope 3":"#aed581"}
    render_kpis(compute_ghg_kpis(),"GHG Dashboard",colors)
    st.subheader("Add GHG Entry")
    scope = st.selectbox("Scope",["Scope 1","Scope 2","Scope 3"])
    sub_activity = st.text_input("Sub-Activity","")
    qty = st.number_input("Quantity",0.0)
    if st.button("Add Entry"):
        st.session_state.entries = pd.concat([st.session_state.entries,
                                              pd.DataFrame([{"Scope":scope,"Activity":scope,"Sub-Activity":sub_activity,"Specific Item":"",
                                                             "Quantity":qty,"Unit":"tCO2e"}])], ignore_index=True)
        st.experimental_rerun()
    if not st.session_state.entries.empty:
        st.dataframe(st.session_state.entries)

# ---------------------------
# Render Energy page
# ---------------------------
def render_energy_dashboard(include_entry=True):
    colors = {"Total":"#ffffff","Fossil":"#f06292","Renewable":"#4db6ac"}
    energy_kpis, co2e_kpis, fossil_df, renewable_df = compute_energy_kpis()
    render_kpis(energy_kpis,"Energy Consumption",colors,unit="kWh")
    render_kpis(co2e_kpis,"CO₂e Emissions",colors,unit="kg")
    
    # Month-wise stacking
    trend = pd.DataFrame({"Month":MONTHS})
    if not fossil_df.empty:
        trend["Fossil"] = fossil_df.groupby("Sub-Activity")["Quantity"].sum().sum()
    else:
        trend["Fossil"] = 0
    if not renewable_df.empty:
        trend["Renewable"] = renewable_df.groupby("Month")["Energy_kWh"].sum().reindex(MONTHS, fill_value=0).values
    else:
        trend["Renewable"] = 0
    st.subheader("Monthly Energy Trend")
    fig = px.bar(trend, x="Month", y=["Fossil","Renewable"], barmode="stack",
                 labels={"value":"Energy (kWh)","Month":"Month"})
    st.plotly_chart(fig,use_container_width=True)

    if include_entry:
        st.subheader("Add Renewable Energy Entry")
        source = st.selectbox("Source",["Solar","Wind","Biogas","Purchased Green Energy"])
        loc = st.text_input("Location")
        annual = st.number_input("Annual Energy kWh",0.0)
        if st.button("Add Renewable Entry"):
            monthly = annual/12
            for m in MONTHS:
                st.session_state.renewable_list.append({"Source":source,"Location":loc,"Month":m,"Energy_kWh":monthly,
                                                         "Type":"Renewable","CO2e_kg":monthly*EM_FACTORS.get(source,0)})
            st.experimental_rerun()

# ---------------------------
# Render Home page
# ---------------------------
if st.session_state.page=="Home":
    render_ghg_dashboard()
    render_energy_dashboard(include_entry=False)
elif st.session_state.page=="GHG":
    render_ghg_dashboard()
elif st.session_state.page=="Energy":
    render_energy_dashboard(include_entry=True)
else:
    st.info("Page under development.")
