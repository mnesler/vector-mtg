# Quick Start Guide: Fine-tuning Qwen for MTG Deck Building

This guide will get you started with fine-tuning Qwen/Qwen2.5-1.5B-Instruct on your MTG data.

## Prerequisites

1. **Python 3.9+** installed
2. **PostgreSQL database** with Commander Spellbook data
3. **GPU with at least 8GB VRAM** (recommended: 16GB+)
4. **~20GB disk space** for model and data

## Step 1: Install Dependencies

```bash
cd /home/maxwell/vector-mtg/project-llm-deck-builder
pip install -r requirements.txt
```

## Step 2: Generate Training Data

Format your Commander Spellbook data into Qwen's chat format:

```bash
cd training

python format_qwen_data.py \
  --db-connection "postgresql://localhost/commander_spellbook" \
  --output ../data/qwen_training.jsonl \
  --combo-samples 5000 \
  --synergy-samples 2000
```

**Output:**
- `data/qwen_training.jsonl` - Training set (~6,300 examples)
- `data/qwen_training_validation.jsonl` - Validation set (~700 examples)

**What this does:**
- Extracts combo explanations from your database
- Formats card synergy data
- Converts everything to Qwen's chat message format
- Generates natural question variations

## Step 3: Verify Data Format

Check that your data looks correct:

```bash
# View first few examples
head -n 3 ../data/qwen_training.jsonl | python -m json.tool

# Count examples
wc -l ../data/qwen_training.jsonl
```

Expected format:
```json
{
  "messages": [
    {"role": "system", "content": "You are an expert MTG assistant..."},
    {"role": "user", "content": "How does the combo work?"},
    {"role": "assistant", "content": "This combo produces..."}
  ]
}
```

## Step 4: Train the Model

Start LoRA fine-tuning:

```bash
python train_qwen_lora.py \
  --model_name Qwen/Qwen2.5-1.5B-Instruct \
  --train_file ../data/qwen_training.jsonl \
  --val_file ../data/qwen_training_validation.jsonl \
  --output_dir ../models/qwen-mtg-lora \
  --epochs 3 \
  --batch_size 4 \
  --lora_r 16 \
  --learning_rate 2e-4
```

**Training time:** 1-3 hours on a modern GPU (RTX 3090/4090)

**Memory usage:** ~10-12GB VRAM with default settings

**Parameters explained:**
- `--epochs 3`: Train for 3 passes through the data
- `--batch_size 4`: Process 4 examples at a time
- `--lora_r 16`: LoRA rank (higher = more parameters, better quality, slower)
- `--learning_rate 2e-4`: How fast the model learns

## Step 5: Test Your Model

Run interactive testing:

```bash
cd ../inference

# Interactive chat mode
python test_qwen.py \
  --model_path ../models/qwen-mtg-lora \
  --interactive

# Test with pre-defined prompts
python test_qwen.py \
  --model_path ../models/qwen-mtg-lora \
  --test

# Single prompt
python test_qwen.py \
  --model_path ../models/qwen-mtg-lora \
  --prompt "What combos work in Simic Commander?"
```

## Step 6: Use in Production

Example integration:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch

# Load model
tokenizer = AutoTokenizer.from_pretrained("../models/qwen-mtg-lora", trust_remote_code=True)
base_model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-1.5B-Instruct",
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True
)
model = PeftModel.from_pretrained(base_model, "../models/qwen-mtg-lora")
model.eval()

# Generate response
messages = [
    {"role": "system", "content": "You are an MTG deck building assistant."},
    {"role": "user", "content": "What combos work in Simic?"}
]

prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

with torch.no_grad():
    outputs = model.generate(**inputs, max_new_tokens=300, temperature=0.7)

response = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(response)
```

## Troubleshooting

### Out of Memory (OOM) Error

**Solution 1:** Reduce batch size
```bash
python train_qwen_lora.py --batch_size 2  # or even 1
```

**Solution 2:** Enable gradient accumulation
```bash
python train_qwen_lora.py --batch_size 2 --gradient_accumulation_steps 8
```

**Solution 3:** Reduce sequence length
```bash
python train_qwen_lora.py --max_seq_length 256
```

### Model Not Responding Well

**Solution 1:** Train longer
```bash
python train_qwen_lora.py --epochs 5
```

**Solution 2:** Increase LoRA rank
```bash
python train_qwen_lora.py --lora_r 32
```

**Solution 3:** Add more training data
```bash
python format_qwen_data.py --combo-samples 10000 --synergy-samples 5000
```

### Database Connection Issues

Check your connection string:
```bash
# Test connection
psql -d commander_spellbook -c "SELECT COUNT(*) FROM variants;"

# If using password
python format_qwen_data.py \
  --db-connection "postgresql://user:password@localhost:5432/commander_spellbook"
```

## Performance Tuning

### For Better Quality (Slower Training)

```bash
python train_qwen_lora.py \
  --lora_r 32 \
  --lora_alpha 64 \
  --epochs 5 \
  --learning_rate 1e-4 \
  --max_seq_length 768
```

### For Faster Training (Lower Quality)

```bash
python train_qwen_lora.py \
  --lora_r 8 \
  --lora_alpha 16 \
  --epochs 2 \
  --batch_size 8 \
  --max_seq_length 256
```

## Next Steps

1. **Evaluate model quality** - Test on specific deck building scenarios
2. **Collect more data** - Add EDHREC data, Moxfield decks
3. **Deploy as API** - See `deck_recommender.py` for FastAPI integration
4. **Fine-tune further** - Continuous training with user feedback

## Resources

- [Qwen Documentation](https://qwen.readthedocs.io/)
- [PEFT/LoRA Guide](https://huggingface.co/docs/peft)
- [Training Format Details](./QWEN_TRAINING_FORMAT.md)
- [ML Training Data Guide](../../project-data-collection/ML_TRAINING_DATA_GUIDE.md)

## Common Commands Cheat Sheet

```bash
# Generate data
cd training
python format_qwen_data.py --db-connection "postgresql://localhost/commander_spellbook"

# Train model
python train_qwen_lora.py --train_file ../data/qwen_training.jsonl --epochs 3

# Test model
cd ../inference
python test_qwen.py --model_path ../models/qwen-mtg-lora --interactive

# Check GPU usage
nvidia-smi

# Monitor training
tensorboard --logdir ../models/qwen-mtg-lora/runs
```

## Expected Results

After training on ~7,000 examples for 3 epochs, you should see:

- **Training loss:** ~1.5-2.0
- **Validation loss:** ~1.8-2.2
- **Response quality:** Coherent combo explanations, accurate synergy assessments
- **Inference speed:** ~2-5 tokens/second on consumer GPU

The model should be able to:
- ✅ Explain MTG combos step-by-step
- ✅ Suggest cards that synergize together
- ✅ Recommend combos for specific color combinations
- ✅ Provide budget alternatives for expensive cards
- ✅ Answer questions about deck building strategies
