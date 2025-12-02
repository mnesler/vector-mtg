# MTG Query Parser Fine-Tuning Guide

## Overview

This document outlines strategies for training a specialized model to parse Magic: The Gathering search queries into structured components for semantic search.

## Current Problem

The current Phi-3.5-mini-instruct model (3.8B parameters) is prone to hallucination and unreliable for query parsing:
- Returns wrong creature types (e.g., "vampires" when asked for "zombies")
- Uses examples from the prompt instead of parsing the actual query
- Inconsistent output format

## Goal

Train a small, fast, reliable model that parses MTG queries like:

```
Input:  "zombies, but only ones in blue"
Output: {"positive": "zombies blue", "exclude": ["black", "red", "green", "white"]}

Input:  "vampires no black"
Output: {"positive": "vampires", "exclude": ["black"]}

Input:  "red and green wolves"
Output: {"positive": "red green wolves", "exclude": []}
```

---

## Approach 1: Fine-Tune a Small Model

### Recommended Models

#### Option A: T5-Small/Base (Best for Structured Output)
- **T5-small**: 60M parameters, very fast
- **T5-base**: 220M parameters, more accurate
- **Pros**: Designed for text-to-text tasks, excellent for JSON generation
- **Cons**: Encoder-decoder architecture (slightly more complex)

```python
from transformers import T5ForConditionalGeneration, T5Tokenizer

model = T5ForConditionalGeneration.from_pretrained("t5-small")
tokenizer = T5Tokenizer.from_pretrained("t5-small")
```

#### Option B: Small Decoder Models
- **Phi-2** (2.7B) - Good balance of size/performance
- **Qwen2.5-1.5B-Instruct** - Excellent instruction following
- **Llama-3.2-1B-Instruct** - Very small, fast
- **Pros**: Single architecture, easier to work with
- **Cons**: Larger than T5, may be slower

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct")
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct")
```

### Training Process

1. **Prepare Data** (see Data Generation section below)
2. **Format for Training**
3. **Fine-tune**
4. **Evaluate**
5. **Deploy**

#### Training Script Template

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from trl import SFTTrainer
from datasets import Dataset

# 1. Load base model
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct")
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct")

# 2. Load your training data
with open("mtg_training_data.jsonl") as f:
    data = [json.loads(line) for line in f]

# 3. Format for training
def format_training_example(item):
    return f"""<|user|>Parse this MTG search query: {item['input']}<|end|>
<|assistant|>{json.dumps(item['output'])}<|end|>"""

formatted_data = [{"text": format_training_example(item)} for item in data]
dataset = Dataset.from_list(formatted_data)

# 4. Configure training
training_args = TrainingArguments(
    output_dir="./mtg-query-parser",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-5,
    warmup_steps=100,
    logging_steps=50,
    save_steps=500,
    eval_strategy="steps",
    eval_steps=500,
    save_total_limit=3,
    fp16=True,  # Use mixed precision if GPU available
)

# 5. Create trainer
trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    tokenizer=tokenizer,
    max_seq_length=256,
)

# 6. Train
trainer.train()

# 7. Save
model.save_pretrained("./mtg-query-parser-final")
tokenizer.save_pretrained("./mtg-query-parser-final")
```

---

## Data Generation Strategies

### Strategy 1: Synthetic Data Generation (RECOMMENDED START)

Generate training examples programmatically based on known patterns.

**Advantages:**
- No manual labeling required
- Can generate thousands of examples quickly
- Covers all edge cases systematically
- Free

**Implementation:**

