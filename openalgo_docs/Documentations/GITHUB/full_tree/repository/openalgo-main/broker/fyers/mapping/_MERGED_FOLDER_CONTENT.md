# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\fyers\mapping



---

# FILE: broker\fyers\mapping\margin_data.py

```py
# Mapping OpenAlgo API Request https://openalgo.in/docs
# Mapping Fyers Margin API

from broker.fyers.mapping.transform_data import map_action, map_order_type, map_product_type
from database.token_db import get_br_symbol
from utils.logging import get_logger

logger = get_logger(__name__)


def transform_margin_positions(positions):
    """
    Transform OpenAlgo margin position format to Fyers margin format.

    OpenAlgo Format:
    {
        "symbol": "NIFTY",
        "exchange": "NSE",
        "action": "BUY",
        "quantity": 50,
        "pricetype": "MARKET",
        "product": "NRML",
        "price": 0,
        "trigger_price": 0
    }

    Fyers Format:
    {
        "symbol": "NSE:NIFTY23DECFUT",
        "qty": 50,
        "side": 1,  # 1=Buy, -1=Sell
        "type": 2,  # 1=Limit, 2=Market, 3=SL-M, 4=SL-L
        "productType": "MARGIN",
        "limitPrice": 0.0,
        "stopLoss": 0.0,
        "stopPrice": 0.0,
        "takeProfit": 0.0
    }

    Args:
        positions: List of positions in OpenAlgo format

    Returns:
        List of positions in Fyers format
    """
    transformed_positions = []
    skipped_positions = []

    for position in positions:
        try:
            symbol = position["symbol"]
            exchange = position["exchange"]

            # Get the broker symbol for Fyers
            br_symbol = get_br_symbol(symbol, exchange)

            # Validate symbol exists and is not None
            if not br_symbol or br_symbol is None or str(br_symbol).lower() == "none":
                logger.warning(f"Symbol not found for: {symbol} on exchange: {exchange}")
                skipped_positions.append(f"{symbol} ({exchange})")
                continue

            # Validate symbol is a valid string
            br_symbol_str = str(br_symbol).strip()
            if not br_symbol_str:
                logger.warning(
                    f"Invalid symbol format for {symbol} ({exchange}): '{br_symbol_str}'"
                )
                skipped_positions.append(f"{symbol} ({exchange}) - invalid symbol: {br_symbol_str}")
                continue

            # Transform the position
            transformed_position = {
                "symbol": br_symbol_str,
                "qty": int(position["quantity"]),
                "side": map_action(position["action"].upper()),
                "type": map_order_type(position["pricetype"]),
                "productType": map_product_type(position["product"]),
                "limitPrice": float(position.get("price", 0.0)),
                "stopLoss": 0.0,
                "stopPrice": float(position.get("trigger_price", 0.0)),
                "takeProfit": 0.0,
            }

            transformed_positions.append(transformed_position)
            logger.debug(
                f"Successfully transformed position: {symbol} ({exchange}) -> {br_symbol_str}"
            )

        except Exception as e:
            logger.error(f"Error transforming position: {position}, Error: {e}")
            skipped_positions.append(f"{position.get('symbol', 'unknown')} - Error: {str(e)}")
            continue

    # Log summary
    if skipped_positions:
        logger.warning(
            f"Skipped {len(skipped_positions)} position(s) due to missing/invalid symbols: {', '.join(skipped_positions)}"
        )

    if transformed_positions:
        logger.info(
            f"Successfully transformed {len(transformed_positions)} position(s) for margin calculation"
        )

    return transformed_positions


def parse_margin_response(response_data):
    """
    Parse Fyers margin response to OpenAlgo standard format.

    Fyers API returns total margin only, without detailed breakdown:
    - margin_avail: Available margin in account
    - margin_total: Approximate margin required for the order
    - margin_new_order: Total margin required including existing positions

    Unlike Angel/Zerodha, Fyers doesn't provide margin breakdown (SPAN/Exposure).
    We map margin_new_order to total_margin_required and set span/exposure to 0.

    Args:
        response_data: Raw response from Fyers API

    Expected response structure:
    {
        "s": "ok",
        "code": 200,
        "message": "",
        "data": {
            "margin_avail": 1999.9,
            "margin_total": 147738.0563,
            "margin_new_order": 147738.0563
        }
    }

    Returns:
        Standardized margin response matching OpenAlgo format:
        {
            "status": "success",
            "data": {
                "total_margin_required": 147738.0563,
                "span_margin": 0,
                "exposure_margin": 0
            }
        }
    """
    try:
        if not response_data or not isinstance(response_data, dict):
            return {"status": "error", "message": "Invalid response from broker"}

        # Check if the response has the expected structure
        # Fyers uses 's' field for status: 'ok' for success
        if response_data.get("s") != "ok":
            error_message = response_data.get("message", "Failed to calculate margin")
            error_code = response_data.get("code", "Unknown")
            return {
                "status": "error",
                "message": f"Fyers API Error (Code {error_code}): {error_message}",
            }

        # Extract margin data
        data = response_data.get("data", {})

        # Extract values from Fyers response
        margin_avail = data.get("margin_avail", 0)
        margin_total = data.get("margin_total", 0)
        margin_new_order = data.get("margin_new_order", 0)

        logger.info("=" * 80)
        logger.info("FYERS MARGIN API - DETAILED BREAKDOWN")
        logger.info("=" * 80)
        logger.info(f"Available Margin:        Rs. {margin_avail:,.2f}")
        logger.info(f"Margin Total:            Rs. {margin_total:,.2f}")
        logger.info(f"Margin New Order:        Rs. {margin_new_order:,.2f}")
        logger.info("")
        logger.info("NOTES:")
        logger.info("  - margin_avail: Available margin in your account")
        logger.info("  - margin_total: Approximate margin required for the order")
        logger.info("  - margin_new_order: Total margin including existing positions")
        logger.info("")
        logger.warning("⚠ IMPORTANT: Fyers does not provide SPAN/Exposure breakdown")
        logger.warning("⚠ Using margin_new_order as total_margin_required")
        logger.info("=" * 80)

        # Return standardized format matching OpenAlgo specification
        # Note: Fyers doesn't provide span_margin and exposure_margin breakdown
        # We use margin_new_order as the total margin required
        return {
            "status": "success",
            "data": {
                "total_margin_required": margin_new_order,
                "span_margin": 0,  # Fyers doesn't provide SPAN margin breakdown
                "exposure_margin": 0,  # Fyers doesn't provide Exposure margin breakdown
            },
        }

    except Exception as e:
        logger.error(f"Error parsing margin response: {e}")
        return {"status": "error", "message": f"Failed to parse margin response: {str(e)}"}

```


