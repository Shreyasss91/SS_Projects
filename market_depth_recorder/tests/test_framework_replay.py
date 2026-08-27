"""F9 determinism harness tests (`framework_replay.py`, Plan_002 §22.12).

Every test here is offline: a hand-built synthetic raw `.jsonl.gz`, the **real** orchestrator and the
**real** `BrokerAdapter`, and a transport that is a list. Nothing in this file touches a broker, a
socket, a market, or any file under `data/` — so nothing it asserts is a statement about a broker.
What it does assert is the F9 deliverable: the framework's allocation behaviour is a deterministic
function of the tick stream, and it stays inside its own invariants across a whole session.

The matrix mirrors §22.12.6 case for case.
"""

from __future__ import annotations

import copy
import gzip
import json
import os
import subprocess
import sys
import threading
from datetime import date

import pytest

from market_depth_recorder import framework_replay as FR
from market_depth_recorder.config import load_config
from market_depth_recorder.market_depth_framework.orchestrator import (
    TRIGGER_INITIAL,
    TRIGGER_INTERVAL,
    TRIGGER_WINDOW_CHANGE,
)

from .test_framework_integration import framework_block

SESSION_DATE = date(2026, 7, 6)
T0 = 1_781_060_400  # fixed integer epoch; packets land at T0 + sec + 0.5

NIFTY_STEP = 50
NIFTY_STRIKES = [23000 + NIFTY_STEP * i for i in range(41)]  # 23000..25000
SENSEX_STEP = 100
SENSEX_STRIKES = [77000 + SENSEX_STEP * i for i in range(41)]  # 77000..81000
EXPIRY = "09-JUL-26"


# --------------------------------------------------------------------------------------------------
# Synthetic session
# --------------------------------------------------------------------------------------------------
def _instruments_block() -> dict:
    return {
        "NIFTY": {
            "option_exchange": "NFO", "expiry": EXPIRY, "strike_step": NIFTY_STEP,
            "contracts": [[k, f"N{k}CE", f"N{k}PE", 0.05] for k in NIFTY_STRIKES],
        },
        "SENSEX": {
            "option_exchange": "BFO", "expiry": EXPIRY, "strike_step": SENSEX_STEP,
            "contracts": [[k, f"S{k}CE", f"S{k}PE", 0.05] for k in SENSEX_STRIKES],
        },
    }


def _header() -> dict:
    return {
        "meta_type": "HEADER", "session_date": SESSION_DATE.isoformat(), "schema_version": 1,
        "config_hash": "sha256:test", "underlyings": ["NIFTY", "SENSEX"], "open_timestamp": T0,
        "instruments": _instruments_block(),
    }


def _spot(recv: float, symbol: str, exchange: str, ltp: float) -> dict:
    return {"symbol": symbol, "exchange": exchange, "mode": 1, "ltp": ltp,
            "timestamp": int(recv), "recv_ts": recv}


def _nifty_spot_at(sec: int, *, drift: float) -> float:
    """A spot that walks steadily upward, so the ATM strike really moves across the session."""
    return 23500.0 + drift * sec


def session_packets(nsec: int = 120, *, drift: float = 4.0) -> list[dict]:
    """One spot packet per underlying per second. Deliberately no option packets.

    Leaving the option book out is the point: the driver must reach its allocation decisions from spot
    movement alone, so the replay's determinism cannot be an artifact of whichever legs the recording
    happened to already be subscribed to.
    """
    out: list[dict] = []
    for sec in range(nsec):
        recv = T0 + sec + 0.5
        out.append(_spot(recv, "NIFTY", "NSE_INDEX", _nifty_spot_at(sec, drift=drift)))
        out.append(_spot(recv, "SENSEX", "BSE_INDEX", 79000.0 + drift * 3 * sec))
    return out


def write_raw(path, packets: list[dict], *, header: dict | None = None) -> str:
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        fh.write(json.dumps(header if header is not None else _header()) + "\n")
        for p in packets:
            fh.write(json.dumps(p) + "\n")
        fh.write(json.dumps({"meta_type": "EOF", "record_count": len(packets)}) + "\n")
    return str(path)


