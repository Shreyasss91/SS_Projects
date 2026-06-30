# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\restx_api



---

# FILE: restx_api\__init__.py

```py
from flask import Blueprint
from flask_restx import Api

api_v1_bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")
api = Api(
    api_v1_bp,
    version="1.0",
    title="OpenAlgo API",
    description="API for OpenAlgo Trading Platform",
    doc=False,
)

# Import namespaces
from .analyzer import api as analyzer_ns
from .basket_order import api as basket_order_ns
from .cancel_all_order import api as cancel_all_order_ns
from .cancel_gtt_order import api as cancel_gtt_order_ns
from .cancel_order import api as cancel_order_ns
from .chart_api import api as chart_ns
from .close_position import api as close_position_ns
from .depth import api as depth_ns
from .expiry import api as expiry_ns
from .funds import api as funds_ns
from .gtt_orderbook import api as gtt_orderbook_ns
from .history import api as history_ns
from .holdings import api as holdings_ns
from .instruments import api as instruments_ns
from .intervals import api as intervals_ns
from .margin import api as margin_ns
from .market_holidays import api as market_holidays_ns
from .market_timings import api as market_timings_ns
from .modify_gtt_order import api as modify_gtt_order_ns
from .modify_order import api as modify_order_ns
from .multi_option_greeks import api as multi_option_greeks_ns
from .multiquotes import api as multiquotes_ns
from .openposition import api as openposition_ns
from .option_chain import api as option_chain_ns
from .option_greeks import api as option_greeks_ns
from .option_symbol import api as option_symbol_ns
from .options_multiorder import api as options_multiorder_ns
from .options_order import api as options_order_ns
from .orderbook import api as orderbook_ns
from .orderstatus import api as orderstatus_ns
from .ping import api as ping_ns
from .place_gtt_order import api as place_gtt_order_ns
from .place_order import api as place_order_ns
from .place_smart_order import api as place_smart_order_ns
from .pnl_symbols import api as pnl_symbols_ns
from .positionbook import api as positionbook_ns
from .quotes import api as quotes_ns
from .search import api as search_ns
from .split_order import api as split_order_ns
from .symbol import api as symbol_ns
from .synthetic_future import api as synthetic_future_ns
from .telegram_bot import api as telegram_ns
from .ticker import api as ticker_ns
from .tradebook import api as tradebook_ns
from .whatsapp_bot import api as whatsapp_ns

# Add namespaces
api.add_namespace(place_order_ns, path="/placeorder")
api.add_namespace(place_smart_order_ns, path="/placesmartorder")
api.add_namespace(modify_order_ns, path="/modifyorder")
api.add_namespace(cancel_order_ns, path="/cancelorder")
api.add_namespace(close_position_ns, path="/closeposition")
api.add_namespace(cancel_all_order_ns, path="/cancelallorder")
api.add_namespace(quotes_ns, path="/quotes")
api.add_namespace(multiquotes_ns, path="/multiquotes")
api.add_namespace(history_ns, path="/history")
api.add_namespace(depth_ns, path="/depth")
api.add_namespace(option_chain_ns, path="/optionchain")
api.add_namespace(intervals_ns, path="/intervals")
api.add_namespace(funds_ns, path="/funds")
api.add_namespace(orderbook_ns, path="/orderbook")
api.add_namespace(tradebook_ns, path="/tradebook")
api.add_namespace(positionbook_ns, path="/positionbook")
api.add_namespace(holdings_ns, path="/holdings")
api.add_namespace(basket_order_ns, path="/basketorder")
api.add_namespace(split_order_ns, path="/splitorder")
api.add_namespace(orderstatus_ns, path="/orderstatus")
api.add_namespace(openposition_ns, path="/openposition")
api.add_namespace(ticker_ns, path="/ticker")
api.add_namespace(symbol_ns, path="/symbol")
api.add_namespace(search_ns, path="/search")
api.add_namespace(expiry_ns, path="/expiry")
api.add_namespace(option_symbol_ns, path="/optionsymbol")
api.add_namespace(options_order_ns, path="/optionsorder")
api.add_namespace(options_multiorder_ns, path="/optionsmultiorder")
api.add_namespace(option_greeks_ns, path="/optiongreeks")
api.add_namespace(multi_option_greeks_ns, path="/multioptiongreeks")
api.add_namespace(synthetic_future_ns, path="/syntheticfuture")
api.add_namespace(analyzer_ns, path="/analyzer")
api.add_namespace(ping_ns, path="/ping")
api.add_namespace(telegram_ns, path="/telegram")
api.add_namespace(whatsapp_ns, path="/whatsapp")
api.add_namespace(margin_ns, path="/margin")
api.add_namespace(instruments_ns, path="/instruments")
api.add_namespace(chart_ns, path="/chart")
api.add_namespace(market_holidays_ns, path="/market/holidays")
api.add_namespace(market_timings_ns, path="/market/timings")
api.add_namespace(pnl_symbols_ns, path="/pnl")
api.add_namespace(place_gtt_order_ns, path="/placegttorder")
api.add_namespace(modify_gtt_order_ns, path="/modifygttorder")
api.add_namespace(cancel_gtt_order_ns, path="/cancelgttorder")
api.add_namespace(gtt_orderbook_ns, path="/gttorderbook")

```


---

# FILE: restx_api\account_schema.py

```py
from marshmallow import INCLUDE, Schema, fields, validate


class FundsSchema(Schema):
    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))


class OrderbookSchema(Schema):
    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))


class TradebookSchema(Schema):
    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))


class PositionbookSchema(Schema):
    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))


class HoldingsSchema(Schema):
    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))


class OrderStatusSchema(Schema):
    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))
    strategy = fields.Str(required=True)
    orderid = fields.Str(required=True)


class OpenPositionSchema(Schema):
    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))
    strategy = fields.Str(required=True)
    symbol = fields.Str(required=True)
    exchange = fields.Str(required=True)
    product = fields.Str(required=True, validate=validate.OneOf(["MIS", "NRML", "CNC"]))


class AnalyzerSchema(Schema):
    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))


class AnalyzerToggleSchema(Schema):
    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))
    mode = fields.Bool(required=True)


class PingSchema(Schema):
    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))


class ChartSchema(Schema):
    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))

    class Meta:
        # Allow unknown fields - chart preferences can have any key-value pairs
        unknown = INCLUDE


class PnlSymbolsSchema(Schema):
    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))

```


---

# FILE: restx_api\analyzer.py

```py
import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from database.apilog_db import async_log_order
from database.apilog_db import executor as log_executor
from limiter import limiter
from restx_api.account_schema import AnalyzerSchema, AnalyzerToggleSchema
from services.analyzer_service import get_analyzer_status, toggle_analyzer_mode
from utils.logging import get_logger

API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "10 per second")
api = Namespace("analyzer", description="Analyzer Mode API")

# Initialize logger
logger = get_logger(__name__)

# Initialize schemas
analyzer_schema = AnalyzerSchema()
analyzer_toggle_schema = AnalyzerToggleSchema()


@api.route("/", strict_slashes=False)
class AnalyzerStatus(Resource):
    @limiter.limit(API_RATE_LIMIT)
    def post(self):
        """Get analyzer mode status and statistics"""
        try:
            data = request.json

            # Validate and deserialize input using AnalyzerSchema
            try:
                analyzer_data = analyzer_schema.load(data)
            except ValidationError as err:
                error_message = str(err.messages)
                error_response = {"status": "error", "message": error_message}
                log_executor.submit(async_log_order, "analyzer_status", data, error_response)
                return make_response(jsonify(error_response), 400)

            # Extract API key
            api_key = analyzer_data.pop("apikey", None)

            # Call the service function to get analyzer status
            success, response_data, status_code = get_analyzer_status(
                analyzer_data=analyzer_data, api_key=api_key
            )

            return make_response(jsonify(response_data), status_code)

        except Exception:
            logger.exception("An unexpected error occurred in Analyzer status endpoint.")
            error_message = "An unexpected error occurred"
            error_response = {"status": "error", "message": error_message}
            log_executor.submit(async_log_order, "analyzer_status", data, error_response)
            return make_response(jsonify(error_response), 500)


@api.route("/toggle", strict_slashes=False)
class AnalyzerToggle(Resource):
    @limiter.limit(API_RATE_LIMIT)
    def post(self):
        """Toggle analyzer mode on/off"""
        try:
            data = request.json

            # Validate and deserialize input using AnalyzerToggleSchema
            try:
                analyzer_data = analyzer_toggle_schema.load(data)
            except ValidationError as err:
                error_message = str(err.messages)
                error_response = {"status": "error", "message": error_message}
                log_executor.submit(async_log_order, "analyzer_toggle", data, error_response)
                return make_response(jsonify(error_response), 400)

            # Extract API key
            api_key = analyzer_data.pop("apikey", None)

            # Call the service function to toggle analyzer mode
            success, response_data, status_code = toggle_analyzer_mode(
                analyzer_data=analyzer_data, api_key=api_key
            )

            return make_response(jsonify(response_data), status_code)

        except Exception:
            logger.exception("An unexpected error occurred in Analyzer toggle endpoint.")
            error_message = "An unexpected error occurred"
            error_response = {"status": "error", "message": error_message}
            log_executor.submit(async_log_order, "analyzer_toggle", data, error_response)
            return make_response(jsonify(error_response), 500)

```


---

# FILE: restx_api\basket_order.py

```py
import copy
import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from database.settings_db import get_analyze_mode
from events import OrderFailedEvent
from utils.event_bus import bus
from limiter import limiter
from restx_api.schemas import BasketOrderSchema
from services.basket_order_service import emit_analyzer_error, place_basket_order
from utils.logging import get_logger

API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "10 per second")
api = Namespace("basket_order", description="Basket Order API")

# Initialize logger
logger = get_logger(__name__)

# Initialize schema
basket_schema = BasketOrderSchema()


@api.route("/", strict_slashes=False)
class BasketOrder(Resource):
    @limiter.limit(API_RATE_LIMIT)
    def post(self):
        """Place multiple orders in a basket"""
        try:
            data = request.json

            # Validate and deserialize input
            try:
                basket_data = basket_schema.load(data)
            except ValidationError as err:
                error_message = str(err.messages)
                if get_analyze_mode():
                    return make_response(jsonify(emit_analyzer_error(data, error_message)), 400)
                error_response = {"status": "error", "message": error_message}
                bus.publish(OrderFailedEvent(
                    mode="live",
                    api_type="basketorder",
                    request_data=data,
                    response_data=error_response,
                    error_message=error_message,
                ))
                return make_response(jsonify(error_response), 400)

            # Extract API key
            api_key = basket_data.pop("apikey", None)

            # Call the service function to place the basket order
            success, response_data, status_code = place_basket_order(
                basket_data=basket_data, api_key=api_key
            )

            return make_response(jsonify(response_data), status_code)

        except Exception:
            logger.exception("An unexpected error occurred in BasketOrder endpoint.")
            error_message = "An unexpected error occurred"
            if get_analyze_mode():
                return make_response(jsonify(emit_analyzer_error(data, error_message)), 500)
            error_response = {"status": "error", "message": error_message}
            bus.publish(OrderFailedEvent(
                mode="live",
                api_type="basketorder",
                request_data=data,
                response_data=error_response,
                error_message=error_message,
            ))
            return make_response(jsonify(error_response), 500)

```


---

# FILE: restx_api\cancel_all_order.py

```py
import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from database.settings_db import get_analyze_mode
from events import OrderFailedEvent
from utils.event_bus import bus
from limiter import limiter
from restx_api.schemas import CancelAllOrderSchema
from services.cancel_all_order_service import cancel_all_orders, emit_analyzer_error
from utils.logging import get_logger

API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "10 per second")
api = Namespace("cancel_all_order", description="Cancel All Orders API")

# Initialize logger
logger = get_logger(__name__)

# Initialize schema
cancel_all_order_schema = CancelAllOrderSchema()


@api.route("/", strict_slashes=False)
class CancelAllOrder(Resource):
    @limiter.limit(API_RATE_LIMIT)
    def post(self):
        """Cancel all open orders"""
        try:
            data = request.json

            # Validate and deserialize input
            try:
                order_data = cancel_all_order_schema.load(data)
            except ValidationError as err:
                error_message = str(err.messages)
                if get_analyze_mode():
                    return make_response(jsonify(emit_analyzer_error(data, error_message)), 400)
                error_response = {"status": "error", "message": error_message}
                bus.publish(OrderFailedEvent(
                    mode="live",
                    api_type="cancelallorder",
                    request_data=data,
                    response_data=error_response,
                    error_message=error_message,
                ))
                return make_response(jsonify(error_response), 400)

            # Extract API key
            api_key = order_data.pop("apikey", None)

            # Call the service function to cancel all orders
            success, response_data, status_code = cancel_all_orders(
                order_data=order_data, api_key=api_key
            )

            return make_response(jsonify(response_data), status_code)

        except KeyError as e:
            missing_field = str(e)
            logger.exception(f"KeyError: Missing field {missing_field}")
            error_message = f"A required field is missing: {missing_field}"
            if get_analyze_mode():
                return make_response(jsonify(emit_analyzer_error(data, error_message)), 400)
            error_response = {"status": "error", "message": error_message}
            bus.publish(OrderFailedEvent(
                mode="live",
                api_type="cancelallorder",
                request_data=data,
                response_data=error_response,
                error_message=error_message,
            ))
            return make_response(jsonify(error_response), 400)

        except Exception:
            logger.exception("An unexpected error occurred in CancelAllOrder endpoint.")
            error_message = "An unexpected error occurred"
            if get_analyze_mode():
                return make_response(jsonify(emit_analyzer_error(data, error_message)), 500)
            error_response = {"status": "error", "message": error_message}
            bus.publish(OrderFailedEvent(
                mode="live",
                api_type="cancelallorder",
                request_data=data,
                response_data=error_response,
                error_message=error_message,
            ))
            return make_response(jsonify(error_response), 500)

```


---

# FILE: restx_api\cancel_gtt_order.py

```py
import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from database.settings_db import get_analyze_mode
from events import GTTCancelFailedEvent
from limiter import limiter
from restx_api.schemas import CancelGTTOrderSchema
from services.cancel_gtt_order_service import cancel_gtt_order, emit_analyzer_error
from utils.event_bus import bus
from utils.logging import get_logger

ORDER_RATE_LIMIT = os.getenv("ORDER_RATE_LIMIT", "10 per second")
api = Namespace("cancel_gtt_order", description="Cancel GTT Order API")

logger = get_logger(__name__)
cancel_gtt_schema = CancelGTTOrderSchema()


@api.route("/", strict_slashes=False)
class CancelGTTOrder(Resource):
    @limiter.limit(ORDER_RATE_LIMIT)
    def post(self):
        """Cancel an active GTT trigger."""
        try:
            data = request.json or {}

            try:
                order_data = cancel_gtt_schema.load(data)
            except ValidationError as err:
                error_message = str(err.messages)
                if get_analyze_mode():
                    return make_response(jsonify(emit_analyzer_error(data, error_message)), 400)
                error_response = {"status": "error", "message": error_message}
                safe_request = {k: v for k, v in data.items() if k != "apikey"}
                bus.publish(GTTCancelFailedEvent(
                    mode="live",
                    api_type="cancelgttorder",
                    trigger_id=data.get("trigger_id", ""),
                    request_data=safe_request,
                    response_data=error_response,
                    error_message=error_message,
                ))
                return make_response(jsonify(error_response), 400)

            api_key = order_data.pop("apikey", None)
            trigger_id = order_data.get("trigger_id")
            strategy = order_data.get("strategy")

            success, response_data, status_code = cancel_gtt_order(
                trigger_id=trigger_id, api_key=api_key, strategy=strategy
            )

            return make_response(jsonify(response_data), status_code)

        except Exception:
            logger.exception("An unexpected error occurred in CancelGTTOrder endpoint.")
            return make_response(
                jsonify({"status": "error", "message": "An unexpected error occurred"}), 500
            )

```


---

# FILE: restx_api\cancel_order.py

```py
import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from database.settings_db import get_analyze_mode
from events import OrderFailedEvent
from utils.event_bus import bus
from limiter import limiter
from restx_api.schemas import CancelOrderSchema
from services.cancel_order_service import cancel_order, emit_analyzer_error
from utils.logging import get_logger

ORDER_RATE_LIMIT = os.getenv("ORDER_RATE_LIMIT", "10 per second")
api = Namespace("cancel_order", description="Cancel Order API")

# Initialize logger
logger = get_logger(__name__)

# Initialize schema
cancel_order_schema = CancelOrderSchema()


@api.route("/", strict_slashes=False)
class CancelOrder(Resource):
    @limiter.limit(ORDER_RATE_LIMIT)
    def post(self):
        """Cancel an existing order"""
        try:
            data = request.json

            # Validate and deserialize input
            try:
                order_data = cancel_order_schema.load(data)
            except ValidationError as err:
                error_message = str(err.messages)
                if get_analyze_mode():
                    return make_response(jsonify(emit_analyzer_error(data, error_message)), 400)
                error_response = {"status": "error", "message": error_message}
                bus.publish(OrderFailedEvent(
                    mode="live",
                    api_type="cancelorder",
                    request_data=data,
                    response_data=error_response,
                    error_message=error_message,
                ))
                return make_response(jsonify(error_response), 400)

            # Extract API key and order ID
            api_key = order_data.pop("apikey", None)
            orderid = order_data.get("orderid")

            # Call the service function to cancel the order
            success, response_data, status_code = cancel_order(orderid=orderid, api_key=api_key)

            return make_response(jsonify(response_data), status_code)

        except KeyError as e:
            missing_field = str(e)
            logger.exception(f"KeyError: Missing field {missing_field}")
            error_message = f"A required field is missing: {missing_field}"
            if get_analyze_mode():
                return make_response(jsonify(emit_analyzer_error(data, error_message)), 400)
            error_response = {"status": "error", "message": error_message}
            bus.publish(OrderFailedEvent(
                mode="live",
                api_type="cancelorder",
                request_data=data,
                response_data=error_response,
                error_message=error_message,
            ))
            return make_response(jsonify(error_response), 400)

        except Exception:
            logger.exception("An unexpected error occurred in CancelOrder endpoint.")
            error_message = "An unexpected error occurred"
            if get_analyze_mode():
                return make_response(jsonify(emit_analyzer_error(data, error_message)), 500)
            error_response = {"status": "error", "message": error_message}
            bus.publish(OrderFailedEvent(
                mode="live",
                api_type="cancelorder",
                request_data=data,
                response_data=error_response,
                error_message=error_message,
            ))
            return make_response(jsonify(error_response), 500)

```


---

# FILE: restx_api\chart_api.py

```py
import json
import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from limiter import limiter
from services.chart_service import get_chart_preferences, update_chart_preferences
from utils.logging import get_logger

from .account_schema import ChartSchema

API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "10 per second")
api = Namespace("chart", description="Chart Preferences and Cloud Workspace Sync")

# Initialize logger
logger = get_logger(__name__)

# Initialize schema
chart_schema = ChartSchema()


@api.route("", strict_slashes=False)
class ChartPreferencesResource(Resource):
    @limiter.limit(API_RATE_LIMIT)
    @api.doc(params={"apikey": "API Key for authentication"})
    def get(self):
        """
        Get chart preferences.

        Pass apikey as query parameter: /api/v1/chart?apikey=your-api-key
        Returns all saved chart preferences for the user.
        """
        try:
            # Get apikey from query parameter
            api_key = request.args.get("apikey")

            if not api_key:
                return make_response(
                    jsonify({"status": "error", "message": "Missing apikey parameter"}), 400
                )

            logger.info(f"[ChartAPI] GET preferences request. API Key present: {bool(api_key)}")
            success, response_data, status_code = get_chart_preferences(api_key)

            return make_response(jsonify(response_data), status_code)

        except Exception as e:
            logger.exception(f"Unexpected error in chart GET endpoint: {e}")
            return make_response(
                jsonify({"status": "error", "message": "An unexpected error occurred"}), 500
            )

    @limiter.limit(API_RATE_LIMIT)
    def post(self):
        """
        Update chart preferences.

        Send apikey and preferences in JSON body:
        {"apikey": "your-api-key", "tv_theme": "dark", "tv_chart_layout": "{...}"}
        """
        try:
            data = request.json
            if not data:
                return make_response(
                    jsonify({"status": "error", "message": "No data provided"}), 400
                )

            # Validate that apikey is present
            chart_data = chart_schema.load(data)
            api_key = chart_data["apikey"]

            # Extract preferences (all keys except apikey)
            preferences = {k: v for k, v in data.items() if k != "apikey"}

            # Limit payload: max 50 keys, each key max 50 chars, each value max 1MB
            if len(preferences) > 50:
                return make_response(
                    jsonify({"status": "error", "message": "Too many preference keys (max 50)"}), 400
                )
            for k, v in preferences.items():
                if len(k) > 50:
                    return make_response(
                        jsonify({"status": "error", "message": f"Preference key too long: {k[:20]}... (max 50 chars)"}), 400
                    )
                # Check serialized size for all value types (not just strings)
                try:
                    serialized = json.dumps(v)
                except (TypeError, ValueError):
                    serialized = str(v)
                if len(serialized) > 1_048_576:
                    return make_response(
                        jsonify({"status": "error", "message": f"Preference value too large for key: {k} (max 1MB)"}), 400
                    )

            if not preferences:
                return make_response(
                    jsonify({"status": "error", "message": "No preferences provided to update"}),
                    400,
                )

            logger.info(f"[ChartAPI] POST update request. Keys: {list(preferences.keys())}")
            success, response_data, status_code = update_chart_preferences(api_key, preferences)

            return make_response(jsonify(response_data), status_code)

        except ValidationError as err:
            return make_response(jsonify({"status": "error", "message": err.messages}), 400)
        except Exception as e:
            logger.exception(f"Unexpected error in chart POST endpoint: {e}")
            return make_response(
                jsonify({"status": "error", "message": "An unexpected error occurred"}), 500
            )

```