---

# FILE: broker\fyers\mapping\order_data.py

```py
import json

from database.token_db import get_oa_symbol, get_symbol
from utils.logging import get_logger

logger = get_logger(__name__)


# Mapping of (Exchange Code, Segment Code) to Exchange
exchange_map = {
    (10, 10): "NSE",
    (10, 11): "NFO",
    (10, 12): "CDS",
    (12, 10): "BSE",
    (12, 11): "BFO",
    (11, 20): "MCX",
}


def get_exchange(exchange_code, segment_code):
    # Key is a tuple of exchange_code and segment_code
    key = (exchange_code, segment_code)

    # Return the exchange name if key exists, else return None or a default value
    return exchange_map.get(key, "Unknown Exchange")


def map_order_data(order_data):
    """
    Processes and modifies a list of order dictionaries based on specific conditions.

    Parameters:
    - order_data: A list of dictionaries, where each dictionary represents an order.

    Returns:
    - The modified order_data with updated 'tradingsymbol' and 'product' fields.
    """
    if not order_data or order_data.get("orderBook") is None:
        logger.debug("No order data available in 'orderBook'.")
        return []

    order_list = order_data["orderBook"]

    for order in order_list:
        exchange_code = order.get("exchange")
        segment_code = order.get("segment")
        exchange = get_exchange(exchange_code, segment_code)
        symbol = order.get("symbol")

        if symbol:
            oa_symbol = get_oa_symbol(brsymbol=symbol, exchange=exchange)
            if oa_symbol:
                order["symbol"] = oa_symbol
                order["exchange"] = exchange
            else:
                logger.warning(
                    f"Could not map Fyers brsymbol '{symbol}' for exchange '{exchange}'. Keeping original."
                )
        else:
            logger.warning(f"Symbol not found in order: {order}. Keeping original trading symbol.")

    return order_list


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
            if order["side"] == 1:
                total_buy_orders += 1
            elif order["side"] == -1:
                total_sell_orders += 1

            # Count orders based on their status
            if order["status"] == 2:
                total_completed_orders += 1
            elif order["status"] == 6:
                total_open_orders += 1
            elif order["status"] == 5:
                total_rejected_orders += 1

    # Compile and return the statistics
    return {
        "total_buy_orders": total_buy_orders,
        "total_sell_orders": total_sell_orders,
        "total_completed_orders": total_completed_orders,
        "total_open_orders": total_open_orders,
        "total_rejected_orders": total_rejected_orders,
    }


def transform_order_data(orders):
    if isinstance(orders, dict):
        orders = [orders]

    transformed_orders = []

    status_map = {2: "complete", 5: "rejected", 4: "trigger pending", 6: "open", 1: "cancelled"}
    side_map = {1: "BUY", -1: "SELL"}
    type_map = {1: "LIMIT", 2: "MARKET", 3: "SL-M", 4: "SL"}
    product_map = {"CNC": "CNC", "INTRADAY": "MIS", "MARGIN": "NRML", "CO": "CO", "BO": "BO"}

    for order in orders:
        if not isinstance(order, dict):
            logger.warning(f"Expected a dict, but found {type(order)}. Skipping this item.")
            continue

        order_status_code = order.get("status")
        order_status = status_map.get(order_status_code, "unknown")
        if order_status == "unknown":
            logger.warning(
                f"Unknown order status code '{order_status_code}' for order: {order.get('id')}"
            )

        side_code = order.get("side")
        action = side_map.get(side_code, "unknown")
        if action == "unknown":
            logger.warning(f"Unknown side code '{side_code}' for order: {order.get('id')}")

        type_code = order.get("type")
        ordertype = type_map.get(type_code, "unknown")
        if ordertype == "unknown":
            logger.warning(f"Unknown order type code '{type_code}' for order: {order.get('id')}")

        product_code = order.get("productType")
        producttype = product_map.get(product_code, "unknown")
        if producttype == "unknown":
            logger.warning(f"Unknown product type '{product_code}' for order: {order.get('id')}")

        transformed_order = {
            "symbol": order.get("symbol", ""),
            "exchange": order.get("exchange", ""),
            "action": action,
            "quantity": order.get("qty", 0),
            "price": order.get("limitPrice", 0.0),
            "trigger_price": order.get("stopPrice", 0.0),
            "pricetype": ordertype,
            "product": producttype,
            "orderid": order.get("id", ""),
            "order_status": order_status,
            "timestamp": order.get("orderDateTime", ""),
        }
        transformed_orders.append(transformed_order)

    return transformed_orders


def map_trade_data(trade_data):
    """
    Processes and modifies a list of order dictionaries based on specific conditions.

    Parameters:
    - trade_data: A list of dictionaries, where each dictionary represents an order.

    Returns:
    - The modified trade_data with updated 'symbol' and 'product' fields.
    """
    if not trade_data or trade_data.get("tradeBook") is None:
        logger.debug("No trade data available in 'tradeBook'.")
        return []

    trade_list = trade_data["tradeBook"]

    for trade in trade_list:
        exchange_code = trade.get("exchange")
        segment_code = trade.get("segment")
        exchange = get_exchange(exchange_code, segment_code)
        symbol = trade.get("symbol")

        if symbol:
            oa_symbol = get_oa_symbol(brsymbol=symbol, exchange=exchange)
            if oa_symbol:
                trade["symbol"] = oa_symbol
                trade["exchange"] = exchange
            else:
                logger.warning(
                    f"Could not map Fyers brsymbol '{symbol}' for exchange '{exchange}'. Keeping original."
                )
        else:
            logger.warning(f"Symbol not found in trade: {trade}. Keeping original trading symbol.")

    return trade_list


def transform_tradebook_data(tradebook_data):
    transformed_data = []
    side_map = {1: "BUY", -1: "SELL"}
    product_map = {"CNC": "CNC", "INTRADAY": "MIS", "MARGIN": "NRML", "CO": "CO", "BO": "BO"}

    for trade in tradebook_data:
        symbol = trade.get("symbol")

        side_code = trade.get("side")
        action = side_map.get(side_code, "unknown")
        if action == "unknown":
            logger.warning(f"Unknown side code '{side_code}' for trade: {trade.get('orderNumber')}")

        product_code = trade.get("productType")
        producttype = product_map.get(product_code, "unknown")
        if producttype == "unknown":
            logger.warning(
                f"Unknown product type '{product_code}' for trade: {trade.get('orderNumber')}"
            )

        transformed_trade = {
            "symbol": symbol,
            "exchange": trade.get("exchange", ""),
            "product": producttype,
            "action": action,
            "quantity": trade.get("tradedQty", 0),
            "average_price": trade.get("tradePrice", 0.0),
            "trade_value": trade.get("tradeValue", 0),
            "orderid": trade.get("orderNumber", ""),
            "timestamp": trade.get("orderDateTime", ""),
        }
        transformed_data.append(transformed_trade)
    return transformed_data


def map_position_data(position_data):
    """
    Processes and modifies a list of OpenPosition dictionaries based on specific conditions.

    Parameters:
    - position_data: A list of dictionaries, where each dictionary represents an Open Position.

    Returns:
    - The modified order_data with updated 'tradingsymbol'
    """
    if not position_data or position_data.get("netPositions") is None:
        logger.debug("No position data available in 'netPositions'.")
        return []

    position_list = position_data["netPositions"]
    logger.debug(f"Raw Fyers positions: {position_list}")

    for position in position_list:
        exchange_code = position.get("exchange")
        segment_code = position.get("segment")
        exchange = get_exchange(exchange_code, segment_code)
        symbol = position.get("symbol")

        if symbol:
            oa_symbol = get_oa_symbol(brsymbol=symbol, exchange=exchange)
            if oa_symbol:
                position["symbol"] = oa_symbol
                position["exchange"] = exchange
            else:
                logger.warning(
                    f"Could not map Fyers brsymbol '{symbol}' for exchange '{exchange}'. Keeping original."
                )
        else:
            logger.warning(
                f"Symbol not found in position: {position}. Keeping original trading symbol."
            )

    return position_list


def transform_positions_data(positions_data):
    transformed_data = []

    for position in positions_data:
        # Ensure values are floats rounded to 2 decimal places (not strings)
        average_price_formatted = round(float(position.get("netAvg", 0.0)), 2)

        # Get LTP and PNL from Fyers response as numbers
        ltp = round(float(position.get("ltp", 0.0)), 2)
        pnl = round(float(position.get("pl", 0.0)), 2)

        if position.get("productType") == "CNC":
            producttype = "CNC"
        if position.get("productType") == "INTRADAY":
            producttype = "MIS"
        if position.get("productType") == "MARGIN":
            producttype = "NRML"
        if position.get("productType") == "CO":
            producttype = "CO"
        if position.get("productType") == "BO":
            producttype = "BO"

        transformed_position = {
            "symbol": position.get("symbol", ""),
            "exchange": position.get("exchange", ""),
            "product": producttype,
            "quantity": position.get("netQty", "0"),
            "average_price": average_price_formatted,
            "ltp": ltp,
            "pnl": pnl,
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
    if not portfolio_data or portfolio_data.get("holdings") is None:
        logger.debug("No portfolio data available in 'holdings'.")
        return []

    portfolio_list = portfolio_data["holdings"]
    logger.debug(f"Raw Fyers portfolio: {portfolio_list}")

    for portfolio in portfolio_list:
        if portfolio.get("holdingType") in ("HLD", "T1"):
            portfolio["holdingType"] = "CNC"
        else:
            logger.warning(
                f"Fyers Portfolio - Unknown product value for delivery: {portfolio.get('holdingType')}"
            )

        exchange_code = portfolio.get("exchange")
        segment_code = portfolio.get("segment")
        exchange = get_exchange(exchange_code, segment_code)
        symbol = portfolio.get("symbol")

        if symbol:
            oa_symbol = get_oa_symbol(brsymbol=symbol, exchange=exchange)
            if oa_symbol:
                portfolio["symbol"] = oa_symbol
                portfolio["exchange"] = exchange
            else:
                logger.warning(
                    f"Could not map Fyers brsymbol '{symbol}' for exchange '{exchange}'. Keeping original."
                )
        else:
            logger.warning(
                f"Symbol not found in portfolio holding: {portfolio}. Keeping original trading symbol."
            )

    return portfolio_list


def transform_holdings_data(holdings_data):
    transformed_data = []
    for holdings in holdings_data:
        pnl = round(holdings.get("pl", 0.0), 2)
        cost_price = holdings.get("costPrice", 0.0)
        ltp = holdings.get("ltp", 0)

        # Handle zero cost price to avoid division by zero
        if cost_price and cost_price != 0:
            pnlpercent = round((ltp - cost_price) / cost_price * 100, 2)
        else:
            pnlpercent = 0.0

        transformed_position = {
            "symbol": holdings.get("symbol", ""),
            "exchange": holdings.get("exchange", ""),
            "quantity": holdings.get("quantity", 0),
            "product": holdings.get("holdingType", ""),
            "average_price": round(float(cost_price), 2),
            "ltp": round(float(ltp), 2),
            "pnl": pnl,
            "pnlpercent": pnlpercent,
        }
        transformed_data.append(transformed_position)
    return transformed_data


def calculate_portfolio_statistics(holdings_data):
    totalholdingvalue = sum(item["ltp"] * item["quantity"] for item in holdings_data)
    totalinvvalue = sum(item["costPrice"] * item["quantity"] for item in holdings_data)
    totalprofitandloss = sum(item["pl"] for item in holdings_data)

    # To avoid division by zero in the case when total_investment_value is 0
    totalpnlpercentage = (totalprofitandloss / totalinvvalue * 100) if totalinvvalue else 0
    totalpnlpercentage = round(totalpnlpercentage, 2)

    return {
        "totalholdingvalue": totalholdingvalue,
        "totalinvvalue": totalinvvalue,
        "totalprofitandloss": totalprofitandloss,
        "totalpnlpercentage": totalpnlpercentage,
    }

```


