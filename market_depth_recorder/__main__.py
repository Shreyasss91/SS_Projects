"""Command-line entrypoint for the Market Depth Recorder (spec §8.2).

Run from the parent ``SS_Projects/``::

    python -m market_depth_recorder --validate-config --config market_depth_recorder/config.yaml

The live recorder (default, no mode flag) and the replay/preflight/status subcommands are scaffolded
here. In P0 only ``--validate-config`` is wired end-to-end; the rest parse cleanly and report which
later phase implements them, exiting 0 so CI/ops smoke checks stay green.
"""

from __future__ import annotations

import argparse
import os
import sys

from .config import ConfigError, load_config
from .utils import get_logger, parse_ist_hhmm, setup_logging

logger = get_logger(__name__)

# Exit codes: 0 = success/clean, 1 = validation failure (§7.3 rule 5), 2 = CLI usage error.
EXIT_OK = 0
EXIT_VALIDATION = 1
EXIT_USAGE = 2


def build_parser() -> argparse.ArgumentParser:
    """Assemble the full §8.2 argument surface. Kept in one place so every subcommand is discoverable
    even while most are stubbed."""
    p = argparse.ArgumentParser(
        prog="python -m market_depth_recorder",
        description="Market Depth Recorder — capture, replay, and operational dry-run subcommands.",
    )
    p.add_argument("--config", default="config.yaml",
                   help="Path to config.yaml (default: ./config.yaml).")

    # Operational dry-run subcommands (§8.2) — no live market required, each exits 0/1.
    p.add_argument("--validate-config", action="store_true",
                   help="Run all §7.3 validation checks, print a report, exit 0 (valid) / 1 (invalid).")
    p.add_argument("--preflight", action="store_true",
                   help="Run the §3.2.5 depth preflight and print actual depth per underlying (P1).")
    p.add_argument("--status", action="store_true",
                   help="Pretty-print the current health.json (§6.4) and exit (P6).")
    p.add_argument("--eod-report", dest="eod_report", action="store_true",
                   help="Run the EOD health & sanity checks on a day's captured data; write a dated "
                        "report and exit 0 (clean) / 1 (any FAIL) (P10-C).")
    p.add_argument("--date", default=None, metavar="YYYY-MM-DD",
                   help="Session date for --eod-report (default: today, IST).")

    # Replay / reprocess (§8) — build the fat Tier-2 DuckDB store from a raw log.
    p.add_argument("--replay", nargs="?", const=True, default=None, metavar="RAW_LOG",
                   help="Replay a raw .jsonl.gz into the DuckDB analytical store (P7).")
    p.add_argument("--catchup", action="store_true",
                   help="Rebuild every raw log lacking an up-to-date analytics store, oldest-first (P7).")
    p.add_argument("--output", default=None, metavar="DUCKDB",
                   help="Replay output path; only valid with --replay (§8.2).")
    p.add_argument("--verify", action="store_true",
                   help="Replay then diff against a reference build (§8.4) (P7).")
    p.add_argument("--verify-against-live", action="store_true",
                   help="Restrict --verify comparison to the recorder.live_metrics columns (§8.4) (P7).")

    # Replay filters (§8.2).
    p.add_argument("--underlying", default=None,
                   help="Restrict replay to a single underlying by name (§8.2).")
    p.add_argument("--from", dest="from_time", default=None, metavar="HH:MM",
                   help="Replay slice start, IST HH:MM (§8.2).")
    p.add_argument("--to", dest="to_time", default=None, metavar="HH:MM",
                   help="Replay slice end, IST HH:MM (§8.2).")
    return p


def _guard_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    """Arg-dependency guards (B2b). Usage errors exit 2 via ``parser.error``."""
    replay_active = args.replay is not None or args.catchup
    if args.output is not None and not replay_active:
        parser.error("--output is only valid together with --replay/--catchup")
    if (args.verify or args.verify_against_live) and not replay_active:
        parser.error("--verify/--verify-against-live are only valid with --replay/--catchup")
    if args.date is not None and not args.eod_report:
        parser.error("--date is only valid together with --eod-report")
    for flag, value in (("--from", args.from_time), ("--to", args.to_time)):
        if value is not None:
            try:
                parse_ist_hhmm(value)
            except ValueError as exc:
                parser.error(f"{flag}: {exc}")


def _cmd_validate_config(args: argparse.Namespace) -> int:
    """Load + validate the config; print an OK line (stdout) or the failure report (stderr)."""
    try:
        cfg = load_config(args.config)
    except ConfigError as exc:
        print(exc.report(), file=sys.stderr)
        return EXIT_VALIDATION
    print(f"CONFIG OK: {args.config}")
    print(f"  underlyings : {', '.join(u.name for u in cfg.underlyings)}")
    print(f"  transport   : {cfg.websocket['transport']}")
    print(f"  config_hash : {cfg.config_hash}")
    return EXIT_OK


