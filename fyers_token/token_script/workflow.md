# Fyers Token Update — Workflow

A phone-friendly web tool that refreshes the **Fyers** access token used by
**OpenAlgo**, without touching a desktop. It runs a small Flask server on port
**5050**, reached from a phone over Tailscale, and writes the new (encrypted)
token straight into OpenAlgo's database.

This document explains the token model, the three ways to refresh, the exact
step-by-step flows, the one login gotcha that trips people up, and how to
recover when something fails.

---

## 1. Why this tool exists

Fyers API v3 auth is **browser-based**: getting an access token requires a login
page with TOTP + PIN, protected by a Cloudflare bot-check. That is awkward to do
on the trading server itself. This tool moves the whole flow to your phone:

- The server generates the TOTP and the Fyers login URL.
- You log in on the phone, copy the redirect URL back into the page.
- The server exchanges it for an access token and writes it to OpenAlgo's DB,
  encrypted, verified, ready to use.

It also keeps a **refresh token** so that, for ~15 days, the token can be renewed
with a single tap and **no browser at all**.

---

## 2. File map

| File | Role |
| --- | --- |
| `web_server.py` | The Flask app (port 5050). Serves the UI, runs the flows, manages the OpenAlgo daemon. |
| `templates/index.html` | The single-page UI (mobile-first, served to the phone). |
| `update_fyers_token.py` | The worker that writes an access token into OpenAlgo's DB (encrypt, verify, round-trip decrypt). Modes: default (browser), `--manual`, `--headless`, `--show-current`, `--dry-run`. |
| `run_token_update.py` | The headless runner. Calls the Fyers refresh-token API, then invokes `update_fyers_token.py --headless`. Intended for cron. |
| `.env` | All secrets and config (gitignored — never committed). |
| `logs/fyers_token_update.log` | Authoritative record of every token write. |
| `logs/openalgo_pid.log`, `logs/openalgo_process.json` | OpenAlgo daemon tracking. |

Ports: **5050** = this tool, **5000** = OpenAlgo, **8765** = OpenAlgo WebSocket
proxy, **5555** = OpenAlgo ZeroMQ bus.

---

## 3. The token model (read this first)

Two different tokens, two different lifetimes. Confusing them is the source of
most trouble.

| Token | Lives in | Lifetime | How to renew |
| --- | --- | --- | --- |
| **Access token** | OpenAlgo DB (`auth` table, Fernet-encrypted) | Expires **daily ~3:00 AM IST** | Any of the three modes below |
| **Refresh token** | `.env` → `FYERS_REFRESH_TOKEN` (a JWT) | **~15 days** | Only a fresh **browser (Authcode) login** mints a new one |

Key consequences:

- The **access token** is what OpenAlgo actually trades with. It dies every day
  at ~3 AM, so it must be refreshed each trading day.
- The **refresh token** is the shortcut: while it is valid, Auto mode renews the
  access token with no browser. But once it lapses (~15 days), the **only** way
  back is a full browser login — which mints a new refresh token and resets the
  15-day clock.
- The tool decodes the refresh token's `exp` claim and shows a banner at the top
  of the page (green / amber / red) so it never lapses unnoticed.

---

## 4. Where the token is stored

`update_fyers_token.py` writes to OpenAlgo's main database:

```
openalgo/db/openalgo.db  ->  table: auth  ->  row: name='<user>', broker='fyers'
```

- The token is **Fernet-encrypted** before storage. The key is derived by PBKDF2
  from `API_KEY_PEPPER` + a fixed salt — the same scheme OpenAlgo uses, so the
  value written here is readable by OpenAlgo.
- The write is verified two ways in the log: a row check (`Verification passed`)
  and a `Round-trip decrypt OK` that proves OpenAlgo can decrypt it.
- `openalgo/db/openalgo.db` is **gitignored** — the token never enters version
  control.
