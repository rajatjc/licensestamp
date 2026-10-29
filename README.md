# licensestamp

Add and update license headers in your source files. By default it writes a short, standard [SPDX](https://spdx.dev/learn/handling-license-info/) header. The copyright years come from git history, and you can run it from the command line, as a pre-commit hook, or as a CI check.

```python
# SPDX-FileCopyrightText: 2023-2026 Rajat Sharma
# SPDX-License-Identifier: MIT

print("Hello World")
```

## Install

```bash
pipx install licensestamp     # or: pip install licensestamp
```

It needs Python 3.11 or newer and has no dependencies.

## Use

```bash
licensestamp --author "Rajat Sharma" --license MIT src/app.py   # one file
licensestamp --author "Rajat Sharma" --license MIT .            # the whole project, skipping what .gitignore ignores
licensestamp --check .                                          # CI: list files that need a header, change nothing
licensestamp --diff .                                           # show what would change
```

The exit code is `0` when every file is already up to date and `1` when files were changed (or would be, with `--check` or `--diff`). Usage errors exit with `2`.

## Configure

Set your details once in `.licensestamp.toml` at the root of the repo:

```toml
author = "Rajat Sharma"
license = "MIT"                # any SPDX identifier, e.g. "Apache-2.0" or "MIT OR Apache-2.0"
exclude = ["vendor/*", "*.min.js"]
# template = "HEADER.txt"      # write full license text instead of the SPDX lines (see below)
# git = false                  # don't read years from git
```

Or put the same keys under `[tool.licensestamp]` in `pyproject.toml`. Command-line options override the file.

## pre-commit

```yaml
repos:
  - repo: https://github.com/rajatjc/licensestamp
    rev: v1.0.0
    hooks:
      - id: licensestamp
```

With a `.licensestamp.toml` in place, no `args` are needed. To pass them inline, use `args: [--author, "Rajat Sharma", --license, MIT]`.

## How the years work

- **Start year:** the year of the file's first commit. If the existing header claims an earlier year, that year is kept.
- **End year:** the current year if the file's code has changed since the last commit. Otherwise it's the year of the last commit.
- **Header-only changes don't count.** Adding or fixing a header never moves the end year, so running `licensestamp .` on a clean repo is stable.
- **Outside git, or with `--no-git`:** every file you pass is dated to the current year.

## Full license text instead

Point `--template` (or `template` in the config) at a text file. The file can use `$author`, `$year` and `$license`:

```text
Copyright (c) $year $author

Permission is hereby granted, free of charge, to any person obtaining a copy ...
```

licensestamp adds an `SPDX-License-Identifier` line if the template doesn't have one. That line is how it finds its own header again on the next run.

## What it leaves alone

- Lines that must stay first: shebangs, Python encoding lines, `<?xml ...?>`, `<!DOCTYPE>` and `<?php`.
- Other copyright holders' `SPDX-FileCopyrightText` lines. It only updates the line with your name.
- Comments at the top of the file that aren't a license header. The header is added above them.
- Line endings (LF or CRLF), a UTF-8 BOM, and a missing final newline.
- Binary, empty and non-UTF-8 files, symlinks, and file types it doesn't recognise.

## Supported files

| Comment | Files |
|---|---|
| `#` | Python, shell, Ruby, Perl, R, YAML, TOML, Terraform/HCL, Nix, PowerShell, CMake, Elixir, Julia, Nim, Starlark, GraphQL, Dockerfile, Makefile, Justfile, Gemfile, … |
| `//` | C, C++, C#, F#, Objective-C, Java, Kotlin, Scala, Groovy/Gradle, Go, Rust, JavaScript, TypeScript, Swift, Dart, PHP, Protobuf, Zig, Solidity |
| `--` | SQL, Lua, Haskell, Elm, Ada |
| `;;` | Emacs Lisp, Common Lisp, Clojure, Scheme, Racket |
| `%` | TeX/LaTeX, Erlang |
| `/* */` | CSS, SCSS, Less |
| `<!-- -->` | HTML, XML, SVG, Vue, Svelte, XSLT |

Files without an extension are recognised from their shebang (`python`, `bash`, `sh`, `zsh`, `ruby`, `perl`, `node`, `deno`, `bun`, …).

## Prior art

[add-license-header](https://github.com/arkinmodi/add-license-header) and the FSFE's [REUSE tool](https://reuse.software/). licensestamp is a fresh implementation. It focuses on short SPDX headers, git-accurate years, and staying out of the way of headers and file details it doesn't own.

## License

MIT © Rajat Sharma