def _cmd_preflight(args: argparse.Namespace) -> int:
    """§3.2.5 preflight (P3): resolve each underlying's weekly chain over REST, then run the **live**
    depth probe (subscribe one ``:50`` depth on the near-ATM probe strike and read the actual
    ``depth_levels``/``is_50_depth`` off the first raw packet, §9). REST resolution is a prerequisite
    (exit 1 on failure); the depth probe is best-effort — an unreachable WS/session degrades to
    ``actual_depth=<unreachable>`` and still exits 0 (plan decision 30)."""
    try:
        cfg = load_config(args.config)
    except ConfigError as exc:
        print(exc.report(), file=sys.stderr)
        return EXIT_VALIDATION
    setup_logging(str(cfg.recorder.get("log_level", "INFO")))

    # Imported here (not at module top) so --validate-config and --help never pay the import.
    from .instrument_manager import InstrumentManager, RestError

    manager = InstrumentManager(cfg)
    try:
        manager.resolve()
    except RestError as exc:
        print(f"PREFLIGHT FAILED: {exc}", file=sys.stderr)
        return EXIT_VALIDATION

    # Live depth probe — best-effort; any failure (incl. deferred SDK transport) degrades gracefully.
    from .websocket_client import run_depth_preflight

    try:
        probes = {p.name: p for p in run_depth_preflight(cfg, manager)}
    except Exception as exc:  # noqa: BLE001 — the probe never fails the preflight (decision 30)
        print(f"PREFLIGHT: depth probe unavailable ({exc})", file=sys.stderr)
        probes = {}

    print(f"PREFLIGHT OK: {args.config}")
    for row in manager.preflight_report():
        probe = probes.get(row["name"])
        if probe is None:
            actual = "<unreachable: no WS/session>"
        elif probe.actual_depth is not None:
            actual = str(probe.actual_depth)
        else:
            actual = f"<{probe.note}>"
        print(
            f"  {row['name']:<10} {row['option_exchange']:<4} expiry={row['expiry']} "
            f"step={row['strike_step']} strikes={row['n_strikes']} "
            f"requested_depth={row['requested_depth']} probe_strike={row['probe_strike']} "
            f"actual_depth={actual}"
        )
    return EXIT_OK


def _cmd_replay(args: argparse.Namespace) -> int:
    """Offline replay / reprocess (§8): rebuild the fat DuckDB analytical store from a raw log with the
    **full** metric catalog. Supports ``--catchup`` (self-heal every stale day), ``--output`` (side file),
    ``--verify`` (diff vs a prior build) / ``--verify-against-live`` (diff live_metrics vs the SQLite live
    store), and the ``--underlying`` / ``--from`` / ``--to`` filters."""
    try:
        cfg = load_config(args.config)
    except ConfigError as exc:
        print(exc.report(), file=sys.stderr)
        return EXIT_VALIDATION
    setup_logging(str(cfg.recorder.get("log_level", "INFO")))

    from .replay import (
        canonical_output, catchup, live_store_path, replay_file, replay_side_output, verify,
    )

    if args.catchup:
        n = catchup(cfg)
        print(f"CATCHUP OK: rebuilt {n} analytical store(s)")
        return EXIT_OK

    raw_path = args.replay if isinstance(args.replay, str) else None
    if raw_path is None:
        print("--replay requires a raw log path (or use --catchup)", file=sys.stderr)
        return EXIT_USAGE
    if not os.path.exists(raw_path):
        print(f"raw log not found: {raw_path}", file=sys.stderr)
        return EXIT_VALIDATION

    from_t = parse_ist_hhmm(args.from_time) if args.from_time else None
    to_t = parse_ist_hhmm(args.to_time) if args.to_time else None
    verify_mode = args.verify or args.verify_against_live
    # Ad-hoc/verify runs default to a .replay.duckdb side file so the canonical store is never clobbered.
    out = args.output or (replay_side_output(raw_path) if verify_mode else canonical_output(cfg, raw_path))

    try:
        stats = replay_file(cfg, raw_path, out, underlying=args.underlying, from_t=from_t, to_t=to_t)
    except Exception as exc:  # noqa: BLE001 — surface a clean failure (e.g. pre-enrichment HEADER)
        print(f"REPLAY FAILED: {exc}", file=sys.stderr)
        return EXIT_VALIDATION
    print(f"REPLAY OK: {raw_path} -> {out} "
          f"({stats.rows} rows, {stats.packets} packets, {stats.corrupt_lines} corrupt line(s))")

    if not verify_mode:
        return EXIT_OK

    if args.verify_against_live:
        reference, live_subset = live_store_path(cfg, raw_path), True
    else:
        reference, live_subset = canonical_output(cfg, raw_path), False
    if not os.path.exists(reference):
        print(f"VERIFY: reference not found: {reference}", file=sys.stderr)
        return EXIT_VALIDATION
    ok, report = verify(cfg, out, reference, live_subset=live_subset)
    for line in report:
        print(line, file=sys.stdout if ok else sys.stderr)
    return EXIT_OK if ok else EXIT_VALIDATION


