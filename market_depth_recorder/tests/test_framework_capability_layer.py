"""F2 tests for the Broker Capabilities layer (Plan_002 §10.1, §13.1, §13.2, §16).

Everything here is offline and deterministic: no live FYERS, no WebSocket, no market feed, no network,
no credentials. The layer is pure arithmetic over validated configuration, which is exactly why it can
be pinned this hard.

The load-bearing assertions, restated so a future reader does not have to reconstruct them:

* ``effective_budget = min(total_symbol_budget, max_connections * symbols_per_connection)``, and for
  FYERS that is ``min(UNLIMITED, 3 * 5) = 15``.
* ``max_channels`` never participates. The disproven model was ``5 * 50 = 250``.
* Premium eligibility is a broker/exchange fact: NFO yes, BFO no.
* ``UNLIMITED_BUDGET`` stays an ``int`` through the arithmetic.
* 15 is derived from configuration, never a constant in framework code.
"""

from __future__ import annotations

import ast
import itertools
from pathlib import Path

import pytest

from market_depth_recorder.market_depth_framework import (
    UNLIMITED_BUDGET,
    BrokerCapability,
    BrokerCapabilityLayer,
    DepthType,
    FrameworkConfigError,
    Instrument,
    PremiumTier,
    StandardTier,
    build_capability_layers,
    capability_layer_for,
    check_premium_floor_feasible,
    eligible_underlyings,
    load_framework_config,
    validate_framework_config,
)
from market_depth_recorder.market_depth_framework import capability_layer as layer_module

# The FROZEN FYERS facts (Documents/patches/tbt_concurrency_reconciliation_20260714.md).
FYERS_PREMIUM = dict(depth=50, symbols_per_connection=5, max_connections=3, max_channels=50)
FYERS_PREMIUM_EXCHANGES = frozenset({"NSE", "NFO"})

EXAMPLE_CONFIG = (
    Path(layer_module.__file__).resolve().parent / "config.example.yaml"
)


def make_capability(**overrides) -> BrokerCapability:
    fields = {
        "broker": "fyers",
        "premium": PremiumTier(**FYERS_PREMIUM),
        "standard": StandardTier(depth=5),
        "premium_exchanges": FYERS_PREMIUM_EXCHANGES,
    }
    fields.update(overrides)
    return BrokerCapability(**fields)


def make_layer(**overrides) -> BrokerCapabilityLayer:
    return BrokerCapabilityLayer(make_capability(**overrides))


# ============================================================ 1. FYERS: 5 x 3 -> effective_budget 15
def test_fyers_effective_budget_is_fifteen():
    """5 symbols per connection x 3 connections = 15 (§16)."""
    assert make_layer().effective_budget == 15


def test_effective_budget_is_derived_from_the_configured_connection_math():
    """Not a constant: change the broker's connection facts and the budget follows."""
    other = make_layer(premium=PremiumTier(**{**FYERS_PREMIUM, "symbols_per_connection": 20,
                                             "max_connections": 1}))
    assert other.effective_budget == 20
    full_chain = make_layer(premium=PremiumTier(**{**FYERS_PREMIUM, "symbols_per_connection": 50,
                                                  "max_connections": 2}))
    assert full_chain.effective_budget == 100


def test_effective_budget_is_an_int():
    budget = make_layer().effective_budget
    assert isinstance(budget, int) and not isinstance(budget, bool)


def test_effective_budget_is_stable_across_reads():
    """Computed once from frozen inputs, so a rebalance pass cannot see it drift mid-session."""
    layer = make_layer()
    assert len({layer.effective_budget for _ in range(50)}) == 1


# ================================================================ 2. max_channels never buys capacity
def test_max_channels_does_not_increase_the_budget():
    """The disproven model was 5 per *channel* x 50 channels = 250. Channels are a pause/resume
    grouping and carry no capacity."""
    baseline = make_layer().effective_budget
    for channels in (1, 2, 50, 500, 10_000):
        widened = make_layer(premium=PremiumTier(**{**FYERS_PREMIUM, "max_channels": channels}))
        assert widened.effective_budget == baseline == 15


