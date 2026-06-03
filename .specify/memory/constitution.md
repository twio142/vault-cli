<!--
SYNC IMPACT REPORT
==================
Version change: [UNVERSIONED] → 1.0.0
Modified principles: none (initial fill)
Added sections: Core Principles (I–V), Technical Constraints, Development Workflow, Governance
Removed sections: none
Templates requiring updates:
  ✅ .specify/templates/plan-template.md — Constitution Check gates align with principles below
  ✅ .specify/templates/spec-template.md — no changes required; structure is principle-agnostic
  ✅ .specify/templates/tasks-template.md — no changes required; task format is principle-agnostic
Deferred items: none
-->

# vault-cli Constitution

## Core Principles

### I. Simplicity

The implementation MUST remain a single Python file (`vault.py`). No package structure, no helper
modules, no abstractions beyond what the task at hand requires. Complexity MUST be justified by a
concrete present need — not anticipated future needs. Three similar lines are preferable to a
premature abstraction.

**Rationale**: The target scope is ~250 lines. Package structure and layering add maintenance
overhead with no benefit at this scale.

### II. Offline-First

After the one-time model download, vault-cli MUST function with no network access. There MUST be
no background daemon, no server process, and no remote service dependency in the hot path. The tool
is invoked as a one-shot subprocess; it starts, runs, and exits.

**Rationale**: Agents call vault-cli as a shell tool during tasks. Reliability requires zero
external dependencies at runtime.

### III. Machine-Readable Output

All command output MUST be structured for programmatic consumption by AI agents:
- `vault search`: one result per line, tab-separated `<path>\t<score>\t<preview>`
- `vault neighbors`: labeled sections (`links:`, `backlinks:`) with one path per line
- `vault index`: single summary line (`Indexed N notes (M updated).`)
- `vault read`: raw note content, no wrapper

Errors MUST go to stderr. Stdout MUST contain only the structured result.

**Rationale**: The primary consumer is an AI agent parsing shell output, not a human reading a
terminal.

### IV. Incremental & Idempotent

`vault index` MUST diff against stored mtimes and only re-embed changed notes. Running it twice in
a row MUST produce the same result with zero re-embeds on the second run. The `--force` flag exists
for when a full rebuild is explicitly needed.

Fallback strategies are REQUIRED wherever a primary data source may be stale: `metadata.json`
absent → parse `[[...]]` from raw note text.

**Rationale**: Vault indexing involves a slow ML model. Needless re-embedding degrades agent
workflow latency.

### V. Vault Safety

vault-cli MUST NEVER write to the vault directory. The only write locations are:
- `~/.cache/vault-cli/<vault-id>/` — LanceDB index files

Index files MUST live outside the vault to prevent iCloud sync from thrashing on LanceDB's binary
files during re-index.

**Rationale**: The vault is the user's primary data. Accidental writes or sync conflicts could
corrupt notes.

## Technical Constraints

- **Language**: Python 3.11+
- **Dependencies**: `sentence-transformers`, `lancedb`, `pyarrow`, `click` — no others
- **Embedding model**: `BAAI/bge-m3`, 1024-dim, `normalize_embeddings=True`
- **Index location**: `~/.cache/vault-cli/<vault-id>/`, where `<vault-id>` is a short hash of the
  resolved vault path
- **Vault discovery**: `VAULT_DIR` env var → walk up from cwd until `.obsidian/` found → error
- **Embedding text**: `{title}\n\n{headings}\n\n{body[:2000]}`
- **Batch size**: 32 during indexing

No new dependencies may be added without amending this constitution.

## Development Workflow

Implementation MUST proceed in this order, testing each command against the live vault before
moving on:

1. Config + path resolution
2. `vault read`
3. `vault neighbors`
4. `vault index`
5. `vault search`

Each command MUST be validated against the live vault before the next is begun. There are no
automated tests; correctness is verified by manual invocation against real vault data.

## Governance

This constitution supersedes all other practices for vault-cli. Amendments require:
1. A concrete motivation (not speculation about future needs)
2. A version bump per semantic versioning:
   - MAJOR: removal or redefinition of a principle
   - MINOR: new principle or section added
   - PATCH: clarification or wording fix
3. Propagation of changes to all affected templates

All implementation decisions MUST be checked against the five Core Principles before code is
written. Violations require justification in the plan's Complexity Tracking table.

**Version**: 1.0.0 | **Ratified**: 2026-06-03 | **Last Amended**: 2026-06-03
