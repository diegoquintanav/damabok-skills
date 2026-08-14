# CONTEXT_LINEAGE.md Format

The `context-lineage-generator` skill produces TWO artifacts in `OUTPUT_REPO/<repo-slug>/`, next to `CONTEXT.md`:

- **`CONTEXT_LINEAGE.md`** — the **editable source of truth**, following the template below. Content between the auto markers is generated; everything below `## Manual Notes` is preserved.
- **`context-lineage.json`** — **generated from the markdown**, validated against `assets/context-lineage.schema.json`, and consumed by `dama-assessment` and `openmetadata-mapper`. Never hand-edit the JSON; regenerate it after any markdown change.

## Template

```md
# Context Lineage

> Generated from `CONTEXT.md` by the `context-lineage-generator` skill.

<!-- context-lineage:auto:start -->
## Concepts

| Concept | Stable ID | Data I/O points | Other mentions |
| --- | --- | --- | --- |

## Concept Details

### {Concept}

**Definition**: {quoted from CONTEXT.md}

**Data read/write points**:

| Stable ID | Location | Kind | Direction | Evidence | Confidence |
| --- | --- | --- | --- | --- | --- |

**Other mentions**:

| Stable ID | Location | Kind | Confidence |
| --- | --- | --- | --- |

## Data I/O Summary

| Asset | Kind | Concepts consumed | Concepts produced |
| --- | --- | --- | --- |

## Terminology Drift

| Avoided term | Concept | Location | Suggested action | Status |
| --- | --- | --- | --- | --- |

## Unknowns and Gaps

## Refresh
<!-- context-lineage:auto:end -->

## Manual Notes
```

## Stable IDs

Reuse the sibling lineage prefixes so files compare across repos: `concept:`, `table:`, `dbt_source:`, `dbt_model:`, `snapshot:`, `exposure:`, `column:`, `dag:`, `script:`, `api:`, `file:`, `ci:`, `env:`, `secret:`.

Concept slugs: use the explicit identifier when present (`concept:sw`, `concept:order`), otherwise kebab-case the canonical term (`concept:carrier-surcharge`). With `CONTEXT-MAP.md`, prefix with the context slug (`concept:fulfillment:sw`).

## Values

- **Direction**: `consumes`, `produces`, `transforms`.
- **Kind**: `dbt_source`, `dbt_model`, `snapshot`, `table`, `view`, `column`, `exposure`, `dag`, `script`, `api`, `file`, `ci`, `env`, `secret`.
- **Confidence**: `High` — identifier match inside a data definition (SQL column, schema YAML entry, DAG operator); `Medium` — fuzzy, name-only, or variant match; `Low` — docs, comments, or indirect references.
- **Evidence**: compact file path plus symbol, line, or command. Never secret values.

## Classifying mentions

- **Data I/O point** — the location reads, writes, or transforms stored data: SQL models/sources/snapshots, schema YAML column entries, DAG operators, scripts with DB/file/API I/O, CI deploy jobs, env/secret references consumed by data processes.
- **Other mention** — docs, tests, comments, ad-hoc analysis SQL that does not persist, prose in YAML descriptions.

## Rules

- Omit tables with no rows instead of leaving them blank.
- Keep one `### {Concept}` section per concept, ordered as in `CONTEXT.md`.
- Preserve manual notes below the auto markers verbatim.
- List every concept from `CONTEXT.md` in the Concepts table, even those with zero hits (they belong in Unknowns and Gaps).

## Vocabulary candidates

**This stage asks the user nothing.** It records what it is unsure about and lets the
right reader settle it. See [`../damabok-shared/AMBIGUITY-GATE.md`](../damabok-shared/AMBIGUITY-GATE.md).

- **Avoided terms found in code** → a `proposed` row in `## Terminology Drift`, with the
  file location as evidence. This is the observation that keeps `CONTEXT.md` from falling
  behind the codebase, but the ruling belongs to `domain-business-modeling`, which owns
  the glossary — so it is recorded here and asked there, on the next run.
