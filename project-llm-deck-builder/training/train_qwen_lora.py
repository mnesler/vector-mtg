"""
LoRA Fine-Tuning Script for Qwen/Qwen2.5-1.5B-Instruct

This script fine-tunes Qwen/Qwen2.5-1.5B-Instruct using LoRA for MTG deck building.
Uses chat-formatted training data (JSONL with messages array).

Usage:
    python train_qwen_lora.py \
        --model_name Qwen/Qwen2.5-1.5B-Instruct \
        --train_file ../data/qwen_training.jsonl \
        --val_file ../data/qwen_training_validation.jsonl \
        --output_dir ../models/qwen-mtg-lora \
        --epochs 3 \
        --batch_size 4
"""

import os
import json
import torch
from dataclasses import dataclass, field
from typing import Optional, Dict, List
from pathlib import Path

from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForSeq2Seq,
)
from datasets import load_dataset
from peft import LoraConfig, get_peft_model, TaskType, prepare_model_for_kbit_training
import argparse


@dataclass
class QwenTrainingConfig:
    """Configuration for Qwen LoRA training."""

    model_name: str = "Qwen/Qwen2.5-1.5B-Instruct"
    train_file: str = "../data/qwen_training.jsonl"
    val_file: Optional[str] = "../data/qwen_training_validation.jsonl"
    output_dir: str = "../models/qwen-mtg-lora"

    # LoRA hyperparameters
    lora_r: int = 16  # Rank
    lora_alpha: int = 32  # Alpha scaling
    lora_dropout: float = 0.05
    lora_target_modules: List[str] = field(
        default_factory=lambda: [
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ]
    )

    # Training hyperparameters
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 4
    per_device_eval_batch_size: int = 4
    gradient_accumulation_steps: int = 4
    learning_rate: float = 2e-4
    max_seq_length: int = 512
    warmup_steps: int = 100
    logging_steps: int = 10
    save_steps: int = 100
    eval_steps: int = 100

    # Optimization
    optim: str = "adamw_torch"
    fp16: bool = True
    gradient_checkpointing: bool = True


class QwenDataPreprocessor:
    """Preprocess chat-formatted data for Qwen training."""

    def __init__(self, tokenizer, max_seq_length: int = 512):
        self.tokenizer = tokenizer
        self.max_seq_length = max_seq_length

    def format_chat_example(self, example: Dict) -> Dict:
        """
        Convert chat messages to Qwen chat template format.

        Input format:
        {
            "messages": [
                {"role": "system", "content": "..."},
                {"role": "user", "content": "..."},
                {"role": "assistant", "content": "..."}
            ]
        }

        Output: Tokenized input_ids and labels
        """
        messages = example["messages"]

        # Use Qwen's chat template
        formatted_text = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=False
        )

        # Tokenize
        tokenized = self.tokenizer(
            formatted_text,
            truncation=True,
            max_length=self.max_seq_length,
            padding=False,
            return_tensors=None,
        )

        # For causal LM, labels are the same as input_ids
        tokenized["labels"] = tokenized["input_ids"].copy()

        return tokenized

    def preprocess_dataset(self, dataset):
        """Apply preprocessing to entire dataset."""
        return dataset.map(
            self.format_chat_example,
            remove_columns=dataset.column_names,
            desc="Formatting chat examples",
        )


def load_qwen_model(config: QwenTrainingConfig):
    """Load Qwen model with LoRA configuration."""

    print(f"Loading model: {config.model_name}")

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        config.model_name,
        trust_remote_code=True,
        padding_side="right",  # Important for training
    )

    # Ensure pad token is set
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Load model with 4-bit quantization for memory efficiency (optional)
    model = AutoModelForCausalLM.from_pretrained(
        config.model_name,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
    )

    # Enable gradient checkpointing for memory efficiency
    if config.gradient_checkpointing:
        model.gradient_checkpointing_enable()
        model = prepare_model_for_kbit_training(model)

    # Configure LoRA
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        lora_dropout=config.lora_dropout,
        target_modules=config.lora_target_modules,
        bias="none",
    )

    # Apply LoRA
    model = get_peft_model(model, lora_config)

    print("\nLoRA Configuration:")
    model.print_trainable_parameters()

    return model, tokenizer


def load_training_data(config: QwenTrainingConfig, tokenizer):
    """Load and preprocess training data."""

    print(f"\nLoading training data from {config.train_file}")

    # Load datasets
    data_files = {"train": config.train_file}
    if config.val_file and Path(config.val_file).exists():
        data_files["validation"] = config.val_file

    dataset = load_dataset("json", data_files=data_files)

    print(f"Loaded {len(dataset['train'])} training examples")
    if "validation" in dataset:
        print(f"Loaded {len(dataset['validation'])} validation examples")

    # Preprocess
    preprocessor = QwenDataPreprocessor(tokenizer, config.max_seq_length)
    tokenized_datasets = {}

    tokenized_datasets["train"] = preprocessor.preprocess_dataset(dataset["train"])

    if "validation" in dataset:
        tokenized_datasets["validation"] = preprocessor.preprocess_dataset(
            dataset["validation"]
        )

    return tokenized_datasets


