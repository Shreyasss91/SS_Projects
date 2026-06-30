# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\definedge\mapping



---

# FILE: broker\definedge\mapping\__init__.py

```py
# DefinedGe Securities mapping modules

```


---

# FILE: broker\definedge\mapping\margin_data.py

```py
# Mapping OpenAlgo API Request https://openalgo.in/docs
# Mapping Definedge Span Calculator API

from broker.definedge.mapping.transform_data import map_exchange, map_product_type
from database.token_db import get_br_symbol, get_symbol_info
from utils.logging import get_logger

logger = get_logger(__name__)


def transform_margin_positions(positions):
    """
    Transform OpenAlgo margin positions to Definedge Span Calculator format.

    Args:
        positions: List of positions in OpenAlgo format

    Returns:
        List of positions in Definedge format
    """
    transformed_positions = []

    for position in positions:
        try:
            # Get broker symbol
            tradingsymbol = get_br_symbol(position["symbol"], position["exchange"])

            if not tradingsymbol:
                logger.warning(
                    f"Broker symbol not found for: {position['symbol']} on {position['exchange']}"
                )
                continue

            # Get symbol info from database which contains expiry, strike, option_type, name
            symbol_info = get_symbol_info(position["symbol"], position["exchange"])

            if not symbol_info:
                logger.warning(
                    f"Symbol info not found for: {position['symbol']} on {position['exchange']}"
                )
                continue

            # Extract details from symbol info (accessing object attributes, not dict)
            expiry = getattr(symbol_info, "expiry", "") or ""
            strike = getattr(symbol_info, "strike", "") or ""
            option_type = getattr(symbol_info, "instrumenttype", "") or ""  # CE or PE
            underlying_name = getattr(symbol_info, "name", "") or ""

            # Calculate open_buy_qty and open_sell_qty based on action
            action = position["action"].upper()
            quantity = int(position["quantity"])

            open_buy_qty = quantity if action == "BUY" else 0
            open_sell_qty = quantity if action == "SELL" else 0

            # Map product type
            product_type = map_product_type(position["product"])

            # Build the transformed position
            transformed = {
                "product_type": product_type,
                "exchange": map_exchange(position["exchange"]),
                "symbol_name": underlying_name,
                "tradingsymbol": tradingsymbol,
                "open_buy_qty": open_buy_qty,
                "open_sell_qty": open_sell_qty,
            }

            # Add expiry for derivatives
            if expiry:
                # Convert expiry format from DD-MMM-YY to DD-MMM-YYYY
                # The API expects format like "23-FEB-2023"
                # Database stores it as "23-FEB-23"
                if len(expiry) == 9 and expiry[7:9].isdigit():  # Format: DD-MMM-YY
                    year_suffix = expiry[7:9]
                    year_prefix = "20" if int(year_suffix) < 50 else "19"
                    expiry_full = f"{expiry[:7]}{year_prefix}{year_suffix}"
                    transformed["expiry"] = expiry_full
                else:
                    transformed["expiry"] = expiry

            # Add strike price for options
            if strike and strike != "":
                transformed["option_strike"] = str(int(float(strike)))

            # Add option type for options (CE/PE)
            if option_type and option_type in ["CE", "PE"]:
                transformed["option_type"] = option_type

            transformed_positions.append(transformed)

        except Exception as e:
            logger.error(f"Error transforming position: {position}, Error: {e}")
            continue

    return transformed_positions


def parse_margin_response(response_data):
    """
    Parse Definedge margin response to OpenAlgo standard format.

    Args:
        response_data: Raw response from Definedge API

    Returns:
        Standardized margin response
    """
    try:
        if not response_data or not isinstance(response_data, dict):
            return {"status": "error", "message": "Invalid response from broker"}

        # Check for error response
        if response_data.get("status") == "FAILURE" or response_data.get("status") == "ERROR":
            error_message = response_data.get("message", "Failed to calculate margin")
            return {"status": "error", "message": error_message}

        # Check for success
        if response_data.get("status") != "SUCCESS":
            return {
                "status": "error",
                "message": response_data.get("message", "Unknown error from broker"),
            }

        # Extract margin values from Definedge response
        span_margin = float(response_data.get("span", 0))
        exposure_margin = float(response_data.get("exposure", 0))
        total_margin_required = span_margin + exposure_margin

        # Return standardized OpenAlgo format
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

# FILE: broker\definedge\mapping\order_data.py

```py
import json

