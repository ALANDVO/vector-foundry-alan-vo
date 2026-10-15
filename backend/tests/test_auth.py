# Vector Foundry - Auth Tests
"""Tests for authentication endpoints."""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


@pytest.fixture
def mock_user(db_session: AsyncSession):
    """Create a test user."""
    user = User(
        keycloak_id="test-sub-123",
        username="testuser",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        roles=["viewer"],
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client: AsyncClient):
    """Test /auth/me without authentication returns 401."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_with_invalid_token(client: AsyncClient):
    """Test /auth/me with invalid token returns 401."""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout_endpoint(client: AsyncClient):
    """Test logout endpoint returns logout URL."""
    response = await client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    data = response.json()
    assert "logout_url" in data or "message" in data


@pytest.mark.asyncio
async def test_provider_info_endpoint(client: AsyncClient):
    """Test LLM provider info endpoint."""
    response = await client.get("/api/v1/llm/provider")
    assert response.status_code == 200
    data = response.json()
    assert "provider" in data
    assert "configured" in data