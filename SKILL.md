---
name: vault-cli
description: Search, read, and navigate an Obsidian vault. Use proactively before writing or reasoning about any topic the user may have notes on.
---

# Vault CLI

## Session Start

Run a quick incremental refresh before using `vault` **for the first time** (use `run_in_background: true`):

```bash
vault index
```

This only re-embeds changed notes and takes a few seconds. Use `--force` only if results seem clearly wrong.

## Commands

```bash
vault search "<query>" [-k N]      # semantic search, default k=5
vault read "<title or relative path>" [--head N]
vault neighbors "<title or relative path>"
```

`search` returns a JSON array:

```json
[{"path": "folder/Note.md", "block": "section-slug", "heading": "Section", "score": 0.74, "text": "..."}]
```

- `path` — note path relative to vault root
- `block` — section slug (`intro` for content before the first heading)
- `heading` — heading text; empty string for preamble blocks
- `score` — cosine similarity 0–1

## Workflow

**1. Search**

Natural language queries work. The model is multilingual — an English query surfaces Chinese or German notes on the same topic.

```bash
vault search "epistemic humility" -k 5
```

Be specific. "motivation as a limited resource" beats "motivation". For broad topics, run multiple focused queries.

**2. Decide whether the block text is enough**

Each result contains the matched passage. If `text` answers the question, skip `read`. Use `read` when you need the full note structure, frontmatter, or sections that didn't surface in search. `--head 20` is useful for a quick scan before reading in full.

**3. Expand via wikilinks when useful**

```bash
vault neighbors "Epistemic Humility"
# returns: {"links": [...], "backlinks": [...]}
```

Use when a note looks like a hub, or when you want to explore a topic cluster beyond what search surfaces.

## Notes

- Scores below 0.4 are noise. If all results are below 0.5, the vault likely has little on the topic — say so.
- Use `-k 10` or more for survey tasks or when initial results feel narrow.
- If `read` or `neighbors` reports an ambiguous title, use the full `path` from the search result.
- If `vault` fails to find the vault, `VAULT_DIR` is likely not set. Tell the user and ask them to add it to their shell profile.
