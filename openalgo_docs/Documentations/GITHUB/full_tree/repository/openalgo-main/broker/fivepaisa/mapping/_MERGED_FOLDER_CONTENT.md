# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\fivepaisa\mapping



---

# FILE: broker\fivepaisa\mapping\margin_data.py

```py
# Mapping OpenAlgo API Request https://openalgo.in/docs
# 5paisa does not provide position-specific Margin Calculator API

from utils.logging import get_logger

logger = get_logger(__name__)


def transform_margin_positions(positions):
    """
    Transform OpenAlgo margin position format to broker format.

    Note: 5paisa does not provide a position-specific margin calculator API.
    The available Margin API only returns account-level margin information.

    Args:
        positions: List of positions in OpenAlgo format

    Raises:
        NotImplementedError: 5paisa does not support position-specific margin calculator API
    """
    raise NotImplementedError("5paisa does not support position-specific margin calculator API")


def parse_margin_response(response_data):
    """
    Parse broker margin calculator response to OpenAlgo standard format.

    Note: 5paisa does not provide a position-specific margin calculator API.
    The available Margin API only returns account-level margin information.

    Args:
        response_data: Raw response from broker margin calculator API

    Raises:
        NotImplementedError: 5paisa does not support position-specific margin calculator API
    """
    raise NotImplementedError("5paisa does not support position-specific margin calculator API")

```


---

# FILE: broker\fivepaisa\mapping\order_data.py

