# Depth-transition probe — 5 <-> 50 behaviour on the OpenAlgo/FYERS path

**Date prepared:** 2026-08-26 · **Status: F7B COMPLETE — LIVE EVIDENCE RECORDED 2026-08-26** ·
**Method:** to be filled by `tools/fyers/depth_transition_probe.py --live` during a live NSE session.

> **This document is now evidence for the fields marked OBSERVED, and only those.**
> A live run on 2026-08-26 filled in the transition matrix, the unsubscribe question and the
> acknowledgement semantics. Reconnect and premium-capacity behaviour were **not** measured and
> remain `UNKNOWN` — not "no". Every remaining `UNKNOWN` is a question this run did not answer. Do not
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

### Mid-run instrumentation correction (2026-08-26, during the live session)

One further correction was made **during** the live window, and it is recorded here rather than
quietly absorbed. As committed, F7A could measure only whether an unsubscribe was *accepted*: it
sent the frame, parsed the ack, and stopped. PART J asks a second question — whether the broker
subscription is genuinely removed — and the committed harness had no instrument capable of
answering it. Worse, the naive instrument is wrong: observing silence after an unsubscribe proves
nothing on its own, because a quiet market or a dead connection produces the same silence.

`_measure_unsubscribe_effect` was therefore added to `tools/fyers/depth_transition_probe.py`, and
it measures a four-stage sequence with a **control**:

| Stage | Purpose |
| --- | --- |
| observe | establish the leg is delivering (`packets_before`) |
| unsubscribe | the protocol question — is it accepted |
| observe | did delivery stop (`packets_after_unsubscribe`) |
| **re-subscribe, observe** | the control — can the feed still deliver this leg (`packets_after_resubscribe`) |

The verdict rule is deliberately narrow. Packets still arriving after an accepted unsubscribe is
`effect_observed = False`. Silence *followed by a successful resumption* is `effect_observed =
True`. **Silence with no resumption is `None` — UNKNOWN**, because it cannot be attributed. The
premium (`:50`) leg is preferred as the target, since whether a 50-level slot is released is the
question capacity planning needs.

The instrument is what produced §12, so the committed probe now contains the code that produced
the committed evidence, and section 14 of `tests/test_f7_depth_probe_harness.py` covers all four
verdict shapes offline. It reads the feed and sends two frames on the leg it is already measuring;
it adds no instrument, no retry loop and no framework behaviour.

---

## 2. Date and time of the live run

| Field | Value |
| --- | --- |
| Date (IST) | 2026-08-26 (Wednesday) — OBSERVED |
| Start / end time (IST) | 09:34:56 to approximately 09:52 — OBSERVED |
| Inside 09:15-15:30 session | Yes; the tool's own `in_market_session` gate recorded `true` — OBSERVED |
| Expiry-day run? | No. Front NIFTY weekly is 01-SEP-26, six sessions out — OBSERVED |

## 3. Environment

| Field | Value |
| --- | --- |
| Host OS | Windows 11 Pro 10.0.26200 — OBSERVED |
| Python | 3.13.5 — OBSERVED |
| Proxy URL | `ws://127.0.0.1:8765` — OBSERVED |
| Probe tool + revision | `tools/fyers/depth_transition_probe.py` at `61c5bfe` plus the uncommitted §12 unsubscribe-effect measurement added during this run — OBSERVED |
| Evidence JSON | `depth_transition_baseline_20260826.json`, `..._C2_caseA_...`, `..._C3_caseB_...`, `..._C5_...`, `..._C4_...`, `..._unsub_...` (six files, one per invocation) — OBSERVED |
| Recorder running concurrently? | **No** recorder process, but the proxy was **not** idle: `ws_proxy_stats.json` reported `clients_connected: 3` and `total_symbols: 180` from another client throughout. Whether any of those 180 were premium legs was **not** visible — this is a real confound for §15 and is recorded as such rather than assumed away. — OBSERVED (the sharing) / UNKNOWN (its premium composition) |

## 4. OpenAlgo version

