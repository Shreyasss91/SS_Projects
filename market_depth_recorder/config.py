"""Config loader + validation for the Market Depth Recorder (spec §7.1–§7.3).

``load_config(path)`` parses ``config.yaml``, runs **all** §7.3 validation rules (collecting every
failure, not just the first), computes the provenance ``config_hash`` (§3.5.4/§4.1b), and returns a
frozen typed :class:`Config`. Any validation failure raises :class:`ConfigError` carrying the full
report — the CLI turns that into a stderr report + **exit code 1** (§7.3 rule 5). No silent defaults.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import date
from types import MappingProxyType
from typing import Any
from urllib.parse import urlparse

import yaml

from .metrics import registry
from .utils import parse_ist_hhmm

# Top-level sections that must be present and be mappings (§7.1 template).
_SECTIONS = (
    "openalgo", "recorder", "metrics", "regime", "queues", "file_writer",
    "database", "analytics_db", "reprocess", "websocket", "processor",
)
_REQUIRED_UNDERLYING_KEYS = (
    "name", "spot_symbol", "spot_exchange", "option_exchange",
    "expected_strike_step", "strike_step_fallback",
)


class ConfigError(Exception):
    """Raised when config validation fails. ``errors`` is the full ordered list of problems so the
    operator sees every issue in one pass (§7.3 rule 3 collects ALL failures)."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(f"{len(errors)} config validation error(s)")

    def report(self) -> str:
        lines = ["CONFIG VALIDATION FAILED:"]
        lines += [f"  - {e}" for e in self.errors]
        return "\n".join(lines)


@dataclass(frozen=True)
class Underlying:
    """One entry of ``underlyings[]`` (§7.1). Typed so the engine iterates a list of objects keyed
    by ``name`` rather than branching on symbol literals (genericization contract)."""

    name: str
    spot_symbol: str
    spot_exchange: str
    option_exchange: str
    requested_depth: int
    expected_strike_step: tuple[int, ...]
    strike_step_fallback: int
    initial_window: int
    expansion_threshold: int
    expansion_step: int
    atm_max_strike_range: int


@dataclass(frozen=True)
class Config:
    """Frozen, validated configuration object (§7.3 rule E8: typed, not a raw dict).

    Each top-level section is exposed as a read-only mapping; ``underlyings`` is a tuple of typed
    :class:`Underlying`. ``config_hash`` is the provenance stamp threaded into the raw HEADER line
    (§3.5.4) and both stores' ``recorder_meta`` (§4.1b).
    """

    openalgo: MappingProxyType
    recorder: MappingProxyType
    metrics: MappingProxyType
    regime: MappingProxyType
    queues: MappingProxyType
    file_writer: MappingProxyType
    database: MappingProxyType
    analytics_db: MappingProxyType
    reprocess: MappingProxyType
    websocket: MappingProxyType
    processor: MappingProxyType
    underlyings: tuple[Underlying, ...]
    config_hash: str
    source_path: str


# --------------------------------------------------------------------------------------------------
# config_hash (§3.5.4 / §4.1b) — E7
# --------------------------------------------------------------------------------------------------
def compute_config_hash(raw: dict[str, Any]) -> str:
    """sha256 over the canonicalized ``metrics`` + ``regime`` + ``underlyings`` config — the parts
    that determine the produced column values. Deterministic (sorted keys), so an unchanged config
    hashes identically and any formula/threshold/underlying change flips it (§4.1b, §8.4)."""
    subset = {
        "metrics": raw.get("metrics"),
        "regime": raw.get("regime"),
        "underlyings": raw.get("underlyings"),
    }
    canonical = json.dumps(subset, sort_keys=True, separators=(",", ":"), default=str)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------------------------------