---

# FILE: restx_api\close_position.py

```py
import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from database.settings_db import get_analyze_mode
from events import OrderFailedEvent
from utils.event_bus import bus
from limiter import limiter
from restx_api.schemas import ClosePositionSchema
from services.close_position_service import close_position, emit_analyzer_error
from utils.logging import get_logger

API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "10 per second")
api = Namespace("close_position", description="Close Position API")

# Initialize logger
logger = get_logger(__name__)

# Initialize schema
close_position_schema = ClosePositionSchema()


@api.route("/", strict_slashes=False)
class ClosePosition(Resource):
    @limiter.limit(API_RATE_LIMIT)
    def post(self):
        """Close all open positions"""
        try:
            data = request.json

            # Validate and deserialize input
            try:
                position_data = close_position_schema.load(data)
            except ValidationError as err:
                error_message = str(err.messages)
                if get_analyze_mode():
                    return make_response(jsonify(emit_analyzer_error(data, error_message)), 400)
                error_response = {"status": "error", "message": error_message}
                bus.publish(OrderFailedEvent(
                    mode="live",
                    api_type="closeposition",
                    request_data=data,
                    response_data=error_response,
                    error_message=error_message,
                ))
                return make_response(jsonify(error_response), 400)

            # Extract API key
            api_key = position_data.pop("apikey", None)

            # Call the service function to close all positions
            success, response_data, status_code = close_position(
                position_data=position_data, api_key=api_key
            )

            return make_response(jsonify(response_data), status_code)

        except KeyError as e:
            missing_field = str(e)
            logger.exception(f"KeyError: Missing field {missing_field}")
            error_message = f"A required field is missing: {missing_field}"
            if get_analyze_mode():
                return make_response(jsonify(emit_analyzer_error(data, error_message)), 400)
            error_response = {"status": "error", "message": error_message}
            bus.publish(OrderFailedEvent(
                mode="live",
                api_type="closeposition",
                request_data=data,
                response_data=error_response,
                error_message=error_message,
            ))
            return make_response(jsonify(error_response), 400)

        except Exception:
            logger.exception("An unexpected error occurred in ClosePosition endpoint.")
            error_message = "An unexpected error occurred"
            if get_analyze_mode():
                return make_response(jsonify(emit_analyzer_error(data, error_message)), 500)
            error_response = {"status": "error", "message": error_message}
            bus.publish(OrderFailedEvent(
                mode="live",
                api_type="closeposition",
                request_data=data,
                response_data=error_response,
                error_message=error_message,
            ))
            return make_response(jsonify(error_response), 500)

```


---

# FILE: restx_api\data_schemas.py

```py
import re

from marshmallow import Schema, ValidationError, fields, validate

from utils.constants import VALID_EXCHANGES


# Custom validator for date or timestamp string
def validate_date_or_timestamp(data):
    """
    Validates that the input string is either in 'YYYY-MM-DD' format or a numeric timestamp.
    """
    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    timestamp_pattern = re.compile(r"^\d{10,13}$")  # Allows for seconds or milliseconds
    if not (isinstance(data, str) and (date_pattern.match(data) or timestamp_pattern.match(data))):
        raise ValidationError(
            "Field must be a string in 'YYYY-MM-DD' format or a numeric timestamp."
        )


# Custom validator for option offset
def validate_option_offset(data):
    """
    Validates option offset: ATM, ITM1-ITM50, OTM1-OTM50
    """
    data_upper = data.upper()
    if data_upper == "ATM":
        return True

    # Check for ITM pattern: ITM followed by 1-50
    itm_pattern = re.compile(r"^ITM([1-9]|[1-4][0-9]|50)$")
    otm_pattern = re.compile(r"^OTM([1-9]|[1-4][0-9]|50)$")

    if not (itm_pattern.match(data_upper) or otm_pattern.match(data_upper)):
        raise ValidationError("Offset must be ATM, ITM1-ITM50, or OTM1-OTM50")

    return True


class QuotesSchema(Schema):
    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))
    symbol = fields.Str(required=True)  # Single symbol
    exchange = fields.Str(required=True, validate=validate.OneOf(VALID_EXCHANGES))  # Exchange (e.g., NSE, BSE)


class SymbolExchangePair(Schema):
    symbol = fields.Str(required=True)
    exchange = fields.Str(required=True, validate=validate.OneOf(VALID_EXCHANGES))


class MultiQuotesSchema(Schema):
    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))
    symbols = fields.List(
        fields.Nested(SymbolExchangePair), required=True, validate=validate.Length(min=1)
    )


class HistorySchema(Schema):
    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))
    symbol = fields.Str(required=True)
    exchange = fields.Str(required=True, validate=validate.OneOf(VALID_EXCHANGES))  # Exchange (e.g., NSE, BSE)
    interval = fields.Str(
        required=True,
        validate=validate.OneOf(
            [
                # Seconds intervals
                "1s",
                "5s",
                "10s",
                "15s",
                "30s",
                "45s",
                # Minutes intervals
                "1m",
                "2m",
                "3m",
                "5m",
                "10m",
                "15m",
                "20m",
                "30m",
                # Hours intervals
                "1h",
                "2h",
                "3h",
                "4h",
                # Daily, Weekly, Monthly, Quarterly, Yearly intervals
                "D",
                "W",
                "M",
                "Q",
                "Y",
            ]
        ),
    )
    start_date = fields.Date(required=True, format="%Y-%m-%d")  # YYYY-MM-DD
    end_date = fields.Date(required=True, format="%Y-%m-%d")  # YYYY-MM-DD
    # Optional: Data source - 'api' (broker, default) or 'db' (DuckDB/Historify)
    source = fields.Str(required=False, load_default="api", validate=validate.OneOf(["api", "db"]))
    # OI is now always included by default for F&O exchanges


class DepthSchema(Schema):
    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))
    symbol = fields.Str(required=True)
    exchange = fields.Str(required=True, validate=validate.OneOf(VALID_EXCHANGES))  # Exchange (e.g., NSE, BSE)


class IntervalsSchema(Schema):
    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))


class SymbolSchema(Schema):
    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))  # API Key for authentication
    symbol = fields.Str(required=True)  # Symbol code (e.g., RELIANCE)
    exchange = fields.Str(required=True, validate=validate.OneOf(VALID_EXCHANGES))  # Exchange (e.g., NSE, BSE)


class TickerSchema(Schema):
    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))
    symbol = fields.Str(required=True)  # Combined exchange:symbol format
    interval = fields.Str(
        required=True,
        validate=validate.OneOf(["1m", "5m", "15m", "30m", "1h", "4h", "D", "W", "M"]),
    )  # Supported intervals: 1m, 5m, 15m, 30m, 1h, 4h, D, W, M etc.
    from_ = fields.Str(
        data_key="from", required=True, validate=validate_date_or_timestamp
    )  # YYYY-MM-DD or millisecond timestamp
    to = fields.Str(
        required=True, validate=validate_date_or_timestamp
    )  # YYYY-MM-DD or millisecond timestamp
    adjusted = fields.Bool(required=False, default=True)  # Adjust for splits
    sort = fields.Str(
        required=False, default="asc", validate=validate.OneOf(["asc", "desc"])
    )  # Sort direction


class SearchSchema(Schema):
    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))  # API Key for authentication
    query = fields.Str(required=True)  # Search query/symbol name
    exchange = fields.Str(required=False, validate=validate.OneOf(VALID_EXCHANGES))  # Optional exchange filter (e.g., NSE, BSE)


class ExpirySchema(Schema):
    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))  # API Key for authentication
    symbol = fields.Str(required=True)  # Underlying symbol (e.g., NIFTY, BANKNIFTY)
    exchange = fields.Str(
        required=True, validate=validate.OneOf(["NFO", "BFO", "MCX", "CDS", "CRYPTO"])
    )  # Exchange (e.g., NFO, BFO, MCX, CDS, CRYPTO)
    instrumenttype = fields.Str(
        required=True, validate=validate.OneOf(["futures", "options"])
    )  # futures or options


class OptionSymbolSchema(Schema):
    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))  # API Key for authentication
    strategy = fields.Str(
        required=False, allow_none=True
    )  # DEPRECATED: Strategy name (optional, will be removed in future versions)
    underlying = fields.Str(required=True)  # Underlying symbol (NIFTY, RELIANCE, NIFTY28OCT25FUT)
    exchange = fields.Str(required=True, validate=validate.OneOf(VALID_EXCHANGES))  # Exchange (NSE_INDEX, NSE, NFO)
    expiry_date = fields.Str(
        required=False
    )  # Expiry date in DDMMMYY format (e.g., 28OCT25). Optional if underlying includes expiry
    strike_int = fields.Int(
        required=False, validate=validate.Range(min=1), allow_none=True
    )  # OPTIONAL: Strike interval. If not provided, actual strikes from database will be used (RECOMMENDED for accuracy)
    offset = fields.Str(
        required=True, validate=validate_option_offset
    )  # Strike offset from ATM (ATM, ITM1-ITM50, OTM1-OTM50)
    option_type = fields.Str(
        required=True, validate=validate.OneOf(["CE", "PE", "ce", "pe"])
    )  # Call or Put option


class OptionGreeksSchema(Schema):
    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))  # API Key for authentication
    symbol = fields.Str(required=True)  # Option symbol (e.g., NIFTY28NOV2424000CE)
    exchange = fields.Str(
        required=True, validate=validate.OneOf(["NFO", "BFO", "CDS", "MCX", "CRYPTO"])
    )  # Exchange (NFO, BFO, CDS, MCX, CRYPTO)
    interest_rate = fields.Float(
        required=False, validate=validate.Range(min=0, max=100)
    )  # Risk-free interest rate (annualized %). Optional, defaults per exchange
    forward_price = fields.Float(
        required=False, validate=validate.Range(min=0)
    )  # Optional: Custom forward/synthetic futures price. If provided, skips underlying price fetch
    underlying_symbol = fields.Str(
        required=False
    )  # Optional: Specify underlying symbol (e.g., NIFTY or NIFTY28NOV24FUT)
    underlying_exchange = fields.Str(
        required=False
    )  # Optional: Specify underlying exchange (NSE_INDEX, NFO, etc.)
    expiry_time = fields.Str(
        required=False
    )  # Optional: Custom expiry time in HH:MM format (e.g., "15:30", "19:00"). If not provided, uses exchange defaults


class InstrumentsSchema(Schema):
    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))  # API Key for authentication
    exchange = fields.Str(
        required=False,
        validate=validate.OneOf(VALID_EXCHANGES),
    )  # Optional exchange filter
    format = fields.Str(
        required=False, validate=validate.OneOf(["json", "csv"])
    )  # Output format (json or csv), defaults to json


class OptionChainSchema(Schema):
    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))  # API Key for authentication
    underlying = fields.Str(required=True)  # Underlying symbol (e.g., NIFTY, BANKNIFTY, RELIANCE)
    exchange = fields.Str(
        required=True, validate=validate.OneOf(VALID_EXCHANGES)
    )  # Exchange (NSE_INDEX, NSE, NFO, BSE_INDEX, BSE, BFO, MCX, CDS)
    expiry_date = fields.Str(
        required=True
    )  # Expiry date in DDMMMYY format (e.g., 28NOV25) - MANDATORY
    strike_count = fields.Int(
        required=False, validate=validate.Range(min=1, max=100), allow_none=True
    )  # Number of strikes above/below ATM. If not provided, returns entire chain


class MarketHolidaysSchema(Schema):
    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))  # API Key for authentication
    year = fields.Int(
        required=False, validate=validate.Range(min=2020, max=2050)
    )  # Year to get holidays for (defaults to current year)


class MarketTimingsSchema(Schema):
    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))  # API Key for authentication
    date = fields.Str(required=True)  # Date in YYYY-MM-DD format


class OptionSymbolRequest(Schema):
    """Schema for a single option symbol request in batch"""

    symbol = fields.Str(required=True)  # Option symbol (e.g., NIFTY28NOV2424000CE)
    exchange = fields.Str(required=True, validate=validate.OneOf(["NFO", "BFO", "CDS", "MCX", "CRYPTO"]))
    underlying_symbol = fields.Str(required=False)  # Optional: Specify underlying symbol
    underlying_exchange = fields.Str(required=False)  # Optional: Specify underlying exchange


class MultiOptionGreeksSchema(Schema):
    """Schema for batch option greeks requests"""

    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))  # API Key for authentication
    symbols = fields.List(
        fields.Nested(OptionSymbolRequest),
        required=True,
        validate=validate.Length(min=1, max=50),  # Max 50 symbols per request
    )
    interest_rate = fields.Float(
        required=False, validate=validate.Range(min=0, max=100)
    )  # Common interest rate for all
    expiry_time = fields.Str(required=False)  # Optional: Common expiry time for all

```


---

# FILE: restx_api\depth.py

```py
import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from limiter import limiter
from services.depth_service import get_depth
from utils.logging import get_logger

from .data_schemas import DepthSchema

API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "10 per second")
api = Namespace("depth", description="Market Depth API")

# Initialize logger
logger = get_logger(__name__)

# Initialize schema
depth_schema = DepthSchema()


@api.route("/", strict_slashes=False)
class Depth(Resource):
    @limiter.limit(API_RATE_LIMIT)
    def post(self):
        """Get market depth for given symbol"""
        try:
            # Validate request data
            depth_data = depth_schema.load(request.json)

            api_key = depth_data["apikey"]
            symbol = depth_data["symbol"]
            exchange = depth_data["exchange"]

            # Call the service function to get depth data with API key
            success, response_data, status_code = get_depth(
                symbol=symbol, exchange=exchange, api_key=api_key
            )

            return make_response(jsonify(response_data), status_code)

        except ValidationError as err:
            return make_response(jsonify({"status": "error", "message": err.messages}), 400)
        except Exception as e:
            logger.exception(f"Unexpected error in depth endpoint: {e}")
            return make_response(
                jsonify({"status": "error", "message": "An unexpected error occurred"}), 500
            )

```


---

# FILE: restx_api\expiry.py

```py
import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from limiter import limiter
from services.expiry_service import get_expiry_dates
from utils.logging import get_logger

from .data_schemas import ExpirySchema

API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "10 per second")
api = Namespace("expiry", description="Expiry dates API for F&O instruments")

# Initialize logger
logger = get_logger(__name__)

# Initialize schema
expiry_schema = ExpirySchema()


@api.route("/", strict_slashes=False)
class Expiry(Resource):
    @limiter.limit(API_RATE_LIMIT)
    def post(self):
        """Get expiry dates for F&O symbols (futures or options) for a given underlying symbol"""
        try:
            # Validate request data
            expiry_data = expiry_schema.load(request.json)

            # Extract parameters
            api_key = expiry_data.pop("apikey", None)
            symbol = expiry_data["symbol"]
            exchange = expiry_data["exchange"]
            instrumenttype = expiry_data["instrumenttype"]

            # Call the service function to get expiry dates
            success, response_data, status_code = get_expiry_dates(
                symbol=symbol, exchange=exchange, instrumenttype=instrumenttype, api_key=api_key
            )

            return make_response(jsonify(response_data), status_code)

        except ValidationError as err:
            return make_response(jsonify({"status": "error", "message": err.messages}), 400)

        except Exception as e:
            logger.exception(f"Unexpected error in expiry endpoint: {e}")
            return make_response(
                jsonify({"status": "error", "message": "An unexpected error occurred"}), 500
            )

```


---

# FILE: restx_api\funds.py

```py
import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from database.auth_db import get_auth_token_broker
from limiter import limiter
from services.funds_service import get_funds
from utils.logging import get_logger

from .account_schema import FundsSchema

API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "10 per second")
api = Namespace("funds", description="Account Funds API")

# Initialize logger
logger = get_logger(__name__)

# Initialize schema
funds_schema = FundsSchema()


@api.route("/", strict_slashes=False)
class Funds(Resource):
    @limiter.limit(API_RATE_LIMIT)
    def post(self):
        """Get account funds and margin details"""
        try:
            # Validate request data
            funds_data = funds_schema.load(request.json)

            api_key = funds_data["apikey"]

            # Call the service function to get funds data with API key
            success, response_data, status_code = get_funds(api_key=api_key)
            return make_response(jsonify(response_data), status_code)

        except ValidationError as err:
            return make_response(jsonify({"status": "error", "message": err.messages}), 400)
        except Exception as e:
            logger.exception(f"Unexpected error in funds endpoint: {e}")
            return make_response(
                jsonify({"status": "error", "message": "An unexpected error occurred"}), 500
            )

```


---

# FILE: restx_api\gtt_orderbook.py

```py
import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from limiter import limiter
from restx_api.schemas import GTTOrderBookSchema
from services.gtt_orderbook_service import get_gtt_orderbook
from utils.logging import get_logger

API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "10 per second")
api = Namespace("gtt_orderbook", description="GTT Order Book API")

logger = get_logger(__name__)
gtt_book_schema = GTTOrderBookSchema()


@api.route("/", strict_slashes=False)
class GTTOrderBook(Resource):
    @limiter.limit(API_RATE_LIMIT)
    def post(self):
        """List all GTT triggers for the authenticated user."""
        try:
            book_data = gtt_book_schema.load(request.json or {})
            api_key = book_data["apikey"]

            success, response_data, status_code = get_gtt_orderbook(api_key=api_key)
            return make_response(jsonify(response_data), status_code)

        except ValidationError as err:
            return make_response(jsonify({"status": "error", "message": err.messages}), 400)
        except Exception:
            logger.exception("An unexpected error occurred in GTTOrderBook endpoint.")
            return make_response(
                jsonify({"status": "error", "message": "An unexpected error occurred"}), 500
            )

```


---

# FILE: restx_api\history.py

```py
import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from limiter import limiter
from services.history_service import get_history
from utils.logging import get_logger

from .data_schemas import HistorySchema

API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "10 per second")
api = Namespace("history", description="Historical Data API")

# Initialize logger
logger = get_logger(__name__)

# Initialize schema
history_schema = HistorySchema()


@api.route("/", strict_slashes=False)
class History(Resource):
    @limiter.limit(API_RATE_LIMIT)
    def post(self):
        """Get historical data for given symbol"""
        try:
            # Validate request data
            history_data = history_schema.load(request.json)

            api_key = history_data["apikey"]
            symbol = history_data["symbol"]
            exchange = history_data["exchange"]
            interval = history_data["interval"]
            start_date = history_data["start_date"]
            end_date = history_data["end_date"]
            source = history_data.get("source", "api")  # Optional, defaults to 'api'

            # Call the service function to get historical data with API key
            success, response_data, status_code = get_history(
                symbol=symbol,
                exchange=exchange,
                interval=interval,
                start_date=start_date,
                end_date=end_date,
                api_key=api_key,
                source=source,
            )

            return make_response(jsonify(response_data), status_code)

        except ValidationError as err:
            return make_response(jsonify({"status": "error", "message": err.messages}), 400)
        except Exception as e:
            logger.exception(f"Unexpected error in history endpoint: {e}")
            return make_response(
                jsonify({"status": "error", "message": "An unexpected error occurred"}), 500
            )

```


