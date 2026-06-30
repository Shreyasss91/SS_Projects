# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\sandbox



---

# FILE: sandbox\__init__.py

```py
# sandbox/__init__.py
"""
Sandbox Mode - API Analyzer Environment

OpenAlgo is an open-source application that provides Sandbox Mode (API Analyzer)
to make it easier for traders to test strategies in a realistic simulated
environment without executing real trades through a broker.

Key Features:
- ₹10,000,000 (1 Crore) starting sandbox capital (configurable)
- Auto reset every Sunday at midnight IST (configurable)
- Real market data integration
- Realistic order execution simulation
- Position and holdings management
- Leverage-based margin calculations
- Auto square-off for MIS positions
- T+1 settlement for CNC holdings
- Self-hosted, transparent, open-source testing environment
"""

__version__ = "1.0.0"

```


---

# FILE: sandbox\catch_up_processor.py

```py
# sandbox/catch_up_processor.py
"""
Catch-Up Processor - Handles missed scheduled jobs after app restart

Features:
- T+1 settlement catch-up for CNC positions
- Daily PnL reset catch-up if app was down during SESSION_EXPIRY_TIME
- Called after master contract download completes (fresh login)
"""

import os
from datetime import datetime, timedelta
from decimal import Decimal

import pytz

from utils.logging import get_logger

logger = get_logger(__name__)

# IST timezone
IST = pytz.timezone("Asia/Kolkata")


def get_last_session_boundary():
    """
    Get the most recent session boundary time (SESSION_EXPIRY_TIME)
    Returns datetime in IST
    """
    session_expiry_str = os.getenv("SESSION_EXPIRY_TIME", "03:00")
    reset_hour, reset_minute = map(int, session_expiry_str.split(":"))

    now = datetime.now(IST)
    today_boundary = now.replace(hour=reset_hour, minute=reset_minute, second=0, microsecond=0)

    if now >= today_boundary:
        return today_boundary
    else:
        return today_boundary - timedelta(days=1)


def catch_up_mis_squareoff():
    """
    Check and square-off any MIS positions from previous days
    MIS positions are intraday and should NEVER carry overnight
    Called after master contract download completes

    IMPORTANT: Since these positions are from previous days, their P&L should NOT
    be added to today_realized_pnl - only to accumulated/all-time realized_pnl
    """
    try:
        from database.sandbox_db import SandboxFunds, SandboxPositions, db_session
        from sandbox.fund_manager import FundManager

        # Get today's date at midnight IST
        today = datetime.now(IST).date()
        today_start = datetime.combine(today, datetime.min.time())
        today_start = IST.localize(today_start)

        # Find MIS positions from previous days (created before today)
        stale_mis_positions = (
            SandboxPositions.query.filter_by(product="MIS")
            .filter(SandboxPositions.quantity != 0, SandboxPositions.created_at < today_start)
            .all()
        )

        if not stale_mis_positions:
            logger.debug("Catch-up: No stale MIS positions found")
            return

        logger.info(
            f"Catch-up: Found {len(stale_mis_positions)} stale MIS positions from previous days"
        )

        # Process each stale MIS position manually (not through normal close flow)
        # This ensures we don't add to today_realized_pnl
        for position in stale_mis_positions:
            try:
                user_id = position.user_id
                symbol = position.symbol
                quantity = position.quantity
                avg_price = Decimal(str(position.average_price))
                margin_blocked = Decimal(str(position.margin_blocked or 0))

                # Get current LTP for settlement (use last known LTP or avg price)
                if position.ltp and Decimal(str(position.ltp)) > 0:
                    settlement_price = Decimal(str(position.ltp))
                else:
                    settlement_price = avg_price

                # Calculate realized P&L (apply contract_value for crypto, e.g. 0.01 for ETHUSD.P)
                from database.token_db import get_symbol_info as _get_sym_info
                _sym_cv = _get_sym_info(symbol, position.exchange)
                _cv = Decimal(str(_sym_cv.contract_value)) if _sym_cv and _sym_cv.contract_value else Decimal("1.0")
                if quantity > 0:
                    realized_pnl = (settlement_price - avg_price) * Decimal(str(quantity)) * _cv
                else:
                    realized_pnl = (avg_price - settlement_price) * Decimal(str(abs(quantity))) * _cv

                logger.info(
                    f"Catch-up settling stale MIS: {symbol} for {user_id}, "
                    f"qty={quantity}, pnl={realized_pnl}, margin={margin_blocked}"
                )

                # Update funds - add to realized_pnl but NOT today_realized_pnl
                funds = SandboxFunds.query.filter_by(user_id=user_id).first()
                if funds:
                    # Release margin back to available balance
                    funds.available_balance += margin_blocked + realized_pnl
                    funds.used_margin -= margin_blocked

                    # Add to all-time realized P&L only (NOT today_realized_pnl)
                    funds.realized_pnl = (funds.realized_pnl or Decimal("0.00")) + realized_pnl
                    funds.total_pnl = funds.realized_pnl + (funds.unrealized_pnl or Decimal("0.00"))

                    # Ensure used_margin doesn't go negative
                    if funds.used_margin < 0:
                        funds.used_margin = Decimal("0.00")

                # Update position to closed state
                position.quantity = 0
                position.margin_blocked = Decimal("0.00")
                position.pnl = realized_pnl
                position.accumulated_realized_pnl = (
                    position.accumulated_realized_pnl or Decimal("0.00")
                ) + realized_pnl
                # DO NOT update today_realized_pnl since this is from a previous day
                position.today_realized_pnl = Decimal("0.00")

                db_session.commit()
                logger.info(f"Catch-up: Settled stale MIS position {symbol} for {user_id}")

            except Exception as e:
                db_session.rollback()
                logger.exception(f"Error settling stale MIS position {position.symbol}: {e}")

        logger.info("Catch-up: Stale MIS positions settled")

    except Exception as e:
        logger.exception(f"Error in catch-up MIS square-off: {e}")


def catch_up_t1_settlement():
    """
    Check and process T+1 settlement if needed
    Called after master contract download completes
    """
    try:
        from database.sandbox_db import SandboxPositions
        from sandbox.holdings_manager import process_all_t1_settlements

        # Check if there are any CNC positions that need settlement
        ist = IST
        today = datetime.now(ist).date()
        settlement_cutoff = datetime.combine(today, datetime.min.time())

        pending_positions = (
            SandboxPositions.query.filter_by(product="CNC")
            .filter(SandboxPositions.created_at < settlement_cutoff)
            .count()
        )

        if pending_positions > 0:
            logger.info(f"Catch-up: Found {pending_positions} CNC positions pending T+1 settlement")
            process_all_t1_settlements()
            logger.info("Catch-up: T+1 settlement completed")
        else:
            logger.debug("Catch-up: No CNC positions pending T+1 settlement")

    except Exception as e:
        logger.exception(f"Error in catch-up T+1 settlement: {e}")


def catch_up_daily_pnl_reset():
    """
    Check and reset daily PnL if needed
    Called after master contract download completes
    """
    try:
        from database.sandbox_db import SandboxFunds, SandboxPositions, db_session

        last_session_boundary = get_last_session_boundary()

        # Check if there are positions with non-zero today_realized_pnl
        # that were last updated before the session boundary
        positions_needing_reset = SandboxPositions.query.filter(
            SandboxPositions.today_realized_pnl != None,
            SandboxPositions.today_realized_pnl != Decimal("0.00"),
            SandboxPositions.updated_at < last_session_boundary,
        ).count()

        funds_needing_reset = SandboxFunds.query.filter(
            SandboxFunds.today_realized_pnl != None,
            SandboxFunds.today_realized_pnl != Decimal("0.00"),
            SandboxFunds.updated_at < last_session_boundary,
        ).count()

        if positions_needing_reset > 0 or funds_needing_reset > 0:
            logger.info(
                f"Catch-up: Found {positions_needing_reset} positions, {funds_needing_reset} funds needing PnL reset"
            )

            # Reset all today_realized_pnl that are from before session boundary
            SandboxPositions.query.filter(
                SandboxPositions.updated_at < last_session_boundary
            ).update({"today_realized_pnl": Decimal("0.00")})

            SandboxFunds.query.filter(SandboxFunds.updated_at < last_session_boundary).update(
                {"today_realized_pnl": Decimal("0.00")}
            )

            db_session.commit()
            logger.info("Catch-up: Daily PnL reset completed")
        else:
            logger.debug("Catch-up: No stale today_realized_pnl found")

    except Exception as e:
        logger.exception(f"Error in catch-up daily PnL reset: {e}")


def catch_up_daily_pnl_snapshot():
    """
    Check and create daily P&L snapshots for missed days
    If the app was down at 23:59 IST, the snapshot wouldn't have been captured
    """
    try:
        from datetime import date, timedelta

        from database.sandbox_db import (
            SandboxDailyPnL,
            SandboxFunds,
            SandboxHoldings,
            SandboxPositions,
            db_session,
        )

        today = date.today()
        yesterday = today - timedelta(days=1)

        # Get all users with funds
        all_funds = SandboxFunds.query.all()

        for funds in all_funds:
            user_id = funds.user_id

            # Check if yesterday's snapshot exists
            existing_snapshot = SandboxDailyPnL.query.filter_by(
                user_id=user_id, date=yesterday
            ).first()

            if existing_snapshot:
                logger.debug(f"Catch-up: Yesterday's snapshot already exists for user {user_id}")
                continue

            # Calculate yesterday's P&L from available data
            # Since we don't have exact yesterday's values, use what we can reconstruct:
            # - All-time realized - today's realized = yesterday's (approximate)
            all_time_realized = Decimal(str(funds.realized_pnl or 0))
            today_realized = Decimal(str(funds.today_realized_pnl or 0))

            # Yesterday's realized = All-time - Today's
            # This is approximate but better than nothing
            yesterday_realized = all_time_realized - today_realized

            # For unrealized, we can't know yesterday's values accurately
            # So we'll set them to 0 (positions may have changed)
            positions_unrealized = Decimal("0.00")
            holdings_unrealized = Decimal("0.00")

            # Only create snapshot if there was some activity
            if yesterday_realized != 0 or all_time_realized != 0:
                snapshot = SandboxDailyPnL(
                    user_id=user_id,
                    date=yesterday,
                    realized_pnl=yesterday_realized,
                    positions_unrealized_pnl=positions_unrealized,
                    holdings_unrealized_pnl=holdings_unrealized,
                    total_mtm=yesterday_realized,  # Only realized since we don't know unrealized
                    available_balance=funds.available_balance,
                    used_margin=funds.used_margin,
                    portfolio_value=funds.available_balance + funds.used_margin,
                )
                db_session.add(snapshot)
                logger.info(
                    f"Catch-up: Created yesterday's P&L snapshot for user {user_id}, realized={yesterday_realized}"
                )

        db_session.commit()
        logger.info("Catch-up: Daily P&L snapshot backfill completed")

    except Exception as e:
        logger.exception(f"Error in catch-up daily P&L snapshot: {e}")


def run_catch_up_tasks():
    """
    Run all catch-up tasks after master contract download completes
    This ensures scheduled jobs that were missed (due to app being down) are processed

    Note: Runs regardless of sandbox mode - the sandbox database exists independently
    and positions need to be settled even if user is not in analyzer mode
    """
    try:
        logger.info("Running catch-up tasks after master contract download...")

        # Run MIS square-off catch-up (stale overnight positions)
        catch_up_mis_squareoff()

        # Run T+1 settlement catch-up
        catch_up_t1_settlement()

        # Run daily PnL reset catch-up
        catch_up_daily_pnl_reset()

        # Run daily PnL snapshot catch-up (for missed days)
        catch_up_daily_pnl_snapshot()

        logger.info("Catch-up tasks completed")

    except Exception as e:
        logger.exception(f"Error running catch-up tasks: {e}")

```


---

# FILE: sandbox\execution_engine.py

```py
# sandbox/execution_engine.py
"""
Execution Engine - Monitors and executes pending orders

Features:
- Background order monitoring (every 5 seconds configurable)
- Real-time quote fetching from broker
- Order execution based on price type (MARKET, LIMIT, SL, SL-M)
- Trade creation and position updates
- Rate limit compliance (10 orders/second, 50 API calls/second)
- Batch processing for efficiency
"""

import os
import sys
import time
import uuid
from datetime import datetime
from decimal import Decimal

import pytz

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.auth_db import get_auth_token_broker
from database.sandbox_db import SandboxOrders, SandboxPositions, SandboxTrades, db_session
from database.token_db import get_symbol_info
from sandbox.fund_manager import FundManager, reconcile_margin, validate_margin_consistency
from services.quotes_service import get_multiquotes, get_quotes
from utils.logging import get_logger

logger = get_logger(__name__)


class ExecutionEngine:
    """Executes pending orders based on market data"""

    def __init__(self):
        # Read rate limits from .env (same as API protection)
        self.order_rate_limit = int(os.getenv("ORDER_RATE_LIMIT", "10 per second").split()[0])
        self.api_rate_limit = int(os.getenv("API_RATE_LIMIT", "50 per second").split()[0])
        self.batch_delay = 1.0  # 1 second between batches

    def check_and_execute_pending_orders(self):
        """
        Main execution loop - checks all pending orders and executes if conditions met
        Respects rate limits through batch processing
        """
        try:
            # Get all pending orders
            pending_orders = SandboxOrders.query.filter_by(order_status="open").all()

            if not pending_orders:
                logger.debug("No pending orders to process")
                return

            logger.info(f"Processing {len(pending_orders)} pending orders")

            # Group orders by user and symbol for efficient quote fetching
            orders_by_symbol = {}
            for order in pending_orders:
                key = (order.symbol, order.exchange)
                if key not in orders_by_symbol:
                    orders_by_symbol[key] = []
                orders_by_symbol[key].append(order)

            # Fetch quotes using multiquotes (more efficient - single API call)
            # Falls back to individual quotes if multiquotes fails
            quote_cache = {}
            symbols_list = list(orders_by_symbol.keys())

            # Fetch quotes using multiquotes only (no individual quote fallback to avoid rate limiting)
            # WebSocket is the primary data source; multiquotes is the fallback
            quote_cache = self._fetch_quotes_batch(symbols_list)

            # Log symbols that couldn't be fetched (don't retry individually to avoid rate limits)
            failed_symbols = [
                s for s in symbols_list if s not in quote_cache or quote_cache[s] is None
            ]
            if failed_symbols:
                logger.debug(
                    f"{len(failed_symbols)} symbols not available via multiquotes, waiting for WebSocket data"
                )

            # Process orders in batches (respecting order rate limit of 10/second)
            orders_processed = 0
            for i in range(0, len(pending_orders), self.order_rate_limit):
                batch = pending_orders[i : i + self.order_rate_limit]

                for order in batch:
                    quote = quote_cache.get((order.symbol, order.exchange))
                    if quote:
                        self._process_order(order, quote)
                        orders_processed += 1

                # Wait 1 second before next batch if more orders remain
                if i + self.order_rate_limit < len(pending_orders):
                    time.sleep(self.batch_delay)

            logger.info(f"Processed {orders_processed} orders")

        except Exception as e:
            logger.exception(f"Error in execution engine: {e}")

    def _fetch_quote(self, symbol, exchange):
        """
        Fetch real-time quote for a symbol using API key
        Returns dict with ltp, high, low, open, close, etc.
        Returns None if quote cannot be fetched (permission error, API error, etc.)
        """
        try:
            # Get any user's API key for fetching quotes
            from database.auth_db import ApiKeys, decrypt_token

            api_key_obj = ApiKeys.query.first()

            if not api_key_obj:
                logger.debug("No API keys found for fetching quotes")
                return None

            # Decrypt the API key
            api_key = decrypt_token(api_key_obj.api_key_encrypted)

            # Use quotes service with API key authentication
            success, response, status_code = get_quotes(
                symbol=symbol, exchange=exchange, api_key=api_key
            )

            if success and "data" in response:
                quote_data = response["data"]
                logger.debug(f"Fetched quote for {symbol}: LTP={quote_data.get('ltp', 0)}")
                return quote_data
            else:
                # Log at debug level to avoid spam for permission errors
                logger.debug(
                    f"Could not fetch quote for {symbol}: {response.get('message', 'Unknown error')}"
                )
                return None

        except Exception as e:
            # Handle all exceptions gracefully - don't stop execution engine
            logger.debug(f"Exception fetching quote for {symbol}: {str(e)}")
            return None

    def _fetch_quotes_batch(self, symbols_list):
        """
        Fetch quotes for multiple symbols in a single API call using multiquotes.
        Returns dict mapping (symbol, exchange) to quote data.
        Returns empty dict if multiquotes fails completely.
        """
        quote_cache = {}

        if not symbols_list:
            return quote_cache

        try:
            # Get any user's API key for fetching quotes
            from database.auth_db import ApiKeys, decrypt_token

            api_key_obj = ApiKeys.query.first()

            if not api_key_obj:
                logger.debug("No API keys found for fetching multiquotes")
                return quote_cache

            # Decrypt the API key
            api_key = decrypt_token(api_key_obj.api_key_encrypted)

            # Prepare symbols list for multiquotes API
            symbols_payload = [
                {"symbol": symbol, "exchange": exchange} for symbol, exchange in symbols_list
            ]

            # Use multiquotes service
            success, response, status_code = get_multiquotes(
                symbols=symbols_payload, api_key=api_key
            )

            if success and "results" in response:
                results = response["results"]
                successful_count = 0

                for result in results:
                    symbol = result.get("symbol")
                    exchange = result.get("exchange")

                    # Check if this result has data or error
                    if "data" in result and result["data"]:
                        quote_data = result["data"]
                        quote_cache[(symbol, exchange)] = quote_data
                        logger.debug(f"Multiquotes: {symbol} LTP={quote_data.get('ltp', 0)}")
                        successful_count += 1
                    elif "error" in result:
                        logger.debug(f"Multiquotes error for {symbol}: {result['error']}")

                logger.info(
                    f"Multiquotes fetched {successful_count}/{len(symbols_list)} symbols successfully"
                )
            else:
                logger.debug(f"Multiquotes failed: {response.get('message', 'Unknown error')}")

        except Exception as e:
            logger.debug(f"Exception in multiquotes fetch: {str(e)}")

        return quote_cache

    def _publish_fill_event(
        self, orderid, tradeid, symbol, exchange, action, quantity, price, product, strategy
    ):
        """Emit SandboxOrderFilledEvent so the analyzer-mode UI auto-refreshes.

        Logged at INFO so it's visible in server logs and confirms the
        event-bus path was reached (any breakage in registration or imports
        would suppress the log too).
        """
        try:
            from events import SandboxOrderFilledEvent
            from utils.event_bus import bus

            bus.publish(
                SandboxOrderFilledEvent(
                    mode="analyze",
                    api_type="sandbox.fill",
                    orderid=orderid,
                    tradeid=tradeid,
                    symbol=symbol,
                    exchange=exchange,
                    action=action,
                    quantity=quantity,
                    price=price,
                    product=product,
                    strategy=strategy,
                )
            )
            logger.info(
                f"[sandbox-fill] Published SandboxOrderFilledEvent for {orderid} "
                f"({symbol} {action} {quantity} @ {price})"
            )
        except Exception as pub_err:
            # Never let event-bus failures break order execution
            logger.debug(f"Failed to publish SandboxOrderFilledEvent: {pub_err}")

    def _process_order(self, order, quote):
        """
        Process a single order based on current quote
        Determines if order should be executed based on price type
        """
        try:
            # Check if this order already has a trade (prevent duplicates)
            # This can happen with MARKET orders that are executed immediately on placement
            # but the order status hasn't been updated to 'complete' yet due to race condition
            existing_trade = SandboxTrades.query.filter_by(orderid=order.orderid).first()
            if existing_trade:
                logger.debug(
                    f"Order {order.orderid} already has trade {existing_trade.tradeid}, skipping execution"
                )
                # Update order status to complete if it's still open (race condition cleanup)
                if order.order_status == "open":
                    order.order_status = "complete"
                    order.average_price = existing_trade.price
                    order.filled_quantity = order.quantity
                    order.pending_quantity = 0
                    order.update_timestamp = datetime.now(pytz.timezone("Asia/Kolkata"))
                    db_session.commit()
                    logger.info(
                        f"Updated order {order.orderid} status to complete (was in race condition)"
                    )
                    # Race-condition cleanup transitions an order to complete
                    # without going through _execute_order, so emit here too.
                    self._publish_fill_event(
                        orderid=order.orderid,
                        tradeid=existing_trade.tradeid,
                        symbol=order.symbol,
                        exchange=order.exchange,
                        action=order.action,
                        quantity=int(order.quantity),
                        price=float(existing_trade.price),
                        product=order.product,
                        strategy=order.strategy or "",
                    )
                return

            ltp = Decimal(str(quote.get("ltp", 0)))
            bid = Decimal(str(quote.get("bid", 0)))
            ask = Decimal(str(quote.get("ask", 0)))

            if ltp <= 0:
                logger.warning(f"Invalid LTP for order {order.orderid}: {ltp}")
                return

            # Determine if order should be executed based on price type
            should_execute = False
            execution_price = None

            if order.price_type == "MARKET":
                # Market orders execute immediately at bid/ask (more realistic)
                # BUY: Execute at ask price (pay seller's asking price)
                # SELL: Execute at bid price (receive buyer's bid price)
                # If bid/ask is 0, fall back to LTP
                should_execute = True
                if order.action == "BUY":
                    execution_price = ask if ask > 0 else ltp
                else:  # SELL
                    execution_price = bid if bid > 0 else ltp

            elif order.price_type == "LIMIT":
                # Limit BUY: Execute if LTP <= Limit Price, fill at limit price
                # Limit SELL: Execute if LTP >= Limit Price, fill at limit price
                # In real exchanges, limit orders sit on the book at the limit price
                # and fill at that price when the market crosses through
                if order.action == "BUY" and ltp <= order.price:
                    should_execute = True
                    execution_price = order.price  # Fill at limit price
                elif order.action == "SELL" and ltp >= order.price:
                    should_execute = True
                    execution_price = order.price  # Fill at limit price

            elif order.price_type == "SL":
                # Stop Loss Limit order
                # SL BUY: When LTP >= trigger price, order activates. Execute at LTP if LTP <= limit price
                # SL SELL: When LTP <= trigger price, order activates. Execute at LTP if LTP >= limit price
                if order.action == "BUY" and ltp >= order.trigger_price:
                    if ltp <= order.price:
                        should_execute = True
                        execution_price = ltp  # Execute at current market price (LTP)
                elif order.action == "SELL" and ltp <= order.trigger_price:
                    if ltp >= order.price:
                        should_execute = True
                        execution_price = ltp  # Execute at current market price (LTP)

            elif order.price_type == "SL-M":
                # Stop Loss Market order
                # BUY: Execute at market when LTP >= trigger price
                # SELL: Execute at market when LTP <= trigger price
                if order.action == "BUY" and ltp >= order.trigger_price:
                    should_execute = True
                    execution_price = ltp
                elif order.action == "SELL" and ltp <= order.trigger_price:
                    should_execute = True
                    execution_price = ltp

            # Execute the order if conditions are met
            if should_execute:
                self._execute_order(order, execution_price)

        except Exception as e:
            logger.exception(f"Error processing order {order.orderid}: {e}")

    def _execute_order(self, order, execution_price):
        """
        Execute an order - create trade, update positions, release/adjust margin
        """
        try:
            logger.info(
                f"Executing order {order.orderid}: {order.symbol} {order.action} {order.quantity} @ {execution_price}"
            )

            # Generate trade ID
            tradeid = self._generate_trade_id()

            # Create trade record
            trade = SandboxTrades(
                tradeid=tradeid,
                orderid=order.orderid,
                user_id=order.user_id,
                symbol=order.symbol,
                exchange=order.exchange,
                action=order.action,
                quantity=order.quantity,
                price=execution_price,
                product=order.product,
                strategy=order.strategy,
                trade_timestamp=datetime.now(pytz.timezone("Asia/Kolkata")),
            )

            db_session.add(trade)

            # Update order status
            order.order_status = "complete"
            order.average_price = execution_price
            order.filled_quantity = order.quantity
            order.pending_quantity = 0
            order.update_timestamp = datetime.now(pytz.timezone("Asia/Kolkata"))

            db_session.commit()

            # Update position
            self._update_position(order, execution_price)

            logger.info(f"Order {order.orderid} executed successfully. Trade ID: {tradeid}")

            # Notify UI subscribers (OrderBook / TradeBook / Positions auto-refresh).
            # Engine-internal fills don't go through the service layer, so the
            # service-layer publish points (place_order_service etc.) never see
            # them — without this the analyzer UI sits stale until manual refresh.
            self._publish_fill_event(
                orderid=order.orderid,
                tradeid=tradeid,
                symbol=order.symbol,
                exchange=order.exchange,
                action=order.action,
                quantity=int(order.quantity),
                price=float(execution_price),
                product=order.product,
                strategy=order.strategy or "",
            )

        except Exception as e:
            db_session.rollback()
            logger.exception(f"Error executing order {order.orderid}: {e}")

            # Mark order as rejected
            try:
                order.order_status = "rejected"
                order.rejection_reason = f"Execution error: {str(e)}"
                order.update_timestamp = datetime.now(pytz.timezone("Asia/Kolkata"))
                db_session.commit()
            except Exception:
                db_session.rollback()

    def _update_position(self, order, execution_price):
        """
        Update or create position after trade execution
        Handle netting for opposite positions

        Note: Margin was already blocked when order was placed (for pending orders like LIMIT/SL/SL-M)
        or during immediate execution (for MARKET orders). We only need to release margin when
        positions are closed/reduced.
        """
        try:
            fund_manager = FundManager(order.user_id)

            # Check if position exists
            position = SandboxPositions.query.filter_by(
                user_id=order.user_id,
                symbol=order.symbol,
                exchange=order.exchange,
                product=order.product,
            ).first()

            if not position:
                # Create new position
                # Store the exact margin that was blocked at order placement time
                order_margin = (
                    order.margin_blocked
                    if hasattr(order, "margin_blocked") and order.margin_blocked
                    else Decimal("0.00")
                )
                position = SandboxPositions(
                    user_id=order.user_id,
                    symbol=order.symbol,
                    exchange=order.exchange,
                    product=order.product,
                    quantity=order.quantity if order.action == "BUY" else -order.quantity,
                    average_price=execution_price,
                    ltp=execution_price,
                    pnl=Decimal("0.00"),
                    pnl_percent=Decimal("0.00"),
                    accumulated_realized_pnl=Decimal("0.00"),
                    margin_blocked=order_margin,  # Store exact margin from order
                    created_at=datetime.now(pytz.timezone("Asia/Kolkata")),
                )
                db_session.add(position)
                logger.info(
                    f"Created new position: {order.symbol} {order.action} {order.quantity} (margin blocked: ₹{order_margin})"
                )

            else:
                # Update existing position (netting logic)
                old_quantity = position.quantity
                new_quantity = order.quantity if order.action == "BUY" else -order.quantity
                final_quantity = old_quantity + new_quantity

                # Special case: Reopening a closed position (old_quantity = 0)
                if old_quantity == 0:
                    # Keep accumulated realized P&L from previous trades, start fresh unrealized P&L
                    position.quantity = new_quantity
                    position.average_price = execution_price
                    position.ltp = execution_price
                    position.pnl = Decimal("0.00")  # Reset current P&L (will be updated by MTM)
                    position.pnl_percent = Decimal("0.00")
                    # accumulated_realized_pnl stays as is from previous closed trades
                    # today_realized_pnl: Keep current value (already reset at session boundary)
                    # Store the exact margin that was blocked at order placement time
                    order_margin = (
                        order.margin_blocked
                        if hasattr(order, "margin_blocked") and order.margin_blocked
                        else Decimal("0.00")
                    )
                    position.margin_blocked = order_margin
                    logger.info(
                        f"Reopened position: {order.symbol} {order.action} {order.quantity} (accumulated realized P&L: ₹{position.accumulated_realized_pnl}) (margin blocked: ₹{order_margin})"
                    )

                elif final_quantity == 0:
                    # Position closed completely
                    # Calculate realized P&L
                    _sym_cv_info = get_symbol_info(order.symbol, order.exchange)
                    _cv = float(_sym_cv_info.contract_value) if _sym_cv_info and _sym_cv_info.contract_value else 1.0
                    realized_pnl = self._calculate_realized_pnl(
                        old_quantity, position.average_price, abs(new_quantity), execution_price, contract_value=_cv
                    )

                    # Release the EXACT margin that was stored in the position
                    # This prevents over-release when execution price differs from order placement price
                    margin_to_release = (
                        position.margin_blocked
                        if hasattr(position, "margin_blocked") and position.margin_blocked
                        else Decimal("0.00")
                    )

                    if margin_to_release > 0:
                        fund_manager.release_margin(
                            margin_to_release, realized_pnl, f"Position closed: {order.symbol}"
                        )
                        logger.info(
                            f"Released exact margin ₹{margin_to_release} for closed position (from position.margin_blocked)"
                        )

                    # Keep position with 0 quantity to show it was closed
                    # Add realized P&L to accumulated realized P&L (all-time)
                    position.accumulated_realized_pnl += realized_pnl
                    # Add realized P&L to today's realized P&L (resets daily at session boundary)
                    position.today_realized_pnl = (
                        position.today_realized_pnl or Decimal("0.00")
                    ) + realized_pnl

                    position.quantity = 0
                    position.margin_blocked = Decimal(
                        "0.00"
                    )  # Reset margin to 0 when position fully closed
                    position.ltp = execution_price
                    position.pnl = (
                        position.today_realized_pnl
                    )  # Display today's realized P&L for closed positions
                    position.pnl_percent = Decimal("0.00")
                    logger.info(
                        f"Position closed: {order.symbol}, Realized P&L: ₹{realized_pnl}, Today's Realized P&L: ₹{position.today_realized_pnl}"
                    )

                elif (old_quantity > 0 and final_quantity > old_quantity) or (
                    old_quantity < 0 and final_quantity < old_quantity
                ):
                    # Adding to existing position (same direction, position size increasing)
                    # Calculate new average price
                    total_value = (abs(old_quantity) * position.average_price) + (
                        abs(new_quantity) * execution_price
                    )
                    total_quantity = abs(old_quantity) + abs(new_quantity)
                    new_average_price = total_value / total_quantity

                    position.quantity = final_quantity
                    position.average_price = new_average_price
                    position.ltp = execution_price

                    # Accumulate margin - add the margin blocked for this order to existing position margin
                    order_margin = (
                        order.margin_blocked
                        if hasattr(order, "margin_blocked") and order.margin_blocked
                        else Decimal("0.00")
                    )
                    position.margin_blocked = (
                        position.margin_blocked
                        if hasattr(position, "margin_blocked") and position.margin_blocked
                        else Decimal("0.00")
                    ) + order_margin
                    logger.info(
                        f"Added to position: {order.symbol}, New qty: {final_quantity}, Avg: {new_average_price} (total margin blocked: ₹{position.margin_blocked})"
                    )

                else:
                    # Reducing position (opposite direction) or position reversal
                    reduced_quantity = min(abs(old_quantity), abs(new_quantity))

                    # Calculate realized P&L for reduced portion
                    _sym_cv_info = get_symbol_info(order.symbol, order.exchange)
                    _cv = float(_sym_cv_info.contract_value) if _sym_cv_info and _sym_cv_info.contract_value else 1.0
                    realized_pnl = self._calculate_realized_pnl(
                        old_quantity, position.average_price, reduced_quantity, execution_price, contract_value=_cv
                    )

                    # Add realized P&L to accumulated realized P&L (all-time)
                    # This tracks all partial closes
                    position.accumulated_realized_pnl = (
                        position.accumulated_realized_pnl or Decimal("0.00")
                    ) + realized_pnl
                    # Add realized P&L to today's realized P&L (resets daily at session boundary)
                    position.today_realized_pnl = (
                        position.today_realized_pnl or Decimal("0.00")
                    ) + realized_pnl

                    # Release margin PROPORTIONALLY for reduced quantity
                    # Use exact margin stored in position, release proportionally
                    current_margin = (
                        position.margin_blocked
                        if hasattr(position, "margin_blocked") and position.margin_blocked
                        else Decimal("0.00")
                    )

                    if abs(old_quantity) > 0:
                        # Calculate proportion of position being reduced
                        reduction_proportion = Decimal(str(reduced_quantity)) / Decimal(
                            str(abs(old_quantity))
                        )
                        margin_to_release = current_margin * reduction_proportion
                    else:
                        margin_to_release = Decimal("0.00")

                    if margin_to_release > 0:
                        fund_manager.release_margin(
                            margin_to_release, realized_pnl, f"Position reduced: {order.symbol}"
                        )
                        logger.info(
                            f"Released proportional margin ₹{margin_to_release} for reduced position ({reduction_proportion * 100:.1f}% of ₹{current_margin})"
                        )

                    # Update remaining margin after proportional release
                    remaining_margin = current_margin - margin_to_release

                    # If position reversed, set margin for new reversed position
                    if abs(new_quantity) > abs(old_quantity):
                        # Position reversed - remaining quantity creates opposite position
                        remaining_quantity = abs(new_quantity) - abs(old_quantity)
                        position.quantity = (
                            remaining_quantity if order.action == "BUY" else -remaining_quantity
                        )
                        position.average_price = execution_price

                        # For reversed position, the new margin comes from the excess quantity in the order
                        # The old position's margin was fully released, new position gets fresh margin
                        # Note: order.margin_blocked contains margin for the FULL order quantity
                        # We need to calculate what portion corresponds to the excess quantity
                        if abs(new_quantity) > 0:
                            excess_proportion = Decimal(str(remaining_quantity)) / Decimal(
                                str(abs(new_quantity))
                            )
                            order_margin = (
                                order.margin_blocked
                                if hasattr(order, "margin_blocked") and order.margin_blocked
                                else Decimal("0.00")
                            )
                            new_position_margin = order_margin * excess_proportion
                            position.margin_blocked = new_position_margin
                            logger.info(
                                f"Position reversed: {order.symbol}, New qty: {position.quantity} (new margin: ₹{new_position_margin})"
                            )
                        else:
                            position.margin_blocked = Decimal("0.00")
                    else:
                        # Position reduced but not reversed - keep remaining margin
                        position.quantity = final_quantity
                        position.margin_blocked = remaining_margin
                        logger.info(
                            f"Position reduced: {order.symbol}, New qty: {final_quantity}, Remaining margin: ₹{remaining_margin}"
                        )

                    position.ltp = execution_price
                    logger.info(
                        f"Partial close: {order.symbol}, New qty: {final_quantity}, Realized P&L: ₹{realized_pnl}"
                    )

            db_session.commit()

            # Validate margin consistency after position update
            is_consistent, discrepancy = validate_margin_consistency(order.user_id)
            if not is_consistent:
                logger.warning(
                    f"Margin inconsistency detected after position update for {order.symbol}: "
                    f"discrepancy={discrepancy}. Auto-reconciling..."
                )
                # Auto-reconcile to prevent margin leaks
                reconcile_margin(order.user_id, auto_fix=True)

        except Exception as e:
            db_session.rollback()
            logger.exception(f"Error updating position for order {order.orderid}: {e}")
            raise

    def _calculate_realized_pnl(self, old_quantity, avg_price, close_quantity, close_price, contract_value=1.0):
        """Calculate realized P&L for closed positions, multiplied by contract_value (e.g. 0.01 for ETHUSD.P)."""
        try:
            avg_price = Decimal(str(avg_price))
            close_price = Decimal(str(close_price))
            close_quantity = Decimal(str(close_quantity))
            cv = Decimal(str(contract_value))

            if old_quantity > 0:
                # Long position closed
                pnl = (close_price - avg_price) * close_quantity * cv
            else:
                # Short position closed
                pnl = (avg_price - close_price) * close_quantity * cv

            return pnl

        except Exception as e:
            logger.exception(f"Error calculating realized P&L: {e}")
            return Decimal("0.00")

    def _generate_trade_id(self):
        """Generate unique trade ID"""
        now = datetime.now(pytz.timezone("Asia/Kolkata"))
        timestamp = now.strftime("%Y%m%d-%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"TRADE-{timestamp}-{unique_id}"


def run_execution_engine_once():
    """Run one cycle of the execution engine"""
    engine = ExecutionEngine()
    engine.check_and_execute_pending_orders()


if __name__ == "__main__":
    """Run execution engine in standalone mode for testing"""
    logger.info("Starting Sandbox Execution Engine")

    # Get check interval from config
    from database.sandbox_db import init_db

    init_db()

    check_interval = int(get_config("order_check_interval", "5"))
    logger.info(f"Order check interval: {check_interval} seconds")

    try:
        while True:
            run_execution_engine_once()
            time.sleep(check_interval)
    except KeyboardInterrupt:
        logger.info("Execution engine stopped by user")
    except Exception as e:
        logger.exception(f"Execution engine error: {e}")

```


