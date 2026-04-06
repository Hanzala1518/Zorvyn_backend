import logging
import time
from typing import Optional, List
from collections import defaultdict
from datetime import datetime, date, timedelta, timezone
from calendar import month_name
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

_cache: dict = {}
CACHE_TTL = 300  # 5 minutes — reduces repeated Supabase round-trips


def _get_cached(key: str):
    entry = _cache.get(key)
    if entry and (time.time() - entry["ts"]) < CACHE_TTL:
        return entry["data"]
    return None


def _set_cached(key: str, value):
    _cache[key] = {"data": value, "ts": time.time()}


def _fetch_all_active(client) -> list:
    response = (
        client.table("transactions")
        .select("amount, type, category, date, created_at, created_by, id, description, notes")
        .eq("is_deleted", False)
        .execute()
    )
    rows = response.data or []
    for r in rows:
        r["amount"] = float(r.get("amount", 0) or 0)
    return rows


def get_summary(client) -> dict:
    cached = _get_cached("summary")
    if cached:
        return cached

    rows = _fetch_all_active(client)
    income = sum(r["amount"] for r in rows if r["type"] == "income")
    expenses = sum(r["amount"] for r in rows if r["type"] == "expense")

    result = {
        "total_income": round(income, 2),
        "total_expenses": round(expenses, 2),
        "net_balance": round(income - expenses, 2),
        "transaction_count": len(rows),
        "income_count": sum(1 for r in rows if r["type"] == "income"),
        "expense_count": sum(1 for r in rows if r["type"] == "expense"),
    }
    _set_cached("summary", result)
    return result


def get_category_breakdown(transaction_type: str | None, client) -> list:
    rows = _fetch_all_active(client)
    if transaction_type:
        rows = [r for r in rows if r["type"] == transaction_type]

    totals = defaultdict(lambda: {"total": 0.0, "count": 0})
    for r in rows:
        totals[r["category"]]["total"] += r["amount"]
        totals[r["category"]]["count"] += 1

    grand_total = sum(v["total"] for v in totals.values()) or 1
    result = [
        {
            "category": cat,
            "total": round(v["total"], 2),
            "count": v["count"],
            "percentage": round((v["total"] / grand_total) * 100, 1),
        }
        for cat, v in totals.items()
    ]
    return sorted(result, key=lambda x: x["total"], reverse=True)


def get_monthly_trends(year: int, client) -> list:
    rows = _fetch_all_active(client)
    rows = [r for r in rows if r["date"] and r["date"].startswith(str(year))]

    months = {i: {"income": 0.0, "expenses": 0.0} for i in range(1, 13)}
    for r in rows:
        try:
            m = int(r["date"][5:7])
            if r["type"] == "income":
                months[m]["income"] += r["amount"]
            else:
                months[m]["expenses"] += r["amount"]
        except Exception:
            continue

    return [
        {
            "month": m,
            "month_name": month_name[m],
            "income": round(months[m]["income"], 2),
            "expenses": round(months[m]["expenses"], 2),
            "net": round(months[m]["income"] - months[m]["expenses"], 2),
        }
        for m in range(1, 13)
    ]


def get_weekly_trends(weeks: int, client) -> list:
    cutoff = date.today() - timedelta(weeks=weeks)
    rows = _fetch_all_active(client)
    rows = [r for r in rows if r["date"] and r["date"] >= cutoff.isoformat()]

    week_data = defaultdict(lambda: {"income": 0.0, "expenses": 0.0})
    for r in rows:
        try:
            d = date.fromisoformat(r["date"][:10])
            week_key = f"{d.isocalendar()[0]}-W{d.isocalendar()[1]:02d}"
            if r["type"] == "income":
                week_data[week_key]["income"] += r["amount"]
            else:
                week_data[week_key]["expenses"] += r["amount"]
        except Exception:
            continue

    return sorted(
        [
            {
                "week": w,
                "income": round(v["income"], 2),
                "expenses": round(v["expenses"], 2),
                "net": round(v["income"] - v["expenses"], 2),
            }
            for w, v in week_data.items()
        ],
        key=lambda x: x["week"],
    )


def get_recent_activity(limit: int, client) -> list:
    response = (
        client.table("transactions")
        .select("id, amount, type, category, date, description, notes, created_by, created_at")
        .eq("is_deleted", False)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    rows = response.data or []

    user_ids = list({r["created_by"] for r in rows if r.get("created_by")})
    user_map = {}
    if user_ids:
        users_resp = (
            client.table("users")
            .select("id, email, full_name")
            .in_("id", user_ids)
            .execute()
        )
        user_map = {u["id"]: u for u in (users_resp.data or [])}

    result = []
    for r in rows:
        user = user_map.get(r.get("created_by"), {})
        result.append({
            **r,
            "amount": float(r.get("amount") or 0),
            "created_by_email": user.get("email", "Unknown"),
            "created_by_name": user.get("full_name", "Unknown"),
        })
    return result


def get_top_categories(limit: int, client) -> list:
    breakdown = get_category_breakdown("expense", client)
    return breakdown[:limit]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _raise(exc: Exception):
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=str(exc),
    )


# ── 1. Summary ──────────────────────────────────────────────────────────────

def get_summary(client) -> dict:
    try:
        rows = (
            client.table("transactions")
            .select("amount, type")
            .eq("is_deleted", False)
            .execute()
            .data
        )
    except Exception as exc:
        _raise(exc)

    income_rows  = [r for r in rows if r["type"] == "income"]
    expense_rows = [r for r in rows if r["type"] == "expense"]

    total_income   = round(sum(float(r["amount"]) for r in income_rows),  2)
    total_expenses = round(sum(float(r["amount"]) for r in expense_rows), 2)
    net_balance    = round(total_income - total_expenses, 2)

    return {
        "total_income":      total_income,
        "total_expenses":    total_expenses,
        "net_balance":       net_balance,
        "transaction_count": len(rows),
        "income_count":      len(income_rows),
        "expense_count":     len(expense_rows),
    }


