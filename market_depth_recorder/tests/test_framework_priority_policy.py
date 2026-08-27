"""F4 tests for the Priority Policy (Plan_002 §10.3, §14.2, §14.6, §22.5).

The Priority Policy answers one question -- among the candidates for one underlying, in what order do
they matter -- so these tests police two things in equal measure: that the order is right and
1-based, and that the layer still knows nothing about budgets, premium overlays, hysteresis, cooldown,
subscriptions, or brokers. Several tests therefore assert over the module's **source** rather than its
behaviour: a scope boundary that is only reviewed drifts, and one that is asserted does not.

No live broker, WebSocket, feed, network, or credential is used anywhere in this file. Underlyings and
exchanges are synthetic, so nothing can pass by accident on a NIFTY-shaped chain.
"""

from __future__ import annotations

import ast
import random
from pathlib import Path

import pytest

from market_depth_recorder.market_depth_framework import (
    FrameworkConfigError,
    Instrument,
)
from market_depth_recorder.market_depth_framework.priority_policy import (
    DEFAULT_POLICY,
    AtmDistancePolicy,
    MarketContext,
    PriorityPolicy,
    PriorityScore,
    market_context_from_window,
    policy_for,
    rank_candidates,
    rank_scores,
)
from market_depth_recorder.market_depth_framework.window_manager import (
    FixedExpiryCalendar,
    TagSymbolCodec,
    WindowManager,
    WindowSpec,
    WindowStatus,
)

MODULE_PATH = Path(
    __import__(
        "market_depth_recorder.market_depth_framework.priority_policy",
        fromlist=["priority_policy"],
    ).__file__
).resolve()

CALL_TAG = "CE"
PUT_TAG = "PE"

ALPHA = "ALPHAIDX"
BETA = "BETAIDX"
ALPHA_EXCHANGE = "XFO"
BETA_EXCHANGE = "YFO"
ALPHA_STEP = 50.0
BETA_STEP = 100.0
ALPHA_EXPIRY = "28AUG26"
BETA_EXPIRY = "27AUG26"

CODEC_RULE = "equity_option"
EXPIRY_RULE = "weekly"


# ----------------------------------------------------------------------------------------------
# Builders / fixtures
# ----------------------------------------------------------------------------------------------
def leg(underlying: str, exchange: str, strike: float, tag: str, expiry: str) -> Instrument:
    return Instrument(
        underlying=underlying,
        exchange=exchange,
        symbol=f"{underlying}{expiry}{strike:g}{tag}",
        expiry=expiry,
        strike=strike,
        option_type=tag,
    )


def chain(underlying: str, exchange: str, strikes, expiry: str) -> list[Instrument]:
    return [leg(underlying, exchange, k, tag, expiry) for k in strikes for tag in (CALL_TAG, PUT_TAG)]


def strikes_around(centre: float, step: float, count: int) -> list[float]:
    return [centre + step * i for i in range(-count, count + 1)]


@pytest.fixture
def policy() -> AtmDistancePolicy:
    return AtmDistancePolicy()


@pytest.fixture
def alpha_ctx() -> MarketContext:
    return MarketContext(underlying=ALPHA, spot=25012.0, atm_strike=25000.0)


@pytest.fixture
def alpha_candidates() -> list[Instrument]:
    return chain(ALPHA, ALPHA_EXCHANGE, strikes_around(25000.0, ALPHA_STEP, 4), ALPHA_EXPIRY)


@pytest.fixture
def beta_candidates() -> list[Instrument]:
    return chain(BETA, BETA_EXCHANGE, strikes_around(80000.0, BETA_STEP, 3), BETA_EXPIRY)


def ranked_symbols(scores) -> list[str]:
    return [s.instrument.symbol for s in scores]


# ----------------------------------------------------------------------------------------------
# ATM-distance ranking
# ----------------------------------------------------------------------------------------------
def test_the_atm_pair_ranks_first(policy, alpha_candidates, alpha_ctx):
    scores = policy.compute_priorities(alpha_candidates, alpha_ctx)
    assert {s.instrument.strike for s in scores[:2]} == {25000.0}


