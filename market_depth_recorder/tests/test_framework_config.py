"""F1 tests for the framework configuration schema and its fail-fast contract (Plan_002 §17).

Covers the shape of a valid block, one negative case per rule, the error-collection behaviour, and the
exit-1 contract both in-process and through a real subprocess.
"""

from __future__ import annotations

import copy
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

from market_depth_recorder.market_depth_framework import (
    UNLIMITED_BUDGET,
    FRAMEWORK_SECTION,
    FrameworkConfigError,
    load_framework_config,
    validate_framework_config,
)
from market_depth_recorder.market_depth_framework.__main__ import (
    EXIT_OK,
    EXIT_VALIDATION,
    main,
)

# Repo root that must be on PYTHONPATH for ``market_depth_recorder`` to import.
SS_PROJECTS = Path(__file__).resolve().parents[2]


def good_block() -> dict[str, Any]:
    """The §17 configuration surface, with the FROZEN FYERS capability facts."""
    return {
        "enabled": False,
        "broker": "fyers",
        "broker_capabilities": {
            "fyers": {
                "premium": {"depth": 50, "symbols_per_connection": 5,
                            "max_connections": 3, "max_channels": 50},
                "standard": {"depth": 5},
                "premium_exchanges": ["NSE", "NFO"],
            }
        },
        "window_manager": {},
        "priority_policy": {"policy": "atm_distance"},
        "budget_allocator": {
            "policy": "weighted",
            "min_per_underlying": 2,
            "weights": {"NIFTY": 2.0, "SENSEX": 1.0},
            "redistribute_unspent": True,
        },
        "depth_allocator": {
            "churn_cooldown_seconds": 30,
            "hysteresis_buffer": 2,
            "history_limit": 200,
        },
        "rebalance": {"trigger": "both", "interval_seconds": 5},
    }


def good_root() -> dict[str, Any]:
    return {FRAMEWORK_SECTION: good_block()}


def mutated(path: list[str], value: Any) -> dict[str, Any]:
    """Deep-copy the good root and set one nested key, so each negative test isolates one rule."""
    root = copy.deepcopy(good_root())
    node = root[FRAMEWORK_SECTION]
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value
    return root


def dropped(path: list[str]) -> dict[str, Any]:
    root = copy.deepcopy(good_root())
    node = root[FRAMEWORK_SECTION]
    for key in path[:-1]:
        node = node[key]
    del node[path[-1]]
    return root


def errors_of(root: dict[str, Any]) -> list[str]:
    with pytest.raises(FrameworkConfigError) as excinfo:
        validate_framework_config(root)
    return excinfo.value.errors


# ------------------------------------------------------------------------------- happy path ----
def test_good_config_validates_and_is_typed():
    cfg = validate_framework_config(good_root())
    assert cfg is not None
    assert cfg.enabled is False
    cap = cfg.broker_capabilities["fyers"]
    assert cap.premium.depth == 50 and cap.standard.depth == 5
    assert cap.premium_exchanges == frozenset({"NSE", "NFO"})
    assert cap.total_symbol_budget == UNLIMITED_BUDGET
    assert cfg.rebalance["trigger"] == "both"


def test_absent_section_means_framework_off_not_an_error():
    """F1's actual runtime state: the recorder's shipped config carries no framework block."""
    assert validate_framework_config({"recorder": {}}) is None


def test_optional_total_symbol_budget_is_honoured_when_present():
    cfg = validate_framework_config(
        mutated(["broker_capabilities", "fyers", "total_symbol_budget"], 15)
    )
    assert cfg is not None
    assert cfg.broker_capabilities["fyers"].total_symbol_budget == 15


def test_optional_window_manager_may_be_absent():
    cfg = validate_framework_config(dropped(["window_manager"]))
    assert cfg is not None and dict(cfg.window_manager) == {}


def test_config_object_sections_are_read_only():
    cfg = validate_framework_config(good_root())
    assert cfg is not None
    with pytest.raises(TypeError):
        cfg.rebalance["trigger"] = "interval"  # type: ignore[index]


# --------------------------------------------------------------------- structural / unknown ----
def test_non_mapping_root_is_rejected():
    # ``FrameworkConfigError.__str__`` is a count summary, matching the recorder's ``ConfigError``;
    # the per-error text lives in ``.errors``, which is what the operator report renders.
    with pytest.raises(FrameworkConfigError) as excinfo:
        validate_framework_config(["not", "a", "mapping"])  # type: ignore[arg-type]
    assert any("mapping" in e for e in excinfo.value.errors)


