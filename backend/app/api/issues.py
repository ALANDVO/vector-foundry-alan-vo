# Vector Foundry - Issues API
"""API endpoints for tracking issues."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.issue import TrackingIssue, ChecklistItem, IssueAnalysis
from app.schemas.issues import (
    IssueListResponse,
    IssueDetailResponse,
    IssueComparisonRequest,
    IssueComparisonResponse,
    ChecklistItemResponse,
    IssueAnalysisResponse,
)

router = APIRouter(prefix="/issues", tags=["issues"])


@router.get("", response_model=IssueListResponse)
async def list_issues(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in title and body"),
    label: Optional[str] = Query(None, description="Filter by label name"),
    state: str = Query("open", description="Filter by state: open, closed, all"),
    sort: str = Query("updated", description="Sort field: updated, created, comments, readiness"),
    order: str = Query("desc", description="Sort order: asc, desc"),
    db: AsyncSession = Depends(get_db),
) -> IssueListResponse:
    """List tracking issues with pagination, filtering, and sorting."""
    query = select(TrackingIssue)

    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                TrackingIssue.title.ilike(search_term),
                TrackingIssue.body.ilike(search_term),
            )
        )

    if label:
        query = query.where(TrackingIssue.labels.any(lambda l: l["name"] == label))

    if state != "all":
        query = query.where(TrackingIssue.state == state)

    # Apply sorting
    sort_column = {
        "updated": TrackingIssue.updated_at,
        "created": TrackingIssue.created_at,
        "comments": TrackingIssue.comments,
        "readiness": IssueAnalysis.readiness_score,
    }.get(sort, TrackingIssue.updated_at)

    if sort == "readiness":
        query = query.outerjoin(IssueAnalysis, TrackingIssue.id == IssueAnalysis.issue_id)
        sort_column = IssueAnalysis.readiness_score

    if order == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    # Apply pagination
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    issues = result.scalars().all()

    # Fetch analyses for these issues
    issue_ids = [issue.id for issue in issues]
    analyses = {}
    if issue_ids:
        analysis_result = await db.execute(
            select(IssueAnalysis).where(IssueAnalysis.issue_id.in_(issue_ids))
        )
        analyses = {a.issue_id: a for a in analysis_result.scalars().all()}

    # Fetch checklist counts for these issues
    checklist_counts = {}
    if issue_ids:
        checklist_result = await db.execute(
            select(ChecklistItem.issue_id, func.count(ChecklistItem.id).label("total"),
                   func.sum(ChecklistItem.completed).label("completed"))
            .where(ChecklistItem.issue_id.in_(issue_ids))
            .group_by(ChecklistItem.issue_id)
        )
        for row in checklist_result.all():
            checklist_counts[row.issue_id] = {"completed": row.completed or 0, "total": row.total or 0}

    # Build response items
    items = []
    for issue in issues:
        analysis = analyses.get(issue.id)
        checklist = checklist_counts.get(issue.id, {"completed": 0, "total": 0})

        items.append({
            "number": issue.number,
            "title": issue.title,
            "body": issue.body,
            "html_url": issue.html_url,
            "state": issue.state,
            "comments": issue.comments,
            "labels": issue.labels,
            "author": {"login": issue.author_login, "avatar_url": issue.author_avatar_url},
            "created_at": issue.created_at.isoformat(),
            "updated_at": issue.updated_at.isoformat(),
            "checklist_progress": checklist,
            "readiness_score": analysis.readiness_score if analysis else None,
        })

    return IssueListResponse(issues=items, total=total, page=page, per_page=per_page)


@router.get("/{number}", response_model=IssueDetailResponse)
async def get_issue(
    number: int,
    db: AsyncSession = Depends(get_db),
) -> IssueDetailResponse:
    """Get a single tracking issue with full details."""
    # Get issue
    result = await db.execute(
        select(TrackingIssue).where(TrackingIssue.number == number)
    )
    issue = result.scalar_one_or_none()

    if not issue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")

    # Get checklist items
    checklist_result = await db.execute(
        select(ChecklistItem)
        .where(ChecklistItem.issue_id == issue.id)
        .order_by(ChecklistItem.position)
    )
    checklist_items = [
        ChecklistItemResponse(text=item.text, completed=item.completed, level=item.level)
        for item in checklist_result.scalars().all()
    ]

    # Get analysis
    analysis_result = await db.execute(
        select(IssueAnalysis).where(IssueAnalysis.issue_id == issue.id)
    )
    analysis = analysis_result.scalar_one_or_none()

    analysis_resp = None
    if analysis:
        analysis_resp = IssueAnalysisResponse(
            readiness_score=analysis.readiness_score,
            blocking_dependencies=analysis.blocking_dependencies,
            unresolved_questions=analysis.unresolved_questions,
            progress_summary=analysis.progress_summary,
            last_analyzed=analysis.last_analyzed.isoformat(),
        )

    return IssueDetailResponse(
        number=issue.number,
        title=issue.title,
        body=issue.body,
        html_url=issue.html_url,
        state=issue.state,
        comments=issue.comments,
        labels=issue.labels,
        author={"login": issue.author_login, "avatar_url": issue.author_avatar_url},
        created_at=issue.created_at.isoformat(),
        updated_at=issue.updated_at.isoformat(),
        checklist=checklist_items,
        analysis=analysis_resp,
    )


@router.post("/compare", response_model=List[IssueComparisonResponse])
async def compare_issues(
    request: IssueComparisonRequest,
    db: AsyncSession = Depends(get_db),
) -> List[IssueComparisonResponse]:
    """Compare multiple issues side by side."""
    if not request.numbers:
        return []

    if len(request.numbers) > 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot compare more than 6 issues at once",
        )

    # Get issues
    result = await db.execute(
        select(TrackingIssue)
        .where(TrackingIssue.number.in_(request.numbers))
    )
    issues = result.scalars().all()

    issue_ids = [issue.id for issue in issues]
    issue_map = {issue.number: issue for issue in issues}

    # Get analyses
    analysis_result = await db.execute(
        select(IssueAnalysis).where(IssueAnalysis.issue_id.in_(issue_ids))
    )
    analyses = {a.issue_id: a for a in analysis_result.scalars().all()}

    # Get checklist counts
    checklist_result = await db.execute(
        select(ChecklistItem.issue_id, func.count(ChecklistItem.id).label("total"),
               func.sum(ChecklistItem.completed).label("completed"))
        .where(ChecklistItem.issue_id.in_(issue_ids))
        .group_by(ChecklistItem.issue_id)
    )
    checklist_counts = {row.issue_id: {"completed": row.completed or 0, "total": row.total or 0}
                        for row in checklist_result.all()}

    # Preserve order from request
    ordered_issues = [issue_map.get(n) for n in request.numbers if n in issue_map]

    response = []
    for issue in ordered_issues:
        analysis = analyses.get(issue.id)
        checklist = checklist_counts.get(issue.id, {"completed": 0, "total": 0})

        response.append(IssueComparisonResponse(
            number=issue.number,
            title=issue.title,
            labels=issue.labels,
            readiness_score=analysis.readiness_score if analysis else None,
            checklist_progress=checklist,
            blocking_count=len(analysis.blocking_dependencies) if analysis else 0,
            questions_count=len(analysis.unresolved_questions) if analysis else 0,
            last_analyzed=analysis.last_analyzed.isoformat() if analysis else None,
        ))

    return response