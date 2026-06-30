# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\docs\userguide



---

# FILE: docs\userguide\README.md

```md
# OpenAlgo User Guide

Welcome to the official OpenAlgo User Guide - your comprehensive resource for mastering algorithmic trading with OpenAlgo.

## What You'll Learn

This guide takes you from zero to automated trading, covering everything from basic concepts to advanced strategy deployment.

## Guide Structure

### Getting Started (Modules 01-05)
- [01 - What is OpenAlgo](./01-what-is-openalgo/README.md)
- [02 - Key Concepts](./02-key-concepts/README.md)
- [03 - System Requirements](./03-system-requirements/README.md)
- [04 - Installation Guide](./04-installation/README.md)
- [05 - First-Time Setup](./05-first-time-setup/README.md)

### Broker & Interface (Modules 06-10)
- [06 - Broker Connection](./06-broker-connection/README.md)
- [07 - Dashboard Overview](./07-dashboard-overview/README.md)
- [08 - Understanding the Interface](./08-understanding-interface/README.md)
- [09 - API Key Management](./09-api-key-management/README.md)
- [10 - Placing Your First Order](./10-placing-first-order/README.md)

### Order Management (Modules 11-15)
- [11 - Order Types Explained](./11-order-types/README.md)
- [12 - Smart Orders](./12-smart-orders/README.md)
- [13 - Basket Orders](./13-basket-orders/README.md)
- [14 - Positions & Holdings](./14-positions-holdings/README.md)
- [15 - Analyzer Mode (Sandbox Testing)](./15-analyzer-mode/README.md)

### Reference
- [Symbol Format Guide](./symbol-format/README.md) - Essential reference for symbol naming conventions

### Platform Integrations (Modules 16-19)
- [16 - TradingView Integration](./16-tradingview-integration/README.md)
- [17 - Amibroker Integration](./17-amibroker-integration/README.md)
- [18 - ChartInk Integration](./18-chartink-integration/README.md)
- [19 - GoCharting Integration](./19-gocharting-integration/README.md)

### Strategy Building (Modules 20-22)
- [20 - Python Strategies](./20-python-strategies/README.md)
- [21 - Flow Visual Builder](./21-flow-visual-builder/README.md)
- [22 - Action Center](./22-action-center/README.md)

### Monitoring & Alerts (Modules 23-26)
- [23 - Telegram Bot](./23-telegram-bot/README.md)
- [24 - PnL Tracker](./24-pnl-tracker/README.md)
- [25 - Latency Monitor](./25-latency-monitor/README.md)
- [26 - Traffic Logs](./26-traffic-logs/README.md)

### Security & Support (Modules 27-30)
- [27 - Security Settings](./27-security-settings/README.md)
- [28 - Two-Factor Authentication](./28-two-factor-auth/README.md)
- [29 - Troubleshooting](./29-troubleshooting/README.md)
- [30 - FAQs](./30-faqs/README.md)

### Analytics Tools (Module 31)
- [31 - Tools (Options & Strategy Analytics Suite)](./31-tools/README.md)

## Quick Navigation

| I want to... | Go to |
|--------------|-------|
| Understand what OpenAlgo does | [Module 01](./01-what-is-openalgo/README.md) |
| Install OpenAlgo | [Module 04](./04-installation/README.md) |
| Connect my broker | [Module 06](./06-broker-connection/README.md) |
| Place my first order | [Module 10](./10-placing-first-order/README.md) |
| Test without real money | [Module 15](./15-analyzer-mode/README.md) |
| Understand symbol formats | [Symbol Format Guide](./symbol-format/README.md) |
| Connect TradingView | [Module 16](./16-tradingview-integration/README.md) |
| Build visual strategies | [Module 21](./21-flow-visual-builder/README.md) |
| Get Telegram alerts | [Module 23](./23-telegram-bot/README.md) |
| Use options analytics tools | [Module 31](./31-tools/README.md) |

## Additional Resources

- **Developer Documentation**: See `/design` folder for technical architecture
- **Official Docs**: [docs.openalgo.in](https://docs.openalgo.in)
- **Community**: [Discord](https://www.openalgo.in/discord)
- **Video Tutorials**: [YouTube](https://www.youtube.com/@openalgo)

## Support

If you encounter issues:
1. Check [Troubleshooting](./29-troubleshooting/README.md)
2. Read [FAQs](./30-faqs/README.md)
3. Ask on [Discord](https://www.openalgo.in/discord)
4. Open a [GitHub Issue](https://github.com/marketcalls/openalgo/issues)

```


