# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\deltaexchange\mapping



---

# FILE: broker\deltaexchange\mapping\margin_data.py

```py
# mapping/margin_data.py
# Mapping OpenAlgo margin positions to Delta Exchange margin_required API format
# Delta Exchange endpoint: GET /v2/products/{product_id}/margin_required

from broker.deltaexchange.mapping.transform_data import _order_size
from database.token_db import get_token
from utils.logging import get_logger

logger = get_logger(__name__)


def transform_margin_positions(positions):
    """
    Transform OpenAlgo margin position list to Delta Exchange format.

    Each OpenAlgo position is converted to a dict with the fields needed
    to call GET /v2/products/{product_id}/margin_required:
        product_id  (int)  – from token DB (token = product_id on Delta)
        size        (int|float)  – contracts (int) or spot quantity (float)
        side        (str)  – "buy" or "sell"
        order_type  (str)  – "limit_order" or "market_order"
        limit_price (str)  – required if order_type == "limit_order"

    Args:
        positions: List of dicts in OpenAlgo format
            {symbol, exchange, action (BUY/SELL), quantity, product,
             price (optional), pricetype (optional)}

    Returns:
        List of dicts in Delta Exchange margin format, skipping invalid entries.
    """
    transformed = []
    skipped = []

    for pos in positions:
        try:
            symbol = pos["symbol"]
            exchange = pos.get("exchange", "CRYPTO")

            # token == product_id on Delta Exchange
            token = get_token(symbol, exchange)
            if not token:
                logger.warning(f"Token not found for {symbol} on {exchange}")
                skipped.append(symbol)
                continue

            product_id = int(token)
            side = pos["action"].lower()  # "buy" or "sell"

            pricetype = pos.get("pricetype", "MARKET").upper()
            if pricetype in ("LIMIT", "SL"):
                order_type = "limit_order"
            else:
                order_type = "market_order"

            entry = {
                "product_id": product_id,
                "size": _order_size(pos["quantity"], symbol, exchange),
                "side": side,
                "order_type": order_type,
            }

            price = pos.get("price", 0)
            if order_type == "limit_order":
                try:
                    price_f = float(price) if price is not None else 0.0
                except (ValueError, TypeError):
                    price_f = 0.0

                if price_f > 0:
                    entry["limit_price"] = str(price_f)
                else:
                    # limit_price is required for limit_order but none was provided —
                    # fall back to market_order so the margin call still succeeds
                    logger.warning(
                        f"limit_order for {symbol} has no valid price "
                        f"(got {price!r}); falling back to market_order for margin calculation"
                    )
                    entry["order_type"] = "market_order"

            transformed.append(entry)
            logger.debug(
                f"Transformed margin position: {symbol} → product_id={product_id} "
                f"size={entry['size']} side={side}"
            )

        except Exception as e:
            logger.error(f"Error transforming margin position {pos}: {e}")
            skipped.append(str(pos.get("symbol", "unknown")))

    if skipped:
        logger.warning(f"Skipped {len(skipped)} position(s): {', '.join(skipped)}")

    return transformed


def parse_margin_response(response_data):
    """
    Parse the Delta Exchange GET /v2/products/{product_id}/margin_required response.

    Expected response shape:
        {
          "success": true,
          "result": {
            "initial_margin":      "500.00",   // margin required to open
            "maintenance_margin":  "250.00",   // margin to keep position open
            "order_size":          10
          }
        }

    OpenAlgo margin format (3 fields):
        total_margin_required  ← initial_margin
        span_margin            ← initial_margin  (Delta has no SPAN concept; use same)
        exposure_margin        ← 0.00            (no separate exposure on crypto)

    Returns:
        {"status": "success", "data": {...}} or {"status": "error", "message": ...}
    """
    try:
        if not response_data or not isinstance(response_data, dict):
            return {"status": "error", "message": "Invalid response from Delta Exchange"}

        if not response_data.get("success", False):
            error = response_data.get("error", {})
            msg = error.get("message", "Unknown error") if isinstance(error, dict) else str(error)
            return {"status": "error", "message": msg}

        result = response_data.get("result", {})
        if not isinstance(result, dict):
            return {"status": "error", "message": "Unexpected margin result format"}

        initial_margin = _f(result.get("initial_margin", 0))

        return {
            "status": "success",
            "data": {
                "total_margin_required": initial_margin,
                "span_margin": initial_margin,
                "exposure_margin": 0.0,
            },
        }

    except Exception as e:
        logger.error(f"Error parsing margin_required response: {e}")
        return {"status": "error", "message": f"Failed to parse margin response: {e}"}


def _f(value):
    """Safe float conversion."""
    try:
        return float(value or 0)
    except (ValueError, TypeError):
        return 0.0

```


