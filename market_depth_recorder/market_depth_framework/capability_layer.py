"""Broker Capabilities layer (Plan_002 §10.1, §13.1, §13.2, §16) -- phase F2.

This is the layer that turns a broker's **declared facts** (the F1 dataclasses in
:mod:`.capabilities`) into the **single logical answers** the rest of the framework consumes. The
separation is deliberate and load-bearing:

* :mod:`.capabilities` carries what the broker says about itself. It computes nothing.
* This module resolves those facts. It holds no state of its own beyond the capability it wraps.

The framework consumes **one** logical budget -- :attr:`BrokerCapabilityLayer.effective_budget` --
and never sees a connection or a channel. Connection packing is the Broker Adapter's problem (F7).
That is exactly what keeps the engine broker-agnostic: a broker exposing ``1 x 20`` or full-chain 50
changes only its capability configuration, never an allocator.

**The budget formula (Plan_002 §10.1)**::

    effective_budget = min(total_symbol_budget, max_connections * symbols_per_connection)

``max_channels`` **never** enters this arithmetic. The FROZEN FYERS finding is 5 Market-Depth symbols
per *connection*, 3 connections per app per user, and 50 channels per connection that are a
pause/resume grouping carrying **no** capacity -- so the real ceiling is ``3 x 5 = 15``, not the
``5 x 50 = 250`` an earlier reading assumed. Multiplying channels in is precisely the mistake that
produced a ceiling roughly 16x too large. Evidence:
``Documents/evidence/fyers_tbt_concurrency_20260714/tbt_concurrency_reconciliation_20260714.md``.

The number 15 appears nowhere in this module. It is *derived* from configuration, so a broker with
different connection math needs no code change.

**What this layer does not know:** underlyings, strikes, ranking, priority scores, windows,
subscription state, or allocation policy. It answers capability questions only. The two module-level
functions that do take underlying names (:func:`eligible_underlyings` and
:func:`check_premium_floor_feasible`) are deliberately **not** methods -- they receive the
underlying-to-exchange mapping as an argument, so the layer itself stays ignorant of it.

**No I/O.** Every computation here is pure and deterministic: no file, socket, thread, subprocess,
queue, or database connection. The layer is safe to construct and call from any thread, including
inside the PROCESSOR loop.
"""

from __future__ import annotations

from typing import Mapping

from .capabilities import UNLIMITED_BUDGET, BrokerCapability
from .config import FrameworkConfig, FrameworkConfigError
from .models import DepthType