# Validation harness
# --------------------------------------------------------------------------------------------------
class _Validator:
    """Accumulates validation errors instead of raising on the first — the operator gets one complete
    report (§7.3 rule 3). Access helpers guard against missing/mistyped keys so a malformed config
    never crashes the validator itself."""

    def __init__(self, raw: dict[str, Any]):
        self.raw = raw
        self.errors: list[str] = []

    def fail(self, msg: str) -> None:
        self.errors.append(msg)

    def section(self, name: str) -> dict[str, Any]:
        val = self.raw.get(name)
        if not isinstance(val, dict):
            self.fail(f"[{name}] section missing or not a mapping")
            return {}
        return val

    def num(self, section: str, sect: dict, key: str) -> float | None:
        """Fetch a numeric value; records an error and returns None if absent or non-numeric
        (booleans rejected — YAML ``true`` is not a number)."""
        if key not in sect:
            self.fail(f"[{section}] missing required key '{key}'")
            return None
        val = sect[key]
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            self.fail(f"[{section}.{key}] must be numeric, got {val!r}")
            return None
        return val

    def check(self, cond: bool, msg: str) -> None:
        if not cond:
            self.fail(msg)

    def pos_int_list(self, section: str, sect: dict, key: str) -> None:
        val = sect.get(key)
        if not isinstance(val, list) or not val:
            self.fail(f"[{section}.{key}] must be a non-empty list")
            return
        for item in val:
            if isinstance(item, bool) or not isinstance(item, int) or item <= 0:
                self.fail(f"[{section}.{key}] must contain only positive integers, got {item!r}")


