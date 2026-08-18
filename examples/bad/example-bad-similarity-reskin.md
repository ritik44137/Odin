# Bad Example: Novelty by Renaming

## Why this is bad

Near-duplicates are caught by an embedding search over the whole corpus, not by
string matching. Renaming the domain leaves the meaning intact, so a re-skin scores
close to its original and is rejected. `scripts/check_novelty.py` demonstrates the
effect locally: reword a draft's title and slug while leaving the substance alone
and it still scores above 0.9 against the original.

## The original task

**Title:** Rebuild strict TOML parsing for nested inline tables
**Objective:** Update the parser so it accepts valid nested inline-table constructs,
rejects malformed and duplicate-key variants with precise failure behaviour, and
preserves the rest of the parser API.

## The re-skin

**Title:** Rebuild strict YAML parsing for nested flow mappings
**Objective:** Update the parser so it accepts valid nested flow-mapping constructs,
rejects malformed and duplicate-key variants with precise failure behaviour, and
preserves the rest of the parser API.

## Problems

- The engineering content is identical: recursive descent over a nested literal
  syntax, duplicate-key detection across scopes, precise error behaviour, API
  compatibility. Only the format name changed.
- The verifier design transfers unchanged, which is the clearest signal that no new
  problem is being posed.
- The difficulty explanation would be the same sentence with one noun replaced.
- A reviewer who has seen the first task learns nothing from the second, which is
  the actual bar behind the similarity gate.

## What genuine novelty looks like

Change the *shape of the reasoning*, not the domain vocabulary. Starting from the
same parser codebase, these are different problems:

- make the parser incremental, so it re-parses only the changed region of a document
  and must maintain position state across edits
- add error recovery that continues after the first failure and reports every
  problem in one pass, which requires deciding where to resynchronise
- make the parser preserve comments and formatting through a parse/serialise round
  trip, which changes the data model rather than the grammar

Each demands a different design, a different verifier, and a different failure mode.
A domain swap demands none of those.

## Test to apply before building

Ask what a solver has to *figure out* that no previous task required. If the answer
is "the same thing, in a different format", the idea is not ready. If you cannot
answer at all, the similarity stage will answer for you.
