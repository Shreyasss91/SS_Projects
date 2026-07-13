"""Arrow-backend validation on the ~100-minute representative dataset (2026-07-07 raw log).

Rebuilds the full ~100-min raw log with the arrow write backend and reports:
total wall, replay(loop) vs finalize() split, peak RSS, output DB size, per-table row counts,
and --verify vs the existing executemany analytics store (data/2026-07-07/…analytics…duckdb).
The replay loop mirrors replay.replay_file exactly, so a clean --verify also proves faithfulness.
"""
from __future__ import annotations

import gzip, json, math, os, queue, threading, time

import duckdb
import psutil

from market_depth_recorder.config import load_config
from market_depth_recorder.replay import _load_header, _date_from_header_or_name, _drain, verify
from market_depth_recorder.instrument_manager import InstrumentManager
from market_depth_recorder.processor import TickProcessor
from market_depth_recorder.database_writer import DuckDBAnalyticalWriter, _TABLE_COLUMNS

SCRATCH = os.path.dirname(os.path.abspath(__file__))
CONFIG = "market_depth_recorder/config.yaml"
RAW = "market_depth_recorder/data/2026-07-07/market_depth_raw_20260707.jsonl.gz"
REFERENCE = "market_depth_recorder/data/2026-07-07/market_depth_analytics_20260707.duckdb"
OUT = os.path.join(SCRATCH, "bench", "fullrun_arrow.duckdb")


class PeakRSS(threading.Thread):
    def __init__(self, proc, interval=0.2):
        super().__init__(daemon=True)
        self._proc, self._interval, self._stop = proc, interval, threading.Event()
        self.peak = 0

    def run(self):
        while not self._stop.is_set():
            try:
                self.peak = max(self.peak, self._proc.memory_info().rss)
            except Exception:
                pass
            self._stop.wait(self._interval)

    def stop(self):
        self._stop.set()


def main():
    cfg = load_config(CONFIG)
    interval = float(cfg.recorder["resample_interval_sec"])
    proc = psutil.Process(os.getpid())
    sampler = PeakRSS(proc)
    packets = 0
    t_finalize = 0.0
    sampler.start()
    t0 = time.perf_counter()
    with gzip.open(RAW, "rt", encoding="utf-8") as fh:
        header = _load_header(fh)
        im = InstrumentManager.from_header(cfg, (header or {}).get("instruments"))
        vclock = {"t": 0.0}
        db_q: queue.Queue = queue.Queue()
        tp = TickProcessor(cfg, im, queue.Queue(), db_q, threading.Event(),
                           time_fn=lambda: vclock["t"], active_metrics="all")
        sd = _date_from_header_or_name(header, RAW)
        w = DuckDBAnalyticalWriter(cfg, OUT, session_date=sd, source_raw=os.path.basename(RAW),
                                   write_backend="arrow")
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
            import sys
            w.__exit__(*sys.exc_info())
            raise
    wall = time.perf_counter() - t0
    sampler.stop(); sampler.join(timeout=2.0)

    db_size_mb = os.path.getsize(OUT) / (1024 * 1024)
    con = duckdb.connect(OUT, read_only=True)
    try:
        counts = {t: con.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in _TABLE_COLUMNS}
    finally:
        con.close()

    ok, report = verify(cfg, OUT, REFERENCE, live_subset=False)

    print("\n================ Arrow full-run (~100-min dataset) ================")
    print(f"packets            = {packets}")
    print(f"rows written       = {w.rows_written}")
    print(f"total wall         = {wall:.1f}s")
    print(f"  replay (loop)    = {wall - t_finalize:.1f}s")
    print(f"  finalize()       = {t_finalize:.1f}s")
    print(f"peak RSS           = {sampler.peak/(1024*1024):.1f} MB")
    print(f"output DB size     = {db_size_mb:.1f} MB   (reference {os.path.getsize(REFERENCE)/(1024*1024):.1f} MB)")
    print(f"row counts         = {counts}")
    print(f"--verify vs store  = {'OK (no drift)' if ok else 'DRIFT'}")
    for line in report:
        print(f"    {line}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
