# Vector Foundry - Authentication Core
"""Role-based access control utilities for OIDC/Keycloak authentication.

Provides role constants and dependency factories that can be applied to
FastAPI routes to enforce authorization.  Roles follow the established
convention:

- ``viewer``   — read access to issues and analysis
- ``operator`` — can trigger GitHub sync and write operations
- ``admin``    — full access including user/role management
"""

from typing import List

from fastapi import Depends, HTTPException, status

from app.models.user import User

# Role constants — single source of truth for role names used across
# backend, frontend, and Keycloak realm configuration.
ROLE_VIEWER = "viewer"
ROLE_OPERATOR = "operator"
ROLE_ADMIN = "admin"

# Convenience tuples used when requiring "read" access (any authenticated
# viewer-level user).
VIEWER_ROLES: tuple[str, ...] = (ROLE_VIEWER, ROLE_OPERATOR, ROLE_ADMIN)
# Roles allowed to write / trigger mutations.
OPERATOR_ROLES: tuple[str, ...] = (ROLE_OPERATOR, ROLE_ADMIN)
# Roles allowed administrative actions.
ADMIN_ROLES: tuple[str, ...] = (ROLE_ADMIN,)


def require_role(*required_roles: str):
    """Create a FastAPI dependency that requires one of *required_roles*.

    Usage::

        from app.core.auth import require_role

        @router.get("/secure")
        async def secure(user: User = Depends(require_role("admin"))):
            ...
    """
    if not required_roles:
        required_roles = (ROLE_VIEWER,)

    async def role_checker(
        user: User = Depends(_get_user_lazy),
    ) -> User:
        if not user.has_any_role(list(required_roles)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this operation",
            )
        return user

    return role_checker


# Pre-built dependencies for common role requirements.
require_viewer = require_role(*VIEWER_ROLES)
require_operator = require_role(*OPERATOR_ROLES)
require_admin = require_role(*ADMIN_ROLES)


async def _get_user_lazy() -> User:
    """Lazy indirection so ``require_role`` avoids a circular import.

    ``get_current_user`` lives in ``app.api.auth`` which itself imports
    from ``app.core`` packages.  By deferring the import we break the
    cycle.
    """
    from app.api.auth import get_current_user

    return await get_current_user()