class BrokerCapabilityLayer:
    """Resolves one broker's declared capability into the answers the framework consumes.

    Wraps a single :class:`~.capabilities.BrokerCapability`. Construction is cheap and total: the
    capability was already validated (structurally by its own ``__post_init__``, and against the
    schema by :func:`~.config.validate_framework_config`), so there is nothing left to fail on.

    Args:
        capability: The broker's validated declared facts.

    Raises:
        TypeError: If ``capability`` is not a :class:`~.capabilities.BrokerCapability`. This is a
            programming error rather than a config error, so it is not routed through
            :class:`~.config.FrameworkConfigError`.
    """

    __slots__ = ("_capability", "_effective_budget")

    def __init__(self, capability: BrokerCapability) -> None:
        if not isinstance(capability, BrokerCapability):
            raise TypeError(
                f"BrokerCapabilityLayer requires a BrokerCapability, got {type(capability).__name__}"
            )
        self._capability = capability
        # Computed once. The inputs are frozen, so the result cannot drift mid-session and every
        # caller in a rebalance pass sees the same number.
        self._effective_budget = min(
            capability.total_symbol_budget,
            capability.premium.max_connections * capability.premium.symbols_per_connection,
        )

    # ------------------------------------------------------------------ declared facts (pass-through)
    @property
    def capability(self) -> BrokerCapability:
        """The wrapped declared facts. Frozen, so exposing it cannot let a caller mutate the layer."""
        return self._capability

    @property
    def broker(self) -> str:
        """Broker identifier, as it appears under ``broker_capabilities`` in config."""
        return self._capability.broker

    @property
    def standard_depth(self) -> int:
        """Book levels the always-available baseline tier delivers."""
        return self._capability.standard.depth

    @property
    def premium_depth(self) -> int:
        """Book levels the scarce premium tier delivers, where the broker serves it."""
        return self._capability.premium.depth

    @property
    def premium_exchanges(self) -> frozenset[str]:
        """Exchanges on which this broker serves the premium tier. Frozen, so it cannot drift."""
        return self._capability.premium_exchanges

    # --------------------------------------------------------------------------------- the budget
    @property
    def effective_budget(self) -> int:
        """The one logical premium-symbol budget the framework consumes.

        ``min(total_symbol_budget, max_connections * symbols_per_connection)`` (§10.1). Always an
        ``int``: :data:`~.capabilities.UNLIMITED_BUDGET` is an integer sentinel rather than
        ``float('inf')`` precisely so ``min()`` here cannot promote the result to a float and quietly
        break every ``-> int`` contract downstream.

        ``max_channels`` is absent from this expression by design and must stay absent.
        """
        return self._effective_budget

    @property
    def has_account_wide_cap(self) -> bool:
        """Whether the broker declares an account-wide cap beyond its connection math.

        ``False`` means ``total_symbol_budget`` was omitted and carries the
        :data:`~.capabilities.UNLIMITED_BUDGET` sentinel -- a documented semantic for an absent
        optional key, not a silent default.
        """
        return self._capability.total_symbol_budget != UNLIMITED_BUDGET

    # ------------------------------------------------------------------------- per-exchange answers
    def supports_premium(self, exchange: str) -> bool:
        """Whether this broker serves the premium tier on ``exchange`` (fork F13, §13.1).

        Matching is **exact and case-sensitive**: the exchange code in configuration must be written
        the same way the instrument master reports it. Case-folding here would be a silent
        normalization, and the framework's contract everywhere else is to fail loudly rather than
        quietly repair a config value.

        Raises:
            ValueError: If ``exchange`` is not a non-empty string. A malformed exchange is a bug in
                the caller; returning ``False`` would hide it behind a plausible-looking answer.
        """
        _check_exchange(exchange)
        return exchange in self._capability.premium_exchanges

    def premium_capacity(self, exchange: str) -> int:
        """Premium slots this broker can serve on ``exchange``.

        :attr:`effective_budget` where the exchange is eligible, **0** where it is not. This is the
        capability-level expression of fork F13: an underlying on an ineligible exchange reports zero
        premium candidate capacity, so it receives zero premium budget and takes no floor. Its
        standard-depth baseline coverage is untouched -- eligibility governs the premium overlay only.
        """
        return self._effective_budget if self.supports_premium(exchange) else 0

    def available_tiers(self, exchange: str) -> tuple[DepthType, ...]:
        """Depth tiers this broker can serve on ``exchange``, baseline first.

        Every exchange gets :attr:`~.models.DepthType.STANDARD`; only premium-eligible exchanges also
        get :attr:`~.models.DepthType.PREMIUM`. Ordering is fixed rather than set-derived so the
        result is deterministic and replay-stable.
        """
        if self.supports_premium(exchange):
            return (DepthType.STANDARD, DepthType.PREMIUM)
        return (DepthType.STANDARD,)

    def depth_for(self, exchange: str, tier: DepthType) -> int:
        """Book levels the broker will **actually** serve for ``tier`` on ``exchange``.

        A ``PREMIUM`` request on an ineligible exchange resolves to the standard depth, because that
        is what the broker will really deliver -- the caller asking is not an error, and reporting the
        truthful number is what lets the recorder store a self-describing ``depth_levels`` and emit
        deep-book-only metrics as ``NULL`` where the book is genuinely shallower.

        Raises:
            TypeError: If ``tier`` is not a :class:`~.models.DepthType`.
        """
        if not isinstance(tier, DepthType):
            raise TypeError(f"depth_for() requires a DepthType, got {type(tier).__name__}")
        if tier is DepthType.PREMIUM and self.supports_premium(exchange):
            return self.premium_depth
        _check_exchange(exchange)
        return self.standard_depth

    def __repr__(self) -> str:
        return (
            f"BrokerCapabilityLayer(broker={self.broker!r}, "
            f"effective_budget={self._effective_budget}, "
            f"premium_depth={self.premium_depth}, standard_depth={self.standard_depth})"
        )


def _check_exchange(exchange: str) -> None:
    if not isinstance(exchange, str) or not exchange.strip():
        raise ValueError(f"exchange must be a non-empty string, got {exchange!r}")


# ------------------------------------------------------------------------------------- construction
def build_capability_layers(config: FrameworkConfig) -> Mapping[str, BrokerCapabilityLayer]:
    """Wrap every configured broker capability in its layer.

    Returns a plain ``dict`` keyed by broker name, in configuration order. Building all of them up
    front means a multi-broker deployment resolves its budgets once at startup rather than per
    rebalance pass.
    """
    return {name: BrokerCapabilityLayer(cap) for name, cap in config.broker_capabilities.items()}