def test_non_mapping_section_is_rejected():
    assert any("must be a mapping" in e for e in errors_of({FRAMEWORK_SECTION: "nope"}))


@pytest.mark.parametrize("section", [
    "broker_capabilities", "priority_policy", "budget_allocator", "depth_allocator", "rebalance",
])
def test_every_required_section_is_required(section):
    assert errors_of(dropped([section]))


def test_unknown_top_level_key_is_rejected():
    """A typo'd key that validation ignores is a silent default by another name."""
    errs = errors_of(mutated(["rebalence"], {}))
    assert any("unknown key" in e and "rebalence" in e for e in errs)


def test_unknown_nested_key_is_rejected():
    errs = errors_of(mutated(["depth_allocator", "cooldown"], 5))
    assert any("unknown key" in e and "cooldown" in e for e in errs)


def test_unknown_capability_key_is_rejected():
    errs = errors_of(mutated(["broker_capabilities", "fyers", "tbt_budget"], 15))
    assert any("unknown key" in e and "tbt_budget" in e for e in errs)


# ------------------------------------------------------------------------- value-level rules ----
@pytest.mark.parametrize("bad", ["yes", 1, None])
def test_enabled_must_be_boolean(bad):
    assert any("enabled" in e for e in errors_of(mutated(["enabled"], bad)))


def test_missing_enabled_is_rejected():
    assert any("enabled" in e for e in errors_of(dropped(["enabled"])))


@pytest.mark.parametrize("bad", ["gamma", "", None, 1])
def test_priority_policy_must_be_a_known_choice(bad):
    assert any("policy" in e for e in errors_of(mutated(["priority_policy", "policy"], bad)))


def test_priority_policy_accepts_both_documented_choices():
    for choice in ("atm_distance", "blended"):
        assert validate_framework_config(mutated(["priority_policy", "policy"], choice)) is not None


@pytest.mark.parametrize("bad", ["round_robin", None, 2])
def test_budget_policy_must_be_a_known_choice(bad):
    assert any("policy" in e for e in errors_of(mutated(["budget_allocator", "policy"], bad)))


@pytest.mark.parametrize("bad", ["hourly", None, True])
def test_rebalance_trigger_must_be_a_known_choice(bad):
    assert any("trigger" in e for e in errors_of(mutated(["rebalance", "trigger"], bad)))


def test_rebalance_trigger_accepts_all_three_choices():
    for choice in ("interval", "window_change", "both"):
        assert validate_framework_config(mutated(["rebalance", "trigger"], choice)) is not None


@pytest.mark.parametrize("bad", [0, -1, "5"])
def test_rebalance_interval_must_be_positive(bad):
    assert any("interval_seconds" in e for e in errors_of(mutated(["rebalance", "interval_seconds"], bad)))


@pytest.mark.parametrize("bad", [-1, 1.5, "2", None, True])
def test_min_per_underlying_must_be_a_non_negative_int(bad):
    errs = errors_of(mutated(["budget_allocator", "min_per_underlying"], bad))
    assert any("min_per_underlying" in e for e in errs)


def test_min_per_underlying_zero_is_allowed():
    """Zero is a legitimate 'no floor' setting; only negatives are out of range."""
    assert validate_framework_config(mutated(["budget_allocator", "min_per_underlying"], 0)) is not None


@pytest.mark.parametrize("bad", [0, -1, "heavy", None, True])
def test_weights_must_be_positive_numbers(bad):
    errs = errors_of(mutated(["budget_allocator", "weights"], {"NIFTY": bad}))
    assert any("weights" in e for e in errs)


def test_weights_must_be_a_mapping():
    assert any("weights" in e for e in errors_of(mutated(["budget_allocator", "weights"], ["NIFTY"])))


@pytest.mark.parametrize("bad", [-1, "30", None, True])
def test_churn_cooldown_must_be_a_non_negative_number(bad):
    errs = errors_of(mutated(["depth_allocator", "churn_cooldown_seconds"], bad))
    assert any("churn_cooldown_seconds" in e for e in errs)


@pytest.mark.parametrize("bad", [-1, 1.5, "2", None])
def test_hysteresis_buffer_must_be_a_non_negative_int(bad):
    errs = errors_of(mutated(["depth_allocator", "hysteresis_buffer"], bad))
    assert any("hysteresis_buffer" in e for e in errs)


@pytest.mark.parametrize("bad", [0, -1, "200", None])
def test_history_limit_must_be_a_positive_int(bad):
    errs = errors_of(mutated(["depth_allocator", "history_limit"], bad))
    assert any("history_limit" in e for e in errs)


