#!/usr/bin/env python3
"""Memory-safe DuckDB-side table diff for market-depth-recorder analytics stores.

Compares two analytics DuckDB files table-by-table *entirely inside DuckDB* (ATTACH +
SQL), so peak memory stays bounded regardless of table size — unlike the built-in
``replay.verify()``, whose ``_read_table`` materialises every row into Python dicts and
OOMs on multi-million-row stores.

Two modes:
  exact      (default) per-table symmetric ``EXCEPT`` over the full row (NULL-equal set
             semantics). Zero tolerance — use when the two builds should be BIT-EXACT
             (same code + config + backend, e.g. a determinism / regression gate).
  tolerance  PK-join; float columns pass when ``abs(a - b) <= atol + rtol*abs(ref)``,
             non-float columns must match exactly (NULL-safe). Mirrors — and extends —
             ``replay._values_equal`` (whose pure-absolute atol mis-scales for
             large-magnitude quantities). Reports per-column max abs diff so
             sub-tolerance noise is visible.

Table / column / PK definitions come from
``market_depth_recorder.replay._TABLE_SPEC``, so the comparison covers exactly the set
of columns ``--verify`` uses.

Inputs
  BUILT   path to the candidate analytics .duckdb
  REF     path to the reference analytics .duckdb

Output
  Per-table verdict, per-column max abs diff (tolerance mode), and a grand total, to
  stdout.

Exit codes
  0  no drift (identical within the selected mode)
  1  drift detected
  2  usage / runtime error (bad path, schema mismatch, ...)

----------------------------------------------------------------------------------------
Purpose
  Reusable determinism / value-parity gate for analytics rebuilds — the scalable
  replacement for the OOM-prone built-in verify at full-day scale, and a working
  prototype of the deferred DuckDB-side ``verify()`` rewrite + atol/rtol semantics.

Typical workflow
  1. Rebuild an analytics store two ways (two backends, or before/after a change, or a
     re-replay vs a canonical reference).
  2. `exact` mode to prove a like-for-like rebuild is bit-identical, OR
     `tolerance` mode to compare across a numerically-different implementation.
  3. A non-zero exit fails your gate.

Example command line
  # bit-exact determinism gate (e.g. chunked build vs canonical reference)
  python market_depth_recorder/tools/validation/duckdb_table_diff.py \
      build.duckdb reference.duckdb

  # tolerance gate across implementations (atol + rtol, like numpy.isclose)
  python market_depth_recorder/tools/validation/duckdb_table_diff.py \
      --mode tolerance --atol 1e-9 --rtol 1e-9 build.duckdb reference.duckdb

Related documentation
  Documents/PERFORMANCE.md  (§6 the _slope/reference finding; §11 the deferred
                             DuckDB-side verify() rewrite this prototypes)
  Documents/archive/offline-replay-optimization-engineering-journal.md
"""
from __future__ import annotations

import argparse
import os
import pathlib
import sys

# Allow running as a plain script: put the SS_Projects root (…/tools/validation → up 3)
# on sys.path so `import market_depth_recorder...` resolves without PYTHONPATH.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

import duckdb  # noqa: E402

from market_depth_recorder.replay import _TABLE_SPEC  # noqa: E402

try:
    from market_depth_recorder.replay import _VERIFY_ATOL as _DEFAULT_ATOL
except Exception:  # pragma: no cover - fallback if the constant is renamed
    _DEFAULT_ATOL = 1e-9

_FLOAT_TYPES = {"DOUBLE", "REAL", "FLOAT", "DECIMAL"}


def _attach(con: duckdb.DuckDBPyConnection, built: str, ref: str) -> None:
    con.execute(f"ATTACH '{built}' AS built (READ_ONLY)")
    con.execute(f"ATTACH '{ref}' AS ref (READ_ONLY)")


def _col_types(con: duckdb.DuckDBPyConnection, table: str) -> dict[str, str]:
    rows = con.execute(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_catalog='built' AND table_name=?",
        [table],
    ).fetchall()
    return {name: dtype.upper() for name, dtype in rows}


def diff_exact(con: duckdb.DuckDBPyConnection) -> int:
    """Per-table symmetric EXCEPT (bit-exact set difference). Returns total diverging rows."""
    grand = 0
    for table, (columns, _pk) in _TABLE_SPEC.items():
        cols = ", ".join(columns)
        nb = con.execute(f"SELECT count(*) FROM built.{table}").fetchone()[0]
        nr = con.execute(f"SELECT count(*) FROM ref.{table}").fetchone()[0]
        only_b = con.execute(
            f"SELECT count(*) FROM (SELECT {cols} FROM built.{table} "
            f"EXCEPT SELECT {cols} FROM ref.{table})"
        ).fetchone()[0]
        only_r = con.execute(
            f"SELECT count(*) FROM (SELECT {cols} FROM ref.{table} "
            f"EXCEPT SELECT {cols} FROM built.{table})"
        ).fetchone()[0]
        div = only_b + only_r
        grand += div
        status = "OK" if div == 0 else f"DRIFT (only_built={only_b} only_ref={only_r})"
        print(f"[{table:<26}] built={nb:>10} ref={nr:>10} symdiff={div:<8} -> {status}")
    return grand


