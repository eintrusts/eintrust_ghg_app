import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px

# ---------------------------
# Config & CSS
# ---------------------------
st.set_page_config(page_title="EinTrust Dashboard", page_icon="🌍", layout="wide")
st.markdown("""
<style>
.stApp {background-color:#0d1117; color:#e6edf3;}
.kpi {background:linear-gradient(145deg,#12131a,#1a1b22); padding:20px; border-radius:12px; text-align:center; box-shadow:0 4px 12px rgba(0,0,0,0.5); min-height:120px; display:flex; flex-direction:column; justify-content:center; align-items:center; margin-bottom:10px;}
.kpi-value {font-size:28px; font-weight:700; color:#ffffff; margin-bottom:5px;}
.kpi-unit {font-size:16px; font-weight:500; color:#cfd8dc; margin-bottom:5px;}
.kpi-label {font-size:14px; color:#cfd8dc; letter-spacing:0.5px;}
</style>
""", unsafe_allow_html=True)

MONTHS = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]

# ---------------------------
# Session state
# ---------------------------
if "entries" not in st.session_state:
    st.session_state.entries = pd.DataFrame(columns=["Scope","Activity","Sub-Activity","Specific Item","Quantity","Unit"])
if "energy_entries" not in st.session_state:
    st.session_state.energy_entries = pd.DataFrame(columns=["Source","Location","Month","Energy_kWh","CO2e_kg","Type"])
if "page" not in st.session_state:
    st.session_state.page = "Home"

# ---------------------------
# Sidebar
# ---------------------------
with st.sidebar:
    st.image("https://github.com/eintrusts/eintrust_ghg_app/raw/main/EinTrust%20%20logo.png", use_container_width=True)
    st.markdown("---")
    
    if st.button("Home"): st.session_state.page="Home"
    
    env_exp = st.expander("Environment", expanded=True)
    with env_exp:
        if st.button("GHG"): st.session_state.page="GHG"
        if st.button("Energy"): st.session_state.page="Energy"
        if st.button("Water"): st.session_state.page="Water"
        if st.button("Waste"): st.session_state.page="Waste"
        if st.button("Biodiversity"): st.session_state.page="Biodiversity"
    
    social_exp = st.expander("Social", expanded=False)
    with social_exp:
        if st.button("Employee"): st.session_state.page="Employee"
        if st.button("Health & Safety"): st.session_state.page="Health & Safety"
        if st.button("CSR"): st.session_state.page="CSR"

    gov_exp = st.expander("Governance", expanded=False)
    with gov_exp:
        if st.button("Board"): st.session_state.page="Board"
        if st.button("Policies"): st.session_state.page="Policies"
        if st.button("Compliance"): st.session_state.page="Compliance"
        if st.button("Risk Management"): st.session_state.page="Risk Management"

# ---------------------------
# GHG/ENERGY Helpers
# ---------------------------
def format_indian(n):
    try:
        x=int(round(float(n)))
    except: return "0"
    s=str(abs(x))
    if len(s)<=3: res=s
    else:
        res=s[-3:]; s=s[:-3]
        while len(s)>2:
            res=s[-2:]+","+res
            s=s[:-2]
        if s: res=s+","+res
    return ("-" if x<0 else "")+res

def render_kpis(kpis,title="",colors=None):
    st.subheader(title)
    c1,c2,c3,c4=st.columns(4)
    labels=["Total","Scope 1","Scope 2","Scope 3"]
    for col,label in zip([c1,c2,c3,c4],labels):
        value=format_indian(kpis.get(label,0))
        color=colors.get(label,"#ffffff") if colors else "#ffffff"
        unit=kpis.get("Unit","")
        col.markdown(f"<div class='kpi'><div class='kpi-value' style='color:{color}'>{value}</div><div class='kpi-unit'>{unit}</div><div class='kpi-label'>{label.lower()}</div></div>", unsafe_allow_html=True)

