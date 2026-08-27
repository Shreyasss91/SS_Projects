"""F1 tests for the package skeleton's inertness and scope boundaries (Plan_002 §22.1).

F1's whole promise is that the framework exists and changes nothing. These tests make that promise
checkable rather than reviewable: importing the package must start no thread, open no handle, and pull
in no recorder module, and none of the layers Plan_002 assigns to a later phase may have appeared
early.
"""

from __future__ import annotations

import ast
import subprocess
import sys
import threading
from pathlib import Path

import pytest

import market_depth_recorder.market_depth_framework as framework

PACKAGE_DIR = Path(framework.__file__).resolve().parent
SS_PROJECTS = Path(__file__).resolve().parents[2]

# The complete module set the package is built out to. F8's orchestrator.py is the last layer
# Plan_002 §22 assigns to this package, so the guard flipped from "these must not exist yet" to an
# exact closed set: an unplanned module now fails just as loudly as an early arrival used to.
PACKAGE_MODULES = (
    "__init__", "__main__", "broker_adapter", "budget_allocator", "capabilities",
    "capability_layer", "config", "depth_allocator", "models", "orchestrator",
    "priority_policy", "subscription_manager", "subscription_state", "window_manager",
)


def source_files() -> list[Path]:
    return sorted(PACKAGE_DIR.glob("*.py"))


def test_package_exports_exactly_the_current_phase_surface():
    """Exact equality, not a subset: an accidental export fails as loudly as a missing one. The set
    widens by one phase at a time -- F1 contracts, F2's capability layer, F3's Window Manager,
    F4's Priority Policy, F5's two allocators, F6's subscription layer, F7.5's Broker Adapter."""
    assert set(framework.__all__) == {
        # F1 -- contracts
        "UNLIMITED_BUDGET", "BrokerCapability", "PremiumTier", "StandardTier",
        "FRAMEWORK_SECTION", "FrameworkConfig", "FrameworkConfigError",
        "load_framework_config", "validate_framework_config",
        "DepthType", "Instrument", "__version__",
        # F2 -- Broker Capabilities layer
        "BrokerCapabilityLayer", "build_capability_layers", "capability_layer_for",
        "check_premium_floor_feasible", "eligible_underlyings",
        # F3 -- Window Manager and its seams
        "WindowManager", "WindowSpec", "WindowResult", "WindowStatus", "OptionSide",
        "SymbolCodec", "ExpiryCalendar", "TagSymbolCodec", "FixedExpiryCalendar",
        "window_specs_from_underlyings",
        # F4 -- Priority Policy (ranking only; budget and depth are F5)
        "DEFAULT_POLICY", "AtmDistancePolicy", "MarketContext", "PriorityPolicy",
        "PriorityScore", "market_context_from_window", "policy_for", "rank_candidates",
        "rank_scores",
        # F5 -- Budget Allocator (inter-underlying split) and Depth Allocator (premium overlay)
        "BUDGET_POLICIES", "DEFAULT_BUDGET_POLICY", "BudgetAllocator", "budget_allocator_for",
        "DepthAllocation", "DepthAllocationDiff", "DepthAllocator", "depth_allocator_for",
        "depth_allocators_for",
        # F6 -- Subscription layer (state + pure reconciliation; broker execution is F7.5)
        "ActionKind", "SubscriptionAction", "SubscriptionManager", "SubscriptionPlan",
        "SubscriptionState",
        # F7.5 -- Broker Adapter (wire rendering and dispatch, written from the F7B evidence)
        "UNASSIGNED", "BrokerAdapter", "DepthTransport", "DispatchResult", "LegState",
        "LegView", "TransportError", "WireDialect", "WireOp", "WireRequest", "instruments_of",
        # F8 -- Framework Orchestrator (the one PROCESSOR call site) and its trigger labels
        "DEFAULT_CODEC_RULE", "DEFAULT_EXPIRY_RULE", "TRIGGER_INITIAL", "TRIGGER_INTERVAL",
        "TRIGGER_WINDOW_CHANGE", "FrameworkOrchestrator", "RebalanceResult", "orchestrator_for",
    }
    for name in framework.__all__:
        assert hasattr(framework, name), f"__all__ advertises {name} but it is not importable"


