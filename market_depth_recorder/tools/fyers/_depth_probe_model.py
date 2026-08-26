#!/usr/bin/env python3
"""Broker-neutral data model for the F7 depth-transition probe (Plan_002 §20.1).

This module is **pure**: it builds probe requests, parses probe responses, classifies what the
evidence actually supports, and serialises the result. It performs **no network I/O, no file I/O,
and no broker import** -- at import time or at any other time. The live wire work belongs to the
sibling runner ``depth_transition_probe.py``; keeping the model separate is what makes the whole
classification path testable offline without a broker.

Why a model at all
------------------
Plan_002 §20.1 refuses to guess the depth-transition mechanism, and the failure mode it guards
against is subtle: a subscribe request that returns ``status: "success"`` proves only that the
request was *accepted*. It does not prove the delivered depth changed. This module makes that
distinction structural rather than a matter of discipline -- see :class:`DepthEvidence`, whose
:attr:`~DepthEvidence.confidence` is ``OBSERVED`` only when market-data levels were actually
counted, and :func:`classify_transition`, which returns ``UNKNOWN`` unless *both* sides were
observed. There is deliberately no code path that promotes an acknowledgement to an observation.

The three depths, never conflated
---------------------------------
``requested``  what the probe asked for (the ``depth`` field in the subscribe frame)
``reported``   what the acknowledgement echoed back (proxy ``actual_depth`` / ``depth``)
``observed``   how many levels were actually counted in delivered market-data packets

Only ``observed`` is evidence of delivered depth. ``reported`` is evidence about the
acknowledgement, which is a different claim.

Two symbol forms, never assumed equivalent
------------------------------------------
The recorder encodes depth twice -- it appends a ``:50`` suffix to the symbol *and* sends a
``depth`` field (source fact, ``websocket_client.wire_symbol``). The OpenAlgo proxy keys a
subscription by ``(symbol, exchange, mode)``, which does **not** include depth (source fact,
``websocket_proxy/server.py``). Whether a same-symbol depth change and a suffixed-symbol depth
change are the same operation is therefore an open empirical question, so :class:`SymbolForm`
keeps them distinct and the default plan runs both.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping

# The suffix the recorder appends for a deep-book request, and the depth at or below which it does
# not. Mirrored here (not imported) so the probe can build the *logical* form at depth 50 too --
# the recorder itself cannot express that, and it is exactly the case the probe must isolate.
TBT_SUFFIX = ":50"
TBT_MIN_DEPTH = 5

# Safety: the probe is a measurement, not a load test (Plan_002 §20.1 deliverable standard).
MAX_INSTRUMENTS_HARD_CAP = 2

_SECRET_HINTS = ("api_key", "apikey", "token", "secret", "password", "auth", "pepper")
_REDACTED = "[REDACTED]"


class Operation(Enum):
    """A single wire operation the probe can issue."""

    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    RECONNECT = "reconnect"
    OBSERVE = "observe"

    def __str__(self) -> str:
        return self.value


class SymbolForm(Enum):
    """How the depth request is spelled on the wire.

    ``LOGICAL``  the bare symbol; depth carried only by the ``depth`` field (CASE A)
    ``SUFFIXED`` the recorder's ``SYMBOL:50`` spelling plus the ``depth`` field (CASE B)
    """

    LOGICAL = "logical"
    SUFFIXED = "suffixed"

    def __str__(self) -> str:
        return self.value


class Mechanism(Enum):
    """Which candidate transition mechanism a case exercises. §20.1 requires both, separately."""

    BARE_RESUBSCRIBE = "bare_resubscribe"
    UNSUBSCRIBE_THEN_SUBSCRIBE = "unsubscribe_then_subscribe"

    def __str__(self) -> str:
        return self.value


class Confidence(Enum):
    """What the evidence actually supports. Never widened by convenience."""

    OBSERVED = "observed"
    INFERRED = "inferred"
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        return self.value


class TransitionOutcome(Enum):
    """The verdict for one transition case."""

    DEPTH_CHANGED = "depth_changed"
    DEPTH_UNCHANGED = "depth_unchanged"
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        return self.value


def probe_wire_symbol(symbol: str, depth: int, form: SymbolForm) -> str:
    """Spell ``symbol`` for a ``depth`` request in the requested ``form``.

    ``LOGICAL`` never suffixes -- that is the whole point of CASE A, and the recorder cannot
    produce it. ``SUFFIXED`` reproduces the recorder's rule: suffix only above the broker default.
    """
    if not isinstance(symbol, str) or not symbol:
        raise ValueError("symbol must be a non-empty string")
    if isinstance(depth, bool) or not isinstance(depth, int) or depth <= 0:
        raise ValueError(f"depth must be a positive int, got {depth!r}")
    if not isinstance(form, SymbolForm):
        raise TypeError(f"form must be a SymbolForm, got {type(form).__name__}")
    if form is SymbolForm.SUFFIXED and depth > TBT_MIN_DEPTH:
        return f"{symbol}{TBT_SUFFIX}"
    return symbol


def redact(params: Mapping[str, Any]) -> dict[str, Any]:
    """Copy ``params`` with any secret-looking value replaced.

    Matching is on the key name, case-insensitively, by substring -- so ``api_key``, ``API_KEY``
    and ``broker_api_secret`` are all caught. Non-secret values pass through untouched. Evidence
    files are committed, so nothing unredacted may reach one.
    """
    out: dict[str, Any] = {}
    for key, value in params.items():
        lowered = str(key).lower()
        out[key] = _REDACTED if any(hint in lowered for hint in _SECRET_HINTS) else value
    return out


@dataclass(frozen=True, slots=True)
class DepthEvidence:
    """The three depths, kept apart, plus the confidence that follows from them.

    ``observed_packets`` is the number of market-data packets the ``observed`` count rests on.
    A count with zero packets behind it is not an observation, so it does not earn ``OBSERVED``.
    """

    requested: int
    reported: int | None = None
    observed: int | None = None
    observed_packets: int = 0

    def __post_init__(self) -> None:
        if isinstance(self.requested, bool) or not isinstance(self.requested, int):
            raise TypeError("requested depth must be an int")
        if self.requested <= 0:
            raise ValueError("requested depth must be positive")
        if self.observed_packets < 0:
            raise ValueError("observed_packets cannot be negative")

    @property
    def confidence(self) -> Confidence:
        """``OBSERVED`` only when levels were counted in delivered packets.

        An acknowledgement alone is ``INFERRED``: it is evidence about what the broker *said*,
        never about what it *sent*. Nothing here promotes one to the other.
        """
        if self.observed is not None and self.observed_packets > 0:
            return Confidence.OBSERVED
        if self.reported is not None:
            return Confidence.INFERRED
        return Confidence.UNKNOWN

    @property
    def effective_depth(self) -> int | None:
        """The delivered depth, or ``None`` when it was not observed.

        Deliberately does **not** fall back to ``reported`` or ``requested``. A caller that wants
        a number must cope with not getting one.
        """
        return self.observed if self.confidence is Confidence.OBSERVED else None


@dataclass(frozen=True, slots=True)
class ProbeRequest:
    """One wire operation, fully described for audit. ``params`` must already be redacted."""

    seq: int
    operation: Operation
    logical_symbol: str
    exchange: str
    wire_symbol: str
    symbol_form: SymbolForm
    requested_depth: int
    mode: int
    connection_id: str
    params: Mapping[str, Any] = field(default_factory=dict)
    sent_at: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.params, Mapping):
            raise TypeError("params must be a mapping")
        leaked = [
            key for key, value in self.params.items()
            if any(hint in str(key).lower() for hint in _SECRET_HINTS) and value != _REDACTED
        ]
        if leaked:
            raise ValueError(f"unredacted secret-looking params: {sorted(leaked)}")


@dataclass(frozen=True, slots=True)
class ProbeResult:
    """What came back for one :class:`ProbeRequest`, and what it is worth as evidence."""

    request: ProbeRequest
    depth: DepthEvidence
    status: str | None = None
    error: str | None = None
    latency_s: float | None = None
    received_at: float | None = None
    notes: tuple[str, ...] = ()

    @property
    def accepted(self) -> bool:
        """Whether the *request* was accepted. Says nothing about delivered depth."""
        return self.status in ("success", "partial")


@dataclass(frozen=True, slots=True)
class TransitionCase:
    """One row of the §20.1 transition matrix, in one symbol form, by one mechanism."""

    case_id: str
    from_depth: int
    to_depth: int
    symbol_form: SymbolForm
    mechanism: Mechanism = Mechanism.BARE_RESUBSCRIBE

    @property
    def label(self) -> str:
        return f"{self.from_depth}->{self.to_depth} {self.symbol_form} {self.mechanism}"


@dataclass(frozen=True, slots=True)
class TransitionObservation:
    """The before/after pair for one case, plus the side questions §20.1 asks."""

    case: TransitionCase
    before: DepthEvidence
    after: DepthEvidence
    prior_still_active: bool | None = None
    duplicate_subscription: bool | None = None
    capacity_delta: int | None = None
    acknowledgement_seen: bool | None = None
    transient_loss_s: float | None = None

    @property
    def outcome(self) -> TransitionOutcome:
        return classify_transition(self.before, self.after)

    @property
    def confidence(self) -> Confidence:
        """The weaker of the two sides -- a transition is only as good as its worse observation."""
        return weakest(self.before.confidence, self.after.confidence)


def weakest(*confidences: Confidence) -> Confidence:
    """The least-supported of ``confidences``. UNKNOWN dominates, then INFERRED."""
    order = {Confidence.UNKNOWN: 0, Confidence.INFERRED: 1, Confidence.OBSERVED: 2}
    if not confidences:
        return Confidence.UNKNOWN
    return min(confidences, key=lambda conf: order[conf])


def classify_transition(before: DepthEvidence, after: DepthEvidence) -> TransitionOutcome:
    """Decide whether the delivered depth changed.

    Returns ``UNKNOWN`` unless **both** sides were actually observed. This is the single guard
    that stops "the request succeeded" from becoming "the depth changed" (§20.1): an
    acknowledgement echoing ``actual_depth: 50`` is ``INFERRED``, and two ``INFERRED`` sides still
    yield ``UNKNOWN``.
    """
    if before.confidence is not Confidence.OBSERVED:
        return TransitionOutcome.UNKNOWN
    if after.confidence is not Confidence.OBSERVED:
        return TransitionOutcome.UNKNOWN
    if before.effective_depth == after.effective_depth:
        return TransitionOutcome.DEPTH_UNCHANGED
    return TransitionOutcome.DEPTH_CHANGED


@dataclass(frozen=True, slots=True)
class SupportEvidence:
    """Whether some operation (e.g. unsubscribe) is supported by the live path.

    ``attempted=False`` yields ``UNKNOWN`` no matter what else is set: absence of a test is not
    evidence of absence (§20.1).
    """

    operation: Operation
    attempted: bool = False
    accepted: bool | None = None
    error: str | None = None
    effect_observed: bool | None = None

    @property
    def confidence(self) -> Confidence:
        if not self.attempted:
            return Confidence.UNKNOWN
        if self.effect_observed is not None:
            return Confidence.OBSERVED
        return Confidence.INFERRED

    @property
    def supported(self) -> bool | None:
        """``True``/``False`` only on evidence; ``None`` means not established.

        An accepted request with no observed effect stays ``None`` -- acceptance is not proof the
        operation did anything. An explicit rejection is enough to say ``False``.
        """
        if not self.attempted:
            return None
        if self.effect_observed is not None:
            return bool(self.effect_observed)
        if self.accepted is False:
            return False
        return None


def default_transition_plan() -> tuple[TransitionCase, ...]:
    """The minimal deterministic case set that answers §20.1 on at most two instruments.

    Covers all four transitions; runs 5->50 in both symbol forms (the CASE A / CASE B question)
    and 5->50 / 50->5 by both mechanisms, and keeps the two idempotent rows in the logical form
    only -- they are controls, and a second spelling of a no-op buys nothing.
    """
    return (
        TransitionCase("C1_5_5_logical", 5, 5, SymbolForm.LOGICAL),
        TransitionCase("C2_5_50_logical", 5, 50, SymbolForm.LOGICAL),
        TransitionCase("C3_5_50_suffixed", 5, 50, SymbolForm.SUFFIXED),
        TransitionCase("C4_50_50_logical", 50, 50, SymbolForm.LOGICAL),
        TransitionCase("C5_50_5_logical", 50, 5, SymbolForm.LOGICAL),
        TransitionCase(
            "C6_5_50_logical_unsub", 5, 50, SymbolForm.LOGICAL,
            Mechanism.UNSUBSCRIBE_THEN_SUBSCRIBE,
        ),
        TransitionCase(
            "C7_50_5_logical_unsub", 50, 5, SymbolForm.LOGICAL,
            Mechanism.UNSUBSCRIBE_THEN_SUBSCRIBE,
        ),
    )


def probe_request_id(seq: int) -> str:
    """Deterministic correlation id for one probe request.

    The proxy echoes a supplied ``request_id`` back in its acknowledgement (source fact,
    ``websocket_proxy/server.py``). Without it an ack can only be matched to a request by arrival
    order, so a stray asynchronous frame would be silently mis-attributed to the wrong leg -- and a
    one-shot live run has no second chance to notice. Derived from ``seq`` so evidence stays
    byte-for-byte reproducible.
    """
    return f"probe-{seq}"


def build_subscribe_request(
    *,
    seq: int,
    logical_symbol: str,
    exchange: str,
    depth: int,
    form: SymbolForm,
    mode: int,
    connection_id: str = "c0",
    extra: Mapping[str, Any] | None = None,
) -> ProbeRequest:
    """Build one subscribe :class:`ProbeRequest`, with ``params`` redacted up front."""
    wire = probe_wire_symbol(logical_symbol, depth, form)
    params: dict[str, Any] = {
        "action": str(Operation.SUBSCRIBE),
        "symbol": wire,
        "exchange": exchange,
        "mode": mode,
        "depth": depth,
        "request_id": probe_request_id(seq),
    }
    if extra:
        params.update(extra)
    return ProbeRequest(
        seq=seq,
        operation=Operation.SUBSCRIBE,
        logical_symbol=logical_symbol,
        exchange=exchange,
        wire_symbol=wire,
        symbol_form=form,
        requested_depth=depth,
        mode=mode,
        connection_id=connection_id,
        params=redact(params),
    )


def build_unsubscribe_request(
    *,
    seq: int,
    logical_symbol: str,
    exchange: str,
    depth: int,
    form: SymbolForm,
    mode: int,
    connection_id: str = "c0",
    extra: Mapping[str, Any] | None = None,
) -> ProbeRequest:
    """Build one unsubscribe :class:`ProbeRequest` mirroring a prior subscribe's spelling."""
    wire = probe_wire_symbol(logical_symbol, depth, form)
    params: dict[str, Any] = {
        "action": str(Operation.UNSUBSCRIBE),
        "symbol": wire,
        "exchange": exchange,
        "mode": mode,
        "request_id": probe_request_id(seq),
    }
    if extra:
        params.update(extra)
    return ProbeRequest(
        seq=seq,
        operation=Operation.UNSUBSCRIBE,
        logical_symbol=logical_symbol,
        exchange=exchange,
        wire_symbol=wire,
        symbol_form=form,
        requested_depth=depth,
        mode=mode,
        connection_id=connection_id,
        params=redact(params),
    )