@pytest.fixture
def cfg(base_config, write_config):
    raw = copy.deepcopy(base_config)
    raw["market_depth_framework"] = framework_block()
    return load_config(write_config(raw))


@pytest.fixture
def raw_log(tmp_path):
    return write_raw(tmp_path / "synthetic.jsonl.gz", session_packets())


def read_log(path) -> tuple[list[dict], dict]:
    records, terminal = [], None
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            obj = json.loads(line)
            if obj.get("meta_type") == "DIGEST":
                terminal = obj
            else:
                records.append(obj)
    return records, terminal


def run(cfg, raw, out, **kw):
    return FR.replay_framework(cfg, str(raw), str(out), **kw)


# --------------------------------------------------------------------------------------------------
# 1 - the same log replayed twice
# --------------------------------------------------------------------------------------------------
def test_two_replays_of_one_log_are_byte_identical(cfg, raw_log, tmp_path):
    a, b = tmp_path / "a.jsonl", tmp_path / "b.jsonl"
    sa, sb = run(cfg, raw_log, a), run(cfg, raw_log, b)

    assert a.read_bytes() == b.read_bytes()
    assert sa.digest == sb.digest and sa.digest.startswith("sha256:")
    assert sa.records == sb.records > 0
    assert FR.verify_logs(str(a), str(b)).identical


def test_a_replay_actually_allocated_something(cfg, raw_log, tmp_path):
    """Guard against a vacuously deterministic run: an empty log is byte-identical too."""
    stats = run(cfg, raw_log, tmp_path / "a.jsonl")
    assert stats.packets > 0 and stats.passes > 0 and stats.actions > 0 and stats.frames > 0
    assert stats.peak_premium > 0, "the hybrid never claimed a premium leg"


# --------------------------------------------------------------------------------------------------
# 2 - hash seed independence
# --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("seeds", [("0", "524287")])
def test_the_allocation_log_does_not_depend_on_pythonhashseed(cfg, raw_log, tmp_path, seeds):
    outs = []
    for index, seed in enumerate(seeds):
        out = tmp_path / f"seed{index}.jsonl"
        env = dict(os.environ, PYTHONHASHSEED=seed)
        code = (
            "from market_depth_recorder.config import load_config;"
            "from market_depth_recorder import framework_replay as FR;"
            f"FR.replay_framework(load_config({cfg.source_path!r}), {str(raw_log)!r}, {str(out)!r})"
        )
        proc = subprocess.run(
            [sys.executable, "-c", code], env=env, cwd=str(_repo_parent()),
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, timeout=300,
        )
        assert proc.returncode == 0, proc.stderr
        outs.append(out.read_bytes())
    assert outs[0] == outs[1]


def _repo_parent():
    """The directory `market_depth_recorder` is importable from."""
    import market_depth_recorder

    return os.path.dirname(os.path.dirname(os.path.abspath(market_depth_recorder.__file__)))


# --------------------------------------------------------------------------------------------------
# 3 - --verify against a perturbed reference
# --------------------------------------------------------------------------------------------------
def test_verify_names_the_first_divergence_by_sequence(cfg, raw_log, tmp_path):
    good, perturbed = tmp_path / "good.jsonl", tmp_path / "bad.jsonl"
    run(cfg, raw_log, good)

    records, terminal = read_log(good)
    assert len(records) >= 3
    target = records[2]
    target["premium_occupancy"] = target["premium_occupancy"] + 1  # a single-field perturbation
    with open(perturbed, "w", encoding="utf-8", newline="\n") as fh:
        for rec in records:
            fh.write(FR._dump(rec) + "\n")
        fh.write(FR._dump(terminal) + "\n")

    result = FR.verify_logs(str(good), str(perturbed))
    assert not result.identical
    assert result.seq == records[2]["seq"]
    assert result.field_path == "premium_occupancy"
    assert "premium_occupancy" in result.describe()


def test_verify_cli_exits_non_zero_on_divergence(cfg, raw_log, tmp_path, capsys):
    good, other = tmp_path / "good.jsonl", tmp_path / "other.jsonl"
    run(cfg, raw_log, good)
    run(cfg, raw_log, other, max_packets=20)

    assert FR.main(["--verify", str(good), str(other)]) == 1
    assert FR.main(["--verify", str(good), str(good)]) == 0
    assert "identical" in capsys.readouterr().out


