import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Load data
@st.cache_data
def load_data():
    try:
        base = os.path.join(os.path.dirname(__file__), "..", "..")
        users_df = pd.read_csv(os.path.join(base, "data/processed/users.csv"))
        repos_df = pd.read_csv(os.path.join(base, "data/processed/repositories.csv"))
        classifications_df = pd.read_csv(os.path.join(base, "data/processed/classifications.csv"))
        return users_df, repos_df, classifications_df
    except FileNotFoundError:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

users_df, repos_df, classifications_df = load_data()

if users_df.empty:
    st.warning("⚠️ No data found in `data/` directory. Please run the extraction script first.")
    st.stop()

st.title("Peru Developer Ecosystem Overview")

# Key metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Developers", len(users_df))
with col2:
    st.metric("Total Repositories", len(repos_df))
with col3:
    st.metric("Total Stars", repos_df["stargazers_count"].sum())
with col4:
    active_pct = (users_df["is_active"].sum() / len(users_df)) * 100 if len(users_df) > 0 else 0
    st.metric("Active Developers", f"{active_pct:.1f}%")

# Charts
col1, col2 = st.columns(2)

with col1:
    st.subheader("Top 10 Developers by Impact")
    top_devs = users_df.nlargest(10, "impact_score")[["login", "impact_score"]]
    fig = px.bar(top_devs, x="login", y="impact_score", color="impact_score",
                 color_continuous_scale="Viridis")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    if not classifications_df.empty:
        st.subheader("Industry Distribution")
        industry_counts = classifications_df["industry_name"].value_counts()
        fig = px.pie(values=industry_counts.values, names=industry_counts.index, hole=.3)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No classification data available to display industry distribution.")
