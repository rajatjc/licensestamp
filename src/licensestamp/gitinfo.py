# SPDX-FileCopyrightText: 2026 Rajat Sharma
# SPDX-License-Identifier: MIT

"""What git knows about a file: when it was committed, and what it looked like at HEAD."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

_SKIP_DIRS = {
    ".git", ".hg", ".svn", ".venv", ".tox", ".nox", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    "node_modules", "venv", "__pycache__", "build", "dist", "target",
}


def _git(cwd: Path, *args: str) -> bytes | None:
    try:
        result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, check=False)
    except OSError:
        return None
    return result.stdout if result.returncode == 0 else None


def commit_years(path: Path) -> tuple[int, int] | None:
    """The years of the file's first and latest commits, or None if it has never been committed."""
    path = path.resolve()
    log = _git(path.parent, "log", "--follow", "--format=%ad", "--date=format:%Y", "--", path.name)
    years = [int(y) for y in (log or b"").split()]
    return (min(years), max(years)) if years else None


def committed_text(path: Path) -> str | None:
    """The file's contents at HEAD."""
    path = path.resolve()
    data = _git(path.parent, "show", f"HEAD:./{path.name}")
    return None if data is None else data.decode("utf-8-sig", errors="replace")


def list_files(directory: Path) -> list[Path]:
    """Files under `directory`: git's list (which honours .gitignore), or a plain walk outside a repo."""
    listed = _git(directory, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    if listed is not None:
        return [directory / name for name in listed.decode().split("\0") if name]
    files = []
    for root, dirs, names in os.walk(directory):
        dirs[:] = sorted(d for d in dirs if d not in _SKIP_DIRS and not d.endswith(".egg-info"))
        files += [Path(root) / name for name in sorted(names)]
    return files
