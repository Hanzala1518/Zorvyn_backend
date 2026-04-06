import logging
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from app.dependencies import (
    require_admin, require_viewer_or_above,
    get_supabase_admin_client,
)
from app.services import dashboard_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/summary")
async def summary(current_user: dict = Depends(require_viewer_or_above)):
    client = get_supabase_admin_client()
    return dashboard_service.get_summary(client)


@router.get("/category-breakdown")
async def category_breakdown(
    type: str = None,
    current_user: dict = Depends(require_viewer_or_above),
):
    client = get_supabase_admin_client()
    return dashboard_service.get_category_breakdown(type, client)


@router.get("/monthly-trends")
async def monthly_trends(
    year: int = datetime.now().year,
    current_user: dict = Depends(require_viewer_or_above),
):
    client = get_supabase_admin_client()
    return dashboard_service.get_monthly_trends(year, client)


@router.get("/weekly-trends")
async def weekly_trends(
    weeks: int = Query(8, ge=1, le=52),
    current_user: dict = Depends(require_viewer_or_above),
):
    client = get_supabase_admin_client()
    return dashboard_service.get_weekly_trends(weeks, client)


@router.get("/recent-activity")
async def recent_activity(
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(require_viewer_or_above),
):
    client = get_supabase_admin_client()
    return dashboard_service.get_recent_activity(limit, client)


@router.get("/top-categories")
async def top_categories(
    limit: int = Query(5, ge=1, le=20),
    current_user: dict = Depends(require_viewer_or_above),
):
    client = get_supabase_admin_client()
    return dashboard_service.get_top_categories(limit, client)


@router.get("/audit-logs")
async def audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_admin),
):
    client = get_supabase_admin_client()
    offset = (page - 1) * page_size
    response = (
        client.table("audit_logs")
        .select("*", count="exact")
        .order("created_at", desc=True)
        .range(offset, offset + page_size - 1)
        .execute()
    )
    return {
        "logs": response.data or [],
        "total": response.count or 0,
        "page": page,
        "page_size": page_size,
    }
