# Plan_002 F10B Evidence — Detailed Test & Experimental Record

## 1. Document control

| Field | Value |
|---|---|
| Document | `Documents/patches/Plan_002_F10B_Evidence.md` |
| Purpose | Forensic test notebook for F10B: how the phase was prepared, executed, monitored, analysed, corrected and concluded |
| Trading date | 2026-08-28 (NIFTY weekly expiry 01-SEP-2026) |
| Phase | Plan_002 §22.13, stage F10B |
| Companion | `Documents/patches/f10_live_validation_20260828.md` — the concise **formal** F26 evidence and D18 decision record |
| Starting checkpoint | `77bd786` `feat(framework): prepare F10 live validation` (F10A, 2026-08-27) |
| Final checkpoint | `18e9dd6` `docs(framework): record F10B true-scale live validation` (2026-08-28) |
| Status | F10B complete; D18 CLOSED; **three discrepancies against the formal evidence were found while writing this document, reported, and then corrected in a separate commit — see §16.6 and §24** |
| Records | Actual execution, not planned execution |

**Relationship to the formal evidence.** `f10_live_validation_20260828.md` states the result. This
document states how the result was obtained, what else was seen on the way, which intermediate
readings were wrong, and where the two documents do not agree.

**Labels used throughout.** `OBSERVED` · `INFERRED` · `UNKNOWN` · `NOT TESTED` · `CORRECTED` ·
`TOOLING / HARNESS ISSUE` · `RUNTIME ANOMALY` · `FOLLOW-UP` · `DISCREPANCY` ·
`NOT RECOVERABLE FROM AVAILABLE ARTIFACTS`.

**Evidence sources used for this document**

| Source | Used for |
|---|---|
| `data/2026-08-28/market_depth_raw_20260828.jsonl.gz` (313.9 MB) | Tier-0 depth verification, reconnect verification, HEADER/EOF |
| `data/f10b_timeline_20260828.jsonl` (1293 samples, 3 meta, 2 event) | coverage, envelopes, `delivering_legs` history |
| `data/f10b_recorder.log` (9263 lines) | reconnects, dispatch plans, teardown, anomalies |
| `data/f10b_watcher.log` | watcher console classification |
| `data/f10b_start_time.txt` | recorder start wall clock |
| `data/health.json` | final published health payload |
| `data/reprocess.log` | Tier-2 rebuild |
| `openalgo/log/errors.jsonl` | broker-side TBT refusals (read-only) |
| `Documents/F10_LIVE_VALIDATION.md` | the runbook actually followed |
| `plans/Plan_002_...md` §5, §22.13 | objective, forks, thresholds, checklist |
| `Documents/CHANGELOG.md` | F10A and F10B entries |
| `git log` / `git show` | checkpoints and file inventory |

---

## 2. F10B objective and gate

From Plan_002 §22.13 and §5 (D18).

- **D18 was the target.** "Perf and RSS at true scale — up to 15 legs at 50-level plus the hybrid
  remainder — have never been measured." P10-E measured `<=5` NFO @50 plus ~120 SENSEX @5, so the
  number D18 asks for did not exist.
- **True-scale validation was required.** The target condition is up to 15 premium legs at 50-level
  *plus* the standard-depth remainder, running together.
- **The broker ceiling above 15 was deliberately not to be probed** — F24 = A: "We ARE measuring:
  behaviour while operating at configured budget = 15. We are NOT measuring: broker's maximum
  capacity > 15."
- **Reconnect restoration could only be observed naturally** — F23 = A: a forced reconnect
  "introduces an avoidable risk to the very live run we're trying to measure."
- **The framework had to be genuinely enabled** — F22 = A: shadow mode "cannot demonstrate the
  actual subscription/load behaviour".
- **Evidence standard** — F26 = A: a dated document in `Documents/patches/` separating
  OBSERVED / INFERRED / UNKNOWN.
- **Binding limits, recorded in §22.13.1:** no 16th premium subscription, no forced reconnect, no
  deliberate broker stress, no unsubscribe experimentation, no arbitrary depth experiments, no
  production-architecture change during the run, no allocator-rule change, no F7/F8 behaviour change
  because a live observation looks interesting. "If something unexpected happens:
  OBSERVE / RECORD / DO NOT IMPROVISE."

**Hard gate (runbook §A).** `--preflight` must show `NIFTY/NFO -> 50`. If NIFTY came back 5, the run
could not measure 15 legs @50 and the session was to be stopped rather than reported as a
measurement.

---

## 3. Starting state / pre-F10B checkpoint

| Item | State | Evidence |
|---|---|---|
| HEAD before F10B | `77bd786` | `git log` |
| Branch | `main` | `git rev-parse --abbrev-ref HEAD` |
| F10A | COMPLETE 2026-08-27, committed and pushed | §22.13.3 all ticked; `git show 77bd786` |
| Framework in committed config | **disabled** (`config.yaml:173 enabled: false`) | `git show 77bd786:...config.yaml` and current file |
| Code changes made for F10B | **none** | `18e9dd6` touches three documents only |
| `config_hash` | `sha256:8a48bcdd4fca933d1dbc85bd9a5c1dc055403392da0afeb22e629af550a1468b` | HEADER of the raw log, and all 1293 timeline samples |
| Broker contact during F10A | none | §22.13.4 |
| Untracked runtime dirs | `../db/`, `../log/` — pre-existing, untouched | `git status` |
| Pre-existing credential issue | a tracked 66-character `openalgo.api_key` in `config.yaml`, present on `origin/main` | **UNRELATED to F10 — separate security task, deliberately not addressed here** |

F10A shipped six files (1295 insertions):
`Documents/ARCHITECTURE.md`, `Documents/CHANGELOG.md`, `Documents/F10_LIVE_VALIDATION.md`,
`plans/Plan_002_market_depth_framework_implementation.md`, `tests/test_f10_live_monitor.py`,
`tools/validation/f10_live_monitor.py`.

Commits `c2b1704` and `6ef0e90` (FYERS HSM auth timeout / FD leak; depth-service auth guard) sit
**after** `77bd786` in history and are **not** F10B work. They are not attributed to F10B anywhere
in this document.

---

## 4. F10A preparation

### 4.1 What F10A introduced

| File | What it is |
|---|---|
| `tools/validation/f10_live_monitor.py` (529 lines) | Read-only watcher: samples `health.json`, appends a JSONL timeline, applies the F25 rules with a 3-sample sustain, renders the F26 evidence skeleton |
| `tests/test_f10_live_monitor.py` (364 lines) | 36 offline tests over synthetic health snapshots, including two source-level guards |
| `Documents/F10_LIVE_VALIDATION.md` (163 lines) | The F10B runbook |
| `plans/Plan_002...md` §22.13 (+135) | Forks F22-F26, threshold derivation, both checklists |
| `Documents/ARCHITECTURE.md` (+47), `Documents/CHANGELOG.md` (+59) | living docs |

The decisive F10A act was an **instrumentation audit performed before writing anything**, whose
result was *do not build a monitoring system*: `health.json` already publishes the three queue
depths, the three drop counters, `degraded_level`, `cycle_ms_p50` / `cycle_ms_max`, `rss_mb`,
`active_contracts`, `actual_depth`, `restart_count`, the framework planning view
(`processor.py:618`) and the FEED execution view (`websocket_client.py:780-793`). Only a timeline,
a classifier and an evidence skeleton were missing.

### 4.2 F10A verification

Recorded in §22.13.3 / §22.13.6 and the CHANGELOG. `OBSERVED` results carried forward from the F10A
record; commands not re-executed for this document:

| Check | Result | What it established |
|---|---|---|
| Full test suite, run **twice** | **1504 passed** each run (1468 existing + 36 new), no flakes | the watcher does not perturb the suite and is not flaky |
| `--validate-config` with `enabled: false` and `enabled: true` | both exit 0 | a framework misconfiguration surfaces offline, not at the open |
| `compute_config_hash` with the flag on vs off | byte-identical | the framework block is outside the hashed scope (`config.py:108-118`), so the session stays comparable with every prior session |
| `git diff --check` | clean | no whitespace damage |
| Watcher source audit | `os.kill`, `SIGTERM`, `SIGINT`, `terminate(`, `taskkill` asserted **absent** | aborting is the operator's act; the tool has no kill path |
| Watcher FD/thread/lock audit | one appended file handle under `with`, no thread, no lock, no socket, no recorder import | the watcher cannot perturb the measurement |
| Recorder runtime files | none modified | F10 is a measurement phase |
| Committed config | framework still **disabled** | F10A does not go live |

**Exact shell syntax for the F10A checks is `NOT RECOVERABLE FROM AVAILABLE ARTIFACTS`** — the
results are recorded in §22.13.3, §22.13.6 and the CHANGELOG, but the invocations themselves were
not preserved in a file. The operations are named above; they have not been reconstructed as
verbatim commands.

---

## 5. F10B preflight gate

| Check | Result | Evidence | Status |
|---|---|---|---|
| `--preflight` depth capability | `NIFTY/NFO -> 50`, `SENSEX/BFO -> 5` | recorded in §22.13.5; independently corroborated by `actual_depth = {"NIFTY": 50, "SENSEX": 5}` in **all 1293** timeline samples and in the final `health.json` | **HARD GATE PASSED** |
| `--validate-config` with `enabled: true` | exit 0 | §22.13.5 | OBSERVED |
| `config_hash` after the flip | unchanged | one distinct value across 1293 samples and the Tier-0 HEADER | OBSERVED |
| Framework enabled before activation | `false` in the committed config | `config.yaml:173` at `77bd786` | OBSERVED |
| Disk free | sufficient; 10.3 GB free at teardown | §11 / §10 Scenario H | OBSERVED |
| Recorder state at start | mid-day start, ATM re-seeded via REST | `10:12:06 mid-day restart in record window — seeding ATM via REST quotes` | OBSERVED |
| WebSocket | connected at 10:12:06 | `[Feed] websocket: Websocket connected` | OBSERVED |
| Chain resolution | NIFTY expiry 01-SEP-26, step 50, 231 strikes / 462 contracts; SENSEX expiry 03-SEP-26, step 100, 170 strikes / 340 contracts | recorder log 10:12:05-10:12:06 | OBSERVED |
| ATM seeding | NIFTY spot 24155.45 (window ±500, 20 strikes); SENSEX spot 77252.61 (window ±3000, 60 strikes) | recorder log 10:12:06 | OBSERVED |

