# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\angel\mapping



---

# FILE: broker\angel\mapping\margin_data.py

```py
# Mapping OpenAlgo API Request https://openalgo.in/docs
# Mapping Angel Broking Margin API https://smartapi.angelbroking.com/docs/Margin

from database.token_db import get_token
from utils.logging import get_logger

logger = get_logger(__name__)


def transform_margin_positions(positions):
    """
    Transform OpenAlgo margin position format to Angel Broking margin format.

    Args:
        positions: List of positions in OpenAlgo format

    Returns:
        List of positions in Angel Broking format
    """
    transformed_positions = []
    skipped_positions = []

    for position in positions:
        try:
            symbol = position["symbol"]
            exchange = position["exchange"]

            # Get the token for the symbol
            token = get_token(symbol, exchange)

            # Validate token exists and is not None
            if not token or token is None or str(token).lower() == "none":
                logger.warning(f"Token not found for symbol: {symbol} on exchange: {exchange}")
                skipped_positions.append(f"{symbol} ({exchange})")
                continue

            # Validate token is a valid number/string (Angel expects numeric token)
            token_str = str(token).strip()
            if not token_str or not token_str.replace(".", "").replace("-", "").isdigit():
                logger.warning(f"Invalid token format for {symbol} ({exchange}): '{token_str}'")
                skipped_positions.append(f"{symbol} ({exchange}) - invalid token: {token_str}")
                continue

            # Transform the position
            transformed_position = {
                "exchange": exchange,
                "qty": int(position["quantity"]),
                "price": float(position.get("price", 0)),
                "productType": map_product_type(position["product"]),
                "token": token_str,
                "tradeType": position["action"].upper(),
                "orderType": map_order_type(position["pricetype"]),
            }

            transformed_positions.append(transformed_position)
            logger.debug(
                f"Successfully transformed position: {symbol} ({exchange}) with token: {token_str}"
            )

        except Exception as e:
            logger.error(f"Error transforming position: {position}, Error: {e}")
            skipped_positions.append(f"{position.get('symbol', 'unknown')} - Error: {str(e)}")
            continue

    # Log summary
    if skipped_positions:
        logger.warning(
            f"Skipped {len(skipped_positions)} position(s) due to missing/invalid tokens: {', '.join(skipped_positions)}"
        )

    if transformed_positions:
        logger.info(
            f"Successfully transformed {len(transformed_positions)} position(s) for margin calculation"
        )

    return transformed_positions


def map_product_type(product):
    """
    Maps OpenAlgo product type to Angel Broking product type.

    OpenAlgo: CNC, NRML, MIS
    Angel: DELIVERY, CARRYFORWARD, INTRADAY, MARGIN
    """
    product_type_mapping = {
        "CNC": "DELIVERY",
        "NRML": "CARRYFORWARD",
        "MIS": "INTRADAY",
    }
    return product_type_mapping.get(product, "INTRADAY")


def map_order_type(pricetype):
    """
    Maps OpenAlgo price type to Angel Broking order type.

    OpenAlgo: MARKET, LIMIT, SL, SL-M
    Angel: MARKET, LIMIT, STOPLOSS_LIMIT, STOPLOSS_MARKET
    """
    order_type_mapping = {
        "MARKET": "MARKET",
        "LIMIT": "LIMIT",
        "SL": "STOPLOSS_LIMIT",
        "SL-M": "STOPLOSS_MARKET",
    }
    return order_type_mapping.get(pricetype, "MARKET")


def parse_margin_response(response_data):
    """
    Parse Angel Broking margin calculator response to OpenAlgo standard format.

    Args:
        response_data: Raw response from Angel Broking margin calculator API

    Returns:
        Standardized margin response matching OpenAlgo format
    """
    try:
        if not response_data or not isinstance(response_data, dict):
            return {"status": "error", "message": "Invalid response from broker"}

        # Check if the response has the expected structure
        if response_data.get("status") is False:
            return {
                "status": "error",
                "message": response_data.get("message", "Failed to calculate margin"),
            }

        # Extract margin data from Angel's margin calculator response
        data = response_data.get("data", {})
        margin_components = data.get("marginComponents", {})

        # Extract values from Angel's response
        total_margin_required = data.get("totalMarginRequired", 0)
        span_margin = margin_components.get("spanMargin", 0)

        # Angel API doesn't provide exposure margin explicitly, so set it to 0
        exposure_margin = 0

        # Return standardized format matching OpenAlgo API specification
        return {
            "status": "success",
            "data": {
                "total_margin_required": total_margin_required,
                "span_margin": span_margin,
                "exposure_margin": exposure_margin,
            },
        }

    except Exception as e:
        logger.error(f"Error parsing margin response: {e}")
        return {"status": "error", "message": f"Failed to parse margin response: {str(e)}"}

```


