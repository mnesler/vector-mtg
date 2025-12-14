# LLM Deck Building Assistant

## Purpose
Train and deploy an LLM model (with LoRA fine-tuning) that assists users in building MTG decks, with focus on Commander and Standard formats.

## Components

### Training (`/training`)
- **LoRA Implementation**: Fine-tuning scripts for deck building
- **Training Data Preparation**: Format data from project-data-collection
- **Model Training**: Training loops, hyperparameter tuning
- **Evaluation**: Model performance metrics

### Models (`/models`)
- **Base Models**: Pre-trained model checkpoints
- **LoRA Adapters**: Trained LoRA weights
- **Model Configs**: Training configurations
- **Exports**: Production-ready models

### Inference (`/inference`)
- **Deck Recommendation Engine**: Generate deck suggestions
- **Card Synergy Analysis**: Identify card combinations
- **Meta Analysis**: Suggest cards based on format meta
- **API Server**: Expose LLM via REST API

### Tests (`/tests`)
- Model quality tests
- Inference speed benchmarks
- Recommendation accuracy validation

## Training Data Sources
All data comes from `project-data-collection`:
- Card embeddings and metadata
- Combo data (EDHREC, Commander Spellbook)
- Deck archetypes (Moxfield)
- Format-specific trends (Commander/Standard)

## Tech Stack
- **Base Model**: Qwen/Qwen2.5-1.5B-Instruct (1.5B parameters, instruction-tuned)
- **Fine-Tuning**: LoRA via PEFT (Parameter-Efficient Fine-Tuning)
- **Framework**: PyTorch + Hugging Face Transformers
- **Training**: Gradient checkpointing for memory efficiency
- **Inference**: FastAPI with LoRA adapter loading
- **Data Format**: Conversational chat format (system/user/assistant messages)

## Current Status
- ✅ **Data formatting pipeline ready** - Converts Commander Spellbook data to Qwen format
- ✅ **Training scripts complete** - LoRA fine-tuning for Qwen/Qwen2.5-1.5B-Instruct
- ✅ **Inference tools ready** - Interactive testing and deployment code
- ✅ **Documentation complete** - Full guides for training and adding new data
- ⬜ **Initial model training** - Ready to run on your data
- ⬜ **Production deployment** - API integration pending

## Quick Start

### 1. Generate Training Data
```bash
cd training
python format_qwen_data.py \
  --db-connection "postgresql://localhost/commander_spellbook" \
  --output ../data/qwen_training.jsonl
```

### 2. Train Model
```bash
python train_qwen_lora.py \
  --train_file ../data/qwen_training.jsonl \
  --output_dir ../models/qwen-mtg-lora \
  --epochs 3
```

### 3. Test Model
```bash
cd ../inference
python test_qwen.py --model_path ../models/qwen-mtg-lora --interactive
```

**See [QWEN_SETUP_COMPLETE.md](./QWEN_SETUP_COMPLETE.md) for detailed instructions.**

## Use Cases
1. "Build me a Simic landfall Commander deck under $200"
2. "What cards synergize with Heliod, Sun-Crowned?"
3. "Suggest combo finishers for my Golgari deck"
4. "What's missing from this Standard aggro list?"

## Documentation

- **[QWEN_SETUP_COMPLETE.md](./QWEN_SETUP_COMPLETE.md)** - Complete overview and quick reference
- **[docs/QUICK_START.md](./docs/QUICK_START.md)** - Step-by-step tutorial
- **[docs/QWEN_TRAINING_FORMAT.md](./docs/QWEN_TRAINING_FORMAT.md)** - Data format specification
- **[docs/ADDING_NEW_DATA.md](./docs/ADDING_NEW_DATA.md)** - How to add new data without retraining from scratch
