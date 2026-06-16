# vault-cli

A command-line tool for AI agents to search and read a directory of Markdown notes.

## Install

Requires [uv](https://docs.astral.sh/uv/). Dependencies are declared inline and managed automatically.

```bash
ln -s "$PWD/vault.py" /usr/local/bin/vault
```

The first run downloads dependencies and the embedding model (~470 MB). All subsequent runs are offline.

## Usage

### Point to your notes

Either set `VAULT_DIR`:

```bash
export VAULT_DIR=/path/to/your/notes
```

Or run commands from anywhere inside your notes directory — it's detected automatically by looking for a `.vaultignore` file (up to 3 directory layers up).

### Build the index

```bash
vault index
```

Only re-embeds notes that changed since the last run. Use `--force` to rebuild from scratch.

### Search

```bash
vault search "machine learning optimization"
vault search "your query" -k 10
```

Returns a JSON array of `{path, block, heading, score, text}` objects — results point to specific sections within notes, not just the note as a whole. Cross-lingual queries work — an English query will match Chinese or Japanese notes on the same topic.

### Read a note

```bash
vault read "Note Title"
vault read "folder/Note Title.md" --head 20
```

### Exclude notes from the index

Place a `.vaultignore` file in your vault root with gitignore-style patterns to exclude notes from indexing.

## Agent Skill

`SKILL.md` is a Claude agent skill for vault access. To install, copy it into your Claude skills directory:

```bash
cp SKILL.md ~/.claude/skills/vault-cli/SKILL.md
```

## Notes

- If two notes share the same title in different folders, use the full relative path to disambiguate.
