#!/usr/bin/env python3
"""High-precision adjudication of the closed-form OLS ``_slope`` against exact arithmetic.

Given a JSON file of captured input series, recomputes each series' least-squares slope
three ways using the **identical** formula and ``eps``:

  * numpy pairwise sums        — the historical / reference implementation
  * pure-Python sequential sums — the current (Phase-1b) implementation
  * exact ``fractions.Fraction`` arithmetic on the exact float inputs — ground truth

then reports each float result's absolute and relative error against the exact value and
tallies which of numpy vs pure-Python is closer. Because ``sx`` and ``sxx`` are exact
integers in every path, the only source of divergence is the summation order of
``sy`` / ``sxy`` — this isolates floating-point accumulation error.

This was the tool that settled whether the Phase-1b pure-Python ``_slope`` (which
differs from the old numpy one only in summation order) was as accurate as the original.
It generalises to any float-vs-float summation-order question of this shape.

Inputs
  SERIES_JSON   {"eps": <float>, "series": [{"symbol","ts","n","y":[...]}, ...]}
                (historically produced by capture_series.py — see
                Documents/archive/validation-artifacts/).
  --targets     optional JSON [{"symbol","ts_epoch","time_window","built","ref"}, ...]
                with the stored DB values, to cross-check that the recomputed
                pure/numpy slopes match what was actually written (built=pure, ref=numpy).
  --eps         override the OLS denominator epsilon (default: value from SERIES_JSON).

Output
  Per-series error table + summary (winners, mean abs error, max rel error) to stdout.

Exit codes
  0  pure-Python is as accurate as, or more accurate than, numpy (validation passes)
  1  numpy is more accurate (would warrant revisiting the pure-Python implementation)
  2  usage / runtime error, or a DB cross-check mismatch (captured inputs not faithful)

----------------------------------------------------------------------------------------
Purpose
  Adjudicate a numerical change against a higher-precision reference instead of against
  an assumption — the discipline behind keeping the pure-Python _slope.

Typical workflow
  1. Capture the exact input series for the rows under question to a SERIES_JSON.
  2. Run this tool; read the winner tally and mean/max errors.
  3. Exit 0 confirms the current implementation is at least as accurate.

Example command line
  python market_depth_recorder/tools/validation/highprec_slope.py \
      captured.json --targets targets.json

Related documentation
  Documents/PERFORMANCE.md  (§6 the _slope investigation and why the reference changed)
  Documents/archive/offline-replay-optimization-engineering-journal.md
  Documents/archive/validation-artifacts/  (the original 45-row captured.json/targets.json)
"""
from __future__ import annotations

import argparse
import json
import sys
from fractions import Fraction as F

import numpy as np


def slope_numpy(y: list[float], eps: float) -> float:
    """OLS slope via numpy pairwise summation (historical / reference implementation)."""
    m = len(y)
    x = np.arange(1, m + 1, dtype=np.float64)
    yv = np.asarray(y, dtype=np.float64)
    denom = m * float((x * x).sum()) - float(x.sum()) ** 2
    return (m * float((x * yv).sum()) - float(x.sum()) * float(yv.sum())) / (denom + eps)


def slope_pure(y: list[float], eps: float) -> float:
    """OLS slope via pure-Python sequential summation (current implementation)."""
    m = len(y)
    sx = m * (m + 1) / 2.0
    sxx = m * (m + 1) * (2 * m + 1) / 6.0
    sy = 0.0
    sxy = 0.0
    for i, yi in enumerate(y, start=1):
        sy += yi
        sxy += i * yi
    denom = m * sxx - sx * sx
    return (m * sxy - sx * sy) / (denom + eps)


