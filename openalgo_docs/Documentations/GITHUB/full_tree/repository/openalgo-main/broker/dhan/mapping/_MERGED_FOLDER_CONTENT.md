# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\dhan\mapping



---

# FILE: broker\dhan\mapping\gtt_data.py

```py
# Dhan Forever Order payload transforms (OpenAlgo ⇄ Dhan).
# Dhan v2 reference: https://dhanhq.co/docs/v2/forever/

from broker.dhan.mapping.transform_data import (
    map_exchange,
    map_exchange_type,
    map_product_type,
    reverse_map_product_type,
)
from database.token_db import get_oa_symbol, get_token


# Dhan Forever Order status → OpenAlgo GTT status.
_STATUS_MAP = {
    "TRANSIT": "active",
    "PENDING": "active",
    "CONFIRM": "active",
    "TRADED": "triggered",
    "EXPIRED": "expired",
    "CANCELLED": "cancelled",
    "REJECTED": "rejected",
}


def _resolve_single_trigger(data):
    """For SINGLE GTT, resolve the active trigger from new fields if the legacy
    ``trigger_price`` alias was not pre-populated by the schema (e.g., the UI
    modify route bypasses schema)."""
    if data.get("trigger_price") not in (None, "", 0, 0.0):
        return float(data["trigger_price"])
    sl = data.get("triggerprice_sl") or 0
    tg = data.get("triggerprice_tg") or 0
    return float(sl) if float(sl) > 0 else float(tg)


def transform_place_gtt(data):
    """Transform an OpenAlgo flat place-GTT payload into Dhan's POST /forever/orders body.

    SINGLE → ``triggerPrice`` (= resolved trigger) + ``price`` + ``quantity``.
    OCO    → primary (stoploss) leg uses ``price`` (= ``stoploss``) +
             ``triggerPrice`` (= ``triggerprice_sl``); target leg uses
             ``price1`` (= ``target``) + ``triggerPrice1``
             (= ``triggerprice_tg``) + ``quantity1`` (same qty).

    Caller must populate ``data['dhan_client_id']`` before calling.
    """
    security_id = get_token(data["symbol"], data["exchange"])
    trigger_type = (data.get("trigger_type") or "").upper()  # SINGLE | OCO

    if trigger_type == "SINGLE":
        primary_trigger = _resolve_single_trigger(data)
        primary_price = float(data["price"])
    else:  # OCO — primary leg = stoploss
        primary_trigger = float(data["triggerprice_sl"])
        primary_price = float(data["stoploss"])

    body = {
        "dhanClientId": str(data["dhan_client_id"]),
        "orderFlag": trigger_type,  # SINGLE | OCO — Dhan's exact spelling
        "transactionType": data["action"].upper(),
        "exchangeSegment": map_exchange_type(data["exchange"]),
        "productType": map_product_type(data["product"]),
        "orderType": data.get("pricetype", "LIMIT"),  # LIMIT | MARKET
        "validity": "DAY",
        "securityId": str(security_id),
        "quantity": int(data["quantity"]),
        "price": primary_price,
        "triggerPrice": primary_trigger,
    }

    if trigger_type == "OCO":
        body["price1"] = float(data["target"])
        body["triggerPrice1"] = float(data["triggerprice_tg"])
        body["quantity1"] = int(data["quantity"])

    # OpenAlgo's ``strategy`` doubles as Dhan's correlationId (max 30 chars).
    correlation_id = data.get("correlation_id") or data.get("strategy") or ""
    if correlation_id:
        body["correlationId"] = str(correlation_id)[:30]

    return body


def transform_modify_gtt(data, leg_name):
    """Transform an OpenAlgo modify-GTT payload into Dhan's PUT /forever/orders/{id} body.

    Dhan modifies one leg at a time. Field semantics dispatch by
    ``trigger_type`` (the OpenAlgo flag), not by ``leg_name`` — Dhan's leg
    labels for SINGLE orders can be ENTRY_LEG / STOP_LOSS_LEG / TARGET_LEG
    depending on the action+trigger relationship to LTP at place-time, but
    for OpenAlgo a SINGLE always carries its values in ``price`` and the
    resolved trigger.

        - SINGLE (any leg_name) → ``price`` + resolved trigger.
        - OCO + STOP_LOSS_LEG  → ``stoploss`` + ``triggerprice_sl``.
        - OCO + TARGET_LEG     → ``target``   + ``triggerprice_tg``.

    ``leg_name`` is forwarded as Dhan's API tag so the PUT targets the right
    leg.
    """
    trigger_type = (data.get("trigger_type") or "").upper()

    if trigger_type == "OCO":
        if leg_name == "TARGET_LEG":
            leg_price = float(data["target"])
            leg_trigger = float(data["triggerprice_tg"])
        else:  # STOP_LOSS_LEG
            leg_price = float(data["stoploss"])
            leg_trigger = float(data["triggerprice_sl"])
    else:  # SINGLE — leg_name is a Dhan tag only, values come from SINGLE fields.
        leg_price = float(data["price"])
        leg_trigger = _resolve_single_trigger(data)

    return {
        "dhanClientId": str(data["dhan_client_id"]),
        "orderId": str(data["trigger_id"]),
        "orderFlag": trigger_type,
        "orderType": data.get("pricetype", "LIMIT"),
        "legName": leg_name,
        "quantity": int(data["quantity"]),
        "price": leg_price,
        "triggerPrice": leg_trigger,
        "validity": "DAY",
    }


def map_gtt_book(gtt_list):
    """Normalise Dhan's GET /forever/orders response into an OpenAlgo-shaped list.

    Dhan returns a flat list of legs (one row per leg). SINGLE has one leg
    (``ENTRY_LEG``); OCO has two (``STOP_LOSS_LEG`` + ``TARGET_LEG``) sharing
    one ``orderId``. We group by orderId, sort triggers ascending, and emit
    one OpenAlgo entry per order. ``last_price`` is not returned by Dhan, so
    it is left as 0 — the frontend will display "₹0.00".
    """
    if not isinstance(gtt_list, list):
        return []

    # Active-only filter: drop TRADED/EXPIRED/CANCELLED/REJECTED at the broker
    # mapper so the orderbook UI shows only triggers that can still fire.
    _ACTIVE_RAW = {"TRANSIT", "PENDING", "CONFIRM"}

    grouped = {}
    for item in gtt_list:
        oid = str(item.get("orderId", "") or "")
        if not oid:
            continue
        if (item.get("orderStatus") or "").upper() not in _ACTIVE_RAW:
            continue
        grouped.setdefault(oid, []).append(item)

    result = []
    for oid, legs in grouped.items():
        first = legs[0]
        ex = map_exchange(first.get("exchangeSegment", "")) or ""
        br_sym = first.get("tradingSymbol", "")
        oa_sym = (
            get_oa_symbol(brsymbol=br_sym, exchange=ex) if br_sym and ex else br_sym
        )

        # Sort legs so STOP_LOSS_LEG (lower trigger) comes first for OCO.
        sorted_legs = sorted(
            legs, key=lambda l: float(l.get("triggerPrice", 0) or 0)
        )
        trigger_prices = [float(l.get("triggerPrice", 0) or 0) for l in sorted_legs]

        out_legs = []
        for leg in sorted_legs:
            leg_price = float(leg.get("price", 0) or 0)
            # Dhan's GET response doesn't expose LIMIT/MARKET — infer from price.
            # MARKET GTTs are stored with price=0; LIMIT GTTs carry the limit.
            inferred_pricetype = "MARKET" if leg_price == 0 else "LIMIT"
            out_legs.append({
                "action": (leg.get("transactionType", "") or "").upper(),
                "quantity": leg.get("quantity", 0),
                "price": leg.get("price", 0),
                "pricetype": inferred_pricetype,
                "product": reverse_map_product_type(leg.get("productType", "")) or "CNC",
                # Dhan-internal legName needed by modify (STOP_LOSS_LEG / TARGET_LEG / ENTRY_LEG).
                "leg_name": leg.get("legName", "") or "",
            })

        # Dhan reuses the ``orderType`` field in the GET response for the SINGLE/OCO flag.
        flag = (first.get("orderType") or "").upper()
        trigger_type_oa = "two-leg" if flag == "OCO" else "single"
        status_raw = (first.get("orderStatus") or "").upper()

        result.append({
            "trigger_id": oid,
            "trigger_type": trigger_type_oa,
            "status": _STATUS_MAP.get(status_raw, status_raw.lower()),
            "symbol": oa_sym or br_sym,
            "exchange": ex,
            "trigger_prices": trigger_prices,
            "last_price": 0,  # Dhan does not return LTP in this response
            "legs": out_legs,
            "created_at": first.get("createTime", "") or "",
            "updated_at": first.get("updateTime", "") or "",
            # Dhan Forever Orders have no explicit expiry — leave blank.
            "expires_at": "",
        })

    return result

```


