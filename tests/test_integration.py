"""Integration tests for the complete analysis workflow."""

import os
import pytest
from pathlib import Path
from src.workflow import analyze_repository

@pytest.fixture
def test_repo_url():
    """Provide a real, public repository URL for testing."""
    return "https://github.com/eugenp/tutorials.git"

@pytest.fixture
def reports_dir():
    """Create and return the reports directory path."""
    reports_path = Path("reports")
    reports_path.mkdir(exist_ok=True)
    return reports_path

def test_end_to_end_analysis(test_repo_url, reports_dir):
    """Test the complete analysis workflow with a real repository."""
    # Run the analysis
    result = analyze_repository(test_repo_url)
    
    # Verify the analysis completed without errors
    assert "error" not in result, f"Analysis failed with error: {result.get('error')}"
    
    # Verify we got a report
    assert "report" in result
    assert isinstance(result["report"], str)
    assert len(result["report"]) > 0
    
    # Verify messages were logged
    assert "messages" in result
    assert len(result["messages"]) > 0
    
    # Verify a report file was created
    report_files = list(reports_dir.glob("*.md"))
    assert len(report_files) > 0, "No report file was generated"
    
    # Verify the latest report file has content
    latest_report = max(report_files, key=os.path.getctime)
    assert latest_report.stat().st_size > 0, "Report file is empty"

def test_analysis_with_invalid_repo():
    """Test the workflow handles invalid repository URLs gracefully."""
    invalid_url = "https://github.com/not/a/real/repository.git"
    
    # Run the analysis
    result = analyze_repository(invalid_url)
    
    # Verify we got an error
    assert "error" in result
    assert isinstance(result["error"], str)
    assert len(result["error"]) > 0
    
    # Verify error message was logged
    assert "messages" in result
    assert any("Error" in msg for msg in result["messages"]) 