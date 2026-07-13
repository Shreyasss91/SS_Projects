"""A/B validation: executemany vs arrow finalize backend, full metric set on the fixed slice.

For each backend: total wall, finalize() time, rows, peak RSS, and --verify drift vs the reference.
The replay loop mirrors replay.replay_file exactly (same processor/writer/emit), so a clean --verify
also proves this harness is a faithful proxy for the production path.
"""
from __future__ import annotations

import gzip, json, math, os, queue, threading, time

import psutil

from market_depth_recorder.config import load_config
from market_depth_recorder.replay import _load_header, _date_from_header_or_name, _drain, verify
from market_depth_recorder.instrument_manager import InstrumentManager
from market_depth_recorder.processor import TickProcessor
from market_depth_recorder.database_writer import DuckDBAnalyticalWriter

SCRATCH = os.path.dirname(os.path.abspath(__file__))
CONFIG = "market_depth_recorder/config.yaml"
SLICE = os.path.join(SCRATCH, "slice", "market_depth_raw_20260707.jsonl.gz")
REFERENCE = os.path.join(SCRATCH, "bench", "slice_reference.duckdb")


class PeakRSS(threading.Thread):
    def __init__(self, proc, interval=0.1):
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


def run_backend(cfg, backend: str) -> dict:
    out = os.path.join(SCRATCH, "bench", f"slice_backend_{backend}.duckdb")
    interval = float(cfg.recorder["resample_interval_sec"])
    proc = psutil.Process(os.getpid())
    sampler = PeakRSS(proc)
    t_finalize = 0.0
    sampler.start()
    t0 = time.perf_counter()
    with gzip.open(SLICE, "rt", encoding="utf-8") as fh:
        header = _load_header(fh)
        im = InstrumentManager.from_header(cfg, (header or {}).get("instruments"))
        vclock = {"t": 0.0}
        db_q: queue.Queue = queue.Queue()
        tp = TickProcessor(cfg, im, queue.Queue(), db_q, threading.Event(),
                           time_fn=lambda: vclock["t"], active_metrics="all")
        sd = _date_from_header_or_name(header, SLICE)
        w = DuckDBAnalyticalWriter(cfg, out, session_date=sd, source_raw=os.path.basename(SLICE),
                                   write_backend=backend)
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
                if next_b is None:
                    next_b = (math.floor(recv / interval) + 1) * interval
                while recv >= next_b:
                    tp.emit_second(int(next_b))
                    _drain(db_q, w)
                    next_b += interval
            _drain(db_q, w)
            t_bf = time.perf_counter()
            w.__exit__(None, None, None)      # finalize + CHECKPOINT + atomic rename
            t_finalize = time.perf_counter() - t_bf
        except BaseException:
            w.__exit__(*__import__("sys").exc_info())
            raise
    wall = time.perf_counter() - t0
    sampler.stop(); sampler.join(timeout=2.0)
    ok, report = verify(cfg, out, REFERENCE, live_subset=False)
    return {
        "backend": backend, "wall": wall, "finalize": t_finalize, "loop": wall - t_finalize,
        "rows": w.rows_written, "peak_rss_mb": sampler.peak / (1024 * 1024),
        "verify_ok": ok, "verify": report,
    }


def main():
    cfg = load_config(CONFIG)
    results = [run_backend(cfg, b) for b in ("executemany", "arrow")]
    print("\n================ A/B: finalize backend (fixed slice) ================")
    hdr = f"{'backend':<12} {'wall(s)':>9} {'finalize(s)':>12} {'loop(s)':>8} {'rows':>7} {'peakRSS(MB)':>12} {'verify':>8}"
    print(hdr); print("-" * len(hdr))
    for r in results:
        print(f"{r['backend']:<12} {r['wall']:>9.2f} {r['finalize']:>12.2f} {r['loop']:>8.2f} "
              f"{r['rows']:>7} {r['peak_rss_mb']:>12.1f} {'OK' if r['verify_ok'] else 'DRIFT':>8}")
    e, a = results
    print(f"\nfinalize speedup: {e['finalize'] / a['finalize']:.1f}x   "
          f"total wall speedup: {e['wall'] / a['wall']:.1f}x")
    for r in results:
        print(f"\n[{r['backend']}] verify: {'; '.join(r['verify'])}")
    return 0 if all(r["verify_ok"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
