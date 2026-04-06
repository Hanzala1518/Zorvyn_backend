"""
Analytics service:
- Financial Health Score (0-100)
- Recurring transaction detection
- Spending velocity (daily average + projection)
"""
import logging
from datetime import datetime, timezone, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


def _months_back(n: int) -> str:
    today = datetime.now(timezone.utc)
    # subtract ~30 days per month
    dt = today - timedelta(days=30 * n)
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()


def _current_month_bounds():
    today = datetime.now(timezone.utc)
    start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return start.isoformat(), today.isoformat()


def _last_month_bounds():
    today = datetime.now(timezone.utc)
    first_this_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_end = first_this_month - timedelta(seconds=1)
    last_month_start = last_month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return last_month_start.isoformat(), last_month_end.isoformat()


def _fetch_transactions(client, date_from: str | None = None) -> list:
    q = (
        client.table("transactions")
        .select("amount, type, category, date")
        .eq("is_deleted", False)
    )
    if date_from:
        q = q.gte("date", date_from)
    return q.execute().data or []


def compute_financial_health_score(client) -> dict:
    """
    0-100 composite score:
      Savings Rate    40 pts  (income - expenses) / income
      Diversity       20 pts  number of unique income categories
      Consistency     20 pts  % of last 6 months with positive net
      Balance         20 pts  latest-month net >= 0

    Returns grade, score, breakdown, and insights list.
    """
    six_months_ago = _months_back(6)
    txns = _fetch_transactions(client, six_months_ago)

    # Bucket by month
    by_month: dict[str, dict] = defaultdict(lambda: {"income": 0.0, "expense": 0.0, "income_categories": set()})
    for t in txns:
        month = t["date"][:7]  # "YYYY-MM"
        amount = float(t.get("amount", 0))
        if t["type"] == "income":
            by_month[month]["income"] += amount
            by_month[month]["income_categories"].add(t.get("category"))
        elif t["type"] == "expense":
            by_month[month]["expense"] += amount

    months_sorted = sorted(by_month.keys())
    current_month = datetime.now(timezone.utc).strftime("%Y-%m")

    # --- Savings Rate (40 pts) ---
    cur = by_month.get(current_month, {"income": 0.0, "expense": 0.0, "income_categories": set()})
    total_income = cur["income"]
    total_expense = cur["expense"]
    if total_income > 0:
        savings_rate = (total_income - total_expense) / total_income
    else:
        savings_rate = 0.0

    if savings_rate >= 0.3:
        savings_pts = 40
    elif savings_rate >= 0.2:
        savings_pts = 32
    elif savings_rate >= 0.1:
        savings_pts = 20
    elif savings_rate >= 0:
        savings_pts = 10
    else:
        savings_pts = 0

    # --- Diversity (20 pts) ---
    all_income_cats: set = set()
    for m in by_month.values():
        all_income_cats |= m["income_categories"]
    num_cats = len(all_income_cats - {None})
    diversity_pts = min(num_cats * 5, 20)

    # --- Consistency (20 pts): months with positive net ---
    positive_months = sum(
        1 for m in months_sorted
        if by_month[m]["income"] > by_month[m]["expense"]
    )
    total_months = len(months_sorted) or 1
    consistency_ratio = positive_months / total_months
    consistency_pts = round(consistency_ratio * 20)

    # --- Balance (20 pts): current month net ---
    net_current = total_income - total_expense
    balance_pts = 20 if net_current >= 0 else 0

    score = savings_pts + diversity_pts + consistency_pts + balance_pts

    if score >= 90:
        grade = "A+"
    elif score >= 80:
        grade = "A"
    elif score >= 70:
        grade = "B"
    elif score >= 60:
        grade = "C"
    elif score >= 50:
        grade = "D"
    else:
        grade = "F"

    insights = []
    if savings_pts < 20:
        insights.append(f"Savings rate is {round(savings_rate * 100, 1)}% — target 20%+ for a healthy buffer.")
    if diversity_pts < 10:
        insights.append("Low income diversity — consider additional income sources to reduce risk.")
    if consistency_pts < 12:
        insights.append("Irregular income/expense balance — review monthly spending patterns.")
    if balance_pts == 0:
        insights.append("Expenses exceeded income this month — review discretionary spending.")
    if not insights:
        insights.append("Excellent financial health! Keep maintaining your spending discipline.")

    return {
        "score": score,
        "grade": grade,
        "breakdown": {
            "savings_rate_pts": savings_pts,
            "diversity_pts": diversity_pts,
            "consistency_pts": consistency_pts,
            "balance_pts": balance_pts,
            "savings_rate_pct": round(savings_rate * 100, 1),
            "positive_months": positive_months,
            "total_months_analyzed": total_months,
            "income_categories": num_cats,
        },
        "insights": insights,
    }


