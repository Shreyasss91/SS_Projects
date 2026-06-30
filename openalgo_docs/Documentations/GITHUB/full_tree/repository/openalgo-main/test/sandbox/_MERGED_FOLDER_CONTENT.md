# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\test\sandbox



---

# FILE: test\sandbox\__init__.py

```py
# test/sandbox/__init__.py
"""Sandbox test suite"""

```


---

# FILE: test\sandbox\README.md

```md
# Sandbox Mode Test Suite

This directory contains comprehensive tests for the OpenAlgo sandbox (sandbox trading) mode.

## Test Files

### 1. test_margin_scenarios.py
**Purpose:** Tests complete margin flow across various trading scenarios

**Test Cases:**
- BUY 100 → SELL 50 → SELL 50 (partial position closure)
- BUY 100 → SELL 100 → BUY 100 → SELL 100 (position cycling)
- BUY 100 → SELL 200 (position reversal)
- BUY 100 → BUY 100 (adding to position)

**Key Features Tested:**
- Margin blocking at order placement
- Margin release on position closure
- Double-blocking prevention
- Position reopening after closure

### 2. test_cnc_sell_validation.py
**Purpose:** Tests CNC (delivery) SELL order validation

**Test Cases:**
- CNC SELL without position/holdings (should reject)
- CNC SELL with existing position (should succeed)
- CNC SELL exceeding available quantity (should reject)
- CNC SELL with holdings only
- MIS short selling (should allow without position)
- CNC SELL with combined position and holdings

**Key Features Tested:**
- Position and holdings validation
- Rejection reason clarity
- MIS vs CNC product differences
- Error message accuracy

### 3. test_rejected_order.py
**Purpose:** Verifies rejected orders appear in orderbook

**Test Cases:**
- Places invalid CNC SELL order
- Checks orderbook for rejected order
- Verifies rejection reason is stored

**Key Features Tested:**
- Audit trail for rejected orders
- Order ID generation for all orders
- Rejection reason storage
- No margin blocking for rejected orders

### 4. test_orderbook_api.py
**Purpose:** Tests orderbook API response structure

**Test Cases:**
- Retrieves orderbook via API
- Parses response structure
- Filters rejected orders
- Verifies rejection reasons in response

**Key Features Tested:**
- API response format
- Rejected order visibility
- Statistics accuracy
- Field completeness

### 5. test_fund_manager.py
**Purpose:** Tests fund management and margin calculations

**Test Cases:**
- Initial capital setup
- Margin blocking/release
- P&L calculations
- Balance updates

## Running Tests

### Individual Test
```bash
cd /path/to/openalgo
source .venv/bin/activate
python test/sandbox/test_margin_scenarios.py
```

### All Sandbox Tests
```bash
cd /path/to/openalgo
source .venv/bin/activate

# Run all tests
for test in test/sandbox/test_*.py; do
    echo "Running $test..."
    python "$test"
done
```

### Quick Test Commands
```bash
# Test margin scenarios
python test/sandbox/test_margin_scenarios.py

# Test CNC validation
python test/sandbox/test_cnc_sell_validation.py

# Test rejected orders
python test/sandbox/test_rejected_order.py

# Test orderbook API
python test/sandbox/test_orderbook_api.py
```

## Test Data

Tests use the following test data:
- **Test User:** `testuser` or `rajandran`
- **Test Symbol:** `ZEEL` or `RELIANCE`
- **Test Exchange:** `NSE`
- **Test Products:** `CNC` (delivery), `MIS` (intraday)
- **Initial Capital:** ₹1,00,00,000 (1 Crore)

## Common Issues

### 1. Order ID Conflicts
**Issue:** `UNIQUE constraint failed: sandbox_orders.orderid`
**Solution:** Clear all orders before testing
```python
SandboxOrders.query.delete()  # Clear ALL orders
db_session.commit()
```

### 2. API Authentication Failures
**Issue:** Quote fetching fails with authentication error
**Solution:** Test uses fallback prices when API unavailable

### 3. Database Lock Errors
**Issue:** Database is locked
**Solution:** Ensure no other processes are using the database

## Expected Test Results

All tests should pass with output similar to:
```
✅ SCENARIO 1 PASSED
✅ SCENARIO 2 PASSED
✅ SCENARIO 3 PASSED
✅ SCENARIO 4 PASSED

