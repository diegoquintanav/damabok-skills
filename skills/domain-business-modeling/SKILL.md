---
name: domain-business-modeling
description: "CONTEXT.md, business domain model, business glossary, ubiquitous language, domain terminology, ADR. Build and sharpen a project's business vocabulary and record architectural decisions."
license: Apache-2.0
metadata:
  author: diegoquintanav
  version: "2.0"
---

# Domain Modeling

Actively build and sharpen the project's domain model. This is the *active* discipline — challenging terms, inventing edge-case scenarios, and writing the glossary and decisions down the moment they crystallise. (Merely *reading* `CONTEXT.md` for vocabulary is not this skill — that's a one-line habit any skill can do. This skill is for when you're changing the model, not just consuming it.)

This skill owns `CONTEXT.md`. Every downstream stage reads the vocabulary it produces and none of them may edit it — what they detect they *record*, as candidate rows this skill rules on. **This is the pipeline's only interactive gate**, because this is the only stage that can act on the answer.

## Two modes

**Session mode** — a human is designing, and terms crystallise in conversation. Resolve them as they come up; the conversation *is* the gate.

**Pipeline mode** — the `damabok-orchestrator` invokes this as phase 1. It runs on every pipeline run, in one of two shapes:

| Shape | When | What it does |
| --- | --- | --- |
| **Bootstrap** | no `CONTEXT.md` in the output repo | Read the code, propose the vocabulary, run the gate, write |
| **Reconcile** | `CONTEXT.md` exists | Read the `status: proposed` candidates the last run's downstream stages recorded, run the gate on them, apply what the user accepts |

Reconcile is what closes the loop. Without it a candidate recorded in phase 2 would never be ruled on, and `_Avoid_` would never grow.

The rules below apply to all of them; the gate matters most in pipeline mode, where no human is watching each term go by.

## Artifact location

In pipeline runs, both artifacts live in the **output repo**, never in the analyzed repo:

```
<OUTPUT_REPO>/<repo-slug>/
├── CONTEXT.md      ← editable source of truth
└── context.json    ← generated from it, validated, consumed by context-lineage-generator
```

`<repo-slug>` is the analyzed repository's directory basename. In session mode without an output repo, `CONTEXT.md` sits at the working repo's root as usual.

## Hard Rules

- **Never write to the analyzed repository.** It is read-only input. Every artifact goes to `<OUTPUT_REPO>/<repo-slug>/`.
- **Run the interactive gate before writing.** Batch new/fuzzy terms, avoid-list candidates, code conflicts, **and every `status: proposed` candidate recorded by the last run's downstream stages** into 3–5 focused questions, then write. Those 3–5 are the whole run's budget — no other stage asks anything. See [`../damabok-shared/AMBIGUITY-GATE.md`](../damabok-shared/AMBIGUITY-GATE.md).
- **Ask about avoid-list candidates explicitly.** A word that names a known concept but isn't its canonical term is a question, not a silent omission.
- **Close every candidate you raise.** An accepted candidate is written into `CONTEXT.md` and its row is dropped from the artifact that raised it. A declined one is marked `rejected` there, so it is never asked again. One left unasked keeps `proposed` and returns next run. Nothing is reported as prose and forgotten.
- **`CONTEXT.md` is a glossary and nothing else** — no implementation details, no specs, no scratch notes.
- **Only terms specific to this domain.** General programming concepts don't belong, however heavily the project uses them.
- **Record what you could not settle** under `## Unknowns and Gaps`. Never guess a definition to avoid an empty line.
- **Regenerate `context.json` from the markdown** after any change, and validate it. A validation failure is fixed in the markdown, never patched into the JSON.

## Decision Gates

| Signal | Action |
| --- | --- |
| `CONTEXT.md` exists in `<OUTPUT_REPO>/<repo-slug>/` | Read it; extend it. It is the source of truth. In pipeline mode, also **reconcile**: load pending candidates and gate them. |
| `CONTEXT.md` absent there, but present at the analyzed repo's root | **Legacy seed** from the pre-pipeline experiment: read it, propose migrating its content into `<OUTPUT_REPO>/<repo-slug>/CONTEXT.md`, and confirm with the user before writing. Never write back to the analyzed repo, and never delete the original. |
| Neither exists | Bootstrap: derive candidate terms from the code, then run the gate before writing. |
| `CONTEXT-MAP.md` exists | Multi-context repo — resolve which context the work belongs to; ask if unclear. |
| A term conflicts with an existing entry | Gate question — do not silently overwrite the existing definition. |
| A non-canonical wording found in code or conversation | Gate question: add it to that term's `_Avoid_` list? |
| A downstream stage recorded a candidate | Every `status: proposed` row in `context-lineage.json` `terminologyDrift[]` and `dama-assessment.json` `glossarySuggestions[]`, and every missing-concept candidate in `OPENMETADATA_MAPPING.json` `unknownMappings[]`, is gate input. A proposal to change the glossary, never an automatic edit. |
| A candidate is already `status: rejected` | Settled. Do not ask about it, do not apply it, do not remove it. |
| A word is in the `_Avoid_` list of two or more concepts and is not itself a term | **The glossary is missing a concept.** Rank it above ordinary drift: every downstream stage has been working around a hole. Ask for a definition, not for permission to avoid it. |
| Decision is hard to reverse, surprising, and a real trade-off | Offer an ADR (all three must hold). |

