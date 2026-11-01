import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from . import db

router = APIRouter(prefix="/api/auth")


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=128)


def _require_supabase():
    if not db.SUPABASE_ENABLED:
        raise HTTPException(404, "Account sign-in is not enabled.")


async def _auth_request(path, body):
    _require_supabase()
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"{db.SUPABASE_URL}/auth/v1/{path}",
                headers={"apikey": db.SUPABASE_ANON_KEY},
                json=body,
            )
    except httpx.HTTPError as exc:
        raise HTTPException(503, "Could not reach Supabase Auth. Try again shortly.") from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise HTTPException(502, "Supabase Auth returned an invalid response.") from exc
    if response.is_error:
        detail = data.get("msg") or data.get("message") or data.get("error_description")
        if not detail:
            detail = "Account request failed."
        raise HTTPException(response.status_code, str(detail)[:300])
    return data


@router.post("/signup")
async def signup(body: Credentials):
    return await _auth_request("signup", body.model_dump())


@router.post("/login")
async def login(body: Credentials):
    return await _auth_request("token?grant_type=password", body.model_dump())


@router.post("/refresh")
async def refresh(body: dict):
    refresh_token = body.get("refresh_token")
    if not isinstance(refresh_token, str) or not refresh_token.strip():
        raise HTTPException(400, "A refresh token is required.")
    return await _auth_request(
        "token?grant_type=refresh_token", {"refresh_token": refresh_token}
    )


@router.get("/config")
def config():
    return {
        "auth_enabled": db.SUPABASE_ENABLED,
        "supabase_url": db.SUPABASE_URL if db.SUPABASE_ENABLED else None,
        "supabase_anon_key": db.SUPABASE_ANON_KEY if db.SUPABASE_ENABLED else None,
    }


def verify_access_token(access_token):
    _require_supabase()
    try:
        response = httpx.get(
            f"{db.SUPABASE_URL}/auth/v1/user",
            headers={
                "apikey": db.SUPABASE_ANON_KEY,
                "Authorization": f"Bearer {access_token}",
            },
            timeout=10,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(503, "Could not verify the account with Supabase.") from exc
    if response.status_code == 401:
        raise HTTPException(401, "Your session has expired. Please sign in again.")
    if response.is_error:
        raise HTTPException(503, "Supabase could not verify the account.")
    try:
        user = response.json()
    except ValueError as exc:
        raise HTTPException(502, "Supabase returned an invalid account response.") from exc
    if not isinstance(user, dict) or not user.get("id"):
        raise HTTPException(401, "Supabase returned no account for this session.")
    return user["id"]
