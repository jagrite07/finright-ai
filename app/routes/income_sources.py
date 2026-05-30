# FinRight AI — Income Sources Routes
# Manage recurring income streams: salary, business, rental, etc.

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.database import db_fetch_all, db_insert, db_update, db_delete
from app.security import get_current_user
from app.constants import MSG
import uuid

router = APIRouter(prefix="/income-sources", tags=["Income Sources"])


class IncomeSourceCreate(BaseModel):
    name: str
    type: str = "Salary / Bonus"
    amount: float
    currency: str = "NPR"
    frequency: str = "Monthly"   # Monthly, Weekly, Annual, One-time
    account: Optional[str] = None
    note: Optional[str] = None


class IncomeSourceUpdate(BaseModel):
    name: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    frequency: Optional[str] = None
    account: Optional[str] = None
    note: Optional[str] = None


@router.get("/")
async def list_income_sources(user: dict = Depends(get_current_user)):
    """
    Get all income sources with monthly equivalent calculated.
    Converts annual/weekly amounts to monthly for comparison.
    """
    sources = await db_fetch_all("income_sources", user["id"])

    # Calculate monthly equivalent for each
    for s in sources:
        s["monthly_equivalent"] = _to_monthly(s.get("amount", 0), s.get("frequency", "Monthly"))

    total_monthly = sum(s["monthly_equivalent"] for s in sources)
    total_annual = total_monthly * 12

    return {
        "sources": sources,
        "total_monthly": total_monthly,
        "total_annual": total_annual,
        "count": len(sources),
    }


@router.post("/", status_code=201)
async def create_income_source(
    data: IncomeSourceCreate,
    user: dict = Depends(get_current_user)
):
    """Add a new income source"""
    row = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "name": data.name,
        "type": data.type,
        "amount": data.amount,
        "currency": data.currency,
        "frequency": data.frequency,
        "account": data.account,
        "note": data.note or "",
    }
    result = await db_insert("income_sources", row)
    if not result:
        raise HTTPException(status_code=500, detail=MSG["server_error"])
    return {"success": True, "message": "Income source added", "data": result}


@router.put("/{source_id}")
async def update_income_source(
    source_id: str,
    data: IncomeSourceUpdate,
    user: dict = Depends(get_current_user)
):
    """Update an income source"""
    updates = data.model_dump(exclude_none=True)
    result = await db_update("income_sources", source_id, user["id"], updates)
    if not result:
        raise HTTPException(status_code=404, detail=MSG["not_found"])
    return {"success": True, "message": "Income source updated", "data": result}


@router.delete("/{source_id}")
async def delete_income_source(source_id: str, user: dict = Depends(get_current_user)):
    """Remove an income source"""
    success = await db_delete("income_sources", source_id, user["id"])
    if not success:
        raise HTTPException(status_code=404, detail=MSG["not_found"])
    return {"success": True, "message": "Income source removed"}


def _to_monthly(amount: float, frequency: str) -> float:
    """Convert any frequency to monthly equivalent"""
    freq_map = {
        "Monthly":   amount,
        "Weekly":    amount * 52 / 12,
        "Annual":    amount / 12,
        "One-time":  0,
        "Quarterly": amount / 3,
        "Daily":     amount * 365 / 12,
    }
    return round(freq_map.get(frequency, amount), 2)