---

# FILE: docs\userguide\remote-mcp.md

```md
# Remote MCP

Lets hosted AI clients — ChatGPT, Claude.ai, Claude mobile — talk to your OpenAlgo install over the internet so you can ask them to fetch quotes, summarise positions, or place orders in plain English.

Local stdio MCP (Claude Desktop / Cursor / Windsurf on the same machine as your install) keeps working unchanged. Remote MCP is a parallel, opt-in transport that shares the same 40 tools but reaches them over HTTPS.

| You want to... | Use |
| --- | --- |
| Trade from your laptop using Claude Desktop, Cursor, or Windsurf | **Local stdio** (MCP setup guide) |
| Trade from ChatGPT.com, Claude.ai, or the Claude mobile app | **Remote MCP** (this guide) |
| Both | Enable both — they don't interfere |

***

## What you need

1. **OpenAlgo on your own domain with HTTPS.** Dashboard reachable at `https://yourdomain.com`, login + broker auth + orders all working through the web UI. If you're not there yet, start with one of the install scripts: `install/install.sh`, `install/install-multi.sh`, `install/install-docker.sh`, or `install/install-docker-multi-custom-ssl.sh`.
2. **OpenAlgo 2.0.1.0 or later.** Footer of the dashboard shows the version, or `curl https://yourdomain.com/api/v1/openalgo-version`. On older builds run `install/update.sh` first.
3. **An OpenAlgo API key.** Generate one at **Profile → API Keys**. The MCP server uses it server-side; hosted clients never see it — they get OAuth tokens instead.
4. **A paid AI plan.** ChatGPT Plus / Team / Enterprise, or Claude Pro / Team / Enterprise. Custom MCP servers aren't on the free tiers.

***

## Turn it on

### Native install (`install.sh`)

The installer asks at run time whether to enable Remote MCP. If you said **yes**, it's already on at `https://yourdomain.com/mcp` — skip to *Connecting*.

If you said no and want to flip it now, edit `/var/python/openalgo/.env`:

```ini
MCP_HTTP_ENABLED = 'True'
MCP_PUBLIC_URL = 'https://yourdomain.com'
```

Then `sudo systemctl restart openalgo`.

### Multi-domain native (`install-multi.sh`)

Edit the per-deploy `.env` (typically `/var/python/openalgo-flask/<deploy-name>/.env`) with the same two keys, then `sudo systemctl restart openalgo-<deploy-name>`.

### Docker (`install-docker.sh` / `install-docker-multi-custom-ssl.sh`)

```bash
cd /path/to/openalgo
sudo ./install/enable-remote-mcp-docker.sh
```

The helper picks the stack (or asks if you have several), backs up the bind-mounted `.env`, sets the keys, restarts the container, and probes the OAuth + healthz endpoints. Re-run for each instance.

### Defaults the install applies

| Key | Default | Effect |
| --- | --- | --- |
| `MCP_HTTP_ENABLED` | `True` | Master switch |
| `MCP_PUBLIC_URL` | Your dashboard URL | Issuer for OAuth tokens |
| `MCP_OAUTH_REQUIRE_APPROVAL` | `True` | New clients land pending until you approve |
| `MCP_OAUTH_WRITE_SCOPE_ENABLED` | `False` | **Read-only by default** — order placement off until you opt in |
| `MCP_HTTP_CORS_ORIGINS` | `https://claude.ai,https://chatgpt.com` | Browsers that can complete OAuth |

Read-only is the safe starting posture. Flip `MCP_OAUTH_WRITE_SCOPE_ENABLED=True` later, after you've watched a few read-only sessions in the audit log and decided you want order placement from AI clients.

***

## Connecting & using ChatGPT and Claude

Once it's enabled, your MCP URL is:

```
https://yourdomain.com/mcp
```

The first connect is a six-step dance the AI client does mostly automatically. The one human step is approving the new client at `/admin/remote-mcp` — your server holds it there until you say so, which is what stops random people from registering against your domain.

***

### Adding OpenAlgo to ChatGPT

> Heads up — ChatGPT recently renamed **Connectors → Apps**. Same feature, new menu name. The in-chat menu still says *Connectors*, so don't be confused.

#### Step 1 — Open Apps settings

