# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\docs\api\whatsapp-services



---

# FILE: docs\api\whatsapp-services\notify.md

```md
# WhatsApp Notify

Send a WhatsApp message — text, image, document, or any combination — to
yourself, a single recipient, or a small group (up to 5). This is the single
trader-facing send endpoint; everything you might do with `wa.send()` in a
script is exposed here.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/whatsapp/notify
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/whatsapp/notify
Custom Domain:  POST https://<your-custom-domain>/api/v1/whatsapp/notify
```

## Sample API Requests

### Send to yourself (paired device's own number)

```json
{
  "apikey": "<your_app_apikey>",
  "self": true,
  "message": "Build #482 finished in 1m 23s"
}
```

### Send to a single phone number

```json
{
  "apikey": "<your_app_apikey>",
  "phone": "919876543210",
  "message": "Order placed: BUY RELIANCE x 10 @ MARKET"
}
```

### Send to a linked OpenAlgo user

```json
{
  "apikey": "<your_app_apikey>",
  "username": "rajan",
  "message": "Daily summary attached",
  "document_path": "/srv/reports/2026-05-17.pdf",
  "filename": "summary.pdf"
}
```

### Small broadcast (max 5 recipients)

```json
{
  "apikey": "<your_app_apikey>",
  "phones": ["919876543210", "919812345678", "919900112233"],
  "image_path": "/srv/charts/nifty.png",
  "caption": "NIFTY EOD chart"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/whatsapp/notify \
  -H 'Content-Type: application/json' \
  -d '{
    "apikey": "<your_app_apikey>",
    "self": true,
    "message": "Alert from OpenAlgo"
  }'
```

## Sample API Response

### Fire-and-forget (default)

```json
{
  "status": "success",
  "message": "Queued for 1 recipient(s)",
  "queued": 1
}
```

### `wait_for_delivery: true`

```json
{
  "status": "success",
  "message": "Delivered to 2, failed 0",
  "data": {
    "sent":    ["919876543210@s.whatsapp.net", "919812345678@s.whatsapp.net"],
    "failed":  [],
    "skipped": 0
  }
}
```

## Request Body

| Parameter | Type | Description |
|-----------|------|-------------|
| `apikey` | string | OpenAlgo API key. **Mandatory.** |
| `self` | boolean | If `true`, send to the paired device's own number. |
| `username` | string | OpenAlgo username — resolves through the linked-users table. |
| `phone` | string | Single E.164 digit string (e.g. `919876543210`). |
| `phones` | array of strings | Up to 5 E.164 digit strings (small broadcast). Anything beyond 5 is dropped. |
| `message` | string | Text body. Optional if `image_path` or `document_path` is set. Max 4096 chars. |
| `image_path` | string | Server-local path to an image file. |
| `document_path` | string | Server-local path to a document file (PDF, CSV, etc.). |
| `caption` | string | Caption attached to the image. For documents, sent as a follow-up text. |
| `filename` | string | Override the document's display name on the recipient's device. |
| `wait_for_delivery` | boolean | Default `false`. When `true`, block until wars returns and include per-recipient delivery report. |

Exactly one recipient form is required: `self`, `username`, `phone`, or
`phones`. Combining is not supported.

## Response Fields (async)

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `success` or `error` |
| `message` | string | Human-readable summary |
| `queued` | int | Number of recipients dispatched to the alert pool |

## Response Fields (`wait_for_delivery: true`)

`data` contains the per-recipient report from `send_sync`:

| Field | Type | Description |
|-------|------|-------------|
| `sent` | array | JIDs that wars confirmed accepted |
| `failed` | array | `[{ "to": "<jid>", "error": "<msg>" }, ...]` |
| `skipped` | int | Recipients trimmed by the 5-recipient cap |

## Notes

- The bot must be paired and connected for `notify` to deliver. Connect /
  disconnect lives on the `/whatsapp` admin web UI; this REST namespace
  intentionally does not expose those controls. If the bot is paused, the
  message is queued in `whatsapp_notification_queue` for a later retry.
- Image / document paths are read from the OpenAlgo server's filesystem,
  not uploaded by the API call. Place files in a server-readable location
  first.
- **Attachment path allowlist.** For security, only paths inside the
  directories listed in the `WHATSAPP_ATTACHMENT_ROOTS` env var are
  accepted. The default (when unset) is `<openalgo>/db/attachments/` only.
  Anything outside the allowlist returns `400 image_path is not allowed`.
  Set `WHATSAPP_ATTACHMENT_ROOTS` to a comma-separated list of absolute
  directories to expand it. Paths containing `..`, paths under sensitive
  system trees (`/etc`, `/proc`, `/sys`, `/root`, `/var/log`, `C:\Windows`,
  `C:\Users\Default`), and symlinks that resolve outside the allowlist are
  always rejected.