---

# FILE: broker\angel\mapping\order_data.py

```py
import json

from database.token_db import get_oa_symbol, get_symbol
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
    # Check if order_data is empty or doesn't have 'data' key
    if not order_data or "data" not in order_data or order_data["data"] is None:
        # Handle the case where there is no data
        # For example, you might want to display a message to the user
        # or pass an empty list or dictionary to the template.
        logger.info("No data available.")
        order_data = []  # Return empty list as the functions expect a list
    else:
        order_data = order_data["data"]
        logger.info(f"{order_data}")

    if order_data:
        for order in order_data:
            # Extract the instrument_token and exchange for the current order
            symboltoken = order["symboltoken"]
            exchange = order["exchange"]

            # Use the get_symbol function to fetch the symbol from the database
            symbol_from_db = get_symbol(symboltoken, exchange)

            # Check if a symbol was found; if so, update the trading_symbol in the current order
            if symbol_from_db:
                order["tradingsymbol"] = symbol_from_db
                if (order["exchange"] == "NSE" or order["exchange"] == "BSE") and order[
                    "producttype"
                ] == "DELIVERY":
                    order["producttype"] = "CNC"

                elif order["producttype"] == "INTRADAY":
                    order["producttype"] = "MIS"

                elif (
                    order["exchange"] in ["NFO", "MCX", "BFO", "CDS"]
                    and order["producttype"] == "CARRYFORWARD"
                ):
                    order["producttype"] = "NRML"
            else:
                logger.info(
                    f"Symbol not found for token {symboltoken} and exchange {exchange}. Keeping original trading symbol."
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
            if order["transactiontype"] == "BUY":
                total_buy_orders += 1
            elif order["transactiontype"] == "SELL":
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
            logger.warning(
                f"Warning: Expected a dict, but found a {type(order)}. Skipping this item."
            )
            continue

        ordertype = order.get("ordertype", "")
        if ordertype == "STOPLOSS_LIMIT":
            ordertype = "SL"
        if ordertype == "STOPLOSS_MARKET":
            ordertype = "SL-M"

        transformed_order = {
            "symbol": order.get("tradingsymbol", ""),
            "exchange": order.get("exchange", ""),
            "action": order.get("transactiontype", ""),
            "quantity": order.get("quantity", 0),
            "price": order.get("averageprice", 0.0) or order.get("price", 0.0),
            "trigger_price": order.get("triggerprice", 0.0),
            "pricetype": ordertype,
            "product": order.get("producttype", ""),
            "orderid": order.get("orderid", ""),
            "order_status": order.get("status", ""),
            "timestamp": order.get("updatetime", ""),
        }

        transformed_orders.append(transformed_order)

    return transformed_orders


def map_trade_data(trade_data):
    """
    Processes and modifies a list of order dictionaries based on specific conditions.

    Parameters:
    - order_data: A list of dictionaries, where each dictionary represents an order.

    Returns:
    - The modified order_data with updated 'tradingsymbol' and 'product' fields.
    """
    # Check if 'data' is None
    if trade_data["data"] is None:
        # Handle the case where there is no data
        # For example, you might want to display a message to the user
        # or pass an empty list or dictionary to the template.
        logger.info("No data available.")
        trade_data = {}  # or set it to an empty list if it's supposed to be a list
    else:
        trade_data = trade_data["data"]

    if trade_data:
        for order in trade_data:
            # Extract the instrument_token and exchange for the current order
            symbol = order["tradingsymbol"]
            exchange = order["exchange"]

            # Use the get_symbol function to fetch the symbol from the database
            symbol_from_db = get_oa_symbol(symbol, exchange)

            # Check if a symbol was found; if so, update the trading_symbol in the current order
            if symbol_from_db:
                order["tradingsymbol"] = symbol_from_db
                if (order["exchange"] == "NSE" or order["exchange"] == "BSE") and order[
                    "producttype"
                ] == "DELIVERY":
                    order["producttype"] = "CNC"

                elif order["producttype"] == "INTRADAY":
                    order["producttype"] = "MIS"

                elif (
                    order["exchange"] in ["NFO", "MCX", "BFO", "CDS"]
                    and order["producttype"] == "CARRYFORWARD"
                ):
                    order["producttype"] = "NRML"
            else:
                logger.info(
                    f"Unable to find the symbol {symbol} and exchange {exchange}. Keeping original trading symbol."
                )

    return trade_data


def transform_tradebook_data(tradebook_data):
    transformed_data = []
    for trade in tradebook_data:
        transformed_trade = {
            "symbol": trade.get("tradingsymbol", ""),
            "exchange": trade.get("exchange", ""),
            "product": trade.get("producttype", ""),
            "action": trade.get("transactiontype", ""),
            "quantity": trade.get("quantity", 0),
            "average_price": trade.get("fillprice", 0.0),
            "trade_value": trade.get("tradevalue", 0),
            "orderid": trade.get("orderid", ""),
            "timestamp": trade.get("filltime", ""),
        }
        transformed_data.append(transformed_trade)
    return transformed_data


def map_position_data(position_data):
    return map_order_data(position_data)


def transform_positions_data(positions_data):
    transformed_data = []
    for position in positions_data:
        transformed_position = {
            "symbol": position.get("tradingsymbol", ""),
            "exchange": position.get("exchange", ""),
            "product": position.get("producttype", ""),
            "quantity": position.get("netqty", 0),
            "average_price": position.get("avgnetprice", 0.0),
            "ltp": position.get("ltp", 0.0),
            "pnl": position.get("pnl", 0.0),
        }
        transformed_data.append(transformed_position)
    return transformed_data


def transform_holdings_data(holdings_data):
    transformed_data = []
    for holdings in holdings_data["holdings"]:
        transformed_position = {
            "symbol": holdings.get("tradingsymbol", ""),
            "exchange": holdings.get("exchange", ""),
            "quantity": holdings.get("quantity", 0),
            "product": holdings.get("product", ""),
            "pnl": holdings.get("profitandloss", 0.0),
            "pnlpercent": holdings.get("pnlpercentage", 0.0),
        }
        transformed_data.append(transformed_position)
    return transformed_data


def map_portfolio_data(portfolio_data):
    """
    Processes and modifies a list of Portfolio dictionaries based on specific conditions and
    ensures both holdings and totalholding parts are transmitted in a single response.

    Parameters:
    - portfolio_data: A dictionary, where keys are 'holdings' and 'totalholding',
                      and values are lists/dictionaries representing the portfolio information.

    Returns:
    - The modified portfolio_data with 'product' fields changed for 'holdings' and 'totalholding' included.
    """
    # Check if 'data' is None or doesn't contain 'holdings'
    if portfolio_data.get("data") is None or "holdings" not in portfolio_data["data"]:
        logger.info("No data available.")
        # Return an empty structure or handle this scenario as needed
        return {}

    # Directly work with 'data' for clarity and simplicity
    data = portfolio_data["data"]

    # Modify 'product' field for each holding if applicable
    if data.get("holdings"):
        for portfolio in data["holdings"]:
            symbol = portfolio["tradingsymbol"]
            exchange = portfolio["exchange"]
            symbol_from_db = get_oa_symbol(symbol, exchange)

            # Check if a symbol was found; if so, update the trading_symbol in the current order
            if symbol_from_db:
                portfolio["tradingsymbol"] = symbol_from_db
            if portfolio["product"] == "DELIVERY":
                portfolio["product"] = "CNC"  # Modify 'product' field
            else:
                logger.info("AngelOne Portfolio - Product Value for Delivery Not Found or Changed.")

    # The function already works with 'data', which includes 'holdings' and 'totalholding',
    # so we can return 'data' directly without additional modifications.
    return data


def calculate_portfolio_statistics(holdings_data):
    if holdings_data["totalholding"] is None:
        totalholdingvalue = 0
        totalinvvalue = 0
        totalprofitandloss = 0
        totalpnlpercentage = 0
    else:
        totalholdingvalue = holdings_data["totalholding"]["totalholdingvalue"]
        totalinvvalue = holdings_data["totalholding"]["totalinvvalue"]
        totalprofitandloss = holdings_data["totalholding"]["totalprofitandloss"]

        # To avoid division by zero in the case when total_investment_value is 0
        totalpnlpercentage = holdings_data["totalholding"]["totalpnlpercentage"]

    return {
        "totalholdingvalue": totalholdingvalue,
        "totalinvvalue": totalinvvalue,
        "totalprofitandloss": totalprofitandloss,
        "totalpnlpercentage": totalpnlpercentage,
    }

```


