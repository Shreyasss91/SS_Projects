"""InstrumentManager + RestClient tests (spec §3.2). All run without a live feed / broker / socket.

Covers: RestClient retry/timeout/5xx/4xx against a scripted fake opener; the resolution pipeline
(weekly-expiry selection, instrument filtering, strike-step mode detection, O(1) maps, tick_size);
longest-prefix / name-column disambiguation (NIFTYNXT50 not shadowed by NIFTY); expiry parsing; the
empty-expiry fast-fail; and the ``--preflight`` exit codes.
"""

from __future__ import annotations

import io
import json
import urllib.error
from datetime import date

import pytest

from market_depth_recorder.__main__ import main
from market_depth_recorder.config import load_config
from market_depth_recorder.instrument_manager import (
    InstrumentManager,
    RestClient,
    RestError,
    _norm_strike,
    _option_type,
    _parse_expiry,
)


# --------------------------------------------------------------------------------------------------
# Fakes
# --------------------------------------------------------------------------------------------------
class _FakeResp:
    """Minimal context-manager stand-in for a urllib response (only ``read`` is used)."""

    def __init__(self, body: bytes):
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self) -> bytes:
        return self._body


class _ScriptedOpener:
    """Yields queued actions on each ``open`` call: bytes → a response body; an Exception → raised."""

    def __init__(self, actions):
        self._actions = list(actions)
        self.calls = 0

    def open(self, req, timeout=None):
        self.calls += 1
        action = self._actions.pop(0)
        if isinstance(action, BaseException):
            raise action
        return _FakeResp(action)


def _http_error(code: int, body: bytes = b"") -> urllib.error.HTTPError:
    return urllib.error.HTTPError("http://x/api", code, "err", {}, io.BytesIO(body))


def _envelope(data) -> bytes:
    return json.dumps({"status": "success", "data": data}).encode("utf-8")


class FakeRest:
    """Injectable RestClient replacement returning canned instruments/expiry dicts, no network."""

    def __init__(self, instruments: dict, expiries: dict):
        self._instruments = instruments
        self._expiries = expiries
        self.calls: list = []

    def get_instruments(self, exchange: str) -> list:
        self.calls.append(("instruments", exchange))
        return self._instruments[exchange]

    def get_expiry(self, symbol: str, exchange: str) -> list:
        self.calls.append(("expiry", symbol, exchange))
        return self._expiries[(symbol, exchange)]


# --------------------------------------------------------------------------------------------------
# Canned master data
# --------------------------------------------------------------------------------------------------
def _nfo_rows(expiry: str = "09-JUL-26") -> list[dict]:
    rows: list[dict] = []
    for strike in range(23000, 24001, 50):
        for ot in ("CE", "PE"):
            rows.append({
                "symbol": f"NIFTY09JUL26{strike}{ot}", "name": "NIFTY", "exchange": "NFO",
                "expiry": expiry, "strike": float(strike),
                "instrumenttype": "OPTIDX", "tick_size": 0.05,
            })
    # Contaminant #1: a different underlying on the same exchange — must NOT leak into the NIFTY chain.
    rows.append({
        "symbol": "NIFTYNXT5009JUL2612000CE", "name": "NIFTYNXT50", "exchange": "NFO",
        "expiry": expiry, "strike": 12000.0, "instrumenttype": "OPTIDX", "tick_size": 0.05,
    })
    # Contaminant #2: correct underlying but a later expiry — excluded (expiry != E_weekly).
    rows.append({
        "symbol": "NIFTY16JUL2623000CE", "name": "NIFTY", "exchange": "NFO",
        "expiry": "16-JUL-26", "strike": 23000.0, "instrumenttype": "OPTIDX", "tick_size": 0.05,
    })
    # Contaminant #3: a future on the same underlying — not an option type, excluded.
    rows.append({
        "symbol": "NIFTY09JUL26FUT", "name": "NIFTY", "exchange": "NFO",
        "expiry": expiry, "strike": None, "instrumenttype": "FUTIDX", "tick_size": 0.05,
    })
    return rows


