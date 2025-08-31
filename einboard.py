import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io

# --- Page Config ---
st.set_page_config(page_title="EinTrust GHG Dashboard", page_icon="🌍", layout="wide")

# --- Custom CSS for Dark Professional Theme ---
st.markdown("""
    <style>
        .stApp {
            background-color: #121212;
            color: #ffffff;
        }
        .stMetric label, .stMarkdown, .stTextInput, .stSelectbox, .stNumberInput {
            color: #ffffff !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- Initialize Session State ---
if "emissions" not in st.session_state:
    st.session_state.emissions = []
if "archive" not in st.session_state:
    st.session_state.archive = None

# --- Functions ---
def get_fy(date: datetime):
    return date.year if date.month >= 4 else date.year - 1

def auto_archive():
    if st.session_state.emissions:
        df = pd.DataFrame(st.session_state.emissions)
        output = io.StringIO()
        df.to_csv(output, index=False)
        st.session_state.archive = output.getvalue().encode("utf-8")
        st.session_state.emissions = []

# Check if new financial year (April)
current_month = datetime.now().month
if current_month == 4 and st.session_state.emissions:
    auto_archive()

# --- Sidebar (UNCHANGED as per your request) ---
st.sidebar.title("Navigation")
st.sidebar.write("Use the options to navigate.")

# --- Main Content ---
st.title("EinTrust GHG Dashboard")
st.markdown("Estimate Scope 1, 2, and 3 emissions for net zero journey.")

# --- Data Entry ---
st.subheader("Add Activity Data")
with st.form("entry_form"):
    activity = st.text_input("Activity")
    scope = st.selectbox("Scope", ["Scope 1", "Scope 2", "Scope 3"])
    emissions = st.number_input("Emissions (tCO2e)", min_value=0.0, step=0.1)
    submitted = st.form_submit_button("Add Entry")
    if submitted and activity and emissions > 0:
        st.session_state.emissions.append({
            "date": datetime.now(),
            "activity": activity,
            "scope": scope,
            "emissions": emissions
        })

# --- Archive & Reset ---
if st.button("Archive & Reset"):
    auto_archive()

if st.session_state.archive:
    st.download_button("Download Last Archived Data (CSV)",
                       data=st.session_state.archive,
                       file_name="archived_emissions.csv",
                       mime="text/csv")

# --- Display Dashboard ---
if st.session_state.emissions:
    df = pd.DataFrame(st.session_state.emissions)

    # Convert emissions to Indian numbering system
    def format_in_indian_system(x):
        return f"{x:,.0f}".replace(",", "X").replace("X", ",")

    # --- Key Emission Indicators ---
    st.subheader("Key Emission Indicators")
    total_emissions = df["emissions"].sum()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Emissions (tCO2e)", format_in_indian_system(total_emissions))
    col2.metric("Scope 1", format_in_indian_system(df[df["scope"] == "Scope 1"]["emissions"].sum()))
    col3.metric("Scope 2", format_in_indian_system(df[df["scope"] == "Scope 2"]["emissions"].sum()))
    col4.metric("Scope 3", format_in_indian_system(df[df["scope"] == "Scope 3"]["emissions"].sum()))

    # --- Emission Breakdown by Scope (Pie Chart with theme colors) ---
    st.subheader("Emission Breakdown by Scope")
    pie = px.pie(df, names="scope", values="emissions",
                 color="scope",
                 color_discrete_map={
                     "Scope 1": "#1f77b4",
                     "Scope 2": "#ff7f0e",
                     "Scope 3": "#2ca02c"
                 })
    pie.update_layout(paper_bgcolor='#121212', plot_bgcolor='#121212', font_color="white")
    st.plotly_chart(pie, use_container_width=True)

    # --- Emissions Trend Over Time (Monthly Apr→Mar, stacked by scope) ---
    st.subheader("Emissions Trend Over Time (Monthly — Apr→Mar)")
    df["FY"] = df["date"].apply(get_fy)
    df["Month"] = df["date"].dt.month
    month_map = {4:"Apr",5:"May",6:"Jun",7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec",1:"Jan",2:"Feb",3:"Mar"}
    df["MonthName"] = df["Month"].map(month_map)
    trend = df.groupby(["FY","MonthName","scope"])["emissions"].sum().reset_index()
    trend["MonthName"] = pd.Categorical(trend["MonthName"], categories=["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"], ordered=True)
    trend = trend.sort_values(["FY","MonthName"])
    stacked_bar = px.bar(trend, x="MonthName", y="emissions", color="scope",
                         color_discrete_map={
                             "Scope 1": "#1f77b4",
                             "Scope 2": "#ff7f0e",
                             "Scope 3": "#2ca02c"
                         },
                         barmode="stack")
    stacked_bar.update_layout(paper_bgcolor='#121212', plot_bgcolor='#121212', font_color="white")
    st.plotly_chart(stacked_bar, use_container_width=True)

    # --- Emissions Log (Bottom) ---
    st.subheader("Emissions Log")
    st.dataframe(df[["date","activity","scope","emissions"]].sort_values("date", ascending=False), use_container_width=True)
