"""Dump the 45 over-atol book_pressure_slope target keys (+ stored built/ref values) to JSON."""
import json, os
import duckdb

SCRATCH = os.path.dirname(os.path.abspath(__file__))
BUILT = os.path.join(SCRATCH, "bench", "fullrun_arrow.duckdb").replace("\\", "/")
REF = ("C:/Users/admin/Downloads/ai tools/openalgo_platform/openalgo/strategies/"
       "SS_Projects/market_depth_recorder/data/2026-07-07/market_depth_analytics_20260707.duckdb")

con = duckdb.connect(":memory:")
con.execute(f"ATTACH '{BUILT}' AS built (READ_ONLY)")
con.execute(f"ATTACH '{REF}' AS ref (READ_ONLY)")

# typeof timestamp to know how to match during replay
tcol = con.execute("SELECT data_type FROM information_schema.columns "
                   "WHERE table_catalog='built' AND table_name='strike_window_metrics' "
                   "AND column_name='timestamp'").fetchone()[0]
print("timestamp column type =", tcol)

on = "b.timestamp=r.timestamp AND b.symbol=r.symbol AND b.time_window=r.time_window"
rows = con.execute(f"""
  SELECT b.symbol, b.time_window, b.timestamp AS ts_epoch,
         b.book_pressure_slope AS built, r.book_pressure_slope AS ref
  FROM built.strike_window_metrics b JOIN ref.strike_window_metrics r ON {on}
  WHERE abs(b.book_pressure_slope - r.book_pressure_slope) > 1e-9
""").fetchall()

targets = [{"symbol": s, "time_window": int(w), "ts_epoch": int(te),
            "built": bt, "ref": rf} for s, w, te, bt, rf in rows]
out = os.path.join(SCRATCH, "targets.json")
with open(out, "w") as fh:
    json.dump(targets, fh, indent=1)
print(f"{len(targets)} targets -> {out}")
print("sample:", targets[0])
con.close()
