#!/usr/bin/env python3
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
import warnings
from pathlib import Path

import click
import lancedb
import pyarrow as pa

warnings.filterwarnings("ignore", message=".*mean pooling.*")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCHEMA = pa.schema(
    [
        pa.field("path", pa.string()),
        pa.field("block", pa.string()),
        pa.field("title", pa.string()),
        pa.field("heading", pa.string()),
        pa.field("mtime", pa.float64()),
        pa.field("text", pa.string()),
        pa.field("vector", pa.list_(pa.float32(), 384)),
    ]
)

_EXCLUDED_DIRS = {".obsidian", "_assets"}

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def find_vault_root() -> Path:
    vault_env = os.environ.get("VAULT_DIR")
    if vault_env:
        p = Path(vault_env).expanduser().resolve()
        if (p / ".obsidian").is_dir():
            return p
        raise SystemExit(
            f"Error: VAULT_DIR='{vault_env}' but no .obsidian/ directory found there."
        )
    candidate = Path.cwd()
    while True:
        if (candidate / ".obsidian").is_dir():
            return candidate
        parent = candidate.parent
        if parent == candidate:
            break
        candidate = parent
    raise SystemExit(
        "Error: Vault not found. Set VAULT_DIR or run from within a vault directory."
    )


def resolve_path(vault_dir: Path, arg: str) -> Path:
    p = vault_dir / arg
    if p.exists():
        return p
    p = vault_dir / (arg + ".md")
    if p.exists():
        return p
    stem = Path(arg).stem
    matches = [
        f
        for f in vault_dir.rglob("*.md")
        if f.stem == stem
        and not (_EXCLUDED_DIRS & set(f.relative_to(vault_dir).parts[:-1]))
    ]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        listing = "\n  ".join(str(m.relative_to(vault_dir)) for m in sorted(matches))
        raise SystemExit(f"Error: Ambiguous title '{arg}'. Matches:\n  {listing}")
    raise FileNotFoundError(f"Note not found: {arg}")


def cache_dir(vault_path: Path) -> Path:
    vault_id = hashlib.sha256(str(vault_path.resolve()).encode()).hexdigest()[:8]
    d = Path.home() / ".cache" / "vault-cli" / vault_id
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------------------
# Metadata helpers
# ---------------------------------------------------------------------------


