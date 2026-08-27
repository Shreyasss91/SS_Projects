"""F10A tests for the live-session watcher (`tools/validation/f10_live_monitor.py`, Plan_002 §22.13).

Entirely offline: synthetic `health.json` snapshots, no recorder process, no broker, no socket, no
market. Nothing here is a statement about a live session -- what it asserts is that the abort rules
fire on exactly the conditions the runbook says they do, and stay silent otherwise, so that tomorrow
the operator can trust the verdict rather than re-deriving it under time pressure.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parent.parent / "tools" / "validation"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import f10_live_monitor as M  # noqa: E402


# --------------------------------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------------------------------
def health(**over) -> dict:
    """A healthy snapshot in the shape `main.py` actually writes, overridable field by field."""
    base = {
        "state": "RECORD", "config_hash": "sha256:test", "websocket_status": "connected",
        "raw_file_queue_size": 12, "proc_queue_size": 30, "db_queue_size": 5,
        "raw_dropped_total": 0, "proc_dropped_total": 0, "db_rows_dropped_total": 0,
        "degraded_level": 0, "cycle_ms_p50": 22.0, "cycle_ms_max": 45.0, "rss_mb": 58.0,
        "active_contracts": 200, "actual_depth": {"NIFTY": 50, "SENSEX": 5}, "restart_count": 0,
        "framework": {"passes": 10},
        "framework_feed": {"plans_executed": 10, "plan_failures": 0, "desired_legs": 200,
                           "premium_legs": 15, "effective_budget": 15, "delivering_legs": 195,
                           "claimed_wire_symbols": 200},
    }
    base.update(over)
    return base


@pytest.fixture
def cfg_path(tmp_path) -> str:
    p = tmp_path / "config.yaml"
    p.write_text(
        "queues:\n  max_queue_size: 50000\n  raw_file_queue_max: 100000\n"
        "  warn_watermark_pct: 70\n  critical_watermark_pct: 90\n",
        encoding="utf-8",
    )
    return str(p)


@pytest.fixture
def thresholds(cfg_path) -> dict:
    return M.thresholds_from(cfg_path)


def s(snapshot: dict, *, at: float = 100.0) -> dict:
    return M.sample(snapshot, at=at)


def codes(conditions) -> set[str]:
    return {c["code"] for c in conditions}


# --------------------------------------------------------------------------------------------------
# 1. Thresholds are derived, never assumed
# --------------------------------------------------------------------------------------------------
def test_queue_thresholds_come_from_the_config_not_from_constants(thresholds):
    assert thresholds["proc_warn"] == pytest.approx(35000.0)
    assert thresholds["proc_crit"] == pytest.approx(45000.0)
    assert thresholds["raw_warn"] == pytest.approx(70000.0)
    assert thresholds["raw_crit"] == pytest.approx(90000.0)


def test_raising_the_queue_cap_raises_the_thresholds_with_it(tmp_path):
    p = tmp_path / "big.yaml"
    p.write_text("queues:\n  max_queue_size: 200000\n  raw_file_queue_max: 400000\n"
                 "  warn_watermark_pct: 70\n  critical_watermark_pct: 90\n", encoding="utf-8")
    assert M.thresholds_from(str(p))["proc_crit"] == pytest.approx(180000.0)


def test_an_incomplete_queue_block_is_an_error_not_a_default(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text("queues:\n  max_queue_size: 50000\n", encoding="utf-8")
    with pytest.raises(ValueError):
        M.thresholds_from(str(p))


def test_the_documented_soft_thresholds_match_the_projects_existing_figures():
    """These two are eod_report's own targets; the tool must not quietly hold a different opinion."""
    from market_depth_recorder import eod_report

    assert M.CYCLE_MS_SOFT == eod_report._CYCLE_MS_TARGET
    assert M.RSS_MB_SOFT == eod_report._RSS_MB_TARGET


# --------------------------------------------------------------------------------------------------
# 2. A healthy session raises nothing
# --------------------------------------------------------------------------------------------------
def test_a_healthy_snapshot_raises_no_condition_at_all(thresholds):
    assert M.classify(s(health()), None, thresholds) == []