def test_nearer_to_atm_outranks_further(policy, alpha_candidates, alpha_ctx):
    scores = policy.compute_priorities(alpha_candidates, alpha_ctx)
    by_symbol = {s.instrument.symbol: s for s in scores}
    near = by_symbol[leg(ALPHA, ALPHA_EXCHANGE, 25050.0, CALL_TAG, ALPHA_EXPIRY).symbol]
    far = by_symbol[leg(ALPHA, ALPHA_EXCHANGE, 25200.0, CALL_TAG, ALPHA_EXPIRY).symbol]
    assert near.rank < far.rank


def test_distance_is_symmetric_about_atm(policy, alpha_candidates, alpha_ctx):
    """A strike one step above ATM and one step below score identically; only symbol separates them."""
    scores = {s.instrument.symbol: s.score for s in policy.compute_priorities(alpha_candidates, alpha_ctx)}
    above = scores[leg(ALPHA, ALPHA_EXCHANGE, 25050.0, CALL_TAG, ALPHA_EXPIRY).symbol]
    below = scores[leg(ALPHA, ALPHA_EXCHANGE, 24950.0, CALL_TAG, ALPHA_EXPIRY).symbol]
    assert above == below


def test_score_is_negative_distance_from_atm(policy, alpha_candidates, alpha_ctx):
    for score in policy.compute_priorities(alpha_candidates, alpha_ctx):
        assert score.score == -abs(float(score.instrument.strike) - alpha_ctx.atm_strike)


def test_the_atm_leg_scores_zero(policy, alpha_candidates, alpha_ctx):
    scores = {s.instrument.strike: s.score for s in policy.compute_priorities(alpha_candidates, alpha_ctx)}
    assert scores[25000.0] == 0.0


def test_scores_are_monotonic_in_distance(policy, alpha_candidates, alpha_ctx):
    scores = policy.compute_priorities(alpha_candidates, alpha_ctx)
    distances = [abs(float(s.instrument.strike) - alpha_ctx.atm_strike) for s in scores]
    assert distances == sorted(distances), "rank order must never move outward then back in"


def test_atm_need_not_equal_spot(policy, alpha_candidates):
    """Distance is measured from ATM, not from spot -- the ATM the Window Manager already resolved."""
    ctx = MarketContext(underlying=ALPHA, spot=25049.0, atm_strike=25050.0)
    scores = policy.compute_priorities(alpha_candidates, ctx)
    assert {s.instrument.strike for s in scores[:2]} == {25050.0}


def test_ranking_is_independent_of_the_strike_step(policy, beta_candidates):
    """A 100-point grid ranks exactly like a 50-point one: no step constant is involved."""
    ctx = MarketContext(underlying=BETA, spot=80010.0, atm_strike=80000.0)
    scores = policy.compute_priorities(beta_candidates, ctx)
    assert {s.instrument.strike for s in scores[:2]} == {80000.0}
    # The four legs one step out all tie on distance, so §10.3's symbol tie-break -- not the step --
    # orders them; the band as a whole is what ranks next.
    assert {s.instrument.strike for s in scores[2:6]} == {79900.0, 80100.0}


# ----------------------------------------------------------------------------------------------
# 1-based rank (§14.2, fork F4)
# ----------------------------------------------------------------------------------------------
def test_rank_starts_at_one(policy, alpha_candidates, alpha_ctx):
    assert policy.compute_priorities(alpha_candidates, alpha_ctx)[0].rank == 1


def test_ranks_are_consecutive_from_one(policy, alpha_candidates, alpha_ctx):
    scores = policy.compute_priorities(alpha_candidates, alpha_ctx)
    assert [s.rank for s in scores] == list(range(1, len(alpha_candidates) + 1))


def test_no_rank_is_zero(policy, alpha_candidates, alpha_ctx):
    assert all(s.rank >= 1 for s in policy.compute_priorities(alpha_candidates, alpha_ctx))


def test_rank_zero_is_rejected_by_the_score_type():
    """The 1-based basis is enforced by the type, not merely produced by the ranker."""
    instrument = leg(ALPHA, ALPHA_EXCHANGE, 25000.0, CALL_TAG, ALPHA_EXPIRY)
    with pytest.raises(ValueError, match="1-based"):
        PriorityScore(instrument=instrument, score=0.0, rank=0)


def test_negative_rank_is_rejected():
    instrument = leg(ALPHA, ALPHA_EXCHANGE, 25000.0, CALL_TAG, ALPHA_EXPIRY)
    with pytest.raises(ValueError, match="1-based"):
        PriorityScore(instrument=instrument, score=0.0, rank=-1)


