# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\pocketful\mapping



---

# FILE: broker\pocketful\mapping\margin_data.py

```py
# Mapping OpenAlgo API Request https://openalgo.in/docs
# Pocketful does not provide Margin Calculator API

from utils.logging import get_logger

logger = get_logger(__name__)


def transform_margin_positions(positions):
    """
    Transform OpenAlgo margin position format to broker format.

    Note: Pocketful does not provide a margin calculator API.

    Args:
        positions: List of positions in OpenAlgo format

    Raises:
        NotImplementedError: Pocketful does not support margin calculator API
    """
    raise NotImplementedError("Pocketful does not support margin calculator API")


def parse_margin_response(response_data):
    """
    Parse broker margin calculator response to OpenAlgo standard format.

    Note: Pocketful does not provide a margin calculator API.

    Args:
        response_data: Raw response from broker margin calculator API

    Raises:
        NotImplementedError: Pocketful does not support margin calculator API
    """
    raise NotImplementedError("Pocketful does not support margin calculator API")

```


---

# FILE: broker\pocketful\mapping\order_data.py

```py
import json

from database.token_db import get_oa_symbol, get_symbol
from utils.logging import get_logger

logger = get_logger(__name__)


def map_order_data(order_data):
    """
    Processes and modifies a list of order dictionaries based on specific conditions.
    Handles different field names in Pocketful API response.

    Parameters:
    - order_data: A list of dictionaries, where each dictionary represents an order.

    Returns:
    - The modified order_data with updated 'tradingsymbol' and 'product' fields.
    """
    # Check if we have any data
    if not order_data or "data" not in order_data:
        logger.info("No data available or invalid format.")
        return {}

    # Handle Pocketful's response format which might have nested orders
    if isinstance(order_data["data"], dict) and "orders" in order_data["data"]:
        orders = order_data["data"]["orders"]
    else:
        orders = order_data["data"]

    if not orders:
        logger.info("No orders found in data.")
        return orders

    # Process each order
    for order in orders:
        # Safely extract exchange
        if "exchange" in order:
            exchange = order["exchange"]
        else:
            logger.warning(f"Warning: Order missing 'exchange' field: {order}")
            continue

        # Safely extract symbol (handle both possible field names)
        symbol = None
        if "trading_symbol" in order:
            symbol = order["trading_symbol"]
            # Add 'tradingsymbol' field for consistency with rest of the system
            order["tradingsymbol"] = symbol
        elif "tradingsymbol" in order:
            symbol = order["tradingsymbol"]
        else:
            logger.warning(
                f"Warning: Order missing symbol fields (tried 'trading_symbol' and 'tradingsymbol'): {order}"
            )
            continue

        # Check if symbol was found; if so, update with OpenAlgo format
        if symbol:
            # Convert to OpenAlgo symbol format
            oa_symbol = get_oa_symbol(symbol, exchange)
            order["tradingsymbol"] = oa_symbol
            # Also update trading_symbol if it exists to maintain consistency
            if "trading_symbol" in order:
                order["trading_symbol"] = oa_symbol
        else:
            logger.info(f"Symbol is empty for exchange {exchange}. Keeping original symbol.")

    # Return processed orders
    return orders


def calculate_order_statistics(order_data):
    """
    Calculates statistics from order data, including totals for buy orders, sell orders,
    completed orders, open orders, and rejected orders.
    Handles different field names in Pocketful API response.

    Parameters:
    - order_data: A list of dictionaries, where each dictionary represents an order.

    Returns:
    - A dictionary containing counts of different types of orders.
    """
    # Initialize counters
    total_buy_orders = total_sell_orders = 0
    total_completed_orders = total_open_orders = total_rejected_orders = total_cancelled_orders = 0

    if order_data:
        for order in order_data:
            # Get transaction type - check different possible field names
            transaction_type = None
            if "transaction_type" in order:
                transaction_type = order["transaction_type"]
            elif "order_side" in order:
                transaction_type = order["order_side"]

            # Count buy and sell orders
            if transaction_type:
                if transaction_type.upper() == "BUY":
                    total_buy_orders += 1
                elif transaction_type.upper() == "SELL":
                    total_sell_orders += 1

            # Get status and mode for classification
            status = None
            if "status" in order:
                status = order["status"].upper() if order["status"] else ""
            elif "order_status" in order:
                status = order["order_status"].upper() if order["order_status"] else ""

            mode = order.get("mode", "").upper()

            # Flag to track if order has been counted
            counted = False

            # Classify order based on status
            if status:
                if "CANCEL_CONFIRMED" in status:  # Check for cancelled status first
                    total_cancelled_orders += 1
                    counted = True
                elif "COMPLETE" in status:
                    total_completed_orders += 1
                    counted = True
                elif "REJECTED" in status:
                    total_rejected_orders += 1
                    counted = True

            # Count as open if either status or mode indicates it's open and hasn't been counted yet
            if not counted and (
                "OPEN" in (status or "")
                or "NEW" in (status or "")
                or "PENDING" in (status or "")
                or "SUBMIT" in (status or "")
                or "MODIFY" in (status or "")
                or mode == "NEW"
            ):
                total_open_orders += 1

    # Compile and return the statistics
    return {
        "total_buy_orders": total_buy_orders,
        "total_sell_orders": total_sell_orders,
        "total_completed_orders": total_completed_orders,
        "total_open_orders": total_open_orders,
        "total_rejected_orders": total_rejected_orders,
        "total_cancelled_orders": total_cancelled_orders,
    }


def transform_order_data(orders):
    """
    Transform order data from Pocketful API format to OpenAlgo standard format.
    Handles both completed and pending orders from the combined order book.

    Args:
        orders: Order data from Pocketful API. Can be a single order dict, a list of orders,
               or a response dict containing orders in data field.

    Returns:
        List of transformed orders in standard format
    """
    # Extract orders from data if it's a response object
    if isinstance(orders, dict) and "data" in orders:
        # Handle both possible formats from our API functions
        if isinstance(orders["data"], list):
            orders = orders["data"]
        elif isinstance(orders["data"], dict) and "orders" in orders["data"]:
            orders = orders["data"]["orders"]
        else:
            logger.warning("Warning: Unexpected data structure. Expected orders in data field.")
            orders = []

    # If we have a single order dict, convert it to a list
    if isinstance(orders, dict):
        orders = [orders]

    # Initialize result list
    transformed_orders = []

    for order in orders:
        # Skip non-dict items
        if not isinstance(order, dict):
            logger.warning(
                f"Warning: Expected a dict, but found a {type(order)}. Skipping this item."
            )
            continue

        # Map order status
        order_status = "unknown"
        status = order.get("order_status", "").upper()
        mode = order.get("mode", "").upper()

        # Handle different status mappings
        if "CANCEL_CONFIRMED" in status:
            order_status = "cancelled"
        elif "COMPLETE" in status:
            order_status = "complete"
        elif "REJECTED" in status:
            order_status = "rejected"
        elif "TRIGGER PENDING" in status:
            order_status = "trigger pending"
        elif (
            "OPEN" in status
            or "PENDING" in status
            or "AMO_SUBMIT" in status
            or "MODIFY" in status
            or mode == "NEW"
        ):
            order_status = "open"
        elif "CANCEL" in status:
            order_status = "cancelled"

        # Get symbol from trading_symbol or tradingsymbol (handling different formats)
        symbol = order.get("trading_symbol", order.get("tradingsymbol", ""))

        # Get transaction type from order_side or transaction_type
        action = order.get("order_side", order.get("transaction_type", ""))
        if action.upper() == "BUY":
            action = "BUY"
        elif action.upper() == "SELL":
            action = "SELL"

        # Get order type
        price_type = order.get("order_type", "")

        # Create transformed order
        transformed_order = {
            "symbol": symbol,
            "exchange": order.get("exchange", ""),
            "action": action,
            "quantity": order.get("quantity", 0),
            "price": order.get("price", 0.0),
            "trigger_price": order.get("trigger_price", 0.0),
            "pricetype": price_type,
            "product": order.get("product", ""),
            "orderid": order.get("oms_order_id", order.get("order_id", "")),
            "order_status": order_status,
            "timestamp": order.get("order_entry_time", order.get("order_timestamp", "")),
            "filled_quantity": order.get("filled_quantity", 0),
            "pending_quantity": order.get("remaining_quantity", 0),
            "average_price": order.get("average_price", 0.0)
            or order.get("average_trade_price", 0.0),
        }

        transformed_orders.append(transformed_order)

    return transformed_orders


def map_trade_data(trade_data):
    """
    Process Pocketful's trade data to map any broker-specific fields.

    Args:
        trade_data: Trade data response from Pocketful API

    Returns:
        Processed trade data with standardized fields
    """
    # Check if we have any data - now handling direct trades array
    if not trade_data:
        logger.info("No trade data available.")
        return []

    # Handle different possible structures:
    trades = []

    # Case 1: data is already the trades array (when coming from get_trade_book)
    if (
        isinstance(trade_data, dict)
        and "data" in trade_data
        and isinstance(trade_data["data"], list)
    ):
        trades = trade_data["data"]
    # Case 2: nested structure (when directly handling API response)
    elif (
        isinstance(trade_data, dict)
        and "data" in trade_data
        and isinstance(trade_data["data"], dict)
        and "trades" in trade_data["data"]
    ):
        trades = trade_data["data"]["trades"]
    # Case 3: direct array of trades
    elif isinstance(trade_data, list):
        trades = trade_data
    else:
        logger.info(f"Unexpected trade data format: {type(trade_data)}")
        return []

    if not trades:
        logger.info("No trades found in data.")
        return []

    logger.info(f"Processing {len(trades)} trades")

    # Process each trade
    processed_trades = []
    for trade in trades:
        # Create a copy to avoid modifying the original data
        processed_trade = dict(trade)

        # Safely extract exchange
        exchange = processed_trade.get("exchange", "")

        # Safely extract symbol
        symbol = processed_trade.get("trading_symbol", "")
        if symbol:
            # Add 'tradingsymbol' field for consistency with rest of the system
            processed_trade["tradingsymbol"] = symbol

            # Convert to OpenAlgo symbol format if exchange is available
            if exchange:
                oa_symbol = get_oa_symbol(symbol, exchange)
                processed_trade["tradingsymbol"] = oa_symbol

        # Map transaction_type/order_side to a standard format
        if "order_side" in processed_trade and not processed_trade.get("transaction_type"):
            processed_trade["transaction_type"] = processed_trade["order_side"]

        # Map trade-specific fields to standard names expected by transform function
        if "trade_quantity" in processed_trade and not processed_trade.get("fill_quantity"):
            processed_trade["fill_quantity"] = processed_trade["trade_quantity"]

        if "trade_price" in processed_trade and not processed_trade.get("avg_price"):
            processed_trade["avg_price"] = processed_trade["trade_price"]

        if "trade_time" in processed_trade and not processed_trade.get("fill_timestamp"):
            processed_trade["fill_timestamp"] = processed_trade["trade_time"]

        if "oms_order_id" in processed_trade and not processed_trade.get("order_id"):
            processed_trade["order_id"] = processed_trade["oms_order_id"]

        if "trade_number" in processed_trade and not processed_trade.get("trade_id"):
            processed_trade["trade_id"] = processed_trade["trade_number"]

        processed_trades.append(processed_trade)

    # Return processed trades
    return processed_trades


def transform_tradebook_data(tradebook_data):
    """
    Transform tradebook data from Pocketful API format to OpenAlgo standard format.

    Args:
        tradebook_data: Response from Pocketful's trade book API

    Returns:
        List of transformed trades in standard format
    """
    # First map the trade data to standardize fields
    trades = map_trade_data(tradebook_data)

    transformed_data = []
    for trade in trades:
        # Map fields from Pocketful's format to our standard format
        transformed_trade = {
            "symbol": trade.get("tradingsymbol", ""),
            "exchange": trade.get("exchange", ""),
            "product": trade.get("product", ""),  # Pocketful uses 'product' as is
            "action": trade.get("transaction_type", "").upper(),  # BUY/SELL
            "quantity": int(trade.get("fill_quantity", 0)),  # Executed quantity
            "average_price": float(trade.get("avg_price", 0.0)),  # Trade price
            "trade_id": trade.get("trade_id", ""),  # Unique trade identifier
            "orderid": trade.get("order_id", ""),  # Parent order identifier
            "timestamp": trade.get("fill_timestamp", ""),  # Trade execution time
            "trade_value": 0.0,  # Will calculate below
        }

        # Calculate trade value
        if transformed_trade["quantity"] > 0 and transformed_trade["average_price"] > 0:
            transformed_trade["trade_value"] = (
                transformed_trade["quantity"] * transformed_trade["average_price"]
            )

        transformed_data.append(transformed_trade)

    return transformed_data


def map_position_data(position_data):
    """
    Processes and modifies a list of position dictionaries based on specific conditions.
    Handles Pocketful's position API response format.

    Parameters:
    - position_data: Response from Pocketful's position API

    Returns:
    - The modified position data with updated 'tradingsymbol' field
    """
    # Check if we have any data - now handling direct positions array
    if not position_data:
        logger.info("No position data available.")
        return []

    # Handle different possible structures:
    positions = []
    logger.debug(f"DEBUG - Position data type: {type(position_data)}")

    # Case 1: data is already the positions array (when coming from get_positions)
    if (
        isinstance(position_data, dict)
        and "data" in position_data
        and isinstance(position_data["data"], list)
    ):
        logger.info(
            f"DEBUG - Using Case 1: data is a list with {len(position_data['data'])} positions"
        )
        positions = position_data["data"]
    # Case 2: nested structure (when directly handling API response)
    elif (
        isinstance(position_data, dict)
        and "data" in position_data
        and isinstance(position_data["data"], dict)
        and "positions" in position_data["data"]
    ):
        logger.debug("DEBUG - Using Case 2: data.positions structure")
        positions = position_data["data"]["positions"]
    # Case 3: direct array of positions
    elif isinstance(position_data, list):
        logger.debug(f"DEBUG - Using Case 3: direct array with {len(position_data)} positions")
        positions = position_data
    # Case 4: Legacy structure with 'net' key
    elif (
        isinstance(position_data, dict)
        and "data" in position_data
        and isinstance(position_data["data"], dict)
        and "net" in position_data["data"]
    ):
        logger.debug("DEBUG - Using Case 4: data.net structure")
        positions = position_data["data"]["net"] if position_data["data"]["net"] is not None else []
    else:
        logger.debug(f"DEBUG - Unexpected position data format: {type(position_data)}")
        # For debugging, try to print more details about the structure
        if isinstance(position_data, dict):
            logger.debug(f"DEBUG - Dict keys: {position_data.keys()}")
            if "data" in position_data:
                logger.info(f"DEBUG - Data type: {type(position_data['data'])}")
                if isinstance(position_data["data"], dict):
                    logger.info(f"DEBUG - Data dict keys: {position_data['data'].keys()}")
        return []

    if not positions:
        logger.info("No positions found in data.")
        return []

    logger.info(f"Processing {len(positions)} positions")

    # Process each position
    processed_positions = []
    for position in positions:
        # Create a copy to avoid modifying the original data
        processed_position = dict(position)

        # Safely extract exchange
        exchange = processed_position.get("exchange", "")

        # Safely extract symbol (handle both trading_symbol and tradingsymbol fields)
        symbol = processed_position.get(
            "trading_symbol", processed_position.get("tradingsymbol", "")
        )
        if symbol:
            # Add 'tradingsymbol' field for consistency with rest of the system
            processed_position["tradingsymbol"] = symbol

            # Convert to OpenAlgo symbol format if exchange is available
            if exchange:
                oa_symbol = get_oa_symbol(symbol, exchange)
                if oa_symbol:
                    processed_position["tradingsymbol"] = oa_symbol
                else:
                    logger.info(
                        f"Symbol {symbol} not found in database for exchange {exchange}. Keeping original symbol."
                    )

        # Map Pocketful-specific fields to standard format

        # Ensure quantity field exists - prioritize net_quantity since that's what we need
        if "net_quantity" in processed_position:
            processed_position["quantity"] = processed_position["net_quantity"]

        # Handle average price
        if (
            "average_buy_price" in processed_position
            and float(processed_position.get("average_buy_price", 0)) > 0
        ):
            processed_position["average_price"] = processed_position["average_buy_price"]
        elif (
            "average_sell_price" in processed_position
            and float(processed_position.get("average_sell_price", 0)) > 0
        ):
            processed_position["average_price"] = processed_position["average_sell_price"]

        # Handle last price
        if "ltp" in processed_position:
            processed_position["last_price"] = processed_position["ltp"]

        # Handle buy/sell quantity
        if "buy_quantity" in processed_position:
            processed_position["buy_quantity"] = processed_position["buy_quantity"]
        if "sell_quantity" in processed_position:
            processed_position["sell_quantity"] = processed_position["sell_quantity"]

        # Handle pnl calculation
        if (
            "ltp" in processed_position
            and "net_quantity" in processed_position
            and "average_buy_price" in processed_position
            and processed_position.get("net_quantity", 0) > 0
        ):
            # Calculate PnL for long positions
            qty = float(processed_position["net_quantity"])
            avg = float(processed_position["average_buy_price"])
            ltp = float(processed_position["ltp"])
            processed_position["pnl"] = (ltp - avg) * qty
        elif (
            "ltp" in processed_position
            and "net_quantity" in processed_position
            and "average_sell_price" in processed_position
            and processed_position.get("net_quantity", 0) < 0
        ):
            # Calculate PnL for short positions
            qty = abs(float(processed_position["net_quantity"]))
            avg = float(processed_position["average_sell_price"])
            ltp = float(processed_position["ltp"])
            processed_position["pnl"] = (avg - ltp) * qty

        processed_positions.append(processed_position)

    # Return processed positions
    return processed_positions


def transform_positions_data(positions_data):
    transformed_data = []

    for position in positions_data:
        # Ensure average_price is treated as a float, then format to a string with 2 decimal places
        average_price_formatted = "{:.2f}".format(float(position.get("average_price", 0.0)))

        transformed_position = {
            "symbol": position.get("tradingsymbol", ""),
            "exchange": position.get("exchange", ""),
            "product": position.get("product", ""),
            "quantity": position.get("quantity", "0"),
            "average_price": average_price_formatted,
        }
        transformed_data.append(transformed_position)
    return transformed_data


def transform_holdings_data(holdings_data):
    """
    Transform holdings data from Pocketful API format to OpenAlgo standard format.
    Handles responses from both /api/v1/holdings and /api/v1/portfolio/demat-holdings endpoints.
    Can be called twice in the pipeline, so it detects if data is already transformed.

    Args:
        holdings_data: Response from Pocketful's holdings API or previously transformed data

    Returns:
        List of transformed holdings in standard format
    """
    if not holdings_data:
        logger.info("No holdings data available")
        return []

    logger.debug(f"DEBUG - Transforming {len(holdings_data)} holdings entries")
    if holdings_data and len(holdings_data) > 0:
        logger.debug(f"DEBUG - Sample holding data: {holdings_data[0]}")

    # Check if this data has already been transformed (called twice in the pipeline)
    # If the first item has 'symbol' and 'product' fields, it's likely already been transformed
    is_already_transformed = False
    if holdings_data and isinstance(holdings_data, list) and len(holdings_data) > 0:
        first_item = holdings_data[0]
        if isinstance(first_item, dict) and "symbol" in first_item and "product" in first_item:
            logger.debug(
                "DEBUG - Data appears to be already transformed, preserving existing transformation"
            )
            is_already_transformed = True
            # Keep existing transformed data if it has valid symbols
            if first_item.get("symbol"):
                return holdings_data

    transformed_data = []
    for holding in holdings_data:
        # Extract tradingsymbol and exchange with fallbacks for different field names
        tradingsymbol = None

        # Check all possible field names for trading symbol
        for field in ["tradingsymbol", "trading_symbol", "symbol"]:
            if field in holding and holding[field]:
                tradingsymbol = holding[field]
                logger.info(f"DEBUG - Found symbol in '{field}' field: {tradingsymbol}")
                break

        # If still not found, check in instrument_details if available
        if (
            not tradingsymbol
            and "instrument_details" in holding
            and isinstance(holding["instrument_details"], dict)
        ):
            if "trading_symbol" in holding["instrument_details"]:
                tradingsymbol = holding["instrument_details"]["trading_symbol"]
                logger.debug(
                    f"DEBUG - Found symbol in instrument_details.trading_symbol: {tradingsymbol}"
                )
            elif "symbol" in holding["instrument_details"]:
                tradingsymbol = holding["instrument_details"]["symbol"]
                logger.debug(f"DEBUG - Found symbol in instrument_details.symbol: {tradingsymbol}")

        # Last fallback - check the 'symbol' field directly
        if not tradingsymbol and "symbol" in holding:
            tradingsymbol = holding["symbol"]
            logger.info(f"DEBUG - Using 'symbol' field directly: {tradingsymbol}")

        if not tradingsymbol:
            logger.warning(f"WARNING: Could not find trading symbol in holding: {holding}")
            continue

        # Get exchange with fallbacks
        exchange = holding.get("exchange", "NSE")  # Default to NSE if not specified

        # Convert to OpenAlgo symbol format if needed
        if tradingsymbol and exchange:
            # Clean up the symbol if it has -EQ suffix
            if tradingsymbol.endswith("-EQ"):
                tradingsymbol = tradingsymbol.replace("-EQ", "")
                logger.debug(f"DEBUG - Removed -EQ suffix, symbol is now: {tradingsymbol}")

            # Try to convert to OpenAlgo symbol format
            try:
                logger.info(
                    f"DEBUG - Converting symbol '{tradingsymbol}' for exchange '{exchange}' to OpenAlgo format"
                )
                oa_symbol = get_oa_symbol(tradingsymbol, exchange)
                if oa_symbol:
                    tradingsymbol = oa_symbol
                    logger.debug(f"DEBUG - Converted to OpenAlgo symbol: {tradingsymbol}")
                else:
                    logger.debug(
                        f"DEBUG - Could not convert to OpenAlgo symbol, using original: {tradingsymbol}"
                    )
            except Exception as e:
                logger.error(f"DEBUG - Error converting symbol to OpenAlgo format: {e}")
                # If conversion fails, still use the cleaned symbol
                logger.debug(f"DEBUG - Using original symbol: {tradingsymbol}")

        # Get quantity with fallbacks for different field names
        quantity = 0
        for field in ["quantity", "free_quantity", "qty"]:
            if field in holding and holding[field] is not None:
                try:
                    quantity = int(float(holding[field]))
                    logger.info(f"DEBUG - Found quantity in '{field}' field: {quantity}")
                    break
                except (ValueError, TypeError):
                    continue

        # Get average price with fallbacks
        average_price = 0.0
        for field in ["average_price", "buy_avg", "avg_price", "buy_price"]:
            if field in holding and holding[field] is not None:
                try:
                    average_price = float(holding[field])
                    logger.info(f"DEBUG - Found average price in '{field}' field: {average_price}")
                    break
                except (ValueError, TypeError):
                    continue

        # Get last price (LTP) with fallbacks
        last_price = 0.0
        for field in ["last_price", "ltp", "current_price", "market_price"]:
            if field in holding and holding[field] is not None:
                try:
                    last_price = float(holding[field])
                    logger.info(f"DEBUG - Found last price in '{field}' field: {last_price}")
                    break
                except (ValueError, TypeError):
                    continue

        # Calculate P&L if not directly provided
        pnl = 0.0
        if "pnl" in holding and holding["pnl"] is not None:
            try:
                pnl = float(holding["pnl"])
            except (ValueError, TypeError):
                # Calculate if conversion fails
                pnl = (
                    (last_price - average_price) * quantity
                    if quantity > 0 and average_price > 0
                    else 0.0
                )
        else:
            # Calculate if not provided
            pnl = (
                (last_price - average_price) * quantity
                if quantity > 0 and average_price > 0
                else 0.0
            )

        # Calculate P&L percentage
        pnl_percent = 0.0
        if "pnl_percent" in holding or "pnl_percentage" in holding:
            try:
                pnl_percent = float(
                    holding.get("pnl_percent") or holding.get("pnl_percentage", 0.0)
                )
            except (ValueError, TypeError):
                # Calculate if conversion fails
                pnl_percent = (
                    ((last_price - average_price) / average_price * 100)
                    if average_price > 0
                    else 0.0
                )
        else:
            # Calculate if not provided
            pnl_percent = (
                ((last_price - average_price) / average_price * 100) if average_price > 0 else 0.0
            )

        logger.debug(f"DEBUG - Final transformed symbol: {tradingsymbol}")
        logger.debug(f"DEBUG - P&L calculated: {pnl}")

        # Create transformed holding with all available fields
        transformed_holding = {
            "symbol": tradingsymbol,  # This must never be None
            "exchange": exchange,
            "quantity": quantity,
            "average_price": round(average_price, 2),
            "last_price": round(last_price, 2),
            "product": "CNC",  # Holdings are always CNC (Cash and Carry)
            "pnl": round(pnl, 2),
            "pnlpercent": round(pnl_percent, 2),
            # Additional fields with fallbacks
            "close_price": float(holding.get("close_price") or holding.get("previous_close", 0.0)),
            "isin": holding.get("isin", ""),
            "day_change": float(holding.get("day_change", 0.0)),
            "day_change_percentage": float(holding.get("day_change_percentage", 0.0)),
        }

        # Ensure symbol is never None in the final output
        if transformed_holding["symbol"] is None:
            logger.warning("WARNING: Symbol is still None after transformation. Using fallback.")
            # Try using the 'symbol' field directly, which should be available in the Pocketful API response
            if "symbol" in holding and holding["symbol"]:
                transformed_holding["symbol"] = holding["symbol"]
                logger.info(
                    f"DEBUG - Using symbol from input directly: {transformed_holding['symbol']}"
                )
            # If still no symbol, use trading_symbol
            elif "trading_symbol" in holding and holding["trading_symbol"]:
                transformed_holding["symbol"] = holding["trading_symbol"]
                logger.info(
                    f"DEBUG - Using trading_symbol as fallback: {transformed_holding['symbol']}"
                )
            # Next try ISIN as a fallback
            elif transformed_holding["isin"]:
                transformed_holding["symbol"] = f"ISIN_{transformed_holding['isin']}"
                logger.info(
                    f"DEBUG - Using ISIN as symbol placeholder: {transformed_holding['symbol']}"
                )
            # Last resort - use a placeholder with a unique identifier
            else:
                unique_id = (
                    hash(str(holding)) % 10000
                )  # Create a deterministic ID from the holding data
                transformed_holding["symbol"] = f"UNKNOWN_{unique_id}"
                logger.warning(
                    f"WARNING: Created placeholder symbol: {transformed_holding['symbol']}"
                )

        transformed_data.append(transformed_holding)

    logger.debug(f"DEBUG - Transformed {len(transformed_data)} holdings entries")
    if transformed_data and len(transformed_data) > 0:
        logger.debug(f"DEBUG - Sample transformed holding: {transformed_data[0]}")

    return transformed_data


def map_portfolio_data(portfolio_data):
    """
    Processes and modifies a list of Portfolio dictionaries based on specific conditions.

    Parameters:
    - portfolio_data: Data from the holdings API, could be a list of dictionaries or a dict with data inside.

    Returns:
    - The processed portfolio data with standardized 'product' fields.
    """
    logger.debug(f"DEBUG - map_portfolio_data input type: {type(portfolio_data)}")

    # Handle different input formats safely
    processed_data = []

    # Case 1: portfolio_data is a dict with 'data' key
    if isinstance(portfolio_data, dict) and "data" in portfolio_data:
        if portfolio_data["data"] is None:
            logger.info("DEBUG - No data available in portfolio_data['data'].")
            return []
        processed_data = portfolio_data["data"]

    # Case 2: portfolio_data is already a list
    elif isinstance(portfolio_data, list):
        processed_data = portfolio_data

    # Case 3: portfolio_data is a dict but doesn't have 'data' key
    elif isinstance(portfolio_data, dict):
        logger.debug(f"DEBUG - Portfolio data keys: {portfolio_data.keys()}")
        # Try to find list data in other common keys
        for key in ["holdings", "holdingsData", "portfolio"]:
            if key in portfolio_data and isinstance(portfolio_data[key], list):
                processed_data = portfolio_data[key]
                break
        # If still no data found but there are dict values, check if any value is a list
        if not processed_data:
            for key, value in portfolio_data.items():
                if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                    processed_data = value
                    break

    # Final check and processing
    if not processed_data:
        logger.debug("DEBUG - No portfolio data found after processing.")
        return []

    logger.debug(f"DEBUG - Processing {len(processed_data)} portfolio entries")

    # Process each portfolio item
    for item in processed_data:
        if "product" in item:
            # Ensure CNC is correctly mapped (it already is for Pocketful)
            if item["product"] == "CNC":
                pass  # Already correct
            else:
                logger.info(f"DEBUG - Non-CNC product found: {item['product']}")
        else:
            # If product is missing, default to CNC for holdings
            item["product"] = "CNC"

    return processed_data


def calculate_portfolio_statistics(holdings_data):
    """
    Calculate portfolio statistics from holdings data.

    Args:
        holdings_data: List of transformed holdings data entries

    Returns:
        Dictionary with portfolio statistics
    """
    if not holdings_data:
        logger.info("No holdings data available for calculating statistics")
        return {
            "totalholdingvalue": 0.0,
            "totalinvvalue": 0.0,
            "totalprofitandloss": 0.0,
            "totalpnlpercentage": 0.0,
        }

    logger.debug(
        f"DEBUG - Calculating portfolio statistics for {len(holdings_data)} holdings entries"
    )

    try:
        # Calculate total holding value (current market value)
        totalholdingvalue = sum(
            float(item.get("last_price", 0)) * float(item.get("quantity", 0))
            for item in holdings_data
        )

        # Calculate total investment value (cost basis)
        totalinvvalue = sum(
            float(item.get("average_price", 0)) * float(item.get("quantity", 0))
            for item in holdings_data
        )

        # Get the sum of all individual P&Ls
        totalprofitandloss = sum(float(item.get("pnl", 0)) for item in holdings_data)

        # Calculate overall P&L percentage (avoiding division by zero)
        totalpnlpercentage = (
            (totalprofitandloss / totalinvvalue * 100) if totalinvvalue > 0 else 0.0
        )

        # Round values for better display
        result = {
            "totalholdingvalue": round(totalholdingvalue, 2),
            "totalinvvalue": round(totalinvvalue, 2),
            "totalprofitandloss": round(totalprofitandloss, 2),
            "totalpnlpercentage": round(totalpnlpercentage, 2),
        }

        logger.debug(f"DEBUG - Portfolio statistics: {result}")
        return result

    except Exception as e:
        logger.error(f"ERROR - Failed to calculate portfolio statistics: {e}")
        return {
            "totalholdingvalue": 0.0,
            "totalinvvalue": 0.0,
            "totalprofitandloss": 0.0,
            "totalpnlpercentage": 0.0,
        }

```


