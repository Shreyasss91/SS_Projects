"""Replay the ~100-min raw log and capture the exact book_pressure input series for the 45 target
(symbol, ts, time_window) keys — the series that _regression_slopes feeds to _slope. Also captures ctx.eps.

Wraps TickProcessor._window_rows (the method that has ts+symbol+hist) and reconstructs the series exactly
as _regression_slopes does: _valued(_lastn(hist, n), "book_pressure"). No DB write — inputs only.
Output: captured.json  = {"eps": <float>, "series": [{symbol,ts,n, y:[...]}, ...]}
"""
from __future__ import annotations

import gzip, json, math, os, queue, threading

from market_depth_recorder.config import load_config
from market_depth_recorder.replay import _load_header, _date_from_header_or_name
from market_depth_recorder.instrument_manager import InstrumentManager
from market_depth_recorder.processor import TickProcessor
from market_depth_recorder.metrics.rolling import _lastn, _valued

SCRATCH = os.path.dirname(os.path.abspath(__file__))
CONFIG = "market_depth_recorder/config.yaml"
RAW = "market_depth_recorder/data/2026-07-07/market_depth_raw_20260707.jsonl.gz"

targets = json.load(open(os.path.join(SCRATCH, "targets.json")))
want = {(t["symbol"], t["ts_epoch"], t["time_window"]) for t in targets}
captured: dict[tuple, list] = {}


def main():
    cfg = load_config(CONFIG)
    interval = float(cfg.recorder["resample_interval_sec"])
    with gzip.open(RAW, "rt", encoding="utf-8") as fh:
        header = _load_header(fh)
        im = InstrumentManager.from_header(cfg, (header or {}).get("instruments"))
        vclock = {"t": 0.0}
        tp = TickProcessor(cfg, im, queue.Queue(), queue.Queue(), threading.Event(),
                           time_fn=lambda: vclock["t"], active_metrics="all")
        eps = tp._ctx.eps

        orig_window_rows = tp._window_rows

        def wrapped(ts, clean, heavy_skip):
            hist = list(tp._window[clean])
            for n in tp._time_windows:
                key = (clean, int(ts), int(n))
                if key in want and key not in captured:
                    y = _valued(_lastn(hist, n), "book_pressure")
                    captured[key] = list(y)
            return orig_window_rows(ts, clean, heavy_skip)

        tp._window_rows = wrapped

        _date_from_header_or_name(header, RAW)
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
                next_b += interval

    out_series = [{"symbol": s, "ts": t, "n": n, "y": captured[(s, t, n)]}
                  for (s, t, n) in want if (s, t, n) in captured]
    missing = [k for k in want if k not in captured]
    payload = {"eps": eps, "series": out_series}
    with open(os.path.join(SCRATCH, "captured.json"), "w") as fh:
        json.dump(payload, fh)
    print(f"eps = {eps!r}")
    print(f"captured {len(out_series)}/{len(want)} target series; missing={len(missing)}")
    if missing:
        for k in missing[:10]:
            print("  MISSING", k)


if __name__ == "__main__":
    main()