---

# FILE: restx_api\holdings.py

```py
import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from limiter import limiter
from services.holdings_service import get_holdings
from utils.logging import get_logger

from .account_schema import HoldingsSchema

API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "10 per second")
api = Namespace("holdings", description="Holdings API")

# Initialize logger
logger = get_logger(__name__)

# Initialize schema
holdings_schema = HoldingsSchema()


@api.route("/", strict_slashes=False)
class Holdings(Resource):
    @limiter.limit(API_RATE_LIMIT)
    def post(self):
        """Get holdings details"""
        try:
            # Validate request data
            holdings_data = holdings_schema.load(request.json)

            api_key = holdings_data["apikey"]

            # Call the service function to get holdings data with API key
            success, response_data, status_code = get_holdings(api_key=api_key)

            return make_response(jsonify(response_data), status_code)

        except ValidationError as err:
            return make_response(jsonify({"status": "error", "message": err.messages}), 400)
        except Exception as e:
            logger.exception(f"Unexpected error in holdings endpoint: {e}")
            return make_response(
                jsonify({"status": "error", "message": "An unexpected error occurred"}), 500
            )

```


---

# FILE: restx_api\instruments.py

```py
import os

from flask import Response, jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from limiter import limiter
from services.instruments_service import get_instruments
from utils.logging import get_logger

from .data_schemas import InstrumentsSchema


class CSVResponse(Response):
    """Custom Response class that supports both CSV and JSON properties for latency monitoring"""

    @property
    def json(self):
        return getattr(self, "_json", None)

    @json.setter
    def json(self, value):
        self._json = value


API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "10 per second")
api = Namespace("instruments", description="Instruments/Symbols download API")

# Initialize logger
logger = get_logger(__name__)

# Initialize schema
instruments_schema = InstrumentsSchema()


@api.route("/", strict_slashes=False)
class Instruments(Resource):
    @limiter.limit(API_RATE_LIMIT)
    def get(self):
        """
        Download all instruments/symbols from the database

        Query Parameters:
            - apikey (required): API key for authentication
            - exchange (optional): Filter by exchange (NSE, BSE, NFO, BFO, BCD, CDS, MCX, NSE_INDEX, BSE_INDEX)
            - format (optional): Output format - 'json' (default) or 'csv'

        Returns:
            - JSON format: Returns instrument data in JSON format
            - CSV format: Returns instrument data as downloadable CSV file
        """
        try:
            # Get query parameters
            query_params = {
                "apikey": request.args.get("apikey"),
                "exchange": request.args.get("exchange"),
                "format": request.args.get("format", "json").lower(),
            }

            # Validate request data
            instruments_data = instruments_schema.load(query_params)

            # Extract parameters
            api_key = instruments_data.get("apikey")
            exchange = instruments_data.get("exchange")
            format_type = instruments_data.get("format", "json")

            # Call the service function to get instruments
            success, response_data, status_code, headers = get_instruments(
                exchange=exchange, api_key=api_key, format=format_type
            )

            # Handle CSV response
            if format_type == "csv":
                if success:
                    response = CSVResponse(response_data, status=status_code)
                    for key, value in headers.items():
                        response.headers[key] = value
                    # Set json property for latency monitoring
                    response.json = {
                        "request_id": f"instruments_{exchange if exchange else 'all'}",
                        "format": "csv",
                        "exchange": exchange if exchange else "all",
                    }
                    return response
                else:
                    # Error case with CSV format
                    error_message = (
                        response_data.get("message", "An error occurred")
                        if isinstance(response_data, dict)
                        else str(response_data)
                    )
                    response = CSVResponse(error_message, status=status_code)
                    response.content_type = "text/plain"
                    response.json = {
                        "request_id": f"instruments_{exchange if exchange else 'all'}_error",
                        "format": "csv",
                        "status": "error",
                    }
                    return response

            # Handle JSON response
            return make_response(jsonify(response_data), status_code)

        except ValidationError as err:
            logger.warning(f"Validation error in instruments endpoint: {err.messages}")
            # Check if CSV format was requested
            format_type = request.args.get("format", "json").lower()
            if format_type == "csv":
                response = CSVResponse(str(err.messages), status=400)
                response.content_type = "text/plain"
                response.json = {"request_id": "instruments_validation_error", "format": "csv"}
                return response
            return make_response(jsonify({"status": "error", "message": err.messages}), 400)

        except Exception as e:
            logger.exception(f"Unexpected error in instruments endpoint: {e}")
            # Check if CSV format was requested
            format_type = request.args.get("format", "json").lower()
            if format_type == "csv":
                response = CSVResponse("An unexpected error occurred", status=500)
                response.content_type = "text/plain"
                response.json = {"request_id": "instruments_error", "format": "csv"}
                return response
            return make_response(
                jsonify({"status": "error", "message": "An unexpected error occurred"}), 500
            )

```


---

# FILE: restx_api\intervals.py

```py
import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from limiter import limiter
from services.intervals_service import get_intervals
from utils.logging import get_logger

from .data_schemas import IntervalsSchema

API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "10 per second")
api = Namespace("intervals", description="Supported Intervals API")

# Initialize logger
logger = get_logger(__name__)

# Initialize schema
intervals_schema = IntervalsSchema()


@api.route("/", strict_slashes=False)
class Intervals(Resource):
    @limiter.limit(API_RATE_LIMIT)
    def post(self):
        """Get supported intervals for the broker"""
        try:
            # Validate request data
            intervals_data = intervals_schema.load(request.json)

            api_key = intervals_data["apikey"]

            # Call the service function to get intervals data with API key
            success, response_data, status_code = get_intervals(api_key=api_key)

            return make_response(jsonify(response_data), status_code)

        except ValidationError as err:
            return make_response(jsonify({"status": "error", "message": err.messages}), 400)
        except Exception as e:
            logger.exception(f"Unexpected error in intervals endpoint: {e}")
            return make_response(
                jsonify({"status": "error", "message": "An unexpected error occurred"}), 500
            )

```


---

# FILE: restx_api\margin.py

```py
import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from database.apilog_db import async_log_order
from database.apilog_db import executor as log_executor
from limiter import limiter
from restx_api.schemas import MarginCalculatorSchema
from services.margin_service import calculate_margin
from utils.logging import get_logger

API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "50 per second")
api = Namespace("margin", description="Margin Calculator API")

# Initialize logger
logger = get_logger(__name__)

# Initialize schema
margin_schema = MarginCalculatorSchema()


@api.route("/", strict_slashes=False)
class MarginCalculator(Resource):
    @limiter.limit(API_RATE_LIMIT)
    def post(self):
        """Calculate margin requirement for a basket of positions"""
        try:
            # Get the request data
            data = request.json

            # Validate and deserialize input using Marshmallow schema
            try:
                validated_data = margin_schema.load(data)
            except ValidationError as err:
                error_message = str(err.messages)
                error_response = {"status": "error", "message": error_message}
                log_executor.submit(async_log_order, "margin", data, error_response)
                return make_response(jsonify(error_response), 400)

            # Extract API key without removing it from the validated data
            api_key = validated_data.get("apikey", None)

            # Call the service function to calculate margin
            success, response_data, status_code = calculate_margin(
                margin_data=validated_data, api_key=api_key
            )

            return make_response(jsonify(response_data), status_code)

        except Exception:
            logger.exception("An unexpected error occurred in Margin Calculator endpoint.")
            error_response = {
                "status": "error",
                "message": "An unexpected error occurred in the API endpoint",
            }
            # Log the error
            try:
                log_executor.submit(
                    async_log_order, "margin", data if "data" in locals() else {}, error_response
                )
            except Exception as e:
                logger.exception(f"Failed to log margin order: {e}")
            return make_response(jsonify(error_response), 500)

```


---

# FILE: restx_api\market_holidays.py

```py
import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from limiter import limiter
from services.market_calendar_service import get_holidays
from utils.logging import get_logger

from .data_schemas import MarketHolidaysSchema

API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "10 per second")
api = Namespace("market/holidays", description="Market Holidays API")

# Initialize logger
logger = get_logger(__name__)

# Initialize schema
holidays_schema = MarketHolidaysSchema()


@api.route("/", strict_slashes=False)
class MarketHolidays(Resource):
    @limiter.limit(API_RATE_LIMIT)
    def post(self):
        """Get market holidays for a specific year"""
        try:
            # Validate request data
            holidays_data = holidays_schema.load(request.json)

            # Extract parameters
            year = holidays_data.get("year")

            # Call the service function to get holidays
            success, response_data, status_code = get_holidays(year=year)

            return make_response(jsonify(response_data), status_code)

        except ValidationError as err:
            return make_response(jsonify({"status": "error", "message": err.messages}), 400)

        except Exception as e:
            logger.exception(f"Unexpected error in market holidays endpoint: {e}")
            return make_response(
                jsonify({"status": "error", "message": "An unexpected error occurred"}), 500
            )

```


---

# FILE: restx_api\market_timings.py

```py
import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from limiter import limiter
from services.market_calendar_service import get_timings
from utils.logging import get_logger

from .data_schemas import MarketTimingsSchema

API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "10 per second")
api = Namespace("market/timings", description="Market Timings API")

# Initialize logger
logger = get_logger(__name__)

# Initialize schema
timings_schema = MarketTimingsSchema()


@api.route("/", strict_slashes=False)
class MarketTimings(Resource):
    @limiter.limit(API_RATE_LIMIT)
    def post(self):
        """Get market timings for a specific date"""
        try:
            # Validate request data
            timings_data = timings_schema.load(request.json)

            # Extract parameters
            date_str = timings_data["date"]

            # Call the service function to get timings
            success, response_data, status_code = get_timings(date_str=date_str)

            return make_response(jsonify(response_data), status_code)

        except ValidationError as err:
            return make_response(jsonify({"status": "error", "message": err.messages}), 400)

        except Exception as e:
            logger.exception(f"Unexpected error in market timings endpoint: {e}")
            return make_response(
                jsonify({"status": "error", "message": "An unexpected error occurred"}), 500
            )

```


---

# FILE: restx_api\modify_gtt_order.py

```py
import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from database.settings_db import get_analyze_mode
from events import GTTModifyFailedEvent
from limiter import limiter
from restx_api.schemas import ModifyGTTOrderSchema
from services.modify_gtt_order_service import emit_analyzer_error, modify_gtt_order
from utils.event_bus import bus
from utils.logging import get_logger

ORDER_RATE_LIMIT = os.getenv("ORDER_RATE_LIMIT", "10 per second")
api = Namespace("modify_gtt_order", description="Modify GTT Order API")

logger = get_logger(__name__)
modify_gtt_schema = ModifyGTTOrderSchema()


@api.route("/", strict_slashes=False)
class ModifyGTTOrder(Resource):
    @limiter.limit(ORDER_RATE_LIMIT)
    def post(self):
        """Modify an active GTT — replaces trigger prices, legs, and condition."""
        try:
            data = request.json or {}

            try:
                order_data = modify_gtt_schema.load(data)
            except ValidationError as err:
                error_message = str(err.messages)
                if get_analyze_mode():
                    return make_response(jsonify(emit_analyzer_error(data, error_message)), 400)
                error_response = {"status": "error", "message": error_message}
                safe_request = {k: v for k, v in data.items() if k != "apikey"}
                bus.publish(GTTModifyFailedEvent(
                    mode="live",
                    api_type="modifygttorder",
                    symbol=data.get("symbol", ""),
                    trigger_id=data.get("trigger_id", ""),
                    request_data=safe_request,
                    response_data=error_response,
                    error_message=error_message,
                ))
                return make_response(jsonify(error_response), 400)

            api_key = order_data.pop("apikey", None)

            success, response_data, status_code = modify_gtt_order(
                order_data=order_data, api_key=api_key
            )

            return make_response(jsonify(response_data), status_code)

        except Exception:
            logger.exception("An unexpected error occurred in ModifyGTTOrder endpoint.")
            return make_response(
                jsonify({"status": "error", "message": "An unexpected error occurred"}), 500
            )

```


---

# FILE: restx_api\modify_order.py

```py
import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from database.settings_db import get_analyze_mode
from events import OrderFailedEvent
from utils.event_bus import bus
from limiter import limiter
from restx_api.schemas import ModifyOrderSchema
from services.modify_order_service import emit_analyzer_error, modify_order
from utils.logging import get_logger

ORDER_RATE_LIMIT = os.getenv("ORDER_RATE_LIMIT", "10 per second")
api = Namespace("modify_order", description="Modify Order API")

# Initialize logger
logger = get_logger(__name__)

# Initialize schema
modify_order_schema = ModifyOrderSchema()


@api.route("/", strict_slashes=False)
class ModifyOrder(Resource):
    @limiter.limit(ORDER_RATE_LIMIT)
    def post(self):
        """Modify an existing order"""
        try:
            data = request.json

            # Validate and deserialize input
            try:
                order_data = modify_order_schema.load(data)
            except ValidationError as err:
                error_message = str(err.messages)
                if get_analyze_mode():
                    return make_response(jsonify(emit_analyzer_error(data, error_message)), 400)
                error_response = {"status": "error", "message": error_message}
                bus.publish(OrderFailedEvent(
                    mode="live",
                    api_type="modifyorder",
                    request_data=data,
                    response_data=error_response,
                    error_message=error_message,
                ))
                return make_response(jsonify(error_response), 400)

            # Extract API key
            api_key = order_data.pop("apikey", None)

            # Call the service function to modify the order
            success, response_data, status_code = modify_order(
                order_data=order_data, api_key=api_key
            )

            return make_response(jsonify(response_data), status_code)

        except KeyError as e:
            missing_field = str(e)
            logger.exception(f"KeyError: Missing field {missing_field}")
            error_message = f"A required field is missing: {missing_field}"
            if get_analyze_mode():
                return make_response(jsonify(emit_analyzer_error(data, error_message)), 400)
            error_response = {"status": "error", "message": error_message}
            bus.publish(OrderFailedEvent(
                mode="live",
                api_type="modifyorder",
                request_data=data,
                response_data=error_response,
                error_message=error_message,
            ))
            return make_response(jsonify(error_response), 400)

        except Exception:
            logger.exception("An unexpected error occurred in ModifyOrder endpoint.")
            error_message = "An unexpected error occurred"
            if get_analyze_mode():
                return make_response(jsonify(emit_analyzer_error(data, error_message)), 500)
            error_response = {"status": "error", "message": error_message}
            bus.publish(OrderFailedEvent(
                mode="live",
                api_type="modifyorder",
                request_data=data,
                response_data=error_response,
                error_message=error_message,
            ))
            return make_response(jsonify(error_response), 500)

```


---

# FILE: restx_api\multi_option_greeks.py

```py
import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from database.auth_db import verify_api_key
from limiter import limiter
from services.option_greeks_service import get_multi_option_greeks
from utils.logging import get_logger

from .data_schemas import MultiOptionGreeksSchema

logger = get_logger(__name__)

# Rate limit for multi option greeks API (same as multiquotes)
API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "10 per second")

api = Namespace("multioptiongreeks", description="Batch Option Greeks API")

# Initialize schema
multi_option_greeks_schema = MultiOptionGreeksSchema()


@api.route("", strict_slashes=False)
class MultiOptionGreeks(Resource):
    @limiter.limit(API_RATE_LIMIT)
    def post(self):
        """
        Calculate Option Greeks for multiple symbols in a single request

        This endpoint calculates option Greeks (Delta, Gamma, Theta, Vega, Rho)
        and Implied Volatility for multiple option symbols using Black-76 model.

        Required fields:
        - apikey: API key for authentication
        - symbols: List of option symbol requests, each containing:
            - symbol: Option symbol (e.g., NIFTY28NOV2424000CE)
            - exchange: Exchange code (NFO, BFO, CDS, MCX)
            - underlying_symbol: (Optional) Underlying symbol
            - underlying_exchange: (Optional) Underlying exchange

        Optional fields:
        - interest_rate: Risk-free interest rate (annualized %). Applied to all symbols.
        - expiry_time: Custom expiry time in HH:MM format. Applied to all symbols.

        Example Request:
        {
            "apikey": "your_api_key",
            "symbols": [
                {"symbol": "NIFTY30DEC2524000CE", "exchange": "NFO"},
                {"symbol": "NIFTY30DEC2524000PE", "exchange": "NFO"},
                {"symbol": "NIFTY30DEC2526000CE", "exchange": "NFO", "underlying_symbol": "NIFTY30DEC25FUT", "underlying_exchange": "NFO"}
            ],
            "interest_rate": 7.0
        }

        Example Response:
        {
            "status": "success",
            "data": [
                {
                    "status": "success",
                    "symbol": "NIFTY30DEC2524000CE",
                    "exchange": "NFO",
                    "implied_volatility": 15.25,
                    "greeks": {"delta": 0.52, "gamma": 0.0001, "theta": -4.97, "vega": 30.76, "rho": 0.001}
                },
                ...
            ],
            "summary": {"total": 3, "success": 2, "failed": 1}
        }
        """
        try:
            # Get request data
            data = request.json

            if data is None:
                return make_response(
                    jsonify(
                        {"status": "error", "message": "Request body is missing or invalid JSON"}
                    ),
                    400,
                )

            # Validate request data
            try:
                validated_data = multi_option_greeks_schema.load(data)
            except ValidationError as err:
                logger.warning(f"Validation error in multi option greeks request: {err.messages}")
                return make_response(
                    jsonify(
                        {"status": "error", "message": "Validation failed", "errors": err.messages}
                    ),
                    400,
                )

            # Extract validated data
            api_key = validated_data.get("apikey")
            symbols = validated_data.get("symbols")
            interest_rate = validated_data.get("interest_rate")
            expiry_time = validated_data.get("expiry_time")

            # Verify API key
            if not verify_api_key(api_key):
                logger.warning(f"Invalid API key used for multi option greeks: {api_key[:10]}...")
                return make_response(
                    jsonify({"status": "error", "message": "Invalid openalgo apikey"}), 401
                )

            # Get multi option Greeks
            logger.info(f"Calculating Greeks for {len(symbols)} symbols")

            success, response, status_code = get_multi_option_greeks(
                symbols=symbols,
                interest_rate=interest_rate,
                expiry_time=expiry_time,
                api_key=api_key,
            )

            if success:
                logger.info(f"Multi Greeks calculated: {response.get('summary', {})}")
            else:
                logger.error(f"Failed to calculate multi Greeks: {response.get('message')}")

            return make_response(jsonify(response), status_code)

        except Exception as e:
            logger.exception(f"Unexpected error in multi option greeks endpoint: {e}")
            return make_response(
                jsonify(
                    {
                        "status": "error",
                        "message": "Internal server error while calculating option Greeks",
                    }
                ),
                500,
            )

```


---

# FILE: restx_api\multiquotes.py

```py
import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from limiter import limiter
from services.quotes_service import get_multiquotes
from utils.logging import get_logger

from .data_schemas import MultiQuotesSchema

API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "10 per second")
api = Namespace("multiquotes", description="Real-time Multiple Quotes API")

# Initialize logger
logger = get_logger(__name__)

# Initialize schema
multiquotes_schema = MultiQuotesSchema()


@api.route("/", strict_slashes=False)
class MultiQuotes(Resource):
    @limiter.limit(API_RATE_LIMIT)
    def post(self):
        """Get real-time quotes for multiple symbols"""
        try:
            # Validate request data
            multiquotes_data = multiquotes_schema.load(request.json)

            api_key = multiquotes_data["apikey"]
            symbols = multiquotes_data["symbols"]

            # Call the service function to get multiquotes data with API key
            success, response_data, status_code = get_multiquotes(symbols=symbols, api_key=api_key)

            return make_response(jsonify(response_data), status_code)

        except ValidationError as err:
            return make_response(jsonify({"status": "error", "message": err.messages}), 400)
        except Exception as e:
            logger.exception(f"Unexpected error in multiquotes endpoint: {e}")
            return make_response(
                jsonify({"status": "error", "message": "An unexpected error occurred"}), 500
            )

```


