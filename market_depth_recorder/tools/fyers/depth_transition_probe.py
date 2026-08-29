#!/usr/bin/env python3
"""F7 depth-transition probe -- what does a 5 <-> 50 depth change actually do? (Plan_002 §20.1)

Measures the real behaviour of the **OpenAlgo proxy path the recorder uses** (``ws://host:8765``,
the ``action: subscribe`` JSON protocol) when an already-subscribed option leg is re-requested at a
different depth. Plan_002 §20.1 forbids guessing this, and §22 orders the evidence document written
*before* the Broker Adapter contract -- this tool produces that evidence.

Unlike ``tbt_channel_probe.py`` / ``tbt_multiconn_probe.py``, which bypass OpenAlgo and drive the
FYERS client directly, this probe deliberately speaks the **proxy** protocol: the Broker Adapter
(F7's output) will sit on exactly that path, so that is the path whose semantics must be measured.
It therefore imports no OpenAlgo platform code at all.

The question, precisely
-----------------------
The recorder encodes depth twice -- a ``:50`` symbol suffix **and** a ``depth`` field -- while the
proxy keys a subscription by ``(symbol, exchange, mode)``, which excludes depth (both source facts;
see ``_depth_probe_model``). So "5 -> 50" may be a depth change on one subscription, or the
creation of a second, independent one. The probe runs both spellings and does not assume they are
the same operation:

    CASE A  logical  ``NIFTY...CE``      + depth=50   (same wire symbol as the depth-5 request)
    CASE B  suffixed ``NIFTY...CE:50``   + depth=50   (the recorder's own spelling)

What counts as an answer
------------------------
A request returning ``status: "success"`` is **not** an answer. Every verdict is classified
``OBSERVED`` / ``INFERRED`` / ``UNKNOWN``, and a transition is only ``DEPTH_CHANGED`` when the
delivered level count was actually observed on *both* sides. All of that logic lives in the pure
sibling ``_depth_probe_model.py`` and is unit-tested offline without a broker.

Safety
------
Dry-run is the default; ``--live`` is required to touch the network, and outside the IST market
session ``--live`` additionally requires ``--allow-outside-session`` (depth ticks only flow in
session, so a probe run before 09:15 measures nothing and merely burns a broker session). At most
:data:`MAX_INSTRUMENTS_HARD_CAP` instruments, one bounded observation window per leg, no retries,
no background thread, and a single synchronous connection closed in a ``finally``.

Typical workflow
  1. After 03:00 IST (past the daily broker-token rollover), start OpenAlgo and log into FYERS.
  2. Confirm the proxy is listening on 8765 and the feed token is populated.
  3. Dry-run first -- it prints the exact frame sequence and writes a dry-run artefact:
       python market_depth_recorder/tools/fyers/depth_transition_probe.py \
           --symbols NIFTY28AUG2624500CE --out /tmp/probe_dryrun.json
  4. In session (09:15-15:30 IST), run live with a current-expiry NFO leg:
       OPENALGO_API_KEY=... python market_depth_recorder/tools/fyers/depth_transition_probe.py \
           --live --symbols NIFTY28AUG2624500CE \
           --out market_depth_recorder/Documents/evidence/depth_transition_YYYYMMDD/depth_transition_probe_YYYYMMDD.json

Full operator procedure: ``Documents/evidence/depth_transition_20260826/depth_transition_probe_runbook_20260826.md``.

Related documentation
  Documents/evidence/depth_transition_20260826/depth_transition_probe_20260826.md   the evidence document this fills in
  Documents/evidence/fyers_tbt_concurrency_20260714/tbt_concurrency_reconciliation_20260714.md   the evidence standard to match
  plans/Plan_002_market_depth_framework_implementation.md §20.1  the probe specification

Exit codes: 0 ran (see report), 2 setup/usage error.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import pathlib
import sys
import time

# Shared model lives in the sibling module (the script dir is on sys.path[0] at launch), exactly as
# the TBT probes import _tbt_common. The model is pure -- it imports no network library.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from _depth_probe_model import (  # noqa: E402
    MAX_INSTRUMENTS_HARD_CAP,
    TBT_SUFFIX,
    Confidence,
    DepthEvidence,
    Mechanism,
    Operation,
    ProbeRequest,
    ProbeResult,
    SupportEvidence,
    SymbolForm,
    TransitionCase,
    TransitionObservation,
    build_evidence,
    build_subscribe_request,
    build_unsubscribe_request,
    default_transition_plan,
    dumps_evidence,
    observe_depth,
    parse_subscribe_ack,
    per_leg_entries,
    requests_for_case,
)

DEFAULT_URL = "ws://127.0.0.1:8765"
DEFAULT_EXCHANGE = "NFO"
DEFAULT_MODE = 3  # Depth. The proxy accepts 1/2/3 or LTP/Quote/Depth.
DEFAULT_OBSERVE_SECS = 12.0
DEFAULT_SETTLE_SECS = 1.0
_IST = _dt.timezone(_dt.timedelta(hours=5, minutes=30))
_SESSION_OPEN = _dt.time(9, 15)
_SESSION_CLOSE = _dt.time(15, 30)


def in_market_session(now: _dt.datetime | None = None) -> bool:
    """Whether ``now`` (default: now, IST) is inside the 09:15-15:30 weekday session.

    A weekday/clock check only -- it knows nothing about exchange holidays, so a ``True`` here is
    necessary but not sufficient. The operator confirms a real feed before trusting a run.
    """
    moment = now.astimezone(_IST) if now is not None else _dt.datetime.now(_IST)
    if moment.weekday() >= 5:
        return False
    return _SESSION_OPEN <= moment.time() <= _SESSION_CLOSE


def logical_of(wire_symbol: str) -> str:
    """The logical symbol behind a wire symbol, dropping any ``:50`` suffix."""
    if wire_symbol.endswith(TBT_SUFFIX):
        return wire_symbol[: -len(TBT_SUFFIX)]
    return wire_symbol


def plan_for(
    cases: tuple[TransitionCase, ...],
    symbols: tuple[str, ...],
    *,
    exchange: str,
    mode: int,
) -> list[tuple[TransitionCase, str, tuple[ProbeRequest, ...]]]:
    """Pair each case with an instrument and its ordered request sequence.

    Cases are spread round-robin over the (at most two) instruments so consecutive cases do not
    fight over one leg's subscription state. The result is deterministic given its inputs.
    """
    out = []
    seq = 0
    for index, case in enumerate(cases):
        symbol = symbols[index % len(symbols)]
        requests = requests_for_case(
            case, logical_symbol=symbol, exchange=exchange, mode=mode, start_seq=seq
        )
        seq += len(requests)
        out.append((case, symbol, requests))
    return out


def _dry_run_report(
    plan: list[tuple[TransitionCase, str, tuple[ProbeRequest, ...]]],
) -> list[ProbeResult]:
    """Turn the planned frames into UNKNOWN-depth results. Nothing is sent; nothing is claimed."""
    results: list[ProbeResult] = []
    for _case, _symbol, requests in plan:
        for request in requests:
            results.append(
                ProbeResult(
                    request=request,
                    depth=DepthEvidence(requested=request.requested_depth),
                    status=None,
                    notes=("dry-run: frame built, not sent",),
                )
            )
    return results


class _Session:
    """One synchronous WebSocket conversation with the OpenAlgo proxy.

    Deliberately blocking and single-threaded: a probe wants deterministic ordering far more than
    throughput, and it keeps the tool free of the background thread a callback client would need
    (Plan_002 four-thread contract). The socket is closed by :meth:`close` on every path.
    """

    def __init__(self, url: str, *, api_key: str, timeout: float = 10.0):
        import websocket  # deferred: importing this module must never require a network library

        self._ws = websocket.create_connection(url, timeout=timeout)
        self._api_key = api_key
        self._inbox: list[dict] = []
        self.send({"action": "authenticate", "api_key": api_key})
        ack = self.read_until(lambda m: "status" in m or "type" in m, deadline_s=timeout)
        self.auth_ack = ack

    def send(self, frame: dict) -> None:
        self._ws.send(json.dumps(frame))

    def _recv(self) -> dict | None:
        import websocket

        try:
            raw = self._ws.recv()
        except websocket.WebSocketTimeoutException:
            return None
        if not raw:
            return None
        try:
            return json.loads(raw)
        except (ValueError, TypeError):
            return None

    def read_until(self, predicate, *, deadline_s: float) -> dict | None:
        """Read frames until ``predicate`` matches or the window expires. Non-matches are kept."""
        end = time.monotonic() + deadline_s
        while time.monotonic() < end:
            message = self._recv()
            if message is None:
                continue
            if predicate(message):
                return message
            self._inbox.append(message)
        return None

    def drain(self, seconds: float) -> list[dict]:
        """Collect every frame arriving in a bounded window, plus anything already buffered."""
        collected = list(self._inbox)
        self._inbox.clear()
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            message = self._recv()
            if message is not None:
                collected.append(message)
        return collected

    def close(self) -> None:
        try:
            self._ws.close()
        except Exception:  # noqa: BLE001 - cleanup must never mask the probe's own result
            pass


def _packets_for(messages: list[dict], logical_symbol: str) -> dict[str, list[dict]]:
    """Group market-data packets for one logical leg by the **wire** symbol they arrived under.

    Grouping by wire symbol is what makes a duplicate subscription visible: if packets arrive under
    both ``X`` and ``X:50`` after a transition, the two spellings are two live subscriptions.
    """
    grouped: dict[str, list[dict]] = {}
    for message in messages:
        symbol = message.get("symbol")
        if not isinstance(symbol, str) or logical_of(symbol) != logical_symbol:
            continue
        grouped.setdefault(symbol, []).append(message)
    return grouped


def _ack_notes(legs, correlated: bool) -> tuple[str, ...]:
    """Record the acknowledgement's *shape* alongside its verdict.

    The proxy answers with an aggregate status plus a list of per-leg entries. Which of the two a
    given result came from is itself one of F7B's questions, so both are written down rather than
    collapsed. ``ack_correlated`` says whether the echoed request_id matched this request; a False
    here means the ack was matched by arrival order and is correspondingly weaker.
    """
    notes = [f"ack_correlated={correlated}", f"ack_per_leg_entries={len(legs)}"]
    for index, entry in enumerate(legs):
        notes.append(
            f"ack_leg[{index}] symbol={entry.get('symbol')!r} status={entry.get('status')!r} "
            f"depth={entry.get('depth')!r} actual_depth={entry.get('actual_depth')!r}"
        )
    return tuple(notes)


def _run_case_live(
    session: _Session,
    case: TransitionCase,
    symbol: str,
    requests: tuple[ProbeRequest, ...],
    *,
    observe_secs: float,
    settle_secs: float,
) -> tuple[list[ProbeResult], TransitionObservation, SupportEvidence | None]:
    """Execute one case and record what was actually seen. No inference beyond the model's rules."""
    results: list[ProbeResult] = []
    before_ev = DepthEvidence(requested=case.from_depth)
    after_ev = DepthEvidence(requested=case.to_depth)
    unsub_support: SupportEvidence | None = None
    duplicate: bool | None = None
    prior_active: bool | None = None
    ack_seen: bool | None = None
    last_before_ts: float | None = None
    first_after_ts: float | None = None

    for request in requests:
        sent = time.time()
        session.send(dict(request.params))
        # Correlate on the echoed request_id when the proxy supplies one, so a stray asynchronous
        # frame cannot be silently mis-attributed to this leg. A proxy that does not echo it sends
        # no request_id at all, and the ack is then accepted on arrival order as before.
        wanted = request.params.get("request_id")
        ack = session.read_until(
            lambda m: str(m.get("type", "")) != "market_data"
            and m.get("request_id") in (None, wanted),
            deadline_s=settle_secs + 4.0,
        )
        status, reported, error = parse_subscribe_ack(ack)
        legs = per_leg_entries(ack)
        correlated = bool(ack) and ack.get("request_id") == wanted
        latency = time.time() - sent
        stamped = ProbeRequest(
            seq=request.seq, operation=request.operation, logical_symbol=request.logical_symbol,
            exchange=request.exchange, wire_symbol=request.wire_symbol,
            symbol_form=request.symbol_form, requested_depth=request.requested_depth,
            mode=request.mode, connection_id=request.connection_id, params=request.params,
            sent_at=sent,
        )

        if request.operation is Operation.UNSUBSCRIBE:
            unsub_support = SupportEvidence(
                operation=Operation.UNSUBSCRIBE, attempted=True,
                accepted=status in ("success", "partial"), error=error,
            )
            results.append(ProbeResult(
                request=stamped, depth=DepthEvidence(requested=request.requested_depth),
                status=status, error=error, latency_s=latency, received_at=time.time(),
                notes=_ack_notes(legs, correlated),
            ))
            continue

        window = session.drain(observe_secs)
        grouped = _packets_for(window, symbol)
        packets = [p for group in grouped.values() for p in group]
        evidence = observe_depth(request.requested_depth, packets, reported=reported)
        results.append(ProbeResult(
            request=stamped, depth=evidence, status=status, error=error,
            latency_s=latency, received_at=time.time(),
            notes=tuple(f"wire_symbol_seen={k} packets={len(v)}" for k, v in sorted(grouped.items()))
            + _ack_notes(legs, correlated),
        ))

        if request.seq == requests[0].seq:
            before_ev = evidence
            last_before_ts = time.time() if packets else None
        elif request is requests[-1]:
            after_ev = evidence
            ack_seen = ack is not None
            first_after_ts = time.time() if packets else None
            live_spellings = {k for k, v in grouped.items() if v}
            if live_spellings:
                duplicate = len(live_spellings) > 1
                prior = requests[0].wire_symbol
                prior_active = prior in live_spellings if prior != request.wire_symbol else None

    transient = None
    if last_before_ts is not None and first_after_ts is not None:
        transient = max(0.0, first_after_ts - last_before_ts - observe_secs)

    observation = TransitionObservation(
        case=case, before=before_ev, after=after_ev,
        prior_still_active=prior_active, duplicate_subscription=duplicate,
        capacity_delta=None,  # not safely measurable without approaching the broker ceiling
        acknowledgement_seen=ack_seen, transient_loss_s=transient,
    )
    return results, observation, unsub_support


