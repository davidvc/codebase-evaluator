"""Module defining the Maven analysis workflow."""

from langgraph.graph import StateGraph, END
from src.types import AnalysisState
from src.structure_analysis import analyze_structure
from src.report_generator import generate_report
from src.report_writer import save_report


def create_analysis_workflow():
    """Creates a graph for the Maven analysis workflow.

    Returns:
        A compiled LangGraph workflow for Maven analysis
    """
    # Create the graph
    workflow = StateGraph(AnalysisState)

    # Define tasks
    tasks = [
        {"name": "structure_analysis", "function": analyze_structure},
        {"name": "report_generation", "function": generate_report},
        {"name": "save_report", "function": save_report},
    ]

    # Add nodes
    for task in tasks:
        workflow.add_node(task["name"], task["function"])

    # Add edges
    workflow.set_entry_point("structure_analysis")
    workflow.add_edge("structure_analysis", "report_generation")
    workflow.add_edge("report_generation", "save_report")
    workflow.add_edge("save_report", END)

    return workflow.compile()


def analyze_repository(repo_url: str) -> dict:
    """Analyzes a Maven repository and generates a report.

    Args:
        repo_url: URL of the repository to analyze

    Returns:
        Dictionary containing the analysis results and messages
    """
    workflow = create_analysis_workflow()

    result = workflow.invoke(
        {"messages": [], "report": None, "db": None, "repo_url": repo_url}
    )

    return result
