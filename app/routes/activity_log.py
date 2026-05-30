# FinRight AI — Activity Log Routes
# Tracks everything the user does: added transaction, created goal, etc.

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional
from app.database import db_fetch_all, db_insert
from app.security import get_current_user
import uuid

router = APIRouter(prefix="/activity", tags=["Activity Log"])


class ActivityCreate(BaseModel):
    action: str          # e.g. "added_transaction", "created_goal"
    description: str     # Human readable: "Added Rs.5,000 expense — Food"
    amount: Optional[float] = None
    category: Optional[str] = None
    icon: Optional[str] = None


@router.get("/")
async def get_activity_log(
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    user: dict = Depends(get_current_user)
):
    """
    Get recent activity log entries.
    Shows latest actions first.
    """
    logs = await db_fetch_all("activity_log", user["id"])

    # Sort newest first
    logs.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    # Paginate
    total = len(logs)
    paginated = logs[offset: offset + limit]

    return {
        "logs": paginated,
        "total": total,
        "has_more": offset + limit < total,
    }


@router.post("/")
async def log_activity(data: ActivityCreate, user: dict = Depends(get_current_user)):
    """
    Log a user action.
    Called automatically when transactions, goals, etc. are created.
    """
    row = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "action": data.action,
        "description": data.description,
        "amount": data.amount,
        "category": data.category,
        "icon": data.icon or _get_default_icon(data.action),
    }
    result = await db_insert("activity_log", row)
    return {"success": True, "data": result}


@router.delete("/clear")
async def clear_activity_log(user: dict = Depends(get_current_user)):
    """Clear all activity log entries for the user"""
    from app.database import get_db
    db = get_db()
    db.table("activity_log").delete().eq("user_id", user["id"]).execute()
    return {"success": True, "message": "Activity log cleared"}


def _get_default_icon(action: str) -> str:
    """Map action name to an emoji icon"""
    icons = {
        "added_transaction":  "💰",
        "deleted_transaction": "🗑",
        "created_goal":       "🎯",
        "updated_goal":       "✏️",
        "deleted_goal":       "🗑",
        "set_budget":         "📊",
        "added_account":      "🏦",
        "updated_profile":    "👤",
        "bulk_import":        "📥",
        "added_income":       "💵",
    }
    return icons.get(action, "📝")
