import uuid
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies import (
    require_admin,
    get_supabase_admin_client,
)
from app.services import user_service
from app.schemas.user import UserCreate, UserUpdate

logger = logging.getLogger(__name__)
router = APIRouter()


def _log_audit(action, performed_by, target_id, details, admin_client):
    try:
        admin_client.table("audit_logs").insert({
            "id": str(uuid.uuid4()),
            "action": action,
            "performed_by": performed_by,
            "target_id": str(target_id),
            "details": details,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
    except Exception as e:
        logger.error(f"Audit log error: {e}")


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    current_user: dict = Depends(require_admin),
):
    admin_client = get_supabase_admin_client()
    user = user_service.create_user(body, admin_client)
    _log_audit("user_created", current_user["id"], user["id"], {"email": user["email"], "role": user["role"]}, admin_client)
    return user


@router.get("/")
async def list_users(
    page: int = 1,
    page_size: int = 10,
    current_user: dict = Depends(require_admin),
):
    if page < 1:
        page = 1
    if page_size > 100:
        page_size = 100
    client = get_supabase_admin_client()
    return user_service.get_all_users(page, page_size, client)


@router.get("/{user_id}")
async def get_user(user_id: str, current_user: dict = Depends(require_admin)):
    client = get_supabase_admin_client()
    user = user_service.get_user_by_id(user_id, client)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


@router.patch("/{user_id}")
async def update_user(
    user_id: str,
    body: UserUpdate,
    current_user: dict = Depends(require_admin),
):
    if current_user["id"] == user_id and body.role and body.role.value != current_user["role"]:
        raise HTTPException(status_code=400, detail="You cannot change your own role.")

    admin_client = get_supabase_admin_client()
    user = user_service.update_user(user_id, body, admin_client)
    _log_audit("user_updated", current_user["id"], user_id, body.model_dump(exclude_none=True), admin_client)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, current_user: dict = Depends(require_admin)):
    if current_user["id"] == user_id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account.")

    admin_client = get_supabase_admin_client()
    success = user_service.soft_delete_user(user_id, admin_client)
    if not success:
        raise HTTPException(status_code=404, detail="User not found.")
    _log_audit("user_deleted", current_user["id"], user_id, {}, admin_client)
