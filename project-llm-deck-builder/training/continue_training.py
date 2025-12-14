"""
Continue training an existing Qwen LoRA model with new data.

This script allows you to add new training data to your existing model
without starting from scratch. Useful for incremental updates.

Usage:
    python continue_training.py \
        --existing_model ../models/qwen-mtg-lora \
        --new_data ../data/new_combos.jsonl \
        --output_dir ../models/qwen-mtg-lora-v2 \
        --epochs 1
"""

import argparse
import json
from pathlib import Path
from train_qwen_lora import QwenTrainingConfig, train


def merge_datasets(existing_train: str, new_data: str, output_file: str, keep_old_ratio: float = 0.3):
    """
    Merge existing and new training data, optionally downsampling old data
    to prevent catastrophic forgetting while focusing on new patterns.

    Args:
        existing_train: Path to original training data
        new_data: Path to new training data
        output_file: Where to save merged data
        keep_old_ratio: Fraction of old data to keep (0.3 = 30%)
    """
    import random

    print(f"\nMerging datasets...")
    print(f"  Existing: {existing_train}")
    print(f"  New data: {new_data}")
    print(f"  Keep old ratio: {keep_old_ratio}")

    # Load old data
    old_examples = []
    if Path(existing_train).exists():
        with open(existing_train, 'r') as f:
            old_examples = [json.loads(line) for line in f]
        print(f"  Loaded {len(old_examples)} old examples")

    # Load new data
    new_examples = []
    with open(new_data, 'r') as f:
        new_examples = [json.loads(line) for line in f]
    print(f"  Loaded {len(new_examples)} new examples")

    # Sample old data
    if keep_old_ratio < 1.0:
        keep_count = int(len(old_examples) * keep_old_ratio)
        old_examples = random.sample(old_examples, keep_count)
        print(f"  Sampled {len(old_examples)} old examples ({keep_old_ratio*100:.0f}%)")

    # Merge
    merged = old_examples + new_examples
    random.shuffle(merged)

    # Save
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        for example in merged:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')

    print(f"  ✓ Saved {len(merged)} merged examples to {output_file}")
    print(f"    - Old examples: {len(old_examples)}")
    print(f"    - New examples: {len(new_examples)}")

    return len(old_examples), len(new_examples)


def main():
    parser = argparse.ArgumentParser(
        description="Continue training existing Qwen LoRA model with new data"
    )

    # Model paths
    parser.add_argument(
        "--existing_model",
        type=str,
        required=True,
        help="Path to existing LoRA model to continue training"
    )
    parser.add_argument(
        "--new_data",
        type=str,
        required=True,
        help="Path to new training data (JSONL)"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        required=True,
        help="Output directory for updated model"
    )

    # Optional: include old training data
    parser.add_argument(
        "--old_train_file",
        type=str,
        default=None,
        help="Path to original training data (to prevent catastrophic forgetting)"
    )
    parser.add_argument(
        "--keep_old_ratio",
        type=float,
        default=0.3,
        help="Fraction of old data to include (0.0-1.0). Default: 0.3 (30%%)"
    )

    # Training params
    parser.add_argument(
        "--epochs",
        type=int,
        default=1,
        help="Number of epochs (use 1-2 for continued training)"
    )
    parser.add_argument(
        "--learning_rate",
        type=float,
        default=1e-4,
        help="Learning rate (lower than initial training). Default: 1e-4"
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=4,
        help="Batch size"
    )

    args = parser.parse_args()

    # Validate paths
    if not Path(args.existing_model).exists():
        print(f"Error: Existing model not found at {args.existing_model}")
        return

    if not Path(args.new_data).exists():
        print(f"Error: New data not found at {args.new_data}")
        return

    print("\n" + "="*60)
    print("CONTINUED TRAINING CONFIGURATION")
    print("="*60)
    print(f"Existing model: {args.existing_model}")
    print(f"New data: {args.new_data}")
    print(f"Output: {args.output_dir}")
    print(f"Epochs: {args.epochs} (recommended: 1-2 for continued training)")
    print(f"Learning rate: {args.learning_rate} (lower than initial training)")
    print("="*60 + "\n")

    # Merge datasets if old training data provided
    train_file = args.new_data
    if args.old_train_file and Path(args.old_train_file).exists():
        merged_file = Path(args.output_dir) / "merged_training.jsonl"
        old_count, new_count = merge_datasets(
            args.old_train_file,
            args.new_data,
            str(merged_file),
            args.keep_old_ratio
        )
        train_file = str(merged_file)

        print(f"\n💡 TIP: Merged {old_count} old + {new_count} new examples")
        print(f"   This helps prevent catastrophic forgetting while learning new patterns.\n")
    else:
        print("\n⚠️  WARNING: Training only on new data without old examples")
        print("   Model may forget previously learned patterns (catastrophic forgetting)")
        print("   Consider using --old_train_file to include some old data\n")

    # Create training config
    config = QwenTrainingConfig(
        model_name=args.existing_model,  # Start from existing LoRA model
        train_file=train_file,
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        learning_rate=args.learning_rate,
    )

    # Train
    print("\n" + "="*60)
    print("Starting continued training...")
    print("="*60 + "\n")

    try:
        trainer = train(config)

        print("\n" + "="*60)
        print("SUCCESS! Continued training complete.")
        print("="*60)
        print(f"\nUpdated model saved to: {args.output_dir}")
        print("\nNext steps:")
        print("1. Test the updated model:")
        print(f"   python ../inference/test_qwen.py --model_path {args.output_dir} --test")
        print("2. Compare with original model:")
        print(f"   python ../inference/test_qwen.py --model_path {args.existing_model} --test")

    except Exception as e:
        print(f"\nError during training: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
