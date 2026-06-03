# Research: vault-cli — Obsidian Vault Access Tool

**Branch**: `001-vault-obsidian-cli` | **Date**: 2026-06-03

All decisions below were resolved from `DEVELOPMENT.md`, the project constitution, and established
library documentation. No external unknowns remain.

---

## Decision 1: Embedding Model

**Decision**: BAAI/bge-m3 via `sentence-transformers`

**Rationale**: 1024-dimensional output; strong multilingual support (Chinese, German, English);
`normalize_embeddings=True` enables cosine similarity via dot product, which matches LanceDB's
default metric. Model is downloaded once, then cached locally by sentence-transformers.

**Alternatives considered**: `text-embedding-3-small` (OpenAI) — rejected (requires network);
`all-MiniLM-L6-v2` — rejected (384-dim, weaker multilingual); `paraphrase-multilingual-mpnet` —
rejected (slower, less accurate on mixed-language corpora than bge-m3).

---

## Decision 2: Vector Store

**Decision**: LanceDB (embedded, file-based)

**Rationale**: No server process; stores data as files compatible with `~/.cache/`; native Python
API; supports ANN search out of the box with cosine metric.

**Alternatives considered**: ChromaDB — rejected (requires a running process or has heavier deps);
FAISS — rejected (no persistence layer, requires manual index serialization); SQLite with pgvector
— rejected (pgvector requires PostgreSQL).

---

## Decision 3: LanceDB Incremental Update Pattern

**Decision**: Delete-then-insert (not upsert)

**Rationale**: LanceDB does not provide a primary-key upsert on arbitrary string keys. The
idiomatic approach is:
1. Load existing table; build `{path: mtime}` dict.
2. Walk vault; collect paths where mtime differs from stored value (or path is new).
3. Delete stale rows: `table.delete("path IN ('a.md', 'b.md', ...)")`.
4. Insert new rows: `table.add(list_of_dicts)`.

`merge_insert` (LanceDB ≥0.5) was considered but adds complexity without benefit for this use
case.

**Alternatives considered**: Drop and recreate entire table on every run — rejected (too slow;
O(N) embeds when only M notes changed).

---

## Decision 4: Embedding Text Format

**Decision**: `{title}\n\n{headings joined by \n}\n\n{body[:2000]}`

**Rationale**: Headings are high-signal and appear before any 2000-char truncation. Full body
for short notes; truncated for longer ones. bge-m3 handles mixed-language content in a single
string without preprocessing.

---

## Decision 5: CLI Framework

**Decision**: `click` with a `@click.group()` top-level and four `@cli.command()` decorators

**Rationale**: Clean subcommand pattern; handles argument parsing, help generation, and error
messages with minimal boilerplate. Consistent with the dependency list in DEVELOPMENT.md.

---

## Decision 6: Vault ID / Cache Path

**Decision**: `hashlib.sha256(str(vault_path.resolve()).encode()).hexdigest()[:8]`

Cache path: `~/.cache/vault-cli/<vault-id>/`

**Rationale**: Short, collision-resistant for personal vaults; deterministic across runs on the
same machine. Keeps index files off iCloud sync.

---

## Decision 7: LanceDB Table Schema

**Decision**: Define schema explicitly with `pyarrow`:

```python
import pyarrow as pa

SCHEMA = pa.schema([
    pa.field("path",    pa.string()),
    pa.field("title",   pa.string()),
    pa.field("mtime",   pa.float64()),
    pa.field("preview", pa.string()),
    pa.field("vector",  pa.list_(pa.float32(), 1024)),
])
```

**Rationale**: Explicit schema prevents type-inference errors on the first insert and on empty
tables.

---

## Decision 8: Wikilink Parsing Fallback

**Decision**: `re.findall(r'\[\[([^\|\]]+)', note_text)` — captures link target before any `|`
alias separator.

**Rationale**: Handles both `[[Note Title]]` and `[[Note Title|alias]]` forms. Only needed when
`metadata.json` is absent or stale; plugin data is preferred when available.

---

## Decision 9: Index Progress Output

**Decision**: Per-batch progress line to stderr using carriage-return overwrite:

```python
print(f"\rIndexing {done}/{total} notes...", end="", file=sys.stderr, flush=True)
# after last batch:
print(file=sys.stderr)  # newline
```

Final summary line to stdout: `print(f"Indexed {total} notes ({updated} updated).")`

**Rationale**: Keeps terminal output clean during long runs; stderr progress does not pollute
agent-parseable stdout (FR-015).

---

## Decision 10: Vault Root Resolution

**Decision**:
1. Check `VAULT_DIR` environment variable.
2. Walk up from `Path.cwd()` until a directory containing `.obsidian/` is found.
3. Raise a clear `SystemExit` with instructions if neither resolves.

**Rationale**: Matches the spec (FR-011) and DEVELOPMENT.md. Allows flexible invocation from
anywhere within the vault tree.

---

## Decision 11: Implementation Order

**Decision**: config+resolution → `read` → `neighbors` → `index` → `search`

**Rationale**: Each step validates the previous. `read` is trivial; `neighbors` needs no ML;
`index` builds the ML pipeline; `search` exercises the full stack. Matches DEVELOPMENT.md.

---

## All NEEDS CLARIFICATION: Resolved

No unresolved decisions remain. All technical choices are established above.