---

# FILE: restx_api\openposition.py

```py
import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from database.apilog_db import async_log_order
from database.apilog_db import executor as log_executor
from database.settings_db import get_analyze_mode
from limiter import limiter
from restx_api.account_schema import OpenPositionSchema
from services.openposition_service import emit_analyzer_error, get_open_position
from utils.logging import get_logger

API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "10 per second")
api = Namespace("openposition", description="Open Position API")

# Initialize logger
logger = get_logger(__name__)

# Initialize schema
openposition_schema = OpenPositionSchema()


@api.route("/", strict_slashes=False)
class OpenPosition(Resource):
    @limiter.limit(API_RATE_LIMIT)
    def post(self):
        """Get quantity of an open position"""
        try:
            data = request.json

            # Validate and deserialize input using OpenPositionSchema
            try:
                position_data = openposition_schema.load(data)
            except ValidationError as err:
                error_message = str(err.messages)
                if get_analyze_mode():
                    return make_response(jsonify(emit_analyzer_error(data, error_message)), 400)
                error_response = {"status": "error", "message": error_message}
                log_executor.submit(async_log_order, "openposition", data, error_response)
                return make_response(jsonify(error_response), 400)

            # Extract API key
            api_key = position_data.pop("apikey", None)

            # Call the service function to get the open position quantity
            success, response_data, status_code = get_open_position(
                position_data=position_data, api_key=api_key
            )

            return make_response(jsonify(response_data), status_code)

        except Exception:
            logger.exception("An unexpected error occurred in OpenPosition endpoint.")
            error_message = "An unexpected error occurred"
            if get_analyze_mode():
                return make_response(jsonify(emit_analyzer_error(data, error_message)), 500)
            error_response = {"status": "error", "message": error_message}
            log_executor.submit(async_log_order, "openposition", data, error_response)
            return make_response(jsonify(error_response), 500)

```


---

# FILE: restx_api\option_chain.py

```py
"""
Option Chain API Endpoint

POST /api/v1/optionchain

Fetches option chain data with real-time quotes for strikes.
Each CE and PE option includes its own label (ATM, ITM1, ITM2, OTM1, OTM2, etc.).

Request Body:
{
    "apikey": "your_api_key",
    "underlying": "NIFTY",
    "exchange": "NSE_INDEX",
    "expiry_date": "30DEC25",
    "strike_count": 10  // Optional: if not provided, returns entire chain
}

Response:
{
    "status": "success",
    "underlying": "NIFTY",
    "underlying_ltp": 24250.50,
    "expiry_date": "30DEC25",
    "atm_strike": 24250.0,
    "chain": [
        {
            "strike": 24000.0,
            "ce": {
                "symbol": "NIFTY30DEC2524000CE",
                "label": "ITM5",
                "ltp": 320.50,
                ...
            },
            "pe": {
                "symbol": "NIFTY30DEC2524000PE",
                "label": "OTM5",
                "ltp": 85.25,
                ...
            }
        },
        {
            "strike": 24250.0,
            "ce": { "symbol": "...", "label": "ATM", ... },
            "pe": { "symbol": "...", "label": "ATM", ... }
        },
        {
            "strike": 24500.0,
            "ce": { "symbol": "...", "label": "OTM5", ... },
            "pe": { "symbol": "...", "label": "ITM5", ... }
        },
        ...
    ]
}

Strike Labels (different for CE and PE):
    - ATM: At-The-Money strike (same for both CE and PE)
    - Strike BELOW ATM: CE is ITM, PE is OTM
    - Strike ABOVE ATM: CE is OTM, PE is ITM
"""

import os

from flask import request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from limiter import limiter
from services.option_chain_service import get_option_chain
from utils.logging import get_logger

from .data_schemas import OptionChainSchema

# Initialize logger
logger = get_logger(__name__)

# Create namespace
api = Namespace("optionchain", description="Get Option Chain with Real-time Quotes")

# Get rate limit from environment
API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "10 per second")


@api.route("/", strict_slashes=False)
class OptionChain(Resource):
    @limiter.limit(API_RATE_LIMIT)
    def post(self):
        """Get option chain for underlying with real-time quotes"""
        try:
            # Validate request data
            schema = OptionChainSchema()
            data = schema.load(request.json)

            # Extract parameters
            api_key = data["apikey"]
            underlying = data["underlying"]
            exchange = data["exchange"]
            expiry_date = data["expiry_date"]
            strike_count = data.get("strike_count")  # None means return entire chain

            logger.info(
                f"Option chain request: underlying={underlying}, exchange={exchange}, "
                f"expiry={expiry_date}, strike_count={'all' if strike_count is None else strike_count}"
            )

            # Call service to get option chain
            success, response, status_code = get_option_chain(
                underlying=underlying,
                exchange=exchange,
                expiry_date=expiry_date,
                strike_count=strike_count,
                api_key=api_key,
            )

            return response, status_code

        except ValidationError as err:
            logger.warning(f"Validation error in option chain request: {err.messages}")
            return {"status": "error", "message": "Validation error", "errors": err.messages}, 400
        except Exception as e:
            logger.exception(f"Unexpected error in option chain endpoint: {e}")
            return {"status": "error", "message": "An unexpected error occurred"}, 500

```


---

# FILE: restx_api\option_greeks.py

```py
import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from database.auth_db import verify_api_key
from limiter import limiter
from services.option_greeks_service import get_option_greeks
from utils.logging import get_logger

from .data_schemas import OptionGreeksSchema

logger = get_logger(__name__)

# Rate limit for option greeks API
GREEKS_RATE_LIMIT = os.getenv("GREEKS_RATE_LIMIT", "30 per minute")

api = Namespace("optiongreeks", description="Option Greeks API")

# Initialize schema
option_greeks_schema = OptionGreeksSchema()


@api.route("", strict_slashes=False)
class OptionGreeks(Resource):
    @limiter.limit(GREEKS_RATE_LIMIT)
    def post(self):
        """
        Calculate Option Greeks (Delta, Gamma, Theta, Vega, Rho) and Implied Volatility

        This endpoint calculates option Greeks using Black-76 model for options
        across all supported exchanges (NFO, BFO, CDS, MCX).

        Required fields:
        - apikey: API key for authentication
        - symbol: Option symbol (e.g., NIFTY28NOV2424000CE)
        - exchange: Exchange code (NFO, BFO, CDS, MCX)

        Optional fields:
        - interest_rate: Risk-free interest rate (annualized %). Defaults to 0%
        - forward_price: Custom forward/synthetic futures price. If provided, skips underlying price fetch.
                        Useful for synthetic futures (Spot × e^rT) or illiquid underlyings.
        - underlying_symbol: Underlying symbol (e.g., NIFTY or NIFTY28NOV24FUT)
        - underlying_exchange: Underlying exchange (NSE_INDEX, NFO, etc.)
        - expiry_time: Custom expiry time in HH:MM format (e.g., "15:30")

        Example Request (with forward_price):
        {
            "apikey": "your_api_key",
            "symbol": "NIFTY02DEC2524000CE",
            "exchange": "NFO",
            "forward_price": 24550.75,
            "interest_rate": 7.0
        }

        Example Response:
        {
            "status": "success",
            "symbol": "NIFTY02DEC2524000CE",
            "exchange": "NFO",
            "underlying": "NIFTY",
            "strike": 24000,
            "option_type": "CE",
            "expiry_date": "02-Dec-2025",
            "days_to_expiry": 30.5,
            "forward_price": 24550.75,
            "option_price": 296.05,
            "interest_rate": 7.0,
            "implied_volatility": 15.25,
            "greeks": {
                "delta": 0.5234,
                "gamma": 0.000125,
                "theta": -4.9678,
                "vega": 30.7654,
                "rho": 0.001234
            }
        }
        """
        try:
            # Get request data
            data = request.json

            if data is None:
                return make_response(
                    jsonify(
                        {"status": "error", "message": "Request body is missing or invalid JSON"}
                    ),
                    400,
                )

            # Validate request data
            try:
                validated_data = option_greeks_schema.load(data)
            except ValidationError as err:
                logger.warning(f"Validation error in option greeks request: {err.messages}")
                return make_response(
                    jsonify(
                        {"status": "error", "message": "Validation failed", "errors": err.messages}
                    ),
                    400,
                )

            # Extract validated data
            api_key = validated_data.get("apikey")
            symbol = validated_data.get("symbol")
            exchange = validated_data.get("exchange")
            interest_rate = validated_data.get("interest_rate")
            forward_price = validated_data.get("forward_price")
            underlying_symbol = validated_data.get("underlying_symbol")
            underlying_exchange = validated_data.get("underlying_exchange")
            expiry_time = validated_data.get("expiry_time")

            # Verify API key
            if not verify_api_key(api_key):
                logger.warning(f"Invalid API key used for option greeks: {api_key[:10]}...")
                return make_response(
                    jsonify({"status": "error", "message": "Invalid openalgo apikey"}), 401
                )

            # Get option Greeks
            logger.info(f"Calculating Greeks for {symbol} on {exchange}")
            if forward_price:
                logger.info(f"Using custom forward price: {forward_price}")
            elif underlying_symbol:
                logger.info(
                    f"Using custom underlying: {underlying_symbol} on {underlying_exchange or 'auto-detected'}"
                )
            if expiry_time:
                logger.info(f"Using custom expiry time: {expiry_time}")

            success, response, status_code = get_option_greeks(
                option_symbol=symbol,
                exchange=exchange,
                interest_rate=interest_rate,
                forward_price=forward_price,
                underlying_symbol=underlying_symbol,
                underlying_exchange=underlying_exchange,
                expiry_time=expiry_time,
                api_key=api_key,
            )

            if success:
                logger.info(f"Greeks calculated successfully: {symbol}")
            else:
                logger.error(f"Failed to calculate Greeks: {response.get('message')}")

            return make_response(jsonify(response), status_code)

        except Exception as e:
            logger.exception(f"Unexpected error in option greeks endpoint: {e}")
            return make_response(
                jsonify(
                    {
                        "status": "error",
                        "message": "Internal server error while calculating option Greeks",
                    }
                ),
                500,
            )

```


---

# FILE: restx_api\option_symbol.py

```py
"""
Option Symbol API Endpoint

POST /api/v1/optionsymbol

Fetches option symbol based on underlying, expiry, strike offset, and option type.
Calculates ATM from current LTP and returns the appropriate option symbol.

Request Body:
{
    "apikey": "your_api_key",
    "strategy": "strategy_name",  // DEPRECATED: Optional, will be removed in future versions
    "underlying": "NIFTY",  // or "NIFTY28OCT25FUT"
    "exchange": "NSE_INDEX",  // or "NSE", "NFO", "BSE_INDEX", "BSE", "BFO"
    "expiry_date": "28OCT25",  // Optional if underlying includes expiry
    "strike_int": 50,  // Optional: Strike interval. If omitted, actual strikes from database are used (RECOMMENDED)
    "offset": "ITM2",  // ATM, ITM1-ITM50, OTM1-OTM50
    "option_type": "CE"  // CE or PE
}

Response:
{
    "status": "success",
    "symbol": "NIFTY28OCT2523500CE",
    "exchange": "NFO",
    "lotsize": 25,
    "tick_size": 0.05,
    "underlying_ltp": 23587.50
}
"""

import os

from flask import request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from limiter import limiter
from services.option_symbol_service import get_option_symbol
from utils.logging import get_logger

from .data_schemas import OptionSymbolSchema

# Initialize logger
logger = get_logger(__name__)

# Create namespace
api = Namespace("optionsymbol", description="Get Option Symbol based on Underlying and Offset")

# Get rate limit from environment
API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "10 per second")


@api.route("/", strict_slashes=False)
class OptionSymbol(Resource):
    @limiter.limit(API_RATE_LIMIT)
    def post(self):
        """Get option symbol based on underlying, expiry, strike offset, and option type"""
        try:
            # Validate request data
            schema = OptionSymbolSchema()
            data = schema.load(request.json)

            # Extract parameters
            api_key = data["apikey"]
            underlying = data["underlying"]
            exchange = data["exchange"]
            expiry_date = data.get("expiry_date")  # Optional
            strike_int = data.get(
                "strike_int"
            )  # Optional - if not provided, actual strikes from database will be used
            offset = data["offset"]
            option_type = data["option_type"]

            logger.info(
                f"Option symbol request: underlying={underlying}, exchange={exchange}, "
                f"expiry={expiry_date}, strike_int={strike_int}, offset={offset}, type={option_type}"
            )

            # Call service to get option symbol
            success, response, status_code = get_option_symbol(
                underlying=underlying,
                exchange=exchange,
                expiry_date=expiry_date,
                strike_int=strike_int,
                offset=offset,
                option_type=option_type,
                api_key=api_key,
            )

            return response, status_code

        except ValidationError as err:
            logger.warning(f"Validation error in option symbol request: {err.messages}")
            return {"status": "error", "message": "Validation error", "errors": err.messages}, 400
        except Exception as e:
            logger.exception(f"Unexpected error in option symbol endpoint: {e}")
            return {"status": "error", "message": "An unexpected error occurred"}, 500

```


---

# FILE: restx_api\options_multiorder.py

```py
"""
Options Multi-Order API Endpoint

POST /api/v1/optionsmultiorder

Places multiple option legs with common underlying, resolving symbols based on offset.
BUY legs are executed first, then SELL legs for margin efficiency.
Each leg supports optional splitsize parameter to split large orders.

Request Body:
{
    "apikey": "your_api_key",
    "strategy": "Iron Condor",
    "underlying": "NIFTY",
    "exchange": "NSE_INDEX",
    "expiry_date": "28NOV24",
    "legs": [
        {
            "offset": "OTM10",
            "option_type": "CE",
            "action": "BUY",
            "quantity": 75,
            "splitsize": 0  // Optional: If > 0, splits this leg into multiple orders of this size
        },
        {
            "offset": "OTM10",
            "option_type": "PE",
            "action": "BUY",
            "quantity": 150,
            "splitsize": 75  // Example: splits 150 qty into 2 orders of 75 each
        },
        {
            "offset": "OTM5",
            "option_type": "CE",
            "action": "SELL",
            "quantity": 75
        },
        {
            "offset": "OTM5",
            "option_type": "PE",
            "action": "SELL",
            "quantity": 75
        }
    ]
}

Response (Success - Regular Legs):
{
    "status": "success",
    "underlying": "NIFTY",
    "underlying_ltp": 26000.50,
    "results": [
        {
            "leg": 1,
            "symbol": "NIFTY25NOV2526000CE",
            "exchange": "NFO",
            "offset": "OTM10",
            "option_type": "CE",
            "action": "BUY",
            "status": "success",
            "orderid": "240123000001234"
        },
        ...
    ]
}

Response (Success - With Split Leg):
{
    "status": "success",
    "underlying": "NIFTY",
    "underlying_ltp": 26000.50,
    "results": [
        {
            "leg": 1,
            "symbol": "NIFTY25NOV2526000CE",
            "exchange": "NFO",
            "offset": "OTM10",
            "option_type": "CE",
            "action": "BUY",
            "status": "success",
            "orderid": "240123000001234"
        },
        {
            "leg": 2,
            "symbol": "NIFTY25NOV2526000PE",
            "exchange": "NFO",
            "offset": "OTM10",
            "option_type": "PE",
            "action": "BUY",
            "status": "success",
            "total_quantity": 150,
            "split_size": 75,
            "split_results": [
                {"order_num": 1, "quantity": 75, "status": "success", "orderid": "240123000001235"},
                {"order_num": 2, "quantity": 75, "status": "success", "orderid": "240123000001236"}
            ]
        },
        ...
    ]
}

Note: BUY legs execute first for margin efficiency, then SELL legs.
"""

import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from limiter import limiter
from restx_api.schemas import OptionsMultiOrderSchema
from services.options_multiorder_service import place_options_multiorder
from utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Create namespace
api = Namespace("optionsmultiorder", description="Options Multi-Order API")

# Get rate limit from environment
ORDER_RATE_LIMIT = os.getenv("ORDER_RATE_LIMIT", "10 per second")


@api.route("/", strict_slashes=False)
class OptionsMultiOrder(Resource):
    @limiter.limit(ORDER_RATE_LIMIT)
    def post(self):
        """
        Place multiple option legs with common underlying.
        BUY legs execute first for margin efficiency.
        """
        try:
            # Validate request data
            schema = OptionsMultiOrderSchema()
            data = schema.load(request.json)

            # Extract API key
            api_key = data.get("apikey")

            logger.info(
                f"Options multi-order API request: underlying={data.get('underlying')}, "
                f"legs={len(data.get('legs', []))}"
            )

            # Call the service function
            success, response_data, status_code = place_options_multiorder(
                multiorder_data=data, api_key=api_key
            )

            return make_response(jsonify(response_data), status_code)

        except ValidationError as err:
            logger.warning(f"Validation error in options multi-order request: {err.messages}")
            return make_response(
                jsonify({"status": "error", "message": "Validation error", "errors": err.messages}),
                400,
            )
        except Exception:
            logger.exception("An unexpected error occurred in OptionsMultiOrder endpoint.")
            error_response = {
                "status": "error",
                "message": "An unexpected error occurred in the API endpoint",
            }
            return make_response(jsonify(error_response), 500)

```


---

# FILE: restx_api\options_order.py

```py
"""
Options Order API Endpoint

POST /api/v1/optionsorder

Places option orders by resolving option symbol based on underlying and offset,
then placing the order. Works in both live and analyze (sandbox) mode.
Supports order splitting via optional splitsize parameter.

Request Body:
{
    "apikey": "your_api_key",
    "strategy": "strategy_name",
    "underlying": "NIFTY",  // or "NIFTY28NOV24FUT"
    "exchange": "NSE_INDEX",  // or "NSE", "NFO", "BSE_INDEX", "BSE", "BFO"
    "expiry_date": "28NOV24",  // Optional if underlying includes expiry
    "strike_int": 50,  // Optional: Strike interval. If omitted, actual strikes from database are used (RECOMMENDED)
    "offset": "ITM2",  // ATM, ITM1-ITM50, OTM1-OTM50
    "option_type": "CE",  // CE or PE
    "action": "BUY",  // or "SELL"
    "quantity": 75,
    "splitsize": 0,  // Optional: If > 0, splits order into multiple orders of this size
    "pricetype": "MARKET",  // or "LIMIT", "SL", "SL-M"
    "product": "MIS",  // or "NRML"
    "price": 0.0,  // For LIMIT orders
    "trigger_price": 0.0,  // For SL/SL-M orders
    "disclosed_quantity": 0
}

Response (Success - Live Mode - Regular Order):
{
    "status": "success",
    "orderid": "240123000001234",
    "symbol": "NIFTY28NOV2423500CE",
    "exchange": "NFO",
    "underlying": "NIFTY",
    "underlying_ltp": 23587.50,
    "offset": "ITM2",
    "option_type": "CE"
}

Response (Success - Split Order):
{
    "status": "success",
    "symbol": "NIFTY28NOV2423500CE",
    "exchange": "NFO",
    "underlying": "NIFTY",
    "underlying_ltp": 23587.50,
    "offset": "ITM2",
    "option_type": "CE",
    "total_quantity": 150,
    "split_size": 50,
    "results": [
        {"order_num": 1, "quantity": 50, "status": "success", "orderid": "240123000001234"},
        {"order_num": 2, "quantity": 50, "status": "success", "orderid": "240123000001235"},
        {"order_num": 3, "quantity": 50, "status": "success", "orderid": "240123000001236"}
    ]
}

Response (Success - Analyze Mode):
{
    "status": "success",
    "orderid": "SB-1234567890",
    "symbol": "NIFTY28NOV2423500CE",
    "exchange": "NFO",
    "underlying": "NIFTY",
    "underlying_ltp": 23587.50,
    "offset": "ITM2",
    "option_type": "CE",
    "mode": "analyze"
}

Response (Error):
{
    "status": "error",
    "message": "Option symbol NIFTY28NOV2425500CE not found in NFO. Symbol may not exist or master contract needs update."
}
"""

import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from limiter import limiter
from restx_api.schemas import OptionsOrderSchema
from services.place_options_order_service import place_options_order
from utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Create namespace
api = Namespace("optionsorder", description="Place Options Order API")

# Get rate limit from environment
ORDER_RATE_LIMIT = os.getenv("ORDER_RATE_LIMIT", "10 per second")


@api.route("/", strict_slashes=False)
class OptionsOrder(Resource):
    @limiter.limit(ORDER_RATE_LIMIT)
    def post(self):
        """
        Place an options order by resolving the symbol based on underlying and offset.
        Works in both live and analyze (sandbox) mode.
        """
        try:
            # Validate request data
            schema = OptionsOrderSchema()
            data = schema.load(request.json)

            # Extract API key
            api_key = data.get("apikey")

            logger.info(
                f"Options order API request: underlying={data.get('underlying')}, "
                f"offset={data.get('offset')}, action={data.get('action')}"
            )

            # Call the service function to place the options order
            success, response_data, status_code = place_options_order(
                options_data=data, api_key=api_key
            )

            return make_response(jsonify(response_data), status_code)

        except ValidationError as err:
            logger.warning(f"Validation error in options order request: {err.messages}")
            return make_response(
                jsonify({"status": "error", "message": "Validation error", "errors": err.messages}),
                400,
            )
        except Exception:
            logger.exception("An unexpected error occurred in OptionsOrder endpoint.")
            error_response = {
                "status": "error",
                "message": "An unexpected error occurred in the API endpoint",
            }
            return make_response(jsonify(error_response), 500)

```


