# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\motilal\mapping



---

# FILE: broker\motilal\mapping\margin_data.py

```py
# Mapping OpenAlgo API Request https://openalgo.in/docs
# Mapping Motilal Oswal Margin API - See Motilal_Oswal.md documentation
# Note: Motilal Oswal does not provide a margin calculator API.

from utils.logging import get_logger

logger = get_logger(__name__)


def transform_margin_positions(positions):
    """
    Transform OpenAlgo margin position format to Motilal Oswal margin format.

    Note: Motilal Oswal does not provide a margin calculator API.
    This function is a placeholder for API consistency.

    Args:
        positions: List of positions in OpenAlgo format

    Returns:
        Empty list (API not supported)
    """
    logger.warning("Motilal Oswal does not provide margin calculator API")
    return []


def parse_margin_response(response_data):
    """
    Parse margin response.

    Note: Motilal Oswal does not provide a margin calculator API.
    This function is a placeholder for API consistency.

    Args:
        response_data: Response data

    Returns:
        Error dict (API not supported)
    """
    return {"status": "error", "message": "Motilal Oswal does not support margin calculator API"}

```


---

# FILE: broker\motilal\mapping\order_data.py

```py
import json

from broker.motilal.mapping.transform_data import reverse_map_exchange
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
            motilal_exchange = order["exchange"]
            # Convert Motilal exchange (NSEFO) to OpenAlgo exchange (NFO) for database lookup
            openalgo_exchange = reverse_map_exchange(motilal_exchange)

            # Use the get_symbol function to fetch the symbol from the database
            # Use OpenAlgo exchange format for lookup
            symbol_from_db = get_symbol(symboltoken, openalgo_exchange)

            # Check if a symbol was found; if so, update the trading_symbol in the current order
            if symbol_from_db:
                order["symbol"] = symbol_from_db  # Motilal uses 'symbol' field
                # Convert exchange to OpenAlgo format for display
                order["exchange"] = openalgo_exchange

                # Map Motilal product types to OpenAlgo format
                if openalgo_exchange in ["NSE", "BSE"]:
                    if order["producttype"] == "DELIVERY":
                        order["producttype"] = "CNC"
                    elif order["producttype"] == "VALUEPLUS":
                        order["producttype"] = "MIS"  # Motilal uses VALUEPLUS for margin intraday

                elif openalgo_exchange in ["NFO", "MCX", "CDS", "BFO"]:
                    # F&O segment product mapping
                    if order["producttype"] == "NORMAL":
                        order["producttype"] = "MIS"  # Motilal uses NORMAL for F&O intraday
                    elif order["producttype"] == "VALUEPLUS":
                        order["producttype"] = "NRML"
            else:
                logger.info(
                    f"Symbol not found for token {symboltoken} and exchange {openalgo_exchange}. Keeping original trading symbol."
                )
                # Still convert exchange to OpenAlgo format
                order["exchange"] = openalgo_exchange

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
            # Count buy and sell orders - Motilal uses 'buyorsell' field
            if order.get("buyorsell", "").upper() == "BUY":
                total_buy_orders += 1
            elif order.get("buyorsell", "").upper() == "SELL":
                total_sell_orders += 1

            # Count orders based on their status - Motilal uses 'orderstatus' field
            order_status = order.get("orderstatus", "").lower()
            if order_status == "traded" or order_status == "complete":
                total_completed_orders += 1
            elif order_status in ["confirm", "sent", "open"]:
                total_open_orders += 1
            elif order_status in ["rejected", "error"]:
                total_rejected_orders += 1
            # Note: 'cancel' status orders are not counted in statistics (following Angel One implementation)

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

        # Map Motilal order types to OpenAlgo standard format
        # Motilal returns: Market, Limit, Stoploss (title case)
        # OpenAlgo standard: MARKET, LIMIT, SL, SL-M (uppercase)
        ordertype = order.get("ordertype", "")
        if ordertype == "Stoploss" or ordertype == "STOPLOSS":
            # Determine if it's SL or SL-M based on trigger price
            if float(order.get("triggerprice", 0)) > 0:
                ordertype = "SL"
            else:
                ordertype = "SL-M"
        elif ordertype == "Market":
            ordertype = "MARKET"
        elif ordertype == "Limit":
            ordertype = "LIMIT"
        else:
            # Default to uppercase if unrecognized
            ordertype = ordertype.upper()

        # Map Motilal order status to OpenAlgo standard format
        # Motilal returns: Traded, Confirm, Sent, Error, Rejected, Cancel (title case)
        # OpenAlgo standard: complete, open, rejected, cancelled (lowercase)
        order_status = order.get("orderstatus", "")
        if order_status == "Traded" or order_status == "Complete":
            order_status = "complete"
        elif order_status in ["Confirm", "Sent", "Open"]:
            order_status = "open"
        elif order_status in ["Rejected", "Error"]:
            order_status = "rejected"
        elif order_status == "Cancel":
            order_status = "cancelled"
        else:
            # Keep lowercase for standard format
            order_status = order_status.lower()

        # Determine which price to use:
        # - For executed orders: use averageprice (execution price)
        # - For pending/open orders: use price (order price)
        avg_price = float(order.get("averageprice", 0.0))
        order_price = float(order.get("price", 0.0))

        # Log for debugging price issues
        if order_price == 0 and ordertype == "LIMIT" and order_status == "open":
            logger.warning("LIMIT order with open status has price=0.")
            logger.warning(f"Order ID: {order.get('uniqueorderid')}")
            logger.warning(f"Symbol: {order.get('symbol')}")
            logger.warning(f"Order Type: {order.get('ordertype')}")
            logger.warning(f"Order Status: {order.get('orderstatus')}")
            logger.warning(
                f"Raw price field value: '{order.get('price')}' (type: {type(order.get('price'))})"
            )
            logger.warning(
                f"Raw averageprice field value: '{order.get('averageprice')}' (type: {type(order.get('averageprice'))})"
            )
            logger.warning(f"Full raw order data: {json.dumps(order, indent=2)}")

        # If averageprice is 0, use the order price (for pending orders)
        display_price = avg_price if avg_price > 0 else order_price

        transformed_order = {
            "symbol": order.get("symbol", ""),  # Motilal uses 'symbol'
            "exchange": order.get("exchange", ""),
            "action": order.get("buyorsell", "").upper(),  # Ensure uppercase BUY/SELL
            "quantity": order.get("orderqty", 0),  # Motilal uses 'orderqty'
            "price": round(float(display_price), 2),  # Format to 2 decimal places
            "trigger_price": round(
                float(order.get("triggerprice", 0.0)), 2
            ),  # Format to 2 decimal places
            "pricetype": ordertype,
            "product": order.get("producttype", ""),
            "orderid": order.get("uniqueorderid", ""),  # Motilal uses 'uniqueorderid'
            "order_status": order_status,  # Standardized lowercase status
            "timestamp": order.get("lastmodifiedtime", ""),  # Motilal uses 'lastmodifiedtime'
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
            symbol = order["symbol"]  # Motilal uses 'symbol'
            motilal_exchange = order["exchange"]
            # Convert Motilal exchange to OpenAlgo exchange for database lookup
            openalgo_exchange = reverse_map_exchange(motilal_exchange)

            # Use the get_symbol function to fetch the symbol from the database
            symbol_from_db = get_oa_symbol(symbol, openalgo_exchange)

            # Check if a symbol was found; if so, update the trading_symbol in the current order
            if symbol_from_db:
                order["symbol"] = symbol_from_db
                # Convert exchange to OpenAlgo format
                order["exchange"] = openalgo_exchange

                # Map Motilal product types to OpenAlgo format
                if openalgo_exchange in ["NSE", "BSE"]:
                    if order["producttype"] == "DELIVERY":
                        order["producttype"] = "CNC"
                    elif order["producttype"] == "VALUEPLUS":
                        order["producttype"] = "MIS"  # Motilal uses VALUEPLUS for margin intraday

                elif openalgo_exchange in ["NFO", "MCX", "CDS", "BFO"]:
                    if order["producttype"] == "NORMAL":
                        order["producttype"] = "MIS"  # Motilal uses NORMAL for F&O intraday
                    elif order["producttype"] == "VALUEPLUS":
                        order["producttype"] = "NRML"
            else:
                logger.info(
                    f"Unable to find the symbol {symbol} and exchange {openalgo_exchange}. Keeping original trading symbol."
                )
                order["exchange"] = openalgo_exchange

    return trade_data


def transform_tradebook_data(tradebook_data):
    """
    Transforms Motilal Oswal tradebook data to OpenAlgo format.
    Motilal field names: symbol, buyorsell, tradeqty, tradeprice, tradetime, etc.
    """
    transformed_data = []
    for trade in tradebook_data:
        transformed_trade = {
            "symbol": trade.get("symbol", ""),  # Motilal uses 'symbol'
            "exchange": trade.get("exchange", ""),
            "product": trade.get("producttype", ""),
            "action": trade.get("buyorsell", ""),  # Motilal uses 'buyorsell'
            "quantity": trade.get("tradeqty", 0),  # Motilal uses 'tradeqty'
            "average_price": trade.get("tradeprice", 0.0),  # Motilal uses 'tradeprice'
            "trade_value": trade.get("tradevalue", 0),
            "orderid": trade.get("uniqueorderid", ""),  # Motilal uses 'uniqueorderid'
            "timestamp": trade.get("tradetime", ""),  # Motilal uses 'tradetime'
        }
        transformed_data.append(transformed_trade)
    return transformed_data


def map_position_data(position_data):
    """
    Processes and modifies position data based on specific conditions.
    Motilal uses 'productname' field instead of 'producttype' for positions.

    Parameters:
    - position_data: Response from Motilal positions API

    Returns:
    - Modified position_data with updated symbols and product types
    """
    # Check if position_data is empty or doesn't have 'data' key
    if not position_data or "data" not in position_data or position_data["data"] is None:
        logger.info("No position data available.")
        return []

    position_data_list = position_data["data"]
    logger.info(f"Processing {len(position_data_list)} positions")

    if position_data_list:
        for position in position_data_list:
            # Extract the symboltoken and exchange for the current position
            symboltoken = position.get("symboltoken")
            motilal_exchange = position.get("exchange")
            # Convert Motilal exchange to OpenAlgo exchange for database lookup
            openalgo_exchange = reverse_map_exchange(motilal_exchange)

            # Use the get_symbol function to fetch the symbol from the database
            symbol_from_db = get_symbol(symboltoken, openalgo_exchange)

            # Check if a symbol was found; if so, update the symbol in the current position
            if symbol_from_db:
                position["symbol"] = symbol_from_db
                # Convert exchange to OpenAlgo format
                position["exchange"] = openalgo_exchange

                # Map Motilal product types to OpenAlgo format
                # Motilal uses 'productname' field for positions instead of 'producttype'
                productname = position.get("productname", "")

                if openalgo_exchange in ["NSE", "BSE"]:
                    # Cash segment product mapping
                    if productname == "DELIVERY":
                        position["productname"] = "CNC"
                    elif productname == "VALUEPLUS":
                        position["productname"] = (
                            "MIS"  # Motilal uses VALUEPLUS for margin intraday
                        )

                elif openalgo_exchange in ["NFO", "MCX", "CDS", "BFO"]:
                    # F&O segment product mapping
                    if productname == "NORMAL":
                        position["productname"] = "MIS"  # Motilal uses NORMAL for F&O intraday
                    elif productname == "VALUEPLUS":
                        position["productname"] = "NRML"
            else:
                logger.info(
                    f"Symbol not found for token {symboltoken} and exchange {openalgo_exchange}. Keeping original symbol."
                )
                position["exchange"] = openalgo_exchange

    return position_data_list


def transform_positions_data(positions_data):
    """
    Transforms Motilal Oswal positions data to OpenAlgo format.
    Motilal doesn't have netqty - calculate from buyquantity and sellquantity.
    """
    transformed_data = []
    for position in positions_data:
        # Calculate net quantity from buy and sell quantities
        buyqty = int(position.get("buyquantity", 0))
        sellqty = int(position.get("sellquantity", 0))
        net_qty = buyqty - sellqty

        # Calculate average price (weighted average if needed)
        buyamt = float(position.get("buyamount", 0.0))
        sellamt = float(position.get("sellamount", 0.0))
        avg_price = 0.0
        if net_qty != 0:
            if net_qty > 0:  # Long position
                avg_price = buyamt / buyqty if buyqty > 0 else 0.0
            else:  # Short position
                avg_price = sellamt / sellqty if sellqty > 0 else 0.0

        transformed_position = {
            "symbol": position.get("symbol", ""),  # Motilal uses 'symbol'
            "exchange": position.get("exchange", ""),
            "product": position.get("productname", ""),  # Motilal uses 'productname'
            "quantity": net_qty,
            "average_price": avg_price,
            "ltp": position.get("LTP", 0.0),  # Motilal uses 'LTP'
            "pnl": position.get("marktomarket", 0.0)
            + position.get("bookedprofitloss", 0.0),  # Total P&L
        }
        transformed_data.append(transformed_position)
    return transformed_data


def transform_holdings_data(holdings_data):
    """
    Transforms Motilal Oswal holdings data to OpenAlgo format.
    Motilal holdings response has: scripname, dpquantity, buyavgprice, nsesymboltoken, bsescripcode
    """
    transformed_data = []
    # Motilal returns holdings directly in the data array
    holdings_list = (
        holdings_data if isinstance(holdings_data, list) else holdings_data.get("holdings", [])
    )

    for holdings in holdings_list:
        # Get the mapped OpenAlgo symbol and exchange from map_portfolio_data
        symbol = holdings.get("symbol", "")  # Already mapped by map_portfolio_data
        exchange = holdings.get("exchange", "NSE")  # Already determined by map_portfolio_data

        # Get quantity
        dp_qty = int(holdings.get("dpquantity", 0))

        # P&L calculation would need current LTP, which is not in holdings response
        # For now, set to 0.0

        transformed_position = {
            "symbol": symbol,
            "exchange": exchange,
            "quantity": dp_qty,
            "product": "CNC",  # Holdings are always CNC/DELIVERY
            "pnl": 0.0,  # Would need current price to calculate P&L
            "pnlpercent": 0.0,
        }
        transformed_data.append(transformed_position)
    return transformed_data


def map_portfolio_data(portfolio_data):
    """
    Processes Motilal Oswal portfolio/holdings data.
    Motilal returns holdings with nsesymboltoken and bsescripcode fields.

    Holdings structure:
    - scripname: Broker symbol (e.g., "RELAXO EQ")
    - dpquantity: Total quantity
    - buyavgprice: Average buy price
    - nsesymboltoken: NSE token
    - bsescripcode: BSE scrip code

    Parameters:
    - portfolio_data: A dictionary containing holdings data

    Returns:
    - The modified portfolio_data with mapped fields (OpenAlgo symbols and exchange).
    """
    # Log the raw response for debugging
    logger.info(
        f"Motilal Holdings API Response: status={portfolio_data.get('status')}, data_type={type(portfolio_data.get('data'))}"
    )

    # Motilal returns status as "SUCCESS" string
    if portfolio_data.get("status") != "SUCCESS":
        logger.warning(f"Holdings API returned non-SUCCESS status: {portfolio_data.get('status')}")
        return {"holdings": [], "totalholding": None}

    if portfolio_data.get("data") is None:
        logger.info("No holdings data available (data is None).")
        return {"holdings": [], "totalholding": None}

    # Directly work with 'data' for clarity and simplicity
    data = portfolio_data["data"]

    # Check if data is empty list
    if isinstance(data, list) and len(data) == 0:
        logger.info("Holdings data is empty list - no holdings found in API response.")
        return {"holdings": [], "totalholding": None}

    logger.info(
        f"Processing {len(data) if isinstance(data, list) else 'unknown'} holdings from Motilal API"
    )

    # Motilal returns holdings as a list directly
    if isinstance(data, list):
        for idx, holding in enumerate(data):
            logger.info(
                f"Processing holding {idx + 1}: scripname={holding.get('scripname')}, dpquantity={holding.get('dpquantity')}"
            )

            # Determine exchange based on which token is available
            # Priority: NSE token first, then BSE scripcode
            nsesymboltoken = holding.get("nsesymboltoken")
            bsescripcode = holding.get("bsescripcode")

            logger.debug(
                f"Tokens for {holding.get('scripname')}: nsesymboltoken={nsesymboltoken}, bsescripcode={bsescripcode}"
            )

            exchange = None
            token = None

            # Check which token is available (non-zero, non-null)
            if nsesymboltoken and int(nsesymboltoken) > 0:
                exchange = "NSE"
                token = nsesymboltoken
            elif bsescripcode and int(bsescripcode) > 0:
                exchange = "BSE"
                token = bsescripcode
            else:
                # If no valid token, log and skip symbol lookup
                logger.warning(
                    f"No valid token found for holding: {holding.get('scripname', 'Unknown')}"
                )
                holding["symbol"] = holding.get("scripname", "")  # Keep broker symbol as fallback
                holding["exchange"] = "NSE"  # Default to NSE
                holding["product"] = "CNC"
                continue

            # Use get_symbol to fetch the OpenAlgo symbol from database
            symbol_from_db = get_symbol(token, exchange)

            if symbol_from_db:
                holding["symbol"] = symbol_from_db
                holding["exchange"] = exchange
                logger.info(
                    f"✓ Mapped holding: {holding.get('scripname')} (token {token} on {exchange}) -> {symbol_from_db}"
                )
            else:
                # If symbol not found in database, keep the scripname as fallback
                logger.warning(
                    f"Symbol not found in DB for token {token} on {exchange}. Using scripname: {holding.get('scripname', '')}"
                )
                holding["symbol"] = holding.get("scripname", "")
                holding["exchange"] = exchange

            # All holdings are CNC/DELIVERY product
            holding["product"] = "CNC"

        logger.info(f"Completed processing holdings. Total processed: {len(data)}")

    return {"holdings": data, "totalholding": None}  # Match expected structure


def calculate_portfolio_statistics(holdings_data):
    """
    Calculates portfolio statistics from holdings data.
    Motilal doesn't provide totalholding summary in the API response,
    so we return zeros for all statistics.
    """
    # Check if holdings_data has the expected structure
    if (
        not holdings_data
        or "totalholding" not in holdings_data
        or holdings_data["totalholding"] is None
    ):
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

# FILE: broker\motilal\mapping\transform_data.py

```py
# Mapping OpenAlgo API Request https://openalgo.in/docs
# Mapping Motilal Oswal Parameters - See Motilal_Oswal.md documentation

