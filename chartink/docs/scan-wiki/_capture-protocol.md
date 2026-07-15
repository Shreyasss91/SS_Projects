# Scan capture protocol

Capture before documenting. For each dashboard scan, record:

1. Scan ID, exact title, source URL, dashboard description/metadata, and the
   full definition.
2. Each filter in display order, with its exact wording and enabled/disabled
   state. Preserve nested groups and parentheses/AND/OR relationships.
3. Any scan-level settings that change results (universe, periodicity, sorting,
   or other options visible in Chartink).
4. A capture timestamp and the number of enabled and disabled filters.

When the UI shows disabled filters only through styling or a toggle, store that
state explicitly in the page's filter table. The verbatim definition is not a
substitute for the status record.

Do not rename scan titles, infer missing filters, enable disabled filters, or
reorder conditions during capture. Analysis is added only after this snapshot
has been verified.
