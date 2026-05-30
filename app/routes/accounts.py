# FinRight AI — Accounts Routes
# Bank accounts, digital wallets, cash — manage and track balances

from fastapi import APIRouter, Depends, HTTPException
from app.schema import AccountCreate, MessageResponse
from app.database import db_fetch_all, db_insert, db_update, db_delete
from app.security import get_current_user
from app.constants import MSG, DEFAULT_ACCOUNTS
import uuid

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.get("/")
async def list_accounts(user: dict = Depends(get_current_user)):
    """
    Get all accounts with calculated balances from transactions.
    Shows real-time balance based on actual transaction history.
    """
    uid = user["id"]
    accounts = await db_fetch_all("accounts", uid)
    txns = await db_fetch_all("transactions", uid)

    # Calculate real balance per account from transactions
    from collections import defaultdict
    tx_balance: dict = defaultdict(float)
    for t in txns:
        acc = t.get("account") or ""
        if t["type"] in ("Income", "Assets"):
            tx_balance[acc] += t["amount"]
        elif t["type"] in ("Expenses", "Liabilities"):
            tx_balance[acc] -= t["amount"]

    # Merge with account records
    result = []
    for acc in accounts:
        name = acc["name"]
        tx_bal = tx_balance.get(name, 0)
        result.append({
            **acc,
            "transaction_balance": round(tx_bal, 2),
            "display_balance": acc.get("balance") or round(tx_bal, 2),
        })

    total = sum(a["display_balance"] for a in result)

    return {
        "accounts": sorted(result, key=lambda x: -x["display_balance"]),
        "total_balance": round(total, 2),
        "count": len(result),
    }


@router.post("/", response_model=MessageResponse, status_code=201)
async def create_account(data: AccountCreate, user: dict = Depends(get_current_user)):
    """Create a new account"""
    # Check duplicate name
    existing = await db_fetch_all("accounts", user["id"])
    if any(a["name"].lower() == data.name.lower() for a in existing):
        raise HTTPException(status_code=400, detail="Account with this name already exists")

    row = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "name": data.name,
        "type": data.type,
        "color": data.color,
        "balance": data.balance,
        "note": data.note or "",
        "is_default": False,
    }
    result = await db_insert("accounts", row)
    if not result:
        raise HTTPException(status_code=500, detail=MSG["server_error"])
    return MessageResponse(success=True, message="Account created", data=result)


@router.put("/{account_id}", response_model=MessageResponse)
async def update_account(
    account_id: str,
    data: AccountCreate,
    user: dict = Depends(get_current_user)
):
    """Update account details"""
    updates = {
        "name": data.name,
        "type": data.type,
        "color": data.color,
        "balance": data.balance,
        "note": data.note or "",
    }
    result = await db_update("accounts", account_id, user["id"], updates)
    if not result:
        raise HTTPException(status_code=404, detail=MSG["not_found"])
    return MessageResponse(success=True, message="Account updated", data=result)


@router.patch("/{account_id}/balance")
async def set_balance(
    account_id: str,
    balance: float,
    user: dict = Depends(get_current_user)
):
    """Manually set an account balance"""
    result = await db_update("accounts", account_id, user["id"], {"balance": balance})
    if not result:
        raise HTTPException(status_code=404, detail=MSG["not_found"])
    return {"success": True, "message": "Balance updated", "balance": balance}


@router.delete("/{account_id}", response_model=MessageResponse)
async def delete_account(account_id: str, user: dict = Depends(get_current_user)):
    """Delete an account"""
    accounts = await db_fetch_all("accounts", user["id"])
    account = next((a for a in accounts if a["id"] == account_id), None)

    if not account:
        raise HTTPException(status_code=404, detail=MSG["not_found"])
    if account.get("is_default"):
        raise HTTPException(status_code=400, detail="Cannot delete default accounts")

    await db_delete("accounts", account_id, user["id"])
    return MessageResponse(success=True, message="Account deleted")