def requests_for_case(
    case: TransitionCase,
    *,
    logical_symbol: str,
    exchange: str,
    mode: int,
    start_seq: int = 0,
    connection_id: str = "c0",
) -> tuple[ProbeRequest, ...]:
    """The ordered wire operations for one case: establish ``from_depth``, then transition.

    ``BARE_RESUBSCRIBE`` issues subscribe(from) then subscribe(to).
    ``UNSUBSCRIBE_THEN_SUBSCRIBE`` issues subscribe(from), unsubscribe(from), subscribe(to).

    The establishing leg always uses the recorder's own spelling for its depth, so every case
    starts from the state the recorder would really be in; only the transition leg carries the
    case's ``symbol_form``, since that spelling is the variable under test.
    """
    seq = start_seq
    out: list[ProbeRequest] = [
        build_subscribe_request(
            seq=seq, logical_symbol=logical_symbol, exchange=exchange,
            depth=case.from_depth, form=SymbolForm.SUFFIXED, mode=mode,
            connection_id=connection_id,
        )
    ]
    seq += 1
    if case.mechanism is Mechanism.UNSUBSCRIBE_THEN_SUBSCRIBE:
        out.append(build_unsubscribe_request(
            seq=seq, logical_symbol=logical_symbol, exchange=exchange,
            depth=case.from_depth, form=SymbolForm.SUFFIXED, mode=mode,
            connection_id=connection_id,
        ))
        seq += 1
    out.append(build_subscribe_request(
        seq=seq, logical_symbol=logical_symbol, exchange=exchange,
        depth=case.to_depth, form=case.symbol_form, mode=mode,
        connection_id=connection_id,
    ))
    return tuple(out)


