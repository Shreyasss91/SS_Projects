"""Config loader + validation tests (§7.3). All run without a live feed.

One happy-path test, one negative test per §7.3 rule (asserting the specific field in the message),
the ``--validate-config`` exit codes, config_hash determinism, and live_metrics membership.
"""

from __future__ import annotations

import copy

import pytest

from market_depth_recorder.__main__ import main
from market_depth_recorder.config import ConfigError, compute_config_hash, load_config
from market_depth_recorder.tests.conftest import PACKAGE_ROOT, _good_config


# --------------------------------------------------------------------------------------------------
# I2 — happy path
# --------------------------------------------------------------------------------------------------
def test_happy_path_loads(base_config, write_config):
    cfg = load_config(write_config(base_config))
    assert [u.name for u in cfg.underlyings] == ["NIFTY", "SENSEX"]
    assert cfg.websocket["transport"] == "raw"
    assert cfg.config_hash.startswith("sha256:")
    # Frozen typed object, not a raw dict.
    with pytest.raises(Exception):
        cfg.underlyings[0].name = "X"  # type: ignore[misc]


def test_shipped_config_valid(tmp_path, monkeypatch):
    """The shipped config.yaml (§7.1) passes validation. chdir to tmp so its ``./data`` write-probe
    lands in a throwaway dir, not the working tree."""
    monkeypatch.chdir(tmp_path)
    cfg = load_config(str(PACKAGE_ROOT / "config.yaml"))
    assert cfg.config_hash.startswith("sha256:")
    assert len(cfg.underlyings) == 2


# --------------------------------------------------------------------------------------------------
# I3 — one negative per §7.3 rule (field asserted in the message)
# --------------------------------------------------------------------------------------------------
def _mutate(base, path, value):
    cfg = copy.deepcopy(base)
    node = cfg
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value
    return cfg


NEGATIVE_CASES = [
    # (mutation path, bad value, substring expected in an error message)
    (("recorder", "session_start"), "16:00", "session_start must be < session_end"),
    (("database", "batch_write_interval_ms"), 100, "batch_write_interval_ms"),
    (("analytics_db", "memory_limit_mb"), 128, "memory_limit_mb"),
    (("analytics_db", "threads"), 128, "threads"),
    (("websocket", "transport"), "grpc", "transport"),
    (("processor", "mode"), "coroutine", "processor.mode"),
    (("queues", "warn_watermark_pct"), 95, "warn_watermark_pct"),
    (("queues", "raw_file_queue_max"), 100, "raw_file_queue_max"),
    (("metrics", "time_windows_sec"), [], "time_windows_sec"),
    (("metrics", "round_number_multiples"), [5, -3], "round_number_multiples"),
    (("recorder", "min_free_disk_mb"), -1, "min_free_disk_mb"),
    (("recorder", "disk_check_interval_sec"), 1, "disk_check_interval_sec"),
    (("recorder", "skip_non_trading_days"), "yes", "skip_non_trading_days"),
    (("openalgo", "host_server"), "ftp://x", "host_server"),
    (("openalgo", "websocket_url"), "http://x", "websocket_url"),
    (("recorder", "live_metrics"), ["spread", "bogus_metric"], "unknown metric"),
]


@pytest.mark.parametrize("path,value,expected", NEGATIVE_CASES,
                         ids=[c[0][-1] for c in NEGATIVE_CASES])
def test_negative_rule(base_config, write_config, path, value, expected):
    bad = _mutate(base_config, path, value)
    with pytest.raises(ConfigError) as exc:
        load_config(write_config(bad))
    joined = "\n".join(exc.value.errors)
    assert expected in joined, f"expected {expected!r} in errors:\n{joined}"


def test_process_mode_requires_shards(base_config, write_config):
    bad = copy.deepcopy(base_config)
    bad["processor"]["mode"] = "process"
    bad["processor"]["shards"] = 0
    with pytest.raises(ConfigError) as exc:
        load_config(write_config(bad))
    assert any("shards" in e for e in exc.value.errors)


def test_holiday_parse_only_when_skip_enabled(base_config, write_config):
    # skip=False → a malformed holiday is tolerated (not enforced, §3.1.5).
    ok = copy.deepcopy(base_config)
    ok["recorder"]["trading_holidays"] = ["not-a-date"]
    load_config(write_config(ok))  # no raise
    # skip=True → the same malformed holiday now fails.
    bad = copy.deepcopy(ok)
    bad["recorder"]["skip_non_trading_days"] = True
    with pytest.raises(ConfigError) as exc:
        load_config(write_config(bad))
    assert any("trading_holidays" in e for e in exc.value.errors)


