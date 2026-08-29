# Market Depth Recorder Microservice - Enhanced Design Specification

## 1. System Overview & Objective
The **Market Depth Recorder** is a production-grade, standalone Python microservice engineered to capture, compute, and persist real-time market depth data for the configured weekly option chains (initially **NIFTY** and **SENSEX**).

> **Depth-level reality (verified against OpenAlgo/FYERS source).** OpenAlgo's default depth is **5 levels**; deeper books (20/30/50) are *broker-capability dependent* (`websocket_proxy/mapping.py::get_supported_depth_levels`, `base_adapter.py:254`). True **50-level** depth is available **only via FYERS' separate tick-by-tick (TBT) WebSocket**, and the FYERS adapter restricts TBT to `TBT_SUPPORTED_EXCHANGES = {"NSE", "NFO"}` (`broker/fyers/streaming/fyers_websocket_adapter.py:44`). Practical consequence: **NIFTY** options (exchange **NFO**) get true 50-level depth, but **SENSEX** options trade on **BFO**, which is *not* TBT-supported and therefore degrade to **5-level** depth. The recorder must **auto-detect the actual depth level per symbol** and record whatever the feed delivers (best-effort), never assume 50. **Live-verified cap — FROZEN (2026-07-14, P10-E/P10-F; supersedes the 2026-07-06 P9 reading):** FYERS' TBT feed limits Market-Depth subscriptions to **5 symbols per _connection_**, with **3 connections per app per user** and **50 channels per connection**. Channels are a **pause/resume logical grouping and carry no capacity** — they do **not** multiply the 5-symbol limit. The effective ceiling is therefore **`tbt_budget = 15` (3 × 5)**, confirmed live (15 distinct legs concurrent; a 4th connection refused). Stock OpenAlgo pinned *every* 50-depth subscription to channel `"1"` (`broker/fyers/streaming/fyers_websocket_adapter.py`), so the broker returned `symbol count exceeds limit: 5` and a large NIFTY chain silently starved. **The P9-era claim of "5 symbols per channel × 50 channels = ceiling 250" is disproven**; the OpenAlgo channel-spread patch is kept (harmless, and its channel-resume plumbing is correct) but it buys **15, not 250**. **Consequence: a full NIFTY chain at 50-level is not achievable.** Reaching 15 requires the **hybrid** — near-ATM legs at 50-level within `tbt_budget`, the rest at 5-level — over a multi-connection broker layer. `tbt_budget` is a broker **capability**, not an architectural constant: the allocator consumes one logical budget and connection management stays hidden behind the broker-capability layer, so the engine remains broker-agnostic. This protocol layer is **FROZEN unless new external evidence emerges**. Canonical evidence: `Documents/evidence/fyers_tbt_concurrency_20260714/tbt_concurrency_reconciliation_20260714.md`; see also `Documents/evidence/openalgo_platform/OPENALGO_PATCH.md` §8 and `plans/Plan_001_evidence/Phase9_notes.md` (original, superseded finding). See §3.3 for the `:50` subscription mechanism and §3.2.5 for the capability preflight.

Option market depth data is extremely heavy, bursting up to hundreds of updates per second across dozens of active strike prices. To capture this flow without dropping packets or bottlenecking execution, the recorder uses a **three-tier storage pipeline** — a **thin, low-latency live path** during market hours and a **fat, exhaustive offline path** after close, both derived from the same lossless raw log:

1.  **Raw WebSocket Logs — source of truth (Tier 0, always live):**
    *   *Purpose:* Retain 100% of the raw, unedited tick feed from OpenAlgo, including broker-timestamped order book shifts, raw quantities, and order counts.
    *   *Format:* Every JSON depth snapshot is written as a single line to a gzip-compressed flat file (`market_depth_raw_YYYYMMDD.jsonl.gz`). This minimizes file size while preserving the full feed for replay.
2.  **Thin Live Metrics — signal path (Tier 1, live, minimal):**
    *   *Purpose:* Feed *live* strategies/dashboards with only the metrics a real-time signal actually needs, at 1-second cadence, keeping in-session CPU and write load low.
    *   *Scope:* A **configurable subset** (`recorder.live_metrics`, e.g. spread, weighted OBI, book pressure, best bid/ask qty, ATM aggregates + regime) — *not* the full 24-metric catalog. Written to a small daily live store.
3.  **Full Analytical Metrics — backtest path (Tier 2, offline, exhaustive):**
    *   *Purpose:* The complete per-strike catalog (all 24 metrics), rolling-window metrics (5/10/30s), and multi-strike aggregates for research/backtesting.
    *   *How:* Produced by **replaying the raw log through the same processor with the full metric set enabled** (§8). This runs **automatically at end-of-session** (post-teardown), with a scheduled fallback and on-demand invocation (§8.6). Because it never competes with live capture, the fat path can afford the exhaustive computation.
    *   *Format:* A daily-rotated **DuckDB** analytical store (`market_depth_analytics_YYYYMMDD.duckdb`, columnar — schema in §4), written in a single bulk pass by the offline build and aligning with the platform's existing `db/historify.duckdb`. DuckDB's columnar layout and vectorized scans suit the analytical/backtest access pattern (wide column subsets, full-session range scans) far better than a row-store.

> **Why split thin/fat:** the raw log makes every metric reconstructable offline, so the live process need not compute the entire catalog under burst load. This removes the real-time CPU/write pressure that motivated "degraded mode" (§5.1) and guarantees the exhaustive dataset is ready before the next session — without ever risking the live signal path.

---

### 1.1 Architecture Context & System Topology
The microservice functions as a high-throughput bridge between the OpenAlgo API Gateway/WebSocket proxy and downstream trading systems (e.g., algorithmic execution containers, visualization dashboards, and machine learning models).

```
 ┌──────────────────────┐         ┌────────────────────────┐         ┌────────────────────────┐
 │   OpenAlgo Gateway   │ ──REST─►│ Instrument & Expiry Mg │ ──Maps─►│ Dynamic Strike Manager │
 │ (REST / WebSocket)   │         │ (Expiry / Strike Step) │         │    (Boundary Check)    │
 └──────────┬───────────┘         └────────────────────────┘         └───────────┬────────────┘
            │                                                                    │
         WS Ticks                                                          WS Subscribe
            │                                                                    │
            ▼                                                                    ▼
 ┌──────────────────────┐         ┌────────────────────────┐         ┌────────────────────────┐
 │  WebSocket Client    ├────────►│ Raw Queue (Memory FIFO)├────────►│  Dynamic WS Manager    │
 └──────────────────────┘         └───────────┬────────────┘         └────────────────────────┘
                                              │
                                     ┌────────┴────────┐
                                     ▼                 ▼
                          ┌────────────────────┐   ┌────────────────────┐
                          │ Gzip File Writer   │   │  Metric Processor  │
                          │ (Raw JSONL Logs)   │   │  (NumPy Engine)    │
                          └────────┬───────────┘   └───────────┬────────┘
                                   │                           │
                                Disk Log                  DB Records
                                   │                           │
                                   ▼                           ▼
                          ┌────────────────────┐   ┌────────────────────┐
                          │  .jsonl.gz File    │   │ SQLite Batch Writer│
                          └────────────────────┘   └───────────┬────────┘
                                                               │
                                                               ▼
                                                   ┌────────────────────┐
                                                   │    SQLite .db      │
                                                   └────────────────────┘
```

---

### 1.2 High-Throughput & Volumetric Constraints
Market depth feeds for options are verbose. Under normal market conditions:
*   A single active contract generates between **20 and 50 depth updates per second**.
*   During periods of high volatility, this rate can burst to **150+ updates per second**.
*   *(Illustrative, with the default two-underlying config — actual counts derive from each underlying's `initial_window`/`expansion_step` in §7.)* With an initial monitoring window of $\approx 2000$ points for NIFTY ($\approx 41$ strikes $\times 2$ options = 82 active contracts) and $\approx 6000$ points for SENSEX ($\approx 61$ strikes $\times 2$ options = 122 active contracts), the service monitors on the order of **200 concurrent option contracts**; capacity planning must scale with the number of configured underlyings, not assume two.
*   **Aggregated Input Rate:** The system is engineered to handle an average incoming rate of **4,000 to 8,000 packets per second**, with flash bursts exceeding **12,000 packets per second** without dropping messages or introducing pipeline lag.

---

### 1.3 System Design Philosophy
To ensure production reliability on local machines without complex system dependencies, the microservice is built around three core design principles:
1.  **Zero-Dependency Standalone Model:** The service requires only standard Python libraries plus NumPy, SQLite3, **DuckDB**, and the **OpenAlgo Python SDK** (`openalgo`) for the feed transport — all **embedded, in-process** libraries. DuckDB (like SQLite) runs inside the process and the SDK is a client library, so this does **not** introduce an external database server: there is still no PostgreSQL/MongoDB daemon and no network message broker (RabbitMQ, Redis) beyond OpenAlgo's own proxy that the recorder connects to as a client. Installation stays a simple `pip install`, and the live footprint stays under 500 MB (the DuckDB bulk build runs in the *separate* end-of-session replay subprocess, so its memory does not add to the live recorder's). The recorder ships a **standalone `requirements.txt` and runs in its own virtual environment** (it imports only the `openalgo` client library, not the platform source), so it can run on a separate core/host from OpenAlgo. *(The `websocket-client`-based raw transport of §3.3.1a is the **primary/default** capture path — see the verified-finding note in §3.3.1 — and adds no server dependency either.)*
2.  **Concurrency Separation (Thread Isolation):** Network I/O, raw file logging, CPU-bound computations, and database commits are assigned to dedicated background threads. They communicate using thread-safe, non-blocking FIFO queues (`queue.Queue`), ensuring that slow disk operations never block network packet reads.
3.  **Self-Healing & Unsupervised Operation:** The orchestrator is designed to start automatically via cron schedule, detect and resolve connection outages using exponential backoff, dynamically expand options chains as market spot prices move, and gracefully flush write buffers during daily shutdown.

---

### 1.4 Performance Targets & Guarantees
*   **Network Capture (bounded, audit-protected):** The WebSocket receiving thread never blocks on socket reads and sustains loads of ~15,000 updates/sec. Capture is **lossless for the raw audit path except under genuine disk saturation** — the receiver applies backpressure to `raw_file_queue` before shedding, and any raw drop (only if the disk cannot keep up) is **counted and logged at ERROR**. The analytics path (`proc_queue`) is allowed to shed first under overload. (This replaces the earlier unconditional "zero dropped packets" claim, which a bounded drop-on-full queue cannot actually guarantee.)
*   **Computation Latency:** Vectorized metric calculations completed in **$< 15$ milliseconds** per 1-second resampler cycle using NumPy array operations.
*   **Disk Write Latency:** Batched SQLite transaction commits executed in **$< 50$ milliseconds** per commit, avoiding I/O blocking.
*   **Resource Footprint:** Maximum CPU utilization $< 15\%$ on a standard quad-core CPU, with memory usage capped at **$500$ MB** under maximum load.

---

## 2. Directory Layout & Module Flow

The microservice is isolated inside its own folder to ensure it can run on a separate CPU core or host.

### 2.1 Recorder Directory Schema
```
market_depth_recorder/
│
├── config.example.yaml      # Tracked, credential-free configuration template
├── config.yaml              # Local runtime config copied from the template; git-ignored, never committed
├── main.py                  # Orchestrator daemon, lifecycle manager, and schedule loop
├── instrument_manager.py    # Expiry detection, symbol filter, and strike step auto-detector
├── websocket_client.py      # OpenAlgo SDK feed wrapper (connect/subscribe/resubscribe + DSM boundary manager); raw-WS fallback
├── processor.py             # Resampling engine, mathematical metrics, and aggregations
├── database_writer.py       # Two writers: SQLiteLiveWriter (thin live, per-second commits) + DuckDBAnalyticalWriter (fat offline, bulk load)
├── file_writer.py           # Thread-safe gzip JSONL flat-file logger
├── replay.py                # Offline reprocess: raw .jsonl.gz → DuckDB analytical store (§8)
├── utils.py                 # Math helpers (decay arrays), logger configurations, and time calculations
├── metrics/registry.py      # Declarative metric registry (§3.4.0) — extension point for M1..M29+
├── requirements.txt         # Standalone dependency pins (openalgo, numpy, duckdb, pyyaml, websocket-client)
├── Documents/               # Living docs: ARCHITECTURE.md, CHANGELOG.md, per-module references
├── tests/                   # pytest suites (config, instrument, processor, replay, …) — no live feed needed
│
└── data/                    # Local storage directory for daily rotated databases and raw files
    ├── market_depth_raw_20260702.jsonl.gz   # Tier 0: compressed raw WebSocket tick logs (source of truth)
    ├── market_depth_live_20260702.db         # Tier 1: THIN live store (SQLite/WAL) — configurable metric subset, written during market hours
    ├── market_depth_live_20260702.db-wal     # SQLite Write-Ahead Log temporary file (thin live store)
    ├── market_depth_live_20260702.db-shm     # SQLite Shared Memory index file (thin live store)
    ├── market_depth_analytics_20260702.duckdb # Tier 2: FAT analytical store (DuckDB) — full metric catalog, bulk-built offline at end-of-session (§8, §8.6)
    ├── market_depth_20260702.replay.duckdb   # (optional) ad-hoc DuckDB replay output for formula changes / diffs (`--output`, §8.4)
    └── health.json                           # Cross-platform liveness file (§6.4; path is config-driven)
```

The two derived stores are intentionally different **shapes and backends**:
*   **Thin live store — SQLite/WAL.** Carries only the `recorder.live_metrics` subset, written incrementally as ~1 small transaction/second during market hours. This append-mostly, high-frequency, single-writer OLTP pattern is exactly what SQLite/WAL handles well; it stays cheap so the live path never bottlenecks capture.
*   **Fat analytical store — DuckDB.** Carries the exhaustive §4 catalog, written in a **single bulk pass** by the offline build. DuckDB is a columnar OLAP engine — great for one big write followed by wide analytical scans, and it aligns with the platform's existing `db/historify.duckdb`. It is deliberately **not** used for the live path: DuckDB is a single-writer store optimized for bulk loads, not thousands of small per-second transactions.

Both are reconstructable from Tier 0 at any time, so neither is a single point of loss. (DuckDB stores each day in one `.duckdb` file — no `-wal`/`-shm` sidecars persist after the bulk write is checkpointed and the connection closed.)

---

### 2.2 End-to-End Data Pipeline & Execution Flow
The lifecycle of a single data point follows a sequence of actions distributed across thread boundaries:

1.  **Phase A: Configuration Loading & Bootstrapping (09:00 AM)**
    *   `main.py` starts, reads `config.yaml`, and initiates standard loggers.
    *   `main.py` initializes `InstrumentManager`, which executes HTTP REST queries to OpenAlgo, resolves the weekly option contract expiry date ($E_{\text{weekly}}$), auto-calculates index strike step modes ($\Delta_{\text{strike}}$), and builds the static index lookup tables.
