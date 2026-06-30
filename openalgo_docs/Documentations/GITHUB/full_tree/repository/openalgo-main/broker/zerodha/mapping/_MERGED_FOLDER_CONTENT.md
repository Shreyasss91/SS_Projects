# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\zerodha\mapping



---

# FILE: broker\zerodha\mapping\gtt_data.py

```py
# Zerodha GTT payload transforms (OpenAlgo ⇄ Kite).
# Kite Connect GTT API reference: https://kite.trade/docs/connect/v3/gtt/

from database.token_db import get_br_symbol, get_oa_symbol


def _build_order(data, price, tradingsymbol, exchange):
    """Build one Kite `orders[]` entry sharing action/qty/product/pricetype across legs."""
    return {
        "exchange": exchange,
        "tradingsymbol": tradingsymbol,
        "transaction_type": data["action"].upper(),
        "quantity": int(data["quantity"]),
        "order_type": data.get("pricetype", "LIMIT"),
        "product": data["product"],
        "price": float(price),
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
    """Transform an OpenAlgo flat place-GTT payload into Kite's `{type, condition, orders}`.

    Expected ``data`` keys (post-schema):
        symbol, exchange, trigger_type ("SINGLE" | "OCO"), action, product,
        quantity, pricetype, price, last_price, and:
        - SINGLE → trigger_price (legacy alias resolved by the schema).
        - OCO    → triggerprice_sl + stoploss + triggerprice_tg + target.

    Mapping:
        SINGLE → trigger=trigger_price, limit=price.
        OCO    → stoploss leg (trigger=triggerprice_sl, limit=stoploss) +
                 target   leg (trigger=triggerprice_tg, limit=target).
                 trigger_values is sorted low→high as Kite requires.

    Caller is responsible for JSON-encoding ``condition`` and ``orders`` and
    URL-encoding the form.
    """
    tradingsymbol = get_br_symbol(data["symbol"], data["exchange"])
    exchange = data["exchange"]
    trigger_type_oa = (data.get("trigger_type") or "").upper()

    if trigger_type_oa == "OCO":
        kite_type = "two-leg"
        trigger_values = [float(data["triggerprice_sl"]), float(data["triggerprice_tg"])]
        orders = [
            _build_order(data, data["stoploss"], tradingsymbol, exchange),
            _build_order(data, data["target"], tradingsymbol, exchange),
        ]
    else:  # SINGLE
        kite_type = "single"
        trigger_values = [_resolve_single_trigger(data)]
        orders = [_build_order(data, data["price"], tradingsymbol, exchange)]

    condition = {
        "exchange": exchange,
        "tradingsymbol": tradingsymbol,
        "trigger_values": trigger_values,
        "last_price": float(data["last_price"]),
    }

    return {"type": kite_type, "condition": condition, "orders": orders}


def transform_modify_gtt(data):
    """Transform an OpenAlgo modify-GTT payload (flat shape) into Kite's body.

    Kite's PUT /gtt/triggers/:id takes the same ``{type, condition, orders}``
    shape as POST, so the place transform is reused.
    """
    return transform_place_gtt(data)


def map_gtt_book(gtt_data):
    """Normalise Kite's GET /gtt/triggers response into an OpenAlgo-shaped list.

    Kite returns ``{"status": "success", "data": [{...}, ...]}``. Each GTT has
    ``id``, ``user_id``, ``type``, ``status``, ``condition``, ``orders``, ``created_at``, ``updated_at``,
    ``expires_at``, ``meta``. We flatten to a broker-neutral shape and translate the
    Kite tradingsymbol back to OpenAlgo's symbol.
    """
    if not isinstance(gtt_data, dict):
        return []

    data = gtt_data.get("data") or []
    normalised = []

    # Active-only filter: drop triggered/disabled/expired/cancelled/rejected/
    # deleted at the broker mapper so the orderbook UI shows only triggers
    # that can still fire. Kite's GTT statuses: active, triggered, disabled,
    # expired, cancelled, rejected, deleted.
    for gtt in data:
        if (gtt.get("status") or "").lower() != "active":
            continue
        condition = gtt.get("condition") or {}
        orders = gtt.get("orders") or []
        exchange = condition.get("exchange", "")
        br_symbol = condition.get("tradingsymbol", "")
        oa_symbol = get_oa_symbol(brsymbol=br_symbol, exchange=exchange) if br_symbol else ""

        legs = []
        for order in orders:
            legs.append(
                {
                    "action": order.get("transaction_type", ""),
                    "quantity": order.get("quantity", 0),
                    "price": order.get("price", 0),
                    "pricetype": order.get("order_type", "LIMIT"),
                    "product": order.get("product", ""),
                }
            )

        normalised.append(
            {
                "trigger_id": str(gtt.get("id", "")),
                "trigger_type": gtt.get("type", ""),
                "status": gtt.get("status", ""),
                "symbol": oa_symbol or br_symbol,
                "exchange": exchange,
                "trigger_prices": condition.get("trigger_values", []),
                "last_price": condition.get("last_price", 0),
                "legs": legs,
                "created_at": gtt.get("created_at", ""),
                "updated_at": gtt.get("updated_at", ""),
                "expires_at": gtt.get("expires_at", ""),
            }
        )

    return normalised

```