```py
import json
import re
from datetime import datetime, timedelta

from broker.fivepaisa.mapping.transform_data import reverse_map_exchange
from database.token_db import get_oa_symbol, get_symbol
from utils.logging import get_logger

logger = get_logger(__name__)


def convert_date_string(date_str):
    # Extract the timestamp and timezone offset using regular expressions
    match = re.search(r"/Date\((\d+)([+-]\d{4})\)/", date_str)
    if match:
        timestamp = int(match.group(1)) / 1000  # Convert from milliseconds to seconds
        offset = match.group(2)

        # Convert the timestamp to a datetime object
        dt = datetime.utcfromtimestamp(timestamp)

        # Apply the timezone offset
        offset_hours = int(offset[:3])
        offset_minutes = int(offset[0] + offset[3:])  # Handle the sign correctly
        dt += timedelta(hours=offset_hours, minutes=offset_minutes)

        # Return the result as a formatted string
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    else:
        return "Invalid date format"


def map_order_data(order_data):
    """
    Processes and modifies a list of order dictionaries based on specific conditions.

    Parameters:
    - order_data: A list of dictionaries, where each dictionary represents an order.

    Returns:
    - The modified order_data with updated 'tradingsymbol' and 'product' fields.
    """
    # Check if 'data' is None
    if order_data["body"]["OrderBookDetail"] is None:
        # Handle the case where there is no data
        logger.info("No data available.")
        order_data = {}  # or set it to an empty list if it's supposed to be a list
    else:
        order_data = order_data["body"]["OrderBookDetail"]

    if order_data:
        for order in order_data:
            # CRITICAL FIX: Ensure BrokerOrderId is always stored as a string to maintain consistent comparison
            if "BrokerOrderId" in order:
                order["BrokerOrderId"] = str(order["BrokerOrderId"])

            # Extract the instrument_token and exchange for the current order
            symboltoken = order["ScripCode"]
            Exch = order["Exch"]
            ExchType = order["ExchType"]

            exchange = reverse_map_exchange(Exch, ExchType)

            # Use the get_symbol function to fetch the symbol from the database
            symbol_from_db = get_symbol(symboltoken, exchange)

            # Check if a symbol was found; if so, update the trading_symbol in the current order
            if symbol_from_db:
                order["ScripName"] = symbol_from_db
                order["Exch"] = exchange
                if (order["Exch"] == "NSE" or order["Exch"] == "BSE") and order["DelvIntra"] == "D":
                    order["DelvIntra"] = "CNC"

                elif order["DelvIntra"] == "I":
                    order["DelvIntra"] = "MIS"

                elif order["Exch"] in ["NFO", "MCX", "BFO", "CDS"] and order["DelvIntra"] == "D":
                    order["DelvIntra"] = "NRML"
            else:
                logger.info(
                    f"Symbol not found for token {{symboltoken}} and exchange {exchange}. Keeping original trading symbol."
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
    total_completed_orders = total_open_orders = total_rejected_orders = total_cancelled_orders = 0

    if order_data:
        for order in order_data:
            # Count buy and sell orders
            if order["BuySell"] == "B":
                total_buy_orders += 1
                order["BuySell"] = "BUY"
            elif order["BuySell"] == "S":
                total_sell_orders += 1
                order["BuySell"] = "SELL"

            # Count orders based on their status
            status = order["OrderStatus"].strip() if order["OrderStatus"] else ""

            # Normalize status to standardized values
            if status == "Fully Executed":
                total_completed_orders += 1
                order["OrderStatus"] = "complete"
            elif status in ["Pending", "Modified", "Open"]:
                total_open_orders += 1
                order["OrderStatus"] = "open"
            elif "Rejected" in status:
                total_rejected_orders += 1
                order["OrderStatus"] = "rejected"
            elif status == "Cancelled":
                total_cancelled_orders += 1
                order["OrderStatus"] = "cancelled"

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

        pricetype = ""

        # Handle potential null/None SLTriggerRate safely
        sl_trigger_rate = order.get("SLTriggerRate", 0)
        stoplevel = float(sl_trigger_rate) if sl_trigger_rate is not None else 0

        if order.get("AtMarket") == "Y" and stoplevel == 0:
            pricetype = "MARKET"
        elif order.get("AtMarket") == "N" and stoplevel == 0:
            pricetype = "LIMIT"
        elif order.get("AtMarket") == "Y" and stoplevel > 0:
            pricetype = "SL-M"
        elif order.get("AtMarket") == "N" and stoplevel > 0:
            pricetype = "SL"
        else:
            # Default to LIMIT for any other scenario
            pricetype = "LIMIT"

        # Extract quantity based on availability (TradedQty or PendingQty)
        quantity = order.get("TradedQty", 0)
        # If TradedQty is 0 but there's a PendingQty, use that instead for rejected/canceled orders
        if quantity == 0 and order.get("Qty") is not None:
            quantity = order.get("Qty")

        # CRITICAL FIX: Ensure BrokerOrderId is properly converted to string consistently
        # This ensures the same format is used when comparing in the orderstatus endpoint
        orderid = str(order.get("BrokerOrderId", ""))

        transformed_order = {
            "symbol": order.get("ScripName", ""),
            "exchange": order.get("Exch", ""),
            "action": order.get("BuySell", ""),
            "quantity": quantity,
            "price": order.get("Rate", 0.0),
            "trigger_price": stoplevel,
            "pricetype": pricetype,
            "product": order.get("DelvIntra", ""),
            "orderid": orderid,  # String formatted order ID
            "order_status": order.get("OrderStatus", ""),
            "timestamp": convert_date_string(order.get("BrokerOrderTime", "")),
            "reason": order.get("Reason", ""),  # Add rejection reason if present
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
    if trade_data["body"]["TradeBookDetail"] is None:
        # Handle the case where there is no data
        # For example, you might want to display a message to the user
        # or pass an empty list or dictionary to the template.
        logger.info("No data available.")
        trade_data = {}  # or set it to an empty list if it's supposed to be a list
    else:
        trade_data = trade_data["body"]["TradeBookDetail"]

    if trade_data:
        for order in trade_data:
            # Extract the instrument_token and exchange for the current order
            symboltoken = order["ScripCode"]
            Exch = order["Exch"]
            ExchType = order["ExchType"]

            exchange = reverse_map_exchange(Exch, ExchType)

            # Use the get_symbol function to fetch the symbol from the database
            symbol_from_db = get_symbol(symboltoken, exchange)

            # Check if a symbol was found; if so, update the trading_symbol in the current order
            if symbol_from_db:
                order["ScripName"] = symbol_from_db
                order["Exch"] = exchange
                if (order["Exch"] == "NSE" or order["Exch"] == "BSE") and order["DelvIntra"] == "D":
                    order["DelvIntra"] = "CNC"

                elif order["DelvIntra"] == "I":
                    order["DelvIntra"] = "MIS"

                elif order["Exch"] in ["NFO", "MCX", "BFO", "CDS"] and order["DelvIntra"] == "D":
                    order["DelvIntra"] = "NRML"

                if order["BuySell"] == "B":
                    order["BuySell"] = "BUY"
                elif order["BuySell"] == "S":
                    order["BuySell"] = "SELL"

            else:
                logger.info(
                    f"Symbol not found for token {{symboltoken}} and exchange {exchange}. Keeping original trading symbol."
                )

    return trade_data


def transform_tradebook_data(tradebook_data):
    transformed_data = []
    for trade in tradebook_data:
        quantity = float(trade.get("Qty", 0))
        average_price = float(trade.get("Rate", 0.0))
        trade_value = quantity * average_price

        transformed_trade = {
            "symbol": trade.get("ScripName", ""),
            "exchange": trade.get("Exch", ""),
            "product": trade.get("DelvIntra", ""),
            "action": trade.get("BuySell", ""),
            "quantity": trade.get("Qty", 0),
            "average_price": trade.get("Rate", 0.0),
            "trade_value": round(trade_value, 2),
            "orderid": trade.get("ExchOrderID", ""),
            "timestamp": convert_date_string(trade.get("ExchangeTradeTime", "")),
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
    # Check if 'data' is None
    if position_data["body"]["NetPositionDetail"] is None:
        # Handle the case where there is no data
        # For example, you might want to display a message to the user
        # or pass an empty list or dictionary to the template.
        logger.info("No data available.")
        position_data = {}  # or set it to an empty list if it's supposed to be a list
    else:
        position_data = position_data["body"]["NetPositionDetail"]

    logger.info(f"{position_data}")

    if position_data:
        for position in position_data:
            # Extract the instrument_token and exchange for the current order
            symboltoken = position["ScripCode"]
            Exch = position["Exch"]
            ExchType = position["ExchType"]

            exchange = reverse_map_exchange(Exch, ExchType)

            # Use the get_symbol function to fetch the symbol from the database
            symbol_from_db = get_symbol(symboltoken, exchange)

            # Check if a symbol was found; if so, update the trading_symbol in the current order
            if symbol_from_db:
                position["ScripName"] = symbol_from_db
                position["Exch"] = exchange
                position["Exch"] = exchange
                if (position["Exch"] == "NSE" or position["Exch"] == "BSE") and position[
                    "OrderFor"
                ] == "D":
                    position["OrderFor"] = "CNC"

                elif position["OrderFor"] == "I":
                    position["OrderFor"] = "MIS"

                elif (
                    position["Exch"] in ["NFO", "MCX", "BFO", "CDS"] and position["OrderFor"] == "D"
                ):
                    position["OrderFor"] = "NRML"

            else:
                logger.info(
                    f"Symbol not found for token {{symboltoken}} and exchange {exchange}. Keeping original trading symbol."
                )

    return position_data


def transform_positions_data(positions_data):
    transformed_data = []
    for position in positions_data:
        average_price = 0.0
        net_qty = float(position.get("NetQty", 0))

        if net_qty > 0:
            average_price = position.get("BuyAvgRate", 0)
        else:  # net_qty < 0
            average_price = position.get("SellAvgRate", 0)

        transformed_position = {
            "symbol": position.get("ScripName", ""),
            "exchange": position.get("Exch", ""),
            "product": position.get("OrderFor", ""),
            "quantity": position.get("NetQty", 0),
            "average_price": average_price,
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
    if portfolio_data["body"]["Data"] is None:
        logger.info("No data available.")
        # Return an empty structure or handle this scenario as needed
        return {}

    # Directly work with 'data' for clarity and simplicity
    data = portfolio_data["body"]

    # Modify 'product' field for each holding if applicable
    if data.get("Data"):
        for portfolio in data["Data"]:
            if portfolio["Exch"] == "N":
                portfolio["Exch"] = "NSE"
            if portfolio["Exch"] == "B":
                portfolio["Exch"] = "BSE"

    # The function already works with 'data', which includes 'holdings' and 'totalholding',
    # so we can return 'data' directly without additional modifications.
    return data


def calculate_portfolio_statistics(holdings_data):
    total_holding_value = 0
    total_inv_value = 0

    for holdings in holdings_data["Data"]:
        avg_rate = float(holdings.get("AvgRate", 0.0))
        current_price = float(holdings.get("CurrentPrice", 0.0))
        quantity = float(holdings.get("Quantity", 0.0))

        inv_value = avg_rate * quantity
        holding_value = current_price * quantity

        total_inv_value += inv_value
        total_holding_value += holding_value

    total_profit_and_loss = total_holding_value - total_inv_value

    # To avoid division by zero in the case when total_inv_value is 0
    total_pnl_percentage = (
        (total_profit_and_loss / total_inv_value * 100) if total_inv_value != 0 else 0
    )

    return {
        "totalholdingvalue": total_holding_value,
        "totalinvvalue": total_inv_value,
        "totalprofitandloss": total_profit_and_loss,
        "totalpnlpercentage": total_pnl_percentage,
    }


def transform_holdings_data(holdings_data):
    transformed_data = []
    for holdings in holdings_data["Data"]:
        buyvalue = float(holdings.get("AvgRate", 0.0)) * float(holdings.get("Quantity", 0.0))
        ltpvalue = float(holdings.get("CurrentPrice", 0.0)) * float(holdings.get("Quantity", 0.0))

        pnl = ltpvalue - buyvalue
        pnlpercent = (ltpvalue - buyvalue) / buyvalue * 100

        transformed_position = {
            "symbol": holdings.get("Symbol", ""),
            "exchange": holdings.get("Exch", ""),
            "quantity": holdings.get("Quantity", 0),
            "product": "CNC",
            "pnl": round(pnl, 2),
            "pnlpercent": round(pnlpercent, 2),
        }
        transformed_data.append(transformed_position)
    return transformed_data

```


