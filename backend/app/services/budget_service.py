"""
Budget management: create/update, list with live spending, status, delete.
"""
import uuid
import logging
from datetime import datetime, timezone
from fastapi import HTTPException
from app.schemas.budget import BudgetCreate, BudgetUpdate

logger = logging.getLogger(__name__)

_NOW = lambda: datetime.now(timezone.utc).isoformat()


def _get_current_month_spending(user_id: str, category: str, client) -> float:
    """Sum all expenses for the given category in the current calendar month."""
    today = datetime.now(timezone.utc)
    month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
    tomorrow = today.replace(hour=23, minute=59, second=59).isoformat()

    cats = client.table("categories").select("id").eq("name", category).execute()
    if not cats.data:
        return 0.0
    category_id = cats.data[0]["id"]

    response = (
        client.table("transactions")
        .select("amount")
        .eq("user_id", user_id)
        .eq("category_id", category_id)
        .eq("type", "expense")
        .eq("is_deleted", False)
        .gte("transaction_date", month_start)
        .lte("transaction_date", tomorrow)
        .execute()
    )
    return sum(float(t.get("amount", 0)) for t in (response.data or []))


def _budget_with_status(budget: dict, spending: float) -> dict:
    limit = float(budget.get("monthly_limit", 0))
    if limit <= 0:
        status = "safe"
    elif spending >= limit:
        status = "exceeded"
    elif spending >= limit * 0.8:
        status = "warning"
    else:
        status = "safe"

    return {
        **budget,
        "current_spending": round(spending, 2),
        "remaining": round(max(limit - spending, 0), 2),
        "status": status,
    }


def create_or_update_budget(user_id: str, data: BudgetCreate, admin_client) -> dict:
    """Upsert budget for a user+category pair."""
    existing = (
        admin_client.table("budgets")
        .select("id")
        .eq("user_id", user_id)
        .eq("category", data.category)
        .eq("is_active", True)
        .execute()
    )

    now = _NOW()
    if existing.data:
        response = (
            admin_client.table("budgets")
            .update({"monthly_limit": data.monthly_limit, "updated_at": now})
            .eq("id", existing.data[0]["id"])
            .execute()
        )
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to update budget.")
        return response.data[0]

    record = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "category": data.category,
        "monthly_limit": data.monthly_limit,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    response = admin_client.table("budgets").insert(record).execute()
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create budget.")
    return response.data[0]


def get_all_budgets(user_id: str, client) -> list:
    """Return all active budgets for the user, each with live spending."""
    response = (
        client.table("budgets")
        .select("*")
        .eq("user_id", user_id)
        .eq("is_active", True)
        .execute()
    )
    result = []
    for budget in (response.data or []):
        spending = _get_current_month_spending(user_id, budget["category"], client)
        result.append(_budget_with_status(budget, spending))
    return result


def get_budget_status(user_id: str, category: str, client) -> dict:
    """Return a single budget's status for the current month."""
    response = (
        client.table("budgets")
        .select("*")
        .eq("user_id", user_id)
        .eq("category", category)
        .eq("is_active", True)
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="No active budget found for this category.")
    spending = _get_current_month_spending(user_id, category, client)
    return _budget_with_status(response.data[0], spending)


def delete_budget(user_id: str, budget_id: str, admin_client) -> dict:
    """Soft-delete a budget."""
    check = (
        admin_client.table("budgets")
        .select("id, user_id")
        .eq("id", budget_id)
        .eq("is_active", True)
        .execute()
    )
    if not check.data:
        raise HTTPException(status_code=404, detail="Budget not found.")
    if check.data[0]["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied.")

    admin_client.table("budgets").update({
        "is_active": False,
        "updated_at": _NOW(),
    }).eq("id", budget_id).execute()

    return {"message": "Budget deleted successfully."}
