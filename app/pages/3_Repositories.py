import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Repositories - GitHub Peru", page_icon="🇵🇪", layout="wide")
st.title("Repository Explorer")

@st.cache_data
def load_data():
    try:
        users_df = pd.read_csv("data/processed/users.csv")
        repos_df = pd.read_csv("data/processed/repositories.csv")
        return users_df, repos_df
    except FileNotFoundError:
        return pd.DataFrame(), pd.DataFrame()

users_df, repos_df = load_data()

if not users_df.empty and not repos_df.empty:
    user_mapping = dict(zip(users_df["id"], users_df["login"]))
    repos_display_df = repos_df.copy()
    repos_display_df["owner_login"] = repos_display_df["owner_id"].map(user_mapping)
    
    col1, col2 = st.columns(2)
    with col1:
        min_repo_stars = st.slider("Minimum Repo Stars", 0, int(repos_display_df["stargazers_count"].max()), 0)
    with col2:
        all_repo_langs = repos_display_df["primary_language"].dropna().unique()
        repo_lang_filter = st.multiselect("Repository Language", options=all_repo_langs)
        
    filtered_repos = repos_display_df.copy()
    if min_repo_stars > 0:
        filtered_repos = filtered_repos[filtered_repos["stargazers_count"] >= min_repo_stars]
    if repo_lang_filter:
        filtered_repos = filtered_repos[filtered_repos["primary_language"].isin(repo_lang_filter)]
        
    st.subheader(f"Showing {len(filtered_repos)} Repositories")
    
    display_cols = ["owner_login", "name", "description", "primary_language", 
                   "stargazers_count", "forks_count", "open_issues_count"]
    available_cols = [c for c in display_cols if c in filtered_repos.columns]
    
    st.dataframe(filtered_repos[available_cols], use_container_width=True)
    
    if not filtered_repos.empty:
        st.subheader("Top 10 Repositories by Stars")
        top_repos = filtered_repos.nlargest(10, "stargazers_count")
        top_repos["display_name"] = top_repos["owner_login"] + "/" + top_repos["name"]
        
        fig = px.bar(
            top_repos, x="display_name", y="stargazers_count", color="primary_language",
            labels={"display_name": "Repository", "stargazers_count": "Stars", "primary_language": "Language"},
            title="Most Starred Repos",
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Insufficient data to display repositories.")
