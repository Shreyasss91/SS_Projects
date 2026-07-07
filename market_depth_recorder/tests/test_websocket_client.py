"""DepthWebSocketClient + DSM + tee + reconnect + live depth preflight tests (spec §3.3/§6.1/§3.2.5).

All run offline: an injected fake ``FeedTransport`` (no socket), plain ``queue.Queue``s, an injected
clock and ``sleep_fn``. No live broker / WS / market.
"""

from __future__ import annotations

import queue
import threading

import pytest

from market_depth_recorder.config import load_config
from market_depth_recorder.websocket_client import (
    DepthProbeResult,
    DepthWebSocketClient,
    TransportNotConnected,
    normalize_market_data,
    run_depth_preflight,
    wire_symbol,
)


# --------------------------------------------------------------------------------------------------
# Fakes
# --------------------------------------------------------------------------------------------------
class FakeTransport:
    """No-socket transport: records sent frames, lets the test fire on_open / deliver messages."""

    def __init__(self, *, connected: bool = True, open_ok: bool = True, deliver_on_open=None):
        self.sent: list[dict] = []
        self.connected = connected
        self.open_ok = open_ok
        self.deliver_on_open = list(deliver_on_open or [])
        self.closed = False
        self._close = threading.Event()
        self.on_open = self.on_message = self.on_close = None

    def bind(self, *, on_open, on_message, on_close):
        self.on_open, self.on_message, self.on_close = on_open, on_message, on_close

    def run_session(self):
        if not self.open_ok:
            return
        if self.on_open:
            self.on_open()
        for msg in self.deliver_on_open:
            if self.on_message:
                self.on_message(msg)
        self._close.wait()

    def send(self, frame):
        if not self.connected:
            raise TransportNotConnected("transport down")
        self.sent.append(frame)

    def close(self):
        self.closed = True
        self._close.set()


class FakeInstrumentManager:
    """Minimal resolved-manager stand-in: wide strike grids + probe strikes for NIFTY and SENSEX."""

    def __init__(self):
        self.strike_to_symbol_map = {}
        self.symbol_to_strike_map = {}
        self.active_strikes_list = {}
        self.chains = {}
        self._add("NIFTY", range(22000, 25001, 100), 23500)
        self._add("SENSEX", range(78000, 82001, 100), 80000)

    def _add(self, name, strikes, probe):
        strikes = list(strikes)
        self.active_strikes_list[name] = strikes
        self.strike_to_symbol_map[name] = {
            k: {"CE": f"{name}W{k}CE", "PE": f"{name}W{k}PE"} for k in strikes
        }
        for k in strikes:
            for ot in ("CE", "PE"):
                self.symbol_to_strike_map[f"{name}W{k}{ot}"] = {
                    "underlying": name, "strike": k, "option_type": ot,
                }
        self.chains[name] = type("C", (), {"probe_strike": probe})()


@pytest.fixture
def cfg(base_config, write_config):
    return load_config(write_config(base_config))


def _client(cfg, transport, **kw):
    return DepthWebSocketClient(
        cfg, FakeInstrumentManager(),
        raw_file_queue=kw.pop("raw_q", queue.Queue()),
        proc_queue=kw.pop("proc_q", queue.Queue()),
        shutdown_event=kw.pop("shutdown", threading.Event()),
        transport=transport,
        time_fn=kw.pop("time_fn", lambda: 1000.0),
        sleep_fn=kw.pop("sleep_fn", lambda _s: None),
    )


def _md(symbol, exchange, mode, data):
    return {"type": "market_data", "symbol": symbol, "exchange": exchange, "mode": mode, "data": data}


# --------------------------------------------------------------------------------------------------
# Module helpers
# --------------------------------------------------------------------------------------------------
def test_wire_symbol_suffix():
    assert wire_symbol("NIFTY123CE", 50) == "NIFTY123CE:50"
    assert wire_symbol("NIFTY123CE", 5) == "NIFTY123CE"


def test_normalize_keeps_wire_symbol_and_fields():
    msg = _md("N23500CE:50", "NFO", 3,
              {"ltp": 1.2, "feed_time": 42, "depth_levels": 50, "is_50_depth": True,
               "depth": {"buy": [], "sell": []}})
    p = normalize_market_data(msg, recv_ts=99.0)
    assert p["symbol"] == "N23500CE:50"  # keeps :50 (§3.3.3)
    assert p["exchange"] == "NFO" and p["mode"] == 3 and p["recv_ts"] == 99.0
    assert p["feed_time"] == 42 and p["depth_levels"] == 50 and p["is_50_depth"] is True


