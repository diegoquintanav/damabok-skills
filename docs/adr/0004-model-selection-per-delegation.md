---
status: proposed
---

# Model selection is passed per delegation

`SKILL.md` has no `model:` field — models attach to agents, not skills. The orchestrator
passes a model with each delegation, rather than defining a subagent per stage.
Per-stage agent files would have to be duplicated across `.opencode/` and `.claude/`,
reintroducing exactly the two-host drift that `ORCHESTRATION.md` exists to prevent, and
the choice is more legible sitting next to the phase it governs.

| Stage | Model | Why |
| --- | --- | --- |
| `domain-business-modeling` | Opus | Only ~27 terms in observed executions, but a naming error propagates into all three downstream stages. Cheapest possible place to spend. |
| `context-lineage-generator` | Sonnet | Largest volume today; still the floor once a deriver lands (see below). |
| `dama-assessment` | Opus | Real DAMA reasoning — master vs reference, entity vs measurement survivorship — over only ~27 rows in observed executions. |
| `openmetadata-mapper` | Sonnet | Mechanical once inputs are fixed; only FQN/type ambiguity needs judgment. |
| `project-lineage-generator` | Haiku | Pure inventory, outside the concept chain. |
| `damabok-orchestrator` | Sonnet | Thin by design: delegation, validation gating, recovery. |

**`context-lineage-generator` does not drop to a cheap model once tool-backed.** The
deriver removes its transcription, which is precisely its *mechanical* half; what remains
is data-I/O-vs-mention classification and confidence. Token count falls while reasoning
density rises. The cheap-model wins are `project-lineage-generator` and the mechanical
half of `openmetadata-mapper`.

*Amended by [0005](0005-single-gate-in-glossary-stage.md):* this entry originally counted
the `_Avoid_`-in-code gate among what remains. That gate has moved to
`domain-business-modeling`, so the margin here is thinner than first stated.
Classification still carries it — deciding whether a hit is a data I/O point or a passing
mention is the judgment the whole artifact rests on — but the case is now one reason
rather than two.
