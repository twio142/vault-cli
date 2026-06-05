# CLI Command Contracts: Block-Level Search

## Modified Commands

### `./vault.py index [--force]`

Behavior unchanged from the user's perspective. Internally now splits each note into blocks before embedding.

**Output** (stdout):
```
Indexed {total} notes ({updated} updated, {blocks} blocks).
```

**Incremental behavior**: Notes are diffed by mtime as before. When a note changes, all its blocks are deleted and re-embedded. Blocks from deleted notes are purged.

---

### `./vault.py search <query> [--k N]`

Returns block-level results instead of note-level results.

**Output** (stdout) — JSON array:
```json
[
  {
    "path": "relative/path/to/Note.md",
    "block": "section-slug",
    "heading": "Section Heading",
    "score": 0.8412,
    "text": "Full text content of the block..."
  }
]
```

| Field | Type | Description |
|-------|------|-------------|
| `path` | string | Note path relative to vault root |
| `block` | string | Block identifier within the note |
| `heading` | string | Section heading; empty string for preamble blocks |
| `score` | float | Cosine similarity score, 0–1 |
| `text` | string | Full block text content |

**Default**: `--k 5` (top 5 blocks; may include multiple blocks from the same note)

---

## Unchanged Commands

### `./vault.py read <note_path> [--head N]`

No changes. Returns full note content regardless of block structure.

### `./vault.py neighbors <note_path>`

No changes. Returns links and backlinks at note level.
