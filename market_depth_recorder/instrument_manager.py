"""Instrument & Expiry Manager (spec §3.2).

Runs once at startup: query the OpenAlgo REST API, resolve each configured underlying's **current
weekly option chain**, auto-detect the **strike step**, and compile the **O(1) lookup maps**
(``strike_to_symbol_map``, ``symbol_to_strike_map``, ``active_strikes_list``) plus a per-symbol
``tick_size`` table (for M29) that the DSM (P3) and processor (P4) consume.

Pure resolution logic — **no sockets, threads, or DB**. The only file descriptor is a transient HTTP
connection, opened under ``with`` and closed on every path (success, retry, error). The §3.2.5 *live*
depth probe (reading ``depth_levels``/``is_50_depth`` off a raw packet) is deferred to P3 — see the
plan's decision 10; ``--preflight`` here resolves the chain offline and reports ``actual_depth`` as
pending.

Genericization: every index name / exchange / strike step comes from ``config.underlyings`` — this
module never branches on ``NIFTY``/``SENSEX`` and holds no such literal. State is keyed by ``name``.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from .config import Config, Underlying
from .utils import get_logger

logger = get_logger(__name__)

# Option instrument-type tags seen in the OpenAlgo master (services/expiry_service.py:123-124).
# OPTIDX/OPTSTK carry the CE/PE in the symbol suffix; CE/PE tag it directly.
_OPTION_INSTRUMENT_TYPES = frozenset({"OPTIDX", "OPTSTK", "CE", "PE"})

# REST defaults (§3.2.1: 10 s timeout, up to 3 retries). Kept module-private, not engine config —
# they govern the transport, not any produced value, so they never touch config_hash.
_REST_TIMEOUT_SEC = 10.0
_REST_MAX_RETRIES = 3
_REST_BACKOFF_SEC = 0.5


class RestError(Exception):
    """A REST call failed after retries, returned a non-success status, or a malformed body."""


# --------------------------------------------------------------------------------------------------
# RestClient (subtask A) — stdlib urllib; no third-party dependency (standalone-venv promise).
# --------------------------------------------------------------------------------------------------
class RestClient:
    """Thin OpenAlgo REST wrapper over ``urllib`` — instruments (GET) + expiry (POST).

    Auth per §3.2.1: ``apikey`` as a query parameter for instruments, in the JSON body for expiry.
    Each call opens a connection, reads the response under ``with`` (closed on every path), and retries
    up to ``max_retries`` on a network error or 5xx with linear backoff; 4xx (bad key / bad request)
    is terminal. Injectable: tests substitute a fake exposing ``get_instruments``/``get_expiry``.
    """

    def __init__(
        self,
        host_server: str,
        api_key: str,
        *,
        timeout: float = _REST_TIMEOUT_SEC,
        max_retries: int = _REST_MAX_RETRIES,
        backoff_sec: float = _REST_BACKOFF_SEC,
        opener: urllib.request.OpenerDirector | None = None,
    ):
        self._base = host_server.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout
        self._max_retries = max(1, max_retries)
        self._backoff = backoff_sec
        # One shared opener; urllib still opens/closes a socket per request under the with-block below.
        self._opener = opener or urllib.request.build_opener()

    def get_instruments(self, exchange: str) -> list[dict[str, Any]]:
        """`GET /api/v1/instruments/?apikey=…&exchange=<exchange>&format=json` → the ``data`` list."""
        query = urllib.parse.urlencode(
            {"apikey": self._api_key, "exchange": exchange, "format": "json"}
        )
        url = f"{self._base}/api/v1/instruments/?{query}"
        payload = self._request("GET", url)
        return _extract_data_list(payload, f"instruments[{exchange}]")

    def get_expiry(self, symbol: str, exchange: str) -> list[str]:
        """`POST /api/v1/expiry/` (options) → the sorted, future-only ``data`` expiry list."""
        url = f"{self._base}/api/v1/expiry/"
        body = json.dumps(
            {"apikey": self._api_key, "symbol": symbol,
             "exchange": exchange, "instrumenttype": "options"}
        ).encode("utf-8")
        payload = self._request("POST", url, body=body)
        return _extract_data_list(payload, f"expiry[{symbol}/{exchange}]")

    def get_quote(self, symbol: str, exchange: str) -> float:
        """`POST /api/v1/quotes/` ``{apikey, symbol, exchange}`` → ``data.ltp`` (float).

        The P6 mid-day-restart ATM seed (§3.1.2): one direct quote per underlying resolves the current
        spot instantly rather than waiting for the first WS tick. Unlike instruments/expiry (DB-backed),
        this endpoint **requires a live broker session** — the orchestrator falls back to the lazy WS
        spot-tick seed on any failure (plan decision 57). The response is closed on every path (the
        shared ``_request`` retry loop); a missing/non-numeric ``ltp`` raises :class:`RestError`.
        """
        url = f"{self._base}/api/v1/quotes/"
        body = json.dumps(
            {"apikey": self._api_key, "symbol": symbol, "exchange": exchange}
        ).encode("utf-8")
        payload = self._request("POST", url, body=body)
        data = _extract_data_obj(payload, f"quotes[{symbol}/{exchange}]")
        ltp = data.get("ltp")
        if ltp is None:
            raise RestError(f"quotes[{symbol}/{exchange}]: 'ltp' missing from response")
        try:
            return float(ltp)
        except (TypeError, ValueError) as exc:
            raise RestError(f"quotes[{symbol}/{exchange}]: non-numeric ltp {ltp!r}") from exc

    def _request(self, method: str, url: str, body: bytes | None = None) -> Any:
        """Issue one HTTP request with retries; return the parsed JSON payload or raise ``RestError``.

        The response object is always consumed inside ``with`` (or explicitly closed for the HTTPError
        error-body path) so no descriptor leaks across success, retry, or failure.
        """
        headers = {"Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        last_err: RestError | None = None
        for attempt in range(1, self._max_retries + 1):
            req = urllib.request.Request(url, data=body, headers=headers, method=method)
            try:
                with self._opener.open(req, timeout=self._timeout) as resp:
                    raw = resp.read()
                return json.loads(raw.decode("utf-8"))
            except urllib.error.HTTPError as exc:
                # HTTPError is itself an open response object — read then close it to free the fd.
                try:
                    detail = exc.read().decode("utf-8", "replace")
                except Exception:  # noqa: BLE001 — best-effort error detail only
                    detail = ""
                finally:
                    exc.close()
                if exc.code < 500:  # 4xx is terminal — retrying a bad key/request never helps.
                    raise RestError(f"{method} {url} → HTTP {exc.code}: {detail}") from exc
                last_err = RestError(f"{method} {url} → HTTP {exc.code}: {detail}")
            except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
                last_err = RestError(f"{method} {url} → {type(exc).__name__}: {exc}")
            if attempt < self._max_retries:
                time.sleep(self._backoff * attempt)
        # Loop exhausted without returning → the last recorded error is the failure.
        raise last_err if last_err else RestError(f"{method} {url} → unknown failure")


def _extract_data_list(payload: Any, ctx: str) -> list:
    """Validate the standard OpenAlgo envelope ``{"status":"success","data":[…]}`` → the list."""
    if not isinstance(payload, dict):
        raise RestError(f"{ctx}: expected a JSON object, got {type(payload).__name__}")
    if payload.get("status") != "success":
        raise RestError(
            f"{ctx}: API status={payload.get('status')!r} message={payload.get('message')!r}"
        )
    data = payload.get("data")
    if not isinstance(data, list):
        raise RestError(f"{ctx}: 'data' missing or not a list")
    return data


def _extract_data_obj(payload: Any, ctx: str) -> dict:
    """Validate the OpenAlgo envelope ``{"status":"success","data":{…}}`` → the object (quotes)."""
    if not isinstance(payload, dict):
        raise RestError(f"{ctx}: expected a JSON object, got {type(payload).__name__}")
    if payload.get("status") != "success":
        raise RestError(
            f"{ctx}: API status={payload.get('status')!r} message={payload.get('message')!r}"
        )
    data = payload.get("data")
    if not isinstance(data, dict):
        raise RestError(f"{ctx}: 'data' missing or not an object")
    return data


# --------------------------------------------------------------------------------------------------
# Resolved-chain result (subtask E)
# --------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class ResolvedChain:
    """The resolved weekly chain for one underlying — the frozen summary the orchestrator/preflight
    reports and the DSM (P3) seeds boundaries from. Keyed in :class:`InstrumentManager` by ``name``."""

    name: str
    option_exchange: str
    expiry: str                  # E_weekly as returned by the API (DD-MMM-YY, uppercase)
    expiry_date: date            # parsed, for logging / rollover reasoning
    strike_step: int             # detected (or fallback) step
    strikes: tuple[float, ...]   # sorted unique strikes (int when integral)
    requested_depth: int
    probe_strike: float          # near-ATM placeholder (median strike); DSM refines with live spot in P3
    n_contracts: int


# --------------------------------------------------------------------------------------------------
# InstrumentManager (subtasks B–E)
# --------------------------------------------------------------------------------------------------
class InstrumentManager:
    """Resolves every configured underlying's weekly chain and exposes the O(1) lookup structures.

    ``resolve()`` performs the REST calls (one expiry POST + one instruments GET per underlying) and
    populates the maps. All maps are keyed by underlying ``name`` / OpenAlgo ``symbol``; no index
    literal appears here. The DSM (P3) reads ``strike_to_symbol_map``/``active_strikes_list`` for
    subscription math; the processor (P4) reads ``tick_size_map`` for M29.
    """

    def __init__(self, config: Config, rest_client: RestClient | None = None):
        self._config = config
        self._rest = rest_client or RestClient(
            config.openalgo["host_server"], config.openalgo["api_key"]
        )
        # name → {strike → {"CE": symbol, "PE": symbol}}
        self.strike_to_symbol_map: dict[str, dict[float, dict[str, str]]] = {}
        # symbol → {"underlying", "strike", "option_type"}
        self.symbol_to_strike_map: dict[str, dict[str, Any]] = {}
        # name → sorted unique strikes
        self.active_strikes_list: dict[str, list[float]] = {}
        # symbol → tick_size (M29)
        self.tick_size_map: dict[str, float] = {}
        # name → ResolvedChain
        self.chains: dict[str, ResolvedChain] = {}
        self._resolved = False

    # -- public API ---------------------------------------------------------------------------------
    @property
    def resolved(self) -> bool:
        """True once :meth:`resolve` has populated the lookup maps (the P6 orchestrator resolves the
        chains exactly once at Milestone 1 and skips a redundant re-fetch on a supervised restart)."""
        return self._resolved

    def resolve(self) -> None:
        """Resolve every configured underlying (looping ``config.underlyings`` — never branching on a
        name). Raises :class:`RestError` on any REST failure or an empty/absent chain."""
        for u in self._config.underlyings:
            self._resolve_underlying(u)
        self._resolved = True

    # -- provenance / replay reconstruction (§3.5.4 HEADER, §8) -------------------------------------
    def to_header_dict(self) -> dict[str, Any]:
        """Serialize the resolved chain for the raw-log HEADER so replay is **self-contained** (plan
        decision 65): per underlying ``{option_exchange, expiry, strike_step, contracts:[[strike,
        ce_sym, pe_sym, tick_size], …]}``. This carries everything the offline processor needs
        (symbol↔strike/type + ``tick_size`` for M29) — so a past-day replay never re-hits REST and never
        reverse-parses symbols. Built from the same maps ``resolve()`` populated; keyed by ``name``."""
        out: dict[str, Any] = {}
        for name, chain in self.chains.items():
            s2s = self.strike_to_symbol_map.get(name, {})
            contracts = []
            for strike in self.active_strikes_list.get(name, []):
                pair = s2s.get(strike, {})
                ce, pe = pair.get("CE"), pair.get("PE")
                tick = self.tick_size_map.get(ce) if ce else None
                if tick is None and pe:
                    tick = self.tick_size_map.get(pe)
                contracts.append([strike, ce, pe, tick])
            out[name] = {
                "option_exchange": chain.option_exchange,
                "expiry": chain.expiry,
                "strike_step": chain.strike_step,
                "contracts": contracts,
            }
        return out

    @classmethod
    def from_header(cls, config: Config, header: dict[str, Any]) -> "InstrumentManager":
        """Reconstruct a fully-resolved :class:`InstrumentManager` from a raw-log HEADER's ``instruments``
        block — **no REST** (plan decision 65). The offline replay uses this so it is correct for a log
        of any age (the live chain may have rolled since). Raises :class:`RestError` if the HEADER lacks
        the block (an old-format log)."""
        if not header:
            raise RestError("raw-log HEADER has no 'instruments' block — cannot reconstruct chains "
                            "(pre-enrichment log; rebuild is not self-contained)")
        im = cls(config)  # a RestClient is constructed but never called
        by_name = {u.name: u for u in config.underlyings}
        for name, block in header.items():
            oexch = block.get("option_exchange")
            expiry = block.get("expiry")
            step = block.get("strike_step")
            contracts = block.get("contracts") or []
            s2s: dict[float, dict[str, str]] = {}
            strikes: list[float] = []
            for row in contracts:
                padded = (list(row) + [None, None, None, None])[:4]
                strike, ce, pe, tick = padded
                strikes.append(strike)
                pair: dict[str, str] = {}
                if ce:
                    pair["CE"] = ce
                    im.symbol_to_strike_map[ce] = {"underlying": name, "strike": strike, "option_type": "CE"}
                    im.tick_size_map[ce] = tick
                if pe:
                    pair["PE"] = pe
                    im.symbol_to_strike_map[pe] = {"underlying": name, "strike": strike, "option_type": "PE"}
                    im.tick_size_map[pe] = tick
                s2s[strike] = pair
            strikes = sorted(set(strikes))
            im.strike_to_symbol_map[name] = s2s
            im.active_strikes_list[name] = strikes
            u = by_name.get(name)
            im.chains[name] = ResolvedChain(
                name=name, option_exchange=oexch, expiry=str(expiry),
                expiry_date=_parse_expiry(expiry) if expiry else date.min,
                strike_step=step, strikes=tuple(strikes),
                requested_depth=u.requested_depth if u else 0,
                probe_strike=strikes[len(strikes) // 2] if strikes else 0,
                n_contracts=len(contracts),
            )
        im._resolved = True
        return im

    def preflight_report(self) -> list[dict[str, Any]]:
        """One dict per resolved underlying for the ``--preflight`` summary (offline; ``actual_depth``
        is filled by the P3 live probe, not here)."""
        return [
            {
                "name": c.name,
                "option_exchange": c.option_exchange,
                "expiry": c.expiry,
                "strike_step": c.strike_step,
                "n_strikes": len(c.strikes),
                "requested_depth": c.requested_depth,
                "probe_strike": c.probe_strike,
            }
            for c in self.chains.values()
        ]

    # -- per-underlying resolution ------------------------------------------------------------------
    def _resolve_underlying(self, u: Underlying) -> None:
        # 1. Weekly expiry (authoritative endpoint; data[0] is E_weekly with the rollover gate met).
        expiries = self._rest.get_expiry(u.name, u.option_exchange)
        if not expiries:
            raise RestError(
                f"[{u.name}] no future expiries returned for {u.option_exchange} — cannot resolve chain"
            )
        e_weekly = str(expiries[0])
        e_date = _parse_expiry(e_weekly)

        # 2. Instrument master (strike grid + symbols + tick_size) for the option exchange.
        rows = self._rest.get_instruments(u.option_exchange)

        # 3. Filter to this underlying's active weekly options.
        opts = self._filter_options(rows, u, e_weekly)
        if not opts:
            raise RestError(
                f"[{u.name}] no option contracts for expiry {e_weekly} in {u.option_exchange}"
            )

        # 4. Strike-step auto-detect + validate.
        strikes = sorted({r["_strike"] for r in opts})
        step = self._detect_strike_step(u, strikes)

        # 5. O(1) maps + tick_size.
        s2s: dict[float, dict[str, str]] = {}
        for r in opts:
            strike, otype, symbol = r["_strike"], r["_otype"], str(r["symbol"])
            s2s.setdefault(strike, {})[otype] = symbol
            self.symbol_to_strike_map[symbol] = {
                "underlying": u.name, "strike": strike, "option_type": otype,
            }
            self.tick_size_map[symbol] = r.get("tick_size")
        self.strike_to_symbol_map[u.name] = s2s
        self.active_strikes_list[u.name] = strikes

        # 6. Frozen summary. Probe strike = median strike (no live spot yet; DSM refines in P3).
        probe = strikes[len(strikes) // 2]
        self.chains[u.name] = ResolvedChain(
            name=u.name,
            option_exchange=u.option_exchange,
            expiry=e_weekly,
            expiry_date=e_date,
            strike_step=step,
            strikes=tuple(strikes),
            requested_depth=u.requested_depth,
            probe_strike=probe,
            n_contracts=len(opts),
        )
        logger.info(
            "[%s] resolved weekly chain: expiry=%s step=%s strikes=%d contracts=%d probe=%s",
            u.name, e_weekly, step, len(strikes), len(opts), probe,
        )

    def _filter_options(
        self, rows: list, u: Underlying, e_weekly: str
    ) -> list[dict[str, Any]]:
        """Keep active weekly option rows for ``u``: matching underlying, an option instrumenttype with
        a resolvable CE/PE and a positive strike, and ``expiry == E_weekly``."""
        e_upper = e_weekly.upper()
        out: list[dict[str, Any]] = []
        for r in rows:
            if not isinstance(r, dict):
                continue
            itype = str(r.get("instrumenttype", "")).upper()
            if itype not in _OPTION_INSTRUMENT_TYPES:
                continue
            if str(r.get("expiry", "")).upper() != e_upper:
                continue
            if not self._matches_underlying(r, u):
                continue
            otype = _option_type(itype, str(r.get("symbol", "")))
            if otype is None:
                continue
            strike = _norm_strike(r.get("strike"))
            if strike is None:
                continue
            enriched = dict(r)
            enriched["_strike"] = strike
            enriched["_otype"] = otype
            out.append(enriched)
        return out

    def _matches_underlying(self, row: dict, u: Underlying) -> bool:
        """Primary: exact ``name`` column match (unambiguous — we already query per option-exchange).
        Fallback (blank ``name``): longest-prefix over the configured names on the ``symbol`` string so
        e.g. NIFTYNXT50 is not shadowed by NIFTY (cf. ``database/qty_freeze_db.py:211-219``)."""
        name = str(row.get("name", "")).strip().upper()
        target = u.name.upper()
        if name:
            return name == target
        # Blank name column: longest-prefix over the configured names on the symbol. An F&O symbol is
        # BASE + DDMMMYY…, so the char right after the base is always a digit — that guard stops NIFTY
        # from matching NIFTYNXT50 (…NXT50 → next char 'N'), which longest-prefix alone cannot do when
        # NIFTYNXT50 is not itself a configured underlying.
        sym = str(row.get("symbol", "")).upper()
        best: str | None = None
        for other in self._config.underlyings:
            on = other.name.upper()
            after = sym[len(on):len(on) + 1]
            if sym.startswith(on) and after.isdigit() and (best is None or len(on) > len(best)):
                best = on
        return best == target

    def _detect_strike_step(self, u: Underlying, strikes: list[float]) -> int:
        """§3.2.3 mode-of-adjacent-differences step detection, validated against
        ``expected_strike_step`` with a warned fallback. ``Counter`` (not ``statistics.mode``) so ties
        never raise and we take the *most common* step, robust to wide far-OTM gaps."""
        if len(strikes) < 2:
            logger.warning(
                "[%s] only %d strike(s) for expiry — cannot detect step, using fallback %s",
                u.name, len(strikes), u.strike_step_fallback,
            )
            return u.strike_step_fallback
        diffs = [b - a for a, b in zip(strikes, strikes[1:]) if b > a]
        if not diffs:
            logger.warning(
                "[%s] no positive strike gaps — using fallback %s", u.name, u.strike_step_fallback
            )
            return u.strike_step_fallback
        step_val = Counter(diffs).most_common(1)[0][0]
        detected = int(step_val) if float(step_val).is_integer() else step_val
        if detected in u.expected_strike_step:
            return detected
        logger.warning(
            "[%s] detected strike step %s not in expected %s — using fallback %s",
            u.name, detected, list(u.expected_strike_step), u.strike_step_fallback,
        )
        return u.strike_step_fallback


# --------------------------------------------------------------------------------------------------
# Module helpers
# --------------------------------------------------------------------------------------------------
def _parse_expiry(value: str) -> date:
    """Parse an OpenAlgo expiry string (``DD-MMM-YY`` uppercase, fallback ``DD-MMM-YYYY``) to a date."""
    text = str(value).strip()
    for fmt in ("%d-%b-%y", "%d-%b-%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise RestError(f"unparseable expiry {value!r} (expected DD-MMM-YY)")


def _option_type(instrumenttype: str, symbol: str) -> str | None:
    """Resolve CE/PE from the instrumenttype tag, falling back to the symbol suffix (OPTIDX/OPTSTK)."""
    if instrumenttype in ("CE", "PE"):
        return instrumenttype
    s = symbol.upper()
    if s.endswith("CE"):
        return "CE"
    if s.endswith("PE"):
        return "PE"
    return None


def _norm_strike(strike: Any) -> float | None:
    """Normalize a master ``strike`` float to an int key when integral (index strikes are), else keep
    the float; reject null/non-numeric/≤0."""
    try:
        f = float(strike)
    except (TypeError, ValueError):
        return None
    if f <= 0:
        return None
    return int(f) if f.is_integer() else f