---

# FILE: sandbox\execution_thread.py

```py
# sandbox/execution_thread.py
"""
Execution Engine Thread Manager

Manages the execution engine as a daemon thread that:
- Starts automatically when analyzer mode is enabled
- Stops gracefully when analyzer mode is disabled
- Runs continuously in the background monitoring and executing orders
- Supports WebSocket-based or polling-based execution
- Automatic fallback to polling if WebSocket is unavailable
"""

import os
import threading
import time

from database.sandbox_db import get_config
from utils.logging import get_logger

logger = get_logger(__name__)

# Global thread instance
_execution_thread = None
_websocket_engine = None
_thread_lock = threading.Lock()
_stop_event = threading.Event()
_current_engine_type = None  # Track which engine type is running
_auto_upgrade_thread = None
_auto_upgrade_stop_event = threading.Event()
_auto_upgrade_enabled = False


class ExecutionEngineThread(threading.Thread):
    """Daemon thread that runs the execution engine"""

    def __init__(self):
        super().__init__(daemon=True, name="SandboxExecutionEngine")
        self.stop_event = threading.Event()
        self.check_interval = int(get_config("order_check_interval", "5"))

    def run(self):
        """Main thread loop"""
        from sandbox.execution_engine import ExecutionEngine

        logger.debug("Sandbox Execution Engine thread started")
        engine = ExecutionEngine()

        while not self.stop_event.is_set():
            try:
                engine.check_and_execute_pending_orders()
            except Exception as e:
                logger.exception(f"Error in execution engine thread: {e}")

            # Sleep in small increments to allow quick shutdown
            for _ in range(self.check_interval):
                if self.stop_event.is_set():
                    break
                time.sleep(1)

        logger.debug("Sandbox Execution Engine thread stopped")

    def stop(self):
        """Signal the thread to stop"""
        self.stop_event.set()


def _is_websocket_proxy_healthy() -> bool:
    """Check if WebSocket proxy server is running and accepting connections"""
    import os
    import socket

    try:
        # Get WebSocket proxy host and port from environment
        ws_host = os.getenv("WEBSOCKET_HOST", "127.0.0.1")
        ws_port = int(os.getenv("WEBSOCKET_PORT", "8765"))

        # Try to connect to the WebSocket proxy server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)  # 2 second timeout
        result = sock.connect_ex((ws_host, ws_port))
        sock.close()

        if result == 0:
            logger.debug(f"WebSocket proxy is healthy at {ws_host}:{ws_port}")
            return True
        else:
            logger.debug(f"WebSocket proxy not reachable at {ws_host}:{ws_port}")
            return False
    except Exception as e:
        logger.debug(f"WebSocket proxy health check failed: {e}")
        return False


def start_execution_engine(engine_type: str = None):
    """
    Start the execution engine daemon thread
    Thread-safe - only one instance will run

    Args:
        engine_type: 'websocket', 'polling', or None (auto-detect)

    Engine selection priority:
    1. If engine_type param is provided, use it
    2. Otherwise, check SANDBOX_ENGINE_TYPE env var
    3. Default: 'websocket' (with automatic fallback to polling if unavailable)

    Fallback behavior:
    - Always tries WebSocket first (unless explicitly set to 'polling')
    - Automatically falls back to polling if WebSocket proxy is unhealthy
    - WebSocket engine has built-in fallback to polling if data becomes stale
    """
    global _execution_thread, _websocket_engine, _current_engine_type
    global _auto_upgrade_thread, _auto_upgrade_enabled

    with _thread_lock:
        # Check if any engine is already running
        if _execution_thread is not None and _execution_thread.is_alive():
            logger.debug("Polling execution engine already running")
            return True, "Execution engine already running (type: polling)"

        if _websocket_engine is not None:
            from sandbox.websocket_execution_engine import is_websocket_execution_engine_running

            if is_websocket_execution_engine_running():
                logger.debug("WebSocket execution engine already running")
                return True, "Execution engine already running (type: websocket)"

        # Determine engine type - default to websocket (with auto-fallback)
        if engine_type is None:
            engine_type = os.getenv("SANDBOX_ENGINE_TYPE", "websocket").lower()
            if os.getenv("SANDBOX_ENGINE_TYPE"):
                logger.info(f"Sandbox engine type forced by env: {engine_type}")

        logger.debug(f"Starting execution engine with type: {engine_type}")

        try:
            if engine_type == "websocket":
                # Try WebSocket engine first
                if _is_websocket_proxy_healthy():
                    from sandbox.websocket_execution_engine import (
                        get_websocket_execution_engine,
                        start_websocket_execution_engine,
                    )

                    success, message = start_websocket_execution_engine()
                    if success:
                        _websocket_engine = get_websocket_execution_engine()
                        _current_engine_type = "websocket"
                        logger.debug("WebSocket execution engine started (with built-in fallback)")
                        return True, "WebSocket execution engine started"
                    else:
                        logger.warning(
                            f"Failed to start WebSocket engine: {message}, falling back to polling"
                        )
                else:
                    logger.debug(
                        "WebSocket proxy not healthy at startup, falling back to polling engine"
                    )

                # Fallback to polling
                engine_type = "polling"
                _auto_upgrade_enabled = True

            # Start polling engine (default)
            _execution_thread = ExecutionEngineThread()
            _execution_thread.start()
            _current_engine_type = "polling"
            logger.debug("Polling execution engine started successfully")
            if _auto_upgrade_enabled:
                _start_websocket_upgrade_watcher()
            return True, "Polling execution engine started"

        except Exception as e:
            logger.exception(f"Failed to start execution engine: {e}")
            return False, f"Failed to start execution engine: {str(e)}"


def stop_execution_engine():
    """
    Stop the execution engine daemon thread gracefully.
    Handles both WebSocket and polling engine types.
    """
    global _execution_thread, _websocket_engine, _current_engine_type
    global _auto_upgrade_thread, _auto_upgrade_enabled

    with _thread_lock:
        stopped_any = False

        # Stop auto-upgrade watcher
        _stop_websocket_upgrade_watcher()

        # Stop WebSocket engine if running
        if _websocket_engine is not None:
            try:
                from sandbox.websocket_execution_engine import stop_websocket_execution_engine

                success, message = stop_websocket_execution_engine()
                if success:
                    logger.info("WebSocket execution engine stopped")
                    stopped_any = True
                _websocket_engine = None
            except Exception as e:
                logger.exception(f"Error stopping WebSocket execution engine: {e}")

        # Stop polling engine if running
        if _execution_thread is not None and _execution_thread.is_alive():
            try:
                logger.info("Stopping polling execution engine thread...")
                _execution_thread.stop()

                # Wait up to 10 seconds for thread to stop
                _execution_thread.join(timeout=10)

                if _execution_thread.is_alive():
                    logger.warning("Polling execution engine thread did not stop gracefully")
                else:
                    logger.info("Polling execution engine thread stopped successfully")
                    stopped_any = True

                _execution_thread = None
            except Exception as e:
                logger.exception(f"Error stopping polling execution engine: {e}")

        _current_engine_type = None
        _auto_upgrade_enabled = False

        if stopped_any:
            return True, "Execution engine stopped"
        else:
            return True, "Execution engine not running"


def _start_websocket_upgrade_watcher():
    """Start a background watcher to upgrade polling -> websocket when available."""
    global _auto_upgrade_thread, _auto_upgrade_stop_event

    if _auto_upgrade_thread and _auto_upgrade_thread.is_alive():
        return

    _auto_upgrade_stop_event.clear()

    def _watch():
        global _execution_thread, _websocket_engine, _current_engine_type
        while not _auto_upgrade_stop_event.is_set():
            time.sleep(5)
            if _auto_upgrade_stop_event.is_set():
                break
            if not _is_websocket_proxy_healthy():
                continue
            with _thread_lock:
                # Only upgrade if polling is running and websocket engine is not
                if _execution_thread is None or not _execution_thread.is_alive():
                    continue
                if _websocket_engine is not None:
                    continue
                try:
                    from sandbox.websocket_execution_engine import (
                        get_websocket_execution_engine,
                        start_websocket_execution_engine,
                    )

                    success, message = start_websocket_execution_engine()
                    if success:
                        _websocket_engine = get_websocket_execution_engine()
                        _current_engine_type = "websocket"
                        logger.debug("WebSocket execution engine started (auto-upgrade)")

                        # Stop polling engine after successful upgrade
                        _execution_thread.stop()
                        _execution_thread.join(timeout=10)
                        if _execution_thread.is_alive():
                            logger.warning("Polling execution engine did not stop after upgrade")
                        else:
                            logger.debug("Polling execution engine stopped after upgrade")
                        _execution_thread = None
                        break
                    else:
                        logger.warning(
                            f"Auto-upgrade failed to start WebSocket engine: {message}"
                        )
                except Exception as e:
                    logger.exception(f"Error during auto-upgrade to WebSocket engine: {e}")

    _auto_upgrade_thread = threading.Thread(
        target=_watch, daemon=True, name="SandboxEngine-WsUpgradeWatcher"
    )
    _auto_upgrade_thread.start()


def _stop_websocket_upgrade_watcher():
    """Stop the background websocket upgrade watcher."""
    global _auto_upgrade_thread, _auto_upgrade_stop_event

    _auto_upgrade_stop_event.set()
    if _auto_upgrade_thread and _auto_upgrade_thread.is_alive():
        _auto_upgrade_thread.join(timeout=5)
    _auto_upgrade_thread = None


def is_execution_engine_running():
    """Check if any execution engine is running"""
    global _execution_thread, _websocket_engine

    # Check polling engine
    if _execution_thread is not None and _execution_thread.is_alive():
        return True

    # Check WebSocket engine
    if _websocket_engine is not None:
        try:
            from sandbox.websocket_execution_engine import is_websocket_execution_engine_running

            if is_websocket_execution_engine_running():
                return True
        except Exception:
            pass

    return False


def get_execution_engine_status():
    """Get status information about the execution engine"""
    global _current_engine_type

    running = is_execution_engine_running()
    engine_type = _current_engine_type if running else None

    status = {
        "running": running,
        "engine_type": engine_type,
        "check_interval": int(get_config("order_check_interval", "5")),
        "configured_type": os.getenv("SANDBOX_ENGINE_TYPE", "polling"),
    }

    # Add thread info for polling engine
    if _execution_thread is not None:
        status["thread_name"] = _execution_thread.name
        status["thread_alive"] = _execution_thread.is_alive()

    # Add WebSocket engine info if available
    if _websocket_engine is not None:
        status["websocket_engine"] = True

    return status

```


---

# FILE: sandbox\fund_manager.py

