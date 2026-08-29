# Runbook — running the F7B live depth-transition probe

**Prepared:** 2026-08-26 · **Executed:** 2026-08-26 09:34-09:52 IST — see
[`depth_transition_probe_20260826.md`](depth_transition_probe_20260826.md) for the results ·
**For:** the operator, at market open · **Tool:**
`tools/fyers/depth_transition_probe.py` · **Fills in:**
[`depth_transition_probe_20260826.md`](depth_transition_probe_20260826.md)

> **DO NOT RUN THE LIVE PROBE BEFORE MARKET DATA IS AVAILABLE.** Outside the 09:15-15:30 IST
> session no depth packets flow, so every case would come back UNKNOWN — a wasted broker session
> that proves nothing. The tool refuses `--live` outside the session for this reason.

No credentials appear in this runbook. The API key is read from the `OPENALGO_API_KEY` environment
variable and is never passed on the command line (it would land in shell history) and never written
to an evidence file.

---

## Before you start

- Run **once**, on a normal trading day, on a **liquid, non-expiring-today** NFO contract.
- Prefer a day when the recorder is **not** running: it holds premium slots, and a probe competing
  for them will read as a capacity failure that is really just contention.
- Budget about 10 minutes. Seven cases, one bounded observation window each.

## Steps

**1. Start OpenAlgo.** Bring the platform up the usual way and let it settle.

**2. Log in to FYERS afresh.** Broker tokens expire daily around 03:00 IST, so a session from
yesterday is dead even if the row still exists. Complete the interactive OAuth login in the browser.

**3. Confirm the session is current.** In the OpenAlgo UI, check that the broker shows as connected
and that the login timestamp is from **today, after 03:00 IST**.

**4. Confirm the feed token is populated.** A broker session can exist with no market-data token; a
missing feed token gives clean subscribe acknowledgements and zero packets, which is the single most
misleading failure mode for this probe. Verify the platform reports the market feed as available.

**5. Confirm the proxy is listening.** The WebSocket proxy must be accepting connections on port
8765 (and the app on 5000, ZeroMQ on 5555):

```
netstat -ano | findstr "8765"
```

**6. Confirm the probe environment.** From `SS_Projects/market_depth_recorder`:

```
python tools/fyers/depth_transition_probe.py --help
```

Set the API key in the environment for this shell only — never inline in the command:

```
$env:OPENALGO_API_KEY = "<your OpenAlgo API key>"      # PowerShell
export OPENALGO_API_KEY="<your OpenAlgo API key>"       # bash
```

**7. Choose one or two NFO instruments.** A near-ATM NIFTY weekly option leg with real two-sided
liquidity. **NFO only** — 50-level TBT is NSE/NFO-restricted, so a SENSEX/BFO leg cannot answer the
question. Do not reuse a symbol from an older document: expiries roll. Two instruments is the
maximum the tool accepts.

**8. Dry-run first.** This sends nothing and touches no network. It prints the exact frame sequence
so you can confirm the plan before any broker interaction:

```
python tools/fyers/depth_transition_probe.py \
    --symbols NIFTY<EXPIRY><STRIKE>CE \
    --out Documents/evidence/depth_transition_dryrun_<YYYYMMDD>.json
```

Read the printed sequence. Every frame should be a `subscribe` or `unsubscribe` on your chosen
symbol. If anything else appears, stop.

**9. Verify the baseline at 5 levels before transitioning anything.** Run the control case alone
first. If this does not deliver market data, the rest of the run is meaningless — fix the feed and
start again:

```
python tools/fyers/depth_transition_probe.py --live \
    --symbols NIFTY<EXPIRY><STRIKE>CE --cases C1_5_5_logical \
    --out Documents/evidence/depth_transition_baseline_<YYYYMMDD>.json
```

Confirm the printed result shows a non-zero observed depth. A `success` status with no observed
depth means **no data arrived** — go back to steps 4 and 5.

**10. Run the minimal live probe.** Only after step 9 shows live data:

```
python tools/fyers/depth_transition_probe.py --live \
    --symbols NIFTY<EXPIRY><STRIKE>CE \
    --out Documents/evidence/depth_transition_probe_<YYYYMMDD>.json
```

Let it finish. Do not re-run it in a loop, do not add instruments, and do not raise the limits to
"get a better sample" — a second opinion on a broker cap is not worth tripping one.

After the cases, and before cleanup, the tool measures the **unsubscribe effect** on whichever leg
is still delivering (the `:50` leg by preference): observe, unsubscribe, observe, **re-subscribe**,
observe. The re-subscribe is a control, not an extra subscription — cleanup releases it moments
later — and it is what separates "the leg stopped" from "the market went quiet". Expect two extra
frames on one instrument and a result whose notes carry `packets_before=`,
`packets_after_unsubscribe=`, `packets_after_resubscribe=` and `effect_observed=`. If
`effect_observed=unknown`, that is the honest answer and not a reason to re-run.

**11. Capture the evidence.** Transcribe the JSON into
[`depth_transition_probe_20260826.md`](depth_transition_probe_20260826.md), section by section,
keeping the confidence each result carries:

- **OBSERVED** — levels counted in delivered market-data packets.
- **INFERRED** — from an acknowledgement only.
- **UNKNOWN** — not established.

Never promote one to the next. `actual_depth: 50` in an acknowledgement is INFERRED, not confirmed
50-level data. A case that did not run stays UNKNOWN; it does not become "no". Keep the JSON
alongside the document as the primary record.

**12. Verify cleanup and stop.** The tool unsubscribes every symbol it subscribed — including
the leg the unsubscribe-effect control re-subscribed in step 10 — and closes its connection before
exiting. Confirm the platform shows no leftover subscriptions from the probe, and
that no probe process is still running. Then unset the API key from your shell:

```
Remove-Item Env:OPENALGO_API_KEY      # PowerShell
unset OPENALGO_API_KEY                 # bash
```

---

## If something goes wrong

| Symptom | What it means | What to do |
| --- | --- | --- |
| `cannot reach the OpenAlgo proxy` | Nothing listening on 8765 | Go back to step 5 |
| `--live needs OPENALGO_API_KEY` | Key not in this shell's environment | Step 6 |
| `outside the 09:15-15:30 IST session` | Ran too early or too late | Wait for the session |
| Acks succeed, observed depth is always `None` | No market data arriving — usually a missing feed token | Steps 4 and 5; do **not** record the acks as results |
| A case reports UNKNOWN | That case is unanswered | Record it as UNKNOWN; do not infer an answer |

## What must not happen

- Do not fabricate or interpolate any cell of the evidence document.
- Do not run with more than two instruments, or remove the safety limits.
- Do not deliberately exceed the broker's premium capacity to find the ceiling.
- Do not leave the probe running in the background.
- Do not put an API key, token, or any secret into a command line, an evidence file, or this
  document.
- Do not close F7, write the Broker Adapter, or start F8 until the evidence document's observed-facts
  section contains real observations.
