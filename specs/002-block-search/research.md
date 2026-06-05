# Research: Block-Level Search

**Date**: 2026-06-05

## Chunking Strategy

**Decision**: Split notes at Markdown heading boundaries. Each heading + its content (until the next same-or-higher-level heading) forms one block.

**Rationale**: Headings are the natural semantic unit in Obsidian notes. Paragraph-level splitting produces too many tiny blocks; sentence-level is over-engineering for this scale.

**Alternatives considered**:
- Paragraph splitting — produces noisy low-signal blocks for short paragraphs; headings are more meaningful
- Fixed token windows — ignores document structure; heading-based is simpler and more interpretable
- Sentence splitting — too granular; adds complexity with marginal retrieval benefit at vault scale

**Rules**:
1. Split at every `#`, `##`, `###`, etc. heading line
2. Each block = heading text + all content until next heading of same or higher level
3. Notes with no headings → single block (whole note)
4. Blocks shorter than 50 characters → skip
5. Blocks longer than ~2000 characters → split at paragraph boundaries into sub-blocks of ≤2000 chars

## Block Identifier Format

**Decision**: `{heading_slug}` where the slug is the heading text lowercased with spaces replaced by hyphens. For un-headed content (preamble before first heading) use `intro`. For sub-blocks after length splitting, append `-{n}` (e.g., `training-data-1`).

**Rationale**: Human-readable, allows agents to understand what the block contains from the identifier alone. Does not need to be stable across heading renames (full re-index with `--force` is acceptable per spec assumptions).

**Alternatives considered**:
- Line offsets (`L42`) — stable across renames but opaque; agents can't infer content from the id
- Sequential integers (`block-0`, `block-1`) — same opacity problem

## Schema Design

**Decision**: Replace the `notes` table with a `blocks` table. No parallel note-level table.

| Field | Type | Purpose |
|-------|------|---------|
| `path` | string | Note relative path (for grouping and incremental sync) |
| `block` | string | Block identifier within the note |
| `title` | string | Note title (for display) |
| `heading` | string | Section heading text (empty for intro block) |
| `mtime` | float64 | Note mtime (used for incremental diff — per note, not per block) |
| `text` | string | Full block text content |
| `vector` | list[float32, 384] | Embedding vector |

**Rationale**: A single flat table is simpler and sufficient. Incremental sync keys on `path` (note-level mtime), deletes all blocks for a changed note, and re-inserts. This avoids block-level change tracking which would require storing per-block hashes.

**Alternatives considered**:
- Keep `notes` table alongside a new `blocks` table — two tables to maintain, no benefit since `search` only uses blocks now
- Store block hash for per-block incremental sync — over-engineering; note mtime is cheap and notes rarely have >20 blocks

## Embedding Text per Block

**Decision**: `{note_title}\n\n{heading}\n\n{block_text}`

**Rationale**: Prepending title and heading gives the model context about where the block lives, improving retrieval for queries that reference the broader topic. Matches the existing pattern for note-level embedding.

## Search Output Format

**Decision**: Extend existing JSON output with `block` and `heading` fields, rename `preview` to `text` and return full block text.

```json
[
  {
    "path": "Machine Learning.md",
    "block": "training-data",
    "heading": "Training Data",
    "score": 0.82,
    "text": "Training data is the..."
  }
]
```

**Rationale**: `text` replaces the truncated `preview` since block content is already bounded in length. Agents need the full block text to use results directly.
