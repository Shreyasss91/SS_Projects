"""Framework Orchestrator: the one call site the recorder's PROCESSOR uses (Plan_002 §10.8, §11).

Every other framework module answers one question. This one asks them in order, once per rebalance
pass, and hands back a :class:`~.subscription_state.SubscriptionPlan`::

    snapshot -> window -> rank -> budget -> depth -> reconcile -> plan

It exists so the recorder has **one** call site instead of seven, and so the pass order -- which is a
decided property of the design, not a caller's choice -- lives in the framework rather than in
``processor.py``.

What it deliberately is not:

* **Not a thread.** It is a plain synchronous object. The caller's thread is the only thread, and the
  caller is PROCESSOR (Plan_002 §13). There is no loop here, no timer, and no sleep.
* **Not a broker client.** No wire symbol, no premium suffix, no connection arithmetic, no I/O. The
  only broker fact it reads is ``effective_budget`` from the capability layer, which is a number.
* **Not a state owner.** The desired coverage lives in :class:`~.subscription_state.SubscriptionState`
  (PROCESSOR-owned); the incumbency and cooldown live in the per-underlying
  :class:`~.depth_allocator.DepthAllocator`. The only state added here is the rebalance trigger's own
  bookkeeping -- the last pass timestamp and the last window key -- because F11 asks this object to
  own the trigger.

The trigger (Plan_002 §14.5, fork F11) fires on **interval OR window/ATM change, whichever comes
first**. The window-change half is answered from a cheap key -- the ATM strike plus the index span of
the strikes inside the window -- computed by binary search over a precomputed strike ladder, so the
hot path a caller may run on every packet costs a couple of ``bisect`` calls rather than a full
candidate sweep. The full pass only runs once the trigger has already said yes.
"""

from __future__ import annotations

import bisect
import math
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from .budget_allocator import BudgetAllocator, budget_allocator_for
from .capability_layer import (
    BrokerCapabilityLayer,
    capability_layer_for,
    eligible_underlyings,
)
from .config import FrameworkConfig, FrameworkConfigError
from .depth_allocator import DepthAllocator, depth_allocators_for
from .models import DepthType, Instrument
from .priority_policy import PriorityPolicy, policy_for, rank_candidates
from .subscription_manager import SubscriptionManager
from .subscription_state import SubscriptionPlan, SubscriptionState
from .window_manager import (
    ExpiryCalendar,
    FixedExpiryCalendar,
    SymbolCodec,
    TagSymbolCodec,
    WindowManager,
    WindowResult,
    window_specs_from_underlyings,
)

__all__ = [
    "DEFAULT_CODEC_RULE",
    "DEFAULT_EXPIRY_RULE",
    "FrameworkOrchestrator",
    "RebalanceResult",
    "TRIGGER_INITIAL",
    "TRIGGER_INTERVAL",
    "TRIGGER_WINDOW_CHANGE",
    "orchestrator_for",
]

#: Trigger labels, carried on :class:`RebalanceResult` so a log line says *why* a pass ran.
TRIGGER_INITIAL = "initial"
TRIGGER_INTERVAL = "interval"
TRIGGER_WINDOW_CHANGE = "window_change"

#: Names used when ``window_manager`` names no rule of its own. They are rule *names*, not option
#: tags: the tags themselves always come from configuration (genericization contract).
DEFAULT_CODEC_RULE = "option_tags"
DEFAULT_EXPIRY_RULE = "active_expiry"


@dataclass(frozen=True, slots=True)
class RebalanceResult:
    """Everything one pass produced, as a value.

    ``desired`` is a snapshot copy rather than a live view, so a caller that hands it to another
    thread (F8 hands it to FEED for the reconnect reissue) cannot observe it mutating underneath.
    """

    plan: SubscriptionPlan
    desired: Mapping[Instrument, DepthType]
    windows: tuple[WindowResult, ...]
    budgets: Mapping[str, int]  #: Premium budget per **premium-eligible** underlying, that pass.
    trigger: str
    at: float

    @property
    def is_empty(self) -> bool:
        """Whether this pass asks for no wire action at all."""
        return self.plan.is_empty