from database.token_db import get_br_symbol, get_symbol_info
from utils.logging import get_logger
from utils.mpp_slab import calculate_protected_price, get_instrument_type_from_symbol

logger = get_logger(__name__)


def map_exchange(exchange):
    """
    Maps OpenAlgo exchange names to Motilal Oswal exchange names.

    OpenAlgo uses: NSE, BSE, NFO, CDS, MCX, BFO
    Motilal uses: NSE, BSE, NSEFO, NSECD, MCX, BSEFO
    """
    exchange_mapping = {
        "NSE": "NSE",
        "BSE": "BSE",
        "NFO": "NSEFO",
        "CDS": "NSECD",
        "MCX": "MCX",
        "BFO": "BSEFO",
        "NSEFO": "NSEFO",  # Already in Motilal format
        "NSECD": "NSECD",  # Already in Motilal format
        "BSEFO": "BSEFO",  # Already in Motilal format
    }
    return exchange_mapping.get(exchange, exchange)


def reverse_map_exchange(exchange):
    """
    Reverse maps Motilal Oswal exchange names to OpenAlgo exchange names.
    """
    reverse_exchange_mapping = {
        "NSE": "NSE",
        "BSE": "BSE",
        "NSEFO": "NFO",
        "NSECD": "CDS",
        "MCX": "MCX",
        "BSEFO": "BFO",
    }
    return reverse_exchange_mapping.get(exchange, exchange)


