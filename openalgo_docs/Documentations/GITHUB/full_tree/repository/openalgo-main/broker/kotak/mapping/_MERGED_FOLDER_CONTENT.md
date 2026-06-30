# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\kotak\mapping



---

# FILE: broker\kotak\mapping\margin_data.py

```py
# Mapping OpenAlgo API Request https://openalgo.in/docs
# Mapping Kotak Neo Margin API

from broker.kotak.mapping.transform_data import (
    map_order_type,
    map_product_type,
    reverse_map_exchange,
)
from database.token_db import get_token
from utils.logging import get_logger

logger = get_logger(__name__)


def transform_margin_position(position):
    """
    Transform a single OpenAlgo margin position to Kotak margin format.

    Note: Kotak margin API accepts only one order at a time, not a batch.

    Args:
        position: Position in OpenAlgo format

    Returns:
        Dict in Kotak margin format or None if transformation fails
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
        exchange_segment = reverse_map_exchange(position["exchange"])
        if not exchange_segment:
            logger.warning(f"Invalid exchange: {position['exchange']}")
            return None

        # Map transaction type
        transaction_type = "B" if position["action"].upper() == "BUY" else "S"

        # Transform the position (all values must be strings for Kotak API)
        transformed = {
            "brkName": "KOTAK",
            "brnchId": "ONLINE",
            "exSeg": exchange_segment,
            "prc": str(position.get("price", "0")),
            "prcTp": map_order_type(position["pricetype"]),
            "prod": map_product_type(position["product"]),
            "qty": str(position["quantity"]),
            "tok": str(token),
            "trnsTp": transaction_type,
        }

        return transformed

    except Exception as e:
        logger.error(f"Error transforming position: {position}, Error: {e}")
        return None


def parse_margin_response(response_data):
    """
    Parse Kotak margin response to OpenAlgo standard format.

    Args:
        response_data: Raw response from Kotak API

    Returns:
        Standardized margin response
    """
    try:
        if not response_data or not isinstance(response_data, dict):
            return {"status": "error", "message": "Invalid response from broker"}

        # Check if the response status is Ok
        if response_data.get("stat") != "Ok":
            error_message = response_data.get("errMsg", "Failed to calculate margin")
            return {"status": "error", "message": error_message}

        # Extract margin data
        # Kotak returns: avlMrgn, reqdMrgn, ordMrgn, mrgnUsd, rmsVldtd, etc.
        total_margin_required = float(response_data.get("reqdMrgn", 0))

        # Return standardized format matching OpenAlgo API specification
        return {
            "status": "success",
            "data": {
                "total_margin_required": total_margin_required,
                "span_margin": 0,  # Kotak doesn't provide separate span margin
                "exposure_margin": 0,  # Kotak doesn't provide separate exposure margin
            },
        }

    except Exception as e:
        logger.error(f"Error parsing margin response: {e}")
        return {"status": "error", "message": f"Failed to parse margin response: {str(e)}"}


def parse_batch_margin_response(responses):
    """
    Parse multiple Kotak margin responses and aggregate them.

    Args:
        responses: List of individual margin responses

    Returns:
        Aggregated margin response
    """
    try:
        total_required_margin = 0

        for response in responses:
            if response.get("status") == "success":
                data = response.get("data", {})
                total_required_margin += data.get("total_margin_required", 0)

        # Return standardized format matching OpenAlgo API specification
        return {
            "status": "success",
            "data": {
                "total_margin_required": total_required_margin,
                "span_margin": 0,  # Kotak doesn't provide separate span margin
                "exposure_margin": 0,  # Kotak doesn't provide separate exposure margin
            },
        }

    except Exception as e:
        logger.error(f"Error parsing batch margin response: {e}")
        return {"status": "error", "message": f"Failed to parse batch margin response: {str(e)}"}

```


---

# FILE: broker\kotak\mapping\order_data.py

