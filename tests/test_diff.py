"""Tests for the diff engine."""

import pytest

from api_contract_guardian.diff import (
    Change,
    DiffResult,
    Severity,
    diff_specs,
)


# ── Minimal spec fixtures ──

def _make_spec(paths=None, schemas=None, security_schemes=None, security=None, servers=None, info=None, openapi="3.0.3"):
    spec = {
        "openapi": openapi,
        "info": info or {"title": "Test API", "version": "1.0.0"},
        "paths": paths or {},
    }
    if schemas:
        spec["components"] = {"schemas": schemas}
    if security_schemes:
        if "components" not in spec:
            spec["components"] = {}
        spec["components"]["securitySchemes"] = security_schemes
    if security is not None:
        spec["security"] = security
    if servers is not None:
        spec["servers"] = servers
    return spec


# ── Severity and Change tests ──

class TestSeverity:
    def test_values(self):
        assert Severity.BREAKING.value == "breaking"
        assert Severity.DANGEROUS.value == "dangerous"
        assert Severity.NON_BREAKING.value == "non_breaking"
        assert Severity.INFO.value == "info"


class TestChange:
    def test_to_dict(self):
        c = Change(kind="path_removed", severity=Severity.BREAKING, path="paths./users", description="Removed", old_value="/users")
        d = c.to_dict()
        assert d["kind"] == "path_removed"
        assert d["severity"] == "breaking"
        assert d["path"] == "paths./users"
        assert d["old_value"] == "/users"


class TestDiffResult:
    def test_empty_result(self):
        r = DiffResult()
        assert not r.has_breaking
        assert r.breaking_changes == []
        assert r.to_dict()["summary"]["breaking"] == 0

    def test_has_breaking(self):
        r = DiffResult(changes=[Change(kind="x", severity=Severity.BREAKING, path="", description="")])
        assert r.has_breaking

    def test_to_dict_summary(self):
        r = DiffResult(changes=[
            Change(kind="a", severity=Severity.BREAKING, path="", description=""),
            Change(kind="b", severity=Severity.NON_BREAKING, path="", description=""),
        ])
        s = r.to_dict()["summary"]
        assert s["breaking"] == 1
        assert s["non_breaking"] == 1


# ── Path diff tests ──

class TestPathDiff:
    def test_path_removed_breaking(self):
        old = _make_spec(paths={"/users": {}})
        new = _make_spec(paths={})
        result = diff_specs(old, new)
        assert any(c.kind == "path_removed" and c.severity == Severity.BREAKING for c in result.changes)

    def test_path_added_non_breaking(self):
        old = _make_spec(paths={})
        new = _make_spec(paths={"/users": {}})
        result = diff_specs(old, new)
        assert any(c.kind == "path_added" and c.severity == Severity.NON_BREAKING for c in result.changes)

    def test_no_path_changes(self):
        old = _make_spec(paths={"/users": {}})
        new = _make_spec(paths={"/users": {}})
        result = diff_specs(old, new)
        path_changes = [c for c in result.changes if c.kind.startswith("path_")]
        assert len(path_changes) == 0

    def test_multiple_paths_removed(self):
        old = _make_spec(paths={"/users": {}, "/items": {}, "/orders": {}})
        new = _make_spec(paths={"/items": {}})
        result = diff_specs(old, new)
        removed = [c for c in result.changes if c.kind == "path_removed"]
        assert len(removed) == 2


# ── Operation diff tests ──

class TestOperationDiff:
    def test_operation_removed_breaking(self):
        old = _make_spec(paths={"/users": {"get": {"responses": {"200": {"description": "OK"}}}}})
        new = _make_spec(paths={"/users": {}})
        result = diff_specs(old, new)
        assert any(c.kind == "operation_removed" for c in result.changes)

    def test_operation_added_non_breaking(self):
        old = _make_spec(paths={"/users": {}})
        new = _make_spec(paths={"/users": {"get": {"responses": {"200": {"description": "OK"}}}}})
        result = diff_specs(old, new)
        assert any(c.kind == "operation_added" for c in result.changes)

    def test_operation_deprecated_dangerous(self):
        old = _make_spec(paths={"/users": {"get": {"responses": {"200": {"description": "OK"}}}}})
        new = _make_spec(paths={"/users": {"get": {"deprecated": True, "responses": {"200": {"description": "OK"}}}}})
        result = diff_specs(old, new)
        assert any(c.kind == "operation_deprecated" and c.severity == Severity.DANGEROUS for c in result.changes)

    def test_multiple_methods_removed(self):
        old = _make_spec(paths={"/users": {"get": {"responses": {"200": {"description": "OK"}}}, "post": {"responses": {"201": {"description": "Created"}}}}})
        new = _make_spec(paths={"/users": {}})
        result = diff_specs(old, new)
        removed = [c for c in result.changes if c.kind == "operation_removed"]
        assert len(removed) == 2


