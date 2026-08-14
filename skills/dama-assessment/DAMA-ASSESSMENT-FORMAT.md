# DAMA_ASSESSMENT.md Format

The `dama-assessment` skill produces TWO artifacts in `OUTPUT_REPO/<repo-slug>/`, next to `CONTEXT_LINEAGE.md`:

- **`DAMA_ASSESSMENT.md`** — the **editable source of truth**, following the template below. Content between the auto markers is generated; everything below `## Manual Notes` is preserved.
- **`dama-assessment.json`** — **generated from the markdown**, validated against `assets/dama-assessment.schema.json`, and consumed by `openmetadata-mapper`. Never hand-edit the JSON; regenerate it after any markdown change.

## Template

```md
# DAMA Assessment

> Generated from `CONTEXT_LINEAGE.md` by the `dama-assessment` skill.

<!-- dama-assessment:auto:start -->
## Classification Summary

| Category | Count | Concepts |
| --- | --- | --- |

> Golden record flags are cross-cutting and listed under `## Golden Record Candidates`; a flagged master entity also appears under `## Master Data Candidates`.

## Master Data Candidates

| Concept | Stable ID | Rationale | Key data assets | Confidence |
| --- | --- | --- | --- | --- |

## Reference Data Candidates

| Concept | Stable ID | Code values / domains | Managed in | Confidence |
| --- | --- | --- | --- | --- |

## Golden Record Candidates

| Concept | Stable ID | Record type | Source systems reconciled | Survivorship model | Evidence | Confidence |
| --- | --- | --- | --- | --- | --- | --- |

## Transactional / Derived

| Concept | Stable ID | Basis | Confidence |
| --- | --- | --- | --- |

## Glossary Suggestions

| Proposed term | Definition | Suggested context | Avoid | Confidence | Status |
| --- | --- | --- | --- | --- | --- |

## Open Questions

## Unknowns and Gaps

## Refresh
<!-- dama-assessment:auto:end -->

## Manual Notes
```

## Rules

- Exactly one primary category per concept; a concept may additionally carry the golden-record flag. List every concept from the input, even when a category has no hits.
- Stable IDs reuse sibling prefixes: `concept:`, `dbt_source:`, `dbt_model:`, `snapshot:`, `column:`, `dag:`, `script:`, `api:`, `file:`, `ci:`, `env:`, `secret:`.
- **Golden record**: cross-cutting flag, not a peer category. Requires two or more distinct sources reconciled by survivorship logic (dedup, pick-best, maturity selection, snapshot, match/merge). `Record type` is `entity` (MDM: a master-data entity reconciled across sources, e.g. a warehouse location — the concept ALSO appears under Master Data) or `measurement` (data-quality survivorship: transactional values reconciled across sources, e.g. shipment weight readings — the concept stays under Transactional / Derived). Cite the model that performs the survival.
- **Vocabulary-absent candidates**: `_Avoid_` terms in `CONTEXT.md` that map to code entities are listed under `## Open Questions` with evidence and a proposed category. They are never auto-classified into the category tables.
- **Confidence**: `High` — clear signal with strong evidence; `Medium` — plausible but partial evidence; `Low` — inferred.
- **Glossary suggestions** follow the `CONTEXT.md` format: canonical term, one/two-sentence definition, `_Avoid_` list. Never duplicate existing `CONTEXT.md` terms.
- Omit tables with no rows.
- Preserve manual notes below the auto markers verbatim.

## Vocabulary candidates

**This stage asks the user nothing.** It records what it is unsure about and lets the
right reader settle it. See [`../damabok-shared/AMBIGUITY-GATE.md`](../damabok-shared/AMBIGUITY-GATE.md).

- **`Low`-confidence or ambiguous classifications** — a concept that could be reference
  data or master data — are written with that confidence and the evidence behind them.
  The user judges them in the preview, next to the evidence.