**Why `SENSEX/BFO -> 5` was expected and is not a failure.** True 50-level is FYERS TBT, restricted
to NSE/NFO. SENSEX trades on BFO, which has no TBT tier, so it degrades to the 5-level book by
design (CLAUDE.md, "Depth Reality"). The framework confirms this at runtime: `eligible_underlyings`
in the final `health.json` is `["NIFTY"]` — SENSEX is never a premium candidate. The gate is about
NIFTY, and NIFTY reported 50.

---

## 6. Activation procedure

The single change, `config.yaml` line 173:

```yaml
market_depth_framework:
  enabled: false   ->   enabled: true
```

`OBSERVED` properties:

- Only that flag was changed. `git diff --stat config.yaml` is **empty** against HEAD today, so the
  file was restored exactly.
- `config_hash` did not move: `sha256:8a48bcdd...1468b` in the Tier-0 HEADER and in every sample.
- The framework came up at the intended budget:
  `10:12:06 framework mode ON — the adapter owns option subscriptions (premium budget 15)`.
- `effective_budget` was `15` in **all 1293** samples; no other value ever appeared.
- The flip was temporary and was reverted at teardown (§10 Scenario G).

**`TOOLING / HARNESS ISSUE` recorded during the revert.** The edit and the revert were applied with
`sed -i`, which rewrote the file's CRLF line endings to LF. `git status` then showed `config.yaml`
as modified while `git diff` showed no content change. Resolved with `git checkout -- config.yaml`,
after which the file is byte-identical to HEAD. This is a tooling artifact of editing a CRLF file on
Windows with a POSIX tool, not a recorder or framework defect. `FOLLOW-UP`: prefer an editor that
preserves line endings for the enable/disable flip.

---

## 7. Monitoring architecture

### 7.1 Recorder

One process, four workers, started 10:12:01 IST (`data/f10b_start_time.txt`), pipeline up at
10:12:06 (`pipeline started: 4 workers (raw · db · processor · feed)`). Outputs:

| Artifact | Final size | Note |
|---|---|---|
| `data/2026-08-28/market_depth_raw_20260828.jsonl.gz` | 313.9 MB | Tier 0, lossless |
| `data/2026-08-28/market_depth_live_20260828.db` | 552.0 MB | Tier 1, after WAL checkpoint |
| `data/2026-08-28/market_depth_analytics_20260828.duckdb` | 1871.8 MB | Tier 2, rebuilt offline |
| `data/f10b_recorder.log` | 9263 lines | stdout/stderr to file, never a PIPE |

### 7.2 Timeline watcher

`tools/validation/f10_live_monitor.py`, 15.0 s cadence, source `data/health.json`, append-only JSONL
timeline at `data/f10b_timeline_20260828.jsonl`, console mirror at `data/f10b_watcher.log`.

Thresholds actually in force, read from the timeline `meta` rows (not from documentation):

```json
{"cycle_ms_hard": 500.0, "cycle_ms_soft": 30.0,
 "db_crit": 45000.0, "db_warn": 35000.0,
 "proc_crit": 45000.0, "proc_warn": 35000.0,
 "raw_crit": 90000.0, "raw_warn": 70000.0,
 "rss_mb_hard": 2048.0, "rss_mb_soft": 500.0,
 "sustain": 3, "interval": 15.0}
```

**What the watcher can detect:** anything published to `health.json` at a 15 s granularity —
queue depths, drop counters, `degraded_level`, cycle percentiles, RSS, `premium_legs` vs
`effective_budget`, `delivering_legs`, `websocket_status`, `restart_count`, `plan_failures`,
and the disappearance of the framework block.

**What it cannot detect** (`OBSERVED` limitations, all of which mattered on the day):

1. Anything that lives for less than one sampling interval. The single `refused=2` /
   `premium=13/15` dispatch at 11:28:58 (§10 Scenario F) lasted under one second and never
   appeared in a sample.
2. Anything the recorder does not publish. Per-plan `refused` counts are logged, not published;
   `health.json` exposes `plan_failures`, and a refusal is not a plan failure.
3. Anything downstream of OpenAlgo. The broker's TBT refusals appear only in OpenAlgo's own
   `log/errors.jsonl`.
4. Depth *content*. `delivering_legs` counts legs seen delivering; only Tier 0 shows the actual
   book shape per symbol.

### 7.3 Persistent external monitor

A separate poll-and-report monitor watched the recorder log for: recorder errors, genuine
`failed=[1-9]`, genuine `refused=[1-9]`, corrupt/dropped conditions, reconnect/disconnect, DEGRADED,
watcher-classified events, teardown, and process exit.

**`TOOLING / HARNESS ISSUE` — monitor filter false positive.** The first filter matched the bare
words `failed` / `refused`, which match every normal `sent=0 failed=0 refused=0` line, i.e. all 4574
of them. Corrected to `failed=[1-9]` / `refused=[1-9]`. This is recorded because the corrected
filter is what makes the 11:28:58 `refused=2` line findable at all, and because an uncorrected
filter would have buried it in 4574 false positives.

**`TOOLING / HARNESS ISSUE` — stale traceback.** A disk-space monitor grepped the whole of
`data/reprocess.log` and reported a `KeyboardInterrupt` traceback that belonged to an **earlier,
unrelated** run. The file is append-only across runs and still contains that older traceback above
the `=== reprocess start 2026-08-28T15:35:10 ===` banner. Corrected by scoping the grep to the
current run: `sed -n '/reprocess start 2026-08-28T15:35/,$p'`. No F10B failure existed.

**`TOOLING / HARNESS ISSUE` — scratch files written into the project.** The monitor initially wrote
state files `data/.lastrp` and `data/.prevrp` inside the project. They were removed and the monitor
re-armed with its state in the session scratchpad directory. No recorder artifact was affected.

---

## 8. Monitoring interruptions and sampling coverage

Measured directly from `data/f10b_timeline_20260828.jsonl`, not from recollection.

| Measure | Value |
|---|---|
| Samples | 1293 |
| First sample | 10:12:31 IST |
| Last sample | 15:37:05 IST |
| Watcher `meta` rows (process starts) | **3** — 10:12:31, 10:42:05, 11:05:47 IST |
| Gaps > 20 s | **2** |
| Gap 1 | **62.2 s**, 10:41:03 -> 10:42:05 |
| Gap 2 | **40.4 s**, 11:05:07 -> 11:05:47 |
| Recorder restarts during the watch | **0** (`restart_count = 0` in every sample; exactly one HEADER and one EOF in the raw log) |

**`CORRECTED` (in-session).** An in-session report of a "~20 minute sampling gap" was wrong. The
measured gaps are 62.2 s and 40.4 s. The second watcher ran longer than its termination notice
implied.

**`DISCREPANCY` D1 against the formal evidence.**
`f10_live_validation_20260828.md` states: *"One 62 s gap ending 10:42:05, from a watcher restart.
Coverage is otherwise continuous 10:12:31-15:37:05."* Plan_002 §22.13.5 likewise says *"one 62 s
gap"*. The timeline contains **two** gaps and **three** watcher starts. The 40.4 s gap ending
11:05:47 is unrecorded in both. Resolved from the underlying artifact (the `meta` rows and the
sample timestamps), which is the stronger evidence. See §24.

**Effect on the result: none.** Both gaps precede 11:06; the 15-leg measurement window is
13:56-14:37 and is covered by 160 consecutive samples with no gap. The recorder did not restart
during either interruption, so Tier 0 is continuous regardless of what the watcher was doing.

**`TOOLING / HARNESS ISSUE`.** The watcher processes were terminated by the agent harness's
background-task management, not by the operator and not by any recorder condition. Later waits were
moved to poll-and-break monitors to avoid it.

---

## 9. Live-session timeline

`Time | Event | Evidence source | Observation | Interpretation`

