# SPDX-FileCopyrightText: 2026 Rajat Sharma
# SPDX-License-Identifier: MIT

from pathlib import Path

import pytest

from licensestamp.core import Settings, stamp_text
from licensestamp.styles import C_BLOCK, HASH, HTML, SLASH, style_for

SETTINGS = Settings(author="Rajat Sharma", license="MIT", use_git=False, year=2026)
HEADER = "# SPDX-FileCopyrightText: 2026 Rajat Sharma\n# SPDX-License-Identifier: MIT\n"


def stamp(text, style=HASH, settings=SETTINGS):
    return stamp_text(text, style, settings, Path("example"))


def test_adds_a_header_above_the_code():
    assert stamp("print('hi')\n") == HEADER + "\nprint('hi')\n"


def test_running_twice_changes_nothing():
    once = stamp("print('hi')\n")
    assert stamp(once) == once


def test_shebang_and_encoding_stay_on_top():
    src = "#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\nprint('hi')\n"
    assert stamp(src) == "#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n" + HEADER + "\nprint('hi')\n"


def test_extends_the_years_of_an_existing_header():
    src = "# SPDX-FileCopyrightText: 2023 Rajat Sharma\n# SPDX-License-Identifier: MIT\n\nx = 1\n"
    assert stamp(src).startswith("# SPDX-FileCopyrightText: 2023-2026 Rajat Sharma\n")


def test_keeps_other_copyright_holders_and_updates_the_license():
    src = (
        "# SPDX-FileCopyrightText: 2021 Someone Else\n"
        "# SPDX-FileCopyrightText: 2024 Rajat Sharma\n"
        "# SPDX-License-Identifier: Apache-2.0\n"
        "\n"
        "x = 1\n"
    )
    assert stamp(src) == (
        "# SPDX-FileCopyrightText: 2021 Someone Else\n"
        "# SPDX-FileCopyrightText: 2024-2026 Rajat Sharma\n"
        "# SPDX-License-Identifier: MIT\n"
        "\n"
        "x = 1\n"
    )


def test_adds_our_line_to_someone_elses_header():
    src = "# SPDX-FileCopyrightText: 2020 Someone Else\n# SPDX-License-Identifier: MIT\n\nx = 1\n"
    assert stamp(src) == (
        "# SPDX-FileCopyrightText: 2020 Someone Else\n"
        "# SPDX-FileCopyrightText: 2026 Rajat Sharma\n"
        "# SPDX-License-Identifier: MIT\n"
        "\n"
        "x = 1\n"
    )


def test_leaves_an_unrelated_leading_comment_alone():
    src = "# Helpers for parsing dates.\nimport datetime\n"
    assert stamp(src) == HEADER + "\n# Helpers for parsing dates.\nimport datetime\n"


def test_line_comment_languages():
    assert stamp("package main\n", SLASH) == (
        "// SPDX-FileCopyrightText: 2026 Rajat Sharma\n// SPDX-License-Identifier: MIT\n\npackage main\n"
    )


def test_block_comments():
    expected = "/*\n * SPDX-FileCopyrightText: 2026 Rajat Sharma\n * SPDX-License-Identifier: MIT\n */\n\nbody {}\n"
    assert stamp("body {}\n", C_BLOCK) == expected
    assert stamp(expected, C_BLOCK) == expected


def test_html_header_goes_below_the_doctype():
    out = stamp("<!DOCTYPE html>\n<html></html>\n", HTML)
    assert out == (
        "<!DOCTYPE html>\n"
        "<!--\n"
        "  SPDX-FileCopyrightText: 2026 Rajat Sharma\n"
        "  SPDX-License-Identifier: MIT\n"
        "-->\n"
        "\n"
        "<html></html>\n"
    )
    assert stamp(out, HTML) == out


def test_php_open_tag_stays_first():
    assert stamp("<?php\necho 1;\n", SLASH).startswith("<?php\n// SPDX-FileCopyrightText")


def test_template_header():
    settings = Settings("Rajat Sharma", "MIT", template="Copyright (c) $year $author\n\nAll rights reserved.\n",
                        use_git=False, year=2026)
    out = stamp("x = 1\n", settings=settings)
    assert out == (
        "# Copyright (c) 2026 Rajat Sharma\n"
        "#\n"
        "# All rights reserved.\n"
        "#\n"
        "# SPDX-License-Identifier: MIT\n"
        "\n"
        "x = 1\n"
    )
    assert stamp(out, settings=settings) == out

    next_year = Settings("Rajat Sharma", "MIT", template=settings.template, use_git=False, year=2027)
    assert stamp(out, settings=next_year).startswith("# Copyright (c) 2026-2027 Rajat Sharma\n")


def test_switching_from_a_template_back_to_spdx_drops_the_prose():
    src = "# Copyright (c) 2024 Rajat Sharma\n#\n# Some license text.\n#\n# SPDX-License-Identifier: MIT\n\nx = 1\n"
    assert stamp(src) == (
        "# SPDX-FileCopyrightText: 2024-2026 Rajat Sharma\n# SPDX-License-Identifier: MIT\n\nx = 1\n"
    )


def test_keeps_crlf_line_endings():
    assert stamp("x = 1\r\ny = 2\r\n") == HEADER.replace("\n", "\r\n") + "\r\nx = 1\r\ny = 2\r\n"


def test_keeps_a_missing_final_newline():
    assert stamp("x = 1") == HEADER + "\nx = 1"


@pytest.mark.parametrize(
    "name, first_line, style",
    [
        ("app.py", "", HASH),
        ("Dockerfile", "", HASH),
        ("Dockerfile.dev", "", HASH),
        ("CMakeLists.txt", "", HASH),
        ("main.go", "", SLASH),
        ("App.tsx", "", SLASH),
        ("site.css", "", C_BLOCK),
        ("index.html", "", HTML),
        ("deploy", "#!/usr/bin/env bash", HASH),
        ("manage", "#!/usr/bin/python3.12", HASH),
        ("serve", "#!/usr/bin/env -S node --no-warnings", SLASH),
        ("data.json", "", None),
        ("notes", "plain text", None),
    ],
)
def test_style_for(name, first_line, style):
    assert style_for(Path(name), first_line) == style
