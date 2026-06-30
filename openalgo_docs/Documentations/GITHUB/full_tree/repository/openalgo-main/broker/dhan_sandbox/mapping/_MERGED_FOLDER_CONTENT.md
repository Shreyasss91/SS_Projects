# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\dhan_sandbox\mapping



---

# FILE: broker\dhan_sandbox\mapping\margin_data.py

```py
# Mapping OpenAlgo API Request https://openalgo.in/docs
# Mapping Dhan Sandbox Margin API https://dhanhq.co/docs/v2/funds/

from broker.dhan_sandbox.mapping.transform_data import (
    map_exchange_type,
    map_order_type,
    map_product_type,
)
from database.token_db import get_token
from utils.logging import get_logger

logger = get_logger(__name__)


def transform_margin_position(position, client_id):
    """
    Transform a single OpenAlgo margin position to Dhan Sandbox margin format.

    Note: Dhan Sandbox margin calculator API accepts only one order at a time, not a batch.

    Args:
        position: Position in OpenAlgo format
        client_id: Dhan client ID

    Returns:
        Dict in Dhan Sandbox margin format or None if transformation fails
    """
    try:
        # Get the token for the symbol
        token = get_token(position["symbol"], position["exchange"])

        if not token:
            logger.warning(
                f"Token not found for symbol: {position['symbol']} on exchange: {position['exchange']}"
            )
            return None

        # Map exchange segment
        exchange_segment = map_exchange_type(position["exchange"])
        if not exchange_segment:
            logger.warning(f"Invalid exchange: {position['exchange']}")
            return None

        # Transform the position
        transformed = {
            "dhanClientId": client_id,
            "exchangeSegment": exchange_segment,
            "transactionType": position["action"].upper(),
            "quantity": int(position["quantity"]),
            "productType": map_product_type_for_margin(position["product"]),
            "securityId": str(token),
            "price": float(position.get("price", 0)),
        }

        # Add trigger price if present
        trigger_price = position.get("trigger_price", 0)
        if trigger_price and float(trigger_price) > 0:
            transformed["triggerPrice"] = float(trigger_price)

        return transformed

    except Exception as e:
        logger.error(f"Error transforming position: {position}, Error: {e}")
        return None


def map_product_type_for_margin(product):
    """
    Maps OpenAlgo product type to Dhan Sandbox product type for margin calculation.

    OpenAlgo: CNC, NRML, MIS
    Dhan Sandbox: CNC, MARGIN, INTRADAY, MTF, CO, BO
    """
    product_type_mapping = {
        "CNC": "CNC",
        "NRML": "MARGIN",
        "MIS": "INTRADAY",
    }
    return product_type_mapping.get(product, "INTRADAY")


def parse_margin_response(response_data):
    """
    Parse Dhan Sandbox margin response to OpenAlgo standard format.

    Args:
        response_data: Raw response from Dhan Sandbox API

    Returns:
        Standardized margin response
    """
    try:
        if not response_data or not isinstance(response_data, dict):
            return {"status": "error", "message": "Invalid response from broker"}

        # Check for error response
        if response_data.get("errorType") or response_data.get("status") == "failed":
            error_message = response_data.get("errorMessage", "Failed to calculate margin")
            return {"status": "error", "message": error_message}

        total_margin = response_data.get("totalMargin", 0)
        span_margin = response_data.get("spanMargin", 0)
        exposure_margin = response_data.get("exposureMargin", 0)

        # Return standardized format with OpenAlgo-compatible aliases.
        return {
            "status": "success",
            "data": {
                "total_margin_required": total_margin,
                "total_margin": total_margin,
                "span_margin": span_margin,
                "exposure_margin": exposure_margin,
                "margin_benefit": 0,
                "positions": response_data.get("positions", []),
                "available_balance": response_data.get("availableBalance", 0),
                "variable_margin": response_data.get("variableMargin", 0),
                "insufficient_balance": response_data.get("insufficientBalance", 0),
                "brokerage": response_data.get("brokerage", 0),
                "leverage": response_data.get("leverage", "1.00"),
                "raw_response": response_data,  # Include raw response for debugging
            },
        }

    except Exception as e:
        logger.error(f"Error parsing margin response: {e}")
        return {"status": "error", "message": f"Failed to parse margin response: {str(e)}"}


def parse_multi_margin_response(response_data):
    """
    Parse Dhan Sandbox /v2/margincalculator/multi response to OpenAlgo standard format.

    Response structure:
    {
        "total_margin": "150000.00",
        "span_margin": "50000.00",
        "exposure_margin": "30000.00",
        "equity_margin": "70000.00",
        "fo_margin": "0.00",
        "commodity_margin": "0.00",
        "currency": "INR",
        "hedge_benefit": ""
    }

    Args:
        response_data: Raw response from Dhan Sandbox multi-margin API

    Returns:
        Standardized margin response
    """
    try:
        if not response_data or not isinstance(response_data, dict):
            return {"status": "error", "message": "Invalid response from broker"}

        # Check for error response
        if response_data.get("errorType") or response_data.get("status") == "failed":
            error_message = response_data.get("errorMessage", "Failed to calculate margin")
            return {"status": "error", "message": error_message}

        # Parse multi-margin response fields
        total_margin = response_data.get("total_margin", "0")
        span_margin = response_data.get("span_margin", "0")
        exposure_margin = response_data.get("exposure_margin", "0")

        # Return standardized format with multi-margin specific fields
        return {
            "status": "success",
            "data": {
                "total_margin_required": float(total_margin) if total_margin else 0,
                "total_margin": float(total_margin) if total_margin else 0,
                "span_margin": float(span_margin) if span_margin else 0,
                "exposure_margin": float(exposure_margin) if exposure_margin else 0,
                "margin_benefit": float(response_data.get("hedge_benefit", "0") or "0"),
                "positions": response_data.get("positions", []),
                "equity_margin": float(response_data.get("equity_margin", "0") or "0"),
                "fo_margin": float(response_data.get("fo_margin", "0") or "0"),
                "commodity_margin": float(response_data.get("commodity_margin", "0") or "0"),
                "currency": response_data.get("currency", "INR"),
                "hedge_benefit": response_data.get("hedge_benefit", ""),
                "raw_response": response_data,
            },
        }

    except Exception as e:
        logger.error(f"Error parsing multi-margin response: {e}")
        return {"status": "error", "message": f"Failed to parse multi-margin response: {str(e)}"}


def parse_batch_margin_response(responses):
    """
    Parse multiple Dhan Sandbox margin responses and aggregate them.

    Args:
        responses: List of individual margin responses

    Returns:
        Aggregated margin response
    """
    try:
        total_margin = 0
        total_span = 0
        total_exposure = 0
        total_brokerage = 0
        available_balance = 0
        insufficient_balance = 0
        all_responses = []

        for response in responses:
            if response.get("status") == "success":
                data = response.get("data", {})
                total_margin += data.get("total_margin_required", 0)
                total_span += data.get("span_margin", 0)
                total_exposure += data.get("exposure_margin", 0)
                total_brokerage += data.get("brokerage", 0)
                # Take the max available balance (it should be same for all)
                available_balance = max(available_balance, data.get("available_balance", 0))
                all_responses.append(data.get("raw_response", {}))

        # Calculate total insufficient balance
        insufficient_balance = max(0, total_margin - available_balance)

        return {
            "status": "success",
            "data": {
                "total_margin_required": total_margin,
                "total_margin": total_margin,
                "span_margin": total_span,
                "exposure_margin": total_exposure,
                "margin_benefit": 0,
                "positions": [],
                "available_balance": available_balance,
                "total_brokerage": total_brokerage,
                "insufficient_balance": insufficient_balance,
                "total_positions": len(responses),
                "individual_margins": all_responses,
            },
        }

    except Exception as e:
        logger.error(f"Error parsing batch margin response: {e}")
        return {"status": "error", "message": f"Failed to parse batch margin response: {str(e)}"}

```