---

# FILE: broker\pocketful\mapping\transform_data.py

```py
# Mapping OpenAlgo API Request https://openalgo.in/docs
# Mapping Pocketful API Parameters https://api.pocketful.in/docs/

from broker.pocketful.api.data import BrokerData
from database.token_db import get_br_symbol, get_symbol_info, get_token
from utils.logging import get_logger
from utils.mpp_slab import calculate_protected_price, get_instrument_type_from_symbol

logger = get_logger(__name__)


def transform_data(data, client_id=None, auth_token=None):
    """
    Transforms OpenAlgo order format to Pocketful order format.
    For market orders, fetches quotes and adjusts price using MPP (Market Price Protection):
    - EQ/FUT: Price < 100: 2%, 100-500: 1%, > 500: 0.5%
    - OPT (CE/PE): Price < 10: 5%, 10-100: 3%, 100-500: 2%, > 500: 1%

    Args:
        data: OpenAlgo order data dictionary
        client_id: Client ID to use for the order, if available
        auth_token: Authentication token for fetching quotes (passed from order_api)
    """
    # Get broker symbol for the order
    symbol = get_br_symbol(data["symbol"], data["exchange"])

    # Get the numeric token for the symbol
    token = get_token(data["symbol"], data["exchange"])

    # Map order type
    order_type = map_order_type(data["pricetype"])

    # Map order side (BUY/SELL)
    order_side = data["action"].upper()

    # Map product type
    product = map_product_type(data["product"])

    # Default price
    price = float(data.get("price", "0"))

    # Apply Market Price Protection for MARKET orders (case-insensitive check)
    if str(data.get("pricetype") or "").upper() == "MARKET":
        logger.info(
            f"MPP: MARKET order detected for Symbol={data['symbol']}, Exchange={data['exchange']}, Action={order_side}"
        )
        try:
            if auth_token:
                # Create BrokerData instance to fetch quotes
                broker_data = BrokerData(auth_token)

                # Fetch quotes for the symbol
                quote_data = broker_data.get_quotes(data["symbol"], data["exchange"])
                logger.info(
                    f"MPP Quote Response: Symbol={data['symbol']}, Exchange={data['exchange']}, "
                    f"LTP={quote_data.get('ltp')}, Bid={quote_data.get('bid')}, Ask={quote_data.get('ask')}"
                )

                # Get instrument type from symbol
                instrument_type = get_instrument_type_from_symbol(data["symbol"])

                # Get tick_size from database
                tick_size = None
                symbol_info = get_symbol_info(data["symbol"], data["exchange"])
                if symbol_info and symbol_info.tick_size:
                    tick_size = symbol_info.tick_size
                logger.info(
                    f"MPP Symbol Info: InstrumentType={instrument_type}, TickSize={tick_size}"
                )

                # Get LTP for price calculation
                ltp = float(quote_data.get("ltp", 0))

                if ltp > 0:
                    # Calculate protected price using centralized MPP slab with tick size from database
                    protected_price = calculate_protected_price(
                        price=ltp,
                        action=order_side,
                        symbol=data["symbol"],
                        instrument_type=instrument_type,
                        tick_size=tick_size,
                    )
                    price = protected_price

                    # Convert order type from MARKET to LIMIT
                    order_type = "LIMIT"
                    logger.info(
                        f"MPP Conversion Complete: Symbol={data['symbol']}, OrderType=MARKET->LIMIT, "
                        f"FinalPrice={protected_price}"
                    )
                else:
                    logger.warning(
                        f"MPP Warning: LTP is 0 or invalid for Symbol={data['symbol']}, "
                        f"Exchange={data['exchange']}. Proceeding with regular market order"
                    )
            else:
                logger.warning(
                    f"MPP Warning: No auth token available for Symbol={data['symbol']}. "
                    f"Cannot fetch quotes for MPP adjustment"
                )
        except Exception as e:
            logger.error(
                f"MPP Error: Failed to apply MPP for Symbol={data['symbol']}, "
                f"Exchange={data['exchange']}, Error={str(e)}. Proceeding with regular market order."
            )

    # Basic mapping
    transformed = {
        "exchange": data["exchange"],
        "instrument_token": token,  # Pocketful uses numeric instrument_token
        "client_id": client_id,  # Use the provided client_id
        "order_type": order_type,
        "amo": False,  # Default to regular order
        "price": price,
        "quantity": int(data["quantity"]),
        "disclosed_quantity": int(data.get("disclosed_quantity", "0")),
        "validity": "DAY",
        "product": product,
        "order_side": order_side,
        "device": "WEB",  # Default to WEB
        "user_order_id": 1,  # Default value
        "trigger_price": float(data.get("trigger_price", "0")),
        "execution_type": "REGULAR",  # Default to regular order
    }

    # Log order data for debugging
    logger.info(
        f"Transformed order data: exchange={transformed['exchange']}, "
        f"order_type={transformed['order_type']}, price={transformed['price']}, "
        f"quantity={transformed['quantity']}, order_side={transformed['order_side']}"
    )

    # Extended mapping for fields that might need conditional logic or additional processing
    transformed["disclosed_quantity"] = int(data.get("disclosed_quantity", "0"))
    transformed["trigger_price"] = float(data.get("trigger_price", "0"))

    return transformed


def transform_modify_order_data(data, client_id=None):
    """
    Transforms OpenAlgo order modification format to Pocketful order format.

    Args:
        data: OpenAlgo order data dictionary
        client_id: Client ID to use for the order, if available
    """
    # Get broker symbol for the order
    symbol = get_br_symbol(data["symbol"], data["exchange"])

    # Get the numeric token for the symbol
    token = get_token(data["symbol"], data["exchange"])

    # Map order type
    order_type = map_order_type(data["pricetype"])

    # Map order side (BUY/SELL)
    order_side = data["action"].upper()

    # Map product type
    product = map_product_type(data["product"])

    # Create the transformed data dictionary with all required fields for Pocketful API
    return {
        "exchange": data["exchange"],
        "instrument_token": token,
        "client_id": client_id,
        "order_type": order_type,
        "price": float(data.get("price", "0")),
        "quantity": int(data["quantity"]),
        "disclosed_quantity": int(data.get("disclosed_quantity", "0")),
        "validity": "DAY",
        "product": product,
        "order_side": order_side,
        "device": "WEB",
        "user_order_id": 1,
        "trigger_price": float(data.get("trigger_price", "0")),
        "oms_order_id": data.get(
            "orderid", ""
        ),  # This is the ID needed to identify which order to modify
        "execution_type": "REGULAR",
    }


def map_order_type(pricetype):
    """
    Maps OpenAlgo pricetype to Pocketful order type.
    """
    order_type_mapping = {
        "MARKET": "MARKET",
        "LIMIT": "LIMIT",
        "SL": "SL",
        "SL-M": "SLM",  # Pocketful uses SLM instead of SL-M
    }
    return order_type_mapping.get(pricetype.upper(), "MARKET")  # Default to MARKET if not found


def map_product_type(product):
    """
    Maps OpenAlgo product type to Pocketful product type.
    """
    product_type_mapping = {"CNC": "CNC", "NRML": "NRML", "MIS": "MIS"}
    return product_type_mapping.get(product.upper(), "MIS")  # Default to MIS if not found


def reverse_map_product_type(exchange, product):
    """
    Reverse maps the broker product type to the OpenAlgo product type, considering the exchange.
    """
    # Exchange to OpenAlgo product type mapping for 'D'
    exchange_mapping = {
        "CNC": "CNC",
        "NRML": "NRML",
        "MIS": "MIS",
    }

    return exchange_mapping.get(product)

```