def _cmd_status(args: argparse.Namespace) -> int:
    """Pretty-print the current ``health.json`` (§6.4). A missing file is not an error (the recorder is
    simply not running) → friendly message + exit 0 (plan decision 62)."""
    try:
        cfg = load_config(args.config)
    except ConfigError as exc:
        print(exc.report(), file=sys.stderr)
        return EXIT_VALIDATION
    from .main import read_status

    code, text = read_status(cfg.recorder["health_file_path"])
    print(text, file=sys.stderr if code != EXIT_OK else sys.stdout)
    return code


def _cmd_eod_report(args: argparse.Namespace) -> int:
    """Run the EOD health & sanity checks on a day's captured data, write a dated markdown+JSON report,
    and exit 0 (clean) / 1 (any FAIL) (P10-C)."""
    from datetime import date as _date

    try:
        cfg = load_config(args.config)
    except ConfigError as exc:
        print(exc.report(), file=sys.stderr)
        return EXIT_VALIDATION
    setup_logging(str(cfg.recorder.get("log_level", "INFO")))

    from .utils import now_ist
    if args.date:
        try:
            sess = _date.fromisoformat(args.date)
        except ValueError:
            print(f"--date: invalid date {args.date!r} (expected YYYY-MM-DD)", file=sys.stderr)
            return EXIT_USAGE
    else:
        sess = now_ist().date()

    from .eod_report import run_eod_report
    code, report = run_eod_report(cfg, sess)
    c = report["counts"]
    print(f"EOD REPORT [{report['overall']}] {sess.isoformat()} → {report.get('report_md')}")
    print(f"  PASS {c['PASS']} · WARN {c['WARN']} · FAIL {c['FAIL']} · SKIP {c['SKIP']}")
    return code


def _cmd_run(args: argparse.Namespace) -> int:
    """Default (no-mode) entry: the live recording daemon (§3.1). Loads config, resolves the chains, and
    hands control to :class:`~market_depth_recorder.main.RecorderOrchestrator`."""
    try:
        cfg = load_config(args.config)
    except ConfigError as exc:
        print(exc.report(), file=sys.stderr)
        return EXIT_VALIDATION
    setup_logging(str(cfg.recorder.get("log_level", "INFO")))

    from .instrument_manager import InstrumentManager
    from .main import RecorderOrchestrator

    orchestrator = RecorderOrchestrator(cfg, InstrumentManager(cfg))
    _install_sigterm_handler(orchestrator)
    try:
        return orchestrator.run()
    except KeyboardInterrupt:
        orchestrator.stop()
        return EXIT_OK


def _make_sigterm_handler(orchestrator):
    """Build the SIGTERM handler closure (factored out so it is unit-testable without delivering a real
    OS signal — the P8 test invokes it directly; real delivery is exercised in P9)."""

    def _handle(signum, frame):  # noqa: ARG001 — signal-handler signature
        logger.warning("SIGTERM received — initiating graceful teardown")
        orchestrator.stop()

    return _handle


def _install_sigterm_handler(orchestrator) -> bool:
    """Register SIGTERM → graceful teardown (P8, fork 3) for the **live daemon only**.

    Without it, an OS ``SIGTERM`` (systemd / ``docker stop``) hard-kills the ``daemon=True`` workers
    mid-write, skipping the raw EOF marker + FD close — a lossless-raw gap on managed shutdown. The
    handler calls ``orchestrator.stop()`` (idempotent → the existing drain/EOF/FD-close path). SIGINT
    already maps to ``KeyboardInterrupt`` above. Best-effort: needs the main thread + SIGTERM support;
    ``signal.signal`` raises ``ValueError`` off the main thread, which we swallow (returns ``False``)."""
    import signal

    sig = getattr(signal, "SIGTERM", None)
    if sig is None:
        return False
    try:
        signal.signal(sig, _make_sigterm_handler(orchestrator))
        return True
    except (ValueError, OSError, RuntimeError):
        logger.debug("could not install SIGTERM handler (non-main thread or unsupported)", exc_info=True)
        return False


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _guard_args(args, parser)

    if args.validate_config:
        return _cmd_validate_config(args)
    if args.preflight:
        return _cmd_preflight(args)
    if args.status:
        return _cmd_status(args)
    if args.eod_report:
        return _cmd_eod_report(args)
    if args.replay is not None or args.catchup:
        return _cmd_replay(args)

    # Default: the live recording daemon (P6).
    return _cmd_run(args)


if __name__ == "__main__":
    sys.exit(main())
