# Follow-up investigation — 2026-08-30

**Scope.** The four **OPEN FOLLOW-UP** items in Plan_002 §23.1 as they stood 2026-08-29.

**Method.** Read-only analysis of the F10B artifacts in `data/`, plus source inspection.
No production code was modified. Every number below is derived from the primary artifacts and is
reproducible from the scripts noted in §6.

**Status vocabulary** is the plan's own: `OBSERVED` > `INFERRED` > `UNKNOWN` > `NOT TESTED`.
A `NOT TESTED` boundary is never read as a negative result.

---

## 1. Summary

| Item | Status before | Status after |
|---|---|---|
| Cause of the two `health.json` `PermissionError` events | `INFERRED` | **ESTABLISHED** (§2) |
| 15-leg condition held only 40 of 361 minutes | open | **EXPLAINED** — market liquidity, not an allocation defect (§3) |
| Flaky `test_real_four_thread_pipeline_end_to_end` | open | **ROOT CAUSE IDENTIFIED**, fix not applied (§4) |
| `_JOIN_TIMEOUT_SEC` sizing for a full trading day | open | **NOT STARTED** — deferred, needs a measured session (§5) |

Two further results fell out of the work and are recorded in §3.4 and §3.5.

---

## 2. The two `health.json` `PermissionError` events — `INFERRED` → `ESTABLISHED`

### 2.1 The events

Both are in `data/f10b_recorder.log`, raised at `main.py:481` inside `_write_health`:

| # | Timestamp (IST) | Log line | Exception |
|---|---|---|---|
| 1 | `2026-08-28 11:10:03,162` | 1570 | `PermissionError: [WinError 5] Access is denied: '.tmp_2cm5lm0z' -> '.../data/health.json'` |
| 2 | `2026-08-28 15:24:50,126` | 9004 | `PermissionError: [WinError 5] Access is denied: '.tmp_u1enx5su' -> '.../data/health.json'` |

Both are the `os.replace` at the end of `atomic_write` (`utils.py:134`) — the rename step, not the
write. On Windows that rename fails while any process holds the destination open.

### 2.2 The correlation

The watcher (`tools/validation/f10_live_monitor.py`) reads `health.json` every 15 s. Its timeline
`data/f10b_timeline_20260828.jsonl` holds 1293 samples, each stamped with `at`.

| Event | Timestamp | Nearest watcher sample | Offset |
|---|---|---|---|
| 1 | `11:10:03.162` | `11:10:03.166` | **+4 ms** |
| 2 | `15:24:50.126` | `15:24:50.127` | **+1 ms** |

### 2.3 The `at` field is the watcher's own clock — verified, not assumed

