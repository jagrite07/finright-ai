# FinRight AI — Dashboard Route
# Returns everything the dashboard needs in ONE API call
# Fast, efficient — single request loads the whole dashboard

from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.database import db_fetch_all
from app.security import get_current_user
from app.services.analytics import (
    calculate_net_worth,
    calculate_period_summary,
    calculate_category_breakdown,
    calculate_monthly_trend,
    calculate_budget_status,
    calculate_goal_progress,
    generate_insights,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/")
async def get_dashboard(
    date_from: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    user: dict = Depends(get_current_user)
):
    """
    Returns complete dashboard data in one call:
    - Net worth
    - Period summary (income, expenses, savings)
    - Top spending categories
    - Monthly trend (last 6 months)
    - Budget status
    - Goal progress
    - AI insights
    """
    uid = user["id"]

    # Load all data in parallel (one call each)
    txns    = await db_fetch_all("transactions", uid)
    budgets = await db_fetch_all("budgets", uid)
    goals   = await db_fetch_all("goals", uid)
    profile = await db_fetch_all("profiles", uid)

    prof = profile[0] if profile else {}

    # Calculate everything
    net_worth      = calculate_net_worth(txns)
    period_summary = calculate_period_summary(txns, date_from, date_to)
    categories     = calculate_category_breakdown(txns, "Expenses", date_from, date_to)
    monthly_trend  = calculate_monthly_trend(txns, months=6)
    budget_status  = calculate_budget_status(txns, budgets)
    goal_progress  = calculate_goal_progress(goals)
    insights       = generate_insights(txns, budgets, goals, period_summary)

    # Top spending category
    top_category = categories[0]["category"] if categories else "—"

    # Savings rate color
    sr = period_summary["savings_rate"]
    sr_color = "#22c97a" if sr >= 20 else "#ffb347" if sr >= 0 else "#ff5e7a"

    return {
        "period": {
            "from": date_from or "All Time",
            "to": date_to or "All Time",
        },
        "net_worth": net_worth,
        "period_summary": period_summary,
        "savings_rate_color": sr_color,
        "top_category": top_category,
        "categories": categories[:6],           # top 6 expense categories
        "monthly_trend": monthly_trend,
        "budget_status": budget_status[:5],     # top 5 budgets
        "goals": goal_progress[:4],             # top 4 goals
        "insights": insights,
        "profile": {
            "name": prof.get("full_name", ""),
            "currency": prof.get("currency", "NPR"),
        }
    }


@router.get("/summary")
async def get_quick_summary(user: dict = Depends(get_current_user)):
    """
    Quick summary — used for sidebar stats and header cards.
    Lighter than full dashboard.
    """
    uid = user["id"]
    txns = await db_fetch_all("transactions", uid)
    net_worth = calculate_net_worth(txns)
    summary = calculate_period_summary(txns)

    return {
        "net_worth": net_worth["net_worth"],
        "total_assets": net_worth["total_assets"],
        "total_liabilities": net_worth["total_liabilities"],
        "income": summary["income"],
        "expenses": summary["expenses"],
        "savings": summary["savings"],
        "savings_rate": summary["savings_rate"],
        "transaction_count": len(txns),
    }