def test_p10e_style_numbers_are_healthy(thresholds):
    """22 ms p50 / 58 MB was P10-E's measured normal. The watcher must not call the baseline sick."""
    assert M.classify(s(health(cycle_ms_p50=22.0, cycle_ms_max=60.0, rss_mb=58.0)), None,
                      thresholds) == []


def test_a_flag_off_health_file_is_watchable_and_quiet(thresholds):
    snapshot = health()
    del snapshot["framework"]
    del snapshot["framework_feed"]
    flat = s(snapshot)
    assert flat["framework_present"] is False
    assert flat["premium_legs"] is None
    assert M.classify(flat, None, thresholds) == []


# --------------------------------------------------------------------------------------------------
# 3. The instant aborts
# --------------------------------------------------------------------------------------------------
def test_one_lost_raw_packet_is_an_instant_abort(thresholds):
    w = M.Watch(sustain=3)
    aborts = w.observe(s(health(raw_dropped_total=1)), thresholds)
    assert codes(aborts) == {"raw_loss"}


def test_premium_above_the_budget_is_an_instant_abort(thresholds):
    w = M.Watch(sustain=3)
    snapshot = health()
    snapshot["framework_feed"]["premium_legs"] = 16
    assert "budget_exceeded" in codes(w.observe(s(snapshot), thresholds))


def test_premium_exactly_at_the_budget_is_not_an_abort(thresholds):
    """Running at 15 of 15 is the point of the run, not a fault."""
    assert M.classify(s(health()), None, thresholds) == []


# --------------------------------------------------------------------------------------------------
# 4. The sustain rule
# --------------------------------------------------------------------------------------------------
def test_a_single_slow_cycle_does_not_abort_the_session(thresholds):
    w = M.Watch(sustain=3)
    assert w.observe(s(health(cycle_ms_p50=600.0), at=1.0), thresholds) == []


def test_a_slow_cycle_that_persists_does_abort(thresholds):
    w = M.Watch(sustain=3)
    out = [w.observe(s(health(cycle_ms_p50=600.0), at=float(i)), thresholds) for i in range(3)]
    assert out[0] == [] and out[1] == []
    assert codes(out[2]) == {"cycle_ms_hard"}
    assert out[2][0]["streak"] == 3


def test_recovery_resets_the_streak(thresholds):
    w = M.Watch(sustain=3)
    w.observe(s(health(cycle_ms_p50=600.0), at=1.0), thresholds)
    w.observe(s(health(cycle_ms_p50=600.0), at=2.0), thresholds)
    w.observe(s(health(cycle_ms_p50=22.0), at=3.0), thresholds)      # recovered
    w.observe(s(health(cycle_ms_p50=600.0), at=4.0), thresholds)
    assert w.observe(s(health(cycle_ms_p50=600.0), at=5.0), thresholds) == []


def test_sustain_must_be_at_least_one():
    with pytest.raises(ValueError):
        M.Watch(sustain=0)


# --------------------------------------------------------------------------------------------------
# 5. Queues, degradation, memory
# --------------------------------------------------------------------------------------------------
def test_the_warn_watermark_is_soft_and_the_critical_one_is_hard(thresholds):
    assert codes(M.classify(s(health(proc_queue_size=36000)), None, thresholds)) == {"proc_queue_size_warn"}
    assert codes(M.classify(s(health(proc_queue_size=46000)), None, thresholds)) == {
        "proc_queue_size_critical"}


def test_the_raw_queue_has_its_own_larger_thresholds(thresholds):
    """raw_file_queue_max is 2x max_queue_size, and the protected path must not trip at the smaller one."""
    assert M.classify(s(health(raw_file_queue_size=50000)), None, thresholds) == []
    assert codes(M.classify(s(health(raw_file_queue_size=95000)), None, thresholds)) == {
        "raw_file_queue_size_critical"}


def test_degraded_level_one_warns_and_two_is_hard(thresholds):
    assert codes(M.classify(s(health(degraded_level=1)), None, thresholds)) == {"degraded_warn"}
    assert "degraded_critical" in codes(M.classify(s(health(degraded_level=2)), None, thresholds))


