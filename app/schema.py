# ============================================================
# FinRight AI — app/schema.py
#
# Data models for API requests and responses.
# Pydantic validates automatically — wrong data = clear error.
#
# XxxCreate   = fields needed to CREATE a record
# XxxUpdate   = fields to UPDATE (all optional)
# XxxResponse = what we send BACK to the client
# ============================================================

from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import date, datetime


# ── Auth ──────────────────────────────────────────────────

class SignUpRequest(BaseModel):
    full_name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class ForgotPasswordRequest(BaseModel):
    email: str


# ── Transactions ──────────────────────────────────────────

class TransactionCreate(BaseModel):
    type: str                            # Income|Expenses|Assets|Liabilities
    category: str                        # e.g. Variable, Fixed, Liquid
    sub_category: str                    # e.g. Food, Rent, Cash
    amount: float
    orig_amount: Optional[float] = None  # Original if foreign currency
    orig_currency: str = "NPR"
    account: Optional[str] = None
    date: date
    note: Optional[str] = None
    is_recurring: bool = False

    @field_validator("amount")
    def must_be_positive(cls, v):
        if v <= 0: raise ValueError("Amount must be > 0")
        return v

class TransactionUpdate(BaseModel):
    type: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    amount: Optional[float] = None
    account: Optional[str] = None
    date: Optional[date] = None
    note: Optional[str] = None


# ── Goals ─────────────────────────────────────────────────

class GoalCreate(BaseModel):
    name: str
    icon: str = "🎯"
    target: float
    saved: float = 0
    currency: str = "NPR"
    deadline: Optional[date] = None
    priority: str = "Medium"
    goal_type: Optional[str] = None
    linked_account: Optional[str] = None

class GoalUpdate(BaseModel):
    name: Optional[str] = None
    target: Optional[float] = None
    saved: Optional[float] = None
    deadline: Optional[date] = None
    priority: Optional[str] = None
    linked_account: Optional[str] = None


# ── Budgets ───────────────────────────────────────────────

class BudgetCreate(BaseModel):
    category: str
    limit_amount: float
    currency: str = "NPR"
    month: Optional[str] = None

    @field_validator("limit_amount")
    def must_be_positive(cls, v):
        if v <= 0: raise ValueError("Limit must be > 0")
        return v


# ── Accounts ──────────────────────────────────────────────

class AccountCreate(BaseModel):
    name: str
    type: str = "Bank Account"
    color: str = "#1a6ba0"
    balance: float = 0
    note: Optional[str] = None


# ── Profile ───────────────────────────────────────────────

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    currency: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    marital_status: Optional[str] = None
    housing: Optional[str] = None
    rent: Optional[float] = None
    transport: Optional[str] = None
    transport_cost: Optional[float] = None
    loan_emi: Optional[float] = None
    onboarded: Optional[bool] = None


# ── Taxonomy ──────────────────────────────────────────────

class TaxonomyCreate(BaseModel):
    type: str
    category: str
    sub_category: str
    is_recurring: bool = False


# ── Generic ───────────────────────────────────────────────

class MessageResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