## During the session

### Challenge against the glossary

When the user uses a term that conflicts with the existing language in `CONTEXT.md`, call it out immediately. "Your glossary defines 'cancellation' as X, but you seem to mean Y — which is it?"

### Sharpen fuzzy language

When the user uses vague or overloaded terms, propose a precise canonical term. "You're saying 'account' — do you mean the Customer or the User? Those are different things."

### Discuss concrete scenarios

When domain relationships are being discussed, stress-test them with specific scenarios. Invent scenarios that probe edge cases and force the user to be precise about the boundaries between concepts.

### Cross-reference with code

When the user states how something works, check whether the code agrees. If you find a contradiction, surface it: "Your code cancels entire Orders, but you just said partial cancellation is possible — which is right?"

### Update CONTEXT.md inline

When a term is resolved, update `CONTEXT.md` right there. Don't batch resolved terms up — capture them as they happen. Use the format in [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md).

**Gate trigger:** resolving terms one at a time is right while the answer is already in the conversation. The moment **two or more** terms are pending and *unresolved* — ambiguous, conflicting, or avoid-list candidates — stop resolving them singly and ask as one batch per [`../damabok-shared/AMBIGUITY-GATE.md`](../damabok-shared/AMBIGUITY-GATE.md). In pipeline mode nothing is pre-resolved, so the gate always runs before the first write.

### Offer ADRs sparingly

Only offer to create an ADR when all three are true:

1. **Hard to reverse** — the cost of changing your mind later is meaningful
2. **Surprising without context** — a future reader will wonder "why did they do it this way?"
3. **The result of a real trade-off** — there were genuine alternatives and you picked one for specific reasons

If any of the three is missing, skip the ADR. Use the format in [ADR-FORMAT.md](./ADR-FORMAT.md).

## Execution Steps (pipeline mode)

1. Resolve `<repo-slug>` and locate any existing `CONTEXT.md` per the decision gates above.
2. **Load pending candidates** from the previous run, if the artifacts exist in `<OUTPUT_REPO>/<repo-slug>/`: every `status: proposed` entry in `context-lineage.json` `terminologyDrift[]` and `dama-assessment.json` `glossarySuggestions[]`, plus any missing-concept candidate in `OPENMETADATA_MAPPING.json` `unknownMappings[]`. Skip anything already `rejected`. On a bootstrap run there are none — that is expected, not an error.
3. Bootstrap only: inspect the analyzed repo for domain vocabulary — dbt model and column names, source YAMLs, DAG and script names, docs, README. Prefer words the business uses over words the schema uses. Draft candidate terms with one/two-sentence definitions, grouping them thematically when clusters emerge.
4. Pool the gate candidates: this stage's own (fuzzy terms, overlaps, non-canonical wordings found in code, contradictions with the code) plus the pending ones from step 2. Rank by downstream blast radius.
5. **Run the interactive gate** — 3–5 focused questions in one batch. This is the entire run's budget.
6. Write `CONTEXT.md`, applying what the user accepted and routing unresolved items to `## Unknowns and Gaps`.
7. **Close the candidates you asked about**, in the artifact that raised each one: drop accepted rows (the glossary now records them), and set `status: rejected` on declined ones. Fix the markdown and regenerate that stage's JSON — never patch the JSON directly. Candidates you did not ask about keep `proposed` and stay put.
8. Generate `context.json` from the markdown per the derivation rules, then validate:

   ```bash
   python3 <PLUGIN_ROOT>/scripts/validate_artifact.py \
     --schema <PLUGIN_ROOT>/skills/domain-business-modeling/assets/context.schema.json \
     --data <OUTPUT_REPO>/<repo-slug>/context.json
   ```

9. Report: artifact paths, term count, validation PASS/FAIL, gate answers applied, candidates retired and rejected, unresolved items.

## Output Contract

Return:

- Whether this was preview or write mode.
- Files created or modified (always under `<OUTPUT_REPO>/<repo-slug>/`).
- Term count, and how many carry `_Avoid_` entries.
- Schema validation PASS/FAIL.
- Gate questions asked and how they were answered.
- Candidates closed: how many applied to `CONTEXT.md` and dropped, how many marked `rejected`, and which artifacts were regenerated as a result.
- Candidates still `proposed`, carried to the next run.
- Unresolved items needing human follow-up.

## References

- [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md) — the `CONTEXT.md` template, interactive gate, and markdown→JSON derivation rules.
- [ADR-FORMAT.md](./ADR-FORMAT.md) — ADR template and numbering.
- [`assets/context.schema.json`](./assets/context.schema.json) — the contract `context.json` must satisfy.
- [`../damabok-shared/AMBIGUITY-GATE.md`](../damabok-shared/AMBIGUITY-GATE.md) — how the pipeline handles uncertainty: which stage asks, and where every other stage records.
- [`../damabok-shared/SCHEMA-CONVENTIONS.md`](../damabok-shared/SCHEMA-CONVENTIONS.md) — shared JSON contract rules.
- [`../context-lineage-generator/SKILL.md`](../context-lineage-generator/SKILL.md) — consumes `context.json`; reports terminology drift back here.
