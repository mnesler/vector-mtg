"""
Format MTG training data for Qwen/Qwen2.5-1.5B-Instruct fine-tuning.

Qwen expects conversational format with system/user/assistant roles:
{
    "messages": [
        {"role": "system", "content": "You are an MTG deck building assistant."},
        {"role": "user", "content": "What cards work well with Sol Ring?"},
        {"role": "assistant", "content": "Sol Ring synergizes with..."}
    ]
}

This script converts Commander Spellbook data into this format.
"""

import json
import psycopg2
from typing import List, Dict, Any
import random
from pathlib import Path


class QwenDataFormatter:
    """Format MTG data for Qwen instruction tuning."""

    SYSTEM_PROMPTS = [
        "You are an expert Magic: The Gathering deck building assistant specializing in Commander and Standard formats.",
        "You are a knowledgeable MTG advisor helping players build competitive and casual decks.",
        "You are an AI assistant with deep knowledge of Magic: The Gathering combos, synergies, and deck building strategies.",
    ]

    def __init__(self, db_connection_string: str):
        """Initialize with database connection."""
        self.conn = psycopg2.connect(db_connection_string)
        self.cursor = self.conn.cursor()

    def format_combo_explanation(self, combo_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format: User asks about a combo, assistant explains it.

        Example:
        User: "How does the Hullbreaker Horror + Sol Ring combo work?"
        Assistant: "This combo creates infinite colorless mana. Here's how: ..."
        """
        card_names = combo_data['card_names']
        description = combo_data['description']
        features = combo_data.get('features', [])
        mana_needed = combo_data.get('mana_needed', '')

        # Generate natural variations of the question
        questions = [
            f"How does the {card_names} combo work?",
            f"Explain the {card_names} interaction.",
            f"What does {card_names} do together?",
            f"Can you describe the {card_names} combo?",
        ]

        # Build comprehensive answer
        answer_parts = []

        if features:
            feature_list = ', '.join(features)
            answer_parts.append(f"This combo produces: {feature_list}.")

        answer_parts.append(f"\nHow it works:\n{description}")

        if mana_needed:
            answer_parts.append(f"\nMana required: {mana_needed}")

        answer = '\n'.join(answer_parts)

        return {
            "messages": [
                {"role": "system", "content": random.choice(self.SYSTEM_PROMPTS)},
                {"role": "user", "content": random.choice(questions)},
                {"role": "assistant", "content": answer}
            ]
        }

    def format_card_synergy(self, synergy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format: User asks if cards work together, assistant explains synergy.

        Example:
        User: "Do Exquisite Blood and Sanguine Bond work together?"
        Assistant: "Yes! These cards create a powerful infinite life/damage combo..."
        """
        card1 = synergy_data['card_1_name']
        card2 = synergy_data['card_2_name']
        synergy_score = synergy_data['synergy_score']
        combos = synergy_data.get('combo_examples', [])

        questions = [
            f"Do {card1} and {card2} work together?",
            f"What's the synergy between {card1} and {card2}?",
            f"Should I play {card1} with {card2}?",
            f"How do {card1} and {card2} interact?",
        ]

        # Build answer based on synergy strength
        if synergy_score > 0.7:
            answer = f"Yes! {card1} and {card2} have excellent synergy"
        elif synergy_score > 0.4:
            answer = f"{card1} and {card2} work well together"
        else:
            answer = f"{card1} and {card2} can be played together but have limited synergy"

        if combos:
            answer += f". They appear together in popular combos like: {', '.join(combos[:3])}."

        answer += f" (Synergy score: {synergy_score:.2f})"

        return {
            "messages": [
                {"role": "system", "content": random.choice(self.SYSTEM_PROMPTS)},
                {"role": "user", "content": random.choice(questions)},
                {"role": "assistant", "content": answer}
            ]
        }

    def format_deck_recommendation(self, deck_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format: User asks for deck suggestions, assistant recommends cards/combos.

        Example:
        User: "What combos should I include in my Simic deck?"
        Assistant: "For a Simic deck, consider these combos: ..."
        """
        colors = deck_data.get('colors', [])
        format_name = deck_data.get('format', 'Commander')
        budget = deck_data.get('budget', None)
        recommended_combos = deck_data.get('combos', [])

        color_name = self._get_color_identity_name(colors)

        questions = [
            f"What combos work in {color_name} {format_name}?",
            f"Suggest combos for my {color_name} deck.",
            f"What are the best {color_name} combos in {format_name}?",
        ]

        if budget:
            questions.append(f"What {color_name} combos can I build for under ${budget}?")

        answer_parts = [f"Here are excellent {color_name} combos for {format_name}:"]

        for i, combo in enumerate(recommended_combos[:5], 1):
            combo_text = f"\n{i}. {combo['cards']}"
            if combo.get('features'):
                combo_text += f" - {', '.join(combo['features'])}"
            if budget and combo.get('price'):
                combo_text += f" (${combo['price']:.2f})"
            answer_parts.append(combo_text)

        return {
            "messages": [
                {"role": "system", "content": random.choice(self.SYSTEM_PROMPTS)},
                {"role": "user", "content": random.choice(questions)},
                {"role": "assistant", "content": '\n'.join(answer_parts)}
            ]
        }

    def format_card_alternatives(self, card_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format: User asks for card alternatives, assistant suggests similar cards.

        Example:
        User: "What cards are similar to Sol Ring?"
        Assistant: "Cards similar to Sol Ring include: Mana Crypt, Mana Vault..."
        """
        card_name = card_data['card_name']
        alternatives = card_data.get('alternatives', [])

        questions = [
            f"What cards are similar to {card_name}?",
            f"What can I use instead of {card_name}?",
            f"Give me alternatives to {card_name}.",
            f"What's a budget alternative to {card_name}?",
        ]

        answer_parts = [f"Cards similar to {card_name}:"]

        for i, alt in enumerate(alternatives[:5], 1):
            alt_text = f"\n{i}. {alt['name']}"
            if alt.get('price'):
                alt_text += f" (${alt['price']:.2f})"
            if alt.get('reason'):
                alt_text += f" - {alt['reason']}"
            answer_parts.append(alt_text)

        return {
            "messages": [
                {"role": "system", "content": random.choice(self.SYSTEM_PROMPTS)},
                {"role": "user", "content": random.choice(questions)},
                {"role": "assistant", "content": '\n'.join(answer_parts)}
            ]
        }

    def _get_color_identity_name(self, colors: List[str]) -> str:
        """Convert color identity array to name (e.g., ['U', 'G'] -> 'Simic')."""
        color_combos = {
            frozenset(['W', 'U']): 'Azorius',
            frozenset(['U', 'B']): 'Dimir',
            frozenset(['B', 'R']): 'Rakdos',
            frozenset(['R', 'G']): 'Gruul',
            frozenset(['G', 'W']): 'Selesnya',
            frozenset(['W', 'B']): 'Orzhov',
            frozenset(['U', 'R']): 'Izzet',
            frozenset(['B', 'G']): 'Golgari',
            frozenset(['R', 'W']): 'Boros',
            frozenset(['G', 'U']): 'Simic',
        }

        if not colors:
            return 'colorless'
        elif len(colors) == 1:
            color_names = {'W': 'white', 'U': 'blue', 'B': 'black', 'R': 'red', 'G': 'green'}
            return color_names.get(colors[0], 'unknown')
        elif len(colors) == 2:
            return color_combos.get(frozenset(colors), '-'.join(colors))
        else:
            return f"{len(colors)}-color"

    def extract_combo_training_data(self, limit: int = 10000) -> List[Dict[str, Any]]:
        """Extract combo explanations from database."""
        query = """
        SELECT
            v.id AS combo_id,
            array_to_string(array_agg(DISTINCT c.name ORDER BY c.name), ' + ') AS card_names,
            v.description,
            v.mana_needed,
            v.identity AS colors,
            v.popularity,
            array_agg(DISTINCT f.name) FILTER (WHERE f.name IS NOT NULL) AS features
        FROM variants v
        JOIN variant_cards vc ON v.id = vc.variant_id
        JOIN cards c ON vc.card_id = c.id
        LEFT JOIN variant_features vf ON v.id = vf.variant_id
        LEFT JOIN features f ON vf.feature_id = f.id
        WHERE v.status = 'OK'
          AND v.description IS NOT NULL
          AND v.description != ''
        GROUP BY v.id, v.description, v.mana_needed, v.identity, v.popularity
        ORDER BY v.popularity DESC
        LIMIT %s
        """

        self.cursor.execute(query, (limit,))
        results = []

        for row in self.cursor.fetchall():
            results.append({
                'card_names': row[1],
                'description': row[2],
                'mana_needed': row[3],
                'colors': row[4],
                'features': row[6] if row[6] else []
            })

        return results

    def extract_synergy_training_data(self, limit: int = 5000) -> List[Dict[str, Any]]:
        """Extract card synergy pairs from database."""
        query = """
        SELECT
            c1.name AS card_1_name,
            c2.name AS card_2_name,
            AVG(v.popularity) / 1000.0 AS synergy_score,
            array_agg(DISTINCT v.id ORDER BY v.popularity DESC) AS combo_ids
        FROM variant_cards vc1
        JOIN variant_cards vc2 ON vc1.variant_id = vc2.variant_id AND vc1.card_id < vc2.card_id
        JOIN cards c1 ON vc1.card_id = c1.id
        JOIN cards c2 ON vc2.card_id = c2.id
        JOIN variants v ON vc1.variant_id = v.id
        WHERE v.status = 'OK'
        GROUP BY c1.name, c2.name
        HAVING COUNT(DISTINCT vc1.variant_id) >= 3
        ORDER BY synergy_score DESC
        LIMIT %s
        """

        self.cursor.execute(query, (limit,))
        results = []

        for row in self.cursor.fetchall():
            results.append({
                'card_1_name': row[0],
                'card_2_name': row[1],
                'synergy_score': float(row[2]),
                'combo_examples': row[3][:3] if row[3] else []
            })

        return results

    def generate_training_dataset(
        self,
        output_file: str,
        combo_samples: int = 5000,
        synergy_samples: int = 2000
    ):
        """Generate complete training dataset in Qwen format."""

        print("Extracting combo data...")
        combos = self.extract_combo_training_data(limit=combo_samples)

        print("Extracting synergy data...")
        synergies = self.extract_synergy_training_data(limit=synergy_samples)

        print("Formatting data for Qwen...")
        training_examples = []

        # Format combos
        for combo in combos:
            training_examples.append(self.format_combo_explanation(combo))

        # Format synergies
        for synergy in synergies:
            training_examples.append(self.format_card_synergy(synergy))

        # Shuffle for better training
        random.shuffle(training_examples)

        # Write to JSONL (one JSON object per line)
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"Writing {len(training_examples)} examples to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            for example in training_examples:
                f.write(json.dumps(example, ensure_ascii=False) + '\n')

        print(f"✓ Training data saved to {output_file}")
        print(f"  Total examples: {len(training_examples)}")
        print(f"  - Combo explanations: {len(combos)}")
        print(f"  - Card synergies: {len(synergies)}")

        # Generate validation split (10%)
        val_size = len(training_examples) // 10
        val_file = output_file.replace('.jsonl', '_validation.jsonl')

        print(f"\nCreating validation set ({val_size} examples)...")
        with open(val_file, 'w', encoding='utf-8') as f:
            for example in training_examples[:val_size]:
                f.write(json.dumps(example, ensure_ascii=False) + '\n')

        print(f"✓ Validation data saved to {val_file}")

        return {
            'train_file': output_file,
            'val_file': val_file,
            'train_count': len(training_examples) - val_size,
            'val_count': val_size
        }


def main():
    """Main execution."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Format MTG data for Qwen/Qwen2.5-1.5B-Instruct fine-tuning"
    )
    parser.add_argument(
        '--db-connection',
        type=str,
        default='postgresql://localhost/commander_spellbook',
        help='PostgreSQL connection string'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='../data/qwen_training.jsonl',
        help='Output JSONL file path'
    )
    parser.add_argument(
        '--combo-samples',
        type=int,
        default=5000,
        help='Number of combo examples to generate'
    )
    parser.add_argument(
        '--synergy-samples',
        type=int,
        default=2000,
        help='Number of synergy examples to generate'
    )

    args = parser.parse_args()

    formatter = QwenDataFormatter(args.db_connection)

    try:
        result = formatter.generate_training_dataset(
            output_file=args.output,
            combo_samples=args.combo_samples,
            synergy_samples=args.synergy_samples
        )

        print("\n" + "="*60)
        print("DATASET GENERATION COMPLETE")
        print("="*60)
        print(f"Training file: {result['train_file']} ({result['train_count']} examples)")
        print(f"Validation file: {result['val_file']} ({result['val_count']} examples)")
        print("\nNext steps:")
        print("1. Review sample examples in the generated files")
        print("2. Run training with: python train_qwen_lora.py")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        formatter.conn.close()


if __name__ == '__main__':
    main()
