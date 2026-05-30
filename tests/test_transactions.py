# FinRight AI — Tests
# Run with: pytest tests/

from app.services.analytics import (
    calculate_net_worth,
    calculate_period_summary,
    calculate_category_breakdown,
    calculate_goal_progress
)
from app.security import validate_password_strength


# ── Sample test data ─────────────────────────────────────────
SAMPLE_TRANSACTIONS = [
    {"type": "Income",      "amount": 179859, "date": "2025-01-01", "category": "Income",   "sub_category": "Salary / Bonus"},
    {"type": "Expenses",    "amount": 15000,  "date": "2025-01-05", "category": "Variable", "sub_category": "Food"},
    {"type": "Expenses",    "amount": 5000,   "date": "2025-01-10", "category": "Variable", "sub_category": "Transport"},
    {"type": "Assets",      "amount": 100000, "date": "2025-01-15", "category": "Liquid",   "sub_category": "Savings account"},
    {"type": "Liabilities", "amount": 50000,  "date": "2025-01-01", "category": "Liabilities", "sub_category": "Personal loans"},
]

SAMPLE_GOALS = [
    {"id": "1", "name": "Bangkok Trip", "target": 50000, "saved": 25000, "deadline": "2025-12-01"},
    {"id": "2", "name": "Emergency Fund", "target": 300000, "saved": 300000, "deadline": None},
]


# ── Net Worth Tests ──────────────────────────────────────────
def test_net_worth_calculation():
    result = calculate_net_worth(SAMPLE_TRANSACTIONS)
    assert result["total_assets"] == 100000
    assert result["total_liabilities"] == 50000
    assert result["net_worth"] == 50000
    print("✓ Net worth calculation correct")


def test_net_worth_no_transactions():
    result = calculate_net_worth([])
    assert result["net_worth"] == 0
    print("✓ Net worth with no data returns 0")


# ── Period Summary Tests ─────────────────────────────────────
def test_period_summary():
    result = calculate_period_summary(SAMPLE_TRANSACTIONS)
    assert result["income"] == 179859
    assert result["expenses"] == 20000
    assert result["savings"] == 159859
    print(f"✓ Period summary: income={result['income']}, savings_rate={result['savings_rate']}%")


def test_period_summary_with_date_filter():
    result = calculate_period_summary(
        SAMPLE_TRANSACTIONS,
        date_from="2025-01-05",
        date_to="2025-01-10"
    )
    assert result["income"] == 0
    assert result["expenses"] == 20000
    print("✓ Date filter working correctly")


# ── Category Breakdown Tests ─────────────────────────────────
def test_category_breakdown():
    result = calculate_category_breakdown(SAMPLE_TRANSACTIONS, "Expenses")
    assert len(result) == 2
    assert result[0]["category"] == "Food"      # Highest expense
    assert result[0]["amount"] == 15000
    assert result[0]["percentage"] == 75.0
    print(f"✓ Category breakdown: {result}")


# ── Goal Progress Tests ──────────────────────────────────────
def test_goal_progress():
    result = calculate_goal_progress(SAMPLE_GOALS)
    bangkok = next(g for g in result if g["name"] == "Bangkok Trip")
    emergency = next(g for g in result if g["name"] == "Emergency Fund")

    assert bangkok["progress_pct"] == 50.0
    assert not bangkok["is_complete"]
    assert emergency["is_complete"]
    print(f"✓ Goal progress: Bangkok={bangkok['progress_pct']}%, Emergency={emergency['is_complete']}")


# ── Password Validation Tests ────────────────────────────────
def test_password_too_short():
    ok, msg = validate_password_strength("Abc1!")
    assert not ok
    assert "8 characters" in msg
    print(f"✓ Short password rejected: {msg}")


def test_password_no_uppercase():
    ok, msg = validate_password_strength("password123!")
    assert not ok
    assert "uppercase" in msg
    print(f"✓ No uppercase rejected: {msg}")


def test_password_valid():
    ok, msg = validate_password_strength("FinRight@2025")
    assert ok
    assert msg == ""
    print("✓ Strong password accepted")


# ── Run all tests ────────────────────────────────────────────
if __name__ == "__main__":
    print("\n── Running FinRight AI Tests ──\n")
    test_net_worth_calculation()
    test_net_worth_no_transactions()
    test_period_summary()
    test_period_summary_with_date_filter()
    test_category_breakdown()
    test_goal_progress()
    test_password_too_short()
    test_password_no_uppercase()
    test_password_valid()
    print("\n✅ All tests passed!\n")
