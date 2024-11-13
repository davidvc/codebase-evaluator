"""Module containing shared type definitions."""

from typing import TypedDict, Sequence, Any

class AnalysisState(TypedDict, total=False):
    """Type for the state of the analysis workflow."""
    messages: Sequence[str]
    report: str | None
    db: Any  # Can be None or Chroma
    repo_url: str
