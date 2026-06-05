# Implementation Plan: Block-Level Search

**Branch**: `002-block-search` | **Date**: 2026-06-05 | **Spec**: [spec.md](spec.md)

## Summary

Replace note-level embeddings with block-level embeddings. Each note is split into sections (by Markdown heading hierarchy) before indexing. `search` returns individual blocks with their in-note location, giving agents directly usable passages instead of whole notes.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: fastembed, lancedb, pyarrow, click (unchanged from current)

**Storage**: LanceDB — `notes` table replaced by `blocks` table with extended schema

**Testing**: Manual invocation against live vault (no automated tests per constitution)

**Target Platform**: macOS (darwin)

**Project Type**: CLI (single file, per constitution Principle I)

**Performance Goals**: `search` under 3s on a vault of up to 50,000 blocks (~5000 notes × 10 blocks avg)

**Constraints**: Single file `vault.py`, offline-capable, no new dependencies

**Scale/Scope**: 400–5000 notes, average 5–15 blocks per note

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Simplicity (single file) | ✅ PASS | All changes stay in `vault.py` |
| II. Offline-First | ✅ PASS | Same embedding model, no new network calls |
| III. Machine-Readable Output | ✅ PASS | `search` output remains JSON, fields extended |
| IV. Incremental & Idempotent | ✅ PASS | Incremental diff by note mtime; blocks for changed notes deleted and re-embedded |
| V. Vault Safety | ✅ PASS | All writes stay in `~/.cache/vault-cli/<id>/` |

No violations. No complexity tracking required.

## Project Structure

### Documentation (this feature)

```text
specs/002-block-search/
├── plan.md
├── research.md
├── data-model.md
├── contracts/
│   └── cli-commands.md
├── quickstart.md
└── tasks.md
```

### Source Code

```text
vault.py          # single file — all changes here
```

**Structure Decision**: Single-file, per constitution. No new files or modules introduced.