```py
# sandbox/fund_manager.py
"""
Fund Manager - Handles simulated capital and margin calculations

Features:
- ₹10,000,000 (1 Crore) starting capital (configurable)
- Automatic reset via APScheduler on configured day/time (default: Sunday 00:00 IST)
- Leverage-based margin calculations
- Real-time available balance tracking

Auto-Reset:
- Runs as APScheduler background job (see squareoff_thread.py)
- Configurable day (Monday-Sunday) and time (HH:MM format)
- Resets all user funds to starting capital even if app was stopped during reset time
- Schedule automatically reloads when reset_day or reset_time config is changed
"""

import os
import sys
import threading
from datetime import datetime, timedelta
from decimal import Decimal

import pytz

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.sandbox_db import (
    SandboxFunds,
    SandboxHoldings,
    SandboxPositions,
    db_session,
    get_config,
)
from database.token_db import get_symbol_info
from utils.logging import get_logger
from utils.symbol_utils import is_future, is_option

logger = get_logger(__name__)


class FundManager:
    """Manages sandbox funds for sandbox mode"""

    # Class-level lock for thread safety across all fund operations.
    # RLock (reentrant) is required because guarded methods call
    # _ensure_funds_initialized() -> initialize_funds(), which re-acquires
    # the same lock on the same thread.
    _lock = threading.RLock()

    def __init__(self, user_id):
        self.user_id = user_id
        self.starting_capital = Decimal(get_config("starting_capital", "10000000.00"))

    def initialize_funds(self):
        """Initialize funds for a new user"""
        with self._lock:
            try:
                # Check if user already has funds
                funds = SandboxFunds.query.filter_by(user_id=self.user_id).first()

                if not funds:
                    # Create new fund account
                    funds = SandboxFunds(
                        user_id=self.user_id,
                        total_capital=self.starting_capital,
                        available_balance=self.starting_capital,
                        used_margin=Decimal("0.00"),
                        realized_pnl=Decimal("0.00"),
                        today_realized_pnl=Decimal("0.00"),
                        unrealized_pnl=Decimal("0.00"),
                        total_pnl=Decimal("0.00"),
                        last_reset_date=datetime.now(pytz.timezone("Asia/Kolkata")),
                        reset_count=0,
                    )
                    db_session.add(funds)
                    db_session.commit()
                    logger.info(
                        f"Initialized funds for user {self.user_id} with ₹{self.starting_capital}"
                    )
                    return True, "Funds initialized successfully"
                else:
                    logger.debug(f"User {self.user_id} already has funds initialized")
                    return True, "Funds already initialized"

            except Exception as e:
                db_session.rollback()
                logger.exception(f"Error initializing funds for user {self.user_id}: {e}")
                return False, f"Error initializing funds: {str(e)}"

    def get_funds(self):
        """Get current fund status for user"""
        try:
            funds = SandboxFunds.query.filter_by(user_id=self.user_id).first()

            if not funds:
                # Initialize funds if not exists
                success, message = self.initialize_funds()
                if not success:
                    return None

                funds = SandboxFunds.query.filter_by(user_id=self.user_id).first()

            # Check if reset is needed
            self._check_and_reset_funds(funds)

            # Return fund details
            return {
                "availablecash": float(funds.available_balance),
                "collateral": 0.00,  # No collateral in sandbox
                "m2munrealized": float(funds.unrealized_pnl),
                "m2mrealized": float(
                    funds.today_realized_pnl or 0
                ),  # Today's realized P&L (resets daily)
                "total_realized_pnl": float(funds.realized_pnl),  # All-time realized P&L
                "today_realized_pnl": float(funds.today_realized_pnl or 0),
                "utiliseddebits": float(funds.used_margin),
                "grossexposure": float(funds.used_margin),
                "totalpnl": float(funds.total_pnl),
                "last_reset": funds.last_reset_date.strftime("%Y-%m-%d %H:%M:%S"),
                "reset_count": funds.reset_count,
            }

        except Exception as e:
            logger.exception(f"Error getting funds for user {self.user_id}: {e}")
            return None

    def _check_and_reset_funds(self, funds):
        """Check if funds need to be reset (every Sunday at midnight IST)"""
        try:
            # Check if auto-reset is disabled
            reset_day = get_config("reset_day", "Never")
            if reset_day.lower() == "never":
                return  # Skip reset check entirely

            ist = pytz.timezone("Asia/Kolkata")
            now = datetime.now(ist)
            last_reset = funds.last_reset_date

            # Make last_reset timezone aware if it isn't
            if last_reset.tzinfo is None:
                last_reset = ist.localize(last_reset)

            # Check if it's the configured reset day and we haven't reset today
            reset_time_str = get_config("reset_time", "00:00")

            if now.strftime("%A") == reset_day:
                reset_hour, reset_minute = map(int, reset_time_str.split(":"))
                reset_time_today = now.replace(
                    hour=reset_hour, minute=reset_minute, second=0, microsecond=0
                )

                # If current time is past reset time and last reset was before today's reset time
                if now >= reset_time_today and last_reset < reset_time_today:
                    self._reset_funds(funds)

        except Exception as e:
            logger.exception(f"Error checking fund reset for user {self.user_id}: {e}")

    def _reset_funds(self, funds):
        """Reset funds to starting capital"""
        with self._lock:
            try:
                logger.info(f"Resetting funds for user {self.user_id}")

                # Reset all fund values
                funds.total_capital = self.starting_capital
                funds.available_balance = self.starting_capital
                funds.used_margin = Decimal("0.00")
                funds.realized_pnl = Decimal("0.00")
                funds.today_realized_pnl = Decimal("0.00")
                funds.unrealized_pnl = Decimal("0.00")
                funds.total_pnl = Decimal("0.00")
                funds.last_reset_date = datetime.now(pytz.timezone("Asia/Kolkata"))
                funds.reset_count += 1

                db_session.commit()

                # Clear all positions and holdings
                SandboxPositions.query.filter_by(user_id=self.user_id).delete()
                SandboxHoldings.query.filter_by(user_id=self.user_id).delete()
                db_session.commit()

                logger.info(
                    f"Funds reset successfully for user {self.user_id} (Reset #{funds.reset_count})"
                )

            except Exception as e:
                db_session.rollback()
                logger.exception(f"Error resetting funds for user {self.user_id}: {e}")

    def _ensure_funds_initialized(self):
        """Ensure funds are initialized for the user, creating them if needed.

        Returns:
            SandboxFunds or None: The funds record, or None if initialization failed.
        """
        funds = SandboxFunds.query.filter_by(user_id=self.user_id).first()
        if not funds:
            logger.info(f"Auto-initializing funds for user {self.user_id}")
            success, message = self.initialize_funds()
            if not success:
                logger.error(f"Failed to auto-initialize funds for user {self.user_id}: {message}")
                return None
            funds = SandboxFunds.query.filter_by(user_id=self.user_id).first()
        return funds

    def check_margin_available(self, required_margin):
        """Check if user has sufficient margin available"""
        try:
            funds = self._ensure_funds_initialized()

            if not funds:
                return False, "Funds not initialized"

            required_margin = Decimal(str(required_margin))

            if funds.available_balance >= required_margin:
                return True, "Sufficient margin available"
            else:
                shortage = required_margin - funds.available_balance
                return (
                    False,
                    f"Insufficient funds. Required: ₹{required_margin}, Available: ₹{funds.available_balance}, Shortage: ₹{shortage}",
                )

        except Exception as e:
            logger.exception(f"Error checking margin for user {self.user_id}: {e}")
            return False, f"Error checking margin: {str(e)}"

    def block_margin(self, amount, description=""):
        """Block margin for a trade"""
        with self._lock:
            try:
                funds = self._ensure_funds_initialized()

                if not funds:
                    return False, "Funds not initialized"

                amount = Decimal(str(amount))

                if funds.available_balance < amount:
                    return (
                        False,
                        f"Insufficient funds. Required: ₹{amount}, Available: ₹{funds.available_balance}",
                    )

                # Block the margin
                funds.available_balance -= amount
                funds.used_margin += amount

                db_session.commit()

                logger.info(f"Blocked ₹{amount} margin for user {self.user_id}. {description}")
                return True, f"Margin blocked: ₹{amount}"

            except Exception as e:
                db_session.rollback()
                logger.exception(f"Error blocking margin for user {self.user_id}: {e}")
                return False, f"Error blocking margin: {str(e)}"

    def release_margin(self, amount, realized_pnl=0, description=""):
        """Release blocked margin and update P&L"""
        with self._lock:
            try:
                funds = self._ensure_funds_initialized()

                if not funds:
                    return False, "Funds not initialized"

                amount = Decimal(str(amount))
                realized_pnl = Decimal(str(realized_pnl))

                # Release the margin
                funds.used_margin -= amount
                funds.available_balance += amount

                # Add realized P&L (all-time)
                funds.available_balance += realized_pnl
                funds.realized_pnl += realized_pnl
                # Add to today's realized P&L (resets daily at session boundary)
                funds.today_realized_pnl = (
                    funds.today_realized_pnl or Decimal("0.00")
                ) + realized_pnl
                funds.total_pnl = funds.realized_pnl + funds.unrealized_pnl

                db_session.commit()

                logger.info(
                    f"Released ₹{amount} margin for user {self.user_id}. Realized P&L: ₹{realized_pnl}. {description}"
                )
                return True, f"Margin released: ₹{amount}, P&L: ₹{realized_pnl}"

            except Exception as e:
                db_session.rollback()
                logger.exception(f"Error releasing margin for user {self.user_id}: {e}")
                return False, f"Error releasing margin: {str(e)}"

    def transfer_margin_to_holdings(self, amount, description=""):
        """
        Transfer margin to holdings during T+1 settlement
        Reduces used_margin without crediting available_balance
        (the money is now represented in holdings value, not available cash)
        """
        with self._lock:
            try:
                funds = self._ensure_funds_initialized()

                if not funds:
                    return False, "Funds not initialized"

                amount = Decimal(str(amount))

                # Reduce used margin (release from used_margin)
                # But do NOT credit available_balance - money is now in holdings
                funds.used_margin -= amount

                db_session.commit()

                logger.debug(
                    f"Transferred ₹{amount} margin to holdings for user {self.user_id}. {description}"
                )
                return True, f"Margin transferred to holdings: ₹{amount}"

            except Exception as e:
                db_session.rollback()
                logger.exception(f"Error transferring margin to holdings for user {self.user_id}: {e}")
                return False, f"Error transferring margin to holdings: {str(e)}"

    def credit_sale_proceeds(self, amount, description=""):
        """
        Credit sale proceeds from selling CNC holdings
        Increases available_balance when holdings are sold
        """
        with self._lock:
            try:
                funds = self._ensure_funds_initialized()

                if not funds:
                    return False, "Funds not initialized"

                amount = Decimal(str(amount))

                # Credit sale proceeds to available balance
                funds.available_balance += amount

                db_session.commit()

                logger.info(
                    f"Credited ₹{amount} sale proceeds for user {self.user_id}. {description}"
                )
                return True, f"Sale proceeds credited: ₹{amount}"

            except Exception as e:
                db_session.rollback()
                logger.exception(f"Error crediting sale proceeds for user {self.user_id}: {e}")
                return False, f"Error crediting sale proceeds: {str(e)}"

    def update_unrealized_pnl(self, unrealized_pnl):
        """Update unrealized P&L from open positions"""
        with self._lock:
            try:
                funds = self._ensure_funds_initialized()

                if not funds:
                    return False, "Funds not initialized"

                unrealized_pnl = Decimal(str(unrealized_pnl))

                funds.unrealized_pnl = unrealized_pnl
                funds.total_pnl = funds.realized_pnl + funds.unrealized_pnl

                db_session.commit()

                return True, "Unrealized P&L updated"

            except Exception as e:
                db_session.rollback()
                logger.exception(f"Error updating unrealized P&L for user {self.user_id}: {e}")
                return False, f"Error updating unrealized P&L: {str(e)}"

    def calculate_margin_required(self, symbol, exchange, product, quantity, price, action=None):
        """Calculate margin required for a trade based on leverage rules"""
        try:
            quantity = abs(int(quantity))
            price = Decimal(str(price))

            # Get symbol info to determine instrument type (from cache)
            symbol_obj = get_symbol_info(symbol, exchange)

            if not symbol_obj:
                logger.error(f"Symbol {symbol} not found on {exchange}")
                return None, "Symbol not found"

            # Calculate trade value (quantity × price)
            trade_value = quantity * price

            # Determine leverage based on action, product and symbol type
            leverage = self._get_leverage(exchange, product, symbol, action)

            if leverage is None:
                return None, "Unable to determine leverage"

            # Calculate margin (always use leverage-based calculation)
            margin = trade_value / Decimal(str(leverage))

            logger.debug(
                f"Margin for {symbol} {exchange} {product} {action}: ₹{margin} (Trade value: ₹{trade_value}, Leverage: {leverage}x)"
            )

            return margin, "Margin calculated successfully"

        except Exception as e:
            logger.exception(f"Error calculating margin: {e}")
            return None, f"Error calculating margin: {str(e)}"

    def _get_leverage(self, exchange, product, symbol, action=None):
        """Get leverage multiplier based on exchange, product, symbol type, and action"""
        try:
            # Equity exchanges
            if exchange in ["NSE", "BSE"]:
                if product == "MIS":
                    return Decimal(get_config("equity_mis_leverage", "5"))
                elif product == "CNC":
                    return Decimal(get_config("equity_cnc_leverage", "1"))
                else:  # NRML
                    return Decimal(get_config("equity_cnc_leverage", "1"))

            # Futures (NFO, BFO, MCX, CDS, BCD, NCDEX exchanges with FUT suffix)
            elif is_future(symbol, exchange):
                return Decimal(get_config("futures_leverage", "10"))

            # Options (NFO, BFO, MCX, CDS, BCD, NCDEX exchanges with CE/PE suffix)
            elif is_option(symbol, exchange):
                # Options use different leverage based on BUY vs SELL
                if action == "BUY":
                    return Decimal(get_config("option_buy_leverage", "1"))
                else:  # SELL
                    return Decimal(get_config("option_sell_leverage", "1"))

            # Default to 1x leverage
            return Decimal("1")

        except Exception as e:
            logger.exception(f"Error getting leverage: {e}")
            return Decimal("1")


def get_user_funds(user_id):
    """Helper function to get user funds"""
    fund_manager = FundManager(user_id)
    return fund_manager.get_funds()


def initialize_user_funds(user_id):
    """Helper function to initialize user funds"""
    fund_manager = FundManager(user_id)
    return fund_manager.initialize_funds()


def reset_all_user_funds():
    """
    Reset funds for all users (called by scheduler on configured reset day/time)
    This is the scheduled auto-reset function that runs independently of user actions.
    """
    try:
        logger.info("=== AUTO-RESET: Starting scheduled fund reset for all users ===")

        # Get all unique user IDs from funds table
        all_funds = SandboxFunds.query.all()

        if not all_funds:
            logger.info("No user funds to reset")
            return

        reset_count = 0
        for fund in all_funds:
            try:
                # Create FundManager for this user
                fm = FundManager(fund.user_id)

                # Call the internal reset function
                fm._reset_funds(fund)
                reset_count += 1

            except Exception as e:
                logger.exception(f"Error resetting funds for user {fund.user_id}: {e}")
                continue

        logger.info(f"=== AUTO-RESET: Successfully reset {reset_count} user fund accounts ===")

    except Exception as e:
        logger.exception(f"Error in scheduled auto-reset: {e}")


def reconcile_margin(user_id, auto_fix=True):
    """
    Reconcile used_margin in funds with actual margin blocked in positions.

    This function detects and optionally fixes margin discrepancies that can occur
    when position closures don't properly release margin.

    Args:
        user_id: User ID to reconcile
        auto_fix: If True, automatically fix discrepancies. If False, only report.

    Returns:
        tuple: (has_discrepancy: bool, discrepancy_amount: Decimal, message: str)
    """
    try:
        # Calculate total margin blocked across all open positions
        positions = SandboxPositions.query.filter_by(user_id=user_id).all()
        total_position_margin = sum(
            Decimal(str(pos.margin_blocked or 0))
            for pos in positions
            if pos.quantity != 0  # Only count open positions
        )

        # Get current used_margin from funds
        funds = SandboxFunds.query.filter_by(user_id=user_id).first()
        if not funds:
            return False, Decimal("0"), "No funds record found for user"

        current_used_margin = Decimal(str(funds.used_margin or 0))

        # Calculate discrepancy
        discrepancy = current_used_margin - total_position_margin

        if discrepancy == 0:
            return False, Decimal("0"), "No margin discrepancy detected"

        # Log the discrepancy
        logger.warning(
            f"Margin discrepancy detected for user {user_id}: "
            f"used_margin={current_used_margin}, position_margin={total_position_margin}, "
            f"discrepancy={discrepancy}"
        )

        if auto_fix:
            # Fix the discrepancy by adjusting used_margin and available_balance
            funds.used_margin = total_position_margin
            funds.available_balance += discrepancy  # Release the stuck margin
            db_session.commit()

            logger.info(
                f"Margin reconciled for user {user_id}: "
                f"Released {discrepancy} stuck margin, "
                f"new used_margin={total_position_margin}"
            )

            return True, discrepancy, f"Margin reconciled. Released {discrepancy} stuck margin."
        else:
            return (
                True,
                discrepancy,
                f"Discrepancy of {discrepancy} detected but not fixed (auto_fix=False)",
            )

    except Exception as e:
        logger.exception(f"Error reconciling margin for user {user_id}: {e}")
        db_session.rollback()
        return False, Decimal("0"), f"Error during reconciliation: {str(e)}"


def reconcile_all_users_margin():
    """
    Reconcile margin for all users.

    Returns:
        dict: Summary of reconciliation results
    """
    try:
        logger.info("=== Starting margin reconciliation for all users ===")

        all_funds = SandboxFunds.query.all()

        if not all_funds:
            logger.info("No user funds to reconcile")
            return {"users_checked": 0, "discrepancies_found": 0, "total_released": 0}

        users_checked = 0
        discrepancies_found = 0
        total_released = Decimal("0")

        for fund in all_funds:
            has_discrepancy, amount, message = reconcile_margin(fund.user_id, auto_fix=True)
            users_checked += 1

            if has_discrepancy:
                discrepancies_found += 1
                total_released += amount
                logger.info(f"User {fund.user_id}: {message}")

        logger.info(
            f"=== Margin reconciliation complete: "
            f"{users_checked} users checked, {discrepancies_found} discrepancies fixed, "
            f"total margin released: {total_released} ==="
        )

        return {
            "users_checked": users_checked,
            "discrepancies_found": discrepancies_found,
            "total_released": float(total_released),
        }

    except Exception as e:
        logger.exception(f"Error in margin reconciliation: {e}")
        return {"error": str(e)}


def validate_margin_consistency(user_id):
    """
    Validate that used_margin equals sum of position margins.
    Call this after position updates to detect issues early.

    Returns:
        tuple: (is_consistent: bool, discrepancy: Decimal)
    """
    try:
        # Calculate total margin blocked across all open positions
        positions = SandboxPositions.query.filter_by(user_id=user_id).all()
        total_position_margin = sum(
            Decimal(str(pos.margin_blocked or 0))
            for pos in positions
            if pos.quantity != 0  # Only count open positions
        )

        # Get current used_margin from funds
        funds = SandboxFunds.query.filter_by(user_id=user_id).first()
        if not funds:
            return True, Decimal("0")  # No funds = no discrepancy to report

        current_used_margin = Decimal(str(funds.used_margin or 0))
        discrepancy = current_used_margin - total_position_margin

        if discrepancy != 0:
            logger.warning(
                f"Margin inconsistency for user {user_id}: "
                f"used_margin={current_used_margin}, position_margin={total_position_margin}, "
                f"discrepancy={discrepancy}"
            )
            return False, discrepancy

        return True, Decimal("0")

    except Exception as e:
        logger.exception(f"Error validating margin for user {user_id}: {e}")
        return True, Decimal("0")  # Don't block operations on validation error

```


---

# FILE: sandbox\holdings_manager.py

```py
# sandbox/holdings_manager.py
"""
Holdings Manager - Handles T+1 settlement and holdings tracking

Features:
- T+1 settlement for CNC positions
- Automatic position-to-holdings conversion
- Holdings P&L tracking with MTM
- Holdings retrieval with live prices
- Daily settlement processing
"""

import os
import sys
from datetime import date, datetime
from decimal import Decimal

import pytz

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.sandbox_db import SandboxHoldings, SandboxPositions, db_session
from services.quotes_service import get_multiquotes, get_quotes
from utils.logging import get_logger

logger = get_logger(__name__)


class HoldingsManager:
    """Manages holdings and T+1 settlement"""

    def __init__(self, user_id):
        self.user_id = user_id

    def get_holdings(self, update_mtm=True):
        """
        Get all holdings for the user

        Args:
            update_mtm: bool - Whether to update MTM with live prices

        Returns:
            tuple: (success: bool, response: dict, status_code: int)
        """
        try:
            # Get all holdings, excluding zero-quantity holdings
            holdings = (
                SandboxHoldings.query.filter_by(user_id=self.user_id)
                .filter(SandboxHoldings.quantity != 0)
                .all()
            )

            if update_mtm:
                self._update_holdings_mtm(holdings)

            holdings_list = []
            total_pnl = Decimal("0.00")
            total_value = Decimal("0.00")
            total_investment = Decimal("0.00")

            for holding in holdings:
                pnl = Decimal(str(holding.pnl))
                total_pnl += pnl

                current_value = (
                    abs(holding.quantity) * holding.ltp if holding.ltp else Decimal("0.00")
                )
                total_value += current_value

                investment_value = abs(holding.quantity) * holding.average_price
                total_investment += investment_value

                holdings_list.append(
                    {
                        "symbol": holding.symbol,
                        "exchange": holding.exchange,
                        "product": "CNC",
                        "quantity": holding.quantity,
                        "average_price": float(holding.average_price),
                        "ltp": float(holding.ltp) if holding.ltp else 0.0,
                        "pnl": float(pnl),
                        "pnlpercent": float(holding.pnl_percent),
                        "current_value": float(current_value),
                        "settlement_date": holding.settlement_date.strftime("%Y-%m-%d"),
                    }
                )

            # Calculate overall P&L percentage
            pnl_percent = (
                (total_pnl / total_investment * 100) if total_investment > 0 else Decimal("0.00")
            )

            return (
                True,
                {
                    "status": "success",
                    "data": {
                        "holdings": holdings_list,
                        "statistics": {
                            "totalholdingvalue": float(total_value),
                            "totalinvvalue": float(total_investment),
                            "totalprofitandloss": float(total_pnl),
                            "totalpnlpercentage": float(pnl_percent),
                        },
                    },
                    "mode": "analyze",
                },
                200,
            )

        except Exception as e:
            logger.exception(f"Error getting holdings for user {self.user_id}: {e}")
            return (
                False,
                {
                    "status": "error",
                    "message": f"Error getting holdings: {str(e)}",
                    "mode": "analyze",
                },
                500,
            )

    def process_t1_settlement(self):
        """
        Process T+1 settlement - move CNC positions to holdings
        Should be called daily after market close
        """
        try:
            ist = pytz.timezone("Asia/Kolkata")
            today = datetime.now(ist).date()
            settlement_cutoff = datetime.combine(today, datetime.min.time())

            # Get all CNC positions from yesterday or earlier
            cnc_positions = (
                SandboxPositions.query.filter_by(user_id=self.user_id, product="CNC")
                .filter(SandboxPositions.created_at < settlement_cutoff)
                .all()
            )

            if not cnc_positions:
                logger.debug(f"No CNC positions to settle for user {self.user_id}")
                return True, "No positions to settle"

            settled_count = 0

            for position in cnc_positions:
                # Skip positions with zero quantity (already squared off)
                if position.quantity == 0:
                    db_session.delete(position)
                    logger.debug(
                        f"Deleted zero-quantity position: {position.symbol} {position.exchange}"
                    )
                    continue

                # Initialize fund manager for margin operations
                from sandbox.fund_manager import FundManager

                fund_manager = FundManager(self.user_id)

                # Check if holding already exists
                holding = SandboxHoldings.query.filter_by(
                    user_id=self.user_id, symbol=position.symbol, exchange=position.exchange
                ).first()

                if holding:
                    # Update existing holding
                    old_holding_qty = holding.quantity

                    if position.quantity > 0:
                        # Adding to holding (BUY)
                        # Calculate new average price
                        total_value = (abs(holding.quantity) * holding.average_price) + (
                            abs(position.quantity) * position.average_price
                        )
                        total_quantity = abs(holding.quantity) + abs(position.quantity)

                        holding.quantity += position.quantity
                        holding.average_price = (
                            total_value / total_quantity
                            if total_quantity > 0
                            else holding.average_price
                        )

                        # Transfer margin from used_margin to holdings (don't credit available_balance)
                        margin_amount = abs(position.quantity) * position.average_price
                        fund_manager.transfer_margin_to_holdings(
                            margin_amount, f"T+1 settlement: {position.symbol} BUY → Holdings"
                        )
                        logger.debug(
                            f"Added to holding: {position.symbol}, Qty: {holding.quantity}, Margin transferred: ₹{margin_amount}"
                        )

                    else:
                        # Reducing holding (SELL)
                        holding.quantity += position.quantity

                        # Credit sale proceeds to available balance
                        sale_proceeds = abs(position.quantity) * position.average_price
                        fund_manager.credit_sale_proceeds(
                            sale_proceeds, f"T+1 settlement: {position.symbol} SELL from Holdings"
                        )
                        logger.debug(
                            f"Reduced holding: {position.symbol}, Qty: {holding.quantity}, Sale proceeds: ₹{sale_proceeds}"
                        )

                    holding.ltp = position.ltp
                    holding.updated_at = datetime.now(ist)

                    # If holding quantity becomes 0 after update, delete the holding
                    if holding.quantity == 0:
                        db_session.delete(holding)
                        logger.debug(f"Deleted zero-quantity holding: {position.symbol}")

                else:
                    # Create new holding (BUY position becoming holding)
                    holding = SandboxHoldings(
                        user_id=self.user_id,
                        symbol=position.symbol,
                        exchange=position.exchange,
                        quantity=position.quantity,
                        average_price=position.average_price,
                        ltp=position.ltp or position.average_price,
                        pnl=Decimal("0.00"),
                        pnl_percent=Decimal("0.00"),
                        settlement_date=today,
                        created_at=datetime.now(ist),
                    )
                    db_session.add(holding)

                    # Transfer margin from used_margin to holdings (don't credit available_balance)
                    margin_amount = abs(position.quantity) * position.average_price
                    fund_manager.transfer_margin_to_holdings(
                        margin_amount, f"T+1 settlement: {position.symbol} → Holdings"
                    )
                    logger.debug(
                        f"Created new holding: {position.symbol}, Qty: {position.quantity}, Margin transferred: ₹{margin_amount}"
                    )

                # Delete the position after settling
                db_session.delete(position)
                settled_count += 1

            db_session.commit()

            logger.debug(f"Settled {settled_count} CNC positions for user {self.user_id}")

            # Notify UI so Positions and Holdings auto-refresh once T+1 lands.
            # Direct DB mutation (no order placement), so nothing else publishes
            # for this transition.
            if settled_count:
                try:
                    from events import SandboxT1SettlementEvent
                    from utils.event_bus import bus

                    bus.publish(
                        SandboxT1SettlementEvent(
                            mode="analyze",
                            api_type="sandbox.t1_settlement",
                            settled_users=1,
                            settled_positions=settled_count,
                        )
                    )
                except Exception as pub_err:
                    logger.debug(f"Failed to publish SandboxT1SettlementEvent: {pub_err}")

            return True, f"Settled {settled_count} positions"

        except Exception as e:
            db_session.rollback()
            logger.exception(f"Error processing T+1 settlement for user {self.user_id}: {e}")
            return False, f"Settlement error: {str(e)}"

    def _update_holdings_mtm(self, holdings):
        """Update MTM for all holdings with live quotes using batch multiquotes"""
        try:
            if not holdings:
                return

            # Get unique symbols as list of dicts for multiquotes
            symbols_to_fetch = []
            seen = set()
            for holding in holdings:
                key = (holding.symbol, holding.exchange)
                if key not in seen:
                    seen.add(key)
                    symbols_to_fetch.append({"symbol": holding.symbol, "exchange": holding.exchange})

            if not symbols_to_fetch:
                return

            # Fetch all quotes in a single batch call using multiquotes
            quote_cache = {}
            try:
                # Get any user's API key for fetching quotes
                from database.auth_db import ApiKeys, decrypt_token

                api_key_obj = ApiKeys.query.first()
                if api_key_obj:
                    api_key = decrypt_token(api_key_obj.api_key_encrypted)
                    success, response, status_code = get_multiquotes(
                        symbols=symbols_to_fetch, api_key=api_key
                    )

                    if success and "results" in response:
                        for result in response["results"]:
                            symbol = result.get("symbol")
                            exchange = result.get("exchange")
                            data = result.get("data")
                            if symbol and exchange and data:
                                quote_cache[(symbol, exchange)] = data
                    else:
                        logger.debug(f"Multiquotes returned no results: {response.get('message', 'Unknown error')}")
                else:
                    logger.warning("No API keys found for fetching multiquotes")
            except Exception as e:
                logger.exception(f"Error fetching multiquotes for holdings MTM: {e}")

            # Update MTM for each holding
            for holding in holdings:
                quote = quote_cache.get((holding.symbol, holding.exchange))
                if quote:
                    ltp = Decimal(str(quote.get("ltp", 0)))
                    if ltp > 0:
                        holding.ltp = ltp
                        holding.pnl = self._calculate_holding_pnl(
                            holding.quantity, holding.average_price, ltp
                        )
                        holding.pnl_percent = self._calculate_pnl_percent(
                            holding.average_price, ltp
                        )

            db_session.commit()

        except Exception as e:
            db_session.rollback()
            logger.exception(f"Error updating holdings MTM: {e}")

    def _calculate_holding_pnl(self, quantity, avg_price, ltp):
        """Calculate P&L for a holding"""
        try:
            quantity = Decimal(str(quantity))
            avg_price = Decimal(str(avg_price))
            ltp = Decimal(str(ltp))

            # Holdings are always long positions
            pnl = (ltp - avg_price) * abs(quantity)

            return pnl

        except Exception as e:
            logger.exception(f"Error calculating holding P&L: {e}")
            return Decimal("0.00")

    def _calculate_pnl_percent(self, avg_price, ltp):
        """Calculate P&L percentage"""
        try:
            avg_price = Decimal(str(avg_price))
            ltp = Decimal(str(ltp))

            if avg_price <= 0:
                return Decimal("0.00")

            pnl_percent = ((ltp - avg_price) / avg_price) * Decimal("100")

            return pnl_percent

        except Exception as e:
            logger.exception(f"Error calculating P&L percent: {e}")
            return Decimal("0.00")

    def _fetch_quote(self, symbol, exchange):
        """Fetch real-time quote for a symbol using API key"""
        try:
            # Get any user's API key for fetching quotes
            from database.auth_db import ApiKeys, decrypt_token

            api_key_obj = ApiKeys.query.first()

            if not api_key_obj:
                logger.warning("No API keys found for fetching quotes")
                return None

            # Decrypt the API key
            api_key = decrypt_token(api_key_obj.api_key_encrypted)

            # Use quotes service with API key authentication
            success, response, status_code = get_quotes(
                symbol=symbol, exchange=exchange, api_key=api_key
            )

            if success and "data" in response:
                return response["data"]
            else:
                return None

        except Exception as e:
            logger.exception(f"Error fetching quote for {symbol}: {e}")
            return None


def process_all_t1_settlements():
    """Process T+1 settlement for all users"""
    try:
        # Get all unique users with CNC positions
        ist = pytz.timezone("Asia/Kolkata")
        today = datetime.now(ist).date()
        settlement_cutoff = datetime.combine(today, datetime.min.time())

        positions = (
            SandboxPositions.query.filter_by(product="CNC")
            .filter(SandboxPositions.created_at < settlement_cutoff)
            .all()
        )

        if not positions:
            logger.info("No CNC positions to settle")
            return

        users = set(p.user_id for p in positions)
        logger.info(f"Processing T+1 settlement for {len(users)} users")

        settled_users = 0
        for user_id in users:
            hm = HoldingsManager(user_id)
            success, message = hm.process_t1_settlement()
            if success:
                settled_users += 1

        logger.info(f"T+1 settlement completed for {settled_users} users")

    except Exception as e:
        logger.exception(f"Error processing all T+1 settlements: {e}")


if __name__ == "__main__":
    """Run T+1 settlement processor"""
    logger.info("Starting T+1 Settlement Processor")

    from database.sandbox_db import init_db

    init_db()

    process_all_t1_settlements()
    logger.info("T+1 settlement processing completed")

```


