# SPDX-FileCopyrightText: 2026 Rajat Sharma
# SPDX-License-Identifier: MIT

"""Find, build and replace the license header in a file's text."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from string import Template

from . import gitinfo
from .styles import Style

LICENSE_TAG = "SPDX-License-Identifier:"
COPYRIGHT_TAG = "SPDX-FileCopyrightText:"

_CODING = re.compile(r"^[ \t\f]*#.*?coding[:=]")
_YEAR = re.compile(r"\b(?:19|20)\d\d\b")


@dataclass
class Settings:
    author: str
    license: str
    template: str | None = None
    use_git: bool = True
    year: int = field(default_factory=lambda: date.today().year)


@dataclass
class _Parts:
    newline: str
    trailing_newline: bool
    preamble: list[str]
    header: list[str] | None  # text of the existing license header, comment syntax removed
    body: list[str]


def stamp_text(text: str, style: Style, settings: Settings, path: Path) -> str:
    """Return `text` with its license header added or brought up to date."""
    parts = _split(text, style)
    start, end = _years(parts, text, style, settings, path)
    years = str(start) if start == end else f"{start}-{end}"
    if settings.template is not None:
        lines = template_header(settings.template, settings.author, settings.license, years)
    else:
        lines = spdx_header(parts.header, settings.author, settings.license, years)
    out = [*parts.preamble, *style.render(lines)]
    if parts.body:
        out += ["", *parts.body]
    ending = parts.newline if parts.trailing_newline or not parts.body else ""
    return parts.newline.join(out) + ending


def spdx_header(existing: list[str] | None, author: str, license: str, years: str) -> list[str]:
    """Our SPDX lines, keeping any other holders' SPDX lines from the existing header."""
    kept = [
        t
        for t in (line.strip() for line in existing or [])
        if t.startswith("SPDX-")
        and not t.startswith(LICENSE_TAG)
        and not (t.startswith(COPYRIGHT_TAG) and author in t)
    ]
    others_copyright = [t for t in kept if t.startswith(COPYRIGHT_TAG)]
    other_tags = [t for t in kept if not t.startswith(COPYRIGHT_TAG)]
    ours = f"{COPYRIGHT_TAG} {years} {author}"
    return [*others_copyright, ours, *other_tags, f"{LICENSE_TAG} {license}"]


def template_header(template: str, author: str, license: str, years: str) -> list[str]:
    """Fill in a template; an SPDX identifier is added if the template has none, so the header can be found again."""
    text = Template(template).safe_substitute(author=author, license=license, year=years)
    lines = [line.rstrip() for line in text.strip("\n").split("\n")]
    if not any(LICENSE_TAG in line for line in lines):
        lines += ["", f"{LICENSE_TAG} {license}"]
    return lines


def claimed_years(header: list[str], author: str) -> tuple[int, int] | None:
    """The earliest and latest year on the author's lines of an existing header."""
    years = [int(y) for line in header if author in line for y in _YEAR.findall(line)]
    return (min(years), max(years)) if years else None


def _years(parts: _Parts, text: str, style: Style, settings: Settings, path: Path) -> tuple[int, int]:
    now = settings.year
    claimed = claimed_years(parts.header, settings.author) if parts.header else None
    history = gitinfo.commit_years(path) if settings.use_git else None
    if history is None:
        # Without history, a file we were asked to stamp counts as edited now.
        return (min(claimed[0], now) if claimed else now), now
    first, last = history
    committed = gitinfo.committed_text(path)
    # Only a change outside the header moves the end year; adding or fixing the header doesn't.
    edited = committed is None or _content(committed, style) != _content(text, style)
    if claimed:
        start = min(first, claimed[0])
        return start, (max(claimed[1], now) if edited else claimed[1])
    return first, (now if edited else last)


def _content(text: str, style: Style) -> list[str]:
    parts = _split(text, style)
    return [*parts.preamble, *parts.body]


def _split(text: str, style: Style) -> _Parts:
    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(newline)
    trailing_newline = lines[-1] == ""
    if trailing_newline:
        lines.pop()
    top = _preamble_end(lines, style)
    start = _skip_blank(lines, top)
    end = style.block_end(lines, start)
    header = None
    if end is not None and any(LICENSE_TAG in line for line in lines[start:end]):
        header = style.strip(lines[start:end])
        start = _skip_blank(lines, end)
    return _Parts(newline, trailing_newline, lines[:top], header, lines[start:])


def _preamble_end(lines: list[str], style: Style) -> int:
    """Count the lines that must stay above the header: shebang, encoding, XML/doctype, `<?php`."""
    i = 1 if lines and lines[0].startswith("#!") else 0
    while i < len(lines):
        line = lines[i].strip().lower()
        encoding = style.line == "#" and i <= 1 and _CODING.match(lines[i])
        if not (encoding or line.startswith(("<?xml", "<!doctype")) or line == "<?php"):
            break
        i += 1
    return i


def _skip_blank(lines: list[str], i: int) -> int:
    while i < len(lines) and not lines[i].strip():
        i += 1
    return i