def transform_data(data, token, auth_token=None):
    """
    Transforms the OpenAlgo API request structure to Motilal Oswal expected structure.

    Motilal blocks MARKET / SL-M orders on vendor (algo) channels with errorcode M01108
    ("Cannot place Market orders for Algo Orders"). To keep order intent intact we apply
    Market Price Protection (MPP) and convert:
        MARKET -> LIMIT  at LTP +/- slab%
        SL-M   -> STOPLOSS (SL) at trigger +/- slab%
    """
    symbol = get_br_symbol(data["symbol"], data["exchange"])
    openalgo_exchange = data["exchange"]
    motilal_exchange = map_exchange(openalgo_exchange)
    action = data["action"].upper()
    pricetype = data["pricetype"]

    price = data.get("price", "0")
    trigger_price = data.get("trigger_price", "0")
    order_type = map_order_type(pricetype)

    # MPP for MARKET orders: fetch LTP, compute protected limit price
    if pricetype == "MARKET":
        logger.info(
            f"MPP: MARKET order detected for Symbol={data['symbol']}, "
            f"Exchange={openalgo_exchange}, Action={action}"
        )
        try:
            if auth_token:
                from broker.motilal.api.data import BrokerData

                broker_data = BrokerData(auth_token)
                quote_data = broker_data.get_quotes(data["symbol"], openalgo_exchange)
                ltp = float(quote_data.get("ltp", 0)) if quote_data else 0

                if ltp > 0:
                    instrument_type = get_instrument_type_from_symbol(data["symbol"])
                    tick_size = None
                    symbol_info = get_symbol_info(data["symbol"], openalgo_exchange)
                    if symbol_info and symbol_info.tick_size:
                        tick_size = symbol_info.tick_size

                    protected_price = calculate_protected_price(
                        price=ltp,
                        action=action,
                        symbol=data["symbol"],
                        instrument_type=instrument_type,
                        tick_size=tick_size,
                    )
                    price = str(protected_price)
                    order_type = "LIMIT"
                    logger.info(
                        f"MPP Conversion Complete: Symbol={data['symbol']}, "
                        f"OrderType=MARKET->LIMIT, FinalPrice={protected_price}"
                    )
                else:
                    logger.warning(
                        f"MPP: LTP unavailable for {data['symbol']}, sending MARKET as-is"
                    )
            else:
                logger.warning(
                    f"MPP: No auth_token for {data['symbol']}, cannot fetch LTP"
                )
        except Exception as e:
            logger.error(
                f"MPP Error for MARKET {data['symbol']}: {e}. Sending MARKET as-is"
            )

    # MPP for SL-M orders: convert to STOPLOSS with protected limit price
    elif pricetype == "SL-M":
        try:
            tp = float(trigger_price)
        except (TypeError, ValueError):
            tp = 0.0
        if tp > 0:
            try:
                instrument_type = get_instrument_type_from_symbol(data["symbol"])
                tick_size = None
                symbol_info = get_symbol_info(data["symbol"], openalgo_exchange)
                if symbol_info and symbol_info.tick_size:
                    tick_size = symbol_info.tick_size

                protected_price = calculate_protected_price(
                    price=tp,
                    action=action,
                    symbol=data["symbol"],
                    instrument_type=instrument_type,
                    tick_size=tick_size,
                )
                price = str(protected_price)
                order_type = "STOPLOSS"
                logger.info(
                    f"MPP Conversion Complete: Symbol={data['symbol']}, "
                    f"OrderType=SL-M->STOPLOSS, Trigger={tp}, LimitPrice={protected_price}"
                )
            except Exception as e:
                logger.error(
                    f"MPP Error for SL-M {data['symbol']}: {e}. Sending SL-M as-is"
                )
        else:
            logger.warning(
                f"MPP: trigger_price=0 for SL-M {data['symbol']}, sending as-is"
            )

    # Basic mapping for Motilal Oswal
    transformed = {
        "apikey": data["apikey"],
        "symboltoken": token,
        "buyorsell": action,  # Motilal uses 'buyorsell' instead of 'transactiontype'
        "exchange": motilal_exchange,
        "ordertype": order_type,
        "producttype": map_product_type(
            data["product"], openalgo_exchange
        ),  # Pass OpenAlgo exchange for context
        "orderduration": "DAY",  # Motilal uses 'orderduration' instead of 'duration'
        "price": price,
        "triggerprice": trigger_price,
        "disclosedquantity": data.get("disclosed_quantity", "0"),
        "quantity": data["quantity"],
        "amoorder": "N",  # AMO-Order (Y or N)
        "algoid": "",  # Algo Id or Blank for Non-Algo Orders
        "goodtilldate": "",  # DD-MMM-YYYY format if GTD
        "tag": "",  # Echo back to identify order (max 10 characters)
        "participantcode": "",  # Participant Code if applicable
    }

    return transformed


