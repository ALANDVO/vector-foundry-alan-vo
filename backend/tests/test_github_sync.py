# Vector Foundry - GitHub Sync Tests
"""Tests for GitHub sync service (with mocked API)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.issue import TrackingIssue, ChecklistItem, IssueAnalysis, SyncLog
from app.services.github_sync import GitHubSyncService


@pytest.fixture
def mock_github_response():
    """Mock GitHub API response for tracking issues."""
    return [
        {
            "number": 31844,
            "title": "Tracking issue for specialization (RFC 1210)",
            "body": "## Implementation Steps\n- [x] Land PR #30652\n- [ ] Fix soundness hole",
            "html_url": "https://github.com/rust-lang/rust/issues/31844",
            "state": "open",
            "comments": 323,
            "labels": [
                {"name": "F-specialization", "color": "ff0000"},
                {"name": "tracking-issue", "color": "00ff00"},
            ],
            "user": {"login": "rust-lang", "avatar_url": "https://github.com/rust-lang.png"},
            "created_at": "2019-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        },
        {
            "number": 43467,
            "title": "Tracking issue for RFC 1861: Extern types",
            "body": "## Steps\n- [x] Implement RFC\n- [ ] Documentation",
            "html_url": "https://github.com/rust-lang/rust/issues/43467",
            "state": "open",
            "comments": 292,
            "labels": [
                {"name": "F-extern-types", "color": "ff0000"},
                {"name": "tracking-issue", "color": "00ff00"},
            ],
            "user": {"login": "rust-lang", "avatar_url": "https://github.com/rust-lang.png"},
            "created_at": "2020-01-01T00:00:00Z",
            "updated_at": "2024-06-01T00:00:00Z",
        },
    ]


@pytest.mark.asyncio
async def test_fetch_tracking_issues(db_session: AsyncSession, mock_github_response):
    """Test fetching tracking issues from GitHub."""
    service = GitHubSyncService()

    # Mock the HTTP client
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.json.return_value = mock_github_response
    mock_response.raise_for_status = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    service.client = mock_client

    issues = await service.fetch_tracking_issues(max_pages=1)

    assert len(issues) == 2
    assert issues[0]["number"] == 31844
    assert issues[1]["number"] == 43467


@pytest.mark.asyncio
async def test_sync_all_creates_issues(db_session: AsyncSession, mock_github_response):
    """Test full sync creates new issues."""
    service = GitHubSyncService()

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.json.return_value = mock_github_response
    mock_response.raise_for_status = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    service.client = mock_client

    sync_log = await service.sync_all(db_session, max_pages=1)

    assert sync_log.status == "completed"
    assert sync_log.issues_fetched == 2
    assert sync_log.issues_created == 2
    assert sync_log.issues_updated == 0

    # Verify issues were created
    from sqlalchemy import select
    result = await db_session.execute(select(TrackingIssue))
    issues = result.scalars().all()
    assert len(issues) == 2


@pytest.mark.asyncio
async def test_sync_all_updates_existing(db_session: AsyncSession, mock_github_response):
    """Test sync updates existing issues."""
    service = GitHubSyncService()

    # Pre-create an issue
    existing = TrackingIssue(
        number=31844,
        title="Old title",
        body="Old body",
        html_url="https://github.com/rust-lang/rust/issues/31844",
        state="closed",
        comments=100,
        labels=[],
        author_login="old",
        author_avatar_url="https://example.com/old.png",
        created_at=datetime(2019, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
    )
    db_session.add(existing)
    await db_session.commit()

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.json.return_value = mock_github_response
    mock_response.raise_for_status = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    service.client = mock_client

    sync_log = await service.sync_all(db_session, max_pages=1)

    assert sync_log.issues_created == 1  # Only the second issue is new
    assert sync_log.issues_updated == 1  # First issue updated

    # Verify the existing issue was updated
    from sqlalchemy import select
    result = await db_session.execute(
        select(TrackingIssue).where(TrackingIssue.number == 31844)
    )
    issue = result.scalar_one()
    assert issue.title == "Tracking issue for specialization (RFC 1210)"
    assert issue.state == "open"
    assert issue.comments == 323


@pytest.mark.asyncio
async def test_sync_skips_prs(db_session: AsyncSession):
    """Test sync skips pull requests."""
    service = GitHubSyncService()

    pr_response = [{
        "number": 12345,
        "title": "PR title",
        "body": "PR body",
        "html_url": "https://github.com/rust-lang/rust/pull/12345",
        "state": "open",
        "comments": 10,
        "labels": [{"name": "tracking-issue", "color": "00ff00"}],
        "user": {"login": "user", "avatar_url": "https://github.com/user.png"},
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "pull_request": {"url": "https://api.github.com/repos/rust-lang/rust/pulls/12345"},
    }]

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.json.return_value = pr_response
    mock_response.raise_for_status = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    service.client = mock_client

    sync_log = await service.sync_all(db_session, max_pages=1)

    assert sync_log.issues_created == 0
    assert sync_log.issues_fetched == 1


@pytest.mark.asyncio
async def test_sync_checklist_items(db_session: AsyncSession, mock_github_response):
    """Test checklist items are synced correctly."""
    service = GitHubSyncService()

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.json.return_value = mock_github_response
    mock_response.raise_for_status = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    service.client = mock_client

    await service.sync_all(db_session, max_pages=1)

    # Verify checklist items
    from sqlalchemy import select
    result = await db_session.execute(select(ChecklistItem))
    items = result.scalars().all()
    assert len(items) > 0

    # Check first issue has checklist items
    issue1_items = [item for item in items if item.issue_id == 1]
    assert len(issue1_items) >= 2
    completed = [item for item in issue1_items if item.completed]
    assert len(completed) >= 1


@pytest.mark.asyncio
async def test_sync_creates_analysis(db_session: AsyncSession, mock_github_response):
    """Test sync creates analysis for issues."""
    service = GitHubSyncService()

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.json.return_value = mock_github_response
    mock_response.raise_for_status = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    service.client = mock_client

    await service.sync_all(db_session, max_pages=1)

    # Verify analysis records
    from sqlalchemy import select
    result = await db_session.execute(select(IssueAnalysis))
    analyses = result.scalars().all()
    assert len(analyses) == 2

    for analysis in analyses:
        assert 0 <= analysis.readiness_score <= 100
        assert analysis.checklist_total > 0
        assert analysis.checklist_completed <= analysis.checklist_total
        assert isinstance(analysis.blocking_dependencies, list)
        assert isinstance(analysis.unresolved_questions, list)
        assert len(analysis.progress_summary) > 0


@pytest.mark.asyncio
async def test_sync_log_created(db_session: AsyncSession, mock_github_response):
    """Test sync log is created with correct data."""
    service = GitHubSyncService()

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.json.return_value = mock_github_response
    mock_response.raise_for_status = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    service.client = mock_client

    sync_log = await service.sync_all(db_session, max_pages=1)

    assert sync_log.id is not None
    assert sync_log.started_at is not None
    assert sync_log.completed_at is not None
    assert sync_log.status == "completed"
    assert sync_log.issues_fetched == 2