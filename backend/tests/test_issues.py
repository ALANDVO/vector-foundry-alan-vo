# Vector Foundry - Issues Tests
"""Tests for issues API endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.models.issue import TrackingIssue, ChecklistItem, IssueAnalysis


@pytest.fixture
async def sample_issues(db_session: AsyncSession):
    """Create sample issues for testing."""
    issues = []

    # Issue 1: High readiness, many checklist items completed
    issue1 = TrackingIssue(
        number=31844,
        title="Tracking issue for specialization (RFC 1210)",
        body="""
## Implementation Steps
- [x] Land https://github.com/rust-lang/rust/pull/30652 =)
- [ ] Restrictions around lifetime dispatch (currently a **soundness hole**)
- [ ] `default impl` (https://github.com/rust-lang/rust/issues/37653)
- [ ] Integration with associated consts
""",
        html_url="https://github.com/rust-lang/rust/issues/31844",
        state="open",
        comments=323,
        labels=[{"name": "F-specialization", "color": "ff0000"}, {"name": "tracking-issue", "color": "00ff00"}],
        author_login="rust-lang",
        author_avatar_url="https://github.com/rust-lang.png",
        created_at=datetime(2019, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    db_session.add(issue1)
    await db_session.flush()

    # Add checklist items
    checklist1 = [
        ChecklistItem(issue_id=issue1.id, text="Land PR #30652", completed=True, level=0, position=0),
        ChecklistItem(issue_id=issue1.id, text="Restrictions around lifetime dispatch", completed=False, level=0, position=1),
        ChecklistItem(issue_id=issue1.id, text="default impl", completed=False, level=0, position=2),
        ChecklistItem(issue_id=issue1.id, text="Integration with associated consts", completed=False, level=0, position=3),
    ]
    for item in checklist1:
        db_session.add(item)

    # Add analysis
    analysis1 = IssueAnalysis(
        issue_id=issue1.id,
        readiness_score=45,
        blocking_dependencies=["Lifetime dispatch soundness hole", "References rust-lang/rust#37653"],
        unresolved_questions=[
            {"category": "Soundness", "question": "Should associated type be specializable at all?"},
            {"category": "API Design", "question": "When should projection reveal a default type?"},
        ],
        progress_summary="Specialization has partial implementation but soundness issues remain unresolved.",
        checklist_completed=1,
        checklist_total=4,
    )
    db_session.add(analysis1)

    issues.append(issue1)

    # Issue 2: Lower readiness, fewer comments
    issue2 = TrackingIssue(
        number=43467,
        title="Tracking issue for RFC 1861: Extern types",
        body="""
## Steps
- [x] Implement the RFC (#44295)
- [ ] Adjust documentation
- [ ] Stabilization PR
""",
        html_url="https://github.com/rust-lang/rust/issues/43467",
        state="open",
        comments=292,
        labels=[{"name": "F-extern-types", "color": "ff0000"}, {"name": "tracking-issue", "color": "00ff00"}],
        author_login="rust-lang",
        author_avatar_url="https://github.com/rust-lang.png",
        created_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2024, 6, 1, tzinfo=timezone.utc),
    )
    db_session.add(issue2)
    await db_session.flush()

    checklist2 = [
        ChecklistItem(issue_id=issue2.id, text="Implement the RFC", completed=True, level=0, position=0),
        ChecklistItem(issue_id=issue2.id, text="Adjust documentation", completed=False, level=0, position=1),
        ChecklistItem(issue_id=issue2.id, text="Stabilization PR", completed=False, level=0, position=2),
    ]
    for item in checklist2:
        db_session.add(item)

    analysis2 = IssueAnalysis(
        issue_id=issue2.id,
        readiness_score=35,
        blocking_dependencies=["Alignment computation for extern types", "Symbol collision in v0 mangling"],
        unresolved_questions=[
            {"category": "Implementation", "question": "What is the principled fix for alignment computation?"},
        ],
        progress_summary="RFC implemented but fundamental alignment issues block stabilization.",
        checklist_completed=1,
        checklist_total=3,
    )
    db_session.add(analysis2)

    issues.append(issue2)

    await db_session.commit()
    return issues


@pytest.mark.asyncio
async def test_list_issues(client: AsyncClient, sample_issues):
    """Test listing issues with pagination."""
    response = await client.get("/api/v1/issues", params={"page": 1, "per_page": 10})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    assert len(data["issues"]) >= 2
    assert data["page"] == 1
    assert data["per_page"] == 10


@pytest.mark.asyncio
async def test_list_issues_with_search(client: AsyncClient, sample_issues):
    """Test searching issues."""
    response = await client.get("/api/v1/issues", params={"search": "specialization"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    for issue in data["issues"]:
        assert "specialization" in issue["title"].lower()


@pytest.mark.asyncio
async def test_list_issues_with_state_filter(client: AsyncClient, sample_issues):
    """Test filtering by state."""
    response = await client.get("/api/v1/issues", params={"state": "open"})
    assert response.status_code == 200
    data = response.json()
    for issue in data["issues"]:
        assert issue["state"] == "open"


@pytest.mark.asyncio
async def test_list_issues_with_sort(client: AsyncClient, sample_issues):
    """Test sorting issues."""
    response = await client.get("/api/v1/issues", params={"sort": "comments", "order": "desc"})
    assert response.status_code == 200
    data = response.json()
    comments = [issue["comments"] for issue in data["issues"]]
    assert comments == sorted(comments, reverse=True)


@pytest.mark.asyncio
async def test_get_issue_detail(client: AsyncClient, sample_issues):
    """Test getting a single issue with full details."""
    response = await client.get("/api/v1/issues/31844")
    assert response.status_code == 200
    data = response.json()
    assert data["number"] == 31844
    assert data["title"] == "Tracking issue for specialization (RFC 1210)"
    assert len(data["checklist"]) == 4
    assert data["analysis"] is not None
    assert data["analysis"]["readiness_score"] == 45
    assert len(data["analysis"]["blocking_dependencies"]) == 2
    assert len(data["analysis"]["unresolved_questions"]) == 2


@pytest.mark.asyncio
async def test_get_issue_not_found(client: AsyncClient):
    """Test getting non-existent issue returns 404."""
    response = await client.get("/api/v1/issues/999999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_compare_issues(client: AsyncClient, sample_issues):
    """Test comparing multiple issues."""
    response = await client.post(
        "/api/v1/issues/compare",
        json={"numbers": [31844, 43467]},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    numbers = [issue["number"] for issue in data]
    assert 31844 in numbers
    assert 43467 in numbers
    for issue in data:
        assert "readiness_score" in issue
        assert "checklist_progress" in issue


@pytest.mark.asyncio
async def test_compare_too_many_issues(client: AsyncClient):
    """Test comparing more than 6 issues fails."""
    response = await client.post(
        "/api/v1/issues/compare",
        json={"numbers": [1, 2, 3, 4, 5, 6, 7]},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_compare_empty(client: AsyncClient):
    """Test comparing empty list returns empty array."""
    response = await client.post(
        "/api/v1/issues/compare",
        json={"numbers": []},
    )
    assert response.status_code == 200
    data = response.json()
    assert data == []