# ── Parameter diff tests ──

class TestParameterDiff:
    def test_required_param_removed_breaking(self):
        old = _make_spec(paths={"/users": {"get": {"parameters": [{"name": "id", "in": "query", "required": True}], "responses": {"200": {"description": "OK"}}}}})
        new = _make_spec(paths={"/users": {"get": {"parameters": [], "responses": {"200": {"description": "OK"}}}}})
        result = diff_specs(old, new)
        assert any(c.kind == "parameter_removed" and c.severity == Severity.BREAKING for c in result.changes)

    def test_optional_param_removed_non_breaking(self):
        old = _make_spec(paths={"/users": {"get": {"parameters": [{"name": "page", "in": "query", "required": False}], "responses": {"200": {"description": "OK"}}}}})
        new = _make_spec(paths={"/users": {"get": {"parameters": [], "responses": {"200": {"description": "OK"}}}}})
        result = diff_specs(old, new)
        assert any(c.kind == "parameter_removed" and c.severity == Severity.NON_BREAKING for c in result.changes)

    def test_required_param_added_breaking(self):
        old = _make_spec(paths={"/users": {"get": {"parameters": [], "responses": {"200": {"description": "OK"}}}}})
        new = _make_spec(paths={"/users": {"get": {"parameters": [{"name": "id", "in": "query", "required": True}], "responses": {"200": {"description": "OK"}}}}})
        result = diff_specs(old, new)
        assert any(c.kind == "parameter_added" and c.severity == Severity.BREAKING for c in result.changes)

    def test_optional_param_added_non_breaking(self):
        old = _make_spec(paths={"/users": {"get": {"parameters": [], "responses": {"200": {"description": "OK"}}}}})
        new = _make_spec(paths={"/users": {"get": {"parameters": [{"name": "page", "in": "query", "required": False}], "responses": {"200": {"description": "OK"}}}}})
        result = diff_specs(old, new)
        assert any(c.kind == "parameter_added" and c.severity == Severity.NON_BREAKING for c in result.changes)

    def test_param_became_required_breaking(self):
        old = _make_spec(paths={"/users": {"get": {"parameters": [{"name": "id", "in": "query", "required": False}], "responses": {"200": {"description": "OK"}}}}})
        new = _make_spec(paths={"/users": {"get": {"parameters": [{"name": "id", "in": "query", "required": True}], "responses": {"200": {"description": "OK"}}}}})
        result = diff_specs(old, new)
        assert any(c.kind == "parameter_became_required" for c in result.changes)

    def test_param_type_changed_breaking(self):
        old = _make_spec(paths={"/users": {"get": {"parameters": [{"name": "id", "in": "query", "required": False, "schema": {"type": "string"}}], "responses": {"200": {"description": "OK"}}}}})
        new = _make_spec(paths={"/users": {"get": {"parameters": [{"name": "id", "in": "query", "required": False, "schema": {"type": "integer"}}], "responses": {"200": {"description": "OK"}}}}})
        result = diff_specs(old, new)
        assert any(c.kind == "parameter_type_changed" for c in result.changes)


# ── Request body diff tests ──

