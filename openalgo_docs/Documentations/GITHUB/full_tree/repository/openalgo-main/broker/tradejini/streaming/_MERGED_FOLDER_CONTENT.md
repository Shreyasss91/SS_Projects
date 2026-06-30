# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\tradejini\streaming



---

# FILE: broker\tradejini\streaming\__init__.py

```py
"""
Tradejini WebSocket streaming module
"""

from .tradejini_adapter import TradejiniWebSocketAdapter
from .tradejini_mapping import TradejiniCapabilityRegistry, TradejiniExchangeMapper

__all__ = ["TradejiniWebSocketAdapter", "TradejiniExchangeMapper", "TradejiniCapabilityRegistry"]

```


---

# FILE: broker\tradejini\streaming\nxtradstream.py

```py
import errno
import json
import os
import re
import struct
import sys
import threading
import time
import zlib
from datetime import datetime

import websocket

from utils.logging import get_logger

logger = get_logger(__name__)


CURRENT_VERSION = 1
PKG_VERSION = "1.0.2"


def commafmt(value, precision=2):
    v = str(round(float(value), 2))
    parts = v.split(".")
    parts[0] = re.sub(r"\B(?=(\d{3})+(?!\d))", ",", parts[0])
    return ".".join(parts)


def divide(value, divisor=100.0):
    return value / float(divisor)


def datefmt(value):
    if value is None:
        return value
    date_time = datetime.fromtimestamp(value)
    return str(date_time)


L1 = "L1"
L5 = "L5"
OHLC = "OHLC"
AUTH = "auth"
MARKET_STATUS = "marketStatus"
EVENTS = "EVENTS"
PING = "PING"
GREEKS = "greeks"

SEG_INFO = {
    1: {"exchSeg": "NSE", "precision": 2, "divisor": 100.0},
    2: {"exchSeg": "BSE", "precision": 2, "divisor": 100.0},
    3: {"exchSeg": "NFO", "precision": 2, "divisor": 100.0},
    4: {"exchSeg": "BFO", "precision": 2, "divisor": 100.0},
    5: {"exchSeg": "CDS", "precision": 4, "divisor": 10000000.0},
    6: {"exchSeg": "BCD", "precision": 4, "divisor": 10000.0},
    7: {"exchSeg": "MCD", "precision": 4, "divisor": 10000.0},
    8: {"exchSeg": "MCX", "precision": 2, "divisor": 100.0},
    9: {"exchSeg": "NCO", "precision": 2, "divisor": 10000.0},
    10: {"exchSeg": "BCO", "precision": 2, "divisor": 10000.0},
}
PKT_TYPE = {10: L1, 11: L5, 12: OHLC, 13: AUTH, 14: MARKET_STATUS, 15: EVENTS, 16: PING, 17: GREEKS}

# spec format :: 67: {  "struct":"d", "key": "ltp", "len": 8, "fmt": lambda v, p :  commafmt(v, p) },
DEFAULT_PKT_INFO = {
    "PKT_SPEC": {
        10: {
            26: {"struct": "B", "key": "exchSeg", "len": 1},
            27: {"struct": "i", "key": "token", "len": 4},
            28: {"struct    ": "B", "key": "precision", "len": 1},
            29: {"struct": "i", "key": "ltp", "len": 4, "fmt": lambda v, d: divide(v, d)},
            30: {"struct": "i", "key": "open", "len": 4, "fmt": lambda v, d: divide(v, d)},
            31: {"struct": "i", "key": "high", "len": 4, "fmt": lambda v, d: divide(v, d)},
            32: {"struct": "i", "key": "low", "len": 4, "fmt": lambda v, d: divide(v, d)},
            33: {"struct": "i", "key": "close", "len": 4, "fmt": lambda v, d: divide(v, d)},
            34: {"struct": "i", "key": "chng", "len": 4, "fmt": lambda v, d: divide(v, d)},
            35: {"struct": "i", "key": "chngPer", "len": 4, "fmt": lambda v, d: divide(v)},
            36: {"struct": "i", "key": "atp", "len": 4, "fmt": lambda v, d: divide(v, d)},
            37: {"struct": "i", "key": "yHigh", "len": 4, "fmt": lambda v, d: divide(v, d)},
            38: {"struct": "i", "key": "yLow", "len": 4, "fmt": lambda v, d: divide(v, d)},
            39: {"struct": "<I", "key": "ltq", "len": 4},
            40: {"struct": "<I", "key": "vol", "len": 4},
            41: {"struct": "d", "key": "ttv", "len": 8},
            42: {"struct": "i", "key": "ucl", "len": 4, "fmt": lambda v, d: divide(v, d)},
            43: {"struct": "i", "key": "lcl", "len": 4, "fmt": lambda v, d: divide(v, d)},
            44: {"struct": "<I", "key": "OI", "len": 4},
            45: {"struct": "i", "key": "OIChngPer", "len": 4, "fmt": lambda v, d: divide(v)},
            46: {"struct": "i", "key": "ltt", "len": 4, "fmt": lambda v: datefmt(v)},
            49: {"struct": "i", "key": "bidPrice", "len": 4, "fmt": lambda v, d: divide(v, d)},
            50: {"struct": "<I", "key": "qty", "len": 4},
            51: {"struct": "<I", "key": "no", "len": 4},
            52: {"struct": "i", "key": "askPrice", "len": 4, "fmt": lambda v, d: divide(v, d)},
            53: {"struct": "<I", "key": "qty", "len": 4},
            54: {"struct": "<I", "key": "no", "len": 4},
            55: {"struct": "B", "key": "nDepth", "len": 1},
            56: {"struct": "H", "key": "nLen", "len": 2},
            58: {"struct": "<I", "key": "prevOI", "len": 4},
            59: {"struct": "<I", "key": "dayHighOI", "len": 4},
            60: {"struct": "<I", "key": "dayLowOI", "len": 4},
            70: {"struct": "i", "key": "spotPrice", "len": 4, "fmt": lambda v, d: divide(v, d)},
            71: {"struct": "i", "key": "dayClose", "len": 4, "fmt": lambda v, d: divide(v, d)},
            74: {"struct": "i", "key": "vwap", "len": 4, "fmt": lambda v, d: divide(v, d)},
        },
        11: {
            26: {"struct": "B", "key": "exchSeg", "len": 1},
            27: {"struct": "i", "key": "token", "len": 4},
            28: {"struct": "B", "key": "precision", "len": 1},
            47: {"struct": "<I", "key": "totBuyQty", "len": 4},
            48: {"struct": "<I", "key": "totSellQty", "len": 4},
            49: {"struct": "i", "key": "price", "len": 4, "fmt": lambda v, d: divide(v, d)},
            50: {"struct": "<I", "key": "qty", "len": 4},
            51: {"struct": "<I", "key": "no", "len": 4},
            52: {"struct": "i", "key": "price", "len": 4, "fmt": lambda v, d: divide(v, d)},
            53: {"struct": "<I", "key": "qty", "len": 4},
            54: {"struct": "<I", "key": "no", "len": 4},
            55: {"struct": "B", "key": "nDepth", "len": 1},
        },
        12: {
            26: {"struct": "B", "key": "exchSeg", "len": 1},
            27: {"struct": "i", "key": "token", "len": 4},
            28: {"struct": "B", "key": "precision", "len": 1},
            30: {"struct": "i", "key": "open", "len": 4, "fmt": lambda v, d: divide(v, d)},
            31: {"struct": "i", "key": "high", "len": 4, "fmt": lambda v, d: divide(v, d)},
            32: {"struct": "i", "key": "low", "len": 4, "fmt": lambda v, d: divide(v, d)},
            33: {"struct": "i", "key": "close", "len": 4, "fmt": lambda v, d: divide(v, d)},
            40: {"struct": "<I", "key": "vol", "len": 4},
            46: {"struct": "i", "key": "time", "len": 4, "fmt": lambda v: datefmt(v)},
            74: {"struct": "i", "key": "vwap", "len": 4, "fmt": lambda v, d: divide(v, d)},
            75: {"struct": "string", "key": "type", "len": 4},
            76: {"struct": "<I", "key": "minuteOi", "len": 4},
        },
        13: {
            25: {"struct": "B", "key": "auth_status", "len": 1},
        },
        14: {
            56: {"struct": "H", "key": "nLen", "len": 2},
            26: {"struct": "B", "key": "exchSeg", "len": 1},
            57: {"struct": "B", "key": "marketStatus", "len": 1},
        },
        15: {
            56: {"struct": "H", "key": "nLen", "len": 2},
            # length will be dynamiccaly altered from message
            61: {"struct": "string", "key": "message", "len": 100},
        },
        16: {
            62: {"struct": "B", "key": "pong", "len": 1},
        },
        17: {
            26: {"struct": "B", "key": "exchSeg", "len": 1},
            27: {"struct": "i", "key": "token", "len": 4},
            63: {"struct": "d", "key": "itm", "len": 8},
            64: {"struct": "d", "key": "iv", "len": 8},
            65: {"struct": "d", "key": "delta", "len": 8},
            66: {"struct": "d", "key": "gamma", "len": 8},
            67: {"struct": "d", "key": "theta", "len": 8},
            68: {"struct": "d", "key": "rho", "len": 8},
            69: {"struct": "d", "key": "vega", "len": 8},
            72: {"struct": "d", "key": "highiv", "len": 8},
            73: {"struct": "d", "key": "lowiv", "len": 8},
        },
    },
    "BID_ASK_OBJ_LEN": 3,
    "MARKET_STATUS_OBJ_LEN": 2,
}


class NxtradStream:
    def __init__(self, url, version="3.1", stream_cb=None, connect_cb=None):
        self.ws = None
        self.isConnected = False

        self.stream_cb = stream_cb
        self.connect_cb = connect_cb

        self.host = "wss://" + url + "/v2.1/stream"

        self.L1_dict = {}
        self.token = ""
        self.version = version

    def connect(self, token):
        self.token = token
        self.__tryConnect()

    def reconnect(self):
        if not self.token:
            sys.exit("Unable to connect auth token is empty")
        if self.isConnected:
            logger.info("Socket already connected")
            return
        logger.info("Reconnecting...")
        self.__tryConnect()

    def __tryConnect(self):
        url = self.host + "?token=" + self.token + "&version=" + self.version
        # websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp(
            url,
            on_open=self.__on_open,
            on_message=self.__on_message,
            on_error=self.__on_error,
            on_close=self.__on_close,
        )

        self._ws_thread = threading.Thread(target=self.__task)
        self._ws_thread.start()

    def subscribeEvents(self, type):
        req = {}
        req["type"] = "event"
        req["action"] = "sub"

        req["events"] = type

        return self.__send_data(req)

    def sendPing(self):
        req = {}
        req["type"] = "PING"
        return self.__send_data(req)

    def subscribeL1(self, tokens):
        req = {}
        req["type"] = "L1"
        req["action"] = "sub"

        _l = []
        for i in tokens:
            _l.append({"t": i})

        req["tokens"] = _l

        return self.__send_data(req)

    def subscribeL1SnapShot(self, tokens):
        req = {}
        req["type"] = "L1S"
        req["action"] = "sub"

        _l = []
        for i in tokens:
            _l.append({"t": i})

        req["tokens"] = _l

        return self.__send_data(req)

    def subscribeL2(self, tokens):
        req = {}
        req["type"] = "L5"
        req["action"] = "sub"

        _l = []
        for i in tokens:
            _l.append({"t": i})

        req["tokens"] = _l

        return self.__send_data(req)

    def subscribeL2SnapShot(self, tokens):
        req = {}
        req["type"] = "L5S"
        req["action"] = "sub"

        _l = []
        for i in tokens:
            _l.append({"t": i})

        req["tokens"] = _l

        return self.__send_data(req)

    def subscribeGreeks(self, tokens):
        req = {}
        req["type"] = "greeks"
        req["action"] = "sub"

        _l = []
        for i in tokens:
            _l.append({"t": i})

        req["tokens"] = _l

        return self.__send_data(req)

    def subscribeGreeksSnapShot(self, tokens):
        req = {}
        req["type"] = "greeks-snapshot"
        req["action"] = "sub"

        _l = []
        for i in tokens:
            _l.append({"t": i})

        req["tokens"] = _l

        return self.__send_data(req)

    def unsubscribeEvents(self):
        req = {}
        req["type"] = "event"
        req["action"] = "unsub"

        return self.__send_data(req)

    def unsubscribeL1(self):
        self.L1_dict.clear()

        req = {}
        req["type"] = "L1"
        req["action"] = "unsub"

        return self.__send_data(req)

    def unsubscribeL2(self):
        req = {}
        req["type"] = "L5"
        req["action"] = "unsub"

        return self.__send_data(req)

    def unsubscribeGreeks(self):
        req = {}
        req["type"] = "greeks"
        req["action"] = "unsub"

        return self.__send_data(req)

    def subscribeOHLC(self, tokens, interval):
        req = {}
        req["type"] = "OHLC"
        req["action"] = "sub"

        _l = []
        for i in tokens:
            _l.append({"t": i})

        req["tokens"] = _l
        req["chartInterval"] = interval

        return self.__send_data(req)

    def unsubscribeOHLC(self, interval):
        req = {}
        req["type"] = "OHLC"
        req["action"] = "unsub"
        req["chartInterval"] = interval

        return self.__send_data(req)

    def disconnect(self):
        self.isConnected = False
        try:
            self.ws.close()
        except Exception:
            pass

    def isConnected(self):
        return self.isConnected

    def __send_data(self, req):
        if not self.isConnected:
            return False

        r = json.dumps(req)
        # logger.info(f"{r}")
        self.ws.send(r + "\n")
        return True

    def __frame_from_spec(self, spec, data, idx):
        binaryKey = spec["struct"]
        binaryLen = spec["len"]

        parsed = None
        if binaryKey == "string":
            parsed = self.__ab2str(data, idx, binaryLen)
        else:
            parsed = struct.unpack(binaryKey, data[idx : idx + binaryLen])[0]

        return parsed

    def __format_values(self, divisor, raw_data, jData):
        for key, value in raw_data.items():
            spec = value[0]
            framed = value[1]
            jData[spec["key"]] = spec["fmt"](framed, divisor) if "fmt" in spec else framed

    def __ab2str(self, buf, offset, length):
        unpacklen = str(length) + "s"
        v = struct.unpack(unpacklen, buf[offset : offset + length])
        res = v[0].rstrip(b"\x00").decode("utf_8")
        return res

    def __onsinglePacket(self, data, data_len):
        pktType = struct.unpack("b", data[2:3])[0]
        pktSpec = DEFAULT_PKT_INFO["PKT_SPEC"]
        if pktType not in pktSpec:
            logger.debug(f"Unknown PktType : {pktType}")
            return

        packetType = PKT_TYPE[pktType]
        quoteSpec = pktSpec[pktType]
        jData = None
        if packetType == L1:
            jData = self.__decodeL1PKT(quoteSpec, data_len, data)
        elif packetType == L5:
            jData = self.__decodeL2PKT(quoteSpec, data_len, data)
        elif packetType == OHLC:
            jData = self.__decodeOHLC(quoteSpec, data_len, data)
        elif packetType == MARKET_STATUS:
            jData = self.__decodeMarketStatus(quoteSpec, data_len, data)
        elif packetType == EVENTS:
            jData = self.__decodeMessage(quoteSpec, data_len, data)
        elif packetType == PING:
            jData = self.__decodeStatus(quoteSpec, data_len, data)
        elif packetType == GREEKS:
            jData = self.__decodeL1PKT(quoteSpec, data_len, data)

        if jData is not None:
            jData["msgType"] = packetType

            if packetType == L1:
                t = jData["symbol"]
                if t in self.L1_dict:
                    _cache_d = self.L1_dict[t]
                    _cache_d.update(jData)
                    jData = _cache_d
                self.L1_dict[t] = jData

            self._callback(self.stream_cb, self, jData)

    def __decodeL1PKT(self, pktSpec, data_len, data):
        jData = {}
        raw_data = {}
        exchange_info = None
        divisor = 100.0
        precision = 2
        idx = 3
        while idx < data_len:
            pktKey = struct.unpack("B", data[idx : idx + 1])
            idx += 1
            spec = pktSpec[pktKey[0]]
            framed = self.__frame_from_spec(spec, data, idx)
            if spec["key"] == "exchSeg":
                exchange_info = SEG_INFO[framed]
                precision = exchange_info["precision"]
                divisor = exchange_info["divisor"]
                jData[spec["key"]] = exchange_info["exchSeg"]
            elif spec["key"] == "ltt":
                jData[spec["key"]] = spec["fmt"](framed) if "fmt" in spec else framed
            else:
                raw_data[spec["key"]] = (spec, framed)

            idx += spec["len"]

        if exchange_info is not None:
            self.__format_values(divisor, raw_data, jData)

        jData["symbol"] = str(jData["token"]) + "_" + jData["exchSeg"]
        jData["precision"] = precision

        return jData

    def __decodeL2PKT(self, pktSpec, data_len, data):
        exchange_info = None
        raw_data = {}
        divisor = 100.0
        precision = 2
        noLevel = 0
        bids = []
        asks = []
        list = None
        lObj = {}
        jData = {}
        idx = 3
        while idx < data_len:
            pktKey = struct.unpack("B", data[idx : idx + 1])
            idx += 1
            spec = pktSpec[pktKey[0]]
            framed = self.__frame_from_spec(spec, data, idx)
            if spec["key"] == "nDepth":
                noLevel = framed
                list = bids
            elif spec["key"] == "exchSeg":
                exchange_info = SEG_INFO[framed]
                precision = exchange_info["precision"]
                divisor = exchange_info["divisor"]
                jData[spec["key"]] = exchange_info["exchSeg"]
            else:
                if list is not None:
                    lObj[spec["key"]] = spec["fmt"](framed, divisor) if "fmt" in spec else framed
                else:
                    raw_data[spec["key"]] = (spec, framed)

            if list is not None:
                if len(lObj) == DEFAULT_PKT_INFO["BID_ASK_OBJ_LEN"]:
                    list.append(lObj)
                    lObj = {}
                if noLevel == len(list):
                    list = asks

            idx += spec["len"]

        if exchange_info is not None:
            self.__format_values(divisor, raw_data, jData)

        jData["bid"] = bids
        jData["ask"] = asks
        jData["precision"] = precision
        jData["symbol"] = str(jData["token"]) + "_" + jData["exchSeg"]
        return jData

    def __decodeOHLC(self, pktSpec, data_len, data):
        jData = {}
        raw_data = {}
        exchange_info = None
        divisor = 100.0
        precision = 2
        idx = 3
        while idx < data_len:
            pktKey = struct.unpack("B", data[idx : idx + 1])
            idx += 1
            spec = pktSpec[pktKey[0]]
            framed = self.__frame_from_spec(spec, data, idx)
            if spec["key"] == "exchSeg":
                exchange_info = SEG_INFO[framed]
                precision = exchange_info["precision"]
                divisor = exchange_info["divisor"]
                jData[spec["key"]] = exchange_info["exchSeg"]
            elif spec["key"] == "time":
                jData[spec["key"]] = spec["fmt"](framed) if "fmt" in spec else framed
            else:
                raw_data[spec["key"]] = (spec, framed)

            idx += spec["len"]

        if exchange_info is not None:
            self.__format_values(divisor, raw_data, jData)

        jData["symbol"] = str(jData["token"]) + "_" + jData["exchSeg"]
        jData["precision"] = precision

        return jData

    def __decodeMarketStatus(self, pktSpec, data_len, data):
        lObj = {}
        jData = {}
        idx = 3
        noOfLen = 0
        exchange_info = None
        list = None
        while idx < data_len:
            pktKey = struct.unpack("B", data[idx : idx + 1])
            idx += 1
            spec = pktSpec[pktKey[0]]
            framed = self.__frame_from_spec(spec, data, idx)
            if spec["key"] == "nLen":
                noOfLen = framed
                list = []
            else:
                lObj[spec["key"]] = framed
                if spec["key"] == "exchSeg":
                    exchange_info = SEG_INFO[framed]
                    lObj[spec["key"]] = exchange_info["exchSeg"]

            if list is not None:
                if len(lObj) == DEFAULT_PKT_INFO["MARKET_STATUS_OBJ_LEN"]:
                    list.append(lObj)
                    lObj = {}

            idx += spec["len"]

        jData["status"] = list
        return jData

    def __decodeMessage(self, pktSpec, data_len, data):
        jData = {}
        idx = 3
        noOfLen = 0
        while idx < data_len:
            pktKey = struct.unpack("B", data[idx : idx + 1])
            idx += 1
            spec = pktSpec[pktKey[0]]
            framed = self.__frame_from_spec(spec, data, idx)
            if spec["key"] == "nLen":
                noOfLen = framed
                pktSpec[61]["len"] = noOfLen  # Setttng message len from here
            else:
                jData[spec["key"]] = framed

            idx += spec["len"]

        return jData

    def __decodeStatus(self, pktSpec, data_len, data):
        jData = {}
        idx = 3
        while idx < data_len:
            pktKey = struct.unpack("B", data[idx : idx + 1])
            idx += 1
            spec = pktSpec[pktKey[0]]
            framed = self.__frame_from_spec(spec, data, idx)
            jData[spec["key"]] = spec["fmt"](framed) if "fmt" in spec else framed
            idx += spec["len"]

        return jData

    def __decompressZLib(self, c_data):
        dc_data = zlib.decompress(c_data)
        return dc_data

    def __on_message(self, ws, message):
        totalRecivedLen = struct.unpack("i", message[:4])[0]
        version = struct.unpack("b", message[4:5])[0]
        if version != CURRENT_VERSION:
            logger.debug("Kindly download and use the updated SDK.")
            return

        compressionAlgo = struct.unpack("b", message[5:6])[0]
        dc_data = message[6:]
        if compressionAlgo == 100:
            dc_data = self.__decompressZLib(message[6:])

        totalRecivedLen = len(dc_data)
        bufferIndex = 0
        while bufferIndex < totalRecivedLen:
            pktLen = struct.unpack("h", dc_data[bufferIndex : (bufferIndex + 2)])[0]
            if pktLen <= 0:
                logger.info(f"Packet Length is wrong exiting the loop{str(pktLen)}")
                break

            self.__onsinglePacket(dc_data[bufferIndex : (bufferIndex + pktLen)], pktLen)
            bufferIndex += pktLen

    def __on_error(self, ws, error):
        self.isConnected = False
        self._callback(self.connect_cb, self, {"s": "error", "reason": error})

    def __on_close(self, ws, close_status_code, close_msg):
        self.isConnected = False
        self._callback(
            self.connect_cb, self, {"s": "closed", "code": close_status_code, "reason": close_msg}
        )

    def __on_open(self, ws):
        self.isConnected = True
        self._callback(self.connect_cb, self, {"s": "connected"})

    def __task(self):
        self.ws.run_forever()

    def _callback(self, callback, *args):
        if callback:
            try:
                callback(*args)
            except Exception as e:
                logger.info(f"Error in Calling callback {callback}: {e}")

```


