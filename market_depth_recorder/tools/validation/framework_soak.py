#!/usr/bin/env python3
"""Soak the adaptive depth framework over a whole session, offline, and report what it did.

Replays a raw ``.jsonl.gz`` through the **real** orchestrator and the **real** ``BrokerAdapter``
(`market_depth_recorder/framework_replay.py`), then summarises the session: pass counts by trigger,
subscription churn, the premium-occupancy histogram, per-pass wall time, and peak RSS.

Inputs
  RAW           raw market-depth .jsonl.gz to replay (read-only; never modified)
  --config      config.yaml (default: the packaged market_depth_recorder/config.yaml)
  --out         allocation log path (default: a temp file, removed after)
  --report      optional markdown report path
  --ledger      optional JSONL file to append the summary record to
  --repeat      replay N times and require every run byte-identical (default 2)
  --confirm-after-passes  passes a leg may stay unconfirmed before delivery is synthesized

Output
  A human summary to stdout, optionally a markdown report and a JSON ledger record.

Exit codes
  0  soak completed with no invariant violation and byte-identical repeats
  1  an invariant was violated, or two replays of one log diverged
  2  usage / runtime error (missing file, missing psutil, ...)

----------------------------------------------------------------------------------------
What this tool is, and is not

It is a **determinism and invariant** soak. The transport is a list; no socket is opened, no broker is
contacted, and a leg the (absent) broker never confirms is confirmed by the driver so the replay can
make progress. Every such confirmation is counted and reported separately.

It is therefore **not broker evidence**. It cannot establish reconnect depth restoration, the real
premium ceiling, or any other broker behaviour; those remain UNKNOWN and are settled only by F10's
live run. Nothing in its report may be cited as a broker fact.

Related documentation
  Documents/framework_replay.md
  plans/Plan_002_market_depth_framework_implementation.md  (§22.12, F9; forks F18-F21)
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import pathlib
import sys
import tempfile
import threading
import time

# Allow running as a plain script: SS_Projects root is .../tools/validation -> up 3.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

_PACKAGED_CONFIG = pathlib.Path(__file__).resolve().parents[2] / "config.yaml"


class PeakRSS(threading.Thread):
    """Background sampler of this process's resident set size; reports the peak seen."""

    def __init__(self, proc, interval: float = 0.2):
        super().__init__(daemon=True)
        self._proc, self._interval, self._stop = proc, interval, threading.Event()
        self.peak = 0

    def run(self) -> None:
        while not self._stop.is_set():
            try:
                self.peak = max(self.peak, self._proc.memory_info().rss)
            except Exception:  # noqa: BLE001 - a sampling miss must never abort the soak
                pass
            self._stop.wait(self._interval)

    def stop(self) -> None:
        self._stop.set()


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="framework_soak.py",
        description="Soak the adaptive depth framework over a session, offline. Not broker evidence.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog="Exit: 0 clean, 1 invariant violation or divergence, 2 error.",
    )
    p.add_argument("raw", metavar="RAW", help="raw market-depth .jsonl.gz to replay (read-only)")
    p.add_argument("--config", default=str(_PACKAGED_CONFIG), help="path to config.yaml")
    p.add_argument("--out", default=None, help="allocation log (default: temp file, removed after)")
    p.add_argument("--report", default=None, help="optional markdown report path")
    p.add_argument("--ledger", default=None, help="optional JSONL file to append the summary to")
    p.add_argument("--repeat", type=int, default=2, help="replays required to be byte-identical")
    p.add_argument("--max-packets", type=int, default=None, help="stop after N packets")
    p.add_argument("--confirm-after-passes", type=int, default=None,
                   help="passes a leg may stay unconfirmed before its delivery is synthesized")
    return p.parse_args(argv)


def _read_records(path: str) -> tuple[list[dict], dict | None]:
    records, terminal = [], None
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if obj.get("meta_type") == "DIGEST":
                terminal = obj
            else:
                records.append(obj)
    return records, terminal


def _min_flip_gap(records: list[dict]) -> float | None:
    """The shortest virtual-time gap between two tier flips of the *same* leg, or ``None``.

    This is the churn cooldown observed rather than configured: it must not be smaller than
    ``depth_allocator.churn_cooldown_seconds``.
    """
    last: dict[str, float] = {}
    smallest: float | None = None
    for rec in records:
        for kind, _depth, symbol in rec["actions"]:
            if kind not in ("upgrade", "downgrade"):
                continue
            previous = last.get(symbol)
            if previous is not None:
                gap = rec["at"] - previous
                smallest = gap if smallest is None else min(smallest, gap)
            last[symbol] = rec["at"]
    return None if smallest is None else round(smallest, 3)