def test_rank_must_be_an_int_not_a_bool():
    instrument = leg(ALPHA, ALPHA_EXCHANGE, 25000.0, CALL_TAG, ALPHA_EXPIRY)
    with pytest.raises(ValueError, match="must be an int"):
        PriorityScore(instrument=instrument, score=0.0, rank=True)


def test_rank_equals_position_plus_one(policy, alpha_candidates, alpha_ctx):
    """The one place a 0-based index could leak in is the enumerate; pin the relationship."""
    scores = policy.compute_priorities(alpha_candidates, alpha_ctx)
    for position, score in enumerate(scores):
        assert score.rank == position + 1


# ----------------------------------------------------------------------------------------------
# Total order and tie-break (§10.3)
# ----------------------------------------------------------------------------------------------
def test_the_order_is_score_descending(policy, alpha_candidates, alpha_ctx):
    scores = policy.compute_priorities(alpha_candidates, alpha_ctx)
    assert [s.score for s in scores] == sorted((s.score for s in scores), reverse=True)


def test_ties_break_by_symbol_ascending(policy, alpha_candidates, alpha_ctx):
    """§10.3's total order: score desc, then symbol. The CE/PE pair at one strike is the common tie."""
    scores = policy.compute_priorities(alpha_candidates, alpha_ctx)
    top_two = ranked_symbols(scores[:2])
    assert top_two == sorted(top_two)


def test_mirrored_strikes_tie_and_break_by_symbol(policy, alpha_candidates, alpha_ctx):
    scores = policy.compute_priorities(alpha_candidates, alpha_ctx)
    band = [s for s in scores if abs(float(s.instrument.strike) - 25000.0) == ALPHA_STEP]
    assert len(band) == 4
    assert ranked_symbols(band) == sorted(ranked_symbols(band))


def test_the_full_order_is_score_then_symbol(policy, alpha_candidates, alpha_ctx):
    scores = policy.compute_priorities(alpha_candidates, alpha_ctx)
    keys = [(-s.score, s.instrument.symbol) for s in scores]
    assert keys == sorted(keys)


def test_the_tie_break_does_not_prefer_calls_over_puts(policy, alpha_ctx):
    """Ordering must come from the symbol, not from an unstated side preference."""
    call = leg(ALPHA, ALPHA_EXCHANGE, 25000.0, CALL_TAG, ALPHA_EXPIRY)
    put = leg(ALPHA, ALPHA_EXCHANGE, 25000.0, PUT_TAG, ALPHA_EXPIRY)
    scores = policy.compute_priorities([call, put], alpha_ctx)
    winner = min(call.symbol, put.symbol)
    assert scores[0].instrument.symbol == winner


def test_rank_scores_is_the_only_ordering_and_sorts_raw_pairs():
    a = leg(ALPHA, ALPHA_EXCHANGE, 25000.0, CALL_TAG, ALPHA_EXPIRY)
    b = leg(ALPHA, ALPHA_EXCHANGE, 25050.0, CALL_TAG, ALPHA_EXPIRY)
    scores = rank_scores([(a, -50.0), (b, 0.0)])
    assert [s.instrument.symbol for s in scores] == [b.symbol, a.symbol]
    assert [s.rank for s in scores] == [1, 2]


def test_rank_scores_rejects_duplicate_symbols():
    """Two rows for one leg cannot be separated by the tie-break, so the caller is told, not guessed at."""
    a = leg(ALPHA, ALPHA_EXCHANGE, 25000.0, CALL_TAG, ALPHA_EXPIRY)
    with pytest.raises(ValueError, match="distinct symbols"):
        rank_scores([(a, 0.0), (a, -1.0)])


def test_rank_scores_rejects_a_non_finite_score():
    a = leg(ALPHA, ALPHA_EXCHANGE, 25000.0, CALL_TAG, ALPHA_EXPIRY)
    with pytest.raises(ValueError, match="finite"):
        rank_scores([(a, float("nan"))])


def test_rank_scores_rejects_a_non_instrument():
    with pytest.raises(ValueError, match="Instrument"):
        rank_scores([("ALPHAIDX25000CE", 0.0)])


def test_rank_scores_on_an_empty_input_is_empty():
    assert rank_scores([]) == ()


