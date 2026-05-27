"""Shared test fixtures for api-contract-guardian.

Patches revenueholdings_license.require_license so CLI tests never
hit the free-tier rate limit paywall.
"""

from __future__ import annotations

import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def _mock_require_license():
    """Auto-patch _require_license for all in-process CLI tests.

    The license paywall (commit 81dbb02) calls sys.exit(1) when the
    daily free-tier limit is exceeded.  During testing we must bypass
    this so CliRunner never receives SystemExit(1) from the license
    check.  We patch at the *bound* name used by cli.py so the mock
    applies regardless of import order.
    """
    with patch("api_contract_guardian.cli._require_license"):
        yield
