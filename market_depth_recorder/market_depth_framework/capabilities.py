"""Broker-capability dataclasses (Plan_002 §10.1, §16, §17).

**F1 delivers the data shapes only.** The Broker Capabilities *layer* -- resolving
``effective_budget = min(total_symbol_budget, max_connections * symbols_per_connection)`` and
answering per-exchange premium eligibility -- is phase **F2** (Plan_002 §22). Nothing here computes a
budget or decides eligibility; these types carry the broker's declared facts and nothing more.

Why the shape looks like this: the FROZEN FYERS finding is that TBT caps at **5 Market-Depth symbols
per connection**, with **3 connections per app per user** and **50 channels per connection that are a
pause/resume grouping carrying no capacity**. So the real ceiling is ``3 x 5 = 15``, not the
``5 x 50 = 250`` an earlier reading assumed. ``max_channels`` is therefore carried for bookkeeping and
is **excluded from budget arithmetic** -- multiplying it in is precisely the mistake that produced a
ceiling roughly 16x too large. See ``Documents/patches/tbt_concurrency_reconciliation_20260714.md``.

The engine consumes one logical budget and never sees a connection; connection packing is the Broker
Adapter's problem (F7). That is what keeps the framework broker-agnostic -- another broker exposing
``1 x 20`` or full-chain 50 changes only this capability data, never the allocator.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Sentinel for "this broker imposes no account-wide symbol cap beyond its connection math".
#
# Deliberately an ``int``, never ``float('inf')`` (Plan_002 §10.1): budget arithmetic and every
# ``-> int`` contract downstream stay honest, and ``min()`` against it yields an int rather than
# silently promoting the whole calculation to float. A fixed literal rather than ``sys.maxsize`` so
# the value is identical on every platform and replay stays byte-deterministic.
UNLIMITED_BUDGET: int = 2**31 - 1


def _check_positive_int(value: object, label: str) -> None:
    """Structural guard shared by the tiers. Booleans are rejected explicitly -- ``True`` is an ``int``
    in Python, and a YAML ``true`` landing in a count field is a config error, not a 1."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an int, got {value!r}")
    if value <= 0:
        raise ValueError(f"{label} must be > 0, got {value!r}")


@dataclass(frozen=True, slots=True)
class StandardTier:
    """The always-available depth tier -- what the broker serves without a scarce-resource budget.

    Every eligible leg holds this tier for the whole session (BASELINE MONOTONICITY, Plan_002 §6).
    There is no connection arithmetic because there is no budget to run out of.
    """

    depth: int

    def __post_init__(self) -> None:
        _check_positive_int(self.depth, "StandardTier.depth")


@dataclass(frozen=True, slots=True)
class PremiumTier:
    """The scarce deep-book tier and the connection facts that bound it.

    Attributes:
        depth: Book levels the premium tier delivers (50 for FYERS TBT).
        symbols_per_connection: Concurrent premium symbols one connection carries (5 for FYERS).
        max_connections: Connections the broker allows per app per user (3 for FYERS).
        max_channels: Channels per connection. **Bookkeeping only.** Channels are a pause/resume
            grouping and carry no capacity, so this value must never be multiplied into a budget.
            Carried so the adapter can respect the broker's channel bookkeeping in F7.
    """

    depth: int
    symbols_per_connection: int
    max_connections: int
    max_channels: int

    def __post_init__(self) -> None:
        _check_positive_int(self.depth, "PremiumTier.depth")
        _check_positive_int(self.symbols_per_connection, "PremiumTier.symbols_per_connection")
        _check_positive_int(self.max_connections, "PremiumTier.max_connections")
        _check_positive_int(self.max_channels, "PremiumTier.max_channels")


@dataclass(frozen=True, slots=True)
class BrokerCapability:
    """Everything one broker declares about the depth it can serve.

    Attributes:
        broker: Broker identifier as it appears under ``broker_capabilities`` in config.
        premium: The scarce deep-book tier and its connection bounds.
        standard: The unbounded baseline tier.
        premium_exchanges: Exchanges on which this broker serves the premium tier. An option leg on
            any other exchange can hold the baseline but can never be promoted -- that is fork F13,
            and it is why the drafts' example wasted 2 of 15 slots on an exchange with no deep book.
            Resolution of eligibility from this set is F2; F1 only carries it.
        total_symbol_budget: Account-wide premium-symbol cap, when the broker imposes one beyond its
            connection math. Optional in config; omission means :data:`UNLIMITED_BUDGET`, which is a
            documented semantic ("no extra cap"), not a silent default for a required value.

    F1 intentionally exposes **no** ``effective_budget()`` and **no** ``supports_premium()``. Both are
    the F2 layer's behaviour, and the approval for F1 was explicit that capability dataclasses must not
    become the capability layer.
    """

    broker: str
    premium: PremiumTier
    standard: StandardTier
    premium_exchanges: frozenset[str] = field(default_factory=frozenset)
    total_symbol_budget: int = UNLIMITED_BUDGET

    def __post_init__(self) -> None:
        if not isinstance(self.broker, str) or not self.broker.strip():
            raise ValueError(f"BrokerCapability.broker must be a non-empty string, got {self.broker!r}")
        if not isinstance(self.premium, PremiumTier):
            raise ValueError(f"BrokerCapability.premium must be a PremiumTier, got {self.premium!r}")
        if not isinstance(self.standard, StandardTier):
            raise ValueError(f"BrokerCapability.standard must be a StandardTier, got {self.standard!r}")
        if not isinstance(self.premium_exchanges, frozenset):
            raise ValueError(
                f"BrokerCapability.premium_exchanges must be a frozenset, got {self.premium_exchanges!r}"
            )
        _check_positive_int(self.total_symbol_budget, "BrokerCapability.total_symbol_budget")
        # A "premium" tier no deeper than the baseline is a config mistake, not a degenerate case
        # worth supporting: the whole point of the scarce tier is that it sees further.
        if self.premium.depth <= self.standard.depth:
            raise ValueError(
                f"BrokerCapability.premium.depth ({self.premium.depth}) must be > "
                f"standard.depth ({self.standard.depth})"
            )