2.  **Phase B: Spot Handshake & Base Subscriptions (09:10 AM)**
    *   `main.py` instantiates `DepthWebSocketClient` (the SDK-feed wrapper, §3.3.1) and calls `client.connect()`.
    *   Upon successful connection, the transport handles authentication and the wrapper registers `subscribe_ltp` for index spot trackers. **OpenAlgo symbol format:** spot indices are `symbol="NIFTY"` / `exchange="NSE_INDEX"` and `symbol="SENSEX"` / `exchange="BSE_INDEX"` (the `EXCHANGE:SYMBOL` colon form is *not* OpenAlgo's convention). Indices expose only *synthetic* depth, so spot is always subscribed in LTP mode.
3.  **Phase C: Strike Discovery & Option Chain Registration (09:15 AM)**
    *   As the first spot LTP ticks arrive, the client thread routes them to the Dynamic Strike Manager (DSM).
    *   The DSM resolves the At-The-Money (ATM) index strikes, sets up boundary parameters ($B_{\text{lower}}$ and $B_{\text{upper}}$), maps option strike prices, resolves option symbol names from lookups, and transmits the subscription frames to OpenAlgo.
4.  **Phase D: High-Speed Receiving & Fan-Out (Market Hours)**
    *   The WebSocket thread receives JSON depth packets. It bypasses heavy parsing and **fans each packet out to TWO independent queues** — `raw_file_queue` (audit) and `proc_queue` (analytics). This is a *tee*, not a shared queue: a single `queue.Queue` delivers each item to exactly one consumer's `get()`, so the raw logger and the processor **must not** read the same queue or each would see only ~half the ticks. See §5.1 for the corrected topology and the per-queue backpressure policy (audit is protected; analytics is the first to shed load).
5.  **Phase E: Compressed Audit Logging**
    *   The `RawTickFileWriter` background thread pulls items from `raw_file_queue`.
    *   It serializes the dictionary to a single-line JSON string, appends it to the active gzip `.jsonl.gz` handle, and flushes/`fsync`s on the buffered schedule in §3.5.3 (count- **or** time-based) — **not** a hard `os.fsync` every 100 entries, which at multi-kHz rates would issue ~80 fsyncs/sec and defeat the "shield the receiver from disk latency" goal.
6.  **Phase F: Time-Slice Resampling & Aggregation**
    *   The `TickProcessor` background thread pulls items from `proc_queue` and maintains an in-memory symbol tick cache.
    *   Once per second, a timer triggers a resampler pass:
        *   Extracts cache snapshots, applying forward-fill or staleness checks.
        *   Runs mathematical calculations using NumPy arrays (spread, OBI, pressures).
        *   Appends values to rolling time window deques.
        *   Performs multi-strike aggregations (Net bias, PCR, Regime shifts).
        *   Packages the resulting datasets and pushes them to `db_queue`.
7.  **Phase G: Transaction Database Commit**
    *   The `SQLiteLiveWriter` background thread monitors `db_queue`.
    *   Every 500 rows or 1 second, it initiates an atomic write transaction, runs bulk insertion queries, commits the batch, and logs database warnings.

---

### 2.3 Threading & Memory Allocation Model
Because Python runs under a Global Interpreter Lock (GIL), the threading model is designed to optimize execution:
*   **GIL Bypassing:**
    *   *I/O Operations:* Socket reads, file compression (`gzip`), and SQLite writes release the GIL, allowing threads to execute concurrently.
    *   *Mathematical Operations:* NumPy calculations are executed in compiled C arrays, releasing the GIL during array operations.
*   **Memory Safety & Queue Boundaries:**
    *   Three bounded queues exist: `raw_file_queue` (WS→audit), `proc_queue` (WS→analytics), and `db_queue` (processor→SQLite), each with a configurable `maxsize` (default `50000`). Bounding prevents unbounded memory growth if a downstream stage stalls (disk full, I/O failure).
    *   **Per-queue shedding priority (not a single "drop at the client boundary" rule):** the audit path is the last to shed. Under sustained overload the order is (1) throttle/shed the **analytics** `proc_queue` first, (2) then `db_queue`, and only if `raw_file_queue` itself saturates (disk genuinely cannot keep up) is a raw packet dropped — and every such drop is counted and logged so the "lossless raw" claim is never silently violated (see §5.1 and the honest restatement of guarantees in §1.4).
*   **Lock Isolation:**
    *   The only shared resource between threads is the list of active subscriptions (`active_subscriptions`), which is protected by a reentrant lock (`threading.RLock()`) to prevent race conditions between the WebSocket receiver, DSM boundary expansions, and processing loops. All other variables are local to their respective threads.

---

## 3. Detailed Component Design

### 3.1 Orchestrator & Schedule Daemon (`main.py`)
This module drives the execution lifecycle of the microservice. It runs on the main thread as a daemon supervisor, operating a time-comparison loop that evaluates the local system clock against key session milestones.

#### 3.1.1 Time-Comparison Loop & Milestone State Machine
To avoid CPU spikes, the daemon runs a loop that sleeps for 1 second (`time.sleep(1)`) on each cycle. The schedule state machine is governed by five main milestones:

*   **Milestone 1: 09:00 AM – Initialization Phase**
    *   *Task:* Instantiates `InstrumentManager`. Downloads the master instrument list via REST API, parses weekly option contracts, extracts the current active expiration, and calculates index strike step intervals.
    *   *I/O Tasks:* Resolves the daily output directory (e.g., `./data/`), runs database integrity checks on the daily SQLite database file, and configures daily gzip file logging parameters.
*   **Milestone 2: 09:10 AM – Feed Connection Phase**
    *   *Task:* Instantiates `DepthWebSocketClient` (the SDK-feed wrapper, §3.3.1) and connects to the OpenAlgo proxy via `client.connect()` — authentication is handled by the transport (SDK internally, or the `authenticate` frame on the raw fallback).
    *   *Subscription Task:* Registers index spot ticker LTP subscriptions via `subscribe_ltp` — `NIFTY`/`NSE_INDEX` and `SENSEX`/`BSE_INDEX` in OpenAlgo symbol/exchange format (raw equivalent: LTP `mode=1`). It does not yet subscribe to option strikes.
*   **Milestone 3: 09:15 AM – Active Recording Phase**
    *   *Task:* Launches background execution threads: `TickProcessor` (resampling and calculations), `RawTickFileWriter` (gzip logging), and `SQLiteLiveWriter` (batched metric storage).
    *   *Dynamic Manager Task:* Resolves the initial ATM strike from the incoming spot ticks, sets up upper/lower boundaries, and registers option subscriptions.
*   **Milestone 4: 03:30 PM – Subscription Closure Phase**
    *   *Task:* Disables the Dynamic Strike Manager (DSM) boundary checking loop.
    *   *WebSocket Tasks:* Transmits unsubscribe payloads for all active option symbols to the WebSocket proxy, freeing network bandwidth.
*   **Milestone 5: 03:35 PM – Graceful Teardown Phase**
    *   *Task:* Signals all background threads to terminate by setting a global shutdown event (`self.shutdown_event = threading.Event()`).
    *   *Flushing Protocol:* Drains memory queues, commits the remaining **thin-live** rows, flushes and closes the gzip raw file handle (writing its EOF marker), and joins threads.
*   **Milestone 6: 03:35 PM+ – End-of-Session Reprocess (fat path, automatic):**
    *   After a **clean** teardown (raw log closed with a valid EOF), the orchestrator launches the **offline reprocess** of the day's raw log to build the full DuckDB analytical store `market_depth_analytics_YYYYMMDD.duckdb` (§8), gated on `reprocess.auto_on_session_end`. It runs as a **separate subprocess** so a crash/slowness in reprocessing can never affect the recorder; its stdout/stderr are redirected to `reprocess.log_file` (a file, not a PIPE) and the child is `wait()`-reaped (FD hygiene). On completion (or if it was skipped because the shutdown was unclean), the main loop sleeps until 09:00 AM the next day. The scheduled fallback (§8.6 mode 2) covers any day whose reprocess did not complete.

---

#### 3.1.2 Mid-Day Startup & Resiliency Engine
If the microservice process is restarted mid-day (e.g., following a power loss, network dropout, or server reboot), the orchestrator executes the following recovery path:
1.  **State Evaluation:** Checks if the startup timestamp falls within active recording hours:
    $$\text{09:15 AM} \le T_{\text{current}} < \text{03:30 PM}$$
2.  **Bypass Gating:** If true, the orchestrator bypasses Milestone 1 & 2 delays and goes straight to initialization.
3.  **One-Shot Spot Resolution:** Executes a direct REST API call (`/api/v1/quotes`) to retrieve the latest spot price for **each configured underlying**. This resolves the current At-The-Money (ATM) strike price instantly rather than waiting for WebSocket updates.
4.  **Immediate Subscription:** Launches the DSM with boundaries centered on the retrieved spot price, subscribes to option strikes, starts the processing/writing threads, and immediately enters the active recording phase.

---

#### 3.1.3 Thread Supervisor & Exception Gating
Recorders must be self-healing. The orchestrator implements a supervisor pattern to prevent silent failures:
*   **Sentinel Error Register:** Background threads (`processor`, `file_writer`, `db_writer`) are wrapped in `try/except` blocks. If an uncaught exception occurs (e.g., SQLite file write lockup or Gzip file system error), the thread writes its exception details to a shared, thread-safe error queue.
*   **Health Checks:** Every 5 seconds, the main orchestrator checks the status of all background thread handles (`is_alive()`) and scans the error queue.
*   **Fail-Fast Recovery:** If a thread crash is detected, the supervisor sets `self.shutdown_event`, halts all remaining threads, cleans up sockets, and restarts the entire recording loop to resume data capture within seconds.

---

#### 3.1.4 Atomic Queue Flushing & Data Loss Prevention
To ensure no data is lost during shutdown, the teardown phase follows a strict queue flushing protocol:
1.  **Shutdown Gating:** When `self.shutdown_event` is set, background threads stop receiving new inputs but continue processing.
2.  **Ordered Drain:** Threads exit only once their input queue is empty (`queue.empty() == True`). Order matters: the `TickProcessor` must fully drain `proc_queue` and flush its final 1-second cycle into `db_queue` **before** the `SQLiteLiveWriter` is allowed to finish; the `RawTickFileWriter` independently drains `raw_file_queue`. So the shutdown join order is **processor → db_writer**, with **raw_file_writer** joined in parallel.
3.  **Handle Disposal:** The orchestrator waits for the writer threads to join (`thread.join(timeout=10)`) before closing the SQLite database connection and writing the final gzip EOF marker. This guarantees that all metrics computed up to 03:30 PM are written to disk.
4.  **Signal-triggered graceful teardown (P8):** the normal teardown above is driven by the milestone clock (`session_end + teardown_grace_min`) or a `KeyboardInterrupt` (SIGINT). Because the workers are `daemon=True`, an OS `SIGTERM` (systemd / `docker stop`) would otherwise hard-kill them mid-write and skip this protocol (losing the EOF marker + FD close). The live daemon therefore registers a **SIGTERM** handler → `orchestrator.stop()`, routing a managed shutdown through the same ordered drain / EOF / FD-close path, so the lossless-raw invariant holds under production supervisors. (Registration is best-effort: main thread + SIGTERM support; real OS-signal delivery is validated in the P9 live run.)

#### 3.1.5 Session Guards (disk space & trading calendar)
Two lightweight guards protect unattended operation:
*   **Disk-space guard:** at startup and every `recorder.disk_check_interval_sec`, the orchestrator checks free space on `recorder.output_dir`. Below `recorder.min_free_disk_mb` it logs an **ERROR** — the lossless-raw invariant (§1.4/§5.1) permits a raw drop *only* on genuine disk saturation, so low free space is the early warning for that single failure mode. This never blocks the pipeline; it surfaces the one condition under which raw capture can legitimately shed.
*   **Trading-calendar guard (optional):** when `recorder.skip_non_trading_days: true`, on startup the daemon compares today's IST date against `recorder.trading_holidays[]` (and weekends); on a non-trading day it logs one INFO line and idles until the next day rather than idle-connecting to a closed feed. Default `false` preserves the always-run behavior.

---

### 3.2 Instrument & Expiry Manager (`instrument_manager.py`)
This module handles weekly options identification and strike grid mappings on startup, querying the OpenAlgo REST API to establish a static, optimized lookup cache.

#### 3.2.1 REST API Querying & Raw Filtering Pipeline
On initialization during the startup phase (at 09:00 AM), the `InstrumentManager` queries the OpenAlgo instrument master endpoint.
*   **REST Endpoint:** Executes a `GET` request to `http://127.0.0.1:5000/api/v1/instruments/` (verified in `restx_api/instruments.py`) with a connection timeout of 10 seconds and up to 3 automatic retries. **Auth is required:** the `apikey` is passed as a query parameter, and the query is narrowed per underlying with the `exchange` filter (e.g. `?apikey=…&exchange=NFO`, and `&exchange=BFO` for SENSEX) rather than downloading the entire universe. `format=json` is the default.
*   **Expiry via dedicated endpoint (preferred):** Rather than re-deriving expiries from the raw master, the manager can call `POST /api/v1/expiry` (`restx_api/expiry.py`) with `{apikey, symbol, exchange, instrumenttype}` to obtain the authoritative F&O expiry list for an underlying. The instrument master is then used only for the strike grid. Symbol/token resolution can additionally use `POST /api/v1/symbol` and `/api/v1/search`.
*   **Response Parsing:** The response contains a JSON list of instrument specifications. The manager iterates through the list, filtering for active option contracts using three conditions:
    1.  *Exchange Filter:* The instrument `exchange` must equal the configured option exchange for the underlying — **`"NFO"`** for NIFTY option contracts and **`"BFO"`** (BSE F&O — *not* `"BSE"`) for SENSEX option contracts. Exchanges come from config (§7), not hardcoded.
    2.  *Instrument Type:* `instrumenttype` must be an option type (`CE` or `PE`), i.e. the contract carries a non-null `strike` and an option-type suffix.
    3.  *Symbol Base Name:* The base asset symbol must match one of the configured underlyings (e.g. `"NIFTY"` or `"SENSEX"`). Use longest-prefix matching so `NIFTYNXT50`/`SENSEX50` are not shadowed by `NIFTY`/`SENSEX` (cf. `database/qty_freeze_db.py:211-215`).

---

#### 3.2.2 Weekly Expiry Resolution Algorithm
Weekly options expire on specific days (NIFTY typically on Thursday, SENSEX on Friday). The manager extracts the correct active weekly contract using the following logic:
*   **Date Normalization:** Parses instrument expiry strings (e.g., `YYYY-MM-DD` or broker-specific formats like `09JUL26`) into standard Python `datetime.date` objects.
*   **Expiration Selection:** Filters out past expiries and selects the nearest active date:
    $$E_{\text{weekly}} = \min \{ D_{\text{expiry}} \mid D_{\text{expiry}} \ge D_{\text{today}} \}$$
*   **Expiry Rollover Gate:** On the day of expiry itself ($D_{\text{expiry}} == D_{\text{today}}$), the manager continues to record the expiring weekly contract because trading continues until 03:30 PM. The rollover to the next week's contract occurs only on the subsequent morning's startup.

---

#### 3.2.3 Auto-Detection & Validation of Strike Steps
Standard option chains utilize fixed strike intervals (e.g., 50 points for NIFTY, 100 points for SENSEX). To detect these steps automatically and safely:
*   **Sorting & Differencing:** The manager extracts all unique strike prices for the resolved weekly expiry $E_{\text{weekly}}$, sorts them in ascending order:
    $$K = [K_1, K_2, \dots, K_M]$$
    And calculates the adjacent differences:
    $$\Delta_i = K_{i+1} - K_i \quad \text{for } i \in [1, M-1]$$
*   **Mode-Based Strike Detection:** Because far out-of-the-money (OTM) leaps may have wider strike steps, using a simple minimum difference can be unstable. The manager calculates the strike step step $\Delta_{\text{strike}}$ using the statistical mode:
    $$\Delta_{\text{strike}} = \text{mode}(\Delta)$$
*   **Validation Rules (config-driven, not hardcoded per index):** For each underlying, the detected step is validated against that underlying's configured `expected_strike_step` set. If $\Delta_{\text{strike}}$ is not in the accepted set, the manager logs a critical warning and uses the underlying's configured `strike_step_fallback`:
    *   e.g. `NIFTY` accepts `{50, 100}`, fallback `50`; `SENSEX` accepts `{100, 200}`, fallback `100` — but these values come from `underlyings[]` in `config.yaml` (§7), so adding an underlying needs no code change.

---

#### 3.2.4 O(1) Cache Mapping Structures
To prevent CPU bottlenecking from string operations during high-frequency WebSocket resampler loops, the `InstrumentManager` compiles and exposes static lookup dictionaries in memory:
*   `strike_to_symbol_map`: A nested dictionary structure of format:
    ```python
    {
        "NIFTY": {
            23400: {"CE": "NIFTY16JUN2623400CE", "PE": "NIFTY16JUN2623400PE"},
            23450: {"CE": "NIFTY16JUN2623450CE", "PE": "NIFTY16JUN2623450PE"},
            ...
        },
        "SENSEX": { ... }
    }
    ```
*   `symbol_to_strike_map`: A flat dictionary for reverse translations:
    ```python
    {
        "NIFTY16JUN2623400CE": {"underlying": "NIFTY", "strike": 23400, "option_type": "CE"},
        "NIFTY16JUN2623400PE": {"underlying": "NIFTY", "strike": 23400, "option_type": "PE"},
        ...
    }
    ```
*   `active_strikes_list`: A sorted list of unique numerical strikes for each index, facilitating binary searches when resolving the closest ATM strike from live spot index ticks.

These maps allow $O(1)$ lookup complexity, shielding the metrics processor from string parsing overhead.

#### 3.2.5 Depth-Capability Preflight
Because true depth is broker- and exchange-dependent (§1), the manager runs a one-time **preflight** at startup so that silent 5-level degradation is *visible and recorded* rather than surprising downstream models:
*   For each configured underlying, issue a single `:50` depth subscription on a representative near-ATM strike and inspect the first depth packet's reported `depth_levels` / `is_50_depth` fields (`fyers_mapping.py:322-323`). **These fields are present only on the raw transport** (§3.3.1 finding — the SDK callback drops them); over the SDK path the preflight can only infer the level count from `len(depth["buy"])`. Since raw is the default transport, the preflight reads the reported fields directly.
*   Log, at WARNING level, the **actual** depth level that will be recorded per (underlying, exchange) — e.g. `NIFTY/NFO → 50`, `SENSEX/BFO → 5 (TBT unsupported)`.
*   Persist the resolved level per symbol so every stored row is self-describing (see the `depth_levels` column added in §4). Metrics that are meaningless at 5 levels (e.g. the 50-level cumulative-depth vector) are emitted as `NULL` for 5-level symbols instead of being silently truncated.

### 3.3 Dynamic WebSocket Manager (`websocket_client.py`)
This module manages the full lifecycle of the market-data feed to the OpenAlgo proxy server and drives the real-time **Dynamic Strike Manager (DSM)** to update option subscriptions based on underlying spot movements. It supports two interchangeable transports selected by config (`websocket.transport`): a hand-rolled **raw-WebSocket client** (§3.3.1a, the **default/primary** path) and the **OpenAlgo Python SDK feed client** (§3.3.1, the alternate). Raw is the default because the SDK's depth callback strips the audit-critical fields the recorder needs — see the verified-finding note below.

#### 3.3.1 Feed Transport — OpenAlgo SDK Client (alternate)

> **Verified finding (2026-07, `openalgo==2.0.2`).** The SDK's depth callback (`feed.py:456-467`) rebuilds the payload and delivers only `{ltp, timestamp, depth:{buy,sell}}` — it **drops `feed_time`, `depth_levels`, `is_50_depth`, and `total_buy/sell_qty`**. The proxy *does* send these over the wire (`websocket_proxy/server.py:1821-1827`); only the SDK convenience layer discards them. Because the recorder's audit (M23 latency via `feed_time`, the §3.2.5 depth preflight, and the self-describing `depth_levels`/`is_50_depth` columns) depends on those fields, the **raw transport (§3.3.1a) is the default**; the SDK path is retained for LTP/spot or degraded deployments. The SDK also defaults `auto_reconnect=True` (see the construction note below).

Rather than re-implement the proxy's wire protocol, the manager wraps the SDK's feed client — the same client the platform's own strategies use (`openalgo.api(...)`, verified in `strategies/examples/` and the trading engine's `market_data/feed_manager.py`). The SDK owns the socket, the `{"action":"authenticate", ...}` handshake, ping/pong, and JSON framing; the recorder keeps ownership of **subscription state and resubscribe-on-reconnect** (the FeedManager pattern), so no protocol details leak into the recorder.
*   **Client construction:** `client = api(api_key=<cfg>, host=<cfg.host_server>, ws_url=<cfg.websocket_url>, auto_reconnect=False)` — the first three come from the `openalgo:` config block (§7), no hardcoding. `auto_reconnect=False` is deliberate: the SDK's built-in reconnect loop (`feed.py:229-272`) would otherwise fight the recorder-owned reconnect/resubscribe state machine below (double replay). The recorder solely owns reconnect.
*   **Connect / disconnect:** the FEED thread calls `client.connect()` (returns bool / may raise) and `client.disconnect()` on teardown. `connect()` is a **single attempt**; the recorder owns the retry loop around it (below), exactly as `feed_manager.py` does.
*   **Callback-based delivery:** subscriptions register a callback instead of a receive loop:
    ```python
    client.subscribe_depth(
        instruments=[{"exchange": "NFO", "symbol": "NIFTY16JUN2623400CE:50"}],
        on_data_received=self._on_raw_tick,      # fans out to raw_file_queue + proc_queue (§2.2 Phase D)
    )
    client.subscribe_ltp(                          # index spot trackers (§3.3.2)
        instruments=[{"exchange": "NSE_INDEX", "symbol": "NIFTY"}],
        on_data_received=self._on_spot_tick,
    )
    ```
    The SDK invokes `on_data_received` on its own delivery thread; the recorder's callback does only the cheap tee (two `put`s) and returns immediately, so the SDK thread is never blocked (§5.1).
*   **Reconnection State Machine (recorder-owned):** the FEED thread runs a supervised loop: on a failed/`False` `connect()` or a mid-session drop it retries with the same exponential backoff, then **resubscribes every symbol in the `_wanted`/`active_subscriptions` set** (§3.3.4 never-shrink) before resuming:
    $$T_{\text{backoff}} = \min(60, 1.5^{\text{attempts}} \cdot 2.0)\text{ seconds}$$
    During outages the local resampler thread keeps running, emitting forward-filled/`NULL` frames so the 1-second grid stays contiguous (§6.2). A `subscribe_*` issued while disconnected is recorded in `active_subscriptions` only and flushed by the next reconnect's resubscribe — never silently lost.
*   **Concurrency:** calls **into** the SDK client (`subscribe_*`/`unsubscribe_*`) are serialized by a `client_lock` so the FEED thread's resubscribe and a DSM caller's subscribe never interleave on the client; `connect()`/`disconnect()` are owned solely by the FEED thread and deliberately **not** taken under that lock (a blocking connect must not stall subscribes). This mirrors the two-lock split in `feed_manager.py` (state lock vs. client lock).

#### 3.3.1a Feed Transport — Raw WebSocket (primary/default)
Because the SDK strips the audit-critical depth fields (§3.3.1 verified finding), the **default** transport is a hand-rolled `websocket-client` daemon thread that speaks the proxy protocol directly and preserves the full packet (`feed_time`, `depth_levels`, `is_50_depth`, `total_*_qty`). This path is selected by `websocket.transport: raw` (§7, the default) and is behaviorally equivalent from the pipeline's perspective (same tee into `raw_file_queue`/`proc_queue`, same DSM, same never-shrink). It implements directly:
*   **Handshake:** `{"action": "authenticate", "api_key": "<cfg>"}` on connect.
*   **Heartbeat:** a monitor sends a ping every `heartbeat_interval_sec`; no pong/message within `heartbeat_timeout_sec` forces a close and triggers the same backoff state machine above.
*   **Subscribe frame:** the raw depth/LTP JSON frames shown in §3.3.2–§3.3.3.

The two transports are interchangeable and the choice is config only; raw is the default so the audit log is complete and self-describing, and the SDK path remains available for LTP-only or convenience use.

---

#### 3.3.2 Dynamic Strike Manager (DSM) & Boundary Checking Math
The DSM acts as a controller that processes index spot price ticks ($S_t$) and dynamically adjusts options subscriptions.
*   **Spot Ticker Subscription:** On connection, the manager automatically subscribes to index spot prices via the SDK `client.subscribe_ltp(instruments=[{"exchange": spot_exchange, "symbol": spot_symbol}], on_data_received=…)` (raw-transport equivalent: an LTP `mode=1` frame). Underlyings and their `spot_symbol`/`spot_exchange` are supplied by config (§7) — e.g. `NIFTY`/`NSE_INDEX`, `SENSEX`/`BSE_INDEX` — so this is not limited to any specific index. Indices expose only synthetic depth, so spot always stays in LTP mode.
*   **Validation of Spot Ticks:** To prevent false boundary triggers from anomalous data spikes:
    *   Ticks where $S_t \le 0$ are discarded.
    *   Ticks representing a single-tick change of $>2\%$ from the 10-tick rolling median are flagged and ignored.
*   **Boundary Update Equations:**
    Let $S_0$ be the initial spot price. On startup, boundaries are set based on the configuration window ($W$):
    $$B_{\text{lower}} = S_0 - W \quad \text{and} \quad B_{\text{upper}} = S_0 + W$$
    The manager calls the auto-detected strike list from the `InstrumentManager` and selects all option strike prices $K$ within:
    $$K_{\text{initial}} = \{ K \mid B_{\text{lower}} \le K \le B_{\text{upper}} \}$$
    On every valid spot tick $S_t$, boundary thresholds are evaluated:
    *   *Lower Boundary Breach Check:*
        $$\text{If } S_t \le B_{\text{lower}} + T \quad (\text{where } T \text{ is the expansion threshold})$$
        Calculate the expanded boundary using the expansion step ($E$):
        $$B_{\text{lower, new}} = B_{\text{lower}} - E$$
        Identify new strikes to subscribe:
        $$K_{\text{new}} = \{ K \mid B_{\text{lower, new}} \le K < B_{\text{lower}} \}$$
        Update state:
        $$B_{\text{lower}} = B_{\text{lower, new}}$$
    *   *Upper Boundary Breach Check:*
        $$\text{If } S_t \ge B_{\text{upper}} - T \quad (\text{where } T \text{ is the expansion threshold})$$
        Calculate the expanded boundary using the expansion step ($E$):
        $$B_{\text{upper, new}} = B_{\text{upper}} + E$$
        Identify new strikes to subscribe:
        $$K_{\text{new}} = \{ K \mid B_{\text{upper}} < K \le B_{\text{upper, new}} \}$$
        Update state:
        $$B_{\text{upper}} = B_{\text{upper, new}}$$

