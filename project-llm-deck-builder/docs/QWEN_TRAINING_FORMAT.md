# Qwen/Qwen2.5-1.5B-Instruct Training Data Format

## Overview

Qwen models expect conversational training data in a specific chat format. This document explains how to format your MTG deck building data for fine-tuning Qwen/Qwen2.5-1.5B-Instruct.

## Data Format Requirements

### Chat Message Format

Qwen uses a conversational format with three roles:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are an expert Magic: The Gathering deck building assistant."
    },
    {
      "role": "user",
      "content": "How does the Hullbreaker Horror + Sol Ring combo work?"
    },
    {
      "role": "assistant",
      "content": "This combo produces infinite colorless mana. Here's how it works: ..."
    }
  ]
}
```

### Role Descriptions

- **system**: Sets the context and behavior of the model. Use this to define the assistant's expertise.
- **user**: The user's question or request.
- **assistant**: The model's expected response.

## File Format

Save training data as **JSONL** (JSON Lines):
- One JSON object per line
- Each line is a complete training example
- UTF-8 encoding

Example file (`qwen_training.jsonl`):
```jsonl
{"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
{"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

## Training Example Types

### 1. Combo Explanations

**Goal**: Teach the model to explain MTG combos step-by-step.

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are an expert Magic: The Gathering deck building assistant specializing in Commander and Standard formats."
    },
    {
      "role": "user",
      "content": "How does the Hullbreaker Horror + Sol Ring combo work?"
    },
    {
      "role": "assistant",
      "content": "This combo produces: Infinite colorless mana, Infinite mana, Infinite storm count.\n\nHow it works:\n1. With Hullbreaker Horror on the battlefield and Sol Ring in hand, cast Sol Ring by paying {1}.\n2. Hullbreaker Horror's ability triggers, allowing you to return Sol Ring to your hand.\n3. Repeat steps 1-2 infinitely to generate infinite colorless mana.\n\nMana required: {1}"
    }
  ]
}
```

### 2. Card Synergy Questions

**Goal**: Teach the model to evaluate if cards work well together.

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a knowledgeable MTG advisor helping players build competitive and casual decks."
    },
    {
      "role": "user",
      "content": "Do Exquisite Blood and Sanguine Bond work together?"
    },
    {
      "role": "assistant",
      "content": "Yes! Exquisite Blood and Sanguine Bond have excellent synergy. They appear together in popular combos like infinite life/damage loops. (Synergy score: 0.95)"
    }
  ]
}
```

### 3. Deck Recommendations

**Goal**: Suggest combos or cards for specific deck archetypes.

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are an AI assistant with deep knowledge of Magic: The Gathering combos and deck building strategies."
    },
    {
      "role": "user",
      "content": "What combos work in Simic Commander?"
    },
    {
      "role": "assistant",
      "content": "Here are excellent Simic combos for Commander:\n\n1. Intruder Alarm + Paradise Mantle - Infinite mana, Infinite untap\n2. Kinnan, Bonder Prodigy + Basalt Monolith - Infinite colorless mana\n3. Thrasios, Triton Hero + Dramatic Reversal - Infinite card draw\n4. Pili-Pala + Grand Architect - Infinite colored mana\n5. Freed from the Real + Selvala, Heart of the Wilds - Infinite mana"
    }
  ]
}
```

### 4. Card Alternatives

**Goal**: Suggest budget or functional replacements for expensive cards.

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are an expert Magic: The Gathering deck building assistant."
    },
    {
      "role": "user",
      "content": "What's a budget alternative to Mana Crypt?"
    },
    {
      "role": "assistant",
      "content": "Cards similar to Mana Crypt:\n\n1. Sol Ring ($1.50) - Produces 2 colorless mana, no downside\n2. Mana Vault ($8.00) - Similar fast mana but requires untap payment\n3. Arcane Signet ($2.00) - Produces mana matching your commander's colors\n4. Thought Vessel ($3.50) - Ramp plus no maximum hand size\n5. Mind Stone ($0.50) - Ramp with card draw option"
    }
  ]
}
```

## Best Practices

### 1. Vary System Prompts

Use different system prompts to prevent overfitting:

```python
SYSTEM_PROMPTS = [
    "You are an expert Magic: The Gathering deck building assistant specializing in Commander and Standard formats.",
    "You are a knowledgeable MTG advisor helping players build competitive and casual decks.",
    "You are an AI assistant with deep knowledge of Magic: The Gathering combos, synergies, and deck building strategies.",
]
```

