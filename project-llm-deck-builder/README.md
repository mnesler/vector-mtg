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

## Tech Stack (Proposed)
- **Base Model**: Consider LLaMA 2/3, Mistral, or GPT-style models
- **LoRA**: PEFT (Parameter-Efficient Fine-Tuning)
- **Framework**: PyTorch, Hugging Face Transformers
- **Training**: DeepSpeed or FSDP for distributed training
- **Inference**: vLLM or FastAPI with model serving

## Current Status
- Not yet started
- Depends on data collection project for training data
- Needs architecture design and model selection

## Use Cases
1. "Build me a Simic landfall Commander deck under $200"
2. "What cards synergize with Heliod, Sun-Crowned?"
3. "Suggest combo finishers for my Golgari deck"
4. "What's missing from this Standard aggro list?"
