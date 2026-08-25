"""Framework data models: leg identity and depth tier (Plan_002 §9, fork F10).

The single decision these two types encode is **F10: state is keyed by leg identity, and depth is a
value, never part of the key.** The recorder's existing ``_subscriptions`` map is keyed by *wire
symbol*, and ``wire_symbol()`` appends a ``:50`` suffix for premium depth -- so a depth transition
changes the key and "the same leg at a different depth" is inexpressible (Plan_002 §21 D-9).
:class:`Instrument` fixes that by carrying no depth at all; :class:`DepthType` names the tier
separately. The wire symbol and its suffix become a rendering detail owned by the Broker Adapter (F7).

Genericization: no index name, exchange code, strike step, or option-type semantics appears here.
Symbol construction and option-type meaning belong to the ``SymbolCodec`` seam (Plan_002 §10.2, F3);
these models only require that identity fields are present and well-formed.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum


class DepthType(Enum):
    """Which depth tier a leg is subscribed at.

    A **tier**, not a level count. The numeric book depth (5, 20, 50, ...) is a broker fact that lives
    on :class:`~.capabilities.BrokerCapability`, because it varies by broker and by exchange -- FYERS
    serves 50-level TBT on NSE/NFO but only 5-level on BFO. Keeping the number off the tier is what
    lets the same allocation logic run against a broker whose premium tier is 20 rather than 50.

    ``STANDARD`` is the permanent baseline every eligible leg holds for the session; ``PREMIUM`` is the
    mutable overlay bounded by the broker's budget (Plan_002 §6, fork F2).
    """

    STANDARD = "standard"
    PREMIUM = "premium"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class Instrument:
    """One option leg, identified independently of the depth it is streaming at (F10).

    Frozen and hashable so it can key the ``set``/``dict`` state in Plan_002 §9 (``baseline``,
    ``premium_overlay``, ``pending``, ``failed``). Equality and hashing cover every field, so two
    instruments are the same leg exactly when their identity matches -- there is no depth component to
    make one leg look like two.

    Attributes:
        underlying: The configured ``underlyings[].name`` this leg belongs to. Used to group state
            per underlying; never compared against a hardcoded index name.
        exchange: The option exchange (``underlyings[].option_exchange``). Carried because premium
            eligibility is per-exchange (Plan_002 §13.1), resolved by the capability layer in F2.
        symbol: The OpenAlgo symbol for the leg, as produced by the instrument master. Also the
            documented tiebreaker for the total ordering in §10.3 (score desc, then symbol).
        expiry: Expiry tag exactly as the instrument master returns it.
        strike: Strike price. ``float`` because the master reports fractional strikes.
        option_type: Option side tag from the master. Validated as non-empty only -- its semantics
            belong to the ``SymbolCodec`` seam, so a broker or asset class using different tags needs
            no change here.
    """

    underlying: str
    exchange: str
    symbol: str
    expiry: str
    strike: float
    option_type: str

    def __post_init__(self) -> None:
        """Reject a malformed leg at construction, so no partially-valid identity enters framework
        state. Consistent with the config contract: fail loudly, never silently normalize."""
        for field_name in ("underlying", "exchange", "symbol", "expiry", "option_type"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Instrument.{field_name} must be a non-empty string, got {value!r}"
                )
        if isinstance(self.strike, bool) or not isinstance(self.strike, (int, float)):
            raise ValueError(f"Instrument.strike must be numeric, got {self.strike!r}")
        if not math.isfinite(float(self.strike)):
            raise ValueError(f"Instrument.strike must be finite, got {self.strike!r}")

    def __str__(self) -> str:
        return f"{self.symbol}@{self.exchange}"