| Time (IST) | Event | Evidence source | Observation | Interpretation |
|---|---|---|---|---|
| 10:12:01 | Recorder start | `f10b_start_time.txt` | wall-clock start recorded | mid-day start, per runbook §C.1 |
| 10:12:05-06 | Chains resolved | recorder log | NIFTY 01-SEP-26 / 462 contracts; SENSEX 03-SEP-26 / 340 | REST path, before any WS dependency |
| 10:12:06 | Framework ON | recorder log | `premium budget 15` | F22=A active |
| 10:12:06 | WS connected, raw log opened, live store opened | recorder log | — | pipeline up |
| 10:12:06 | ATM seeded | recorder log | NIFTY 24155.45, SENSEX 77252.61 | mid-day recovery path exercised |
| 10:12:06-07 | Passes 1-2 | recorder log | `sent=40`, then `sent=120`, `premium=15/15` | initial subscription fan-out |
| 10:12:07 | **First broker refusal cluster** | `openalgo/log/errors.jsonl` | 4 records | broker-side, invisible to the framework |
| 10:12:31 | Watcher run 1 starts | timeline `meta` | thresholds recorded | — |
| 10:41:03 -> 10:42:05 | **Gap 1 (62.2 s)** | timeline | watcher run 2 starts | harness termination |
| 10:44:36 | **Reconnect 1** | recorder log | `ping/pong timed out` -> disconnect -> reissued 162 legs | natural |
| 11:05:07 -> 11:05:47 | **Gap 2 (40.4 s)** | timeline | watcher run 3 starts | harness termination |
| 11:10:03 | Health write failure 1 | recorder log | `PermissionError [WinError 5]` | transient, non-consecutive |
| 11:28:58 | **`refused=2`, `premium=13/15`** | recorder log pass 1084 | the only non-zero refusal the framework itself saw | see §10 Scenario F |
| 11:28:59 | Recovery | recorder log pass 1085 | `sent=2 refused=0 premium=15/15` | recovered within ~0.5 s |
| 11:28:59 | Refusal cluster (2 records) | `errors.jsonl` | **not** at a reconnect | see D3 |
| 12:29:33 | **Reconnect 2** | recorder log | reissued 172 legs | natural |
| 12:29:53-12:38:09 | `delivering_legs = 7` | timeline (34 samples) | 8.5 min | partial multi-connection state |
| 12:37:59 | **Reconnect 3** | recorder log | reissued 172 legs | natural |
| 13:35:11 | **Reconnect 4** | recorder log | reissued 172 legs | natural |
| **13:56:29** | **`delivering_legs` reaches 15** | timeline | start of the true-scale window | the D18 measurement begins |
| 14:14:03.813 | **Reconnect 5 — inside the window** | recorder log | `ping/pong timed out`; reissued 172 legs at 14:14:13.038 | natural, not forced |
| 14:14:15 | single sample at `delivering_legs = 0` | timeline | the only zero of the session | the reconnect seen from the sampler |
| 14:14:13.633 | **First 50-level packet after the reconnect** | Tier 0 | same 15 symbols | UNKNOWN #1 resolves here |
| 14:14:30-14:36:32 | back at 15 | timeline | — | restoration complete |
| **14:36:32** | window ends | timeline | 40.0 min, 160 samples at 15 | — |
| 14:36:33 | **Reconnect 6** | recorder log | reissued 172 legs | natural |
| 14:51:03 | single sample at `delivering_legs = 3` | timeline | — | transient |
| 15:24:50 | Health write failure 2 | recorder log | `PermissionError [WinError 5]` | transient, non-consecutive |
| 15:35:00.120 | **Teardown** | recorder log | `teardown time reached (session_end + grace) — draining pipeline` | scheduled, `session_end` + grace |
| 15:35:00.136 | Feed socket closed | recorder log | — | drain order per `main.py:450-471` |
| 15:35:10.148 | `SQLiteLiveWriter did not join within 10s` | recorder log | exactly `_JOIN_TIMEOUT_SEC` | see Scenario G |
| 15:35:10.154 | Reprocess child launched | recorder log | `--replay --catchup`, output to log file | FD hygiene: not a PIPE |
| 15:56:38.827 | Reprocess child `rc=0` | recorder log | 2 stores rebuilt | — |
| 15:56:38.851 | `orchestrator exit rc=0 restarts=0` | recorder log | clean exit | session complete |

Timestamps from `health.json` samples (`at`, float epoch), recorder log lines (millisecond wall
clock), Tier-0 records (`recv_ts`) and OpenAlgo error records (`ts`, whole seconds) are kept
distinct above and are never mixed within a single derived figure.

---

## 10. Scenario matrix

### Scenario A — Normal framework operation

**Expected:** framework active, plans execute, no plan failures, no drops, stable queues.

**`OBSERVED`:** `framework_present = true` in all 1293 samples. 4603 planning passes published,
4573 executed, 30 superseded (`plan_mailbox: published 4603, taken 4573, superseded 30, pending 0`).
`plan_failures = 0` and `failures = 0` for the whole session. `last_error: null`.
`degraded_level = 0` in every sample. Queue peaks over the whole session: proc 7, db 2, raw 37 —
against criticals of 45,000 / 45,000 / 90,000. `raw_dropped_total`, `proc_dropped_total`,
`db_rows_dropped_total` all **0** at every sample and at the end. `restart_count = 0`.
2,192,685 observations consumed.

**Result: PASS.**

### Scenario B — Full premium budget

**Expected:** premium budget 15; the framework maintains 15 premium assignments.

**`OBSERVED`:** `effective_budget = 15` and `premium_legs = 15` in **all 1293** samples. In the
recorder log, `premium=15/15` appears **4574** times and `premium=13/15` **once** (11:28:58).
`desired_legs` grew 160 -> 172 as the window opened; `claimed_wire_symbols = 172` at the end.

**Critical distinction, and the central lesson of the day.** `premium_legs = 15` means the framework
holds 15 premium assignments and dispatched them successfully to OpenAlgo. It is **not** proof of
15 delivered 50-level streams. `delivering_legs` (packet-derived, `websocket_client.py:791`) shows
what actually arrived, and it was 15 for only 160 of 1293 samples.

**Result: PASS as an allocation claim; NOT sufficient as delivery evidence.**

### Scenario C — True-scale delivery

**Expected:** 15 distinct premium legs actually delivering 50-level, plus the hybrid remainder.

**`OBSERVED`, verified against Tier 0 (§12):** over 13:56:29-14:36:32 the raw log contains
**401,881 depth records** across **172 distinct symbols**, of which **exactly 15 reached a
(50, 50) book** and never anything less on any record in the window. The 15:

```
NIFTY01SEP2623900CE:50
NIFTY01SEP2623950CE:50   NIFTY01SEP2623950PE:50
NIFTY01SEP2624000CE:50   NIFTY01SEP2624000PE:50
NIFTY01SEP2624050CE:50   NIFTY01SEP2624050PE:50
NIFTY01SEP2624100CE:50   NIFTY01SEP2624100PE:50
NIFTY01SEP2624150CE:50   NIFTY01SEP2624150PE:50
NIFTY01SEP2624200CE:50   NIFTY01SEP2624200PE:50
NIFTY01SEP2624250CE:50   NIFTY01SEP2624250PE:50
```

Near-ATM 01-SEP-2026 NIFTY, strikes 23900-24250. The set is **asymmetric**: 23900**CE** is premium,
23900**PE** is not — 15 is an odd number and the priority policy ranks individual legs, not pairs.
The `:50` suffix on the wire symbol is how the premium tier is requested.

Remainder in the same window: 135 symbols at (5, 5), 4 more reaching 5 on the buy side
((5,4) x1, (5,2) x3) — **139 symbols with a 5-deep book**, matching the formal evidence's "139
carried 5 levels" — plus 18 shallower/partial symbols (4,5)/(3,2)/(2,2)/(2,1)/(1,2)/(1,1).

**Duration: 40.0 minutes**, 160 samples.

**Result: PASS. This is the measurement D18 required.**

### Scenario D — Performance under true-scale load

**`OBSERVED` inside the 15-leg window (n = 160):**

| Metric | min | median | max | Threshold |
|---|---|---|---|---|
| `cycle_ms_p50` | 14.5 | **17.2** | 19.0 | soft 30, hard 500 |
| `cycle_ms_max` | 32.3 | 39.2 | **44.1** | — |
| `rss_mb` | 92.7 | 97.1 | **97.7** | soft 500, hard 2048 |
| `proc_queue_size` | 0 | — | **4** | crit 45,000 |
| `db_queue_size` | 0 | — | **2** | crit 45,000 |
| `raw_file_queue_size` | 0 | — | **37** | crit 90,000 |
| `degraded_level` | 0 | 0 | **0** | crit 2 |
| `active_contracts` / `desired_legs` | 172 | 172 | 172 | — |
| all three drop counters | 0 | 0 | **0** | any > 0 = instant abort (raw) |

**Result: PASS, with wide margin.** The largest queue occupancy observed anywhere in the window is
37 records against a 90,000 cap — 0.04%.

### Scenario E — Natural reconnect

**`NOT a forced test.` F23 = A forbids forcing one.**

**`OBSERVED`:** six disconnect/reconnect cycles, all natural, all with the same proximate cause in
the log — `websocket: ping/pong timed out - goodbye` (6 occurrences) followed by
`feed disconnected — reconnecting in 3.0s (attempt 1)`:

| # | Disconnect | Reissue | Legs reissued | Framework result |
|---|---|---|---|---|
| 1 | 10:44:36.024 | 10:44:39.059 | 162 | `failed=0 refused=0` |
| 2 | 12:29:33.152 | 12:29:39.917 | 172 | `failed=0 refused=0` |
| 3 | 12:37:59.419 | 12:38:10.523 | 172 | `failed=0 refused=0` |
| 4 | 13:35:11.806 | 13:35:42.244 | 172 | `failed=0 refused=0` |
| 5 | **14:14:03.813** | 14:14:13.038 | 172 | `failed=0 refused=0` |
| 6 | 14:36:33.595 | 14:36:43.629 | 172 | `failed=0 refused=0` |

Reconnect 5 fell **inside** the 15-leg window. Tier-0 verification across 14:13:50-14:15:30:

- 50-level symbols before the disconnect: **15**
- 50-level symbols after: **15**
- **identical set** (`set(pre) == set(post)` -> `True`)
- first 50-level packet after the disconnect at **14:14:13.633** = **+9.8 s** measured from the
  disconnect log line at 14:14:03.813, or **+10.6 s** measured from the 14:14:03.0 second boundary
  used in the formal evidence. Same packet; different reference epoch. Both are stated here to
  avoid the appearance of a contradiction.

**Result: UNKNOWN #1 RESOLVED by natural observation.** See §13 for the boundary of that claim.

### Scenario F — Broker refusal behaviour

**`OBSERVED` in `openalgo/log/errors.jsonl`:** 30 records matching
`symbol count exceeds limit: 5, please unsubscribe few symbols before resuming the channel or
subscribing additional symbols`.

