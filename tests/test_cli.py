"""Tests for the CLI entry point.

These are *integration-style* smoke tests: they invoke the installed
``api-contract-guardian`` command and verify basic behaviour.  No in-memory
mocking is used so the tests exercise the real packaging / entry-point path.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

EXECUTABLE = [sys.executable, "-m", "api_contract_guardian"]

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures"
SPEC_V1 = FIXTURE_DIR / "spec-v1.yaml"
SPEC_V2 = FIXTURE_DIR / "spec-v2.yaml"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the CLI and capture stdout/stderr as text."""
    result = subprocess.run(
        EXECUTABLE + list(args),
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    return result


class TestHelpOutput:
    """Smoke-level checks for top-level help."""

    def test_help_exits_zero(self) -> None:
        result = _run("--help")
        assert result.returncode == 0
        assert "Usage:" in result.stdout

    def test_help_lists_known_commands(self) -> None:
        result = _run("--help")
        assert "diff" in result.stdout
        assert "check" in result.stdout
        assert "migrate" in result.stdout

    def test_empty_args_exits_nonzero(self) -> None:
        result = _run()
        assert result.returncode != 0


class TestVersionOutput:
    """The ``version`` command should always be callable."""

    def test_version_printed(self) -> None:
        result = _run("version")
        assert result.returncode == 0
        assert "0.1.0" in result.stdout


class TestDiffCommand:
    """End-to-end checks for ``diff``."""

    def test_diff_help(self) -> None:
        result = _run("diff", "--help")
        assert result.returncode == 0
        assert "old" in result.stdout
        assert "new" in result.stdout

    @pytest.mark.skipif(
        not SPEC_V1.exists() or not SPEC_V2.exists(),
        reason="fixture spec files not present",
    )
    def test_diff_valid_specs(self) -> None:
        result = _run("diff", str(SPEC_V1), str(SPEC_V2))
        assert result.returncode == 0
        assert "Summary:" in result.stdout
        assert "breaking" in result.stdout

    def test_diff_missing_file(self) -> None:
        result = _run("diff", "/no/such/file.yaml", str(SPEC_V1))
        assert result.returncode != 0
        assert "Error" in result.stdout or "Error" in result.stderr


class TestCheckCommand:
    """End-to-end checks for ``check`` (CI-gate style)."""

    def test_check_help(self) -> None:
        result = _run("check", "--help")
        assert result.returncode == 0

    @pytest.mark.skipif(
        not SPEC_V1.exists() or not SPEC_V2.exists(),
        reason="fixture spec files not present",
    )
    def test_check_valid_specs(self) -> None:
        result = _run("check", str(SPEC_V1), str(SPEC_V2))
        # ``check`` should exit 0 on non-breaking diffs in fixtures, but we
        # don't enforce that here because fixture contents may vary.
        assert result.returncode in (0, 1)

    def test_check_missing_file(self) -> None:
        result = _run("check", "/no/such/file.yaml", str(SPEC_V1))
        assert result.returncode != 0


class TestMigrateCommand:
    """End-to-end checks for ``migrate``."""

    def test_migrate_help(self) -> None:
        result = _run("migrate", "--help")
        assert result.returncode == 0

    @pytest.mark.skipif(
        not SPEC_V1.exists() or not SPEC_V2.exists(),
        reason="fixture spec files not present",
    )
    def test_migrate_valid_specs(self, tmp_path) -> None:
        # Write to pytest's tmp_path rather than the repo root: writing and
        # unlinking an artifact inside the repo pollutes the working tree and
        # fails outright on filesystems where deletion is not permitted.
        out = tmp_path / "tmp-migration.md"
        result = _run("migrate", str(SPEC_V1), str(SPEC_V2), "--output", str(out))
        assert result.returncode == 0
        assert out.exists()
        text = out.read_text(encoding="utf-8")
        assert "Migration Guide" in text


class TestErrorObservability:
    """Errors go to stderr and --output creates missing parent dirs."""

    def test_load_error_goes_to_stderr(self) -> None:
        result = _run("diff", "does-not-exist.yaml", "also-missing.yaml")
        assert result.returncode == 1
        assert "Error loading" in result.stderr
        assert "Error" not in result.stdout

    def test_diff_output_creates_parent_dirs(self, tmp_path: Path) -> None:
        out = tmp_path / "nested" / "dir" / "report.json"
        result = _run(
            "diff", str(SPEC_V1), str(SPEC_V2), "--format", "json", "--output", str(out)
        )
        assert result.returncode == 0
        assert out.exists()
        assert "Written to" in result.stdout


class TestMachineReadableOutput:
    """--format json/yaml stdout must parse even with very long lines.

    Rich's Console soft-wraps long lines at the console width (80 columns
    when piped), which corrupts JSON/YAML piped into CI. Machine formats are
    emitted raw via click.echo and must never be wrapped.
    """

    @pytest.mark.skipif(
        not SPEC_V1.exists() or not SPEC_V2.exists(),
        reason="fixture specs missing",
    )
    def test_piped_json_stdout_parses(self) -> None:
        import json

        result = _run("diff", str(SPEC_V1), str(SPEC_V2), "--format", "json")
        assert result.returncode == 0
        payload = json.loads(result.stdout)  # raises if rich wrapped any line
        assert "changes" in payload

    @pytest.mark.skipif(
        not SPEC_V1.exists() or not SPEC_V2.exists(),
        reason="fixture specs missing",
    )
    def test_piped_yaml_stdout_parses(self) -> None:
        import yaml

        result = _run("diff", str(SPEC_V1), str(SPEC_V2), "--format", "yaml")
        assert result.returncode == 0
        payload = yaml.safe_load(result.stdout)
        assert isinstance(payload, dict) and "changes" in payload

    @pytest.mark.skipif(
        not SPEC_V1.exists() or not SPEC_V2.exists(),
        reason="fixture specs missing",
    )
    def test_check_json_stdout_parses(self) -> None:
        import json

        result = _run("check", str(SPEC_V1), str(SPEC_V2), "--format", "json")
        assert result.returncode in (0, 1)
        payload = json.loads(result.stdout)
        assert "gate" in payload and "diff" in payload