# ----------------------------------------------------------------------------------------------
# Candidate identity preservation
# ----------------------------------------------------------------------------------------------
def test_every_candidate_is_scored_exactly_once(policy, alpha_candidates, alpha_ctx):
    scores = policy.compute_priorities(alpha_candidates, alpha_ctx)
    assert len(scores) == len(alpha_candidates)
    assert {s.instrument for s in scores} == set(alpha_candidates)


def test_the_scored_instruments_are_the_same_objects(policy, alpha_candidates, alpha_ctx):
    """F5 must receive what F3 produced, not a re-derived lookup that could drift."""
    scores = policy.compute_priorities(alpha_candidates, alpha_ctx)
    originals = {id(c) for c in alpha_candidates}
    assert all(id(s.instrument) in originals for s in scores)


def test_no_candidate_is_dropped_or_invented(policy, alpha_candidates, alpha_ctx):
    scores = policy.compute_priorities(alpha_candidates, alpha_ctx)
    assert sorted(ranked_symbols(scores)) == sorted(c.symbol for c in alpha_candidates)


def test_the_input_sequence_is_not_mutated(policy, alpha_candidates, alpha_ctx):
    before = list(alpha_candidates)
    policy.compute_priorities(alpha_candidates, alpha_ctx)
    assert alpha_candidates == before


def test_the_score_carries_the_symbol_passthrough(policy, alpha_candidates, alpha_ctx):
    for score in policy.compute_priorities(alpha_candidates, alpha_ctx):
        assert score.symbol == score.instrument.symbol


# ----------------------------------------------------------------------------------------------
# Determinism
# ----------------------------------------------------------------------------------------------
def test_repeated_evaluation_is_identical(policy, alpha_candidates, alpha_ctx):
    first = policy.compute_priorities(alpha_candidates, alpha_ctx)
    for _ in range(5):
        assert policy.compute_priorities(alpha_candidates, alpha_ctx) == first


def test_shuffled_input_produces_the_identical_ranking(policy, alpha_candidates, alpha_ctx):
    expected = policy.compute_priorities(alpha_candidates, alpha_ctx)
    rng = random.Random(20260825)
    for _ in range(10):
        shuffled = list(alpha_candidates)
        rng.shuffle(shuffled)
        assert policy.compute_priorities(shuffled, alpha_ctx) == expected


def test_two_policy_instances_agree(alpha_candidates, alpha_ctx):
    assert AtmDistancePolicy().compute_priorities(alpha_candidates, alpha_ctx) == \
        AtmDistancePolicy().compute_priorities(alpha_candidates, alpha_ctx)


def test_the_policy_holds_no_state_between_passes(policy, alpha_candidates, alpha_ctx):
    first = policy.compute_priorities(alpha_candidates, alpha_ctx)
    other = MarketContext(underlying=ALPHA, spot=25200.0, atm_strike=25200.0)
    policy.compute_priorities(alpha_candidates, other)
    assert policy.compute_priorities(alpha_candidates, alpha_ctx) == first


def test_the_result_is_a_tuple(policy, alpha_candidates, alpha_ctx):
    assert isinstance(policy.compute_priorities(alpha_candidates, alpha_ctx), tuple)


def test_a_score_is_frozen(policy, alpha_candidates, alpha_ctx):
    score = policy.compute_priorities(alpha_candidates, alpha_ctx)[0]
    with pytest.raises(Exception):
        score.rank = 2  # type: ignore[misc]


# ----------------------------------------------------------------------------------------------
# Empty and degenerate inputs
# ----------------------------------------------------------------------------------------------
def test_an_empty_candidate_universe_ranks_to_nothing(policy, alpha_ctx):
    assert policy.compute_priorities([], alpha_ctx) == ()


def test_a_single_candidate_gets_rank_one(policy, alpha_ctx):
    only = leg(ALPHA, ALPHA_EXCHANGE, 25400.0, CALL_TAG, ALPHA_EXPIRY)
    scores = policy.compute_priorities([only], alpha_ctx)
    assert [s.rank for s in scores] == [1]


def test_a_candidate_from_another_underlying_raises(policy, alpha_ctx):
    """A wiring error, not a quiet skip: an empty or partial ranking would hide it."""
    foreign = leg(BETA, BETA_EXCHANGE, 80000.0, CALL_TAG, BETA_EXPIRY)
    with pytest.raises(ValueError, match="belongs to underlying"):
        policy.compute_priorities([foreign], alpha_ctx)