def _file_digest(path: str) -> str:
    """sha256 of a file, read in chunks. Provenance for the report; the file is only ever read."""
    import hashlib

    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def summarise(records: list[dict]) -> dict:
    """Turn an allocation log into the numbers the report is made of."""
    triggers: collections.Counter = collections.Counter()
    kinds: collections.Counter = collections.Counter()
    occupancy: collections.Counter = collections.Counter()
    per_symbol_flips: collections.Counter = collections.Counter()
    wire_ops: collections.Counter = collections.Counter()
    budgets: dict[str, list[int]] = {}

    for rec in records:
        triggers[rec["trigger"]] += 1
        occupancy[rec["premium_occupancy"]] += 1
        for kind, _depth, symbol in rec["actions"]:
            kinds[kind] += 1
            if kind in ("upgrade", "downgrade"):
                per_symbol_flips[symbol] += 1
        for action, _symbol in rec["wire"]:
            wire_ops[action] += 1
        for name, value in rec["budgets"].items():
            budgets.setdefault(name, []).append(int(value))

    churny = per_symbol_flips.most_common(5)
    return {
        "passes_with_an_unresolved_window": sum(
            1 for r in records if any(w["status"] != "resolved" for w in r["windows"])
        ),
        "min_seconds_between_flips_of_one_leg": _min_flip_gap(records),
        "passes": len(records),
        "triggers": dict(sorted(triggers.items())),
        "actions": dict(sorted(kinds.items())),
        "wire_ops": dict(sorted(wire_ops.items())),
        "premium_occupancy_histogram": {str(k): v for k, v in sorted(occupancy.items())},
        "premium_occupancy_max": max(occupancy) if occupancy else 0,
        "tier_flips_total": sum(per_symbol_flips.values()),
        "tier_flips_distinct_legs": len(per_symbol_flips),
        "churniest_legs": [{"symbol": s, "flips": n} for s, n in churny],
        "budget_per_underlying": {
            name: {"min": min(v), "max": max(v)} for name, v in sorted(budgets.items())
        },
    }


