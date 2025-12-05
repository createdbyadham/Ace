"""
Test endpoints that forward user JWTs to Supabase PostgREST to verify RLS policies.

IMPORTANT: These use the ANON key, NOT service role key.
The service role key bypasses RLS entirely and defeats the purpose of testing.
"""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, EmailStr
import httpx

from core.config import settings

router = APIRouter(prefix="/test", tags=["RLS Tests"])


# ============================================================================
# AUTH ENDPOINTS - Sign up / Sign in via Supabase GoTrue
# ============================================================================

class AuthRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user_id: str
    email: str


@router.post("/signup", response_model=AuthResponse)
async def signup(payload: AuthRequest):
    """
    Sign up a new user via Supabase Auth (GoTrue).
    
    Returns the access_token (JWT) you can use for RLS testing.
    """
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise HTTPException(
            status_code=500,
            detail="SUPABASE_URL and SUPABASE_ANON_KEY must be set"
        )
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.supabase_url}/auth/v1/signup",
            json={"email": payload.email, "password": payload.password},
            headers={
                "apikey": settings.supabase_anon_key,
                "Content-Type": "application/json",
            },
        )
    
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    
    data = resp.json()
    
    # Supabase might require email confirmation depending on settings
    if "access_token" not in data:
        # User created but needs email confirmation
        return {
            "access_token": "",
            "refresh_token": "",
            "user_id": data.get("id", data.get("user", {}).get("id", "")),
            "email": payload.email,
            "message": "Check email for confirmation link, or disable email confirmation in Supabase dashboard",
        }
    
    return AuthResponse(
        access_token=data["access_token"],
        refresh_token=data.get("refresh_token", ""),
        user_id=data["user"]["id"],
        email=data["user"]["email"],
    )


@router.post("/signin", response_model=AuthResponse)
async def signin(payload: AuthRequest):
    """
    Sign in an existing user via Supabase Auth (GoTrue).
    
    Returns the access_token (JWT) you can use for RLS testing.
    """
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise HTTPException(
            status_code=500,
            detail="SUPABASE_URL and SUPABASE_ANON_KEY must be set"
        )
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.supabase_url}/auth/v1/token?grant_type=password",
            json={"email": payload.email, "password": payload.password},
            headers={
                "apikey": settings.supabase_anon_key,
                "Content-Type": "application/json",
            },
        )
    
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    
    data = resp.json()
    
    return AuthResponse(
        access_token=data["access_token"],
        refresh_token=data.get("refresh_token", ""),
        user_id=data["user"]["id"],
        email=data["user"]["email"],
    )


@router.get("/me")
async def get_current_user(authorization: str | None = Header(None)):
    """
    Verify a JWT and return the user info from Supabase Auth.
    
    Useful to confirm your token is valid and see the user_id.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise HTTPException(
            status_code=500,
            detail="SUPABASE_URL and SUPABASE_ANON_KEY must be set"
        )
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.supabase_url}/auth/v1/user",
            headers={
                "Authorization": authorization,
                "apikey": settings.supabase_anon_key,
            },
        )
    
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    
    return resp.json()

__all__ = ["router"]

