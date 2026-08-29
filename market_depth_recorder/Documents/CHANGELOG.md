# Changelog — Market Depth Recorder

Dated running log; one entry per phase/iteration (what changed, why, affected files, deferred work).

## 2026-08-29 — Docs: reconcile the Plan_002 phase roster and add an outstanding-work register

**Why.** A pending-work reconciliation against Plan_002 found the authoritative plan contradicting
itself. The §22 phase roster still carried the gate *criteria* for F5, F6, F7 and F9 with no outcome,
and recorded F8 as "SCOPE PROPOSED 2026-08-26, awaiting approval ... no code written" — while §22.10
and the §23 closing list both record F8 approved and implemented on 2026-08-27. A reader working
top-down was told the recorder integration had never been approved. Separately, the eight remaining
UNKNOWNs lived only in `plans/Plan_002_evidence/Plan_002_F10B_Evidence.md`, which is the record of one
session; nothing in the live plan carried them forward.

**What changed.** `plans/Plan_002_market_depth_framework_implementation.md` only.

- Roster rows F5, F6, F7, F9 now state the outcome alongside the criterion, in the same form as
  F1-F4; F7 also points at `Documents/evidence/depth_transition_20260826/` rather than the folder root.
- The F8 row now reads **APPROVED and IMPLEMENTED 2026-08-27**, naming forks F15=A / F16=A and
  recording that F17 was opened at that gate and closed by F7.6.
- The narrative sentence asserting F8 "stays blocked until F7.5 passes its gate" is put in the past
  and pointed at the new register. The identical sentence inside §22.8 is **left alone**: it is a
  historical phase-gate record and was true when written.
- New **§23.1 Outstanding-work register**, in three deliberately distinct categories — OPEN FOLLOW-UP
  (4 items), UNKNOWN / NOT TESTED (5 boundaries), HISTORICAL / CLOSED (5 records).

**Why three categories.** Filing a deliberately untested boundary as a to-do manufactures an
artificial backlog. The premium ceiling above 15 is `NOT TESTED` because fork F24=A prohibits probing
it, and complete reconnect coverage is an evidence boundary, not an unexecuted phase. Neither is work.
Only the first category is.

**One finding recorded, not acted on.** The `health.json` `PermissionError` events now have a
concrete mechanism in code: `atomic_write` ends in `os.replace` (`utils.py:134`), which raises
`WinError 5` on Windows while another process holds the destination open, and the watcher opens the
file every 15 s (`f10_live_monitor.py:110-113`). Both sides already absorb it (`main.py:482`,
`f10_live_monitor.py:481`). This strengthens the inference but does not prove those two specific
events were that race, so the status stays `INFERRED` rather than being promoted to `OBSERVED`.

**Verification.** `git diff --check` clean; `config.yaml` byte-identical to HEAD and the framework
still disabled; no source file touched; CRLF preserved (3139 -> 3197, zero bare LF, byte-level rewrite
with a per-file assertion — `sed -i` is never used on these documents, issue #8); 14 relative
markdown links all resolve; full suite **1504 passed**.

**Deferred.**
- The F10B evidence labels "UNKNOWN #1/#2" in its body in the opposite order to its own §18 list
  (body: #1 reconnect, #2 ceiling; §18: 1 ceiling, 2 reconnect). §23.1 cites the §18 ordering and
  names each item so it cannot be misread, but reconciling the labels in the evidence document is a
  separate correction and was **not** made here.
- The `_JOIN_TIMEOUT_SEC` sizing, the 40-of-361-minutes allocation question, the `PermissionError`
  cause, and the flaky `test_real_four_thread_pipeline_end_to_end` remain OPEN FOLLOW-UP.
- The exposed OpenAlgo API key in `config.yaml` is separate security work with its own remediation
  path (rotation) and is deliberately outside this register and this commit.
- F1/F2/F3 name both a fork and a phase. Deliberately **not** renumbered.

## 2026-08-29 — Docs: evidence/ grouped one folder per experiment, with an index

**Why.** Renaming `patches/` to `evidence/` fixed the name but left 14 files flat, and inspecting
them showed a distinction the flat listing hid: the 8 JSON files are machine-generated probe captures
(`is_broker_evidence`, `schema`, `observations` written by the `tools/fyers/` probes), while the
`.md` files are human-written narrative. Five of those captures had **zero** inbound references, so
flat they read as orphans; grouped with the run that produced them they are plainly the raw data
behind a finding. Grouping by experiment keeps a capture attached to its narrative.

**What changed.** 14 files moved into three per-experiment folders, all recorded by git as pure
renames, plus a new index:

- `Documents/evidence/README.md` (new) — what each experiment establishes, which document is
  canonical, which questions remain UNKNOWN, and the rule for where a new experiment goes
- `fyers_tbt_concurrency_20260714/` — the canonical FROZEN reconciliation and its two probe captures
- `depth_transition_20260826/` — the 20-section evidence document, its runbook, and six captures
- `openalgo_platform/` — `OPENALGO_PATCH.md`, its reference diff, and the reconnect-storm issue

104 path references were rewritten across 32 files. Every source-file occurrence is a comment or
docstring; no functional path and no behaviour changed.

**One broken link caught and fixed.** `depth_transition_probe_20260826.md` linked to
`tbt_concurrency_reconciliation_20260714.md` as a bare same-folder relative link, which stopped
resolving once the two files landed in sibling folders. It is now `../fyers_tbt_concurrency_20260714/`.
A repo-wide relative-link check was added to the verification pass for this move: all markdown
relative links in the repository resolve.

**Why three folders and not more.** The split follows experiment boundaries, which are the boundaries
the captures already have. It is not a topic taxonomy: `openalgo_platform/` is separated because a
platform defect must never contaminate the broker protocol characterization, which is the same
reasoning `openalgo_tbt_reconnect_storm_issue.md` states in its own header.

**Unchanged.** No file was renamed, only moved, so bare-filename references stay valid and the dates
stay legible when a file is opened alone. The platform-scope exception keeping the OpenAlgo artifacts
inside the recorder rather than in `../openalgo_docs/` still stands and is still open for a separate
decision.

**Affected files.** 14 moved; `Documents/evidence/README.md` (new); 32 files reference-rewritten;
`Documents/CHANGELOG.md`.

**Deferred.** `graphify-out/` and the `__pycache__` byte-matches still carry the old paths; both
regenerate. The MB/MiB artifact in the formal F10B evidence remains open. `test_integration.py::
test_real_four_thread_pipeline_end_to_end` failed once under full-suite load during this work and
passed in isolation and on a clean re-run — a pre-existing flaky threaded test, unrelated to these
documentation moves, worth investigating on its own.

## 2026-08-29 — Docs: Documents/patches/ renamed to Documents/evidence/; Plan_001 phase notes filed with their plan

**Why.** Only 3 of the 15 files in `Documents/patches/` were patches. The folder had become a drawer
holding three unlike things: broker-protocol evidence, OpenAlgo platform artifacts, and one
plan-phase narrative. The name pointed the wrong way twice, because `a154f27` had already given real
OpenAlgo platform patches a separate home. Renaming now cost 146 reference rewrites; the count only
grows with every experiment added.

**What changed.** 16 files moved, all recorded by git as pure renames:

- `Documents/patches/` -> `Documents/evidence/` (14 files: the `tbt_*` and `depth_transition_*`
  protocol evidence, `OPENALGO_PATCH.md`, `openalgo_fyers_tbt_channels.patch`,
  `openalgo_tbt_reconnect_storm_issue.md`)
- `Documents/patches/Phase9_notes.md` -> `plans/Plan_001_evidence/Phase9_notes.md`
- `Documents/phase_10E_notes.md` -> `plans/Plan_001_evidence/phase_10E_notes.md`

146 path references were rewritten across 35 files, including `CLAUDE.md`, the FROZEN protocol block
in `market_depth_recorder_design.md`, `PROJECT_NOTES.md`, six source files (`eod_report.py`,
`capabilities.py`, `capability_layer.py`, and three `tools/fyers/` probes), two test modules, and
`config.example.yaml`. Every source-file occurrence is a comment or docstring; no functional path,
no behaviour, and no protocol claim changed. Bare-filename references were already path-independent
and are unchanged.

**Why the phase notes moved with the plan, not with the evidence.** `Phase9_notes.md` and
`phase_10E_notes.md` are plan-phase narrative, the same kind as the two F10B documents relocated
earlier today. Leaving them behind would have meant applying that rule to Plan_002 and not to
Plan_001. They travel together because `phase_10E_notes.md` is the document that supersedes Phase 9's
5-per-channel finding, and the supersession is hard to follow with the two filed apart.

**Why the folder was not split further.** The `tbt_*`, `depth_transition_*` and OpenAlgo-patch files
all share one lifetime: durable, frozen, cited from source. Subfoldering them by topic would buy
tidiness, not correctness, and 14 files is a browsable directory. `evidence/` rather than
`broker_evidence/` because `OPENALGO_PATCH.md` is a platform change, not broker evidence.

**Not moved.** `OPENALGO_PATCH.md` and `openalgo_fyers_tbt_channels.patch` stay inside the recorder
rather than joining `../openalgo_docs/`, despite the `a154f27` precedent. Moving them would cross the
project-scope boundary in `CLAUDE.md`, and `PROJECT_NOTES.md` already records them as a deliberate
platform-scope exception. Open for a later decision.

**Note on earlier entries.** Path references in older entries were repointed to `Documents/evidence/`
so that nothing in this file dangles, following the convention set in the entry below. The one
exception is that entry itself: its rename mapping and its prose state where those files were on
2026-08-29, so its `Documents/patches/` paths are left standing as the historical record. Git history
records every original path.

**Affected files.** 16 moved as above; 35 files reference-rewritten; `Documents/CHANGELOG.md`.

**Deferred.** `graphify-out/` and the `__pycache__` byte-matches still carry the old paths; both
regenerate and are not hand-edited. The MB/MiB artifact in the formal F10B evidence remains open.

## 2026-08-29 — Docs: F10B phase records relocated to plans/Plan_002_evidence/

**Why.** `Documents/patches/` holds two different kinds of artifact. Most of it is durable
broker/protocol evidence that outlives the plan which produced it —
`tbt_concurrency_reconciliation_20260714.md` and `OPENALGO_PATCH.md` were produced under Plan_001 and
are now cited by Plan_002, by `market_depth_framework/capabilities.py`, `capability_layer.py`,
`config.example.yaml`, two test modules, `eod_report.py`, the design spec, `PROJECT_NOTES.md`, and
both `CLAUDE.md` files. The two F10B documents are the other kind: narrative records of one phase of
one plan, referenced only by Plan_002 and this changelog. Filing by *kind* rather than by plan number
keeps the protocol evidence at a stable path that code and CLAUDE.md can keep pointing at, and puts
the phase records next to the plan they substantiate without the folder name going stale when a later
plan cites the same protocol facts.

**What changed.** Two files moved, recorded by git as pure renames (100% similarity, no content
edit in the move itself):

- `Documents/patches/f10_live_validation_20260828.md` -> `plans/Plan_002_evidence/f10_live_validation_20260828.md`
- `Documents/patches/Plan_002_F10B_Evidence.md` -> `plans/Plan_002_evidence/Plan_002_F10B_Evidence.md`

15 path references were repointed across four documents (this changelog 5, Plan_002 4, and the two
moved documents 5 and 1 for their self- and cross-references). Bare-filename references were already
path-independent and are unchanged.

**Deliberately not moved.** The `depth_transition_*` probe document, runbook, and five JSON captures
stay in `Documents/patches/`. They were produced during Plan_002 but they are broker-protocol
findings, not plan-phase narrative, and `tools/fyers/depth_transition_probe.py`, `tools/fyers/README.md`,
`Documents/ARCHITECTURE.md` and `Documents/market_depth_framework.md` cite them as such. The same
reasoning keeps every Plan_001-era TBT artifact where it is.

**Note on earlier entries.** The path references inside the 2026-08-28 entries below were repointed to
the new location so that no path in this file dangles. Those files were at `Documents/patches/` when
those commits were made; git history records the original paths, and the rename commit records the
mapping.

**Affected files.** `plans/Plan_002_evidence/f10_live_validation_20260828.md` (moved),
`plans/Plan_002_evidence/Plan_002_F10B_Evidence.md` (moved), `Documents/CHANGELOG.md`,
`plans/Plan_002_market_depth_framework_implementation.md`.

**Deferred.** `graphify-out/` still indexes the old paths; it regenerates on the next
`graphify update .` and is not hand-edited. The MB/MiB artifact in the formal F10B evidence
("closed at 552 MB (from 578 MB...)" on one file whose byte count never changed) remains open from
the 2026-08-28 entry.

## 2026-08-28 — F10B evidence: forensic record and three artifact-driven corrections

**Why.** The F10B record committed as `18e9dd6` states the result. It did not state *how* the result
was obtained, which intermediate readings were wrong, or what else was seen on the way. A detailed
forensic record was written to close that gap — and, in re-deriving the original document's numbers
from the primary artifacts, it found three factual discrepancies in it.

**What landed.** `plans/Plan_002_evidence/Plan_002_F10B_Evidence.md` (new, 1266 lines): a 24-section
engineering experiment record covering the F10A preparation and its verification, the F10B preflight
gate, the activation, the three-layer monitoring architecture and what each layer structurally cannot
see, the sampling-coverage measurement, a minute-by-minute session timeline, a nine-scenario matrix
(A-I), the performance results, the Tier 0 and reconnect verification methodologies as executed, the
broker-refusal analysis, an 11-row issue/anomaly table, six correction subsections, a
claim-by-claim OBSERVED/INFERRED/UNKNOWN ledger, the D18 decision, a 17-block reproducibility
appendix, a six-level evidence hierarchy, twelve lessons, and a final audit checklist. Where a detail
could not be substantiated it is marked `NOT RECOVERABLE FROM AVAILABLE ARTIFACTS` rather than filled
in from memory — two F10A invocations are so marked.

**The three corrections.** All are artifact-driven, all are applied to
`plans/Plan_002_evidence/f10_live_validation_20260828.md` and `plans/Plan_002...md` §22.13.5a, and **none
changes the D18 verdict** — every one concerns the session narrative outside the 13:56:29-14:36:32
measurement window.

- **D1 — watcher gap count.** Was "one 62 s gap ... otherwise continuous". The timeline holds **two**
  gaps (**62.2 s** 10:41:03->10:42:05, **40.4 s** 11:05:07->11:05:47) and **three** watcher `meta`
  rows. A watcher/harness issue, not a recorder failure: `restart_count = 0` and the Tier 0 stream is
  continuous (one HEADER, one EOF). Both gaps precede 11:06; the measurement window is covered by 160
  consecutive samples with no gap.
- **D2 — the absolute `refused=0` claim.** Was `failed=0 refused=0` as a whole-session fact, plus
  "the framework never saw the refusals". In fact: 4574 dispatch lines, `failed=0` on all; **4573**
  with `refused=0`; pass **1084** at **11:28:58.570** logged `sent=6 failed=0 refused=2 skipped=157
  premium=13/15`, with pass **1085** recovering ~0.5 s later at `premium=15/15`. The dip was shorter
  than the 15 s watcher cadence, and a refusal is not a `plan_failure`. The 30 broker records are
  **15 logical events** (double-logged); **the framework saw 1 and was unaware of 14.** The finding
  to carry forward: a steady `premium_legs = 15` with `plan_failures = 0` **cannot be read as proof
  that no refusal occurred**. Classified as an observability / evidence-boundary finding, **not a
  framework defect**.
- **D3 — refusal clustering.** Was "4-refusal clusters at exactly the connect and reconnect
  timestamps ... and never between them". The **11:28 cluster holds 2 records and falls at a
  `window_change`**, no disconnect nearby. Restated at the supported strength: **every observed
  refusal cluster coincided with a moment at which premium legs were being requested or re-requested
  — initial fan-out, reconnect, or `window_change`.** The internal OpenAlgo/FYERS allocation
  mechanism stays UNKNOWN; the 5-per-connection / 3-connection reading stays INFERRED.

**Method note.** The corrections were found by treating the primary artifacts as authoritative and
re-deriving the committed numbers rather than trusting them: D1 from the timeline's `meta` rows and
sample deltas, D2 from `grep -cE "refused=[1-9]"` against the `premium=N/15` histogram (the earlier
bare-word `refused` filter matched all 4574 benign lines and hid it), D3 from the refusal timestamps
cross-referenced against the dispatch log. Four further differences were checked and found to be
**reconciliations, not contradictions**: the depth-record count (401,716 vs 401,881 — different
window boundaries), the restoration latency (+10.6 s vs +9.8 s — different reference epoch), "30
refusals" (records vs logical events), and "139 at 5 levels" (135 at exactly (5,5) plus 4 reaching 5
buy-side).

**Affected files.** `plans/Plan_002_evidence/Plan_002_F10B_Evidence.md` (new);
`plans/Plan_002_evidence/f10_live_validation_20260828.md` (D1/D2/D3 corrected in place, superseded readings
stated rather than erased, provenance note added); `plans/Plan_002...md` (§22.13.5 gap item
corrected, §22.13.5a correction record added, UNKNOWN restatements sharpened); this changelog. **No
source, config, test or runtime file changed.** `18e9dd6` is preserved unamended as the original F10B
checkpoint.

**Deferred.** (a) The formal evidence's "the live DB closed at 552 MB (from 578 MB mid-teardown)"
reads a **MB/MiB unit artifact** on one unchanged 578,785,280-byte file (= 552.0 MiB) as a size
reduction. Flagged in the forensic record §16.6; **left unchanged in the formal evidence** because it
is outside the three approved corrections. (b) D18 remains **CLOSED**; UNKNOWN #2 (broker ceiling
above 15) remains **UNKNOWN / NOT TESTED**, never probed per F24=A.

## 2026-08-28 — F10B: live validation at true scale (closes D18)

**Why.** F10A prepared everything offline; D18 could only close on a live session. One session was run
end to end on 2026-08-28 with the framework genuinely enabled (F22 = A).

**What happened.** Preflight confirmed the hard gate (`NIFTY/NFO -> 50`, `SENSEX/BFO -> 5`). Recorder ran
10:12:01 to 15:35:00 IST; the read-only watcher took 1293 samples at 15 s (**two** gaps at watcher
restarts — 62.2 s and 40.4 s, both before 11:06; corrected 2026-08-28, see the entry below).
`config_hash` unchanged throughout, as predicted from `config.py:108-118`.

**The measurement D18 needed.** For **40 minutes (13:56:29-14:36:32)** the recorder ran the true-scale
hybrid: **15 NIFTY legs at a full 50x50 book plus 139 legs @5, 172 contracts, 401,716 depth records** —
verified per symbol against the Tier 0 raw, not inferred from a counter. Envelope: `cycle_ms_p50`
17.2 ms median (soft target 30), `cycle_ms_max` 44.1 ms peak (hard 500), RSS 97.7 MB peak (soft 500),
proc/db/raw queue peaks 4/2/37 against 45,000/45,000/90,000, `degraded_level` 0, **zero drops on all
three counters**. Tripling the premium legs over P10-E did not degrade cycle time. **D18 CLOSED.**

**UNKNOWN #1 resolved.** Six reconnects occurred naturally; **none was forced** (F23 = A). At the
14:14:03 reconnect the identical set of 15 premium symbols resumed 50-level delivery, first 50-level
packet at **+10.6 s**. **UNKNOWN #2 (broker ceiling above 15) stands** — never probed, per F24 = A.

