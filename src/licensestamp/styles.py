# SPDX-FileCopyrightText: 2026 Rajat Sharma
# SPDX-License-Identifier: MIT

"""Comment syntax for each family of languages, and how to choose one for a file."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Style:
    """A way of writing a comment block: either line comments or one block comment."""

    line: str | None = None
    open: str = ""
    middle: str = ""
    close: str = ""

    def render(self, text: list[str]) -> list[str]:
        """Turn plain text lines into comment lines."""
        if self.line is not None:
            return [f"{self.line} {t}".rstrip() for t in text]
        return [self.open, *((self.middle + t).rstrip() for t in text), self.close]

    def block_end(self, lines: list[str], start: int) -> int | None:
        """Return the index just past the comment block that starts at `start`, if one does."""
        if start >= len(lines):
            return None
        if self.line is not None:
            end = start
            while end < len(lines) and lines[end].lstrip().startswith(self.line):
                end += 1
            return end if end > start else None
        first = lines[start].lstrip()
        if not first.startswith(self.open):
            return None
        closer = self.close.strip()
        if closer in first[len(self.open) :]:
            return start + 1
        for i in range(start + 1, len(lines)):
            if closer in lines[i]:
                return i + 1
        return None

    def strip(self, block: list[str]) -> list[str]:
        """Return the text inside a comment block, without the comment syntax."""
        if self.line is not None:
            text = [raw.lstrip()[len(self.line) :] for raw in block]
            return [t[1:] if t.startswith(" ") else t for t in text]
        closer, marker = self.close.strip(), self.middle.strip()
        text = []
        last = len(block) - 1
        for i, raw in enumerate(block):
            t = raw.strip()
            if i == 0:
                t = t.removeprefix(self.open)
            if i == last:
                t = t.removesuffix(closer)
            t = t.strip()
            if marker and t.startswith(marker):
                t = t[len(marker) :].strip()
            # Drop the bare opener and closer lines, keep blank lines in between.
            if t or 0 < i < last:
                text.append(t)
        return text


HASH = Style(line="#")
SLASH = Style(line="//")
DASH = Style(line="--")
LISP = Style(line=";;")
PERCENT = Style(line="%")
C_BLOCK = Style(open="/*", middle=" * ", close=" */")
HTML = Style(open="<!--", middle="  ", close="-->")


def _each(style: Style, *suffixes: str) -> dict[str, Style]:
    return dict.fromkeys(suffixes, style)


_BY_SUFFIX = {
    **_each(HASH, "py", "pyi", "pyw", "sh", "bash", "zsh", "fish", "rb", "pl", "pm", "r", "yaml", "yml",
            "toml", "tf", "tfvars", "hcl", "nix", "ps1", "psm1", "cmake", "ex", "exs", "jl", "cr", "nim",
            "bzl", "mk", "dockerfile", "graphql", "gql"),
    **_each(SLASH, "c", "h", "cc", "cpp", "cxx", "hh", "hpp", "hxx", "m", "mm", "cs", "fs", "java", "kt",
            "kts", "scala", "sc", "groovy", "gradle", "go", "rs", "js", "jsx", "mjs", "cjs", "ts", "tsx",
            "mts", "cts", "swift", "dart", "php", "proto", "zig", "sol"),
    **_each(DASH, "sql", "lua", "hs", "elm", "adb", "ads"),
    **_each(LISP, "el", "lisp", "cl", "clj", "cljs", "cljc", "edn", "scm", "rkt"),
    **_each(PERCENT, "tex", "sty", "cls", "erl", "hrl"),
    **_each(C_BLOCK, "css", "scss", "less"),
    **_each(HTML, "html", "htm", "xhtml", "xml", "svg", "vue", "svelte", "xsl", "xslt"),
}

_BY_NAME = _each(HASH, "Dockerfile", "Containerfile", "Makefile", "GNUmakefile", "makefile", "CMakeLists.txt",
                 "Justfile", "justfile", "Rakefile", "Gemfile", "Brewfile", "Vagrantfile", "BUILD",
                 "BUILD.bazel", "WORKSPACE")

_BY_INTERPRETER = {
    **_each(HASH, "python", "sh", "bash", "zsh", "fish", "ksh", "dash", "ruby", "perl", "rscript"),
    **_each(SLASH, "node", "deno", "bun", "tsx", "ts-node"),
}


def _interpreter(first_line: str) -> str | None:
    """Name the interpreter in a shebang: `#!/usr/bin/env python3.12` -> `python`."""
    if not first_line.startswith("#!"):
        return None
    parts = first_line[2:].split()
    if not parts:
        return None
    name = Path(parts[0]).name
    if name == "env":
        name = next((p for p in parts[1:] if not p.startswith("-")), "")
    match = re.match(r"[A-Za-z-]+", name)
    return match.group(0).lower() if match else None


def style_for(path: Path, first_line: str) -> Style | None:
    """Pick the comment style for a file, or None if the file type isn't supported."""
    if path.name in _BY_NAME or path.name.startswith(("Dockerfile.", "Containerfile.")):
        return HASH
    if path.suffix:
        return _BY_SUFFIX.get(path.suffix.lower().lstrip("."))
    return _BY_INTERPRETER.get(_interpreter(first_line) or "")
