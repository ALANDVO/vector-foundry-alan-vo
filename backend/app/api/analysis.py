# Vector Foundry - Analysis API
"""API endpoints for analysis of tracking issues."""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.issue import TrackingIssue
from app.schemas.issues import IssueAnalysisResponse
from app.services.analysis import update_issue_analysis


router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/{issue_number}", response_model=IssueAnalysisResponse)
async def get_issue_analysis(
    issue_number: int,
    db: AsyncSession = Depends(get_db),
) -> IssueAnalysisResponse:
    """Get analysis for a specific tracking issue."""
    # Find the issue
    result = await db.execute(
        select(TrackingIssue).where(TrackingIssue.number == issue_number)
    )
    issue = result.scalar_one_or_none()
    if not issue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")

    # Compute or retrieve analysis
    analysis = issue.analysis
    if not analysis:
        analysis = await update_issue_analysis(db, issue)

    # Build response
    return IssueAnalysisResponse(
        readiness_score=analysis.readiness_score,
        blocking_dependencies=analysis.blocking_dependencies,
        unresolved_questions=analysis.unresolved_questions,
        progress_summary=analysis.progress_summary,
        last_analyzed=analysis.last_analyzed.isoformat(),
    )
