import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- Page Config ---
st.set_page_config(page_title="EinTrust GHG Dashboard", page_icon="🌍", layout="wide")

# --- Custom Styling ---
st.markdown("""
    <style>
        /* Global Background */
        body, .stApp {
            background-color: #0f1f1f; /* Dark teal for energy-saving mode */
            color: #e0f2f1; /* Light text for readability */
            font-family: 'Helvetica', sans-serif;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #163020; /* Forest green sidebar */
            color: #e0f2f1;
        }

        section[data-testid="stSidebar"] * {
            color: #e0f2f1 !important;
        }

        /* Titles */
        h1, h2, h3, h4 {
            color: #6EC207 !important; /* Fresh Green */
        }

        /* Metric cards */
        div[data-testid="stMetricValue"] {
            color: #6EC207 !important; /* Green metrics */
            font-weight: bold;
        }

        /* Buttons */
        .stButton>button {
            background-color: #1E3D59;
            color: white;
            border-radius: 8px;
            border: none;
        }
        .stButton>button:hover {
            background-color: #163020;
            color: #6EC207;
        }
    </style>
""", unsafe_allow_html=True)

# --- Sidebar Logo ---
st.sidebar.image("https://avatars.githubusercontent.com/u/181635316?s=200&v=4", use_column_width=True)

# --- Sidebar Navigation ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard"])

# --- Dashboard Page ---
if page == "Dashboard":
    st.title("🌍 EinTrust GHG Dashboard")
    st.markdown("### Estimate Scope 1, 2, and 3 emissions for your Net Zero journey")

    # --- Input Section ---
    st.subheader("Activity Input")
    activity_type = st.selectbox("Select Activity", ["Electricity", "Fuel", "Travel", "Waste"])
    quantity = st.number_input("Enter Quantity", min_value=0.0, format="%.2f")
    unit = st.text_input("Unit (e.g., kWh, liters, km, kg)")
    add_btn = st.button("Add Entry")

    # --- Session State for Data ---
    if "data" not in st.session_state:
        st.session_state.data = pd.DataFrame(columns=["Date", "Activity", "Quantity", "Unit", "Emissions (kgCO2e)"])

    # --- Emission Factors (simplified demo values) ---
    emission_factors = {
        "Electricity": 0.82,  # kg CO2e/kWh (India avg)
        "Fuel": 2.68,        # kg CO2e/liter diesel
        "Travel": 0.15,      # kg CO2e/km (car avg)
        "Waste": 1.20        # kg CO2e/kg waste
    }

    # --- Add Entry ---
    if add_btn and quantity > 0:
        emissions = quantity * emission_factors.get(activity_type, 0)
        new_row = pd.DataFrame({
            "Date": [datetime.now().strftime("%Y-%m-%d %H:%M")],
            "Activity": [activity_type],
            "Quantity": [quantity],
            "Unit": [unit],
            "Emissions (kgCO2e)": [round(emissions, 2)]
        })
        st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
        st.success("✅ Entry added successfully!")

    # --- Dashboard View ---
    st.subheader("Emissions Overview")

    if not st.session_state.data.empty:
        total_emissions = st.session_state.data["Emissions (kgCO2e)"].sum()

        # Metrics
        col1, col2 = st.columns(2)
        col1.metric("Total Entries", len(st.session_state.data))
        col2.metric("Total Emissions", f"{total_emissions:.2f} kgCO2e")

        # Chart
        fig = px.bar(
            st.session_state.data,
            x="Activity", y="Emissions (kgCO2e)",
            color="Activity",
            title="Emissions by Activity",
            template="plotly_dark"
        )
        st.plotly_chart(fig, use_container_width=True)

        # Table
        st.dataframe(st.session_state.data, use_container_width=True)
    else:
        st.info("No activity added yet. Start by entering your first activity above.")
