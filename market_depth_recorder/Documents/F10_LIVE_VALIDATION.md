# F10_LIVE_VALIDATION.md — the true-scale live validation runbook (F10B)

F10 closes **Plan_001 D18**: perf and RSS at true scale — up to 15 legs at 50-level plus the hybrid
remainder — have never been measured. P10-E measured `<=5` NFO @50 plus ~120 SENSEX @5, so the number
that matters has never existed.

F10 runs in two stages. **F10A** is preparation and is done offline (this document, the watcher,
the checklist in Plan_002 §22.13). **F10B** is one live market session. This runbook is F10B's
procedure; it is written to be followed under time pressure, so the decisions are already made.

Decisions in force (Plan_002 §22.13): **F22 = A** framework genuinely enabled · **F23 = A** natural
reconnect only · **F24 = A** run at the configured budget, never probe the ceiling · **F25** criteria
below · **F26 = A** dated evidence document at the F7 standard.

---

## A. Preconditions

Everything in `Documents/LIVE_RUN.md` §A still applies — OpenAlgo reachable, FYERS session valid
(tokens expire ~03:00 IST), the OpenAlgo channel-spread patch applied **and OpenAlgo restarted**,
static IP whitelisted, a trading day, disk space. F10B adds:

- [ ] `git status` clean apart from the intended `enabled` flip and the known untracked runtime dirs.
- [ ] `python -m market_depth_recorder --validate-config --config market_depth_recorder/config.yaml`
      exits 0 **with the flag on** — the framework block is validated on every start, so a
      misconfiguration must surface here, not at 09:15.
- [ ] `--preflight` shows `NIFTY/NFO -> 50`, `SENSEX/BFO -> 5`. If NIFTY comes back 5, **stop**: the
      run cannot measure 15 legs @50 and there is nothing to learn about D18 today.
- [ ] The watcher runs against the current config:
      `python market_depth_recorder/tools/validation/f10_live_monitor.py <health.json> -c <config.yaml> --once`
      exits 0 before the session (it reads a stale health file happily; the point is that thresholds
      derive cleanly).
- [ ] The evidence file path for today is chosen: `Documents/patches/f10_live_validation_YYYYMMDD.md`.

## B. Enabling the framework

One line in `config.yaml`:

```yaml
market_depth_framework:
  enabled: true          # F10B only. Back to false at the end of the session.
```

Two properties of that flip, both verified offline in F10A:

- **It does not change `config_hash`.** The framework block is excluded from the hash, so today's raw
  log carries the same `config_hash` as every previous session and the evidence stays comparable.
- **It is tracked.** `config.yaml` is in git, so a flag left on shows up in `git status` /
  `git diff` — the accident the flip is most likely to cause is also the one git makes visible.

## C. Run sequence

1. Start the recorder as usual (`Documents/LIVE_RUN.md` §B) once OpenAlgo is healthy, the FYERS
   session is valid, market data is flowing. **Do not** optimise for 09:15:00; record the actual
   start timestamp instead.
2. Start the watcher in a second terminal:

   ```
   python market_depth_recorder/tools/validation/f10_live_monitor.py \
       <output_dir>/health.json -c market_depth_recorder/config.yaml \
       -o <output_dir>/f10_timeline.jsonl --interval 15
   ```

   It samples, classifies, and appends a timeline. It **observes only** — it opens no socket, imports
   no recorder module, and has no kill path. When it prints `ABORT` the operator acts, per §D.
3. Let the session run. The hybrid should exercise near-ATM premium plus the standard remainder on its
   own. **Do not** manipulate subscriptions to make the measurement more interesting.
4. Spot-check `--status` a few times as usual. The watcher timeline is the record; `--status` is for
   your own eyes.
5. Graceful teardown at `session_end + teardown_grace_min` as normal. Then **flip `enabled` back to
   `false`** and confirm `git diff --stat market_depth_recorder/config.yaml` is empty.
6. Render the evidence skeleton and complete it:

   ```
   python market_depth_recorder/tools/validation/f10_live_monitor.py \
       --render <output_dir>/f10_timeline.jsonl \
       --evidence-out Documents/patches/f10_live_validation_YYYYMMDD.md
   ```

   The skeleton fills OBSERVED from the timeline and leaves INFERRED, the P10-E comparison and the
   D18 conclusion as `FILL IN`, because those are judgements.

## D. Abort criteria (fork F25)

Every numeric threshold below is read from `config.yaml` or is a figure the project already committed
to. Two are host facts and are marked as such — they are not derived from the system, and pretending
otherwise would be the sort of invented number this section exists to avoid.

