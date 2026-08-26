"""F7A offline tests for the depth-transition probe harness (Plan_002 §20.1, §22.8).

These tests cover the harness only -- request construction, response parsing, transition
classification, evidence capture, redaction, safety limits and cleanup. **None of them asserts
anything about broker behaviour**, because none of them has seen a broker: whether FYERS actually
changes 5 -> 50, whether unsubscribe is required, and what a reconnect restores are F7B questions
that only a live session can answer.

The most important test here is the inverse one: :func:`test_accepted_request_never_becomes_a_depth
_claim` and its neighbours pin down that the harness *cannot* record a verified depth change merely
because a request came back ``status: "success"``. That guard is the reason the eventual evidence
document can be trusted.

The tools directory is deliberately not a package (see ``tools/README.md``), so the two modules are
loaded by path, registering each in ``sys.modules`` first -- ``dataclasses`` resolves annotations
through the module entry, and omitting it raises ``AttributeError`` inside ``_is_type``.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import subprocess
import sys
import threading
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
TOOLS_FYERS = PACKAGE_ROOT / "tools" / "fyers"


def _load(name: str):
    """Import a ``tools/fyers`` module by path, registered under ``name`` in ``sys.modules``."""
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, TOOLS_FYERS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # dataclasses needs this before exec_module
    spec.loader.exec_module(module)
    return module


model = _load("_depth_probe_model")
probe = _load("depth_transition_probe")

Confidence = model.Confidence
Mechanism = model.Mechanism
Operation = model.Operation
SymbolForm = model.SymbolForm
TransitionOutcome = model.TransitionOutcome
DepthEvidence = model.DepthEvidence


def _packet(symbol: str, levels: int, *, side: str = "buy") -> dict:
    """A market-data packet carrying ``levels`` book entries on one side."""
    return {
        "type": "market_data",
        "symbol": symbol,
        "depth": {side: [{"price": 100.0 + i, "quantity": 1} for i in range(levels)]},
    }


# --------------------------------------------------------------------------------------
# 1. Wire-symbol construction: CASE A (logical) and CASE B (recorder-style) stay distinct
# --------------------------------------------------------------------------------------

def test_logical_form_never_suffixes():
    assert model.probe_wire_symbol("X", 50, SymbolForm.LOGICAL) == "X"
    assert model.probe_wire_symbol("X", 5, SymbolForm.LOGICAL) == "X"


def test_suffixed_form_suffixes_only_above_the_tbt_minimum():
    assert model.probe_wire_symbol("X", 50, SymbolForm.SUFFIXED) == "X:50"
    assert model.probe_wire_symbol("X", 20, SymbolForm.SUFFIXED) == "X:50"
    assert model.probe_wire_symbol("X", 5, SymbolForm.SUFFIXED) == "X"


def test_case_a_and_case_b_produce_different_wire_symbols_at_depth_50():
    """The whole reason both are probed: the proxy keys subscriptions by symbol, not depth."""
    assert model.probe_wire_symbol("X", 50, SymbolForm.LOGICAL) != model.probe_wire_symbol(
        "X", 50, SymbolForm.SUFFIXED
    )


def test_logical_of_strips_the_suffix():
    assert probe.logical_of("X:50") == "X"
    assert probe.logical_of("X") == "X"


# --------------------------------------------------------------------------------------
# 2. Request construction
# --------------------------------------------------------------------------------------

def test_subscribe_request_carries_both_depth_encodings():
    request = model.build_subscribe_request(
        seq=0, logical_symbol="X", exchange="NFO", depth=50, form=SymbolForm.SUFFIXED, mode=3
    )
    assert request.params["action"] == "subscribe"
    assert request.params["symbol"] == "X:50"
    assert request.params["depth"] == 50
    assert request.params["exchange"] == "NFO"
    assert request.params["mode"] == 3
    assert request.operation is Operation.SUBSCRIBE
    assert request.logical_symbol == "X"


def test_unsubscribe_request_mirrors_the_subscribe_spelling_and_omits_depth():
    request = model.build_unsubscribe_request(
        seq=1, logical_symbol="X", exchange="NFO", depth=50, form=SymbolForm.SUFFIXED, mode=3
    )
    assert request.params["action"] == "unsubscribe"
    assert request.params["symbol"] == "X:50"
    assert "depth" not in request.params
    assert request.requested_depth == 50  # retained for the record, not sent


def test_extra_params_are_merged():
    request = model.build_subscribe_request(
        seq=0, logical_symbol="X", exchange="NFO", depth=5, form=SymbolForm.LOGICAL, mode=3,
        extra={"channel": "1"},
    )
    assert request.params["channel"] == "1"


# --------------------------------------------------------------------------------------
# 3. Case sequences and the default plan
# --------------------------------------------------------------------------------------

def test_bare_resubscribe_case_is_two_subscribes():
    case = model.TransitionCase("t", 5, 50, SymbolForm.LOGICAL)
    requests = model.requests_for_case(case, logical_symbol="X", exchange="NFO", mode=3)
    assert [r.operation for r in requests] == [Operation.SUBSCRIBE, Operation.SUBSCRIBE]
    assert [r.requested_depth for r in requests] == [5, 50]
    assert [r.seq for r in requests] == [0, 1]


def test_unsubscribe_mechanism_inserts_the_release_between_the_two_subscribes():
    case = model.TransitionCase("t", 5, 50, SymbolForm.LOGICAL, Mechanism.UNSUBSCRIBE_THEN_SUBSCRIBE)
    requests = model.requests_for_case(case, logical_symbol="X", exchange="NFO", mode=3, start_seq=7)
    assert [r.operation for r in requests] == [
        Operation.SUBSCRIBE, Operation.UNSUBSCRIBE, Operation.SUBSCRIBE
    ]
    assert [r.seq for r in requests] == [7, 8, 9]


def test_establishing_leg_always_uses_the_recorder_spelling():
    """Only the transition leg varies; the run must start from the recorder's real state."""
    case = model.TransitionCase("t", 50, 5, SymbolForm.LOGICAL)
    first, last = model.requests_for_case(case, logical_symbol="X", exchange="NFO", mode=3)
    assert first.wire_symbol == "X:50"
    assert first.symbol_form is SymbolForm.SUFFIXED
    assert last.symbol_form is SymbolForm.LOGICAL


