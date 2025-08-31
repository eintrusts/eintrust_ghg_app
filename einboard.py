import streamlit as st
import pandas as pd
import plotly.express as px

# --- Page Config ---
st.set_page_config(page_title="EinTrust GHG Dashboard", page_icon="🌍", layout="wide")

# --- Sidebar Navigation ---
st.sidebar.title("Navigation")
menu = st.sidebar.radio("Go to:", ["Input Data", "ESG Dashboard"])

# --- Data Storage Placeholder ---
if "esg_data" not in st.session_state:
    st.session_state["esg_data"] = {
        "Environment": {},
        "Social": {},
        "Governance": {}
    }

# ---------------------- INPUT DATA TAB ----------------------
if menu == "Input Data":
    st.title("📊 ESG Data Input")
    st.markdown("Please enter your organization's ESG data below:")

    # Environment Section
    with st.expander("🌱 Environment"):
        st.session_state["esg_data"]["Environment"]["GHG Emissions"] = st.number_input("Total GHG Emissions (tCO2e)", min_value=0.0)
        st.session_state["esg_data"]["Environment"]["Energy Consumption"] = st.number_input("Total Energy Consumption (MWh)", min_value=0.0)
        st.session_state["esg_data"]["Environment"]["Water Consumption"] = st.number_input("Total Water Withdrawal (ML)", min_value=0.0)
        st.session_state["esg_data"]["Environment"]["Waste Generated"] = st.number_input("Total Waste Generated (tons)", min_value=0.0)
        st.session_state["esg_data"]["Environment"]["Biodiversity Initiatives"] = st.text_area("Biodiversity Initiatives")

    # Social Section
    with st.expander("👥 Social"):
        st.session_state["esg_data"]["Social"]["Employees"] = st.number_input("Total Employees", min_value=0)
        st.session_state["esg_data"]["Social"]["Health & Safety"] = st.text_area("Health & Safety Measures")
        st.session_state["esg_data"]["Social"]["CSR Initiatives"] = st.text_area("CSR Initiatives")

    # Governance Section
    with st.expander("🏛 Governance"):
        st.session_state["esg_data"]["Governance"]["Board Composition"] = st.text_area("Board Composition")
        st.session_state["esg_data"]["Governance"]["Policies"] = st.text_area("Key Policies")
        st.session_state["esg_data"]["Governance"]["Compliance"] = st.text_area("Compliance Mechanisms")
        st.session_state["esg_data"]["Governance"]["Risk Management"] = st.text_area("Risk Management Approach")

    st.success("Data saved in session. Switch to 'ESG Dashboard' to view results.")

# ---------------------- ESG DASHBOARD TAB ----------------------
elif menu == "ESG Dashboard":
    st.title("📈 ESG Dashboard")
    esg_data = st.session_state["esg_data"]

    # Show Environment Data
    st.subheader("🌱 Environment")
    st.write(esg_data["Environment"])

    # Show Social Data
    st.subheader("👥 Social")
    st.write(esg_data["Social"])

    # Show Governance Data
    st.subheader("🏛 Governance")
    st.write(esg_data["Governance"])

    # Example visualization: Environment numeric indicators
    env_numeric = {k: v for k, v in esg_data["Environment"].items() if isinstance(v, (int, float))}
    if env_numeric:
        df_env = pd.DataFrame(list(env_numeric.items()), columns=["Indicator", "Value"])
        fig = px.bar(df_env, x="Indicator", y="Value", title="Environment Indicators")
        st.plotly_chart(fig, use_container_width=True)