def _depth_in(payload: Mapping[str, Any]) -> int | None:
    """Read a depth value from one mapping, ``actual_depth`` first, or ``None``.

    ``actual_depth`` is preferred because the proxy fills the per-leg ``depth`` with
    ``response.get("actual_depth", depth_level)`` -- i.e. it falls back to echoing *our own
    requested* depth when the adapter reports nothing (source fact, ``websocket_proxy/server.py``).
    So neither key is broker evidence; ``depth`` especially cannot be trusted as the broker's
    answer. A missing, boolean or non-numeric value yields ``None``, never a substituted request
    value.
    """
    for key in ("actual_depth", "depth"):
        value = payload.get(key)
        if isinstance(value, bool):
            continue
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.strip().lstrip("-").isdigit():
            return int(value)
    return None


def per_leg_entries(payload: Mapping[str, Any] | None) -> tuple[Mapping[str, Any], ...]:
    """Return the per-leg result entries carried inside a proxy acknowledgement.

    The proxy's ack is two-level (source fact, ``websocket_proxy/server.py``): an aggregate
    ``status`` at the top plus a list of per-leg dicts -- ``subscriptions`` for subscribe,
    ``successful`` / ``failed`` for unsubscribe. Recording both levels is what lets the evidence
    distinguish "the request was accepted" from "this particular leg was accepted", which is
    exactly the acknowledgement question F7B has to answer.
    """
    if not isinstance(payload, Mapping):
        return ()
    out: list[Mapping[str, Any]] = []
    for key in ("subscriptions", "successful", "failed"):
        value = payload.get(key)
        if isinstance(value, (list, tuple)):
            out.extend(entry for entry in value if isinstance(entry, Mapping))
    return tuple(out)


