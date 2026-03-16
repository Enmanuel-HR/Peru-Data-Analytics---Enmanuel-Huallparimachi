from datetime import datetime, timezone
from collections import Counter
from loguru import logger

class UserMetricsCalculator:
    def __init__(self):
        # Use UTC for consistency
        self.today = datetime.now(timezone.utc)

    def calculate_all_metrics(
        self,
        user: dict,
        repos: list[dict],
        classifications: list[dict]
    ) -> dict:
        """
        Calculate all user-level metrics.

        Args:
            user: User data from GitHub API
            repos: List of user's repositories (raw dicts or objects with dict access)
            classifications: Industry classifications for repos

        Returns:
            Dictionary with all calculated metrics
        """
        metrics = {}

        if not repos:
            logger.warning(f"No repositories found for user {user.get('login')}, returning basic metrics.")
            return self._empty_metrics(user)

        # Activity Metrics
        metrics["total_repos"] = len(repos)
        metrics["total_stars_received"] = sum(r.get("stargazers_count", 0) for r in repos)
        metrics["total_forks_received"] = sum(r.get("forks_count", 0) for r in repos)
        metrics["avg_stars_per_repo"] = (
            metrics["total_stars_received"] / metrics["total_repos"]
            if metrics["total_repos"] > 0 else 0
        )

        try:
            created_at_str = user.get("created_at", "").replace("Z", "+00:00")
            created_at = datetime.fromisoformat(created_at_str)
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            metrics["account_age_days"] = (self.today - created_at).days
        except Exception as e:
            logger.error(f"Error parsing user created_at: {e}")
            metrics["account_age_days"] = 0

        metrics["repos_per_year"] = (
            metrics["total_repos"] / (metrics["account_age_days"] / 365.25)
            if metrics["account_age_days"] > 0 else 0
        )

        # Influence Metrics
        metrics["followers"] = user.get("followers", 0)
        metrics["following"] = user.get("following", 0)
        metrics["follower_ratio"] = (
            metrics["followers"] / max(metrics["following"], 1)
            if metrics["following"] > 0 else metrics["followers"]
        )
        metrics["h_index"] = self._calculate_h_index(repos)
        metrics["impact_score"] = (
            metrics["total_stars_received"] +
            (metrics["total_forks_received"] * 2) +
            metrics["followers"]
        )

        # Technical Metrics
        languages = [r.get("language") for r in repos if r.get("language")]
        lang_counts = Counter(languages)
        metrics["primary_languages"] = [l for l, _ in lang_counts.most_common(3)]
        metrics["language_diversity"] = len(set(languages))

        industry_codes = [c.get("industry_code") for c in classifications if c.get("industry_code")]
        metrics["industries_served"] = len(set(industry_codes))
        metrics["primary_industry"] = Counter(industry_codes).most_common(1)[0][0] if industry_codes else None

        # Documentation quality
        repos_with_readme = sum(1 for r in repos if r.get("has_readme") or r.get("readme_content"))
        repos_with_license = sum(1 for r in repos if r.get("license"))
        metrics["has_readme_pct"] = repos_with_readme / len(repos) if repos else 0
        metrics["has_license_pct"] = repos_with_license / len(repos) if repos else 0

        # Engagement Metrics
        metrics["total_open_issues"] = sum(r.get("open_issues_count", 0) for r in repos)

        try:
            push_dates = []
            for r in repos:
                if r.get("pushed_at"):
                    dt = datetime.fromisoformat(r["pushed_at"].replace("Z", "+00:00"))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    push_dates.append(dt)

            if push_dates:
                last_push = max(push_dates)
                metrics["days_since_last_push"] = (self.today - last_push).days
                metrics["is_active"] = metrics["days_since_last_push"] < 90
            else:
                metrics["days_since_last_push"] = None
                metrics["is_active"] = False
        except Exception as e:
            logger.error(f"Error calculating last push: {e}")
            metrics["days_since_last_push"] = None
            metrics["is_active"] = False

        return metrics

    def _calculate_h_index(self, repos: list[dict]) -> int:
        """
        Calculate h-index based on repository stars.
        h-index = h if h repos have at least h stars each.
        """
        stars = sorted([r.get("stargazers_count", 0) for r in repos], reverse=True)
        h = 0
        for i, s in enumerate(stars):
            if s >= i + 1:
                h = i + 1
            else:
                break
        return h

    def _empty_metrics(self, user: dict) -> dict:
        return {
            "total_repos": 0, "total_stars_received": 0, "total_forks_received": 0,
            "avg_stars_per_repo": 0, "account_age_days": 0, "repos_per_year": 0,
            "followers": user.get("followers", 0), "following": user.get("following", 0),
            "follower_ratio": 0, "h_index": 0, "impact_score": 0,
            "primary_languages": [], "language_diversity": 0, "industries_served": 0,
            "primary_industry": None, "has_readme_pct": 0, "has_license_pct": 0,
            "total_open_issues": 0, "days_since_last_push": None, "is_active": False
        }