def slope_exact(y: list[float], eps: float) -> F:
    """Exact rational evaluation of the SAME formula on the exact float inputs (ground truth)."""
    m = len(y)
    yf = [F(v) for v in y]  # each float64 is an exact rational
    sx = F(m * (m + 1), 2)
    sxx = F(m * (m + 1) * (2 * m + 1), 6)
    sy = sum(yf, F(0))
    sxy = sum((F(i) * yi for i, yi in enumerate(yf, start=1)), F(0))
    denom = m * sxx - sx * sx
    return (m * sxy - sx * sy) / (denom + F(eps))


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="highprec_slope.py",
        description="Validate the closed-form OLS _slope against exact Fraction arithmetic.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog="Exit codes: 0 = pure-Python as/more accurate, 1 = numpy more accurate, 2 = error.",
    )
    p.add_argument("series_json", metavar="SERIES_JSON",
                   help='captured series file: {"eps": float, "series": [{symbol,ts,n,y:[...]}]}')
    p.add_argument("--targets", help="optional targets JSON with stored built/ref values to cross-check")
    p.add_argument("--eps", type=float, default=None,
                   help="OLS denominator epsilon (default: taken from SERIES_JSON)")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        with open(args.series_json) as fh:
            payload = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read SERIES_JSON: {exc}", file=sys.stderr)
        return 2

    eps = args.eps if args.eps is not None else payload.get("eps")
    if eps is None:
        print("error: no eps in SERIES_JSON and --eps not given", file=sys.stderr)
        return 2
    series = payload.get("series", [])
    if not series:
        print("error: SERIES_JSON has no 'series'", file=sys.stderr)
        return 2

    targets = {}
    if args.targets:
        try:
            with open(args.targets) as fh:
                targets = {(t["symbol"], t["ts_epoch"], t["time_window"]): t
                           for t in json.load(fh)}
        except (OSError, json.JSONDecodeError, KeyError) as exc:
            print(f"error: cannot read --targets: {exc}", file=sys.stderr)
            return 2

    print(f"eps = {eps!r}   series = {len(series)}\n")
    hdr = (f"{'symbol':<22}{'n':>3} {'m':>3} {'|slope|':>13} "
           f"{'np_abserr':>11} {'pure_abserr':>12} {'np_relerr':>11} {'pure_relerr':>12}  winner")
    print(hdr)

    np_wins = pure_wins = ties = 0
    np_abs_sum = pure_abs_sum = 0.0
    np_rel_max = pure_rel_max = 0.0
    mism_np = mism_pure = 0

    for s in series:
        y = s["y"]
        exact = slope_exact(y, eps)
        sn = slope_numpy(y, eps)
        sp = slope_pure(y, eps)

        tgt = targets.get((s.get("symbol"), s.get("ts"), s.get("n")))
        if tgt is not None:
            if abs(sp - tgt["built"]) > 1e-6:
                mism_pure += 1
            if abs(sn - tgt["ref"]) > 1e-6:
                mism_np += 1

        np_abs = abs(F(sn) - exact)
        pure_abs = abs(F(sp) - exact)
        absmag = abs(exact) if exact != 0 else F(1)
        np_rel = float(np_abs / absmag)
        pure_rel = float(pure_abs / absmag)
        np_abs_f = float(np_abs)
        pure_abs_f = float(pure_abs)
        np_abs_sum += np_abs_f
        pure_abs_sum += pure_abs_f
        np_rel_max = max(np_rel_max, np_rel)
        pure_rel_max = max(pure_rel_max, pure_rel)
        if pure_abs < np_abs:
            winner = "pure"; pure_wins += 1
        elif np_abs < pure_abs:
            winner = "numpy"; np_wins += 1
        else:
            winner = "tie"; ties += 1
        print(f"{s.get('symbol', ''):<22}{s.get('n', 0):>3} {len(y):>3} {abs(float(exact)):>13.4f} "
              f"{np_abs_f:>11.3e} {pure_abs_f:>12.3e} {np_rel:>11.3e} {pure_rel:>12.3e}  {winner}")

    print(f"\nDB cross-check mismatches: pure-vs-built={mism_pure}  numpy-vs-ref={mism_np} (expect 0)")
    print(f"winners: pure closer={pure_wins}  numpy closer={np_wins}  tie={ties}")
    print(f"mean abs err : numpy={np_abs_sum / len(series):.3e}   pure={pure_abs_sum / len(series):.3e}")
    print(f"max  rel err : numpy={np_rel_max:.3e}   pure={pure_rel_max:.3e}")
    pure_at_least_as_accurate = pure_abs_sum <= np_abs_sum
    print(f"\n=> both agree to ~{max(np_rel_max, pure_rel_max):.1e} RELATIVE; "
          f"{'pure-Python is as/more accurate' if pure_at_least_as_accurate else 'numpy is more accurate'}")

    if targets and (mism_pure or mism_np):
        print("\nWARNING: DB cross-check mismatched — captured inputs may not be faithful.", file=sys.stderr)
        return 2
    return 0 if pure_at_least_as_accurate else 1


if __name__ == "__main__":
    raise SystemExit(main())
