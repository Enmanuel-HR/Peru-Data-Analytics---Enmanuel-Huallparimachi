from sqlalchemy import func
from sqlalchemy.orm import Session
from src.database.models import User, Repository
from datetime import datetime, timedelta, timezone
from collections import Counter
from loguru import logger

class EcosystemMetricsCalculator:
    def __init__(self, session: Session):
        self.session = session
        self.today = datetime.now(timezone.utc)

    def calculate_all(self) -> dict:
        """Calculate all ecosystem-level metrics for Peru."""
        logger.info("Calculating ecosystem-level metrics...")
        
        # 1. Total Developers
        total_developers = self.session.query(func.count(User.id)).scalar() or 0
        
        # 2. Total Repositories
        total_repositories = self.session.query(func.count(Repository.id)).scalar() or 0
        
        # 3. Total Stars
        total_stars = self.session.query(func.sum(Repository.stargazers_count)).scalar() or 0
        
        # 4. Avg Repos per User
        avg_repos_per_user = round(total_repositories / max(total_developers, 1), 2)
        
        # 5. Most Popular Languages (Top 10)
        # We'll get all primary languages and count them
        repos_langs = self.session.query(Repository.primary_language).filter(Repository.primary_language != None).all()
        lang_counts = Counter([r.primary_language for r in repos_langs])
        most_popular_languages = dict(lang_counts.most_common(10))
        
        # 6. Industry Distribution
        # Count repos per industry classification
        industry_data = self.session.query(Repository.industry_classification, func.count(Repository.id)).\
            group_by(Repository.industry_classification).all()
        industry_distribution = {industry: count for industry, count in industry_data if industry}
        
        # 7. Active Developer Pct (% active in last 90 days)
        ninety_days_ago = self.today - timedelta(days=90)
        # Using pushed_at as a proxy for activity
        active_devs = self.session.query(func.count(func.distinct(Repository.owner_id))).\
            filter(Repository.pushed_at >= ninety_days_ago).scalar() or 0
        active_developer_pct = round((active_devs / max(total_developers, 1)) * 100, 2)
        
        # 8. Avg Account Age (Tenure in days)
        # Note: func.avg might return a float or decimal depending on DB
        avg_age_days = self.session.query(func.avg(
            func.julianday(func.current_timestamp()) - func.julianday(User.created_at)
        )).scalar() or 0
        
        return {
            "total_developers": total_developers,
            "total_repositories": total_repositories,
            "total_stars": int(total_stars),
            "avg_repos_per_user": avg_repos_per_user,
            "most_popular_languages": most_popular_languages,
            "industry_distribution": industry_distribution,
            "active_developer_pct": active_developer_pct,
            "avg_account_age_days": round(float(avg_age_days), 2)
        }
