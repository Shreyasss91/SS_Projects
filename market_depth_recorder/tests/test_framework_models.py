"""F1 tests for the framework data models (Plan_002 §9, fork F10).

The load-bearing assertion in this file is that ``Instrument`` carries **no depth**. That is fork F10,
and it is the fix for §21 D-9: the recorder's ``_subscriptions`` map keys on the wire symbol, whose
``:50`` suffix encodes depth, so a depth transition changes the key and one leg looks like two.
"""

from __future__ import annotations

import dataclasses

import pytest

from market_depth_recorder.market_depth_framework import DepthType, Instrument


def make_instrument(**overrides) -> Instrument:
    """A valid leg; tests override one field at a time so a failure names the field it came from."""
    fields = {
        "underlying": "NIFTY",
        "exchange": "NFO",
        "symbol": "NIFTY28AUG2524000CE",
        "expiry": "28-AUG-25",
        "strike": 24000.0,
        "option_type": "CE",
    }
    fields.update(overrides)
    return Instrument(**fields)


# ---------------------------------------------------------------------------------- DepthType ----
def test_depth_type_is_a_tier_not_a_level_count():
    """The tier must not carry a number: 50 is a FYERS/NFO fact, and a broker whose premium tier is
    20 must reuse this enum unchanged."""
    assert {d.value for d in DepthType} == {"standard", "premium"}
    for member in DepthType:
        assert isinstance(member.value, str)
        assert not member.value.isdigit()


def test_depth_type_str_is_the_tier_name():
    assert str(DepthType.STANDARD) == "standard"
    assert str(DepthType.PREMIUM) == "premium"


# --------------------------------------------------------------------------------- Instrument ----
def test_instrument_has_no_depth_field():
    """Fork F10, stated directly: depth is a value elsewhere, never part of leg identity."""
    names = {f.name for f in dataclasses.fields(Instrument)}
    assert names == {"underlying", "exchange", "symbol", "expiry", "strike", "option_type"}
    for forbidden in ("depth", "depth_levels", "depth_type", "tier", "requested_depth", "wire_symbol"):
        assert forbidden not in names, f"Instrument must not carry {forbidden!r} (F10)"


def test_instrument_is_frozen():
    inst = make_instrument()
    with pytest.raises(dataclasses.FrozenInstanceError):
        inst.strike = 24100.0  # type: ignore[misc]


def test_instrument_is_hashable_and_usable_as_a_set_key():
    """Plan_002 §9 keys four sets by Instrument; that requires hashability."""
    a, b = make_instrument(), make_instrument()
    assert a == b and hash(a) == hash(b)
    assert len({a, b}) == 1
    assert {a: DepthType.PREMIUM}[b] is DepthType.PREMIUM


def test_same_leg_at_different_depths_is_one_key():
    """The point of F10. Depth lives in the value, so promoting a leg does not create a second key --
    which is exactly what the wire-symbol-keyed map cannot express (§21 D-9)."""
    leg = make_instrument()
    state: dict[Instrument, DepthType] = {leg: DepthType.STANDARD}
    state[make_instrument()] = DepthType.PREMIUM
    assert len(state) == 1
    assert state[leg] is DepthType.PREMIUM


def test_instruments_differing_in_identity_are_distinct():
    base = make_instrument()
    assert base != make_instrument(strike=24100.0)
    assert base != make_instrument(option_type="PE")
    assert base != make_instrument(exchange="BFO")
    assert base != make_instrument(underlying="SENSEX")
    assert base != make_instrument(expiry="04-SEP-25")
    assert len({base, make_instrument(strike=24100.0), make_instrument(option_type="PE")}) == 3


@pytest.mark.parametrize("field", ["underlying", "exchange", "symbol", "expiry", "option_type"])
@pytest.mark.parametrize("bad", ["", "   ", None, 123])
def test_instrument_rejects_malformed_identity_fields(field, bad):
    with pytest.raises(ValueError, match=field):
        make_instrument(**{field: bad})


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_instrument_rejects_non_finite_strike(bad):
    with pytest.raises(ValueError, match="finite"):
        make_instrument(strike=bad)


@pytest.mark.parametrize("bad", ["24000", None, True])
def test_instrument_rejects_non_numeric_strike(bad):
    with pytest.raises(ValueError, match="numeric"):
        make_instrument(strike=bad)


def test_instrument_accepts_integer_and_fractional_strikes():
    """The instrument master reports fractional strikes (e.g. VEDL...292.5CE)."""
    assert make_instrument(strike=24000).strike == 24000
    assert make_instrument(strike=292.5).strike == 292.5


def test_instrument_str_is_symbol_at_exchange():
    assert str(make_instrument()) == "NIFTY28AUG2524000CE@NFO"