---

# FILE: sandbox\order_manager.py

```py
# sandbox/order_manager.py
"""
Order Manager - Handles sandbox order placement and validation

Features:
- Order validation (symbol, quantity, price, etc.)
- Margin checking before order placement
- Order placement with unique order IDs
- Order modification and cancellation
- Support for all order types: MARKET, LIMIT, SL, SL-M
"""

import os
import sys
import time
import uuid
from datetime import datetime
from decimal import Decimal

import pytz

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.sandbox_db import SandboxOrders, SandboxPositions, SandboxTrades, db_session
from database.symbol import SymToken
from database.token_db import get_symbol_info
from sandbox.fund_manager import FundManager
from utils.constants import VALID_EXCHANGES
from utils.logging import get_logger
from utils.symbol_utils import is_future, is_option

logger = get_logger(__name__)


class OrderManager:
    """Manages sandbox orders for sandbox mode"""

    def __init__(self, user_id):
        self.user_id = user_id
        self.fund_manager = FundManager(user_id)

    def place_order(self, order_data, prefetched_quote=None):
        """
        Place a new order in sandbox mode

        Args:
            order_data: dict containing order parameters
                - symbol: str
                - exchange: str
                - action: str (BUY/SELL)
                - quantity: int
                - price: float (optional for MARKET orders)
                - trigger_price: float (optional for SL orders)
                - price_type: str (MARKET/LIMIT/SL/SL-M)
                - product: str (CNC/NRML/MIS)
                - strategy: str (optional)
            prefetched_quote: dict (optional) pre-fetched quote from multiquotes
                batch call, avoids per-order REST API calls in basket orders

        Returns:
            tuple: (success: bool, response: dict, status_code: int)
        """
        try:
            # Validate order data
            is_valid, validation_msg = self._validate_order(order_data)
            if not is_valid:
                return False, {"status": "error", "message": validation_msg, "mode": "analyze"}, 400

            # Extract order parameters
            symbol = order_data["symbol"]
            exchange = order_data["exchange"].upper()
            action = order_data["action"].upper()
            quantity = int(order_data["quantity"])
            price = Decimal(str(order_data.get("price", 0))) if order_data.get("price") else None
            trigger_price = (
                Decimal(str(order_data.get("trigger_price", 0)))
                if order_data.get("trigger_price")
                else None
            )
            price_type = order_data["price_type"].upper()
            product = order_data["product"].upper()
            strategy = order_data.get("strategy", "")

            # Drop fields that don't apply to this price_type so stale values from
            # the form (e.g. a leftover trigger_price after switching SL-M -> LIMIT)
            # cannot be stored or shown back in the orderbook.
            #   MARKET -> no price, no trigger
            #   LIMIT  -> price only
            #   SL     -> price + trigger
            #   SL-M   -> trigger only
            if price_type in ("MARKET", "SL-M"):
                price = None
            if price_type in ("MARKET", "LIMIT"):
                trigger_price = None

            # Get symbol info for lot size validation (from cache)
            symbol_obj = get_symbol_info(symbol, exchange)
            if not symbol_obj:
                return (
                    False,
                    {
                        "status": "error",
                        "message": f"Symbol {symbol} not found on {exchange}",
                        "mode": "analyze",
                    },
                    400,
                )

            # Validate lot size for F&O
            if exchange in ["NFO", "BFO", "CDS", "BCD", "MCX", "NCDEX", "CRYPTO"]:
                lot_size = symbol_obj.lotsize or 1
                if quantity % lot_size != 0:
                    return (
                        False,
                        {
                            "status": "error",
                            "message": f"Quantity must be in multiples of lot size {lot_size}",
                            "mode": "analyze",
                        },
                        400,
                    )

            # Validate MIS orders - reject if after square-off time but before market open
            # Exception: Allow orders that reduce/close existing positions
            if product == "MIS":
                from datetime import time as dt_time

                from sandbox.squareoff_manager import SquareOffManager

                som = SquareOffManager()
                square_off_time = som.square_off_times.get(exchange)

                if square_off_time:
                    ist = pytz.timezone("Asia/Kolkata")
                    now = datetime.now(ist)
                    current_time = now.time()

                    # Market opens at 9:00 AM IST
                    market_open_time = dt_time(9, 0)

                    # Check if we're in the blocked period
                    # Two scenarios:
                    # 1. After square-off time same day: e.g., 15:20 (after 15:15 square-off)
                    # 2. Before market open next day: e.g., 02:00 (before 09:00 market open)
                    is_blocked = False
                    if current_time >= square_off_time:
                        # After square-off time - block until next day
                        is_blocked = True
                    elif current_time < market_open_time:
                        # Before market open - still blocked from yesterday
                        is_blocked = True

                    if is_blocked:
                        # Check if this order will reduce/close an existing OPEN position
                        existing_position = (
                            SandboxPositions.query.filter_by(
                                user_id=self.user_id,
                                symbol=symbol,
                                exchange=exchange,
                                product=product,
                            )
                            .filter(SandboxPositions.quantity != 0)
                            .first()
                        )

                        # Allow if reducing existing position
                        # BUY reduces short position (negative qty), SELL reduces long position (positive qty)
                        is_reducing = False
                        if existing_position:
                            if action == "BUY" and existing_position.quantity < 0:
                                is_reducing = True  # Covering short
                            elif action == "SELL" and existing_position.quantity > 0:
                                is_reducing = True  # Closing long

                        # Block only if opening/increasing position, allow if closing/reducing
                        if not is_reducing:
                            return (
                                False,
                                {
                                    "status": "error",
                                    "message": f"MIS orders cannot be placed after square-off time ({square_off_time.strftime('%H:%M')} IST). Trading resumes at 09:00 AM IST.",
                                    "mode": "analyze",
                                },
                                400,
                            )

            # Track validation for CNC SELL orders
            cnc_sell_rejection_reason = None

            # Validate SELL orders based on product type
            # CNC (delivery) requires existing positions/holdings, MIS (intraday) allows short selling
            if action == "SELL":
                if product == "CNC":
                    # CNC SELL orders require existing long positions or holdings
                    # Check existing position
                    existing_position = SandboxPositions.query.filter_by(
                        user_id=self.user_id, symbol=symbol, exchange=exchange, product=product
                    ).first()

                    # Check holdings (T+1 settled positions)
                    from database.sandbox_db import SandboxHoldings

                    existing_holdings = SandboxHoldings.query.filter_by(
                        user_id=self.user_id, symbol=symbol, exchange=exchange
                    ).first()

                    # Calculate total available quantity
                    position_qty = (
                        existing_position.quantity
                        if existing_position and existing_position.quantity > 0
                        else 0
                    )
                    holdings_qty = (
                        existing_holdings.quantity
                        if existing_holdings and existing_holdings.quantity > 0
                        else 0
                    )
                    total_available = position_qty + holdings_qty

                    if total_available <= 0:
                        cnc_sell_rejection_reason = f"Cannot sell {symbol} in CNC. No positions or holdings available. CNC (delivery) requires existing shares. Use MIS for intraday short selling."
                    elif quantity > total_available:
                        cnc_sell_rejection_reason = f"Cannot sell {quantity} shares of {symbol} in CNC. Only {total_available} shares available (Position: {position_qty}, Holdings: {holdings_qty})"
                    else:
                        logger.info(
                            f"CNC SELL validation passed: {symbol} - Available: {total_available} (Pos: {position_qty}, Hold: {holdings_qty}), Requested: {quantity}"
                        )

                elif product == "MIS":
                    # MIS allows short selling (negative positions) since it's intraday
                    logger.info(f"MIS SELL order: {symbol} - Short selling allowed for intraday")

            # Determine price for margin calculation based on order type
            margin_calculation_price = None
            cached_quote = None  # Cache quote for reuse in immediate execution

            # Check for existing position early (needed for fallback pricing)
            temp_existing_position = SandboxPositions.query.filter_by(
                user_id=self.user_id, symbol=symbol, exchange=exchange, product=product
            ).first()

            if price_type == "MARKET":
                # For MARKET orders, fetch current LTP for margin calculation
                # We need a valid price - reject order if unavailable (no hardcoded fallback)
                quote_fetch_success = False

                # Attempt 0: Use pre-fetched quote from batch call (basket orders)
                if prefetched_quote and prefetched_quote.get("ltp"):
                    try:
                        ltp_val = Decimal(str(prefetched_quote["ltp"]))
                        if ltp_val > 0:
                            margin_calculation_price = ltp_val
                            cached_quote = prefetched_quote
                            logger.debug(
                                f"Using pre-fetched LTP {margin_calculation_price} for MARKET order margin calculation"
                            )
                            quote_fetch_success = True
                    except Exception as e:
                        logger.debug(f"Pre-fetched quote unusable: {e}")

                # Attempt 1: Fetch live quote with retry
                if not quote_fetch_success:
                    for attempt in range(3):
                        try:
                            from sandbox.execution_engine import ExecutionEngine

                            engine = ExecutionEngine()
                            quote = engine._fetch_quote(symbol, exchange)
                            if quote and quote.get("ltp") and Decimal(str(quote["ltp"])) > 0:
                                margin_calculation_price = Decimal(str(quote["ltp"]))
                                cached_quote = quote  # Cache for immediate execution
                                logger.debug(
                                    f"Using LTP {margin_calculation_price} for MARKET order margin calculation"
                                )
                                quote_fetch_success = True
                                break
                        except Exception as e:
                            logger.debug(f"Quote fetch attempt {attempt + 1} failed: {e}")

                        # Wait before retry (0.3s, 0.6s, 0.9s)
                        if attempt < 2:
                            time.sleep(0.3 * (attempt + 1))

                # Attempt 2: Use position's last known LTP as fallback
                if not quote_fetch_success:
                    if (
                        temp_existing_position
                        and temp_existing_position.ltp
                        and temp_existing_position.ltp > 0
                    ):
                        margin_calculation_price = temp_existing_position.ltp
                        logger.warning(
                            f"Quote fetch failed, using last known price {margin_calculation_price} for {symbol}"
                        )
                        quote_fetch_success = True

                # Attempt 3: Reject order if no valid price available
                if not quote_fetch_success:
                    logger.error(
                        f"Cannot place MARKET order for {symbol} - unable to fetch current price"
                    )
                    return (
                        False,
                        {
                            "status": "error",
                            "message": f"Cannot place MARKET order for {symbol} - unable to fetch current price. Please try again later or use LIMIT order with a specific price.",
                            "mode": "analyze",
                        },
                        400,
                    )

            elif price_type == "LIMIT":
                # For LIMIT orders, use the limit price for margin calculation
                margin_calculation_price = price
                logger.debug(f"Using LIMIT price {margin_calculation_price} for margin calculation")

                # Fetch current LTP to check if this LIMIT order is marketable
                # Marketable = can be executed immediately at market price
                # Use pre-fetched quote if available, otherwise REST API with retry
                marketability_checked = False

                if prefetched_quote and prefetched_quote.get("ltp"):
                    try:
                        current_ltp = Decimal(str(prefetched_quote["ltp"]))
                        if current_ltp > 0:
                            if (action == "BUY" and current_ltp <= price) or (
                                action == "SELL" and current_ltp >= price
                            ):
                                cached_quote = prefetched_quote
                                logger.info(
                                    f"LIMIT order is marketable (pre-fetched): {action} limit={price}, LTP={current_ltp}"
                                )
                            marketability_checked = True
                    except Exception as e:
                        logger.debug(f"Pre-fetched marketability check failed: {e}")

                if not marketability_checked:
                    for attempt in range(3):
                        try:
                            from sandbox.execution_engine import ExecutionEngine

                            engine = ExecutionEngine()
                            quote = engine._fetch_quote(symbol, exchange)
                            if quote and quote.get("ltp") and Decimal(str(quote["ltp"])) > 0:
                                current_ltp = Decimal(str(quote["ltp"]))
                                if (action == "BUY" and current_ltp <= price) or (
                                    action == "SELL" and current_ltp >= price
                                ):
                                    cached_quote = quote
                                    logger.info(
                                        f"LIMIT order is marketable: {action} limit={price}, LTP={current_ltp}"
                                    )
                                break
                        except Exception as e:
                            logger.debug(f"Marketability check attempt {attempt + 1} failed: {e}")

                        if attempt < 2:
                            time.sleep(0.3 * (attempt + 1))

            elif price_type in ["SL", "SL-M"]:
                # For SL/SL-M orders, use trigger price for margin calculation
                # This represents the worst-case price at which order will be triggered
                margin_calculation_price = trigger_price
                logger.debug(
                    f"Using trigger price {margin_calculation_price} for {price_type} order margin calculation"
                )

                # Fetch current LTP to check if trigger is already met
                # If so, execute immediately instead of waiting for next tick
                # Use pre-fetched quote if available, otherwise REST API with retry
                trigger_checked = False

                if prefetched_quote and prefetched_quote.get("ltp"):
                    try:
                        current_ltp = Decimal(str(prefetched_quote["ltp"]))
                        if current_ltp > 0:
                            trigger_met = False
                            if action == "BUY" and current_ltp >= trigger_price:
                                trigger_met = True
                            elif action == "SELL" and current_ltp <= trigger_price:
                                trigger_met = True

                            if trigger_met:
                                if price_type == "SL-M":
                                    cached_quote = prefetched_quote
                                    logger.info(
                                        f"SL-M trigger already met (pre-fetched): {action} trigger={trigger_price}, LTP={current_ltp}"
                                    )
                                elif price_type == "SL":
                                    if (action == "BUY" and current_ltp <= price) or (
                                        action == "SELL" and current_ltp >= price
                                    ):
                                        cached_quote = prefetched_quote
                                        logger.info(
                                            f"SL trigger+limit already met (pre-fetched): {action} trigger={trigger_price}, limit={price}, LTP={current_ltp}"
                                        )
                            trigger_checked = True
                    except Exception as e:
                        logger.debug(f"Pre-fetched SL trigger check failed: {e}")

                if not trigger_checked:
                    for attempt in range(3):
                        try:
                            from sandbox.execution_engine import ExecutionEngine

                            engine = ExecutionEngine()
                            quote = engine._fetch_quote(symbol, exchange)
                            if quote and quote.get("ltp") and Decimal(str(quote["ltp"])) > 0:
                                current_ltp = Decimal(str(quote["ltp"]))
                                trigger_met = False

                                if action == "BUY" and current_ltp >= trigger_price:
                                    trigger_met = True
                                elif action == "SELL" and current_ltp <= trigger_price:
                                    trigger_met = True

                                if trigger_met:
                                    if price_type == "SL-M":
                                        cached_quote = quote
                                        logger.info(
                                            f"SL-M order trigger already met: {action} trigger={trigger_price}, LTP={current_ltp}"
                                        )
                                    elif price_type == "SL":
                                        if (action == "BUY" and current_ltp <= price) or (
                                            action == "SELL" and current_ltp >= price
                                        ):
                                            cached_quote = quote
                                            logger.info(
                                                f"SL order trigger+limit already met: {action} trigger={trigger_price}, limit={price}, LTP={current_ltp}"
                                            )
                                break
                        except Exception as e:
                            logger.debug(f"SL trigger check attempt {attempt + 1} failed: {e}")

                        if attempt < 2:
                            time.sleep(0.3 * (attempt + 1))

            # Validate that we have a valid price for margin calculation
            if not margin_calculation_price or margin_calculation_price <= 0:
                return (
                    False,
                    {
                        "status": "error",
                        "message": f"Invalid price for margin calculation. Please provide valid price/trigger_price for {price_type} order",
                        "mode": "analyze",
                    },
                    400,
                )

            # Calculate required margin using the appropriate price
            margin_required, margin_msg = self.fund_manager.calculate_margin_required(
                symbol, exchange, product, quantity, margin_calculation_price, action
            )

            if margin_required is None:
                return (
                    False,
                    {
                        "status": "error",
                        "message": f"Unable to calculate margin: {margin_msg}",
                        "mode": "analyze",
                    },
                    400,
                )

            # Check if this order will close/reduce/reverse an existing position
            existing_position = SandboxPositions.query.filter_by(
                user_id=self.user_id, symbol=symbol, exchange=exchange, product=product
            ).first()

            # Calculate margin to block based on position impact
            actual_margin_to_block = margin_required

            if existing_position and existing_position.quantity != 0:
                # Check if order is opposite to position direction
                if (existing_position.quantity > 0 and action == "SELL") or (
                    existing_position.quantity < 0 and action == "BUY"
                ):
                    # Opposite direction - will reduce or reverse position
                    existing_qty = abs(existing_position.quantity)
                    order_qty = quantity

                    if order_qty <= existing_qty:
                        # Order will only reduce/close position - no new margin needed
                        actual_margin_to_block = Decimal("0")
                        logger.info("Order will reduce position - no margin required")
                    else:
                        # Order will reverse position - only block margin for excess quantity
                        excess_qty = order_qty - existing_qty
                        actual_margin_to_block, _ = self.fund_manager.calculate_margin_required(
                            symbol, exchange, product, excess_qty, margin_calculation_price, action
                        )
                        logger.info(
                            f"Order will reverse position - margin for {excess_qty} shares: ₹{actual_margin_to_block}"
                        )

            # Check margin availability and block margin if needed
            # Margin is required for:
            # - All BUY orders (long positions)
            # - SELL orders for options (selling options requires margin)
            # - SELL orders for futures (short selling futures requires margin)
            # - SELL orders for equity in MIS (intraday short selling requires margin)
            # - SELL orders for equity in NRML (if short selling is allowed)
            # Note: SELL orders for equity in CNC don't need margin blocking (selling owned shares)
            should_block_margin = False

            if action == "BUY":
                # All BUY orders require margin
                should_block_margin = True
            elif action == "SELL":
                if is_option(symbol, exchange):
                    # Selling options requires margin
                    should_block_margin = True
                elif is_future(symbol, exchange):
                    # Short selling futures requires margin
                    should_block_margin = True
                elif product in ["MIS", "NRML"]:
                    # Intraday/margin short selling of equity requires margin
                    should_block_margin = True
                # CNC SELL doesn't need margin (selling owned shares)

            if should_block_margin:
                if actual_margin_to_block > 0:
                    # Check and block margin only for new exposure
                    can_trade, margin_check_msg = self.fund_manager.check_margin_available(
                        actual_margin_to_block
                    )
                    if not can_trade:
                        return (
                            False,
                            {"status": "error", "message": margin_check_msg, "mode": "analyze"},
                            400,
                        )

                    # Block margin
                    success, block_msg = self.fund_manager.block_margin(
                        actual_margin_to_block, f"Order: {symbol} {action} {quantity}"
                    )
                    if not success:
                        return (
                            False,
                            {"status": "error", "message": block_msg, "mode": "analyze"},
                            400,
                        )
                    logger.info(
                        f"Blocked margin ₹{actual_margin_to_block} for {symbol} {action} {quantity} order"
                    )
                else:
                    logger.info(
                        f"No margin to block for {symbol} {action} - will reduce existing position"
                    )
            else:
                logger.info(
                    f"No margin blocking required for {symbol} {action} {product} (CNC SELL of owned shares)"
                )

            # Generate unique order ID
            orderid = self._generate_order_id()

            # Check if order should be rejected (CNC SELL validation failed)
            if cnc_sell_rejection_reason:
                # Create rejected order for audit trail
                # For MARKET orders, store the LTP we used for margin calculation as reference price
                order_price_to_store = margin_calculation_price if price_type == "MARKET" else price

                order = SandboxOrders(
                    orderid=orderid,
                    user_id=self.user_id,
                    strategy=strategy,
                    symbol=symbol,
                    exchange=exchange,
                    action=action,
                    quantity=quantity,
                    price=order_price_to_store,
                    trigger_price=trigger_price,
                    price_type=price_type,
                    product=product,
                    order_status="rejected",
                    average_price=None,
                    filled_quantity=0,
                    pending_quantity=0,
                    rejection_reason=cnc_sell_rejection_reason,
                    margin_blocked=Decimal("0"),  # No margin blocked for rejected orders
                    order_timestamp=datetime.now(pytz.timezone("Asia/Kolkata")),
                )

                db_session.add(order)
                db_session.commit()

                logger.info(
                    f"Order rejected: {orderid} - {symbol} {action} {quantity} - Reason: {cnc_sell_rejection_reason}"
                )

                return (
                    False,
                    {
                        "status": "error",
                        "orderid": orderid,
                        "message": cnc_sell_rejection_reason,
                        "mode": "analyze",
                    },
                    400,
                )

            # Create order record (for accepted orders)
            # For MARKET orders, store the LTP we used for margin calculation as reference price
            order_price_to_store = margin_calculation_price if price_type == "MARKET" else price

            order = SandboxOrders(
                orderid=orderid,
                user_id=self.user_id,
                strategy=strategy,
                symbol=symbol,
                exchange=exchange,
                action=action,
                quantity=quantity,
                price=order_price_to_store,
                trigger_price=trigger_price,
                price_type=price_type,
                product=product,
                order_status="open",
                average_price=None,
                filled_quantity=0,
                pending_quantity=quantity,
                rejection_reason=None,
                margin_blocked=actual_margin_to_block,  # Store exact margin blocked
                order_timestamp=datetime.now(pytz.timezone("Asia/Kolkata")),
            )

            db_session.add(order)
            db_session.commit()

            logger.info(f"Order placed: {orderid} - {symbol} {action} {quantity} @ {price_type}")

            # Execute orders immediately when conditions are already met
            # MARKET: always immediate, LIMIT: if marketable, SL/SL-M: if trigger already met
            # This must happen BEFORE notifying the WebSocket engine to prevent
            # duplicate execution (WebSocket tick arriving before immediate execution completes)
            if price_type == "MARKET" or (cached_quote and price_type in ["LIMIT", "SL", "SL-M"]):
                try:
                    from sandbox.execution_engine import ExecutionEngine

                    exec_engine = ExecutionEngine()

                    # Use cached quote from earlier check (already fetched above)
                    if cached_quote:
                        ltp = Decimal(str(cached_quote.get("ltp", 0)))

                        if price_type == "LIMIT":
                            # Marketable LIMIT: fill at LTP (market price), not limit price
                            # In real exchanges, a marketable limit order gets price improvement
                            # e.g., BUY LIMIT 1500, LTP 1417 → fills at 1417
                            if ltp > 0:
                                exec_engine._execute_order(order, ltp)
                                logger.info(
                                    f"Marketable limit order {orderid} executed at LTP {ltp} (limit was {price})"
                                )
                            else:
                                logger.warning(
                                    f"Invalid LTP in cached quote for {symbol}, order remains open"
                                )
                        elif price_type in ["SL", "SL-M"]:
                            # SL/SL-M with trigger already met: execute at LTP
                            if ltp > 0:
                                exec_engine._execute_order(order, ltp)
                                logger.info(
                                    f"{price_type} order {orderid} executed at LTP {ltp} (trigger already met)"
                                )
                            else:
                                logger.warning(
                                    f"Invalid LTP in cached quote for {symbol}, order remains open"
                                )
                        else:
                            # MARKET order: process normally (fills at bid/ask or LTP)
                            exec_engine._process_order(order, cached_quote)
                            logger.info(
                                f"Market order {orderid} executed immediately"
                            )
                    else:
                        logger.warning(
                            f"Could not fetch quote for {symbol} on {exchange}, order remains open"
                        )
                except Exception as e:
                    logger.exception(f"Error executing order immediately: {e}")
                    # Order remains in 'open' status if execution fails

            # Only notify WebSocket execution engine for orders that are STILL open
            # (not already executed immediately above). This prevents the WebSocket
            # engine from re-executing an already completed order.
            db_session.refresh(order)
            if order.order_status == "open":
                try:
                    from sandbox.websocket_execution_engine import (
                        get_websocket_execution_engine,
                        is_websocket_execution_engine_running,
                    )

                    if is_websocket_execution_engine_running():
                        ws_engine = get_websocket_execution_engine()
                        ws_engine.notify_order_placed(order)
                except Exception as e:
                    logger.debug(f"WebSocket execution engine notification skipped: {e}")

            return True, {"status": "success", "orderid": orderid, "mode": "analyze"}, 200

        except Exception as e:
            db_session.rollback()
            logger.exception(f"Error placing order: {e}")
            return (
                False,
                {"status": "error", "message": f"Error placing order: {str(e)}", "mode": "analyze"},
                500,
            )

    def modify_order(self, orderid, new_data):
        """
        Modify an existing open order

        Args:
            orderid: str - Order ID to modify
            new_data: dict - New order parameters (quantity, price, trigger_price)

        Returns:
            tuple: (success: bool, response: dict, status_code: int)
        """
        try:
            # Get existing order
            order = SandboxOrders.query.filter_by(orderid=orderid, user_id=self.user_id).first()

            if not order:
                return (
                    False,
                    {"status": "error", "message": f"Order {orderid} not found", "mode": "analyze"},
                    404,
                )

            if order.order_status != "open":
                return (
                    False,
                    {
                        "status": "error",
                        "message": f"Cannot modify order in {order.order_status} status",
                        "mode": "analyze",
                    },
                    400,
                )

            # Update order parameters
            if "quantity" in new_data:
                new_quantity = int(new_data["quantity"])
                # Validate lot size (from cache)
                symbol_obj = get_symbol_info(order.symbol, order.exchange)
                if symbol_obj and order.exchange in ["NFO", "BFO", "CDS", "BCD", "MCX", "NCDEX", "CRYPTO"]:
                    lot_size = symbol_obj.lotsize or 1
                    if new_quantity % lot_size != 0:
                        return (
                            False,
                            {
                                "status": "error",
                                "message": f"Quantity must be in multiples of lot size {lot_size}",
                                "mode": "analyze",
                            },
                            400,
                        )
                order.quantity = new_quantity
                order.pending_quantity = new_quantity

            # Only accept the fields that apply to this order's price_type:
            #   MARKET -> none, LIMIT -> price, SL -> price+trigger, SL-M -> trigger
            allows_price = order.price_type in ("LIMIT", "SL")
            allows_trigger = order.price_type in ("SL", "SL-M")

            if "price" in new_data and new_data["price"]:
                if not allows_price:
                    return (
                        False,
                        {
                            "status": "error",
                            "message": f"{order.price_type} orders do not accept a price",
                            "mode": "analyze",
                        },
                        400,
                    )
                order.price = Decimal(str(new_data["price"]))

            if "trigger_price" in new_data and new_data["trigger_price"]:
                if not allows_trigger:
                    return (
                        False,
                        {
                            "status": "error",
                            "message": f"{order.price_type} orders do not accept a trigger_price",
                            "mode": "analyze",
                        },
                        400,
                    )
                order.trigger_price = Decimal(str(new_data["trigger_price"]))

            order.update_timestamp = datetime.now(pytz.timezone("Asia/Kolkata"))

            db_session.commit()

            logger.info(f"Order modified: {orderid}")

            return (
                True,
                {
                    "status": "success",
                    "orderid": orderid,
                    "message": "Order modified successfully",
                    "mode": "analyze",
                },
                200,
            )

        except Exception as e:
            db_session.rollback()
            logger.exception(f"Error modifying order {orderid}: {e}")
            return (
                False,
                {
                    "status": "error",
                    "message": f"Error modifying order: {str(e)}",
                    "mode": "analyze",
                },
                500,
            )

    def cancel_order(self, orderid):
        """
        Cancel an existing open order

        Args:
            orderid: str - Order ID to cancel

        Returns:
            tuple: (success: bool, response: dict, status_code: int)
        """
        try:
            # Get existing order
            order = SandboxOrders.query.filter_by(orderid=orderid, user_id=self.user_id).first()

            if not order:
                return (
                    False,
                    {"status": "error", "message": f"Order {orderid} not found", "mode": "analyze"},
                    404,
                )

            if order.order_status != "open":
                return (
                    False,
                    {
                        "status": "error",
                        "message": f"Cannot cancel order in {order.order_status} status",
                        "mode": "analyze",
                    },
                    400,
                )

            # Update order status
            order.order_status = "cancelled"
            order.update_timestamp = datetime.now(pytz.timezone("Asia/Kolkata"))

            # Release blocked margin using the exact amount that was blocked
            if (
                hasattr(order, "margin_blocked")
                and order.margin_blocked
                and order.margin_blocked > 0
            ):
                self.fund_manager.release_margin(
                    order.margin_blocked, 0, f"Order cancelled: {orderid}"
                )
                logger.info(
                    f"Released margin ₹{order.margin_blocked} for cancelled order {orderid}"
                )
            else:
                # Fallback for old orders without margin_blocked field
                # Need to recalculate margin that was blocked based on order parameters
                # Get symbol info to determine if margin was blocked for this order (from cache)
                symbol_obj = get_symbol_info(order.symbol, order.exchange)

                if symbol_obj:
                    # Determine if this order would have had margin blocked
                    should_release_margin = False

                    if order.action == "BUY":
                        should_release_margin = True
                    elif order.action == "SELL":
                        if is_option(order.symbol, order.exchange) or is_future(
                            order.symbol, order.exchange
                        ):
                            should_release_margin = True
                        elif order.product in ["MIS", "NRML"]:
                            should_release_margin = True

                    if should_release_margin:
                        # Get price for margin calculation
                        if not order.price:
                            # If price is not set (old MARKET orders), fetch current LTP
                            try:
                                from sandbox.execution_engine import ExecutionEngine

                                engine = ExecutionEngine()
                                quote = engine._fetch_quote(order.symbol, order.exchange)
                                if quote and quote.get("ltp"):
                                    order_price = Decimal(str(quote["ltp"]))
                                else:
                                    logger.error(
                                        f"Cannot fetch LTP for {order.symbol} to calculate margin release"
                                    )
                                    order_price = Decimal("0")
                            except Exception as e:
                                logger.exception(f"Error fetching quote for margin release: {e}")
                                order_price = Decimal("0")
                        else:
                            order_price = order.price

                        # Calculate margin that was blocked
                        if order_price > 0:
                            margin_blocked, _ = self.fund_manager.calculate_margin_required(
                                order.symbol,
                                order.exchange,
                                order.product,
                                order.quantity,
                                order_price,
                                order.action,
                            )
                            if margin_blocked:
                                self.fund_manager.release_margin(
                                    margin_blocked, 0, f"Order cancelled: {orderid}"
                                )
                                logger.info(
                                    f"Released calculated margin ₹{margin_blocked} for cancelled order {orderid}"
                                )
                    else:
                        logger.info(
                            f"No margin to release for cancelled order {orderid} ({order.action} {order.product})"
                        )

            db_session.commit()

            logger.info(f"Order cancelled: {orderid}")

            return (
                True,
                {
                    "status": "success",
                    "orderid": orderid,
                    "message": "Order cancelled successfully",
                    "mode": "analyze",
                },
                200,
            )

        except Exception as e:
            db_session.rollback()
            logger.exception(f"Error cancelling order {orderid}: {e}")
            return (
                False,
                {
                    "status": "error",
                    "message": f"Error cancelling order: {str(e)}",
                    "mode": "analyze",
                },
                500,
            )

    def get_orderbook(self):
        """Get all orders for the user for current session only"""
        try:
            import os
            from datetime import datetime, timedelta
            from datetime import time as dt_time

            # Get session expiry time from config (e.g., '03:00')
            session_expiry_str = os.getenv("SESSION_EXPIRY_TIME", "03:00")
            expiry_hour, expiry_minute = map(int, session_expiry_str.split(":"))

            # Get current time
            now = datetime.now()
            today = now.date()

            # Calculate session start time
            # If current time is before session expiry (e.g., before 3 AM),
            # session started yesterday at expiry time
            session_expiry_time = dt_time(expiry_hour, expiry_minute)

            if now.time() < session_expiry_time:
                # We're in the early morning before session expiry
                # Session started yesterday at expiry time
                session_start = datetime.combine(today - timedelta(days=1), session_expiry_time)
            else:
                # We're after session expiry time
                # Session started today at expiry time
                session_start = datetime.combine(today, session_expiry_time)

            orders = (
                SandboxOrders.query.filter(
                    SandboxOrders.user_id == self.user_id,
                    SandboxOrders.order_timestamp >= session_start,
                )
                .order_by(SandboxOrders.order_timestamp.desc())
                .all()
            )

            orderbook = []
            for order in orders:
                orderbook.append(
                    {
                        "orderid": order.orderid,
                        "symbol": order.symbol,
                        "exchange": order.exchange,
                        "action": order.action,
                        "quantity": order.quantity,
                        "price": float(order.price) if order.price else 0.0,
                        "trigger_price": float(order.trigger_price) if order.trigger_price else 0.0,
                        "pricetype": order.price_type,  # Match broker API format
                        "product": order.product,
                        "order_status": order.order_status,  # Match broker API format
                        "average_price": float(order.average_price) if order.average_price else 0.0,
                        "filled_quantity": order.filled_quantity,
                        "pending_quantity": order.pending_quantity,
                        "rejection_reason": order.rejection_reason
                        or "",  # Include rejection reason
                        "timestamp": order.order_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        "strategy": order.strategy or "",
                    }
                )

            # Calculate statistics
            statistics = self._calculate_order_statistics(orders)

            return (
                True,
                {
                    "status": "success",
                    "data": {"orders": orderbook, "statistics": statistics},
                    "mode": "analyze",
                },
                200,
            )

        except Exception as e:
            logger.exception(f"Error getting orderbook: {e}")
            return (
                False,
                {
                    "status": "error",
                    "message": f"Error getting orderbook: {str(e)}",
                    "mode": "analyze",
                },
                500,
            )

    def get_order_status(self, orderid):
        """Get status of a specific order"""
        try:
            order = SandboxOrders.query.filter_by(orderid=orderid, user_id=self.user_id).first()

            if not order:
                return (
                    False,
                    {"status": "error", "message": f"Order {orderid} not found", "mode": "analyze"},
                    404,
                )

            return (
                True,
                {
                    "status": "success",
                    "data": {
                        "orderid": order.orderid,
                        "symbol": order.symbol,
                        "exchange": order.exchange,
                        "action": order.action,
                        "quantity": order.quantity,
                        "price": float(order.price) if order.price else 0.0,
                        "trigger_price": float(order.trigger_price) if order.trigger_price else 0.0,
                        "price_type": order.price_type,
                        "product": order.product,
                        "order_status": order.order_status,
                        "average_price": float(order.average_price) if order.average_price else 0.0,
                        "filled_quantity": order.filled_quantity,
                        "pending_quantity": order.pending_quantity,
                        "timestamp": order.order_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        "strategy": order.strategy or "",
                    },
                    "mode": "analyze",
                },
                200,
            )

        except Exception as e:
            logger.exception(f"Error getting order status: {e}")
            return (
                False,
                {
                    "status": "error",
                    "message": f"Error getting order status: {str(e)}",
                    "mode": "analyze",
                },
                500,
            )

    def _validate_order(self, order_data):
        """Validate order parameters"""
        required_fields = ["symbol", "exchange", "action", "quantity", "price_type", "product"]

        for field in required_fields:
            if field not in order_data or not order_data[field]:
                return False, f"Missing required field: {field}"

        # Validate action
        if order_data["action"].upper() not in ["BUY", "SELL"]:
            return False, "Invalid action. Must be BUY or SELL"

        # Validate price_type
        if order_data["price_type"].upper() not in ["MARKET", "LIMIT", "SL", "SL-M"]:
            return False, "Invalid price_type. Must be MARKET, LIMIT, SL, or SL-M"

        # Validate product
        if order_data["product"].upper() not in ["CNC", "NRML", "MIS"]:
            return False, "Invalid product. Must be CNC, NRML, or MIS"

        # Validate product-exchange compatibility
        exchange = order_data["exchange"].upper()
        product = order_data["product"].upper()

        # Equity exchanges (NSE/BSE cash segment): Only CNC and MIS allowed
        if exchange in ["NSE", "BSE"]:
            if product == "NRML":
                return (
                    False,
                    f"NRML product not allowed for {exchange} equity segment. Use CNC for delivery or MIS for intraday.",
                )

        # Derivatives exchanges (F&O, Commodity, Currency): Only NRML and MIS allowed
        if exchange in ["NFO", "BFO", "MCX", "CDS", "BCD", "NCDEX", "CRYPTO"]:
            if product == "CNC":
                return (
                    False,
                    f"CNC product not allowed for {exchange} derivatives segment. Use NRML for carryforward or MIS for intraday.",
                )

        # Validate quantity
        try:
            quantity = int(order_data["quantity"])
            if quantity <= 0:
                return False, "Quantity must be positive"
        except (ValueError, TypeError):
            return False, "Invalid quantity"

        # Validate price for LIMIT and SL orders
        if order_data["price_type"].upper() in ["LIMIT", "SL"]:
            if "price" not in order_data or not order_data["price"]:
                return False, f"{order_data['price_type']} orders require price"
            try:
                price = float(order_data["price"])
                if price <= 0:
                    return False, "Price must be positive"
            except (ValueError, TypeError):
                return False, "Invalid price"

        # Validate trigger_price for SL and SL-M orders
        if order_data["price_type"].upper() in ["SL", "SL-M"]:
            if "trigger_price" not in order_data or not order_data["trigger_price"]:
                return False, f"{order_data['price_type']} orders require trigger_price"
            try:
                trigger_price = float(order_data["trigger_price"])
                if trigger_price <= 0:
                    return False, "Trigger price must be positive"
            except (ValueError, TypeError):
                return False, "Invalid trigger_price"

        # Validate exchange — use the central VALID_EXCHANGES so adding a new
        # exchange (NCO, GLOBAL_INDEX, ...) is a one-place change in
        # utils/constants.py.
        if order_data["exchange"].upper() not in VALID_EXCHANGES:
            return False, f"Invalid exchange. Must be one of {', '.join(VALID_EXCHANGES)}"

        return True, "Validation passed"

    def _generate_order_id(self):
        """
        Generate unique order ID in format: YYMMDD + 8-digit unique sequence
        Example: 25100112345678 (Year 2025, Oct 1st, unique sequence)

        Uses microsecond timestamp + random component to avoid race conditions
        when multiple orders are placed in parallel.
        """
        import random

        now = datetime.now(pytz.timezone("Asia/Kolkata"))
        date_prefix = now.strftime("%y%m%d")  # YYMMDD format

        # Use microseconds (0-999999) + random (0-99) for 8-digit unique sequence
        # This avoids race conditions when parallel orders query count simultaneously
        micro = now.microsecond
        rand_suffix = random.randint(0, 99)

        # Combine: first 6 digits from microseconds, last 2 from random
        sequence = f"{micro:06d}{rand_suffix:02d}"

        return f"{date_prefix}{sequence}"

    def _calculate_order_statistics(self, orders):
        """Calculate order statistics matching broker API format"""
        # Count orders by action
        total_buy_orders = sum(1 for o in orders if o.action == "BUY")
        total_sell_orders = sum(1 for o in orders if o.action == "SELL")

        # Count orders by status
        total_completed_orders = sum(1 for o in orders if o.order_status == "complete")
        total_open_orders = sum(1 for o in orders if o.order_status == "open")
        total_rejected_orders = sum(1 for o in orders if o.order_status == "rejected")

        return {
            "total_buy_orders": total_buy_orders,
            "total_sell_orders": total_sell_orders,
            "total_completed_orders": total_completed_orders,
            "total_open_orders": total_open_orders,
            "total_rejected_orders": total_rejected_orders,
        }

```


