“Continue the Chartink wiki overhaul from the source audit.”
019f63e4-21e8-7362-960d-a0f987c89a74  


keep this task list in mind(modify if needed)
  ### Remaining

    1. Inspect the available JSON exports and determine whether they contain full scan definitions and filter states.
    2. Capture or recover each scan’s complete condition tree.
    3. Record every filter’s exact wording, order, grouping, and enabled/disabled state.
    4. Record scan-level settings such as universe, timeframe, periodicity, and sorting.
    5. Preserve raw source captures before adding explanations.
    6. Create one detailed Markdown page for each scan.
    7. Classify each scan by horizon, method, and context.
    8. Explain calculation logic, usage, strengths, limitations, and false-signal risks.
    9. Update the wiki index with page links and filter counts.
    10. Perform final QA for all 478 scans, including source fidelity and reconciliation.
	
	
material quality issues to fix:
  - Method classifications and tags are sometimes inferred from titles instead of actual active conditions.
  - Filter tables include group rows alongside filters, which makes them less clear.
  - Much of the explanatory prose is generic rather than tailored to the scan’s real logic.
  - “Verbatim” should be labeled more precisely: the text tree is a faithful rendering of atlas_json; atlas_query is the literal compiled Chartink query.
  - The current QA validates its own rendering, but needs stronger source-to-page checks.
  
  