```python
import json
import itertools

# MTG domain knowledge
creatures = [
    "zombies", "vampires", "elves", "goblins", "dragons", "wolves",
    "werewolves", "angels", "demons", "spirits", "soldiers", "wizards",
    "knights", "merfolk", "beasts", "birds", "cats", "elementals",
    "faeries", "giants", "hydras", "insects", "phoenixes", "rogues",
    "shamans", "sphinxes", "trolls", "warriors", "clerics"
]

colors = ["white", "blue", "black", "red", "green"]

keywords = [
    "flying", "trample", "haste", "lifelink", "deathtouch",
    "vigilance", "first strike", "double strike", "menace",
    "reach", "hexproof", "indestructible"
]

training_data = []

# Pattern 1: "X but only Y color" (1,500+ examples)
for creature in creatures:
    for color in colors:
        excluded_colors = [c for c in colors if c != color]

        # Base form
        training_data.append({
            "input": f"{creature} but only {color}",
            "output": {
                "positive": f"{creature} {color}",
                "exclude": excluded_colors
            }
        })

        # Variation: "but only ones in"
        training_data.append({
            "input": f"{creature}, but only ones in {color}",
            "output": {
                "positive": f"{creature} {color}",
                "exclude": excluded_colors
            }
        })

        # Variation: "only"
        training_data.append({
            "input": f"{creature} only {color}",
            "output": {
                "positive": f"{creature} {color}",
                "exclude": excluded_colors
            }
        })

# Pattern 2: "X no Y" (1,000+ examples)
for creature in creatures:
    for exclude_item in colors + keywords:
        # "no"
        training_data.append({
            "input": f"{creature} no {exclude_item}",
            "output": {
                "positive": creature,
                "exclude": [exclude_item]
            }
        })

        # "without"
        training_data.append({
            "input": f"{creature} without {exclude_item}",
            "output": {
                "positive": creature,
                "exclude": [exclude_item]
            }
        })

# Pattern 3: Simple queries (900+ examples)
for creature in creatures:
    # Just the creature
    training_data.append({
        "input": creature,
        "output": {
            "positive": creature,
            "exclude": []
        }
    })

    # Creature + color
    for color in colors:
        training_data.append({
            "input": f"{color} {creature}",
            "output": {
                "positive": f"{color} {creature}",
                "exclude": []
            }
        })

# Pattern 4: Multi-color queries (400+ examples)
for creature in creatures[:20]:
    for color1, color2 in itertools.combinations(colors, 2):
        training_data.append({
            "input": f"{color1} and {color2} {creature}",
            "output": {
                "positive": f"{color1} {color2} {creature}",
                "exclude": []
            }
        })

# Pattern 5: With keywords (600+ examples)
for creature in creatures[:20]:
    for keyword in keywords:
        training_data.append({
            "input": f"{creature} with {keyword}",
            "output": {
                "positive": f"{creature} {keyword}",
                "exclude": []
            }
        })

print(f"Generated {len(training_data)} training examples")

# Save to JSONL
with open("mtg_training_data.jsonl", "w") as f:
    for item in training_data:
        f.write(json.dumps(item) + "\n")
```

**Expected Output:** ~4,000-5,000 training examples

### Strategy 2: Real User Queries

Collect actual searches from users and label them.

**Implementation:**

```python
# In api_server_rules.py, add logging
import logging

# Set up query logger
query_logger = logging.getLogger('user_queries')
query_logger.setLevel(logging.INFO)
handler = logging.FileHandler('logs/user_queries.log')
query_logger.addHandler(handler)

@app.get("/api/cards/semantic")
async def semantic_search(query: str, ...):
    # Log the query
    query_logger.info(json.dumps({
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "user_agent": request.headers.get("user-agent")
    }))

    # ... rest of code
```

**Labeling Process:**

1. Review `user_queries.log` weekly
2. Manually create correct parse outputs
3. Add to training dataset
4. Retrain model periodically

### Strategy 3: LLM-Generated Data

Use GPT-4/Claude to generate diverse examples.

```python
import anthropic

client = anthropic.Anthropic(api_key="your-key")

def generate_training_batch(n=20):
    prompt = f"""Generate {n} diverse Magic: The Gathering card search queries with their parsed outputs.

Format:
Query: [natural language query]
Output: {{"positive": "...", "exclude": [...]}}

Include varied patterns:
- "X but only Y color"
- "X without Y"
- "color and color creatures"
- Simple searches

Examples:
Query: vampires but only red
Output: {{"positive": "vampires red", "exclude": ["white", "blue", "black", "green"]}}

Query: elves no black
Output: {{"positive": "elves", "exclude": ["black"]}}

Generate {n} MORE diverse examples:"""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    # Parse and return
    return parse_llm_response(message.content)

# Generate 500 examples
all_data = []
for _ in range(25):  # 25 batches of 20
    all_data.extend(generate_training_batch())
```

### Strategy 4: Data Augmentation

Expand synthetic data with natural variations.

```python
def augment_query(query, output):
    """Create natural variations of a query."""
    variations = []

    # Original
    variations.append({"input": query, "output": output})

    # Capitalization
    variations.append({"input": query.capitalize(), "output": output})
    variations.append({"input": query.upper(), "output": output})

    # Add filler words
    if "but only" in query:
        variations.append({
            "input": query.replace("but only", "but I only want"),
            "output": output
        })

    # Spelling variations (British English, etc.)
    replacements = {
        "color": ["colour"],
        "artifact": ["artefact"],
    }

    for old, new_list in replacements.items():
        if old in query:
            for new in new_list:
                variations.append({
                    "input": query.replace(old, new),
                    "output": output
                })

    return variations

# Apply to all synthetic data
augmented_data = []
for item in training_data:
    augmented_data.extend(augment_query(item["input"], item["output"]))
```