- **New glossary terms** not already in `CONTEXT.md` become `proposed` rows in
  `## Glossary Suggestions`. `domain-business-modeling` rules on them at its gate; this
  stage never edits the glossary.
- **Conflicting evidence** goes to `## Open Questions` with both sides stated.

### Status column

`proposed` (or empty) means nobody has ruled on it. `rejected` means the user declined it
at a previous gate — **carry those rows forward verbatim and never re-raise them.** An
accepted suggestion does not appear here at all: it is already a term in `CONTEXT.md`, and
`## Glossary Suggestions` must not duplicate terms the glossary already has.

## Derivation rules (markdown → JSON)

| Markdown | JSON |
| --- | --- |
| Analyzed repo's directory basename | `sourceRepo` |
| The input artifact named in the blockquote | `generatedFrom` (normally `"CONTEXT_LINEAGE.md"`) |
| Rows of `## Master Data Candidates` | `classifications[]` with `category: "master_data"` |
| Rows of `## Reference Data Candidates` | `classifications[]` with `category: "reference_data"` |
| Rows of `## Transactional / Derived` | `classifications[]` with `category: "transactional_derived"` |
| `Concept` / `Stable ID` / `Confidence` columns | `classifications[].concept`, `.stableId`, `.confidence` |
| `Rationale` / `Basis` / `Code values / domains` column — whichever descriptive column that table has | `classifications[].rationale` |
| `Key data assets` / `Managed in` column | `classifications[].keyAssets[]` — extract the backticked stable IDs; fall back to splitting on `,` when the cell has none |
| Rows of `## Golden Record Candidates`, joined on `Stable ID` | merged into that concept's `classifications[].goldenRecord` `{recordType, sourceSystems, survivorshipModel, evidence, confidence}` — the key is **absent** for non-golden concepts |
| `Record type` column, taking the word before the parenthesis (`entity (MDM)` → `entity`) | `goldenRecord.recordType` |
| The golden-record row's own `Confidence` | `goldenRecord.confidence` — kept separate, since confidence in the survivorship claim often differs from confidence in the primary classification |
| `## Glossary Suggestions` rows | `glossarySuggestions[]` `{term, definition, avoid, suggestedContext, confidence, status}` — omit `status` when the cell is empty; it defaults to `proposed` |
| `## Open Questions` entries | `openQuestions[]` `{item, evidence, proposedCategory}` |
| `## Unknowns and Gaps` bullets | `unknowns[]` `{item, reason}` |
| `## Classification Summary` table | *not carried* — the counts are derivable from `classifications[]` |

**Every concept appears exactly once** in `classifications[]`, whichever table it came from. A golden-record row never creates a second entry — it attaches to the concept's existing one, which is what makes "cross-cutting flag, not a peer category" true in the data and not just in the prose.

**Stable IDs are the join key**: every `classifications[].stableId` must exist in `context-lineage.json`.

Validate before reporting the stage complete:

```bash
python3 <PLUGIN_ROOT>/scripts/validate_artifact.py \
  --schema <PLUGIN_ROOT>/skills/dama-assessment/assets/dama-assessment.schema.json \
  --data <OUTPUT_REPO>/<repo-slug>/dama-assessment.json
```

## Example row (a fulfillment repo)

```md
## Golden Record Candidates

| Concept | Stable ID | Record type | Source systems reconciled | Survivorship model | Evidence | Confidence |
| --- | --- | --- | --- | --- | --- | --- |
| Shipment weight (sw) | `concept:sw` | measurement (data-quality) | carrier_api + wms (scan_feed) + depot_scanner | pick-best (`int_shipment_weight__scanner_carrier_pick_best`) | `dbt_model:int_shipment_weight__scanner_carrier_pick_best` | High |
| WarehouseLocation | `concept:warehouse-location` | entity (MDM) | crm (crm_warehouse_location) + wms (fulfillment orders) | match on `location_code` / `is_valid_location` | `dbt_model:raw_crm__historical_order_terms` | Medium |
```
