import os
import tempfile
from git import Repo
import chromadb
from typing import List, Dict
import datetime
import shutil
import logging
from langchain_openai import OpenAIEmbeddings
import re

class OpenAIEmbeddingFunction:
    """Wrapper class to make OpenAIEmbeddings compatible with ChromaDB's interface."""
    def __init__(self):
        self._embeddings = OpenAIEmbeddings()
        
    def __call__(self, input: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        return self._embeddings.embed_documents(input)

class RepoIndexer:
    def __init__(self, persist_directory: str = "./chroma_db"):
        """Initialize RepoIndexer with persistent storage."""
        # Get absolute path and current working directory
        cwd = os.getcwd()
        self.persist_directory = os.path.abspath(persist_directory)
        
        logging.info("\n=== ChromaDB Initialization ===")
        logging.info(f"Current working directory: {cwd}")
        logging.info(f"Database directory (relative): {persist_directory}")
        logging.info(f"Database directory (absolute): {os.path.abspath(persist_directory)}")
        
        # Create embedding function
        self.embedding_function = OpenAIEmbeddingFunction()
        
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(
            name="code_chunks",
            metadata={"hnsw:space": "cosine"},
            embedding_function=self.embedding_function
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

    def chunk_content(self, content: str, file_path: str) -> List[Dict]:
        """Split content into smaller, meaningful chunks."""
        chunks = []
        
        # Handle different file types appropriately
        if file_path.endswith(('.py', '.java', '.js', '.ts', '.cpp', '.cs')):
            # Split by class/function definitions while preserving context
            # Basic splitting on common code block markers
            blocks = re.split(r'(?=\n(?:class|def|function|interface|public|private)\s+)', content)
            
            for i, block in enumerate(blocks):
                if len(block.strip()) > 0:
                    chunks.append({
                        'content': block.strip(),
                        'chunk_type': 'code_block',
                        'sequence': i
                    })
        else:
            # For other files, use simpler paragraph-based chunking
            paragraphs = content.split('\n\n')
            for i, para in enumerate(paragraphs):
                if len(para.strip()) > 0:
                    chunks.append({
                        'content': para.strip(),
                        'chunk_type': 'text_block',
                        'sequence': i
                    })
        
        return chunks

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
                            # Split content into chunks
                            chunks = self.chunk_content(content, file_path)
                            
                            for chunk in chunks:
                                self.collection.add(
                                    documents=[chunk['content']],
                                    metadatas=[{
                                        "file_path": relative_path,
                                        "repo_url": repo_url,
                                        "indexed_at": str(datetime.datetime.now()),
                                        "chunk_type": chunk['chunk_type'],
                                        "sequence": chunk['sequence']
                                    }],
                                    ids=[f"{repo_url}_{relative_path}_{chunk['sequence']}"]
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
            logging.info(f"Database location: {self.persist_directory}")
            
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