def diff_tolerance(con: duckdb.DuckDBPyConnection, atol: float, rtol: float) -> int:
    """PK-join tolerance diff: floats pass when abs(a-b) <= atol + rtol*abs(ref).

    Reports per-column max abs diff. Returns total cells violating the tolerance.
    """
    grand_bad = 0
    for table, (columns, pk) in _TABLE_SPEC.items():
        types = _col_types(con, table)
        on = " AND ".join(f"b.{k} IS NOT DISTINCT FROM r.{k}" for k in pk)
        non_pk = [c for c in columns if c not in pk]

        worst: list[tuple[str, int, float | None]] = []  # (col, bad_count, max_abs_diff)
        for c in non_pk:
            is_float = any(t in types.get(c, "") for t in _FLOAT_TYPES)
            if is_float:
                pred = (
                    f"((b.{c} IS NULL) <> (r.{c} IS NULL)) OR "
                    f"(b.{c} IS NOT NULL AND r.{c} IS NOT NULL AND "
                    f"NOT (isnan(b.{c}) AND isnan(r.{c})) AND "
                    f"abs(b.{c} - r.{c}) > {atol} + {rtol} * abs(r.{c}))"
                )
                maxdiff = (
                    f"max(CASE WHEN b.{c} IS NOT NULL AND r.{c} IS NOT NULL "
                    f"AND NOT (isnan(b.{c}) AND isnan(r.{c})) "
                    f"THEN abs(b.{c} - r.{c}) ELSE NULL END)"
                )
            else:
                pred = f"(b.{c} IS DISTINCT FROM r.{c})"
                maxdiff = "NULL"
            row = con.execute(
                f"SELECT sum(CASE WHEN {pred} THEN 1 ELSE 0 END), {maxdiff} "
                f"FROM built.{table} b JOIN ref.{table} r ON {on}"
            ).fetchone()
            worst.append((c, row[0] or 0, row[1]))

        table_bad = sum(w[1] for w in worst)
        grand_bad += table_bad
        offenders = [w for w in worst if w[1]]
        status = "OK" if table_bad == 0 else f"{len(offenders)} col(s) over tolerance"
        print(f"[{table}]  -> {status}")
        floaty = sorted(
            (w for w in worst if w[2] is not None),
            key=lambda w: w[2] if w[2] is not None else -1.0,
            reverse=True,
        )[:6]
        for c, bad, md in floaty:
            flag = "  <-- OVER TOL" if bad else ""
            print(f"    {c:<30} max|diff|={md:.3e}  bad_cells={bad}{flag}")
        for c, bad, md in offenders:
            if md is None:  # non-float column mismatch
                print(f"    {c:<30} NON-FLOAT MISMATCH bad_cells={bad}  <-- OVER TOL")
        print()
    return grand_bad


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="duckdb_table_diff.py",
        description="Memory-safe DuckDB-side diff of two market-depth-recorder analytics stores.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog="Exit codes: 0 = no drift, 1 = drift, 2 = usage/runtime error.",
    )
    p.add_argument("built", metavar="BUILT", help="candidate analytics .duckdb path")
    p.add_argument("ref", metavar="REF", help="reference analytics .duckdb path")
    p.add_argument(
        "--mode",
        choices=("exact", "tolerance"),
        default="exact",
        help="exact = bit-exact symmetric EXCEPT; tolerance = PK-join atol+rtol float compare",
    )
    p.add_argument("--atol", type=float, default=_DEFAULT_ATOL,
                   help="absolute tolerance (tolerance mode)")
    p.add_argument("--rtol", type=float, default=0.0,
                   help="relative tolerance (tolerance mode); 0 reproduces the legacy pure-absolute gate")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    for label, path in (("BUILT", args.built), ("REF", args.ref)):
        if not os.path.isfile(path):
            print(f"error: {label} not found: {path}", file=sys.stderr)
            return 2

    con = duckdb.connect(":memory:")
    try:
        _attach(con, args.built, args.ref)
        print(f"BUILT = {args.built}\nREF   = {args.ref}\nmode  = {args.mode}", end="")
        if args.mode == "tolerance":
            print(f"   atol={args.atol}  rtol={args.rtol}", end="")
        print("\n")
        if args.mode == "exact":
            total = diff_exact(con)
            unit = "symmetric-difference rows"
            ok_msg = "ZERO DRIFT (bit-exact, identical set)"
        else:
            total = diff_tolerance(con, args.atol, args.rtol)
            unit = "cells over tolerance"
            ok_msg = f"ZERO DRIFT within atol={args.atol} rtol={args.rtol}"
    except duckdb.Error as exc:
        print(f"error: DuckDB comparison failed (schema/type mismatch?): {exc}", file=sys.stderr)
        return 2
    finally:
        con.close()

    print(f"\nGRAND {unit} = {total}  -> {ok_msg if total == 0 else 'DRIFT'}")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
