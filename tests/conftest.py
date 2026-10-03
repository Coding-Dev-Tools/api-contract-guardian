"""Mock revenueholdings_license for tests so CLI commands don't hit the paywall."""

import sys
from unittest.mock import MagicMock

# Replace the module before any import resolves it
_mock = MagicMock()
_mock.require_license = MagicMock(return_value=None)
sys.modules["revenueholdings_license"] = _mock

# Also mock the rate_limiter submodule
_rate_limiter_mock = MagicMock()
sys.modules["revenueholdings_license.rate_limiter"] = _rate_limiter_mock
