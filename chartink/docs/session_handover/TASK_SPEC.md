# Detailed Task Specification

## 1. Deliverable

Build a searchable Markdown wiki documenting every scan visible on the user's Chartink dashboard at capture time. It covers Indian-equity scans intended for intraday, swing, and positional workflows. The deliverable preserves the original Chartink definitions and adds detailed educational explanations; it does not redesign scans, give personalised investment advice, or execute trades.

## 2. Required input

For every scan, obtain:

- exact display name;
- stable Chartink identifier and canonical source URL;
- full displayed scan definition, including all groups and filters;
- explicit enabled/disabled state for every filter;
- visible scan-level settings that affect results.

Preferred additional data: dashboard order/folder, description, visible metadata, timestamped screenshot/raw text, and official Chartink explanations for non-obvious operators.

If authenticated browser access is unavailable, accept user-supplied copied definitions, HTML, screenshots, or export files placed in the workspace. Titles alone are insufficient: no page can be complete without its full definition and filter states.

## 3. Output layout

Use the following structure unless real dashboard organisation justifies a clearer, equivalent arrangement:

```text
docs/scan-wiki/
  README.md                         # linked Markdown index and reconciliation
  _template.md                      # template only; not a scan page
  _capture-protocol.md              # source-capture rules
  scans/
    <stable-id>--<safe-title>.md    # one page per source scan
  source-snapshots/                 # optional immutable raw captures
```

Markdown is the primary required output. Do not replace the wiki/index with a CSV. A machine-readable supplement is optional only if the Markdown remains authoritative.

Filenames must use a stable ID plus a filesystem-safe title. Keep the exact displayed title in front matter and heading, even if it contains characters unsuitable for a filename.

## 4. Mandatory page content

Every `scans/*.md` file must contain all of the following:

1. **YAML front matter**: `scan_id`, `scan_name`, `source_url`, `market`, `horizon`, `classification`, `tags`, `captured_at`, `enabled_filter_count`, and `disabled_filter_count`.
2. **Source**: original identity and capture metadata.
3. **What this scan is for**: a cautious plain-language explanation of the screening objective.
4. **Exact Chartink scan definition**: the complete source copied verbatim in a fenced `text` block. It includes enabled and disabled filters, groups, display order, and visible scan-level settings.
5. **Filter status and interpretation**: an ordered table with one row per filter and columns for ordinal position, status, verbatim filter, and explanation.
6. **How the enabled logic works**: the role of each active filter, boolean interaction, total selection, and selectivity.
7. **Disabled filters**: each condition, the hypothesis/confirmation it would add, expected change if enabled, and trade-offs; mark authorial intent as inference unless evidenced.
8. **Calculation notes**: formulas/inputs, periods, price fields, crossover or comparison behavior, offsets, and known Chartink semantics.
9. **How to use it**: likely horizon, universe/liquidity context, confirmation, timing, invalidation/risk considerations, and operational constraints.
10. **Strengths** plus **Limitations and false-signal risks**.
11. **Classification and related concepts**: controlled tags and conceptual references only; no silent deduplication.

## 5. Source-fidelity contract

The following rules are binding:

- Every source filter appears in the exact-definition block and filter table.
- Enabled filters retain `Enabled` status; disabled filters retain `Disabled` status.
- Original wording, order, nesting, AND/OR logic, parentheses, fields, periods, offsets, thresholds, and comparators are retained.
- The source definition must never be replaced with a cleaned-up formula, reconstructed pseudo-code, or explanation.
- Interpretive text must remain outside the exact-definition block.
- If a visual state or expression is ambiguous, use `Needs review`, preserve available evidence, and report the exception rather than guessing.

## 6. Workflow milestones

### A. Inventory

Enumerate all dashboard scans. Create a raw inventory with ID, name, URL, and dashboard order. Record the dashboard's reported total and reconcile it to inventory count. Name every inaccessible or errored scan explicitly.

### B. Complete source capture

Open every scan and record its complete definition, scan-level settings, and visual enabled/disabled filter states. Save raw captures before writing explanations. Track `captured`, `needs-review`, and `not-accessible` states.

### C. Source QA

Before analysis, verify for each captured scan that:

- filter table rows equal enabled + disabled + needs-review counts;
- all table filters occur in the source snapshot;
- group structure and operators were retained;
- ID, title, and URL match the inventory.

### D. Detailed authoring

Classify and write each page using actual scan logic. Batch processing is allowed only after raw source data is durable and verified. Avoid generic boilerplate that does not describe the particular scan.

### E. Final QA

Check links, duplicate IDs, duplicate filenames, missing headings, empty verbatim blocks, missing disabled filters, and inventory reconciliation. Read a representative sample across all horizons and methods. Produce an exceptions section in the index.

## 7. Acceptance criteria

The task is complete when all are true:

- Index inventory count equals the dashboard count, or every discrepancy is named and explained.
- Each documented scan has one uniquely identified Markdown file.
- Every page has a non-empty complete verbatim definition and an explicit row for every filter.
- Disabled filters are present in both source and table and receive separate analysis.
- Calculations, practical use, strengths, and limitations are tailored to each scan's logic.
- No source condition is altered and no Chartink scan is modified.

## 8. Explicit non-goals

- Executing scans, trades, orders, alerts, or automations.
- Asking for credentials or extracting browser cookies/passwords.
- Combining similar scans, changing their names/logic, or deleting duplicates.
- Claiming return, win-rate, or suitability guarantees.