def parse_subscribe_ack(
    payload: Mapping[str, Any] | None,
) -> tuple[str | None, int | None, str | None]:
    """Extract ``(status, reported_depth, error)`` from a proxy acknowledgement.

    ``status`` is the aggregate status; ``per_leg_entries`` exposes the per-leg detail alongside
    it. The reported depth is taken from the per-leg entry when the ack carries one, because that
    is where the real frame puts it -- the top level has no depth field at all -- and falls back to
    a flat payload for already-unwrapped inputs. Whatever it comes from it is only ever
    :attr:`Confidence.INFERRED`; see :func:`_depth_in`.

    ``error`` is a *genuine* error only. The proxy sends an informational ``message`` --
    "Subscription processing complete" -- alongside a **successful** ack, so treating any
    ``message`` as an error would stamp a false error onto every good result. A message is
    surfaced only when the aggregate status is not success/partial, or when it belongs to a
    per-leg entry that itself failed.
    """
    if not isinstance(payload, Mapping):
        return None, None, None
    status = payload.get("status")
    status = str(status) if status is not None else None

    legs = per_leg_entries(payload)
    reported: int | None = None
    for entry in legs:
        reported = _depth_in(entry)
        if reported is not None:
            break
    if reported is None and not legs:
        reported = _depth_in(payload)

    error: str | None = None
    for entry in legs:
        if str(entry.get("status", "")).lower() not in ("success", "partial"):
            message = entry.get("message") or entry.get("error")
            if message is not None:
                error = str(message)
                break
    if error is None:
        explicit = payload.get("error")
        if explicit is not None:
            error = str(explicit)
        elif status is not None and status.lower() not in ("success", "partial"):
            message = payload.get("message")
            error = str(message) if message is not None else None
        elif status is None:
            message = payload.get("message")
            error = str(message) if message is not None else None
    return status, reported, error