1. Avatar (bottom left) → **Settings**
2. Sidebar → **Apps**
3. Top right → **Add more** → opens **New App BETA**

#### Step 2 — Fill in the form

| Field | Value |
| --- | --- |
| Name | `OpenAlgo` |
| Description | `OpenAlgo trading server` (optional) |
| MCP Server URL | `https://yourdomain.com/mcp` |
| Authentication | `OAuth` |

#### Step 3 — Advanced OAuth settings

Expand **Advanced OAuth settings** → **Registration method** → `Dynamic Client Registration (DCR)`.

The notice *"CIMD is unavailable…"* is expected — OpenAlgo advertises DCR. DCR is the right pick.

Default scopes ChatGPT requests are `read:market read:account`. Add `write:orders` only if you've turned `MCP_OAUTH_WRITE_SCOPE_ENABLED=True` on the server **and** you want this connector to place orders.

#### Step 4 — Acknowledge and create

Tick *"I understand and want to continue"* under the orange warning, then **Create**.

#### Step 5 — Expected error

ChatGPT will show:

> OAuth authorization failed: unauthorized_client

This is normal. Your server saw the registration but is holding it until you approve. Don't dismiss the modal.

#### Step 6 — Approve in OpenAlgo

1. New tab → `https://yourdomain.com/admin/remote-mcp`
2. Sign in (TOTP if MCP 2FA is on)
3. **Pending approvals** → verify name + timestamp match → **Approve**

#### Step 7 — Complete OAuth

1. Back in ChatGPT → **Reconnect**
2. A tab pops to `https://yourdomain.com/oauth/authorize?...`
3. Sign in if needed → consent screen lists scopes (verify the redirect URI is a `chatgpt.com` URL) → **Authorize**
4. App moves from Drafts to Enabled

#### Step 8 — Use it

In any new chat, click **+** below the message box → **Connectors** → toggle **OpenAlgo** ON.

Try:

> *"Using OpenAlgo, give me the LTP of RELIANCE on NSE."*

ChatGPT calls `get_quote` and shows the price. With `read:account` granted, also try:

> *"What's my account balance and current open positions?"*

#### What works on ChatGPT

- All read-only tools work cleanly: quotes, depth, holdings, positions, funds, history, orderbook
- `modify_order`, `cancel_order`, `cancel_all_orders` usually go through
- `place_order` is often blocked by ChatGPT's own safety policy even when `write:orders` was granted. If you need order placement from a hosted client, use Claude.ai

#### Useful ChatGPT prompts

- *"Get me the bid-ask spread for INFY and HDFCBANK"*
- *"Summarise my holdings and tell me which are in profit"*
- *"Pull 1-day candles for SBIN for the last 30 days and tell me the trend"*
- *"List my orders from today and show fills vs rejects"*

***

### Adding OpenAlgo to Claude.ai

#### Step 1 — Connectors page

claude.ai → name (bottom left) → **Settings** → **Connectors**.

#### Step 2 — Add custom

Top right **+** → **Add custom connector**.

#### Step 3 — Fill in

| Field | Value |
| --- | --- |
| Name | `OpenAlgo` |
| Remote MCP server URL | `https://yourdomain.com/mcp` |

Leave **Advanced settings** alone — OAuth is detected automatically. Click **Add**.

#### Step 4 — Expected error

Same as ChatGPT — first attempt fails with a pending-approval error. Keep the page open.

#### Step 5 — Approve in OpenAlgo

`https://yourdomain.com/admin/remote-mcp` → **Pending approvals** → **Approve**.

#### Step 6 — Complete OAuth

Back in claude.ai → **Connect** on the connector card → sign in to OpenAlgo (+ TOTP if on) → consent screen (verify redirect URI is `claude.ai`) → **Authorize**. Card switches to **Disconnect** when you're live.

#### Step 7 — Tool permissions

Click your **OpenAlgo** connector to expand permissions:

| Group | Recommendation |
| --- | --- |
| Interactive tools (`place_order`, `modify_order`, `cancel_order`, ...) | **Ask me** at first; **Always allow** once you trust the prompts |
| Read-only tools | **Always allow** |
| App-only tools | **Always allow** |

You can override individual tools — e.g. *Always allow* most things but force *Ask me* for `cancel_all_orders`.

#### Step 8 — Use it

In any chat, click the **Tools** icon below the message box → toggle **OpenAlgo** on.