def test_a_non_instrument_candidate_raises(policy, alpha_ctx):
    with pytest.raises(ValueError, match="Instrument"):
        policy.compute_priorities(["ALPHAIDX25000CE"], alpha_ctx)


def test_a_non_context_raises(policy, alpha_candidates):
    with pytest.raises(ValueError, match="MarketContext"):
        policy.compute_priorities(alpha_candidates, {"spot": 25000.0})


def test_candidates_far_outside_any_window_still_rank(policy, alpha_ctx):
    """Whether a leg is a candidate is F3's question; F4 ranks what it is handed."""
    far = leg(ALPHA, ALPHA_EXCHANGE, 99000.0, CALL_TAG, ALPHA_EXPIRY)
    near = leg(ALPHA, ALPHA_EXCHANGE, 25000.0, CALL_TAG, ALPHA_EXPIRY)
    scores = policy.compute_priorities([far, near], alpha_ctx)
    assert ranked_symbols(scores) == [near.symbol, far.symbol]


# ----------------------------------------------------------------------------------------------
# MarketContext (§10.3): a frozen per-pass snapshot
# ----------------------------------------------------------------------------------------------
def test_the_context_is_frozen(alpha_ctx):
    with pytest.raises(Exception):
        alpha_ctx.spot = 25100.0  # type: ignore[misc]


def test_the_context_carries_exactly_the_agreed_fields():
    """A field carried unused is a field nobody has decided the semantics of."""
    assert set(MarketContext.__dataclass_fields__) == {"underlying", "spot", "atm_strike"}


@pytest.mark.parametrize("spot", [0.0, -1.0])
def test_a_non_positive_spot_is_rejected(spot):
    with pytest.raises(ValueError, match="positive"):
        MarketContext(underlying=ALPHA, spot=spot, atm_strike=25000.0)


@pytest.mark.parametrize("value", [float("nan"), float("inf")])
def test_a_non_finite_context_number_is_rejected(value):
    with pytest.raises(ValueError, match="finite"):
        MarketContext(underlying=ALPHA, spot=value, atm_strike=25000.0)


def test_a_blank_context_underlying_is_rejected():
    with pytest.raises(ValueError, match="non-empty"):
        MarketContext(underlying="   ", spot=25000.0, atm_strike=25000.0)


def test_a_bool_spot_is_rejected():
    with pytest.raises(ValueError, match="real number"):
        MarketContext(underlying=ALPHA, spot=True, atm_strike=25000.0)


def test_two_identical_contexts_are_equal():
    assert MarketContext(ALPHA, 25012.0, 25000.0) == MarketContext(ALPHA, 25012.0, 25000.0)


# ----------------------------------------------------------------------------------------------
# Default policy selection (§14.6, fork F12)
# ----------------------------------------------------------------------------------------------
def test_the_default_policy_name_is_atm_distance():
    assert DEFAULT_POLICY == "atm_distance"


def test_an_unset_policy_resolves_to_atm_distance():
    assert isinstance(policy_for(None), AtmDistancePolicy)


def test_naming_atm_distance_resolves_to_it():
    assert policy_for("atm_distance").name == "atm_distance"


def test_blended_is_never_silently_substituted():
    """§14.6: a policy that silently degrades to another is the forbidden silent default."""
    with pytest.raises(FrameworkConfigError) as excinfo:
        policy_for("blended")
    assert any("blended" in e for e in excinfo.value.errors)
    assert any("not implemented" in e for e in excinfo.value.errors)


def test_an_unknown_policy_name_fails_fast():
    with pytest.raises(FrameworkConfigError) as excinfo:
        policy_for("nearest_by_vibes")
    assert any("unknown" in e for e in excinfo.value.errors)


def test_a_non_string_policy_name_fails_fast():
    with pytest.raises(FrameworkConfigError):
        policy_for(7)  # type: ignore[arg-type]


def test_the_default_policy_satisfies_the_protocol():
    assert isinstance(AtmDistancePolicy(), PriorityPolicy)