```py
import json

from broker.kotak.mapping.transform_data import map_exchange
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
    # Check if 'data' is None
    # if order_data has key 'data' and its value is None

    if order_data["stat"] == "Not_Ok":
        logger.info("No data available.")
        order_data = {}  # or set it to an empty list if it's supposed to be a list
        return order_data

    if order_data["data"] is None:
        # Handle the case where there is no data
        # For example, you might want to display a message to the user
        # or pass an empty list or dictionary to the template.
        logger.info("No data available.")
        order_data = {}  # or set it to an empty list if it's supposed to be a list
    else:
        order_data = order_data["data"]

    if order_data:
        for order in order_data:
            # Extract the instrument_token and exchange for the current order
            symboltoken = order["tok"]
            exchange = map_exchange(order["exSeg"])
            order["exSeg"] = exchange

            # Use the get_symbol function to fetch the symbol from the database
            symbol_from_db = get_symbol(symboltoken, exchange)

            # Check if a symbol was found; if so, update the trading_symbol in the current order
            if symbol_from_db:
                order["trdSym"] = symbol_from_db
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
            if order["trnsTp"] == "B":
                order["trnsTp"] = "BUY"
                total_buy_orders += 1
            elif order["trnsTp"] == "S":
                order["trnsTp"] = "SELL"
                total_sell_orders += 1

            # Normalize "trigger pending" to "open" for UI compatibility
            if order["ordSt"] == "trigger pending":
                order["ordSt"] = "open"

            # Count orders based on their status
            if order["ordSt"] == "complete":
                total_completed_orders += 1
            elif order["ordSt"] == "open":
                total_open_orders += 1
            elif order["ordSt"] == "rejected":
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
        if order.get("prcTp") == "MKT":
            order["prcTp"] = "MARKET"
        elif order.get("prcTp") == "L":
            order["prcTp"] = "LIMIT"
        elif order.get("prcTp") == "SL":
            order["prcTp"] = "SL"
        elif order.get("prcTp") == "SL-M":
            order["prcTp"] = "SL-M"

        # For limit orders, show the order price (prc) instead of average price (avgPrc)
        # avgPrc is only relevant for executed orders
        order_price = order.get("avgPrc", 0.0)
        if order.get("prcTp") in ["LIMIT", "SL"]:
            # If order is not executed/complete, use the limit price
            if order.get("ordSt") != "complete":
                order_price = order.get("prc", 0.0)

        transformed_order = {
            "symbol": order.get("trdSym", ""),
            "exchange": order.get("exSeg", ""),
            "action": order.get("trnsTp", ""),
            "quantity": order.get("qty", 0),
            "price": order_price,
            "trigger_price": order.get("trgPrc", 0.0),
            "pricetype": order.get("prcTp", ""),
            "product": order.get("prod", ""),
            "orderid": order.get("nOrdNo", ""),
            "order_status": order.get("ordSt", ""),
            "timestamp": order.get("ordEntTm", ""),
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
    if trade_data["stat"] == "Not_Ok":
        logger.info("No data available.")
        trade_data = {}  # or set it to an empty list if it's supposed to be a list
        return trade_data
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
            symbol = order["tok"]
            exchange = map_exchange(order["exSeg"])
            order["exSeg"] = exchange
            logger.info(f"{symbol}")
            logger.info(f"{exchange}")
            # Use the get_symbol function to fetch the symbol from the database
            symbol_from_db = get_symbol(symbol, exchange)
            logger.info(f"{symbol_from_db}")
            # Check if a symbol was found; if so, update the trading_symbol in the current order
            if symbol_from_db:
                order["trdSym"] = symbol_from_db
            else:
                logger.info(
                    f"Unable to find the symbol {symbol} and exchange {exchange}. Keeping original trading symbol."
                )

            # Map transaction type regardless of symbol lookup result
            if order["trnsTp"] == "B":
                order["trnsTp"] = "BUY"
            elif order["trnsTp"] == "S":
                order["trnsTp"] = "SELL"
    logger.info(f"{trade_data}")
    return trade_data


def transform_tradebook_data(tradebook_data):
    transformed_data = []

    for trade in tradebook_data:
        transformed_trade = {
            "symbol": trade.get("trdSym", ""),
            "exchange": trade.get("exSeg", ""),
            "product": trade.get("prod", ""),
            "action": trade.get("trnsTp", ""),
            "quantity": trade.get("fldQty", 0),
            "average_price": trade.get("avgPrc", 0.0),
            "trade_value": float(trade.get("fldQty", 0.0)) * float(trade.get("avgPrc", 0.0)),
            "orderid": trade.get("nOrdNo", ""),
            "timestamp": trade.get("exTm", ""),
        }
        transformed_data.append(transformed_trade)
    return transformed_data


def map_position_data(position_data):
    return map_order_data(position_data)


def transform_positions_data(positions_data):
    transformed_data = []
    for position in positions_data:
        transformed_position = {
            "symbol": position.get("trdSym", ""),
            "exchange": position.get("exSeg", ""),
            "product": position.get("prod", ""),
            "quantity": (int(position.get("flBuyQty", 0)) - int(position.get("flSellQty", 0)))
            + (int(position.get("cfBuyQty", 0)) - int(position.get("cfSellQty", 0))),
            "average_price": position.get("avgnetprice", 0.0),
        }
        buy_qty = float(position.get("flBuyQty", 0))
        sell_qty = float(position.get("flSellQty", 0))

        if transformed_position["quantity"] > 0 and buy_qty > 0:
            transformed_position["average_price"] = round(
                float(position.get("buyAmt", 0)) / buy_qty, 2
            )
        elif transformed_position["quantity"] < 0 and sell_qty > 0:
            transformed_position["average_price"] = round(
                float(position.get("sellAmt", 0)) / sell_qty, 2
            )
        elif transformed_position["quantity"] != 0:
            transformed_position["average_price"] = 0.0

        transformed_data.append(transformed_position)

    return transformed_data


def transform_holdings_data(holdings_data):
    transformed_data = []
    logger.info("Holdings Data")
    logger.info(f"{holdings_data}")
    for holding in holdings_data:
        transformed_position = {
            "symbol": holding.get("displaySymbol", ""),
            "exchange": holding.get("exchangeSegment", ""),
            "quantity": holding.get("quantity", 0),
            "product": holding.get("instrumentType", ""),
            "pnl": round(
                (float(holding.get("mktValue", 0.0)) - float(holding.get("holdingCost", 0.0))), 2
            ),
            "pnlpercent": round(
                (
                    (float(holding.get("mktValue", 0.0)) - float(holding.get("holdingCost", 0.0)))
                    / float(holding.get("holdingCost", 0.0))
                    * 100
                )
                if float(holding.get("holdingCost", 0.0)) != 0
                else 0,
                2,
            ),
        }

        transformed_data.append(transformed_position)
    logger.info("Holdings Data")
    logger.info(f"{transformed_data}")
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
    if portfolio_data.get("data") is None:
        logger.info("No data available.")
        # Return an empty structure or handle this scenario as needed
        return {}

    # Directly work with 'data' for clarity and simplicity
    holdings = portfolio_data["data"]

    # Modify 'product' field for each holding if applicable

    for portfolio in holdings:
        token = portfolio["instrumentToken"]

        exchange = map_exchange(portfolio["exchangeSegment"])
        portfolio["exchangeSegment"] = exchange
        symbol_from_db = get_symbol(token, exchange)

        # Check if a symbol was found; if so, update the trading_symbol in the current order
        if symbol_from_db:
            portfolio["symbol"] = symbol_from_db
        if portfolio["instrumentType"] == "Equity":
            portfolio["instrumentType"] = "CNC"  # Modify 'product' field
        else:
            logger.info("Kotak Portfolio - Product Value for Delivery Not Found or Changed.")

    # The function already works with 'data', which includes 'holdings' and 'totalholding',
    # so we can return 'data' directly without additional modifications.

    return holdings


def calculate_portfolio_statistics(holdings_data):
    totalholdingvalue = sum(item["mktValue"] for item in holdings_data)
    totalinvvalue = sum(item["holdingCost"] for item in holdings_data)
    totalprofitandloss = sum(item["mktValue"] - item["holdingCost"] for item in holdings_data)

    totalpnlpercentage = (totalprofitandloss / totalinvvalue) * 100 if totalinvvalue != 0 else 0

    # To avoid division by zero in the case when total_investment_value is 0
    totalpnlpercentage = round(totalpnlpercentage, 2)

    return {
        "totalholdingvalue": totalholdingvalue,
        "totalinvvalue": totalinvvalue,
        "totalprofitandloss": totalprofitandloss,
        "totalpnlpercentage": totalpnlpercentage,
    }

```