# --------------------------------------------------------------------------------------------------
# Tee (fan-out) — §2.2 Phase D / §5.1
# --------------------------------------------------------------------------------------------------
def test_tee_delivers_same_packet_to_both_queues(cfg):
    raw_q, proc_q = queue.Queue(), queue.Queue()
    c = _client(cfg, FakeTransport(), raw_q=raw_q, proc_q=proc_q)
    packet = {"symbol": "X", "mode": 3}
    c._tee(packet)
    assert proc_q.get_nowait() is packet
    assert raw_q.get_nowait() is packet


def test_tee_proc_sheds_first(cfg):
    raw_q, proc_q = queue.Queue(), queue.Queue(maxsize=1)
    proc_q.put_nowait({"filler": True})  # proc full; raw has room
    c = _client(cfg, FakeTransport(), raw_q=raw_q, proc_q=proc_q)
    c._tee({"symbol": "X"})
    assert c.proc_dropped_total == 1
    assert c.raw_dropped_total == 0
    assert raw_q.get_nowait()["symbol"] == "X"  # audit still captured


def test_tee_raw_drops_last_on_saturation(cfg, monkeypatch):
    monkeypatch.setattr("market_depth_recorder.websocket_client._RAW_PUT_TIMEOUT_SEC", 0.0)
    raw_q, proc_q = queue.Queue(maxsize=1), queue.Queue()
    raw_q.put_nowait({"filler": True})  # raw full
    c = _client(cfg, FakeTransport(), raw_q=raw_q, proc_q=proc_q)
    c._tee({"symbol": "X"})
    assert c.raw_dropped_total == 1  # the single sanctioned raw-loss boundary
    assert proc_q.get_nowait()["symbol"] == "X"


def test_on_message_routes_spot_and_tees(cfg):
    raw_q, proc_q = queue.Queue(), queue.Queue()
    ft = FakeTransport()
    c = _client(cfg, ft, raw_q=raw_q, proc_q=proc_q)
    c._on_message(_md("NIFTY", "NSE_INDEX", 1, {"ltp": 23500.0}))
    assert c.current_spot_prices["NIFTY"] == 23500.0  # DSM saw the spot
    assert not raw_q.empty() and not proc_q.empty()   # still teed
    # the spot tick seeded boundaries → option depth subscriptions were issued
    assert any(f.get("mode") == 3 for f in ft.sent)


def test_control_message_not_teed(cfg):
    raw_q, proc_q = queue.Queue(), queue.Queue()
    c = _client(cfg, FakeTransport(), raw_q=raw_q, proc_q=proc_q)
    c._on_message({"type": "subscribe", "status": "success"})
    assert raw_q.empty() and proc_q.empty()


# --------------------------------------------------------------------------------------------------
# DSM — §3.3.2
# --------------------------------------------------------------------------------------------------
def test_dsm_seeds_initial_window(cfg):
    c = _client(cfg, FakeTransport())
    new = c._on_spot("NIFTY", 23500.0)  # window ±1000 → [22500, 24500]
    assert min(new) == 22500 and max(new) == 24500
    lo, hi = c.boundaries("NIFTY")
    assert lo == 22500 and hi == 24500


def _ramp(c, name, start, stop, step):
    """Feed a gradual spot ramp so no single tick exceeds the 2% spike guard (§3.3.2). Real spot
    moves tick-by-tick; large one-shot jumps are (correctly) rejected as spikes."""
    px = start
    while (px < stop) if step > 0 else (px > stop):
        c._route_spot(name, {"ltp": float(px)})
        px += step
    c._route_spot(name, {"ltp": float(stop)})


def test_dsm_upper_breach_expands_and_selects_new(cfg):
    c = _client(cfg, FakeTransport())
    c._route_spot("NIFTY", {"ltp": 23500.0})           # seed [22500, 24500]
    seeded = c.active_subscriptions
    _ramp(c, "NIFTY", 23500, 24400, 50)                # ramp up past b_upper - threshold (24300)
    _, hi = c.boundaries("NIFTY")
    assert hi > 24500.0                                # upper boundary expanded
    grew = c.active_subscriptions - seeded
    assert any(int(s[len("NIFTYW"):-len("CE:50")]) > 24500
               for s in grew if s.endswith("CE:50"))   # new higher-strike legs subscribed


def test_dsm_lower_breach_expands(cfg):
    c = _client(cfg, FakeTransport())
    c._route_spot("NIFTY", {"ltp": 23500.0})           # seed [22500, 24500]
    _ramp(c, "NIFTY", 23500, 22600, -50)               # ramp down past b_lower + threshold (22700)
    lo, _ = c.boundaries("NIFTY")
    assert lo < 22500.0
    assert any(s.endswith("CE:50") and int(s[len("NIFTYW"):-len("CE:50")]) < 22500
               for s in c.active_subscriptions)


