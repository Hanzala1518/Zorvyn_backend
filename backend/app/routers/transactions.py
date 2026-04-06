import csv
import logging
from io import StringIO
from datetime import date
from typing import Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from app.dependencies import (
    require_admin,
    require_analyst_or_above, require_viewer_or_above,
    get_supabase_admin_client,
)
from app.services import transaction_service
from app.schemas.transaction import TransactionCreate, TransactionUpdate, TransactionFilter, TransactionType

logger = logging.getLogger(__name__)
router = APIRouter()


def _build_filters(
    type: Optional[TransactionType] = None,
    category: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    min_amount: Optional[Decimal] = None,
    max_amount: Optional[Decimal] = None,
    search: Optional[str] = None,
) -> TransactionFilter:
    return TransactionFilter(
        type=type, category=category, date_from=date_from, date_to=date_to,
        min_amount=min_amount, max_amount=max_amount, search=search,
    )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_transaction(
    body: TransactionCreate,
    current_user: dict = Depends(require_analyst_or_above),
):
    admin_client = get_supabase_admin_client()
    return transaction_service.create_transaction(body, current_user["id"], admin_client, admin_client)


@router.get("/export")
async def export_transactions(
    current_user: dict = Depends(require_analyst_or_above),
    type: Optional[TransactionType] = None,
    category: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    min_amount: Optional[Decimal] = None,
    max_amount: Optional[Decimal] = None,
    search: Optional[str] = None,
):
    filters = _build_filters(type, category, date_from, date_to, min_amount, max_amount, search)
    client = get_supabase_admin_client()
    rows = transaction_service.get_all_for_export(filters, client)

    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["id", "amount", "type", "category", "date", "notes", "description", "created_at"],
        extrasaction="ignore",
    )
    writer.writeheader()
    writer.writerows(rows)
    output.seek(0)

    filename = f"transactions_{date.today().isoformat()}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/")
async def list_transactions(
    current_user: dict = Depends(require_viewer_or_above),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    type: Optional[TransactionType] = None,
    category: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    min_amount: Optional[Decimal] = None,
    max_amount: Optional[Decimal] = None,
    search: Optional[str] = None,
):
    filters = _build_filters(type, category, date_from, date_to, min_amount, max_amount, search)
    client = get_supabase_admin_client()
    return transaction_service.get_transactions(filters, page, page_size, client)


@router.get("/{transaction_id}")
async def get_transaction(
    transaction_id: str,
    current_user: dict = Depends(require_viewer_or_above),
):
    client = get_supabase_admin_client()
    tx = transaction_service.get_transaction_by_id(transaction_id, client)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    return tx


@router.patch("/{transaction_id}")
async def update_transaction(
    transaction_id: str,
    body: TransactionUpdate,
    current_user: dict = Depends(require_analyst_or_above),
):
    admin_client = get_supabase_admin_client()
    tx = transaction_service.get_transaction_by_id(transaction_id, admin_client)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    return transaction_service.update_transaction(transaction_id, body, current_user["id"], admin_client, admin_client)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: str,
    current_user: dict = Depends(require_admin),
):
    admin_client = get_supabase_admin_client()
    success = transaction_service.soft_delete_transaction(transaction_id, current_user["id"], admin_client)
    if not success:
        raise HTTPException(status_code=404, detail="Transaction not found.")