def test_verify_reports_a_record_count_difference(cfg, raw_log, tmp_path):
    long_run, short_run = tmp_path / "long.jsonl", tmp_path / "short.jsonl"
    run(cfg, raw_log, long_run)
    run(cfg, raw_log, short_run, max_packets=30)

    result = FR.verify_logs(str(long_run), str(short_run))
    assert not result.identical
    assert result.reason in ("records differ", "record counts differ")


# --------------------------------------------------------------------------------------------------
# 4 - a spot crossing a window boundary
# --------------------------------------------------------------------------------------------------
def test_a_window_change_fires_a_pass_of_its_own(cfg, tmp_path):
    """A moving spot must produce `window_change` passes, not only interval passes.

    The drift is chosen so the ATM strike moves *slower* than the rebalance interval: both trigger
    kinds then appear in one session, which is what makes the assertion meaningful.
    """
    raw = write_raw(tmp_path / "moving.jsonl.gz", session_packets(120, drift=2.0))
    run(cfg, raw, tmp_path / "moving.jsonl")
    records, _ = read_log(tmp_path / "moving.jsonl")

    triggers = [r["trigger"] for r in records]
    assert triggers[0] == TRIGGER_INITIAL
    assert TRIGGER_WINDOW_CHANGE in triggers
    assert TRIGGER_INTERVAL in triggers


def test_a_still_spot_produces_only_interval_passes(cfg, tmp_path):
    """Once every underlying has a spot, a motionless market must stop re-planning windows.

    The first pass fires on the first spot packet in the file, so the *second* underlying is still
    `no_spot` then and resolves one pass later -- a real window change, correctly reported. The
    steady-state assertion therefore starts once every window has resolved.
    """
    raw = write_raw(tmp_path / "still.jsonl.gz", session_packets(60, drift=0.0))
    run(cfg, raw, tmp_path / "still.jsonl")
    records, _ = read_log(tmp_path / "still.jsonl")

    assert records[0]["trigger"] == TRIGGER_INITIAL
    settled = _first_fully_resolved(records)
    assert settled is not None, "no pass ever resolved every underlying's window"
    assert {r["trigger"] for r in records[settled + 1:]} <= {TRIGGER_INTERVAL}


def _first_fully_resolved(records: list[dict]) -> int | None:
    """Index of the first pass at which every underlying's window has a spot."""
    for index, rec in enumerate(records):
        if all(w["status"] == "resolved" for w in rec["windows"]):
            return index
    return None


# --------------------------------------------------------------------------------------------------
# 5 - the whole session stays inside the budget
# --------------------------------------------------------------------------------------------------
def test_premium_occupancy_never_exceeds_the_effective_budget(cfg, raw_log, tmp_path):
    stats = run(cfg, raw_log, tmp_path / "soak.jsonl")
    records, _ = read_log(tmp_path / "soak.jsonl")

    assert stats.effective_budget > 0
    assert stats.budget_violations == 0
    for rec in records:
        assert rec["premium_occupancy"] <= rec["effective_budget"] == stats.effective_budget


def test_the_soak_reports_no_invariant_violation_of_any_kind(cfg, raw_log, tmp_path):
    stats = run(cfg, raw_log, tmp_path / "soak.jsonl")
    assert (stats.budget_violations, stats.ownership_violations, stats.order_violations) == (0, 0, 0)


# --------------------------------------------------------------------------------------------------
# 6 - churn cooldown across a session
# --------------------------------------------------------------------------------------------------
def test_no_leg_flips_tier_faster_than_the_churn_cooldown(cfg, raw_log, tmp_path):
    cooldown = cfg.framework.depth_allocator["churn_cooldown_seconds"]
    run(cfg, raw_log, tmp_path / "churn.jsonl")
    records, _ = read_log(tmp_path / "churn.jsonl")

    last_flip: dict[str, float] = {}
    for rec in records:
        for kind, _depth, symbol in rec["actions"]:
            if kind not in ("upgrade", "downgrade"):
                continue
            previous = last_flip.get(symbol)
            if previous is not None:
                assert rec["at"] - previous >= cooldown, (
                    f"{symbol} flipped tier {rec['at'] - previous:.1f}s apart, "
                    f"inside the {cooldown}s cooldown"
                )
            last_flip[symbol] = rec["at"]


