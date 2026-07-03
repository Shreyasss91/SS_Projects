"""Command-line entrypoint for the Market Depth Recorder (spec §8.2).

Run from the parent ``SS_Projects/``::

    python -m market_depth_recorder --validate-config --config market_depth_recorder/config.yaml

The live recorder (default, no mode flag) and the replay/preflight/status subcommands are scaffolded
here. In P0 only ``--validate-config`` is wired end-to-end; the rest parse cleanly and report which
later phase implements them, exiting 0 so CI/ops smoke checks stay green.
"""

from __future__ import annotations

import argparse
import sys

from .config import ConfigError, load_config
from .utils import parse_ist_hhmm, setup_logging

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
    """Offline §3.2.5 preflight (P1): resolve each underlying's weekly chain over REST and report the
    planned near-ATM probe strike + requested depth. The *live* depth-level probe (actual
    depth_levels/is_50_depth off a raw packet) lands in P3, so ``actual_depth`` prints as pending.
    Exit 0 on a clean resolution, 1 on any config/REST/resolution failure."""
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

    print(f"PREFLIGHT OK: {args.config}")
    for row in manager.preflight_report():
        print(
            f"  {row['name']:<10} {row['option_exchange']:<4} expiry={row['expiry']} "
            f"step={row['strike_step']} strikes={row['n_strikes']} "
            f"requested_depth={row['requested_depth']} probe_strike={row['probe_strike']} "
            f"actual_depth=<pending P3 raw-WS probe>"
        )
    return EXIT_OK


def _stub(name: str, phase: str) -> int:
    """Report a not-yet-implemented subcommand and exit cleanly (§B2a)."""
    print(f"{name}: not implemented until {phase}.")
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _guard_args(args, parser)

    if args.validate_config:
        return _cmd_validate_config(args)
    if args.preflight:
        return _cmd_preflight(args)
    if args.status:
        return _stub("--status", "P6 (orchestrator health file)")
    if args.replay is not None or args.catchup:
        return _stub("--replay/--catchup", "P7 (replay + DuckDB writer)")

    # Default: the live recording daemon (P6).
    return _stub("live recorder", "P6 (orchestrator)")


if __name__ == "__main__":
    sys.exit(main())
