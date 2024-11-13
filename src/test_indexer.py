import logging

# Configure logging BEFORE importing RepoIndexer
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    force=True  # This ensures we override any existing logger configuration
)

from repo_indexer import RepoIndexer

def main():
    logging.info("=== Starting Test Indexer ===")
    
    # Initialize the indexer
    indexer = RepoIndexer()
    
    # Test with a small public repository
    repo_url = "https://github.com/deweyjose/graphqlcodegen"
    
    logging.info(f"Starting to index repository: {repo_url}")
    indexer.index_repo(repo_url)
    
    # Verify the indexed content
    collection = indexer.collection
    results = collection.get()
    logging.info(f"\nIndexed {len(results['ids'])} files")
    
    # Print some sample metadata
    logging.info("\nSample of indexed files:")
    for i in range(min(5, len(results['ids']))):
        logging.info(f"- {results['metadatas'][i]['file_path']}")

if __name__ == "__main__":
    main()