def transform_modify_order_data(data, token, lastmodifiedtime, qtytradedtoday):
    """
    Transforms modify order data for Motilal Oswal API.
    Motilal uses different field names compared to Angel Broking.

    Args:
        data: OpenAlgo modify order request data
        token: Symbol token for the instrument
        lastmodifiedtime: Last modified time from order book (dd-MMM-yyyy HH:mm:ss format)
        qtytradedtoday: Quantity traded today from order book

    Returns:
        Dict containing Motilal-formatted modify order request
    """
    return {
        "uniqueorderid": data["orderid"],  # Motilal uses uniqueorderid
        "newordertype": map_order_type(data["pricetype"]),
        "neworderduration": "DAY",  # Motilal uses neworderduration
        "newprice": float(data.get("price", "0")),
        "newtriggerprice": float(data.get("trigger_price", "0")),
        "newquantityinlot": int(data["quantity"]),
        "newdisclosedquantity": int(data.get("disclosed_quantity", "0")),
        "newgoodtilldate": "",
        "lastmodifiedtime": lastmodifiedtime,  # Fetched from order book
        "qtytradedtoday": qtytradedtoday,  # Fetched from order book
    }


def map_order_type(pricetype):
    """
    Maps OpenAlgo pricetype to Motilal Oswal order type.
    Motilal supports: LIMIT, MARKET, STOPLOSS
    """
    order_type_mapping = {
        "MARKET": "MARKET",
        "LIMIT": "LIMIT",
        "SL": "STOPLOSS",
        "SL-M": "STOPLOSS",
    }
    return order_type_mapping.get(pricetype, "MARKET")  # Default to MARKET if not found


