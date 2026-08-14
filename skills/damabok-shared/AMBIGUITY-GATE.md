# Ambiguity Gate

The shared contract for how every skill in the pipeline handles what it is unsure about.

This file is a reference doc, not a skill. Stages link to it from their `## References`
section and from a Hard Rule.

## The rule that decides everything else

**Ask where the answer can be applied.**

A question is worth asking only at a point where the answer changes a file the asking
stage can write. Asked anywhere else it costs the user an interruption and produces a
value with nowhere to live.

That splits pipeline uncertainty in two:

| Kind | Example | What the answer changes | Who handles it |
| --- | --- | --- | --- |
| **A — artifact uncertainty** | "Is this `Low`-confidence edge a real lineage edge?" | the asking stage's own artifact | recorded, then settled in the preview |
| **B — vocabulary uncertainty** | "The code says `expense`, the glossary says `Costs` — which is right?" | `CONTEXT.md` | recorded as a candidate; `domain-business-modeling` asks next run |

Only `domain-business-modeling` runs an interactive gate, because it is the only stage
that owns the file kind-B answers mutate. Every other stage **records and moves on**.

## Kind A — record it, let the preview settle it

Do not ask. Write the row with its evidence and its honest `Low`/`Medium` confidence, and
route what you could not settle at all to your stage's unresolved section:

| Stage | Section |
| --- | --- |
| `domain-business-modeling` | `## Unknowns and Gaps` in `CONTEXT.md` |
| `context-lineage-generator` | `## Unknowns and Gaps` |
| `dama-assessment` | `## Open Questions` |
| `openmetadata-mapper` | `## Unknown Mappings` |

In the JSON companion these appear in that stage's `unknowns[]` array as `{item, reason}`
— see [SCHEMA-CONVENTIONS.md](./SCHEMA-CONVENTIONS.md).

The run is preview-by-default and the markdown is the editable source of truth, so the
user reads these rows next to their evidence and corrects them in place. That is a better
review than three questions pulled out of context, and it is the review the orchestrator's
preview/apply flow already provides.

## Kind B — record it as a candidate

Two stages genuinely discover vocabulary while working. Each writes its findings into the
section it already has:

| Stage | Section | JSON |
| --- | --- | --- |
| `context-lineage-generator` | `## Terminology Drift` | `terminologyDrift[]` |
| `dama-assessment` | `## Glossary Suggestions` | `glossarySuggestions[]` |
| `openmetadata-mapper` | `## Unknown Mappings` | `unknownMappings[]` — **missing-concept candidates only** |

### Missing-concept candidates

`openmetadata-mapper` raises no vocabulary of its own, but it is the stage that compares
every `_Avoid_` entry against the term list, so it is where one particular gap becomes
visible: **a word avoided by two or more concepts that is not itself a term.** If two
separate concepts each need to warn you off a word, the word is very likely its own
concept, and the glossary has never defined it.

That is a frequency test, not a judgement about meaning — count the owners, don't reason
about the word. It is the only vocabulary candidate this stage records, and it goes in
`## Unknown Mappings` alongside its owning concepts as evidence.

Every candidate row carries a `status`:

| `status` | Meaning | Lifecycle |
| --- | --- | --- |
| `proposed` | Nobody has ruled on it yet. The default when the field is absent. | Offered to the user at the next `domain-business-modeling` gate |
| `rejected` | The user considered it and said no. | Persists; **never re-asked** |

There is deliberately no `accepted`. An accepted candidate is applied to `CONTEXT.md`
immediately and its row disappears on the next regeneration — the glossary itself becomes
the record. Only the negative answer needs storage, because only the negative answer
leaves no other trace.

**`openmetadata-mapper` records no vocabulary candidates except missing concepts.** It
*consumes* `_Avoid_` lists to build `synonyms` and `relatedTerms`; it does not discover
new wordings. Anything of that sort is already visible to `context-lineage-generator`,
which searches the same repository with the same tokens and has the file evidence to
justify the claim. The one exception is the missing-concept test above, which is available
to this stage alone because it is the stage that compares `_Avoid_` against the term list.

## The gate (`domain-business-modeling` only)

1. Build the proposed glossary content in memory.
2. Collect gate candidates from **two** sources:
   - this stage's own findings — new or fuzzy terms, overlaps, contradictions with code;
   - every `status: proposed` row in the previous run's `context-lineage.json`
     (`terminologyDrift[]`) and `dama-assessment.json` (`glossarySuggestions[]`);
   - missing-concept candidates in `OPENMETADATA_MAPPING.json` (`unknownMappings[]`).
     Rank these high: a word two concepts both warn against is a hole in the glossary, and
     every downstream stage has been working around it.
3. **Ask: 3–5 focused questions, one batch.** This is the whole run's budget, not this
   stage's share of it.
4. Write `CONTEXT.md`, applying accepted answers. Mark rejected candidates `rejected` in
   the artifact that raised them. Route the unanswered to `## Unknowns and Gaps`.

Because the gate runs in phase 1, downstream stages in the same run already see the
updated vocabulary.

### Asking about a drift candidate

**The question is almost never "add this word to the `_Avoid_` list?"** On the first real
corpus, 6 of 7 drift candidates were words already in the list — the stage found an
occurrence of a word the glossary had *already* ruled against. The open question there is
about the occurrence, not the list:

| Situation | Wrong question | Right question |
| --- | --- | --- |
| Word already in `_Avoid_`, found in code | "Add `expense` to Costs' `_Avoid_` list?" | "The dashboard section reads `Expenses` while the glossary mandates `Costs` — is the code wrong, or is the glossary?" |
| Word not yet in `_Avoid_` | — | "Code calls this `X`; the canonical term is `Y`. Should `X` be avoided?" |
| Word avoided by two concepts, defined by none | "Add it to both lists?" | "`customer` is avoided by WarehouseLocation and by Order but defined nowhere — what is a customer?" |

Always state which side you believe and why. A drift candidate is a claim that the code
and the glossary disagree; the user's job is to say which one moves, and they can only do
that if you have already worked out what the code actually does.

### Choosing the 3–5

Rank by downstream blast radius. A wrong canonical term propagates into a lineage edge,
then a DAMA classification, then an OpenMetadata glossary term; a missing `_Avoid_` entry
only lets one stray word survive another cycle. Prefer the former. Everything unasked
keeps its `proposed` status and returns next run — nothing is lost by not asking.

## Why this converges

Run 1 collects candidates and asks about the most consequential few. Run 2 applies those
answers to `CONTEXT.md`, retires them, and asks about the next few. Rejected items never
return. The candidate pool shrinks every run, and `_Avoid_` — the project's ledger of
words we deliberately don't use — actually grows.

The previous design asked the same class of question in all four stages and reported the
answers as prose, so an approval had nowhere to be written and came back identically on
the next run. The negative answer persisted; the useful one evaporated.

## Non-goals

- **Do not ask about mechanics.** Formatting, file locations, whether to preview or write
  — those are the skill's job, and the preview/apply flow already covers them.
- **Do not ask the same item twice.** A `rejected` candidate is settled. Re-asking every
  run trains the user to skim, and a skimmed gate is worse than no gate.
- **Do not block on an answer.** An unanswered question stays `proposed` and the write
  proceeds. The gate raises confidence; it is not a lock.
- **Do not exceed the budget to be thorough.** Five good questions get read. Fifteen get
  skipped. At ~150 repositories an unreadable gate is the same as no gate — and costs 150
  interruptions to achieve it.
