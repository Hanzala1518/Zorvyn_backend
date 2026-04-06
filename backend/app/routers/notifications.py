"""
Notification endpoints: list, mark-read, mark-all-read.
"""
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_current_user, get_supabase_admin_client

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def list_notifications(current_user: dict = Depends(get_current_user)):
    admin_client = get_supabase_admin_client()
    response = (
        admin_client.table("notifications")
        .select("*")
        .eq("user_id", current_user["id"])
        .order("created_at", desc=True)
        .execute()
    )
    notifications = response.data or []
    unread_count = sum(1 for n in notifications if not n.get("is_read"))
    return {"notifications": notifications, "unread_count": unread_count}


@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
):
    admin_client = get_supabase_admin_client()
    check = (
        admin_client.table("notifications")
        .select("id, user_id")
        .eq("id", notification_id)
        .execute()
    )
    if not check.data:
        raise HTTPException(status_code=404, detail="Notification not found.")
    if check.data[0]["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied.")

    admin_client.table("notifications").update({
        "is_read": True,
        "read_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", notification_id).execute()

    return {"message": "Notification marked as read."}


@router.patch("/read-all")
async def mark_all_read(current_user: dict = Depends(get_current_user)):
    admin_client = get_supabase_admin_client()
    admin_client.table("notifications").update({
        "is_read": True,
        "read_at": datetime.now(timezone.utc).isoformat(),
    }).eq("user_id", current_user["id"]).eq("is_read", False).execute()

    return {"message": "All notifications marked as read."}