Two loggers emit the same event: `fyers_tbt_websocket` (15) and `fyers_websocket_adapter` (15).
**The 30 records are therefore 15 logical broker refusals, each recorded twice.** The formal
evidence's "30" counts records; both numbers are correct for what they count, and this document
states which is which.

Clusters by minute:

| Minute | Records | Logical events | Coincides with |
|---|---|---|---|
| 10:12 | 4 | 2 | initial subscription fan-out |
| 10:44 | 4 | 2 | reconnect 1 |
| **11:28** | **2** | **1** | **a `window_change`, NOT a reconnect** |
| 12:29 | 4 | 2 | reconnect 2 |
| 12:38 | 4 | 2 | reconnect 3 |
| 13:35 | 4 | 2 | reconnect 4 |
| 14:14 | 4 | 2 | reconnect 5 |
| 14:36 | 4 | 2 | reconnect 6 |

First 10:12:07, last 14:36:44.

**Framework counters versus broker errors.**

| Layer | What it reported |
|---|---|
| Framework (health) | `plan_failures = 0`, `failures = 0`, `pending_rejections = 0`, `last_error: null` |
| Framework (per-plan log) | `failed=0` on **all 4574** dispatch lines; `refused=0` on **4573** of them |
| Framework (the exception) | pass **1084**, 11:28:58.570: `sent=6 failed=0 refused=2 skipped=157 premium=13/15` |
| OpenAlgo/FYERS | 30 records / 15 refusal events |

**`DISCREPANCY` D2 against the formal evidence.** `f10_live_validation_20260828.md` states
`failed=0 refused=0` as a whole-session fact and asserts *"The framework never saw the refusals."*
One dispatch — pass 1084 — did see two, and `premium_legs` momentarily fell to 13/15. Pass 1085
recovered to `sent=2 refused=0 premium=15/15` about 0.5 s later. The event is invisible in the
timeline because it lived well under the 15 s sampling interval. The claim is **true for 4573 of
4574 dispatches and false as an absolute**. See §24.

**`DISCREPANCY` D3 against the formal evidence.** INFERRED item 3 states the refusals *"never"* fall
between the connect and reconnect timestamps. The 11:28:59 cluster does exactly that: it follows the
`window_change` at pass 1084, at a moment with no disconnect anywhere near it (nearest reconnects:
10:44 and 12:29). The refined `OBSERVED` statement is: **every refusal cluster coincides with a
moment at which new premium legs were being requested** — either a (re)connect fan-out or a
window-change that moved the premium set. That is a weaker and better-supported claim than "only at
reconnects". See §24.

**Why the framework counters were not sufficient.** OpenAlgo accepted the subscription requests, so
the framework's dispatch succeeded; the broker refused downstream and reported it into OpenAlgo's own
log. `delivering_legs` sat at 5 for **1097 of 1293 samples (274.2 min of the 361 observed)**. A
report built from framework counters alone would have described a fully successful 15-leg session
all day.

**Result: the single most important operational finding of F10B.**

### Scenario G — Teardown

**`OBSERVED` sequence:**

| Time | Line |
|---|---|
| 15:35:00.120 | `teardown time reached (session_end + grace) — draining pipeline` |
| 15:35:00.136 | `feed socket closed (code=None reason=None)` |
| 15:35:10.148 | `ERROR ... worker SQLiteLiveWriter did not join within 10s` |
| 15:35:10.154 | `reprocess: launching python -m market_depth_recorder --replay --catchup` |
| 15:56:38.827 | `reprocess: child exited rc=0` |
| 15:56:38.851 | `orchestrator exit rc=0 restarts=0` |

- **EOF marker written.** The last line of the raw log is
  `{"meta_type":"EOF","record_count":3043790,"close_timestamp":1787911500}`. The file contains
  **exactly one HEADER and one EOF** — no interior restart markers, corroborating
  `restart_count = 0`.
- **`RUNTIME ANOMALY` — the 10 s join.** The error fired at exactly `_JOIN_TIMEOUT_SEC` (10.0 s,
  `main.py:64`, used at `main.py:467`). `db_queue_size` was **0**, so this is not unwritten rows; it
  is close/checkpoint cost on a large SQLite database. The thread **did** finish: the live store
  closed cleanly at 552.0 MiB after its WAL checkpoint. `FOLLOW-UP`: the 10 s budget may be too small
  for a full-size trading day. **Not changed** — changing it during or immediately after the run
  would be improvising.
- **`CORRECTED` — the apparent 21-minute hang.** The recorder stayed alive from 15:35:10 to
  15:56:38 after teardown. This was read in-session as a possible hang. It is **by design**:
  `_maybe_reprocess` (`main.py:535-556`) calls `self._reprocess_launcher(...)`, which **waits on the
  child** — the FD-hygiene rule that a subprocess writes to a log file and is `.wait()`-reaped. The
  launch is itself proof the EOF was flushed, because `_maybe_reprocess` is gated on `_clean_eof()`
  (`main.py:557-561`), which returns `raw_writer.eof_written`.
- **`CORRECTED` — the "578 MB -> 552 MB WAL checkpoint" reading.** An in-session note read the live
  store as shrinking from 578 MB to 552 MB across the checkpoint. The file on disk is
  **578,785,280 bytes = 552.0 MiB** — one unchanged file described in two units. There is no
  measured size reduction; only the closed size (552.0 MiB) is `OBSERVED`. See §16.6 note.
- **Config restored.** `enabled` back to `false`; `git diff --stat config.yaml` empty.

**Result: PASS with one recorded anomaly.**

### Scenario H — Disk and reprocess behaviour

**`OBSERVED`:** the child rebuilt **two** analytical stores, not one:

| Store | Rows | Batches | Wall time |
|---|---|---|---|
| `market_depth_analytics_20260707.duckdb` | — | — | skipped, up to date |
| `market_depth_analytics_20260714.duckdb` | 2,805,069 | 30 | 15:35:12 -> 15:37:39 |
| `market_depth_analytics_20260828.duckdb` | 12,835,490 | 130 | 15:37:39 -> 15:56:38 |

Today's replay: `3,043,790 packets, 19,374 seconds, 12,835,490 rows, 0 corrupt lines`. The packet
count matches the EOF `record_count` exactly.

**`CORRECTED` — the disk projection.** An in-session projection of ~7-8 GB for the rebuild,
extrapolated from the 2026-07-07 ratio of ~25x, **was wrong**. Actual: **1871.8 MB from a 313.9 MB
raw ≈ 6x**. Free space was 10.3 GB at teardown and 9.4 GB at the time of writing, after both stores
had been produced. The projection is recorded because it was acted on during the session; it is
corrected because it was inaccurate.

**Result: PASS. The disk concern was real at the time and turned out to be unfounded.**

### Scenario I — Health-file write failures

**`RUNTIME ANOMALY`, 2 occurrences:**

| # | Time | Error |
|---|---|---|
| 1 | 11:10:03.162 | `failed to write health file ./market_depth_recorder/data/health.json` + traceback |
| 2 | 15:24:50.126 | same |

- Both are `PermissionError [WinError 5]` raised by `os.replace(tmp, path)` at `utils.py:134` — the
  atomic-swap step of `atomic_write`.
- The call site (`_write_health`, `main.py:479-482`) wraps the write in try/except, logs, and never
  crashes the loop. That is why the session continued unaffected.
- **Not consecutive** — 4 h 14 min apart — so the 3-sample sustain rule was never engaged, and no
  F25 criterion covers this condition in any case.
- Disk was not the cause: ample free space at the time.
- `INFERRED`, not proven: a transient Windows file lock, most plausibly the watcher reading
  `health.json` during the rename. **The cause was not instrumented and is not established.**
- No data loss: the health file is a status publication, not a data path. Two samples read slightly
  stale content; Tier 0, Tier 1 and the counters are unaffected.

**Result: recorded, no action taken, no abort criterion applicable.**

---

## 11. Performance results

| | P10-E baseline | F10B 5-leg baseline (n=1097) | **F10B 15-leg window (n=160)** |
|---|---|---|---|
| Premium legs delivering @50 | <= 5 | 5 | **15** |
| Standard-depth legs | ~120 SENSEX @5 | — | **139** |
| Total contracts | ~125 | 160-172 | **172** |
| `cycle_ms_p50` | ~22 | 17.0 median (11.8-22.1) | **17.2 median (14.5-19.0)** |
| `cycle_ms_max` | 43-60 | 41.6 median, 89.0 peak | **39.2 median, 44.1 peak** |
| `rss_mb` | 52-58 | 95.3 median, 105.3 peak | **97.1 median, 97.7 peak** |
| proc / db / raw queue peak | — | 7 / 2 / 37 (whole session) | **4 / 2 / 37** |
| Drops (raw / proc / db) | 0 | 0 | **0** |
| `degraded_level` | 0 | 0 | **0** |
| Duration | — | 274.2 min | **40.0 min** |

**What this proves.** Tripling the premium-leg count relative to the P10-E measurement, while adding
~47 contracts, produced **no observed cycle-time degradation during the 40-minute true-scale
window**: p50 is flat at ~17 ms and the *maximum* is lower inside the window (44.1 ms peak) than
outside it (89.0 ms peak). RSS reached 97.7 MB against a 500 MB soft target and a 2048 MB host hard
limit.

**What this does not prove.** It says nothing about budgets above 15, nothing about sessions longer
than one trading day, and nothing about a 15-leg condition sustained for hours rather than 40
minutes. The 15-leg state existed for 40 of 361 observed minutes and the measurement is of that
window.

---

## 12. Tier-0 verification methodology

This is the section that separates F10B from a counter-reading exercise. The authoritative proof of
15 full-depth legs came from the **raw delivered packets**, not from allocation state, not from
subscription acknowledgement, and not from `delivering_legs` alone.

