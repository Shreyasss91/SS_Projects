# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\groww\mapping



---

# FILE: broker\groww\mapping\margin_data.py

```py
# Mapping OpenAlgo API Request https://openalgo.in/docs
# Mapping Groww Margin API

from broker.groww.mapping.transform_data import (
    map_order_type,
    map_product_type,
    map_segment_type,
    map_transaction_type,
)
from database.token_db import get_br_symbol
from utils.logging import get_logger

logger = get_logger(__name__)


def map_margin_exchange(exchange):
    """
    Maps the OpenAlgo Exchange to Groww Exchange values for margin API.
    Groww only accepts NSE/BSE - segment (CASH/FNO) is passed separately.
    """
    exchange_mapping = {
        "NSE": "NSE",
        "BSE": "BSE",
        "NFO": "NSE",  # F&O on NSE - segment=FNO handles the distinction
        "BFO": "BSE",  # F&O on BSE - segment=FNO handles the distinction
    }
    return exchange_mapping.get(exchange.upper(), "NSE")


def transform_margin_positions(positions):
    """
    Transform OpenAlgo margin positions to Groww margin format.

    Args:
        positions: List of positions in OpenAlgo format

    Returns:
        Tuple of (segment, transformed_positions_list)
        - segment: "CASH" or "FNO"
        - transformed_positions_list: List of positions in Groww format
    """
    transformed_positions = []
    segment = None

    for position in positions:
        try:
            symbol = position["symbol"]
            exchange = position["exchange"]

            # Determine segment from exchange
            position_segment = map_segment_type(exchange)

            # All positions in a request must be from the same segment
            if segment is None:
                segment = position_segment
            elif segment != position_segment:
                logger.warning(
                    f"Mixed segments detected. Groww only supports single segment per request. Using first segment: {segment}"
                )
                continue

            # Get broker symbol from database (Groww uses different symbol format)
            broker_symbol = get_br_symbol(symbol, exchange)
            if not broker_symbol:
                logger.warning(
                    f"Broker symbol not found for {symbol} on {exchange}, using original symbol"
                )
                broker_symbol = symbol

            # Transform the position
            transformed_position = {
                "trading_symbol": broker_symbol,
                "transaction_type": map_transaction_type(position["action"]),
                "quantity": int(position["quantity"]),
                "order_type": map_order_type(position["pricetype"]),
                "product": map_product_type(position["product"]),
                "exchange": map_margin_exchange(exchange),
            }

            # Add price if provided (for LIMIT orders)
            if position.get("price") and float(position["price"]) > 0:
                transformed_position["price"] = float(position["price"])

            transformed_positions.append(transformed_position)

        except Exception as e:
            logger.error(f"Error transforming position: {position}, Error: {e}")
            continue

    # Default to CASH if no positions were successfully transformed
    if segment is None:
        segment = "CASH"

    return segment, transformed_positions


def parse_margin_response(response_data):
    """
    Parse Groww margin response to OpenAlgo standard format.

    Args:
        response_data: Raw response from Groww API

    Returns:
        Standardized margin response
    """
    try:
        if not response_data or not isinstance(response_data, dict):
            return {"status": "error", "message": "Invalid response from broker"}

        # Check if the response status is SUCCESS
        if response_data.get("status") != "SUCCESS":
            error_message = response_data.get("message", "Failed to calculate margin")
            # Check for errors array
            if "errors" in response_data and isinstance(response_data["errors"], list):
                if len(response_data["errors"]) > 0:
                    error_message = response_data["errors"][0].get("message", error_message)
            return {"status": "error", "message": error_message}

        # Extract margin data from payload
        payload = response_data.get("payload", {})

        # Calculate total margin
        total_requirement = float(payload.get("total_requirement", 0))

        # Return standardized format matching OpenAlgo API specification
        return {
            "status": "success",
            "data": {
                "total_margin_required": total_requirement,
                "span_margin": float(payload.get("span_required") or 0),
                "exposure_margin": float(payload.get("exposure_required") or 0),
            },
        }

    except Exception as e:
        logger.error(f"Error parsing margin response: {e}")
        return {"status": "error", "message": f"Failed to parse margin response: {str(e)}"}

```


---

# FILE: broker\groww\mapping\order_data.py

