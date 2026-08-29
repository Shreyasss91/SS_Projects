# FYERS TBT — Jul-07 vs Jul-14 reconciliation (instantaneous concurrency)

**Date:** 2026-07-14 · **Status:** authoritative · **Method:** re-analysis of the raw
`.jsonl.gz` audit logs (Tier 0) at **per-second instantaneous granularity**, not aggregate
session coverage.

## Why this exists
Two live investigations appeared to contradict each other:

- **P10-E (2026-07-07)** concluded the channel-spread patch worked: *"full-run raw shows NFO
  `depth_levels` up to 47 across all 80 legs / ~16 TBT channels … no global FYERS cap"* →
  *"D2 holds — whole chain at 50-level, no hybrid."*
- **P10-E-0714 + P10-F (2026-07-14)** — official FYERS docs + single-connection probe +
  multi-connection probe — establish a hard **5 Market-Depth symbols per connection** cap
  (channels do not add capacity), effective **15** across 3 connections.

Before locking the architecture on `tbt_budget = 15`, the contradiction had to be reconciled
against the **evidence**, not overwritten.

## The discriminating question
Aggregate "did depth packets exist for many legs over the session" does **not** prove
concurrent streaming. The right question: **at any given second, how many distinct NFO legs
were simultaneously receiving 50-level depth on the single TBT connection?** (On both days the
recorder used one OpenAlgo TBT connection with the channel-spread patch, so distinct NFO
symbols per 1-second `recv_ts` bucket = instantaneous concurrency on that connection.)

## Result — the two days are CONSISTENT

| Measure (NFO / NIFTY, mode-3 depth) | **Jul-07** | **Jul-14** |
|---|---|---|
| Distinct NFO legs that *ever* streamed depth | **9** | 5 |
| **Max concurrent distinct legs / second** | **5** | **5** |
| Seconds with **> 5** concurrent | **0** | **0** |
| Mean / median concurrency per second | 4.74 / 5 | 4.96 / 5 |
| Active set over the session | **fixed** (same 5 lowest strikes at early=mid=late) | fixed (lowest 5) |
| 50-level depth on the streaming legs | yes (levels up to 50) | yes (all 50) |
| Total NFO depth packets | 56,754 | 29,482 |

Jul-07 concurrency histogram (distinct-legs-per-second → #seconds): **`3:75, 4:1466, 5:4774`**
— never above 5. The 9 distinct legs arise only because ATM drifted during the day and the
patch's **lowest-first** channel-1 assignment shifted which 5 lowest strikes occupied channel 1
(5 dominant legs 7k–12k packets each; 4 transient legs ~1k each). At no instant did >5 stream.

## Conclusion
1. **The 5-per-connection cap was in force on BOTH days.** No FYERS behavior change; no
   environment difference. The days agree.
2. **The P10-E (2026-07-07) "full chain / no global cap / no hybrid (D2)" conclusion was a
   measurement artifact** — it read genuine 50-*level* depth on ≤5 streaming legs plus the
   80-leg *subscription* as "80 legs *streaming*," without checking instantaneous concurrency.
   Only 9 legs ever carried depth; never more than 5 at once.
3. **Jul-14 is authoritative** — corroborated by (a) official FYERS docs, (b) the
   single-connection channel probe, (c) the multi-connection probe, and now (d) the Jul-07 raw
   re-read itself. The effective single-connection ceiling is **5**; across the documented
   3 connections it is **15** (`tbt_budget = 15`).

## Investigation #2 — OpenAlgo code delta (`git pull --rebase`) ruled out
Between the runs OpenAlgo was upgraded, so the code was **not identical** and had to be
excluded as a cause. Reflog: **Jul-07 ran at `4b2afd81`** (the 2026-06-22 clone, untouched
until Jul-10); pulls on Jul-10/Jul-11 fast-forwarded to **`a7f2be6`**, the **Jul-14** state.

`git diff 4b2afd81 a7f2be6` over every TBT-relevant path shows the **FYERS TBT streaming
implementation is byte-identical** across the upgrade:

| File (TBT streaming path) | Jul-07 → Jul-14 |
|---|---|
| `broker/fyers/streaming/fyers_tbt_websocket.py` | **UNCHANGED** |
| `broker/fyers/streaming/fyers_websocket_adapter.py` (channel-spread patch + 5/channel packing) | **UNCHANGED** |
| `broker/fyers/streaming/msg_pb2.py` (protobuf depth parse) | **UNCHANGED** |

The upgrade touched only **REST-API** files (`broker/fyers/api/data.py`, `order_api.py`, new
`rate_limiter.py`) and the **ZMQ proxy** (`websocket_proxy/base_adapter.py`,
`connection_manager.py`, `server.py` — the sole websocket commit `c9591ae6` is the ZMQ
*fan-in* fix). **None affect the TBT 50-level symbol-streaming cap** — a bus/proxy change can
only drop or deliver ticks, never make the broker stream *more* symbols than its per-connection
ceiling. TBT-relevant deps unchanged (`websocket-client 1.9.0`, `protobuf 6.33.5`).

**Verdict on the three hypotheses:** (1) FYERS behavior change — *ruled out* (both raws cap at
5 concurrent); (2) OpenAlgo TBT-code change — *ruled out* (byte-identical); (3) interpretation
artifact — *confirmed* (the Jul-07 raw itself never exceeded 5 concurrent). The two days are
consistent; only the P10-E write-up drifted from its own raw.

## Cascading correction to the P10-E record (flagged, see close-out)
Because P10-E's premise ("80 legs streamed at 50-level") is false, several P10-E claims that
depended on it need correcting alongside the protocol docs:
- **E2** "no global cap / patch works" → **artifact** (only ≤5 concurrent; see above).
- **E4** "perf/RSS fine at full 50-level scale (rss 52–58 MB, cycle ≈22 ms)" → those numbers
  were measured on **≤5 NFO @50 + 120 SENSEX @5**, **not** the claimed 80 × 50-level. The
  perf/RSS-at-true-scale check is therefore **still open**.
- **E9** "NIFTY depth coverage PASSES" → only the ≤5 streaming legs, not the chain.
- **D2** "whole chain @50, no hybrid" → **reopened**; a full chain is not achievable on one
  connection → **hybrid** (near-ATM @50 + rest @5) or multi-connection, budget 15.

## Reproduce
```
# per-second distinct NFO (NIFTY) symbols with mode-3 depth, from the raw audit log:
#   bucket int(recv_ts) -> set(symbol);  report max/mean and count of seconds > 5
# inputs (Tier-0 raw, retained):
#   data/2026-07-07/market_depth_raw_20260707.jsonl.gz
#   data/2026-07-14/market_depth_raw_20260714.jsonl.gz
```

## Related
- `tbt_multiconn_20260714.json` — the multi-connection probe evidence (C1 5/5, C3 15/15, C4 refused).
- `tbt_probe_20260714.json` — the single-connection channel matrix evidence.
- `OPENALGO_PATCH.md` §8 — the authoritative protocol correction.
- `Phase9_notes.md` §3 — original (superseded) 5-per-channel framing.
