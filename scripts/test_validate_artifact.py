#!/usr/bin/env python3
"""Self-tests for validate_artifact.py. Stdlib only: python3 tools/test_validate_artifact.py"""

import unittest

from validate_artifact import check_schema_keywords, validate

SCHEMA = {
    "type": "object",
    "required": ["schemaVersion", "terms"],
    "additionalProperties": False,
    "properties": {
        "schemaVersion": {"const": "context-v1"},
        "terms": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["term", "definition"],
                "additionalProperties": False,
                "properties": {
                    "term": {"type": "string"},
                    "definition": {"type": "string"},
                    "confidence": {"enum": ["High", "Medium", "Low"]},
                    "slug": {"type": "string", "pattern": "^[a-z][a-z0-9_-]*$"},
                    "avoid": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "unknowns": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["item", "reason"],
                "additionalProperties": False,
                "properties": {"item": {"type": "string"}, "reason": {"type": "string"}},
            },
        },
    },
}


def valid_doc():
    return {
        "schemaVersion": "context-v1",
        "terms": [{"term": "Order", "definition": "A shipping agreement.", "slug": "order"}],
    }


class TestValid(unittest.TestCase):
    def test_minimal_document_passes(self):
        self.assertEqual(validate(SCHEMA, valid_doc()), [])

    def test_optional_fields_may_be_omitted(self):
        """The complexity budget's core rule: often-empty arrays are never required."""
        doc = {"schemaVersion": "context-v1", "terms": [{"term": "T", "definition": "D"}]}
        self.assertEqual(validate(SCHEMA, doc), [])

    def test_optional_fields_may_be_present(self):
        doc = valid_doc()
        doc["terms"][0]["avoid"] = ["purchase", "transaction"]
        doc["unknowns"] = [{"item": "maduresa", "reason": "only exists as English column"}]
        self.assertEqual(validate(SCHEMA, doc), [])


class TestViolations(unittest.TestCase):
    def assert_one_error(self, doc, *fragments):
        errors = validate(SCHEMA, doc)
        self.assertEqual(len(errors), 1, f"expected exactly one error, got {errors}")
        for fragment in fragments:
            self.assertIn(fragment, errors[0])

    def test_missing_required_property(self):
        doc = valid_doc()
        del doc["terms"][0]["definition"]
        self.assert_one_error(doc, "$/terms/0", "missing required property 'definition'")

    def test_missing_required_at_root(self):
        self.assert_one_error({"schemaVersion": "context-v1"}, "$:", "'terms'")

    def test_wrong_type(self):
        doc = valid_doc()
        doc["terms"][0]["term"] = 42
        self.assert_one_error(doc, "$/terms/0/term", "expected string, got integer")

    def test_enum_violation(self):
        doc = valid_doc()
        doc["terms"][0]["confidence"] = "Maybe"
        self.assert_one_error(doc, "$/terms/0/confidence", "not one of")

    def test_pattern_violation(self):
        doc = valid_doc()
        doc["terms"][0]["slug"] = "ORDER"
        self.assert_one_error(doc, "$/terms/0/slug", "does not match pattern")

    def test_const_violation(self):
        doc = valid_doc()
        doc["schemaVersion"] = "context-v2"
        self.assert_one_error(doc, "$/schemaVersion", "expected const")

    def test_additional_property_rejected(self):
        doc = valid_doc()
        doc["terms"][0]["notes"] = "hand-added"
        self.assert_one_error(doc, "$/terms/0", "unexpected property 'notes'")

    def test_min_items(self):
        doc = valid_doc()
        doc["terms"] = []
        self.assert_one_error(doc, "$/terms", "at least 1 item")

    def test_boolean_is_not_a_string(self):
        """bool subclasses int in Python; JSON Schema keeps the types distinct."""
        doc = valid_doc()
        doc["terms"][0]["term"] = True
        self.assert_one_error(doc, "expected string, got boolean")

    def test_reports_every_violation_not_just_the_first(self):
        doc = {"schemaVersion": "wrong", "terms": [{"term": "T"}, {"definition": "D"}]}
        errors = validate(SCHEMA, doc)
        self.assertEqual(len(errors), 3, errors)

    def test_nested_paths_are_addressable(self):
        doc = valid_doc()
        doc["terms"][0]["avoid"] = ["ok", 3]
        self.assert_one_error(doc, "$/terms/0/avoid/1")


class TestSchemaKeywordGuard(unittest.TestCase):
    """The tool enforces SCHEMA-CONVENTIONS.md rather than silently ignoring keywords."""

    def test_supported_schema_is_accepted(self):
        self.assertEqual(check_schema_keywords(SCHEMA), [])

    def test_ref_is_rejected(self):
        errors = check_schema_keywords({"type": "object", "$ref": "#/definitions/x"})
        self.assertEqual(len(errors), 1)
        self.assertIn("$ref", errors[0])

    def test_oneof_is_rejected_when_nested(self):
        schema = {"type": "object", "properties": {"a": {"oneOf": [{"type": "string"}]}}}
        errors = check_schema_keywords(schema)
        self.assertEqual(len(errors), 1)
        self.assertIn("$/properties/a", errors[0])

    def test_unsupported_keyword_inside_items_is_rejected(self):
        schema = {"type": "array", "items": {"type": "string", "format": "email"}}
        errors = check_schema_keywords(schema)
        self.assertEqual(len(errors), 1)
        self.assertIn("format", errors[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