def test_default_plan_covers_all_four_transitions_and_both_symbol_forms():
    plan = model.default_transition_plan()
    transitions = {(c.from_depth, c.to_depth) for c in plan}
    assert transitions == {(5, 5), (5, 50), (50, 50), (50, 5)}
    forms = {c.symbol_form for c in plan if (c.from_depth, c.to_depth) == (5, 50)}
    assert forms == {SymbolForm.LOGICAL, SymbolForm.SUFFIXED}
    assert Mechanism.UNSUBSCRIBE_THEN_SUBSCRIBE in {c.mechanism for c in plan}
    assert len({c.case_id for c in plan}) == len(plan)


def test_plan_for_is_deterministic_and_spreads_cases_over_instruments():
    plan_a = probe.plan_for(model.default_transition_plan(), ("A", "B"), exchange="NFO", mode=3)
    plan_b = probe.plan_for(model.default_transition_plan(), ("A", "B"), exchange="NFO", mode=3)
    assert [(c.case_id, s, [r.seq for r in rs]) for c, s, rs in plan_a] == [
        (c.case_id, s, [r.seq for r in rs]) for c, s, rs in plan_b
    ]
    assert {s for _c, s, _rs in plan_a} == {"A", "B"}
    seqs = [r.seq for _c, _s, rs in plan_a for r in rs]
    assert seqs == sorted(seqs) and len(seqs) == len(set(seqs))


# --------------------------------------------------------------------------------------
# 4. Acknowledgement parsing -- what the broker SAID
# --------------------------------------------------------------------------------------

def test_ack_prefers_actual_depth_over_the_echoed_request_depth():
    status, reported, error = model.parse_subscribe_ack(
        {"status": "success", "depth": 50, "actual_depth": 5}
    )
    assert (status, reported, error) == ("success", 5, None)


def test_ack_without_any_depth_reports_none_not_the_request():
    assert model.parse_subscribe_ack({"status": "success"}) == ("success", None, None)


def test_ack_missing_entirely_is_all_none():
    assert model.parse_subscribe_ack(None) == (None, None, None)


