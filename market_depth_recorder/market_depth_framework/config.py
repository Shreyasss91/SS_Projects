"""Framework configuration schema and fail-fast validation (Plan_002 §17).

Mirrors the recorder's ``config.py`` conventions deliberately: a frozen typed config object, a
validator that **collects every error in one pass** so the operator sees all problems at once, and an
error type whose ``report()`` renders them. Missing or out-of-range values fail hard -- there are no
silent defaults, in line with the genericization contract.

Two schema decisions worth stating explicitly, since neither is a plain "required key":

* **The whole ``market_depth_framework`` section is optional in the file.** Absent means the framework
  is off, which is exactly the F1 state -- the recorder's own loader is untouched and never sees this
  section. Present-but-malformed still fails hard. Wiring the section into the shipped ``config.yaml``
  is F8's integration step, not F1's.
* **``total_symbol_budget`` is optional per broker**, and omitting it means :data:`UNLIMITED_BUDGET` --
  "this broker imposes no account-wide cap beyond its connection math". That is a documented semantic
  for an absent *optional* key, not a default silently filling in a required one.

Unknown keys are rejected. A typo'd key that validation ignores is the same failure mode as a silent
default: the operator believes a setting is in force when it is not.

**F1 validates shape, not feasibility.** The §13.2 check
(``min_per_underlying * len(eligible_underlyings) <= effective_budget``) needs both ``effective_budget``
and the eligible-underlying set, which the Broker Capabilities layer resolves in **F2**. F1 checks that
``min_per_underlying`` is a well-formed non-negative int and stops there.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

import yaml

from .capabilities import UNLIMITED_BUDGET, BrokerCapability, PremiumTier, StandardTier

# Top-level key the framework's config lives under, inside the recorder's config file.
FRAMEWORK_SECTION = "market_depth_framework"

_REQUIRED_SECTIONS = ("broker_capabilities", "priority_policy", "budget_allocator",
                      "depth_allocator", "rebalance")
# Present in §17 as a placeholder with no keys of its own -- per-underlying zones are resolved from
# ``underlyings[]`` (F3). Optional until F3 gives it real keys.
_OPTIONAL_SECTIONS = ("window_manager",)

_PRIORITY_POLICIES = ("atm_distance", "blended")
_BUDGET_POLICIES = ("weighted", "equal", "proportional_to_candidates")
_REBALANCE_TRIGGERS = ("interval", "window_change", "both")

_PREMIUM_TIER_KEYS = ("depth", "symbols_per_connection", "max_connections", "max_channels")
_STANDARD_TIER_KEYS = ("depth",)
_CAPABILITY_KEYS = ("premium", "standard", "premium_exchanges", "total_symbol_budget")


class FrameworkConfigError(Exception):
    """Raised when framework config validation fails.

    ``errors`` is the full ordered list, so one run surfaces every problem rather than making the
    operator fix them one restart at a time.
    """

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(f"{len(errors)} framework config validation error(s)")

    def report(self) -> str:
        lines = ["FRAMEWORK CONFIG VALIDATION FAILED:"]
        lines += [f"  - {e}" for e in self.errors]
        return "\n".join(lines)


@dataclass(frozen=True)
class FrameworkConfig:
    """Frozen, validated framework configuration.

    ``broker_capabilities`` is typed all the way down; the behavioural sections stay read-only mappings
    until the phase that owns each one gives it a typed shape (F4 priority policy, F5 allocators,
    F8 rebalance). Typing them now would mean guessing at fields those phases have not designed.
    """

    enabled: bool
    broker_capabilities: Mapping[str, BrokerCapability]
    priority_policy: MappingProxyType
    budget_allocator: MappingProxyType
    depth_allocator: MappingProxyType
    rebalance: MappingProxyType
    window_manager: MappingProxyType


class _Validator:
    """Accumulates errors instead of raising on the first, matching the recorder's ``_Validator``.

    Every accessor guards against a missing or mistyped key, so a malformed config produces a complete
    report rather than crashing the validator partway through.
    """

    def __init__(self) -> None:
        self.errors: list[str] = []

    def fail(self, msg: str) -> None:
        self.errors.append(msg)

    def mapping(self, tag: str, value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            self.fail(f"[{tag}] must be a mapping, got {type(value).__name__}")
            return {}
        return value

    def unknown_keys(self, tag: str, sect: Mapping[str, Any], allowed: tuple[str, ...]) -> None:
        for key in sect:
            if key not in allowed:
                self.fail(f"[{tag}] unknown key {key!r} (allowed: {', '.join(sorted(allowed))})")

    def boolean(self, tag: str, sect: Mapping[str, Any], key: str) -> bool | None:
        if key not in sect:
            self.fail(f"[{tag}] missing required key '{key}'")
            return None
        val = sect[key]
        if not isinstance(val, bool):
            self.fail(f"[{tag}.{key}] must be a boolean, got {val!r}")
            return None
        return val

    def integer(self, tag: str, sect: Mapping[str, Any], key: str, minimum: int) -> int | None:
        if key not in sect:
            self.fail(f"[{tag}] missing required key '{key}'")
            return None
        val = sect[key]
        # Booleans are ints in Python; a YAML ``true`` in a count field is an error, not a 1.
        if isinstance(val, bool) or not isinstance(val, int):
            self.fail(f"[{tag}.{key}] must be an int, got {val!r}")
            return None
        if val < minimum:
            self.fail(f"[{tag}.{key}] must be >= {minimum}, got {val}")
            return None
        return val

    def number(self, tag: str, sect: Mapping[str, Any], key: str, minimum: float) -> float | None:
        if key not in sect:
            self.fail(f"[{tag}] missing required key '{key}'")
            return None
        val = sect[key]
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            self.fail(f"[{tag}.{key}] must be numeric, got {val!r}")
            return None
        if val < minimum:
            self.fail(f"[{tag}.{key}] must be >= {minimum}, got {val}")
            return None
        return float(val)

    def choice(self, tag: str, sect: Mapping[str, Any], key: str,
               allowed: tuple[str, ...]) -> str | None:
        if key not in sect:
            self.fail(f"[{tag}] missing required key '{key}'")
            return None
        val = sect[key]
        if val not in allowed:
            self.fail(f"[{tag}.{key}] must be one of {list(allowed)}, got {val!r}")
            return None
        return val


def _validate_capability(v: _Validator, name: str, raw: Any) -> BrokerCapability | None:
    """Validate one ``broker_capabilities`` entry and build its typed capability."""
    tag = f"{FRAMEWORK_SECTION}.broker_capabilities.{name}"
    sect = v.mapping(tag, raw)
    if not sect:
        return None
    v.unknown_keys(tag, sect, _CAPABILITY_KEYS)

    premium_raw = v.mapping(f"{tag}.premium", sect.get("premium"))
    v.unknown_keys(f"{tag}.premium", premium_raw, _PREMIUM_TIER_KEYS)
    premium_vals = {
        key: v.integer(f"{tag}.premium", premium_raw, key, 1) for key in _PREMIUM_TIER_KEYS
    }

    standard_raw = v.mapping(f"{tag}.standard", sect.get("standard"))
    v.unknown_keys(f"{tag}.standard", standard_raw, _STANDARD_TIER_KEYS)
    standard_depth = v.integer(f"{tag}.standard", standard_raw, "depth", 1)

    exchanges_raw = sect.get("premium_exchanges")
    exchanges: set[str] = set()
    if not isinstance(exchanges_raw, list) or not exchanges_raw:
        v.fail(f"[{tag}.premium_exchanges] must be a non-empty list")
    else:
        for item in exchanges_raw:
            if not isinstance(item, str) or not item.strip():
                v.fail(f"[{tag}.premium_exchanges] must contain non-empty strings, got {item!r}")
            else:
                exchanges.add(item)

    # Optional: absent means "no account-wide cap beyond the connection math" (see module docstring).
    if "total_symbol_budget" in sect:
        total_budget = v.integer(tag, sect, "total_symbol_budget", 1)
    else:
        total_budget = UNLIMITED_BUDGET

    if any(val is None for val in premium_vals.values()):
        return None
    if standard_depth is None or total_budget is None or not exchanges:
        return None

    # Cross-field invariants live on the dataclass; surface them as validation errors rather than
    # letting a ValueError escape and hide the rest of the report.
    try:
        return BrokerCapability(
            broker=name,
            premium=PremiumTier(**premium_vals),  # type: ignore[arg-type]
            standard=StandardTier(depth=standard_depth),
            premium_exchanges=frozenset(exchanges),
            total_symbol_budget=total_budget,
        )
    except ValueError as exc:
        v.fail(f"[{tag}] {exc}")
        return None


def validate_framework_config(root: Mapping[str, Any]) -> FrameworkConfig | None:
    """Validate the framework block inside an already-parsed config root.

    Args:
        root: The whole parsed config mapping (the recorder's ``config.yaml`` root).

    Returns:
        A frozen :class:`FrameworkConfig`, or ``None`` when the section is absent -- which means the
        framework is off and the recorder runs its existing path unchanged.

    Raises:
        FrameworkConfigError: On any validation failure, carrying the complete error list.
    """
    if not isinstance(root, Mapping):
        raise FrameworkConfigError([f"config root must be a mapping, got {type(root).__name__}"])
    if FRAMEWORK_SECTION not in root:
        return None

    v = _Validator()
    sect = v.mapping(FRAMEWORK_SECTION, root[FRAMEWORK_SECTION])
    allowed = ("enabled",) + _REQUIRED_SECTIONS + _OPTIONAL_SECTIONS
    v.unknown_keys(FRAMEWORK_SECTION, sect, allowed)

    enabled = v.boolean(FRAMEWORK_SECTION, sect, "enabled")

    # broker_capabilities
    caps_tag = f"{FRAMEWORK_SECTION}.broker_capabilities"
    caps_raw = sect.get("broker_capabilities")
    capabilities: dict[str, BrokerCapability] = {}
    if not isinstance(caps_raw, dict) or not caps_raw:
        v.fail(f"[{caps_tag}] must be a non-empty mapping of broker name to capability")
    else:
        for broker_name, entry in caps_raw.items():
            built = _validate_capability(v, str(broker_name), entry)
            if built is not None:
                capabilities[str(broker_name)] = built

    # priority_policy
    pp_tag = f"{FRAMEWORK_SECTION}.priority_policy"
    pp = v.mapping(pp_tag, sect.get("priority_policy"))
    v.unknown_keys(pp_tag, pp, ("policy",))
    v.choice(pp_tag, pp, "policy", _PRIORITY_POLICIES)

    # budget_allocator
    ba_tag = f"{FRAMEWORK_SECTION}.budget_allocator"
    ba = v.mapping(ba_tag, sect.get("budget_allocator"))
    v.unknown_keys(ba_tag, ba, ("policy", "min_per_underlying", "weights", "redistribute_unspent"))
    v.choice(ba_tag, ba, "policy", _BUDGET_POLICIES)
    v.integer(ba_tag, ba, "min_per_underlying", 0)
    v.boolean(ba_tag, ba, "redistribute_unspent")
    weights = ba.get("weights")
    if "weights" not in ba:
        v.fail(f"[{ba_tag}] missing required key 'weights'")
    elif not isinstance(weights, dict):
        v.fail(f"[{ba_tag}.weights] must be a mapping of underlying name to weight, got {weights!r}")
    else:
        for key, val in weights.items():
            if isinstance(val, bool) or not isinstance(val, (int, float)) or val <= 0:
                v.fail(f"[{ba_tag}.weights.{key}] must be a positive number, got {val!r}")

    # depth_allocator
    da_tag = f"{FRAMEWORK_SECTION}.depth_allocator"
    da = v.mapping(da_tag, sect.get("depth_allocator"))
    v.unknown_keys(da_tag, da, ("churn_cooldown_seconds", "hysteresis_buffer", "history_limit"))
    v.number(da_tag, da, "churn_cooldown_seconds", 0.0)
    v.integer(da_tag, da, "hysteresis_buffer", 0)
    v.integer(da_tag, da, "history_limit", 1)

    # rebalance
    rb_tag = f"{FRAMEWORK_SECTION}.rebalance"
    rb = v.mapping(rb_tag, sect.get("rebalance"))
    v.unknown_keys(rb_tag, rb, ("trigger", "interval_seconds"))
    v.choice(rb_tag, rb, "trigger", _REBALANCE_TRIGGERS)
    interval = v.number(rb_tag, rb, "interval_seconds", 0.0)
    if interval is not None and interval <= 0:
        v.fail(f"[{rb_tag}.interval_seconds] must be > 0, got {interval}")

    # window_manager - optional placeholder; validated as a mapping if present (F3 gives it keys).
    wm_tag = f"{FRAMEWORK_SECTION}.window_manager"
    wm_raw = sect.get("window_manager")
    window_manager: dict[str, Any] = {}
    if "window_manager" in sect and wm_raw is not None:
        window_manager = v.mapping(wm_tag, wm_raw)

    if v.errors:
        raise FrameworkConfigError(v.errors)

    return FrameworkConfig(
        enabled=bool(enabled),
        broker_capabilities=MappingProxyType(capabilities),
        priority_policy=MappingProxyType(dict(pp)),
        budget_allocator=MappingProxyType(dict(ba)),
        depth_allocator=MappingProxyType(dict(da)),
        rebalance=MappingProxyType(dict(rb)),
        window_manager=MappingProxyType(dict(window_manager)),
    )


def load_framework_config(path: str) -> FrameworkConfig | None:
    """Parse a YAML config file and validate its framework block.

    Returns ``None`` when the file carries no framework section (framework off). Raises
    :class:`FrameworkConfigError` on an unreadable/malformed file or any validation failure.
    """
    try:
        with open(path, encoding="utf-8") as fh:
            raw = yaml.safe_load(fh)
    except FileNotFoundError as exc:
        raise FrameworkConfigError([f"config file not found: {path!r} ({exc})"]) from exc
    except yaml.YAMLError as exc:
        raise FrameworkConfigError([f"config is not well-formed YAML: {exc}"]) from exc
    if not isinstance(raw, dict):
        raise FrameworkConfigError([f"config root must be a mapping, got {type(raw).__name__}"])
    return validate_framework_config(raw)
