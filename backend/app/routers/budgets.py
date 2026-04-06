"""
Budget management endpoints (viewer and above).
"""
import logging
from fastapi import APIRouter, Depends
from app.dependencies import require_viewer_or_above, get_supabase_admin_client, get_supabase_client
from app.services import budget_service
from app.schemas.budget import BudgetCreate, BudgetResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def list_budgets(current_user: dict = Depends(require_viewer_or_above)):
    client = get_supabase_client()
    return budget_service.get_all_budgets(current_user["id"], client)


@router.post("/", status_code=201)
async def create_budget(
    body: BudgetCreate,
    current_user: dict = Depends(require_viewer_or_above),
):
    admin_client = get_supabase_admin_client()
    return budget_service.create_or_update_budget(current_user["id"], body, admin_client)


@router.delete("/{budget_id}")
async def delete_budget(
    budget_id: str,
    current_user: dict = Depends(require_viewer_or_above),
):
    admin_client = get_supabase_admin_client()
    return budget_service.delete_budget(current_user["id"], budget_id, admin_client)