def test_ack_error_is_surfaced():
    _status, _reported, error = model.parse_subscribe_ack(
        {"status": "error", "message": "no such symbol"}
    )
    assert error == "no such symbol"


def test_ack_ignores_non_numeric_and_boolean_depths():
    assert model.parse_subscribe_ack({"depth": True})[1] is None
    assert model.parse_subscribe_ack({"depth": "deep"})[1] is None
    assert model.parse_subscribe_ack({"depth": "50"})[1] == 50


# --------------------------------------------------------------------------------------
# 5. Depth counting and observation -- what the broker SENT
# --------------------------------------------------------------------------------------

def test_count_depth_levels_uses_the_deeper_side():
    packet = {"depth": {"buy": [1, 2, 3], "sell": [1, 2, 3, 4, 5]}}
    assert model.count_depth_levels(packet) == 5


def test_count_depth_levels_accepts_bids_asks_naming():
    assert model.count_depth_levels({"depth": {"bids": [1] * 50, "asks": [1] * 50}}) == 50


def test_packet_without_a_book_is_not_an_observation():
    assert model.count_depth_levels({"ltp": 100.0}) is None
    assert model.count_depth_levels(None) is None
    assert model.count_depth_levels({"depth": {}}) is None


def test_observe_depth_takes_the_maximum_across_packets():
    """A snapshot then thin incrementals must not read as a shallower book."""
    evidence = model.observe_depth(50, [_packet("X", 50), _packet("X", 2), _packet("X", 7)])
    assert evidence.observed == 50
    assert evidence.observed_packets == 3
    assert evidence.confidence is Confidence.OBSERVED


def test_observe_depth_with_no_packets_is_unknown():
    evidence = model.observe_depth(50, [])
    assert evidence.observed is None
    assert evidence.observed_packets == 0
    assert evidence.confidence is Confidence.UNKNOWN
    assert evidence.effective_depth is None


def test_bookless_packets_do_not_count_as_observations():
    evidence = model.observe_depth(50, [{"symbol": "X", "ltp": 1.0}])
    assert evidence.observed_packets == 0
    assert evidence.confidence is Confidence.UNKNOWN


# --------------------------------------------------------------------------------------
# 6. The confidence lattice -- the anti-fabrication core
# --------------------------------------------------------------------------------------

def test_acknowledgement_alone_is_inferred_never_observed():
    evidence = DepthEvidence(requested=50, reported=50)
    assert evidence.confidence is Confidence.INFERRED
    assert evidence.effective_depth is None, "a reported depth is not a delivered depth"


def test_observation_requires_at_least_one_packet():
    assert DepthEvidence(requested=50, observed=50, observed_packets=0).confidence is (
        Confidence.UNKNOWN
    )
    assert DepthEvidence(requested=50, observed=50, observed_packets=1).confidence is (
        Confidence.OBSERVED
    )


def test_nothing_at_all_is_unknown():
    assert DepthEvidence(requested=50).confidence is Confidence.UNKNOWN


def test_weakest_is_dominated_by_unknown():
    assert model.weakest(Confidence.OBSERVED, Confidence.UNKNOWN) is Confidence.UNKNOWN
    assert model.weakest(Confidence.OBSERVED, Confidence.INFERRED) is Confidence.INFERRED
    assert model.weakest(Confidence.OBSERVED, Confidence.OBSERVED) is Confidence.OBSERVED
    assert model.weakest() is Confidence.UNKNOWN


def test_depth_evidence_rejects_nonsense_inputs():
    with pytest.raises(ValueError):
        DepthEvidence(requested=0)
    with pytest.raises(TypeError):
        DepthEvidence(requested=True)
    with pytest.raises(ValueError):
        DepthEvidence(requested=5, observed_packets=-1)


# --------------------------------------------------------------------------------------
# 7. Transition classification -- "success" must never become "depth changed"
# --------------------------------------------------------------------------------------

