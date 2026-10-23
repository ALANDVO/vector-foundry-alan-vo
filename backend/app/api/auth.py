# Vector Foundry - Auth API
"""API endpoints for authentication (OIDC/Keycloak)."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt, jwk
from jose.exceptions import JWTError, JWSError
from jose.utils import base64url_decode
import httpx

from app.core.config import get_settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import TokenData, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])

settings = get_settings()

# JWKS cache
_jwks_cache: dict = {}


async def get_jwks() -> dict:
    """Fetch and cache JWKS from OIDC discovery."""
    global _jwks_cache
    if "keys" in _jwks_cache:
        return _jwks_cache

    discovery_url = settings.effective_oidc_discovery_url
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Get discovery document
        discovery_resp = await client.get(discovery_url)
        discovery_resp.raise_for_status()
        discovery = discovery_resp.json()

        # Get JWKS
        jwks_resp = await client.get(discovery["jwks_uri"])
        jwks_resp.raise_for_status()
        _jwks_cache = jwks_resp.json()

    return _jwks_cache


async def verify_token(token: str) -> dict:
    """Verify JWT token using JWKS."""
    # Quick format check: JWT must have 3 parts
    if not token or token.count(".") != 2:
        raise HTTPException(status_code=401, detail="Invalid token format")

    try:
        # Get header first to extract kid (doesn't need JWKS)
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        # Now fetch JWKS
        jwks = await get_jwks()

        key = None
        for jwk_key in jwks.get("keys", []):
            if jwk_key.get("kid") == kid:
                key = jwk.construct(jwk_key)
                break

        if not key:
            raise HTTPException(status_code=401, detail="Invalid token: key not found")

        # Verify signature
        message, encoded_sig = token.rsplit(".", 1)
        decoded_sig = base64url_decode(encoded_sig.encode())
        if not key.verify(message.encode(), decoded_sig):
            raise HTTPException(status_code=401, detail="Invalid token: signature verification failed")

        # Decode and verify claims
        payload = jwt.get_unverified_claims(token)

        # Verify issuer
        expected_issuer = settings.effective_oidc_issuer
        if payload.get("iss") != expected_issuer:
            raise HTTPException(status_code=401, detail=f"Invalid issuer: expected {expected_issuer}")

        # Verify audience
        if settings.oidc_audience not in payload.get("aud", []):
            raise HTTPException(status_code=401, detail="Invalid audience")

        return payload
    except (JWTError, JWSError, ValueError, KeyError) as e:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current authenticated user from Bearer token."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header.split(" ")[1]
    payload = await verify_token(token)

    # Get or create user
    keycloak_id = payload.get("sub")
    result = await db.execute(select(User).where(User.keycloak_id == keycloak_id))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            keycloak_id=keycloak_id,
            username=payload.get("preferred_username", keycloak_id),
            email=payload.get("email", ""),
            first_name=payload.get("given_name"),
            last_name=payload.get("family_name"),
            roles=payload.get("realm_access", {}).get("roles", []),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        # Update roles from token
        user.roles = payload.get("realm_access", {}).get("roles", [])
        user.last_login = func.now()
        await db.commit()

    return user


async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Get current user if authenticated, otherwise None."""
    try:
        return await get_current_user(request, db)
    except HTTPException:
        return None


@router.get("/login")
async def login(redirect: str = "/"):
    """Initiate OIDC login flow (redirects to Keycloak)."""
    discovery_url = settings.effective_oidc_discovery_url
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(discovery_url)
        resp.raise_for_status()
        discovery = resp.json()

    auth_endpoint = discovery["authorization_endpoint"]
    params = {
        "client_id": settings.keycloak_client_id,
        "response_type": "code",
        "scope": "openid profile email",
        "redirect_uri": f"{settings.keycloak_server_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/token",
        "state": redirect,
        "prompt": "login",
    }

    auth_url = f"{auth_endpoint}?{httpx.QueryParams(params)}"
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def callback(code: str, state: str = "/"):
    """Handle OIDC callback (exchanges code for tokens)."""
    discovery_url = settings.effective_oidc_discovery_url
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(discovery_url)
        resp.raise_for_status()
        discovery = resp.json()

    token_endpoint = discovery["token_endpoint"]
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": f"{settings.keycloak_server_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/token",
        "client_id": settings.keycloak_client_id,
        "client_secret": settings.keycloak_client_secret,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        token_resp = await client.post(token_endpoint, data=data)
        token_resp.raise_for_status()
        tokens = token_resp.json()

    # Redirect to frontend with tokens in fragment (for SPA)
    frontend_url = "http://localhost:5173"
    fragment = httpx.QueryParams({
        "access_token": tokens["access_token"],
        "refresh_token": tokens.get("refresh_token", ""),
        "id_token": tokens.get("id_token", ""),
        "expires_in": str(tokens.get("expires_in", 300)),
    })
    return RedirectResponse(url=f"{frontend_url}/callback#{fragment}")


@router.post("/logout")
async def logout():
    """Logout endpoint (client should clear tokens)."""
    try:
        discovery_url = settings.effective_oidc_discovery_url
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(discovery_url)
            resp.raise_for_status()
            discovery = resp.json()

        end_session_endpoint = discovery.get("end_session_endpoint")
        if end_session_endpoint:
            logout_url = f"{end_session_endpoint}?client_id={settings.keycloak_client_id}"
            return {"logout_url": logout_url}
    except Exception:
        # Handle Keycloak unavailable gracefully
        pass

    return {"message": "Logged out locally"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(user: User = Depends(get_current_user)):
    """Get current user info."""
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        name=user.full_name,
        roles=user.roles,
    )