#!/usr/bin/env python3
"""Watch a live F10 validation session from the outside and decide, by rule, when to abort it.

Reads the recorder's own ``health.json`` on a fixed cadence, appends every sample to a JSONL
timeline, and classifies each sample against the F10 abort criteria. It **observes only**: it opens
no socket, contacts no broker, imports no recorder runtime module, holds no recorder lock, and never
writes into the recorder's data path. Stopping the run is always an operator action -- this tool
tells the operator *when*, and leaves the *doing* to them (Documents/F10_LIVE_VALIDATION.md, D).

Inputs
  HEALTH        path to the live health.json (default: derived from --config)
  --config      config.yaml, read for the queue watermarks the thresholds are derived from
  --out         JSONL timeline to append samples to (default: alongside health.json)
  --interval    seconds between samples (default 15)
  --sustain     consecutive samples a non-instant condition must hold to become HARD (default 3)
  --once        take a single sample, classify it, and exit (for spot checks and tests)
  --render      render an F26 evidence skeleton from an existing timeline instead of sampling

Exit codes
  0  the session ran to the end of the watch with no HARD condition
  1  a HARD abort condition fired (the operator must act; this tool has not acted)
  2  usage / runtime error (missing health file, unreadable config, ...)

----------------------------------------------------------------------------------------
Where the thresholds come from

Every numeric threshold is either read from ``config.yaml`` or taken from a figure the project has
already committed to elsewhere. Two exceptions are marked HOST below, because the system does not
define them; they are host facts, and the runbook says so rather than hiding it.

  queues.max_queue_size, queues.raw_file_queue_max      config.yaml
  queues.warn_watermark_pct / critical_watermark_pct    config.yaml (the same lines PROCESSOR
                                                        derives its own degraded levels from)
  cycle_ms soft 30 ms                                   eod_report._CYCLE_MS_TARGET
  cycle_ms hard 500 ms                                  half the 1 s real-time budget; P10-E notes
                                                        record that the real signal is "cycle_ms
                                                        approaching 1000 ms"
  rss_mb soft 500 MB                                    eod_report._RSS_MB_TARGET
  rss_mb hard 2048 MB                                   HOST -- the recorder runs on an 8 GB machine
  raw_dropped_total > 0                                 the lossless-raw invariant (CLAUDE.md); the
                                                        one instant, no-sustain abort
  premium_legs > effective_budget                       a framework invariant, instant

Related documentation
  Documents/F10_LIVE_VALIDATION.md                      the runbook this tool serves
  plans/Plan_002_market_depth_framework_implementation.md  (§22.13, F10; forks F22-F26)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

HARD = "HARD"
SOFT = "SOFT"

CYCLE_MS_SOFT = 30.0      # eod_report._CYCLE_MS_TARGET
CYCLE_MS_HARD = 500.0     # half the 1 s per-second budget
RSS_MB_SOFT = 500.0       # eod_report._RSS_MB_TARGET
RSS_MB_HARD = 2048.0      # HOST: an 8 GB machine
DEFAULT_INTERVAL = 15.0
DEFAULT_SUSTAIN = 3

#: Conditions that abort on their first observation, because by the time they repeat the thing they
#: protect is already gone.
INSTANT = frozenset({"raw_loss", "budget_exceeded"})


# --------------------------------------------------------------------------------------------------
# Thresholds
# --------------------------------------------------------------------------------------------------
def thresholds_from(config_path: str) -> dict:
    """Derive the numeric abort thresholds from the recorder's own configuration.

    Reading them rather than restating them is deliberate: an operator who raises
    ``max_queue_size`` for the run must not silently leave this tool watching the old number.
    """
    import yaml  # local import: the tool is usable for --render without a config

    with open(config_path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    q = raw.get("queues") or {}
    try:
        max_q = float(q["max_queue_size"])
        raw_max = float(q["raw_file_queue_max"])
        warn_pct = float(q["warn_watermark_pct"])
        crit_pct = float(q["critical_watermark_pct"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"config {config_path}: queues block incomplete or non-numeric ({exc})") from exc
    return {
        "proc_warn": max_q * warn_pct / 100.0,
        "proc_crit": max_q * crit_pct / 100.0,
        "db_warn": max_q * warn_pct / 100.0,
        "db_crit": max_q * crit_pct / 100.0,
        "raw_warn": raw_max * warn_pct / 100.0,
        "raw_crit": raw_max * crit_pct / 100.0,
        "cycle_ms_soft": CYCLE_MS_SOFT,
        "cycle_ms_hard": CYCLE_MS_HARD,
        "rss_mb_soft": RSS_MB_SOFT,
        "rss_mb_hard": RSS_MB_HARD,
    }


# --------------------------------------------------------------------------------------------------
# Sampling
# --------------------------------------------------------------------------------------------------
def read_health(path: str) -> dict:
    """One health.json snapshot. A partially written file is a transient, not a session fault."""
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _framework_view(health: dict) -> dict:
    """FEED's execution view merged over PROCESSOR's planning view, both optional (flag-off = {})."""
    view = dict(health.get("framework") or {})
    view.update(health.get("framework_feed") or {})
    return view


def sample(health: dict, *, at: float) -> dict:
    """Flatten one health snapshot into the fields the F10 evidence needs, and nothing else."""
    fw = _framework_view(health)
    return {
        "at": round(at, 3),
        "state": health.get("state"),
        "websocket_status": health.get("websocket_status"),
        "raw_file_queue_size": health.get("raw_file_queue_size", 0),
        "proc_queue_size": health.get("proc_queue_size", 0),
        "db_queue_size": health.get("db_queue_size", 0),
        "raw_dropped_total": health.get("raw_dropped_total", 0) or 0,
        "proc_dropped_total": health.get("proc_dropped_total", 0) or 0,
        "db_rows_dropped_total": health.get("db_rows_dropped_total", 0) or 0,
        "degraded_level": health.get("degraded_level", 0) or 0,
        "cycle_ms_p50": health.get("cycle_ms_p50", 0.0) or 0.0,
        "cycle_ms_max": health.get("cycle_ms_max", 0.0) or 0.0,
        "rss_mb": health.get("rss_mb", 0.0) or 0.0,
        "active_contracts": health.get("active_contracts", 0) or 0,
        "actual_depth": dict(health.get("actual_depth") or {}),
        "restart_count": health.get("restart_count", 0) or 0,
        "premium_legs": fw.get("premium_legs"),
        "effective_budget": fw.get("effective_budget"),
        "delivering_legs": fw.get("delivering_legs"),
        "desired_legs": fw.get("desired_legs"),
        "plans_executed": fw.get("plans_executed"),
        "plan_failures": fw.get("plan_failures"),
        "framework_present": bool(fw),
    }


# --------------------------------------------------------------------------------------------------
# Classification
# --------------------------------------------------------------------------------------------------
def classify(current: dict, previous: dict | None, thresholds: dict) -> list[dict]:
    """Conditions raised by one sample, each as ``{code, level, detail}``.

    ``level`` here is the condition's *nature*, not yet the verdict: a non-instant HARD-natured
    condition only becomes an abort once it has held for ``--sustain`` consecutive samples, which is
    :func:`Watch.observe`'s job. Keeping the two apart is what stops a single slow cycle from
    aborting a session the P10-E notes already tell us tolerates slow cycles.
    """
    out: list[dict] = []

    def raise_(code: str, level: str, detail: str) -> None:
        out.append({"code": code, "level": level, "detail": detail})

    # --- the lossless-raw invariant: instant, and the only drop counter that is an abort ----------
    if current["raw_dropped_total"] > 0:
        raise_("raw_loss", HARD, f"raw_dropped_total={current['raw_dropped_total']} (lossless raw violated)")

    # --- framework invariant: premium occupancy above the budget it was given ---------------------
    budget, premium = current.get("effective_budget"), current.get("premium_legs")
    if budget is not None and premium is not None and premium > budget:
        raise_("budget_exceeded", HARD, f"premium_legs={premium} > effective_budget={budget}")

    # --- queues: warn at the configured warn watermark, hard at the critical one ------------------
    for key, warn_k, crit_k in (
        ("proc_queue_size", "proc_warn", "proc_crit"),
        ("db_queue_size", "db_warn", "db_crit"),
        ("raw_file_queue_size", "raw_warn", "raw_crit"),
    ):
        size = current[key]
        if size >= thresholds[crit_k]:
            raise_(f"{key}_critical", HARD, f"{key}={size} >= {thresholds[crit_k]:.0f}")
        elif size >= thresholds[warn_k]:
            raise_(f"{key}_warn", SOFT, f"{key}={size} >= {thresholds[warn_k]:.0f}")

    # --- PROCESSOR cadence ------------------------------------------------------------------------
    p50 = current["cycle_ms_p50"]
    if p50 >= thresholds["cycle_ms_hard"]:
        raise_("cycle_ms_hard", HARD, f"cycle_ms_p50={p50:.1f} >= {thresholds['cycle_ms_hard']:.0f} ms")
    elif p50 >= thresholds["cycle_ms_soft"]:
        raise_("cycle_ms_soft", SOFT, f"cycle_ms_p50={p50:.1f} >= {thresholds['cycle_ms_soft']:.0f} ms")

    # --- memory ------------------------------------------------------------------------------------
    rss = current["rss_mb"]
    if rss >= thresholds["rss_mb_hard"]:
        raise_("rss_hard", HARD, f"rss_mb={rss:.0f} >= {thresholds['rss_mb_hard']:.0f}")
    elif rss >= thresholds["rss_mb_soft"]:
        raise_("rss_soft", SOFT, f"rss_mb={rss:.0f} >= {thresholds['rss_mb_soft']:.0f}")

    # --- degraded mode ------------------------------------------------------------------------------
    level = current["degraded_level"]
    if level >= 2:
        raise_("degraded_critical", HARD, f"degraded_level={level}")
    elif level >= 1:
        raise_("degraded_warn", SOFT, f"degraded_level={level}")

    if previous is None:
        return out

    # --- deltas: a storm is growth, not a number ----------------------------------------------------
    fails_now, fails_before = current.get("plan_failures"), previous.get("plan_failures")
    if fails_now is not None and fails_before is not None and fails_now > fails_before:
        raise_("plan_failures_growing", HARD,
               f"plan_failures {fails_before} -> {fails_now} between samples")

    db_delta = current["db_rows_dropped_total"] - previous["db_rows_dropped_total"]
    if db_delta > 0:
        raise_("db_drops_growing", HARD, f"db_rows_dropped_total +{db_delta} between samples")

    proc_delta = current["proc_dropped_total"] - previous["proc_dropped_total"]
    if proc_delta > 0:
        raise_("proc_drops_growing", SOFT, f"proc_dropped_total +{proc_delta} between samples")

    if current["restart_count"] > previous["restart_count"]:
        raise_("restart", SOFT, f"restart_count {previous['restart_count']} -> {current['restart_count']}")

    if previous.get("framework_present") and not current.get("framework_present"):
        raise_("framework_vanished", HARD, "framework block disappeared from health.json while enabled")

    if previous.get("websocket_status") == "connected" and current.get("websocket_status") != "connected":
        raise_("ws_not_connected", SOFT, f"websocket_status={current.get('websocket_status')}")

    return out


class Watch:
    """Turns a stream of per-sample conditions into abort verdicts by applying the sustain rule."""

    __slots__ = ("sustain", "_streaks", "previous", "samples", "events")

    def __init__(self, *, sustain: int = DEFAULT_SUSTAIN) -> None:
        if sustain < 1:
            raise ValueError("sustain must be >= 1")
        self.sustain = sustain
        self._streaks: dict[str, int] = {}
        self.previous: dict | None = None
        self.samples: list[dict] = []
        self.events: list[dict] = []

    def observe(self, current: dict, thresholds: dict) -> list[dict]:
        """Record one sample; return the conditions that are aborts *as of this sample*."""
        conditions = classify(current, self.previous, thresholds)
        raised = {c["code"] for c in conditions}
        for code in list(self._streaks):
            if code not in raised:
                del self._streaks[code]

        aborts: list[dict] = []
        for condition in conditions:
            code = condition["code"]
            self._streaks[code] = self._streaks.get(code, 0) + 1
            condition = dict(condition, at=current["at"], streak=self._streaks[code])
            self.events.append(condition)
            if condition["level"] != HARD:
                continue
            needed = 1 if code in INSTANT else self.sustain
            if self._streaks[code] >= needed:
                aborts.append(condition)

        self.previous = current
        self.samples.append(current)
        return aborts


# --------------------------------------------------------------------------------------------------
# Evidence rendering (fork F26)
# --------------------------------------------------------------------------------------------------
def _span(samples: list[dict], key: str) -> tuple[float, float]:
    values = [s.get(key) or 0 for s in samples]
    return (min(values), max(values)) if values else (0, 0)


def render_evidence(samples: list[dict], events: list[dict], *, meta: dict) -> str:
    """The F26 evidence skeleton: OBSERVED filled from the timeline, INFERRED and UNKNOWN left standing.

    Deliberately a skeleton. Every OBSERVED number here came out of the recorder's own health file;
    the conclusion, the P10-E comparison, and the D18 verdict are written by a person who watched the
    session, because those are judgements and this tool has none.
    """
    if not samples:
        return "# F10 live validation -- no samples\n\nThe timeline is empty; nothing is claimed.\n"

    cyc_lo, cyc_hi = _span(samples, "cycle_ms_p50")
    _, cyc_max = _span(samples, "cycle_ms_max")
    rss_lo, rss_hi = _span(samples, "rss_mb")
    _, proc_hi = _span(samples, "proc_queue_size")
    _, db_hi = _span(samples, "db_queue_size")
    _, raw_hi = _span(samples, "raw_file_queue_size")
    _, prem_hi = _span(samples, "premium_legs")
    budgets = {s.get("effective_budget") for s in samples if s.get("effective_budget") is not None}
    depths = {json.dumps(s.get("actual_depth"), sort_keys=True) for s in samples if s.get("actual_depth")}
    last = samples[-1]
    hard = [e for e in events if e["level"] == HARD]
    soft = [e for e in events if e["level"] == SOFT]

    def _soft_table() -> str:
        if not soft:
            return "None observed.\n"
        counts: dict[str, int] = {}
        first: dict[str, float] = {}
        for e in soft:
            counts[e["code"]] = counts.get(e["code"], 0) + 1
            first.setdefault(e["code"], e["at"])
        rows = "\n".join(f"| `{code}` | {n} | {first[code]} |" for code, n in sorted(counts.items()))
        return f"| Condition | Samples | First at |\n|---|---|---|\n{rows}\n"

    return f"""# F10 live validation -- evidence