---

# FILE: restx_api\orderbook.py

```py
import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from limiter import limiter
from services.orderbook_service import get_orderbook
from utils.logging import get_logger

from .account_schema import OrderbookSchema

API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "10 per second")
api = Namespace("orderbook", description="Order Book API")

# Initialize logger
logger = get_logger(__name__)

# Initialize schema
orderbook_schema = OrderbookSchema()


@api.route("/", strict_slashes=False)
class Orderbook(Resource):
    @limiter.limit(API_RATE_LIMIT)
    def post(self):
        """Get order book details"""
        try:
            # Validate request data
            orderbook_data = orderbook_schema.load(request.json)

            api_key = orderbook_data["apikey"]

            # Call the service function to get orderbook data with API key
            success, response_data, status_code = get_orderbook(api_key=api_key)

            return make_response(jsonify(response_data), status_code)

        except ValidationError as err:
            return make_response(jsonify({"status": "error", "message": err.messages}), 400)
        except Exception as e:
            logger.exception(f"Unexpected error in orderbook endpoint: {e}")
            return make_response(
                jsonify({"status": "error", "message": "An unexpected error occurred"}), 500
            )

```


---

# FILE: restx_api\orderstatus.py

```py
import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from database.apilog_db import async_log_order
from database.apilog_db import executor as log_executor
from database.settings_db import get_analyze_mode
from limiter import limiter
from restx_api.account_schema import OrderStatusSchema
from services.orderstatus_service import emit_analyzer_error, get_order_status
from utils.logging import get_logger

API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "10 per second")
api = Namespace("orderstatus", description="Order Status API")

# Initialize logger
logger = get_logger(__name__)

# Initialize schema
orderstatus_schema = OrderStatusSchema()


@api.route("/", strict_slashes=False)
class OrderStatus(Resource):
    @limiter.limit(API_RATE_LIMIT)
    def post(self):
        """Get status of a specific order"""
        try:
            data = request.json

            # Validate and deserialize input using OrderStatusSchema
            try:
                status_data = orderstatus_schema.load(data)
            except ValidationError as err:
                error_message = str(err.messages)
                if get_analyze_mode():
                    return make_response(jsonify(emit_analyzer_error(data, error_message)), 400)
                error_response = {"status": "error", "message": error_message}
                log_executor.submit(async_log_order, "orderstatus", data, error_response)
                return make_response(jsonify(error_response), 400)

            # Extract API key
            api_key = status_data.pop("apikey", None)

            # Call the service function to get the order status
            success, response_data, status_code = get_order_status(
                status_data=status_data, api_key=api_key
            )

            return make_response(jsonify(response_data), status_code)

        except Exception:
            logger.exception("An unexpected error occurred in OrderStatus endpoint.")
            error_message = "An unexpected error occurred"
            if get_analyze_mode():
                return make_response(jsonify(emit_analyzer_error(data, error_message)), 500)
            error_response = {"status": "error", "message": error_message}
            log_executor.submit(async_log_order, "orderstatus", data, error_response)
            return make_response(jsonify(error_response), 500)

```


---

# FILE: restx_api\ping.py

```py
import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from limiter import limiter
from services.ping_service import get_ping
from utils.logging import get_logger

from .account_schema import PingSchema

API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "10 per second")
api = Namespace("ping", description="Ping API to check connectivity and authentication")

# Initialize logger
logger = get_logger(__name__)

# Initialize schema
ping_schema = PingSchema()


@api.route("/", strict_slashes=False)
class Ping(Resource):
    @limiter.limit(API_RATE_LIMIT)
    def post(self):
        """Check API connectivity and authentication"""
        try:
            # Validate request data
            ping_data = ping_schema.load(request.json)

            api_key = ping_data["apikey"]

            # Call the service function to get ping response with API key
            success, response_data, status_code = get_ping(api_key=api_key)
            return make_response(jsonify(response_data), status_code)

        except ValidationError as err:
            return make_response(jsonify({"status": "error", "message": err.messages}), 400)
        except Exception as e:
            logger.exception(f"Unexpected error in ping endpoint: {e}")
            return make_response(
                jsonify({"status": "error", "message": "An unexpected error occurred"}), 500
            )

```


---

# FILE: restx_api\place_gtt_order.py

```py
import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from database.settings_db import get_analyze_mode
from events import GTTFailedEvent
from limiter import limiter
from restx_api.schemas import PlaceGTTOrderSchema
from services.place_gtt_order_service import emit_analyzer_error, place_gtt_order
from utils.event_bus import bus
from utils.logging import get_logger

ORDER_RATE_LIMIT = os.getenv("ORDER_RATE_LIMIT", "10 per second")
api = Namespace("place_gtt_order", description="Place GTT Order API")

logger = get_logger(__name__)
place_gtt_schema = PlaceGTTOrderSchema()


@api.route("/", strict_slashes=False)
class PlaceGTTOrder(Resource):
    @limiter.limit(ORDER_RATE_LIMIT)
    def post(self):
        """Place a GTT (Good Till Triggered) order — single or two-leg OCO."""
        try:
            data = request.json or {}

            try:
                order_data = place_gtt_schema.load(data)
            except ValidationError as err:
                error_message = str(err.messages)
                if get_analyze_mode():
                    return make_response(jsonify(emit_analyzer_error(data, error_message)), 400)
                error_response = {"status": "error", "message": error_message}
                safe_request = {k: v for k, v in data.items() if k != "apikey"}
                bus.publish(GTTFailedEvent(
                    mode="live",
                    api_type="placegttorder",
                    symbol=data.get("symbol", ""),
                    exchange=data.get("exchange", ""),
                    trigger_type=data.get("trigger_type", ""),
                    request_data=safe_request,
                    response_data=error_response,
                    error_message=error_message,
                ))
                return make_response(jsonify(error_response), 400)

            api_key = order_data.pop("apikey", None)

            success, response_data, status_code = place_gtt_order(
                order_data=order_data, api_key=api_key
            )

            return make_response(jsonify(response_data), status_code)

        except Exception:
            logger.exception("An unexpected error occurred in PlaceGTTOrder endpoint.")
            return make_response(
                jsonify({"status": "error", "message": "An unexpected error occurred"}), 500
            )

```


---

# FILE: restx_api\place_order.py

```py
import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource, fields
from marshmallow import ValidationError

from limiter import limiter
from restx_api.schemas import OrderSchema
from services.place_order_service import place_order
from utils.logging import get_logger

ORDER_RATE_LIMIT = os.getenv("ORDER_RATE_LIMIT", "10 per second")
api = Namespace("place_order", description="Place Order API")

# Initialize logger
logger = get_logger(__name__)

# Initialize schema
order_schema = OrderSchema()


@api.route("/", strict_slashes=False)
class PlaceOrder(Resource):
    @limiter.limit(ORDER_RATE_LIMIT)
    def post(self):
        """Place an order with the broker"""
        try:
            data = request.json

            # Validate and deserialize input
            try:
                order_data = order_schema.load(data)
            except ValidationError as err:
                error_response = {"status": "error", "message": str(err.messages)}
                return make_response(jsonify(error_response), 400)

            # Extract API key
            api_key = order_data.get("apikey", None)

            # Call the service function to place the order
            success, response_data, status_code = place_order(order_data=order_data, api_key=api_key)

            return make_response(jsonify(response_data), status_code)

        except Exception:
            logger.exception("An unexpected error occurred in PlaceOrder endpoint.")
            error_response = {
                "status": "error",
                "message": "An unexpected error occurred in the API endpoint",
            }
            return make_response(jsonify(error_response), 500)

```


---

# FILE: restx_api\place_smart_order.py

```py
import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from database.settings_db import get_analyze_mode
from events import OrderFailedEvent
from utils.event_bus import bus
from limiter import limiter
from restx_api.schemas import SmartOrderSchema
from services.place_smart_order_service import emit_analyzer_error, place_smart_order
from utils.logging import get_logger

SMART_ORDER_RATE_LIMIT = os.getenv("SMART_ORDER_RATE_LIMIT", "10 per second")
api = Namespace("place_smart_order", description="Place Smart Order API")

# Initialize logger
logger = get_logger(__name__)

# Initialize schema
smart_order_schema = SmartOrderSchema()


@api.route("/", strict_slashes=False)
class SmartOrder(Resource):
    @limiter.limit(SMART_ORDER_RATE_LIMIT)
    def post(self):
        """Place a smart order"""
        try:
            data = request.json

            # Validate and deserialize input
            try:
                order_data = smart_order_schema.load(data)
            except ValidationError as err:
                error_message = str(err.messages)
                if get_analyze_mode():
                    return make_response(jsonify(emit_analyzer_error(data, error_message)), 400)
                error_response = {"status": "error", "message": error_message}
                bus.publish(OrderFailedEvent(
                    mode="live",
                    api_type="placesmartorder",
                    request_data=data,
                    response_data=error_response,
                    error_message=error_message,
                ))
                return make_response(jsonify(error_response), 400)

            # Extract API key
            api_key = order_data.pop("apikey", None)

            # Call the service function to place the smart order
            success, response_data, status_code = place_smart_order(
                order_data=order_data, api_key=api_key
            )

            return make_response(jsonify(response_data), status_code)

        except Exception:
            logger.exception("An unexpected error occurred in SmartOrder endpoint.")
            error_message = "An unexpected error occurred"
            if get_analyze_mode():
                return make_response(jsonify(emit_analyzer_error(data, error_message)), 500)
            error_response = {"status": "error", "message": error_message}
            bus.publish(OrderFailedEvent(
                mode="live",
                api_type="placesmartorder",
                request_data=data,
                response_data=error_response,
                error_message=error_message,
            ))
            return make_response(jsonify(error_response), 500)

```


---

# FILE: restx_api\pnl_symbols.py

```py
import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from limiter import limiter
from services.sandbox_service import is_sandbox_mode, sandbox_get_pnl_symbols
from utils.logging import get_logger

from .account_schema import PnlSymbolsSchema

API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "10 per second")
api = Namespace("pnl", description="P&L Analysis API")

# Initialize logger
logger = get_logger(__name__)

# Initialize schema
pnl_symbols_schema = PnlSymbolsSchema()


@api.route("/symbols", strict_slashes=False)
class PnLSymbols(Resource):
    @limiter.limit(API_RATE_LIMIT)
    def post(self):
        """Get day P&L breakdown by symbol (Sandbox mode only)"""
        try:
            # Check if sandbox mode is enabled
            if not is_sandbox_mode():
                return make_response(
                    jsonify(
                        {
                            "status": "error",
                            "message": "This endpoint is only available in sandbox/analyzer mode",
                        }
                    ),
                    400,
                )

            # Validate request data
            pnl_data = pnl_symbols_schema.load(request.json)

            api_key = pnl_data["apikey"]

            # Call the service function to get PnL by symbols
            success, response_data, status_code = sandbox_get_pnl_symbols(api_key, request.json)
            return make_response(jsonify(response_data), status_code)

        except ValidationError as err:
            return make_response(jsonify({"status": "error", "message": err.messages}), 400)
        except Exception as e:
            logger.exception(f"Unexpected error in pnl/symbols endpoint: {e}")
            return make_response(
                jsonify({"status": "error", "message": "An unexpected error occurred"}), 500
            )

```


---

# FILE: restx_api\positionbook.py

```py
import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from limiter import limiter
from services.positionbook_service import get_positionbook
from utils.logging import get_logger

from .account_schema import PositionbookSchema

API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "10 per second")
api = Namespace("positionbook", description="Position Book API")

# Initialize logger
logger = get_logger(__name__)

# Initialize schema
positionbook_schema = PositionbookSchema()


@api.route("/", strict_slashes=False)
class Positionbook(Resource):
    @limiter.limit(API_RATE_LIMIT)
    def post(self):
        """Get position book details"""
        try:
            # Validate request data
            positionbook_data = positionbook_schema.load(request.json)

            api_key = positionbook_data["apikey"]

            # Call the service function to get positionbook data with API key
            success, response_data, status_code = get_positionbook(api_key=api_key)

            return make_response(jsonify(response_data), status_code)

        except ValidationError as err:
            return make_response(jsonify({"status": "error", "message": err.messages}), 400)
        except Exception as e:
            logger.exception(f"Unexpected error in positionbook endpoint: {e}")
            return make_response(
                jsonify({"status": "error", "message": "An unexpected error occurred"}), 500
            )

```


---

# FILE: restx_api\quotes.py

```py
import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from limiter import limiter
from services.quotes_service import get_quotes
from utils.logging import get_logger

from .data_schemas import QuotesSchema

API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "10 per second")
api = Namespace("quotes", description="Real-time Quotes API")

# Initialize logger
logger = get_logger(__name__)

# Initialize schema
quotes_schema = QuotesSchema()


@api.route("/", strict_slashes=False)
class Quotes(Resource):
    @limiter.limit(API_RATE_LIMIT)
    def post(self):
        """Get real-time quotes for given symbol"""
        try:
            # Validate request data
            quotes_data = quotes_schema.load(request.json)

            api_key = quotes_data["apikey"]
            symbol = quotes_data["symbol"]
            exchange = quotes_data["exchange"]

            # Call the service function to get quotes data with API key
            success, response_data, status_code = get_quotes(
                symbol=symbol, exchange=exchange, api_key=api_key
            )

            return make_response(jsonify(response_data), status_code)

        except ValidationError as err:
            return make_response(jsonify({"status": "error", "message": err.messages}), 400)
        except Exception as e:
            logger.exception(f"Unexpected error in quotes endpoint: {e}")
            return make_response(
                jsonify({"status": "error", "message": "An unexpected error occurred"}), 500
            )

```


---

# FILE: restx_api\schemas.py