| Field | Value |
| --- | --- |
| OpenAlgo git revision | `87ce4d8db` — OBSERVED |
| TBT channel patch applied? | UNKNOWN — not re-verified at run time; no probe result depends on it |
| `websocket_proxy/server.py` matches the source facts in §1 | Yes for facts 9-13, which were re-read from this revision on 2026-08-26 and are corroborated by the live frames — OBSERVED |

## 5. FYERS session status

| Field | Value |
| --- | --- |
| Login performed after the 03:00 IST token rollover | Yes — auth row written 2026-08-26 09:09 IST — OBSERVED |
| `feed_token` populated | No, NULL — and **irrelevant for FYERS**: `broker/fyers/streaming/*.py` authenticates with `get_auth_token(user_id)` (the `auth` column). A NULL `feed_token` is normal here. — SOURCE FACT |
| Other active broker connections at run time | One broker connection, three proxy clients, 180 symbols held by another client — OBSERVED |
| Premium (TBT) slots already in use before the probe | UNKNOWN — the proxy exposes no per-symbol depth-tier count, and PART M forbids discovering it by approaching the ceiling |

No credential value appears in this document or in the evidence JSON; the probe redacts any
parameter whose key looks like a secret, and refuses to build a request that would carry one.

## 6. Instruments

| Field | Value |
| --- | --- |
| Instrument 1 (logical symbol) | `NIFTY01SEP2624300CE` — OBSERVED |
| Instrument 2 (logical symbol, optional) | None. One instrument answered every question; a second would have consumed premium capacity for nothing. — OBSERVED |
| Exchange | NFO (fixed: 50-level is NSE/NFO-only; BFO/SENSEX cannot answer this question) |
| Expiry | 01-SEP-26 weekly, confirmed present in `symtoken` — OBSERVED |
| Liquidity sanity check at run time | 09:34 IST: ltp 187.8, bid 187.35 / ask 187.8, volume 14,495,000. Spot 24344.55, so the leg was near the money and continuously traded. — OBSERVED |

Maximum two instruments, enforced in code (`MAX_INSTRUMENTS_HARD_CAP = 2`).

---

## 7. Standard subscription (depth = 5) — the baseline

Establishes that the path works at all before anything is transitioned. If this does not deliver
market data, **nothing further in this document is meaningful** and the run must be abandoned.

| Question | Result |
| --- | --- |
| Request accepted (`status`) | `success` — OBSERVED |
| Reported depth in the ack (`actual_depth`) | `actual_depth` **absent**; the per-leg entry carried `depth: 5`, which is the echoed request — OBSERVED |
| Market data received | Yes — 9 packets in the first window, 6 in the second — OBSERVED |
| **Observed** levels in delivered packets | **5** — OBSERVED |
| Wire symbol packets arrived under | `NIFTY01SEP2624300CE` (unsuffixed) — OBSERVED |
| Confidence | OBSERVED — requested 5, reported 5 and observed 5 all agree, which is what makes this a usable control for every case below |

## 8. Same-symbol 5 -> 50 (CASE A) — case `C2_5_50_logical`

Re-subscribe the **same logical symbol** with `depth: 50`, no suffix change.

| Question | Result |
| --- | --- |
| Request form sent | `subscribe` · symbol `SYMBOL` · depth 50 · mode 3 |
| Response status | `success` — OBSERVED |
| Reported depth | `50`, from the per-leg entry; `actual_depth` absent — OBSERVED |
| **Observed** market-data depth after | **5** — the book did **not** change — OBSERVED (9 packets) |
| Prior depth-5 subscription still active | Yes. Both requests carry the same wire symbol, so they address one subscription (source fact 6) and it continued delivering. — OBSERVED |
| Duplicate subscription created | No — packets arrived under one wire symbol only — OBSERVED |
| Premium capacity consumed | UNKNOWN — not measurable without approaching the ceiling (PART M) |
| Acknowledgement distinguishable from an echo | **No.** `actual_depth` was absent, so the ack's `depth` field is the request read back. The ack said 50 while the wire delivered 5. — OBSERVED |
| Transient data loss during the change | None observed — delivery was continuous across the request — OBSERVED |
| **Outcome** | `depth_unchanged` — **a bare re-subscribe on the logical symbol does not promote depth** — OBSERVED |
| Confidence | OBSERVED |

