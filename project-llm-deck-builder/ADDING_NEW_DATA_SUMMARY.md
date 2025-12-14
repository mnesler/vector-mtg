# Adding New Data - Quick Reference

## TL;DR

**Don't retrain from scratch unless you have to!**

| Data Type | Solution | Time | Command |
|-----------|----------|------|---------|
| Card metadata, prices | **RAG** | Setup once | Set up vector DB |
| 500-2000 new combos | **Continued training** | 15-30 min | `continue_training.py` |
| 2x-3x more data | **Retrain** | 1-3 hours | `train_qwen_lora.py` |

---

## The Three Options

### 🔍 Option 1: RAG (Retrieval-Augmented Generation)

**Best for:** Card lists, metadata, prices

```python
# Store cards in vector DB
# Retrieve at inference time
# No retraining needed!
```

**When to use:**
- ✅ Got full Scryfall card database (~25,000 cards)
- ✅ Card prices that change daily
- ✅ Legality info that changes with bans
- ✅ Any frequently-updated data

**Pros:** No retraining, real-time updates, infinite scalability

**Cons:** Requires vector DB setup

---

### ➕ Option 2: Continued Training

**Best for:** Small-to-medium combo/synergy additions

```bash
python training/continue_training.py \
  --existing_model models/qwen-mtg-lora \
  --new_data data/new_combos.jsonl \
  --old_train_file data/qwen_training.jsonl \
  --keep_old_ratio 0.3 \
  --epochs 1
```

**When to use:**
- ✅ Found 500-2000 new combo examples
- ✅ Want to add new synergy patterns
- ✅ Similar data types to existing training

**Pros:** Fast (15-30 min), builds on existing knowledge

**Cons:** Risk of forgetting old patterns, degrades after multiple updates

---

### 🔄 Option 3: Retrain From Scratch

**Best for:** Major data additions, new capabilities

```bash
cat data/*.jsonl > data/combined.jsonl
python training/train_qwen_lora.py \
  --train_file data/combined.jsonl \
  --epochs 3
```

**When to use:**
- ✅ You have 2x-3x more data than before
- ✅ Adding new task types (sideboarding, mulligan decisions)
- ✅ Model quality degraded after multiple continued trainings

**Pros:** Best quality, no forgetting, consistent across all data

**Cons:** Takes full training time (1-3 hours)

---

## Real-World Examples

### Example 1: Found full Scryfall database

**Data:** All 25,000+ MTG cards with metadata

**Answer:** Use RAG (no retraining)

**Why:** Too much to train on, changes frequently with new sets

---

### Example 2: Found 800 new combos from a forum

**Data:** 800 combo descriptions

**Answer:** Continued training

```bash
python continue_training.py \
  --new_data data/forum_combos.jsonl \
  --epochs 1
```

**Why:** Medium-sized addition, similar patterns to existing data

---

### Example 3: Got EDHREC data with 10,000+ deck lists

**Data:** 10,000 full Commander deck lists

**Answer:** Retrain from scratch

```bash
cat data/qwen_training.jsonl data/edhrec.jsonl > data/v2.jsonl
python train_qwen_lora.py --train_file data/v2.jsonl
```

**Why:** Large addition (>50% increase), new patterns (full decks vs combos)

---

## Decision Flowchart

```
Got new data?
│
├─ Is it metadata/facts that change frequently?
│  └─ Use RAG ✅
│
├─ Is it < 2000 examples of similar type?
│  └─ Use continued training ✅
│
└─ Is it 2x+ more data or new task types?
   └─ Retrain from scratch ✅
```

---

## Preventing "Catastrophic Forgetting"

When using continued training, model might forget old knowledge.

**Solutions:**

1. **Mix in old data** (30%):
   ```bash
   --old_train_file data/qwen_training.jsonl --keep_old_ratio 0.3
   ```

2. **Lower learning rate**:
   ```bash
   --learning_rate 1e-4  # Half of initial
   ```

3. **Fewer epochs**:
   ```bash
   --epochs 1  # Not 3
   ```

---

## Recommended Workflow

1. **Phase 1:** Initial training with Commander Spellbook (~7,500 examples)

2. **Phase 2:** Add card metadata via RAG (no retraining)

3. **Phase 3:** Monthly continued training with new combos (as you find them)

4. **Phase 4:** Major retrain every 6 months when you have 2x-3x data

---

## Quick Commands

### Continued Training
```bash
python training/continue_training.py \
  --existing_model models/qwen-mtg-lora \
  --new_data data/new_combos.jsonl \
  --old_train_file data/qwen_training.jsonl \
  --output_dir models/qwen-mtg-lora-v2 \
  --epochs 1
```

### Retrain From Scratch
```bash
cat data/*.jsonl > data/combined.jsonl
python training/train_qwen_lora.py \
  --train_file data/combined.jsonl \
  --output_dir models/qwen-mtg-lora-v2 \
  --epochs 3
```

### Test Both Models
```bash
# Test new model
python inference/test_qwen.py --model_path models/qwen-mtg-lora-v2 --test

# Compare with old model
python inference/test_qwen.py --model_path models/qwen-mtg-lora --test
```

---

## See Full Guide

For detailed explanation and code examples:
- **[docs/ADDING_NEW_DATA.md](./docs/ADDING_NEW_DATA.md)**
