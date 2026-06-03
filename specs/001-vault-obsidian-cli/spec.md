# Feature Specification: vault-cli — Obsidian Vault Access Tool

**Feature Branch**: `001-vault-obsidian-cli`

**Created**: 2026-06-03

**Status**: Draft

**Input**: User description: "the cli tool described in dev notes"

## User Scenarios & Testing

### User Story 1 - Semantic Note Search (Priority: P1)

An AI agent needs to find notes relevant to a topic. The agent runs a search query and receives
a ranked list of note paths with similarity scores and previews, allowing it to identify which
notes to read next.

**Why this priority**: Semantic search is the core value of the tool. Without it, an agent cannot
navigate a large vault efficiently.

**Independent Test**: Can be tested by running `vault search "some topic"` after indexing and
verifying ranked results are returned in the correct format.

**Acceptance Scenarios**:

1. **Given** the vault is indexed, **When** the agent runs `vault search "topic"`, **Then** it
   receives up to 5 results (default), each on its own line as `<path>\t<score>\t<preview>`,
   ordered by relevance descending.
2. **Given** the vault is indexed, **When** the agent runs `vault search "topic" --k 10`,
   **Then** it receives up to 10 results.
3. **Given** the vault index does not exist, **When** the agent runs `vault search "topic"`,
   **Then** an actionable error is printed to stderr explaining the index must be built first.

---

### User Story 2 - Note Content Reading (Priority: P2)

An AI agent needs to read the full content of a specific note. The agent provides a note path and
receives the raw note text so it can extract information or context.

**Why this priority**: After finding relevant notes via search or link traversal, the agent must
read their full content to extract information. Without reading, search results alone are
insufficient.

**Independent Test**: Can be tested by running `vault read "Note Title"` and verifying the note
content is printed to stdout verbatim.

**Acceptance Scenarios**:

1. **Given** a note exists in the vault, **When** the agent runs `vault read "Note Title"`,
   **Then** the full note content is printed to stdout.
2. **Given** a note exists, **When** the agent runs `vault read "Note Title" --head 10`, **Then**
   only the first 10 lines are printed.
3. **Given** a note does not exist, **When** the agent runs `vault read "Missing Note"`, **Then**
   a clear error is printed to stderr and nothing is printed to stdout.
4. **Given** a note exists, **When** the agent provides the path with or without the `.md`
   extension, **Then** the note is found and its content returned.

---

### User Story 3 - Note Link Traversal (Priority: P3)

An AI agent needs to explore the graph structure of the vault by discovering which notes a given
note links to, and which notes link back to it.

**Why this priority**: Link traversal enables graph-based navigation — an agent can follow topic
threads and discover related notes without issuing new search queries.

**Independent Test**: Can be tested by running `vault neighbors "Note Title"` and verifying
outgoing links and backlinks appear in labeled sections.

**Acceptance Scenarios**:

1. **Given** a note with outgoing wikilinks, **When** the agent runs `vault neighbors "Note Title"`,
   **Then** all linked notes are listed under a `links:` section, one per line.
2. **Given** other notes link to the target note, **When** the agent runs
   `vault neighbors "Note Title"`, **Then** all referencing notes are listed under a `backlinks:`
   section, one per line.
3. **Given** no links exist in either direction, **When** the agent runs
   `vault neighbors "Note Title"`, **Then** the respective section appears with no entries.
4. **Given** the vault metadata plugin data is unavailable or stale, **When** the agent runs
   `vault neighbors "Note Title"`, **Then** links are derived directly from the note's raw text.

---

### User Story 4 - Vault Index Management (Priority: P4)

A user or setup script builds or updates the vault search index so that semantic search can
function. Routine re-indexing only processes changed notes.

**Why this priority**: Indexing is a prerequisite for search but is a periodic operation, not
part of the agent's real-time workflow.

**Independent Test**: Can be tested by running `vault index` and verifying the summary line
reports the correct count of indexed and updated notes.

**Acceptance Scenarios**:

1. **Given** no index exists, **When** the user runs `vault index`, **Then** all vault notes are
   indexed and the output reads `Indexed N notes (M updated).`
2. **Given** an index exists and no notes have changed, **When** the user runs `vault index`,
   **Then** 0 notes are re-embedded and the summary reflects this.
3. **Given** some notes have been modified since the last index run, **When** the user runs
   `vault index`, **Then** only changed notes are re-embedded; unchanged notes are skipped.
4. **Given** any state, **When** the user runs `vault index --force`, **Then** all notes are
   re-indexed from scratch regardless of prior state.
5. **Given** no vault can be located, **When** any command runs, **Then** a clear error is
   printed to stderr explaining how to configure the vault location.

### Edge Cases

- What happens when a note path contains special characters or subdirectory separators?
- How does the system handle notes added while the Obsidian metadata plugin was not running
  (no wikilink data available in plugin output)?
