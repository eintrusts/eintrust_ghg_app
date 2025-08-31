import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io
from office365.runtime.auth.user_credential import UserCredential
from office365.sharepoint.client_context import ClientContext

# OAuth imports
from authlib.integrations.requests_client import OAuth2Session
from urllib.parse import urlparse, parse_qs

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

# --- OAuth Config ---
CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID"
CLIENT_SECRET = "YOUR_GOOGLE_CLIENT_SECRET"
REDIRECT_URI = "http://localhost:8501"  # Change if deployed
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPE = ["openid", "email", "profile"]

def google_login():
    if "oauth_state" not in st.session_state:
        # Create OAuth session
        oauth = OAuth2Session(CLIENT_ID, CLIENT_SECRET, scope=SCOPE, redirect_uri=REDIRECT_URI)
        uri, state = oauth.create_authorization_url(AUTH_URL, access_type="offline", prompt="select_account")
        st.session_state.oauth_state = state
        st.markdown(f"[Login with Google]({uri})")
        st.stop()
    else:
        # Parse the response from redirect
        query_params = parse_qs(urlparse(st.experimental_get_query_params().get("url","")).query)
        if "code" in query_params:
            code = query_params["code"][0]
            oauth = OAuth2Session(CLIENT_ID, CLIENT_SECRET, scope=SCOPE, redirect_uri=REDIRECT_URI)
            token = oauth.fetch_token(TOKEN_URL, code=code)
            userinfo = oauth.get("https://www.googleapis.com/oauth2/v3/userinfo").json()
            st.session_state.user_email = userinfo["email"]
            if not st.session_state.user_profile:
                st.session_state.user_profile = {
                    "company_name": "Your Company",
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
            "Timestamp":"-","Scope":"Total","Category":"-","Activity":"-",
            "Quantity":log_df["Quantity"].sum(),"Unit":"","Emissi_