# --------------------------------------------------------------------------------------------------
# 7 - retiering inside the pre-observation window (the F7.6 invariant, over a session)
# --------------------------------------------------------------------------------------------------
def test_release_precedes_claim_when_no_leg_ever_confirms(cfg, tmp_path):
    """With confirmation switched off, every retier happens before any packet arrives -- exactly the
    pre-observation window F7.6 exists for, now sustained for a whole session."""
    raw = write_raw(tmp_path / "pre.jsonl.gz", session_packets(150, drift=8.0))
    stats = run(cfg, raw, tmp_path / "pre.jsonl", confirm_after_passes=10**6)

    assert stats.simulated_confirmations == 0
    assert stats.order_violations == 0
    assert stats.ownership_violations == 0
    assert stats.budget_violations == 0


def test_a_retier_unsubscribes_the_old_wire_spelling_before_subscribing_the_new_one(cfg, tmp_path):
    raw = write_raw(tmp_path / "retier.jsonl.gz", session_packets(150, drift=8.0))
    run(cfg, raw, tmp_path / "retier.jsonl", confirm_after_passes=10**6)
    records, _ = read_log(tmp_path / "retier.jsonl")

    retiers = 0
    for rec in records:
        seen_release: set[str] = set()
        for action, symbol in rec["wire"]:
            base = symbol.split(":", 1)[0]
            if action == "unsubscribe":
                seen_release.add(base)
                continue
            # a subscribe for a base already on the wire this pass must follow its release
            claimed = [s for a, s in rec["wire"] if a == "unsubscribe" and s.split(":", 1)[0] == base]
            if claimed:
                assert base in seen_release
                retiers += 1
    assert retiers > 0, "the session never retiered a leg; the invariant was not exercised"


# --------------------------------------------------------------------------------------------------
# 8 - an ineligible exchange
# --------------------------------------------------------------------------------------------------
def test_an_ineligible_exchange_gets_no_premium_leg_and_no_refusal_storm(cfg, raw_log, tmp_path):
    """SENSEX/BFO is not premium-eligible in the shipped capability block: full baseline, zero deep."""
    stats = run(cfg, raw_log, tmp_path / "bfo.jsonl")
    records, _ = read_log(tmp_path / "bfo.jsonl")

    assert "SENSEX" in stats.underlyings
    scored = 0
    for rec in records:
        window = next(w for w in rec["windows"] if w["underlying"] == "SENSEX")
        if window["status"] != "resolved":
            continue  # before its first spot there is nothing to cover, which is not a lost baseline
        scored += 1
        sensex = rec["desired"].get("SENSEX", {})
        assert sensex.get("premium", 0) == 0, "a premium leg was desired on an ineligible exchange"
        assert sensex.get("standard", 0) > 0, "the ineligible underlying lost its baseline"
        assert rec["dispatch"]["refused"] == 0
        assert rec["dispatch"]["failed"] == 0
    assert scored > 0, "SENSEX never resolved a window; the ineligible path was not exercised"


def test_the_eligible_underlying_does_get_premium_legs(cfg, raw_log, tmp_path):
    run(cfg, raw_log, tmp_path / "nfo.jsonl")
    records, _ = read_log(tmp_path / "nfo.jsonl")
    assert any(rec["desired"].get("NIFTY", {}).get("premium", 0) > 0 for rec in records)


# --------------------------------------------------------------------------------------------------
# 9 - the driver touches no live path
# --------------------------------------------------------------------------------------------------
def test_the_driver_creates_no_thread_and_no_store(cfg, raw_log, tmp_path):
    before = threading.active_count()
    out = tmp_path / "quiet.jsonl"
    run(cfg, raw_log, out)

    assert threading.active_count() == before
    strays = [
        p for p in tmp_path.rglob("*")
        if p.suffix in (".db", ".duckdb", ".db-wal", ".db-shm")
    ]
    assert strays == []
    assert out.exists()


