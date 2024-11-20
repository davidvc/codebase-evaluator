"""Shared data models for code analysis."""

from dataclasses import dataclass
from typing import List, Dict
from pydantic import BaseModel, Field


class ApiAnalysisOutput(BaseModel):
    """Structure for API analysis output."""

    public_interfaces: List[str] = Field(
        description="List of public interfaces and their purposes"
    )
    component_interactions: List[str] = Field(
        description="List of component interactions"
    )
    behaviors: List[str] = Field(description="List of key behaviors")
    external_dependencies: List[str] = Field(
        description="List of external dependencies"
    )


class ImplementationAnalysisOutput(BaseModel):
    """Structure for implementation analysis output."""

    code_organization: Dict[str, str] = Field(
        description="Assessment of code organization"
    )
    design_patterns: List[str] = Field(description="List of identified design patterns")
    error_handling: Dict[str, str] = Field(description="Assessment of error handling")
    resource_management: Dict[str, str] = Field(
        description="Assessment of resource management"
    )
    solid_evaluation: Dict[str, str] = Field(
        description="Evaluation against SOLID principles"
    )


@dataclass
class ApiAnalysis:
    """Analysis of a component's API surface."""

    public_interfaces: List[str]
    component_interactions: List[str]
    behaviors: List[str]
    external_dependencies: List[str]

    @classmethod
    def from_output(cls, output: dict) -> "ApiAnalysis":
        """Create ApiAnalysis from parsed output."""
        return cls(
            public_interfaces=output.get("public_interfaces", []),
            component_interactions=output.get("component_interactions", []),
            behaviors=output.get("behaviors", []),
            external_dependencies=output.get("external_dependencies", []),
        )


@dataclass
class ImplementationAnalysis:
    """Analysis of a component's implementation details."""

    code_organization: Dict[str, str]
    design_patterns: List[str]
    error_handling: Dict[str, str]
    resource_management: Dict[str, str]
    solid_evaluation: Dict[str, str]

    @classmethod
    def from_output(cls, output: dict) -> "ImplementationAnalysis":
        """Create ImplementationAnalysis from parsed output."""
        return cls(
            code_organization=output.get("code_organization", {}),
            design_patterns=output.get("design_patterns", []),
            error_handling=output.get("error_handling", {}),
            resource_management=output.get("resource_management", {}),
            solid_evaluation=output.get("solid_evaluation", {}),
        )


@dataclass
class ComponentAnalysis:
    """Complete analysis of a code component."""

    name: str
    api_analysis: ApiAnalysis
    implementation_analysis: ImplementationAnalysis
    quality_score: float
    recommendations: List[str]
