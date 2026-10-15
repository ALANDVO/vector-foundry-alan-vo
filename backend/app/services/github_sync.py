# Vector Foundry - GitHub Sync Service
"""Service for fetching tracking issues from GitHub API."""

import httpx
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import db_manager
from app.models.issue import TrackingIssue, ChecklistItem, SyncLog
from app.services.analysis import parse_checklist, update_issue_analysis


settings = get_settings()


class GitHubSyncService:
    """Service for syncing tracking issues from rust-lang/rust."""

    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if settings.github_token:
            headers["Authorization"] = f"Bearer {settings.github_token}"
        self.client = httpx.AsyncClient(
            base_url=settings.github_api_url,
            headers=headers,
            timeout=30.0,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def fetch_tracking_issues(self, max_pages: int = 5) -> List[dict]:
        """Fetch tracking issues from GitHub."""
        issues = []
        page = 1

        while page <= max_pages:
            params = {
                "state": "all",
                "labels": "tracking-issue",
                "per_page": 100,
                "page": page,
                "sort": "updated",
                "direction": "desc",
            }

            resp = await self.client.get(
                f"/repos/{settings.github_repo_owner}/{settings.github_repo_name}/issues",
                params=params,
            )
            resp.raise_for_status()
            page_issues = resp.json()

            if not page_issues:
                break

            issues.extend(page_issues)
            page += 1

        return issues

    async def fetch_issue_details(self, number: int) -> dict:
        """Fetch full details for a single issue."""
        resp = await self.client.get(
            f"/repos/{settings.github_repo_owner}/{settings.github_repo_name}/issues/{number}",
        )
        resp.raise_for_status()
        return resp.json()

    async def sync_all(self, db: AsyncSession, max_pages: int = 5) -> SyncLog:
        """Perform full sync of tracking issues."""
        sync_log = SyncLog(
            started_at=datetime.now(timezone.utc),
            status="running",
        )
        db.add(sync_log)
        await db.commit()
        await db.refresh(sync_log)

        try:
            issues_data = await self.fetch_tracking_issues(max_pages)
            sync_log.issues_fetched = len(issues_data)

            created = 0
            updated = 0

            for issue_data in issues_data:
                # Skip PRs
                if "pull_request" in issue_data:
                    continue

                result = await db.execute(
                    select(TrackingIssue).where(TrackingIssue.number == issue_data["number"])
                )
                existing = result.scalar_one_or_none()

                if existing:
                    # Update existing
                    existing.title = issue_data["title"]
                    existing.body = issue_data["body"] or ""
                    existing.html_url = issue_data["html_url"]
                    existing.state = issue_data["state"]
                    existing.comments = issue_data["comments"]
                    existing.labels = [
                        {"name": l["name"], "color": l["color"]}
                        for l in issue_data.get("labels", [])
                    ]
                    existing.author_login = issue_data["user"]["login"]
                    existing.author_avatar_url = issue_data["user"]["avatar_url"]
                    existing.updated_at = datetime.fromisoformat(
                        issue_data["updated_at"].replace("Z", "+00:00")
                    )
                    existing.fetched_at = datetime.now(timezone.utc)
                    updated += 1
                    issue = existing
                else:
                    # Create new
                    issue = TrackingIssue(
                        number=issue_data["number"],
                        title=issue_data["title"],
                        body=issue_data["body"] or "",
                        html_url=issue_data["html_url"],
                        state=issue_data["state"],
                        comments=issue_data["comments"],
                        labels=[
                            {"name": l["name"], "color": l["color"]}
                            for l in issue_data.get("labels", [])
                        ],
                        author_login=issue_data["user"]["login"],
                        author_avatar_url=issue_data["user"]["avatar_url"],
                        created_at=datetime.fromisoformat(
                            issue_data["created_at"].replace("Z", "+00:00")
                        ),
                        updated_at=datetime.fromisoformat(
                            issue_data["updated_at"].replace("Z", "+00:00")
                        ),
                        fetched_at=datetime.now(timezone.utc),
                    )
                    db.add(issue)
                    await db.flush()
                    created += 1

                # Parse and store checklist items
                await self._sync_checklist(db, issue, issue_data["body"] or "")

                # Update analysis
                await update_issue_analysis(db, issue)

            sync_log.issues_created = created
            sync_log.issues_updated = updated
            sync_log.status = "completed"
            sync_log.completed_at = datetime.now(timezone.utc)

            await db.commit()
            return sync_log

        except Exception as e:
            sync_log.status = "failed"
            sync_log.error_message = str(e)
            sync_log.completed_at = datetime.now(timezone.utc)
            await db.commit()
            raise

    async def _sync_checklist(self, db: AsyncSession, issue: TrackingIssue, body: str):
        """Sync checklist items for an issue."""
        # Delete existing checklist items
        from sqlalchemy import delete
        await db.execute(delete(ChecklistItem).where(ChecklistItem.issue_id == issue.id))

        # Parse new checklist
        checklist_data = parse_checklist(body)

        for i, (text, completed, level) in enumerate(checklist_data):
            item = ChecklistItem(
                issue_id=issue.id,
                text=text,
                completed=completed,
                level=level,
                position=i,
            )
            db.add(item)