def train(config: QwenTrainingConfig):
    """Main training function."""

    # Create output directory
    Path(config.output_dir).mkdir(parents=True, exist_ok=True)

    # Load model and tokenizer
    model, tokenizer = load_qwen_model(config)

    # Load and preprocess data
    tokenized_datasets = load_training_data(config, tokenizer)

    # Data collator for dynamic padding
    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        model=model,
        padding=True,
    )

    # Training arguments
    training_args = TrainingArguments(
        output_dir=config.output_dir,
        num_train_epochs=config.num_train_epochs,
        per_device_train_batch_size=config.per_device_train_batch_size,
        per_device_eval_batch_size=config.per_device_eval_batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        learning_rate=config.learning_rate,
        warmup_steps=config.warmup_steps,
        logging_steps=config.logging_steps,
        save_steps=config.save_steps,
        eval_steps=config.eval_steps,
        evaluation_strategy="steps" if "validation" in tokenized_datasets else "no",
        save_total_limit=3,
        fp16=config.fp16,
        optim=config.optim,
        gradient_checkpointing=config.gradient_checkpointing,
        report_to=["tensorboard"],
        load_best_model_at_end=True if "validation" in tokenized_datasets else False,
        metric_for_best_model="eval_loss" if "validation" in tokenized_datasets else None,
    )

    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets.get("validation"),
        data_collator=data_collator,
    )

    # Train
    print("\n" + "=" * 60)
    print("Starting training...")
    print("=" * 60)

    trainer.train()

    # Save final model
    print("\n" + "=" * 60)
    print("Training complete! Saving model...")
    print("=" * 60)

    trainer.save_model(config.output_dir)
    tokenizer.save_pretrained(config.output_dir)

    # Save training config
    config_path = Path(config.output_dir) / "training_config.json"
    with open(config_path, "w") as f:
        json.dump(vars(config), f, indent=2)

    print(f"\nModel saved to: {config.output_dir}")
    print(f"Config saved to: {config_path}")

    return trainer


def main():
    parser = argparse.ArgumentParser(
        description="Fine-tune Qwen/Qwen2.5-1.5B-Instruct with LoRA for MTG deck building"
    )

    # Model and data
    parser.add_argument(
        "--model_name",
        type=str,
        default="Qwen/Qwen2.5-1.5B-Instruct",
        help="HuggingFace model name",
    )
    parser.add_argument(
        "--train_file", type=str, required=True, help="Path to training JSONL file"
    )
    parser.add_argument(
        "--val_file",
        type=str,
        default=None,
        help="Path to validation JSONL file (optional)",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="../models/qwen-mtg-lora",
        help="Output directory for model",
    )

    # LoRA config
    parser.add_argument("--lora_r", type=int, default=16, help="LoRA rank")
    parser.add_argument("--lora_alpha", type=int, default=32, help="LoRA alpha")
    parser.add_argument("--lora_dropout", type=float, default=0.05, help="LoRA dropout")

    # Training config
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=4, help="Training batch size")
    parser.add_argument(
        "--gradient_accumulation_steps",
        type=int,
        default=4,
        help="Gradient accumulation steps",
    )
    parser.add_argument("--learning_rate", type=float, default=2e-4, help="Learning rate")
    parser.add_argument(
        "--max_seq_length", type=int, default=512, help="Maximum sequence length"
    )

    args = parser.parse_args()

    # Create config
    config = QwenTrainingConfig(
        model_name=args.model_name,
        train_file=args.train_file,
        val_file=args.val_file,
        output_dir=args.output_dir,
        lora_r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        learning_rate=args.learning_rate,
        max_seq_length=args.max_seq_length,
    )

    # Print configuration
    print("\n" + "=" * 60)
    print("QWEN LORA TRAINING CONFIGURATION")
    print("=" * 60)
    print(f"Model: {config.model_name}")
    print(f"Training file: {config.train_file}")
    print(f"Validation file: {config.val_file}")
    print(f"Output directory: {config.output_dir}")
    print(f"\nLoRA Config:")
    print(f"  Rank: {config.lora_r}")
    print(f"  Alpha: {config.lora_alpha}")
    print(f"  Dropout: {config.lora_dropout}")
    print(f"\nTraining Config:")
    print(f"  Epochs: {config.num_train_epochs}")
    print(f"  Batch size: {config.per_device_train_batch_size}")
    print(f"  Gradient accumulation: {config.gradient_accumulation_steps}")
    print(f"  Learning rate: {config.learning_rate}")
    print(f"  Max sequence length: {config.max_seq_length}")
    print("=" * 60 + "\n")

    # Train
    try:
        trainer = train(config)
        print("\n" + "=" * 60)
        print("SUCCESS! Training completed successfully.")
        print("=" * 60)
        print(f"\nYour fine-tuned model is ready at: {config.output_dir}")
        print("\nNext steps:")
        print(f"1. Test inference: python ../inference/test_qwen.py --model_path {config.output_dir}")
        print("2. Deploy model for deck recommendations")
        print("3. Evaluate model quality on test prompts")

    except Exception as e:
        print("\n" + "=" * 60)
        print("ERROR during training!")
        print("=" * 60)
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
