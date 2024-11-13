"""Module for generating codebase analysis reports."""

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
import chromadb
from src.types import AnalysisState

# Load environment variables from .env file
load_dotenv()

def truncate_content(content: str, max_chars: int = 1000) -> str:
    """Truncate content if it exceeds max_chars while preserving meaningful context."""
    if len(content) <= max_chars:
        return content
    
    # Try to find a good breaking point
    break_point = content[:max_chars].rfind('\n\n')
    if break_point == -1:
        break_point = content[:max_chars].rfind('\n')
    if break_point == -1:
        break_point = content[:max_chars].rfind('. ')
    if break_point == -1:
        break_point = max_chars
    
    return content[:break_point] + "\n... (content truncated)"

def organize_contexts(results) -> str:
    """Organize search results into a coherent context structure."""
    organized = {}
    
    # Process results from similarity_search_with_score which returns [(Document, score), ...]
    for doc, score in results:
        file_path = doc.metadata['file_path']
        
        if file_path not in organized:
            organized[file_path] = []
            
        organized[file_path].append({
            'content': truncate_content(doc.page_content),
            'sequence': doc.metadata.get('sequence', 0)
        })
    
    # Sort chunks within each file by sequence
    context_parts = []
    for file_path, chunks in organized.items():
        chunks.sort(key=lambda x: x['sequence'])
        context_parts.append(f"File: {file_path}\n" + 
                           "\n".join(chunk['content'] for chunk in chunks))
    
    return "\n\n" + "="*50 + "\n\n".join(context_parts)

def generate_report(state: AnalysisState) -> dict:
    """Analyzes code and generates a report.
    
    Args:
        state: AnalysisState object containing indexed code snippets
        
    Returns:
        Updated state with generated report
    """
    # Initialize our chat model
    model = ChatOpenAI(model="gpt-4")
    
    # Define analysis queries to get comprehensive coverage
    analysis_queries = [
        "Find all main entry points and core modules of the application",
        "Identify key classes, interfaces, and their relationships",
        "Locate configuration files and environment setup code",
        "Find database models and data access patterns",
        "Identify API endpoints and service interfaces",
        "Locate test files and testing patterns",
        "Find dependency injection and service registration code",
        "Identify error handling and logging mechanisms",
        "Find authentication and authorization implementations",
        "Locate performance-critical code sections"
    ]
    
    # Gather context from multiple targeted searches
    contexts = []
    collection = state["db"]
    
    for query in analysis_queries:
        results = collection.similarity_search_with_score(
            query,
            k=5  # Reduced from 10 to 5 to limit token count
        )
        contexts.append(f"Results for '{query}':\n" + 
                      organize_contexts(results))
    
    full_context = "\n\n" + "="*50 + "\n\n".join(contexts)
    
    # Create our prompt for analyzing the codebase
    analyze_prompt = ChatPromptTemplate.from_messages([
        ("system", 
         """You are a senior software architect tasked with performing in-depth codebase analysis. 
         Generate a comprehensive technical report that covers:

        1. Project Architecture
           - Overall architectural style (e.g., MVC, microservices, layered)
           - System boundaries and main components
           - Data flow between components
           
        2. Codebase Structure
           - Main entry points and bootstrapping process
           - Core modules and their responsibilities
           - Directory organization and code layout
           
        3. Technical Stack
           - Programming languages and versions
           - Frameworks and major libraries
           - Database technologies and data storage
           - External services and integrations
           
        4. Implementation Patterns
           - Design patterns utilized
           - Error handling and logging approaches
           - Security mechanisms
           - Testing strategy and coverage
           - Performance considerations
           
        5. Code Quality & Maintainability
           - Code organization principles
           - Dependency management
           - Configuration management
           - Documentation practices

        Provide specific examples from the code to support your findings.
        Focus on factual observations rather than suggestions or critiques.
        If certain aspects cannot be determined from the available code, note this explicitly."""),
        ("user", "Analyze the following code sections:\n{context}")
    ])
    
    chain = analyze_prompt | model | StrOutputParser()
    report = chain.invoke({"context": full_context})
    
    return {
        "report": report,
        "messages": list(state["messages"]) + ["Report generated successfully"],
        "db": state["db"],
        "repo_url": state["repo_url"]
    }