> *"Show me the current LTP of NIFTY 50 and a quick view of my open positions."*

Claude shows expandable tool-call cards. *Ask me* tools surface a permission prompt with **Allow once / Always allow / Deny**.

#### What works on Claude.ai

- All read-only tools work
- All write tools work — `place_order`, `modify_order`, `cancel_order`, `cancel_all_orders`
- The same OAuth tokens work in the **Claude iOS / Android apps** — chat-trade from your phone, no extra setup

#### Recommended posture for write tools

- Start in **Sandbox / Analyzer mode** (`/analyzer`) and dry-run prompts before turning live trading on
- Keep **MCP 2FA** on — every fresh authorization demands a TOTP code
- Set a tight `MCP_RATE_LIMIT_WRITE` (e.g. `5 per minute`) so a runaway model can't fire a flurry of orders before you intervene
- Tail `log/mcp.jsonl` while testing — every call recorded with timestamp, scope, outcome, latency
- Keep the **Kill switch** at `/admin/remote-mcp` one click away

#### Useful Claude prompts

- *"Place a limit BUY for 1 share of TCS at ₹3500 in CNC product on NSE"*
- *"Modify my last open INFY order — change the quantity to 5"*
- *"Cancel all my open orders"*
- *"What was my P&L today?"*

For more example prompts per tool, see the Tool References — the same prompts work on Remote MCP.

***

## Switching scopes after connecting

Already connected with `read:market read:account` and want to add `write:orders`?

1. Set `MCP_OAUTH_WRITE_SCOPE_ENABLED=True` in `.env` and restart
2. **Disconnect** the connector / app in ChatGPT or Claude
3. Re-add it with the broader scope set
4. Re-approve at `/admin/remote-mcp`

OAuth doesn't let an existing token widen its scope — re-consent is required. By design.

***

## Daily operations

### `/admin/remote-mcp`

| Section | What it's for |
| --- | --- |
| **Pending approvals** | New clients land here. Approve only ones you recognise — the name is set by the hosted client itself |
| **Approved clients** | Currently authorised. Each row shows last-used time |
| **Revoked clients** | Historical — cannot re-authorize without admin re-approval |
| **MCP tool call audit** | Every tool call: timestamp, client, tool, scope, outcome, latency. Filter by tool or outcome |
| **Kill switch** | One click revokes every refresh token across every approved client. Use it the moment something looks wrong |

### Audit log

Same data as the admin page, written to `log/mcp.jsonl` as JSON Lines. Tail with:

```bash
tail -f log/mcp.jsonl
```

Tool **arguments are hashed**, not stored verbatim — the log itself is not a data leak.

### 2FA enforcement

Profile → TOTP → **2FA Enforcement** lets you gate three independent purposes:

| Purpose | What it gates |
| --- | --- |
| Dashboard sign-in | TOTP after password on every login |
| Remote MCP authorization | Fresh TOTP at `/oauth/authorize` for every `write:orders` grant |
| Password reset | Forces TOTP path (no email fallback) |

All three default off so existing installs see no change. Saving requires a fresh TOTP code in the same request — proves you have authenticator access for both enabling and disabling.

***

## Configuration reference

All keys live in `.env` (native) or the bind-mounted `.env` (Docker). The first five are set by the installer.

| Key | Default | Purpose |
| --- | --- | --- |
| `MCP_HTTP_ENABLED` | `False` | Master switch |
| `MCP_PUBLIC_URL` | required when enabled | Public HTTPS origin advertised in OAuth metadata |
| `MCP_OAUTH_REQUIRE_APPROVAL` | `True` | New clients land pending until admin approves |
| `MCP_OAUTH_WRITE_SCOPE_ENABLED` | `False` | Whether `write:orders` is grantable at all |
| `MCP_HTTP_CORS_ORIGINS` | `https://claude.ai,https://chatgpt.com` | Browser allowlist |
| `MCP_HTTP_IP_ALLOWLIST` | empty | Optional IP / CIDR allowlist on `/mcp` |
| `MCP_OAUTH_ACCESS_TTL` | `900` | Access-token TTL in seconds (max 3600) |
| `MCP_OAUTH_REFRESH_TTL` | `2592000` | Refresh-token TTL in seconds (30 days) |
| `MCP_OAUTH_CODE_TTL` | `60` | Authorization-code TTL (max 300) |
| `MCP_RATE_LIMIT_READ` | `60 per minute` | Per-token cap for read scopes |
| `MCP_RATE_LIMIT_WRITE` | `50 per minute` | Per-token cap for `write:orders` |
| `MCP_LOOPBACK_URL` | inherits `HOST_SERVER` | Override only for unusual topologies |
| `MCP_OAUTH_KEYS_DIR` | `keys` | Directory for RS256 signing keys |

