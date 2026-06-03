# Implementation Plan: vault-cli — Obsidian Vault Access Tool

**Branch**: `001-vault-obsidian-cli` | **Date**: 2026-06-03 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-vault-obsidian-cli/spec.md`

## Summary

Build a single-file Python CLI (`vault.py`) giving AI agents semantic access to an Obsidian vault
through four commands: `index`, `search`, `neighbors`, and `read`. The implementation uses
BAAI/bge-m3 embeddings stored in an embedded LanceDB vector database for offline semantic search,
with incremental mtime-based re-indexing and wikilink graph traversal via metadata plugin data
or raw-text regex fallback. No background daemon; invoked as a one-shot subprocess.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `sentence-transformers` (BAAI/bge-m3 embeddings), `lancedb` (embedded
vector store), `pyarrow` (LanceDB table schema), `click` (CLI framework)

**Storage**: LanceDB embedded database at `~/.cache/vault-cli/<vault-id>/`, where `<vault-id>`
is the first 8 hex characters of `sha256(str(resolved_vault_path))`.

**Testing**: Manual validation against the live vault; each command tested before the next is
implemented (see DEVELOPMENT.md implementation order).

**Target Platform**: macOS/Linux desktop CLI (invoked as a Python subprocess)

**Project Type**: CLI tool

**Performance Goals**: `vault search` cold-start under 5 seconds for vaults up to 5,000 notes;
`vault index` incremental run (fewer than 10% of notes changed) under 10 seconds.

**Constraints**: Fully offline after one-time model download (~2 GB); single-file implementation
(`vault.py`); no background daemon; index stored outside vault at `~/.cache/vault-cli/`.

**Scale/Scope**: 500–5,000 notes; single user; no concurrent access.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Simplicity | ✅ PASS | Single file `vault.py`; four commands; no package structure |
| II. Offline-First | ✅ PASS | LanceDB embedded; model runs locally; zero network at runtime |
| III. Machine-Readable Output | ✅ PASS | Tab-separated search; labeled-section neighbors; raw-content read; single-line index summary |
| IV. Incremental & Idempotent | ✅ PASS | mtime diff on index; regex fallback for neighbors; `--force` for full rebuild |
| V. Vault Safety | ✅ PASS | All writes go to `~/.cache/vault-cli/`; vault directory is read-only |

No violations. No Complexity Tracking required.

## Project Structure

### Documentation (this feature)

```text
specs/001-vault-obsidian-cli/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── cli-commands.md  # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
vault-cli/
├── vault.py             # entire implementation (~250 lines)
└── requirements.txt
```

**Structure Decision**: Single-file per constitution Principle I. All four commands plus shared
helpers (vault resolution, path resolution, model loading, cache path) live in `vault.py`.
No `src/` hierarchy is needed at this scale.
