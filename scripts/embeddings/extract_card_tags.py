"""
MTG Card Tag Extraction using LLM
==================================
Extracts functional mechanics tags from MTG cards using an LLM.

This is Phase 2 of the incremental tagging system:
1. ✅ Schema deployed with 65 tags across 10 categories
2. → LLM extraction function (this file)
3. Test on sample cards
4. Batch process all cards
5. Build abstraction extractor

Author: Generated with Claude Code
Date: 2025-12-13
"""

import os
import sys
import json
import time
from typing import List, Dict, Optional
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import data models and utilities
from embeddings.models import TagResult, CardTagExtraction
from embeddings.rate_limit_handler import handle_rate_limit
from embeddings.prompt_builder import build_tag_extraction_prompt
from embeddings.database import (
    get_default_db_connection_string,
    load_tag_taxonomy,
    store_card_tags
)

# LLM provider imports
try:
    from anthropic import Anthropic, RateLimitError
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    RateLimitError = None

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CardTagExtractor:
    """
    Extracts functional mechanics tags from MTG cards using LLM.

    Features:
    - Loads tag taxonomy from database
    - Generates optimized prompts for LLM
    - Parses and validates LLM responses
    - Returns confidence-scored tags
    """

    def __init__(
        self,
        llm_model: Optional[str] = None,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        db_connection_string: Optional[str] = None
    ):
        """
        Initialize the tag extractor.

        Args:
            llm_model: Model to use. If None, auto-selects based on provider:
                       - Claude: "claude-3-5-haiku-20241022" (fast, cheap)
                       - OpenAI: "gpt-4o-mini"
                       - Ollama: "qwen2.5:7b-instruct-q4_K_M" (local, free)
            provider: "anthropic", "openai", or "ollama". If None, auto-detects from env vars
            api_key: API key (defaults to ANTHROPIC_API_KEY or OPENAI_API_KEY). Not needed for Ollama.
            db_connection_string: PostgreSQL connection string
        """
        # Auto-detect provider if not specified
        if provider is None:
            if os.getenv('ANTHROPIC_API_KEY'):
                provider = 'anthropic'
            elif os.getenv('OPENAI_API_KEY'):
                provider = 'openai'
            else:
                # Default to ollama if no API keys found
                provider = 'ollama'

        self.provider = provider.lower()

        # Auto-select model if not specified
        if llm_model is None:
            if self.provider == 'anthropic':
                llm_model = "claude-3-5-haiku-20241022"  # Fast and cheap
            elif self.provider == 'openai':
                llm_model = "gpt-4o-mini"
            elif self.provider == 'ollama':
                llm_model = "qwen2.5:7b-instruct-q4_K_M"  # Local, free

        self.llm_model = llm_model

        # Initialize client based on provider
        if self.provider == 'anthropic':
            if not ANTHROPIC_AVAILABLE:
                raise ImportError("anthropic package not installed. Run: pip install anthropic")
            self.client = Anthropic(api_key=api_key or os.getenv('ANTHROPIC_API_KEY'))
        elif self.provider == 'openai':
            if not OPENAI_AVAILABLE:
                raise ImportError("openai package not installed. Run: pip install openai")
            self.client = OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
        elif self.provider == 'ollama':
            if not OLLAMA_AVAILABLE:
                raise ImportError("ollama package not installed. Run: pip install ollama")
            self.client = None  # Ollama uses module-level functions
        else:
            raise ValueError(f"Unknown provider: {provider}. Use 'anthropic', 'openai', or 'ollama'")

        self.db_conn_string = db_connection_string or self._get_default_db_string()
        self.available_tags = []
        self.tag_taxonomy_loaded = False

        logger.info(f"Initialized CardTagExtractor with {self.provider} ({self.llm_model})")

    def _get_default_db_string(self) -> str:
        """Get default database connection string from environment"""
        return get_default_db_connection_string()

    def load_tag_taxonomy(self) -> None:
        """
        Load available tags from database.

        Loads tags with their categories, descriptions, and hierarchy info.
        This is called once and cached for all subsequent extractions.
        """
        logger.info("Loading tag taxonomy from database...")
        self.available_tags = load_tag_taxonomy(self.db_conn_string)
        self.tag_taxonomy_loaded = True
        logger.info(f"Loaded {len(self.available_tags)} tags from database")

    def _build_extraction_prompt(
        self,
        card_name: str,
        oracle_text: str,
        type_line: str
    ) -> str:
        """
        Build the LLM prompt for tag extraction.

        Args:
            card_name: Name of the card
            oracle_text: Oracle rules text
            type_line: Card type line (e.g., "Creature — Human Wizard")

        Returns:
            Formatted prompt string
        """
        if not self.tag_taxonomy_loaded:
            self.load_tag_taxonomy()

        return build_tag_extraction_prompt(
            card_name=card_name,
            oracle_text=oracle_text,
            type_line=type_line,
            available_tags=self.available_tags
        )

    def extract_tags(
        self,
        card_name: str,
        oracle_text: str,
        type_line: str,
        card_id: Optional[str] = None,
        max_retries: int = 5
    ) -> CardTagExtraction:
        """
        Extract functional tags from a card using LLM.

        Automatically retries on rate limit errors with exponential backoff.

        Args:
            card_name: Name of the card
            oracle_text: Oracle rules text
            type_line: Card type line
            card_id: Optional card UUID for tracking
            max_retries: Maximum number of retries on rate limit (default: 5)

        Returns:
            CardTagExtraction with extracted tags and confidence scores
        """
        retry_count = 0

        while retry_count <= max_retries:
            try:
                prompt = self._build_extraction_prompt(card_name, oracle_text, type_line)

                logger.debug(f"Extracting tags for: {card_name} (attempt {retry_count + 1}/{max_retries + 1})")

                # Call appropriate API based on provider
                if self.provider == 'anthropic':
                    response = self.client.messages.create(
                        model=self.llm_model,
                        max_tokens=1000,
                        temperature=0.1,
                        system="You are an MTG rules expert that extracts functional tags from cards. Return only valid JSON.",
                        messages=[
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ]
                    )
                    content = response.content[0].text.strip()

                elif self.provider == 'openai':
                    response = self.client.chat.completions.create(
                        model=self.llm_model,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are an MTG rules expert that extracts functional tags from cards. Return only valid JSON."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        temperature=0.1,
                        max_tokens=500
                    )
                    content = response.choices[0].message.content.strip()

                elif self.provider == 'ollama':
                    if not OLLAMA_AVAILABLE:
                        raise RuntimeError("Ollama package not installed. Install with: pip install ollama")
                    
                    response = ollama.chat(
                        model=self.llm_model,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are an MTG rules expert that extracts functional tags from cards. Return only valid JSON."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        options={
                            "temperature": 0.1,
                            "num_predict": 500
                        }
                    )
                    content = response['message']['content'].strip()

                else:
                    raise ValueError(f"Unsupported provider: {self.provider}")

                # Extract JSON from markdown code blocks if present
                if content.startswith("```json"):
                    content = content.split("```json")[1].split("```")[0].strip()
                elif content.startswith("```"):
                    content = content.split("```")[1].split("```")[0].strip()

                tags_data = json.loads(content)

                # Validate and convert to TagResult objects
                tags = []
                for tag_dict in tags_data:
                    tag_name = tag_dict.get('tag')
                    confidence = float(tag_dict.get('confidence', 0.0))

                    # Validate tag exists in taxonomy
                    if not any(t['name'] == tag_name for t in self.available_tags):
                        logger.warning(f"LLM returned unknown tag '{tag_name}' for {card_name}, skipping")
                        continue

                    # Validate confidence range
                    if not 0.0 <= confidence <= 1.0:
                        logger.warning(f"Invalid confidence {confidence} for tag '{tag_name}', clamping to [0,1]")
                        confidence = max(0.0, min(1.0, confidence))

                    tags.append(TagResult(
                        tag=tag_name,
                        confidence=confidence
                    ))

                logger.info(f"Extracted {len(tags)} tags for {card_name}")

                return CardTagExtraction(
                    card_id=card_id or '',
                    card_name=card_name,
                    tags=tags,
                    extraction_successful=True
                )

            except Exception as e:
                # Check if this is a rate limit error
                is_rate_limit = (
                    RateLimitError is not None and isinstance(e, RateLimitError)
                ) or (
                    # Also check by error type name for OpenAI
                    type(e).__name__ == 'RateLimitError'
                )

                if is_rate_limit:
                    retry_count += 1
                    if retry_count > max_retries:
                        logger.error(f"Rate limit exceeded after {max_retries} retries for {card_name}")
                        return CardTagExtraction(
                            card_id=card_id or '',
                            card_name=card_name,
                            tags=[],
                            extraction_successful=False,
                            error_message=f"Rate limit exceeded after {max_retries} retries"
                        )

                    # Wait for rate limit to reset
                    handle_rate_limit(e)
                    logger.info(f"Retrying extraction for {card_name} (attempt {retry_count + 1}/{max_retries + 1})")
                    continue

                # Not a rate limit error, fall through to other error handlers
                raise

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response for {card_name}: {e}")
                logger.error(f"Response was: {content}")
                return CardTagExtraction(
                    card_id=card_id or '',
                    card_name=card_name,
                    tags=[],
                    extraction_successful=False,
                    error_message=f"JSON parse error: {str(e)}"
                )

            except Exception as e:
                logger.error(f"Failed to extract tags for {card_name}: {e}")
                return CardTagExtraction(
                    card_id=card_id or '',
                    card_name=card_name,
                    tags=[],
                    extraction_successful=False,
                    error_message=str(e)
                )

    def store_tags(
        self,
        extraction: CardTagExtraction,
        extraction_prompt_version: str = "1.0"
    ) -> bool:
        """
        Store extracted tags in the database.

        The trigger `update_card_tag_cache_trigger` will automatically:
        - Update cards.tag_cache[]
        - Calculate cards.tag_confidence_avg
        - Add to review queue if confidence < 0.7

        Args:
            extraction: CardTagExtraction result from extract_tags()
            extraction_prompt_version: Version string for tracking prompt iterations

        Returns:
            True if successful, False otherwise
        """
        return store_card_tags(
            extraction=extraction,
            db_conn_string=self.db_conn_string,
            llm_model=self.llm_model,
            llm_provider=self.provider,
            extraction_prompt_version=extraction_prompt_version
        )