# ---------------------------
# GHG Dashboard
# ---------------------------
def render_ghg_dashboard(include_data=True):
    df = st.session_state.entries
    kpis={"Scope 1":0,"Scope 2":0,"Scope 3":0,"Total":0,"Unit":"tCO₂e"}
    if not df.empty:
        for s in ["Scope 1","Scope 2","Scope 3"]:
            kpis[s]=df[df["Scope"]==s]["Quantity"].sum()
        kpis["Total"]=df["Quantity"].sum()
    colors={"Total":"#ffffff","Scope 1":"#81c784","Scope 2":"#4db6ac","Scope 3":"#aed581"}
    render_kpis(kpis,"GHG emissions dashboard",colors)

    if include_data:
        st.subheader("Add GHG Entry")
        scope=st.selectbox("Scope",["Scope 1","Scope 2","Scope 3"])
        activity=st.text_input("Activity")
        sub_activity=st.text_input("Sub-Activity")
        quantity=st.number_input("Quantity (tCO2e)",0.0)
        if st.button("Add GHG Entry"):
            new={"Scope":scope,"Activity":activity,"Sub-Activity":sub_activity,"Specific Item":"","Quantity":quantity,"Unit":"tCO₂e"}
            st.session_state.entries=pd.concat([st.session_state.entries,pd.DataFrame([new])],ignore_index=True)
            st.success("GHG entry added!"); st.experimental_rerun()

# ---------------------------
# Energy Dashboard
# ---------------------------
def render_energy_dashboard(include_entry=True):
    # Fossil from GHG
    fossil_entries = st.session_state.entries.copy()
    fossil_list=[]
    if not fossil_entries.empty:
        for _,r in fossil_entries.iterrows():
            fossil_list.append({"Source":r["Sub-Activity"],"Location":"N/A","Month":m,"Energy_kWh":r["Quantity"]*1000,"CO2e_kg":r["Quantity"]*1000,"Type":"Fossil"} for m in MONTHS)
        fossil_list = [item for sublist in fossil_list for item in sublist]

    renewable_df = st.session_state.energy_entries.copy()
    all_energy = pd.DataFrame(fossil_list) if fossil_list else pd.DataFrame(columns=["Source","Location","Month","Energy_kWh","CO2e_kg","Type"])
    if not renewable_df.empty:
        all_energy=pd.concat([all_energy,renewable_df],ignore_index=True)
    if "Type" not in all_energy.columns:
        all_energy["Type"]="Unknown"

    # KPIs
    kpis={"Total":all_energy["Energy_kWh"].sum() if not all_energy.empty else 0,
          "Fossil":all_energy[all_energy["Type"]=="Fossil"]["Energy_kWh"].sum() if not all_energy.empty else 0,
          "Renewable":all_energy[all_energy["Type"]=="Renewable"]["Energy_KWh"].sum() if "Energy_KWh" in all_energy else 0,
          "Unit":"kWh"}
    colors={"Total":"#ffffff","Fossil":"#f06292","Renewable":"#4db6ac"}
    render_kpis(kpis,"Energy dashboard",colors)

    # Monthly trend
    if not all_energy.empty:
        all_energy["Month"]=pd.Categorical(all_energy["Month"],categories=MONTHS,ordered=True)
        trend=all_energy.groupby(["Month","Type"])["Energy_kWh"].sum().reset_index()
        fig=px.bar(trend,x="Month",y="Energy_kWh",color="Type",barmode="stack",title="Monthly Energy Consumption")
        st.plotly_chart(fig,use_container_width=True)

    # Renewable entry
    if include_entry:
        st.subheader("Add Renewable Energy")
        source=st.selectbox("Source",["Solar","Wind","Biogas"])
        location=st.text_input("Location")
        energy=st.number_input("Annual Energy (kWh)",0.0)
        if st.button("Add Renewable Entry"):
            rows=[]
            monthly=energy/12
            for m in MONTHS:
                rows.append({"Source":source,"Location":location,"Month":m,"Energy_kWh":monthly,"CO2e_kg":monthly*0,"Type":"Renewable"})
            st.session_state.energy_entries=pd.concat([st.session_state.energy_entries,pd.DataFrame(rows)],ignore_index=True)
            st.success("Renewable energy added!"); st.experimental_rerun()

# ---------------------------
# Page rendering
# ---------------------------
st.title("🌍 EinTrust Sustainability Dashboard")

if st.session_state.page=="Home":
    render_ghg_dashboard(include_data=False)
    render_energy_dashboard(include_entry=False)
elif st.session_state.page=="GHG":
    render_ghg_dashboard(include_data=True)
elif st.session_state.page=="Energy":
    render_energy_dashboard(include_entry=True)
else:
    st.subheader(f"{st.session_state.page} section")
    st.info("Under development. Use sidebar to navigate.")