---

# FILE: broker\dhan_sandbox\mapping\order_data.py

```py
import json
from datetime import datetime, timedelta, timezone

from broker.dhan_sandbox.mapping.transform_data import map_exchange
from database.token_db import get_symbol
from utils.logging import get_logger

logger = get_logger(__name__)

# IST is UTC+5:30
_IST = timezone(timedelta(hours=5, minutes=30))
_UTC = timezone.utc


def _utc_to_ist(timestamp_str):
    """Convert a UTC timestamp string from Dhan sandbox API to IST.
    Dhan sandbox returns updateTime in UTC without timezone info.
    """
    if not timestamp_str:
        return timestamp_str
    try:
        # Parse the timestamp (format: '2026-02-19 03:44:27')
        dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        # Treat it as UTC, then convert to IST
        dt_utc = dt.replace(tzinfo=_UTC)
        dt_ist = dt_utc.astimezone(_IST)
        # Return in the same format without timezone suffix (frontend handles display)
        return dt_ist.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError) as e:
        logger.debug(f"Could not convert timestamp '{timestamp_str}': {e}")
        return timestamp_str


def map_order_data(order_data):
    """
    Processes and modifies a list of order dictionaries based on specific conditions.

    Parameters:
    - order_data: A list of dictionaries, where each dictionary represents an order.

    Returns:
    - The modified order_data with updated 'tradingsymbol' and 'product' fields.
    """
    # Handle error responses from the API (e.g., after-hours errors, auth errors)
    if isinstance(order_data, dict) and (order_data.get("errorType") or order_data.get("status") in ("error", "failed")):
        logger.info(f"API returned error, no order data to map: {order_data.get('errorType', order_data.get('status', 'unknown'))}")
        return []

    # Check if 'data' is None
    if order_data is None:
        # Handle the case where there is no data
        # For example, you might want to display a message to the user
        # or pass an empty list or dictionary to the template.
        logger.info("No data available.")
        order_data = {}  # or set it to an empty list if it's supposed to be a list
    else:
        order_data = order_data

    if order_data:
        for order in order_data:
            # Extract the instrument_token and exchange for the current order
            instrument_token = order["securityId"]
            exchange = map_exchange(order["exchangeSegment"])
            order["exchangeSegment"] = exchange

            # Use the get_symbol function to fetch the symbol from the database
            symbol_from_db = get_symbol(instrument_token, exchange)

            # Check if a symbol was found; if so, update the trading_symbol in the current order
            if symbol_from_db:
                order["tradingSymbol"] = symbol_from_db
                if (
                    order["exchangeSegment"] == "NSE" or order["exchangeSegment"] == "BSE"
                ) and order["productType"] == "CNC":
                    order["productType"] = "CNC"

                elif order["productType"] == "INTRADAY":
                    order["productType"] = "MIS"

                elif (
                    order["exchangeSegment"] in ["NFO", "MCX", "BFO", "CDS"]
                    and order["productType"] == "MARGIN"
                ):
                    order["productType"] = "NRML"
            else:
                logger.warning(
                    f"Symbol not found for token {instrument_token} and exchange {exchange}. Keeping original trading symbol."
                )

    return order_data


def calculate_order_statistics(order_data):
    """
    Calculates statistics from order data, including totals for buy orders, sell orders,
    completed orders, open orders, and rejected orders.

    Parameters:
    - order_data: A list of dictionaries, where each dictionary represents an order.

    Returns:
    - A dictionary containing counts of different types of orders.
    """
    # Initialize counters
    total_buy_orders = total_sell_orders = 0
    total_completed_orders = total_open_orders = total_rejected_orders = 0

    if order_data:
        for order in order_data:
            # Count buy and sell orders
            if order["transactionType"] == "BUY":
                total_buy_orders += 1
            elif order["transactionType"] == "SELL":
                total_sell_orders += 1

            # Count orders based on their status
            if order["orderStatus"] == "TRADED":
                total_completed_orders += 1
                order["orderStatus"] = "complete"
            elif order["orderStatus"] == "PENDING":
                total_open_orders += 1
                order["orderStatus"] = "open"
            elif order["orderStatus"] == "REJECTED":
                total_rejected_orders += 1
                order["orderStatus"] = "rejected"
            elif order["orderStatus"] == "CANCELLED":
                order["orderStatus"] = "cancelled"
            elif order["orderStatus"] == "TRANSIT":
                total_open_orders += 1
                order["orderStatus"] = "open"
            elif order["orderStatus"] == "PART_TRADED":
                total_open_orders += 1
                order["orderStatus"] = "open"
            elif order["orderStatus"] == "EXPIRED":
                order["orderStatus"] = "cancelled"

    # Compile and return the statistics
    return {
        "total_buy_orders": total_buy_orders,
        "total_sell_orders": total_sell_orders,
        "total_completed_orders": total_completed_orders,
        "total_open_orders": total_open_orders,
        "total_rejected_orders": total_rejected_orders,
    }


def transform_order_data(orders):
    # Directly handling a dictionary assuming it's the structure we expect
    if isinstance(orders, dict):
        # Convert the single dictionary into a list of one dictionary
        orders = [orders]

    transformed_orders = []

    for order in orders:
        # Make sure each item is indeed a dictionary
        if not isinstance(order, dict):
            logger.warning(
                f"Warning: Expected a dict, but found a {type(order)}. Skipping this item."
            )
            continue

        if order["orderType"] == "MARKET":
            order["orderType"] = "MARKET"
        if order["orderType"] == "LIMIT":
            order["orderType"] = "LIMIT"
        if order["orderType"] == "STOP_LOSS":
            order["orderType"] = "SL"
        if order["orderType"] == "STOP_LOSS_MARKET":
            order["orderType"] = "SL-M"

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
            "timestamp": _utc_to_ist(order.get("updateTime", "")),
        }

        transformed_orders.append(transformed_order)

    return transformed_orders


def map_trade_data(trade_data):
    return map_order_data(trade_data)


def transform_tradebook_data(tradebook_data):
    transformed_data = []
    for trade in tradebook_data:
        transformed_trade = {
            "symbol": trade.get("tradingSymbol", ""),
            "exchange": trade.get("exchangeSegment", ""),
            "product": trade.get("productType", ""),
            "action": trade.get("transactionType", ""),
            "quantity": trade.get("tradedQuantity", 0),
            "average_price": trade.get("tradedPrice", 0.0),
            "trade_value": trade.get("tradedQuantity", 0) * trade.get("tradedPrice", 0.0),
            "orderid": trade.get("orderId", ""),
            "timestamp": _utc_to_ist(trade.get("updateTime", "")),
        }
        transformed_data.append(transformed_trade)
    return transformed_data


def map_position_data(position_data):
    return map_order_data(position_data)


def transform_positions_data(positions_data):
    # Avoid fetching LTP using a globally decrypted API key from DB.
    # That pattern can leak cross-user data in multi-user setups.
    transformed_data = []
    for position in positions_data:
        realized_pnl = float(position.get("realizedProfit", 0))
        unrealized_pnl = float(position.get("unrealizedProfit", 0))
        symbol = position.get("tradingSymbol", "")
        exchange = position.get("exchangeSegment", "")

        # Use broker-provided LTP fields when available, then safe fallback.
        ltp = 0.0
        for candidate in (
            position.get("ltp"),
            position.get("lastTradedPrice"),
            position.get("lastPrice"),
            position.get("closePrice"),
        ):
            try:
                parsed = float(candidate)
            except (TypeError, ValueError):
                continue
            if parsed > 0:
                ltp = parsed
                break

        if ltp <= 0:
            try:
                ltp = float(position.get("costPrice", 0) or 0)
            except (TypeError, ValueError):
                ltp = 0.0

        transformed_position = {
            "symbol": symbol,
            "exchange": exchange,
            "product": position.get("productType", ""),
            "quantity": position.get("netQty", 0),
            "average_price": position.get("costPrice", 0.0),
            "ltp": round(ltp, 2),
            "pnl": round(realized_pnl + unrealized_pnl, 2),
        }
        transformed_data.append(transformed_position)
    return transformed_data


def transform_holdings_data(holdings_data):
    transformed_data = []
    for holdings in holdings_data:
        transformed_position = {
            "symbol": holdings.get("tradingSymbol", ""),
            "exchange": holdings.get("exchange", ""),
            "quantity": holdings.get("totalQty", 0),
            "product": "CNC",
            "pnl": 0.0,
            "pnlpercent": 0.0,
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
    totalholdingvalue = sum(item["avgCostPrice"] * item["totalQty"] for item in holdings_data)
    totalinvvalue = sum(item["avgCostPrice"] * item["totalQty"] for item in holdings_data)
    totalprofitandloss = 0

    # To avoid division by zero in the case when total_investment_value is 0
    totalpnlpercentage = (totalprofitandloss / totalinvvalue * 100) if totalinvvalue else 0

    return {
        "totalholdingvalue": totalholdingvalue,
        "totalinvvalue": totalinvvalue,
        "totalprofitandloss": totalprofitandloss,
        "totalpnlpercentage": totalpnlpercentage,
    }

```


