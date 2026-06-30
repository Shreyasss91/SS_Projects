# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\upstox\mapping



---

# FILE: broker\upstox\mapping\margin_data.py

```py
# Mapping OpenAlgo API Request https://openalgo.in/docs
# Mapping Upstox Margin API https://upstox.com/developer/api-documentation/margin

from broker.upstox.mapping.transform_data import map_product_type
from database.token_db import get_token
from utils.logging import get_logger

logger = get_logger(__name__)


def transform_margin_positions(positions):
    """
    Transform OpenAlgo margin position format to Upstox margin format.

    Args:
        positions: List of positions in OpenAlgo format

    Returns:
        List of positions in Upstox format
    """
    transformed_positions = []
    skipped_positions = []

    for position in positions:
        try:
            symbol = position["symbol"]
            exchange = position["exchange"]

            # Get the instrument key for Upstox (format: EXCHANGE_SEGMENT|TOKEN)
            # Note: get_token() returns instrument_key for Upstox, not get_br_symbol()
            instrument_key = get_token(symbol, exchange)

            # Validate instrument key exists and is not None
            if (
                not instrument_key
                or instrument_key is None
                or str(instrument_key).lower() == "none"
            ):
                logger.warning(f"Instrument key not found for: {symbol} on exchange: {exchange}")
                skipped_positions.append(f"{symbol} ({exchange})")
                continue

            # Validate instrument key format (Upstox format: EXCHANGE_SEGMENT|TOKEN)
            instrument_key_str = str(instrument_key).strip()
            if not instrument_key_str or "|" not in instrument_key_str:
                logger.warning(
                    f"Invalid instrument key format for {symbol} ({exchange}): '{instrument_key_str}'"
                )
                skipped_positions.append(
                    f"{symbol} ({exchange}) - invalid key: {instrument_key_str}"
                )
                continue

            # Transform the position
            transformed_position = {
                "instrument_key": instrument_key_str,
                "quantity": int(position["quantity"]),
                "transaction_type": position["action"].upper(),
                "product": map_product_type(position["product"]),
            }

            # Add price if provided (optional field)
            if position.get("price") and float(position["price"]) > 0:
                transformed_position["price"] = float(position["price"])

            transformed_positions.append(transformed_position)
            logger.debug(
                f"Successfully transformed position: {symbol} ({exchange}) with key: {instrument_key_str}"
            )

        except Exception as e:
            logger.error(f"Error transforming position: {position}, Error: {e}")
            skipped_positions.append(f"{position.get('symbol', 'unknown')} - Error: {str(e)}")
            continue

    # Log summary
    if skipped_positions:
        logger.warning(
            f"Skipped {len(skipped_positions)} position(s) due to missing/invalid instrument keys: {', '.join(skipped_positions)}"
        )

    if transformed_positions:
        logger.info(
            f"Successfully transformed {len(transformed_positions)} position(s) for margin calculation"
        )

    return transformed_positions


def parse_margin_response(response_data):
    """
    Parse Upstox margin response to OpenAlgo standard format.

    Args:
        response_data: Raw response from Upstox margin API

    Returns:
        Standardized margin response matching OpenAlgo format
    """
    try:
        if not response_data or not isinstance(response_data, dict):
            return {"status": "error", "message": "Invalid response from broker"}

        # Check if the response status is success
        if response_data.get("status") != "success":
            error_message = response_data.get("message", "Failed to calculate margin")
            # Check for errors array
            if "errors" in response_data:
                errors = response_data["errors"]
                if isinstance(errors, list) and len(errors) > 0:
                    error_message = errors[0].get("message", error_message)
            return {"status": "error", "message": error_message}

        # Extract margin data from Upstox response
        data = response_data.get("data", {})

        # Extract top-level margin values
        required_margin = data.get("required_margin", 0)
        final_margin = data.get("final_margin", 0)

        # Calculate margin benefit (difference between required and final margin)
        margin_benefit = required_margin - final_margin

        # Extract margin breakdown (array of margins per instrument)
        margins = data.get("margins", [])

        # Aggregate margin components from all instruments
        total_span = 0
        total_exposure = 0

        for margin in margins:
            total_span += margin.get("span_margin", 0)
            total_exposure += margin.get("exposure_margin", 0)

        # Return standardized format matching OpenAlgo API specification
        return {
            "status": "success",
            "data": {
                "total_margin_required": required_margin,
                "span_margin": total_span,
                "exposure_margin": total_exposure,
            },
        }

    except Exception as e:
        logger.error(f"Error parsing margin response: {e}")
        return {"status": "error", "message": f"Failed to parse margin response: {str(e)}"}

```


---

# FILE: broker\upstox\mapping\order_data.py

