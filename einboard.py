import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io
from office365.runtime.auth.user_credential import UserCredential
from office365.sharepoint.client_context import ClientContext

# --- Page Config ---
st.set_page_config(page_title="EinTrust GHG Dashboard", page_icon="🌍", layout="wide")

# --- Load Emission Factors (internal use only) ---
try:
    emission_factors = pd.read_csv("emission_factors.csv")
except FileNotFoundError:
    st.error("emission_factors.csv not found. Please place it in the same folder as this app.")
    emission_factors = pd.DataFrame(columns=["scope","category","activity","unit","emission_factor"])

# --- Session State ---
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "user_profile" not in st.session_state:
    st.session_state.user_profile = {}
if "page" not in st.session_state:
    st.session_state.page = "login"
if "emissions_summary" not in st.session_state:
    st.session_state.emissions_summary = {"Scope 1":0, "Scope 2":0, "Scope 3":0}
if "emissions_log" not in st.session_state:
    st.session_state.emissions_log = []

# --- SharePoint Config ---
SHAREPOINT_URL = "https://eintrusts.sharepoint.com/sites/EinTrust"
USERNAME = "your_service_account@eintrusts.com"
PASSWORD = "your_password"
TARGET_FOLDER = "/sites/EinTrust/Shared Documents/ClientData"
ctx = ClientContext(SHAREPOINT_URL).with_credentials(UserCredential(USERNAME, PASSWORD))

# --- Placeholder OAuth Login (replace with proper OAuth setup) ---
def login_placeholder():
    st.info("Login placeholder: Set st.session_state.user_email manually for now")
    if st.button("Login as demo@example.com"):
        st.session_state.user_email = "demo@example.com"
        st.session_state.user_profile = {
            "company_name": "Demo Company",
            "email": st.session_state.user_email,
            "responsible_person_name": "",
            "responsible_person_contact": ""
        }
        st.session_state.page = "dashboard"
        st.experimental_rerun()

# --- Logout ---
def logout():
    st.session_state.user_email = None
    st.session_state.user_profile = {}
    st.session_state.page = "login"
    st.experimental_rerun()

# --- Profile Page ---
def profile_page():
    st.title("Profile Information")
    profile = st.session_state.user_profile
    st.text_input("Company Name", value=profile["company_name"], disabled=True)
    st.text_input("Email ID", value=profile["email"], disabled=True)
    resp_name = st.text_input("Responsible Person Name", value=profile["responsible_person_name"])
    resp_contact = st.text_input("Responsible Person Contact", value=profile["responsible_person_contact"])
    if st.button("Save Profile"):
        st.session_state.user_profile["responsible_person_name"] = resp_name
        st.session_state.user_profile["responsible_person_contact"] = resp_contact
        st.success("Profile updated successfully!")

# --- Dashboard Page ---
def dashboard_page():
    st.title("Einboard")
    st.markdown(f"Welcome **{st.session_state.user_email}**! Estimate Scope 1, 2, and 3 emissions for net zero journey.")

    # Sidebar - Add Activity
    st.sidebar.header("Add Activity Data")
    scope_options = emission_factors["scope"].dropna().unique()
    selected_scope = st.sidebar.selectbox("Select Scope", scope_options)
    filtered_df = emission_factors[emission_factors["scope"]==selected_scope]
    
    if selected_scope=="Scope 3":
        category_options = filtered_df["category"].dropna().unique()
        selected_category = st.sidebar.selectbox("Select Scope 3 Category", category_options)
        category_df = filtered_df[filtered_df["category"]==selected_category]
        activity_options = category_df["activity"].dropna().unique()
        selected_activity = st.sidebar.selectbox("Select Activity", activity_options)
        activity_df = category_df[category_df["activity"]==selected_activity]
    else:
        selected_category = "-"
        activity_options = filtered_df["activity"].dropna().unique()
        selected_activity = st.sidebar.selectbox("Select Activity", activity_options)
        activity_df = filtered_df[filtered_df["activity"]==selected_activity]

    if not activity_df.empty:
        unit = activity_df["unit"].values[0]
        ef = activity_df["emission_factor"].values[0]
    else:
        unit, ef = "-", 0

    quantity = st.sidebar.number_input(f"Enter quantity ({unit})", min_value=0.0, format="%.4f")
    if st.sidebar.button("Add Entry") and quantity>0 and ef>0:
        emissions = quantity*ef
        new_entry = {
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Scope": selected_scope,
            "Category": selected_category,
            "Activity": selected_activity,
            "Quantity": quantity,
            "Unit": unit,
            "Emission Factor": ef,
            "Emissions (tCO₂e)": emissions
        }
        st.session_state.emissions_log.append(new_entry)
        summary = {"Scope 1":0,"Scope 2":0,"Scope 3":0}
        for e in st.session_state.emissions_log:
            summary[e["Scope"]] += e["Emissions (tCO₂e)"]
        st.session_state.emissions_summary = summary

    # Dashboard Columns
    col1, col2 = st.columns([1,2])
    with col1:
        st.subheader("📅 Latest Emission Entry")
        if st.session_state.emissions_log:
            latest = st.session_state.emissions_log[-1]
            for k,v in latest.items():
                st.markdown(f"- {k}: {v}")
        else:
            st.info("No data yet.")
    with col2:
        st.subheader("📊 Emission Breakdown by Scope")
        chart_df = pd.DataFrame.from_dict(st.session_state.emissions_summary, orient="index", columns=["Emissions"])
        chart_df = chart_df.reset_index().rename(columns={"index":"Scope"})
        chart_df = chart_df[chart_df["Emissions"]>0]
        if not chart_df.empty:
            fig = px.pie(chart_df, names="Scope", values="Emissions", color_discrete_sequence=px.colors.sequential.Purples_r, hole=0.45)
            st.plotly_chart(fig, use_container_width=True)

    # Emissions Log & SharePoint Save
    if st.session_state.emissions_log:
        st.subheader("📂 Emissions Log")
        log_df = pd.DataFrame(st.session_state.emissions_log)
        log_df.index = range(1,len(log_df)+1)
        total_row = pd.DataFrame([{
            "Timestamp": "-",
            "Scope": "Total",
            "Category": "-",
            "Activity": "-",
            "Quantity": log_df["Quantity"].sum(),
            "Unit": "",
            "Emission Factor": "-",
            "Emissions (tCO₂e)": log_df["Emissions (tCO₂e)"].sum()
        }])
        final_df = pd.concat([log_df,total_row], ignore_index=True)
        st.dataframe(final_df, use_container_width=True)
        # Save to SharePoint
        try:
            csv_buffer = io.StringIO()
            log_df.to_csv(csv_buffer, index=False)
            csv_name = f"emissions_{st.session_state.user_email}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            ctx.web.get_folder_by_server_relative_url(TARGET_FOLDER).upload_file(csv_name, csv_buffer.getvalue().encode()).execute_query()
        except:
            st.error("Failed to save to SharePoint")

# --- Sidebar Bottom ---
if st.session_state.page != "login" and st.session_state.user_email:
    st.sidebar.markdown("---")
    if st.sidebar.button("Profile"):
        st.session_state.page = "profile"
    if st.sidebar.button("Logout"):
        logout()

# --- Page Routing ---
if st.session_state.page == "login":
    if not st.session_state.user_email:
        login_placeholder()
elif st.session_state.page == "profile":
    profile_page()
elif st.session_state.page == "dashboard":
    dashboard_page()