- What happens when the vault contains no `.md` files at all?
- When two notes share the same title in different subdirectories and a bare title is given, the command returns an error listing all matching paths; the caller must re-invoke with the full relative path.

## Requirements

### Functional Requirements

- **FR-001**: The tool MUST expose four commands: `index`, `search`, `neighbors`, and `read`.
- **FR-002**: `vault search <query>` MUST return results ordered by semantic relevance, one per
  line, in the format `<path>\t<score>\t<preview>`.
- **FR-003**: `vault search` MUST support a `--k` flag (default 5) to control result count.
- **FR-004**: `vault read <note-path>` MUST print the full note content to stdout.
- **FR-005**: `vault read` MUST support a `--head N` flag to print only the first N lines.
- **FR-006**: `vault neighbors <note-path>` MUST list outgoing links under `links:` and
  backlinks under `backlinks:`, one path per line.
- **FR-007**: `vault index` MUST only re-embed notes whose content has changed since the last
  index run (mtime-based diffing).
- **FR-008**: `vault index --force` MUST rebuild the entire index from scratch.
- **FR-015**: `vault index` MUST print incremental progress to stderr during indexing (e.g., per-batch or per-note updates) so a human operator can observe long runs. The final summary line (`Indexed N notes (M updated).`) MUST be printed to stdout on completion.
- **FR-016**: `vault search` MUST NOT perform any staleness check. It returns results from the existing index as-is, without warning or error, regardless of whether vault files have changed since the last `vault index` run.
- **FR-009**: All commands MUST accept note paths with or without the `.md` extension. When a bare title matches more than one note in different subdirectories, the command MUST print an error to stderr listing all matching paths and exit without producing output.
- **FR-010**: All error output MUST go to stderr; all structured result output MUST go to stdout.
- **FR-011**: The vault root MUST be resolvable from a `VAULT_DIR` environment variable or by
  walking up the directory tree until a `.obsidian/` directory is found.
- **FR-012**: `vault neighbors` MUST fall back to parsing wikilink syntax directly from raw note
  text when plugin-generated metadata is unavailable or stale.
- **FR-013**: The search index MUST be stored outside the vault directory to avoid conflicts with
  file sync services.
- **FR-014**: The tool MUST support multilingual vaults; a query in one language MUST return
  semantically relevant notes written in another language.

### Key Entities

- **Vault**: The root directory of an Obsidian knowledge base, identified by the presence of a
  `.obsidian/` subdirectory.
- **Note**: A Markdown file (`.md`) within the vault, excluding configured asset and system
  directories.
- **Index**: A persistent store of note embeddings and metadata used to answer semantic search
  queries.
- **Link**: A directed reference from one note to another, expressed as a wikilink
  (`[[Note Title]]`) in note text.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A user can locate a relevant note from a natural-language query in under 5 seconds
  on a cold-start invocation (first call after the index has been built), for a vault of up to
  5,000 notes.
- **SC-002**: Re-indexing a vault of up to 5,000 notes where fewer than 10% of notes have
  changed completes in under 10 seconds.
- **SC-003**: All four commands return correct results against the live vault in manual end-to-end
  validation.
- **SC-004**: An AI agent can complete a multi-step research workflow (search → read → neighbors →
  read) using only these four commands.
- **SC-005**: A query in one language returns semantically relevant notes written in a different
  language (cross-lingual retrieval verified manually).

## Clarifications

### Session 2026-06-03

- Q: When two notes share the same bare title in different subdirectories, which path does resolution use? → A: Error — list both matching paths and require the caller to use the full relative path.
- Q: Should `vault index` show progress during a long run, or only the final summary? → A: Progress printed to stderr during indexing; final summary line to stdout.
- Q: Should `vault search` warn when the index may be stale? → A: No — return results silently from the existing index; staleness is the user's responsibility to manage via `vault index`.
- Q: What is the expected maximum vault size? → A: Medium — 500 to 5,000 notes.

## Assumptions

- The vault contains `.md` files only; canvas files and asset directories are excluded from
  indexing.
- A one-time model download (~2 GB) is required on first use; all subsequent runs are fully
  offline.
- A single user operates the vault; no concurrent write access or multi-user synchronization is
  required.
- The embedding model is downloaded and cached automatically on first use with no manual steps.
- Index files are stored in the user's local cache directory, not inside the vault directory.
- The tool is invoked as a one-shot subprocess; no persistent background process is needed.
- The target vault size is 500–5,000 notes. Behaviour with vaults significantly beyond 5,000 notes is not guaranteed to meet the success criteria.
- Mobile or web interfaces for Obsidian are out of scope; the tool targets desktop CLI use only.
- The `.obsidian/plugins/metadata-extractor/` data is treated as a best-effort cache; its absence
  is a recoverable condition, not an error.
