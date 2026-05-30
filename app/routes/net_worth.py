# FinRight AI — Net Worth Routes
# Assets, liabilities, net worth timeline

from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.database import db_fetch_all
from app.security import get_current_user
from app.services.analytics import calculate_net_worth
from collections import defaultdict

router = APIRouter(prefix="/net-worth", tags=["Net Worth"])


@router.get("/")
async def get_net_worth(user: dict = Depends(get_current_user)):
    """
    Current net worth snapshot.
    Returns: total assets, total liabilities, net worth,
             breakdown by category, and liquid vs illiquid.
    """
    txns = await db_fetch_all("transactions", user["id"])

    net_worth = calculate_net_worth(txns)

    # Asset breakdown by sub-category
    asset_breakdown: dict = defaultdict(float)
    for t in txns:
        if t.get("type") == "Assets":
            cat = t.get("sub_category") or t.get("category") or "Other"
            asset_breakdown[cat] += t["amount"]

    # Liability breakdown
    liability_breakdown: dict = defaultdict(float)
    for t in txns:
        if t.get("type") == "Liabilities":
            cat = t.get("sub_category") or t.get("category") or "Other"
            liability_breakdown[cat] += t["amount"]

    # Liquid vs illiquid assets
    liquid_cats = {"Cash", "Savings account", "Digital wallet balances", "Fixed Deposit"}
    liquid = sum(v for k, v in asset_breakdown.items() if k in liquid_cats)
    illiquid = net_worth["total_assets"] - liquid

    return {
        "net_worth": net_worth["net_worth"],
        "total_assets": net_worth["total_assets"],
        "total_liabilities": net_worth["total_liabilities"],
        "liquid_assets": liquid,
        "illiquid_assets": illiquid,
        "asset_breakdown": [
            {"category": k, "amount": v}
            for k, v in sorted(asset_breakdown.items(), key=lambda x: -x[1])
        ],
        "liability_breakdown": [
            {"category": k, "amount": v}
            for k, v in sorted(liability_breakdown.items(), key=lambda x: -x[1])
        ],
    }


@router.get("/timeline")
async def net_worth_timeline(
    months: int = Query(12, ge=1, le=60),
    user: dict = Depends(get_current_user)
):
    """
    Net worth change over time (month by month).
    Shows how your wealth has grown or shrunk.
    """
    txns = await db_fetch_all("transactions", user["id"])

    # Get all unique months from transactions
    all_months = sorted(set(
        t["date"][:7] for t in txns if t.get("date")
    ))[-months:]

    timeline = []
    for month in all_months:
        end_date = month + "-31"
        assets = sum(
            t["amount"] for t in txns
            if t.get("type") == "Assets" and t.get("date", "") <= end_date
        )
        liabilities = sum(
            t["amount"] for t in txns
            if t.get("type") == "Liabilities" and t.get("date", "") <= end_date
        )
        timeline.append({
            "month": month,
            "assets": assets,
            "liabilities": liabilities,
            "net_worth": assets - liabilities,
        })

    # Calculate growth
    if len(timeline) >= 2:
        first = timeline[0]["net_worth"]
        last = timeline[-1]["net_worth"]
        growth = last - first
        growth_pct = round((growth / abs(first) * 100), 1) if first != 0 else 0
    else:
        growth = growth_pct = 0

    return {
        "timeline": timeline,
        "growth": growth,
        "growth_pct": growth_pct,
        "months_tracked": len(timeline),
    }
