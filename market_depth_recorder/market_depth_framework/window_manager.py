"""Window Manager: which option legs are candidates (Plan_002 §10.2, §15).

This layer answers exactly one question -- **which legs are eligible candidates for one underlying,
given spot** -- and deliberately answers no other. It does not rank candidates (Priority Policy, F4),
does not split a budget (Budget Allocator, F5), does not assign a depth tier (Depth Allocator, F5),
and does not subscribe (Subscription Manager, F6, and Broker Adapter, F7). It knows nothing of budgets,
connections, channels, hysteresis, or cooldown.

**Window semantics are the recorder's, not new ones.** The window is symmetric points from spot --
``lower = spot - window_points``, ``upper = spot + window_points`` -- and membership is inclusive at
both bounds, exactly reproducing the DSM seeding in ``websocket_client.py``
(``st.b_lower <= k <= st.b_upper``). The comparison is exact, with no epsilon, so a strike sitting on a
bound is in and anything past it is out. ATM is the strike nearest to spot with ties resolving to the
lower strike, reproducing ``processor._resolve_atm``'s ``min(strikes, key=...)`` over an ascending
strike list -- implemented order-independently here so a shuffled universe cannot change the answer.

**The candidate set is not the subscription set** (§15). Boundary expansion and the never-shrink
guarantee stay FEED-owned in the recorder; this layer is a pure function of (spot, universe, config)
recomputed from scratch on every pass, holding no window state of its own. That is what makes it
replayable: the same inputs always produce the same tuple.

**Genericization.** The candidate universe is *supplied* as authoritative :class:`~.models.Instrument`
values from the instrument master -- this layer builds no symbol and parses none. Option-side meaning
lives behind the :class:`SymbolCodec` seam and expiry selection behind the :class:`ExpiryCalendar`
seam, both registered **per rule** rather than per index name (§10.2), so a different asset class needs
a new registration, not a change here.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Mapping, Protocol, Sequence, runtime_checkable

from .config import FrameworkConfigError
from .models import Instrument


class OptionSide(Enum):
    """The two option sides, named independently of any broker's tag.

    The instrument master's tag (``CE``/``PE`` for the Indian equity-derivative masters, something
    else elsewhere) is data that reaches the framework on :attr:`Instrument.option_type`; this enum is
    the framework's internal vocabulary, and :class:`SymbolCodec` is the only place the two meet.
    """

    CALL = "call"
    PUT = "put"

    def __str__(self) -> str:
        return self.value


class WindowStatus(Enum):
    """Why a :class:`WindowResult` holds the candidates it holds.

    An empty candidate tuple has several distinct causes and they are not interchangeable when
    diagnosing a quiet session, so the reason is reported rather than inferred. ``RESOLVED`` with an
    empty tuple is itself meaningful: spot and universe were both known and simply no strike fell
    inside the window.
    """

    RESOLVED = "resolved"
    NO_SPOT = "no_spot"
    NO_EXPIRY = "no_expiry"
    NO_UNIVERSE = "no_universe"

    def __str__(self) -> str:
        return self.value


@runtime_checkable
class SymbolCodec(Protocol):
    """Seam owning what an instrument master's option-type tag *means* (§10.2).

    Registered per rule, not per index name. Keeping this out of the Window Manager is what lets the
    same window logic serve a master using different tags.
    """

    def option_side(self, option_type: str) -> OptionSide:
        """Return the side for one master tag, raising :class:`ValueError` if the tag is unknown."""


@runtime_checkable
class ExpiryCalendar(Protocol):
    """Seam owning expiry selection -- weekly/monthly rollover and holidays (§10.2).

    Registered per rule so the *rule* carries the semantics. Implementations must be pure: an
    implementation that reads the clock would make replay non-deterministic, so the session date is
    supplied to the implementation when it is built, never read inside it.
    """

    def active_expiry(self, underlying: str) -> str | None:
        """Return the active expiry tag for one underlying, or ``None`` when none is resolvable."""


class TagSymbolCodec:
    """A :class:`SymbolCodec` built from the master's call and put tags.

    Tags arrive from configuration at the wiring site, so no option-type literal appears in framework
    code. An unrecognised tag raises: guessing a side would silently misclassify a leg, and every
    other boundary in this framework fails visibly rather than plausibly.
    """

    __slots__ = ("_by_tag",)

    def __init__(self, call_tags: Sequence[str], put_tags: Sequence[str]) -> None:
        by_tag: dict[str, OptionSide] = {}
        for tags, side in ((call_tags, OptionSide.CALL), (put_tags, OptionSide.PUT)):
            if not tags:
                raise ValueError(f"TagSymbolCodec needs at least one {side} tag")
            for tag in tags:
                if not isinstance(tag, str) or not tag.strip():
                    raise ValueError(f"option-type tag must be a non-empty string, got {tag!r}")
                if tag in by_tag:
                    raise ValueError(f"option-type tag {tag!r} is registered for both sides")
                by_tag[tag] = side
        self._by_tag = by_tag

    @property
    def tags(self) -> tuple[str, ...]:
        """Every registered tag, in registration order."""
        return tuple(self._by_tag)

    def option_side(self, option_type: str) -> OptionSide:
        try:
            return self._by_tag[option_type]
        except (KeyError, TypeError):
            raise ValueError(
                f"unrecognised option-type tag {option_type!r}; "
                f"registered tags are {sorted(self._by_tag)}"
            ) from None


class FixedExpiryCalendar:
    """An :class:`ExpiryCalendar` over an already-resolved underlying-to-expiry mapping.

    The recorder resolves the active expiry from the instrument master; F8 hands that result in here.
    A rollover rule that computes its own expiry is a different registration, which is the point of
    the seam.
    """

    __slots__ = ("_by_underlying",)

    def __init__(self, expiry_by_underlying: Mapping[str, str]) -> None:
        resolved: dict[str, str] = {}
        for name, expiry in expiry_by_underlying.items():
            if not isinstance(expiry, str) or not expiry.strip():
                raise ValueError(f"expiry for {name!r} must be a non-empty string, got {expiry!r}")
            resolved[str(name)] = expiry
        self._by_underlying = resolved

    def active_expiry(self, underlying: str) -> str | None:
        return self._by_underlying.get(underlying)


@dataclass(frozen=True, slots=True)
class WindowSpec:
    """One underlying's candidate window, resolved from ``underlyings[]`` (§17).

    Attributes:
        name: The configured ``underlyings[].name``. Data, never compared against an index literal.
        exchange: ``underlyings[].option_exchange``. A universe leg claiming this underlying on a
            different exchange is a data inconsistency and raises.
        window_points: ``underlyings[].initial_window`` -- the symmetric half-width in points from
            spot. ``0`` is legal and admits only a strike sitting exactly on spot.
        codec_rule: Which registered :class:`SymbolCodec` this underlying uses.
        expiry_rule: Which registered :class:`ExpiryCalendar` this underlying uses.
    """

    name: str
    exchange: str
    window_points: float
    codec_rule: str
    expiry_rule: str

    def __post_init__(self) -> None:
        for field_name in ("name", "exchange", "codec_rule", "expiry_rule"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"WindowSpec.{field_name} must be a non-empty string, got {value!r}")
        points = self.window_points
        if isinstance(points, bool) or not isinstance(points, (int, float)):
            raise ValueError(f"WindowSpec.window_points must be numeric, got {points!r}")
        if not math.isfinite(float(points)) or float(points) < 0:
            raise ValueError(f"WindowSpec.window_points must be finite and >= 0, got {points!r}")


@dataclass(frozen=True, slots=True)
class WindowResult:
    """The candidate universe for one underlying on one pass.

    ``candidates`` is ordered by ``(strike, option_type, symbol)``. That is an **identity** order, not
    a priority order -- it exists so replay and tests are byte-stable, and F4 remains the only place
    where ranking is defined.
    """

    underlying: str
    status: WindowStatus
    spot: float | None
    atm_strike: float | None
    lower_bound: float | None
    upper_bound: float | None
    candidates: tuple[Instrument, ...]

    @property
    def strikes(self) -> tuple[float, ...]:
        """Distinct candidate strikes, ascending."""
        return tuple(sorted({leg.strike for leg in self.candidates}))

    def __len__(self) -> int:
        return len(self.candidates)


def _sort_key(leg: Instrument) -> tuple[float, str, str]:
    return (float(leg.strike), leg.option_type, leg.symbol)


class WindowManager:
    """Resolves the candidate universe per underlying (§10.2, §15).

    Immutable and threadless: it holds the specs and the seam registries, computes each pass from its
    arguments, and keeps no window state between calls. The never-shrink DSM boundary lives in the
    recorder's FEED thread and is deliberately not mirrored here (§15).
    """

    __slots__ = ("_specs", "_by_name", "_codecs", "_calendars")

    def __init__(
        self,
        specs: Sequence[WindowSpec],
        codecs: Mapping[str, SymbolCodec],
        calendars: Mapping[str, ExpiryCalendar],
    ) -> None:
        if not specs:
            raise FrameworkConfigError(["window manager needs at least one underlying spec"])
        errors: list[str] = []
        by_name: dict[str, WindowSpec] = {}
        for spec in specs:
            if not isinstance(spec, WindowSpec):
                errors.append(f"expected a WindowSpec, got {type(spec).__name__}")
                continue
            if spec.name in by_name:
                errors.append(f"[{spec.name}] duplicate underlying spec")
            by_name[spec.name] = spec
            if spec.codec_rule not in codecs:
                errors.append(
                    f"[{spec.name}] codec rule {spec.codec_rule!r} is not registered; "
                    f"registered rules are {sorted(codecs)}"
                )
            if spec.expiry_rule not in calendars:
                errors.append(
                    f"[{spec.name}] expiry rule {spec.expiry_rule!r} is not registered; "
                    f"registered rules are {sorted(calendars)}"
                )
        if errors:
            raise FrameworkConfigError(errors)
        self._specs = tuple(specs)
        self._by_name = by_name
        self._codecs = dict(codecs)
        self._calendars = dict(calendars)

    @property
    def underlyings(self) -> tuple[str, ...]:
        """Configured underlying names, in configured order -- never mapping-iteration order."""
        return tuple(spec.name for spec in self._specs)

    def spec_for(self, underlying: str) -> WindowSpec:
        """Return one underlying's spec, raising :class:`KeyError` if it is not configured."""
        try:
            return self._by_name[underlying]
        except KeyError:
            raise KeyError(
                f"{underlying!r} is not a configured underlying; configured: {self.underlyings}"
            ) from None

    def codec_for(self, underlying: str) -> SymbolCodec:
        """The :class:`SymbolCodec` registered for this underlying's rule."""
        return self._codecs[self.spec_for(underlying).codec_rule]

    def option_side(self, leg: Instrument) -> OptionSide:
        """Classify one leg's side through its underlying's registered codec."""
        return self.codec_for(leg.underlying).option_side(leg.option_type)

    def candidates(
        self,
        underlying: str,
        spot: float | None,
        universe: Iterable[Instrument],
    ) -> WindowResult:
        """Resolve the candidate universe for one underlying.

        Args:
            underlying: A configured underlying name.
            spot: Last known spot, or ``None`` before the first spot tick. A ``None``, non-positive,
                or non-finite spot yields :attr:`WindowStatus.NO_SPOT` with no candidates -- the
                recorder drops such ticks rather than raising, and so does this.
            universe: Authoritative legs from the instrument master. Legs for other underlyings are
                ignored; a leg claiming this underlying on a contradicting exchange raises.

        Returns:
            A :class:`WindowResult`. Its ``candidates`` are ordered by ``(strike, option_type,
            symbol)`` -- identity order, not priority order.

        Raises:
            KeyError: The underlying is not configured.
            ValueError: A universe leg contradicts the spec's exchange.
        """
        spec = self.spec_for(underlying)

        if spot is None or isinstance(spot, bool) or not isinstance(spot, (int, float)) \
                or not math.isfinite(float(spot)) or float(spot) <= 0:
            return WindowResult(
                underlying=spec.name, status=WindowStatus.NO_SPOT, spot=None, atm_strike=None,
                lower_bound=None, upper_bound=None, candidates=(),
            )
        spot = float(spot)

        expiry = self._calendars[spec.expiry_rule].active_expiry(spec.name)
        if expiry is None:
            return WindowResult(
                underlying=spec.name, status=WindowStatus.NO_EXPIRY, spot=spot, atm_strike=None,
                lower_bound=None, upper_bound=None, candidates=(),
            )

        legs = self._legs_for(spec, expiry, universe)
        if not legs:
            return WindowResult(
                underlying=spec.name, status=WindowStatus.NO_UNIVERSE, spot=spot, atm_strike=None,
                lower_bound=None, upper_bound=None, candidates=(),
            )

        # ATM over the whole active-expiry chain, not over the window: a degenerate window narrower
        # than half a strike step admits no strike, and ATM must still be defined.
        atm = _atm_strike((leg.strike for leg in legs), spot)

        lower = spot - float(spec.window_points)
        upper = spot + float(spec.window_points)
        # Inclusive at both bounds, compared exactly -- the recorder's DSM seeding rule.
        in_window = [leg for leg in legs if lower <= float(leg.strike) <= upper]
        in_window.sort(key=_sort_key)
        return WindowResult(
            underlying=spec.name, status=WindowStatus.RESOLVED, spot=spot,
            atm_strike=atm, lower_bound=lower, upper_bound=upper,
            candidates=tuple(in_window),
        )

    def candidates_for_all(
        self,
        spots: Mapping[str, float | None],
        universe: Iterable[Instrument],
    ) -> tuple[WindowResult, ...]:
        """Resolve every configured underlying, **in configured order**.

        The universe is materialised once so a generator argument is not exhausted by the first
        underlying. An underlying absent from ``spots`` is treated as having no spot yet.
        """
        legs = tuple(universe)
        return tuple(
            self.candidates(spec.name, spots.get(spec.name), legs) for spec in self._specs
        )

    def _legs_for(
        self, spec: WindowSpec, expiry: str, universe: Iterable[Instrument],
    ) -> list[Instrument]:
        """Legs of this underlying at the active expiry, with an exchange contradiction rejected."""
        legs: list[Instrument] = []
        codec = self._codecs[spec.codec_rule]
        for leg in universe:
            if leg.underlying != spec.name:
                continue
            if leg.exchange != spec.exchange:
                raise ValueError(
                    f"[{spec.name}] leg {leg.symbol!r} is on exchange {leg.exchange!r} but the "
                    f"configured option exchange is {spec.exchange!r}"
                )
            # Classify eagerly so an unrecognised tag fails on the pass that saw it, not silently
            # later in the allocator.
            codec.option_side(leg.option_type)
            if leg.expiry == expiry:
                legs.append(leg)
        return legs