def load_metadata(vault_dir: Path, cache: Path | None = None) -> dict:
    # 1. Plugin-generated file (preferred — most up to date when Obsidian is open)
    meta_path = (
        vault_dir / ".obsidian" / "plugins" / "metadata-extractor" / "metadata.json"
    )
    if meta_path.exists():
        try:
            with open(meta_path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    # 2. Cached copy written by fetch_metadata_via_obsidian
    if cache is not None:
        cached = cache / "metadata.json"
        if cached.exists():
            try:
                with open(cached, encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
    return {}


_OBSIDIAN_EVAL_JS = (
    "const r={};"
    "for(const f of app.vault.getMarkdownFiles()){"
    "const c=app.metadataCache.getFileCache(f);"
    "if(!c)continue;"
    "r[f.name]={"
    "fileName:f.basename,"
    "relativePath:f.path,"
    "tags:(c.tags||[]).map(t=>t.tag.slice(1)),"
    "headings:(c.headings||[]).map(h=>({heading:h.heading,level:h.level})),"
    "links:(c.links||[]).map(l=>({link:l.link,"
    "relativePath:(app.metadataCache.getFirstLinkpathDest(l.link,f.path)||{path:l.link+'.md'}).path"
    "}))}}"
    "console.log(JSON.stringify(r));"
)


def fetch_metadata_via_obsidian(vault_name: str, cache: Path) -> dict:
    """Export full vault metadata via obsidian CLI eval and cache to disk."""
    try:
        result = subprocess.run(
            ["obsidian", f"vault={vault_name}", "eval", f"code={_OBSIDIAN_EVAL_JS}"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return {}
    if result.returncode != 0 or not result.stdout.strip():
        return {}
    try:
        metadata = json.loads(result.stdout.strip())
    except json.JSONDecodeError:
        return {}
    out = cache / "metadata.json"
    try:
        with open(out, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False)
    except OSError:
        pass
    return metadata


def build_backlinks(metadata: dict) -> dict:
    backlinks: dict = {}
    for _filename, meta in metadata.items():
        src = meta.get("relativePath", _filename)
        for link in meta.get("links", []):
            target = link.get("relativePath", "")
            if target:
                backlinks.setdefault(target, []).append(src)
    return backlinks


# ---------------------------------------------------------------------------
# Block splitting
# ---------------------------------------------------------------------------

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)", re.MULTILINE)
_MIN_BLOCK = 50
_MAX_BLOCK = 2000


def _slugify(text: str) -> str:
    s = text.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-") or "block"


def split_blocks(body: str, title: str) -> list:
    lines = body.splitlines(keepends=True)
    segments = []
    cur_heading, cur_lines = "", []
    for line in lines:
        m = _HEADING_RE.match(line)
        if m:
            segments.append((cur_heading, cur_lines))
            cur_heading, cur_lines = m.group(2).strip(), [line]
        else:
            cur_lines.append(line)
    segments.append((cur_heading, cur_lines))

    blocks, slug_counts = [], {}
    for heading, seg_lines in segments:
        text = "".join(seg_lines).strip()
        if len(text) < _MIN_BLOCK:
            continue
        base = _slugify(heading) if heading else "intro"
        count = slug_counts.get(base, 0) + 1
        slug_counts[base] = count
        slug = base if count == 1 else f"{base}-{count}"

        if len(text) <= _MAX_BLOCK:
            blocks.append({"block": slug, "heading": heading, "text": text})
        else:
            parts = [p for p in re.split(r"\n\n+", text) if p.strip()]
            sub, sub_len, idx = [], 0, 1
            for part in parts:
                if sub_len + len(part) > _MAX_BLOCK and sub:
                    chunk = "\n\n".join(sub).strip()
                    if len(chunk) >= _MIN_BLOCK:
                        blocks.append(
                            {
                                "block": f"{slug}-{idx}",
                                "heading": heading,
                                "text": chunk,
                            }
                        )
                        idx += 1
                    sub, sub_len = [part], len(part)
                else:
                    sub.append(part)
                    sub_len += len(part)
            if sub:
                chunk = "\n\n".join(sub).strip()
                if len(chunk) >= _MIN_BLOCK:
                    blocks.append(
                        {"block": f"{slug}-{idx}", "heading": heading, "text": chunk}
                    )
    return blocks


# ---------------------------------------------------------------------------
# Index helpers
# ---------------------------------------------------------------------------


def _table_names(db) -> list:
    r = db.list_tables()
    return getattr(r, "tables", None) or list(r)


def open_table(cache: Path, force: bool):
    db = lancedb.connect(str(cache))
    if force:
        return db.create_table("blocks", schema=SCHEMA, mode="overwrite")
    if "blocks" in _table_names(db):
        return db.open_table("blocks")
    return db.create_table("blocks", schema=SCHEMA)


def load_vaultignore(vault_dir: Path) -> list:
    ignore_file = vault_dir / ".vaultignore"
    if not ignore_file.exists():
        return []
    patterns = []
    with open(ignore_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.append(line)
    return patterns


def is_ignored(rel: Path, patterns: list) -> bool:
    rel_str = rel.as_posix()
    for pattern in patterns:
        if pattern.endswith("/"):
            dir_name = pattern.rstrip("/")
            if any(fnmatch.fnmatch(part, dir_name) for part in rel.parts[:-1]):
                return True
        else:
            if (
                fnmatch.fnmatch(rel.name, pattern)
                or fnmatch.fnmatch(rel_str, pattern)
                or any(fnmatch.fnmatch(part, pattern) for part in rel.parts[:-1])
            ):
                return True
    return False


def walk_vault(vault_dir: Path) -> list:
    ignore_patterns = load_vaultignore(vault_dir)
    result = []
    for p in vault_dir.rglob("*.md"):
        rel = p.relative_to(vault_dir)
        if set(rel.parts[:-1]) & _EXCLUDED_DIRS:
            continue
        if ignore_patterns and is_ignored(rel, ignore_patterns):
            continue
        result.append(p)
    return result


def diff_notes(table, vault_dir: Path, all_paths: list) -> list:
    try:
        df = table.to_pandas()
        stored = {} if df.empty else dict(zip(df["path"], df["mtime"]))
    except Exception:
        stored = {}
    changed = []
    for p in all_paths:
        rel = str(p.relative_to(vault_dir))
        if rel not in stored or stored[rel] != p.stat().st_mtime:
            changed.append(p)
    return changed


def embed_blocks(model, vault_dir: Path, paths: list, metadata: dict) -> list:
    all_blocks = []
    for p in paths:
        rel = str(p.relative_to(vault_dir))
        meta = metadata.get(p.name, metadata.get(rel, {}))
        title = meta.get("fileName", p.stem)
        try:
            body = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            print(f"  skipping {rel} (not readable)", file=sys.stderr)
            continue
        mtime = p.stat().st_mtime
        for blk in split_blocks(body, title):
            all_blocks.append({"path": rel, "title": title, "mtime": mtime, **blk})

    total = len(all_blocks)
    texts = [f"{b['title']}\n\n{b['heading']}\n\n{b['text']}" for b in all_blocks]
    rows, done = [], 0
    for i in range(0, total, 32):
        batch = texts[i : i + 32]
        vecs = list(model.embed(batch))
        for j, vec in enumerate(vecs):
            rows.append({**all_blocks[i + j], "vector": vec.tolist()})
        done += len(batch)
        print(
            f"\rIndexing {done}/{total} blocks...", end="", file=sys.stderr, flush=True
        )
    if total > 0:
        print(file=sys.stderr)
    return rows


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@click.group()
def cli():
    pass


@cli.command("index")
@click.option("--force", is_flag=True, default=False)
def cmd_index(force):
    vault = find_vault_root()
    cache = cache_dir(vault)
    table = open_table(cache, force)
    all_paths = walk_vault(vault)
    total = len(all_paths)

    all_rels = {str(p.relative_to(vault)) for p in all_paths}

    if force:
        changed = all_paths
    else:
        changed = diff_notes(table, vault, all_paths)
        try:
            df = table.to_pandas()
            if not df.empty:
                deleted = set(df["path"]) - all_rels
                if deleted:
                    escaped = ", ".join(
                        "'" + r.replace("'", "''") + "'" for r in deleted
                    )
                    table.delete(f"path IN ({escaped})")
        except Exception:
            pass

    updated = len(changed)
    if updated == 0:
        click.echo(f"Indexed {total} notes (0 updated, 0 blocks).")
        return

    if not force and changed:
        rel_paths = [str(p.relative_to(vault)) for p in changed]
        escaped = ", ".join("'" + r.replace("'", "''") + "'" for r in rel_paths)
        table.delete(f"path IN ({escaped})")

    from fastembed import TextEmbedding

    model = TextEmbedding("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    metadata = load_metadata(vault, cache)
    rows = embed_blocks(model, vault, changed, metadata)
    table.add(rows)
    click.echo(f"Indexed {total} notes ({updated} updated, {len(rows)} blocks).")


@cli.command("search")
@click.argument("query")
@click.option("--k", default=5, type=int)
def cmd_search(query, k):
    vault = find_vault_root()
    cache = cache_dir(vault)
    db = lancedb.connect(str(cache))
    if "blocks" not in _table_names(db):
        click.echo("Error: No index found. Run 'vault index' first.", err=True)
        sys.exit(1)
    table = db.open_table("blocks")

    from fastembed import TextEmbedding

    model = TextEmbedding("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    vec = list(model.embed([query]))[0]

    results = table.search(vec).metric("cosine").limit(k).to_list()  # type: ignore[attr-defined]
    output = [
        {
            "path": r["path"],
            "block": r["block"],
            "heading": r["heading"],
            "score": round(1.0 - r["_distance"], 4),
            "text": r["text"],
        }
        for r in results
    ]
    click.echo(json.dumps(output, ensure_ascii=False))


@cli.command("neighbors")
@click.argument("note_path")
def cmd_neighbors(note_path):
    vault = find_vault_root()
    try:
        abs_path = resolve_path(vault, note_path)
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    rel = str(abs_path.relative_to(vault))
    cache = cache_dir(vault)
    metadata = load_metadata(vault, cache)

    if not metadata:
        vault_name = os.environ.get("VAULT_NAME", vault.name)
        metadata = fetch_metadata_via_obsidian(vault_name, cache)

    if metadata:
        meta = metadata.get(abs_path.name, metadata.get(rel, {}))
        links = [
            lnk.get("relativePath", "")
            for lnk in meta.get("links", [])
            if lnk.get("relativePath")
        ]
        backlinks_map = build_backlinks(metadata)
        backlinks = backlinks_map.get(rel, backlinks_map.get(abs_path.name, []))
    else:
        click.echo(
            "Warning: Could not retrieve link data. Is Obsidian running?", err=True
        )
        links, backlinks = [], []

    click.echo(
        json.dumps(
            {
                "links": sorted(set(links)),
                "backlinks": sorted(set(backlinks)),
            },
            ensure_ascii=False,
        )
    )


@cli.command("read")
@click.argument("note_path")
@click.option("--head", default=None, type=int)
def cmd_read(note_path, head):
    vault = find_vault_root()
    try:
        abs_path = resolve_path(vault, note_path)
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    content = abs_path.read_text(encoding="utf-8", errors="replace")
    if head is not None:
        click.echo("\n".join(content.splitlines()[:head]))
    else:
        click.echo(content, nl=False)


if __name__ == "__main__":
    cli()
