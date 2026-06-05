# Feature Specification: Block-Level Search

**Feature Branch**: `002-block-search`

**Created**: 2026-06-05

**Status**: Draft

**Input**: User description: "block-level search indexing — split notes into chunks and index them for more granular retrieval"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Search Returns Specific Passages (Priority: P1)

An AI agent queries the vault for a topic and receives results pointing to the specific paragraph or section within a note that matches, rather than just the note as a whole. The agent can immediately use the returned text without reading the entire note.

**Why this priority**: The core value of block-level search. Without this, the agent must read full notes to find relevant content, which is slow and wastes context.

**Independent Test**: Run `search` with a query that is only discussed in one section of a large note. The top result should identify that section directly, not just the note.

**Acceptance Scenarios**:

1. **Given** a vault is indexed at block level, **When** an agent searches for a topic covered in a subsection of a note, **Then** the result identifies that specific block with its location within the note.
2. **Given** a search query, **When** results are returned, **Then** each result includes the block's text content, its score, and a path that identifies both the file and the block's position.
3. **Given** two notes that both mention a topic but one has a dedicated section on it, **When** a search is run, **Then** the dedicated section ranks higher than the passing mention.

---

### User Story 2 - Block Index Stays in Sync (Priority: P2)

When a note is edited, only the affected blocks are re-embedded on the next `index` run. Deleted notes and removed sections are purged from the index automatically.

**Why this priority**: Without incremental sync, every edit triggers a full re-index, making the tool too slow for regular use.

**Independent Test**: Edit one section of a note, run `index`, and verify only that note's blocks are re-embedded. Delete a note and verify its blocks are removed.

**Acceptance Scenarios**:

1. **Given** a previously indexed vault, **When** a single note is modified and `index` is run again, **Then** only the blocks belonging to that note are re-embedded.
2. **Given** a block exists in the index, **When** the corresponding note is deleted from the vault, **Then** that block is removed from the index on the next `index` run.
3. **Given** an unmodified vault, **When** `index` is run twice in a row, **Then** the second run reports zero blocks updated.

---

### Edge Cases

- What happens when a note consists of a single paragraph with no headings?
- What happens when a block is very short (one line) or very long (thousands of words)?
- What happens when two blocks within the same note are nearly identical?
- How are blocks identified if a heading is renamed?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The index MUST store embeddings at the block level, where a block is a contiguous section of a note defined by its heading hierarchy or paragraph boundaries.
- **FR-002**: Each indexed block MUST be identifiable by a composite key combining the note's relative path and the block's position within that note.
- **FR-003**: `search` results MUST include the block's text content, its location (file + block identifier), and its similarity score.
- **FR-004**: `index` MUST detect which notes have changed (via mtime) and re-index only the blocks belonging to those notes.
- **FR-005**: `index` MUST remove blocks belonging to notes that have been deleted from the vault.
- **FR-006**: `index --force` MUST rebuild the entire block index from scratch.
- **FR-007**: Blocks shorter than a minimum useful length MUST be skipped or merged with adjacent content to avoid noisy low-signal results.
- **FR-008**: Blocks longer than the embedding model's effective token limit MUST be split into sub-blocks rather than truncated.
- **FR-009**: `search` output MUST remain JSON, with each result object extended to include block-level location fields.
- **FR-010**: The `read` command MUST continue to work unchanged — it returns full note content regardless of how the note is chunked internally.

### Key Entities

- **Block**: A contiguous chunk of text within a note, bounded by heading boundaries or paragraph breaks. Has a path, a position identifier, text content, and an embedding vector.
- **Block identifier**: A string encoding a block's position within its note (e.g., heading path or line offset), sufficient to locate the block when the note is read later.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A search query that targets a specific section of a multi-section note returns that section in the top 3 results rather than an unrelated note.
- **SC-002**: `search` response time remains under 3 seconds on a vault of up to 5000 notes with an average of 10 blocks per note.
- **SC-003**: After editing one note in a 400-note vault, `index` re-embeds only the blocks of that note (not the entire vault).
- **SC-004**: Running `index` twice without any vault changes produces identical output both times with zero blocks updated on the second run.

## Assumptions

- Block splitting is based on Markdown heading structure and paragraph boundaries; no semantic sentence-level splitting is needed.
- The minimum block size is approximately 50 characters; shorter content is not worth a separate embedding.
- A note with no headings is treated as a single block.
- Block identifiers do not need to be stable across heading renames; a `--force` rebuild is acceptable after structural edits.
- The existing note-level `read` and `neighbors` commands are out of scope for this feature.
- The constitution's single-file constraint (`vault.py`) remains in effect.
