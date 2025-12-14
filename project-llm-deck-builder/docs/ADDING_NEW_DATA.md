# Adding New Data to Your Trained Model

This guide explains how to incorporate new MTG data into your trained Qwen model **without starting from scratch**.

## Quick Decision Tree

```
Found new data?
│
├─ Is it card metadata (names, types, prices)?
│  └─ ✅ Use RAG (no retraining needed)
│
├─ Is it new combos/synergies (<1000 examples)?
│  └─ ✅ Use continued training
│
├─ Do you have 2x-3x more data than before?
│  └─ ✅ Retrain from scratch
│
└─ Is it a completely new task type?
   └─ ✅ Retrain from scratch
```

---

## Option 1: RAG (Retrieval-Augmented Generation)

**Best for:** Card lists, metadata, frequently updated information

### When to Use RAG

- ✅ Card database (names, types, mana costs, colors)
- ✅ Card prices (change daily)
- ✅ Legality information (changes with bans/unbans)
- ✅ Large card pools (thousands of cards)
- ✅ Real-time data that updates frequently

### How It Works

Instead of training the model on card data, you:
1. Store cards in a vector database
2. Retrieve relevant cards at inference time
3. Pass them as context to your existing model

### Implementation Example

```python
from sentence_transformers import SentenceTransformer
import chromadb

# 1. Create embeddings for all cards
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

cards = [
    {
        "name": "Sol Ring",
        "type": "Artifact",
        "mana_cost": "{1}",
        "text": "{T}: Add {C}{C}",
        "price": 1.50
    },
    # ... more cards
]

# 2. Store in vector database
client = chromadb.Client()
collection = client.create_collection("mtg_cards")

for card in cards:
    # Create searchable text
    card_text = f"{card['name']} {card['type']} {card['text']}"

    collection.add(
        documents=[card_text],
        metadatas=[card],
        ids=[card['name']]
    )

# 3. Retrieve at inference time
def get_recommendations_with_rag(user_query, model, tokenizer):
    # Search for relevant cards
    results = collection.query(
        query_texts=[user_query],
        n_results=5
    )

    # Format as context
    card_context = "\n".join([
        f"- {m['name']} ({m['type']}): {m['text']} - ${m['price']}"
        for m in results['metadatas'][0]
    ])

    # Add to prompt
    messages = [
        {"role": "system", "content": "You are an MTG deck building assistant."},
        {"role": "user", "content": f"Here are some relevant cards:\n{card_context}\n\n{user_query}"}
    ]

    # Generate response with your fine-tuned model
    return generate_response(model, tokenizer, messages)

# Usage
response = get_recommendations_with_rag(
    "What are good mana rocks under $5?",
    model,
    tokenizer
)
```

### Pros & Cons

**Pros:**
- ✅ No retraining required
- ✅ Can update data in real-time
- ✅ Works with massive card databases
- ✅ Model always has access to latest info

**Cons:**
- ❌ Requires vector database setup
- ❌ Slightly more complex architecture
- ❌ Model doesn't "memorize" card relationships

---

## Option 2: Continued Training (Incremental Updates)

**Best for:** New combos, synergies, small-to-medium data additions

### When to Use Continued Training

- ✅ Found 500-2000 new combo examples
- ✅ Discovered new synergy patterns
- ✅ Want to teach model new deck archetypes
- ✅ Adding similar types of examples to existing data

### How It Works

Continue training your existing LoRA model with new data:

```bash
# Step 1: Format new data
python training/format_qwen_data.py \
  --db-connection "postgresql://localhost/new_commander_data" \
  --output data/new_combos.jsonl \
  --combo-samples 1000

# Step 2: Continue training
python training/continue_training.py \
  --existing_model models/qwen-mtg-lora \
  --new_data data/new_combos.jsonl \
  --old_train_file data/qwen_training.jsonl \
  --keep_old_ratio 0.3 \
  --output_dir models/qwen-mtg-lora-v2 \
  --epochs 1 \
  --learning_rate 1e-4
```

### Key Parameters Explained

- `--keep_old_ratio 0.3`: Include 30% of old data to prevent forgetting
- `--epochs 1`: Only 1-2 epochs for continued training (not 3+)
- `--learning_rate 1e-4`: Lower than initial training (2e-4) to avoid disrupting learned patterns

### Preventing Catastrophic Forgetting

**Catastrophic forgetting** = Model forgets old knowledge when learning new patterns.

**Solutions:**

1. **Mix in old data** (recommended):
   ```bash
   --old_train_file data/qwen_training.jsonl --keep_old_ratio 0.3
   ```

2. **Use lower learning rate**:
   ```bash
   --learning_rate 1e-4  # Half of initial 2e-4
   ```

3. **Train for fewer epochs**:
   ```bash
   --epochs 1  # Not 3+
   ```

### Pros & Cons

**Pros:**
- ✅ Faster than training from scratch (15-30 min vs 1-3 hours)
- ✅ Builds on existing knowledge
- ✅ Can add data incrementally as you find it

**Cons:**
- ❌ Risk of catastrophic forgetting if not careful
- ❌ Model quality may degrade over multiple updates
- ❌ After 3-4 updates, better to retrain from scratch

---

## Option 3: Retrain From Scratch

