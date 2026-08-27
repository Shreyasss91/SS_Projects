"""Framework config-validation entrypoint (Plan_002 §17 fail-fast contract).

Deliberately separate from the recorder's ``__main__.py``: F1 must not change recorder behaviour, and
an operator validating a framework block should not have to run the recorder's own validator to do it.
Run from the parent ``SS_Projects/``::

    python -m market_depth_recorder.market_depth_framework --config market_depth_recorder/config.yaml

Exit codes match the recorder's convention -- 0 valid, 1 validation failure, 2 CLI usage error -- so
ops smoke checks treat both the same way.
"""

from __future__ import annotations

import argparse
import sys

from .config import FRAMEWORK_SECTION, FrameworkConfigError, load_framework_config

EXIT_OK = 0
EXIT_VALIDATION = 1
EXIT_USAGE = 2


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m market_depth_recorder.market_depth_framework",
        description="Validate the market_depth_framework configuration block.",
    )
    p.add_argument("--config", default="config.yaml",
                   help="Path to the config YAML (default: ./config.yaml).")
    p.add_argument("--validate-config", action="store_true",
                   help="Validate the framework block; exit 0 (valid) / 1 (invalid). Default action.")
    return p


def main(argv: list[str] | None = None) -> int:
    """Validate and report. Returns the process exit code rather than calling ``sys.exit``, so tests
    assert on it in-process as well as through a subprocess."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        cfg = load_framework_config(args.config)
    except FrameworkConfigError as exc:
        print(exc.report(), file=sys.stderr)
        return EXIT_VALIDATION

    if cfg is None:
        # Absent section is valid: the framework is off and the recorder runs its existing path.
        print(f"FRAMEWORK CONFIG: no '{FRAMEWORK_SECTION}' section in {args.config} (framework off)")
        return EXIT_OK

    print(f"FRAMEWORK CONFIG OK: {args.config}")
    print(f"  enabled      : {cfg.enabled}")
    print(f"  broker       : {cfg.broker}")
    print(f"  brokers      : {', '.join(sorted(cfg.broker_capabilities))}")
    print(f"  policy       : {cfg.priority_policy['policy']} / {cfg.budget_allocator['policy']}")
    print(f"  rebalance    : {cfg.rebalance['trigger']} @ {cfg.rebalance['interval_seconds']}s")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
