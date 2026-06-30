# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\samco\mapping



---

# FILE: broker\samco\mapping\__init__.py

```py

```


---

# FILE: broker\samco\mapping\margin_data.py

```py
# Mapping OpenAlgo API Request https://openalgo.in/docs
# Mapping Samco Span Margin API https://docs-tradeapi.samco.in/span-margin.html

from database.token_db import get_br_symbol
from utils.logging import get_logger

logger = get_logger(__name__)


def transform_margin_position(position):
    """
    Transform a single OpenAlgo margin position to Samco span margin format.

    Samco spanMargin API expects:
    - exchange: Name of the exchange (NFO, MCX, CDS, BFO)
    - tradingSymbol: Trading symbol of the scrip
    - qty: Quantity
    - transactionType: BUY or SELL (optional, default SELL)
    - price: Price (optional, for single scrip)

    Args:
        position: Position in OpenAlgo format
            - symbol: OpenAlgo symbol
            - exchange: Exchange (NFO, MCX, CDS, BFO)
            - quantity: Quantity
            - action: BUY or SELL
            - price: Price (optional)

    Returns:
        Dict in Samco margin format or None if transformation fails
    """
    try:
        symbol = position.get("symbol")
        exchange = position.get("exchange")
        quantity = position.get("quantity")
        action = position.get("action", "SELL").upper()
        price = position.get("price", 0)
        product = position.get("product", "NRML").upper()

        if not symbol or not exchange or not quantity:
            logger.warning(f"Missing required fields in position: {position}")
            return None

        # Validate exchange - spanMargin only works for derivatives
        valid_exchanges = ["NFO", "MCX", "CDS", "BFO", "MFO"]
        if exchange not in valid_exchanges:
            logger.warning(
                f"Exchange {exchange} not valid for span margin. Valid: {valid_exchanges}"
            )
            return None

        # Get broker symbol (trading symbol)
        br_symbol = get_br_symbol(symbol, exchange)
        if not br_symbol:
            logger.warning(f"Could not get broker symbol for: {symbol} on {exchange}")
            return None

        # Map product type to Samco format
        product_map = {
            "NRML": "NRML",
            "MIS": "MIS",
            "CNC": "CNC",
            "INTRADAY": "MIS",
            "CARRYFORWARD": "NRML",
            "MARGIN": "NRML",
        }
        samco_product = product_map.get(product, "NRML")

        # Build the transformed position
        transformed = {
            "exchange": exchange,
            "tradingSymbol": br_symbol,
            "qty": str(int(quantity)),
            "productType": samco_product,
            "orderType": "L",  # Limit order - mandatory field
        }

        # Add optional fields
        if action:
            transformed["transactionType"] = action

        if price and float(price) > 0:
            transformed["price"] = str(float(price))
        else:
            # Price is required for limit orders
            transformed["price"] = "0"

        logger.debug(f"Transformed position: {transformed}")
        return transformed

    except Exception as e:
        logger.error(f"Error transforming position: {position}, Error: {e}")
        return None


def parse_margin_response(response_data):
    """
    Parse Samco span margin response to OpenAlgo standard format.

    Samco spanMargin API returns:
    - status: Success or Failure
    - statusMessage: Description
    - spanDetails:
        - totalRequirement: Total margin required
        - spanRequirement: SPAN margin
        - exposureMargin: Exposure margin
        - spreadBenefit: Spread/hedge benefit (reduction in margin)

    For single scrip, it may also return:
    - estimatedBrokerage: Projected brokerage
    - estimatedExpenses: Other expenses
    - estimatedOrderValue: Total order value
    - marginRequired: Margin needed
    - totalMargin: Total margin

    Args:
        response_data: Raw response from Samco API

    Returns:
        Standardized margin response matching OpenAlgo format
    """
    try:
        if not response_data or not isinstance(response_data, dict):
            return {"status": "error", "message": "Invalid response from broker"}

        # Check for error response
        if response_data.get("status") != "Success":
            error_message = response_data.get("statusMessage", "Failed to calculate margin")
            return {"status": "error", "message": error_message}

        # Extract span details
        span_details = response_data.get("spanDetails", {})

        if span_details:
            # Samco returns: totalMargin, marginRequired, exposureMargin, spreadBenefit
            # totalMargin = marginRequired + exposureMargin
            total_margin = safe_float(span_details.get("totalMargin", 0)) or safe_float(
                span_details.get("totalRequirement", 0)
            )
            span_margin = safe_float(span_details.get("marginRequired", 0)) or safe_float(
                span_details.get("spanRequirement", 0)
            )
            exposure_margin = safe_float(span_details.get("exposureMargin", 0))
            spread_benefit = safe_float(span_details.get("spreadBenefit", 0))
        else:
            # Single scrip response (fallback)
            total_margin = safe_float(response_data.get("totalMargin", 0)) or safe_float(
                response_data.get("marginRequired", 0)
            )
            span_margin = safe_float(response_data.get("marginRequired", 0))
            exposure_margin = safe_float(response_data.get("exposureMargin", 0))
            spread_benefit = 0

        # Return standardized format
        return {
            "status": "success",
            "data": {
                "total_margin_required": total_margin,
                "span_margin": span_margin,
                "exposure_margin": exposure_margin,
                "spread_benefit": spread_benefit,
            },
        }

    except Exception as e:
        logger.error(f"Error parsing margin response: {e}")
        return {"status": "error", "message": f"Failed to parse margin response: {str(e)}"}


def safe_float(value, default=0):
    """Convert string to float, handling commas and empty values"""
    if value is None or value == "":
        return default
    try:
        if isinstance(value, str):
            value = value.replace(",", "")
        return float(value)
    except (ValueError, TypeError):
        return default

```


