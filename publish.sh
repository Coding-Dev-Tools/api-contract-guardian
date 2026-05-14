#!/usr/bin/env bash
set -euo pipefail

# Publish api-contract-guardian to PyPI
# Requires: PYPI_TOKEN (PyPI API token starting with pypi-)
# Usage: ./publish.sh [test|prod]

MODE="${1:-test}"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

cd "$PROJECT_DIR"

# Validate token
if [ -z "${PYPI_TOKEN:-}" ]; then
  echo "ERROR: PYPI_TOKEN environment variable is not set."
  echo "Create a token at https://pypi.org/manage/account/token/"
  exit 1
fi

# Build clean
echo "=== Building package ==="
rm -rf dist/ build/ *.egg-info
python -m build
echo ""

# Check the dist
echo "=== Running twine check ==="
python -m twine check dist/*
echo ""

# Run tests
echo "=== Running tests ==="
python -m pytest tests/ -q
echo ""

if [ "$MODE" = "test" ]; then
  echo "=== Publishing to TestPyPI ==="
  TWINE_USERNAME="__token__" TWINE_PASSWORD="$PYPI_TOKEN" \
    TWINE_REPOSITORY_URL="https://test.pypi.org/legacy/" \
    python -m twine upload dist/*
  echo ""
  echo "Verify: pip install --index-url https://test.pypi.org/simple/ api-contract-guardian"
else
  echo "=== Publishing to PyPI ==="
  TWINE_USERNAME="__token__" TWINE_PASSWORD="$PYPI_TOKEN" \
    python -m twine upload dist/*
  echo ""
  echo "Verify: pip install api-contract-guardian"
fi
