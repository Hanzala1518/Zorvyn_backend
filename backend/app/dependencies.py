"""
Core dependencies: Supabase clients, JWT auth, role guards.

CRITICAL SUPABASE-PY V2 NOTE:
  response = client.table("x").select("*").execute()
  data = response.data          # always a list (empty list if nothing found)
  count = response.count        # only populated when you pass count="exact"

  Do NOT use response["data"] or .single() — v2 returns an APIResponse object.

PERFORMANCE NOTE:
  Supabase clients are module-level singletons to avoid reconnection overhead.
  get_current_user reads role/email/full_name directly from JWT claims (set at
  login time) to eliminate a Supabase round-trip on every authenticated request.
  A lightweight TTL cache backs up the rare case of tokens missing those claims.
"""
import logging
import time
import threading
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from supabase import create_client, Client

from app.config import get_settings, Settings

logger = logging.getLogger(__name__)
settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# ---------------------------------------------------------------------------
# Singleton Supabase clients — created once, reused for all requests.
# ---------------------------------------------------------------------------
_supabase_client: Client | None = None
_supabase_admin_client: Client | None = None
_client_lock = threading.Lock()


def get_supabase_client() -> Client:
    global _supabase_client
    if _supabase_client is None:
        with _client_lock:
            if _supabase_client is None:
                _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _supabase_client


def get_supabase_admin_client() -> Client:
    global _supabase_admin_client
    if _supabase_admin_client is None:
        with _client_lock:
            if _supabase_admin_client is None:
                _supabase_admin_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    return _supabase_admin_client


# ---------------------------------------------------------------------------
# Simple TTL user cache — fallback for old tokens that lack claim fields.
# ---------------------------------------------------------------------------
_USER_CACHE_TTL = 120  # seconds
_user_cache: dict[str, tuple[dict, float]] = {}
_cache_lock = threading.Lock()


def _cache_get(user_id: str) -> dict | None:
    with _cache_lock:
        entry = _user_cache.get(user_id)
        if entry and entry[1] > time.monotonic():
            return entry[0]
        _user_cache.pop(user_id, None)
        return None


def _cache_set(user_id: str, user: dict) -> None:
    with _cache_lock:
        _user_cache[user_id] = (user, time.monotonic() + _USER_CACHE_TTL)


def invalidate_user_cache(user_id: str) -> None:
    """Call this after updating a user's role/status so stale data is evicted."""
    with _cache_lock:
        _user_cache.pop(user_id, None)


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------
CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expired authentication credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id: str = payload.get("sub")
        if not user_id:
            raise CREDENTIALS_EXCEPTION
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode failed: {e}")
        raise CREDENTIALS_EXCEPTION


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> dict:
    payload = decode_token(token)
    user_id = payload.get("sub")

    # Fast path: JWT already carries role/email/full_name (set at login).
    # No Supabase round-trip needed — just trust the signed token.
    role = payload.get("role")
    email = payload.get("email")
    if role and email:
        return {
            "id": user_id,
            "email": email,
            "full_name": payload.get("full_name", ""),
            "role": role,
            "status": "active",
        }

    # Slow path: old token without embedded claims — check cache then DB.
    cached = _cache_get(user_id)
    if cached:
        return cached

    try:
        client = get_supabase_admin_client()
        response = (
            client.table("users")
            .select("id, email, full_name, role, status")
            .eq("id", user_id)
            .eq("is_deleted", False)
            .execute()
        )
        if not response.data:
            raise CREDENTIALS_EXCEPTION

        user = response.data[0]
        if user["status"] != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been deactivated. Contact an administrator.",
            )
        _cache_set(user_id, user)
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {e}")
        raise CREDENTIALS_EXCEPTION


def require_admin(
    current_user: Annotated[dict, Depends(get_current_user)]
) -> dict:
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required for this action.",
        )
    return current_user


def require_analyst_or_above(
    current_user: Annotated[dict, Depends(get_current_user)]
) -> dict:
    if current_user["role"] not in ("admin", "analyst"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Analyst or Admin access required for this action.",
        )
    return current_user


def require_viewer_or_above(
    current_user: Annotated[dict, Depends(get_current_user)]
) -> dict:
    if current_user["role"] not in ("admin", "analyst", "viewer"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource.",
        )
    return current_user



