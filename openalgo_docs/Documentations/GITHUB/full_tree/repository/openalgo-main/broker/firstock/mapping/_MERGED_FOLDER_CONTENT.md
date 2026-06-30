# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\firstock\mapping



---

# FILE: broker\firstock\mapping\margin_data.py

```py
# Mapping OpenAlgo API Request https://openalgo.in/docs
# Mapping Firstock basketMargin API

from broker.firstock.mapping.transform_data import map_order_type, map_product_type
from database.token_db import get_br_symbol, get_symbol_info
from utils.logging import get_logger
from utils.mpp_slab import calculate_protected_price, get_instrument_type_from_symbol

logger = get_logger(__name__)


def _apply_mpp(position, auth_token):
    """
    Convert MARKET/SL-M to LMT/SL-LMT with a protected price for basket margin.

    Matches the place-order MPP behavior: for MARKET/SL-M inputs we always
    return a converted order type (LMT or SL-LMT) even when MPP can't fetch
    an LTP. Fallback price when MPP fails:
      - MARKET -> position.price (user-supplied limit, may be 0)
      - SL-M   -> position.trigger_price (at trigger, SL-LMT becomes a LIMIT
                  at this level)
    Ensures the basketMargin payload never carries a bare MKT/SL-MKT with
    price=0 that would either be rejected or produce meaningless margin.
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

        from broker.firstock.api.data import BrokerData

        broker_data = BrokerData(auth_token)
        quote = broker_data.get_quotes(position["symbol"], position["exchange"])
        ltp = float(quote.get("ltp", 0))

        # Firstock's /getQuote response omits tick_size — fall back to the
        # master contract DB (same pattern as kotak / place-order MPP).
        tick_size = quote.get("tick_size")
        if not tick_size:
            symbol_info = get_symbol_info(position["symbol"], position["exchange"])
            if symbol_info and symbol_info.tick_size:
                tick_size = symbol_info.tick_size

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
    """Build a single Firstock basketMargin leg from an OpenAlgo position."""
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
        "exchange": exchange,
        "tradingSymbol": br_symbol,
        "quantity": str(int(position["quantity"])),
        "price": prc,
        "triggerPrice": str(position.get("trigger_price", 0) or 0),
        "product": map_product_type(position.get("product", "NRML")),
        "transactionType": "B" if position["action"].upper() == "BUY" else "S",
        "priceType": prctyp,
    }


def transform_margin_positions(positions, userid, auth_token=None):
    """
    Transform a list of OpenAlgo positions into a Firstock basketMargin payload.

    Firstock layout (per /V1/basketMargin docs):
      - First leg is flat at the top level of the request body
      - Additional legs are nested inside BasketList_Params[]
      - userId and jKey must be at top level (jKey is added by the caller)
    """
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
        return {"userId": userid, "BasketList_Params": []}

    first = orders[0]
    rest = orders[1:]
    return {
        "userId": userid,
        "exchange": first["exchange"],
        "tradingSymbol": first["tradingSymbol"],
        "quantity": first["quantity"],
        "price": first["price"],
        "triggerPrice": first["triggerPrice"],
        "product": first["product"],
        "transactionType": first["transactionType"],
        "priceType": first["priceType"],
        "BasketList_Params": rest,
    }


def parse_margin_response(response_data):
    """
    Parse Firstock /V1/basketMargin response into OpenAlgo's standard shape.

    Firstock success shape:
      {
        "status": "success",
        "data": {
          "BasketMargin": [...],
          "MarginOnNewOrder": 126783,
          "PreviousMargin": 0,
          "TradedMargin": 126783
        }
      }

    Firstock failure shape:
      {"status": "failed", "error": {"message": "..."}}
      or {"status": "failed"}

    TradedMargin is the post-hedge total margin (analogous to Zerodha's
    initial.total). Map to total_margin_required. span/exposure set to 0
    since Firstock doesn't break them down in this response.
    """
    try:
        if not response_data or not isinstance(response_data, dict):
            return {"status": "error", "message": "Invalid response from broker"}

        if response_data.get("status") != "success":
            error_obj = response_data.get("error") or {}
            error_message = (
                (error_obj.get("message") if isinstance(error_obj, dict) else None)
                or response_data.get("message")
                or response_data.get("emsg")
                or "Failed to calculate margin"
            )
            return {"status": "error", "message": error_message}

        data = response_data.get("data") or {}
        margin_used = float(data.get("TradedMargin", 0) or 0)

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

# FILE: broker\firstock\mapping\order_data.py

```py
import json

from database.token_db import get_oa_symbol, get_symbol
from utils.logging import get_logger

logger = get_logger(__name__)