***

## Security model

The defenses, in plain order:

1. **Approval gate** — random clients can register but cannot complete OAuth until you approve them at `/admin/remote-mcp`
2. **Read-only by default** — `write:orders` is invisible in OAuth discovery until you flip `MCP_OAUTH_WRITE_SCOPE_ENABLED=True`
3. **Short access tokens** — 15-minute TTL caps the damage window if a token is stolen
4. **Rate limits** — per-token, separately for reads and writes
5. **PKCE + JWT** — all the standard OAuth 2.1 hardening (S256-only, exact redirect_uri, refresh token rotation with reuse detection)
6. **Kill switch** — one click revokes everything

> **The blast radius is real.** A stolen access token can place orders the broker accepts — they originate from your registered server IP. The 15-minute TTL caps damage; the kill switch is your panic button. Never combine `MCP_OAUTH_WRITE_SCOPE_ENABLED=True` with `MCP_OAUTH_REQUIRE_APPROVAL=False` — that lets any internet client register, auto-approve, and start placing orders.

For the full threat model and per-defense rationale, see `docs/prd/remote-mcp.md`.

***

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `unauthorized_client` after Create / Add | DCR client not approved yet | Approve at `/admin/remote-mcp` |
| `invalid_client` on retry | Client revoked or DB reset; old `client_id` cached | Disconnect + re-add to force fresh DCR |
| *"Server doesn't implement OAuth"* | Old build | Update to 2.0.1.0+ |
| *"CIMD is unavailable"* in ChatGPT | OpenAlgo advertises DCR, not CIMD | Expected — pick **DCR** |
| Tools missing from chat | Connector not toggled on for that chat | `+` menu (ChatGPT) or Tools menu (Claude) |
| `bad_arguments` on a tool call | Hosted client guessed parameter names | Update OpenAlgo (newer builds expose strict tool schemas) |
| Sudden 401 on every call | Refresh token expired or kill switch fired | **Reconnect** on the connector |
| `place_order` blocked on ChatGPT | OpenAI's safety policy | Use Claude.ai for order placement |
| *"Failed to connect to the server"* on tool calls | Loopback misconfigured | Confirm `HOST_SERVER` in `.env` matches your dashboard URL; restart |
| Tokens issued but `/mcp` returns 401 | `MCP_PUBLIC_URL` doesn't match the URL the client uses | Make them exactly equal — `https://example.com` ≠ `https://www.example.com` |
| Form submit blocked by CSP | Old build | Update to 2.0.1.0+ |
| Container won't restart after enabler | Bad `.env` change | Run the rollback one-liner the enabler printed; restart; check `log/errors.jsonl` |

***

## Subdomain mode (advanced)

If you want MCP on a separate hostname (e.g. `mcp.yourdomain.com`) so its cookies, CORS, and TLS lifecycle are isolated from the dashboard, the manual recipe is in `install/Remote-MCP-readme.md`. Same nginx + certbot pattern as `install-docker-multi-custom-ssl.sh`. Most users don't need this — same-domain is what the installer automates.

***

## Disabling

Native:

```bash
sudo sed -i "s|MCP_HTTP_ENABLED.*|MCP_HTTP_ENABLED = 'False'|" /var/python/openalgo/.env
sudo systemctl restart openalgo
```

(`install-multi.sh` users: substitute the per-deploy `.env` and service name.)

Docker:

```bash
sudo sed -i "s|MCP_HTTP_ENABLED.*|MCP_HTTP_ENABLED = 'False'|" /opt/openalgo/<domain>/.env
cd /opt/openalgo/<domain> && sudo docker compose restart
```

OAuth + MCP routes immediately stop responding. Existing tokens hit 404. **Local stdio MCP is unaffected** — it runs over stdin/stdout and doesn't touch the HTTP transport.

For a softer takedown that keeps Remote MCP enabled but boots every active session: visit `/admin/remote-mcp` → **Kill switch**. Hosted clients are forced through a fresh OAuth dance the next time they refresh.

***

## Related