```py
from marshmallow import EXCLUDE, Schema, ValidationError, fields, post_load, pre_load, validate

from utils.constants import CRYPTO_EXCHANGES, VALID_EXCHANGES


def _coerce_quantity_to_int(data):
    """Convert quantity from float to int for non-crypto exchanges.

    Raises ValidationError if a fractional quantity (e.g. 1.9) is sent
    to a non-crypto exchange, since brokers like Zerodha only accept integers.
    """
    if data.get("exchange") not in CRYPTO_EXCHANGES and "quantity" in data:
        qty = data["quantity"]
        if qty != int(qty):
            raise ValidationError(
                {"quantity": [f"Fractional quantity ({qty}) is not allowed for non-crypto exchanges."]}
            )
        data["quantity"] = int(qty)
    return data


class OrderSchema(Schema):
    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))
    strategy = fields.Str(required=True)
    exchange = fields.Str(required=True, validate=validate.OneOf(VALID_EXCHANGES))
    symbol = fields.Str(required=True)
    action = fields.Str(required=True, validate=validate.OneOf(["BUY", "SELL", "buy", "sell"]))
    quantity = fields.Float(
        required=True, validate=validate.Range(min=0, min_inclusive=False, error="Quantity must be a positive number.")
    )
    pricetype = fields.Str(
        missing="MARKET", validate=validate.OneOf(["MARKET", "LIMIT", "SL", "SL-M"])
    )
    product = fields.Str(missing="MIS", validate=validate.OneOf(["MIS", "NRML", "CNC"]))
    price = fields.Float(
        missing=0.0, validate=validate.Range(min=0, error="Price must be a non-negative number.")
    )
    trigger_price = fields.Float(
        missing=0.0,
        validate=validate.Range(min=0, error="Trigger price must be a non-negative number."),
    )
    disclosed_quantity = fields.Int(
        missing=0,
        validate=validate.Range(min=0, error="Disclosed quantity must be a non-negative integer."),
    )
    underlying_ltp = fields.Float(
        missing=None, allow_none=True
    )  # Optional: passed from options order for execution reference

    @post_load
    def coerce_quantity(self, data, **kwargs):
        return _coerce_quantity_to_int(data)


class SmartOrderSchema(Schema):
    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))
    strategy = fields.Str(required=True)
    exchange = fields.Str(required=True, validate=validate.OneOf(VALID_EXCHANGES))
    symbol = fields.Str(required=True)
    action = fields.Str(required=True, validate=validate.OneOf(["BUY", "SELL", "buy", "sell"]))
    quantity = fields.Float(
        required=True,
        validate=validate.Range(min=0, error="Quantity must be a non-negative number."),
    )
    position_size = fields.Float(required=True)
    pricetype = fields.Str(
        missing="MARKET", validate=validate.OneOf(["MARKET", "LIMIT", "SL", "SL-M"])
    )
    product = fields.Str(missing="MIS", validate=validate.OneOf(["MIS", "NRML", "CNC"]))
    price = fields.Float(
        missing=0.0, validate=validate.Range(min=0, error="Price must be a non-negative number.")
    )
    trigger_price = fields.Float(
        missing=0.0,
        validate=validate.Range(min=0, error="Trigger price must be a non-negative number."),
    )
    disclosed_quantity = fields.Int(
        missing=0,
        validate=validate.Range(min=0, error="Disclosed quantity must be a non-negative integer."),
    )

    @post_load
    def coerce_quantity(self, data, **kwargs):
        return _coerce_quantity_to_int(data)


class ModifyOrderSchema(Schema):
    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))
    strategy = fields.Str(required=True)
    exchange = fields.Str(required=True, validate=validate.OneOf(VALID_EXCHANGES))
    symbol = fields.Str(required=True)
    orderid = fields.Str(required=True)
    action = fields.Str(required=True, validate=validate.OneOf(["BUY", "SELL", "buy", "sell"]))
    product = fields.Str(required=True, validate=validate.OneOf(["MIS", "NRML", "CNC"]))
    pricetype = fields.Str(
        required=True, validate=validate.OneOf(["MARKET", "LIMIT", "SL", "SL-M"])
    )
    price = fields.Float(
        required=True, validate=validate.Range(min=0, error="Price must be a non-negative number.")
    )
    quantity = fields.Float(
        required=True, validate=validate.Range(min=0, min_inclusive=False, error="Quantity must be a positive number.")
    )
    disclosed_quantity = fields.Int(
        required=True,
        validate=validate.Range(min=0, error="Disclosed quantity must be a non-negative integer."),
    )
    trigger_price = fields.Float(
        required=True,
        validate=validate.Range(min=0, error="Trigger price must be a non-negative number."),
    )

    @post_load
    def coerce_quantity(self, data, **kwargs):
        return _coerce_quantity_to_int(data)


class CancelOrderSchema(Schema):
    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))
    strategy = fields.Str(required=True)
    orderid = fields.Str(required=True)


class ClosePositionSchema(Schema):
    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))
    strategy = fields.Str(required=True)


class CancelAllOrderSchema(Schema):
    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))
    strategy = fields.Str(required=True)


class BasketOrderItemSchema(Schema):
    exchange = fields.Str(required=True, validate=validate.OneOf(VALID_EXCHANGES))
    symbol = fields.Str(required=True)
    action = fields.Str(required=True, validate=validate.OneOf(["BUY", "SELL", "buy", "sell"]))
    quantity = fields.Float(
        required=True, validate=validate.Range(min=0, min_inclusive=False, error="Quantity must be a positive number.")
    )
    pricetype = fields.Str(
        missing="MARKET", validate=validate.OneOf(["MARKET", "LIMIT", "SL", "SL-M"])
    )
    product = fields.Str(missing="MIS", validate=validate.OneOf(["MIS", "NRML", "CNC"]))
    price = fields.Float(
        missing=0.0, validate=validate.Range(min=0, error="Price must be a non-negative number.")
    )
    trigger_price = fields.Float(
        missing=0.0,
        validate=validate.Range(min=0, error="Trigger price must be a non-negative number."),
    )
    disclosed_quantity = fields.Int(
        missing=0,
        validate=validate.Range(min=0, error="Disclosed quantity must be a non-negative integer."),
    )

    @post_load
    def coerce_quantity(self, data, **kwargs):
        return _coerce_quantity_to_int(data)


class BasketOrderSchema(Schema):
    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))
    strategy = fields.Str(required=True)
    orders = fields.List(
        fields.Nested(BasketOrderItemSchema), required=True
    )  # List of order details


class SplitOrderSchema(Schema):
    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))
    strategy = fields.Str(required=True)
    exchange = fields.Str(required=True, validate=validate.OneOf(VALID_EXCHANGES))
    symbol = fields.Str(required=True)
    action = fields.Str(required=True, validate=validate.OneOf(["BUY", "SELL", "buy", "sell"]))
    quantity = fields.Float(
        required=True,
        validate=validate.Range(min=0, min_inclusive=False, error="Total quantity must be a positive number."),
    )  # Total quantity to split
    splitsize = fields.Int(
        required=True,
        validate=validate.Range(min=1, error="Split size must be a positive integer."),
    )  # Size of each split
    pricetype = fields.Str(
        missing="MARKET", validate=validate.OneOf(["MARKET", "LIMIT", "SL", "SL-M"])
    )
    product = fields.Str(missing="MIS", validate=validate.OneOf(["MIS", "NRML", "CNC"]))
    price = fields.Float(
        missing=0.0, validate=validate.Range(min=0, error="Price must be a non-negative number.")
    )
    trigger_price = fields.Float(
        missing=0.0,
        validate=validate.Range(min=0, error="Trigger price must be a non-negative number."),
    )
    disclosed_quantity = fields.Int(
        missing=0,
        validate=validate.Range(min=0, error="Disclosed quantity must be a non-negative integer."),
    )

    @post_load
    def coerce_quantity(self, data, **kwargs):
        return _coerce_quantity_to_int(data)


class OptionsOrderSchema(Schema):
    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))
    strategy = fields.Str(required=True)
    underlying = fields.Str(
        required=True
    )  # Underlying symbol (NIFTY, BANKNIFTY, RELIANCE, or NIFTY28NOV24FUT)
    exchange = fields.Str(required=True, validate=validate.OneOf(VALID_EXCHANGES))  # Exchange (NSE_INDEX, NSE, BSE_INDEX, BSE, NFO, BFO)
    expiry_date = fields.Str(
        required=False
    )  # Optional if underlying includes expiry (DDMMMYY format)
    strike_int = fields.Int(
        required=False, validate=validate.Range(min=1), allow_none=True
    )  # OPTIONAL: Strike interval. If not provided, actual strikes from database will be used (RECOMMENDED for accuracy)
    offset = fields.Str(required=True)  # ATM, ITM1-ITM50, OTM1-OTM50
    option_type = fields.Str(
        required=True, validate=validate.OneOf(["CE", "PE", "ce", "pe"])
    )  # Call or Put
    action = fields.Str(required=True, validate=validate.OneOf(["BUY", "SELL", "buy", "sell"]))
    quantity = fields.Int(
        required=True, validate=validate.Range(min=1, error="Quantity must be a positive integer.")
    )
    splitsize = fields.Int(
        missing=0,
        validate=validate.Range(min=0, error="Split size must be a non-negative integer."),
        allow_none=True,
    )  # Optional: If > 0, splits order into multiple orders of this size
    pricetype = fields.Str(
        missing="MARKET", validate=validate.OneOf(["MARKET", "LIMIT", "SL", "SL-M"])
    )
    product = fields.Str(
        missing="MIS", validate=validate.OneOf(["MIS", "NRML"])
    )  # Options only support MIS and NRML
    price = fields.Float(
        missing=0.0, validate=validate.Range(min=0, error="Price must be a non-negative number.")
    )
    trigger_price = fields.Float(
        missing=0.0,
        validate=validate.Range(min=0, error="Trigger price must be a non-negative number."),
    )
    disclosed_quantity = fields.Int(
        missing=0,
        validate=validate.Range(min=0, error="Disclosed quantity must be a non-negative integer."),
    )


class OptionsMultiOrderLegSchema(Schema):
    """Schema for a single leg in options multi-order (no symbol - resolved from offset)"""

    offset = fields.Str(required=True)  # ATM, ITM1-ITM50, OTM1-OTM50
    option_type = fields.Str(
        required=True, validate=validate.OneOf(["CE", "PE", "ce", "pe"])
    )  # Call or Put
    action = fields.Str(required=True, validate=validate.OneOf(["BUY", "SELL", "buy", "sell"]))
    quantity = fields.Int(
        required=True, validate=validate.Range(min=1, error="Quantity must be a positive integer.")
    )
    splitsize = fields.Int(
        missing=0,
        validate=validate.Range(min=0, error="Split size must be a non-negative integer."),
        allow_none=True,
    )  # Optional: If > 0, splits leg into multiple orders of this size
    expiry_date = fields.Str(
        required=False
    )  # Optional per-leg expiry (DDMMMYY format) - for diagonal/calendar spreads
    pricetype = fields.Str(
        missing="MARKET", validate=validate.OneOf(["MARKET", "LIMIT", "SL", "SL-M"])
    )
    product = fields.Str(
        missing="MIS", validate=validate.OneOf(["MIS", "NRML"])
    )  # Options only support MIS and NRML
    price = fields.Float(
        missing=0.0, validate=validate.Range(min=0, error="Price must be a non-negative number.")
    )
    trigger_price = fields.Float(
        missing=0.0,
        validate=validate.Range(min=0, error="Trigger price must be a non-negative number."),
    )
    disclosed_quantity = fields.Int(
        missing=0,
        validate=validate.Range(min=0, error="Disclosed quantity must be a non-negative integer."),
    )


class OptionsMultiOrderSchema(Schema):
    """Schema for options multi-order with multiple legs sharing common underlying"""

    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))
    strategy = fields.Str(required=True)
    underlying = fields.Str(required=True)  # Underlying symbol (NIFTY, BANKNIFTY, RELIANCE)
    exchange = fields.Str(required=True, validate=validate.OneOf(VALID_EXCHANGES))  # Exchange (NSE_INDEX, NSE, BSE_INDEX, BSE)
    expiry_date = fields.Str(
        required=False
    )  # Optional if underlying includes expiry (DDMMMYY format)
    strike_int = fields.Int(
        required=False, validate=validate.Range(min=1), allow_none=True
    )  # Optional strike interval
    legs = fields.List(
        fields.Nested(OptionsMultiOrderLegSchema),
        required=True,
        validate=validate.Length(min=1, max=20, error="Legs must contain 1 to 20 items."),
    )


class SyntheticFutureSchema(Schema):
    """Schema for synthetic future calculation"""

    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))
    underlying = fields.Str(required=True)  # Underlying symbol (NIFTY, BANKNIFTY, RELIANCE)
    exchange = fields.Str(required=True, validate=validate.OneOf(VALID_EXCHANGES))  # Exchange (NSE_INDEX, NSE, BSE_INDEX, BSE)
    expiry_date = fields.Str(required=True)  # Expiry date in DDMMMYY format (e.g., 28OCT25)


class MarginPositionSchema(Schema):
    """Schema for a single position in margin calculation"""

    symbol = fields.Str(
        required=True,
        validate=validate.Length(
            min=1, max=50, error="Symbol must be between 1 and 50 characters."
        ),
    )
    exchange = fields.Str(
        required=True, validate=validate.OneOf(VALID_EXCHANGES)
    )
    action = fields.Str(required=True, validate=validate.OneOf(["BUY", "SELL", "buy", "sell"]))
    quantity = fields.Str(required=True)  # String to match API contract, validated in service layer
    product = fields.Str(required=True, validate=validate.OneOf(["MIS", "NRML", "CNC"]))
    pricetype = fields.Str(
        required=True, validate=validate.OneOf(["MARKET", "LIMIT", "SL", "SL-M"])
    )
    price = fields.Str(missing="0")  # String to match API contract
    trigger_price = fields.Str(missing="0")  # String to match API contract


class MarginCalculatorSchema(Schema):
    """Schema for margin calculator request"""

    apikey = fields.Str(
        required=True, validate=validate.Length(min=1, max=256, error="API key must be between 1 and 256 characters.")
    )
    positions = fields.List(
        fields.Nested(MarginPositionSchema),
        required=True,
        validate=validate.Length(min=1, max=50, error="Positions must contain 1 to 50 items."),
    )


# -----------------------------------------------------------------------------
# GTT (Good Till Triggered) Schemas
# -----------------------------------------------------------------------------

def _validate_gtt_place_request(data):
    """Validate flat GTT-place fields and normalise.

    Field semantics:
        ``price``            — entry/SINGLE limit price.
        ``triggerprice_sl``  — stoploss leg trigger.
        ``stoploss``         — stoploss leg limit price.
        ``triggerprice_tg``  — target leg trigger.
        ``target``           — target leg limit price.

    SINGLE: exactly one of ``triggerprice_sl`` / ``triggerprice_tg`` must be
    non-zero; the other is cleared. The resolved trigger is stored in
    ``trigger_price`` (legacy alias) so downstream broker mappers stay simple.
    OCO: all four (``triggerprice_sl``, ``stoploss``, ``triggerprice_tg``,
    ``target``) are required, and ``triggerprice_sl < triggerprice_tg``.
    """
    trigger_type = (data.get("trigger_type") or "").upper()
    if trigger_type not in ("SINGLE", "OCO"):
        raise ValidationError({"trigger_type": ["Must be 'SINGLE' or 'OCO'."]})
    data["trigger_type"] = trigger_type

    sl_trigger = data.get("triggerprice_sl")
    tg_trigger = data.get("triggerprice_tg")

    if trigger_type == "OCO":
        stoploss = data.get("stoploss")
        target = data.get("target")
        if sl_trigger in (None, 0, 0.0):
            raise ValidationError({"triggerprice_sl": ["Required for OCO (stoploss trigger)."]})
        if stoploss in (None, 0, 0.0):
            raise ValidationError({"stoploss": ["Required for OCO (stoploss leg limit)."]})
        if tg_trigger in (None, 0, 0.0):
            raise ValidationError({"triggerprice_tg": ["Required for OCO (target trigger)."]})
        if target in (None, 0, 0.0):
            raise ValidationError({"target": ["Required for OCO (target leg limit)."]})
        if float(sl_trigger) >= float(tg_trigger):
            raise ValidationError({
                "triggerprice_sl": [
                    "Stoploss trigger must be less than target trigger (triggerprice_tg)."
                ]
            })
        # Legacy alias used by broker mappers / event payloads.
        data["trigger_price"] = float(tg_trigger)
    else:  # SINGLE — exactly one of triggerprice_sl / triggerprice_tg is the trigger.
        sl_v = float(sl_trigger) if sl_trigger not in (None, "", 0, 0.0) else 0.0
        tg_v = float(tg_trigger) if tg_trigger not in (None, "", 0, 0.0) else 0.0
        if sl_v <= 0 and tg_v <= 0:
            raise ValidationError({
                "triggerprice_sl": [
                    "SINGLE GTT requires a positive triggerprice_sl or triggerprice_tg."
                ]
            })
        resolved = sl_v if sl_v > 0 else tg_v
        data["triggerprice_sl"] = sl_v if sl_v > 0 else None
        data["triggerprice_tg"] = tg_v if sl_v <= 0 else None
        data["stoploss"] = None
        data["target"] = None
        data["trigger_price"] = resolved  # legacy alias

    exchange = data.get("exchange")
    qty = data.get("quantity")
    if qty is not None and exchange and exchange not in CRYPTO_EXCHANGES:
        if qty != int(qty):
            raise ValidationError({
                "quantity": [f"Fractional quantity ({qty}) is not allowed for non-crypto exchanges."]
            })
        data["quantity"] = int(qty)

    data["action"] = data["action"].upper()
    return data


class PlaceGTTOrderSchema(Schema):
    """Schema for placing a GTT in the flat shape.

    Required fields (all GTTs): apikey, strategy, trigger_type ('SINGLE' or
    'OCO'), exchange, symbol, action, product, quantity, pricetype, price.

    Trigger fields:
        ``triggerprice_sl`` — stoploss leg trigger
        ``triggerprice_tg`` — target leg trigger
        ``stoploss``        — stoploss leg limit (OCO only)
        ``target``          — target leg limit (OCO only)

    SINGLE: pass exactly one of triggerprice_sl / triggerprice_tg (the other
    may be 0 or omitted). OCO: all four are required.

    ``last_price`` is fetched server-side from the quotes API and should not
    be sent by clients.
    """

    class Meta:
        unknown = EXCLUDE

    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))
    strategy = fields.Str(required=True)
    trigger_type = fields.Str(required=True)
    exchange = fields.Str(required=True, validate=validate.OneOf(VALID_EXCHANGES))
    symbol = fields.Str(required=True)
    action = fields.Str(required=True, validate=validate.OneOf(["BUY", "SELL", "buy", "sell"]))
    product = fields.Str(
        required=True,
        validate=validate.OneOf(
            ["NRML", "CNC"],
            error="GTT supports only CNC (delivery) or NRML (overnight F&O); MIS is intraday-only.",
        ),
    )
    quantity = fields.Float(
        required=True,
        validate=validate.Range(min=0, min_inclusive=False, error="Quantity must be a positive number."),
    )
    pricetype = fields.Str(missing="LIMIT", validate=validate.OneOf(["LIMIT", "MARKET"]))
    price = fields.Float(
        required=True,
        validate=validate.Range(min=0, error="Price must be a non-negative number."),
    )
    triggerprice_sl = fields.Float(
        missing=0.0,
        validate=validate.Range(min=0, error="triggerprice_sl must be non-negative."),
    )
    triggerprice_tg = fields.Float(
        missing=0.0,
        validate=validate.Range(min=0, error="triggerprice_tg must be non-negative."),
    )
    stoploss = fields.Float(missing=None, allow_none=True)
    target = fields.Float(missing=None, allow_none=True)
    expires_at = fields.Str(missing=None, allow_none=True)

    @pre_load
    def coerce_empty_to_none(self, data, **kwargs):
        if isinstance(data, dict):
            for key in ("stoploss", "target", "triggerprice_sl", "triggerprice_tg"):
                if data.get(key) == "":
                    data[key] = None if key in ("stoploss", "target") else 0.0
        return data

    @post_load
    def post_process(self, data, **kwargs):
        return _validate_gtt_place_request(data)


class ModifyGTTOrderSchema(Schema):
    """Schema for modifying an active GTT in the flat shape.

    Same fields as :class:`PlaceGTTOrderSchema`, plus ``trigger_id``. Modify
    is a full replacement: the broker's PUT semantics replace trigger prices,
    last price, and order params atomically.
    """

    class Meta:
        unknown = EXCLUDE

    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))
    strategy = fields.Str(required=True)
    trigger_id = fields.Str(required=True, validate=validate.Length(min=1))
    trigger_type = fields.Str(required=True)
    exchange = fields.Str(required=True, validate=validate.OneOf(VALID_EXCHANGES))
    symbol = fields.Str(required=True)
    action = fields.Str(required=True, validate=validate.OneOf(["BUY", "SELL", "buy", "sell"]))
    product = fields.Str(
        required=True,
        validate=validate.OneOf(
            ["NRML", "CNC"],
            error="GTT supports only CNC (delivery) or NRML (overnight F&O); MIS is intraday-only.",
        ),
    )
    quantity = fields.Float(
        required=True,
        validate=validate.Range(min=0, min_inclusive=False, error="Quantity must be a positive number."),
    )
    pricetype = fields.Str(missing="LIMIT", validate=validate.OneOf(["LIMIT", "MARKET"]))
    price = fields.Float(
        required=True,
        validate=validate.Range(min=0, error="Price must be a non-negative number."),
    )
    triggerprice_sl = fields.Float(
        missing=0.0,
        validate=validate.Range(min=0, error="triggerprice_sl must be non-negative."),
    )
    triggerprice_tg = fields.Float(
        missing=0.0,
        validate=validate.Range(min=0, error="triggerprice_tg must be non-negative."),
    )
    stoploss = fields.Float(missing=None, allow_none=True)
    target = fields.Float(missing=None, allow_none=True)

    @pre_load
    def coerce_empty_to_none(self, data, **kwargs):
        if isinstance(data, dict):
            for key in ("stoploss", "target", "triggerprice_sl", "triggerprice_tg"):
                if data.get(key) == "":
                    data[key] = None if key in ("stoploss", "target") else 0.0
        return data

    @post_load
    def post_process(self, data, **kwargs):
        return _validate_gtt_place_request(data)


class CancelGTTOrderSchema(Schema):
    """Schema for cancelling an active GTT."""

    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))
    strategy = fields.Str(required=True)
    trigger_id = fields.Str(required=True, validate=validate.Length(min=1))


class GTTOrderBookSchema(Schema):
    """Schema for listing all GTT triggers for a user."""

    apikey = fields.Str(required=True, validate=validate.Length(min=1, max=256))

```


---

# FILE: restx_api\search.py

```py
import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from limiter import limiter
from services.search_service import search_symbols
from utils.logging import get_logger

from .data_schemas import SearchSchema

API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "10 per second")
api = Namespace("search", description="Symbol search API")

# Initialize logger
logger = get_logger(__name__)

# Initialize schema
search_schema = SearchSchema()


@api.route("/", strict_slashes=False)
class Search(Resource):
    @limiter.limit(API_RATE_LIMIT)
    def post(self):
        """Search for symbols in the database"""
        try:
            # Validate request data
            search_data = search_schema.load(request.json)

            # Extract parameters
            api_key = search_data.pop("apikey", None)
            query = search_data["query"]
            exchange = search_data.get("exchange")

            # Call the service function to search symbols
            success, response_data, status_code = search_symbols(
                query=query, exchange=exchange, api_key=api_key
            )

            return make_response(jsonify(response_data), status_code)

        except ValidationError as err:
            return make_response(jsonify({"status": "error", "message": err.messages}), 400)

        except Exception as e:
            logger.exception(f"Unexpected error in search endpoint: {e}")
            return make_response(
                jsonify({"status": "error", "message": "An unexpected error occurred"}), 500
            )

```


---

# FILE: restx_api\split_order.py

```py
import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from database.settings_db import get_analyze_mode
from events import OrderFailedEvent
from utils.event_bus import bus
from limiter import limiter
from restx_api.schemas import SplitOrderSchema
from services.split_order_service import emit_analyzer_error, split_order
from utils.logging import get_logger

API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "10 per second")
api = Namespace("split_order", description="Split Order API")

# Initialize logger
logger = get_logger(__name__)

# Initialize schema
split_schema = SplitOrderSchema()


@api.route("/", strict_slashes=False)
class SplitOrder(Resource):
    @limiter.limit(API_RATE_LIMIT)
    def post(self):
        """Split a large order into multiple orders of specified size"""
        try:
            data = request.json

            # Validate and deserialize input
            try:
                split_data = split_schema.load(data)
            except ValidationError as err:
                error_message = str(err.messages)
                if get_analyze_mode():
                    return make_response(jsonify(emit_analyzer_error(data, error_message)), 400)
                error_response = {"status": "error", "message": error_message}
                bus.publish(OrderFailedEvent(
                    mode="live",
                    api_type="splitorder",
                    request_data=data,
                    response_data=error_response,
                    error_message=error_message,
                ))
                return make_response(jsonify(error_response), 400)

            # Extract API key
            api_key = split_data.pop("apikey", None)

            # Call the service function to split the order
            success, response_data, status_code = split_order(
                split_data=split_data, api_key=api_key
            )

            return make_response(jsonify(response_data), status_code)

        except Exception:
            logger.exception("An unexpected error occurred in SplitOrder endpoint.")
            error_message = "An unexpected error occurred"
            if get_analyze_mode():
                return make_response(jsonify(emit_analyzer_error(data, error_message)), 500)
            error_response = {"status": "error", "message": error_message}
            bus.publish(OrderFailedEvent(
                mode="live",
                api_type="splitorder",
                request_data=data,
                response_data=error_response,
                error_message=error_message,
            ))
            return make_response(jsonify(error_response), 500)

```


