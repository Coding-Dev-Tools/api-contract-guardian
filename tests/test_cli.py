"""Tests for the CLI interface using Typer's CliRunner."""

from __future__ import annotations

import os
import tempfile
import yaml

from typer.testing import CliRunner

from api_contract_guardian.cli import app

runner = CliRunner()


# ── Helper ──


def _write_yaml(data: dict) -> str:
    """Write a YAML file and return its path."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
    yaml.dump(data, f)
    f.close()
    return f.name


# ── Fixtures ──


def _identical_specs():
    """Return two identical minimal specs."""
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {"responses": {"200": {"description": "List users"}}},
            },
        },
    }
    return _write_yaml(spec), _write_yaml(spec)


def _breaking_specs():
    """Return two specs where an endpoint is removed (breaking change)."""
    old = {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {"responses": {"200": {"description": "List users"}}},
            },
            "/users/{id}": {
                "delete": {"responses": {"204": {"description": "Deleted"}}},
            },
        },
    }
    new = {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {"responses": {"200": {"description": "List users"}}},
            },
        },
    }
    return _write_yaml(old), _write_yaml(new)


class TestVersionCommand:
    """Tests for the ``version`` subcommand."""

    def test_version_output(self):
        """version prints the package version string."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "api-contract-guardian v0.1.0" in result.output

    def test_version_exit_code(self):
        """version exits with code 0."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0


class TestDiffCommand:
    """Tests for the ``diff`` subcommand."""

    def test_diff_json_format(self):
        """diff --format json outputs valid JSON with no changes."""
        old_path, new_path = _identical_specs()
        try:
            result = runner.invoke(app, ["diff", old_path, new_path, "--format", "json"])
            assert result.exit_code == 0
            assert '"breaking": 0' in result.output
        finally:
            os.unlink(old_path)
            os.unlink(new_path)

    def test_diff_with_breaking_changes_json(self):
        """diff detects breaking changes."""
        old_path, new_path = _breaking_specs()
        try:
            result = runner.invoke(app, ["diff", old_path, new_path, "--format", "json"])
            assert result.exit_code == 0
            assert '"breaking": 1' in result.output or "path_removed" in result.output
        finally:
            os.unlink(old_path)
            os.unlink(new_path)

    def test_diff_rich_format(self):
        """diff default (rich) format prints a summary table."""
        old_path, new_path = _identical_specs()
        try:
            result = runner.invoke(app, ["diff", old_path, new_path])
            assert result.exit_code == 0
            assert "Change Summary" in result.output
            assert "Breaking" in result.output
            assert "0" in result.output
        finally:
            os.unlink(old_path)
            os.unlink(new_path)

    def test_diff_output_file(self):
        """diff --output writes JSON to a file."""
        old_path, new_path = _identical_specs()
        out_path = tempfile.mktemp(suffix=".json")
        try:
            result = runner.invoke(app, ["diff", old_path, new_path, "--output", out_path])
            assert result.exit_code == 0
            assert os.path.isfile(out_path)
            with open(out_path) as f:
                content = f.read()
            assert "summary" in content
        finally:
            os.unlink(old_path)
            os.unlink(new_path)
            if os.path.isfile(out_path):
                os.unlink(out_path)

    def test_diff_invalid_file(self):
        """diff exits with code 1 for a non-existent file."""
        result = runner.invoke(app, ["diff", "nonexistent.yaml", "also-missing.yaml"])
        assert result.exit_code == 1
        assert "Error loading" in result.output


class TestCheckCommand:
    """Tests for the ``check`` (CI gating) subcommand."""

    def test_check_with_no_changes(self):
        """check passes when there are no changes."""
        old_path, new_path = _identical_specs()
        try:
            result = runner.invoke(app, ["check", old_path, new_path])
            assert result.exit_code == 0
            assert "passed" in result.output.lower() or "✓" in result.output
        finally:
            os.unlink(old_path)
            os.unlink(new_path)

    def test_check_with_breaking_changes(self):
        """check fails (exit 1) when breaking changes are detected."""
        old_path, new_path = _breaking_specs()
        try:
            result = runner.invoke(app, ["check", old_path, new_path])
            assert result.exit_code == 1
            assert "breaking" in result.output.lower()
        finally:
            os.unlink(old_path)
            os.unlink(new_path)

    def test_check_allow_breaking(self):
        """check passes even with breaking changes when --allow-breaking is used."""
        old_path, new_path = _breaking_specs()
        try:
            result = runner.invoke(app, ["check", old_path, new_path, "--allow-breaking"])
            assert result.exit_code == 0
        finally:
            os.unlink(old_path)
            os.unlink(new_path)

    def test_check_max_breaking_zero_with_no_changes(self):
        """check passes with --max-breaking=0 when no changes."""
        old_path, new_path = _identical_specs()
        try:
            result = runner.invoke(app, ["check", old_path, new_path, "--max-breaking", "0"])
            assert result.exit_code == 0
        finally:
            os.unlink(old_path)
            os.unlink(new_path)

    def test_check_output_file(self):
        """check --output writes gate+diff JSON to a file."""
        old_path, new_path = _identical_specs()
        out_path = tempfile.mktemp(suffix=".json")
        try:
            result = runner.invoke(app, ["check", old_path, new_path, "--output", out_path])
            assert result.exit_code == 0
            assert os.path.isfile(out_path)
            with open(out_path) as f:
                content = f.read()
            assert "gate" in content
            assert "diff" in content
        finally:
            os.unlink(old_path)
            os.unlink(new_path)
            if os.path.isfile(out_path):
                os.unlink(out_path)


class TestMigrateCommand:
    """Tests for the ``migrate`` subcommand."""

    def test_migrate_default_format(self):
        """migrate produces a markdown migration guide by default."""
        old_path, new_path = _identical_specs()
        try:
            result = runner.invoke(app, ["migrate", old_path, new_path])
            assert result.exit_code == 0
            assert result.output.strip()  # non-empty output
        finally:
            os.unlink(old_path)
            os.unlink(new_path)

    def test_migrate_json_format(self):
        """migrate --format json outputs structured JSON."""
        old_path, new_path = _identical_specs()
        try:
            result = runner.invoke(app, ["migrate", old_path, new_path, "--format", "json"])
            assert result.exit_code == 0
            assert "summary" in result.output or "changes" in result.output
        finally:
            os.unlink(old_path)
            os.unlink(new_path)

    def test_migrate_output_file(self):
        """migrate --output writes content to a file."""
        old_path, new_path = _identical_specs()
        out_path = tempfile.mktemp(suffix=".md")
        try:
            result = runner.invoke(app, ["migrate", old_path, new_path, "--output", out_path])
            assert result.exit_code == 0
            assert os.path.isfile(out_path)
            with open(out_path) as f:
                content = f.read()
            assert len(content) > 0
        finally:
            os.unlink(old_path)
            os.unlink(new_path)
            if os.path.isfile(out_path):
                os.unlink(out_path)

    def test_migrate_invalid_input(self):
        """migrate exits with code 1 for invalid files."""
        result = runner.invoke(app, ["migrate", "no-such-file.yaml", "also-missing.yaml"])
        assert result.exit_code == 1


class TestHelp:
    """Tests for top-level ``--help``."""

    def test_help_contains_commands(self):
        """--help lists all expected subcommands."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        for cmd in ["diff", "check", "migrate", "mcp", "version"]:
            assert cmd in result.output

    def test_help_contains_description(self):
        """--help contains the tool description."""
        result = runner.invoke(app, ["--help"])
        assert "breaking changes" in result.output.lower()


class TestMCPCommand:
    """Tests for the ``mcp`` subcommand."""

    def test_mcp_command_exists(self):
        """mcp subcommand is listed in help."""
        result = runner.invoke(app, ["--help"])
        assert "mcp" in result.output
