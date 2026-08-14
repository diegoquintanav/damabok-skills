---
status: accepted
---

# `_Avoid_` is three relationships, and the glossary can tell them apart

Implemented on the `gate-consolidation` branch.

`openmetadata-mapper` mapped every `_Avoid_` entry to `synonyms` unconditionally. Run one
produced, among others:

```
north               synonyms=['SOUTH', 'EAST']
warehouse-location  synonyms=['order', 'customer']
```

NORTH, SOUTH and EAST are the three mutually exclusive warehouse regions; a
WarehouseLocation is a fulfillment site and an order is a shipping agreement. For example,
in an observed execution of the pipeline against a private repository, **26 of 54
`_Avoid_` entries named another glossary term** — more than half the emitted synonyms
asserted that two deliberately distinct concepts were the same word. Ingesting that would
have made the catalogue state the opposite of what the glossary exists to say. The mapping
was unsafe to publish and nobody noticed, because nothing ever compared an `_Avoid_` entry
against the term list.

The root cause is that one field carried three different relationships:

| Relationship | Meaning | Example | Target |
| --- | --- | --- | --- |
| Synonym | same concept, wording we rejected | `profit` → NetMargin | `synonyms` |
| Disambiguation | a *different* concept we get confused with | `order` → WarehouseLocation | `relatedTerms` / `relatedTo` |
| **Missing concept** | names something real the glossary never defines | `customer`, `surcharge` | a gate candidate |

Only the first matches the field's name, which is why the instrument felt like it was
doing more harm than good — it was, for two of its three jobs.

**The glossary can classify them itself**, with no new field and no hand-sorting:

1. The avoided word **is another term** → disambiguation. Emit `relatedTerms`, never
   `synonyms`.
2. The avoided word **is avoided by two or more different concepts**, and is not itself a
   term → **missing concept**. Raise it as a gate candidate.
3. Otherwise → a true synonym. Emit `synonyms`.

Rule 2 is the load-bearing one and it is deliberately a *frequency* test, not a semantic
one: if two separate concepts each need to warn you off a word, the word is almost
certainly its own thing. On this corpus it yields exactly two candidates — `customer`
(avoided by WarehouseLocation and Order) and `surcharge` (avoided by ServicePlan and
RateLock) — and both are demonstrably real. A customer is the party holding an order;
carrier surcharges are regulated charges with dedicated models
(`int_revenue_cost__carrier_surcharge_*`) and their own cost and income lines. Neither is
defined anywhere in `CONTEXT.md`.

**Rejected: splitting `_Avoid_` into two markdown fields.** It reads more clearly, but it
costs a schema change and a one-off hand-classification of all 54 entries, and it would
still not surface the third case. The mechanical test gets the same correctness for free,
in the same style as [0001](0001-stable-id-derivation.md): a presence check against
something already written down, not a judgement about a word's shape.

What `_Avoid_` means is now stated in `CONTEXT-FORMAT.md` — *"don't confuse with"* — which
covers all three cases honestly, where "don't use" only ever covered one.

The wider lesson is the one [0002](0002-schema-gaps-before-deriver.md) already recorded in
a different key: a field with nowhere to put a distinction will silently flatten it. There
the loss was `confidence` on two different claims; here it was three relationships in one
list. Both were invisible until something downstream consumed the flattened value and
produced a confident, wrong answer.
