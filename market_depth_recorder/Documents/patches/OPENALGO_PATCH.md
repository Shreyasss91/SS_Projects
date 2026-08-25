# OpenAlgo Patch — FYERS TBT channel spread (P10-A)

**Status:** applied to the working tree (2026-07-06) and **kept applied**; the P10-E "live validation"
(2026-07-14) was later shown to be a **measurement artifact** — see §8. The patch is harmless and its
channel-resume plumbing is correct, but it buys **`tbt_budget = 15`, not 250**. Reference diff:
`Documents/patches/openalgo_fyers_tbt_channels.patch` (regenerated 2026-08-25 after the comment-block
correction; the diff is comment-only relative to the 2026-07-06 original).

> ⚠️ **SUPERSEDED PREMISE — read §8 first.** This patch was built on the assumption that FYERS TBT allows
> *5 symbols **per channel*** (→ 250 per connection). The **official FYERS TBT docs, a single-connection
> probe, a multi-connection probe, and a re-read of both live raws all disprove that**: the cap is **5
> Market-Depth symbols per _connection_**, with **3 connections per app per user** and **50 channels per
> connection that are a pause/resume grouping, not extra capacity**. The channel-spread patch therefore does
> **not** raise the ceiling. The real, confirmed ceiling is **`tbt_budget = 15` (3 × 5)** — a full NIFTY
> chain at 50-level is **not achievable**; reaching 15 needs the **hybrid** (near-ATM @50 + rest @5) over a
> multi-connection broker layer. §1–§7 below are preserved as the original reasoning and every stale claim
> in them carries an inline `→ SUPERSEDED` marker; **§8 is the authoritative correction.** This protocol
> layer is **FROZEN unless new external evidence emerges**. Canonical evidence:
> `Documents/patches/tbt_concurrency_reconciliation_20260714.md`.

> This patch lives in a file **outside** the `market_depth_recorder/` package — it modifies the OpenAlgo
> platform. It is a deliberate, user-authorized **scope exception** (the recorder is otherwise
> broker-agnostic and never edits the platform). Keep it minimal and documented so it survives upgrades.

## 1. What problem it fixes

FYERS' 50-level TBT depth feed caps at **5 symbols per channel** (broker error: *"symbol count exceeds
limit: 5, please unsubscribe few symbols before resuming the channel"*). The feed exposes **channels
1–50**. **→ SUPERSEDED (§8): the cap is per _connection_, not per channel** — the broker's wording
("resuming *the channel*") was misread as a per-channel limit. The bug being fixed here is real either way
(pinning to channel `"1"` is wrong), but the ceiling it lifts is 5 → 15 across 3 connections, not 5 → 250. OpenAlgo's FYERS adapter, however, **hardcoded `channel="1"`** for *every* 50-depth subscription
(`broker/fyers/streaming/fyers_websocket_adapter.py`, old lines 682/686), so the 6th 50-depth symbol
onward was silently rejected and the whole channel stalled → *"TBT data stall … Forcing reconnect"* in a
loop. Effect on the recorder (P9): 80 NIFTY `:50` legs → **NIFTY captured zero depth**; SENSEX (non-TBT
5-level HSM) was unaffected. Details: `Documents/patches/Phase9_notes.md` §3.

## 2. What the patch does

Packs 50-depth subscriptions **5 per channel across channels 1–50** instead of pinning to channel 1,
lifting the effective ceiling from **5 → 250** symbols. **(❌ Disproven — the real cap is 5 per _connection_,
not per channel; the spread does not lift it. See §8.)**

- New class constants `TBT_SYMBOLS_PER_CHANNEL = 5`, `TBT_MAX_CHANNELS = 50`.
- New helper `_assign_tbt_channel(subscription_key)`:
  - **Re-subscribing an existing symbol reuses its stored channel** — so reconnects don't renumber a live
    symbol (the TBT client resubscribes per its own `subscriptions[channel]` state).
  - A **new** symbol fills the lowest-numbered channel with a free (< 5) slot.
  - Returns `None` when all 250 slots are used → the caller logs a clear `ERROR` and returns `False`
    (no silent starvation). **→ SUPERSEDED (§8): this 250 bound is unreachable dead code** — FYERS refuses
    the 6th Market-Depth symbol on a connection long before it is hit. Left in place deliberately:
    correcting it to 15 is a *behavior* change to platform code, and the budget belongs in the
    broker-capability layer, not hardcoded in the adapter.
- `_subscribe_tbt_depth` now stores and subscribes with the assigned channel (was `"1"`), and logs the
  channel used.