class TestRequestBodyDiff:
    def test_request_body_removed_breaking(self):
        old = _make_spec(paths={"/users": {"post": {"requestBody": {"content": {"application/json": {}}}, "responses": {"201": {"description": "Created"}}}}})
        new = _make_spec(paths={"/users": {"post": {"responses": {"201": {"description": "Created"}}}}})
        result = diff_specs(old, new)
        assert any(c.kind == "request_body_removed" for c in result.changes)

    def test_request_body_added_non_breaking(self):
        old = _make_spec(paths={"/users": {"post": {"responses": {"201": {"description": "Created"}}}}})
        new = _make_spec(paths={"/users": {"post": {"requestBody": {"content": {"application/json": {}}}, "responses": {"201": {"description": "Created"}}}}})
        result = diff_specs(old, new)
        assert any(c.kind == "request_body_added" for c in result.changes)

    def test_request_body_became_required_breaking(self):
        old = _make_spec(paths={"/users": {"post": {"requestBody": {"content": {"application/json": {}}}, "responses": {"201": {"description": "Created"}}}}})
        new = _make_spec(paths={"/users": {"post": {"requestBody": {"required": True, "content": {"application/json": {}}}, "responses": {"201": {"description": "Created"}}}}})
        result = diff_specs(old, new)
        assert any(c.kind == "request_body_became_required" for c in result.changes)

    def test_request_content_type_removed_breaking(self):
        old = _make_spec(paths={"/users": {"post": {"requestBody": {"content": {"application/json": {}, "application/xml": {}}}, "responses": {"201": {"description": "Created"}}}}})
        new = _make_spec(paths={"/users": {"post": {"requestBody": {"content": {"application/json": {}}}, "responses": {"201": {"description": "Created"}}}}})
        result = diff_specs(old, new)
        assert any(c.kind == "request_content_type_removed" for c in result.changes)

    def test_request_content_type_added_non_breaking(self):
        old = _make_spec(paths={"/users": {"post": {"requestBody": {"content": {"application/json": {}}}, "responses": {"201": {"description": "Created"}}}}})
        new = _make_spec(paths={"/users": {"post": {"requestBody": {"content": {"application/json": {}, "application/xml": {}}}, "responses": {"201": {"description": "Created"}}}}})
        result = diff_specs(old, new)
        assert any(c.kind == "request_content_type_added" for c in result.changes)


# ── Response diff tests ──

class TestResponseDiff:
    def test_response_removed_breaking(self):
        old = _make_spec(paths={"/users": {"get": {"responses": {"200": {"description": "OK"}, "404": {"description": "Not Found"}}}}})
        new = _make_spec(paths={"/users": {"get": {"responses": {"200": {"description": "OK"}}}}})
        result = diff_specs(old, new)
        assert any(c.kind == "response_removed" for c in result.changes)

    def test_response_added_non_breaking(self):
        old = _make_spec(paths={"/users": {"get": {"responses": {"200": {"description": "OK"}}}}})
        new = _make_spec(paths={"/users": {"get": {"responses": {"200": {"description": "OK"}, "404": {"description": "Not Found"}}}}})
        result = diff_specs(old, new)
        assert any(c.kind == "response_added" for c in result.changes)

    def test_response_content_type_removed_breaking(self):
        old = _make_spec(paths={"/users": {"get": {"responses": {"200": {"content": {"application/json": {}, "application/xml": {}}}}}}})
        new = _make_spec(paths={"/users": {"get": {"responses": {"200": {"content": {"application/json": {}}}}}}})
        result = diff_specs(old, new)
        assert any(c.kind == "response_content_type_removed" for c in result.changes)

    def test_response_content_type_added_non_breaking(self):
        old = _make_spec(paths={"/users": {"get": {"responses": {"200": {"content": {"application/json": {}}}}}}})
        new = _make_spec(paths={"/users": {"get": {"responses": {"200": {"content": {"application/json": {}, "application/xml": {}}}}}}})
        result = diff_specs(old, new)
        assert any(c.kind == "response_content_type_added" for c in result.changes)


# ── Schema diff tests ──

