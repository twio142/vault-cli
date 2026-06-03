---

description: "Task list for vault-cli — Obsidian Vault Access Tool"
---

# Tasks: vault-cli — Obsidian Vault Access Tool

**Input**: Design documents from `specs/001-vault-obsidian-cli/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/cli-commands.md ✅

**Tests**: No automated tests. Each command validated manually against the live vault before
the next command is implemented (per DEVELOPMENT.md and quickstart.md checklist).

**Implementation file**: All code lives in a single file — `vault.py` at the repository root.

**Phase ordering note**: US4 (vault index, spec priority P4) appears before US1 (vault search,
spec priority P1) because vault search requires a built index to function. Implementation order
follows DEVELOPMENT.md: read → neighbors → index → search.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different logical sections, no incomplete dependency)
- **[Story]**: Which user story this task belongs to (US1=search, US2=read, US3=neighbors, US4=index)

---

## Phase 1: Setup

**Purpose**: Project initialization and dependency declaration

- [x] T001 Create `vault.py` with top-level click group scaffold: import block (`click`, `pathlib`, `os`, `re`, `sys`, `hashlib`, `json`), `@click.group()` decorated `cli()` function, and stub `if __name__ == "__main__": cli()` entry point
- [x] T002 [P] Create `requirements.txt` with four dependencies: `sentence-transformers`, `lancedb`, `pyarrow`, `click`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared helpers required by every command. MUST be complete before any command is implemented.

**⚠️ CRITICAL**: No command implementation can begin until this phase is complete.

- [x] T003 Implement `find_vault_root() -> Path` in `vault.py`: check `VAULT_DIR` env var first; if unset, walk up from `Path.cwd()` until a directory containing `.obsidian/` is found; raise `SystemExit` with message `"Error: Vault not found. Set VAULT_DIR or run from within a vault directory."` if neither resolves
- [x] T004 [P] Implement `resolve_path(vault_dir: Path, arg: str) -> Path` in `vault.py`: try `vault_dir / arg` (exact match); try `vault_dir / (arg + ".md")`; walk vault for all `.md` files where `Path(p).stem == arg`; raise `FileNotFoundError` for 0 matches; raise `SystemExit` listing all matches for 2+ matches (ambiguous title error per FR-009)
- [x] T005 [P] Implement `cache_dir(vault_path: Path) -> Path` in `vault.py`: return `Path.home() / ".cache" / "vault-cli" / hashlib.sha256(str(vault_path.resolve()).encode()).hexdigest()[:8]`; call `.mkdir(parents=True, exist_ok=True)` before returning

**Checkpoint**: Helpers complete — all three functions testable by importing and calling them.

---

## Phase 3: User Story 2 — Note Content Reading (Spec Priority: P2) 🎯 First MVP command

**Goal**: Agent can read full note content or a head-truncated excerpt by path or bare title.

**Independent Test**: `python vault.py read "Note Title"` prints raw note content to stdout; `--head 5` prints exactly 5 lines; missing note prints to stderr only.

### Implementation for User Story 2

- [x] T006 [US2] Implement `@cli.command() read` in `vault.py`: accept `note_path` argument and `--head` integer option (default None); call `find_vault_root()` and `resolve_path()`; read file as UTF-8; if `--head N`, print first N lines; else print full content; errors go to stderr (use `click.echo(..., err=True)`) and exit non-zero

**Checkpoint**: `vault read` fully functional — run quickstart.md read validation items before proceeding.

---

## Phase 4: User Story 3 — Note Link Traversal (Spec Priority: P3)

**Goal**: Agent can discover outgoing links and backlinks for any note.

**Independent Test**: `python vault.py neighbors "Note Title"` prints `links:` and `backlinks:` sections; works when metadata.json is absent (regex fallback).

### Implementation for User Story 3

- [x] T007 [US3] Implement `load_metadata(vault_dir: Path) -> dict` in `vault.py`: load `vault_dir / ".obsidian" / "plugins" / "metadata-extractor" / "metadata.json"` via `json.load()`; return empty dict `{}` if the file is absent or malformed (do not raise)
- [x] T008 [P] [US3] Implement `parse_wikilinks(note_text: str) -> list[str]` in `vault.py`: return `re.findall(r'\[\[([^\|\]]+)', note_text)` — captures link target before any `|` alias separator; used as fallback when metadata is absent
- [x] T009 [US3] Implement `build_backlinks(metadata: dict) -> dict[str, list[str]]` in `vault.py`: invert all `links` arrays — for each note in metadata, for each entry in its `links` list, append the source note's `relativePath` to `backlinks[link["relativePath"]]`; return the resulting dict
- [x] T010 [US3] Implement `@cli.command() neighbors` in `vault.py`: accept `note_path` argument; resolve path; call `load_metadata()`; if metadata empty, call `parse_wikilinks()` on raw note text for outgoing links; call `build_backlinks()`; print `links:\n  <path>\n  ...` and `backlinks:\n  <path>\n  ...` to stdout (empty section = label with no entries)

**Checkpoint**: `vault neighbors` fully functional — run quickstart.md neighbors validation items before proceeding.

---

## Phase 5: User Story 4 — Vault Index Management (Spec Priority: P4)

**Purpose**: Build the vector index required by vault search (US1). MUST complete before Phase 6.

**⚠️ PREREQUISITE for Phase 6 (vault search)**

**Goal**: User can build and incrementally update the vault search index.

**Independent Test**: `python vault.py index` prints progress to stderr and summary to stdout; second run with no changes shows 0 updated; `--force` re-embeds all notes.

### Implementation for User Story 4

- [x] T011 [US4] Add `lancedb`, `pyarrow`, and `sentence_transformers` imports to `vault.py`; define `SCHEMA = pa.schema([pa.field("path", pa.string()), pa.field("title", pa.string()), pa.field("mtime", pa.float64()), pa.field("preview", pa.string()), pa.field("vector", pa.list_(pa.float32(), 1024))])` as a module-level constant
- [x] T012 [P] [US4] Implement `open_table(cache: Path, force: bool) -> lancedb.table.Table` in `vault.py`: connect to LanceDB at `cache`; if `force` and table exists, drop it; open or create `notes` table with `SCHEMA`; return table
- [x] T013 [P] [US4] Implement `walk_vault(vault_dir: Path) -> list[Path]` in `vault.py`: recursively find all `.md` files under `vault_dir`, excluding any path under `.obsidian/` or `_assets/`, and any file matching `*.canvas`; return list of absolute paths
- [x] T014 [US4] Implement `diff_notes(table, vault_dir: Path, all_paths: list[Path]) -> list[Path]` in `vault.py`: build `{path_str: mtime}` dict from existing table rows; for each file in `all_paths`, compute relative path and current mtime; collect files where mtime differs or path is new; return list of changed absolute paths
- [x] T015 [US4] Implement `embed_notes(model, vault_dir: Path, paths: list[Path], metadata: dict) -> list[dict]` in `vault.py`: for each path, build `title` (from metadata or stem), `headings` (from metadata), `body` (raw file text); construct embed text as `"{title}\n\n{headings_joined}\n\n{body[:2000]}"`; call `model.encode(texts, batch_size=32, normalize_embeddings=True)` in batches of 32; print `\rIndexing {done}/{total} notes...` to stderr with `end=""` after each batch; print final newline to stderr; return list of row dicts with `path`, `title`, `mtime`, `preview` (first 300 chars of body), `vector` fields
- [x] T016 [US4] Implement `@cli.command() index` in `vault.py`: accept `--force` flag; call `find_vault_root()`, `cache_dir()`, `open_table()`; if not force, call `diff_notes()` — if 0 changed, print summary and return early; delete stale rows via `table.delete(f"path IN ({placeholders})")` with the changed paths; load model (`SentenceTransformer("BAAI/bge-m3")`); call `embed_notes()`; call `table.add(rows)`; print `Indexed {total} notes ({updated} updated).` to stdout

**Checkpoint**: `vault index` fully functional — run quickstart.md index validation items before proceeding.

---

## Phase 6: User Story 1 — Semantic Note Search (Spec Priority: P1)

**Depends on**: Phase 5 complete and vault indexed.

**Goal**: Agent receives ranked, tab-separated note results for any natural-language query.

**Independent Test**: `python vault.py search "topic"` returns tab-separated results ordered by score; `--k 10` returns up to 10 results; cross-lingual query returns relevant notes in another language.

### Implementation for User Story 1

- [x] T017 [US1] Implement `@cli.command() search` in `vault.py`: accept `query` argument and `--k` integer option (default 5); call `find_vault_root()`, `cache_dir()`; if table does not exist, print `"Error: No index found. Run 'vault index' first."` to stderr and exit non-zero; load model; encode query via `model.encode([query], normalize_embeddings=True)[0]`; run `table.search(vector).limit(k).to_list()`; for each result, print `{path}\t{score:.4f}\t{preview[:120]}` to stdout (replace tabs/newlines in preview with space)

**Checkpoint**: `vault search` fully functional — run all quickstart.md search validation items, including cross-lingual query.

---

## Phase 7: Polish & End-to-End Validation

**Purpose**: Full workflow verification and cleanup.

- [ ] T018 Run complete quickstart.md validation checklist against the live vault; check off each item; fix any failing items in `vault.py`
- [ ] T019 [P] Verify agent workflow: `vault search` → pick top result → `vault read` (result path) → `vault neighbors` (same path) → `vault read` (a backlinked note); confirm SC-004 is satisfied
- [ ] T020 [P] Verify cross-lingual retrieval (SC-005): run an English query and confirm at least one Chinese or German note (if present in vault) appears in results
- [ ] T021 [P] Check cold-start search latency (SC-001): time `python vault.py search "topic"` from a fresh Python process; confirm under 5 seconds for the live vault size

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all commands
- **vault read (Phase 3)**: Depends on Phase 2 — independent of Phases 4, 5, 6
- **vault neighbors (Phase 4)**: Depends on Phase 2 — independent of Phases 3, 5, 6
- **vault index (Phase 5)**: Depends on Phase 2 — BLOCKS Phase 6
- **vault search (Phase 6)**: Depends on Phase 5 (index must exist)
- **Polish (Phase 7)**: Depends on all Phases 3–6

### User Story Dependencies

- **US2 (vault read, P2)**: Independent — can start after Foundational
- **US3 (vault neighbors, P3)**: Independent — can start after Foundational
- **US4 (vault index, P4)**: Independent — can start after Foundational; BLOCKS US1
- **US1 (vault search, P1)**: Requires US4 complete and vault indexed

### Within Each Phase

- Tasks marked [P] share no file-section conflicts and can be worked simultaneously
- Validate against live vault before advancing to the next phase

### Parallel Opportunities

- T001 and T002 can run in parallel (Setup)
- T003, T004, T005 can all run in parallel (Foundational)
- Phases 3 and 4 (vault read + vault neighbors) can be implemented in parallel
- T011, T012, T013 can run in parallel (vault index setup)
- T018, T019, T020, T021 can run in parallel (Polish)

---

## Implementation Strategy

### MVP (Phase 3 only — vault read)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: vault read
4. **STOP and VALIDATE**: `vault read "Note Title"` works correctly
5. Proceed to Phase 4

### Full Sequential Delivery

1. Phase 1 + 2 → Foundation
2. Phase 3 → `vault read` working
3. Phase 4 → `vault neighbors` working
4. Phase 5 → `vault index` working (first model download here)
5. Phase 6 → `vault search` working
6. Phase 7 → Full validation

---

## Notes

- All code goes in `vault.py` — no other Python files
- [P] marks tasks with no dependency conflicts; safe to parallelize within a phase
- Test each command against the live vault before advancing
- Phase ordering deviates from spec priority order because vault search (P1) depends on vault index (P4)
- Model load (~2–3 s) first occurs in Phase 5; all phases before that are fast