- After a successful write the worker drops a **cache sentinel** and logs
  `Restart OpenAlgo for the new token to take effect`.

---

## 5. The three update modes

The UI exposes three ways to get a fresh access token:

1. **Authcode (browser)** — full Fyers login on the phone. Needed when the
   refresh token has expired or when you have none. Mints a new refresh token.
   - Endpoints: `GET /api/authcode/start`, `POST /api/authcode/complete`.
2. **Auto (refresh token, browser-free)** — uses the stored refresh token +
   PIN to mint a new access token via `validate-refresh-token`. One tap, no
   Cloudflare page. Works only while the refresh token is valid.
   - Endpoint: `POST /api/update {mode:"auto"}` → `run_token_update.py --headless`.
3. **Manual (paste)** — paste a raw access token you obtained elsewhere.
   - Endpoint: `POST /api/update {mode:"manual", token:"..."}`.

Decision rule:

```
Refresh-token banner is GREEN  ->  use Auto (one tap, no browser)
Banner is AMBER/RED or missing ->  use Authcode (browser login; also refreshes the refresh token)
Have a token from elsewhere    ->  use Manual
```

---

## 6. Primary workflow — Authcode (browser login)

Use this when the refresh token is expired/near-expiry, or after a long gap.

1. **Open the tool** on the phone: `http://<tailscale-ip>:5050`.
2. Tap **Get Authcode**. The server generates a **TOTP** (30-second window) and a
   Fyers login URL, and moves to Step 2.
3. Open the Fyers login. Two options:
   - Tap **Open Fyers Login** (opens a new tab), or
   - Tap **Copy login URL** and paste it into a different browser.
     Use this when the login page comes up blank — see the gotcha in section 7.
4. On the Fyers page: enter your **Client ID**, the **TOTP** shown on the tool,
   and your **PIN**; authorize.
5. Fyers redirects to `http://127.0.0.1:5000/fyers/callback?...&auth_code=...`.
   That page will **fail to load** ("site can't be reached") — this is expected,
   because `127.0.0.1:5000` on the phone is nothing. **Copy the full URL** from
   the address bar anyway.
6. Back on the tool, **paste that URL** into the "Paste Redirect URL here" box and
   tap **Complete Update**.
7. The server extracts `auth_code`, exchanges it for an access token
   (`validate-authcode`), saves the **new refresh token** to `.env`, then runs
   `update_fyers_token.py --headless` to write the access token to the DB. Live
   logs stream in via SSE.
8. Watch for `Token updated successfully` in the streamed log.
9. **Restart OpenAlgo** (section 9) so it loads the new token.

Timing note: the TOTP expires in 30 s. Have the tool open when you enter it, or
just tap **Get Authcode** again for a fresh one.

---

## 7. The one gotcha: blank / spinning Fyers login page

The Fyers `generate-authcode` page is a JavaScript app whose login form only
renders **after a Cloudflare "verify you are human" (Turnstile) check passes**.
That check is **IP-reputation based**, and it silently fails — leaving a blank
page or an endless spinner — when the browser's outbound IP looks non-residential:

- a **Tailscale exit node**, a **VPN**, or a flagged **office/datacenter network**;
- it can fail identically on multiple machines if they share that same network / IP.

It is **not** a bug in this tool, your `.env`, or the `redirect_uri`. The URL,
client ID, and redirect are all correct — the bot-check is the blocker.

**Fix, in order of effectiveness:**

1. **Open the copied login URL on your phone using mobile data (not Wi-Fi).** A
   different, residential IP + a clean mobile browser is the highest-odds fix.
   This is exactly what the **Copy login URL** button is for.
2. Use an **Incognito/Private window with extensions disabled**, allow
   third-party cookies, and try a **different browser** (Edge/Firefox vs Chrome).
3. If every option spins, open DevTools (F12) -> Network, reload, and look for a
   **red/failed** or stuck **pending** request to `challenges.cloudflare.com` or
   `login.fyers.in`. Transient Fyers/Cloudflare issues also happen — retry later.

