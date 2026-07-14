# OpenAlgo issue — FYERS TBT `_run_websocket` retry-on-return storm

**Type:** OpenAlgo platform implementation issue (NOT a FYERS protocol finding — recorded separately so it
does not contaminate the TBT protocol characterization). **Found:** 2026-07-14, while building
`tools/fyers/tbt_multiconn_probe.py`. **Severity:** medium (self-inflicted rate-limit; no data corruption).
**Status:** worked around in the probe; **not** patched in OpenAlgo. Candidate to upstream.

## File
`broker/fyers/streaming/fyers_tbt_websocket.py` — `FyersTbtWebSocket._run_websocket()` (and the
`connect()` wait loop).

## Symptom
When a TBT WebSocket **handshake fails** (e.g. FYERS/Cloudflare returns HTTP `429 Too Many Requests`,
`error code: 1015`, on connecting a 4th connection while 3 are already open), the client **hammers the
handshake endpoint ~10×/second** for the full 15 s `connect()` window — ~150 failed handshakes for a single
logical connect attempt. That burst **self-inflicts** an IP-level Cloudflare rate-limit that then blocks
*legitimate* subsequent connects, confounding any experiment and abusing the broker endpoint.

## Root cause
`_run_websocket()` is a `while self.running:` loop that calls `self.ws.run_forever()` each iteration:

```python
def _run_websocket(self):
    while self.running:
        try:
            self.ws = websocket.WebSocketApp(...)
            self.ws.run_forever(ping_interval=0)     # RETURNS on handshake failure (does not raise)
        except Exception as e:
            self.logger.error(...)
            self.connected = False
            if self.running and self.reconnect_enabled:   # <-- guard only reached on EXCEPTION
                self._handle_reconnect()
            else:
                break
```

A **handshake failure makes `run_forever()` return normally** (it invokes `on_error`/`on_close` and returns —
it does **not** raise). So the `except` branch — the only place the `reconnect_enabled` guard and the
back-off `_handle_reconnect()` live — is **never reached**. Control falls back to `while self.running:`, which
is still `True` (a failed `connect()` never clears `running`), so it **immediately re-enters `run_forever()`**
with **no delay and no reconnect-enabled check**. Hence the tight storm until `connect()`'s 15 s wait elapses
and teardown sets `running = False`.

Net: `reconnect_enabled = False` does **not** actually stop the retry on a *handshake* failure, and
`_handle_reconnect()`'s exponential back-off (5→60 s) does **not** apply to it — both only guard the
*exception* path, not the *return* path.

## Impact
- **Abusive** to FYERS/Cloudflare: ~150 handshakes per failed connect → `429 / 1015` rate-limit that can
  linger for minutes and block healthy reconnects.
- Affects **any** TBT reconnect that fails at the handshake (transient network blip, broker maintenance,
  connection-cap rejection) — not just the probe. In production a flapping TBT feed would storm on every
  failed handshake instead of backing off.

## Probe workaround (in `tools/fyers/tbt_multiconn_probe.py`)
Set `client.running = False` from the `on_error` callback when the client has **not** yet reached a live
connection — this lets `run_forever()` return once and the `while self.running:` loop exit after a **single**
failed handshake (~1–3 frames instead of ~150). This is a diagnostics-only shim; it does not change platform
behavior.

## Suggested upstream fix (for OpenAlgo, if pursued)
In `_run_websocket()`, after `run_forever()` **returns**, apply the same guard the exception path uses —
e.g.:

```python
self.ws.run_forever(ping_interval=0)
self.connected = False
if not (self.running and self.reconnect_enabled):
    break
self._handle_reconnect()     # honor the 5→60s back-off on the return path too
continue
```

so a returned (handshake-failed) run also respects `reconnect_enabled` and the exponential back-off, instead
of busy-looping. (Verify interaction with the health-check/force-reconnect path before adopting.)

## Related
- `tools/fyers/tbt_multiconn_probe.py` — where the workaround lives and why.
- `Documents/patches/tbt_concurrency_reconciliation_20260714.md` — the protocol reconciliation (separate concern).
