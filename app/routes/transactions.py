# FinRight AI — Transaction Routes
# Handles: list, create, update, delete transactions

from fastapi import APIRouter, Depends, HTTPException, Query
from app.schema import TransactionCreate, TransactionUpdate, MessageResponse
from app.database import db_fetch_all, db_insert, db_update, db_delete
from app.security import get_current_user
from app.constants import MSG
from datetime import date
from typing import Optional
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("/")
async def list_transactions(
    type: Optional[str] = Query(None, description="Filter by type"),
    category: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, le=500),
    user: dict = Depends(get_current_user)
):
    """
    Get all transactions for the logged-in user.
    Supports filtering by type, category, date range, and search.
    """
    txns = await db_fetch_all("transactions", user["id"])

    # Apply filters
    if type:
        txns = [t for t in txns if t.get("type") == type]
    if category:
        txns = [t for t in txns if t.get("category") == category]
    if date_from:
        txns = [t for t in txns if t.get("date", "") >= str(date_from)]
    if date_to:
        txns = [t for t in txns if t.get("date", "") <= str(date_to)]
    if search:
        s = search.lower()
        txns = [t for t in txns if
            s in (t.get("sub_category") or "").lower() or
            s in (t.get("note") or "").lower() or
            s in (t.get("category") or "").lower()
        ]

    # Sort newest first
    txns.sort(key=lambda t: t.get("date", ""), reverse=True)

    # Paginate
    total = len(txns)
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "items": txns[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_more": end < total
    }


@router.post("/", response_model=MessageResponse, status_code=201)
async def create_transaction(
    data: TransactionCreate,
    user: dict = Depends(get_current_user)
):
    """Save a new transaction"""
    row = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "type": data.type,
        "category": data.category,
        "sub_category": data.sub_category,
        "amount": data.amount,
        "orig_amount": data.orig_amount or data.amount,
        "orig_currency": data.orig_currency,
        "account": data.account,
        "date": str(data.date),
        "note": data.note or "",
        "is_recurring": data.is_recurring
    }

    result = await db_insert("transactions", row)
    if not result:
        raise HTTPException(status_code=500, detail=MSG["server_error"])

    return MessageResponse(
        success=True,
        message=MSG["txn_created"],
        data=result
    )


@router.put("/{txn_id}", response_model=MessageResponse)
async def update_transaction(
    txn_id: str,
    data: TransactionUpdate,
    user: dict = Depends(get_current_user)
):
    """Update an existing transaction"""
    updates = data.model_dump(exclude_none=True)
    if "date" in updates:
        updates["date"] = str(updates["date"])

    result = await db_update("transactions", txn_id, user["id"], updates)
    if not result:
        raise HTTPException(status_code=404, detail=MSG["not_found"])

    return MessageResponse(success=True, message="Transaction updated", data=result)


@router.delete("/{txn_id}", response_model=MessageResponse)
async def delete_transaction(
    txn_id: str,
    user: dict = Depends(get_current_user)
):
    """Delete a transaction"""
    success = await db_delete("transactions", txn_id, user["id"])
    if not success:
        raise HTTPException(status_code=404, detail=MSG["not_found"])

    return MessageResponse(success=True, message=MSG["txn_deleted"])


@router.post("/bulk", response_model=MessageResponse)
async def bulk_import(
    transactions: list[TransactionCreate],
    user: dict = Depends(get_current_user)
):
    """Import multiple transactions at once (bulk upload)"""
    if not transactions:
        raise HTTPException(status_code=400, detail="No transactions provided")

    saved = 0
    errors = []

    for i, txn in enumerate(transactions):
        row = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "type": txn.type,
            "category": txn.category,
            "sub_category": txn.sub_category,
            "amount": txn.amount,
            "orig_amount": txn.orig_amount or txn.amount,
            "orig_currency": txn.orig_currency,
            "account": txn.account,
            "date": str(txn.date),
            "note": txn.note or "",
            "is_recurring": txn.is_recurring
        }
        result = await db_insert("transactions", row)
        if result:
            saved += 1
        else:
            errors.append(f"Row {i+1} failed")

    return MessageResponse(
        success=True,
        message=f"Imported {saved} of {len(transactions)} transactions",
        data={"saved": saved, "errors": errors}
    )
