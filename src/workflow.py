"""Module defining the complete analysis workflow."""

import json
from langgraph.graph import StateGraph, END
from src.repo_indexer import RepoIndexer
from src.report_generator import generate_report
from src.report_writer import save_report
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores.chroma import Chroma
from src.types import AnalysisState
from src.structure_analysis import analyze_structure
from src.component_discovery import discover_components
from src.integration_analysis import analyze_integration

# Load custom model configuration
with open('src/custom_model_config.json', 'r') as config_file:
    custom_model_config = json.load(config_file)

def create_analysis_workflow():
    """Creates a graph for the complete analysis workflow.
    
    Returns:
        A compiled LangGraph workflow for the complete analysis
    """
    # Create the graph
    workflow = StateGraph(AnalysisState)
    
    # Define tasks
    tasks = [
        {"name": "structure_analysis", "function": analyze_structure, "parallel": True},
        {"name": "component_discovery", "function": discover_components, "parallel": True},
        {"name": "integration_analysis", "function": analyze_integration, "parallel": False},
        {"name": "quality_assessment", "function": generate_report, "parallel": False}
    ]
    
    # Define the indexing node
    def index_repository(state: AnalysisState) -> dict:
        """Creates a vector database from the repository."""
        indexer = RepoIndexer()
        indexer.index_repo(state["repo_url"])
        
        # Create embedding function using custom model
        embedding_function = ChatOpenAI(
            model_url=custom_model_config["model_url"],
            api_key=custom_model_config["api_key"],
            model_name=custom_model_config["model_name"]
        )
        
        # Convert ChromaDB collection to LangChain vector store
        langchain_db = Chroma(
            client=indexer.client,
            collection_name="code_chunks",
            embedding_function=embedding_function
        )
        
        return {
            "db": langchain_db,
            "messages": list(state["messages"]) + 
                        ["Repository indexed successfully"],
            "report": state.get("report"),
            "repo_url": state["repo_url"]
        }
    
    # Add nodes dynamically based on tasks
    workflow.add_node("index", index_repository)
    for task in tasks:
        workflow.add_node(task["name"], task["function"])
    
    # Add edges
    workflow.set_entry_point("index")
    for i in range(len(tasks) - 1):
        workflow.add_edge(tasks[i]["name"], tasks[i + 1]["name"])
    workflow.add_edge(tasks[-1]["name"], "save")
    workflow.add_edge("save", END)
    
    return workflow.compile()


def analyze_repository(repo_url: str) -> dict:
    """Analyzes a repository and generates a report.
    
    Args:
        repo_url: URL of the repository to analyze
        
    Returns:
        Dictionary containing the analysis results and messages
    """
    workflow = create_analysis_workflow()
    
    result = workflow.invoke({
        "messages": [],
        "report": "",
        "db": None,
        "repo_url": repo_url
    })
    
    return result
