# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\kotak\streaming



---

# FILE: broker\kotak\streaming\__init__.py

```py
"""
Kotak WebSocket streaming integration for OpenAlgo.
Exposes the high-level adapter and core websocket client.
"""

from .kotak_adapter import KotakWebSocketAdapter
from .kotak_websocket import KotakWebSocket

__all__ = ["KotakWebSocketAdapter", "KotakWebSocket"]

```


---

# FILE: broker\kotak\streaming\HSWebSocketLib.py

```py
import datetime
import json

import websocket

from utils.logging import get_logger

logger = get_logger(__name__)


# from neo_api_client.logger import logger

isEncyptOut = False
isEncyptIn = True

MAX_SCRIPS = 100
FieldTypes = {"FLOAT32": 1, "LONG": 2, "DATE": 3, "STRING": 4}
TRASH_VAL = -2147483648
STRING_INDEX = {"NAME": 51, "SYMBOL": 52, "EXCHG": 53, "TSYMBOL": 54}
DEPTH_INDEX = {"MULTIPLIER": 32, "PRECISION": 33}
BinRespTypes = {
    "CONNECTION_TYPE": 1,
    "THROTTLING_TYPE": 2,
    "ACK_TYPE": 3,
    "SUBSCRIBE_TYPE": 4,
    "UNSUBSCRIBE_TYPE": 5,
    "DATA_TYPE": 6,
    "CHPAUSE_TYPE": 7,
    "CHRESUME_TYPE": 8,
    "SNAPSHOT": 9,
    "OPC_SUBSCRIBE": 10,
}
BinRespStat = {"OK": "K", "NOT_OK": "N"}
ResponseTypes = {"SNAP": 83, "UPDATE": 85}
STAT = {"OK": "Ok", "NOT_OK": "NotOk"}
RespTypeValues = {
    "CONN": "cn",
    "SUBS": "sub",
    "UNSUBS": "unsub",
    "SNAP": "snap",
    "CHANNELR": "cr",
    "CHANNELP": "cp",
    "OPC": "opc",
}
RespCodes = {
    "SUCCESS": 200,
    "CONNECTION_FAILED": 11001,
    "CONNECTION_INVALID": 11002,
    "SUBSCRIPTION_FAILED": 11011,
    "UNSUBSCRIPTION_FAILED": 11012,
    "SNAPSHOT_FAILED": 11013,
    "CHANNELP_FAILED": 11031,
    "CHANNELR_FAILED": 11032,
}


def DataType(c, d):
    return {"name": c, "type": d}


TopicTypes = {"SCRIP": "sf", "INDEX": "if", "DEPTH": "dp"}
INDEX_INDEX = {"LTP": 2, "CLOSE": 3, "CHANGE": 10, "PERCHANGE": 11, "MULTIPLIER": 8, "PRECISION": 9}
SCRIP_INDEX = {
    "VOLUME": 4,
    "LTP": 5,
    "CLOSE": 21,
    "VWAP": 13,
    "MULTIPLIER": 23,
    "PRECISION": 24,
    "CHANGE": 25,
    "PERCHANGE": 26,
    "TURNOVER": 27,
}
Keys = {
    "TYPE": "type",
    "USER_ID": "user",
    "SESSION_ID": "sessionid",
    "SCRIPS": "scrips",
    "CHANNEL_NUM": "channelnum",
    "CHANNEL_NUMS": "channelnums",
    "JWT": "jwt",
    "REDIS_KEY": "redis",
    "STK_PRC": "stkprc",
    "HIGH_STK": "highstk",
    "LOW_STK": "lowstk",
    "OPC_KEY": "key",
    "AUTHORIZATION": "Authorization",
    "SID": "Sid",
    "X_ACCESS_TOKEN": "x-access-token",
    "SOURCE": "source",
}
ReqTypeValues = {
    "CONNECTION": "cn",
    "SCRIP_SUBS": "mws",
    "SCRIP_UNSUBS": "mwu",
    "INDEX_SUBS": "ifs",
    "INDEX_UNSUBS": "ifu",
    "DEPTH_SUBS": "dps",
    "DEPTH_UNSUBS": "dpu",
    "CHANNEL_RESUME": "cr",
    "CHANNEL_PAUSE": "cp",
    "SNAP_MW": "mwsp",
    "SNAP_DP": "dpsp",
    "SNAP_IF": "ifsp",
    "OPC_SUBS": "opc",
    "THROTTLING_INTERVAL": "ti",
    "STR": "str",
    "FORCE_CONNECTION": "fcn",
    "LOG": "log",
}

INDEX_MAPPING = [None] * 55
INDEX_MAPPING[0] = DataType("ftm0", FieldTypes.get("DATE"))
INDEX_MAPPING[1] = DataType("dtm1", FieldTypes.get("DATE"))
INDEX_MAPPING[INDEX_INDEX["LTP"]] = DataType("iv", FieldTypes.get("FLOAT32"))
INDEX_MAPPING[INDEX_INDEX["CLOSE"]] = DataType("ic", FieldTypes.get("FLOAT32"))
INDEX_MAPPING[4] = DataType("tvalue", FieldTypes.get("DATE"))
INDEX_MAPPING[5] = DataType("highPrice", FieldTypes.get("FLOAT32"))
INDEX_MAPPING[6] = DataType("lowPrice", FieldTypes.get("FLOAT32"))
INDEX_MAPPING[7] = DataType("openingPrice", FieldTypes.get("FLOAT32"))
INDEX_MAPPING[INDEX_INDEX["MULTIPLIER"]] = DataType("mul", FieldTypes.get("LONG"))
INDEX_MAPPING[INDEX_INDEX["PRECISION"]] = DataType("prec", FieldTypes.get("LONG"))
INDEX_MAPPING[INDEX_INDEX["CHANGE"]] = DataType("cng", FieldTypes.get("FLOAT32"))
INDEX_MAPPING[INDEX_INDEX["PERCHANGE"]] = DataType("nc", FieldTypes.get("STRING"))
INDEX_MAPPING[STRING_INDEX["NAME"]] = DataType("name", FieldTypes.get("STRING"))
INDEX_MAPPING[STRING_INDEX["SYMBOL"]] = DataType("tk", FieldTypes.get("STRING"))
INDEX_MAPPING[STRING_INDEX["EXCHG"]] = DataType("e", FieldTypes.get("STRING"))
INDEX_MAPPING[STRING_INDEX["TSYMBOL"]] = DataType("ts", FieldTypes.get("STRING"))

SCRIP_MAPPING = [None] * 100
SCRIP_MAPPING[0] = DataType("ftm0", FieldTypes["DATE"])
SCRIP_MAPPING[1] = DataType("dtm1", FieldTypes["DATE"])
SCRIP_MAPPING[2] = DataType("fdtm", FieldTypes["DATE"])
SCRIP_MAPPING[3] = DataType("ltt", FieldTypes["DATE"])
SCRIP_MAPPING[SCRIP_INDEX["VOLUME"]] = DataType("v", FieldTypes["LONG"])
SCRIP_MAPPING[SCRIP_INDEX["LTP"]] = DataType("ltp", FieldTypes["FLOAT32"])
SCRIP_MAPPING[6] = DataType("ltq", FieldTypes["LONG"])
SCRIP_MAPPING[7] = DataType("tbq", FieldTypes["LONG"])
SCRIP_MAPPING[8] = DataType("tsq", FieldTypes["LONG"])
SCRIP_MAPPING[9] = DataType("bp", FieldTypes["FLOAT32"])
SCRIP_MAPPING[10] = DataType("sp", FieldTypes["FLOAT32"])
SCRIP_MAPPING[11] = DataType("bq", FieldTypes["LONG"])
SCRIP_MAPPING[12] = DataType("bs", FieldTypes["LONG"])
SCRIP_MAPPING[SCRIP_INDEX["VWAP"]] = DataType("ap", FieldTypes["FLOAT32"])
SCRIP_MAPPING[14] = DataType("lo", FieldTypes["FLOAT32"])
SCRIP_MAPPING[15] = DataType("h", FieldTypes["FLOAT32"])
SCRIP_MAPPING[16] = DataType("lcl", FieldTypes["FLOAT32"])
SCRIP_MAPPING[17] = DataType("ucl", FieldTypes["FLOAT32"])
SCRIP_MAPPING[18] = DataType("yh", FieldTypes["FLOAT32"])
SCRIP_MAPPING[19] = DataType("yl", FieldTypes["FLOAT32"])
SCRIP_MAPPING[20] = DataType("op", FieldTypes["FLOAT32"])
SCRIP_MAPPING[SCRIP_INDEX["CLOSE"]] = DataType("c", FieldTypes["FLOAT32"])
SCRIP_MAPPING[22] = DataType("oi", FieldTypes["LONG"])
SCRIP_MAPPING[SCRIP_INDEX["MULTIPLIER"]] = DataType("mul", FieldTypes["LONG"])
SCRIP_MAPPING[SCRIP_INDEX["PRECISION"]] = DataType("prec", FieldTypes["LONG"])
SCRIP_MAPPING[SCRIP_INDEX["CHANGE"]] = DataType("cng", FieldTypes["FLOAT32"])
SCRIP_MAPPING[SCRIP_INDEX["PERCHANGE"]] = DataType("nc", FieldTypes["STRING"])
SCRIP_MAPPING[SCRIP_INDEX["TURNOVER"]] = DataType("to", FieldTypes["FLOAT32"])
SCRIP_MAPPING[STRING_INDEX["NAME"]] = DataType("name", FieldTypes["STRING"])
SCRIP_MAPPING[STRING_INDEX["SYMBOL"]] = DataType("tk", FieldTypes["STRING"])
SCRIP_MAPPING[STRING_INDEX["EXCHG"]] = DataType("e", FieldTypes["STRING"])
SCRIP_MAPPING[STRING_INDEX["TSYMBOL"]] = DataType("ts", FieldTypes["STRING"])

DEPTH_MAPPING = [None] * 55
DEPTH_MAPPING[0] = DataType("ftm0", FieldTypes.get("DATE"))
DEPTH_MAPPING[1] = DataType("dtm1", FieldTypes.get("DATE"))
DEPTH_MAPPING[2] = DataType("bp", FieldTypes.get("FLOAT32"))
DEPTH_MAPPING[3] = DataType("bp1", FieldTypes.get("FLOAT32"))
DEPTH_MAPPING[4] = DataType("bp2", FieldTypes.get("FLOAT32"))
DEPTH_MAPPING[5] = DataType("bp3", FieldTypes.get("FLOAT32"))
DEPTH_MAPPING[6] = DataType("bp4", FieldTypes.get("FLOAT32"))
DEPTH_MAPPING[7] = DataType("sp", FieldTypes.get("FLOAT32"))
DEPTH_MAPPING[8] = DataType("sp1", FieldTypes.get("FLOAT32"))
DEPTH_MAPPING[9] = DataType("sp2", FieldTypes.get("FLOAT32"))
DEPTH_MAPPING[10] = DataType("sp3", FieldTypes.get("FLOAT32"))
DEPTH_MAPPING[11] = DataType("sp4", FieldTypes.get("FLOAT32"))
DEPTH_MAPPING[12] = DataType("bq", FieldTypes.get("LONG"))
DEPTH_MAPPING[13] = DataType("bq1", FieldTypes.get("LONG"))
DEPTH_MAPPING[14] = DataType("bq2", FieldTypes.get("LONG"))
DEPTH_MAPPING[15] = DataType("bq3", FieldTypes.get("LONG"))
DEPTH_MAPPING[16] = DataType("bq4", FieldTypes.get("LONG"))
DEPTH_MAPPING[17] = DataType("bs", FieldTypes.get("LONG"))
DEPTH_MAPPING[18] = DataType("bs1", FieldTypes.get("LONG"))
DEPTH_MAPPING[19] = DataType("bs2", FieldTypes.get("LONG"))
DEPTH_MAPPING[20] = DataType("bs3", FieldTypes.get("LONG"))
DEPTH_MAPPING[21] = DataType("bs4", FieldTypes.get("LONG"))
DEPTH_MAPPING[22] = DataType("bno1", FieldTypes.get("LONG"))
DEPTH_MAPPING[23] = DataType("bno2", FieldTypes.get("LONG"))
DEPTH_MAPPING[24] = DataType("bno3", FieldTypes.get("LONG"))
DEPTH_MAPPING[25] = DataType("bno4", FieldTypes.get("LONG"))
DEPTH_MAPPING[26] = DataType("bno5", FieldTypes.get("LONG"))
DEPTH_MAPPING[27] = DataType("sno1", FieldTypes.get("LONG"))
DEPTH_MAPPING[28] = DataType("sno2", FieldTypes.get("LONG"))
DEPTH_MAPPING[29] = DataType("sno3", FieldTypes.get("LONG"))
DEPTH_MAPPING[30] = DataType("sno4", FieldTypes.get("LONG"))
DEPTH_MAPPING[31] = DataType("sno5", FieldTypes.get("LONG"))
DEPTH_MAPPING[DEPTH_INDEX["MULTIPLIER"]] = DataType("mul", FieldTypes["LONG"])
DEPTH_MAPPING[DEPTH_INDEX["PRECISION"]] = DataType("prec", FieldTypes["LONG"])
DEPTH_MAPPING[STRING_INDEX["NAME"]] = DataType("name", FieldTypes["STRING"])
DEPTH_MAPPING[STRING_INDEX["SYMBOL"]] = DataType("tk", FieldTypes["STRING"])
DEPTH_MAPPING[STRING_INDEX["EXCHG"]] = DataType("e", FieldTypes["STRING"])
DEPTH_MAPPING[STRING_INDEX["TSYMBOL"]] = DataType("ts", FieldTypes["STRING"])


def leadingZero(a):
    return "0" + str(a) if a < 10 else str(a)


def getFormatDate(a):
    date = datetime.datetime.fromtimestamp(a)
    formatDate = f"{leadingZero(date.day)}/{leadingZero(date.month)}/{date.year} {leadingZero(date.hour)}:{leadingZero(date.minute)}:{leadingZero(date.second)}"
    return formatDate


class ByteData:
    def __init__(self, c):
        self.pos = 0
        self.bytes = [0] * (c)
        self.startOfMsg = 0

    def lenth(self):
        # logger.info(f"lenght of the bytes {self.bytes} {len(self.bytes)}")
        pass

    def markStartOfMsg(self):
        self.startOfMsg = self.pos
        self.pos += 2

    def markEndOfMsg(self):
        len = self.pos - self.startOfMsg - 2
        self.bytes[0] = (len >> 8) & 255
        self.bytes[1] = len & 255

    def clear(self):
        self.pos = 0

    def getPosition(self):
        return self.pos

    def getBytes(self):
        return self.bytes

    def appendByte(self, d):
        # logger.info(f"in append Bytes POS {self.pos}")
        # logger.info(f"in append Bytes d {d}")
        self.bytes[self.pos] = d
        self.pos += 1
        # logger.info(f"in append Bytes {self.bytes}")

    def appendByteAtPos(self, e, d):
        self.bytes[e] = d

    def appendChar(self, d):
        self.bytes[self.pos] = d
        self.pos += 1

    def appendCharAtPos(self, e, d):
        self.bytes[e] = d

    def appendShort(self, d):
        self.bytes[self.pos] = (d >> 8) & 255
        self.pos += 1
        self.bytes[self.pos] = d & 255
        self.pos += 1

    def appendInt(self, d):
        self.bytes[self.pos] = (d >> 24) & 255
        self.pos += 1
        self.bytes[self.pos] = (d >> 16) & 255
        self.pos += 1
        self.bytes[self.pos] = (d >> 8) & 255
        self.pos += 1
        self.bytes[self.pos] = d & 255
        self.pos += 1

    def appendLong(self, d):
        self.bytes[self.pos] = (d >> 56) & 255
        self.pos += 1
        self.bytes[self.pos] = (d >> 48) & 255
        self.pos += 1
        self.bytes[self.pos] = (d >> 40) & 255
        self.pos += 1
        self.bytes[self.pos] = (d >> 32) & 255
        self.pos += 1
        self.bytes[self.pos] = (d >> 24) & 255
        self.pos += 1
        self.bytes[self.pos] = (d >> 16) & 255
        self.pos += 1
        self.bytes[self.pos] = (d >> 8) & 255
        self.pos += 1
        self.bytes[self.pos] = d & 255
        self.pos += 1

    def append_long_as_big_int(self, e):
        d = int(e)
        self.bytes.append((d >> 56) & 255)
        self.bytes.append((d >> 48) & 255)
        self.bytes.append((d >> 40) & 255)
        self.bytes.append((d >> 32) & 255)
        self.bytes.append((d >> 24) & 255)
        self.bytes.append((d >> 16) & 255)
        self.bytes.append((d >> 8) & 255)
        self.bytes.append(d & 255)

    def append_string(self, d):
        str_len = len(d)
        for i in range(str_len):
            self.bytes[self.pos] = ord(d[i])
            self.pos += 1
            # self.bytes.append(ord(d[i]))

    def append_byte_array(self, d):
        byte_len = len(d)
        for i in range(byte_len):
            self.bytes[self.pos] = d[i]
            self.pos += 1
            # self.bytes.append(d[i])

    def appendByteArr(self, e, d):
        for i in range(d):
            self.bytes[self.pos] = e[i]
            self.pos += 1


class TopicData:
    def __init__(self, feed_type):
        self.feedType = feed_type
        self.exchange = None
        self.symbol = None
        self.tSymbol = None
        self.multiplier = 1
        self.precision = 2
        self.precisionValue = 100
        self.jsonArray = None
        self.fieldDataArray = [None] * 100
        self.updatedFieldsArray = [None] * 100
        self.fieldDataArray[STRING_INDEX["NAME"]] = feed_type

    def getKey(self):
        return f"{self.exchange}|{self.symbol}"

    def setLongValues(self, index_val, value):
        if self.fieldDataArray[index_val] != value and value != TRASH_VAL:
            self.fieldDataArray[index_val] = value
            self.updatedFieldsArray[index_val] = True

    def prepareCommonData(self):
        self.updatedFieldsArray[STRING_INDEX["NAME"]] = True
        self.updatedFieldsArray[STRING_INDEX["EXCHG"]] = True
        self.updatedFieldsArray[STRING_INDEX["SYMBOL"]] = True

    def setStringValues(self, e, d):
        if e == STRING_INDEX["SYMBOL"]:
            self.symbol = d
            self.fieldDataArray[STRING_INDEX["SYMBOL"]] = d
        elif e == STRING_INDEX["EXCHG"]:
            self.exchange = d
            self.fieldDataArray[STRING_INDEX["EXCHG"]] = d
        elif e == STRING_INDEX["TSYMBOL"]:
            self.tSymbol = d
            self.fieldDataArray[STRING_INDEX["TSYMBOL"]] = d
            self.updatedFieldsArray[STRING_INDEX["TSYMBOL"]] = True


class DepthTopicData(TopicData):
    def __init__(self):
        # logger.info("INSIDE DepthTopicData")
        super().__init__(TopicTypes["DEPTH"])
        self.updatedFieldsArray = [None] * 100
        # Inherit sensible defaults from TopicData (multiplier=1, precision=2, precisionValue=100)
        # setMultiplierAndPrec() will override these once the broker sends actual values

    def setMultiplierAndPrec(self):
        # logger.info("INTO setMultiplierAndPrec")
        if self.updatedFieldsArray[DEPTH_INDEX["PRECISION"]]:
            self.precision = self.fieldDataArray[DEPTH_INDEX["PRECISION"]]
            self.precisionValue = 10**self.precision
        if self.updatedFieldsArray[DEPTH_INDEX["MULTIPLIER"]]:
            self.multiplier = self.fieldDataArray[DEPTH_INDEX["MULTIPLIER"]]

    def prepareData(self):
        # logger.info("INSIDE prepareData")
        self.prepareCommonData()
        # logger.info(f"\nDepth: {self.feedType} {self.exchange} {self.symbol}")
        json_res = {}
        for d in range(len(DEPTH_MAPPING)):
            c = DEPTH_MAPPING[d]
            e = self.fieldDataArray[d]
            if self.updatedFieldsArray[d] and e is not None and c:
                if c["type"] == FieldTypes.get("FLOAT32"):
                    e = round(e / (self.multiplier * self.precisionValue), self.precision)
                elif c["type"] == FieldTypes.get("DATE"):
                    e = getFormatDate(e)
                # logger.info(f"{d} : {c['name']} : {e}")
                json_res[c["name"]] = str(e)
        self.updatedFieldsArray = [None] * 100
        # logger.info(f"INSIDE Parse Data {json_res}")
        return json_res


def get_acknowledgement_req(a):
    buffer = ByteData(11)  # bytearray(11)
    buffer.markStartOfMsg()
    buffer.appendByte(BinRespTypes["ACK_TYPE"])
    buffer.appendByte(1)
    buffer.appendByte(1)
    buffer.appendShort(4)
    buffer.appendInt(a)
    buffer.markEndOfMsg()
    return buffer.getBytes()


def prepare_connection_request(a):
    user_id_len = len(a)
    src = "JS_API"
    src_len = len(src)
    buffer = bytearray(user_id_len + src_len + 10)
    buffer[0] = BinRespTypes.get("CONNECTION_TYPE")
    buffer[1] = 2
    buffer[2] = 1
    buffer[3:5] = int(user_id_len).to_bytes(2, byteorder="big")
    buffer[5 : 5 + user_id_len] = a.encode()
    buffer[5 + user_id_len] = 2
    buffer[6 + user_id_len : 8 + user_id_len] = int(src_len).to_bytes(2, byteorder="big")
    buffer[8 + user_id_len : 8 + user_id_len + src_len] = src.encode()
    # End-of-message marker (0xFF) — not in BinRespTypes since it's a framing byte, not a type
    buffer[8 + user_id_len + src_len] = 0xFF
    return buffer


def prepareConnectionRequest2(a, c):
    # a = bytearray(bytes(a, encoding='utf8'))
    # c = bytearray(bytes(c, encoding='utf8'))
    src = "JS_API"
    # src = bytearray(bytes(src, encoding='utf8'))
    srcLen = len(src)
    jwtLen = len(a)
    redisLen = len(c)
    buffer = ByteData(srcLen + jwtLen + redisLen + 13)
    buffer.markStartOfMsg()
    buffer.appendByte(BinRespTypes["CONNECTION_TYPE"])
    buffer.appendByte(3)
    buffer.appendByte(1)
    buffer.appendShort(jwtLen)
    buffer.append_string(a)
    buffer.appendByte(2)
    buffer.appendShort(redisLen)
    buffer.append_string(c)
    buffer.appendByte(3)
    buffer.appendShort(srcLen)
    buffer.append_string(src)
    buffer.markEndOfMsg()
    return buffer.getBytes()


def is_scrip_ok(a):
    scrips_count = len(a.split("&"))
    if scrips_count > MAX_SCRIPS:
        logger.info(f"Maximum scrips allowed per request is {str(MAX_SCRIPS)}")
        return False
    return True


def getScripByteArray(c, a):
    if c[-1] == "&":
        c = c[:-1]
    scripArray = c.split("&")
    scripsCount = len(scripArray)
    dataLen = 0
    for index in range(scripsCount):
        scripArray[index] = a + "|" + scripArray[index]
        dataLen += len(scripArray[index]) + 1
    # logger.info(f"Data len {dataLen}")
    bytes = [0] * (dataLen + 2)
    pos = 0
    bytes[pos] = (scripsCount >> 8) & 255
    pos += 1
    bytes[pos] = scripsCount & 255
    pos += 1
    for index in range(scripsCount):
        currScrip = scripArray[index]
        scripLen = len(currScrip)
        bytes[pos] = scripLen & 255
        pos += 1
        for strIndex in range(scripLen):
            bytes[pos] = ord(currScrip[strIndex])
            pos += 1
    # logger.info(f"Bytes {bytes}")
    return bytes


def prepareSubsUnSubsRequest(scrips, subscribe_type, scrip_prefix, channel_num):
    # logger.info("Prepare prepareSubsUnSubsRequest")
    if not is_scrip_ok(scrips):
        return

    dataArr = getScripByteArray(scrips, scrip_prefix)
    # logger.info(f"Length Arr {dataArr}")
    # buffer = [0] * (len(dataArr) + 11) #ByteData(len(dataArr) + 11)
    buffer = ByteData(len(dataArr) + 11)
    buffer.markStartOfMsg()
    buffer.appendByte(subscribe_type)
    buffer.appendByte(2)
    buffer.appendByte(1)
    buffer.appendShort(len(dataArr))
    buffer.appendByteArr(dataArr, len(dataArr))
    buffer.appendByte(2)
    buffer.appendShort(1)
    buffer.appendByte(int(channel_num))
    buffer.markEndOfMsg()
    return buffer.getBytes()


def prepareSnapshotRequest(a, c, d):
    # logger.info(f"INTO prepareSnapshotRequest {a} {c} {d}")
    if not is_scrip_ok(a):
        return
    dataArr = getScripByteArray(a, d)
    # logger.info(f"DATA ARRAY {dataArr}")
    buffer = ByteData(len(dataArr) + 7)
    buffer.markStartOfMsg()
    buffer.appendByte(c)
    buffer.appendByte(1)
    buffer.appendByte(2)
    buffer.appendShort(len(dataArr))
    buffer.appendByteArr(dataArr, len(dataArr))
    buffer.markEndOfMsg()
    return buffer.getBytes()


def prepareChannelRequest(c, a):
    buffer = bytearray(15)
    buffer[0] = c
    buffer[1] = 1
    buffer[2] = 1
    buffer[3:5] = (8).to_bytes(2, byteorder="big")
    int1, int2 = 0, 0
    for d in a:
        if 0 < d <= 32:
            int1 |= 1 << d
        elif 32 < d <= 64:
            int2 |= 1 << d
        else:
            logger.info("Error: Channel values must be in this range  [ val > 0 && val < 65 ]")
    buffer[5:9] = int2.to_bytes(4, byteorder="big")
    buffer[9:13] = int1.to_bytes(4, byteorder="big")
    return buffer


def prepareThrottlingIntervalRequest(a):
    buffer = bytearray(11)
    buffer[0] = BinRespTypes.get("THROTTLING_TYPE")
    buffer[1] = 1
    buffer[2] = 1
    buffer[3] = (4 >> 8) & 255
    buffer[4] = 4 & 255
    buffer[5] = (a >> 24) & 255
    buffer[6] = (a >> 16) & 255
    buffer[7] = (a >> 8) & 255
    buffer[8] = a & 255
    return buffer


def get_scrip_byte_array(c, a):
    if c[-1] == "&":
        c = c[:-1]
    scrip_array = c.split("&")
    scrips_count = len(scrip_array)
    data_len = 0
    for index in range(scrips_count):
        scrip_array[index] = a + "|" + scrip_array[index]
        data_len += len(scrip_array[index]) + 1
    bytes = bytearray(data_len + 2)
    pos = 0
    bytes[pos] = (scrips_count >> 8) & 255
    pos += 1
    bytes[pos] = scrips_count & 255
    pos += 1
    for index in range(scrips_count):
        curr_scrip = scrip_array[index]
        scrip_len = len(curr_scrip)
        bytes[pos] = scrip_len & 255
        pos += 1
        for str_index in range(scrip_len):
            bytes[pos] = ord(curr_scrip[str_index])
            pos += 1
    return bytes


def get_opc_chain_subs_request(d, e, a, c, f):
    opc_key_len = len(d)
    buffer = bytearray(opc_key_len + 30)
    pos = 0
    buffer[pos] = BinRespTypes.get("OPC_SUBSCRIBE")
    pos += 1
    buffer[pos] = 5
    pos += 1
    buffer[pos] = 1
    pos += 1
    buffer[pos] = opc_key_len >> 8 & 255
    pos += 1
    buffer[pos] = opc_key_len & 255
    pos += 1
    for i in range(opc_key_len):
        buffer[pos] = ord(d[i])
        pos += 1
    buffer[pos] = 2
    pos += 1
    buffer[pos] = 8 >> 8 & 255
    pos += 1
    buffer[pos] = 8 & 255
    pos += 1
    # The below code assumes the input value of e is a 64-bit integer
    buffer[pos] = e >> 56 & 255
    pos += 1
    buffer[pos] = e >> 48 & 255
    pos += 1
    buffer[pos] = e >> 40 & 255
    pos += 1
    buffer[pos] = e >> 32 & 255
    pos += 1
    buffer[pos] = e >> 24 & 255
    pos += 1
    buffer[pos] = e >> 16 & 255
    pos += 1
    buffer[pos] = e >> 8 & 255
    pos += 1
    buffer[pos] = e & 255
    pos += 1
    buffer[pos] = 3
    pos += 1
    buffer[pos] = 1 >> 8 & 255
    pos += 1
    buffer[pos] = 1 & 255
    pos += 1
    buffer[pos] = a
    pos += 1
    buffer[pos] = 4
    pos += 1
    buffer[pos] = 1 >> 8 & 255
    pos += 1
    buffer[pos] = 1 & 255
    pos += 1
    buffer[pos] = c
    pos += 1
    buffer[pos] = 5
    pos += 1
    buffer[pos] = 1 >> 8 & 255
    pos += 1
    buffer[pos] = 1 & 255
    pos += 1
    buffer[pos] = f
    return buffer


def send_json_arr_resp(a):
    json_arr_res = []
    json_arr_res.append(a)
    return json.dumps(json_arr_res)


def buf2long(a):
    b = bytearray(a)
    val = 0
    leng = len(b)
    for i in range(leng):
        j = leng - 1 - i
        val += b[j] << (i * 8)
    return val


def buf2string(a):
    return bytes(a).decode("utf-8", errors="replace")


class ScripTopicData(TopicData):
    def __init__(self):
        super().__init__(TopicTypes["SCRIP"])
        # Inherit sensible defaults from TopicData (multiplier=1, precision=2, precisionValue=100)
        # setMultiplierAndPrec() will override these once the broker sends actual values

    def setMultiplierAndPrec(self):
        if self.updatedFieldsArray[SCRIP_INDEX["PRECISION"]]:
            self.precision = self.fieldDataArray[SCRIP_INDEX["PRECISION"]]
            self.precisionValue = pow(10, self.precision)
        if self.updatedFieldsArray[SCRIP_INDEX["MULTIPLIER"]]:
            self.multiplier = self.fieldDataArray[SCRIP_INDEX["MULTIPLIER"]]

    def prepareData(self):
        self.prepareCommonData()
        if (
            self.updatedFieldsArray[SCRIP_INDEX["LTP"]]
            or self.updatedFieldsArray[SCRIP_INDEX["CLOSE"]]
        ):
            ltp = self.fieldDataArray[SCRIP_INDEX["LTP"]]
            close = self.fieldDataArray[SCRIP_INDEX["CLOSE"]]
            if ltp is not None and close is not None:
                change = ltp - close
                self.fieldDataArray[SCRIP_INDEX["CHANGE"]] = change
                self.updatedFieldsArray[SCRIP_INDEX["CHANGE"]] = True
                per_change = f"{change / close * 100:.2f}" if close != 0 else "0.00"
                self.fieldDataArray[SCRIP_INDEX["PERCHANGE"]] = per_change
                self.updatedFieldsArray[SCRIP_INDEX["PERCHANGE"]] = True
        if (
            self.updatedFieldsArray[SCRIP_INDEX["VOLUME"]]
            or self.updatedFieldsArray[SCRIP_INDEX["VWAP"]]
        ):
            volume = self.fieldDataArray[SCRIP_INDEX["VOLUME"]]
            vwap = self.fieldDataArray[SCRIP_INDEX["VWAP"]]
            if volume is not None and vwap is not None:
                self.fieldDataArray[SCRIP_INDEX["TURNOVER"]] = volume * vwap
                self.updatedFieldsArray[SCRIP_INDEX["TURNOVER"]] = True
        # logger.info(f"\nScrip::{self.feedType}|{self.exchange}|{self.symbol}")
        jsonRes = {}
        for index in range(len(SCRIP_MAPPING)):
            dataType = SCRIP_MAPPING[index]
            val = self.fieldDataArray[index]
            if self.updatedFieldsArray[index] and val is not None and dataType:
                if dataType["type"] == FieldTypes["FLOAT32"]:
                    val = f"{val / (self.multiplier * self.precisionValue):.2f}"
                elif dataType["type"] == FieldTypes["DATE"]:
                    val = getFormatDate(val)
                # logger.info(f'{str(index)}:{dataType["name"]}:{str(val)}')
                jsonRes[dataType["name"]] = str(val)
        self.updatedFieldsArray = [None] * 100
        return jsonRes


class IndexTopicData(TopicData):
    def __init__(self):
        # logger.info("INSIDE IndexTopicData")
        super().__init__(TopicTypes["INDEX"])
        self.updatedFieldsArray = [None] * 100
        # Inherit sensible defaults from TopicData (multiplier=1, precision=2, precisionValue=100)
        # setMultiplierAndPrec() will override these once the broker sends actual values

    def setMultiplierAndPrec(self):
        if self.updatedFieldsArray[INDEX_INDEX["PRECISION"]]:
            self.precision = self.fieldDataArray[INDEX_INDEX["PRECISION"]]
            self.precisionValue = 10**self.precision
        if self.updatedFieldsArray[INDEX_INDEX["MULTIPLIER"]]:
            self.multiplier = self.fieldDataArray[INDEX_INDEX["MULTIPLIER"]]

    def prepareData(self):
        self.prepareCommonData()
        if (
            self.updatedFieldsArray[INDEX_INDEX["LTP"]]
            or self.updatedFieldsArray[INDEX_INDEX["CLOSE"]]
        ):
            ltp = self.fieldDataArray[INDEX_INDEX["LTP"]]
            close = self.fieldDataArray[INDEX_INDEX["CLOSE"]]
            if ltp is not None and close is not None:
                change = ltp - close
                self.fieldDataArray[INDEX_INDEX["CHANGE"]] = change
                self.updatedFieldsArray[INDEX_INDEX["CHANGE"]] = True
                per_change = round(change / close * 100, self.precision) if close != 0 else 0.0
                self.fieldDataArray[INDEX_INDEX["PERCHANGE"]] = per_change
                self.updatedFieldsArray[INDEX_INDEX["PERCHANGE"]] = True
        # logger.info(f"\nIndex::{self.feedType}|{self.exchange}|{self.symbol}")
        json_res = {}
        for index in range(len(INDEX_MAPPING)):
            data_type = INDEX_MAPPING[index]
            val = self.fieldDataArray[index]
            if self.updatedFieldsArray[index] and val is not None and data_type is not None:
                if data_type["type"] == FieldTypes["FLOAT32"]:
                    val = round(val / (self.multiplier * self.precisionValue), self.precision)
                elif data_type["type"] == FieldTypes["DATE"]:
                    val = getFormatDate(val)
                # logger.info(f'{str(index)}:{data_type["name"]}:{str(val)}')
                json_res[data_type["name"]] = str(val)
        self.updatedFieldsArray = [None] * 100
        return json_res


class HSWrapper:
    def __init__(self, ws_app=None, send_lock=None):
        self.counter = 0
        self.ack_num = 0
        self._ws_app = ws_app  # Reference to WebSocketApp for sending acks
        self._send_lock = send_lock  # Serialize sends with subscription messages
        self.topic_list = {}  # Per-instance topic data, not shared globally
        self._max_topics = 5000  # Cap topic_list to prevent unbounded memory growth

    def getNewTopicData(self, c):
        # logger.info(f"INPUT {c}")
        feed_type, *_ = c.split("|")
        topic = None
        if feed_type == TopicTypes.get("SCRIP"):
            topic = ScripTopicData()
        elif feed_type == TopicTypes.get("INDEX"):
            # logger.info("INTO FEED TYPE index")
            topic = IndexTopicData()
        elif feed_type == TopicTypes.get("DEPTH"):
            topic = DepthTopicData()
        return topic

    def getStatus(self, c, d):
        status = BinRespStat.get("NOT_OK")
        field_count = buf2long(c[d : d + 1])
        d += 1
        if field_count > 0:
            fld = buf2long(c[d : d + 1])
            d = d + 1
            field_length = buf2long(c[d : d + 2])
            d += 2
            status = buf2string(c[d : d + field_length])
            d += field_length
        return status

    def parseData(self, e):
        if len(e) < 3:
            logger.warning(f"Truncated binary message: {len(e)} bytes, dropping")
            return None
        pos = 0
        # logger.info(f"INTO Parse Data {e}")
        try:
            return self._parseDataInner(e)
        except (IndexError, ValueError) as exc:
            logger.error(f"Malformed binary message ({len(e)} bytes): {exc}, dropping")
            return None

    def _parseDataInner(self, e):
        pos = 0
        packetsCount = buf2long(e[pos:2])
        pos += 2
        type = int.from_bytes(e[pos : pos + 1], "big")
        pos += 1
        # logger.info(f"Type in HSWebsocket {type}")
        # logger.info(f"parse data {e}")
        # logger.info(f"parse data len {len(e)}")
        if type == BinRespTypes.get("CONNECTION_TYPE"):
            jsonRes = {}
            fCount = int.from_bytes(e[pos : pos + 1], "big")
            pos += 1
            if fCount >= 2:
                fid1 = int.from_bytes(e[pos : pos + 1], "big")
                pos += 1
                valLen = int.from_bytes(e[pos : pos + 2], "big")
                pos += 2
                status = e[pos : pos + valLen].decode("utf-8")
                pos += valLen
                fid1 = int.from_bytes(e[pos : pos + 1], "big")
                pos += 1
                valLen = int.from_bytes(e[pos : pos + 2], "big")
                pos += 2
                ackCount = int.from_bytes(e[pos : pos + valLen], "big")
                # logger.info(f"STATUS {status}")
                if status == BinRespStat.get("OK"):
                    jsonRes["stat"] = STAT.get("OK")
                    jsonRes["type"] = RespTypeValues.get("CONN")
                    jsonRes["msg"] = "successful"
                    jsonRes["stCode"] = RespCodes.get("SUCCESS")
                elif status == BinRespStat.get("NOT_OK"):
                    jsonRes["stat"] = STAT.get("NOT_OK")
                    jsonRes["type"] = RespTypeValues.get("CONN")
                    jsonRes["msg"] = "failed"
                    jsonRes["stCode"] = RespCodes.get("CONNECTION_FAILED")
                self.ack_num = ackCount
            elif fCount == 1:
                fid1 = int.from_bytes(e[pos : pos + 1], "big")
                pos += 1
                valLen = int.from_bytes(e[pos : pos + 2], "big")
                pos += 2
                status = e[pos : pos + valLen].decode("utf-8")
                pos += valLen
                if status == BinRespStat.get("OK"):
                    jsonRes["stat"] = STAT.get("OK")
                    jsonRes["type"] = RespTypeValues.get("CONN")
                    jsonRes["msg"] = "successful"
                    jsonRes["stCode"] = RespCodes.get("SUCCESS")
                elif status == BinRespStat.get("NOT_OK"):
                    jsonRes["stat"] = STAT.get("NOT_OK")
                    jsonRes["type"] = RespTypeValues.get("CONN")
                    jsonRes["msg"] = "failed"
                    jsonRes["stCode"] = RespCodes.get("CONNECTION_FAILED")
            else:
                jsonRes["stat"] = STAT.get("NOT_OK")
                jsonRes["type"] = RespTypeValues.get("CONN")
                jsonRes["msg"] = "invalid field count"
                jsonRes["stCode"] = RespCodes.get("CONNECTION_INVALID")
            return send_json_arr_resp(jsonRes)
        else:
            if type == BinRespTypes.get("DATA_TYPE"):
                # logger.info("IN By Datatype ")
                # logger.info(f"IN By self.ack_num {self.ack_num}")
                msg_num = 0
                if self.ack_num > 0:
                    # logger.info(f"ack_num {self.ack_num}")
                    self.counter += 1
                    msg_num = buf2long(e[pos : pos + 4])
                    pos += 4
                    if self.counter == self.ack_num:
                        req = get_acknowledgement_req(msg_num)
                        ws = self._ws_app
                        if ws:
                            if self._send_lock:
                                with self._send_lock:
                                    ws.send(req, 0x2)
                            else:
                                ws.send(req, 0x2)
                            self.counter = 0
                        # logger.info(f"Acknowledgement sent for message num: {msg_num}")
                h = []
                g = buf2long(e[pos : pos + 2])
                # logger.info(f"G in {g}")
                pos += 2
                for n in range(g):
                    sub_msg_len = buf2long(e[pos : pos + 2])
                    pos += 2
                    sub_msg_start = pos
                    c = buf2long(e[pos : pos + 1])
                    # logger.info(f"ResponseType: {c}")
                    pos += 1
                    if c == ResponseTypes.get("SNAP"):
                        f = buf2long(e[pos : pos + 4])
                        pos += 4
                        # logger.info(f"topic Id: {f}")
                        name_len = buf2long(e[pos : pos + 1])
                        pos += 1
                        topic_name = buf2string(e[pos : pos + name_len])
                        # logger.info(f"TOPIC Name {topic_name}")
                        pos += name_len
                        d = self.getNewTopicData(topic_name)
                        if d:
                            # Evict oldest entries if topic_list exceeds cap
                            if len(self.topic_list) >= self._max_topics and f not in self.topic_list:
                                oldest_key = next(iter(self.topic_list))
                                del self.topic_list[oldest_key]
                            self.topic_list[f] = d
                            fcount = buf2long(e[pos : pos + 1])
                            pos += 1
                            max_fields = len(d.fieldDataArray)
                            # logger.info(f"fcount1: {fcount}")
                            for index in range(fcount):
                                fvalue = buf2long(e[pos : pos + 4])
                                if index < max_fields:
                                    d.setLongValues(index, fvalue)
                                pos += 4
                            # logger.info("Able to set ")
                            d.setMultiplierAndPrec()
                            fcount = buf2long(e[pos : pos + 1])
                            pos += 1
                            # logger.info(f"fcount2: {fcount}")
                            for index in range(fcount):
                                fid = buf2long(e[pos : pos + 1])
                                pos += 1
                                data_len = buf2long(e[pos : pos + 1])
                                pos += 1
                                str_val = buf2string(e[pos : pos + data_len])
                                pos += data_len
                                d.setStringValues(fid, str_val)
                                # logger.info(f"{fid} : {str_val}")
                            h.append(d.prepareData())
                        else:
                            logger.info("Invalid topic feed type !")
                            # Skip integer fields to keep pos aligned
                            fcount_skip = buf2long(e[pos : pos + 1])
                            pos += 1
                            pos += fcount_skip * 4
                            # Skip string fields
                            fcount2_skip = buf2long(e[pos : pos + 1])
                            pos += 1
                            for _ in range(fcount2_skip):
                                pos += 1  # fid
                                skip_len = buf2long(e[pos : pos + 1])
                                pos += 1
                                pos += skip_len
                    else:
                        if c == ResponseTypes.get("UPDATE"):
                            logger.debug("updates ......")
                            f = buf2long(e[pos : pos + 4])
                            # logger.info(f"topic Id: {f}")
                            pos += 4
                            d = self.topic_list.get(f)
                            if not d:
                                logger.info("Topic Not Available in TopicList!")
                                # Skip remaining fields for this update to keep pos correct
                                fcount = buf2long(e[pos : pos + 1])
                                pos += 1
                                pos += fcount * 4
                                continue
                            # logger.info("INSIDE Else COndition ")
                            fcount = buf2long(e[pos : pos + 1])
                            pos += 1
                            max_fields = len(d.fieldDataArray)
                            # logger.info(f"fcount1: {fcount}")
                            for index in range(fcount):
                                fvalue = buf2long(e[pos : pos + 4])
                                if index < max_fields:
                                    d.setLongValues(index, fvalue)
                                # d[index] = fvalue
                                # logger.info(f"index: {index} val: {fvalue}")
                                pos += 4
                            d.setMultiplierAndPrec()
                            h.append(d.prepareData())
                        else:
                            logger.info(f"Invalid ResponseType: {c}")
                            # Skip remaining bytes of this sub-message to keep pos aligned
                            pos = sub_msg_start + sub_msg_len
                return h
            else:
                if type == BinRespTypes.get("SUBSCRIBE_TYPE") or type == BinRespTypes.get(
                    "UNSUBSCRIBE_TYPE"
                ):
                    # logger.info("INTO SUBScirbe Condition")
                    status = self.getStatus(e, pos)
                    json_res = {}
                    if status == BinRespStat.get("OK"):
                        json_res["stat"] = STAT.get("OK")
                        json_res["type"] = (
                            RespTypeValues.get("SUBS")
                            if type == BinRespTypes.get("SUBSCRIBE_TYPE")
                            else RespTypeValues.get("UNSUBS")
                        )
                        json_res["msg"] = "successful"
                        json_res["stCode"] = RespCodes.get("SUCCESS")
                    elif status == BinRespStat.get("NOT_OK"):
                        json_res["stat"] = STAT.get("NOT_OK")
                        if type == BinRespTypes.get("SUBSCRIBE_TYPE"):
                            json_res["type"] = RespTypeValues.get("SUBS")
                            json_res["msg"] = "subscription failed"
                            json_res["stCode"] = RespCodes.get("SUBSCRIPTION_FAILED")
                        else:
                            json_res["type"] = RespTypeValues.get("UNSUBS")
                            json_res["msg"] = "unsubscription failed"
                            json_res["stCode"] = RespCodes.get("UNSUBSCRIPTION_FAILED")
                    return send_json_arr_resp(json_res)

                else:
                    if type == BinRespTypes.get("SNAPSHOT"):
                        status = self.getStatus(e, pos)
                        json_res = {}
                        if status == BinRespStat.get("OK"):
                            json_res["stat"] = STAT.get("OK")
                            json_res["type"] = RespTypeValues.get("SNAP")
                            json_res["msg"] = "successful"
                            json_res["stCode"] = RespCodes.get("SUCCESS")
                        elif status == BinRespStat.get("NOT_OK"):
                            json_res["stat"] = STAT.get("NOT_OK")
                            json_res["type"] = RespTypeValues.get("SNAP")
                            json_res["msg"] = "failed"
                            json_res["stCode"] = RespCodes.get("SNAPSHOT_FAILED")
                        return send_json_arr_resp(json_res)
                    elif type == BinRespTypes.get("CHPAUSE_TYPE") or type == BinRespTypes.get(
                        "CHRESUME_TYPE"
                    ):
                        status = self.getStatus(e, pos)
                        json_res = {}
                        if status == BinRespStat.get("OK"):
                            json_res["stat"] = STAT.get("OK")
                            if type == BinRespTypes.get("CHPAUSE_TYPE"):
                                json_res["type"] = RespTypeValues.get("CHANNELP")
                            else:
                                json_res["type"] = RespTypeValues.get("CHANNELR")
                            json_res["msg"] = "successful"
                            json_res["stCode"] = RespCodes.get("SUCCESS")
                        elif status == BinRespStat.get("NOT_OK"):
                            json_res["stat"] = STAT.get("NOT_OK")
                            if type == BinRespTypes.get("CHPAUSE_TYPE"):
                                json_res["type"] = RespTypeValues.get("CHANNELP")
                            else:
                                json_res["type"] = RespTypeValues.get("CHANNELR")
                            json_res["msg"] = "failed"
                            if type == BinRespTypes.get("CHPAUSE_TYPE"):
                                json_res["stCode"] = RespCodes.get("CHANNELP_FAILED")
                            else:
                                json_res["stCode"] = RespCodes.get("CHANNELR_FAILED")
                        return send_json_arr_resp(json_res)
                    elif type == BinRespTypes.get("OPC_SUBSCRIBE"):
                        status = self.getStatus(e, pos)
                        pos += 5
                        json_res = {}
                        if status == BinRespStat.get("OK"):
                            json_res["stat"] = STAT.get("OK")
                            json_res["type"] = RespTypeValues.get("OPC")
                            json_res["msg"] = "successful"
                            json_res["stCode"] = RespCodes.get("SUCCESS")
                            fld = buf2long(e[pos : pos + 1])
                            pos += 1
                            field_length = buf2long(e[pos : pos + 2])
                            pos += 2
                            opc_key = buf2string(e[pos : pos + field_length])
                            pos += field_length
                            json_res["key"] = opc_key
                            fld = buf2long(e[pos : pos + 1])
                            pos += 1
                            field_length = buf2long(e[pos : pos + 2])
                            pos += 2
                            data = buf2string(e[pos : pos + field_length])
                            pos += field_length
                            json_res["scrips"] = json.loads(data)["data"]
                        elif status == BinRespStat.get("NOT_OK"):
                            json_res["stat"] = STAT.get("NOT_OK")
                            json_res["type"] = RespTypeValues.get("OPC")
                            json_res["msg"] = "failed"
                            json_res["stCode"] = 11040

                        return send_json_arr_resp(json_res)
                    else:
                        return None


class StartServer:
    def __init__(self, a, token, sid, onopen, onmessage, onerror, onclose, owner=None, send_lock=None):
        self.userSocket = self
        self.a = a
        self.onopen = onopen
        self.onmessage = onmessage
        self.onerror = onerror
        self.onclose = onclose
        self.token, self.sid = token, sid
        self._owner = owner  # HSWebSocket instance that owns this connection
        self._send_lock = send_lock  # Lock for serializing WebSocket sends
        self._ws_app = None
        try:
            # websocket.enableTrace(True)
            self._ws_app = websocket.WebSocketApp(
                a,
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
            )
        except Exception as e:
            logger.error(f"WebSocket not supported: {e}")
            self.onerror(e)

        if self._ws_app:
            self.hsWrapper = HSWrapper(ws_app=self._ws_app, send_lock=self._send_lock)
            # Store references on the owning HSWebSocket instance
            if self._owner is not None:
                self._owner._ws_app = self._ws_app
                self._owner._hs_wrapper = self.hsWrapper
            self._ws_app.run_forever(
                ping_interval=30,
                ping_timeout=10,
            )
            # run_forever() has returned — clean up references to break reference cycles
            # so that StartServer, HSWrapper, and WebSocketApp can be GC'd promptly
            self._ws_app = None
            self.hsWrapper = None
            self.onopen = None
            self.onmessage = None
            self.onerror = None
            self.onclose = None
            if self._owner is not None:
                self._owner = None
        else:
            logger.info("WebSocket not initialized!")

    def on_open(self, ws):
        # logger.info("[OnOpen]: Function is running in HSWebscoket")
        callback = self.onopen
        if callback:
            callback()

    def on_message(self, ws, inData):
        # logger.info("[OnMessage]: Function is running in HSWebsocket")
        callback = self.onmessage
        if not callback:
            return
        outData = None
        if isinstance(inData, bytes):
            hsw = self.hsWrapper
            if not hsw:
                return
            jsonData = hsw.parseData(inData)
            # logger.info(f"JSON DATA in HSWEBSOCKE ON MESSAGE {jsonData}")
            if jsonData:
                outData = json.dumps(jsonData) if isEncyptOut else jsonData
        else:
            outData = inData if not isEncyptIn else json.loads(inData) if isEncyptOut else inData
        if outData:
            callback(outData)

    def on_close(self, ws, close_status_code, close_msg):
        # logger.info(f"[OnClose]: Function is running HSWebsocket {close_status_code}")
        callback = self.onclose
        if callback:
            callback()

    def on_error(self, ws, error):
        callback = self.onerror
        if callback:
            callback(error)
        logger.info(f"ERROR in HSWebscoket {error}")
        logger.info("[OnError]: Function is running HSWebsocket")


SCRIP_PREFIX = "sf"
INDEX_PREFIX = "if"
DEPTH_PREFIX = "dp"


def convert_to_dict(scrips=None, channelnum=None):
    dict_data = {
        "scrips": scrips,
        "sub_type": BinRespTypes.get("SUBSCRIBE_TYPE"),
        "SCRIP_PREFIX": SCRIP_PREFIX,
        "channelnum": channelnum,
    }
    return dict_data


class HSWebSocket:
    def __init__(self):
        self.onclose = None
        self.url = None
        self.onopen = None
        self.onmessage = None
        self.on_error = None
        self._ws_app = None  # Per-instance WebSocketApp reference
        self._hs_wrapper = None  # Per-instance HSWrapper reference
        self._send_lock = None  # Optional lock for serializing sends

    def open_connection(self, url, token, sid, on_open, on_message, on_error, on_close):
        self.url = url
        self.onopen = on_open
        self.onmessage = on_message
        self.on_error = on_error
        self.onclose = on_close
        StartServer(self.url, token, sid, self.onopen, self.onmessage, self.on_error, self.onclose, owner=self, send_lock=self._send_lock)

    def hs_send(self, d):
        req_json = json.loads(d)
        req_type = req_json[Keys.get("TYPE")]
        # logger.info(f"Req Type {req_type}")
        req = {}
        if Keys.get("SCRIPS") in req_json:
            scrips = req_json[Keys.get("SCRIPS")]
            # logger.info(f"scrips {scrips}")
            channelnum = req_json[Keys.get("CHANNEL_NUM")]
            # logger.info(f"CHANNEL NUM {channelnum}")
        else:
            scrips = None
            channelnum = 1
        # scrips = None
        # channelnum = req_json[Keys.get("CHANNEL_NUM")]
        if req_type == ReqTypeValues.get("CONNECTION"):
            if Keys.get("USER_ID") in req_json:
                user = req_json[Keys.get("USER_ID")]
                req = prepare_connection_request(user)
            elif Keys.get("SESSION_ID") in req_json:
                # logger.info("INSIDE SESSION_ID")
                session_id = req_json[Keys.get("SESSION_ID")]
                req = prepare_connection_request(session_id)
            elif Keys.get("AUTHORIZATION") in req_json:
                # logger.info("INSIDE AUTHORIZATION")
                jwt = req_json[Keys.get("AUTHORIZATION")]
                redis_key = req_json[Keys.get("SID")]
                if jwt and redis_key:
                    req = prepareConnectionRequest2(jwt, redis_key)
                    # req = {"Authorization": jwt, "Sid": redis_key}
                else:
                    logger.info("Authorization mode is enabled: Authorization or Sid not found !")
            else:
                logger.info("Invalid conn mode !")
        elif req_type == ReqTypeValues.get("SCRIP_SUBS"):
            req = prepareSubsUnSubsRequest(
                scrips, BinRespTypes.get("SUBSCRIBE_TYPE"), SCRIP_PREFIX, channelnum
            )
            # logger.info(f"*********** SUB SCRIPS req {req}")
        elif req_type == ReqTypeValues.get("SCRIP_UNSUBS"):
            req = prepareSubsUnSubsRequest(
                scrips, BinRespTypes.get("UNSUBSCRIBE_TYPE"), SCRIP_PREFIX, channelnum
            )
        elif req_type == ReqTypeValues.get("INDEX_SUBS"):
            req = prepareSubsUnSubsRequest(
                scrips, BinRespTypes.get("SUBSCRIBE_TYPE"), INDEX_PREFIX, channelnum
            )
        elif req_type == ReqTypeValues.get("INDEX_UNSUBS"):
            req = prepareSubsUnSubsRequest(
                scrips, BinRespTypes.get("UNSUBSCRIBE_TYPE"), INDEX_PREFIX, channelnum
            )
        elif req_type == ReqTypeValues.get("DEPTH_SUBS"):
            req = prepareSubsUnSubsRequest(
                scrips, BinRespTypes.get("SUBSCRIBE_TYPE"), DEPTH_PREFIX, channelnum
            )
        elif req_type == ReqTypeValues.get("DEPTH_UNSUBS"):
            req = prepareSubsUnSubsRequest(
                scrips, BinRespTypes.get("UNSUBSCRIBE_TYPE"), DEPTH_PREFIX, channelnum
            )
        elif req_type == ReqTypeValues.get("CHANNEL_PAUSE"):
            req = prepareChannelRequest(BinRespTypes.get("CHPAUSE_TYPE"), channelnum)
        elif req_type == ReqTypeValues.get("CHANNEL_RESUME"):
            req = prepareChannelRequest(BinRespTypes.get("CHRESUME_TYPE"), channelnum)
        elif req_type == ReqTypeValues.get("SNAP_MW"):
            req = prepareSnapshotRequest(scrips, BinRespTypes.get("SNAPSHOT"), SCRIP_PREFIX)
        elif req_type == ReqTypeValues.get("SNAP_DP"):
            req = prepareSnapshotRequest(scrips, BinRespTypes.get("SNAPSHOT"), DEPTH_PREFIX)
        elif req_type == ReqTypeValues.get("SNAP_IF"):
            req = prepareSnapshotRequest(scrips, BinRespTypes.get("SNAPSHOT"), INDEX_PREFIX)
        elif req_type == ReqTypeValues.get("OPC_SUBS"):
            req = get_opc_chain_subs_request(
                req_json[Keys.get("OPC_KEY")],
                req_json[Keys.get("STK_PRC")],
                req_json[Keys.get("HIGH_STK")],
                req_json[Keys.get("LOW_STK")],
                channelnum,
            )
        elif req_type == ReqTypeValues.get("THROTTLING_INTERVAL"):
            req = prepareThrottlingIntervalRequest(scrips)
        ws = self._ws_app
        if ws and req:
            ws.send(req, 0x2)
        else:
            logger.info(
                "Unable to send request !, Reason: Connection faulty or request not valid !"
            )

    def close(self):
        if self._ws_app:
            self._ws_app.close()
            self._ws_app = None
        if self._hs_wrapper:
            self._hs_wrapper.topic_list.clear()
        self._hs_wrapper = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


#
# import json
# import websocket
#
#
# class HSIWebSocket:
#     def __init__(self, url):
#         self.hsiSocket = None
#         self.reqData = None
#         self.hsiWs = None
#         self.OPEN = 0
#         self.readyState = 0
#         self.url = url
#         self.start_hsi_server(self.url)
#
#     def start_hsi_server(self, url):
#         self.hsiWs = websocket.WebSocketApp(url,
#                                             on_message=self.on_message,
#                                             on_error=self.on_error,
#                                             on_close=self.on_close)
#         self.hsiWs.on_open = self.on_open
#         self.hsiWs.run_forever()
#
#     def on_message(self, ws, message):
#         logger.info(f"Received message: {message}")
#
#     def on_error(self, ws, error):
#         logger.info(f"Error: {error}")
#
#     def on_close(self, ws):
#         logger.info("Connection closed")
#         self.OPEN = 0
#         self.readyState = 0
#         self.hsiWs = None
#
#     def on_open(self, ws):
#         logger.info("Connection established")
#         self.OPEN = 1
#         self.readyState = 1
#
#     def send(self, d):
#         reqJson = json.loads(d)
#         req = None
#         if reqJson['type'] == 'CONNECTION':
#             if 'Authorization' in reqJson and 'Sid' in reqJson and 'src' in reqJson:
#                 req = {
#                     'type': 'cn',
#                     'Authorization': reqJson['Authorization'],
#                     'Sid': reqJson['Sid'],
#                     'src': reqJson['src']
#                 }
#                 self.reqData = req
#             else:
#                 if 'x-access-token' in reqJson and 'src' in reqJson:
#                     req = {
#                         'type': 'cn',
#                         'x-access-token': reqJson['x-access-token'],
#                         'src': reqJson['src']
#                     }
#                     self.reqData = req
#                 else:
#                     logger.info("Invalid connection mode !")
#         else:
#             if reqJson['type'] == 'FORCE_CONNECTION':
#                 self.reqData = self.reqData['type'] = 'fcn'
#                 req = self.reqData
#             else:
#                 logger.info("Invalid Request !")
#         if self.hsiWs and req:
#             logger.info(f"REQ {req}")
#             self.hsiWs.send(json.dumps(req))
#         else:
#             logger.info("Unable to send request! Reason: Connection faulty or request not valid!")
#
#     def close(self):
#         self.hsiWs.close()
#         self.OPEN = 0
#         self.readyState = 0
#         self.hsiWs = None


class StartHSIServer:
    def __init__(self, url, onopen, onmessage, onerror, onclose, owner=None):
        self.OPEN = None
        self.readyState = None
        self.url = url
        self.onopen = onopen
        self.onmessage = onmessage
        self.onerror = onerror
        self.onclose = onclose
        self._owner = owner  # HSIWebSocket instance that owns this connection
        self._ws_app = None
        try:
            # websocket.enableTrace(True)
            self._ws_app = websocket.WebSocketApp(
                self.url,
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
            )
        except Exception:
            logger.info("WebSocket not supported!")
        # Store reference on the owning HSIWebSocket instance
        if self._owner is not None and self._ws_app:
            self._owner._ws_app = self._ws_app
        if self._ws_app:
            self._ws_app.run_forever(
                ping_interval=30,
                ping_timeout=10,
            )
            # run_forever() returned — break reference cycles for prompt GC
            self._ws_app = None
            self.onopen = None
            self.onmessage = None
            self.onerror = None
            self.onclose = None
            if self._owner is not None:
                self._owner = None

    def on_message(self, ws, message):
        # logger.info(f"Received message: {message}")
        callback = self.onmessage
        if callback:
            callback(message)

    def on_error(self, ws, error):
        logger.info(f"Error: {error}")
        callback = self.onerror
        if callback:
            callback(error)

    def on_close(self, ws, close_status_code, close_msg):
        logger.info("Connection closed")
        self.OPEN = 0
        self.readyState = 0
        self._ws_app = None
        callback = self.onclose
        if callback:
            callback()

    def on_open(self, ws):
        logger.info("Connection established HSWebSocket")
        self.OPEN = 1
        self.readyState = 1
        callback = self.onopen
        if callback:
            callback()


class HSIWebSocket:
    def __init__(self):
        self.hsiSocket = None
        self.reqData = None
        self.OPEN = 0
        self.readyState = 0
        self.url = None
        self.onopen = None
        self.onmessage = None
        self.onclose = None
        self.onerror = None
        self._ws_app = None  # Per-instance WebSocketApp reference

    def open_connection(self, url, onopen, onmessage, onclose, onerror):
        self.url = url
        self.onopen = onopen
        self.onmessage = onmessage
        self.onclose = onclose
        self.onerror = onerror
        StartHSIServer(self.url, self.onopen, self.onmessage, self.onerror, self.onclose, owner=self)

    def send(self, d):
        reqJson = json.loads(d)
        req = None
        if reqJson["type"] == "CONNECTION":
            if "Authorization" in reqJson and "Sid" in reqJson and "source" in reqJson:
                req = {
                    "type": "cn",
                    "Authorization": reqJson["Authorization"],
                    "Sid": reqJson["Sid"],
                    "src": reqJson["source"],
                }
                self.reqData = req
            else:
                if "x-access-token" in reqJson and "src" in reqJson:
                    req = {
                        "type": "cn",
                        "x-access-token": reqJson["x-access-token"],
                        "source": reqJson["source"],
                    }
                    self.reqData = req
                else:
                    logger.info("Invalid connection mode !")
        else:
            if reqJson["type"] == "FORCE_CONNECTION":
                self.reqData = self.reqData["type"] = "fcn"
                req = self.reqData
            else:
                logger.info("Invalid Request !")
        if self._ws_app and req:
            js_obj = json.dumps(req)
            self._ws_app.send(js_obj)
        else:
            logger.info("Unable to send request! Reason: Connection faulty or request not valid!")

    def close(self):
        self.OPEN = 0
        self.readyState = 0
        if self._ws_app:
            self._ws_app.close()
            self._ws_app = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

```


