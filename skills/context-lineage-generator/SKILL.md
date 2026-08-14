---
name: context-lineage-generator
description: "CONTEXT_LINEAGE.md, context lineage, concept inventory, concept-to-data mapping. Generate per-repo inventories mapping CONTEXT.md domain concepts to data read/write points."
license: Apache-2.0
metadata:
  author: diegoquintanav
  version: "1.0"
---

# Context Lineage Generator

## Activation Contract

Use when the user asks to generate, preview, or update `CONTEXT_LINEAGE.md`, map domain concepts from `CONTEXT.md` to the codebase, find where a concept is read or written, or build concept-level data lineage.

Default to **read-only preview**. Write files only when the user explicitly says `apply`, `write`, `update`, or equivalent.

## Artifact location

Both artifacts live in the **output repo**, never in the analyzed repo:

```
<OUTPUT_REPO>/<repo-slug>/
├── CONTEXT_LINEAGE.md    ← editable source of truth
└── context-lineage.json  ← generated from it, validated, consumed by dama-assessment
```

Input `context.json` / `CONTEXT.md` come from the same directory; the analyzed repository is searched but never written to.

## Hard Rules

- **Never write to the analyzed repository.** It is read-only input. Every artifact goes to `<OUTPUT_REPO>/<repo-slug>/`.
- Read `context.json` as the source of concepts (falling back to `CONTEXT.md` when the JSON is absent). Never invent concepts or definitions.
- Analyze only the target repository. Do not crawl sibling repos or infer cross-repo links from local filesystem layout.
- **Focus on data read/write points**: databases, dbt models/sources/snapshots, DAG operators, scripts, APIs, files, and similar storage. Non-data mentions are secondary and recorded as such.
- Generate `CONTEXT_LINEAGE.md` as the canonical artifact using the template in [CONTEXT-LINEAGE-FORMAT.md](./CONTEXT-LINEAGE-FORMAT.md). Fixed template so another agent can compare files reliably.
- Preserve manual notes. Only replace content between `<!-- context-lineage:auto:start -->` and `<!-- context-lineage:auto:end -->`.
- Cover every concept in the input. Record unknowns/gaps explicitly instead of pretending certainty.
- Never expose secret values. Env/secret names and evidence only.
- Mark each data relationship with evidence and confidence: `High`, `Medium`, or `Low`.
- Matches of `_Avoid_` terms are terminology-drift candidates, never lineage edges.
- **Record uncertainty for the gate; only `domain-business-modeling` asks.** Every `_Avoid_`-term-found-in-code hit becomes a `proposed` row in `## Terminology Drift`, which `domain-business-modeling` rules on at its gate — it owns `CONTEXT.md`, this stage does not. Rows already marked `rejected` stay rejected and are never re-raised. See [`../damabok-shared/AMBIGUITY-GATE.md`](../damabok-shared/AMBIGUITY-GATE.md).
- **Regenerate `context-lineage.json` from the markdown** after any change, and validate it. A validation failure is fixed in the markdown, never patched into the JSON.

## Decision Gates

| Signal | Action |
| --- | --- |
| Concept has an explicit identifier in `CONTEXT.md` (`sw`, `order`, `carrier-rate`) | Search identifier plus snake_case/kebab variants as primary tokens |
| Concept has no explicit identifier | Search canonical name and key terms; cap confidence at Medium |
| `CONTEXT-MAP.md` exists | Iterate contexts; prefix concept IDs with the context slug |
| dbt project present | Prioritize `models/`, `snapshots/`, and sources YAMLs; use `ref()` / `source()` as edge evidence |
| DAGs or scripts exist | Map reads/writes at I/O boundaries: DB, files, APIs, env/secrets |
| Token found only in docs/tests/comments | Record as other mention, not a data I/O point |
| `_Avoid_` term found in code | Record a `proposed` row in `## Terminology Drift` with the location as evidence. Carry forward any existing `rejected` row unchanged |
| Concept has zero data I/O points after searching | Record it in `## Unknowns and Gaps`, stating whether you believe it absent from the data layer or a search miss |
| Data point would be recorded at `Low` confidence | Write it, marked `Low`, with the evidence that makes it weak. The preview is where the user judges it |

## Execution Steps

1. Read `context.json` (or `CONTEXT.md`, and `CONTEXT-MAP.md` if present) from `<OUTPUT_REPO>/<repo-slug>/`. Extract every concept: stable ID, canonical term, definition, explicit identifier, `_Avoid_` terms.
2. Derive search tokens per concept: explicit identifier, canonical name, snake_case/kebab variants, and `_Avoid_` terms (drift checks only).
3. Search the target repo with case-insensitive pattern matching across code, config, and data files (SQL, YAML, Python, DAGs, CI, env templates, docs).
4. Classify each hit as data I/O point or other mention. Record evidence as compact file path plus symbol, line, or command.
5. Build the inventory per the FORMAT file: concept table, per-concept details with data read/write points, reverse data-asset index, terminology drift, unknowns.
6. Route what you could not settle: `_Avoid_`-term hits to `## Terminology Drift` as `proposed` candidates, everything else — `Low`-confidence points you doubt, concepts with no data points — to `## Unknowns and Gaps`. Ask nothing.
7. Preview by default; write only on explicit instruction.
8. Generate `context-lineage.json` from the markdown per the derivation rules, then validate:

   ```bash
   python3 <PLUGIN_ROOT>/scripts/validate_artifact.py \
     --schema <PLUGIN_ROOT>/skills/context-lineage-generator/assets/context-lineage.schema.json \
     --data <OUTPUT_REPO>/<repo-slug>/context-lineage.json
   ```

## Output Contract

`CONTEXT_LINEAGE.md` must follow [CONTEXT-LINEAGE-FORMAT.md](./CONTEXT-LINEAGE-FORMAT.md) exactly, with generated content between `<!-- context-lineage:auto:start -->` and `<!-- context-lineage:auto:end -->`.

Return:
- Whether this was preview or write mode.
- Files created or modified (always under `<OUTPUT_REPO>/<repo-slug>/`).
- Concepts with data I/O points found, with counts, and concepts with none.
- Schema validation PASS/FAIL.
- Terminology-drift candidates recorded, with their status, for the next `domain-business-modeling` gate.
- Unknowns and gaps needing human validation.

## References

- [CONTEXT-LINEAGE-FORMAT.md](./CONTEXT-LINEAGE-FORMAT.md) — stable markdown template, candidate recording, and markdown→JSON derivation rules.
- [`assets/context-lineage.schema.json`](./assets/context-lineage.schema.json) — the contract `context-lineage.json` must satisfy.
- [`../damabok-shared/AMBIGUITY-GATE.md`](../damabok-shared/AMBIGUITY-GATE.md) — how the pipeline handles uncertainty: which stage asks, and where every other stage records.
- [`../damabok-shared/SCHEMA-CONVENTIONS.md`](../damabok-shared/SCHEMA-CONVENTIONS.md) — shared JSON contract rules.
- [`../project-lineage-generator/SKILL.md`](../project-lineage-generator/SKILL.md) — sibling asset/process lineage; reuse its stable ID prefixes for cross-repo comparability.
- [`../domain-business-modeling/SKILL.md`](../domain-business-modeling/SKILL.md) — owns `CONTEXT.md` vocabulary; drift candidates flow back to it.
- [`../dama-assessment/SKILL.md`](../dama-assessment/SKILL.md) — consumes `context-lineage.json`.