---

# FILE: broker\deltaexchange\mapping\order_data.py

```py
import json

from database.token_db import get_oa_symbol, get_symbol, get_symbol_info
from utils.logging import get_logger

logger = get_logger(__name__)


def map_order_data(order_data):
    """
    Normalises a list of Delta Exchange order dicts to the OpenAlgo internal format.

    Delta Exchange order fields used:
        id               – raw integer order ID
        product_id       – contract / product ID
        product_symbol   – contract symbol (e.g. "BTCUSD")
        side             – "buy" | "sell"
        order_type       – "limit_order" | "market_order"
        stop_order_type  – "stop_loss_order" (present on SL/SL-M orders)
        state            – "open" | "pending" | "closed" | "cancelled"
        size             – total order size (contracts)
        unfilled_size    – contracts not yet filled
        limit_price      – limit price (string)
        stop_price       – stop trigger price (string, optional)
        reduce_only      – bool, true if order can only reduce a position
        created_at       – creation timestamp (microseconds string)
    """
    try:
        if order_data is None:
            return []
        if isinstance(order_data, dict) and not order_data.get("success", True):
            logger.error(f"Error in order data: {order_data.get('error', 'Unknown error')}")
            return []
        if isinstance(order_data, str):
            logger.error(f"Received string instead of order list: {order_data[:200]}")
            return []
        if not isinstance(order_data, list):
            logger.warning(f"Expected list, got {type(order_data)}")
            return []

        for order in order_data:
            if not isinstance(order, dict):
                continue

            raw_id = order.get("id", "")
            product_id = order.get("product_id", "")
            product_symbol = order.get("product_symbol", "")

            # Composite order ID: "{product_id}:{order_id}"
            order["orderId"] = f"{product_id}:{raw_id}" if product_id else str(raw_id)

            # Symbol: prefer DB lookup, fall back to product_symbol
            symbol_from_db = get_symbol(str(product_id), "CRYPTO") if product_id else None
            order["tradingSymbol"] = symbol_from_db or product_symbol

            # Exchange and product type (Delta = single crypto exchange)
            order["exchangeSegment"] = "CRYPTO"
            order["productType"] = "NRML"

            # Transaction type
            order["transactionType"] = order.get("side", "").upper()  # BUY / SELL

            # Order type — must check stop_order_type FIRST:
            #   stop_loss_order + limit_order  → "SL"
            #   stop_loss_order + market_order → "SL-M"
            #   (no stop)       + limit_order  → "LIMIT"
            #   (no stop)       + market_order → "MARKET"
            raw_ot = order.get("order_type", "")
            is_stop = order.get("stop_order_type") == "stop_loss_order"
            if is_stop:
                order["orderType"] = "SL" if raw_ot == "limit_order" else "SL-M"
            elif raw_ot == "limit_order":
                order["orderType"] = "LIMIT"
            elif raw_ot == "market_order":
                order["orderType"] = "MARKET"
            else:
                order["orderType"] = raw_ot.upper()

            # Status mapping
            # "pending" = stop order waiting to be triggered → treat as open
            state = order.get("state", "").lower()
            if state == "open":
                order["orderStatus"] = "open"
            elif state in ("closed", "filled"):
                order["orderStatus"] = "complete"
            elif state == "cancelled":
                order["orderStatus"] = "cancelled"
            elif state == "pending":
                order["orderStatus"] = "open"  # pending = stop order triggered but not filled
            else:
                order["orderStatus"] = state

            # Numeric fields
            order["quantity"] = order.get("size", 0)
            order["price"] = float(order.get("limit_price") or 0)
            order["triggerPrice"] = float(order.get("stop_price") or 0)
            order["updateTime"] = order.get("created_at", "")

            # Reduce-only flag (crypto-specific, pass through for display)
            order["reduceOnly"] = bool(order.get("reduce_only", False))

            # Stop trigger method (how the stop price is evaluated)
            order["stopTriggerMethod"] = order.get("stop_trigger_method", "")

            # Trailing stop amount (present on trailing stop orders)
            order["trailAmount"] = order.get("trail_amount", "")

            # Post-only flag
            order["postOnly"] = bool(order.get("post_only", False))

            # Client order ID (caller-supplied reference)
            order["clientOrderId"] = order.get("client_order_id", "")

            # Bracket order fields (pass through for display/reconciliation)
            order["bracketStopLossPrice"] = order.get("bracket_stop_loss_price", "")
            order["bracketStopLossLimitPrice"] = order.get("bracket_stop_loss_limit_price", "")
            order["bracketTrailAmount"] = order.get("bracket_trail_amount", "")
            order["bracketTakeProfitPrice"] = order.get("bracket_take_profit_price", "")
            order["bracketTakeProfitLimitPrice"] = order.get("bracket_take_profit_limit_price", "")

        return order_data

    except Exception as e:
        logger.error(f"Exception in map_order_data: {e}")
        return []


def calculate_order_statistics(order_data):
    """
    Calculates statistics from order data, including totals for buy orders, sell orders,
    completed orders, open orders, and rejected orders.

    Parameters:
    - order_data: A list of dictionaries, where each dictionary represents an order.

    Returns:
    - A dictionary containing counts of different types of orders.
    """
    try:
        # Initialize counters
        total_buy_orders = total_sell_orders = 0
        total_completed_orders = total_open_orders = total_rejected_orders = 0

        # Handle None or non-list inputs
        if not order_data or not isinstance(order_data, list):
            return {
                "total_buy_orders": 0,
                "total_sell_orders": 0,
                "total_completed_orders": 0,
                "total_open_orders": 0,
                "total_rejected_orders": 0,
            }

        for order in order_data:
            if not isinstance(order, dict):
                continue

            # Count buy and sell orders
            if order.get("transactionType") == "BUY":
                total_buy_orders += 1
            elif order.get("transactionType") == "SELL":
                total_sell_orders += 1

            # Delta Exchange states: open/pending → open, closed/filled → complete,
            # cancelled → cancelled.  (rejected is rare on Delta)
            status = order.get("orderStatus", "").lower()
            if status in ("complete", "closed", "filled"):
                total_completed_orders += 1
                order["orderStatus"] = "complete"
            elif status in ("open", "pending"):
                total_open_orders += 1
                order["orderStatus"] = "open"
            elif status == "rejected":
                total_rejected_orders += 1
                order["orderStatus"] = "rejected"
            elif status == "cancelled":
                order["orderStatus"] = "cancelled"

        # Compile and return the statistics
        return {
            "total_buy_orders": total_buy_orders,
            "total_sell_orders": total_sell_orders,
            "total_completed_orders": total_completed_orders,
            "total_open_orders": total_open_orders,
            "total_rejected_orders": total_rejected_orders,
        }
    except Exception as e:
        logger.error(f"Exception in calculate_order_statistics: {e}")
        return {
            "total_buy_orders": 0,
            "total_sell_orders": 0,
            "total_completed_orders": 0,
            "total_open_orders": 0,
            "total_rejected_orders": 0,
        }


def transform_order_data(orders):
    try:
        # Handle None input
        if orders is None:
            return []

        # Directly handling a dictionary assuming it's the structure we expect
        if isinstance(orders, dict):
            # Convert the single dictionary into a list of one dictionary
            orders = [orders]

        # Handle non-list inputs
        if not isinstance(orders, list):
            logger.warning(f"Expected list or dict but got {type(orders)}")
            return []

        transformed_orders = []

        for order in orders:
            # Make sure each item is indeed a dictionary
            if not isinstance(order, dict):
                logger.warning(
                    f"Warning: Expected a dict, but found a {type(order)}. Skipping this item."
                )
                continue

            # Map order types to standard format
            order_type = order.get("orderType", "").upper()
            if order_type == "MARKET":
                order["orderType"] = "MARKET"
            elif order_type == "LIMIT":
                order["orderType"] = "LIMIT"
            elif order_type == "STOP_LOSS":
                order["orderType"] = "SL"
            elif order_type == "STOP_LOSS_MARKET":
                order["orderType"] = "SL-M"
            elif order_type == "OCO":
                order["orderType"] = "OCO"

            transformed_order = {
                "symbol": order.get("tradingSymbol", ""),
                "exchange": order.get("exchangeSegment", ""),
                "action": order.get("transactionType", ""),
                "quantity": order.get("quantity", 0),
                "price": order.get("price", 0.0),
                "trigger_price": order.get("triggerPrice", 0.0),
                "pricetype": order.get("orderType", ""),
                "product": order.get("productType", ""),
                "orderid": order.get("orderId", ""),
                "order_status": order.get("orderStatus", ""),
                "timestamp": order.get("updateTime", ""),
            }

            transformed_orders.append(transformed_order)

        return transformed_orders
    except Exception as e:
        logger.error(f"Exception in transform_order_data: {e}")
        return []


def map_trade_data(trade_data):
    """
    Normalises a list of Delta Exchange fill/trade dicts to the OpenAlgo internal format.

    Delta Exchange fill fields (from GET /v2/fills or order history):
        id             – fill ID
        product_id     – contract ID
        product_symbol – contract symbol
        side           – "buy" | "sell"
        size           – contracts traded
        price          – execution price (string)
        order_id       – associated order ID
        created_at     – fill timestamp
    """
    try:
        # Check if 'data' is None
        if trade_data is None:
            logger.info("No trade data available.")
            return []

        # Check if trade_data is an error response (dict with status)
        if isinstance(trade_data, dict) and "status" in trade_data:
            if trade_data.get("status") in ["error", "failure"]:
                logger.error(f"Error in trade data: {trade_data.get('message', 'Unknown error')}")
                return []

        # Check if trade_data is a string (unexpected response)
        if isinstance(trade_data, str):
            logger.error(f"Received string response instead of trade data: {trade_data[:200]}...")
            return []

        # Ensure trade_data is a list
        if not isinstance(trade_data, list):
            logger.warning(f"Expected list but got {type(trade_data)}: {trade_data}")
            return []

        for trade in trade_data:
            if not isinstance(trade, dict):
                logger.warning(f"Skipping non-dictionary trade: {type(trade)}")
                continue

            product_id = trade.get("product_id", "")
            product_symbol = trade.get("product_symbol", "")
            order_id = trade.get("order_id", "")

            # Resolve symbol from DB; fall back to product_symbol
            symbol_from_db = get_symbol(str(product_id), "CRYPTO") if product_id else None
            trade["tradingSymbol"] = symbol_from_db or product_symbol

            trade["exchangeSegment"] = "CRYPTO"
            trade["productType"] = "NRML"

            # Composite order ID for reference
            trade["orderId"] = f"{product_id}:{order_id}" if product_id else str(order_id)

            trade["tradedQuantity"] = trade.get("size", 0)
            trade["tradedPrice"] = float(trade.get("price") or 0)
            trade["transactionType"] = trade.get("side", "").upper()
            trade["updateTime"] = trade.get("created_at", "")

            logger.debug(
                f"Mapped fill {trade.get('id', '')}: "
                f"symbol={trade['tradingSymbol']} side={trade['transactionType']}"
            )

        return trade_data

    except Exception as e:
        logger.error(f"Exception in map_trade_data: {e}")
        return []


def transform_tradebook_data(tradebook_data):
    """
    Transform Delta Exchange fill/trade data to OpenAlgo standard format.
    Expects list of dicts pre-normalised by map_trade_data().
    """
    try:
        # Handle None input
        if tradebook_data is None:
            return []

        # Handle non-list inputs
        if not isinstance(tradebook_data, list):
            logger.warning(f"Expected list but got {type(tradebook_data)}")
            return []

        transformed_data = []
        for trade in tradebook_data:
            # Ensure each trade is a dictionary
            if not isinstance(trade, dict):
                logger.warning(f"Skipping non-dictionary trade: {type(trade)}")
                continue

            try:
                quantity = float(trade.get("tradedQuantity", 0) or 0)
            except (TypeError, ValueError):
                quantity = 0.0

            try:
                price = float(trade.get("tradedPrice", 0.0) or 0.0)
            except (TypeError, ValueError):
                price = 0.0

            transformed_trade = {
                "symbol": trade.get("tradingSymbol", ""),
                "exchange": trade.get("exchangeSegment", ""),
                "product": trade.get("productType", ""),
                "action": trade.get("transactionType", ""),
                "quantity": quantity,
                "average_price": price,
                "trade_value": quantity * price,
                "orderid": trade.get("orderId", ""),
                "timestamp": trade.get("updateTime", ""),
            }
            transformed_data.append(transformed_trade)
        return transformed_data
    except Exception as e:
        logger.error(f"Exception in transform_tradebook_data: {e}")
        return []


def map_position_data(position_data):
    """
    Normalises a list of Delta Exchange position dicts to the OpenAlgo internal format.

    Delta Exchange /v2/positions/margined fields used:
        product_id       – contract ID (for symbol lookup)
        product_symbol   – contract symbol
        size             – net position size (positive = long, negative = short)
        entry_price      – average entry price (string)
        realized_pnl     – realised PnL since position opened (string)
        realized_funding – realised funding since position opened (string)
        margin           – current margin blocked (string)
    """
    try:
        # Check if position_data is None
        if position_data is None:
            logger.info("No position data available.")
            return []

        # Check if position_data is an error response (dict with status)
        if isinstance(position_data, dict) and "status" in position_data:
            if position_data.get("status") in ["error", "failure"]:
                logger.error(
                    f"Error in position data: {position_data.get('message', 'Unknown error')}"
                )
                return []

        # Check if position_data is a string (unexpected response)
        if isinstance(position_data, str):
            logger.error(
                f"Received string response instead of position data: {position_data[:200]}..."
            )
            return []

        if isinstance(position_data, list):
            all_positions = position_data
        else:
            logger.warning(f"Unexpected position data format: {type(position_data)}")
            return []

        processed_positions = []

        for position in all_positions:
            if not isinstance(position, dict):
                logger.warning(f"Skipping non-dictionary position: {type(position)}")
                continue

            product_id = position.get("product_id", "")
            product_symbol = position.get("product_symbol", "")
            is_spot = position.get("_is_spot", False)

            # Resolve symbol from DB; fall back to product_symbol.
            # For spot wallet entries, product_id is the asset_id (not a product token),
            # so look up by brsymbol (e.g. BTC_INR) instead.
            if is_spot:
                symbol_from_db = get_oa_symbol(product_symbol, "CRYPTO")
            else:
                symbol_from_db = get_symbol(str(product_id), "CRYPTO") if product_id else None
            position["tradingSymbol"] = symbol_from_db or product_symbol

            position["exchangeSegment"] = "CRYPTO"
            position["productType"] = "CNC" if is_spot else "NRML"

            # Net quantity: positive = long, negative = short
            # Use float() to support fractional spot sizes (e.g. 0.0001 BTC)
            try:
                net_qty = float(position.get("size", 0))
            except (ValueError, TypeError):
                net_qty = 0
            position["netQty"] = net_qty

            # Average entry price
            position["avgCostPrice"] = float(position.get("entry_price") or 0)

            # LTP is not returned by positions/margined; will be enriched by quotes step
            position["lastTradedPrice"] = 0.0
            position["marketValue"] = 0.0

            # Total PnL = realised + unrealised (both returned by /v2/positions/margined)
            realised = float(position.get("realized_pnl") or 0)
            unrealised = float(position.get("unrealized_pnl") or 0)
            position["pnlAbsolute"] = realised + unrealised

            # Contract value: look up from master contract cache using the resolved canonical symbol.
            # Delta Exchange v2 API removed nested product payloads from positions responses,
            # so we read contract_value (e.g. 0.01 ETH for ETHUSD.P) from the in-memory symbol cache.
            # This is forwarded to the frontend so the live P&L recalculation in useLivePrice.ts
            # scales correctly.
            lot_size = 1.0
            if symbol_from_db:
                sym_info = get_symbol_info(symbol_from_db, "CRYPTO")
                if sym_info and sym_info.contract_value is not None:
                    lot_size = float(sym_info.contract_value)
            position["lot_size"] = lot_size

            position["multiplier"] = 1
            position["positionType"] = "open" if net_qty != 0 else "closed"

            logger.debug(
                f"Mapped position: {position['tradingSymbol']} size={net_qty} "
                f"entry={position['avgCostPrice']} realised={realised} unrealised={unrealised} total_pnl={realised + unrealised}"
            )

            processed_positions.append(position)

        return processed_positions

    except Exception as e:
        logger.error(f"Exception in map_position_data: {e}")
        return []


def transform_positions_data(positions_data):
    """
    Transform positions data to OpenAlgo standard format.
    Matches the structure used by Angel broker for consistency.

    OpenAlgo Standard Fields:
    - symbol: Trading symbol
    - exchange: Exchange name
    - product: Product type (MIS/CNC/NRML)
    - quantity: Net quantity
    - average_price: Average cost price (float)
    - ltp: Last traded price (float)
    - pnl: Profit and loss (float)
    """
    try:
        # Handle None input
        if positions_data is None:
            return []

        # Handle non-list inputs
        if not isinstance(positions_data, list):
            logger.warning(f"Expected list but got {type(positions_data)}")
            return []

        transformed_data = []
        for position in positions_data:
            # Ensure each position is a dictionary
            if not isinstance(position, dict):
                logger.warning(f"Skipping non-dictionary position: {type(position)}")
                continue

            # OpenAlgo standard format (matching Angel broker structure)
            transformed_position = {
                "symbol": position.get("tradingSymbol", ""),
                "exchange": position.get("exchangeSegment", ""),
                "product": position.get("productType", ""),
                "quantity": position.get("netQty", 0),
                "average_price": float(
                    position.get("avgCostPrice", 0.0)
                ),  # Float as per OpenAlgo standard
                "ltp": float(position.get("lastTradedPrice", 0.0)),  # Last traded price
                "pnl": float(position.get("pnlAbsolute", 0.0)),  # Profit and loss
                "lot_size": float(position.get("lot_size", 1.0)),  # Contract size (e.g. 0.01 ETH for ETHUSD.P)
            }
            transformed_data.append(transformed_position)
        return transformed_data
    except Exception as e:
        logger.error(f"Exception in transform_positions_data: {e}")
        return []


def transform_holdings_data(holdings_data):
    try:
        # Handle None input
        if holdings_data is None:
            return []

        # Handle non-list inputs
        if not isinstance(holdings_data, list):
            logger.warning(f"Expected list but got {type(holdings_data)}")
            return []

        transformed_data = []
        for holding in holdings_data:
            # Ensure each holding is a dictionary
            if not isinstance(holding, dict):
                logger.warning(f"Skipping non-dictionary holding: {type(holding)}")
                continue

            transformed_holding = {
                "symbol": holding.get("tradingSymbol", holding.get("symbol", "")),
                "exchange": holding.get("exchangeSegment", "NSE"),  # Default to NSE
                "quantity": holding.get("totalQty", holding.get("total_qty", 0)),
                "product": "CNC",  # Holdings are always CNC (Cash and Carry)
                "pnl": holding.get("pnlAbsolute", 0.0),
                "pnlpercent": holding.get("pnlPercent", 0.0),
            }
            transformed_data.append(transformed_holding)
        return transformed_data
    except Exception as e:
        logger.error(f"Exception in transform_holdings_data: {e}")
        return []


def map_portfolio_data(portfolio_data):
    """
    Processes and modifies a list of Portfolio dictionaries based on specific conditions.

    Parameters:
    - portfolio_data: A list of dictionaries, where each dictionary represents portfolio information.

    Returns:
    - The modified portfolio_data with updated fields.
    """
    try:
        # Check if 'portfolio_data' is None
        if portfolio_data is None:
            logger.info("No portfolio data available.")
            return []

        # Check if portfolio_data is an error response (dict with status)
        if isinstance(portfolio_data, dict) and "status" in portfolio_data:
            if portfolio_data.get("status") in ["error", "failure"]:
                logger.error(
                    f"Error in portfolio data: {portfolio_data.get('message', 'Unknown error')}"
                )
                return []

        # Check if portfolio_data is a string (unexpected response)
        if isinstance(portfolio_data, str):
            logger.error(
                f"Received string response instead of portfolio data: {portfolio_data[:200]}..."
            )
            return []

        # Ensure portfolio_data is a list
        if not isinstance(portfolio_data, list):
            logger.warning(f"Expected list but got {type(portfolio_data)}: {portfolio_data}")
            return []

        if portfolio_data:
            for holding in portfolio_data:
                # Ensure each holding is a dictionary
                if not isinstance(holding, dict):
                    logger.warning(f"Skipping non-dictionary holding: {type(holding)}")
                    continue

                # Delta Exchange has no equity holdings; this branch is a no-op.
                # Fields are set to safe defaults so upstream transforms don't break.
                holding.setdefault("tradingSymbol", "")
                holding.setdefault("exchangeSegment", "CRYPTO")
                holding.setdefault("totalQty", 0)
                holding.setdefault("avgCostPrice", 0.0)
                holding.setdefault("lastTradedPrice", 0.0)
                holding.setdefault("marketValue", 0.0)
                holding.setdefault("pnlAbsolute", 0.0)
                holding.setdefault("pnlPercent", 0.0)

        return portfolio_data

    except Exception as e:
        logger.error(f"Exception in map_portfolio_data: {e}")
        return []


def calculate_portfolio_statistics(holdings_data):
    try:
        # Handle None or empty input
        if not holdings_data or not isinstance(holdings_data, list):
            return {
                "totalholdingvalue": 0.0,
                "totalinvvalue": 0.0,
                "totalprofitandloss": 0.0,
                "totalpnlpercentage": 0.0,
            }

        totalholdingvalue = 0.0
        totalinvvalue = 0.0
        totalprofitandloss = 0.0

        for holding in holdings_data:
            # Ensure each holding is a dictionary
            if not isinstance(holding, dict):
                continue

            # Delta Exchange has no equity holdings; calculate from normalised fields.
            total_qty = holding.get("totalQty", 0)
            avg_price = holding.get("avgCostPrice", 0.0)
            market_price = holding.get("lastTradedPrice", avg_price)

            # Calculate values
            investment_value = total_qty * avg_price
            market_value = total_qty * market_price
            pnl = market_value - investment_value

            # Add to totals
            totalholdingvalue += market_value
            totalinvvalue += investment_value
            totalprofitandloss += pnl

        # Calculate percentage - avoid division by zero
        totalpnlpercentage = (
            (totalprofitandloss / totalinvvalue * 100) if totalinvvalue > 0 else 0.0
        )

        return {
            "totalholdingvalue": round(totalholdingvalue, 2),
            "totalinvvalue": round(totalinvvalue, 2),
            "totalprofitandloss": round(totalprofitandloss, 2),
            "totalpnlpercentage": round(totalpnlpercentage, 2),
        }
    except Exception as e:
        logger.error(f"Exception in calculate_portfolio_statistics: {e}")
        return {
            "totalholdingvalue": 0.0,
            "totalinvvalue": 0.0,
            "totalprofitandloss": 0.0,
            "totalpnlpercentage": 0.0,
        }

```


