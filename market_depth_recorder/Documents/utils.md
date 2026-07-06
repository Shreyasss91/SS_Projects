# Module: `utils.py`

Shared primitives (spec §2.1). No engine constants live here — every magic number resolves from config.

## Public API

- `IST` — fixed `+05:30` tzinfo (no DST), so no third-party tz dependency.
- `setup_logging(level="INFO")` — configure the root logger with a **single** console handler
  (idempotent: repeat calls only adjust the level, never stack handlers or leak handler FDs). Every line
  includes the thread name — the owning thread is load-bearing context in the multi-threaded pipeline (§5.1).
- `get_logger(name)` — module logger; mirrors the platform convention `logger = get_logger(__name__)`.
- `parse_ist_hhmm(value) -> datetime.time` — parse `"HH:MM"` as an IST wall-clock time; `ValueError` with
  a clear message on malformed input (drives §7.3 fast-fail and the `--from/--to` CLI guards).
- `now_ist() -> datetime` — current IST wall-clock time (session timezone, §3.1).
- `to_epoch_seconds(dt=None) -> int` — UTC epoch seconds for storage timestamps (§4.1 stores UNIX
  seconds, UTC); naive datetimes assumed UTC; `None` = now.
- `decay_weights(n_levels, decay_k) -> np.ndarray` — `w_i = exp(-decay_k·(i-1))` for `i ∈ [1, n_levels]`
  (§3.4.2 M8). With `decay_k=0.2`: `w_1=1.0`, `w_5≈0.45`, `w_10≈0.16`, `w_20≈0.02`.
- `atomic_write(path, data, encoding="utf-8")` — temp file in the same dir + `fsync` + `os.replace`, so a
  reader never sees a half-written file (health.json, §6.4). Cleans the temp and closes the descriptor on
  every path (success, error, adoption failure).
- `free_disk_mb(path) -> float` — free MiB on the filesystem containing `path` (disk-space guard, §3.1.5).
- `process_rss_mb() -> float` (F6, P8) — current-process resident set in MiB, **stdlib only** (no
  `psutil`): Windows working set via `ctypes`/`K32GetProcessMemoryInfo` (explicit `restype`/`argtypes` —
  the default int marshalling truncates the handle/pointer on 64-bit); Unix peak `ru_maxrss` from
  `resource.getrusage` (Linux KiB / macOS bytes → MiB). Best-effort: any failure → `0.0` + one DEBUG
  (observability must never crash the recorder). Feeds the `health.json` `rss_mb` field + the P8 perf
  target (< 500 MB).

## Threads / locks / FDs owned

`setup_logging` owns one `StreamHandler` (stderr; not a new FD). `atomic_write` transiently owns one temp
fd, closed on all paths. No threads or locks.

## Tests

`tests/test_utils.py` — decay reference values + monotonicity + arg rejection, IST parse ok/bad,
`to_epoch_seconds` sanity, atomic round-trip + no-stray-temp, disk-free positive/finite.
