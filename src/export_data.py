import pandas as pd
from sqlalchemy import create_engine
import os
import sys
from loguru import logger

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from src.database.db_config import SessionLocal
from src.database.models import User as DBUser, Repository as DBRepo
from src.metrics.user_metrics import UserMetricsCalculator
from src.classification.industry_categories import INDUSTRY_CATEGORIES

def export_db_to_csv():
    """
    Exports SQLite tables to CSV files for the Streamlit dashboard.
    Calculates necessary metrics on the fly for the dashboard.
    """
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///peru_analytics.db")
    engine = create_engine(DATABASE_URL)
    session = SessionLocal()
    metrics_calc = UserMetricsCalculator()
    
    if not os.path.exists("data/processed"):
        os.makedirs("data/processed")
    
    logger.info("Exporting Database to CSV for Dashboard...")
    
    try:
        # 1. Process Users and Metrics
        db_users = session.query(DBUser).all()
        user_list = []
        
        for user in db_users:
            # We need repo dicts for the calculator
            user_repos = []
            classifications = []
            
            for repo in user.repositories:
                user_repos.append({
                    "id": repo.id,
                    "stargazers_count": repo.stargazers_count,
                    "forks_count": repo.forks_count,
                    "language": repo.primary_language,
                    "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
                    "license": repo.license,
                    "open_issues_count": repo.open_issues_count
                })
                classifications.append({
                    "industry_code": repo.industry_classification
                })
            
            # Calculate metrics
            user_dict = {column.name: getattr(user, column.name) for column in user.__table__.columns}
            # Convert datetime to string for the calculator if needed, but the current model stores datetime objects
            # The calculator expects a dict. Let's ensure created_at is a string if it uses .replace("Z", ...)
            if user_dict.get('created_at'):
                user_dict['created_at'] = user_dict['created_at'].isoformat()
            
            metrics = metrics_calc.calculate_all_metrics(user_dict, user_repos, classifications)
            
            # Merge metrics into user data
            user_dict.update(metrics)
            
            # Flatten primary_languages for CSV
            for i, lang in enumerate(metrics.get("primary_languages", []), 1):
                user_dict[f"primary_language_{i}"] = lang
                
            user_list.append(user_dict)

        users_df = pd.DataFrame(user_list)
        users_df.to_csv("data/processed/users.csv", index=False)
        logger.info(f"  Exported data/processed/users.csv ({len(users_df)} users)")
        
        # 2. Repositories CSV
        repos_df = pd.read_sql("SELECT * FROM repositories", engine)
        repos_df.to_csv("data/processed/repositories.csv", index=False)
        logger.info(f"  Exported data/processed/repositories.csv ({len(repos_df)} repos)")
        
        # 3. Classifications
        class_data = []
        for _, row in repos_df.iterrows():
            code = row['industry_classification']
            info = INDUSTRY_CATEGORIES.get(code, INDUSTRY_CATEGORIES.get('J'))
            class_data.append({
                "repo_id": row['id'],
                "industry_code": code,
                "industry_name": info['en']
            })
        
        class_df = pd.DataFrame(class_data)
        class_df.to_csv("data/processed/classifications.csv", index=False)
        logger.info("  Exported data/processed/classifications.csv")
        
        logger.success("Export completed!")
        
    except Exception as e:
        logger.error(f"Export failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        session.close()

if __name__ == "__main__":
    export_db_to_csv()