- MCP Server Setup Guide — local stdio integration with Claude Desktop / Cursor / Windsurf
- Tool References — every tool with parameters and example prompts (shared across both transports)
- OpenAlgo Symbol Format — how equity / future / option symbols are constructed
- `install/Remote-MCP-readme.md` — operator-focused install + threat model in the source tree
- `docs/prd/remote-mcp.md` — full architecture and threat model


---

# Agent Instructions: Querying This Documentation

If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.openalgo.in/mcp/remote-mcp.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

```


---

# FILE: docs\userguide\TRACKER.md

```md
# OpenAlgo User Guide - Tracker

## About This Guide

This comprehensive user guide is designed for **traders of all levels** - from complete beginners to experienced algo traders. It serves as the definitive reference for using OpenAlgo effectively.

**Target Audience**: Traders, investors, and anyone wanting to automate their trading

**Prerequisite Knowledge**: Basic understanding of stock markets and trading

## Progress Overview

| # | Module | Status | Difficulty |
|---|--------|--------|------------|
| 01 | What is OpenAlgo | ✅ Complete | Beginner |
| 02 | Key Concepts | ✅ Complete | Beginner |
| 03 | System Requirements | ✅ Complete | Beginner |
| 04 | Installation Guide | ✅ Complete | Beginner |
| 05 | First-Time Setup | ✅ Complete | Beginner |
| 06 | Broker Connection | ✅ Complete | Beginner |
| 07 | Dashboard Overview | ✅ Complete | Beginner |
| 08 | Understanding the Interface | ✅ Complete | Beginner |
| 09 | API Key Management | ✅ Complete | Beginner |
| 10 | Placing Your First Order | ✅ Complete | Beginner |
| 11 | Order Types Explained | ✅ Complete | Intermediate |
| 12 | Smart Orders | ✅ Complete | Intermediate |
| 13 | Basket Orders | ✅ Complete | Intermediate |
| 14 | Positions & Holdings | ✅ Complete | Beginner |
| 15 | Analyzer Mode (Sandbox Testing) | ✅ Complete | Beginner |
| -- | **Symbol Format Guide** | ✅ Complete | All Levels |
| 16 | TradingView Integration | ✅ Complete | Intermediate |
| 17 | Amibroker Integration | ✅ Complete | Intermediate |
| 18 | ChartInk Integration | ✅ Complete | Intermediate |
| 19 | GoCharting Integration | ✅ Complete | Intermediate |
| 20 | Python Strategies | ✅ Complete | Advanced |
| 21 | Flow Visual Builder | ✅ Complete | Intermediate |
| 22 | Action Center | ✅ Complete | Intermediate |
| 23 | Telegram Bot | ✅ Complete | Beginner |
| 24 | PnL Tracker | ✅ Complete | Beginner |
| 25 | Latency Monitor | ✅ Complete | Intermediate |
| 26 | Traffic Logs | ✅ Complete | Intermediate |
| 27 | Security Settings | ✅ Complete | Beginner |
| 28 | Two-Factor Authentication | ✅ Complete | Beginner |
| 29 | Troubleshooting | ✅ Complete | All Levels |
| 30 | FAQs | ✅ Complete | All Levels |

## Learning Path

### Path 1: Quick Start (New Users)
1. What is OpenAlgo (01)
2. Installation Guide (04)
3. First-Time Setup (05)
4. Broker Connection (06)
5. **Symbol Format Guide** (Reference)
6. Placing Your First Order (10)
7. Analyzer Mode (15)

### Path 2: TradingView Traders
1. Quick Start Path
2. API Key Management (09)
3. TradingView Integration (16)
4. Order Types (11)
5. Action Center (22)

### Path 3: Amibroker Users
1. Quick Start Path
2. API Key Management (09)
3. Amibroker Integration (17)
4. Smart Orders (12)
5. Basket Orders (13)

### Path 4: Advanced Automation
1. Complete Intermediate modules
2. Python Strategies (20)
3. Flow Visual Builder (21)
4. ChartInk Integration (18)

## Difficulty Legend
- **Beginner**: No programming knowledge required
- **Intermediate**: Basic understanding of APIs helpful
- **Advanced**: Programming knowledge required

## Guide Standards
- Step-by-step instructions with screenshots descriptions
- Real-world examples and use cases
- Tips and best practices highlighted
- Common mistakes and how to avoid them
- Video tutorial links where available

```