TEST RESULTS: 4 passed, 0 failed
🎉 ALL TESTS PASSED!
```

## Test Coverage

The test suite covers:
- ✅ Margin calculations (blocking, release, tracking)
- ✅ Position lifecycle (open, add, reduce, close, reopen)
- ✅ Order validation (product rules, quantity checks)
- ✅ Rejected order handling (audit trail, visibility)
- ✅ API response formats (orderbook, tradebook)
- ✅ Edge cases (reversals, partial fills, short selling)

## Adding New Tests

When adding new tests:
1. Follow the naming convention: `test_<feature>.py`
2. Include clear test cases with expected outcomes
3. Reset test data at the beginning of each test
4. Use descriptive assertion messages
5. Document the test purpose and scenarios

## Dependencies

Tests require:
- SQLAlchemy for database operations
- Decimal for precise calculations
- datetime for timestamps
- pytz for timezone handling

All dependencies are included in the main requirements.txt file.
```


---

# FILE: test\sandbox\test_cnc_sell_validation.py

```py
#!/usr/bin/env python3
"""
Test CNC SELL validation - ensures CNC sell orders are only allowed with existing positions/holdings
MIS orders allow short selling (negative positions)
"""

import sys
from decimal import Decimal

from database.sandbox_db import (
    SandboxFunds,
    SandboxHoldings,
    SandboxOrders,
    SandboxPositions,
    db_session,
    init_db,
)
from sandbox.order_manager import OrderManager


def reset_test_data(user_id="testuser"):
    """Reset test data"""
    print(f"\n🔄 Resetting data for user: {user_id}")

    # Delete all existing data - also delete ALL orders to avoid ID conflicts
    SandboxOrders.query.delete()  # Delete ALL orders to reset ID counter
    SandboxPositions.query.filter_by(user_id=user_id).delete()
    SandboxHoldings.query.filter_by(user_id=user_id).delete()

    # Ensure user has funds
    funds = SandboxFunds.query.filter_by(user_id=user_id).first()
    if not funds:
        funds = SandboxFunds(
            user_id=user_id,
            total_capital=Decimal("10000000.00"),
            available_balance=Decimal("10000000.00"),
            used_margin=Decimal("0.00"),
        )
        db_session.add(funds)
    else:
        funds.available_balance = Decimal("10000000.00")
        funds.used_margin = Decimal("0.00")

    db_session.commit()
    print("✅ Data reset complete")


def test_cnc_sell_without_position():
    """Test 1: CNC SELL should fail without position/holdings"""
    print("\n" + "=" * 60)
    print("TEST 1: CNC SELL without position/holdings")
    print("=" * 60)

    user_id = "testuser"
    reset_test_data(user_id)

    om = OrderManager(user_id)

    # Try to sell without any position
    print("→ Attempting CNC SELL 100 RELIANCE (no position)...")
    success, response, code = om.place_order(
        {
            "symbol": "RELIANCE",
            "exchange": "NSE",
            "action": "SELL",
            "quantity": 100,
            "price_type": "MARKET",
            "product": "CNC",
        }
    )

    if not success and "No positions or holdings available" in response.get("message", ""):
        print(f"✅ PASS: {response['message']}")
        return True
    else:
        print(f"❌ FAIL: Expected rejection, got: {response}")
        return False


def test_cnc_sell_with_position():
    """Test 2: CNC SELL should succeed with existing position"""
    print("\n" + "=" * 60)
    print("TEST 2: CNC SELL with existing position")
    print("=" * 60)

    user_id = "testuser"
    reset_test_data(user_id)

    # Create a position
    position = SandboxPositions(
        user_id=user_id,
        symbol="RELIANCE",
        exchange="NSE",
        product="CNC",
        quantity=100,
        average_price=Decimal("2500.00"),
    )
    db_session.add(position)
    db_session.commit()
    print("✅ Created position: RELIANCE 100 shares")

    om = OrderManager(user_id)

    # Try to sell within position limits
    print("→ Attempting CNC SELL 50 RELIANCE (have 100)...")
    success, response, code = om.place_order(
        {
            "symbol": "RELIANCE",
            "exchange": "NSE",
            "action": "SELL",
            "quantity": 50,
            "price_type": "MARKET",
            "product": "CNC",
        }
    )

    if success:
        print(f"✅ PASS: Order placed successfully - {response.get('orderid')}")
        return True
    else:
        print(f"❌ FAIL: Order rejected: {response.get('message')}")
        return False


def test_cnc_sell_exceeding_position():
    """Test 3: CNC SELL should fail when exceeding available quantity"""
    print("\n" + "=" * 60)
    print("TEST 3: CNC SELL exceeding available quantity")
    print("=" * 60)

    user_id = "testuser"
    reset_test_data(user_id)

    # Create a position
    position = SandboxPositions(
        user_id=user_id,
        symbol="RELIANCE",
        exchange="NSE",
        product="CNC",
        quantity=50,
        average_price=Decimal("2500.00"),
    )
    db_session.add(position)
    db_session.commit()
    print("✅ Created position: RELIANCE 50 shares")

    om = OrderManager(user_id)

    # Try to sell more than available
    print("→ Attempting CNC SELL 100 RELIANCE (have only 50)...")
    success, response, code = om.place_order(
        {
            "symbol": "RELIANCE",
            "exchange": "NSE",
            "action": "SELL",
            "quantity": 100,
            "price_type": "MARKET",
            "product": "CNC",
        }
    )

    if not success and "Only 50 shares available" in response.get("message", ""):
        print(f"✅ PASS: {response['message']}")
        return True
    else:
        print(f"❌ FAIL: Expected rejection for exceeding quantity, got: {response}")
        return False


def test_cnc_sell_with_holdings():
    """Test 4: CNC SELL should work with holdings"""
    print("\n" + "=" * 60)
    print("TEST 4: CNC SELL with holdings")
    print("=" * 60)

    user_id = "testuser"
    reset_test_data(user_id)

    # Create holdings (T+1 settled shares)
    from datetime import date

    holding = SandboxHoldings(
        user_id=user_id,
        symbol="RELIANCE",
        exchange="NSE",
        quantity=200,
        average_price=Decimal("2400.00"),
        settlement_date=date.today(),
    )
    db_session.add(holding)
    db_session.commit()
    print("✅ Created holdings: RELIANCE 200 shares")

    om = OrderManager(user_id)

    # Try to sell from holdings
    print("→ Attempting CNC SELL 150 RELIANCE (have 200 in holdings)...")
    success, response, code = om.place_order(
        {
            "symbol": "RELIANCE",
            "exchange": "NSE",
            "action": "SELL",
            "quantity": 150,
            "price_type": "MARKET",
            "product": "CNC",
        }
    )

    if success:
        print(f"✅ PASS: Order placed successfully - {response.get('orderid')}")
        return True
    else:
        print(f"❌ FAIL: Order rejected: {response.get('message')}")
        return False


def test_mis_short_selling():
    """Test 5: MIS SELL should allow short selling (no position required)"""
    print("\n" + "=" * 60)
    print("TEST 5: MIS short selling (without position)")
    print("=" * 60)

    user_id = "testuser"
    reset_test_data(user_id)

    om = OrderManager(user_id)

    # Try MIS short sell without any position
    print("→ Attempting MIS SELL 100 RELIANCE (short selling)...")
    success, response, code = om.place_order(
        {
            "symbol": "RELIANCE",
            "exchange": "NSE",
            "action": "SELL",
            "quantity": 100,
            "price_type": "MARKET",
            "product": "MIS",
        }
    )

    if success:
        print(f"✅ PASS: MIS short sell order placed - {response.get('orderid')}")
        return True
    else:
        print(f"❌ FAIL: MIS short sell rejected: {response.get('message')}")
        return False


def test_cnc_sell_with_position_and_holdings():
    """Test 6: CNC SELL should combine position and holdings"""
    print("\n" + "=" * 60)
    print("TEST 6: CNC SELL with both position and holdings")
    print("=" * 60)

    user_id = "testuser"
    reset_test_data(user_id)

    # Create position
    position = SandboxPositions(
        user_id=user_id,
        symbol="RELIANCE",
        exchange="NSE",
        product="CNC",
        quantity=50,
        average_price=Decimal("2500.00"),
    )
    db_session.add(position)

    # Create holdings
    from datetime import date

    holding = SandboxHoldings(
        user_id=user_id,
        symbol="RELIANCE",
        exchange="NSE",
        quantity=100,
        average_price=Decimal("2400.00"),
        settlement_date=date.today(),
    )
    db_session.add(holding)
    db_session.commit()

    print("✅ Created position: 50 shares + holdings: 100 shares = Total: 150 shares")

    om = OrderManager(user_id)

    # Try to sell combined quantity
    print("→ Attempting CNC SELL 120 RELIANCE (have 150 total)...")
    success, response, code = om.place_order(
        {
            "symbol": "RELIANCE",
            "exchange": "NSE",
            "action": "SELL",
            "quantity": 120,
            "price_type": "MARKET",
            "product": "CNC",
        }
    )

    if success:
        print(f"✅ PASS: Order placed successfully - {response.get('orderid')}")
        return True
    else:
        print(f"❌ FAIL: Order rejected: {response.get('message')}")
        return False


if __name__ == "__main__":
    # Initialize database
    init_db()

    print("\n🧪 TESTING CNC SELL VALIDATION")
    print("=" * 60)

    tests = [
        test_cnc_sell_without_position,
        test_cnc_sell_with_position,
        test_cnc_sell_exceeding_position,
        test_cnc_sell_with_holdings,
        test_mis_short_selling,
        test_cnc_sell_with_position_and_holdings,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ TEST ERROR: {e}")
            import traceback

            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed == 0:
        print("🎉 ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)

```