---

# FILE: sandbox\position_manager.py

```py
# sandbox/position_manager.py
"""
Position Manager - Handles position tracking and MTM calculations

Features:
- Real-time position tracking
- Mark-to-Market (MTM) P&L calculations
- Position netting (same symbol/exchange/product)
- Open position retrieval with live P&L
- Background MTM updates (configurable interval)
"""

import os
import sys
import time
from datetime import datetime
from decimal import Decimal

import pytz

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.sandbox_db import SandboxPositions, SandboxTrades, db_session, get_config
from database.token_db import get_symbol_info
from sandbox.fund_manager import FundManager
from sandbox.holdings_manager import HoldingsManager
from services.market_data_service import get_market_data_service
from services.quotes_service import get_multiquotes, get_quotes
from utils.logging import get_logger

logger = get_logger(__name__)

# Maximum age (seconds) for WebSocket data to be considered fresh
WEBSOCKET_DATA_MAX_AGE = 5


def parse_expiry_from_symbol(symbol, exchange):
    """
    Parse expiry date from F&O symbol name.

    Supports formats like:
    - NIFTY09DEC2526000CE -> 09-Dec-2025
    - BANKNIFTY31JUL25FUT -> 31-Jul-2025
    - RELIANCE25DEC24FUT -> 25-Dec-2024

    Args:
        symbol: Trading symbol (e.g., NIFTY09DEC2526000CE)
        exchange: Exchange (NFO, BFO, MCX, CDS, etc.)

    Returns:
        datetime.date or None if not an F&O instrument or parsing fails
    """
    import re

    # Only process F&O exchanges
    fo_exchanges = ["NFO", "BFO", "MCX", "CDS", "BCD", "NCDEX", "CRYPTO"]
    if exchange not in fo_exchanges:
        return None

    # Pattern to extract date from symbol: DDMMMYY (e.g., 09DEC25, 31JUL25)
    # This pattern looks for 2 digits + 3 letters (month) + 2 digits (year)
    pattern = r"(\d{2})([A-Z]{3})(\d{2})"

    match = re.search(pattern, symbol)
    if not match:
        return None

    try:
        day = int(match.group(1))
        month_str = match.group(2)
        year_short = int(match.group(3))

        # Convert 2-digit year to 4-digit (assuming 20xx)
        year = 2000 + year_short

        # Parse month
        month_map = {
            "JAN": 1,
            "FEB": 2,
            "MAR": 3,
            "APR": 4,
            "MAY": 5,
            "JUN": 6,
            "JUL": 7,
            "AUG": 8,
            "SEP": 9,
            "OCT": 10,
            "NOV": 11,
            "DEC": 12,
        }

        month = month_map.get(month_str)
        if not month:
            return None

        # Create date object
        from datetime import date

        expiry_date = date(year, month, day)

        return expiry_date

    except (ValueError, KeyError) as e:
        logger.debug(f"Could not parse expiry from symbol {symbol}: {e}")
        return None


def get_expiry_from_database(symbol, exchange):
    """
    Get expiry date from SymToken database as fallback.

    Args:
        symbol: Trading symbol
        exchange: Exchange

    Returns:
        datetime.date or None
    """
    try:
        from datetime import datetime

        from database.symbol import SymToken

        sym_token = SymToken.query.filter_by(symbol=symbol, exchange=exchange).first()

        if sym_token and sym_token.expiry:
            # Expiry format in DB is typically "DD-MMM-YY" (e.g., "09-DEC-25")
            try:
                expiry_date = datetime.strptime(sym_token.expiry, "%d-%b-%y").date()
                return expiry_date
            except ValueError:
                try:
                    # Try alternative format "DD-MMM-YYYY"
                    expiry_date = datetime.strptime(sym_token.expiry, "%d-%b-%Y").date()
                    return expiry_date
                except ValueError:
                    logger.debug(f"Could not parse expiry '{sym_token.expiry}' for {symbol}")
                    return None

        return None

    except Exception as e:
        logger.debug(f"Error fetching expiry from DB for {symbol}: {e}")
        return None


def get_contract_expiry(symbol, exchange):
    """
    Get contract expiry date for a symbol.
    First tries to parse from symbol name, then falls back to database lookup.

    Args:
        symbol: Trading symbol
        exchange: Exchange

    Returns:
        datetime.date or None if not an F&O instrument
    """
    # First try parsing from symbol name (faster, no DB query)
    expiry = parse_expiry_from_symbol(symbol, exchange)

    if expiry:
        return expiry

    # Fallback to database lookup
    return get_expiry_from_database(symbol, exchange)


class PositionManager:
    """Manages positions and MTM calculations"""

    def __init__(self, user_id):
        self.user_id = user_id
        self.fund_manager = FundManager(user_id)

    def _get_contract_value(self, symbol: str, exchange: str) -> Decimal:
        """Look up contract_value multiplier for a symbol (e.g. 0.01 for ETHUSD.P).
        Returns 1.0 for normal equity instruments."""
        try:
            sym_info = get_symbol_info(symbol, exchange)
            if sym_info and sym_info.contract_value and float(sym_info.contract_value) != 1.0:
                return Decimal(str(sym_info.contract_value))
        except Exception:
            pass
        return Decimal("1.0")

    def _check_and_close_expired_positions(self, positions):
        """
        Check for expired F&O contracts and auto-close them.

        For expired contracts with qty > 0:
        - Options expire worthless (value = 0)
        - Futures settle at last LTP or average price
        - Releases blocked margin back to available balance
        - Marks position as closed (quantity = 0)

        Note: Does NOT filter out today's closed positions (qty=0).
        All positions passed to this function are shown (session filtering
        already happened in get_open_positions).

        Args:
            positions: List of SandboxPositions objects to check

        Returns:
            list: All positions (expired ones settled, others unchanged)
        """
        from datetime import date

        today = date.today()
        valid_positions = []
        expired_count = 0

        for position in positions:
            # Get contract expiry date
            expiry_date = get_contract_expiry(position.symbol, position.exchange)

            # If no expiry found (equity or couldn't parse), keep the position
            if expiry_date is None:
                valid_positions.append(position)
                continue

            # Check if contract has expired
            is_expired = today > expiry_date

            # For already closed positions (qty=0), just keep them
            # These are today's closed trades - show them regardless of expiry
            if position.quantity == 0:
                valid_positions.append(position)
                continue

            # For open positions (qty != 0)
            if is_expired:
                # Contract has expired - auto-close it
                logger.info(
                    f"Expired contract detected: {position.symbol} "
                    f"(expiry: {expiry_date}, today: {today}, user: {position.user_id})"
                )

                try:
                    self._settle_expired_position(position)
                    expired_count += 1
                    # Add to valid_positions - it's now closed but still show it
                    valid_positions.append(position)
                except Exception as e:
                    logger.exception(f"Error settling expired position {position.symbol}: {e}")
                    valid_positions.append(position)
            else:
                # Contract is still valid
                valid_positions.append(position)

        if expired_count > 0:
            logger.info(f"Auto-closed {expired_count} expired contract(s) for user {self.user_id}")

        return valid_positions

    def _settle_expired_position(self, position):
        """
        Settle an expired position.

        Settlement prices:
        - Options: Expire at 0 (most expire worthless - conservative approach)
        - Futures: Use last stored LTP, or average price as fallback
        - Releases margin and updates realized P&L

        Args:
            position: SandboxPositions object to settle
        """
        from decimal import Decimal

        symbol = position.symbol
        quantity = position.quantity
        avg_price = Decimal(str(position.average_price))
        margin_blocked = Decimal(str(position.margin_blocked or 0))

        # Determine settlement price based on instrument type.
        # CRYPTO canonical suffixes: CE/PE = option, FUT = dated future, no suffix = perpetual.
        is_option = symbol.endswith("CE") or symbol.endswith("PE")

        if is_option:
            # Options expire worthless (at 0)
            # This is conservative - user loses full premium for longs
            settlement_price = Decimal("0")
            logger.info(f"Option {symbol} expired - settling at 0 (worthless)")
        else:
            # Futures: use last LTP if available, otherwise average price
            if position.ltp and Decimal(str(position.ltp)) > 0:
                settlement_price = Decimal(str(position.ltp))
                logger.info(f"Future {symbol} expired - settling at last LTP: {settlement_price}")
            else:
                settlement_price = avg_price
                logger.info(f"Future {symbol} expired - settling at avg price: {settlement_price}")

        # Calculate realized P&L for this closure
        if quantity > 0:
            # Long position: P&L = (settlement - avg) * qty
            close_pnl = (settlement_price - avg_price) * Decimal(str(quantity))
        else:
            # Short position: P&L = (avg - settlement) * abs(qty)
            close_pnl = (avg_price - settlement_price) * Decimal(str(abs(quantity)))

        # Get accumulated realized P&L from position
        accumulated_realized = Decimal(str(position.accumulated_realized_pnl or 0))

        # Total realized P&L for this position
        total_realized_pnl = accumulated_realized + close_pnl

        logger.info(
            f"Settling expired {symbol}: qty={quantity}, avg={avg_price}, "
            f"settlement={settlement_price}, close_pnl={close_pnl}, "
            f"total_realized={total_realized_pnl}, margin_to_release={margin_blocked}"
        )

        # Release margin and update funds
        self.fund_manager.release_margin(
            amount=margin_blocked,
            realized_pnl=close_pnl,
            description=f"Expired contract settlement: {symbol}",
        )

        # Get expiry date for hiding the position
        expiry_date = get_contract_expiry(symbol, position.exchange)

        # Update position to closed state
        position.quantity = 0
        position.ltp = settlement_price
        position.pnl = total_realized_pnl
        position.accumulated_realized_pnl = total_realized_pnl
        position.margin_blocked = Decimal("0")

        db_session.commit()

        # Set updated_at to expiry date AFTER commit to bypass onupdate trigger
        # This hides expired contracts from current session
        if expiry_date:
            from sqlalchemy import text

            hide_date = datetime.combine(expiry_date, datetime.min.time())
            db_session.execute(
                text("UPDATE sandbox_positions SET updated_at = :hide_date WHERE id = :pos_id"),
                {"hide_date": hide_date, "pos_id": position.id},
            )
            db_session.commit()

        logger.info(f"Expired position {symbol} settled successfully for user {position.user_id}")

    def get_open_positions(self, update_mtm=True):
        """
        Get all open positions for the user
        - After session expiry, only NRML positions carry forward
        - MIS and CNC positions are settled at session expiry

        Args:
            update_mtm: bool - Whether to update MTM with live prices

        Returns:
            tuple: (success: bool, response: dict, status_code: int)
        """
        try:
            import os
            from datetime import datetime, time, timedelta

            # Get session expiry time from config (e.g., '03:00')
            session_expiry_str = os.getenv("SESSION_EXPIRY_TIME", "03:00")
            expiry_hour, expiry_minute = map(int, session_expiry_str.split(":"))

            # Get current time
            now = datetime.now()
            today = now.date()

            # Calculate if we're in a new session
            session_expiry_time = time(expiry_hour, expiry_minute)

            # Determine last session expiry
            if now.time() < session_expiry_time:
                # We're before today's session expiry (e.g., before 3 AM)
                # Last session expired yesterday at 3 AM
                last_session_expiry = datetime.combine(
                    today - timedelta(days=1), session_expiry_time
                )
            else:
                # We're after today's session expiry (e.g., after 3 AM)
                # Last session expired today at 3 AM
                last_session_expiry = datetime.combine(today, session_expiry_time)

            # Get all positions (including zero quantity ones from current session)
            positions_query = SandboxPositions.query.filter(
                SandboxPositions.user_id == self.user_id
            )

            # Check if we need to filter positions based on product type
            # If position was created before last session expiry and it's not NRML,
            # it should have been settled
            all_positions = positions_query.all()
            positions = []

            for position in all_positions:
                # CATCH-UP RESET: Check if today_realized_pnl needs to be reset
                # This handles the case where the scheduled reset job was missed
                # Reset if position has non-zero today_realized_pnl and was last updated before session boundary
                needs_pnl_reset = False
                if position.today_realized_pnl and position.today_realized_pnl != 0:
                    # Check if there's been a session boundary since the position was created/traded
                    # If position was last modified before today's session boundary, reset today_realized_pnl
                    position_date = position.updated_at.date() if position.updated_at else today
                    session_boundary_date = last_session_expiry.date()

                    # If position's date is before today's session boundary date, or
                    # if same date but position was updated before session expiry time
                    if position_date < session_boundary_date:
                        needs_pnl_reset = True
                    elif (
                        position_date == session_boundary_date
                        and position.updated_at < last_session_expiry
                    ):
                        needs_pnl_reset = True

                if needs_pnl_reset:
                    logger.info(
                        f"Catch-up reset: Resetting today_realized_pnl for {position.symbol} from {position.today_realized_pnl} to 0"
                    )
                    # Use raw SQL to avoid triggering onupdate=func.now() which would change updated_at
                    # If we used ORM commit(), updated_at would be set to NOW and old positions would
                    # pass the session filter, causing yesterday's closed positions to show today
                    from sqlalchemy import text

                    db_session.execute(
                        text(
                            "UPDATE sandbox_positions SET today_realized_pnl = 0 WHERE id = :pos_id"
                        ),
                        {"pos_id": position.id},
                    )
                    db_session.commit()
                    # Refresh from database instead of setting directly
                    # Setting position.today_realized_pnl = X would mark the ORM object as "dirty"
                    # which causes it to be committed later in _update_positions_mtm, triggering
                    # onupdate=func.now() and bringing old closed positions back into view
                    db_session.refresh(position)

                # If position was updated after last session expiry, include it
                if position.updated_at >= last_session_expiry:
                    # For OPEN positions (qty != 0): always include
                    if position.quantity != 0:
                        positions.append(position)
                    # For CLOSED positions (qty == 0): only include if actually traded today
                    # Check: today_realized_pnl != 0 (has P&L from today's trades)
                    # This prevents old closed positions with corrupted updated_at from showing
                    elif position.today_realized_pnl and position.today_realized_pnl != 0:
                        positions.append(position)
                    # Skip old closed positions with corrupted updated_at
                # If position was updated before last session expiry, only include NRML with non-zero quantity
                elif position.product == "NRML" and position.quantity != 0:
                    positions.append(position)
                # Skip MIS and CNC positions from previous session

            # Check for and auto-close expired F&O contracts
            # This handles NRML positions where the contract has expired
            positions = self._check_and_close_expired_positions(positions)

            if update_mtm:
                self._update_positions_mtm(positions)

            positions_list = []
            total_unrealized_pnl = Decimal("0.00")  # Only from open positions
            total_today_realized_pnl = Decimal("0.00")  # Today's realized P&L
            total_pnl_today = Decimal("0.00")  # Today's total (realized + unrealized)

            # Build contract_value lookup map for all positions using in-memory cache
            try:
                _cv_map = {}
                for p in positions:
                    sym_info = get_symbol_info(p.symbol, p.exchange)
                    if sym_info and sym_info.contract_value:
                        _cv_map[p.symbol] = float(sym_info.contract_value)
            except Exception:
                _cv_map = {}

            for position in positions:
                unrealized_pnl = Decimal(str(position.pnl))  # Current unrealized P&L from MTM
                today_realized = Decimal(str(position.today_realized_pnl or 0))

                # For open positions: total_pnl_today = today's realized + unrealized
                # For closed positions (qty=0): total_pnl_today = today's realized only
                if position.quantity != 0:
                    total_unrealized_pnl += unrealized_pnl
                    position_total_pnl_today = today_realized + unrealized_pnl
                else:
                    # Closed position - only today's realized matters
                    position_total_pnl_today = today_realized

                total_today_realized_pnl += today_realized
                total_pnl_today += position_total_pnl_today

                # Calculate P&L% based on total P&L (realized + unrealized) for the day
                # For open positions: % based on total investment
                # For closed positions (qty=0): 0% (like Zerodha - avg resets to 0, can't calculate)
                pos_cv = _cv_map.get(position.symbol, 1.0)
                pos_cv_dec = Decimal(str(pos_cv))
                if position.quantity != 0:
                    investment = abs(Decimal(str(position.average_price)) * Decimal(str(position.quantity)) * pos_cv_dec)
                    if investment > 0:
                        calculated_pnl_percent = (position_total_pnl_today / investment) * Decimal("100")
                    else:
                        calculated_pnl_percent = Decimal("0.00")
                    display_avg_price = float(position.average_price)
                else:
                    # Closed position - show 0% and avg=0 (like Zerodha)
                    calculated_pnl_percent = Decimal("0.00")
                    display_avg_price = 0.0  # Reset to 0 for display (like Zerodha)

                positions_list.append(
                    {
                        "symbol": position.symbol,
                        "exchange": position.exchange,
                        "product": position.product,
                        "quantity": position.quantity,
                        "average_price": display_avg_price,  # 0 for closed positions (like Zerodha)
                        "ltp": float(position.ltp) if position.ltp else 0.0,
                        "pnl": float(
                            position_total_pnl_today
                        ),  # Today's total P&L (realized + unrealized)
                        "pnlpercent": float(calculated_pnl_percent),  # Fixed: use pnlpercent (no underscore) to match frontend
                        "unrealized_pnl": float(unrealized_pnl),  # Unrealized only (for reference)
                        "today_realized_pnl": float(today_realized),
                        "total_pnl_today": float(position_total_pnl_today),
                        "lot_size": pos_cv,  # contract_value multiplier (e.g. 0.01 for ETHUSD.P)
                    }
                )

            # Update fund unrealized P&L (only from open positions)
            # Closed position P&L is already in realized_pnl, so don't include it here
            if update_mtm:
                self.fund_manager.update_unrealized_pnl(total_unrealized_pnl)

            return (
                True,
                {
                    "status": "success",
                    "data": positions_list,
                    "total_pnl": float(
                        total_pnl_today
                    ),  # Today's total P&L (realized + unrealized)
                    "total_unrealized_pnl": float(total_unrealized_pnl),
                    "total_today_realized_pnl": float(total_today_realized_pnl),
                    "total_pnl_today": float(total_pnl_today),
                    "mode": "analyze",
                },
                200,
            )

        except Exception as e:
            logger.exception(f"Error getting positions for user {self.user_id}: {e}")
            return (
                False,
                {
                    "status": "error",
                    "message": f"Error getting positions: {str(e)}",
                    "mode": "analyze",
                },
                500,
            )

    def get_position_for_symbol(self, symbol, exchange, product):
        """Get position for a specific symbol"""
        try:
            position = SandboxPositions.query.filter_by(
                user_id=self.user_id, symbol=symbol, exchange=exchange, product=product
            ).first()

            if not position:
                return None

            # Update MTM
            self._update_single_position_mtm(position)

            return {
                "symbol": position.symbol,
                "exchange": position.exchange,
                "product": position.product,
                "quantity": position.quantity,
                "average_price": float(position.average_price),
                "ltp": float(position.ltp) if position.ltp else 0.0,
                "pnl": float(position.pnl),
                "pnl_percent": float(position.pnl_percent),
            }

        except Exception as e:
            logger.exception(f"Error getting position for {symbol}: {e}")
            return None

    def _update_positions_mtm(self, positions):
        """
        Update MTM for all positions with live quotes.
        Uses WebSocket data first, falls back to multiquotes API if WebSocket data is stale.
        """
        try:
            if not positions:
                return

            # Get unique symbols
            symbols_to_fetch = set()
            for position in positions:
                if position.quantity != 0:  # Only fetch for open positions
                    symbols_to_fetch.add((position.symbol, position.exchange))

            if not symbols_to_fetch:
                return

            symbols_list = list(symbols_to_fetch)

            # Try WebSocket data first (from MarketDataService)
            quote_cache = self._fetch_quotes_from_websocket(symbols_list)
            ws_count = len(quote_cache)

            # Find symbols that need fallback to multiquotes
            missing_symbols = [
                s for s in symbols_list if s not in quote_cache or quote_cache[s] is None
            ]

            if missing_symbols:
                # Fallback to multiquotes for missing symbols (no individual quote fallback to avoid rate limiting)
                logger.debug(
                    f"Positions MTM: {ws_count} from WebSocket, {len(missing_symbols)} need multiquotes fallback"
                )
                multiquotes_cache = self._fetch_quotes_batch(missing_symbols)
                quote_cache.update(multiquotes_cache)

                # Log any symbols that couldn't be fetched (don't fall back to individual quotes)
                still_missing = [
                    s for s in missing_symbols if s not in quote_cache or quote_cache[s] is None
                ]
                if still_missing:
                    logger.debug(f"{len(still_missing)} symbols not available via multiquotes, waiting for WebSocket data")
            else:
                logger.debug(f"Positions MTM: All {ws_count} symbols from WebSocket (no API calls)")

            # Update MTM for each position
            for position in positions:
                # Skip MTM update for closed positions (quantity = 0)
                # They already have today's realized P&L stored in position.pnl
                if position.quantity == 0:
                    continue

                quote = quote_cache.get((position.symbol, position.exchange))
                if quote:
                    ltp = Decimal(str(quote.get("ltp", 0)))
                    if ltp > 0:
                        position.ltp = ltp

                        # Calculate current unrealized P&L for open position
                        cv = self._get_contract_value(position.symbol, position.exchange)
                        current_unrealized_pnl = self._calculate_position_pnl(
                            position.quantity, position.average_price, ltp, contract_value=cv
                        )

                        # pnl = unrealized only (broker standard - Zerodha Kite style)
                        # This is the primary P&L field for open positions
                        position.pnl = current_unrealized_pnl

                        position.pnl_percent = self._calculate_pnl_percent(
                            position.average_price, ltp, position.quantity
                        )

            db_session.commit()

        except Exception as e:
            db_session.rollback()
            logger.exception(f"Error updating positions MTM: {e}")

    def _update_single_position_mtm(self, position):
        """
        Update MTM for a single position.
        Uses WebSocket data first, falls back to REST API if unavailable.
        """
        try:
            # Skip MTM update for closed positions (quantity = 0)
            # They already have today's realized P&L stored from when position was closed
            if position.quantity == 0:
                return

            # Try WebSocket first
            ws_quotes = self._fetch_quotes_from_websocket([(position.symbol, position.exchange)])
            quote = ws_quotes.get((position.symbol, position.exchange))

            # Fallback to REST API if WebSocket data not available
            if not quote:
                quote = self._fetch_quote(position.symbol, position.exchange)

            if quote:
                ltp = Decimal(str(quote.get("ltp", 0)))
                if ltp > 0:
                    position.ltp = ltp

                    # Calculate current unrealized P&L for open position
                    cv = self._get_contract_value(position.symbol, position.exchange)
                    current_unrealized_pnl = self._calculate_position_pnl(
                        position.quantity, position.average_price, ltp, contract_value=cv
                    )

                    # pnl = unrealized only (broker standard - Zerodha Kite style)
                    position.pnl = current_unrealized_pnl

                    position.pnl_percent = self._calculate_pnl_percent(
                        position.average_price, ltp, position.quantity
                    )
                    db_session.commit()

        except Exception as e:
            db_session.rollback()
            logger.exception(f"Error updating position MTM for {position.symbol}: {e}")

    def _calculate_position_pnl(self, quantity, avg_price, ltp, contract_value=None):
        """Calculate P&L for a position, multiplied by contract_value (e.g. 0.01 for ETHUSD.P)."""
        try:
            quantity = Decimal(str(quantity))
            avg_price = Decimal(str(avg_price))
            ltp = Decimal(str(ltp))
            cv = Decimal(str(contract_value)) if contract_value is not None else Decimal("1.0")

            if quantity > 0:
                # Long position
                pnl = (ltp - avg_price) * quantity * cv
            else:
                # Short position
                pnl = (avg_price - ltp) * abs(quantity) * cv

            return pnl

        except Exception as e:
            logger.exception(f"Error calculating position P&L: {e}")
            return Decimal("0.00")

    def _calculate_pnl_percent(self, avg_price, ltp, quantity):
        """Calculate P&L percentage"""
        try:
            avg_price = Decimal(str(avg_price))
            ltp = Decimal(str(ltp))

            if avg_price <= 0:
                return Decimal("0.00")

            if quantity > 0:
                # Long position
                pnl_percent = ((ltp - avg_price) / avg_price) * Decimal("100")
            else:
                # Short position
                pnl_percent = ((avg_price - ltp) / avg_price) * Decimal("100")

            return pnl_percent

        except Exception as e:
            logger.exception(f"Error calculating P&L percent: {e}")
            return Decimal("0.00")

    def _fetch_quotes_from_websocket(self, symbols_list):
        """
        Fetch LTP from WebSocket (MarketDataService) for multiple symbols.
        Returns dict mapping (symbol, exchange) to quote data.
        Only returns data that is fresh (within WEBSOCKET_DATA_MAX_AGE seconds).
        """
        quote_cache = {}

        if not symbols_list:
            return quote_cache

        try:
            market_data_service = get_market_data_service()
            current_time = time.time()

            for symbol, exchange in symbols_list:
                # Get all cached data from MarketDataService
                data = market_data_service.get_all_data(symbol, exchange)

                if data:
                    # Check if data is fresh using last_update timestamp
                    last_update = data.get("last_update", 0)
                    age = current_time - last_update

                    if age <= WEBSOCKET_DATA_MAX_AGE:
                        # Get LTP from the ltp sub-dict
                        ltp_data = data.get("ltp", {})
                        ltp = ltp_data.get("value") if isinstance(ltp_data, dict) else None

                        if ltp and ltp > 0:
                            quote_cache[(symbol, exchange)] = {"ltp": ltp}
                    else:
                        logger.debug(f"WebSocket data stale for {symbol} (age: {age:.1f}s)")

            return quote_cache

        except Exception as e:
            logger.debug(f"Error fetching from WebSocket: {e}")
            return quote_cache

    def _fetch_quote(self, symbol, exchange):
        """Fetch real-time quote for a symbol using API key"""
        try:
            # Get any user's API key for fetching quotes
            from database.auth_db import ApiKeys, decrypt_token

            api_key_obj = ApiKeys.query.first()

            if not api_key_obj:
                logger.warning("No API keys found for fetching quotes")
                return None

            # Decrypt the API key
            api_key = decrypt_token(api_key_obj.api_key_encrypted)

            # Use quotes service with API key authentication
            success, response, status_code = get_quotes(
                symbol=symbol, exchange=exchange, api_key=api_key
            )

            if success and "data" in response:
                return response["data"]
            else:
                logger.warning(
                    f"Failed to fetch quote for {symbol}: {response.get('message', 'Unknown error')}"
                )
                return None

        except Exception as e:
            logger.exception(f"Error fetching quote for {symbol}: {e}")
            return None

    def _fetch_quotes_batch(self, symbols_list):
        """
        Fetch quotes for multiple symbols in a single API call using multiquotes.
        Returns dict mapping (symbol, exchange) to quote data.
        Returns empty dict if multiquotes fails completely.
        """
        quote_cache = {}

        if not symbols_list:
            return quote_cache

        try:
            # Get any user's API key for fetching quotes
            from database.auth_db import ApiKeys, decrypt_token

            api_key_obj = ApiKeys.query.first()

            if not api_key_obj:
                logger.debug("No API keys found for fetching multiquotes")
                return quote_cache

            # Decrypt the API key
            api_key = decrypt_token(api_key_obj.api_key_encrypted)

            # Prepare symbols list for multiquotes API
            symbols_payload = [
                {"symbol": symbol, "exchange": exchange} for symbol, exchange in symbols_list
            ]

            # Use multiquotes service
            success, response, status_code = get_multiquotes(
                symbols=symbols_payload, api_key=api_key
            )

            if success and "results" in response:
                results = response["results"]
                successful_count = 0

                for result in results:
                    symbol = result.get("symbol")
                    exchange = result.get("exchange")

                    # Check if this result has data or error
                    if "data" in result and result["data"]:
                        quote_data = result["data"]
                        quote_cache[(symbol, exchange)] = quote_data
                        logger.debug(f"Multiquotes: {symbol} LTP={quote_data.get('ltp', 0)}")
                        successful_count += 1
                    elif "error" in result:
                        logger.debug(f"Multiquotes error for {symbol}: {result['error']}")

                logger.info(
                    f"Positions MTM: Multiquotes fetched {successful_count}/{len(symbols_list)} symbols"
                )
            else:
                logger.debug(f"Multiquotes failed: {response.get('message', 'Unknown error')}")

        except Exception as e:
            logger.debug(f"Exception in multiquotes fetch: {str(e)}")

        return quote_cache

    def close_position(self, symbol, exchange, product):
        """
        Close a position (square-off)
        Creates a reverse order to close the position
        """
        try:
            position = SandboxPositions.query.filter_by(
                user_id=self.user_id, symbol=symbol, exchange=exchange, product=product
            ).first()

            if not position:
                return (
                    False,
                    {
                        "status": "error",
                        "message": f"No open position found for {symbol}",
                        "mode": "analyze",
                    },
                    404,
                )

            # Determine action (opposite of current position)
            action = "SELL" if position.quantity > 0 else "BUY"
            quantity = abs(position.quantity)

            # Create market order to close position
            from sandbox.order_manager import OrderManager

            order_manager = OrderManager(self.user_id)

            order_data = {
                "symbol": symbol,
                "exchange": exchange,
                "action": action,
                "quantity": quantity,
                "price_type": "MARKET",
                "product": product,
                "strategy": "AUTO_SQUARE_OFF",
            }

            success, response, status_code = order_manager.place_order(order_data)

            if success:
                logger.info(f"Position close order placed: {symbol} {action} {quantity}")
                return (
                    True,
                    {
                        "status": "success",
                        "message": f"Position close order placed for {symbol}",
                        "orderid": response.get("orderid"),
                        "mode": "analyze",
                    },
                    200,
                )
            else:
                return False, response, status_code

        except Exception as e:
            logger.exception(f"Error closing position {symbol}: {e}")
            return (
                False,
                {
                    "status": "error",
                    "message": f"Error closing position: {str(e)}",
                    "mode": "analyze",
                },
                500,
            )

    def get_tradebook(self):
        """Get all executed trades for the user for current session only"""
        try:
            import os
            from datetime import datetime, time, timedelta

            # Get session expiry time from config (e.g., '03:00')
            session_expiry_str = os.getenv("SESSION_EXPIRY_TIME", "03:00")
            expiry_hour, expiry_minute = map(int, session_expiry_str.split(":"))

            # Get current time
            now = datetime.now()
            today = now.date()

            # Calculate session start time
            # If current time is before session expiry (e.g., before 3 AM),
            # session started yesterday at expiry time
            session_expiry_time = time(expiry_hour, expiry_minute)

            if now.time() < session_expiry_time:
                # We're in the early morning before session expiry
                # Session started yesterday at expiry time
                session_start = datetime.combine(today - timedelta(days=1), session_expiry_time)
            else:
                # We're after session expiry time
                # Session started today at expiry time
                session_start = datetime.combine(today, session_expiry_time)

            trades = (
                SandboxTrades.query.filter(
                    SandboxTrades.user_id == self.user_id,
                    SandboxTrades.trade_timestamp >= session_start,
                )
                .order_by(SandboxTrades.trade_timestamp.desc())
                .all()
            )

            tradebook = []
            for trade in trades:
                price = float(trade.price)
                quantity = abs(trade.quantity)  # Use absolute value for trade_value calculation
                trade_value = round(price * quantity, 2)  # Round to 2 decimal places

                tradebook.append(
                    {
                        "tradeid": trade.tradeid,
                        "orderid": trade.orderid,
                        "symbol": trade.symbol,
                        "exchange": trade.exchange,
                        "action": trade.action,
                        "quantity": trade.quantity,
                        "average_price": round(price, 2),  # Round to 2 decimal places
                        "price": round(price, 2),  # Round to 2 decimal places
                        "trade_value": trade_value,  # Trade value already rounded above
                        "product": trade.product,
                        "strategy": trade.strategy or "",
                        "timestamp": trade.trade_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )

            return True, {"status": "success", "data": tradebook, "mode": "analyze"}, 200

        except Exception as e:
            logger.exception(f"Error getting tradebook: {e}")
            return (
                False,
                {
                    "status": "error",
                    "message": f"Error getting tradebook: {str(e)}",
                    "mode": "analyze",
                },
                500,
            )

    def process_session_settlement(self):
        """
        Process session expiry settlement (at SESSION_EXPIRY_TIME):
        1. Auto square-off MIS positions
        2. Move CNC positions to holdings (T+1 settlement)
        3. Keep NRML positions as carry forward

        This should be called at session expiry time (e.g., 3:00 AM IST)
        """
        try:
            import os
            from datetime import date, datetime

            from database import db
            from database.sandbox_db import SandboxHoldings

            # Get session expiry time from config
            session_expiry_str = os.getenv("SESSION_EXPIRY_TIME", "03:00")
            logger.info(f"Processing session settlement at {session_expiry_str}")

            # Get all open positions
            positions = SandboxPositions.query.filter_by(user_id=self.user_id).all()

            for position in positions:
                if position.quantity == 0:
                    continue  # Skip closed positions

                if position.product == "MIS":
                    # Auto square-off MIS positions at market close
                    # Create a reverse order to square off
                    action = "SELL" if position.quantity > 0 else "BUY"
                    quantity = abs(position.quantity)

                    # Use last traded price or average price for square-off
                    price = float(position.average_price) if position.average_price else 0

                    # Update position to closed
                    position.quantity = 0
                    position.pnl = float(position.realized_pnl)
                    db.session.commit()

                    logger.info(f"Auto squared-off MIS position: {position.symbol} qty: {quantity}")

                elif position.product == "CNC" and position.quantity > 0:
                    # Move CNC buy positions to holdings (T+1 settlement)
                    # CNC sell positions are already closed (no short delivery allowed)

                    # Check if holdings exist
                    holdings = SandboxHoldings.query.filter_by(
                        user_id=self.user_id, symbol=position.symbol, exchange=position.exchange
                    ).first()

                    if holdings:
                        # Update existing holdings
                        holdings.quantity += position.quantity
                        holdings.average_price = (
                            holdings.average_price * holdings.quantity
                            + position.average_price * position.quantity
                        ) / (holdings.quantity + position.quantity)
                    else:
                        # Create new holdings
                        holdings = SandboxHoldings(
                            user_id=self.user_id,
                            symbol=position.symbol,
                            exchange=position.exchange,
                            quantity=position.quantity,
                            average_price=position.average_price,
                            settlement_date=date.today(),
                        )
                        db.session.add(holdings)

                    # Clear the CNC position
                    position.quantity = 0
                    position.pnl = float(position.realized_pnl)
                    db.session.commit()

                    logger.debug(
                        f"Moved CNC position to holdings: {position.symbol} qty: {position.quantity}"
                    )

                # NRML positions remain as-is (carry forward)

            return (
                True,
                {"status": "success", "message": "Session settlement completed", "mode": "analyze"},
                200,
            )

        except Exception as e:
            logger.exception(f"Error in EOD settlement: {e}")
            db.session.rollback()
            return (
                False,
                {
                    "status": "error",
                    "message": f"Error in EOD settlement: {str(e)}",
                    "mode": "analyze",
                },
                500,
            )


def update_all_positions_mtm():
    """Background task to update MTM for all positions"""
    try:
        # Skip MTM updates when market is closed (prices won't change)
        from database.market_calendar_db import is_market_open

        if not is_market_open():
            logger.debug("Market closed - skipping MTM update")
            return

        # Get all unique users with positions
        positions = SandboxPositions.query.all()

        if not positions:
            logger.debug("No positions to update")
            return

        users = set(p.user_id for p in positions)
        logger.info(f"Updating MTM for {len(positions)} positions across {len(users)} users")

        for user_id in users:
            pm = PositionManager(user_id)
            pm.get_open_positions(update_mtm=True)

        logger.info("MTM update completed")

    except Exception as e:
        logger.exception(f"Error updating MTM for all positions: {e}")


def process_all_users_settlement():
    """
    Process T+1 settlement for all users at midnight (00:00 IST)
    - Moves CNC positions to holdings
    - Auto squares-off any remaining MIS positions
    - NRML positions carry forward
    """
    try:
        # Get all unique users with positions
        positions = SandboxPositions.query.all()

        if not positions:
            logger.info("No positions to settle")
            return

        users = set(p.user_id for p in positions)
        logger.debug(f"Processing T+1 settlement for {len(users)} users at midnight")

        for user_id in users:
            try:
                holdings_manager = HoldingsManager(user_id)
                success, message = holdings_manager.process_t1_settlement()

                if success:
                    logger.debug(f"Settlement completed for user {user_id}")
                else:
                    logger.error(f"Settlement failed for user {user_id}: {message}")

            except Exception as e:
                logger.exception(f"Error in settlement for user {user_id}: {e}")
                continue

        logger.debug("T+1 settlement completed for all users")

    except Exception as e:
        logger.exception(f"Error in T+1 settlement process: {e}")


def cleanup_expired_contracts():
    """
    Clean up expired F&O contracts from sandbox positions.
    Runs on startup when analyzer mode is enabled.

    This handles cases where:
    - App was stopped for several days
    - User hasn't logged in for a while
    - Contracts expired while app was not running

    Expired contracts are settled with:
    - Margin released back to available balance
    - P&L calculated and added to realized P&L
    - Position quantity set to 0
    """
    from datetime import date
    from decimal import Decimal

    from sandbox.fund_manager import FundManager

    try:
        today = date.today()

        # Find all open positions in F&O exchanges
        fo_exchanges = ["NFO", "BFO", "MCX", "CDS", "BCD", "NCDEX", "CRYPTO"]

        expired_positions = []

        # Query all open positions in F&O exchanges
        all_fo_positions = SandboxPositions.query.filter(
            SandboxPositions.exchange.in_(fo_exchanges), SandboxPositions.quantity != 0
        ).all()

        if not all_fo_positions:
            logger.debug("No open F&O positions to check for expiry")
            return

        logger.debug(f"Checking {len(all_fo_positions)} F&O positions for expired contracts")

        # Check each position for expiry
        for position in all_fo_positions:
            expiry_date = get_contract_expiry(position.symbol, position.exchange)

            if expiry_date and today > expiry_date:
                expired_positions.append(position)
                logger.debug(
                    f"Found expired contract: {position.symbol} "
                    f"(expiry: {expiry_date}, user: {position.user_id})"
                )

        if not expired_positions:
            logger.debug("No expired F&O contracts found")
            return

        logger.debug(f"Found {len(expired_positions)} expired contracts to clean up")

        # Group by user for efficient processing
        user_positions = {}
        for pos in expired_positions:
            if pos.user_id not in user_positions:
                user_positions[pos.user_id] = []
            user_positions[pos.user_id].append(pos)

        # Process each user's expired positions
        for user_id, positions in user_positions.items():
            try:
                fund_manager = FundManager(user_id)

                for position in positions:
                    try:
                        symbol = position.symbol
                        quantity = position.quantity
                        avg_price = Decimal(str(position.average_price))
                        margin_blocked = Decimal(str(position.margin_blocked or 0))

                        # Determine settlement price based on instrument type.
                        # CRYPTO canonical suffixes: CE/PE = option, FUT/other = future/perpetual.
                        is_option = symbol.endswith("CE") or symbol.endswith("PE")

                        if is_option:
                            # Options expire worthless (at 0)
                            # This is conservative - user loses full premium for longs
                            settlement_price = Decimal("0")
                            logger.info(f"Option {symbol} expired - settling at 0 (worthless)")
                        else:
                            # Futures: use last LTP if available, otherwise average price
                            if position.ltp and Decimal(str(position.ltp)) > 0:
                                settlement_price = Decimal(str(position.ltp))
                            else:
                                settlement_price = avg_price
                            logger.info(f"Future {symbol} expired - settling at {settlement_price}")

                        # Calculate realized P&L
                        if quantity > 0:
                            close_pnl = (settlement_price - avg_price) * Decimal(str(quantity))
                        else:
                            close_pnl = (avg_price - settlement_price) * Decimal(str(abs(quantity)))

                        accumulated_realized = Decimal(str(position.accumulated_realized_pnl or 0))
                        total_realized_pnl = accumulated_realized + close_pnl

                        logger.info(
                            f"Settling expired {symbol}: qty={quantity}, "
                            f"settlement_price={settlement_price}, close_pnl={close_pnl}, "
                            f"margin_to_release={margin_blocked}"
                        )

                        # Release margin and update funds
                        fund_manager.release_margin(
                            amount=margin_blocked,
                            realized_pnl=close_pnl,
                            description=f"Expired contract cleanup: {symbol}",
                        )

                        # Update position to closed state
                        position.quantity = 0
                        position.ltp = settlement_price
                        position.pnl = total_realized_pnl
                        position.accumulated_realized_pnl = total_realized_pnl
                        position.margin_blocked = Decimal("0")

                        db_session.commit()

                        # Set updated_at to expiry date AFTER commit to bypass onupdate trigger
                        # This hides expired contracts from current session
                        from sqlalchemy import text

                        hide_date = datetime.combine(expiry_date, datetime.min.time())
                        db_session.execute(
                            text(
                                "UPDATE sandbox_positions SET updated_at = :hide_date WHERE id = :pos_id"
                            ),
                            {"hide_date": hide_date, "pos_id": position.id},
                        )
                        db_session.commit()

                        logger.info(f"Expired contract {symbol} cleaned up for user {user_id}")

                    except Exception as e:
                        db_session.rollback()
                        logger.exception(f"Error cleaning up expired position {position.symbol}: {e}")
                        continue

            except Exception as e:
                logger.exception(f"Error processing expired contracts for user {user_id}: {e}")
                continue

        logger.info(
            f"Expired contract cleanup completed: {len(expired_positions)} contracts processed"
        )

    except Exception as e:
        logger.exception(f"Error in expired contract cleanup: {e}")


def catchup_missed_settlements():
    """
    Catch-up settlement for positions that should have been settled while app was stopped.
    Runs on startup when analyzer mode is enabled.

    This function handles:
    1. Expired F&O contracts - settles them and releases margin
    2. CNC positions older than 1 day - settles them to holdings
    """
    try:
        # First, clean up expired F&O contracts
        # This is important to do first so users don't see stale contracts
        logger.debug("Running expired contract cleanup...")
        cleanup_expired_contracts()

        # Then handle CNC T+1 settlement
        ist = pytz.timezone("Asia/Kolkata")
        today = datetime.now(ist).date()
        cutoff_time = datetime.combine(today, datetime.min.time())

        cnc_positions = (
            SandboxPositions.query.filter_by(product="CNC")
            .filter(SandboxPositions.quantity != 0, SandboxPositions.created_at < cutoff_time)
            .all()
        )

        if not cnc_positions:
            logger.debug("No CNC positions for catch-up settlement")
            return

        logger.info(f"Found {len(cnc_positions)} CNC positions that need catch-up settlement")

        users = set(p.user_id for p in cnc_positions)

        for user_id in users:
            try:
                holdings_manager = HoldingsManager(user_id)
                success, message = holdings_manager.process_t1_settlement()

                if success:
                    logger.info(f"Catch-up settlement completed for user {user_id}")
                else:
                    logger.error(f"Catch-up settlement failed for user {user_id}: {message}")

            except Exception as e:
                logger.exception(f"Error in catch-up settlement for user {user_id}: {e}")
                continue

        logger.info("Catch-up settlement process completed")

    except Exception as e:
        logger.exception(f"Error in catch-up settlement: {e}")


if __name__ == "__main__":
    """Run MTM updater in standalone mode"""
    logger.info("Starting Sandbox MTM Updater")

    from database.sandbox_db import init_db

    init_db()

    mtm_interval = int(get_config("mtm_update_interval", "5"))

    if mtm_interval == 0:
        logger.info("Automatic MTM updates disabled (interval = 0)")
        exit(0)

    logger.info(f"MTM update interval: {mtm_interval} seconds")

    try:
        while True:
            update_all_positions_mtm()
            time.sleep(mtm_interval)
    except KeyboardInterrupt:
        logger.info("MTM updater stopped by user")
    except Exception as e:
        logger.exception(f"MTM updater error: {e}")

```