**Why it was necessary.** Scenario F establishes that OpenAlgo accepted every subscription while the
broker refused downstream. Every layer above Tier 0 was therefore reporting success at moments when
delivery was not happening. Only the bytes that actually arrived settle the question.

**The verification, as executed**

```text
Purpose:       prove that 15 distinct symbols carried a full 50x50 book throughout the window
Input:         data/2026-08-28/market_depth_raw_20260828.jsonl.gz  (313.9 MB, 3,043,790 records)
Operation:
  1. stream the gzip line by line (never load it into memory)
  2. cheap prefilter on the raw line for '"Depth"' before json.loads
  3. keep records with data_type == 'Depth'
  4. take t = recv_ts (fall back to timestamp)
  5. filter W0 <= t <= W1 with W0/W1 = 13:56:29 / 14:36:32 IST as epoch floats
  6. per symbol: count records, and track max(len(depth['buy'])), max(len(depth['sell']))
  7. classify symbols by their (max_buy, max_sell) pair
Result:        401,881 depth records; 172 distinct symbols
               (50,50) -> 15 symbols        <- the premium legs
               (5,5)   -> 135 symbols
               (5,4) x1, (5,2) x3           -> 139 symbols with a 5-deep book
               (4,5), (3,2), (2,2) x4, (2,1) x3, (1,2), (1,1) x8 -> 18 shallow/partial
Interpretation: exactly 15 legs delivered the 50-level book, concurrently, for the whole window
Evidence strength: HIGHEST — delivered packets, per symbol, per record
```

Corroborating facts read from the same file:

- HEADER `config_hash` = `sha256:8a48bcdd...1468b`, identical to all 1293 timeline samples.
- `session_date = "2026-08-28"`, `schema_version = 1`, `underlyings = ["NIFTY","SENSEX"]`,
  `open_timestamp = 1787892126`.
- Exactly one HEADER and one EOF; `record_count = 3,043,790`, matching the replay packet count
  exactly, with `0 corrupt lines`.

**Reconciliation with the formal evidence (not a contradiction).** The formal document reports
**401,716** records "across 13:56:30-14:36:30"; this document reports **401,881** across
13:56:29-14:36:32, the exact sample boundaries of the 15-leg run. The 165-record difference is the
~3.5 s of boundary. Both counts are correct for their stated window; the symbol classification —
15 at (50,50), 139 with a 5-deep book, 172 total — is **identical** under both.

---

## 13. Reconnect-depth-restoration verification methodology

```text
Purpose:       determine whether a naturally occurring reconnect restored 50-level delivery,
               and to the same symbols
Reference:     disconnect logged 14:14:03.813 ("ping/pong timed out" -> reconnect in 3.0s)
               reissue logged   14:14:13.038 ("reissued 172 leg(s) failed=0 refused=0")
Input:         the same Tier-0 stream, filtered to 14:13:50 .. 14:15:30 IST
Operation:
  1. keep Depth records with len(buy) >= 50 and len(sell) >= 50
  2. partition on t < 14:14:03.813 (pre) vs t >= (post)
  3. compare the two symbol sets; record the earliest post-reconnect 50-level packet time
Result:        pre  = 15 distinct symbols
               post = 15 distinct symbols
               set(pre) == set(post)  ->  True
               earliest post packet   ->  14:14:13.633
Latency:       +9.8 s from the disconnect log line (14:14:03.813)
               +10.6 s from the 14:14:03.0 second boundary (the figure in the formal evidence)
Interpretation: the identical premium set resumed full-depth delivery within ~10 s
Evidence strength: HIGHEST — delivered packets, both sides of the event
```

**Boundary of the claim.** This was a **natural** reconnect caused by a ping/pong timeout, observed
under F23 = A, never forced. It resolves the question *"does a naturally occurring reconnect, under
this configuration and in this session, restore the observed premium depth?"* — answer: **yes, to
the same 15 symbols, in about 10 seconds.** It does **not** prove restoration under every reconnect
failure mode, under a broker-side session drop, at a different time of day, or with a different
premium set. Five other natural reconnects occurred and were not individually depth-verified in
Tier 0; only reconnect 5 fell inside the 15-leg window where a restoration to 15 is observable at
all.

---

## 14. Broker-refusal analysis

**How the refusals were found.** Not by the framework and not by the watcher — neither can see them.
They were found by reading OpenAlgo's own structured error log, `openalgo/log/errors.jsonl`, which
is outside this project and was opened **read-only**.

```text
Purpose:       determine whether the broker refused subscriptions the framework believed succeeded
Input:         openalgo/log/errors.jsonl (one JSON object per line;
                                          keys: ts, level, logger, module, file, message)
Operation:     json.loads each line; match 'symbol count exceeds limit';
               group by r['ts'][:16] (minute); tally by r['logger']
Result:        30 records; 15 from fyers_tbt_websocket, 15 from fyers_websocket_adapter
               = 15 logical refusals, double-logged
               clusters: 10:12 x4, 10:44 x4, 11:28 x2, 12:29 x4, 12:38 x4,
                         13:35 x4, 14:14 x4, 14:36 x4
               first 10:12:07, last 14:36:44
Message:       "TBT error: symbol count exceeds limit: 5, please unsubscribe few symbols
                before resuming the channel or subscribing additional symbols"
Source file:   broker/fyers/streaming/fyers_websocket_adapter.py:683
Evidence strength: HIGH for the events; NONE for the internal mechanism
```

A second, empty `strategies/SS_Projects/log/errors.jsonl` exists (0 bytes) and contains nothing —
the recorder's own error channel logged no refusal, consistent with the framework never being told.

**Separation of claim strength:**

`OBSERVED`
- 30 refusal records exist, spanning 10:12:07 to 14:36:44.
- They are 15 logical events, each logged by two loggers.
- Every cluster coincides with a moment at which premium legs were being (re)requested: the initial
  fan-out, five of the six reconnects, and one `window_change` (11:28:58).
- Delivery fell to 5 legs for 1097 of 1293 samples.
- Delivery reached 15 legs for 160 samples, and 7 legs for 34.
- Exactly one framework dispatch reported a refusal (`refused=2`, pass 1084).
- The broker's message names a limit of **5**, matching the frozen FYERS TBT per-connection cap.

`INFERRED`
- The 5-leg plateau is the FYERS per-connection TBT cap of 5, not a framework fault. Rests on: the
  broker's own message text, `premium_legs = 15` held continuously, and delivery pinned at exactly 5.
- The 15-leg window is all three TBT connections carrying their 5 symbols at once; 7 is a partial
  intermediate. Rests on the frozen capability model (`tbt_budget = 15` = 3 x 5) and the observed
  5 / 7 / 15 plateaus. Nothing in this session instruments OpenAlgo's connection assignment.
- The refusals are a re-request-time effect rather than a steady-state one.

`UNKNOWN`
- The internal OpenAlgo/FYERS connection-allocation mechanics.
- **Why the 3-connection condition held for only 40 of 361 minutes.**
- Whether all 15 logical refusals share one causal path.
- Why 11:28 produced 1 logical refusal where every other cluster produced 2.

Note that 14:14 produced **both** a refusal cluster **and** full 50-level restoration, so a refusal
cluster does not by itself predict degraded delivery.

---

## 15. Issues, bugs and anomalies encountered

| # | Issue | Detected when | Evidence | Impact | Resolution | Class / follow-up |
|---|---|---|---|---|---|---|
| 1 | Monitor filter matched `failed=0` / `refused=0` | during the session | 4574 benign dispatch lines | noise; would have buried the real event | filter changed to `failed=[1-9]` / `refused=[1-9]` | `TOOLING / HARNESS ISSUE` |
| 2 | Watcher processes terminated by the agent harness | 10:41 and 11:05 | 3 `meta` rows; 2 gaps | 102.6 s of unsampled time, all before 11:06 | restarted; later waits moved to poll-and-break monitors | `TOOLING / HARNESS ISSUE` |
| 3 | Timeline sampling gaps | post-session analysis | 62.2 s + 40.4 s | none — outside the measurement window; recorder never restarted | recorded | `TOOLING / HARNESS ISSUE`; **`DISCREPANCY` D1** |
| 4 | Health-file write failures x2 | 11:10:03, 15:24:50 | `PermissionError [WinError 5]` at `utils.py:134` | none — caught, logged, loop continues; not consecutive | recorded, no action | `RUNTIME ANOMALY`; cause `INFERRED` only |
| 5 | `SQLiteLiveWriter did not join within 10s` | 15:35:10.148 | `main.py:467`, `_JOIN_TIMEOUT_SEC = 10.0` | none — `db_queue_size = 0`; thread finished; DB closed clean; `rc=0` | recorded, **not changed** | `RUNTIME ANOMALY`; `FOLLOW-UP`: join budget may be too small for a full day |
| 6 | Stale `KeyboardInterrupt` traceback reported as a failure | during reprocess | belongs to an earlier run, above the 15:35:10 banner in the append-only log | false alarm | grep scoped to the current run's banner | `TOOLING / HARNESS ISSUE` |
| 7 | Monitor scratch files written into the project | during the session | `data/.lastrp`, `data/.prevrp` | none | removed; state moved to the scratchpad | `TOOLING / HARNESS ISSUE` |
| 8 | `sed -i` rewrote `config.yaml` CRLF -> LF | at the revert | `git status` modified, `git diff` empty | none | `git checkout -- config.yaml` | `TOOLING / HARNESS ISSUE` |
| 9 | Broker refusals invisible to the framework | post-session cross-check | 30 records in OpenAlgo's log vs `plan_failures = 0` | **high** — counters alone would have reported a fully successful session | recorded as the central operational finding | **observability gap**, not a defect in either layer; `FOLLOW-UP` |
| 10 | One dispatch saw `refused=2`, `premium=13/15` | post-session log audit | pass 1084, 11:28:58.570 | none — recovered in ~0.5 s | recorded | `RUNTIME ANOMALY`; **`DISCREPANCY` D2** |
| 11 | Six feed disconnects (`ping/pong timed out`) | during the session | 6 x `websocket: ping/pong timed out - goodbye` | resubscription each time; one fell inside the measurement window and was turned into evidence | recorded | `RUNTIME ANOMALY`, external to this project; handled by the existing reconnect path |