```py
import json

from database.token_db import get_symbol
from utils.logging import get_logger

logger = get_logger(__name__)


def map_order_data(order_data):
    """
    Processes and modifies a list of order dictionaries based on specific conditions.

    Parameters:
    - order_data: A list of dictionaries, where each dictionary represents an order.

    Returns:
    - The modified order_data with updated 'tradingsymbol' and 'product' fields.
    """
    # Check if 'data' is None
    if order_data["data"] is None:
        # Handle the case where there is no data
        # For example, you might want to display a message to the user
        # or pass an empty list or dictionary to the template.
        logger.debug("No order data available to map.")
        order_data = {}  # or set it to an empty list if it's supposed to be a list
    else:
        order_data = order_data["data"]

    if order_data:
        for order in order_data:
            # Extract the instrument_token and exchange for the current order
            instrument_token = order["instrument_token"]
            exchange = order["exchange"]

            # Use the get_symbol function to fetch the symbol from the database
            symbol_from_db = get_symbol(instrument_token, exchange)

            # Check if a symbol was found; if so, update the trading_symbol in the current order
            if symbol_from_db:
                order["tradingsymbol"] = symbol_from_db
                if (order["exchange"] == "NSE" or order["exchange"] == "BSE") and order[
                    "product"
                ] == "D":
                    order["product"] = "CNC"

                elif order["product"] == "I":
                    order["product"] = "MIS"

                elif order["exchange"] in ["NFO", "MCX", "BFO", "CDS"] and order["product"] == "D":
                    order["product"] = "NRML"
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
            if order["transaction_type"] == "BUY":
                total_buy_orders += 1
            elif order["transaction_type"] == "SELL":
                total_sell_orders += 1

            # Count orders based on their status
            if order["status"] == "complete":
                total_completed_orders += 1
            elif order["status"] == "open":
                total_open_orders += 1
            elif order["status"] == "rejected":
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
    # Directly handling a dictionary assuming it's the structure we expect
    if isinstance(orders, dict):
        # Convert the single dictionary into a list of one dictionary
        orders = [orders]

    transformed_orders = []

    for order in orders:
        # Make sure each item is indeed a dictionary
        if not isinstance(order, dict):
            logger.warning(f"Expected a dict, but found {type(order)}. Skipping this item.")
            continue

        transformed_order = {
            "symbol": order.get("tradingsymbol", ""),
            "exchange": order.get("exchange", ""),
            "action": order.get("transaction_type", ""),
            "quantity": order.get("quantity", 0),
            "price": order.get("price", 0.0),
            "trigger_price": order.get("trigger_price", 0.0),
            "pricetype": order.get("order_type", ""),
            "product": order.get("product", ""),
            "orderid": order.get("order_id", ""),
            "order_status": order.get("status", ""),
            "timestamp": order.get("order_timestamp", ""),
        }

        transformed_orders.append(transformed_order)

    return transformed_orders


def map_trade_data(trade_data):
    return map_order_data(trade_data)


def transform_tradebook_data(tradebook_data):
    transformed_data = []
    for trade in tradebook_data:
        transformed_trade = {
            "symbol": trade.get("tradingsymbol", ""),
            "exchange": trade.get("exchange", ""),
            "product": trade.get("product", ""),
            "action": trade.get("transaction_type", ""),
            "quantity": trade.get("quantity", 0),
            "average_price": trade.get("average_price", 0.0),
            "trade_value": trade.get("quantity", 0) * trade.get("average_price", 0.0),
            "orderid": trade.get("order_id", ""),
            "timestamp": trade.get("order_timestamp", ""),
        }
        transformed_data.append(transformed_trade)
    return transformed_data


def map_position_data(position_data):
    return map_order_data(position_data)


def transform_positions_data(positions_data):
    transformed_data = []
    for position in positions_data:
        # Handle null average_price from Upstox API
        # According to Upstox API docs:
        # - average_price: Average price at which the net position quantity was acquired
        # - buy_price: Average price at which quantities were bought
        # - sell_price: Average price at which quantities were sold
        # - day_buy_price: Average price at which the day qty was bought
        # - day_sell_price: Average price at which the day quantity was sold

        avg_price = position.get("average_price")
        quantity = position.get("quantity", 0)

        # If average_price is null or 0, calculate it from available data
        if avg_price is None or avg_price == 0:
            if quantity > 0:
                # Net LONG position
                # Priority: buy_price (overall average) > day_buy_price (intraday only)
                avg_price = position.get("buy_price", 0.0)
                if avg_price == 0 or avg_price is None:
                    avg_price = position.get("day_buy_price", 0.0)

            elif quantity < 0:
                # Net SHORT position
                # Priority: sell_price (overall average) > day_sell_price (intraday only)
                avg_price = position.get("sell_price", 0.0)
                if avg_price == 0 or avg_price is None:
                    avg_price = position.get("day_sell_price", 0.0)
            else:
                # quantity == 0: Position is closed
                avg_price = 0.0

        # Final conversion to float, handling None
        average_price = float(avg_price) if avg_price is not None else 0.0

        transformed_position = {
            "symbol": position.get("tradingsymbol", ""),
            "exchange": position.get("exchange", ""),
            "product": position.get("product", ""),
            "quantity": position.get("quantity", 0),
            "average_price": average_price,
            "pnl": position.get("pnl", 0.0),
            "ltp": position.get("last_price", 0.0),
        }
        transformed_data.append(transformed_position)
    return transformed_data


def transform_holdings_data(holdings_data):
    transformed_data = []
    for holdings in holdings_data:
        transformed_position = {
            "symbol": holdings.get("tradingsymbol", ""),
            "exchange": holdings.get("exchange", ""),
            "quantity": holdings.get("quantity", 0),
            "product": holdings.get("product", ""),
            "pnl": holdings.get("pnl", 0.0),
            "pnlpercent": (holdings.get("last_price", 0) - holdings.get("average_price", 0.0))
            / holdings.get("average_price", 0.0)
            * 100,
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
    # Check if 'data' is None
    if portfolio_data["data"] is None:
        # Handle the case where there is no data
        # For example, you might want to display a message to the user
        # or pass an empty list or dictionary to the template.
        logger.debug("No portfolio data available to map.")
        portfolio_data = {}  # or set it to an empty list if it's supposed to be a list
    else:
        portfolio_data = portfolio_data["data"]

    if portfolio_data:
        for portfolio in portfolio_data:
            if portfolio["product"] == "D":
                portfolio["product"] = "CNC"

            else:
                logger.warning(
                    "Upstox Portfolio - Product value for Delivery not found or changed."
                )

    return portfolio_data


def calculate_portfolio_statistics(holdings_data):
    totalholdingvalue = sum(item["last_price"] * item["quantity"] for item in holdings_data)
    totalinvvalue = sum(item["average_price"] * item["quantity"] for item in holdings_data)
    totalprofitandloss = sum(item["pnl"] for item in holdings_data)

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

# FILE: broker\upstox\mapping\transform_data.py

```py
# Mapping OpenAlgo API Request https://openalgo.in/docs
# Mapping Upstox Broking Parameters https://upstox.com/developer/api-documentation/orders

