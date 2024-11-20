"""Module for analyzing Maven project structure."""

import os
import tempfile
from git import Repo
from src.types import AnalysisState


def clone_repository(repo_url: str) -> str:
    """Clone a repository to a temporary directory."""
    temp_dir = tempfile.mkdtemp()
    Repo.clone_from(repo_url, temp_dir)
    return temp_dir


def analyze_structure(state: AnalysisState) -> dict:
    """Analyze Maven project structure.

    This function:
    1. Clones the repository
    2. Checks for Maven directory structure
    3. Stores repo path for further analysis
    """
    messages = list(state.get("messages", []))
    messages.append("Starting Maven structure analysis...")

    try:
        # Clone repository
        repo_dir = clone_repository(state["repo_url"])
        messages.append("Repository cloned successfully")

        # Check Maven directories
        maven_dirs = {
            "src/main/java": os.path.exists(os.path.join(repo_dir, "src/main/java")),
            "src/test/java": os.path.exists(os.path.join(repo_dir, "src/test/java")),
            "src/main/resources": os.path.exists(
                os.path.join(repo_dir, "src/main/resources")
            ),
            "src/test/resources": os.path.exists(
                os.path.join(repo_dir, "src/test/resources")
            ),
        }

        # Create analysis results
        analysis_results = {
            "directories": maven_dirs,
            "is_maven_project": maven_dirs[
                "src/main/java"
            ],  # Consider it Maven if it has src/main/java
        }

        messages.append("Maven structure analysis completed")

        return {
            **state,
            "messages": messages,
            "structure_analysis": analysis_results,
            "repo_path": repo_dir,  # Store repo path for other analysis steps
        }

    except Exception as e:
        messages.append(f"Error during Maven structure analysis: {str(e)}")
        return {**state, "messages": messages, "error": str(e)}
