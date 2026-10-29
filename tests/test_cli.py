# SPDX-FileCopyrightText: 2026 Rajat Sharma
# SPDX-License-Identifier: MIT

import codecs

import pytest

from licensestamp.cli import main

ARGS = ["--author", "Rajat Sharma", "--license", "MIT", "--no-git", "--year", "2026"]


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "app.py").write_text("x = 1\n")
    (tmp_path / "web").mkdir()
    (tmp_path / "web" / "main.js").write_text("export {}\n")
    (tmp_path / "data.json").write_text("{}\n")
    return tmp_path


def test_stamps_a_directory_then_has_nothing_left_to_do(project, capsys):
    assert main([".", *ARGS]) == 1
    assert (project / "app.py").read_text().startswith("# SPDX-FileCopyrightText: 2026 Rajat Sharma\n")
    assert (project / "web" / "main.js").read_text().startswith("// SPDX-FileCopyrightText: 2026 Rajat Sharma\n")
    assert (project / "data.json").read_text() == "{}\n"
    assert "stamped app.py" in capsys.readouterr().out

    assert main([".", *ARGS]) == 0


def test_check_reports_without_writing(project, capsys):
    assert main(["app.py", "--check", *ARGS]) == 1
    assert (project / "app.py").read_text() == "x = 1\n"
    assert "app.py: license header missing" in capsys.readouterr().out


def test_diff_prints_the_change_without_writing(project, capsys):
    assert main(["app.py", "--diff", *ARGS]) == 1
    assert (project / "app.py").read_text() == "x = 1\n"
    assert "+# SPDX-License-Identifier: MIT" in capsys.readouterr().out


def test_reads_settings_from_the_config_file(project):
    (project / ".licensestamp.toml").write_text('author = "Rajat Sharma"\nlicense = "Apache-2.0"\nexclude = ["web/*"]\n')
    assert main([".", "--no-git", "--year", "2026"]) == 1
    assert "SPDX-License-Identifier: Apache-2.0" in (project / "app.py").read_text()
    assert (project / "web" / "main.js").read_text() == "export {}\n"


def test_reads_settings_from_pyproject(project):
    (project / "pyproject.toml").write_text('[tool.licensestamp]\nauthor = "Rajat Sharma"\nlicense = "MIT"\n')
    assert main(["app.py", "--no-git", "--year", "2026"]) == 1


def test_template_from_the_config_file(project):
    (project / "HEADER.txt").write_text("Copyright $year $author. All rights reserved.\n")
    (project / ".licensestamp.toml").write_text('author = "Rajat Sharma"\nlicense = "MIT"\ntemplate = "HEADER.txt"\n')
    main(["app.py", "--no-git", "--year", "2026"])
    assert (project / "app.py").read_text().startswith("# Copyright 2026 Rajat Sharma. All rights reserved.\n")


def test_author_and_license_are_required(project):
    with pytest.raises(SystemExit) as exit_info:
        main(["app.py"])
    assert exit_info.value.code == 2


def test_walks_dot_directories_but_not_clutter(project):
    (project / ".github").mkdir()
    (project / ".github" / "ci.yml").write_text("on: push\n")
    (project / ".venv").mkdir()
    (project / ".venv" / "site.py").write_text("v = 1\n")
    main([".", *ARGS])
    assert (project / ".github" / "ci.yml").read_text().startswith("# SPDX-FileCopyrightText")
    assert (project / ".venv" / "site.py").read_text() == "v = 1\n"


def test_skips_binary_and_empty_files(project):
    (project / "blob.py").write_bytes(b"\x00\x01binary")
    (project / "__init__.py").write_text("")
    main([".", *ARGS])
    assert (project / "blob.py").read_bytes() == b"\x00\x01binary"
    assert (project / "__init__.py").read_text() == ""


def test_keeps_a_utf8_bom(project):
    (project / "bom.py").write_bytes(codecs.BOM_UTF8 + b"x = 1\n")
    main(["bom.py", *ARGS])
    data = (project / "bom.py").read_bytes()
    assert data.startswith(codecs.BOM_UTF8 + b"# SPDX-FileCopyrightText")
