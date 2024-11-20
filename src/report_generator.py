"""Module for generating codebase analysis reports."""

import os
from typing import List, Dict
from collections import defaultdict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from src.types import AnalysisState


def get_package_structure(directory: str) -> Dict[str, List[str]]:
    """Group Java files by package."""
    packages = defaultdict(list)
    for root, _, files in os.walk(directory):
        java_files = [f for f in files if f.endswith(".java")]
        if java_files:
            # Convert path to package
            package = os.path.relpath(root, directory).replace("/", ".")
            for file in java_files:
                packages[package].extend([(file, os.path.join(root, file))])
    return dict(packages)


def analyze_package(
    package: str, files: List[tuple[str, str]], model: ChatOpenAI
) -> str:
    """Analyze a single package's code."""
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a senior software architect analyzing a Java package.
        Focus on:
        - Package's purpose and responsibility
        - Key classes and their roles
        - Design patterns used
        - SOLID principles adherence
        - Code quality and maintainability
        
        Provide concrete examples from the code.
        """,
            ),
            (
                "user",
                """Analyze this Java package:
        Package: {package}
        
        Files:
        {files}
        
        Provide:
        1. Package purpose and responsibility
        2. Key classes and their interactions
        3. Design patterns identified
        4. SOLID principles evaluation
        5. Specific improvement recommendations
        """,
            ),
        ]
    )

    # Read and format files
    file_contents = []
    for filename, filepath in files:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            file_contents.append(f"File: {filename}\n```java\n{content}\n```")

    files_text = "\n\n".join(file_contents)

    chain = prompt | model
    return chain.invoke({"package": package, "files": files_text})


def synthesize_reports(
    package_analyses: Dict[str, str], model: ChatOpenAI
) -> tuple[str, str]:
    """Create overview and assessment reports from package analyses."""
    synthesis_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a senior software architect synthesizing a codebase analysis.
        Create two reports:
        1. High-level overview with architecture diagram
        2. Quality assessment with specific recommendations
        
        Focus on:
        - Overall system purpose and design
        - Component interactions
        - Architecture patterns
        - SOLID principles
        - Code maintainability
        - Test quality
        
        Include a mermaid diagram for the architecture overview.
        """,
            ),
            (
                "user",
                """Based on these package analyses, create comprehensive reports:
        
        {analyses}
        
        Generate:
        1. Overview Report:
           - System purpose and functionality
           - Key components and their roles
           - Main workflows
           - Architecture diagram (mermaid)
           
        2. Assessment Report:
           - Architecture evaluation
           - SOLID principles adherence
           - Code quality assessment
           - Test coverage and quality
           - Top 3 improvement opportunities
        """,
            ),
        ]
    )

    analyses_text = "\n\n".join(
        [f"Package: {pkg}\n{analysis}" for pkg, analysis in package_analyses.items()]
    )

    chain = synthesis_prompt | model
    combined_report = chain.invoke({"analyses": analyses_text})

    # Split into overview and assessment
    parts = combined_report.split("2. Assessment Report:")
    overview = parts[0].replace("1. Overview Report:", "").strip()
    assessment = parts[1].strip() if len(parts) > 1 else ""

    return overview, assessment


def generate_report(state: AnalysisState) -> dict:
    """Generate codebase analysis reports.

    Analyzes code package by package, then synthesizes findings into:
    1. High-level overview report
    2. Detailed quality assessment report
    """
    messages = list(state.get("messages", []))

    try:
        structure = state.get("structure_analysis")
        repo_path = state.get("repo_path")

        if not structure or not repo_path:
            messages.append("ERROR: Missing analysis results or repository path")
            return {
                **state,
                "messages": messages,
                "error": "Missing analysis results or repository path",
            }

        model = ChatOpenAI(model="gpt-4")
        package_analyses = {}

        # Analyze source code packages
        if structure["directories"]["src/main/java"]:
            main_path = os.path.join(repo_path, "src/main/java")
            packages = get_package_structure(main_path)

            messages.append(f"Analyzing {len(packages)} source packages...")
            for package, files in packages.items():
                package_analyses[package] = analyze_package(package, files, model)

        # Analyze test code packages
        if structure["directories"]["src/test/java"]:
            test_path = os.path.join(repo_path, "src/test/java")
            test_packages = get_package_structure(test_path)

            messages.append(f"Analyzing {len(test_packages)} test packages...")
            for package, files in test_packages.items():
                package_analyses[f"test.{package}"] = analyze_package(
                    package, files, model
                )

        # Synthesize reports
        messages.append("Generating final reports...")
        overview, assessment = synthesize_reports(package_analyses, model)

        full_report = f"""# Codebase Analysis Report

## Overview Report
{overview}

## Quality Assessment Report
{assessment}
"""

        messages.append("Reports generated successfully")

        return {
            **state,
            "messages": messages,
            "report": full_report,
            "repo_path": repo_path,
        }

    except Exception as e:
        messages.append(f"Error generating reports: {str(e)}")
        return {**state, "messages": messages, "error": str(e)}
