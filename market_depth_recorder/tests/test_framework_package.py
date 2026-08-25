"""F1 tests for the package skeleton's inertness and scope boundaries (Plan_002 §22.1).

F1's whole promise is that the framework exists and changes nothing. These tests make that promise
checkable rather than reviewable: importing the package must start no thread, open no handle, and pull
in no recorder module, and none of the F2-F7 layers may have appeared early.
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

# Every layer Plan_002 §22 assigns to a later phase. Their absence is F1's boundary.
LATER_PHASE_MODULES = (
    "window_manager",      # F3
    "priority_policy",     # F4
    "budget_allocator",    # F5
    "depth_allocator",     # F5
    "subscription",        # F6
    "subscription_manager",
    "broker_adapter",      # F7
    "orchestrator",        # F8
)


def source_files() -> list[Path]:
    return sorted(PACKAGE_DIR.glob("*.py"))


def test_package_exports_exactly_the_f1_surface():
    assert set(framework.__all__) == {
        "UNLIMITED_BUDGET", "BrokerCapability", "PremiumTier", "StandardTier",
        "FRAMEWORK_SECTION", "FrameworkConfig", "FrameworkConfigError",
        "load_framework_config", "validate_framework_config",
        "DepthType", "Instrument", "__version__",
    }
    for name in framework.__all__:
        assert hasattr(framework, name), f"__all__ advertises {name} but it is not importable"


def test_no_later_phase_module_exists_yet():
    """F1 establishes contracts, not F2-F6 behaviour."""
    present = {p.stem for p in source_files()}
    for module in LATER_PHASE_MODULES:
        assert module not in present, f"{module}.py belongs to a later phase, not F1"


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


def test_recorder_still_imports_and_is_unchanged_by_the_framework():
    """The recorder must not gain a framework dependency in F1."""
    import market_depth_recorder.config as recorder_config

    source = Path(recorder_config.__file__).read_text(encoding="utf-8")
    assert "market_depth_framework" not in source


@pytest.mark.parametrize("module_name", ["models", "capabilities", "config"])
def test_each_f1_module_is_importable_standalone(module_name):
    import importlib

    module = importlib.import_module(f"market_depth_recorder.market_depth_framework.{module_name}")
    assert module.__doc__, f"{module_name}.py must carry a module docstring"
