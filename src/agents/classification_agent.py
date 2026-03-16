import json
import os
from openai import OpenAI
from dotenv import load_dotenv
from loguru import logger
from src.extraction.github_client import GitHubClient
from src.extraction.repo_extractor import RepoExtractor

load_dotenv()

class ClassificationAgent:
    def __init__(self, github_client: GitHubClient = None):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.error("OPENAI_API_KEY not found in environment.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.github_client = github_client or GitHubClient()
        self.repo_extractor = RepoExtractor(self.github_client)
        
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_readme",
                    "description": "Fetch the README content of a repository for more context.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "owner": {"type": "string"},
                            "repo": {"type": "string"}
                        },
                        "required": ["owner", "repo"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_languages",
                    "description": "Get the detailed programming languages byte counts used in a repository.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "owner": {"type": "string"},
                            "repo": {"type": "string"}
                        },
                        "required": ["owner", "repo"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "classify_industry",
                    "description": "Final step: Classify a repository into a Peruvian CIIU industry category.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "repo_name": {"type": "string"},
                            "industry_code": {
                                "type": "string",
                                "enum": ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U"],
                                "description": "The 1-letter CIIU industry code."
                            },
                            "confidence": {
                                "type": "string", 
                                "enum": ["high", "medium", "low"]
                            },
                            "reasoning": {"type": "string", "description": "Short explanation of the classification."}
                        },
                        "required": ["repo_name", "industry_code", "confidence", "reasoning"]
                    }
                }
            }
        ]

    def run(self, repository: dict) -> dict:
        """
        Run the classification agent on a repository.
        The agent decides what information it needs and classifies the repo.
        """
        owner = repository.get('owner', {}).get('login') if isinstance(repository.get('owner'), dict) else repository.get('owner')
        name = repository.get('name')
        
        messages = [
            {
                "role": "system",
                "content": """You are an AI agent that classifies GitHub repositories into industry categories based on Peru's CIIU standards.

Your task is to analyze a repository and determine which industry it serves.
You have access to tools to get more information if needed.

Industry codes:
A: Agriculture, forestry, fishing
B: Mining
C: Manufacturing
D: Electricity, gas, steam
E: Water supply; sewerage
F: Construction
G: Wholesale and retail trade
H: Transportation and storage
I: Accommodation and food services
J: Information and communications (IT/Software)
K: Financial and insurance
L: Real estate
M: Professional, scientific, technical
N: Administrative and support
O: Public administration and defense
P: Education
Q: Human health and social work
R: Arts, entertainment and recreation
S: Other service activities
T: Activities of households
U: Extraterritorial organizations

Steps:
1. Review the basic repository information.
2. If the description is too vague, use 'get_readme' to fetch more context.
3. If technical stack is key to classification, use 'get_languages'.
4. Once you have enough context, make your final classification using the 'classify_industry' tool.
"""
            },
            {
                "role": "user",
                "content": f"""Please classify this repository:

Owner: {owner}
Name: {name}
Description: {repository.get('description', 'No description')}
Primary Language: {repository.get('language', 'Unknown')}
Topics: {', '.join(repository.get('topics', [])) if repository.get('topics') else 'None'}
"""
            }
        ]

        logger.info(f"Starting classification agent for {owner}/{name}")

        for _ in range(5):  # Limit steps to prevent infinite loops
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=messages,
                tools=self.tools,
                tool_choice="auto"
            )

            message = response.choices[0].message
            messages.append(message)

            if message.tool_calls:
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)

                    logger.info(f"Agent calling tool: {function_name} with {arguments}")

                    owner_arg = arguments.get("owner", owner)
                    repo_arg = arguments.get("repo", arguments.get("name", name))

                    if function_name == "get_readme":
                        logger.info(f"Agent determined a README is needed for {owner_arg}/{repo_arg}")
                        result = self.repo_extractor.get_repo_readme(owner_arg, repo_arg)
                    elif function_name == "get_languages":
                        logger.info(f"Agent is analyzing language breakdown for {owner_arg}/{repo_arg}")
                        result = self.repo_extractor.get_repo_languages(owner_arg, repo_arg)
                    elif function_name == "classify_industry":
                        # Final classification reached
                        logger.success(f"Agent finished: {arguments['industry_code']} for {name}")
                        logger.info(f"Reasoning: {arguments.get('reasoning')}")
                        return arguments

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(result)
                    })
            else:
                # No tool calls - agent is stuck or produced direct text
                break

        return {"error": "Agent did not produce classification using the required tool."}