**Concurrency:** `_subscribe_tbt_depth` is always called under `self.lock` (held from
`subscribe()`'s `with self.lock:` through the mode-3 branch), so the channel count/assign is race-free —
no new lock is taken (taking the non-reentrant `self.lock` again would deadlock).

**Downstream already handles multi-channel:** the TBT client resumes each newly-used channel on first
subscribe (`fyers_tbt_websocket.py::_flush_subscribe_batch` → `switch_channel(resume_channels=[…])`) and
resubscribes per channel on reconnect. No client change needed.

## 3. Pro / cons analysis (why this over the alternatives)

> **→ SUPERSEDED (§8): the "Ceiling" column below is wrong for A and B.** Both were costed at 250; the
> true ceiling for either is **15** (3 connections × 5 per connection). The *verdict* is unchanged — A is
> still chosen, because the correction lowers A and B **equally** and B's objections (vendoring ~1000 LOC,
> breaking the broker-agnostic contract, duplicate token/session management) all still stand. What changes
> is that A no longer delivers a full chain, which is why the **hybrid** is now the design.

| Option | Ceiling (as costed) | Ceiling (true, §8) | Effort | Keeps recorder broker-agnostic | Token/session mgmt | Verdict |
|---|---|---|---|---|---|---|
| **A. Patch OpenAlgo channels (this)** | 250 ❌ | **15** | ~35 lines, 1 file | ✅ yes | stays in OpenAlgo | **chosen** |
| B. Direct FYERS connection from recorder | 250 ❌ | **15** | ~1000+ LOC vendored (TBT+HSM+protobuf) | ❌ breaks the core design contract | recorder must do daily 3 AM refresh; concurrent-session risk | rejected |
| C. Stay ≤ 5 symbols (recorder-only clamp) | 5 | 5 | trivial | ✅ yes | n/a | superseded by the hybrid |

**Pros of A**
- The recorder stays a clean, broker-agnostic OpenAlgo client — zero FYERS code in the microservice.
- FYERS token lifecycle (daily ~03:00 IST refresh) and one shared broker session stay in OpenAlgo.
- Fixes a **latent limitation for OpenAlgo's own tools** (Option Chain / GEX / IV-surface all request
  50-depth and hit the same channel-1 cap) — candidate to upstream.

**Cons of A**
- Edits **platform** code (outside the recorder scope; user-authorized here).
- **Upgrade drift:** a `git pull` on OpenAlgo `main` can clobber it — see §4.
- Touches a shared code path → re-test the platform's own 50-depth consumers (§5).

**Why not B:** vendoring FYERS' proprietary TBT/HSM/protobuf into the recorder throws away the
"config-driven, broker/exchange-agnostic, talks to OpenAlgo only over HTTP/WS, imports no platform
module" contract (plan locked decisions), duplicates auth/token/session handling, and risks FYERS
per-app concurrent-session limits (we already saw 429s) — large permanent complexity for a ceiling A
reaches in ~35 lines.

## 4. Operator notes

**Apply / re-apply (e.g. after an OpenAlgo upgrade clobbers it):**
```bash
cd <openalgo repo root>
git apply strategies/SS_Projects/market_depth_recorder/Documents/patches/openalgo_fyers_tbt_channels.patch
# or, if it no longer applies cleanly after upstream changes, re-do the 3 edits from §2 by hand.
```

**Revert:**
```bash
cd <openalgo repo root>
git checkout -- broker/fyers/streaming/fyers_websocket_adapter.py    # if uncommitted
# or: git apply -R <the .patch>
```

**Take effect:** the FYERS adapter is loaded at OpenAlgo startup — a **restart is required** for the patch
to take effect (editing the file while OpenAlgo runs changes nothing until restart). A restart disrupts
the live feed, so schedule it before market open or in a maintenance window.

**Upgrade drift (important):** `Documents/patches/openalgo_fyers_tbt_channels.patch` is the source of
truth for re-applying. After any OpenAlgo upgrade, re-check that the channel spread is present
(`grep -n TBT_SYMBOLS_PER_CHANNEL broker/fyers/streaming/fyers_websocket_adapter.py`) and re-apply if
missing. Consider upstreaming to remove the maintenance burden.

## 5. Re-test checklist (before calling P10-A done)

- [ ] Restart OpenAlgo cleanly; FYERS session valid.
- [ ] **Recorder** `--preflight` a NIFTY window **> 5 symbols** → depth streams (no *"exceeds limit: 5"* /
      *"TBT data stall"* in `log/errors.jsonl`); raw shows NIFTY mode-3 `depth_levels=50`.
- [ ] **OpenAlgo Option Chain / GEX** (its own 50-depth consumers) still render 50-level depth for many
      strikes — the patch must not regress them.
- [ ] Log shows subs distributed across channels (`… on channel 1`, `… on channel 2`, …), 5 per channel.
      **→ SUPERSEDED (§8): this check passes and proves nothing.** Subscriptions *are* distributed across
      channels, but only ≤5 per connection ever **stream**. The meaningful check is a per-second count of
      **distinct legs actually delivering depth**, not the subscribe log — confusing the two is exactly how
      the P10-E artifact arose.

## 6. Risks this patch does NOT remove (verify live — P10-E)

1. **Global FYERS TBT cap** beyond the per-channel 5 (a per-app total across channels) — spreading NIFTY's
   ~80 legs over ~16 channels is the test (**P10-E2**). If it exists, the "whole chain at 50-level, no
   hybrid" decision reopens. **→ RESOLVED (P10-E, 2026-07-14): the cap is real — it is 5 per _connection_,
   independent of channel. The "whole chain at 50-level, no hybrid" decision is reopened. See §8.**
