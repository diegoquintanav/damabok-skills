# CONTEXT.md Format

The `domain-business-modeling` skill produces TWO artifacts in `OUTPUT_REPO/<repo-slug>/`:

- **`CONTEXT.md`** — the **editable source of truth**, following the template below.
- **`context.json`** — **generated from the markdown**, validated against
  `assets/context.schema.json`, and consumed by `context-lineage-generator`. Never
  hand-edit the JSON; regenerate it after any markdown change.

## Structure

```md
# {Context Name}

{One or two sentence description of what this context is and why it exists.}

## Language

**Order**:
{A one or two sentence description of the term}
_Avoid_: Purchase, transaction

**Invoice**:
A request for payment sent to a customer after delivery.
_Avoid_: Bill, payment request

**Customer**:
A person or organization that places orders.
_Avoid_: Client, buyer, account

## Unknowns and Gaps

- {Term or question the glossary cannot yet settle, and why.}
```

When terms cluster naturally, replace the flat `## Language` section with thematic `##`
headings (`## Shipping`, `## Billing and rates`, …) holding the same term entries.
Both shapes are valid; `## Unknowns and Gaps` is always last.

## Language

Write the glossary in the language the project's domain is discussed in — a Portuguese
project keeps Portuguese terms, definitions, and a localized avoid marker (`_Evitar_`).
Match whatever an existing `CONTEXT.md` already uses; only the JSON field names are
always English.

## Rules

- **Be opinionated.** When multiple words exist for the same concept, pick the best one and list the others under `_Avoid_`.
- **`_Avoid_` means "don't confuse with", not merely "don't say".** It legitimately holds three different relationships, and downstream stages classify them mechanically rather than guessing — see [`../damabok-shared/AMBIGUITY-GATE.md`](../damabok-shared/AMBIGUITY-GATE.md):

  | Entry | Relationship | Example |
  | --- | --- | --- |
  | is another term in this glossary | a *different* concept you get confused with | `WarehouseLocation` avoids `Order` |
  | is avoided by two or more concepts, and is not a term | **a concept this glossary is missing** | `vendor`, avoided by WarehouseLocation and Order |
  | anything else | a true synonym you rejected | `NetMargin` avoids `profit` |

  You do not label these yourself. Write the words down honestly; the classification falls out of the glossary as it stands.
- **Keep definitions tight.** One or two sentences max. Define what it IS, not what it does.
- **Only include terms specific to this project's context.** General programming concepts (timeouts, error types, utility patterns) don't belong even if the project uses them extensively. Before adding a term, ask: is this a concept unique to this context, or a general programming concept? Only the former belongs.
- **Group terms under subheadings** when natural clusters emerge. If all terms belong to a single cohesive area, a flat list is fine.
- **Record what you could not settle.** Terms that surfaced but resist definition, and questions the gate left unanswered, go under `## Unknowns and Gaps` rather than being dropped or guessed at.

## Interactive gate

**This is the pipeline's only gate.** No other stage asks the user anything, so the 3–5
questions here are the whole run's budget. See
[`../damabok-shared/AMBIGUITY-GATE.md`](../damabok-shared/AMBIGUITY-GATE.md).

Before writing, ask the user to confirm — drawing from this stage's own findings:

- **New or fuzzy terms** — a term about to enter the glossary whose meaning is not yet pinned down, or that overlaps an existing entry.
- **Avoid-list candidates** — a word found in the code or the conversation that names an existing concept but is not its canonical term. "Code calls this `cust_type`; canonical term is `Customer Segment`. Add `cust_type` to its `_Avoid_` list?"
- **Conflicts with the code** — where a proposed definition contradicts what the code actually does.

…and from **candidates the last run recorded downstream**, all of which are proposals to
change this glossary:

| Source | Array | Rows to gate |
| --- | --- | --- |
| `context-lineage.json` | `terminologyDrift[]` | avoided terms found in code |
| `dama-assessment.json` | `glossarySuggestions[]` | terms visible in data assets but missing here |

Take only rows with `status: proposed` or no `status`. Skip `rejected` — those are settled.

### Closing candidates

A gate that only asks is the failure this design exists to fix. After writing `CONTEXT.md`:

| Answer | `CONTEXT.md` | The row that raised it |
| --- | --- | --- |
| Accepted | term or `_Avoid_` entry added, carrying `source` | **dropped** — the glossary is now the record |
| Declined | unchanged | `status: rejected`, kept forever, never re-asked |
| Not asked | unchanged | left `proposed`, returns next run |

Edit the raising stage's markdown and regenerate its JSON; never patch the JSON directly.

