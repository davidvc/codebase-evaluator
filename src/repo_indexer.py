import os
import tempfile
from git import Repo, GitCommandError
import chromadb
from typing import List, Dict, Optional
import datetime
import shutil
import logging
import re
from urllib.parse import urlparse
from langchain_openai import OpenAIEmbeddings


class RepoIndexerError(Exception):
    """Base exception class for RepoIndexer errors."""
    pass


class InvalidRepositoryError(RepoIndexerError):
    """Raised when the repository URL is invalid or inaccessible."""
    pass


class FileProcessingError(RepoIndexerError):
    """Raised when there's an error processing a specific file."""
    pass


class DatabaseError(RepoIndexerError):
    """Raised when there's an error interacting with ChromaDB."""
    pass


class OpenAIEmbeddingFunction:
    """Wrapper class to make OpenAIEmbeddings compatible with ChromaDB's interface."""
    def __init__(self):
        self._embeddings = OpenAIEmbeddings()
        
    def __call__(self, input: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        return self._embeddings.embed_documents(input)


class RepoIndexer:
    # Maximum repository size in bytes (1GB)
    MAX_REPO_SIZE = 1024 * 1024 * 1024
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """Initialize RepoIndexer with persistent storage.
        
        Args:
            persist_directory: Path to store the ChromaDB database
            
        Raises:
            DatabaseError: If there's an error initializing ChromaDB
        """
        try:
            # Get absolute path and current working directory
            cwd = os.getcwd()
            self.persist_directory = os.path.abspath(persist_directory)
            
            logging.info("\n=== ChromaDB Initialization ===")
            logging.info(f"Current working directory: {cwd}")
            logging.info(f"Database directory (relative): {persist_directory}")
            logging.info(f"Database directory (absolute): {self.persist_directory}")
            
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
                
        except Exception as e:
            raise DatabaseError(f"Failed to initialize ChromaDB: {str(e)}") from e

    def validate_repo_url(self, repo_url: str) -> None:
        """Validate the repository URL format.
        
        Args:
            repo_url: URL of the repository to validate
            
        Raises:
            InvalidRepositoryError: If the URL is invalid
        """
        try:
            parsed = urlparse(repo_url)
            if not all([parsed.scheme, parsed.netloc]):
                raise InvalidRepositoryError("Invalid repository URL format")
            if not repo_url.endswith('.git'):
                raise InvalidRepositoryError("URL must end with .git")
        except Exception as e:
            raise InvalidRepositoryError(f"Invalid repository URL: {str(e)}") from e

    def clone_repo(self, repo_url: str) -> str:
        """Clone a GitHub repository to a temporary directory.
        
        Args:
            repo_url: URL of the repository to clone
            
        Returns:
            Path to the cloned repository
            
        Raises:
            InvalidRepositoryError: If cloning fails or repo is too large
        """
        self.validate_repo_url(repo_url)
        
        logging.info(f"\nCloning repository: {repo_url}")
        temp_dir = tempfile.mkdtemp()
        logging.info(f"Created temporary directory: {temp_dir}")
        
        try:
            repo = Repo.clone_from(repo_url, temp_dir)
            
            # Check repository size
            repo_size = sum(
                os.path.getsize(os.path.join(dirpath, filename))
                for dirpath, _, filenames in os.walk(temp_dir)
                for filename in filenames
            )
            if repo_size > self.MAX_REPO_SIZE:
                shutil.rmtree(temp_dir)
                raise InvalidRepositoryError(
                    f"Repository size ({repo_size} bytes) exceeds maximum allowed size ({self.MAX_REPO_SIZE} bytes)"
                )
                
            logging.info("Repository cloned successfully")
            return temp_dir
            
        except GitCommandError as e:
            shutil.rmtree(temp_dir)
            raise InvalidRepositoryError(f"Failed to clone repository: {str(e)}") from e
        except Exception as e:
            shutil.rmtree(temp_dir)
            raise InvalidRepositoryError(f"Unexpected error while cloning: {str(e)}") from e

    def read_file_content(self, file_path: str) -> Optional[str]:
        """Read and return the content of a file.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            File content as string, or None if file should be skipped
            
        Raises:
            FileProcessingError: If there's an error reading the file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content.strip():
                    logging.warning(f"Skipping empty file: {file_path}")
                    return None
                return content
        except UnicodeDecodeError:
            logging.warning(f"Skipping binary file: {file_path}")
            return None
        except Exception as e:
            raise FileProcessingError(f"Error reading file {file_path}: {str(e)}") from e

    def chunk_content(self, content: str, file_path: str) -> List[Dict]:
        """Split content into smaller, meaningful chunks.
        
        Args:
            content: File content to chunk
            file_path: Path of the file being chunked
            
        Returns:
            List of chunks with metadata
        """
        chunks = []
        
        # Handle different file types appropriately
        if file_path.endswith(('.py', '.java', '.js', '.ts', '.cpp', '.cs')):
            # Split by class/function definitions while preserving context
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

    def index_repo(self, repo_url: str) -> Dict[str, int]:
        """Index a GitHub repository into ChromaDB.
        
        Args:
            repo_url: URL of the repository to index
            
        Returns:
            Dictionary with indexing statistics
            
        Raises:
            InvalidRepositoryError: If repository is invalid or inaccessible
            DatabaseError: If there's an error with ChromaDB operations
            FileProcessingError: If there's an error processing files
        """
        logging.info(f"\n=== Starting indexing process for {repo_url} ===")
        repo_path = None
        files_processed = 0
        files_skipped = 0
        files_failed = 0
        
        try:
            repo_path = self.clone_repo(repo_url)
            
            # Get existing indexed files
            logging.debug("\nChecking for previously indexed files...")
            existing_files = set()
            try:
                if len(self.collection.get()['ids']) > 0:
                    existing_metadata = self.collection.get()['metadatas']
                    existing_files = {meta['file_path'] for meta in existing_metadata}
                    logging.debug(f"Found {len(existing_files)} previously indexed files")
            except Exception as e:
                raise DatabaseError(f"Error getting existing files: {str(e)}") from e
            
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
                    
                    try:
                        content = self.read_file_content(file_path)
                        if content is None:
                            files_skipped += 1
                            continue
                            
                        # Split content into chunks
                        chunks = self.chunk_content(content, file_path)
                        
                        for chunk in chunks:
                            try:
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
                            except Exception as e:
                                raise DatabaseError(f"Error adding chunk to database: {str(e)}") from e
                        
                        files_processed += 1
                        logging.debug(f"Successfully indexed: {relative_path}")
                        
                        if files_processed % 100 == 0:
                            logging.info(f"Progress: Processed {files_processed} new files")
                            
                    except FileProcessingError as e:
                        logging.error(str(e))
                        files_failed += 1
                        continue
            
            stats = {
                "files_processed": files_processed,
                "files_skipped": files_skipped,
                "files_failed": files_failed,
                "total_files": files_processed + files_skipped + files_failed
            }
            
            logging.info(f"\n=== Indexing Summary ===")
            logging.info(f"Repository: {repo_url}")
            logging.info(f"New files indexed: {files_processed}")
            logging.info(f"Files skipped: {files_skipped}")
            logging.info(f"Files failed: {files_failed}")
            logging.info(f"Total files encountered: {stats['total_files']}")
            logging.info(f"Database location: {self.persist_directory}")
            
            return stats
            
        except (InvalidRepositoryError, DatabaseError) as e:
            logging.error(str(e))
            raise
        finally:
            if repo_path:
                logging.debug(f"\nCleaning up temporary directory: {repo_path}")
                try:
                    shutil.rmtree(repo_path)
                    logging.debug("Cleanup successful")
                except Exception as e:
                    logging.error(f"Error during cleanup: {str(e)}")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Example usage
    indexer = RepoIndexer()
    repo_url = "https://github.com/example/repo.git"  # Replace with actual repo URL
    try:
        stats = indexer.index_repo(repo_url)
        print(f"\nIndexing completed successfully. Stats: {stats}")
    except RepoIndexerError as e:
        print(f"\nError during indexing: {str(e)}")
