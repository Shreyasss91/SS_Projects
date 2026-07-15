# Chartink

Inventory and documentation workspace for Chartink scans.

## Layout

```text
chartink/
  scans_url_index.md          # main index: sl no, name, URL, folded details (478 scans)
  README.md

  data/exports/               # machine-readable captures
  tools/                      # re-runnable export / index helpers
  docs/
    scan-wiki/                # per-scan wiki scaffold + template
    session_handover/         # prior session notes / task spec
  archive/
    scrape-probes/            # one-off auth/scrape experiments (kept for reference)
    raw-captures/             # HTML/JS dumps from failed automated attempts
```

## Main deliverable

- **[scans_url_index.md](scans_url_index.md)** — full dashboard inventory (478 scans).

## Data

| File | Purpose |
|---|---|
| `data/exports/chartink_dashboard_pages.json` | Canonical multi-page dashboard export (Inertia payloads) |
| `data/exports/all_scans_raw.json` | Flattened scan objects used for the index |
| `data/exports/history_screeners.json` | Chrome-history sample of screener URLs (partial) |
| `data/exports/chartink_dashboard_pages.from_raw_dashboard.json` | Alternate export copy from the scrape session |

## Tools

| Script | Purpose |
|---|---|
| `tools/export_dashboard_console.js` | Paste in Chrome DevTools (logged-in Chartink) to download a fresh multi-page export |
| `tools/process_export.py` | Rebuild `scans_url_index.md` from an export JSON |
| `tools/clip_export_script.py` | Copy the console export script to the clipboard |

Rebuild index:

```bash
python chartink/tools/process_export.py
# or
python chartink/tools/process_export.py path/to/chartink_dashboard_pages.json
```

## Docs

- **Scan wiki (main deliverable detail pages):** [`docs/scan-wiki/README.md`](docs/scan-wiki/README.md) — 478 pages + source snapshots + QA
- Rebuild wiki from export: `python tools/build_scan_wiki.py`
- Wiki template / capture protocol: `docs/scan-wiki/_template.md`, `_capture-protocol.md`
- Session / task notes: `docs/session_handover/`

## Archive

Probe scripts and raw captures under `archive/` are not required for normal use. They record how the inventory was attempted/automated. Safe to keep; ask before deleting.