**An accepted term carries `source` in `context.json`**, naming the artifact and candidate
it came from — `"dama-assessment.json glossarySuggestions: Fulfillment Center"`. Dropping the
row makes the glossary the single record of the *term*; without `source` it also destroys
the record of where the term came from, which is not the duplication that rule was avoiding.
Terms derived directly from the analyzed repository omit the key.

Unresolved items go to `## Unknowns and Gaps`.

## Derivation rules (markdown → JSON)

| Markdown | JSON |
| --- | --- |
| `# {Context Name}` | `contextName` |
| Paragraph under the H1 | `contextDescription` |
| Analyzed repo's directory basename | `sourceRepo` |
| Each `**{Term}**:` entry | one item in `terms[]` |
| The term text, verbatim including any parenthetical short code | `terms[].term` |
| Slug of the term's short code when present, else a kebab/snake slug of the term | `terms[].stableId`, prefixed `concept:` — see the slug rules below |
| The line(s) following the term | `terms[].definition` |
| `_Avoid_:` / `_Evita_:` line, split on `,`, trimmed | `terms[].avoid[]` — omit the key when the line is absent |
| The `##` thematic heading the term sits under (not `## Language`) | `terms[].group` — omit the key for ungrouped glossaries |
| `## Unknowns and Gaps` bullets | `unknowns[]` `{item, reason}` |

### Slug rules

The ID must match `^concept:[a-z0-9_-]+$`, so it is always lowercase ASCII.

1. **A parenthetical that is a short code becomes the slug.** `**Shipment weight (sw)**` → `concept:sw`.
2. **A parenthetical that is a synonym does not.** `**Order (confirmation number)**` → `concept:order`, not `concept:confirmation-number`. The test: a short code is an identifier that appears in the code (a column, a variable); a synonym is another word for the same thing. When unsure, ask in the gate rather than guessing — this decision is hard to reverse.
3. **Otherwise kebab-case the term**, lowercased, accents stripped to ASCII: `**Cost ledger**` → `concept:cost-ledger`.
4. **Drop elided articles rather than stranding them.** `**Coût d'entrepôt**` → `concept:cout-entrepot`, never `cout-d-entrepot`.
5. **Connector words (`de`, `per`, `a`) may be kept or dropped**, but never re-decided later. An existing glossary is authoritative: if it already has `concept:categorie-de-clients` alongside `concept:temps-livraison`, preserve that inconsistency rather than normalizing it.

**Stable IDs are the join key** for every downstream stage: `concept:sw` in
`context.json` is the same concept as `concept:sw` in `context-lineage.json` and
`dama-assessment.json`. Once assigned, a stable ID does not change even if the display
term is reworded — renaming one silently breaks the chain.

**When regenerating over an existing glossary, read the downstream artifacts' IDs first and reuse them verbatim.** Re-deriving a slug from the markdown alone can land on a different-but-defensible form and quietly sever the chain; the existing ID always wins over the rule that would have produced it.

This stage has no `generatedFrom` field. It is the first stage, derived from a repository rather than from an upstream artifact — `sourceRepo` carries the provenance instead.

Validate before reporting the stage complete:

```bash
python3 <PLUGIN_ROOT>/scripts/validate_artifact.py \
  --schema <PLUGIN_ROOT>/skills/domain-business-modeling/assets/context.schema.json \
  --data <OUTPUT_REPO>/<repo-slug>/context.json
```

## Single vs multi-context repos

Paths below are relative to the glossary's home — `<OUTPUT_REPO>/<repo-slug>/` in pipeline runs, the working repo's root in session mode. In a pipeline run, the sub-paths in a context map (`./src/ordering/`) refer to locations in the *analyzed* repo; the `CONTEXT.md` files themselves still live in the output repo, mirroring that structure.

**Single context (most repos):** One `CONTEXT.md`.

**Multiple contexts:** A `CONTEXT-MAP.md` alongside it lists the contexts, where they live, and how they relate to each other:

```md
# Context Map

## Contexts

- [Ordering](./src/ordering/CONTEXT.md) — receives and tracks customer orders
- [Billing](./src/billing/CONTEXT.md) — generates invoices and processes payments
- [Fulfillment](./src/fulfillment/CONTEXT.md) — manages warehouse picking and shipping

## Relationships

- **Ordering → Fulfillment**: Ordering emits `OrderPlaced` events; Fulfillment consumes them to start picking
- **Fulfillment → Billing**: Fulfillment emits `ShipmentDispatched` events; Billing consumes them to generate invoices
- **Ordering ↔ Billing**: Shared types for `CustomerId` and `Money`
```

The skill infers which structure applies:

- If `CONTEXT-MAP.md` exists, read it to find contexts
- If only a single `CONTEXT.md` exists, single context
- If neither exists, create `CONTEXT.md` lazily when the first term is resolved

When multiple contexts exist, infer which one the current topic relates to. If unclear, ask.