---

# FILE: broker\kotak\mapping\transform_data.py

```py
# Mapping OpenAlgo API Request https://openalgo.in/docs
# Mapping Kotak Neo API Parameters

from database.token_db import get_br_symbol
from utils.logging import get_logger

logger = get_logger(__name__)


def _fmt_price(value):
    """Kotak rejects '0.0' on numeric fields — emit '0' for zero, otherwise stringified value."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return str(value) if value is not None else "0"
    if f == 0:
        return "0"
    return str(value)


def transform_data(data, token):
    """
    Transforms the new API request structure to the current expected structure.
    ALL values must be strings for Kotak API.
    """
    symbol = get_br_symbol(data["symbol"], data["exchange"])

    order_type = map_order_type(data["pricetype"])
    action = data["action"].upper()

    transformed = {
        "am": "NO",
        "dq": str(data.get("disclosed_quantity", "0")),
        "es": reverse_map_exchange(data["exchange"]),
        "mp": "0",
        "pc": data.get("product", "MIS"),
        "pf": "N",
        "pr": _fmt_price(data.get("price", 0)),
        "pt": order_type,
        "qt": str(data["quantity"]),
        "rt": "DAY",
        "tp": _fmt_price(data.get("trigger_price", 0)),
        "ts": symbol,
        "tt": "B" if action == "BUY" else ("S" if action == "SELL" else "None"),
    }

    logger.info(f"Transformed order data: {transformed}")
    return transformed


def transform_modify_order_data(data, token):
    symbol = get_br_symbol(data["symbol"], data["exchange"])
    transformed = {
        "tk": str(token),
        "dq": str(data.get("disclosed_quantity", "0")),
        "es": reverse_map_exchange(data["exchange"]),
        "mp": "0",
        "dd": "NA",
        "vd": "DAY",
        "pc": data.get("product", "MIS"),
        "pr": _fmt_price(data.get("price", 0)),
        "pt": map_order_type(data["pricetype"]),
        "qt": str(data["quantity"]),
        "tp": _fmt_price(data.get("trigger_price", 0)),
        "ts": symbol,
        "no": str(data["orderid"]),
        "tt": "B" if data["action"] == "BUY" else ("S" if data["action"] == "SELL" else "None"),
    }
    return transformed


def map_order_type(pricetype):
    """
    Maps the new pricetype to the existing order type.
    """
    order_type_mapping = {"MARKET": "MKT", "LIMIT": "L", "SL": "SL", "SL-M": "SL-M"}
    return order_type_mapping.get(pricetype, "MARKET")  # Default to MARKET if not found


def map_product_type(product):
    """
    Maps the new product type to the existing product type.
    """
    product_type_mapping = {
        "CNC": "CNC",
        "NRML": "NRML",
        "MIS": "MIS",
    }
    return product_type_mapping.get(product)  # Default to DELIVERY if not found


def map_variety(pricetype):
    """
    Maps the pricetype to the existing order variety.
    """
    variety_mapping = {"MARKET": "NORMAL", "LIMIT": "NORMAL", "SL": "STOPLOSS", "SL-M": "STOPLOSS"}
    return variety_mapping.get(pricetype, "NORMAL")  # Default to DELIVERY if not found


def map_exchange(brexchange):
    """
    Maps the Broker Exchange to the OpenAlgo Exchange.
    """

    exchange_mapping = {
        "nse_cm": "NSE",
        "bse_cm": "BSE",
        "cde_fo": "CDS",
        "nse_fo": "NFO",
        "bse_fo": "BFO",
        "bcs_fo": "BCD",
        "mcx_fo": "MCX",
    }
    return exchange_mapping.get(brexchange)


def reverse_map_exchange(exchange):
    """
    Maps the Broker Exchange to the OpenAlgo Exchange.
    """

    exchange_mapping = {
        "NSE": "nse_cm",
        "BSE": "bse_cm",
        "CDS": "cde_fo",
        "NFO": "nse_fo",
        "BFO": "bse_fo",
        "BCD": "bcs_fo",
        "MCX": "mcx_fo",
    }
    return exchange_mapping.get(exchange)


def reverse_map_product_type(product):
    """
    Maps the new product type to the existing product type.
    """
    reverse_product_type_mapping = {
        "CNC": "CNC",
        "NRML": "NRML",
        "MIS": "MIS",
    }
    return reverse_product_type_mapping.get(product)

```
