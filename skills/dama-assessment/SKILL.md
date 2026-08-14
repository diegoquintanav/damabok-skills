---
name: dama-assessment
description: "DAMA assessment, master data, reference data, golden record, MDM candidates, data governance. Classify CONTEXT_LINEAGE.md concepts into DAMA-DMBOK categories and propose golden-record candidates."
license: Apache-2.0
metadata:
  author: diegoquintanav
  version: "1.0"
---

# DAMA Assessment

## Activation Contract

Use when the user asks to generate, preview, or update `DAMA_ASSESSMENT.md`, classify domain concepts into DAMA-DMBOK categories (master data, reference data, golden records), or propose MDM/data-governance candidates from a context lineage.

Default to **read-only preview**. Write files only when the user explicitly says `apply`, `write`, `update`, or equivalent.

## Artifact location

Both artifacts live in the **output repo**, never in the analyzed repo:

```
<OUTPUT_REPO>/<repo-slug>/
├── DAMA_ASSESSMENT.md     ← editable source of truth
└── dama-assessment.json   ← generated from it, validated, consumed by openmetadata-mapper
```

## Hard Rules

- **Never write to the analyzed repository.** Every artifact goes to `<OUTPUT_REPO>/<repo-slug>/`.
- Input is `context-lineage.json` (falling back to `CONTEXT_LINEAGE.md` when the JSON is absent). Never invent concepts; classify only what the input contains.
- Surface vocabulary-absent candidates: when an `_Avoid_` term in `CONTEXT.md` maps to real code entities (models, columns, sources), list it under Open Questions with evidence and a proposed category. Never auto-classify absent terms into the category tables.
- Classify EVERY concept into one primary category: master data, reference data, or transactional/derived. No concept left unclassified.
- Golden record is a cross-cutting flag, not a peer category. A master-data entity with survivorship evidence is additionally a golden record (`entity`, MDM). Transactional/measurement data reconciled across sources is a golden record (`measurement`, data-quality survivorship) and its primary category stays transactional/derived.
- Golden-record flags require survivorship evidence: multiple source systems reconciled by dedup, pick-best, maturity selection, snapshot, or match/merge logic. Cite the model that performs the survival.
- **Record uncertainty for the gate; only `domain-business-modeling` asks.** Weak or ambiguous classifications are written with `Low`/`Medium` confidence and their evidence, for the user to judge in the preview. Newly surfaced wording becomes a `proposed` row in `## Glossary Suggestions`, which `domain-business-modeling` rules on at its gate — it owns `CONTEXT.md`, this stage does not. Rows already marked `rejected` stay rejected and are never re-raised. See [`../damabok-shared/AMBIGUITY-GATE.md`](../damabok-shared/AMBIGUITY-GATE.md).
- Regenerate `dama-assessment.json` from the markdown after any change, and validate it. A validation failure is fixed in the markdown, never patched into the JSON.
- Generate `DAMA_ASSESSMENT.md` with the template in [DAMA-ASSESSMENT-FORMAT.md](./DAMA-ASSESSMENT-FORMAT.md). Fixed template; preserve manual notes; only replace content between `<!-- dama-assessment:auto:start -->` and `<!-- dama-assessment:auto:end -->`.
- Glossary suggestions follow the `CONTEXT.md` format (term, definition, avoid list) and must NOT duplicate terms already present.
- Never expose secret values. Evidence only.
- Mark every classification with evidence and confidence: `High`, `Medium`, or `Low`.

## Decision Gates

| Signal | Example | Category |
| --- | --- | --- |
| Stable identity, shared across processes, slow-changing; also reconciled across sources → + golden record (entity) | WarehouseLocation | Master data |
| Code list / categorization values, often standardized | NORTH/SOUTH/EAST, `carrier-rate` values, timezone map | Reference data |
| Transactional data with multiple sources reconciled by dedup/pick-best/snapshot → + golden record (measurement) | sw (carrier_api vs wms vs depot_scanner) | Transactional / derived |
| Computed from other concepts, no own identity | net-margin, margins, costs | Transactional / derived |
| No clear signal, or evidence conflicts | — | Classify on the best available evidence at `Low` confidence and record the conflict in `## Open Questions` |

## Execution Steps

1. Read the input: Concepts table, Concept Details, Data I/O Summary, and any Unknowns/Gaps.
2. Classify each concept into one primary category per the Decision Gates. Record stable IDs and evidence from the lineage.
3. Apply the golden-record flag cross-cutting: master-data entities with survivorship evidence get `entity` (MDM); transactional data with survivorship evidence gets `measurement` (data-quality survivorship, not entity MDM). Name the source systems reconciled and the survivorship model (e.g. `int_shipment_weight__scanner_carrier_pick_best`).
4. Scan `_Avoid_` terms from `CONTEXT.md`: if an avoided term appears in code identifiers (e.g. `vendor` → `raw_crm__historical_order_terms`), record it in Open Questions as a vocabulary-absent candidate with evidence and a proposed category. Never auto-classify it into the category tables.
5. Propose glossary suggestions: terms visible in data assets but missing from `CONTEXT.md` (e.g. maturity, source system, survivorship), in `CONTEXT.md` format.
6. Build `DAMA_ASSESSMENT.md` per the FORMAT file, marking glossary suggestions `proposed` and carrying any existing `rejected` rows forward verbatim. Ask nothing. Preview by default; write only on explicit instruction.
7. Generate `dama-assessment.json` from the markdown per the derivation rules, then validate:

   ```bash
   python3 <PLUGIN_ROOT>/scripts/validate_artifact.py \
     --schema <PLUGIN_ROOT>/skills/dama-assessment/assets/dama-assessment.schema.json \
     --data <OUTPUT_REPO>/<repo-slug>/dama-assessment.json
   ```

## Output Contract

`DAMA_ASSESSMENT.md` must follow [DAMA-ASSESSMENT-FORMAT.md](./DAMA-ASSESSMENT-FORMAT.md) exactly, with generated content between `<!-- dama-assessment:auto:start -->` and `<!-- dama-assessment:auto:end -->`.

Return:
- Whether this was preview or write mode.
- Files created or modified (always under `<OUTPUT_REPO>/<repo-slug>/`).
- Classification counts per primary category, plus golden-record flags.
- Golden-record flags with survivorship evidence and record type (entity MDM / measurement data-quality).
- Schema validation PASS/FAIL.
- Glossary suggestions recorded, with their status.
- Glossary suggestions and open questions needing human confirmation.

## References

- [DAMA-ASSESSMENT-FORMAT.md](./DAMA-ASSESSMENT-FORMAT.md) — stable markdown template, candidate recording, and markdown→JSON derivation rules.
- [`assets/dama-assessment.schema.json`](./assets/dama-assessment.schema.json) — the contract `dama-assessment.json` must satisfy.
- [`../damabok-shared/AMBIGUITY-GATE.md`](../damabok-shared/AMBIGUITY-GATE.md) — how the pipeline handles uncertainty: which stage asks, and where every other stage records.
- [`../damabok-shared/SCHEMA-CONVENTIONS.md`](../damabok-shared/SCHEMA-CONVENTIONS.md) — shared JSON contract rules.
- [`../context-lineage-generator/SKILL.md`](../context-lineage-generator/SKILL.md) — produces the input artifact (`context-lineage.json`).
- [`../domain-business-modeling/SKILL.md`](../domain-business-modeling/SKILL.md) — owns `CONTEXT.md`; glossary suggestions flow back to it.
- [`../openmetadata-mapper/SKILL.md`](../openmetadata-mapper/SKILL.md) — consumes `dama-assessment.json`.