## 9. Recorder-style `:50` 5 -> 50 (CASE B) — case `C3_5_50_suffixed`

Subscribe `SYMBOL:50` with `depth: 50` while `SYMBOL` at depth 5 is still subscribed. Under source
fact 6 these are two different subscription keys, so this may create a second stream rather than
change one — which is exactly what §8's `duplicate_subscription` row is there to catch.

| Question | Result |
| --- | --- |
| Request form sent | `subscribe` · symbol `SYMBOL:50` · depth 50 · mode 3 |
| Response status | `success` — OBSERVED |
| Reported depth | `50`, per-leg; `actual_depth` absent — OBSERVED |
| **Observed** market-data depth after | **50** — OBSERVED (33 packets) |
| Packets still arriving under the unsuffixed symbol | **Yes** — 8 packets under `NIFTY01SEP2624300CE` in the same window — OBSERVED |
| Packets arriving under both spellings (duplicate) | **Yes** — 8 under `NIFTY01SEP2624300CE` and 25 under `NIFTY01SEP2624300CE:50`, concurrently. Two live subscriptions, not one promoted subscription. — OBSERVED |
| Premium capacity consumed | UNKNOWN — see §15 |
| Transient data loss during the change | None observed; the depth-5 leg never stopped — OBSERVED |
| **Outcome** | `depth_changed`, 5 -> 50 — **the `:50` spelling is what selects the deep book** — OBSERVED |
| Confidence | OBSERVED |

## 10. Premium -> standard, 50 -> 5 — cases `C5_50_5_logical`, `C7_50_5_logical_unsub`

The direction that matters for **releasing** capacity. If a demotion does not actually free a
premium slot, the allocator's release-before-claim ordering (F6) buys nothing on the wire.

| Question | Bare re-subscribe (`C5`) | Unsubscribe-then-subscribe (`C7`) |
| --- | --- | --- |
| Response status | `success` — OBSERVED | not run as a case |
| Reported depth | `5`, per-leg echo — OBSERVED | not run as a case |
| **Observed** depth after | **50** — the deep book kept flowing — OBSERVED (`:50` leg, 25 packets) | not run as a case |
| Premium slot actually released | **No** — the `:50` leg was still delivering, so nothing was released — OBSERVED | INFERRED yes, from §12: an explicit unsubscribe of the `:50` spelling does stop delivery. The composed demotion was not itself executed. |
| Still receiving data at 5 levels | Yes, on a **new, separate** leg: 13 packets under the unsuffixed symbol — OBSERVED | INFERRED |
| Coverage lost entirely | No — OBSERVED | INFERRED no |
| **Outcome** | `depth_unchanged`, 50 -> 50: **a bare re-subscribe at depth 5 does not demote; it adds a second 5-level leg beside the still-live 50-level one** — OBSERVED | UNKNOWN — not executed as a single case |

## 11. Premium -> premium, 50 -> 50 — case `C4_50_50_logical`

The idempotence question: does re-requesting a depth a leg already has cost anything? If a repeated
premium request consumes a second slot, the adapter must suppress no-op re-subscribes.

| Question | Result |
| --- | --- |
| Response status | `success` — OBSERVED |
| **Observed** depth unchanged | Yes, 50 -> 50 — OBSERVED (26 then 37 packets) |
| Second premium slot consumed | UNKNOWN. The repeat request used the **logical** spelling, which per §8 yields a 5-level leg, so this case did not in fact ask for a second premium leg. |
| Duplicate subscription created | **Yes** — 24 packets under `:50` and 13 under the unsuffixed symbol, concurrently — OBSERVED |
| Data interrupted | No — OBSERVED |
| **Outcome** | `depth_unchanged`. Note the case is weaker than its name suggests: the second request was logical, so it re-tested §8 rather than a true 50 -> 50 repeat on the same spelling. A same-spelling `:50` repeat was **not** run. — OBSERVED, with the scope limit stated |