def test_the_disproven_channel_model_is_not_what_the_layer_computes():
    layer = make_layer()
    premium = layer.capability.premium
    assert layer.effective_budget == premium.symbols_per_connection * premium.max_connections
    assert layer.effective_budget != premium.symbols_per_connection * premium.max_channels
    assert premium.symbols_per_connection * premium.max_channels == 250


def test_no_framework_source_file_multiplies_max_channels():
    """A guard on the *source*, not just the result: no expression anywhere in the package may put
    max_channels on either side of a multiplication."""
    package_dir = Path(layer_module.__file__).resolve().parent
    for path in sorted(package_dir.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
                rendered = ast.unparse(node)
                assert "max_channels" not in rendered, (
                    f"{path.name} multiplies max_channels: {rendered}"
                )


# ==================================================== 3 & 4. total_symbol_budget interacts via min()
def test_total_budget_below_connection_capacity_caps_the_budget():
    """An account-wide cap tighter than the connection math wins."""
    assert make_layer(total_symbol_budget=8).effective_budget == 8
    assert make_layer(total_symbol_budget=1).effective_budget == 1


def test_total_budget_above_connection_capacity_is_capped_by_connections():
    """A generous account-wide cap does not conjure connections that do not exist."""
    for generous in (16, 100, 250, 10_000):
        assert make_layer(total_symbol_budget=generous).effective_budget == 15


def test_total_budget_equal_to_connection_capacity():
    assert make_layer(total_symbol_budget=15).effective_budget == 15


@pytest.mark.parametrize("per_conn,conns,total", itertools.product((1, 5, 20, 50), (1, 3, 8),
                                                                   (1, 7, 15, 400)))
def test_effective_budget_is_always_the_minimum_of_the_two_bounds(per_conn, conns, total):
    """Property test over the whole small grid: the formula holds, the result is a positive int, and
    it never exceeds either bound."""
    layer = make_layer(
        premium=PremiumTier(depth=50, symbols_per_connection=per_conn, max_connections=conns,
                            max_channels=50),
        total_symbol_budget=total,
    )
    expected = min(total, per_conn * conns)
    assert layer.effective_budget == expected
    assert isinstance(layer.effective_budget, int)
    assert 0 < layer.effective_budget <= total
    assert layer.effective_budget <= per_conn * conns


# ============================================================================= 5. UNLIMITED_BUDGET
def test_omitted_total_budget_means_unlimited_and_the_connections_decide():
    layer = make_layer()
    assert layer.capability.total_symbol_budget == UNLIMITED_BUDGET
    assert layer.effective_budget == 15
    assert layer.has_account_wide_cap is False


def test_declared_total_budget_reports_an_account_wide_cap():
    assert make_layer(total_symbol_budget=8).has_account_wide_cap is True
    # A declared value that happens to equal the sentinel is still "no extra cap" -- the sentinel is
    # the documented meaning of the number, not a marker of how it was supplied.
    assert make_layer(total_symbol_budget=UNLIMITED_BUDGET).has_account_wide_cap is False


def test_unlimited_budget_does_not_promote_the_arithmetic_to_float():
    """The reason the sentinel is an int and not float('inf'): min() must return an int."""
    layer = make_layer(total_symbol_budget=UNLIMITED_BUDGET)
    assert isinstance(layer.effective_budget, int)
    assert not isinstance(layer.effective_budget, float)


def test_unlimited_budget_never_surfaces_as_a_real_budget():
    """With a real connection bound present the connection math always wins, so no allocator is ever
    handed 2**31-1 slots to fill. The sentinel means 'no extra cap', never a quantity to spend."""
    for per_conn, conns in ((5, 3), (50, 3), (1000, 1000)):
        layer = make_layer(premium=PremiumTier(depth=50, symbols_per_connection=per_conn,
                                               max_connections=conns, max_channels=50))
        assert layer.effective_budget == per_conn * conns < UNLIMITED_BUDGET
        assert isinstance(layer.effective_budget, int)


# ================================================================= 6, 7, 8. per-exchange eligibility
def test_nfo_is_premium_eligible():
    assert make_layer().supports_premium("NFO") is True


def test_bfo_is_not_premium_eligible():
    """BFO has no TBT deep book, so a SENSEX leg can hold the baseline but never be promoted (§13.1)."""
    assert make_layer().supports_premium("BFO") is False


@pytest.mark.parametrize("exchange,expected", [("NSE", True), ("NFO", True), ("BFO", False),
                                               ("BSE", False), ("MCX", False), ("CDS", False)])
def test_eligibility_follows_the_configured_set_only(exchange, expected):
    assert make_layer().supports_premium(exchange) is expected


def test_an_ineligible_exchange_has_zero_premium_capacity():
    layer = make_layer()
    assert layer.premium_capacity("BFO") == 0
    assert layer.premium_capacity("NFO") == 15


def test_an_ineligible_exchange_still_gets_full_standard_baseline():
    """Eligibility governs the premium overlay only, never the baseline (§13.1)."""
    layer = make_layer()
    assert layer.depth_for("BFO", DepthType.STANDARD) == 5
    assert DepthType.STANDARD in layer.available_tiers("BFO")


def test_available_tiers_is_deterministic_and_baseline_first():
    layer = make_layer()
    assert layer.available_tiers("NFO") == (DepthType.STANDARD, DepthType.PREMIUM)
    assert layer.available_tiers("BFO") == (DepthType.STANDARD,)


def test_depth_for_reports_what_the_broker_will_actually_serve():
    layer = make_layer()
    assert layer.depth_for("NFO", DepthType.PREMIUM) == 50
    assert layer.depth_for("NFO", DepthType.STANDARD) == 5
    # A premium request on an ineligible exchange resolves to what really arrives: 5 levels.
    assert layer.depth_for("BFO", DepthType.PREMIUM) == 5


def test_eligibility_matching_is_case_sensitive_by_design():
    """Case-folding would be a silent normalization; the contract everywhere else is to fail visibly."""
    layer = make_layer()
    assert layer.supports_premium("NFO") is True
    assert layer.supports_premium("nfo") is False


@pytest.mark.parametrize("bad", ["", "   ", None, 5, ["NFO"]])
def test_a_malformed_exchange_raises_rather_than_answering_false(bad):
    """Returning False would hide a caller bug behind a plausible-looking answer."""
    with pytest.raises(ValueError, match="exchange"):
        make_layer().supports_premium(bad)


def test_depth_for_rejects_a_non_depthtype_tier():
    with pytest.raises(TypeError, match="DepthType"):
        make_layer().depth_for("NFO", "premium")


# ================================================================ 9 & 10. configuration fail-fast
def _cfg(**broker_overrides):
    """A minimal valid framework config root, with the FYERS block overridable."""
    fyers = {
        "premium": dict(FYERS_PREMIUM),
        "standard": {"depth": 5},
        "premium_exchanges": ["NSE", "NFO"],
    }
    fyers.update(broker_overrides)
    return {
        "market_depth_framework": {
            "enabled": False,
            "broker_capabilities": {"fyers": fyers},
            "priority_policy": {"policy": "atm_distance"},
            "budget_allocator": {"policy": "weighted", "min_per_underlying": 2,
                                 "weights": {"NIFTY": 1.0}, "redistribute_unspent": True},
            "depth_allocator": {"churn_cooldown_seconds": 30, "hysteresis_buffer": 2,
                                "history_limit": 200},
            "rebalance": {"trigger": "both", "interval_seconds": 5},
        }
    }


def test_the_layer_is_built_from_validated_config_end_to_end():
    config = validate_framework_config(_cfg())
    layer = capability_layer_for(config, "fyers")
    assert layer.broker == "fyers"
    assert layer.effective_budget == 15
    assert layer.supports_premium("NFO") is True
    assert layer.supports_premium("BFO") is False


def test_build_capability_layers_wraps_every_configured_broker():
    layers = build_capability_layers(validate_framework_config(_cfg()))
    assert set(layers) == {"fyers"}
    assert layers["fyers"].effective_budget == 15


@pytest.mark.parametrize("bad_premium", [
    {"depth": 50, "symbols_per_connection": 0, "max_connections": 3, "max_channels": 50},
    {"depth": 50, "symbols_per_connection": 5, "max_connections": -1, "max_channels": 50},
    {"depth": 50, "symbols_per_connection": 5, "max_connections": 3, "max_channels": 0},
    {"depth": 0, "symbols_per_connection": 5, "max_connections": 3, "max_channels": 50},
])
def test_invalid_capability_values_fail_validation(bad_premium):
    with pytest.raises(FrameworkConfigError):
        validate_framework_config(_cfg(premium=bad_premium))


def test_premium_depth_not_deeper_than_standard_fails_validation():
    shallow = {**FYERS_PREMIUM, "depth": 5}
    with pytest.raises(FrameworkConfigError) as excinfo:
        validate_framework_config(_cfg(premium=shallow))
    assert any("must be >" in e for e in excinfo.value.errors)


@pytest.mark.parametrize("missing", ["premium", "standard", "premium_exchanges"])
def test_missing_required_capability_configuration_fails_validation(missing):
    root = _cfg()
    del root["market_depth_framework"]["broker_capabilities"]["fyers"][missing]
    with pytest.raises(FrameworkConfigError):
        validate_framework_config(root)


@pytest.mark.parametrize("missing_key", list(FYERS_PREMIUM))
def test_missing_premium_tier_key_fails_validation(missing_key):
    premium = {k: v for k, v in FYERS_PREMIUM.items() if k != missing_key}
    with pytest.raises(FrameworkConfigError) as excinfo:
        validate_framework_config(_cfg(premium=premium))
    assert any(missing_key in e for e in excinfo.value.errors)


def test_an_unconfigured_broker_fails_fast_rather_than_guessing_a_budget():
    config = validate_framework_config(_cfg())
    with pytest.raises(FrameworkConfigError) as excinfo:
        capability_layer_for(config, "zerodha")
    assert any("zerodha" in e for e in excinfo.value.errors)


@pytest.mark.parametrize("bad", ["", "   ", None, 7])
def test_a_malformed_broker_name_fails_fast(bad):
    config = validate_framework_config(_cfg())
    with pytest.raises(FrameworkConfigError):
        capability_layer_for(config, bad)


def test_the_layer_rejects_a_non_capability():
    with pytest.raises(TypeError, match="BrokerCapability"):
        BrokerCapabilityLayer({"premium": {"depth": 50}})


def test_capability_facts_are_not_duplicated_in_allocator_config():
    """No premium_eligible / premium_budget key exists in allocator config: eligibility and the budget
    are broker facts, and hand-copying either would let config drift from the broker (§17)."""
    config = validate_framework_config(_cfg())
    for section in (config.budget_allocator, config.depth_allocator, config.priority_policy):
        for forbidden in ("premium_eligible", "premium_budget", "tbt_budget", "effective_budget",
                          "premium_exchanges", "symbols_per_connection", "max_connections"):
            assert forbidden not in section


# ==================================================================== the shipped reference config
def test_the_reference_config_example_validates_and_yields_fifteen():
    """End-to-end proof that the FYERS facts reach a budget of 15 through configuration alone."""
    config = load_framework_config(str(EXAMPLE_CONFIG))
    assert config is not None
    layer = capability_layer_for(config, "fyers")
    assert layer.effective_budget == 15
    assert layer.premium_depth == 50
    assert layer.standard_depth == 5
    assert layer.supports_premium("NFO") is True
    assert layer.supports_premium("BFO") is False


def test_the_reference_config_leaves_the_framework_disabled():
    """It is a copy source, not a live config; wiring it in is F8."""
    config = load_framework_config(str(EXAMPLE_CONFIG))
    assert config is not None and config.enabled is False


# ======================================================= §13.2 startup feasibility over underlyings
NIFTY_NFO_SENSEX_BFO = {"NIFTY": "NFO", "SENSEX": "BFO"}


def test_eligible_underlyings_excludes_the_ineligible_exchange():
    assert eligible_underlyings(make_layer(), NIFTY_NFO_SENSEX_BFO) == ("NIFTY",)


def test_eligible_underlyings_preserves_configuration_order():
    mapping = {"ALPHA": "NFO", "BETA": "BFO", "GAMMA": "NSE", "DELTA": "NFO"}
    assert eligible_underlyings(make_layer(), mapping) == ("ALPHA", "GAMMA", "DELTA")


def test_the_floor_is_scoped_to_eligible_underlyings_only():
    """Read over all configured underlyings the check would demand a floor for SENSEX and contradict
    §13.1's 'SENSEX gets 0' (§13.2)."""
    assert check_premium_floor_feasible(make_layer(), NIFTY_NFO_SENSEX_BFO, 2) == ("NIFTY",)
    # 15 // 2 = 7 eligible underlyings would fit at a floor of 2; one eligible underlying always does.
    assert check_premium_floor_feasible(make_layer(), NIFTY_NFO_SENSEX_BFO, 15) == ("NIFTY",)


def test_an_infeasible_floor_fails_fast():
    with pytest.raises(FrameworkConfigError) as excinfo:
        check_premium_floor_feasible(make_layer(), NIFTY_NFO_SENSEX_BFO, 16)
    assert any("infeasible" in e for e in excinfo.value.errors)


def test_the_floor_check_counts_only_eligible_underlyings():
    """Eight underlyings, four eligible: a floor of 4 needs 16 > 15 and must fail; a floor of 3 fits."""
    mapping = {f"U{i}": ("NFO" if i % 2 == 0 else "BFO") for i in range(8)}
    assert len(eligible_underlyings(make_layer(), mapping)) == 4
    assert len(check_premium_floor_feasible(make_layer(), mapping, 3)) == 4
    with pytest.raises(FrameworkConfigError):
        check_premium_floor_feasible(make_layer(), mapping, 4)


def test_a_zero_floor_is_always_feasible():
    mapping = {f"U{i}": "NFO" for i in range(100)}
    assert len(check_premium_floor_feasible(make_layer(), mapping, 0)) == 100


def test_no_eligible_underlying_makes_any_floor_feasible():
    """An all-BFO deployment is a legitimate degraded configuration: everything runs at baseline."""
    assert check_premium_floor_feasible(make_layer(), {"SENSEX": "BFO"}, 10) == ()


@pytest.mark.parametrize("bad", [-1, 2.5, "2", None, True])
def test_the_floor_check_rejects_a_malformed_floor(bad):
    # __str__ is a count summary; the operator-facing text lives in .errors (as in F1).
    with pytest.raises(FrameworkConfigError) as excinfo:
        check_premium_floor_feasible(make_layer(), NIFTY_NFO_SENSEX_BFO, bad)
    assert any("min_per_underlying" in e for e in excinfo.value.errors)


@pytest.mark.parametrize("mapping", [{"": "NFO"}, {"NIFTY": ""}, {"NIFTY": None}, {"NIFTY": 5}])
def test_a_malformed_underlying_mapping_fails_fast(mapping):
    """A missing exchange would silently make an underlying ineligible -- the quiet wrong answer the
    fail-fast contract exists to prevent."""
    with pytest.raises(FrameworkConfigError):
        eligible_underlyings(make_layer(), mapping)


def test_the_floor_check_rejects_a_non_mapping():
    with pytest.raises(FrameworkConfigError) as excinfo:
        eligible_underlyings(make_layer(), [("NIFTY", "NFO")])
    assert any("mapping" in e for e in excinfo.value.errors)


# ================================================= 11. independence from underlyings/ranking/policy
def test_the_layer_class_knows_nothing_about_underlyings_or_allocation():
    """The layer answers capability questions. Everything below belongs to F3-F6."""
    forbidden = (
        "underlyings", "underlying", "strikes", "strike", "rank", "ranking", "priority",
        "score", "window", "atm", "spot", "subscribe", "subscription", "allocate",
        "allocation", "policy", "weights", "candidates",
    )
    for name in dir(BrokerCapabilityLayer):
        if name.startswith("_"):
            continue
        for token in forbidden:
            assert token not in name.lower(), (
                f"BrokerCapabilityLayer.{name} reads like {token!r} -- that belongs to a later phase"
            )


def test_the_layer_never_touches_an_instrument():
    """It takes exchange codes, never legs: eligibility is per-exchange, not per-strike."""
    source = Path(layer_module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for arg in node.args.args + node.args.kwonlyargs:
                annotation = ast.unparse(arg.annotation) if arg.annotation else ""
                assert "Instrument" not in annotation, (
                    f"{node.name}() takes an Instrument; the capability layer is per-exchange"
                )


def test_the_layer_answers_identically_for_two_legs_on_the_same_exchange():
    """Corollary of the above, asserted behaviourally: strike and expiry cannot change the answer."""
    layer = make_layer()
    near = Instrument("NIFTY", "NFO", "N1", "28AUG26", 24000.0, "CE")
    far = Instrument("NIFTY", "NFO", "N2", "25SEP26", 31000.0, "PE")
    assert layer.supports_premium(near.exchange) == layer.supports_premium(far.exchange)
    assert layer.premium_capacity(near.exchange) == layer.premium_capacity(far.exchange)


def test_no_later_phase_layer_exists_yet():
    """F2 stopped at the Broker Capabilities boundary; F4 added priority_policy.py and no more. The
    list shortens by exactly one module per phase, so an early arrival still fails here."""
    package_dir = Path(layer_module.__file__).resolve().parent
    present = {p.stem for p in package_dir.glob("*.py")}
    for module in ("budget_allocator", "depth_allocator",
                   "subscription", "subscription_manager", "broker_adapter", "orchestrator"):
        assert module not in present, f"{module}.py belongs to F5 or later"


def test_the_layer_exposes_no_allocation_behaviour():
    for forbidden in ("allocate_budget", "allocate_depth", "compute_priorities", "rank_scores",
                      "reconcile", "candidates_for"):
        assert not hasattr(BrokerCapabilityLayer, forbidden)
    for forbidden in ("allocate_budget", "allocate_depth", "compute_priorities", "rank_scores"):
        assert not hasattr(layer_module, forbidden)


# ============================================================================== 12. determinism / IO
def test_repeated_construction_yields_identical_answers():
    first, second = make_layer(), make_layer()
    assert first.effective_budget == second.effective_budget
    assert first.available_tiers("NFO") == second.available_tiers("NFO")
    assert first.premium_capacity("BFO") == second.premium_capacity("BFO")


def test_the_layer_holds_no_mutable_state():
    """__slots__ with no setters: a caller cannot bolt state onto the layer mid-session."""
    layer = make_layer()
    with pytest.raises(AttributeError):
        layer.effective_budget = 250  # type: ignore[misc]
    with pytest.raises(AttributeError):
        layer.extra = "state"  # type: ignore[attr-defined]


def test_the_wrapped_capability_cannot_be_mutated_through_the_layer():
    import dataclasses

    with pytest.raises(dataclasses.FrozenInstanceError):
        make_layer().capability.total_symbol_budget = 250  # type: ignore[misc]


def test_the_layer_module_performs_no_io():
    """No open/socket/thread/subprocess/queue/DB call anywhere in the module's source."""
    tree = ast.parse(Path(layer_module.__file__).read_text(encoding="utf-8"))
    banned_calls = {"open", "connect", "Thread", "Popen", "run", "Queue", "socket"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(func, ast.Name) else (
                func.attr if isinstance(func, ast.Attribute) else "")
            assert name not in banned_calls, f"capability_layer.py calls {name}()"
    imported = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import)
                for a in n.names}
    imported |= {(n.module or "").split(".")[0] for n in ast.walk(tree)
                 if isinstance(n, ast.ImportFrom) and n.level == 0}
    for module in ("socket", "threading", "subprocess", "sqlite3", "queue", "asyncio", "yaml"):
        assert module not in imported, f"capability_layer.py imports {module}"


def test_no_hardcoded_fifteen_in_framework_source():
    """15 must be derived from configuration, never a framework constant. Docstrings may cite it."""
    package_dir = Path(layer_module.__file__).resolve().parent
    for path in sorted(package_dir.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        _strip_docstrings(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
                if node.value.value == 15:
                    names = [ast.unparse(t) for t in node.targets]
                    raise AssertionError(f"{path.name} hardcodes 15 as {names}")
            if isinstance(node, ast.AnnAssign) and isinstance(node.value, ast.Constant):
                if node.value.value == 15:
                    raise AssertionError(f"{path.name} hardcodes 15 as {ast.unparse(node.target)}")


def _strip_docstrings(tree: ast.AST) -> None:
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                node.body = body[1:] or [ast.Pass()]


def test_repr_is_informative_and_states_the_derived_budget():
    text = repr(make_layer())
    assert "fyers" in text and "effective_budget=15" in text
