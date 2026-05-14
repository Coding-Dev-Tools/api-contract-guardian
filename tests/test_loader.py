"""Tests for the loader module."""

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from api_contract_guardian.loader import (
    SpecLoadError,
    get_operations,
    get_paths,
    get_schemas,
    load_spec,
    load_spec_from_string,
    validate_openapi_version,
)


# ── Fixtures ──

@pytest.fixture
def sample_spec():
    return {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {},
    }


@pytest.fixture
def yaml_spec_file(tmp_path):
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {"/users": {"get": {"responses": {"200": {"description": "OK"}}}}},
    }
    p = tmp_path / "spec.yaml"
    p.write_text(yaml.dump(spec), encoding="utf-8")
    return p


@pytest.fixture
def json_spec_file(tmp_path):
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {},
    }
    p = tmp_path / "spec.json"
    p.write_text(json.dumps(spec), encoding="utf-8")
    return p


# ── load_spec tests ──

class TestLoadSpec:
    def test_load_yaml_file(self, yaml_spec_file):
        spec = load_spec(yaml_spec_file)
        assert spec["openapi"] == "3.0.3"
        assert "/users" in spec["paths"]

    def test_load_json_file(self, json_spec_file):
        spec = load_spec(json_spec_file)
        assert spec["openapi"] == "3.0.3"

    def test_load_yml_extension(self, tmp_path):
        p = tmp_path / "spec.yml"
        p.write_text(yaml.dump({"openapi": "3.0.3", "info": {"title": "T", "version": "1.0.0"}, "paths": {}}), encoding="utf-8")
        spec = load_spec(p)
        assert spec["openapi"] == "3.0.3"

    def test_load_nonexistent_file_raises(self):
        with pytest.raises(SpecLoadError, match="not found"):
            load_spec("/nonexistent/path/spec.yaml")

    def test_load_invalid_yaml_raises(self, tmp_path):
        p = tmp_path / "bad.yaml"
        p.write_text(":\n  bad: yaml: [", encoding="utf-8")
        with pytest.raises(SpecLoadError, match="Invalid YAML"):
            load_spec(p)

    def test_load_invalid_json_raises(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("{invalid json", encoding="utf-8")
        with pytest.raises(SpecLoadError, match="Invalid JSON"):
            load_spec(p)

    def test_load_non_dict_spec_raises(self, tmp_path):
        p = tmp_path / "list.yaml"
        p.write_text(yaml.dump(["item1", "item2"]), encoding="utf-8")
        with pytest.raises(SpecLoadError, match="not a valid OpenAPI document"):
            load_spec(p)

    def test_load_string_path(self, yaml_spec_file):
        spec = load_spec(str(yaml_spec_file))
        assert spec["openapi"] == "3.0.3"

    def test_load_unknown_extension_tries_yaml_then_json(self, tmp_path):
        p = tmp_path / "spec.txt"
        spec_data = {"openapi": "3.0.3", "info": {"title": "T", "version": "1.0.0"}, "paths": {}}
        p.write_text(yaml.dump(spec_data), encoding="utf-8")
        spec = load_spec(p)
        assert spec["openapi"] == "3.0.3"


# ── load_spec_from_string tests ──

class TestLoadSpecFromString:
    def test_load_yaml_string(self):
        content = yaml.dump({"openapi": "3.0.3", "info": {"title": "T", "version": "1.0.0"}, "paths": {}})
        spec = load_spec_from_string(content, fmt="yaml")
        assert spec["openapi"] == "3.0.3"

    def test_load_json_string(self):
        content = json.dumps({"openapi": "3.0.3", "info": {"title": "T", "version": "1.0.0"}, "paths": {}})
        spec = load_spec_from_string(content, fmt="json")
        assert spec["openapi"] == "3.0.3"

    def test_load_invalid_yaml_string_raises(self):
        with pytest.raises(SpecLoadError, match="Invalid YAML"):
            load_spec_from_string(":\n  bad: yaml: [", fmt="yaml")

    def test_load_invalid_json_string_raises(self):
        with pytest.raises(SpecLoadError, match="Invalid JSON"):
            load_spec_from_string("{invalid", fmt="json")

    def test_load_non_dict_string_raises(self):
        with pytest.raises(SpecLoadError, match="not a valid OpenAPI document"):
            load_spec_from_string('["list", "not", "dict"]', fmt="json")


# ── validate_openapi_version tests ──

class TestValidateOpenapiVersion:
    def test_valid_3_0_spec(self, sample_spec):
        version = validate_openapi_version(sample_spec)
        assert version == "3.0.3"

    def test_valid_3_1_spec(self):
        version = validate_openapi_version({"openapi": "3.1.0"})
        assert version == "3.1.0"

    def test_swagger_2_raises(self):
        with pytest.raises(SpecLoadError, match="not supported"):
            validate_openapi_version({"swagger": "2.0"})

    def test_unknown_version_raises(self):
        with pytest.raises(SpecLoadError, match="Unrecognized"):
            validate_openapi_version({"openapi": "4.0.0"})

    def test_missing_version_raises(self):
        with pytest.raises(SpecLoadError, match="does not contain"):
            validate_openapi_version({"info": {"title": "T"}})


# ── Helper function tests ──

class TestGetPaths:
    def test_returns_paths(self):
        spec = {"paths": {"/users": {}, "/items": {}}}
        assert get_paths(spec) == {"/users": {}, "/items": {}}

    def test_empty_paths(self):
        assert get_paths({}) == {}

    def test_no_paths_key(self):
        assert get_paths({"info": {}}) == {}


class TestGetSchemas:
    def test_returns_schemas(self):
        spec = {"components": {"schemas": {"User": {"type": "object"}}}}
        assert "User" in get_schemas(spec)

    def test_no_components(self):
        assert get_schemas({}) == {}

    def test_no_schemas_in_components(self):
        assert get_schemas({"components": {}}) == {}


class TestGetOperations:
    def test_extracts_methods(self):
        path_item = {"get": {}, "post": {}, "put": {}}
        ops = get_operations(path_item)
        assert set(ops.keys()) == {"get", "post", "put"}

    def test_ignores_non_methods(self):
        path_item = {"get": {}, "parameters": [], "summary": "test"}
        ops = get_operations(path_item)
        assert "get" in ops
        assert "parameters" not in ops
        assert "summary" not in ops

    def test_all_methods(self):
        path_item = {"get": {}, "post": {}, "put": {}, "patch": {}, "delete": {}, "head": {}, "options": {}, "trace": {}}
        ops = get_operations(path_item)
        assert len(ops) == 8

    def test_empty_path_item(self):
        ops = get_operations({})
        assert ops == {}
