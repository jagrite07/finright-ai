# ============================================================
# FinRight AI — app/services/analytics.py
#
# All financial calculations in one place.
# Pure functions — no database calls, just math on data.
#
# FUNCTIONS:
#   calculate_net_worth()          assets - liabilities
#   calculate_period_summary()     income, expenses, savings
#   calculate_category_breakdown() spending by category (pie chart)
#   calculate_monthly_trend()      monthly income vs expenses (bar chart)
#   calculate_budget_status()      actual vs budget limits
#   calculate_goal_progress()      % complete per goal
#   generate_insights()            financial tips and alerts
# ============================================================

from datetime import date as date_type, datetime
from typing import Optional
from collections import defaultdict


def calculate_net_worth(transactions: list) -> dict:
    """
    Total net worth = Total Assets - Total Liabilities.

    Returns:
        {"net_worth": 500000, "total_assets": 800000, "total_liabilities": 300000}
    """
    assets = sum(t["amount"] for t in transactions if t.get("type") == "Assets")
    liabs  = sum(t["amount"] for t in transactions if t.get("type") == "Liabilities")
    return {"net_worth": assets - liabs, "total_assets": assets, "total_liabilities": liabs}


def calculate_period_summary(transactions: list, date_from=None, date_to=None) -> dict:
    """
    Income, expenses, savings for a date range.

    Returns:
        {"income": 179859, "expenses": 25000, "savings": 154859, "savings_rate": 86.1}
    """
    ft = transactions
    if date_from: ft = [t for t in ft if t.get("date", "") >= date_from]
    if date_to:   ft = [t for t in ft if t.get("date", "") <= date_to]

    inc = sum(t["amount"] for t in ft if t.get("type") == "Income")
    exp = sum(t["amount"] for t in ft if t.get("type") == "Expenses")
    sav = inc - exp

    return {
        "income": inc,
        "expenses": exp,
        "savings": sav,
        "savings_rate": round(sav / inc * 100, 1) if inc > 0 else 0.0,
        "transaction_count": len(ft),
    }


def calculate_category_breakdown(transactions: list, txn_type="Expenses", date_from=None, date_to=None) -> list:
    """
    Spending split by sub-category for pie/donut charts.

    Returns sorted list:
        [{"category": "Food", "amount": 15000, "percentage": 60.0}, ...]
    """
    ft = [t for t in transactions if t.get("type") == txn_type]
    if date_from: ft = [t for t in ft if t.get("date", "") >= date_from]
    if date_to:   ft = [t for t in ft if t.get("date", "") <= date_to]

    totals: dict = defaultdict(float)
    for t in ft:
        cat = t.get("sub_category") or t.get("category") or "Other"
        totals[cat] += t["amount"]

    total = sum(totals.values())
    return [
        {"category": k, "amount": v, "percentage": round(v / total * 100, 1) if total > 0 else 0}
        for k, v in sorted(totals.items(), key=lambda x: -x[1])
    ]


def calculate_monthly_trend(transactions: list, months: int = 6) -> list:
    """
    Income vs expenses per month for the last N months.

    Returns:
        [{"month": "2025-01", "income": 179859, "expenses": 25000, "savings": 154859}, ...]
    """
    monthly: dict = defaultdict(lambda: {"income": 0, "expenses": 0})
    for t in transactions:
        d = t.get("date", "")
        if len(d) >= 7:
            m = d[:7]
            if t.get("type") == "Income":    monthly[m]["income"]   += t["amount"]
            elif t.get("type") == "Expenses": monthly[m]["expenses"] += t["amount"]

    sorted_months = sorted(monthly.keys())[-months:]
    return [
        {"month": m, "income": monthly[m]["income"], "expenses": monthly[m]["expenses"],
         "savings": monthly[m]["income"] - monthly[m]["expenses"]}
        for m in sorted_months
    ]


def calculate_budget_status(transactions: list, budgets: list, month: str = None) -> list:
    """
    Actual spending vs budget limits.
    Status: on_track (<70%), caution (70-100%), over_budget (>100%)

    Returns:
        [{"category": "Food", "limit": 20000, "spent": 15000, "percentage": 75.0, "status": "caution"}, ...]
    """
    if not month:
        month = datetime.now().strftime("%Y-%m")

    spending: dict = defaultdict(float)
    for t in transactions:
        if t.get("type") == "Expenses" and t.get("date", "").startswith(month):
            cat = t.get("sub_category") or t.get("category") or "Other"
            spending[cat] += t["amount"]

    result = []
    for b in budgets:
        cat = b.get("category")
        limit = b.get("limit_amount", 0)
        spent = spending.get(cat, 0)
        pct = round(spent / limit * 100, 1) if limit > 0 else 0
        status = "over_budget" if pct >= 100 else "caution" if pct >= 70 else "on_track"
        result.append({"category": cat, "limit": limit, "spent": spent,
                       "remaining": max(0, limit - spent), "percentage": pct, "status": status})
    return sorted(result, key=lambda x: -x["percentage"])


def calculate_goal_progress(goals: list) -> list:
    """
    Adds progress_pct, monthly_needed, months_remaining, is_complete to each goal.
    """
    today = date_type.today()
    result = []
    for g in goals:
        target = g.get("target", 0)
        saved  = g.get("saved", 0)
        pct    = round(saved / target * 100, 1) if target > 0 else 0
        monthly_needed = 0
        months_remaining = 0
        dl = g.get("deadline")
        if dl:
            try:
                deadline = date_type.fromisoformat(str(dl))
                months_remaining = max(1, (deadline.year - today.year) * 12 + (deadline.month - today.month))
                monthly_needed = round(max(0, target - saved) / months_remaining)
            except Exception:
                pass
        result.append({**g, "progress_pct": pct, "monthly_needed": monthly_needed,
                       "months_remaining": months_remaining, "is_complete": saved >= target})
    return result


def generate_insights(transactions: list, budgets: list, goals: list, period_summary: dict) -> list:
    """
    Generate up to 5 financial tips based on user data.
    Types: positive (green), tip (blue), caution (amber), warning (red)
    """
    insights = []
    sr = period_summary.get("savings_rate", 0)

    if sr >= 30:
        insights.append({"type": "positive", "message": f"Great! You saved {sr}% of income this period."})
    elif sr >= 10:
        insights.append({"type": "tip", "message": f"You saved {sr}%. Aim for 20-30% for financial security."})
    elif sr < 0:
        insights.append({"type": "warning", "message": "You spent more than you earned this period."})

    if period_summary.get("income", 0) == 0:
        insights.append({"type": "tip", "message": "No income recorded. Add income sources in Settings."})

    for b in calculate_budget_status(transactions, budgets):
        if b["status"] == "over_budget":
            insights.append({"type": "warning", "message": f"{b['category']} is over budget ({b['percentage']:.0f}% used)."})
        elif b["status"] == "caution":
            insights.append({"type": "caution", "message": f"{b['category']} at {b['percentage']:.0f}% of budget."})

    for g in goals:
        if g.get("target", 0) > 0:
            pct = g.get("saved", 0) / g["target"] * 100
            if pct >= 100:
                insights.append({"type": "positive", "message": f"Goal achieved: {g['name']} 🎉"})

    return insights[:5]