def test_dsm_ignores_nonpositive_and_spikes(cfg):
    c = _client(cfg, FakeTransport())
    assert c._on_spot("NIFTY", -1.0) == []
    c._on_spot("NIFTY", 23500.0)                        # seed + median baseline
    assert c._on_spot("NIFTY", 30000.0) == []           # >2% vs median → ignored
    assert c.current_spot_prices["NIFTY"] == 23500.0    # spike did not update spot


def test_never_shrink_on_pullback(cfg):
    c = _client(cfg, FakeTransport())
    c._route_spot("NIFTY", {"ltp": 23500.0})
    _ramp(c, "NIFTY", 23500, 24400, 50)                 # ramp up → expand upper
    peak = set(c.active_subscriptions)
    assert len(peak) > 0
    _ramp(c, "NIFTY", 24400, 23000, -50)                # pull back — must never unsubscribe
    assert peak <= c.active_subscriptions               # only grows


# --------------------------------------------------------------------------------------------------
# P6 orchestrator touches — seed_spot / freeze_dsm / connection_status / last_recv_ts / actual_depth
# --------------------------------------------------------------------------------------------------
def test_connection_status_tracks_open_close(cfg):
    c = _client(cfg, FakeTransport())
    assert c.connection_status == "disconnected"
    c._on_open()
    assert c.connection_status == "connected"
    c._on_close(1000, "bye")
    assert c.connection_status == "disconnected"


def test_seed_spot_seeds_dsm_and_subscribes(cfg):
    ft = FakeTransport()
    c = _client(cfg, ft)
    c.seed_spot("NIFTY", 23500.0)                       # same entry as a live spot tick
    lo, hi = c.boundaries("NIFTY")
    assert lo == 22500 and hi == 24500
    assert any(f.get("mode") == 3 for f in ft.sent)     # option depth subscriptions issued


def test_seed_spot_ignores_bad_price_and_unknown_name(cfg):
    ft = FakeTransport()
    c = _client(cfg, ft)
    c.seed_spot("NIFTY", "n/a")                         # non-numeric → no-op
    c.seed_spot("UNKNOWN", 100.0)                       # unknown underlying → no-op
    assert ft.sent == []
    assert c.boundaries("NIFTY") == (None, None)


def test_freeze_dsm_halts_expansion(cfg):
    c = _client(cfg, FakeTransport())
    c._route_spot("NIFTY", {"ltp": 23500.0})            # seed [22500, 24500]
    frozen_before = set(c.active_subscriptions)
    c.freeze_dsm()
    _ramp(c, "NIFTY", 23500, 24400, 50)                 # would normally breach + expand upper
    _, hi = c.boundaries("NIFTY")
    assert hi == 24500.0                                # boundary unchanged — expansion halted
    assert c.active_subscriptions == frozen_before      # no new legs after freeze


def test_last_recv_ts_set_on_message(cfg):
    c = _client(cfg, FakeTransport(), time_fn=lambda: 4242.0)
    assert c.last_recv_ts is None
    c._on_message(_md("NIFTY", "NSE_INDEX", 1, {"ltp": 23500.0}))
    assert c.last_recv_ts == 4242.0


def test_actual_depth_tracks_max_seen(cfg):
    c = _client(cfg, FakeTransport())
    c._on_message(_md("NIFTYW23500CE:50", "NFO", 3,
                      {"depth_levels": 50, "depth": {"buy": [], "sell": []}}))
    assert c.actual_depth["NIFTY"] == 50
    # Max-seen: a later thinner packet does not overwrite the recorded 50-level capability.
    c._on_message(_md("NIFTYW23500CE:50", "NFO", 3,
                      {"depth_levels": 5, "depth": {"buy": [], "sell": []}}))
    assert c.actual_depth["NIFTY"] == 50


def test_actual_depth_updates_upward_when_thin_arrives_first(cfg):
    # Regression: an illiquid OTM strike (few populated levels) arriving FIRST must not freeze the
    # map below the true capability — a later liquid near-ATM 50-level packet updates it upward.
    c = _client(cfg, FakeTransport())
    c._on_message(_md("NIFTYW23500CE:50", "NFO", 3,
                      {"depth_levels": 27, "depth": {"buy": [], "sell": []}}))
    assert c.actual_depth["NIFTY"] == 27
    c._on_message(_md("NIFTYW24500CE:50", "NFO", 3,
                      {"depth_levels": 50, "depth": {"buy": [], "sell": []}}))
    assert c.actual_depth["NIFTY"] == 50