**Best for:** Major data additions, new task types, quality improvements

### When to Retrain From Scratch

- ✅ You have 2x-3x more data than before
- ✅ Adding fundamentally new capabilities (e.g., sideboarding, mulligan decisions)
- ✅ Model quality has degraded after multiple continued trainings
- ✅ You want to ensure best possible quality

### How It Works

Merge all data and train from the base Qwen model:

```bash
# Step 1: Merge datasets
cat data/qwen_training.jsonl \
    data/new_combos.jsonl \
    data/edhrec_data.jsonl \
    > data/qwen_v2_combined.jsonl

# Step 2: Train from scratch
python training/train_qwen_lora.py \
  --model_name Qwen/Qwen2.5-1.5B-Instruct \
  --train_file data/qwen_v2_combined.jsonl \
  --output_dir models/qwen-mtg-lora-v2 \
  --epochs 3 \
  --batch_size 4
```

### Pros & Cons

**Pros:**
- ✅ No catastrophic forgetting
- ✅ Consistent quality across all data
- ✅ Model learns all patterns equally well

**Cons:**
- ❌ Takes full training time (1-3 hours)
- ❌ Wastes compute if you only have small updates

---

## Recommended Workflow

### Phase 1: Initial Training (You've done this)

```bash
# Train on Commander Spellbook data
python train_qwen_lora.py --train_file data/qwen_training.jsonl
```

**Result:** Model v1 with ~7,500 examples

---

### Phase 2: Add Card Metadata (RAG)

```bash
# Set up vector database for card lookups
# No retraining needed!
```

**Result:** Model v1 + RAG for card data

---

### Phase 3: Incremental Updates (Every 1-2 months)

```bash
# Continue training with new combos
python continue_training.py \
  --existing_model models/qwen-mtg-lora \
  --new_data data/month2_combos.jsonl \
  --old_train_file data/qwen_training.jsonl \
  --epochs 1
```

**Result:** Model v1.1, v1.2, v1.3... with incremental improvements

---

### Phase 4: Major Update (Every 6 months or when you have 2x data)

```bash
# Retrain from scratch with all accumulated data
cat data/*.jsonl > data/qwen_v2_full.jsonl
python train_qwen_lora.py --train_file data/qwen_v2_full.jsonl
```

**Result:** Model v2 with all data, fresh training

---

## Examples by Data Type

### Example 1: You Found EDHREC Data

**Data:** 10,000 popular Commander deck lists

**Recommendation:** Retrain from scratch

```bash
# Format EDHREC data
python format_edhrec_data.py --output data/edhrec.jsonl

# Merge with existing
cat data/qwen_training.jsonl data/edhrec.jsonl > data/qwen_v2.jsonl

# Retrain
python train_qwen_lora.py --train_file data/qwen_v2.jsonl --epochs 3
```

**Why:** This is a large amount of new data (>50% increase) with new patterns (full deck lists vs individual combos). Retraining ensures quality.

---

### Example 2: You Found 500 New Combos

**Data:** 500 new combo descriptions from a forum

**Recommendation:** Continued training

```bash
# Format new combos
python format_new_combos.py --output data/new_500.jsonl

# Continue training
python continue_training.py \
  --existing_model models/qwen-mtg-lora \
  --new_data data/new_500.jsonl \
  --old_train_file data/qwen_training.jsonl \
  --keep_old_ratio 0.3 \
  --epochs 1
```

**Why:** Small-to-medium data addition with similar patterns. Continued training is faster and sufficient.

---

### Example 3: You Got Full Scryfall Card Database

**Data:** All ~25,000 MTG cards with metadata

**Recommendation:** RAG (no training)

```python
# Load into vector database
import chromadb
client = chromadb.Client()
collection = client.create_collection("scryfall_cards")

for card in scryfall_cards:
    collection.add(
        documents=[f"{card['name']} {card['type_line']} {card['oracle_text']}"],
        metadatas=[card],
        ids=[card['id']]
    )

# Use at inference time
def answer_with_card_knowledge(query):
    relevant_cards = collection.query(query, n_results=10)
    # Pass to model as context
```

**Why:** Too much data to train on, changes frequently (new sets), and metadata is better suited for retrieval than memorization.

---

## Monitoring Model Quality

After adding new data, always test:

```bash
# Test updated model
python inference/test_qwen.py \
  --model_path models/qwen-mtg-lora-v2 \
  --test

# Compare with original
python inference/test_qwen.py \
  --model_path models/qwen-mtg-lora \
  --test
```

### Quality Checklist

- ✅ Model still answers old questions correctly (no forgetting)
- ✅ Model handles new data types well
- ✅ Response quality is consistent
- ✅ No degradation in fluency or coherence

If quality degrades → Retrain from scratch with all data

---

## Summary

| Scenario | Solution | Time | Pros |
|----------|----------|------|------|
| Card metadata, prices | RAG | Setup: 1 hour | No retraining, real-time updates |
| 500-2000 new examples | Continued training | 15-30 min | Fast, incremental |
| 2x-3x more data | Retrain from scratch | 1-3 hours | Best quality |
| New task types | Retrain from scratch | 1-3 hours | Learns new patterns well |

**General rule:** Start with RAG for data that changes. Use continued training for small updates. Retrain from scratch when you have major additions.
