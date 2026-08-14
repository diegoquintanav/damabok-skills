---
name: openmetadata-mapper
description: "OpenMetadata, glossary term, classification, tag, entity reference, metadata mapping, data governance metadata. Map CONTEXT_LINEAGE.md concepts to OpenMetadata v1.12 definitions as MCP-consumable JSON."
license: Apache-2.0
metadata:
  author: diegoquintanav
  version: "2.0"
---

# OpenMetadata Mapper

## Activation Contract

Use when the user asks to generate, preview, or update `OPENMETADATA_MAPPING.md` / `OPENMETADATA_MAPPING.json`, map domain concepts to OpenMetadata glossary/classification/asset definitions, or prepare metadata for ingestion by an OpenMetadata MCP server.

Default to **read-only preview**. Write files only when the user explicitly says `apply`, `write`, `update`, or equivalent.

## Artifact location

Both artifacts live in the **output repo**, never in the analyzed repo:

```
<OUTPUT_REPO>/<repo-slug>/
├── OPENMETADATA_MAPPING.md    ← editable source of truth
└── OPENMETADATA_MAPPING.json  ← generated from it, validated, ingested via the OpenMetadata MCP
```

## Hard Rules

- **Never write to the analyzed repository.** Every artifact goes to `<OUTPUT_REPO>/<repo-slug>/`.
- **The markdown is the source of truth.** `OPENMETADATA_MAPPING.md` is the editable artifact (domain-business-modeling pattern: auto-managed region + `## Manual Notes`). `OPENMETADATA_MAPPING.json` is ALWAYS generated from the markdown — never hand-edit the JSON, and never generate it without writing/updating the markdown first.
- When lineage/DAMA inputs change: update the markdown (terms, classifications, asset mappings, unknowns) inside the auto region, preserve `## Manual Notes`, then regenerate the JSON.
- When the user edits the markdown directly: parse it and regenerate the JSON from it.
- Input: `context-lineage.json` (required) and `dama-assessment.json` (optional), falling back to the matching markdown when the JSON is absent. Never invent concepts, assets, or definitions.
- **Record uncertainty for the preview; only `domain-business-modeling` asks.** This stage *consumes* `_Avoid_` lists to build `synonyms` and raises no vocabulary candidates of its own. Anything it might notice is already visible to `context-lineage-generator`, which searches the same repository with the same tokens and has the file evidence to justify the claim. Ambiguous asset types and unresolved FQNs go to `## Unknown Mappings` for the user to settle in the preview. See [`../damabok-shared/AMBIGUITY-GATE.md`](../damabok-shared/AMBIGUITY-GATE.md).
- **Omit optional keys rather than emitting empty arrays** — a term with no synonyms has no `synonyms` key.
- Emit OpenMetadata v1.12 API-shaped JSON: `CreateGlossary`, `CreateGlossaryTerm`, `CreateClassification`, `CreateTag`, and asset `entityReference` shapes — so an OpenMetadata MCP server can ingest it directly.
- Fully qualified names: glossary terms `Glossary.Term`, tags `Classification.Tag`. Derive slugs from the concept stable IDs in the lineage (e.g. `concept:sw` → term `sw`); use one stable glossary name derived from the context.
- Every concept maps to exactly one glossary term. `_Avoid_` entries never become separate terms, and **only some of them become `synonyms`** — classify each one first, per the three-way test in [`OPENMETADATA-MAPPING-FORMAT.md`](./OPENMETADATA-MAPPING-FORMAT.md#classifying-_avoid_-entries). Emitting a disambiguation as a synonym tells the catalogue that two deliberately distinct concepts are the same word.
- `relatedTerms` use OpenMetadata relation types: `broader`, `narrower`, `synonym`, `relatedTo`, `partOf`, `hasPart`, `antonym`. They must reference only existing term FQNs.
- DAMA categories (only when the DAMA input is present) become one `DAMA` classification with tags `MasterData`, `ReferenceData`, `TransactionalDerived`, `GoldenRecordEntity`, `GoldenRecordMeasurement`, attached to the matching terms.
- Data I/O assets map to `entityReference`s with a conservative type: `table` (dbt_model/dbt_source/snapshot), `column`, `pipeline` (dag/script), `dashboard` (exposure). When the service/database FQN is unknown, use a `[SERVICE]` placeholder or record the gap — never invent an FQN.
- Determinism: identical markdown → identical JSON (terms in heading order, assets in table order). No secrets.
- Validate the final JSON against `assets/openmetadata-mapping.schema.json`; a mapping that fails schema validation is not complete — fix the markdown and regenerate, never patch the JSON by hand.

## Decision Gates

| Signal | Action |
| --- | --- |
| `OPENMETADATA_MAPPING.md` exists | Parse it as the source; apply input changes inside the auto region |
| Markdown does not exist yet | Build it from lineage/DAMA inputs per the FORMAT template |
| Concept has an explicit identifier (`sw`, `order`) | term name = identifier slug; displayName = canonical term |
| Concept has no identifier | term name = kebab/snake slug of canonical term |
| `_Avoid_` entry **matches another glossary term** | `relatedTerms` with `relatedTo` — a disambiguation, never a `synonyms` entry |
| `_Avoid_` entry is **avoided by two or more concepts** and is not itself a term | Neither `synonyms` nor `relatedTerms`. Omit it and note it in `## Unknown Mappings` as a missing-concept candidate for `domain-business-modeling` |
| `_Avoid_` entry matches nothing else | `synonyms` entry on the canonical term |
| Concept family visible in lineage (energies, tariffs, contracts) | `relatedTerms` with `broader`/`narrower`/`relatedTo` |
| DAMA_ASSESSMENT.md present | add `DAMA` classification + tags; attach per concept |
| Asset stable ID prefix known (`dbt_model:`, `dbt_source:`, `snapshot:`) | `entityReference` type `table` |
| Asset is `column:` | `entityReference` type `column` with parent table FQN |
| Asset is `dag:` / `script:` | `entityReference` type `pipeline` |
| Asset is `exposure:` | `entityReference` type `dashboard` |
| FQN or type not derivable | Record in `unknownMappings` with what you do know. Never guess |
| DAMA classification confidence is `Low`/`Medium` | Attach the tag and carry the upstream confidence into `## Unknown Mappings` as a note, so the preview shows what the tag rests on |
| Service name unknown | Use the `[SERVICE]` placeholder and note it once — deployment config, not a mapping gap |

## Execution Steps

1. Read `context-lineage.json` (and `dama-assessment.json` if present) and any existing `OPENMETADATA_MAPPING.md` from `<OUTPUT_REPO>/<repo-slug>/`.
2. Build or update the markdown source per [OPENMETADATA-MAPPING-FORMAT.md](./OPENMETADATA-MAPPING-FORMAT.md): glossary, terms (slug, displayName, description, synonyms from `_Avoid_` terms, relatedTerms, tags), classifications, asset mappings, unknown mappings — all inside the auto region, `## Manual Notes` preserved.
3. Route what you could not derive — ambiguous asset types, unresolved FQNs, weak DAMA→tag choices — to `## Unknown Mappings`, with what you do know. Ask nothing.
4. Generate `OPENMETADATA_MAPPING.json` from the markdown, following the derivation rules in the FORMAT file.
5. Validate: the JSON parses; every term in the markdown appears once in the JSON; `relatedTerms` reference existing term FQNs; no secrets. Then run the schema check:

   ```bash
   python3 <PLUGIN_ROOT>/scripts/validate_artifact.py \
     --schema <PLUGIN_ROOT>/skills/openmetadata-mapper/assets/openmetadata-mapping.schema.json \
     --data <OUTPUT_REPO>/<repo-slug>/OPENMETADATA_MAPPING.json
   ```

6. Preview by default; write both files only on explicit instruction.

## Output Contract

- `OPENMETADATA_MAPPING.md` — editable source, per the FORMAT template (auto region + Manual Notes).
- `OPENMETADATA_MAPPING.json` — generated from the markdown, per the FORMAT template.

Return:
- Whether this was preview or write mode.
- Files created or modified (always under `<OUTPUT_REPO>/<repo-slug>/`).
- Schema validation: `PASS` or `FAIL` against `assets/openmetadata-mapping.schema.json`.
- Counts: glossary terms, classifications/tags, asset entity references.
- `unknownMappings` needing human input (FQN gaps, ambiguous asset types), and why each could not be derived.

## References

- [OPENMETADATA-MAPPING-FORMAT.md](./OPENMETADATA-MAPPING-FORMAT.md) — markdown source template, unresolved-mapping routing, and JSON derivation rules.
- [`assets/openmetadata-mapping.schema.json`](./assets/openmetadata-mapping.schema.json) — JSON Schema the generated artifact must satisfy.
- [`../damabok-shared/AMBIGUITY-GATE.md`](../damabok-shared/AMBIGUITY-GATE.md) — how the pipeline handles uncertainty: which stage asks, and where every other stage records.
- [`../damabok-shared/SCHEMA-CONVENTIONS.md`](../damabok-shared/SCHEMA-CONVENTIONS.md) — shared JSON contract rules.
- [`../context-lineage-generator/SKILL.md`](../context-lineage-generator/SKILL.md) — produces the required input (`context-lineage.json`).
- [`../dama-assessment/SKILL.md`](../dama-assessment/SKILL.md) — optional input (`dama-assessment.json`).
- [`../domain-business-modeling/SKILL.md`](../domain-business-modeling/SKILL.md) — owns the vocabulary the mapping encodes; synonym/avoid candidates flow back to it.
- [`../project-lineage-generator/SKILL.md`](../project-lineage-generator/SKILL.md) — stable ID prefixes reused for asset references.