# --------------------------------------------------------------------- capability sub-schema ----
def test_broker_capabilities_must_be_a_non_empty_mapping():
    assert any("broker_capabilities" in e for e in errors_of(mutated(["broker_capabilities"], {})))
    assert any("broker_capabilities" in e for e in errors_of(mutated(["broker_capabilities"], [])))


@pytest.mark.parametrize("key", ["depth", "symbols_per_connection", "max_connections", "max_channels"])
def test_every_premium_tier_key_is_required(key):
    errs = errors_of(dropped(["broker_capabilities", "fyers", "premium", key]))
    assert any(key in e for e in errs)


@pytest.mark.parametrize("bad", [0, -1, 1.5, "5", True])
def test_premium_tier_values_must_be_positive_ints(bad):
    errs = errors_of(mutated(["broker_capabilities", "fyers", "premium", "symbols_per_connection"], bad))
    assert any("symbols_per_connection" in e for e in errs)


def test_premium_depth_must_exceed_standard_depth():
    """Cross-field invariant surfaces as a validation error, not an escaping ValueError."""
    errs = errors_of(mutated(["broker_capabilities", "fyers", "standard"], {"depth": 50}))
    assert any("must be >" in e for e in errs)


@pytest.mark.parametrize("bad", [[], "NFO", None, [""], [1]])
def test_premium_exchanges_must_be_a_non_empty_string_list(bad):
    errs = errors_of(mutated(["broker_capabilities", "fyers", "premium_exchanges"], bad))
    assert any("premium_exchanges" in e for e in errs)


def test_capability_for_a_broker_with_no_premium_exchange_shape_is_still_typed():
    """A broker whose premium tier is 20 rather than 50 needs no code change -- only config."""
    root = mutated(["broker_capabilities", "other"], {
        "premium": {"depth": 20, "symbols_per_connection": 10,
                    "max_connections": 1, "max_channels": 1},
        "standard": {"depth": 5},
        "premium_exchanges": ["XYZ"],
        "total_symbol_budget": 10,
    })
    cfg = validate_framework_config(root)
    assert cfg is not None
    assert cfg.broker_capabilities["other"].premium.depth == 20
    assert cfg.broker_capabilities["other"].total_symbol_budget == 10


# ------------------------------------------------------------------- error-collection contract ----
def test_validation_collects_every_error_in_one_pass():
    """The operator must see all problems at once, matching the recorder's §7.3 rule 3."""
    root = copy.deepcopy(good_root())
    block = root[FRAMEWORK_SECTION]
    block["enabled"] = "yes"
    block["priority_policy"]["policy"] = "gamma"
    block["rebalance"]["trigger"] = "hourly"
    block["depth_allocator"]["history_limit"] = 0
    errs = errors_of(root)
    assert len(errs) >= 4
    joined = " | ".join(errs)
    for token in ("enabled", "policy", "trigger", "history_limit"):
        assert token in joined


def test_error_report_lists_every_error():
    with pytest.raises(FrameworkConfigError) as excinfo:
        validate_framework_config(mutated(["enabled"], "yes"))
    report = excinfo.value.report()
    assert report.startswith("FRAMEWORK CONFIG VALIDATION FAILED:")
    assert all(err in report for err in excinfo.value.errors)


# ----------------------------------------------------------------------------- file loading ----
def write_yaml(tmp_path: Path, payload: Any, name: str = "config.yaml") -> Path:
    path = tmp_path / name
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    return path


def test_load_framework_config_reads_a_valid_file(tmp_path):
    cfg = load_framework_config(str(write_yaml(tmp_path, good_root())))
    assert cfg is not None and cfg.broker_capabilities["fyers"].premium.depth == 50


def test_load_framework_config_returns_none_for_a_file_without_the_section(tmp_path):
    assert load_framework_config(str(write_yaml(tmp_path, {"recorder": {"log_level": "INFO"}}))) is None


def test_load_framework_config_rejects_a_missing_file(tmp_path):
    with pytest.raises(FrameworkConfigError) as excinfo:
        load_framework_config(str(tmp_path / "absent.yaml"))
    assert any("not found" in e for e in excinfo.value.errors)


