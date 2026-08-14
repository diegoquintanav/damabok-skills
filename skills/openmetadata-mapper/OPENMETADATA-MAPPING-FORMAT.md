# OpenMetadata Mapping Format

The `openmetadata-mapper` skill produces TWO artifacts in `OUTPUT_REPO/<repo-slug>/`:

- **`OPENMETADATA_MAPPING.md`** — the **editable source of truth**, following the template below (domain-business-modeling pattern: auto-managed region + `## Manual Notes`). Edit this file to adjust the mapping.
- **`OPENMETADATA_MAPPING.json`** — **generated from the markdown**, shaped like OpenMetadata v1.12 API create requests so an OpenMetadata MCP server can consume it. Never hand-edit the JSON; regenerate it after any markdown change.

## Markdown source template

```md
# OpenMetadata Mapping

> Source file for `OPENMETADATA_MAPPING.json`. Edit this file, then regenerate the JSON with the `openmetadata-mapper` skill.

<!-- openmetadata-mapping:auto:start -->
## Glossary

- **Name**: `OrderFulfillment`
- **Display name**: Order Fulfillment
- **Description**: Domain vocabulary for order fulfillment and shipping cost tracking.

## Terms

### sw

- **Display name**: Shipment weight
- **Description**: The shipped weight measured at the fulfillment center, used to allocate certain costs and compute margins.
- **Synonyms**: base weight; billed weight
- **Related terms**: `broader OrderFulfillment.Weight`; `relatedTo OrderFulfillment.gw`
- **Tags**: `DAMA.GoldenRecordMeasurement`

### warehouse-location

- **Display name**: WarehouseLocation
- **Description**: The stable identifier for a fulfillment location used across systems...
- **Synonyms**: order; vendor
- **Tags**: `DAMA.MasterData`; `DAMA.GoldenRecordEntity`

## Classifications

### DAMA

- **Display name**: DAMA-DMBOK
- **Description**: DAMA-DMBOK categories assigned by the dama-assessment skill.
- **Tags**:
  - `MasterData`: Core entity with stable identity shared across processes.
  - `ReferenceData`: Code list or categorization values.
  - `TransactionalDerived`: Computed from other concepts.
  - `GoldenRecordEntity`: Master entity reconciled across sources (MDM).
  - `GoldenRecordMeasurement`: Transactional data reconciled across sources (data-quality survivorship).

## Asset Mappings

| Term FQN | Type | Name | FQN | Role | Evidence |
| --- | --- | --- | --- | --- | --- |
| OrderFulfillment.sw | column | sw | [SERVICE].dbt_fulfillment_prod.dm_cost_ledger_monthly.sw | produces | CONTEXT_LINEAGE.md line 183 |
| OrderFulfillment.sw | table | raw_wms__shipment_weight_from_scans | [SERVICE].dbt_fulfillment_prod.raw_wms__shipment_weight_from_scans | transforms | CONTEXT_LINEAGE.md line 186 |

## Unknown Mappings

| Type | Reference | Role | Notes |
| --- | --- | --- | --- |
| summary | [SERVICE] | — | Service name placeholder applies to all FQNs; resolve in the MCP layer. |
| macro | margin_per_shipment_macro | transforms | dbt macro, not a materialized table. |
<!-- openmetadata-mapping:auto:end -->

## Manual Notes
```

## Unresolved mappings

**This stage asks the user nothing, and records no vocabulary candidates.** See
[`../damabok-shared/AMBIGUITY-GATE.md`](../damabok-shared/AMBIGUITY-GATE.md).

- **Ambiguous asset type or unresolved FQN** — where an asset could be a `table` or a
  `column`, or the schema/table part of an FQN is genuinely uncertain — goes to
  `## Unknown Mappings` with everything you *did* derive. Never guess an FQN.
- **DAMA category → tag choices** resting on `Low`/`Medium` upstream confidence: attach
  the tag, and note the confidence in `## Unknown Mappings` so the preview shows what it
  rests on.
- **Synonym candidates are not this stage's to raise.** `synonyms` are built *from* the
  `_Avoid_` lists already in `CONTEXT.md`; this stage consumes vocabulary and never
  discovers it. `context-lineage-generator` searches the same repository with the same
  tokens and has the file evidence, so a candidate worth raising is raised there.

The `[SERVICE]` placeholder is likewise not a question — the OpenMetadata service name is
deployment configuration resolved in the MCP layer, not domain knowledge the user should
be asked to supply per run.

## Derivation rules (markdown → JSON)