---

# FILE: sandbox\squareoff_manager.py

```py
# sandbox/squareoff_manager.py
"""
Square-Off Manager - Handles automatic position closure at exchange-specific times

Features:
- Auto square-off for MIS positions at configured times
- Exchange-specific timings (NSE/BSE: 3:15 PM, CDS/BCD: 4:45 PM, MCX: 11:30 PM, NCDEX: 5:00 PM)
- Market order creation for position closure
- Background scheduler for automatic execution
- Configurable square-off times
"""

import os
import sys
from datetime import datetime, time
from decimal import Decimal

import pytz

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.sandbox_db import SandboxPositions, db_session, get_config
from sandbox.position_manager import PositionManager
from utils.logging import get_logger

logger = get_logger(__name__)


class SquareOffManager:
    """Manages automatic square-off of MIS positions"""

    def __init__(self):
        self.ist = pytz.timezone("Asia/Kolkata")

        # Load square-off times from config
        self.square_off_times = {
            "NSE": self._parse_time(get_config("nse_bse_square_off_time", "15:15")),
            "BSE": self._parse_time(get_config("nse_bse_square_off_time", "15:15")),
            "NFO": self._parse_time(get_config("nse_bse_square_off_time", "15:15")),
            "BFO": self._parse_time(get_config("nse_bse_square_off_time", "15:15")),
            "CDS": self._parse_time(get_config("cds_bcd_square_off_time", "16:45")),
            "BCD": self._parse_time(get_config("cds_bcd_square_off_time", "16:45")),
            "MCX": self._parse_time(get_config("mcx_square_off_time", "23:30")),
            "NCDEX": self._parse_time(get_config("ncdex_square_off_time", "17:00")),
        }

    def _parse_time(self, time_str):
        """Parse time string (HH:MM) to time object"""
        try:
            hour, minute = map(int, time_str.split(":"))
            return time(hour=hour, minute=minute)
        except Exception as e:
            logger.exception(f"Error parsing time '{time_str}': {e}")
            return time(15, 15)  # Default to 3:15 PM

    def check_and_square_off(self):
        """
        Check if it's time to square-off positions and execute
        Should be called frequently (e.g., every minute)
        """
        try:
            now = datetime.now(self.ist)
            current_time = now.time()

            # Step 1: Cancel all open MIS orders past square-off time
            cancelled_count = self._cancel_open_mis_orders(current_time)

            # Step 2: Get all open MIS positions (quantity != 0)
            mis_positions = (
                SandboxPositions.query.filter_by(product="MIS")
                .filter(SandboxPositions.quantity != 0)
                .all()
            )

            positions_to_close = []
            if mis_positions:
                # Check each position against its exchange's square-off time
                for position in mis_positions:
                    exchange = position.exchange
                    square_off_time = self.square_off_times.get(exchange)

                    if not square_off_time:
                        logger.warning(f"No square-off time configured for exchange {exchange}")
                        continue

                    # Check if current time has passed square-off time
                    if current_time >= square_off_time:
                        positions_to_close.append(position)
            else:
                logger.debug("No MIS positions to square-off")

            if positions_to_close:
                logger.info(f"Found {len(positions_to_close)} MIS positions to square-off")
                self._square_off_positions(positions_to_close)
            else:
                logger.debug(f"No positions due for square-off at {current_time.strftime('%H:%M')}")

            # Notify UI if anything changed. The per-position close goes through
            # _execute_order (already publishes SandboxOrderFilledEvent), so
            # Positions/OrderBook will refresh per-fill. But the auto-cancel
            # path bypasses the service layer entirely, so without this emit
            # OrderBook would miss the cancellations until manual refresh.
            if cancelled_count or positions_to_close:
                try:
                    from events import SandboxAutoSquareOffEvent
                    from utils.event_bus import bus

                    bus.publish(
                        SandboxAutoSquareOffEvent(
                            mode="analyze",
                            api_type="sandbox.auto_squareoff",
                            cancelled_orders=cancelled_count,
                            closed_positions=len(positions_to_close),
                        )
                    )
                except Exception as pub_err:
                    logger.debug(f"Failed to publish SandboxAutoSquareOffEvent: {pub_err}")

        except Exception as e:
            logger.exception(f"Error checking square-off conditions: {e}")

    def _cancel_open_mis_orders(self, current_time):
        """Cancel all open MIS orders past their exchange's square-off time.

        Returns the number of orders successfully cancelled, so the caller
        can decide whether to emit a UI-refresh event.
        """
        cancelled_count = 0
        try:
            from database.sandbox_db import SandboxOrders
            from sandbox.order_manager import OrderManager

            # Get all open MIS orders
            open_orders = SandboxOrders.query.filter_by(product="MIS", order_status="open").all()

            if not open_orders:
                return 0

            for order in open_orders:
                exchange = order.exchange
                square_off_time = self.square_off_times.get(exchange)

                if not square_off_time:
                    continue

                # Check if current time has passed square-off time for this exchange
                if current_time >= square_off_time:
                    try:
                        order_manager = OrderManager(order.user_id)
                        success, response, status_code = order_manager.cancel_order(order.orderid)

                        if success:
                            logger.info(
                                f"Auto-cancelled MIS order {order.orderid} for {order.symbol} past square-off time"
                            )
                            cancelled_count += 1
                        else:
                            logger.error(
                                f"Failed to cancel MIS order {order.orderid}: {response.get('message', 'Unknown error')}"
                            )

                    except Exception as e:
                        logger.exception(f"Error cancelling MIS order {order.orderid}: {e}")

            if cancelled_count > 0:
                logger.info(
                    f"Auto-cancelled {cancelled_count} open MIS orders past square-off time"
                )

        except Exception as e:
            logger.exception(f"Error in _cancel_open_mis_orders: {e}")

        return cancelled_count

    def _square_off_positions(self, positions):
        """Square-off a list of positions"""
        success_count = 0
        error_count = 0

        for position in positions:
            try:
                pm = PositionManager(position.user_id)
                success, response, status_code = pm.close_position(
                    position.symbol, position.exchange, position.product
                )

                if success:
                    logger.info(
                        f"Auto square-off: {position.symbol} for user {position.user_id} - "
                        f"OrderID: {response.get('orderid', 'N/A')}"
                    )
                    success_count += 1
                else:
                    logger.error(
                        f"Failed to square-off {position.symbol} for user {position.user_id}: "
                        f"{response.get('message', 'Unknown error')}"
                    )
                    error_count += 1

            except Exception as e:
                logger.exception(f"Error squaring-off position {position.symbol}: {e}")
                error_count += 1

        logger.info(f"Square-off completed: {success_count} successful, {error_count} failed")

    def force_square_off_all_mis(self):
        """Force square-off all MIS positions immediately"""
        try:
            mis_positions = (
                SandboxPositions.query.filter_by(product="MIS")
                .filter(SandboxPositions.quantity != 0)
                .all()
            )

            if not mis_positions:
                logger.info("No MIS positions to force square-off")
                return True, "No positions to square-off"

            logger.warning(f"Force squaring-off {len(mis_positions)} MIS positions")
            self._square_off_positions(mis_positions)

            return True, f"Force square-off initiated for {len(mis_positions)} positions"

        except Exception as e:
            logger.exception(f"Error force squaring-off positions: {e}")
            return False, f"Error: {str(e)}"

    def get_time_to_square_off(self, exchange):
        """Get time remaining until square-off for an exchange"""
        try:
            square_off_time = self.square_off_times.get(exchange)

            if not square_off_time:
                return None

            now = datetime.now(self.ist)
            current_time = now.time()

            # Create datetime objects for comparison
            square_off_dt = datetime.combine(now.date(), square_off_time)
            current_dt = datetime.combine(now.date(), current_time)

            # Calculate time difference
            time_diff = square_off_dt - current_dt

            # If time has passed, return 0 or negative
            return time_diff.total_seconds()

        except Exception as e:
            logger.exception(f"Error calculating time to square-off: {e}")
            return None

    def get_square_off_status(self):
        """Get status of square-off times for all exchanges"""
        try:
            now = datetime.now(self.ist)
            current_time = now.time()

            status = {}

            for exchange, square_off_time in self.square_off_times.items():
                time_to_square_off = self.get_time_to_square_off(exchange)

                status[exchange] = {
                    "square_off_time": square_off_time.strftime("%H:%M"),
                    "current_time": current_time.strftime("%H:%M"),
                    "time_remaining_seconds": int(time_to_square_off) if time_to_square_off else 0,
                    "is_past_square_off": current_time >= square_off_time,
                }

            return status

        except Exception as e:
            logger.exception(f"Error getting square-off status: {e}")
            return {}


def run_square_off_check():
    """Run one cycle of square-off check"""
    som = SquareOffManager()
    som.check_and_square_off()


if __name__ == "__main__":
    """Run square-off manager in standalone mode"""
    import time as time_module

    logger.info("Starting Sandbox Square-Off Manager")

    from database.sandbox_db import init_db

    init_db()

    som = SquareOffManager()

    # Display square-off times
    status = som.get_square_off_status()
    logger.info("Configured square-off times:")
    for exchange, info in status.items():
        logger.info(f"  {exchange}: {info['square_off_time']} IST")

    # Run check every minute
    check_interval = 60  # 1 minute

    try:
        while True:
            run_square_off_check()
            time_module.sleep(check_interval)
    except KeyboardInterrupt:
        logger.info("Square-off manager stopped by user")
    except Exception as e:
        logger.exception(f"Square-off manager error: {e}")

```