---

# FILE: broker\dhan\mapping\margin_data.py

```py
# Mapping OpenAlgo API Request https://openalgo.in/docs
# Mapping Dhan Margin API https://dhanhq.co/docs/v2/funds/

from broker.dhan.mapping.transform_data import map_exchange_type, map_order_type, map_product_type
from database.token_db import get_token
from utils.logging import get_logger

logger = get_logger(__name__)


def transform_margin_position(position, client_id):
    """
    Transform a single OpenAlgo margin position to Dhan margin format.

    Note: Dhan margin calculator API accepts only one order at a time, not a batch.

    Args:
        position: Position in OpenAlgo format
        client_id: Dhan client ID

    Returns:
        Dict in Dhan margin format or None if transformation fails
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
    Maps OpenAlgo product type to Dhan product type for margin calculation.

    OpenAlgo: CNC, NRML, MIS
    Dhan: CNC, MARGIN, INTRADAY, MTF, CO, BO
    """
    product_type_mapping = {
        "CNC": "CNC",
        "NRML": "MARGIN",
        "MIS": "INTRADAY",
    }
    return product_type_mapping.get(product, "INTRADAY")


def parse_margin_response(response_data):
    """
    Parse Dhan margin response to OpenAlgo standard format.

    According to Dhan API docs, response includes:
    - totalMargin: Total margin required for placing the order
    - spanMargin: SPAN margin required
    - exposureMargin: Exposure margin required
    - availableBalance: Available amount in trading account
    - variableMargin: VAR or variable margin required
    - insufficientBalance: Insufficient amount in account
    - brokerage: Brokerage charges
    - leverage: Margin leverage based on product type

    Args:
        response_data: Raw response from Dhan API

    Returns:
        Standardized margin response matching OpenAlgo format
    """
    try:
        if not response_data or not isinstance(response_data, dict):
            return {"status": "error", "message": "Invalid response from broker"}

        # Check for error response
        if response_data.get("errorType") or response_data.get("status") == "failed":
            error_message = response_data.get("errorMessage", "Failed to calculate margin")
            return {"status": "error", "message": error_message}

        # Extract margin values from response
        total_margin = float(response_data.get("totalMargin", 0))
        span_margin = float(response_data.get("spanMargin", 0))
        exposure_margin = float(response_data.get("exposureMargin", 0))

        # Return standardized format (only essential fields)
        return {
            "status": "success",
            "data": {
                "total_margin_required": total_margin,
                "span_margin": span_margin,
                "exposure_margin": exposure_margin,
            },
        }

    except Exception as e:
        logger.error(f"Error parsing margin response: {e}")
        return {"status": "error", "message": f"Failed to parse margin response: {str(e)}"}


def parse_batch_margin_response(responses):
    """
    Parse multiple Dhan margin responses and aggregate them by simple summation.

    IMPORTANT - Limitation:
    Since Dhan API only supports single-leg margin calculation, we calculate
    each leg individually and SUM the results. This approach:

    ✓ Works correctly for independent positions
    ✗ Does NOT account for spread/hedge benefits in combo strategies
    ✗ Does NOT provide portfolio-level margin optimization

    Example:
    - Short Straddle (CE + PE): Sum of individual margins (no hedge benefit)
    - Iron Condor: Sum of 4 individual leg margins (no spread benefit)

    This is a limitation of the Dhan API, not OpenAlgo.

    Args:
        responses: List of individual margin responses (one per leg)

    Returns:
        Aggregated margin response matching OpenAlgo format
    """
    try:
        total_margin = 0
        total_span = 0
        total_exposure = 0
        successful_legs = 0

        logger.info("AGGREGATING INDIVIDUAL LEG MARGINS")
        logger.info("-" * 80)

        for idx, response in enumerate(responses, 1):
            if response.get("status") == "success":
                data = response.get("data", {})
                leg_margin = data.get("total_margin_required", 0)
                leg_span = data.get("span_margin", 0)
                leg_exposure = data.get("exposure_margin", 0)

                total_margin += leg_margin
                total_span += leg_span
                total_exposure += leg_exposure
                successful_legs += 1

                logger.debug(
                    f"Leg {idx}: Total={leg_margin:,.2f}, SPAN={leg_span:,.2f}, Exposure={leg_exposure:,.2f}"
                )

        logger.info(f"Successfully aggregated {successful_legs} legs")
        logger.info(f"Total Margin (Sum):      Rs. {total_margin:,.2f}")
        logger.info(f"Total SPAN (Sum):        Rs. {total_span:,.2f}")
        logger.info(f"Total Exposure (Sum):    Rs. {total_exposure:,.2f}")
        logger.info("-" * 80)

        return {
            "status": "success",
            "data": {
                "total_margin_required": total_margin,
                "span_margin": total_span,
                "exposure_margin": total_exposure,
            },
        }

    except Exception as e:
        logger.error(f"Error parsing batch margin response: {e}")
        return {"status": "error", "message": f"Failed to parse batch margin response: {str(e)}"}

```