---

# FILE: broker\fyers\mapping\transform_data.py

```py
# Mapping OpenAlgo API Request https://openalgo.in/docs
# Mapping Fyers Broking Parameters

from database.token_db import get_br_symbol
from utils.logging import get_logger

logger = get_logger(__name__)


def transform_data(data):
    """
    Transforms the OpenAlgo Platform API request structure to the format expected by the Fyers API.
    """
    symbol = get_br_symbol(data["symbol"], data["exchange"])

    quantity = int(data["quantity"])
    price = float(data.get("price", 0))
    trigger_price = float(data.get("trigger_price", 0))
    disclosed_quantity = int(data.get("disclosed_quantity", 0))

    transformed = {
        "symbol": symbol,
        "qty": quantity,
        "type": map_order_type(data["pricetype"]),
        "side": map_action(data["action"]),
        "productType": map_product_type(data["product"]),
        "limitPrice": price,
        "stopPrice": trigger_price,
        "validity": "DAY",
        "disclosedQty": disclosed_quantity,
        "offlineOrder": False,
        "stopLoss": 0,
        "takeProfit": 0,
        "orderTag": "openalgo",
    }

    return transformed


def transform_modify_order_data(data):
    """
    Transforms the order modification data to the format expected by Fyers API.
    Handles empty strings and None values for price and trigger_price.
    """
    order_id = data.get("orderid", "N/A")
    try:
        quantity = int(data.get("quantity", 0))
    except (ValueError, TypeError) as e:
        logger.warning(
            f"Could not parse quantity for order modification {order_id}. Defaulting to 0. Error: {e}"
        )
        quantity = 0

    try:
        price = float(data.get("price", 0)) if data.get("price") else 0.0
    except (ValueError, TypeError) as e:
        logger.warning(
            f"Could not parse price for order modification {order_id}. Defaulting to 0.0. Error: {e}"
        )
        price = 0.0

    try:
        trigger_price = float(data.get("trigger_price", 0)) if data.get("trigger_price") else 0.0
    except (ValueError, TypeError) as e:
        logger.warning(
            f"Could not parse trigger_price for order modification {order_id}. Defaulting to 0.0. Error: {e}"
        )
        trigger_price = 0.0

    return {
        "id": data["orderid"],
        "qty": quantity,
        "type": map_order_type(data.get("pricetype", "")),
        "limitPrice": price,
        "stopPrice": trigger_price,
    }


def map_order_type(pricetype):
    """
    Maps the OpenAlgo pricetype to the Fyers order type.
    """
    order_type_mapping = {"MARKET": 2, "LIMIT": 1, "SL": 4, "SL-M": 3}
    order_type = order_type_mapping.get(pricetype)
    if order_type is None:
        logger.warning(f"Unknown pricetype '{pricetype}' received. Defaulting to MARKET (2).")
        return 2  # Default to MARKET
    return order_type


def map_action(action):
    """
    Maps the OpenAlgo action to the Fyers side.
    """
    action_mapping = {"BUY": 1, "SELL": -1}
    side = action_mapping.get(action)
    if side is None:
        logger.warning(f"Unknown action '{action}' received. Cannot map to a side.")
    return side


def map_product_type(product):
    """
    Maps the OpenAlgo product type to the Fyers product type.
    """
    product_type_mapping = {
        "CNC": "CNC",
        "NRML": "MARGIN",
        "MIS": "INTRADAY",
        "CO": "CO",
        "BO": "BO",
    }
    fyers_product = product_type_mapping.get(product)
    if fyers_product is None:
        logger.warning(f"Unknown product type '{product}' received. Defaulting to INTRADAY.")
        return "INTRADAY"  # Default to INTRADAY
    return fyers_product


def reverse_map_product_type(product):
    """
    Reverse maps the Fyers product type to the OpenAlgo product type.
    """
    reverse_product_mapping = {
        "CNC": "CNC",
        "MARGIN": "NRML",
        "INTRADAY": "MIS",
        "CO": "CO",
        "BO": "BO",
    }
    oa_product = reverse_product_mapping.get(product)
    if oa_product is None:
        logger.warning(
            f"Unknown Fyers product type '{product}' received. Cannot map to OpenAlgo product type."
        )
    return oa_product

```
