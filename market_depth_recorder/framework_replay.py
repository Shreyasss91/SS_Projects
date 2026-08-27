"""Framework replay — the determinism harness for the adaptive depth framework (Plan_002 §22.12, F9).

**A second driver, not a second `replay.py`.** `replay.replay_file` rebuilds the Tier-2 analytical
store by driving :class:`~market_depth_recorder.processor.TickProcessor` directly; it never calls
``run()``, so the framework pass never fires during a rebuild. That is deliberate and stays true: the
metric catalog must not depend on which legs happened to be subscribed. This module therefore replays
the same raw log through the **framework** instead, and writes an allocation log — one record per
rebalance pass — that two independent runs must produce byte-identically (fork F18, option A).

What is real here and what is not, stated once because the distinction is the whole point:

* **Real:** the `FrameworkOrchestrator`, every decision layer inside it, the `BrokerAdapter`, the
  wire rendering, the release-before-claim ordering, the connection pool and its budget, and the spot
  prices — which are read from the recording's own packets, so the window really moves the way the
  market moved it.
* **Simulated:** the broker. The transport records frames and never refuses them, and a leg still
  ``REQUESTED`` after ``confirm_after_passes`` passes is handed a synthesized delivery so the replay
  makes forward progress. Every such confirmation is counted in the record as
  ``simulated_confirmations``.
* **Therefore:** nothing this module produces is broker evidence. It cannot establish reconnect depth
  restoration, the real premium ceiling, or any other broker semantic; both of those remain UNKNOWN.
  It establishes one thing only — that the framework's own allocation behaviour is a deterministic
  function of the tick stream.

Concurrency / FDs: a single synchronous pass. No thread, no socket, no subprocess, no DuckDB, no
SQLite. The only descriptors are the gzip reader and the allocation-log writer, both ``with``-closed.

Genericization: no index name, exchange code, strike step, or depth literal appears here. Underlyings
come from the recorder config, the chains from the log's own HEADER (via
:meth:`InstrumentManager.from_header` — no REST, correct for a log of any age), and every depth
spelling from the capability layer through the adapter.

CLI (its own entry point, so no existing command line changes)::

    python -m market_depth_recorder.framework_replay RAW [-o OUT] [--from HH:MM] [--to HH:MM]
    python -m market_depth_recorder.framework_replay --verify LOG_A LOG_B
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import pathlib
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Iterator, Mapping

from .config import Config, load_config
from .framework_bridge import build_universe
from .instrument_manager import InstrumentManager
from .market_depth_framework import (
    BrokerAdapter,
    DepthType,
    Instrument,
    LegState,
    orchestrator_for,
)
from .utils import IST, get_logger

logger = get_logger(__name__)

SCHEMA_VERSION = 1
_DIGEST_META = "DIGEST"

#: The config that ships beside the recorder, used when the CLI is given no ``--config``.
PACKAGED_CONFIG = pathlib.Path(__file__).resolve().parent / "config.yaml"

#: How many passes a leg may stay unconfirmed before the driver synthesizes its delivery. One pass
#: keeps the subscribe-to-first-packet window open for exactly one rebalance, which is the window the
#: F7.6 fix exists for -- long enough to exercise it, short enough that coverage still converges.
DEFAULT_CONFIRM_AFTER_PASSES = 1


# --------------------------------------------------------------------------------------------------
# Transport (fork F18) -- a recorder, never a socket
# --------------------------------------------------------------------------------------------------
class RecordingTransport:
    """A list with a ``send`` method: the framework's `DepthTransport`, minus the broker.

    Deliberately total — it never raises. A transport failure is a broker behaviour, and this module
    does not model broker behaviours; the failure paths are covered by the adapter's own suite against
    an explicitly failing transport.
    """

    __slots__ = ("frames",)

    def __init__(self) -> None:
        self.frames: list[dict[str, Any]] = []

    def send(self, frame: Mapping[str, Any]) -> None:
        self.frames.append(dict(frame))


# --------------------------------------------------------------------------------------------------
# Stats
# --------------------------------------------------------------------------------------------------
@dataclass
class ReplayStats:
    """What one framework replay did. Every field is JSON-safe."""

    packets: int = 0
    corrupt_lines: int = 0
    passes: int = 0
    records: int = 0
    actions: int = 0
    frames: int = 0
    simulated_confirmations: int = 0
    peak_premium: int = 0
    effective_budget: int = 0
    source_raw: str = ""
    output: str = ""
    digest: str = ""
    first_ts: float | None = None
    last_ts: float | None = None
    underlyings: tuple[str, ...] = ()
    windows_seen: int = 0
    budget_violations: int = 0
    ownership_violations: int = 0
    order_violations: int = 0
    spot_symbols: dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "packets": self.packets,
            "corrupt_lines": self.corrupt_lines,
            "passes": self.passes,
            "records": self.records,
            "actions": self.actions,
            "frames": self.frames,
            "simulated_confirmations": self.simulated_confirmations,
            "peak_premium": self.peak_premium,
            "effective_budget": self.effective_budget,
            "windows_seen": self.windows_seen,
            "budget_violations": self.budget_violations,
            "ownership_violations": self.ownership_violations,
            "order_violations": self.order_violations,
            "underlyings": list(self.underlyings),
        }


# --------------------------------------------------------------------------------------------------
# Raw reading -- mirrors replay.py's tolerance without importing it
# --------------------------------------------------------------------------------------------------
def _load_header(fh) -> dict | None:
    """The log's HEADER meta line, or ``None`` for a pre-enrichment log. Leaves ``fh`` after it."""
    for raw in fh:
        raw = raw.strip()
        if not raw:
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            return None
        return obj if obj.get("meta_type") == "HEADER" else None
    return None


