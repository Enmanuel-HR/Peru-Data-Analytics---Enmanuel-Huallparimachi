import sys
import os
import pandas as pd
from loguru import logger

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.export_data import export_db_to_csv

def main():
    logger.info("Recalculating all metrics...")
    export_db_to_csv()
    logger.success("Metrics recalculated and exported.")

if __name__ == "__main__":
    main()
