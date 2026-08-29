# Phase 9 — Live-Run Session Notes (2026-07-06)

Working log of the P9 live-run session: what was executed against a **live** OpenAlgo + FYERS session
during IST market hours, the bugs found and fixed, the headline finding that changes the design, and
every test performed. Companion to the runbook `LIVE_RUN.md` (procedure) — this file is the **record of
what actually happened**. Decisions here are reflected in the plan doc (P10) and, where they touch the
architecture, in `ARCHITECTURE.md` / `CHANGELOG.md` / the design spec.

## 0. Context

- Market **live** (IST Mon 2026-07-06, ~13:36–14:19), OpenAlgo running at `127.0.0.1:5000`, broker = FYERS.
- Goal: execute P9 — operator-driven live confirmation of the whole pipeline (the parts that "cannot be
  faked": real 50-level TBT depth, per-level `orders`, real per-second cycle time and RSS at chain scale).
- Deps confirmed present globally: `openalgo==2.0.2` (the load-bearing exact pin), `numpy 2.4.4`,
  `duckdb 1.5.2`, `PyYAML`, `websocket-client`. Config validated clean (`--validate-config` → exit 0).

## 1. Bugs found & fixed this session (all with test coverage; 228 tests green)

The plan's P1/P3 "verified findings" were read from OpenAlgo **source** on 2026-07-03. Two of them did not
hold against the **live master data / library behaviour**, and surfaced immediately on first live contact.

### 1.1 InstrumentManager `name`-column match (real bug — blocked all resolution)
- **Symptom:** `--preflight` → `PREFLIGHT FAILED: [NIFTY] no option contracts for expiry 07-JUL-26 in NFO`.
- **Root cause:** the live OpenAlgo NFO master returns the `name` column as the **full contract label**
  (`"NIFTY 07 Jul 26 29450 CE"`), **not** the base underlying (`"NIFTY"`). Plan decision 12 assumed
  `name` == base underlying, with the symbol-prefix guard used only when `name` is **blank**. Non-blank +
  non-base `name` therefore took the exact-match branch, failed, and rejected every option row (0 of 77,317).
- **Fix:** `instrument_manager.py::_matches_underlying` — broadened the fallback trigger from *"name blank"*
  to *"exact name match failed"*, so the authoritative **symbol** longest-prefix guard (with the
  digit-after-base guard that already stops NIFTYNXT50 shadowing) runs for descriptive-`name` masters too.
- **Result:** NIFTY resolved 234 strikes/step 50/468 contracts; SENSEX 184/step 100/368 contracts.

### 1.2 Invalid heartbeat config crashed the WS (real bug)
- **Symptom:** `--preflight` live probe → `WebSocketException: Ensure ping_interval > ping_timeout` on the
  probe thread; preflight then masked it as `actual_depth=<unreachable>` (graceful-degrade by design).
- **Root cause:** `config.yaml` had `heartbeat_interval_sec: 10`, `heartbeat_timeout_sec: 12`.
  `websocket-client`'s `run_forever` **requires `ping_interval > ping_timeout`**. The combo was invalid
  and never validated at startup, so it blew up on the FEED thread at connect.
- **Fix (two parts):**
  - `config.yaml`: `heartbeat_timeout_sec: 12 → 8` (+ comment stating the constraint). Same fix in the
    test fixture `tests/conftest.py`.
  - `config.py`: new Rule-3 validation — `0 < heartbeat_timeout_sec < heartbeat_interval_sec`, fast-fail at
    startup rather than crashing a background thread later.

### 1.3 Preflight depth-level inference for 5-level (non-TBT) books (correctness gap)
- **Symptom:** SENSEX preflight reported `actual_depth=?` (couldn't determine the level count).
- **Root cause:** `run_depth_preflight` read only the self-describing `depth_levels` field, which the
  **5-level BFO (non-TBT) packet omits**. The spec (§3.2.5/§9) says to infer from `len(depth["buy"])` when
  the field is absent.
- **Fix:** `websocket_client.py::run_depth_preflight` — when `depth_levels` is missing, infer level count
  from `max(len(buy), len(sell))`. SENSEX now correctly reports `actual_depth=5` and the §9 DEPTH DEGRADED
  alarm fires (actual 5 < requested 50).

## 2. Live-run results — confirmations captured

| Check | Result |
|---|---|
| Chain resolution (real master) | NIFTY 234 strikes/step 50; SENSEX 184/step 100 |
| Preflight actual depth | **NIFTY/NFO → 50-level TBT**, **SENSEX/BFO → 5-level** |
| Per-level `orders` | **populated** (M13/M14 computable); `orders==0 → NULL` caveat holds |
| §9 silent-degrade alarm | Fires correctly for SENSEX (actual 5 < requested 50) |
| Pipeline milestones | Init → Connect → Record; **mid-day REST ATM seed** worked (spot NIFTY 24437.10 / SENSEX 78334.37) |
| Active contracts | 200 (NIFTY 80 legs + SENSEX 120 legs subscribed) |
| Raw audit fields | `feed_time` / `depth_levels` / `is_50_depth` / `total_*_qty` present; HEADER carries `instruments` block |
| Perf (SENSEX-dominated load) | `cycle_ms_p50 = 10.5`, `cycle_ms_max = 14.2` (**< 15 ms** ✓) |
| Memory | `rss_mb = 51` (**≪ 500 MB** ✓) |
| Losslessness | `raw_dropped_total = 0`, `db_rows_dropped_total = 0`; queues bounded; `degraded_level = 0` |
| Book parsing sanity | 95.1% books correctly ordered (bid<ask); locked 1.2% + crossed 3.7% = synthetic-feed artifact |
| Raw volume captured | 36,711 records / 2.6 MB gz; live DB 8.4 MB (option_strike_metrics 25,936 rows) |

**Not confirmable this session (blocked — see §3):** full NIFTY chain at 50-level; authoritative RSS at
full 50-level scale; graceful teardown via external OS signal on Windows (see §4).

## 3. Headline finding — FYERS TBT caps at 5 symbols per channel; OpenAlgo pins channel "1"

> **UPDATE (P10-E/P10-F, 2026-07-14) — corrected & authoritative; FROZEN.** The "5 per channel" framing in
> this section's title and below is **superseded**. Official FYERS TBT docs + a single-connection probe + a
> multi-connection probe + a re-read of both live raws establish the cap is **5 Market-Depth symbols per
> _connection_** (3 connections/app/user, 50 channels/connection); channels are a pause/resume grouping,
> **not** capacity. The channel-spread patch does **not** lift the ceiling — only 5 legs stream per
> connection. Three connections **do** combine, so the confirmed ceiling is **`tbt_budget = 15` (3 × 5)**;
> a full NIFTY chain at 50-level is **not achievable** and the **hybrid** (near-ATM @50 + rest @5) is now
> the design, not a fallback. Every stale claim below carries an inline `→ SUPERSEDED` marker; the narrative
> is preserved as the historical record. **Canonical evidence:**
> `Documents/evidence/tbt_concurrency_reconciliation_20260714.md`; see also `OPENALGO_PATCH.md` §8 and the
> probes `tools/fyers/tbt_channel_probe.py` / `tools/fyers/tbt_multiconn_probe.py`.

The single most important P9 result — it **cannot be faked** and it breaks a core design assumption.

- **Broker error (OpenAlgo `log/errors.jsonl`):**
  `TBT error: symbol count exceeds limit: 5, please unsubscribe few symbols before resuming the channel
  or subscribing additional symbols` → repeated `TBT data stall detected - no data for 120s. Forcing
  reconnect...`
- **Effect:** the daemon subscribed **80 NIFTY legs** at `:50` → FYERS rejected the **whole TBT channel**
  → NIFTY captured **zero depth** (only 255 mode-1 spot records; 0 mode-3 depth). SENSEX (BFO, **non-TBT**
  5-level HSM feed) streamed all 120 legs fine (12,353 depth packets). The single-strike preflight worked
  because 1 ≤ 5.
- **Cap is per-channel, but OpenAlgo makes it a hard total of 5:**
  **→ SUPERSEDED: the cap is per _connection_.** OpenAlgo's `channel="1"` hardcode is a real bug, but it is
  not what makes 5 the total — 5 is the total on any single connection regardless of channel spreading.
  - FYERS TBT feed has **channels 1–50**; the error ("resuming *the channel*") means **5 symbols per channel**.
    **→ SUPERSEDED: this inference from the error wording is the root of the whole mistake.** The broker says
    "the channel" but enforces the count **per connection**; the docs state the limit as symbols-per-connection
    and never say "5 per channel".
  - OpenAlgo's adapter **hardcodes `channel="1"`** for every depth-50 sub
    (`broker/fyers/streaming/fyers_websocket_adapter.py:682,686`) — never spreads across the other 49.
  - The OpenAlgo WS proxy protocol exposes **no channel field**, so the recorder cannot choose channels →
    effective ceiling the recorder can reach today = **5 symbols total**.
- **Secondary:** FYERS **429 Too Many Requests** on the quotes/depth REST path under the subscription load.

### Design implication + decision
- `CLAUDE.md` "Depth Reality" ("NIFTY/NFO → 50" for the chain) is only reachable if OpenAlgo spreads TBT
  subs across channels. **Decision (user, 2026-07-06): patch OpenAlgo** to bucket depth-50 subs 5-per-channel
  across channels 1–50 (ceiling 5×50 = 250), then **subscribe the whole NIFTY chain at 50-level — no hybrid**.
  The hybrid (50-near-ATM + 5-level rest) was only ever a workaround for the cap; the patch removes the cap,
  restoring the original full-chain-50 design. Hybrid retained only as a **documented fallback**.
  **→ SUPERSEDED: reversed on both counts.** The ceiling is **15, not 250**, and the patch does **not**
  remove the cap. The full-chain-50 design is unreachable and the **hybrid is now the design, not the
  fallback** (Plan_001 decision #17, delivery deferred to Plan_002). The patch is nonetheless kept — it is
  harmless and its channel-resume plumbing is correct.
- **Rejected alternative — direct FYERS connection (bypass OpenAlgo):** would vendor ~1000+ LOC of
  FYERS-proprietary TBT/HSM/protobuf into the recorder, **break the broker-agnostic design contract**,
  duplicate token/session management (daily ~03:00 IST refresh), and risk concurrent-session conflicts with
  OpenAlgo's own feed — large permanent complexity for a ceiling the patch reaches in ~10 lines.
- **Recorder needs no depth-code change for full-50:** it already sends `:50` for all NIFTY legs
  (requested_depth=50). With the patch those 80 legs (16 channels) should stream. → recorder work is
  validation, not new subscription logic.
  **→ SUPERSEDED: they did not stream.** The recorder still subscribes all ~80 NIFTY legs at `:50`, but
  only ≤5 concurrent legs ever deliver depth (~6% of the chain). The hybrid **does** require new
  subscription logic — a per-leg depth decision and the ability to demote 50→5 — which is precisely the
  allocator work Plan_002 exists to specify.
- **Still to verify live (next session):** (a) whether FYERS also imposes a **global** TBT cap beyond the
  per-channel 5; (b) perf/RSS at 80 × 50-level (the authoritative memory check the P8 harness can't do).
  **→ RESOLVED (P10-F):** (a) there is no *additional* global cap — the per-connection 5 **was** the cap all
  along, and 3 connections combine to 15. (b) **never measured and now unmeasurable as posed** — 80 ×
  50-level cannot occur on FYERS, so the P10-E perf numbers describe ≤5 NFO @50 + ~120 SENSEX @5. The
  hybrid's real load profile must be re-measured once the allocator lands.

## 4. Tests / verifications performed this session

- `--validate-config` → exit 0 (before and after config edits).
- `--preflight` (live): iterated 3× — (1) exposed the `name`-match bug, (2) exposed the heartbeat bug,
  (3) clean: NIFTY→50, SENSEX→5, §9 alarm firing.
- Full daemon run (~9 min live): milestones, health.json polled, live SQLite + raw gzip growing.
- **Raw-log analysis** (tolerant read of the live-written gz): 9,437→12,353 depth packets; bid/ask
  ordering 95.1% ok / 1.2% locked / 3.7% crossed → **ruled out a best_bid/best_ask parsing bug**; HEADER
  `instruments` block present; symbol kept `:50` verbatim; SENSEX at 5 levels in raw.
- **Symbol/mode distribution:** SENSEX 12,353 (mode 3) vs NIFTY 255 (mode 1 only) → confirmed NIFTY depth absent.
- **Live DB query:** `option_strike_metrics` 25,936 rows = 100% SENSEX, 0 NIFTY; `strike_window_metrics` /
  `aggregated_window_metrics` = 0 (expected — fat/offline-only, not in the thin live subset).
- **OpenAlgo server-log inspection** (`log/errors.jsonl`) → the authoritative TBT 5-symbol error + 429s.
- **Platform-code reading** (diagnosis only, no edits): `fyers_tbt_websocket.py` (channels 1–50, per-channel
  batch subscribe, protobuf, `access_token=APPID:SECRET`), `fyers_websocket_adapter.py` (`channel="1"`
  hardcode), `connection_manager.py` (proxy cap 1000×3 = not the limiter).
  **→ NOTE (P10-F): the per-channel batch subscribe here is message _coalescing_, not capacity.** Reading it
  as evidence for a per-channel symbol budget was part of the original misdiagnosis.
- **Full offline suite:** `pytest market_depth_recorder/tests/ -q` → **228 passed** after all fixes.
- **Windows teardown caveat:** the daemon (PID 13412) could be stopped **only** with `taskkill /F` —
  external graceful SIGTERM is unreliable for a Windows console process not in the caller's process group.
  Graceful teardown (EOF + auto-reprocess) must be exercised via in-console Ctrl-C or the natural 15:35
  auto-teardown, not an external signal. Force-kill left the raw gz **without an EOF marker** (the crash
  path — replay-tolerant by design; 36,711 records intact).

## 5. Files touched this session (fixes only; P10 work is separate)
- `instrument_manager.py` — `_matches_underlying` fallback broadened.
- `config.py` — heartbeat validation rule added.
- `config.yaml` — `heartbeat_timeout_sec 12 → 8`.
- `tests/conftest.py` — fixture heartbeat `12 → 8`.
- `websocket_client.py` — preflight depth-level inference fallback.
- `plans/Plan_001_evidence/Phase9_notes.md` — this file.

## 6. Open items → P10 (planned separately)
1. OpenAlgo channel-spread **patch** + reference `.patch` file + `Documents/evidence/OPENALGO_PATCH.md` (pro/cons + operator notes).
2. Recorder: **dated sub-folders**, data relocated **inside** `market_depth_recorder/`.
3. **EOD health & sanity-check** tool + dated report (markdown + json).
4. Live validation next session: full NIFTY 50-level, global-cap check, perf/RSS at scale, graceful teardown.
   **→ P10-E (2026-07-14): global-cap check DONE — the cap is 5 symbols per _connection_ (official FYERS docs
   + probe `tools/fyers/tbt_channel_probe.py`); channel spreading does not help, so full NIFTY 50-level is not
   achievable on one connection. See `OPENALGO_PATCH.md` §8. Perf/RSS-at-scale and graceful-teardown remain
   pending (the 5-symbol cap blocks a full-chain 50-level load test).**
   **→ P10-F (2026-07-14): multi-connection probe (`tools/fyers/tbt_multiconn_probe.py`) confirms 3 independent
   connections stream 15/15 distinct 50-level legs concurrently; a 4th is refused → `tbt_budget = 15`. This
   also reconciled the apparent P9/P10-E "full-chain" reading: the Jul-07 raw itself never streamed >5
   concurrent NFO legs — the earlier conclusion was an interpretation artifact, NOT a FYERS/OpenAlgo change
   (TBT code was byte-identical across the Jul-10/11 upgrade). Canonical:
   `Documents/evidence/tbt_concurrency_reconciliation_20260714.md`.**