def _count_for(messages: list[dict], wire: str) -> int:
    """Packets that arrived under exactly this wire symbol."""
    return sum(1 for m in messages
               if m.get("type") == "market_data" and m.get("symbol") == wire)


def _measure_unsubscribe_effect(
    session: _Session, plan, *, exchange: str, mode: int, observe_secs: float,
) -> tuple[list[ProbeResult], SupportEvidence]:
    """Measure whether unsubscribe actually stops delivery -- not merely whether it is accepted.

    §20.1 PART J insists these are two different questions, and that the second one is not to be
    inferred from the first or from source. So the sequence is observe -> unsubscribe -> observe
    -> **re-subscribe** -> observe. The re-subscribe is the control: without it, silence after an
    unsubscribe is ambiguous (the leg may have stopped, or the whole feed may have gone quiet),
    and an ambiguous silence must not be recorded as proof. ``effect_observed`` is therefore set
    only when the leg was delivering, then went silent, and then delivered again on re-subscribe.
    """
    seen: list[tuple[str, str]] = []
    for _case, symbol, requests in plan:
        for request in requests:
            if request.operation is Operation.SUBSCRIBE:
                pair = (symbol, request.wire_symbol)
                if pair not in seen:
                    seen.append(pair)

    before_window = session.drain(observe_secs)
    live = [(sym, wire, _count_for(before_window, wire)) for sym, wire in seen]
    live = [entry for entry in live if entry[2] > 0]
    if not live:
        # Nothing was delivering, so there is no effect to observe. Not evidence of anything.
        return [], SupportEvidence(operation=Operation.UNSUBSCRIBE, attempted=False)
    # Prefer the premium leg: whether a 50-level slot is genuinely released is the question that
    # matters for capacity planning.
    live.sort(key=lambda e: (not e[1].endswith(TBT_SUFFIX), -e[2]))
    symbol, wire, before_count = live[0]
    form = SymbolForm.SUFFIXED if wire.endswith(TBT_SUFFIX) else SymbolForm.LOGICAL
    depth = 50 if form is SymbolForm.SUFFIXED else 5

    out: list[ProbeResult] = []
    unsub = build_unsubscribe_request(
        seq=9_000, logical_symbol=symbol, exchange=exchange, depth=depth, form=form, mode=mode,
    )
    sent = time.time()
    try:
        session.send(dict(unsub.params))
        wanted = unsub.params.get("request_id")
        ack = session.read_until(
            lambda m: str(m.get("type", "")) != "market_data"
            and m.get("request_id") in (None, wanted),
            deadline_s=5.0,
        )
        status, _reported, error = parse_subscribe_ack(ack)
    except Exception as exc:  # noqa: BLE001 - recorded as evidence, never fatal
        status, error = None, f"{type(exc).__name__}: {exc}"
    unsub_latency = time.time() - sent
    accepted = status in ("success", "partial")

    after_count = _count_for(session.drain(observe_secs), wire)

    # Control: bring the same leg back and confirm the feed can still deliver it.
    resub = build_subscribe_request(
        seq=9_001, logical_symbol=symbol, exchange=exchange, depth=depth, form=form, mode=mode,
    )
    resumed_count = -1
    resub_status = None
    try:
        session.send(dict(resub.params))
        wanted = resub.params.get("request_id")
        session.read_until(
            lambda m: str(m.get("type", "")) != "market_data"
            and m.get("request_id") in (None, wanted),
            deadline_s=5.0,
        )
        resumed_count = _count_for(session.drain(observe_secs), wire)
        resub_status = "sent"
    except Exception as exc:  # noqa: BLE001
        resub_status = f"{type(exc).__name__}: {exc}"

    if after_count > 0:
        effect: bool | None = False           # accepted, yet the data kept coming
    elif resumed_count > 0:
        effect = True                         # went silent, and the feed provably still works
    else:
        effect = None                         # silence we cannot attribute -- stays UNKNOWN

    notes = (
        f"unsub_effect_target={wire}",
        f"packets_before={before_count}",
        f"packets_after_unsubscribe={after_count}",
        f"packets_after_resubscribe={resumed_count}",
        f"resubscribe_control={resub_status}",
        "effect_observed=" + ("unknown" if effect is None else str(effect).lower()),
    )
    out.append(ProbeResult(
        request=unsub, depth=DepthEvidence(requested=depth), status=status, error=error,
        latency_s=unsub_latency, received_at=time.time(), notes=notes,
    ))
    return out, SupportEvidence(
        operation=Operation.UNSUBSCRIBE, attempted=True, accepted=accepted,
        error=error, effect_observed=effect,
    )


