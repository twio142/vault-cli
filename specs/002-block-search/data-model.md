# Data Model: Block-Level Search

## Block

The atomic unit of the index. Replaces the previous `notes` table entry.

| Field | Type | Description |
|-------|------|-------------|
| `path` | string | Relative path of the note within the vault (e.g., `folder/Note.md`) |
| `block` | string | Block identifier within the note (e.g., `training-data`, `intro`) |
| `title` | string | Note title (stem of filename or `fileName` from metadata) |
| `heading` | string | Section heading text; empty string for preamble block |
| `mtime` | float64 | Note file modification time (Unix timestamp) |
| `text` | string | Full text content of the block |
| `vector` | float32[384] | Embedding vector for the block |

**Primary key**: `(path, block)` — composite, unique per block within the vault.

**Incremental sync key**: `path` + `mtime` — same as previous note-level sync; all blocks for a note are replaced atomically when the note changes.

## Block Splitting Rules

1. A note is split at every Markdown heading line (`#`, `##`, `###`, etc.).
2. Each block consists of: the heading line (if present) + all content until the next heading at the same or higher level.
3. Content appearing before the first heading is the `intro` block.
4. Blocks with fewer than 50 characters (excluding whitespace) are discarded.
5. Blocks exceeding 2000 characters are split at paragraph boundaries; sub-blocks are identified by appending `-{n}` to the slug (e.g., `section-name-1`, `section-name-2`).

## Block Identifier Rules

- Slug = heading text lowercased, non-alphanumeric characters replaced by hyphens, consecutive hyphens collapsed.
- Preamble (content before first heading) → `intro`.
- If two blocks in the same note produce the same slug, append `-{n}` starting from `2` (e.g., `setup`, `setup-2`).
