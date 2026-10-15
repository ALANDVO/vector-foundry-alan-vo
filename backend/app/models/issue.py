# Vector Foundry - Issue Models
"""SQLAlchemy models for tracking issues and analysis."""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TrackingIssue(Base):
    """Model for a GitHub tracking issue from rust-lang/rust."""

    __tablename__ = "tracking_issues"
    __table_args__ = (
        Index("ix_tracking_issues_state", "state"),
        Index("ix_tracking_issues_updated_at", "updated_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    html_url: Mapped[str] = mapped_column(String(500), nullable=False)
    state: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    comments: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    labels: Mapped[List[dict]] = mapped_column(JSON, nullable=False, default=list)
    author_login: Mapped[str] = mapped_column(String(100), nullable=False)
    author_avatar_url: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    checklist_items: Mapped[List["ChecklistItem"]] = relationship(
        "ChecklistItem", back_populates="issue", cascade="all, delete-orphan"
    )
    analysis: Mapped[Optional["IssueAnalysis"]] = relationship(
        "IssueAnalysis", back_populates="issue", cascade="all, delete-orphan", uselist=False
    )

    def __repr__(self) -> str:
        return f"<TrackingIssue(number={self.number}, title='{self.title[:50]}...')>"


class ChecklistItem(Base):
    """Model for a checklist item within a tracking issue."""

    __tablename__ = "checklist_items"
    __table_args__ = (
        Index("ix_checklist_items_issue_id", "issue_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    issue_id: Mapped[int] = mapped_column(Integer, ForeignKey("tracking_issues.id", ondelete="CASCADE"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    completed: Mapped[bool] = mapped_column(nullable=False, default=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    issue: Mapped["TrackingIssue"] = relationship("TrackingIssue", back_populates="checklist_items")

    def __repr__(self) -> str:
        return f"<ChecklistItem(issue_id={self.issue_id}, completed={self.completed}, text='{self.text[:30]}...')>"


class IssueAnalysis(Base):
    """Model for computed analysis of a tracking issue."""

    __tablename__ = "issue_analyses"
    __table_args__ = (
        Index("ix_issue_analyses_issue_id", "issue_id", unique=True),
        Index("ix_issue_analyses_readiness_score", "readiness_score"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    issue_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tracking_issues.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    readiness_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    blocking_dependencies: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    unresolved_questions: Mapped[List[dict]] = mapped_column(JSON, nullable=False, default=list)
    progress_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    checklist_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    checklist_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_analyzed: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    analysis_version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0")

    issue: Mapped["TrackingIssue"] = relationship("TrackingIssue", back_populates="analysis")

    def __repr__(self) -> str:
        return f"<IssueAnalysis(issue_id={self.issue_id}, score={self.readiness_score})>"


class SyncLog(Base):
    """Model for tracking GitHub sync operations."""

    __tablename__ = "sync_logs"
    __table_args__ = (
        Index("ix_sync_logs_started_at", "started_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")  # running, completed, failed
    issues_fetched: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    issues_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    issues_updated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<SyncLog(id={self.id}, status={self.status}, fetched={self.issues_fetched})>"