Case `C1_5_5_logical` runs the same idempotence check at standard depth and is the control: whatever
a repeat request does at 5 levels is the baseline against which `C4`'s cost is read.

## 12. Unsubscribe

Source fact 5 says the proxy *dispatches* `unsubscribe`. That is a code fact about routing; it says
nothing about whether the broker leg is genuinely released or a premium slot returned.

| Question | Result |
| --- | --- |
| Operation attempted | Yes, on the premium `NIFTY01SEP2624300CE:50` leg — OBSERVED |
| Request accepted | Yes, `status: success` — OBSERVED (this is the *protocol* answer only) |
| Market data actually stopped afterwards | **Yes** — 20 packets before, **0** in the window after — OBSERVED |
| Control that makes that silence meaningful | The same leg was re-subscribed and delivered **21** packets again. The feed was demonstrably alive, so the silence is attributable to the unsubscribe and not to a quiet market or a dead connection. — OBSERVED |
| Premium slot returned | UNKNOWN — delivery stopping is not the same as slot accounting, and the proxy exposes no slot counter |
| Required before a depth change, or optional | **Not required to obtain depth 50** — §9 reached 50 without it. It **is** required to release the superseded spelling, since §9 and §10 both leave the old leg live. — OBSERVED |
| Which spelling must be unsubscribed (`SYMBOL` vs `SYMBOL:50`) | The exact wire symbol. Unsubscribing `…:50` stopped the `…:50` leg; the two spellings are independent subscriptions. — OBSERVED |
| **Supported** | **Yes — end to end, with the effect observed rather than inferred from acceptance** — OBSERVED |

An accepted unsubscribe with no observed effect stays UNKNOWN, not "supported". An untested
unsubscribe stays UNKNOWN, not "unsupported".

The re-subscribe control in row 4 comes from `_measure_unsubscribe_effect`, added mid-run — see
*Mid-run instrumentation correction* in §1. Without it, row 3 alone would have been silence of
unknown cause and this section would have read UNKNOWN.

## 13. Acknowledgement and per-leg feedback

| Question | Result |
| --- | --- |
| Per-symbol acknowledgement present | **Yes** — every ack carried exactly one `subscriptions[]` entry with `symbol`, `status` and `depth`, and every ack correlated to its request via the echoed `request_id` (`ack_correlated=True` on all 14 subscribes) — OBSERVED |
| `actual_depth` present and distinguishable from the echoed request | **No.** `actual_depth` was **absent in every ack**, so the per-leg `depth` is the request read back. §8 is the proof: the ack said `depth: 50` while the wire delivered 5 levels. **The acknowledgement carries no information about delivered depth.** — OBSERVED |
| Per-leg **failure** reported, or only an aggregate `partial` | UNKNOWN — no request was rejected, so no failure path was exercised. Inducing one would have meant a deliberately invalid or over-capacity request, which PART M rules out. |
| A rejected premium request identifiable as such | UNKNOWN — same reason |
| Any asynchronous later notification of a downgrade | **None seen.** In §8, delivered depth was 5 while the ack claimed 50, and no later frame ever corrected it. A silent downgrade is silent. — OBSERVED |
| Ack latency (median / max) | subscribe: median 1 ms, max 651 ms (n=14). unsubscribe: median 581 ms, max 10,008 ms (n=12) — the maximum is a read deadline expiring, not a slow ack: one cleanup unsubscribe returned no ack at all within its window. — OBSERVED |
| Unacknowledged unsubscribe | One cleanup unsubscribe (`…:50`, seq 10001) recorded `status: None` — no ack arrived before the deadline. It occurred while heavy 50-level traffic was in flight. Recorded because an unreliable ack is itself a design input; not investigated further. — OBSERVED |

This section decides whether the framework can ever have a real per-leg acknowledgement ledger, or
whether F6's snapshot-derived `pending`/`failed` (Option A) remains the only honest observability.

## 14. Reconnect