---

# FILE: broker\kotak\streaming\kotak_adapter.py

```py
"""
High-level, AliceBlue-style adapter for Kotak broker WebSocket streaming.
Each instance is fully isolated and safe for multi-client use.
"""

import threading
import time

from database.auth_db import get_auth_token
from utils.logging import get_logger
from websocket_proxy.base_adapter import BaseBrokerWebSocketAdapter

from .kotak_websocket import KotakWebSocket

logger = get_logger(__name__)


class KotakWebSocketAdapter(BaseBrokerWebSocketAdapter):
    """
    Adapter for Kotak WebSocket streaming, suitable for OpenAlgo or similar frameworks.
    Each instance is isolated and manages its own KotakWebSocket client.
    """

    # Thread cleanup timeout
    THREAD_JOIN_TIMEOUT = 5

    def __init__(self):
        super().__init__()  # ← Initialize base adapter (sets up ZMQ)
        self._ws_client = None
        self._user_id = None
        self._broker_name = "kotak"
        self._auth_config = None
        self._connected = False
        self._lock = threading.RLock()

        # Reconnection state
        self._running = False
        self._reconnecting = False
        self._reconnect_timer = None
        self._reconnect_delay = 5        # base delay in seconds
        self._max_reconnect_delay = 60   # maximum delay in seconds
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 10

        # Cache structures - following AliceBlue pattern exactly
        self._ltp_cache = {}  # {(exchange, symbol): ltp_value}
        self._quote_cache = {}  # {(exchange, symbol): full_quote_dict}
        self._depth_cache = {}  # {(exchange, symbol): depth_dict}
        self._symbol_state = {}  # {broker_exchange|token: data} for partial update merging
        self._depth_poll_state = {}  # {exchange|symbol: data} for depth polling state

        # Mapping from Kotak format to OpenAlgo format - critical for data flow
        self._kotak_to_openalgo = {}  # {(kotak_exchange, token): (exchange, symbol)}

        # Track active subscription modes per symbol - CRITICAL FOR MULTI-CLIENT SUPPORT
        self._symbol_modes = {}  # {(kotak_exchange, token): set of active modes}

        # Batch subscription management - debounced fan-in so a burst of
        # subscribe() calls collapses into one HSI frame per sub_type.
        # Each entry: {"kotak_exchange": str, "token": str, "sub_type": str, "channelnum": str}
        self._subscription_queue = []
        self._batch_timer = None
        # 50ms is enough to coalesce a burst (e.g. option chain load) without
        # adding a perceptible floor to single-symbol cold subscribes.
        self._batch_delay = 0.05
        self._max_batch_size = 100  # HSI MAX_SCRIPS limit per frame

    def initialize(self, broker_name: str, user_id: str, auth_data=None):
        """Initialize adapter for a specific user/session - following AliceBlue pattern."""
        self._broker_name = broker_name.lower()
        self._user_id = user_id

        # Load authentication from DB
        auth_string = get_auth_token(user_id)
        if not auth_string:
            logger.error(f"No authentication token found for user {user_id}")
            raise ValueError(f"No authentication token found for user {user_id}")

        auth_parts = auth_string.split(":::")
        if len(auth_parts) != 4:
            logger.error("Invalid authentication token format")
            raise ValueError("Invalid authentication token format")

        self._auth_config = dict(
            zip(["auth_token", "sid", "hs_server_id", "access_token"], auth_parts)
        )

        # Create websocket client
        self._ws_client = KotakWebSocket(self._auth_config)

        # Set up internal callbacks - this MUST happen during initialization like AliceBlue
        self._setup_internal_callbacks()

        logger.debug(f"Initialized KotakWebSocketAdapter for user {user_id}")

    def _setup_internal_callbacks(self):
        """Setup internal callbacks - following AliceBlue's _on_data_received pattern."""

        def on_quote_internal(quote):
            """Internal callback - mirrors AliceBlue's _on_data_received method."""
            try:
                logger.debug(f"Internal quote callback received: {quote}")
                self._on_data_received(quote)
            except Exception as e:
                logger.error(f"Error in internal quote handler: {e}")

        def on_depth_internal(depth):
            """Internal callback for depth data."""
            try:
                logger.debug(f"Internal depth callback received: {depth}")
                self._on_data_received(depth)
            except Exception as e:
                logger.error(f"Error in internal depth handler: {e}")

        def on_open_internal():
            """Internal callback when WebSocket transport opens."""
            logger.info("Kotak WebSocket transport opened")
            # Reset reconnection state only when connection actually succeeds
            with self._lock:
                self._connected = True
                self._reconnect_attempts = 0
                self._reconnecting = False

        def on_close_internal():
            """Internal callback when WebSocket connection closes."""
            logger.info("Kotak WebSocket connection closed")

            with self._lock:
                self._connected = False
                if not self._running:
                    logger.debug("Not reconnecting - adapter stopped")
                    return

                if self._reconnecting:
                    logger.debug("Reconnection already in progress, skipping")
                    return

                self._reconnecting = True

            self._schedule_reconnection()

        def on_error_internal(error):
            """Internal callback for WebSocket errors."""
            logger.error(f"Kotak WebSocket error: {error}")

        # Set callbacks on the websocket client - this is crucial
        if self._ws_client:
            logger.debug("Setting up internal callbacks on KotakWebSocket client")
            self._ws_client.set_callbacks(
                on_quote=on_quote_internal,
                on_depth=on_depth_internal,
                on_open=on_open_internal,
                on_close=on_close_internal,
                on_error=on_error_internal,
            )

    def _on_data_received(self, parsed_data):
        """Handle received and parsed market data - FIXED for partial updates like AliceBlue."""
        try:
            logger.debug(f"Data received: {parsed_data}")

            # --- FIX: Handle list of dicts (multi-script update) ---
            if isinstance(parsed_data, list):
                for item in parsed_data:
                    self._on_data_received(item)
                return

            # Work on a copy to avoid mutating the caller's dict
            parsed_data = parsed_data.copy()

            # Extract key identifiers - following AliceBlue pattern
            token = str(parsed_data.get("tk", ""))
            broker_exchange = parsed_data.get("e", "UNKNOWN")
            ltp = parsed_data.get("ltp")

            # **CRITICAL FIX**: Check if this is depth data (has bids/asks) or LTP data
            has_depth_data = "bids" in parsed_data and "asks" in parsed_data
            has_ltp_data = ltp and float(ltp) > 0

            # Create symbol key - following AliceBlue pattern
            symbol_key = f"{broker_exchange}|{token}"

            # --- Lock section 1: State merging and write-back ---
            with self._lock:
                # Check if this is a partial update by detecting missing expected fields
                is_partial_update = self._is_partial_update(parsed_data)

                # --- CRITICAL: If partial update and no previous state, initialize state ---
                if is_partial_update and symbol_key not in self._symbol_state:
                    logger.debug(f"Initializing state for partial update: {symbol_key}")
                    # Create initial state with proper default values
                    initial_state = {
                        "tk": parsed_data.get("tk", ""),
                        "e": parsed_data.get("e", ""),
                        "ts": parsed_data.get("ts", ""),
                        "ltp": 0.0,
                        "open": 0.0,
                        "high": 0.0,
                        "low": 0.0,
                        "prev_close": 0.0,
                        "volume": 0.0,
                        "bid": 0.0,
                        "ask": 0.0,
                        "bids": [],
                        "asks": [],
                    }

                    # **CRITICAL**: Copy any non-zero/non-empty values from the partial update
                    for key, value in parsed_data.items():
                        if key in initial_state:
                            # Don't overwrite with zero values for price fields
                            if key in ["open", "high", "low", "prev_close", "bid", "ask"]:
                                if value != 0.0 and value != 21474836.48:  # Kotak's invalid value
                                    initial_state[key] = value
                            elif key in ["ltp"]:
                                # **CRITICAL FIX**: Only update LTP if it's a valid positive value
                                if value and float(value) > 0:
                                    initial_state[key] = value
                            elif key in ["volume"]:
                                if value != 0.0 and value != 2147483648:  # Kotak's invalid volume
                                    initial_state[key] = value
                            elif key in ["ts"]:
                                if value:  # Non-empty symbol name
                                    initial_state[key] = value
                            else:
                                initial_state[key] = value

                    self._symbol_state[symbol_key] = initial_state

                # --- CRITICAL: Merge depth levels per level, not just per side ---
                if has_depth_data:
                    prev_state = self._symbol_state.get(symbol_key, {})
                    prev_bids = prev_state.get("bids", []) if prev_state else []
                    prev_asks = prev_state.get("asks", []) if prev_state else []
                    new_bids = parsed_data.get("bids", [])
                    new_asks = parsed_data.get("asks", [])
                    merged_bids = []
                    merged_asks = []
                    for i in range(5):
                        # --- BUY SIDE ---
                        if i < len(new_bids):
                            b = new_bids[i]
                            prev_b = (
                                prev_bids[i]
                                if i < len(prev_bids)
                                else {"price": 0, "quantity": 0, "orders": 0}
                            )
                            merged_bids.append(
                                {
                                    "price": b.get("price", 0)
                                    if b.get("price", 0) != 0
                                    else prev_b.get("price", 0),
                                    "quantity": b.get("quantity", 0)
                                    if b.get("quantity", 0) != 0
                                    else prev_b.get("quantity", 0),
                                    "orders": b.get("orders", 0)
                                    if b.get("orders", 0) != 0
                                    else prev_b.get("orders", 0),
                                }
                            )
                        elif i < len(prev_bids):
                            merged_bids.append(prev_bids[i])
                        else:
                            merged_bids.append({"price": 0, "quantity": 0, "orders": 0})

                        # --- SELL SIDE ---
                        if i < len(new_asks):
                            a = new_asks[i]
                            prev_a = (
                                prev_asks[i]
                                if i < len(prev_asks)
                                else {"price": 0, "quantity": 0, "orders": 0}
                            )
                            merged_asks.append(
                                {
                                    "price": a.get("price", 0)
                                    if a.get("price", 0) != 0
                                    else prev_a.get("price", 0),
                                    "quantity": a.get("quantity", 0)
                                    if a.get("quantity", 0) != 0
                                    else prev_a.get("quantity", 0),
                                    "orders": a.get("orders", 0)
                                    if a.get("orders", 0) != 0
                                    else prev_a.get("orders", 0),
                                }
                            )
                        elif i < len(prev_asks):
                            merged_asks.append(prev_asks[i])
                        else:
                            merged_asks.append({"price": 0, "quantity": 0, "orders": 0})
                    # Update parsed_data with merged depth
                    parsed_data["bids"] = merged_bids
                    parsed_data["asks"] = merged_asks

                # **CRITICAL FIX FOR PARTIAL UPDATES**: Implement AliceBlue-style state merging
                if is_partial_update and symbol_key in self._symbol_state:
                    logger.debug(f"Partial update detected for {symbol_key}")
                    merged_data = self._symbol_state[symbol_key].copy()
                    for key, value in parsed_data.items():
                        if key not in ["tk", "e"]:
                            # Skip zero values for price fields (preserve previous known value)
                            if (
                                key in ["open", "high", "low", "prev_close", "bid", "ask", "ltp"]
                                and value == 0.0
                            ):
                                continue
                            elif key == "volume" and value == 0.0:
                                continue
                            elif key == "ts" and not value:
                                continue
                            else:
                                merged_data[key] = value
                        else:
                            merged_data[key] = value
                    parsed_data = merged_data
                    logger.debug(
                        f"Merged data: {dict((k, v) for k, v in parsed_data.items() if k not in ['tk'])}"
                    )
                    ltp = parsed_data.get("ltp")
                    has_depth_data = "bids" in parsed_data and "asks" in parsed_data
                    has_ltp_data = ltp and float(ltp) > 0

                # Store the complete data only for mapped symbols (avoids unbounded growth
                # from unsolicited broker data for symbols we're not subscribed to)
                if (broker_exchange, token) in self._kotak_to_openalgo:
                    self._symbol_state[symbol_key] = {
                        **parsed_data,
                        "bids": parsed_data.get("bids", []),
                        "asks": parsed_data.get("asks", []),
                    }

            # Skip if neither LTP nor depth data is present (after merging)
            if not has_ltp_data and not has_depth_data:
                logger.debug("No LTP or depth data after merging")
                return

            # --- Lock section 2: Mapping lookup, cache updates, publish queue building ---
            mapping_key = (broker_exchange, token)
            publish_queue = []

            with self._lock:
                if mapping_key in self._kotak_to_openalgo:
                    exchange, symbol = self._kotak_to_openalgo[mapping_key]
                    cache_key = (exchange, symbol)

                    # For LTP data, update LTP cache
                    if has_ltp_data:
                        self._ltp_cache[cache_key] = float(ltp)

                    # For depth data, update depth cache
                    # Use cached LTP as fallback when current packet has no LTP
                    # (Kotak sends depth and LTP as separate packets)
                    cached_ltp = self._ltp_cache.get(cache_key, 0.0)

                    if has_depth_data:
                        depth_data = {
                            "buy": parsed_data.get("bids", []),
                            "sell": parsed_data.get("asks", []),
                            "totalbuyqty": parsed_data.get("totalbuyqty", 0),
                            "totalsellqty": parsed_data.get("totalsellqty", 0),
                            "ltp": float(ltp) if has_ltp_data else cached_ltp,
                        }
                        self._depth_cache[cache_key] = depth_data

                    # Always update quote cache with complete merged data
                    self._quote_cache[cache_key] = parsed_data.copy()

                    # Snapshot active modes and cached depth for publish queue building
                    active_modes = set(self._symbol_modes.get(mapping_key, set()))
                    effective_ltp = float(ltp) if has_ltp_data else cached_ltp
                    local_depth_cache = self._depth_cache.get(cache_key, {}).copy() if not has_depth_data else None
                else:
                    exchange = symbol = cache_key = None
                    active_modes = set()
                    effective_ltp = 0.0
                    local_depth_cache = None

            # --- Build publish queue outside lock (pure computation on local data) ---
            if exchange and symbol:
                for mode in active_modes:
                    mode_map = {1: "LTP", 2: "QUOTE", 3: "DEPTH"}
                    mode_str = mode_map.get(mode, "LTP")
                    topic = f"{exchange}_{symbol}_{mode_str}"

                    if mode == 1 and has_ltp_data:
                        publish_data = {
                            "ltp": float(ltp),
                            "ltt": parsed_data.get("timestamp", int(time.time() * 1000)),
                        }
                    elif mode == 2 and effective_ltp > 0:
                        publish_data = {
                            "ltp": effective_ltp,
                            "ltt": parsed_data.get("timestamp", int(time.time() * 1000)),
                            "volume": parsed_data.get("volume", 0),
                            "open": parsed_data.get("open", 0.0),
                            "high": parsed_data.get("high", 0.0),
                            "low": parsed_data.get("low", 0.0),
                            "close": parsed_data.get("prev_close", 0.0),
                        }
                    elif mode == 3:
                        # Use current depth data or fall back to cached depth
                        # (Kotak sends depth and LTP as separate packets)
                        if has_depth_data:
                            depth_buy = parsed_data.get("bids", [])
                            depth_sell = parsed_data.get("asks", [])
                            depth_total_buy = parsed_data.get("totalbuyqty", 0)
                            depth_total_sell = parsed_data.get("totalsellqty", 0)
                        elif local_depth_cache:
                            depth_buy = local_depth_cache.get("buy", [])
                            depth_sell = local_depth_cache.get("sell", [])
                            depth_total_buy = local_depth_cache.get("totalbuyqty", 0)
                            depth_total_sell = local_depth_cache.get("totalsellqty", 0)
                        else:
                            continue  # No depth data available at all

                        publish_data = {
                            "timestamp": int(time.time() * 1000),
                            "depth": {
                                "buy": depth_buy,
                                "sell": depth_sell,
                            },
                            "totalbuyqty": depth_total_buy,
                            "totalsellqty": depth_total_sell,
                        }
                        # Only include LTP if valid; omitting it lets
                        # the frontend fall back to polled REST data
                        if effective_ltp > 0:
                            publish_data["ltp"] = effective_ltp
                    else:
                        continue
                    publish_data.update(
                        {
                            "symbol": symbol,
                            "exchange": exchange,
                            "timestamp": int(time.time() * 1000),
                        }
                    )
                    publish_queue.append((topic, publish_data))

                if has_ltp_data:
                    logger.debug(f"Updated LTP cache: {exchange}:{symbol} = {ltp}")
                if has_depth_data:
                    logger.debug(f"Updated depth cache: {exchange}:{symbol}")
            else:
                logger.debug(f"No mapping found for {mapping_key}")

            # Publish outside lock to avoid blocking other adapter operations
            for topic, publish_data in publish_queue:
                logger.debug(f"Publishing to ZMQ topic: {topic}")
                self.publish_market_data(topic, publish_data)

        except Exception as e:
            logger.error(f"Error processing received data: {e}")

    def _is_partial_update(self, parsed_data):
        """
        Determine if this is a partial update based on missing expected fields.
        Less aggressive detection to avoid skipping valid updates.
        """
        # If we have LTP and symbol name, treat as valid update
        ltp = parsed_data.get("ltp", 0.0)
        symbol_name = parsed_data.get("ts", "")

        if ltp and float(ltp) > 0 and symbol_name:
            return False  # Complete enough to process

        # Check for quote mode partial updates
        quote_fields = ["open", "high", "low", "prev_close"]
        has_quote_fields = any(
            field in parsed_data and parsed_data[field] != 0.0 for field in quote_fields
        )

        if not has_quote_fields and not symbol_name:
            return True  # Definitely partial

        return False  # Default to processing the update

    def _start_batch_timer(self):
        """Arm the debounce timer that flushes the subscription queue."""
        if self._batch_timer:
            self._batch_timer.cancel()

        self._batch_timer = threading.Timer(
            self._batch_delay, self._process_batch_subscriptions
        )
        self._batch_timer.daemon = True
        self._batch_timer.start()

    def _enqueue_subscription(self, kotak_exchange, token, sub_type, channelnum="1"):
        """Append a subscription to the queue and arm the batch timer if idle."""
        with self._lock:
            self._subscription_queue.append(
                {
                    "kotak_exchange": kotak_exchange,
                    "token": str(token),
                    "sub_type": sub_type,
                    "channelnum": channelnum,
                }
            )
            should_start = len(self._subscription_queue) == 1
        if should_start:
            self._start_batch_timer()

    def _process_batch_subscriptions(self):
        """Drain the queue, group by (sub_type, channelnum), send batched frames."""
        with self._lock:
            self._batch_timer = None
            if not self._subscription_queue:
                return

            # Group by (sub_type, channelnum) and dedupe per group so we
            # never send the same scrip twice in one frame.
            groups = {}
            for sub in self._subscription_queue:
                key = (sub["sub_type"], sub["channelnum"])
                groups.setdefault(key, [])
                pair = (sub["kotak_exchange"], sub["token"])
                if pair not in groups[key]:
                    groups[key].append(pair)
            self._subscription_queue.clear()
            ws = self._ws_client

        if not ws:
            logger.warning("Batch subscribe skipped — WebSocket client not available")
            return

        for (sub_type, channelnum), scrips in groups.items():
            for i in range(0, len(scrips), self._max_batch_size):
                chunk = scrips[i : i + self._max_batch_size]
                try:
                    logger.info(
                        f"Batch subscribing {len(chunk)} scrips "
                        f"(sub_type={sub_type}, channel={channelnum})"
                    )
                    ws.subscribe_batch(chunk, sub_type=sub_type, channelnum=channelnum)
                except Exception as e:
                    logger.error(
                        f"Batch subscribe failed for sub_type={sub_type}: {e}"
                    )

    def connect(self):
        """Connect to WebSocket - following AliceBlue pattern."""
        if not self._ws_client:
            logger.error("WebSocket client not initialized. Call initialize() first.")
            return

        # Guard against double-connect
        if self._ws_client.is_connected():
            logger.debug("WebSocket already connected, skipping")
            return

        try:
            self._running = True
            self._ws_client.connect()
            # Don't set _connected = True here; the on_close_internal/on_open
            # callbacks handle the _connected flag based on actual connection state.
            # connect() only starts the async connection thread.
            logger.debug("Kotak WebSocket connection initiated")
        except Exception as e:
            logger.error(f"Error connecting to Kotak WebSocket: {e}")
            self._connected = False

    def disconnect(self):
        """
        Disconnect from WebSocket and clean up all resources.
        Uses try/finally to ensure ZMQ cleanup even if WebSocket close fails.
        """
        with self._lock:
            self._running = False
            self._reconnecting = False

            # Cancel any pending reconnection timer
            if self._reconnect_timer:
                self._reconnect_timer.cancel()
                self._reconnect_timer = None
                logger.debug("Cancelled pending reconnection timer")

            # Cancel any pending batch subscription timer and drop unsent items
            if self._batch_timer:
                self._batch_timer.cancel()
                self._batch_timer = None
            self._subscription_queue.clear()

        try:
            if self._ws_client:
                try:
                    self._ws_client.close()
                except Exception as e:
                    logger.error(f"Error closing WebSocket client: {e}")
                finally:
                    self._ws_client = None

            # Clear all internal caches to release memory
            with self._lock:
                self._connected = False
                self._ltp_cache.clear()
                self._quote_cache.clear()
                self._depth_cache.clear()
                self._symbol_state.clear()
                self._depth_poll_state.clear()
                self._kotak_to_openalgo.clear()
                self._symbol_modes.clear()
                self.subscriptions.clear()
                self._reconnect_attempts = 0

        finally:
            # Always clean up ZeroMQ resources - CRITICAL for multi-instance support
            try:
                self.cleanup_zmq()
            except Exception as e:
                logger.error(f"Error cleaning up ZMQ resources: {e}")

        logger.debug("Kotak WebSocket disconnected")

    def _schedule_reconnection(self):
        """Schedule reconnection with exponential backoff."""
        with self._lock:
            if not self._running:
                logger.debug("Skipping reconnection schedule - adapter stopped")
                self._reconnecting = False
                return

            if self._reconnect_attempts >= self._max_reconnect_attempts:
                logger.error("Maximum reconnection attempts reached, cleaning up")
                self._running = False
                self._reconnecting = False
                # Release ZMQ resources since we're giving up
                try:
                    self.cleanup_zmq()
                except Exception as e:
                    logger.error(f"Error cleaning up ZMQ after max reconnect attempts: {e}")
                return

            delay = min(
                self._reconnect_delay * (2 ** self._reconnect_attempts),
                self._max_reconnect_delay,
            )

            logger.info(
                f"Reconnecting in {delay}s (attempt {self._reconnect_attempts + 1})"
            )

            # Cancel any existing timer before creating new one
            if self._reconnect_timer:
                self._reconnect_timer.cancel()

            self._reconnect_timer = threading.Timer(delay, self._attempt_reconnection)
            self._reconnect_timer.daemon = True
            self._reconnect_timer.start()

    def _attempt_reconnection(self):
        """Attempt to reconnect to WebSocket."""
        with self._lock:
            # Clear timer reference since we're now executing
            self._reconnect_timer = None

            if not self._running:
                logger.debug("Reconnection cancelled - adapter no longer running")
                self._reconnecting = False
                return

            self._reconnect_attempts += 1

        try:
            # Save current subscriptions before cleanup
            with self._lock:
                saved_subs = dict(self.subscriptions)

            # Clean up old WebSocket client
            if self._ws_client:
                logger.debug("Cleaning up old WebSocket client before reconnection")
                try:
                    self._ws_client.close()
                    # Verify old thread actually stopped
                    self._ws_client.wait_until_closed(timeout=5)
                except Exception as cleanup_err:
                    logger.warning(f"Error cleaning up old WebSocket: {cleanup_err}")

            # Recreate WebSocket client with fresh credentials
            self._recreate_ws_client()

            if self._ws_client:
                # Clear stale state from old session before reconnecting
                with self._lock:
                    self._symbol_state.clear()

                # Connect the new client (async — _connected is set by on_open callback,
                # which also resets _reconnect_attempts and _reconnecting)
                self._ws_client.connect()
                logger.info("Kotak WebSocket reconnection initiated")

                # Re-subscribe saved symbols
                failed_resubs = []
                for sub_key, sub_info in saved_subs.items():
                    try:
                        self.subscribe(
                            sub_info["symbol"],
                            sub_info["exchange"],
                            sub_info["mode"],
                        )
                        logger.info(
                            f"Resubscribed to {sub_info['exchange']}:{sub_info['symbol']}"
                        )
                    except Exception as e:
                        failed_resubs.append(f"{sub_info['exchange']}:{sub_info['symbol']}")
                        logger.error(
                            f"Error resubscribing to {sub_info['exchange']}:{sub_info['symbol']}: {e}"
                        )
                if failed_resubs:
                    logger.error(
                        f"Failed to resubscribe {len(failed_resubs)} symbols after reconnection: "
                        f"{', '.join(failed_resubs)}"
                    )
            else:
                logger.error("Failed to recreate WebSocket client")
                with self._lock:
                    self._reconnecting = False
                self._schedule_reconnection()

        except Exception as e:
            logger.error(f"Reconnection error: {e}")
            with self._lock:
                self._reconnecting = False
            self._schedule_reconnection()

    def _recreate_ws_client(self):
        """Recreate the WebSocket client with current credentials from DB."""
        try:
            auth_string = get_auth_token(self._user_id)
            if not auth_string:
                logger.error(
                    f"Cannot recreate client - no auth token for user {self._user_id}"
                )
                self._ws_client = None
                return

            auth_parts = auth_string.split(":::")
            if len(auth_parts) != 4:
                logger.error("Invalid authentication token format during reconnection")
                self._ws_client = None
                return

            self._auth_config = dict(
                zip(
                    ["auth_token", "sid", "hs_server_id", "access_token"],
                    auth_parts,
                )
            )

            # Create new WebSocket client
            self._ws_client = KotakWebSocket(self._auth_config)

            # Restore internal callbacks
            self._setup_internal_callbacks()

            logger.debug("WebSocket client recreated successfully")

        except Exception as e:
            logger.error(f"Error recreating WebSocket client: {e}")
            self._ws_client = None

    def cleanup(self):
        """
        Clean up all resources including WebSocket connection and ZMQ resources.
        Should be called before discarding the adapter instance.
        """
        try:
            # Cancel any pending reconnection timer
            with self._lock:
                if self._reconnect_timer:
                    self._reconnect_timer.cancel()
                    self._reconnect_timer = None
                if self._batch_timer:
                    self._batch_timer.cancel()
                    self._batch_timer = None
                self._subscription_queue.clear()

            # Disconnect WebSocket if connected
            if self._ws_client:
                try:
                    self._ws_client.close()
                except Exception as ws_err:
                    logger.error(
                        f"Error closing WebSocket client during cleanup: {ws_err}"
                    )
                finally:
                    self._ws_client = None

            # Reset adapter state
            with self._lock:
                self._running = False
                self._connected = False
                self._reconnecting = False
                self._reconnect_attempts = 0
                self._ltp_cache.clear()
                self._quote_cache.clear()
                self._depth_cache.clear()
                self._symbol_state.clear()
                self._depth_poll_state.clear()
                self._kotak_to_openalgo.clear()
                self._symbol_modes.clear()
                self.subscriptions.clear()

            # Clean up ZMQ resources
            self.cleanup_zmq()

            logger.info("Kotak adapter cleaned up completely")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            # Try one last time to clean up ZMQ resources
            try:
                self.cleanup_zmq()
            except Exception as zmq_err:
                logger.error(
                    f"Error cleaning up ZMQ during final cleanup attempt: {zmq_err}"
                )

    def __del__(self):
        """
        Destructor - ensures resources are released even when adapter is garbage collected.
        This is a safety net; callers should explicitly call disconnect() or cleanup().
        """
        try:
            try:
                self.cleanup()
            except Exception:
                pass
            try:
                self.cleanup_zmq()
            except Exception:
                pass
        except Exception:
            pass

    def subscribe(self, symbol, exchange, mode, depth_level=0):
        """Subscribe to a symbol - FIXED for multi-client support."""
        if not self._ws_client:
            logger.error("WebSocket client not initialized.")
            return self._create_error_response(
                "NOT_INITIALIZED", "WebSocket client not initialized."
            )

        try:
            logger.debug(f"Subscribing to {exchange}:{symbol} with mode {mode}")

            if mode in (1, 2):
                # Quote/LTP subscription
                success = self.subscribe_quote(exchange, symbol, mode)
            elif mode == 3:
                # Depth subscription + quote subscription for LTP updates
                # (Kotak sends depth and LTP as separate streams;
                # "dps" only sends bid/ask, "mws" sends LTP)
                success = self.subscribe_depth(exchange, symbol, mode)
                quote_success = self.subscribe_quote(exchange, symbol, mode)
                if not quote_success:
                    logger.warning(f"Depth subscribed but quote (LTP) subscription failed for {exchange}:{symbol}")
            else:
                logger.error(f"Unknown subscribe mode: {mode}")
                return self._create_error_response(
                    "INVALID_MODE", f"Unknown subscribe mode: {mode}"
                )

            if success:
                # Track subscription - following AliceBlue pattern with detailed tracking
                sub_key = f"{exchange}|{symbol}|{mode}"
                with self._lock:
                    self.subscriptions[sub_key] = {
                        "symbol": symbol,
                        "exchange": exchange,
                        "mode": mode,
                        "depth_level": depth_level,
                    }
                return self._create_success_response(
                    f"Subscribed to {exchange}:{symbol} mode {mode}"
                )
            else:
                return self._create_error_response(
                    "SUBSCRIPTION_FAILED", f"Failed to subscribe to {exchange}:{symbol}"
                )

        except Exception as e:
            logger.error(f"Error in subscribe: {e}")
            return self._create_error_response("SUBSCRIPTION_ERROR", f"Error subscribing: {str(e)}")

    def unsubscribe(self, symbol, exchange, mode):
        """Unsubscribe from a symbol - FIXED for multi-client support."""
        if not self._ws_client:
            logger.error("WebSocket client not initialized.")
            return self._create_error_response(
                "NOT_INITIALIZED", "WebSocket client not initialized."
            )

        try:
            logger.debug(f"Unsubscribing from {exchange}:{symbol} with mode {mode}")

            if mode in (1, 2):
                self.unsubscribe_quote(exchange, symbol, mode)
            elif mode == 3:
                self.unsubscribe_depth(exchange, symbol, mode)
                self.unsubscribe_quote(exchange, symbol, mode)

            # Clean up tracking and cache - following AliceBlue pattern
            sub_key = f"{exchange}|{symbol}|{mode}"
            with self._lock:
                self.subscriptions.pop(sub_key, None)

                # Only clean up caches if NO modes are active for this symbol
                from broker.kotak.streaming.kotak_mapping import get_kotak_exchange
                from database.token_db import get_token

                kotak_exchange = get_kotak_exchange(exchange)
                token = get_token(symbol, exchange)
                mapping_key = (kotak_exchange, str(token))

                # Clean up caches if no modes remain (mapping_key already removed
                # by unsubscribe_quote/unsubscribe_depth, or still present but empty)
                modes_empty = mapping_key not in self._symbol_modes or not self._symbol_modes.get(mapping_key)
                if modes_empty:
                    cache_key = (exchange, symbol)
                    self._ltp_cache.pop(cache_key, None)
                    self._quote_cache.pop(cache_key, None)
                    self._depth_cache.pop(cache_key, None)
                    # Also clean up the depth polling state used by get_depth()
                    self._depth_poll_state.pop(f"{exchange}|{symbol}", None)

            return self._create_success_response(f"Unsubscribed from {exchange}:{symbol}")

        except Exception as e:
            logger.error(f"Error in unsubscribe: {e}")
            return self._create_error_response(
                "UNSUBSCRIPTION_ERROR", f"Error unsubscribing: {str(e)}"
            )

    def subscribe_quote(self, exchange, symbol, mode):
        """Subscribe to quote (LTP) - FIXED for multi-client support."""
        if not self._ws_client:
            logger.error("WebSocket client not initialized.")
            return False

        try:
            from broker.kotak.streaming.kotak_mapping import get_kotak_exchange
            from database.token_db import get_token

            kotak_exchange = get_kotak_exchange(exchange)
            token = get_token(symbol, exchange)

            if not token:
                logger.error(f"No token found for {symbol} on {exchange}")
                return False

            logger.debug(f"Mapping: {exchange}:{symbol} -> {kotak_exchange}:{token}")

            # Store mapping and track mode - CRITICAL FOR MULTI-CLIENT SUPPORT
            with self._lock:
                mapping_key = (kotak_exchange, str(token))
                self._kotak_to_openalgo[mapping_key] = (exchange, symbol)

                # Track active modes for this symbol
                if mapping_key not in self._symbol_modes:
                    self._symbol_modes[mapping_key] = set()
                self._symbol_modes[mapping_key].add(mode)

                logger.debug(f"Stored mapping: {mapping_key} -> ({exchange}, {symbol})")
                logger.debug(f"Active modes for {mapping_key}: {self._symbol_modes[mapping_key]}")

            # Re-check ws_client after releasing lock to avoid race with disconnect()
            if not self._ws_client:
                logger.error("WebSocket client became None during subscribe_quote")
                return False

            # Enqueue for batched dispatch — flushed by _process_batch_subscriptions.
            self._enqueue_subscription(kotak_exchange, token, sub_type="mws")
            logger.debug(
                f"Queued quote subscription: {exchange}:{symbol} "
                f"(kotak: {kotak_exchange}|{token})"
            )
            return True

        except Exception as e:
            logger.error(f"Error subscribing to quote for {exchange}:{symbol}: {e}")
            return False

    def unsubscribe_quote(self, exchange, symbol, mode):
        """Unsubscribe from quote - FIXED for multi-client support."""
        if not self._ws_client:
            logger.error("WebSocket client not initialized.")
            return

        try:
            from broker.kotak.streaming.kotak_mapping import get_kotak_exchange
            from database.token_db import get_token

            kotak_exchange = get_kotak_exchange(exchange)
            token = get_token(symbol, exchange)

            if not token:
                logger.error(f"No token found for {symbol} on {exchange}")
                return

            # **CRITICAL FIX**: Only unsubscribe from broker if no other modes are active
            should_unsub_broker = False
            with self._lock:
                mapping_key = (kotak_exchange, str(token))

                # Remove this mode from active modes
                if mapping_key in self._symbol_modes:
                    self._symbol_modes[mapping_key].discard(mode)

                    # Only unsubscribe from broker if no LTP/QUOTE modes are active
                    ltp_quote_modes = {1, 2}
                    active_ltp_quote_modes = self._symbol_modes[mapping_key] & ltp_quote_modes

                    if not active_ltp_quote_modes:
                        should_unsub_broker = True

                    # Clean up mapping and cached state only if NO modes are active
                    if not self._symbol_modes[mapping_key]:
                        self._kotak_to_openalgo.pop(mapping_key, None)
                        self._symbol_modes.pop(mapping_key, None)
                        # Clean up symbol state to prevent unbounded memory growth
                        symbol_key = f"{kotak_exchange}|{token}"
                        self._symbol_state.pop(symbol_key, None)
                        logger.debug(f"Cleaned up mapping for: {exchange}:{symbol}")

            # Send unsubscribe outside lock to avoid deadlock
            if should_unsub_broker:
                ws = self._ws_client
                if ws:
                    ws.unsubscribe(kotak_exchange, token, sub_type="mwu")
                    logger.debug(f"Unsubscribed from broker: {exchange}:{symbol}")

        except Exception as e:
            logger.error(f"Error unsubscribing from quote for {exchange}:{symbol}: {e}")

    def subscribe_depth(self, exchange, symbol, mode):
        """Subscribe to market depth - FIXED for multi-client support."""
        if not self._ws_client:
            logger.error("WebSocket client not initialized.")
            return False

        try:
            from broker.kotak.streaming.kotak_mapping import get_kotak_exchange
            from database.token_db import get_token

            kotak_exchange = get_kotak_exchange(exchange)
            token = get_token(symbol, exchange)

            if not token:
                logger.error(f"No token found for {symbol} on {exchange}")
                return False

            # Store mapping and track mode
            with self._lock:
                mapping_key = (kotak_exchange, str(token))
                self._kotak_to_openalgo[mapping_key] = (exchange, symbol)

                # Track active modes for this symbol
                if mapping_key not in self._symbol_modes:
                    self._symbol_modes[mapping_key] = set()
                self._symbol_modes[mapping_key].add(mode)

            # Re-check ws_client after releasing lock to avoid race with disconnect()
            if not self._ws_client:
                logger.error("WebSocket client became None during subscribe_depth")
                return False

            # Enqueue for batched dispatch — flushed by _process_batch_subscriptions.
            self._enqueue_subscription(kotak_exchange, token, sub_type="dps")
            logger.debug(
                f"Queued depth subscription: {exchange}:{symbol} "
                f"(kotak: {kotak_exchange}|{token})"
            )
            return True

        except Exception as e:
            logger.error(f"Error subscribing to depth for {exchange}:{symbol}: {e}")
            return False

    def unsubscribe_depth(self, exchange, symbol, mode):
        """Unsubscribe from market depth - FIXED for multi-client support."""
        if not self._ws_client:
            logger.error("WebSocket client not initialized.")
            return

        try:
            from broker.kotak.streaming.kotak_mapping import get_kotak_exchange
            from database.token_db import get_token

            kotak_exchange = get_kotak_exchange(exchange)
            token = get_token(symbol, exchange)

            if not token:
                logger.error(f"No token found for {symbol} on {exchange}")
                return

            # **CRITICAL FIX**: Only unsubscribe from broker if no other modes are active
            should_unsub_broker = False
            with self._lock:
                mapping_key = (kotak_exchange, str(token))

                # Remove this mode from active modes
                if mapping_key in self._symbol_modes:
                    self._symbol_modes[mapping_key].discard(mode)

                    # Only unsubscribe from broker if no DEPTH modes are active
                    if 3 not in self._symbol_modes[mapping_key]:
                        should_unsub_broker = True

                    # Clean up mapping and cached state only if NO modes are active
                    if not self._symbol_modes[mapping_key]:
                        self._kotak_to_openalgo.pop(mapping_key, None)
                        self._symbol_modes.pop(mapping_key, None)
                        # Clean up symbol state to prevent unbounded memory growth
                        symbol_key = f"{kotak_exchange}|{token}"
                        self._symbol_state.pop(symbol_key, None)
                        logger.debug(f"Cleaned up mapping for: {exchange}:{symbol}")

            # Send unsubscribe outside lock to avoid deadlock
            if should_unsub_broker:
                ws = self._ws_client
                if ws:
                    ws.unsubscribe(kotak_exchange, token, sub_type="dpu")
                    logger.debug(f"Unsubscribed from broker depth: {exchange}:{symbol}")

        except Exception as e:
            logger.error(f"Error unsubscribing from depth for {exchange}:{symbol}: {e}")

    def get_ltp(self):
        """Return LTP data in the format expected by the WebSocket server."""
        with self._lock:
            # Create the expected nested format that matches AliceBlue/Angel response
            ltp_dict = {}

            # Convert cache format to client-expected nested format
            for (exchange, symbol), ltp_value in self._ltp_cache.items():
                if exchange not in ltp_dict:
                    ltp_dict[exchange] = {}

                ltp_dict[exchange][symbol] = {
                    "ltp": ltp_value,
                    "timestamp": int(time.time() * 1000),
                }

            logger.debug(f"get_ltp returning: {ltp_dict}")
            return ltp_dict  # Return nested dict format

    def get_quote(self):
        """Return quote data in the format expected by the WebSocket server."""
        with self._lock:
            quote_dict = {}

            # Convert quote cache to client-expected nested format
            for (exchange, symbol), quote_data in self._quote_cache.items():
                if exchange not in quote_dict:
                    quote_dict[exchange] = {}

                # Build complete quote data from cached state
                quote_dict[exchange][symbol] = {
                    "timestamp": int(time.time() * 1000),
                    "ltp": quote_data.get("ltp", 0.0),
                    "open": quote_data.get("open", 0.0),
                    "high": quote_data.get("high", 0.0),
                    "low": quote_data.get("low", 0.0),
                    "close": quote_data.get("prev_close", 0.0),
                    "volume": quote_data.get("volume", 0),
                }

            logger.debug(f"get_quote returning: {quote_dict}")
            return quote_dict

    def get_depth(self):
        """Return depth data in the format expected by the WebSocket server."""
        with self._lock:
            depth_dict = {}

            for (exchange, symbol), depth_data in self._depth_cache.items():
                if exchange not in depth_dict:
                    depth_dict[exchange] = {}

                prev_depth = self._depth_poll_state.get(f"{exchange}|{symbol}", {})
                prev_buy = prev_depth.get("buyBook", {}) if prev_depth else {}
                prev_sell = prev_depth.get("sellBook", {}) if prev_depth else {}

                buy_book = {}
                for i, level in enumerate(depth_data.get("buy", [])[:5], 1):
                    # If this level is all zero, use previous value if available
                    if (
                        level.get("price", 0) == 0
                        and level.get("quantity", 0) == 0
                        and level.get("orders", 0) == 0
                    ):
                        prev = prev_buy.get(str(i), {"price": "0", "qty": "0", "orders": "0"})
                        buy_book[str(i)] = prev
                    else:
                        buy_book[str(i)] = {
                            "price": str(level.get("price", 0)),
                            "qty": str(level.get("quantity", 0)),
                            "orders": str(level.get("orders", 0)),
                        }

                sell_book = {}
                for i, level in enumerate(depth_data.get("sell", [])[:5], 1):
                    if (
                        level.get("price", 0) == 0
                        and level.get("quantity", 0) == 0
                        and level.get("orders", 0) == 0
                    ):
                        prev = prev_sell.get(str(i), {"price": "0", "qty": "0", "orders": "0"})
                        sell_book[str(i)] = prev
                    else:
                        sell_book[str(i)] = {
                            "price": str(level.get("price", 0)),
                            "qty": str(level.get("quantity", 0)),
                            "orders": str(level.get("orders", 0)),
                        }

                # Save merged state for next poll
                self._depth_poll_state[f"{exchange}|{symbol}"] = {
                    "buyBook": buy_book,
                    "sellBook": sell_book,
                }

                depth_dict[exchange][symbol] = {
                    "timestamp": int(time.time() * 1000),
                    "ltp": depth_data.get("ltp", 0.0),
                    "buyBook": buy_book,
                    "sellBook": sell_book,
                }

            logger.debug(f"get_depth returning: {depth_dict}")
            return depth_dict

    def get_last_quote(self):
        """Return the last quote data."""
        with self._lock:
            return dict(self._quote_cache)

    def get_last_depth(self):
        """Return last depth data."""
        with self._lock:
            if self._ws_client:
                return self._ws_client.get_last_depth()
        return {}

    def is_connected(self):
        """Check if WebSocket is connected."""
        return self._ws_client.is_connected() if self._ws_client else False

    def set_callbacks(
        self,
        on_quote=None,
        on_depth=None,
        on_index=None,
        on_error=None,
        on_open=None,
        on_close=None,
    ):
        """Set additional user callbacks - following AliceBlue pattern."""
        # Internal callbacks are already set up during initialization
        # This method is for additional user callbacks if needed
        logger.debug("set_callbacks called - internal callbacks remain active")
        # Don't override internal callbacks - they handle the cache updates
        pass

```


