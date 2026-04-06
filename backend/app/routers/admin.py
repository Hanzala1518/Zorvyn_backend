"""
Admin-only endpoints:
- Pending approval queue
- Approve / reject user accounts
- Health score, spending velocity, recurring transactions
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies import require_admin, get_supabase_admin_client, get_supabase_client
from app.services import registration_service, analytics_service
from app.schemas.auth import RejectUserRequest

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/pending-approvals")
async def pending_approvals(current_user: dict = Depends(require_admin)):
    admin_client = get_supabase_admin_client()
    return registration_service.get_pending_approvals(admin_client)


@router.post("/approve/{user_id}")
async def approve_user(user_id: str, current_user: dict = Depends(require_admin)):
    admin_client = get_supabase_admin_client()
    return registration_service.approve_user(user_id, current_user["id"], admin_client)


@router.post("/reject/{user_id}")
async def reject_user(
    user_id: str,
    body: RejectUserRequest,
    current_user: dict = Depends(require_admin),
):
    admin_client = get_supabase_admin_client()
    return registration_service.reject_user(
        user_id, body.reason, current_user["id"], admin_client
    )


@router.get("/health-score")
async def health_score(current_user: dict = Depends(require_admin)):
    client = get_supabase_client()
    return analytics_service.compute_financial_health_score(client)


@router.get("/spending-velocity")
async def spending_velocity(current_user: dict = Depends(require_admin)):
    client = get_supabase_client()
    return analytics_service.get_spending_velocity(client)


@router.get("/recurring-transactions")
async def recurring_transactions(current_user: dict = Depends(require_admin)):
    client = get_supabase_client()
    return analytics_service.detect_recurring_transactions(client)
