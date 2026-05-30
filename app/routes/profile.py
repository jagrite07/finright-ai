# FinRight AI — Profile Routes
# User profile, onboarding data, personal settings

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.database import db_fetch_all, db_upsert
from app.security import get_current_user
from app.constants import MSG

router = APIRouter(prefix="/profile", tags=["Profile"])


class ProfileUpdateFull(BaseModel):
    full_name: Optional[str] = None
    currency: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    partner_name: Optional[str] = None
    partner_income: Optional[float] = None
    housing: Optional[str] = None
    rent: Optional[float] = None
    transport: Optional[str] = None
    transport_cost: Optional[float] = None
    electricity: Optional[float] = None
    internet: Optional[float] = None
    gym: Optional[float] = None
    insurance: Optional[float] = None
    loan_emi: Optional[float] = None
    loans: Optional[list] = None
    financial_goals: Optional[list] = None
    onboarded: Optional[bool] = None


@router.get("/")
async def get_profile(user: dict = Depends(get_current_user)):
    """Get the current user's full profile"""
    uid = user["id"]
    profiles = await db_fetch_all("profiles", uid)

    if not profiles:
        # Return empty profile if not set up yet
        return {
            "id": uid,
            "email": user.get("email"),
            "full_name": user.get("full_name", ""),
            "currency": "NPR",
            "country": "Nepal",
            "onboarded": False,
        }

    prof = profiles[0]
    prof["email"] = user.get("email")

    # Calculate total fixed monthly expenses
    fixed_monthly = sum([
        prof.get("rent") or 0,
        prof.get("electricity") or 0,
        prof.get("internet") or 0,
        prof.get("gym") or 0,
        prof.get("insurance") or 0,
        prof.get("loan_emi") or 0,
        prof.get("transport_cost") or 0,
    ])
    prof["total_fixed_monthly"] = fixed_monthly

    return prof


@router.put("/")
async def update_profile(
    data: ProfileUpdateFull,
    user: dict = Depends(get_current_user)
):
    """Update profile — partial updates supported"""
    updates = data.model_dump(exclude_none=True)
    updates["id"] = user["id"]

    result = await db_upsert("profiles", updates)
    if not result:
        raise HTTPException(status_code=500, detail=MSG["server_error"])

    return {"success": True, "message": MSG["profile_updated"], "data": result}


@router.get("/fixed-expenses")
async def get_fixed_expenses(user: dict = Depends(get_current_user)):
    """
    Get all monthly fixed expenses from profile.
    Used for the budget baseline and cash flow analysis.
    """
    profiles = await db_fetch_all("profiles", user["id"])
    if not profiles:
        return {"fixed_expenses": [], "total": 0}

    prof = profiles[0]
    expenses = [
        {"name": "Rent / Housing",    "amount": prof.get("rent") or 0,           "icon": "🏠"},
        {"name": "Electricity",       "amount": prof.get("electricity") or 0,     "icon": "⚡"},
        {"name": "Internet",          "amount": prof.get("internet") or 0,        "icon": "📶"},
        {"name": "Gym",               "amount": prof.get("gym") or 0,             "icon": "💪"},
        {"name": "Insurance",         "amount": prof.get("insurance") or 0,       "icon": "🛡"},
        {"name": "Loan EMI",          "amount": prof.get("loan_emi") or 0,        "icon": "🏦"},
        {"name": "Transport",         "amount": prof.get("transport_cost") or 0,  "icon": "🚗"},
    ]

    # Only include non-zero expenses
    active = [e for e in expenses if e["amount"] > 0]
    total = sum(e["amount"] for e in active)

    return {
        "fixed_expenses": active,
        "total": total,
        "currency": prof.get("currency", "NPR"),
    }


@router.patch("/onboarding-complete")
async def mark_onboarded(user: dict = Depends(get_current_user)):
    """Mark user as having completed onboarding"""
    result = await db_upsert("profiles", {"id": user["id"], "onboarded": True})
    return {"success": True, "message": "Onboarding complete", "data": result}