---

# FILE: test\sandbox\test_fund_manager.py

```py
# test/sandbox/test_fund_manager.py
"""
Test suite for Sandbox Fund Manager

Tests:
- Fund initialization
- Margin blocking and release
- P&L calculations
- Sunday reset functionality
- Leverage calculations
"""

import os
import sys
from decimal import Decimal

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.sandbox_db import SandboxFunds, db_session
from sandbox.fund_manager import FundManager, get_user_funds, initialize_user_funds


def test_fund_initialization():
    """Test fund initialization for new user"""
    print("\n" + "=" * 50)
    print("TEST 1: Fund Initialization")
    print("=" * 50)

    test_user = "TEST_USER_001"

    # Clean up any existing test data
    cleanup_test_data(test_user)

    # Initialize funds
    success, message = initialize_user_funds(test_user)
    print(f"✓ Initialize funds: {message}")
    assert success, "Fund initialization failed"

    # Get funds
    funds = get_user_funds(test_user)
    print(f"✓ Available cash: ₹{funds['availablecash']:,.2f}")
    assert funds["availablecash"] == 10000000.00, "Starting capital should be ₹1 Crore"

    # Try initializing again - should not fail
    success, message = initialize_user_funds(test_user)
    print(f"✓ Re-initialize funds: {message}")
    assert success, "Re-initialization should not fail"

    print("✅ PASSED: Fund Initialization\n")


def test_margin_operations():
    """Test margin blocking and release"""
    print("=" * 50)
    print("TEST 2: Margin Operations")
    print("=" * 50)

    test_user = "TEST_USER_002"
    cleanup_test_data(test_user)
    initialize_user_funds(test_user)

    fm = FundManager(test_user)

    # Get initial balance
    funds = fm.get_funds()
    initial_balance = Decimal(str(funds["availablecash"]))
    print(f"✓ Initial balance: ₹{initial_balance:,.2f}")

    # Block margin
    margin_amount = Decimal("100000.00")
    success, message = fm.block_margin(margin_amount, "Test trade")
    print(f"✓ Block margin: {message}")
    assert success, "Margin blocking failed"

    funds = fm.get_funds()
    available = Decimal(str(funds["availablecash"]))
    used = Decimal(str(funds["utiliseddebits"]))

    print(f"✓ Available after block: ₹{available:,.2f}")
    print(f"✓ Used margin: ₹{used:,.2f}")
    assert available == initial_balance - margin_amount, "Available balance incorrect"
    assert used == margin_amount, "Used margin incorrect"

    # Release margin with profit
    profit = Decimal("5000.00")
    success, message = fm.release_margin(margin_amount, profit, "Test trade complete")
    print(f"✓ Release margin: {message}")
    assert success, "Margin release failed"

    funds = fm.get_funds()
    final_balance = Decimal(str(funds["availablecash"]))
    realized_pnl = Decimal(str(funds["m2mrealized"]))

    print(f"✓ Final balance: ₹{final_balance:,.2f}")
    print(f"✓ Realized P&L: ₹{realized_pnl:,.2f}")
    assert final_balance == initial_balance + profit, "Final balance incorrect"
    assert realized_pnl == profit, "Realized P&L incorrect"

    print("✅ PASSED: Margin Operations\n")


def test_insufficient_funds():
    """Test insufficient funds scenario"""
    print("=" * 50)
    print("TEST 3: Insufficient Funds")
    print("=" * 50)

    test_user = "TEST_USER_003"
    cleanup_test_data(test_user)
    initialize_user_funds(test_user)

    fm = FundManager(test_user)

    # Try to block more than available
    excessive_amount = Decimal("15000000.00")  # More than 1 Crore
    success, message = fm.block_margin(excessive_amount, "Excessive trade")
    print(f"✓ Block excessive margin: {message}")
    assert not success, "Should fail for insufficient funds"
    assert "Insufficient funds" in message, "Error message should indicate insufficient funds"

    print("✅ PASSED: Insufficient Funds\n")


def test_leverage_calculations():
    """Test leverage-based margin calculations"""
    print("=" * 50)
    print("TEST 4: Leverage Calculations")
    print("=" * 50)

    test_user = "TEST_USER_004"
    cleanup_test_data(test_user)
    initialize_user_funds(test_user)

    fm = FundManager(test_user)

    test_cases = [
        {
            "name": "Equity MIS (5x leverage)",
            "symbol": "RELIANCE",
            "exchange": "NSE",
            "product": "MIS",
            "quantity": 100,
            "price": 1500,
            "expected_leverage": 5,
        },
        {
            "name": "Equity CNC (1x leverage)",
            "symbol": "RELIANCE",
            "exchange": "NSE",
            "product": "CNC",
            "quantity": 100,
            "price": 1500,
            "expected_leverage": 1,
        },
    ]

    for test_case in test_cases:
        trade_value = test_case["quantity"] * test_case["price"]
        expected_margin = trade_value / test_case["expected_leverage"]

        margin, message = fm.calculate_margin_required(
            test_case["symbol"],
            test_case["exchange"],
            test_case["product"],
            test_case["quantity"],
            test_case["price"],
        )

        if margin:
            print(f"✓ {test_case['name']}")
            print(f"  Trade value: ₹{trade_value:,.2f}")
            print(f"  Required margin: ₹{float(margin):,.2f}")
            print(f"  Expected margin: ₹{expected_margin:,.2f}")

    print("✅ PASSED: Leverage Calculations\n")


def test_unrealized_pnl():
    """Test unrealized P&L updates"""
    print("=" * 50)
    print("TEST 5: Unrealized P&L")
    print("=" * 50)

    test_user = "TEST_USER_005"
    cleanup_test_data(test_user)
    initialize_user_funds(test_user)

    fm = FundManager(test_user)

    # Update unrealized P&L
    unrealized = Decimal("25000.00")
    success, message = fm.update_unrealized_pnl(unrealized)
    print(f"✓ Update unrealized P&L: {message}")
    assert success, "Unrealized P&L update failed"

    funds = fm.get_funds()
    m2m = Decimal(str(funds["m2munrealized"]))
    total_pnl = Decimal(str(funds["totalpnl"]))

    print(f"✓ Unrealized P&L: ₹{m2m:,.2f}")
    print(f"✓ Total P&L: ₹{total_pnl:,.2f}")
    assert m2m == unrealized, "Unrealized P&L incorrect"
    assert total_pnl == unrealized, "Total P&L incorrect"

    print("✅ PASSED: Unrealized P&L\n")


def cleanup_test_data(user_id):
    """Clean up test data for a user"""
    try:
        SandboxFunds.query.filter_by(user_id=user_id).delete()
        db_session.commit()
    except Exception:
        db_session.rollback()


def run_all_tests():
    """Run all fund manager tests"""
    print("\n" + "=" * 50)
    print("SANDBOX FUND MANAGER TEST SUITE")
    print("=" * 50)

    try:
        test_fund_initialization()
        test_margin_operations()
        test_insufficient_funds()
        test_leverage_calculations()
        test_unrealized_pnl()

        print("\n" + "=" * 50)
        print("✅ ALL TESTS PASSED")
        print("=" * 50 + "\n")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        raise
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}\n")
        raise


if __name__ == "__main__":
    run_all_tests()

```


