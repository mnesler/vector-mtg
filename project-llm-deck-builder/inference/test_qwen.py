"""
Test inference script for fine-tuned Qwen MTG deck building model.

Usage:
    python test_qwen.py --model_path ../models/qwen-mtg-lora
    python test_qwen.py --model_path ../models/qwen-mtg-lora --prompt "What combos work in Simic?"
"""

import argparse
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel


def load_finetuned_model(model_path: str, base_model: str = "Qwen/Qwen2.5-1.5B-Instruct"):
    """Load fine-tuned LoRA model."""
    print(f"Loading base model: {base_model}")

    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        trust_remote_code=True
    )

    base = AutoModelForCausalLM.from_pretrained(
        base_model,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True
    )

    print(f"Loading LoRA weights from: {model_path}")
    model = PeftModel.from_pretrained(base, model_path)
    model.eval()

    return model, tokenizer


def generate_response(
    model,
    tokenizer,
    user_prompt: str,
    system_prompt: str = "You are an expert Magic: The Gathering deck building assistant specializing in Commander and Standard formats.",
    max_new_tokens: int = 300,
    temperature: float = 0.7,
    top_p: float = 0.9,
):
    """Generate response from fine-tuned model."""

    # Format as chat
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    # Apply chat template
    formatted_prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    # Tokenize
    inputs = tokenizer(formatted_prompt, return_tensors="pt").to(model.device)

    # Generate
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            do_sample=True,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    # Decode
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Extract just the assistant's response
    # Remove the input prompt from the output
    if formatted_prompt in response:
        response = response[len(formatted_prompt):].strip()

    return response


def run_interactive_mode(model, tokenizer):
    """Run interactive chat mode."""
    print("\n" + "="*60)
    print("MTG Deck Building Assistant - Interactive Mode")
    print("="*60)
    print("Type your questions about MTG deck building.")
    print("Type 'exit' or 'quit' to end.\n")

    while True:
        try:
            user_input = input("You: ").strip()

            if user_input.lower() in ['exit', 'quit']:
                print("Goodbye!")
                break

            if not user_input:
                continue

            print("\nAssistant: ", end="", flush=True)
            response = generate_response(model, tokenizer, user_input)
            print(response + "\n")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


def run_test_prompts(model, tokenizer):
    """Run a series of test prompts."""

    test_prompts = [
        "How does the Hullbreaker Horror + Sol Ring combo work?",
        "What combos work in Simic Commander?",
        "Do Exquisite Blood and Sanguine Bond work together?",
        "What's a budget alternative to Mana Crypt?",
        "What are the best infinite mana combos?",
    ]

    print("\n" + "="*60)
    print("Running Test Prompts")
    print("="*60 + "\n")

    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n[Test {i}/{len(test_prompts)}]")
        print(f"User: {prompt}")
        print("-" * 60)

        response = generate_response(model, tokenizer, prompt)
        print(f"Assistant: {response}")
        print("="*60)


def main():
    parser = argparse.ArgumentParser(description="Test fine-tuned Qwen MTG model")
    parser.add_argument(
        "--model_path",
        type=str,
        required=True,
        help="Path to fine-tuned LoRA model"
    )
    parser.add_argument(
        "--base_model",
        type=str,
        default="Qwen/Qwen2.5-1.5B-Instruct",
        help="Base model name"
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default=None,
        help="Single prompt to test (optional)"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run test prompts"
    )
    parser.add_argument(
        "--max_new_tokens",
        type=int,
        default=300,
        help="Maximum tokens to generate"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Sampling temperature"
    )

    args = parser.parse_args()

    # Load model
    model, tokenizer = load_finetuned_model(args.model_path, args.base_model)

    print(f"\n✓ Model loaded successfully from {args.model_path}")

    # Run appropriate mode
    if args.prompt:
        # Single prompt mode
        print(f"\nUser: {args.prompt}")
        print("-" * 60)
        response = generate_response(
            model,
            tokenizer,
            args.prompt,
            max_new_tokens=args.max_new_tokens,
            temperature=args.temperature
        )
        print(f"Assistant: {response}\n")

    elif args.test:
        # Test prompts mode
        run_test_prompts(model, tokenizer)

    elif args.interactive:
        # Interactive mode
        run_interactive_mode(model, tokenizer)

    else:
        # Default: run test prompts
        print("\nNo mode specified. Running test prompts...")
        print("Use --interactive for chat mode or --prompt for single query\n")
        run_test_prompts(model, tokenizer)


if __name__ == "__main__":
    main()