- **`Low`-confidence data points** → written as lineage, marked `Low`, with the evidence
  that makes them weak. The user judges them in the preview, where the evidence is
  visible; a yes/no question stripped of that context is a worse review.
- **Concepts with zero data I/O points** → `## Unknowns and Gaps`, stating whether you
  believe the concept genuinely absent from the data layer or the search a miss.

### Status column

`proposed` (or empty) means nobody has ruled on it. `rejected` means the user declined it
at a previous gate — **carry those rows forward verbatim and never re-raise them.** An
accepted candidate does not appear here at all: it has been written into `CONTEXT.md`, so
the glossary is its record and the row is simply gone.

## Derivation rules (markdown → JSON)

| Markdown | JSON |
| --- | --- |
| Analyzed repo's directory basename | `sourceRepo` |
| The input artifact named in the blockquote | `generatedFrom` (normally `"CONTEXT.md"`) |
| Each `### {Concept}` section | one item in `concepts[]` |
| Heading text | `concepts[].concept` |
| Stable ID column from the `## Concepts` table | `concepts[].stableId` |
| `**Data read/write points**` table rows | `concepts[].dataPoints[]` `{stableId, location, kind, direction, evidence, confidence}` — omit the key when the table is absent |
| `**Other mentions**` table rows | `concepts[].otherMentions[]` `{stableId, location, kind, evidence, confidence}` — omit the key when absent |
| `## Terminology Drift` table rows | `terminologyDrift[]` `{avoidedTerm, stableId, location, suggestedAction, status}` — one entry per concept, see below. Omit `status` when the cell is empty; it defaults to `proposed` |
| `## Unknowns and Gaps` bullets | `unknowns[]` `{item, reason}` |
| `**Definition**` line | *not carried* — it already lives in `context.json`; restating it invites drift |
| `## Data I/O Summary` table | *not carried* — it is the inverse index of `concepts[].dataPoints[]`, derivable on demand |

The `## Concepts` summary table is likewise not carried: its counts are `len(dataPoints)` and `len(otherMentions)`.

**A drift row naming several concepts becomes one entry per concept.** An avoided term often shadows more than one concept — `margin` blurs both *NetMargin* and *CostLedger* — so the markdown row lists both. `terminologyDrift[].stableId` is singular, so emit one entry per concept, repeating the term and location. Never drop the second concept to fit the row into one entry.

**Both tables carry `evidence` when the markdown supplies it**, including `**Other mentions**` rows. If a mention is worth citing a line for, that citation survives into the JSON.

**Stable IDs are the join key.** `concepts[].stableId` must match the same concept's `stableId` in `context.json`, and `terminologyDrift[].stableId` must name an existing concept.

Validate before reporting the stage complete:

```bash
python3 <PLUGIN_ROOT>/scripts/validate_artifact.py \
  --schema <PLUGIN_ROOT>/skills/context-lineage-generator/assets/context-lineage.schema.json \
  --data <OUTPUT_REPO>/<repo-slug>/context-lineage.json
```

## Example row (a fulfillment repo)

```md
### Shipment weight (sw)

**Definition**: The shipped weight measured at the fulfillment center, used to allocate certain costs and compute margins.

**Data read/write points**:

| Stable ID | Location | Kind | Direction | Evidence | Confidence |
| --- | --- | --- | --- | --- | --- |
| `column:dm_cost_ledger_monthly.sw` | `dbt_fulfillment/models/fulfillment/marts/dm_cost_ledger_monthly.sql` | column | produces | `sw` column, line 7 | High |
| `dbt_source:dm_shipment_weight__to_ledger` | `dbt_fulfillment/models/fulfillment/raw/raw_wms__shipment_weight_from_scans.sql` | dbt_source | consumes | `source('wms', 'dm_shipment_weight__to_ledger')`, line 5 | High |
```