- The 5-recipient cap is a ToS-safety guardrail — bulk-messaging patterns
  can get the paired device unlinked by Meta. Use the official WhatsApp
  Business API for genuine mass-messaging use cases.

```


---

# FILE: docs\api\whatsapp-services\README.md

```md
# WhatsApp Services

WhatsApp delivery via the unofficial multi-device protocol, powered by the
[`wars`](https://pypi.org/project/wars/) library (Rust core via PyO3).

OpenAlgo runs one paired WhatsApp Web session per install. Once paired
from the `/whatsapp` admin page, the bot stays connected in the same
Flask process that serves orders, so notifications fire from the same
event bus that drives Telegram alerts. Linked users can also run slash
commands against the bot (`/orderbook`, `/positions`, `/quote`, etc.)
once they send `/link <api_key>` from their phone.

## Security model — minimal REST surface

The REST API at `/api/v1/whatsapp/` exposes **exactly one** endpoint:
`POST /notify` (send a message). Everything else — pairing, unpairing,
starting / stopping the bot, reading or mutating config, listing linked
recipients, broadcasting to all of them, viewing stats, editing
preferences — is **admin-only** and lives behind the Flask session cookie
at `/whatsapp/...` (consumed by the React `/whatsapp` admin page).

Why this stance:

- The paired-device session blob is functionally a credential to the
  operator's WhatsApp account. A leaked API key must never be enough to
  re-pair the bot or wipe an existing session.
- A leaked API key must never let an attacker enumerate the operator's
  linked contact list, change rate limits, or fan out to every linked
  user via `/broadcast`.
- The paired session blob (~300 KB of Signal Protocol private keys) is
  encrypted at rest with a Fernet key derived from
  `API_KEY_PEPPER + FERNET_SALT + ":whatsapp-session"`. Anyone with the
  `openalgo.db` file **and** the `.env` secrets can impersonate the
  device — keep both secret.

## REST endpoint

| Endpoint | Method | Description |
|----------|--------|-------------|
| [Notify](./notify.md) | POST | Send text / image / document to self, one user, or up to 5 recipients. |

That is the entire public surface.

## Admin operations (web UI only)

Performed on the logged-in `/whatsapp` page. Not exposed via API key:

- **Pair** a new device (QR or pair-code).
- **Unlink** the paired device (wipes the encrypted session blob).
- **Start / Stop** the bot's WhatsApp connection.
- **Config**: toggle broadcast, adjust rate limits, message length cap.
- **Users**: list and revoke linked recipients.
- **Broadcast**: send to every linked user matching filters.
- **Stats**: command usage analytics.
- **Preferences**: per-user notification toggles.

These are all routed through `blueprints/whatsapp.py` with
`@check_session_validity`, so only the logged-in OpenAlgo admin can
invoke them.

## Quick example: trade alert to yourself

```bash
curl -X POST http://127.0.0.1:5000/api/v1/whatsapp/notify \
  -H 'Content-Type: application/json' \
  -d '{
    "apikey": "<your_app_apikey>",
    "self": true,
    "message": "Build #482 deployed. P&L: +1.2%"
  }'
```

## Quick example: chart to client + yourself

```bash
curl -X POST http://127.0.0.1:5000/api/v1/whatsapp/notify \
  -H 'Content-Type: application/json' \
  -d '{
    "apikey": "<your_app_apikey>",
    "phones": ["919876543210", "919812345678"],
    "image_path": "/srv/charts/nifty_eod.png",
    "caption": "NIFTY end-of-day chart"
  }'
```

Up to 5 recipients per call — anything beyond that is dropped. This is a
ToS-safety guardrail; bulk-messaging patterns can get the paired device
unlinked by Meta.

## Receiving messages (bot commands)

Once paired, any WhatsApp user can message the bot and run queries:

```
/link <YOUR_API_KEY>        # one-time, links this WhatsApp number to your OpenAlgo user
/orderbook                  # today's orders
/positions                  # open positions
/funds                      # available cash
/pnl                        # net P&L
/quote RELIANCE NSE         # last traded price
/closeall                   # square off all positions
/help                       # full command list
```

Each command runs against the OpenAlgo SDK using the linked user's API
key, so results are identical to what you would get from the REST API.

## Event-driven order alerts

When you place an order via `/api/v1/placeorder` (or any of the other
order endpoints), the order service publishes an `order.placed` event to
the in-process event bus. The WhatsApp subscriber listens on every order
topic — `order.placed`, `order.modified`, `order.cancelled`,
`orders.all_cancelled`, `position.closed`, `basket.completed`,
`split.completed`, `options.completed`, `multiorder.completed` — and
sends the linked user a formatted alert automatically. No explicit
`/notify` call needed.

The Telegram subscriber sits on the same topics, so both channels fire
in parallel from a single order placement.

## Rate limits

| Endpoint | Limit |
|----------|-------|
| `/notify` | 30 / minute |
| Bot commands (inbound) | 10 / second per linked user |

```