def test_accepted_request_never_becomes_a_depth_claim():
    """PART M's explicit requirement: acceptance alone cannot mark a result verified.

    Both acks say ``actual_depth: 50`` and both requests were accepted; no market data was seen.
    The verdict must be UNKNOWN, and the result's ``accepted`` flag must not leak into the depth.
    """
    before = DepthEvidence(requested=5, reported=5)
    after = DepthEvidence(requested=50, reported=50)
    observation = model.TransitionObservation(
        case=model.TransitionCase("t", 5, 50, SymbolForm.LOGICAL), before=before, after=after
    )
    assert observation.outcome is TransitionOutcome.UNKNOWN
    assert observation.confidence is Confidence.INFERRED
    assert observation.before.effective_depth is None
    assert observation.after.effective_depth is None

    request = model.build_subscribe_request(
        seq=0, logical_symbol="X", exchange="NFO", depth=50, form=SymbolForm.LOGICAL, mode=3
    )
    result = model.ProbeResult(request=request, depth=after, status="success")
    assert result.accepted is True
    assert result.depth.confidence is Confidence.INFERRED
    assert result.depth.effective_depth is None


def test_half_observed_transition_is_unknown_in_both_directions():
    observed = DepthEvidence(requested=50, observed=50, observed_packets=3)
    inferred = DepthEvidence(requested=5, reported=5)
    assert model.classify_transition(inferred, observed) is TransitionOutcome.UNKNOWN
    assert model.classify_transition(observed, inferred) is TransitionOutcome.UNKNOWN


def test_fully_observed_change_is_reported_as_changed():
    before = DepthEvidence(requested=5, observed=5, observed_packets=4)
    after = DepthEvidence(requested=50, observed=50, observed_packets=4)
    assert model.classify_transition(before, after) is TransitionOutcome.DEPTH_CHANGED


def test_fully_observed_non_change_is_reported_as_unchanged():
    """The outcome the harness must be equally willing to record."""
    before = DepthEvidence(requested=5, observed=5, observed_packets=4)
    after = DepthEvidence(requested=50, reported=50, observed=5, observed_packets=4)
    assert model.classify_transition(before, after) is TransitionOutcome.DEPTH_UNCHANGED


# --------------------------------------------------------------------------------------
# 8. Support evidence -- absence of a test is not evidence of absence
# --------------------------------------------------------------------------------------

def test_unattempted_operation_is_unknown_not_unsupported():
    support = model.SupportEvidence(operation=Operation.UNSUBSCRIBE, attempted=False)
    assert support.supported is None
    assert support.confidence is Confidence.UNKNOWN


def test_accepted_but_uneffective_operation_stays_undecided():
    support = model.SupportEvidence(
        operation=Operation.UNSUBSCRIBE, attempted=True, accepted=True
    )
    assert support.supported is None, "acceptance is not proof the operation did anything"
    assert support.confidence is Confidence.INFERRED


def test_explicit_rejection_is_enough_to_say_unsupported():
    support = model.SupportEvidence(
        operation=Operation.UNSUBSCRIBE, attempted=True, accepted=False, error="INVALID_ACTION"
    )
    assert support.supported is False


def test_observed_effect_decides_it_either_way():
    assert model.SupportEvidence(
        operation=Operation.UNSUBSCRIBE, attempted=True, accepted=True, effect_observed=True
    ).supported is True
    assert model.SupportEvidence(
        operation=Operation.UNSUBSCRIBE, attempted=True, accepted=True, effect_observed=False
    ).supported is False


# --------------------------------------------------------------------------------------
# 9. Secret hygiene -- no credential may reach an evidence file
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize(
    "key", ["api_key", "API_KEY", "apikey", "feed_token", "auth_token", "secret", "password",
            "API_KEY_PEPPER"],
)
def test_secret_looking_keys_are_redacted(key):
    assert model.redact({key: "hunter2"})[key] == "[REDACTED]"


def test_redaction_leaves_ordinary_fields_intact():
    out = model.redact({"symbol": "X", "depth": 50, "api_key": "s3cr3t"})
    assert out == {"symbol": "X", "depth": 50, "api_key": "[REDACTED]"}


def test_probe_request_refuses_unredacted_secrets():
    with pytest.raises(ValueError, match="unredacted"):
        model.ProbeRequest(
            seq=0, operation=Operation.SUBSCRIBE, logical_symbol="X", exchange="NFO",
            wire_symbol="X", symbol_form=SymbolForm.LOGICAL, requested_depth=5, mode=3,
            connection_id="c0", params={"api_key": "s3cr3t"},
        )


