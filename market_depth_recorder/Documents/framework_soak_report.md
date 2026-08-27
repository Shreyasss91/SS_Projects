# Framework soak report (F9 / F20)

- Generated: 2026-08-27T10:08:41Z (UTC, wall clock of the reporting run only)
- Config: `config.yaml`
- Allocation-log digest: `sha256:44a0f674071f8c7bbc54e400ac2c469067c4a41ac694171eb6a0790b6b92cbc2`
- Replays required byte-identical: 2 (all identical)

## Provenance of the recording

- Path as given: `market_depth_recorder/data/2026-07-14/market_depth_raw_20260714.jsonl.gz`
- File: `market_depth_raw_20260714.jsonl.gz` (36056632 bytes)
- Recording sha256: `sha256:f92c67a6294be588f2ebec093a391e9633bd7e80c5170a4af60b4ff505e52266`

The recording was opened **read-only** and never modified, copied into the repository, or
committed. It is not the harness's deterministic test fixture -- that is a synthetic session
generated inside the test suite -- and nothing here is used to infer broker capacity,
reconnect behaviour, or any other broker semantic.

## What this is not

This soak ran offline against a recording transport. It opened no socket and contacted no
broker. It is a determinism and invariant result, **not broker evidence**: reconnect depth
restoration and the real premium ceiling remain UNKNOWN and are settled only by a live run.

## Session

- Packets read: 319445 (corrupt lines tolerated: 0)
- Rebalance passes: 772
- Trigger mix: {'initial': 1, 'interval': 508, 'window_change': 263}
- Underlyings: NIFTY, SENSEX
- Effective premium budget: 15
- Simulated confirmations (driver, not broker): 236

## Allocation behaviour

- Plan actions by kind: {'downgrade': 34, 'subscribe': 340, 'upgrade': 34}
- Wire operations: {'subscribe': 236, 'unsubscribe': 68}
- Tier flips: 68 across 4 distinct legs
- Churniest legs: [{'symbol': 'NIFTY14JUL2623900CE', 'flips': 17}, {'symbol': 'NIFTY14JUL2623950PE', 'flips': 17}, {'symbol': 'NIFTY14JUL2624300CE', 'flips': 17}, {'symbol': 'NIFTY14JUL2624300PE', 'flips': 17}]
- Per-underlying budget range: {'NIFTY': {'min': 0, 'max': 15}}

### Premium-occupancy histogram (occupancy -> passes)

| Premium legs held | Passes |
|---|---|
| 0 | 313 |
| 15 | 459 |

Peak occupancy 15 of an effective budget of 15.

313 of 772 passes ran while at least one underlying still had no spot -- a premium-eligible underlying with no spot has no window, so it can hold no premium leg. Zero-occupancy passes come from that, not from the allocator declining to spend its budget.

## Invariants

| Invariant | Violations |
|---|---|
| Premium occupancy never exceeds the effective budget | 0 |
| No instrument owned at two tiers at once | 0 |
| Obsolete tier released before the new tier is claimed (F7.6) | 0 |

Shortest observed gap between two tier flips of one leg: 30.072 s (configured churn cooldown: 30 s).

## Cost

- Wall time: 19.37 s for 2 replays
- Mean pass wall time: 12.546 ms
- Peak RSS: 46.8 MB
