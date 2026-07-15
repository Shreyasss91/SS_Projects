# Scan Wiki QA Report

Generated: 2026-07-15T13:10:23.380546+05:30

## Inventory reconciliation

- Export scans: 478
- Expected dashboard total: 478
- Match: YES
- Unique IDs: 478
- Unique filenames: 478

## Source fidelity

- Scans with isEnabled status matching table: 478/478
- Status mismatches: 0
- Missing pages: 0
- Empty/short verbatim definitions: 0
- Filter table mismatches: 0
- Missing snapshots: 0

## Issues

No critical issues found. All 478 scans reconciled with source snapshots and pages.

## Counts

- Total enabled leaf filters: 2614
- Total disabled leaf filters: 671
- Scans containing ≥1 disabled filter: 218
- Scans with zero enabled leaves: 0

## Notes

- Verbatim definitions are reconstructed from `atlas_json` so disabled filters are retained;
  `atlas_query` is also stored because it is Chartink's compiled active query string.
- Sorting UI state is not present in the dashboard list export fields; not fabricated.
- Periodicity is represented via measure offsets (daily/weekly/monthly/N-minute) inside conditions.