def _validate(raw: dict[str, Any], path: str) -> list[str]:
    """Run every §7.3 rule against ``raw``, returning the full error list (empty == valid)."""
    v = _Validator(raw)

    # Structural: sections present.
    for name in _SECTIONS:
        v.section(name)
    if not isinstance(raw.get("underlyings"), list) or not raw.get("underlyings"):
        v.fail("[underlyings] must be a non-empty list")

    recorder = v.section("recorder")
    metrics = v.section("metrics")
    queues = v.section("queues")
    database = v.section("database")
    analytics = v.section("analytics_db")
    websocket = v.section("websocket")
    processor = v.section("processor")
    openalgo = v.section("openalgo")

    # Rule 2 — I/O: output_dir writable (create + delete a temp file; mkdir if missing).
    output_dir = recorder.get("output_dir")
    if not output_dir:
        v.fail("[recorder.output_dir] missing")
    else:
        try:
            os.makedirs(output_dir, exist_ok=True)
            fd, tmp = tempfile.mkstemp(prefix=".wtest_", dir=output_dir)
            os.close(fd)
            os.unlink(tmp)
        except OSError as exc:
            v.fail(f"[recorder.output_dir] not writable: {output_dir!r} ({exc})")

    # Rule 4 — health_file_path parent dir writable/creatable.
    health_path = recorder.get("health_file_path")
    if not health_path:
        v.fail("[recorder.health_file_path] missing")
    else:
        parent = os.path.dirname(os.path.abspath(health_path))
        try:
            os.makedirs(parent, exist_ok=True)
            if not os.access(parent, os.W_OK):
                v.fail(f"[recorder.health_file_path] parent dir not writable: {parent!r}")
        except OSError as exc:
            v.fail(f"[recorder.health_file_path] parent dir not creatable: {parent!r} ({exc})")

    # Rule 6 — URL validation.
    _check_url(v, "openalgo.host_server", openalgo.get("host_server"), {"http", "https"})
    _check_url(v, "openalgo.websocket_url", openalgo.get("websocket_url"), {"ws", "wss"})
    if not openalgo.get("api_key"):
        v.fail("[openalgo.api_key] must be a non-empty string")

    # Rule 3 — session window.
    start_t = end_t = None
    try:
        start_t = parse_ist_hhmm(recorder["session_start"])
    except (KeyError, ValueError) as exc:
        v.fail(f"[recorder.session_start] invalid: {exc}")
    try:
        end_t = parse_ist_hhmm(recorder["session_end"])
    except (KeyError, ValueError) as exc:
        v.fail(f"[recorder.session_end] invalid: {exc}")
    if start_t and end_t and not (start_t < end_t):
        v.fail("[recorder] session_start must be < session_end")

    # Rule 3 — database.batch_write_interval_ms ∈ [500, 5000].
    bwi = v.num("database", database, "batch_write_interval_ms")
    if bwi is not None:
        v.check(500 <= bwi <= 5000, "[database.batch_write_interval_ms] must be in [500, 5000]")

    # Rule 3 — live SQLite writer bounds (§3.6.1–§3.6.4, consumed by SQLiteLiveWriter in P5).
    batch_size = v.num("database", database, "batch_size")
    if batch_size is not None:
        v.check(1 <= batch_size <= 5000, "[database.batch_size] must be in [1, 5000]")
    cache_mb = v.num("database", database, "cache_size_mb")
    if cache_mb is not None:
        v.check(cache_mb >= 1, "[database.cache_size_mb] must be >= 1")
    wal_ckpt = v.num("database", database, "wal_checkpoint_interval_sec")
    if wal_ckpt is not None:
        v.check(wal_ckpt >= 30, "[database.wal_checkpoint_interval_sec] must be >= 30")

    # Rule 3 — analytics store bounds.
    mem = v.num("analytics_db", analytics, "memory_limit_mb")
    if mem is not None:
        v.check(mem >= 256, "[analytics_db.memory_limit_mb] must be >= 256")
    threads = v.num("analytics_db", analytics, "threads")
    if threads is not None:
        v.check(1 <= threads <= 64, "[analytics_db.threads] must be in [1, 64]")
    write_backend = analytics.get("write_backend")
    v.check(write_backend in {"executemany", "arrow"},
            f"[analytics_db.write_backend] must be 'executemany' or 'arrow', got {write_backend!r}")

    # Rule 3 — enum fields.
    transport = websocket.get("transport")
    v.check(transport in {"sdk", "raw"},
            f"[websocket.transport] must be 'sdk' or 'raw', got {transport!r}")
    # Raw transport heartbeat: websocket-client run_forever() requires ping_interval > ping_timeout,
    # else it raises "Ensure ping_interval > ping_timeout" on the FEED thread. Fast-fail here rather
    # than crashing a background thread at connect time.
    hb_interval = v.num("websocket", websocket, "heartbeat_interval_sec")
    hb_timeout = v.num("websocket", websocket, "heartbeat_timeout_sec")
    if hb_interval is not None and hb_timeout is not None:
        v.check(0 < hb_timeout < hb_interval,
                "[websocket] require 0 < heartbeat_timeout_sec < heartbeat_interval_sec "
                "(websocket-client run_forever needs ping_interval > ping_timeout)")
    mode = processor.get("mode")
    v.check(mode in {"thread", "process"},
            f"[processor.mode] must be 'thread' or 'process', got {mode!r}")
    if mode == "process":
        shards = v.num("processor", processor, "shards")
        if shards is not None:
            v.check(shards >= 1, "[processor.shards] must be >= 1 when processor.mode == 'process'")

    # Rule 3 — watermark ordering + audit-queue capacity.
    warn = v.num("queues", queues, "warn_watermark_pct")
    crit = v.num("queues", queues, "critical_watermark_pct")
    if warn is not None and crit is not None:
        v.check(0 < warn < crit <= 100,
                "[queues] require 0 < warn_watermark_pct < critical_watermark_pct <= 100")
    max_q = v.num("queues", queues, "max_queue_size")
    raw_q = v.num("queues", queues, "raw_file_queue_max")
    if max_q is not None and raw_q is not None:
        v.check(raw_q >= max_q,
                "[queues.raw_file_queue_max] must be >= queues.max_queue_size (audit queue outlasts analytics)")

    # Rule 3 — non-empty positive-int lists.
    v.pos_int_list("metrics", metrics, "time_windows_sec")
    v.pos_int_list("metrics", metrics, "round_number_multiples")

    # Rule 3 — M25 probe size must be a positive number (§3.4.2-F).
    fpq = v.num("metrics", metrics, "fill_probe_qty")
    if fpq is not None:
        v.check(fpq > 0, "[metrics.fill_probe_qty] must be > 0")

    # Rule 3 — regime classifier thresholds must be numeric (§3.4.4-C). This guards the PyYAML
    # exponent trap: `5.0e6` (no sign) parses as the STRING "5.0e6", which then crashes the classifier
    # mid-session at `nop > theta_pressure` (float > str) once full-depth data makes NOP non-null.
    # v.num turns that latent runtime crash into a clear startup failure — write the value as
    # `5000000.0` or `5.0e+6` so PyYAML parses it as a float.
    regime = v.section("regime")
    for key in ("theta_pressure", "theta_bias", "theta_pinning", "theta_spread",
                "quote_stability_min"):
        v.num("regime", regime, key)

    # Rule 3 — session guards.
    disk = v.num("recorder", recorder, "min_free_disk_mb")
    if disk is not None:
        v.check(disk >= 0, "[recorder.min_free_disk_mb] must be >= 0")
    dci = v.num("recorder", recorder, "disk_check_interval_sec")
    if dci is not None:
        v.check(dci >= 5, "[recorder.disk_check_interval_sec] must be >= 5")

    # Rule 3 — P6 orchestrator supervisor bounds (§3.1.3, consumed by RecorderOrchestrator).
    sup = v.num("recorder", recorder, "supervisor_interval_sec")
    if sup is not None:
        v.check(sup >= 1, "[recorder.supervisor_interval_sec] must be >= 1")
    mra = v.num("recorder", recorder, "max_restart_attempts")
    if mra is not None:
        v.check(mra >= 0, "[recorder.max_restart_attempts] must be >= 0")
    skip = recorder.get("skip_non_trading_days")
    v.check(isinstance(skip, bool), "[recorder.skip_non_trading_days] must be a boolean")
    # P10-B: optional dated sub-folder layout for the day's data (defaults to flat when absent).
    partitioned = recorder.get("date_partitioned", False)
    v.check(isinstance(partitioned, bool), "[recorder.date_partitioned] must be a boolean")
    holidays = recorder.get("trading_holidays", [])
    if not isinstance(holidays, list):
        v.fail("[recorder.trading_holidays] must be a list")
    elif skip is True:
        for h in holidays:
            try:
                date.fromisoformat(str(h))
            except ValueError:
                v.fail(f"[recorder.trading_holidays] '{h}' is not a valid YYYY-MM-DD date")

    # Rule 3 — live_metrics membership against the registry (§3.4.0).
    _validate_live_metrics(v, recorder.get("live_metrics"))

    # Rule 3 — per-underlying checks.
    _validate_underlyings(v, raw.get("underlyings"))

    return v.errors


