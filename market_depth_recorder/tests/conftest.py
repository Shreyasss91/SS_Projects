"""Shared pytest fixtures: a known-good config dict plus a helper to materialize it to a YAML file.

The good config mirrors the shipped ``config.yaml`` (§7.1) but points ``output_dir`` /
``health_file_path`` at a per-test ``tmp_path`` so validation's write-probe (rule 2/4) has no
side effects on the working tree. Negative tests deep-copy this dict and mutate one field.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Callable

import pytest
import yaml

PACKAGE_ROOT = Path(__file__).resolve().parent.parent


def pytest_configure(config):
    """Register the ``integration`` marker (P8 whole-pipeline harness) so it is deselectable
    (``-m "not integration"``) without a PytestUnknownMarkWarning."""
    config.addinivalue_line(
        "markers", "integration: whole-pipeline soak harness (real threads + real reprocess subprocess)"
    )


def _good_config(data_dir: str) -> dict[str, Any]:
    return {
        "openalgo": {
            "host_server": "http://127.0.0.1:5000",
            "websocket_url": "ws://127.0.0.1:8765",
            "api_key": "openalgo-apikey",
        },
        "recorder": {
            "output_dir": data_dir,
            "log_level": "INFO",
            "resample_interval_sec": 1.0,
            "staleness_timeout_sec": 5.0,
            "session_start": "09:15",
            "session_end": "15:30",
            "teardown_grace_min": 5,
            "health_file_path": str(Path(data_dir) / "health.json"),
            "health_write_interval_sec": 10,
            "min_free_disk_mb": 2048,
            "disk_check_interval_sec": 60,
            "skip_non_trading_days": False,
            "trading_holidays": [],
            "supervisor_interval_sec": 5,
            "max_restart_attempts": 3,
            "live_metrics": ["spread", "weighted_obi", "book_pressure", "best_bid_qty",
                             "best_ask_qty", "atm_aggregates", "regime"],
        },
        "metrics": {
            "decay_k": 0.2,
            "effective_depth_pct": 0.005,
            "round_number_multiples": [5, 10],
            "book_pressure_levels": 10,
            "fill_probe_qty": 1500,
            "wall_sigma_mult": 3.0,
            "time_windows_sec": [5, 10, 30],
            "small_window_strikes": 2,
            "medium_window_divisor": 2,
        },
        "regime": {
            "theta_pressure": 5.0e6,
            "theta_bias": 0.15,
            "theta_pinning": 3.0,
            "theta_spread": 0.02,
            "quote_stability_min": 0.4,
        },
        "queues": {
            "max_queue_size": 50000,
            "raw_file_queue_max": 100000,
            "warn_watermark_pct": 70,
            "critical_watermark_pct": 90,
        },
        "file_writer": {
            "gzip_compresslevel": 6,
            "flush_max_records": 500,
            "fsync_interval_sec": 2.0,
        },
        "database": {
            "batch_size": 500,
            "batch_write_interval_ms": 1000,
            "cache_size_mb": 64,
            "wal_checkpoint_interval_sec": 600,
        },
        "analytics_db": {
            "memory_limit_mb": 2048,
            "threads": 4,
            "checkpoint_on_close": True,
        },
        "reprocess": {
            "auto_on_session_end": True,
            "lock_file": str(Path(data_dir) / "reprocess.lock"),
            "log_file": str(Path(data_dir) / "reprocess.log"),
            "catchup_on_start": True,
            "full_metrics": True,
        },
        "websocket": {
            "transport": "raw",
            "heartbeat_interval_sec": 10,
            "heartbeat_timeout_sec": 12,
            "backoff_base": 1.5,
            "backoff_mult": 2.0,
            "backoff_max_sec": 60,
        },
        "processor": {
            "mode": "thread",
            "shards": 1,
        },
        "underlyings": [
            {
                "name": "NIFTY", "spot_symbol": "NIFTY", "spot_exchange": "NSE_INDEX",
                "option_exchange": "NFO", "requested_depth": 50,
                "expected_strike_step": [50, 100], "strike_step_fallback": 50,
                "initial_window": 1000, "expansion_threshold": 200, "expansion_step": 300,
                "atm_max_strike_range": 20,
            },
            {
                "name": "SENSEX", "spot_symbol": "SENSEX", "spot_exchange": "BSE_INDEX",
                "option_exchange": "BFO", "requested_depth": 50,
                "expected_strike_step": [100, 200], "strike_step_fallback": 100,
                "initial_window": 3000, "expansion_threshold": 600, "expansion_step": 500,
                "atm_max_strike_range": 30,
            },
        ],
    }


@pytest.fixture
def base_config(tmp_path) -> dict[str, Any]:
    """A fresh, valid config dict with data paths under ``tmp_path``. Deep-copy before mutating."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return copy.deepcopy(_good_config(str(data_dir)))


@pytest.fixture
def write_config(tmp_path) -> Callable[[dict[str, Any]], str]:
    """Return a helper that dumps a config dict to a YAML file under ``tmp_path`` and returns its path."""
    def _write(cfg: dict[str, Any], name: str = "config.yaml") -> str:
        path = tmp_path / name
        path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
        return str(path)
    return _write
