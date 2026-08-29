"""Shared building blocks for the FYERS TBT diagnostic probes.

Both sibling probes import from here so the token loading, the instrumented
client subclass, the raw-frame helpers, and the ``Recorder`` live in exactly one
place:

  * ``tbt_channel_probe.py``   — single connection, channel matrix (T1/T2/T2p/T3)
  * ``tbt_multiconn_probe.py`` — N concurrent independent connections (budget test)

SCOPE NOTE: this module imports OpenAlgo platform code (the FYERS streaming
client and the persisted auth store). It is a deliberate, documented diagnostics
scope exception — **read-only w.r.t. platform code** (it drives the client, never
edits it), in the same spirit as ``Documents/evidence/openalgo_platform/OPENALGO_PATCH.md``. All
platform imports are DEFERRED inside functions so importing this module needs
only the stdlib (the caller puts the OpenAlgo root on ``sys.path`` first).
"""
from __future__ import annotations

import collections
import json
import os
import pathlib
import sys
import threading
import time

# tools/fyers/<this> -> parents: [0]=fyers [1]=tools [2]=market_depth_recorder
# [3]=SS_Projects [4]=strategies [5]=openalgo repo root.
DEFAULT_OPENALGO_ROOT = str(pathlib.Path(__file__).resolve().parents[5])


class Recorder:
    """Thread-safe capture of one connection's requests, frames, errors, packets.

    Backward-compatible with the single-connection channel probe:
    ``record_packet(ticker)`` still works with no snapshot flag. The
    multi-connection probe passes ``is_snapshot`` so we also capture, per symbol,
    the first snapshot arrival and the first incremental-update arrival — the
    detailed timing evidence that makes "received" claims defensible.
    """

    def __init__(self, test: str, description: str):
        self.test = test
        self.description = description
        self._lock = threading.Lock()
        self.requests: list[dict] = []
        self.inbound_frames: list[dict] = []          # FYERS text ACKs
        self.errors: list[dict] = []                  # FYERS protobuf/JSON errors (on_error)
        self.closes: list[dict] = []                  # unexpected drop / close events
        self.packets: collections.Counter = collections.Counter()
        self.snap_counts: collections.Counter = collections.Counter()
        self.incr_counts: collections.Counter = collections.Counter()
        self.first_ts: dict[str, float] = {}          # first packet (any) per symbol
        self.first_snapshot_ts: dict[str, float] = {}
        self.first_incr_ts: dict[str, float] = {}
        self.subscribed: list[str] = []
        self.connect_requested_ts: float | None = None
        self.connect_ts: float | None = None          # when connect() returned True

    def record_request(self, op: str, symbols, channel):
        with self._lock:
            self.requests.append({
                "ts": time.time(), "op": op,
                "symbols": list(symbols) if symbols else None,
                "channel": channel, "channel_type": type(channel).__name__,
            })

    def record_inbound(self, raw: str):
        with self._lock:
            self.inbound_frames.append({"ts": time.time(), "raw": raw[:2000]})

    def record_error(self, msg):
        with self._lock:
            self.errors.append({"ts": time.time(), "msg": str(msg)[:2000]})

    def record_close(self, info):
        with self._lock:
            self.closes.append({"ts": time.time(), "info": str(info)[:500]})

    def record_packet(self, ticker: str, is_snapshot: bool | None = None):
        with self._lock:
            now = time.time()
            self.packets[ticker] += 1
            self.first_ts.setdefault(ticker, now)
            if is_snapshot is True:
                self.snap_counts[ticker] += 1
                self.first_snapshot_ts.setdefault(ticker, now)
            elif is_snapshot is False:
                self.incr_counts[ticker] += 1
                self.first_incr_ts.setdefault(ticker, now)

    def snapshot(self) -> dict:
        """Immutable view of everything captured, with raw timestamps preserved.

        Callers derive relative deltas (e.g. first_snapshot - connect_ts) at
        report time; here we keep raw wall-clock ts so the JSON is self-contained.
        """
        with self._lock:
            streamed = {
                t: {
                    "packets": c,
                    "snapshots": self.snap_counts.get(t, 0),
                    "increments": self.incr_counts.get(t, 0),
                    "first_ts": self.first_ts.get(t),
                    "first_snapshot_ts": self.first_snapshot_ts.get(t),
                    "first_incr_ts": self.first_incr_ts.get(t),
                }
                for t, c in self.packets.items()
            }
            return {
                "test": self.test, "description": self.description,
                "subscribed": list(self.subscribed),
                "subscribed_count": len(self.subscribed),
                "connect_requested_ts": self.connect_requested_ts,
                "connect_ts": self.connect_ts,
                "requests": list(self.requests),
                "inbound_frames": list(self.inbound_frames),
                "errors": list(self.errors),
                "closes": list(self.closes),
                "streamed": streamed,
                "streamed_count": len(self.packets),
                "total_packets": int(sum(self.packets.values())),
            }


def load_token(token: str | None, openalgo_root: str, user_id: str) -> str | None:
    """Resolve the FYERS access token: explicit arg > env > OpenAlgo persisted DB.

    The DB path works even with OpenAlgo stopped (it decrypts the stored auth
    token via Fernet, needing APP_KEY / API_KEY_PEPPER from the .env).
    """
    if token:
        return token
    env = os.environ.get("FYERS_TBT_TOKEN")
    if env:
        return env
    try:
        try:
            from dotenv import load_dotenv
            load_dotenv(os.path.join(openalgo_root, ".env"))
        except Exception:
            pass  # env may already be set; Fernet decrypt needs APP_KEY/API_KEY_PEPPER
        from database.auth_db import get_auth_token
        return get_auth_token(user_id, bypass_cache=True)
    except Exception as exc:  # noqa: BLE001
        print(f"error: could not auto-load FYERS token from OpenAlgo DB: {exc}\n"
              f"       pass --token or set FYERS_TBT_TOKEN", file=sys.stderr)
        return None


def make_instrumented_cls():
    """Build the instrumented TBT subclass after sys.path is set (import deferred)."""
    from broker.fyers.streaming.fyers_tbt_websocket import FyersTbtWebSocket

    class InstrumentedTbt(FyersTbtWebSocket):
        recorder: Recorder | None = None

        def _on_message(self, ws, message):
            # Tee inbound TEXT frames (JSON subscribe ACKs) before the base parses them.
            if self.recorder is not None and isinstance(message, str) and message != "pong":
                self.recorder.record_inbound(message)
            return super()._on_message(ws, message)

    return InstrumentedTbt


def send(client, obj) -> None:
    client.ws.send(json.dumps(obj))


def subscribe(client, symbols, channel) -> None:
    send(client, {"type": 1, "data": {
        "subs": 1, "symbols": list(symbols), "mode": "depth", "channel": channel}})


def resume(client, channels) -> None:
    send(client, {"type": 2, "data": {
        "resumeChannels": list(channels), "pauseChannels": []}})
