# F10 live validation -- evidence

- Trading date: 2026-08-28 (NIFTY weekly expiry 01-SEP-2026)
- Samples: 1293 at 15.0 s cadence
- Window: recorder started 10:12:01 IST, teardown 15:35:00 IST; watcher samples 10:12:31 .. 15:37:05 IST
- Recorder `config_hash`: `sha256:8a48bcdd4fca933d1dbc85bd9a5c1dc055403392da0afeb22e629af550a1468b` (identical in every one of the 1293 samples and in the Tier 0 HEADER)
- Health file: `C:\Users\admin\Downloads\ai tools\openalgo_platform\openalgo\strategies\SS_Projects\market_depth_recorder\data\health.json`
- Timeline: `C:\Users\admin\Downloads\ai tools\openalgo_platform\openalgo\strategies\SS_Projects\market_depth_recorder\data\f10b_timeline_20260828.jsonl`

## OBSERVED

Every number below was read from the recorder's own `health.json` during the session.

| Measure | Observed |
|---|---|
| `cycle_ms_p50` | 11.8 .. 22.1 ms |
| `cycle_ms_max` | up to 89.0 ms |
| `rss_mb` | 53 .. 105 MB |
| `proc_queue_size` peak | 7 |
| `db_queue_size` peak | 2 |
| `raw_file_queue_size` peak | 37 |
| `raw_dropped_total` final | 0 |
| `db_rows_dropped_total` final | 0 |
| `proc_dropped_total` final | 0 |
| `degraded_level` peak | 0 |
| Premium legs peak | 15 |
| Effective budget seen | [15] |
| Delivering legs (final) | 5 |
| Desired legs (final) | 172 |
| Plans executed (final) | 4573 |
| Plan failures (final) | 0 |
| `actual_depth` seen | ['{"NIFTY": 50, "SENSEX": 5}'] |
| Restarts during watch | 0 |

### Delivery at depth -- the measurement D18 needed

`delivering_legs` is packet-derived (`websocket_client.py:791`), so it is evidence of delivery, not
of dispatch. `premium_legs` was 15 for the entire session; delivery was not.

| `delivering_legs` | Samples | Duration | Note |
|---|---|---|---|
| 15 | 160 | **40.0 min** | 13:56:29-14:36:32 -- the true-scale window |
| 7 | 34 | 8.5 min | 12:29:53-12:38:24 |
| 5 | 1097 | 274.2 min | the plateau for most of the day |
| 3 | 1 | 0.2 min | 14:51:03, single sample |
| 0 | 1 | 0.2 min | 14:14:15, during the reconnect |

Verified in the Tier 0 raw across 13:56:30-14:36:30: **172 distinct symbols, of which exactly 15
carried a 50x50 book on every record** (4 lakh+ depth records), 139 carried 5 levels, and the
remainder were shallow/partial. The 15 were the near-ATM 01-SEP-2026 NIFTY strikes 23900-24250.

### Broker-side and connection events

| Event | Count | Detail |
|---|---|---|
| Natural reconnects | 6 | 10:44:36, 12:29:33, 12:37:59, 13:35:11, 14:14:03, 14:36:33. **None forced** (F23=A). |
| Broker TBT refusals | 30 | `symbol count exceeds limit: 5` in OpenAlgo `log/errors.jsonl`, in 4-refusal clusters at 10:12, 10:44, 11:28, 12:29, 12:38, 13:35, 14:14, 14:36. |
| Framework-reported failures | 0 | `failed=0 refused=0`, `plan_failures=0`, `plans_executed=4573`. The framework never saw the refusals; OpenAlgo accepted the requests. |
| Restarts | 0 | `restart_count = 0` throughout. |

The gap between `premium_legs = 15` (dispatched, accepted) and `delivering_legs` (observed) is the
central operational finding of the day: **counters alone would have reported a fully successful
15-leg session.** Only the packet-derived measure and the Tier 0 raw showed otherwise.

### Abort conditions fired

None.

### Soft conditions recorded

| Condition | Samples | First at |
|---|---|---|
| `ws_not_connected` | 2 | 1787900889.366 |


## INFERRED

Each item below is a reading of the observations, not itself an observation.

1. **The 5-leg plateau is the FYERS per-connection TBT cap, not a framework fault.** The framework
   dispatched `premium_legs = 15` continuously and logged `failed=0 refused=0 plan_failures=0` all
   session, because OpenAlgo accepted every request. The refusals appear only in OpenAlgo's own
   `log/errors.jsonl`, downstream. Rests on: the 30 broker refusals, the constant `premium_legs=15`,
   and `delivering_legs` sitting at 5 for 274 of the 361 observed minutes.
2. **The 15-leg window is the three TBT connections all carrying their 5 symbols at once.** 5 and 15
   are exactly 1x and 3x the documented per-connection cap, and 7 (8.5 min) is a partial
   intermediate. Rests on the frozen FYERS capability model (`tbt_budget = 15` = 3 x 5) plus the
   observed 5 / 7 / 15 plateaus. **Not established:** why the allocation reached 3 connections only
   between 13:56 and 14:36. Nothing in this session instruments OpenAlgo's connection assignment, so
   the mechanism is unproven.
