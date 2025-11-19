# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""CI/CD tooling and pre-commit hooks for provide.io ecosystem.

This package provides:
- Reusable GitHub Actions for Python CI/CD workflows
- Pre-commit hooks for code quality enforcement
- Centralized configuration validation
- Standardized CI/CD patterns across provide.io projects
"""

from __future__ import annotations

from provide.foundation.utils.versioning import get_version

__version__ = get_version("provide-cicd", __file__)

__all__ = [
    "__version__",
]

# 🧰⚙️🔚
