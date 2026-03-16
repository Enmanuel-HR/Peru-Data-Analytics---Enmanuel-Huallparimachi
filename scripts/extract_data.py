import sys
import os
from loguru import logger

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.full_etl import run_full_etl

if __name__ == "__main__":
    logger.info("Running Data Extraction...")
    # Default parameters for extraction
    run_full_etl(target_repo_count=1000, user_search_limit=500)
