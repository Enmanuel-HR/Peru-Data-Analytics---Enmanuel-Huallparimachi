import os
import requests
import time
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential
from loguru import logger

load_dotenv()

class GitHubClient:
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        if not self.token:
            logger.warning("GITHUB_TOKEN not found in environment variables.")

    def check_rate_limit(self) -> dict:
        """Check current rate limit status."""
        try:
            response = requests.get(
                f"{self.base_url}/rate_limit",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error checking rate limit: {e}")
            return {}

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60)
    )
    def make_request(self, endpoint: str, params: dict = None) -> dict:
        """Make a rate-limit-aware request to GitHub API."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = requests.get(
            url,
            headers=self.headers,
            params=params
        )

        # Check rate limit
        remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
        limit = int(response.headers.get("X-RateLimit-Limit", 0))
        reset_time = int(response.headers.get("X-RateLimit-Reset", 0))

        if remaining < 10:
            sleep_time = max(0, reset_time - int(time.time())) + 1
            logger.warning(f"Rate limit low ({remaining}/{limit}). Sleeping for {sleep_time} seconds...")
            time.sleep(sleep_time)

        response.raise_for_status()
        return response.json()