---

## 8. Auto (refresh-token) workflow — browser-free

While the refresh-token banner is **green**:

- **From the UI:** tap the **Auto** option (calls `POST /api/update {mode:"auto"}`).
- **From the CLI / cron:** `python run_token_update.py --headless`.

What happens: `run_token_update.py` calls Fyers `validate-refresh-token` with
`appIdHash` (sha256 of `client_id:secret_key`), the stored `FYERS_REFRESH_TOKEN`,
and `FYERS_PIN`. On success it receives a fresh access token (and a rotated
refresh token, which it writes back to `.env`), then runs
`update_fyers_token.py --headless` to persist the access token to the DB.

Requires all of: `FYERS_CLIENT_ID`, `FYERS_SECRET_KEY`, `FYERS_REFRESH_TOKEN`,
`FYERS_PIN`. If the refresh token is expired, this fails cleanly — fall back to
the Authcode flow.

Suggested cron (weekdays, before market open):

```
55 8 * * 1-5  cd /path/to/token_script && python run_token_update.py --headless
```

---

## 9. After updating: restart OpenAlgo

A new access token in the DB does **not** reach a running OpenAlgo automatically;
the worker log says as much (`Restart OpenAlgo for the new token to take effect`).

From this tool:

- `POST /api/openalgo/stop` then `POST /api/openalgo/start`, or the equivalent
  buttons in the OpenAlgo panel of the UI.

Until OpenAlgo is restarted it keeps serving the **old** token from memory.

---

## 10. The refresh-token expiry banner

The status panel polls `GET /api/status` (~every 30 s); the response includes a
`refresh_token` object produced by `_refresh_token_status()` in `web_server.py`,
which decodes the JWT `exp` (signature not verified — timestamps only):

| State | Condition | Banner |
| --- | --- | --- |
| `valid` | more than 3 days left | green — "valid, N days left, works until DATE" |
| `expiring` | 3 days or fewer left | amber — "expires in N days, re-login soon" |
| `expired` | past expiry | red — "expired, browser login required" |
| `missing` / `unknown` | no token / not a JWT | grey |

The 3-day threshold is the constant `REFRESH_TOKEN_WARN_DAYS` in `web_server.py`.
When it turns amber or red, do an Authcode (browser) login to mint a fresh
refresh token and reset the 15-day clock.

---

## 11. Troubleshooting

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Fyers login page blank / spinning | Cloudflare Turnstile failing on VPN/Tailscale/office IP | Open the copied URL on phone mobile data (section 7) |
| Banner red "refresh token expired" | >15 days since last browser login | Do the Authcode flow (section 6) |
| Auto mode fails | Refresh token expired, or missing `FYERS_PIN`/keys | Check `.env`; if expired, use Authcode |
| "auth_code not found in URL" on Complete | Pasted the wrong URL | Paste the full redirect URL that contains `auth_code=` |
| Token written but OpenAlgo still rejects | OpenAlgo not restarted | Restart OpenAlgo (section 9) |
| `/api/status` returns 500 | Server bug in the status path | Check the server console traceback; `_refresh_token_status()` and `_pid_log_from_meta()` are hardened not to raise |
| TOTP rejected | Clock skew, or code expired mid-entry | Tap Get Authcode again; verify the server clock |

The `logs/fyers_token_update.log` tail is the authoritative record of the last
write — look for `Token updated successfully`, `Verification passed`, and
`Round-trip decrypt OK`.

---

## 12. Security notes

- `.env` holds the client secret, TOTP key, PIN, and refresh token. It is
  **gitignored** and must never be committed or shared.
- The access token in the DB is **encrypted at rest** (Fernet).
- The tool is exposed only over **Tailscale**, not the public internet.
- The refresh token is a bearer credential valid for ~15 days — treat the `.env`
  file accordingly.