def _check_url(v: _Validator, key: str, value: Any, schemes: set[str]) -> None:
    if not isinstance(value, str) or not value:
        v.fail(f"[{key}] must be a non-empty URL string")
        return
    parsed = urlparse(value)
    if parsed.scheme not in schemes or not parsed.netloc:
        v.fail(f"[{key}] must be a valid {'/'.join(sorted(schemes))} URL, got {value!r}")


def _validate_live_metrics(v: _Validator, live_metrics: Any) -> None:
    if live_metrics == "all":
        return
    if not isinstance(live_metrics, list) or not live_metrics:
        v.fail("[recorder.live_metrics] must be a non-empty list or the literal 'all'")
        return
    known = registry.known_names()
    for name in live_metrics:
        if name not in known:
            v.fail(f"[recorder.live_metrics] unknown metric/aggregate '{name}' (not in the metric registry)")


def _validate_underlyings(v: _Validator, underlyings: Any) -> None:
    if not isinstance(underlyings, list):
        return  # already reported as structural error
    seen: set[str] = set()
    for idx, u in enumerate(underlyings):
        tag = f"underlyings[{idx}]"
        if not isinstance(u, dict):
            v.fail(f"[{tag}] must be a mapping")
            continue
        name = u.get("name")
        tag = f"underlyings[{name or idx}]"
        # Required keys present + non-empty.
        for key in _REQUIRED_UNDERLYING_KEYS:
            if not u.get(key) and u.get(key) != 0:
                v.fail(f"[{tag}] missing/empty required key '{key}'")
        # Unique name.
        if name:
            if name in seen:
                v.fail(f"[{tag}] duplicate underlying name '{name}'")
            seen.add(name)
        # expected_strike_step non-empty positive-int list.
        ess = u.get("expected_strike_step")
        if not isinstance(ess, list) or not ess:
            v.fail(f"[{tag}.expected_strike_step] must be a non-empty list")
            ess = []
        else:
            for s in ess:
                if isinstance(s, bool) or not isinstance(s, int) or s <= 0:
                    v.fail(f"[{tag}.expected_strike_step] must contain positive integers, got {s!r}")
        # strike_step_fallback ∈ expected_strike_step.
        fb = u.get("strike_step_fallback")
        if ess and fb not in ess:
            v.fail(f"[{tag}.strike_step_fallback] {fb!r} must be one of expected_strike_step {ess}")
        # expansion_threshold < initial_window.
        et, iw = u.get("expansion_threshold"), u.get("initial_window")
        if isinstance(et, int) and isinstance(iw, int):
            v.check(et < iw, f"[{tag}] expansion_threshold ({et}) must be < initial_window ({iw})")
        else:
            v.fail(f"[{tag}] expansion_threshold and initial_window must be integers")