@dataclass(frozen=True, slots=True)
class _Ladder:
    """The precomputed strike ladder for one underlying, used only by the cheap trigger key."""

    strikes: tuple[float, ...]
    window_points: float
    expiry: str


class FrameworkOrchestrator:
    """One rebalance pass, in the decided order (§11).

    Args:
        window_manager: Resolves the candidate legs for each underlying from a spot price.
        policy: The priority policy used to rank candidates within an underlying.
        budget_allocator: Splits the one premium budget across underlyings.
        depth_allocators: One :class:`~.depth_allocator.DepthAllocator` per underlying -- a shared one
            would let a busy chain's reallocation reset a quiet chain's cooldown.
        subscription_manager: The stateless desired-vs-live reconciler.
        state: The PROCESSOR-owned :class:`~.subscription_state.SubscriptionState`.
        capability: The broker capability layer -- read for ``effective_budget`` and nothing else.
        universe: Every option leg the instrument master resolved, as framework identities.
        expiries: The active expiry per underlying, used to build the trigger's strike ladder.
        trigger: ``"interval"``, ``"window_change"`` or ``"both"`` (§14.5, F11).
        interval_seconds: The interval half of the trigger. Ignored when the trigger is
            ``"window_change"``.
        clock: Injected time source. No business logic here reads a wall clock.

    Thread ownership: **the caller's thread only**. Every method is synchronous and unlocked because a
    single thread owns this object, exactly as :class:`~.subscription_state.SubscriptionState` is
    single-writer. Calling it from two threads would be an architecture violation, not merely a race.
    """

    __slots__ = (
        "_windows", "_policy", "_budget", "_allocators", "_manager", "_state", "_capability",
        "_universe", "_ladders", "_eligible", "_trigger", "_interval", "_clock",
        "_last_pass_at", "_last_key", "_passes",
    )

    def __init__(
        self,
        *,
        window_manager: WindowManager,
        policy: PriorityPolicy,
        budget_allocator: BudgetAllocator,
        depth_allocators: Mapping[str, DepthAllocator],
        subscription_manager: SubscriptionManager,
        state: SubscriptionState,
        capability: BrokerCapabilityLayer,
        universe: Iterable[Instrument],
        expiries: Mapping[str, str],
        trigger: str,
        interval_seconds: float,
        clock: Callable[[], float],
    ) -> None:
        if not isinstance(window_manager, WindowManager):
            raise TypeError(
                f"window_manager must be a WindowManager, got {type(window_manager).__name__}"
            )
        if not isinstance(capability, BrokerCapabilityLayer):
            raise TypeError(
                f"capability must be a BrokerCapabilityLayer, got {type(capability).__name__}"
            )
        if not isinstance(state, SubscriptionState):
            raise TypeError(f"state must be a SubscriptionState, got {type(state).__name__}")
        if not callable(clock):
            raise TypeError("clock must be callable")
        if trigger not in ("interval", "window_change", "both"):
            raise FrameworkConfigError([f"unknown rebalance trigger {trigger!r}"])
        interval = float(interval_seconds)
        if trigger in ("interval", "both") and not interval > 0:
            raise FrameworkConfigError(
                [f"rebalance.interval_seconds must be > 0 for trigger {trigger!r}, got {interval!r}"]
            )

        self._windows = window_manager
        self._policy = policy
        self._budget = budget_allocator
        self._manager = subscription_manager
        self._state = state
        self._capability = capability
        self._trigger = trigger
        self._interval = interval
        self._clock = clock

        names = tuple(window_manager.underlyings)
        missing = [name for name in names if name not in depth_allocators]
        if missing:
            raise FrameworkConfigError(
                [f"no depth allocator configured for underlying {name!r}" for name in missing]
            )
        self._allocators = dict(depth_allocators)

        # Materialize the universe once: a generator handed in would be exhausted by the first pass,
        # and every pass sweeps it again.
        self._universe: tuple[Instrument, ...] = tuple(universe)
        for leg in self._universe:
            if not isinstance(leg, Instrument):
                raise TypeError(f"universe must contain Instruments, got {type(leg).__name__}")
        self._ladders = self._build_ladders(names, expiries)
        # Premium eligibility is a broker fact (§13.1, fork F13), resolved once from each underlying's
        # option exchange. An ineligible underlying is not merely capped at zero premium: it is kept
        # out of the budget split entirely, so the ``min_per_underlying`` floor is never spent on a
        # chain the broker cannot serve premium depth for (§13.2).
        self._eligible = frozenset(
            eligible_underlyings(
                capability, {name: window_manager.spec_for(name).exchange for name in names}
            )
        )

        self._last_pass_at: float | None = None
        self._last_key: tuple | None = None
        self._passes = 0

    # ------------------------------------------------------------------------------- introspection
    @property
    def underlyings(self) -> tuple[str, ...]:
        """The configured underlyings, in configured order."""
        return tuple(self._windows.underlyings)

    @property
    def capability(self) -> BrokerCapabilityLayer:
        """The resolved capability layer this orchestrator planned with.

        Exposed so the **one** broker-facing consumer (the FEED-side ``BrokerAdapter``, F8) renders the
        wire with the very object the plan was budgeted against, instead of resolving a second layer
        that could silently disagree.
        """
        return self._capability

    @property
    def effective_budget(self) -> int:
        """The one logical premium budget, straight from the capability layer. Never a literal."""
        return self._capability.effective_budget

    @property
    def eligible(self) -> frozenset[str]:
        """The underlyings whose option exchange the broker serves premium depth on (§13.1)."""
        return self._eligible

    @property
    def passes(self) -> int:
        """How many full passes have run. Observability for the health file."""
        return self._passes

    @property
    def last_pass_at(self) -> float | None:
        """When the last full pass ran, or ``None`` before the first."""
        return self._last_pass_at

    def desired(self) -> dict[Instrument, DepthType]:
        """The current desired coverage, rebuilt from state. A copy, safe to hand across a thread."""
        return self._state.desired()

    # ----------------------------------------------------------------------------- trigger (§14.5)
    def due(self, spots: Mapping[str, float | None]) -> str | None:
        """Whether a pass is due right now, and which half of the trigger fired.

        Cheap by construction: the window half is a couple of ``bisect`` calls per underlying against
        a precomputed ladder, so a caller may ask on every packet. The first pass is always due --
        there is no coverage yet, and waiting an interval for it would leave the session blind.

        Returns the trigger label, or ``None`` when nothing is due.
        """
        key = self._window_key(spots)
        if key is None:
            return None  # no usable spot for any underlying yet -- nothing to plan against
        if self._last_pass_at is None:
            return TRIGGER_INITIAL
        if self._trigger in ("window_change", "both") and key != self._last_key:
            return TRIGGER_WINDOW_CHANGE
        if self._trigger in ("interval", "both"):
            if float(self._clock()) - self._last_pass_at >= self._interval:
                return TRIGGER_INTERVAL
        return None

    # ------------------------------------------------------------------------------ the pass (§11)
    def rebalance(
        self,
        spots: Mapping[str, float | None],
        live: Mapping[Instrument, DepthType],
        *,
        rejected: Iterable[Instrument] = (),
        trigger: str | None = None,
    ) -> RebalanceResult | None:
        """Run one full pass and return its plan, or ``None`` when nothing is due.

        Args:
            spots: Last known spot per underlying, from the caller's own spot cache. A missing,
                ``None``, non-positive or non-finite spot yields no candidates for that underlying
                and never raises -- the recorder drops such ticks and so does this.
            live: What the broker is **observed** to be delivering, from the adapter's snapshot. The
                observation boundary is delivery-derived, never acknowledgement-derived (§20.4).
            rejected: Legs the broker explicitly rejected since the previous pass. Observability: a
                rejected leg is absent from ``live`` anyway, so reconciliation re-plans it regardless.
            trigger: Force a pass with this label, skipping :meth:`due`. Used for the startup pass and
                by tests; ``None`` consults the trigger.

        The order is fixed and is the design's, not a caller's: observation is folded in first, then
        windows, ranking, budget, depth, and only then reconciliation. ``record_dispatch`` runs on the
        same pass that produced the plan, so a leg is pending from the moment it is planned.
        """
        label = trigger if trigger is not None else self.due(spots)
        if label is None:
            return None

        # 1. Fold in what was observed since the previous pass. Both are pure state annotations --
        #    neither generates an action, and neither can manufacture a failure (§20.4).
        self._state.apply_live(live)
        failures = tuple(rejected)
        if failures:
            self._state.record_failed(failures)

        # 2. Windows: which legs are candidates at this spot.
        results = self._windows.candidates_for_all(spots, self._universe)

        # 3. Ranking: a total order within each underlying, never across them.
        ranked = rank_candidates(self._policy, results)

        # 4. Budget: split the one premium budget across the **premium-eligible** underlyings that
        #    have candidates. An ineligible chain gets no entry, hence budget 0 below, hence every one
        #    of its legs stays standard -- the broker could not deliver premium there anyway.
        counts = {
            result.underlying: len(result.candidates)
            for result in results
            if result.underlying in self._eligible
        }
        budgets = self._budget.allocate_budget(self._capability.effective_budget, counts)

        # 5. Depth: choose the premium legs per underlying, under hysteresis and cooldown.
        desired: dict[Instrument, DepthType] = {}
        for result in results:
            allocation = self._allocators[result.underlying].allocate(
                ranked[result.underlying], budgets.get(result.underlying, 0)
            )
            for leg in allocation.premium:
                desired[leg] = DepthType.PREMIUM
            for leg in allocation.standard:
                desired[leg] = DepthType.STANDARD

        # 6. Reconcile against live. ``set_desired`` grows the baseline monotonically, so a leg that
        #    left the window stays subscribed at standard rather than being torn down (§12).
        self._state.set_desired(desired)
        full_desired = self._state.desired()
        plan = self._manager.reconcile(full_desired, live)

        # 7. Record the dispatch on the same pass: the plan is about to be handed to the executor, and
        #    a leg is pending from the moment it is planned, not from the moment a frame lands.
        self._state.record_dispatch(plan)

        at = float(self._clock())
        self._last_pass_at = at
        self._last_key = self._window_key(spots)
        self._passes += 1
        return RebalanceResult(
            plan=plan,
            desired=MappingProxyType(dict(full_desired)),
            windows=results,
            budgets=MappingProxyType(dict(budgets)),
            trigger=label,
            at=at,
        )

    def reset(self) -> None:
        """Forget the desired coverage and the trigger history (graceful session shutdown, §9).

        The allocators keep their own history deliberately: an operator reading the health file after a
        session end still wants to see what the last allocation was.
        """
        self._state.reset()
        self._last_pass_at = None
        self._last_key = None

    # ------------------------------------------------------------------------------------ internals
    def _build_ladders(
        self, names: Sequence[str], expiries: Mapping[str, str]
    ) -> dict[str, _Ladder]:
        """Precompute the per-underlying strike ladder the cheap trigger key reads.

        Built once from the universe, because the universe is fixed for a session: the instrument
        master resolves one chain per underlying at startup and the recorder never re-resolves it
        mid-session.
        """
        if not isinstance(expiries, Mapping):
            raise TypeError(f"expiries must be a mapping, got {type(expiries).__name__}")
        ladders: dict[str, _Ladder] = {}
        for name in names:
            expiry = expiries.get(name)
            if not isinstance(expiry, str) or not expiry.strip():
                raise FrameworkConfigError(
                    [f"no active expiry supplied for underlying {name!r}"]
                )
            spec = self._windows.spec_for(name)
            strikes = sorted(
                {
                    float(leg.strike)
                    for leg in self._universe
                    if leg.underlying == name and leg.expiry == expiry
                }
            )
            ladders[name] = _Ladder(
                strikes=tuple(strikes),
                window_points=float(spec.window_points),
                expiry=expiry,
            )
        return ladders

    def _window_key(self, spots: Mapping[str, float | None]) -> tuple | None:
        """A cheap, order-independent fingerprint of "which legs the window admits, and where ATM is".

        Two ``bisect`` calls plus an ATM decision per underlying. It changes exactly when the ATM
        strike moves or when a strike enters or leaves the window, which is the definition of a
        window/ATM change in §14.5 -- and it never touches the candidate legs themselves, which is
        what keeps it affordable on a per-packet caller.

        ``None`` means no underlying has a usable spot yet, so there is nothing to plan against.
        """
        if not isinstance(spots, Mapping):
            raise TypeError(f"spots must be a mapping, got {type(spots).__name__}")
        parts: list[tuple] = []
        usable = False
        for name in self._windows.underlyings:
            ladder = self._ladders[name]
            spot = spots.get(name)
            if not _is_usable_spot(spot) or not ladder.strikes:
                parts.append((name, None))
                continue
            usable = True
            price = float(spot)  # type: ignore[arg-type]
            lo = bisect.bisect_left(ladder.strikes, price - ladder.window_points)
            hi = bisect.bisect_right(ladder.strikes, price + ladder.window_points)
            parts.append((name, lo, hi, _atm_of(ladder.strikes, price)))
        if not usable:
            return None
        return tuple(parts)


