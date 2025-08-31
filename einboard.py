import streamlit as st

# --- Page Config ---
st.set_page_config(page_title="EinTrust ESG Dashboard", page_icon="🌍", layout="wide")

# --- Custom CSS for Theme ---
st.markdown("""
    <style>
        body {
            background-color: #1e2d24; /* dark greenish background */
            color: #e8f5e9; /* light text */
        }
        .sidebar .sidebar-content {
            background-color: #13322b; /* dark sidebar */
        }
        h1, h2, h3, h4 {
            color: #a3d9a5; /* light green headers */
        }
        .st-expanderHeader {
            font-weight: bold;
            color: #64b5f6 !important; /* royal blue for expander titles */
        }
    </style>
""", unsafe_allow_html=True)

# --- Title ---
st.title("🌍 EinTrust ESG Dashboard")

st.markdown("A structured ESG data collection and tracking platform for clients.")

# --- ESG Sections ---
st.header("E - Environment")
with st.expander("🌱 GHG Emissions"):
    st.number_input("Total GHG emissions (tCO₂e)", min_value=0, step=1)
    st.text_area("Notes / Assumptions")
    st.file_uploader("Upload supporting document", type=["csv","xlsx","pdf"])

with st.expander("⚡ Energy"):
    st.number_input("Total Energy Consumption (kWh)", min_value=0, step=100)
    st.number_input("Renewable Energy Share (%)", min_value=0, max_value=100, step=1)
    st.text_area("Notes")

with st.expander("💧 Water"):
    st.number_input("Total Water Withdrawal (m³)", min_value=0, step=100)
    st.number_input("Water Recycled (%)", min_value=0, max_value=100, step=1)

with st.expander("♻ Waste"):
    st.number_input("Total Waste Generated (tons)", min_value=0, step=1)
    st.number_input("Waste Recycled (%)", min_value=0, max_value=100, step=1)

with st.expander("🌿 Biodiversity"):
    st.text_area("Biodiversity initiatives/projects")
    st.file_uploader("Upload biodiversity-related reports", type=["pdf","docx"])


st.header("S - Social")
with st.expander("👥 Employees"):
    st.number_input("Total Employees", min_value=0, step=1)
    st.number_input("Training Hours per Employee", min_value=0, step=1)

with st.expander("⚕ Health & Safety"):
    st.number_input("Total Incidents", min_value=0, step=1)
    st.number_input("Lost Time Injury Frequency Rate (LTIFR)", min_value=0, step=1)

with st.expander("🤝 CSR"):
    st.number_input("CSR Spend (₹)", min_value=0, step=1000)
    st.text_area("CSR Projects Overview")


st.header("G - Governance")
with st.expander("🏛 Board"):
    st.number_input("Total Board Members", min_value=0, step=1)
    st.number_input("Independent Directors (%)", min_value=0, max_value=100, step=1)

with st.expander("📜 Policies"):
    st.text_area("List of Key Policies (Code of Conduct, ESG Policy, etc.)")

with st.expander("✔ Compliance"):
    st.text_area("Compliance Certifications (ISO, SEBI-BRR, etc.)")
    st.file_uploader("Upload Compliance Documents", type=["pdf","docx"])

with st.expander("⚖ Risk Management"):
    st.text_area("Key ESG Risks Identified")
    st.text_area("Mitigation Measures")

# --- Save Button ---
if st.button("💾 Save ESG Data"):
    st.success("Data saved successfully (placeholder).")
