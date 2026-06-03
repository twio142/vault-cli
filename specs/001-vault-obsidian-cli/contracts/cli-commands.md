# CLI Command Contracts: vault-cli

**Branch**: `001-vault-obsidian-cli` | **Date**: 2026-06-03

All commands are invoked as `python vault.py <command> [args]` or `vault <command> [args]` if
installed as a script entry point.

---

## Global Behaviour

- **Vault resolution**: `VAULT_DIR` env var → walk up from `cwd` until `.obsidian/` found → error.
- **Stdout**: structured result only (machine-parseable).
- **Stderr**: errors, warnings, and progress messages.
- **Exit codes**: `0` on success; non-zero on any error.

---

## `vault index`

### Synopsis

```
vault index [--force]
```

### Options

| Flag      | Type    | Default | Description |
|-----------|---------|---------|-------------|
| `--force` | boolean | false   | Drop and recreate the entire index |

### Behaviour

1. Load or create the LanceDB `notes` table at `~/.cache/vault-cli/<vault-id>/`.
2. Walk all `.md` files under vault root (excluding `.obsidian/`, `_assets/`, `*.canvas`).
3. Diff against stored mtimes. Collect changed/new paths.
4. Emit progress to stderr per batch: `\rIndexing {done}/{total} notes...`
5. Delete stale rows for changed paths; insert new rows.
6. Print final summary to stdout: `Indexed {N} notes ({M} updated).`

With `--force`: drop the table entirely before step 1.

### Output (stdout)

```
Indexed 342 notes (12 updated).
```

### Output (stderr, during run)

```
Indexing 32/342 notes...
```

### Error cases

| Condition | Stderr message |
|-----------|----------------|
| Vault not found | `Error: Vault not found. Set VAULT_DIR or run from within a vault directory.` |
| Model download fails | Propagated from sentence-transformers |

---

## `vault search`

### Synopsis

```
vault search <query> [--k N]
```

### Arguments

| Name    | Required | Description |
|---------|----------|-------------|
| `query` | Yes      | Natural-language search query (any language) |

### Options

| Flag  | Type | Default | Description |
|-------|------|---------|-------------|
| `--k` | int  | 5       | Maximum number of results to return |

### Behaviour

1. Embed `query` with BAAI/bge-m3 (`normalize_embeddings=True`).
2. Run ANN search against the `notes` table, return top-k by cosine similarity.
3. Print one result per line to stdout.
4. No staleness check is performed (FR-016).

### Output format (stdout)

One line per result, tab-separated:

```
<relative-path>\t<score>\t<preview>
```

- `<relative-path>`: path from vault root (e.g., `folder/Note.md`)
- `<score>`: cosine similarity, float `0.0`–`1.0`, 4 decimal places
- `<preview>`: first 120 chars of body text (no tabs or newlines)

**Example**:

```
folder/Note Title.md	0.8712	This note covers the topic in detail...
```

### Error cases

| Condition | Stderr message |
|-----------|----------------|
| Index does not exist | `Error: No index found. Run 'vault index' first.` |
| Vault not found | `Error: Vault not found. Set VAULT_DIR or run from within a vault directory.` |

---

## `vault neighbors`

### Synopsis

```
vault neighbors <note-path>
```

### Arguments

| Name         | Required | Description |
|--------------|----------|-------------|
| `note-path`  | Yes      | Note path or bare title (with or without `.md`) |

### Behaviour

1. Resolve `note-path` to an absolute file path (exact match → `.md` suffix → ambiguity error).
2. Load `metadata.json`. If absent, parse `[[...]]` from raw note text.
3. Build backlinks map by inverting all `links` arrays across the full metadata dict.
4. Print outgoing links and backlinks to stdout.

### Path resolution rules

- If bare title matches exactly one note: resolve.
- If bare title matches multiple notes in different subdirectories: **error** (list all matches).
- If no match: error.

### Output format (stdout)

```
links:
  Other Note.md
  Third Note.md
backlinks:
  Referencing Note.md
```

Empty sections are printed with no entries:

```
links:
backlinks:
  Referencing Note.md
```

### Error cases

| Condition | Stderr message |
|-----------|----------------|
| Note not found | `Error: Note not found: <arg>` |
| Ambiguous title | `Error: Ambiguous title '<title>'. Matches:\n  path/A.md\n  path/B.md` |
| Vault not found | `Error: Vault not found. Set VAULT_DIR or run from within a vault directory.` |

---

## `vault read`

### Synopsis

```
vault read <note-path> [--head N]
```

### Arguments

| Name         | Required | Description |
|--------------|----------|-------------|
| `note-path`  | Yes      | Note path or bare title (with or without `.md`) |

### Options

| Flag     | Type | Default | Description |
|----------|------|---------|-------------|
| `--head` | int  | None    | Print only the first N lines |

### Behaviour

1. Resolve `note-path` (same rules as `vault neighbors`).
2. Read file content.
3. If `--head N`: print first N lines; otherwise print full content.

### Output format (stdout)

Raw file content (UTF-8). No wrapper, no metadata headers.

### Error cases

| Condition | Stderr message |
|-----------|----------------|
| Note not found | `Error: Note not found: <arg>` |
| Ambiguous title | `Error: Ambiguous title '<title>'. Matches:\n  path/A.md\n  path/B.md` |
| Vault not found | `Error: Vault not found. Set VAULT_DIR or run from within a vault directory.` |

---

## Path Resolution Helper (shared)

Used by `read` and `neighbors`:

```
resolve_path(vault_dir, arg):
  1. Try vault_dir / arg            (exact match)
  2. Try vault_dir / (arg + ".md")  (append extension)
  3. Walk vault for all notes where Path(p).stem == arg
       → 0 matches: FileNotFoundError
       → 1 match: return that path
       → 2+ matches: AmbiguousNoteError (list all matches)
```