# ------------------------------------------------------------------------------------ module helpers
def _is_usable_spot(spot: object) -> bool:
    """The recorder's own rule: a spot must be a finite positive number to plan against."""
    if isinstance(spot, bool) or not isinstance(spot, (int, float)):
        return False
    value = float(spot)
    return math.isfinite(value) and value > 0.0


def _atm_of(strikes: Sequence[float], spot: float) -> float | None:
    """The strike nearest ``spot``, with an exact tie resolving to the **lower** strike.

    The same answer :func:`~.window_manager._atm_strike` gives, reached by binary search because this
    runs on the caller's hot path. The tie rule is a decided framework rule (§15, F3 Decision 2), so
    it is reproduced here rather than approximated.
    """
    if not strikes:
        return None
    index = bisect.bisect_left(strikes, spot)
    if index == 0:
        return strikes[0]
    if index >= len(strikes):
        return strikes[-1]
    lower, upper = strikes[index - 1], strikes[index]
    return upper if (upper - spot) < (spot - lower) else lower


def _codecs_from_config(section: Mapping[str, Any]) -> tuple[dict[str, SymbolCodec], str]:
    """Build the option-side codecs from ``market_depth_framework.window_manager``.

    The call/put tags are configuration, never literals here: a broker or asset class using different
    tags changes the config, not this module (genericization contract). A framework that is enabled
    without codec tags fast-fails -- a silently guessed tag would misclassify every leg.
    """
    rule = section.get("codec_rule", DEFAULT_CODEC_RULE)
    if not isinstance(rule, str) or not rule.strip():
        raise FrameworkConfigError(
            ["[market_depth_framework.window_manager.codec_rule] must be a non-empty string"]
        )
    raw = section.get("codecs")
    if raw is None:
        raise FrameworkConfigError(
            [
                "[market_depth_framework.window_manager.codecs] is required when the framework is "
                "enabled: it maps a codec rule name to its call/put option tags"
            ]
        )
    if not isinstance(raw, Mapping):
        raise FrameworkConfigError(
            ["[market_depth_framework.window_manager.codecs] must be a mapping"]
        )
    errors: list[str] = []
    codecs: dict[str, SymbolCodec] = {}
    for name, entry in raw.items():
        tag = f"[market_depth_framework.window_manager.codecs.{name}]"
        if not isinstance(entry, Mapping):
            errors.append(f"{tag} must be a mapping")
            continue
        unknown = sorted(set(entry) - {"call_tags", "put_tags"})
        if unknown:
            errors.append(f"{tag} unknown key(s): {', '.join(unknown)}")
        try:
            codecs[str(name)] = TagSymbolCodec(
                call_tags=tuple(entry.get("call_tags") or ()),
                put_tags=tuple(entry.get("put_tags") or ()),
            )
        except (TypeError, ValueError) as exc:
            errors.append(f"{tag} {exc}")
    if rule not in codecs:
        errors.append(
            f"[market_depth_framework.window_manager.codec_rule] {rule!r} is not defined under "
            f"'codecs' (defined: {', '.join(sorted(codecs)) or '(none)'})"
        )
    if errors:
        raise FrameworkConfigError(errors)
    return codecs, rule


