"""
JWT authentication dependency for Supabase Auth.
Validates the JWT and extracts user info.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

import httpx
from fastapi import Header, HTTPException, status

from core.config import settings


@dataclass
class CurrentUser:
    """Authenticated user extracted from JWT."""
    id: UUID
    email: str


async def get_current_user(authorization: str | None = Header(None)) -> CurrentUser:
    """
    Dependency that validates the JWT via Supabase Auth and returns the current user.
    
    Usage:
        @router.post("/endpoint")
        async def my_endpoint(user: CurrentUser = Depends(get_current_user)):
            print(user.id, user.email)
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must start with 'Bearer '",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SUPABASE_URL and SUPABASE_ANON_KEY must be configured",
        )
    
    # Validate JWT by calling Supabase Auth
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.supabase_url}/auth/v1/user",
            headers={
                "Authorization": authorization,
                "apikey": settings.supabase_anon_key,
            },
        )
    
    if resp.status_code == 401:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Auth service error: {resp.text}",
        )
    
    data = resp.json()
    
    return CurrentUser(
        id=UUID(data["id"]),
        email=data.get("email", ""),
    )


__all__ = ["CurrentUser", "get_current_user"]