def _bfo_rows(expiry: str = "10-JUL-26") -> list[dict]:
    rows: list[dict] = []
    for strike in range(80000, 81001, 100):
        for ot in ("CE", "PE"):
            rows.append({
                "symbol": f"SENSEX10JUL26{strike}{ot}", "name": "SENSEX", "exchange": "BFO",
                "expiry": expiry, "strike": float(strike),
                "instrumenttype": "OPTIDX", "tick_size": 0.05,
            })
    return rows


def _fake_rest() -> FakeRest:
    return FakeRest(
        instruments={"NFO": _nfo_rows(), "BFO": _bfo_rows()},
        expiries={
            ("NIFTY", "NFO"): ["09-JUL-26", "16-JUL-26"],
            ("SENSEX", "BFO"): ["10-JUL-26", "17-JUL-26"],
        },
    )


@pytest.fixture
def cfg(base_config, write_config):
    return load_config(write_config(base_config))


# --------------------------------------------------------------------------------------------------
# RestClient (subtask A)
# --------------------------------------------------------------------------------------------------
def test_restclient_success():
    opener = _ScriptedOpener([_envelope([{"symbol": "X"}])])
    rc = RestClient("http://h", "k", opener=opener, backoff_sec=0)
    assert rc.get_instruments("NFO") == [{"symbol": "X"}]
    assert opener.calls == 1


def test_restclient_retries_then_succeeds():
    opener = _ScriptedOpener([urllib.error.URLError("boom"), _envelope([])])
    rc = RestClient("http://h", "k", opener=opener, backoff_sec=0)
    assert rc.get_instruments("NFO") == []
    assert opener.calls == 2


def test_restclient_timeout_exhausts_retries():
    opener = _ScriptedOpener([TimeoutError("t"), TimeoutError("t"), TimeoutError("t")])
    rc = RestClient("http://h", "k", opener=opener, backoff_sec=0)
    with pytest.raises(RestError):
        rc.get_instruments("NFO")
    assert opener.calls == 3  # all retries consumed


def test_restclient_5xx_retries_then_fails():
    opener = _ScriptedOpener([_http_error(500), _http_error(502), _http_error(503)])
    rc = RestClient("http://h", "k", opener=opener, backoff_sec=0)
    with pytest.raises(RestError):
        rc.get_instruments("NFO")
    assert opener.calls == 3


def test_restclient_4xx_is_terminal_no_retry():
    opener = _ScriptedOpener([_http_error(403, b'{"message":"Invalid apikey"}')])
    rc = RestClient("http://h", "k", opener=opener, backoff_sec=0)
    with pytest.raises(RestError, match="403"):
        rc.get_instruments("NFO")
    assert opener.calls == 1  # 4xx not retried


def test_restclient_non_success_status_raises():
    opener = _ScriptedOpener([json.dumps({"status": "error", "message": "no"}).encode()])
    rc = RestClient("http://h", "k", opener=opener, backoff_sec=0)
    with pytest.raises(RestError, match="status="):
        rc.get_instruments("NFO")


def test_restclient_expiry_posts_body(monkeypatch):
    captured = {}

    class _CapOpener:
        def open(self, req, timeout=None):
            captured["method"] = req.get_method()
            captured["body"] = json.loads(req.data.decode())
            return _FakeResp(_envelope(["09-JUL-26"]))

    rc = RestClient("http://h", "mykey", opener=_CapOpener(), backoff_sec=0)
    assert rc.get_expiry("NIFTY", "NFO") == ["09-JUL-26"]
    assert captured["method"] == "POST"
    assert captured["body"] == {
        "apikey": "mykey", "symbol": "NIFTY", "exchange": "NFO", "instrumenttype": "options",
    }


