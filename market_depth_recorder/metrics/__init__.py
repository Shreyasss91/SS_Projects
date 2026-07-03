"""Metric layer for the Market Depth Recorder.

``registry`` holds the declarative metric registry (spec §3.4.0): every metric (M1–M29, the
rolling-window outputs of §3.4.3, and the multi-strike aggregates / regime of §3.4.4) is a
declarative :class:`~market_depth_recorder.metrics.registry.MetricSpec` entry rather than an
inline hardcoded list.

Function bodies (the actual NumPy computations) are bound to those specs in P4/P7:
  * ``per_strike`` — M1–M29 single-snapshot metrics (P4a).
  * ``rolling`` / ``aggregate`` — §3.4.3 window + §3.4.4 aggregate/regime metrics (P4b, not yet present).
Importing the compute module runs its ``@bind(name)`` decorators, so ``registry.METRIC_FUNCS`` is
populated as a side effect of importing this package. ``snapshot`` holds the shared
:class:`BookSnapshot` / :class:`MetricContext` the bodies consume.
"""

from . import per_strike  # noqa: F401  — side effect: binds M1–M29 bodies into registry.METRIC_FUNCS
