---
status: accepted
---

# One gate, in the stage that owns the glossary

Implemented on the `gate-consolidation` branch.

The gate was specified in all four stages and had never executed. Reviewing why exposed
one mistake with five faces: **it asked questions at a place where the answer could not be
applied.**

Vocabulary answers mutate `CONTEXT.md`, which only `domain-business-modeling` may write.
The old contract said so itself — and still made the term-avoidance question mandatory in
every stage, then routed the answers into a prose report. An approval therefore had
nowhere to be written and returned identically next run, while a *rejection* persisted,
because rejections routed to an unresolved section that existed. The gate remembered the
useless answer and lost the valuable one.

The rule that replaces it: **ask where the answer can be applied.**

- **Kind A**, uncertainty about the asking stage's own artifact, is recorded with evidence
  and honest confidence and settled by the user in the preview. That was already the
  review the preview/apply flow provided, and it shows a row beside its evidence rather
  than as a decontextualized question.
- **Kind B**, vocabulary, becomes a candidate row with a `status`, gated by
  `domain-business-modeling` on the next run.

`status` is `proposed | rejected`, absent meaning `proposed`. **There is deliberately no
`accepted`**: an accepted candidate is written into `CONTEXT.md` and its row disappears,
so the glossary is the record. Storing `accepted` would put one fact in two places and let
them disagree.

*Amended by the first run:* dropping the row makes the glossary the record of the *term*,
but it also destroyed the record of where the term came from. `Fulfillment Center` was
accepted from an English candidate and rewritten twice before it was right, and none of
that was recoverable from the working tree. Terms therefore carry an optional `source`
string naming the artifact and candidate that proposed them, omitted for terms derived
directly from the analyzed repository. This is not the duplication the rule was avoiding —
the definition still lives in exactly one place.

This required a second half that did not exist. Phase 1 read `CONTEXT.md exists → use it,
proceed to phase 2`, making it a no-op on every run after the first — precisely when
candidates are pending. It now reconciles, which is what makes the loop converge: run 1
collects, run 2 applies and retires, the pool shrinks, `_Avoid_` finally grows.

**The orchestrator asks, not the phase sub-agent.** A delegated sub-agent has no channel
to the user; no per-phase agent definition grants one; and the phase agents are spawned by
an agent that is itself a sub-agent. The Claude Code orchestrator agent had said the
orchestrator asks while every `SKILL.md` said the sub-agent does, and the opencode file
said neither — live drift between two hosts whose whole reason for sharing
`ORCHESTRATION.md` is to prevent it. Phase 1 is now explicitly propose / ask / apply.

**Rejected: keeping a gate per stage and adding a run-level budget.** It preserves the
symmetry but not the property that matters. Three of the four stages still could not act
on their own answers, so the storage problem would remain and only the question count
would improve.

**`openmetadata-mapper` loses vocabulary candidates entirely.** It *consumes* `_Avoid_`
lists to build `synonyms` and never discovers them; anything it might notice is already
visible to `context-lineage-generator`, which searches the same repository with the same
tokens and holds the file evidence. A stage that cannot produce better evidence than its
upstream should not raise the question.

Token savings are real but second-order — three stages stop collecting, ranking and
folding in answers. [0003](0003-derivation-into-code.md) is still where the 226k actually
goes. The first-order wins are correctness (approvals now persist) and scale: at ~150
repositories, four gates is 600 human interrupts and one gate is 150, declining per repo
as each glossary settles.