def test_actual_depth_falls_back_to_populated_levels_when_field_absent(cfg):
    # BFO/SENSEX 5-level books carry depth_levels=None; the map must still register them via the
    # populated per-side level count (else SENSEX vanishes from the §9 health map).
    c = _client(cfg, FakeTransport())
    lv = [{"price": 100.0 + i, "quantity": 1, "orders": 1} for i in range(5)]
    c._on_message(_md("SENSEXW80000CE", "BFO", 3,
                      {"depth_levels": None, "depth": {"buy": lv, "sell": lv}}))
    assert c.actual_depth["SENSEX"] == 5


# --------------------------------------------------------------------------------------------------
# Reconnect / never-shrink recovery — §6.1
# --------------------------------------------------------------------------------------------------
def test_on_open_authenticates_subscribes_spots_and_resubscribes(cfg):
    ft = FakeTransport()
    c = _client(cfg, ft)
    c._route_spot("NIFTY", {"ltp": 23500.0})            # build some option subs
    option_subs = c.active_subscriptions
    ft.sent.clear()
    c._on_open()                                        # simulate (re)connect
    actions = [f["action"] for f in ft.sent]
    assert actions[0] == "authenticate"
    spot_syms = {f["symbol"] for f in ft.sent if f.get("mode") == 1}
    assert {"NIFTY", "SENSEX"} <= spot_syms             # both spots resubscribed
    resent = {f["symbol"] for f in ft.sent if f.get("mode") == 3}
    assert option_subs <= resent                        # every option leg restored


def test_subscribe_while_disconnected_is_flushed_on_reconnect(cfg):
    ft = FakeTransport(connected=False)                 # sends raise TransportNotConnected
    c = _client(cfg, ft)
    c._route_spot("NIFTY", {"ltp": 23500.0})            # frames recorded, sends swallowed
    assert ft.sent == []                                # nothing left the socket
    assert len(c.active_subscriptions) > 0              # but tracked for recovery
    ft.connected = True
    c._resubscribe_all()
    assert {f["symbol"] for f in ft.sent} == c.active_subscriptions


def test_reconnect_backoff_sequence(cfg):
    waits: list[float] = []
    shutdown = threading.Event()

    def sleep_fn(secs):
        waits.append(secs)
        if len(waits) >= 3:
            shutdown.set()

    ft = FakeTransport(open_ok=False)                   # every connect attempt fails immediately
    c = _client(cfg, ft, shutdown=shutdown, sleep_fn=sleep_fn)
    c.run()                                             # synchronous; sleep_fn stops it after 3
    # T = min(60, 1.5^attempts * 2.0) for attempts 1,2,3
    assert waits == pytest.approx([3.0, 4.5, 6.75])
    assert ft.closed                                    # socket closed on exit


# --------------------------------------------------------------------------------------------------
# Live depth preflight — §3.2.5 / §9
# --------------------------------------------------------------------------------------------------
def _depth_pkt(name, strike, depth_levels, is_50, requested_depth, orders):
    sym = wire_symbol(f"{name}W{strike}CE", requested_depth)
    exch = "NFO" if name == "NIFTY" else "BFO"
    return _md(sym, exch, 3, {
        "depth_levels": depth_levels, "is_50_depth": is_50,
        "depth": {"buy": [{"price": 1.0, "quantity": 10, "orders": orders}], "sell": []},
    })


def test_preflight_reads_depth_and_warns_on_degradation(cfg, caplog):
    im = FakeInstrumentManager()
    packets = [
        _depth_pkt("NIFTY", 23500, 50, True, 50, orders=3),    # full TBT
        _depth_pkt("SENSEX", 80000, 5, False, 50, orders=0),   # degraded to 5, orders=0
    ]
    ft = FakeTransport(deliver_on_open=packets)
    with caplog.at_level("WARNING"):
        results = run_depth_preflight(cfg, im, transport=ft, timeout=2.0)
    by = {r.name: r for r in results}
    assert by["NIFTY"].actual_depth == 50 and by["NIFTY"].per_level_orders_available is True
    assert by["SENSEX"].actual_depth == 5 and by["SENSEX"].per_level_orders_available is False
    assert any("DEPTH DEGRADED" in r.message for r in caplog.records)  # SENSEX 5 < 50
    assert ft.closed


def test_preflight_unreachable_degrades_fast(cfg):
    ft = FakeTransport(open_ok=False)                  # never opens
    results = run_depth_preflight(cfg, FakeInstrumentManager(), transport=ft, timeout=30.0)
    assert all(r.reachable is False and r.actual_depth is None for r in results)
    assert all("unreachable" in r.note for r in results)


def test_preflight_result_shape():
    r = DepthProbeResult("NIFTY", "NFO", 50, True, 50, True, True, "ok")
    assert r.name == "NIFTY" and r.actual_depth == 50