---

# FILE: broker\dhan\mapping\order_data.py

```py
import json

from broker.dhan.mapping.transform_data import map_exchange
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
            "timestamp": order.get("updateTime", ""),
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
            "timestamp": trade.get("updateTime", ""),
        }
        transformed_data.append(transformed_trade)
    return transformed_data


def map_position_data(position_data):
    return map_order_data(position_data)


def transform_positions_data(positions_data):
    # Dhan's /v2/positions doesn't include LTP unlike other brokers
    # Fetch LTP via multiquotes service (same pattern as sandbox mode)
    ltp_map = {}
    if positions_data:
        try:
            from database.auth_db import ApiKeys, decrypt_token
            from services.quotes_service import get_multiquotes

            api_key_obj = ApiKeys.query.first()
            if api_key_obj:
                api_key = decrypt_token(api_key_obj.api_key_encrypted)
                symbols_payload = [
                    {"symbol": pos.get("tradingSymbol", ""), "exchange": pos.get("exchangeSegment", "")}
                    for pos in positions_data
                    if pos.get("tradingSymbol") and pos.get("exchangeSegment")
                ]
                if symbols_payload:
                    success, response, _ = get_multiquotes(symbols=symbols_payload, api_key=api_key)
                    if success and "results" in response:
                        for result in response["results"]:
                            if "data" in result and result["data"]:
                                key = f"{result['exchange']}:{result['symbol']}"
                                ltp_map[key] = float(result["data"].get("ltp", 0))
        except Exception as e:
            logger.warning(f"Failed to fetch LTP via multiquotes: {e}")

    transformed_data = []
    for position in positions_data:
        realized_pnl = float(position.get("realizedProfit", 0))
        unrealized_pnl = float(position.get("unrealizedProfit", 0))
        symbol = position.get("tradingSymbol", "")
        exchange = position.get("exchangeSegment", "")
        ltp = ltp_map.get(f"{exchange}:{symbol}", 0.0)

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


def map_portfolio_data(portfolio_data):
    """Validate the Dhan /holdings response and enrich each row with LTP +
    real exchange so the downstream stats and transform stages can render
    a meaningful row on first paint.

    Dhan returns ``exchange="ALL"`` for every holding (demat is exchange-
    agnostic) and the /holdings endpoint does NOT include LTP. We resolve
    the actual listing exchange via the SymToken cache (probing NSE then
    BSE using the broker-returned ``securityId``) and batch-fetch LTPs
    via the multiquote service — same pattern transform_positions_data
    uses for the same reason.

    Enrichment writes three private fields into each holding dict that
    calculate_portfolio_statistics and transform_holdings_data both
    consume:

    - ``_oa_symbol``: OpenAlgo symbol resolved from securityId+exchange
    - ``_exchange``: real exchange ("NSE" or "BSE"), never "ALL"
    - ``_ltp``: last-traded price (0.0 if multiquote failed/missing — the
      frontend's useLivePrice hook fills it in via WebSocket within seconds)
    """
    if portfolio_data is None or (
        isinstance(portfolio_data, dict)
        and (
            portfolio_data.get("errorCode") == "DHOLDING_ERROR"
            or portfolio_data.get("internalErrorCode") == "DH-1111"
            or portfolio_data.get("internalErrorMessage") == "No holdings available"
        )
    ):
        logger.info("No data or no holdings available.")
        return {}
    if not isinstance(portfolio_data, list):
        return {}

    # Resolve exchange per holding via SymToken cache. securityId is the
    # Dhan broker token and is exchange-scoped, so a single hit uniquely
    # identifies the listing. Probe NSE first (most equity), then BSE.
    for h in portfolio_data:
        security_id = str(h.get("securityId", "") or "")
        trading_sym = h.get("tradingSymbol", "")
        resolved_exchange = None
        resolved_symbol = trading_sym
        if security_id:
            for candidate in ("NSE", "BSE"):
                sym = get_symbol(security_id, candidate)
                if sym:
                    resolved_exchange = candidate
                    resolved_symbol = sym
                    break
        h["_oa_symbol"] = resolved_symbol
        h["_exchange"] = resolved_exchange or "NSE"
        h["_ltp"] = 0.0

    # Batch-fetch LTPs via multiquote.
    try:
        from database.auth_db import ApiKeys, decrypt_token
        from services.quotes_service import get_multiquotes

        api_key_obj = ApiKeys.query.first()
        if api_key_obj:
            api_key = decrypt_token(api_key_obj.api_key_encrypted)
            symbols_payload = [
                {"symbol": h["_oa_symbol"], "exchange": h["_exchange"]}
                for h in portfolio_data
                if h.get("_oa_symbol") and h.get("_exchange")
            ]
            if symbols_payload:
                success, response, _ = get_multiquotes(
                    symbols=symbols_payload, api_key=api_key
                )
                if success and isinstance(response, dict) and "results" in response:
                    ltp_map = {}
                    for result in response["results"]:
                        if isinstance(result, dict) and result.get("data"):
                            key = f"{result.get('exchange')}:{result.get('symbol')}"
                            ltp_map[key] = float(result["data"].get("ltp", 0) or 0)
                    for h in portfolio_data:
                        key = f"{h['_exchange']}:{h['_oa_symbol']}"
                        if key in ltp_map:
                            h["_ltp"] = ltp_map[key]
    except Exception as e:
        logger.warning(f"Failed to fetch LTP via multiquotes for holdings: {e}")

    return portfolio_data


def calculate_portfolio_statistics(holdings_data):
    if not holdings_data:
        return {
            "totalholdingvalue": 0,
            "totalinvvalue": 0,
            "totalprofitandloss": 0,
            "totalpnlpercentage": 0,
        }
    totalinvvalue = sum(
        float(item.get("avgCostPrice", 0) or 0) * int(item.get("totalQty", 0) or 0)
        for item in holdings_data
    )
    # Prefer the enriched _ltp when present; fall back to avg cost so the
    # value is at least equal to investment (i.e. zero P&L) instead of zero
    # holding value before the frontend's useLivePrice fills in live LTP.
    totalholdingvalue = sum(
        (float(item.get("_ltp", 0) or 0) or float(item.get("avgCostPrice", 0) or 0))
        * int(item.get("totalQty", 0) or 0)
        for item in holdings_data
    )
    totalprofitandloss = totalholdingvalue - totalinvvalue
    totalpnlpercentage = (totalprofitandloss / totalinvvalue * 100) if totalinvvalue else 0
    return {
        "totalholdingvalue": totalholdingvalue,
        "totalinvvalue": totalinvvalue,
        "totalprofitandloss": totalprofitandloss,
        "totalpnlpercentage": totalpnlpercentage,
    }


def transform_holdings_data(holdings_data):
    transformed_data = []
    if not holdings_data:
        return transformed_data
    for h in holdings_data:
        qty = int(h.get("totalQty", 0) or 0)
        avg = float(h.get("avgCostPrice", 0) or 0)
        ltp = float(h.get("_ltp", 0) or 0)
        if ltp > 0 and avg > 0:
            pnl = round((ltp - avg) * qty, 2)
            pnlpercent = round((ltp - avg) / avg * 100, 2)
        else:
            pnl = 0.0
            pnlpercent = 0.0
        transformed_data.append({
            "symbol": h.get("_oa_symbol") or h.get("tradingSymbol", ""),
            "exchange": h.get("_exchange") or "NSE",
            "quantity": qty,
            "product": "CNC",
            "average_price": round(avg, 2),
            "ltp": round(ltp, 2),
            "pnl": pnl,
            "pnlpercent": pnlpercent,
        })
    return transformed_data

```