def test_extraction_on_known_cards():
    """
    Test the extraction function on well-known combo cards.

    This validates that the LLM correctly identifies key mechanics.
    """
    logger.info("=" * 80)
    logger.info("TESTING TAG EXTRACTION ON KNOWN COMBO CARDS")
    logger.info("=" * 80)

    extractor = CardTagExtractor()
    extractor.load_tag_taxonomy()

    # Define test cards with expected tags
    test_cards = [
        {
            "name": "Pemmin's Aura",
            "type": "Enchantment — Aura",
            "text": """Enchant creature
{U}: Enchanted creature gains flying until end of turn.
{U}: Untap enchanted creature.
{1}: Enchanted creature gets +1/-1 or -1/+1 until end of turn.""",
            "expected_tags": ["untaps_permanents", "grants_abilities", "enchantment", "aura", "infinite_enabler"]
        },
        {
            "name": "Sol Ring",
            "type": "Artifact",
            "text": "{T}: Add {C}{C}.",
            "expected_tags": ["artifact", "generates_mana", "generates_colorless_mana"]
        },
        {
            "name": "Blood Artist",
            "type": "Creature — Vampire",
            "text": "Whenever Blood Artist or another creature dies, target player loses 1 life and you gain 1 life.",
            "expected_tags": ["creature", "triggers_on_death", "drains_life", "gains_life"]
        },
        {
            "name": "Ashnod's Altar",
            "type": "Artifact",
            "text": "Sacrifice a creature: Add {C}{C}.",
            "expected_tags": ["artifact", "sacrifices_creatures", "generates_mana", "generates_colorless_mana"]
        },
        {
            "name": "Thassa's Oracle",
            "type": "Creature — Merfolk Wizard",
            "text": """When Thassa's Oracle enters the battlefield, look at the top X cards of your library, where X is your devotion to blue. Put up to one of them on top of your library and the rest on the bottom of your library in a random order. If X is greater than or equal to the number of cards in your library, you win the game.""",
            "expected_tags": ["creature", "triggers_on_etb", "wins_with_empty_library", "alternate_win_con"]
        }
    ]

    results = []
    for card in test_cards:
        print(f"\n{'=' * 80}")
        print(f"Testing: {card['name']}")
        print(f"{'=' * 80}")

        extraction = extractor.extract_tags(
            card_name=card['name'],
            oracle_text=card['text'],
            type_line=card['type']
        )

        if extraction.extraction_successful:
            print(f"✅ Extraction successful")
            print(f"\nExtracted {len(extraction.tags)} tags:")
            for tag in extraction.tags:
                emoji = "✅" if tag.tag in card['expected_tags'] else "⚠️"
                print(f"  {emoji} {tag.tag}: {tag.confidence:.2f}")

            print(f"\nExpected tags: {', '.join(card['expected_tags'])}")

            # Check coverage
            extracted_tag_names = {tag.tag for tag in extraction.tags}
            expected_tag_names = set(card['expected_tags'])
            missing = expected_tag_names - extracted_tag_names
            extra = extracted_tag_names - expected_tag_names

            if missing:
                print(f"\n❌ Missing expected tags: {', '.join(missing)}")
            if extra:
                print(f"\n⚠️  Extra tags (not expected): {', '.join(extra)}")

            if not missing and not extra:
                print(f"\n🎉 Perfect match!")

            results.append({
                "card": card['name'],
                "success": True,
                "missing": list(missing),
                "extra": list(extra)
            })
        else:
            print(f"❌ Extraction failed: {extraction.error_message}")
            results.append({
                "card": card['name'],
                "success": False,
                "error": extraction.error_message
            })

    # Summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    successful = sum(1 for r in results if r['success'])
    print(f"Successful extractions: {successful}/{len(results)}")

    perfect_matches = sum(
        1 for r in results
        if r['success'] and not r.get('missing') and not r.get('extra')
    )
    print(f"Perfect matches: {perfect_matches}/{len(results)}")


if __name__ == "__main__":
    # Run test suite
    test_extraction_on_known_cards()
