# vault-cli Developer Guide

`vault-cli` is an offline-first, single-file semantic search and navigation tool for Obsidian vaults, built specifically for AI agents and CLI users.

## 🛠 Commands & Operations

This project is structured as a self-contained, single-file CLI (`vault.py`) powered by `uv`.

### Running Commands (via uv script)
```bash
# General help / Usage
./vault.py -h

# Index the vault (incremental by default, use -f/--force to rebuild)
./vault.py index
./vault.py index --force

# Preview indexing changes without writing
./vault.py index --dry-run

# Semantic search for blocks (returns JSON array of results)
./vault.py search "neural network layers"
./vault.py search "your query" -k 10

# Read note contents
./vault.py read "Note Title"
./vault.py read "folder/Note Title.md" --head 20
```

---

## 💻 Tech Stack & Dependencies

- **Runtime**: Python 3.11+
- **Execution Manager**: `uv` (script runner with inline dependency definitions)
- **Vector DB**: `lancedb` (embedded serverless vector database)
- **Embeddings**: `fastembed` (Sentence Transformers `paraphrase-multilingual-MiniLM-L12-v2`, cached locally in `~/.cache/vault-cli/models/`)
- **CLI Framework**: `click`
- **Data Serialization**: `pyarrow` (underpinning LanceDB and Arrow tables)

---

## 📏 Architecture & Constraints

1. **Single-File Principle**: All source code and logic must reside entirely in `vault.py`. No external modules or helper files should be created.
2. **Offline-First**: No remote API calls are made during indexing or searching. Model downloads are cached on first run.
3. **Vault Safety**: The semantic index and model weights are stored outside the vault (under `~/.cache/vault-cli/`) to avoid conflict with Obsidian sync or cloud backups.
4. **Vault Root Auto-detection**:
   - `VAULT_DIR` environment variable takes precedence.
   - Otherwise, the tool traverses up to **3 layers of directories** from the current working directory (CWD) looking for a `.vaultignore` file to find the vault root.
5. **Ignore Patterns**: Uses standard glob patterns specified in `.vaultignore` to filter out files. Folders like `.git`, `.obsidian`, `.trash`, etc., are hard-excluded by default.
6. **Error Handling**: 
   - Print all descriptive/actionable errors to `stderr` and exit with non-zero status code where appropriate.
   - Ambiguous bare titles matching multiple paths should display all candidate paths in the error.

---

## 🎨 Coding & Style Guidelines

- **Imports**: Clean import groups (stdlib, third-party). Keep startup speed high by postponing heavy imports (`fastembed`) to command execution time.
- **Error Messages**: Always write clear, user-friendly error messages that guide the user on how to resolve the issue (e.g. instructing them to set `VAULT_DIR` or run `vault index`).
- **Encoding**: Always read and write files with explicit `encoding="utf-8"` and proper error handling (`errors="replace"` for robust text parsing).
- **Format**: Follow standard PEP 8 coding style guidelines. Keep formatting clean and consistent.
- **Testing**: Per feature specification, manual verification of commands is preferred as there is no automated test suite. Check changes against a live vault.