---

#### 3.3.3 Thread-Safe DSM Subscription Flow
Option subscriptions are tracked inside a thread-safe set `self.active_subscriptions`. To prevent concurrent write corruption, access is guarded by a reentrant lock (`self.lock = threading.RLock()`).

```
                    ┌────────────────────────────┐
                    │     Spot LTP Tick (St)     │
                    └──────────────┬─────────────┘
                                   │
                                   ▼
                    ┌────────────────────────────┐
                    │      Validate Tick         │ ── (Ignore if Spike or <= 0)
                    └──────────────┬─────────────┘
                                   │
                                   ▼
                    ┌────────────────────────────┐
                    │   Check Boundary Breaches  │ ── (St <= B_lower+T or St >= B_upper-T)
                    └──────────────┬─────────────┘
                                   │
                                   ▼
                    ┌────────────────────────────┐
                    │    Acquire RLock Lock      │
                    └──────────────┬─────────────┘
                                   │
                                   ▼
                    ┌────────────────────────────┐
                    │ Compute New Option Symbols │ ── (Using strike_to_symbol_map)
                    └──────────────┬─────────────┘
                                   │
                                   ▼
                    ┌────────────────────────────┐
                    │    Filter Unsubscribed     │ ── (New Symbols - active_subscriptions)
                    └──────────────┬─────────────┘
                                   │
                                   ▼
                    ┌────────────────────────────┐
                    │   Add to Set & Subscribe   │ ── (client.subscribe_depth / raw frame, symbol + ":50" suffix)
                    └────────────────────────────┘
```

##### Depth Subscription Mechanism (the `:50` suffix)
Requesting depth mode alone yields only the broker default (**5 levels**). In OpenAlgo, the **50-level TBT feed is triggered by appending a `":50"` suffix to the option symbol** — the FYERS adapter keys off `symbol.endswith(":50")` and routes those subscriptions to the TBT WebSocket (`broker/fyers/streaming/fyers_websocket_adapter.py:349`); the proxy re-publishes ticks under the *same* suffixed topic, so the recorder must subscribe, match delivered topics, and store using the suffixed symbol string.

*   **Primary (SDK):** the suffix rides inside the SDK instrument dict —
    ```python
    client.subscribe_depth(
        instruments=[{"exchange": "NFO", "symbol": "NIFTY16JUN2623400CE:50"}],
        on_data_received=self._on_raw_tick,
    )
    ```
*   **Fallback (raw):** the equivalent proxy frame, used only on the raw transport (§3.3.1a) —
    ```json
    {"action": "subscribe", "symbol": "NIFTY16JUN2623400CE:50", "exchange": "NFO", "mode": 3, "depth": 50}
    ```
*   ✅ **Verified (2026-07):** the SDK's `subscribe_depth` passes a `:50`-suffixed symbol through **unaltered** (`feed.py:733-754`, `_send_subscribe_msg`), and the FYERS adapter routes it to the TBT path via `symbol.endswith(":50")` + `TBT_SUPPORTED_EXCHANGES={"NSE","NFO"}` (`fyers_websocket_adapter.py:45,349,358`). The residual reason to prefer **raw** is not the suffix but that the SDK *depth callback* strips `feed_time`/`depth_levels`/`is_50_depth` (§3.3.1 finding) — so `websocket.transport: raw` is the default. The §3.2.5 preflight still confirms the actual delivered depth per (underlying, exchange) at startup.
*   For exchanges where TBT is unsupported (e.g. **BFO**/SENSEX), OpenAlgo automatically **falls back to 5-level** depth on either transport. The recorder does not fail — it records whatever `depth_levels` the feed reports (see §3.2.5 preflight and §3.4.2 handling of variable level counts).
*   The strike-level DB `symbol` is stored **without** the `:50` suffix (the suffix is a transport detail); the raw `.jsonl.gz` log preserves the packet exactly as received.

#### 3.3.4 "Never Shrink" Rule Implementation
*   When new symbols are resolved during boundary shifts, the manager takes the difference of the target symbols against `self.active_subscriptions` to ensure it only issues subscriptions for new contracts.
*   Once a symbol is added to `self.active_subscriptions`, it is **never** removed, and no `"unsubscribe"` commands are sent to the WebSocket proxy.
*   This ensures the historical depth timeline remains contiguous for all active strikes, even if the spot price pulls back from a previous day's extreme boundary. All active options subscriptions are reset only upon graceful daily shutdown at 03:35 PM.

### 3.4 Metric Processor (`processor.py`)
Consolidates raw WebSocket packets, standardizes the tick timeline, performs high-performance mathematical computations using **NumPy**, and aggregates option chain matrices.

#### 3.4.0 Metric Registry (declarative extension point)
Every metric (M1–M29, the rolling-window outputs of §3.4.3, and the multi-strike aggregates of §3.4.4) is organized as an entry in a **declarative metric registry** (`metrics/registry.py`) rather than an inline hardcoded list. Each entry declares:
*   its **id/name** (the token used in `recorder.live_metrics`),
*   the **inputs** it consumes (touch, full book, rolling deque, spot, tick_size, `feed_time`, …),
*   its **minimum depth** requirement (so deep-book-only metrics auto-`NULL` when the populated level count $L$ is shallower — §3.4.2),
*   the **output column(s)** it writes, and its **thin/fat eligibility**.

This makes three things config-only rather than code changes: (1) `recorder.live_metrics` is **validated against the registry** at startup (an unknown name fast-fails, §7.3); (2) the **thin (live) vs fat (offline)** split is simply *which registry entries fire* — the same `TickProcessor` runs both; and (3) **adding a future metric (M30+)** is a pure additive registration, with no edits to the resampler, the writers, or the validation. The per-metric formulas below (§3.4.2–§3.4.4) are the registered function bodies; the registry is the wiring around them.

---