---

# FILE: restx_api\symbol.py

```py
import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from limiter import limiter
from services.symbol_service import get_symbol_info
from utils.logging import get_logger

from .data_schemas import SymbolSchema

API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "10 per second")
api = Namespace("symbol", description="Symbol information API")

# Initialize logger
logger = get_logger(__name__)

# Initialize schema
symbol_schema = SymbolSchema()


@api.route("/", strict_slashes=False)
class Symbol(Resource):
    @limiter.limit(API_RATE_LIMIT)
    def post(self):
        """Get symbol information for a given symbol and exchange"""
        try:
            # Validate request data
            symbol_data = symbol_schema.load(request.json)

            # Extract parameters
            api_key = symbol_data.pop("apikey", None)
            symbol = symbol_data["symbol"]
            exchange = symbol_data["exchange"]

            # Call the service function to get symbol information
            success, response_data, status_code = get_symbol_info(
                symbol=symbol, exchange=exchange, api_key=api_key
            )

            return make_response(jsonify(response_data), status_code)

        except ValidationError as err:
            return make_response(jsonify({"status": "error", "message": err.messages}), 400)

        except Exception as e:
            logger.exception(f"Unexpected error in symbol endpoint: {e}")
            return make_response(
                jsonify({"status": "error", "message": "An unexpected error occurred"}), 500
            )

```


---

# FILE: restx_api\synthetic_future.py

```py
"""
Synthetic Future API Endpoint

POST /api/v1/syntheticfuture

Calculates synthetic future price using ATM Call and Put options.
Does NOT place any orders - returns calculation only.

Request Body:
{
    "apikey": "your_api_key",
    "underlying": "NIFTY",
    "exchange": "NSE_INDEX",
    "expiry_date": "28OCT25"
}

Response (Success):
{
    "status": "success",
    "underlying": "NIFTY",
    "underlying_ltp": 25966.05,
    "expiry": "28OCT25",
    "atm_strike": 26000,
    "synthetic_future_price": 26015.25
}

Response (Error):
{
    "status": "error",
    "message": "Could not fetch LTP for Call option: NIFTY28OCT2526000CE"
}
"""

import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from limiter import limiter
from restx_api.schemas import SyntheticFutureSchema
from services.synthetic_future_service import calculate_synthetic_future
from utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Create namespace
api = Namespace("syntheticfuture", description="Calculate Synthetic Future Price")

# Get rate limit from environment
API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "10 per second")


@api.route("/", strict_slashes=False)
class SyntheticFuture(Resource):
    @limiter.limit(API_RATE_LIMIT)
    def post(self):
        """
        Calculate synthetic future price using ATM options.
        Does NOT place any orders - returns calculation only.
        """
        try:
            # Validate request data
            schema = SyntheticFutureSchema()
            data = schema.load(request.json)

            # Extract parameters
            api_key = data.get("apikey")
            underlying = data.get("underlying")
            exchange = data.get("exchange")
            expiry_date = data.get("expiry_date")

            logger.info(
                f"Synthetic future calculation request: underlying={underlying}, "
                f"exchange={exchange}, expiry={expiry_date}"
            )

            # Call the service function to calculate synthetic future
            success, response_data, status_code = calculate_synthetic_future(
                underlying=underlying, exchange=exchange, expiry_date=expiry_date, api_key=api_key
            )

            return make_response(jsonify(response_data), status_code)

        except ValidationError as err:
            logger.warning(f"Validation error in synthetic future request: {err.messages}")
            return make_response(
                jsonify({"status": "error", "message": "Validation error", "errors": err.messages}),
                400,
            )
        except Exception:
            logger.exception("An unexpected error occurred in SyntheticFuture endpoint.")
            error_response = {
                "status": "error",
                "message": "An unexpected error occurred in the API endpoint",
            }
            return make_response(jsonify(error_response), 500)

```


---

# FILE: restx_api\telegram_bot.py

```py
import asyncio
import os
from concurrent.futures import ThreadPoolExecutor

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource, fields

from database.auth_db import verify_api_key
from database.telegram_db import (
    get_all_telegram_users,
    get_bot_config,
    get_command_stats,
    get_telegram_user_by_username,
    get_user_preferences,
    update_bot_config,
    update_user_preferences,
)
from limiter import limiter
from services.telegram_alert_service import TelegramAlertService, alert_executor
from services.telegram_bot_service import telegram_bot_service
from utils.logging import get_logger

logger = get_logger(__name__)

# Rate limit for telegram operations
TELEGRAM_RATE_LIMIT = os.getenv("TELEGRAM_RATE_LIMIT", "30 per minute")

api = Namespace("telegram", description="Telegram Bot API")

# Thread pool for async operations
executor = ThreadPoolExecutor(max_workers=2)

# Initialize telegram alert service
telegram_alert = TelegramAlertService()

# Define Swagger models
bot_config_model = api.model(
    "BotConfig",
    {
        "token": fields.String(description="Telegram Bot Token"),
        "webhook_url": fields.String(description="Webhook URL for bot"),
        "polling_mode": fields.Boolean(description="Use polling mode"),
        "broadcast_enabled": fields.Boolean(description="Enable broadcast messages"),
        "rate_limit_per_minute": fields.Integer(description="Rate limit per minute"),
    },
)

user_link_model = api.model(
    "UserLink",
    {
        "apikey": fields.String(required=True, description="API Key"),
        "telegram_id": fields.Integer(required=True, description="Telegram User ID"),
        "username": fields.String(required=True, description="OpenAlgo Username"),
    },
)

broadcast_model = api.model(
    "Broadcast",
    {
        "apikey": fields.String(required=True, description="API Key"),
        "message": fields.String(required=True, description="Message to broadcast"),
        "filters": fields.Raw(description="Optional filters for users"),
    },
)

notification_model = api.model(
    "Notification",
    {
        "apikey": fields.String(required=True, description="API Key"),
        "username": fields.String(required=True, description="OpenAlgo Username"),
        "message": fields.String(required=True, description="Notification message"),
        "priority": fields.Integer(description="Priority (1-10)", default=5),
        "wait_for_delivery": fields.Boolean(
            description="Wait for delivery confirmation (default: false, returns immediately)",
            default=False,
        ),
    },
)

preferences_model = api.model(
    "UserPreferences",
    {
        "apikey": fields.String(required=True, description="API Key"),
        "telegram_id": fields.Integer(required=True, description="Telegram User ID"),
        "order_notifications": fields.Boolean(description="Enable order notifications"),
        "trade_notifications": fields.Boolean(description="Enable trade notifications"),
        "pnl_notifications": fields.Boolean(description="Enable P&L notifications"),
        "daily_summary": fields.Boolean(description="Enable daily summary"),
        "summary_time": fields.String(description="Daily summary time (HH:MM)"),
        "language": fields.String(description="Preferred language"),
        "timezone": fields.String(description="User timezone"),
    },
)


def run_async(coro):
    """Helper to run async coroutine in sync context"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@api.route("/config", strict_slashes=False)
class TelegramBotConfig(Resource):
    @limiter.limit(TELEGRAM_RATE_LIMIT)
    @api.doc(security="apikey")
    def get(self):
        """Get current bot configuration"""
        try:
            api_key = request.headers.get("X-API-KEY") or request.args.get("apikey")

            if not api_key or not verify_api_key(api_key):
                return make_response(
                    jsonify({"status": "error", "message": "Invalid or missing API key"}), 401
                )

            config = get_bot_config()

            # Don't expose the full token for security
            if config.get("bot_token"):
                config["bot_token"] = (
                    config["bot_token"][:10] + "..."
                    if len(config["bot_token"]) > 10
                    else config["bot_token"]
                )

            return make_response(jsonify({"status": "success", "data": config}), 200)

        except Exception:
            logger.exception("Error getting bot config")
            return make_response(
                jsonify({"status": "error", "message": "Failed to get bot configuration"}), 500
            )

    @limiter.limit(TELEGRAM_RATE_LIMIT)
    @api.doc(security="apikey")
    @api.expect(bot_config_model)
    def post(self):
        """Update bot configuration"""
        try:
            data = request.json
            api_key = data.get("apikey") or request.headers.get("X-API-KEY")

            if not api_key or not verify_api_key(api_key):
                return make_response(
                    jsonify({"status": "error", "message": "Invalid or missing API key"}), 401
                )

            # Update configuration
            config_update = {}
            if "token" in data:
                config_update["token"] = data["token"]
            if "webhook_url" in data:
                config_update["webhook_url"] = data["webhook_url"]
            if "polling_mode" in data:
                config_update["polling_mode"] = data["polling_mode"]
            if "broadcast_enabled" in data:
                config_update["broadcast_enabled"] = data["broadcast_enabled"]
            if "rate_limit_per_minute" in data:
                try:
                    rate_limit = int(data["rate_limit_per_minute"])
                    if not 1 <= rate_limit <= 120:
                        return make_response(
                            jsonify({"status": "error", "message": "rate_limit_per_minute must be between 1 and 120"}), 400
                        )
                    config_update["rate_limit_per_minute"] = rate_limit
                except (TypeError, ValueError):
                    return make_response(
                        jsonify({"status": "error", "message": "rate_limit_per_minute must be an integer"}), 400
                    )

            success = update_bot_config(config_update)

            if success:
                return make_response(
                    jsonify({"status": "success", "message": "Bot configuration updated"}), 200
                )
            else:
                return make_response(
                    jsonify({"status": "error", "message": "Failed to update bot configuration"}),
                    500,
                )

        except Exception:
            logger.exception("Error updating bot config")
            return make_response(
                jsonify({"status": "error", "message": "Failed to update bot configuration"}), 500
            )


@api.route("/start", strict_slashes=False)
class StartBot(Resource):
    @limiter.limit(TELEGRAM_RATE_LIMIT)
    @api.doc(security="apikey")
    def post(self):
        """Start the Telegram bot"""
        try:
            data = request.json or {}
            api_key = data.get("apikey") or request.headers.get("X-API-KEY")

            if not api_key or not verify_api_key(api_key):
                return make_response(
                    jsonify({"status": "error", "message": "Invalid or missing API key"}), 401
                )

            # Get bot configuration
            config = get_bot_config()

            if not config.get("bot_token"):
                return make_response(
                    jsonify({"status": "error", "message": "Bot token not configured"}), 400
                )

            # Initialize bot
            success, message = run_async(
                telegram_bot_service.initialize_bot(
                    token=config["bot_token"], webhook_url=config.get("webhook_url")
                )
            )

            if not success:
                return make_response(jsonify({"status": "error", "message": message}), 500)

            # Start bot
            if config.get("polling_mode", True):
                success, message = run_async(bot.start_polling())
            else:
                # Webhook mode would be configured separately
                success = True
                message = "Bot initialized for webhook mode"

            if success:
                return make_response(jsonify({"status": "success", "message": message}), 200)
            else:
                return make_response(jsonify({"status": "error", "message": message}), 500)

        except Exception as e:
            logger.exception("Error starting bot")
            return make_response(
                jsonify({"status": "error", "message": f"Failed to start bot: {str(e)}"}), 500
            )


@api.route("/stop", strict_slashes=False)
class StopBot(Resource):
    @limiter.limit(TELEGRAM_RATE_LIMIT)
    @api.doc(security="apikey")
    def post(self):
        """Stop the Telegram bot"""
        try:
            data = request.json or {}
            api_key = data.get("apikey") or request.headers.get("X-API-KEY")

            if not api_key or not verify_api_key(api_key):
                return make_response(
                    jsonify({"status": "error", "message": "Invalid or missing API key"}), 401
                )

            # Stop bot
            success, message = run_async(telegram_bot_service.stop_bot())

            if success:
                return make_response(jsonify({"status": "success", "message": message}), 200)
            else:
                return make_response(jsonify({"status": "error", "message": message}), 500)

        except Exception as e:
            logger.exception("Error stopping bot")
            return make_response(
                jsonify({"status": "error", "message": f"Failed to stop bot: {str(e)}"}), 500
            )


def get_webhook_secret():
    """
    Get or generate webhook secret for Telegram webhook verification.
    Uses TELEGRAM_WEBHOOK_SECRET env var, or derives from bot token if not set.
    """
    # First check for explicit webhook secret
    secret = os.getenv("TELEGRAM_WEBHOOK_SECRET")
    if secret:
        return secret

    # Fall back to deriving from bot token (first 32 chars of token hash)
    config = get_bot_config()
    bot_token = config.get("bot_token")
    if bot_token:
        import hashlib

        return hashlib.sha256(bot_token.encode()).hexdigest()[:32]

    return None


@api.route("/webhook", strict_slashes=False)
class WebhookHandler(Resource):
    def post(self):
        """
        Handle Telegram webhook updates.

        Security: Verifies X-Telegram-Bot-Api-Secret-Token header to ensure
        requests are genuinely from Telegram and not from attackers.
        """
        try:
            # Verify webhook secret token (Telegram sends this header when secret_token is configured)
            expected_secret = get_webhook_secret()

            if expected_secret:
                received_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")

                if not received_secret:
                    logger.warning("Webhook request missing secret token header")
                    # Return 401 Unauthorized for missing token
                    return make_response("Unauthorized", 401)

                if received_secret != expected_secret:
                    logger.warning("Webhook request with invalid secret token")
                    # Return 403 Forbidden for invalid token
                    return make_response("Forbidden", 403)

            # Get update data from Telegram
            update_data = request.json

            if not update_data:
                return make_response("", 200)

            # Basic structure validation - Telegram updates must have update_id
            if not isinstance(update_data, dict) or "update_id" not in update_data:
                logger.warning("Invalid webhook payload structure")
                return make_response("Bad Request", 400)

            # Process update asynchronously
            # Note: process_webhook_update method needs to be implemented in the new service
            # For now, return success
            logger.info(f"Webhook update received: update_id={update_data.get('update_id')}")

            # Always return 200 to Telegram for valid requests
            return make_response("", 200)

        except Exception as e:
            logger.exception(f"Error processing webhook: {str(e)}")
            # Still return 200 to avoid Telegram retries for processing errors
            return make_response("", 200)


@api.route("/users", strict_slashes=False)
class TelegramUsers(Resource):
    @limiter.limit(TELEGRAM_RATE_LIMIT)
    @api.doc(security="apikey")
    def get(self):
        """Get all linked Telegram users"""
        try:
            api_key = request.headers.get("X-API-KEY") or request.args.get("apikey")

            if not api_key or not verify_api_key(api_key):
                return make_response(
                    jsonify({"status": "error", "message": "Invalid or missing API key"}), 401
                )

            # Get filters from query params
            filters = {}
            if request.args.get("broker"):
                filters["broker"] = request.args.get("broker")
            if request.args.get("notifications_enabled"):
                filters["notifications_enabled"] = (
                    request.args.get("notifications_enabled").lower() == "true"
                )

            users = get_all_telegram_users(filters)

            return make_response(
                jsonify({"status": "success", "data": users, "count": len(users)}), 200
            )

        except Exception:
            logger.exception("Error getting telegram users")
            return make_response(
                jsonify({"status": "error", "message": "Failed to get users"}), 500
            )


@api.route("/broadcast", strict_slashes=False)
class BroadcastMessage(Resource):
    @limiter.limit("5 per minute")
    @api.doc(security="apikey")
    @api.expect(broadcast_model)
    def post(self):
        """Broadcast message to multiple users"""
        try:
            data = request.json
            api_key = data.get("apikey") or request.headers.get("X-API-KEY")

            if not api_key or not verify_api_key(api_key):
                return make_response(
                    jsonify({"status": "error", "message": "Invalid or missing API key"}), 401
                )

            message = data.get("message")
            filters = data.get("filters", {})

            if not message or not isinstance(message, str):
                return make_response(
                    jsonify({"status": "error", "message": "Message is required"}), 400
                )

            if len(message) > 4096:
                return make_response(
                    jsonify({"status": "error", "message": "Message must not exceed 4096 characters"}), 400
                )

            # Check if broadcast is enabled
            config = get_bot_config()
            if not config.get("broadcast_enabled", True):
                return make_response(
                    jsonify({"status": "error", "message": "Broadcast is disabled"}), 403
                )

            # Send broadcast
            # Note: broadcast_message method needs to be implemented in the new service
            # For now, return a placeholder response
            success_count, fail_count = 0, 0

            return make_response(
                jsonify(
                    {
                        "status": "success",
                        "message": f"Broadcast sent to {success_count} users, failed for {fail_count} users",
                        "success_count": success_count,
                        "fail_count": fail_count,
                    }
                ),
                200,
            )

        except Exception:
            logger.exception("Error broadcasting message")
            return make_response(
                jsonify({"status": "error", "message": "Failed to broadcast message"}), 500
            )


@api.route("/notify", strict_slashes=False)
class SendNotification(Resource):
    @limiter.limit(TELEGRAM_RATE_LIMIT)
    @api.doc(security="apikey")
    @api.expect(notification_model)
    def post(self):
        """Send notification to a specific user"""
        try:
            data = request.json
            api_key = data.get("apikey") or request.headers.get("X-API-KEY")

            if not api_key or not verify_api_key(api_key):
                return make_response(
                    jsonify({"status": "error", "message": "Invalid or missing API key"}), 401
                )

            username = data.get("username")
            message = data.get("message")
            try:
                priority = int(data.get("priority", 5))
                if not 1 <= priority <= 10:
                    priority = 5
            except (TypeError, ValueError):
                priority = 5

            if not username or not message:
                return make_response(
                    jsonify({"status": "error", "message": "Username and message are required"}),
                    400,
                )

            # Get user's telegram ID
            user = get_telegram_user_by_username(username)

            if not user:
                return make_response(
                    jsonify(
                        {"status": "error", "message": "User not found or not linked to Telegram"}
                    ),
                    404,
                )

            # Get telegram_id from user
            telegram_id = user.get("telegram_id")

            if not telegram_id:
                return make_response(
                    jsonify({"status": "error", "message": "User telegram_id not found"}), 404
                )

            # Send notification via telegram alert service
            wait_for_delivery = data.get("wait_for_delivery", False)

            if wait_for_delivery:
                # Synchronous: wait for delivery confirmation
                success = telegram_alert.send_alert_sync(telegram_id, message)
                if success:
                    logger.info(f"Telegram alert sent to user {username} (ID: {telegram_id})")
                    return make_response(
                        jsonify({"status": "success", "message": "Notification sent successfully"}),
                        200,
                    )
                else:
                    logger.warning(
                        f"Failed to send telegram alert to user {username} (ID: {telegram_id}), queued for retry"
                    )
                    return make_response(
                        jsonify(
                            {"status": "success", "message": "Notification queued for delivery"}
                        ),
                        200,
                    )
            else:
                # Async: fire-and-forget (default, fast path)
                alert_executor.submit(telegram_alert.send_alert_sync, telegram_id, message)
                logger.info(
                    f"Telegram notification queued for user {username} (ID: {telegram_id})"
                )
                return make_response(
                    jsonify({"status": "success", "message": "Notification queued for delivery"}),
                    200,
                )

        except Exception:
            logger.exception("Error sending notification")
            return make_response(
                jsonify({"status": "error", "message": "Failed to send notification"}), 500
            )


@api.route("/stats", strict_slashes=False)
class TelegramStats(Resource):
    @limiter.limit(TELEGRAM_RATE_LIMIT)
    @api.doc(security="apikey")
    def get(self):
        """Get bot usage statistics"""
        try:
            api_key = request.headers.get("X-API-KEY") or request.args.get("apikey")

            if not api_key or not verify_api_key(api_key):
                return make_response(
                    jsonify({"status": "error", "message": "Invalid or missing API key"}), 401
                )

            # Get days parameter (default 7, max 365)
            try:
                days = min(max(int(request.args.get("days", 7)), 1), 365)
            except (TypeError, ValueError):
                days = 7

            stats = get_command_stats(days)

            return make_response(jsonify({"status": "success", "data": stats}), 200)

        except Exception:
            logger.exception("Error getting stats")
            return make_response(
                jsonify({"status": "error", "message": "Failed to get statistics"}), 500
            )


@api.route("/preferences", strict_slashes=False)
class UserPreferences(Resource):
    @limiter.limit(TELEGRAM_RATE_LIMIT)
    @api.doc(security="apikey")
    def get(self):
        """Get user preferences"""
        try:
            api_key = request.headers.get("X-API-KEY") or request.args.get("apikey")
            telegram_id = request.args.get("telegram_id", type=int)

            if not api_key or not verify_api_key(api_key):
                return make_response(
                    jsonify({"status": "error", "message": "Invalid or missing API key"}), 401
                )

            if not telegram_id:
                return make_response(
                    jsonify({"status": "error", "message": "telegram_id is required"}), 400
                )

            preferences = get_user_preferences(telegram_id)

            return make_response(jsonify({"status": "success", "data": preferences}), 200)

        except Exception:
            logger.exception("Error getting preferences")
            return make_response(
                jsonify({"status": "error", "message": "Failed to get preferences"}), 500
            )

    @limiter.limit(TELEGRAM_RATE_LIMIT)
    @api.doc(security="apikey")
    @api.expect(preferences_model)
    def post(self):
        """Update user preferences"""
        try:
            data = request.json
            api_key = data.get("apikey") or request.headers.get("X-API-KEY")

            if not api_key or not verify_api_key(api_key):
                return make_response(
                    jsonify({"status": "error", "message": "Invalid or missing API key"}), 401
                )

            telegram_id = data.get("telegram_id")

            if not telegram_id:
                return make_response(
                    jsonify({"status": "error", "message": "telegram_id is required"}), 400
                )

            # Extract preferences
            preferences = {}
            for key in [
                "order_notifications",
                "trade_notifications",
                "pnl_notifications",
                "daily_summary",
                "summary_time",
                "language",
                "timezone",
            ]:
                if key in data:
                    preferences[key] = data[key]

            success = update_user_preferences(telegram_id, preferences)

            if success:
                return make_response(
                    jsonify({"status": "success", "message": "Preferences updated successfully"}),
                    200,
                )
            else:
                return make_response(
                    jsonify({"status": "error", "message": "Failed to update preferences"}), 500
                )

        except Exception:
            logger.exception("Error updating preferences")
            return make_response(
                jsonify({"status": "error", "message": "Failed to update preferences"}), 500
            )

```