---

# FILE: broker\tradejini\streaming\tradejini_adapter.py

```py
import json
import logging
import os
import sys
import threading
import time
from typing import Any, Dict, List, Optional

# Add parent directory to path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../"))

from database.auth_db import get_auth_token
from database.token_db import get_token
from websocket_proxy.base_adapter import BaseBrokerWebSocketAdapter
from websocket_proxy.mapping import SymbolMapper

from .nxtradstream import NxtradStream
from .tradejini_mapping import TradejiniCapabilityRegistry, TradejiniExchangeMapper


class TradejiniWebSocketAdapter(BaseBrokerWebSocketAdapter):
    """Tradejini-specific implementation of the WebSocket adapter"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("tradejini_websocket")
        self.ws_client = None
        self.user_id = None
        self.broker_name = "tradejini"
        self.reconnect_delay = 5  # Initial delay in seconds
        self.max_reconnect_delay = 60  # Maximum delay in seconds
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.running = False
        self.lock = threading.Lock()
        self.ws_url = None
        self._connect_thread = None

    def initialize(
        self, broker_name: str, user_id: str, auth_data: dict[str, str] | None = None
    ) -> None:
        """
        Initialize connection with Tradejini WebSocket API

        Args:
            broker_name: Name of the broker (always 'tradejini' in this case)
            user_id: Client ID/user ID
            auth_data: If provided, use these credentials instead of fetching from DB

        Raises:
            ValueError: If required authentication tokens are not found
        """
        self.user_id = user_id
        self.broker_name = broker_name

        # Get tokens from database if not provided
        if not auth_data:
            # Fetch authentication tokens from database
            # For Tradejini, the access token is used for both API and WebSocket
            auth_token = get_auth_token(user_id)

            if not auth_token:
                self.logger.error(f"No authentication token found for user {user_id}")
                raise ValueError(f"No authentication token found for user {user_id}")

            # Get API key from environment for Tradejini
            api_key = os.getenv("BROKER_API_SECRET", "")

            # Format token for Tradejini WebSocket (api_key:access_token)
            if api_key and ":" not in auth_token:
                ws_token = f"{api_key}:{auth_token}"
            else:
                ws_token = auth_token

            ws_url = "api.tradejini.com"
        else:
            # Use provided tokens
            auth_token = auth_data.get("auth_token")
            feed_token = auth_data.get(
                "feed_token", auth_token
            )  # Use auth_token if feed_token not provided
            ws_url = auth_data.get("ws_url", "api.tradejini.com")

            if not auth_token:
                self.logger.error("Missing required authentication data")
                raise ValueError("Missing required authentication data")

            # Get API key from environment or auth_data for Tradejini
            api_key = auth_data.get("api_key", os.getenv("BROKER_API_SECRET", ""))

            # Format token for Tradejini WebSocket (api_key:access_token)
            if api_key and ":" not in auth_token:
                ws_token = f"{api_key}:{auth_token}"
            else:
                ws_token = auth_token

        # Store WebSocket URL
        self.ws_url = ws_url

        # Create NxtradStream instance
        self.ws_client = NxtradStream(
            url=ws_url, version="3.1", stream_cb=self._on_data, connect_cb=self._on_connection_event
        )

        # Store the token for connection
        self.ws_token = ws_token
        self.running = True

    def connect(self) -> None:
        """Establish connection to Tradejini WebSocket"""
        if not self.ws_client:
            self.logger.error("WebSocket client not initialized. Call initialize() first.")
            return

        self._connect_thread = threading.Thread(target=self._connect_with_retry, daemon=True)
        self._connect_thread.start()

    def _connect_with_retry(self) -> None:
        """Connect to Tradejini WebSocket with retry logic"""
        while self.running and self.reconnect_attempts < self.max_reconnect_attempts:
            try:
                self.logger.info(
                    f"Connecting to Tradejini WebSocket (attempt {self.reconnect_attempts + 1})"
                )
                self.ws_client.connect(self.ws_token)
                self.reconnect_attempts = 0  # Reset attempts on successful connection
                break

            except Exception as e:
                self.reconnect_attempts += 1
                delay = min(
                    self.reconnect_delay * (2**self.reconnect_attempts), self.max_reconnect_delay
                )
                self.logger.error(f"Connection failed: {e}. Retrying in {delay} seconds...")
                time.sleep(delay)

        if self.reconnect_attempts >= self.max_reconnect_attempts:
            self.logger.error("Max reconnection attempts reached. Giving up.")

    def disconnect(self) -> None:
        """Disconnect from Tradejini WebSocket"""
        self.running = False
        if hasattr(self, "ws_client") and self.ws_client:
            self.ws_client.disconnect()

        # Clean up ZeroMQ resources
        self.cleanup_zmq()

    def subscribe(
        self, symbol: str, exchange: str, mode: int = 2, depth_level: int = 5
    ) -> dict[str, Any]:
        """
        Subscribe to market data with Tradejini-specific implementation

        Args:
            symbol: Trading symbol (e.g., 'RELIANCE')
            exchange: Exchange code (e.g., 'NSE', 'BSE', 'NFO')
            mode: Subscription mode - 1:LTP, 2:Quote, 3:Depth
            depth_level: Market depth level (5 for Tradejini)

        Returns:
            Dict: Response with status and error message if applicable
        """
        # Validate mode
        if mode not in [1, 2, 3]:
            return self._create_error_response(
                "INVALID_MODE", f"Invalid mode {mode}. Must be 1 (LTP), 2 (Quote), or 3 (Depth)"
            )

        # If depth mode, check if supported depth level
        if mode == 3 and depth_level not in [5]:
            return self._create_error_response(
                "INVALID_DEPTH", f"Invalid depth level {depth_level}. Must be 5"
            )

        # Map symbol to token using symbol mapper
        token_info = SymbolMapper.get_token_from_symbol(symbol, exchange)
        if not token_info:
            return self._create_error_response(
                "SYMBOL_NOT_FOUND", f"Symbol {symbol} not found for exchange {exchange}"
            )

        token = token_info["token"]
        brexchange = token_info["brexchange"]

        # Check if the requested depth level is supported for this exchange
        is_fallback = False
        actual_depth = depth_level

        if mode == 3:  # Depth mode
            if not TradejiniCapabilityRegistry.is_depth_level_supported(exchange, depth_level):
                # If requested depth is not supported, use the highest available
                actual_depth = TradejiniCapabilityRegistry.get_fallback_depth_level(
                    exchange, depth_level
                )
                is_fallback = True

                self.logger.info(
                    f"Depth level {depth_level} not supported for {exchange}, "
                    f"using {actual_depth} instead"
                )

        # Generate unique correlation ID
        correlation_id = f"{symbol}_{exchange}_{mode}"
        if mode == 3:
            correlation_id = f"{correlation_id}_{depth_level}"

        # Store subscription for reconnection
        with self.lock:
            self.subscriptions[correlation_id] = {
                "symbol": symbol,
                "exchange": exchange,
                "brexchange": brexchange,
                "token": token,
                "mode": mode,
                "depth_level": depth_level,
                "actual_depth": actual_depth,
                "is_fallback": is_fallback,
            }

        # Subscribe if connected
        if self.connected and self.ws_client:
            try:
                # Create token string with exchange segment
                token_str = f"{token}_{brexchange}"

                self.logger.info(
                    f"Subscribing to {symbol} with token {token} on {brexchange} (token_str: {token_str})"
                )

                # Subscribe based on mode
                if mode == 1:
                    # LTP mode - use L1 subscription
                    self.ws_client.subscribeL1([token_str])
                elif mode == 2:
                    # Quote mode - use L1 subscription (full quote)
                    self.ws_client.subscribeL1([token_str])
                elif mode == 3:
                    # Depth mode - use L5 subscription (5 level depth)
                    self.ws_client.subscribeL2([token_str])

            except Exception as e:
                self.logger.error(f"Error subscribing to {symbol}.{exchange}: {e}")
                return self._create_error_response("SUBSCRIPTION_ERROR", str(e))

        # Return success with capability info
        return self._create_success_response(
            "Subscription requested"
            if not is_fallback
            else f"Using depth level {actual_depth} instead of requested {depth_level}",
            symbol=symbol,
            exchange=exchange,
            mode=mode,
            requested_depth=depth_level,
            actual_depth=actual_depth,
            is_fallback=is_fallback,
        )

    def unsubscribe(self, symbol: str, exchange: str, mode: int = 2) -> dict[str, Any]:
        """
        Unsubscribe from market data

        Args:
            symbol: Trading symbol
            exchange: Exchange code
            mode: Subscription mode

        Returns:
            Dict: Response with status
        """
        # Map symbol to token
        token_info = SymbolMapper.get_token_from_symbol(symbol, exchange)
        if not token_info:
            return self._create_error_response(
                "SYMBOL_NOT_FOUND", f"Symbol {symbol} not found for exchange {exchange}"
            )

        # Generate correlation ID
        correlation_id = f"{symbol}_{exchange}_{mode}"

        # Remove from subscriptions
        with self.lock:
            if correlation_id in self.subscriptions:
                del self.subscriptions[correlation_id]

        # Unsubscribe if connected
        if self.connected and self.ws_client:
            try:
                # Tradejini unsubscribes from all tokens for a given type
                if mode in [1, 2]:
                    self.ws_client.unsubscribeL1()
                elif mode == 3:
                    self.ws_client.unsubscribeL2()

            except Exception as e:
                self.logger.error(f"Error unsubscribing from {symbol}.{exchange}: {e}")
                return self._create_error_response("UNSUBSCRIPTION_ERROR", str(e))

        return self._create_success_response(
            f"Unsubscribed from {symbol}.{exchange}", symbol=symbol, exchange=exchange, mode=mode
        )

    def _on_connection_event(self, ws, message) -> None:
        """Callback for connection events"""
        status = message.get("s")

        if status == "connected":
            self.logger.info("Connected to Tradejini WebSocket")
            self.connected = True

            # Resubscribe to existing subscriptions if reconnecting
            with self.lock:
                for correlation_id, sub in self.subscriptions.items():
                    try:
                        token_str = f"{sub['token']}_{sub['brexchange']}"

                        self.logger.info(
                            f"Resubscribing to {sub['symbol']} with token {sub['token']} on {sub['brexchange']} (token_str: {token_str})"
                        )

                        if sub["mode"] in [1, 2]:
                            self.ws_client.subscribeL1([token_str])
                        elif sub["mode"] == 3:
                            self.ws_client.subscribeL2([token_str])

                        self.logger.info(
                            f"Resubscribed to {sub['symbol']}.{sub['exchange']} with correlation_id: {correlation_id}"
                        )
                    except Exception as e:
                        self.logger.error(
                            f"Error resubscribing to {sub['symbol']}.{sub['exchange']}: {e}"
                        )

        elif status == "error":
            self.logger.error(f"Tradejini WebSocket error: {message.get('reason')}")

        elif status == "closed":
            self.logger.info(f"Tradejini WebSocket connection closed: {message.get('reason')}")
            self.connected = False

            # Attempt to reconnect if we're still running
            if self.running:
                self._connect_thread = threading.Thread(target=self._connect_with_retry, daemon=True)
                self._connect_thread.start()

    def _on_data(self, ws, message) -> None:
        """Callback for market data from the WebSocket"""
        try:
            # Debug log the raw message data
            self.logger.debug(f"RAW TRADEJINI DATA: Type={type(message)}, Data={message}")

            # Extract message type
            msg_type = message.get("msgType")

            # Check for authentication message
            if msg_type == "auth":
                auth_status = message.get("auth_status")
                if auth_status == 1:
                    self.logger.info("Successfully authenticated with Tradejini WebSocket")
                else:
                    self.logger.error(f"Authentication failed with Tradejini WebSocket: {message}")
                return

            # Check for ping/pong messages
            if msg_type in ["PING", "pong"]:
                self.logger.debug(f"Received {msg_type} message")
                return

            # Check for event messages
            if msg_type == "EVENTS":
                self.logger.info(f"Received event message: {message.get('message', '')}")
                return

            if not msg_type:
                self.logger.warning(f"Received message without msgType: {message}")
                return

            # Extract symbol and exchange from the message
            symbol_str = message.get("symbol", "")
            if not symbol_str:
                self.logger.warning(f"Received message without symbol: {message}")
                return

            # Symbol format is "token_exchSeg" (e.g., "11536_NSE")
            parts = symbol_str.split("_")
            if len(parts) != 2:
                self.logger.warning(f"Invalid symbol format: {symbol_str}")
                return

            token = str(parts[0])  # Ensure token is string
            brexchange = parts[1]

            # Find ALL subscriptions that match this token
            matching_subscriptions = []
            with self.lock:
                for sub in self.subscriptions.values():
                    # Compare both as strings to ensure match
                    if str(sub["token"]) == token and sub["brexchange"] == brexchange:
                        matching_subscriptions.append(sub)

            if not matching_subscriptions:
                self.logger.info(
                    f"Received data for unsubscribed token: {token} on {brexchange}. Active subscriptions: {list(self.subscriptions.keys())}"
                )
                return

            # Process data for each matching subscription (different modes for same symbol)
            for subscription in matching_subscriptions:
                # Create topic for ZeroMQ
                symbol = subscription["symbol"]
                exchange = subscription["exchange"]
                subscription_mode = subscription["mode"]

                # Determine which data to send based on message type and subscription mode
                # L1 messages contain both LTP and Quote data
                # L5 messages contain depth data
                should_publish = False

                if msg_type == "L1":
                    # L1 data can be used for both LTP and Quote modes
                    if subscription_mode in [1, 2]:  # LTP or Quote
                        should_publish = True
                elif msg_type == "L5" or msg_type == "L2":
                    # L5/L2 data is for depth mode
                    if subscription_mode == 3:  # Depth
                        should_publish = True

                if not should_publish:
                    continue

                # Map subscription mode to topic string
                if subscription_mode == 1:
                    mode_str = "LTP"
                    actual_mode = 1
                elif subscription_mode == 2:
                    mode_str = "QUOTE"
                    actual_mode = 2
                elif subscription_mode == 3:
                    mode_str = "DEPTH"
                    actual_mode = 3
                else:
                    self.logger.warning(f"Unknown subscription mode: {subscription_mode}")
                    continue

                # Topic format: EXCHANGE_SYMBOL_MODE (like Angel adapter)
                topic = f"{exchange}_{symbol}_{mode_str}"

                # Normalize the data based on subscription mode
                market_data = self._normalize_market_data(message, actual_mode)

                # Add metadata
                market_data.update(
                    {
                        "symbol": symbol,
                        "exchange": exchange,
                        "mode": subscription_mode,
                        "timestamp": int(time.time() * 1000),  # Current timestamp in ms
                    }
                )

                # Log the market data we're sending
                self.logger.debug(f"Publishing to topic '{topic}': {market_data}")

                # Publish to ZeroMQ
                try:
                    self.publish_market_data(topic, market_data)
                    # Debug: Log that we've sent the data
                    self.logger.debug(
                        f"Data published successfully to ZeroMQ on port {self.zmq_port}"
                    )
                except Exception as zmq_error:
                    self.logger.error(f"Failed to publish to ZeroMQ: {zmq_error}")

        except Exception as e:
            self.logger.error(f"Error processing market data: {e}", exc_info=True)

    def _normalize_market_data(self, message, mode) -> dict[str, Any]:
        """
        Normalize broker-specific data format to a common format

        Args:
            message: The raw message from the broker
            mode: Subscription mode

        Returns:
            Dict: Normalized market data
        """
        if mode == 1:  # LTP mode
            return {
                "ltp": message.get("ltp", 0),
                "ltt": message.get("ltt", ""),  # Keep as string like depth mode
            }
        elif mode == 2:  # Quote mode
            result = {
                "ltp": message.get("ltp", 0),
                "ltt": message.get("ltt"),
                "volume": message.get("vol", 0),
                "open": message.get("open", 0),
                "high": message.get("high", 0),
                "low": message.get("low", 0),
                "close": message.get("close", 0),
                "last_quantity": message.get("ltq", 0),
                "average_price": message.get("atp", 0),
                "total_buy_quantity": message.get("totBuyQty", 0),
                "total_sell_quantity": message.get("totSellQty", 0),
                "oi": message.get("OI", 0),
                "change": message.get("chng", 0),
                "change_percent": message.get("chngPer", 0),
            }
            return result
        elif mode == 3:  # Depth mode
            result = {
                "ltp": message.get("ltp", 0),
                "ltt": message.get("ltt"),
                "volume": message.get("vol", 0),
                "open": message.get("open", 0),
                "high": message.get("high", 0),
                "low": message.get("low", 0),
                "close": message.get("close", 0),
                "oi": message.get("OI", 0),
                "upper_circuit": message.get("ucl", 0),
                "lower_circuit": message.get("lcl", 0),
                "total_buy_quantity": message.get("totBuyQty", 0),
                "total_sell_quantity": message.get("totSellQty", 0),
            }

            # Add depth data if available
            if "bid" in message and "ask" in message:
                result["depth"] = {
                    "buy": self._extract_depth_data(message.get("bid", [])),
                    "sell": self._extract_depth_data(message.get("ask", [])),
                }

            return result
        else:
            return {}

    def _extract_depth_data(self, depth_list) -> list[dict[str, Any]]:
        """
        Extract depth data from Tradejini's message format

        Args:
            depth_list: List of depth levels from the message

        Returns:
            List: List of depth levels with price, quantity, and orders
        """
        depth = []

        for level in depth_list:
            if isinstance(level, dict):
                depth.append(
                    {
                        "price": level.get("price", 0),
                        "quantity": level.get("qty", 0),
                        "orders": level.get("no", 0),
                    }
                )

        # If no depth data found, return empty levels as fallback
        if not depth:
            for i in range(5):  # Default to 5 empty levels
                depth.append({"price": 0.0, "quantity": 0, "orders": 0})

        return depth

```