def _ist_minutes(recv_ts: float) -> int:
    dt = datetime.fromtimestamp(recv_ts, tz=IST)
    return dt.hour * 60 + dt.minute


def _in_slice(recv_ts: float, from_t, to_t) -> bool:
    if from_t is None and to_t is None:
        return True
    minutes = _ist_minutes(recv_ts)
    if from_t is not None and minutes < from_t.hour * 60 + from_t.minute:
        return False
    if to_t is not None and minutes > to_t.hour * 60 + to_t.minute:
        return False
    return True


def _packets(fh, stats: ReplayStats, from_t, to_t) -> Iterator[dict]:
    """Every usable packet in the log, in file order, with meta lines and corruption tolerated."""
    for raw in fh:
        raw = raw.strip()
        if not raw:
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            stats.corrupt_lines += 1
            continue
        if obj.get("meta_type") in ("HEADER", "EOF"):
            continue  # a restart writes a second HEADER; both are tolerated
        recv = obj.get("recv_ts")
        if recv is None or not isinstance(recv, (int, float)):
            continue
        if not _in_slice(float(recv), from_t, to_t):
            continue
        yield obj


# --------------------------------------------------------------------------------------------------
# Allocation-log records (fork F19) -- plain .jsonl, diffable by eye
# --------------------------------------------------------------------------------------------------
def _num(value: object) -> float | None:
    """Normalize a float for the log so two runs cannot differ by formatting alone."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        # round() before float() so 24_950.000000000004 and 24_950.0 cannot diverge textually.
        return float(round(float(value), 6))
    return None


def _action_row(action) -> list[object]:
    """One plan action as a positional row: kind, target tier, symbol."""
    return [str(action.kind), str(action.depth), action.instrument.symbol]


def _window_row(window) -> dict[str, Any]:
    return {
        "underlying": window.underlying,
        "status": str(getattr(window.status, "value", window.status)),
        "spot": _num(window.spot),
        "atm": _num(window.atm_strike),
        "lower": _num(window.lower_bound),
        "upper": _num(window.upper_bound),
        "candidates": len(window.candidates),
    }


def _desired_counts(desired: Mapping[Instrument, DepthType]) -> dict[str, dict[str, int]]:
    """Desired coverage per underlying per tier -- a count, not a leg dump, so the log stays readable."""
    counts: dict[str, dict[str, int]] = {}
    for leg, tier in desired.items():
        bucket = counts.setdefault(leg.underlying, {})
        key = str(tier)
        bucket[key] = bucket.get(key, 0) + 1
    return {name: dict(sorted(tiers.items())) for name, tiers in sorted(counts.items())}


def _record(
    *,
    seq: int,
    at: float,
    trigger: str,
    spots: Mapping[str, float | None],
    result,
    dispatch,
    frames: list[dict[str, Any]],
    premium: int,
    budget: int,
    confirmations: int,
) -> dict[str, Any]:
    """One pass, as the value the whole harness compares."""
    return {
        "seq": seq,
        "at": _num(at),
        "trigger": trigger,
        "spots": {name: _num(spots.get(name)) for name in sorted(spots)},
        "windows": [_window_row(w) for w in result.windows],
        "budgets": {name: int(result.budgets[name]) for name in sorted(result.budgets)},
        "desired": _desired_counts(result.desired),
        "actions": [_action_row(a) for a in result.plan.ordered_actions()],
        "removed": [leg.symbol for leg in result.plan.removed],
        "wire": [[frame.get("action"), frame.get("symbol")] for frame in frames],
        "dispatch": {
            "sent": len(dispatch.sent),
            "failed": len(dispatch.failed),
            "refused": len(dispatch.refused),
            "skipped": len(dispatch.skipped),
        },
        "premium_occupancy": premium,
        "effective_budget": budget,
        "simulated_confirmations": confirmations,
    }


def _dump(record: Mapping[str, Any]) -> str:
    """Canonical JSON: keys sorted, no float repr drift, ASCII-safe, one line."""
    return json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False)


# --------------------------------------------------------------------------------------------------
# Invariant checks -- the soak assertions, evaluated on every pass rather than only at the end
# --------------------------------------------------------------------------------------------------
def _owned_tiers(adapter: BrokerAdapter) -> dict[Instrument, set[DepthType]]:
    """Every tier the adapter currently holds per instrument (`REQUESTED` or `DELIVERING`)."""
    owned: dict[Instrument, set[DepthType]] = {}
    for view in adapter.legs():
        if view.state in (LegState.REQUESTED, LegState.DELIVERING):
            owned.setdefault(view.instrument, set()).add(view.tier)
    return owned


def _check_invariants(adapter: BrokerAdapter, frames: list[dict[str, Any]], stats: ReplayStats) -> None:
    """Budget, single-tier ownership, and release-before-claim, checked against the adapter itself."""
    premium = adapter.premium_leg_count()
    stats.peak_premium = max(stats.peak_premium, premium)
    if premium > adapter.effective_budget:
        stats.budget_violations += 1
        logger.error(
            "framework replay: premium occupancy %d exceeds effective budget %d",
            premium, adapter.effective_budget,
        )
    for instrument, tiers in _owned_tiers(adapter).items():
        if len(tiers) > 1:
            stats.ownership_violations += 1
            logger.error(
                "framework replay: %s is owned at %d tiers at once", instrument.symbol, len(tiers)
            )
    # Release-before-claim, read off this pass's own frames: for a symbol that was both released and
    # claimed, the unsubscribe of the old spelling must precede the subscribe of the new one.
    first_claim: dict[str, int] = {}
    last_release: dict[str, int] = {}
    for index, frame in enumerate(frames):
        symbol = str(frame.get("symbol", ""))
        base = symbol.split(":", 1)[0]
        if frame.get("action") == "unsubscribe":
            last_release[base] = index
        else:
            first_claim.setdefault(base, index)
    for base, claim_at in first_claim.items():
        release_at = last_release.get(base)
        if release_at is not None and release_at > claim_at:
            stats.order_violations += 1
            logger.error("framework replay: %s was claimed before its release", base)


# --------------------------------------------------------------------------------------------------
# The driver
# --------------------------------------------------------------------------------------------------
def replay_framework(
    config: Config,
    raw_path: str,
    output_path: str,
    *,
    from_t=None,
    to_t=None,
    confirm_after_passes: int = DEFAULT_CONFIRM_AFTER_PASSES,
    max_packets: int | None = None,
    packets: Iterator[dict] | None = None,
    header: Mapping[str, Any] | None = None,
) -> ReplayStats:
    """Replay one raw log through the framework and write its allocation log.

    Args:
        config: A loaded recorder config whose ``market_depth_framework`` block is present. The
            block's ``enabled`` flag is **not** consulted: replaying is an offline analysis of what
            the framework would do, and refusing to analyse it because the live flag is off would make
            the harness unusable exactly when it is most wanted.
        raw_path: The raw ``.jsonl.gz`` recording. Read-only; never modified, never copied.
        output_path: Where to write the ``.jsonl`` allocation log.
        from_t / to_t: Optional IST time slice, same semantics as `replay.replay_file`.
        confirm_after_passes: How many passes a leg may stay unconfirmed before its delivery is
            synthesized. ``0`` confirms at the end of the claiming pass; a large value never confirms.
        max_packets: Stop after this many packets. Bounds the suite's soak test.
        packets / header: Inject the stream directly instead of opening ``raw_path``. Used by the
            tests, which must run without any file under ``data/``.

    Returns:
        :class:`ReplayStats`, including the digest of the allocation log.
    """
    framework = getattr(config, "framework", None)
    if framework is None:
        raise ValueError(
            "framework replay requires a [market_depth_framework] config block; none is present"
        )
    if int(confirm_after_passes) < 0:
        raise ValueError(f"confirm_after_passes must be >= 0, got {confirm_after_passes!r}")

    stats = ReplayStats()
    stats.source_raw = os.path.basename(raw_path) if raw_path else "<injected>"
    stats.output = output_path

    if packets is None:
        with gzip.open(raw_path, "rt", encoding="utf-8") as fh:
            head = _load_header(fh)
            return _drive(
                config, framework, _packets(fh, stats, from_t, to_t), head, output_path,
                stats=stats, confirm_after_passes=int(confirm_after_passes),
                max_packets=max_packets,
            )
    return _drive(
        config, framework, packets, header, output_path,
        stats=stats, confirm_after_passes=int(confirm_after_passes), max_packets=max_packets,
    )


def _drive(
    config: Config,
    framework,
    packets: Iterator[dict],
    header: Mapping[str, Any] | None,
    output_path: str,
    *,
    stats: ReplayStats,
    confirm_after_passes: int,
    max_packets: int | None,
) -> ReplayStats:
    """The pass loop itself, with the stream already open."""
    instrument_manager = InstrumentManager.from_header(config, (header or {}).get("instruments"))
    universe, expiries = build_universe(instrument_manager)

    vclock = {"t": 0.0}
    clock: Callable[[], float] = lambda: vclock["t"]  # noqa: E731 -- injected, deliberately trivial

    orchestrator = orchestrator_for(
        framework,
        underlyings=[
            {
                "name": u.name,
                "option_exchange": u.option_exchange,
                "initial_window": u.initial_window,
            }
            for u in config.underlyings
        ],
        universe=universe,
        expiries=expiries,
        clock=clock,
    )
    transport = RecordingTransport()
    adapter = BrokerAdapter(orchestrator.capability, transport, clock=clock)

    stats.effective_budget = adapter.effective_budget
    stats.underlyings = tuple(orchestrator.underlyings)
    spot_to_name = {u.spot_symbol: u.name for u in config.underlyings}
    stats.spot_symbols = dict(sorted(spot_to_name.items()))

    spots: dict[str, float | None] = {name: None for name in stats.underlyings}
    claimed_at_pass: dict[str, int] = {}
    seq = 0
    digest = hashlib.sha256()

    with open(output_path, "w", encoding="utf-8", newline="\n") as out:
        for packet in packets:
            recv = float(packet["recv_ts"])
            vclock["t"] = recv
            stats.packets += 1
            if stats.first_ts is None:
                stats.first_ts = recv
            stats.last_ts = recv

            # Real packets are the realism: a claimed leg confirmed by the recording's own data is
            # confirmed by data, not by the driver. A packet for a leg the framework never claimed is
            # ignored by the adapter, which is the correct behaviour on a shared connection.
            adapter.observe(packet)

            symbol = packet.get("symbol")
            if isinstance(symbol, str):
                name = spot_to_name.get(symbol)
                if name is not None:
                    ltp = packet.get("ltp")
                    if isinstance(ltp, (int, float)) and not isinstance(ltp, bool):
                        spots[name] = float(ltp)

            trigger = orchestrator.due(spots)
            if trigger is not None:
                seq += 1
                line = _run_pass(
                    orchestrator, adapter, orchestrator.capability, transport, spots, trigger,
                    seq=seq, at=recv, stats=stats,
                    claimed_at_pass=claimed_at_pass,
                    confirm_after_passes=confirm_after_passes,
                )
                if line is not None:
                    out.write(line + "\n")
                    digest.update(line.encode("utf-8"))
                    stats.records += 1
                else:
                    seq -= 1  # a pass that produced nothing does not consume a sequence number

            if max_packets is not None and stats.packets >= max_packets:
                break

        stats.passes = orchestrator.passes
        stats.digest = "sha256:" + digest.hexdigest()
        terminal = {
            "meta_type": _DIGEST_META,
            "schema_version": SCHEMA_VERSION,
            "digest": stats.digest,
            "records": stats.records,
            "stats": stats.as_dict(),
        }
        out.write(_dump(terminal) + "\n")

    logger.info(
        "framework replay: %s -> %s (%d packets, %d passes, %d records, %d actions, peak premium "
        "%d/%d, %s)",
        stats.source_raw, os.path.basename(output_path), stats.packets, stats.passes,
        stats.records, stats.actions, stats.peak_premium, stats.effective_budget, stats.digest,
    )
    return stats


def _run_pass(
    orchestrator,
    adapter: BrokerAdapter,
    capability,
    transport: RecordingTransport,
    spots: Mapping[str, float | None],
    trigger: str,
    *,
    seq: int,
    at: float,
    stats: ReplayStats,
    claimed_at_pass: dict[str, int],
    confirm_after_passes: int,
) -> str | None:
    """One rebalance pass end to end, returning its allocation-log line (or ``None`` if it did nothing)."""
    result = orchestrator.rebalance(
        spots, adapter.live_snapshot(), rejected=adapter.take_rejections(), trigger=trigger
    )
    if result is None:
        return None

    before = len(transport.frames)
    dispatch = adapter.apply(result.plan)
    frames = transport.frames[before:]
    stats.frames += len(frames)
    stats.actions += len(result.plan.ordered_actions())
    stats.windows_seen += len(result.windows)

    for view in adapter.legs():
        claimed_at_pass.setdefault(view.wire_symbol, seq)

    confirmations = _confirm_stale_legs(
        adapter, capability, seq=seq, claimed_at_pass=claimed_at_pass,
        confirm_after_passes=confirm_after_passes,
    )
    stats.simulated_confirmations += confirmations

    _check_invariants(adapter, frames, stats)
    return _dump(
        _record(
            seq=seq, at=at, trigger=trigger, spots=spots, result=result, dispatch=dispatch,
            frames=frames, premium=adapter.premium_leg_count(),
            budget=adapter.effective_budget, confirmations=confirmations,
        )
    )


def _confirm_stale_legs(
    adapter: BrokerAdapter,
    capability,
    *,
    seq: int,
    claimed_at_pass: Mapping[str, int],
    confirm_after_passes: int,
) -> int:
    """Synthesize a delivery for legs the (absent) broker has not confirmed. Simulation, not evidence.

    Without this the replay would stall: the live snapshot is delivery-derived, so a leg that never
    delivers never becomes live, and every pass would re-plan the same subscription forever. The
    synthesized packet carries the tier's nominal depth because that is what the driver *claimed*, not
    because any broker said so -- which is exactly why the count is reported separately in every
    record.
    """
    premium_depth = capability.premium_depth
    standard_depth = capability.standard_depth
    confirmed = 0
    for view in sorted(adapter.legs(), key=lambda v: v.wire_symbol):
        if view.state is not LegState.REQUESTED:
            continue
        claimed = claimed_at_pass.get(view.wire_symbol)
        if claimed is None or seq - claimed < confirm_after_passes:
            continue
        levels = premium_depth if view.tier is DepthType.PREMIUM else standard_depth
        adapter.observe({"symbol": view.wire_symbol, "depth_levels": levels})
        confirmed += 1
    return confirmed


# --------------------------------------------------------------------------------------------------
# --verify (fork F19) -- name the first divergence, never a bare boolean
# --------------------------------------------------------------------------------------------------
@dataclass
class VerifyResult:
    """The outcome of diffing two allocation logs."""

    identical: bool
    reason: str = ""
    seq: int | None = None
    field_path: str = ""
    left: object = None
    right: object = None

    def describe(self) -> str:
        if self.identical:
            return "identical"
        where = f" at record seq={self.seq}" if self.seq is not None else ""
        what = f" field {self.field_path!r}" if self.field_path else ""
        detail = "" if self.left is None and self.right is None else f": {self.left!r} != {self.right!r}"
        return f"{self.reason}{where}{what}{detail}"


def _read_log(path: str) -> tuple[list[dict], dict | None]:
    records: list[dict] = []
    terminal: dict | None = None
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if obj.get("meta_type") == _DIGEST_META:
                terminal = obj
            else:
                records.append(obj)
    return records, terminal


def _first_difference(left: object, right: object, path: str = "") -> tuple[str, object, object] | None:
    """Depth-first walk naming the first field where two records disagree."""
    if isinstance(left, dict) and isinstance(right, dict):
        for key in sorted(set(left) | set(right)):
            here = f"{path}.{key}" if path else str(key)
            if key not in left or key not in right:
                return here, left.get(key, "<absent>"), right.get(key, "<absent>")
            found = _first_difference(left[key], right[key], here)
            if found is not None:
                return found
        return None
    if isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            return f"{path}[len]", len(left), len(right)
        for index, (a, b) in enumerate(zip(left, right)):
            found = _first_difference(a, b, f"{path}[{index}]")
            if found is not None:
                return found
        return None
    return None if left == right else (path or "<record>", left, right)


def verify_logs(reference_path: str, candidate_path: str) -> VerifyResult:
    """Diff two allocation logs, reporting the **first** divergence rather than a verdict alone."""
    ref_records, ref_meta = _read_log(reference_path)
    cand_records, cand_meta = _read_log(candidate_path)

    for index in range(min(len(ref_records), len(cand_records))):
        found = _first_difference(ref_records[index], cand_records[index])
        if found is not None:
            path, left, right = found
            return VerifyResult(
                False, "records differ", seq=ref_records[index].get("seq"),
                field_path=path, left=left, right=right,
            )
    if len(ref_records) != len(cand_records):
        longer = ref_records if len(ref_records) > len(cand_records) else cand_records
        extra = longer[min(len(ref_records), len(cand_records))]
        return VerifyResult(
            False, "record counts differ", seq=extra.get("seq"),
            field_path="<count>", left=len(ref_records), right=len(cand_records),
        )

    ref_digest = (ref_meta or {}).get("digest")
    cand_digest = (cand_meta or {}).get("digest")
    if ref_digest != cand_digest:
        return VerifyResult(
            False, "digests differ", field_path="digest", left=ref_digest, right=cand_digest
        )
    return VerifyResult(True)


# --------------------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------------------
def _parse_hhmm(value: str):
    hh, _, mm = value.partition(":")
    return datetime.strptime(f"{int(hh):02d}:{int(mm or 0):02d}", "%H:%M").time()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m market_depth_recorder.framework_replay",
        description="Replay a raw recording through the adaptive depth framework (offline; no broker).",
    )
    parser.add_argument("raw", nargs="?", help="raw market_depth_raw_*.jsonl.gz recording (read-only)")
    parser.add_argument("-o", "--output", help="allocation log path (default: alongside the raw log)")
    parser.add_argument(
        "-c", "--config", default=str(PACKAGED_CONFIG), help="recorder config.yaml"
    )
    parser.add_argument("--from", dest="from_t", type=_parse_hhmm, help="IST start HH:MM")
    parser.add_argument("--to", dest="to_t", type=_parse_hhmm, help="IST end HH:MM")
    parser.add_argument("--max-packets", type=int, help="stop after N packets")
    parser.add_argument(
        "--confirm-after-passes", type=int, default=DEFAULT_CONFIRM_AFTER_PASSES,
        help="passes a leg may stay unconfirmed before its delivery is synthesized",
    )
    parser.add_argument(
        "--verify", nargs=2, metavar=("REFERENCE", "CANDIDATE"),
        help="diff two allocation logs and report the first divergence",
    )
    args = parser.parse_args(argv)

    if args.verify:
        result = verify_logs(*args.verify)
        print(result.describe())
        return 0 if result.identical else 1

    if not args.raw:
        parser.error("a raw recording is required unless --verify is used")
    # Fail closed: a missing recording is reported, never silently replaced by another file.
    if not os.path.isfile(args.raw):
        print(f"raw recording not found: {args.raw}", file=sys.stderr)
        return 2

    config = load_config(args.config or str(PACKAGED_CONFIG))
    output = args.output or (os.path.splitext(os.path.splitext(args.raw)[0])[0] + ".allocation.jsonl")
    stats = replay_framework(
        config, args.raw, output,
        from_t=args.from_t, to_t=args.to_t,
        confirm_after_passes=args.confirm_after_passes,
        max_packets=args.max_packets,
    )
    print(_dump({"output": output, "digest": stats.digest, **stats.as_dict()}))
    violations = stats.budget_violations + stats.ownership_violations + stats.order_violations
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
