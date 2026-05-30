# FinRight AI — Goals Routes
# Savings goals: create, update, track progress, delete

from fastapi import APIRouter, Depends, HTTPException
from app.schema import GoalCreate, GoalUpdate, MessageResponse
from app.database import db_fetch_all, db_insert, db_update, db_delete
from app.security import get_current_user
from app.services.analytics import calculate_goal_progress
from app.constants import MSG
import uuid

router = APIRouter(prefix="/goals", tags=["Goals"])


@router.get("/")
async def list_goals(user: dict = Depends(get_current_user)):
    """Get all goals with progress calculated"""
    goals = await db_fetch_all("goals", user["id"])
    return {"goals": calculate_goal_progress(goals), "total": len(goals)}


@router.get("/{goal_id}")
async def get_goal(goal_id: str, user: dict = Depends(get_current_user)):
    """Get a single goal by ID"""
    goals = await db_fetch_all("goals", user["id"])
    goal = next((g for g in goals if g["id"] == goal_id), None)
    if not goal:
        raise HTTPException(status_code=404, detail=MSG["not_found"])
    return calculate_goal_progress([goal])[0]


@router.post("/", response_model=MessageResponse, status_code=201)
async def create_goal(data: GoalCreate, user: dict = Depends(get_current_user)):
    """Create a new savings goal"""
    row = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "name": data.name,
        "icon": data.icon,
        "target": data.target,
        "saved": data.saved,
        "currency": data.currency,
        "deadline": str(data.deadline) if data.deadline else None,
        "priority": data.priority,
        "goal_type": data.goal_type,
        "linked_account": data.linked_account,
        "monthly_saving": 0,
    }
    result = await db_insert("goals", row)
    if not result:
        raise HTTPException(status_code=500, detail=MSG["server_error"])
    return MessageResponse(success=True, message=MSG["goal_created"], data=result)


@router.put("/{goal_id}", response_model=MessageResponse)
async def update_goal(
    goal_id: str,
    data: GoalUpdate,
    user: dict = Depends(get_current_user)
):
    """Update goal details"""
    updates = data.model_dump(exclude_none=True)
    if "deadline" in updates and updates["deadline"]:
        updates["deadline"] = str(updates["deadline"])

    result = await db_update("goals", goal_id, user["id"], updates)
    if not result:
        raise HTTPException(status_code=404, detail=MSG["not_found"])
    return MessageResponse(success=True, message=MSG["goal_updated"], data=result)


@router.patch("/{goal_id}/savings", response_model=MessageResponse)
async def update_savings(
    goal_id: str,
    amount: float,
    user: dict = Depends(get_current_user)
):
    """
    Update the saved amount for a goal.
    Used when user manually adds savings to a goal.
    """
    if amount < 0:
        raise HTTPException(status_code=400, detail="Amount cannot be negative")

    result = await db_update("goals", goal_id, user["id"], {"saved": amount})
    if not result:
        raise HTTPException(status_code=404, detail=MSG["not_found"])
    return MessageResponse(
        success=True,
        message=f"Goal savings updated to {amount}",
        data=result
    )


@router.delete("/{goal_id}", response_model=MessageResponse)
async def delete_goal(goal_id: str, user: dict = Depends(get_current_user)):
    """Delete a goal"""
    success = await db_delete("goals", goal_id, user["id"])
    if not success:
        raise HTTPException(status_code=404, detail=MSG["not_found"])
    return MessageResponse(success=True, message="Goal deleted")