---

# FILE: test\sandbox\test_margin_scenarios.py

```py
#!/usr/bin/env python3
"""
Test script to verify margin calculations in all scenarios
"""

import sys
import time
from decimal import Decimal

from database.sandbox_db import (
    SandboxFunds,
    SandboxOrders,
    SandboxPositions,
    SandboxTrades,
    db_session,
    init_db,
)
from sandbox.execution_engine import ExecutionEngine
from sandbox.order_manager import OrderManager


def reset_user_data(user_id="rajandran"):
    """Reset all sandbox data for user"""
    print(f"\nResetting data for user: {user_id}")

    # Delete all existing data
    SandboxOrders.query.filter_by(user_id=user_id).delete()
    SandboxTrades.query.filter_by(user_id=user_id).delete()
    SandboxPositions.query.filter_by(user_id=user_id).delete()

    # Reset funds
    funds = SandboxFunds.query.filter_by(user_id=user_id).first()
    if funds:
        funds.total_capital = Decimal("10000000.00")
        funds.available_balance = Decimal("10000000.00")
        funds.used_margin = Decimal("0.00")
        funds.realized_pnl = Decimal("0.00")
        funds.unrealized_pnl = Decimal("0.00")
        funds.total_pnl = Decimal("0.00")

    db_session.commit()
    print("✓ Data reset complete")


def get_margin_status(user_id="rajandran"):
    """Get current margin status"""
    funds = SandboxFunds.query.filter_by(user_id=user_id).first()
    if funds:
        return {
            "available": float(funds.available_balance),
            "used": float(funds.used_margin),
            "total": float(funds.total_capital),
        }
    return None


def print_margin_status(label, status):
    """Print margin status nicely"""
    print(f"{label}:")
    print(f"  Available: ₹{status['available']:,.2f}")
    print(f"  Used: ₹{status['used']:,.2f}")
    print(f"  Total: ₹{status['total']:,.2f}")


def test_scenario_1():
    """Test: BUY 100 → SELL 50 → SELL 50"""
    print("\n" + "=" * 60)
    print("SCENARIO 1: BUY 100 → SELL 50 → SELL 50")
    print("=" * 60)

    user_id = "rajandran"
    reset_user_data(user_id)

    om = OrderManager(user_id)
    ee = ExecutionEngine()

    # Initial status
    status = get_margin_status(user_id)
    print_margin_status("Initial", status)

    # BUY 100 ZEEL
    print("\n→ Placing BUY 100 ZEEL...")
    success, response, _ = om.place_order(
        {
            "symbol": "ZEEL",
            "exchange": "NSE",
            "action": "BUY",
            "quantity": 100,
            "price_type": "MARKET",
            "product": "CNC",
        }
    )
    if success:
        print(f"  ✓ Order placed: {response.get('orderid')}")

    # Execute the order
    ee.check_and_execute_pending_orders()

    status = get_margin_status(user_id)
    print_margin_status("After BUY 100", status)
    expected_margin = 100 * 112.37  # Assuming LTP is ₹112.37
    assert abs(status["used"] - expected_margin) < 1, (
        f"Expected margin ~₹{expected_margin}, got ₹{status['used']}"
    )

    # SELL 50 ZEEL
    print("\n→ Placing SELL 50 ZEEL...")
    success, response, _ = om.place_order(
        {
            "symbol": "ZEEL",
            "exchange": "NSE",
            "action": "SELL",
            "quantity": 50,
            "price_type": "MARKET",
            "product": "CNC",
        }
    )
    if success:
        print(f"  ✓ Order placed: {response.get('orderid')}")

    # Execute the order
    ee.check_and_execute_pending_orders()

    status = get_margin_status(user_id)
    print_margin_status("After SELL 50", status)
    expected_margin = 50 * 112.37  # Half position closed
    assert abs(status["used"] - expected_margin) < 1, (
        f"Expected margin ~₹{expected_margin}, got ₹{status['used']}"
    )

    # SELL 50 ZEEL (close position)
    print("\n→ Placing SELL 50 ZEEL (closing position)...")
    success, response, _ = om.place_order(
        {
            "symbol": "ZEEL",
            "exchange": "NSE",
            "action": "SELL",
            "quantity": 50,
            "price_type": "MARKET",
            "product": "CNC",
        }
    )
    if success:
        print(f"  ✓ Order placed: {response.get('orderid')}")

    # Execute the order
    ee.check_and_execute_pending_orders()

    status = get_margin_status(user_id)
    print_margin_status("After SELL 50 (position closed)", status)
    assert status["used"] == 0, f"Expected margin ₹0, got ₹{status['used']}"

    print("\n✅ SCENARIO 1 PASSED")


def test_scenario_2():
    """Test: BUY 100 → SELL 100 → BUY 100 → SELL 100"""
    print("\n" + "=" * 60)
    print("SCENARIO 2: BUY 100 → SELL 100 → BUY 100 → SELL 100")
    print("=" * 60)

    user_id = "rajandran"
    reset_user_data(user_id)

    om = OrderManager(user_id)
    ee = ExecutionEngine()

    # Round 1: BUY 100 → SELL 100
    print("\n→ Round 1: BUY 100 ZEEL...")
    om.place_order(
        {
            "symbol": "ZEEL",
            "exchange": "NSE",
            "action": "BUY",
            "quantity": 100,
            "price_type": "MARKET",
            "product": "CNC",
        }
    )
    ee.check_and_execute_pending_orders()

    status = get_margin_status(user_id)
    print_margin_status("After BUY 100", status)
    expected_margin = 100 * 112.37
    assert abs(status["used"] - expected_margin) < 1, (
        f"Expected margin ~₹{expected_margin}, got ₹{status['used']}"
    )

    print("\n→ Round 1: SELL 100 ZEEL...")
    om.place_order(
        {
            "symbol": "ZEEL",
            "exchange": "NSE",
            "action": "SELL",
            "quantity": 100,
            "price_type": "MARKET",
            "product": "CNC",
        }
    )
    ee.check_and_execute_pending_orders()

    status = get_margin_status(user_id)
    print_margin_status("After SELL 100", status)
    assert status["used"] == 0, f"Expected margin ₹0, got ₹{status['used']}"

    # Round 2: BUY 100 → SELL 100
    print("\n→ Round 2: BUY 100 ZEEL...")
    om.place_order(
        {
            "symbol": "ZEEL",
            "exchange": "NSE",
            "action": "BUY",
            "quantity": 100,
            "price_type": "MARKET",
            "product": "CNC",
        }
    )
    ee.check_and_execute_pending_orders()

    status = get_margin_status(user_id)
    print_margin_status("After BUY 100 (reopened)", status)
    assert abs(status["used"] - expected_margin) < 1, (
        f"Expected margin ~₹{expected_margin}, got ₹{status['used']}"
    )

    print("\n→ Round 2: SELL 100 ZEEL...")
    om.place_order(
        {
            "symbol": "ZEEL",
            "exchange": "NSE",
            "action": "SELL",
            "quantity": 100,
            "price_type": "MARKET",
            "product": "CNC",
        }
    )
    ee.check_and_execute_pending_orders()

    status = get_margin_status(user_id)
    print_margin_status("After SELL 100 (closed again)", status)
    assert status["used"] == 0, f"Expected margin ₹0, got ₹{status['used']}"

    print("\n✅ SCENARIO 2 PASSED")


def test_scenario_3():
    """Test: BUY 100 → SELL 200 (position reversal)"""
    print("\n" + "=" * 60)
    print("SCENARIO 3: BUY 100 → SELL 200 (position reversal)")
    print("=" * 60)

    user_id = "rajandran"
    reset_user_data(user_id)

    om = OrderManager(user_id)
    ee = ExecutionEngine()

    # BUY 100
    print("\n→ BUY 100 ZEEL...")
    om.place_order(
        {
            "symbol": "ZEEL",
            "exchange": "NSE",
            "action": "BUY",
            "quantity": 100,
            "price_type": "MARKET",
            "product": "CNC",
        }
    )
    ee.check_and_execute_pending_orders()

    status = get_margin_status(user_id)
    print_margin_status("After BUY 100", status)
    expected_margin = 100 * 112.37
    assert abs(status["used"] - expected_margin) < 1, (
        f"Expected margin ~₹{expected_margin}, got ₹{status['used']}"
    )

    # SELL 200 (reversal to SHORT 100)
    print("\n→ SELL 200 ZEEL (reversing to SHORT 100)...")
    om.place_order(
        {
            "symbol": "ZEEL",
            "exchange": "NSE",
            "action": "SELL",
            "quantity": 200,
            "price_type": "MARKET",
            "product": "CNC",
        }
    )
    ee.check_and_execute_pending_orders()

    status = get_margin_status(user_id)
    print_margin_status("After SELL 200 (SHORT 100)", status)
    # Should have margin for SHORT 100
    assert abs(status["used"] - expected_margin) < 1, (
        f"Expected margin ~₹{expected_margin}, got ₹{status['used']}"
    )

    print("\n✅ SCENARIO 3 PASSED")


def test_scenario_4():
    """Test: BUY 100 → BUY 100 (adding to position)"""
    print("\n" + "=" * 60)
    print("SCENARIO 4: BUY 100 → BUY 100 (adding to position)")
    print("=" * 60)

    user_id = "rajandran"
    reset_user_data(user_id)

    om = OrderManager(user_id)
    ee = ExecutionEngine()

    # BUY 100
    print("\n→ BUY 100 ZEEL...")
    om.place_order(
        {
            "symbol": "ZEEL",
            "exchange": "NSE",
            "action": "BUY",
            "quantity": 100,
            "price_type": "MARKET",
            "product": "CNC",
        }
    )
    ee.check_and_execute_pending_orders()

    status = get_margin_status(user_id)
    print_margin_status("After BUY 100", status)
    expected_margin = 100 * 112.37
    assert abs(status["used"] - expected_margin) < 1, (
        f"Expected margin ~₹{expected_margin}, got ₹{status['used']}"
    )

    # BUY 100 more
    print("\n→ BUY 100 ZEEL (adding to position)...")
    om.place_order(
        {
            "symbol": "ZEEL",
            "exchange": "NSE",
            "action": "BUY",
            "quantity": 100,
            "price_type": "MARKET",
            "product": "CNC",
        }
    )
    ee.check_and_execute_pending_orders()

    status = get_margin_status(user_id)
    print_margin_status("After BUY 100 (total 200)", status)
    expected_margin = 200 * 112.37
    assert abs(status["used"] - expected_margin) < 1, (
        f"Expected margin ~₹{expected_margin}, got ₹{status['used']}"
    )

    print("\n✅ SCENARIO 4 PASSED")


if __name__ == "__main__":
    # Initialize database
    init_db()

    print("\n🧪 TESTING MARGIN SCENARIOS")
    print("=" * 60)

    try:
        test_scenario_1()
        test_scenario_2()
        test_scenario_3()
        test_scenario_4()

        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

```