def test_builders_never_emit_an_unredacted_secret():
    request = model.build_subscribe_request(
        seq=0, logical_symbol="X", exchange="NFO", depth=5, form=SymbolForm.LOGICAL, mode=3,
        extra={"api_key": "s3cr3t"},
    )
    assert request.params["api_key"] == "[REDACTED]"


def test_evidence_environment_is_redacted():
    evidence = model.build_evidence(
        mode="dry-run", environment={"url": "ws://h:8765", "api_key": "s3cr3t"}
    )
    assert evidence["environment"]["api_key"] == "[REDACTED]"
    assert "s3cr3t" not in model.dumps_evidence(evidence)


# --------------------------------------------------------------------------------------
# 10. Evidence record: self-describing, deterministic, honest about its own mode
# --------------------------------------------------------------------------------------

def test_dry_run_evidence_is_flagged_as_not_broker_evidence():
    evidence = model.build_evidence(mode="dry-run", environment={})
    assert evidence["is_broker_evidence"] is False
    assert evidence["mode"] == "dry-run"


def test_live_evidence_is_flagged_as_broker_evidence():
    assert model.build_evidence(mode="live", environment={})["is_broker_evidence"] is True


def test_evidence_serialisation_is_stable_and_json_parseable():
    evidence = model.build_evidence(
        mode="dry-run", environment={"b": 2, "a": 1},
        support=[model.SupportEvidence(operation=Operation.UNSUBSCRIBE)],
    )
    text = model.dumps_evidence(evidence)
    assert text == model.dumps_evidence(evidence)
    assert text.endswith("\n")
    parsed = json.loads(text)
    assert parsed["schema"] == "market_depth_recorder.depth_transition_probe/1"
    assert parsed["support"][0]["supported"] is None
    assert parsed["support"][0]["confidence"] == "unknown"


def test_result_dict_keeps_the_three_depths_apart():
    request = model.build_subscribe_request(
        seq=0, logical_symbol="X", exchange="NFO", depth=50, form=SymbolForm.LOGICAL, mode=3
    )
    result = model.ProbeResult(
        request=request, depth=DepthEvidence(requested=50, reported=50), status="success"
    )
    payload = model.result_to_dict(result)
    assert payload["depth"]["requested"] == 50
    assert payload["depth"]["reported"] == 50
    assert payload["depth"]["observed"] is None
    assert payload["depth"]["effective_depth"] is None
    assert payload["depth"]["confidence"] == "inferred"


def test_observation_dict_records_the_side_questions():
    observation = model.TransitionObservation(
        case=model.TransitionCase("t", 5, 50, SymbolForm.SUFFIXED),
        before=DepthEvidence(requested=5), after=DepthEvidence(requested=50),
        prior_still_active=None, duplicate_subscription=None, capacity_delta=None,
        acknowledgement_seen=True,
    )
    payload = model.observation_to_dict(observation)
    assert payload["outcome"] == "unknown"
    assert payload["prior_still_active"] is None
    assert payload["duplicate_subscription"] is None
    assert payload["capacity_delta"] is None
    assert payload["acknowledgement_seen"] is True


# --------------------------------------------------------------------------------------
# 11. CLI: dry-run is the default, live is opt-in, limits are enforced
# --------------------------------------------------------------------------------------

def test_live_is_not_the_default():
    args = probe.build_parser().parse_args(["--symbols", "X"])
    assert args.live is False
    assert args.allow_outside_session is False


def test_missing_symbols_is_a_usage_error(capsys):
    assert probe.main([]) == 2
    assert "symbols" in capsys.readouterr().err


def test_instrument_count_is_capped(capsys):
    assert model.MAX_INSTRUMENTS_HARD_CAP == 2
    assert probe.main(["--symbols", "A,B,C"]) == 2
    assert "safety limit" in capsys.readouterr().err


def test_unknown_case_id_is_a_usage_error(capsys):
    assert probe.main(["--symbols", "X", "--cases", "NOPE"]) == 2
    assert "no case matched" in capsys.readouterr().err