### 2. Vary User Questions

Generate natural variations of questions:

```python
questions = [
    f"How does the {cards} combo work?",
    f"Explain the {cards} interaction.",
    f"What does {cards} do together?",
    f"Can you describe the {cards} combo?",
]
```

### 3. Include Metadata in Responses

Add helpful context like prices, popularity, or color identity:

```
"Yes! These cards have excellent synergy (Synergy score: 0.95)"
"Sol Ring ($1.50) - Produces 2 colorless mana"
```

### 4. Keep Responses Natural

Write conversational, helpful responses:
- ✅ "Yes! These cards create an infinite combo..."
- ❌ "Synergy score: 0.95. Combo detected."

## Data Generation Pipeline

### Step 1: Extract Data from Database

```bash
python training/format_qwen_data.py \
  --db-connection "postgresql://localhost/commander_spellbook" \
  --output data/qwen_training.jsonl \
  --combo-samples 5000 \
  --synergy-samples 2000
```

This generates:
- `qwen_training.jsonl` - Training set (90% of data)
- `qwen_training_validation.jsonl` - Validation set (10% of data)

### Step 2: Verify Data Quality

```python
import json

# Load and inspect examples
with open('data/qwen_training.jsonl', 'r') as f:
    for i, line in enumerate(f):
        if i >= 5:  # Show first 5 examples
            break
        example = json.loads(line)
        print(json.dumps(example, indent=2))
        print("-" * 80)
```

### Step 3: Train Model

```bash
python training/train_qwen_lora.py \
  --model_name Qwen/Qwen2.5-1.5B-Instruct \
  --train_file data/qwen_training.jsonl \
  --val_file data/qwen_training_validation.jsonl \
  --output_dir models/qwen-mtg-lora \
  --epochs 3 \
  --batch_size 4
```

## Dataset Statistics

Expected dataset size for Commander Spellbook data:

| Data Type | Examples | Source |
|-----------|----------|--------|
| Combo Explanations | ~5,000 | Variants table with descriptions |
| Card Synergies | ~2,000 | Card pairs from variant_cards |
| Deck Recommendations | ~500 | Color identity groupings |
| Card Alternatives | ~500 | Similar cards by type/function |
| **Total** | **~8,000** | |

## Token Length Considerations

Qwen/Qwen2.5-1.5B-Instruct has a context window of **32,768 tokens**.

Recommended message lengths:
- **System prompt**: 20-50 tokens
- **User question**: 10-30 tokens
- **Assistant response**: 50-300 tokens
- **Total per example**: 80-380 tokens

For combo explanations with long descriptions, truncate to ~200 tokens to prevent memory issues during training.

## Multi-Turn Conversations (Advanced)

For more natural conversations, you can include multiple turns:

```json
{
  "messages": [
    {"role": "system", "content": "You are an MTG deck building assistant."},
    {"role": "user", "content": "I'm building a Simic deck."},
    {"role": "assistant", "content": "Great! What's your budget and are you focused on combos or value?"},
    {"role": "user", "content": "Under $200, combo-focused."},
    {"role": "assistant", "content": "Perfect! Here are budget Simic combos:\n1. Pili-Pala + Grand Architect ($5)..."}
  ]
}
```

## Troubleshooting

### Issue: "role must be one of system/user/assistant"

**Solution**: Check that all message objects have valid `role` fields.

### Issue: Messages not properly formatted

**Solution**: Ensure each line in JSONL is valid JSON:
```bash
# Validate JSONL
python -c "
import json
with open('data/qwen_training.jsonl') as f:
    for i, line in enumerate(f, 1):
        try:
            json.loads(line)
        except:
            print(f'Invalid JSON on line {i}')
"
```

### Issue: Model outputs generic responses

**Solution**:
- Increase training examples (aim for 5,000+)
- Train for more epochs (3-5)
- Use higher LoRA rank (r=16 or r=32)
- Ensure diverse question variations

## References

- [Qwen2.5 Documentation](https://qwen.readthedocs.io/)
- [Hugging Face Qwen Models](https://huggingface.co/Qwen)
- [LoRA Fine-Tuning Guide](https://huggingface.co/docs/peft/main/en/index)