from database.token_db import get_oa_symbol, get_symbol
from utils.logging import get_logger

logger = get_logger(__name__)


def map_order_data(order_data):
    """
    Processes and modifies a list of order dictionaries for DefinedGe Securities.

    Parameters:
    - order_data: A dictionary containing order data from DefinedGe API

    Returns:
    - The modified order_data with updated 'tradingsymbol' fields
    """
    # Handle DefinedGe API response structure
    if isinstance(order_data, dict):
        if order_data.get("status") == "SUCCESS" and "orders" in order_data:
            orders = order_data["orders"]
        elif order_data.get("status") == "ERROR":
            logger.error(f"DefinedGe API error: {order_data.get('message', 'Unknown error')}")
            return []
        else:
            # Handle case where data might be directly in the response
            orders = order_data if isinstance(order_data, list) else []
    else:
        orders = order_data if order_data else []

    if orders:
        for order in orders:
            # Extract the exchange and symbol for the current order
            exchange = order.get("exchange", "")
            symbol = order.get("tradingsymbol", "")

            # Convert broker symbol to OpenAlgo format
            if symbol and exchange:
                oa_symbol = get_oa_symbol(brsymbol=symbol, exchange=exchange)
                if oa_symbol:
                    order["tradingsymbol"] = oa_symbol

                    # Map product types to OpenAlgo constants following Angel pattern
                    if (order["exchange"] == "NSE" or order["exchange"] == "BSE") and order.get(
                        "product_type"
                    ) == "NORMAL":
                        order["product_type"] = "CNC"

                    elif order.get("product_type") == "INTRADAY":
                        order["product_type"] = "MIS"

                    elif (
                        order["exchange"] in ["NFO", "MCX", "BFO", "CDS"]
                        and order.get("product_type") == "NORMAL"
                    ):
                        order["product_type"] = "NRML"
                else:
                    logger.info(
                        f"Symbol {symbol} on exchange {exchange} not found. Keeping original."
                    )

    return orders