def test_case_selection_narrows_the_plan(tmp_path, capsys):
    out = tmp_path / "e.json"
    assert probe.main(["--symbols", "X", "--cases", "C2_5_50_logical", "--out", str(out)]) == 0
    capsys.readouterr()
    evidence = json.loads(out.read_text(encoding="utf-8"))
    assert evidence["environment"]["cases"] == ["C2_5_50_logical"]
    assert len(evidence["results"]) == 2


def test_dry_run_writes_an_artefact_with_no_broker_claims(tmp_path, capsys):
    out = tmp_path / "dry.json"
    assert probe.main(["--symbols", "X", "--out", str(out)]) == 0
    assert "not broker evidence" in capsys.readouterr().out
    evidence = json.loads(out.read_text(encoding="utf-8"))
    assert evidence["is_broker_evidence"] is False
    assert evidence["observations"] == []
    assert all(r["depth"]["confidence"] == "unknown" for r in evidence["results"])
    assert all(r["depth"]["effective_depth"] is None for r in evidence["results"])
    assert all(r["status"] is None for r in evidence["results"])


def test_live_without_a_key_refuses_before_touching_the_network(monkeypatch, capsys):
    monkeypatch.delenv("OPENALGO_API_KEY", raising=False)
    monkeypatch.setattr(probe, "_Session", _never_construct)
    assert probe.main(["--symbols", "X", "--live"]) == 2
    assert "OPENALGO_API_KEY" in capsys.readouterr().err


def test_live_outside_the_session_refuses_unless_forced(monkeypatch, capsys):
    monkeypatch.setenv("OPENALGO_API_KEY", "k")
    monkeypatch.setattr(probe, "in_market_session", lambda *a, **k: False)
    monkeypatch.setattr(probe, "_Session", _never_construct)
    assert probe.main(["--symbols", "X", "--live"]) == 2
    assert "outside the 09:15-15:30 IST session" in capsys.readouterr().err


def test_unreachable_proxy_is_a_setup_error_not_a_result(monkeypatch, capsys):
    monkeypatch.setenv("OPENALGO_API_KEY", "k")
    monkeypatch.setattr(probe, "in_market_session", lambda *a, **k: True)

    def _refuse(*_a, **_k):
        raise ConnectionRefusedError("nothing listening")

    monkeypatch.setattr(probe, "_Session", _refuse)
    assert probe.main(["--symbols", "X", "--live"]) == 2
    assert "cannot reach the OpenAlgo proxy" in capsys.readouterr().err


def _never_construct(*_args, **_kwargs):
    raise AssertionError("the live path must not be reached in this test")


@pytest.mark.parametrize(
    ("weekday_iso", "expected"),
    [("2026-08-26T09:14:59", False), ("2026-08-26T09:15:00", True),
     ("2026-08-26T15:30:00", True), ("2026-08-26T15:30:01", False),
     ("2026-08-29T12:00:00", False)],  # Saturday
)
def test_market_session_window(weekday_iso, expected):
    import datetime as dt

    moment = dt.datetime.fromisoformat(weekday_iso).replace(tzinfo=probe._IST)
    assert probe.in_market_session(moment) is expected


# --------------------------------------------------------------------------------------
# 12. Live-path result processing, driven by a stub session (still no broker)
# --------------------------------------------------------------------------------------

class _StubSession:
    """A scripted proxy: replies to every frame, optionally emits market data per subscribe."""

    def __init__(self, acks, windows):
        self.acks = list(acks)
        self.windows = list(windows)
        self.sent: list[dict] = []

    def send(self, frame):
        self.sent.append(frame)

    def read_until(self, _predicate, *, deadline_s):  # noqa: ARG002 - stub honours no clock
        return self.acks.pop(0) if self.acks else None

    def drain(self, _seconds):
        return self.windows.pop(0) if self.windows else []

    def close(self):
        pass


def _run(case, acks, windows, symbol="X"):
    requests = model.requests_for_case(case, logical_symbol=symbol, exchange="NFO", mode=3)
    session = _StubSession(acks, windows)
    results, observation, unsub = probe._run_case_live(
        session, case, symbol, requests, observe_secs=0.0, settle_secs=0.0
    )
    return session, results, observation, unsub


