# Tasks: Block-Level Search

**Input**: Design documents from `specs/002-block-search/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli-commands.md

**Organization**: Tasks are grouped by user story. All changes are in `vault.py`.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Replace the note-level schema and add block splitting. Both user stories depend on this.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T001 Replace `SCHEMA` constant in `vault.py` — change table name from `notes` to `blocks` and update fields: remove `preview`, add `block` (string), `heading` (string), `text` (string); keep `path`, `title`, `mtime`, `vector[384]`
- [ ] T002 Implement `split_blocks(path: Path, body: str, title: str) -> list[dict]` in `vault.py` — splits a note into blocks by Markdown heading boundaries; each block is `{block, heading, text}`; rules: skip blocks < 50 chars, split blocks > 2000 chars at paragraph boundaries with slug suffix `-{n}`, preamble before first heading uses slug `intro`, duplicate slugs within a note get `-2`, `-3` suffixes

**Checkpoint**: Schema and splitter ready. User story implementation can begin.

---

## Phase 2: User Story 1 — Search Returns Specific Passages (Priority: P1) 🎯 MVP

**Goal**: `search` returns block-level results with location and full text.

**Independent Test**: Run `./vault.py index --force` then `./vault.py search "topic"`. Each result must include `path`, `block`, `heading`, `score`, and `text` fields. The `block` field must identify a specific section, not the whole note.

### Implementation for User Story 1

- [ ] T003 [US1] Replace `embed_notes` with `embed_blocks` in `vault.py` — iterate over `split_blocks()` output per note, build embed text as `{title}\n\n{heading}\n\n{block_text}`, return rows with all block fields (`path`, `block`, `heading`, `title`, `mtime`, `text`, `vector`)
- [ ] T004 [US1] Update `cmd_index` in `vault.py` — call `embed_blocks` instead of `embed_notes`; update summary line to `Indexed {total} notes ({updated} updated, {blocks} blocks).`
- [ ] T005 [US1] Update `cmd_search` in `vault.py` — update result mapping to output `{path, block, heading, score, text}` JSON fields; remove `preview` field

**Checkpoint**: `./vault.py index --force && ./vault.py search "query"` returns block-level JSON results.

---

## Phase 3: User Story 2 — Block Index Stays in Sync (Priority: P2)

**Goal**: Incremental `index` runs re-embed only changed notes' blocks and purge deleted notes' blocks.

**Independent Test**: Edit one note, run `./vault.py index`. Only that note's blocks should be reported as updated. Delete a note, run `./vault.py index`. That note's blocks should be gone from search results.

### Implementation for User Story 2

- [ ] T006 [US2] Verify `diff_notes` in `vault.py` handles multiple rows per path — `dict(zip(df["path"], df["mtime"]))` naturally deduplicates since all blocks for a note share the same mtime; confirm no change needed or fix if not correct
- [ ] T007 [US2] Verify orphan cleanup in `cmd_index` uses `path IN (...)` delete — this already removes all blocks for deleted notes since the delete key is `path`; confirm no change needed or fix if not correct
- [ ] T008 [US2] Run quickstart.md scenarios 3, 4, 5, 6 against live vault to validate incremental sync and idempotency

**Checkpoint**: Two sequential `./vault.py index` runs with no vault changes report 0 blocks updated on the second run.

---

## Phase 4: Polish

- [ ] T009 Update `README.md` — document that `search` now returns block-level results; update the output format description
- [ ] T010 Run all quickstart.md validation scenarios (1–6) against live vault

---

## Dependencies & Execution Order

- **Phase 1 (Foundational)**: No dependencies — start immediately
- **Phase 2 (US1)**: Requires Phase 1 complete (T001, T002)
- **Phase 3 (US2)**: Requires Phase 2 complete — incremental logic only makes sense once blocks are being written
- **Phase 4 (Polish)**: Requires Phase 2 and 3 complete

### Within Each Phase

- T001 before T002 (schema before splitter, to avoid editing back-and-forth)
- T002 before T003 (splitter before embed_blocks)
- T003 before T004 before T005 (embed → index → search, each builds on previous)
- T006 and T007 can run in parallel (different functions)

---

## Implementation Strategy

### MVP (User Story 1 only)

1. Complete Phase 1 (T001–T002)
2. Complete Phase 2 (T003–T005)
3. Run `./vault.py index --force && ./vault.py search "test query"` — validate block-level output
4. **STOP and validate** before proceeding to sync verification

### Full Delivery

1. Phase 1 → Phase 2 → Phase 3 → Phase 4
2. Each phase verified against quickstart.md before moving on

---

## Notes

- All changes are in `vault.py` only (constitution Principle I)
- No new dependencies
- `--force` handles schema migration (drops and recreates the table)
- Users must run `./vault.py index --force` after upgrading to re-build the block index