```py
import datetime
import json
import os
import re
from typing import Any, Dict, List, Optional

import pandas as pd

from broker.dhan.mapping.transform_data import map_exchange
from database.token_db import get_symbol
from utils.logging import get_logger

logger = get_logger(__name__)


def map_order_data(order_data):
    """
    Processes and modifies order data from Groww format to OpenAlgo format.

    Parameters:
    - order_data: A dictionary with either 'data' key or raw Groww API response with 'order_list'.

    Returns:
    - The modified order_data with standardized fields in OpenAlgo format.
    """
    logger.info("Starting map_order_data function")
    logger.debug(f"Order data type: {type(order_data)}")

    # Initialize empty result
    mapped_orders = []

    # Handle empty input
    if not order_data:
        logger.warning("Order data is None or empty")
        return mapped_orders

    # Determine which data source to use
    orders_to_process = None

    # For debugging, log all keys in the structure
    if isinstance(order_data, dict):
        logger.debug(f"Keys in order_data: {list(order_data.keys())}")
        if "raw_response" in order_data and isinstance(order_data["raw_response"], dict):
            logger.debug(f"Keys in raw_response: {list(order_data['raw_response'].keys())}")

    # Try raw_response (direct Groww API format) first if it exists
    if isinstance(order_data, dict) and "raw_response" in order_data and order_data["raw_response"]:
        raw_response = order_data["raw_response"]
        if "order_list" in raw_response and raw_response["order_list"]:
            logger.info("Using raw_response.order_list for mapping")
            orders_to_process = raw_response["order_list"]

    # Then try the data array if raw_response wasn't available or was empty
    if not orders_to_process and isinstance(order_data, dict) and "data" in order_data:
        if order_data["data"]:
            logger.info("Using data array for mapping")
            orders_to_process = order_data["data"]

    # Handle direct order_list format (from Groww API)
    if not orders_to_process and isinstance(order_data, dict) and "order_list" in order_data:
        if order_data["order_list"]:
            logger.info("Using direct order_list for mapping")
            orders_to_process = order_data["order_list"]

    # If no valid orders found, return empty result
    if not orders_to_process:
        logger.warning("No valid orders found for mapping")
        return mapped_orders

    logger.info(f"Processing {len(orders_to_process)} orders")

    for i, order in enumerate(orders_to_process):
        logger.debug(f"Processing order {i + 1}/{len(orders_to_process)}")
        logger.debug(f"Original order: {order}")

        # Get fields from order - handle both original Groww API and our standardized format
        order_id = order.get("groww_order_id", order.get("orderid", ""))
        symbol = order.get("trading_symbol", order.get("tradingsymbol", ""))
        status = order.get("order_status", order.get("status", ""))
        remark = order.get("remark", order.get("remarks", ""))
        order_type = order.get("order_type", order.get("pricetype", "MARKET"))
        transaction_type = order.get("transaction_type", order.get("action", ""))
        product = order.get("product", "")
        timestamp = order.get("created_at", order.get("timestamp", ""))

        # For debugging
        if i == 0:
            logger.debug(f"Sample order id: {order_id}, symbol: {symbol}, type: {order_type}")

        # Get the trading symbol from Groww order data
        broker_symbol = order.get("trading_symbol", "")
        exchange = order.get("exchange", "")

        # Convert broker symbol to OpenAlgo format
        openalgo_symbol = broker_symbol

        # If it's an options or futures symbol (especially for NFO exchange)
        if exchange == "NFO" and broker_symbol and " " in broker_symbol:
            try:
                # Import the conversion function
                from broker.groww.database.master_contract_db import format_groww_to_openalgo_symbol

                openalgo_symbol = format_groww_to_openalgo_symbol(broker_symbol, exchange)
                logger.info(f"Transformed display symbol: {broker_symbol} -> {openalgo_symbol}")
            except Exception as e:
                logger.error(f"Error converting symbol format: {e}")

        # Look up in database as fallback
        if openalgo_symbol == broker_symbol and " " in broker_symbol:
            try:
                # Look up in database
                from broker.groww.database.master_contract_db import SymToken, db_session

                db_record = (
                    db_session.query(SymToken)
                    .filter_by(brsymbol=broker_symbol, brexchange=exchange)
                    .first()
                )
                if db_record and db_record.symbol:
                    openalgo_symbol = db_record.symbol
                    logger.info(f"Found symbol in database: {broker_symbol} -> {openalgo_symbol}")
            except Exception as e:
                logger.error(f"Error looking up symbol in database: {e}")

        mapped_order = {
            "orderid": order.get("groww_order_id", ""),
            "symbol": openalgo_symbol,  # Using the converted OpenAlgo format symbol
            "exchange": order.get("exchange", "NSE"),
            "transaction_type": order.get("transaction_type", ""),
            "order_type": order.get("order_type", "MARKET"),
            "status": order.get(
                "order_status", order.get("status", "")
            ),  # Try order_status first, then status
            "product": order.get("product", "CNC"),
            "quantity": order.get("quantity", 0),
            "price": order.get("price", 0.0),
            "trigger_price": order.get("trigger_price", 0.0),
            "order_timestamp": order.get("created_at", ""),
            "order_reference_id": order.get("order_reference_id", ""),
        }

        # Map status to OpenAlgo format
        status_map = {
            "NEW": "open",
            "ACKED": "open",
            "OPEN": "open",  # Added OPEN status from Groww API
            "TRIGGER_PENDING": "trigger pending",
            "APPROVED": "open",
            "EXECUTED": "complete",
            "COMPLETED": "complete",
            "CANCELLED": "cancelled",
            "REJECTED": "rejected",
        }
        original_status = mapped_order["status"]
        mapped_order["status"] = status_map.get(original_status, "open")
        logger.debug(f"Mapped status from '{original_status}' to '{mapped_order['status']}'")

        # Map product type to OpenAlgo format
        original_product = mapped_order["product"]
        if original_product == "CNC":
            mapped_order["product"] = "CNC"
        elif original_product == "INTRADAY":
            mapped_order["product"] = "MIS"
        elif original_product == "MARGIN":
            mapped_order["product"] = "NRML"

        logger.debug(f"Mapped product from '{original_product}' to '{mapped_order['product']}'")
        logger.debug(f"Mapped order: {mapped_order}")

        mapped_orders.append(mapped_order)

    logger.info(f"Finished mapping {len(mapped_orders)} orders")
    return mapped_orders


def calculate_order_statistics(order_data):
    """
    Calculates statistics from order data, including totals for buy orders, sell orders,
    completed orders, open orders, and rejected orders.

    Parameters:
    - order_data: Can be either:
      1. A list of order dictionaries (direct from get_order_book)
      2. A dictionary with nested data structures (for backward compatibility)

    Returns:
    - A dictionary containing counts of different types of orders.
    """
    logger.info("Starting calculate_order_statistics")
    logger.debug(f"Order data type: {type(order_data)}")

    # Initialize counters
    total_buy_orders = total_sell_orders = 0
    total_completed_orders = total_open_orders = total_rejected_orders = 0

    # Default empty statistics
    default_stats = {
        "total_buy_orders": 0,
        "total_sell_orders": 0,
        "total_completed_orders": 0,
        "total_open_orders": 0,
        "total_rejected_orders": 0,
    }

    # Handle empty input
    if not order_data:
        logger.warning("Order data is None or empty in calculate_order_statistics")
        return default_stats

    # Determine which data structure we're dealing with
    orders_to_process = None

    # Case 1: Direct list of orders (preferred new format)
    if isinstance(order_data, list):
        logger.info("Using direct list of orders for statistics")
        orders_to_process = order_data
    # Case 2: Nested dictionary with 'data' key (backward compatibility)
    elif isinstance(order_data, dict) and "data" in order_data:
        logger.info("Using nested data dictionary for statistics")
        orders_to_process = order_data["data"]
    # Case 3: Direct Groww API response with 'order_list' (original API format)
    elif isinstance(order_data, dict) and "order_list" in order_data:
        logger.info("Using direct order_list for statistics")
        orders_to_process = order_data["order_list"]

    # If no valid order data found, return default stats
    if not orders_to_process:
        logger.warning("No valid orders found for statistics calculation")
        return default_stats

    logger.info(f"Calculating statistics for {len(orders_to_process)} orders")

    for i, order in enumerate(orders_to_process):
        # Log the structure of the first order for debugging
        if i == 0:
            logger.debug(f"Sample order structure for statistics: {order}")

        # Count buy and sell orders
        transaction_type = order.get("transaction_type")
        if transaction_type == "BUY":
            total_buy_orders += 1
        elif transaction_type == "SELL":
            total_sell_orders += 1
        else:
            logger.debug(f"Unknown transaction type: {transaction_type}")

        # Count orders based on their status
        status = order.get("order_status")
        if status in ["EXECUTED", "COMPLETED"]:
            total_completed_orders += 1
        elif status in ["NEW", "ACKED", "APPROVED", "OPEN"]:
            total_open_orders += 1
        elif status == "REJECTED":
            total_rejected_orders += 1
        else:
            logger.debug(f"Order with status not counted in statistics: {status}")

    # Compile statistics
    stats = {
        "total_buy_orders": total_buy_orders,
        "total_sell_orders": total_sell_orders,
        "total_completed_orders": total_completed_orders,
        "total_open_orders": total_open_orders,
        "total_rejected_orders": total_rejected_orders,
    }

    logger.info(f"Order statistics calculated: {stats}")
    return stats


def transform_order_data(orders):
    """
    Transform order data from Groww API format to OpenAlgo standard format

    Args:
        orders (dict): Order data from Groww API

    Returns:
        list: Transformed orders in OpenAlgo format for orderbook.py
    """
    logger.info("Starting transform_order_data function")
    logger.debug(f"Input order data type: {type(orders)}")

    # If we get a list directly, these are already mapped orders from map_order_data
    if isinstance(orders, list):
        logger.info(f"Received {len(orders)} pre-mapped orders")
        orders_to_process = orders
    else:
        # Try to extract orders from different possible structures
        orders_to_process = []

        # If orders is None or empty, return empty list
        if not orders:
            logger.warning("Orders input is None or empty")
            return []

        # Handle dictionary structures with data or order_list
        if isinstance(orders, dict):
            # Log keys for debugging
            logger.debug(f"Keys in orders: {list(orders.keys()) if orders else 'None'}")

            # Try raw_response.order_list format
            if "raw_response" in orders and orders["raw_response"]:
                raw_response = orders["raw_response"]
                logger.debug(
                    f"Raw response keys: {list(raw_response.keys()) if raw_response else 'None'}"
                )
                if "order_list" in raw_response and raw_response["order_list"]:
                    logger.info("Using raw_response.order_list for transformation")
                    orders_to_process = raw_response["order_list"]

            # Try data array format
            if not orders_to_process and "data" in orders and orders["data"]:
                logger.info("Using data array for transformation")
                orders_to_process = orders["data"]

            # Try direct order_list format
            if not orders_to_process and "order_list" in orders and orders["order_list"]:
                logger.info("Using direct order_list for transformation")
                orders_to_process = orders["order_list"]

    # If we still couldn't find orders, return empty list
    if not orders_to_process:
        logger.warning("No valid orders found for transformation")
        return []

    logger.info(f"Processing {len(orders_to_process)} orders for transformation")
    transformed_orders = []

    # Dump first order for debug
    if len(orders_to_process) > 0:
        logger.debug(f"Sample order to transform: {orders_to_process[0]}")

    for i, order in enumerate(orders_to_process):
        # Get fields with fallbacks between original and mapped formats
        order_id = order.get("groww_order_id", order.get("orderid", ""))

        # Get the symbol, with fallbacks to other field names
        broker_symbol = order.get(
            "trading_symbol", order.get("tradingsymbol", order.get("symbol", ""))
        )
        exchange = order.get("exchange", "NSE")

        # Get proper OpenAlgo symbol from database using token lookup
        token = None
        symbol = broker_symbol

        # Try to get token from order data if available
        if "token" in order:
            token = order.get("token")

        # If we have a token or brsymbol (tradingsymbol/trading_symbol), look up the OpenAlgo symbol from the database
        try:
            from database.token_db import get_oa_symbol

            # Try to get the OpenAlgo symbol using the token if available
            if token:
                openalgo_symbol = get_oa_symbol(token, exchange)
                if openalgo_symbol:
                    symbol = openalgo_symbol
                    logger.info(f"Found OpenAlgo symbol by token: {broker_symbol} -> {symbol}")

            # If token lookup failed or token wasn't available, try by broker symbol
            elif broker_symbol:
                # First check if we already have the OpenAlgo symbol
                if exchange == "NFO" and (
                    broker_symbol.endswith("CE") or broker_symbol.endswith("PE")
                ):
                    # Query the database to find the OpenAlgo symbol for this broker symbol
                    from broker.groww.database.master_contract_db import SymToken, db_session

                    with db_session() as session:
                        record = (
                            session.query(SymToken)
                            .filter(
                                SymToken.brsymbol == broker_symbol, SymToken.exchange == exchange
                            )
                            .first()
                        )

                        if record and record.symbol:
                            symbol = record.symbol
                            logger.info(
                                f"Found OpenAlgo symbol in database: {broker_symbol} -> {symbol}"
                            )
        except Exception as e:
            logger.error(f"Error looking up OpenAlgo symbol from database: {e}")
            # Fall back to the original symbol
            symbol = broker_symbol

        # Make sure we get the status from all possible fields
        status = order.get("order_status", order.get("status", ""))
        logger.debug(f"Order {i} raw status: {status}")

        order_type = order.get("order_type", order.get("pricetype", "MARKET"))
        transaction_type = order.get("transaction_type", order.get("action", ""))
        product = order.get("product", order.get("product", "CNC"))
        timestamp = order.get(
            "created_at", order.get("timestamp", order.get("order_timestamp", ""))
        )
        price = order.get("price", 0.0)
        trigger_price = order.get("trigger_price", 0.0)
        quantity = order.get("quantity", 0)

        # Map order type to OpenAlgo format
        mapped_order_type = order_type
        if order_type == "STOP_LOSS":
            mapped_order_type = "SL"
        elif order_type == "STOP_LOSS_MARKET":
            mapped_order_type = "SL-M"

        # Map product type
        mapped_product = product
        if product == "INTRADAY":
            mapped_product = "MIS"
        elif product == "MARGIN":
            mapped_product = "NRML"

        # Map status
        status_map = {
            "NEW": "open",
            "ACKED": "open",
            "OPEN": "open",
            "TRIGGER_PENDING": "trigger pending",
            "APPROVED": "open",
            "EXECUTED": "complete",
            "COMPLETED": "complete",
            "CANCELLED": "cancelled",
            "REJECTED": "rejected",
        }
        # Log original status for debugging
        logger.debug(f"Original order status for order {i}: '{status}'")

        # Important: Use the status map but ensure we have a fallback value
        # If status isn't in our map, use the lowercase version of the original status
        mapped_status = status_map.get(status, status.lower() if status else "")
        logger.debug(f"Mapped status for order {i}: '{mapped_status}'")

        # Log key fields for debugging
        logger.debug(
            f"Order {i}: Symbol='{symbol}', ID='{order_id}', Type='{mapped_order_type}', Product='{mapped_product}'"
        )

        # For NFO instruments, ensure the symbol is in OpenAlgo format (AARTIIND29MAY25630CE)
        exchange = order.get("exchange", "NSE")
        if exchange == "NFO" and " " in symbol:
            try:
                # Import the conversion function
                from broker.groww.database.master_contract_db import format_groww_to_openalgo_symbol

                openalgo_symbol = format_groww_to_openalgo_symbol(symbol, exchange)
                if openalgo_symbol:
                    # Store broker symbol for reference
                    broker_symbol = symbol
                    # Use OpenAlgo symbol format for display
                    symbol = openalgo_symbol
                    logger.info(f"Transformed order symbol for UI: {broker_symbol} -> {symbol}")
            except Exception as e:
                logger.error(f"Error converting order symbol format: {e}")

        # Create transformed order in OpenAlgo format
        transformed_order = {
            "symbol": symbol,  # Now guaranteed to be in OpenAlgo format
            "exchange": order.get("exchange", "NSE"),
            "action": transaction_type,
            "quantity": quantity,
            "price": price,
            "trigger_price": trigger_price,
            "pricetype": mapped_order_type,
            "product": mapped_product,
            "orderid": order_id,
            "order_status": mapped_status,
            "timestamp": timestamp,
        }

        # Add to result
        transformed_orders.append(transformed_order)

    logger.info(f"Successfully transformed {len(transformed_orders)} orders")

    # Final check to ensure all symbols are in OpenAlgo format using database lookups
    # This avoids complex transformations since the database already has the correct symbols
    for order in transformed_orders:
        # Only process NFO symbols that might be in broker format
        if order.get("exchange") == "NFO" and "symbol" in order and order["symbol"]:
            symbol = order["symbol"]

            # If token is available, try token lookup first
            token = order.get("token")
            if token:
                try:
                    from database.token_db import get_oa_symbol

                    openalgo_symbol = get_oa_symbol(token, order.get("exchange", "NSE"))
                    if openalgo_symbol:
                        order["symbol"] = openalgo_symbol
                        logger.info(f"Final token lookup: {symbol} -> {openalgo_symbol}")
                        continue
                except Exception as e:
                    logger.error(f"Error in final token lookup: {e}")

            # Last resort - try looking up the broker symbol directly from database
            try:
                from broker.groww.database.master_contract_db import SymToken, db_session

                with db_session() as session:
                    # Look for this symbol as a broker symbol (brsymbol) in the database
                    record = (
                        session.query(SymToken)
                        .filter(
                            SymToken.brsymbol == symbol,
                            SymToken.exchange == order.get("exchange", "NSE"),
                        )
                        .first()
                    )

                    if record and record.symbol:
                        order["symbol"] = record.symbol
                        logger.info(f"Final db lookup: {symbol} -> {record.symbol}")
            except Exception as e:
                logger.error(f"Error in final database lookup: {e}")

    return transformed_orders


def map_trade_data(trade_data):
    logger.info(f"Map trade data received type: {type(trade_data)}")

    # If it's a tuple with status code (from direct API), extract the data
    if isinstance(trade_data, tuple) and len(trade_data) == 2:
        trade_data = trade_data[0]
        logger.info("Extracted trade data from tuple")

    # Handle direct list of trades (which our get_trade_book now returns)
    if isinstance(trade_data, list):
        logger.info(f"Received direct list of {len(trade_data)} trades")
        return trade_data

    # Handle dictionary formats
    if isinstance(trade_data, dict):
        # Log keys for debugging
        logger.info(f"Trade data dict keys: {list(trade_data.keys())}")

        # Check for data field
        if "data" in trade_data and isinstance(trade_data["data"], list):
            logger.info(f"Using 'data' field with {len(trade_data['data'])} trades")
            return trade_data["data"]

        # Check for tradebook field
        if "tradebook" in trade_data and isinstance(trade_data["tradebook"], list):
            logger.info(f"Using 'tradebook' field with {len(trade_data['tradebook'])} trades")
            return trade_data["tradebook"]

    # If all else fails, try the regular order mapping (fallback)
    logger.info("Falling back to regular order mapping")
    return map_order_data(trade_data)


def transform_tradebook_data(tradebook_data):
    logger.info(f"Transform tradebook received type: {type(tradebook_data)}")

    # Handle empty input
    if not tradebook_data:
        logger.warning("Tradebook data is empty")
        return []

    # Log first trade for debugging
    if isinstance(tradebook_data, list) and tradebook_data:
        logger.info(f"Sample trade to transform: {json.dumps(tradebook_data[0], indent=2)[:500]}")

    transformed_data = []
    for trade in tradebook_data:
        # Get values with fallbacks for different field naming conventions
        broker_symbol = trade.get(
            "tradingSymbol", trade.get("tradingsymbol", trade.get("symbol", ""))
        )
        exchange = trade.get("exchangeSegment", trade.get("exchange", "NSE"))
        segment = trade.get("segment", "")

        # Determine proper exchange based on segment and symbol pattern
        if segment == "FNO" or any(marker in broker_symbol for marker in ["CE", "PE", "FUT"]):
            exchange = "NFO"
        else:
            exchange = "NSE"

        # Try to get token from trade data if available
        token = trade.get("token", trade.get("instrument_token", None))
        symbol = broker_symbol

        # Try to get OpenAlgo symbol from database
        try:
            from database.token_db import get_oa_symbol

            # Try to get the OpenAlgo symbol using the token if available
            if token:
                openalgo_symbol = get_oa_symbol(token, exchange)
                if openalgo_symbol:
                    symbol = openalgo_symbol
                    logger.info(f"Found OpenAlgo symbol by token: {broker_symbol} -> {symbol}")

            # If token lookup failed or token wasn't available, try by broker symbol
            elif broker_symbol:
                # For options/futures specifically, try database lookup
                if exchange == "NFO" and (
                    broker_symbol.endswith("CE")
                    or broker_symbol.endswith("PE")
                    or "FUT" in broker_symbol
                ):
                    # Query the database to find the OpenAlgo symbol for this broker symbol
                    from broker.groww.database.master_contract_db import SymToken, db_session

                    with db_session() as session:
                        record = (
                            session.query(SymToken)
                            .filter(
                                SymToken.brsymbol == broker_symbol, SymToken.exchange == exchange
                            )
                            .first()
                        )

                        if record and record.symbol:
                            symbol = record.symbol
                            logger.info(
                                f"Found OpenAlgo symbol in database: {broker_symbol} -> {symbol}"
                            )
        except Exception as e:
            logger.error(f"Error looking up OpenAlgo symbol from database: {e}")

        # Get other trade fields
        product = trade.get("productType", trade.get("product", ""))
        action = trade.get("transactionType", trade.get("transaction_type", ""))
        quantity = float(trade.get("tradedQuantity", trade.get("quantity", 0)))
        price = float(trade.get("tradedPrice", trade.get("price", 0.0)))
        orderid = trade.get("orderId", trade.get("order_id", ""))
        timestamp = trade.get(
            "updateTime", trade.get("timestamp", trade.get("trade_date_time", ""))
        )
        tradeid = trade.get("tradeId", trade.get("trade_id", ""))

        # Calculate trade value
        trade_value = quantity * price

        # Create the transformed trade object
        transformed_trade = {
            "symbol": symbol,
            "exchange": exchange,
            "product": product,
            "action": action,
            "quantity": quantity,
            "average_price": price,
            "trade_price": price,
            "trade_value": trade_value,
            "orderid": orderid,
            "timestamp": timestamp,
            "tradeid": tradeid,
        }
        transformed_data.append(transformed_trade)

    logger.info(f"Transformed {len(transformed_data)} trades successfully")
    return transformed_data
    # def transform_tradebook_data(tradebook_data):
    logger.info(f"Transform tradebook received type: {type(tradebook_data)}")

    # Handle empty input
    if not tradebook_data:
        logger.warning("Tradebook data is empty")
        return []

    # Log first trade for debugging
    if isinstance(tradebook_data, list) and tradebook_data:
        logger.info(f"Sample trade to transform: {json.dumps(tradebook_data[0], indent=2)[:500]}")

    transformed_data = []
    for trade in tradebook_data:
        # Get values with fallbacks for different field naming conventions
        symbol = trade.get("tradingSymbol", trade.get("symbol", ""))
        exchange = trade.get("exchangeSegment", trade.get("exchange", ""))
        product = trade.get("productType", trade.get("product", ""))
        action = trade.get("transactionType", trade.get("transaction_type", ""))
        quantity = trade.get("tradedQuantity", trade.get("quantity", 0))
        price = trade.get("tradedPrice", trade.get("price", 0.0))
        orderid = trade.get("orderId", trade.get("order_id", ""))
        timestamp = trade.get(
            "updateTime", trade.get("timestamp", trade.get("trade_date_time", ""))
        )
        tradeid = trade.get("tradeId", trade.get("trade_id", ""))

        # Calculate trade value
        trade_value = quantity * price

        # Create the transformed trade object
        transformed_trade = {
            "symbol": symbol,
            "exchange": exchange,
            "product": product,
            "action": action,
            "quantity": quantity,
            "average_price": price,
            "trade_price": price,  # Added for consistency
            "trade_value": trade_value,
            "orderid": orderid,
            "timestamp": timestamp,
            "tradeid": tradeid,  # Added for reference
        }
        transformed_data.append(transformed_trade)

    logger.info(f"Transformed {len(transformed_data)} trades successfully")
    return transformed_data


def map_position_data(position_data):
    logger.info(f"Map position data received type: {type(position_data)}")

    # If it's a tuple with status code (from direct API), extract the data
    if isinstance(position_data, tuple) and len(position_data) == 2:
        position_data = position_data[0]
        logger.info("Extracted position data from tuple")

    # Handle direct list of positions
    if isinstance(position_data, list):
        logger.info(f"Received direct list of {len(position_data)} positions")
        return position_data

    # Handle dictionary formats
    if isinstance(position_data, dict):
        # Log keys for debugging
        logger.info(f"Position data dict keys: {list(position_data.keys())}")

        # Check for data field
        if "data" in position_data and isinstance(position_data["data"], list):
            logger.info(f"Using 'data' field with {len(position_data['data'])} positions")
            return position_data["data"]

    # If all else fails, try the regular order mapping (fallback)
    logger.info("Falling back to regular order mapping")
    return map_order_data(position_data)


def transform_positions_data(positions_data):
    logger.info(
        f"Transform positions received type: {type(positions_data)}, length: {len(positions_data) if isinstance(positions_data, list) else 'not a list'}"
    )

    # Handle empty input
    if not positions_data:
        logger.warning("Positions data is empty")
        return []

    # Log first position for debugging
    if isinstance(positions_data, list) and positions_data:
        logger.info(
            f"Sample position to transform: {json.dumps(positions_data[0], indent=2)[:500]}"
        )

    transformed_data = []
    for position in positions_data:
        # Get tradingsymbol with fallbacks
        # Make sure we explicitly check for the trading_symbol field which is in the Groww API response
        trading_symbol = position.get("trading_symbol", "")
        broker_symbol = position.get("tradingsymbol", trading_symbol)
        if not broker_symbol:
            broker_symbol = position.get("symbol", "")

        # Ensure broker_symbol is a string, not None
        broker_symbol = str(broker_symbol) if broker_symbol is not None else ""
        exchange = position.get("exchange", "NSE")
        segment = position.get("segment", "")

        # For debugging
        logger.info(
            f"Processing position with trading_symbol: {trading_symbol}, broker_symbol: {broker_symbol}, segment: {segment}"
        )

        # Determine proper exchange based on segment and symbol pattern
        if segment == "FNO" or (
            broker_symbol and any(marker in broker_symbol for marker in ["CE", "PE", "FUT"])
        ):
            exchange = "NFO"
        else:
            exchange = "NSE"

        # Try to get token from position data if available
        token = position.get("token", position.get("instrument_token", None))

        # For cash segment, use the trading_symbol directly
        if segment == "CASH" or exchange == "NSE":
            symbol = broker_symbol
            # Ensure we have a trading symbol for cash segment
            if not symbol and "trading_symbol" in position:
                symbol = position["trading_symbol"]
        else:
            symbol = broker_symbol

        # Try to get OpenAlgo symbol from database
        try:
            from database.token_db import get_oa_symbol

            # Try to get the OpenAlgo symbol using the token if available
            if token:
                openalgo_symbol = get_oa_symbol(token, exchange)
                if openalgo_symbol:
                    symbol = openalgo_symbol
                    logger.info(f"Found OpenAlgo symbol by token: {broker_symbol} -> {symbol}")

            # If token lookup failed or token wasn't available, try by broker symbol
            elif broker_symbol:
                # For options/futures specifically, try database lookup
                if exchange == "NFO" and (
                    broker_symbol.endswith("CE")
                    or broker_symbol.endswith("PE")
                    or "FUT" in broker_symbol
                ):
                    # Query the database to find the OpenAlgo symbol for this broker symbol
                    from broker.groww.database.master_contract_db import SymToken, db_session

                    with db_session() as session:
                        record = (
                            session.query(SymToken)
                            .filter(
                                SymToken.brsymbol == broker_symbol, SymToken.exchange == exchange
                            )
                            .first()
                        )

                        if record and record.symbol:
                            symbol = record.symbol
                            logger.info(
                                f"Found OpenAlgo symbol in database: {broker_symbol} -> {symbol}"
                            )
        except Exception as e:
            logger.error(f"Error looking up OpenAlgo symbol from database: {e}")

        # Continue with the rest of your transformation
        quantity = float(position.get("quantity", 0))
        sell_qty = float(position.get("sellQty", 0))
        buy_qty = float(position.get("buyQty", 0))
        avg_price = float(position.get("avgPrice", 0))
        close_price = float(position.get("closePrice", 0))
        last_price = float(position.get("lastPrice", 0))
        pnl = float(position.get("pnl", 0))
        multiplier = float(position.get("multiplier", 1))
        unrealised = float(position.get("unrealised", 0))
        realised = float(position.get("realised", 0))

        transformed_position = {
            "symbol": symbol,
            "exchange": exchange,
            "product": position.get("product", "CNC"),
            "quantity": quantity,
            "average_price": avg_price,
            "close_price": close_price,
            "last_price": last_price,
            "pnl": pnl,
            "multiplier": multiplier,
            "unrealised": unrealised,
            "realised": realised,
            "buy_quantity": buy_qty,
            "sell_quantity": sell_qty,
            "instrument_token": position.get("instrument_token", position.get("symbol_isin", "")),
        }
        transformed_data.append(transformed_position)

    logger.info(f"Transformed {len(transformed_data)} positions successfully")
    return transformed_data


def transform_holdings_data(holdings_data):
    """
    Transform holdings data from Groww API

    Args:
        holdings_data: Can be a list of holdings or a tuple (holdings_list, metadata)

    Returns:
        List of transformed holdings
    """

    # Handle dictionary input with nested holdings
    if isinstance(holdings_data, dict) and "data" in holdings_data:
        holdings_data = holdings_data["data"].get("holdings", [])

    # Handle tuple input (holdings list, metadata)
    if isinstance(holdings_data, tuple):
        holdings_data = holdings_data[0]  # Take the first element (holdings list)

    # Validate input
    if not isinstance(holdings_data, list):
        logger.error(f"Invalid holdings data format: {type(holdings_data)}")
        return []

    transformed_data = []
    for holdings in holdings_data:
        # Extract symbol from trading symbol
        symbol = holdings.get("symbol", "")
        if not symbol and "trading_symbol" in holdings:
            # Try to extract symbol from trading symbol
            symbol = holdings["trading_symbol"].replace("NSE:", "").replace("BSE:", "")

        transformed_position = {
            "symbol": symbol,
            "exchange": holdings.get("exchange", "NSE"),  # Default to NSE
            "quantity": float(holdings.get("quantity", holdings.get("totalQty", 0))),
            "average_price": float(holdings.get("average_price", holdings.get("avgPrice", 0))),
            "product": holdings.get("product", "CNC"),
            "pnl": float(holdings.get("pnl", 0)),
            "pnlpercent": float(holdings.get("pnlpercent", 0)),
        }
        transformed_data.append(transformed_position)

    return transformed_data


def map_portfolio_data(portfolio_data):
    """
    Processes and modifies a list of Portfolio dictionaries based on specific conditions.

    Parameters:
    - portfolio_data: A list of dictionaries, where each dictionary represents an portfolio information.

    Returns:
    - The modified portfolio_data with  'product' fields.
    """
    # Check if 'portfolio_data' is empty
    if (
        portfolio_data is None
        or isinstance(portfolio_data, dict)
        and (
            portfolio_data.get("errorCode") == "DHOLDING_ERROR"
            or portfolio_data.get("internalErrorCode") == "DH-1111"
            or portfolio_data.get("internalErrorMessage") == "No holdings available"
        )
    ):
        # Handle the case where there is no data or specific error message about no holdings
        logger.info("No data or no holdings available.")
        portfolio_data = {}  # This resets portfolio_data to an empty dictionary if conditions are met

    return portfolio_data


def calculate_portfolio_statistics(holdings_data):
    """
    Calculate portfolio statistics from Groww API holdings data

    Parameters:
    - holdings_data: Holdings data from Groww API

    Returns:
    - Dictionary with portfolio statistics
    """
    # Logging for debugging
    logger.info(f"Input holdings data type: {type(holdings_data)}")
    logger.info(f"Input holdings data: {holdings_data}")

    # Check if holdings_data is empty or None
    if not holdings_data:
        return {
            "totalholdingvalue": 0,
            "totalinvvalue": 0,
            "totalpnlpercentage": 0,
            "totalprofitandloss": 0,
        }

    # Extract holdings from the API response structure
    if isinstance(holdings_data, dict):
        # Check if statistics are already provided
        if "data" in holdings_data and "statistics" in holdings_data["data"]:
            return holdings_data["data"]["statistics"]

        if "payload" in holdings_data:
            holdings_data = holdings_data["payload"].get("holdings", [])
        elif "data" in holdings_data and "holdings" in holdings_data["data"]:
            holdings_data = holdings_data["data"]["holdings"]

    # Validate holdings data
    if not isinstance(holdings_data, list):
        logger.error(f"Invalid holdings data format: {type(holdings_data)}")
        return {
            "totalholdingvalue": 0,
            "totalinvvalue": 0,
            "totalpnlpercentage": 0,
            "totalprofitandloss": 0,
        }

    # Calculate total holding value
    totalholdingvalue = 0
    totalinvvalue = 0
    totalprofitandloss = 0

    for holding in holdings_data:
        # Handle different possible key variations
        quantity = float(holding.get("quantity", holding.get("qty", 0)))
        avg_price = float(holding.get("average_price", holding.get("avgPrice", 0)))

        # Calculate holding value
        holding_value = quantity * avg_price
        totalholdingvalue += holding_value
        totalinvvalue += holding_value

        # Use provided PnL if available
        pnl = float(holding.get("pnl", 0))
        totalprofitandloss += pnl

    # Calculate PnL percentage
    totalpnlpercentage = (totalprofitandloss / totalinvvalue * 100) if totalinvvalue else 0

    # Prepare and return statistics
    return {
        "totalholdingvalue": round(totalholdingvalue, 2),
        "totalinvvalue": round(totalinvvalue, 2),
        "totalpnlpercentage": round(totalpnlpercentage, 2),
        "totalprofitandloss": round(totalprofitandloss, 2),
    }

```