def test_live_run_with_acks_but_no_market_data_stays_unknown():
    """The end-to-end version of the anti-fabrication guarantee."""
    case = model.TransitionCase("C2", 5, 50, SymbolForm.LOGICAL)
    _session, results, observation, _unsub = _run(
        case,
        acks=[{"status": "success", "actual_depth": 5}, {"status": "success", "actual_depth": 50}],
        windows=[[], []],
    )
    assert all(r.accepted for r in results)
    assert observation.outcome is TransitionOutcome.UNKNOWN
    assert observation.confidence is not Confidence.OBSERVED
    assert observation.before.effective_depth is None
    assert observation.after.effective_depth is None


def test_live_run_with_real_packets_records_an_observed_change():
    case = model.TransitionCase("C2", 5, 50, SymbolForm.LOGICAL)
    _session, _results, observation, _unsub = _run(
        case,
        acks=[{"status": "success"}, {"status": "success", "actual_depth": 50}],
        windows=[[_packet("X", 5)] * 3, [_packet("X", 50)] * 3],
    )
    assert observation.outcome is TransitionOutcome.DEPTH_CHANGED
    assert observation.confidence is Confidence.OBSERVED
    assert (observation.before.effective_depth, observation.after.effective_depth) == (5, 50)
    assert observation.acknowledgement_seen is True


def test_live_run_records_an_observed_non_change():
    """If the depth does not move, the harness must say so rather than trust the ack."""
    case = model.TransitionCase("C2", 5, 50, SymbolForm.LOGICAL)
    _session, _results, observation, _unsub = _run(
        case,
        acks=[{"status": "success"}, {"status": "success", "actual_depth": 50}],
        windows=[[_packet("X", 5)] * 2, [_packet("X", 5)] * 2],
    )
    assert observation.outcome is TransitionOutcome.DEPTH_UNCHANGED
    assert observation.after.reported == 50
    assert observation.after.observed == 5


def test_duplicate_subscription_is_detected_from_the_wire_spellings():
    """Packets arriving under both spellings after the transition mean two live subscriptions."""
    case = model.TransitionCase("C3", 5, 50, SymbolForm.SUFFIXED)
    _session, _results, observation, _unsub = _run(
        case,
        acks=[{"status": "success"}, {"status": "success"}],
        windows=[[_packet("X", 5)], [_packet("X", 5), _packet("X:50", 50)]],
    )
    assert observation.duplicate_subscription is True
    assert observation.prior_still_active is True
    assert observation.after.observed == 50


def test_single_spelling_after_transition_is_not_a_duplicate():
    case = model.TransitionCase("C3", 5, 50, SymbolForm.SUFFIXED)
    _session, _results, observation, _unsub = _run(
        case,
        acks=[{"status": "success"}, {"status": "success"}],
        windows=[[_packet("X", 5)], [_packet("X:50", 50)]],
    )
    assert observation.duplicate_subscription is False
    assert observation.prior_still_active is False


def test_packets_for_another_symbol_are_ignored():
    case = model.TransitionCase("C2", 5, 50, SymbolForm.LOGICAL)
    _session, _results, observation, _unsub = _run(
        case,
        acks=[{"status": "success"}, {"status": "success"}],
        windows=[[_packet("OTHER", 5)], [_packet("OTHER", 50)]],
    )
    assert observation.before.observed_packets == 0
    assert observation.outcome is TransitionOutcome.UNKNOWN


def test_unsubscribe_mechanism_records_support_evidence_without_overclaiming():
    case = model.TransitionCase(
        "C6", 5, 50, SymbolForm.LOGICAL, Mechanism.UNSUBSCRIBE_THEN_SUBSCRIBE
    )
    session, results, _observation, unsub = _run(
        case,
        acks=[{"status": "success"}, {"status": "success"}, {"status": "success"}],
        windows=[[_packet("X", 5)], [_packet("X", 50)]],
    )
    assert [f["action"] for f in session.sent] == ["subscribe", "unsubscribe", "subscribe"]
    assert unsub is not None
    assert unsub.attempted is True and unsub.accepted is True
    assert unsub.supported is None, "an accepted unsubscribe is not yet a working unsubscribe"
    assert len(results) == 3