# --------------------------------------------------------------------------------------------------
# Resolution pipeline (subtasks B–E) — happy path
# --------------------------------------------------------------------------------------------------
def test_resolve_happy_path(cfg):
    im = InstrumentManager(cfg, rest_client=_fake_rest())
    im.resolve()

    nifty = im.chains["NIFTY"]
    assert nifty.expiry == "09-JUL-26"
    assert nifty.expiry_date == date(2026, 7, 9)
    assert nifty.strike_step == 50
    assert im.active_strikes_list["NIFTY"] == list(range(23000, 24001, 50))
    assert nifty.n_contracts == 2 * len(range(23000, 24001, 50))
    # Probe strike = median strike (odd count → exact middle).
    assert nifty.probe_strike == im.active_strikes_list["NIFTY"][len(im.active_strikes_list["NIFTY"]) // 2]

    # O(1) maps built from the master symbols directly.
    assert im.strike_to_symbol_map["NIFTY"][23000] == {
        "CE": "NIFTY09JUL2623000CE", "PE": "NIFTY09JUL2623000PE",
    }
    assert im.symbol_to_strike_map["NIFTY09JUL2623000CE"] == {
        "underlying": "NIFTY", "strike": 23000, "option_type": "CE",
    }
    assert im.tick_size_map["NIFTY09JUL2623000CE"] == 0.05

    # SENSEX resolved with its own step.
    assert im.chains["SENSEX"].strike_step == 100
    assert im.active_strikes_list["SENSEX"] == list(range(80000, 81001, 100))


def test_resolve_excludes_contaminants(cfg):
    im = InstrumentManager(cfg, rest_client=_fake_rest())
    im.resolve()
    # NIFTYNXT50 must not shadow / leak into NIFTY.
    assert "NIFTYNXT5009JUL2612000CE" not in im.symbol_to_strike_map
    assert 12000 not in im.active_strikes_list["NIFTY"]
    # Later-expiry and futures rows excluded.
    assert "NIFTY16JUL2623000CE" not in im.symbol_to_strike_map
    assert "NIFTY09JUL26FUT" not in im.symbol_to_strike_map


def test_resolve_empty_expiry_fast_fails(cfg):
    rest = FakeRest(instruments={"NFO": _nfo_rows(), "BFO": _bfo_rows()},
                    expiries={("NIFTY", "NFO"): [], ("SENSEX", "BFO"): ["10-JUL-26"]})
    im = InstrumentManager(cfg, rest_client=rest)
    with pytest.raises(RestError, match="no future expiries"):
        im.resolve()


def test_resolve_no_contracts_fast_fails(cfg):
    # Expiry resolves but no instrument row matches it → fast-fail.
    rest = FakeRest(instruments={"NFO": _nfo_rows(expiry="16-JUL-26"), "BFO": _bfo_rows()},
                    expiries={("NIFTY", "NFO"): ["09-JUL-26"], ("SENSEX", "BFO"): ["10-JUL-26"]})
    im = InstrumentManager(cfg, rest_client=rest)
    with pytest.raises(RestError, match="no option contracts"):
        im.resolve()


def test_resolve_name_column_blank_falls_back_to_prefix(cfg):
    # A master with blank `name` must still route via longest-prefix on the symbol.
    rows = []
    for strike in (23000, 23050, 23100):
        rows.append({"symbol": f"NIFTY09JUL26{strike}CE", "name": "", "exchange": "NFO",
                     "expiry": "09-JUL-26", "strike": float(strike),
                     "instrumenttype": "OPTIDX", "tick_size": 0.05})
    rows.append({"symbol": "NIFTYNXT5009JUL2612000CE", "name": "", "exchange": "NFO",
                 "expiry": "09-JUL-26", "strike": 12000.0,
                 "instrumenttype": "OPTIDX", "tick_size": 0.05})
    rest = FakeRest(instruments={"NFO": rows, "BFO": _bfo_rows()},
                    expiries={("NIFTY", "NFO"): ["09-JUL-26"], ("SENSEX", "BFO"): ["10-JUL-26"]})
    im = InstrumentManager(cfg, rest_client=rest)
    im.resolve()
    assert im.active_strikes_list["NIFTY"] == [23000, 23050, 23100]
    assert 12000 not in im.active_strikes_list["NIFTY"]  # NIFTYNXT50 still not shadowed


# --------------------------------------------------------------------------------------------------
# Strike-step detection edge cases (subtask D)
# --------------------------------------------------------------------------------------------------
def test_strike_step_mode_ignores_wide_otm_gaps(cfg):
    im = InstrumentManager(cfg, rest_client=_fake_rest())
    u = cfg.underlyings[0]  # NIFTY: expected [50, 100], fallback 50
    # 50 is the mode even though one adjacent gap is 100 (a missing far strike).
    assert im._detect_strike_step(u, [23000, 23050, 23100, 23200]) == 50


def test_strike_step_single_strike_uses_fallback(cfg, caplog):
    im = InstrumentManager(cfg, rest_client=_fake_rest())
    u = cfg.underlyings[0]
    with caplog.at_level("WARNING"):
        assert im._detect_strike_step(u, [23000]) == u.strike_step_fallback
    assert any("only 1 strike" in r.message for r in caplog.records)


def test_strike_step_unexpected_uses_fallback_with_warning(cfg, caplog):
    im = InstrumentManager(cfg, rest_client=_fake_rest())
    u = cfg.underlyings[0]  # expected [50, 100], fallback 50
    with caplog.at_level("WARNING"):
        # Mode step 75 is not in the expected set → fallback.
        assert im._detect_strike_step(u, [23000, 23075, 23150, 23225]) == 50
    assert any("not in expected" in r.message for r in caplog.records)


# --------------------------------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------------------------------
def test_parse_expiry_formats():
    assert _parse_expiry("09-JUL-26") == date(2026, 7, 9)
    assert _parse_expiry("09-JUL-2026") == date(2026, 7, 9)
    with pytest.raises(RestError):
        _parse_expiry("2026-07-09")


def test_option_type_resolution():
    assert _option_type("CE", "X") == "CE"
    assert _option_type("OPTIDX", "NIFTY09JUL2623000PE") == "PE"
    assert _option_type("OPTIDX", "NIFTY09JUL26FUT") is None


def test_norm_strike():
    assert _norm_strike(23000.0) == 23000 and isinstance(_norm_strike(23000.0), int)
    assert _norm_strike(292.5) == 292.5
    assert _norm_strike(None) is None
    assert _norm_strike(0) is None
    assert _norm_strike("bad") is None


# --------------------------------------------------------------------------------------------------
# --preflight exit codes (subtask F)
# --------------------------------------------------------------------------------------------------
def test_preflight_ok(base_config, write_config, monkeypatch, capsys):
    path = write_config(base_config)

    class _OkManager:
        def __init__(self, cfg, rest_client=None):
            pass

        def resolve(self):
            return None

        def preflight_report(self):
            return [{"name": "NIFTY", "option_exchange": "NFO", "expiry": "09-JUL-26",
                     "strike_step": 50, "n_strikes": 21, "requested_depth": 50,
                     "probe_strike": 23500}]

    monkeypatch.setattr("market_depth_recorder.instrument_manager.InstrumentManager", _OkManager)
    assert main(["--preflight", "--config", path]) == 0
    out = capsys.readouterr().out
    assert "PREFLIGHT OK" in out
    assert "actual_depth=<pending P3 raw-WS probe>" in out


def test_preflight_rest_failure_exits_1(base_config, write_config, monkeypatch, capsys):
    path = write_config(base_config)

    class _FailManager:
        def __init__(self, cfg, rest_client=None):
            pass

        def resolve(self):
            raise RestError("connection refused")

    monkeypatch.setattr("market_depth_recorder.instrument_manager.InstrumentManager", _FailManager)
    assert main(["--preflight", "--config", path]) == 1
    assert "PREFLIGHT FAILED" in capsys.readouterr().err


def test_preflight_bad_config_exits_1(base_config, write_config, capsys):
    base_config["websocket"]["transport"] = "carrier-pigeon"  # invalid enum → config error
    path = write_config(base_config)
    assert main(["--preflight", "--config", path]) == 1
    assert "CONFIG VALIDATION FAILED" in capsys.readouterr().err
