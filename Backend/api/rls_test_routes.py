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


# ============================================================================
# RLS TEST ENDPOINTS - Forward JWT to PostgREST
# ============================================================================


def _get_supabase_headers(authorization: str | None) -> dict[str, str]:
    """Build headers for Supabase PostgREST: user JWT + anon key."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header with user JWT")
    
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise HTTPException(
            status_code=500, 
            detail="SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment"
        )
    
    return {
        "Authorization": authorization,  # Bearer <user_jwt> from client
        "apikey": settings.supabase_anon_key,
        "Content-Type": "application/json",
        "Prefer": "return=representation, resolution=merge-duplicates",
    }


@router.post("/upsert_profile")
async def upsert_profile(request: Request, authorization: str | None = Header(None)):
    """
    Upsert a profile row into public.users using the user's JWT.
    
    Body: {"user_id": "<uuid>", "username": "...", "display_name": "...", "avatar_url": "..."}
    
    Required: user_id, username
    Optional: display_name, avatar_url
    
    RLS policy should enforce that user_id = auth.uid().
    """
    body = await request.json()
    
    if "user_id" not in body:
        raise HTTPException(status_code=400, detail="body must include user_id")
    if "username" not in body:
        raise HTTPException(status_code=400, detail="body must include username")

    headers = _get_supabase_headers(authorization)
    
    async with httpx.AsyncClient() as client:
        url = f"{settings.supabase_url}/rest/v1/users?on_conflict=user_id"
        resp = await client.post(url, json=body, headers=headers)
    
    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    
    return resp.json()


@router.post("/insert_card")
async def insert_card(request: Request, authorization: str | None = Header(None)):
    """
    Insert a card as the user.
    
    Body: {"owner_id": "<uuid>", "content": {"front": "...", "back": "..."}, "deck_id": null}
    
    RLS policy should enforce that owner_id = auth.uid().
    """
    body = await request.json()
    
    if "owner_id" not in body or "content" not in body:
        raise HTTPException(status_code=400, detail="body must include owner_id and content")
    
    headers = _get_supabase_headers(authorization)
    
    async with httpx.AsyncClient() as client:
        url = f"{settings.supabase_url}/rest/v1/cards"
        resp = await client.post(url, json=body, headers=headers)
    
    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    
    return resp.json()


@router.get("/cards_by_owner/{owner_id}")
async def cards_by_owner(owner_id: str, authorization: str | None = Header(None)):
    """
    Select cards by owner_id.
    
    If RLS is working correctly:
    - Querying your own user_id → returns your cards
    - Querying someone else's user_id → returns [] (empty array)
    """
    headers = _get_supabase_headers(authorization)
    
    async with httpx.AsyncClient() as client:
        url = f"{settings.supabase_url}/rest/v1/cards?owner_id=eq.{owner_id}"
        resp = await client.get(url, headers=headers)
    
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    
    return resp.json()


@router.get("/my_profile")
async def get_my_profile(authorization: str | None = Header(None)):
    """
    Get the current user's profile based on their JWT.
    
    Uses PostgREST's ability to filter by auth.uid() in RLS.
    """
    headers = _get_supabase_headers(authorization)
    
    async with httpx.AsyncClient() as client:
        # This will only return rows where user_id = auth.uid() due to RLS
        url = f"{settings.supabase_url}/rest/v1/users?select=*"
        resp = await client.get(url, headers=headers)
    
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    
    rows = resp.json()
    if not rows:
        return None
    return rows[0]


@router.post("/insert_deck")
async def insert_deck(request: Request, authorization: str | None = Header(None)):
    """
    Insert a deck as the user.
    
    Body: {"owner_id": "<uuid>", "name": "..."}
    
    RLS policy should enforce that owner_id = auth.uid().
    """
    body = await request.json()
    
    if "owner_id" not in body or "name" not in body:
        raise HTTPException(status_code=400, detail="body must include owner_id and name")
    
    headers = _get_supabase_headers(authorization)
    
    async with httpx.AsyncClient() as client:
        url = f"{settings.supabase_url}/rest/v1/decks"
        resp = await client.post(url, json=body, headers=headers)
    
    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    
    return resp.json()


@router.get("/decks_by_owner/{owner_id}")
async def decks_by_owner(owner_id: str, authorization: str | None = Header(None)):
    """
    Select decks by owner_id.
    
    If RLS is working correctly:
    - Querying your own user_id → returns your decks
    - Querying someone else's user_id → returns []
    """
    headers = _get_supabase_headers(authorization)
    
    async with httpx.AsyncClient() as client:
        url = f"{settings.supabase_url}/rest/v1/decks?owner_id=eq.{owner_id}"
        resp = await client.get(url, headers=headers)
    
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    
    return resp.json()


__all__ = ["router"]