def _atm_strike(strikes: Iterable[float], spot: float) -> float | None:
    """The strike nearest to spot, with an exact tie resolving to the **lower** strike.

    This is a decided framework rule (Plan_002 SS15, F3 Decision 2), not an artifact of how the
    universe happened to arrive: for two equally distant strikes the lower one is the ATM, and the
    answer must not depend on list order, dict order, or input ordering. The candidates are sorted
    ascending first and improvement is strict, which delivers exactly that.

    It is also the answer ``processor._resolve_atm`` already gives -- its
    ``min(strikes, key=lambda k: abs(k - spot))`` over the recorder's ascending
    ``active_strikes_list`` returns the first minimum -- so the framework and the recorder agree, with
    the rule made explicit and order-independent here rather than incidental.
    """
    best: float | None = None
    best_distance: float | None = None
    for value in sorted({float(k) for k in strikes}):
        distance = abs(value - spot)
        if best_distance is None or distance < best_distance:
            best, best_distance = value, distance
    return best


def window_specs_from_underlyings(
    underlyings: Sequence[Mapping[str, Any]],
    *,
    codec_rule: str,
    expiry_rule: str,
) -> tuple[WindowSpec, ...]:
    """Build specs from recorder-shaped ``underlyings[]`` entries (§17).

    Only plain mappings cross this boundary, so the framework's one-way dependency on the recorder
    holds: nothing here imports a recorder module. ``codec_rule`` and ``expiry_rule`` are required
    keyword arguments rather than defaults -- a silently defaulted seam is exactly the kind of quiet
    assumption this project fails fast on -- and an entry may name its own rule to override them.

    Raises:
        FrameworkConfigError: With the complete list of problems, never just the first.
    """
    if not underlyings:
        raise FrameworkConfigError(["underlyings[] must define at least one underlying"])
    errors: list[str] = []
    specs: list[WindowSpec] = []
    for index, entry in enumerate(underlyings):
        tag = f"underlyings[{index}]"
        if not isinstance(entry, Mapping):
            errors.append(f"[{tag}] must be a mapping, got {type(entry).__name__}")
            continue
        name = entry.get("name")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"[{tag}.name] must be a non-empty string, got {name!r}")
            name = None
        tag = f"underlyings[{index}]" if name is None else f"underlyings[{name}]"
        exchange = entry.get("option_exchange")
        if not isinstance(exchange, str) or not exchange.strip():
            errors.append(f"[{tag}.option_exchange] must be a non-empty string, got {exchange!r}")
        points = entry.get("initial_window")
        if isinstance(points, bool) or not isinstance(points, (int, float)) \
                or not math.isfinite(float(points)) or float(points) < 0:
            errors.append(f"[{tag}.initial_window] must be a finite number >= 0, got {points!r}")
        entry_codec = entry.get("codec_rule", codec_rule)
        entry_expiry = entry.get("expiry_rule", expiry_rule)
        for key, value in (("codec_rule", entry_codec), ("expiry_rule", entry_expiry)):
            if not isinstance(value, str) or not value.strip():
                errors.append(f"[{tag}.{key}] must be a non-empty string, got {value!r}")
        if errors:
            continue
        specs.append(WindowSpec(
            name=str(name), exchange=str(exchange), window_points=float(points),
            codec_rule=str(entry_codec), expiry_rule=str(entry_expiry),
        ))
    if errors:
        raise FrameworkConfigError(errors)
    return tuple(specs)