---

## Complete Data Generation Script

Save as `scripts/training/generate_training_data.py`:

```python
#!/usr/bin/env python3
"""Generate training data for MTG query parser."""

import json
import random
import itertools
from pathlib import Path

def generate_mtg_training_data():
    """Generate comprehensive training dataset."""

    # MTG domain knowledge
    creatures = [
        "zombies", "vampires", "elves", "goblins", "dragons", "wolves",
        "werewolves", "angels", "demons", "spirits", "soldiers", "wizards",
        "knights", "merfolk", "beasts", "birds", "cats", "elementals",
        "faeries", "giants", "hydras", "insects", "phoenixes", "rogues"
    ]

    colors = ["white", "blue", "black", "red", "green"]

    keywords = [
        "flying", "trample", "haste", "lifelink", "deathtouch",
        "vigilance", "first strike", "double strike", "menace", "reach"
    ]

    data = []

    # Pattern 1: "X but only Y"
    print("Generating 'but only' patterns...")
    for creature in creatures:
        for color in colors:
            excluded = [c for c in colors if c != color]

            data.extend([
                {
                    "input": f"{creature} but only {color}",
                    "output": {"positive": f"{creature} {color}", "exclude": excluded}
                },
                {
                    "input": f"{creature}, but only ones in {color}",
                    "output": {"positive": f"{creature} {color}", "exclude": excluded}
                },
                {
                    "input": f"{creature} only {color}",
                    "output": {"positive": f"{creature} {color}", "exclude": excluded}
                }
            ])

    # Pattern 2: "X no Y"
    print("Generating 'no/without' patterns...")
    for creature in creatures:
        for exclude_item in colors + keywords:
            data.extend([
                {
                    "input": f"{creature} no {exclude_item}",
                    "output": {"positive": creature, "exclude": [exclude_item]}
                },
                {
                    "input": f"{creature} without {exclude_item}",
                    "output": {"positive": creature, "exclude": [exclude_item]}
                }
            ])

    # Pattern 3: Simple queries
    print("Generating simple queries...")
    for creature in creatures:
        data.append({
            "input": creature,
            "output": {"positive": creature, "exclude": []}
        })

        for color in colors:
            data.append({
                "input": f"{color} {creature}",
                "output": {"positive": f"{color} {creature}", "exclude": []}
            })

    # Pattern 4: Multi-color
    print("Generating multi-color queries...")
    for creature in creatures[:15]:
        for color1, color2 in itertools.combinations(colors, 2):
            data.append({
                "input": f"{color1} and {color2} {creature}",
                "output": {"positive": f"{color1} {color2} {creature}", "exclude": []}
            })

    # Pattern 5: With keywords
    print("Generating keyword queries...")
    for creature in creatures[:15]:
        for keyword in keywords[:5]:
            data.append({
                "input": f"{creature} with {keyword}",
                "output": {"positive": f"{creature} {keyword}", "exclude": []}
            })

    return data

def save_training_data(data, output_dir="data/training"):
    """Save training data to JSONL."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Shuffle data
    random.shuffle(data)

    # Split into train/validation (90/10)
    split_idx = int(len(data) * 0.9)
    train_data = data[:split_idx]
    val_data = data[split_idx:]

    # Save train
    train_path = Path(output_dir) / "train.jsonl"
    with open(train_path, "w") as f:
        for item in train_data:
            f.write(json.dumps(item) + "\n")

    # Save validation
    val_path = Path(output_dir) / "validation.jsonl"
    with open(val_path, "w") as f:
        for item in val_data:
            f.write(json.dumps(item) + "\n")

    print(f"\n✓ Generated {len(data)} total examples")
    print(f"  - Training: {len(train_data)} examples -> {train_path}")
    print(f"  - Validation: {len(val_data)} examples -> {val_path}")

    # Show samples
    print("\nSample training examples:")
    for item in random.sample(train_data, 5):
        print(f"  Input:  {item['input']}")
        print(f"  Output: {item['output']}")
        print()

if __name__ == "__main__":
    data = generate_mtg_training_data()
    save_training_data(data)
```

---

## Training Environment Setup

### Requirements

```bash
# requirements-training.txt
torch>=2.0.0
transformers>=4.35.0
datasets>=2.14.0
trl>=0.7.0
accelerate>=0.24.0
peft>=0.6.0  # For LoRA fine-tuning (optional)
wandb  # For experiment tracking (optional)
```

Install:
```bash
pip install -r requirements-training.txt
```

### Hardware Requirements

- **Minimum**: 16GB RAM, CPU only (slow, ~hours)
- **Recommended**: GPU with 8GB+ VRAM (NVIDIA RTX 3060 or better)
- **Optimal**: GPU with 16GB+ VRAM, or cloud GPU (vast.ai, runpod.io)

