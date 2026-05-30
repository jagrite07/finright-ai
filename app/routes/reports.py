# FinRight AI — Reports Routes
# Income vs expenses, category breakdown, savings trend, tax summary

from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.database import db_fetch_all
from app.security import get_current_user
from app.services.analytics import (
    calculate_period_summary,
    calculate_category_breakdown,
    calculate_monthly_trend,
)
from collections import defaultdict

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/summary")
async def period_summary(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    """Income, expenses, savings summary for a date range"""
    txns = await db_fetch_all("transactions", user["id"])
    return calculate_period_summary(txns, date_from, date_to)


@router.get("/income-vs-expenses")
async def income_vs_expenses(
    months: int = Query(6, ge=1, le=24),
    user: dict = Depends(get_current_user)
):
    """
    Monthly income vs expenses bar chart data.
    Used for the main reports chart.
    """
    txns = await db_fetch_all("transactions", user["id"])
    trend = calculate_monthly_trend(txns, months)

    # Add running totals
    running_savings = 0
    for month in trend:
        running_savings += month["savings"]
        month["cumulative_savings"] = running_savings

    return {
        "months": trend,
        "total_income": sum(m["income"] for m in trend),
        "total_expenses": sum(m["expenses"] for m in trend),
        "total_savings": sum(m["savings"] for m in trend),
    }


@router.get("/expenses/breakdown")
async def expense_breakdown(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    group_by: str = Query("sub_category", description="sub_category or category"),
    user: dict = Depends(get_current_user)
):
    """
    Expense breakdown by category — used for pie/donut charts.
    """
    txns = await db_fetch_all("transactions", user["id"])
    breakdown = calculate_category_breakdown(txns, "Expenses", date_from, date_to)
    return {"breakdown": breakdown, "total": sum(b["amount"] for b in breakdown)}


@router.get("/savings-trend")
async def savings_trend(
    months: int = Query(12, ge=1, le=36),
    user: dict = Depends(get_current_user)
):
    """
    Savings rate trend over time.
    Shows if user is improving or declining in savings habits.
    """
    txns = await db_fetch_all("transactions", user["id"])
    trend = calculate_monthly_trend(txns, months)

    return {
        "trend": [
            {
                "month": m["month"],
                "savings_rate": round(m["savings"] / m["income"] * 100, 1)
                               if m["income"] > 0 else 0,
                "savings": m["savings"],
            }
            for m in trend
        ]
    }


@router.get("/tax-summary")
async def tax_summary(
    year: Optional[int] = Query(None),
    user: dict = Depends(get_current_user)
):
    """
    Tax-relevant summary for the year.
    Groups income by source and expenses by deductible categories.
    """
    from datetime import datetime
    txns = await db_fetch_all("transactions", user["id"])
    tax_year = year or datetime.now().year
    year_str = str(tax_year)

    # Filter to tax year
    year_txns = [t for t in txns if t.get("date", "").startswith(year_str)]

    # Income by source
    income_by_source: dict = defaultdict(float)
    for t in year_txns:
        if t.get("type") == "Income":
            income_by_source[t.get("sub_category", "Other")] += t["amount"]

    # Deductible expenses (Insurance, Health, Education, Loan interest)
    deductible_cats = {"Insurance", "Health & Medicine", "Education", "EMI / Loan Repayment"}
    deductible: dict = defaultdict(float)
    for t in year_txns:
        if t.get("type") == "Expenses" and t.get("sub_category") in deductible_cats:
            deductible[t["sub_category"]] += t["amount"]

    total_income = sum(income_by_source.values())
    total_deductible = sum(deductible.values())

    return {
        "tax_year": tax_year,
        "total_income": total_income,
        "income_by_source": [
            {"source": k, "amount": v}
            for k, v in sorted(income_by_source.items(), key=lambda x: -x[1])
        ],
        "total_deductible_expenses": total_deductible,
        "deductible_expenses": [
            {"category": k, "amount": v}
            for k, v in sorted(deductible.items(), key=lambda x: -x[1])
        ],
        "taxable_income": max(0, total_income - total_deductible),
    }


@router.get("/account-balances")
async def account_balances(user: dict = Depends(get_current_user)):
    """
    Current balance per account based on transaction history.
    """
    txns = await db_fetch_all("transactions", user["id"])
    accounts = await db_fetch_all("accounts", user["id"])

    # Calculate balance per account from transactions
    balances: dict = defaultdict(float)
    for t in txns:
        acc = t.get("account") or "Unknown"
        if t["type"] in ("Income", "Assets"):
            balances[acc] += t["amount"]
        elif t["type"] in ("Expenses", "Liabilities"):
            balances[acc] -= t["amount"]

    # Merge with account metadata
    result = []
    for acc in accounts:
        name = acc["name"]
        result.append({
            "name": name,
            "type": acc.get("type"),
            "color": acc.get("color", "#1a6ba0"),
            "balance": balances.get(name, acc.get("balance", 0)),
        })

    return {
        "accounts": sorted(result, key=lambda x: -x["balance"]),
        "total_balance": sum(r["balance"] for r in result),
    }