If `at` were copied out of `health.json` (written on the recorder's cadence), matching it to the
error would prove nothing. It was tested and rejected:

```
mod 1.0s  -> remainder spread 0.998s   free-running
mod 5.0s  -> remainder spread 4.994s   free-running
mod 15.0s -> remainder spread 14.979s  free-running
```

A value copied from a coarser-cadence file would be quantised to that cadence. `at` is not
quantised at 1 s, 5 s or 15 s — it is a free-running clock with ~15 s cadence and millisecond
jitter, i.e. the watcher's own sampling instant.

### 2.4 The ordering is exactly right

`tools/validation/f10_live_monitor.py`:

- **line 480** — `health = read_health(args.health)` (opens `health.json`, line 112)
- **line 488** — `current = sample(health, at=time.time())` (stamps `at`)

The stamp is taken **after** the read. So the file is held open in the milliseconds *preceding*
`at` — which is precisely where both errors landed (+4 ms and +1 ms before the stamp).

### 2.5 Verdict

Under a null model where an unrelated error is uniform over the 15 s sampling period, and using a
generous ±4 ms vulnerable window:

```
P(one unrelated error lands in the window) = 5.33e-04
P(both land in the window by chance)      = 2.84e-07   (about 1 in 3.5 million)
```

**The inference is established.** Both errors occurred while the watcher held `health.json` open.
The events remain benign and structurally expected — both sides already absorb them
(`main.py:482`, `f10_live_monitor.py:481`) — but the mechanism is no longer a guess.

This item can be promoted out of OPEN FOLLOW-UP. No code change is required or implied.

---

## 3. The 15-leg condition held only 40 of 361 minutes — EXPLAINED

The question was framed in the register as an *allocation-consistency* question. It is not one.

### 3.1 The framework held 15 premium slots for 100% of the session

`premium_legs` — `adapter.premium_leg_count()`, `websocket_client.py:789` — has exactly **one
distinct value across all 1293 samples: 15**. The framework asked for and held the full premium
budget for the entire watched session. There is no allocation shortfall to explain.

### 3.2 `delivering_legs` is a liquidity measure, not a health measure

`websocket_client.py:791`:

```python
"delivering_legs": sum(1 for view in adapter.legs() if view.is_delivering)
```

`broker_adapter.py:213` — `is_delivering` is `state is LegState.DELIVERING`, and `LegState.DELIVERING`
is defined at line 127 as *"at least one packet observed on this wire symbol"*. Line 653 shows the
transition is **sticky**: `REQUESTED` or `FAILED` become `DELIVERING` on the first packet, and stay
there until the leg is released or a reconnect discards the adapter's local knowledge
(lines 38-39).

So `delivering_legs` counts how many premium strikes have ticked **at least once since the leg was
last claimed**. A subscribed-but-illiquid strike never ticks and is never counted. It measures
liquidity across the 15 selected strikes; it does not measure whether the framework did its job.

### 3.3 Observed distribution

| `delivering_legs` | Samples |
|---|---|
| 15 | 160 |
| 7 | 34 |
| 5 | 1097 |
| 3 | 1 |
| 0 | 1 |

Run-length, with every reconnect from the recorder log:

```
  5 legs  10:12:31 -> 12:29:53   137.4 min
  7 legs  12:29:53 -> 12:38:24     8.5 min     (reconnect 12:29:33)
  5 legs  12:38:24 -> 13:56:29    78.1 min     (reconnect 12:37:59 — drop at +14 s)
 15 legs  13:56:29 -> 14:14:15    17.8 min
  0 legs  14:14:15 -> 14:14:30     0.25 min    (reconnect 14:14:03 — drop at +2 s)
 15 legs  14:14:30 -> 14:36:47    22.3 min     (restored, consistent with the plan's +10.6 s)
  5 legs  14:36:47 -> 14:51:03    14.3 min     (reconnect 14:36:33 — drop at +4 s)
  3 legs  14:51:03 -> 14:51:18     0.25 min
  5 legs  14:51:18 -> 15:37:05    45.8 min
```

**Every decrease in `delivering_legs` coincides with a reconnect** (+14 s, +2 s, +4 s), which is
exactly the predicted behaviour of a sticky cumulative counter that a reconnect resets. The single
remaining decrease (5 → 3 at 14:51:03, one sample) is a retier releasing and re-claiming legs.

### 3.4 Result: the "40 minutes" is the D18 window itself

```
15-leg window (measured)      : 13:56:29 .. 14:36:32   (40.0 min, 160 samples)
D18 window (Plan_002 §22.13.5): 13:56:29 .. 14:36:32
```

Identical to the second. The 15-leg condition did not "hold for only 40 of 361 minutes" as a
defect — it held for the whole of the window D18 was measured over, and the plan's own arithmetic
(40 of 361) describes that window as a fraction of the session.

Two depth-degradation hypotheses are also eliminated: `actual_depth` was `{"NIFTY": 50,
"SENSEX": 5}` for the **entire** 324.6-minute watch, so NIFTY never degraded to 5, and the
pre-flight stop condition was never approached.

**Interpretation (`INFERRED`).** The framework selects the 15 strikes nearest ATM. Only the
innermost ~5 ticked for most of the session; the outer ~10 were too illiquid to deliver. Activity
broadened in the final 40 minutes before close and all 15 ticked. This reading is consistent with
every measurement above but is not directly proven by them — the artifacts record *that* legs
delivered, not *why*.

**Consequence, worth a product decision but not a defect:** for most of the session roughly 10 of
the 15 premium slots were occupied by strikes too illiquid to deliver a packet. Distance-to-ATM is
a reasonable liquidity proxy and the framework uses it correctly; whether the budget should instead
favour realised activity is a policy question, not a bug.

### 3.5 A finding that bears on `UNKNOWN #1`

`UNKNOWN #1` (reconnect depth restoration) is recorded in §22.13.5 as **RESOLVED** on the strength
of the 14:14:03 reconnect only, with the plan noting five other natural reconnects were not
individually depth-verified.

This work inspected a **second** reconnect. At 14:36:33 the feed dropped and 172 legs were
reissued at 14:36:43. `delivering_legs` fell to 5 and **did not return to 15 for the remaining
~60 minutes of the session.**

The two reconnects therefore had materially different outcomes. The mechanism in §3.2 explains
this without contradicting the plan: resumption is gated by whether a strike happens to tick after
the reissue, so a reconnect resets a *liquidity* counter, not a subscription. The 14:14:03
reconnect resumed during the active period, so all 15 re-ticked quickly; the 14:36:33 reconnect
occurred as activity was fading, so only 5 did.

**Recommended action.** `UNKNOWN #1` should not stand as `RESOLVED`. It should be restated as
`PARTIALLY OBSERVED`: one reconnect resumed quickly, one did not, and the difference is explained
by liquidity rather than by depth restoration. Note also that `delivering_legs` proves only that a
packet arrived on the `SYMBOL:50` wire symbol — it does **not** establish the level count, which
remains the preserve of the Tier 0 raw-log verification the plan cites. Nothing here contradicts
the plan's Tier 0 claim; this says only that `delivering_legs` is not the evidence for it.

---

## 4. Flaky `test_real_four_thread_pipeline_end_to_end` — root cause identified, fix NOT applied

### 4.1 The finding

`tests/test_integration.py:186`. The test is not mysteriously nondeterministic; **its deterministic
worst case does not fit the budget it is given.**

Part 1, before any DuckDB work begins:

| Component | Worst-case cost |
|---|---|
| `_wait_until(lambda: ...records_written > 0, timeout=15.0)` | 15.0 s |
| `time.sleep(1.4)` | 1.4 s |
| `_teardown_pipeline()` — four **sequential** `join(timeout=10)` (`main.py:463-468`) | 40.0 s |
| **Total** | **56.4 s** |

Part 2 then runs `subprocess.run(... --replay --catchup ..., timeout=120)` to build the DuckDB
store, replays the same raw log a second time in-process via `replay.replay_file`, and runs
`replay.verify`. Against a 60 s cap that leaves ~3.6 s of margin for two DuckDB builds.

The joins are sequential, not parallel: feed → processor → `db_shutdown_event.set()` → db_writer →
raw_writer, each with its own 10 s budget.

### 4.2 Supporting observations

- There is **no timeout configuration in the repository at all**: `pytest.ini`, `setup.cfg`,
  `pyproject.toml` and `tox.ini` are all absent. The 60 s figure comes from the invocation or CI,
  not from config. `tests/conftest.py` registers the `integration` marker and nothing else.
- The measured 13.75 s isolated run leaves the ~56.4 s worst case unexercised — which is exactly
  why the test passes alone and fails under load.

### 4.3 Why no fix is recorded here

**`NOT TESTED` — environment, not conclusion.** The project's dependencies (`pytest`, `duckdb`,
`PyYAML`, `openalgo`, `websocket-client`) are not installed in any interpreter available from this
workspace, and there is no venv in the tree. The F10B artifacts were produced on a different host
(paths in the logs read `C:\Users\admin\...`), reachable here only through the Tailscale share,
which exposes the project directory and not that host's Python environment.

