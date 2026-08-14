---
status: accepted
---

# Stable IDs are rule-derived, then registry-authoritative

Implemented in `959a904`.

The first real pipeline run proved slug derivation was underspecified in three ways that
could silently sever the join key. The rules now live in
`skills/domain-business-modeling/CONTEXT-FORMAT.md` under "Slug rules":

- **Elided articles are dropped.** `Coût d'entrepôt` → `cout-entrepot`,
  never a stranded `cout-d-entrepot`.
- **Connector words are frozen as they are, never normalized.** The corpus really does
  contain both `categorie-de-clients` and `temps-livraison`. Normalizing would
  re-key every downstream artifact for no functional gain.
- **A parenthetical is a short code only if it appears as an identifier in the analyzed
  repo.** `sw` is a real column, so `Shipment weight (sw)` →
  `concept:sw`. `número` appears nowhere in the code, so `Order (número)` →
  `concept:order`, not `concept:numero`.

The last rule is deliberately *not* a token-shape test. A shape allowlist like
`^[a-z][a-z0-9_]*$` rejects `número` only by accident of its accent, and would happily
accept a plain-ASCII synonym such as "number" and mint the wrong ID. Presence in the
codebase is the property that actually distinguishes the two, and it is mechanically
checkable.

**Rejected: an explicit stable-ID marker in `CONTEXT.md`.** It would make derivation
purely mechanical, but at the cost of putting machine keys into a glossary written for
humans. It is also unnecessary: `context.json` is already the ID registry, and
`CONTEXT-FORMAT.md` states that an existing ID beats the rule that would have produced
it. A fresh repo derives from the rules; every run thereafter reuses the registry.