def map_order_data(order_data):
    """
    Processes and modifies order data based on Firstock's format.
    Handles both raw API response and pre-mapped data.

    Parameters:
    - order_data: Either raw API response or list of pre-mapped orders

    Returns:
    - List of mapped orders in OpenAlgo format
    """
    # If it's a list, data is already mapped
    if isinstance(order_data, list):
        return order_data

    # If it's a dict with status/data, it's raw API response
    if isinstance(order_data, dict):
        if order_data.get("status") != "success":
            logger.warning("No data available or invalid response.")
            return []
        orders = order_data.get("data", [])
    else:
        logger.info("Invalid order data format")
        return []

    mapped_orders = []
    for order in orders:
        mapped_order = {}
        # Get OpenAlgo symbol from token
        symbol_from_db = get_symbol(order.get("token"), order.get("exchange"))
        if symbol_from_db:
            mapped_order["tsym"] = symbol_from_db
        else:
            logger.info(
                f"Symbol not found for token {order.get('token')} and exchange {order.get('exchange')}."
            )
            mapped_order["tsym"] = order.get("tradingSymbol", "")

        # Map transaction type (will be converted to BUY/SELL in calculate_order_statistics)
        mapped_order["trantype"] = order.get("transactionType", "")

        # Map product type (will be converted in calculate_order_statistics)
        mapped_order["prd"] = order.get("product", "")

        # Map price type (will be converted in calculate_order_statistics)
        mapped_order["prctyp"] = order.get("priceType", "")

        # Map other fields
        mapped_order["norenordno"] = order.get("orderNumber", "")
        mapped_order["qty"] = order.get("quantity", "0")
        mapped_order["prc"] = order.get("price", "0.00")
        mapped_order["exch"] = order.get("exchange", "")
        mapped_order["status"] = order.get("status", "").upper()
        mapped_order["trgprc"] = order.get("triggerPrice", "0.00")
        mapped_order["norentm"] = order.get("orderTime", "")

        mapped_orders.append(mapped_order)

    return mapped_orders