---

# FILE: broker\samco\mapping\order_data.py

```py
import json

from database.token_db import get_oa_symbol, get_symbol
from utils.logging import get_logger

logger = get_logger(__name__)


def map_order_status(status):
    """
    Maps Samco order status to OpenAlgo standardized status.
    OpenAlgo expects: 'open', 'complete', 'cancelled', 'rejected'
    """
    status_lower = status.lower() if status else ""
    status_mapping = {
        "open": "open",
        "pending": "open",
        "ordered": "open",
        "trigger pending": "open",
        "after market order req received": "open",
        "complete": "complete",
        "completed": "complete",
        "executed": "complete",
        "filled": "complete",
        "cancelled": "cancelled",
        "canceled": "cancelled",
        "rejected": "rejected",
    }
    mapped = status_mapping.get(status_lower, status_lower)
    if mapped == status_lower and status_lower not in status_mapping:
        logger.warning(f"Unknown Samco order status: '{status}' — defaulting to '{status_lower}'")
    return mapped


def map_order_data(order_data):
    """
    Processes and modifies a list of order dictionaries based on specific conditions.

    Parameters:
    - order_data: A dictionary containing Samco order book response.

    Returns:
    - The modified order_data with updated 'tradingSymbol' and 'productCode' fields.
    """
    # Check if order_data is empty or doesn't have 'orderBookDetails' key
    if (
        not order_data
        or "orderBookDetails" not in order_data
        or order_data["orderBookDetails"] is None
    ):
        logger.info("No data available.")
        return []

    order_data = order_data["orderBookDetails"]
    logger.info(f"{order_data}")

    if order_data:
        for order in order_data:
            # Extract the symbol and exchange for the current order
            symbol = order.get("symbol", "")
            trading_symbol = order.get("tradingSymbol", "")
            exchange = order.get("exchange", "")

            # Use the get_oa_symbol function to fetch the OpenAlgo symbol from the database
            symbol_from_db = get_oa_symbol(trading_symbol, exchange)

            # Check if a symbol was found; if so, update the trading_symbol in the current order
            if symbol_from_db:
                order["tradingSymbol"] = symbol_from_db
                # Map product codes to OpenAlgo format
                product_code = order.get("productCode", "")
                if (
                    order["exchange"] == "NSE" or order["exchange"] == "BSE"
                ) and product_code == "CNC":
                    order["productCode"] = "CNC"
                elif product_code == "MIS":
                    order["productCode"] = "MIS"
                elif order["exchange"] in ["NFO", "MCX", "BFO", "CDS"] and product_code == "NRML":
                    order["productCode"] = "NRML"
            else:
                logger.info(
                    f"Symbol not found for {trading_symbol} and exchange {exchange}. Keeping original trading symbol."
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
    total_buy_orders = total_sell_orders = 0
    total_completed_orders = total_open_orders = total_rejected_orders = 0

    if order_data:
        for order in order_data:
            # Count buy and sell orders
            if order.get("transactionType") == "BUY":
                total_buy_orders += 1
            elif order.get("transactionType") == "SELL":
                total_sell_orders += 1

            # Count orders based on their status (Samco uses different status values)
            status = order.get("orderStatus", "").lower()
            if status in ["complete", "executed"]:
                total_completed_orders += 1
            elif status in ["open", "pending", "trigger pending"]:
                total_open_orders += 1
            elif status == "rejected":
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
    Transforms Samco order data to OpenAlgo standardized format.
    """
    if isinstance(orders, dict):
        orders = [orders]

    transformed_orders = []

    for order in orders:
        if not isinstance(order, dict):
            logger.warning(
                f"Warning: Expected a dict, but found a {type(order)}. Skipping this item."
            )
            continue

        # Map Samco order type to OpenAlgo format
        # Samco converts MKT orders to L with marketProtection, so check for that
        ordertype = order.get("orderType", "")
        market_protection = order.get("marketProtection")

        if ordertype == "L" and market_protection:
            # Market order converted to Limit with market protection
            ordertype = "MARKET"
        elif ordertype == "L":
            ordertype = "LIMIT"
        elif ordertype == "MKT":
            ordertype = "MARKET"
        elif ordertype == "SL":
            ordertype = "SL"
        elif ordertype == "SL-M":
            ordertype = "SL-M"

        transformed_order = {
            "symbol": order.get("tradingSymbol", ""),
            "exchange": order.get("exchange", ""),
            "action": order.get("transactionType", ""),
            "quantity": order.get("totalQuanity", 0),
            "price": order.get("orderPrice", 0.0),
            "trigger_price": order.get("triggerPrice", 0.0),
            "pricetype": ordertype,
            "product": order.get("productCode", ""),
            "orderid": order.get("orderNumber", ""),
            "order_status": map_order_status(order.get("orderStatus", "")),
            "timestamp": order.get("orderTime", ""),
        }

        transformed_orders.append(transformed_order)

    return transformed_orders


def map_trade_data(trade_data):
    """
    Processes and modifies a list of trade dictionaries based on specific conditions.

    Parameters:
    - trade_data: A dictionary containing Samco trade book response.

    Returns:
    - The modified trade_data with updated 'tradingSymbol' and 'productCode' fields.
    """
    # Check if 'tradeBookDetails' is None or missing
    if (
        not trade_data
        or "tradeBookDetails" not in trade_data
        or trade_data["tradeBookDetails"] is None
    ):
        logger.info("No trade data available.")
        return []

    trade_data = trade_data["tradeBookDetails"]

    if trade_data:
        for trade in trade_data:
            symbol = trade.get("tradingSymbol", "")
            exchange = trade.get("exchange", "")

            symbol_from_db = get_oa_symbol(symbol, exchange)

            if symbol_from_db:
                trade["tradingSymbol"] = symbol_from_db
                product_code = trade.get("productCode", "")
                if (
                    trade["exchange"] == "NSE" or trade["exchange"] == "BSE"
                ) and product_code == "CNC":
                    trade["productCode"] = "CNC"
                elif product_code == "MIS":
                    trade["productCode"] = "MIS"
                elif trade["exchange"] in ["NFO", "MCX", "BFO", "CDS"] and product_code == "NRML":
                    trade["productCode"] = "NRML"
            else:
                logger.info(
                    f"Unable to find the symbol {symbol} and exchange {exchange}. Keeping original trading symbol."
                )

    return trade_data


def transform_tradebook_data(tradebook_data):
    """
    Transforms Samco tradebook data to OpenAlgo standardized format.
    """
    transformed_data = []
    for trade in tradebook_data:
        transformed_trade = {
            "symbol": trade.get("tradingSymbol", ""),
            "exchange": trade.get("exchange", ""),
            "product": trade.get("productCode", ""),
            "action": trade.get("transactionType", ""),
            "quantity": trade.get("filledQuantity", 0),
            "average_price": trade.get("tradePrice", 0.0),
            "trade_value": trade.get("orderValue", 0),
            "orderid": trade.get("orderNumber", ""),
            "timestamp": trade.get("tradeTime", ""),
        }
        transformed_data.append(transformed_trade)
    return transformed_data


def map_position_data(position_data):
    """
    Processes and modifies position data from Samco.
    """
    if (
        not position_data
        or "positionDetails" not in position_data
        or position_data["positionDetails"] is None
    ):
        logger.info("No position data available.")
        return []

    positions = position_data["positionDetails"]

    if positions:
        for position in positions:
            symbol = position.get("tradingSymbol", "")
            exchange = position.get("exchange", "")

            symbol_from_db = get_oa_symbol(symbol, exchange)

            if symbol_from_db:
                position["tradingSymbol"] = symbol_from_db
                product_code = position.get("productCode", "")
                if (
                    position["exchange"] == "NSE" or position["exchange"] == "BSE"
                ) and product_code == "CNC":
                    position["productCode"] = "CNC"
                elif product_code == "MIS":
                    position["productCode"] = "MIS"
                elif (
                    position["exchange"] in ["NFO", "MCX", "BFO", "CDS"] and product_code == "NRML"
                ):
                    position["productCode"] = "NRML"
            else:
                logger.info(
                    f"Symbol not found for {symbol} and exchange {exchange}. Keeping original trading symbol."
                )

    return positions


def transform_positions_data(positions_data):
    """
    Transforms Samco positions data to OpenAlgo standardized format.
    Samco returns netQuantity as positive and uses transactionType to indicate direction.
    """
    transformed_data = []
    for position in positions_data:
        # Handle lastTradedPrice which may have comma formatting like "1,550.00"
        ltp = position.get("lastTradedPrice", "0")
        if isinstance(ltp, str):
            ltp = ltp.replace(",", "")

        # Use averageBuyPrice or averageSellPrice based on transaction type
        transaction_type = position.get("transactionType", "")
        if transaction_type == "SELL":
            avg_price = position.get("averageSellPrice", "0")
        else:
            avg_price = position.get("averageBuyPrice", "0")
        if isinstance(avg_price, str):
            avg_price = avg_price.replace(",", "")

        # Format average_price to 2 decimal places like Zerodha
        average_price_formatted = f"{float(avg_price) if avg_price else 0.0:.2f}"

        # Calculate total P&L (realized + unrealized) and round to 2 decimals
        realized_pnl = float(position.get("realizedGainAndLoss", 0) or 0)
        unrealized_pnl = float(position.get("unrealizedGainAndLoss", 0) or 0)
        total_pnl = round(realized_pnl + unrealized_pnl, 2)

        # Make quantity negative for SELL (short) positions
        qty = int(position.get("netQuantity", 0))
        if transaction_type == "SELL" and qty > 0:
            qty = -qty

        transformed_position = {
            "symbol": position.get("tradingSymbol", ""),
            "exchange": position.get("exchange", ""),
            "product": position.get("productCode", ""),
            "quantity": str(qty),
            "average_price": average_price_formatted,
            "ltp": round(float(ltp) if ltp else 0.0, 2),
            "pnl": total_pnl,
        }
        transformed_data.append(transformed_position)
    return transformed_data


def map_portfolio_data(portfolio_data):
    """
    Processes and modifies portfolio/holdings data from Samco.
    """
    if not portfolio_data or portfolio_data.get("status") != "Success":
        logger.info("No portfolio data available.")
        return {}

    holdings = portfolio_data.get("holdingDetails", [])

    if holdings:
        for holding in holdings:
            symbol = holding.get("tradingSymbol", "")
            exchange = holding.get("exchange", "NSE")

            symbol_from_db = get_oa_symbol(symbol, exchange)

            if symbol_from_db:
                holding["tradingSymbol"] = symbol_from_db

            # Samco holdings are typically CNC
            holding["product"] = "CNC"

    return {"holdings": holdings, "totalholding": portfolio_data.get("holdingSummary", None)}


def transform_holdings_data(holdings_data):
    """
    Transforms Samco holdings data to OpenAlgo standardized format.
    """
    transformed_data = []
    holdings = holdings_data.get("holdings", [])

    for holding in holdings:
        # Get quantity and pnl
        quantity = int(holding.get("holdingsQuantity", 0) or 0)
        pnl = float(holding.get("totalGainAndLoss", 0) or 0)

        # Calculate pnl percentage from holdingsValue and pnl
        holdings_value = float(holding.get("holdingsValue", 0) or 0)
        if holdings_value > 0:
            pnl_percent = (
                round((pnl / (holdings_value - pnl)) * 100, 2)
                if (holdings_value - pnl) != 0
                else 0.0
            )
        else:
            pnl_percent = 0.0

        transformed_holding = {
            "symbol": holding.get("tradingSymbol", ""),
            "exchange": holding.get("exchange", "NSE"),
            "quantity": quantity,
            "product": holding.get("product", "CNC"),
            "pnl": round(pnl, 2),
            "pnlpercent": pnl_percent,
        }
        transformed_data.append(transformed_holding)
    return transformed_data


def calculate_portfolio_statistics(holdings_data):
    """
    Calculates portfolio statistics from Samco holdings data.
    """
    totalholding = holdings_data.get("totalholding")

    if totalholding is None:
        return {
            "totalholdingvalue": 0,
            "totalinvvalue": 0,
            "totalprofitandloss": 0,
            "totalpnlpercentage": 0,
        }

    # Samco holdingSummary fields
    portfolio_value = float(totalholding.get("portfolioValue", 0) or 0)
    total_pnl = float(totalholding.get("totalGainAndLossAmount", 0) or 0)

    # Calculate investment value (portfolio value - pnl)
    total_inv_value = portfolio_value - total_pnl

    # Calculate pnl percentage
    pnl_percentage = round((total_pnl / total_inv_value) * 100, 2) if total_inv_value != 0 else 0

    return {
        "totalholdingvalue": round(portfolio_value, 2),
        "totalinvvalue": round(total_inv_value, 2),
        "totalprofitandloss": round(total_pnl, 2),
        "totalpnlpercentage": pnl_percentage,
    }

```