# ----------------------------------------------------------------------------------------------
# Multiple underlyings
# ----------------------------------------------------------------------------------------------
def window_manager() -> WindowManager:
    return WindowManager(
        (
            WindowSpec(ALPHA, ALPHA_EXCHANGE, 200.0, CODEC_RULE, EXPIRY_RULE),
            WindowSpec(BETA, BETA_EXCHANGE, 500.0, CODEC_RULE, EXPIRY_RULE),
        ),
        {CODEC_RULE: TagSymbolCodec(call_tags=(CALL_TAG,), put_tags=(PUT_TAG,))},
        {EXPIRY_RULE: FixedExpiryCalendar({ALPHA: ALPHA_EXPIRY, BETA: BETA_EXPIRY})},
    )


def test_each_underlying_ranks_independently_from_one(policy, alpha_candidates, beta_candidates):
    ranked = rank_candidates(policy, (
        window_manager().candidates(ALPHA, 25012.0, alpha_candidates),
        window_manager().candidates(BETA, 80010.0, beta_candidates),
    ))
    assert set(ranked) == {ALPHA, BETA}
    for scores in ranked.values():
        assert [s.rank for s in scores] == list(range(1, len(scores) + 1))


def test_underlyings_do_not_share_a_rank_pool(policy, alpha_candidates, beta_candidates):
    """Ranking across underlyings would presuppose a shared pool -- that split is F5's question."""
    ranked = rank_candidates(policy, (
        window_manager().candidates(ALPHA, 25012.0, alpha_candidates),
        window_manager().candidates(BETA, 80010.0, beta_candidates),
    ))
    assert ranked[ALPHA][0].rank == 1
    assert ranked[BETA][0].rank == 1


def test_one_underlyings_candidates_do_not_affect_anothers(policy, alpha_candidates, beta_candidates):
    both = rank_candidates(policy, (
        window_manager().candidates(ALPHA, 25012.0, alpha_candidates),
        window_manager().candidates(BETA, 80010.0, beta_candidates),
    ))
    alone = rank_candidates(policy, (window_manager().candidates(ALPHA, 25012.0, alpha_candidates),))
    assert both[ALPHA] == alone[ALPHA]


def test_an_unresolved_window_ranks_to_an_empty_tuple(policy, alpha_candidates):
    result = window_manager().candidates(ALPHA, None, alpha_candidates)
    assert result.status is WindowStatus.NO_SPOT
    assert rank_candidates(policy, (result,)) == {ALPHA: ()}


def test_a_duplicate_window_result_raises(policy, alpha_candidates):
    result = window_manager().candidates(ALPHA, 25012.0, alpha_candidates)
    with pytest.raises(ValueError, match="duplicate"):
        rank_candidates(policy, (result, result))


def test_rank_candidates_rejects_a_non_window_result(policy):
    with pytest.raises(ValueError, match="WindowResult"):
        rank_candidates(policy, ({"underlying": ALPHA},))


# ----------------------------------------------------------------------------------------------
# The F3 -> F4 hand-off
# ----------------------------------------------------------------------------------------------
def test_the_context_adapter_reads_f3s_spot_and_atm(alpha_candidates):
    result = window_manager().candidates(ALPHA, 25012.0, alpha_candidates)
    ctx = market_context_from_window(result)
    assert (ctx.underlying, ctx.spot, ctx.atm_strike) == (ALPHA, 25012.0, 25000.0)


def test_the_adapter_never_re_resolves_an_atm(alpha_candidates):
    """§15 states the ATM rule once; F4 must read it, not restate it."""
    result = window_manager().candidates(ALPHA, 25025.0, alpha_candidates)
    assert market_context_from_window(result).atm_strike == result.atm_strike


@pytest.mark.parametrize("spot", [None, 0.0])
def test_the_adapter_refuses_an_unresolved_window(alpha_candidates, spot):
    result = window_manager().candidates(ALPHA, spot, alpha_candidates)
    with pytest.raises(ValueError, match="NO_SPOT"):
        market_context_from_window(result)


def test_the_adapter_refuses_a_non_window_result():
    with pytest.raises(ValueError, match="WindowResult"):
        market_context_from_window({"underlying": ALPHA})


