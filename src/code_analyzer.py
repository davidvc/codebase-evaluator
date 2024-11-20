"""Module for complete Java code analysis."""

import os
from typing import List, Optional
from langchain_openai import ChatOpenAI
from src.models import ComponentAnalysis, ApiAnalysis, ImplementationAnalysis
from src.api_analyzer import ApiAnalyzer
from src.implementation_analyzer import ImplementationAnalyzer


class CodeAnalyzer:
    """Analyzes Java code at both API and implementation levels."""

    def __init__(self, model: Optional[ChatOpenAI] = None):
        """Initialize with optional custom model."""
        self.api_analyzer = ApiAnalyzer(model)
        self.impl_analyzer = ImplementationAnalyzer(model)

    def analyze_component(self, component_path: str) -> ComponentAnalysis:
        """Perform complete analysis of a code component.

        Args:
            component_path: Path to the component directory

        Returns:
            ComponentAnalysis containing both API and implementation analysis
        """
        try:
            # Read all Java files in the component
            java_files = []
            for root, _, files in os.walk(component_path):
                for file in files:
                    if file.endswith(".java"):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, "r", encoding="utf-8") as f:
                                content = f.read()
                            rel_path = os.path.relpath(file_path, component_path)
                            java_files.append((rel_path, content))
                        except Exception as e:
                            print(f"Error reading file {file_path}: {str(e)}")
                            continue

            if not java_files:
                return ComponentAnalysis(
                    name=os.path.basename(component_path),
                    api_analysis=ApiAnalysis([], [], [], []),
                    implementation_analysis=ImplementationAnalysis({}, [], {}, {}, {}),
                )

            # Perform both levels of analysis
            api_analysis = self.api_analyzer.analyze(java_files)
            impl_analysis = self.impl_analyzer.analyze(java_files)

            return ComponentAnalysis(
                name=os.path.basename(component_path),
                api_analysis=api_analysis,
                implementation_analysis=impl_analysis,
            )

        except Exception as e:
            print(f"Error analyzing component: {str(e)}")
            return ComponentAnalysis(
                name=os.path.basename(component_path),
                api_analysis=ApiAnalysis([], [], [], []),
                implementation_analysis=ImplementationAnalysis({}, [], {}, {}, {}),
            )