---

## Deployment

### Integration with Existing Code

Replace current query parser in `scripts/api/query_parser_service.py`:

```python
class QueryParserService:
    def __init__(self, model_path: str = "./models/mtg-query-parser"):
        """Initialize with fine-tuned model if available, else use regex."""
        self.use_finetuned = Path(model_path).exists()

        if self.use_finetuned:
            print(f"Loading fine-tuned query parser: {model_path}")
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = AutoModelForCausalLM.from_pretrained(model_path)
            self.model.eval()
            print("✓ Fine-tuned query parser ready")
        else:
            print("⚠ Fine-tuned model not found, using regex-only parser")

    def parse_query(self, query: str) -> Dict[str, any]:
        # 1. Try regex first (fastest)
        regex_result = self.parse_query_regex(query)
        if regex_result:
            return regex_result

        # 2. Use fine-tuned model if available
        if self.use_finetuned:
            return self._parse_with_model(query)

        # 3. Fallback: use query as-is
        return {
            "positive_query": query,
            "exclusions": [],
            "original_query": query
        }

    def _parse_with_model(self, query: str) -> Dict[str, any]:
        """Parse using fine-tuned model."""
        prompt = f"<|user|>Parse this MTG search query: {query}<|end|>\n<|assistant|>"
        inputs = self.tokenizer(prompt, return_tensors="pt")

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=100,
                num_beams=1,
                pad_token_id=self.tokenizer.eos_token_id
            )

        result = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        json_str = result.split("<|assistant|>")[-1].strip()

        try:
            parsed = json.loads(json_str)
            parsed['original_query'] = query
            return parsed
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "positive_query": query,
                "exclusions": [],
                "original_query": query
            }
```

---

## Evaluation

### Test Set

Create a diverse test set (`data/test/queries.json`):

```json
[
  {"query": "zombies but only blue", "expected": {"positive": "zombies blue", "exclude": ["black", "white", "red", "green"]}},
  {"query": "red dragons", "expected": {"positive": "red dragons", "exclude": []}},
  {"query": "elves without black", "expected": {"positive": "elves", "exclude": ["black"]}},
  {"query": "werewolves and vampires", "expected": {"positive": "werewolves vampires", "exclude": []}}
]
```

### Evaluation Script

```python
def evaluate_parser(parser, test_file="data/test/queries.json"):
    """Evaluate parser accuracy."""
    with open(test_file) as f:
        test_cases = json.load(f)

    correct = 0
    total = len(test_cases)

    for case in test_cases:
        result = parser.parse_query(case["query"])
        expected = case["expected"]

        # Check if matches
        if (result["positive"] == expected["positive"] and
            set(result["exclude"]) == set(expected["exclude"])):
            correct += 1
        else:
            print(f"FAIL: {case['query']}")
            print(f"  Expected: {expected}")
            print(f"  Got:      {result}")

    accuracy = correct / total * 100
    print(f"\nAccuracy: {accuracy:.1f}% ({correct}/{total})")
    return accuracy
```

---

## Next Steps

1. **Generate Training Data**: Run `scripts/training/generate_training_data.py`
2. **Train Model**: Use the training script template
3. **Evaluate**: Test on holdout set
4. **Deploy**: Integrate into `query_parser_service.py`
5. **Monitor**: Log real queries, retrain periodically

---

## Cost & Time Estimates

### Training
- **Data Generation**: 5 minutes
- **Training on GPU**: 30-60 minutes
- **Training on CPU**: 4-8 hours

### Costs
- **Cloud GPU** (RunPod/Vast.ai): $0.20-0.50/hour
- **Total training cost**: $0.50-1.00
- **Inference cost**: Free (runs locally)

---

## Alternative: Structured Output with Grammar

If training is too complex, consider using grammar-constrained generation:

```python
from outlines import models, generate

# Force model to output valid JSON
model = models.Transformers("Qwen/Qwen2.5-1.5B-Instruct")

schema = {
    "type": "object",
    "properties": {
        "positive": {"type": "string"},
        "exclude": {"type": "array", "items": {"type": "string"}}
    }
}

generator = generate.json(model, schema)
result = generator(f"Parse: {query}")
```

This can improve output reliability without fine-tuning.

---

## Conclusion

**Recommended Path:**
1. Start with regex patterns (current implementation) ✓
2. Generate synthetic training data (easy, free)
3. Fine-tune Qwen2.5-1.5B on synthetic data
4. Log real queries and add to training set
5. Retrain quarterly

This gives you a reliable, fast, and continuously improving query parser.