---

# FILE: broker\deltaexchange\mapping\transform_data.py

```py
﻿# Mapping OpenAlgo API Request to Delta Exchange API Parameters
# Delta Exchange API docs: https://docs.delta.exchange

from database.token_db import get_br_symbol, get_symbol_info, get_token
from utils.logging import get_logger

logger = get_logger(__name__)


def _order_size(quantity, symbol, exchange):
    """
    Convert quantity to the correct type for the Delta Exchange size parameter.
    - Spot instruments: fractional float (e.g. 0.05 SOL)
    - Derivatives (futures/options/perps): integer number of contracts

    Raises ValueError if a fractional quantity is passed for a non-spot instrument.
    """
    qty = float(quantity)
    info = get_symbol_info(symbol, exchange)
    if info and info.instrumenttype == "SPOT":
        return qty
    if qty != int(qty):
        raise ValueError(
            f"Fractional quantity ({qty}) not allowed for derivative contracts. "
            f"Use whole numbers for {symbol}."
        )
    return int(qty)


def transform_data(data, token):
    """
    Transforms the OpenAlgo API request structure to Delta Exchange POST /v2/orders payload.

    Delta Exchange order parameters:
        product_id           (int)  - Contract identifier (= token from master contract DB)
        product_symbol       (str)  - Contract symbol e.g. "BTCUSD"
        size                 (int)  - Number of contracts
        side                 (str)  - "buy" or "sell"
        order_type           (str)  - "limit_order" or "market_order"
        limit_price          (str)  - Required for limit orders (string for full precision)
        time_in_force        (str)  - "gtc" (default) or "ioc"
        stop_order_type      (str)  - "stop_loss_order" (for SL/SL-M orders)
        stop_price           (str)  - Required for stop orders
        stop_trigger_method  (str)  - "last_traded_price" | "mark_price" | "index_price"
                                      (default: "last_traded_price" for stop orders)
        trail_amount         (str)  - Trailing offset for trailing stop orders
        post_only            (bool) - True = maker-only; rejected if would take liquidity
        reduce_only          (bool) - True if order must only reduce an existing position
        client_order_id      (str)  - Optional caller-supplied order reference
        bracket_stop_loss_price           (str) - Bracket stop-loss trigger price
        bracket_stop_loss_limit_price     (str) - Bracket stop-loss limit price
        bracket_trail_amount              (str) - Bracket trailing stop offset
        bracket_stop_trigger_method       (str) - Trigger method for bracket stop
        bracket_take_profit_price         (str) - Bracket take-profit trigger price
        bracket_take_profit_limit_price   (str) - Bracket take-profit limit price
    """
    symbol = get_br_symbol(data["symbol"], data["exchange"]) or data["symbol"]
    order_type = map_order_type(data["pricetype"])
    side = data["action"].lower()  # "buy" or "sell"

    size = _order_size(data["quantity"], data["symbol"], data["exchange"])

    transformed = {
        "product_id": int(token),
        "product_symbol": symbol,
        "size": size,
        "side": side,
        "order_type": order_type,
        "time_in_force": "gtc",
    }

    # Add limit_price for limit orders
    if order_type == "limit_order":
        price = data.get("price", "0")
        transformed["limit_price"] = str(price) if price else "0"

    # Handle stop-loss orders
    if data["pricetype"] in ("SL", "SL-M"):
        transformed["stop_order_type"] = "stop_loss_order"
        trigger = data.get("trigger_price", "0")
        transformed["stop_price"] = str(trigger) if trigger else "0"
        # Default trigger method; caller can override via data["stop_trigger_method"]
        transformed["stop_trigger_method"] = data.get(
            "stop_trigger_method", "last_traded_price"
        )
        # Trailing stop: forward trail_amount if provided
        if data.get("trail_amount"):
            transformed["trail_amount"] = str(data["trail_amount"])

    # Handle IOC validity
    if data.get("validity") == "IOC":
        transformed["time_in_force"] = "ioc"

    # Post-only (maker-only limit orders)
    if data.get("post_only") is True:
        transformed["post_only"] = True

    # Reduce-only: forward if explicitly provided
    if data.get("reduce_only") is True:
        transformed["reduce_only"] = True

    # Client order ID (strategy/signal reference)
    if data.get("client_order_id"):
        transformed["client_order_id"] = str(data["client_order_id"])

    # Bracket order fields — forward any that are present
    bracket_fields = (
        "bracket_stop_loss_price",
        "bracket_stop_loss_limit_price",
        "bracket_trail_amount",
        "bracket_stop_trigger_method",
        "bracket_take_profit_price",
        "bracket_take_profit_limit_price",
    )
    for field in bracket_fields:
        if data.get(field):
            transformed[field] = str(data[field])

    logger.debug(f"[DeltaExchange] Transformed order: {transformed}")
    return transformed


def transform_modify_order_data(data):
    """
    Transforms OpenAlgo modify order data to Delta Exchange PUT /v2/orders payload.

    Delta Exchange modify fields:
        id           (int) - Order ID (extracted from composite "{product_id}:{order_id}")
        product_id   (int) - Contract ID
        size         (int) - New order size
        limit_price  (str) - New limit price (use "0" for market/stop-market orders)
        stop_price   (str) - Stop trigger price (for SL / SL-M orders only)

    OpenAlgo pricetype mapping:
        MARKET / LIMIT  → no stop_price
        SL              → limit_price = price, stop_price = trigger_price
        SL-M            → limit_price = "0",  stop_price = trigger_price
    """
    orderid = data["orderid"]
    # Composite ID format: "{product_id}:{order_id}"
    if ":" in str(orderid):
        product_id_str, order_id_str = str(orderid).split(":", 1)
        product_id = int(product_id_str)
        order_id = int(order_id_str)
    else:
        order_id = int(orderid)
        product_id = int(get_token(data["symbol"], data["exchange"]) or 0)

    pricetype = str(data.get("pricetype", "")).upper()
    is_stop_order = pricetype in ("SL", "SL-M")

    # For stop-market (SL-M) orders the limit_price is irrelevant — use "0".
    # For stop-limit (SL) orders the limit_price is the limit leg.
    if pricetype == "SL-M":
        limit_price = "0"
    else:
        limit_price = str(data.get("price", "0"))

    size = _order_size(data["quantity"], data["symbol"], data["exchange"])

    transformed = {
        "id": order_id,
        "product_id": product_id,
        "size": size,
        "limit_price": limit_price,
    }

    # Include stop_price only for SL / SL-M orders; omit entirely for regular orders
    # so Delta does not interpret the field unexpectedly.
    if is_stop_order:
        trigger_price = data.get("trigger_price", "0")
        transformed["stop_price"] = str(trigger_price) if trigger_price else "0"

    return transformed


def map_order_type(pricetype):
    """Maps OpenAlgo pricetype to Delta Exchange order_type string."""
    mapping = {
        "MARKET": "market_order",
        "LIMIT": "limit_order",
        "SL": "limit_order",
        "SL-M": "market_order",
    }
    return mapping.get(pricetype, "market_order")


def map_product_type(product):
    """
    Delta Exchange does not use equity-style product types (CNC/NRML/MIS).
    Returns the value as-is for interface compatibility.
    """
    return product


def reverse_map_product_type(br_product):
    """
    Maps Delta Exchange position category back to OpenAlgo product type.
    All crypto futures/options map to NRML.
    """
    return "NRML"


def map_exchange(br_exchange):
    """
    Maps a Delta Exchange broker exchange field back to OpenAlgo exchange code.
    Delta Exchange is a single crypto derivatives exchange.
    """
    return "CRYPTO"


def map_exchange_type(exchange):
    """
    Maps an OpenAlgo exchange code to the Delta Exchange context.
    All contracts on Delta Exchange are under a single platform.
    """
    return "CRYPTO"

```