---

# FILE: broker\samco\mapping\transform_data.py

```py
# Mapping OpenAlgo API Request https://openalgo.in/docs
# Mapping Samco Parameters https://www.samco.in/stocknote-api-documentation

from database.token_db import get_br_symbol, get_symbol_info
from utils.logging import get_logger
from utils.mpp_slab import (
    calculate_protected_price,
    get_instrument_type_from_symbol,
    get_mpp_percentage,
)

logger = get_logger(__name__)


def transform_data(data, token, auth_token=None):
    """
    Transforms the OpenAlgo API request structure to Samco expected structure.

    For MARKET orders, fetches LTP and converts to LIMIT with MPP (Market Price Protection).
    For SL-M orders, converts to SL with protected limit price based on trigger price.
    Samco no longer accepts MKT or SL-M order types.

    Args:
        data: Order data dictionary
        token: Instrument token
        auth_token: Authentication token for fetching quotes
    """
    symbol = get_br_symbol(data["symbol"], data["exchange"])

    # Default values
    price = str(data.get("price", "0"))
    order_type = map_order_type(data["pricetype"])
    action = data["action"].upper()
    mpp_percentage = None

    # Apply Market Price Protection for MARKET orders (Samco only accepts L/SL)
    if data["pricetype"] == "MARKET":
        logger.info(
            f"MPP: MARKET order detected for Symbol={data['symbol']}, "
            f"Exchange={data['exchange']}, Action={action}"
        )
        try:
            if auth_token:
                from broker.samco.api.data import BrokerData

                broker_data = BrokerData(auth_token)
                quote_data = broker_data.get_quotes(data["symbol"], data["exchange"])
                logger.info(
                    f"MPP Quote Response: Symbol={data['symbol']}, "
                    f"LTP={quote_data.get('ltp') if quote_data else None}"
                )

                if quote_data:
                    instrument_type = get_instrument_type_from_symbol(data["symbol"])
                    tick_size = None
                    symbol_info = get_symbol_info(data["symbol"], data["exchange"])
                    if symbol_info and symbol_info.tick_size:
                        tick_size = symbol_info.tick_size

                    ltp = float(quote_data.get("ltp", 0))

                    if ltp > 0:
                        mpp_percentage = get_mpp_percentage(ltp, instrument_type)
                        protected_price = calculate_protected_price(
                            price=ltp,
                            action=action,
                            symbol=data["symbol"],
                            instrument_type=instrument_type,
                            tick_size=tick_size,
                        )
                        price = str(protected_price)
                        order_type = "L"
                        logger.info(
                            f"MPP Conversion: Symbol={data['symbol']}, MKT->L, "
                            f"LTP={ltp}, ProtectedPrice={protected_price}, MPP={mpp_percentage}%"
                        )
                    else:
                        raise ValueError(
                            f"LTP is 0 for Symbol={data['symbol']}. Cannot determine market price."
                        )
                else:
                    raise ValueError(
                        f"No quote data for Symbol={data['symbol']}. Cannot determine market price."
                    )
            else:
                raise ValueError(
                    f"No auth token for Symbol={data['symbol']}. Cannot fetch quotes for MPP."
                )
        except Exception as e:
            logger.error(f"MPP Error: {str(e)}")
            raise ValueError(f"MARKET order failed: {str(e)}")

    # Apply Market Price Protection for SL-M orders (convert to SL with protected price)
    elif data["pricetype"] == "SL-M":
        try:
            trigger_price = float(data.get("trigger_price", 0))
        except (TypeError, ValueError):
            trigger_price = 0.0
        logger.info(
            f"MPP: SL-M order detected for Symbol={data['symbol']}, "
            f"Action={action}, TriggerPrice={trigger_price}"
        )
        if trigger_price > 0:
            try:
                instrument_type = get_instrument_type_from_symbol(data["symbol"])
                tick_size = None
                symbol_info = get_symbol_info(data["symbol"], data["exchange"])
                if symbol_info and symbol_info.tick_size:
                    tick_size = symbol_info.tick_size

                mpp_percentage = get_mpp_percentage(trigger_price, instrument_type)
                protected_price = calculate_protected_price(
                    price=trigger_price,
                    action=action,
                    symbol=data["symbol"],
                    instrument_type=instrument_type,
                    tick_size=tick_size,
                )
                price = str(protected_price)
                order_type = "SL"
                logger.info(
                    f"MPP Conversion: Symbol={data['symbol']}, SL-M->SL, "
                    f"TriggerPrice={trigger_price}, LimitPrice={protected_price}, MPP={mpp_percentage}%"
                )
            except Exception as e:
                logger.error(
                    f"MPP Error: Failed for SL-M Symbol={data['symbol']}, Error={str(e)}. "
                    f"Falling back to SL order type"
                )
                order_type = "SL"
        else:
            logger.warning(
                f"MPP Warning: Trigger price is 0 for SL-M Symbol={data['symbol']}. "
                f"Falling back to SL order type"
            )
            order_type = "SL"

    # Basic mapping for Samco placeOrder API
    transformed = {
        "symbolName": symbol,
        "exchange": data["exchange"],
        "transactionType": action,
        "orderType": order_type,
        "quantity": str(data["quantity"]),
        "disclosedQuantity": str(data.get("disclosed_quantity", "0")),
        "orderValidity": "DAY",
        "productType": map_product_type(data["product"]),
        "afterMarketOrderFlag": "NO",
    }

    # Add price for LIMIT and SL orders (and MPP-converted orders)
    if order_type in ["L", "SL"]:
        if price == "0" and data["pricetype"] in ["LIMIT", "SL"]:
            price = str(data.get("price", "0"))
        transformed["price"] = price

    # Add trigger price for SL orders
    if order_type == "SL" or data["pricetype"] in ["SL", "SL-M"]:
        transformed["triggerPrice"] = str(data.get("trigger_price", "0"))

    # Add marketProtection for MPP-converted orders (dynamic slab percentage)
    if data["pricetype"] in ["MARKET", "SL-M"] and mpp_percentage is not None:
        transformed["marketProtection"] = str(int(mpp_percentage))

    return transformed


def transform_modify_order_data(data):
    """
    Transforms the OpenAlgo modify order request to Samco expected structure.
    Only includes fields that can be modified (orderNumber goes in URL).
    """
    transformed = {
        "orderType": map_order_type(data["pricetype"]),
        "quantity": str(data["quantity"]),
        "orderValidity": "DAY",
    }

    # Only add disclosedQuantity if provided and > 0 (must be min 10% of quantity)
    disclosed_qty = data.get("disclosed_quantity")
    if disclosed_qty and int(disclosed_qty) > 0:
        transformed["disclosedQuantity"] = str(disclosed_qty)

    # Add price for LIMIT and SL orders
    if data["pricetype"] in ["LIMIT", "SL"]:
        transformed["price"] = str(data.get("price", "0"))

    # Add trigger price for SL and SL-M orders
    if data["pricetype"] in ["SL", "SL-M"]:
        transformed["triggerPrice"] = str(data.get("trigger_price", "0"))

    return transformed


def map_order_type(pricetype):
    """
    Maps OpenAlgo pricetype to Samco order type.
    """
    order_type_mapping = {"MARKET": "MKT", "LIMIT": "L", "SL": "SL", "SL-M": "SL-M"}
    return order_type_mapping.get(pricetype, "MKT")


def map_product_type(product):
    """
    Maps OpenAlgo product type to Samco product type.
    """
    product_type_mapping = {
        "CNC": "CNC",
        "NRML": "NRML",
        "MIS": "MIS",
    }
    return product_type_mapping.get(product, "MIS")


def reverse_map_product_type(product):
    """
    Maps Samco product type back to OpenAlgo product type.
    """
    reverse_product_type_mapping = {
        "CNC": "CNC",
        "NRML": "NRML",
        "MIS": "MIS",
    }
    return reverse_product_type_mapping.get(product, "MIS")

```