# --------------------------------------------------------------------------------------------------
# Public loader
# --------------------------------------------------------------------------------------------------
def load_config(path: str) -> Config:
    """Load + validate ``config.yaml`` at ``path``. Raises :class:`ConfigError` (with the full report)
    on any failure; otherwise returns a frozen :class:`Config`."""
    # Rule 1 — well-formed YAML.
    try:
        with open(path, encoding="utf-8") as fh:
            raw = yaml.safe_load(fh)
    except FileNotFoundError as exc:
        raise ConfigError([f"config file not found: {path!r} ({exc})"]) from exc
    except yaml.YAMLError as exc:
        raise ConfigError([f"config.yaml is not well-formed YAML: {exc}"]) from exc
    if not isinstance(raw, dict):
        raise ConfigError([f"config root must be a mapping, got {type(raw).__name__}"])

    errors = _validate(raw, path)
    if errors:
        raise ConfigError(errors)

    return _build(raw, path)


def _build(raw: dict[str, Any], path: str) -> Config:
    """Assemble the frozen Config from an already-validated dict."""
    underlyings = tuple(
        Underlying(
            name=u["name"],
            spot_symbol=u["spot_symbol"],
            spot_exchange=u["spot_exchange"],
            option_exchange=u["option_exchange"],
            requested_depth=u["requested_depth"],
            expected_strike_step=tuple(u["expected_strike_step"]),
            strike_step_fallback=u["strike_step_fallback"],
            initial_window=u["initial_window"],
            expansion_threshold=u["expansion_threshold"],
            expansion_step=u["expansion_step"],
            atm_max_strike_range=u["atm_max_strike_range"],
        )
        for u in raw["underlyings"]
    )
    return Config(
        openalgo=MappingProxyType(dict(raw["openalgo"])),
        recorder=MappingProxyType(dict(raw["recorder"])),
        metrics=MappingProxyType(dict(raw["metrics"])),
        regime=MappingProxyType(dict(raw["regime"])),
        queues=MappingProxyType(dict(raw["queues"])),
        file_writer=MappingProxyType(dict(raw["file_writer"])),
        database=MappingProxyType(dict(raw["database"])),
        analytics_db=MappingProxyType(dict(raw["analytics_db"])),
        reprocess=MappingProxyType(dict(raw["reprocess"])),
        websocket=MappingProxyType(dict(raw["websocket"])),
        processor=MappingProxyType(dict(raw["processor"])),
        underlyings=underlyings,
        config_hash=compute_config_hash(raw),
        source_path=os.path.abspath(path),
    )
