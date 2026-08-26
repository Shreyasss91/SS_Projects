# Graph Report - market_depth_recorder  (2026-08-26)

## Corpus Check
- 129 files · ~298,440 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3608 nodes · 6613 edges · 231 communities (205 shown, 26 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 668 edges (avg confidence: 0.7)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6c34a8ca`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_framework_capability_layer.py
- DuckDBAnalyticalWriter
- test_framework_config.py
- replay.py
- BookSnapshot
- SQLiteLiveWriter
- test_framework_window_manager.py
- RecorderOrchestrator
- FrameworkConfigError
- test_f7_depth_probe_harness.py
- market_depth_framework/__init__.py
- tbt_multiconn_probe.py
- test_replay.py
- test_framework_subscription_manager.py
- load_config
- Depth-transition probe — 5 <-> 50 behaviour on the OpenAlgo/FYERS path
- PremiumTier
- Instrument
- websocket_client.py
- allocator
- test_framework_subscription_state.py
- Config
- utils.py
- BrokerCapabilityLayer
- __main__.py
- Changelog — Market Depth Recorder
- test_framework_depth_allocator.py
- test_framework_priority_policy.py
- test_processor.py
- WindowManager
- test_websocket_client.py
- test_main.py
- Architecture — Market Depth Recorder
- Milestone
- SubscriptionPlan
- Common Pitfalls and Best Practices
- BudgetAllocator
- PriorityScore
- DepthAllocator
- processor.py
- RestError
- test_metrics_per_strike.py
- DepthWebSocketClient
- RawTickFileWriter
- RestClient
- Any
- InstrumentManager
- rolling.py
- TickProcessor
- numbers
- _depth_probe_model.py
- config.py
- test_eod_report.py
- test_framework_package.py
- leg
- test_framework_models.py
- market_depth_framework — module reference
- prompt_generic_market_depth_framework.md
- aggregate.py
- rank_candidates
- Plan_002 — Generic Market-Depth Framework — Implementation Plan
- _packet
- DepthEvidence
- executable_source
- test_integration.py
- _Session
- Summary: Generic Market-Depth Framework Documents (qwen/)
- test_metrics_rolling.py
- CLAUDE.md
- FUTURE_WORK.md
- test_framework_budget_allocator.py
- leg
- benchmark.py
- 3. Bugs found & fixed (the value of running live)
- MarketContext
- .candidates
- registry.py
- create_changes_patch.py
- Market Depth Recorder — Analytics Replay Performance Optimization
- `database_writer.py` — store writers (§3.6)
- Framework Implementation Plan
- 5. Budget Allocator & Depth Allocator
- `websocket_client.py` — Dynamic WebSocket Manager + DSM (§3.3, §6.1, §3.2.5/§9)
- ._maybe_rollover
- AtmDistancePolicy
- window_specs_from_underlyings
- module_tree
- depth_transition_probe.py
- compute_config_hash
- OpenAlgo Patch — FYERS TBT channel spread (P10-A)
- Generic Market-Depth Framework Architecture
- 3. Window Manager
- SymbolCodec
- Market Depth Recorder Microservice - Enhanced Design Specification
- `main.py` — Recorder Orchestrator (P6)
- Phase 9 — Live-Run Session Notes (2026-07-06)
- 4. Priority Policy
- executable_source
- test_metrics_aggregate.py
- Operator Notes — Market Depth Recorder
- 7.1 Technical Risks
- Success Metrics
- Phase 3: Budget Allocator, Depth Allocator & Subscription Manager
- 6. Subscription Manager
- .allocate_budget
- TagSymbolCodec
- decay_weights
- Plan 001 — Market Depth Recorder Implementation
- PROJECT_NOTES.md
- Confidence
- ProbeRequest
- `depth_transition_probe.py`
- StrikeHistory
- `file_writer.py` — Tier-0 gzip audit writer (§3.5)
- `instrument_manager.py` — Instrument & Expiry Manager (§3.2)
- Performance — Offline Analytics Replay Optimization
- Phase 2: Window Manager & Priority Policy
- Phase 5: Testing, Validation & Migration
- Phase 2: Window Manager & Priority Policy
- Phase 4: Broker Adapter & Integration
- `replay.py` — Offline replay + DuckDB rebuild (P7)
- duckdb_table_diff.py
- main
- P0 — Scaffolding, config, utils, registry skeleton
- Any
- `eod_report.py` — EOD health & sanity-check report (P10-C)
- 2. Broker Capabilities Layer
- 7. Broker Adapter
- 10. Component contracts
- _subscribe_ack
- DepthProbeResult
- ._on_message
- Offline Replay Optimization — Engineering Journal
- OpenAlgo issue — FYERS TBT `_run_websocket` retry-on-return storm
- `processor.py` — Metric Processor (P4a + P4b)
- Module: `metrics/registry.py`
- 22. Proposed phase sequence
- FakeClock
- FakeInstrumentManager
- build_evidence
- Module: `config.py`
- LIVE_RUN.md — P9 live-run session runbook
- `metrics/` — Metric registry, snapshot & compute bodies (P4a + P4b)
- comprehensive_implementation_guide_part2.md
- Appendix B: API Reference
- Phase 6: Production Readiness & Documentation
- Phase 1: Foundation & Broker Capabilities Layer
- Setup — Market Depth Recorder
- budget_allocator_for
- 3. Detailed Component Design
- Context
- _StubSession
- _FakeHandle
- executable_source
- HISTORY.md
- 8.1 Phase-Specific Success Criteria
- 1.3 Key Design Decisions
- .build_health
- 3.3 Dynamic WebSocket Manager (`websocket_client.py`)
- 3.4.2 Exhaustive Per-Strike Metric Computation
- 4. Database Schema Design (dual backend: live SQLite + analytical DuckDB)
- 8. Replay & Reprocess Mode (Offline Regeneration)
- 14. Depth-allocation and ranking semantics
- module_tree
- ranked_symbols
- _OkManager
- EOD Health & Sanity Report — 2026-07-07
- Validation Artifacts — Offline Replay Optimization
- integration.md — whole-pipeline harness + FD audit (P8)
- Phase 5: Testing, Validation & Migration
- .resolve_filename
- 3.1 Orchestrator & Schedule Daemon (`main.py`)
- 3.2 Instrument & Expiry Manager (`instrument_manager.py`)
- 3.4.3 Rolling Time Window Calculations
- 3.6 Store Writers (`database_writer.py`)
- P10 — Full-chain 50-level via OpenAlgo channel patch + dated storage + EOD health report
- P9 — Live-run session (runbook authored now, executed when market opens)
- TransitionOutcome
- `tools/` — maintained developer utilities
- 5. Every optimization — what, why, measured contribution
- Phase 3: Allocators & Subscription Manager
- Phase 6: Production Readiness & Documentation
- 8.2 Overall System Performance Metrics
- 10. Testing Strategy
- 12. Appendices
- 5.2 Depth Allocator
- Module: `utils.py`
- 1. System Overview & Objective
- 3.5 Gzip Flat File Writer (`file_writer.py`)
- 6. Recovery, Failover & Network Fault Tolerance
- P6 — Orchestrator (`main.py`)
- P4 — Processor thin/live (`processor.py`), split P4a / P4b
- P5 — SQLite live writer (`database_writer.py::SQLiteLiveWriter`)
- P8 — Offline Integration & Soak (automated, committed)
- 13. Budget-allocation semantics
- 20. Fork decisions — CLOSED (2026-08-25)
- test_preflight_reads_depth_and_warns_on_degradation
- Legacy pre-Phase-1b analytics reference (obsolete, retained for provenance)
- 11. Migration from FYERS-Specific Implementation
- 9. Failure Modes & Recovery
- .has_touch
- P2 — Tier-0 gzip file writer (`file_writer.py`)
- P7 — Replay + DuckDB writer (`replay.py`, `database_writer.py::DuckDBAnalyticalWriter`)
- 6. Locked decisions — Plan_002
- _never_construct
- chain
- Success Metrics
- dump_targets.py
- 2026-07-12 — Phase 1b: replay perf, NumPy→pure-Python (in progress, one hotspot per commit)
- Complete_Project_Plan_refer-market-depth-recorder-design-md-an-peppy-dolphin.md
- tests/__init__.py
- _load
- test_case_a_and_case_b_produce_different_wire_symbols_at_depth_50
- test_establishing_leg_always_uses_the_recorder_spelling
- test_harness_imports_no_recorder_or_framework_module
- test_framework_still_has_no_broker_adapter
- test_largest_remainder_hands_the_shortfall_to_the_biggest_fraction
- test_three_way_split_never_overshoots_through_rounding
- test_exact_integer_shares_are_not_lost_to_float_error
- test_the_floor_is_capped_by_the_candidate_count
- test_the_floor_is_never_applied_to_an_ineligible_underlying
- test_an_infeasible_floor_degrades_deterministically_and_never_raises
- test_redistribution_can_be_switched_off
- test_equal_weights_fall_back_to_the_name_tie_break
- test_a_missing_weight_for_an_eligible_underlying_is_a_wiring_error
- test_a_missing_weight_for_an_ineligible_underlying_is_fine
- test_worked_example_a_single_eligible_underlying_absorbs_the_budget
- test_worked_example_b_capped_underlying_frees_slots_to_the_other
- test_rank_equals_position_plus_one
- test_no_later_phase_module_exists_yet

## God Nodes (most connected - your core abstractions)
1. `Instrument` - 82 edges
2. `FrameworkConfigError` - 70 edges
3. `load_config()` - 65 edges
4. `write_config()` - 57 edges
5. `Config` - 54 edges
6. `RecorderOrchestrator` - 54 edges
7. `BookSnapshot` - 52 edges
8. `allocator()` - 52 edges
9. `ranked()` - 51 edges
10. `TickProcessor` - 46 edges

## Surprising Connections (you probably didn't know these)
- `PeakRSS` --uses--> `DuckDBAnalyticalWriter`  [INFERRED]
  Documents/archive/validation-artifacts/arrow_ab.py → database_writer.py
- `PeakRSS` --uses--> `InstrumentManager`  [INFERRED]
  Documents/archive/validation-artifacts/arrow_ab.py → instrument_manager.py
- `PeakRSS` --uses--> `TickProcessor`  [INFERRED]
  Documents/archive/validation-artifacts/arrow_ab.py → processor.py
- `run_backend()` --calls--> `DuckDBAnalyticalWriter`  [INFERRED]
  Documents/archive/validation-artifacts/arrow_ab.py → database_writer.py
- `run_backend()` --calls--> `TickProcessor`  [INFERRED]
  Documents/archive/validation-artifacts/arrow_ab.py → processor.py

## Import Cycles
- None detected.

## Communities (231 total, 26 thin omitted)

### Community 0 - "test_framework_capability_layer.py"
Cohesion: 0.04
Nodes (76): check_premium_floor_feasible(), eligible_underlyings(), The configured underlyings whose option exchange is premium-eligible (§13.1)., Startup feasibility check for ``budget_allocator.min_per_underlying`` (§13.2)., make_layer(), AST, F2 tests for the Broker Capabilities layer (Plan_002 §10.1, §13.1, §13.2, §16)., A guard on the *source*, not just the result: no expression anywhere in the pack (+68 more)

### Community 1 - "DuckDBAnalyticalWriter"
Cohesion: 0.06
Nodes (57): Connection, DuckDBAnalyticalWriter, Absolute path of the daily live DB for date ``d`` (§3.6.3). Reused by the orches, Offline fat-store writer (§3.6.5) — the P7 replay sink.      Runs **only** insid, Buffer one per-second row envelope (``{"table","rows"}``); unknown tables are co, Insert one buffered batch for ``table`` and clear it — **the single batching sea, Flush every table's trailing partial batch, stamp provenance, and ``CHECKPOINT``, Legacy path: one parameterized INSERT per row. Correct but pathologically slow f (+49 more)

### Community 2 - "test_framework_config.py"
Cohesion: 0.06
Nodes (68): CompletedProcess, dropped(), errors_of(), good_block(), good_root(), mutated(), Any, Path (+60 more)

### Community 3 - "replay.py"
Cohesion: 0.06
Nodes (44): main(), PeakRSS, A/B validation: executemany vs arrow finalize backend, full metric set on the fi, run_backend(), main(), PeakRSS, Arrow-backend validation on the ~100-minute representative dataset (2026-07-07 r, main() (+36 more)

### Community 4 - "BookSnapshot"
Cohesion: 0.08
Nodes (51): _anomaly_freshness(), _argmax(), _ask_stack_ratio(), _avg_order_size(), _best_bid_ask_qty(), _bid_stack_ratio(), _book_pressure(), _confidence() (+43 more)

### Community 5 - "SQLiteLiveWriter"
Cohesion: 0.06
Nodes (35): date, Event, Background consumer of ``db_queue`` that batch-commits per-second rows to the th, Flag the single overlap second after a mid-day restart so its commit uses INSERT, Open the current-date live DB: connect → integrity check (recover if corrupt) →, Fast corruption probe (§6.3). ``PRAGMA quick_check`` returns ``ok`` on a healthy, Archive a corrupt live DB (+ its ``-wal``/``-shm``) and reconnect to a fresh fil, High-performance WAL tuning (§3.6.2). ``cache_size`` is negative → KiB (MiB × 10 (+27 more)

### Community 6 - "test_framework_window_manager.py"
Cohesion: 0.04
Nodes (22): alpha_universe(), beta_universe(), chain(), F3 tests for the Window Manager (Plan_002 §10.2, §15, §22.4).  The Window Mana, Spot exactly midway: the LOWER strike wins. Plan_002 SS15, F3 Decision 2 -- a de, The tie rule must not depend on list order, dict order, or input ordering (F3 De, The recorder drops a non-positive or spiking spot rather than raising; so does t, Materialised once inside, so the second underlying does not see an exhausted ite (+14 more)

### Community 7 - "RecorderOrchestrator"
Cohesion: 0.07
Nodes (20): True once :meth:`resolve` has populated the lookup maps (the P6 orchestrator res, date, datetime, Constructs, supervises, and tears down the four-thread live pipeline (see module, Run one session end-to-end: (idle if a non-trading day) → resolve → build/superv, Request a graceful shutdown from another thread / signal handler (idempotent)., Trading-calendar guard (§3.1.5): if ``skip_non_trading_days`` and today (IST) is, Disk-space guard (§3.1.5): ERROR (non-blocking) when free space on ``output_dir` (+12 more)

### Community 8 - "FrameworkConfigError"
Cohesion: 0.08
Nodes (38): capability_layer_for(), Resolve the capability layer for one broker.      Raises:         FrameworkConfi, FrameworkConfigError, load_framework_config(), Any, Exception, Framework configuration schema and fail-fast validation (Plan_002 §17).  Mirro, Validate one ``broker_capabilities`` entry and build its typed capability. (+30 more)

### Community 10 - "market_depth_framework/__init__.py"
Cohesion: 0.07
Nodes (33): Budget Allocator: how one logical premium budget splits across underlyings (Plan, FrameworkConfig, Frozen, validated framework configuration.      ``broker_capabilities`` is typ, _check_budget(), depth_allocator_for(), depth_allocators_for(), DepthAllocation, DepthAllocationDiff (+25 more)

### Community 11 - "tbt_multiconn_probe.py"
Cohesion: 0.09
Nodes (35): main(), _parse_args(), _print_hint(), _print_report(), groups: list of (symbols, channel_value). channel_value type is honored verbatim, run_test(), load_token(), make_instrumented_cls() (+27 more)

### Community 12 - "test_replay.py"
Cohesion: 0.09
Nodes (39): _Cell, Public entry to feed one packet into the cache. The live thread uses the interna, The latest packet cached for one option symbol + its receive time (staleness bas, _build_live_store(), _depth(), _depth_pkt(), _drive(), _header() (+31 more)

### Community 13 - "test_framework_subscription_manager.py"
Cohesion: 0.11
Nodes (41): action_numbers(), executable_source(), leg(), module_source(), module_tree(), numbers(), prem_map(), Module (+33 more)

### Community 14 - "load_config"
Cohesion: 0.10
Nodes (39): ConfigError, load_config(), Exception, Raised when config validation fails. ``errors`` is the full ordered list of prob, Load + validate ``config.yaml`` at ``path``. Raises :class:`ConfigError` (with t, Return a helper that dumps a config dict to a YAML file under ``tmp_path`` and r, write_config(), _mutate() (+31 more)

### Community 15 - "Depth-transition probe — 5 <-> 50 behaviour on the OpenAlgo/FYERS path"
Cohesion: 0.05
Nodes (38): 10. Premium -> standard, 50 -> 5 — cases `C5_50_5_logical`, `C7_50_5_logical_unsub`, 11. Premium -> premium, 50 -> 50 — case `C4_50_50_logical`, 12. Unsubscribe, 13. Acknowledgement and per-leg feedback, 14. Reconnect, 15. Premium-capacity behaviour, 16. Observed facts, 17. Inferences (+30 more)

### Community 16 - "PremiumTier"
Cohesion: 0.08
Nodes (35): BrokerCapability, _check_positive_int(), PremiumTier, Broker-capability dataclasses (Plan_002 §10.1, §16, §17).  **F1 delivers the dat, Structural guard shared by the tiers. Booleans are rejected explicitly -- ``True, The always-available depth tier -- what the broker serves without a scarce-resou, The scarce deep-book tier and the connection facts that bound it.      Attribute, Everything one broker declares about the depth it can serve.      Attributes: (+27 more)

### Community 17 - "Instrument"
Cohesion: 0.08
Nodes (17): Every leg this pass considered, premium first, each in rank order., DepthType, Instrument, Enum, Which depth tier a leg is subscribed at.      A **tier**, not a level count. The, One option leg, identified independently of the depth it is streaming at (F10)., Reject a malformed leg at construction, so no partially-valid identity enters fr, PROCESSOR-owned, single-writer subscription state (§9, §20.4).      Holds the de (+9 more)

### Community 18 - "websocket_client.py"
Cohesion: 0.07
Nodes (24): FeedTransport, _log_preflight(), make_transport(), _orders_populated(), Any, Event, Protocol, Dynamic WebSocket Manager + DSM (spec §3.3, §6.1, §3.2.5/§9).  The first **net (+16 more)

### Community 19 - "allocator"
Cohesion: 0.08
Nodes (39): allocator(), ranked(), The steady state: repeated passes over an unchanged market must not move a singl, The budget is a hard broker limit; exceeding it is a refused subscription, not a, A ranking supplied in reverse order must select the same legs: position is not a, A wiring error: one allocator serves exactly one underlying (§10.5)., Gating it would leave the recorder unsubscribed for a full cooldown at startup., §14.3, fork F5. Gating a baseline add leaves a newly-relevant strike entirely un (+31 more)

### Community 20 - "test_framework_subscription_state.py"
Cohesion: 0.17
Nodes (37): leg(), numbers(), prem_map(), F6 tests for SubscriptionState and the plan/action value types (Plan_002 §9, §12, A synthetic leg whose symbol encodes its number, so failures name the leg., state(), std_map(), test_a_fresh_state_is_empty() (+29 more)

### Community 21 - "Config"
Cohesion: 0.11
Nodes (31): Config, Frozen, validated configuration object (§7.3 rule E8: typed, not a raw dict)., _build_insert(), Store writers (spec §3.6). Two writers, one logical schema (§4), different backe, ``INSERT OR <verb> INTO table (cols…) VALUES (?, …)`` — columns named for drift-, build_report(), Check, check_duckdb() (+23 more)

### Community 22 - "utils.py"
Cohesion: 0.08
Nodes (33): dt_time, _default_reprocess_launcher(), Recorder orchestrator — the conductor (spec §3.1, §6.4, §8.6).  P0–P5 built ever, Launch the reprocess child with stdout+stderr → a real log file (never a PIPE —, Read + pretty-print the health file for ``--status``. Returns ``(exit_code, text, read_status(), test_read_status_missing_file(), utils.py primitive tests (§2.1 utils): decay weights, IST parsing, atomic write, (+25 more)

### Community 23 - "BrokerCapabilityLayer"
Cohesion: 0.07
Nodes (23): BrokerCapabilityLayer, build_capability_layers(), _check_broker_name(), _check_exchange(), Broker Capabilities layer (Plan_002 §10.1, §13.1, §13.2, §16) -- phase F2.  This, Exchanges on which this broker serves the premium tier. Frozen, so it cannot dri, The one logical premium-symbol budget the framework consumes.          ``min(tot, Whether the broker declares an account-wide cap beyond its connection math. (+15 more)

### Community 24 - "__main__.py"
Cohesion: 0.10
Nodes (34): build_parser(), _cmd_eod_report(), _cmd_preflight(), _cmd_replay(), _cmd_run(), _cmd_status(), _cmd_validate_config(), _guard_args() (+26 more)

### Community 25 - "Changelog — Market Depth Recorder"
Cohesion: 0.06
Nodes (34): 2026-07-03 — P0: Scaffolding, config, utils, registry skeleton, 2026-07-03 — P1: InstrumentManager (`instrument_manager.py`), 2026-07-03 — P2: Tier-0 gzip file writer (`file_writer.py`), 2026-07-03 — P3: WebSocket client + DSM (`websocket_client.py`), 2026-07-03 — P4a: Processor engine + per-strike metrics (`processor.py`, `metrics/`), 2026-07-04 — P4b: Rolling windows + aggregates + regime (`metrics/rolling.py`, `metrics/aggregate.py`), 2026-07-04 — P5: SQLite live writer (`database_writer.py::SQLiteLiveWriter`), 2026-07-05 — P6: Orchestrator (`main.py::RecorderOrchestrator`) (+26 more)

### Community 26 - "test_framework_depth_allocator.py"
Cohesion: 0.10
Nodes (31): _cfg(), executable_source(), FakeClock, module_source(), module_tree(), Module, F5 tests for the Depth Allocator (Plan_002 §10.5, §14, §20.3, §22.6).  The Depth, §10.5: a shared instance would let one underlying's reallocation reset another's (+23 more)

### Community 27 - "test_framework_priority_policy.py"
Cohesion: 0.07
Nodes (11): module_source(), module_tree(), AST, F4 tests for the Priority Policy (Plan_002 §10.3, §14.2, §14.6, §22.5).  The P, F5 must receive what F3 produced, not a re-derived lookup that could drift., A field carried unused is a field nobody has decided the semantics of., test_module_imports_no_capability_layer_and_no_recorder(), test_module_imports_no_runtime_or_io_machinery() (+3 more)

### Community 28 - "test_processor.py"
Cohesion: 0.19
Nodes (30): agg_row(), depth_packet(), envelopes_by_table(), FakeIM, feed(), make_proc(), TickProcessor engine (spec §3.4.1, §5.1, §6.2) — ingest/classify, resample emit,, Minimal stand-in for the resolved InstrumentManager (only the maps the processor (+22 more)

### Community 29 - "WindowManager"
Cohesion: 0.08
Nodes (30): FixedExpiryCalendar, An :class:`ExpiryCalendar` over an already-resolved underlying-to-expiry mapping, One underlying's candidate window, resolved from ``underlyings[]`` (§17)., Resolves the candidate universe per underlying (§10.2, §15).      Immutable an, Configured underlying names, in configured order -- never mapping-iteration orde, WindowManager, WindowSpec, manager() (+22 more)

### Community 30 - "test_websocket_client.py"
Cohesion: 0.16
Nodes (28): _client(), FakeTransport, _md(), _ramp(), DepthWebSocketClient + DSM + tee + reconnect + live depth preflight tests (spec, Feed a gradual spot ramp so no single tick exceeds the 2% spike guard (§3.3.2)., No-socket transport: records sent frames, lets the test fire on_open / deliver m, test_actual_depth_falls_back_to_populated_levels_when_field_absent() (+20 more)

### Community 31 - "test_main.py"
Cohesion: 0.21
Nodes (27): Clock, FakeIM, FakeRest, _fast_supervise(), ist_epoch(), make_factory(), _orch(), RecorderOrchestrator tests (spec §3.1 / §6.4 / §8.6). All run offline.  A virtua (+19 more)

### Community 32 - "Architecture — Market Depth Recorder"
Cohesion: 0.06
Nodes (30): Architecture — Market Depth Recorder, `budget_allocator.py` — one logical budget split across underlyings (§10.4, §13), Built state (F1) — market_depth_framework, contracts only, Built state (F2) — Broker Capabilities layer, Built state (F3) — Window Manager, Built state (F4) — Priority Policy, Built state (F5) — Budget Allocator + Depth Allocator, Built state (F6) — Subscription layer (state + pure reconciliation) (+22 more)

### Community 33 - "Milestone"
Cohesion: 0.09
Nodes (13): Milestone, The §3.1.1 milestone the orchestrator is currently in (surfaced as health ``stat, str, FakeDbWriter, FakeFeed, FakeProcessor, FakeRawWriter, FakeWorker (+5 more)

### Community 34 - "SubscriptionPlan"
Cohesion: 0.11
Nodes (22): _action_sort_key(), Pure desired/current subscription reconciliation (Plan_002 §10.6, §14.4).  This, Stateless reconciler from desired/current depth maps to a :class:`SubscriptionPl, Reconcile a desired leg -> depth map against a live one, purely (§10.6, §14.4)., SubscriptionManager, ActionKind, Enum, Subscription state and the reconciliation vocabulary (Plan_002 §9, §12, §20.4). (+14 more)

### Community 35 - "Common Pitfalls and Best Practices"
Cohesion: 0.07
Nodes (28): 1.1 Project Structure Creation (Days 1-2), 1.2 Data Models Implementation (Days 3-5), 2.1 Broker Capabilities Interface (Days 1-3), Best Practice: Fast-Fail on Configuration, Never Default Silently, Best Practice: Provide Meaningful Error Messages, Best Practice: Use Type Hints Everywhere, Capability Models (`capabilities/models.py`), Code: Exception Hierarchy (`core/exceptions.py`) (+20 more)

### Community 36 - "BudgetAllocator"
Cohesion: 0.07
Nodes (23): BudgetAllocator, Floor per **premium-eligible** underlying (§13.2). Never applied to an ineligibl, Configured relative weights, read-only. Empty means unweighted (§17)., Whether slots freed by a candidate cap are handed on (§13.3, fork F6)., Split one premium budget across underlyings (§10.4).      Immutable and stateles, Without the floor, a 1.0-weighted underlying against a 20.0-weighted one would r, Budget beyond every candidate in existence must exit the loop, not spin., Iteration order of a dict must never reach the result, or a replay could disagre (+15 more)

### Community 37 - "PriorityScore"
Cohesion: 0.11
Nodes (25): PriorityScore, Convenience passthrough -- the tie-break key of the total order, read often., One candidate's score and its **1-based** rank (§14.2).      ``rank`` is the o, leg(), A leg alternating between rank 3 and rank 4 around a budget of 3 must not flip t, The control case: buffer 0 flaps, which is what the buffer exists to prevent., A caller may pass a subset of a ranking; rank values, not their density, decide., Exercised on both sides so an off-by-one in the comparison cannot pass. (+17 more)

### Community 38 - "DepthAllocator"
Cohesion: 0.10
Nodes (13): DepthAllocator, Choose the premium overlay for **one** underlying (§10.5, §14).      Construct o, The current premium overlay, in the rank order of the pass that set it., False until the first pass runs -- the flag that keeps the first pass out of the, The bounded debug ring, oldest first., Choose this underlying's premium overlay for one pass (§14.1, §14.3, §14.4)., The §14.1 selection: the ``budget`` lowest effective ranks, challenger-first on, One candidate's effective rank under §14.1.          The band limit depends on ` (+5 more)

### Community 39 - "processor.py"
Cohesion: 0.12
Nodes (20): liquidity_delta_instant(), ofi_instant(), Best-level Order Flow Imbalance for one second (Cont–Kukanov–Stoikov, §3.4.3-E)., Price-aligned ΔQ+ / ΔQ- vs the prior second across the top-N price union, both s, Per-second option-book snapshot + metric context (spec §3.4.2, plan decision 35), One second of a single strike's rolling inputs (spec §3.4.3). ``None`` fields ma, Per-strike aggregate inputs for one second (spec §3.4.4). Pooled by the multi-st, Compact prior-second book kept for price-aligned ΔQ (§3.4.3-B) and touch OFI (§3 (+12 more)

### Community 40 - "RestError"
Cohesion: 0.12
Nodes (19): One entry of ``underlyings[]`` (§7.1). Typed so the engine iterates a list of ob, Underlying, _extract_data_obj(), _parse_expiry(), date, Exception, Instrument & Expiry Manager (spec §3.2).  Runs once at startup: query the Open, `POST /api/v1/quotes/` ``{apikey, symbol, exchange}`` → ``data.ltp`` (float). (+11 more)

### Community 41 - "test_metrics_per_strike.py"
Cohesion: 0.21
Nodes (24): call(), deep(), make_ctx(), make_snap(), Per-strike metric bodies M1-M29 (spec §3.4.2) — hand-computed fixtures + guard c, small(), test_best_bid_ask_qty(), test_confidence_range_and_freshness() (+16 more)

### Community 42 - "DepthWebSocketClient"
Cohesion: 0.13
Nodes (10): DepthWebSocketClient, Feed lifecycle + DSM + tee + reconnect. Transport-agnostic; the transport is inj, Seed/advance the DSM from an out-of-band spot price (the P6 mid-day REST quote,, Stop DSM boundary expansion at ``session_end`` (§3.1.1 Milestone 4). Never-shrin, Authenticate, (re)subscribe spots, and restore every option subscription (never-, Validate a spot tick, seed or advance boundaries, and return the new strikes to, Expand boundaries on a breach and collect the newly covered strikes (§3.3.2). Ca, Map strikes → CE/PE wire symbols, diff against the never-shrink set, add + subsc (+2 more)

### Community 43 - "RawTickFileWriter"
Cohesion: 0.18
Nodes (19): Background consumer of ``raw_file_queue`` that appends each packet to the daily, RawTickFileWriter, Clock, _epoch_for(), RawTickFileWriter (Tier-0 gzip audit log) tests — spec §3.5. All run offline (no, Deterministic injected clock (epoch seconds) — drives timestamps, fsync cadence,, Parse every JSONL record from a complete gzip log (stdlib only — no pandas depen, Parse records from a possibly-torn gzip log, stopping cleanly at the first damag (+11 more)

### Community 44 - "RestClient"
Cohesion: 0.15
Nodes (19): HTTPError, Thin OpenAlgo REST wrapper over ``urllib`` — instruments (GET) + expiry (POST)., RestClient, OpenerDirector, _envelope(), _http_error(), _quote_envelope(), Yields queued actions on each ``open`` call: bytes → a response body; an Excepti (+11 more)

### Community 45 - "Any"
Cohesion: 0.10
Nodes (16): _extract_data_list(), _norm_strike(), _option_type(), Any, Issue one HTTP request with retries; return the parsed JSON payload or raise ``R, Validate the standard OpenAlgo envelope ``{"status":"success","data":[…]}`` → th, Serialize the resolved chain for the raw-log HEADER so replay is **self-containe, One dict per resolved underlying for the ``--preflight`` summary (offline; ``act (+8 more)

### Community 46 - "InstrumentManager"
Cohesion: 0.20
Nodes (19): InstrumentManager, Resolves every configured underlying's weekly chain and exposes the O(1) lookup, _bfo_rows(), _fake_rest(), FakeRest, _nfo_rows(), InstrumentManager + RestClient tests (spec §3.2). All run without a live feed /, Injectable RestClient replacement returning canned instruments/expiry dicts, no (+11 more)

### Community 47 - "rolling.py"
Cohesion: 0.16
Nodes (21): _book_churn(), _flow_intensity(), _lastn(), _liquidity_flow(), _mean_std_minmax(), _micro_price_rv(), _ofi_sum(), _pressure_acceleration() (+13 more)

### Community 48 - "TickProcessor"
Cohesion: 0.14
Nodes (8): Single-owner resample/compute thread (§3.4.1). See module docstring for ownershi, Emit one second's rows for every tracked symbol. Pure w.r.t. the injected clock, Compute the per-strike scalars the rolling + aggregate metrics need (always, whe, Dominant wall size (max resting qty, for pinning) + its price when it qualifies, The strike step for an underlying, derived from the resolved chain's sorted stri, Critical-pressure relief: evict already-stale cached ticks for the least-active, Nearest-rank percentile of the recent per-second cycle times (ms); 0.0 before an, TickProcessor

### Community 49 - "numbers"
Cohesion: 0.11
Nodes (23): numbers(), Make exactly these ranks the incumbent premium set via a first, ungated pass., budget 3, buffer 2, incumbent rank 4 -> effective 2, challenger rank 3 -> effect, budget 3, buffer 2, incumbent rank 5 -> effective 3, challenger rank 3 -> effect, budget 3, buffer 2, incumbent rank 6 -> 6 > 3 + 2, so it competes at its true ra, buffer 0 collapses the band and the subtraction, so selection is the plain top b, The anti-lockout property. Even with every nearby rank incumbent, the rank-1 leg, The §14.1 argument generalised: while buffer <= budget, no incumbent configurati (+15 more)

### Community 50 - "_depth_probe_model.py"
Cohesion: 0.14
Nodes (19): build_subscribe_request(), build_unsubscribe_request(), Mechanism, Operation, probe_request_id(), probe_wire_symbol(), Enum, Spell ``symbol`` for a ``depth`` request in the requested ``form``.      ``LOG (+11 more)

### Community 51 - "config.py"
Cohesion: 0.20
Nodes (14): _build(), _check_url(), Any, Config loader + validation for the Market Depth Recorder (spec §7.1–§7.3).  ``, Accumulates validation errors instead of raising on the first — the operator get, Fetch a numeric value; records an error and returns None if absent or non-numeri, Run every §7.3 rule against ``raw``, returning the full error list (empty == val, Assemble the frozen Config from an already-validated dict. (+6 more)

### Community 52 - "test_eod_report.py"
Cohesion: 0.21
Nodes (17): _depth_pkt(), _make_live_db(), P10-C — EOD health & sanity-check report.  Exercises the per-tier check function, _status(), test_duckdb_populated_meta(), test_live_db_clean(), test_live_db_nifty_missing_fails(), test_ops_clean() (+9 more)

### Community 53 - "test_framework_package.py"
Cohesion: 0.12
Nodes (20): AST, Path, F1 tests for the package skeleton's inertness and scope boundaries (Plan_002 §22, A subprocess import with a fresh interpreter: no socket, file, or DB handle is c, Genericization contract: no index name, exchange code, or strike step as a liter, Return the tree with every module/class/function docstring removed., The recorder must not gain a framework dependency in F1., Exact equality, not a subset: an accidental export fails as loudly as a missing (+12 more)

### Community 54 - "leg"
Cohesion: 0.10
Nodes (21): rank_scores(), Assign **1-based** ranks over ``(instrument, score)`` pairs (§10.3, §14.2)., leg(), A strike one step above ATM and one step below score identically; only symbol se, The 1-based basis is enforced by the type, not merely produced by the ranker., Ordering must come from the symbol, not from an unstated side preference., Two rows for one leg cannot be separated by the tie-break, so the caller is told, A wiring error, not a quiet skip: an empty or partial ranking would hide it. (+13 more)

### Community 55 - "test_framework_models.py"
Cohesion: 0.14
Nodes (19): make_instrument(), F1 tests for the framework data models (Plan_002 §9, fork F10).  The load-bearin, The instrument master reports fractional strikes (e.g. VEDL...292.5CE)., A valid leg; tests override one field at a time so a failure names the field it, The tier must not carry a number: 50 is a FYERS/NFO fact, and a broker whose pre, Fork F10, stated directly: depth is a value elsewhere, never part of leg identit, Plan_002 §9 keys four sets by Instrument; that requires hashability., The point of F10. Depth lives in the value, so promoting a leg does not create a (+11 more)

### Community 56 - "market_depth_framework — module reference"
Cohesion: 0.10
Nodes (19): `budget_allocator.py` — the inter-underlying premium split (Plan_002 §10.4, §13), `capabilities.py` — broker-declared facts (Plan_002 §10.1, §16), `capability_layer.py` — the Broker Capabilities layer (Plan_002 §10.1, §13.1, §13.2, §16), `config.example.yaml` — the FYERS capability configuration (§16), Config keys consumed, `config.py` — schema and fail-fast validation (Plan_002 §17), `depth_allocator.py` — the premium overlay within one underlying (Plan_002 §10.5, §14), Fail-fast / exit-1 contract (+11 more)

### Community 57 - "prompt_generic_market_depth_framework.md"
Cohesion: 0.10
Nodes (19): Broker Adapter, Depth Allocator, Design Expectations, Overall Architecture, Overall Build Order, Overall Design Philosophy, Phase 1 — Broker Capabilities, Phase 2 — Window Manager (+11 more)

### Community 58 - "aggregate.py"
Cohesion: 0.14
Nodes (15): _bnet(), compute_underlying(), _consolidated_pressures(), _in_window(), _mean_attr(), _net_options_pressure(), _pooled_obi(), Multi-strike aggregate + regime bodies (spec §3.4.4), bound to their registry sp (+7 more)

### Community 59 - "rank_candidates"
Cohesion: 0.15
Nodes (18): market_context_from_window(), rank_candidates(), Build the frozen per-pass context from a resolved :class:`~.window_manager.Windo, Rank each underlying's candidates independently, keyed by underlying.      Ran, Ranking across underlyings would presuppose a shared pool -- that split is F5's, §15 states the ATM rule once; F4 must read it, not restate it., test_a_duplicate_window_result_raises(), test_an_unresolved_window_ranks_to_an_empty_tuple() (+10 more)

### Community 60 - "Plan_002 — Generic Market-Depth Framework — Implementation Plan"
Cohesion: 0.11
Nodes (18): 11. Data flow — one rebalance pass, 12. Reconciliation semantics, 15. Window Manager semantics, 16. Broker capability + adapter contract, 17. Configuration surface (draft), 18. Testing architecture, 19. Integration with the existing recorder, 1. Document control (+10 more)

### Community 61 - "_packet"
Cohesion: 0.15
Nodes (19): _packet(), A snapshot then thin incrementals must not read as a shallower book., A market-data packet carrying ``levels`` book entries on one side.      This i, The end-to-end version of the anti-fabrication guarantee., If the depth does not move, the harness must say so rather than trust the ack., Packets arriving under both spellings after the transition mean two live subscri, End-to-end on the verified wire shapes: nested ack plus the ``data``-enveloped p, _run() (+11 more)

### Community 62 - "DepthEvidence"
Cohesion: 0.11
Nodes (16): PART M's explicit requirement: acceptance alone cannot mark a result verified., The outcome the harness must be equally willing to record., test_accepted_request_never_becomes_a_depth_claim(), test_acknowledgement_alone_is_inferred_never_observed(), test_depth_evidence_rejects_nonsense_inputs(), test_fully_observed_change_is_reported_as_changed(), test_fully_observed_non_change_is_reported_as_unchanged(), test_half_observed_transition_is_unknown_in_both_directions() (+8 more)

### Community 63 - "executable_source"
Cohesion: 0.11
Nodes (19): executable_source(), module_source(), module_tree(), Module, The module with every docstring stripped: prose may cite a later phase, code may, effective_budget arrives as an integer; nothing here reconstructs it from connec, F7 owns broker execution and any transition mechanics; F6 must not name them., The clock is injected and has no default: a wall-clock read would make replay de (+11 more)

### Community 64 - "test_integration.py"
Cohesion: 0.15
Nodes (13): _chain_block(), _depth_msg(), _header_instruments(), P8 — whole-pipeline integration & soak harness (the real four-thread pipeline en, ~2.5 s of feed across three 1-second buckets (a prior second exists for rolling, Plays a list of ``(delay_sec, market_data_msg)`` through the real feed callbacks, A ``market_data`` depth envelope with per-level ``orders`` populated (M13/M14 co, RecordedTransport (+5 more)

### Community 65 - "_Session"
Cohesion: 0.19
Nodes (12): ProbeResult, What came back for one :class:`ProbeRequest`, and what it is worth as evidence., Whether the *request* was accepted. Says nothing about delivered depth., _cleanup(), main(), One synchronous WebSocket conversation with the OpenAlgo proxy.      Deliberat, Read frames until ``predicate`` matches or the window expires. Non-matches are k, Collect every frame arriving in a bounded window, plus anything already buffered (+4 more)

### Community 66 - "Summary: Generic Market-Depth Framework Documents (qwen/)"
Cohesion: 0.11
Nodes (17): 0. Locked decisions (2026-08-05), 1. What this document set is, 2. Core design philosophy (from the prompt), 3.1 Broker Capabilities Layer (Phase 1), 3.2 Window Manager (Phase 2), 3.3 Priority Policy (Phase 3), 3.4 Budget Allocator + Depth Allocator (Phase 4), 3.5 Subscription Manager (Phase 5) (+9 more)

### Community 67 - "test_metrics_rolling.py"
Cohesion: 0.27
Nodes (17): call(), ctx(), Rolling-window metric bodies (spec §3.4.3) — hand-computed fixtures + the instan, Build a list of WindowSample from parallel keyword series (all same length)., samples(), test_liquidity_flow_churn_intensity(), test_micro_price_rv_skips_invalid(), test_ofi_sum_and_boundary_skip() (+9 more)

### Community 68 - "CLAUDE.md"
Cohesion: 0.12
Nodes (15): Before Proposing Code, Concurrency — High Risk, Config over Hardcoding — Genericization Contract, Data Integrity (the recorder's "trading safety"), Depth Reality, Documentation (maintained from day one), FD Hygiene, graphify (+7 more)

### Community 69 - "FUTURE_WORK.md"
Cohesion: 0.12
Nodes (16): 1. DuckDB-side `verify()` rewrite, 2. Relative tolerance verification (`atol + rtol`), 3. Phase 2 — Parallel replay, 4. Incremental real-time rolling engine, 5. Benchmark & validation framework improvements, 6. Future storage / backend ideas, 7. Engineering tooling, Future Ideas / Parking Lot (+8 more)

### Community 70 - "test_framework_budget_allocator.py"
Cohesion: 0.20
Nodes (15): allocator(), F5 tests for the Budget Allocator (Plan_002 §10.4, §13, §22.6).  The Budget Al, If total capacity meets the budget, nothing may be left on the table -- an unspe, 0 is a valid answer; a missing key is not. The caller must be able to tell 'allo, test_a_malformed_budget_is_refused(), test_a_malformed_candidate_count_is_refused(), test_a_non_mapping_candidate_count_is_refused(), test_a_single_eligible_underlying_absorbs_up_to_its_capacity() (+7 more)

### Community 71 - "leg"
Cohesion: 0.13
Nodes (17): call_legs(), leg(), put_legs(), Asserted independently of the call side, not inferred from it., Both sides are not assumed present: the layer reports what the master supplies., The genericization claim, exercised: different tags, same window logic, no code, One strike, one side. Not an error -- a thin chain is a real early-session state, test_a_call_only_universe_yields_only_calls() (+9 more)

### Community 72 - "benchmark.py"
Cohesion: 0.19
Nodes (11): BenchSample, _cpu_seconds(), _format(), main(), Replay benchmark harness (dev/measurement tool — NOT part of the runtime pipelin, Total CPU seconds (user+system) for the process + all children, or None if psuti, Replay ``raw_path`` once under measurement and return a :class:`BenchSample`., One benchmark run's structured result (serialized to the JSON ledger). (+3 more)

### Community 73 - "3. Bugs found & fixed (the value of running live)"
Cohesion: 0.12
Nodes (15): 1. Purpose & setup, 2. Checklist results (E1–E9), 3. Bugs found & fixed (the value of running live), 4. E4 perf & E8 verify — the two nuanced findings, 5. Files touched, 6. Residual / follow-ups, Bug 1 — `theta_pressure` YAML exponent trap (processor crash-loop), Bug 2 — `crossed/zero market` logged at CRITICAL (hot-path flood) (+7 more)

### Community 74 - "MarketContext"
Cohesion: 0.12
Nodes (14): MarketContext, Score and rank ``candidates`` against ``ctx``., A frozen snapshot of one underlying's market state for one rebalance pass (§10.3, alpha_ctx(), Distance is measured from ATM, not from spot -- the ATM the Window Manager alrea, A 100-point grid ranks exactly like a 50-point one: no step constant is involved, test_a_blank_context_underlying_is_rejected(), test_a_bool_spot_is_rejected() (+6 more)

### Community 75 - ".candidates"
Cohesion: 0.13
Nodes (9): _atm_strike(), Return one underlying's spec, raising :class:`KeyError` if it is not configured., The :class:`SymbolCodec` registered for this underlying's rule., Classify one leg's side through its underlying's registered codec., Resolve the candidate universe for one underlying.          Args:, Resolve every configured underlying, **in configured order**.          The uni, Legs of this underlying at the active expiry, with an exchange contradiction rej, The strike nearest to spot, with an exact tie resolving to the **lower** strike. (+1 more)

### Community 76 - "registry.py"
Cohesion: 0.17
Nodes (15): active_columns(), bind(), known_aggregates(), MetricSpec, Declarative metric registry (spec §3.4.0) — the extension point for M1..M29 and, Resolve a ``live_metrics`` token to the metric spec(s) it selects.      ``"all, The named aggregate group tokens (e.g. ``atm_aggregates``) — convenience for doc, Bind a compute function to an **already-registered** metric spec (P4/P7). (+7 more)

### Community 77 - "create_changes_patch.py"
Cohesion: 0.23
Nodes (14): batch_groups(), diff_filtered(), discover_repo(), main(), parse_name_status(), Path, Walk upward until we find:          main.py, Parse `git diff --name-status -z` into a list of path-groups.      The -z stre (+6 more)

### Community 78 - "Market Depth Recorder — Analytics Replay Performance Optimization"
Cohesion: 0.13
Nodes (15): Authoritative Optimization Order, Context, Critical files, ⚠ CRITICAL FINDING (2026-07-13) — the real bottleneck is the DuckDB WRITE, not metric compute, ⚠ FINDING (2026-07-13) — ~100-min arrow rebuild is faithful, but the `--verify` gate is mis-scaled, Future Phase (deferred — not in this scope), Market Depth Recorder — Analytics Replay Performance Optimization, Part B — Real-time suitability (assessment, documented not implemented) (+7 more)

### Community 79 - "`database_writer.py` — store writers (§3.6)"
Cohesion: 0.13
Nodes (14): Batch / commit engine (§3.6.1), Config keys consumed, Corruption recovery (§6.3), Daily selection + defensive rollover (§3.6.3), `database_writer.py` — store writers (§3.6), `DuckDBAnalyticalWriter(config, output_path, *, session_date=None, source_raw=None, schema_version=SCHEMA_VERSION, time_fn=time.time, write_backend=None)` — P7, Genericization, Input contract (`db_queue`) (+6 more)

### Community 80 - "Framework Implementation Plan"
Cohesion: 0.13
Nodes (14): Appendix A: Glossary, Appendix B: Reference Documents, Continuous Improvement, Document History, Document Information, Executive Summary, Framework Implementation Plan, Future Enhancements (Post-v1) (+6 more)

### Community 81 - "5. Budget Allocator & Depth Allocator"
Cohesion: 0.13
Nodes (15): 5.10 Performance Considerations, 5.11 Worked Example, 5.1.1 Purpose, 5.1.2 What it does NOT know, 5.1.3 Interface, 5.1.4 Configuration, 5.1 Budget Allocator, 5.3 Configuration (+7 more)

### Community 82 - "`websocket_client.py` — Dynamic WebSocket Manager + DSM (§3.3, §6.1, §3.2.5/§9)"
Cohesion: 0.13
Nodes (14): Backpressure (§5.1, decision 28), Config keys consumed, Data flow (one packet), Deferred, `DepthWebSocketClient(config, instrument_manager, raw_file_queue, proc_queue, shutdown_event, *, time_fn=time.time, sleep_fn=time.sleep, transport=None, name="Feed")`, DSM (§3.3.2), Genericization, Module helpers (+6 more)

### Community 83 - "._maybe_rollover"
Cohesion: 0.16
Nodes (7): Open (append) the current-date gzip handle and write the provenance HEADER line, Flush → fsync → close the handle (idempotent; guards a None/closed handle). No E, Serialize one packet to a JSONL line and append it, honoring rollover + two-tier, Two-tier flush (§3.5.3): cheap ``flush()`` at ``flush_max_records``; bounded dur, Defensive daily-file rollover (§3.5.4). Fires only if the IST date changes mid-r, Append the EOF provenance marker for the current file (§3.5.4): data ``record_co, Drain ``raw_file_queue`` until shutdown is signaled AND the queue is empty (§3.5

### Community 84 - "AtmDistancePolicy"
Cohesion: 0.14
Nodes (14): AtmDistancePolicy, policy_for(), Rank by absolute distance from ATM, nearest first (§14.6, fork F12 default)., Resolve a configured ``priority_policy.policy`` name to a policy instance., policy(), §14.6: a policy that silently degrades to another is the forbidden silent defaul, test_a_non_string_policy_name_fails_fast(), test_an_unknown_policy_name_fails_fast() (+6 more)

### Community 85 - "window_specs_from_underlyings"
Cohesion: 0.19
Nodes (15): Any, Build specs from recorder-shaped ``underlyings[]`` entries (§17).      Only pl, window_specs_from_underlyings(), underlyings[] belongs to the recorder; the framework reads its three keys and no, No silently defaulted seam: the rules are keyword-only and required., recorder_entry(), test_an_entry_may_override_its_rules(), test_specs_are_built_from_recorder_shaped_underlyings() (+7 more)

### Community 86 - "module_tree"
Cohesion: 0.13
Nodes (15): executable_source(), module_source(), module_tree(), AST, The module with every docstring stripped: prose may cite a broker, code may not., Extends the F1 banned-token guard with the option-type tags: option-side meaning, F3 must not know tbt_budget, premium slots, connections, or channels., Determinism: no clock, no randomness, no environment, no network. (+7 more)

### Community 87 - "depth_transition_probe.py"
Cohesion: 0.16
Nodes (14): dumps_evidence(), Serialise an evidence record deterministically (stable key order, trailing newli, _ack_notes(), build_parser(), in_market_session(), logical_of(), _packets_for(), ArgumentParser (+6 more)

### Community 88 - "compute_config_hash"
Cohesion: 0.19
Nodes (13): compute_config_hash(), sha256 over the canonicalized ``metrics`` + ``regime`` + ``underlyings`` config, base_config(), _good_config(), Any, pytest_configure(), Shared pytest fixtures: a known-good config dict plus a helper to materialize it, A fresh, valid config dict with data paths under ``tmp_path``. Deep-copy before (+5 more)

### Community 89 - "OpenAlgo Patch — FYERS TBT channel spread (P10-A)"
Cohesion: 0.14
Nodes (13): 1. What problem it fixes, 2. What the patch does, 3. Pro / cons analysis (why this over the alternatives), 4. Operator notes, 5. Re-test checklist (before calling P10-A done), 6. Risks this patch does NOT remove (verify live — P10-E), 7. Verification done so far (offline, this session), 8.1 Authoritative source — official FYERS TBT docs (+5 more)

### Community 90 - "Generic Market-Depth Framework Architecture"
Cohesion: 0.14
Nodes (13): 0.1 Concurrency Contract (binding), 0.2 Corrected Pipeline, 0. Locked Decisions & Corrections Applied, 8.1 System Startup Sequence, 8.2 Runtime Data Flow, 8.3 Shutdown Sequence, 8.4 Configuration Management, 8. Integration & Lifecycle (+5 more)

### Community 91 - "3. Window Manager"
Cohesion: 0.14
Nodes (14): 3.10 Failure Modes, 3.11 Edge Cases, 3.12 Performance Considerations, 3.1 Purpose, 3.2 Responsibilities, 3.3 What Window Manager Does NOT Know, 3.4.1 Extension points: `SymbolCodec` and `ExpiryCalendar`, 3.4 Interface Definition (+6 more)

### Community 92 - "SymbolCodec"
Cohesion: 0.15
Nodes (11): ExpiryCalendar, Protocol, Seam owning what an instrument master's option-type tag *means* (§10.2)., Return the side for one master tag, raising :class:`ValueError` if the tag is un, Seam owning expiry selection -- weekly/monthly rollover and holidays (§10.2)., Return the active expiry tag for one underlying, or ``None`` when none is resolv, SymbolCodec, calendars() (+3 more)

### Community 93 - "Market Depth Recorder Microservice - Enhanced Design Specification"
Cohesion: 0.14
Nodes (13): 2.1 Complete Directory Schema, 2.2 End-to-End Data Pipeline & Execution Flow, 2.3 Threading & Memory Allocation Model, 2. Directory Layout & Module Flow, 5.1 Concurrency Architecture & Thread Functions, 5.2 Scaling the Processor to a Separate Process (design headroom), 5. Threading, Queue Safety & Backpressure, 7.1 Annotated YAML Configuration Template (+5 more)

### Community 94 - "`main.py` — Recorder Orchestrator (P6)"
Cohesion: 0.15
Nodes (12): Additive touches to earlier modules (all tested), Config keys consumed, Deviation note (trading-calendar idle), Genericization, Health schema (`health.json`, §6.4 + §9), `main.py` — Recorder Orchestrator (P6), Public API, Responsibilities (+4 more)

### Community 95 - "Phase 9 — Live-Run Session Notes (2026-07-06)"
Cohesion: 0.15
Nodes (12): 0. Context, 1.1 InstrumentManager `name`-column match (real bug — blocked all resolution), 1.2 Invalid heartbeat config crashed the WS (real bug), 1.3 Preflight depth-level inference for 5-level (non-TBT) books (correctness gap), 1. Bugs found & fixed this session (all with test coverage; 228 tests green), 2. Live-run results — confirmations captured, 3. Headline finding — FYERS TBT caps at 5 symbols per channel; OpenAlgo pins channel "1", 4. Tests / verifications performed this session (+4 more)

### Community 96 - "4. Priority Policy"
Cohesion: 0.15
Nodes (13): 4.10 Failure Modes, 4.11 Extension Points, 4.12 Testing Strategy, 4.1 Purpose, 4.2 Responsibilities, 4.3 What Priority Policy Does NOT Know, 4.4 Interface Definition, 4.5 Configuration (+5 more)

### Community 97 - "executable_source"
Cohesion: 0.15
Nodes (13): executable_source(), The module with every docstring stripped: prose may cite a broker fact, code may, The budget is a broker capability that arrives as an integer (§13). Reconstructi, §13.3, fork F6: redistribution reads capacity and weights only. Reading a leg's, F5 is pure and synchronous. Every one of these is a file descriptor, and product, Word-boundary matched: `runtime` in a message is not a clock read., test_no_broker_capability_arithmetic_in_executable_code(), test_no_clock_or_randomness_reaches_the_split() (+5 more)

### Community 98 - "test_metrics_aggregate.py"
Cohesion: 0.35
Nodes (12): call(), ctx(), feat(), Multi-strike aggregate + regime bodies (spec §3.4.4) — hand-computed fixtures +, regime(), test_bnet_pooled_and_window_invariant(), test_compute_underlying_windows_and_scalars(), test_consolidated_pressures_and_nop() (+4 more)

### Community 99 - "Operator Notes — Market Depth Recorder"
Cohesion: 0.17
Nodes (11): 1.1 Before the open (one-time per day / per deploy), 1.2 Start the daemon, 1.3 Mid-session health (any time), 1. Daily run, 2. End of day (EOD), 3. Verification checklist (per capture), 4. Operator precautions, 5. Runtime files — what's what (all under `data/`, all gitignored) (+3 more)

### Community 100 - "7.1 Technical Risks"
Cohesion: 0.17
Nodes (12): 7.1.1 Broker API Instability, 7.1.2 Memory Exhaustion, 7.1.3 Data Corruption, 7.1 Technical Risks, 7.2.1 Subscription Limit Exhaustion, 7.2.2 Clock Skew and Timestamp Issues, 7.2.3 Disk Space Exhaustion, 7.2 Operational Risks (+4 more)

### Community 101 - "Success Metrics"
Cohesion: 0.17
Nodes (12): 8.3 Status Snapshot Example, 8.4 Continuous Improvement Process, Appendix C: Quick Reference Commands, Conclusion, Configuration Validation, Goal Setting, Health Checks, Log Analysis (+4 more)

### Community 102 - "Phase 3: Budget Allocator, Depth Allocator & Subscription Manager"
Cohesion: 0.17
Nodes (12): 5.1 Budget Allocator (Day 1), 5.2 Depth Allocator Core (Days 2-3), 5.3 Advanced Allocation Strategies (Days 4-5), 6.1 Subscription State Management (Days 1-3), 6.2 Subscription Lifecycle Management (Days 4-5), 6.3 Batch Operations (Days 1-2), 6.4 Subscription Manager Integration (Days 3-5), Phase 3: Budget Allocator, Depth Allocator & Subscription Manager (+4 more)

### Community 103 - "6. Subscription Manager"
Cohesion: 0.17
Nodes (12): 6.10 Recovery Mechanisms, 6.11 Edge Cases, 6.1 Purpose, 6.2 Responsibilities, 6.3 Interface Definition, 6.4 Configuration, 6.5 Lifecycle, 6.6 State Management (+4 more)

### Community 104 - ".allocate_budget"
Cohesion: 0.17
Nodes (7): _check_budget(), _check_counts(), Split ``total_budget`` across the underlyings in ``candidate_counts`` (§10.4, §1, Weight per eligible underlying, or a wiring error naming what is missing (§17)., Seat ``min_per_underlying`` for eligible underlyings; return what is left to spl, Largest-remainder weighted split of ``remaining``, then cap each share by its ca, Hand out slots freed by a candidate cap, one at a time, in weight order (§13.3,

### Community 105 - "TagSymbolCodec"
Cohesion: 0.17
Nodes (9): Every registered tag, in registration order., A :class:`SymbolCodec` built from the master's call and put tags.      Tags ar, TagSymbolCodec, test_codec_maps_configured_tags_to_sides(), test_codec_rejects_a_blank_tag(), test_codec_rejects_a_tag_registered_on_both_sides(), test_codec_rejects_an_empty_side(), test_codec_rejects_an_unknown_tag() (+1 more)

### Community 106 - "decay_weights"
Cohesion: 0.17
Nodes (9): _parse_side(), ndarray, Decay weights ``w_1..w_n`` (§3.4.2 M8), sliced from the precomputed array., Turn one side's list-of-level-dicts into ``(price, qty, orders)`` float64 arrays, test_decay_weights_reference_values(), test_decay_weights_rejects_bad_args(), decay_weights(), ndarray (+1 more)

### Community 107 - "Plan 001 — Market Depth Recorder Implementation"
Cohesion: 0.17
Nodes (11): Cross-cutting invariants (guard every phase), Decisions taken during P3 planning (2026-07-03), Locked decisions — Generic Market-Depth Framework docs (2026-08-05), P0.0 — Doc sync (execute FIRST, right after exiting plan mode) — ✅ DONE (2026-07-03, commit 29eb68a), P1 — InstrumentManager (`instrument_manager.py`), P1 subtask checklist (embedded 2026-07-03; ✅ complete 2026-07-03), P3 subtask checklist (embedded 2026-07-03; tick as completed), P3 — WebSocket client + DSM (`websocket_client.py`) (+3 more)

### Community 108 - "PROJECT_NOTES.md"
Cohesion: 0.17
Nodes (10): Agnosticism — avoid, Completion Audit, Decision Rules, Design Invariants (must not break), Documentation (`Documents/`), Module Map & Threading Topology, Output Style, Planning & Implementation (+2 more)

### Community 109 - "Confidence"
Cohesion: 0.18
Nodes (8): Confidence, The weaker of the two sides -- a transition is only as good as its worse observa, The least-supported of ``confidences``. UNKNOWN dominates, then INFERRED., Whether some operation (e.g. unsubscribe) is supported by the live path., ``True``/``False`` only on evidence; ``None`` means not established., What the evidence actually supports. Never widened by convenience., SupportEvidence, weakest()

### Community 110 - "ProbeRequest"
Cohesion: 0.18
Nodes (10): default_transition_plan(), ProbeRequest, One wire operation, fully described for audit. ``params`` must already be redact, One row of the §20.1 transition matrix, in one symbol form, by one mechanism., The minimal deterministic case set that answers §20.1 on at most two instruments, TransitionCase, _dry_run_report(), plan_for() (+2 more)

### Community 111 - "`depth_transition_probe.py`"
Cohesion: 0.17
Nodes (11): Cases, `depth_transition_probe.py`, Related, `tbt_channel_probe.py`, `tbt_multiconn_probe.py`, The two spellings, Three depths, never conflated, `tools/fyers/` — FYERS streaming diagnostics (+3 more)

### Community 112 - "StrikeHistory"
Cohesion: 0.20
Nodes (5): deque, Per-symbol rolling history that M22 (quote stability) and M24 (confidence) read, The last ``window`` entries of one deque (fewer during warm-up)., StrikeHistory, Event

### Community 113 - "`file_writer.py` — Tier-0 gzip audit writer (§3.5)"
Cohesion: 0.18
Nodes (10): Config keys consumed, Daily rollover (§3.5.4, defensive), File format (self-describing — §3.5.4), `file_writer.py` — Tier-0 gzip audit writer (§3.5), Public API, `RawTickFileWriter(config, raw_file_queue, shutdown_event, session_date, *, schema_version=SCHEMA_VERSION, time_fn=time.time, error_queue=None, instruments=None, name="RawFileWriter")`, Responsibility, Tests (`tests/test_file_writer.py`, offline) (+2 more)

### Community 114 - "`instrument_manager.py` — Instrument & Expiry Manager (§3.2)"
Cohesion: 0.18
Nodes (10): CLI, Config keys consumed, Deferred to later phases, `instrument_manager.py` — Instrument & Expiry Manager (§3.2), `InstrumentManager(config, rest_client=None)`, Public API, Resolution rules, Responsibility (+2 more)

### Community 115 - "Performance — Offline Analytics Replay Optimization"
Cohesion: 0.18
Nodes (11): 10. Lessons learned, 11. Deferred work (framework evolution — not blockers), 1. Executive summary, 2. Original problem statement, 3. Investigation timeline, 4. The key turning point — measurement disproved the profile, 6. The `_slope` investigation — why the canonical reference changed, 7. Arrow writer redesign (+3 more)

### Community 116 - "Phase 2: Window Manager & Priority Policy"
Cohesion: 0.18
Nodes (11): 2.1 Conceptual Overview, 2.2.1 Core Data Models, 2.2.2 Worked Example: Zone Calculations, 2.2 Zone Manager Implementation, 2.3.1 The Market Context, 2.3.2 Policy Interface and Base Classes, 2.3.3 Worked Example: Policy Comparison, 2.3 Priority Policy System (+3 more)

### Community 117 - "Phase 5: Testing, Validation & Migration"
Cohesion: 0.18
Nodes (11): 10.1 Unit Test Completion (Days 1-2), 10.2 Integration Testing (Days 3-5), 11.1 Validation Against Requirements (Days 1-2), 11.2 Stress Testing (Days 3-5), 12.1 Migration Analysis (Days 1-2), 12.2 Migration Implementation (Days 3-5), Phase 5 Milestone Checklist, Phase 5: Testing, Validation & Migration (+3 more)

### Community 118 - "Phase 2: Window Manager & Priority Policy"
Cohesion: 0.18
Nodes (11): 3.1 Window Manager Foundation (Days 1-3), 3.2 Dynamic Window Updates (Days 4-5), 3.3 Multi-Underlying Support (Days 1-2), 3.4 Window Manager Integration Tests (Days 3-5), 4.1 Priority Policy Base Class (Days 1-2), 4.2 Built-in Priority Policies (Days 3-5), Phase 2 Milestone Checklist, Phase 2: Window Manager & Priority Policy (+3 more)

### Community 119 - "Phase 4: Broker Adapter & Integration"
Cohesion: 0.18
Nodes (11): 7.1 Base Adapter Implementation (Days 1-3), 7.2 Adapter Communication Layer (Days 4-5), 8.1 FYERS Adapter Implementation (Days 1-4), 8.2 Market Data Processing (Day 5), 9.1 Framework Orchestrator (Days 1-3), 9.2 Lifecycle Management (Days 4-5), Phase 4: Broker Adapter & Integration, Phase 4 Milestone Checklist (+3 more)

### Community 120 - "`replay.py` — Offline replay + DuckDB rebuild (P7)"
Cohesion: 0.18
Nodes (10): CLI (`__main__.py`, §8.2), Config keys consumed, Filters (decision 72) — warm-up caveat, Genericization, How it works, Public API, `replay.py` — Offline replay + DuckDB rebuild (P7), Tests (`tests/test_replay.py`, offline) (+2 more)

### Community 121 - "duckdb_table_diff.py"
Cohesion: 0.33
Nodes (10): DuckDBPyConnection, _attach(), _col_types(), diff_exact(), diff_tolerance(), main(), _parse_args(), Namespace (+2 more)

### Community 122 - "main"
Cohesion: 0.27
Nodes (10): F, main(), _parse_args(), Namespace, OLS slope via numpy pairwise summation (historical / reference implementation)., OLS slope via pure-Python sequential summation (current implementation)., Exact rational evaluation of the SAME formula on the exact float inputs (ground, slope_exact() (+2 more)

### Community 123 - "P0 — Scaffolding, config, utils, registry skeleton"
Cohesion: 0.18
Nodes (11): P0-A · Git-aware folder rename `MarketDepth_Recorder/` → `market_depth_recorder/`, P0-B · Package skeleton + CLI surface — ✅, P0-C · `requirements.txt` + venv bootstrap — ✅, P0-D · `config.yaml` (materialize §7.1 template) — ✅, P0-E · `config.py` — load + full §7.3 validation (fast-fail, exit 1) — ✅, P0-F · `utils.py` — shared primitives — ✅, P0-G · `metrics/registry.py` — declarative skeleton (§3.4.0), **full M1–M29 metadata** — ✅, P0-H · `Documents/` skeleton — ✅ (+3 more)

### Community 124 - "Any"
Cohesion: 0.24
Nodes (11): count_depth_levels(), _depth_in(), observe_depth(), parse_subscribe_ack(), per_leg_entries(), Any, Read a depth value from one mapping, ``actual_depth`` first, or ``None``., Return the per-leg result entries carried inside a proxy acknowledgement. (+3 more)

### Community 125 - "`eod_report.py` — EOD health & sanity-check report (P10-C)"
Cohesion: 0.20
Nodes (9): Checks (status = worst-wins overall), CLI, Config keys consumed, `eod_report.py` — EOD health & sanity-check report (P10-C), First real run (2026-07-06), Paths & FDs, Public API, Responsibility (+1 more)

### Community 126 - "2. Broker Capabilities Layer"
Cohesion: 0.20
Nodes (10): 2.1 Purpose, 2.2 Responsibilities, 2.3 Interface Definition, 2.4 Configuration Format, 2.5 Lifecycle, 2.6 State Management, 2.7 Threading Model, 2.8 Extension Points (+2 more)

### Community 127 - "7. Broker Adapter"
Cohesion: 0.20
Nodes (10): 7.1 Purpose, 7.2 Responsibilities, 7.3 Interface Definition, 7.4 Configuration, 7.5 Lifecycle, 7.6 State Management, 7.7 Threading Model, 7.8 Extension Points (+2 more)

### Community 128 - "10. Component contracts"
Cohesion: 0.20
Nodes (10): 10.1 Broker Capabilities, 10.2 Window Manager, 10.3 Priority Policy, 10.4 Budget Allocator, 10.5 Depth Allocator, 10.6 Subscription Manager — **not a thread** (F1), 10.7 Broker Adapter, 10.8 Framework Orchestrator (+2 more)

### Community 129 - "_subscribe_ack"
Cohesion: 0.20
Nodes (10): The real ack has no top-level depth at all -- it lives in ``subscriptions[]``., Subscription processing complete" rides along with success; it must not become a, Reading depth out of the nested entry does not make it evidence of delivered dep, The real two-level subscribe acknowledgement (``server.py`` subscribe_client)., An ack carrying somebody else's request_id must not be accepted for this leg., _subscribe_ack(), test_ack_depth_is_still_only_inferred_however_it_was_read(), test_ack_reads_depth_from_the_real_nested_subscription_entry() (+2 more)

### Community 130 - "DepthProbeResult"
Cohesion: 0.20
Nodes (5): _FakeResp, Minimal context-manager stand-in for a urllib response (only ``read`` is used)., test_preflight_result_shape(), DepthProbeResult, Per-underlying result of the live depth probe.

### Community 131 - "._on_message"
Cohesion: 0.20
Nodes (6): test_normalize_keeps_wire_symbol_and_fields(), normalize_market_data(), Flatten a proxy ``market_data`` envelope into the canonical in-process packet (p, Filter to market_data, normalize, route spot ticks to the DSM, and tee every pac, Track the MAX observed depth per underlying (§9 health map: alarm if a feed that, Two independent puts, no lock, returns immediately. Analytics sheds first, audit

### Community 132 - "Offline Replay Optimization — Engineering Journal"
Cohesion: 0.22
Nodes (9): Background, Deferred work (framework evolution — not blockers), Investigation timeline, Key design decisions, Lessons learned, Major findings, Offline Replay Optimization — Engineering Journal, Performance milestones (+1 more)

### Community 133 - "OpenAlgo issue — FYERS TBT `_run_websocket` retry-on-return storm"
Cohesion: 0.22
Nodes (8): File, Impact, OpenAlgo issue — FYERS TBT `_run_websocket` retry-on-return storm, Probe workaround (in `tools/fyers/tbt_multiconn_probe.py`), Related, Root cause, Suggested upstream fix (for OpenAlgo, if pursued), Symptom

### Community 134 - "`processor.py` — Metric Processor (P4a + P4b)"
Cohesion: 0.22
Nodes (8): Behaviour details, Config keys consumed, db_queue contract (P4 defines; P5/P7 consume) — decision 38, Deferred to P5+ / later, `processor.py` — Metric Processor (P4a + P4b), Public API, Responsibility, Threads / locks / FDs

### Community 135 - "Module: `metrics/registry.py`"
Cohesion: 0.22
Nodes (8): Module: `metrics/registry.py`, Notes / caveats, P4a additions (bodies bound), Public API, Tests, Threads / locks / FDs owned, What is registered (metadata only), Why a registry

### Community 136 - "22. Proposed phase sequence"
Cohesion: 0.22
Nodes (9): 22.1 F1 subtask checklist (approved 2026-08-25; embedded before implementation) — **COMPLETE 2026-08-25**, 22.2 F0 approval gate, 22.3 F2 subtask checklist (approved 2026-08-25) — **COMPLETE 2026-08-25**, 22.4 F3 subtask checklist (approved 2026-08-25; embedded before implementation) — **COMPLETE 2026-08-25**, 22.5 F4 subtask checklist (approved 2026-08-25; embedded before implementation) — **COMPLETE 2026-08-25**, 22.6 F5 subtask checklist (approved 2026-08-25; embedded before implementation) — **COMPLETE 2026-08-25**, 22.7 F6 subtask checklist (approved 2026-08-25; embedded before implementation), 22.8 F7 subtask checklist - split F7A / F7B (approved 2026-08-26; embedded before implementation) (+1 more)

### Community 137 - "FakeClock"
Cohesion: 0.25
Nodes (6): FakeClock, The injected clock. Tests advance it explicitly; nothing here ever sleeps., test_effective_budget_must_be_a_plain_int(), test_effective_budget_must_not_be_negative(), test_every_mutator_advances_last_updated_from_the_injected_clock(), test_last_updated_is_stamped_at_construction_from_the_clock()

### Community 138 - "FakeInstrumentManager"
Cohesion: 0.25
Nodes (6): FakeInstrumentManager, Minimal resolved-manager stand-in: wide strike grids + probe strikes for NIFTY a, test_preflight_unreachable_degrades_fast(), Exception, Raised by a transport's ``send`` when the socket is not currently open., TransportNotConnected

### Community 139 - "build_evidence"
Cohesion: 0.25
Nodes (9): build_evidence(), observation_to_dict(), The before/after pair for one case, plus the side questions §20.1 asks., One :class:`ProbeResult` as JSON-ready primitives, confidence included., One :class:`TransitionObservation` as JSON-ready primitives., Assemble the full evidence record.      ``mode`` is ``"dry-run"`` or ``"live"`, result_to_dict(), TransitionObservation (+1 more)

### Community 140 - "Module: `config.py`"
Cohesion: 0.25
Nodes (7): Config keys consumed, Module: `config.py`, Public API, Responsibilities, Tests, Threads / locks / FDs owned, Validation rules (§7.3) implemented

### Community 141 - "LIVE_RUN.md — P9 live-run session runbook"
Cohesion: 0.25
Nodes (7): A. Preconditions (verify before starting), B. Run sequence, C. Confirmations to capture (paste results here after the run), D. Abort / rollback, LIVE_RUN.md — P9 live-run session runbook, P10-E — 2026-07-07 (patched OpenAlgo, fresh instance; ✅ PASS with known WARNs), P9 first run — 2026-07-06 (⚠️ PARTIAL PASS; full record `Documents/patches/Phase9_notes.md`)

### Community 142 - "`metrics/` — Metric registry, snapshot & compute bodies (P4a + P4b)"
Cohesion: 0.25
Nodes (7): `aggregate.py` — multi-strike aggregates + regime (spec §3.4.4), `metrics/` — Metric registry, snapshot & compute bodies (P4a + P4b), `per_strike.py` — M1–M29 bodies (spec §3.4.2), `registry.py` — declarative registry + binding, `rolling.py` — rolling-window bodies (spec §3.4.3), `snapshot.py` — shared inputs, Tests

### Community 143 - "comprehensive_implementation_guide_part2.md"
Cohesion: 0.25
Nodes (7): 4.1 Base Adapter Interface, 4.2 FYERS Adapter Implementation, 4.3 Adapter Factory, Appendix A: Complete Configuration Example, Comprehensive Implementation Guide - Part 2, Market Depth Recorder Framework (Phases 2-6), Phase 4: Broker Adapter & Integration

### Community 144 - "Appendix B: API Reference"
Cohesion: 0.25
Nodes (8): Appendix B: API Reference, BrokerAdapter, BudgetAllocator, DepthAllocator, MarketDepthRecorder, PriorityPolicy, SubscriptionManager, WindowManager

### Community 145 - "Phase 6: Production Readiness & Documentation"
Cohesion: 0.25
Nodes (8): 13.1 Comprehensive Documentation (Days 1-3), 13.2 Deployment Preparation (Days 4-5), 14.1 Production Dry Run (Days 1-3), 14.2 Release Preparation (Days 4-5), Phase 6 Milestone Checklist, Phase 6: Production Readiness & Documentation, Week 15: Documentation & Deployment, Week 16: Final Validation & Release

### Community 146 - "Phase 1: Foundation & Broker Capabilities Layer"
Cohesion: 0.25
Nodes (8): 1.1 Project Structure Creation (Days 1-2), 1.2 Data Models Implementation (Days 3-5), 2.1 Broker Capabilities Interface (Days 1-3), 2.2 Configuration Management (Days 4-5), Phase 1: Foundation & Broker Capabilities Layer, Phase 1 Milestone Checklist, Week 1: Core Infrastructure Setup, Week 2: Broker Capabilities Layer

### Community 147 - "Setup — Market Depth Recorder"
Cohesion: 0.25
Nodes (7): Bootstrap (from the parent `SS_Projects/`), Configuration, FYERS 50-level (TBT) precondition, Run (always as a module, from `SS_Projects/`), Setup — Market Depth Recorder, Storage layout (P10-B), Tests (no live feed required)

### Community 148 - "budget_allocator_for"
Cohesion: 0.36
Nodes (8): budget_allocator_for(), Build the allocator from a validated ``budget_allocator`` config block (§17)., _cfg(), The same rule as `policy_for('blended')`: an operator who configured one split a, test_an_unimplemented_policy_is_refused_not_silently_served_by_weighted(), test_an_unknown_policy_is_refused(), test_configured_weights_are_read_only(), test_the_allocator_is_built_from_validated_config_end_to_end()

### Community 149 - "3. Detailed Component Design"
Cohesion: 0.25
Nodes (8): 3.4.0 Metric Registry (declarative extension point), 3.4.1 Resampling & Queue Routing Pipeline, 3.4.4 Multi-Strike Aggregate Matrix, 3.4 Metric Processor (`processor.py`), 3. Detailed Component Design, A. Strike Aggregation Windows, B. Mathematical Aggregation Formulas, C. Regime Classification Engine

### Community 150 - "Context"
Cohesion: 0.25
Nodes (8): Context, Decisions taken during P0 planning (2026-07-03), Decisions taken during P10-F — FYERS TBT protocol closure (2026-07-14), Decisions taken during P1 planning (2026-07-03), Locked decisions, Progress-tracking convention (this doc is live), Successor plan — the framework (2026-08-25), Verified integration findings (drive several decisions below)

### Community 151 - "_StubSession"
Cohesion: 0.25
Nodes (3): A scripted proxy: replies to every frame, optionally emits market data per subsc, _StubSession, test_cleanup_unsubscribes_every_wire_symbol_it_subscribed()

### Community 152 - "_FakeHandle"
Cohesion: 0.25
Nodes (3): _FakeHandle, Stand-in gzip handle whose first N writes raise OSError (models disk saturation), test_write_error_counted_and_thread_survives()

### Community 153 - "executable_source"
Cohesion: 0.25
Nodes (8): executable_source(), The module with every docstring stripped: prose may cite a later phase, code may, F4 ranks; it must not know tbt_budget, premium slots, connections, or channels., test_no_allocation_or_overlay_concept_appears(), test_no_budget_or_capability_concept_appears(), test_no_depth_tier_is_assigned(), test_no_index_exchange_or_option_tag_literal_in_executable_code(), test_the_source_scan_is_not_vacuous()

### Community 155 - "8.1 Phase-Specific Success Criteria"
Cohesion: 0.29
Nodes (7): 8.1 Phase-Specific Success Criteria, Phase 1: Foundation & Broker Capabilities, Phase 2: Window Manager & Priority Policy, Phase 3: Allocators & Subscription Manager, Phase 4: Broker Adapter & Integration, Phase 5: Testing, Validation & Migration, Phase 6: Production Readiness

### Community 156 - "1.3 Key Design Decisions"
Cohesion: 0.29
Nodes (7): 1.1 Layered Architecture, 1.2 Responsibility Boundaries, 1.3.1 Separation of Concerns, 1.3.2 Broker Agnosticism, 1.3.3 Capability-Driven Design, 1.3 Key Design Decisions, 1. Architecture Overview

### Community 157 - ".build_health"
Cohesion: 0.29
Nodes (4): _int_or_none(), Assemble the §6.4 health payload from the live workers' counters. ``getattr`` de, The never-shrink set of subscribed **wire** symbols (with ``:50`` on depth topic, ``"connected"`` while a session is open, else ``"disconnected"`` (health ``webso

### Community 158 - "3.3 Dynamic WebSocket Manager (`websocket_client.py`)"
Cohesion: 0.29
Nodes (7): 3.3.1 Feed Transport — OpenAlgo SDK Client (alternate), 3.3.1a Feed Transport — Raw WebSocket (primary/default), 3.3.2 Dynamic Strike Manager (DSM) & Boundary Checking Math, 3.3.3 Thread-Safe DSM Subscription Flow, 3.3.4 "Never Shrink" Rule Implementation, 3.3 Dynamic WebSocket Manager (`websocket_client.py`), Depth Subscription Mechanism (the `:50` suffix)

### Community 159 - "3.4.2 Exhaustive Per-Strike Metric Computation"
Cohesion: 0.29
Nodes (7): 3.4.2 Exhaustive Per-Strike Metric Computation, A. Spread Dynamics, B. Order Book Imbalances (OBI), C. Volumetric & Pressure Ratios, D. Liquidity Concentration & Structure, E. Wall Analytics & Book Stability, F. Extended Execution & Fair-Value Metrics

### Community 160 - "4. Database Schema Design (dual backend: live SQLite + analytical DuckDB)"
Cohesion: 0.29
Nodes (7): 4.1 SQL Schema Statements (SQLite — thin live store), 4.1a DuckDB Dialect (fat analytical store), 4.1b Provenance Table (`recorder_meta`, both backends), 4.2 Secondary Indexing Strategies, 4.3 Storage Layout (`WITHOUT ROWID` — live SQLite only, applied selectively), 4.4 Daily Database Maintenance & Checkpoints, 4. Database Schema Design (dual backend: live SQLite + analytical DuckDB)

### Community 161 - "8. Replay & Reprocess Mode (Offline Regeneration)"
Cohesion: 0.29
Nodes (7): 8.1 Purpose & Guarantees, 8.2 Invocation, 8.3 Simulated-Clock Resampler, 8.4 Verify Sub-Mode (drift detection), 8.5 Idempotency & Rotation, 8.6 Trigger Modes (when the fat path runs), 8. Replay & Reprocess Mode (Offline Regeneration)

### Community 162 - "14. Depth-allocation and ranking semantics"
Cohesion: 0.29
Nodes (7): 14.1 Hysteresis is effective-rank stickiness within a bounded protection band (F3 — resolved 2026-08-25), 14.2 One rank basis (F4), 14.3 Cooldown scope (F5), 14.4 Diff semantics under BASELINE MONOTONICITY (F8), 14.5 Rebalance trigger (F11), 14.6 Default priority policy (F12), 14. Depth-allocation and ranking semantics

### Community 163 - "module_tree"
Cohesion: 0.29
Nodes (7): module_source(), module_tree(), Module, 15 is a measured FYERS capability, not an architectural constant., test_no_hardcoded_broker_ceiling_in_executable_code(), test_the_module_does_not_import_later_phase_layers(), test_the_module_imports_only_the_stdlib_and_one_sibling()

### Community 164 - "ranked_symbols"
Cohesion: 0.29
Nodes (7): ranked_symbols(), §10.3's total order: score desc, then symbol. The CE/PE pair at one strike is th, Whether a leg is a candidate is F3's question; F4 ranks what it is handed., test_candidates_far_outside_any_window_still_rank(), test_mirrored_strikes_tie_and_break_by_symbol(), test_no_candidate_is_dropped_or_invented(), test_ties_break_by_symbol_ascending()

### Community 165 - "_OkManager"
Cohesion: 0.29
Nodes (5): _OkManager, P3: --preflight resolves the chain then runs the live depth probe; the actual de, Graceful degrade (decision 30): resolve OK but the depth probe can't connect → e, test_preflight_ok(), test_preflight_ws_unreachable_exits_0()

### Community 166 - "EOD Health & Sanity Report — 2026-07-07"
Cohesion: 0.33
Nodes (5): EOD Health & Sanity Report — 2026-07-07, Ops — health.json, Tier 0 — Raw audit log, Tier 1 — Live SQLite, Tier 2 — DuckDB analytics

### Community 167 - "Validation Artifacts — Offline Replay Optimization"
Cohesion: 0.33
Nodes (5): How the `_slope` adjudication was performed, Reproducibility note, Validation Artifacts — Offline Replay Optimization, What each artifact is, Why they were created

### Community 168 - "integration.md — whole-pipeline harness + FD audit (P8)"
Cohesion: 0.33
Nodes (5): Assertions (the whole-pipeline FD audit is assertion-backed), FD-holding resources covered (open → close, every path), integration.md — whole-pipeline harness + FD audit (P8), Notes, What it exercises

### Community 169 - "Phase 5: Testing, Validation & Migration"
Cohesion: 0.33
Nodes (6): 5.1 Unit Test Examples, 5.2 Integration Test Example, 5.3.1 Legacy to New Framework Mapping, 5.3.2 Migration Steps, 5.3 Migration Guide, Phase 5: Testing, Validation & Migration

### Community 170 - ".resolve_filename"
Cohesion: 0.33
Nodes (4): date, Event, Absolute path of the daily raw log for date ``d`` (§3.5.4). Reused by replay/orc, test_resolve_filename()

### Community 171 - "3.1 Orchestrator & Schedule Daemon (`main.py`)"
Cohesion: 0.33
Nodes (6): 3.1.1 Time-Comparison Loop & Milestone State Machine, 3.1.2 Mid-Day Startup & Resiliency Engine, 3.1.3 Thread Supervisor & Exception Gating, 3.1.4 Atomic Queue Flushing & Data Loss Prevention, 3.1.5 Session Guards (disk space & trading calendar), 3.1 Orchestrator & Schedule Daemon (`main.py`)

### Community 172 - "3.2 Instrument & Expiry Manager (`instrument_manager.py`)"
Cohesion: 0.33
Nodes (6): 3.2.1 REST API Querying & Raw Filtering Pipeline, 3.2.2 Weekly Expiry Resolution Algorithm, 3.2.3 Auto-Detection & Validation of Strike Steps, 3.2.4 O(1) Cache Mapping Structures, 3.2.5 Depth-Capability Preflight, 3.2 Instrument & Expiry Manager (`instrument_manager.py`)

### Community 173 - "3.4.3 Rolling Time Window Calculations"
Cohesion: 0.33
Nodes (6): 3.4.3 Rolling Time Window Calculations, A. Window Stat Trends, B. Liquidity Flow Dynamics, C. Options Book Momentum, D. Wall Persistence & Lifetime Analytics, E. Order Flow Imbalance (OFI)

### Community 174 - "3.6 Store Writers (`database_writer.py`)"
Cohesion: 0.33
Nodes (6): 3.6.1 Live Writer — Thread Architecture & Batch Transaction Engine, 3.6.2 Live Writer — High-Performance PRAGMA Tuning, 3.6.3 Live Writer — Daily Database Selection & Table Initialization, 3.6.4 Live Writer — Teardown Protocol, 3.6.5 Analytical Writer — DuckDB Bulk Load (offline), 3.6 Store Writers (`database_writer.py`)

### Community 175 - "P10 — Full-chain 50-level via OpenAlgo channel patch + dated storage + EOD health report"
Cohesion: 0.33
Nodes (6): P10-A · OpenAlgo channel-spread patch (PLATFORM code — scope-exception, user-authorized), P10-B · Dated storage inside the package (recorder code) — ✅ (2026-07-06, 237 tests), P10-C · EOD health & sanity-check + dated report (new module + CLI) — ✅ (2026-07-06, 252 tests), P10-D · Docs — ✅ (2026-07-06), P10-E · Live validation — ✅ DONE (2026-07-07; PASS with known WARNs; full record `Documents/{LIVE_RUN,phase_10E_notes}.md`), P10 — Full-chain 50-level via OpenAlgo channel patch + dated storage + EOD health report

### Community 176 - "P9 — Live-run session (runbook authored now, executed when market opens)"
Cohesion: 0.33
Nodes (6): P9-A · Preconditions checklist, P9-B · Run sequence, P9-C · Confirmations to capture (the P8 spec bullets, live), P9-D · Abort / rollback (in the runbook), P9 EXECUTION LOG (2026-07-06) — partial pass + one design-breaking finding, P9 — Live-run session (runbook authored now, executed when market opens)

### Community 177 - "TransitionOutcome"
Cohesion: 0.40
Nodes (4): classify_transition(), The verdict for one transition case., Decide whether the delivered depth changed.      Returns ``UNKNOWN`` unless **, TransitionOutcome

### Community 178 - "`tools/` — maintained developer utilities"
Cohesion: 0.33
Nodes (5): `fyers/`, `performance/`, Related, `tools/` — maintained developer utilities, `validation/`

### Community 179 - "5. Every optimization — what, why, measured contribution"
Cohesion: 0.40
Nodes (5): 5.1 Phase 1b — NumPy → pure-Python on tiny arrays *(kept; small offline impact)*, 5.2 P-W — Arrow columnar write backend *(the decisive lever)* — §7, 5.3 Phase P-C — chunked-Arrow streaming writer *(bounds peak RSS)* — §8, 5.4 Deferred / dropped for the offline goal, 5. Every optimization — what, why, measured contribution

### Community 180 - "Phase 3: Allocators & Subscription Manager"
Cohesion: 0.40
Nodes (5): 3.1 Budget Allocator Implementation, 3.2.1 Worked Example: The Two Stages Together, 3.2 Depth Allocator Implementation, 3.3 Subscription Manager Implementation, Phase 3: Allocators & Subscription Manager

### Community 181 - "Phase 6: Production Readiness & Documentation"
Cohesion: 0.40
Nodes (5): 6.1 Deployment Checklist, 6.2 Monitoring Metrics, 6.3 Troubleshooting Guide, Common Issues, Phase 6: Production Readiness & Documentation

### Community 182 - "8.2 Overall System Performance Metrics"
Cohesion: 0.40
Nodes (5): 8.2.1 Data Quality Metrics, 8.2.2 System Reliability Metrics, 8.2.3 Resource Efficiency Metrics, 8.2.4 Business Value Metrics, 8.2 Overall System Performance Metrics

### Community 183 - "10. Testing Strategy"
Cohesion: 0.40
Nodes (5): 10.1 Unit Tests, 10.2 Integration Tests, 10.3 Broker Adapter Tests, 10.4 Performance Tests, 10. Testing Strategy

### Community 184 - "12. Appendices"
Cohesion: 0.40
Nodes (5): 12. Appendices, Appendix A: Glossary, Appendix B: Configuration Reference, Appendix C: API Reference, Appendix D: Change Log

### Community 185 - "5.2 Depth Allocator"
Cohesion: 0.40
Nodes (5): 5.2.1 Purpose, 5.2.2 Responsibilities, 5.2.3 What Depth Allocator Does NOT Know, 5.2.4 Interface Definition, 5.2 Depth Allocator

### Community 186 - "Module: `utils.py`"
Cohesion: 0.40
Nodes (4): Module: `utils.py`, Public API, Tests, Threads / locks / FDs owned

### Community 187 - "1. System Overview & Objective"
Cohesion: 0.40
Nodes (5): 1.1 Architecture Context & System Topology, 1.2 High-Throughput & Volumetric Constraints, 1.3 System Design Philosophy, 1.4 Performance Targets & Guarantees, 1. System Overview & Objective

### Community 188 - "3.5 Gzip Flat File Writer (`file_writer.py`)"
Cohesion: 0.40
Nodes (5): 3.5.1 Thread Architecture & Queue Consumer Loop, 3.5.2 Gzip Compression & File Handle Details, 3.5.3 Buffered Flushing & Crash Resilience, 3.5.4 Daily File Naming & Graceful Teardown, 3.5 Gzip Flat File Writer (`file_writer.py`)

### Community 189 - "6. Recovery, Failover & Network Fault Tolerance"
Cohesion: 0.40
Nodes (5): 6.1 WebSocket Reconnection & Subscription Restoration Engine, 6.2 Timeline Continuity Guard & NaN Padding, 6.3 SQLite Database Corruption Recovery Pipeline, 6.4 Liveness Watchdog & OS-Agnostic Supervision, 6. Recovery, Failover & Network Fault Tolerance

### Community 190 - "P6 — Orchestrator (`main.py`)"
Cohesion: 0.40
Nodes (5): Concurrency & FD ownership, Decisions taken during P6 planning (2026-07-04), Forks resolved (2026-07-04, user), P6 — Orchestrator (`main.py`), P6 subtask checklist (embedded 2026-07-04; ✅ complete 2026-07-05)

### Community 191 - "P4 — Processor thin/live (`processor.py`), split P4a / P4b"
Cohesion: 0.40
Nodes (5): Decisions taken during P4 planning (2026-07-03), Decisions taken during P4b planning (2026-07-03), P4 — Processor thin/live (`processor.py`), split P4a / P4b, P4a subtask checklist — engine + per-strike M1–M29 (embedded 2026-07-03; ✅ complete 2026-07-03), P4b subtask checklist — rolling windows + aggregates + regime (embedded 2026-07-03; ✅ complete 2026-07-04)

### Community 192 - "P5 — SQLite live writer (`database_writer.py::SQLiteLiveWriter`)"
Cohesion: 0.40
Nodes (5): Decisions taken during P5 planning (2026-07-04), FD structure (close on EVERY path), Forks resolved (2026-07-04), P5 — SQLite live writer (`database_writer.py::SQLiteLiveWriter`), P5 subtask checklist (embedded 2026-07-04; ✅ complete 2026-07-04)

### Community 193 - "P8 — Offline Integration & Soak (automated, committed)"
Cohesion: 0.40
Nodes (5): Forks resolved (2026-07-06, user), P8.0 — Doc sync (execute FIRST) — ✅ (this doc + spec §6.4/§3.1.4 + PROJECT_NOTES + the main.md/CHANGELOG e2e-claim correction), P8 — Offline Integration & Soak (automated, committed), P8 subtask checklist (embedded 2026-07-06; ✅ complete 2026-07-06), Two exploration findings that reshape P8 (verified 2026-07-06)

### Community 194 - "13. Budget-allocation semantics"
Cohesion: 0.40
Nodes (5): 13.1 Premium eligibility (F13), 13.2 `min_per_underlying` applies to eligible underlyings only (F7 + F13), 13.3 Redistribution of unspent slots (F6), 13.4 Worked examples, 13. Budget-allocation semantics

### Community 195 - "20. Fork decisions — CLOSED (2026-08-25)"
Cohesion: 0.40
Nodes (5): 20.1 F9 — depth-transition probe specification (phase F7), 20.2 F14 — provisional decision, validated in phase F8, 20.3 F3 re-resolution — hysteresis semantics (decided 2026-08-25, before F5 implementation), 20.4 F6 — pending/failed feedback model (decided 2026-08-25, before F6 implementation), 20. Fork decisions — CLOSED (2026-08-25)

### Community 196 - "test_preflight_reads_depth_and_warns_on_degradation"
Cohesion: 0.40
Nodes (5): _depth_pkt(), test_preflight_reads_depth_and_warns_on_degradation(), test_wire_symbol_suffix(), Append the ``:50`` TBT suffix when requesting more than the broker default (plan, wire_symbol()

### Community 197 - "Legacy pre-Phase-1b analytics reference (obsolete, retained for provenance)"
Cohesion: 0.50
Nodes (3): Do not use for verification, Legacy pre-Phase-1b analytics reference (obsolete, retained for provenance), Why this reference was retired (not "wrong" — obsolete)

### Community 198 - "11. Migration from FYERS-Specific Implementation"
Cohesion: 0.50
Nodes (4): 11.1 Migration Phases, 11.2 Backward Compatibility, 11.3 Testing During Migration, 11. Migration from FYERS-Specific Implementation

### Community 199 - "9. Failure Modes & Recovery"
Cohesion: 0.50
Nodes (4): 9.1 Failure Mode Matrix, 9.2 Recovery Strategy, 9.3 Reconciliation Strategy, 9. Failure Modes & Recovery

### Community 201 - "P2 — Tier-0 gzip file writer (`file_writer.py`)"
Cohesion: 0.50
Nodes (4): Decisions taken during P2 planning (2026-07-03), FD structure (close on EVERY path), P2 subtask checklist (embedded 2026-07-03; ✅ complete 2026-07-03), P2 — Tier-0 gzip file writer (`file_writer.py`)

### Community 202 - "P7 — Replay + DuckDB writer (`replay.py`, `database_writer.py::DuckDBAnalyticalWriter`)"
Cohesion: 0.50
Nodes (4): Decisions taken during P7 planning (2026-07-05), Forks resolved (2026-07-05, user), P7 — Replay + DuckDB writer (`replay.py`, `database_writer.py::DuckDBAnalyticalWriter`), P7 subtask checklist (embedded 2026-07-05; ✅ complete 2026-07-06)

### Community 203 - "6. Locked decisions — Plan_002"
Cohesion: 0.50
Nodes (4): 6. Locked decisions — Plan_002, F1 — DECIDED (2026-08-25): there is NO SUBSCRIPTION thread, F2 — DECIDED (2026-08-25): permanent standard-depth baseline + mutable premium-depth overlay, F3 window semantics — DECIDED (2026-08-25, at the F3 completion gate)

### Community 204 - "_never_construct"
Cohesion: 0.50
Nodes (4): _never_construct(), test_dry_run_makes_no_socket_and_starts_no_thread(), test_live_outside_the_session_refuses_unless_forced(), test_live_without_a_key_refuses_before_touching_the_network()

### Community 205 - "chain"
Cohesion: 0.67
Nodes (4): alpha_candidates(), beta_candidates(), chain(), strikes_around()

### Community 206 - "Success Metrics"
Cohesion: 0.67
Nodes (3): Project Metrics, Success Metrics, Technical Metrics

## Knowledge Gaps
- **796 isolated node(s):** `Project`, `Scope`, `Workflow (full detail in `PROJECT_NOTES.md`)`, `Documentation (maintained from day one)`, `Implementation Discipline` (+791 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **26 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DepthAllocator` connect `DepthAllocator` to `PriorityScore`, `market_depth_framework/__init__.py`, `StrikeHistory`, `Instrument`, `numbers`, `allocator`, `test_framework_depth_allocator.py`?**
  _High betweenness centrality (0.226) - this node is a cross-community bridge._
- **Why does `Config` connect `Config` to `DuckDBAnalyticalWriter`, `DepthProbeResult`, `replay.py`, `SQLiteLiveWriter`, `RecorderOrchestrator`, `FakeInstrumentManager`, `test_replay.py`, `load_config`, `websocket_client.py`, `utils.py`, `__main__.py`, `Milestone`, `processor.py`, `RestError`, `.resolve_filename`, `RawTickFileWriter`, `RestClient`, `DepthWebSocketClient`, `InstrumentManager`, `TickProcessor`, `config.py`, `StrikeHistory`?**
  _High betweenness centrality (0.162) - this node is a cross-community bridge._
- **Why does `Instrument` connect `Instrument` to `test_framework_capability_layer.py`, `test_framework_window_manager.py`, `market_depth_framework/__init__.py`, `test_framework_subscription_manager.py`, `test_framework_subscription_state.py`, `WindowManager`, `SubscriptionPlan`, `PriorityScore`, `DepthAllocator`, `leg`, `test_framework_models.py`, `rank_candidates`, `leg`, `MarketContext`, `.candidates`, `chain`, `AtmDistancePolicy`, `SymbolCodec`, `TagSymbolCodec`?**
  _High betweenness centrality (0.095) - this node is a cross-community bridge._
- **Are the 25 inferred relationships involving `Instrument` (e.g. with `DepthAllocation` and `DepthAllocationDiff`) actually correct?**
  _`Instrument` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 49 inferred relationships involving `FrameworkConfigError` (e.g. with `BudgetAllocator` and `BrokerCapabilityLayer`) actually correct?**
  _`FrameworkConfigError` has 49 INFERRED edges - model-reasoned connections that need verification._
- **Are the 50 inferred relationships involving `load_config()` (e.g. with `main()` and `main()`) actually correct?**
  _`load_config()` has 50 INFERRED edges - model-reasoned connections that need verification._
- **Are the 53 inferred relationships involving `write_config()` (e.g. with `_write()` and `test_collects_all_errors()`) actually correct?**
  _`write_config()` has 53 INFERRED edges - model-reasoned connections that need verification._