def test_rejected_unsubscribe_is_recorded_as_unsupported():
    case = model.TransitionCase(
        "C6", 5, 50, SymbolForm.LOGICAL, Mechanism.UNSUBSCRIBE_THEN_SUBSCRIBE
    )
    _session, _results, _observation, unsub = _run(
        case,
        acks=[{"status": "success"}, {"status": "error", "message": "INVALID_ACTION"},
              {"status": "success"}],
        windows=[[_packet("X", 5)], [_packet("X", 50)]],
    )
    assert unsub.accepted is False
    assert unsub.supported is False
    assert unsub.error == "INVALID_ACTION"


def test_missing_acknowledgement_is_recorded_not_assumed():
    case = model.TransitionCase("C2", 5, 50, SymbolForm.LOGICAL)
    _session, _results, observation, _unsub = _run(
        case, acks=[], windows=[[_packet("X", 5)], [_packet("X", 50)]]
    )
    assert observation.acknowledgement_seen is False
    assert observation.outcome is TransitionOutcome.DEPTH_CHANGED, (
        "delivered data stands on its own, with or without an ack"
    )


# --------------------------------------------------------------------------------------
# 13. Cleanup: every subscribed spelling is released
# --------------------------------------------------------------------------------------

def test_cleanup_unsubscribes_every_wire_symbol_it_subscribed():
    plan = probe.plan_for(model.default_transition_plan(), ("X",), exchange="NFO", mode=3)
    session = _StubSession(acks=[{"status": "success"}] * 10, windows=[])
    results = probe._cleanup(session, plan, exchange="NFO", mode=3)
    released = {f["symbol"] for f in session.sent}
    subscribed = {r.wire_symbol for _c, _s, rs in plan for r in rs
                  if r.operation is Operation.SUBSCRIBE}
    assert released == subscribed
    assert all(f["action"] == "unsubscribe" for f in session.sent)
    assert all("cleanup" in r.notes for r in results)


def test_cleanup_failure_is_recorded_not_raised():
    class _Broken(_StubSession):
        def send(self, frame):
            raise OSError("socket gone")

    plan = probe.plan_for(model.default_transition_plan()[:1], ("X",), exchange="NFO", mode=3)
    results = probe._cleanup(_Broken([], []), plan, exchange="NFO", mode=3)
    assert results and results[0].error.startswith("OSError")
    assert results[0].status is None


# --------------------------------------------------------------------------------------
# 14. Inertness: importing or dry-running must not touch the network
# --------------------------------------------------------------------------------------

_IMPORT_PROBE = """
import sys, threading
before = threading.active_count()
sys.path.insert(0, {tools!r})
import _depth_probe_model, depth_transition_probe
assert threading.active_count() == before, "import started a thread"
banned = [m for m in ("websocket", "socket", "openalgo", "requests", "httpx") if m in sys.modules
          and m != "socket"]
print("OK", banned)
"""


def test_importing_the_harness_starts_no_thread_and_loads_no_network_client():
    code = _IMPORT_PROBE.format(tools=str(TOOLS_FYERS))
    completed = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=60
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "OK []", completed.stdout


def test_dry_run_makes_no_socket_and_starts_no_thread(monkeypatch, tmp_path):
    import socket as socket_module

    def _forbidden(*_a, **_k):
        raise AssertionError("dry-run attempted network I/O")

    monkeypatch.setattr(socket_module, "socket", _forbidden)
    monkeypatch.setattr(socket_module, "create_connection", _forbidden)
    monkeypatch.setattr(probe, "_Session", _never_construct)
    before = threading.active_count()
    assert probe.main(["--symbols", "X", "--out", str(tmp_path / "e.json")]) == 0
    assert threading.active_count() == before


@pytest.mark.parametrize("filename", ["depth_transition_probe.py", "_depth_probe_model.py"])
def test_harness_imports_no_recorder_or_framework_module(filename):
    """Checked over the parsed imports, so prose mentioning a module name cannot fail it."""
    tree = ast.parse((TOOLS_FYERS / filename).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    roots = {name.split(".")[0] for name in imported}
    assert "market_depth_recorder" not in roots
    assert "market_depth_framework" not in roots
    assert not any("market_depth_framework" in name for name in imported)


def test_framework_still_has_no_broker_adapter():
    """F7 measures first; the adapter is written from the evidence, not before it (§22)."""
    assert not (PACKAGE_ROOT / "market_depth_framework" / "broker_adapter.py").exists()
