# Agent Guide

## Orchestrator

- `damabok-orchestrator` is the entry point: it drives the pipeline from a target repository path to an OpenMetadata proposal.
- Usage: `damabok-orchestrator: run the pipeline on <repo-path>` (add `--apply` to skip per-phase confirmations).
- Two distribution channels, kept from drifting apart by hand:

  | Channel | Agent definition | Skills | How it's used |
  | --- | --- | --- | --- |
  | **Claude Code Plugin** (packaged, installable) | `agents/damabok-orchestrator.md` — self-contained, `ORCHESTRATION.md` inlined into its body | `skills/` (plugin root) | `.claude-plugin/plugin.json` + `marketplace.json`; installed via Claude Code's plugin mechanism, at an arbitrary path Claude Code manages. Paths inside the plugin resolve against `PLUGIN_ROOT`, resolved once per run — see the orchestrator's own opening section. |
  | **opencode / direct clone** (unpackaged) | `.opencode/agents/damabok-orchestrator.md` — thin, defers to `ORCHESTRATION.md` | `skills/` (repo-relative — opencode reads it directly; `.claude/skills` is a symlink to the same directory for local Claude Code discovery when working in this repo unpackaged) | Clone or copy this repo; every path is relative to the repo root, exactly as it always has been. No install step, no marketplace. |

- **`ORCHESTRATION.md`** (repo root) is the canonical, maintainer-facing playbook — the source both the opencode orchestrator and this doc describe. `agents/damabok-orchestrator.md` (the packaged version) carries the same content inlined, with plugin-specific path resolution, kept in sync by hand at edit time. Edit `ORCHESTRATION.md` to change pipeline behavior, then port the change into `agents/damabok-orchestrator.md`.
- `opencode.json` and `.mcp.json` each hold the same OpenMetadata MCP configuration, in their host's native format.

## Where artifacts go

**The analyzed repository is never written to.** Every artifact lands in the output repo, one directory per analyzed repo:

```
<OUTPUT_REPO>/<repo-slug>/     default OUTPUT_REPO: ../damabok-assessment
├── CONTEXT.md              + context.json
├── CONTEXT_LINEAGE.md      + context-lineage.json
├── DAMA_ASSESSMENT.md      + dama-assessment.json
└── OPENMETADATA_MAPPING.md + OPENMETADATA_MAPPING.json
```

## Skills

Each phase is executed by a delegated sub-agent that FIRST reads the phase's skill contract:

- `domain-business-modeling` — `skills/domain-business-modeling/SKILL.md` (+ `CONTEXT-FORMAT.md`, `ADR-FORMAT.md`, `assets/context.schema.json`) — owns `CONTEXT.md`; bootstraps the glossary when missing and migrates legacy ones out of analyzed repos.
- `context-lineage-generator` — `skills/context-lineage-generator/SKILL.md` (+ `CONTEXT-LINEAGE-FORMAT.md`, `assets/context-lineage.schema.json`) — produces `CONTEXT_LINEAGE.md` + `context-lineage.json`.
- `dama-assessment` — `skills/dama-assessment/SKILL.md` (+ `DAMA-ASSESSMENT-FORMAT.md`, `assets/dama-assessment.schema.json`) — produces `DAMA_ASSESSMENT.md` + `dama-assessment.json`.
- `openmetadata-mapper` — `skills/openmetadata-mapper/SKILL.md` (+ `OPENMETADATA-MAPPING-FORMAT.md`, `assets/openmetadata-mapping.schema.json`) — produces the editable `OPENMETADATA_MAPPING.md` and the derived `OPENMETADATA_MAPPING.json`.
- `project-lineage-generator` — `skills/project-lineage-generator/SKILL.md` — sibling asset/process lineage (`PROJECT_LINEAGE.md`). Not part of the concept chain; it supplies the shared stable-ID prefixes.

In the packaged plugin, every path above is relative to `PLUGIN_ROOT`, not the repo root.

Shared contracts, referenced by every skill rather than duplicated in each:

- `skills/damabok-shared/AMBIGUITY-GATE.md` — how the pipeline handles uncertainty: which stage asks, and where every other stage records.
- `skills/damabok-shared/SCHEMA-CONVENTIONS.md` — the JSON contract rules.

## Conventions

- **Never write to the analyzed repository.** It is read-only input; artifacts go to `<OUTPUT_REPO>/<repo-slug>/`.
- Markdown artifacts are the editable sources; JSON is always generated from markdown, never hand-edited.
- **Every stage has a companion JSON schema** in its `assets/`. Validate before calling a phase complete:

  ```bash
  python3 scripts/validate_artifact.py --schema <stage-schema.json> --data <artifact.json>
  ```

  (`<PLUGIN_ROOT>/scripts/validate_artifact.py` in the packaged plugin.)

  A `FAIL` is fixed in the markdown and regenerated — never patched into the JSON. A failure blocks the next phase.
- **Only `domain-business-modeling` asks the user anything**, in phase 1: 3–5 focused questions, batched, for the whole run. The orchestrator puts them to the user, since a delegated sub-agent has no channel to one. Every other stage records candidates and unresolved items in its own artifact.
- Only `domain-business-modeling` edits `CONTEXT.md`. Other stages record vocabulary candidates as `proposed` rows; phase 1 gates them on the next run, applies what the user accepts, and marks the rest `rejected` so they are never re-asked.
- Respect auto-managed regions (`<!-- <name>:auto:start/end -->`); preserve `## Manual Notes`.
- Evidence + confidence on every claim; never invent concepts, definitions, or assets.
- Preview by default; write only on explicit confirmation.
- Stable IDs (`concept:sw`) are the join key across all four stages and do not change when a display term is reworded.

## Tools

- `scripts/validate_artifact.py` — stdlib-only validator for the draft-07 subset the schemas use. It rejects unsupported keywords (`$ref`, `oneOf`, `format`, …) rather than ignoring them, so the complexity budget is enforced mechanically.
- `scripts/test_validate_artifact.py` — self-tests: `python3 scripts/test_validate_artifact.py`.