def test_load_framework_config_rejects_malformed_yaml(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text("market_depth_framework: [unclosed\n", encoding="utf-8")
    with pytest.raises(FrameworkConfigError) as excinfo:
        load_framework_config(str(path))
    assert any("YAML" in e for e in excinfo.value.errors)


def test_load_framework_config_rejects_a_non_mapping_root(tmp_path):
    with pytest.raises(FrameworkConfigError) as excinfo:
        load_framework_config(str(write_yaml(tmp_path, ["a", "b"])))
    assert any("mapping" in e for e in excinfo.value.errors)


# ------------------------------------------------------------------ fail-fast / exit-1 contract ----
def test_main_exits_zero_for_a_valid_block(tmp_path, capsys):
    code = main(["--config", str(write_yaml(tmp_path, good_root()))])
    assert code == EXIT_OK
    assert "FRAMEWORK CONFIG OK" in capsys.readouterr().out


def test_main_exits_zero_when_the_section_is_absent(tmp_path, capsys):
    code = main(["--config", str(write_yaml(tmp_path, {"recorder": {}}))])
    assert code == EXIT_OK
    assert "framework off" in capsys.readouterr().out


def test_main_exits_one_for_an_invalid_block(tmp_path, capsys):
    path = write_yaml(tmp_path, mutated(["rebalance", "trigger"], "hourly"))
    code = main(["--config", str(path)])
    assert code == EXIT_VALIDATION
    assert "FRAMEWORK CONFIG VALIDATION FAILED" in capsys.readouterr().err


def test_main_exits_one_for_a_missing_file(tmp_path):
    assert main(["--config", str(tmp_path / "absent.yaml")]) == EXIT_VALIDATION


def run_module(config_path: Path) -> subprocess.CompletedProcess:
    """Invoke the package entrypoint as a real subprocess, so the exit code is the process's own."""
    return subprocess.run(
        [sys.executable, "-m", "market_depth_recorder.market_depth_framework",
         "--config", str(config_path)],
        cwd=str(SS_PROJECTS), capture_output=True, text=True, timeout=120,
    )


def test_subprocess_exits_one_on_invalid_config(tmp_path):
    """The contract operators actually rely on: a real non-zero process exit."""
    result = run_module(write_yaml(tmp_path, mutated(["enabled"], "yes")))
    assert result.returncode == 1
    assert "FRAMEWORK CONFIG VALIDATION FAILED" in result.stderr


def test_subprocess_exits_zero_on_valid_config(tmp_path):
    result = run_module(write_yaml(tmp_path, good_root()))
    assert result.returncode == 0
    assert "FRAMEWORK CONFIG OK" in result.stdout


# ------------------------------------------------------------------ F1 boundary (scope guard) ----
def test_f1_does_not_run_the_feasibility_check():
    """§13.2's ``min_per_underlying * len(eligible) <= effective_budget`` needs the F2 capability
    layer. A floor of 1000 is structurally valid and must pass F1 untouched."""
    assert validate_framework_config(
        mutated(["budget_allocator", "min_per_underlying"], 1000)
    ) is not None


def test_no_premium_eligible_key_exists_in_allocator_config():
    """Plan_002 §17: eligibility is a broker fact, so putting it in allocator config would let it
    drift from the broker."""
    errs = errors_of(mutated(["budget_allocator", "premium_eligible"], ["NIFTY"]))
    assert any("unknown key" in e and "premium_eligible" in e for e in errs)


def test_no_premium_budget_key_exists_in_allocator_config():
    """§13: the budget is a capability, never a number hand-copied into config."""
    errs = errors_of(mutated(["budget_allocator", "premium_budget"], 15))
    assert any("unknown key" in e and "premium_budget" in e for e in errs)


# ------------------------------------------------------------------------ active broker (§10.9) ----
def test_broker_defaults_to_the_only_configured_capability():
    """With a single broker there is nothing to choose, so the key stays optional."""
    root = copy.deepcopy(good_root())
    del root[FRAMEWORK_SECTION]["broker"]
    cfg = validate_framework_config(root)
    assert cfg is not None
    assert cfg.broker == "fyers"


def test_broker_is_required_once_a_second_capability_is_configured():
    """An unstated choice between two brokers is the operator's to make, never this module's to guess."""
    root = mutated(["broker_capabilities", "other"], copy.deepcopy(good_block()["broker_capabilities"]["fyers"]))
    del root[FRAMEWORK_SECTION]["broker"]
    with pytest.raises(FrameworkConfigError) as exc:
        validate_framework_config(root)
    assert any("broker" in e and "more than one" in e for e in exc.value.errors)


def test_broker_must_name_a_configured_capability():
    root = mutated(["broker"], "nosuchbroker")
    with pytest.raises(FrameworkConfigError) as exc:
        validate_framework_config(root)
    assert any("no entry under broker_capabilities" in e for e in exc.value.errors)


def test_broker_must_be_a_non_empty_string():
    root = mutated(["broker"], "")
    with pytest.raises(FrameworkConfigError) as exc:
        validate_framework_config(root)
    assert any("must be a non-empty string" in e for e in exc.value.errors)
