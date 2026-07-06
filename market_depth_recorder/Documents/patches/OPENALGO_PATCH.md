# OpenAlgo Patch — FYERS TBT channel spread (P10-A)

**Status:** applied to the working tree (2026-07-06). Reference diff:
`Documents/patches/openalgo_fyers_tbt_channels.patch`. **Not yet live-validated** — requires an OpenAlgo
restart during market hours (P10-E1/E2).

> This patch lives in a file **outside** the `market_depth_recorder/` package — it modifies the OpenAlgo
> platform. It is a deliberate, user-authorized **scope exception** (the recorder is otherwise
> broker-agnostic and never edits the platform). Keep it minimal and documented so it survives upgrades.

## 1. What problem it fixes

FYERS' 50-level TBT depth feed caps at **5 symbols per channel** (broker error: *"symbol count exceeds
limit: 5, please unsubscribe few symbols before resuming the channel"*). The feed exposes **channels
1–50**. OpenAlgo's FYERS adapter, however, **hardcoded `channel="1"`** for *every* 50-depth subscription
(`broker/fyers/streaming/fyers_websocket_adapter.py`, old lines 682/686), so the 6th 50-depth symbol
onward was silently rejected and the whole channel stalled → *"TBT data stall … Forcing reconnect"* in a
loop. Effect on the recorder (P9): 80 NIFTY `:50` legs → **NIFTY captured zero depth**; SENSEX (non-TBT
5-level HSM) was unaffected. Details: `Documents/patches/Phase9_notes.md` §3.

## 2. What the patch does

Packs 50-depth subscriptions **5 per channel across channels 1–50** instead of pinning to channel 1,
lifting the effective ceiling from **5 → 250** symbols.

- New class constants `TBT_SYMBOLS_PER_CHANNEL = 5`, `TBT_MAX_CHANNELS = 50`.
- New helper `_assign_tbt_channel(subscription_key)`:
  - **Re-subscribing an existing symbol reuses its stored channel** — so reconnects don't renumber a live
    symbol (the TBT client resubscribes per its own `subscriptions[channel]` state).
  - A **new** symbol fills the lowest-numbered channel with a free (< 5) slot.
  - Returns `None` when all 250 slots are used → the caller logs a clear `ERROR` and returns `False`
    (no silent starvation).
- `_subscribe_tbt_depth` now stores and subscribes with the assigned channel (was `"1"`), and logs the
  channel used.

**Concurrency:** `_subscribe_tbt_depth` is always called under `self.lock` (held from
`subscribe()`'s `with self.lock:` through the mode-3 branch), so the channel count/assign is race-free —
no new lock is taken (taking the non-reentrant `self.lock` again would deadlock).

**Downstream already handles multi-channel:** the TBT client resumes each newly-used channel on first
subscribe (`fyers_tbt_websocket.py::_flush_subscribe_batch` → `switch_channel(resume_channels=[…])`) and
resubscribes per channel on reconnect. No client change needed.

## 3. Pro / cons analysis (why this over the alternatives)

| Option | Ceiling | Effort | Keeps recorder broker-agnostic | Token/session mgmt | Verdict |
|---|---|---|---|---|---|
| **A. Patch OpenAlgo channels (this)** | 250 | ~35 lines, 1 file | ✅ yes | stays in OpenAlgo | **chosen** |
| B. Direct FYERS connection from recorder | 250 | ~1000+ LOC vendored (TBT+HSM+protobuf) | ❌ breaks the core design contract | recorder must do daily 3 AM refresh; concurrent-session risk | rejected |
| C. Stay ≤ 5 symbols (recorder-only clamp) | 5 | trivial | ✅ yes | n/a | fallback only |

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

## 6. Risks this patch does NOT remove (verify live — P10-E)

1. **Global FYERS TBT cap** beyond the per-channel 5 (a per-app total across channels) — spreading NIFTY's
   ~80 legs over ~16 channels is the test (**P10-E2**). If it exists, the "whole chain at 50-level, no
   hybrid" decision reopens.
2. **Perf/storage at 80 × 50-level** — the authoritative `< 15 ms` / `< 500 MB` check the SENSEX-dominated
   P9 run couldn't make (**P10-E4/E5**).

## 7. Verification done so far (offline, this session)
- `python -m py_compile broker/fyers/streaming/fyers_websocket_adapter.py` → OK.
- Confirmed the channel-resume + per-channel reconnect-resubscribe path already exists in the TBT client
  (no client change needed).
- **Live smoke (§5) deferred to P10-E** — needs an OpenAlgo restart during market hours.