def test_the_full_f3_to_f4_pass_is_deterministic(policy, alpha_candidates):
    rng = random.Random(20260826)
    result = window_manager().candidates(ALPHA, 25012.0, alpha_candidates)
    expected = policy.compute_priorities(result.candidates, market_context_from_window(result))
    for _ in range(10):
        shuffled = list(alpha_candidates)
        rng.shuffle(shuffled)
        again = window_manager().candidates(ALPHA, 25012.0, shuffled)
        assert policy.compute_priorities(again.candidates, market_context_from_window(again)) == expected


# ----------------------------------------------------------------------------------------------
# Scope boundary, asserted on the source
# ----------------------------------------------------------------------------------------------
def module_source() -> str:
    return MODULE_PATH.read_text(encoding="utf-8")


def module_tree() -> ast.AST:
    return ast.parse(module_source())


def executable_source() -> str:
    """The module with every docstring stripped: prose may cite a later phase, code may not."""
    tree = module_tree()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                node.body = body[1:] or [ast.Pass()]
    return ast.unparse(tree)


def test_the_source_scan_is_not_vacuous():
    stripped = executable_source()
    assert len(stripped) > 2000
    assert "rank_scores" in stripped
    assert "among candidates, which matter most" not in stripped, "docstrings must be stripped"


def test_no_index_exchange_or_option_tag_literal_in_executable_code():
    stripped = executable_source()
    for token in ("NIFTY", "SENSEX", "BANKNIFTY", "NFO", "BFO", "NSE", "BSE", "'CE'", "'PE'"):
        assert token not in stripped, f"priority_policy.py hardcodes {token}"


def test_no_budget_or_capability_concept_appears():
    """F4 ranks; it must not know tbt_budget, premium slots, connections, or channels."""
    stripped = executable_source().lower()
    for token in ("tbt", "symbols_per_connection", "max_connections", "max_channels",
                  "effective_budget", "capability", "allocate", "depth_for"):
        assert token not in stripped, f"priority_policy.py references {token!r}"


def test_no_allocation_or_overlay_concept_appears():
    stripped = executable_source().lower()
    for token in ("hysteresis", "cooldown", "overlay", "displace", "incumbent", "challenger",
                  "subscribe", "subscription", "reconcile", "adapter", "wire_symbol"):
        assert token not in stripped, f"priority_policy.py references {token!r}"


def test_no_depth_tier_is_assigned():
    stripped = executable_source()
    for token in ("DepthType", "PREMIUM", "STANDARD", "depth"):
        assert token not in stripped, f"priority_policy.py references {token}"


def test_module_imports_no_capability_layer_and_no_recorder():
    for node in ast.walk(module_tree()):
        if isinstance(node, ast.ImportFrom):
            assert node.module not in ("capabilities", "capability_layer")
            assert not (node.module or "").startswith("market_depth_recorder")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("market_depth_recorder")


def test_module_imports_no_runtime_or_io_machinery():
    banned = {"time", "datetime", "random", "socket", "os", "threading", "queue", "asyncio",
              "sqlite3", "subprocess", "requests", "httpx", "websocket"}
    for node in ast.walk(module_tree()):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in banned, f"imports {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            assert root not in banned, f"imports from {node.module}"


def test_module_opens_no_resource():
    banned = {"open", "connect", "Thread", "Popen", "Queue", "socket", "Session"}
    for node in ast.walk(module_tree()):
        if isinstance(node, ast.Call):
            name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            assert name not in banned, f"priority_policy.py calls {name}()"


def test_ranking_is_not_reimplemented_by_a_later_module():
    """F4 owns ranking and nothing else does.

    The old form of this guard named the modules still ahead of F4; F8's orchestrator.py was the last
    of them, so the durable form asserts what the guard was really protecting -- that a later layer
    consumes ``rank_candidates`` rather than growing a ranking of its own.
    """
    package_dir = MODULE_PATH.parent
    definers = []
    for path in sorted(package_dir.glob("*.py")):
        if path.stem in ("priority_policy", "__init__"):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name in ("compute_priorities", "rank_scores", "rank_candidates"):
                    definers.append(f"{path.name}:{node.name}")
    assert not definers, f"ranking is reimplemented in {definers}"


def test_the_policy_exposes_no_allocation_method():
    public = {n for n in dir(AtmDistancePolicy) if not n.startswith("_")}
    assert public == {"name", "compute_priorities"}


def test_the_score_carries_no_tier_or_slot_field():
    assert set(PriorityScore.__dataclass_fields__) == {"instrument", "score", "rank"}