def count_depth_levels(packet: Mapping[str, Any] | None) -> int | None:
    """Count bid/ask levels actually present in one market-data packet.

    Returns the larger of the two side lengths, or ``None`` when the packet carries no book at
    all. ``None`` means "not observed" and must not be read as zero levels.

    The proxy's market-data frame is an *envelope* -- ``{"type": "market_data", "symbol": ...,
    "exchange": ..., "mode": ..., "data": {...}}`` -- and the book lives one level down at
    ``data.depth`` (source fact, ``websocket_proxy/server.py`` base_message; confirmed against the
    recorder's own reader, ``websocket_client.py`` ``normalize_market_data`` and the preflight
    probe, which both read ``msg["data"]["depth"]``). Reading ``packet["depth"]`` directly would
    silently return ``None`` for every real packet -- every case UNKNOWN, a wasted live session --
    so the envelope is unwrapped first and the flat form is still accepted for already-normalized
    payloads.
    """
    if not isinstance(packet, Mapping):
        return None
    book = packet.get("depth")
    if not isinstance(book, Mapping):
        payload = packet.get("data")
        book = payload.get("depth") if isinstance(payload, Mapping) else None
    if not isinstance(book, Mapping):
        return None
    sides = [
        len(value) for side in ("buy", "bids", "sell", "asks")
        if isinstance(value := book.get(side), (list, tuple))
    ]
    if not sides:
        return None
    return max(sides)


