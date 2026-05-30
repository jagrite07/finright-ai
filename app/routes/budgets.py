# FinRight AI — Budget Routes
# Set and manage spending limits per category

from fastapi import APIRouter, Depends, HTTPException
from app.schema import BudgetCreate, MessageResponse
from app.database import db_fetch_all, db_insert, db_update, db_delete, db_upsert
from app.security import get_current_user
from app.services.analytics import calculate_budget_status
from app.constants import MSG
from datetime import datetime
import uuid

router = APIRouter(prefix="/budgets", tags=["Budgets"])


@router.get("/")
async def list_budgets(user: dict = Depends(get_current_user)):
    """
    Get all budgets with current month spending status.
    Shows: limit, spent, remaining, percentage, status color.
    """
    uid = user["id"]
    budgets = await db_fetch_all("budgets", uid)
    txns = await db_fetch_all("transactions", uid)

    current_month = datetime.now().strftime("%Y-%m")
    budget_status = calculate_budget_status(txns, budgets, current_month)

    return {
        "budgets": budget_status,
        "month": current_month,
        "total_limit": sum(b.get("limit_amount", 0) for b in budgets),
        "total_spent": sum(b.get("spent", 0) for b in budget_status),
    }


@router.post("/", response_model=MessageResponse, status_code=201)
async def set_budget(data: BudgetCreate, user: dict = Depends(get_current_user)):
    """
    Set a budget for a category.
    If a budget for that category already exists, update it.
    """
    uid = user["id"]
    existing = await db_fetch_all("budgets", uid, {"category": data.category})

    if existing:
        # Update existing budget
        result = await db_update(
            "budgets", existing[0]["id"], uid,
            {"limit_amount": data.limit_amount, "currency": data.currency}
        )
        return MessageResponse(success=True, message="Budget updated", data=result)
    else:
        # Create new budget
        row = {
            "id": str(uuid.uuid4()),
            "user_id": uid,
            "category": data.category,
            "limit_amount": data.limit_amount,
            "currency": data.currency,
            "month": data.month or "all",
        }
        result = await db_insert("budgets", row)
        if not result:
            raise HTTPException(status_code=500, detail=MSG["server_error"])
        return MessageResponse(success=True, message=MSG["budget_saved"], data=result)


@router.delete("/{budget_id}", response_model=MessageResponse)
async def delete_budget(budget_id: str, user: dict = Depends(get_current_user)):
    """Remove a budget limit"""
    success = await db_delete("budgets", budget_id, user["id"])
    if not success:
        raise HTTPException(status_code=404, detail=MSG["not_found"])
    return MessageResponse(success=True, message="Budget removed")


@router.get("/alerts")
async def budget_alerts(user: dict = Depends(get_current_user)):
    """
    Returns only budgets that need attention:
    - Over budget (red)
    - Approaching limit (amber, >70%)
    """
    uid = user["id"]
    budgets = await db_fetch_all("budgets", uid)
    txns = await db_fetch_all("transactions", uid)
    current_month = datetime.now().strftime("%Y-%m")
    status = calculate_budget_status(txns, budgets, current_month)

    alerts = [b for b in status if b["status"] in ("over_budget", "caution")]
    return {"alerts": alerts, "count": len(alerts)}
