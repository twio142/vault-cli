# Quickstart: vault-cli

**Branch**: `001-vault-obsidian-cli` | **Date**: 2026-06-03

---

## Prerequisites

- Python 3.11+
- ~2 GB free disk space (one-time model download on first `vault index`)

---

## Install Dependencies

```bash
pip install sentence-transformers lancedb pyarrow click
```

---

## Configure Vault Location

Either set an environment variable:

```bash
export VAULT_DIR=/path/to/your/obsidian/vault
```

Or navigate to anywhere inside your vault before running commands — vault-cli walks up the
directory tree to find the `.obsidian/` directory automatically.

---

## Build the Index

Run once (and again after adding/modifying notes):

```bash
python vault.py index
# Indexing 32/342 notes...   (progress to stderr)
# Indexed 342 notes (342 updated).
```

Subsequent runs only re-embed changed notes:

```bash
python vault.py index
# Indexed 342 notes (3 updated).
```

Force a full rebuild:

```bash
python vault.py index --force
```

---

## Search Notes

```bash
python vault.py search "machine learning optimization"
# folder/ML Basics.md    0.8921    This note covers gradient descent and...
# Papers/SGD paper.md    0.8104    Stochastic gradient descent is a method...
```

Return more results:

```bash
python vault.py search "machine learning" --k 10
```

Cross-lingual queries work out of the box — an English query will match Chinese or German notes
on the same topic.

---

## Read a Note

```bash
python vault.py read "ML Basics"
# (full note content printed to stdout)
```

Read with extension or relative path:

```bash
python vault.py read "folder/ML Basics.md"
```

Read only the first 20 lines:

```bash
python vault.py read "ML Basics" --head 20
```

---

## Browse Note Links

```bash
python vault.py neighbors "ML Basics"
# links:
#   Papers/SGD paper.md
#   folder/Neural Networks.md
# backlinks:
#   Projects/Research Plan.md
```

---

## Typical Agent Workflow

```bash
# 1. Find relevant notes
python vault.py search "transformer attention mechanism" --k 5

# 2. Read the top result
python vault.py read "folder/Attention Is All You Need.md"

# 3. Discover related notes
python vault.py neighbors "folder/Attention Is All You Need.md"

# 4. Read a backlinked note
python vault.py read "Projects/NLP Research.md"
```

---

## Validation Checklist

After implementation, verify each command manually:

- [ ] `vault index` indexes all notes and prints `Indexed N notes (M updated).`
- [ ] `vault index` (second run, no changes) prints `Indexed N notes (0 updated).`
- [ ] `vault index --force` re-embeds all notes
- [ ] `vault search "topic"` returns tab-separated results ordered by score
- [ ] `vault search "english query"` returns Chinese/other-language notes on same topic
- [ ] `vault read "Note Title"` prints full note content
- [ ] `vault read "Note Title" --head 5` prints exactly 5 lines
- [ ] `vault neighbors "Note Title"` prints `links:` and `backlinks:` sections
- [ ] Ambiguous bare title returns error listing all matches
- [ ] Missing note returns error to stderr, nothing to stdout
- [ ] `VAULT_DIR` env var overrides auto-detection
- [ ] Running from a subdirectory inside the vault auto-detects the root