---

# FILE: broker\zerodha\mapping\margin_data.py

```py
# Mapping OpenAlgo API Request https://openalgo.in/docs
# Mapping Zerodha Margin API https://kite.trade/docs/connect/v3/margins/

from database.token_db import get_br_symbol
from utils.logging import get_logger

logger = get_logger(__name__)


def transform_margin_positions(positions):
    """
    Transform OpenAlgo margin position format to Zerodha margin format.

    Args:
        positions: List of positions in OpenAlgo format

    Returns:
        List of positions in Zerodha format
    """
    transformed_positions = []
    skipped_positions = []

    for position in positions:
        try:
            symbol = position["symbol"]
            exchange = position["exchange"]

            # Get the broker symbol for Zerodha
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
                "exchange": exchange,
                "tradingsymbol": br_symbol_str,
                "transaction_type": position["action"].upper(),
                "variety": "regular",  # Default variety for margin calculation
                "product": map_product_type(position["product"]),
                "order_type": map_order_type(position["pricetype"]),
                "quantity": int(position["quantity"]),
                "price": float(position.get("price", 0)),
                "trigger_price": float(position.get("trigger_price", 0)),
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


def map_product_type(product):
    """
    Maps OpenAlgo product type to Zerodha product type.

    OpenAlgo: CNC, NRML, MIS
    Zerodha: CNC, NRML, MIS (Direct mapping - no transformation needed)
    """
    product_type_mapping = {
        "CNC": "CNC",
        "NRML": "NRML",
        "MIS": "MIS",
    }
    return product_type_mapping.get(product, "MIS")


def map_order_type(pricetype):
    """
    Maps OpenAlgo price type to Zerodha order type.

    OpenAlgo: MARKET, LIMIT, SL, SL-M
    Zerodha: MARKET, LIMIT, SL, SL-M (Direct mapping - no transformation needed)
    """
    order_type_mapping = {"MARKET": "MARKET", "LIMIT": "LIMIT", "SL": "SL", "SL-M": "SL-M"}
    return order_type_mapping.get(pricetype, "MARKET")


def parse_margin_response(response_data):
    """
    Parse Zerodha margin response to OpenAlgo standard format.

    Zerodha basket margin response structure:
    - data.initial: Total margins from basket calculation (partially optimized)
    - data.final: Total margins WITH full spread benefit (fully optimized)
    - data.orders: Individual order margins in the basket context

    IMPORTANT NOTE ON MARGIN BENEFIT:
    Zerodha's basket API returns initial.total that is ALREADY partially optimized.
    For example, in a short straddle:
    - orders[CE].span = 179,780 (full span)
    - orders[PE].span = 0 (hedged, no span required!)
    - initial.total = sum of optimized orders = 258,139

    Whereas final.total = 191,119 is the fully-optimized basket margin that
    matches what Kite's web UI displays for the basket. We surface final.total
    as total_margin_required (see extraction below) because initial.total over-
    states margin for defined-risk structures where only one leg is hedged.

    To get TRUE margin benefit (matching Zerodha's web UI):
    - TRUE individual total = Call each order separately and sum = 429,255
    - Basket final total = 191,119
    - TRUE margin benefit = 429,255 - 191,119 = 238,136

    Basket API only provides:
    - initial.total - final.total = 258,139 - 191,119 = 67,020 (option_premium)

    For true individual margins, each position must be queried separately first.

    Args:
        response_data: Raw response from Zerodha API

    Returns:
        Standardized margin response matching OpenAlgo format
    """
    try:
        if not response_data or not isinstance(response_data, dict):
            return {"status": "error", "message": "Invalid response from broker"}

        # Check if the response has the expected structure
        if response_data.get("status") != "success":
            error_message = response_data.get("message", "Failed to calculate margin")
            # Check for error_type field in Zerodha responses
            if "error_type" in response_data:
                error_message = f"{response_data.get('error_type')}: {error_message}"
            return {"status": "error", "message": error_message}

        # Extract margin data
        data = response_data.get("data", {})

        # Initialize variables
        total_margin_required = 0
        span_margin = 0
        exposure_margin = 0
        margin_benefit = 0

        if isinstance(data, dict) and "final" in data:
            # Basket response - use final values which include spread benefit
            initial = data.get("initial", {})
            final = data.get("final", {})

            # Extract all margin components.
            # IMPORTANT: Use final.total (fully-optimized) — initial.total only
            # applies partial optimization (hedged leg's SPAN drops to 0 but the
            # short leg retains its full naked SPAN). For defined-risk
            # strategies (verticals, iron condors, butterflies) the optimized
            # final.total is what Kite web UI displays and is materially lower
            # — e.g. a Bull Put Spread's initial.total of ~Rs.2.26L collapses
            # to a fraction once the spread's capped max-loss is recognized.
            total_margin_required = final.get("total", 0)
            span_margin = final.get("span", 0)
            exposure_margin = final.get("exposure", 0)
            option_premium = final.get("option_premium", 0)
            additional = final.get("additional", 0)
            bo = final.get("bo", 0)
            cash = final.get("cash", 0)
            var = final.get("var", 0)

            # Extract initial values (individual position margins)
            initial_total = initial.get("total", 0)
            initial_span = initial.get("span", 0)
            initial_exposure = initial.get("exposure", 0)
            initial_option_premium = initial.get("option_premium", 0)

            final_total = final.get("total", 0)

            # Calculate margin benefit (savings from spread/hedge recognition)
            # Formula: Margin Benefit = Sum of Individual Margins - Optimized Combined Margin
            # Example: 4,27,882 (individual) - 2,56,121 (optimized) = 1,71,761 (benefit)
            margin_benefit = initial_total - final_total

            logger.info("=" * 80)
            logger.info("ZERODHA BASKET MARGIN - DETAILED BREAKDOWN")
            logger.info("=" * 80)
            logger.info("BASKET INITIAL VALUES (Partially Optimized):")
            logger.info(f"  initial.total           = Rs. {initial_total:,.2f}")
            logger.info(f"  initial.span            = Rs. {initial_span:,.2f}")
            logger.info(f"  initial.exposure        = Rs. {initial_exposure:,.2f}")
            logger.info(f"  initial.option_premium  = Rs. {initial_option_premium:,.2f}")
            logger.info("")
            logger.info("BASKET FINAL VALUES (Fully Optimized):")
            logger.info(f"  final.total             = Rs. {final_total:,.2f}")
            logger.info(f"  final.span              = Rs. {span_margin:,.2f}")
            logger.info(f"  final.exposure          = Rs. {exposure_margin:,.2f}")
            logger.info(f"  final.option_premium    = Rs. {option_premium:,.2f}")
            logger.info(f"  final.additional        = Rs. {additional:,.2f}")
            logger.info(f"  final.bo                = Rs. {bo:,.2f}")
            logger.info(f"  final.cash              = Rs. {cash:,.2f}")
            logger.info(f"  final.var               = Rs. {var:,.2f}")
            logger.info("")
            logger.info("MARGIN BENEFIT (From Basket API):")
            logger.info("  Formula: initial.total - final.total")
            logger.info(
                f"  Calculation: {initial_total:,.2f} - {final_total:,.2f} = Rs. {margin_benefit:,.2f}"
            )
            logger.info(
                f"  Note: This equals option_premium change ({option_premium - initial_option_premium:,.2f})"
            )
            logger.info("")
            logger.warning(
                "⚠ IMPORTANT: Zerodha's basket initial.total is ALREADY partially optimized!"
            )
            logger.warning(
                "⚠ For TRUE margin benefit matching web UI, query each order separately first."
            )
            logger.info("=" * 80)

            # Log individual order margins if available
            orders = data.get("orders", [])
            if orders:
                logger.info("INDIVIDUAL ORDER MARGINS IN BASKET:")
                logger.info("-" * 80)
                basket_orders_sum = 0
                for idx, order in enumerate(orders, 1):
                    order_total = order.get("total", 0)
                    order_span = order.get("span", 0)
                    order_exposure = order.get("exposure", 0)
                    order_premium = order.get("option_premium", 0)
                    basket_orders_sum += order_total

                    hedged_note = " ← HEDGED (Zero SPAN!)" if order_span == 0 else ""
                    logger.info(f"Order {idx}: {order.get('tradingsymbol', 'N/A')}")
                    logger.info(f"  Span:            Rs. {order_span:,.2f}{hedged_note}")
                    logger.info(f"  Exposure:        Rs. {order_exposure:,.2f}")
                    logger.info(f"  Option Premium:  Rs. {order_premium:,.2f}")
                    logger.info(f"  Total:           Rs. {order_total:,.2f}")

                logger.info("-" * 80)
                logger.info(f"Sum of basket orders: Rs. {basket_orders_sum:,.2f}")
                logger.info(f"Matches initial.total: {abs(basket_orders_sum - initial_total) < 1}")
                logger.info("=" * 80)

        elif isinstance(data, list):
            # Orders response - aggregate all order margins
            for order in data:
                span_margin += order.get("span", 0)
                exposure_margin += order.get("exposure", 0)
                total_margin_required += order.get("total", 0)

            # No margin benefit for simple orders (no spread optimization)
            margin_benefit = 0

            logger.debug(
                f"Orders margin: total={total_margin_required}, span={span_margin}, exposure={exposure_margin}"
            )

        # Return standardized format matching OpenAlgo API specification
        response_data = {
            "status": "success",
            "data": {
                "total_margin_required": total_margin_required,
                "span_margin": span_margin,
                "exposure_margin": exposure_margin,
            },
        }

        return response_data

    except Exception as e:
        logger.error(f"Error parsing Zerodha margin response: {e}")
        return {"status": "error", "message": f"Failed to parse margin response: {str(e)}"}

```


