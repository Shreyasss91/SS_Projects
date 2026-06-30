# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\docs\releases



---

# FILE: docs\releases\version-2.0.0.7-released.md

```md
# Version 2.0.0.7 Released

**Date: 30th Apr 2026**

**Real-Time Performance Update: WebSocket Subscribe Batching across Dhan, Fyers & Upstox, Sandbox Event-Driven UI Updates, IIFL Capital Market Data Expansion & Flow Editor Stability**

This is a stability and performance update covering **26 commits** since v2.0.0.6. The headline change is a unified rewrite of WebSocket subscribe handling across three major brokers (Dhan, Fyers, Upstox) — instead of N per-symbol POSTs that hit broker rate limits and occasionally lost ticks for freshly-placed orders, subscriptions are now coalesced into batched grouped flushes. This closes a long-standing class of bugs reported across issues #1304 / #1314 / #1318 where ticks for newly-placed sandbox orders never reached the execution engine, manifesting as "price oscillates through the trigger but the order never fires." Combined with sandbox event-driven UI updates over the existing `analyzer_update` SocketIO channel, the OrderBook / TradeBook / Positions panes now refresh the moment a fill commits.

***

**Highlights**

* **WebSocket subscribe batching (Dhan, Fyers, Upstox)** — Per-symbol subscribe POSTs are now collapsed into single grouped flushes per broker. Closes the entire class of "freshly-placed order is invisible to the sandbox execution engine" bugs (issues #1304, #1314, #1318).
* **Sandbox event-driven UI updates** — Engine-internal fills, auto-square-off, and T+1 settlement now emit on the existing `analyzer_update` SocketIO channel. OrderBook / TradeBook / Positions refresh automatically the moment a fill commits.
* **IIFL Capital market data expansion** — Master contract optimization plus full historical data, quotes, depth, order, and margin API support (#1309, #1319). Brings IIFL Capital up to feature parity with the other Tier-1 brokers.
* **Fyers WebSocket overhaul** — Six separate fixes: HSM subscribe batching, positional-index → `brsymbol` mapping, shared dispatcher registry across reconnects, per-symbol OI gated to FNO-only with a >50-symbol skip, multiquote OI ceiling raised to 100, and index ticks fanned out to both Quote and Depth subscribers.
* **Dhan rate-limit hardening** — Minimum request interval bumped to 1.1s to stay under Dhan's "Order Received N in current second exceeds Limit 10" / 805 threshold.
* **Flow Editor stability** — Condition nodes honor their UI fields (and respect both `true/false` and `yes/no` edge handles), `{{var}}` interpolation supports list indexing, the Expiry node has a Futures/Options dropdown, the Config Panel scrolls on small viewports, and the Execution Log scroll is fixed.
* **Broker symbol normalization** — mstock `instrumenttype` normalized to `CE/PE/FUT` (Angel format), tradejini `expiry` stored as `DD-MMM-YY` (Zerodha format) — reduces broker-specific branching downstream (#1312).
* **Profile page UI fix** — Broker API secret no longer overflows the container or leaks the secret length through visual width.
* **Sandbox stale-field guard** — Drops `price` / `trigger_price` from order payloads based on `pricetype`, preventing leftover values from a previous order type from polluting the next placement.
* **Option chain exchange flip** — Underlying and expiry are now cleared atomically when the user flips the exchange dropdown, eliminating a transient mismatched state.
* **CI security scan resilience** — When `bandit`'s SARIF formatter crashes (a known upstream bug), the security scan no longer fails the entire CI run.

***

**Real-Time / WebSocket**

**Dhan**

* `1a80afb8` — `fix(dhan/ws): batch subscribes to collapse per-symbol WS messages into grouped flushes (#1314)`
* `5aa1156f` — `fix(dhan): bump min request interval to 1.1s to avoid 805 rate limit`

**Fyers**

* `671b8548` — `fix(fyers/ws): batch HSM subscribes to collapse N symbol-token POSTs into one`
* `5eb7baaa` — `fix(fyers/ws): join HSM<->OpenAlgo mapping through brsymbol, not positional index`
* `55129e6c` — `fix(fyers/ws): use shared dispatcher registry so multi-flush reconnects don't drop ticks`
* `15c2c63b` — `fix(fyers/multiquotes): per-symbol OI for FNO only, skip when >50 symbols`
* `81cecdbd` — `fix(fyers/oi-tracker): raise multiquote OI ceiling to 100, narrow OI tracker to 47 strikes`
* `b25bc931` — `fix(fyers/ws): fan out index ticks to both Quote and Depth subscribers`

**Upstox**

* `b9e44488` — `fix(upstox/ws): batch subscribe queue, LTPC carry-forward, larger reconnect budget`

The "price crosses trigger but pending sandbox order never fires" pattern reported across multiple brokers is fully resolved by these batching fixes. Ticks for freshly-placed orders now reliably reach the sandbox execution engine.

***

**Sandbox**

* `3ff65a3f` — `feat(sandbox): emit analyzer_update on engine-internal fills, square-off, T+1`
* `d3981b26` — `fix(sandbox): drop stale price/trigger fields by pricetype`

***

**Brokers**

**IIFL Capital (#1309, #1319)**

* `73857264` — Master contract optimization plus full market data API: historical, quotes, depth.
* `3ba5bf08` — Order API and margin API update.

**mstock**

* `df267180` — `instrumenttype` normalized to `CE/PE/FUT` to match Angel format.

**tradejini**

* `df267180` — Expiry stored in `DD-MMM-YY` format to match Zerodha.

**Dhan / Fyers / Upstox** — see Real-Time / WebSocket above.

***

**Flow Editor**

* `e16bb63c` — `fix(flow): condition nodes now honor their UI fields; respect both true/false and yes/no edge handles`
* `86f67310` — `fix(flow): support list indexing in {{var}} interpolation; fix Execution Log scroll`
* `b3d2ac11` — `fix(flow): make Config Panel scroll on small viewports`
* `193365f2` — `feat(flow): add Futures/Options dropdown to Expiry node`
* `5229c46e` — `docs(flow): document importer name field, fix node contracts, add 7 examples`
* `0f4f71f0` — `docs(flow): add prompt-style JSON import reference for the Flow Editor`

***

**UI / UX**

* `92b5c877` — `fix(ui): broker API secret no longer overflows / leaks length on Profile page`
* `975aafbc` — `fix(optionchain): clear underlying/expiry atomically on exchange flip`

***

**CI / Build**

* `3bdcd068` — `fix(ci): security scan no longer fails when bandit SARIF formatter crashes`

***

**Documentation**

* `d2baab90` — `docs(audit): add per-broker WebSocket keepalive/reconnect audit`
* `eb46e99c` — `docs(plans): expand GTT plan's Action Center coverage`
* `6f06329e` — `docs(claude): bump broker count from 24+ to 30+`
* `4a3b7861` — `chore(release): bump platform version to 2.0.0.7 and document bump procedure` — adds a Version Bumping section to `CLAUDE.md` clarifying the platform version (`utils/version.py` + `pyproject.toml`) is independent of the OpenAlgo Python SDK pin (`openalgo==1.0.49` in `requirements*.txt` and `pyproject.toml` dependencies).

***

**Contributors**

* **@marketcalls (Rajandran)** — release management, Dhan / Fyers / Upstox WebSocket subscribe-batching overhaul, sandbox event-driven UI updates, IIFL Capital market data expansion (#1309, #1319), Flow Editor stability fixes (condition nodes, list indexing, Expiry dropdown, scroll fixes), broker symbol normalization (mstock, tradejini #1312), Dhan rate-limit hardening, Profile UI fix, option chain exchange-flip atomicity, CI bandit SARIF resilience, and the per-broker WebSocket audit documentation.

***

**Links**

* **Repository**: <https://github.com/marketcalls/openalgo>
* **Documentation**: <https://docs.openalgo.in>
* **Discord**: <https://www.openalgo.in/discord>
* **YouTube**: <https://www.youtube.com/@openalgo>
* **Issue tracker**: <https://github.com/marketcalls/openalgo/issues>

***


---

# Agent Instructions: Querying This Documentation

If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.openalgo.in/change-log/release/version-2.0.0.7-released.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

```


---

# FILE: docs\releases\version-2.0.0.8-released.md

```md
# Version 2.0.0.8 Released

**Date: 1st May 2026**

**GTT Orders for Zerodha & Dhan, Telegram `/StopPython` Command, Historify Parquet Aggregation Fix, Codebase-Wide bare-except Sweep & Critical Docker Upgrade Hotfix**

This release covers **6 commits** since v2.0.0.7. The headline addition is end-to-end GTT (Good Till Triggered) order support for Zerodha and Dhan via four new endpoints — `placegttorder`, `modifygttorder`, `cancelgttorder`, `gttorderbook` — currently in pilot, with rollout to the remaining supported brokers planned for upcoming releases. Alongside the feature work, this release ships a **critical hotfix for Docker upgrades from v2.0.0.5 and earlier**: the auto-rotation of publicly-known sample `APP_KEY` introduced in v2.0.0.6 was crashing the gunicorn worker under Docker because the `.env` mount was read-only and the rotation could not write its atomic temp file. Any pre-v2.0.0.6 Docker install that left the sample keys in `.env` was hitting a restart loop on upgrade.

***

**Highlights**

* **GTT Order Implementation (Zerodha + Dhan)** — Pilot rollout of `/api/v1/placegttorder`, `/api/v1/modifygttorder`, `/api/v1/cancelgttorder`, `/api/v1/gttorderbook`. Database migration is mandatory on upgrade. Rollout to all other supported brokers is planned. (#1322)
* **Telegram `/StopPython` command + `/closeall` enhancement** — Lists running Python strategies inline; new **Close all + Stop strategies** button on `/closeall` flattens positions and stops every running strategy in one flow. (#1231)
* **Historify Parquet export now aggregates computed intervals** — Selecting `Parquet` with `5m` / `15m` / `30m` / `1h` / `W` / `M` / `Q` / `Y` no longer silently downgrades to ZIP. The exporter now uses the same DuckDB time-bucket / daily-aggregation logic the ZIP path has used. (#917)
* **Codebase-wide bare-except sweep** — 82 `except:` clauses across 45 files replaced with `except Exception:` (#1039). Restores correct shutdown-signal handling under Gunicorn / Docker / systemd; aligns with PEP 8 / Ruff `E722`.
* **🔴 Critical: Docker `.env` `:ro` mount removed; `APP_KEY` auto-rotation no longer crashes legacy Docker installs.** Affects every Docker user upgrading from v2.0.0.5 or earlier.

***

**Trading APIs**

**GTT Orders (#1322)**

* `ce0e4d59` — `Feat : Gtt Order Implementation. Updated for Dhan and Zerodha`

Pilot APIs (currently Zerodha + Dhan; other brokers to follow):

* `POST /api/v1/placegttorder` — place a GTT trigger.
* `POST /api/v1/modifygttorder` — modify trigger / leg parameters.
* `POST /api/v1/cancelgttorder` — cancel an active GTT.
* `POST /api/v1/gttorderbook` — list active triggers.

Schema highlights: flat place/modify body with `triggerprice_sl` and `triggerprice_tg`, `MIS` rejected, `last_price` fetched server-side; Dhan SINGLE/OCO mapping with per-leg modify; Zerodha `MARKET` pricetype auto-converted to MPP-protected `LIMIT` (Kite GTTs cannot carry MARKET).

⚠️ **Database migration is mandatory on upgrade.** Run before starting the new build:

```bash
uv run python upgrade/migrate_all.py
# or, just for the GTT tables:
uv run python upgrade/migrate_gtt.py
```

Adds `sandbox_gtt` and `sandbox_gtt_legs` tables and defaults. Sandbox / analyze-mode GTT execution is Phase 3 — analyze mode currently returns `501` for GTT calls until the in-progress sandbox integration ships.

API docs: <https://docs.openalgo.in/api-documentation/v1/orders-api/placegttorder>

***

**Telegram Bot (#1231)**

* `53334a0c` — `feat(telegram): add /stoppython and "Close all + Stop strategies" action`

New `/stoppython` command snapshots `RUNNING_STRATEGIES` from `blueprints/python_strategy.py` and renders one inline button per running strategy plus a **Stop All** button and **Cancel**. Per-strategy and bulk actions both prompt for confirmation before terminating, then call `stop_strategy_process()` — the same code path the UI's Stop button uses (`SIGTERM` → `SIGKILL` on Linux/Mac, `taskkill /F /T` on Windows). The strategy-id ↔ button-index map is held in `context.user_data["stoppy_list"]` so `callback_data` stays under Telegram's 64-byte cap regardless of how long strategy IDs get. If nothing is running, the bot replies `ℹ️ No Python strategies running.` and exits cleanly.

`/closeall` confirmation now offers a third button:

| Button | Action |
|--------|--------|
| ✅ Yes, close all | (existing) flattens every open position via `closeposition`. |
| ⚠️ Close all + Stop strategies | Closes all positions, then iterates `RUNNING_STRATEGIES` and terminates each via `stop_strategy_process()`. Reports a combined summary (positions closed, strategies stopped, failures). |
| ❌ Cancel | No-op. |

Help text updated; `docs/design/43-telegram-bot/README.md` brought back in sync with the actually-registered command names (`/orderbook`, `/tradebook`, `/chart`, `/mode`, `/menu`, `/link`, `/unlink`).

***

**Historify (#917)**

* `ee89cf8b` — `fix(historify): aggregate computed intervals in Parquet export`

`export_to_parquet()` previously ran a direct `WHERE interval = ?` query against `market_data`, which returns zero rows for any non-storage interval (only `1m` and `D` are physically stored — `5m / 15m / 30m / 1h`, custom intraday like `25m / 2h`, and `W / M / Q / Y` are aggregated on the fly). To prevent empty downloads, the historify bulk-export blueprint silently overrode the user's Parquet selection to ZIP whenever any computed interval was requested — so picking *Parquet + 5m* produced a `.zip` of CSVs.

`export_to_parquet()` now mirrors `export_to_zip()`'s three-branch interval handling:

| Interval kind | Source | Method |
|---|---|---|
| `1m`, `D` (storage) | direct read | unchanged |
| `5m` / `15m` / `30m` / `1h`, custom intraday (`25m`, `2h`, …) | aggregate from `1m` | DuckDB time-bucket SQL — same query as the ZIP path |
| `W` / `M` / `Q` / `Y`, multi-D | aggregate from `D` | reuses the existing `_get_daily_aggregated_ohlcv()` |

All symbols' rows go into a single Parquet file with the original schema preserved (`symbol, exchange, interval, timestamp, open, high, low, close, volume, oi, datetime`). Skipped symbols (missing source data) are surfaced in the response message rather than silently dropped. Compression codec (`zstd` / `snappy` / `gzip` / `none`) is honored as before.

The blueprint's silent ZIP override now applies only to multi-interval requests (legitimate — single-table formats can't carry per-interval files) and to single-computed CSV/TXT requests (those exporters still use direct queries and need the same treatment in a follow-up).

***

**Code Quality / Stability (#1039)**

* `b6419a90` — `fix: replace bare except clauses with except Exception across codebase`

82 occurrences across 45 production files in `blueprints/`, `broker/` (all 30+ broker integrations), `database/`, `sandbox/`, `services/`, `test/`, `utils/`, and `websocket_proxy/`. Bare `except:` swallows `BaseException`, including `SystemExit` and `KeyboardInterrupt` — meaning `Ctrl+C`, `SIGTERM` from Docker / systemd, and other shutdown signals could be silently absorbed mid-iteration in long-running loops (websocket adapters, Telegram polling, sandbox engine).

Practical effects:

* Cleaner shutdown under Gunicorn / Docker / systemd — `SIGTERM` propagates correctly.
* `MemoryError` and other `BaseException` subclasses now propagate as expected.
* `database/historify_db.py:_safe_timestamp()` additionally upgraded with `logger.warning` so timestamp conversion failures land in `log/errors.jsonl` instead of disappearing silently.
* Ruff `E722` / Flake8 `E722` no longer fire across the codebase, making future CI lint enforcement viable.

No behaviour change for ordinary exception flows — call sites still catch `Exception` and below, exactly as before.

***

**Security / Docker (Critical)**

* `245403f1` — `fix(security/docker): unblock APP_KEY/PEPPER auto-rotation under Docker (v2.0.0.8)`

v2.0.0.6 introduced an auto-rotation in `utils/env_check.py` that detects the publicly-known sample `APP_KEY` / `API_KEY_PEPPER` (which shipped in `.sample.env` up to v2.0.0.5, and which `install-docker.sh` did not rewrite until commit `0162ce3a5`) and replaces them with fresh secrets on first run. Under Docker, the rotation crashed the gunicorn worker:

```
[OpenAlgo security]
Detected publicly-known APP_KEY/API_KEY_PEPPER in .env, but
could not rewrite the file
([Errno 13] Permission denied: '/app/utils/../.env.tmp').
```

Two compounding causes:

1. `docker-compose.yaml` and the install-script compose templates mounted `.env` **read-only** (`./.env:/app/.env:ro`), so the rotation's atomic `.env.tmp` write failed with `EACCES` and `sys.exit(1)` killed the worker — gunicorn restart loop, container hard-down.
2. `install-docker.sh` and `install-docker-multi-custom-ssl.sh` kept `.env` at `chmod 644` owned by host root because the previous `:ro` mount made `chmod 600` + root ownership unreadable to the container's `appuser` (UID 1000) — see issue #960. With `:ro` removed, that workaround flipped into a problem: `appuser` still couldn't *write* a root-owned file even if the mount allowed it.

This affected every Docker user who installed before v2.0.0.6 and pulled the v2.0.0.6+ image — a meaningful slice of the existing Docker install base.

Fixes shipped:

* **Drop `:ro`** from every `.env` mount so the rotation can write its temp file. Touched: `docker-compose.yaml`, `install/install-docker.sh` (compose template), `install/install-docker-multi-custom-ssl.sh` (compose template), `install/docker-run.sh`, `install/docker-run.bat`, `docker-build.sh`.
* **`chown 1000:1000 .env && chmod 600 .env`** in `install/install-docker.sh`, `install/install-docker-multi-custom-ssl.sh`, `install/docker-run.sh` (with Linux/Mac branching). Tighter than the previous mode 644 *and* Docker-compatible at the same time — only `appuser` (UID 1000) on the host can read/write, instead of "anyone with read access to the install dir."
* **`start.sh` pre-flight check** before gunicorn launches. If `APP_KEY` / `API_KEY_PEPPER` is in the publicly-known compromised set AND `.env` is not writable from inside the container, prints an unmissable banner with the safe recovery recipe and exits cleanly. Replaces the buried "Permission denied" stack trace with an actionable error.

**Migration for users who hit the crash on Docker:**

```bash
cd /path/to/openalgo
docker compose down
git pull
docker compose pull

# Generate a fresh APP_KEY only — do NOT touch API_KEY_PEPPER on a populated install
APP_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
sed -i "s|^APP_KEY *=.*|APP_KEY = '$APP_KEY'|" .env

# Make .env writable by the container's appuser (UID 1000)
sudo chown 1000:1000 .env
sudo chmod 600 .env

docker compose up -d
```

⚠️ **Do NOT manually rotate `API_KEY_PEPPER` on a populated install.** The auto-rotation in `utils/env_check.py` deliberately declines to touch the pepper when the database has users — rotating it would invalidate every Argon2 password hash and every Fernet-encrypted broker auth/feed token / TradingView API key, none of which can be recovered. If you genuinely need to rotate the pepper (rare), use the dedicated migration which handles re-encryption and the required password reset:

```bash
uv run python upgrade/rotate_pepper.py
```

After applying the APP_KEY-only migration, `_generate_keys_on_first_run` takes the silent fast path (APP_KEY no longer in `COMPROMISED_APP_KEYS`) and the container boots cleanly. Browser sessions need to log in again — by design, that's how APP_KEY rotation prevents anyone with the leaked sample key from forging your sessions.

***

**Contributors**

* **@marketcalls (Rajandran)** — release management, GTT order implementation for Zerodha and Dhan (#1322), Telegram `/stoppython` command + `/closeall` enhancement (#1231), Historify Parquet aggregation fix (#917), codebase-wide bare-except sweep (#1039), critical Docker `.env` `:ro` hotfix.

***

**Links**

* **Repository**: <https://github.com/marketcalls/openalgo>
* **Documentation**: <https://docs.openalgo.in>
* **Discord**: <https://www.openalgo.in/discord>
* **YouTube**: <https://www.youtube.com/@openalgo>
* **Issue tracker**: <https://github.com/marketcalls/openalgo/issues>

***


---

# Agent Instructions: Querying This Documentation

If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.openalgo.in/change-log/release/version-2.0.0.8-released.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

```


---

# FILE: docs\releases\version-2.0.0.9-released.md

```md
# Version 2.0.0.9 Released

**Date: 1st May 2026**

**Patch: Manual-Rotation Guidance Hardened — Never Recommend Rotating `API_KEY_PEPPER` on a Populated Database**

This is a **single-commit patch release** on top of v2.0.0.8's Docker upgrade hotfix. The auto-rotation in `utils/env_check.py` already gates `API_KEY_PEPPER` rotation on database state — it only rotates the pepper on a fresh install with no users, because rotating it on a populated DB would invalidate every Argon2 password hash and every Fernet-encrypted broker auth/feed token / TradingView API key, none of which can be recovered. But the **fallback error-path messaging** — printed when the rotation cannot write to `.env` (e.g. read-only mount, permission denied) — was still telling users to manually regenerate *both* values. A user with a populated DB who followed that recipe would brick their deployment. Same problem in the `start.sh` pre-flight banner added in v2.0.0.8. v2.0.0.9 makes the user-facing manual-rotation guidance match the auto-rotation gating.

***

**Highlights**

* **Error path now DB-aware** — `utils/env_check.py` branches the manual-rotation message on `db_populated`. Populated DB → instructs only `APP_KEY` rotation, with an explicit "DO NOT change `API_KEY_PEPPER`" warning and a pointer to `upgrade/rotate_pepper.py`. Fresh DB → both can be safely regenerated.
* **`start.sh` pre-flight banner rewritten** — Default advice is `APP_KEY`-only. A second prominent block warns against regenerating `API_KEY_PEPPER` with the reasoning, and points to `upgrade/rotate_pepper.py` for the controlled path.

***

**Security**

* `b9301b78` — `fix(security): never recommend rotating API_KEY_PEPPER on populated DB`

The auto-rotation logic in `utils/env_check.py:329-412` is correct: on a populated DB, only `APP_KEY` is rotated; `API_KEY_PEPPER` is deliberately left alone because rotating the pepper invalidates:

* Every Argon2 password hash in `database/user_db.py` (one-way, cannot be migrated).
* Every Fernet-encrypted broker auth/feed token in `database/auth_db.py`.
* Every Fernet-encrypted TradingView API key.

But the **fallback error-path** — taken when the rotation can't write `.env.tmp` (read-only mount, EACCES) — printed:

```
Detected publicly-known APP_KEY/API_KEY_PEPPER in .env, but
could not rewrite the file (...).

Generate fresh values manually and paste them into .env:
  python -c "import secrets; print(secrets.token_hex(32))"
```

That advice is safe on a fresh install, fatal on a populated one. Same issue in the `start.sh` pre-flight banner added in v2.0.0.8 — it instructed users to `sed`-replace both `APP_KEY` and `API_KEY_PEPPER`.

Fixes shipped:

* **`utils/env_check.py`** — error message branches on `db_populated`. Populated DB prints `APP_KEY`-only instructions plus an explicit, bold "DO NOT change `API_KEY_PEPPER` on this populated install" warning, with the reasoning and a pointer to `upgrade/rotate_pepper.py` for the controlled rotation path that handles re-encryption + password reset. Fresh DB prints the original "both can be regenerated" guidance.
* **`start.sh`** — pre-flight banner rewritten. Default action is `APP_KEY`-only:
  ```bash
  APP_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
  sed -i "s|^APP_KEY *=.*|APP_KEY = '$APP_KEY'|" .env
  sudo chown 1000:1000 .env
  sudo chmod 600 .env
  ```
  A second prominent banner block — `[OpenAlgo] DO NOT regenerate API_KEY_PEPPER` — explains why and points to the rotate_pepper.py migration. PEPPER rotation is only safe on installs with no users; on any other install, leave it alone and let the auto-rotation's silent fast path take over once `APP_KEY` is no longer compromised.

The `_generate_keys_on_first_run` decision matrix (already documented in `utils/env_check.py:332-345`) is unchanged. v2.0.0.9 only tightens the *user-facing manual-rotation guidance* to mirror the same gating.

**Safe upgrade procedure for users on a populated install hitting the v2.0.0.6 → v2.0.0.8 Docker crash:**

```bash
docker compose down
APP_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
sed -i "s|^APP_KEY *=.*|APP_KEY = '$APP_KEY'|" .env
# Do NOT touch API_KEY_PEPPER on a populated DB.
sudo chown 1000:1000 .env
sudo chmod 600 .env
docker compose up -d
```

After this, `_generate_keys_on_first_run` takes the silent fast path for `APP_KEY` (no longer in `COMPROMISED_APP_KEYS`). The pepper remains in the compromised set, but `db_populated=True` gates the rotation off — only a single warning line, no startup block. Browser sessions need to log in again — by-design, that's how `APP_KEY` rotation prevents anyone with the leaked sample key from forging your sessions.

***

**Contributors**

* **@marketcalls (Rajandran)** — security hardening of manual-rotation guidance; PEPPER-safety review against the populated-DB upgrade path.

***

**Links**

* **Repository**: <https://github.com/marketcalls/openalgo>
* **Documentation**: <https://docs.openalgo.in>
* **Discord**: <https://www.openalgo.in/discord>
* **YouTube**: <https://www.youtube.com/@openalgo>
* **Issue tracker**: <https://github.com/marketcalls/openalgo/issues>

***


---

# Agent Instructions: Querying This Documentation

If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.openalgo.in/change-log/release/version-2.0.0.9-released.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

```


---

# FILE: docs\releases\version-2.0.1.0-released.md

```md
# Version 2.0.1.0 Released

**Date: 3rd May 2026**

**Major Feature Release: Remote MCP — Self-Hosted OAuth 2.1 + MCP HTTP/SSE Server for ChatGPT, Claude.ai, and Claude Mobile, Plus Per-Purpose 2FA Enforcement, Symbol Search Expansion, Admin Diagnostics, and Zerodha NCO/GLOBAL\_INDEX Support**

This is the biggest release in the 2.0.x line, covering **20+ commits** since v2.0.0.9. The headline change is **Remote MCP** — a self-hosted OAuth 2.1 + Model Context Protocol HTTP/SSE transport that lets hosted AI clients (ChatGPT.com, Claude.ai, Claude iOS / Android) connect to your OpenAlgo install over HTTPS with the same 40 tools the local stdio MCP already exposes. The local stdio MCP (Claude Desktop, Cursor, Windsurf) is **untouched** — Remote MCP is a parallel, opt-in transport, off by default, that ships behind two enabler scripts (one for native Ubuntu, one for Docker) and a full admin operations console at `/admin/remote-mcp`. Alongside Remote MCP, this release lands per-purpose TOTP enforcement (login / MCP / password reset), a multi-exchange Symbol Search expansion (issue #1326), an admin Diagnostics page with downloadable system reports, and Zerodha NCO + GLOBAL\_INDEX exchange support.

***

**Highlights**

* **Remote MCP — Hosted AI Clients via OAuth** — Brand-new `/mcp` HTTP/SSE transport with full OAuth 2.1 + PKCE, Dynamic Client Registration (DCR), JWKS-published RS256 JWTs, refresh-token rotation with reuse-detection family revocation, and per-token-per-scope rate limits. ChatGPT-compatible discovery (`/.well-known/oauth-authorization-server`, `/.well-known/oauth-protected-resource`), claude.ai-compatible scope flow. Off by default; turned on by `install/enable-remote-mcp.sh` (native) or `install/enable-remote-mcp-docker.sh` (Docker).
* **Per-purpose 2FA enforcement** — TOTP can now be required independently for **dashboard login**, **MCP authorization (`write:orders` consent)**, and **password reset** — set the master switch in Profile → TOTP, then pick which purposes apply. Saving requires a fresh TOTP code in the same request to prove authenticator access for both enabling and disabling.
* **Admin → Remote MCP operations console** — Approve / revoke DCR clients, browse the full MCP tool-call audit log (`log/mcp.jsonl`) by tool / scope / outcome, and a one-click **Kill switch** that atomically revokes every refresh token across every approved client.
* **Symbol Search rewrite (#1326)** — Multi-exchange + multi-instrumenttype filtering, CSV download, AmiBroker / TradingView / Python / Excel copy formats, lifted the 500-row hard cap, exchange-only browse mode, and per-user search history.
* **Admin Diagnostics page** — `/admin/diagnostics` shows live system info (Python / Flask versions, DB sizes, broker session state), a paginated error browser over `log/errors.jsonl`, and a one-click downloadable diagnostic bundle (env-redacted) for support tickets.
* **Zerodha NCO + GLOBAL\_INDEX exchanges** — NCO (NSE Commodities) and GLOBAL\_INDEX (US30 / JAPAN225 / HANGSENG, plus GIFTNIFTY from NSE IFSC) now route correctly through the master contract download and quote endpoints. Quote-only on GLOBAL\_INDEX (no orders by exchange convention).
* **"Virtual / Paper" → "Sandbox" rename** — All in-product copy, docs, and SDK examples now uniformly say *Sandbox* (the database, blueprint, and API endpoint names were already `sandbox` — only display strings were inconsistent).
* **Platform version bump** — `2.0.0.9` → `2.0.1.0`. `.sample.env` `ENV_CONFIG_VERSION` `1.0.6` → `1.0.7`. SDK pin (`openalgo==1.0.49`) unchanged.

***

**Remote MCP — feature deep dive**

Remote MCP brings the OpenAlgo MCP toolset to **hosted AI clients** over the public internet. Same 40 tools as the local stdio integration, exposed at `https://yourdomain.com/mcp` with full OAuth 2.1.

**Architecture in one sentence:** the hosted client (ChatGPT / Claude.ai) only ever holds an OAuth Bearer JWT signed by your server's RS256 keypair; tool dispatch on the server side reuses your existing `/api/v1/*` API key (looked up server-side at boot) over loopback. The hosted client never sees your API key or your broker tokens.

**OAuth foundation (Phase 2a + 2c + 2d)** — `e86cf450f`, `0f4f71f0`-derived family, `cb9350f27`:

* RS256 keypair generated and rotated via `utils/oauth_keys.py`; public set published at `/oauth/jwks.json`
* Dynamic Client Registration at `/oauth/register` (RFC 7591) — clients land in a *pending* bucket, gated behind admin approval (default `MCP_OAUTH_REQUIRE_APPROVAL=True`)
* Authorization Code + PKCE-S256 only — `plain` is not advertised; `alg=none` and `alg=HS256` JWTs are rejected by the verifier
* Refresh-token rotation with **family revocation** (RFC 6749 §10.4): single-use, atomic `UPDATE ... WHERE revoked_at IS NULL`, replay of a revoked token revokes the entire family
* `/oauth/revoke` for explicit token retirement, `/oauth/token` for code-exchange and refresh
* Argon2 hashing with `API_KEY_PEPPER` for client\_secret + refresh-token storage in `database/oauth_db.py`

**Per-purpose 2FA (Phase 2b + Phase 2 UI)** — `dbc595e88`, `ff44adf46`:

* Four new boolean columns on `users`: `totp_enabled` + `totp_required_for_login` + `totp_required_for_mcp` + `totp_required_for_password_reset`
* `is_totp_required_for(purpose)` helper centralizes the gating decision
* Login flow: POST `/auth/login` → on TOTP requirement, returns `totp_required` flag + temp ticket → POST `/auth/login/totp` with code
* Configure flow at `/auth/2fa/configure` requires a fresh TOTP in the same request (proves authenticator access for *both* enabling and disabling — closes the "stolen session can disable 2FA" hole)
* React UI: `TwoFactorEnforcement.tsx` profile-page toggle, `Login.tsx` TOTP step, `ResetPassword.tsx` TOTP path

**HTTP transport (Phase 3)** — `7d805af15`:

* JSON-RPC 2.0 dispatcher at `/mcp` (POST) + Server-Sent Events transport for streaming
* Per-token-per-scope sliding-window rate limits (`MCP_RATE_LIMIT_READ` / `MCP_RATE_LIMIT_WRITE`)
* CORS allowlist (default: `https://claude.ai,https://chatgpt.com`) with `WWW-Authenticate` exposed via `Access-Control-Expose-Headers` so browsers can read the realm hint on 401
* Audit log writes to `log/mcp.jsonl` — every tool call with timestamp, JTI, scope, outcome, latency, `params_hash` (raw params are deliberately *not* logged)
* Tool registry (`utils/mcp_tool_registry.py`) maps all 40 tools to scopes (`read:market` / `read:account` / `write:orders`) and exposes FastMCP-generated JSON schemas in the `tools/list` response
* Pre-flight refusal: server refuses to boot with `MCP_HTTP_ENABLED=True` and `FLASK_DEBUG=True` together (debug tracebacks would leak bearer tokens)

**Install integration (Phase 4)** — `b36637b5e`, `90897a550`:

* `install/enable-remote-mcp.sh` — native Ubuntu enabler. Detects all `openalgo-*` systemd services, refuses if `FLASK_DEBUG=True`, backs up `.env`, sets the four MCP keys, runs `upgrade/migrate_all.py`, restarts the service, and probes the discovery / JWKS / `/mcp/healthz` endpoints to confirm boot.
* `install/enable-remote-mcp-docker.sh` — Docker enabler. Walks `/opt/openalgo/*/docker-compose.yaml`, picks a stack, backs up the bind-mounted `.env`, updates keys, restarts the container (whose `start.sh` runs migrations automatically), and runs the same smoke probe.
* `install/Remote-MCP-readme.md` — operator-focused install guide with same-domain Mode 1 (automated) and subdomain Mode 2 (manual nginx + certbot recipe), threat model, and disabling instructions.
* New `docs/userguide/remote-mcp.md` — end-user guide for connecting ChatGPT (Settings → Apps → New App BETA → Advanced OAuth → DCR) and Claude.ai (Settings → Connectors → + → Add custom connector).

**Admin operations (Phase 5)** — `8be942a7c`:

* `/admin/remote-mcp` React page with three tables (Pending / Approved / Revoked) + audit viewer + kill switch
* `GET /admin/api/oauth/clients` lists clients by status; approve/revoke endpoints require typed-string confirmation for destructive actions
* `GET /admin/api/mcp/audit` — paginated audit log over `log/mcp.jsonl` with whitelisted query keys
* `POST /admin/api/mcp/kill-switch` — typed-string confirm, atomically revokes every refresh token across every approved client (read-only access tokens still expire on their existing 15-minute TTL)

**Security audit fixes + ChatGPT compatibility** — `926a597bf`:

* Migrated from deprecated `authlib.jose` → `joserfc` with explicit `algorithms=["RS256"]` pinning
* `MCP_PUBLIC_URL` is a hard requirement when `MCP_HTTP_ENABLED=True` — collapsing it to empty would let JWTs minted on instance A be replayed against instance B's loopback
* `error_detail` in MCP responses replaced with generic *"Tool execution failed"* — the full detail is in the audit log only, so SQL errors / stack traces don't leak to the model
* Added path-relative discovery alias `/mcp/.well-known/oauth-protected-resource` because ChatGPT fetches it that way (RFC 9728 says root-relative is canonical, but ChatGPT does both)
* Default `MCP_RATE_LIMIT_WRITE` raised from 5/min → 50/min based on real ChatGPT/Claude usage patterns
* Removed the vestigial `MCP_OAUTH_LOGIN_AUTH_LEVEL` env var (replaced by the per-purpose 2FA flags)

**CSP and consent screen fixes** — `52c96a11a`, `5f60b4817`, `3175a4104`:

* Per-page CSP on the consent screen sets `form-action` to allow exactly the registered redirect\_uri's origin — fixes the form-submit block when the global CSP middleware would otherwise refuse the cross-origin POST
* Global CSP middleware (`csp.py`) now respects view-set CSP headers (won't overwrite if a header is already set)
* `tools/list` response now includes the real Pydantic-generated JSON schemas (reach into FastMCP's `_tool_manager._tools`) so ChatGPT stops hallucinating parameter names like `product_type` instead of `product`
* Removed Jinja-time `csrf_token()` dependency on the consent template — render the token via `_csrf_token_value()` helper inside the view so timing-of-globals isn't an issue

**Three new admin endpoints + four new database models:**

| New                     | Purpose                                                                                |
| ----------------------- | -------------------------------------------------------------------------------------- |
| `database/oauth_db.py`  | `OAuthClient`, `OAuthRefreshToken` (with `family_id` / `parent_id`), `OAuthSigningKey` |
| `database/user_db.py`   | 4 boolean columns + `find_user_by_exact_username()`                                    |
| `utils/oauth_keys.py`   | RS256 keypair generation + rotation + `public_jwks()`                                  |
| `utils/oauth_tokens.py` | `issue_access_token`, `rotate_refresh_token`, `verify_access_token`                    |

**Default security posture:**

| Setting                         | Default      | Why                                                   |
| ------------------------------- | ------------ | ----------------------------------------------------- |
| `MCP_HTTP_ENABLED`              | `False`      | Off until you opt in                                  |
| `MCP_OAUTH_REQUIRE_APPROVAL`    | `True`       | DCR clients land pending until admin approves         |
| `MCP_OAUTH_WRITE_SCOPE_ENABLED` | `False`      | Order placement unreachable until you flip the switch |
| `MCP_RATE_LIMIT_READ`           | `60/min`     | Per-token sliding window                              |
| `MCP_RATE_LIMIT_WRITE`          | `50/min`     | Per-token sliding window                              |
| `MCP_MAX_ORDER_QTY`             | `0` (no cap) | Recommend setting a sane cap                          |

***

**Symbol Search expansion (#1326)**

* `232c637fb` — `feat(search): lift 500 cap, allow exchange-only browse, add search history`
* `f0c03eede` — `feat(search): multi-exchange/instrumenttype, CSV download, copy formats`

The Symbol Search page now supports filtering across multiple exchanges and multiple instrument types in a single query, browsing an entire exchange without entering a search term, downloading the result set as CSV, and copying selections in AmiBroker / TradingView / Python / Excel formats. The previous 500-row hard cap is gone — large result sets stream incrementally. Per-user search history is preserved across sessions.

***

**Admin / Operations**

* `566113d49` — `feat(admin): add Diagnostics page with system info, error browser, and downloadable report`

`/admin/diagnostics` consolidates the moving parts of "what's going on with this install" into a single React page: Python / Flask / SQLAlchemy versions, database sizes for all six SQLite/DuckDB databases, broker session state, configured env vars (with secrets redacted), a paginated browser over `log/errors.jsonl` with stack traces and Flask request context, and a one-click **Download diagnostic bundle** that produces an env-redacted ZIP suitable for attaching to a support ticket.

***

**Brokers**

**Zerodha**

* `6bc37381e` — `feat(zerodha): support NCO and GLOBAL_INDEX exchanges`

Adds two Zerodha-only exchange codes:

* **NCO** — NSE Commodities (Zerodha's symbol format differs from NCDEX; this fix routes correctly through the master contract download)
* **GLOBAL\_INDEX** — US30, JAPAN225, HANGSENG, plus `GIFTNIFTY` from NSE IFSC. Quote-only by exchange convention; orders are not supported on GLOBAL\_INDEX.

***

**Documentation**

* `199c544d1` — `docs: rename "virtual/paper trading" to "sandbox trading" terminology`
* `6efaf1655` — `docs: rename remaining "virtual" trading terms to "sandbox" equivalents`
* `500e27cbb` — `docs: add Remote MCP user guide for ChatGPT and Claude.ai`
* New `install/Remote-MCP-readme.md` — operator-focused install + threat model
* New `docs/prd/remote-mcp.md` — full product requirements doc with architecture, MUST/SHOULD/COULD security controls

The "virtual / paper trading" rename only touched display strings — the database (`db/sandbox.db`), blueprint (`blueprints/sandbox.py`), and API endpoints (`/api/v1/sandbox/*`) were already named `sandbox`. The rename closes a long-standing inconsistency between in-product copy and the underlying schema.

***

**Configuration changes**

`.sample.env`:

* `ENV_CONFIG_VERSION` `1.0.6` → `1.0.7`
* New section: `MCP_HTTP_ENABLED`, `MCP_PUBLIC_URL`, `MCP_OAUTH_REQUIRE_APPROVAL`, `MCP_OAUTH_WRITE_SCOPE_ENABLED`, `MCP_HTTP_CORS_ORIGINS`, `MCP_HTTP_IP_ALLOWLIST`, `MCP_OAUTH_ACCESS_TTL`, `MCP_OAUTH_REFRESH_TTL`, `MCP_OAUTH_CODE_TTL`, `MCP_RATE_LIMIT_READ`, `MCP_RATE_LIMIT_WRITE`, `MCP_MAX_ORDER_QTY`
* Removed: `MCP_OAUTH_LOGIN_AUTH_LEVEL` (vestigial — replaced by per-purpose 2FA flags)

`pyproject.toml`:

* `version = "2.0.1.0"`
* SDK pin (`openalgo==1.0.49`) unchanged

`utils/version.py`:

* `VERSION = "2.0.1.0"`

***

**Upgrade procedure**

**For existing installs (Native Ubuntu):**

```bash
cd /var/python/openalgo-flask/<deploy-name>/openalgo
sudo ./install/update.sh
# update.sh runs migrate_all.py — schema changes for the OAuth + 2FA columns
# are applied automatically. Remote MCP stays disabled by default.
```

**For existing installs (Docker):**

```bash
cd /opt/openalgo/<domain>
sudo docker compose pull
sudo docker compose up -d
# The container's start.sh runs migrate_all.py before gunicorn boots.
# Remote MCP stays disabled by default.
```

**To enable Remote MCP (after upgrading):**

```bash
# Native Ubuntu
sudo ./install/enable-remote-mcp.sh

# Docker
sudo ./install/enable-remote-mcp-docker.sh
```

Both enabler scripts are idempotent and back up `.env` before any change. They print a one-liner rollback command if the smoke probe fails.

**For local developers (uv):**

```bash
git pull origin main
uv sync
cd frontend && npm install && npm run build
uv run app.py
```

***

**Contributors**

* **@marketcalls (Rajandran)** — release management, Remote MCP architecture and full OAuth 2.1 implementation (5 phases — scaffold → OAuth foundation → 2FA wiring → discovery + JWKS + DCR → /authorize + /token + /revoke → Phase 2 UI → HTTP/SSE transport → install integration → admin UI), security audit + joserfc migration, CSP fixes for the consent flow, ChatGPT-compatibility hardening (path-relative discovery, real tool schemas, generic error\_detail), Docker enabler, install integration, comprehensive PRD + operator docs + end-user docs, Symbol Search rewrite (#1326), Admin Diagnostics page, Zerodha NCO + GLOBAL\_INDEX support, and the "virtual → sandbox" terminology cleanup.

***

**Links**

* **Repository**: <https://github.com/marketcalls/openalgo>
* **Documentation**: <https://docs.openalgo.in>
* **Remote MCP guide**: <https://docs.openalgo.in/mcp/remote-mcp>
* **Discord**: <https://www.openalgo.in/discord>
* **YouTube**: <https://www.youtube.com/@openalgo>
* **Issue tracker**: <https://github.com/marketcalls/openalgo/issues>

***


---

# Agent Instructions: Querying This Documentation

If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.openalgo.in/change-log/release/version-2.0.1.0-released.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

```


---

# FILE: docs\releases\version-2.0.1.1-released.md

```md
# Version 2.0.1.1 Released

**Date: 17th May 2026**

**Major Feature Release: WhatsApp Bot Integration — Event-Driven Alerts + Slash-Command Queries, Plus a WebSocket Reliability Sweep Across 14 Brokers, New Broker Integrations (IIFLCapital Streaming, Groww Option Chain + WS Depth, Upstox GLOBAL\_INDEX), and Per-Install Fernet Salt Rotation with Crash-Safe Auto-Migration**

This release spans **70+ commits** since v2.0.1.0. The headline change is **WhatsApp** — a self-hosted, event-driven WhatsApp bot that fires order alerts on the same event bus that drives Telegram, accepts slash-command queries (`/orderbook`, `/positions`, `/quote`, …) from the operator's own phone, and exposes a single send endpoint over REST. Pairing happens once from the OpenAlgo admin UI with a QR scan; the encrypted session blob is then stored in `openalgo.db` and the bot auto-reconnects on every server boot. Alongside WhatsApp, this release lands a WebSocket reliability sweep — subscribe batching across 6+ brokers, reconnect hardening across 4+ brokers, file-descriptor leak fixes in two streaming layers, and proxy-level fixes (ZMQ bind, mode normalization, request_id correlation). Three new broker integrations land: IIFLCapital streaming, Groww option chain + WS depth, and Upstox GLOBAL\_INDEX world feeds. Security: a per-install random `FERNET_SALT` now feeds the Fernet KDF, with a crash-safe online migration of existing ciphertext.

***

**Highlights**

* **WhatsApp Bot — event-driven alerts + slash-command queries** — Brand-new `/whatsapp` admin page with auto-rotating QR pair flow, a single trader-facing `POST /api/v1/whatsapp/notify` endpoint that accepts text + image + document attachments, a dedicated worker thread that satisfies wars's PyO3 unsendable contract, and a `subscribers/whatsapp_subscriber` that wires every order topic on the existing event bus so order/position/batch events fire WhatsApp messages in parallel with Telegram. Single-user gate via WhatsApp's own `is_from_me=True` mark — random contacts who message the operator's number cannot drive the bot.
* **`client.whatsapp()` in the openalgo Python SDK (1.0.50)** — One unified call for every common case: send to self, to a single E.164 number, to up to 5 numbers (ToS-safety cap), with text, image, or document payloads. `wait_for_delivery=True` by default so the response carries a real per-recipient delivery report.
* **WebSocket reliability sweep across 14 brokers** — Subscribe batching for Kotak (HSI multi-scrip frames + 50ms debounce), AliceBlue, Nubra, Shoonya, Angel, Flattrade. Reconnect hardening for Dhan (auto-resubscribe + data-stall watchdog), Dhan-Sandbox (eventlet-safe asyncio + single-loop reconnect), Upstox (stall-vs-network reconnect logging), Fyers TBT (batch queue + pong validation + exponential backoff + health check). Cold-subscribe latency cut ~5× on Shoonya; Zerodha lost a ~4s sleep floor.
* **WebSocket-proxy + client fixes** — Bind ZMQ publisher to `ZMQ_HOST` instead of all interfaces (#1378), normalize subscribe/unsubscribe mode case-insensitively (#1375), correlate ack via request_id (#1376), route cache invalidation through `SharedZmqPublisher` to eliminate the PUB→PUB topology (#1374).
* **Three new broker integrations** — **IIFLCapital streaming** (full WS adapter; file-descriptor leaks closed across reconnect cycles, #1416 + #1430), **Groww** (full option chain + WS depth, expiry filter for expired contracts, broker-symbol mangling fix, #1392), **Upstox GLOBAL\_INDEX** (US30 / JAPAN225 / HANGSENG world feeds via the existing Upstox WS adapter).
* **Per-install random Fernet salt** — `FERNET_SALT` env var is now provisioned per install (32-byte hex, generated by `utils/env_check.py`) and feeds the Fernet KDF in `database/auth_db.py`. Crash-safe online migration moves existing ciphertext from the legacy static salt to the new one; if the process dies mid-migration the next boot resumes from the persisted state. Tightens broker-auth-token confidentiality and is the same domain-separated salt the new WhatsApp session blob uses.
* **Platform version bump** — `2.0.1.0` → `2.0.1.1`. SDK pin (`openalgo`) `1.0.49` → `1.0.50`.

***

**WhatsApp Bot — feature deep dive**

WhatsApp brings parity with Telegram for both outbound alerts and interactive command queries, with security choices tuned for the single-user-per-deployment model OpenAlgo runs under.

**Architecture in one sentence:** the wars (PyO3 over whatsapp-rust) library hosts a fully linked WhatsApp Web device inside the Flask process; outgoing alerts flow event-bus → `whatsapp_subscriber` → `WhatsAppBotThread` → `wars.send()`; incoming slash-commands flow `wars.on_message` → `is_from_me=True` gate → command dispatcher → OpenAlgo SDK call → reply via the same bot thread.

**Pairing (admin only)** — `c44a420b`:

* `POST /whatsapp/pair` (session-cookie auth) spawns a temp-DB wars instance, registers an `on_qr` callback that streams `whatsapp_qr` SocketIO events with a `data:image/png` URL, and waits on `wait_until_ready(timeout=300)` for the phone-side scan
* QR refreshes ~every 30 seconds; React `/whatsapp` page swaps the `<img>` source on each `whatsapp_qr` event without polling
* On pair success: `export_session()` → Fernet-encrypted → persisted to `whatsapp_config.session_blob` in `openalgo.db` → temp file unlinked
* Pair-code path (`POST /whatsapp/pair` with `phone` parameter) for users who prefer not to scan a QR

**Encryption at rest** — `database/whatsapp_db.py`:

* Fernet key derived via PBKDF2-SHA256(`API_KEY_PEPPER`, `FERNET_SALT + b":whatsapp-session"`, 100k iters), 32-byte output, base64-urlsafe encoded
* Domain separator (`:whatsapp-session`) means the same `(PEPPER, FERNET_SALT)` pair derives **different** Fernet keys for broker auth tokens, Telegram bot tokens, and WhatsApp session blob — compromising one channel's ciphertext gives no leverage against the others
* Idempotent SQLite `ALTER TABLE ADD COLUMN` migration runs at every init so existing installs pick up the `owner_user_id` / `owner_username` columns without manual schema work

**The unsendable PyO3 trap** — `c44a420b`:

* `wars.WhatsApp` is `#[pyclass(unsendable)]` — every method call panics if invoked from a thread other than its creator
* Solution: a dedicated `WhatsAppBotThread` owns the wars instance for its lifetime; request threads enqueue `(op, args, result_holder, event)` on a `queue.Queue` and wait on a `threading.Event` for the worker to dispatch `wars.send()`
* Re-entrant: command handlers (which wars dispatches on the bot thread itself) bypass the queue via a `threading.get_ident() == self._bot_thread_id` check so they don't deadlock on themselves
* Same shape Telegram uses for python-telegram-bot, for the same reason

**REST surface — intentionally narrow** — `restx_api/whatsapp_bot.py`:

* `POST /api/v1/whatsapp/notify` is the **only** public endpoint
* Pairing, start/stop, config, users, broadcast, stats, preferences live behind the session-authed `/whatsapp/*` blueprint — admin only
* A leaked API key cannot re-pair the device, enumerate linked recipients, change rate limits, or fan out to the operator's contact list
* Hard precheck — every send path refuses with `409 "WhatsApp is not paired or not connected. Pair the device first from the /whatsapp page in OpenAlgo before sending."` if `is_ready()` is false; we explicitly do not queue when unpaired

**Send paths — one unified call**:

* `client.whatsapp("Build #482 deployed")` → wars's single-arg `send("text")` form, routes to the paired device's own number (no need to know own JID)
* `client.whatsapp("hi", to="919876543210")` → single recipient
* `client.whatsapp("alert", to=[...])` → broadcast (capped at 5 server-side — anything beyond is dropped; ToS-safety guardrail)
* `client.whatsapp("EOD chart", to="919...", image="/srv/charts/nifty.png", caption="...")` → image with caption
* `client.whatsapp("report", username="alice", document="/srv/reports/eod.pdf", filename="EOD.pdf")` → document
* Attachment paths validated against `WHATSAPP_ATTACHMENT_ROOTS` allowlist (default: `<openalgo>/db/attachments/`); paths with `..`, paths under `/etc /proc /sys /root /var/log /C:\Windows`, or paths that resolve outside the allowlist are rejected with `400 image_path is not allowed`

**Inbound commands** — `services/whatsapp_bot_service.py`:

| Command | Maps to |
| --- | --- |
| `/help`, `/menu`, `/start` | Command list |
| `/status` | Bot connection + paired status |
| `/orderbook` | `client.orderbook()` |
| `/tradebook` | `client.tradebook()` |
| `/positions` | `client.positionbook()` |
| `/holdings` | `client.holdings()` |
| `/funds` | `client.funds()` |
| `/pnl` | `client.pnl()` or `client.positionbook()` |
| `/quote SYM [EXCH]` | `client.quotes()` |
| `/closeall` | `client.closeposition()` |
| `/mode` | live or analyze |

Auth: the bot only responds when `is_from_me=True` (WhatsApp's multi-device protocol marks messages mirrored from the operator's primary phone with this flag). Random contacts who message the operator's WhatsApp number arrive with `is_from_me=False` and are silently ignored. The OpenAlgo SDK calls run with the operator's API key, looked up from `auth_db` by the `owner_username` captured at pair time — there is no `/link` flow because there is no second user to authorize.

**Auto-reconnect on app boot** — `app.py:_autostart_whatsapp_bot`:

* Background thread spawned during `_init_databases_and_schedulers` (after `db_ready.set()`)
* Loads the encrypted session blob, calls `wars.WhatsApp.from_bytes(blob)`, starts the worker thread, registers handlers
* No QR scan on restart — `is_ready()` flips to true within ~1s of boot
* If wars isn't installed (fresh checkout that hasn't `uv sync`'d), the autostart logs a warning and degrades gracefully — the rest of the Flask app boots normally

**Frontend** — `frontend/src/pages/whatsapp/WhatsAppIndex.tsx`:

* Single-page React UI: Status card with Pair QR + Disconnect button, "Send a one-off message" card, no Linked-Users table (single-user app)
* SocketIO subscriptions for `whatsapp_qr` (auto-rotates the QR image), `whatsapp_pair_code`, `whatsapp_paired`, `whatsapp_pair_status`, `whatsapp_status`
* New `MessageCircle` icon in the profile dropdown so WhatsApp visually differs from Telegram's `MessageSquare`

**RUST_LOG quieting** — `services/whatsapp_bot_service.py`:

* Three known-noisy targets silenced at module import (before any `import wars`): `wacore::send` (stale-device warnings), `whatsapp_rust::message` (PN→LID migration chatter), `wacore_libsignal::protocol::session_cipher` (no-current-session errors that the upper layer already handles)
* `os.environ.setdefault("RUST_LOG", ...)` — operator can still override via shell or `.env` for diagnostics

**openalgo Python SDK 1.0.50** — released to PyPI alongside this version:

* New `WhatsAppAPI` mix-in adds `client.whatsapp(...)` with the four recipient forms and image/document payloads
* Mirrors the `client.telegram()` ergonomics for traders already familiar with the SDK
* Available at <https://pypi.org/project/openalgo/1.0.50/>

***

**WebSocket reliability sweep — 14 brokers touched**

| Broker | Change | Commit |
| --- | --- | --- |
| **IIFLCapital** | Full websocket adapter integrated + file-descriptor leaks closed across reconnect cycles | `0ad69cf3` (#1416), `15179371` (#1430) |
| **Paytm** | NSE\_INDEX/BSE\_INDEX symbol normalization + fd-leak fixes in streaming layer + batch ws subscribe + graceful empty for option chain / OI tracker / historical | `8dba1ea3` (#1413) |
| **Kotak** | Batch subscribe via HSI multi-scrip frames + cut batch debounce 500ms → 50ms + log emitted scrips | `8fef2a57` (#1399) |
| **Groww** | Full option chain + websocket depth integration + drop expired expiries + stop mangling broker symbols | `440b78ef` (#1392) |
| **AliceBlue** | Batch ws subscriptions like Zerodha + event-driven connect + leading-edge subscribe debounce | `09667a6e` (#1389) |
| **Dhan-Sandbox** | Eventlet-safe asyncio + heartbeat align + single-loop reconnect + batch queue | `b5675653` (#1344) |
| **Nubra** | Coalesce per-symbol subscribes into batched SDK calls | `6473aa2e` (#1366) |
| **Shoonya** | Batch queue + auth-fail short-circuit + env-var tuning + interruptible sleeps; cold-subscribe latency cut ~5× via leading-edge debounce | `4b8578d6` (#1381) |
| **Dhan** | Auto-resubscribe on reconnect + data-stall watchdog | `d214a598` (#1372) |
| **Upstox** | Distinguish stall-triggered reconnects from network-induced ones in logs | `42927546` (#1357) |
| **Angel** | Subscribe batch-queue to coalesce per-symbol bursts + defensive `.get()` in place\_order response handling | `790cc64d` (#1352), `a4bdac18` (#846) |
| **Zerodha** | Remove ~4s sleep floor from subscribe path + add auth-fail short-circuit + interruptible sleeps + wire MCX\_INDEX through quote/history/depth/ws | `659d53ab`, `f21f40cc` (#1371), `cd4095eb` (#1385) |
| **Fyers** | Harden TBT client with batch queue, pong validation, exponential backoff, and health check | `463a3004` (#1361) |
| **Flattrade** | Batch-queue subscriptions like Zerodha adapter | `ed37dbc2` (#1341) |
| **Kotak** | Align place/modify order payload with official Neo spec | `b06ef4a8` (#1398) |

**WebSocket-proxy + client layer:**

* `dd9cb64c` (#1378) — `fix(websocket_proxy): bind ZMQ publisher to ZMQ_HOST instead of all interfaces`
* `6ddff2bb` (#1375) — `fix(websocket_proxy): normalize subscribe/unsubscribe mode case-insensitively`
* `9a0f5e42` (#1376) — `fix(websocket_client): correlate subscribe/unsubscribe acks via request_id`
* `521ea129` (#1374) — `fix(cache_invalidation): route through SharedZmqPublisher to eliminate PUB->PUB topology`
* `25eed728` — `fix(ui/websocket-test): keep LTP card live when Depth is also subscribed`
* `f8a1ff4f` (#1386) — `chore(websocket): remove dead get_supported_brokers_list()`
* `06d4cb34` — `docs(audit): add WebSocket broker priority audit`

***

**New broker integrations + exchange expansion**

* **`0ad69cf3` / `15179371`** — IIFLCapital websockets integrated + broker hardening + option-chain perf
* **`440b78ef`** — Groww full option chain + websocket depth integration
* **`c0335582`** — Upstox GLOBAL\_INDEX world feeds (US30 / JAPAN225 / HANGSENG, plus IFSC-routed GIFTNIFTY) on indices and indicators
* **`cd4095eb`** — Zerodha MCX\_INDEX wired through quote/history/depth/ws
* **`ca15b333`** — Groww NSE\_INDEX/BSE\_INDEX in historical (#1338/#1342)
* **`11778af5`** — Symbol search surfaces FUT-only MCX underlyings (#1385)

***

**Security hardening — Fernet per-install salt**

The Fernet KDF in `database/auth_db.py` (which encrypts broker auth tokens) previously used a hardcoded static salt. This release lands a per-install random salt with a crash-safe online migration.

* `2f2e9bee` — `fix(security): rotate Fernet to per-install salt with crash-safe auto-migration`
* `e3c5285d` — place `FERNET_SALT` adjacent to `API_KEY_PEPPER` in `.env`, handle the 4 file-state cases cleanly (placeholder / valid / missing / mid-migration)
* `a1455ff1` — atomic `.env` rewrite falls back to in-place on Docker bind mounts
* `84922078` — degrade gracefully when `.env` is unwritable + pin Docker UID 1000 (#1394)
* `2981ff52` — post-FERNET\_SALT cleanup — security perm-check, dedupe, pool invalidate (#1394)
* `b9301b78` — never recommend rotating `API_KEY_PEPPER` on a populated DB (carried in from late v2.0.0.9 work, re-asserted here)

What this means operationally:

* New installs: `utils/env_check.py` generates a 32-byte hex `FERNET_SALT`, writes it adjacent to `API_KEY_PEPPER` in `.env`, and uses it directly. No migration runs.
* Existing installs upgrading to 2.0.1.1: on first boot, `env_check` detects the placeholder/missing state, generates the new salt, re-encrypts every broker-auth-token ciphertext on the fly with the new key, and atomically swaps. If the process dies mid-migration, the persisted `FERNET_SALT` lets the next boot resume cleanly.
* Same salt entropy feeds the new WhatsApp session blob via the `:whatsapp-session` domain separator.

***

**UI + frontend**

* `cd692653` — `feat(orderbook): make Quantity editable in Modify Order dialog`
* `f968b403` — `fix(ui): align table content with stats cards on Positions/Orderbook/Holdings/Tradebook`
* `d3aa8b6b` — `fix(frontend): auto-reload on stale-chunk import failure (#1393)` — fixes the "ChunkLoadError" trader sees after a deploy when the browser is still holding the old `index-*.js` reference
* `d63ec927` — drop hero gradient on the home page, use solid `text-primary`
* `3f4e2b2b` — home: "New in V2 — 12-Tool Options Analytics Suite" pill
* `624f8726` — home: Integrates With + Made for AI sections
* `61370758` / `54d83c07` — restyle the MCP OAuth consent page to match OpenAlgo dashboard + fix alignment

***

**Configuration changes**

`.sample.env`:

* `FERNET_SALT` — new placeholder line auto-rotated on first boot, placed adjacent to `API_KEY_PEPPER`
* No new keys for WhatsApp — `WHATSAPP_KEY_SALT` reuses the existing `FERNET_SALT` with a `:whatsapp-session` domain suffix (zero new env vars to manage)
* Optional: `WHATSAPP_ATTACHMENT_ROOTS` (comma-separated absolute dirs; defaults to `<openalgo>/db/attachments/`)
* Optional: `RUST_LOG` — defaults to a filter that silences three known-noisy wars/whatsapp-rust modules

`pyproject.toml`:

* `version = "2.0.1.1"`
* New: `wars==0.1.3` dependency (also added to `requirements.txt` + `requirements-nginx.txt`)
* SDK pin (`openalgo`) `1.0.49` → `1.0.50`

`utils/version.py`:

* `VERSION = "2.0.1.1"`

`requirements.txt` + `requirements-nginx.txt`:

* `wars==0.1.3` added after `python-telegram-bot==22.6`
* `openalgo==1.0.49` → `openalgo==1.0.50`

`frontend/src/stores/alertStore.ts`:

* New `whatsapp` toast category alongside `telegram`

***

**Database schema**

New tables created by `database/whatsapp_db.py` on first boot:

| Table | Purpose |
| --- | --- |
| `whatsapp_config` | Singleton row holding the Fernet-encrypted session blob + bot config + owner identity |
| `whatsapp_users` | Optional linked recipients (unused in single-user mode, retained for future multi-recipient deployments) |
| `whatsapp_command_logs` | Slash-command audit log (sensitive args like `/link`'s api\_key are scrubbed before write) |
| `whatsapp_notification_queue` | Retry queue for failed alerts (currently unused — single-user model drops on not-paired instead of queueing) |
| `whatsapp_user_preferences` | Per-user notification toggles + summary time + language + timezone |

Idempotent `PRAGMA table_info` migration adds `owner_user_id` + `owner_username` columns to `whatsapp_config` on existing installs.

***

**Dependencies**

* `wars==0.1.3` added — PyO3 binding over the whatsapp-rust crate; provides the WhatsApp Web client. Wheels available for Python 3.12+ via abi3.
* `openalgo` SDK pin: `1.0.49` → `1.0.50` (PyPI: <https://pypi.org/project/openalgo/1.0.50/>)
* `urllib3` `2.6.3` → `2.7.0` (`4519f55f`) — clears 8 Dependabot high-severity alerts
* `axios` `1.15` → `1.16`, `python-multipart` `0.0.26` → `0.0.27`, pin `pip>=26.1` (`6d61e5c6`)

***

**Documentation**

* New: `docs/api/whatsapp-services/README.md` — architecture + security model + slash-command reference
* New: `docs/api/whatsapp-services/notify.md` — full endpoint reference for `POST /api/v1/whatsapp/notify`
* New: `collections/openalgo/IN_stock/whatsapp_notify.bru` — Bruno collection entry (auto-discovered by `/playground`)
* Updated: `docs/api/README.md` — adds the WhatsApp Services section under the existing service taxonomy
* Updated: `docs/prompt/openalgo python sdk.md` — full `client.whatsapp(...)` reference with all four recipient forms, image/document attachments, fire-and-forget vs synchronous delivery, and inbound slash-command reference
* `52eb8650` — `docs(mcp): rewrite Remote MCP userguide for traders, drop stale install paths`
* `3b3054be` — `docs(claude): update CLAUDE.md with new product surfaces, Ruff tooling, and architecture details (#1412)`
* `1a7d3a0a` — `docs(claude): clarify sandbox terminology and split /sandbox vs /analyzer surfaces`
* `c7e5f4a9` — `docs(services): align order field names with canonical code (pricetype, product)`
* `83499518` / `e2de15ec` — Ubuntu Server Installation guide refresh

***

**Install + infrastructure**

* `79557be5` — `feat(install): inline Remote MCP prompt in install-docker.sh and install-multi.sh`
* `5c8b64b9` — `feat(install): prompt to enable Remote MCP during install.sh`
* `04eac147` — `feat(install): simplify single-deploy paths + drop enable-remote-mcp.sh`
* `647183bd` — `feat(remote-mcp): UI controls for master switch + posture toggles`
* `9ec851ab` — `fix(mcp): use HOST_SERVER for SDK loopback so install.sh deploys work`
* `5fa17bd3` — `fix(diagnostics): correct dead secret keys + git info inside Docker (#1388)`
* `f786e21a` — `chore: add Caddyfile for local https://openalgo.local dev`
* `4e09da8b` — `fix(python-strategy): Stop button works under gunicorn-eventlet (#1404)`

***

**Bug fixes (non-WebSocket)**

* `a4bdac18` — `fix(angel/api): defensive .get() in place_order response handling (#846)`
* `b06ef4a8` — `fix(kotak): align place/modify order payload with official Neo spec (#1398)`
* `ca15b333` — `fix(groww/api): support NSE_INDEX/BSE_INDEX in historical (#1338) (#1342)`
* `11778af5` — `fix(search): surface FUT-only MCX underlyings in symbol search (#1385)`

***

**Upgrade procedure**

**For existing installs (Native Ubuntu):**

```bash
cd /var/python/openalgo-flask/<deploy-name>/openalgo
sudo ./install/update.sh
# update.sh runs migrate_all.py — the new whatsapp_config / whatsapp_users
# tables and the owner_user_id column are created automatically. The
# FERNET_SALT migration runs on first boot inside env_check; existing
# broker-auth ciphertext is re-encrypted on the fly.
```

**For existing installs (Docker):**

```bash
cd /opt/openalgo/<domain>
sudo docker compose pull
sudo docker compose up -d
# The container's start.sh runs migrate_all.py before gunicorn boots.
# FERNET_SALT migration runs on first start.
```

**For local developers (uv):**

```bash
git pull origin main
uv sync
cd frontend && npm install && npm run build
uv run app.py
```

**Enabling WhatsApp** (post-upgrade, optional):

1. Log in to OpenAlgo, open `/whatsapp`.
2. Click **Start pairing**. A QR code appears.
3. On your phone: WhatsApp → Settings → Linked devices → Link a device → scan.
4. Done. The bot auto-starts and reconnects on every server boot from the encrypted session in `openalgo.db`.

The session blob never leaves your server. There is no second-party service to register with — it's a direct Signal-Protocol connection to WhatsApp.

***

**Contributors**

* **@marketcalls (Rajandran)** — release management; WhatsApp architecture and full implementation (database schema with Fernet-encrypted session blob + domain-separated salt, dedicated `WhatsAppBotThread` to satisfy PyO3's unsendable contract, event-bus subscriber wired into all 13 order topics, send-only REST API + session-authed admin blueprint, React `/whatsapp` page with auto-rotating QR, RUST_LOG suppression for the three known-noisy wars modules, attachment-path allowlist with traversal-token rejection, lazy own-JID capture from `is_from_me=True` messages, slash-command dispatcher with `is_from_me` gate, auto-reconnect on app boot); openalgo Python SDK 1.0.50 release with new `client.whatsapp(...)` API; WebSocket reliability sweep across 14 brokers (subscribe batching, reconnect hardening, fd-leak fixes); new IIFLCapital streaming adapter (#1416, #1430); Groww option chain + WS depth (#1392); Upstox GLOBAL_INDEX world feeds; Zerodha MCX_INDEX wiring (#1385); per-install Fernet salt rotation with crash-safe migration; websocket-proxy fixes (ZMQ bind #1378, mode normalization #1375, request_id correlation #1376, SharedZmqPublisher topology #1374); UI alignment fixes and stale-chunk auto-reload; comprehensive WhatsApp documentation (endpoint reference, SDK prompt-doc, Bruno collection entry).

***

**Links**

* **Repository**: <https://github.com/marketcalls/openalgo>
* **Documentation**: <https://docs.openalgo.in>
* **Python SDK on PyPI**: <https://pypi.org/project/openalgo/1.0.50/>
* **WhatsApp service docs**: <https://docs.openalgo.in/api-documentation/v1/whatsapp-services>
* **Discord**: <https://www.openalgo.in/discord>
* **YouTube**: <https://www.youtube.com/@openalgo>
* **Issue tracker**: <https://github.com/marketcalls/openalgo/issues>

***


---

# Agent Instructions: Querying This Documentation

If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.openalgo.in/change-log/release/version-2.0.1.1-released.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

```


---

# FILE: docs\releases\version-2.0.1.2-released.md

```md
# Version 2.0.1.2 Released

**Date: 28th May 2026**

**Maintenance + Performance Release: Option Greeks Rust Core (`opengreeks`, ~13× Faster Chain Refresh with Bit-for-Bit Parity), WebSocket Self-Healing + Subprocess Isolation Under Gunicorn-Eventlet, an Accessibility Sweep, Broker Data-Quality Fixes (Dhan Holdings, Definedge, Kotak Indices), and a Security/Dependency Sweep (ws CVE-2026-45736, SDK 1.0.51 Connection Pooling, idna)**

This release spans 20+ commits since v2.0.1.1. It is a stabilisation and performance pass on top of the WhatsApp release. The headline change is the **option Greeks engine swap** — `py_vollib` is replaced by `opengreeks`, a Rust + PyO3 Black-76 core with byte-identical function signatures, bit-for-bit numerical parity, and a ~13× speedup on a full option-chain refresh. Alongside it, the **WebSocket layer self-heals** on stale broker auth tokens (no more container restart after a new-trading-day re-login) and now runs as an **isolated subprocess under gunicorn-eventlet** to escape the greenlet/real-thread lock-switching hazard. The frontend gets an **accessibility sweep** (aria-labels on 63 icon-only buttons, color-contrast fixes). Three broker data-quality bugs are fixed (Dhan `/holdings`, Definedge master contract, Kotak index quotes). On security, the `ws` npm transitive dependency is patched (CVE-2026-45736), the bundled **openalgo SDK pin moves to 1.0.51** (a connection-pooling fix that prevents socket exhaustion in long-running strategies), and `idna` is bumped.

***

**Highlights**

* **Option Greeks Rust core — `opengreeks` replaces `py_vollib`** — The Black-76 backend for option Greeks and implied volatility is now a Rust + PyO3 core (`opengreeks==0.1.0`, NumPy-only runtime dep). Function signatures are byte-identical, so call sites change only their import path. Numerical parity is bit-for-bit on delta/gamma/theta/vega, float-64-last-bit on rho (7.9e-16), ~13 significant digits on IV. Pure-math speedups: implied volatility 46×, theta 28×, rho 19×, delta/vega/gamma 7–8×; a 40-option chain refresh (IV + 5 Greeks) drops **1.485 ms → 0.116 ms (~12.8×)**. Every downstream consumer (IV Smile, Vol Surface, GEX, IV Chart, Straddle Chart, Flow, `/api/v1/optiongreeks`, `/api/v1/multioptiongreeks`, MCP) routes through `option_greeks_service.calculate_greeks()` and inherits the speedup with no further changes.
* **WebSocket self-heals on stale auth tokens (#1419)** — When a broker adapter returns or raises an auth error (401/403/token expired) on connect or subscribe, the `ConnectionPool` now clears cached tokens, calls `initialize(force=True)` to re-read from `auth_db`, and retries once. Removes the container-restart requirement after a new-trading-day re-login.
* **WebSocket proxy runs as a subprocess under gunicorn-eventlet (#1421, #1438)** — In-process WS + Flask under eventlet shares one process with the eventlet hub, so monkey-patched stdlib locks touched from both the hub and the WS asyncio thread trigger `greenlet.error: Cannot switch to a different thread` and silently corrupt WS state. The app now detects eventlet at runtime (`is_monkey_patched("socket")`) and spawns `python -m websocket_proxy.server` as a child process with no monkey-patching, so all locks are real OS primitives. Atexit handler SIGTERMs with a SIGKILL fallback; the child stays in the gunicorn cgroup so systemd reaps it on hard crash. The dev-server path (no eventlet) is unchanged.
* **Accessibility sweep** — `aria-label` added to 63 icon-only buttons across the app, and 9 color-contrast violations resolved on the home page.
* **Broker data-quality fixes** — **Dhan `/holdings`** now enriches each row with the real exchange (NSE/BSE, resolved via `securityId` probe) and LTP (batch `get_multiquotes`) instead of passing through the demat-wide `"ALL"` placeholder with blank price/P&L (#1446). **Definedge** master contract had swapped `LotSize`/`TickSize` columns in `allmaster.csv` — now corrected (#1450, #1457). **Kotak** index quotes resolve for `MIDCPNIFTY` and other indices (#1436).
* **Security + dependency sweep** — `ws` npm transitive dependency patched for CVE-2026-45736 (uninitialized memory disclosure) via an `overrides` pin to `>=8.20.1` (resolves to 8.21.0); bundled `openalgo` SDK pin `1.0.50` → `1.0.51` (connection-pooling fix); `idna` `3.11` → `3.15`; unused `scipy` pin dropped; `py_vollib==1.0.1` + `py_lets_be_rational==1.0.1` removed (superseded by `opengreeks`).
* **Platform version bump** — `2.0.1.1` → `2.0.1.2`. SDK pin (`openalgo`) `1.0.50` → `1.0.51`.

***

**Option Greeks — Rust core deep dive**

`perf(greeks): replace py_vollib with opengreeks Rust core` — `8d973504`.

The Greeks/IV math previously ran on `py_vollib==1.0.1` (pure Python, backed by `py_lets_be_rational`). This release swaps it for `opengreeks==0.1.0`, a Rust + PyO3 implementation with a NumPy-only runtime footprint.

**Why it's a drop-in:** function signatures are byte-identical, so the migration touches only import paths in `services/option_greeks_service.py` (and `services/iv_chart_service.py`, `broker/dhan_sandbox/api/data.py`). Nothing about the public API or response shape changes.

**Numerical parity** (40-sample replay, NIFTY 26-MAY-2026 chain):

| Quantity | Abs error vs py_vollib |
| --- | --- |
| delta / gamma / theta / vega | 0.0e+00 (bit-for-bit identical) |
| rho | 7.9e-16 (float-64 last bit) |
| implied_volatility | 4.1e-13 (~13 significant digits) |

**Pure-math speedup** (5000-rep median, ATM call):

| Function | Before | After | Speedup |
| --- | --- | --- | --- |
| implied_volatility | 17.29 µs | 0.38 µs | 46.1× |
| theta | 5.79 µs | 0.21 µs | 27.7× |
| rho | 3.96 µs | 0.21 µs | 18.9× |
| delta / vega / gamma | ~1.5 µs | 0.21 µs | 7–8× |
| **40-option chain refresh (IV + 5 Greeks)** | **1.485 ms** | **0.116 ms** | **12.8×** |

**Migration evidence** is captured in `docs/benchmarks/` (baseline JSON + MD, post-migration JSON, parity + speedup report) and is reproducible via the new `scripts/bench_greeks_*.py` / `scripts/bench_parity_opengreeks.py` suite.

***

**WebSocket reliability**

`d077559f` bundles two fixes from @Kalaiviswa:

* **`fix(websocket): self-heal pool on stale auth-token failure (#1419)`** — `ConnectionPool` detects auth errors on connect/subscribe, clears cached tokens, re-initializes from `auth_db` with `force=True`, and retries once. The common symptom this kills: WS data silently stops after the ~3:00 AM IST broker token rollover until the operator restarts the container.
* **`fix(websocket): spawn WS proxy as subprocess under gunicorn+eventlet (#1421) (#1438)`** — Under eventlet, the WS asyncio thread and the eventlet hub share monkey-patched stdlib locks (logging `RLock`, socket.io lock, broker adapter `threading.Lock`), which can throw `greenlet.error: Cannot switch to a different thread` and corrupt WS state. The proxy now runs as a separate, un-monkey-patched child process when eventlet is active; the dev server (standard threading) is unchanged.

***

**Frontend + accessibility**

* `ce597e52` — `fix(a11y): add aria-label to 63 icon-only buttons`
* `7b2ab7c5` — `fix(a11y): resolve 9 color-contrast violations on home page`
* `bb147762` — `fix(frontend): silence vite build warnings`
* `da6a6826` — `fix(frontend): use automatic JSX runtime in vitest`
* `f0246d00` — `style(frontend): apply biome safe-fix cleanup`
* A `vite 7 → 8` / `@vitejs/plugin-react 5 → 6` bump (`0804b6ee`) was attempted and then **reverted** (`d4e881f0`); the toolchain remains on `vite ^7.3.2`.

***

**Broker fixes**

* `c3bb4436` — `fix(dhan): enrich /holdings with real exchange + LTP (#1446)` — Dhan's `/v2/holdings` returns `exchange="ALL"` for every row and omits LTP (only `avgCostPrice`). `map_portfolio_data` now resolves the real NSE/BSE exchange via a `securityId` probe and batch-fetches LTP via `get_multiquotes`, restoring the exchange badge, Avg Price/LTP, P&L, and the real-time WebSocket subscription on the Investor Summary UI.
* `abbcd2ec` — `fix(definedge): correct swapped LotSize/TickSize columns in allmaster.csv (#1450) (#1457)`
* `3099a4e4` — `fix(kotak): resolve index quotes for MIDCPNIFTY and other indices (#1436)`
* `b4134b41` — `fix(whatsapp): make normalize_phone tolerate int phones, reject float/bool`

***

**Admin + infrastructure**

* `d5ee335f` — `fix(admin): handle Docker bind-mounted .env on MCP settings save (#1337)`
* `7e48b2e8` — `feat(scripts): add broker token extraction utility for self-hosted owners` (`scripts/extract_broker_token.py`)
* `a226839c` — `feat(examples): add PyPI download-stats comparator for Indian broker SDKs` (`examples/python/broker_sdk_downloads.py`)

***

**OpenAlgo Python SDK 1.0.51 — connection pooling fix**

Released to PyPI alongside this version and pinned by the platform (`openalgo==1.0.50` → `1.0.51`).

* **The problem:** every REST call (orders, quotes, funds, history, …) opened a brand-new TCP connection and discarded it. Over a full trading day that left thousands of sockets in `TIME_WAIT`, eventually exhausting the OS's ephemeral ports — often misread as a memory/RAM crash when the real cause was socket exhaustion.
* **The fix:** the SDK now reuses a single shared, connection-pooled HTTP client (keep-alive) across all REST calls instead of opening a fresh connection each time. The Strategy webhook sender got the same treatment.
* **What you get:** flat socket count all day (no port/socket exhaustion in long sessions), lower per-call latency (no repeated TCP/TLS handshake), lower CPU and kernel overhead, and clean shutdown via `client.close()` / context-manager support.
* **Note:** the reuse benefit is fully realized in production behind gunicorn (keep-alive). The local dev server closes connections per request, so the effect is less visible there.
* Available at <https://pypi.org/project/openalgo/1.0.51/>.

***

**Security — `ws` CVE-2026-45736**

A moderate-severity Dependabot alert (GHSA-58qx-3vcg-4xpx, CVE-2026-45736 — uninitialized memory disclosure in `ws`) flagged a transitive npm dependency reachable through `socket.io-client → engine.io-client`, which pinned `ws: ~8.18.3` and so locked the resolution to the vulnerable 8.18.x line.

* Fix: added `"ws": ">=8.20.1"` to the existing `overrides` block in `frontend/package.json`; the lockfile now resolves `ws` to **8.21.0**. `npm install` reports **0 vulnerabilities**.
* No browser-bundle impact: `socket.io-client` uses the browser's native `WebSocket` in the React build, not the Node `ws` package — the override only affects the Node-side dependency graph and the lockfile that Dependabot scans.

***

**Dependencies**

* `opengreeks>=0.1.0` added — Rust + PyO3 Black-76 Greeks/IV core; NumPy-only runtime footprint. Replaces `py_vollib`.
* `py_vollib==1.0.1` and `py_lets_be_rational==1.0.1` **removed** (superseded by `opengreeks`).
* `openalgo` SDK pin: `1.0.50` → `1.0.51` (PyPI: <https://pypi.org/project/openalgo/1.0.51/>) — connection-pooling fix.
* `idna` `3.11` → `3.15`.
* `scipy` — unused pin dropped (`a1eca63b`).
* `ws` (npm, transitive) → `>=8.20.1` override, resolves to 8.21.0 (clears Dependabot alert 180 / CVE-2026-45736).

***

**Configuration changes**

`pyproject.toml`:

* `version = "2.0.1.2"`
* `opengreeks>=0.1.0` added; `py_vollib==1.0.1` + `py_lets_be_rational==1.0.1` removed
* `openalgo==1.0.50` → `openalgo==1.0.51`
* `idna==3.11` → `idna==3.15`
* unused `scipy` pin removed

`utils/version.py`:

* `VERSION = "2.0.1.2"`

`requirements.txt` + `requirements-nginx.txt`:

* `opengreeks==0.1.0` added; `py_vollib` / `py_lets_be_rational` removed
* `openalgo==1.0.50` → `openalgo==1.0.51`
* `idna==3.11` → `idna==3.15`

`frontend/package.json`:

* `overrides` gains `"ws": ">=8.20.1"`

***

**Upgrade procedure**

**For existing installs (Native Ubuntu):**

```bash
cd /var/python/openalgo-flask/<deploy-name>/openalgo
sudo ./install/update.sh
# update.sh runs migrate_all.py. No schema migration is required for this
# release; uv sync pulls opengreeks and drops py_vollib automatically.
```

**For existing installs (Docker):**

```bash
cd /opt/openalgo/<domain>
sudo docker compose pull
sudo docker compose up -d
```

**For local developers (uv):**

```bash
git pull origin main
uv sync
# Frontend: a plain pull already ships the CI-built dist. Only rebuild if
# you are editing React code:
cd frontend && npm install && npm run build
uv run app.py
```

There are no new environment variables and no database schema changes in this release.

***

**Contributors**

* **@marketcalls (Rajandran)** — release management; option Greeks Rust-core migration (`py_vollib` → `opengreeks`) with parity + speedup benchmark suite; Dhan `/holdings` exchange + LTP enrichment (#1446); Kotak index-quote resolution (#1436); accessibility sweep (63 aria-labels + color-contrast fixes); frontend build-warning cleanup and biome safe-fixes; Docker bind-mounted `.env` handling on MCP settings save (#1337); broker token extraction utility and PyPI download-stats example; dependency + security sweep (ws CVE-2026-45736 override, SDK 1.0.51 connection-pooling pin, idna bump, scipy drop); openalgo Python SDK 1.0.51 release.
* **@Kalaiviswa** — WebSocket self-heal on stale auth-token failure (#1419) and WS-proxy subprocess isolation under gunicorn-eventlet (#1421, #1438).
* **Community** — Definedge `allmaster.csv` LotSize/TickSize fix (#1450, #1457).

***

**Links**

* **Repository**: <https://github.com/marketcalls/openalgo>
* **Documentation**: <https://docs.openalgo.in>
* **Python SDK on PyPI**: <https://pypi.org/project/openalgo/1.0.51/>
* **Discord**: <https://www.openalgo.in/discord>
* **YouTube**: <https://www.youtube.com/@openalgo>
* **Issue tracker**: <https://github.com/marketcalls/openalgo/issues>

```