**Classification note.** Items 1, 2, 3, 6, 7 and 8 are **test-harness/tooling issues** and say nothing
about the recorder. Item 9 is an **observability gap** spanning two systems. Items 4, 5, 10 and 11
are **runtime anomalies**, none of which affected the result. **No item in this table is a
demonstrated defect in the framework, the allocators, or the recorder pipeline.**

---

## 16. Corrections to earlier observations

Recorded in full, including the superseded readings, because the final result was produced by
re-checking the evidence rather than defending the first interpretation.

### 16.1 Correction 1 — sampling gap

- **Superseded (in-session):** "a ~20 minute sampling gap".
- **`CORRECTED`:** measured from the timeline, a **62.2 s** gap ending 10:42:05 — and, found while
  writing this document, a **second 40.4 s** gap ending 11:05:47.
- Evidence: sample timestamps and three `meta` rows.

### 16.2 Correction 2 — `delivering_legs`

- **Superseded (in-session):** delivery was 5 and the projection was that "D18 likely cannot close".
- **`CORRECTED`:** the histogram is `{0: 1, 3: 1, 5: 1097, 7: 34, 15: 160}` and a **40.0-minute
  window at 15** exists. D18 closes.
- Evidence: 1293 timeline samples, then Tier-0 confirmation.
- **This is the correction that changed the outcome of the phase.** It was found by measuring rather
  than by assuming.

### 16.3 Correction 3 — teardown

- **Superseded (in-session):** the recorder appeared hung for 21 minutes after teardown.
- **`CORRECTED`:** by design — `_maybe_reprocess` waits on the reprocess child
  (`main.py:535-556`), the FD-hygiene `.wait()`-reap. The launch is itself proof the EOF was
  flushed, since the call is gated on `_clean_eof()`.
- Evidence: `main.py:535-561`, and `rc=0` at 15:56:38.

### 16.4 Correction 4 — disk projection

- **Superseded (in-session):** ~7-8 GB DuckDB, extrapolated ~25x from the 2026-07-07 ratio.
- **`CORRECTED`:** **1871.8 MB from a 313.9 MB raw ≈ 6x**; 9.4 GB free after both rebuilds.
- Evidence: file sizes on disk, `reprocess.log`.

### 16.5 Correction 5 — counters versus delivery

- **Superseded (implicitly, at the start of the session):** `premium_legs = 15` with `failed=0
  refused=0` reads as a successful 15-leg session.
- **`CORRECTED`:** it is an allocation/dispatch claim. Delivery was 5 for 274 of 361 minutes, and
  only Tier 0 settles the book depth per symbol.
- Evidence: the `delivering_legs` histogram and the Tier-0 classification.

### 16.6 Corrections found while writing this document

These were discovered by cross-checking the committed evidence against the artifacts. They were
reported for a decision and then, on approval, **corrected in place** in
`Documents/patches/f10_live_validation_20260828.md`, `plans/Plan_002...md` §22.13.5 / §22.13.5a and
`Documents/CHANGELOG.md`, in a **separate commit**; `18e9dd6` is preserved unamended as the original
F10B checkpoint. The superseded readings are stated in those documents rather than erased. See §24.

- **D1 — gap count.** Formal evidence and Plan_002 §22.13.5 say "one 62 s gap ... otherwise
  continuous". There are **two** gaps (62.2 s and 40.4 s) and **three** watcher runs.
- **D2 — `refused=0`.** Formal evidence states `failed=0 refused=0` as a session fact and "the
  framework never saw the refusals". Pass **1084** at 11:28:58.570 logged **`refused=2`** with
  **`premium=13/15`**, recovering ~0.5 s later. True for 4573 of 4574 dispatches; false as an
  absolute.
- **D3 — refusal clustering.** Formal evidence INFERRED item 3 says the refusals land at
  connect/reconnect timestamps "and never between them". The 11:28:59 cluster falls at a
  `window_change` with no nearby reconnect, and holds 2 records rather than 4.
- **Note (in-session reading, not a committed claim): the "578 MB -> 552 MB WAL checkpoint".** The
  live store is one file of **578,785,280 bytes = 552.0 MiB**. The apparent shrink is a MB/MiB unit
  artifact, not a measured reduction. Only the closed size is `OBSERVED`.

### 16.7 Refinements that are *not* discrepancies

- **401,716 vs 401,881 depth records** — different window boundaries (13:56:30-14:36:30 vs
  13:56:29-14:36:32). Both correct; the symbol classification is identical.
- **+10.6 s vs +9.8 s restoration** — the same packet (14:14:13.633) measured from the 14:14:03.0
  second boundary versus the 14:14:03.813 disconnect log line.
- **"30 refusals"** — 30 *records*, being 15 logical events double-logged.
- **"139 at 5 levels"** — 135 symbols at exactly (5,5) plus 4 more reaching 5 on the buy side.

---

## 17. What was actually proven

| Claim | Status | Evidence |
|---|---|---|
| Preflight showed NIFTY/NFO -> 50 (hard gate) | **OBSERVED** | `actual_depth {"NIFTY": 50, "SENSEX": 5}` in all 1293 samples and final health |
| The framework ran genuinely enabled at budget 15 | **OBSERVED** | `framework mode ON ... premium budget 15`; `effective_budget = 15` in every sample |
| 15 premium legs allocated and dispatched | **OBSERVED** | `premium_legs = 15` in all 1293 samples; `premium=15/15` on 4574 log lines |
| 15 premium legs actually delivering a 50x50 book | **OBSERVED / Tier-0 verified** | 15 symbols at (50,50) on every record, 13:56:29-14:36:32 |
| 139 remainder legs at a 5-deep book | **OBSERVED / Tier-0 verified** | 135 at (5,5) + 4 reaching 5 buy-side |
| 172 contracts concurrently | **OBSERVED** | 172 distinct symbols in Tier 0; `active_contracts = 172` |
| True-scale duration 40.0 min | **OBSERVED** | 160 consecutive samples |
| Performance within the F25 envelope at true scale | **OBSERVED** | §11 |
| Zero drops during the window and the session | **OBSERVED** | all three counters 0 at every sample |
| `degraded_level` never above 0 | **OBSERVED** | 1293 samples |
| No abort criterion fired, hard or instant | **OBSERVED** | watcher timeline; 2 soft `ws_not_connected` events only |
| A natural reconnect restored premium depth | **OBSERVED** | Tier-0, both sides of 14:14:03.813 |
| The same 15 symbols were restored | **OBSERVED** | set equality, True |
| Restoration latency ~10 s | **OBSERVED** | first 50-level packet 14:14:13.633 |
| Lossless-raw invariant held | **OBSERVED** | `raw_dropped_total = 0`; EOF `record_count = 3,043,790` = replay packet count; 0 corrupt lines |
| `config_hash` unchanged by the flip | **OBSERVED** | one distinct value across HEADER + 1293 samples |
| Graceful teardown and clean exit | **OBSERVED** | EOF written; `orchestrator exit rc=0 restarts=0` |
| Tier-2 rebuild reproducible from Tier 0 | **OBSERVED** | 12,835,490 rows, 0 corrupt lines, `rc=0` |
| The 5-leg plateau is the FYERS per-connection cap | **INFERRED** | broker message text + constant `premium_legs` + delivery pinned at 5 |
| The 15-leg window is 3 connections x 5 | **INFERRED** | frozen capability model + 5/7/15 plateaus |
| Broker ceiling above 15 | **UNKNOWN** | never probed (F24 = A) |
| General reconnect behaviour across all failure modes | **UNKNOWN** | one reconnect depth-verified; five not |
| Internal cause of each refusal | **UNKNOWN** | OpenAlgo connection allocation uninstrumented here |
| Why the 15-leg condition lasted only 40 minutes | **UNKNOWN** | same |
| Performance over a full-length 15-leg session | **NOT PROVEN** | measured window is 40 min |
| 15 legs as the broker's maximum | **NOT PROVEN** | F24 = A forbids establishing it |
| Behaviour above budget 15 | **NOT TESTED** | deliberately |
| Forced-reconnect recovery | **NOT TESTED** | forbidden by F23 = A |

---

## 18. What remains UNKNOWN or deferred

1. **The broker's true premium ceiling above 15.** `UNKNOWN` **by design** — F24 = A. No 16th
   premium subscription was attempted. `NOT TESTED`, which is not the same as tested-and-negative.
2. **Complete reconnect behaviour across all failure modes.** One natural reconnect was
   depth-verified. Broker-side session drops, token expiry at ~03:00 IST, and forced disconnects are
   `NOT TESTED`.
3. **Internal OpenAlgo/FYERS mechanics behind the refusal clusters.** `UNKNOWN` — not instrumented
   in this project.
4. **Why the 15-leg condition held for only 40 of 361 observed minutes.** `UNKNOWN`. This is an
   **allocation-consistency** question and is explicitly **separate from D18**, which is a
   performance question. `FOLLOW-UP`.
5. **`_JOIN_TIMEOUT_SEC` sizing** for a full-size trading day. `FOLLOW-UP`, deliberately not changed.
6. **The cause of the two health-file `PermissionError` events.** `INFERRED` as a transient Windows
   lock; not established.
