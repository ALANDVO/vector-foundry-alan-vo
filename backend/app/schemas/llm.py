# Vector Foundry - LLM Schemas
"""Pydantic schemas for LLM API."""

from typing import Optional
from pydantic import BaseModel, ConfigDict


class ProviderInfoResponse(BaseModel):
    """LLM provider configuration info."""
    provider: str
    model: Optional[str] = None
    base_url: Optional[str] = None
    configured: bool


class IssueSummaryRequest(BaseModel):
    """Request for issue summary."""
    issue_number: int


class IssueSummaryResponse(BaseModel):
    """AI-generated issue summary."""
    issue_number: int
    summary: str


class BlockersExplanationRequest(BaseModel):
    """Request for blockers explanation."""
    issue_number: int


class BlockersExplanationResponse(BaseModel):
    """AI-generated blockers explanation."""
    issue_number: int
    explanation: str