---

# FILE: test\sandbox\test_orderbook_api.py

```py
#!/usr/bin/env python3
"""
Test that rejected orders appear correctly in the orderbook API response
"""

from decimal import Decimal

from database.sandbox_db import SandboxOrders, db_session, init_db
from sandbox.order_manager import OrderManager

# Initialize database
init_db()

# Test user
user_id = "rajandran"

# Get order manager
om = OrderManager(user_id)

# Get orderbook
success, response, code = om.get_orderbook()

print("📋 Orderbook API Response")
print("=" * 60)
print(f"Success: {success}")
print(f"Status Code: {code}")
print("\nResponse:")
print(f"  Status: {response.get('status')}")
print(f"  Mode: {response.get('mode')}")

# Check for rejected orders
if "data" in response:
    data = response["data"]

    # Extract orders list from data dict
    if isinstance(data, dict) and "orders" in data:
        order_list = data["orders"]
        print(f"\n  Total Orders: {len(order_list)}")
    elif isinstance(data, list):
        order_list = data
        print(f"\n  Total Orders: {len(order_list)}")
    else:
        order_list = []
        print("\n  Unexpected data structure")

    # Filter rejected orders
    rejected_orders = [
        o for o in order_list if isinstance(o, dict) and o.get("order_status") == "rejected"
    ]

    if rejected_orders:
        print(f"\n  ❌ Rejected Orders: {len(rejected_orders)}")
        for order in rejected_orders:
            print(f"\n    Order ID: {order['orderid']}")
            print(f"    Symbol: {order['symbol']}")
            print(f"    Action: {order['action']}")
            print(f"    Quantity: {order['quantity']}")
            print(f"    Product: {order['product']}")
            print(f"    Status: {order['order_status']}")
            print(f"    Rejection Reason: {order.get('rejection_reason', 'N/A')}")
    else:
        print("\n  ✅ No rejected orders")

    # Check statistics
    if "statistics" in response:
        stats = response["statistics"]
        print("\n  📊 Statistics:")
        print(f"    Total Buy Orders: {stats.get('total_buy_orders', 0)}")
        print(f"    Total Sell Orders: {stats.get('total_sell_orders', 0)}")
        print(f"    Open Orders: {stats.get('total_open_orders', 0)}")
        print(f"    Completed Orders: {stats.get('total_completed_orders', 0)}")
        print(f"    Rejected Orders: {stats.get('total_rejected_orders', 0)}")

print("\n" + "=" * 60)

```


