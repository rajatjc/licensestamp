# SPDX-FileCopyrightText: 2026 Rajat Sharma
# SPDX-License-Identifier: MIT

"""Add and update SPDX license headers in source files."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("licensestamp")
except PackageNotFoundError:
    __version__ = "0.0.0"