- Trading date: {meta.get('session_date', 'FILL IN')}
- Samples: {len(samples)} at {meta.get('interval', 'FILL IN')} s cadence
- Window: {meta.get('started', 'FILL IN')} .. {meta.get('ended', 'FILL IN')}
- Recorder `config_hash`: {meta.get('config_hash', 'FILL IN')}
- Health file: `{meta.get('health_path', 'FILL IN')}`
- Timeline: `{meta.get('timeline_path', 'FILL IN')}`

## OBSERVED

Every number below was read from the recorder's own `health.json` during the session.

| Measure | Observed |
|---|---|
| `cycle_ms_p50` | {cyc_lo:.1f} .. {cyc_hi:.1f} ms |
| `cycle_ms_max` | up to {cyc_max:.1f} ms |
| `rss_mb` | {rss_lo:.0f} .. {rss_hi:.0f} MB |
| `proc_queue_size` peak | {proc_hi} |
| `db_queue_size` peak | {db_hi} |
| `raw_file_queue_size` peak | {raw_hi} |
| `raw_dropped_total` final | {last['raw_dropped_total']} |
| `db_rows_dropped_total` final | {last['db_rows_dropped_total']} |
| `proc_dropped_total` final | {last['proc_dropped_total']} |
| `degraded_level` peak | {max(s['degraded_level'] for s in samples)} |
| Premium legs peak | {prem_hi} |
| Effective budget seen | {sorted(budgets) or 'framework absent from health'} |
| Delivering legs (final) | {last.get('delivering_legs')} |
| Desired legs (final) | {last.get('desired_legs')} |
| Plans executed (final) | {last.get('plans_executed')} |
| Plan failures (final) | {last.get('plan_failures')} |
| `actual_depth` seen | {sorted(depths) or 'n/a'} |
| Restarts during watch | {last['restart_count'] - samples[0]['restart_count']} |