def map_product_type(product, exchange=None):
    """
    Maps OpenAlgo product type to Motilal Oswal product type based on exchange.
    Motilal supports: NORMAL, DELIVERY, VALUEPLUS, SELLFROMDP, BTST, MTF

    Product type mapping:
    For Cash Segment (NSE, BSE):
        - CNC (Cash and Carry) → DELIVERY (for delivery/holdings)
        - MIS (Margin Intraday Square off) → VALUEPLUS (for intraday margin trading)
        - NRML → VALUEPLUS (fallback for cash segment with margin)

    For F&O Segment (NFO, MCX, CDS, BFO):
        - NRML (Normal for F&O) → NORMAL
        - MIS → NORMAL (intraday F&O)
        - CNC → NORMAL (fallback for F&O segment)

    Note: VALUEPLUS is Motilal's margin product for intraday trading.
    Accounts may have specific product authorizations based on their configuration.

    Args:
        product: OpenAlgo product type (CNC, MIS, NRML)
        exchange: OpenAlgo exchange name (NSE, BSE, NFO, CDS, MCX, BFO)
    """
    # Determine if this is a cash segment or derivative segment
    # Using OpenAlgo exchange names
    is_cash_segment = exchange in ["NSE", "BSE"]
    is_fo_segment = exchange in ["NFO", "MCX", "CDS", "BFO", "NSEFO", "NSECD", "BSEFO"]

    if is_cash_segment:
        # For cash segment: CNC = DELIVERY, MIS = VALUEPLUS (margin intraday)
        cash_mapping = {
            "CNC": "DELIVERY",  # Delivery for holdings
            "MIS": "VALUEPLUS",  # Margin intraday for MIS
            "NRML": "VALUEPLUS",  # Fallback to margin
        }
        return cash_mapping.get(product, "VALUEPLUS")

    elif is_fo_segment:
        # For F&O segment, use NORMAL
        fo_mapping = {
            "NRML": "NORMAL",
            "MIS": "NORMAL",
            "CNC": "NORMAL",
        }
        return fo_mapping.get(product, "NORMAL")

    else:
        # Default fallback based on product
        default_mapping = {
            "CNC": "DELIVERY",
            "MIS": "VALUEPLUS",
            "NRML": "NORMAL",
        }
        return default_mapping.get(product, "VALUEPLUS")