def _cleanup(session: _Session, plan, *, exchange: str, mode: int) -> list[ProbeResult]:
    """Best-effort release of every wire symbol the probe subscribed.

    Uses the protocol's own ``unsubscribe`` (a source fact -- ``server.py`` dispatches it); nothing
    is invented for cleanup. Failures are recorded, not raised: a cleanup error is itself evidence.
    """
    seen: list[tuple[str, str]] = []
    for _case, symbol, requests in plan:
        for request in requests:
            if request.operation is Operation.SUBSCRIBE:
                pair = (symbol, request.wire_symbol)
                if pair not in seen:
                    seen.append(pair)
    out: list[ProbeResult] = []
    for seq, (symbol, wire) in enumerate(seen):
        form = SymbolForm.SUFFIXED if wire.endswith(TBT_SUFFIX) else SymbolForm.LOGICAL
        depth = 50 if form is SymbolForm.SUFFIXED else 5
        request = build_unsubscribe_request(
            seq=10_000 + seq, logical_symbol=symbol, exchange=exchange,
            depth=depth, form=form, mode=mode,
        )
        sent = time.time()
        try:
            session.send(dict(request.params))
            ack = session.read_until(lambda m: "status" in m, deadline_s=3.0)
            status, _reported, error = parse_subscribe_ack(ack)
        except Exception as exc:  # noqa: BLE001 - recorded as evidence, never fatal
            status, error = None, f"{type(exc).__name__}: {exc}"
        out.append(ProbeResult(
            request=request, depth=DepthEvidence(requested=depth), status=status,
            error=error, latency_s=time.time() - sent, received_at=time.time(),
            notes=("cleanup",),
        ))
    return out


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="depth_transition_probe.py",
        description="Measure OpenAlgo/FYERS 5 <-> 50 depth-transition behaviour (Plan_002 §20.1).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--live", action="store_true",
                        help="actually connect and send frames (default is dry-run)")
    parser.add_argument("--allow-outside-session", action="store_true",
                        help="permit --live outside 09:15-15:30 IST (measures nothing; not advised)")
    parser.add_argument("--symbols", default="",
                        help=f"comma-separated logical symbols (max {MAX_INSTRUMENTS_HARD_CAP})")
    parser.add_argument("--exchange", default=DEFAULT_EXCHANGE,
                        help="exchange for the option legs (50-level needs NSE/NFO)")
    parser.add_argument("--mode", type=int, default=DEFAULT_MODE, help="proxy mode (3 = Depth)")
    parser.add_argument("--url", default=DEFAULT_URL, help="OpenAlgo WebSocket proxy URL")
    parser.add_argument("--observe-secs", type=float, default=DEFAULT_OBSERVE_SECS,
                        help="market-data observation window per subscribe")
    parser.add_argument("--settle-secs", type=float, default=DEFAULT_SETTLE_SECS,
                        help="grace period before reading an acknowledgement")
    parser.add_argument("--cases", default="",
                        help="comma-separated case ids to run (default: the full §20.1 plan)")
    parser.add_argument("--out", default="", help="write the evidence JSON here")
    parser.add_argument("--no-cleanup", action="store_true",
                        help="skip the unsubscribe sweep (leaves live subscriptions; not advised)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    symbols = tuple(s.strip() for s in args.symbols.split(",") if s.strip())
    if not symbols:
        print("error: --symbols is required (1 or 2 current-expiry legs)", file=sys.stderr)
        return 2
    if len(symbols) > MAX_INSTRUMENTS_HARD_CAP:
        print(f"error: at most {MAX_INSTRUMENTS_HARD_CAP} instruments "
              f"(safety limit), got {len(symbols)}", file=sys.stderr)
        return 2

    cases = default_transition_plan()
    if args.cases:
        wanted = {c.strip() for c in args.cases.split(",") if c.strip()}
        cases = tuple(c for c in cases if c.case_id in wanted)
        if not cases:
            print(f"error: no case matched {sorted(wanted)}", file=sys.stderr)
            return 2

    plan = plan_for(cases, symbols, exchange=args.exchange, mode=args.mode)
    environment = {
        "tool": "depth_transition_probe.py",
        "generated_at": _dt.datetime.now(_IST).isoformat(),
        "url": args.url,
        "exchange": args.exchange,
        "mode": args.mode,
        "symbols": list(symbols),
        "cases": [c.case_id for c in cases],
        "observe_secs": args.observe_secs,
        "in_market_session": in_market_session(),
        "python": sys.version.split()[0],
    }

    if not args.live:
        results = _dry_run_report(plan)
        evidence = build_evidence(mode="dry-run", environment=environment, results=results)
        print(f"DRY RUN -- {len(plan)} case(s), {len(results)} frame(s) built, none sent.")
        for case, symbol, requests in plan:
            print(f"  {case.case_id}: {case.label}  [{symbol}]")
            for request in requests:
                print(f"    #{request.seq} {request.operation} {request.wire_symbol} "
                      f"depth={request.requested_depth} mode={request.mode}")
        print("\nAll depth results are UNKNOWN: a dry run is not broker evidence.")
        _write(args.out, evidence)
        return 0

    api_key = os.environ.get("OPENALGO_API_KEY", "").strip()
    if not api_key:
        print("error: --live needs OPENALGO_API_KEY in the environment (never pass it on the "
              "command line -- it would land in your shell history)", file=sys.stderr)
        return 2
    if not in_market_session() and not args.allow_outside_session:
        print("error: outside the 09:15-15:30 IST session, depth ticks do not flow, so a live run "
              "would measure nothing. Re-run in session, or pass --allow-outside-session if you "
              "deliberately want the protocol-only answers.", file=sys.stderr)
        return 2

    try:
        session = _Session(args.url, api_key=api_key)
    except Exception as exc:  # noqa: BLE001 - a setup failure is a usage error, not a result
        print(f"error: cannot reach the OpenAlgo proxy at {args.url}: "
              f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    all_results: list[ProbeResult] = []
    observations: list[TransitionObservation] = []
    support: list[SupportEvidence] = []
    try:
        for case, symbol, requests in plan:
            results, observation, unsub = _run_case_live(
                session, case, symbol, requests,
                observe_secs=args.observe_secs, settle_secs=args.settle_secs,
            )
            all_results.extend(results)
            observations.append(observation)
            if unsub is not None:
                support.append(unsub)
            print(f"  {case.case_id}: {observation.outcome} ({observation.confidence})")
        unsub_results, unsub_effect = _measure_unsubscribe_effect(
            session, plan, exchange=args.exchange, mode=args.mode,
            observe_secs=args.observe_secs,
        )
        all_results.extend(unsub_results)
        if unsub_effect.attempted:
            support.append(unsub_effect)
        if not args.no_cleanup:
            all_results.extend(_cleanup(session, plan, exchange=args.exchange, mode=args.mode))
    finally:
        session.close()

    if not any(s.operation is Operation.UNSUBSCRIBE for s in support):
        support.append(SupportEvidence(operation=Operation.UNSUBSCRIBE, attempted=False))
    evidence = build_evidence(
        mode="live", environment=environment, results=all_results,
        observations=observations, support=support,
    )
    _summarise(observations)
    _write(args.out, evidence)
    return 0


def _summarise(observations: list[TransitionObservation]) -> None:
    print("\nTransition results (a verdict needs BOTH sides observed):")
    for obs in observations:
        before = obs.before.effective_depth
        after = obs.after.effective_depth
        print(f"  {obs.case.case_id:<24} {obs.outcome!s:<16} confidence={obs.confidence} "
              f"observed {before} -> {after}")
    unknown = sum(1 for o in observations if o.confidence is not Confidence.OBSERVED)
    if unknown:
        print(f"\n{unknown} case(s) did not reach OBSERVED -- record them as UNKNOWN, not as 'no'.")


def _write(path: str, evidence: dict) -> None:
    if not path:
        return
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(dumps_evidence(evidence), encoding="utf-8")
    print(f"\nevidence written: {target}")


if __name__ == "__main__":
    raise SystemExit(main())
