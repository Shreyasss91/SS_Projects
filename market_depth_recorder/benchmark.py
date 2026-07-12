"""Replay benchmark harness (dev/measurement tool — NOT part of the runtime pipeline).

Runs an offline replay of a raw ``.jsonl.gz`` through :func:`market_depth_recorder.replay.replay_file`
(the exact production compute path — no metric code is duplicated or bypassed) and records a structured
performance sample so each optimization phase can be measured in isolation:

- **wall_sec** — wall-clock elapsed for the replay call.
- **cpu_sec** / **cpu_util_pct** — process (+ child) CPU seconds and utilization vs a single core.
- **peak_rss_mb** — peak resident memory sampled over the run (process + any children).
- **packets_per_sec** / **rows_per_sec** — throughput derived from the replay's own row/packet counts.

The harness is deliberately **read-only w.r.t. the pipeline**: it imports and times the public
``replay_file`` entry point and never touches metric logic. Child-process CPU/RSS aggregation is included
now so the same harness measures the Phase-2 multi-process replay unchanged.

``psutil`` is used when present (cross-platform CPU/RSS incl. children); if it is unavailable the harness
degrades to :func:`time.process_time` for CPU and reports ``peak_rss_mb=None`` rather than failing — so a
run is never blocked by a missing measurement dependency.

Usage (from the parent ``SS_Projects/``)::

    python -m market_depth_recorder.benchmark \
        --config market_depth_recorder/config.yaml \
        --raw market_depth_recorder/data/2026-07-07/market_depth_raw_20260707.jsonl.gz \
        --label baseline [--from 12:16 --to 12:26] [--json-out bench/results.jsonl]

A one-line human summary goes to stdout; with ``--json-out`` the full sample is appended as one JSON
object per line (a growing ledger across phases).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
from dataclasses import asdict, dataclass

from .config import load_config
from .utils import parse_ist_hhmm

try:  # optional — the harness must run even without it
    import psutil
except Exception:  # noqa: BLE001 — any import failure degrades gracefully
    psutil = None  # type: ignore[assignment]


@dataclass
class BenchSample:
    """One benchmark run's structured result (serialized to the JSON ledger)."""

    label: str
    raw: str
    output: str
    from_time: str | None
    to_time: str | None
    packets: int
    rows: int
    seconds: int
    corrupt_lines: int
    wall_sec: float
    cpu_sec: float | None
    cpu_util_pct: float | None       # CPU seconds / wall × 100 (100 % = one core fully busy)
    peak_rss_mb: float | None
    packets_per_sec: float
    rows_per_sec: float
    psutil_used: bool
    workers: int                     # 1 for single-process replay; set by the caller for Phase 2
    timestamp: float


class _ResourceSampler(threading.Thread):
    """Background sampler that tracks **peak** RSS (process + children) while the replay runs.

    A daemon thread polling every ``interval`` seconds. FD-safe: owns no files/sockets; the ``psutil``
    handle is a lightweight process wrapper. Stopped via an :class:`threading.Event` and joined by the
    caller, so it never outlives the measured run.
    """

    def __init__(self, proc, interval: float = 0.25):
        super().__init__(name="bench-sampler", daemon=True)
        self._proc = proc
        self._interval = interval
        self._stop = threading.Event()
        self.peak_rss = 0

    def _sample_rss(self) -> int:
        total = 0
        try:
            total += self._proc.memory_info().rss
            for child in self._proc.children(recursive=True):
                try:
                    total += child.memory_info().rss
                except Exception:  # noqa: BLE001 — a child may exit mid-sample
                    pass
        except Exception:  # noqa: BLE001 — process may be gone
            pass
        return total

    def run(self) -> None:
        while not self._stop.is_set():
            self.peak_rss = max(self.peak_rss, self._sample_rss())
            self._stop.wait(self._interval)
        # one final sample to catch a late peak
        self.peak_rss = max(self.peak_rss, self._sample_rss())

    def stop(self) -> None:
        self._stop.set()


def _cpu_seconds(proc) -> float | None:
    """Total CPU seconds (user+system) for the process + all children, or None if psutil is absent."""
    if proc is None:
        return None
    try:
        t = proc.cpu_times()
        total = t.user + t.system
        # include finished + running children where the platform exposes them
        ch = getattr(t, "children_user", 0.0) + getattr(t, "children_system", 0.0)
        total += ch
        for child in proc.children(recursive=True):
            try:
                ct = child.cpu_times()
                total += ct.user + ct.system
            except Exception:  # noqa: BLE001
                pass
        return float(total)
    except Exception:  # noqa: BLE001
        return None