---

# FILE: broker\groww\mapping\transform_data.py

```py
# Mapping OpenAlgo API Request https://openalgo.in/docs
# Mapping Groww API Parameters based on SDK documentation

# Groww API constants based on the SDK documentation

# Validity types
VALIDITY_DAY = "DAY"
VALIDITY_IOC = "IOC"

# Exchange types
EXCHANGE_NSE = "NSE"
EXCHANGE_BSE = "BSE"

# Segment types
SEGMENT_CASH = "CASH"
SEGMENT_FNO = "FNO"


# Product types
PRODUCT_CNC = "CNC"
PRODUCT_MIS = "MIS"
PRODUCT_NRML = "NRML"

# Order types
ORDER_TYPE_MARKET = "MARKET"
ORDER_TYPE_LIMIT = "LIMIT"
ORDER_TYPE_SL = "STOP_LOSS_LIMIT"
ORDER_TYPE_SLM = "STOP_LOSS_MARKET"

# Transaction types
TRANSACTION_TYPE_BUY = "BUY"
TRANSACTION_TYPE_SELL = "SELL"

# Order status
ORDER_STATUS_NEW = "NEW"
ORDER_STATUS_ACKED = "ACKED"
ORDER_STATUS_TRIGGER_PENDING = "TRIGGER_PENDING"
ORDER_STATUS_APPROVED = "APPROVED"
ORDER_STATUS_FAILED = "FAILED"
ORDER_STATUS_EXECUTED = "EXECUTED"
ORDER_STATUS_DELIVERY_AWAITED = "DELIVERY_AWAITED"
ORDER_STATUS_CANCELLED = "CANCELLED"
ORDER_STATUS_CANCELLATION_REQUESTED = "CANCELLATION_REQUESTED"
ORDER_STATUS_MODIFICATION_REQUESTED = "MODIFICATION_REQUESTED"
ORDER_STATUS_COMPLETED = "COMPLETED"
ORDER_STATUS_REJECTED = "REJECTED"


def transform_data(data, token):
    """
    Transforms the OpenAlgo API request structure to Groww API structure.

    Parameters required by Groww:
    - trading_symbol (required): string - Trading Symbol of the instrument as defined by the exchange
    - quantity (required): int - Quantity of stocks to order
    - price: float - Price of the stock in rupees case of Limit order
    - trigger_price: float - Trigger price in rupees for the order
    - validity (required): string - Validity of the order
    - exchange (required): string - Stock exchange
    - segment (required): string - Segment
    - product (required): string - Product type
    - order_type (required): string - Enumeration of order types
    - transaction_type (required): string - Type of the trade
    - order_reference_id: string - User provided 8 digit reference id
    """
    # Get the symbol (may need to use broker format if the token mapping is used)
    trading_symbol = data.get("symbol", "")

    # Basic mapping to Groww API format
    transformed = {
        "trading_symbol": trading_symbol,
        "quantity": int(data["quantity"]),
        "validity": map_validity(data.get("validity", "DAY")),
        "exchange": map_exchange_type(data["exchange"]),
        "segment": map_segment_type(data["exchange"]),
        "product": map_product_type(data["product"]),
        "order_type": map_order_type(data["pricetype"]),
        "transaction_type": map_transaction_type(data["action"]),
    }

    # Add price for LIMIT orders
    if data["pricetype"] == "LIMIT":
        transformed["price"] = float(data.get("price", 0))

    # Add trigger price for SL and SL-M orders
    if data["pricetype"] in ["SL", "SL-M"]:
        trigger_price = float(data.get("trigger_price", 0))
        if trigger_price <= 0:
            raise ValueError("Trigger price is required for Stop Loss orders")
        transformed["trigger_price"] = trigger_price

    # Add order reference id if provided
    if data.get("order_reference_id"):
        transformed["order_reference_id"] = data["order_reference_id"]
    elif data.get("strategy"):
        # Use strategy as reference ID if provided, truncating to 8 chars if needed
        reference_id = data["strategy"][:8].ljust(8, "0")
        transformed["order_reference_id"] = reference_id

    return transformed


def transform_modify_order_data(data):
    """
    Transforms the OpenAlgo order modification data to Groww API structure

    Args:
        data (dict): Order data in OpenAlgo format

    Returns:
        dict: Order data in Groww format
    """
    # Create modification payload
    transformed = {}

    # Add fields that can be modified
    if "quantity" in data:
        transformed["quantity"] = int(data["quantity"])

    if "pricetype" in data:
        transformed["order_type"] = map_order_type(data["pricetype"])

    if "price" in data and data.get("pricetype", "").upper() == "LIMIT":
        transformed["price"] = float(data["price"])

    if "trigger_price" in data and data.get("pricetype", "").upper() in ["SL", "SL-M"]:
        transformed["trigger_price"] = float(data["trigger_price"])

    if "validity" in data:
        transformed["validity"] = map_validity(data["validity"])

    # Order reference ID if present
    if "order_reference_id" in data:
        transformed["order_reference_id"] = data["order_reference_id"]

    return transformed


def map_order_type(pricetype):
    """
    Maps the OpenAlgo pricetype to Groww order_type values.
    """
    order_type_mapping = {
        "MARKET": ORDER_TYPE_MARKET,
        "LIMIT": ORDER_TYPE_LIMIT,
        "SL": ORDER_TYPE_SL,
        "SL-M": ORDER_TYPE_SLM,
    }
    return order_type_mapping.get(
        pricetype.upper(), ORDER_TYPE_MARKET
    )  # Default to MARKET if not found


def map_exchange_type(exchange):
    """
    Maps the OpenAlgo Exchange to Groww Exchange values.
    """
    exchange_mapping = {
        "NSE": EXCHANGE_NSE,
        "BSE": EXCHANGE_BSE,
        "NFO": EXCHANGE_NSE,  # NFO is part of NSE for Groww
        "BFO": EXCHANGE_BSE,  # BSE futures & options
    }
    return exchange_mapping.get(exchange.upper(), EXCHANGE_NSE)  # Default to NSE if not found


def map_exchange(brexchange):
    """
    Maps the Groww Exchange to OpenAlgo Exchange format.
    """
    exchange_mapping = {
        EXCHANGE_NSE: "NSE",
        EXCHANGE_BSE: "BSE",
        "NSE_FNO": "NFO",
        "BSE_FNO": "BFO",
    }
    return exchange_mapping.get(brexchange, "NSE")  # Default to NSE if not found


def map_product_type(product):
    """
    Maps the OpenAlgo product type to Groww product type.
    """
    product_type_mapping = {
        "CNC": PRODUCT_CNC,  # Cash and Carry
        "NRML": PRODUCT_NRML,  # Normal delivery
        "MIS": PRODUCT_MIS,  # Intraday
    }
    return product_type_mapping.get(product.upper(), PRODUCT_CNC)  # Default to CNC if not found


def reverse_map_product_type(product):
    """
    Maps the Groww product type to the OpenAlgo product type.
    """
    product_mapping = {PRODUCT_CNC: "CNC", PRODUCT_NRML: "NRML", PRODUCT_MIS: "MIS"}
    return product_mapping.get(product)  # Return None if not found


def get_segment(exchange):
    """
    Map exchange to segment type for Groww
    """
    segment_mapping = {
        "NSE": SEGMENT_CASH,
        "BSE": SEGMENT_CASH,
        "NFO": SEGMENT_FNO,
        "BFO": SEGMENT_FNO,
    }
    return segment_mapping.get(exchange.upper(), SEGMENT_CASH)  # Default to CASH if not found


def map_segment_type(exchange):
    """
    Maps the OpenAlgo exchange to Groww segment type.
    """
    segment_mapping = {
        "NSE": SEGMENT_CASH,
        "BSE": SEGMENT_CASH,
        "NFO": SEGMENT_FNO,
        "BFO": SEGMENT_FNO,
    }
    return segment_mapping.get(exchange.upper(), SEGMENT_CASH)  # Default to CASH if not found


def map_validity(validity):
    """
    Maps OpenAlgo validity to Groww validity type.
    """
    validity_mapping = {
        "DAY": VALIDITY_DAY,
        "IOC": VALIDITY_IOC,
        "GTC": VALIDITY_DAY,  # Groww doesn't support GTC, defaulting to DAY
    }
    return validity_mapping.get(validity.upper(), VALIDITY_DAY)  # Default to DAY if not found


def map_transaction_type(action):
    """
    Maps OpenAlgo action to Groww transaction_type.
    """
    transaction_type_mapping = {"BUY": TRANSACTION_TYPE_BUY, "SELL": TRANSACTION_TYPE_SELL}
    return transaction_type_mapping.get(
        action.upper(), TRANSACTION_TYPE_BUY
    )  # Default to BUY if not found

```