class TestSchemaDiff:
    def test_schema_removed_breaking(self):
        old = _make_spec(schemas={"User": {"type": "object"}})
        new = _make_spec(schemas={})
        result = diff_specs(old, new)
        assert any(c.kind == "schema_removed" for c in result.changes)

    def test_schema_added_non_breaking(self):
        old = _make_spec(schemas={})
        new = _make_spec(schemas={"User": {"type": "object"}})
        result = diff_specs(old, new)
        assert any(c.kind == "schema_added" for c in result.changes)

    def test_schema_type_changed_breaking(self):
        old = _make_spec(schemas={"User": {"type": "object"}})
        new = _make_spec(schemas={"User": {"type": "string"}})
        result = diff_specs(old, new)
        assert any(c.kind == "schema_type_changed" for c in result.changes)

    def test_property_became_required_breaking(self):
        old = _make_spec(schemas={"User": {"type": "object", "required": ["id"], "properties": {"id": {"type": "string"}, "name": {"type": "string"}}}})
        new = _make_spec(schemas={"User": {"type": "object", "required": ["id", "name"], "properties": {"id": {"type": "string"}, "name": {"type": "string"}}}})
        result = diff_specs(old, new)
        assert any(c.kind == "property_became_required" for c in result.changes)

    def test_property_no_longer_required_non_breaking(self):
        old = _make_spec(schemas={"User": {"type": "object", "required": ["id", "name"], "properties": {"id": {"type": "string"}, "name": {"type": "string"}}}})
        new = _make_spec(schemas={"User": {"type": "object", "required": ["id"], "properties": {"id": {"type": "string"}, "name": {"type": "string"}}}})
        result = diff_specs(old, new)
        assert any(c.kind == "property_no_longer_required" for c in result.changes)

    def test_property_removed_breaking_if_required(self):
        old = _make_spec(schemas={"User": {"type": "object", "required": ["id", "name"], "properties": {"id": {"type": "string"}, "name": {"type": "string"}}}})
        new = _make_spec(schemas={"User": {"type": "object", "required": ["id"], "properties": {"id": {"type": "string"}}}})
        result = diff_specs(old, new)
        prop_removed = [c for c in result.changes if c.kind == "property_removed"]
        assert len(prop_removed) == 1
        assert prop_removed[0].severity == Severity.BREAKING

    def test_property_removed_dangerous_if_optional(self):
        old = _make_spec(schemas={"User": {"type": "object", "required": ["id"], "properties": {"id": {"type": "string"}, "nickname": {"type": "string"}}}})
        new = _make_spec(schemas={"User": {"type": "object", "required": ["id"], "properties": {"id": {"type": "string"}}}})
        result = diff_specs(old, new)
        prop_removed = [c for c in result.changes if c.kind == "property_removed"]
        assert len(prop_removed) == 1
        assert prop_removed[0].severity == Severity.DANGEROUS

    def test_property_added_non_breaking(self):
        old = _make_spec(schemas={"User": {"type": "object", "properties": {"id": {"type": "string"}}}})
        new = _make_spec(schemas={"User": {"type": "object", "properties": {"id": {"type": "string"}, "email": {"type": "string"}}}})
        result = diff_specs(old, new)
        assert any(c.kind == "property_added" for c in result.changes)

    def test_property_type_changed_breaking(self):
        old = _make_spec(schemas={"User": {"type": "object", "properties": {"age": {"type": "string"}}}})
        new = _make_spec(schemas={"User": {"type": "object", "properties": {"age": {"type": "integer"}}}})
        result = diff_specs(old, new)
        assert any(c.kind == "property_type_changed" for c in result.changes)

    def test_property_format_changed_dangerous(self):
        old = _make_spec(schemas={"User": {"type": "object", "properties": {"created": {"type": "string", "format": "date"}}}})
        new = _make_spec(schemas={"User": {"type": "object", "properties": {"created": {"type": "string", "format": "date-time"}}}})
        result = diff_specs(old, new)
        assert any(c.kind == "property_format_changed" for c in result.changes)

    def test_enum_values_removed_breaking(self):
        old = _make_spec(schemas={"Status": {"type": "string", "enum": ["active", "inactive", "pending"]}})
        new = _make_spec(schemas={"Status": {"type": "string", "enum": ["active", "inactive"]}})
        result = diff_specs(old, new)
        assert any(c.kind == "enum_values_removed" for c in result.changes)

    def test_no_schema_changes(self):
        old = _make_spec(schemas={"User": {"type": "object", "properties": {"id": {"type": "string"}}}})
        new = _make_spec(schemas={"User": {"type": "object", "properties": {"id": {"type": "string"}}}})
        result = diff_specs(old, new)
        schema_changes = [c for c in result.changes if "schema" in c.kind or "property" in c.kind or "enum" in c.kind]
        assert len(schema_changes) == 0


# ── Security scheme diff tests ──

class TestSecuritySchemeDiff:
    def test_security_scheme_removed_breaking(self):
        old = _make_spec(security_schemes={"bearerAuth": {"type": "http", "scheme": "bearer"}})
        new = _make_spec(security_schemes={})
        result = diff_specs(old, new)
        assert any(c.kind == "security_scheme_removed" for c in result.changes)

    def test_security_scheme_added_non_breaking(self):
        old = _make_spec(security_schemes={})
        new = _make_spec(security_schemes={"bearerAuth": {"type": "http", "scheme": "bearer"}})
        result = diff_specs(old, new)
        assert any(c.kind == "security_scheme_added" for c in result.changes)

    def test_security_scheme_type_changed_breaking(self):
        old = _make_spec(security_schemes={"auth": {"type": "http"}})
        new = _make_spec(security_schemes={"auth": {"type": "oauth2"}})
        result = diff_specs(old, new)
        assert any(c.kind == "security_scheme_type_changed" for c in result.changes)