---

# FILE: broker\zerodha\mapping\order_data.py

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
    if order_data["data"] is None:
        # Handle the case where there is no data
        # For example, you might want to display a message to the user
        # or pass an empty list or dictionary to the template.
        logger.info("No data available.")
        order_data = {}  # or set it to an empty list if it's supposed to be a list
    else:
        order_data = order_data["data"]

    # logger.info(f"{order_data}")

    if order_data:
        for order in order_data:
            # Extract the instrument_token and exchange for the current order
            exchange = order["exchange"]
            symbol = order["tradingsymbol"]

            # Check if a symbol was found; if so, update the trading_symbol in the current order
            if symbol:
                order["tradingsymbol"] = get_oa_symbol(brsymbol=symbol, exchange=exchange)
            else:
                logger.info(
                    f"{symbol} and exchange {exchange} not found. Keeping original trading symbol."
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
            if order["status"] == "COMPLETE":
                total_completed_orders += 1
            elif order["status"] == "OPEN":
                total_open_orders += 1
            elif order["status"] == "REJECTED":
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

        if order.get("status", "") == "COMPLETE":
            order_status = "complete"
        if order.get("status", "") == "REJECTED":
            order_status = "rejected"
        if order.get("status", "") == "TRIGGER PENDING":
            order_status = "trigger pending"
        if order.get("status", "") == "OPEN":
            order_status = "open"
        if order.get("status", "") == "CANCELLED":
            order_status = "cancelled"

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
            "order_status": order_status,
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
            "symbol": trade.get("tradingsymbol"),
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
    """
    Processes and modifies a list of OpenPosition dictionaries based on specific conditions.

    Parameters:
    - position_data: A list of dictionaries, where each dictionary represents an Open Position.

    Returns:
    - The modified order_data with updated 'tradingsymbol'
    """
    # Check if 'data' is None
    if position_data["data"]["net"] is None:
        # Handle the case where there is no data
        # For example, you might want to display a message to the user
        # or pass an empty list or dictionary to the template.
        logger.info("No data available.")
        position_data = {}  # or set it to an empty list if it's supposed to be a list
    else:
        position_data = position_data["data"]["net"]

    # logger.info(f"{order_data}")

    if position_data:
        for position in position_data:
            # Extract the instrument_token and exchange for the current order
            exchange = position["exchange"]
            symbol = position["tradingsymbol"]

            # Check if a symbol was found; if so, update the trading_symbol in the current order
            if symbol:
                position["tradingsymbol"] = get_oa_symbol(brsymbol=symbol, exchange=exchange)
            else:
                logger.info(
                    f"{symbol} and exchange {exchange} not found. Keeping original trading symbol."
                )

    return position_data


def transform_positions_data(positions_data):
    transformed_data = []

    for position in positions_data:
        # Ensure average_price is treated as a float, then format to a string with 2 decimal places
        average_price_formatted = "{:.2f}".format(float(position.get("average_price", 0.0)))

        transformed_position = {
            "symbol": position.get("tradingsymbol", ""),
            "exchange": position.get("exchange", ""),
            "product": position.get("product", ""),
            "quantity": position.get("quantity", "0"),
            "pnl": round(position.get("pnl", 0.0), 2),  # Rounded to two decimals
            "average_price": average_price_formatted,
            "ltp": round(position.get("last_price", 0.0), 2),
        }
        transformed_data.append(transformed_position)
    return transformed_data


def transform_holdings_data(holdings_data):
    transformed_data = []
    for holdings in holdings_data:
        # Handle zero average price case
        average_price = float(holdings.get("average_price") or 0.0)
        if average_price == 0:
            logger.debug(
                f"Encountering zero average price for symbol: {holdings.get('tradingsymbol', 'Unknown')}"
            )
            pnlpercent = 0.0
        else:
            pnlpercent = round(
                (holdings.get("last_price", 0) - average_price) / average_price * 100, 2
            )

        transformed_position = {
            "symbol": holdings.get("tradingsymbol", ""),
            "exchange": holdings.get("exchange", ""),
            "quantity": holdings.get("quantity", 0),
            "product": holdings.get("product", ""),
            "average_price": average_price,
            "pnl": round(holdings.get("pnl", 0.0), 2),  # Rounded to two decimals
            "pnlpercent": pnlpercent,  # Rounded to two decimals
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
        logger.info("No data available.")
        portfolio_data = {}  # or set it to an empty list if it's supposed to be a list
    else:
        portfolio_data = portfolio_data["data"]

    if portfolio_data:
        for portfolio in portfolio_data:
            if portfolio["product"] == "CNC":
                portfolio["product"] = "CNC"

            else:
                logger.info("Zerodha Portfolio - Product Value for Delivery Not Found or Changed.")

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

# FILE: broker\zerodha\mapping\transform_data.py

```py
# Mapping OpenAlgo API Request https://openalgo.in/docs
# Mapping Zerodha Broking Parameters https://kite.trade/docs/connect/v3/

from database.token_db import get_br_symbol


def transform_data(data):
    """
    Transforms the new API request structure to the current expected structure.
    """
    symbol = get_br_symbol(data["symbol"], data["exchange"])

    # Basic mapping
    transformed = {
        "tradingsymbol": symbol,
        "exchange": data["exchange"],
        "transaction_type": data["action"].upper(),
        "order_type": data["pricetype"],
        "quantity": data["quantity"],
        "product": data["product"],
        "price": data.get("price", "0"),
        "trigger_price": data.get("trigger_price", "0"),
        "disclosed_quantity": data.get("disclosed_quantity", "0"),
        "validity": "DAY",
        "market_protection": "-1",
        "tag": "openalgo",
    }

    # Extended mapping for fields that might need conditional logic or additional processing
    transformed["disclosed_quantity"] = data.get("disclosed_quantity", "0")
    transformed["trigger_price"] = data.get("trigger_price", "0")

    return transformed


def transform_modify_order_data(data):
    return {
        "order_type": map_order_type(data["pricetype"]),
        "quantity": data["quantity"],
        "price": data["price"],
        "trigger_price": data.get("trigger_price", "0"),
        "disclosed_quantity": data.get("disclosed_quantity", "0"),
        "validity": "DAY",
    }


def map_order_type(pricetype):
    """
    Maps the new pricetype to the existing order type.
    """
    order_type_mapping = {"MARKET": "MARKET", "LIMIT": "LIMIT", "SL": "SL", "SL-M": "SL-M"}
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
    return product_type_mapping.get(product, "MIS")  # Default to INTRADAY if not found


def reverse_map_product_type(exchange, product):
    """
    Reverse maps the broker product type to the OpenAlgo product type, considering the exchange.
    """
    # Exchange to OpenAlgo product type mapping for 'D'
    exchange_mapping = {
        "CNC": "CNC",
        "NRML": "NRML",
        "MIS": "MIS",
    }

    return exchange_mapping.get(product)

```
