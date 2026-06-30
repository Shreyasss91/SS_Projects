# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\shoonya\mapping



---

# FILE: broker\shoonya\mapping\margin_data.py

```py
# Mapping OpenAlgo API Request https://openalgo.in/docs
# Mapping Shoonya GetBasketMargin API

from broker.shoonya.mapping.transform_data import map_order_type, map_product_type
from database.token_db import get_br_symbol
from utils.logging import get_logger
from utils.mpp_slab import calculate_protected_price, get_instrument_type_from_symbol

logger = get_logger(__name__)


def _apply_mpp(position, auth_token):
    """
    Convert MARKET/SL-M to LMT/SL-LMT with a protected price for basket margin.

    GetBasketMargin rejects MKT/SL-MKT price types, so for MARKET/SL-M inputs we
    always return a converted order type (LMT or SL-LMT) even when MPP can't
    fetch an LTP. Fallback price:
      - MARKET -> position.price (user-supplied limit, may be 0)
      - SL-M   -> position.trigger_price (at trigger, SL-LMT becomes a LIMIT
                  at this level)
    """
    pricetype = position.get("pricetype", "MARKET")
    action = position["action"].upper()
    price = str(position.get("price", 0) or 0)
    order_type = map_order_type(pricetype)

    if pricetype not in ("MARKET", "SL-M"):
        return order_type, price

    original_type = pricetype
    converted_order_type = "LMT" if original_type == "MARKET" else "SL-LMT"
    fallback_price = (
        str(position.get("price", 0) or 0)
        if original_type == "MARKET"
        else str(position.get("trigger_price", 0) or 0)
    )

    logger.info(
        f"Margin MPP: {original_type} detected Symbol={position['symbol']}, "
        f"Exchange={position['exchange']}, Action={action}"
    )
    try:
        if not auth_token:
            logger.warning(
                f"Margin MPP: no auth token for Symbol={position['symbol']}; "
                f"converting {original_type}->{converted_order_type} at supplied price={fallback_price}"
            )
            return converted_order_type, fallback_price

        from broker.shoonya.api.data import BrokerData

        broker_data = BrokerData(auth_token)
        quote = broker_data.get_quotes(position["symbol"], position["exchange"])
        ltp = float(quote.get("ltp", 0))
        tick_size = quote.get("tick_size")
        instrument_type = get_instrument_type_from_symbol(position["symbol"])

        logger.info(
            f"Margin MPP Quote: Symbol={position['symbol']}, LTP={ltp}, "
            f"TickSize={tick_size}, InstrumentType={instrument_type}"
        )

        if ltp > 0:
            protected = calculate_protected_price(
                price=ltp,
                action=action,
                symbol=position["symbol"],
                instrument_type=instrument_type,
                tick_size=tick_size,
            )
            logger.info(
                f"Margin MPP Converted: {original_type}->{converted_order_type}, "
                f"FinalPrice={protected}"
            )
            return converted_order_type, str(protected)

        logger.warning(
            f"Margin MPP: LTP<=0 for Symbol={position['symbol']}; "
            f"converting {original_type}->{converted_order_type} at supplied price={fallback_price}"
        )
        return converted_order_type, fallback_price

    except Exception as e:
        logger.error(
            f"Margin MPP Error: Symbol={position['symbol']}, Error={e}. "
            f"Converting {original_type}->{converted_order_type} at supplied price={fallback_price}"
        )
        return converted_order_type, fallback_price


def _build_order(position, auth_token):
    oa_symbol = position["symbol"]
    exchange = position["exchange"]
    br_symbol = get_br_symbol(oa_symbol, exchange)
    if not br_symbol:
        logger.warning(f"Symbol not found for: {oa_symbol} on exchange: {exchange}")
        return None
    if "&" in br_symbol:
        br_symbol = br_symbol.replace("&", "%26")

    prctyp, prc = _apply_mpp(position, auth_token)

    return {
        "exch": exchange,
        "tsym": br_symbol,
        "qty": str(int(position["quantity"])),
        "prc": prc,
        "trgprc": str(position.get("trigger_price", 0) or 0),
        "prd": map_product_type(position.get("product", "NRML")),
        "trantype": "B" if position["action"].upper() == "BUY" else "S",
        "prctyp": prctyp,
    }


def transform_margin_positions(positions, userid, auth_token=None):
    orders = []
    for position in positions:
        try:
            order = _build_order(position, auth_token)
            if order:
                orders.append(order)
        except Exception as e:
            logger.error(f"Error transforming position: {position}, Error: {e}")
            continue
    if not orders:
        return {"uid": userid, "actid": userid, "basketlists": []}

    first = orders[0]
    rest = orders[1:]
    return {
        "uid": userid,
        "actid": userid,
        "exch": first["exch"],
        "tsym": first["tsym"],
        "qty": first["qty"],
        "prc": first["prc"],
        "trgprc": first["trgprc"],
        "prd": first["prd"],
        "trantype": first["trantype"],
        "prctyp": first["prctyp"],
        "basketlists": rest,
    }


def parse_margin_response(response_data):
    try:
        if not response_data or not isinstance(response_data, dict):
            return {"status": "error", "message": "Invalid response from broker"}
        if response_data.get("stat") != "Ok":
            error_message = (
                response_data.get("emsg")
                or response_data.get("remarks")
                or "Failed to calculate margin"
            )
            return {"status": "error", "message": error_message}
        # Shoonya doc semantics:
        #   marginused      -> "Total margin"        (pre-hedge basket total)
        #   marginusedtrade -> "Margin after trade"  (post-hedge account total)
        # Parallels Zerodha's initial.total vs final.total. Map total to
        # marginused (matches Zerodha impl using initial.total) and set
        # span/exposure to 0 since Shoonya gives no breakdown. See #1268.
        margin_used = float(response_data.get("marginused", 0) or 0)
        return {
            "status": "success",
            "data": {
                "total_margin_required": margin_used,
                "span_margin": 0,
                "exposure_margin": 0,
            },
        }
    except Exception as e:
        logger.error(f"Error parsing margin response: {e}")
        return {"status": "error", "message": f"Failed to parse margin response: {str(e)}"}

```


