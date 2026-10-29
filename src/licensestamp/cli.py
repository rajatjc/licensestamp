# SPDX-FileCopyrightText: 2026 Rajat Sharma
# SPDX-License-Identifier: MIT

"""The `licensestamp` command."""

from __future__ import annotations

import argparse
import codecs
import difflib
import sys
from datetime import date
from fnmatch import fnmatch
from pathlib import Path

from . import __version__, config, gitinfo
from .core import Settings, stamp_text
from .styles import style_for


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="licensestamp", description="Add or update SPDX license headers in source files."
    )
    parser.add_argument("paths", nargs="*", type=Path, metavar="PATH",
                        help="files or directories; directories use git's file list")
    parser.add_argument("--author", help='copyright holder, e.g. "Rajat Sharma"')
    parser.add_argument("--license", help="SPDX license identifier, e.g. MIT or Apache-2.0")
    parser.add_argument("--template", type=Path,
                        help="use this file's text as the header; it can use $author, $year and $license")
    parser.add_argument("--exclude", action="append", default=[], metavar="GLOB",
                        help="skip paths matching GLOB (repeatable)")
    parser.add_argument("--check", action="store_true", help="list files that need changes, without writing")
    parser.add_argument("--diff", action="store_true", help="print the changes as a diff, without writing")
    parser.add_argument("--no-git", action="store_true", help="ignore git history and date headers to this year")
    parser.add_argument("--year", type=int, help="treat YEAR as the current year")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def _collect(paths: list[Path], exclude: list[str]) -> list[Path]:
    found: dict[Path, Path] = {}
    for path in paths:
        for file in gitinfo.list_files(path) if path.is_dir() else [path]:
            if file.is_symlink() or not file.is_file():
                continue
            if any(fnmatch(file.as_posix(), glob) or fnmatch(file.name, glob) for glob in exclude):
                continue
            found.setdefault(file.resolve(), file)
    return list(found.values())


def _read(path: Path) -> tuple[str, bool] | None:
    """Return the file's text and whether it had a UTF-8 BOM, or None for binary and non-UTF-8 files."""
    data = path.read_bytes()
    if b"\0" in data:
        return None
    try:
        return data.decode("utf-8-sig"), data.startswith(codecs.BOM_UTF8)
    except UnicodeDecodeError:
        return None


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if not args.paths:
        parser.error("no files given; pass . to stamp the whole project")

    options, root = config.load(Path.cwd())
    author = args.author or options.get("author")
    license_id = args.license or options.get("license")
    if not author or not license_id:
        parser.error(f"--author and --license are required, on the command line or in {config.CONFIG_NAME}")
    template_path = args.template or (root / options["template"] if root and "template" in options else None)
    try:
        template = template_path.read_text(encoding="utf-8") if template_path else None
    except OSError as error:
        parser.error(f"can't read the template: {error}")
    settings = Settings(
        author=author,
        license=license_id,
        template=template,
        use_git=not args.no_git and options.get("git", True),
        year=args.year or date.today().year,
    )

    pending = 0
    for path in _collect(args.paths, [*options.get("exclude", []), *args.exclude]):
        read = _read(path)
        if read is None:
            continue
        text, bom = read
        style = style_for(path, text.split("\n", 1)[0])
        if style is None or not text.strip():
            continue
        new = stamp_text(text, style, settings, path)
        if new == text:
            continue
        pending += 1
        if args.check:
            print(f"{path}: license header missing or out of date")
        elif args.diff:
            sys.stdout.writelines(difflib.unified_diff(
                text.splitlines(keepends=True), new.splitlines(keepends=True),
                f"a/{path.as_posix()}", f"b/{path.as_posix()}",
            ))
        else:
            path.write_bytes((codecs.BOM_UTF8 if bom else b"") + new.encode("utf-8"))
            print(f"stamped {path}")

    if pending and (args.check or args.diff):
        print(f"{pending} file(s) need a license header update", file=sys.stderr)
    return 1 if pending else 0
