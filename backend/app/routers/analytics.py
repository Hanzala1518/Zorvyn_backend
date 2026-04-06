"""
Analytics endpoints (analyst and above).
"""
import logging
from fastapi import APIRouter, Depends
from app.dependencies import require_analyst_or_above, get_supabase_client

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health-score")
async def health_score(current_user: dict = Depends(require_analyst_or_above)):
    from app.services import analytics_service
    client = get_supabase_client()
    return analytics_service.compute_financial_health_score(client)


@router.get("/recurring")
async def recurring(current_user: dict = Depends(require_analyst_or_above)):
    from app.services import analytics_service
    client = get_supabase_client()
    return analytics_service.detect_recurring_transactions(client)


@router.get("/velocity")
async def velocity(current_user: dict = Depends(require_analyst_or_above)):
    from app.services import analytics_service
    client = get_supabase_client()
    return analytics_service.get_spending_velocity(client)