**Operational finding.** `premium_legs` was 15 all session and the framework logged `plan_failures=0`
with `refused=0` on 4573 of 4574 dispatches, because OpenAlgo accepted the requests at its own layer;
the broker refused downstream. OpenAlgo's `log/errors.jsonl` carries **30** `symbol count exceeds
limit: 5` records = **15 logical refusal events**, each double-logged. Every cluster coincides with a
moment premium legs were being requested or re-requested — initial fan-out, reconnect, or a
`window_change`. Delivery sat at 5 legs for 274 of 361 observed minutes. **Counters alone would have
reported a fully successful 15-leg session**; only the packet-derived `delivering_legs` and the Tier 0
raw showed otherwise. (Corrected 2026-08-28 — see the entry below: one dispatch *did* record
`refused=2`, and the clustering claim was too strong.)

**Defects recorded (none affected the result).** Two transient health-file write failures
(`PermissionError [WinError 5]` on `os.replace`, `utils.py:134`). At teardown, `SQLiteLiveWriter did not
join within 10s` (`main.py:467`) with `db_queue_size = 0` — close/checkpoint cost on a 578 MB database,
not unwritten rows. EOF marker written cleanly (`record_count = 3,043,790`).

**Affected files.** `plans/Plan_002_evidence/f10_live_validation_20260828.md` (new, the F26 evidence);
`plans/Plan_002_market_depth_framework_implementation.md` (D18 closed in §5, F10B checklist ticked, phase
table updated); this changelog. `config.yaml` was flipped to `enabled: true` for the session and back to
`false` at teardown — `git diff --stat config.yaml` is empty.

**Deferred.** (a) Why the 15-leg condition held for only 40 of 361 minutes — OpenAlgo's TBT connection
allocation is uninstrumented here and the mechanism is INFERRED, not proven; this is an
allocation-consistency question, separate from D18. (b) The `_JOIN_TIMEOUT_SEC` budget may be too small
for a full-size trading day. (c) Disk headroom proved a non-issue: the rebuild finished 15:56:38 (`rc=0`,
2 stores, lock released) producing **1872 MB from the 314 MB raw (~6x, not the ~25x projected from
2026-07-07)**, leaving 8.3 GB free. The live SQLite closed at 552 MB.

## 2026-08-27 — F10A: live-validation preparation (forks F22-F26)

**Why.** Plan_001 **D18** is open because performance at true scale — up to 15 legs at 50-level plus the
hybrid remainder — has never been measured; P10-E measured `<=5` NFO @50 plus ~120 SENSEX @5. Closing it
needs one live session (F10B). F10A is everything that can be decided and verified with the market shut,
so that nothing is improvised at 09:15.

**Forks resolved.** F22 = A (the framework runs genuinely enabled — shadow mode cannot demonstrate
subscription behaviour at budget) · F23 = A (natural reconnect only; a forced reconnect risks the very
run being measured) · F24 = A (operate at the configured budget of 15, never probe the ceiling) ·
F25 (criteria defined here, derived from existing system semantics) · F26 = A (dated evidence document
at the F7 standard, separating OBSERVED / INFERRED / UNKNOWN).

**The audit came first, and it said do not build.** Everything D18 asks for is already published to
`health.json` every cycle: the three queue depths, the three drop counters, `degraded_level`,
`cycle_ms_p50` / `cycle_ms_max`, `rss_mb`, `active_contracts`, `actual_depth`, `restart_count`, plus the
framework's own planning view (`processor.py:618`) and the FEED execution view
(`websocket_client.py:780-793`: `plans_executed`, `plan_failures`, `desired_legs`, `premium_legs`,
`effective_budget`, `delivering_legs`, `claimed_wire_symbols`). **No second monitoring system was
written.** The only missing piece was a timeline, a classifier, and an evidence skeleton.

**What landed**

| File | What it is |
|---|---|
| `tools/validation/f10_live_monitor.py` | Read-only watcher: samples `health.json`, appends a JSONL timeline, applies the F25 rules with a 3-sample sustain, renders the F26 evidence skeleton |
| `tests/test_f10_live_monitor.py` | 36 offline tests over synthetic health snapshots, including two source-level guards |
| `Documents/F10_LIVE_VALIDATION.md` | The F10B runbook: preconditions, the enable step, run sequence, abort table, kill switch, and what the evidence may not claim |
| `plans/Plan_002...md` §22.13 | Forks F22-F26, the threshold derivation, and both checklists |

**Every threshold has a source.** Queue criticals are `critical_watermark_pct` of the configured caps
(the same lines PROCESSOR derives `_crit_q` from, `processor.py:197-198`); `cycle_ms` soft is
`eod_report._CYCLE_MS_TARGET` (30 ms) and `rss_mb` soft is `_RSS_MB_TARGET` (500 MB); the instant aborts
are the lossless-raw invariant and the premium-budget invariant. Exactly one number is **not** derived
from the system — the 2048 MB RSS hard limit, which is a fact about an 8 GB host — and it is labelled
**HOST** in both the tool and the runbook rather than dressed up as a system figure.

**The watcher cannot touch the recorder.** No recorder import, no socket, no lock, no thread, one
appended file handle under `with`, and **no kill path** — `os.kill`, `SIGTERM`, `SIGINT`, `terminate(`
and `taskkill` are asserted absent from its source. Aborting is the operator's act, and it is
framework-first: flip `enabled: false`, stop, restart. The raw writer reopens the same day's file in
append mode (`file_writer.py:122`) and both readers skip the interior `EOF` / `HEADER` records
(`replay.py:176`, `framework_replay.py:189`), so stopping mid-session harms neither the audit trail nor
any later rebuild.

**Verified offline, not asserted.** `load_config` accepts `enabled: true`, and `compute_config_hash` is
byte-identical with the flag on and off — the framework block is outside the hashed scope
(`config.py:108-118`), so today's raw log stays comparable with every previous session. No second config
file was created: a copy of `config.yaml` would duplicate the live `openalgo.api_key` into an untracked,
un-ignored file.

**Unchanged.** No recorder runtime file was touched — not the pipeline, the allocators, the Broker
Adapter, `framework_bridge.py`, or F7/F8 behaviour. **The framework is still disabled in the committed
config.** Full suite **1504** (1468 + 36), run twice, no flakes.

**Deferred.** F10B itself: no broker was contacted, no probe was run, nothing was enabled. Both UNKNOWNs
stand by design — the broker's true premium ceiling above 15 (F24 = A never probes it) and reconnect
depth restoration (F23 = A only observes a natural one).

## 2026-08-27 — F9: the framework determinism harness (forks F18-F21)

**Why.** F8 wired the framework into the live recorder behind a flag, but the only way to see a whole
session of allocation behaviour was to run a live session. F9 makes that reproducible offline: replay a
recorded tick stream through the **real** orchestrator and adapter, log every rebalance pass, and assert
that two replays of the same recording are byte-identical. `replay.replay_file` could not be reused —
it drives `TickProcessor.ingest()` / `emit_second()` directly and never calls `run()`, so a Tier-2
rebuild is deliberately framework-free (F8 asserts it). F9 therefore adds a **second driver**
(fork F18 = A); `replay.py` is untouched.

**Forks resolved.** F18 = A (recorder-side driver with a recording transport), F19 = A (plain diffable
`.jsonl` allocation log plus a terminal digest, `--verify` reporting the first divergence),
F20 = A (`tools/` soak script plus a bounded automated soak test), F21 = C (synthetic session is the
normative fixture; one real recording replayed read-only for the written report only, under the
authorization recorded verbatim in Plan_002 §22.12.2.1).

**What landed.**

| File | Change |
| --- | --- |
| `framework_replay.py` | New. Drives `FrameworkOrchestrator` + `BrokerAdapter` over a raw `.jsonl.gz` on a virtual clock, writes one canonical JSON record per pass plus a `DIGEST` record, checks three invariants per pass, and implements `--verify REFERENCE CANDIDATE`. Own CLI entry point — no existing command line changed, `main.py` untouched. Fails closed on a missing recording (exit 2, writes nothing). |
| `tools/validation/framework_soak.py` | New. Replays N times (default 2), requires byte-identical output, summarises trigger mix, action kinds, wire ops, occupancy histogram, tier-flip churn, shortest observed flip gap vs the configured cooldown, wall time, and peak RSS; `--report` writes markdown with a provenance block and a "What this is not" section. |
| `tests/test_framework_replay.py` | New, 32 tests over a short synthetic session (1436 -> 1468). Determinism, the invariant matrix, `--verify`, fail-closed, simulated confirmation, and the bounded soak. |
| `Documents/framework_replay.md` | New module reference. |
| `Documents/framework_soak_report.md` | New. The F9 written soak report. |
| `Documents/ARCHITECTURE.md`, `Documents/market_depth_framework.md` | F9 sections. |
| `plans/Plan_002_...md` | §22.12 decisions, the verbatim F21-C authorization, the ticked checklist, measurements, and the per-case test mapping. |

**What is real and what is simulated.** Real: the orchestrator and every layer, the adapter, wire
rendering, the connection pool, the budget, release-before-claim ordering, spot prices from the
recording's own packets, and option depth packets fed verbatim to `observe()`. Simulated: the broker
(a list), and delivery confirmation for legs the recording does not carry
(`--confirm-after-passes`, default 1, counted per record and in the digest). **Nothing here is broker
evidence.** Reconnect depth restoration and the real premium ceiling remain **UNKNOWN**.

**Measured, real recording** (`market_depth_raw_20260714.jsonl.gz`, read-only, sha256 recorded in the
report): 319,445 packets, 772 passes (1 initial / 508 interval / 263 window_change), 340 subscribes +
34 upgrades + 34 downgrades, peak premium occupancy **15 of an effective budget of 15**, **zero**
violations of all three invariants, two replays byte-identical, ~19 s wall for both, peak RSS 46.8 MB,
shortest observed gap between two flips of one leg 30.072 s against a configured 30 s cooldown. The 313
zero-occupancy passes are exactly the 313 passes in which an underlying still had no spot — no window,
so no premium leg. 236 of the confirmations were synthesized by the driver, not by a broker.

**Honest note on the test matrix.** Two matrix assertions were narrowed during implementation rather
than the framework changed: investigation showed pass 1 fires on the first NIFTY spot packet while
SENSEX is still `no_spot`, so SENSEX's resolution at pass 2 is a genuine `window_change`. Both narrowed
tests carry a positive assertion that the skipped situation actually occurred, so neither can pass
vacuously. Recorded in Plan_002 §22.12.6.1.

**Unchanged.** `replay.py`, `processor.py`, `websocket_client.py`, `main.py`, `framework_bridge.py`,
`broker_adapter.py`, the Tier-2 output, the four threads, the three queues, the lock model, reconnect
semantics, and the capacity model. No thread, lock, socket, subprocess, or FD was added to any live
path; the driver's only descriptors are the gzip reader and the log writer, both under `with`. Recorder
`config_hash` byte-identical to HEAD's.

**Counts.** Full suite **1468** (run twice: 115.78 s and 78.18 s, identical, no flakes).

**Deferred.** F10 (true-scale live validation) has not started. Both UNKNOWNs stand.

## 2026-08-27 — F7.6: the adapter releases what it owns, not what the plan assumed (fork F17)

**Why.** F8's completion gate opened fork F17 and left it unresolved. A leg re-tiered **before its first
packet arrives** is absent from the delivery-derived live snapshot, so `reconcile` spells it a plain
`SUBSCRIBE`; the adapter, deriving its release from the action's kind, claimed the new wire spelling
while still holding the old one, and the stale premium record kept its pool slot. Measured with a
two-slot budget: the new premium claims came back `refused` while the unreleased incumbents held both
slots. The user approved **option A** — fix it in the adapter, as its own phase before F9.

**What landed.**

| File | Change |
| --- | --- |
| `market_depth_framework/broker_adapter.py` | `_execute` iterates the new `_obsolete_tiers(action)` instead of the single `_source_tier(action)`; `_obsolete_tiers` returns the tiers of the wire legs the adapter holds for the same `Instrument` at another tier (`REQUESTED` or `DELIVERING` only), falling back to the plan's declared source tier so the existing "nothing of ours to release" `skipped` record is preserved. Module docstring records the invariant and the owned/observed distinction. |
| `tests/test_framework_broker_adapter.py` | New section 11, 11 tests (124 -> 137). |

**The invariant added.** For a given `Instrument`, the adapter must never claim a new wire tier while an
obsolete wire tier is still adapter-owned — **even when neither leg has yet produced a delivered packet.**

**What F17 was fixed by, and what it was not fixed by.**

| Fixed | Not fixed by |
| --- | --- |
| The adapter no longer loses an unobserved dispatched wire leg during a retier: it releases the tier it owns, then claims. | Changing observed-depth semantics. `live_snapshot()` is still delivery-derived and an owned leg is still absent from it. |
| | Inventing acknowledgements. An ack — including one carrying `depth: 50` — still confirms nothing, and a test asserts it. |
| | Assuming reconnect behaviour. Still UNKNOWN, still unclaimed. |
| | Assuming broker capacity. The two-slot test is a deterministic adapter test over the logical capability model, not evidence about the real FYERS ceiling, which stays UNKNOWN. |
| | Modifying `SubscriptionManager`, `SubscriptionState`, `Instrument`, or `desired vs live`. Untouched. |

**Root cause reproduced by test.** With the pre-F7.6 derivation restored (a test-only monkeypatch of
`_obsolete_tiers` back to `_source_tier` alone), **7 of the 11 new tests fail**. The other 4 are the
invariance guards — the observed-transition regression, the no-unsubscribe-when-nothing-is-owned guard,
the no-duplicate-release guard, and `owned is still not observed` — which must pass in both worlds.

**Unchanged.** Release-before-claim ordering, the latest-wins mailbox, F15, F16, FEED/PROCESSOR
ownership, four threads, three queues, the lock model, reconnect semantics, the capacity model, the
premium-slot value, the F7 evidence/probe/runbook/raw captures, and every recorder integration file
(`websocket_client.py`, `processor.py`, `main.py`, `framework_bridge.py`, `orchestrator.py`). No thread,
lock, socket, subprocess, or FD was added. Recorder `config_hash` unchanged.

**Counts.** Adapter suite 137, framework suite 1068, full suite 1436 (run twice, identical, no flakes).

**Deferred.** F9 (replay/determinism) and F10 (true-scale live validation) have not started. Reconnect
depth restoration and premium-slot accounting remain UNKNOWN.

## 2026-08-27 — F8 recorder integration: the framework goes live behind a flag

**Why.** F7.5 ended with an executable plan and nothing to execute it against: `processor.py`,
`websocket_client.py`, and `main.py` were explicitly out of scope. F8 is that wiring — and the two
design forks it forced, F15 (where FEED drains the plan mailbox) and F16 (who owns an option-leg
subscription when the flag is on), both approved before implementation.

**What landed.**

| File | Change |
| --- | --- |
| `framework_bridge.py` (new) | The one seam. Two `deque(maxlen=1)` mailboxes, the pass driver, fault containment, `build_universe`, `framework_bridge_for`. No thread, lock, queue, or FD. |
| `market_depth_framework/orchestrator.py` (new) | `FrameworkOrchestrator` — one pass: window -> priority -> budget -> depth -> state -> reconcile, plus `due()` (interval / window-change) and `desired()`. |
| `websocket_client.py` | `AdapterTransport`; adapter construction under the flag; F15 drain at the tail of `_on_message` (after the tee) and the end of `_on_open`; F16 ownership gates; `_observe_framework` / `_publish_framework_observation`; `_restore_framework_coverage`; `_close_adapter`; `framework_stats()`; `active_subscriptions` unions the adapter's claimed wire symbols. |
| `processor.py` | `framework_pass()` driven from `run()` — never from `emit_second()` — with its own exception guard; `framework` key in stats when on. |
| `main.py` | The flag is read in exactly one place; one bridge instance shared by PROCESSOR and FEED; `framework` / `framework_feed` health sections only when on. |
| `config.py`, `config.yaml`, framework `config.py` / `__init__.py` / `__main__.py` / `config.example.yaml` | The `market_depth_framework` block in the live config, **excluded from `config_hash`**. |
| `tests/` | `test_framework_integration.py` (47), `test_framework_bridge.py` (15), `test_framework_orchestrator.py` (90) — 152 new tests. |

Framework version `0.7.0 -> 0.8.0`.

**Fork F15 — drain points.** FEED does not poll; while connected it is blocked inside
`transport.run_session()`. The mailbox is drained at the tail of `_on_message` **strictly after
`_tee()`** (the lossless audit path is never delayed by framework work) and at the end of `_on_open`
(the reconnect path). Accepted, documented, tested residual: on a connected but completely silent feed
a pending plan waits for the next packet. With no ticks there is no new window movement, so that plan
is a re-issue of unchanged state — a latency characteristic, not a correctness failure. No timer was
added to remove it, and no fourth lock, no fifth thread, no PROCESSOR-side broker I/O was introduced.

**Fork F16 — ownership.** With the flag ON the framework owns **every** option-leg subscription,
baseline and premium; the DSM keeps spot subscriptions, spot state, boundaries, and health, and
subscribes no strike. Exactly one mechanism restores option coverage on reconnect
(`_restore_framework_coverage()`, not `_resubscribe_all()`), so no leg is subscribed twice. Tests assert
`DSM option-subscription calls == 0` with the flag on and `> 0` with it off, and that a reconnect
produces no duplicate option subscription. `active_subscriptions` still reports actual live coverage,
so the health file does not become misleading.

**Two implementation details resolved in-phase** (neither an ownership/thread/contract change, so
neither a new design fork): the orchestrator's capability layer is exposed through the bridge so FEED's
adapter renders the wire against the very budget the plan was allocated from, instead of resolving a
second layer that could silently disagree; and an **empty** plan is never published, because doing so
would evict a pending plan FEED had not executed while carrying no action of its own (the pass still
counts).

**What stayed UNKNOWN.** Reconnect depth restoration and the premium-slot ceiling. F8 investigated
neither and claims neither: `handle_reconnect()` confirms nothing until packets arrive, and the log line
says so. F10 remains the true-scale live validation phase.

**Audits.** No new thread, lock, queue, socket, or FD in any touched module (diffed construct-by-
construct against `HEAD`); thread count and OS handle count flat over 25 construct/teardown cycles; no
framework or adapter call inside `_spot_lock` or `_sub_lock`; PROCESSOR never touches the adapter and
FEED never runs a pass; importing the framework still pulls in no recorder module.

**The two runs on the wire** (same fake transport, same session: `_on_open` -> one NIFTY spot tick ->
one framework pass -> one depth packet):

| | Frames | DSM frames | Adapter frames | Premium (`:50`) |
| --- | --- | --- | --- | --- |
| Flag OFF | 25 | 25 (`authenticate`, 2 spots, 22 option legs **all at `:50`**) | 0 | 22 -- the old subscribe-everything-deep path |
| Flag ON | 25 | 3 (`authenticate`, 2 spots) | 22 (20 standard + 15 premium across the plan) | **15 == `effective_budget`** |

That is fork F16 in one table: with the flag on the DSM issues no option frame at all, and the premium
tier is bounded by the broker capability instead of being requested for every leg.

**A new design fork surfaced during implementation and is reported UNRESOLVED (F17).** A leg re-tiered
**before its first packet arrives** is planned as a plain add rather than a retier, because `reconcile()`
compares desired against the delivery-derived live snapshot (the §20.4 decision) and an
undelivered leg is not in it. The adapter then claims the new tier without releasing the old one, so
both spellings are held and the stale premium record keeps its slot until it is pruned. Once packets are
flowing the same move plans correctly as `downgrade` + `upgrade` and release-before-claim holds exactly
as designed (asserted in `test_a_promotion_releases_before_it_claims_on_the_real_wire`). Per the F8
directive this was **not** silently resolved: it changes the adapter/state contract, so it is written up
in `plans/Plan_002...` §22.10.9 and put to the gate.

**Flag-off regression.** Every F8 path is inert with the flag off and the old path was not replaced
unconditionally. `config_hash` unchanged: `sha256:8a48bcdd...a1468b`, and a config **with** the
framework block hashes identically to the same config without it.

Framework suite **1057**, full suite **1425** (run twice, identical, no flakes).

**Deferred.** F9 (replay / determinism against the framework) and F10 (true-scale live validation) —
neither started.

## 2026-08-26 — F7.5 Broker Adapter: the layer F7 measured for

**Why.** F6 ended at a deliberate boundary: `reconcile()` produces a plan, and nothing executed it.
F7 then measured what execution actually costs on the wire. This phase is the execution layer,
written **from** that evidence — approved as its own phase (F7.5) so F7 stays what it was, an
evidence phase, and F8 stays what it is, recorder integration.

**What landed.** `market_depth_framework/broker_adapter.py` (~700 lines) and
`tests/test_framework_broker_adapter.py` (126 tests). Version `0.6.0 -> 0.7.0`. Nothing else in the
framework changed; no recorder module changed.

**The four decisions, each traced to a measured fact.**

| Decision | Evidence it comes from |
| --- | --- |
| Wire identity is per tier: `SYMBOL` / `SYMBOL:50`, suffix built from `capability.premium.depth` | CASE A delivered 5 on the bare spelling; CASE B delivered 50 on the suffixed one |
| A retier is **release then claim**, never claim then release | The two spellings are independent concurrent subscriptions, so claiming first transiently holds both legs |
| An acknowledgement never confirms depth; only a delivered packet does | CASE A was acknowledged `success, depth: 50` and delivered 5 levels, uncorrected |
| A leg's tier is fixed at wire-render time, not inferred from level count | Depth is a property of the wire symbol — so a thin book on `SYMBOL:50` is a live premium leg, not a failed one |

**What is deliberately conservative rather than known.** Reconnect depth restoration and premium slot
accounting stayed UNKNOWN in F7, and this phase does not convert either into a claim.
`handle_reconnect()` treats every prior subscription as unknown, reissues the desired coverage, and
confirms nothing until packets arrive; a test greps the module for both "preserves premium depth" and
"loses premium depth" and fails on either. Release-before-claim is the same posture applied to
capacity: it never holds two legs at once, so it cannot overshoot a ceiling nobody has measured.

**What the adapter does not own.** No thread, no socket, no FD. It runs synchronously on the caller's
thread and writes through a `DepthTransport` protocol the caller supplies — it never creates that
transport and never closes it. The four-thread / three-queue contract is untouched. AST tests enforce
all of this: no thread/process/executor/queue construction, no `socket()`/`open()`/`connect()`/
`sqlite3`/`duckdb` call, no real clock read, no import-time statement, no `while` loop (retry is the
next reconciliation pass, not a loop), no hardcoded `15`/`50`/`250`, and no allocator reaching for
`max_connections` / `symbols_per_connection` / `channel_id`.

**Test files updated, and why.** Five existing tests asserted `broker_adapter.py` does not exist.
Those were *scheduling* guards — they held F7 to measuring before anything was written from the
measurement — and each documents itself as a list that shortens as phases land. That ordering was
honoured, so:

- `test_framework_package.py` — `broker_adapter` removed from `LATER_PHASE_MODULES`; the exact-equality
  `__all__` set widened by the eleven new exports.
- `test_framework_capability_layer.py`, `test_framework_priority_policy.py`,
  `test_framework_window_manager.py` — the not-yet-arrived list shortened to `("orchestrator",)`.
- `test_f7_depth_probe_harness.py` — `test_framework_still_has_no_broker_adapter` restated as
  `test_f7_added_no_framework_module` (F7's durable promise: the harness lives entirely under
  `tools/fyers/` and contributed no package module), plus a new guard that the adapter does not import
  the probe.

**No F7 evidence was rewritten.** The evidence document, the runbook, the probe, and the raw captures
are untouched; only tests changed. The seven "does not import broker_adapter" guards in the other
framework test files are unchanged and still carry the layering boundary.

**Affected files.** `market_depth_framework/broker_adapter.py` (new),
`tests/test_framework_broker_adapter.py` (new), `market_depth_framework/__init__.py`,
`tests/test_framework_package.py`, `tests/test_framework_capability_layer.py`,
`tests/test_framework_priority_policy.py`, `tests/test_framework_window_manager.py`,
`tests/test_f7_depth_probe_harness.py`, `plans/Plan_002_market_depth_framework_implementation.md`,
`Documents/ARCHITECTURE.md`, `Documents/market_depth_framework.md`, this file.

**Deferred.** Recorder integration (F8) — wiring the adapter to the FEED-owned WebSocket client, which
is where `DepthTransport` gets a real implementation. Reconnect depth restoration and premium slot
accounting remain UNKNOWN and are measurable only in a live session that can afford a forced
reconnect. Framework suite 769 -> **895**, full suite 1136 -> **1263**. Recorder config hash unchanged
(`sha256:8a48bcdd...a1468b`). F8 not started.

## 2026-08-26 — F7B live measurement: the depth transition, measured

**Why.** F7A had built the instrument; this is the measurement it existed for. Plan_002 §20.1 asks
what a 5 <-> 50 depth transition actually costs on the OpenAlgo/FYERS path, and forbids answering it
from source or from acknowledgements.

**Blocked first, then run.** The 09:17 attempt failed: FYERS' streaming endpoint
(`wss://socket.fyers.in/hsm/v1-5/prod`) was returning Cloudflare `503 Service Unavailable`, and
because `websocket_proxy/server.py:982` calls `adapter.connect()` synchronously inside the async
authenticate handler, the retry loop wedged the proxy's event loop — raw TCP to 8765 completed in
0.01 s while the WebSocket upgrade timed out at 20 s. No evidence was fabricated to fill the gap.
The upstream recovered at ~09:29 and the run proceeded at 09:34.

**What was measured.** Six live invocations on `NIFTY01SEP2624300CE` (NFO, mode 3), one case per
invocation so no case could contaminate the next — the harness cleans up once per process, so
sharing a session across cases would have left legs live between them.

| Case | Requested | Ack said | **Observed** | Verdict |
| --- | --- | --- | --- | --- |
| baseline | 5 -> 5 | 5 | **5 -> 5** | control; requested, reported and observed all agree |
| CASE A `SYMBOL` + `depth:50` | 5 -> 50 | `success`, 50 | **5 -> 5** | **no promotion** |
| CASE B `SYMBOL:50` | 5 -> 50 | `success`, 50 | **5 -> 50** | promotion |
| 50 -> 5 bare re-subscribe | 50 -> 5 | `success`, 5 | **50 -> 50** | no demotion; a second leg appears |
| 50 -> 50 | 50 -> 50 | `success`, 50 | **50 -> 50** | duplicate leg created |
| unsubscribe | — | `success` | **20 -> 0 -> 21** | works end to end |

**The finding.** Depth is a property of the **wire symbol**, not a mutable property of a
subscription. `SYMBOL` and `SYMBOL:50` are two independent subscriptions that stream
simultaneously (CASE B delivered 8 packets under one spelling and 25 under the other in the same
window). The `depth` request parameter does not change delivered depth. There is no in-place
transition: promotion adds a leg, demotion must remove one.

**Why this vindicates the pre-market fix.** CASE A was acknowledged `success` with `depth: 50` and
delivered 5 levels. `actual_depth` was **absent from every acknowledgement**, so the per-leg `depth`
is the request echoed back. A harness that trusted the ack would have concluded the exact opposite
of the truth, and nothing later would have corrected it — no error, no downgrade notice.

**Unsubscribe, measured with a control — an instrument added mid-run.** PART J requires the
*effect*, not the acceptance, and as committed F7A could only measure acceptance: it sent the frame,
parsed the ack, and stopped. So the harness gained `_measure_unsubscribe_effect` **during** the live
session: observe -> unsubscribe -> observe -> **re-subscribe** -> observe. The re-subscribe is what
makes silence meaningful; without it, zero packets could equally mean a quiet market. Result: 20
packets, then 0, then 21. `effect_observed` is set only when the leg went silent *and* provably came
back; silence with no resumption stays UNKNOWN.

That correction is recorded rather than absorbed. The probe as committed now contains the code that
produced the committed evidence, and section 14 of `tests/test_f7_depth_probe_harness.py` covers all
four verdict shapes offline — effect observed, data still flowing after an accepted unsubscribe,
unattributable silence, and nothing delivering to begin with — plus the premium-leg preference, the
per-wire-symbol counting and the transport-failure path. No framework or recorder behaviour was
touched by it.

**Deliberately not measured.** Reconnect depth restoration and premium slot accounting. The proxy
was shared with a live client holding 180 symbols, so forcing a reconnect would have disrupted a
running system; slot accounting requires approaching the broker ceiling, which the safety rules
forbid. Both stay **UNKNOWN** — untested, not "no" — and the adapter contract keeps its
conservative posture (release before claim, re-observe after reconnect) on those grounds.

**Affected files.** `tools/fyers/depth_transition_probe.py` (unsubscribe-effect measurement +
`build_subscribe_request` import); `tests/test_f7_depth_probe_harness.py` (new section 14, 10 tests);
`Documents/evidence/depth_transition_20260826/depth_transition_probe_20260826.md` (filled in, §1-§20, plus the mid-run
instrumentation correction in §1); `Documents/evidence/depth_transition_20260826/depth_transition_probe_runbook_20260826.md`
(executed stamp, the extra measured step); six evidence JSONs under `Documents/evidence/`;
`plans/Plan_002_…md` §22.8/§23; `Documents/market_depth_framework.md`; this file.

**Verified.** F7 harness 93 -> **103 passed**; framework selection **769 passed**, 367 deselected;
full recorder suite **1136 passed**. `market_depth_framework` untouched at 0.6.0, `broker_adapter.py`
still absent, recorder config hash unchanged
(`sha256:8a48bcdd4fca933d1dbc85bd9a5c1dc055403392da0afeb22e629af550a1468b`).

**Deferred.** The Broker Adapter itself (PART Q criterion 6). The contract is derived in §19 of the
evidence document, but no `broker_adapter.py` is written — that is the F7 completion gate awaiting
approval. F8 not started.

## 2026-08-26 — F7A pre-market review: harness corrected against the verified wire format

**Why.** F7A was committed (`f484a96`) and the live run (F7B) was still ~2h from market open, so the
time went into reviewing the harness against the proxy source rather than trusting it. The review
found three defects of one kind: the harness had been written against an **assumed** frame shape and
its tests asserted the same assumption, so code and tests agreed with each other and disagreed with
the wire. All three would have survived a green test suite and surfaced only mid-probe.

**What changed.**

| Defect | Consequence if the live run had gone ahead | Fix |
| --- | --- | --- |
| Book read at `packet["depth"]`; the real frame is an envelope with the book at `packet["data"]["depth"]` | **`observed` would have been `None` for every packet** — every case UNKNOWN, the whole session wasted | `count_depth_levels` unwraps the envelope, still accepting a flat payload |
| Reported depth read at the ack's top level, which has no depth field — it lives in `subscriptions[]` | `reported` always `None`; the acknowledgement question unanswerable | `parse_subscribe_ack` reads the per-leg entry; new `per_leg_entries()` exposes aggregate and per-leg together |
| Informational `message` ("Subscription processing complete") treated as an error | a false error stamped on every successful result | a `message` is an error only on a non-success status, or from a per-leg entry that itself failed |

Also adopted the proxy's `request_id` echo (issue #1376): every probe frame now carries a
deterministic `probe-<seq>` id and the ack is matched on it, so a stray asynchronous frame cannot be
silently mis-attributed to the wrong leg. Each result records `ack_correlated=` and the per-leg ack
detail.

**What did not change.** The confidence lattice is untouched: an acknowledgement still only ever
reaches INFERRED, `effective_depth` still returns `None` unless levels were counted in delivered
packets, and `classify_transition` still returns UNKNOWN unless both sides were observed. Reading the
reported depth out of the right field does not make it evidence. No framework behaviour was added, no
recorder source changed, and the recorder config hash is unchanged.

**Verified.** Source facts 9-13 confirmed at `websocket_proxy/server.py:1246-1256, 1272-1280,
1948-1954` and cross-checked against the recorder's own working reader
(`websocket_client.py:679-688`). Tests 83 -> 93 (10 new, covering the real ack and packet shapes end
to end); framework 769; full suite **1126 passed**; compileall clean; `git diff --check` clean;
framework config OK; recorder `CONFIG OK` with hash `sha256:8a48bcdd…1468b` unchanged; the 20-check
inertness audit still 20/20.

**Affected files.** `tools/fyers/_depth_probe_model.py`, `tools/fyers/depth_transition_probe.py`,
`tests/test_f7_depth_probe_harness.py`, `Documents/evidence/depth_transition_20260826/depth_transition_probe_20260826.md` (§1
source-fact table extended to 13 rows plus the defect table), `plans/Plan_002_…md` (§22.8).

**Deferred.** F7B itself. Environment is not ready: OpenAlgo is not running, and the stored FYERS
`feed_token` is NULL with the auth row last written 2026-08-03 — a fresh post-03:00-IST login is
required before any live run.

---

## 2026-08-26 — Plan_002 F7A: depth-transition probe harness (offline; F7B live evidence pending)

**Why.** Plan_002 §20.1 makes a live depth-transition probe the gate on the Broker Adapter, and §22
fixes the order: F7 measures, the adapter contract is written from the measurement, then F8 integrates.
The question is what actually happens on the wire when the framework retiers a leg between the standard
(5) and premium (50) depth tiers — nothing in the codebase establishes whether that changes an existing
subscription, creates a second one, costs an extra premium slot, or drops ticks in between.

On 2026-08-26 no live probe was possible: the market was closed (01:44 IST), OpenAlgo was not running,
the stored FYERS session was ~23 days stale and long past the daily ~03:00 IST token rollover, and no
`feed_token` was present. The measurement cannot be substituted by anything, so **F7 splits rather than
shrinks**: F7A is the offline harness and evidence infrastructure, F7B is the live measurement.
**F7 is NOT complete until F7B has produced real broker evidence.**

**What changed.**

- **New `tools/fyers/_depth_probe_model.py`** — broker-neutral probe data model. Pure: no network, no
  file I/O, no broker import, and no recorder or framework import (asserted over parsed imports).
  Operations, symbol forms, mechanisms, confidence and outcome are explicit enums.
- **New `tools/fyers/depth_transition_probe.py`** — the runner. Unlike the two TBT probes it does not
  bypass OpenAlgo: it speaks the proxy's own WebSocket protocol, because that is the path the Broker
  Adapter will sit on. One synchronous blocking connection, so no background thread. Dry-run by
  default; `--live` opt-in and additionally refused outside 09:15-15:30 IST unless
  `--allow-outside-session`; hard cap of 2 instruments; no retries, no loops, no background process;
  cleanup unsubscribes every wire symbol it subscribed and closes the socket in a `finally`.
- **New `tests/test_f7_depth_probe_harness.py`** — 83 offline tests, no broker or feed required.
- **New `Documents/evidence/depth_transition_20260826/depth_transition_probe_20260826.md`** — the 20-section evidence document,
  every broker-dependent cell reading `UNKNOWN — LIVE PROBE PENDING`.
- **New `Documents/evidence/depth_transition_20260826/depth_transition_probe_runbook_20260826.md`** — the operator procedure for
  the live run, including the explicit instruction not to run before market data is available.
- **`tools/README.md`, `tools/fyers/README.md`** — tool tables and a full section for the new probe;
  the scope note corrected, since this probe (unlike the TBT ones) imports no platform code.
- **Plan_002 §22.8** — the F7A/F7B checklist and rationale; §23 F7 now reads *F7A prepared / F7B live
  evidence pending*, not complete.

**The design fact that reshaped the probe.** The recorder encodes depth **twice** — a `:50` symbol
suffix (`websocket_client.py:198-200`) *and* a `depth` field (`:558-563`, `:662-666`) — while the proxy
keys a subscription by `(symbol, exchange, mode)`, which excludes depth (`server.py:74,1244`). So a
"depth transition" may be two distinct topics rather than one subscription changing depth. The probe
therefore runs both spellings as separate cases — **CASE A** `SYMBOL` + `depth: 50` and **CASE B**
`SYMBOL:50` + `depth: 50` — and does not assume they are the same operation.

**The invariant that makes the eventual evidence trustworthy.** Requested / reported / **observed**
depth are kept apart and never merged. The proxy echoes the requested depth back when the adapter
reports nothing (`server.py:1254`), so a reply of `depth: 50` may mean nothing at all.
`effective_depth` returns `None` unless the depth was observed in delivered packets, and
`classify_transition` returns `UNKNOWN` unless **both** sides were observed. An accepted request can
never become a recorded depth change; an unattempted operation reports UNKNOWN, never "unsupported".
This is enforced by the model and covered by an explicit test, not left to discipline.

**No broker behaviour is claimed.** No test asserts that FYERS changes 5 -> 50, that unsubscribe is
required or supported, or what a reconnect restores. Dry-run artefacts carry
`is_broker_evidence: false` so they cannot be mistaken for evidence when read back later.

**Resources.** No framework module, no framework thread, no fifth recorder thread, no SUBSCRIPTION
thread, no DB connection, no persistent socket, no broker connection at import. Importing the harness
starts no thread and loads no network client; a dry run performs no socket I/O — both verified by test.
No recorder production behaviour changed: `--validate-config` still `CONFIG OK`, exit 0, config hash
`sha256:8a48bcdd...1a468b` unchanged.

**Verification.** New F7 offline tests **83** green; framework suite **766** green (unchanged); full
suite **1116** green (1033 + 83). `market_depth_framework/broker_adapter.py` still absent, asserted by
test.

**Deferred.** F7B — the live measurement itself: 5 -> 50 in both spellings, 50 -> 5, 50 -> 50,
unsubscribe support and its *effect*, acknowledgement semantics, reconnect depth restoration, and
premium-capacity effects. Then the Broker Adapter contract, written from the evidence. Then F8.

## 2026-08-25 — Plan_002 F6: Subscription layer (state + pure reconciliation)

**Why.** F5 produced each underlying's desired premium/standard tuples. F6 settles the next question and
only that: **what should be subscribed, and how the desired state converges on the live one**. It does
not execute any subscribe/upgrade/downgrade and performs no broker I/O — the actual broker execution and
the evidence for what a depth transition costs on the wire are owned by the Broker Adapter (F7). Splitting
the layer into two modules keeps the data model free of the reconciliation algorithm, so the dependency
runs one way: `subscription_manager.py` imports the plan types from `subscription_state.py`, never the
reverse.

**Decision applied before implementing (Plan_002 §20.4, a NEW F6 fork, not a reopening of F1-F5/F9).**
The `pending` / `failed` feedback model was under-specified — §9 named the fields and §12.7 named their
lifecycle, but §10.6 froze `reconcile` as pure with no mutation and no pending/failed argument, leaving
two incompatible readings (snapshot-derived observability vs. an explicit per-leg broker-ack ledger). It
was resolved to **Option A: snapshot-derived `pending` / `failed`**, recorded with rationale before any
code was written. `pending` and `failed` are **broker-neutral observability**, not a broker
acknowledgement ledger. F6 assumes no per-leg ack API, no FEED per-leg confirmation, and nothing about
whether an unsubscribe exists or whether a bare re-subscribe changes depth — all of that remains F7's to
measure. The acknowledgement *is* the next live snapshot.

**What changed.**

- **New `market_depth_framework/subscription_state.py`.** `SubscriptionState(effective_budget, *, clock)`
  owns the desired coverage and the observability annotations, keyed by `Instrument` (depth is a value —
  membership in `premium_overlay` — never part of the key, never a `:50` wire suffix). `baseline` grows
  monotonically and only `reset()` shrinks it; `premium_overlay` is replaced each pass and bounded by the
  plain-int `effective_budget` (a broker capability passed in, never reconstructed, never a hardcoded
  `15`). Snapshot lifecycle: `record_dispatch(plan)` marks actioned legs `pending` (not broker success)
  and clears them from `failed`; `apply_live(current)` clears any `pending` or `failed` leg the live
  snapshot confirms at its desired depth (the live snapshot is the §5 authoritative observation boundary)
  and **never manufactures** a failure; `record_failed(legs)` is the minimal, no-taxonomy `pending ->
  failed` path. Invariants asserted in code: `premium_overlay ⊆ baseline`, `pending ∩ failed = ∅`. The
  clock is injected with no default; `last_updated` is stamped from it. Also ships the plan/action value
  types `SubscriptionPlan`, `SubscriptionAction`, `ActionKind`.
- **New `market_depth_framework/subscription_manager.py`.** `SubscriptionManager.reconcile(desired,
  current) -> SubscriptionPlan` is stateless, clockless, and **pure**: it realises the eight §6 F2
  transition rows by comparing two leg -> depth maps, keeps `added_new` and `promoted_to_premium` disjoint
  (a leg premium on first sight is `added_new` alone), and reports `removed` as **observability only —
  never an unsubscribe**. It **never inspects `pending` / `failed`**: a still-pending action re-emits and
  that is the retry, asserted absent on the source. `SubscriptionPlan.ordered_actions()` releases
  capacity (demotions) before claiming it (additions/promotions); every group is sorted by
  `str(instrument)` for determinism.
- **`__init__.py`** — five new exports (`SubscriptionState`, `SubscriptionManager`, `SubscriptionPlan`,
  `SubscriptionAction`, `ActionKind`), version `0.5.0` -> `0.6.0`.
- **Four phase-boundary guards shortened** by exactly the two F6 modules (`test_framework_package.py`,
  `test_framework_capability_layer.py`, `test_framework_window_manager.py`,
  `test_framework_priority_policy.py`); the exact-equality `__all__` set widened with the F6 group. None
  relaxed to a subset check.

**Affected files.** `market_depth_framework/subscription_state.py` (new),
`market_depth_framework/subscription_manager.py` (new), `market_depth_framework/__init__.py`,
`tests/test_framework_subscription_state.py` (new, 51),
`tests/test_framework_subscription_manager.py` (new, 35), `tests/test_framework_package.py`,
`tests/test_framework_capability_layer.py`, `tests/test_framework_window_manager.py`,
`tests/test_framework_priority_policy.py`,
`plans/Plan_002_market_depth_framework_implementation.md`, `Documents/ARCHITECTURE.md`,
`Documents/market_depth_framework.md`, this file.

**Verification.** Framework suite **766**, full recorder suite **1033 passed**. `compileall` clean,
`git diff --check` clean, framework config validation exit 0, recorder `--validate-config` still
`CONFIG OK` with config hash `sha256:8a48bcdd...1a468b` unchanged and exit 0 — no recorder behaviour
changed. An AST audit over both new modules confirms no thread, socket, subprocess, DB handle, queue,
executor, network call, file handle, wall-clock read, or module-level side effect; importing the
framework still starts no thread, and no recorder module references it.

**Snapshot-derived, not a broker measurement.** F6 makes no claim to have measured broker
acknowledgements: `pending` / `failed` are derived from the live `current` snapshot the caller supplies.
The broker execution and the depth-transition evidence are F7's. The F7 boundary questions — whether a
bare re-subscribe changes depth, whether an explicit unsubscribe exists or is required, what a transition
costs, behaviour at the 15-symbol ceiling, and reconnect depth restoration — remain **unresolved** and
untouched by F6.

**Deferred.** Broker Adapter and the live depth-transition probe (F7); recorder integration (F8); replay
harness (F9); true-scale validation (F10). Each is asserted *absent* from F6 by source-level AST scans,
so the absence is a checked decision rather than an oversight.

## 2026-08-25 — Plan_002 F5: Budget Allocator + Depth Allocator (allocation only)

**Why.** F3 settled which legs are in play and F4 settled the order in which they matter. F5 settles the
next two questions and only those: **how many premium slots each underlying gets**, and **which of its
legs hold them**. It does not decide what is actually subscribed (Subscription Manager, F6) and performs
no broker I/O (F7). The two allocators are separate deliberately — the split across underlyings is a
*capacity* question answered from candidate counts and configured weights, while the overlay inside one
underlying is a *ranking* question answered from `PriorityScore.rank`. Collapsing them would make the
inter-underlying split depend on individual leg priority, which is exactly the §10.4/§10.3 separation
Plan_002 protects.

**Decision applied before implementing (Plan_002 §20.3).** The F3 hysteresis fork was re-resolved to
remove a two-algorithm ambiguity in the old wording: hysteresis is **effective-rank stickiness inside a
bounded protection band**, and an effective-rank tie is won by the **challenger**. Recorded in the plan
with worked cases *before* any code was written. The `hysteresis_buffer < smallest premium budget`
startup guard was **explicitly rejected** and is absent: the anti-lockout is a property of the selection
rule, not of config. For `buffer <= budget`, a rank-1 challenger is beaten by at most `buffer - 1`
protected incumbents, so it is always inside the top `budget` — verified exhaustively in tests rather
than argued.

**What changed.**

- **New `market_depth_framework/budget_allocator.py`.** `BudgetAllocator.allocate_budget(total_budget,
  candidate_counts)` performs a largest-remainder weighted split on **exact rationals**
  (`fractions.Fraction`, not floats — independent per-underlying rounding can sum above the budget and
  blow a hard broker limit, and float division can truncate an exact `13` to `12`), then redistributes
  unspent slots one at a time, round-robin in descending weight order with ties broken by name.
  `min_per_underlying` floors apply to premium-eligible underlyings only and are capped by candidate
  count. An infeasible floor degrades deterministically and never raises at runtime — that check belongs
  to startup (F7), and raising here would kill PROCESSOR mid-session. `budget_allocator_for()` refuses
  the unimplemented `equal` / `proportional_to_candidates` policies rather than silently serving
  `weighted`, mirroring F4's `policy_for("blended")`.
- **New `market_depth_framework/depth_allocator.py`.** `DepthAllocator`, **one instance per underlying**,
  picks the premium overlay under the §20.3 hysteresis rule and a churn cooldown that gates premium
  reshuffles **only** — a baseline addition is immediate, and the first allocation of the session is
  never gated. A leg leaving the candidate window loses its slot regardless of the cooldown (that is
  disappearance, not churn), and a shrinking budget still truncates, because the budget is a hard broker
  limit. Budget is passed per call and never stored; the clock is **injected with no default**; history
  is a `deque(maxlen=history_limit)`, bounded by construction. Ships `DepthAllocation`,
  `DepthAllocationDiff`, `depth_allocator_for()`, `depth_allocators_for()`.
- **`__init__.py`** — nine new exports, version `0.4.0` -> `0.5.0`.
- **Four phase-boundary guards shortened** by exactly the two F5 modules
  (`test_framework_package.py`, `test_framework_capability_layer.py`,
  `test_framework_window_manager.py`, `test_framework_priority_policy.py`); the exact-equality `__all__`
  set widened with the F5 group. None relaxed to a subset check.

**Affected files.** `market_depth_framework/budget_allocator.py` (new),
`market_depth_framework/depth_allocator.py` (new), `market_depth_framework/__init__.py`,
`tests/test_framework_budget_allocator.py` (new, 71), `tests/test_framework_depth_allocator.py`
(new, 84), `tests/test_framework_package.py`, `tests/test_framework_capability_layer.py`,
`tests/test_framework_window_manager.py`, `tests/test_framework_priority_policy.py`,
`plans/Plan_002_market_depth_framework_implementation.md`, `Documents/ARCHITECTURE.md`,
`Documents/market_depth_framework.md`, this file.

**Verification.** Framework suite **680**, full recorder suite **947 passed**. `compileall` clean,
`git diff --check` clean, framework config validation exit 0, recorder `--validate-config` still
`CONFIG OK` with config hash `sha256:8a48bcdd...1a468b` unchanged and exit 0 — no recorder behaviour
changed. An AST audit over both new modules confirms no thread, socket, subprocess, DB handle, queue,
executor, network call, file handle, wall-clock read, `global`, or module-level side effect; importing
the framework still starts no thread, and no recorder module references it.

**Deferred.** `SubscriptionState` / `SubscriptionManager` / `reconcile()` (F6); Broker Adapter and the
live depth-transition probe (F7); recorder integration (F8); replay harness (F9); true-scale validation
(F10). Each is asserted *absent* from F5 by source-level AST scans, so the absence is a checked
decision rather than an oversight.

**Doc discrepancy noted.** The F4 entry records a framework suite of **490**; the nine
`test_framework_*.py` files at F4 actually collect **525** (the 35-test `test_framework_models.py` was
missing from that count). Full-suite arithmetic is exact and unaffected: 792 at F4 + 155 new = 947.

## 2026-08-25 — Plan_002 F4: Priority Policy (candidate ranking only)

**Why.** F3 settled which legs are in play. F4 settles the next question and only that one: **in what
order do they matter.** It does not decide how many legs may be premium (Budget Allocator, F5), which
ones get the premium overlay (Depth Allocator, F5), or what is actually subscribed (Subscription
Manager, F6). Those four questions were deliberately kept apart in Plan_002 §10, and collapsing any two
of them is what makes the resulting layer untestable in isolation and impossible to replace per broker.
The ranking F4 produces is an **input to F5**, nothing more.

**What changed.**

- **New `market_depth_framework/priority_policy.py`.** `AtmDistancePolicy` scores each candidate
  `-abs(strike - ctx.atm_strike)` — the ATM leg scores exactly `0.0`, nearer outranks further — and
  returns through `rank_scores()`. Also ships `MarketContext`, `PriorityScore`, the `PriorityPolicy`
  protocol, `policy_for()`, `market_context_from_window()`, `rank_candidates()`, and `DEFAULT_POLICY`.
- **`__init__.py`** — nine new exports, version `0.3.0` -> `0.4.0`.
- **New `tests/test_framework_priority_policy.py`** (+81).
- **`tests/test_framework_package.py`**, **`tests/test_framework_capability_layer.py`**, and
  **`tests/test_framework_window_manager.py`** — each phase-absence guard shortened by exactly one
  module (`priority_policy`), and `test_framework_package.py`'s exact-equality `__all__` set widened
  with an F4 group. All three remain exact-equality checks and still fail on any F5+ module arriving
  early. These are the only existing tests touched.

**Decisions worth recording.**

- **One rank basis: `PriorityScore.rank`, 1-based (§14.2, fork F4).** The drafted 0-based positional
  index was **deleted**, not reconciled — two bases in circulation is exactly the off-by-one recorded as
  §21 D-5. `PriorityScore.__post_init__` rejects `rank < 1`, so the floor is enforced by the type rather
  than merely produced by the ranker, and `rank_scores` is the only place a rank is ever constructed.
- **`rank_scores()` is the single ordering site (§10.3).** Every policy returns through it, so the total
  order — **score descending, then symbol ascending** — is defined in exactly one place. Equal-distance
  ties are the common case, not an edge case: the CE and PE at one strike always tie, and so do mirrored
  strikes either side of the ATM. The symbol tie-break is what makes those deterministic rather than
  dependent on the order the universe happened to arrive in. A shuffled candidate list produces a
  byte-identical ranking, which is what replay determinism rests on. Duplicate symbols are refused: the
  tie-break cannot separate two rows for one leg, and guessing would be worse than saying so.
- **`atm_distance` is the default, and `blended` is never silently substituted (§14.6, fork F12).**
  `policy_for("blended")` raises `FrameworkConfigError`. Its gamma/volume/OI inputs are not reliably
  present at pass time, and a policy that quietly degrades to another when its inputs are missing is
  exactly the silent default the fail-fast contract forbids. **Scoping decision taken here, not
  silently:** §22's F4 row names only `AtmDistancePolicy`, so `blended` is left unimplemented and
  refused rather than half-built.
- **The ATM is read, never re-derived.** §15 states the ATM rule (nearest strike; exact tie to the
  **lower** strike) once, and `market_context_from_window()` carries F3's answer forward. Two
  implementations of one rule is how a live run and a replay of the same raw log come to disagree about
  which leg was the ATM. The adapter refuses any non-`RESOLVED` `WindowResult`: ranking a window that
  never resolved a spot would rank nothing while looking like it had succeeded.
- **`MarketContext` carries `underlying`, `spot`, `atm_strike` and nothing else.** **Scoping decision
  taken here, not silently:** no gamma/volume/OI bag was added, because those fields belong to the phase
  that implements the policy consuming them and a field carried unused is a field whose semantics nobody
  has decided. A later blended phase can add fields additively without disturbing F4.
- **Underlyings rank independently, each from rank 1.** Ranking them into one pool would presuppose a
  shared budget, and how budget is split across underlyings is §10.4 / F5's question. A window that did
  not resolve contributes an empty tuple rather than vanishing, so the caller can still see it was
  considered.
- **The scope boundary is asserted on the source, not left to review.** AST scans over the
  docstring-stripped module assert that no budget, `tbt`, `max_channels`, capability, depth-tier,
  overlay, hysteresis, cooldown, subscription, reconciliation, or broker-adapter concept appears in
  executable code, alongside the usual no-index-name and no-exchange-code scan. A boundary that is only
  reviewed drifts; one that is asserted does not.
- **Tests use the same synthetic `ALPHAIDX` / `BETAIDX` underlyings** on exchanges `XFO` / `YFO` with
  strike steps 50 / 100, so no ranking test can pass by accident on a NIFTY-shaped chain, and the
  ranking is shown to be independent of the strike step.

**Verification.** `pytest tests/test_framework_priority_policy.py -q` -> **81 passed** (0.20s); all seven
framework files together -> **490 passed** (2.91s); **full suite 792 passed** (63.20s) = 711 + 81, no
regressions and no flake. `python -m compileall -q market_depth_framework` clean; `git diff --check`
clean. `python -m market_depth_recorder.market_depth_framework --config .../config.example.yaml` exit 0.
The recorder's own `--validate-config` is byte-identical: `CONFIG OK`,
`config_hash sha256:8a48bcdd4fca933d1dbc85bd9a5c1dc055403392da0afeb22e629af550a1468b`, exit 0 — no
recorder behaviour changed. Resource audit: F4 adds no thread, socket, subprocess, DB connection, queue,
executor, or persistent FD — `priority_policy.py` imports only `math`, `dataclasses`, `typing`, and three
sibling modules, and the package's only `open()` is still F1's config read under `with`.

**Affected files.** `market_depth_framework/priority_policy.py` (new),
`market_depth_framework/__init__.py`, `tests/test_framework_priority_policy.py` (new),
`tests/test_framework_package.py`, `tests/test_framework_capability_layer.py`,
`tests/test_framework_window_manager.py`,
`plans/Plan_002_market_depth_framework_implementation.md`, `Documents/ARCHITECTURE.md`,
`Documents/market_depth_framework.md`, `Documents/CHANGELOG.md`.

**Deferred.** Budget Allocator and Depth Allocator incl. hysteresis and cooldown (F5), SubscriptionState
and SubscriptionManager (F6), the live depth-transition probe and Broker Adapter (F7), recorder
integration and the `config.yaml` framework block (F8), replay/determinism harness (F9), true-scale
validation (F10). The `blended` policy remains unimplemented by design. The framework stays inert:
nothing in the recorder imports it, and the subscribe-everything-at-`:50` path remains the active one.

## 2026-08-25 — Plan_002 F3: Window Manager (ATM-relative candidate eligibility)

**Why.** Before anything can be ranked, budgeted, or subscribed, something has to say **which legs are
even in play**. F3 is that layer and only that layer: given a spot price and a supplied instrument
universe it returns the eligible candidates for an underlying. It does not order them by importance (F4),
does not decide how many may be premium (F5), and does not decide what is actually subscribed (F6).
Keeping those four apart is what makes each one testable in isolation and replaceable on its own.

The second reason is that the recorder already has window semantics, in `websocket_client.py`'s DSM
seeding and `processor._resolve_atm`. Writing a second, subtly different definition in the framework
would guarantee that a framework-driven run and a replay of the same raw log disagree about which legs
existed. So F3 reproduces the existing rules rather than inventing new ones, and makes explicit what was
previously incidental.

**What changed.**

- **New `market_depth_framework/window_manager.py`.** `WindowManager` computes
  `lower = spot - window_points`, `upper = spot + window_points`, with membership **inclusive at both
  bounds** and compared **exactly, no epsilon** — `websocket_client.py`'s `st.b_lower <= k <= st.b_upper`.
  ATM is the nearest strike with **ties resolved to the lower strike**, which is what
  `processor._resolve_atm` does over its ascending `active_strikes_list`; reimplemented order-independently
  (sort ascending, keep only a strict improvement) so a shuffled universe cannot change the answer.
  Also ships the two seams — `SymbolCodec` / `TagSymbolCodec` for option side, `ExpiryCalendar` /
  `FixedExpiryCalendar` for expiry selection — plus `WindowSpec`, `WindowResult`, `WindowStatus`,
  `OptionSide`, and `window_specs_from_underlyings()`.
- **`__init__.py`** — ten new exports, version `0.2.0` -> `0.3.0`.
- **New `tests/test_framework_window_manager.py`** (+125).
- **`tests/test_framework_package.py`** and **`tests/test_framework_capability_layer.py`** — each
  phase-absence guard shortened by exactly one module (`window_manager`). Both remain exact-equality
  checks and both still fail on any F4+ module arriving early. These are the only existing tests touched.
- **`config.py` and `config.example.yaml`** — comments only, recording that F3 shipped and deliberately
  added no config keys.

**Decisions worth recording.**

- **The candidate set is not the subscription set (§15).** Boundary expansion, hysteresis, and the
  never-shrink rule stay FEED-owned in the recorder and belong to F6 inside the framework.
  `WindowManager` recomputes from scratch every call and carries no window state between passes — tested
  by shifting the spot and shifting it back and asserting the original result returns exactly.
- **Candidates are sorted `(strike, option_type, symbol)` — identity order, not priority order.** Some
  deterministic order is needed for replay and tests, but inventing a distance-from-ATM order here would
  be smuggling in F4's ranking. A test asserts the output is explicitly *not* distance-ordered.
- **Identity is supplied, never constructed.** The universe arrives as `Instrument` values from the
  instrument master. The framework parses no symbol and builds none; option side comes from a registered
  codec rule and expiry from a registered calendar rule, registered **per rule name, not per index name**
  (§10.2). An unrecognised option-type tag raises on the pass that saw it rather than being guessed at.
- **Degenerate input gets a named status; a caller bug still raises.** `NO_SPOT` (missing, zero, negative,
  NaN, infinite — and `bool`, which is not a price), `NO_EXPIRY`, `NO_UNIVERSE` are ordinary results. An
  unknown underlying, or a leg claiming this underlying on a contradicting exchange, raises: those are
  wiring errors, and a plausible-looking empty result would hide them.
- **No second config system.** The `window_manager` config section stays deliberately **keyless**; zones
  are read from the recorder's existing `underlyings[]` through `window_specs_from_underlyings()`, which
  takes plain mappings (so the one-way dependency holds) and consumes only `name`, `option_exchange`, and
  `initial_window`. Duplicating the zones into a second place is how a config and its source drift apart.
- **Tests use synthetic underlyings, not NIFTY/SENSEX.** `ALPHAIDX` / `BETAIDX` on exchanges `XFO` / `YFO`
  with strike steps 50 / 100 and windows 200 / 500, so no test can pass by accident on a NIFTY-shaped
  universe, and both sides are verified **separately** rather than one being inferred from the other.

**Verification.** `pytest tests/test_framework_window_manager.py -q` -> **125 passed** (0.33s); all six
framework files together -> **444 passed** (1.08s); **full suite 711 passed** (91.47s) = 586 + 125, no
flake this run. `python -m compileall -q market_depth_framework` clean.
`python -m market_depth_framework --config config.example.yaml` exit 0. The recorder's own
`--validate-config` is byte-identical (`config_hash sha256:8a48bcdd...`, exit 0). Resource audit: F3 adds
no thread, socket, subprocess, DB connection, queue, executor, or persistent FD — `window_manager.py`
imports only `math`, `dataclasses`, `enum`, `typing`, and two sibling modules, and the package's only
`open()` is still F1's config read under `with`.

**Affected files.** `market_depth_framework/window_manager.py` (new),
`market_depth_framework/__init__.py`, `market_depth_framework/config.py` (comment),
`market_depth_framework/config.example.yaml` (comments),
`tests/test_framework_window_manager.py` (new), `tests/test_framework_package.py`,
`tests/test_framework_capability_layer.py`,
`plans/Plan_002_market_depth_framework_implementation.md`, `Documents/ARCHITECTURE.md`,
`Documents/market_depth_framework.md`, `Documents/CHANGELOG.md`.

**Deferred.** Priority Policy (F4), Budget/Depth Allocators (F5), SubscriptionState and
SubscriptionManager (F6), the live depth-transition probe and Broker Adapter (F7), recorder integration
and the `config.yaml` framework block (F8), replay/determinism harness (F9), true-scale validation (F10).
The framework stays inert: nothing in the recorder imports it, and the subscribe-everything-at-`:50` path
remains the active one.

**Semantic reconciliation (decided 2026-08-25, after the F3 gate review).** Three F3 semantics were put
to the user at the gate and are now final; all three ratify the implemented behaviour, so **no F3 code
behaviour changed** — only the wording that states the contract.

- **Decision 1 — single-density window.** Window Manager eligibility is a single symmetric
  points-from-spot window derived from the configured `underlyings[]` specification. No two-density /
  decimation model, and no new config key for a fine ATM step, a coarse expansion step, decimation, or
  density. The strike step describes the instrument universe/grid; it does not introduce a second window
  density. Plan_002 §15's stale "ATM zone (fine strike step) plus expansion zones (coarser step)"
  wording has been **rewritten**, not merely annotated, and §10.2 tightened to match.
- **Decision 2 — ATM tie goes to the lower strike.** Promoted from "reproduces the recorder" to an
  explicit deterministic framework rule that must not depend on list, dictionary, or input ordering.
  Recorded in Plan_002 §15 and §10.2; the `_atm_strike` docstring and the two tie tests now cite the
  decision rather than the recorder precedent. The order-independent implementation is unchanged, and
  the direct regression test plus its shuffled-input variant are retained.
- **Decision 3 — window configuration stays keyless.** No framework-side window config keys.
  `window_specs_from_underlyings()` remains the adapter from the recorder's `underlyings[]` into
  `WindowSpec` objects. One source of truth; no duplicate framework window settings.

Re-verified after the reconciliation: **125** F3 tests, **444** framework tests, **711** full suite —
all passing, counts unchanged. No new fork; no F0/F1/F2 decision reopened.

## 2026-08-25 — Plan_002 F2: Broker Capabilities layer (`effective_budget`, premium eligibility)

**Why.** Every later layer needs to know two things about the broker and must not learn anything else:
how many premium-depth legs it may hold at once, and which exchanges can serve a deep book at all. F2
delivers exactly those two answers behind one boundary. The point is not the number — it is that the
number is *derived from configuration*, so the allocators the next phases build stay broker-agnostic. A
broker exposing `1 x 20`, `5 x 10`, or a full 50-leg chain must change only its capability block, never
allocator code.

The boundary is also what keeps the FROZEN TBT finding from leaking. The correct model is 5 Market-Depth
symbols per **connection** x 3 connections = **15**; the disproven reading was 5 per **channel** x 50
channels = 250, roughly 16x too large. If allocators could see `symbols_per_connection`,
`max_connections`, or `max_channels`, that arithmetic could be re-derived — wrongly — anywhere in the
codebase. Behind one `effective_budget` it can be derived in exactly one place, and enforced there.

**What changed.**

- **New `market_depth_framework/capability_layer.py`.** `BrokerCapabilityLayer` wraps one frozen
  `BrokerCapability` and computes
  `effective_budget = min(total_symbol_budget, max_connections * symbols_per_connection)` once at
  construction — `min(UNLIMITED, 3 x 5) = 15` for the shipped FYERS configuration. `max_channels` is
  excluded from that arithmetic by contract: channels are a pause/resume grouping carrying no capacity.
  Also exposes `supports_premium(exchange)`, `premium_capacity(exchange)`, `available_tiers(exchange)`,
  `depth_for(exchange, tier)`, `has_account_wide_cap`, and the passthrough facts.
  Module-level: `build_capability_layers()`, `capability_layer_for()`, `eligible_underlyings()`,
  `check_premium_floor_feasible()` (the §13.2 startup check).
- **New `market_depth_framework/config.example.yaml`** — the reference §17 block with the FYERS facts
  filled in. A **copy source, not a live config** (`enabled: false`); wiring it into the recorder's
  `config.yaml` is F8. A test loads it end to end and asserts budget 15, NFO eligible, BFO not.
- **`__init__.py`** — five new exports, version `0.1.0` -> `0.2.0`.
- **New `tests/test_framework_capability_layer.py`** (+132).
- **`tests/test_framework_package.py`** — the exact-equality `__all__` assertion widened by the five new
  names (renamed from `..._the_f1_surface` to `..._the_current_phase_surface`). Still exact equality, not
  a subset check; the file's test count is unchanged. This is the **only** existing test touched.

**Decisions worth recording.**

- **A separate module, not methods on `BrokerCapability`.** Data and behaviour stay apart, and the F1
  guard asserting that the dataclass carries no budget arithmetic and no eligibility resolution stays
  green *unmodified* — the F1/F2 boundary is still checked rather than rewritten to fit.
- **"15 is derived, not hardcoded" is enforced on the source, not reviewed.** Two AST scans over the
  package: one rejects any multiplication mentioning `max_channels`, the other rejects a literal `15`
  assignment. Two more scans assert the layer performs no I/O and takes no `Instrument`.
- **Exchange matching is exact and case-sensitive**, and a malformed exchange raises rather than
  answering `False`. Case-folding would be a silent normalization, and a plausible-looking `False` would
  hide a caller bug. Worth knowing at F8: exchange codes must match the instrument master exactly.
- **The §13.2 floor is scoped to eligible underlyings only.** Scored over all configured underlyings it
  would demand premium slots for an underlying whose exchange has no deep book, contradicting §13.1.
  Satisfying it at startup is what makes the mid-session failure unreachable, which is why the F5 Budget
  Allocator will have no raising path able to kill the PROCESSOR thread.
- **`UNLIMITED_BUDGET` semantics unchanged from F1** — an `int` sentinel (`2**31 - 1`), never
  `float('inf')`. It means "no account-wide cap beyond the connection math" and can never itself become
  the budget in any realistic configuration, since the connection product wins the `min()`. Tested as a
  property, not as one case.

**Verification.** `pytest tests/test_framework_capability_layer.py -q` -> **132 passed**; the four F1
files together -> **187 passed** (unchanged); **full suite 586 passed** (454 + 132).
`python -m compileall -q market_depth_framework` clean. `config.example.yaml` validates (exit 0); a
malformed capability block reports and exits 1. The recorder's own `--validate-config` is byte-identical
(`config_hash sha256:8a48bcdd...`, exit 0). FD/thread audit: F2 opens no file, socket, thread,
subprocess, queue, or DB connection — the package's only `open()` is still F1's config read under `with`.

**One intermediate flake, recorded rather than papered over.** An earlier full-suite run reported
`1 failed, 585 passed`: the P6 recorder test `tests/test_integration.py::test_real_four_thread_pipeline_end_to_end`.
Rerun in isolation it passed (6.08s), and the subsequent complete suite passed at **586 passed in 80.94s**.
That test drives four real threads against wall-clock waits (a 15s `_wait_until`, a `time.sleep(1.4)`,
10s joins) under a 60s pytest timeout, so it is load-sensitive on a busy machine. F2 adds no thread and
no timing dependency and does not touch that test, so the flake is pre-existing. It was deliberately
**not** modified to make the report look clean.

**Affected files.** `market_depth_framework/capability_layer.py` (new),
`market_depth_framework/config.example.yaml` (new), `market_depth_framework/__init__.py`,
`tests/test_framework_capability_layer.py` (new), `tests/test_framework_package.py`,
`plans/Plan_002_market_depth_framework_implementation.md`, `Documents/ARCHITECTURE.md`,
`Documents/market_depth_framework.md`, `Documents/CHANGELOG.md`.

**Deferred.** Window Manager (F3), Priority Policy (F4), Budget/Depth Allocators (F5), SubscriptionState
and SubscriptionManager (F6), the live depth-transition probe and Broker Adapter (F7), recorder
integration and the `config.yaml` framework block (F8), replay/determinism harness (F9), true-scale
validation (F10). `check_premium_floor_feasible()` exists but is called from no live startup path until
F8 supplies the underlyings mapping. The framework stays inert: nothing in the recorder imports it.

## 2026-08-25 — Plan_002 F1: `market_depth_framework/` skeleton (contracts only, framework inert)

**Why.** Plan_002's seven behavioural layers all rest on three things the framework does not yet have: a
leg identity that survives a depth change, a place to put broker-declared capacity facts, and a
validated config schema. F1 delivers exactly those and stops. Building them as the first phase means F2
onward implement against fixed contracts rather than inventing them mid-layer; keeping *only* those in
F1 means the contracts can be reviewed without a behaviour change riding along.

Two of the three are load-bearing beyond convenience:

- **`Instrument` has no depth field** (fork F10). The recorder keys `_subscriptions` by *wire symbol*,
  and `wire_symbol()` appends `:50` for premium depth — so a 50→5 transition changes the key and one leg
  looks like two (§21 D-9). Depth must be a *value* on the leg, never part of its identity, or the
  hybrid's central operation is inexpressible. The `:50` suffix becomes a rendering detail owned by the
  Broker Adapter (F7).
- **`UNLIMITED_BUDGET` is an `int`** (`2**31 - 1`), not `float('inf')`, so downstream `-> int` contracts
  and `min()` arithmetic stay honest. A fixed literal rather than `sys.maxsize`, so the value is
  identical on every platform and replay stays deterministic.
- **`max_channels` is carried but never multiplied into a budget.** The FROZEN finding is 5 symbols per
  *connection* × 3 connections = **15**; channels are a pause/resume grouping with no capacity.
  Multiplying them in is precisely the error that produced a ceiling ~16× too large. F1 has no budget
  arithmetic at all, and a test asserts `5×3 == 15 ≠ 5×50` so F2 inherits the constraint.

**What.** New sub-package `market_depth_framework/` with a **one-way dependency** — it imports nothing
from the recorder (verified by an AST scan), so it stays independently testable and broker-reusable.

- `models.py` — `Instrument` (frozen, hashable, six identity fields, validating `__post_init__`) and
  `DepthType` (`STANDARD`/`PREMIUM`; names the tier, not the level count — the numeric depth is a broker
  fact that varies by exchange and lives on the capability).
- `capabilities.py` — `UNLIMITED_BUDGET`, `PremiumTier`, `StandardTier`, `BrokerCapability`; all frozen
  and self-validating (`premium.depth > standard.depth` enforced).
- `config.py` — `FRAMEWORK_SECTION`, `FrameworkConfig`, `FrameworkConfigError`,
  `validate_framework_config`, `load_framework_config`. Follows the recorder's conventions exactly:
  every error collected in one pass, `report()` renders them all, unknown keys rejected, no silent
  defaults. The section is optional — absent means the framework is off (the current runtime state);
  present-but-malformed fails hard.
- `__main__.py` — a **separate** `--validate-config` entrypoint (exit 0 valid / 1 invalid / 2 usage), so
  F1 changes no recorder behaviour. `main(argv)` returns the code rather than calling `sys.exit`, so the
  contract is testable in-process as well as via subprocess.

**Scope boundary, enforced by tests rather than by review.** F1 establishes contracts; it does not start
F2–F6. Deliberately absent and asserted absent: `effective_budget()` and `supports_premium()` (F2, the
Broker Capabilities *layer*); the §13.2 feasibility check (needs F2's `effective_budget` and eligible
set); and every `window_manager` / `priority_policy` / `budget_allocator` / `depth_allocator` /
`subscription_manager` / `broker_adapter` module (F3–F7). Subscription reconciliation is F6.

**Inertness.** The framework is not imported by any recorder module, not present in the shipped
`config.yaml`, and not reachable from the live pipeline. A subprocess import test with `socket.socket`
and `sqlite3.connect` nulled asserts the thread count is unchanged and nothing is printed.

**Threads:** none added — the four-thread architecture (FEED, RAW WRITER, PROCESSOR, DB WRITER) is
preserved; fork F1 settles that the framework is synchronous and threadless.
**FDs:** one, transiently — the config handle in `load_framework_config`, under `with`, closed on every
path including the YAML-error unwind. No socket, subprocess, DB handle, queue, or executor.

**Tests.** +187 new (`test_framework_models.py` 36, `test_framework_capabilities.py` 50,
`test_framework_config.py` 91, `test_framework_package.py` 10). Pre-existing suite verified unchanged at
**267** in isolation; full suite **454 passed**. No existing test was modified or weakened.

**Verified.** Shipped `config.yaml` (no framework section) → "no section … (framework off)", exit 0. A
valid framework block → `FRAMEWORK CONFIG OK`, exit 0. An invalid block →
`FRAMEWORK CONFIG VALIDATION FAILED:` with **12 errors collected in one pass**, exit 1. Recorder's own
CLI unchanged: `--validate-config` → `CONFIG OK`, same `config_hash`, exit 0.

**Affected files.** New: `market_depth_framework/{__init__,__main__,models,capabilities,config}.py`;
`tests/test_framework_{models,capabilities,config,package}.py`;
`Documents/market_depth_framework.md`. Modified: `Documents/ARCHITECTURE.md` (package-layout tree +
"Built state (F1)"), `Documents/CHANGELOG.md`, `plans/Plan_002_market_depth_framework_implementation.md`
(§22.1 checklist ticked). **No recorder source, no recorder test, and no `config.yaml` changed.**

**Deferred.** Everything behavioural: F2 Broker Capabilities layer, F3 Window Manager, F4 Priority
Policy, F5 Budget/Depth Allocators, F6 Subscription Manager, F7 Broker Adapter (itself blocked on the
depth-transition probe, Plan_002 §20.1), F8 recorder integration. The behavioural config sections stay
read-only mappings until the phase that owns each gives it a typed shape — typing them now would mean
guessing at fields those phases have not designed.

## 2026-08-25 — Plan_002: all forks closed; F0 approval gate prepared (planning only, still no code)

**Why.** Plan_002 was opened with fourteen forks. F1 (four-thread contract) and F2 (baseline
monotonicity / premium overlay mutability) were decided first and unblocked the architecture. The
remaining twelve were decided in one pass so that the plan states a single settled design rather than a
menu — a phase cannot be implemented against an open fork without the implementer silently deciding it.

**What.** Documentation and plan only. **No `market_depth_framework/` code exists, and none was
written.** P0-P10 behaviour, config, and tests are untouched.

*Decisions recorded (`plans/Plan_002_market_depth_framework_implementation.md` §20)*

| Fork | Decision | Specified in |
|---|---|---|
| F3 hysteresis | displacement-based: challenger inside top `budget` displaces the worst incumbent | §14.1 |
| F4 rank basis | 1-based `PriorityScore.rank` only; the 0-based index is deleted | §14.2 |
| F5 cooldown scope | premium reshuffles only; baseline additions apply immediately | §14.3 |
| F6 unspent budget | deterministic round-robin redistribution in weight order | §13.3 |
| F7 infeasible floors | startup validation, exit 1; no runtime raise | §13.2 |
| F8 diff semantics | `removed` is observability only; `added_new` / `promoted_to_premium` disjoint | §14.4 |
| F9 depth transition | **probe first** — measured in phase F7, never assumed | §20.1 |
| F10 state key | leg identity (`Instrument`); depth is a value, not part of the key | §9 |
| F11 rebalance trigger | interval OR window/ATM change, whichever fires first | §14.5 |
| F12 default policy | `AtmDistancePolicy`; blended is config-selectable, not default | §14.6 |
| F13 premium eligibility | broker/exchange capability; ineligible gets 0 premium, full baseline | §13.1 |
| F14 PROCESSOR -> FEED | latest-wins mailbox, **provisional**, validated in phase F8 | §20.2 |

*Two binding clarifications applied*

1. **`min_per_underlying` is scoped to premium-eligible underlyings.** Read over all configured
   underlyings, F7's startup check demanded a floor for SENSEX while F13 required SENSEX to receive
   zero — a direct contradiction that would have reserved 2 of 15 scarce slots for an exchange (BFO)
   physically unable to use them. Consequence recorded in §13.2: because runtime `active` is always a
   subset of the eligible set, the drafted mid-session `ConfigurationError` becomes **unreachable** and
   is deleted outright rather than guarded, so `allocate_budget()` gains no raising path that could
   kill the PROCESSOR thread.
2. **F14's mailbox is an implementation direction, not permission to add a thread or a second
   broker-I/O owner.** The F1 four-thread contract is absolute regardless of how the hand-off is
   carried.

*F6 specified as capacity-driven, not score-driven*

Redistribution reads **candidate capacity and configured weights only**, never a `PriorityScore` —
coupling it to individual ranking would collapse the Budget Allocator / Depth Allocator separation.
Both worked examples in §13.4 now spend the full budget (Example A: NIFTY 15 / SENSEX 0; Example B:
NIFTY 5 / SENSEX 10), superseding the drafts' three mutually inconsistent answers for identical inputs.

*F9 kept as a measurement, with a specification*

§20.1 defines the probe: all four transitions (`5->50`, `50->5`, `50->50`, `5->5`) and a seven-item
evidence checklist — whether a bare re-subscribe changes depth, whether unsubscribe is required,
whether unsubscribe exists at all through the current OpenAlgo/FYERS path, transient subscription loss,
whether a transition consumes an extra premium slot, behaviour at the 15-symbol ceiling, and reconnect
behaviour afterwards. Deliverable is a dated evidence document under `Documents/evidence/`, held to the
standard of `tbt_concurrency_reconciliation_20260714.md`. **The Broker Adapter is written after that
document exists, not before** — this is the same class of assumption that produced the 250-symbol
error, and it is not to be guessed twice.

*Also recorded*

- §21 gains **D-9** (the recorder's `_subscriptions` key encodes depth via `wire_symbol()`'s `:50`
  suffix, so "the same leg at a different depth" is inexpressible — closed by F10) and **D-10** (the
  drafted `min_per_underlying` would starve the premium budget — closed by the §13.2 scoping).
- §22 phase table reworked: a per-phase **Implements** column, and an explicit ordering constraint that
  **F7 must complete before the Broker Adapter is written**, which must precede F8 integration.
- §22.1 is the new **F0 approval gate** — eight items ticked, one open: user approval of F1 scope.
- §23 expanded from three lines to a per-phase F1-F10 progress list.

**Verification.** No code changed, so no test run was performed or claimed. Sweep of
`Plan_002_market_depth_framework_implementation.md` for open-fork language ("Unsettled", "Open
semantics", "OPEN FORKS", "decisions required", "See fork Fn") returns nothing; the nine surviving
`fork Fn` references were reworded to name the section that settles each.

**Not done / deferred.**
- **Phase F1 is not started.** Explicitly withheld pending approval of the F0 gate.
- **F9 is undecided by design** until the phase-F7 probe produces evidence.
- **F14 is provisional** until the phase-F8 checklist in §20.2 is satisfied against the real FEED loop.
- Plan_001 **Decision 18** remains open; it closes in Plan_002 phase F10.

## 2026-08-25 — Plan_002 opened: generic market-depth framework, planning cycle only (no code)

**Why.** Plan_001 decisions 16 and 17 made the hybrid the design (near-ATM legs at 50-level within
`tbt_budget = 15`, the rest at 5-level) and required a broker-capability layer so the engine stays
broker-agnostic. Neither exists. Plan_002 is the plan for that work, and it is the only one — the same
one-plan-one-location rule Plan_001 follows.

**What.** Documentation only. **No code was written; `market_depth_framework/` does not exist.**

- `plans/Plan_002_market_depth_framework_implementation.md` — new, 23 sections: scope boundary against
  Plan_001, an authority ranking for the four Qwen draft documents, the two decided forks, the
  corrected concurrency contract and pipeline, the subscription state model, nine component contracts,
  reconciliation/allocation/window semantics, config surface, testing architecture, integration plan,
  fourteen forks (two closed, twelve open with recommendations), eight source-document discrepancies,
  and an eleven-phase sequence F0-F10.
- `plans/Plan_001_market_depth_recorder_implementation.md` — cross-reference to the successor plan
  added to the decisions block; decision 18 (perf/RSS at true scale) is carried to Plan_002 phase F10.

**Decisions recorded (user, 2026-08-25; not to be reopened).**
- **F1 — there is no SUBSCRIPTION thread.** The recorder keeps exactly four worker threads (FEED, RAW
  WRITER, PROCESSOR, DB WRITER) and the framework is synchronous and threadless. `SubscriptionManager`
  is a pure component called on PROCESSOR; broker I/O stays on FEED. This supersedes the Qwen drafts'
  §0.1 and §6.7, which mandated a fifth thread.
- **F2 — permanent standard-depth baseline plus mutable premium overlay.** BASELINE MONOTONICITY (an
  eligible leg stays subscribed until graceful shutdown) and PREMIUM OVERLAY MUTABILITY (50-level
  assignment may be promoted, demoted, or reassigned within `tbt_budget`) replace the ambiguous
  "`_subscriptions` never-shrink". A demotion is a depth transition 50 -> 5, never an unsubscribe. An
  eight-row transition table is binding.

**Findings worth carrying (not previously written down).**
- The Qwen Budget Allocator worked example gives three different answers for the same inputs (its own
  split arithmetic yields NIFTY 9 / SENSEX 6, its prose says 9/5, and §0.2 says 10/5).
- The same example allocates 2 of the 15 scarce premium slots to SENSEX, which trades on BFO and can
  never receive 50-level depth. Premium eligibility belongs in the capability layer (fork F13).
- The recorder has **no unsubscribe path at all** — `websocket_client.py` never sends one. Whether a
  depth transition needs unsubscribe-then-subscribe or is a single re-subscribe is therefore unverified
  broker behaviour, and is scheduled as a live probe (phase F7) rather than assumed (fork F9).
- `_subscriptions` is keyed by wire symbol, and `wire_symbol()` encodes depth in the key (`:50`), so
  "the same leg at a different depth" is inexpressible today. Re-keying by leg identity is required
  (fork F10).

**Deferred.** Everything. Twelve forks (F3-F14) need decisions before phase F1 begins, and no
implementation phase starts until its scope is approved.

## 2026-08-25 — Repo-wide doc-accuracy sweep: the disproven FYERS TBT model marked superseded everywhere (no behavior change)

**Why.** A code-vs-plan audit ("has all the phases of Plan_001 completed? check with the code base, not
just the plan doc") confirmed every phase P0-P10 has real backing code, but found the **disproven** FYERS
TBT capacity model still stated as live fact in many places. The false model is *"5 Market-Depth symbols
per **channel** x 50 channels = ceiling 250"*. The true, FROZEN model (official FYERS TBT docs +
single-connection probe + multi-connection probe + a re-read of both live raws) is **5 symbols per
_connection_**, **3 connections per app per user**, **50 channels per connection that are a pause/resume
grouping carrying no capacity** -> **`tbt_budget = 15` (3 x 5)**.

The gap matters: the stale docs promise a ceiling roughly **16x** too large. P10 is titled "Full-chain
50-level" and fully ticked, so a reader would conclude the recorder captures the whole NIFTY chain at
50-level. It does not - it subscribes ~82 legs at `:50` and only ~5 ever stream concurrently (~6% of the
chain). SENSEX is unaffected (BFO -> 5-level, whole chain streams). Left unmarked, these documents would
have mis-anchored the framework design whose entire reason to exist is the hybrid the corrected ceiling
forces.

**What.** Documentation, comments, and one log-message string. **No logic, no constants, no config, and no
behavior changed anywhere.** P0-P10 behavior is untouched; the test suite is green at the same count.

*Sources of truth and plan*
- `market_depth_recorder_design.md` (spec, source of truth) - depth-level reality note rewritten to the
  frozen per-connection model, `tbt_budget = 15`, the hybrid as the design, and the broker-capability
  framing that keeps the engine broker-agnostic.
- `plans/Plan_001_market_depth_recorder_implementation.md` - `PHASE OBJECTIVE NOT DELIVERED` banner on the
  P10 heading; `-> SUPERSEDED (P10-F)` markers on D1, D2, the P10-A section, and A1. `SUPERSEDED` count
  7 -> 12; both remaining bare "250" assertions (lines 1448, 1493) now sit under a banner with a marker
  immediately following.
- `PROJECT_NOTES.md` - P9 headline finding and the P10-A summary corrected.

*Living architecture and operator docs*
- `Documents/ARCHITECTURE.md` - new FROZEN "Depth-capacity reality" block in the phase history, and a
  caveat on the perf targets recording that `cycle_ms_p50 ~ 22 ms` / `< 500 MB` were **not** measured at
  "full 80x50-level" (real load: <=5 NFO @50 + ~120 SENSEX @5) and remain unvalidated at the hybrid's
  profile.
- `Documents/SETUP.md` - the operator precondition no longer claims the patch enables a full 50-level
  chain; states the ~15-leg reality, why the patch is still worth applying, and what remains until the
  allocator lands.
- `Documents/operator_notes.md` - same correction in the operator-precautions list.
- `Documents/LIVE_RUN.md` - markers on the P9 headline finding and on the **E2** result (the "80 legs /
  16 channels / no global cap" pass was a measurement artifact; E2 did not actually pass).
- `plans/Plan_001_evidence/phase_10E_notes.md` - markers on the section-1 objectives and on "D2 holds".

*Patches folder (`Documents/evidence/`)*
- `OPENALGO_PATCH.md` - status line corrected (the "live-validated" claim was the artifact); top banner
  strengthened with the full evidence chain and the real ceiling; `-> SUPERSEDED` markers added to section 1
  (per-channel inference), section 2 (the unreachable 250 bound), section 3 (the pro/cons table, which now
  carries both "as costed" and "true" ceiling columns - the verdict is unchanged, since the correction
  lowers options A and B equally), and section 5 (the channel-distribution check passes and proves nothing;
  the meaningful check counts legs *streaming* per second, not subscribes - exactly how the P10-E artifact
  arose).
- `Phase9_notes.md` - section-3 banner strengthened; markers on the per-channel inference (the root of the
  mistake), the design decision, "recorder needs no depth-code change", "still to verify live" (now
  RESOLVED), and the platform-code reading (per-channel batch subscribe is message *coalescing*, not
  capacity - misreading it was part of the original misdiagnosis).
- `openalgo_fyers_tbt_channels.patch` - **regenerated** (88 -> 116 lines) so the reference diff matches the
  corrected source. Verified with `git apply --check --reverse` against the working tree.
- `tbt_concurrency_reconciliation_20260714.md` - unchanged; it is the canonical corrected evidence.
- `tbt_probe_20260714.json`, `tbt_multiconn_20260714.json` - **deliberately untouched**: raw measurement
  artifacts are evidence and must not be edited.

*Stale second copy of the plan removed*
- `Documents/Complete_Project_Plan_refer-market-depth-recorder-design-md-an-peppy-dolphin.md` - was a
  **1,556-line pre-P10-F snapshot of the plan** with **zero** supersession markers, asserting the 250
  ceiling as fact. Replaced its body with a **pointer stub** to
  `plans/Plan_001_market_depth_recorder_implementation.md`, matching what was already done to
  `~/.claude/plans/refer-market-depth-recorder-design-md-an-peppy-dolphin.md`. The stub records why the copy
  was dangerous rather than merely redundant, and links the corrected sources. One plan, one location.

*Code comments (recorder)*
- `eod_report.py` - the `_CYCLE_MS_TARGET` rationale comment claimed the 30 ms figure was measured "at the
  real full 80x50-level NIFTY scale". Corrected: that scale is unreachable on FYERS, the measurement was
  <=5 NFO @50 + ~120 SENSEX @5, and the target is unvalidated at the hybrid's profile. Threshold value
  unchanged at 30.0.

*Platform code (the existing P10-A scope exception, still uncommitted)*
- `broker/fyers/streaming/fyers_websocket_adapter.py` - three text corrections, no logic change:
  the class-constant comment block (rewritten to the per-connection model with a dated CORRECTION note and
  an explicit "these two constants must not be multiplied into a budget"); the `_assign_tbt_channel`
  docstring (records that the `None` return is effectively unreachable and the loop bounds are not a symbol
  budget); and the call-site comment. The operator-facing ERROR message was reworded from asserting
  "50 channels x 5 = 250 symbols" to naming it a channel-bookkeeping limit and pointing at the real
  per-connection cap. `TBT_SYMBOLS_PER_CHANNEL = 5`, `TBT_MAX_CHANNELS = 50`, and every code path are
  unchanged.

**Verification.**
- `pytest market_depth_recorder/tests/ -q` (run from `strategies/SS_Projects` with `PYTHONPATH` set to that
  directory, which the package imports require) -> **267 passed**, same as before the sweep.
- `python -m py_compile` on `eod_report.py` and `broker/fyers/streaming/fyers_websocket_adapter.py` -> OK.
- `git apply --check --reverse Documents/evidence/openalgo_platform/openalgo_fyers_tbt_channels.patch` -> clean, confirming the
  regenerated diff matches the working tree.
- Repo-wide sweep: every file still containing old-model phrasing ("per channel", "5x50", "ceiling 250",
  "symbols/channel", "no hybrid", "full-chain", "80x50") was re-checked to confirm it also carries
  correction markers. All do. The two remaining zero-marker hits are false positives: "full-chain Level-2"
  in `Documents/qwen/prompt_generic_market_depth_framework.md` (a generic capability phrase, not a capacity
  claim) and the message-coalescing comments in `broker/fyers/streaming/fyers_tbt_websocket.py` ("one JSON
  per channel" - batching, not capacity). `Documents/archive/**` was excluded by design.

**Not done / deferred.**
- **The `250` bound in `_assign_tbt_channel` was deliberately NOT corrected to 15.** That is a *behavior*
  change to platform code, outside a doc-accuracy sweep, and the wrong home for the fix: the budget belongs
  in the broker-capability layer the framework defines, so the engine stays broker-agnostic. It is harmless
  meanwhile - unreachable, because FYERS refuses the 6th symbol on a connection first.
- **The hybrid itself is still not built** (near-ATM @50 within `tbt_budget = 15`, rest @5). It requires new
  subscription logic - a per-leg depth decision and the ability to demote 50->5 - which conflicts with the
  recorder's current never-shrink `_subscriptions` invariant. Deferred to the framework effort.
- **Perf targets are unvalidated** at the hybrid's real load profile and must be re-measured once the
  allocator lands; this is now recorded in `ARCHITECTURE.md` and `eod_report.py` rather than implied away.
- **Decision #18 remains open**; not touched by this sweep.

## 2026-08-25 — P4b checklist reconciled; P0–P10 confirmed complete (no code change)

**Why.** A phase-state audit against `plans/Plan_001_market_depth_recorder_implementation.md` found P4b's
B1/B2/B3 still unticked, while the same phase's B4 (tests), B5 (docs) and B6 (completion audit) were
signed off on 2026-07-04 and `metrics/rolling.py` + `metrics/aggregate.py` existed in the tree. The
question was whether this was missing work or a bookkeeping omission.

**What.** Bookkeeping omission — verified, then ticked. **No implementation code was changed**; the
working tree carried no modifications to engine code at any point in this audit.
- **B1** verified: `metrics/rolling.py` binds all thirteen §3.4.3 rolling specs plus `ofi_instant` /
  `liquidity_delta_instant`, both `None` on the boundary second.
- **B2** verified: `metrics/aggregate.py` binds the seven §3.4.4 specs incl. `regime`/`pinning_score`,
  with `compute_underlying()` doing K_ATM + SMALL/MEDIUM/LARGE grouping from config radii.
- **B3** verified: `processor.py` back-fills `ofi` (line 382), emits both new envelopes (lines 286/290),
  and applies the degraded heavy-skip against `rolling.HEAVY_METRICS` (line 495).
- **P0-J6** stale gate marker ("awaiting approval before P1") reconciled — approval is evidenced by
  P1–P10 all being complete.

**Verification.** `pytest market_depth_recorder/tests/ -q` → **267 passed** in 133s (no live feed);
`python -m market_depth_recorder --validate-config --config market_depth_recorder/config.yaml` → **exit 0**
(`config_hash sha256:8a48bcdd…`, transport `raw`); `compileall` on `metrics/` + `processor.py` → clean;
genericization grep → clean (sole `NIFTY` hit in engine code is a non-functional comment,
`processor.py:144`); no-asyncio grep → clean; `openalgo==2.0.2` pin intact; feed tee still two independent
puts (`websocket_client.py:447` proc / `:454` raw-with-timeout, raw shedding last).

**Affected files.** `plans/Plan_001_market_depth_recorder_implementation.md` (4 checkboxes + a dated P4b
reconciliation note) and `Documents/CHANGELOG.md` (this entry) — documentation only.
`Documents/ARCHITECTURE.md` needed **no** change: its "Built state (P4a + P4b)" section already described
all four §4.1 tables and the per-strike → rolling → aggregate order correctly, i.e. the implemented-state
docs were right all along and only the progress checkboxes had drifted.

**Nuance recorded, deliberately not "fixed".** Decision 39's P4a-era parenthetical lists "wall-score
median, quote stability" as degraded-skippable; the implemented and documented heavy set is rolling-only
(`Documents/processor.md:87`, `Documents/metrics.md:82`). Those two are cheap per-strike bodies over a
bounded deque. Docs match code — the planning text is the stale side. Changing behavior in an audited
phase was out of scope for a reconciliation.

**Deferred / open.** The only remaining unticked item in Plan_001 is the **generic framework**
(`market_depth_framework/`), which the plan explicitly records as *not* covered by P0–P10 and as
requiring a fresh scope-clarification → "let's write the plan" cycle. P0–P10 of the recorder are complete.

## 2026-07-14 — FYERS TBT budget = 15 confirmed; Jul-07/Jul-14 reconciled; protocol layer frozen (P10-F)

**Why.** Two questions remained before locking the architecture: (a) do FYERS' 3 connections × 5 symbols
actually combine to **15** concurrent 50-level symbols, and (b) why did the P10-E (2026-07-07) run appear to
show a full 80-leg 50-level chain when 2026-07-14 showed only 5? Both are now resolved from evidence.

**What.**
- New **multi-connection probe** `tools/fyers/tbt_multiconn_probe.py` + shared `tools/fyers/_tbt_common.py`
  (factored out of `tbt_channel_probe.py`). Drives 3 independent `FyersTbtWebSocket` connections
  concurrently. Result (evidence `Documents/evidence/fyers_tbt_concurrency_20260714/tbt_multiconn_20260714.json`): **C1** 5/5, **C3**
  **15/15 distinct legs streamed concurrently** (each conn 5/5, sustained increments, 0 drops), **C4** 4th
  connection **refused** (`429`). ⇒ **`tbt_budget = 15` (3 × 5)**; single-connection ceiling stays 5.
- **Reconciliation** (`Documents/evidence/fyers_tbt_concurrency_20260714/tbt_concurrency_reconciliation_20260714.md`, **canonical**): a
  per-second re-read of both raws shows **max 5 concurrent** NFO legs on **both** days (Jul-07: 9 distinct
  all session, 0 seconds >5; Jul-14: 5). The `git pull --rebase` between runs left the **TBT streaming code
  byte-identical** (`fyers_tbt_websocket.py`/`fyers_websocket_adapter.py`/`msg_pb2.py` unchanged; changes were
  REST/proxy only). Hypotheses: FYERS-change ✗, code-change ✗, **interpretation-artifact ✓** — P10-E read the
  80-leg *subscription* + genuine 50-*level* depth on ≤5 legs as "80 legs *streaming*."
- **P10-E cascade corrected** (superseded interpretation marked, original preserved; each doc summarizes +
  points to the canonical reconciliation): E2 "no cap/patch works" → artifact; E4 perf/RSS "at full scale"
  → was ≤5 NFO@50 + 120 SENSEX@5, **true 80×50 perf still untested**; E9 NIFTY coverage → ≤5 legs; **D2
  "no hybrid" reopened** → hybrid (near-ATM @50 + rest @5) or multi-connection, budget 15.
- Docs: `OPENALGO_PATCH.md §8.4` (RESOLVED), `Phase9_notes.md` (P10-F callout), `CLAUDE.md` "Depth Reality"
  (budget 15, allocator consumes one logical budget), plan doc P10-E section, `phase_10E_notes.md`/`LIVE_RUN.md`
  (correction banners), `tools/README.md` + `tools/fyers/README.md`. Separate OpenAlgo issue recorded for the
  `_run_websocket` retry-on-return storm (`openalgo_tbt_reconnect_storm_issue.md`) — not a protocol finding.

**Design impact.** Protocol layer **FROZEN unless new external evidence emerges** — do not revisit the FYERS
TBT assumptions without new evidence. FYERS capability = 5 syms/conn, 3 conns, `tbt_budget = 15`, channels =
pause/resume grouping. **`tbt_budget = 15` is a confirmed FYERS broker _capability_, not an architectural
constant** — the allocator consumes a logical TBT Budget exposed by the broker-capability layer; another
broker may expose a different budget with no architectural change. Next effort moves entirely to the generic
allocation framework (Broker Capabilities → Window Manager → TBT Allocator → Allocation Policy → Subscription
Manager), consuming that budget as one broker config. **Open (real):** perf/RSS at true 15 × 50-level +
hybrid remainder — never yet load-tested.

**Affected files.** `tools/fyers/tbt_multiconn_probe.py` (new), `tools/fyers/_tbt_common.py` (new),
`tools/fyers/tbt_channel_probe.py` (refactor to shared module), `Documents/evidence/fyers_tbt_concurrency_20260714/tbt_multiconn_20260714.json`
(new evidence), `Documents/evidence/fyers_tbt_concurrency_20260714/tbt_concurrency_reconciliation_20260714.md` (new, canonical),
`Documents/evidence/openalgo_platform/openalgo_tbt_reconnect_storm_issue.md` (new), `Documents/evidence/openalgo_platform/OPENALGO_PATCH.md`,
`plans/Plan_001_evidence/Phase9_notes.md`, `CLAUDE.md`, `tools/README.md`, `tools/fyers/README.md`,
`plans/Plan_001_evidence/phase_10E_notes.md`, `Documents/LIVE_RUN.md`, plan doc.

## 2026-07-14 — FYERS TBT 50-level ceiling: channel-spread patch disproven (P10-E)

**Why.** Live validation (OpenAlgo's own feed stopped) of the P10-A channel-spread patch, plus the official
FYERS TBT WebSocket docs, **independently disprove** the "5 symbols/channel × 50 = 250" premise the patch was
built on. FYERS caps 50-level Market Depth at **5 symbols per _connection_** (docs: 3 connections/app/user, 5
symbols/connection, 50 channels/connection); **channels are a pause/resume logical grouping, not extra
capacity.** In the 2026-07-14 recorder run, of 40 NIFTY `:50` legs (spread across channels 1–8) **only 5
streamed** (channel 1's five); SENSEX/BFO (5-level HSM) ran all 120 legs normally.

**What.**
- New diagnostics tool **`tools/fyers/tbt_channel_probe.py`** (+ `tools/fyers/README.md`) — drives
  `FyersTbtWebSocket` directly, fresh connection per test, capturing subscribe requests, FYERS ACKs/errors,
  and per-symbol packet counts. Probe matrix: T1 ch1 ✓, T2 ch2-alone ✓, **T2p int-channel silent** (resume
  needs *string* ids), **T3 ch1+ch2 → only 5 stream + "exceeds limit: 5"** (channels share one 5-symbol
  budget). Read-only w.r.t. platform code (documented scope exception, like the patch).
- Docs corrected to the experimentally + officially validated behavior: `Documents/evidence/openalgo_platform/OPENALGO_PATCH.md`
  (new authoritative §8; annotated §2/§6), `plans/Plan_001_evidence/Phase9_notes.md` (dated P10-E callouts),
  `CLAUDE.md` ("Depth Reality"), `tools/README.md` (index). Frozen evidence:
  `Documents/evidence/fyers_tbt_concurrency_20260714/tbt_probe_20260714.json`.

**Design impact.** Full NIFTY 50-level chain is **not** achievable on one connection. The channel-spread
patch is a no-op for the ceiling (harmless; kept for now). Path forward — **hybrid** (5 near-ATM @50 + rest
@5) or **multi-connection** (≤ 3×5; unconfirmed whether budgets combine) — **decision deferred**, to begin as
its own scoped effort. Open question if multi-connection is pursued: whether 3 conns × 5 syms truly yields 15
concurrent depth symbols (extend the probe to a 2-/3-connection test before committing).

**Affected files.** `market_depth_recorder/tools/fyers/tbt_channel_probe.py` (new), `tools/fyers/README.md`
(new), `tools/README.md`, `Documents/evidence/openalgo_platform/OPENALGO_PATCH.md`, `plans/Plan_001_evidence/Phase9_notes.md`,
`Documents/evidence/fyers_tbt_concurrency_20260714/tbt_probe_20260714.json` (new evidence), `CLAUDE.md`.

## 2026-07-13 — Default write backend flipped to `arrow`; `executemany` deprecated; PERFORMANCE.md

**Why.** The milestone review after Phase P-C confirmed the two gating conditions the user set for the
flip are both met: chunked-Arrow **preserves (in fact improves) throughput** *and* **bounds peak RSS**
(800 MB on the representative ~100-min dataset — suitable for the 8 GB target for current workloads; a true
full-session replay is not yet measured on this hardware), with **determinism bit-exact** vs the canonical
reference. **Offline replay on the representative ~100-min dataset improved from ~3h52m to 244.8 s (~57×)**
(671,481-packet / 5,951,233-row dataset).

**What.**
- `config.yaml`: `analytics_db.write_backend` default flipped **`executemany` → `arrow`**.
- **`executemany` is now DEPRECATED** — retained one release cycle as a fallback, selectable via
  `write_backend: executemany` or the `--backend executemany` CLI override. Marked deprecated in
  `config.yaml`, `ARCHITECTURE.md`, and `database_writer.md`.
- Precise wording pass: docs/code that said writer memory is "independent of replay length" now read
  "**bounded by the configured batch size rather than growing with replay duration**" (DuckDB's own
  working set can still vary — the more accurate engineering statement).
- New **`Documents/PERFORMANCE.md`** — the permanent engineering report of the whole optimization journey
  (problem, the measurement turning point that overturned the cProfile mis-diagnosis, every optimization +
  its measured contribution, the `_slope`/reference investigation, Arrow + chunked-Arrow redesigns, final
  benchmark tables, lessons learned, deferred framework work).

**Determinism / tests.** No logic change beyond the default; full suite green. Determinism unchanged
(default `arrow` now takes the already-bit-exact path).

**Affected files.** `config.yaml`, `database_writer.py` (comment), `Documents/ARCHITECTURE.md`,
`Documents/database_writer.md`, `Documents/CHANGELOG.md`, new `Documents/PERFORMANCE.md`.

**Remaining (framework evolution, not blockers).** DuckDB-side `verify()` rewrite (fixes the O(rows)
Python-dict OOM); `atol + rtol` verification semantics; Phase 2 multi-process (deferred, unlikely needed
for current workloads); future incremental real-time rolling engine. Offline replay optimization is
**complete**.

## 2026-07-13 — Phase P-C: chunked-Arrow streaming writer (peak RSS 4× lower, bounded by batch size not duration)

**Why.** Arrow was correctness/perf-validated but its `finalize()` buffered the **whole session** in
`self._buffers` (5.95M row tuples) then pivoted the largest table ~3× at once → **~3.6 GB RSS on ~100-min
data**, projecting to ~20 GB full-day — over the 8 GB target machine. Root cause (measured): the long-lived
per-table buffers dominate RSS; the Arrow pivot only adds a transient peak on top.

**What.** Stream fixed-size batches **during `write()`** instead of buffering the whole session. New
config key **`analytics_db.write_batch_rows`** (default **100_000**; validated positive int ≤ 5_000_000,
fast-fail). The write path is now the single seam **`write → buffer → _flush → backend insert`**: `write()`
flushes a table when its buffer reaches `write_batch_rows`; `_flush(table)` is the **only** place batching
lives (boolify option rows, dispatch to the arrow/executemany insert per batch, advance
`rows_written`/`batches_written`); `finalize()` flushes the trailing partials then stamps + `CHECKPOINT`.
The replay engine and metrics are **completely unaware** of batching — the seam a future streaming/parallel
writer reuses. Also **hardened `close()`**: a mid-`finalize()` failure now discards the partial temp in the
`finally` (previously it orphaned a `.building_<pid>` — exactly how the stale orphan on disk was created).

**Benchmark (~100-min dataset, backend=arrow, one process per run for clean peak RSS):**

| batch | wall | finalize | peak RSS | batches |
|---|---|---|---|---|
| 5_000_000 (unchunked control) | 300.8 s | 86.4 s | **3190 MB** | 4 |
| 250_000 | 247.1 s | 4.1 s | 1278 MB | 26 |
| **100_000 (default)** | **244.8 s** | 1.2 s | **800 MB** | 62 |
| 50_000 | 249.8 s | 0.6 s | 932 MB | 121 |

→ **100k is empirically optimal: 4× lower peak RSS (3190→800 MB) AND fastest wall** (finalize collapses
86→1.2 s as the write overlaps replay). Peak RSS floor is now DuckDB's own working set (`memory_limit`
PRAGMA), not the Python buffer → **writer memory is bounded by the configured batch size rather than growing
with replay duration** (validated on the representative ~100-min dataset; suitable for the 8 GB target for
current workloads — DuckDB's own working set can still vary, and a full session is not yet measured). Default kept at 100k
(data-backed, not assumed).

**Determinism.** Chunked-100k build (62 batches) vs the canonical reference (built pre-chunking, buffer-all)
→ **bit-exact, 0 divergent rows** across all 4 tables (5,951,233 rows) via the memory-safe DuckDB-side
`EXCEPT`. Chunking changes only *when* rows insert, never the data.

**Failure semantics (verified, all-or-nothing canonical).** Injection tests for mid-batch, between-batches,
final-partial-batch, and **after `CHECKPOINT` before rename** all confirm the canonical store is either
complete or absent, no partial output. **267 tests pass.** FD audit: FD-neutral (same single `with`-managed
connection; per-batch Arrow view `unregister`ed in `finally`), cleanup strictly improved.

**Affected files.** `database_writer.py` (`write`/`_flush`/`finalize`/`close`/ctor + `batches_written`),
`config.py` (validation), `config.yaml` (`write_batch_rows`), `tests/conftest.py`, `tests/test_database_writer.py`
(chunk parity + 4 failure-injection tests), `tests/test_replay.py` (chunked==unchunked). Docs:
`ARCHITECTURE.md`, `Documents/database_writer.md`.

**Remaining.** Milestone review → decision on flipping the config default to `arrow` (RSS now bounded) →
final performance report. Then offline optimization is complete; only the separate framework work
(DuckDB-side `verify()` + tolerance) remains.

## 2026-07-13 — Golden reference regenerated from current code; `_slope` validated superior; `--backend` override; verify() OOM found

**Why.** Validating the Arrow write path against the existing 652 MB `data/2026-07-07` analytics store
surfaced a mismatch, which investigation resolved into three benign, fully-understood facts — none an Arrow
defect — making that store **obsolete** rather than a valid reference:

1. **`_slope` (Phase-1b) is numerically *superior*, not merely equivalent.** A tolerance-aware DuckDB-side
   diff (matching `--verify`'s `atol=1e-9`) found the *only* divergence was **45 / 4,440,585**
   `strike_window_metrics.book_pressure_slope` rows at max **abs 1.42e-9 / rel 1.01e-12** (|slope| up to
   ~1.15e6). High-precision adjudication — recomputing each of the 45 slopes with numpy pairwise sums, the
   pure-Python sequential closed form, and an **exact `fractions.Fraction`** reference on the exact float
   inputs (captured via a wrapped-`_window_rows` replay, 45/45, `eps=1e-8`) — showed pure-Python is closer
   to exact in **41/45** rows, mean abs err **2.51e-10 vs 1.07e-9** (~4×), max rel err **8.90e-14 vs
   9.24e-13** (~10×). So the old store (numpy) was the *less* accurate artifact. `_slope` kept as-is.
2. **The provenance `config_hash` differs for a capture-only reason.** Old store `fb97f393` (config commit
   `3b6ceb5`) vs current `8a48bcdd` (`212fb90`): the only hashed-section change is NIFTY DSM
   **subscription-window** knobs (`initial_window` 1000→500, `expansion_threshold` 200→100, `expansion_step`
   300→100). Those govern *which strikes get subscribed during live capture* — **zero** effect on any
   replayed value (the raw log already holds the ticks). `compute_config_hash` hashes `underlyings`
   wholesale, so these live-only knobs flip the stamp regardless. This (not `write_backend`, which is **not**
   hashed) is why the earlier `--verify` aborted on config_hash.
3. **Arrow is value-preserving** (write path only; bit-identical to `executemany`, proven by slice A/B).

**What.** (a) **Archived** the old store → `data/2026-07-07/legacy_pre_p1b/…pre-p1b.legacy.duckdb` with a
provenance `README.md`. (b) Added a per-run **`--backend {executemany,arrow}`** CLI override (threaded
through `replay_file`/`catchup` via a new `write_backend` param on the writer seam) so a canonical rebuild
can pick Arrow **without** editing the committed config default — keeping the default `executemany` until
the flip is approved. (c) **Rebuilt the canonical reference** from current code via the canonical replay
path (`--replay … --backend arrow`, ~6m14s): `data/2026-07-07/market_depth_analytics_20260707.duckdb`,
**607.3 MB**, `config_hash=sha256:8a48bcdd…`, rows spot 11,433 · option 1,480,195 · window 4,440,585 · agg
19,020. (d) **Determinism re-verified bit-exact**: a second `--backend arrow` replay diffed against the new
reference via a memory-safe DuckDB-side symmetric `EXCEPT` → **0 divergent rows** across all 4 tables.

**⚠ New finding — `verify()` is not memory-safe at scale.** The canonical `--verify` **OOM'd**
(`MemoryError` in `replay._read_table`, `replay.py:407`): it materializes **both** the built and reference
tables into nested Python dicts (4.44M rows × 2 × ~30 cols) before comparing — unbounded O(rows) memory. It
cannot run on the ~100-min dataset here, and would fail hard on the 8 GB target machine / full-day data. The
determinism check above used a **DuckDB-side** diff instead (ATTACH both + per-table SQL), which is bounded
and fast. **Recommended (separate framework proposal, deferred): reimplement `verify()`'s per-table
comparison DuckDB-side** — this simultaneously fixes the OOM *and* lets the tolerance become numpy-`isclose`
style `abs(a-b) <= atol + rtol*|b|` (the pure-absolute `_VERIFY_ATOL` mis-scales for unbounded quantities
like slopes — the mechanism behind the 45-row finding). Per user direction, the `_values_equal`/verify
framework change is **not** bundled into this Arrow work.

**Affected files.** `__main__.py` (`--backend` arg + guard + wiring), `replay.py` (`write_backend` param on
`replay_file`/`catchup`), `tests/test_replay.py` (`write_backend` override parity test). Data:
`data/2026-07-07/market_depth_analytics_20260707.duckdb` (regenerated), `…/legacy_pre_p1b/` (archived old
store + README).

**Default NOT flipped (deliberate sequencing).** `config.yaml` `write_backend` **stays `executemany`**.
Arrow is fully validated for correctness + performance, but its `finalize()` buffers all rows → ~3.6 GB RSS
on ~100-min data, which won't scale to a full session on the 8 GB target machine. Per user direction the
default flip is **gated on chunked-Arrow** bounding peak RSS first. Arrow remains selectable now via the
config key or `--backend`. Suite green (**259 passed**).

**Remaining (priority order).** (1) **Chunked-Arrow `finalize()`** — stream fixed-size Arrow batches into
DuckDB instead of buffering all rows; keep throughput, bound peak RSS for the 8 GB machine. **Highest-
priority engineering task before the offline pipeline is production-ready.** On pass (determinism + memory),
flip the default to `arrow`. (2) Separate framework proposal: DuckDB-side, tolerance-scaled `verify()`
(fixes the OOM + the mis-scaled absolute tolerance in one change). (3) Later: remove the legacy `executemany`
path after one clean production cycle on Arrow.

## 2026-07-13 — Write-path pivot: Arrow columnar bulk-load backend for DuckDB finalize (30× replay)

**Why.** The offline replay's real bottleneck is the **DuckDB write**, not metric compute (Phase 0
mis-diagnosed it via cProfile — see the 1b entry's critical-finding note). An un-profiled phase-breakdown of
the fixed slice: `finalize()` **206.9 s** vs all metric compute **4.3 s** (~98 % / ~2 %). Root cause:
`finalize()` did row-by-row `con.executemany("INSERT … VALUES (?,…)", rows)` — a pathological anti-pattern
for DuckDB's vectorized columnar engine. It scales linearly and reproduces the user's original 3h52m
full-day run (206.9 s × 5.95M/74k ≈ 4.4 h).

**What.** Added a config-switchable write backend `analytics_db.write_backend` (`executemany` | `arrow`).
The `arrow` path pivots each table's buffered row tuples into per-column arrays, builds one
`pyarrow.Table`, and `INSERT … SELECT`s it in a single vectorized pass (DuckDB casts each column to the
destination type → bit-identical output). Default stays `executemany` until the full-day `--verify`
confirms `arrow`; `arrow` requires `pyarrow` (now pinned in `requirements.txt`; fast-fail at `_open()` if
selected-but-missing). Legacy path retained for now.

**Validation (A/B, fixed slice, full metric set, both `--verify` clean, exact 73,952-row parity):**

| backend | wall | finalize | peak RSS |
|---|---|---|---|
| executemany | 211.4 s | 206.9 s | 192.5 MB |
| **arrow** | **6.96 s** | **0.77 s** | 258.1 MB |

→ **finalize 269.8×, total wall 30.4×** (the ~6 s read+compute loop is now the floor). Peak RSS +66 MB
(transient columnar copy — watch at full-day scale). Full-day projection: ~3h52m → **single-digit minutes**.

**Affected files.** `database_writer.py` (backend dispatch + `_insert_arrow`/`_insert_executemany` +
pyarrow fast-fail + constructor override), `config.py` (enum validation), `config.yaml` (`write_backend`),
`requirements.txt` (`pyarrow~=23.0.1`), `tests/conftest.py` (fixture key), `tests/test_replay.py`
(arrow-vs-executemany parity test). Suite: **257 passed**.

**Reprioritization (validated).** Arrow write path is the offline #1 lever. **Phase 1c/1a/1d deferred**
(optimize the ~2 % compute slice — not worth it offline). **Phase 2 (multi-process) deferred pending
evaluation after chunked Arrow** — on current measurements a single process rebuilds a full day in minutes,
so it is unlikely to be required for today's workloads, but the design remains available if future datasets
or workflows justify parallelism. Phase 1b retained (correct, verified, and the right work for
the future real-time path).

**Remaining.** (1) full-day `arrow` rebuild + `--verify` against a full-day reference + peak-RSS check;
(2) on pass, flip `config.yaml` default to `arrow`; (3) later, remove the legacy `executemany` path if it
no longer adds value.

## 2026-07-12 — Phase 1b: replay perf, NumPy→pure-Python (in progress, one hotspot per commit)

**Why.** Offline analytics replay took ~3h52m for a full day (single synchronous pass; cost is entirely
per-strike-per-second Python/NumPy metric compute, not the DuckDB write). Phase 0 established a fixed-slice
benchmark harness (`benchmark.py`), a slice reference, a measured baseline (wall 204.3 s), and a cProfile
hotspot ranking. Phase 1b converts the tiny-array NumPy bodies to pure Python, one hotspot per commit,
each gated by `--verify` zero-drift.

**Measurement methodology (user-approved).** Full-slice wall has ~±10 % run-to-run variance (~±20 s), which
swamps a single hotspot's ~2–5 s contribution — so per hotspot: (1) an **isolated microbenchmark** is the
primary gain signal, (2) `--verify` is the correctness gate, (3) the full-slice replay is used only as a
regression check + to measure the **cumulative** phase gain. A periodic full-replay re-profile keeps the
microbench honest — the profiler is the tie-breaker on the real workload.

**Hotspots landed.**
1. **`round_number_depth` (M18), `metrics/per_strike.py:_round_depth`** — vectorised
   `np.isclose(np.remainder(px, r), …)` mask + `qty[mask].sum()` → pure-Python loop reproducing numpy's
   default isclose tolerances exactly (`|rem| ≤ 1e-8`, or `|rem − r| ≤ 1e-8 + 1e-5·r`). Microbench (mult
   `(5,10)`): **33.7× @ n=5, 11.5× @ n=20, 5.0× @ n=50**. `--verify`: no drift. Commit `99b1302`.
2. **rolling window reduces, `metrics/rolling.py`** — `_slope` (closed-form exact `sum(x)`/`sum(x²)` +
   pure-Python y-sums), `_spread_stats` + `_wobi_stats` (shared `_mean_std_minmax()`: one-pass mean /
   population std / min / max); dropped the module's unused `import numpy as np`. (`_micro_price_rv` was
   already pure Python — its cost is series re-extraction, a 1c item.) Microbench: `_slope` 4.9–11.9×,
   `_spread_stats` 6.8–22.3×, `_wobi_stats` 7.3–14.8× (n=5/10/30); max abs diff vs numpy **2.2e-16**.
   `--verify`: no drift. **Cumulative slice wall 204.3 → 179.7 s** (CPU 148.3 → 125.7 s). Re-profile:
   `np.isclose` gone, `ufunc reduce` 2.81 → 1.18 s, `_var` 1.50 → 0.47 s. Commit `db55f31`.
3. **per-strike reduces, `metrics/per_strike.py`** — `_side_wall_score` (`np.argmax`/`np.delete`/`np.median`
   → pure Python: inline first-max argmax, comprehension delete+filter, sort-based median) and `_confidence`
   (`np.std` → `_pop_std()` population std). `_wall` (M20) argmax **kept numpy** — microbench showed the
   pure-Python loop is 2.5× slower on 50-level NIFTY books (~84% of load), so converting would regress.
   Microbench: `_side_wall_score` 3.3–16×, `_confidence` std 22–25×; max abs diff 0.0 / 2.2e-16. `--verify`:
   no drift. Re-profile: `_side_wall_score` dropped out of the top-18, `_var` calls 33577 → 17160 (remainder
   is `processor._wall`), cProfile compute 17.9 → 15.3 s (−2.6 s). Commit `b03e14d`. *(Full-slice wall was
   contention-noisy this session — 179.7/209.9/235.3 s across runs — so microbench + cProfile are the
   authoritative signals; a clean cumulative wall is taken at the 1b phase boundary.)*

4. **`processor.py:TickProcessor._wall`** — `np.concatenate` + `np.argmax` + `.mean()` + `.std()` over the
   combined book (≤100 levels) → pure-Python argmax + one-pass mean/std. **Net win at every size** (8.9× @ 10,
   2.84× @ 60, 1.81× @ 100) *because* it makes 4 numpy calls + an allocation (contrast the per-strike `_wall`,
   argmax-only, where numpy won). Outputs are exact array elements; mean/std only pick the boolean threshold —
   microbench: max abs diff 0.0, **0 flips / 40k**. `--verify`: no drift. Re-profile: `_var` gone from the
   top-16, `ufunc reduce` 0.97 → 0.85 s, cProfile compute 15.29 → **14.57 s**. Commit `b7c6343`.

**Cumulative so far (baseline → after hotspot 4), cProfile on the fixed slice (contention-independent
metric-compute measure):** **28.33 s → 14.57 s (−13.76 s, ~49 % of profiled compute eliminated, 1.94×)** —
28.33 (baseline) → 17.93 (1+2) → 15.29 (3) → 14.57 (4). The slice row count is fixed; this is pure compute
reduction. An authoritative wall/CPU number is deferred to the 1b phase boundary (after hotspot 5) on a
quiet machine.

5. **`snapshot._parse_side` — KEPT numpy (negative result).** Microbench: only 1.06× at 50 levels (NIFTY,
   the dominant load), and `np.argsort` (quicksort, unstable) vs Python stable `sorted` produced different
   tie-order on 40,458/50,000 duplicate-price cases — a divergence-from-reference risk for ~0.2 % overall
   gain. Per the stopping criterion, left as-is. No code change.

**Affected files.** `metrics/per_strike.py`, `metrics/rolling.py`, `processor.py` (+ dev-only `benchmark.py`
from Phase 0). Docs: this CHANGELOG + the peppy-dolphin plan doc.

**Phase 1b concluded** (hotspots 1–4 converted, 5 kept numpy).

### ⚠ Critical finding while measuring the 1b phase boundary — the real bottleneck is the DuckDB write

An **un-profiled** phase-breakdown of the fixed slice (201 s wall) shows metric compute (`emit_second`) is
only **4.3 s (~2 %)**; **`DuckDBAnalyticalWriter.finalize()` is 196.8 s (~98 %)**. Root cause: `finalize()`
(`database_writer.py:729`) uses `con.executemany("INSERT … VALUES (?,…)", rows)` — row-by-row parameterized
INSERT, a pathological anti-pattern for DuckDB's vectorized columnar engine. It scales linearly and
**explains the original 3h52m full-day run** (196.8 s × 5.95M/74k ≈ 4.4 h). Phase 0's "cost is in metric
compute, not the write" was a cProfile artifact (cProfile inflates the Python metric loop and under-weights
the single GIL-released `executemany` C-call). **Proven fix:** Arrow columnar bulk insert
(`pa.table(cols)` + `INSERT … SELECT * FROM arrow_tbl`) — **1.06 s vs 77.2 s, 72.6×**, exact row parity.
This becomes the #1 lever (offline); Phase 1c/1a/1d deferred, Phase 2 deferred pending evaluation after
chunked Arrow (unlikely required for today's workloads, but retained if future workloads justify it). **Implementation
pending user go-ahead** (see the peppy-dolphin plan's "CRITICAL FINDING" section).
Then cumulative full-slice benchmark + re-profile → 1c.

**Deferred (per-strike `.sum()` family).** The M5–M17 numpy `.sum()` reduces are left as numpy: the ratio
sums (raw_obi, stack ratios, OBI) are individually below the profile noise floor, and the absolute persisted
sums (`book_pressure`, `effective_depth`, magnitude ~1e6) carry an 8-way-vs-sequential summation-order risk
(~1e-8 abs) that could breach the 1e-9 verify gate. Revisit only if the profile elevates them.

## 2026-07-07 — P10-E: live validation (patched platform) + 4 bug fixes

**What / why.** Ran P10-E live against the channel-spread-patched OpenAlgo (fresh instance) with a
compressed session to exercise the real timer-based graceful teardown. **Result: PASS with two known
WARNs** (SENSEX 5-level BFO degrade §9; `cycle_ms` > 15 ms). Whole NIFTY chain now streams true TBT depth
(NFO `depth_levels` up to 47 across ~16 channels; no global FYERS cap); `actual_depth={NIFTY:50,SENSEX:5}`;
handles flat (no leak); graceful teardown → clean EOF → auto-reprocess → DuckDB (291 837 rows, 0 corrupt);
EOD report exit 0, no FAIL. Full results in `LIVE_RUN.md` §C (P10-E) and the detailed `phase_10E_notes.md`;
operator guide added in `operator_notes.md`. Four bugs the live full-depth data surfaced were fixed, plus a
perf micro-opt, an E4 target re-tune, and an E8 verify tolerance (regression tests added; suite **257 green**):

1. **regime `theta_pressure: 5.0e6` → PyYAML string** crashed the classifier mid-session (`float > str`)
   once full-depth NIFTY made NOP non-null. Fixed literal → `5000000.0` **and** added numeric validation
   of all regime thresholds in `config.py` (loud startup failure instead of a live crash).
2. **`crossed/zero market` logged at CRITICAL** per level/second (expiry-day flood) → **DEBUG** (rate is
   in the EOD report; data unchanged).
3. **`actual_depth` health map first-write-wins** (froze on an OTM strike, dropped BFO/SENSEX) → **max-seen
   with populated-level fallback** → correct `{NIFTY:50, SENSEX:5}`.
4. **`test_integration` hardcoded a past `SESSION_DATE`** (date-rollover emptied the inspected file) →
   `now_ist().date()`.

Plus three follow-through changes (user-directed):
5. **Perf micro-opt** — removed a redundant weighted_obi/book_pressure double-compute in `processor._core`
   (output-preserving; reuses the persisted per-strike values).
6. **E4 target re-tuned 15 → 30 ms** (`eod_report._CYCLE_MS_TARGET`): `cycle_ms_p50 ≈ 22 ms` is the honest
   full-50-level cost and keeps real-time pace (~45× headroom). Per-underlying `process` sharding is
   **rejected** (wrong lever — NIFTY ≈ 84 % of load in one shard); intra-underlying parallelism **deferred**.
7. **E8 `--verify-against-live` tolerance** — added `_LIVE_SUBSET_TOLERANCE_PCT = 2.0` in `replay.verify()`
   so the disposable live store's expected second-boundary divergence passes (real session: 0.88 % of rows,
   `VERIFY OK: 658/74697 rows differ`); the strict duckdb-vs-duckdb determinism gate stays zero-tolerance.

**Affected files.** `metrics/per_strike.py`, `websocket_client.py`, `processor.py`, `config.py`,
`config.yaml`, `eod_report.py`, `replay.py`; tests `test_metrics_per_strike.py`, `test_websocket_client.py`,
`test_config.py`, `test_integration.py`, `test_replay.py`, `test_eod_report.py`; docs
`Documents/{LIVE_RUN,CHANGELOG,phase_10E_notes,operator_notes}.md` + the plan doc.

**Remaining.** Intra-underlying parallelism for further `cycle_ms` headroom is **deferred** (not needed for
real-time pace today; per-underlying sharding is documented as a non-solution).

## 2026-07-06 — P10-D: docs reconciliation (5-per-channel TBT reality)

**What / why.** Brought every doc in line with the P9 finding and the P10 build. Recorded the **live-verified
FYERS TBT cap (5 symbols/channel; OpenAlgo pins channel `"1"`)** into the **authoritative design spec** §1
depth-reality note (spec wins), and mirrored it into `CLAUDE.md` "Depth Reality" and the `PROJECT_NOTES.md`
roadmap (P9 partial pass + P10-A..E). Filled `LIVE_RUN.md` §C with the P9 results and added the
channel-patch precondition to §A. `SETUP.md` gained the dated-storage layout, `--eod-report`/`--catchup`
usage, and the TBT-patch precondition. `ARCHITECTURE.md` gained the `eod_report.py` module entry and the
P8/P9/P10 built-state narrative (storage topology was added in P10-B). No code changes.

**Affected files.** `market_depth_recorder_design.md`, `CLAUDE.md`, `PROJECT_NOTES.md`, `Documents/{SETUP,
ARCHITECTURE,LIVE_RUN}.md`. All cite `Documents/evidence/{OPENALGO_PATCH,Phase9_notes}.md`.

**Remaining.** **P10-E** — live validation next market session (apply patch + restart OpenAlgo → full NIFTY
50-level, global-cap check, authoritative perf/RSS, graceful teardown, EOD report on the session).

## 2026-07-06 — P10-C: EOD health & sanity-check report

**What / why.** New offline `eod_report.py` + `--eod-report [--date YYYY-MM-DD]` CLI that verifies a day's
captured artifacts and writes a dated PASS/WARN/FAIL report (markdown + JSON) into
`<dated-dir>/reports/eod_healthcheck_<date>.{md,json}`. It is the operator's automated "did the day capture
cleanly?" gate — it would have caught the P9 NIFTY-no-depth failure without a human noticing.

**Checks.** Tier 0 raw (HEADER/instruments/config_hash, EOF cleanliness, record count, timespan,
**per-underlying depth coverage → FAIL on 0 depth**, actual-vs-requested depth = §9 alarm, `feed_time`
coverage among TBT packets, per-level `orders`, crossed/locked share); Tier 1 live SQLite (tables +
**per-underlying option-row coverage**); Tier 2 DuckDB (tables populated + `recorder_meta` stamps, SKIP if
unbuilt); ops `health.json` (drops→FAIL, cycle<15 ms, rss<500, degraded). Worst-wins overall; **exit 0 clean
/ 1 on any FAIL**. Report-only thresholds are fixed spec (§5.1) targets, not config keys.

**First real run** on the P9 capture: **FAIL** — correctly flagged `raw.depth_coverage.NIFTY` +
`live.option_rows.NIFTY`, plus WARNs on missing EOF, SENSEX 5-level degrade, and `cycle_ms_max=25.96 > 15`.

**Affected files.** New `eod_report.py`, `tests/test_eod_report.py` (15), `Documents/eod_report.md`;
`__main__.py` (CLI wiring + `--date` guard). Full suite **252 passed**.

**Deferred.** SETUP.md `--eod-report` usage + ARCHITECTURE/spec reconciliation → **P10-D**.

## 2026-07-06 — P10-B: dated storage inside the package

**What / why.** Relocated the recorder's data **inside** the package (`output_dir → ./market_depth_recorder/
data`) and added an **opt-in dated-sub-folder layout** so every artifact for a trading day is grouped:
`data/<YYYY-MM-DD>/{raw .jsonl.gz, live .db, .duckdb, reports/}`. New `recorder.date_partitioned: true`
(validated bool, optional→flat). **Operational singletons stay at the base dir** (`health.json`,
`reprocess.log/.lock`) so `--status`, the run-lock, and the reprocess launcher stay date-agnostic.

**How.** New `utils.session_output_dir(output_dir, session_date, date_partitioned)` → the effective per-day
dir; wired into `RawTickFileWriter` + `SQLiteLiveWriter`. Replay/reprocess place the canonical DuckDB and
derived live-store **beside the raw log** (`os.path.dirname(raw)`) — flat/partitioned-agnostic — and
`catchup` globs both the base and dated sub-folders (union, sorted by filename). `config_hash` unchanged
(paths aren't part of the formula).

**Affected files.** `config.yaml`, `config.py`, `utils.py`, `file_writer.py`, `database_writer.py`,
`replay.py`; new `tests/test_paths.py` (9 tests). Full suite **237 passed**.

**Deferred.** ARCHITECTURE/spec storage-topology reconciliation → **P10-D**. The P9 data captured under the
old flat `SS_Projects/data` is orphaned by the relocation — the P10-C EOD tool will read an explicit
dir/date, so it can still be pointed at it.

## 2026-07-06 — P9 live run (partial pass) + P10-A OpenAlgo TBT channel-spread patch

**P9 live run.** Executed the recorder against a live OpenAlgo + FYERS session (IST market hours). Confirmed
(cannot be faked): real chain resolution; preflight actual depth **NIFTY/NFO→50, SENSEX/BFO→5** with
per-level `orders`; §9 degrade alarm; Init→Connect→Record + mid-day REST ATM seed; raw audit fields +
HEADER `instruments`; `cycle_ms_p50=10.5`/`max=14.2` (<15), `rss=51 MB`, drops=0. **3 bugs fixed** (228
tests green): (1) `instrument_manager._matches_underlying` — live master `name` is the full contract label,
not the base underlying → symbol-prefix fallback now fires whenever exact-name fails; (2) invalid
`heartbeat_timeout(12) > interval(10)` crashed `run_forever` → config `8` + new `config.py` validation rule;
(3) preflight infers depth level count from `len(depth["buy"])` when `depth_levels` absent (5-level packets).
Full record: `plans/Plan_001_evidence/Phase9_notes.md`.

**Headline finding.** FYERS TBT 50-level depth caps at **5 symbols per channel**, and OpenAlgo hardcoded
`channel="1"` → effective ceiling 5 total. 80 NIFTY `:50` legs → NIFTY captured **0 depth**; SENSEX (non-TBT
HSM 5-level) fine. → P10.

**P10-A (this entry).** Patched the **platform** FYERS adapter to pack 50-depth subs 5-per-channel across
channels 1–50 (ceiling 5→250). New `_assign_tbt_channel()` + class consts; reuses an existing symbol's
channel on reconnect (race-free — caller holds `self.lock`); 250-ceiling → ERROR. TBT client already resumes
new channels + resubscribes per channel, so no client change. `py_compile` OK.

**Affected files.** *Platform:* `broker/fyers/streaming/fyers_websocket_adapter.py` (patch). *Recorder fixes:*
`instrument_manager.py`, `config.py`, `config.yaml`, `websocket_client.py`, `tests/conftest.py`. *Docs:* new
`plans/Plan_001_evidence/Phase9_notes.md`, `Documents/evidence/openalgo_platform/OPENALGO_PATCH.md`, `Documents/evidence/openalgo_platform/openalgo_fyers_tbt_channels.patch`.

**Deferred.** Live smoke of the patch (needs OpenAlgo restart) → **P10-E1/E2**; whole-chain 50-level,
global-cap check, authoritative perf/RSS, graceful teardown → **P10-E**. Dated storage (**P10-B**), EOD
health/sanity report (**P10-C**), and the ARCHITECTURE/CLAUDE/spec Depth-Reality reconciliation (**P10-D**)
are the next phases.

## 2026-07-06 — P8: Offline integration & soak harness + perf/RSS instrument + SIGTERM

**What / why.** The final planned phase. Builds the **automated whole-pipeline harness** (the real
four-thread pipeline end-to-end, driven by a scripted recorded feed + the real reprocess subprocess) that
the P6 docs had claimed but never committed as code; adds the perf/memory instrumentation the `<15 ms` /
`<500 MB` targets need; and closes the managed-shutdown gap with a SIGTERM handler. The **live**
confirmations (FYERS actually delivering 50-level depth, per-level `orders`) become a separate operator
phase **P9** — see `Documents/LIVE_RUN.md` — because they cannot be faked; run when the market is open.

**Forks resolved (user, 2026-07-06).** (1) E2E approach → **build both**: P8 = offline harness (now),
P9 = live run (runbook now, executed later). (2) RSS → **stdlib platform-adaptive** (`ctypes` on Windows,
`getrusage` on Unix — no `psutil`). (3) SIGTERM → **add a graceful-teardown handler**. (4) Cycle timing →
**permanent, surfaced in `health.json`**.

**Added.**
- `tests/test_integration.py` — `@pytest.mark.integration` whole-pipeline harness: `RecordedTransport`
  (a real `FeedTransport` playing a self-paced NIFTY-50-level / SENSEX-5-level feed) drives the real
  `_build_default_pipeline`; asserts clean thread joins, a `HEADER..EOF`-framed raw `.gz` with the
  `instruments` block, depth audit fields preserved (`feed_time`/`depth_levels`/`is_50_depth`/per-level
  `orders`), a populated live `.db`, `health.json` perf fields, and **no FD residue**; then runs the real
  `--replay --catchup` **subprocess** → DuckDB (`built_by="replay"`) and proves determinism via
  `replay.verify`.
- `Documents/integration.md` (harness + whole-pipeline FD audit); `Documents/LIVE_RUN.md` (P9 runbook).

**Edited (small, additive).**
- `utils.py` — `process_rss_mb()` (F6): stdlib platform-adaptive RSS in MiB (Windows working set via
  `ctypes`/`K32GetProcessMemoryInfo` with explicit `restype`/`argtypes`; Unix peak `ru_maxrss`).
- `processor.py` — `perf_counter` around `emit_second` (single-owner, no lock); `cycle_ms_p50`/
  `cycle_ms_max` in `stats()`.
- `main.py` — `build_health()` adds `cycle_ms_p50`/`cycle_ms_max`/`rss_mb`; `read_status` prints them.
- `__main__.py` — `_install_sigterm_handler` / `_make_sigterm_handler` wired into `_cmd_run` (live daemon
  only) → `orchestrator.stop()`.
- `tests/{test_utils,test_processor,test_main}.py` — RSS, cycle-time, SIGTERM, and health/status field
  coverage. `tests/conftest.py` — register the `integration` marker.

**Verification.** Full `pytest market_depth_recorder/tests/ -q` **228 passed** (221 prior + 7 new), no
live feed/broker; the integration harness rebuilds a DuckDB store from a thread-produced raw log via the
genuine subprocess and verifies determinism. **Whole-pipeline FD audit** (assertion-backed): every worker
joined (no `is_alive()` after teardown), raw gzip HEADER..EOF, live SQLite opened+closed, DuckDB build
conn closed, subprocess reaped, no `.tmp_`/`.building_`/`.lock` residue; `process_rss_mb`/SIGTERM add no
FD. **Genericization** grep of `utils/processor/main/__main__.py` clean (NIFTY/SENSEX live only in the
test's canned chain). **Doc correction:** the P6 "real four-thread e2e smoke" claim (which was a manual
check, not committed code) is now accurate.

**Deferred.** P9 live-run execution (needs a live FYERS session during market hours).

## 2026-07-06 — P7: Replay + DuckDB writer (`replay.py`, `database_writer.py::DuckDBAnalyticalWriter`)

**What / why.** Builds the **offline** path — replay the lossless Tier-0 raw `.jsonl.gz` through the
**same** `TickProcessor` (full metric catalog) and bulk-load the fat Tier-2 DuckDB analytics store. This
is the normal way Tier 2 exists (the P6 M6 reprocess shells out to `--replay --catchup`; it now runs a
real build) and the determinism harness (`--verify`). After P7 both tiers are complete — only P8
(integration & soak) remains. Verified end-to-end: the exact M6 `--replay --catchup` subprocess rebuilds
a DuckDB store (5 spot / 30 option / 15 agg rows, `built_by="replay"`) from an enriched raw log.

**Forks resolved (user, 2026-07-05).** (1) Instrument context → **enrich the raw HEADER** with the
resolved chain (self-contained, correct for any-age log). (2) Replay clock → **`recv_ts`** (the recorder
clock the live resampler/staleness used → second-for-second parity). (3) DuckDB bulk load →
**`executemany`, no new dep**. (4) Verify → **both modes**.

**Decisions (plan doc 65–72).** HEADER enrichment via `to_header_dict`/`from_header` (65); `recv_ts`
virtual clock (66); synchronous processor reuse + a thin public `TickProcessor.ingest` (67); plain
`with`-managed `DuckDBAnalyticalWriter`, `executemany` bulk, temp-file-then-rename idempotency (68);
`--catchup` oldest-first self-heal (69); `--verify` both modes with schema/config_hash gate + tolerance
diff (70); robust reader — corrupt-line/missing-EOF/multi-HEADER (71); `--underlying`/`--from`/`--to`
filters with a warm-up caveat (72).

**Added files.**
- `replay.py` — `_load_header`/robust packet reader; `replay_file` (recv_ts-driven synchronous drive →
  DuckDB); `catchup`; `verify` (+ `_read_table`/`_read_meta`/`_values_equal`/`_live_column_set`);
  path resolvers (`canonical_output`/`replay_side_output`/`live_store_path`).
- `tests/test_replay.py` — 15 offline tests. `Documents/replay.md`.

**Edited files.**
- `database_writer.py` — `DuckDBAnalyticalWriter` body + `_DUCKDB_DDL` (§4.1a). `tests/test_database_writer.py`
  — replaced the deferred-stub test with 4 DuckDB writer tests (DDL/provenance, round-trip + NULL +
  `is_50_depth`→BOOLEAN, idempotent fresh file, discard-on-error).
- `instrument_manager.py` — `to_header_dict()` + `from_header()` (+ `_extract_data_obj` already from P6).
- `file_writer.py` — HEADER `instruments` block (new optional `instruments=` arg).
- `main.py` — orchestrator passes `im.to_header_dict()` to the raw writer (guarded for fakes).
- `processor.py` — thin public `ingest(pkt)`.
- `__main__.py` — replaced the `--replay/--catchup` stub with `_cmd_replay` (output resolution, verify
  dispatch, filters, exit codes).
- `market_depth_recorder_design.md` §8.3 (recv_ts basis) + §3.5.4 (HEADER `instruments`); `PROJECT_NOTES.md`.
- `Documents/{database_writer,file_writer,instrument_manager,ARCHITECTURE}.md`.

**Verification.** Full `pytest market_depth_recorder/tests/ -q` **221 passed** (203 prior − 1 removed stub
+ 4 DuckDB + 15 replay). `--replay` builds the four §4.1a tables + `recorder_meta`; `--verify` clean on a
re-replay (determinism); a perturbed metric → drift; `--catchup` self-heals; `--verify-against-live`
live-subset matches a real SQLite live store; rolling warm-up NULLs. **FD audit:** the DuckDB build
connection is `with`-closed + CHECKPOINT + temp→rename on every path (finalize/exception/discard); the gzip
reader is `with`-closed; `verify`/`catchup` read-only connections closed in `finally`; replay adds **no**
thread/subprocess/lock. **Genericization:** `replay.py`/DuckDB writer keyed by `name`; table/column names
are §4 schema constants imported from `processor`. **Invariants:** idempotent fresh file (§8.5); determinism
proven by `--verify`; warm-up reproduced; recv_ts live-parity; lossless raw untouched (read-only).

**Deferred.** P8 — live end-to-end + whole-pipeline FD/soak, live-FYERS depth confirmations, performance
sanity. A pre-enrichment (headerless-`instruments`) log is not self-contained → `from_header` raises a
clear error (there are no such production logs; all P7+ logs carry the block).

## 2026-07-05 — P6: Orchestrator (`main.py::RecorderOrchestrator`)

**What / why.** Builds the **conductor** — the missing piece that constructs, wires, supervises, and
tears down the four-thread live pipeline P0–P5 built as standalone workers. `main.py` owns the §3.1.1
milestone state machine + 1-second loop, the three queues / two shutdown events / `error_queue`,
mid-day-restart recovery, the health file, the session guards (disk + trading calendar), and the
end-of-session reprocess subprocess launcher. It is the `default` (no-mode) CLI entry and implements
`--status`. After P6 the only unbuilt module is P7 (replay/DuckDB). Verified end-to-end against a no-op
transport: real threads build/start/join cleanly (none left alive → no leak), raw `.gz` framed
`HEADER..EOF`, live `.db` created, `health.json` written, reprocess launched with the right command.

**Decisions (plan doc 56–64).** Act-at-launch milestones, record-gate at `session_start` (56);
mid-day-restart ATM seed via new `RestClient.get_quote` + `mark_restart_boundary`, WS fallback (57);
in-process supervisor restart, bounded → fail-fast (58); build the M6 reprocess launcher now, tested
against a stub (59); two-signal teardown in spec drain order **feed → processor → db_writer** (raw
parallel) (60); small additive touches to P1/P2/P3 (61); the §6.4 health payload + `--status` (62);
disk + trading-calendar guards (63); two new config keys `supervisor_interval_sec`/`max_restart_attempts`
(64). **Forks resolved:** add `get_quote` (spec-faithful §3.1.2); init+connect at launch, record-gate at
`session_start`; in-process supervisor restart; build the reprocess launcher now.

**Key design point — two shutdown events.** `shutdown_event` (feed·processor·raw) is separate from
`db_shutdown_event` so teardown joins the processor first (draining `proc_queue` + flushing its final
rows into `db_queue`) and only then signals the db writer — closing the race where both would see a
shared event set with `db_queue` momentarily empty and the db writer could exit before the processor's
final rows land (§3.1.4). No change to any worker's code.

**Added files.**
- `main.py` — `RecorderOrchestrator` (milestone loop, `_build_default_pipeline`, `_seed_restart`,
  `_supervisor_tick`, `_teardown_pipeline`, `build_health`/`_write_health`, disk/holiday guards,
  `_launch_reprocess` + run-lock, `_default_reprocess_launcher`) + `Milestone` enum + `read_status`.
- `tests/test_main.py` — 16 offline tests (virtual clock + fake workers via `pipeline_factory`).
- `Documents/main.md`.

**Edited files.**
- `instrument_manager.py` — `RestClient.get_quote` (+ `_extract_data_obj`); `InstrumentManager.resolved`
  property. `tests/test_instrument_manager.py` — 4 `get_quote` tests.
- `websocket_client.py` — `seed_spot`, `freeze_dsm`, `connection_status`, `last_recv_ts`,
  `_capture_actual_depth`/`actual_depth`. `tests/test_websocket_client.py` — 6 P6-touch tests
  (+ `FakeInstrumentManager.symbol_to_strike_map`).
- `file_writer.py` — `eof_written` flag (the reprocess clean-EOF gate).
- `__main__.py` — `--status` reader wired; the `default` entry now runs `RecorderOrchestrator.run()`.
- `config.py` + `config.yaml` + `tests/conftest.py` + `tests/test_config.py` — `supervisor_interval_sec`
  (≥1) and `max_restart_attempts` (≥0) §7.3 validation + negative tests.
- `Documents/{ARCHITECTURE,instrument_manager,websocket_client}.md`.

**Verification.** Full `pytest market_depth_recorder/tests/ -q` **203 passed** (175 prior + 16 main + 4
`get_quote` + 6 WS touches + 2 config); `--validate-config` → 0 (incl. two new keys); `--status` → 0 with
a friendly message when no health file exists; genericization grep of `main.py` clean; an end-to-end smoke
of the real four-thread pipeline was run **manually** here (the automated committed harness lands in P8 —
`tests/test_integration.py`). **FD/thread audit:** all four workers joined on every
path (clean teardown, crash-restart, KeyboardInterrupt); reprocess child → real log file + `.wait()`-reap
+ lock release; health temp fd closed by `atomic_write`; no thread/queue/FD leak across a supervised
restart (old objects joined + dropped before rebuild).

**Deferred.** P7 replay + `DuckDBAnalyticalWriter` (the reprocess launcher already emits the `--replay
--catchup` command against a stub in tests). Multi-day continuous looping in one process (one `run()` =
one session; the OS scheduler relaunches daily). Live end-to-end + whole-pipeline soak = P8.

## 2026-07-04 — P5: SQLite live writer (`database_writer.py::SQLiteLiveWriter`)

**What / why.** Builds the fourth and final **live thread** — the batching consumer that drains
`db_queue` (the per-second envelopes P4 emits, previously unread) and commits the `recorder.live_metrics`
subset to the thin Tier-1 SQLite/WAL store `market_depth_live_YYYYMMDD.db` (§4.1). Closes the live path
end-to-end (feed → tee → processor → **DB**); the only unbuilt live piece left is the P6 orchestrator.

**Decisions (plan doc 48–55).** Single-owner `sqlite3.Connection`, no lock, opened inside `run()`
(decision 48); column order imported from `processor` so INSERTs can't drift from the emitted tuples (49);
injected clock + session date (50); batch commit on size OR `batch_write_interval_ms` (51); `recorder_meta`
stamped once at DB creation, `built_by="live"` (52); PASSIVE checkpoint cadence + teardown TRUNCATE +
optimize, **no VACUUM** — §4.4 authoritative over §3.6.4 (53); corruption recovery on open — `quick_check`
→ archive `.corrupt_<epoch>.bak` + rebuild, non-fatal since the fat store rebuilds from raw (54); health
counters `rows_written`/`rows_ignored_total`/`commit_error_count`/`corruption_recoveries` (55).

**Forks resolved (plan doc A–C).** (A) Boundary-second `INSERT OR REPLACE` **deferred to P6**: P5 ships
steady-state `INSERT OR IGNORE` + count/log and exposes `mark_restart_boundary(ts)` for P6 to drive.
(B) Added §7.3 validation for `batch_size`/`cache_size_mb`/`wal_checkpoint_interval_sec`. (C) Deferred
`DuckDBAnalyticalWriter` stub raising `NotImplementedError` at construction (P3 `SdkTransport` precedent).

**Added files.**
- `database_writer.py` — `SQLiteLiveWriter(threading.Thread)`: DDL constants (4 tables §4.1 + 4 indexes
  §4.2 + `recorder_meta` §4.1b), `_open_db`/`_quick_check_ok`/`_recover_corrupt_db`/`_apply_pragmas`/
  `_create_schema`, `_buffer`/`_maybe_flush`/`_commit` (IGNORE/REPLACE + PK-collision count), periodic
  `_maybe_checkpoint`, `_teardown_pragmas`, defensive `_maybe_rollover`, `mark_restart_boundary`, and the
  deferred `DuckDBAnalyticalWriter` stub.
- `tests/test_database_writer.py` (14 tests).
- `Documents/database_writer.md`.

**Changed files.**
- `config.py` — §7.3 rules: `batch_size` ∈ [1,5000], `cache_size_mb ≥ 1`, `wal_checkpoint_interval_sec ≥ 30`.
- `config.yaml` — annotated the three keys' bounds.
- `tests/test_config.py` — one negative case per new rule.
- `Documents/{ARCHITECTURE,CHANGELOG}.md`.

**Verification.** Full suite **175 passed** (158 prior + 14 writer + 3 config) with no live feed.
`--validate-config` → 0 on the shipped config, → 1 with the exact message on each seeded-bad key.
Round-trip proof for all four tables (`None` → NULL, column-for-column), batch flush by size and by time,
PK-collision IGNORE count, `mark_restart_boundary` → REPLACE + revert, PASSIVE checkpoint cadence,
teardown TRUNCATE+optimize (no VACUUM), corruption archive+rebuild, graceful drain via the real thread.
**FD audit:** one `sqlite3.Connection` opened in `run()` and closed in `run()`'s `finally` on every path
(clean, exception, shutdown, corruption-rebuild, date-rollover); `run()` hardened so a *partial* `_open_db`
still closes its FD; corruption recovery closes the bad conn before reconnecting; DuckDB stub holds nothing.
**Concurrency:** single-owner connection + state, no lock; cross-thread edges only the thread-safe
`db_queue` and the atomic single-word `mark_restart_boundary` hand-off. **Genericization:** no
index/exchange/strike/CE-PE literal — table/column names are §4 schema constants; symbols flow from
envelopes.

**Deferred.** Boundary-`INSERT OR REPLACE` wiring (P6 drives `mark_restart_boundary`); orchestrator +
health file + `proc_queue`-side shedding (P6); DuckDB analytical writer + replay `--verify` (P7).

## 2026-07-04 — P4b: Rolling windows + aggregates + regime (`metrics/rolling.py`, `metrics/aggregate.py`)

**What / why.** Completes the compute core's metric catalog. `TickProcessor.emit_second` now emits **all
four** §4.1 tables: it back-fills the instantaneous `ofi` on `option_strike_metrics`, emits
`strike_window_metrics` (§3.4.3 rolling windows, one row per `(symbol, w∈time_windows_sec)`), and
`aggregated_window_metrics` (§3.4.4 multi-strike aggregates + regime, one row per `(underlying,
SMALL/MEDIUM/LARGE)`). Compute order is per-strike → rolling → aggregate → regime (decision 37). P7 reuses
all these bodies verbatim (adds only replay + DuckDB, no new math).

**Decisions (plan doc 43–47).** Family-specific bound signatures — rolling `fn(hist, n, ctx)`, aggregate
`fn(ce, pe, ctx)`, scalar `fn(view, ctx)` (43); single-owner P4b engine state (`_window` deques +
`_prev` touch-books, `maxlen = 2·max(window)+1`), no lock (44); windowed liquidity = window **sums** of
per-second price-aligned ΔQ (45); per-underlying regime + pinning written identically into all three
window rows (46); rolling `min_depth` inherited via `None` inputs — a shallow/stale second contributes
`None` and is skipped (47).

**Added files.**
- `metrics/rolling.py` — §3.4.3 window bodies (price_return, spread/wobi stats, regression slopes,
  micro-price RV, windowed liquidity flow/churn/intensity, pressure velocity/accel, wall persistence/
  events, `ofi_sum`) + the instantaneous `ofi_instant` / `liquidity_delta_instant` helpers + the
  `HEAVY_METRICS` degraded-skip set.
- `metrics/aggregate.py` — §3.4.4 per-window bodies (depth_pcr, consolidated_pressures, pooled `bnet`,
  spread_diff, net_options_pressure), per-underlying `pinning_score`/`regime`, and the `compute_underlying`
  ATM-window-slicing orchestrator.
- `tests/test_metrics_rolling.py` + `tests/test_metrics_aggregate.py`.

**Changed files.**
- `processor.py` — P4b wiring in `emit_second`: `_compute_option` (per-strike + rolling + aggregate
  feature), `_core`/`_wall`/`_instantaneous`/`_append_sample`/`_window_rows`/`_agg_rows`/`_strike_step`,
  `STRIKE_WINDOW_COLUMNS`/`AGG_COLUMNS`, degraded heavy-skip, per-underlying agg radii. Still no lock, no
  FDs.
- `metrics/snapshot.py` — `WindowSample`, `StrikeFeatures`, `TouchBook` + `touch_book()`; `MetricContext`
  gains `regime`.
- `metrics/__init__.py` — imports `rolling` + `aggregate` so their bodies bind at package import.
- `tests/test_processor.py` — P4b integration (four tables, `ofi` back-fill, dependency closure, degraded
  heavy-skip keeps cadence, full determinism); the P4a envelope test now tolerates the two new tables.
- `Documents/{processor,metrics,ARCHITECTURE}.md`.

**Verification.** Full suite **158 passed** (130 prior + P4b, incl. two fixed pre-existing tests) with no
live feed. Rolling/aggregate bodies verified against hand-computed fixtures (price-aligned add/remove,
slopes, RV with a skipped stale second, OFI sign + boundary NULL, wall persistence/events, both-sides PCR,
pooled `bnet` window-invariance, all five regime labels); engine integration covers four-table emission,
`ofi` back-fill after the boundary second, dependency closure, degraded heavy-skip keeping the 1s cadence,
and full `emit_second` determinism. **FD audit:** processor still holds no files/sockets/DB/subprocess —
only queues/arrays/deques. **Concurrency:** single-owner state, no lock; cross-thread edges only the two
thread-safe queues. **Genericization:** no index/exchange/strike/CE/PE literal in `rolling.py`/
`aggregate.py`/`processor.py` — CE/PE from the InstrumentManager map, windows/radii/thresholds from config,
all state keyed by `name`.

**Also fixed (pre-existing, exposed by this run).** (1) `test_write_error_counted_and_thread_survives`
(P2) was **date-dependent**: it used the real clock, so the defensive IST rollover fired once the calendar
passed its hardcoded `session_date` (2026-07-03 → -04) and consumed the FakeHandle's one failing write on
the EOF marker — fixed by injecting the existing fixed `Clock()` (the design's inject-the-clock rule). No
production code changed. (2) The P4a `test_emit_produces_spot_and_option_envelopes` assertion was tightened
to a subset check now that `active="all"` emits four tables.

**Deferred.** SQLite live writer (P5 — *now done, see the P5 entry above*), orchestrator + health file +
proc_queue-side shedding (P6), DuckDB analytical writer + replay `--verify` (P7). Process-sharding
(`processor.mode: process`) remains §5.2 headroom.

## 2026-07-03 — P4a: Processor engine + per-strike metrics (`processor.py`, `metrics/`)

**What / why.** The compute core: `TickProcessor`, the third pipeline thread, drains `proc_queue`,
keeps a uniform 1-second grid, and turns each second's option-book snapshots into `spot_states` +
`option_strike_metrics` rows on `db_queue` (§3.4.1). It binds the actual NumPy metric bodies (M1–M29,
§3.4.2) to the registry specs P0 declared as metadata-only. P4 is split (user fork): **P4a** = engine +
single-snapshot per-strike metrics; **P4b** = §3.4.3 rolling (+ `ofi`) and §3.4.4 aggregates/regime.

**Decisions (recorded in the plan doc, decisions 31–41).** Split P4a/P4b (31); metric bodies in
`metrics/` compute modules bound via a new `registry.bind()` (32); single-owner processor thread, no
lock (33); injected clock + pure `emit_second` seam for P7 replay (34); `BookSnapshot` `__slots__`
built once per (symbol,second) (35); `:50`-stripped DB symbol + option/spot/unknown classifier (36);
dependency closure + per-strike→rolling→aggregate order (37); `db_queue` `{"table","rows"}` envelope
contract in §4.1 column order (38); staleness/forward-fill + degraded skeleton keeping the 1s cadence
(39); NULL/guard matrix from `min_depth` + spec caveats (40); M22/M24 touch-history deque as P4a engine
infra, `ofi` deferred to P4b (41).

**Added files.**
- `processor.py` — `TickProcessor(threading.Thread)` (drain/classify/cache, `emit_second`, ATM
  resolution, forward-fill/staleness, degraded skeleton + critical shed, `db_queue` back-pressure,
  `stats()`); `strip_suffix`, `SPOT_COLUMNS`/`OPTION_COLUMNS`. No lock, no FDs.
- `metrics/snapshot.py` — `BookSnapshot` (best-first NumPy arrays, `__slots__`), `MetricContext`,
  `StrikeHistory`.
- `metrics/per_strike.py` — M1–M29 bodies bound via `@bind`, with all §3.4.2 corrections + guards.
- `tests/test_metrics_per_strike.py` (17 tests) + `tests/test_processor.py` (15 tests).
- `Documents/processor.md`, `Documents/metrics.md`.

**Changed files.**
- `metrics/registry.py` — added `bind(name)` (bind body to an existing spec; unknown-name fast-fail),
  `resolve_active(live_metrics)` (ordered active spec set), `active_columns()`.
- `metrics/__init__.py` — imports `per_strike` so bodies bind at package import.
- `config.yaml` + `config.py` — new `metrics.fill_probe_qty` (M25 probe size) + its positive validation;
  `tests/conftest.py` fixture updated.
- `Documents/ARCHITECTURE.md` — P4a built state + updated thread/queue topology.

**Verification.** Full suite **129 passed** (98 prior + 31 new) with no live feed; per-strike metrics
verified against hand-computed values + every guard; engine covers classify/emit/ATM/staleness/
forward-fill/thin-selection/degraded/determinism + a real-thread graceful-drain. FD audit: the
processor holds no files/sockets/DB/subprocess — only queues/arrays/deques (zero FD surface).
Concurrency: single-owner state, no lock; cross-thread edges are only the two thread-safe queues.
Genericization: no index/exchange/strike/CE/PE literal in `processor.py` or the metric modules.

**Deferred.** §3.4.3 rolling metrics + the `ofi` column and §3.4.4 aggregates/regime → **P4b** (so only
`spot_states` + `option_strike_metrics` are emitted now). Heavy-rolling degraded skip set, proc_queue-side
shedding + health-file wiring → P4b/P6. Minor structural refinement: `BookSnapshot`/`MetricContext` live
in `metrics/snapshot.py` (not `processor.py`) to avoid a processor↔metrics circular import.

## 2026-07-03 — P3: WebSocket client + DSM (`websocket_client.py`)

**What / why.** The first **networked** module and the tick producer: a `DepthWebSocketClient` FEED
thread that owns the feed transport, the Dynamic Strike Manager (DSM), the tee into
`raw_file_queue`/`proc_queue`, the recorder-owned reconnect state machine, and the live
depth-capability preflight (§3.3/§6.1/§3.2.5/§9). It closes the loop from "resolved chains" (P1) to
"packets flowing into the audit + analytics queues" (P2 writer downstream).

**Decisions (recorded in the plan doc, decisions 20–30).**
- **Transport seam (20)** — `FeedTransport` protocol; `RawWSTransport` built (default), `SdkTransport`
  a deferred fail-fast stub. The SDK depth callback strips the audit fields, so raw stays default.
- **Canonical packet = wire message, lightly normalized (21)** — `symbol` kept **as received** (keeps
  `:50` on depth topics, §3.3.3); the same dict is teed to both queues; DB-symbol stripping is downstream.
- **Native heartbeat (22)** — `run_forever(ping_interval, ping_timeout)`, no hand-rolled monitor thread.
- **One FEED thread + three locks (23/24)** — `_spot_lock → _sub_lock` order, `_client_lock` independent;
  `connect/disconnect` off `_client_lock`; no I/O under any lock; the tee is lock-free.
- **Lazy DSM seeding (25)** — boundaries seed from the first valid spot tick; P6's REST one-shot feeds the
  same `on_spot` entry, so P3 needs no REST/quotes.
- **Never-shrink (26)** — subscriptions only grow intra-session; `active_subscriptions` holds wire symbols.
- **Tee backpressure (28)** — proc sheds first (WARNING+count), raw sheds last (ERROR+count, the single
  sanctioned raw-loss boundary).
- **`--preflight` graceful-degrade (30)** — offline resolve is a prerequisite (exit 1 on REST failure);
  the live depth probe is best-effort (unreachable WS → `actual_depth=<unreachable>`, exit 0).

**Added files.**
- `websocket_client.py` — `FeedTransport`/`RawWSTransport`/`SdkTransport(stub)`/`make_transport`;
  `DepthWebSocketClient(threading.Thread)` (tee, DSM `_on_spot`/`_check_boundaries`, subscription flow +
  never-shrink, reconnect loop with injected `sleep_fn`, `on_open` auth+resubscribe); module helpers
  `wire_symbol`/`normalize_market_data`; `run_depth_preflight` + `DepthProbeResult` (§3.2.5/§9). One FD
  (WS socket), closed on every path; close-before-reconnect.
- `tests/test_websocket_client.py` (19 tests) — tee both-queues + shed order + raw-drop accounting;
  spot routing; DSM seed/upper-breach/lower-breach (gradual ramps within the 2% spike guard)/spike +
  non-positive rejection; never-shrink on pullback; reconnect auth+spot+resubscribe; disconnected-
  subscribe flushed on reconnect; deterministic backoff sequence; wire-symbol + normalize helpers;
  live preflight reads `depth_levels`/`is_50_depth`/`orders` + WARNs on `actual<requested`; unreachable
  probe degrades fast. All offline (fake transport + injected clock/sleep).
- `Documents/websocket_client.md` (new per-module doc).

**Changed files.**
- `__main__.py` — `_cmd_preflight` re-pointed from P1's offline `<pending>` to the live probe
  (graceful-degrade to `<unreachable>` + exit 0).
- `tests/test_instrument_manager.py` — the two `--preflight` tests updated for the live-probe output
  (`actual_depth=50` / `<unreachable`); added a WS-unreachable-exit-0 CLI test.
- `Documents/ARCHITECTURE.md` (P3 built state; topology now shows the FEED thread + tee + locks;
  transport + CLI notes updated), `Documents/instrument_manager.md` (`--preflight` now live).
- Live plan doc P3 section expanded with decisions 20–30 + subtask checklist.

**Deferred.** `SdkTransport` body (post-P3, additive against the seam); `--status`/orchestration/
teardown/REST-quote mid-day seeding (P6); the resampler/metrics that consume `proc_queue` (P4).

**Verification.** `python -m pytest market_depth_recorder/tests/ -q` → **98 passed** (79 prior + 19
new), no live feed. `--validate-config` → exit 0; `--preflight` without a server → exit 1 at REST
resolution (the documented prerequisite). Genericization grep on `websocket_client.py` → only a
doc-comment `NIFTY/SENSEX` mention; `:50`/`5` are cited transport constants (`_TBT_SUFFIX`/
`_TBT_MIN_DEPTH`). A **real bug the tests caught:** the initial breach tests jumped spot >2% in one
tick and were (correctly) rejected by the DSM's own spike guard — fixed the tests to ramp gradually,
confirming the guard behaves as specified.

## 2026-07-03 — P2: Tier-0 gzip file writer (`file_writer.py`)

**What / why.** The first background writer thread and the first stage of the pipeline: drains
`raw_file_queue` and appends every WS packet to the daily gzip JSON Lines log — the **lossless source
of truth** (§1.4) both derived stores rebuild from. Isolating file I/O to this thread shields the feed
receiver from disk latency (§3.5).

**Decisions (recorded in the plan doc, decisions 15–19).**
- **Single-owner FD, no lock** — the gzip handle is touched only by `run()`; exclusive ownership is
  stronger than a lock.
- **Injected clock (`time_fn`)** — sole source of epoch timestamps, the fsync cadence, and the rollover
  date, so every time branch is deterministic under test.
- **Append mode (`gzip.open("at")`)** — a same-day restart appends a second HEADER (records the restart)
  rather than truncating prior audit data.
- **Write-failure = the one sanctioned raw-loss boundary** — caught, `write_error_count`++, ERROR-logged,
  thread continues (§1.4). Sentinel-error-queue wiring deferred to P6 (optional `error_queue` hook left).
- **Tests round-trip via stdlib `gzip`+`json`** (pandas isn't a pinned dep); one `importorskip("pandas")`
  compat check honors the §3.5.1 tooling claim.

**Added files.**
- `file_writer.py` — `RawTickFileWriter(threading.Thread)`: `resolve_filename` (staticmethod), HEADER at
  open + EOF on clean drain (`SCHEMA_VERSION`/`config_hash`/underlyings stamp, §3.5.4), two-tier flush
  (§3.5.3), defensive IST daily rollover, per-packet write-error accounting; `records_written` /
  `write_error_count` counters for P6 health. One gzip FD, closed on every path via a guarded `finally`.
- `tests/test_file_writer.py` (10 tests) — HEADER/data/EOF round-trip + exact packet equality;
  provenance stamping; cheap-flush cadence; bounded fsync cadence (spied `os.fsync` + controllable
  clock); missing-EOF + byte-truncated-tail tolerance (clean-prefix recovery); defensive rollover;
  write-error accounting (thread survives); graceful drain through the real thread; optional
  `pandas.read_json` compat.
- `Documents/file_writer.md` (new per-module doc).

**Changed files.** `Documents/ARCHITECTURE.md` (P2 built state; threading/queue topology now shows the
raw writer built; provenance bullet notes the HEADER/EOF stamp landed). Live plan doc P2 section
expanded with decisions 15–19 + subtask checklist, boxes ticked.

**Verification.** `python -m pytest market_depth_recorder/tests/ -q` → **79 passed** (69 prior + 10
new), no live feed. Tests run the writer synchronously (`run()` with a pre-set shutdown event) and via
a real started thread (`start()`/`q.join()`/`join()`), reading logs back with stdlib `gzip`+`json`.
The `-o addopts=""` flag is needed only to detach from the openalgo repo's root `pytest` addopts
(`--timeout`), unrelated to this package.

**Robustness fix caught while testing.** The rollover guard originally compared the **machine-local**
date against `session_date` (derived from `now_ist()`); on a non-IST host that mismatch would trigger a
spurious rollover on the first write. Changed to compare in **IST** (`datetime.fromtimestamp(...,
tz=IST)`), matching `session_date`'s basis — the guard now never fires spuriously in a normal session.

**FD audit (P2 surface).** Exactly one gzip handle per open, created in `_open_file` and released by a
guarded, idempotent `_close_file` (`flush` → `fsync` → `close`) inside a `finally`, so it closes on
clean drain, mid-loop exception, rollover, and shutdown alike. `fsync` guards a closed/invalid `fileno`
(`OSError`/`ValueError`). No sockets/DB/subprocess; the single thread is `join()`-reaped by the
orchestrator (P6) and is a daemon as a backstop. Tests leak no handles (fakes hold no real FD). Clean.

**Deferred.** Receiver + tee + the queues themselves → P3; sentinel `error_queue` wiring → P6; the
stores' `recorder_meta` provenance stamps → P5/P7.

## 2026-07-03 — P1: InstrumentManager (`instrument_manager.py`)

**What / why.** First live module: resolve each configured underlying's current weekly option chain
over the OpenAlgo REST API and compile the O(1) lookup structures the DSM (P3) and processor (P4)
consume. Pure resolution — no threads/DB/sockets; the only FD is a transient HTTP connection.

**Decisions (recorded in the plan doc, decisions 10–14).**
- **Live depth probe deferred to P3** (user-confirmed): reading `depth_levels`/`is_50_depth` needs a
  raw-WS subscription (the SDK strips them) and that client is P3. `--preflight` resolves the chain
  offline and reports `actual_depth=<pending P3 raw-WS probe>`.
- **`E_weekly` via `/api/v1/expiry`** (`data[0]`; the service already drops past expiries, sorts, and
  includes the expiry day → rollover gate satisfied). Master used only for the strike grid + tick_size.
- **Underlying match on the `name` column** (exact), longest-prefix `symbol` fallback for blank names
  (NIFTYNXT50 not shadowed by NIFTY).
- **Maps built from master `symbol` rows** (never string-constructed); integral strikes → `int` keys.
- **REST via stdlib `urllib`** (no new dependency).

**Added files.**
- `instrument_manager.py` — `RestClient` (urllib; instruments GET + expiry POST; 10 s timeout, ≤3
  retries on network/5xx, 4xx terminal; injectable opener), `InstrumentManager.resolve()` /
  `preflight_report()`, frozen `ResolvedChain`, and the maps (`strike_to_symbol_map`,
  `symbol_to_strike_map`, `active_strikes_list`, `tick_size_map`). Mode-based strike-step detection
  (§3.2.3) with a warned `strike_step_fallback`.
- `tests/test_instrument_manager.py` — RestClient (success/retry/timeout/5xx/4xx/bad-status/expiry
  body), resolution happy path + contaminant exclusion + blank-name prefix fallback, empty-expiry and
  no-contracts fast-fail, strike-step edge cases (wide-gap mode / single-strike / unexpected→fallback),
  expiry parse, `_option_type`/`_norm_strike`, and `--preflight` exit codes (ok/REST-fail/bad-config).

**Changed files.** `__main__.py` — `--preflight` wired to `_cmd_preflight` (offline resolve + report,
exit 0/1), replacing the P0 stub; imports `setup_logging`. `Documents/ARCHITECTURE.md` (P1 built
state), `Documents/instrument_manager.md` (new per-module doc). Live plan doc P1 boxes ticked.

**Verification.** `python -m pytest market_depth_recorder/tests/ -q` → **69 passed** (48 P0 + 21 new),
no live feed. `--validate-config` still exits 0; `--preflight` with no REST server up exits 1 with a
clean `RestError` (no traceback). All tests run against a scripted fake opener / injected `FakeRest`.
A test caught a real bug: the blank-`name` longest-prefix fallback matched `NIFTYNXT50…` to `NIFTY`
(NIFTYNXT50 isn't a configured underlying) — fixed by requiring the char after the base name to be a
digit (an F&O symbol is `BASE + DDMMMYY…`), so `…NXT50` is rejected.

**FD audit (P1 surface).** Every REST call opens one HTTP connection under `with` (response read then
closed); the `HTTPError` error-body path explicitly `.close()`s the error response before raising or
retrying. No thread/lock/DB/subprocess introduced; `InstrumentManager` holds no long-lived descriptor
after `resolve()`. Clean.

**Deferred.** Live §3.2.5 depth probe + §9 `actual < requested` WARNING → P3; DSM/true-ATM → P3.

## 2026-07-03 — P0: Scaffolding, config, utils, registry skeleton

**What / why.** Stood up the package skeleton so every later phase has a validated config, shared
primitives, and a declarative metric registry to build against. No live feed, threads, or I/O pipeline
yet — those begin at P1.

**Folder rename (P0-A).** `MarketDepth_Recorder/` → `market_depth_recorder/` (the folder *is* the
package, §2.1). The directory-level `git mv` failed (a stale process holds the old dir's handle), so
the three docs were moved **per-file** with `git mv` instead — content and working-tree doc-sync edits
preserved. The now-empty, untracked `MarketDepth_Recorder/` remnant is harmless (git ignores empty
dirs); delete once the holding process closes.

**Added files.**
- `__init__.py` — `__version__ = "0.1.0"`, `SCHEMA_VERSION = 1` (stamped into raw HEADER §3.5.4 and
  `recorder_meta` §4.1b).
- `config.yaml` — §7.1 template materialized verbatim, `transport: "raw"` default, NIFTY+SENSEX.
- `config.py` — YAML load + **all** §7.3 rules (collect-all-errors, fast-fail `ConfigError` → exit 1),
  `compute_config_hash` (sha256 of metrics+regime+underlyings, §3.5.4/§4.1b), frozen typed `Config`
  with typed `Underlying` entries.
- `utils.py` — logging setup (idempotent, single handler, thread name), IST/time helpers
  (`parse_ist_hhmm`, `now_ist`, `to_epoch_seconds`), decay-weight factory (`w_i = exp(-k·(i-1))`,
  §3.4.2 M8), atomic file write, disk-free helper (§3.1.5).
- `metrics/registry.py` — declarative `MetricSpec` + `register`/`resolve`/`known_names`/`GROUPS`;
  **full M1–M29 + §3.4.3 rolling-window + §3.4.4 aggregate/regime metadata**, no function bodies
  (deferred P4/P7). `live_metrics` validation resolves against the complete set from day one.
- `__main__.py` — §8.2 CLI surface; `--validate-config` wired end-to-end (0/1 exit), other subcommands
  parsed + stubbed with clean exits, arg-dependency guards (`--output` needs `--replay`; `--from/--to`
  parse as IST `HH:MM`).
- `requirements.txt` — standalone pins: `openalgo==2.0.2` exact (load-bearing), `numpy/duckdb/PyYAML/
  websocket-client/pytest` compatible-release `~=` against installed versions.
- `.gitignore` — runtime artifacts (`data/**`, `*.jsonl.gz`, `*.db*`, `*.duckdb`, `*.log`, venv, caches).
- `Documents/` — `ARCHITECTURE.md`, this `CHANGELOG.md`, `SETUP.md`, `config.md`, `utils.md`, `registry.md`.
- `tests/` — `conftest.py` (good-config fixture + writer), `test_config.py` (happy path, one negative
  per §7.3 rule, `--validate-config` exit codes, `config_hash` determinism, `live_metrics` membership),
  `test_utils.py` (decay values, IST parse, atomic round-trip, disk free).

**Verification.** `--validate-config` on the shipped config exits 0; **48 tests pass**, no live feed.
Arg guards return exit 2 on misuse; stubs exit 0.

**FD audit (P0 surface).** `config.py` write-probe closes its `mkstemp` fd and unlinks the temp on all
paths; `utils.atomic_write` adopts the raw fd into a file object (closing the bare fd if adoption
fails) and cleans the temp on error; logging adds a single guarded `StreamHandler` (no stacking). No
sockets/DB/subprocess/threads exist yet. Clean.

**Deferred.** Metric function bodies (P4/P7); `recorder_meta`/HEADER stamping (P2/P5/P7); `--preflight`
(P1), `--status` (P6), `--replay`/`--catchup`/`--verify` (P7). Empty `MarketDepth_Recorder/` dir removal
(pending stale handle release).