---

# FILE: broker\kotak\streaming\kotak_mapping.py

```py
"""
Mapping utilities for Kotak broker integration.
Provides exchange, product, and order type mappings between OpenAlgo and Kotak formats.
"""

# Exchange code mappings
OPENALGO_TO_KOTAK_EXCHANGE = {
    "NSE": "nse_cm",
    "nse": "nse_cm",
    "BSE": "bse_cm",
    "bse": "bse_cm",
    "NFO": "nse_fo",
    "nfo": "nse_fo",
    "BFO": "bse_fo",
    "bfo": "bse_fo",
    "CDS": "cde_fo",
    "cds": "cde_fo",
    "BCD": "bcs-fo",
    "bcd": "bcs-fo",
    "MCX": "mcx_fo",
    "mcx": "mcx_fo",
    "NSE_INDEX": "nse_cm",
    "BSE_INDEX": "bse_cm",
}

KOTAK_TO_OPENALGO_EXCHANGE = {v: k for k, v in OPENALGO_TO_KOTAK_EXCHANGE.items()}

# Product type mappings
OPENALGO_TO_KOTAK_PRODUCT = {
    "Normal": "NRML",
    "NRML": "NRML",
    "CNC": "CNC",
    "cnc": "CNC",
    "Cash and Carry": "CNC",
    "MIS": "MIS",
    "mis": "MIS",
    "INTRADAY": "INTRADAY",
    "intraday": "INTRADAY",
    "Cover Order": "CO",
    "co": "CO",
    "CO": "CO",
    "BO": "Bracket Order",
    "Bracket Order": "Bracket Order",
    "bo": "Bracket Order",
}

KOTAK_TO_OPENALGO_PRODUCT = {v: k for k, v in OPENALGO_TO_KOTAK_PRODUCT.items()}

# Order type mappings
OPENALGO_TO_KOTAK_ORDER_TYPE = {
    "Limit": "L",
    "L": "L",
    "l": "L",
    "MKT": "MKT",
    "mkt": "MKT",
    "Market": "MKT",
    "sl": "SL",
    "SL": "SL",
    "Stop loss limit": "SL",
    "Stop loss market": "SL-M",
    "SL-M": "SL-M",
    "sl-m": "SL-M",
    "Spread": "SP",
    "SP": "SP",
    "sp": "SP",
    "2L": "2L",
    "2l": "2L",
    "Two Leg": "2L",
    "3L": "3L",
    "3l": "3L",
    "Three leg": "3L",
}

KOTAK_TO_OPENALGO_ORDER_TYPE = {v: k for k, v in OPENALGO_TO_KOTAK_ORDER_TYPE.items()}


def get_kotak_exchange(openalgo_exchange: str) -> str:
    """
    Convert OpenAlgo exchange code to Kotak exchange code.
    """
    return OPENALGO_TO_KOTAK_EXCHANGE.get(openalgo_exchange, openalgo_exchange)


def get_openalgo_exchange(kotak_exchange: str) -> str:
    """
    Convert Kotak exchange code to OpenAlgo exchange code.
    """
    return KOTAK_TO_OPENALGO_EXCHANGE.get(kotak_exchange, kotak_exchange)


def get_kotak_product(openalgo_product: str) -> str:
    """
    Convert OpenAlgo product type to Kotak product type.
    """
    return OPENALGO_TO_KOTAK_PRODUCT.get(openalgo_product, openalgo_product)


def get_openalgo_product(kotak_product: str) -> str:
    """
    Convert Kotak product type to OpenAlgo product type.
    """
    return KOTAK_TO_OPENALGO_PRODUCT.get(kotak_product, kotak_product)


def get_kotak_order_type(openalgo_order_type: str) -> str:
    """
    Convert OpenAlgo order type to Kotak order type.
    """
    return OPENALGO_TO_KOTAK_ORDER_TYPE.get(openalgo_order_type, openalgo_order_type)


def get_openalgo_order_type(kotak_order_type: str) -> str:
    """
    Convert Kotak order type to OpenAlgo order type.
    """
    return KOTAK_TO_OPENALGO_ORDER_TYPE.get(kotak_order_type, kotak_order_type)

```