def test_memory_warns_at_the_eod_target_and_aborts_at_the_host_ceiling(thresholds):
    assert codes(M.classify(s(health(rss_mb=520.0)), None, thresholds)) == {"rss_soft"}
    assert "rss_hard" in codes(M.classify(s(health(rss_mb=3000.0)), None, thresholds))


# --------------------------------------------------------------------------------------------------
# 6. Deltas need a previous sample
# --------------------------------------------------------------------------------------------------
def test_growing_plan_failures_are_a_refusal_storm(thresholds):
    before = s(health(), at=1.0)
    after = health()
    after["framework_feed"]["plan_failures"] = 3
    assert "plan_failures_growing" in codes(M.classify(s(after, at=2.0), before, thresholds))


def test_a_flat_nonzero_failure_count_is_not_a_storm(thresholds):
    """Three failures at 09:20 that never grow are history, not an emergency."""
    snapshot = health()
    snapshot["framework_feed"]["plan_failures"] = 3
    before, after = s(snapshot, at=1.0), s(snapshot, at=2.0)
    assert M.classify(after, before, thresholds) == []


def test_db_drops_are_hard_and_proc_drops_are_soft(thresholds):
    """The shed order is proc, then db, then raw -- so proc shedding is the design working."""
    before = s(health(), at=1.0)
    assert "db_drops_growing" in codes(
        M.classify(s(health(db_rows_dropped_total=5), at=2.0), before, thresholds))
    got = codes(M.classify(s(health(proc_dropped_total=5), at=2.0), before, thresholds))
    assert got == {"proc_drops_growing"}


def test_a_reconnect_is_recorded_and_never_aborts(thresholds):
    """F23 = A: natural reconnects are observed, not acted on."""
    before = s(health(), at=1.0)
    after = s(health(websocket_status="reconnecting", restart_count=0), at=2.0)
    conditions = M.classify(after, before, thresholds)
    assert codes(conditions) == {"ws_not_connected"}
    assert all(c["level"] == M.SOFT for c in conditions)


def test_a_restart_is_soft(thresholds):
    before = s(health(), at=1.0)
    assert "restart" in codes(M.classify(s(health(restart_count=1), at=2.0), before, thresholds))


def test_the_framework_disappearing_from_health_is_hard(thresholds):
    """With the flag on, the block's absence means the framework is no longer running."""
    before = s(health(), at=1.0)
    gone = health()
    del gone["framework"]
    del gone["framework_feed"]
    assert "framework_vanished" in codes(M.classify(s(gone, at=2.0), before, thresholds))


# --------------------------------------------------------------------------------------------------
# 7. The CLI
# --------------------------------------------------------------------------------------------------
def test_once_writes_a_timeline_and_exits_clean(tmp_path, cfg_path, capsys):
    hp = tmp_path / "health.json"
    hp.write_text(json.dumps(health()), encoding="utf-8")
    out = tmp_path / "timeline.jsonl"
    rc = M.main([str(hp), "-c", cfg_path, "-o", str(out), "--once"])
    assert rc == 0
    samples, _, meta = M._load_timeline(str(out))
    assert len(samples) == 1 and samples[0]["premium_legs"] == 15
    assert meta["started"] and meta["ended"] and meta["aborted"] is False


def test_a_hard_condition_makes_the_cli_exit_one_without_touching_the_recorder(tmp_path, cfg_path):
    hp = tmp_path / "health.json"
    hp.write_text(json.dumps(health(raw_dropped_total=2)), encoding="utf-8")
    out = tmp_path / "timeline.jsonl"
    before = hp.read_bytes()
    assert M.main([str(hp), "-c", cfg_path, "-o", str(out), "--once"]) == 1
    assert hp.read_bytes() == before, "the watcher must never write to the recorder's health file"


def test_a_missing_health_file_is_exit_two_and_writes_nothing(tmp_path, cfg_path):
    out = tmp_path / "timeline.jsonl"
    assert M.main([str(tmp_path / "nope.json"), "-c", cfg_path, "-o", str(out), "--once"]) == 2
    assert not out.exists()