| Question | Result |
| --- | --- |
| Reconnect exercised | **No** — and deliberately so. PART L permits a reconnect test only if safely executable. The proxy was shared with another live client holding 180 symbols; forcing a broker reconnect would have disrupted a running system that is not this probe's to disturb. |
| Subscriptions restored automatically | UNKNOWN — not measured |
| Premium depth restored, or silently downgraded to 5 | UNKNOWN — not measured. **This is the highest-value open question**, because §13 establishes that a downgrade would produce no acknowledgement, no error and no notification — it would be visible only by counting levels in delivered packets. |
| Re-subscribe required to regain 50 | UNKNOWN — not measured |
| Time to first packet after reconnect | UNKNOWN — not measured |
| Premium slots correctly accounted after reconnect | UNKNOWN — not measured |

A silent downgrade to 5 on reconnect would be the most dangerous possible answer: the recorder would
keep writing rows that *look* like premium coverage while the book behind them is shallow. If the
answer is UNKNOWN or "silently downgraded", the adapter must re-observe depth after every reconnect
rather than trusting its own state.

## 15. Premium-capacity behaviour

| Question | Result |
| --- | --- |
| Premium slots in use before the probe | UNKNOWN — no slot counter is exposed, and another client held 180 symbols of unknown composition |
| Slots consumed by a 5 -> 50 transition (CASE A) | UNKNOWN — but CASE A never reached 50 levels at all (§8), so on the evidence it plausibly consumed none |
| Slots consumed by a 5 -> 50 transition (CASE B) | UNKNOWN — at least one leg began delivering 50 levels, so a slot was evidently used; the count is not visible |
| Slots released by a 50 -> 5 transition | **None** — the premium leg stayed live (§10) — OBSERVED |
| Slots released by an explicit unsubscribe | UNKNOWN as accounting; **delivery provably stopped** (§12). These are not the same claim and are kept apart. |
| Behaviour at the ceiling (rejection vs silent downgrade) | UNKNOWN — **and deliberately not tested.** Establishing it means approaching or crossing the broker ceiling on a live account, which PART M forbids. UNKNOWN here means untested, never "no". |

**Not measured by deliberately exceeding the limit.** The safety rules forbid driving the broker to
its ceiling, so capacity is inferred from slots freed and consumed on at most two instruments; the
probe records `capacity_delta` as `null` rather than guessing. The frozen `tbt_budget = 15` from
`tbt_concurrency_reconciliation_20260714.md` is the ceiling this reasoning sits under and is not
re-derived here.

---

## 16. Observed facts

*Only results actually seen in delivered market data belong here.*

Each line below was seen in delivered market data on 2026-08-26, in session, on
`NIFTY01SEP2624300CE` (NFO), mode 3.

1. **Depth is a property of the wire symbol, not a mutable property of a subscription.**
   `SYMBOL` delivers a 5-level book; `SYMBOL:50` delivers a 50-level book. The two are independent
   subscriptions that stream **simultaneously** (§9: 8 packets under one spelling, 25 under the
   other, in the same window).
2. **The `depth` request parameter does not change delivered depth.** `SYMBOL` + `depth: 50` was
   accepted with `status: success` and `depth: 50`, and delivered **5 levels** across 9 packets
   (§8).
3. **There is no in-place transition.** Neither promotion (§8) nor demotion (§10) altered an
   existing leg. Both merely added or left legs: requesting depth 5 on the plain spelling while
   `:50` was live produced a second leg and left the deep one running.
4. **The acknowledgement carries no information about delivered depth.** `actual_depth` was absent
   from every ack, so the per-leg `depth` is the request echoed back. In §8 the ack claimed 50
   while the wire delivered 5, and nothing ever corrected it (§13).
5. **Unsubscribe works end to end.** The `:50` leg delivered 20 packets, then **0** after an
   accepted unsubscribe, then **21** after re-subscribing — the re-subscribe being the control that
   makes the silence attributable (§12).
6. **Per-request correlation is reliable.** Every one of the 14 subscribes correlated to its ack by
   the echoed `request_id`, with exactly one per-leg entry each (§13).
