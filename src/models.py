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
    """Complete analysis of a code component.
    
    This class represents the full analysis of a code component, including both its API
    surface and implementation details, along with recommendations for improvement.

    Attributes:
        name: The name of the analyzed component
        api_analysis: Analysis of the component's API surface and external interfaces
        implementation_analysis: Analysis of the component's internal implementation
        recommendations: List of specific recommendations for improvement
    """

    name: str
    api_analysis: ApiAnalysis
    implementation_analysis: ImplementationAnalysis
    recommendations: List[str] = None

    def __post_init__(self):
        """Initialize default values after dataclass initialization."""
        if self.recommendations is None:
            self.recommendations = []

    @classmethod
    def from_output(cls, output: dict) -> "ComponentAnalysis":
        """Create ComponentAnalysis from parsed output.
        
        Args:
            output: Dictionary containing component analysis data with keys:
                   - name: Component name
                   - api_analysis: API analysis data
                   - implementation_analysis: Implementation analysis data
                   - recommendations: Optional list of recommendations
        
        Returns:
            A new ComponentAnalysis instance initialized with the provided data
        """
        return cls(
            name=output["name"],
            api_analysis=ApiAnalysis.from_output(output.get("api_analysis", {})),
            implementation_analysis=ImplementationAnalysis.from_output(
                output.get("implementation_analysis", {})
            ),
            recommendations=output.get("recommendations", [])
        )