7. **Why 11:28 produced one logical refusal where every other cluster produced two.** `UNKNOWN`.
8. **Sustained-load behaviour** beyond a 40-minute window at 15 legs. `NOT TESTED`.

---

## 19. D18 decision

**D18 — CLOSED 2026-08-28.**

The evidence chain:

1. The hard gate passed: NIFTY/NFO reported 50-level capability, so a 15-legs-@50 measurement was
   possible at all.
2. The framework ran genuinely enabled (F22 = A) at `effective_budget = 15` for the whole session.
3. The true-scale condition **actually occurred**: `delivering_legs = 15` for 160 consecutive
   samples, 13:56:29-14:36:32, **40.0 minutes**.
4. It was **independently verified from Tier 0**, not from a counter: exactly 15 distinct NIFTY
   symbols carried a (50, 50) book on every record in the window, alongside 139 legs with a 5-deep
   book, 172 contracts, 401,881 depth records.
5. The performance envelope in that window sat well inside F25: `cycle_ms_p50` 17.2 ms median
   (soft 30, hard 500), `cycle_ms_max` 44.1 ms peak, RSS 97.7 MB peak (soft 500, hard 2048), queue
   peaks 4 / 2 / 37 against 45,000 / 45,000 / 90,000.
6. `degraded_level` stayed 0 and **all three drop counters stayed 0**.
7. Tripling the premium legs over the P10-E baseline produced no cycle-time degradation.

D18 asked for perf and RSS at true scale. That is now measured, at true scale, from delivered
packets.

**What D18's closure does not mean.** It does **not** establish the broker's absolute premium
ceiling above 15 — that was never probed (F24 = A) and **UNKNOWN #2 stands**. It does not establish
why the true-scale condition was available for only 40 minutes; that mechanism is `INFERRED` at best
and is an allocation-consistency question, not D18.

---

## 20. Final F10B state

| Item | State |
|---|---|
| Session | 10:12:01 -> 15:35:00 IST, 2026-08-28 |
| Teardown | graceful, scheduled (`session_end` + grace) |
| EOF marker | written, `record_count = 3,043,790`, `close_timestamp = 1787911500` |
| Reprocess | `rc=0`; 2 analytical stores rebuilt; 0 corrupt lines |
| Restarts | `restarts=0` |
| Final config | `market_depth_framework.enabled: false`; `git diff --stat config.yaml` empty |
| Framework | disabled in the committed config |
| Watcher / monitors | all stopped |
| Tier 0 | 313.9 MB, lossless, one HEADER + one EOF |
| Tier 1 | 552.0 MiB, closed clean after WAL checkpoint |
| Tier 2 | 1871.8 MB, rebuilt offline from Tier 0 |
| Committed | `18e9dd6` — the three authored F10B documents |
| Deliberately excluded from the commit | `data/health.json`, `data/reprocess.log`, `data/f10_timeline.jsonl`, `data/f10b_*`, `data/2026-08-28/**`, `../db/`, `../log/` |
| Not pushed at the time of writing | `18e9dd6` is local; the push was blocked by the environment's permission classifier |

---

## 21. Reproducibility appendix — command and pattern inventory

Only operations **actually executed** are listed. Where the exact syntax was not preserved, the
operation is named and marked, rather than reconstructed as a plausible-looking command.

### A. Git / state inspection

```text
Purpose:        establish the pre- and post-F10B checkpoints and the staged set
Commands:       git status --short
                git rev-parse --abbrev-ref HEAD
                git show --stat --format="%H%n%ad%n%s" 77bd786
                git show --stat --format="%H%n%ad%n%s" 18e9dd6
                git diff --stat config.yaml
                git log --oneline -1 -- Documents/patches/f10_live_validation_20260828.md
Result:         HEAD 18e9dd6 on main; F10A = 6 files / +1295; F10B = 3 files;
                config.yaml diff empty
Interpretation: no code changed for F10B; the config flip was fully reverted
Evidence strength: HIGH
```

```text
Purpose:        ensure no credential reached the commit
Command:        git diff --cached -U0 | grep -inE "api[_-]?key|token|secret|password"
Result:         no matches
Interpretation: the staged documents carry no credential-shaped string
Evidence strength: HIGH (pattern-based, not exhaustive)
```

### B. Config validation

```text
Purpose:        confirm the framework block validates with the flag on, and the hash is unmoved
Operation:      python -m market_depth_recorder --validate-config --config <config.yaml>
                (F10A, with enabled:false and enabled:true; and again at F10B activation)
Result:         exit 0 in every case; config_hash byte-identical
Exact F10A shell syntax: NOT RECOVERABLE FROM AVAILABLE ARTIFACTS
Evidence strength: HIGH (corroborated at runtime by 1293 samples carrying one hash)
```

```text
Purpose:        confirm the committed config is framework-disabled
Command:        grep -n -A2 "^market_depth_framework:" config.yaml
Result:         line 173  enabled: false
Evidence strength: HIGH
```

### C. Runtime health inspection

```text
Purpose:        read the final published health payload
Command:        head -c 1800 data/health.json
Result:         state=close, 172 active contracts, 0 drops, degraded 0,
                rows_written 3,322,547, stale_rows_total 309,946,
                raw_records_written 3,042,227, restart_count 0,
                framework{passes 4603, failures 0, live_legs 5, pending_rejections 0,
                          eligible_underlyings ["NIFTY"],
                          plan_mailbox{published 4603, taken 4573, superseded 30, pending 0}},
                framework_feed{plans_executed 4573, plan_failures 0, premium_legs 15,
                               effective_budget 15, delivering_legs 5, claimed_wire_symbols 172}
Evidence strength: HIGH for framework state; NOT delivery evidence
```

### D. Log inspection

```text
Purpose:        enumerate every distinct error and warning without reading 9263 lines
Command:        grep -oE "(ERROR|WARNING) +\[[A-Za-z]+\] [^:]*: .{0,70}" data/f10b_recorder.log \
                  | sed 's/[0-9]\{3,\}/N/g' | sort | uniq -c | sort -rn
Result:         7 feed socket closed · 6 raw WS error: ping/pong timed out
                6 feed disconnected — reconnecting · 6 websocket: ping/pong timed out - goodbye
                2 failed to write health file · 1 SQLiteLiveWriter did not join within 10s
Interpretation: the complete anomaly inventory for the session, in six lines
Evidence strength: HIGH
```

```text
Purpose:        find any dispatch that was refused or failed
Commands:       grep -cE "refused=[1-9]" data/f10b_recorder.log   -> 1
                grep -cE "failed=[1-9]"  data/f10b_recorder.log   -> 0
                grep -oE "premium=[0-9]+/15" data/f10b_recorder.log | sort | uniq -c
                  -> 1 premium=13/15 ; 4574 premium=15/15
Interpretation: exactly one dispatch saw a refusal; DISCREPANCY D2
Evidence strength: HIGH
Note:           the earlier bare-word filter (`failed` / `refused`) matched all 4574 lines
```

```text
Purpose:        list every dispatch that actually sent something
Command:        grep -E "framework plan [0-9]+ \([a-z_]+\): sent=[1-9]" data/f10b_recorder.log
Result:         20 dispatch events out of 4574 plans; the rest are skipped/no-op
Interpretation: subscription churn is rare; refusals coincide with these moments
Evidence strength: HIGH
```

```text
Purpose:        recover the reconnect inventory and its proximate cause
Command:        grep -niE "reconnect|disconnect|websocket .*(open|clos)" data/f10b_recorder.log
Result:         6 disconnect/reissue pairs; all preceded by "ping/pong timed out"
Evidence strength: HIGH
```

```text
Purpose:        read the teardown sequence exactly
Command:        sed -n '/15:34:5\|15:35:/,$p' data/f10b_recorder.log | grep -vE "INFO .*\[Proc\]"
Result:         the six-line teardown trace in §10 Scenario G
Evidence strength: HIGH
```

### E. Timeline analysis

```text
Purpose:        coverage, gaps, and watcher lifecycle
Operation:      parse the JSONL; split rows on r['record'] in {meta, sample, event};
                sort samples by r['at'] (float epoch, NOT an ISO string);
                report first/last and every consecutive delta > 20 s;
                convert r['started'] (ISO UTC) on meta rows to IST
Result:         1293 samples, 10:12:31..15:37:05; gaps 62.2 s and 40.4 s; 3 meta rows
Interpretation: two interruptions, both before 11:06, neither in the measurement window
Evidence strength: HIGH
Note:           two earlier parse attempts failed — one keyed on 'ts'/'timestamp'
                (0 samples), one treated 'at' as an ISO string.
                The schema was then read from a sample rather than assumed.
```

```text
Purpose:        find the true-scale window and its envelope
Operation:      Counter over r['delivering_legs'];
                run-length encode the sorted sample stream;
                for the subset with delivering_legs == 15 report
                min/median/max of cycle_ms_p50, cycle_ms_max, rss_mb and
                min/max of the queue, drop, degraded and contract fields
Result:         histogram {0:1, 3:1, 5:1097, 7:34, 15:160};
                the 15-run spans 13:56:29..14:36:32 = 40.0 min
                (interrupted by one 0 sample at 14:14:15, the reconnect);
                envelope as tabulated in §11
Evidence strength: HIGH for the envelope; the run itself is delivery-derived
```

### F. Raw Tier-0 analysis

See §12 for the full block. Streaming, prefiltered on `'"Depth"'`, classified per symbol by
`(max len(depth['buy']), max len(depth['sell']))` inside the window.

```text
Purpose:        confirm the session markers and the record count
Operation:      stream the gzip; collect lines containing '"meta_type"'; print the last line
Result:         exactly 2 meta records — HEADER and EOF;
                EOF {"record_count": 3043790, "close_timestamp": 1787911500}
Interpretation: no interior restart markers; record count matches the replay exactly
Evidence strength: HIGH
```

