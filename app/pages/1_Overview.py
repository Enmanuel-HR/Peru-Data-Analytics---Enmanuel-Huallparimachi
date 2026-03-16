import streamlit as st
import os

# Redirect to the main Overview page logic
if __name__ == "__main__":
    # In Streamlit, pages/1_Overview.py might just be a duplicate of main.py logic 
    # or import the show function.
    from ..main import load_data
    
    st.set_page_config(page_title="Overview - GitHub Peru", page_icon="🇵🇪", layout="wide")
    st.title("Peru Developer Ecosystem Overview")
    
    # We could theoretically import the main logic here. 
    # For now, let's keep it simple.
    os.system("streamlit run app/main.py") # This isn't right for streamlit pages.
    st.info("Please use the main application page or select Overview from the sidebar.")
