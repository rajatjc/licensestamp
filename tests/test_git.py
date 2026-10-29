# SPDX-FileCopyrightText: 2026 Rajat Sharma
# SPDX-License-Identifier: MIT

import os
import shutil
import subprocess

import pytest

from licensestamp.cli import main
from licensestamp.gitinfo import commit_years

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="needs git")

ARGS = ["--author", "Rajat Sharma", "--license", "MIT", "--year", "2026"]


def git(repo, *args, when=None):
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.com",
    }
    if when:
        env |= {"GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when}
    subprocess.run(
        ["git", "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", *args],
        cwd=repo, env=env, check=True, capture_output=True,
    )


@pytest.fixture
def repo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    git(tmp_path, "init", "-q")
    (tmp_path / "app.py").write_text("x = 1\n")
    git(tmp_path, "add", "app.py")
    git(tmp_path, "commit", "-qm", "first", when="2023-05-01T12:00:00")
    (tmp_path / "app.py").write_text("x = 2\n")
    git(tmp_path, "commit", "-qam", "second", when="2025-03-01T12:00:00")
    return tmp_path


def first_line(path):
    return path.read_text().split("\n", 1)[0]


def test_years_come_from_the_history(repo):
    assert commit_years(repo / "app.py") == (2023, 2025)
    assert commit_years(repo / "untracked.py") is None


def test_an_unchanged_file_is_dated_by_its_commits(repo):
    assert main(["app.py", *ARGS]) == 1
    assert first_line(repo / "app.py") == "# SPDX-FileCopyrightText: 2023-2025 Rajat Sharma"
    # Adding the header is itself a change to the file, but it must not bump the year.
    assert main(["app.py", *ARGS]) == 0


def test_editing_the_code_extends_the_years_to_now(repo):
    main(["app.py", *ARGS])
    git(repo, "commit", "-qam", "add header", when="2026-01-02T12:00:00")
    assert main(["app.py", *ARGS]) == 0

    (repo / "app.py").write_text((repo / "app.py").read_text() + "y = 3\n")
    assert main(["app.py", *ARGS]) == 1
    assert first_line(repo / "app.py") == "# SPDX-FileCopyrightText: 2023-2026 Rajat Sharma"


def test_a_new_file_is_dated_this_year(repo):
    (repo / "new.py").write_text("z = 1\n")
    main(["new.py", *ARGS])
    assert first_line(repo / "new.py") == "# SPDX-FileCopyrightText: 2026 Rajat Sharma"


def test_directories_honour_gitignore(repo):
    (repo / ".gitignore").write_text("generated.py\n")
    (repo / "generated.py").write_text("g = 1\n")
    main([".", *ARGS])
    assert (repo / "generated.py").read_text() == "g = 1\n"
