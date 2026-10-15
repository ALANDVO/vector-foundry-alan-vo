# Vector Foundry - Auth Schemas
"""Pydantic schemas for authentication."""

from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class TokenData(BaseModel):
    """Decoded token data."""
    sub: str
    preferred_username: str
    email: str
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    realm_access: dict = {}


class UserResponse(BaseModel):
    """User info response."""
    id: int
    username: str
    email: str
    name: str
    roles: List[str]

    model_config = ConfigDict(from_attributes=True)