def _render_report(payload: dict) -> str:
    """The written report (F20). Plain markdown, no icons, and it states its own limits."""
    stats, summary = payload["stats"], payload["summary"]
    lines = [
        "# Framework soak report (F9 / F20)",
        "",
        f"- Generated: {payload['generated_at']} (UTC, wall clock of the reporting run only)",
        f"- Config: `{payload['config']}`",
        f"- Allocation-log digest: `{payload['digest']}`",
        f"- Replays required byte-identical: {payload['repeat']} "
        f"({'all identical' if payload['identical'] else 'DIVERGED'})",
        "",
        "## Provenance of the recording",
        "",
        f"- Path as given: `{payload['source_path']}`",
        f"- File: `{payload['source_raw']}` ({payload['source_raw_bytes']} bytes)",
        f"- Recording sha256: `{payload['source_sha256']}`",
        "",
        "The recording was opened **read-only** and never modified, copied into the repository, or",
        "committed. It is not the harness's deterministic test fixture -- that is a synthetic session",
        "generated inside the test suite -- and nothing here is used to infer broker capacity,",
        "reconnect behaviour, or any other broker semantic.",
        "",
        "## What this is not",
        "",
        "This soak ran offline against a recording transport. It opened no socket and contacted no",
        "broker. It is a determinism and invariant result, **not broker evidence**: reconnect depth",
        "restoration and the real premium ceiling remain UNKNOWN and are settled only by a live run.",
        "",
        "## Session",
        "",
        f"- Packets read: {stats['packets']} (corrupt lines tolerated: {stats['corrupt_lines']})",
        f"- Rebalance passes: {summary['passes']}",
        f"- Trigger mix: {summary['triggers']}",
        f"- Underlyings: {', '.join(stats['underlyings'])}",
        f"- Effective premium budget: {stats['effective_budget']}",
        f"- Simulated confirmations (driver, not broker): {stats['simulated_confirmations']}",
        "",
        "## Allocation behaviour",
        "",
        f"- Plan actions by kind: {summary['actions']}",
        f"- Wire operations: {summary['wire_ops']}",
        f"- Tier flips: {summary['tier_flips_total']} across "
        f"{summary['tier_flips_distinct_legs']} distinct legs",
        f"- Churniest legs: {summary['churniest_legs']}",
        f"- Per-underlying budget range: {summary['budget_per_underlying']}",
        "",
        "### Premium-occupancy histogram (occupancy -> passes)",
        "",
        "| Premium legs held | Passes |",
        "|---|---|",
    ]
    for occupancy, passes in summary["premium_occupancy_histogram"].items():
        lines.append(f"| {occupancy} | {passes} |")
    lines += [
        "",
        f"Peak occupancy {summary['premium_occupancy_max']} of an effective budget of "
        f"{stats['effective_budget']}.",
        "",
        f"{summary['passes_with_an_unresolved_window']} of {summary['passes']} passes ran while at "
        "least one underlying still had no spot -- a premium-eligible underlying with no spot has no "
        "window, so it can hold no premium leg. Zero-occupancy passes come from that, not from the "
        "allocator declining to spend its budget.",
        "",
        "## Invariants",
        "",
        "| Invariant | Violations |",
        "|---|---|",
        f"| Premium occupancy never exceeds the effective budget | {stats['budget_violations']} |",
        f"| No instrument owned at two tiers at once | {stats['ownership_violations']} |",
        f"| Obsolete tier released before the new tier is claimed (F7.6) | "
        f"{stats['order_violations']} |",
        "",
        f"Shortest observed gap between two tier flips of one leg: "
        f"{summary['min_seconds_between_flips_of_one_leg']} s "
        f"(configured churn cooldown: {payload['churn_cooldown_seconds']} s).",
        "",
        "## Cost",
        "",
        f"- Wall time: {payload['wall_s']:.2f} s for {payload['repeat']} replays",
        f"- Mean pass wall time: {payload['pass_ms_mean']:.3f} ms",
        f"- Peak RSS: {payload['peak_rss_mb']:.1f} MB"
        + ("" if payload["peak_rss_mb"] else " (psutil unavailable; not measured)"),
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    # Fail closed: a missing recording is reported, never silently replaced by another file.
    if not os.path.isfile(args.raw):
        print(f"error: RAW not found: {args.raw}", file=sys.stderr)
        return 2
    if not os.path.isfile(args.config):
        print(f"error: config not found: {args.config}", file=sys.stderr)
        return 2
    if args.repeat < 1:
        print("error: --repeat must be >= 1", file=sys.stderr)
        return 2

    from market_depth_recorder import framework_replay as FR
    from market_depth_recorder.config import load_config

    try:
        import psutil

        sampler = PeakRSS(psutil.Process(os.getpid()))
    except ImportError:
        psutil, sampler = None, None

    cfg = load_config(args.config)
    if cfg.framework is None:
        print("error: config has no market_depth_framework block", file=sys.stderr)
        return 2

    out = args.out or os.path.join(tempfile.gettempdir(), f"framework_soak_{os.getpid()}.jsonl")
    remove_out = args.out is None
    kwargs = {"max_packets": args.max_packets}
    if args.confirm_after_passes is not None:
        kwargs["confirm_after_passes"] = args.confirm_after_passes

    if sampler is not None:
        sampler.start()
    started = time.perf_counter()
    digests: list[str] = []
    payloads: list[bytes] = []
    stats = None
    extra_paths: list[str] = []
    try:
        for run_index in range(args.repeat):
            path = out if run_index == 0 else f"{out}.{run_index}"
            if run_index:
                extra_paths.append(path)
            stats = FR.replay_framework(cfg, args.raw, path, **kwargs)
            digests.append(stats.digest)
            with open(path, "rb") as fh:
                payloads.append(fh.read())
        wall = time.perf_counter() - started
    finally:
        if sampler is not None:
            sampler.stop()

    identical = len(set(digests)) == 1 and len(set(payloads)) == 1
    records, _terminal = _read_records(out)
    summary = summarise(records)
    per_pass_ms = (wall / args.repeat) * 1000.0 / max(len(records), 1)

    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_path": args.raw,
        "source_raw": os.path.basename(args.raw),
        "source_raw_bytes": os.path.getsize(args.raw),
        "source_sha256": _file_digest(args.raw),
        "config": os.path.basename(args.config),
        "churn_cooldown_seconds": cfg.framework.depth_allocator["churn_cooldown_seconds"],
        "digest": digests[0] if digests else "",
        "repeat": args.repeat,
        "identical": identical,
        "wall_s": wall,
        # Wall time divided by passes. A per-pass distribution would need the driver to time each
        # pass, which would put a wall clock inside a module whose determinism guard forbids one --
        # so the mean is reported and no percentile is invented from it.
        "pass_ms_mean": per_pass_ms,
        "peak_rss_mb": (sampler.peak / (1024 * 1024)) if sampler is not None else 0.0,
        "stats": stats.as_dict() if stats is not None else {},
        "summary": summary,
    }

    violations = (
        payload["stats"].get("budget_violations", 0)
        + payload["stats"].get("ownership_violations", 0)
        + payload["stats"].get("order_violations", 0)
    )
    if args.report:
        with open(args.report, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(_render_report(payload))
        print(f"report written: {args.report}")
    if args.ledger:
        with open(args.ledger, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(payload, sort_keys=True) + "\n")

    print(
        f"soak: {payload['source_raw']} packets={payload['stats'].get('packets', 0)} "
        f"passes={summary['passes']} actions={summary['actions']} "
        f"peak_premium={summary['premium_occupancy_max']}/"
        f"{payload['stats'].get('effective_budget', 0)} "
        f"violations={violations} identical={identical} "
        f"wall={wall:.2f}s peak_rss={payload['peak_rss_mb']:.1f}MB"
    )

    for path in ([out] if remove_out else []) + extra_paths:
        try:
            os.remove(path)
        except OSError:
            pass
    return 0 if (identical and not violations) else 1


if __name__ == "__main__":
    raise SystemExit(main())