def detect_recurring_transactions(client) -> list:
    """
    Groups transactions by (category_id, rounded_amount).
    Returns entries that appear in 2+ distinct calendar months.
    Rounds amount to nearest 5 to allow minor variations.
    """
    three_months_ago = _months_back(3)
    txns = _fetch_transactions(client, three_months_ago)

    groups: dict[tuple, list] = defaultdict(list)
    for t in txns:
        amount = float(t.get("amount", 0))
        rounded = round(amount / 5) * 5
        key = (t.get("category_id"), rounded, t.get("type"))
        month = t["transaction_date"][:7]
        groups[key].append(month)

    recurring = []
    cat_ids = set()
    for (cat_id, rounded_amt, txn_type), months in groups.items():
        unique_months = sorted(set(months))
        if len(unique_months) >= 2:
            cat_ids.add(cat_id)
            recurring.append({
                "category_id": cat_id,
                "amount": rounded_amt,
                "type": txn_type,
                "occurrences": len(months),
                "months": unique_months,
            })

    # Enrich with category names
    cat_names: dict[str, str] = {}
    if cat_ids:
        cats = client.table("categories").select("id, name").in_("id", list(cat_ids)).execute()
        for c in (cats.data or []):
            cat_names[c["id"]] = c["name"]

    for item in recurring:
        item["category_name"] = cat_names.get(item["category_id"], "Unknown")

    recurring.sort(key=lambda x: x["occurrences"], reverse=True)
    return recurring


def get_spending_velocity(client) -> dict:
    """
    Daily average spend this month vs last month.
    Projects end-of-month total for current month.
    trend: 'accelerating' | 'stable' | 'decelerating'
    """
    today = datetime.now(timezone.utc)
    cur_start, cur_end = _current_month_bounds()
    lst_start, lst_end = _last_month_bounds()

    def expense_total(date_from, date_to) -> float:
        resp = (
            client.table("transactions")
            .select("amount")
            .eq("type", "expense")
            .eq("is_deleted", False)
            .gte("transaction_date", date_from)
            .lte("transaction_date", date_to)
            .execute()
        )
        return sum(float(t.get("amount", 0)) for t in (resp.data or []))

    cur_total = expense_total(cur_start, cur_end)
    lst_total = expense_total(lst_start, lst_end)

    days_elapsed = max(today.day, 1)
    days_in_month = (
        (today.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    ).day

    # Last month days
    last_month_end_dt = today.replace(day=1) - timedelta(days=1)
    days_in_last_month = last_month_end_dt.day

    cur_daily_avg = cur_total / days_elapsed
    lst_daily_avg = lst_total / days_in_last_month if days_in_last_month > 0 else 0

    projected = cur_daily_avg * days_in_month

    if lst_daily_avg == 0:
        change_pct = 0.0
    else:
        change_pct = ((cur_daily_avg - lst_daily_avg) / lst_daily_avg) * 100

    if change_pct > 10:
        trend = "accelerating"
    elif change_pct < -10:
        trend = "decelerating"
    else:
        trend = "stable"

    return {
        "current_month": {
            "total_spent": round(cur_total, 2),
            "days_elapsed": days_elapsed,
            "daily_average": round(cur_daily_avg, 2),
            "projected_month_total": round(projected, 2),
        },
        "last_month": {
            "total_spent": round(lst_total, 2),
            "days_in_month": days_in_last_month,
            "daily_average": round(lst_daily_avg, 2),
        },
        "change_pct": round(change_pct, 1),
        "trend": trend,
    }
