"""P10-B — dated-sub-folder storage layout.

Covers the `session_output_dir` helper, the live writers landing the day's data in
`<output_dir>/<YYYY-MM-DD>/` when `recorder.date_partitioned` is set, and replay resolving the
canonical DuckDB / live-store paths *beside the raw log* (flat- and partitioned-agnostic), incl.
`catchup` discovering raws in dated sub-folders. Offline — no live feed.
"""

from __future__ import annotations

import gzip
import os
import queue
import threading
from datetime import date

from market_depth_recorder import replay
from market_depth_recorder.config import load_config
from market_depth_recorder.database_writer import DuckDBAnalyticalWriter, SQLiteLiveWriter
from market_depth_recorder.file_writer import RawTickFileWriter
from market_depth_recorder.utils import session_output_dir

SESSION = date(2026, 7, 6)
DATED = "2026-07-06"


# ---- helper -----------------------------------------------------------------------------------
def test_session_output_dir_partitioned_appends_date():
    assert session_output_dir("/data", SESSION, True) == os.path.join("/data", DATED)


def test_session_output_dir_flat_when_disabled():
    assert session_output_dir("/data", SESSION, False) == "/data"


def test_session_output_dir_flat_when_date_none():
    # Defensive: a missing session_date must not produce a "/data/None" path.
    assert session_output_dir("/data", None, True) == "/data"


# ---- writers land in the dated sub-folder -----------------------------------------------------
def _load(base_config, write_config, *, partitioned: bool):
    base_config["recorder"]["date_partitioned"] = partitioned
    return load_config(write_config(base_config))


def test_raw_writer_output_dir_dated(base_config, write_config):
    cfg = _load(base_config, write_config, partitioned=True)
    base = cfg.recorder["output_dir"]
    w = RawTickFileWriter(cfg, queue.Queue(), threading.Event(), SESSION)
    assert w.output_dir == os.path.join(base, DATED)
    assert w.resolve_filename(w.output_dir, SESSION) == os.path.join(
        base, DATED, "market_depth_raw_20260706.jsonl.gz"
    )


def test_live_writer_output_dir_dated(base_config, write_config):
    cfg = _load(base_config, write_config, partitioned=True)
    base = cfg.recorder["output_dir"]
    w = SQLiteLiveWriter(cfg, queue.Queue(), threading.Event(), SESSION)
    assert w.output_dir == os.path.join(base, DATED)


def test_writers_flat_when_partitioning_disabled(base_config, write_config):
    cfg = _load(base_config, write_config, partitioned=False)
    base = cfg.recorder["output_dir"]
    raw = RawTickFileWriter(cfg, queue.Queue(), threading.Event(), SESSION)
    live = SQLiteLiveWriter(cfg, queue.Queue(), threading.Event(), SESSION)
    assert raw.output_dir == base and live.output_dir == base


def test_default_absent_partition_key_is_flat(base_config, write_config):
    # No date_partitioned key at all → treated as flat (backward compatible).
    base_config["recorder"].pop("date_partitioned", None)
    cfg = load_config(write_config(base_config))
    w = RawTickFileWriter(cfg, queue.Queue(), threading.Event(), SESSION)
    assert w.output_dir == cfg.recorder["output_dir"]


# ---- replay paths sit beside the raw log ------------------------------------------------------
def test_replay_canonical_and_live_paths_beside_raw(base_config, write_config, tmp_path):
    cfg = _load(base_config, write_config, partitioned=True)
    dated_dir = tmp_path / "data" / DATED
    dated_dir.mkdir(parents=True)
    raw_path = str(dated_dir / "market_depth_raw_20260706.jsonl.gz")

    assert replay.canonical_output(cfg, raw_path) == str(
        dated_dir / "market_depth_analytics_20260706.duckdb"
    )
    assert replay.live_store_path(cfg, raw_path) == str(
        dated_dir / "market_depth_live_20260706.db"
    )
    # sanity: the duckdb path equals the writer's own resolver rooted at the raw's dir.
    assert replay.canonical_output(cfg, raw_path) == DuckDBAnalyticalWriter.resolve_filename(
        str(dated_dir), SESSION
    )


# ---- catchup discovers raws in dated sub-folders ----------------------------------------------
def test_catchup_discovers_dated_and_flat_raws(base_config, write_config, tmp_path, monkeypatch):
    cfg = _load(base_config, write_config, partitioned=True)
    base = tmp_path / "data"
    # A dated-subdir raw (new layout) and a legacy flat raw at the base — both must be found.
    dated = base / DATED
    dated.mkdir(parents=True)
    dated_raw = dated / "market_depth_raw_20260706.jsonl.gz"
    flat_raw = base / "market_depth_raw_20260705.jsonl.gz"
    for p in (dated_raw, flat_raw):
        with gzip.open(p, "wt", encoding="utf-8") as fh:
            fh.write("")  # content irrelevant — replay_file is stubbed

    seen: list[tuple[str, str]] = []

    def _fake_replay_file(config, raw, out, **kw):
        seen.append((os.path.normpath(raw), os.path.normpath(out)))
        return None

    monkeypatch.setattr(replay, "replay_file", _fake_replay_file)
    built = replay.catchup(cfg)

    assert built == 2
    seen_map = dict(seen)
    # each duckdb is written beside its own raw (same dated sub-folder for the dated one)
    assert seen_map[os.path.normpath(str(dated_raw))] == os.path.normpath(
        str(dated / "market_depth_analytics_20260706.duckdb")
    )
    assert seen_map[os.path.normpath(str(flat_raw))] == os.path.normpath(
        str(base / "market_depth_analytics_20260705.duckdb")
    )
