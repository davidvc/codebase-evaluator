"""Module for saving generated reports to files."""

from pathlib import Path
from datetime import datetime
import re
from src.types import AnalysisState


def save_report(state: AnalysisState) -> dict:
    """Saves the generated report to a file.
    
    Args:
        state: Current state of the analysis workflow
        
    Returns:
        Updated state with save confirmation message
    """
    repo_name = state["repo_url"].rstrip('/').split('/')[-1]
    repo_name = re.sub(r'[^\w\-]', '_', repo_name)
    
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"{repo_name}_report_{date_str}.md"
    filepath = reports_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# Code Analysis Report: {repo_name}\n\n")
        f.write(f"Repository: {state['repo_url']}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        report_content = state.get("report") or "No analysis results available."
        f.write(report_content)
    
    return {**state, "messages": state["messages"] + [f"Report saved to {filepath}"]}
