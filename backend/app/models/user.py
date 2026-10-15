# Vector Foundry - User Models
"""SQLAlchemy models for users and authentication."""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    JSON,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    """Model for application users (synced from Keycloak)."""

    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_keycloak_id", "keycloak_id", unique=True),
        Index("ix_users_username", "username", unique=True),
        Index("ix_users_email", "email", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    keycloak_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    roles: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    @property
    def full_name(self) -> str:
        parts = [self.first_name, self.last_name]
        return " ".join(filter(None, parts)) or self.username

    def has_role(self, role: str) -> bool:
        return role in self.roles

    def has_any_role(self, roles: List[str]) -> bool:
        return any(r in self.roles for r in roles)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', roles={self.roles})>"


class AuditLog(Base):
    """Model for audit logging of important actions."""

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_user_id", "user_id"),
        Index("ix_audit_logs_action", "action"),
        Index("ix_audit_logs_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action='{self.action}', user_id={self.user_id})>"