---

# FILE: sandbox\squareoff_thread.py

```py
# sandbox/squareoff_thread.py
"""
Square-Off Manager Thread

Manages the square-off manager as a separate daemon thread using APScheduler that:
- Runs scheduled jobs at configured square-off times for each exchange
- Uses IST (Asia/Kolkata) timezone for all scheduling
- Cancels pending MIS orders at square-off time
- Closes open MIS positions at square-off time
- Reads all configuration from sandbox database config
"""

import logging
import threading

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from database.sandbox_db import get_config
from utils.logging import get_logger

logger = get_logger(__name__)

# Reduce APScheduler logging verbosity
# APScheduler logs every job execution at INFO level which is too noisy
# Set it to WARNING to only see errors and warnings
logging.getLogger("apscheduler.scheduler").setLevel(logging.WARNING)
logging.getLogger("apscheduler.executors.default").setLevel(logging.WARNING)

# Global scheduler instance
_scheduler = None
_scheduler_lock = threading.Lock()

# IST timezone
IST = pytz.timezone("Asia/Kolkata")


def _schedule_square_off_jobs(scheduler):
    """Schedule square-off jobs for all exchanges based on config"""
    from sandbox.squareoff_manager import SquareOffManager

    som = SquareOffManager()

    # Get configured times from database
    square_off_configs = {
        "NSE_BSE": get_config("nse_bse_square_off_time", "15:15"),
        "CDS_BCD": get_config("cds_bcd_square_off_time", "16:45"),
        "MCX": get_config("mcx_square_off_time", "23:30"),
        "NCDEX": get_config("ncdex_square_off_time", "17:00"),
    }

    logger.debug("Scheduling MIS square-off jobs (IST timezone):")

    for config_name, time_str in square_off_configs.items():
        try:
            hour, minute = map(int, time_str.split(":"))

            # Create cron trigger for the specific time in IST
            trigger = CronTrigger(hour=hour, minute=minute, timezone=IST)

            # Schedule the job
            job = scheduler.add_job(
                func=som.check_and_square_off,
                trigger=trigger,
                id=f"squareoff_{config_name}",
                name=f"MIS Square-off {config_name}",
                replace_existing=True,
                misfire_grace_time=300,  # Allow 5 minutes grace time
            )

            logger.debug(f"  {config_name}: {time_str} IST (Job ID: {job.id})")

        except Exception as e:
            logger.exception(f"Failed to schedule square-off for {config_name}: {e}")

    # Add a backup job that runs every minute to catch any missed executions
    # This provides a safety net in case:
    # - System was restarted during square-off time
    # - Primary cron job failed to execute
    # - There were timing issues or delays
    # Note: The check_and_square_off() function is smart - it only squares off
    # positions if current time is past the configured square-off time
    backup_job = scheduler.add_job(
        func=som.check_and_square_off,
        trigger="interval",
        minutes=1,
        id="squareoff_backup",
        name="MIS Square-off Backup Check",
        replace_existing=True,
        timezone=IST,
    )

    logger.debug(f"  Backup check: Every 1 minute (Job ID: {backup_job.id})")
    logger.debug("  Note: APScheduler logs have been set to WARNING level to reduce verbosity")

    # Schedule T+1 settlement job at midnight (00:00 IST)
    # This moves CNC positions to holdings after market close
    try:
        from sandbox.holdings_manager import process_all_t1_settlements

        settlement_trigger = CronTrigger(hour=0, minute=0, timezone=IST)

        settlement_job = scheduler.add_job(
            func=process_all_t1_settlements,
            trigger=settlement_trigger,
            id="t1_settlement",
            name="T+1 Settlement (CNC to Holdings)",
            replace_existing=True,
            misfire_grace_time=300,
        )

        logger.debug(f"  T+1 Settlement: 00:00 IST (Job ID: {settlement_job.id})")

    except Exception as e:
        logger.exception(f"Failed to schedule T+1 settlement: {e}")

    # Schedule auto-reset job based on configured reset day and time
    # This resets all user funds to starting capital on the configured day/time
    try:
        from sandbox.fund_manager import reset_all_user_funds

        reset_day = get_config("reset_day", "Never")
        reset_time_str = get_config("reset_time", "00:00")

        # Check if auto-reset is disabled
        if reset_day.lower() == "never":
            logger.debug("  Auto-Reset: Disabled (reset_day = Never)")
        else:
            reset_hour, reset_minute = map(int, reset_time_str.split(":"))

            # Map day names to APScheduler day_of_week values
            day_mapping = {
                "Monday": 0,
                "Tuesday": 1,
                "Wednesday": 2,
                "Thursday": 3,
                "Friday": 4,
                "Saturday": 5,
                "Sunday": 6,
            }

            reset_trigger = CronTrigger(
                day_of_week=day_mapping.get(reset_day, 6),  # Default to Sunday
                hour=reset_hour,
                minute=reset_minute,
                timezone=IST,
            )

            reset_job = scheduler.add_job(
                func=reset_all_user_funds,
                trigger=reset_trigger,
                id="auto_reset",
                name=f"Auto-Reset Funds ({reset_day} {reset_time_str})",
                replace_existing=True,
                misfire_grace_time=300,
            )

            logger.debug(f"  Auto-Reset: {reset_day} {reset_time_str} IST (Job ID: {reset_job.id})")

    except Exception as e:
        logger.exception(f"Failed to schedule auto-reset: {e}")

    # Schedule daily P&L snapshot at 23:59 IST (before session boundary reset)
    # This captures the end-of-day P&L for historical reporting
    try:
        import os
        from datetime import date
        from decimal import Decimal

        def capture_daily_pnl_snapshot():
            """Capture end-of-day P&L snapshot for all users"""
            try:
                from database.sandbox_db import (
                    SandboxDailyPnL,
                    SandboxFunds,
                    SandboxHoldings,
                    SandboxPositions,
                    db_session,
                )

                today = date.today()

                # Get all users with funds
                all_funds = SandboxFunds.query.all()

                for funds in all_funds:
                    user_id = funds.user_id

                    # Calculate positions unrealized P&L
                    positions = (
                        SandboxPositions.query.filter_by(user_id=user_id)
                        .filter(SandboxPositions.quantity != 0)
                        .all()
                    )
                    positions_unrealized = sum(Decimal(str(p.pnl or 0)) for p in positions)

                    # Calculate holdings unrealized P&L
                    holdings = (
                        SandboxHoldings.query.filter_by(user_id=user_id)
                        .filter(SandboxHoldings.quantity != 0)
                        .all()
                    )
                    holdings_unrealized = sum(Decimal(str(h.pnl or 0)) for h in holdings)

                    # Get today's realized P&L
                    realized_pnl = Decimal(str(funds.today_realized_pnl or 0))

                    # Total MTM = Realized + Unrealized (positions + holdings)
                    total_unrealized = positions_unrealized + holdings_unrealized
                    total_mtm = realized_pnl + total_unrealized

                    # Portfolio value
                    portfolio_value = Decimal(str(funds.available_balance or 0)) + Decimal(
                        str(funds.used_margin or 0)
                    )

                    # Check if snapshot already exists for today
                    existing = SandboxDailyPnL.query.filter_by(user_id=user_id, date=today).first()

                    if existing:
                        # Update existing snapshot
                        existing.realized_pnl = realized_pnl
                        existing.positions_unrealized_pnl = positions_unrealized
                        existing.holdings_unrealized_pnl = holdings_unrealized
                        existing.total_mtm = total_mtm
                        existing.available_balance = funds.available_balance
                        existing.used_margin = funds.used_margin
                        existing.portfolio_value = portfolio_value
                    else:
                        # Create new snapshot
                        snapshot = SandboxDailyPnL(
                            user_id=user_id,
                            date=today,
                            realized_pnl=realized_pnl,
                            positions_unrealized_pnl=positions_unrealized,
                            holdings_unrealized_pnl=holdings_unrealized,
                            total_mtm=total_mtm,
                            available_balance=funds.available_balance,
                            used_margin=funds.used_margin,
                            portfolio_value=portfolio_value,
                        )
                        db_session.add(snapshot)

                db_session.commit()
                logger.info(f"Daily P&L snapshot captured for {len(all_funds)} users")

            except Exception as e:
                db_session.rollback()
                logger.exception(f"Error capturing daily P&L snapshot: {e}")

        # Schedule snapshot at 23:59 IST (before midnight reset)
        snapshot_trigger = CronTrigger(hour=23, minute=59, timezone=IST)

        snapshot_job = scheduler.add_job(
            func=capture_daily_pnl_snapshot,
            trigger=snapshot_trigger,
            id="daily_pnl_snapshot",
            name="Daily PnL Snapshot (23:59 IST)",
            replace_existing=True,
            misfire_grace_time=300,
        )

        logger.debug(f"  Daily PnL Snapshot: 23:59 IST (Job ID: {snapshot_job.id})")

    except Exception as e:
        logger.exception(f"Failed to schedule daily PnL snapshot: {e}")

    # Schedule daily P&L reset at SESSION_EXPIRY_TIME (default 03:00 IST)
    # This resets today_realized_pnl for all users at session boundary
    try:

        def reset_daily_pnl():
            """Reset today_realized_pnl for all users at session boundary"""
            try:
                from database.sandbox_db import SandboxFunds, SandboxPositions, db_session

                # Reset funds - today_realized_pnl
                funds_count = SandboxFunds.query.update({"today_realized_pnl": Decimal("0.00")})

                # Reset positions - today_realized_pnl
                positions_count = SandboxPositions.query.update(
                    {"today_realized_pnl": Decimal("0.00")}
                )

                db_session.commit()
                logger.info(
                    f"Daily P&L reset completed: {funds_count} funds, {positions_count} positions reset"
                )

            except Exception as e:
                db_session.rollback()
                logger.exception(f"Error in daily P&L reset: {e}")

        # Get reset time from SESSION_EXPIRY_TIME env variable
        session_expiry_str = os.getenv("SESSION_EXPIRY_TIME", "03:00")
        reset_hour, reset_minute = map(int, session_expiry_str.split(":"))

        pnl_reset_trigger = CronTrigger(hour=reset_hour, minute=reset_minute, timezone=IST)

        pnl_reset_job = scheduler.add_job(
            func=reset_daily_pnl,
            trigger=pnl_reset_trigger,
            id="daily_pnl_reset",
            name=f"Daily PnL Reset ({session_expiry_str} IST)",
            replace_existing=True,
            misfire_grace_time=300,
        )

        logger.debug(f"  Daily PnL Reset: {session_expiry_str} IST (Job ID: {pnl_reset_job.id})")

    except Exception as e:
        logger.exception(f"Failed to schedule daily PnL reset: {e}")


def start_squareoff_scheduler():
    """
    Start the square-off scheduler daemon thread
    Thread-safe - only one instance will run
    """
    global _scheduler

    with _scheduler_lock:
        if _scheduler is not None and _scheduler.running:
            logger.debug("Square-off scheduler already running")
            return True, "Square-off scheduler already running"

        try:
            # Create background scheduler with IST timezone
            _scheduler = BackgroundScheduler(
                timezone=IST,
                daemon=True,
                job_defaults={
                    "coalesce": True,  # Combine missed executions
                    "max_instances": 1,  # Only one instance of each job at a time
                },
            )

            # Schedule all square-off jobs
            _schedule_square_off_jobs(_scheduler)

            # Start the scheduler
            _scheduler.start()

            logger.debug("Square-off scheduler started successfully")
            return True, "Square-off scheduler started"

        except Exception as e:
            logger.exception(f"Failed to start square-off scheduler: {e}")
            return False, f"Failed to start square-off scheduler: {str(e)}"


def stop_squareoff_scheduler():
    """
    Stop the square-off scheduler gracefully
    """
    global _scheduler

    with _scheduler_lock:
        if _scheduler is None or not _scheduler.running:
            logger.debug("Square-off scheduler not running")
            return True, "Square-off scheduler not running"

        try:
            logger.info("Stopping square-off scheduler...")
            _scheduler.shutdown(wait=True)
            _scheduler = None
            logger.info("Square-off scheduler stopped successfully")
            return True, "Square-off scheduler stopped"

        except Exception as e:
            logger.exception(f"Error stopping square-off scheduler: {e}")
            return False, f"Error stopping square-off scheduler: {str(e)}"


def is_squareoff_scheduler_running():
    """Check if square-off scheduler is running"""
    global _scheduler
    return _scheduler is not None and _scheduler.running


def get_squareoff_scheduler_status():
    """Get status information about the square-off scheduler"""
    global _scheduler

    if _scheduler is None or not _scheduler.running:
        return {"running": False, "jobs": []}

    jobs_info = []
    for job in _scheduler.get_jobs():
        next_run = job.next_run_time
        jobs_info.append(
            {
                "id": job.id,
                "name": job.name,
                "next_run": next_run.strftime("%Y-%m-%d %H:%M:%S %Z") if next_run else "N/A",
            }
        )

    return {"running": True, "timezone": str(IST), "jobs": jobs_info}


def reload_squareoff_schedule():
    """
    Reload square-off schedule from config
    Useful when config is updated
    """
    global _scheduler

    if _scheduler is None or not _scheduler.running:
        logger.warning("Cannot reload schedule - scheduler not running")
        return False, "Scheduler not running"

    try:
        logger.info("Reloading square-off schedule from config...")

        # Remove all existing jobs
        _scheduler.remove_all_jobs()

        # Re-schedule jobs with new config
        _schedule_square_off_jobs(_scheduler)

        logger.info("Square-off schedule reloaded successfully")
        return True, "Schedule reloaded"

    except Exception as e:
        logger.exception(f"Error reloading schedule: {e}")
        return False, f"Error reloading schedule: {str(e)}"

```