from utils.logging import get_logger

logger = get_logger(__name__)


def transform_data(data, token):
    """
    Transforms the new API request structure to the current expected structure.
    """
    # Basic mapping
    transformed = {
        "quantity": data["quantity"],
        "product": map_product_type(data["product"]),
        "validity": "DAY",
        "price": data.get("price", "0"),
        "tag": "string",
        "instrument_token": token,
        "order_type": map_order_type(data["pricetype"]),
        "transaction_type": data["action"].upper(),
        "disclosed_quantity": data.get("disclosed_quantity", "0"),
        "trigger_price": data.get("trigger_price", "0"),
        "is_amo": "false",  # Assuming false as default; you might need logic to handle this if it can vary
    }

    # Extended mapping for fields that might need conditional logic or additional processing
    transformed["disclosed_quantity"] = data.get("disclosed_quantity", "0")
    transformed["trigger_price"] = data.get("trigger_price", "0")

    return transformed


def transform_modify_order_data(data):
    return {
        "quantity": data["quantity"],
        "validity": "DAY",
        "price": data["price"],
        "order_id": data["orderid"],
        "order_type": map_order_type(data["pricetype"]),
        "disclosed_quantity": data.get("disclosed_quantity", "0"),
        "trigger_price": data.get("trigger_price", "0"),
    }


def map_order_type(pricetype):
    """
    Maps the new pricetype to the existing order type.
    """
    order_type_mapping = {"MARKET": "MARKET", "LIMIT": "LIMIT", "SL": "SL", "SL-M": "SL-M"}
    if pricetype not in order_type_mapping:
        logger.warning(f"Unknown pricetype '{pricetype}' received. Defaulting to 'MARKET'.")
        return "MARKET"
    return order_type_mapping[pricetype]


def map_product_type(product):
    """
    Maps the new product type to the existing product type.
    """
    product_type_mapping = {
        "CNC": "D",
        "NRML": "D",
        "MIS": "I",
    }
    if product not in product_type_mapping:
        logger.warning(f"Unknown product type '{product}' received. Defaulting to 'I' (Intraday).")
        return "I"
    return product_type_mapping[product]


def reverse_map_product_type(exchange, product):
    """
    Reverse maps the broker product type to the OpenAlgo product type, considering the exchange.
    """
    # Exchange to OpenAlgo product type mapping for 'D'
    exchange_mapping_for_d = {
        "NSE": "CNC",
        "BSE": "CNC",
        "NFO": "NRML",
        "BFO": "NRML",
        "MCX": "NRML",
        "CDS": "NRML",
    }

    # Reverse mapping based on product type and exchange
    if product == "D":
        openalgo_product = exchange_mapping_for_d.get(exchange)
        if not openalgo_product:
            logger.warning(
                f"Could not reverse map product type 'D' for unknown exchange '{exchange}'."
            )
        return openalgo_product
    elif product == "I":
        return "MIS"
    else:
        logger.warning(f"Unknown product type '{product}' received for reverse mapping.")
        return None

```
