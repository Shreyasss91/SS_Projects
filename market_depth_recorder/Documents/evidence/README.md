# Evidence

Durable findings about the world outside this codebase: what the broker actually does, and what was
changed in the OpenAlgo platform to work with it. These outlive the plan that produced them and are
cited from source, from the design spec, and from `CLAUDE.md`.

**This folder is not plan narrative.** A record of how one phase of one plan went belongs with its
plan, in `plans/Plan_00N_evidence/`. The test is lifetime: if a later plan would still cite it, it
belongs here.

One folder per experiment. Each holds the human-written finding plus the machine-generated captures
it rests on, so a capture is never separated from the run that produced it.

## `fyers_tbt_concurrency_20260714/`

**Establishes the FYERS TBT capacity limits. FROZEN — do not revisit without new external evidence.**

| File | What it is |
| --- | --- |
| `tbt_concurrency_reconciliation_20260714.md` | **Canonical.** Reconciles the contradictory Jul-07 and Jul-14 readings by re-analysing the Tier 0 raw logs at per-second instantaneous granularity |
| `tbt_probe_20260714.json` | Single-connection probe capture |
| `tbt_multiconn_20260714.json` | Multi-connection probe capture |

The reconciliation is the most-cited document in the project: `CLAUDE.md`, the design spec's frozen
protocol block, `PROJECT_NOTES.md`, `market_depth_framework/capabilities.py`, `capability_layer.py`,
`config.example.yaml`, `eod_report.py`, and two test modules all depend on it. Read it before
changing anything that touches TBT capacity.

Probes: `tools/fyers/tbt_channel_probe.py`, `tools/fyers/tbt_multiconn_probe.py`.

## `depth_transition_20260826/`

**Establishes 5 <-> 50 depth-transition behaviour on the OpenAlgo/FYERS path**, from a live NSE
session on 2026-08-26 (09:34-09:52 IST).

| File | What it is |
| --- | --- |
| `depth_transition_probe_20260826.md` | The 20-section evidence document, filled in from the live run |
| `depth_transition_probe_runbook_20260826.md` | Operator procedure for reproducing it |
| `depth_transition_baseline_20260826.json` | Baseline capture |
| `depth_transition_C2_caseA_20260826.json`, `C3_caseB`, `C4`, `C5` | Per-case captures |
| `depth_transition_unsub_20260826.json` | Unsubscribe-behaviour capture |

Fields are marked `OBSERVED` only where the run measured them. Reconnect and premium-capacity
behaviour were **not** measured and remain `UNKNOWN` — which is not "no". Do not fill an open cell
from a code reading.

Probe: `tools/fyers/depth_transition_probe.py`.

## `openalgo_platform/`

Changes and defects in the OpenAlgo platform itself, kept separate from the protocol findings above
so a platform issue never contaminates the broker characterization.

| File | What it is |
| --- | --- |
| `OPENALGO_PATCH.md` | The FYERS TBT channel-spread patch. **Read §8 first** — the premise it was built on is superseded; the patch is kept because it is harmless and its channel-resume plumbing is correct, but it buys `tbt_budget = 15`, not 250 |
| `openalgo_fyers_tbt_channels.patch` | The reference diff |
| `openalgo_tbt_reconnect_storm_issue.md` | A `_run_websocket` retry-on-return storm. Worked around in the probe, **not** patched in OpenAlgo; candidate to upstream |

These live inside the recorder rather than in the sibling `openalgo_docs/` as a deliberate
platform-scope exception, recorded in `PROJECT_NOTES.md`.

## Adding an experiment

Create `Documents/evidence/<topic>_<YYYYMMDD>/`, put the narrative document and its captures in it,
and add a row above. Mark every claim `OBSERVED` / `INFERRED` / `UNKNOWN`, and never promote an
acknowledgement to delivery evidence or an absent failure to proof of correctness.
