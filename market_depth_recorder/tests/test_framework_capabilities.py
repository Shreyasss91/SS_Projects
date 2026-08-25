"""F1 tests for the broker-capability dataclasses (Plan_002 §10.1, §16).

Two things are pinned here beyond ordinary field validation:

* ``UNLIMITED_BUDGET`` is an ``int``, not ``float('inf')`` -- so downstream ``-> int`` contracts and
  ``min()`` arithmetic stay honest (§10.1).
* F1 exposes **no** budget arithmetic and **no** eligibility resolution. Both are F2. The approval for
  F1 was explicit that capability dataclasses must not become the capability layer, so the absence is
  asserted rather than left to review.
"""

from __future__ import annotations

import dataclasses

import pytest

from market_depth_recorder.market_depth_framework import (
    UNLIMITED_BUDGET,
    BrokerCapability,
    PremiumTier,
    StandardTier,
)

# The FROZEN FYERS facts (Documents/patches/tbt_concurrency_reconciliation_20260714.md).
FYERS_PREMIUM = dict(depth=50, symbols_per_connection=5, max_connections=3, max_channels=50)


def make_capability(**overrides) -> BrokerCapability:
    fields = {
        "broker": "fyers",
        "premium": PremiumTier(**FYERS_PREMIUM),
        "standard": StandardTier(depth=5),
        "premium_exchanges": frozenset({"NSE", "NFO"}),
    }
    fields.update(overrides)
    return BrokerCapability(**fields)


# ----------------------------------------------------------------------------- UNLIMITED_BUDGET ----
def test_unlimited_budget_is_an_int_not_infinity():
    """§10.1: a float sentinel would silently promote budget arithmetic to float."""
    assert isinstance(UNLIMITED_BUDGET, int)
    assert not isinstance(UNLIMITED_BUDGET, bool)
    assert UNLIMITED_BUDGET != float("inf")


def test_unlimited_budget_survives_int_arithmetic():
    """The property that matters downstream: min() against it yields an int."""
    assert isinstance(min(UNLIMITED_BUDGET, 15), int)
    assert min(UNLIMITED_BUDGET, 15) == 15
    assert UNLIMITED_BUDGET > 10_000


# ------------------------------------------------------------------------------------- tiers ----
def test_premium_tier_carries_the_frozen_fyers_facts():
    tier = PremiumTier(**FYERS_PREMIUM)
    assert (tier.depth, tier.symbols_per_connection, tier.max_connections) == (50, 5, 3)
    assert tier.max_channels == 50


def test_tiers_are_frozen():
    with pytest.raises(dataclasses.FrozenInstanceError):
        PremiumTier(**FYERS_PREMIUM).depth = 20  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        StandardTier(depth=5).depth = 20  # type: ignore[misc]


@pytest.mark.parametrize("key", list(FYERS_PREMIUM))
@pytest.mark.parametrize("bad", [0, -1, 1.5, "5", None, True])
def test_premium_tier_rejects_non_positive_int_fields(key, bad):
    fields = dict(FYERS_PREMIUM)
    fields[key] = bad
    with pytest.raises(ValueError, match=key):
        PremiumTier(**fields)


@pytest.mark.parametrize("bad", [0, -1, 1.5, "5", None, True])
def test_standard_tier_rejects_non_positive_int_depth(bad):
    with pytest.raises(ValueError, match="depth"):
        StandardTier(depth=bad)


# -------------------------------------------------------------------------- BrokerCapability ----
def test_capability_defaults_to_unlimited_total_budget():
    """Absent means 'no account-wide cap beyond the connection math' -- a documented semantic for an
    optional key, not a silent default for a required one."""
    assert make_capability().total_symbol_budget == UNLIMITED_BUDGET


def test_capability_carries_premium_exchanges_without_resolving_them():
    """F13 data is present; the eligibility *decision* is F2."""
    cap = make_capability()
    assert cap.premium_exchanges == frozenset({"NSE", "NFO"})
    assert "BFO" not in cap.premium_exchanges


def test_capability_rejects_premium_depth_not_deeper_than_standard():
    with pytest.raises(ValueError, match="must be >"):
        make_capability(premium=PremiumTier(**{**FYERS_PREMIUM, "depth": 5}))
    with pytest.raises(ValueError, match="must be >"):
        make_capability(premium=PremiumTier(**{**FYERS_PREMIUM, "depth": 3}))


@pytest.mark.parametrize("bad", ["", "  ", None, 5])
def test_capability_rejects_malformed_broker_name(bad):
    with pytest.raises(ValueError, match="broker"):
        make_capability(broker=bad)


@pytest.mark.parametrize("bad", [0, -1, "15", None, True])
def test_capability_rejects_non_positive_total_budget(bad):
    with pytest.raises(ValueError, match="total_symbol_budget"):
        make_capability(total_symbol_budget=bad)


def test_capability_rejects_wrong_tier_types():
    with pytest.raises(ValueError, match="premium"):
        make_capability(premium={"depth": 50})
    with pytest.raises(ValueError, match="standard"):
        make_capability(standard={"depth": 5})


def test_capability_rejects_non_frozenset_exchanges():
    """Mutable membership would let a broker fact drift after validation."""
    with pytest.raises(ValueError, match="premium_exchanges"):
        make_capability(premium_exchanges={"NSE", "NFO"})


def test_capability_is_frozen():
    with pytest.raises(dataclasses.FrozenInstanceError):
        make_capability().total_symbol_budget = 15  # type: ignore[misc]


# ------------------------------------------------------------- F1/F2 boundary (scope guard) ----
def test_f1_exposes_no_budget_arithmetic_and_no_eligibility_resolution():
    """The Broker Capabilities *layer* is F2 (Plan_002 §22). These names must not appear yet."""
    for forbidden in ("effective_budget", "supports_premium", "premium_budget", "is_eligible"):
        assert not hasattr(BrokerCapability, forbidden), f"{forbidden} belongs to phase F2, not F1"


def test_max_channels_is_carried_but_no_budget_multiplies_it():
    """Multiplying channels into a budget is the disproven 5x50=250 model. F1 has no budget
    arithmetic at all, so there is nothing that could multiply it -- asserted so F2 inherits the
    constraint rather than rediscovering it."""
    cap = make_capability()
    assert cap.premium.max_channels == 50
    real_ceiling = cap.premium.symbols_per_connection * cap.premium.max_connections
    assert real_ceiling == 15
    assert real_ceiling != cap.premium.symbols_per_connection * cap.premium.max_channels