---

# FILE: broker\tradejini\streaming\tradejini_mapping.py

```py
"""
Tradejini-specific exchange and capability mappings for WebSocket streaming
"""


class TradejiniExchangeMapper:
    """Maps exchange codes between OpenAlgo and Tradejini formats"""

    # Exchange mappings based on Tradejini's SEG_INFO
    EXCHANGE_MAP = {
        "NSE": "NSE",
        "BSE": "BSE",
        "NFO": "NFO",
        "BFO": "BFO",
        "CDS": "CDS",
        "BCD": "BCD",
        "MCD": "MCD",
        "MCX": "MCX",
        "NCO": "NCO",
        "BCO": "BCO",
    }

    # Exchange segment IDs used in Tradejini WebSocket
    EXCHANGE_SEGMENTS = {
        1: "NSE",
        2: "BSE",
        3: "NFO",
        4: "BFO",
        5: "CDS",
        6: "BCD",
        7: "MCD",
        8: "MCX",
        9: "NCO",
        10: "BCO",
    }

    # Reverse mapping
    SEGMENT_TO_ID = {v: k for k, v in EXCHANGE_SEGMENTS.items()}

    @classmethod
    def get_exchange_segment(cls, exchange_code: str) -> int:
        """
        Get Tradejini exchange segment ID from exchange code

        Args:
            exchange_code: Exchange code (e.g., 'NSE', 'BSE')

        Returns:
            int: Exchange segment ID for Tradejini
        """
        return cls.SEGMENT_TO_ID.get(exchange_code.upper(), 1)  # Default to NSE

    @classmethod
    def get_exchange_from_segment(cls, segment_id: int) -> str:
        """
        Get exchange code from Tradejini segment ID

        Args:
            segment_id: Tradejini exchange segment ID

        Returns:
            str: Exchange code
        """
        return cls.EXCHANGE_SEGMENTS.get(segment_id, "NSE")


class TradejiniCapabilityRegistry:
    """Registry for Tradejini-specific capabilities and limitations"""

    # Depth level support by exchange
    # Tradejini supports 5-level depth for all exchanges
    DEPTH_CAPABILITIES = {
        "NSE": {"supported_levels": [5], "default_level": 5, "max_level": 5},
        "BSE": {"supported_levels": [5], "default_level": 5, "max_level": 5},
        "NFO": {"supported_levels": [5], "default_level": 5, "max_level": 5},
        "BFO": {"supported_levels": [5], "default_level": 5, "max_level": 5},
        "MCX": {"supported_levels": [5], "default_level": 5, "max_level": 5},
        "CDS": {"supported_levels": [5], "default_level": 5, "max_level": 5},
        "BCD": {"supported_levels": [5], "default_level": 5, "max_level": 5},
        "MCD": {"supported_levels": [5], "default_level": 5, "max_level": 5},
        "NCO": {"supported_levels": [5], "default_level": 5, "max_level": 5},
        "BCO": {"supported_levels": [5], "default_level": 5, "max_level": 5},
    }

    # Mode capabilities
    MODE_CAPABILITIES = {
        "LTP": 1,  # Last Traded Price only
        "QUOTE": 2,  # Full quote with OHLC
        "DEPTH": 3,  # Market depth (5 levels)
    }

    @classmethod
    def is_depth_level_supported(cls, exchange: str, depth_level: int) -> bool:
        """
        Check if a specific depth level is supported for an exchange

        Args:
            exchange: Exchange code
            depth_level: Requested depth level

        Returns:
            bool: True if supported, False otherwise
        """
        exchange = exchange.upper()
        if exchange not in cls.DEPTH_CAPABILITIES:
            return False

        return depth_level in cls.DEPTH_CAPABILITIES[exchange]["supported_levels"]

    @classmethod
    def get_fallback_depth_level(cls, exchange: str, requested_level: int) -> int:
        """
        Get the appropriate fallback depth level if requested level is not supported

        Args:
            exchange: Exchange code
            requested_level: Originally requested depth level

        Returns:
            int: The fallback depth level to use
        """
        exchange = exchange.upper()

        # If exchange not found, default to 5
        if exchange not in cls.DEPTH_CAPABILITIES:
            return 5

        capabilities = cls.DEPTH_CAPABILITIES[exchange]

        # If requested level is supported, return it
        if requested_level in capabilities["supported_levels"]:
            return requested_level

        # Return the default level for this exchange
        return capabilities["default_level"]

    @classmethod
    def get_max_depth_level(cls, exchange: str) -> int:
        """
        Get the maximum supported depth level for an exchange

        Args:
            exchange: Exchange code

        Returns:
            int: Maximum depth level
        """
        exchange = exchange.upper()

        if exchange not in cls.DEPTH_CAPABILITIES:
            return 5

        return cls.DEPTH_CAPABILITIES[exchange]["max_level"]

    @classmethod
    def is_mode_supported(cls, mode_name: str) -> bool:
        """
        Check if a mode is supported

        Args:
            mode_name: Mode name (e.g., 'LTP', 'QUOTE', 'DEPTH')

        Returns:
            bool: True if supported
        """
        return mode_name.upper() in cls.MODE_CAPABILITIES

    @classmethod
    def get_mode_value(cls, mode_name: str) -> int:
        """
        Get the numeric value for a mode

        Args:
            mode_name: Mode name

        Returns:
            int: Mode value or None if not supported
        """
        return cls.MODE_CAPABILITIES.get(mode_name.upper())

```
