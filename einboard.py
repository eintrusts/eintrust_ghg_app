import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io

# --- Page Config ---
st.set_page_config(page_title="EinTrust GHG Dashboard", page_icon="🌍", layout="wide")

# --- Dark Theme CSS ---
st.markdown("""
    <style>
    .stApp {
        background-color: #121212;
        color: #e0e0e0;
        font-family: 'Segoe UI', sans-serif;
    }
    .stMetric {
        background-color: #1e1e1e;
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0px 0px 10px #00000055;
    }
    </style>
""", unsafe_allow_html=True)

# --- Initialize Session State ---
if "activity_data" not in st.session_state:
    st.session_state["activity_data"] = pd.DataFrame(columns=["Date", "Activity", "Scope", "Emission (kg CO2e)"])
if "archive" not in st.session_state:
    st.session_state["archive"] = None
if "last_reset" not in st.session_state:
    st.session_state["last_reset"] = None

# --- Helper: Get Apr–Mar Financial Year ---
def get_financial_year(date):
    year = date.year
    if date.month < 4:  # Before April → belongs to previous FY
        return f"{year-1}-{year}"
    else:
        return f"{year}-{year+1}"

# --- Auto Reset at April ---
today = datetime.today()
if today.month == 4 and today.day == 1:  # Auto reset on April 1st
    if not st.session_state["activity_data"].empty:
        csv_buffer = io.StringIO()
        st.session_state["activity_data"].to_csv(csv_buffer, index=False)
        st.session_state["archive"] = csv_buffer.getvalue()
        st.session_state["activity_data"] = pd.DataFrame(columns=["Date", "Activity", "Scope", "Emission (kg CO2e)"])
        st.session_state["last_reset"] = today.strftime("%d-%b-%Y")

# --- Title ---
st.title("🌍 EinTrust GHG Dashboard")
st.markdown("Energy-efficient, Apr–Mar cycle emissions tracking.")

# --- Activity Data Entry ---
st.header("➕ Add Activity Data")
col1, col2, col3, col4 = st.columns(4)
with col1:
    date = st.date_input("Date", datetime.today())
with col2:
    activity = st.text_input("Activity")
with col3:
    scope = st.selectbox("Scope", ["Scope 1", "Scope 2", "Scope 3"])
with col4:
    emission = st.number_input("Emission (kg CO2e)", min_value=0.0, step=0.1)

if st.button("Add Entry"):
    new_entry = pd.DataFrame([[date, activity, scope, emission]],
                             columns=["Date", "Activity", "Scope", "Emission (kg CO2e)"])
    st.session_state["activity_data"] = pd.concat([st.session_state["activity_data"], new_entry], ignore_index=True)

# --- Manual Archive & Reset ---
if st.button("Archive & Reset"):
    if not st.session_state["activity_data"].empty:
        csv_buffer = io.StringIO()
        st.session_state["activity_data"].to_csv(csv_buffer, index=False)
        st.session_state["archive"] = csv_buffer.getvalue()
        st.session_state["activity_data"] = pd.DataFrame(columns=["Date", "Activity", "Scope", "Emission (kg CO2e)"])
        st.session_state["last_reset"] = today.strftime("%d-%b-%Y")

# --- Archive Download ---
if st.session_state["archive"]:
    st.download_button(
        label="⬇️ Download Last Archive (CSV)",
        data=st.session_state["archive"],
        file_name=f"GHG_Archive_{st.session_state['last_reset']}.csv",
        mime="text/csv"
    )

# --- Key Emission Indicators ---
st.header("📊 Key Emission Indicators")
df = st.session_state["activity_data"]
if not df.empty:
    total = df["Emission (kg CO2e)"].sum()
    s1 = df[df["Scope"]=="Scope 1"]["Emission (kg CO2e)"].sum()
    s2 = df[df["Scope"]=="Scope 2"]["Emission (kg CO2e)"].sum()
    s3 = df[df["Scope"]=="Scope 3"]["Emission (kg CO2e)"].sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Emissions", f"{total:,.0f}".replace(",", ","))
    col2.metric("Scope 1", f"{s1:,.0f}".replace(",", ","))
    col3.metric("Scope 2", f"{s2:,.0f}".replace(",", ","))
    col4.metric("Scope 3", f"{s3:,.0f}".replace(",", ","))

    # --- Emission Breakdown by Scope ---
    st.subheader("🟢 Emission Breakdown by Scope")
    pie_fig = px.pie(df, values="Emission (kg CO2e)", names="Scope",
                     hole=0.4, template="plotly_dark")
    st.plotly_chart(pie_fig, use_container_width=True)

    # --- Emissions Trend (Stacked, Apr–Mar cycle) ---
    st.subheader("📈 Emissions Trend Over Time (Monthly — Apr→Mar)")
    df["Date"] = pd.to_datetime(df["Date"])
    df["Month"] = df["Date"].dt.to_period("M").astype(str)

    # Create custom Apr–Mar month order
    months_order = ["04", "05", "06", "07", "08", "09", "10", "11", "12", "01", "02", "03"]
    month_map = {m: i for i, m in enumerate(months_order)}

    df["Month_Num"] = df["Date"].dt.strftime("%m")
    df["Month_Order"] = df["Month_Num"].map(month_map)
    df["Month_Label"] = df["Date"].dt.strftime("%b")

    monthly = df.groupby(["Month_Order", "Month_Label", "Scope"])["Emission (kg CO2e)"].sum().reset_index()
    monthly = monthly.sort_values("Month_Order")

    bar_fig = px.bar(monthly, x="Month_Label", y="Emission (kg CO2e)", color="Scope",
                     template="plotly_dark", barmode="stack")
    st.plotly_chart(bar_fig, use_container_width=True)

# --- Emissions Log (Bottom) ---
st.header("📜 Emissions Log")
st.dataframe(st.session_state["activity_data"], use_container_width=True)