# ── Security requirements diff tests ──

class TestSecurityRequirementsDiff:
    def test_global_security_removed_dangerous(self):
        old = _make_spec(security=[{"bearerAuth": []}])
        new = _make_spec(security=[])
        result = diff_specs(old, new)
        assert any(c.kind == "global_security_removed" for c in result.changes)

    def test_global_security_added_dangerous(self):
        old = _make_spec(security=[])
        new = _make_spec(security=[{"bearerAuth": []}])
        result = diff_specs(old, new)
        assert any(c.kind == "global_security_added" for c in result.changes)


# ── Server diff tests ──

class TestServerDiff:
    def test_server_removed_dangerous(self):
        old = _make_spec(servers=[{"url": "https://api.example.com"}])
        new = _make_spec(servers=[{"url": "https://v2.api.example.com"}])
        result = diff_specs(old, new)
        assert any(c.kind == "server_removed" for c in result.changes)

    def test_server_added_info(self):
        old = _make_spec(servers=[{"url": "https://api.example.com"}])
        new = _make_spec(servers=[{"url": "https://api.example.com"}, {"url": "https://staging.example.com"}])
        result = diff_specs(old, new)
        assert any(c.kind == "server_added" and c.severity == Severity.INFO for c in result.changes)


# ── Info diff tests ──

class TestInfoDiff:
    def test_title_changed_info(self):
        old = _make_spec(info={"title": "Old API", "version": "1.0.0"})
        new = _make_spec(info={"title": "New API", "version": "1.0.0"})
        result = diff_specs(old, new)
        assert any(c.kind == "title_changed" for c in result.changes)

    def test_version_changed_info(self):
        old = _make_spec(info={"title": "API", "version": "1.0.0"})
        new = _make_spec(info={"title": "API", "version": "2.0.0"})
        result = diff_specs(old, new)
        assert any(c.kind == "api_version_changed" for c in result.changes)


# ── Integration / complex scenario tests ──

class TestDiffIntegration:
    def test_identical_specs_no_changes(self):
        spec = _make_spec(paths={"/users": {"get": {"responses": {"200": {"description": "OK"}}}}})
        result = diff_specs(spec, spec)
        assert len(result.changes) == 0
        assert not result.has_breaking

    def test_complex_multi_change_scenario(self):
        old = _make_spec(
            paths={
                "/users": {
                    "get": {
                        "parameters": [{"name": "page", "in": "query", "required": False}],
                        "responses": {"200": {"description": "OK"}},
                    },
                    "delete": {"responses": {"204": {"description": "No Content"}}},
                },
                "/items": {"get": {"responses": {"200": {"description": "OK"}}}},
            },
            schemas={"User": {"type": "object", "required": ["id"], "properties": {"id": {"type": "string"}}}},
        )
        new = _make_spec(
            paths={
                "/users": {
                    "get": {
                        "parameters": [{"name": "page", "in": "query", "required": True}],
                        "responses": {"200": {"description": "OK"}},
                    },
                },
            },
            schemas={"User": {"type": "object", "required": ["id", "name"], "properties": {"id": {"type": "string"}, "name": {"type": "string"}}}},
        )
        result = diff_specs(old, new)
        assert result.has_breaking
        # Should detect: path /items removed, operation DELETE removed, param became required, property became required
        breaking = result.breaking_changes
        assert len(breaking) >= 3

    def test_openapi_version_captured(self):
        old = _make_spec(openapi="3.0.0")
        new = _make_spec(openapi="3.1.0")
        result = diff_specs(old, new)
        assert result.old_version == "3.0.0"
        assert result.new_version == "3.1.0"

    def test_empty_specs(self):
        result = diff_specs({}, {})
        assert len(result.changes) == 0

    def test_adding_everything_non_breaking(self):
        old = _make_spec()
        new = _make_spec(
            paths={"/new": {"get": {"responses": {"200": {"description": "OK"}}}}},
            schemas={"NewItem": {"type": "object"}},
        )
        result = diff_specs(old, new)
        assert not result.has_breaking