### G. Reconnect analysis

See §13 for the full block.

### H. Broker error analysis

See §14 for the full block.

```text
Purpose:        locate the correct error log (two candidates exist)
Command:        grep -c "symbol count exceeds limit" \
                  openalgo/log/errors.jsonl  strategies/SS_Projects/log/errors.jsonl
Result:         30  and  0
Interpretation: the refusals are in OpenAlgo's log; the project's own error channel is empty,
                which is itself the evidence that the framework was never told
Evidence strength: HIGH
```

### I. Teardown / reprocess verification

```text
Purpose:        confirm the rebuild completed and how much it produced
Commands:       tail -18 data/reprocess.log
                ls -l data/2026-08-28/
                python -c "os.path.getsize(...)/1048576 for each artifact"
                df -h .
Result:         2 stores rebuilt (2026-07-14: 2,805,069 rows; 2026-08-28: 12,835,490 rows),
                0 corrupt lines, CATCHUP OK;
                raw 313.9 MB / live 552.0 MiB / duckdb 1871.8 MB; 9.4 GB free at writing
Interpretation: ~6x expansion, not the ~25x projected
Evidence strength: HIGH
Note:           an earlier check greped the whole append-only reprocess.log and surfaced a
                KeyboardInterrupt traceback from a previous run. Scope every such grep with
                sed -n '/reprocess start <today>/,$p'
```

---

## 22. Evidence hierarchy

The ranking this investigation used, strongest first:

1. **Tier-0 raw delivery records.** The bytes that actually arrived. The only evidence that settles
   book depth per symbol. Everything decisive in F10B rests here.
2. **Recorder logs and broker error logs.** Runtime and broker events with millisecond (recorder) or
   second (broker) timestamps. Strong for *what happened when*; silent about *what was delivered*.
3. **Timeline health samples.** A 15 s time series of performance and state. Strong for envelopes;
   structurally blind to anything shorter than one interval — which is exactly how the 11:28:58
   `refused=2` event escaped it.
4. **Framework counters and state.** `premium_legs`, `plans_executed`, `plan_failures`,
   `effective_budget`. These describe **planning and dispatch**, i.e. intent that OpenAlgo accepted.
5. **Acknowledgements.** Transport acceptance. Nothing more.
6. **Human observation and interim interpretation.** Lowest. Five of them were wrong on the day
   (§16) and each was overturned by a level above.

**Why level 4 cannot substitute for level 1.** On 2026-08-28 the framework held `premium_legs = 15`
and `plan_failures = 0` for the entire session while actual delivery sat at 5 legs for 274 of 361
minutes, because OpenAlgo accepted every request and the broker refused downstream into a log the
framework never reads. A report built at level 4 would have been internally consistent, fully
"successful", and wrong. `delivering_legs` (level 3, packet-derived) exposed the gap; Tier 0
(level 1) proved the book shape per symbol.

**Why an acknowledgement is not depth confirmation.** The recorder's own log says it:
`framework reconnect: reissued 172 leg(s) (failed=0 refused=0) — depth unconfirmed until packets
arrive`.

---

## 23. Lessons for future validation phases

1. **Delivery must be verified independently of dispatch.** Record a packet-derived measure and
   confirm the decisive claim in Tier 0.
2. **A counter that names desired or claimed state must never be read as delivery evidence** —
   including when it is stable, plausible, and accompanied by zero failures.
3. **Sample-based monitoring has a floor.** Anything shorter than the interval is invisible. Pair the
   timeline with an event-level log audit after the session; the 11:28:58 refusal exists only in the
   log.
4. **Cross-check the layer below.** The broker's refusals were in another system's log. A validation
   that reads only its own logs cannot see the thing it most needs to see.
5. **Monitor filters must distinguish zero from non-zero.** `failed` matches `failed=0`;
   `failed=[1-9]` does not.
6. **Scope greps on append-only logs to the current run**, or old tracebacks will be reported as new
   failures.
7. **A natural reconnect can resolve an UNKNOWN without forcing a risky disconnect** — but only if
   the instrumentation is already recording when it happens.
8. **Understand a long-lived process before calling it hung.** The 21-minute post-teardown wait was
   the documented `.wait()`-reap of the reprocess child.
9. **Project disk from a completed rebuild ratio, not from a different day's raw.** The 25x
   extrapolation was 4x too pessimistic.
10. **Watch the units.** MB and MiB on a 578,785,280-byte file look like a 26 MB saving that never
    happened.
11. **Keep corrections visible.** Five in-session readings were wrong and were overturned by
    measurement; a record that hides them cannot be audited.
12. **Cross-check the formal evidence against the artifacts before treating it as settled.** Three
    inaccuracies in the committed evidence were found only by re-deriving its numbers.

---

## 24. Final audit checklist

- [x] No invented commands — every command in §21 was executed, or the operation is named and marked
      `NOT RECOVERABLE FROM AVAILABLE ARTIFACTS`
- [x] No invented measurements — every figure re-derived from an artifact named in §1
- [x] Planned vs executed clearly separated (§2 objective vs §5-§10 execution)
- [x] OBSERVED / INFERRED / UNKNOWN separated (§14, §17, §18)
- [x] All major anomalies recorded (§15, eleven items, classified)
- [x] Corrections to earlier interpretations recorded (§16, six subsections)
- [x] Tier-0 verification methodology documented (§12)
- [x] Reconnect verification methodology documented (§13)
- [x] Broker refusal analysis documented (§14)
- [x] Teardown behaviour documented (§10 Scenario G)
- [x] Disk / reprocess behaviour documented (§10 Scenario H)
- [x] D18 conclusion agrees with the formal F10B evidence (§19)
- [x] Remaining UNKNOWNs preserved (§18) — UNKNOWN #2 explicitly still open
- [x] No source, config, test or runtime file modified by this documentation task
- [x] **Consistency with the formal evidence — D1, D2 and D3 reported, approved, and CORRECTED** in
      the formal evidence, Plan_002 §22.13.5 / §22.13.5a and the CHANGELOG, in a separate commit;
      `18e9dd6` preserved unamended

### Consistency check against `f10_live_validation_20260828.md` and Plan_002

| Fact | Formal evidence | This document | Agreement |
|---|---|---|---|
| Session timing | 10:12:01 -> 15:35:00 | same | AGREE |
| 40-minute true-scale window | 13:56:29-14:36:32, 160 samples | same | AGREE |
| 15 premium legs at 50x50 | 15, Tier-0 verified | 15, independently re-verified, symbols listed | AGREE |
| 139 standard-depth legs | 139 | 135 at (5,5) + 4 reaching 5 buy-side = 139 | AGREE (refined) |
| 172 contracts | 172 | 172 distinct symbols in Tier 0 | AGREE |
| Depth records in window | 401,716 (13:56:30-14:36:30) | 401,881 (13:56:29-14:36:32) | AGREE (boundary) |
| Performance envelope | as tabulated | re-derived, identical | AGREE |
| Zero drops | 0 / 0 / 0 | same | AGREE |
| Natural reconnect restoration | same 15 symbols | same 15 symbols, set equality True | AGREE |
| Restoration latency | +10.6 s | +9.8 s from the log line = +10.6 s from 14:14:03.0 | AGREE (reference epoch) |
| 30 broker-side refusals | 30 | 30 records = 15 logical events | AGREE (refined) |
| Watcher gap | was "one 62 s gap ... otherwise continuous"; **now corrected to two gaps / three watcher runs** | two gaps: 62.2 s and 40.4 s; three watcher runs | **D1 — CORRECTED, now AGREE** |
| Framework refusals | was `failed=0 refused=0` / "never saw the refusals"; **now corrected to 4573 of 4574** | pass 1084 logged `refused=2`, `premium=13/15` | **D2 — CORRECTED, now AGREE** |
| Refusal clustering | was "4-refusal clusters ... never between [reconnects]"; **now corrected to the request/re-request formulation** | 11:28 cluster = 2 records, at a `window_change` | **D3 — CORRECTED, now AGREE** |
| Teardown behaviour | EOF, join timeout, rc=0 | same | AGREE |
| Final config | disabled, diff empty | same | AGREE |
| D18 | CLOSED | CLOSED | AGREE |
| UNKNOWN #2 | stands | stands | AGREE |

**Every discrepancy was resolved from the underlying artifacts, not by preferring one document.**
D1 from the timeline's `meta` rows and sample deltas; D2 from `grep -cE "refused=[1-9]"` and the
`premium=N/15` histogram; D3 from the refusal timestamps cross-referenced against the dispatch log.

**None of D1, D2 or D3 changes the D18 verdict.** All three concern the session narrative outside the
measurement window: both gaps precede 11:06, and the 11:28:58 refusal is 2.5 hours before the window
opens. The 15-leg measurement, its Tier-0 verification, the envelope and the reconnect evidence are
unaffected.

**Disposition.** The three discrepancies were reported for a decision before any change was made.
On approval they were corrected in `Documents/patches/f10_live_validation_20260828.md`,
`plans/Plan_002...md` (§22.13.5 and the new §22.13.5a) and `Documents/CHANGELOG.md`, in a **separate
corrective commit**. Commit `18e9dd6` is **preserved unamended** as the original F10B evidence
checkpoint, so the history shows the original record and the subsequent artifact-driven correction as
two distinct events. In each corrected document the superseded reading is stated alongside the
correction rather than erased.

**One inaccuracy was deliberately left standing.** The formal evidence's "the live DB closed at
552 MB (from 578 MB mid-teardown, the checkpoint completing)" reads a MB/MiB unit artifact on one
unchanged 578,785,280-byte file as a size reduction (§16.6). It is outside the three approved
corrections and was not changed; it is recorded here and in the CHANGELOG's deferred list.
