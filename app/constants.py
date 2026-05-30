# ============================================================
# FinRight AI — app/constants.py
#
# All fixed values used across the app.
# Change here → updates everywhere.
# ============================================================

# Transaction types (the 4 core types)
TRANSACTION_TYPES = ["Income", "Expenses", "Assets", "Liabilities"]

# Supported currencies
SUPPORTED_CURRENCIES = [
    "NPR", "USD", "EUR", "GBP", "AUD", "CAD",
    "INR", "SGD", "AED", "JPY", "CNY", "THB",
]
HOME_CURRENCY_DEFAULT = "NPR"

# Goal types
GOAL_TYPES = [
    "Travel", "Marriage", "Emergency Fund",
    "Health", "Gym", "Home", "Education", "Other"
]
GOAL_PRIORITIES = ["Low", "Medium", "High"]

# Password rules
PASSWORD_MIN_LENGTH = 8

# Login security
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_SECONDS = 30

# Pagination
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 500

# Default categories — auto-created for every new user
DEFAULT_TAXONOMY = [
    {"type": "Assets", "category": "Liquid",          "sub_category": "Cash"},
    {"type": "Assets", "category": "Liquid",          "sub_category": "Savings account"},
    {"type": "Assets", "category": "Liquid",          "sub_category": "Digital wallet balances"},
    {"type": "Assets", "category": "Liquid",          "sub_category": "Fixed Deposit"},
    {"type": "Assets", "category": "Investments",     "sub_category": "Mutual funds"},
    {"type": "Assets", "category": "Investments",     "sub_category": "Stocks"},
    {"type": "Assets", "category": "Investments",     "sub_category": "Bonds"},
    {"type": "Assets", "category": "Physical Assets", "sub_category": "Property"},
    {"type": "Assets", "category": "Physical Assets", "sub_category": "Gold"},
    {"type": "Assets", "category": "Physical Assets", "sub_category": "Vehicle"},
    {"type": "Liabilities", "category": "Liabilities", "sub_category": "Personal loans"},
    {"type": "Liabilities", "category": "Liabilities", "sub_category": "Credit card dues"},
    {"type": "Liabilities", "category": "Liabilities", "sub_category": "Vehicle loan"},
    {"type": "Liabilities", "category": "Liabilities", "sub_category": "Education loan"},
    {"type": "Income", "category": "Income", "sub_category": "Salary / Bonus"},
    {"type": "Income", "category": "Income", "sub_category": "Business income"},
    {"type": "Income", "category": "Income", "sub_category": "Rental income"},
    {"type": "Income", "category": "Income", "sub_category": "Investment income"},
    {"type": "Income", "category": "Income", "sub_category": "Interest (Bank)"},
    {"type": "Expenses", "category": "Fixed",         "sub_category": "Rent"},
    {"type": "Expenses", "category": "Fixed",         "sub_category": "Insurance"},
    {"type": "Expenses", "category": "Fixed",         "sub_category": "EMI / Loan Repayment"},
    {"type": "Expenses", "category": "Variable",      "sub_category": "Food"},
    {"type": "Expenses", "category": "Variable",      "sub_category": "Transport"},
    {"type": "Expenses", "category": "Variable",      "sub_category": "Health & Medicine"},
    {"type": "Expenses", "category": "Variable",      "sub_category": "Shopping"},
    {"type": "Expenses", "category": "Discretionary", "sub_category": "Travel"},
    {"type": "Expenses", "category": "Discretionary", "sub_category": "Entertainment"},
    {"type": "Expenses", "category": "Discretionary", "sub_category": "Other"},
]

# Default accounts — auto-created for every new user
DEFAULT_ACCOUNTS = [
    {"name": "eSewa",        "type": "Digital Wallet", "color": "#22c97a"},
    {"name": "Khalti",       "type": "Digital Wallet", "color": "#9b94ff"},
    {"name": "Bank Account", "type": "Bank Account",   "color": "#1a9cc8"},
    {"name": "Cash",         "type": "Cash",           "color": "#ffb347"},
]

# Budget status thresholds
BUDGET_STATUS = {
    "on_track":    {"threshold": 0.70, "color": "#22c97a"},
    "caution":     {"threshold": 0.90, "color": "#ffb347"},
    "over_budget": {"threshold": 1.00, "color": "#ff5e7a"},
}

# Standard API response messages
MSG = {
    "login_success":       "Logged in successfully",
    "logout_success":      "Logged out successfully",
    "signup_success":      "Account created — check your email to confirm",
    "invalid_credentials": "Invalid username or password",
    "account_locked":      "Too many attempts — try again in 30 seconds",
    "txn_created":         "Transaction saved",
    "txn_deleted":         "Transaction deleted",
    "goal_created":        "Goal created",
    "goal_updated":        "Goal updated",
    "budget_saved":        "Budget limit set",
    "profile_updated":     "Profile updated",
    "not_found":           "Record not found",
    "unauthorized":        "Please log in to continue",
    "forbidden":           "You don't have permission to do this",
    "server_error":        "Something went wrong — please try again",
}