def observe_depth(
    requested: int,
    packets: Iterable[Mapping[str, Any]],
    *,
    reported: int | None = None,
) -> DepthEvidence:
    """Fold delivered packets into a :class:`DepthEvidence`.

    Takes the **maximum** level count seen: a depth feed sends a full snapshot then incrementals,
    and a thin incremental must not be mistaken for a shallower book. Packets carrying no book at
    all do not count as observations.
    """
    best: int | None = None
    counted = 0
    for packet in packets:
        levels = count_depth_levels(packet)
        if levels is None:
            continue
        counted += 1
        best = levels if best is None else max(best, levels)
    return DepthEvidence(
        requested=requested, reported=reported, observed=best, observed_packets=counted
    )


def result_to_dict(result: ProbeResult) -> dict[str, Any]:
    """One :class:`ProbeResult` as JSON-ready primitives, confidence included."""
    req = result.request
    return {
        "seq": req.seq,
        "operation": str(req.operation),
        "logical_symbol": req.logical_symbol,
        "exchange": req.exchange,
        "wire_symbol": req.wire_symbol,
        "symbol_form": str(req.symbol_form),
        "requested_depth": req.requested_depth,
        "mode": req.mode,
        "connection_id": req.connection_id,
        "params": dict(req.params),
        "sent_at": req.sent_at,
        "received_at": result.received_at,
        "latency_s": result.latency_s,
        "status": result.status,
        "error": result.error,
        "accepted": result.accepted,
        "depth": {
            "requested": result.depth.requested,
            "reported": result.depth.reported,
            "observed": result.depth.observed,
            "observed_packets": result.depth.observed_packets,
            "confidence": str(result.depth.confidence),
            "effective_depth": result.depth.effective_depth,
        },
        "notes": list(result.notes),
    }


def observation_to_dict(obs: TransitionObservation) -> dict[str, Any]:
    """One :class:`TransitionObservation` as JSON-ready primitives."""
    return {
        "case_id": obs.case.case_id,
        "label": obs.case.label,
        "from_depth": obs.case.from_depth,
        "to_depth": obs.case.to_depth,
        "symbol_form": str(obs.case.symbol_form),
        "mechanism": str(obs.case.mechanism),
        "outcome": str(obs.outcome),
        "confidence": str(obs.confidence),
        "before": {
            "requested": obs.before.requested,
            "reported": obs.before.reported,
            "observed": obs.before.observed,
            "observed_packets": obs.before.observed_packets,
            "confidence": str(obs.before.confidence),
        },
        "after": {
            "requested": obs.after.requested,
            "reported": obs.after.reported,
            "observed": obs.after.observed,
            "observed_packets": obs.after.observed_packets,
            "confidence": str(obs.after.confidence),
        },
        "prior_still_active": obs.prior_still_active,
        "duplicate_subscription": obs.duplicate_subscription,
        "capacity_delta": obs.capacity_delta,
        "acknowledgement_seen": obs.acknowledgement_seen,
        "transient_loss_s": obs.transient_loss_s,
    }


def build_evidence(
    *,
    mode: str,
    environment: Mapping[str, Any],
    results: Iterable[ProbeResult] = (),
    observations: Iterable[TransitionObservation] = (),
    support: Iterable[SupportEvidence] = (),
) -> dict[str, Any]:
    """Assemble the full evidence record.

    ``mode`` is ``"dry-run"`` or ``"live"`` and is recorded verbatim, together with an explicit
    ``is_broker_evidence`` flag, so a dry-run artefact can never be mistaken for broker evidence
    when it is read back later.
    """
    return {
        "schema": "market_depth_recorder.depth_transition_probe/1",
        "mode": mode,
        "is_broker_evidence": mode == "live",
        "environment": redact(environment),
        "results": [result_to_dict(result) for result in results],
        "observations": [observation_to_dict(obs) for obs in observations],
        "support": [
            {
                "operation": str(item.operation),
                "attempted": item.attempted,
                "accepted": item.accepted,
                "error": item.error,
                "effect_observed": item.effect_observed,
                "confidence": str(item.confidence),
                "supported": item.supported,
            }
            for item in support
        ],
    }


def dumps_evidence(evidence: Mapping[str, Any]) -> str:
    """Serialise an evidence record deterministically (stable key order, trailing newline)."""
    return json.dumps(evidence, indent=2, sort_keys=True, default=str) + "\n"