def calculate_order_statistics(order_data):
    """
    Calculates statistics from order data, including totals for buy orders, sell orders,
    completed orders, open orders, and rejected orders.

    Parameters:
    - order_data: A list of dictionaries containing order data

    Returns:
    - A dictionary containing counts of different types of orders
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

            # Map product type
            if (order["exch"] == "NSE" or order["exch"] == "BSE") and order["prd"] == "C":
                order["prd"] = "CNC"
            elif order["prd"] == "I":
                order["prd"] = "MIS"
            elif order["exch"] in ["NFO", "MCX", "BFO", "CDS"] and order["prd"] == "M":
                order["prd"] = "NRML"

            # Map price type back to OpenAlgo canonical form. Tolerant of both
            # short codes (Firstock V1 docs) and long forms (V1.7 order book
            # sometimes returns "LIMIT"/"SL-LIMIT"), any casing/underscore.
            raw_prctyp = str(order.get("prctyp") or "").upper().replace("_", "-").strip()
            prctyp_map = {
                "MKT": "MARKET",
                "MARKET": "MARKET",
                "LMT": "LIMIT",
                "LIMIT": "LIMIT",
                "SL-MKT": "SL-M",
                "SL-MARKET": "SL-M",
                "SL-M": "SL-M",
                "SL-LMT": "SL",
                "SL-LIMIT": "SL",
                "SL": "SL",
            }
            order["prctyp"] = prctyp_map.get(raw_prctyp, raw_prctyp)

            # Count orders based on their status
            status = str(order.get("status") or "").upper()
            if status == "COMPLETE":
                total_completed_orders += 1
            elif status in ("OPEN", "TRIGGER PENDING", "TRIGGER_PENDING", "PENDING"):
                total_open_orders += 1
            elif status == "REJECTED":
                total_rejected_orders += 1

    return {
        "total_buy_orders": total_buy_orders,
        "total_sell_orders": total_sell_orders,
        "total_completed_orders": total_completed_orders,
        "total_open_orders": total_open_orders,
        "total_rejected_orders": total_rejected_orders,
    }


def transform_order_data(orders):
    """
    Transform order data to match OpenAlgo format.

    Returns:
    - List of transformed orders in the format expected by orderbook.html
    """
    logger.info(f"Input orders: {orders}")
    if not orders:
        return []

    # First map the Firstock response to intermediate format
    mapped_orders = map_order_data(orders)

    logger.info(f"Mapped orders: {mapped_orders}")

    # Calculate statistics and transform order fields
    calculate_order_statistics(mapped_orders)

    # Map Firstock status -> OpenAlgo canonical status. Firstock returns
    # "CANCELED" (single L) but OpenAlgo UI expects "cancelled" (double L);
    # similarly for TRIGGER_PENDING which the UI treats as an open order.
    status_map = {
        "COMPLETE": "complete",
        "OPEN": "open",
        "REJECTED": "rejected",
        "CANCELED": "cancelled",
        "CANCELLED": "cancelled",
        "TRIGGER PENDING": "trigger_pending",
        "TRIGGER_PENDING": "trigger_pending",
        "PENDING": "open",
    }

    # Transform to final format
    transformed_orders = []
    for order in mapped_orders:
        # Handle empty trigger price
        trigger_price = order.get("trgprc", "0.00")
        if not trigger_price or trigger_price == "":
            trigger_price = "0.00"

        raw_status = str(order.get("status") or "").upper()
        mapped_status = status_map.get(raw_status, raw_status.lower())

        transformed_order = {
            "symbol": order.get("tsym", ""),
            "exchange": order.get("exch", ""),
            "action": order.get("trantype", ""),
            "quantity": order.get("qty", "0"),
            "price": order.get("prc", "0.00"),
            "trigger_price": trigger_price,
            "pricetype": order.get("prctyp", ""),
            "product": order.get("prd", ""),
            "orderid": order.get("norenordno", ""),
            "order_status": mapped_status,
            "timestamp": order.get("norentm", ""),
        }
        transformed_orders.append(transformed_order)

    logger.info(f"Final transformed orders: {transformed_orders}")
    return transformed_orders


def map_trade_data(trade_data):
    """
    Processes and modifies trade data based on Firstock's format.

    Parameters:
    - trade_data: Response from Firstock's tradebook API containing status and data fields

    Returns:
    - List of mapped trades in OpenAlgo format
    """
    # If it's a list, data is already mapped
    if isinstance(trade_data, list):
        return trade_data

    # If it's a dict with status/data, it's raw API response
    if isinstance(trade_data, dict):
        if trade_data.get("status") != "success":
            logger.info("No data available or invalid response.")
            return []
        trades = trade_data.get("data", [])
    else:
        logger.info("Invalid trade data format")
        return []

    mapped_trades = []
    for trade in trades:
        mapped_trade = {}
        # Get OpenAlgo symbol from token
        symbol_from_db = get_symbol(trade.get("token"), trade.get("exchange"))
        if symbol_from_db:
            mapped_trade["tsym"] = symbol_from_db
        else:
            logger.info(
                f"Symbol not found for token {trade.get('token')} and exchange {trade.get('exchange')}."
            )
            mapped_trade["tsym"] = trade.get("tradingSymbol", "")

        # Map transaction type (will be converted to BUY/SELL)
        mapped_trade["trantype"] = trade.get("transactionType", "")

        # Map product type (will be converted to CNC/MIS/NRML)
        mapped_trade["prd"] = trade.get("product", "")

        # Map other fields
        mapped_trade["exch"] = trade.get("exchange", "")
        mapped_trade["qty"] = trade.get("fillQuantity", "0")
        mapped_trade["avgprc"] = trade.get("fillPrice", "0.00")
        mapped_trade["norenordno"] = trade.get("orderNumber", "")
        mapped_trade["norentm"] = trade.get("fillTime", "")

        mapped_trades.append(mapped_trade)

    return mapped_trades


def transform_tradebook_data(trades):
    """
    Transform trade data to match OpenAlgo format.

    Parameters:
    - trades: List of trades from map_trade_data

    Returns:
    - List of transformed trades in the format expected by tradebook.html
    """
    logger.info(f"Input trades: {trades}")
    if not trades:
        return []

    # First map the Firstock response to intermediate format
    mapped_trades = map_trade_data(trades)
    logger.info(f"Mapped trades: {mapped_trades}")

    # Transform to final format
    transformed_trades = []
    for trade in mapped_trades:
        # Convert transaction type
        if trade["trantype"] == "B":
            trade["trantype"] = "BUY"
        elif trade["trantype"] == "S":
            trade["trantype"] = "SELL"

        # Convert product type
        if (trade["exch"] == "NSE" or trade["exch"] == "BSE") and trade["prd"] == "C":
            trade["prd"] = "CNC"
        elif trade["prd"] == "I":
            trade["prd"] = "MIS"
        elif trade["exch"] in ["NFO", "MCX", "BFO", "CDS"] and trade["prd"] == "M":
            trade["prd"] = "NRML"

        # Calculate trade value
        quantity = float(trade.get("qty", "0"))
        price = float(trade.get("avgprc", "0.00"))
        trade_value = quantity * price

        transformed_trade = {
            "symbol": trade.get("tsym", ""),
            "exchange": trade.get("exch", ""),
            "product": trade.get("prd", ""),
            "action": trade.get("trantype", ""),
            "quantity": trade.get("qty", "0"),
            "average_price": trade.get("avgprc", "0.00"),
            "trade_value": f"{trade_value:.2f}",
            "orderid": trade.get("norenordno", ""),
            "timestamp": trade.get("norentm", ""),
        }
        transformed_trades.append(transformed_trade)

    logger.info(f"Final transformed trades: {transformed_trades}")
    return transformed_trades


def map_portfolio_data(portfolio_data):
    """
    Processes and modifies portfolio data based on Firstock's format.

    Parameters:
    - portfolio_data: Response from Firstock's holdings API containing status and data fields

    Returns:
    - List of mapped holdings in OpenAlgo format
    """
    logger.info(f"Raw portfolio data: {json.dumps(portfolio_data, indent=2)}")

    # If it's a list, data is already mapped
    if isinstance(portfolio_data, list):
        return portfolio_data

    # If it's a dict with status/data, it's raw API response
    if isinstance(portfolio_data, dict):
        if portfolio_data.get("status") != "success":
            logger.info("No data available or invalid response.")
            return []
        holdings = portfolio_data.get("data", [])
    else:
        logger.info("Invalid portfolio data format")
        return []

    # Don't deduplicate - show all holdings as returned by Firstock (both NSE and BSE)
    mapped_holdings = []
    for holding in holdings:
        # Handle simple exchange/tradingSymbol structure (new Firstock format)
        if "exchange" in holding and "tradingSymbol" in holding:
            mapped_holding = {}

            # Map exchange trading fields
            mapped_holding["exch"] = holding.get("exchange", "")
            mapped_holding["token"] = holding.get("token", "")
            mapped_holding["trading_symbol"] = holding.get("tradingSymbol", "").replace(
                "-EQ", ""
            )  # Remove -EQ suffix
            mapped_holding["tsym"] = holding.get("tradingSymbol", "").replace(
                "-EQ", ""
            )  # Also set tsym
            mapped_holding["price_precision"] = int(holding.get("pricePrecision", "2"))
            mapped_holding["tick_size"] = float(holding.get("tickSize", "0.05"))
            mapped_holding["lot_size"] = int(holding.get("lotSize", "1"))

            # Get OpenAlgo symbol from token
            if holding.get("token"):
                symbol_from_db = get_symbol(holding.get("token"), holding.get("exchange"))
                if symbol_from_db:
                    mapped_holding["tsym"] = symbol_from_db
                else:
                    logger.info(
                        f"Symbol not found for token {holding.get('token')} and exchange {holding.get('exchange')}."
                    )
                    mapped_holding["tsym"] = mapped_holding["trading_symbol"]
            else:
                mapped_holding["tsym"] = mapped_holding["trading_symbol"]

            # Map holding fields - set default values for now
            lot_size = mapped_holding["lot_size"]

            # Firstock holdings API only provides symbol info, no quantity or price data
            # Setting minimal defaults to maintain API contract
            mapped_holding["holdqty"] = "0"  # No quantity data available
            mapped_holding["btstqty"] = "0"
            mapped_holding["usedqty"] = "0"
            mapped_holding["trade_qty"] = "0"
            mapped_holding["sell_amount"] = "0.000000"

            # No price data available from Firstock holdings API
            mapped_holding["upldprc"] = "0.00"  # No average price data
            mapped_holding["s_prdt_ali"] = "CNC"  # Default to CNC for holdings
            mapped_holding["cur_price"] = "0.00"  # No current price data

            # Add the holding
            mapped_holdings.append(mapped_holding)

    return mapped_holdings


def calculate_portfolio_statistics(holdings_data):
    """
    Calculates statistics from holdings data.

    Parameters:
    - holdings_data: List of holdings from map_portfolio_data

    Returns:
    - Dictionary containing portfolio statistics
    """
    totalholdingvalue = 0.0
    totalinvvalue = 0.0
    totalprofitandloss = 0.0
    totalpnlpercentage = 0.0

    if holdings_data:
        for holding in holdings_data:
            # Calculate total quantity in lots
            holdqty = int(float(holding.get("holdqty", 0)))
            btstqty = int(float(holding.get("btstqty", 0)))
            usedqty = int(float(holding.get("usedqty", 0)))
            trade_qty = int(float(holding.get("trade_qty", 0)))
            total_qty = holdqty + btstqty + trade_qty - usedqty

            # Get prices
            upld_price = float(holding.get("upldprc", 0.00))
            cur_price = float(holding.get("cur_price", 0.00))
            sell_amount = float(holding.get("sell_amount", 0.00))

            # Calculate values
            inv_value = total_qty * upld_price
            cur_value = total_qty * cur_price if cur_price > 0 else total_qty * upld_price

            # Update totals
            totalinvvalue += inv_value
            totalholdingvalue += cur_value
            totalprofitandloss += cur_value - inv_value + sell_amount

    # Calculate overall P&L percentage
    if totalinvvalue > 0:
        totalpnlpercentage = (totalprofitandloss / totalinvvalue) * 100

    return {
        "totalholdingvalue": round(totalholdingvalue, 2),
        "totalinvvalue": round(totalinvvalue, 2),
        "totalprofitandloss": round(totalprofitandloss, 2),
        "totalpnlpercentage": round(totalpnlpercentage, 2),
    }


def transform_holdings_data(holdings):
    """
    Transform holdings data to match OpenAlgo format.

    Parameters:
    - holdings: List of holdings from map_portfolio_data

    Returns:
    - List of transformed holdings in the format expected by holdings.html
    """
    logger.info(f"Input holdings: {holdings}")
    if not holdings:
        return []

    # Holdings are already mapped from map_portfolio_data
    mapped_holdings = holdings
    logger.info(f"Processing holdings: {mapped_holdings}")

    # Transform to final format
    transformed_holdings = []
    for holding in mapped_holdings:
        # Calculate total quantity in lots
        holdqty = int(float(holding.get("holdqty", 0)))
        btstqty = int(float(holding.get("btstqty", 0)))
        usedqty = int(float(holding.get("usedqty", 0)))
        trade_qty = int(float(holding.get("trade_qty", 0)))
        total_qty = holdqty + btstqty + trade_qty - usedqty

        # Get prices and amounts
        upld_price = float(holding.get("upldprc", 0.00))
        cur_price = float(holding.get("cur_price", 0.00))
        sell_amount = float(holding.get("sell_amount", 0.00))

        # Calculate P&L (will be 0 if no quantity/price data available)
        inv_value = total_qty * upld_price
        cur_value = total_qty * cur_price if cur_price > 0 else total_qty * upld_price
        pnl = cur_value - inv_value + sell_amount
        pnl_percent = (pnl / inv_value * 100) if inv_value > 0 else 0.0

        # Note: Firstock holdings API only provides symbol info
        # Quantity and P&L will be 0 due to API limitations
        transformed_holding = {
            "symbol": holding.get("tsym", ""),
            "exchange": holding.get("exch", ""),
            "quantity": total_qty,  # Will be 0 for Firstock
            "product": holding.get("s_prdt_ali", "CNC"),
            "pnl": round(pnl, 2),  # Will be 0 for Firstock
            "pnlpercent": round(pnl_percent, 2),  # Will be 0 for Firstock
        }
        transformed_holdings.append(transformed_holding)

    logger.info(f"Final transformed holdings: {transformed_holdings}")
    return transformed_holdings


def map_position_data(position_data):
    """
    Processes and modifies position data based on Firstock's format.

    Parameters:
    - position_data: Response from Firstock's position book API containing status and data fields

    Returns:
    - List of mapped positions in OpenAlgo format
    """
    # If it's a list, data is already mapped
    if isinstance(position_data, list):
        logger.debug("Position data is already mapped, returning as is")
        logger.debug(f"Number of positions: {len(position_data)}")
        return position_data

    # If it's a dict with status/data, it's raw API response
    if isinstance(position_data, dict):
        logger.debug("Raw position data received:")
        logger.info(f"DEBUG: Status: {position_data.get('status')}")
        logger.info(f"DEBUG: Data type: {type(position_data.get('data'))}")
        if position_data.get("status") != "success":
            logger.info("No data available or invalid response.")
            logger.info(f"DEBUG: Error message: {position_data.get('message', 'No error message')}")
            return []
        positions = position_data.get("data", [])  # Firstock returns list of positions
        logger.debug(f"Number of positions extracted: {len(positions)}")
    else:
        logger.debug(f"Invalid position data format. Type received: {type(position_data)}")
        return []

    mapped_positions = []
    for position in positions:
        logger.debug("\nDEBUG: Processing position:")
        logger.debug(f"Raw position data: {json.dumps(position, indent=2)}")
        mapped_position = {}
        # Get OpenAlgo symbol from token
        symbol_from_db = get_symbol(position.get("token"), position.get("exchange"))
        logger.info(
            f"DEBUG: Looking up symbol - Token: {position.get('token')}, Exchange: {position.get('exchange')}"
        )
        if symbol_from_db:
            mapped_position["tsym"] = symbol_from_db
            logger.debug(f"Symbol found in DB: {symbol_from_db}")
        else:
            logger.info(
                f"DEBUG: Symbol not found for token {position.get('token')} and exchange {position.get('exchange')}."
            )
            mapped_position["tsym"] = position.get("tradingSymbol", "")
            logger.info(f"DEBUG: Using trading symbol from response: {mapped_position['tsym']}")

        # Map product type (will be converted to CNC/MIS/NRML)
        mapped_position["prd"] = position.get("product", "")
        logger.info(f"DEBUG: Product type: {mapped_position['prd']}")

        # Map other fields
        mapped_position["exch"] = position.get("exchange", "")
        mapped_position["netqty"] = position.get("netQuantity", "0")
        mapped_position["netavgprc"] = position.get("netAveragePrice", "0.00")
        mapped_position["daybuyqty"] = position.get("dayBuyQuantity", "0")
        mapped_position["daysellqty"] = position.get("daySellQuantity", "0")
        mapped_position["daybuyamt"] = position.get("dayBuyAmount", "0.00")
        mapped_position["daybuyavgprc"] = position.get("dayBuyAveragePrice", "0.00")
        mapped_position["daysellamt"] = position.get("daySellAmount", "0.00")
        mapped_position["daysellavgprc"] = position.get("daySellAveragePrice", "0.00")
        mapped_position["unrealizedmtom"] = position.get("unrealizedMTOM", "0.00")
        mapped_position["realizedpnl"] = position.get("RealizedPNL", "0.00")

        logger.debug(f"Mapped position data: {json.dumps(mapped_position, indent=2)}")
        mapped_positions.append(mapped_position)

    logger.debug(f"\nDEBUG: Total positions mapped: {len(mapped_positions)}")
    return mapped_positions


def transform_positions_data(positions):
    """
    Transform position data to match OpenAlgo format.

    Parameters:
    - positions: List of positions from map_position_data

    Returns:
    - List of transformed positions in the format expected by positionbook.html
    """
    logger.info(f"Input positions: {positions}")
    if not positions:
        return []

    # First map the Firstock response to intermediate format
    mapped_positions = map_position_data(positions)
    logger.info(f"Mapped positions: {mapped_positions}")

    # Transform to final format
    transformed_positions = []
    for position in mapped_positions:
        # Convert product type
        if (position["exch"] == "NSE" or position["exch"] == "BSE") and position["prd"] == "C":
            position["prd"] = "CNC"
        elif position["prd"] == "I":
            position["prd"] = "MIS"
        elif position["exch"] in ["NFO", "MCX", "BFO", "CDS"] and position["prd"] == "M":
            position["prd"] = "NRML"

        transformed_position = {
            "symbol": position.get("tsym", ""),
            "exchange": position.get("exch", ""),
            "product": position.get("prd", ""),
            "quantity": position.get("netqty", "0"),
            "average_price": position.get("netavgprc", "0.00"),
            "last_price": "0.00",  # Not available in Firstock API
            "pnl": position.get("realizedpnl", "0.00"),
            "day_buy_quantity": position.get("daybuyqty", "0"),
            "day_sell_quantity": position.get("daysellqty", "0"),
            "day_buy_amount": position.get("daybuyamt", "0.00"),
            "day_sell_amount": position.get("daysellamt", "0.00"),
            "day_buy_average_price": position.get("daybuyavgprc", "0.00"),
            "day_sell_average_price": position.get("daysellavgprc", "0.00"),
            "unrealized_pnl": position.get("unrealizedmtom", "0.00"),
            "realized_pnl": position.get("realizedpnl", "0.00"),
        }
        transformed_positions.append(transformed_position)

    logger.info(f"Final transformed positions: {transformed_positions}")
    return transformed_positions

```


---

# FILE: broker\firstock\mapping\transform_data.py

```py
# Mapping OpenAlgo API Request https://openalgo.in/docs
# Mapping Firstock V1 API Parameters https://api.firstock.in/V1/placeOrder

import os

from database.token_db import get_br_symbol, get_symbol_info
from utils.logging import get_logger
from utils.mpp_slab import calculate_protected_price, get_instrument_type_from_symbol

logger = get_logger(__name__)


def transform_data(data, token, auth_token=None):
    """
    Transforms the OpenAlgo API request to Firstock's V1 /placeOrder structure.

    For MARKET and SL-M orders, applies client-side Market Price Protection
    (MPP): fetch LTP, compute a protected price via the OpenAlgo MPP slab,
    convert the order type to LMT / SL-LMT. Also sets mkt_protection="0" so
    Firstock's server-side MPP (V1.7+) is a no-op on the already-protected
    price. Mirrors the pattern in broker/shoonya and broker/flattrade.

    Args:
        data: Order data dictionary (OpenAlgo format).
        token: Instrument token (accepted for signature parity).
        auth_token: Firstock jKey. Required for MPP — if absent, MARKET/SL-M
                    flows through unchanged and Firstock's server-side MPP
                    handles it.
    """
    # Derive userId: prefer the apikey supplied in the request, fall back to
    # the BROKER_API_KEY env var (same source place_order_api uses to
    # overwrite userId just before sending). This makes transform_data robust
    # to callers like the close_position endpoint that don't include apikey.
    raw_apikey = data.get("apikey") or os.getenv("BROKER_API_KEY", "")
    userid = raw_apikey.replace("_API", "") if raw_apikey else ""

    # Get broker symbol and handle special characters
    symbol = get_br_symbol(data["symbol"], data["exchange"])
    if symbol and "&" in symbol:
        symbol = symbol.replace("&", "%26")

    # Default values
    price = str(data.get("price", "0"))
    order_type = map_order_type(data["pricetype"])
    action = data["action"].upper()

    # Apply MPP for MARKET and SL-M orders (V1.7 supports SL-MKT->SL-LMT too).
    if data["pricetype"] in ("MARKET", "SL-M"):
        original_type = data["pricetype"]
        logger.info(
            f"MPP: {original_type} order detected for Symbol={data['symbol']}, "
            f"Exchange={data['exchange']}, Action={action}"
        )
        try:
            if auth_token:
                # Lazy import to avoid circular dependency
                from broker.firstock.api.data import BrokerData

                broker_data = BrokerData(auth_token)
                quote_data = broker_data.get_quotes(data["symbol"], data["exchange"])
                logger.info(
                    f"MPP Quote Response: Symbol={data['symbol']}, Exchange={data['exchange']}, "
                    f"LTP={quote_data.get('ltp')}, Bid={quote_data.get('bid')}, Ask={quote_data.get('ask')}, "
                    f"TickSize={quote_data.get('tick_size')}"
                )

                instrument_type = get_instrument_type_from_symbol(data["symbol"])

                # Firstock's /getQuote response omits tick size, so fetch it
                # from the local master contract DB (same pattern as kotak).
                tick_size = quote_data.get("tick_size")
                if not tick_size:
                    symbol_info = get_symbol_info(data["symbol"], data["exchange"])
                    if symbol_info and symbol_info.tick_size:
                        tick_size = symbol_info.tick_size
                logger.info(
                    f"MPP Symbol Info: InstrumentType={instrument_type}, TickSize={tick_size}"
                )

                ltp = float(quote_data.get("ltp", 0))

                if ltp > 0:
                    protected_price = calculate_protected_price(
                        price=ltp,
                        action=action,
                        symbol=data["symbol"],
                        instrument_type=instrument_type,
                        tick_size=tick_size,
                    )
                    price = str(protected_price)
                    order_type = "LMT" if original_type == "MARKET" else "SL-LMT"
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

    transaction_type = "B" if action == "BUY" else "S"

    transformed = {
        "userId": userid,
        "exchange": data["exchange"],
        "tradingSymbol": symbol,
        "quantity": str(data["quantity"]),
        "price": price,
        "triggerPrice": str(data.get("trigger_price", "0")),
        "product": map_product_type(data["product"]),
        "transactionType": transaction_type,
        "priceType": order_type,
        "retention": "DAY",
        "mkt_protection": "0",
        "remarks": data.get("strategy", "Place Order"),
    }

    # Log order data without sensitive userId field
    safe_log = {k: v for k, v in transformed.items() if k != "userId"}
    logger.info(f"Transformed order data: {safe_log}")
    return transformed


def transform_modify_order_data(data, token, auth_token=None):
    """
    Transform modify order data to Firstock's V1 /modifyOrder format.

    V1.7 extended server-side MPP to modifyOrder too; for MARKET/SL-M we
    attempt the same client-side MARKET -> LMT / SL-M -> SL-LMT conversion
    used by transform_data so the price is owned by OpenAlgo. When we can't
    safely determine direction (action missing — modify requests often omit
    it) we skip client-side MPP and let Firstock's server-side MPP handle it
    using the original order's direction (which the broker knows).

    Expects data["symbol"] to be in OpenAlgo format; the broker symbol is
    derived locally via get_br_symbol.
    """
    oa_symbol = data["symbol"]
    exchange = data["exchange"]

    # Derive broker symbol for the outbound payload; handle & escaping.
    broker_symbol = get_br_symbol(oa_symbol, exchange) or oa_symbol
    if broker_symbol and "&" in broker_symbol:
        broker_symbol = broker_symbol.replace("&", "%26")

    price = str(data.get("price", "0"))
    order_type = map_order_type(data["pricetype"])

    # Do NOT default action — modify orders often omit it, and guessing
    # BUY would apply the wrong MPP direction to SELL modifications.
    action_raw = data.get("action")
    action = action_raw.upper() if action_raw else None

    # mkt_protection defaults to "0" for priced orders (LMT/SL-LMT). If the
    # order lands as MKT/SL-MKT (either because MPP was skipped or fell back),
    # V1.7 requires mkt_protection > 0 — set it to "1" (1%) in that branch.
    mkt_protection = "0"

    if data["pricetype"] in ("MARKET", "SL-M"):
        original_type = data["pricetype"]
        logger.info(
            f"Modify MPP: {original_type} detected for Symbol={oa_symbol}, "
            f"Exchange={exchange}, Action={action_raw!r}"
        )

        if not action:
            # Can't safely pick MPP direction without action. Let Firstock's
            # server-side MPP (V1.7+) handle it using the order's true side.
            logger.info(
                f"Modify MPP: action missing for {oa_symbol}; deferring to "
                f"server-side MPP with mkt_protection=1"
            )
            mkt_protection = "1"
        else:
            try:
                if auth_token:
                    from broker.firstock.api.data import BrokerData

                    broker_data = BrokerData(auth_token)
                    quote_data = broker_data.get_quotes(oa_symbol, exchange)
                    instrument_type = get_instrument_type_from_symbol(oa_symbol)

                    # Firstock's /getQuote response omits tick size, so fetch
                    # it from the local master contract DB (kotak pattern).
                    tick_size = quote_data.get("tick_size")
                    if not tick_size:
                        symbol_info = get_symbol_info(oa_symbol, exchange)
                        if symbol_info and symbol_info.tick_size:
                            tick_size = symbol_info.tick_size

                    ltp = float(quote_data.get("ltp", 0))

                    if ltp > 0:
                        protected_price = calculate_protected_price(
                            price=ltp,
                            action=action,
                            symbol=oa_symbol,
                            instrument_type=instrument_type,
                            tick_size=tick_size,
                        )
                        price = str(protected_price)
                        order_type = "LMT" if original_type == "MARKET" else "SL-LMT"
                        logger.info(
                            f"Modify MPP Conversion Complete: {original_type}->"
                            f"{order_type}, FinalPrice={protected_price}"
                        )
                    else:
                        logger.warning(
                            f"Modify MPP Warning: LTP<=0 for Symbol={oa_symbol}; "
                            f"sending {original_type} with mkt_protection=1"
                        )
                        mkt_protection = "1"
                else:
                    logger.warning(
                        f"Modify MPP Warning: No auth token for Symbol={oa_symbol}; "
                        f"sending {original_type} with mkt_protection=1"
                    )
                    mkt_protection = "1"
            except Exception as e:
                logger.error(
                    f"Modify MPP Error: Symbol={oa_symbol}, Error={str(e)}. "
                    f"Sending {original_type} with mkt_protection=1"
                )
                mkt_protection = "1"

    result = {
        "exchange": exchange,
        "orderNumber": data["orderid"],
        "priceType": order_type,
        "price": price,
        "quantity": str(data["quantity"]),
        "tradingSymbol": broker_symbol,
        "triggerPrice": str(data.get("trigger_price", "0")),
        "retention": "DAY",
        "mkt_protection": mkt_protection,
    }

    # product is optional on modify but included when supplied so V1 accepts
    # product changes (e.g. MIS -> CNC) alongside price/qty edits.
    if data.get("product"):
        result["product"] = map_product_type(data["product"])

    return result


def map_order_type(pricetype):
    """
    Maps the OpenAlgo pricetype to Firstock's order type.
    """
    order_type_mapping = {"MARKET": "MKT", "LIMIT": "LMT", "SL": "SL-LMT", "SL-M": "SL-MKT"}
    return order_type_mapping.get(pricetype, "MKT")  # Default to MKT if not found


def map_product_type(product):
    """
    Maps the OpenAlgo product type to Firstock's product type.
    """
    product_type_mapping = {"CNC": "C", "NRML": "M", "MIS": "I"}
    return product_type_mapping.get(product, "I")  # Default to I (MIS) if not found


def reverse_map_product_type(product):
    """
    Maps Firstock's product type to OpenAlgo product type.
    """
    reverse_product_type_mapping = {"C": "CNC", "M": "NRML", "I": "MIS"}
    return reverse_product_type_mapping.get(product, "MIS")  # Default to MIS if not found

```