def test_the_config_is_required_because_thresholds_are_never_assumed(tmp_path):
    hp = tmp_path / "health.json"
    hp.write_text(json.dumps(health()), encoding="utf-8")
    assert M.main([str(hp), "--once"]) == 2


def test_the_timeline_is_appended_across_watches_not_truncated(tmp_path, cfg_path):
    hp = tmp_path / "health.json"
    hp.write_text(json.dumps(health()), encoding="utf-8")
    out = tmp_path / "timeline.jsonl"
    M.main([str(hp), "-c", cfg_path, "-o", str(out), "--once"])
    M.main([str(hp), "-c", cfg_path, "-o", str(out), "--once"])
    samples, _, _ = M._load_timeline(str(out))
    assert len(samples) == 2


# --------------------------------------------------------------------------------------------------
# 8. Evidence rendering (fork F26)
# --------------------------------------------------------------------------------------------------
def test_the_evidence_skeleton_reports_observed_numbers_and_leaves_judgement_blank(tmp_path, cfg_path):
    hp = tmp_path / "health.json"
    out = tmp_path / "timeline.jsonl"
    for i, cyc in enumerate((20.0, 26.0, 24.0)):
        hp.write_text(json.dumps(health(cycle_ms_p50=cyc, rss_mb=60.0 + i)), encoding="utf-8")
        M.main([str(hp), "-c", cfg_path, "-o", str(out), "--once"])
    text = M.render_evidence(*M._load_timeline(str(out))[:2], meta={"session_date": "2026-08-28"})
    assert "20.0 .. 26.0 ms" in text
    assert "60 .. 62 MB" in text
    for heading in ("## OBSERVED", "## INFERRED", "## UNKNOWN", "## D18 conclusion"):
        assert heading in text
    assert text.count("FILL IN") >= 3, "judgement sections must stay unwritten"


def test_the_unknowns_are_restated_in_every_rendered_evidence_document(tmp_path, cfg_path):
    hp = tmp_path / "health.json"
    out = tmp_path / "timeline.jsonl"
    hp.write_text(json.dumps(health()), encoding="utf-8")
    M.main([str(hp), "-c", cfg_path, "-o", str(out), "--once"])
    text = M.render_evidence(*M._load_timeline(str(out))[:2], meta={})
    assert "Reconnect depth restoration" in text and "UNKNOWN" in text
    assert "true premium ceiling" in text
    assert "does not establish that the broker would accept more" in text


def test_rendering_an_empty_timeline_claims_nothing():
    assert "nothing is claimed" in M.render_evidence([], [], meta={})


def test_render_from_the_cli_writes_the_file(tmp_path, cfg_path):
    hp = tmp_path / "health.json"
    out = tmp_path / "timeline.jsonl"
    hp.write_text(json.dumps(health()), encoding="utf-8")
    M.main([str(hp), "-c", cfg_path, "-o", str(out), "--once"])
    ev = tmp_path / "evidence.md"
    assert M.main(["--render", str(out), "--evidence-out", str(ev)]) == 0
    assert "## OBSERVED" in ev.read_text(encoding="utf-8")


def test_rendering_a_missing_timeline_is_exit_two(tmp_path):
    assert M.main(["--render", str(tmp_path / "nope.jsonl")]) == 2


# --------------------------------------------------------------------------------------------------
# 9. The tool observes and nothing else
# --------------------------------------------------------------------------------------------------
def test_the_monitor_imports_no_recorder_runtime_module():
    """It must not be able to touch the thing it is watching."""
    import ast

    tree = ast.parse(Path(M.__file__).read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    forbidden = {"market_depth_recorder", "websocket_client", "processor", "main",
                 "framework_bridge", "sqlite3", "duckdb", "socket", "subprocess", "threading"}
    assert not (imported & forbidden), f"monitor imports {imported & forbidden}"


def test_the_monitor_never_stops_the_recorder_itself():
    """No kill path in the tool: aborting is the operator's action, by design (runbook D)."""
    source = Path(M.__file__).read_text(encoding="utf-8")
    for forbidden in ("os.kill", "SIGTERM", "SIGINT", "terminate(", "taskkill"):
        assert forbidden not in source, f"monitor must not contain {forbidden}"