### Hard — act now

A hard condition must hold for **3 consecutive samples** (45 s at the default cadence) before it is an
abort, except the two marked *instant*, where by the time it repeats the thing it protects is gone.

| Condition | Threshold | Source |
|---|---|---|
| `raw_loss` *(instant)* | `raw_dropped_total > 0` | the lossless-raw invariant (CLAUDE.md) |
| `budget_exceeded` *(instant)* | `premium_legs > effective_budget` | framework invariant |
| `proc_queue_size_critical` | `>= critical_watermark_pct` of `max_queue_size` (45,000) | `config.yaml` |
| `db_queue_size_critical` | `>= 45,000` | `config.yaml` |
| `raw_file_queue_size_critical` | `>= 90,000` (of `raw_file_queue_max`) | `config.yaml` |
| `cycle_ms_hard` | `cycle_ms_p50 >= 500 ms` | half the 1 s budget; P10-E: the real signal is cycle_ms approaching 1000 ms |
| `rss_hard` | `rss_mb >= 2048` | **HOST** — an 8 GB machine |
| `degraded_critical` | `degraded_level >= 2` | PROCESSOR's own critical watermark |
| `plan_failures_growing` | `plan_failures` rising sample over sample | refusal storm / uncontrolled retry |
| `db_drops_growing` | `db_rows_dropped_total` rising | overload past proc shedding |
| `framework_vanished` | the framework block leaves `health.json` while enabled | containment breach |

Plus the two that no tool can see for you: **any framework exception escaping its containment
boundary** (watch the log), and **the operator's own judgement**. The kill switch is always available
and never needs justification in the moment.

### Soft — record, do not act

`cycle_ms_p50 >= 30 ms` (`eod_report._CYCLE_MS_TARGET`) · `rss_mb >= 500` (`_RSS_MB_TARGET`) ·
`degraded_level == 1` · any queue at its warn watermark (70%) · `proc_dropped_total` rising (proc
sheds first — that is the design working) · a single subscription refusal · a reconnect ·
`websocket_status` leaving `connected`.

These go into the timeline with a timestamp and stay there. A soft condition is evidence, not an
emergency.

### The kill switch

**Stopping the framework is not stopping the recorder.** In order:

1. Flip `enabled: false` in `config.yaml`.
2. `Ctrl-C` / `SIGTERM` the recorder → the graceful drain runs, FDs close, an EOF marker is written.
3. Restart it. Mid-day recovery re-seeds ATM from one REST quote per underlying and resubscribes; the
   raw writer reopens **today's** file in append mode (`file_writer.py:122`, `mode="at"`), so the
   audit trail continues in the same file rather than forking.
4. The interior `EOF`/`HEADER` records the restart leaves behind are skipped by both readers
   (`replay.py:176`, `framework_replay.py:189`), so neither the Tier-2 rebuild nor a framework replay
   is harmed by having stopped.

Only kill the process without the flip if the recorder itself — not the framework — is the problem.
The raw path is the thing being protected; everything else is reconstructable from it.

## E. What must not happen

No intentional 16th premium subscription. No forced reconnect. No deliberate broker stress. No
unsubscribe experimentation. No depth experiments. No architecture, allocator, adapter or F7/F8
behaviour change during the run — not even if a live observation looks interesting. If something
unexpected happens: **observe, record, do not improvise**, unless an abort criterion above already
covers it.

## F. What the evidence may and may not say (fork F26)

The document separates **OBSERVED** / **INFERRED** / **UNKNOWN** and must state, in its own words:

- Legs operating at the configured budget of 15 is *observed*. "The broker supports at least 15" is
  **not** established by it — the ceiling was never probed and stays **UNKNOWN**.
- Reconnect depth restoration is **UNKNOWN** unless a reconnect happened naturally *and* premium legs
  were then seen delivering at depth. The absence of a reconnect establishes nothing.
- D18 closes only if the session actually ran the true-scale hybrid. If NIFTY degraded to 5, or the
  session was aborted, D18 stays open and the document says so.

## G. Related

- `Documents/LIVE_RUN.md` — the general live-run runbook this one extends
- `Documents/operator_notes.md` — daily operation, precautions, CLI reference
- `Documents/framework_replay.md` — the offline harness, and why it is not broker evidence
- `Documents/phase_10E_notes.md` — the P10-E baseline the F10 numbers are compared against
- `plans/Plan_002_market_depth_framework_implementation.md` §22.13 — F10 scope, forks F22-F26, checklist
