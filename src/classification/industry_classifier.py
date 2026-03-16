from ..agents.classification_agent import ClassificationAgent

class IndustryClassifier:
    def __init__(self, github_client):
        self.agent = ClassificationAgent(github_client)

    def classify_repository(self, repo_data: dict) -> dict:
        """
        Classifies a repository into an industry sector.
        """
        return self.agent.run(repo_data)
