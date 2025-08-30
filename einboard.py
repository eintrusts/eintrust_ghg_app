import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.user_credential import UserCredential
import io

# ---------------- LOGIN SYSTEM ----------------
# Dummy credentials (you can add more users here)
credentials = {
    "usernames": {
        "client1": {
            "name": "Client One",
            "password": "password1"
        },
        "client2": {
            "name": "Client Two",
            "password": "password2"
        }
    }
}

authenticator = stauth.Authenticate(
    credentials,
    "eintrust_dashboard",   # cookie name
    "abcdef",               # signature key
    cookie_expiry_days=1
)

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status == False:
    st.error("Username/password is incorrect")
elif authentication_status == None:
    st.warning("Please enter your username and password")
elif authentication_status:
    # Show logout button
    authenticator.logout("Logout", "sidebar")
    st.sidebar.write(f"Welcome {name} 👋")

    # ---------------- DASHBOARD ----------------
    st.title("EinTrust GHG Dashboard")
    st.write("Enter your activity data below:")

    # Example input form
    with st.form("input_form"):
        electricity = st.number_input("Electricity Consumption (kWh)", min_value=0.0, step=0.1)
        diesel = st.number_input("Diesel Consumption (Litres)", min_value=0.0, step=0.1)
        submit = st.form_submit_button("Save Data")

    if submit:
        # Create dataframe
        df = pd.DataFrame({
            "Username": [username],
            "Electricity_kWh": [electricity],
            "Diesel_Litre": [diesel]
        })

        # ---------------- SAVE TO SHAREPOINT ----------------
        try:
            sharepoint_url = "https://yourtenant.sharepoint.com/sites/yoursite"
            relative_url = "/sites/yoursite/Shared Documents/eintrust-data"

            ctx = ClientContext(sharepoint_url).with_credentials(
                UserCredential("your_email@yourtenant.onmicrosoft.com", "your_password")
            )

            file_name = f"{username}_data.xlsx"
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df.to_excel(writer, index=False)

            target_file_url = f"{relative_url}/{file_name}"
            ctx.web.get_folder_by_server_relative_url(relative_url).upload_file(file_name, buffer.getvalue())
            ctx.execute_query()

            st.success("✅ Data saved to SharePoint successfully!")
        except Exception as e:
            st.error(f"❌ Could not save to SharePoint: {e}")

        # Show data on dashboard
        st.subheader("Your Submitted Data")
        st.dataframe(df)