def run_benchmark(
    config_path: str,
    raw_path: str,
    output_path: str,
    *,
    label: str = "run",
    from_time: str | None = None,
    to_time: str | None = None,
    workers: int = 1,
    sampler_interval: float = 0.25,
) -> BenchSample:
    """Replay ``raw_path`` once under measurement and return a :class:`BenchSample`.

    Times only the ``replay_file`` call (config load excluded). CPU/RSS come from psutil when available,
    aggregated over the process tree so the same call measures Phase-2 worker processes too.
    """
    from .replay import replay_file  # local import: keeps the pipeline import graph unchanged

    cfg = load_config(config_path)
    from_t = parse_ist_hhmm(from_time) if from_time else None
    to_t = parse_ist_hhmm(to_time) if to_time else None

    proc = psutil.Process(os.getpid()) if psutil is not None else None
    sampler = _ResourceSampler(proc, sampler_interval) if proc is not None else None

    cpu_before = _cpu_seconds(proc)
    pt_before = time.process_time()
    if sampler is not None:
        sampler.start()
    t0 = time.perf_counter()
    stats = replay_file(cfg, raw_path, output_path, from_t=from_t, to_t=to_t)
    wall = time.perf_counter() - t0
    if sampler is not None:
        sampler.stop()
        sampler.join(timeout=2.0)
    cpu_after = _cpu_seconds(proc)
    pt_after = time.process_time()

    if cpu_before is not None and cpu_after is not None:
        cpu_sec: float | None = cpu_after - cpu_before
    else:  # psutil unavailable → single-process CPU time only (no children)
        cpu_sec = pt_after - pt_before
    cpu_util = (cpu_sec / wall * 100.0) if (cpu_sec is not None and wall > 0) else None
    peak_rss_mb = (sampler.peak_rss / (1024 * 1024)) if sampler is not None and sampler.peak_rss else None

    sample = BenchSample(
        label=label, raw=raw_path, output=output_path, from_time=from_time, to_time=to_time,
        packets=stats.packets, rows=stats.rows, seconds=stats.seconds, corrupt_lines=stats.corrupt_lines,
        wall_sec=round(wall, 3),
        cpu_sec=round(cpu_sec, 3) if cpu_sec is not None else None,
        cpu_util_pct=round(cpu_util, 1) if cpu_util is not None else None,
        peak_rss_mb=round(peak_rss_mb, 1) if peak_rss_mb is not None else None,
        packets_per_sec=round(stats.packets / wall, 1) if wall > 0 else 0.0,
        rows_per_sec=round(stats.rows / wall, 1) if wall > 0 else 0.0,
        psutil_used=psutil is not None, workers=workers, timestamp=time.time(),
    )
    return sample


def _format(sample: BenchSample) -> str:
    slice_s = ""
    if sample.from_time or sample.to_time:
        slice_s = f" slice={sample.from_time or '..'}–{sample.to_time or '..'}"
    return (
        f"BENCH [{sample.label}]{slice_s}\n"
        f"  wall={sample.wall_sec:.1f}s  cpu={sample.cpu_sec}s  cpu_util={sample.cpu_util_pct}%  "
        f"peak_rss={sample.peak_rss_mb} MB  workers={sample.workers}\n"
        f"  packets={sample.packets} ({sample.packets_per_sec}/s)  "
        f"rows={sample.rows} ({sample.rows_per_sec}/s)  seconds={sample.seconds}  "
        f"corrupt={sample.corrupt_lines}"
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="python -m market_depth_recorder.benchmark",
        description="Measure offline replay performance (wall/CPU/RAM/throughput).",
    )
    p.add_argument("--config", default="config.yaml")
    p.add_argument("--raw", required=True, help="Raw .jsonl.gz to replay.")
    p.add_argument("--output", default=None, help="DuckDB output path (default: a temp side file).")
    p.add_argument("--label", default="run", help="Label recorded with the sample.")
    p.add_argument("--from", dest="from_time", default=None, metavar="HH:MM")
    p.add_argument("--to", dest="to_time", default=None, metavar="HH:MM")
    p.add_argument("--json-out", default=None, help="Append the JSON sample as one line to this ledger.")
    p.add_argument("--workers", type=int, default=1, help="Recorded with the sample (Phase 2).")
    args = p.parse_args(argv)

    output = args.output or (args.raw.rsplit(".jsonl.gz", 1)[0] + f".bench_{args.label}.duckdb")
    sample = run_benchmark(
        args.config, args.raw, output, label=args.label,
        from_time=args.from_time, to_time=args.to_time, workers=args.workers,
    )
    print(_format(sample))
    if args.json_out:
        os.makedirs(os.path.dirname(os.path.abspath(args.json_out)), exist_ok=True)
        with open(args.json_out, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(sample)) + "\n")
        print(f"  → appended to {args.json_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())