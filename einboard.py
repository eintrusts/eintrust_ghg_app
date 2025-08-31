# ---------------------------
# SDG Engagement Calculation
# ---------------------------
def calculate_sdg_engagement():
    """
    Dynamically calculate SDG engagement based on real data.
    """
    sdg_engagement = {sdg:0 for sdg in SDG_LIST}

    # --- SDG 7: Affordable & Clean Energy ---
    renewable_df = st.session_state.renewable_entries
    total_renewable_energy = renewable_df["Energy_kWh"].sum() if not renewable_df.empty else 0
    benchmark_renewable = 100000  # Example benchmark
    sdg_engagement["Affordable & Clean Energy"] = min(100, (total_renewable_energy / benchmark_renewable)*100)

    # --- SDG 12: Responsible Consumption & Production ---
    fossil_energy = st.session_state.entries[st.session_state.entries["Scope"].isin(["Scope 1","Scope 2"])]["Quantity"].sum() if not st.session_state.entries.empty else 0
    benchmark_fossil = 50000  # Example benchmark
    sdg_engagement["Responsible Consumption & Production"] = min(100, (fossil_energy / benchmark_fossil)*100)

    # --- SDG 13: Climate Action ---
    total_ghg = st.session_state.entries["Quantity"].sum() if not st.session_state.entries.empty else 0
    benchmark_ghg = 10000  # Example benchmark in tCO2e
    sdg_engagement["Climate Action"] = min(100, (total_ghg / benchmark_ghg)*100)

    # Other SDGs can have placeholder random values or zero
    for sdg in SDG_LIST:
        if sdg not in sdg_engagement:
            sdg_engagement[sdg] = 0

    return sdg_engagement