---

# FILE: broker\fivepaisa\mapping\transform_data.py

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
        "OrderType": map_action(data["action"].upper()),
        "Exchange": map_exchange(data["exchange"]),
        "ExchangeType": map_exchange_type(data["exchange"]),
        "ScripCode": token,
        # "ScriData": symbol,
        # "iOrderValidity": "0",
        "Price": float(data.get("price", "0")),
        "Qty": int(data["quantity"]),
        "StopLossPrice": float(data.get("trigger_price", "0")),
        "DisQty": int(data.get("disclosed_quantity", "0")),
        "IsIntraday": True if data.get("product") == "MIS" else False,
        "AHPlaced": "N",  # AMO Order by default NO
        "RemoteOrderID": "OpenAlgo",
        # "AppSource": "7044"
    }

    return transformed


def transform_modify_order_data(data):
    # Handle empty trigger_price by providing a default of "0" and checking if it's empty
    trigger_price = data.get("trigger_price", "0")
    trigger_price = "0" if trigger_price == "" else trigger_price

    # Handle empty price
    price = data.get("price", "0")
    price = "0" if price == "" else price

    # FivePaisa requires a minimal set of fields for order modification per their documentation
    # Only include fields that are explicitly needed
    transformed = {
        "ExchOrderID": data.get("exchange_order_id", ""),  # The actual exchange order ID
        "Price": price,
        "Qty": data.get("quantity", "0"),
        "StopLossPrice": trigger_price,
        "DisQty": data.get("disclosed_quantity", "0"),
    }

    # Remove empty fields to keep the payload clean
    return {k: v for k, v in transformed.items() if v is not None and v != ""}


