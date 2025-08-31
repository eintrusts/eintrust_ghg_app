import streamlit as st
import pandas as pd
import plotly.express as px

# --- Page Config ---
st.set_page_config(
    page_title="EinTrust ESG & GHG Dashboard",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom Theme Styling ---
st.markdown("""
    <style>
    body {
        background-color: #f4fdf7;
    }
    .stMetric {
        background-color: #e8f9f1;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0px 2px 6px rgba(0,0,0,0.05);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 16px;
        padding: 12px 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Load Emission Factors ---
@st.cache_data
def load_emission_factors():
    try:
        return pd.read_csv("emission_factors.csv")
    except:
        # fallback mock
        return pd.DataFrame({
            "Activity": ["Electricity", "Diesel", "Petrol", "Flight", "Waste", "Water"],
            "Factor": [0.82, 2.68, 2.31, 0.15, 1.20, 0.34],  # kgCO2e/unit
            "Unit": ["kWh", "litre", "litre", "km", "kg", "kL"]
        })

emission_factors = load_emission_factors()

# --- Sidebar Navigation ---
tabs = st.sidebar.radio("📂 Navigation", ["GHG Entry", "Dashboard"])

# --- Initialize session state ---
if "activity_data" not in st.session_state:
    st.session_state.activity_data = {}

# --- Tab 1: GHG Entry ---
if tabs == "GHG Entry":
    st.title("🌱 GHG Activity Data Entry")
    st.markdown("Enter your activity data below. The system will auto-calculate Scope 1, 2, and 3 emissions.")

    with st.form("ghg_form"):
        electricity = st.number_input("Electricity Consumption (kWh)", min_value=0.0, step=0.1)
        diesel = st.number_input("Diesel Consumption (litres)", min_value=0.0, step=0.1)
        petrol = st.number_input("Petrol Consumption (litres)", min_value=0.0, step=0.1)
        travel = st.number_input("Business Travel (Flight km)", min_value=0.0, step=0.1)
        waste = st.number_input("Waste Generated (kg)", min_value=0.0, step=0.1)
        water = st.number_input("Water Consumed (kL)", min_value=0.0, step=0.1)

        submitted = st.form_submit_button("Save Data")

        if submitted:
            st.session_state.activity_data = {
                "Electricity": electricity,
                "Diesel": diesel,
                "Petrol": petrol,
                "Flight": travel,
                "Waste": waste,
                "Water": water
            }
            st.success("✅ Data saved successfully!")

# --- Tab 2: Dashboard ---
elif tabs == "Dashboard":
    st.title("📊 ESG & GHG Dashboard")

    if not st.session_state.activity_data:
        st.warning("⚠️ Please enter activity data in 'GHG Entry' first.")
    else:
        # --- Calculate Emissions ---
        df_input = pd.DataFrame(list(st.session_state.activity_data.items()), columns=["Activity", "Value"])
        df = pd.merge(df_input, emission_factors, on="Activity")
        df["Emissions (kgCO2e)"] = df["Value"] * df["Factor"]

        total_emissions = df["Emissions (kgCO2e)"].sum() / 1000  # tCO2e
        energy_use = st.session_state.activity_data["Electricity"] + st.session_state.activity_data["Diesel"]*10 + st.session_state.activity_data["Petrol"]*9
        water_use = st.session_state.activity_data["Water"]
        waste_gen = st.session_state.activity_data["Waste"]

        # --- KPIs ---
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🌍 Total Emissions", f"{total_emissions:.2f} tCO₂e")
        col2.metric("⚡ Energy Usage", f"{energy_use:.1f} units")
        col3.metric("💧 Water Usage", f"{water_use:.1f} kL")
        col4.metric("🗑️ Waste Generated", f"{waste_gen:.1f} kg")

        # --- Charts ---
        pie_chart = px.pie(df, names="Activity", values="Emissions (kgCO2e)",
                           title="Emission Split by Activity", hole=0.4,
                           color_discrete_sequence=px.colors.sequential.Greens)
        bar_chart = px.bar(df, x="Activity", y="Emissions (kgCO2e)",
                           title="Emissions by Category",
                           color="Activity", color_discrete_sequence=px.colors.sequential.Greens)

        st.plotly_chart(pie_chart, use_container_width=True)
        st.plotly_chart(bar_chart, use_container_width=True)

        # --- ESG Expanders ---
        st.subheader("📌 ESG Breakdown")

        with st.expander("🌱 Environment"):
            st.write(f"**GHG Emissions:** {total_emissions:.2f} tCO₂e")
            st.write(f"**Energy Use:** {energy_use:.1f} units")
            st.write(f"**Water Use:** {water_use:.1f} kL")
            st.write(f"**Waste:** {waste_gen:.1f} kg")

        with st.expander("🤝 Social"):
            st.write("Derived from activity data:")
            st.write("- Employee travel impact considered under Scope 3 (Flight).")
            st.write("- Resource use indirectly linked to employee well-being & efficiency.")

        with st.expander("🏛️ Governance"):
            st.write("Automated indicators:")
            st.write("- Compliance reflected in tracked GHG activities.")
            st.write("- Data transparency ensured via structured reporting.")

