"""Module defining the complete analysis workflow."""

from langgraph.graph import StateGraph, END
from src.repo_indexer import RepoIndexer
from src.report_generator import generate_report
from src.report_writer import save_report
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores.chroma import Chroma
from src.types import AnalysisState


def create_analysis_workflow():
    """Creates a graph for the complete analysis workflow.
    
    Returns:
        A compiled LangGraph workflow for the complete analysis
    """
    # Create the graph
    workflow = StateGraph(AnalysisState)
    
    # Define the indexing node
    def index_repository(state: AnalysisState) -> dict:
        """Creates a vector database from the repository."""
        indexer = RepoIndexer()
        indexer.index_repo(state["repo_url"])
        
        # Create embedding function
        embedding_function = OpenAIEmbeddings()
        
        # Convert ChromaDB collection to LangChain vector store
        langchain_db = Chroma(
            client=indexer.client,
            collection_name="code_chunks",
            embedding_function=embedding_function
        )
        
        return {
            "db": langchain_db,
            "messages": list(state["messages"]) + ["Repository indexed successfully"],
            "report": state.get("report"),
            "repo_url": state["repo_url"]
        }
    
    # Add nodes
    workflow.add_node("index", index_repository)
    workflow.add_node("analyze", generate_report)
    workflow.add_node("save", save_report)
    
    # Add edges
    workflow.set_entry_point("index")
    workflow.add_edge("index", "analyze")
    workflow.add_edge("analyze", "save")
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