#### 3.4.1 Resampling & Queue Routing Pipeline
The processor operates a dual-stage pipeline to handle incoming tick bursts:
1.  **Cache Ingest:** The processor drains its own `proc_queue` (fed by the WS receiver's fan-out in §2.2 Phase D — the processor does **not** copy packets to the file writer; the receiver already teed a copy to `raw_file_queue`). For each packet it updates the in-memory symbol cache (`self.latest_ticks[symbol]`) with the packet's content. Draining is decoupled from computation so a burst fills the cache without blocking.
2.  **1-Second Resampling Loop:** A background thread runs a high-resolution 1-second execution loop. At each interval, it copies the state of `self.latest_ticks` and applies:
    *   *Forward-Fill:* If a symbol did not receive a new tick in the last second, it reuse the previous computed snapshot.
    *   *Staleness Guard:* If the gap since the last received tick exceeds 5 seconds, all calculations are bypassed, and metrics are written as `None`/`NaN` to signify data offline status.

**Thin (live) vs fat (offline) computation modes.** The same `TickProcessor` runs in two modes against the *same* four-table schema (§4):
*   **Live mode (thin):** during market hours the processor computes only the columns named in `recorder.live_metrics` — a cheap, latency-critical subset (e.g. spread, weighted OBI, book pressure, best bid/ask qty, the ATM aggregates, and regime). The remaining catalog columns are left `NULL` and the rows land in the **thin live store** (`market_depth_live_YYYYMMDD.db`, Tier 1). This keeps the per-second cycle well inside the `< 15 ms` budget (§1.4) so live capture is never starved.
*   **Offline mode (fat):** the end-of-session replay (§8, §8.6) re-runs this same loop with the **full** metric set enabled, populating every §4 column into the **fat DuckDB analytical store** (`market_depth_analytics_YYYYMMDD.duckdb`, Tier 2). Because it runs after close on an idle machine, the exhaustive §3.4.2–§3.4.3 computation has no real-time deadline.

The subset is config-driven (no hard-coded metric list), so an operator can widen or narrow the live path — or, in the limit, set `live_metrics: all` to compute everything live at the cost of headroom. The per-metric definitions below (M1–M24) are mode-agnostic: which of them fire is decided purely by the active metric set.

---

#### 3.4.2 Exhaustive Per-Strike Metric Computation
For every active strike, the processor runs vectorized NumPy operations on the available bid/ask levels. **The level count $L$ is per-symbol, not a fixed 50** — it is `50` for TBT-capable symbols (NIFTY/NFO) and `5` where the broker falls back (SENSEX/BFO). All summations written below as $\sum_{i=1}^{50}$ are computed over $\sum_{i=1}^{L}$ where $L$ is the actual number of populated levels; requests for a fixed band (e.g. Top-10) that exceed $L$ clamp to $L$. Metrics whose meaning requires deep book (e.g. the 20/50-level cumulative-depth entries in M19) are emitted as `NULL` when $L < $ the required depth. Below are the mathematical definitions and operational details for all 24 per-strike metrics:

##### A. Spread Dynamics
*   **M1: Bid-Ask Spread:** Measures absolute transactional friction.
    $$\text{Spread} = P_{\text{ask}, 1} - P_{\text{bid}, 1}$$
    *Note: If $\text{Spread} \le 0$, a critical warning is logged, indicating crossed markets or API data anomalies.*
*   **M2: Relative Spread:** Normalizes friction against price scale to compare strikes of different values.
    $$\text{Relative Spread} = \frac{\text{Spread}}{P_{\text{mid}} + \epsilon} \quad (\text{where } \epsilon = 10^{-8})$$
*   **M3: Mid Price:** Baseline valuation.
    $$P_{\text{mid}} = \frac{P_{\text{bid}, 1} + P_{\text{ask}, 1}}{2}$$
*   **M4: Micro Price:** Volume-weighted mid price, reflecting short-term execution imbalances.
    $$P_{\text{micro}} = \frac{P_{\text{bid}, 1} \cdot q_{\text{ask}, 1} + P_{\text{ask}, 1} \cdot q_{\text{bid}, 1}}{q_{\text{bid}, 1} + q_{\text{ask}, 1} + \epsilon}$$
    *Mathematical Rationale:* Incorporates touch-level order quantities ($q_{\text{bid}, 1}, q_{\text{ask}, 1}$), making it sensitive to immediate liquidity pressure.

---

##### B. Order Book Imbalances (OBI)
*   **M5: Raw OBI:** Measures total volume disparity across all 50 levels.
    $$\text{Raw OBI} = \frac{\sum_{i=1}^{50} q_{\text{bid}, i} - \sum_{i=1}^{50} q_{\text{ask}, i}}{\sum_{i=1}^{50} q_{\text{bid}, i} + \sum_{i=1}^{50} q_{\text{ask}, i} + \epsilon}$$
*   **M6: Top-5 OBI & M7: Top-10 OBI:** Captures localized volume pressure close to execution prices.
    $$\text{Top-N OBI} = \frac{\sum_{i=1}^{N} q_{\text{bid}, i} - \sum_{i=1}^{N} q_{\text{ask}, i}}{\sum_{i=1}^{N} q_{\text{bid}, i} + \sum_{i=1}^{N} q_{\text{ask}, i} + \epsilon} \quad (\text{for } N \in \{5, 10\})$$
*   **M8: Weighted OBI:** The core indicator for order book pressure. It applies an exponential decay weight $w_i$ to prioritize levels closer to the touch price.
    $$\text{Weighted OBI} = \frac{\sum_{i=1}^{50} (q_{\text{bid}, i} \cdot w_i) - \sum_{i=1}^{50} (q_{\text{ask}, i} \cdot w_i)}{\sum_{i=1}^{50} (q_{\text{bid}, i} \cdot w_i) + \sum_{i=1}^{50} (q_{\text{ask}, i} \cdot w_i) + \epsilon}$$
    $$\text{where Weight Array: } w_i = e^{-0.2 \cdot (i-1)} \quad \text{for } i \in [1, 50]$$
    *Mathematical Rationale:* Generates decay weights ($w_1 = 1.0$, $w_5 \approx 0.45$, $w_{10} \approx 0.16$, $w_{20} \approx 0.02$). This limits the influence of far-out-of-the-money spoofing walls while preserving high sensitivity to near-the-money changes.

---

##### C. Volumetric & Pressure Ratios
*   **M9: Bid Stack Ratio & M10: Ask Stack Ratio:**
    $$\text{Bid Stack Ratio} = \frac{\sum_{i=1}^{50} q_{\text{bid}, i}}{\sum_{i=1}^{50} (q_{\text{bid}, i} + q_{\text{ask}, i}) + \epsilon} \quad \text{and} \quad \text{Ask Stack Ratio} = 1 - \text{Bid Stack Ratio}$$
*   **M11: Book Pressure:** Computes the **mid-centered** monetary-depth imbalance across the top 10 levels. Each level's size is weighted by its **distance from the mid price**, so a perfectly symmetric book returns 0 and the sign reflects true directional pressure (positive = bid-heavy / buy pressure). With $d_{\text{bid},i} = P_{\text{mid}} - P_{\text{bid},i} \ge 0$ and $d_{\text{ask},i} = P_{\text{ask},i} - P_{\text{mid}} \ge 0$:
    $$\text{Book Pressure} = \sum_{i=1}^{10} d_{\text{bid}, i} \cdot q_{\text{bid}, i} - \sum_{i=1}^{10} d_{\text{ask}, i} \cdot q_{\text{ask}, i}$$
    *Mid-centering (correction):* the previous form $\sum P_{\text{bid},i} q_{\text{bid},i} - \sum P_{\text{ask},i} q_{\text{ask},i}$ carried a **structural negative bias** — because every bid price sits below every ask price, a symmetric book (equal size per side) returns $\sum q_i (P_{\text{bid},i} - P_{\text{ask},i}) \approx -\sum q_i \cdot \text{spread}_i < 0$, so its sign and zero-crossing were not interpretable. Measuring each level's price **as a distance from the mid** removes the spread offset while preserving the bid-heavy = positive convention. *Scale note:* this rescales M11 from notional (₹×qty) to distance-weighted qty (much smaller magnitude); the dependent metrics — NOP (§3.4.4B), pressure velocity/acceleration and pressure trend (§3.4.3A/C), and the regime threshold $\theta_{\text{pressure}}$ (§3.4.4C) — all inherit the new scale consistently, and $\theta_{\text{pressure}}$ must be re-tuned to it.
*   **M12: Best Bid/Ask Quantity:** Raw quantities resting at touch ($q_{\text{bid}, 1}$ and $q_{\text{ask}, 1}$).
*   **M13: Average Order Size:** Establishes the institutional vs. retail profile of the order book.
    $$\text{Avg Size}_{\text{bid}} = \frac{\sum_{i=1}^{10} q_{\text{bid}, i}}{\sum_{i=1}^{10} n_{\text{bid}, i} + \epsilon} \quad \text{and} \quad \text{Avg Size}_{\text{ask}} = \frac{\sum_{i=1}^{10} q_{\text{ask}, i}}{\sum_{i=1}^{10} n_{\text{ask}, i} + \epsilon}$$
    *Where $n_i$ represents the number of orders resting at level $i$.* **Verified data caveat (`fyers_tbt_websocket.py:476-490`):** the per-level `orders` (`nord`) count **is** populated on the TBT feed, so M13/M14 are computable — but it is cumulative state, only refreshed when `nord > 0`, and can be carried forward on diff updates. Treat `orders == 0` at a populated price level as **NULL/undefined** (and guard M13 against divide-by-zero) rather than a real zero.
*   **M14: Order Count Imbalance (OCI):** Compares execution interest based on order counts rather than quantity.
    $$\text{OCI} = \frac{\sum_{i=1}^{10} n_{\text{bid}, i} - \sum_{i=1}^{10} n_{\text{ask}, i}}{\sum_{i=1}^{10} n_{\text{bid}, i} + \sum_{i=1}^{10} n_{\text{ask}, i} + \epsilon}$$

---

##### D. Liquidity Concentration & Structure
*   **M15: Effective Depth:** Sums resting volume within a $\pm 0.5\%$ range of the Mid Price to measure market depth resilient to price slippage.
    $$\text{Effective Depth} = \sum_{i} q_{\text{bid}, i} \cdot \mathbb{I}(P_{\text{bid}, i} \ge 0.995 \cdot P_{\text{mid}}) + \sum_{i} q_{\text{ask}, i} \cdot \mathbb{I}(P_{\text{ask}, i} \le 1.005 \cdot P_{\text{mid}})$$
    *Where $\mathbb{I}()$ is the indicator function.*
*   **M16: Liquidity Concentration Index (LCI):** Measures the percentage of volume concentrated at the inside market.
    $$\text{LCI}_{\text{bid}} = \frac{\sum_{i=1}^{5} q_{\text{bid}, i}}{\sum_{j=1}^{50} q_{\text{bid}, j} + \epsilon} \quad \text{and} \quad \text{LCI}_{\text{ask}} = \frac{\sum_{i=1}^{5} q_{\text{ask}, i}}{\sum_{j=1}^{50} q_{\text{ask}, j} + \epsilon}$$
*   **M17: Touch Dominance:** Identifies if book liquidity is concentrated at the spread boundary.
    $$\text{Touch Dom}_{\text{bid}} = \frac{q_{\text{bid}, 1}}{\sum_{i=1}^{5} q_{\text{bid}, i} + \epsilon} \quad \text{and} \quad \text{Touch Dom}_{\text{ask}} = \frac{q_{\text{ask}, 1}}{\sum_{i=1}^{5} q_{\text{ask}, i} + \epsilon}$$
*   **M18: Round-Number Depth:** Measures institutional clustering by summing volume at round prices (prices where $\text{Price} \pmod{X} == 0$, e.g., $X=5$ or $X=10$), computed per side ($Q_{\text{round,bid}}$, $Q_{\text{round,ask}}$). *Applicability note:* round-number clustering is primarily an **underlying/spot** phenomenon; on option **premiums** (0.05 tick, frequently single-digit values) the effect is weak, so M18 is retained as a **low-priority** feature rather than a primary signal.
*   **M19: Cumulative Depth Vector:** A four-dimensional vector tracking volume aggregates, **computed separately for each side** (a bid vector and an ask vector — $q_i \equiv q_{\text{bid},i}$ or $q_{\text{ask},i}$ respectively):
    $$\vec{Q}_{\text{cum}} = \left[ \sum_{i=1}^{5} q_i, \sum_{i=1}^{10} q_i, \sum_{i=1}^{20} q_i, \sum_{i=1}^{50} q_i \right]$$
    *Depth guard:* per §3.4.2, the 20- and 50-level entries are emitted as `NULL` when the populated level count $L$ is below that depth (e.g. the 5-level SENSEX/BFO fallback).

---

##### E. Wall Analytics & Book Stability
*   **M20: Largest Bid/Ask Wall Price & Size:**
    $$\text{Wall Size}_{\text{bid}} = \max(q_{\text{bid}}) \quad \text{and} \quad P_{\text{wall, bid}} = P_{\text{bid}, j} \quad \text{where } q_{\text{bid}, j} == \text{Wall Size}_{\text{bid}}$$
*   **M21: Wall Score:** Compares the largest wall to the rest of the book levels.
    $$\text{Wall Score}_{\text{bid}} = \frac{\text{Wall Size}_{\text{bid}}}{\text{median}\left(\{ q_{\text{bid}, i} : q_{\text{bid}, i} > 0,\ i \ne j \}\right) + \epsilon}$$
    *Zero-median guard (correction):* in sparse OTM option books most of the deep levels are empty (`0`), so a plain `median(q_i)` over all levels is frequently `0` — dividing by `≈ε` then yields a meaningless multi-billion Wall Score. The median is therefore taken over **non-zero** levels only (excluding the wall level $j$); if fewer than 2 non-zero non-wall levels exist, M21 is emitted as `NULL`.
*   **M22: Quote Stability:** Percentage of seconds over the rolling window where the best prices remain unchanged, indicating market stability.
    $$\text{Stability} = \frac{1}{T} \sum_{t=1}^{T} \mathbb{I}(P_{\text{touch}, t} == P_{\text{touch}, t-1})$$
*   **M23: Anomaly & Freshness Validation:** Calculates network latency to detect stale packets.
    $$\text{Latency} = T_{\text{local}} - T_{\text{broker}}$$
    *If $\text{Latency} > 2.0\text{ seconds}$, the packet is marked as stale.*
    *Data-source note (verified in `broker/fyers/streaming/fyers_mapping.py:319-321`):* $T_{\text{broker}}$ must be read from the payload's **`feed_time`** field (the broker exchange clock). The top-level **`timestamp`** field is **not** broker-stamped — OpenAlgo sets it locally at the proxy via `int(time.time())`, so using it for latency would always yield ≈0 and defeat staleness detection. If `feed_time` is absent or `0` (some feeds/synthetic index depth), M23 is emitted as `NULL` rather than a spurious value.
*   **M24: Confidence Score:** Normalized rating in **[0, 1]** combining spread tightness, OBI stability, and freshness. This is the single authoritative definition (the differing form in the older master spec is superseded).
    $$\text{Confidence} = 0.5 \cdot e^{-5.0 \cdot \text{Relative Spread}} + 0.3 \cdot \big(1.0 - \min(1,\ \text{std}(\text{Top5 OBI}))\big) + 0.2 \cdot \mathbb{I}(\text{Latency} \le 1.0)$$
    *Clamp (correction):* the OBI-stability term is `1 − min(1, std(Top5 OBI))`, not `1 − std(...)`, because a rolling std can exceed 1 and would otherwise make the term (and the score) go **negative**. The final value is additionally clamped to `[0, 1]`. During staleness/outage seconds (M23 NULL), Confidence is written as `0.0`.

---

##### F. Extended Execution & Fair-Value Metrics
These single-snapshot metrics extend the catalog toward **execution cost** and **fair-value** signals that the M1–M24 set does not capture. They are computed from the same per-second book snapshot and stored in `option_strike_metrics`.

*   **M25: Cost-to-Fill & Book Slope:** Uses the *full* depth to answer "how far does price move to fill a target order," the most execution-relevant depth signal. Let $Q$ be the configured probe size (`fill_probe_qty`, e.g. `N` lots × lotsize — config, not hard-coded). Walking the ask book to **buy** $Q$, with $Q^{\text{cum}}_{\text{ask},k} = \sum_{i=1}^{k} q_{\text{ask},i}$ and $k^\* = \min\{k : Q^{\text{cum}}_{\text{ask},k} \ge Q\}$:
    $$\bar{P}_{\text{buy}} = \frac{1}{Q}\left[ \sum_{i=1}^{k^\*-1} P_{\text{ask},i}\,q_{\text{ask},i} + P_{\text{ask},k^\*}\bigl(Q - Q^{\text{cum}}_{\text{ask},k^\*-1}\bigr) \right]$$
    *   **Fill slippage (buy/sell):** relative cost vs mid — $\text{slip}_{\text{buy}} = (\bar{P}_{\text{buy}} - P_{\text{mid}})/P_{\text{mid}}$; symmetrically $\text{slip}_{\text{sell}} = (P_{\text{mid}} - \bar{P}_{\text{sell}})/P_{\text{mid}}$ walking the bid book.
    *   **Book slope (Kyle-$\lambda$ proxy):** price impact **per unit quantity** — $\lambda_{\text{ask}} = (\bar{P}_{\text{buy}} - P_{\text{mid}})/Q$ and $\lambda_{\text{bid}} = (P_{\text{mid}} - \bar{P}_{\text{sell}})/Q$.
    *Depth guard:* if the side cannot absorb $Q$ within its $L$ populated levels ($Q^{\text{cum}}_{\cdot,L} < Q$ — common in the 5-level fallback or thin OTM books), all four values are emitted as `NULL` rather than an optimistic partial-fill price.
*   **M26: Touch Queue Imbalance:** The **L1 (touch) OBI** — the size imbalance at the best bid/ask only. Empirically the strongest 1-tick-ahead predictor in the microstructure literature (Cont–Stoikov queue imbalance) and, unlike the micro price which folds it into a price, it is exposed here as a direct feature. Signed to match the OBI family:
    $$I_{\text{queue}} = \frac{q_{\text{bid},1} - q_{\text{ask},1}}{q_{\text{bid},1} + q_{\text{ask},1} + \epsilon} \quad \in [-1, 1]$$
*   **M27: VAMP (Volume-Adjusted Mid Price):** A multi-level generalization of the micro price (M4), robust when the touch is thin. With the M8 exponential weights $w_i$, form each side's weighted representative price and weighted size, then combine with micro-price (opposite-size) logic:
    $$\tilde{P}_{\text{bid}} = \frac{\sum_{i=1}^{L} w_i q_{\text{bid},i} P_{\text{bid},i}}{\tilde{Q}_{\text{bid}} + \epsilon},\ \ \tilde{Q}_{\text{bid}} = \sum_{i=1}^{L} w_i q_{\text{bid},i} \quad (\text{ask analogous})$$
    $$\text{VAMP} = \frac{\tilde{P}_{\text{bid}}\,\tilde{Q}_{\text{ask}} + \tilde{P}_{\text{ask}}\,\tilde{Q}_{\text{bid}}}{\tilde{Q}_{\text{bid}} + \tilde{Q}_{\text{ask}} + \epsilon}$$
    *Consistency:* at $L=1$ ($w_1=1$) this reduces exactly to the M4 micro price, so VAMP is a strict generalization.
*   **M28: Micro-Price / LTP Divergence (Fair-Value Gap):** The gap between the order-book fair value (micro price) and the last traded price — a lead-lag / mean-reversion signal. Relative, for cross-strike comparability:
    $$\text{FV Gap} = \frac{P_{\text{micro}} - P_{\text{ltp}}}{P_{\text{ltp}} + \epsilon}$$
    Positive ⇒ the book leans above the last print (up-pressure not yet traded through); negative ⇒ the reverse.
*   **M29: Spread in Ticks:** The spread normalized by the instrument's **tick size** (from the master contract / `SymToken.tick_size`, e.g. `0.05` for NFO options) — a cleaner cross-instrument friction measure than the price-relative M2, since one tick is the true minimum increment:
    $$\text{Spread}_{\text{ticks}} = \frac{\text{Spread}}{\text{tick\_size}}$$
    *Guard:* if the tick size is unavailable for the symbol, M29 is emitted as `NULL`.

---

#### 3.4.3 Rolling Time Window Calculations
For each strike, the processor manages thread-safe double-ended queues (`collections.deque`) with fixed capacities matching three time windows: $N \in \{5, 10, 30\}$ seconds. This ensures $O(1)$ insertion and pop complexities, preventing execution latency.

---

##### A. Window Stat Trends
*   **Price Return:** Percentage return of the last traded price over the window.
    $$\text{Return}_N = \frac{P_{\text{ltp}, t} - P_{\text{ltp}, t-N}}{P_{\text{ltp}, t-N} + \epsilon}$$
*   **Spread Statistics:** Calculates the mean ($\mu$), minimum, maximum, and standard deviation ($\sigma$) of the absolute spreads:
    $$\mu_{\text{spread}, N} = \frac{1}{N} \sum_{j=0}^{N-1} \text{Spread}_{t-j} \quad \text{and} \quad \sigma_{\text{spread}, N} = \sqrt{\frac{1}{N} \sum_{j=0}^{N-1} (\text{Spread}_{t-j} - \mu_{\text{spread}, N})^2}$$
*   **Weighted OBI Statistics:** Calculates the rolling mean ($\mu_{\text{wobi}, N}$) and standard deviation ($\sigma_{\text{wobi}, N}$) of the weighted order book imbalance.
*   **Linear Regression Slopes:** Computes the slope of the linear trend line over the window $N$ for Weighted OBI and Book Pressure to measure accumulation intensity:
    $$\text{Slope}_N = \frac{N \sum_{j=1}^{N} (j \cdot y_j) - \sum_{j=1}^{N} j \sum_{j=1}^{N} y_j}{N \sum_{j=1}^{N} j^2 - (\sum_{j=1}^{N} j)^2 + \epsilon}$$
    *Where $y_j$ represents the metric value (Weighted OBI or Book Pressure) at sequence index $j \in [1, N]$.*
*   **Micro-Price Realized Volatility:** The realized volatility of the **micro price** (M4) over the window — a direct price-variance measure that the spread- and OBI-dispersion stats above do not capture, and a cleaner input to the Volatile-regime test (§3.4.4C) than spread width alone. Using 1-second log returns $r_j = \ln\!\big(P_{\text{micro},t-j+1} / P_{\text{micro},t-j}\big)$:
    $$\sigma^{\text{RV}}_N = \sqrt{\sum_{j=1}^{N} r_j^2}$$
    *Guard:* seconds where either micro price is `NULL`/non-positive (staleness/outage, §3.4.1) are skipped from the sum; if fewer than 2 valid returns remain, $\sigma^{\text{RV}}_N$ is `NULL`.

---

##### B. Liquidity Flow Dynamics
Tracks the rate of limit order additions and removals across the top of the book. Because the feed delivers **full 50-level snapshots (not deltas)** and the book is re-indexed on every update, the comparison of consecutive seconds **must align the two snapshots by price, not by level index** (see the correction note below). Let $q_t(p)$ denote the resting quantity at **price $p$** at second $t$ (0 if $p$ is absent from that snapshot), taken per side. Let $\mathcal{P}^{\text{top}}_t$ be the set of prices in the top-10 price levels of a given side at $t$, and define the aligned price set $\mathcal{P} = \mathcal{P}^{\text{top}}_t \cup \mathcal{P}^{\text{top}}_{t-1}$. The bid and ask sides are accumulated independently and then summed:
*   **Liquidity Added (Volume Replenishment):** Sum of size increases at each price, **including prices newly appearing** in the book.
    $$\Delta Q^+_t = \sum_{p \in \mathcal{P}} \max\!\left(0,\ q_t(p) - q_{t-1}(p)\right)$$
*   **Liquidity Removed (Volume Cancellations or Fills):** Sum of size decreases at each price, **including prices that vanished** from the book.
    $$\Delta Q^-_t = \sum_{p \in \mathcal{P}} \max\!\left(0,\ q_{t-1}(p) - q_t(p)\right)$$
    *Price-alignment (correction):* the previous form multiplied a per-index delta by $\mathbb{I}(P_{t,i} == P_{t-1,i})$ — i.e. it compared **level index $i$ across snapshots**. On a full-snapshot feed the level indices shift by one every time the touch moves, so that indicator is `False` for almost every level *precisely during the active seconds this metric is meant to capture*, collapsing $\Delta Q^\pm$ to $\approx 0$ when flow is highest and silently dropping level insertions/deletions. Aligning by **price key** over the union $\mathcal{P}$ (treating an absent price as quantity 0) is snapshot-shift invariant and correctly counts appearances as adds and disappearances as removes.
*   **Book Churn:** The cumulative volume of liquidity added and removed, measuring book activity.
    $$\text{Churn}_N = \sum_{j=0}^{N-1} (\Delta Q^+_{t-j} + \Delta Q^-_{t-j})$$
*   **Flow Intensity:** The frequency of update actions, calculated as the count of seconds in window $N$ where either $\Delta Q^+_t > 0$ or $\Delta Q^-_t > 0$.

---

##### C. Options Book Momentum
*   **Pressure Velocity ($V_{\text{pressure}}$):** The first-order rate of change of the resampled Book Pressure ($BP$):
    $$V_{\text{pressure}, N} = \frac{BP_t - BP_{t-N}}{N}$$
*   **Pressure Acceleration ($A_{\text{pressure}}$):** The second-order rate of change, showing if option pressure is accelerating:
    $$A_{\text{pressure}, N} = \frac{V_{\text{pressure}, t} - V_{\text{pressure}, t-N}}{N}$$

---

##### D. Wall Persistence & Lifetime Analytics
*   **Wall Persistence Price ($P_{\text{wall}}$) & Size ($S_{\text{wall}}$):** Identified when a price level contains a resting quantity greater than the wall threshold (e.g., $S_{\text{wall}} \ge \mu_{\text{size}} + 3\sigma_{\text{size}}$).
*   **Wall Persistence Duration ($T_{\text{persist}}$):** The number of consecutive seconds the wall remains active at the same price:
    $$T_{\text{persist}} = \sum_{j=0}^{k} \mathbb{I}(P_{\text{wall}, t-j} == P_{\text{wall}, t}) \quad \text{for } P_{\text{wall}, t-j} \text{ active}$$
*   **Wall Creation / Destruction Events:** Tracks count events over window $N$:
    *   *Creation:* Count of new walls appearing at prices not previously flagged as walls.
    *   *Destruction:* Count of walls disappearing (either due to cancellation or execution fills).

---

##### E. Order Flow Imbalance (OFI)
The **best-level Order Flow Imbalance** (Cont–Kukanov–Stoikov, *The Price Impact of Order Book Events*, 2014) is the single most documented book-derived short-horizon price predictor, and is the **principled complement** to the price-aligned liquidity flow of §3.4.3-B: where $\Delta Q^\pm$ measures gross depth churn across the top-10, OFI measures the *signed* net pressure at the **touch** only. Comparing the touch of consecutive seconds ($t-1 \to t$), each side contributes one event; with $P^b_t, q^b_t$ the best bid price/size and $P^a_t, q^a_t$ the best ask:
$$
e^b_t = q^b_t \cdot \mathbb{I}(P^b_t \ge P^b_{t-1}) - q^b_{t-1} \cdot \mathbb{I}(P^b_t \le P^b_{t-1})
\qquad
e^a_t = q^a_t \cdot \mathbb{I}(P^a_t \le P^a_{t-1}) - q^a_{t-1} \cdot \mathbb{I}(P^a_t \ge P^a_{t-1})
$$
*   **Instantaneous OFI (per second):** signed touch pressure, positive = upward (bid) pressure:
    $$\text{OFI}_t = e^b_t - e^a_t$$
    By construction: a bid that improves or grows, or an ask that is lifted/pulled up, pushes $\text{OFI}_t > 0$ (bullish); a new/heavier lower ask or a pulled bid pushes it $< 0$ (bearish). A price *equal* to the prior second reduces to the size delta $q_t - q_{t-1}$ at that level. This instantaneous value is persisted per-second in `option_strike_metrics.ofi`.
*   **Windowed OFI:** the cumulative signed pressure over each rolling window $N \in \{5,10,30\}$ s, persisted in `strike_window_metrics.ofi_sum`:
    $$\text{OFI}_N = \sum_{j=0}^{N-1} \text{OFI}_{t-j}$$
    *Note:* OFI is a **touch-level (L1)** quantity by definition — it needs only the best bid/ask, so it is computed even in the 5-level SENSEX/BFO fallback (no deep-book NULL guard applies). On the boundary second after a mid-day restart there is no $t-1$ touch, so $\text{OFI}_t$ is emitted as `NULL` (not 0) to avoid a spurious spike.

---

#### 3.4.4 Multi-Strike Aggregate Matrix
Once per second, the processor resolves the At-The-Money (ATM) strike price ($K_{\text{ATM}}$) relative to the underlying spot price $S_t$ by locating the closest numerical element in the static `active_strikes_list`.

---

##### A. Strike Aggregation Windows
Let $M$ represent the option chain radius limit defined in the configuration (`atm_max_strike_range`, e.g., $M = 20$ for NIFTY, $M = 30$ for SENSEX). Let $\Delta_{\text{strike}}$ represent the auto-detected index strike step. The processor groups active contracts into three strike windows:
1.  **Small Window ($W_{\text{Small}}$):** Strikes within $K_{\text{ATM}} \pm 2 \cdot \Delta_{\text{strike}}$ (representing the immediate near-the-money zone).
2.  **Medium Window ($W_{\text{Medium}}$):** Strikes within $K_{\text{ATM}} \pm \lfloor M/2 \rfloor \cdot \Delta_{\text{strike}}$ (representing the intermediate option chain zone).
3.  **Large Window ($W_{\text{Large}}$):** Strikes within $K_{\text{ATM}} \pm M \cdot \Delta_{\text{strike}}$ (representing the entire active option boundary).

---

##### B. Mathematical Aggregation Formulas
For each window $W \in \{W_{\text{Small}}, W_{\text{Medium}}, W_{\text{Large}}\}$, the processor aggregates call option (CE) and put option (PE) metrics:
*   **Consolidated Option Pressures:** Sum of monetary book pressures for CE and PE contracts:
    $$\text{Pressure}_{\text{CE}, W} = \sum_{K_j \in W} \text{Book Pressure}_{\text{CE}, j} \quad \text{and} \quad \text{Pressure}_{\text{PE}, W} = \sum_{K_j \in W} \text{Book Pressure}_{\text{PE}, j}$$
*   **Depth Put-Call Ratio (Depth PCR):** Ratio of total PE resting depth to CE resting depth across all $L$ levels. **Total resting depth counts both sides of the book** ($q = q^{\text{bid}} + q^{\text{ask}}$), so it measures the liquidity each option type carries independent of directional lean:
    $$\text{Depth PCR}_W = \frac{\sum_{K_j \in W} \sum_{i=1}^{L} \left(q^{\text{bid}}_{\text{PE}, j, i} + q^{\text{ask}}_{\text{PE}, j, i}\right)}{\sum_{K_j \in W} \sum_{i=1}^{L} \left(q^{\text{bid}}_{\text{CE}, j, i} + q^{\text{ask}}_{\text{CE}, j, i}\right) + \epsilon}$$
    *Side & naming (correction):* this is a **liquidity/depth** ratio, distinct from the classical open-interest or traded-volume PCR — label it as such downstream so it is not conflated with sentiment PCR. It sums **both bid and ask** resting quantity; the master spec's §6.1 "CE/PE Depth" used **bid-only**, which mixed resting liquidity with directional lean. Both-sides is the consistent choice here — directional information already lives in Weighted OBI (M8) and $B_{net}$.
*   **Spread Differential:** Difference in mean absolute spreads between puts and calls:
    $$\Delta\text{Spread}_W = \frac{1}{|W|} \sum_{K_j \in W} \text{Spread}_{\text{PE}, j} - \frac{1}{|W|} \sum_{K_j \in W} \text{Spread}_{\text{CE}, j}$$
*   **Net Imbalance Bias ($B_{\text{net}}$):** Measures directional order book pressure. It is computed from **pooled weighted quantities** across the strikes in the window — not by summing per-strike OBI ratios. Let $Q^{\text{bid,w}}_{\cdot,j} = \sum_{i=1}^{L} q_{\text{bid},i}\,w_i$ be the exponentially-weighted (M8) bid quantity for strike $j$, and $Q^{\text{ask,w}}_{\cdot,j}$ the ask analogue:
    $$\text{OBI}_{\text{CE}, W} = \frac{\sum_{K_j \in W}\!\left(Q^{\text{bid,w}}_{\text{CE},j} - Q^{\text{ask,w}}_{\text{CE},j}\right)}{\sum_{K_j \in W}\!\left(Q^{\text{bid,w}}_{\text{CE},j} + Q^{\text{ask,w}}_{\text{CE},j}\right) + \epsilon} \quad (\text{and } \text{OBI}_{\text{PE}, W} \text{ analogously})$$
    $$B_{\text{net}, W} = \text{OBI}_{\text{PE}, W} - \text{OBI}_{\text{CE}, W} \quad \in [-2, 2]$$
    *Scale-invariance (correction):* the previous form, $B_{\text{net}} = \sum_j \text{WeightedOBI}_{\text{PE},j} - \sum_j \text{WeightedOBI}_{\text{CE},j}$, summed **per-strike OBI ratios** (each bounded in $[-1,1]$). That sum grows with the **number of strikes** in the window, so $B_{\text{net}}$ is not comparable across the Small/Medium/Large windows and no single bias threshold $\theta_{\text{bias}}$ (§3.4.4C) can apply to all three. Pooling the weighted bid/ask quantities **before** taking the ratio yields a window-size-independent value in $[-2, 2]$, matching the aggregation approach in the master spec (§6.1).
*   **Net Options Pressure (NOP):** Measures monetary disparity between puts and calls:
    $$\text{NOP}_W = \text{Pressure}_{\text{PE}, W} - \text{Pressure}_{\text{CE}, W}$$
*   **Pinning Score ($PS$):** Measures the likelihood of the spot price pinning near a strike price. It is calculated as the ratio of the largest resting option wall in the Small Window to the average wall size in the Large Window:
    $$PS_W = \frac{\max_{K_j \in W_{\text{Small}}} \left( \text{Wall Size}_{\text{bid}, j}, \text{Wall Size}_{\text{ask}, j} \right)}{\frac{1}{|W_{\text{Large}}|} \sum_{K_k \in W_{\text{Large}}} \max\left( \text{Wall Size}_{\text{bid}, k}, \text{Wall Size}_{\text{ask}, k} \right) + \epsilon}$$

---

##### C. Regime Classification Engine
At each resampled second, the processor classifies the options market regime into one of four states based on the large window ($W_{\text{Large}}$) metrics:
1.  **Trending PE (Bullish Sentiment):** Triggered when net pressure and bias indicate strong buy-side support:
    $$\text{NOP}_{W_{\text{Large}}} > \theta_{\text{pressure}} \quad \text{and} \quad B_{\text{net}, W_{\text{Large}}} > \theta_{\text{bias}}$$
2.  **Trending CE (Bearish Sentiment):** Triggered when net pressure and bias indicate strong sell-side pressure:
    $$\text{NOP}_{W_{\text{Large}}} < -\theta_{\text{pressure}} \quad \text{and} \quad B_{\text{net}, W_{\text{Large}}} < -\theta_{\text{bias}}$$
3.  **Pinning Regime:** Triggered when a dominant strike wall is detected near the spot price, restricting index movement:
    $$PS_{W_{\text{Small}}} > \theta_{\text{pinning}} \quad \text{and} \quad |S_t - K_{\text{ATM}}| \le 0.5 \cdot \Delta_{\text{strike}}$$
4.  **Volatile Regime:** Triggered when liquidity is thin and spreads are wide, indicating high variance:
    $$\text{Mean Relative Spread}_W > \theta_{\text{spread}} \quad \text{and} \quad \text{Quote Stability}_W < 0.4$$
5.  **Balanced (Mean Reverting):** Triggered if none of the directional, pinning, or volatile criteria are met, indicating a stable trading range.

All completed per-second metrics and aggregate records are packaged and pushed directly to the `db_queue`.

### 3.5 Gzip Flat File Writer (`file_writer.py`)
This module is responsible for recording the raw, incoming WebSocket tick stream into a compressed flat file format. By isolating file writing to a dedicated thread, it shields the network receiving loop from disk write latency.

#### 3.5.1 Thread Architecture & Queue Consumer Loop
The module defines a class `RawTickFileWriter` inheriting from `threading.Thread`. It manages an internal loop configured as a consumer pattern:
*   **Thread Execution Loop:** Runs a loop that continues until the shutdown event is signaled and the queue is completely drained:
    ```python
    while not self.shutdown_event.is_set() or not self.queue.empty():
        try:
            packet = self.queue.get(timeout=1.0)
            self._write_packet(packet)
            self.queue.task_done()
        except queue.Empty:
            continue
    ```
*   **Object Serialization:** Converts incoming WebSocket packets (dictionaries) into single-line JSON strings to conform to the JSON Lines (`JSONL`) standard. This ensures that the generated files are compatible with standard data science tooling like Pandas:
    ```python
    # Example reading in pandas
    df = pd.read_json("market_depth_raw_20260702.jsonl.gz", lines=True, compression="gzip")
    ```

---

#### 3.5.2 Gzip Compression & File Handle Details
*   **Compression Configuration:** Opens file handles using Python's native `gzip` module. It uses a compression level of **6** (`compresslevel=6`), which represents the optimal trade-off between CPU compression overhead and output storage size:
    ```python
    self.file_handle = gzip.open(file_path, mode="at", compresslevel=6, encoding="utf-8")
    ```
*   **Path Resolution:** Files are saved within the configured data directory (e.g., `./data/market_depth_raw_YYYYMMDD.jsonl.gz`), using local time for date formatting.

---

#### 3.5.3 Buffered Flushing & Crash Resilience
To protect data against sudden power failures or VM crashes while avoiding constant disk writes, the writer implements a double-flush buffer mechanism:
*   **In-Memory Buffer Accumulation:** Ticks are appended to the Gzip buffer. The OS buffer is not immediately flushed to disk.
*   **Two-tier flush (separate `flush` from `fsync`).** `fsync` is the expensive syscall — at multi-kHz tick rates a per-100-ticks `fsync` would issue ~80 `fsync/sec` and re-introduce the disk stalls this thread exists to avoid. So the userspace `flush()` (cheap, empties the Python/gzip buffer to the OS) runs frequently, but the durable `os.fsync()` runs on a **bounded time cadence** only. Both thresholds are config (`fsync_interval_sec`, `flush_max_records`):
    1.  *Buffer flush (frequent):* when `self.unflushed_count >= flush_max_records` (e.g. 500) → `flush()` only.
    2.  *Durable sync (bounded):* when `time.time() - self.last_fsync_time >= fsync_interval_sec` (e.g. 2.0s) → `flush()` **then** `fsync()`.
*   **Flush Operations:**
    ```python
    self.file_handle.flush()                       # cheap: gzip/OS buffer → page cache
    self.unflushed_count = 0
    if time.time() - self.last_fsync_time >= self.fsync_interval_sec:
        os.fsync(self.file_handle.fileno())        # expensive: page cache → disk, time-bounded
        self.last_fsync_time = time.time()
    ```
    *Crash-window tradeoff:* at most `fsync_interval_sec` of the newest raw ticks can be lost to a hard power failure; both derived stores are reconstructable from raw via the replay path (§8), so this is an acceptable, explicit bound rather than a silent one.

---

#### 3.5.4 Daily File Naming & Graceful Teardown
*   **Filename resolved once per session:** the recorder runs a bounded session (~09:00→15:35 IST) and starts **fresh each morning**, so the daily file `market_depth_raw_YYYYMMDD.jsonl.gz` is resolved **once at startup** from the session date. There is **no live midnight crossing** during a session — the previous "rollover at midnight for 24-hour systems" branch never fires under this schedule and is removed to avoid dead code.
*   **Only defensive guard:** if the process is (unusually) still running as the local date changes, the writer detects the date mismatch on the next write and rolls the file over — flush+`fsync`, close, open the new-dated file — under its writing lock. This path is a safety net, not the normal daily mechanism.
*   **Header meta line (provenance) at open:** the first line written to a freshly-opened raw file is a self-describing HEADER record, complementing the EOF marker, so any raw log is replayable without external metadata:
    ```json
    {"meta_type": "HEADER", "session_date": "2026-07-02", "schema_version": 1, "config_hash": "sha256:…", "underlyings": ["NIFTY", "SENSEX"], "open_timestamp": 1781060400,
     "instruments": {"NIFTY": {"option_exchange": "NFO", "expiry": "09-JUL-26", "strike_step": 50, "contracts": [[24800, "NIFTY…24800CE", "NIFTY…24800PE", 0.05], "…"]}}}
    ```
    Both derived stores stamp the same `schema_version`/`config_hash` (§4.1b), so a rebuild can be tied back to the exact formula/config that produced it. **The HEADER also carries the full resolved chain (`instruments`, P7)** — per underlying the `option_exchange`, weekly `expiry`, detected `strike_step`, and every `[strike, ce_symbol, pe_symbol, tick_size]` contract. This makes the raw log a **self-contained** replay source: the offline rebuild reconstructs the O(1) maps + `tick_size` (M29) via `InstrumentManager.from_header()` with **no REST**, so a log of any age replays correctly even after the live chain has rolled (§8; the orchestrator passes `InstrumentManager.to_header_dict()` to the writer).
*   **Teardown Sequence:**
    Once the queue is drained at `03:35 PM` and the main thread joins the writer, the thread appends an explicit metadata EOF line to mark the log complete:
    ```json
    {"meta_type": "EOF", "record_count": 1045020, "close_timestamp": 1781084100}
    ```
    It then executes a final flush, calls `os.fsync()`, closes the file handle, and terminates.

### 3.6 Store Writers (`database_writer.py`)
This module houses **two** writers with the same logical schema (§4) but different backends, matched to their access pattern:
*   **`SQLiteLiveWriter`** — the live-path writer (§3.6.1–§3.6.4). Runs as a background thread during market hours, committing small per-second batches of the `recorder.live_metrics` subset to the thin SQLite/WAL store.
*   **`DuckDBAnalyticalWriter`** — the offline-path writer (§3.6.5). Runs inside the end-of-session replay subprocess (§8, §8.6), bulk-loading the **full** §4 catalog into the fat DuckDB store in one pass.

Both consume the identical row tuples emitted by `TickProcessor`; only the sink and the load strategy (incremental transactions vs. one bulk append) differ.

#### 3.6.1 Live Writer — Thread Architecture & Batch Transaction Engine
The live database writer runs as a background thread defined in class `SQLiteLiveWriter(threading.Thread)`. It manages a FIFO consumer loop linked to the `db_queue`, targeting the thin live store (`market_depth_live_YYYYMMDD.db`); it receives only the `recorder.live_metrics` columns (the rest of each row is `NULL`). Small, frequent commits are exactly SQLite/WAL's strength, so the live path never blocks on the store.
*   **Queue Consumption:** The thread continuously monitors the `db_queue`. It accumulates incoming metric rows for **all four tables** (spot states, instantaneous strike metrics, rolling strike-window metrics, and multi-strike aggregates) in memory buffers:
    ```python
    batch_spot, batch_strikes, batch_strike_windows, batch_aggs = [], [], [], []
    ```
*   **Transactional Batching Logic:** Writing is triggered either when the buffer length reaches 500 rows or when 1 second has elapsed since the last write. The thread groups the statements inside a single transaction to bypass SQLite's default auto-commit overhead:
    ```python
    try:
        conn.execute("BEGIN TRANSACTION")
        if batch_spot:
            cursor.executemany("INSERT OR IGNORE INTO spot_states VALUES (?, ?, ?, ?)", batch_spot)
        if batch_strikes:
            cursor.executemany("INSERT OR IGNORE INTO option_strike_metrics VALUES (?, ?, ?, ...)", batch_strikes)
        if batch_strike_windows:
            cursor.executemany("INSERT OR IGNORE INTO strike_window_metrics VALUES (?, ?, ?, ...)", batch_strike_windows)
        if batch_aggs:
            cursor.executemany("INSERT OR IGNORE INTO aggregated_window_metrics VALUES (?, ?, ?, ...)", batch_aggs)
        conn.commit()
        ignored = expected_rows - conn.total_changes_delta  # count PK-collision drops (see §4.3)
        if ignored:
            logger.warning("db_writer: %d rows ignored on PK collision", ignored)
    except sqlite3.Error as e:
        conn.rollback()
        # Log critical error
    ```
    *Restart overlap:* for the single boundary second immediately after a mid-day restart, the writer switches these statements to `INSERT OR REPLACE` so the freshest recomputation wins rather than being silently ignored (§4.3).

---

#### 3.6.2 Live Writer — High-Performance PRAGMA Tuning
Upon opening a connection to the daily **live** database, `SQLiteLiveWriter` executes a specific sequence of SQLite `PRAGMA` commands to tune memory and caching:
*   `PRAGMA journal_mode = WAL;` (Write-Ahead Logging: writing is decoupled from the main database file by using a separate `.db-wal` transaction log, preventing lock conflicts during queries).
*   `PRAGMA synchronous = NORMAL;` (Reduces disk synchronization cycles. Safe in WAL mode since checkpoint operations are handled independently, improving write latency).
*   `PRAGMA temp_store = MEMORY;` (Instructs SQLite to store transient indexing structures and temporary query outputs directly in RAM).
*   `PRAGMA cache_size = -64000;` (Sets database cache to 64MB, ensuring indexes remain in memory for faster insertion).

---

#### 3.6.3 Live Writer — Daily Database Selection & Table Initialization
*   **DB selected once per session:** like the raw file, the live daily database `data/market_depth_live_YYYYMMDD.db` (the thin Tier-1 store) is resolved **at startup** from the session date; the bounded 09:00→15:35 session never crosses midnight, so there is no live rollover in normal operation (the old "check the date at midnight" step is removed as dead code). The same defensive date-mismatch guard as §3.5.4 applies only if the process runs unusually long: drain+commit, close cleanly, open the new-dated DB. (The offline replay writes the fat `market_depth_analytics_YYYYMMDD.duckdb` via `DuckDBAnalyticalWriter` — see §3.6.5.)
*   **Database Schema Creation:** If the new daily database file did not exist, the connection routine automatically runs the SQLite creation statements for the **four tables** (`spot_states`, `option_strike_metrics`, `strike_window_metrics`, `aggregated_window_metrics`) and constructs the secondary indexes (§4.2). It then applies the PRAGMA performance tuning parameters.

---

#### 3.6.4 Live Writer — Teardown Protocol
When the scheduler signals a shutdown at `03:35 PM` by setting the global shutdown event, the `SQLiteLiveWriter` thread:
1.  Continues the consumer loop until `db_queue.empty() == True`, ensuring all processed metrics from the end of the session are captured.
2.  Commits the final transaction batch.
3.  Runs `PRAGMA optimize;` to optimize database indexes.
4.  Closes the database connection handle cleanly.
5.  Terminates execution.

---

#### 3.6.5 Analytical Writer — DuckDB Bulk Load (offline)
`DuckDBAnalyticalWriter` runs **only** inside the end-of-session replay subprocess (§8, §8.6), never during live capture. Because replay produces the entire day in one CPU-bound pass, it does not need per-second transactions — it uses DuckDB's **bulk append** path, which is dramatically faster than row-at-a-time inserts:
*   **One connection, write-once:** opens a fresh `market_depth_analytics_YYYYMMDD.duckdb`, runs the DuckDB DDL (§4.1), bulk-loads all four tables, `CHECKPOINT`s, and closes. There is no long-lived open handle and no concurrent reader/writer contention (single writer by construction).
*   **Columnar bulk insert:** rows are accumulated per table and handed to DuckDB in large chunks. The preferred path is the **Appender** API (`conn.append(table, dataframe)` / `duckdb.Appender`) or a registered Arrow/Pandas frame consumed by `INSERT INTO t SELECT * FROM df`. Either way the analytical build materializes each table in a handful of vectorized writes rather than millions of single-row statements.
    ```python
    # Sketch (offline path): accumulate then bulk-append per table
    con = duckdb.connect(output_path)
    con.execute(DDL_ALL_TABLES)                     # §4.1 DuckDB dialect
    con.register("osm_df", strike_rows_frame)       # Arrow/Pandas frame from the replayed rows
    con.execute("INSERT INTO option_strike_metrics SELECT * FROM osm_df")
    # …repeat for spot_states / strike_window_metrics / aggregated_window_metrics…
    con.execute("CHECKPOINT")
    con.close()
    ```
*   **Memory-bounded:** for a full trading day the four frames fit comfortably in memory (well under the 500 MB target), but the writer still loads table-by-table (and, if needed, in timestamp-ordered chunks) so peak RAM stays bounded regardless of session length. DuckDB's own `memory_limit`/`threads` are set from config (§7).
*   **Idempotency by fresh file:** each build writes a brand-new `.duckdb`; re-running replay on the same raw log simply overwrites it with identical content (§8.5). There is no `INSERT OR IGNORE`/`INSERT OR REPLACE` collision handling to reason about, because the bulk build never appends to a pre-existing populated store.
*   **FD hygiene:** the connection is opened in a `with`/`try…finally` so the DuckDB handle (and any transient `.wal`) is always closed and checkpointed, even on error — and the whole writer lives in the reaped replay subprocess, so nothing leaks into the long-running recorder daemon.

---

## 4. Database Schema Design (dual backend: live SQLite + analytical DuckDB)

This **one logical schema** is shared by both derived stores (§1, §2.1): the thin live store (`market_depth_live_YYYYMMDD.db`, **SQLite**) populates only the `recorder.live_metrics` columns, while the fat analytical store (`market_depth_analytics_YYYYMMDD.duckdb`, **DuckDB**) fills every column from the offline replay. The column names, meanings, and primary keys are identical across both backends — only the physical DDL dialect and storage engine differ (SQLite row-store for live incremental writes; DuckDB column-store for the offline bulk build and analytical scans). Each store holds the same **four tables** with clean separation of concerns: index spots (`spot_states`), instantaneous per-strike metrics (`option_strike_metrics`), rolling per-strike windowed metrics (`strike_window_metrics`), and instantaneous multi-strike aggregates (`aggregated_window_metrics`). This split ensures every metric computed in §3.4 has exactly one persistence home and no row is written redundantly.

Below, **§4.1** gives the canonical SQLite DDL (the live store) and **§4.1a** the DuckDB dialect (the analytical store); the two are column-for-column equivalent.

```
┌───────────────────────────────────────┐
│              spot_states              │
├───────────────────────────────────────┤
│ timestamp (PK) | symbol (PK)          │
│ spot_price                            │
│ atm_strike                            │
└──────────────────┬────────────────────┘
                   │
                   │ (1 : N)
                   ▼
┌───────────────────────────────────────┐        ┌───────────────────────────────────────┐
│         option_strike_metrics         │        │        strike_window_metrics          │
│         (instantaneous, ROWID)        │        │  (rolling per time_window, ROWID)     │
├───────────────────────────────────────┤        ├───────────────────────────────────────┤
│ timestamp (PK) | symbol (PK)          │        │ timestamp (PK) | symbol (PK)          │
│ depth_levels   | is_50_depth          │◄──1:3──►│ time_window (PK: 5/10/30)             │
│ strike_price   | option_type          │        │ price_return   | spread_mean/min/max  │
│ ltp            | spread               │        │ spread_std     | wobi_mean/std/slope  │
│ relative_spread| mid_price            │        │ book_pressure_slope                   │
│ micro_price    | weighted_obi         │        │ liquidity_added| liquidity_removed    │
│ raw_obi        | top5_obi / top10_obi │        │ book_churn     | flow_intensity       │
│ book_pressure  | best_bid/ask_qty     │        │ pressure_velocity / _acceleration     │
│ oci            | effective_depth      │        │ wall_persistence                      │
│ bid/ask_wall_price/qty | wall_score   │        │ walls_created  | walls_destroyed      │
│ quote_stability| confidence           │        └───────────────────────────────────────┘
└───────────────────────────────────────┘
                   │
                   │ (per second, aggregated over strikes → SMALL/MEDIUM/LARGE windows)
                   ▼
┌───────────────────────────────────────┐
│        aggregated_window_metrics      │  PK (timestamp, underlying, strike_window)
├───────────────────────────────────────┤  depth_pcr | ce/pe_pressure | bnet | spread_diff
│  (instantaneous multi-strike, no      │  net_options_pressure | pinning_score | regime
│   time_window — see §4.1 Table 4)     │
└───────────────────────────────────────┘
```

---

### 4.1 SQL Schema Statements (SQLite — thin live store)

```sql
-- Table 1: Spot Price States
-- Stores underlying index spot updates exactly once per second.
CREATE TABLE spot_states (
    timestamp INTEGER NOT NULL,    -- UNIX epoch timestamp in seconds (UTC)
    symbol TEXT NOT NULL,          -- Index identifier in OpenAlgo format (e.g., "NIFTY" / "SENSEX"; exchange NSE_INDEX / BSE_INDEX)
    spot_price REAL NOT NULL,      -- Last Traded Price (LTP) of the index spot
    atm_strike INTEGER NOT NULL,   -- Resolved ATM strike price based on spot and step mode
    PRIMARY KEY (timestamp, symbol)
) WITHOUT ROWID;

-- Table 2: Per-Strike Per-Second Metrics
-- Stores the calculated metrics for every active option strike price.
CREATE TABLE option_strike_metrics (
    timestamp INTEGER NOT NULL,    -- UNIX epoch timestamp in seconds (UTC)
    symbol TEXT NOT NULL,          -- Option contract symbol WITHOUT the ":50" transport suffix (e.g., "NIFTY26JUN23400CE")
    strike_price REAL NOT NULL,    -- Numerical strike price (e.g., 23400.0)
    option_type TEXT NOT NULL,     -- Option type identifier ("CE" or "PE")
    depth_levels INTEGER,          -- ACTUAL levels this row was computed from (50 = TBT, 5 = fallback). Self-describes the row (see §3.2.5)
    is_50_depth INTEGER,           -- 1 if full 50-level TBT feed, 0 if 5-level fallback. Deep-book metrics below are NULL when 0
    ltp REAL,                      -- Option last traded price
    spread REAL,                   -- Absolute bid-ask spread (P_ask1 - P_bid1)
    relative_spread REAL,          -- Relative spread (Spread / MidPrice)
    mid_price REAL,                -- Standard Mid Price ((P_bid1 + P_ask1) / 2)
    micro_price REAL,              -- Volume-Weighted Mid Price
    weighted_obi REAL,             -- Imbalance weighted by exponential decay (-1.0 to 1.0)
    raw_obi REAL,                  -- Raw volume imbalance across all 50 levels (-1.0 to 1.0)
    top5_obi REAL,                 -- Volume imbalance across top 5 levels (-1.0 to 1.0)
    top10_obi REAL,                -- Volume imbalance across top 10 levels (-1.0 to 1.0)
    bid_stack_ratio REAL,          -- Bid volume / total volume (0.0 to 1.0)
    ask_stack_ratio REAL,          -- Ask volume / total volume (0.0 to 1.0)
    book_pressure REAL,            -- Top 10 level MID-CENTERED depth imbalance: Σ d_bid·q_bid − Σ d_ask·q_ask (§3.4.2 M11; +ve = bid-heavy)
    best_bid_qty REAL,             -- Raw quantity resting at best bid (touch level)
    best_ask_qty REAL,             -- Raw quantity resting at best ask (touch level)
    avg_order_size_bid REAL,       -- Average order size across bid levels
    avg_order_size_ask REAL,       -- Average order size across ask levels
    oci REAL,                      -- Order Count Imbalance ratio (-1.0 to 1.0)
    effective_depth REAL,          -- Total volume resting within +/- 0.5% of mid price
    lci_bid REAL,                  -- Liquidity Concentration Index for bids (top 5 / total volume)
    lci_ask REAL,                  -- Liquidity Concentration Index for asks (top 5 / total volume)
    touch_dominance_bid REAL,      -- Touch volume / top 5 volume
    touch_dominance_ask REAL,      -- Touch volume / top 5 volume
    round_number_depth_bid REAL,   -- Total bid volume resting at round-number prices
    round_number_depth_ask REAL,   -- Total ask volume resting at round-number prices
    bid_wall_price REAL,           -- Price of the largest bid wall order
    bid_wall_qty REAL,             -- Quantity resting at the largest bid wall
    ask_wall_price REAL,           -- Price of the largest ask wall order
    ask_wall_qty REAL,             -- Quantity resting at the largest ask wall
    wall_score_bid REAL,           -- Bid wall size / median bid size ratio
    wall_score_ask REAL,           -- Ask wall size / median ask size ratio
    quote_stability REAL,          -- Quote stability ratio over the rolling window
    confidence REAL,               -- Normalized recording confidence score (0.0 to 1.0)
    ofi REAL,                      -- Instantaneous best-level Order Flow Imbalance for this second (§3.4.3-E; +ve = bid pressure; NULL on post-restart boundary second)
    fill_slippage_buy REAL,        -- Relative slippage vs mid to BUY fill_probe_qty (§3.4.2 M25; NULL if book too thin)
    fill_slippage_sell REAL,       -- Relative slippage vs mid to SELL fill_probe_qty (§3.4.2 M25; NULL if book too thin)
    book_slope_bid REAL,           -- Bid-side price impact per unit qty, Kyle-λ proxy (§3.4.2 M25)
    book_slope_ask REAL,           -- Ask-side price impact per unit qty, Kyle-λ proxy (§3.4.2 M25)
    queue_imbalance REAL,          -- Touch (L1) OBI: (q_bid1 − q_ask1)/(q_bid1 + q_ask1), −1..1 (§3.4.2 M26)
    vamp REAL,                     -- Volume-Adjusted Mid Price, multi-level micro-price generalization (§3.4.2 M27)
    microprice_ltp_div REAL,       -- Fair-value gap: (micro_price − ltp)/ltp (§3.4.2 M28)
    spread_ticks REAL,             -- Spread / tick_size (§3.4.2 M29; NULL if tick size unknown)
    -- Wide row (~40 cols): kept as a normal ROWID table (NOT WITHOUT ROWID) — see §4.3 for why
    -- WITHOUT ROWID pessimizes wide rows. PK below becomes a UNIQUE index over the rowid table.
    PRIMARY KEY (timestamp, symbol)
);

-- Table 3: Per-Strike Rolling-Window Metrics  (NEW — closes the gap where §3.4.3 metrics had nowhere to be stored)
-- One row per (strike symbol, second, time_window). time_window ∈ {5,10,30} genuinely varies these columns,
-- unlike the aggregate table below. All columns are the rolling/windowed outputs of §3.4.3.
CREATE TABLE strike_window_metrics (
    timestamp INTEGER NOT NULL,      -- UNIX epoch timestamp in seconds (UTC)
    symbol TEXT NOT NULL,            -- Option contract symbol (no ":50" suffix), matches option_strike_metrics.symbol
    time_window INTEGER NOT NULL,    -- Rolling window duration in seconds (5, 10, or 30)
    price_return REAL,               -- LTP % return over the window (§3.4.3-A)
    spread_mean REAL,                -- Rolling mean of absolute spread
    spread_min REAL,                 -- Rolling min spread
    spread_max REAL,                 -- Rolling max spread
    spread_std REAL,                 -- Rolling std of spread
    wobi_mean REAL,                  -- Rolling mean of Weighted OBI
    wobi_std REAL,                   -- Rolling std of Weighted OBI
    wobi_slope REAL,                 -- Linear-regression slope of Weighted OBI over the window
    book_pressure_slope REAL,        -- Linear-regression slope of Book Pressure over the window
    liquidity_added REAL,            -- ΔQ+ replenishment at unchanged price levels (§3.4.3-B)
    liquidity_removed REAL,          -- ΔQ- cancellations/fills at unchanged price levels
    book_churn REAL,                 -- Cumulative added+removed over the window
    flow_intensity REAL,             -- Count of active seconds in window with ΔQ+ or ΔQ-
    pressure_velocity REAL,          -- 1st-order rate of change of Book Pressure (§3.4.3-C)
    pressure_acceleration REAL,      -- 2nd-order rate of change of Book Pressure
    ofi_sum REAL,                    -- Cumulative best-level Order Flow Imbalance over the window (§3.4.3-E)
    micro_price_rv REAL,             -- Realized volatility of micro price over the window, sqrt(Σ r²) of 1s log returns (§3.4.3-A)
    wall_persistence REAL,           -- Consecutive seconds the wall held at one price (§3.4.3-D)
    walls_created INTEGER,           -- Count of new walls appearing over the window
    walls_destroyed INTEGER,         -- Count of walls disappearing over the window
    PRIMARY KEY (timestamp, symbol, time_window)
);

-- Table 4: Aggregated Option Chain Metrics
-- INSTANTANEOUS per-second multi-strike aggregates, one row per (second, underlying, strike_window).
-- NOTE: time_window was REMOVED from this table. §3.4.4 defines these as per-second aggregates only;
-- they do NOT vary by 5/10/30s, so the old (…, time_window) PK wrote 3 identical rows every second.
CREATE TABLE aggregated_window_metrics (
    timestamp INTEGER NOT NULL,          -- UNIX epoch timestamp in seconds (UTC)
    underlying TEXT NOT NULL,            -- Configured underlying name (e.g., "NIFTY", "SENSEX")
    strike_window TEXT NOT NULL,         -- Strike grouping window identifier ("SMALL", "MEDIUM", "LARGE")
    depth_pcr REAL,                      -- Depth Put-Call Ratio: Σ PE (bid+ask) qty / Σ CE (bid+ask) qty (§3.4.4-B; liquidity ratio, not OI/volume PCR)
    ce_pressure REAL,                    -- Consolidated CE book pressure
    pe_pressure REAL,                    -- Consolidated PE book pressure
    bnet REAL,                           -- Net Imbalance Bias: pooled PE Weighted OBI − pooled CE Weighted OBI, ∈[-2,2] (§3.4.4-B)
    spread_diff REAL,                    -- Mean PE spread − mean CE spread
    net_options_pressure REAL,           -- NOP: PE Book Pressure − CE Book Pressure (was duplicated as "market_bias" — removed)
    pinning_score REAL,                  -- Pinning Score PS (§3.4.4-B) — previously computed but not persisted
    regime TEXT,                         -- State classification ("Trending PE/CE", "Pinning", "Volatile", "Balanced")
    PRIMARY KEY (timestamp, underlying, strike_window)
) WITHOUT ROWID;
```

---

### 4.1a DuckDB Dialect (fat analytical store)
The analytical store carries the **same four tables, same columns, same primary keys**, expressed in DuckDB's richer type system. The mapping is mechanical:

| SQLite (live) | DuckDB (analytical) | Notes |
| :--- | :--- | :--- |
| `INTEGER` timestamp | `BIGINT` | UNIX epoch seconds; DuckDB `BIGINT` avoids any 32-bit ambiguity. |
| `INTEGER` (depth_levels, walls_*, atm_strike) | `INTEGER` | Small counts. |
| `is_50_depth INTEGER` (0/1) | `BOOLEAN` | DuckDB has a native boolean; live SQLite keeps 0/1. |
| `REAL` (all metric columns) | `DOUBLE` | 64-bit float. |
| `TEXT` (symbol, option_type, regime, strike_window) | `VARCHAR` | |
| `WITHOUT ROWID` | *(omitted)* | Meaningless in a column store — DuckDB has no rowid; PKs are declared but storage is columnar (§4.3). |

```sql
-- DuckDB dialect — analytical store (market_depth_analytics_YYYYMMDD.duckdb).
-- Column set is identical to §4.1; only types/engine differ. Example for the two representative tables:
CREATE TABLE spot_states (
    timestamp   BIGINT  NOT NULL,
    symbol      VARCHAR NOT NULL,
    spot_price  DOUBLE  NOT NULL,
    atm_strike  INTEGER NOT NULL,
    PRIMARY KEY (timestamp, symbol)
);

CREATE TABLE option_strike_metrics (
    timestamp     BIGINT  NOT NULL,
    symbol        VARCHAR NOT NULL,
    strike_price  DOUBLE  NOT NULL,
    option_type   VARCHAR NOT NULL,
    depth_levels  INTEGER,
    is_50_depth   BOOLEAN,            -- native boolean (0/1 in the SQLite live store)
    ltp DOUBLE, spread DOUBLE, relative_spread DOUBLE, mid_price DOUBLE, micro_price DOUBLE,
    weighted_obi DOUBLE, raw_obi DOUBLE, top5_obi DOUBLE, top10_obi DOUBLE,
    bid_stack_ratio DOUBLE, ask_stack_ratio DOUBLE, book_pressure DOUBLE,
    best_bid_qty DOUBLE, best_ask_qty DOUBLE, avg_order_size_bid DOUBLE, avg_order_size_ask DOUBLE,
    oci DOUBLE, effective_depth DOUBLE, lci_bid DOUBLE, lci_ask DOUBLE,
    touch_dominance_bid DOUBLE, touch_dominance_ask DOUBLE,
    round_number_depth_bid DOUBLE, round_number_depth_ask DOUBLE,
    bid_wall_price DOUBLE, bid_wall_qty DOUBLE, ask_wall_price DOUBLE, ask_wall_qty DOUBLE,
    wall_score_bid DOUBLE, wall_score_ask DOUBLE, quote_stability DOUBLE, confidence DOUBLE,
    ofi DOUBLE,                       -- Instantaneous best-level Order Flow Imbalance (§3.4.3-E)
    fill_slippage_buy DOUBLE, fill_slippage_sell DOUBLE,        -- Cost-to-fill slippage vs mid (§3.4.2 M25)
    book_slope_bid DOUBLE, book_slope_ask DOUBLE,              -- Kyle-λ price impact per unit qty (§3.4.2 M25)
    queue_imbalance DOUBLE,           -- Touch (L1) OBI (§3.4.2 M26)
    vamp DOUBLE,                      -- Volume-Adjusted Mid Price (§3.4.2 M27)
    microprice_ltp_div DOUBLE,        -- Micro-price / LTP fair-value gap (§3.4.2 M28)
    spread_ticks DOUBLE,              -- Spread in ticks (§3.4.2 M29)
    PRIMARY KEY (timestamp, symbol)
);
-- strike_window_metrics and aggregated_window_metrics follow the same 1:1 type mapping.
```

> **Why no `WITHOUT ROWID` / PRAGMA / WAL tuning here.** Those are SQLite row-store concepts (§4.3, §3.6.2) that keep the *live* incremental path fast. DuckDB is columnar and writes the analytical store in a single bulk pass (§3.6.5), so none of them apply — DuckDB manages its own storage, compression, and (checkpointed) WAL internally.

---

### 4.1b Provenance Table (`recorder_meta`, both backends)
Both stores carry a tiny `recorder_meta` table stamping the build's provenance so a file is self-describing and `--verify` (§8.4) can refuse to diff mismatched schemas. It mirrors the raw file's HEADER line (§3.5.4):
```sql
CREATE TABLE recorder_meta (
    schema_version INTEGER NOT NULL,   -- bumped when the §4 column set changes
    config_hash    TEXT    NOT NULL,   -- sha256 of the metrics/regime/underlyings config that produced this store
    built_by       TEXT    NOT NULL,   -- "live" (SQLite live store) or "replay" (DuckDB analytical store)
    build_time     INTEGER NOT NULL,   -- UNIX epoch seconds
    source_raw     TEXT               -- raw .jsonl.gz filename for a replayed store (NULL for the live store)
);
```
The live SQLite store writes one row at DB creation (`built_by="live"`); the offline DuckDB build writes one row naming the raw log it replayed (`built_by="replay"`, `source_raw=…`). (DuckDB dialect: `schema_version`/`build_time` → `INTEGER`/`BIGINT`, text → `VARCHAR`.)

---

### 4.2 Secondary Indexing Strategies
To optimize queries for analytical models and visualization dashboards, the **live SQLite** store creates secondary composite indexes:
*   `idx_osm_strike`: on `option_strike_metrics (strike_price, option_type)` — strike-level time-series of a specific strike over the session.
*   `idx_osm_ts`: on `option_strike_metrics (timestamp)` — temporal slices (whole option chain state for a given second).
*   `idx_swm_symbol`: on `strike_window_metrics (symbol, time_window)` — rolling-window trend of one strike at a chosen window.
*   `idx_spot_ts`: on `spot_states (timestamp)` — joins between index spot prices and options metrics.

```sql
CREATE INDEX idx_osm_strike  ON option_strike_metrics (strike_price, option_type);
CREATE INDEX idx_osm_ts      ON option_strike_metrics (timestamp);
CREATE INDEX idx_swm_symbol  ON strike_window_metrics (symbol, time_window);
CREATE INDEX idx_spot_ts     ON spot_states (timestamp);
```
*(`spot_states` and `aggregated_window_metrics` are `WITHOUT ROWID`, so their compound PK already serves as the clustered primary index — no extra index needed. `option_strike_metrics` and `strike_window_metrics` are ROWID tables; their `PRIMARY KEY` is a UNIQUE index used for upserts and the above secondary indexes cover the common query paths.)*

**DuckDB analytical store — no explicit secondary indexes.** DuckDB is columnar and automatically maintains per-column **min/max zonemaps** on row-group blocks, which prune the full-session range scans and column-subset reads that dominate the analytical/backtest workload — so the `idx_*` indexes above are neither created nor needed there. DuckDB does build an ART index for each declared `PRIMARY KEY` (used for constraint enforcement and point lookups); beyond that, an explicit index is added only if a concrete query proves it necessary. This is another reason the two backends diverge: the live store leans on B-tree indexes for point/upsert access, the analytical store on columnar scans.

---

### 4.3 Storage Layout (`WITHOUT ROWID` — live SQLite only, applied selectively)
This subsection concerns the **live SQLite store only**; the DuckDB analytical store is columnar and has no rowid concept (§4.1a). By default, SQLite tables include a hidden 64-bit `rowid`; secondary indexes point to it, requiring a two-step lookup. Declaring a compound-PK table `WITHOUT ROWID` stores rows directly in the PK B-Tree, saving the redundant rowid key.
*   **Applied only to narrow tables:** `spot_states` (4 cols) and `aggregated_window_metrics` (~10 cols) are `WITHOUT ROWID` — small rows fit comfortably in the B-Tree pages, so they gain the storage/lookup benefit.
*   **NOT applied to wide tables (important correction):** `option_strike_metrics` (~40 cols) and `strike_window_metrics` (~21 cols) are **normal ROWID tables**. SQLite's own guidance is that `WITHOUT ROWID` helps for *small* rows; for wide rows it can **pessimize**, because a row exceeding ~½ page spills into overflow pages that the clustered B-Tree must chase — hurting the exact high-frequency inserts this schema optimizes for. These tables keep the compound `PRIMARY KEY` as a UNIQUE index (used for upserts) plus the §4.2 secondary indexes.
*   **Insert semantics (collision handling — live store):** the live `SQLiteLiveWriter` uses `INSERT OR IGNORE`, which **silently discards** a row whose PK already exists (e.g. a mid-day restart that re-emits the boundary second). To avoid silent loss, either (a) use `INSERT OR REPLACE` so the freshest computation wins, or (b) keep `OR IGNORE` but **count and log** ignored rows so overlaps are visible. This design chooses **(b)** for the append-mostly steady state and **(a)** only for the single overlap-second immediately after a restart. See §3.6.1. *(The DuckDB analytical store sidesteps this entirely: it is bulk-built once into a fresh file per day (§3.6.5), so there are no in-place PK collisions to resolve.)*

---

### 4.4 Daily Database Maintenance & Checkpoints
Since database files are rotated daily (both `market_depth_live_YYYYMMDD.db` and `market_depth_analytics_YYYYMMDD.duckdb`), long-term table pruning is not required. The maintenance below applies to the **live** store, which the writer holds open all session; the analytics store is written once, in a single offline pass, and closed. To ensure database health and query speed, the following operations are run:
*   **WAL Checkpoints:** The batched database writer runs a passive checkpoint (`PRAGMA wal_checkpoint(PASSIVE);`) every `wal_checkpoint_interval_sec` (default 600s) to merge the `.db-wal` back into the primary `.db`, preventing the WAL from growing without bound.
*   **End-of-Session Optimization:** During teardown (~15:35 IST), the orchestrator runs **only**:
    ```sql
    PRAGMA wal_checkpoint(TRUNCATE);   -- fold WAL back and shrink it to zero
    PRAGMA optimize;                    -- refresh index statistics (cheap)
    ```
*   **No `VACUUM` (correction):** the earlier design ran a daily `VACUUM`, which is dropped. `VACUUM` rewrites the entire database file, needs up to **2× the file size** in free disk, and can take minutes on a multi-GB daily depth file — all to defragment a file that is written append-mostly, once, and never pruned (the section's own premise). It provides no query benefit here and risks blocking a clean shutdown. Fresh file each morning already yields a compact, unfragmented database.
*   **DuckDB analytical store (write-once, then read-only):** the fat store needs no ongoing maintenance loop. The offline build (§3.6.5) bulk-loads it, issues a single `CHECKPOINT` to fold DuckDB's internal WAL into the main file, and closes the connection — after which the `.duckdb` is an immutable, columnar, block-compressed artifact for the day. There is no per-second WAL growth to manage (the whole store is written in one pass) and no `VACUUM` (DuckDB compresses and lays out row groups at write time). Downstream research/backtests open it **read-only**, so there is no writer contention to tune.

---

*Note: `WITHOUT ROWID` is used only on the narrow tables (`spot_states`, `aggregated_window_metrics`) where it reduces size/lookup latency; the wide per-strike tables stay as ROWID tables to avoid overflow-page penalties (see §4.3).*

---

## 5. Threading, Queue Safety & Backpressure

To handle burst updates, the microservice separates networking, calculation, and database writes into independent threads linked by thread-safe FIFO queues.

### 5.1 Concurrency Architecture & Thread Functions
The service utilizes four concurrent threads linked by **three** bounded queues. The WebSocket receiver **tees** each packet into two independent queues so the audit and analytics paths are fully decoupled (a shared `queue.Queue` would split ticks between consumers — see §2.2 Phase D):
1.  **Feed Delivery (SDK callback thread, or raw receiver thread in fallback):** on the primary transport the SDK invokes `on_data_received` on its own delivery thread; on the raw fallback (§3.3.1a) a receiver thread blocks on socket reads. Either way, for each depth packet the handler performs a fan-out — one `put` to `raw_file_queue` and one `put` to `proc_queue` — and returns immediately so the delivery thread is never blocked. The audit `put` uses a brief blocking `put(timeout=…)` (so the lossless path applies backpressure before dropping), while the analytics `put` uses `put_nowait()` and drops-with-counter when full (analytics sheds first).
2.  **Raw Logging Thread (`RawTickFileWriter`):** Blocks on `raw_file_queue`. It drains packets, serializes them to JSON Lines, gzip-compresses, and flushes to the `.jsonl.gz` file.
3.  **Resampling & Processing Thread (`TickProcessor`):** Drains `proc_queue` into an in-memory symbol tick cache. It runs a 1-second interval execution timer to compute metrics and pushes database rows to `db_queue`.
4.  **Database Batching Thread (`SQLiteLiveWriter`):** Blocks on `db_queue`. It drains computed records, packages them, and commits them to SQLite in transactions.

```
 ┌───────────────┐   put(timeout)  ┌────────────────┐      ┌───────────────┐
 │   WebSocket   ├────────────────►│ raw_file_queue │─────►│  File Writer  │
 │   Receiver    │   (tee: audit)  │  (Size Limit)  │      │ Thread (Gzip) │
 │  (fan-out)    │                 └────────────────┘      └───────────────┘
 └──────┬────────┘
        │  put_nowait (tee: analytics)
        ▼
 ┌────────────────┐      ┌───────────────┐      ┌───────────────┐      ┌───────────────┐
 │   proc_queue   │─────►│   Processor   ├─────►│   db_queue    │─────►│  DB Writer    │
 │  (Size Limit)  │      │  (Resampler)  │      │ (Size Limit)  │      │Thread(SQLite) │
 └────────────────┘      └───────────────┘      └───────────────┘      └───────────────┘
```
*   **Locking Strategy & Thread-Safe State Isolation:**
    Access to variables shared across threads (such as `self.active_subscriptions` and `self.current_spot_prices`) is guarded by Reentrant Locks (`threading.RLock()`) to prevent race conditions during dynamic strike additions. Spot ticker caches are isolated under a dedicated `self.spot_lock`. To prevent deadlocks, threads must never request locks out of order (always `spot_lock` followed by `RLock`), and no network or I/O calls are executed inside lock scopes.
*   **Backpressure Handling & Degraded Mode Engine (per-queue, audit-protected):**
    *   All queues are initialized with a configurable maximum size (e.g., `proc_queue = queue.Queue(maxsize=50000)`).
    *   **Analytics sheds first.** If `db_queue` or `proc_queue` reaches the warning watermark (default 70%), the `TickProcessor` enters *Degraded Processing Mode*: it **skips the CPU-heavy rolling-window work** (linear-regression slopes, wall-score median scans, quote-stability/velocity/acceleration) and writes those columns as `NULL`. **The 1-second cadence is preserved** — degraded mode never changes the resample interval, because a variable grid (e.g. the old "SENSEX → 2s" rule) breaks the uniform-1s guarantee that §6.2 and downstream pandas rolling ops depend on.
    *   *Note on payload:* the schema is fixed-width, so writing fewer metrics does **not** shrink the SQLite row (skipped columns become `NULL`, same on-disk footprint). Degraded mode's benefit is **CPU/latency relief on the processor**, not DB payload reduction — the earlier "65% payload reduction" claim was incorrect and is removed.
    *   **Overload of the analytics path** (`proc_queue` at 90%+): drop the *oldest cached tick updates* for the least-active symbols (counted + logged). Metrics still emit each second via forward-fill/staleness, so the time grid stays intact.
    *   **The audit path is protected.** A raw packet is dropped **only** if `raw_file_queue` itself saturates (disk cannot keep up); every such drop increments a counter and is logged at ERROR. This is the single, explicit exception to lossless raw capture (see §1.4).
    *   **Thin live path lowers the pressure.** Because the live processor computes only the `recorder.live_metrics` subset (§3.4.1) rather than the full §4 catalog, the per-second cycle is far cheaper and `proc_queue` overload is correspondingly rarer — the exhaustive work is deferred to the offline build (§8), which has no real-time deadline. Analytics-path degradation is therefore a genuine last resort, not an expected steady state, and it never threatens the fat store (which is rebuilt from the always-protected raw log regardless of what the live path shed).
*   **Memory Optimization (Slots):**
    Option depth tick classes are structured using `__slots__` arrays to bypass Python's dynamic instance dictionaries. This reduces individual tick object memory usage by 80%, keeping memory footprints under 500 MB under heavy trading loads.

---

### 5.2 Scaling the Processor to a Separate Process (design headroom)
The default topology runs the four stages as **threads** in one process, which is sufficient for the initial two-underlying config: the receiver/tee and DB writer are I/O-bound (they release the GIL on socket/disk waits), and the thin live processor (§3.4.1) is deliberately cheap. The one stage that is CPU-bound and GIL-contended is `TickProcessor`. As the number of configured `underlyings` grows toward the platform's 20+ simultaneous-symbol target, a single processor thread can become the bottleneck. The architecture is built so this scales **without reshaping the pipeline**:

*   **Queue boundary = process boundary.** `proc_queue` and `db_queue` are the only coupling between the processor and its neighbors, and they carry plain serializable dicts/tuples. Swapping `queue.Queue` for a `multiprocessing.Queue` (or a small ZeroMQ PUSH/PULL, which the platform already uses on port 5555) lets `TickProcessor` run as its **own OS process** with a real, uncontended core — no change to the receiver, file writer, DB writer, or the metric code itself.
*   **Shard by underlying.** Because all per-underlying state is keyed by `name` (the genericization contract, §7), the live processor can be **sharded**: one processor process per underlying (or per group of underlyings), each draining a partitioned `proc_queue` and writing its own rows. The tee simply routes a packet to the shard that owns its symbol. This is horizontal scaling with no shared mutable state to lock.
*   **The offline path already proves the pattern.** The end-of-session fat build (§3.6.5, §8.6) *already* runs the identical `TickProcessor` in a **separate reaped subprocess**. Promoting the live processor to a process reuses that same isolation discipline (file-based logs, `wait()`-reaping, no PIPE) — so the recorder's process model is uniform across live and offline.
*   **When NOT to.** Process isolation adds serialization cost across the queue boundary and more FDs to manage. It is **design headroom, not the default** — the config stays single-process until a deployment's underlying count and measured processor latency justify the switch (guarded by a future `processor.mode: thread|process` toggle rather than a rewrite).

This keeps the near-term implementation simple (threads) while guaranteeing the CPU-bound stage has a documented, low-friction path to multi-core scaling as the underlying count rises.

---

## 6. Recovery, Failover & Network Fault Tolerance

Since this service records data continuously throughout the day, it includes robust fault recovery mechanisms to handle network drops, database corruption, and thread lockups.

---

### 6.1 WebSocket Reconnection & Subscription Restoration Engine
The feed is backed by an automated state machine designed to detect connection drops and restore option subscriptions. Responsibilities split by transport:
*   **Liveness / handshake (transport-owned):** on the **SDK** transport (§3.3.1) the client owns the authenticate handshake and ping/pong liveness internally, surfacing a drop as a failed/`False` `connect()` or an error the FEED thread observes. On the **raw fallback** (§3.3.1a) the manager itself sends a ping every `heartbeat_interval_sec` and treats a missing pong within `heartbeat_timeout_sec` as a dead socket. Either way, a detected drop enters the recorder-owned reconnect state.
*   **Exponential Backoff Protocol (recorder-owned):** the FEED thread schedules reconnect attempts (a fresh `client.connect()` on the SDK path) using the same backoff on both transports:
    $$T_{\text{wait}} = \min(60, 1.5^{\text{attempts}} \cdot 2.0)\text{ seconds}$$
*   **Subscription State Recovery (recorder-owned):** when a reconnection is established, the manager bypasses the Dynamic Strike Manager (DSM) startup initialization. Instead, it reads the current list of option symbols directly from the thread-safe `self.active_subscriptions` cache and **re-issues `subscribe_depth`/`subscribe_ltp` for each** (raw path: a batch subscription frame). This restores all option chain feeds immediately without resetting boundaries or losing track of previously active strikes. Because resubscription lives in the recorder — not the transport — it works identically whether the SDK or the raw client is in use.

---

### 6.2 Timeline Continuity Guard & NaN Padding
To ensure downstream analytical strategies do not encounter time-series gaps, the resampling loop operates independently of the WebSocket state:
*   **Temporal Resampler Independence:** The resampling thread runs on a clock-aligned 1-second execution loop. It does not pause if the WebSocket is disconnected or if the OpenAlgo REST API is unreachable.
*   **Outage Detection:** If the gap since the last received tick for a symbol exceeds the staleness timeout (5.0 seconds), the processor flags the symbol as offline.
*   **NaN Padding Generation:** For every second the connection is offline, the resampler generates database rows for all active option contracts with:
    *   `ltp`, `spread`, `weighted_obi`, `book_pressure` set to `NULL` / `NaN`.
    *   `confidence` metric set to `0.0`.
*   **Downstream Benefits:** This padding maintains consistent time-series spacing in SQLite. Downstream models using pandas rolling window functions or lagging operations can run without encountering missing row dates.
*   **Rolling-window warm-up after (re)start (expected, documented):** the rolling deques (`time_windows_sec` = 5/10/30s) begin **empty** on every start — including a mid-day restart (§3.1.2). For the first ≤ largest-window seconds, `strike_window_metrics` columns (slopes, churn, velocity, acceleration, wall persistence) are partial and emitted as `NULL` until the deque fills. This is correct behaviour, not data loss; instantaneous `option_strike_metrics` are unaffected and available from the first tick.

---

### 6.3 SQLite Database Corruption Recovery Pipeline
During connection initialization, the database writer runs integrity checks to handle unclean host shutdowns (e.g., due to power loss):
1.  **Corruption Testing:** Runs PRAGMA verification commands on startup:
    ```sql
    PRAGMA integrity_check;
    PRAGMA quick_check;
    ```
2.  **Incident Handling:** If either check fails or if the connection throws a `sqlite3.DatabaseError`:
    *   *Close Connection:* Shuts down the database connection cleanly.
    *   *Archive File:* Renames the corrupt database file (along with its `.db-wal` and `.db-shm` files) by appending a timestamp:
        `data/market_depth_live_YYYYMMDD.db.corrupt_1781084100.bak`
    *   *Initialize Fresh Database:* Creates a new live database file at `data/market_depth_live_YYYYMMDD.db` and runs the DDL schema creation and indexing scripts. (Live-store corruption is non-fatal to the catalog: the fat analytical store is rebuilt from the untouched raw log at end-of-session regardless.)
    *   *Event Logging:* Emits a critical log event (via the standard logger, cross-platform — not OS `syslog`) alerting the administrator to the database recovery action.

---

### 6.4 Liveness Watchdog & OS-Agnostic Supervision
Health monitoring is layered so the same code runs on **Windows (this project's primary platform), Linux, and macOS**:
*   **Primary — in-process thread supervisor (cross-platform):** the orchestrator's own supervisor (§3.1.3) is the first line of defense — it checks `is_alive()` on every worker every few seconds and restarts the recording loop on a crash. This works identically on all OSes and needs no external daemon.
*   **Liveness File (cross-platform, config-driven path):** every `health_write_interval_sec` (default 10s) the orchestrator writes a JSON status payload to `recorder.health_file_path` — a **configurable path** (default `./data/health.json`), **not** a hardcoded `/tmp/...` (which does not exist on Windows). Written atomically (temp file + `os.replace`) so a reader never sees a partial file:
    ```json
    {
      "timestamp": 1781084100,
      "websocket_status": "connected",
      "raw_file_queue_size": 15,
      "proc_queue_size": 22,
      "db_queue_size": 40,
      "last_raw_tick_time": 1781084099,
      "active_contracts": 164,
      "raw_dropped_total": 0,
      "cycle_ms_p50": 3.1,
      "cycle_ms_max": 8.7,
      "rss_mb": 214.5
    }
    ```
    *   **Perf fields (P8):** `cycle_ms_p50` / `cycle_ms_max` are the processor's per-second `emit_second` timings (`perf_counter`, from `TickProcessor.stats()`; target **< 15 ms** thin) and `rss_mb` is the process resident set (`utils.process_rss_mb()`, stdlib platform-adaptive; target **< 500 MB**). The full runtime payload also carries `state`, `session_date`, `config_hash`, `proc_dropped_total`, `db_rows_dropped_total`, `degraded_level`, the per-underlying `actual_depth` map, and the writer/processor counters. `--status` pretty-prints these. The authoritative live confirmation of both perf targets is the P9 live-run (§8-adjacent runbook `Documents/LIVE_RUN.md`).
*   **Secondary — external OS supervisor (optional, platform-specific):** if an external watchdog is desired, it stales this file (default 25s):
    *   **Linux:** `systemd` unit with `WatchdogSec=`/`Restart=on-failure`, or a cron-launched guard.
    *   **Windows:** run under **NSSM** or a **Task Scheduler** task (with restart-on-failure) that reads `health.json`.
    *   **macOS:** a `launchd` agent with `KeepAlive`.
    The engine itself only *produces* the health file; the choice of supervisor is deployment config, keeping the recorder OS-agnostic.

---

## 7. Configuration Schema (`config.yaml`)

This section defines the structural configuration parameters stored within `config.yaml`. The schema is parsed on orchestrator startup using PyYAML, and the parameters are validated prior to initializing the background tasks.

### 7.1 Annotated YAML Configuration Template
```yaml
# OpenAlgo Connectivity Settings
openalgo:
  host_server: "http://127.0.0.1:5000"     # HTTP URL of OpenAlgo REST API server (used for master listings)
  websocket_url: "ws://127.0.0.1:8765"     # WebSocket Proxy URI for high-frequency feed connections
  api_key: "openalgo-apikey"               # Security API Key for REST headers and WS authentication payload

# Recorder Engine System Parameters
recorder:
  output_dir: "./data"                    # Relative/absolute directory path for SQLite and Gzip logs
  log_level: "INFO"                       # Console and file logger filter (DEBUG, INFO, WARNING, ERROR)
  resample_interval_sec: 1.0              # Uniform resample grid; NEVER varied at runtime (grid must stay uniform — §5.1/§6.2)
  staleness_timeout_sec: 5.0              # Inactivity before an option strike is padded with NaN/NULL rows
  session_start: "09:15"                  # IST — active recording begins (option subscriptions)
  session_end:   "15:30"                  # IST — subscription closure; teardown at session_end + teardown_grace
  teardown_grace_min: 5                   # Minutes after session_end to drain queues & flush (→ 15:35 shutdown)
  health_file_path: "./data/health.json"  # Cross-platform liveness file (NOT hardcoded /tmp — see §6.4). Windows-safe relative path
  health_write_interval_sec: 10           # Liveness heartbeat cadence
  min_free_disk_mb: 2048                  # Disk-space guard: ERROR below this free space on output_dir (§3.1.5)
  disk_check_interval_sec: 60             # Cadence of the periodic free-space check (§3.1.5)
  skip_non_trading_days: false            # If true, idle on weekends/holidays instead of idle-connecting (§3.1.5)
  trading_holidays: []                    # IST YYYY-MM-DD dates treated as non-trading when skip_non_trading_days=true
  # Thin/fat split (§3.4.1). The LIVE path computes only this subset → thin live store; the
  # full §4 catalog is (re)built offline by replay (§8). A metric name here maps to a metric ID
  # (M1..M24) or a named aggregate; "all" computes everything live (loses headroom). NEVER a
  # hardcoded list in code — the engine reads it from here.
  live_metrics: ["spread", "weighted_obi", "book_pressure", "best_bid_qty",
                 "best_ask_qty", "atm_aggregates", "regime"]   # or: all

# Metric computation constants (all previously hardcoded magic numbers — now config, per project rule)
metrics:
  decay_k: 0.2                            # Exponential decay for Weighted OBI: w_i = exp(-k*(i-1))
  effective_depth_pct: 0.005              # ±0.5% of mid price band for Effective Depth (M15)
  round_number_multiples: [5, 10]         # R values for Round-Number Depth (M18)
  book_pressure_levels: 10                # Top-N levels used by Book Pressure (M11)
  wall_sigma_mult: 3.0                    # Wall threshold: qty ≥ mean + wall_sigma_mult*std (§3.4.3-D)
  time_windows_sec: [5, 10, 30]           # Rolling deque windows for strike_window_metrics
  small_window_strikes: 2                 # SMALL = ATM ± this many strikes (§3.4.4)
  medium_window_divisor: 2                # MEDIUM = ATM ± floor(atm_max_strike_range / divisor) strikes

# Regime classification thresholds (§3.4.4-C) — referenced by the body but previously undefined
regime:
  theta_pressure: 5.0e6                   # NOP magnitude for Trending PE/CE
  theta_bias: 0.15                        # |B_net| for directional trend
  theta_pinning: 3.0                      # Pinning Score threshold for Pinning regime
  theta_spread: 0.02                      # Mean relative-spread threshold for Volatile regime
  quote_stability_min: 0.4                # Below this (with wide spreads) → Volatile

# Backpressure watermarks & queue sizing (§5.1)
queues:
  max_queue_size: 50000                   # Cap for proc_queue / db_queue (memory safety)
  raw_file_queue_max: 100000              # Audit queue is larger — sheds LAST (protected path)
  warn_watermark_pct: 70                  # Enter degraded processing (skip heavy rolling work)
  critical_watermark_pct: 90              # Shed oldest cached ticks for least-active symbols

# Gzip raw-audit writer (§3.5)
file_writer:
  gzip_compresslevel: 6                   # CPU/size tradeoff
  flush_max_records: 500                  # Cheap flush() cadence (buffer → OS)
  fsync_interval_sec: 2.0                 # Bounded durable fsync cadence (bounds crash-loss window — §3.5.3)

# Live SQLite writer — the THIN live store only (§3.6.1–§3.6.4).
database:
  batch_size: 500                         # Rows buffered before a transaction commit
  batch_write_interval_ms: 1000           # Max time before a commit (500 to 5000)
  cache_size_mb: 64                       # PRAGMA cache_size
  wal_checkpoint_interval_sec: 600        # PASSIVE checkpoint cadence (§4.4)

# DuckDB analytical writer — the FAT offline store only (§3.6.5). Used exclusively by the
# replay subprocess, never during live capture.
analytics_db:
  memory_limit_mb: 2048                   # DuckDB PRAGMA memory_limit for the bulk build (fits a full day comfortably)
  threads: 4                              # DuckDB worker threads for the bulk load/scan
  checkpoint_on_close: true               # Fold DuckDB's internal WAL into the .duckdb file before closing (§4.4)

# End-of-session fat-store build (§8, §8.6). The offline replay that turns the raw log into the
# full analytical catalog runs here — automatically after a clean teardown, with an OS-scheduled
# safety net for unclean shutdowns.
reprocess:
  auto_on_session_end: true               # Launch the fat build as a detached child process after teardown (Milestone 6)
  lock_file: "./data/reprocess.lock"      # Run lock so automatic + scheduled builds of the same day never overlap
  log_file: "./data/reprocess.log"        # Child stdout/stderr go HERE (a file, never a PIPE — FD-hygiene rule)
  catchup_on_start: true                  # On boot, --catchup any raw log lacking an up-to-date analytics DB (self-heal after downtime)
  full_metrics: true                      # Offline build computes the ENTIRE §4 catalog (ignores recorder.live_metrics)

# WebSocket lifecycle (§3.3.1 / §6.1)
websocket:
  transport: "raw"                        # "raw" (hand-rolled WS, DEFAULT/primary, §3.3.1a) | "sdk" (OpenAlgo Python SDK feed, alternate).
                                          # Raw is default: the SDK depth callback strips feed_time/depth_levels/is_50_depth (§3.3.1 verified finding). SDK is fine for LTP/spot.
  heartbeat_interval_sec: 10              # Ping cadence (raw transport only; SDK owns its own liveness)
  heartbeat_timeout_sec: 12               # No pong within this → reconnect (raw transport only)
  backoff_base: 1.5                       # T = min(backoff_max_sec, backoff_base^attempts * backoff_mult) — both transports
  backoff_mult: 2.0
  backoff_max_sec: 60

# Live processing topology (§5.2). Threads today; a documented path to per-underlying process
# sharding as the underlying count rises — NOT the default.
processor:
  mode: "thread"                          # "thread" (single-process, default) | "process" (TickProcessor in its own OS process)
  shards: 1                               # When mode=process: number of processor shards (partitioned by underlying `name`)

# Underlyings Subscription Configuration
#
# A LIST (not a hardcoded NIFTY/SENSEX map) so any weekly-option underlying can be
# added with no code change. Symbol/exchange/step are NEVER hardcoded in the engine —
# they are read from here (project rule: config over hardcoding). The engine treats
# every entry uniformly; NIFTY/SENSEX below are just the initial two entries.
underlyings:
  - name: "NIFTY"                          # Underlying base symbol (used for option symbol construction & filtering)
    spot_symbol: "NIFTY"                   # OpenAlgo spot symbol for the index LTP feed
    spot_exchange: "NSE_INDEX"             # OpenAlgo exchange for the index spot (indices → NSE_INDEX / BSE_INDEX)
    option_exchange: "NFO"                 # Exchange to filter option contracts and subscribe on
    requested_depth: 50                    # Depth level requested via the ":50" suffix; engine records the ACTUAL level the feed returns
    expected_strike_step: [50, 100]        # Accepted auto-detected strike steps; anything else warns and uses strike_step_fallback
    strike_step_fallback: 50               # Step to use if auto-detection yields an unexpected value
    initial_window: 1000                   # Points range centered on ATM spot to subscribe during boot (ATM +/- 1000)
    expansion_threshold: 200               # Distance from boundary before triggering DSM expansion
    expansion_step: 300                    # Shift range added to boundaries when a breach is verified
    atm_max_strike_range: 20               # Matrix radius for multi-strike aggregates (ATM +/- 20 strikes)
  - name: "SENSEX"
    spot_symbol: "SENSEX"
    spot_exchange: "BSE_INDEX"
    option_exchange: "BFO"                 # BSE F&O. NOTE: BFO is NOT FYERS-TBT-capable → feed returns 5-level depth (see §1, §3.2.5)
    requested_depth: 50                    # Still request 50; the proxy auto-falls-back to 5 for BFO — recorded as depth_levels=5
    expected_strike_step: [100, 200]
    strike_step_fallback: 100
    initial_window: 3000
    expansion_threshold: 600
    expansion_step: 500
    atm_max_strike_range: 30
```

> **Genericization contract.** No index name, exchange code, or strike step appears as a literal in engine
> code — all three are sourced from `underlyings[]`. Adding a third underlying (e.g. `BANKNIFTY`/`NFO`) is a
> pure config edit. The engine's per-underlying state (strike maps, boundaries, subscriptions, DB rows) is keyed
> by `name`, so the loops in §3.2–§3.4 iterate `underlyings` rather than branching on `NIFTY`/`SENSEX`.

---

### 7.2 Detailed Parameter Breakdown & Validation Constraints

| Section | Parameter Name | Data Type | Default Value | Validation Constraints | Operational Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **openalgo** | `host_server` | String | `"http://127.0.0.1:5000"` | Valid URL, HTTP/HTTPS prefix | Target REST endpoint for instrument lookup. |
| **openalgo** | `websocket_url` | String | `"ws://127.0.0.1:8765"` | Valid URL, WS/WSS prefix | Live feed connection address. |
| **openalgo** | `api_key` | String | N/A | Non-empty string | API authentication string. |
| **recorder** | `output_dir` | String | `"./data"` | Valid directory path | Path where data files are saved. |
| **recorder** | `log_level` | String | `"INFO"` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | Logger filter configuration. |
| **recorder** | `resample_interval_sec` | Float | `1.0` | `> 0`, fixed for the session | Uniform resample grid; never varied at runtime. |
| **recorder** | `staleness_timeout_sec` | Float | `5.0` | $1.0 \le \text{Value} \le 30.0$ | Time before an inactive strike is padded with NULL. |
| **recorder** | `session_start` / `session_end` | String `HH:MM` | `09:15` / `15:30` | Valid IST time, start `<` end | Active recording window (IST). |
| **recorder** | `teardown_grace_min` | Integer | `5` | $0 \le \text{Value} \le 30$ | Minutes after `session_end` to drain & flush. |
| **recorder** | `health_file_path` | String | `"./data/health.json"` | Writable path (cross-platform) | Liveness file; NOT hardcoded `/tmp` (§6.4). |
| **recorder** | `health_write_interval_sec` | Integer | `10` | $1 \le \text{Value} \le 60$ | Liveness heartbeat cadence. |
| **recorder** | `min_free_disk_mb` | Integer | `2048` | `≥ 0` | Disk-space guard ERROR threshold (§3.1.5). |
| **recorder** | `disk_check_interval_sec` | Integer | `60` | `≥ 5` | Periodic free-space check cadence (§3.1.5). |
| **recorder** | `skip_non_trading_days` | Boolean | `false` | `true`/`false` | Idle on weekends/holidays instead of connecting (§3.1.5). |
| **recorder** | `trading_holidays` | List[Str] | `[]` | `YYYY-MM-DD` IST strings | Non-trading dates when `skip_non_trading_days=true` (§3.1.5). |
| **recorder** | `live_metrics` | List[Str] or `"all"` | subset (see template) | Each entry a known metric ID/aggregate, or `"all"` | Metric subset computed on the LIVE path → thin store; full catalog is built offline (§3.4.1, §8). |
| **metrics** | `decay_k` | Float | `0.2` | `> 0` | Weighted-OBI exponential decay. |
| **metrics** | `effective_depth_pct` | Float | `0.005` | `0 < v < 1` | ±band around mid for Effective Depth (M15). |
| **metrics** | `round_number_multiples` | List[Int] | `[5, 10]` | Non-empty positive ints | R values for Round-Number Depth (M18). |
| **metrics** | `wall_sigma_mult` | Float | `3.0` | `> 0` | Wall = mean + k·std threshold. |
| **metrics** | `time_windows_sec` | List[Int] | `[5, 10, 30]` | Non-empty positive ints | Rolling windows for `strike_window_metrics`. |
| **metrics** | `small_window_strikes` / `medium_window_divisor` | Integer | `2` / `2` | Positive ints | SMALL/MEDIUM strike-window sizing (§3.4.4). |
| **regime** | `theta_pressure` / `theta_bias` / `theta_pinning` / `theta_spread` | Float | see template | Real; tuned per book | Regime classification thresholds (§3.4.4-C). |
| **regime** | `quote_stability_min` | Float | `0.4` | `0 ≤ v ≤ 1` | Volatile-regime stability floor. |
| **queues** | `max_queue_size` | Integer | `50000` | $1000 \le \text{Value} \le 200000$ | `proc_queue`/`db_queue` cap. |
| **queues** | `raw_file_queue_max` | Integer | `100000` | `≥ max_queue_size` | Audit queue cap (sheds last). |
| **queues** | `warn_watermark_pct` / `critical_watermark_pct` | Integer | `70` / `90` | `0 < warn < critical ≤ 100` | Degrade / shed thresholds (§5.1). |
| **file_writer** | `gzip_compresslevel` | Integer | `6` | `1 ≤ v ≤ 9` | Compression CPU/size tradeoff. |
| **file_writer** | `flush_max_records` | Integer | `500` | `≥ 1` | Cheap `flush()` cadence. |
| **file_writer** | `fsync_interval_sec` | Float | `2.0` | `> 0` | Bounded durable `fsync` cadence (§3.5.3). |
| **database** | `batch_size` | Integer | `500` | `≥ 1` | Rows per transaction. |
| **database** | `batch_write_interval_ms` | Integer | `1000` | $500 \le \text{Value} \le 5000$ | Max time before a commit. |
| **database** | `cache_size_mb` | Integer | `64` | `≥ 1` | PRAGMA cache_size. |
| **database** | `wal_checkpoint_interval_sec` | Integer | `600` | `≥ 30` | PASSIVE checkpoint cadence (live SQLite store only). |
| **analytics_db** | `memory_limit_mb` | Integer | `2048` | `≥ 256` | DuckDB `memory_limit` for the offline bulk build (§3.6.5). |
| **analytics_db** | `threads` | Integer | `4` | `1 ≤ v ≤ 64` | DuckDB worker threads for the bulk load/scan. |
| **analytics_db** | `checkpoint_on_close` | Boolean | `true` | `true`/`false` | `CHECKPOINT` the `.duckdb` before closing (§4.4). |
| **reprocess** | `auto_on_session_end` | Boolean | `true` | `true`/`false` | Launch the fat build as a detached child after teardown (§8.6 mode 1). |
| **reprocess** | `lock_file` | String | `"./data/reprocess.lock"` | Writable path | Run lock so automatic + scheduled builds never overlap. |
| **reprocess** | `log_file` | String | `"./data/reprocess.log"` | Writable path | Child stdout/stderr sink — a file, never a PIPE (FD hygiene). |
| **reprocess** | `catchup_on_start` | Boolean | `true` | `true`/`false` | On boot, rebuild any raw log lacking an up-to-date analytics DB (§8.6 mode 2). |
| **reprocess** | `full_metrics` | Boolean | `true` | `true`/`false` | Offline build computes the entire §4 catalog, ignoring `recorder.live_metrics`. |
| **websocket** | `transport` | String | `"raw"` | `"sdk"` or `"raw"` | Feed transport: hand-rolled raw WS (default/primary, §3.3.1a) or OpenAlgo SDK client (alternate). Raw is default because the SDK depth callback strips `feed_time`/`depth_levels`/`is_50_depth` (§3.3.1). |
| **websocket** | `heartbeat_interval_sec` / `heartbeat_timeout_sec` | Integer | `10` / `12` | `timeout > interval` | Ping/pong liveness (raw transport only; SDK owns its own). |
| **websocket** | `backoff_base` / `backoff_mult` / `backoff_max_sec` | Float/Int | `1.5` / `2.0` / `60` | `> 0` | Reconnect exponential backoff (both transports). |
| **processor** | `mode` | String | `"thread"` | `"thread"` or `"process"` | Live processing topology (§5.2); `process` isolates `TickProcessor` per OS process. |
| **processor** | `shards` | Integer | `1` | `≥ 1` (only used when `mode="process"`) | Number of per-underlying processor shards. |
| **underlyings[]** | `name` | String | N/A | Non-empty, unique | Underlying base symbol; keys all per-underlying engine state. |
| **underlyings[]** | `spot_symbol` | String | N/A | Non-empty string | OpenAlgo spot symbol for the index LTP feed. |
| **underlyings[]** | `spot_exchange` | String | N/A | Non-empty (e.g. `NSE_INDEX`, `BSE_INDEX`) | OpenAlgo exchange for the index spot. |
| **underlyings[]** | `option_exchange` | String | N/A | Non-empty (e.g. `NFO`, `BFO`) | Exchange used to filter option contracts and subscribe. |
| **underlyings[]** | `requested_depth` | Integer | `50` | One of `{5, 20, 30, 50}` | Depth requested via `":50"` suffix; actual level recorded may fall back (see §3.2.5). |
| **underlyings[]** | `expected_strike_step` | List[Int] | N/A | Non-empty list of positive ints | Accepted auto-detected strike steps. |
| **underlyings[]** | `strike_step_fallback` | Integer | N/A | Positive integer | Step used when detection yields an unexpected value. |
| **underlyings[]** | `initial_window` | Integer | N/A | Positive integer | Initial options subscription range around ATM spot. |
| **underlyings[]** | `expansion_threshold` | Integer | N/A | Positive integer, `< initial_window` | Spot distance to boundary that triggers expansion. |
| **underlyings[]** | `expansion_step` | Integer | N/A | Positive integer | The points increment added during expansions. |
| **underlyings[]** | `atm_max_strike_range` | Integer | N/A | Positive integer | Option chain radius used for aggregate metrics. |

---

### 7.3 Config Validation Rules
At startup, the orchestrator runs the following validation checks:
1.  **Format Verification:** Asserts that `config.yaml` is well-formed YAML.
2.  **I/O Verification:** Confirms write permissions for the configured `output_dir` by creating a temporary file and deleting it.
3.  **Boundary Checks:**
    *   **Per-underlying:** iterating every entry in `underlyings[]`, verifies that `expansion_threshold` is strictly less than `initial_window`:
        $$\text{expansion_threshold} < \text{initial_window}$$
    *   **Per-underlying uniqueness/completeness:** asserts each entry has a unique `name` and all required keys (`spot_symbol`, `spot_exchange`, `option_exchange`, `expected_strike_step`, `strike_step_fallback`) are present and non-empty, and that `strike_step_fallback` ∈ `expected_strike_step`.
    *   Verifies `database.batch_write_interval_ms` ∈ [500, 5000] to prevent disk bottlenecking or queue lag.
    *   **Analytical store:** `analytics_db.memory_limit_mb ≥ 256` and `1 ≤ analytics_db.threads ≤ 64`; validated at startup even though the DuckDB writer only runs in the replay subprocess, so a bad value fails fast rather than at end-of-session.
    *   **`live_metrics` membership:** every entry in `recorder.live_metrics` resolves to a known metric ID/aggregate (or the literal `"all"`); an unknown name aborts startup rather than silently producing an empty live column.
    *   **Enum fields:** `websocket.transport ∈ {"sdk","raw"}` and `processor.mode ∈ {"thread","process"}`; when `processor.mode == "process"`, `processor.shards ≥ 1`. An unknown value aborts startup (no silent fallback to a default transport/topology).
    *   **Watermark ordering:** `0 < queues.warn_watermark_pct < queues.critical_watermark_pct ≤ 100`, and `queues.raw_file_queue_max ≥ queues.max_queue_size` (audit queue must be able to outlast the analytics queue).
    *   **Session window:** `recorder.session_start < recorder.session_end` (parsed as IST `HH:MM`).
    *   **Non-empty lists:** `metrics.time_windows_sec`, `metrics.round_number_multiples`, and each underlying's `expected_strike_step` are non-empty lists of positive integers.
    *   **Session guards:** `recorder.min_free_disk_mb ≥ 0`, `recorder.disk_check_interval_sec ≥ 5`, `recorder.skip_non_trading_days ∈ {true,false}`; every entry in `recorder.trading_holidays` parses as an IST `YYYY-MM-DD` date (enforced only when `skip_non_trading_days=true`).
4.  **I/O portability check:** confirms `recorder.health_file_path`'s parent directory is writable (created if missing) — a relative/cross-platform path, never assuming a POSIX `/tmp`.
5.  **Fast-fail:** every magic constant used by the engine (decay, thresholds, windows, watermarks, cadences) must resolve from config; a missing/out-of-range value aborts startup with a critical validation report to stderr and **exit code 1** (no silent defaults baked into code — project rule).
6.  **Network Validation:** Verifies that both URL strings (`host_server` and `websocket_url`) conform to standard URI formats.

---

## 8. Replay & Reprocess Mode (Offline Regeneration)

The compressed raw log (`market_depth_raw_YYYYMMDD.jsonl.gz`) is the **source of truth** — it preserves 100% of the received feed. Both derived stores hang off it: the **thin live store** (Tier 1) is written in real time with the `recorder.live_metrics` subset, and the **fat analytical store** (Tier 2) is produced by **replaying the raw log through the same processor with the full metric set enabled**. Replay is therefore not an exceptional recovery tool — it is the *normal* production path for building Tier 2, and it runs automatically at end-of-session (§8.6). It also doubles as the reprocess mechanism when formulas, thresholds, window sizes, or the schema evolve. (This is the concrete design for the "Replay Engine" parked on the v2.1 post-migration roadmap; keep this section in sync with that item.)

### 8.1 Purpose & Guarantees
*   **Build the fat store (routine):** the end-of-session run replays the day's raw log into the full DuckDB analytical store (`market_depth_analytics_YYYYMMDD.duckdb`) — this is how Tier 2 exists in the first place, so the live path never has to compute the exhaustive catalog under market-hours pressure.
*   **Reprocess on formula change:** after tuning `metrics`/`regime` config or adding a metric column, rebuild the full historical analytical store for **any** past day from its raw log — no need to have computed the new metric live.
*   **Determinism / parity:** replay drives the **same** `TickProcessor` and metric functions as live recording — there is no second implementation to drift. The only substitution is the **clock source** (see §8.3) and the sink (`DuckDBAnalyticalWriter` bulk load instead of the live SQLite writer).
*   **Non-destructive:** an *ad-hoc* replay (formula experiments, diffs) writes to a **separate** file (e.g. `market_depth_YYYYMMDD.replay.duckdb`) via `--output`, never overwriting the day's analytics store unless explicitly asked, so two builds can be diffed (§8.4). The routine end-of-session build writes the canonical `market_depth_analytics_YYYYMMDD.duckdb`.

### 8.2 Invocation
```bash
# Regenerate one day's canonical analytical store from its raw log (routine end-of-session build)
python -m market_depth_recorder --replay ./data/market_depth_raw_20260703.jsonl.gz \
    --config config.yaml --output ./data/market_depth_analytics_20260703.duckdb

# Ad-hoc experiment: write to a side file so the canonical store is untouched
python -m market_depth_recorder --replay ./data/market_depth_raw_20260703.jsonl.gz \
    --config config.yaml --output ./data/market_depth_20260703.replay.duckdb --verify

# Self-heal: rebuild every raw log that lacks an up-to-date analytics store (§8.6 mode 2)
python -m market_depth_recorder --replay --catchup --config config.yaml

# Optional filters (combine with any of the above)
    [--underlying NIFTY]        # replay a subset
    [--from 09:20 --to 10:30]   # IST time slice
    [--verify]                  # replay then diff against a reference build (see §8.4)
```

Beyond replay, the same `python -m market_depth_recorder` entrypoint exposes **operational dry-run subcommands** (no live market required; each exits `0`/`1` for CI and ops):
```bash
python -m market_depth_recorder --validate-config --config config.yaml   # run all §7.3 checks, print report, exit 0/1
python -m market_depth_recorder --preflight      --config config.yaml    # run the §3.2.5 depth preflight, print actual depth per underlying, exit
python -m market_depth_recorder --status         --config config.yaml    # pretty-print the current health.json (§6.4) and exit
```

### 8.3 Simulated-Clock Resampler
The live resampler is wall-clock driven (§3.4.1). In replay, the 1-second grid is driven by the **packet timestamps** instead:
*   Each raw line carries the recorder-stamped **`recv_ts`** (plus the broker `feed_time` and proxy `timestamp`); replay advances a **virtual clock** from **`recv_ts`** — the exact basis the live resampler boundary AND staleness keyed off (the recorder clock at receive), so the rebuild emits the same 1-second buckets *and the same timestamps* as live capture did (verified P7 decision 66; `recv_ts` is preferred over `feed_time`/`timestamp` precisely because the live processor's `time_fn`/staleness used it, so it alone reproduces the live grid second-for-second and makes `--verify-against-live` meaningful).
*   The two writer threads that touch the network (`DepthWebSocketClient`) and its heartbeat/backoff are **disabled** — replay reads from a file iterator in place of the socket. The `RawTickFileWriter` is also disabled (raw already exists), and so is the thin live-store `SQLiteLiveWriter`. Only `TickProcessor` (with the **full** metric set enabled, not the `live_metrics` subset) + `DuckDBAnalyticalWriter` (§3.6.5) run, so the output is the fat Tier-2 DuckDB catalog.
*   Rolling-window warm-up (§6.2) is reproduced faithfully: the first ≤ largest-window seconds of replayed output are NULL, exactly as in the live run, so the analytical store and the live store are comparable second-for-second.
*   Because replay is CPU-bound only (no live pacing), it runs **much faster than real time** — a full session regenerates in minutes.

### 8.4 Verify Sub-Mode (drift detection)
`--verify` replays into a temp DuckDB file and **diffs it against a reference** for the same day: row counts per table, and a tolerance-based comparison of metric columns (`abs(a-b) <= atol`). Any mismatch is reported per (table, timestamp, symbol) — this catches accidental non-determinism (e.g. a metric that secretly depended on wall-clock or dict ordering) and is the recommended check after any change to `processor.py`. Before diffing, `--verify` first compares the two stores' `recorder_meta.schema_version`/`config_hash` (§4.1b) and aborts with a clear message on a schema-version mismatch, so a deliberate column-set change is never reported as metric drift. Two reference modes:
*   **Against a prior analytical build** (default): full column-for-column comparison of two DuckDB stores — the strict regression check.
*   **Against the thin live store** (`--verify-against-live`): comparison is **restricted to the `recorder.live_metrics` columns**, since the live store deliberately leaves the rest of the catalog `NULL` (§3.4.1). Comparing the full set there would flag those NULLs as false mismatches; scoping to the live subset confirms the live and offline paths agree on the metrics they both compute.

### 8.5 Idempotency & Rotation
Replay bulk-loads (§3.6.5) into a **fresh** DuckDB output file — there is no in-place upsert, so re-running replay on the same raw log is idempotent (the file is overwritten with identical content). Corrupt/truncated trailing lines in a raw log (e.g. from a hard crash before the EOF marker was written) are skipped with a counted warning rather than aborting the run. A partially written `.duckdb` from an interrupted build is discarded and rebuilt on the next run (the run lock and `--catchup` in §8.6 handle detection).

### 8.6 Trigger Modes (when the fat path runs)
Because the fat analytical store is *derived*, it does not need to be built while the market is live. There are three ways it gets built, in priority order:

1.  **Automatic — end-of-session (primary).** After a clean teardown (Milestone 5), the orchestrator launches the reprocess of *today's* raw log as a **separate child process** (Milestone 6), gated on `reprocess.auto_on_session_end: true`. It is a subprocess (not an in-process thread) so the exhaustive computation cannot delay the daemon's shutdown or hold its file descriptors, and it is started **detached with its stdout/stderr redirected to a log file (never a PIPE)** and later `wait()`-reaped, per the platform's FD-hygiene rule. Since the live session has ended, the machine is idle and the full catalog can be computed without contending with capture. A run lock (`reprocess.lock_file`) prevents two builds of the same day from overlapping.
2.  **Scheduled — OS-level fallback (safety net).** If the daemon crashed or was killed before a clean teardown (so Milestone 6 never fired), an OS scheduler entry runs `--replay` for any raw log that has **no matching `market_depth_analytics_*.duckdb`** (or one older than its raw log). This is a plain `--replay --catchup` invocation wired to Task Scheduler / NSSM on Windows or cron / systemd-timer on Linux (mirroring the supervision layer in §6.4), typically a few minutes after `recorder.session_end`. It is idempotent (§8.5), so a redundant run after a successful automatic build is a cheap no-op guarded by the same run lock.
3.  **On-demand — manual (formula changes & backtests).** An operator runs `--replay` directly (§8.2) to rebuild a specific day (or slice) after changing a metric formula, adding a column, or investigating a signal. Ad-hoc runs default to a `.replay.duckdb` `--output` so they never clobber the canonical analytics store, and pair naturally with `--verify` (§8.4) to diff against the previous build.

The `--catchup` helper (mode 2) scans `data/` for raw logs lacking an up-to-date analytics store and processes them oldest-first, so a machine that was offline for several days self-heals its Tier-2 history on the next scheduled tick without manual intervention.

---

## 9. Depth-Capability Preflight & Observability (Operational Scope)

Silent degradation from 50-level to 5-level depth (§1, §3.2.5) is the single most dangerous *quiet* failure for downstream models, so surfacing the **actual** capture state is a first-class operational requirement, not an afterthought:
*   **Startup summary:** after the §3.2.5 preflight, the orchestrator logs one consolidated INFO line per underlying — `underlying, option_exchange, requested_depth, actual_depth, per_level_orders_available` — and a WARNING for any underlying whose `actual_depth < requested_depth`. (`actual_depth`/`per_level_orders_available` are read from the raw packet's `depth_levels`/`is_50_depth`/`orders` fields, present on the default raw transport but stripped by the SDK — §3.3.1.)
*   **Self-describing rows:** every `option_strike_metrics` row carries `depth_levels`/`is_50_depth` (§4.1), so a query can filter or weight by capture quality without external metadata.
*   **Live visibility:** the health file (§6.4) includes `active_contracts` and `raw_dropped_total`; extend it with a per-underlying `actual_depth` map so a dashboard/watchdog can alarm if a feed that should be 50-level silently drops to 5 mid-session (e.g. TBT entitlement lapse).
*   **Per-level `orders` guard:** OCI (M14) and Average Order Size (M13) require a per-level `orders` count. The preflight records whether the feed populates it; if absent, those two metrics are emitted as `NULL` for that underlying rather than computed from a missing field (see §3.4.2). **This must be confirmed against a live FYERS TBT feed during implementation (verification step below).**