def reverse_map_product_type(product, exchange=None):
    """
    Reverse maps Motilal Oswal product type to OpenAlgo product type.
    Context:
    - Motilal uses DELIVERY for cash delivery (CNC)
    - Motilal uses VALUEPLUS for margin intraday (MIS)
    - Motilal uses NORMAL for F&O segment

    Without exchange context:
        DELIVERY → CNC (delivery product)
        VALUEPLUS → MIS (margin intraday)
        NORMAL → MIS (F&O intraday)

    With exchange context:
        For NSE/BSE:
            DELIVERY → CNC (delivery)
            VALUEPLUS → MIS (margin intraday)
        For NSEFO/MCX:
            NORMAL → MIS (intraday F&O)
    """
    # Default reverse mapping without exchange context
    if exchange is None:
        reverse_product_type_mapping = {
            "DELIVERY": "CNC",  # Delivery product
            "VALUEPLUS": "MIS",  # Margin intraday
            "NORMAL": "MIS",  # F&O intraday
            "BTST": "MIS",
            "MTF": "NRML",
        }
        return reverse_product_type_mapping.get(product, "MIS")

    # With exchange context, provide accurate mapping
    is_cash_segment = exchange in ["NSE", "BSE"]

    if is_cash_segment:
        # For cash segment: VALUEPLUS = MIS, DELIVERY = CNC
        cash_reverse_mapping = {"DELIVERY": "CNC", "VALUEPLUS": "MIS", "BTST": "MIS"}
        return cash_reverse_mapping.get(product, "MIS")
    else:
        # For F&O segment: NORMAL is used
        reverse_fo_mapping = {
            "NORMAL": "MIS",
            "VALUEPLUS": "NRML",
        }
        return reverse_fo_mapping.get(product, "MIS")

```