def test_the_driver_imports_no_clock_and_no_randomness():
    """The determinism guard, mirroring the package guards: no wall clock, no RNG, no uuid."""
    source = open(FR.__file__, "r", encoding="utf-8").read()
    for banned in ("import random", "import uuid", "import time", "time.time(", "random.", "uuid."):
        assert banned not in source, f"{banned!r} would make the replay non-deterministic"


def test_the_driver_never_writes_to_the_raw_recording(cfg, raw_log, tmp_path):
    before = open(raw_log, "rb").read()
    run(cfg, raw_log, tmp_path / "ro.jsonl")
    assert open(raw_log, "rb").read() == before


# --------------------------------------------------------------------------------------------------
# 10 - the flag is a live-path switch, not a tool switch
# --------------------------------------------------------------------------------------------------
def test_the_driver_runs_with_the_framework_flag_off(base_config, write_config, raw_log, tmp_path):
    raw = copy.deepcopy(base_config)
    raw["market_depth_framework"] = framework_block(enabled=False)
    disabled = load_config(write_config(raw))
    assert disabled.framework is not None and disabled.framework.enabled is False

    stats = run(disabled, raw_log, tmp_path / "off.jsonl")
    assert stats.records > 0 and stats.actions > 0


def test_the_driver_refuses_a_config_with_no_framework_block(base_config, write_config, raw_log,
                                                             tmp_path):
    raw = copy.deepcopy(base_config)
    raw.pop("market_depth_framework", None)
    plain = load_config(write_config(raw))
    assert plain.framework is None

    with pytest.raises(ValueError, match="framework"):
        run(plain, raw_log, tmp_path / "none.jsonl")


# --------------------------------------------------------------------------------------------------
# CLI + fail-closed
# --------------------------------------------------------------------------------------------------
def test_the_cli_fails_closed_on_a_missing_recording(tmp_path, capsys):
    missing = tmp_path / "not-there.jsonl.gz"
    assert FR.main([str(missing)]) == 2
    assert "not found" in capsys.readouterr().err
    assert not list(tmp_path.glob("*.jsonl")), "a missing input must produce no output at all"


def test_the_cli_writes_a_log_and_prints_a_digest(cfg, raw_log, tmp_path, capsys):
    out = tmp_path / "cli.jsonl"
    rc = FR.main([str(raw_log), "-o", str(out), "-c", cfg.source_path])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["digest"].startswith("sha256:")
    assert payload["output"] == str(out)
    assert out.exists()


def test_the_cli_honours_a_time_slice(cfg, raw_log, tmp_path):
    full, sliced = tmp_path / "full.jsonl", tmp_path / "slice.jsonl"
    assert FR.main([str(raw_log), "-o", str(full), "-c", cfg.source_path]) == 0
    assert FR.main([str(raw_log), "-o", str(sliced), "-c", cfg.source_path, "--from", "23:59"]) == 0

    full_records, _ = read_log(full)
    sliced_records, _ = read_log(sliced)
    assert len(sliced_records) < len(full_records)


def test_a_negative_confirm_window_is_rejected(cfg, raw_log, tmp_path):
    with pytest.raises(ValueError, match="confirm_after_passes"):
        run(cfg, raw_log, tmp_path / "bad.jsonl", confirm_after_passes=-1)


# --------------------------------------------------------------------------------------------------
# Raw-log tolerance, matching replay.py's
# --------------------------------------------------------------------------------------------------
def test_a_corrupt_trailing_line_is_counted_and_survived(cfg, tmp_path):
    path = tmp_path / "corrupt.jsonl.gz"
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        fh.write(json.dumps(_header()) + "\n")
        for packet in session_packets(40):
            fh.write(json.dumps(packet) + "\n")
        fh.write('{"symbol": "NIFTY", "recv_ts": 12, tru')

    stats = run(cfg, path, tmp_path / "corrupt.jsonl")
    assert stats.corrupt_lines == 1
    assert stats.records > 0


def test_a_second_header_from_a_restart_is_tolerated(cfg, tmp_path):
    path = tmp_path / "restart.jsonl.gz"
    packets = session_packets(40)
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        fh.write(json.dumps(_header()) + "\n")
        for packet in packets[:20]:
            fh.write(json.dumps(packet) + "\n")
        fh.write(json.dumps(_header()) + "\n")
        for packet in packets[20:]:
            fh.write(json.dumps(packet) + "\n")

    stats = run(cfg, path, tmp_path / "restart.jsonl")
    assert stats.corrupt_lines == 0 and stats.records > 0


