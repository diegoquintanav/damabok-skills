---
name: project-lineage-generator
description: "PROJECT_LINEAGE.md, project lineage, repo lineage. Generate per-repo lineage docs for data repos."
license: Apache-2.0
metadata:
  author: diegoquintanav
  version: "1.0"
---

# Project Lineage Generator

## Activation Contract

Use when the user asks to generate, preview, or update `PROJECT_LINEAGE.md`, repo lineage, project intelligence, data lineage, or cross-repo-comparable documentation for the organization's data repositories.

Default to **read-only preview**. Write files only when the user explicitly says `apply`, `write`, `update`, or equivalent.

## Hard Rules

- Analyze only the current repository. Do not crawl sibling repos or infer cross-repo links from local filesystem layout.
- Generate `PROJECT_LINEAGE.md` as the canonical artifact; update `AGENTS.md` only with a short pointer section.
- Use a fixed template across repos so another agent can compare files reliably.
- Preserve manual notes. Only replace content between `<!-- project-lineage:auto:start -->` and `<!-- project-lineage:auto:end -->`.
- Never expose secret values. Document env var/secret names and evidence only. `.env.example`, `.env.template`, docs, CI config, and DAG references are acceptable evidence; real `.env` values are not.
- Mark each important relationship with evidence and confidence: `High`, `Medium`, or `Low`.

## Decision Gates

| Repo signal | Action |
| --- | --- |
| `dbt_project.yml` exists | Prioritize source YAMLs and datamart YAMLs with `exposures:`; use `ref()` / `source()` as supporting evidence. |
| `dags/` exists | Map DAGs, `dag_id`, schedule, operators, and followed script commands. |
| DAG/script calls internal modules | Follow internal calls only until I/O boundaries: DB, files, APIs, env/secrets, external tools. |
| `scripts/` or Python CLIs exist | Map entrypoints, tables read/written, APIs consumed, and env vars. |
| `.github/workflows/`, `.gitlab-ci.yml`, or CI files exist | Document CI/CD as execution/deploy lineage, not just job inventory. |
| Graph is compact/useful | Include a Mermaid graph with primary nodes only; omit noisy graphs. |

## Execution Steps

1. Inspect repo structure for Airflow, dbt, Python scripts/packages, CI, Docker/deploy config, env templates, and docs.
2. Extract stable IDs using prefixes such as `table:`, `dbt_model:`, `dbt_source:`, `exposure:`, `dag:`, `script:`, `api:`, `env:`, `secret:`, `ci:`, and `file:`.
3. Build three normalized inventories: **Assets**, **Processes**, and **Edges**.
4. For edges, use normalized directions: `produces`, `consumes`, `orchestrates`, `transforms`, or `deploys`.
5. Record evidence as compact file paths plus symbols, commands, or approximate locations when available.
6. Record unknowns/gaps instead of pretending certainty.
7. In preview mode, return the proposed `PROJECT_LINEAGE.md` content and the `AGENTS.md` pointer change without writing.
8. In write mode, create/update `PROJECT_LINEAGE.md` and add/update this short `AGENTS.md` section:

```md
## Project Lineage

- Read `PROJECT_LINEAGE.md` before cross-repo lineage, impact analysis, DAG/dbt/script changes, or architecture work.
- Keep it updated when data assets, DAGs, scripts, CI, or external boundaries change.
```

## Output Contract

`PROJECT_LINEAGE.md` must use this structure:

```md
# Project Lineage

<!-- project-lineage:auto:start -->
## Project Identity
## Repository Shape
## Stable Identifiers
## Assets
## Processes
## Lineage Edges
## dbt Lineage
## Airflow Lineage
## Scripts and CLIs
## API and External Boundaries
## CI/CD and Deployment Boundaries
## Configuration, Env Vars, and Secrets
## Verification Commands
## Lineage Graph
## Unknowns and Gaps
## Comparison Hints
## Refresh
<!-- project-lineage:auto:end -->

## Manual Notes
```

Tables should include `Stable ID`, `Type`, `Direction` or `Role`, `Evidence`, and `Confidence` where relevant.

Return:
- Whether this was preview or write mode.
- Files created or modified.
- Key lineage findings.
- Unknowns/gaps that need human validation.