---

# FILE: broker\angel\mapping\transform_data.py

```py
# Mapping OpenAlgo API Request https://openalgo.in/docs
# Mapping Angel Broking Parameters https://smartapi.angelbroking.com/docs/Orders

from database.token_db import get_br_symbol


def transform_data(data, token):
    """
    Transforms the new API request structure to the current expected structure.
    """
    symbol = get_br_symbol(data["symbol"], data["exchange"])
    # Basic mapping
    transformed = {
        "apikey": data["apikey"],
        "variety": map_variety(data["pricetype"]),
        "tradingsymbol": symbol,
        "symboltoken": token,
        "transactiontype": data["action"].upper(),
        "exchange": data["exchange"],
        "ordertype": map_order_type(data["pricetype"]),
        "producttype": map_product_type(data["product"]),
        "duration": "DAY",  # Assuming DAY as default; you might need logic to handle this if it can vary
        "price": data.get("price", "0"),
        "squareoff": "0",  # Assuming not applicable; adjust if needed
        "stoploss": data.get("trigger_price", "0"),
        "disclosedquantity": data.get("disclosed_quantity", "0"),
        "quantity": data["quantity"],
    }

    # Extended mapping for fields that might need conditional logic or additional processing
    transformed["disclosedquantity"] = data.get("disclosed_quantity", "0")
    transformed["triggerprice"] = data.get("trigger_price", "0")

    return transformed


def transform_modify_order_data(data, token):
    return {
        "variety": map_variety(data["pricetype"]),
        "orderid": data["orderid"],
        "ordertype": map_order_type(data["pricetype"]),
        "producttype": map_product_type(data["product"]),
        "duration": "DAY",
        "price": data["price"],
        "quantity": data["quantity"],
        "tradingsymbol": data["symbol"],
        "symboltoken": token,
        "exchange": data["exchange"],
        "disclosedquantity": data.get("disclosed_quantity", "0"),
        "stoploss": data.get("trigger_price", "0"),
    }


def map_order_type(pricetype):
    """
    Maps the new pricetype to the existing order type.
    """
    order_type_mapping = {
        "MARKET": "MARKET",
        "LIMIT": "LIMIT",
        "SL": "STOPLOSS_LIMIT",
        "SL-M": "STOPLOSS_MARKET",
    }
    return order_type_mapping.get(pricetype, "MARKET")  # Default to MARKET if not found


def map_product_type(product):
    """
    Maps the new product type to the existing product type.
    """
    product_type_mapping = {
        "CNC": "DELIVERY",
        "NRML": "CARRYFORWARD",
        "MIS": "INTRADAY",
    }
    return product_type_mapping.get(product, "INTRADAY")  # Default to DELIVERY if not found


def map_variety(pricetype):
    """
    Maps the pricetype to the existing order variety.
    """
    variety_mapping = {"MARKET": "NORMAL", "LIMIT": "NORMAL", "SL": "STOPLOSS", "SL-M": "STOPLOSS"}
    return variety_mapping.get(pricetype, "NORMAL")  # Default to DELIVERY if not found


def reverse_map_product_type(product):
    """
    Maps the new product type to the existing product type.
    """
    reverse_product_type_mapping = {
        "DELIVERY": "CNC",
        "CARRYFORWARD": "NRML",
        "INTRADAY": "MIS",
    }
    return reverse_product_type_mapping.get(product)

```