def test_bad_yaml(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text("openalgo: [unclosed\n", encoding="utf-8")
    with pytest.raises(ConfigError) as exc:
        load_config(str(p))
    assert any("well-formed YAML" in e for e in exc.value.errors)


def test_output_dir_not_writable(base_config, write_config, tmp_path):
    blocker = tmp_path / "blocker_file"
    blocker.write_text("x", encoding="utf-8")
    bad = copy.deepcopy(base_config)
    bad["recorder"]["output_dir"] = str(blocker / "data")  # parent is a regular file
    with pytest.raises(ConfigError) as exc:
        load_config(write_config(bad))
    assert any("output_dir" in e for e in exc.value.errors)


# --------------------------------------------------------------------------------------------------
# Per-underlying rules
# --------------------------------------------------------------------------------------------------
def test_expansion_threshold_ge_initial_window(base_config, write_config):
    bad = copy.deepcopy(base_config)
    bad["underlyings"][0]["expansion_threshold"] = 5000  # > initial_window 1000
    with pytest.raises(ConfigError) as exc:
        load_config(write_config(bad))
    assert any("expansion_threshold" in e for e in exc.value.errors)


def test_duplicate_underlying_name(base_config, write_config):
    bad = copy.deepcopy(base_config)
    bad["underlyings"][1]["name"] = "NIFTY"
    with pytest.raises(ConfigError) as exc:
        load_config(write_config(bad))
    assert any("duplicate underlying name" in e for e in exc.value.errors)


def test_strike_step_fallback_membership(base_config, write_config):
    bad = copy.deepcopy(base_config)
    bad["underlyings"][0]["strike_step_fallback"] = 25  # not in [50, 100]
    with pytest.raises(ConfigError) as exc:
        load_config(write_config(bad))
    assert any("strike_step_fallback" in e for e in exc.value.errors)


def test_collects_all_errors(base_config, write_config):
    """Rule 3 collects ALL failures, not just the first."""
    bad = copy.deepcopy(base_config)
    bad["websocket"]["transport"] = "grpc"
    bad["analytics_db"]["threads"] = 128
    with pytest.raises(ConfigError) as exc:
        load_config(write_config(bad))
    assert len(exc.value.errors) >= 2


# --------------------------------------------------------------------------------------------------
# I4 — --validate-config exit codes
# --------------------------------------------------------------------------------------------------
def test_validate_config_exit_ok(base_config, write_config, capsys):
    rc = main(["--validate-config", "--config", write_config(base_config)])
    assert rc == 0
    assert "CONFIG OK" in capsys.readouterr().out


def test_validate_config_exit_fail(base_config, write_config, capsys):
    bad = copy.deepcopy(base_config)
    bad["websocket"]["transport"] = "grpc"
    rc = main(["--validate-config", "--config", write_config(bad)])
    assert rc == 1
    assert "VALIDATION FAILED" in capsys.readouterr().err


# --------------------------------------------------------------------------------------------------
# I5 — config_hash determinism
# --------------------------------------------------------------------------------------------------
def test_config_hash_deterministic():
    a = _good_config("./data")
    b = copy.deepcopy(a)
    assert compute_config_hash(a) == compute_config_hash(b)


def test_config_hash_changes_on_constant():
    a = _good_config("./data")
    b = copy.deepcopy(a)
    b["metrics"]["decay_k"] = 0.3
    assert compute_config_hash(a) != compute_config_hash(b)


def test_config_hash_ignores_non_formula_sections():
    """Only metrics/regime/underlyings feed the hash — changing e.g. a queue size must NOT flip it."""
    a = _good_config("./data")
    b = copy.deepcopy(a)
    b["queues"]["max_queue_size"] = 12345
    assert compute_config_hash(a) == compute_config_hash(b)


# --------------------------------------------------------------------------------------------------
# I6 — live_metrics membership
# --------------------------------------------------------------------------------------------------
def test_live_metrics_all_passes(base_config, write_config):
    cfg = copy.deepcopy(base_config)
    cfg["recorder"]["live_metrics"] = "all"
    load_config(write_config(cfg))  # no raise


def test_live_metrics_full_m_series_pass(base_config, write_config):
    """Every M1–M29 registry name is an accepted live_metrics token."""
    from market_depth_recorder.metrics import registry
    m_names = [s.name for s in registry.REGISTRY.values() if s.m_number is not None]
    assert len(m_names) == 29
    cfg = copy.deepcopy(base_config)
    cfg["recorder"]["live_metrics"] = m_names
    load_config(write_config(cfg))  # no raise
