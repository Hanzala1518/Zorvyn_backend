import logging
import uuid
from typing import Optional, List
from datetime import datetime, timezone
from fastapi import HTTPException, status
from app.schemas.transaction import TransactionCreate, TransactionUpdate, TransactionFilter

logger = logging.getLogger(__name__)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log_audit(action: str, performed_by: str, target_id: str, details: dict, admin_client) -> None:
    try:
        admin_client.table("audit_logs").insert({
            "id": str(uuid.uuid4()),
            "action": action,
            "performed_by": performed_by,
            "target_id": target_id,
            "details": details,
            "created_at": _utcnow(),
        }).execute()
    except Exception as exc:
        logger.error(f"Audit log failed action={action}: {exc}")


def _apply_filters(query, filters: TransactionFilter):
    if filters.type:
        query = query.eq("type", filters.type.value)
    if filters.category:
        query = query.ilike("category", f"%{filters.category}%")
    if filters.date_from:
        query = query.gte("date", filters.date_from.isoformat())
    if filters.date_to:
        query = query.lte("date", filters.date_to.isoformat())
    if filters.min_amount is not None:
        query = query.gte("amount", str(filters.min_amount))
    if filters.max_amount is not None:
        query = query.lte("amount", str(filters.max_amount))
    if filters.search:
        s = filters.search
        query = query.or_(f"notes.ilike.%{s}%,description.ilike.%{s}%,category.ilike.%{s}%")
    return query


def _normalize(record: dict) -> dict:
    if record and "amount" in record:
        try:
            record["amount"] = float(record["amount"])
        except (TypeError, ValueError):
            pass
    return record


def create_transaction(data: TransactionCreate, user_id: str, client, admin_client) -> dict:
    now = _utcnow()
    new_record = {
        "id": str(uuid.uuid4()),
        "amount": str(data.amount),
        "type": data.type.value,
        "category": data.category.strip(),
        "date": data.date.isoformat(),
        "notes": data.notes,
        "description": data.description,
        "created_by": user_id,
        "is_deleted": False,
        "created_at": now,
        "updated_at": now,
    }
    try:
        response = admin_client.table("transactions").insert(new_record).execute()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create transaction.")
    record = _normalize(response.data[0])
    _log_audit(
        "transaction_created", user_id, record["id"],
        {"amount": str(data.amount), "type": data.type.value, "category": data.category},
        admin_client,
    )
    return record


def get_transaction_by_id(transaction_id: str, client) -> Optional[dict]:
    response = (
        client.table("transactions")
        .select("*")
        .eq("id", transaction_id)
        .eq("is_deleted", False)
        .execute()
    )
    return _normalize(response.data[0]) if response.data else None


def get_transactions(filters: TransactionFilter, page: int, page_size: int, client) -> dict:
    offset = (page - 1) * page_size
    try:
        count_q = _apply_filters(
            client.table("transactions").select("id", count="exact").eq("is_deleted", False),
            filters,
        )
        total = count_q.execute().count or 0
        data_q = _apply_filters(
            client.table("transactions").select("*").eq("is_deleted", False),
            filters,
        )
        rows = (
            data_q
            .order("date", desc=True)
            .order("created_at", desc=True)
            .range(offset, offset + page_size - 1)
            .execute()
            .data
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
    return {
        "transactions": [_normalize(r) for r in (rows or [])],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def get_all_for_export(filters: TransactionFilter, client) -> list:
    try:
        data_q = _apply_filters(
            client.table("transactions").select("*").eq("is_deleted", False),
            filters,
        )
        rows = data_q.order("date", desc=True).execute().data
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
    return [_normalize(r) for r in (rows or [])]


get_all_transactions_for_export = get_all_for_export


def update_transaction(transaction_id: str, data: TransactionUpdate, user_id: str, client, admin_client) -> dict:
    update_dict = data.model_dump(exclude_none=True)
    if "type" in update_dict:
        update_dict["type"] = update_dict["type"].value
    if "amount" in update_dict:
        update_dict["amount"] = str(update_dict["amount"])
    if "date" in update_dict:
        update_dict["date"] = update_dict["date"].isoformat()
    if not update_dict:
        raise HTTPException(status_code=400, detail="No fields to update.")
    update_dict["updated_at"] = _utcnow()
    try:
        response = (
            admin_client.table("transactions")
            .update(update_dict)
            .eq("id", transaction_id)
            .eq("is_deleted", False)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found.")
    _log_audit(
        "transaction_updated", user_id, transaction_id,
        data.model_dump(exclude_none=True, mode="json"),
        admin_client,
    )
    return _normalize(response.data[0])


def soft_delete_transaction(transaction_id: str, user_id: str, admin_client, client=None) -> bool:
    try:
        response = (
            admin_client.table("transactions")
            .update({"is_deleted": True, "updated_at": _utcnow()})
            .eq("id", transaction_id)
            .eq("is_deleted", False)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found.")
    _log_audit("transaction_deleted", user_id, transaction_id, {}, admin_client)
    return True
