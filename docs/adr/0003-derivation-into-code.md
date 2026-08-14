---
status: proposed
---

# Derivation moves into code, as one CLI

For example, in an observed execution of the pipeline against a private repository, one
run spent roughly 226k subagent tokens turning 140KB of markdown into 262KB of JSON, most
of it deterministic transcription. Every `## Derivation rules (markdown →
JSON)` table is already a parser specification being executed by a language model. Moving
that into `scripts/derive_json.py` removes most of the cost and upgrades regeneration from
"deterministic if the model behaves" to actually reproducible.

**One CLI with `--stage context|lineage|dama|openmetadata`**, not four scripts — they
would duplicate the markdown-table parser four ways and drift apart.

Two constraints the run exposed, both of which will silently corrupt output if missed:

- **Respect backtick spans when splitting cells.** A regex `^wh_(north|south|east)` inside
  backticks shreds into three cells under a naive split on `|`.
- **Parse by header name, never by column position.** Column order is not stable across
  tables: in `**Other mentions**` tables the evidence cell follows Confidence, while
  elsewhere it precedes it.

Anything generated must validate with `scripts/validate_artifact.py` rather than growing a
second validation path. Note that it deliberately *rejects* `$ref`, `oneOf`, `allOf` and
`format` instead of ignoring them, so new schemas must stay inside the supported subset.

What remains for the model after this lands is the judgment: data-I/O versus mention,
confidence assignment, and the gate.
