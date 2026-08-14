# Schema Conventions

The shared rulebook for every JSON companion artifact in the pipeline. Each stage's
markdown is the human-editable source of truth; the JSON is derived from it, validated,
and consumed by the next stage.

This file is a reference doc, not a skill. Stages link to it from their `## References`
section.

## Why the JSON exists

The markdown is for humans: it carries prose, evidence, and manual notes. The JSON is for
the next skill in the chain: a stable, validated contract that doesn't require the
downstream stage to re-parse markdown tables and hope the columns haven't moved.

Consequence: **the next stage reads the JSON, not the markdown.** If a stage needs
something the JSON doesn't carry, that's a schema gap to fix, not a reason to parse the
markdown.

## Draft and tooling

- JSON Schema **draft-07**.
- Validated by `scripts/validate_artifact.py`, which implements a deliberate subset:
  `type`, `required`, `properties`, `additionalProperties`, `enum`, `const`, `pattern`,
  `items`, `minItems`.
- **Do not use** `$ref`, `oneOf`, `allOf`, `anyOf`, `if`/`then`, or `format`. If a schema
  seems to need them, the shape is too complex — flatten it instead.

## Complexity budget

The pipeline's schemas are read and hand-checked by people, and written by an LLM one
field at a time. Both get worse as nesting and required-field count grow. Hard limits:

1. **Max two levels of object nesting inside array items.** `root.items[]` and, where a
   parent genuinely owns children, `root.items[].children[]`. Never a third level.
2. **`required` lists only what makes the record meaningful.** A field that is routinely
   absent is optional, not required-with-an-empty-value.
3. **Never require an array that is often empty.** `synonyms`, `tags`, `relatedTerms`,
   `unknowns` and friends are optional properties with an implicit `[]` default. Forcing
   the generator to emit `"synonyms": []` on every record to satisfy the schema is noise
   in the artifact and a pointless failure mode in generation.
4. **Never require a field whose value would be `null`.** If a concept has no golden
   record, omit the `goldenRecord` key — do not require it and fill it with nulls.
5. **`additionalProperties: false` stays.** Strictness catches typos and drift; it costs
   nothing as long as rules 2–4 keep the required set small.

The anti-pattern these rules exist to prevent: a term object requiring seven fields, four
of which are usually empty arrays, nested four levels deep.

## Uniform shapes

Reuse these across every schema rather than inventing per-stage variants:

| Concern | Shape |
| --- | --- |
| Version marker | `schemaVersion`: a `const` string on the root object, e.g. `"context-v1"`. Always required. |
| Provenance | `generatedFrom`: a plain string naming the input artifact, e.g. `"CONTEXT.md"`. Not an object. The first stage has no upstream artifact and so omits it entirely — `sourceRepo` carries its provenance. |
| Analyzed repo | `sourceRepo`: the repo slug. Required on every stage, so an artifact is self-identifying once collected into the corpus. |
| Unresolved items | `unknowns`: optional array of `{item, reason}`, both strings. |
| Candidate status | `status`: optional `enum: ["proposed", "rejected"]` on a vocabulary-candidate row. Absent means `proposed`. There is no `accepted` — see [AMBIGUITY-GATE.md](./AMBIGUITY-GATE.md). |
| Provenance of an accepted term | `source`: optional string naming the artifact and candidate a term came from. Omit for terms derived directly from the analyzed repository. Because an accepted candidate's row is dropped, this is the only surviving record that the term did not originate in the glossary. |
| Confidence | `enum: ["High", "Medium", "Low"]` — matching the markdown tables verbatim. |
| Direction / role | `enum: ["consumes", "produces", "transforms"]` |

## Naming and identifiers

Stable IDs reuse the prefixes already defined in
[`CONTEXT-LINEAGE-FORMAT.md`](../context-lineage-generator/CONTEXT-LINEAGE-FORMAT.md) —
do not redefine them per stage:

`concept:`, `table:`, `dbt_source:`, `dbt_model:`, `snapshot:`, `exposure:`, `column:`,
`dag:`, `script:`, `api:`, `file:`, `ci:`, `env:`, `secret:`

A concept's `stableId` is the join key across all four stages. `concept:sw` in
`context.json` is the same concept as `concept:sw` in `dama-assessment.json`.

## Versioning

Every root object carries `schemaVersion` as a `const`. A breaking change to a schema
means bumping that const (`context-v1` → `context-v2`), so an artifact generated under the
old shape fails loudly against the new schema instead of being silently misread.

## Generation rules

- **The JSON is always regenerated from the markdown, never hand-edited.** A validation
  failure is fixed in the markdown, then regenerated.
- **Determinism**: the JSON mirrors markdown order exactly. Identical markdown produces
  identical JSON.
- **No timestamps.** A `generatedAt`/`date` field makes every regeneration a diff even
  when nothing changed, which contradicts determinism and trains reviewers to ignore the
  file. Git already records when the artifact changed.
- **No secrets**: env var and secret *names* may appear; values never do.
- **No duplication of upstream prose.** If the previous stage's JSON already carries a
  definition, reference the concept by `stableId` rather than restating it — restated
  prose drifts.