---

# FILE: broker\dhan_sandbox\mapping\transform_data.py

```py
# Mapping OpenAlgo API Request https://openalgo.in/docs
# Mapping Upstox Broking Parameters https://dhanhq.co/docs/v2/orders/


def transform_data(data, token):
    """
    Transforms the OpenAlgo API request structure to Dhan v2 API structure.

    Parameters required by Dhan v2:
    - dhanClientId (required): string
    - correlationId: string
    - transactionType (required): BUY/SELL
    - exchangeSegment (required): Exchange segment enum
    - productType (required): Product type enum
    - orderType (required): Order type enum
    - validity (required): DAY/IOC
    - securityId (required): string
    - quantity (required): int
    - disclosedQuantity: int
    - price (required): float
    - triggerPrice: float (required for SL orders)
    - afterMarketOrder: boolean
    - amoTime: string (OPEN/OPEN_30/OPEN_60)
    - boProfitValue: float
    - boStopLossValue: float
    """
    # Basic mapping
    transformed = {
        "dhanClientId": data["apikey"],
        "transactionType": data["action"].upper(),
        "exchangeSegment": map_exchange_type(data["exchange"]),
        "productType": map_product_type(data["product"]),
        "orderType": map_order_type(data["pricetype"]),
        "validity": "DAY",  # Default to DAY, can be overridden if IOC is needed
        "securityId": token,
        "quantity": int(data["quantity"]),
        "disclosedQuantity": int(data.get("disclosed_quantity", 0)),
        "price": float(data.get("price", 0)),
        "triggerPrice": float(data.get("trigger_price", 0)),
        "afterMarketOrder": data.get("after_market_order", False),
    }

    # Add correlationId - Dhan API seems to require this field even if optional in docs
    correlation_id = data.get("correlation_id")
    if correlation_id is not None and correlation_id != "":
        transformed["correlationId"] = correlation_id
    else:
        # Use a default correlation ID if not provided
        import uuid

        transformed["correlationId"] = str(uuid.uuid4())[:8]  # Short UUID for tracking

    # Handle amoTime - required for after market orders, default for regular orders
    if data.get("after_market_order", False):
        amo_time = data.get("amo_time")
        if amo_time and amo_time in ["OPEN", "OPEN_30", "OPEN_60"]:
            transformed["amoTime"] = amo_time
        else:
            transformed["amoTime"] = "OPEN"  # Default for after market orders
    else:
        # Even for regular orders, Dhan API seems to require amoTime field
        transformed["amoTime"] = "OPEN"

    # Add bracket order fields only if they have valid values
    bo_profit = data.get("bo_profit_value")
    if bo_profit is not None and bo_profit != 0:
        transformed["boProfitValue"] = float(bo_profit)

    bo_stop_loss = data.get("bo_stop_loss_value")
    if bo_stop_loss is not None and bo_stop_loss != 0:
        transformed["boStopLossValue"] = float(bo_stop_loss)

    # Handle validity for IOC orders if specified
    if data.get("validity") == "IOC":
        transformed["validity"] = "IOC"

    # For SL and SL-M orders, trigger price is required
    if data["pricetype"] in ["SL", "SL-M"] and not transformed["triggerPrice"]:
        raise ValueError("Trigger price is required for Stop Loss orders")

    return transformed


def transform_modify_order_data(data):
    modified = {
        "dhanClientId": data["apikey"],
        "orderId": data["orderid"],
        "orderType": map_order_type(data["pricetype"]),
        "quantity": int(data["quantity"]),
        "validity": "DAY",
    }

    # Set price for non-market orders
    if data.get("pricetype") != "MARKET":
        modified["price"] = float(data["price"])

    # Set disclosed quantity if provided
    disclosed_qty = int(data.get("disclosed_quantity", 0))
    if disclosed_qty > 0:
        modified["disclosedQuantity"] = disclosed_qty

    # Handle trigger price for SL orders
    if data["pricetype"] in ["SL", "SL-M"]:
        trigger_price = float(data.get("trigger_price", 0))
        if trigger_price > 0:
            modified["triggerPrice"] = float(trigger_price)

    return modified


def map_order_type(pricetype):
    """
    Maps the new pricetype to the existing order type.
    """
    order_type_mapping = {
        "MARKET": "MARKET",
        "LIMIT": "LIMIT",
        "SL": "STOP_LOSS",
        "SL-M": "STOP_LOSS_MARKET",
    }
    return order_type_mapping.get(pricetype, "MARKET")  # Default to MARKET if not found


def map_exchange_type(exchange):
    """
    Maps the Broker Exchange to the OpenAlgo Exchange.
    """
    exchange_mapping = {
        "NSE": "NSE_EQ",
        "BSE": "BSE_EQ",
        "CDS": "NSE_CURRENCY",
        "NFO": "NSE_FNO",
        "BFO": "BSE_FNO",
        "BCD": "BSE_CURRENCY",
        "MCX": "MCX_COMM",
    }
    return exchange_mapping.get(exchange)  # Default to MARKET if not found


def map_exchange(brexchange):
    """
    Maps the Broker Exchange to the OpenAlgo Exchange.
    """
    exchange_mapping = {
        "NSE_EQ": "NSE",
        "BSE_EQ": "BSE",
        "NSE_CURRENCY": "CDS",
        "NSE_FNO": "NFO",
        "BSE_FNO": "BFO",
        "BSE_CURRENCY": "BCD",
        "MCX_COMM": "MCX",
    }
    return exchange_mapping.get(brexchange)  # Default to MARKET if not found


def map_product_type(product):
    """
    Maps the new product type to the existing product type.
    """
    product_type_mapping = {
        "CNC": "CNC",
        "NRML": "MARGIN",
        "MIS": "INTRADAY",
    }
    return product_type_mapping.get(product, "INTRADAY")  # Default to INTRADAY if not found


def reverse_map_product_type(product):
    """
    Reverse maps the broker product type to the OpenAlgo product type, considering the exchange.
    """
    # Exchange to OpenAlgo product type mapping for 'D'
    product_mapping = {"CNC": "CNC", "MARGIN": "NRML", "MIS": "INTRADAY"}

    return product_mapping.get(product)  # Removed default; will return None if not found

```
