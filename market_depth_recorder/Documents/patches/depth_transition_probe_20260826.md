# Depth-transition probe — 5 <-> 50 behaviour on the OpenAlgo/FYERS path

**Date prepared:** 2026-08-26 · **Status: F7A PREPARED — F7B LIVE EVIDENCE PENDING** ·
**Method:** to be filled by `tools/fyers/depth_transition_probe.py --live` during a live NSE session.

> **This document is not yet evidence.** Every broker-dependent field below reads
> `UNKNOWN — LIVE PROBE PENDING` and must stay that way until a live run fills it in. Do not
> infer, do not interpolate, do not fill a cell from a code reading. The template exists so that
> the live run has somewhere honest to land, and so a reader can see at a glance which questions
> are still open. The standard to match is
> [`tbt_concurrency_reconciliation_20260714.md`](tbt_concurrency_reconciliation_20260714.md).

## Why this exists

Plan_002 §20.1 makes a live depth-transition probe the gate on the Broker Adapter, and §22 fixes
the order: **F7 measures, the adapter contract is written from the measurement, then F8 integrates.**
The framework's F5 depth allocator can already decide that a leg should move between the standard
(5) and premium (50) tiers. Nothing in the codebase establishes what that move *does* on the wire —
whether it changes an existing subscription, creates a second one, costs an extra premium slot, or
drops ticks in between. Guessing it would put an unverified assumption underneath every later phase.

The recorder is running today at a fixed depth per leg, so this has never had to be answered. The
moment the framework can retier a leg mid-session, it does.

---

## 1. Probe scope

**In scope.** The behaviour of the **OpenAlgo WebSocket proxy path the recorder actually uses**
(`ws://host:8765`, `action: subscribe` / `action: unsubscribe`, mode 3) when an already-subscribed
NFO option leg is re-requested at a different depth. Four transitions (5->5, 5->50, 50->5, 50->50),
two symbol spellings, two mechanisms, plus unsubscribe support, acknowledgement semantics, reconnect
behaviour and premium-capacity effects.

**Out of scope.** Anything measured directly against the FYERS SDK, bypassing OpenAlgo — that is
what `tbt_channel_probe.py` and `tbt_multiconn_probe.py` already did for the concurrency question,
and their conclusion (`tbt_budget = 15`) is frozen and not reopened here. Also out of scope: BFO /
SENSEX at 50 levels (not premium-eligible), and any change to recorder production behaviour.

**The two cases that must not be conflated.** The recorder encodes depth **twice** — a `:50` symbol
suffix *and* a `depth` field — while the proxy keys a subscription by `(symbol, exchange, mode)`,
which excludes depth. So "move this leg to 50" has two candidate spellings, and they may or may not
be the same operation:

| | Wire symbol sent | `depth` field | Proxy subscription key |
| --- | --- | --- | --- |
| **CASE A** logical | `NIFTY…CE` | 50 | same key as the depth-5 subscription |
| **CASE B** recorder-style | `NIFTY…CE:50` | 50 | a *different* key |

CASE A is not expressible by the recorder today (`wire_symbol()` always suffixes above depth 5).
It is probed anyway, because if it works it is the cheaper transition and the adapter should use it.

### Source facts (code, not broker behaviour)

These are read from the repository and are *not* evidence about FYERS. They are why the probe is
shaped the way it is.

