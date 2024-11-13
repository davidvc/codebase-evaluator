"""Integration tests for the complete analysis workflow."""

import pytest
from pathlib import Path
from datetime import datetime
from src.workflow import analyze_repository

def test_end_to_end_workflow():
    """Test the complete analysis workflow."""
    # Use a small, stable open source repo for testing
    test_repo = "https://github.com/deweyjose/graphqlcodegen"
    
    # Run the complete analysis
    result = analyze_repository(test_repo)
    
    # Verify the workflow completed successfully
    assert len(result["messages"]) >= 3  # Should have at least 3 status messages
    assert "Repository indexed successfully" in result["messages"]
    assert "Report generated successfully" in result["messages"]
    
    # Verify that a report file was created
    reports_dir = Path("reports")
    assert reports_dir.exists(), "Reports directory should be created"
    
    # Check if report file exists
    date_str = datetime.now().strftime("%Y%m%d")
    expected_report = reports_dir / f"graphqlcodegen_report_{date_str}.md"
    assert expected_report.exists(), "Report file should be created"
    
    # Verify report contents
    with open(expected_report, 'r', encoding='utf-8') as f:
        report_content = f.read().lower()
        
    expected_sections = [
        "project architecture",
        "codebase structure",
        "technical stack",
        "implementation patterns",
        "code quality"
    ]
    
    for section in expected_sections:
        assert section in report_content, f"Report should contain section about {section}"
