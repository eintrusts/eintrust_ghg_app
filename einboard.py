import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit_authenticator as stauth
from datetime import datetime
from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.user_credential import UserCredential
import io

# ---------------- LOGIN ----------------
credentials = {
    "usernames": {
        "client1": {"name": "Client One", "password": "123"},
        "client2": {"name": "Client Two", "password": "456"}
    }
}

authenticator = stauth.Authenticate(
    credentials,
    "einboard_cookie",
    "secret_key",
    cookie_expiry_days=1
)

name, authentication_status, username = authenticator.login("Login", location="main")

if authentication_status == False:
    st.error("Username/password incorrect")
    st.stop()
elif authentication_status == None:
    st.warning("Please enter your username and password")
    st.stop()
else:
    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"Welcome {name} 👋")

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="EinTrust GHG Dashboard", page_icon="🌍", layout="wide")
st.title("Einboard")
st.markdown("Estimate Scope 1, 2, and 3 emissions for net zero journey.")

# ---------------- LOAD EMISSION FACTORS ----------------
try:
    emission_factors = pd.read_csv("emission_factors.csv")
except FileNotFoundError:
    st.error("emission_factors.csv not found.")
    emission_factors = pd.DataFrame(columns=["scope","category","activity","unit","emission_factor","cost_per_unit_inr"])

# ---------------- SESSION STATE ----------------
if "emissions_summary" not in st.session_state:
    st.session_state.emissions_summary = {"Scope 1":0, "Scope 2":0, "Scope 3":0}
if "emissions_log" not in st.session_state:
    st.session_state.emissions_log = []

# ---------------- SIDEBAR NAVIGATION ----------------
nav_choice = st.sidebar.radio("Navigation", ["Dashboard", "Input CSV"], index=1)

# ---------------- CSV UPLOAD ----------------
if nav_choice == "Input CSV":
    st.header("Upload Activity Data")
    st.markdown("CSV columns required: Scope, Category, Activity, Quantity")
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            required_cols = {"Scope","Category","Activity","Quantity"}
            if not required_cols.issubset(df.columns):
                st.error(f"CSV must have columns: {required_cols}")
            else:
                for _, row in df.iterrows():
                    scope = row["Scope"]
                    category = row.get("Category","-")
                    activity = row["Activity"]
                    quantity = float(row["Quantity"])
                    
                    ef_df = emission_factors[(emission_factors["scope"]==scope) & (emission_factors["activity"]==activity)]
                    if scope=="Scope 3":
                        ef_df = ef_df[ef_df["category"]==category]
                    if not ef_df.empty:
                        ef = ef_df["emission_factor"].values[0]
                        unit = ef_df["unit"].values[0]
                        emissions = quantity*ef
                        entry = {
                            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "Scope": scope,
                            "Category": category,
                            "Activity": activity,
                            "Quantity": quantity,
                            "Unit": unit,
                            "Emission Factor": ef,
                            "Emissions (tCO₂e)": emissions
                        }
                        st.session_state.emissions_log.append(entry)
                # Update summary
                summary = {"Scope 1":0,"Scope 2":0,"Scope 3":0}
                for e in st.session_state.emissions_log:
                    summary[e["Scope"]] += e["Emissions (tCO₂e)"]
                st.session_state.emissions_summary = summary
                st.success("CSV processed successfully!")
        except Exception as e:
            st.error(f"Failed to process CSV: {e}")

# ---------------- DASHBOARD ----------------
else:
    st.sidebar.header("Add Activity Data")
    add_mode = st.sidebar.checkbox("➕ Add Entry Mode", value=False)

    if add_mode:
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
            st.warning(f"No emission factor found for activity: {selected_activity}")
            unit = "-"
            ef = 0

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
    col1,col2 = st.columns([1,2])
    with col1:
        st.subheader("📅 Latest Emission Entry")
        if st.session_state.emissions_log:
            latest = st.session_state.emissions_log[-1]
            for k,v in latest.items():
                st.markdown(f"- {k}: {v}")
        else:
            st.info("No data yet. Add from sidebar or upload CSV.")

    with col2:
        st.subheader("📊 Emission Breakdown by Scope")
        chart_df = pd.DataFrame.from_dict(st.session_state.emissions_summary, orient="index", columns=["Emissions"]).reset_index().rename(columns={"index":"Scope"})
        chart_df = chart_df[chart_df["Emissions"]>0]
        if not chart_df.empty:
            fig = px.pie(chart_df, names="Scope", values="Emissions", color_discrete_sequence=px.colors.sequential.Purples_r, hole=0.45)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data to show chart.")

    # Emission Log
    if st.session_state.emissions_log:
        st.subheader("📂 Emissions Log")
        log_df = pd.DataFrame(st.session_state.emissions_log)
        log_df.index = range(1,len(log_df)+1)
        total_row = pd.DataFrame([{
            "Timestamp":"-",
            "Scope":"Total",
            "Category":"-",
            "Activity":"-",
            "Quantity":log_df["Quantity"].sum(),
            "Unit":"",
            "Emission Factor":"-",
            "Emissions (tCO₂e)":log_df["Emissions (tCO₂e)"].sum()
        }])
        final_df = pd.concat([log_df,total_row], ignore_index=True)
        final_df.index = range(1,len(final_df)+1)
        st.dataframe(final_df, use_container_width=True)

        # ---------------- SAVE TO SHAREPOINT ----------------
        try:
            sharepoint_url = "https://eintrusts.sharepoint.com/sites/EinTrust"
            relative_url = "/sites/EinTrust/Shared Documents/einboard-data"
            ctx = ClientContext(sharepoint_url).with_credentials(
                UserCredential("mrkharat@eintrusts.com", "Eintrust@2025")
            )
            file_name = f"{username}_emissions.xlsx"
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                pd.DataFrame(st.session_state.emissions_log).to_excel(writer, index=False)
            buffer.seek(0)
            ctx.web.get_folder_by_server_relative_url(relative_url).upload_file(file_name, buffer.getvalue())
            ctx.execute_query()
            st.success("✅ Data saved to SharePoint successfully!")
        except Exception as e:
            st.error(f"❌ Could not save to SharePoint: {e}")
