# SPDX-FileCopyrightText: 2026 Rajat Sharma
# SPDX-License-Identifier: MIT

"""Settings from .licensestamp.toml, or from [tool.licensestamp] in pyproject.toml."""

from __future__ import annotations

import tomllib
from pathlib import Path

CONFIG_NAME = ".licensestamp.toml"


def load(start: Path) -> tuple[dict, Path | None]:
    """Return the nearest config and the directory it's in, looking no higher than the repo root."""
    start = start.resolve()
    for directory in [start, *start.parents]:
        own = directory / CONFIG_NAME
        if own.is_file():
            return tomllib.loads(own.read_text(encoding="utf-8")), directory
        pyproject = directory / "pyproject.toml"
        if pyproject.is_file():
            section = tomllib.loads(pyproject.read_text(encoding="utf-8")).get("tool", {}).get("licensestamp")
            if section is not None:
                return section, directory
        if (directory / ".git").exists():
            break
    return {}, None
