import os
import tempfile
from git import Repo
import chromadb
from typing import List, Dict
import glob
import datetime
import shutil
import logging

class RepoIndexer:
    def __init__(self, persist_directory: str = "./chroma_db"):
        """Initialize RepoIndexer with persistent storage."""
        # Get absolute path and current working directory
        cwd = os.getcwd()
        persist_directory = os.path.abspath(persist_directory)
        
        logging.info("\n=== ChromaDB Initialization ===")
        logging.info(f"Current working directory: {cwd}")
        logging.info(f"Database directory (relative): {persist_directory}")
        logging.info(f"Database directory (absolute): {os.path.abspath(persist_directory)}")
        
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(
            name="code_chunks",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Verify database directory exists and show contents
        if os.path.exists(persist_directory):
            logging.info("\nDatabase directory contents:")
            for item in os.listdir(persist_directory):
                item_path = os.path.join(persist_directory, item)
                logging.info(f" - {item} ({'directory' if os.path.isdir(item_path) else 'file'})")
        else:
            logging.warning(f"\nWarning: Database directory not found at {persist_directory}")

    def clone_repo(self, repo_url: str) -> str:
        """Clone a GitHub repository to a temporary directory."""
        logging.info(f"\nCloning repository: {repo_url}")
        temp_dir = tempfile.mkdtemp()
        logging.info(f"Created temporary directory: {temp_dir}")
        Repo.clone_from(repo_url, temp_dir)
        logging.info("Repository cloned successfully")
        return temp_dir

    def read_file_content(self, file_path: str) -> str:
        """Read and return the content of a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            logging.warning(f"Skipping file with encoding issues: {file_path}")
            return ""
        except Exception as e:
            logging.error(f"Error reading file {file_path}: {e}")
            return ""

    def index_repo(self, repo_url: str):
        """Index a GitHub repository into ChromaDB."""
        logging.info(f"\n=== Starting indexing process for {repo_url} ===")
        repo_path = self.clone_repo(repo_url)
        files_processed = 0
        files_skipped = 0
        
        try:
            # Get existing indexed files
            logging.debug("\nChecking for previously indexed files...")
            existing_files = set()
            try:
                if len(self.collection.get()['ids']) > 0:
                    existing_metadata = self.collection.get()['metadatas']
                    existing_files = {meta['file_path'] for meta in existing_metadata}
                    logging.debug(f"Found {len(existing_files)} previously indexed files")
            except Exception as e:
                logging.error(f"Error getting existing files: {e}")
                existing_files = set()
            
            logging.info("\nStarting file processing...")
            # Walk through all files in the repository
            for root, _, files in os.walk(repo_path):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    relative_path = os.path.relpath(file_path, repo_path)
                    
                    logging.debug(f"Processing: {relative_path}")
                    
                    # Skip if file is already indexed
                    if relative_path in existing_files:
                        files_skipped += 1
                        logging.debug(f"Skipping (already indexed): {relative_path}")
                        continue
                    
                    content = self.read_file_content(file_path)
                    if content:
                        try:
                            self.collection.add(
                                documents=[content],
                                metadatas=[{
                                    "file_path": relative_path,
                                    "repo_url": repo_url,
                                    "indexed_at": str(datetime.datetime.now())
                                }],
                                ids=[f"{repo_url}_{relative_path}"]
                            )
                            files_processed += 1
                            logging.debug(f"Successfully indexed: {relative_path}")
                            
                            if files_processed % 100 == 0:
                                logging.info(f"Progress: Processed {files_processed} new files")
                        except Exception as e:
                            logging.error(f"Error indexing file {relative_path}: {e}")
                            continue
            
            logging.info(f"\n=== Indexing Summary ===")
            logging.info(f"Repository: {repo_url}")
            logging.info(f"New files indexed: {files_processed}")
            logging.info(f"Files already indexed: {files_skipped}")
            logging.info(f"Total files encountered: {files_processed + files_skipped}")
            logging.info(f"Database location: {os.path.abspath(self.client._settings.persist_directory)}")
            
        finally:
            logging.debug(f"\nCleaning up temporary directory: {repo_path}")
            try:
                shutil.rmtree(repo_path)
                logging.debug("Cleanup successful")
            except Exception as e:
                logging.error(f"Error during cleanup: {e}")

if __name__ == "__main__":
    # Example usage
    indexer = RepoIndexer()
    repo_url = "https://github.com/example/repo"  # Replace with actual repo URL
    indexer.index_repo(repo_url)