def orchestrator_for(
    config: FrameworkConfig,
    *,
    underlyings: Sequence[Mapping[str, Any]],
    universe: Iterable[Instrument],
    expiries: Mapping[str, str],
    clock: Callable[[], float],
    state: SubscriptionState | None = None,
    broker: str | None = None,
) -> FrameworkOrchestrator:
    """Assemble a :class:`FrameworkOrchestrator` from validated configuration.

    Every component resolves from config through its own ``*_for`` factory, so the wiring lives in one
    place and the recorder never constructs a framework component itself.

    Args:
        config: A validated :class:`~.config.FrameworkConfig`.
        underlyings: The recorder's ``underlyings[]`` entries, read for name, option exchange and
            initial window. No index name, exchange code or strike step is read from anywhere else.
        universe: Every resolved option leg as a framework :class:`~.models.Instrument`.
        expiries: The active expiry per underlying, from the instrument master.
        clock: Injected time source, threaded into the allocators, the state and the trigger.
        state: An existing :class:`~.subscription_state.SubscriptionState` to adopt. ``None`` builds
            one sized to the capability's effective budget.
        broker: Override which configured broker capability is active. ``None`` uses
            ``config.broker``, which validation already resolved.

    Raises:
        FrameworkConfigError: on any configuration problem, with the complete list of errors -- the
            same fast-fail contract the rest of the framework uses.
    """
    if not isinstance(config, FrameworkConfig):
        raise TypeError(f"config must be a FrameworkConfig, got {type(config).__name__}")
    layer = capability_layer_for(config, broker if broker is not None else config.broker)

    window_section = dict(config.window_manager)
    codecs, codec_rule = _codecs_from_config(window_section)
    expiry_rule = window_section.get("expiry_rule", DEFAULT_EXPIRY_RULE)
    if not isinstance(expiry_rule, str) or not expiry_rule.strip():
        raise FrameworkConfigError(
            ["[market_depth_framework.window_manager.expiry_rule] must be a non-empty string"]
        )

    specs = window_specs_from_underlyings(
        underlyings, codec_rule=codec_rule, expiry_rule=expiry_rule
    )
    calendars: dict[str, ExpiryCalendar] = {
        expiry_rule: FixedExpiryCalendar(dict(expiries))
    }
    window_manager = WindowManager(specs, codecs=codecs, calendars=calendars)

    names = tuple(window_manager.underlyings)
    return FrameworkOrchestrator(
        window_manager=window_manager,
        policy=policy_for(config.priority_policy.get("policy")),
        budget_allocator=budget_allocator_for(config),
        depth_allocators=depth_allocators_for(config, names, clock=clock),
        subscription_manager=SubscriptionManager(),
        state=state if state is not None
        else SubscriptionState(layer.effective_budget, clock=clock),
        capability=layer,
        universe=universe,
        expiries=expiries,
        trigger=str(config.rebalance.get("trigger", "both")),
        interval_seconds=float(config.rebalance.get("interval_seconds", 0.0) or 0.0),
        clock=clock,
    )
