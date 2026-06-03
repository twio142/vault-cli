# vault-cli

A command-line tool for AI agents to search and navigate an Obsidian vault.

## Install

```bash
pip install sentence-transformers lancedb pyarrow click
```

The first `vault index` run downloads the embedding model (~2 GB). All subsequent runs are offline.

## Usage

### Point to your vault

Either set `VAULT_DIR`:

```bash
export VAULT_DIR=/path/to/your/vault
```

Or run commands from anywhere inside your vault directory — it's detected automatically.

### Build the index

```bash
python vault.py index
```

Only re-embeds notes that changed since the last run. Use `--force` to rebuild from scratch.

### Search

```bash
python vault.py search "machine learning optimization"
python vault.py search "your query" --k 10
```

Returns tab-separated results: `path  score  preview`. Cross-lingual queries work — an English query will match Chinese or Japanese notes on the same topic.

### Read a note

```bash
python vault.py read "Note Title"
python vault.py read "folder/Note Title.md" --head 20
```

### Explore links

```bash
python vault.py neighbors "Note Title"
```

Shows outgoing links and backlinks for a note.

## Notes

- If two notes share the same title in different folders, use the full relative path to disambiguate.
- `vault neighbors` requires Obsidian to be running if the metadata plugin hasn't generated its cache yet.
- Set `VAULT_NAME` if your Obsidian vault name differs from its folder name.