---

# FILE: broker\kotak\streaming\kotak_websocket.py

```py
"""
Isolated, multi-client-safe WebSocket client for Kotak broker, using HSWebSocketLib.
Inspired by AliceBlue architecture, with per-instance state and thread safety.
Enhanced with partial update handling like AliceBlue's tick feed processing.
"""

import json
import threading
import time
from collections import deque

from utils.logging import get_logger

from .HSWebSocketLib import HSWebSocket

logger = get_logger(__name__)


class KotakWebSocket:
    def __init__(self, auth_config, ws_url="wss://mlhsm.kotaksecurities.com"):
        """
        Each instance is isolated: no shared state.
        auth_config: dict with keys 'auth_token', 'sid', 'hs_server_id', 'access_token'
        """
        self.auth_config = auth_config.copy()
        self.ws_url = ws_url
        self.ws = HSWebSocket()
        self._lock = threading.RLock()
        self._send_lock = threading.Lock()  # Serialize WebSocket sends to prevent frame corruption
        self.ws._send_lock = self._send_lock  # Share lock with HSWebSocket for ack sends
        self._subscriptions = set()  # (exchange, token, type)
        self._is_connected = False
        self._is_authenticated = False
        self._should_run = True
        self._thread = None
        self._on_quote = None
        self._on_depth = None
        self._on_index = None
        self._on_error = None
        self._on_open = None
        self._on_close = None
        self._last_quote = {}
        self._last_depth = {}
        self._last_index = {}
        self._pending_msgs = deque()  # queue for messages before connection

        # **CRITICAL FIX**: Add state storage like AliceBlue for partial updates
        self._symbol_state = {}  # Store last known complete state for each symbol

    def set_callbacks(
        self,
        on_quote=None,
        on_depth=None,
        on_index=None,
        on_error=None,
        on_open=None,
        on_close=None,
    ):
        self._on_quote = on_quote
        self._on_depth = on_depth
        self._on_index = on_index
        self._on_error = on_error
        self._on_open = on_open
        self._on_close = on_close

    def connect(self):
        """Start the websocket connection in a new thread."""
        with self._lock:
            if not self._should_run:
                logger.warning("connect() called on a closed KotakWebSocket, ignoring")
                return

        def _run():
            try:
                self.ws.open_connection(
                    url=self.ws_url,
                    token=self.auth_config["auth_token"],
                    sid=self.auth_config["sid"],
                    on_open=self._handle_open,
                    on_message=self._handle_message,
                    on_error=self._handle_error,
                    on_close=self._handle_close,
                )
            except Exception as e:
                logger.error(f"KotakWebSocket connection error: {e}")
                if self._on_error:
                    self._on_error(e)

        thread = threading.Thread(target=_run, daemon=True)
        with self._lock:
            self._thread = thread
        thread.start()

    def close(self):
        with self._lock:
            if not self._should_run:
                return  # Already closed, avoid double-close
            self._is_connected = False
            self._is_authenticated = False
            self._should_run = False
            # Prevent callbacks from firing during/after explicit close.
            # The adapter handles reconnection; firing these here would double-trigger.
            self._on_close = None
            self._on_error = None
            self._on_open = None
            thread = self._thread
            self._thread = None
        self.ws.close()
        if thread:
            thread.join(timeout=5)
        with self._lock:
            self._pending_msgs.clear()
            self._subscriptions.clear()
            self._symbol_state.clear()
            self._last_quote = {}
            self._last_depth = {}
            self._last_index = {}

    def subscribe(self, exchange, token, sub_type="mws", channelnum="1"):
        """Subscribe to a symbol (quote, depth, or index). sub_type: mws, dps, ifs, etc."""
        with self._lock:
            self._subscriptions.add((exchange, token, sub_type))
        msg = {"type": sub_type, "scrips": f"{exchange}|{token}", "channelnum": channelnum}
        self._send(msg)

    def unsubscribe(self, exchange, token, sub_type="mwu", channelnum="1"):
        """Unsubscribe from a symbol."""
        with self._lock:
            self._subscriptions.discard((exchange, token, sub_type))
            # Clean up cached state if no subscriptions remain for this symbol
            symbol_key = f"{exchange}|{token}"
            has_remaining = any(
                ex == exchange and tk == token for ex, tk, _ in self._subscriptions
            )
            if not has_remaining:
                self._symbol_state.pop(symbol_key, None)
        msg = {"type": sub_type, "scrips": f"{exchange}|{token}", "channelnum": channelnum}
        self._send(msg)

    def subscribe_batch(self, scrips, sub_type="mws", channelnum="1"):
        """Subscribe to multiple scrips in a single WebSocket frame.

        Args:
            scrips: iterable of (exchange, token) tuples
            sub_type: mws (quote), dps (depth), ifs (index)
            channelnum: HSI channel number
        """
        scrips = list(scrips)
        if not scrips:
            return
        with self._lock:
            for exchange, token in scrips:
                self._subscriptions.add((exchange, token, sub_type))
        # HSI protocol uses '&' as the scrip separator (see HSWebSocketLib.is_scrip_ok)
        scrip_str = "&".join(f"{ex}|{tk}" for ex, tk in scrips)
        msg = {"type": sub_type, "scrips": scrip_str, "channelnum": channelnum}
        logger.info(
            f"[KOTAK WSS BATCH] sub_type={sub_type} count={len(scrips)} scrips={scrip_str}"
        )
        self._send(msg)

    def unsubscribe_batch(self, scrips, sub_type="mwu", channelnum="1"):
        """Unsubscribe from multiple scrips in a single WebSocket frame."""
        scrips = list(scrips)
        if not scrips:
            return
        with self._lock:
            for exchange, token in scrips:
                self._subscriptions.discard((exchange, token, sub_type))
                symbol_key = f"{exchange}|{token}"
                has_remaining = any(
                    ex == exchange and tk == token for ex, tk, _ in self._subscriptions
                )
                if not has_remaining:
                    self._symbol_state.pop(symbol_key, None)
        scrip_str = "&".join(f"{ex}|{tk}" for ex, tk in scrips)
        msg = {"type": sub_type, "scrips": scrip_str, "channelnum": channelnum}
        self._send(msg)

    def _send(self, msg):
        with self._lock:
            if not self._is_connected or self.ws is None:
                logger.debug(f"[KOTAK WSS QUEUE] Queuing message until connection open: {msg}")
                self._pending_msgs.append(msg)
                return
        try:
            logger.debug(f"[KOTAK WSS SEND] {msg}")
            with self._send_lock:
                self.ws.hs_send(json.dumps(msg))
            logger.debug(f"Sent message: {msg}")
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            with self._lock:
                on_error = self._on_error
            if on_error:
                on_error(e)

    def _handle_open(self):
        logger.debug("KotakWebSocket connection opened")
        logger.debug("[KOTAK WSS EVENT] Connection opened")
        self._is_authenticated = False
        # Send explicit connection request before any subscriptions
        try:
            cn_msg = {
                "type": "cn",
                "Authorization": self.auth_config.get("auth_token"),
                "Sid": self.auth_config.get("sid"),
            }
            logger.debug(f"[KOTAK WSS SEND] Sending explicit connection request: {cn_msg}")
            with self._send_lock:
                self.ws.hs_send(json.dumps(cn_msg))
        except Exception as e:
            logger.error(f"Error sending explicit connection request: {e}")
            with self._lock:
                on_error = self._on_error
            if on_error:
                on_error(e)
        # Do NOT flush pending messages here; wait for cn ack
        with self._lock:
            on_open = self._on_open
        if on_open:
            on_open()

    def _flush_pending_subscriptions(self):
        # Copy pending messages under lock, then send outside lock to avoid deadlock
        with self._lock:
            pending = list(self._pending_msgs)
            self._pending_msgs.clear()
        for msg in pending:
            try:
                logger.debug(f"[KOTAK WSS SEND/FLUSH] {msg}")
                with self._send_lock:
                    self.ws.hs_send(json.dumps(msg))
            except Exception as e:
                logger.error(f"Error sending pending message: {e}")
                with self._lock:
                    on_error = self._on_error
                if on_error:
                    on_error(e)

    def _handle_close(self):
        logger.debug("KotakWebSocket connection closed")
        logger.debug("[KOTAK WSS EVENT] Connection closed")
        with self._lock:
            self._is_connected = False
            self._is_authenticated = False
            on_close = self._on_close
        if on_close:
            on_close()

    def _handle_error(self, error):
        logger.error(f"KotakWebSocket error: {error}")
        logger.error(f"[KOTAK WSS EVENT] Error: {error}")
        with self._lock:
            on_error = self._on_error
        if on_error:
            on_error(error)

    def _handle_message(self, message):
        logger.debug(f"[KOTAK WSS RECV] {message}")
        try:
            data = json.loads(message) if isinstance(message, str) else message
            if not data:
                return

            # **CRITICAL FIX**: Process each item in list separately
            if isinstance(data, list):
                for item in data:
                    self._process_single_message(item)
            else:
                self._process_single_message(data)

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            with self._lock:
                on_error = self._on_error
            if on_error:
                on_error(e)

    def _process_single_message(self, msg):
        """Process a single message item."""
        # Handle connection ack
        if msg.get("type") == "cn":
            if msg.get("stat") == "Ok":
                logger.debug(
                    "[KOTAK WSS HANDSHAKE] Connection acknowledged by broker. Flushing pending subscriptions."
                )
                with self._lock:
                    self._is_connected = True
                    self._is_authenticated = True
                self._flush_pending_subscriptions()
            else:
                logger.error(
                    f"[KOTAK WSS HANDSHAKE] Connection authentication failed: {msg}"
                )
                with self._lock:
                    self._is_connected = False
                    self._is_authenticated = False
                with self._lock:
                    on_error = self._on_error
                if on_error:
                    on_error(
                        Exception(f"Authentication failed: {msg.get('stat', 'unknown')}")
                    )
            return

        # **CRITICAL FIX**: Create symbol key for state management
        token = msg.get("tk", "")
        exchange = msg.get("e", "")
        symbol_key = f"{exchange}|{token}"

        # Identify type and process
        name = msg.get("name", "")
        if name == "dp":
            # Depth data
            depth = self._parse_depth_with_state(msg, symbol_key)
            with self._lock:
                self._last_depth = depth
            if self._on_depth:
                self._on_depth(depth)
        elif name == "if":
            # Index data
            index = self._parse_index(msg)
            with self._lock:
                self._last_index = index
            if self._on_index:
                self._on_index(index)
        elif "ltp" in msg or any(field in msg for field in ["bp", "sp", "op", "h", "lo", "c", "v"]):
            # Quote data - handle with state merging
            quote = self._parse_quote_with_state(msg, symbol_key)
            with self._lock:
                self._last_quote = quote
            if self._on_quote:
                self._on_quote(quote)

    def _is_partial_update(self, msg):
        """
        Determine if this is a partial update based on missing expected fields.
        FIXED to be less aggressive and preserve complete initial data.
        """
        # If we have LTP and symbol name, check if we have OHLC data
        ltp = msg.get("ltp", 0)
        symbol_name = msg.get("ts", "")

        # Check for presence of OHLC fields
        has_open = "op" in msg and msg.get("op", 0) != 0
        has_high = "h" in msg and msg.get("h", 0) != 0
        has_low = "lo" in msg and msg.get("lo", 0) != 0
        has_close = "c" in msg and msg.get("c", 0) != 0

        # If we have LTP, symbol name, and at least some OHLC data, treat as complete
        if ltp and symbol_name and (has_open or has_high or has_low or has_close):
            return False  # Complete enough to process

        # If we only have LTP and no symbol name or OHLC, it's partial
        if ltp and not symbol_name and not (has_open or has_high or has_low or has_close):
            return True

        return False  # Default to treating as complete

    def _parse_quote_with_state(self, msg, symbol_key):
        """
        Parse quote data with AliceBlue-style state merging for partial updates.
        """
        # Snapshot previous state under lock
        with self._lock:
            prev_state = self._symbol_state.get(symbol_key, {}).copy() if symbol_key in self._symbol_state else None

        # Check if this is a partial update (pure computation, no lock needed)
        is_partial = self._is_partial_update(msg)

        if is_partial and prev_state is not None:
            # This is a partial update - merge with stored state like AliceBlue
            logger.debug(f"Partial quote update detected for {symbol_key}")

            # Start with the last known complete state
            merged_data = prev_state

            # Update only the fields present in the partial update
            for key, value in msg.items():
                # Skip zero values that indicate "no update" for price fields
                if key in ["op", "h", "lo", "c", "bp", "sp"] and value == 0.0:
                    continue
                elif key == "v" and value == 0.0:  # volume
                    continue
                elif key == "ts" and not value:  # symbol name
                    continue
                else:
                    merged_data[key] = value

            # Use merged data for parsing
            msg = merged_data
            logger.debug(f"Merged quote data for {symbol_key}")

        # Parse the complete data (either original or merged)
        quote = {
            "bid": float(msg.get("bp", 0)),
            "ask": float(msg.get("sp", 0)),
            "open": float(msg.get("op", 0)),
            "high": float(msg.get("h", 0)),
            "low": float(msg.get("lo", 0)),
            "ltp": float(msg.get("ltp", 0)),
            "prev_close": float(msg.get("c", 0)),
            "volume": float(msg.get("v", 0)),
            "ts": msg.get("ts", ""),
            "tk": msg.get("tk", ""),
            "e": msg.get("e", ""),
        }

        # Store the complete state for future partial updates
        with self._lock:
            self._symbol_state[symbol_key] = msg.copy()

        return quote

    def _parse_depth_with_state(self, msg, symbol_key):
        """
        Parse depth data with AliceBlue-style state merging for partial updates.
        FIXED to use actual order counts from Kotak data.
        """
        # Check if this is a partial depth update (pure computation, no lock needed)
        has_price_data = any(
            key in msg
            for key in ["bp", "bp1", "bp2", "bp3", "bp4", "sp", "sp1", "sp2", "sp3", "sp4"]
        )

        if not has_price_data:
            # Snapshot previous state under lock for merging
            with self._lock:
                stored_data = self._symbol_state.get(symbol_key, {}).copy() if symbol_key in self._symbol_state else None

            if stored_data is not None:
                # This is a partial update with only quantities - merge with stored state
                logger.debug(f"Partial depth update detected for {symbol_key}")

                # Merge quantity updates with stored price data
                for key, value in msg.items():
                    if key in [
                        "bq",
                        "bq1",
                        "bq2",
                        "bq3",
                        "bq4",
                        "bs",
                        "bs1",
                        "bs2",
                        "bs3",
                        "bs4",
                        "bno1",
                        "bno2",
                        "bno3",
                        "bno4",
                        "bno5",  # CRITICAL: Include bid order counts
                        "sno1",
                        "sno2",
                        "sno3",
                        "sno4",
                        "sno5",
                    ]:  # CRITICAL: Include ask order counts
                        stored_data[key] = value
                    elif key not in ["tk", "e"] and value:  # Update other non-zero fields
                        stored_data[key] = value

                # Use merged data for parsing
                msg = stored_data
                logger.debug(f"Merged depth data for {symbol_key}")

        # Parse depth data with CORRECT order counts (pure computation, no lock needed)
        bids = []
        asks = []
        for i in range(5):
            price_key = f"bp{i}" if i > 0 else "bp"
            qty_key = f"bq{i}" if i > 0 else "bq"
            ask_price_key = f"sp{i}" if i > 0 else "sp"
            ask_qty_key = f"bs{i}" if i > 0 else "bs"

            # **CRITICAL FIX**: Use correct order count fields
            bid_orders_key = f"bno{i + 1}"  # bno1, bno2, bno3, bno4, bno5
            ask_orders_key = f"sno{i + 1}"  # sno1, sno2, sno3, sno4, sno5

            # Bids
            price = float(msg.get(price_key, 0))
            quantity = int(msg.get(qty_key, 0))
            bid_orders = int(msg.get(bid_orders_key, 0))  # Use actual bid order count

            if price > 0 and price != 21474836.48 and quantity >= 0:
                bids.append(
                    {
                        "price": price,
                        "quantity": quantity,
                        "orders": bid_orders,  # FIXED: Use actual order count
                    }
                )

            # Asks
            price = float(msg.get(ask_price_key, 0))
            quantity = int(msg.get(ask_qty_key, 0))
            ask_orders = int(msg.get(ask_orders_key, 0))  # Use actual ask order count

            if price > 0 and price != 21474836.48 and quantity >= 0:
                asks.append(
                    {
                        "price": price,
                        "quantity": quantity,
                        "orders": ask_orders,  # FIXED: Use actual order count
                    }
                )

        # Ensure we always have 5 levels
        while len(bids) < 5:
            bids.append({"price": 0, "quantity": 0, "orders": 0})
        while len(asks) < 5:
            asks.append({"price": 0, "quantity": 0, "orders": 0})

        depth = {
            "bids": bids[:5],
            "asks": asks[:5],
            "totalbuyqty": sum(b["quantity"] for b in bids),
            "totalsellqty": sum(a["quantity"] for a in asks),
            "ltp": float(msg.get("ltp", 0)),
            "ltq": int(msg.get("ltq", 0)),
            "volume": float(msg.get("v", 0)),
            "open": float(msg.get("op", 0)),
            "high": float(msg.get("h", 0)),
            "low": float(msg.get("lo", 0)),
            "prev_close": float(msg.get("c", 0)),
            "oi": int(msg.get("oi", 0)),
            "ts": msg.get("ts", ""),
            "tk": msg.get("tk", ""),
            "e": msg.get("e", ""),
        }

        # Store the complete state for future partial updates
        with self._lock:
            self._symbol_state[symbol_key] = msg.copy()

        return depth

    def _parse_quote(self, msg):
        """Legacy method - maintained for backward compatibility."""
        return self._parse_quote_with_state(msg, f"{msg.get('e', '')}|{msg.get('tk', '')}")

    def _parse_depth(self, msg):
        """Legacy method - maintained for backward compatibility."""
        return self._parse_depth_with_state(msg, f"{msg.get('e', '')}|{msg.get('tk', '')}")

    def _parse_index(self, msg):
        # See index_key_mapping for all fields
        return {
            "ltp": float(msg.get("iv", 0)),
            "prev_close": float(msg.get("ic", 0)),
            "timestamp": msg.get("tvalue", ""),
            "high": float(msg.get("highPrice", 0)),
            "low": float(msg.get("lowPrice", 0)),
            "open": float(msg.get("openingPrice", 0)),
            "mul": float(msg.get("mul", 0)),
            "prec": int(msg.get("prec", 0)),
            "cng": float(msg.get("cng", 0)),
            "nc": float(msg.get("nc", 0)),
            "tk": msg.get("tk", ""),
            "e": msg.get("e", ""),
        }

    def get_last_quote(self):
        with self._lock:
            return self._last_quote.copy()

    def get_last_depth(self):
        with self._lock:
            return self._last_depth.copy()

    def get_last_index(self):
        with self._lock:
            return self._last_index.copy()

    def is_connected(self):
        with self._lock:
            return self._is_connected

    def wait_until_closed(self, timeout=None):
        with self._lock:
            thread = self._thread
        if thread:
            thread.join(timeout)

```