2. **Perf/storage at 80 × 50-level** — the authoritative `< 15 ms` / `< 500 MB` check the SENSEX-dominated
   P9 run couldn't make (**P10-E4/E5**).

## 7. Verification done so far (offline, this session)
- `python -m py_compile broker/fyers/streaming/fyers_websocket_adapter.py` → OK.
- Confirmed the channel-resume + per-channel reconnect-resubscribe path already exists in the TBT client
  (no client change needed).
- **Live smoke (§5) deferred to P10-E** — needs an OpenAlgo restart during market hours.

## 8. Live validation & correction (P10-E, 2026-07-14) — authoritative

The patch was validated live during market hours with OpenAlgo's own feed stopped, using the standalone
probe `market_depth_recorder/tools/fyers/tbt_channel_probe.py` (drives `FyersTbtWebSocket` directly, one
fresh connection per test, recording every subscribe/resume, every FYERS ACK/error, and per-symbol packet
counts). **Result: the patch does not lift the ceiling.**

### 8.1 Authoritative source — official FYERS TBT docs
FYERS TBT WebSocket Usage Guide (https://myapi.fyers.in/docsv3#tag/Tbtws) — rate limits:

| Limit | Value |
|---|---|
| Active connections per app per user | **3** |
| Symbols per connection [Market Depth] | **5** |
| Channels per connection | **50 (1–50)** |

The docs describe channels explicitly as a **logical grouping for pause/resume control** (their example:
Nifty on channel 1, BankNifty on channel 2 — pause/resume to choose which streams) — **not** a capacity
multiplier. Nowhere do they state "5 per channel" or "250 per connection". Channel ids are **strings** in
every official example (`"channel": "1"`, `resumeChannels: ["1"]`).

### 8.2 Experimental confirmation (probe matrix, evidence `tbt_probe_20260714.json`)
| Test | Setup | Result | Meaning |
|---|---|---|---|
| T1 | 5 syms, channel `"1"` | 5/5 stream | baseline |
| T2 | 5 syms, channel `"2"` (string) | 5/5 stream | a non-1 channel works **alone** |
| T2p | 5 syms, channel `2` (int) | 0/5 (silent) | **resume needs a _string_ channel id** |
| T3 | 5 on ch1 **+** 5 on ch2 (strings) | 5/10, `symbol count exceeds limit: 5` | channels share **one** 5-symbol budget |

The same-day live recorder run corroborates: of 40 NIFTY `:50` legs (spread across channels 1–8 by the
patch), **only 5 streamed** — exactly channel 1's five — while SENSEX/BFO (5-level HSM, non-TBT) ran all
120 legs. Raw: `data/2026-07-14/market_depth_raw_20260714.jsonl.gz`; probe JSON:
`Documents/patches/tbt_probe_20260714.json`.

### 8.3 Conclusions
1. **The "5/channel × 50 = 250" premise is wrong.** The effective 50-level ceiling is **5 Market-Depth
   symbols per connection**, confirmed independently by the official docs and the experiment.
2. **The channel-spread patch is a no-op for the ceiling.** Harmless (still 5 stream, same as pinning to
   channel 1) but it does not achieve its goal — keep it for tidy pause/resume semantics or revert it; it
   does **not** enable a full 50-level chain. Cosmetic downside: lowest-first channel assignment makes the
   surviving 5 the *edge* strikes, not ATM.
3. **Channel ids must be strings** (`"1"`) — matches the official examples; an int silently leaves the
   channel paused (T2p). OpenAlgo already sends strings, so no client change is needed there.
4. **Design decision reopened.** A full NIFTY 50-level chain is not achievable on one connection. Realistic
   options: the **hybrid** (5 near-ATM @50 + rest @5-level) or a **multi-connection** design (≤ 3
   connections/app/user × 5 = up to 15 depth symbols). **→ CONFIRMED (P10-F, 2026-07-14): 3 connections
   yield 15 concurrent 50-level symbols; `tbt_budget = 15`. See §8.4.**

### 8.4 Multi-connection question — RESOLVED (P10-F, 2026-07-14)
The docs give **3 connections/app/user** and **5 symbols/connection** but did not state whether they
combine to 15 concurrent Market-Depth symbols. **Settled by the multi-connection probe
`tools/fyers/tbt_multiconn_probe.py`** (evidence `tbt_multiconn_20260714.json`): **3 independent
connections each streamed a distinct 5-symbol group — 15/15 distinct legs concurrently**, with sustained
incremental updates and no interference; a **4th connection was refused** (immediate `429`), consistent
with the 3-connection cap. **Effective ceiling = `tbt_budget = 15` (3 × 5).** The single-connection
ceiling remains **5** (a full 50-level chain is not achievable on one connection). Architecture: the
allocator consumes **one logical TBT budget**; connection management stays an implementation detail of the
broker layer. Full evidence + the Jul-07/Jul-14 reconciliation:
`Documents/patches/tbt_concurrency_reconciliation_20260714.md` (canonical).