A timing fix for a load-sensitive test cannot be validated by inspection, and a timing measurement
taken over a Tailscale mount would not be representative. Rather than commit an unverifiable
change, the fix is left for the host that can run the suite.

### 4.4 Options, in order of preference

1. **Reduce the deterministic floor.** The 15 s `_wait_until` and the fixed `time.sleep(1.4)` are
   generous for a scripted feed whose first option second is expected within a second or two.
   Cutting them attacks the actual cost rather than raising the ceiling.
2. **Give `integration`-marked tests a realistic cap.** The worst case is ~56 s *plus* two DuckDB
   builds. Either a `pytest.ini` with a marker-specific timeout, or `@pytest.mark.timeout(...)` if
   `pytest-timeout` is present. Weakest option: it hides a slow teardown rather than fixing it.
3. **Address the shared root cause (§4.5).** Highest value, but touches production code.

### 4.5 Shared root cause with item 4 of the register

Items 1 and 4 of the register are the same problem seen twice. `main.py:463-468` joins four workers
**sequentially**, 10 s each. One slow worker costs 10 s of teardown in production and 10 s of
wall-clock in this test. So the test's timeout ceiling is really a teardown-latency question, and
instrumenting the joins (§5) is what will finally explain both.

---

## 5. `_JOIN_TIMEOUT_SEC` sizing — NOT STARTED (deferred by choice)