| Markdown | JSON |
| --- | --- |
| Analyzed repo's directory basename | `sourceRepo` |
| The input artifacts named in the blockquote | `generatedFrom` (normally `"CONTEXT_LINEAGE.md"`), and `damaInput` when DAMA was used |
| Glossary `Name` / `Display name` / `Description` | `glossaries[0]` (`name`, `displayName`, `description`) |
| Each `### {name}` under `## Terms` | one term in `glossaries[0].terms[]`: `name` = heading, `displayName` = Display name, `description` = Description |
| The upstream concept's stable ID | `terms[].stableId` — the join key back to `context-lineage.json` |
| `Synonyms` (split on `;`, trim) | `synonyms[]` — omit the key when the line is absent |
| `Related terms` (split on `;`; each `relationType FQN` split on first space) | `relatedTerms[]` `{relationType, termFqn}` — omit when absent |
| `Tags` (split on `;`) | `tags[]` — omit when absent |
| Each `### {name}` under `## Classifications`, with `Tags` list `- `{tag}`: {description}` | one entry in `classifications[]`; each tag → `{name, description}` |
| `Asset Mappings` table rows | `termAssetMappings[]` grouped by `Term FQN`; each row → `assets[]` `{type, name, fullyQualifiedName, role, evidence}` |
| `Unknown Mappings` table rows | `unknownMappings[]` `{type, reference, role, notes}` |

**Omit optional keys rather than emitting empty arrays.** A term with no synonyms has no `synonyms` key at all — not `"synonyms": []`. The same goes for `relatedTerms`, `references`, `tags`, and the top-level `classifications`, `termAssetMappings`, and `unknownMappings`.

**`references` is optional and normally omitted.** Populate it only with genuinely useful external links (a spec, a dashboard, an upstream doc). The former practice of stamping every term with a fixed pointer back to `CONTEXT_LINEAGE.md` carried no information — the provenance is already in `generatedFrom`.

## JSON canonical shape (target)

```json
{
  "schemaVersion": "openmetadata-mapping-v1",
  "openMetadataVersion": "1.12",
  "sourceRepo": "acme-fulfillment",
  "generatedFrom": "CONTEXT_LINEAGE.md",
  "damaInput": "DAMA_ASSESSMENT.md",
  "glossaries": [
    {
      "name": "OrderFulfillment",
      "displayName": "Order Fulfillment",
      "description": "Domain vocabulary for order fulfillment and shipping cost tracking.",
      "terms": [
        {
          "name": "sw",
          "displayName": "Shipment weight",
          "description": "The shipped weight measured at the fulfillment center, used to allocate certain costs and compute margins.",
          "stableId": "concept:sw",
          "synonyms": ["base weight", "billed weight"],
          "relatedTerms": [
            { "relationType": "broader", "termFqn": "OrderFulfillment.Weight" },
            { "relationType": "relatedTo", "termFqn": "OrderFulfillment.gw" }
          ],
          "tags": ["DAMA.GoldenRecordMeasurement"]
        },
        {
          "name": "net-margin",
          "displayName": "NetMargin",
          "description": "The difference between revenue and costs considered in a ledger.",
          "stableId": "concept:net-margin"
        }
      ]
    }
  ],
  "classifications": [
    {
      "name": "DAMA",
      "displayName": "DAMA-DMBOK",
      "description": "DAMA-DMBOK categories assigned by the dama-assessment skill.",
      "tags": [
        { "name": "MasterData", "description": "Core entity with stable identity shared across processes." },
        { "name": "ReferenceData", "description": "Code list or categorization values." },
        { "name": "TransactionalDerived", "description": "Computed from other concepts." },
        { "name": "GoldenRecordEntity", "description": "Master entity reconciled across sources (MDM)." },
        { "name": "GoldenRecordMeasurement", "description": "Transactional data reconciled across sources (data-quality survivorship)." }
      ]
    }
  ],
  "termAssetMappings": [
    {
      "termFqn": "OrderFulfillment.sw",
      "assets": [
        {
          "type": "column",
          "name": "sw",
          "fullyQualifiedName": "[SERVICE].dbt_fulfillment_prod.dm_cost_ledger_monthly.sw",
          "role": "produces",
          "evidence": "CONTEXT_LINEAGE.md line 183"
        },
        {
          "type": "table",
          "name": "raw_wms__shipment_weight_from_scans",
          "fullyQualifiedName": "[SERVICE].dbt_fulfillment_prod.raw_wms__shipment_weight_from_scans",
          "role": "transforms",
          "evidence": "CONTEXT_LINEAGE.md line 186"
        }
      ]
    }
  ]
}
```