### Abort conditions fired

{"None." if not hard else chr(10).join(f"- `{e['code']}` at {e['at']} (streak {e['streak']}): {e['detail']}" for e in hard)}

### Soft conditions recorded

{_soft_table()}

## INFERRED

FILL IN. State each inference and the observation it rests on. An inference is not an observation
and must not be written into the OBSERVED table.

## UNKNOWN

- **Reconnect depth restoration.** UNKNOWN unless a reconnect occurred naturally during this session
  *and* premium legs were seen delivering at depth afterwards. No reconnect was forced. The absence
  of a reconnect establishes nothing.
- **The broker's true premium ceiling.** This session ran at the configured effective budget. Legs
  operating successfully at that budget does not establish that the broker would accept more, and no
  attempt was made to find out. UNKNOWN.

## Comparison against P10-E

FILL IN. P10-E baseline: `cycle_ms_p50` ~22 ms (max 43-60 ms), RSS 52-58 MB, measured at <=5 NFO @50
plus ~120 SENSEX @5.

## D18 conclusion

FILL IN. D18 closes only if this session ran the true-scale hybrid and the envelope above is
acceptable. If it did not, say so and leave D18 open.
"""


# --------------------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------------------
def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="python -m market_depth_recorder.tools.validation.f10_live_monitor",
        description="Read-only F10 live-session watcher and evidence renderer.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("health", nargs="?", help="path to the live health.json")
    p.add_argument("-c", "--config", help="config.yaml the thresholds are derived from")
    p.add_argument("-o", "--out", help="JSONL timeline to append to")
    p.add_argument("--interval", type=float, default=DEFAULT_INTERVAL)
    p.add_argument("--sustain", type=int, default=DEFAULT_SUSTAIN)
    p.add_argument("--max-samples", type=int, default=0, help="stop after N samples (0 = until interrupted)")
    p.add_argument("--once", action="store_true", help="one sample, classify, exit")
    p.add_argument("--render", metavar="TIMELINE", help="render an evidence skeleton from a timeline")
    p.add_argument("--evidence-out", help="where --render writes (default: stdout)")
    return p.parse_args(argv)


def _load_timeline(path: str) -> tuple[list[dict], list[dict], dict]:
    samples, events, meta = [], [], {}
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            kind = obj.get("record")
            if kind == "event":
                events.append(obj)
            elif kind == "meta":
                meta.update(obj)
            else:
                samples.append(obj)
    return samples, events, meta


def _emit(fh, record: dict) -> None:
    fh.write(json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
    fh.flush()


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    if args.render:
        if not os.path.exists(args.render):
            print(f"timeline not found: {args.render}", file=sys.stderr)
            return 2
        samples, events, meta = _load_timeline(args.render)
        meta.setdefault("timeline_path", args.render)
        text = render_evidence(samples, events, meta=meta)
        if args.evidence_out:
            with open(args.evidence_out, "w", encoding="utf-8") as fh:
                fh.write(text)
            print(f"evidence skeleton written: {args.evidence_out}")
        else:
            print(text)
        return 0

    if not args.health:
        print("a health.json path is required unless --render is used", file=sys.stderr)
        return 2
    if not os.path.exists(args.health):
        print(f"health file not found: {args.health}", file=sys.stderr)
        return 2
    if not args.config:
        print("--config is required: the thresholds are derived from it, never assumed", file=sys.stderr)
        return 2
    try:
        thresholds = thresholds_from(args.config)
    except (OSError, ValueError) as exc:
        print(f"could not derive thresholds: {exc}", file=sys.stderr)
        return 2

    out_path = args.out or os.path.join(os.path.dirname(os.path.abspath(args.health)),
                                        "f10_timeline.jsonl")
    watch = Watch(sustain=args.sustain)
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    aborted = False

    with open(out_path, "a", encoding="utf-8") as fh:
        _emit(fh, {"record": "meta", "started": started, "interval": args.interval,
                   "sustain": args.sustain, "health_path": os.path.abspath(args.health),
                   "timeline_path": os.path.abspath(out_path), "thresholds": thresholds})
        taken = 0
        try:
            while True:
                try:
                    health = read_health(args.health)
                except (OSError, ValueError) as exc:
                    print(f"[{taken}] health unreadable this tick ({exc}) -- not a session fault, retrying")
                    if args.once:
                        return 2
                    time.sleep(args.interval)
                    continue

                current = sample(health, at=time.time())
                current["record"] = "sample"
                current["config_hash"] = health.get("config_hash")
                aborts = watch.observe(current, thresholds)
                _emit(fh, current)
                for event in watch.events[-8:]:
                    if event.get("at") == current["at"]:
                        _emit(fh, dict(event, record="event"))

                flag = "ABORT" if aborts else ("warn" if any(
                    e["level"] == SOFT and e["at"] == current["at"] for e in watch.events) else "ok")
                print(f"[{taken:4d}] {flag:5s} state={current['state']} "
                      f"cycle_p50={current['cycle_ms_p50']:.1f} rss={current['rss_mb']:.0f} "
                      f"q={current['proc_queue_size']}/{current['db_queue_size']}/"
                      f"{current['raw_file_queue_size']} "
                      f"premium={current.get('premium_legs')}/{current.get('effective_budget')} "
                      f"drops={current['raw_dropped_total']}")
                for condition in aborts:
                    print(f"       ABORT: {condition['code']} -- {condition['detail']}", file=sys.stderr)

                if aborts:
                    aborted = True
                    print("       operator action required: see Documents/F10_LIVE_VALIDATION.md D",
                          file=sys.stderr)
                    break

                taken += 1
                if args.once or (args.max_samples and taken >= args.max_samples):
                    break
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nwatch stopped by operator")
        finally:
            _emit(fh, {"record": "meta", "ended": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                       "samples": len(watch.samples), "aborted": aborted})

    print(f"timeline: {out_path} ({len(watch.samples)} samples)")
    return 1 if aborted else 0


if __name__ == "__main__":
    raise SystemExit(main())
