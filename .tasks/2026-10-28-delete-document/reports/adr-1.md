# Report — adr-writer, iteration 1

## [2026-10-28T10:08] adr-writer — ADRs 0020 and 0021 drafted

- Created `docs/adr/0020-hard-delete-document-across-all-stores.md` — hard
  delete across filesystem + registry + Qdrant, fail-without-partial-state;
  Status: Proposed.
- Created `docs/adr/0021-orchestrator-executes-roles-in-session.md` — approved
  harness deviation: orchestrator executes roles in-session; Status: Proposed.

Both ADRs list rejected alternatives with reasons. Status remains Proposed;
only the human flips it to Accepted.

## [2026-10-28T11:10] adr-writer — renumbering note

Main concurrently took the number 0020 (`0020-lower-retrieval-threshold-050-near-miss-disclosure.md`, issue #12 pipeline). The two ADRs above were renumbered: 0020 → **0022** (hard delete), 0021 → **0023** (in-session execution). Filenames and title lines were updated accordingly; the historical lines above keep the original numbers as written at the time.
