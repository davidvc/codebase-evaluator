"""Module for analyzing Java code implementation quality."""

import json
from typing import List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from src.models import ImplementationAnalysis


class ImplementationAnalyzer:
    """Analyzes Java code implementation quality."""

    def __init__(self, model: Optional[ChatOpenAI] = None):
        """Initialize with optional custom model."""
        self.model = model or ChatOpenAI(model="gpt-4")

    def analyze(self, files: List[tuple[str, str]]) -> ImplementationAnalysis:
        """Analyze the implementation quality of Java files."""
        if not files:
            return ImplementationAnalysis({}, [], {}, {}, {})

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a senior Java architect analyzing code implementation quality.
            Focus on:
            1. Code organization and clarity
            2. Design patterns used
            3. Error handling approaches
            4. Resource management
            5. SOLID principles adherence
            
            Format your response as JSON with the following structure:
            {
                "code_organization": {"aspect1": "evaluation1", ...},
                "design_patterns": ["pattern1", ...],
                "error_handling": {"aspect1": "evaluation1", ...},
                "resource_management": {"aspect1": "evaluation1", ...},
                "solid_evaluation": {"principle1": "evaluation1", ...}
            }
            """,
                ),
                (
                    "user",
                    """Analyze these Java files focusing on implementation quality:
            
            {files}
            """,
                ),
            ]
        )

        try:
            files_text = "\n\n".join(
                [f"File: {path}\n```java\n{content}\n```" for path, content in files]
            )

            # Get implementation analysis
            result = self.model.invoke(prompt.format_messages(files=files_text))

            # Parse the response
            try:
                if isinstance(result.content, dict):
                    output = result.content
                else:
                    output = json.loads(result.content)
                return ImplementationAnalysis.from_output(output)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON response: {str(e)}")
                print(f"Raw response: {result.content}")
                return ImplementationAnalysis({}, [], {}, {}, {})

        except Exception as e:
            print(f"Error in implementation analysis: {str(e)}")
            return ImplementationAnalysis({}, [], {}, {}, {})