Note what is absent: `net-margin` carries no `synonyms`, `relatedTerms`, `references` or `tags` keys, and there is no `unknownMappings` key at all. Omission is the correct encoding of "none" — see [`../damabok-shared/SCHEMA-CONVENTIONS.md`](../damabok-shared/SCHEMA-CONVENTIONS.md).

## JSON rules

- **Terms**: `name` is the slug from the concept stable ID (`concept:sw` → `sw`; `concept:order` → `order`). `displayName` is the canonical CONTEXT.md term. `description` quotes the lineage definition verbatim. `stableId` carries the full upstream ID so the mapping can be joined back to the lineage and DAMA artifacts.
- **Synonyms**: `_Avoid_` entries that survive the three-way test below. Never a separate term.
- **relatedTerms**: `broader`/`narrower` for family taxonomies, `relatedTo` for cross-links and for `_Avoid_` disambiguations, `partOf`/`hasPart` for composition, `antonym` for terms defined in opposition to each other. Must reference only existing term FQNs.

### Classifying `_Avoid_` entries

`_Avoid_` means *"don't confuse with"*, and that covers three different relationships.
Emitting all of them as `synonyms` tells the catalogue that two deliberately distinct
concepts are the same word. Test each entry, in this order:

| Test | Relationship | Emit |
| --- | --- | --- |
| The entry **is another glossary term** (compare against every term name and stable ID, ignoring any parenthetical code) | Disambiguation — a different concept, commonly confused | `relatedTerms` with `relatedTo` |
| The entry is **avoided by two or more different concepts**, and is not itself a term | Missing concept — it denotes something real the glossary never defines | Neither. Record it once in `## Unknown Mappings` for `domain-business-modeling` to gate |
| Otherwise | True synonym — the same concept, in wording the project rejected | `synonyms` |

The second test is a frequency check, not a judgement about meaning: if two separate
concepts each need to warn you off a word, the word is very likely its own concept. Do not
try to decide that semantically — count the owners.

Worked examples from a fulfillment repo:

| Entry | Owners | Test result | Emitted as |
| --- | --- | --- | --- |
| `SOUTH` on `NORTH` | 1 | `SOUTH` is a term | `relatedTerms` → `relatedTo` |
| `vendor` on `WarehouseLocation` | 1 | `Order` is a term | `relatedTerms` → `relatedTo` |
| `customer` | 2 (WarehouseLocation, Order) | not a term, 2 owners | omitted → `unknownMappings` |
| `surcharge` | 2 (ServicePlan, RateLock) | not a term, 2 owners | omitted → `unknownMappings` |
| `profit` on `NetMargin` | 1 | not a term, 1 owner | `synonyms` |

- **DAMA tags**: only when `DAMA_ASSESSMENT.md` was an input. Golden record flags are cross-cutting: a term can carry both a primary tag and a golden tag.
- **Asset entityReferences**: types are conservative — `table` (dbt_model / dbt_source / snapshot), `column` (with parent table FQN), `pipeline` (dag / script), `dashboard` (exposure). `role` is the lineage direction: `produces`, `consumes`, `transforms`.
- **FQNs**: use `[SERVICE].<schema>.<table>` / `[SERVICE].<schema>.<table>.<column>` when the OpenMetadata service name is unknown; record those in `unknownMappings`. Never invent a service name.
- **Determinism**: the JSON mirrors the markdown order exactly — terms in heading order, assets in table order. Identical markdown → identical JSON.
- **No secrets**: env/secret names may appear as evidence, never values.

## Schema validation

`OPENMETADATA_MAPPING.json` MUST validate against `assets/openmetadata-mapping.schema.json` (JSON Schema draft-07). The schema is authoritative for shape: required fields, types, `additionalProperties`, enums (`relationType`, asset `type`, `role`), and name patterns. A generated JSON that fails the schema must be fixed in the markdown and regenerated — never patched by hand.

```bash
python3 <PLUGIN_ROOT>/scripts/validate_artifact.py \
  --schema <PLUGIN_ROOT>/skills/openmetadata-mapper/assets/openmetadata-mapping.schema.json \
  --data <OUTPUT_REPO>/<repo-slug>/OPENMETADATA_MAPPING.json
```

## Consumption by an MCP server

Each JSON section maps 1:1 to OpenMetadata v1.12 API requests the MCP can issue:
- `glossaries[].terms[]` → `CreateGlossaryTermRequest` (with `relatedTerms` resolved to term FQNs)
- `classifications[]` → `CreateClassificationRequest`; `classifications[].tags[]` → `CreateTagRequest`
- `termAssetMappings[].assets[]` → entity references for `PUT /api/v1/glossaryTerms/{id}/assets/add` (tagging assets), after `[SERVICE]` placeholders are resolved
