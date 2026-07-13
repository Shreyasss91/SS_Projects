#!/usr/bin/env python3
"""Benchmark the analytics writer's peak RSS + throughput at a given streaming batch size.

Rebuilds a raw ``.jsonl.gz`` log through the full metric catalogue with the
``DuckDBAnalyticalWriter``, flushing in fixed-size batches (``write_batch_rows``), and
reports wall time (split into replay vs finalize), **peak RSS**, batches written, rows,
and output DB size.

Run **one batch size per process** — Python does not return freed heap to the OS between
runs, so a second run in the same process would report a polluted peak. To sweep batch
sizes, invoke the tool once per size (e.g. in a shell loop) and compare the JSON ledger.

Inputs
  RAW           path to the raw market-depth .jsonl.gz to replay
  BATCH_ROWS    streaming flush size for this run (writer ``write_batch_rows``)
  --config      config.yaml (default: the packaged market_depth_recorder/config.yaml)
  --backend     write backend: arrow (default) | executemany
  --out         output .duckdb path (default: a temp file; removed after measuring)
  --ledger      optional JSONL file to append the result record to

Output
  A one-line human summary to stdout, and (if --ledger) one JSON record per run.

Exit codes
  0  benchmark completed
  2  usage / runtime error (missing psutil, bad path, ...)

----------------------------------------------------------------------------------------
Purpose
  Measure whether a writer/backend/batch-size choice keeps peak RSS bounded (the 8 GB
  target constraint) while preserving throughput — the gate used to pick the default
  write_batch_rows.

Typical workflow
  1. Pick a representative raw log.
  2. Run once per candidate batch size (separate processes) appending to one --ledger.
  3. Compare peak_rss_mb vs wall_s across sizes; smaller batches bound RSS at some
     insert-overhead cost.

Example command line
  for b in 50000 100000 250000; do \
    python market_depth_recorder/tools/performance/bench_chunk.py \
        data/2026-07-07/market_depth_raw_20260707.jsonl.gz $b \
        --ledger /tmp/chunk_results.jsonl ; \
  done

Related documentation
  Documents/PERFORMANCE.md  (§8 chunked-Arrow redesign; §9 the batch-size benchmark table)
  Documents/archive/offline-replay-optimization-engineering-journal.md
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
import os
import pathlib
import queue
import sys
import threading
import time

# Allow running as a plain script: SS_Projects root is …/tools/performance → up 3.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

_PACKAGED_CONFIG = pathlib.Path(__file__).resolve().parents[1] / "config.yaml"


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
            except Exception:
                pass
            self._stop.wait(self._interval)

    def stop(self) -> None:
        self._stop.set()


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="bench_chunk.py",
        description="Measure writer peak RSS + throughput at a given streaming batch size.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog="Run ONE batch size per process for a clean peak RSS. Exit: 0 ok, 2 error.",
    )
    p.add_argument("raw", metavar="RAW", help="raw market-depth .jsonl.gz to replay")
    p.add_argument("batch_rows", metavar="BATCH_ROWS", type=int, help="streaming flush size")
    p.add_argument("--config", default=str(_PACKAGED_CONFIG), help="path to config.yaml")
    p.add_argument("--backend", choices=("arrow", "executemany"), default="arrow",
                   help="write backend to benchmark")
    p.add_argument("--out", default=None, help="output .duckdb (default: temp file, removed after)")
    p.add_argument("--ledger", default=None, help="optional JSONL file to append the result to")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.batch_rows < 1:
        print("error: BATCH_ROWS must be a positive integer", file=sys.stderr)
        return 2
    if not os.path.isfile(args.raw):
        print(f"error: RAW not found: {args.raw}", file=sys.stderr)
        return 2
    if not os.path.isfile(args.config):
        print(f"error: config not found: {args.config}", file=sys.stderr)
        return 2

    try:
        import psutil
    except ImportError:
        print("error: psutil is required for RSS measurement (uv add --group dev psutil)", file=sys.stderr)
        return 2

    from market_depth_recorder.config import load_config
    from market_depth_recorder.database_writer import DuckDBAnalyticalWriter
    from market_depth_recorder.instrument_manager import InstrumentManager
    from market_depth_recorder.processor import TickProcessor
    from market_depth_recorder.replay import _date_from_header_or_name, _drain, _load_header

    out = args.out or os.path.join(
        os.environ.get("TEMP", "/tmp"), f"bench_chunk_{os.getpid()}.duckdb"
    )
    remove_out = args.out is None

    cfg = load_config(args.config)
    interval = float(cfg.recorder["resample_interval_sec"])
    proc = psutil.Process(os.getpid())
    sampler = PeakRSS(proc)
    packets = 0
    t_finalize = 0.0
    sampler.start()
    t0 = time.perf_counter()
    try:
        with gzip.open(args.raw, "rt", encoding="utf-8") as fh:
            header = _load_header(fh)
            im = InstrumentManager.from_header(cfg, (header or {}).get("instruments"))
            vclock = {"t": 0.0}
            db_q: queue.Queue = queue.Queue()
            tp = TickProcessor(cfg, im, queue.Queue(), db_q, threading.Event(),
                               time_fn=lambda: vclock["t"], active_metrics="all")
            sd = _date_from_header_or_name(header, args.raw)
            w = DuckDBAnalyticalWriter(cfg, out, session_date=sd,
                                       source_raw=os.path.basename(args.raw),
                                       write_backend=args.backend)
            # Bench seam: override the streaming flush size for this run without editing
            # config (analytics_db is read-only at runtime).
            w._batch_rows = args.batch_rows
            w.__enter__()
            try:
                next_b = None
                for raw in fh:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        obj = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    if obj.get("meta_type") in ("HEADER", "EOF"):
                        continue
                    recv = obj.get("recv_ts")
                    if recv is None:
                        continue
                    vclock["t"] = recv
                    tp.ingest(obj)
                    packets += 1
                    if next_b is None:
                        next_b = (math.floor(recv / interval) + 1) * interval
                    while recv >= next_b:
                        tp.emit_second(int(next_b))
                        _drain(db_q, w)
                        next_b += interval
                _drain(db_q, w)
                t_bf = time.perf_counter()
                w.__exit__(None, None, None)
                t_finalize = time.perf_counter() - t_bf
            except BaseException:
                w.__exit__(*sys.exc_info())
                raise
    except Exception as exc:
        sampler.stop()
        print(f"error: benchmark run failed: {exc}", file=sys.stderr)
        return 2

    wall = time.perf_counter() - t0
    sampler.stop()
    sampler.join(timeout=2.0)
    peak_mb = sampler.peak / (1024 * 1024)
    db_mb = os.path.getsize(out) / (1024 * 1024) if os.path.exists(out) else 0.0

    rec = {
        "raw": os.path.basename(args.raw), "backend": args.backend,
        "batch_rows": args.batch_rows, "packets": packets, "rows": w.rows_written,
        "batches": w.batches_written, "wall_s": round(wall, 1),
        "replay_s": round(wall - t_finalize, 1), "finalize_s": round(t_finalize, 1),
        "peak_rss_mb": round(peak_mb, 1), "db_mb": round(db_mb, 1),
    }
    if args.ledger:
        os.makedirs(os.path.dirname(os.path.abspath(args.ledger)), exist_ok=True)
        with open(args.ledger, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + "\n")
    print(f"backend={rec['backend']:<11} batch={rec['batch_rows']:>8}  wall={rec['wall_s']:>6}s  "
          f"(replay {rec['replay_s']}s / finalize {rec['finalize_s']}s)  "
          f"peakRSS={rec['peak_rss_mb']:>7} MB  batches={rec['batches']:>4}  rows={rec['rows']}")

    if remove_out and os.path.exists(out):
        os.remove(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