def test_package_modules_are_exactly_the_planned_set():
    """Exact equality, not a subset. F8's orchestrator.py completed the package, so the durable form
    of the old "no later-phase module exists yet" guard is a closed set: a module that should not be
    here fails, and so does one that quietly went missing."""
    present = {p.stem for p in source_files()}
    assert present == set(PACKAGE_MODULES)


def test_package_imports_nothing_from_the_recorder():
    """One-way dependency: the framework must stay independently testable and broker-reusable."""
    for path in source_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                # Relative imports (level > 0) stay inside the framework package.
                module = node.module or ""
                if node.level == 0:
                    assert not module.startswith("market_depth_recorder"), (
                        f"{path.name} imports {module} from the recorder"
                    )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("market_depth_recorder"), (
                        f"{path.name} imports {alias.name} from the recorder"
                    )


def test_package_creates_no_thread_on_import():
    """Plan_002 F1: the four-thread architecture is preserved; the framework adds no thread."""
    before = threading.active_count()
    import importlib

    importlib.reload(framework)
    assert threading.active_count() == before


def test_importing_the_package_opens_no_handles_and_runs_no_io():
    """A subprocess import with a fresh interpreter: no socket, file, or DB handle is created, and
    nothing is printed. Run out-of-process so an already-imported module cannot mask a side effect."""
    code = (
        "import socket, sqlite3, threading, sys\n"
        "socket.socket = None\n"
        "sqlite3.connect = None\n"
        "before = threading.active_count()\n"
        "import market_depth_recorder.market_depth_framework as f\n"
        "assert threading.active_count() == before, 'framework started a thread'\n"
        "assert f.UNLIMITED_BUDGET > 0\n"
        "print('INERT')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(SS_PROJECTS), capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "INERT", f"import produced extra output: {result.stdout!r}"


def test_no_index_name_or_exchange_literal_in_framework_source():
    """Genericization contract: no index name, exchange code, or strike step as a literal in engine
    code. Docstrings may name FYERS/NIFTY when citing the frozen evidence; executable code may not."""
    banned = ("NIFTY", "SENSEX", "BANKNIFTY", "NFO", "BFO")
    # The adapter is the one module that renders a wire format, so it is scanned like every other.
    for path in source_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                # Docstrings are the first statement of a module/class/function; skip those by
                # checking whether this constant is used as an expression statement.
                continue
        # Strip docstrings, then scan the remaining source text.
        stripped = ast.unparse(_without_docstrings(tree))
        for token in banned:
            assert token not in stripped, f"{path.name} hardcodes {token!r} outside a docstring"


def _without_docstrings(tree: ast.AST) -> ast.AST:
    """Return the tree with every module/class/function docstring removed."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                node.body = body[1:] or [ast.Pass()]
    return tree


def test_the_recorder_framework_dependency_stays_one_way():
    """F8 lets the recorder call *into* the framework; the framework still never imports back.

    The one-way rule is what keeps the framework replayable and testable without the recorder, so it
    is asserted rather than reviewed. The recorder-side import is deliberately confined to the
    validation surface: config loading is the only place F8 lets ``config.py`` touch the framework.
    """
    import market_depth_recorder.config as recorder_config

    tree = ast.parse(Path(recorder_config.__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").endswith(
            "market_depth_framework"
        ):
            imported |= {alias.name for alias in node.names}
    assert imported <= {
        "FRAMEWORK_SECTION",
        "FrameworkConfig",
        "FrameworkConfigError",
        "validate_framework_config",
    }, f"config.py imports more of the framework than the validation surface: {sorted(imported)}"

    for path in source_files():
        source = path.read_text(encoding="utf-8")
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.ImportFrom) and node.level == 0:
                assert "market_depth_recorder" not in (node.module or ""), (
                    f"{path.name} imports the recorder; the dependency must stay one-way"
                )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("market_depth_recorder"), (
                        f"{path.name} imports the recorder; the dependency must stay one-way"
                    )


@pytest.mark.parametrize("module_name", ["models", "capabilities", "config"])
def test_each_f1_module_is_importable_standalone(module_name):
    import importlib

    module = importlib.import_module(f"market_depth_recorder.market_depth_framework.{module_name}")
    assert module.__doc__, f"{module_name}.py must carry a module docstring"