| # | Fact | Location |
| --- | --- | --- |
| 1 | The proxy accepts a per-subscribe `depth` parameter, defaulting to 5 | `websocket_proxy/server.py:1177` |
| 2 | It forwards that depth to the adapter | `websocket_proxy/server.py:1226` |
| 3 | The per-symbol reply carries `depth`, taken from the adapter's `actual_depth` and **falling back to the requested value** | `websocket_proxy/server.py:1254` |
| 4 | The overall reply is `success` / `partial`, computed from a per-symbol success flag | `websocket_proxy/server.py:1216,1274` |
| 5 | The client dispatcher handles `unsubscribe` and `unsubscribe_all` | `websocket_proxy/server.py:735` |
| 6 | A subscription is keyed `(symbol, exchange, mode)` — depth is **not** part of the identity | `websocket_proxy/server.py:74,1244` |
| 7 | The recorder sends depth twice: `symbol = wire_symbol(symbol, depth)` **and** `"depth": requested_depth` | `market_depth_recorder/websocket_client.py:558-563,662-666` |
| 8 | `wire_symbol()` appends `:50` only when `requested_depth > 5` | `market_depth_recorder/websocket_client.py:198-200` |
| 9 | The subscribe ack is **two-level**: an aggregate `status` plus per-leg entries under `subscriptions[]`; there is **no top-level depth field at all** | `websocket_proxy/server.py:1246-1256,1272-1280` |
| 10 | The unsubscribe ack mirrors it, with per-leg entries under `successful[]` / `failed[]` | `websocket_proxy/server.py` `unsubscribe_client` |
| 11 | A **successful** ack still carries an informational `message` ("Subscription processing complete") | `websocket_proxy/server.py:1272-1280` |
| 12 | The market-data frame is an envelope — `{type, symbol, exchange, mode, data}` — and the book sits at **`data.depth`**, one level down | `websocket_proxy/server.py:1948-1954`; confirmed by the recorder's own reader `websocket_client.py:679-688` |
| 13 | A client-supplied `request_id` is echoed back in the ack, enabling per-request correlation | `websocket_proxy/server.py` `subscribe_client` / `unsubscribe_client` (issue #1376) |

Fact 3 is the one that most easily produces a false positive: **a reply saying `depth: 50` may be
nothing more than the proxy echoing the request back.** It is therefore recorded as *reported*
depth and never as delivered depth.

Facts 9-13 were established in the **pre-market review of 2026-08-26**, after F7A was committed and
before any live run. They corrected three real defects in the harness, all of the same kind: the
harness had been written against an *assumed* frame shape, and its tests asserted the same
assumption, so the two agreed with each other and disagreed with the wire.

| Defect | Effect had the live run gone ahead | Fixed by |
| --- | --- | --- |
| Book read at `packet["depth"]` instead of `packet["data"]["depth"]` (fact 12) | **`observed` would have been `None` for every packet** — every case UNKNOWN, the session spent proving nothing | `count_depth_levels` unwraps the envelope, still accepting a flat payload |
| Reported depth read at the top level, where the ack has no depth field (fact 9) | `reported` always `None`; the acknowledgement question unanswerable | `parse_subscribe_ack` reads the per-leg entry; `per_leg_entries()` exposes both levels |
| Informational `message` treated as an error (fact 11) | Every successful result stamped with a false error | a `message` is an error only on a non-success status or a failed per-leg entry |

Fact 13 was then adopted so an ack is matched to its request by an echoed `request_id` rather than
by arrival order alone; `ack_correlated=` is recorded per result, and a `False` marks a weaker match.
None of this changes what the probe is willing to *conclude* — the confidence lattice is untouched.

---

## 2. Date and time of the live run

| Field | Value |
| --- | --- |
| Date (IST) | UNKNOWN — LIVE PROBE PENDING |
| Start / end time (IST) | UNKNOWN — LIVE PROBE PENDING |
| Inside 09:15-15:30 session | UNKNOWN — LIVE PROBE PENDING |
| Expiry-day run? | UNKNOWN — LIVE PROBE PENDING |

## 3. Environment

| Field | Value |
| --- | --- |
| Host OS | UNKNOWN — LIVE PROBE PENDING |
| Python | UNKNOWN — LIVE PROBE PENDING |
| Proxy URL | UNKNOWN — LIVE PROBE PENDING (default `ws://127.0.0.1:8765`) |
| Probe tool + revision | `tools/fyers/depth_transition_probe.py`, git rev UNKNOWN — LIVE PROBE PENDING |
| Evidence JSON | UNKNOWN — LIVE PROBE PENDING |
| Recorder running concurrently? | UNKNOWN — LIVE PROBE PENDING (should be **no**; it would consume premium slots) |

## 4. OpenAlgo version

| Field | Value |
| --- | --- |
| OpenAlgo git revision | UNKNOWN — LIVE PROBE PENDING |
| TBT channel patch applied? | UNKNOWN — LIVE PROBE PENDING (see `OPENALGO_PATCH.md` §8) |
| `websocket_proxy/server.py` matches the source facts in §1 | UNKNOWN — LIVE PROBE PENDING (re-verify at run time; line numbers above are from 2026-08-26) |

## 5. FYERS session status

| Field | Value |
| --- | --- |
| Login performed after the 03:00 IST token rollover | UNKNOWN — LIVE PROBE PENDING |
| `feed_token` populated | UNKNOWN — LIVE PROBE PENDING |
| Other active broker connections at run time | UNKNOWN — LIVE PROBE PENDING |
| Premium (TBT) slots already in use before the probe | UNKNOWN — LIVE PROBE PENDING |

No credential value appears in this document or in the evidence JSON; the probe redacts any
parameter whose key looks like a secret, and refuses to build a request that would carry one.

## 6. Instruments

| Field | Value |
| --- | --- |
| Instrument 1 (logical symbol) | UNKNOWN — LIVE PROBE PENDING |
| Instrument 2 (logical symbol, optional) | UNKNOWN — LIVE PROBE PENDING |
| Exchange | NFO (fixed: 50-level is NSE/NFO-only; BFO/SENSEX cannot answer this question) |
| Expiry | UNKNOWN — LIVE PROBE PENDING (pick a current, liquid, non-expiring-today contract) |
| Liquidity sanity check at run time | UNKNOWN — LIVE PROBE PENDING |

Maximum two instruments, enforced in code (`MAX_INSTRUMENTS_HARD_CAP = 2`).

---

## 7. Standard subscription (depth = 5) — the baseline

Establishes that the path works at all before anything is transitioned. If this does not deliver
market data, **nothing further in this document is meaningful** and the run must be abandoned.

| Question | Result |
| --- | --- |
| Request accepted (`status`) | UNKNOWN — LIVE PROBE PENDING |
| Reported depth in the ack (`actual_depth`) | UNKNOWN — LIVE PROBE PENDING |
| Market data received | UNKNOWN — LIVE PROBE PENDING |
| **Observed** levels in delivered packets | UNKNOWN — LIVE PROBE PENDING |
| Wire symbol packets arrived under | UNKNOWN — LIVE PROBE PENDING |
| Confidence | UNKNOWN |

## 8. Same-symbol 5 -> 50 (CASE A) — case `C2_5_50_logical`

Re-subscribe the **same logical symbol** with `depth: 50`, no suffix change.

| Question | Result |
| --- | --- |
| Request form sent | `subscribe` · symbol `SYMBOL` · depth 50 · mode 3 |
| Response status | UNKNOWN — LIVE PROBE PENDING |
| Reported depth | UNKNOWN — LIVE PROBE PENDING |
| **Observed** market-data depth after | UNKNOWN — LIVE PROBE PENDING |
| Prior depth-5 subscription still active | UNKNOWN — LIVE PROBE PENDING |
| Duplicate subscription created | UNKNOWN — LIVE PROBE PENDING |
| Premium capacity consumed | UNKNOWN — LIVE PROBE PENDING |
| Acknowledgement distinguishable from an echo | UNKNOWN — LIVE PROBE PENDING |
| Transient data loss during the change | UNKNOWN — LIVE PROBE PENDING |
| **Outcome** | UNKNOWN — LIVE PROBE PENDING |
| Confidence | UNKNOWN |

## 9. Recorder-style `:50` 5 -> 50 (CASE B) — case `C3_5_50_suffixed`

Subscribe `SYMBOL:50` with `depth: 50` while `SYMBOL` at depth 5 is still subscribed. Under source
fact 6 these are two different subscription keys, so this may create a second stream rather than
change one — which is exactly what §8's `duplicate_subscription` row is there to catch.

| Question | Result |
| --- | --- |
| Request form sent | `subscribe` · symbol `SYMBOL:50` · depth 50 · mode 3 |
| Response status | UNKNOWN — LIVE PROBE PENDING |
| Reported depth | UNKNOWN — LIVE PROBE PENDING |
| **Observed** market-data depth after | UNKNOWN — LIVE PROBE PENDING |
| Packets still arriving under the unsuffixed symbol | UNKNOWN — LIVE PROBE PENDING |
| Packets arriving under both spellings (duplicate) | UNKNOWN — LIVE PROBE PENDING |
| Premium capacity consumed | UNKNOWN — LIVE PROBE PENDING |
| Transient data loss during the change | UNKNOWN — LIVE PROBE PENDING |
| **Outcome** | UNKNOWN — LIVE PROBE PENDING |
| Confidence | UNKNOWN |

## 10. Premium -> standard, 50 -> 5 — cases `C5_50_5_logical`, `C7_50_5_logical_unsub`

The direction that matters for **releasing** capacity. If a demotion does not actually free a
premium slot, the allocator's release-before-claim ordering (F6) buys nothing on the wire.

| Question | Bare re-subscribe (`C5`) | Unsubscribe-then-subscribe (`C7`) |
| --- | --- | --- |
| Response status | UNKNOWN — LIVE PROBE PENDING | UNKNOWN — LIVE PROBE PENDING |
| Reported depth | UNKNOWN — LIVE PROBE PENDING | UNKNOWN — LIVE PROBE PENDING |
| **Observed** depth after | UNKNOWN — LIVE PROBE PENDING | UNKNOWN — LIVE PROBE PENDING |
| Premium slot actually released | UNKNOWN — LIVE PROBE PENDING | UNKNOWN — LIVE PROBE PENDING |
| Still receiving data at 5 levels | UNKNOWN — LIVE PROBE PENDING | UNKNOWN — LIVE PROBE PENDING |
| Coverage lost entirely | UNKNOWN — LIVE PROBE PENDING | UNKNOWN — LIVE PROBE PENDING |
| **Outcome** | UNKNOWN — LIVE PROBE PENDING | UNKNOWN — LIVE PROBE PENDING |

## 11. Premium -> premium, 50 -> 50 — case `C4_50_50_logical`

The idempotence question: does re-requesting a depth a leg already has cost anything? If a repeated
premium request consumes a second slot, the adapter must suppress no-op re-subscribes.

| Question | Result |
| --- | --- |
| Response status | UNKNOWN — LIVE PROBE PENDING |
| **Observed** depth unchanged | UNKNOWN — LIVE PROBE PENDING |
| Second premium slot consumed | UNKNOWN — LIVE PROBE PENDING |
| Duplicate subscription created | UNKNOWN — LIVE PROBE PENDING |
| Data interrupted | UNKNOWN — LIVE PROBE PENDING |
| **Outcome** | UNKNOWN — LIVE PROBE PENDING |

Case `C1_5_5_logical` runs the same idempotence check at standard depth and is the control: whatever
a repeat request does at 5 levels is the baseline against which `C4`'s cost is read.

## 12. Unsubscribe

Source fact 5 says the proxy *dispatches* `unsubscribe`. That is a code fact about routing; it says
nothing about whether the broker leg is genuinely released or a premium slot returned.

| Question | Result |
| --- | --- |
| Operation attempted | UNKNOWN — LIVE PROBE PENDING |
| Request accepted | UNKNOWN — LIVE PROBE PENDING |
| Market data actually stopped afterwards | UNKNOWN — LIVE PROBE PENDING |
| Premium slot returned | UNKNOWN — LIVE PROBE PENDING |
| Required before a depth change, or optional | UNKNOWN — LIVE PROBE PENDING |
| Which spelling must be unsubscribed (`SYMBOL` vs `SYMBOL:50`) | UNKNOWN — LIVE PROBE PENDING |
| **Supported** | UNKNOWN — LIVE PROBE PENDING |

An accepted unsubscribe with no observed effect stays UNKNOWN, not "supported". An untested
unsubscribe stays UNKNOWN, not "unsupported".

## 13. Acknowledgement and per-leg feedback

| Question | Result |
| --- | --- |
| Per-symbol acknowledgement present | UNKNOWN — LIVE PROBE PENDING |
| `actual_depth` present and distinguishable from the echoed request | UNKNOWN — LIVE PROBE PENDING |
| Per-leg **failure** reported, or only an aggregate `partial` | UNKNOWN — LIVE PROBE PENDING |
| A rejected premium request identifiable as such | UNKNOWN — LIVE PROBE PENDING |
| Any asynchronous later notification of a downgrade | UNKNOWN — LIVE PROBE PENDING |
| Ack latency (median / max) | UNKNOWN — LIVE PROBE PENDING |

This section decides whether the framework can ever have a real per-leg acknowledgement ledger, or
whether F6's snapshot-derived `pending`/`failed` (Option A) remains the only honest observability.

## 14. Reconnect

| Question | Result |
| --- | --- |
| Reconnect exercised | UNKNOWN — LIVE PROBE PENDING |
| Subscriptions restored automatically | UNKNOWN — LIVE PROBE PENDING |
| Premium depth restored, or silently downgraded to 5 | UNKNOWN — LIVE PROBE PENDING |
| Re-subscribe required to regain 50 | UNKNOWN — LIVE PROBE PENDING |
| Time to first packet after reconnect | UNKNOWN — LIVE PROBE PENDING |
| Premium slots correctly accounted after reconnect | UNKNOWN — LIVE PROBE PENDING |

A silent downgrade to 5 on reconnect would be the most dangerous possible answer: the recorder would
keep writing rows that *look* like premium coverage while the book behind them is shallow. If the
answer is UNKNOWN or "silently downgraded", the adapter must re-observe depth after every reconnect
rather than trusting its own state.

## 15. Premium-capacity behaviour

| Question | Result |
| --- | --- |
| Premium slots in use before the probe | UNKNOWN — LIVE PROBE PENDING |
| Slots consumed by a 5 -> 50 transition (CASE A) | UNKNOWN — LIVE PROBE PENDING |
| Slots consumed by a 5 -> 50 transition (CASE B) | UNKNOWN — LIVE PROBE PENDING |
| Slots released by a 50 -> 5 transition | UNKNOWN — LIVE PROBE PENDING |
| Slots released by an explicit unsubscribe | UNKNOWN — LIVE PROBE PENDING |
| Behaviour at the ceiling (rejection vs silent downgrade) | UNKNOWN — LIVE PROBE PENDING |

**Not measured by deliberately exceeding the limit.** The safety rules forbid driving the broker to
its ceiling, so capacity is inferred from slots freed and consumed on at most two instruments; the
probe records `capacity_delta` as `null` rather than guessing. The frozen `tbt_budget = 15` from
`tbt_concurrency_reconciliation_20260714.md` is the ceiling this reasoning sits under and is not
re-derived here.

---

## 16. Observed facts

*Only results actually seen in delivered market data belong here.*

UNKNOWN — LIVE PROBE PENDING. Nothing has been observed. This section is empty and must stay empty
until a live run fills it.

## 17. Inferences

*Conclusions drawn from observed facts, each labelled with the observation it rests on. An
acknowledgement-only result is an inference, never an observation.*

UNKNOWN — LIVE PROBE PENDING.

## 18. Unknowns

Everything in §7-§15 is currently unknown. Restated explicitly, so that no later reader mistakes an
absent answer for a negative one:

- Whether a bare re-subscribe changes delivered depth — **UNKNOWN**, not "no".
- Whether unsubscribe is required before a depth change — **UNKNOWN**, not "no".
- Whether unsubscribe is supported end to end — **UNKNOWN**, not "unsupported".
- Whether a transition is atomic — **UNKNOWN**.
- Whether a transition consumes an extra premium slot — **UNKNOWN**.
- Whether a transition can lose coverage — **UNKNOWN**.
- Whether reconnect restores premium depth — **UNKNOWN**.
- Whether a per-leg acknowledgement or per-leg failure callback exists — **UNKNOWN**.
- Whether CASE A and CASE B are the same operation — **UNKNOWN**.

## 19. Broker Adapter consequences

The adapter contract is written **from** the answers above; it is not drafted in advance. What can
be said now is only which way each answer would push the design:

| If the live answer is… | …the adapter must |
| --- | --- |
| bare re-subscribe changes depth (CASE A) | expose a single `set_depth(leg, tier)` and let the transition be one operation |
| only CASE B changes depth | treat retiering as *two* subscriptions and own the release of the old spelling |
| unsubscribe is required first | make retiering a two-step release/claim, and surface the gap to the caller |
| a transition is non-atomic | expose the transient window so callers do not treat retiering as free |
| a transition consumes an extra slot | reserve the slot *before* the claim, and hold F6's release-before-claim ordering as a hard requirement |
| reconnect downgrades silently | re-observe delivered depth after every reconnect instead of trusting state |
| no per-leg failure feedback exists | keep F6's snapshot-derived `pending`/`failed` as the only observability, and never add a fake ack ledger |

Whatever the answers, the boundary does not move: **all broker-specific knowledge lives in the
adapter.** `BudgetAllocator`, `DepthAllocator`, `SubscriptionState` and `SubscriptionManager` stay
broker-neutral and consume one logical `tbt_budget` from the capability layer, exactly as
`tbt_budget = 15` is a FYERS capability rather than an architectural constant.

## 20. Final conclusion

**F7 is NOT complete.**

- **F7A — prepared (2026-08-26).** The probe harness, its broker-neutral data model, 83 offline
  tests, this template and the operator runbook exist and are verified. The harness is inert:
  importing it starts no thread and loads no network client, and a dry run performs no I/O.
- **F7B — pending.** No live measurement has been taken. Every broker-dependent cell above reads
  `UNKNOWN — LIVE PROBE PENDING`.

The Broker Adapter must not be written, and F8 must not begin, until this document's §16 contains
real observations and §20 is replaced by a conclusion drawn from them.

---

## Appendix — how to fill this in

Follow [`depth_transition_probe_runbook_20260826.md`](depth_transition_probe_runbook_20260826.md).
The live run writes an evidence JSON next to this file; transcribe from that JSON, not from memory,
and keep the JSON as the primary record. Each transcribed cell keeps the confidence the JSON gives
it: **OBSERVED** (counted in delivered packets), **INFERRED** (from an acknowledgement), or
**UNKNOWN**. The harness will not upgrade one to another, and neither should a reader.