---

# FILE: sandbox\websocket_execution_engine.py

```py
# sandbox/websocket_execution_engine.py
"""
WebSocket-based Execution Engine - Event-driven order execution

Features:
- Real-time order execution using WebSocket market data
- Subscribes to MarketDataService for LTP updates
- Immediate execution when price conditions are met (sub-second latency)
- Automatic fallback to polling engine if WebSocket data is stale
- Thread-safe order index management
"""

import os
import sys
import threading
import time
from decimal import Decimal
from typing import Dict, List, Optional, Set

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.sandbox_db import SandboxOrders, db_session
from services.market_data_service import get_market_data_service
from services.websocket_service import subscribe_to_symbols, unsubscribe_from_symbols
from utils.logging import get_logger

logger = get_logger(__name__)


class WebSocketExecutionEngine:
    """
    Event-driven execution engine that uses WebSocket market data
    instead of polling for order execution.
    """

    def __init__(self):
        self.market_data_service = get_market_data_service()
        self._subscriber_id: str | None = None
        self._running = False
        self._lock = threading.Lock()

        # Index of pending orders by symbol key (exchange:symbol)
        # Maps symbol_key -> list of order IDs
        self._pending_orders_index: dict[str, list[str]] = {}

        # Track symbols we're monitoring
        self._monitored_symbols: set[str] = set()

        # Track per-user symbol subscriptions (refcounts)
        # {user_id: {symbol_key: count}}
        self._user_symbol_refcounts: dict[str, dict[str, int]] = {}

        # Fallback settings
        self.fallback_enabled = os.getenv("SANDBOX_ENGINE_FALLBACK", "true").lower() == "true"
        self.stale_data_threshold = 30  # seconds
        self._fallback_thread: threading.Thread | None = None
        self._fallback_running = False

        # Import execution engine for order processing and fallback
        from sandbox.execution_engine import ExecutionEngine

        self._execution_engine = ExecutionEngine()

    def start(self):
        """Start the WebSocket execution engine"""
        if self._running:
            logger.debug("WebSocket execution engine already running")
            return

        logger.debug("Starting WebSocket execution engine")
        self._running = True

        # Build initial order index from database
        self._rebuild_order_index()

        # Subscribe to MarketDataService with CRITICAL priority for immediate processing
        try:
            self._subscriber_id = self.market_data_service.subscribe_critical(
                callback=self._on_market_data,
                filter_symbols=None,  # All symbols - we filter in callback
                name="sandbox_websocket_execution_engine",
            )
            logger.debug(f"Subscribed to MarketDataService with ID: {self._subscriber_id}")
        except Exception as e:
            logger.exception(f"Failed to subscribe to MarketDataService: {e}")
            self._running = False
            return

        # Start health monitoring thread
        self._start_health_monitor()

    def stop(self):
        """Stop the WebSocket execution engine"""
        if not self._running:
            return

        logger.info("Stopping WebSocket execution engine")
        self._running = False

        # Stop fallback if running
        self._stop_fallback()

        # Unsubscribe from MarketDataService
        if self._subscriber_id:
            try:
                self.market_data_service.unsubscribe_from_updates(self._subscriber_id)
                logger.info("Unsubscribed from MarketDataService")
            except Exception as e:
                logger.exception(f"Error unsubscribing from MarketDataService: {e}")

        self._subscriber_id = None

        # Unsubscribe all WebSocket symbols for all users
        self._unsubscribe_all_ws()

    def _rebuild_order_index(self):
        """Build index of pending orders from database"""
        subscriptions_to_add: dict[str, list[tuple[str, str]]] = {}

        with self._lock:
            self._pending_orders_index.clear()
            self._monitored_symbols.clear()
            self._user_symbol_refcounts.clear()

            try:
                pending_orders = SandboxOrders.query.filter_by(order_status="open").all()

                for order in pending_orders:
                    symbol_key = f"{order.exchange}:{order.symbol}"
                    if symbol_key not in self._pending_orders_index:
                        self._pending_orders_index[symbol_key] = []
                    self._pending_orders_index[symbol_key].append(order.orderid)
                    self._monitored_symbols.add(symbol_key)
                    self._increment_user_symbol_refcount(order.user_id, symbol_key)

                logger.debug(
                    f"Built order index: {len(pending_orders)} orders across {len(self._monitored_symbols)} symbols"
                )

            except Exception as e:
                logger.exception(f"Error building order index: {e}")
                return

            # Build subscriptions per user (outside lock)
            for user_id, symbols in self._user_symbol_refcounts.items():
                new_symbols = []
                for symbol_key in symbols:
                    exchange, symbol = symbol_key.split(":", 1)
                    new_symbols.append((symbol, exchange))
                if new_symbols:
                    subscriptions_to_add[user_id] = new_symbols

        # Subscribe for all users
        for user_id, symbols in subscriptions_to_add.items():
            self._subscribe_ws_symbols(user_id, symbols)

    def notify_order_placed(self, order):
        """Called when a new order is placed to update the index"""
        symbol_key = f"{order.exchange}:{order.symbol}"
        subscribe_user = None
        subscribe_symbol = None

        with self._lock:
            if symbol_key not in self._pending_orders_index:
                self._pending_orders_index[symbol_key] = []

            if order.orderid not in self._pending_orders_index[symbol_key]:
                self._pending_orders_index[symbol_key].append(order.orderid)
                self._monitored_symbols.add(symbol_key)
                logger.debug(f"Added order {order.orderid} to index for {symbol_key}")

            # Increment refcount and decide if we need to subscribe
            if self._increment_user_symbol_refcount(order.user_id, symbol_key):
                subscribe_user = order.user_id
                subscribe_symbol = symbol_key

        if subscribe_user and subscribe_symbol:
            exchange, symbol = subscribe_symbol.split(":", 1)
            self._subscribe_ws_symbols(subscribe_user, [(symbol, exchange)])

    def notify_order_completed(self, order_id: str, symbol_key: str, user_id: str | None = None):
        """Called when an order is completed/cancelled to update the index"""
        unsubscribe_user = None
        unsubscribe_symbol = None

        with self._lock:
            if symbol_key and symbol_key in self._pending_orders_index:
                if order_id in self._pending_orders_index[symbol_key]:
                    self._pending_orders_index[symbol_key].remove(order_id)
                    logger.debug(f"Removed order {order_id} from index for {symbol_key}")

                # Clean up empty symbol entries
                if not self._pending_orders_index[symbol_key]:
                    del self._pending_orders_index[symbol_key]
                    self._monitored_symbols.discard(symbol_key)
            else:
                # Fallback: remove order_id from any symbol list
                self._remove_order_from_index(order_id)

            # Decrement refcount and decide if we should unsubscribe
            if user_id and symbol_key:
                if self._decrement_user_symbol_refcount(user_id, symbol_key):
                    unsubscribe_user = user_id
                    unsubscribe_symbol = symbol_key

        if unsubscribe_user and unsubscribe_symbol:
            exchange, symbol = unsubscribe_symbol.split(":", 1)
            self._unsubscribe_ws_symbols(unsubscribe_user, [(symbol, exchange)])

    def _on_market_data(self, data: dict):
        """
        Callback when new market data arrives from WebSocket.
        Called immediately when LTP updates are received.
        """
        if not self._running:
            return

        try:
            symbol = data.get("symbol", "").upper()
            exchange = data.get("exchange", "")
            market_data = data.get("data", {})
            ltp = market_data.get("ltp")

            if not ltp or not symbol or not exchange:
                return

            symbol_key = f"{exchange}:{symbol}"

            # Check if we have pending orders for this symbol
            with self._lock:
                order_ids = self._pending_orders_index.get(symbol_key, []).copy()

            if not order_ids:
                return

            # Process each pending order for this symbol
            for order_id in order_ids:
                try:
                    self._check_and_execute_order(order_id, Decimal(str(ltp)))
                except Exception as e:
                    logger.exception(f"Error processing order {order_id}: {e}")

        except Exception as e:
            logger.exception(f"Error in market data callback: {e}")

    def _check_and_execute_order(self, order_id: str, ltp: Decimal):
        """
        Check if an order should execute at the current LTP and execute if conditions are met.
        """
        try:
            # Fetch the order from database
            order = SandboxOrders.query.filter_by(orderid=order_id, order_status="open").first()

            if not order:
                # Order no longer pending, remove from index and unsubscribe if possible
                stale_order = SandboxOrders.query.filter_by(orderid=order_id).first()
                if stale_order:
                    symbol_key = f"{stale_order.exchange}:{stale_order.symbol}"
                    self.notify_order_completed(order_id, symbol_key, stale_order.user_id)
                else:
                    self.notify_order_completed(order_id, "", None)
                return

            # Create a mock quote for the execution engine's _process_order method
            quote = {
                "ltp": float(ltp),
                "bid": float(ltp),  # Use LTP as bid/ask fallback
                "ask": float(ltp),
            }

            # Use the existing execution engine's order processing logic
            self._execution_engine._process_order(order, quote)

            # If order was executed, remove from index
            # Refresh the order to check status
            db_session.refresh(order)
            if order.order_status != "open":
                symbol_key = f"{order.exchange}:{order.symbol}"
                self.notify_order_completed(order_id, symbol_key, order.user_id)

        except Exception as e:
            logger.exception(f"Error checking/executing order {order_id}: {e}")

    def _start_health_monitor(self):
        """Start a thread to monitor WebSocket health and trigger fallback if needed"""

        def monitor():
            while self._running:
                try:
                    # Check if market data is fresh
                    is_fresh = self.market_data_service.is_data_fresh(
                        max_age_seconds=self.stale_data_threshold
                    )

                    if not is_fresh and self.fallback_enabled and not self._fallback_running:
                        logger.debug("WebSocket data is stale, starting polling fallback")
                        self._start_fallback()
                    elif is_fresh and self._fallback_running:
                        logger.debug("WebSocket data recovered, stopping polling fallback")
                        self._stop_fallback()

                except Exception as e:
                    logger.exception(f"Error in health monitor: {e}")

                time.sleep(5)  # Check every 5 seconds

        monitor_thread = threading.Thread(
            target=monitor, daemon=True, name="WSExecEngine-HealthMonitor"
        )
        monitor_thread.start()
        logger.debug("Started health monitor thread")

    def _start_fallback(self):
        """Start polling fallback when WebSocket is unavailable"""
        if self._fallback_running:
            return

        self._fallback_running = True

        def fallback_loop():
            from database.sandbox_db import get_config
            from sandbox.execution_engine import run_execution_engine_once

            check_interval = int(get_config("order_check_interval", "5"))
            logger.debug(f"Fallback polling started with {check_interval}s interval")

            while self._fallback_running and self._running:
                try:
                    run_execution_engine_once()
                except Exception as e:
                    logger.exception(f"Error in fallback polling: {e}")

                # Sleep in small increments for quick shutdown
                for _ in range(check_interval):
                    if not self._fallback_running or not self._running:
                        break
                    time.sleep(1)

            logger.debug("Fallback polling stopped")

        self._fallback_thread = threading.Thread(
            target=fallback_loop, daemon=True, name="WSExecEngine-Fallback"
        )
        self._fallback_thread.start()

    def _stop_fallback(self):
        """Stop polling fallback"""
        self._fallback_running = False

        if self._fallback_thread and self._fallback_thread.is_alive():
            self._fallback_thread.join(timeout=10)
            self._fallback_thread = None

    def _increment_user_symbol_refcount(self, user_id: str, symbol_key: str) -> bool:
        """
        Increment refcount for a user's symbol. Returns True if this is the first ref.
        """
        if user_id not in self._user_symbol_refcounts:
            self._user_symbol_refcounts[user_id] = {}

        current = self._user_symbol_refcounts[user_id].get(symbol_key, 0)
        self._user_symbol_refcounts[user_id][symbol_key] = current + 1
        return current == 0

    def _decrement_user_symbol_refcount(self, user_id: str, symbol_key: str) -> bool:
        """
        Decrement refcount for a user's symbol. Returns True if count reaches zero.
        """
        if user_id not in self._user_symbol_refcounts:
            return False

        current = self._user_symbol_refcounts[user_id].get(symbol_key, 0)
        if current <= 1:
            self._user_symbol_refcounts[user_id].pop(symbol_key, None)
            if not self._user_symbol_refcounts[user_id]:
                self._user_symbol_refcounts.pop(user_id, None)
            return True

        self._user_symbol_refcounts[user_id][symbol_key] = current - 1
        return False

    def _remove_order_from_index(self, order_id: str):
        """Remove order_id from all symbol buckets (fallback cleanup)."""
        to_cleanup = []
        for symbol_key, order_ids in self._pending_orders_index.items():
            if order_id in order_ids:
                order_ids.remove(order_id)
                logger.debug(f"Removed order {order_id} from index for {symbol_key} (fallback)")
                if not order_ids:
                    to_cleanup.append(symbol_key)
        for symbol_key in to_cleanup:
            del self._pending_orders_index[symbol_key]
            self._monitored_symbols.discard(symbol_key)

    def _subscribe_ws_symbols(self, user_id: str, symbols: list[tuple[str, str]]):
        """Subscribe to LTP via WebSocket for the given user and symbols."""
        if not symbols:
            return

        try:
            from database.auth_db import get_api_key_for_tradingview, get_broker_name

            api_key = get_api_key_for_tradingview(user_id)
            if not api_key:
                logger.warning(
                    f"WebSocket subscribe skipped: no API key for user {user_id}"
                )
                return
            broker = get_broker_name(api_key) if api_key else None
            broker_name = broker or "unknown"
            if broker_name == "unknown":
                logger.warning(
                    f"WebSocket subscribe may fail: unknown broker for user {user_id}"
                )

            symbol_payload = [{"symbol": s, "exchange": e} for s, e in symbols]
            success, response, status_code = subscribe_to_symbols(
                username=user_id, broker=broker_name, symbols=symbol_payload, mode="LTP"
            )
            if not success:
                logger.warning(
                    f"WebSocket subscribe failed for user {user_id}: {response.get('message')} (status {status_code})"
                )
        except Exception as e:
            logger.exception(f"Error subscribing WebSocket symbols for user {user_id}: {e}")

    def _unsubscribe_ws_symbols(self, user_id: str, symbols: list[tuple[str, str]]):
        """Unsubscribe from LTP via WebSocket for the given user and symbols."""
        if not symbols:
            return

        try:
            from database.auth_db import get_api_key_for_tradingview, get_broker_name

            api_key = get_api_key_for_tradingview(user_id)
            if not api_key:
                logger.warning(
                    f"WebSocket unsubscribe skipped: no API key for user {user_id}"
                )
                return
            broker = get_broker_name(api_key) if api_key else None
            broker_name = broker or "unknown"
            if broker_name == "unknown":
                logger.warning(
                    f"WebSocket unsubscribe may fail: unknown broker for user {user_id}"
                )

            symbol_payload = [{"symbol": s, "exchange": e} for s, e in symbols]
            success, response, status_code = unsubscribe_from_symbols(
                username=user_id, broker=broker_name, symbols=symbol_payload, mode="LTP"
            )
            if not success:
                logger.warning(
                    f"WebSocket unsubscribe failed for user {user_id}: {response.get('message')} (status {status_code})"
                )
        except Exception as e:
            logger.exception(f"Error unsubscribing WebSocket symbols for user {user_id}: {e}")

    def _unsubscribe_all_ws(self):
        """Unsubscribe all WebSocket symbols for all users."""
        users_to_unsub = []
        with self._lock:
            for user_id, symbols in self._user_symbol_refcounts.items():
                symbol_list = []
                for symbol_key in symbols:
                    exchange, symbol = symbol_key.split(":", 1)
                    symbol_list.append((symbol, exchange))
                if symbol_list:
                    users_to_unsub.append((user_id, symbol_list))
            self._user_symbol_refcounts.clear()

        for user_id, symbols in users_to_unsub:
            self._unsubscribe_ws_symbols(user_id, symbols)


# Global instance for singleton access
_websocket_execution_engine: WebSocketExecutionEngine | None = None
_engine_lock = threading.Lock()


def get_websocket_execution_engine() -> WebSocketExecutionEngine:
    """Get or create the singleton WebSocket execution engine instance"""
    global _websocket_execution_engine

    with _engine_lock:
        if _websocket_execution_engine is None:
            _websocket_execution_engine = WebSocketExecutionEngine()
        return _websocket_execution_engine


def start_websocket_execution_engine():
    """Start the WebSocket execution engine"""
    engine = get_websocket_execution_engine()
    engine.start()
    return True, "WebSocket execution engine started"


def stop_websocket_execution_engine():
    """Stop the WebSocket execution engine"""
    global _websocket_execution_engine

    with _engine_lock:
        if _websocket_execution_engine:
            _websocket_execution_engine.stop()
            _websocket_execution_engine = None
            return True, "WebSocket execution engine stopped"
        return True, "WebSocket execution engine not running"


def is_websocket_execution_engine_running() -> bool:
    """Check if WebSocket execution engine is running"""
    with _engine_lock:
        return _websocket_execution_engine is not None and _websocket_execution_engine._running

```