# ── 2. Category breakdown ────────────────────────────────────────────────────

def get_category_breakdown(
    transaction_type: Optional[str],
    client,
) -> list:
    try:
        query = (
            client.table("transactions")
            .select("amount, type, category")
            .eq("is_deleted", False)
        )
        if transaction_type:
            query = query.eq("type", transaction_type)
        rows = query.execute().data
    except Exception as exc:
        _raise(exc)

    buckets: dict = defaultdict(lambda: {"total": 0.0, "count": 0})
    grand_total = 0.0

    for r in rows:
        amount = float(r["amount"])
        buckets[r["category"]]["total"] += amount
        buckets[r["category"]]["count"] += 1
        grand_total += amount

    result = []
    for cat, vals in buckets.items():
        pct = round(vals["total"] / grand_total * 100, 2) if grand_total else 0.0
        result.append({
            "category":   cat,
            "total":      round(vals["total"], 2),
            "count":      vals["count"],
            "percentage": pct,
        })

    result.sort(key=lambda x: x["total"], reverse=True)
    return result


# ── 3. Monthly trends ────────────────────────────────────────────────────────

def get_monthly_trends(year: int, client) -> list:
    try:
        rows = (
            client.table("transactions")
            .select("amount, type, date")
            .eq("is_deleted", False)
            .gte("date", f"{year}-01-01")
            .lte("date", f"{year}-12-31")
            .execute()
            .data
        )
    except Exception as exc:
        _raise(exc)

    monthly: dict = {
        m: {"income": 0.0, "expenses": 0.0}
        for m in range(1, 13)
    }
    for r in rows:
        m = int(r["date"][5:7])
        amount = float(r["amount"])
        if r["type"] == "income":
            monthly[m]["income"] += amount
        else:
            monthly[m]["expenses"] += amount

    return [
        {
            "month":      m,
            "month_name": month_name[m],
            "income":     round(vals["income"], 2),
            "expenses":   round(vals["expenses"], 2),
            "net":        round(vals["income"] - vals["expenses"], 2),
        }
        for m, vals in sorted(monthly.items())
    ]


# ── 4. Weekly trends ─────────────────────────────────────────────────────────

def get_weekly_trends(weeks: int, client) -> list:
    since = (_utcnow() - timedelta(weeks=weeks)).date()
    try:
        rows = (
            client.table("transactions")
            .select("amount, type, date")
            .eq("is_deleted", False)
            .gte("date", since.isoformat())
            .execute()
            .data
        )
    except Exception as exc:
        _raise(exc)

    buckets: dict = defaultdict(lambda: {"income": 0.0, "expenses": 0.0})
    for r in rows:
        d = datetime.fromisoformat(r["date"]).date() if "T" in r["date"] else \
            datetime.strptime(r["date"][:10], "%Y-%m-%d").date()
        iso_week = f"{d.isocalendar()[0]}-W{d.isocalendar()[1]:02d}"
        amount = float(r["amount"])
        if r["type"] == "income":
            buckets[iso_week]["income"] += amount
        else:
            buckets[iso_week]["expenses"] += amount

    return [
        {
            "week":     week,
            "income":   round(vals["income"], 2),
            "expenses": round(vals["expenses"], 2),
            "net":      round(vals["income"] - vals["expenses"], 2),
        }
        for week, vals in sorted(buckets.items())
    ]


# ── 5. Recent activity ───────────────────────────────────────────────────────

def get_recent_activity(limit: int, client) -> list:
    try:
        rows = (
            client.table("transactions")
            .select("id, amount, type, category, date, description, created_by, created_at")
            .eq("is_deleted", False)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
            .data
        )
    except Exception as exc:
        _raise(exc)

    # Fetch emails for distinct created_by IDs
    user_ids = list({r["created_by"] for r in rows if r.get("created_by")})
    email_map: dict = {}
    if user_ids:
        try:
            users = (
                client.table("users")
                .select("id, email")
                .in_("id", user_ids)
                .execute()
                .data
            )
            email_map = {u["id"]: u["email"] for u in users}
        except Exception:
            pass

    return [
        {
            "id":               r["id"],
            "amount":           float(r["amount"]),
            "type":             r["type"],
            "category":         r["category"],
            "date":             r["date"],
            "description":      r.get("description"),
            "created_by_email": email_map.get(r["created_by"]),
            "created_at":       r["created_at"],
        }
        for r in rows
    ]


# ── 6. Top categories ────────────────────────────────────────────────────────

def get_top_categories(limit: int, client) -> list:
    try:
        rows = (
            client.table("transactions")
            .select("amount, category")
            .eq("is_deleted", False)
            .eq("type", "expense")
            .execute()
            .data
        )
    except Exception as exc:
        _raise(exc)

    buckets: dict = defaultdict(lambda: {"total": 0.0, "count": 0})
    for r in rows:
        buckets[r["category"]]["total"]  += float(r["amount"])
        buckets[r["category"]]["count"]  += 1

    sorted_cats = sorted(buckets.items(), key=lambda x: x[1]["total"], reverse=True)
    return [
        {
            "category": cat,
            "total":    round(vals["total"], 2),
            "count":    vals["count"],
        }
        for cat, vals in sorted_cats[:limit]
    ]


# ── kept for legacy import guard ─────────────────────────────────────────────
class DashboardService:
    """Thin shim — use module-level functions directly."""

    def __init__(self, supabase) -> None:
        self._c = supabase
