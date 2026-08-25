#!/usr/bin/env python3
# Raw docstring: it is printed verbatim as --help/--usage, so backslashes
# in the text must survive rather than be read as escape sequences.
r"""
create_changes_patch.py

Creates a single patch file containing:

1. Staged changes
2. Unstaged tracked changes
3. Untracked files

The script automatically discovers the project root by walking upward from
its own location until it finds a directory containing:

    main.py

(main.py alone marks the root: it does NOT need to also contain '.git'.
The enclosing git checkout may live several levels above the Python
project — e.g. strategies/SS_Projects/.git wrapping
SS_Projects/market_depth_recorder/main.py. Git resolves the checkout on
its own from any subdirectory, so every git call runs with the project
root as its working directory.)

This allows the script to live anywhere inside the repository
(it currently lives at tools/git/create_changes_patch.py).

All examples below are written to be run from the REPOSITORY ROOT.

----------------------------------------------------------------------
USAGE
----------------------------------------------------------------------

Basic:

    python tools/git/create_changes_patch.py

Specify output file:

    python tools/git/create_changes_patch.py -o review.patch

(Examples are written on one line so they paste straight into
PowerShell, where '\' is NOT a line-continuation character.)

Ignore specific files:

    python tools/git/create_changes_patch.py --ignore documentation/TODO.md --ignore notes.txt

Ignore directories:

    python tools/git/create_changes_patch.py --ignore documentation/generated --ignore logs

Ignore using glob patterns:

    python tools/git/create_changes_patch.py --ignore "*.log" --ignore "*.tmp"

Multiple ignore patterns are allowed:

    python tools/git/create_changes_patch.py --ignore documentation/generated --ignore "*.csv" --ignore "*.png"

Ignore patterns apply to ALL THREE sections (staged, unstaged and
untracked). Paths are matched relative to the REPOSITORY ROOT, and a
literal path is ANCHORED there — it is not matched at arbitrary depth:

    logs                -> the top-level logs/ only.
                           src/logs/ is NOT affected.
    logs/               -> same, trailing slash is ignored
    src/logs            -> the nested one; spell it out explicitly
    documentation/gen   -> anchored at the repository root

A glob, by contrast, is matched against the whole relative path, and
'*' spans '/', so a glob does reach any depth:

    "*.csv"             -> every .csv anywhere in the tree
    "*__pycache__*"     -> every __pycache__ dir at any depth
                           (a bare `--ignore __pycache__` would only
                           match one at the repository root)

__pycache__, *.pyc and *.patch are ignored at any depth by default —
you do not need to pass them. Override with --no-default-ignores.

For renames and copies, an entry is dropped only when EVERY path it
touches is ignored. A rename that crosses the ignore boundary
(logs/x.csv -> src/x.csv under `--ignore logs`) is kept, because the
un-ignored side is a real change worth seeing.

Patch files (*.patch) are ignored by default so a leftover patch from a
previous run is not embedded into the next one. Override with
--no-default-ignores.

Show detected repository:

    python tools/git/create_changes_patch.py --verbose

Help (both print this entire text):

    python tools/git/create_changes_patch.py --help
    python tools/git/create_changes_patch.py --usage

----------------------------------------------------------------------
WHAT GETS INCLUDED
----------------------------------------------------------------------

✓ Staged changes
✓ Unstaged tracked changes
✓ Untracked files

----------------------------------------------------------------------
WHAT DOES NOT GET INCLUDED
----------------------------------------------------------------------

✗ Ignored files (.gitignore)
✗ Files/directories matching --ignore
✗ *.patch, __pycache__/ and *.pyc at any depth
  (unless --no-default-ignores)
✗ Deleted files that no longer exist (handled by git diff normally)

----------------------------------------------------------------------
OUTPUT FORMAT
----------------------------------------------------------------------

============================================================
STAGED CHANGES
============================================================

<git patch>

============================================================
UNSTAGED TRACKED CHANGES
============================================================

<git patch>

============================================================
UNTRACKED FILES
============================================================

### FILE: path/to/file

<git patch>

### FILE: another/file

<git patch>

----------------------------------------------------------------------
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import subprocess
import sys
from pathlib import Path

# Always-on ignores. Written as globs on purpose: '*' spans '/', so
# these reach ANY depth, unlike a literal --ignore path which stays
# anchored at the repository root.
#
#   *.patch        This script's own output format. A leftover
#                  changes.patch from a previous run is untracked, so it
#                  would be swallowed whole into the next run —
#                  embedding a stale patch (including the very logs/
#                  noise that was filtered out) inside the new one.
#                  Excluding just the current output file is not enough,
#                  because -o/--output moves that target around.
#
#   __pycache__    Python bytecode is never review material. A repo
#   *.pyc          .gitignore usually hides these already, but that only
#                  covers UNtracked files: bytecode that was force-added
#                  or committed before the ignore rule existed is still
#                  diffed every run. Owning the rule here keeps the
#                  script self-sufficient in any repository.
DEFAULT_IGNORE_PATTERNS = ["*.patch", "*__pycache__*", "*.pyc"]


# ---------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------

def eprint(*args):
    print(*args, file=sys.stderr)


def run_git(repo: Path, args):
    result = subprocess.run(
        ["git"] + args,
        cwd=repo,
        capture_output=True,
        text=True,
        # Pin the decode: text=True would otherwise use the system locale
        # (cp1252 on a stock Windows box) while we write the patch as
        # UTF-8, silently turning every em-dash into mojibake. errors=
        # "replace" keeps a stray undecodable byte from aborting the run.
        encoding="utf-8",
        errors="replace",
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())

    return result.stdout


# ---------------------------------------------------------------------
# Repository discovery
# ---------------------------------------------------------------------

def discover_repo(start: Path) -> Path:
    """
    Walk upward until we find:

        main.py
    """

    current = start.resolve()

    while True:
        main_py = current / "main.py"

        if main_py.exists():
            return current

        if current.parent == current:
            raise RuntimeError(
                "Could not locate project root.\n"
                "Expected a directory containing 'main.py'."
            )

        current = current.parent


# ---------------------------------------------------------------------
# Ignore handling
# ---------------------------------------------------------------------

def should_ignore(relpath: str, ignore_patterns):
    relpath = relpath.replace("\\", "/")

    for pattern in ignore_patterns:

        pattern = pattern.replace("\\", "/")

        if fnmatch.fnmatch(relpath, pattern):
            return True

        if relpath == pattern:
            return True

        if relpath.startswith(pattern.rstrip("/") + "/"):
            return True

    return False


# ---------------------------------------------------------------------
# Patch helpers
# ---------------------------------------------------------------------

def parse_name_status(raw):
    """
    Parse `git diff --name-status -z` into a list of path-groups.

    The -z stream is a flat sequence of NUL-terminated fields:

        <status>\0<path>\0                     for A/M/D/T/U
        <status>\0<src>\0<dst>\0               for R### / C###

    Renames and copies are the reason this exists: they are the only
    entries that carry TWO paths, and `--name-only` collapses them to the
    destination alone, which makes the source path invisible to the
    --ignore filter.

    Returns a list of lists, one inner list per changed entry, holding
    every path that entry touches.
    """

    fields = [x for x in raw.split("\0") if x]

    groups = []
    i = 0

    while i < len(fields):

        status = fields[i]
        i += 1

        # R100 / C75 style statuses consume a source AND a destination.
        takes_two = status[:1] in ("R", "C")
        want = 2 if takes_two else 1

        paths = fields[i:i + want]
        i += want

        if paths:
            groups.append(paths)

    return groups


def batch_groups(groups, budget=20000, max_paths=400):
    """
    Split path-groups into batches small enough to survive the OS
    command-line limit.

    Windows CreateProcess caps the whole command line at 32767
    characters; a repo with ~1200 changed files produces ~94000
    characters of pathspec and dies with
    `[WinError 206] The filename or extension is too long`. The budget
    is deliberately well under the cap to leave room for the git
    executable, base_args and per-argument quoting overhead.

    Batching is by GROUP, never by individual path, so both halves of a
    rename always land in the same git invocation — split them and git
    stops seeing the pair as a rename and reports an unrelated
    delete + add instead.
    """

    batches = []
    current = []
    size = 0

    for paths in groups:

        cost = sum(len(p) + 3 for p in paths)   # +3 ≈ quotes + separator

        if current and (size + cost > budget or len(current) >= max_paths):
            batches.append(current)
            current = []
            size = 0

        current.extend(paths)
        size += cost

    if current:
        batches.append(current)

    return batches


def diff_filtered(repo: Path, base_args, ignore_patterns, output_relpath):
    """
    Run a `git diff` variant restricted to the paths that survive the
    --ignore filter.

    We resolve the affected paths first (`--name-status -z`, so paths with
    spaces or non-ASCII characters survive intact) and only then ask git
    for the patch of the surviving paths. Filtering the path list rather
    than the patch text keeps one single ignore semantic across staged,
    unstaged and untracked sections.

    Rename/copy rule: an entry is dropped only when EVERY path it touches
    is ignored. A rename that crosses the ignore boundary (say
    logs/x.csv -> src/x.csv under `--ignore logs`) is therefore kept,
    because the un-ignored side is a real change the reader must see.
    Dropping on "any side matches" would hide the arrival of src/x.csv
    entirely, and silently losing a change is worse than one extra hunk.
    """

    raw = run_git(repo, ["diff"] + base_args + ["--name-status", "-z"])

    kept = []

    for paths in parse_name_status(raw):

        visible = [
            p for p in paths
            if p.replace("\\", "/") != output_relpath
            and not should_ignore(p, ignore_patterns)
        ]

        if not visible:
            continue

        # Feed BOTH sides of a surviving rename back to git: restricting
        # the pathspec to the destination alone makes git re-report the
        # rename as an unrelated add.
        kept.append(paths)

    # Without this guard a trailing bare `--` would make git fall back to
    # "all paths", i.e. silently undo the filtering we just did.
    if not kept:
        return ""

    # Concatenating per-batch patches is safe: every batch emits its own
    # self-contained `diff --git` stanzas.
    chunks = [
        run_git(repo, ["diff"] + base_args + ["--"] + batch)
        for batch in batch_groups(kept)
    ]

    return "".join(chunks)


def write_header(f, title):
    f.write("\n")
    f.write("=" * 72 + "\n")
    f.write(title + "\n")
    f.write("=" * 72 + "\n\n")


def write_text_if_any(f, text):
    if text.strip():
        f.write(text.rstrip())
        f.write("\n\n")
    else:
        f.write("(none)\n\n")


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():

    # The module docstring IS the manual, so hand it to argparse rather
    # than maintaining a second, thinner description that would drift.
    # RawDescription keeps its hand-drawn rules and indented examples
    # intact — the default formatter reflows them into soup.
    parser = argparse.ArgumentParser(
        prog=Path(__file__).name,
        description=__doc__ or "",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-o",
        "--output",
        default="changes.patch",
        help="Output patch file (default: changes.patch)"
    )

    parser.add_argument(
        "--ignore",
        action="append",
        default=[],
        metavar="PATTERN",
        help=(
            "Ignore file/directory/glob pattern. "
            "Can be specified multiple times."
        )
    )

    parser.add_argument(
        "--no-default-ignores",
        action="store_true",
        help=(
            "Do not apply the built-in ignore patterns "
            f"({', '.join(DEFAULT_IGNORE_PATTERNS)}). Use this if you "
            "genuinely need patch files included in the output."
        )
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print the resolved repository, output path and active ignore patterns."
    )

    # Same built-in action as -h/--help, so the two can never diverge.
    parser.add_argument(
        "--usage",
        action="help",
        help="Show this full usage text and exit (alias for --help)."
    )

    args = parser.parse_args()

    if not args.no_default_ignores:
        args.ignore = list(args.ignore) + DEFAULT_IGNORE_PATTERNS

    script_dir = Path(__file__).parent
    repo = discover_repo(script_dir)

    if args.verbose:
        print(f"Repository : {repo}")
        print(f"Output     : {args.output}")

        if args.ignore:
            print("Ignore patterns:")
            for p in args.ignore:
                print(f"  - {p}")

        print()

    out_path = repo / args.output

    # Remove any existing patch file so we always start fresh.
    # (missing_ok=True requires Python 3.8+)
    out_path.unlink(missing_ok=True)

    # Repository-relative path of the output patch. This allows us to
    # automatically exclude the generated patch from including itself,
    # even when a custom output path is supplied via -o/--output.
    output_relpath = out_path.relative_to(repo).as_posix()

    with out_path.open("w", encoding="utf-8", newline="\n") as f:

        # ----------------------------------------------------------
        # STAGED
        # ----------------------------------------------------------

        write_header(f, "STAGED CHANGES")

        staged = diff_filtered(repo, ["--cached"], args.ignore, output_relpath)
        write_text_if_any(f, staged)

        # ----------------------------------------------------------
        # UNSTAGED
        # ----------------------------------------------------------

        write_header(f, "UNSTAGED TRACKED CHANGES")

        unstaged = diff_filtered(repo, [], args.ignore, output_relpath)
        write_text_if_any(f, unstaged)

        # ----------------------------------------------------------
        # UNTRACKED
        # ----------------------------------------------------------

        write_header(f, "UNTRACKED FILES")

        untracked = run_git(
            repo,
            ["ls-files", "--others", "--exclude-standard"]
        )

        files = []

        for line in untracked.splitlines():

            line = line.strip()

            if not line:
                continue

            # Never include the output patch itself.
            if line.replace("\\", "/") == output_relpath:
                continue

            if should_ignore(line, args.ignore):
                continue

            files.append(line)


        if not files:
            f.write("(none)\n")

        for file in sorted(files):

            f.write(f"\n### FILE: {file}\n\n")

            patch = subprocess.run(
                [
                    "git",
                    "diff",
                    "--no-index",
                    "--",
                    os.devnull,
                    file,
                ],
                cwd=repo,
                capture_output=True,
                text=True,
                encoding="utf-8",   # see run_git()
                errors="replace",
            )

            # git diff --no-index returns:
            #   0 = no diff
            #   1 = diff found
            # so don't treat 1 as an error.

            f.write(patch.stdout.rstrip())
            f.write("\n\n")

    print(f"Patch written to:\n{out_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        eprint(f"\nERROR: {ex}")
        sys.exit(1)