---

# FILE: broker\shoonya\mapping\order_data.py

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
    # Check if 'data' is None
    if order_data is None or (
        isinstance(order_data, dict) and (order_data.get("stat") == "Not_Ok")
    ):
        # Handle the case where there is no data
        # For example, you might want to display a message to the user
        # or pass an empty list or dictionary to the template.
        logger.info("No data available.")
        order_data = []  # Return empty list for consistency with expected format
    else:
        order_data = order_data

    if order_data:
        for order in order_data:
            # Extract the instrument_token and exchange for the current order
            symboltoken = order["token"]
            exchange = order["exch"]

            # Use the get_symbol function to fetch the symbol from the database
            symbol_from_db = get_symbol(symboltoken, exchange)

            # Check if a symbol was found; if so, update the trading_symbol in the current order
            if symbol_from_db:
                order["tsym"] = symbol_from_db
                if (order["exch"] == "NSE" or order["exch"] == "BSE") and order["prd"] == "C":
                    order["prd"] = "CNC"

                elif order["prd"] == "I":
                    order["prd"] = "MIS"

                elif order["exch"] in ["NFO", "MCX", "BFO", "CDS"] and order["prd"] == "M":
                    order["prd"] = "NRML"

                if order["prctyp"] == "MKT":
                    order["prctyp"] = "MARKET"
                elif order["prctyp"] == "LMT":
                    order["prctyp"] = "LIMIT"
                elif order["prctyp"] == "SL-MKT":
                    order["prctyp"] = "SL-M"
                elif order["prctyp"] == "SL-LMT":
                    order["prctyp"] = "SL"

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
            if order["trantype"] == "B":
                order["trantype"] = "BUY"
                total_buy_orders += 1
            elif order["trantype"] == "S":
                order["trantype"] = "SELL"
                total_sell_orders += 1

            # Count orders based on their status
            status = str(order.get("status") or "").upper()
            if status == "COMPLETE":
                total_completed_orders += 1
            elif status in ("OPEN", "TRIGGER PENDING", "PENDING"):
                total_open_orders += 1
            elif status == "REJECTED":
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
    transformed_orders = []

    for order in orders:
        # Make sure each item is indeed a dictionary
        if not isinstance(order, dict):
            logger.warning(
                f"Warning: Expected a dict, but found a {type(order)}. Skipping this item."
            )
            continue

        # Map Shoonya status to OpenAlgo status
        raw_status = str(order.get("status") or "").upper()
        status_map = {
            "COMPLETE": "complete",
            "OPEN": "open",
            "REJECTED": "rejected",
            "CANCELED": "cancelled",
            "CANCELLED": "cancelled",
            "TRIGGER PENDING": "open",
            "PENDING": "open",
        }
        mapped_status = status_map.get(raw_status, raw_status.lower())

        transformed_order = {
            "symbol": order.get("tsym", ""),
            "exchange": order.get("exch", ""),
            "action": order.get("trantype", ""),
            "quantity": order.get("qty", 0),
            "price": order.get("prc", 0.0),
            "trigger_price": order.get("trgprc", 0.0),
            "pricetype": order.get("prctyp", ""),
            "product": order.get("prd", ""),
            "orderid": order.get("norenordno", ""),
            "order_status": mapped_status,
            "timestamp": order.get("norentm", ""),
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
    if trade_data is None or (
        isinstance(trade_data, dict) and (trade_data.get("stat") == "Not_Ok")
    ):
        # Handle the case where there is no data
        # For example, you might want to display a message to the user
        # or pass an empty list or dictionary to the template.
        logger.info("No data available.")
        trade_data = []  # Return empty list for consistency with expected format
    else:
        trade_data = trade_data

    if trade_data:
        for order in trade_data:
            # Extract the instrument_token and exchange for the current order
            symbol = order["tsym"]
            exchange = order["exch"]

            # Use the get_symbol function to fetch the symbol from the database
            symbol_from_db = get_oa_symbol(symbol, exchange)

            # Check if a symbol was found; if so, update the trading_symbol in the current order
            if symbol_from_db:
                order["tsym"] = symbol_from_db
                if (order["exch"] == "NSE" or order["exch"] == "BSE") and order["prd"] == "C":
                    order["prd"] = "CNC"

                elif order["prd"] == "I":
                    order["prd"] = "MIS"

                elif order["exch"] in ["NFO", "MCX", "BFO", "CDS"] and order["prd"] == "M":
                    order["prd"] = "NRML"

                if order["trantype"] == "B":
                    order["trantype"] = "BUY"
                elif order["trantype"] == "S":
                    order["trantype"] = "SELL"

            else:
                logger.info(
                    f"Unable to find the symbol {symbol} and exchange {exchange}. Keeping original trading symbol."
                )

    return trade_data


def transform_tradebook_data(tradebook_data):
    transformed_data = []
    for trade in tradebook_data:
        # Parse the timestamp from Shoonya format "HH:MM:SS DD-MM-YYYY" to just "HH:MM:SS"
        timestamp = trade.get("norentm", "")
        if timestamp and " " in timestamp:
            # Extract just the time part (HH:MM:SS) from "HH:MM:SS DD-MM-YYYY"
            timestamp = timestamp.split(" ")[0]

        transformed_trade = {
            "symbol": trade.get("tsym", ""),
            "exchange": trade.get("exch", ""),
            "product": trade.get("prd", ""),
            "action": trade.get("trantype", ""),
            "quantity": trade.get("qty", 0),
            "average_price": trade.get("avgprc", 0.0),
            "trade_value": float(trade.get("avgprc", 0)) * int(trade.get("qty", 0)),
            "orderid": trade.get("norenordno", ""),
            "timestamp": timestamp,  # Now just "HH:MM:SS"
        }
        transformed_data.append(transformed_trade)
    return transformed_data


def map_position_data(position_data):
    if position_data is None or (
        isinstance(position_data, dict) and (position_data.get("stat") == "Not_Ok")
    ):
        # Handle the case where there is no data
        # For example, you might want to display a message to the user
        # or pass an empty list or dictionary to the template.
        logger.info("No data available.")
        position_data = []  # Return empty list for consistency with expected format
    else:
        position_data = position_data

    if position_data:
        for order in position_data:
            # Extract the instrument_token and exchange for the current order
            symbol = order["tsym"]
            exchange = order["exch"]

            # Use the get_symbol function to fetch the symbol from the database
            symbol_from_db = get_oa_symbol(symbol, exchange)

            # Check if a symbol was found; if so, update the trading_symbol in the current order
            if symbol_from_db:
                order["tsym"] = symbol_from_db
                if (order["exch"] == "NSE" or order["exch"] == "BSE") and order["prd"] == "C":
                    order["prd"] = "CNC"

                elif order["prd"] == "I":
                    order["prd"] = "MIS"

                elif order["exch"] in ["NFO", "MCX", "BFO", "CDS"] and order["prd"] == "M":
                    order["prd"] = "NRML"

            else:
                logger.info(
                    f"Unable to find the symbol {symbol} and exchange {exchange}. Keeping original trading symbol."
                )

    return position_data


def transform_positions_data(positions_data):
    transformed_data = []
    for position in positions_data:
        # Get position values
        netqty = float(position.get("netqty", 0))
        netavgprc = float(position.get("netavgprc", 0.0))
        lp = float(position.get("lp", 0.0))  # Last Price from Shoonya
        rpnl = float(position.get("rpnl", 0.0))  # Realized P&L
        urmtom = float(position.get("urmtom", 0.0))  # Unrealized MTM

        # For closed positions, Shoonya zeroes out netavgprc
        # Use daybuyavgprc or totbuyavgprc as fallback for average price
        if netavgprc == 0 and netqty == 0:
            netavgprc = float(position.get("daybuyavgprc", 0.0)) or float(
                position.get("totbuyavgprc", 0.0)
            )

        # Calculate PnL
        if netqty != 0 and lp > 0:
            # Open position: use unrealized MTM if available, else calculate
            if urmtom != 0:
                pnl = urmtom + rpnl
            else:
                if netqty > 0:
                    pnl = (lp - netavgprc) * netqty + rpnl
                else:
                    pnl = (netavgprc - lp) * abs(netqty) + rpnl
        else:
            # Closed position: use realized P&L
            pnl = rpnl

        transformed_position = {
            "symbol": position.get("tsym", ""),
            "exchange": position.get("exch", ""),
            "product": position.get("prd", ""),
            "quantity": netqty,
            "average_price": netavgprc,
            "ltp": lp,
            "pnl": pnl,
        }
        transformed_data.append(transformed_position)
    return transformed_data


def map_portfolio_data(portfolio_data):
    """
    Processes and modifies a list of Portfolio dictionaries based on specific conditions and
    ensures both holdings and totalholding parts are transmitted in a single response.

    Parameters:
    - portfolio_data: A list of dictionaries, where each dictionary represents portfolio information.

    Returns:
    - The modified portfolio_data with 'product' fields changed for 'holdings' and 'totalholding' included.
    """
    # Check if 'portfolio_data' is a list
    if not portfolio_data or not isinstance(portfolio_data, list):
        logger.info("No data available or incorrect data format.")
        return []

    # Iterate over the portfolio_data list and process each entry
    for portfolio in portfolio_data:
        # Ensure 'stat' is 'Ok' before proceeding
        if portfolio.get("stat") != "Ok":
            logger.info(f"Error: {portfolio.get('emsg', 'Unknown error occurred.')}")
            continue

        # Process the 'exch_tsym' list inside each portfolio entry
        for exch_tsym in portfolio.get("exch_tsym", []):
            symbol = exch_tsym.get("tsym", "")
            exchange = exch_tsym.get("exch", "")

            # Replace 'get_oa_symbol' function with your actual symbol fetching logic
            symbol_from_db = get_oa_symbol(symbol, exchange)

            if symbol_from_db:
                exch_tsym["tsym"] = symbol_from_db
            else:
                logger.info(f"Shoonya Portfolio - Product Value for {symbol} Not Found or Changed.")

    return portfolio_data


def calculate_portfolio_statistics(holdings_data):
    """
    Calculates portfolio statistics according to Shoonya API specifications.
    """
    totalholdingvalue = 0
    totalinvvalue = 0
    totalprofitandloss = 0
    totalpnlpercentage = 0

    # Check if the data is valid or contains an error
    if not holdings_data or not isinstance(holdings_data, list):
        logger.error("Error: Invalid or missing holdings data.")
        return {
            "totalholdingvalue": totalholdingvalue,
            "totalinvvalue": totalinvvalue,
            "totalprofitandloss": totalprofitandloss,
            "totalpnlpercentage": totalpnlpercentage,
        }

    # Iterate over the list of holdings
    for holding in holdings_data:
        # Ensure 'stat' is 'Ok' before proceeding
        if holding.get("stat") != "Ok":
            logger.info(f"Error: {holding.get('emsg', 'Unknown error occurred.')}")
            continue

        # Get NSE entry
        nse_entry = next(
            (exch for exch in holding.get("exch_tsym", []) if exch.get("exch") == "NSE"), None
        )
        if not nse_entry:
            continue

        # Get quantities from API response
        holdqty = float(holding.get("holdqty", 0))
        btstqty = float(holding.get("btstqty", 0))
        brkcolqty = float(holding.get("brkcolqty", 0))
        unplgdqty = float(holding.get("unplgdqty", 0))
        benqty = float(holding.get("benqty", 0))
        npoadqty = float(holding.get("npoadqty", 0))
        dpqty = float(holding.get("dpqty", 0))
        usedqty = float(holding.get("usedqty", 0))

        # Calculate valuation using Shoonya's formula
        upldprc = float(holding.get("upldprc", 0))
        valuation = (
            (btstqty + holdqty + brkcolqty + unplgdqty + benqty + max(npoadqty, dpqty)) - usedqty
        ) * upldprc

        # Calculate investment value and P&L
        totalinvvalue += valuation
        totalholdingvalue += valuation

    # Calculate overall P&L percentage
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
    Transforms holdings data according to Shoonya API specifications.
    """
    transformed_data = []
    if isinstance(holdings_data, list):
        for holding in holdings_data:
            if holding.get("stat") != "Ok":
                continue

            # Get NSE entry
            nse_entries = [
                exch for exch in holding.get("exch_tsym", []) if exch.get("exch") == "NSE"
            ]
            for exch_tsym in nse_entries:
                # Calculate total quantity using Shoonya's formula
                holdqty = float(holding.get("holdqty", 0))
                btstqty = float(holding.get("btstqty", 0))
                brkcolqty = float(holding.get("brkcolqty", 0))
                unplgdqty = float(holding.get("unplgdqty", 0))
                benqty = float(holding.get("benqty", 0))
                npoadqty = float(holding.get("npoadqty", 0))
                dpqty = float(holding.get("dpqty", 0))
                usedqty = float(holding.get("usedqty", 0))

                total_qty = (
                    btstqty
                    + holdqty
                    + brkcolqty
                    + unplgdqty
                    + benqty
                    + max(npoadqty, dpqty)
                    - usedqty
                )

                transformed_position = {
                    "symbol": exch_tsym.get("tsym", ""),
                    "exchange": exch_tsym.get("exch", ""),
                    "quantity": int(total_qty),
                    "product": holding.get("s_prdt_ali", "CNC"),
                    "pnl": 0.0,  # Will be calculated when market price is available
                    "pnlpercent": 0.0,  # Will be calculated when market price is available
                }
                transformed_data.append(transformed_position)
    return transformed_data

```


---

# FILE: broker\shoonya\mapping\transform_data.py

```py
# Mapping OpenAlgo API Request https://openalgo.in/docs
# Mapping Shoonya Broking Parameters https://shoonya.com/api-documentation

from database.token_db import get_br_symbol
from utils.logging import get_logger
from utils.mpp_slab import calculate_protected_price, get_instrument_type_from_symbol

logger = get_logger(__name__)


def transform_data(data, token, auth_token=None):
    """
    Transforms the new API request structure to the current expected structure.
    For market orders, fetches quotes and adjusts price using MPP (Market Price Protection):
    - EQ/FUT: Price < 100: 2%, 100-500: 1%, > 500: 0.5%
    - OPT (CE/PE): Price < 10: 5%, 10-100: 3%, 100-500: 2%, > 500: 1%

    Args:
        data: Order data dictionary
        token: Instrument token
        auth_token: Authentication token for fetching quotes (passed from order_api)
    """
    userid = data["apikey"]
    symbol = get_br_symbol(data["symbol"], data["exchange"])
    # Handle special characters in symbol
    if symbol and "&" in symbol:
        symbol = symbol.replace("&", "%26")

    # Default values
    price = str(data.get("price", "0"))
    order_type = map_order_type(data["pricetype"])
    action = data["action"].upper()

    # Apply Market Price Protection for MARKET and SL-M orders
    # Shoonya blocks both MKT and SL-MKT order types for API orders
    if data["pricetype"] in ("MARKET", "SL-M"):
        original_type = data["pricetype"]
        logger.info(
            f"MPP: {original_type} order detected for Symbol={data['symbol']}, Exchange={data['exchange']}, Action={action}"
        )
        try:
            if auth_token:
                # Lazy import to avoid circular dependency
                from broker.shoonya.api.data import BrokerData

                # Create BrokerData instance to fetch quotes
                broker_data = BrokerData(auth_token)

                # Fetch quotes for the symbol
                quote_data = broker_data.get_quotes(data["symbol"], data["exchange"])
                logger.info(
                    f"MPP Quote Response: Symbol={data['symbol']}, Exchange={data['exchange']}, "
                    f"LTP={quote_data.get('ltp')}, Bid={quote_data.get('bid')}, Ask={quote_data.get('ask')}, "
                    f"TickSize={quote_data.get('tick_size')}"
                )

                # Get instrument type from symbol
                instrument_type = get_instrument_type_from_symbol(data["symbol"])

                # Get tick_size from quote response
                tick_size = quote_data.get("tick_size")
                logger.info(
                    f"MPP Symbol Info: InstrumentType={instrument_type}, TickSize={tick_size}"
                )

                # Get LTP for price calculation
                ltp = float(quote_data.get("ltp", 0))

                if ltp > 0:
                    # Calculate protected price using centralized MPP slab with tick size rounding
                    protected_price = calculate_protected_price(
                        price=ltp,
                        action=action,
                        symbol=data["symbol"],
                        instrument_type=instrument_type,
                        tick_size=tick_size,
                    )
                    price = str(protected_price)

                    if original_type == "MARKET":
                        # Convert MARKET to LIMIT
                        order_type = "LMT"
                    else:
                        # Convert SL-M to SL-LMT (keep trigger price)
                        order_type = "SL-LMT"

                    logger.info(
                        f"MPP Conversion Complete: Symbol={data['symbol']}, "
                        f"OrderType={original_type}->{order_type}, FinalPrice={protected_price}"
                    )
                else:
                    logger.warning(
                        f"MPP Warning: LTP is 0 or invalid for Symbol={data['symbol']}, "
                        f"Exchange={data['exchange']}. Proceeding with regular {original_type} order"
                    )
            else:
                logger.warning(
                    f"MPP Warning: No auth token available for Symbol={data['symbol']}. "
                    f"Cannot fetch quotes for MPP adjustment"
                )
        except Exception as e:
            logger.error(
                f"MPP Error: Failed to apply MPP for Symbol={data['symbol']}, "
                f"Exchange={data['exchange']}, Error={str(e)}. Proceeding with regular {original_type} order."
            )

    # Basic mapping
    transformed = {
        "uid": userid,
        "actid": userid,
        "exch": data["exchange"],
        "tsym": symbol,
        "qty": str(data["quantity"]),
        "prc": price,
        "trgprc": str(data.get("trigger_price", "0")),
        "dscqty": str(data.get("disclosed_quantity", "0")),
        "prd": map_product_type(data["product"]),
        "trantype": "B" if action == "BUY" else "S",
        "prctyp": order_type,
        "mkt_protection": "0",
        "ret": "DAY",
        "ordersource": "API",
    }

    # Log order data without sensitive fields
    safe_log = {k: v for k, v in transformed.items() if k not in ("uid", "actid")}
    logger.info(f"Transformed order data: {safe_log}")
    return transformed


def transform_modify_order_data(data, token):
    # Handle special characters in symbol
    symbol = data["symbol"]
    if symbol and "&" in symbol:
        symbol = symbol.replace("&", "%26")

    result = {
        "uid": data["apikey"],
        "exch": data["exchange"],
        "norenordno": data["orderid"],
        "prctyp": map_order_type(data["pricetype"]),
        "prc": str(data["price"]),
        "qty": str(data["quantity"]),
        "tsym": symbol,
        "ret": "DAY",
        "dscqty": str(data.get("disclosed_quantity") or 0),
    }

    # Only include trigger price for SL/SL-M orders
    # Sending trgprc=0 for LIMIT orders causes "Trigger price invalid - 0.00" error
    if data["pricetype"] in ["SL", "SL-M"]:
        result["trgprc"] = str(data.get("trigger_price") or 0)

    return result


def map_order_type(pricetype):
    """
    Maps the new pricetype to the existing order type.
    """
    order_type_mapping = {"MARKET": "MKT", "LIMIT": "LMT", "SL": "SL-LMT", "SL-M": "SL-MKT"}
    return order_type_mapping.get(pricetype, "MARKET")  # Default to MARKET if not found


def map_product_type(product):
    """
    Maps the new product type to the existing product type.
    """
    product_type_mapping = {
        "CNC": "C",
        "NRML": "M",
        "MIS": "I",
    }
    return product_type_mapping.get(product, "I")  # Default to DELIVERY if not found


def reverse_map_product_type(product):
    """
    Maps the new product type to the existing product type.
    """
    reverse_product_type_mapping = {
        "C": "CNC",
        "M": "NRML",
        "I": "MIS",
    }
    return reverse_product_type_mapping.get(product)

```
