#!/usr/bin/env python3
"""
CLI script to run the codebase analysis workflow.

Usage:
    python main.py https://github.com/username/repository
"""

import sys
import logging
from src.workflow import analyze_repository

# Add logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <repository_url>")
        print("Example: python main.py https://github.com/username/repository")
        sys.exit(1)
    
    repo_url = sys.argv[1]
    logging.info(f"Analyzing repository: {repo_url}")
    logging.info("This may take a few minutes...")
    
    try:
        result = analyze_repository(repo_url)
        
        # Print all messages from the workflow
        for message in result["messages"]:
            logging.info(message)
            
    except Exception as e:
        logging.error(f"Error analyzing repository: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
