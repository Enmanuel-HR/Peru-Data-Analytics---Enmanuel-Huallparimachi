import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Industries - GitHub Peru", page_icon="🇵🇪", layout="wide")
st.title("Industry Analysis")

@st.cache_data
def load_data():
    try:
        repos_df = pd.read_csv("data/processed/repositories.csv")
        classifications_df = pd.read_csv("data/processed/classifications.csv")
        return repos_df, classifications_df
    except FileNotFoundError:
        return pd.DataFrame(), pd.DataFrame()

repos_df, classifications_df = load_data()

if not classifications_df.empty and not repos_df.empty:
    repo_industries = pd.merge(
        repos_df, 
        classifications_df, 
        left_on="id", 
        right_on="repo_id",
        how="inner"
    )
    
    if not repo_industries.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Repositories Classified", len(repo_industries))
        with col2:
            st.metric("Unique Industries Identified", repo_industries["industry_name"].nunique())
            
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Repositories by Industry")
            ind_counts = repo_industries["industry_name"].value_counts().reset_index()
            ind_counts.columns = ["Industry", "Repositories"]
            
            fig = px.bar(
                ind_counts,
                y="Industry",
                x="Repositories",
                orientation='h',
                color="Repositories",
                color_continuous_scale="Blues"
            )
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.subheader("Top Languages by Industry")
            if "primary_language" in repo_industries.columns:
                lang_ind = repo_industries.groupby(["industry_name", "primary_language"]).size().reset_index(name="count")
                
                top_inds = ind_counts.head(5)["Industry"].tolist()
                filtered_lang_ind = lang_ind[lang_ind["industry_name"].isin(top_inds)]
                
                fig2 = px.bar(
                    filtered_lang_ind,
                    x="industry_name",
                    y="count",
                    color="primary_language",
                    barmode="stack",
                    labels={"industry_name": "Industry", "count": "Repositories", "primary_language": "Language"}
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Language data not available for this view.")
    else:
         st.warning("No matches found between repositories and classifications.")
else:
    st.warning("Insufficient data to display industry analysis.")
