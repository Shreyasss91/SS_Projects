"""Metric layer for the Market Depth Recorder.

``registry`` holds the declarative metric registry (spec §3.4.0): every metric (M1–M29, the
rolling-window outputs of §3.4.3, and the multi-strike aggregates / regime of §3.4.4) is a
declarative :class:`~market_depth_recorder.metrics.registry.MetricSpec` entry rather than an
inline hardcoded list. Function bodies (the actual NumPy computations) are added in P4/P7; P0
registers metadata only.
"""
