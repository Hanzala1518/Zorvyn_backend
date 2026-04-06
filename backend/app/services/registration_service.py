"""
Handles user self-registration with the approval flow:
- viewer  -> immediately active,  approval_status='approved'
- analyst -> status='inactive',   approval_status='pending_approval'
             admin must approve before they can log in
"""
import uuid
import logging
from datetime import datetime, timezone
from fastapi import HTTPException
from app.schemas.auth import RegisterRequest
from app.services.auth_service import hash_password

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _create_notification(
    user_id: str,
    notif_type: str,
    title: str,
    message: str,
    metadata: dict,
    admin_client,
) -> None:
    try:
        admin_client.table("notifications").insert({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": notif_type,
            "title": title,
            "message": message,
            "metadata": metadata,
            "created_at": _now(),
        }).execute()
    except Exception as exc:
        logger.error(f"Failed to create notification: {exc}")


def register_user(data: RegisterRequest, admin_client) -> dict:
    """
    Public registration. Returns dict with status and requires_approval flag.
    Raises 409 if email already exists (non-deleted).
    """
    existing = (
        admin_client.table("users")
        .select("id, is_deleted, approval_status")
        .eq("email", data.email.lower().strip())
        .execute()
    )
    if existing.data:
        active = [u for u in existing.data if not u.get("is_deleted")]
        if active:
            raise HTTPException(
                status_code=409,
                detail="An account with this email already exists.",
            )

    is_analyst = data.role.value == "analyst"

    record = {
        "id": str(uuid.uuid4()),
        "email": data.email.lower().strip(),
        "full_name": data.full_name.strip(),
        "password_hash": hash_password(data.password),
        "role": data.role.value,
        "status": "inactive" if is_analyst else "active",
        "approval_status": "pending_approval" if is_analyst else "approved",
        "is_deleted": False,
        "created_at": _now(),
        "updated_at": _now(),
    }

    response = admin_client.table("users").insert(record).execute()
    if not response.data:
        raise HTTPException(
            status_code=500,
            detail="Failed to create account. Please try again.",
        )

    new_user_id = response.data[0]["id"]

    if is_analyst:
        # Notify all active admins about the pending approval request
        admins = (
            admin_client.table("users")
            .select("id")
            .eq("role", "admin")
            .eq("status", "active")
            .eq("is_deleted", False)
            .execute()
        )
        for admin in (admins.data or []):
            _create_notification(
                admin["id"],
                "approval_request",
                "New Analyst Approval Request",
                f"{data.full_name} ({data.email}) has registered and is requesting Analyst access.",
                {
                    "applicant_id": new_user_id,
                    "applicant_name": data.full_name,
                    "applicant_email": data.email,
                },
                admin_client,
            )
        return {
            "message": (
                "Your account has been created. It is currently pending admin approval. "
                "You will be notified once approved."
            ),
            "status": "pending_approval",
            "requires_approval": True,
        }

    return {
        "message": "Account created successfully! You can now log in.",
        "status": "active",
        "requires_approval": False,
    }


def get_pending_approvals(admin_client) -> list:
    """Returns all users awaiting approval, ordered oldest-first."""
    response = (
        admin_client.table("users")
        .select("id, email, full_name, role, created_at, approval_status")
        .eq("approval_status", "pending_approval")
        .eq("is_deleted", False)
        .order("created_at", desc=False)
        .execute()
    )
    return response.data or []


def approve_user(user_id: str, admin_id: str, admin_client) -> dict:
    """Activate a pending analyst account."""
    check = (
        admin_client.table("users")
        .select("id, email, full_name, approval_status")
        .eq("id", user_id)
        .eq("is_deleted", False)
        .execute()
    )
    if not check.data:
        raise HTTPException(status_code=404, detail="User not found.")

    user = check.data[0]
    if user["approval_status"] != "pending_approval":
        raise HTTPException(status_code=400, detail="This user is not pending approval.")

    response = (
        admin_client.table("users")
        .update({
            "status": "active",
            "approval_status": "approved",
            "approved_by": admin_id,
            "approved_at": _now(),
            "updated_at": _now(),
        })
        .eq("id", user_id)
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to approve user.")

    _create_notification(
        user_id,
        "account_approved",
        "Your Account Has Been Approved",
        "Congratulations! Your analyst account has been approved. You can now log in to the Finance Dashboard.",
        {"approved_by_id": admin_id},
        admin_client,
    )

    return {"message": f"User {user['full_name']} has been approved successfully."}


def reject_user(user_id: str, reason: str, admin_id: str, admin_client) -> dict:
    """Reject and soft-delete a pending account with a reason."""
    check = (
        admin_client.table("users")
        .select("id, email, full_name, approval_status")
        .eq("id", user_id)
        .eq("is_deleted", False)
        .execute()
    )
    if not check.data:
        raise HTTPException(status_code=404, detail="User not found.")

    user = check.data[0]
    if user["approval_status"] != "pending_approval":
        raise HTTPException(status_code=400, detail="This user is not pending approval.")

    admin_client.table("users").update({
        "approval_status": "rejected",
        "rejection_reason": reason,
        "status": "inactive",
        "is_deleted": True,
        "updated_at": _now(),
    }).eq("id", user_id).execute()

    return {"message": f"User {user['full_name']} has been rejected."}
