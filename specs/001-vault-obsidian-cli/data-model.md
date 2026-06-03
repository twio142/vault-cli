# Data Model: vault-cli — Obsidian Vault Access Tool

**Branch**: `001-vault-obsidian-cli` | **Date**: 2026-06-03

---

## LanceDB Table: `notes`

Primary persistent data store. One row per indexed note.

| Field     | Type                  | Constraints           | Description |
|-----------|-----------------------|-----------------------|-------------|
| `path`    | `string`              | Unique, non-null      | Relative path from vault root (e.g., `folder/Note Title.md`) |
| `title`   | `string`              | Non-null              | Note title: `fileName` from metadata.json, or filename stem |
| `mtime`   | `float64`             | Non-null              | File modification time, seconds since Unix epoch |
| `preview` | `string`              | Non-null, ≤300 chars  | First 300 characters of body text (after frontmatter) |
| `vector`  | `list<float32>[1024]` | Non-null, normalized  | BGE-M3 embedding with `normalize_embeddings=True` |

**Primary key**: `path` (used for delete-then-insert upsert pattern).

**Index type**: ANN (approximate nearest-neighbor) on `vector` column, cosine metric (equivalent
to dot product on normalized vectors).

---

## Embedded Text Format (not stored; used at index time)

For each note, the text submitted to the embedding model is constructed as:

```
{title}

{heading1}
{heading2}
...

{body text, first 2000 characters}
```

Fields sourced from metadata.json when available; raw file parsing otherwise.

---

## Runtime Note Record (in-memory only)

Used during indexing and neighbors traversal. Not persisted beyond the LanceDB row.

| Field       | Type           | Source |
|-------------|----------------|--------|
| `path`      | `str`          | Relative path from vault root |
| `title`     | `str`          | `metadata["fileName"]` or `Path(path).stem` |
| `headings`  | `list[str]`    | `[h["heading"] for h in metadata["headings"]]` |
| `body`      | `str`          | Raw `.md` file content |
| `links`     | `list[str]`    | `[l["relativePath"] for l in metadata["links"]]` |
| `mtime`     | `float`        | `os.path.getmtime(abs_path)` |

---

## metadata.json (Obsidian plugin output)

Location: `<vault>/.obsidian/plugins/metadata-extractor/metadata.json`

Object keyed by filename (e.g., `"Note Title.md"`):

```json
{
  "Note Title.md": {
    "fileName": "Note Title",
    "relativePath": "Note Title.md",
    "tags": ["tag1", "tag2"],
    "frontmatter": {},
    "headings": [
      { "heading": "Section", "level": 2 }
    ],
    "links": [
      { "link": "Other Note", "relativePath": "Other Note.md" }
    ]
  }
}
```

**Backlinks** are not stored; they are derived by inverting the `links` map across all entries.

**Staleness**: Only updated when Obsidian is running. Treated as best-effort cache; absence is
recoverable (regex fallback applies).

---

## Backlinks Map (in-memory, derived)

Built during `vault neighbors` by inverting `metadata.json`:

```python
backlinks: dict[str, list[str]] = {}
for filename, meta in metadata.items():
    for link in meta.get("links", []):
        target = link["relativePath"]
        backlinks.setdefault(target, []).append(meta["relativePath"])
```

---

## Cache Directory Layout

```text
~/.cache/vault-cli/
└── <vault-id>/           # sha256(resolved_vault_path)[:8]
    └── notes.lance/      # LanceDB table files (managed by LanceDB)
```

`<vault-id>` is the first 8 hex characters of `sha256(str(vault_path.resolve()).encode())`.

---

## Excluded Files

The following are excluded from indexing (never appear in the `notes` table):

- Any file under `<vault>/.obsidian/`
- Any file under `<vault>/_assets/`
- Any file matching `*.canvas`
- Any non-`.md` file