def calculate_order_statistics(order_data):
    """
    Calculates statistics from DefinedGe order data.

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
            # Count buy and sell orders (DefinedGe uses 'order_type' field)
            order_type = order.get("order_type", "").upper()
            if order_type == "BUY":
                total_buy_orders += 1
            elif order_type == "SELL":
                total_sell_orders += 1

            # Count orders based on their status (DefinedGe status mapping)
            status = order.get("order_status", "").upper()
            if status in ["COMPLETE", "EXECUTED"]:
                total_completed_orders += 1
            elif status in ["OPEN", "PENDING"]:
                total_open_orders += 1
            elif status in ["REJECTED", "CANCELLED"]:
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
    """
    Transform DefinedGe order data to OpenAlgo format.

    Parameters:
    - orders: List of order dictionaries from DefinedGe API

    Returns:
    - List of transformed order dictionaries
    """
    # Handle single dictionary case
    if isinstance(orders, dict):
        orders = [orders]

    transformed_orders = []

    for order in orders:
        if not isinstance(order, dict):
            logger.warning(f"Expected a dict, but found a {type(order)}. Skipping this item.")
            continue

        # Map DefinedGe order status to OpenAlgo format
        status = order.get("order_status", "").upper()
        if status in ["COMPLETE", "EXECUTED"]:
            order_status = "complete"
        elif status in ["REJECTED"]:
            order_status = "rejected"
        elif status in ["TRIGGER PENDING"]:
            order_status = "trigger pending"
        elif status in ["OPEN", "PENDING"]:
            order_status = "open"
        elif status in ["CANCELLED"]:
            order_status = "cancelled"
        else:
            order_status = status.lower()

        transformed_order = {
            "symbol": order.get("tradingsymbol", ""),
            "exchange": order.get("exchange", ""),
            "action": order.get("order_type", ""),  # DefinedGe uses 'order_type' for BUY/SELL
            "quantity": order.get("quantity", 0),
            "price": order.get("price", 0.0),
            "trigger_price": order.get("trigger_price", 0.0),
            "pricetype": order.get("price_type", ""),  # DefinedGe uses 'price_type'
            "product": order.get("product_type", ""),  # DefinedGe uses 'product_type'
            "orderid": order.get("order_id", ""),
            "order_status": order_status,
            "timestamp": order.get("order_timestamp", order.get("timestamp", "")),
        }

        transformed_orders.append(transformed_order)

    return transformed_orders


def map_trade_data(trade_data):
    """
    Processes and modifies trade data from DefinedGe Securities.

    Parameters:
    - trade_data: A dictionary containing trade data from DefinedGe API

    Returns:
    - The modified trade_data with updated 'tradingsymbol' and 'product' fields
    """
    # Handle DefinedGe API response structure for trades
    if isinstance(trade_data, dict):
        if trade_data.get("status") == "SUCCESS" and "trades" in trade_data:
            trades = trade_data["trades"]
        elif trade_data.get("status") == "ERROR":
            logger.error(f"DefinedGe API error: {trade_data.get('message', 'Unknown error')}")
            return []
        else:
            # Handle case where data might be directly in the response
            trades = trade_data if isinstance(trade_data, list) else []
    else:
        trades = trade_data if trade_data else []

    if trades:
        for trade in trades:
            # Extract the exchange and symbol for the current trade
            exchange = trade.get("exchange", "")
            symbol = trade.get("tradingsymbol", "")

            # Convert broker symbol to OpenAlgo format
            if symbol and exchange:
                oa_symbol = get_oa_symbol(brsymbol=symbol, exchange=exchange)
                if oa_symbol:
                    trade["tradingsymbol"] = oa_symbol
                else:
                    logger.info(
                        f"Symbol {symbol} on exchange {exchange} not found. Keeping original."
                    )

            # Map product types to OpenAlgo constants (following OpenAlgo order constants)
            product_type = trade.get("product_type", "")
            if product_type == "INTRADAY":
                trade["product_type"] = "MIS"
            elif product_type == "NORMAL":
                if exchange in ["NSE", "BSE"]:
                    trade["product_type"] = "CNC"
                elif exchange in ["NFO", "MCX", "BFO", "CDS"]:
                    trade["product_type"] = "NRML"
            elif product_type == "CNC":
                trade["product_type"] = "CNC"

    return trades


def transform_tradebook_data(tradebook_data):
    """
    Transform DefinedGe tradebook data to OpenAlgo format.

    Parameters:
    - tradebook_data: List of trade dictionaries from DefinedGe API

    Returns:
    - List of transformed trade dictionaries matching OpenAlgo format
    """
    transformed_data = []

    for trade in tradebook_data:
        if not isinstance(trade, dict):
            logger.warning(f"Expected a dict, but found a {type(trade)}. Skipping this item.")
            continue

        # Extract quantity - ensure it's an integer
        quantity = int(trade.get("filled_qty", trade.get("quantity", 0)))

        # Get fill price (executed trade price) - Definedge returns this as 'fill_price'
        # If fill_price is 0 or not present, use average_traded_price or price as fallback
        fill_price = float(trade.get("fill_price", 0))
        if fill_price == 0:
            fill_price = float(trade.get("average_traded_price", trade.get("price", 0)))

        # Calculate trade value = quantity * fill_price
        trade_value = round(quantity * fill_price, 2)

        # Get timestamp - Definedge provides fill_time for executed trades
        timestamp = trade.get("fill_time", trade.get("exchange_time", ""))

        # Map product type to OpenAlgo format
        product_type = trade.get("product_type", "")
        if product_type == "INTRADAY":
            product_type = "MIS"
        elif product_type == "NORMAL":
            # Check exchange to determine if it's CNC or NRML
            exchange = trade.get("exchange", "")
            if exchange in ["NSE", "BSE"]:
                product_type = "CNC"
            else:
                product_type = "NRML"

        transformed_trade = {
            "symbol": trade.get("tradingsymbol", ""),
            "exchange": trade.get("exchange", ""),
            "product": product_type,  # Mapped to OpenAlgo constants
            "action": trade.get("order_type", "").upper(),  # BUY/SELL
            "quantity": quantity,
            "average_price": round(fill_price, 2),  # Using fill_price as average_price
            "trade_value": trade_value,  # Calculated value
            "orderid": trade.get("order_id", ""),
            "timestamp": timestamp,  # Using fill_time for executed trades
        }

        transformed_data.append(transformed_trade)

    return transformed_data


def map_position_data(position_data):
    """
    Processes and modifies position data from DefinedGe Securities.

    Parameters:
    - position_data: A dictionary containing position data from DefinedGe API

    Returns:
    - The modified position_data with updated 'tradingsymbol' and 'product_type' fields
    """
    # Handle DefinedGe API response structure for positions
    if isinstance(position_data, dict):
        if position_data.get("status") == "SUCCESS" and "positions" in position_data:
            positions = position_data["positions"]
        elif position_data.get("status") == "ERROR":
            logger.error(f"DefinedGe API error: {position_data.get('message', 'Unknown error')}")
            return []
        else:
            # Handle case where data might be directly in the response
            positions = position_data if isinstance(position_data, list) else []
    else:
        positions = position_data if position_data else []

    if positions:
        for position in positions:
            # Extract the exchange and symbol for the current position
            exchange = position.get("exchange", "")
            symbol = position.get("tradingsymbol", "")

            # Convert broker symbol to OpenAlgo format
            if symbol and exchange:
                oa_symbol = get_oa_symbol(brsymbol=symbol, exchange=exchange)
                if oa_symbol:
                    position["tradingsymbol"] = oa_symbol
                else:
                    logger.info(
                        f"Symbol {symbol} on exchange {exchange} not found. Keeping original."
                    )

            # Map product types to OpenAlgo constants
            product_type = position.get("product_type", "")
            if product_type == "INTRADAY":
                position["product_type"] = "MIS"
            elif product_type == "NORMAL":
                if exchange in ["NSE", "BSE"]:
                    position["product_type"] = "CNC"
                elif exchange in ["NFO", "MCX", "BFO", "CDS"]:
                    position["product_type"] = "NRML"
            elif product_type == "CNC":
                position["product_type"] = "CNC"

    return positions


def transform_positions_data(positions_data):
    """
    Transform DefinedGe positions data to OpenAlgo format.
    Following Angel's pattern for consistency.
    """
    transformed_data = []

    for position in positions_data:
        # Get net quantity to determine if position is closed
        net_qty = int(position.get("net_quantity", 0))

        # For closed positions (net_qty = 0), show realized P&L, otherwise show unrealized P&L
        if net_qty == 0:
            pnl = position.get("realized_pnl", 0.0)
        else:
            pnl = position.get("unrealized_pnl", 0.0)

        transformed_position = {
            "symbol": position.get("tradingsymbol", ""),
            "exchange": position.get("exchange", ""),
            "product": position.get(
                "product_type", ""
            ),  # Already mapped to MIS/CNC/NRML in map_position_data
            "quantity": net_qty,
            "average_price": position.get("net_averageprice", 0.0),
            "ltp": position.get("lastPrice", 0.0),
            "pnl": pnl,  # Shows realized P&L for closed, unrealized for open positions
        }
        transformed_data.append(transformed_position)

    return transformed_data


def map_portfolio_data(portfolio_data):
    """
    Processes and modifies a list of Portfolio dictionaries for DefinedGe Securities.

    Parameters:
    - portfolio_data: A dictionary containing portfolio data from DefinedGe API

    Returns:
    - The modified portfolio_data with updated 'tradingsymbol' fields
    """
    # Handle DefinedGe API response structure for portfolio/holdings
    if isinstance(portfolio_data, dict):
        if portfolio_data.get("status") == "SUCCESS" and "data" in portfolio_data:
            # DefinedGe returns holdings in 'data' array
            holdings_list = portfolio_data["data"]
            data = {"holdings": holdings_list}
        elif portfolio_data.get("status") == "ERROR":
            logger.error(f"DefinedGe API error: {portfolio_data.get('message', 'Unknown error')}")
            return {}
        else:
            # Handle case where data might be directly in the response
            data = portfolio_data
    else:
        data = portfolio_data if portfolio_data else {}

    # Check if holdings exist
    if not data.get("holdings"):
        logger.info("No holdings data available.")
        return data

    # Process holdings and update symbols
    for holding in data["holdings"]:
        # DefinedGe API returns tradingsymbol as an array of objects
        tradingsymbol_array = holding.get("tradingsymbol", [])

        if tradingsymbol_array and isinstance(tradingsymbol_array, list):
            # Use the first tradingsymbol entry (usually NSE)
            first_symbol_obj = tradingsymbol_array[0]
            exchange = first_symbol_obj.get("exchange", "")
            symbol = first_symbol_obj.get("tradingsymbol", "")

            # Add exchange and symbol fields to holding for compatibility
            holding["exchange"] = exchange
            holding["symbol"] = symbol

            # Convert broker symbol to OpenAlgo format
            if symbol and exchange:
                oa_symbol = get_oa_symbol(brsymbol=symbol, exchange=exchange)
                if oa_symbol:
                    holding["tradingsymbol"] = oa_symbol
                else:
                    holding["tradingsymbol"] = symbol
                    logger.info(
                        f"Symbol {symbol} on exchange {exchange} not found. Keeping original."
                    )
            else:
                holding["tradingsymbol"] = symbol

    return data


def calculate_portfolio_statistics(holdings_data):
    """
    Calculates portfolio statistics from DefinedGe holdings data.
    Following Angel's pattern for consistency.
    """
    # Initialize default values
    totalholdingvalue = 0
    totalinvvalue = 0
    totalprofitandloss = 0
    totalpnlpercentage = 0

    # Since Definedge doesn't provide totalholding summary,
    # we need to calculate from individual holdings
    if holdings_data.get("holdings"):
        for holding in holdings_data["holdings"]:
            # Get quantities
            dp_qty = float(holding.get("dp_qty", 0))
            t1_qty = float(holding.get("t1_qty", 0))
            total_qty = dp_qty + t1_qty

            # Skip if no holdings
            if total_qty == 0:
                continue

            # Get average buy price
            avg_buy_price = float(holding.get("avg_buy_price", 0))

            # Calculate investment value
            investment_value = total_qty * avg_buy_price
            totalinvvalue += investment_value

            # For current value, we need LTP which Definedge doesn't provide in holdings
            # In production, this should be fetched from market data
            # For now, use investment value as placeholder
            current_value = investment_value  # Should be total_qty * ltp
            totalholdingvalue += current_value

            # Calculate P&L (will be 0 with placeholder values)
            pnl = current_value - investment_value
            totalprofitandloss += pnl

        # Calculate percentage
        if totalinvvalue > 0:
            totalpnlpercentage = (totalprofitandloss / totalinvvalue) * 100

    return {
        "totalholdingvalue": round(totalholdingvalue, 2),
        "totalinvvalue": round(totalinvvalue, 2),
        "totalprofitandloss": round(totalprofitandloss, 2),
        "totalpnlpercentage": round(totalpnlpercentage, 2),
    }


def transform_holdings_data(holdings_data):
    """
    Transform DefinedGe holdings data to OpenAlgo format.
    Following Angel's pattern for consistency.
    """
    transformed_data = []

    # Get holdings from the data structure
    holdings = holdings_data.get("holdings", [])

    for holding in holdings:
        if not isinstance(holding, dict):
            logger.warning(f"Expected a dict, but found a {type(holding)}. Skipping this item.")
            continue

        # Get quantity - use dp_qty + t1_qty for total holding quantity
        dp_qty = float(holding.get("dp_qty", 0))
        t1_qty = float(holding.get("t1_qty", 0))
        total_qty = dp_qty + t1_qty

        # Skip if no holdings
        if total_qty == 0:
            continue

        # Get average buy price
        avg_buy_price = float(holding.get("avg_buy_price", 0))

        # Get symbol and exchange (already processed by map_portfolio_data)
        symbol = holding.get("tradingsymbol", "")
        exchange = holding.get("exchange", "")

        # Calculate investment value
        investment_value = total_qty * avg_buy_price

        # For current value, we need LTP - since Definedge doesn't provide it in holdings,
        # we'll need to get it from market data or use a placeholder
        # For now, calculate P&L as 0 since we don't have real-time price
        # This should be updated with actual market prices in production
        current_value = investment_value  # Placeholder - should be total_qty * ltp
        pnl = 0.0  # Placeholder - should be current_value - investment_value
        pnl_percent = 0.0  # Placeholder

        transformed_holding = {
            "symbol": symbol,
            "exchange": exchange,
            "quantity": int(total_qty),
            "product": "CNC",  # Holdings are always CNC (delivery)
            "pnl": round(pnl, 2),
            "pnlpercent": round(pnl_percent, 2),
        }

        transformed_data.append(transformed_holding)

    return transformed_data

```


---

# FILE: broker\definedge\mapping\symbol_map.py

```py
from utils.logging import get_logger

logger = get_logger(__name__)


def get_br_symbol(symbol, exchange):
    """Convert OpenAlgo symbol to DefinedGe Securities symbol format"""
    try:
        # DefinedGe uses similar symbol format to NSE/BSE
        # For equity symbols, remove -EQ suffix if present
        if exchange in ["NSE", "BSE"] and symbol.endswith("-EQ"):
            return symbol[:-3]

        # For derivatives, DefinedGe uses standard format
        return symbol

    except Exception as e:
        logger.error(f"Error converting symbol {symbol}: {e}")
        return symbol


def get_oa_symbol(symbol, exchange):
    """Convert DefinedGe Securities symbol to OpenAlgo symbol format"""
    try:
        # For equity symbols on NSE, add -EQ suffix
        if exchange == "NSE" and not any(x in symbol for x in ["FUT", "CE", "PE"]):
            return f"{symbol}-EQ"

        # For other exchanges and derivatives, return as is
        return symbol

    except Exception as e:
        logger.error(f"Error converting symbol {symbol}: {e}")
        return symbol

```


---

# FILE: broker\definedge\mapping\transform_data.py

```py
from utils.logging import get_logger

logger = get_logger(__name__)


def transform_data(data, token_id):
    """Transform OpenAlgo order data to DefinedGe Securities format"""
    from database.token_db import get_br_symbol

    try:
        # Get broker symbol format
        symbol = get_br_symbol(data["symbol"], data["exchange"])

        # Map OpenAlgo fields to DefinedGe fields based on API docs
        transformed_data = {
            "tradingsymbol": symbol,
            "exchange": map_exchange(data["exchange"]),
            "quantity": data["quantity"],
            "price": data.get("price", "0"),
            "price_type": map_price_type(data["pricetype"]),
            "product_type": map_product_type(data["product"]),
            "order_type": data["action"].upper(),
        }

        # Add optional fields based on order type
        if data.get("trigger_price") and data["pricetype"] in ["SL", "SL-M"]:
            transformed_data["trigger_price"] = data["trigger_price"]

        # Add disclosed quantity if provided
        if data.get("disclosed_quantity"):
            transformed_data["disclosed_quantity"] = data["disclosed_quantity"]

        logger.info(f"Transformed order data: {transformed_data}")
        return transformed_data

    except Exception as e:
        logger.error(f"Error transforming data: {e}")
        return data


def transform_modify_order_data(data, token_id):
    """Transform modify order data to DefinedGe format"""
    from database.token_db import get_br_symbol

    try:
        logger.info(f"Input modify order data: {data}")

        # Check if symbol already has broker format (-EQ suffix)
        if "-" in data["symbol"]:
            # Symbol is already in broker format, use it directly
            symbol = data["symbol"]
            logger.info(f"Symbol already in broker format: {symbol}")
        else:
            # Get broker symbol format
            symbol = get_br_symbol(data["symbol"], data["exchange"])
            logger.info(f"Broker symbol after conversion: {symbol}")

        # If symbol is None or empty, raise an error
        if not symbol:
            logger.error(f"Failed to get broker symbol for {data['symbol']} on {data['exchange']}")
            symbol = data["symbol"]  # Use original as fallback

        # Map DefinedGe API fields according to documentation
        transformed_data = {
            "order_id": data["orderid"],  # API expects 'order_id', not 'norenordno'
            "tradingsymbol": symbol,  # REQUIRED field
            "exchange": map_exchange(data["exchange"]),
            "quantity": str(data.get("quantity")),  # Ensure it's a string
            "price": str(data.get("price", "0")),  # Ensure it's a string
            "price_type": map_definedge_price_type(data.get("pricetype", "LIMIT")),
            "product_type": map_product_type_for_modify(data.get("product", "CNC")),
            "order_type": data.get("action", "BUY").upper(),  # BUY/SELL required
        }

        # Only add trigger_price if it's actually provided AND the order type requires it
        pricetype = data.get("pricetype", "LIMIT")
        trigger_price = data.get("trigger_price")

        # More robust filtering - only include trigger_price for stop loss orders with valid values
        if (
            trigger_price
            and trigger_price != "0"
            and trigger_price != ""
            and trigger_price != "0.0"
            and str(trigger_price).replace(".", "").replace("0", "")  # Not just zeros
            and pricetype in ["SL", "SL-M"]
        ):
            try:
                # Validate it's actually a number
                float(trigger_price)
                transformed_data["trigger_price"] = trigger_price
                logger.info(f"Added trigger_price: {trigger_price} for pricetype: {pricetype}")
            except (ValueError, TypeError):
                logger.warning(
                    f"Invalid trigger_price value: {trigger_price}, excluding from request"
                )
        else:
            logger.info(
                f"Excluding trigger_price - pricetype: {pricetype}, trigger_price: {trigger_price}"
            )

        # Add optional fields if provided
        if data.get("disclosed_quantity"):
            transformed_data["disclosed_quantity"] = data.get("disclosed_quantity")

        # Default values for required fields
        transformed_data["validity"] = "DAY"  # Default validity

        # Remove None values and empty strings, but keep required fields
        required_fields = [
            "order_id",
            "tradingsymbol",
            "exchange",
            "quantity",
            "price",
            "price_type",
            "product_type",
            "order_type",
        ]
        transformed_data = {
            k: v
            for k, v in transformed_data.items()
            if (k in required_fields) or (v is not None and v != "")
        }

        # Final safety check: Remove trigger_price if pricetype is not SL or SL-M
        final_pricetype = data.get("pricetype", "LIMIT")
        if final_pricetype not in ["SL", "SL-M"] and "trigger_price" in transformed_data:
            logger.warning(f"Removing trigger_price for non-SL order type: {final_pricetype}")
            del transformed_data["trigger_price"]

        logger.info(f"Final transformed modify order data: {transformed_data}")
        return transformed_data

    except Exception as e:
        logger.error(f"Error transforming modify order data: {e}")
        return data


def map_exchange(exchange):
    """Map OpenAlgo exchange to DefinedGe exchange"""
    exchange_mapping = {
        "NSE": "NSE",
        "BSE": "BSE",
        "NFO": "NFO",
        "BFO": "BFO",
        "CDS": "CDS",
        "MCX": "MCX",
    }
    return exchange_mapping.get(exchange, exchange)


def reverse_map_exchange(exchange):
    """Map DefinedGe exchange to OpenAlgo exchange"""
    reverse_mapping = {
        "NSE": "NSE",
        "BSE": "BSE",
        "NFO": "NFO",
        "BFO": "BFO",
        "CDS": "CDS",
        "MCX": "MCX",
    }
    return reverse_mapping.get(exchange, exchange)


def map_product_type(product):
    """Map OpenAlgo product type to DefinedGe product type"""
    product_mapping = {
        "MIS": "INTRADAY",
        "CNC": "NORMAL",
        "NRML": "NORMAL",
        "CO": "COVER_ORDER",
        "BO": "BRACKET_ORDER",
    }
    return product_mapping.get(product, "NORMAL")


def reverse_map_product_type(product):
    """Map DefinedGe product type to OpenAlgo product type"""
    reverse_mapping = {
        "INTRADAY": "MIS",
        "NORMAL": "CNC",  # For NSE/BSE cash segment
        "COVER_ORDER": "CO",
        "BRACKET_ORDER": "BO",
    }
    # Default based on exchange - NORMAL maps to CNC for cash, NRML for F&O
    return reverse_mapping.get(product, "CNC")


def map_price_type(pricetype):
    """Map OpenAlgo price type to DefinedGe price type"""
    price_mapping = {
        "MARKET": "MARKET",
        "LIMIT": "LIMIT",
        "SL": "STOP_LOSS",
        "SL-M": "STOP_LOSS_MARKET",
    }
    return price_mapping.get(pricetype, "LIMIT")


def map_definedge_price_type(pricetype):
    """Map OpenAlgo price type to DefinedGe API price type (for modify order)"""
    price_mapping = {"MARKET": "MARKET", "LIMIT": "LIMIT", "SL": "SL-LIMIT", "SL-M": "SL-MARKET"}
    return price_mapping.get(pricetype, "LIMIT")


def map_product_type_for_modify(product):
    """Map OpenAlgo product type to DefinedGe product type for modify order"""
    product_mapping = {
        "MIS": "INTRADAY",
        "CNC": "CNC",  # DefinedGe modify API expects CNC for equity
        "NRML": "NORMAL",
    }
    return product_mapping.get(product, "CNC")


def reverse_map_price_type(pricetype):
    """Map DefinedGe price type to OpenAlgo price type"""
    reverse_mapping = {
        "MARKET": "MARKET",
        "LIMIT": "LIMIT",
        "STOP_LOSS": "SL",
        "STOP_LOSS_MARKET": "SL-M",
    }
    return reverse_mapping.get(pricetype, "LIMIT")


def map_order_status(status):
    """Map DefinedGe order status to OpenAlgo status"""
    status_mapping = {
        "COMPLETE": "COMPLETE",
        "OPEN": "OPEN",
        "PENDING": "PENDING",
        "CANCELLED": "CANCELLED",
        "REJECTED": "REJECTED",
        "PARTIALLY_FILLED": "OPEN",
    }
    return status_mapping.get(status, status)


def transform_order_data(order):
    """Transform DefinedGe order data to OpenAlgo format"""
    try:
        transformed_order = {
            "symbol": order.get("tradingsymbol", ""),
            "exchange": reverse_map_exchange(order.get("exchange", "")),
            "action": order.get("order_type", "").lower(),
            "quantity": order.get("quantity", "0"),
            "price": order.get("price", "0"),
            "pricetype": reverse_map_price_type(order.get("price_type", "LIMIT")),
            "product": reverse_map_product_type(order.get("product_type", "NORMAL")),
            "orderid": order.get("order_id", ""),
            "status": map_order_status(order.get("order_status", "")),
            "timestamp": order.get("order_entry_time", ""),
            "filled_qty": order.get("filled_qty", "0"),
            "pending_qty": order.get("pending_qty", "0"),
            "average_price": order.get("average_traded_price", "0"),
        }

        return transformed_order

    except Exception as e:
        logger.error(f"Error transforming order data: {e}")
        return order


def transform_position_data(position):
    """Transform DefinedGe position data to OpenAlgo format"""
    try:
        transformed_position = {
            "symbol": position.get("tradingsymbol", ""),
            "exchange": reverse_map_exchange(position.get("exchange", "")),
            "product": reverse_map_product_type(position.get("product_type", "NORMAL")),
            "quantity": position.get("net_quantity", "0"),
            "average_price": position.get("net_averageprice", "0"),
            "pnl": position.get("unrealized_pnl", "0"),
            "realized_pnl": position.get("realized_pnl", "0"),
            "last_price": position.get("lastPrice", "0"),
        }

        return transformed_position

    except Exception as e:
        logger.error(f"Error transforming position data: {e}")
        return position


def transform_holding_data(holding):
    """Transform DefinedGe holding data to OpenAlgo format"""
    try:
        # DefinedGe holdings have multiple trading symbols for different exchanges
        trading_symbols = holding.get("tradingsymbol", [])

        # Use NSE symbol if available, otherwise use first available
        symbol_info = None
        for ts in trading_symbols:
            if ts.get("exchange") == "NSE":
                symbol_info = ts
                break

        if not symbol_info and trading_symbols:
            symbol_info = trading_symbols[0]

        if symbol_info:
            transformed_holding = {
                "symbol": symbol_info.get("tradingsymbol", ""),
                "exchange": symbol_info.get("exchange", ""),
                "quantity": holding.get("t1_qty", "0"),
                "average_price": holding.get("avg_buy_price", "0"),
                "isin": symbol_info.get("isin", ""),
                "product": "CNC",
            }
        else:
            transformed_holding = {
                "symbol": "",
                "exchange": "",
                "quantity": "0",
                "average_price": "0",
                "isin": "",
                "product": "CNC",
            }

        return transformed_holding

    except Exception as e:
        logger.error(f"Error transforming holding data: {e}")
        return holding

```