def map_action(action):
    """
    Maps the new action to the existing order type.
    """
    action_mapping = {"BUY": "B", "SELL": "S"}
    return action_mapping.get(action)


def map_exchange(exchange):
    """
    Maps the new exchange to the existing exchange
    """
    exchange_mapping = {
        "NSE": "N",
        "BSE": "B",
        "NFO": "N",
        "BFO": "B",
        "CDS": "N",
        "BCD": "B",
        "MCX": "M",
        "NSE_INDEX": "N",  # NSE indices use same exchange code as NSE
        "BSE_INDEX": "B",  # BSE indices use same exchange code as BSE
    }
    return exchange_mapping.get(exchange)


def map_exchange_type(exchange):
    """
    Maps the new exchange to the existing exchange type
    """
    exchange_mapping_type = {
        "NSE": "C",
        "BSE": "C",
        "NFO": "D",
        "BFO": "D",
        "CDS": "U",
        "BCD": "U",
        "MCX": "D",
        "NSE_INDEX": "C",  # Indices use Cash type in Fivepaisa scrip master
        "BSE_INDEX": "C",  # Indices use Cash type in Fivepaisa scrip master
    }
    return exchange_mapping_type.get(exchange)


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
        "CNC": "D",
        "NRML": "D",
        "MIS": "I",
    }
    return product_type_mapping.get(product, "I")  # Default to DELIVERY if not found


def map_variety(pricetype):
    """
    Maps the pricetype to the existing order variety.
    """
    variety_mapping = {"MARKET": "NORMAL", "LIMIT": "NORMAL", "SL": "STOPLOSS", "SL-M": "STOPLOSS"}
    return variety_mapping.get(pricetype, "NORMAL")  # Default to DELIVERY if not found


# Function to map Exch and ExchType to exchange names with additional conditions
def reverse_map_exchange(Exch, ExchType):
    exchange_mapping = {
        ("N", "C"): "NSE",
        ("B", "C"): "BSE",
        ("N", "D"): "NFO",
        ("B", "D"): "BFO",
        ("N", "U"): "CDS",
        ("B", "U"): "BCD",
        ("M", "D"): "MCX",
        # Add other mappings as needed
    }

    return exchange_mapping.get((Exch, ExchType))


def reverse_map_product_type(product, exchange):
    """
    Maps the new product type to the existing product type based on the exchange.
    """
    if exchange in ["NSE", "BSE"]:
        reverse_product_type_mapping = {
            "D": "CNC",
            "I": "MIS",
        }
    else:
        reverse_product_type_mapping = {
            "D": "NRML",
            "I": "MIS",
        }

    return reverse_product_type_mapping.get(product)

```
