---
status: accepted
---

# Schema gaps are fixed before any deriver is written

Implemented in `959a904`.

The first run dropped real data in four places where a schema had nowhere to put it:
`otherMentions[].evidence`, `goldenRecord.confidence`,
`glossarySuggestions.suggestedContext`, and `unknownMappings.reference` (required, so
broad notes were emitted as `""`). All four are now optional-and-carried.

The ordering matters: a code generator written against the old schemas would have
encoded that loss permanently and made it much harder to notice, because a deterministic
parser producing valid output looks correct. The sharpest case was WarehouseLocation,
whose `Medium` confidence in a survivorship claim was being flattened under its `High`
master-data classification — two different claims that a single confidence field cannot
express.
