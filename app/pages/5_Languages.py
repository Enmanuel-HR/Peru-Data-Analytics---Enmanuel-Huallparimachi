import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Languages - GitHub Peru", page_icon="🇵🇪", layout="wide")
st.title("Language Analytics")

@st.cache_data
def load_data():
    try:
        repos_df = pd.read_csv("data/processed/repositories.csv")
        return repos_df
    except FileNotFoundError:
        return pd.DataFrame()

repos_df = load_data()

if not repos_df.empty and "primary_language" in repos_df.columns:
    valid_repos = repos_df.dropna(subset=["primary_language"])
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Repositories with Language Data", len(valid_repos))
    with col2:
        st.metric("Unique Languages", valid_repos["primary_language"].nunique())
        
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Language Distribution (Top 15)")
        lang_counts = valid_repos["primary_language"].value_counts().head(15).reset_index()
        lang_counts.columns = ["Language", "Count"]
        
        fig = px.pie(
            lang_counts, 
            values="Count", 
            names="Language", 
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.subheader("Language Impact (Total Stars)")
        lang_stars = valid_repos.groupby("primary_language")["stargazers_count"].sum().reset_index()
        lang_stars = lang_stars[lang_stars["stargazers_count"] > 0].nlargest(15, "stargazers_count")
        
        fig2 = px.bar(
            lang_stars,
            x="primary_language",
            y="stargazers_count",
            log_y=True,
            labels={"primary_language": "Language", "stargazers_count": "Total Stars (Log Scale)"},
            color="stargazers_count",
            color_continuous_scale="Viridis"
        )
        fig2.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig2, use_container_width=True)
        
    st.subheader("Language Statistics")
    lang_stats = valid_repos.groupby("primary_language").agg(
        Repositories=("id", "count"),
        Total_Stars=("stargazers_count", "sum"),
        Avg_Stars=("stargazers_count", "mean"),
        Total_Forks=("forks_count", "sum")
    ).reset_index().sort_values("Repositories", ascending=False)
    
    lang_stats["Avg_Stars"] = lang_stats["Avg_Stars"].round(1)
    
    st.dataframe(lang_stats, use_container_width=True)
else:
     st.warning("Language data not available in repositories database.")