3. **Refusals are a resubscribe-time effect.** All 30 land in 4-refusal clusters at exactly the
   connect and reconnect timestamps (10:12, 10:44, 11:28, 12:29, 12:38, 13:35, 14:14, 14:36) and
   never between them. Rests on the refusal timestamps against the six reconnect timestamps.
   Note that 14:14 produced refusals *and* full 50-level restoration, so a refusal cluster does not
   by itself predict degraded delivery.

## Deviations and defects observed during the run

Recorded because they happened, not because they changed the result.

| Item | Detail | Effect on this evidence |
|---|---|---|
| Watcher sampling gap | One 62 s gap ending 10:42:05, from a watcher restart. Coverage is otherwise continuous 10:12:31-15:37:05. | Negligible. An earlier report in-session of a "~20 minute gap" was wrong; the measured gap is 62 s. |
| Health-file write failures | 2 occurrences (11:10:03, 15:24:50): `PermissionError [WinError 5]` on `os.replace` in `utils.py:134`, a transient Windows lock during the atomic swap. Never consecutive. | None. No F25 criterion covers it; the 3-sample sustain rule was never engaged. |
| `SQLiteLiveWriter did not join within 10s` | At teardown, the db writer exceeded the `_JOIN_TIMEOUT_SEC` budget (`main.py:467`). `db_queue_size` was 0, so this is close/checkpoint cost on a 578 MB database, not unwritten rows. | None for Tier 0. Worth a follow-up: the join budget may simply be too small for a full-size day. The thread finished afterwards: the live DB closed at 552 MB (from 578 MB mid-teardown, the checkpoint completing) and the orchestrator exited `rc=0 restarts=0`. |
| Disk headroom | 10.3 GB free at teardown. A mid-session projection of ~7-8 GB for the rebuild (extrapolating the 2026-07-07 ratio of ~25x) **proved wrong**: the actual store is **1872 MB from a 314 MB raw (~6x)**, finishing 15:56:38 with 8.3 GB free. | None. The projection is recorded because it was acted on during the session, and corrected because it was inaccurate. |

## UNKNOWN

- **Reconnect depth restoration -- RESOLVED this session by natural observation.** F23=A allows this
  to close only if a reconnect happened on its own *and* premium legs were then seen delivering at
  depth. Both occurred. Six reconnects happened naturally; **none was forced**. At the 14:14:03
  reconnect, which fell inside the 15-leg window, the identical set of 15 premium symbols resumed
  full 50-level delivery, first 50-level packet at **+10.6 s** (14:14:13). Verified against Tier 0,
  not against a counter.
- **The broker's true premium ceiling -- STILL UNKNOWN.** Per F24=A this session ran at the
  configured effective budget of 15 and never probed beyond it. No 16th premium subscription was
  attempted. That 15 legs sustained 50-level delivery says nothing about whether the broker would
  accept more. UNKNOWN, deliberately.

## Comparison against P10-E

P10-E baseline: `cycle_ms_p50` ~22 ms (max 43-60 ms), RSS 52-58 MB, at <=5 NFO @50 plus ~120
SENSEX @5.

| | P10-E | F10B 5-leg baseline | **F10B 15-leg window** |
|---|---|---|---|
| Premium legs delivering @50 | <=5 | 5 | **15** |
| Total contracts | ~125 | 160-172 | **172** |
| `cycle_ms_p50` | ~22 | 17.0 median (11.8-22.1) | **17.2 median (14.5-19.0)** |
| `cycle_ms_max` | 43-60 | 41.6 median, 89.0 peak | **39.2 median, 44.1 peak** |
| RSS | 52-58 MB | 95.3 median, 105.3 peak | **97.1 median, 97.7 peak** |
| Drops (raw/proc/db) | 0 | 0 | **0** |
| `degraded_level` | 0 | 0 | **0** |

Tripling the premium legs and adding ~47 contracts did not degrade cycle time -- p50 is flat at
~17 ms and the *maximum* is lower inside the 15-leg window than outside it. RSS rose to ~97 MB
against a 500 MB soft target. The cost of true scale is well inside the envelope.

## D18 conclusion

**D18 CLOSES.**

D18 asked for perf/RSS at true scale -- up to 15 legs @50 plus the hybrid remainder -- which had
never been measured. This session measured it. Between **13:56:29 and 14:36:32 (40 minutes)** the
recorder ran the genuine true-scale hybrid: **15 NIFTY legs at a full 50x50 book plus 139 legs at
5 levels, 172 contracts total, 401,716 depth records**, verified per symbol against the Tier 0 raw
rather than inferred from a counter. Every symbol in that window reported `(50, 50)` on every
record.

The envelope in that window: `cycle_ms_p50` 17.2 ms median (soft target 30), `cycle_ms_max` 44.1 ms
peak (hard 500), RSS 97.7 MB peak (soft 500, hard 2048), queues effectively empty (proc peak 4, db
peak 2, raw peak 37 against 45,000/45,000/90,000), `degraded_level` 0, and **zero drops on all three
counters**. No abort condition fired at any point in the session, hard or instant. The
lossless-raw invariant held: `raw_dropped_total = 0`, EOF marker written on a clean drain with
`record_count = 3,043,790`.

**What this does not establish.** It does not establish the broker's ceiling above 15 (F24=A, and
UNKNOWN #2 stands). It does not establish *why* the 15-leg condition held for only 40 of 361
minutes -- the mechanism behind OpenAlgo's TBT connection allocation is uninstrumented here and is
INFERRED at best. D18 is a performance question, and at true scale the performance is now measured;
the allocation-consistency question is separate and is not D18.
