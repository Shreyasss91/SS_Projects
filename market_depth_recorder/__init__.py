"""Market Depth Recorder — standalone high-throughput option market-depth capture microservice.

The folder *is* the Python package (spec §2.1). Run it from the parent ``SS_Projects/`` with::

    python -m market_depth_recorder --validate-config --config market_depth_recorder/config.yaml

Three-tier persistence pipeline: Tier 0 raw ``.jsonl.gz`` (lossless source of truth) →
Tier 1 thin live SQLite/WAL (``recorder.live_metrics`` subset) → Tier 2 fat DuckDB analytics
(full catalog, rebuilt offline by replaying Tier 0). Config-driven and broker/exchange/symbol-agnostic.
"""

__version__ = "0.1.0"

# Bumped whenever the §4 column set (persisted schema) changes. Stamped into the raw HEADER line
# (§3.5.4) and the ``recorder_meta`` provenance table (§4.1b); ``--verify`` refuses to diff mismatched
# schema versions (§8.4).
SCHEMA_VERSION = 1
