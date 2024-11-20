"""Module for analyzing Java API surfaces."""

import json
from typing import List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from src.models import ApiAnalysis


class ApiAnalyzer:
    """Analyzes Java code API surfaces."""

    def __init__(self, model: Optional[ChatOpenAI] = None):
        """Initialize with optional custom model."""
        self.model = model or ChatOpenAI(model="gpt-4")

    def analyze(self, files: List[tuple[str, str]]) -> ApiAnalysis:
        """Analyze the API surface of Java files."""
        if not files:
            return ApiAnalysis([], [], [], [])

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a senior Java architect analyzing a component's API surface.
            Focus on:
            1. Public interfaces and their contracts
            2. Component interactions and dependencies
            3. System behaviors implemented
            4. External dependencies and their usage
            
            Format your response as JSON with the following structure:
            {
                "public_interfaces": ["interface1: purpose", ...],
                "component_interactions": ["interaction1", ...],
                "behaviors": ["behavior1", ...],
                "external_dependencies": ["dependency1", ...]
            }
            """,
                ),
                (
                    "user",
                    """Analyze these Java files focusing on their API surface:
            
            {files}
            """,
                ),
            ]
        )

        try:
            # Format files for analysis
            files_text = "\n\n".join(
                [f"File: {path}\n```java\n{content}\n```" for path, content in files]
            )

            # Get API analysis
            result = self.model.invoke(prompt.format_messages(files=files_text))

            analysis_dict = json.loads(result.content)
            
            return ApiAnalysis(
                public_interfaces=analysis_dict.get("public_interfaces", []),
                component_interactions=analysis_dict.get("component_interactions", []),
                behaviors=analysis_dict.get("behaviors", []),
                external_dependencies=analysis_dict.get("external_dependencies", [])
            )

        except Exception as e:
            print(f"Error in API analysis: {str(e)}")
            return ApiAnalysis([], [], [], [])
