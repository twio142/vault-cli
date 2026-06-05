# Quickstart: Block-Level Search

## Validation Scenarios

### 1. Block-level result for a specific section

**Setup**: Pick a note with multiple `##` headings on distinct topics.

```bash
./vault.py search "your topic here" --k 5
```

**Expected**: The top result's `block` and `heading` fields identify the specific section, not the whole note. The `text` field contains only that section's content.

---

### 2. Multiple blocks from the same note

**Setup**: Pick a note where different sections cover different topics.

```bash
./vault.py search "topic from section A" --k 5
```

**Expected**: Results include the relevant section block, not the note twice. Other blocks from the same note may appear lower in results if they are semantically related.

---

### 3. Incremental re-index

**Setup**: Run index, then edit one note, then run index again.

```bash
./vault.py index
# edit one note
./vault.py index
```

**Expected**: Second run reports only the edited note's blocks as updated, not all blocks.

---

### 4. Idempotency

```bash
./vault.py index
./vault.py index
```

**Expected**: Second run reports `0 updated`.

---

### 5. Cross-lingual block search

```bash
./vault.py search "机器学习" --k 5
```

**Expected**: Returns English-language blocks about machine learning with scores above 0.5.

---

### 6. Note with no headings

**Setup**: Find a note with no `#` headings.

```bash
./vault.py search "unique phrase from that note"
```

**Expected**: Result has `block: "intro"` and `heading: ""`.
