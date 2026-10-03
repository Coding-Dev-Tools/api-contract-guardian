"""Edge-case tests for api-contract-guardian uncovered code paths.

Covers:
- require_license absent (cli.py:19-20)
- __main__.py entry point (__main__.py:3-5)
- version command (cli.py:256)
"""

from __future__ import annotations

import subprocess
import sys

from typer.testing import CliRunner

from api_contract_guardian.cli import app

runner = CliRunner()


class TestLicenseAgnostic:
    """Tests that work regardless of license module availability."""

    def test_version_command_runs(self):
        """version command prints version string."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "v" in result.output

    def test_help_contains_version(self):
        """help output includes version command."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "version" in result.output


class TestMainModule:
    """Tests for __main__.py entry point."""

    def test_main_module_runs(self):
        """python -m api_contract_guardian --help works."""
        result = subprocess.run(
            [sys.executable, "-m", "api_contract_guardian", "--help"],
            capture_output=True,
            text=False,
        )
        assert result.returncode == 0
        assert b"Usage" in result.stdout

    def test_main_module_version(self):
        """python -m api_contract_guardian version works."""
        result = subprocess.run(
            [sys.executable, "-m", "api_contract_guardian", "version"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "v" in result.stdout


class TestDiffEdgeCases:
    """Edge cases for diff command."""

    def test_diff_invalid_input(self):
        """diff with non-existent file shows error."""
        result = runner.invoke(
            app, ["diff", "/nonexistent/old.yaml", "/nonexistent/new.yaml"]
        )
        assert result.exit_code != 0
        assert "Error" in result.output


class TestCheckEdgeCases:
    """Edge cases for check command."""

    def test_check_invalid_input(self):
        """check with non-existent file shows error."""
        result = runner.invoke(
            app, ["check", "/nonexistent/old.yaml", "/nonexistent/new.yaml"]
        )
        assert result.exit_code != 0
        assert "Error" in result.output


class TestMigrateEdgeCases:
    """Edge cases for migrate command."""

    def test_migrate_invalid_input(self):
        """migrate with non-existent file shows error."""
        result = runner.invoke(
            app, ["migrate", "/nonexistent/old.yaml", "/nonexistent/new.yaml"]
        )
        assert result.exit_code != 0
        assert "Error" in result.output