def capability_layer_for(config: FrameworkConfig, broker: str) -> BrokerCapabilityLayer:
    """Resolve the capability layer for one broker.

    Raises:
        FrameworkConfigError: If ``broker`` has no entry under ``broker_capabilities``. This is a
            startup configuration failure and carries the exit-1 contract: running against a broker
            whose capabilities are unknown would mean guessing at a budget, and a guessed budget is
            precisely the failure this whole layer exists to prevent.
    """
    _check_broker_name(broker)
    capability = config.broker_capabilities.get(broker)
    if capability is None:
        known = ", ".join(sorted(config.broker_capabilities)) or "(none configured)"
        raise FrameworkConfigError(
            [f"no broker capability configured for {broker!r} (configured brokers: {known})"]
        )
    return BrokerCapabilityLayer(capability)


def _check_broker_name(broker: str) -> None:
    if not isinstance(broker, str) or not broker.strip():
        raise FrameworkConfigError([f"broker name must be a non-empty string, got {broker!r}"])


# --------------------------------------------------------- startup validation over underlyings (§13.2)
def eligible_underlyings(
    layer: BrokerCapabilityLayer, underlying_exchanges: Mapping[str, str]
) -> tuple[str, ...]:
    """The configured underlyings whose option exchange is premium-eligible (§13.1).

    Deliberately a module-level function rather than a method: the layer must not know about
    underlyings, so the caller supplies the name-to-exchange mapping (from the recorder's
    ``underlyings[]``). Order follows the mapping's insertion order, so the result is deterministic
    and replayable.

    Raises:
        FrameworkConfigError: If the mapping is malformed. A missing or empty exchange would silently
            make an underlying ineligible, which is exactly the kind of quiet wrong answer the
            fail-fast contract exists to prevent.
    """
    errors: list[str] = []
    if not isinstance(underlying_exchanges, Mapping):
        raise FrameworkConfigError(
            [f"underlying_exchanges must be a mapping, got {type(underlying_exchanges).__name__}"]
        )
    result: list[str] = []
    for name, exchange in underlying_exchanges.items():
        if not isinstance(name, str) or not name.strip():
            errors.append(f"underlying name must be a non-empty string, got {name!r}")
            continue
        if not isinstance(exchange, str) or not exchange.strip():
            errors.append(f"underlying {name!r} has a malformed option exchange: {exchange!r}")
            continue
        if layer.supports_premium(exchange):
            result.append(name)
    if errors:
        raise FrameworkConfigError(errors)
    return tuple(result)


def check_premium_floor_feasible(
    layer: BrokerCapabilityLayer,
    underlying_exchanges: Mapping[str, str],
    min_per_underlying: int,
) -> tuple[str, ...]:
    """Startup feasibility check for ``budget_allocator.min_per_underlying`` (§13.2).

    The floor is scoped to **premium-eligible** underlyings. Read over all configured underlyings it
    would demand a floor for an underlying on an exchange with no deep book, contradicting §13.1's
    "an ineligible underlying gets 0". Scoped this way::

        min_per_underlying * len(eligible_underlyings) <= effective_budget

    Because runtime ``active`` is always a subset of the eligible set, satisfying this at startup
    makes an equivalent mid-session failure unreachable -- which is why the Budget Allocator has no
    raising path and cannot kill the PROCESSOR thread (§13.2).

    Returns:
        The eligible underlying names, so the caller does not have to resolve them twice.

    Raises:
        FrameworkConfigError: If the floor cannot be met, carrying the exit-1 contract.
    """
    if isinstance(min_per_underlying, bool) or not isinstance(min_per_underlying, int):
        raise FrameworkConfigError(
            [f"min_per_underlying must be an int, got {min_per_underlying!r}"]
        )
    if min_per_underlying < 0:
        raise FrameworkConfigError(
            [f"min_per_underlying must be >= 0, got {min_per_underlying}"]
        )

    eligible = eligible_underlyings(layer, underlying_exchanges)
    required = min_per_underlying * len(eligible)
    if required > layer.effective_budget:
        raise FrameworkConfigError([
            f"budget_allocator.min_per_underlying={min_per_underlying} is infeasible: "
            f"{len(eligible)} premium-eligible underlying(s) ({', '.join(eligible)}) require "
            f"{required} premium slots, but broker {layer.broker!r} has an effective_budget of "
            f"{layer.effective_budget}"
        ])
    return eligible
