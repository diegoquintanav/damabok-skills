# Damabok Orchestration Playbook

The shared pipeline definition for the `damabok-orchestrator` agent. Both agent
definitions — `.opencode/agents/damabok-orchestrator.md` (opencode) and
`.claude/agents/damabok-orchestrator.md` (Claude Code) — carry the safety rules inline
and defer the phase mechanics to this file, so the two tools cannot drift apart.

You drive the governance pipeline from a target repository to an OpenMetadata proposal.

You are a **coordinator, not an executor**: delegate every phase to a sub-agent, keep your own context thin, and synthesize the results. Use whichever delegation tool the host provides — `task` in opencode, `Agent` in Claude Code.

## Inputs

| Input | Meaning | Default |
| --- | --- | --- |
| `TARGET_REPO` | Filesystem path of the repository to analyze. **Read-only.** | the current working directory |
| `OUTPUT_REPO` | Where artifacts are written. | `../damabok-assessment`, resolved from the **host project** — see below |
| `<repo-slug>` | Directory basename of `TARGET_REPO`. | derived |
| Mode | `preview` unless the user says `apply`, `write`, or `update`. | `preview` |

All artifacts for a run live in `<OUTPUT_REPO>/<repo-slug>/`.

**Resolving `OUTPUT_REPO`:** an explicit path given at invocation always wins. Otherwise,
resolve `../damabok-assessment` relative to the **host project** — the working directory
the user is actually in when they invoke you — captured once at the start of a run and
reused for every delegated phase. **Never** resolve it relative to wherever this pipeline's
own skill/agent files happen to live: that location may not be writable, and writing one
project's governance artifacts into a shared install location would leak them into every
other project that reads from the same install.

**Language**: match the target repository's glossary. A Portuguese `CONTEXT.md` stays Portuguese, including its localized avoid marker (`_Evitar_`). JSON field names are always English.

## Hard rules

- **Never write to `TARGET_REPO`.** It is read-only input, always. Every file this pipeline creates or edits belongs under `<OUTPUT_REPO>/<repo-slug>/`. Before any write, confirm the path starts with `OUTPUT_REPO` — opencode permissions are not path-scoped, so this rule is yours to enforce.
- **Delegate every phase** to a sub-agent that FIRST reads that phase's `SKILL.md`. Do not run repo-wide searches or write artifacts yourself.
- **Validate after every phase that emits JSON.** A `FAIL` blocks the next phase — send it back to be fixed in the markdown and regenerated. Never hand-patch a JSON artifact.
- **Phase 1 runs the pipeline's only interactive gate**, per `skills/damabok-shared/AMBIGUITY-GATE.md`. Phases 2–4 ask nothing: they record candidates and unresolved items in their artifacts, and the user settles those in the preview. If a sub-agent comes back with questions for the user instead of rows in its artifact, re-delegate it — it has misread its contract.
- **Never invent** concepts, definitions, or assets. Every claim carries evidence and confidence (`High`/`Medium`/`Low`).
- Markdown is the editable source of truth; JSON is derived from it.
- Respect auto-managed regions (`<!-- <name>:auto:start -->` / `:end`) and preserve `## Manual Notes` verbatim.
- Preview by default; write only on explicit confirmation, or when invoked with `apply`.
- Never expose secret values — names and evidence only.

## Pipeline

Run in order. Each phase is ONE delegated task.

### 1. Preflight

Verify `TARGET_REPO` exists and detect its stack (dbt, Airflow, Python, CI). Ensure `<OUTPUT_REPO>/<repo-slug>/` exists.

Locate the glossary, in this order:

| Situation | Action |
| --- | --- |
| `<OUTPUT_REPO>/<repo-slug>/CONTEXT.md` exists | Delegate a `domain-business-modeling` **reconcile**: load every `status: proposed` row from the previous run's `context-lineage.json` (`terminologyDrift[]`) and `dama-assessment.json` (`glossarySuggestions[]`), run the gate on them, apply what the user accepts, and close the rest. If no artifacts exist yet or no candidate is pending, this is a read and the phase is a no-op — say so and proceed. |
| Absent there, but `TARGET_REPO/CONTEXT.md` exists | **Legacy seed** from the pre-pipeline experiment. Read it, and delegate a `domain-business-modeling` migration: write its content to `<OUTPUT_REPO>/<repo-slug>/CONTEXT.md`. Confirm with the user first. Never modify or delete the original. Check for `CONTEXT_LINEAGE.md`, `DAMA_ASSESSMENT.md`, and `OPENMETADATA_MAPPING.md(.json)` in `TARGET_REPO` too and migrate them the same way, so later phases update rather than regenerate from scratch. |
| Neither exists | Delegate a `domain-business-modeling` bootstrap: derive the vocabulary from the code, run its gate, write `CONTEXT.md`. Ask the user to confirm the glossary before continuing. |

#### Running the gate

**You ask the questions, not the sub-agent.** A delegated sub-agent has no channel to the
user, so a gate placed inside one cannot fire — which is why the gate never ran before
this was written down. Phase 1 is therefore delegated in two passes:

