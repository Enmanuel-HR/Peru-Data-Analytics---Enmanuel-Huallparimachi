import sys
import os
from loguru import logger
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.extraction.github_client import GitHubClient
from src.extraction.user_extractor import UserExtractor
from src.extraction.repo_extractor import RepoExtractor
from src.database.db_config import init_db, SessionLocal
from src.database.models import User as DBUser, Repository as DBRepo, RepositoryLanguage
from src.agents.classification_agent import ClassificationAgent
from src.metrics.user_metrics import UserMetricsCalculator
from datetime import datetime, timezone

load_dotenv()

def run_etl(max_users=5, repos_per_user=5):
    """
    Run a sample ETL process.
    - max_users: Number of users to fetch from Peru.
    - repos_per_user: Number of repos per user to process.
    """
    logger.info("Starting Peru Analytics ETL Process...")
    
    # 1. Initialize Database
    init_db()
    session = SessionLocal()
    
    # 2. Initialize GitHub Client and Agent
    client = GitHubClient()
    user_ext = UserExtractor(client)
    repo_ext = RepoExtractor(client)
    agent = ClassificationAgent(client)
    
    try:
        # 3. Search for Users in Peru
        logger.info(f"Searching for top {max_users} users in Peru...")
        users = user_ext.search_users_by_location("Peru", max_users=max_users)
        
        for user_data in users:
            login = user_data['login']
            logger.info(f"Processing user: {login}")
            
            # Fetch full user details
            full_user = user_ext.get_user_details(login)
            
            # Save User to DB
            db_user = session.query(DBUser).filter_by(id=full_user['id']).first()
            if not db_user:
                db_user = DBUser(
                    id=full_user['id'],
                    login=full_user['login'],
                    name=full_user.get('name'),
                    location=full_user.get('location'),
                    bio=full_user.get('bio'),
                    company=full_user.get('company'),
                    blog=full_user.get('blog'),
                    email=full_user.get('email'),
                    followers=full_user.get('followers', 0),
                    following=full_user.get('following', 0),
                    public_repos=full_user.get('public_repos', 0),
                    created_at=datetime.fromisoformat(full_user['created_at'].replace('Z', '+00:00'))
                )
                session.add(db_user)
                session.commit()
            
            # 4. Fetch User Repositories
            logger.info(f"Fetching repos for {login}...")
            repos = user_ext.get_user_repos(login)[:repos_per_user]
            
            for repo_data in repos:
                repo_name = repo_data['name']
                logger.info(f"  Processing repo: {repo_name}")
                
                # Check if repo already exists
                db_repo = session.query(DBRepo).filter_by(id=repo_data['id']).first()
                if db_repo:
                    continue
                
                # Fetch deeper data (README, Languages)
                readme = repo_ext.get_repo_readme(login, repo_name)
                languages = repo_ext.get_repo_languages(login, repo_name)
                
                # 5. Classify using Agent
                logger.info(f"    Classifying {repo_name} using AI Agent...")
                classification = agent.run({
                    "owner": login,
                    "name": repo_name,
                    "description": repo_data.get('description'),
                    "language": repo_data.get('language'),
                    "topics": repo_data.get('topics', [])
                })
                
                # 6. Save Repo to DB
                new_repo = DBRepo(
                    id=repo_data['id'],
                    owner_id=db_user.id,
                    name=repo_name,
                    full_name=repo_data['full_name'],
                    description=repo_data.get('description'),
                    topics=repo_data.get('topics', []),
                    primary_language=repo_data.get('language'),
                    stargazers_count=repo_data.get('stargazers_count', 0),
                    forks_count=repo_data.get('forks_count', 0),
                    watchers_count=repo_data.get('watchers_count', 0),
                    open_issues_count=repo_data.get('open_issues_count', 0),
                    created_at=datetime.fromisoformat(repo_data['created_at'].replace('Z', '+00:00')),
                    pushed_at=datetime.fromisoformat(repo_data['pushed_at'].replace('Z', '+00:00')),
                    license=repo_data.get('license', {}).get('name') if repo_data.get('license') else None,
                    readme_content=readme,
                    industry_classification=classification.get('industry_code', 'J')
                )
                session.add(new_repo)
                
                # Save Languages
                for lang, bytes_count in languages.items():
                    db_lang = RepositoryLanguage(
                        repo_id=new_repo.id,
                        language_name=lang,
                        bytes_count=bytes_count
                    )
                    session.add(db_lang)
                
                session.commit()
        
        logger.success("ETL process completed successfully!")
        
    except Exception as e:
        logger.error(f"ETL failed: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    # Scaling up to target 1,000+ repositories
    # Using a larger pool of users to ensure we find high-quality repos
    run_etl(max_users=100, repos_per_user=20)
