#!/usr/bin/env python3
"""Validate a pipeline JSON artifact against its stage's JSON Schema.

Implements the deliberate draft-07 subset declared in
`skills/damabok-shared/SCHEMA-CONVENTIONS.md`:

    type, required, properties, additionalProperties, enum, const, pattern,
    items, minItems

This is NOT a general-purpose draft-07 validator. Keywords outside the subset
($ref, oneOf, allOf, anyOf, if/then, format) are rejected as schema errors
rather than ignored -- the complexity budget is enforced by the tool, not just
documented. Stdlib only, so the orchestrator can call it with no install step.

Usage:
    python3 tools/validate_artifact.py --schema <schema.json> --data <artifact.json>

Exit codes:
    0  data conforms to the schema
    1  data violates the schema (one line per violation on stdout)
    2  usage error, unreadable file, malformed JSON, or unsupported schema keyword
"""

import argparse
import json
import re
import sys

SUPPORTED = {
    "$schema",
    "$id",
    "title",
    "description",
    "type",
    "required",
    "properties",
    "additionalProperties",
    "enum",
    "const",
    "pattern",
    "items",
    "minItems",
}

TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "boolean": bool,
    "null": type(None),
}


def type_name(value):
    """JSON type name for a Python value, for readable error messages."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, str):
        return "string"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def matches_type(value, expected):
    """True when value satisfies the JSON Schema type `expected`."""
    if expected == "integer":
        # bool is a subclass of int in Python; JSON Schema keeps them distinct.
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    py_type = TYPES.get(expected)
    if py_type is None:
        return False
    if py_type is not bool and isinstance(value, bool):
        # Guard against bool sneaking through as an int-like value.
        return expected == "boolean"
    return isinstance(value, py_type)


def check_schema_keywords(schema, path="$"):
    """Reject schema keywords outside the supported subset. Returns error strings."""
    errors = []
    if not isinstance(schema, dict):
        return [f"{path}: schema must be an object, got {type_name(schema)}"]
    for key in schema:
        if key not in SUPPORTED:
            errors.append(f"{path}: unsupported schema keyword '{key}'")
    if isinstance(schema.get("properties"), dict):
        for name, sub in schema["properties"].items():
            errors.extend(check_schema_keywords(sub, f"{path}/properties/{name}"))
    if isinstance(schema.get("items"), dict):
        errors.extend(check_schema_keywords(schema["items"], f"{path}/items"))
    return errors


def validate(schema, data, path="$"):
    """Validate `data` against `schema`. Returns a list of violation strings."""
    errors = []

    if "const" in schema and data != schema["const"]:
        errors.append(f"{path}: expected const {schema['const']!r}, got {data!r}")

    if "enum" in schema and data not in schema["enum"]:
        allowed = ", ".join(repr(v) for v in schema["enum"])
        errors.append(f"{path}: {data!r} is not one of [{allowed}]")

    expected = schema.get("type")
    if expected is not None and not matches_type(data, expected):
        errors.append(f"{path}: expected {expected}, got {type_name(data)}")
        # Type is wrong, so structural checks below would only add noise.
        return errors

    if isinstance(data, str) and "pattern" in schema:
        if re.search(schema["pattern"], data) is None:
            errors.append(f"{path}: {data!r} does not match pattern {schema['pattern']}")

    if isinstance(data, dict):
        errors.extend(validate_object(schema, data, path))
    elif isinstance(data, list):
        errors.extend(validate_array(schema, data, path))

    return errors


def validate_object(schema, data, path):
    errors = []
    properties = schema.get("properties", {})

    for name in schema.get("required", []):
        if name not in data:
            errors.append(f"{path}: missing required property '{name}'")

    if schema.get("additionalProperties") is False:
        for name in data:
            if name not in properties:
                errors.append(f"{path}: unexpected property '{name}'")

    for name, value in data.items():
        if name in properties:
            errors.extend(validate(properties[name], value, f"{path}/{name}"))

    return errors


def validate_array(schema, data, path):
    errors = []

    min_items = schema.get("minItems")
    if min_items is not None and len(data) < min_items:
        errors.append(f"{path}: expected at least {min_items} item(s), got {len(data)}")

    item_schema = schema.get("items")
    if isinstance(item_schema, dict):
        for index, item in enumerate(data):
            errors.extend(validate(item_schema, item, f"{path}/{index}"))

    return errors


def load_json(kind, filepath):
    """Read and parse a JSON file, exiting 2 with a clear message on failure."""
    try:
        with open(filepath, encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        sys.stderr.write(f"ERROR: {kind} file not found: {filepath}\n")
        raise SystemExit(2)
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"ERROR: {kind} file is not valid JSON: {filepath}\n  {exc}\n")
        raise SystemExit(2)
    except OSError as exc:
        sys.stderr.write(f"ERROR: cannot read {kind} file {filepath}: {exc}\n")
        raise SystemExit(2)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate a pipeline JSON artifact against its stage's JSON Schema.",
    )
    parser.add_argument("--schema", required=True, help="path to the JSON Schema file")
    parser.add_argument("--data", required=True, help="path to the JSON artifact to validate")
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="suppress the PASS line; violations are still printed",
    )
    args = parser.parse_args(argv)

    schema = load_json("schema", args.schema)
    data = load_json("data", args.data)

    schema_errors = check_schema_keywords(schema)
    if schema_errors:
        sys.stderr.write(f"ERROR: schema uses keywords outside the supported subset: {args.schema}\n")
        for error in schema_errors:
            sys.stderr.write(f"  {error}\n")
        sys.stderr.write("See .agents/skills/_shared/SCHEMA-CONVENTIONS.md\n")
        return 2

    errors = validate(schema, data)

    if errors:
        print(f"FAIL: {args.data}")
        for error in errors:
            print(f"  {error}")
        return 1

    if not args.quiet:
        print(f"PASS: {args.data} conforms to {args.schema}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