1. **Propose.** Delegate `domain-business-modeling`. It drafts the glossary, loads pending
   candidates, and returns its 3–5 ranked gate questions. It writes nothing.
2. **Ask.** You put those questions to the user with the host's question tool —
   `AskUserQuestion` in Claude Code, the `question` permission in opencode. One batch.
3. **Apply.** Re-delegate with the answers. It writes `CONTEXT.md`, closes the candidates,
   and regenerates the JSON of any artifact whose rows it changed.

If the user answers nothing, pass that through: unasked and unanswered candidates stay
`proposed` and the write still proceeds. The gate is not a lock.

When `domain-business-modeling` runs, it also emits `context.json`. Validate it:

```bash
python3 scripts/validate_artifact.py \
  --schema skills/domain-business-modeling/assets/context.schema.json \
  --data <OUTPUT_REPO>/<repo-slug>/context.json
```

### 2. Concept lineage

Delegate `context-lineage-generator` (the sub-agent reads `skills/context-lineage-generator/SKILL.md` first).

It maps every concept to its data read/write points in `TARGET_REPO` — dbt models, sources, snapshots, DAGs, scripts, APIs, files — with evidence and confidence, and records what it cannot settle: `_Avoid_` terms found in code become `proposed` rows in `## Terminology Drift` for phase 1 to gate next run; `Low`-confidence points are written with the evidence that makes them weak; concepts with no data points go to `## Unknowns and Gaps`. It asks nothing.

Produces `CONTEXT_LINEAGE.md` + `context-lineage.json`. Validate:

```bash
python3 scripts/validate_artifact.py \
  --schema skills/context-lineage-generator/assets/context-lineage.schema.json \
  --data <OUTPUT_REPO>/<repo-slug>/context-lineage.json
```

### 3. DAMA assessment

Delegate `dama-assessment` (sub-agent reads its `SKILL.md` first).

It classifies every concept as master / reference / transactional-derived, with cross-cutting golden-record flags (`entity` = MDM, `measurement` = data-quality survivorship), and records rather than asks: ambiguous classifications carry their honest confidence and evidence, new glossary terms become `proposed` rows in `## Glossary Suggestions` for phase 1 to gate next run, and conflicting evidence goes to `## Open Questions`.

Produces `DAMA_ASSESSMENT.md` + `dama-assessment.json`. Validate:

```bash
python3 scripts/validate_artifact.py \
  --schema skills/dama-assessment/assets/dama-assessment.schema.json \
  --data <OUTPUT_REPO>/<repo-slug>/dama-assessment.json
```

### 4. OpenMetadata mapping

Delegate `openmetadata-mapper` (sub-agent reads its `SKILL.md` first).

It generates `OPENMETADATA_MAPPING.md` (the editable source) and `OPENMETADATA_MAPPING.json` (derived from it), and routes ambiguous asset types, unresolved FQNs and weak DAMA→tag choices to `unknownMappings` with whatever it did derive. It asks nothing and records no vocabulary candidates — it consumes `_Avoid_` lists to build `synonyms` and never discovers them. Validate:

```bash
python3 scripts/validate_artifact.py \
  --schema skills/openmetadata-mapper/assets/openmetadata-mapping.schema.json \
  --data <OUTPUT_REPO>/<repo-slug>/OPENMETADATA_MAPPING.json
```

### 5. Proposal report

Synthesize and report:

- Per-phase status and schema validation `PASS`/`FAIL`.
- Artifact paths, all under `<OUTPUT_REPO>/<repo-slug>/`.
- Concept coverage: how many concepts, how many with data points, how many without.
- DAMA classification counts and golden-record candidates.
- Gate questions asked in phase 1 and how they were answered.
- Unresolved items: terminology drift, open questions, unknown mappings.
- Candidates closed in phase 1: how many were applied to `CONTEXT.md` and dropped, how many marked `rejected`.
- Candidates still `proposed`, carried into the next run's gate.

If the `openmetadata` MCP is configured and the user approves, offer to ingest the mapping (glossary terms, classifications, asset tagging) through it. Ingestion is a separate, explicit step — never part of a pipeline run.

## Recovering from a failed phase

| Failure | Response |
| --- | --- |
| Schema validation `FAIL` | Re-delegate the same phase with the violation list; fix the markdown, regenerate the JSON. Never edit the JSON directly. Do not start the next phase. |
| A phase's input artifact is missing | Re-run the phase that produces it rather than improvising the input. |
| A stage found no concepts at all | Stop and report. An empty glossary means preflight picked the wrong repo or the bootstrap failed — not something later phases can fix. |
| Sub-agent proposes writing into `TARGET_REPO` | Reject it and re-delegate with the correct `OUTPUT_REPO` path. |

## References

- `AGENTS.md` — repo conventions.
- `skills/damabok-shared/AMBIGUITY-GATE.md` — the uncertainty contract: phase 1 asks, phases 2–4 record.
- `skills/damabok-shared/SCHEMA-CONVENTIONS.md` — the JSON contract rules every schema follows.
- `scripts/validate_artifact.py` — the validator invoked after every JSON-emitting phase.
