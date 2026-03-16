import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Developers - GitHub Peru", page_icon="🇵🇪", layout="wide")
st.title("Developer Explorer")

@st.cache_data
def load_data():
    try:
        users_df = pd.read_csv("data/processed/users.csv")
        return users_df
    except FileNotFoundError:
        return pd.DataFrame()

users_df = load_data()

if not users_df.empty:
    col1, col2, col3 = st.columns(3)
    with col1:
        min_stars = st.slider("Minimum Stars", 0, 1000, 0)
    with col2:
        all_langs = users_df["primary_language_1"].dropna().unique() if "primary_language_1" in users_df.columns else []
        language_filter = st.multiselect("Primary Language", options=all_langs)
    with col3:
        active_only = st.checkbox("Active developers only")

    filtered_df = users_df.copy()
    if min_stars > 0:
        filtered_df = filtered_df[filtered_df["total_stars_received"] >= min_stars]
    if language_filter:
        filtered_df = filtered_df[filtered_df["primary_language_1"].isin(language_filter)]
    if active_only:
        filtered_df = filtered_df[filtered_df["is_active"] == True]

    display_cols = ["login", "name", "total_repos", "total_stars_received", "followers", "impact_score", "primary_language_1"]
    available_cols = [c for c in display_cols if c in filtered_df.columns]
    
    st.dataframe(filtered_df[available_cols], use_container_width=True)
else:
    st.warning("⚠️ No data found. Please run the extraction script first.")
