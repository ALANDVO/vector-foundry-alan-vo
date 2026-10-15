# Vector Foundry - LLM API
"""API endpoints for optional LLM-powered insights."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.issue import TrackingIssue, IssueAnalysis
from app.services.llm import create_provider, generate_issue_summary, explain_blockers
from app.schemas.llm import (
    IssueSummaryRequest,
    IssueSummaryResponse,
    BlockersExplanationRequest,
    BlockersExplanationResponse,
    ProviderInfoResponse,
)

router = APIRouter(prefix="/llm", tags=["llm"])


@router.get("/provider", response_model=ProviderInfoResponse)
async def get_provider_info():
    """Get information about configured LLM provider."""
    from app.core.config import get_settings
    settings = get_settings()

    return ProviderInfoResponse(
        provider=settings.llm_provider if settings.llm_api_key else "none",
        model=settings.llm_model if settings.llm_api_key else None,
        base_url=settings.llm_base_url if settings.llm_api_key else None,
        configured=bool(settings.llm_api_key),
    )


@router.post("/summary", response_model=IssueSummaryResponse)
async def generate_summary(
    request: IssueSummaryRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate AI summary for an issue (advisory, opt-in)."""
    provider = create_provider()
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM provider not configured. Set LLM_API_KEY to enable.",
        )

    # Fetch issue with analysis
    result = await db.execute(
        select(TrackingIssue)
        .options(selectinload(TrackingIssue.analysis))
        .where(TrackingIssue.number == request.issue_number)
    )
    issue = result.scalar_one_or_none()

    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    if not issue.analysis:
        raise HTTPException(
            status_code=400,
            detail="Issue has not been analyzed yet. Run analysis first.",
        )

    try:
        summary = await generate_issue_summary(issue, issue.analysis, provider)
        return IssueSummaryResponse(issue_number=issue.number, summary=summary)
    finally:
        if hasattr(provider, 'close'):
            await provider.close()


@router.post("/explain-blockers", response_model=BlockersExplanationResponse)
async def explain_blockers_endpoint(
    request: BlockersExplanationRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate plain-language explanation of blockers (advisory, opt-in)."""
    provider = create_provider()
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM provider not configured. Set LLM_API_KEY to enable.",
        )

    # Fetch issue with analysis
    result = await db.execute(
        select(TrackingIssue)
        .options(selectinload(TrackingIssue.analysis))
        .where(TrackingIssue.number == request.issue_number)
    )
    issue = result.scalar_one_or_none()

    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    if not issue.analysis:
        raise HTTPException(
            status_code=400,
            detail="Issue has not been analyzed yet. Run analysis first.",
        )

    try:
        explanation = await explain_blockers(issue.analysis, provider)
        return BlockersExplanationResponse(issue_number=issue.number, explanation=explanation)
    finally:
        if hasattr(provider, 'close'):
            await provider.close()