Left untouched. Fork F25's rationale is the reason:

> "I do not want Claude inventing arbitrary numeric thresholds ... propose exact numeric abort
> thresholds from existing system semantics where possible."

Changing `10.0` on speculation would be exactly that. The plan also records the item as
"deliberately not changed ... its own investigation, not a phase".

**When a session is available**, the instrument-first path is:

1. Wrap each `join()` at `main.py:463-468` with `time.monotonic()` and log `join_ms` per worker.
2. Run a full session; read the distribution.
3. Only then decide — and note the real question may be **ordering**, not magnitude: the budget is
   40 s cumulative because the joins are serial, so parallelising them may matter more than
   changing 10.0.

---

## 6. Reproducibility

The analysis scripts are committed alongside this note, in
`plans/Plan_002_evidence/analysis/`:

| Script | Produces |
|---|---|
| `analyze_perm.py` | the two PermissionError events, nearest-sample search, log context |
| `verify_at.py` | the `at` quantisation test and the null-model probability |
| `analyze_15leg.py` | field distributions, per-minute aggregation, run-length encoding |
| `transitions.py` | recorder-log context at the 13:56:29 / 14:14:15 / 14:36:47 instants |
| `verify_mechanism.py` | reconnect correlation, 15-leg window vs D18 window |

Run them from the repository root; no arguments are required:

```
python plans/Plan_002_evidence/analysis/analyze_perm.py
python plans/Plan_002_evidence/analysis/verify_at.py
python plans/Plan_002_evidence/analysis/analyze_15leg.py
python plans/Plan_002_evidence/analysis/transitions.py
python plans/Plan_002_evidence/analysis/verify_mechanism.py
```

**Data location.** Each script resolves its inputs through a shared `resolve_data_dir()`, in this
order:

1. `$MARKET_DEPTH_DATA` — set this to override everything else.
2. `<repo>/data` — derived from the script's own location (`parents[3]`), used when
   `data/f10b_timeline_20260828.jsonl` is present. This is the normal case.
3. `%TEMP%/mdr_analysis` — a fallback for the local staged copies, so the scripts keep working
   off a scratch dir when the artifacts have been copied off the share.
4. Otherwise the script exits with instructions rather than guessing.

Because path (2) is derived from `__file__` and not from the working directory, the scripts behave
identically whether they are invoked from the repository root or from anywhere else.

Primary artifacts (read-only, unchanged): `data/f10b_recorder.log`,
`data/f10b_watcher.log`, `data/f10b_timeline_20260828.jsonl`.

**Verification performed.** All five scripts were byte-compiled and executed against the staged
copies, and all five exited 0 reproducing the figures quoted in this note — notably
`P(both land in window by chance) = 2.84e-07 (1 in 3.52e+06)` (§2),
`premium_legs: 1293 samples, distinct values 1 -> 15x1293` (§3), and
`15-leg window: 13:56:29 .. 14:36:32 (40.0 min, 160 samples)` (§3). With `MARKET_DEPTH_DATA`
unset, resolution was confirmed to land on the repository `data/` directory with both the timeline
and the recorder log present. Deterministic environment caveat: the scripts read only the JSONL and
log artifacts, so the numbers above are reproducible on any host that can read `data/` — but the
timing work in §4 was *not* reproducible here, because no interpreter on this host carries the
project's dependencies (see §4.3).

---

## 7. What changed

**Nothing in the source tree.** This is an analysis document. Two register entries are proposed for
promotion (§2, §3), one restatement is recommended (§3.5), and one fix is specified but not applied
(§4.3).
