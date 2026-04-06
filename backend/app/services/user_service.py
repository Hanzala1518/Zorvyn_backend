import logging
import uuid
from typing import Optional
from datetime import datetime, timezone
from fastapi import HTTPException, status
from app.schemas.user import UserCreate, UserUpdate
from app.services.auth_service import hash_password, verify_password

logger = logging.getLogger(__name__)
_USER_COLS = "id, email, full_name, role, status, created_at, updated_at"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_user(data: UserCreate, admin_client) -> dict:
    existing = (
        admin_client.table("users")
        .select("id")
        .eq("email", data.email.lower().strip())
        .eq("is_deleted", False)
        .execute()
    )
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )
    record = {
        "id": str(uuid.uuid4()),
        "email": data.email.lower().strip(),
        "full_name": data.full_name.strip(),
        "password_hash": hash_password(data.password),
        "role": data.role.value,
        "status": "active",
        "is_deleted": False,
        "created_at": _utcnow(),
        "updated_at": _utcnow(),
    }
    response = admin_client.table("users").insert(record).execute()
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create user.")
    user = response.data[0]
    return {k: v for k, v in user.items() if k != "password_hash"}


def get_user_by_id(user_id: str, client) -> Optional[dict]:
    response = (
        client.table("users")
        .select(_USER_COLS)
        .eq("id", user_id)
        .eq("is_deleted", False)
        .execute()
    )
    return response.data[0] if response.data else None


def get_all_users(page: int, page_size: int, client) -> dict:
    offset = (page - 1) * page_size
    response = (
        client.table("users")
        .select(_USER_COLS, count="exact")
        .eq("is_deleted", False)
        .order("created_at", desc=True)
        .range(offset, offset + page_size - 1)
        .execute()
    )
    return {
        "users": response.data or [],
        "total": response.count or 0,
        "page": page,
        "page_size": page_size,
    }


def update_user(user_id: str, data: UserUpdate, admin_client) -> dict:
    update_dict = data.model_dump(exclude_none=True)
    if "role" in update_dict:
        update_dict["role"] = update_dict["role"].value
    if "status" in update_dict:
        update_dict["status"] = update_dict["status"].value
    if not update_dict:
        raise HTTPException(status_code=400, detail="No fields provided to update.")
    update_dict["updated_at"] = _utcnow()
    response = (
        admin_client.table("users")
        .update(update_dict)
        .eq("id", user_id)
        .eq("is_deleted", False)
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="User not found.")
    user = response.data[0]
    return {k: v for k, v in user.items() if k != "password_hash"}


def soft_delete_user(user_id: str, admin_client) -> bool:
    response = (
        admin_client.table("users")
        .update({"is_deleted": True, "status": "inactive", "updated_at": _utcnow()})
        .eq("id", user_id)
        .eq("is_deleted", False)
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="User not found.")
    return True


def change_password(user_id: str, current_password: str, new_password: str, admin_client) -> bool:
    response = (
        admin_client.table("users")
        .select("password_hash")
        .eq("id", user_id)
        .eq("is_deleted", False)
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="User not found.")
    if not verify_password(current_password, response.data[0]["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    admin_client.table("users").update({
        "password_hash": hash_password(new_password),
        "updated_at": _utcnow(),
    }).eq("id", user_id).execute()
    return True
