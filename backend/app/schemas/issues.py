# Vector Foundry - Issue Schemas
"""Pydantic schemas for issue API."""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ChecklistItemResponse(BaseModel):
    """Checklist item in issue detail."""
    text: str
    completed: bool
    level: int = 0


class IssueAnalysisResponse(BaseModel):
    """Issue analysis in detail view."""
    readiness_score: int
    blocking_dependencies: List[str]
    unresolved_questions: List[dict]
    progress_summary: str
    last_analyzed: str


class IssueSummary(BaseModel):
    """Summary of an issue for list view."""
    number: int
    title: str
    body: str
    html_url: str
    state: str
    comments: int
    labels: List[dict]
    author: dict
    created_at: str
    updated_at: str
    checklist_progress: dict
    readiness_score: Optional[int] = None


class IssueListResponse(BaseModel):
    """Paginated list of issues."""
    issues: List[IssueSummary]
    total: int
    page: int
    per_page: int


class IssueDetailResponse(BaseModel):
    """Full issue detail with checklist and analysis."""
    number: int
    title: str
    body: str
    html_url: str
    state: str
    comments: int
    labels: List[dict]
    author: dict
    created_at: str
    updated_at: str
    checklist: List[ChecklistItemResponse]
    analysis: Optional[IssueAnalysisResponse] = None


class IssueComparisonRequest(BaseModel):
    """Request for comparing multiple issues."""
    numbers: List[int] = Field(default_factory=list, min_length=0, max_length=6)


class IssueComparisonResponse(BaseModel):
    """Issue data for comparison view."""
    number: int
    title: str
    labels: List[dict]
    readiness_score: Optional[int] = None
    checklist_progress: dict
    blocking_count: int
    questions_count: int
    last_analyzed: Optional[str] = None