7. **No transition caused a data gap.** In every case the pre-existing leg kept delivering
   throughout (§8-§11).

## 17. Inferences

*Conclusions drawn from observed facts, each labelled with the observation it rests on. An
acknowledgement-only result is an inference, never an observation.*

- **Promotion and demotion are add/remove pairs, not edits.** From observations 1-3 and 5: to
  reach 50 you subscribe `SYMBOL:50`; to leave 50 you unsubscribe `SYMBOL:50`. Nothing else
  observed changes a leg's depth.
- **A retier is therefore never atomic, and briefly doubles subscriptions.** From 1, 3 and 7:
  the old leg keeps delivering until it is explicitly released, so there is an interval in which
  both spellings are live. This is the opposite of a gap — it is an overlap, and it is what
  consumes capacity twice if the release is forgotten.
- **A demotion that only re-subscribes is a capacity leak.** From 3 and observation in §10: the
  premium leg survives, so the slot is never returned. Any implementation that "demotes" by
  subscribing at depth 5 would silently accumulate premium legs.
- **Delivered depth can only be established by counting levels in packets.** From 4 and §13: no
  status, field, error or later notification distinguishes a served premium request from a
  silently downgraded one.
- **`feed_token` is irrelevant on this path.** Source fact plus a successful live run with
  `feed_token` NULL throughout.

## 18. Unknowns

These were **not** answered by this run. Restated explicitly so that no later reader mistakes an
absent answer for a negative one:

- **Whether reconnect restores premium depth or silently downgrades to 5** — **UNKNOWN**, not "no".
  Not exercised: the proxy was shared with a live client holding 180 symbols, and PART L permits a
  reconnect test only when safely executable. This is the most consequential open question, because
  §13 shows a downgrade would be undetectable except by counting levels.
- **Premium slot accounting** — how many slots a promotion consumes, and whether an unsubscribe
  returns one — **UNKNOWN**. No counter is exposed, and establishing it empirically means
  approaching the ceiling, which PART M forbids.
- **Behaviour at the ceiling** (rejection vs silent downgrade) — **UNKNOWN**, deliberately untested.
- **Whether a per-leg *failure* is reported, or only an aggregate `partial`** — **UNKNOWN**. No
  request failed, so the failure path was never exercised. Per-leg *success* entries do exist (§13).
- **Whether a same-spelling `:50` -> `:50` repeat is idempotent** — **UNKNOWN**. §11's second
  request used the logical spelling, so a true same-spelling repeat was not run.
- **Why one cleanup unsubscribe returned no acknowledgement** (§13) — **UNKNOWN**, observed once.
- **Whether any of this generalises beyond NIFTY/NFO** — **UNKNOWN**. One instrument, one exchange,
  one session. BFO/SENSEX cannot reach 50 levels at all and was correctly not used.

**Answered by this run, and no longer unknown:** whether a bare re-subscribe changes depth (no —
§8); whether unsubscribe is supported end to end (yes — §12); whether a transition is atomic (no,
it is an overlap — §17); whether a transition loses coverage (no — §16.7); whether CASE A and
CASE B are the same operation (**no — they are decisively different**, §8 vs §9).

## 19. Broker Adapter consequences

The adapter contract is written **from** the answers above. The table below was drafted before the
run as a set of conditionals; the live evidence has now selected among them, and the selected rows
are marked. It is kept intact rather than rewritten, so the reasoning remains auditable.

