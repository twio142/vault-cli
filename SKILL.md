---
name: vault-cli
description: Search and read a markdown directory. Use proactively before writing or reasoning about any topic the user may have notes on.
---

# Vault CLI

## Session Start

**Always run this unconditionally at the start of every session, before any other vault command** (use `run_in_background: true`):

```bash
vault index
```

This only re-embeds changed notes and takes a few seconds. Use `--force` only if results seem clearly wrong.

## Commands

```bash
vault read "<title or relative path>" [--head N]

vault search "<query>" [-k N]      # semantic search, default k=5
# returns: [{"path": "folder/Note.md", "block": "section-slug", "heading": "Section", "score": 0.74, "text": "..."}]
```

- `path` — note path relative to vault root
- `block` — section slug (`intro` for content before the first heading)
- `heading` — heading text; empty string for preamble blocks
- `score` — cosine similarity 0–1

## Workflow

**1. Find the note (when you don't have an exact path)**

If the user refers to a note by topic or description rather than giving you an exact path, run `vault search` first (see Commands). Use the `path` from the result for any subsequent `read` call. Never guess or invent a path — if the user didn't give you one, search for it.

**2. Search**

Natural language queries work. The model is multilingual — an English query surfaces Chinese or German notes on the same topic. Be specific: "motivation as a limited resource" beats "motivation". For broad topics, run multiple focused queries.

**3. Decide whether the block text is enough**

Each result contains the matched passage. If `text` answers the question, skip `read`. Use `read` when you need the full note structure, frontmatter, or sections that didn't surface in search. `--head 20` is useful for a quick scan before reading in full.

## Notes

- **Never call `vault read` with a guessed or invented path.** Always run `vault search` first and use the `path` field from the results. No exceptions.
- **If any `vault` command exits with an error, stop immediately and report the exact error to the user.** Do not fall back to `grep`, `find`, etc.
- Scores below 0.4 are noise. If all results are below 0.5, the vault likely has little on the topic — say so.
- Use `-k 10` or more for survey tasks or when initial results feel narrow.
- If `read` reports an ambiguous title, use the full `path` from the search result.
- If `vault` fails to find the vault, `VAULT_DIR` is likely not set. Tell the user and ask them to add it to their shell profile.
