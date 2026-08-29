# MOVED — see the Market Depth Recorder plan in `plans/`

This file is a **pointer stub**. It holds no plan content and must not be edited or used as a
reference.

**The authoritative plan document is:**

```
market_depth_recorder/plans/Plan_001_market_depth_recorder_implementation.md
```

Absolute path on this machine:

```
C:\Users\admin\Downloads\ai tools\openalgo_platform\openalgo\strategies\SS_Projects\market_depth_recorder\plans\Plan_001_market_depth_recorder_implementation.md
```

Stubbed 2026-08-25 at the user's instruction, matching what was already done to
`~/.claude/plans/refer-market-depth-recorder-design-md-an-peppy-dolphin.md`. The plan lives with the
code it plans, is version controlled alongside it, and is the **single authoritative** source for
phase progress, locked decisions, and subtask checklists.

**Why this copy was dangerous, not merely redundant.** It was a 1,556-line snapshot of the plan taken
before P10-F. It contained **zero** `SUPERSEDED` markers and asserted the **disproven** FYERS TBT model
as live fact — "5 symbols per channel across channels 1-50, ceiling 5x50 = 250" — which the official
FYERS TBT docs, a single-connection probe, a multi-connection probe, and a re-read of two live raws all
refute. The real ceiling is **`tbt_budget = 15`** (3 connections x 5 Market-Depth symbols per
*connection*; channels are a pause/resume grouping carrying no capacity). A reader who found this copy
first would have designed against a ceiling that is roughly 16x too large.

For the corrected model see:

- `plans/Plan_001_market_depth_recorder_implementation.md` — P10 heading banner and the P10-A / P10-E
  `SUPERSEDED (P10-F)` markers
- `Documents/evidence/fyers_tbt_concurrency_20260714/tbt_concurrency_reconciliation_20260714.md` — canonical evidence
- `Documents/evidence/openalgo_platform/OPENALGO_PATCH.md` section 8 — the authoritative correction
- `market_depth_recorder_design.md` — the depth-level reality note (source of truth)

Do not restore content here. Do not create a second copy. One plan, one location.
