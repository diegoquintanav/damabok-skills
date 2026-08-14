# Decisions

Architecture decisions for the pipeline itself, one per file in [`docs/adr/`](adr/).
(Decisions about an *analyzed* repo's domain belong in that repo's own ADRs — see
`skills/domain-business-modeling/ADR-FORMAT.md`.)

| ADR | Status | Decision |
| --- | --- | --- |
| [0001](adr/0001-stable-id-derivation.md) | accepted | Stable IDs are rule-derived, then registry-authoritative |
| [0002](adr/0002-schema-gaps-before-deriver.md) | accepted | Schema gaps are fixed before any deriver is written |
| [0003](adr/0003-derivation-into-code.md) | proposed | Derivation moves into code, as one CLI |
| [0004](adr/0004-model-selection-per-delegation.md) | proposed | Model selection is passed per delegation |
| [0005](adr/0005-single-gate-in-glossary-stage.md) | accepted | One gate, in the stage that owns the glossary |
| [0006](adr/0006-avoid-three-relationships.md) | accepted | `_Avoid_` is three relationships, and the glossary can tell them apart |