def test_a_preenrichment_log_without_instruments_is_reported(cfg, tmp_path):
    header = _header()
    header.pop("instruments")
    path = write_raw(tmp_path / "old.jsonl.gz", session_packets(10), header=header)

    with pytest.raises(Exception, match="instruments"):
        run(cfg, path, tmp_path / "old.jsonl")


# --------------------------------------------------------------------------------------------------
# Simulated confirmation is labelled, never smuggled in as evidence
# --------------------------------------------------------------------------------------------------
def test_simulated_confirmations_are_counted_in_every_record(cfg, raw_log, tmp_path):
    stats = run(cfg, raw_log, tmp_path / "sim.jsonl", confirm_after_passes=1)
    records, terminal = read_log(tmp_path / "sim.jsonl")

    assert stats.simulated_confirmations > 0, "no leg was ever confirmed; the model is not exercised"
    assert sum(r["simulated_confirmations"] for r in records) == stats.simulated_confirmations
    assert terminal["stats"]["simulated_confirmations"] == stats.simulated_confirmations


def test_confirmation_makes_coverage_converge(cfg, raw_log, tmp_path):
    """With deliveries confirmed the plan settles; without them it keeps re-planning the same legs."""
    settled = run(cfg, raw_log, tmp_path / "settled.jsonl", confirm_after_passes=1)
    stalled = run(cfg, raw_log, tmp_path / "stalled.jsonl", confirm_after_passes=10**6)
    assert settled.actions <= stalled.actions


# --------------------------------------------------------------------------------------------------
# The bounded soak (F20 option A): the tool's own summariser, over a short synthetic session
# --------------------------------------------------------------------------------------------------
def test_the_bounded_soak_holds_every_invariant_and_repeats_identically(cfg, tmp_path):
    """The suite-resident half of F20. Bounded on purpose -- the long soak is the `tools/` script."""
    from market_depth_recorder.tools.validation.framework_soak import summarise

    raw = write_raw(tmp_path / "soak.jsonl.gz", session_packets(300, drift=3.0))
    first = run(cfg, raw, tmp_path / "soak_a.jsonl")
    second = run(cfg, raw, tmp_path / "soak_b.jsonl")

    assert first.digest == second.digest
    assert (tmp_path / "soak_a.jsonl").read_bytes() == (tmp_path / "soak_b.jsonl").read_bytes()
    assert (first.budget_violations, first.ownership_violations, first.order_violations) == (0, 0, 0)

    records, _ = read_log(tmp_path / "soak_a.jsonl")
    summary = summarise(records)
    assert summary["passes"] == first.records > 10
    assert summary["premium_occupancy_max"] <= first.effective_budget
    assert sum(summary["premium_occupancy_histogram"].values()) == summary["passes"]
    assert set(summary["wire_ops"]) <= {"subscribe", "unsubscribe"}
    assert summary["tier_flips_total"] >= 0


def test_the_soak_tool_fails_closed_on_a_missing_recording(cfg, tmp_path, capsys):
    from market_depth_recorder.tools.validation import framework_soak

    rc = framework_soak.main([
        str(tmp_path / "absent.jsonl.gz"), "--config", cfg.source_path,
    ])
    assert rc == 2
    assert "not found" in capsys.readouterr().err


def test_the_soak_tool_reports_a_clean_session(cfg, tmp_path, capsys):
    from market_depth_recorder.tools.validation import framework_soak

    raw = write_raw(tmp_path / "tool.jsonl.gz", session_packets(120, drift=3.0))
    report = tmp_path / "report.md"
    rc = framework_soak.main([
        raw, "--config", cfg.source_path, "--out", str(tmp_path / "tool.jsonl"),
        "--report", str(report), "--repeat", "2",
    ])
    assert rc == 0
    text = report.read_text(encoding="utf-8")
    assert "not broker evidence" in text
    assert "Premium-occupancy histogram" in text
    assert "violations=0" in capsys.readouterr().out