---

# FILE: broker\dhan\mapping\transform_data.py

```py
# Mapping OpenAlgo API Request https://openalgo.in/docs
# Mapping Upstox Broking Parameters https://dhanhq.co/docs/v2/orders/


def transform_data(data, token):
    """
    Transforms the OpenAlgo API request structure to Dhan v2 API structure.
    Based on the exact structure from Dhan documentation.
    """
    # Build payload exactly as shown in Dhan documentation
    transformed = {
        "dhanClientId": data.get("dhan_client_id", data["apikey"]),
        "transactionType": data["action"].upper(),
        "exchangeSegment": map_exchange_type(data["exchange"]),
        "productType": map_product_type(data["product"]),
        "orderType": map_order_type(data["pricetype"]),
        "validity": "DAY",
        "securityId": token,
        "quantity": int(data["quantity"]),
    }

    # Add optional fields only if needed
    correlation_id = data.get("correlation_id", "")
    if correlation_id:
        transformed["correlationId"] = correlation_id

    # Set price for non-market orders
    if data["pricetype"] != "MARKET":
        price = float(data.get("price", 0))
        transformed["price"] = float(price)

    # Set disclosed quantity if provided
    disclosed_qty = int(data.get("disclosed_quantity", 0))
    if disclosed_qty > 0:
        transformed["disclosedQuantity"] = disclosed_qty

    # Set trigger price for SL orders
    if data["pricetype"] in ["SL", "SL-M"]:
        trigger_price = float(data.get("trigger_price", 0))
        if trigger_price > 0:
            transformed["triggerPrice"] = float(trigger_price)
        else:
            raise ValueError("Trigger price is required for Stop Loss orders")

    # Handle after market orders
    after_market = data.get("after_market_order", False)
    if after_market:
        transformed["afterMarketOrder"] = True
        amo_time = data.get("amo_time", "")
        if amo_time in ["PRE_OPEN", "OPEN", "OPEN_30", "OPEN_60"]:
            transformed["amoTime"] = amo_time

    # Handle bracket order values
    if data.get("product") == "BO":
        bo_profit = data.get("bo_profit_value")
        bo_stop_loss = data.get("bo_stop_loss_value")
        if bo_profit:
            transformed["boProfitValue"] = float(bo_profit)
        if bo_stop_loss:
            transformed["boStopLossValue"] = float(bo_stop_loss)

    # Handle IOC validity
    if data.get("validity") == "IOC":
        transformed["validity"] = "IOC"

    return transformed


def transform_modify_order_data(data):
    modified = {
        "dhanClientId": data.get("dhan_client_id", data["apikey"]),
        "orderId": data["orderid"],
        "orderType": map_order_type(data["pricetype"]),
        "legName": "ENTRY_LEG",
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
