import base64
from .github_client import GitHubClient
from loguru import logger

class RepoExtractor:
    def __init__(self, client: GitHubClient):
        self.client = client

    def search_repos_by_stars(
        self,
        usernames: list[str],
        min_stars: int = 1
    ) -> list[dict]:
        """
        Search for top repositories from a list of users.
        
        Args:
            usernames: List of GitHub usernames to check.
            min_stars: Minimum star count to include a repository.
            
        Returns:
            List of repositories sorted by stars (top 1000).
        """
        repos = []
        logger.info(f"Extracting repositories from {len(usernames)} users...")

        for username in usernames:
            try:
                # Fetching user's repos sorted by stars to get the best ones first
                user_repos = self.client.make_request(
                    f"users/{username}/repos",
                    params={
                        "sort": "stars", 
                        "direction": "desc",
                        "per_page": 100
                    }
                )

                for repo in user_repos:
                    # Skip forks as per project overview logic
                    if repo.get("fork"):
                        continue
                        
                    if repo["stargazers_count"] >= min_stars:
                        repos.append(repo)
                        
                logger.debug(f"Collected {len(repos)} repositories so far...")
                
            except Exception as e:
                logger.error(f"Error extracting repos for {username}: {e}")
                continue

        # Sort all repos by stars across all users and take top 1000
        repos.sort(key=lambda x: x["stargazers_count"], reverse=True)
        logger.info(f"Total repositories found: {len(repos)}. Returning top 1000.")
        return repos[:1000]

    def get_repo_readme(self, owner: str, repo: str) -> str:
        """
        Get the README content of a repository.
        Returns empty string if not found.
        """
        try:
            result = self.client.make_request(
                f"repos/{owner}/{repo}/readme"
            )

            # GitHub returns content as base64 encoded
            content = base64.b64decode(result["content"]).decode("utf-8")
            return content[:5000]  # Limit to 5000 chars to manage data size and LLM tokens

        except Exception as e:
            logger.debug(f"README not found or error for {owner}/{repo}: {e}")
            return ""

    def get_repo_languages(self, owner: str, repo: str) -> dict:
        """Get the language breakdown of a repository."""
        logger.debug(f"Fetching languages for {owner}/{repo}")
        return self.client.make_request(f"repos/{owner}/{repo}/languages")

    def get_repo_contributors(self, owner: str, repo: str) -> list[dict]:
        """Get the contributors of a repository."""
        logger.debug(f"Fetching contributors for {owner}/{repo}")
        return self.client.make_request(
            f"repos/{owner}/{repo}/contributors",
            params={"per_page": 100}
        )