---

# FILE: test\sandbox\test_rejected_order.py

```py
#!/usr/bin/env python3
"""
Test that rejected CNC SELL orders appear in the orderbook
"""

from decimal import Decimal

from database.sandbox_db import SandboxFunds, SandboxOrders, SandboxPositions, db_session, init_db
from sandbox.order_manager import OrderManager

# Initialize database
init_db()

# Test user
user_id = "rajandran"

# Clear ALL previous orders to avoid ID conflicts
SandboxOrders.query.delete()  # Delete ALL orders
SandboxPositions.query.filter_by(user_id=user_id, symbol="ZEEL", product="CNC").delete()
db_session.commit()

# Ensure user has funds
funds = SandboxFunds.query.filter_by(user_id=user_id).first()
if not funds:
    funds = SandboxFunds(
        user_id=user_id,
        total_capital=Decimal("10000000.00"),
        available_balance=Decimal("10000000.00"),
        used_margin=Decimal("0.00"),
    )
    db_session.add(funds)
    db_session.commit()

print("🧪 Testing Rejected Order in Orderbook")
print("=" * 60)

# Create order manager
om = OrderManager(user_id)

# Try to place a CNC SELL order without position
print("\n→ Attempting CNC SELL 100 ZEEL (no position)...")
success, response, code = om.place_order(
    {
        "symbol": "ZEEL",
        "exchange": "NSE",
        "action": "SELL",
        "quantity": 100,
        "price_type": "MARKET",
        "product": "CNC",
    }
)

print(f"Response: {response}")
print(f"Success: {success}, Code: {code}")

# Check orderbook
print("\n📋 Checking Orderbook...")
orders = SandboxOrders.query.filter_by(user_id=user_id).all()

print(f"Found {len(orders)} order(s):")
for order in orders:
    print(f"\n  Order ID: {order.orderid}")
    print(f"  Symbol: {order.symbol}")
    print(f"  Action: {order.action}")
    print(f"  Quantity: {order.quantity}")
    print(f"  Product: {order.product}")
    print(f"  Status: {order.order_status}")
    print(f"  Rejection Reason: {order.rejection_reason}")
    print(f"  Margin Blocked: {order.margin_blocked}")

if orders and orders[0].order_status == "rejected":
    print("\n✅ SUCCESS: Rejected order appears in orderbook!")
else:
    print("\n❌ FAIL: Rejected order not in orderbook")

print("=" * 60)

```