| If the live answer is… | …the adapter must |
| --- | --- |
| bare re-subscribe changes depth (CASE A) | expose a single `set_depth(leg, tier)` and let the transition be one operation — **RULED OUT by §8** |
| only CASE B changes depth | treat retiering as *two* subscriptions and own the release of the old spelling — **SELECTED by §9 + §10** |
| unsubscribe is required first | make retiering a two-step release/claim, and surface the gap to the caller — **PARTIALLY SELECTED**: not required *before* the claim (§9 reached 50 without it), but mandatory *after* it, or the old leg leaks (§10, §12) |
| a transition is non-atomic | expose the transient window so callers do not treat retiering as free — **SELECTED**, though the window is an **overlap**, not a gap (§16.7) |
| a transition consumes an extra slot | reserve the slot *before* the claim, and hold F6's release-before-claim ordering as a hard requirement — **UNRESOLVED** (§15); F6's ordering is retained as the conservative choice |
| reconnect downgrades silently | re-observe delivered depth after every reconnect instead of trusting state — **UNRESOLVED** (§14); §13 shows a downgrade would be invisible to acks, so re-observation is retained as the conservative choice |
| no per-leg failure feedback exists | keep F6's snapshot-derived `pending`/`failed` as the only observability, and never add a fake ack ledger — **SELECTED for depth**: per-leg *success* entries exist but carry no `actual_depth`, so they cannot confirm a tier (§13) |

**The resulting contract, stated positively.** All of it OBSERVED except where noted:

1. `promote(leg)` subscribes the `:50` spelling; `demote(leg)` **unsubscribes** it. Depth is never
   an argument to an edit, because no edit exists.
2. Every promotion owns a matching release of the superseded spelling. Skipping it does not fail —
   it leaks a live leg, silently.
3. A retier passes through a state where both spellings are live. The adapter must expose that
   overlap, and must not report a retier complete until the release is done.
4. The adapter must **never** treat an acknowledgement as confirmation of tier. `actual_depth` does
   not exist on this path; only counted levels in delivered packets establish depth.
5. Because slot accounting (§15) and reconnect behaviour (§14) are unresolved, the adapter keeps
   the conservative posture: release before claim, and re-observe delivered depth after reconnect.
   Both are retained on the grounds that the evidence does not permit relaxing them — not on the
   grounds that the evidence supports them.

Whatever the answers, the boundary does not move: **all broker-specific knowledge lives in the
adapter.** `BudgetAllocator`, `DepthAllocator`, `SubscriptionState` and `SubscriptionManager` stay
broker-neutral and consume one logical `tbt_budget` from the capability layer, exactly as
`tbt_budget = 15` is a FYERS capability rather than an architectural constant.

## 20. Final conclusion

**F7 is complete for the questions it set out to answer, and explicitly incomplete for two.**

- **F7A — prepared (2026-08-26).** The probe harness, its broker-neutral data model, 93 offline
  tests, this document and the operator runbook exist and are verified. The harness is inert:
  importing it starts no thread and loads no network client, and a dry run performs no I/O.
- **F7B — measured (2026-08-26, 09:34-09:52 IST).** Six live invocations on one NFO option, one
  case per invocation so that no case could contaminate the next. Every transition verdict rests on
  counted levels in delivered packets, never on an acknowledgement.

**The decisive result:** CASE A and CASE B are **not** the same operation. `SYMBOL` + `depth: 50`
is acknowledged as `success` with `depth: 50` and delivers **5 levels**; `SYMBOL:50` delivers 50.
Had the harness trusted the acknowledgement — as it would have before the pre-market fix — this run
would have concluded the exact opposite of the truth. The `depth` parameter is inert on this path;
the `:50` suffix is the mechanism.

**Deliberately not established:** reconnect depth restoration (§14) and premium slot accounting
(§15). Both were unsafe to measure — the first would have disrupted a shared live proxy, the second
requires approaching the broker ceiling. They remain **UNKNOWN**, which means untested, not "no".
The adapter therefore keeps its conservative posture in both areas rather than optimising against
evidence that does not exist.

The Broker Adapter contract in §19 follows from §16-§17. F8 must not begin until that adapter is
written and reviewed.

---

## Appendix — how to fill this in

Follow [`depth_transition_probe_runbook_20260826.md`](depth_transition_probe_runbook_20260826.md).
The live run writes an evidence JSON next to this file; transcribe from that JSON, not from memory,
and keep the JSON as the primary record. Each transcribed cell keeps the confidence the JSON gives
it: **OBSERVED** (counted in delivered packets), **INFERRED** (from an acknowledgement), or
**UNKNOWN**. The harness will not upgrade one to another, and neither should a reader.