---

# FILE: restx_api\ticker.py

```py
import importlib
import os
from datetime import UTC, datetime, timedelta, timezone, date

import pandas as pd
import pytz
from flask import Response, jsonify, make_response, request
from flask_restx import Namespace, Resource, fields
from marshmallow import ValidationError

from database.auth_db import get_auth_token_broker
from limiter import limiter
from utils.logging import get_logger

from .data_schemas import TickerSchema

from types import ModuleType



API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "10 per second")
api = Namespace("ticker", description="Stock Ticker Data API")

# Initialize logger
logger = get_logger(__name__)

# Initialize schema
ticker_schema = TickerSchema()


def import_broker_module(broker_name: str) -> ModuleType | None:
    try:
        module_path = f"broker.{broker_name}.api.data"
        broker_module = importlib.import_module(module_path)
        return broker_module
    except ImportError as error:
        logger.exception(f"Error importing broker module '{module_path}': {error}")
        return None


class TextResponse(Response):
    """Custom Response class that supports both text and JSON properties"""

    @property
    def json(self):
        return getattr(self, "_json", None)

    @json.setter
    def json(self, value):
        self._json = value


def convert_timestamp(timestamp: float, interval: str) -> str | tuple[str, str]:
    """Convert timestamp to appropriate format based on interval"""
    # Convert timestamp to datetime in UTC
    dt = datetime.fromtimestamp(timestamp, tz=UTC)

    # Convert to IST
    ist = pytz.timezone("Asia/Kolkata")
    dt_ist = dt.astimezone(ist)

    # For daily data: just return the date
    if interval.upper() == "D":
        return dt_ist.strftime("%Y-%m-%d")

    # For intraday: return date and time separately
    return dt_ist.strftime("%Y-%m-%d"), dt_ist.strftime("%H:%M:%S")


def validate_and_adjust_date_range(
    start_date: str | date,
    end_date: str | date,
    interval: str,
) -> tuple[str | date, str | date, bool]:
    """
    Validate and adjust date range based on interval to prevent large queries

    Rules:
    - D, W, M intervals: maximum 10 years from end_date
    - All other intervals: maximum 30 days from end_date

    Returns tuple: (adjusted_start_date, adjusted_end_date, was_adjusted)
    """
    try:
        # Parse dates
        if isinstance(start_date, str):
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            start_dt = start_date

        if isinstance(end_date, str):
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            end_dt = end_date

        # Determine maximum allowed range based on interval
        interval_upper = interval.upper()
        if interval_upper in ["D", "W", "M"]:
            # Daily, Weekly, Monthly: 10 years maximum
            max_days = 10 * 365  # 10 years
        else:
            # Intraday intervals: 30 days maximum
            max_days = 30

        # Calculate the earliest allowed start date
        earliest_start = end_dt - timedelta(days=max_days)

        # Check if adjustment is needed
        if start_dt < earliest_start:
            adjusted_start = earliest_start.strftime("%Y-%m-%d")
            logger.warning(
                f"Date range adjusted: {start_date} -> {adjusted_start} (interval: {interval}, max days: {max_days})"
            )
            return adjusted_start, end_date, True

        return start_date, end_date, False

    except Exception as e:
        logger.exception(f"Error in date range validation: {e}")
        # Return original dates if parsing fails
        return start_date, end_date, False


@api.route("/<string:symbol>")
@api.doc(
    params={
        "symbol": "Stock symbol with exchange (e.g., NSE:RELIANCE)",
        "interval": "Time interval (e.g., D, 5m, 1h)",
        "from": "Start date (YYYY-MM-DD)",
        "to": "End date (YYYY-MM-DD)",
        "adjusted": "Adjust for splits (true/false)",
        "sort": "Sort order (asc/desc)",
        "apikey": "API Key for authentication",
        "format": "Response format (json/txt). Default: json",
    }
)
class Ticker(Resource):
    @limiter.limit(API_RATE_LIMIT)
    def get(self, symbol):
        """Get aggregate bars for a stock over a given date range with specified interval"""
        try:
            # Default to NSE:RELIANCE if no symbol is provided
            if not symbol:
                symbol = "NSE:RELIANCE"

            # Split exchange and symbol
            parts = symbol.split(":")
            if len(parts) == 2:
                exchange, symbol = parts
            else:
                exchange = "NSE"
                symbol = "RELIANCE"

            # Get parameters from query string
            ticker_data = {
                "apikey": request.args.get("apikey"),
                "symbol": symbol,
                "exchange": exchange,
                "interval": request.args.get("interval", "D"),
                "start_date": request.args.get("from"),
                "end_date": request.args.get("to"),
            }

            # Get format parameter
            response_format = request.args.get("format", "json").lower()

            # Validate request data using HistorySchema since we're reusing that functionality
            from .data_schemas import HistorySchema

            history_schema = HistorySchema()
            history_data = history_schema.load(ticker_data)

            # Apply date range restrictions to prevent large queries
            if history_data.get("start_date") and history_data.get("end_date"):
                adjusted_start, adjusted_end, was_adjusted = validate_and_adjust_date_range(
                    history_data["start_date"], history_data["end_date"], history_data["interval"]
                )
                history_data["start_date"] = adjusted_start
                history_data["end_date"] = adjusted_end

                if was_adjusted:
                    logger.info(
                        f"Date range restricted for {history_data['symbol']} ({history_data['interval']}): {adjusted_start} to {adjusted_end}"
                    )

            api_key = history_data["apikey"]
            AUTH_TOKEN, broker = get_auth_token_broker(api_key)
            if AUTH_TOKEN is None:
                if response_format == "txt":
                    response = TextResponse("Invalid openalgo apikey\n")
                    response.content_type = "text/plain"
                    response.json = {"request_id": f"ticker_{symbol}_{history_data['interval']}"}
                    return response, 403
                return make_response(
                    jsonify({"status": "error", "message": "Invalid openalgo apikey"}), 403
                )

            broker_module = import_broker_module(broker)
            if broker_module is None:
                if response_format == "txt":
                    response = TextResponse("Broker-specific module not found\n")
                    response.content_type = "text/plain"
                    response.json = {"request_id": f"ticker_{symbol}_{history_data['interval']}"}
                    return response, 404
                return make_response(
                    jsonify({"status": "error", "message": "Broker-specific module not found"}), 404
                )

            try:
                # Initialize broker's data handler
                data_handler = broker_module.BrokerData(AUTH_TOKEN)

                # Use chunked API call
                df = data_handler.get_history(
                    history_data["symbol"],
                    history_data["exchange"],
                    history_data["interval"],
                    history_data["start_date"],
                    history_data["end_date"],
                )

                if not isinstance(df, pd.DataFrame):
                    raise ValueError("Invalid data format returned from broker")

                # Format the response based on the format parameter
                if response_format == "txt":
                    # Convert timestamps to datetime format
                    text_output = []
                    interval = history_data["interval"]
                    symbol_with_exchange = f"{history_data['exchange']}:{history_data['symbol']}"

                    for _, row in df.iterrows():
                        # Convert timestamp based on interval
                        timestamp = convert_timestamp(row["timestamp"], interval)
                        # Convert volume to integer by removing decimal point
                        volume = int(row["volume"])
                        if interval.upper() == "D":
                            # Daily format: Ticker,Date_YMD,Open,High,Low,Close,Volume
                            text_output.append(
                                f"{symbol_with_exchange},{timestamp},{row['open']},{row['high']},{row['low']},{row['close']},{volume}"
                            )
                        else:
                            # Intraday format: Ticker,Date_YMD,Time,Open,High,Low,Close,Volume
                            date, time = timestamp
                            text_output.append(
                                f"{symbol_with_exchange},{date},{time},{row['open']},{row['high']},{row['low']},{row['close']},{volume}"
                            )

                    # Create plain text response
                    response = TextResponse("\n".join(text_output))
                    response.content_type = "text/plain"
                    response.json = {"request_id": f"ticker_{symbol}_{history_data['interval']}"}
                    return response
                else:
                    # Return JSON format
                    return make_response(
                        jsonify({"status": "success", "data": df.to_dict(orient="records")}), 200
                    )

            except Exception as e:
                logger.exception(f"Error in broker_module.get_history: {e}")
                if response_format == "txt":
                    response = TextResponse(str(e))
                    response.content_type = "text/plain"
                    response.json = {"request_id": f"ticker_{symbol}_{history_data['interval']}"}
                    return response, 500
                return make_response(jsonify({"status": "error", "message": str(e)}), 500)

        except ValidationError as err:
            if response_format == "txt":
                response = TextResponse(str(err.messages))
                response.content_type = "text/plain"
                response.json = {"request_id": "ticker_validation_error"}
                return response, 400
            return make_response(jsonify({"status": "error", "message": err.messages}), 400)
        except Exception as e:
            logger.exception(f"Unexpected error in ticker endpoint: {e}")
            if response_format == "txt":
                response = TextResponse("An unexpected error occurred")
                response.content_type = "text/plain"
                response.json = {"request_id": "ticker_unknown_error"}
                return response, 500
            return make_response(
                jsonify({"status": "error", "message": "An unexpected error occurred"}), 500
            )

```


---

# FILE: restx_api\tradebook.py

```py
import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from limiter import limiter
from services.tradebook_service import get_tradebook
from utils.logging import get_logger

from .account_schema import TradebookSchema

API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "10 per second")
api = Namespace("tradebook", description="Trade Book API")

# Initialize logger
logger = get_logger(__name__)

# Initialize schema
tradebook_schema = TradebookSchema()


@api.route("/", strict_slashes=False)
class Tradebook(Resource):
    @limiter.limit(API_RATE_LIMIT)
    def post(self):
        """Get trade book details"""
        try:
            # Validate request data
            tradebook_data = tradebook_schema.load(request.json)

            api_key = tradebook_data["apikey"]

            # Call the service function to get tradebook data with API key
            success, response_data, status_code = get_tradebook(api_key=api_key)

            return make_response(jsonify(response_data), status_code)

        except ValidationError as err:
            return make_response(jsonify({"status": "error", "message": err.messages}), 400)
        except Exception as e:
            logger.exception(f"Unexpected error in tradebook endpoint: {e}")
            return make_response(
                jsonify({"status": "error", "message": "An unexpected error occurred"}), 500
            )

```


---

# FILE: restx_api\whatsapp_bot.py

```py
"""
WhatsApp REST namespace — deliberately minimal.

The only thing an external API-key holder can do is **send a WhatsApp
message**. Everything else — pairing, unpairing, starting / stopping the
bot, reading or mutating config, listing linked recipients, broadcasting
to all of them, reading stats, editing preferences — is admin-only and
lives behind the session-authed blueprint at /whatsapp.

Why so restrictive: the paired-device session blob is functionally a
credential to the operator's WhatsApp account. A leaked API key should
never be enough to re-pair, wipe, or reconfigure the bot, or to enumerate
the operator's contact list. The narrow `/notify` surface lets strategies
and external dashboards fire alerts without ever exposing that admin
control plane.

Mounted at /api/v1/whatsapp.
"""

import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource, fields

from database.auth_db import verify_api_key
from database.whatsapp_db import get_whatsapp_user_by_username
from limiter import limiter
from services.whatsapp_alert_service import alert_executor, whatsapp_alert_service
from services.whatsapp_bot_service import (
    normalize_phone,
    phone_to_jid,
    validate_attachment_path,
    whatsapp_bot_service,
)
from utils.logging import get_logger

logger = get_logger(__name__)

WHATSAPP_RATE_LIMIT = os.getenv("WHATSAPP_RATE_LIMIT", "30 per minute")

api = Namespace("whatsapp", description="WhatsApp send API")

notify_model = api.model(
    "WhatsAppNotification",
    {
        "apikey": fields.String(required=True),
        "self": fields.Boolean(
            default=False,
            description="If true, send to the paired device's own number (the operator).",
        ),
        "username": fields.String(
            description="OpenAlgo username — resolves to that user's linked WhatsApp number."
        ),
        "phone": fields.String(
            description="Single E.164 digit string to message directly (e.g. 919876543210)."
        ),
        "phones": fields.List(
            fields.String,
            description="Up to 5 E.164 digit strings for a small broadcast. "
            "Anything beyond 5 is dropped — WhatsApp ToS-safe usage.",
        ),
        "message": fields.String(description="Text body. Optional if image/document set."),
        "image_path": fields.String(description="Server-local path to an image file"),
        "document_path": fields.String(description="Server-local path to a document file"),
        "caption": fields.String(description="Caption for image / follow-up for document"),
        "filename": fields.String(description="Override document display name"),
        "wait_for_delivery": fields.Boolean(default=True),
    },
)


def _resolve_api_key(data: dict | None = None) -> str | None:
    if data is None:
        data = {}
    return data.get("apikey") or request.headers.get("X-API-KEY") or request.args.get("apikey")


def _auth_or_401(data: dict | None = None):
    api_key = _resolve_api_key(data)
    if not api_key or not verify_api_key(api_key):
        return make_response(
            jsonify({"status": "error", "message": "Invalid or missing API key"}), 401
        )
    return None


@api.route("/notify", strict_slashes=False)
class WhatsAppNotify(Resource):
    @limiter.limit(WHATSAPP_RATE_LIMIT)
    @api.doc(security="apikey")
    @api.expect(notify_model)
    def post(self):
        """Send a WhatsApp message — the single trader-facing send entry.

        Recipient (exactly one of):
            "self": true                — send to the paired device's own number
            "username": "<openalgo>"    — resolve via linked-users table
            "phone": "919876543210"     — direct E.164 digits
            "phones": ["a", "b", ...]   — small broadcast (up to 5 recipients)

        Payload — combine freely:
            "message": "..."            text body
            "image_path": "/path/png"   image attachment (caption falls back to message)
            "document_path": "/path/pdf"
            "caption": "..."
            "filename": "..."

        Fire-and-forget by default; set "wait_for_delivery": true to block
        and receive a per-recipient delivery report.
        """
        data = request.json or {}
        err = _auth_or_401(data)
        if err:
            return err

        # Hard precheck: refuse the send entirely if WhatsApp isn't ready.
        # We do NOT queue on not-paired — a caller is better off seeing a
        # clear "pair first" error than discovering hours later that their
        # alerts never went out. The /whatsapp admin UI is the only place
        # pairing happens.
        if not whatsapp_bot_service.is_ready():
            return make_response(
                jsonify(
                    {
                        "status": "error",
                        "message": (
                            "WhatsApp is not paired or not connected. Pair the device "
                            "first from the /whatsapp page in OpenAlgo before sending."
                        ),
                    }
                ),
                409,  # Conflict: server is in the wrong state for this operation
            )

        message = data.get("message")
        if message and len(message) > 4096:
            return make_response(
                jsonify({"status": "error", "message": "Message must not exceed 4096 characters"}),
                400,
            )

        raw_image_path = data.get("image_path")
        raw_document_path = data.get("document_path")
        caption = data.get("caption")
        filename = data.get("filename")
        # Default to synchronous delivery so the trader sees a real success /
        # failure report instead of a "Queued" lie. wars.send blocks <1s on
        # a connected session, well inside the 30s alert pool timeout. Set
        # wait_for_delivery=false explicitly for true fire-and-forget.
        wait_for_delivery = bool(data.get("wait_for_delivery", True))

        if not message and not raw_image_path and not raw_document_path:
            return make_response(
                jsonify(
                    {
                        "status": "error",
                        "message": "Provide at least one of: message, image_path, document_path",
                    }
                ),
                400,
            )

        # Resolve attachment paths against the configured allowlist. A bare
        # 400 with a generic message — we deliberately do NOT echo back why
        # a path was rejected (path leakage), nor the original path.
        image_path = validate_attachment_path(raw_image_path)
        document_path = validate_attachment_path(raw_document_path)
        if raw_image_path and not image_path:
            return make_response(
                jsonify({"status": "error", "message": "image_path is not allowed"}), 400
            )
        if raw_document_path and not document_path:
            return make_response(
                jsonify({"status": "error", "message": "document_path is not allowed"}), 400
            )

        targets: list[str] = []
        if data.get("self"):
            targets = []  # empty -> send_sync uses own_jid
        elif data.get("phones"):
            raw = data["phones"]
            if not isinstance(raw, list):
                return make_response(
                    jsonify({"status": "error", "message": "'phones' must be a list"}), 400
                )
            for p in raw[:5]:
                digits = normalize_phone(str(p))
                if digits:
                    targets.append(phone_to_jid(digits))
            if not targets:
                return make_response(
                    jsonify({"status": "error", "message": "No valid phones in list"}), 400
                )
        elif data.get("phone"):
            digits = normalize_phone(data["phone"])
            if not digits:
                return make_response(
                    jsonify({"status": "error", "message": "Invalid phone number"}), 400
                )
            targets = [phone_to_jid(digits)]
        elif data.get("username"):
            user = get_whatsapp_user_by_username(data["username"])
            if not user:
                return make_response(
                    jsonify(
                        {
                            "status": "error",
                            "message": "Username not found or not linked to WhatsApp",
                        }
                    ),
                    404,
                )
            targets = [user["whatsapp_jid"]]
        else:
            return make_response(
                jsonify(
                    {
                        "status": "error",
                        "message": (
                            "Specify one of: 'self', 'username', 'phone', or 'phones'"
                        ),
                    }
                ),
                400,
            )

        if wait_for_delivery:
            report = whatsapp_bot_service.send_sync(
                to=targets if targets else None,
                text=message,
                image=image_path,
                document=document_path,
                caption=caption,
                filename=filename,
            )
            return make_response(
                jsonify(
                    {
                        "status": "success",
                        "message": (
                            f"Delivered to {len(report['sent'])}, failed {len(report['failed'])}"
                        ),
                        "data": report,
                    }
                ),
                200,
            )

        recipients = targets or [""]  # empty -> self in send_alert_sync
        for jid in recipients:
            alert_executor.submit(
                whatsapp_alert_service.send_alert_sync,
                jid,
                message or caption or "",
                image_path,
                document_path,
            )
        return make_response(
            jsonify(
                {
                    "status": "success",
                    "message": f"Queued for {len(recipients)} recipient(s)",
                    "queued": len(recipients),
                }
            ),
            200,
        )

```
