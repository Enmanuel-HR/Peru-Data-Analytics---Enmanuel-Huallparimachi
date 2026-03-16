import sys
import os
import pandas as pd
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
from datetime import datetime, timezone

load_dotenv()

def run_full_etl(target_repo_count=1000, user_search_limit=200):
    """
    Run the full ETL process targeting the top starred repositories in Peru.
    1. Discovery: Find 200+ top users in Peru.
    2. Collection: Fetch all repository metadata for these users.
    3. Selection: Sort and select the top 'target_repo_count' by stars.
    4. Processing: Fetch details (README/Langs) and Classify using AI Agent.
    """
    logger.info(f"🚀 Starting Full Scale ETL (Target: {target_repo_count} repos)")
    
    # 1. Initialize
    init_db()
    session = SessionLocal()
    client = GitHubClient()
    user_ext = UserExtractor(client)
    repo_ext = RepoExtractor(client)
    agent = ClassificationAgent(client)
    
    try:
        # Phase 1: User Discovery
        logger.info(f"Phase 1: Discovering top {user_search_limit} users in Peru...")
        users_metadata = user_ext.search_users_by_location("Peru", max_users=user_search_limit)
        user_logins = [u['login'] for u in users_metadata]
        
        # Phase 2: Repository Pool Collection
        logger.info(f"Phase 2: Collecting repository candidates from {len(user_logins)} users...")
        all_repo_candidates = []
        
        import json
        cache_file = "data/raw/repo_candidates_cache.json"
        
        if os.path.exists(cache_file):
            logger.info("  🟢 Found existing repository candidates cache! Loading from disk (skipping GitHub API)...")
            with open(cache_file, 'r', encoding='utf-8') as f:
                all_repo_candidates = json.load(f)
        else:
            for i, login in enumerate(user_logins):
                if i % 10 == 0:
                    logger.info(f"  Progress: {i}/{len(user_logins)} users processed...")
                
                # Fetch user details to save to DB later
                full_user = user_ext.get_user_details(login)
                
                # Save User to DB if not exists
                db_user = session.query(DBUser).filter_by(id=full_user['id']).first()
                if not db_user:
                    db_user = DBUser(
                        id=full_user['id'],
                        login=full_user['login'],
                        name=full_user.get('name'),
                        location=full_user.get('location'),
                        followers=full_user.get('followers', 0),
                        public_repos=full_user.get('public_repos', 0),
                        created_at=datetime.fromisoformat(full_user['created_at'].replace('Z', '+00:00'))
                    )
                    session.add(db_user)
                    session.commit()
                
                # Get all repos for this user
                user_repos = user_ext.get_user_repos(login)
                for r in user_repos:
                    r['owner_db_id'] = db_user.id # Tag with DB ID
                    all_repo_candidates.append(r)
            
            # Save raw collection to cache to avoid re-fetching in the future
            logger.info("  💾 Saving repository candidates to cache...")
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(all_repo_candidates, f)
        
        # Phase 3: Selection (Top 1000)
        logger.info(f"Phase 3: Selecting top {target_repo_count} from {len(all_repo_candidates)} candidates...")
        # Sort by stars descending
        all_repo_candidates.sort(key=lambda x: x.get('stargazers_count', 0), reverse=True)
        top_repos = all_repo_candidates[:target_repo_count]
        
        # Phase 4: Processing & Classification
        logger.info(f"Phase 4: Processing and Classifying {len(top_repos)} repositories...")
        for i, repo_data in enumerate(top_repos):
            repo_name = repo_data['name']
            login = repo_data['owner']['login']
            
            # Check if repo already exists with classification
            db_repo = session.query(DBRepo).filter_by(id=repo_data['id']).first()
            if db_repo and db_repo.industry_classification:
                continue
                
            logger.info(f"  [{i+1}/{len(top_repos)}] Processing: {login}/{repo_name} ({repo_data.get('stargazers_count')} stars)")
            
            # Fetch deeper data
            readme = repo_ext.get_repo_readme(login, repo_name)
            languages = repo_ext.get_repo_languages(login, repo_name)
            
            # AI Agent Classification
            classification = agent.run({
                "owner": login,
                "name": repo_name,
                "description": repo_data.get('description'),
                "language": repo_data.get('language'),
                "topics": repo_data.get('topics', [])
            })
            
            # Save Repo to DB
            if not db_repo:
                db_repo = DBRepo(
                    id=repo_data['id'],
                    owner_id=repo_data['owner_db_id'],
                    name=repo_name,
                    full_name=repo_data['full_name'],
                    description=repo_data.get('description'),
                    topics=repo_data.get('topics', []),
                    primary_language=repo_data.get('language'),
                    stargazers_count=repo_data.get('stargazers_count', 0),
                    forks_count=repo_data.get('forks_count', 0),
                    open_issues_count=repo_data.get('open_issues_count', 0),
                    created_at=datetime.fromisoformat(repo_data['created_at'].replace('Z', '+00:00')),
                    pushed_at=datetime.fromisoformat(repo_data['pushed_at'].replace('Z', '+00:00')),
                    readme_content=readme,
                    industry_classification=classification.get('industry_code', 'J')
                )
                session.add(db_repo)
            else:
                db_repo.industry_classification = classification.get('industry_code', 'J')
                db_repo.readme_content = readme
            
            # Save Languages
            for lang, bytes_count in languages.items():
                # Check if exists
                exists = session.query(RepositoryLanguage).filter_by(repo_id=db_repo.id, language_name=lang).first()
                if not exists:
                    db_lang = RepositoryLanguage(repo_id=db_repo.id, language_name=lang, bytes_count=bytes_count)
                    session.add(db_lang)
            
            session.commit() # Commit daily to avoid data loss
            
        logger.success("✅ Full Scale ETL process completed!")
        
    except Exception as e:
        logger.error(f"❌ ETL failed: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    # You can adjust these values. 
    # Warning: target_repo_count=1000 will consume ~1000 OpenAI calls.
    run_full_etl(target_repo_count=1000, user_search_limit=500)
