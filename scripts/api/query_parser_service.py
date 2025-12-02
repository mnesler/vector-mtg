#!/usr/bin/env python3
"""
Query Parser Service using a lightweight local LLM.
Parses natural language search queries into structured search parameters.
"""

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import json
import re
from typing import Dict, List


class QueryParserService:
    """Service for parsing natural language queries using a local LLM."""

    def __init__(self, model_name: str = "microsoft/Phi-3.5-mini-instruct"):
        """
        Initialize the query parser with a lightweight LLM.
        
        Args:
            model_name: HuggingFace model to use for parsing
        """
        print(f"Loading query parser model: {model_name}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto",
            trust_remote_code=True
        )
        self.model.eval()
        print(f"✓ Query parser ready (using {'GPU' if torch.cuda.is_available() else 'CPU'})")

    def parse_query_regex(self, query: str) -> Dict[str, any]:
        """
        Parse query using regex patterns (fast, deterministic).
        Falls back to LLM if pattern doesn't match.
        """
        exclusions = []
        positive_query = query

        # Pattern 1: "X, but only ones in Y" or "X, but only Y"
        only_pattern = r'(.+?),?\s+but\s+only\s+(?:ones\s+in\s+)?(\w+)'
        match = re.search(only_pattern, query, re.IGNORECASE)
        if match:
            creature_type = match.group(1).strip()
            desired_color = match.group(2).strip().lower()

            # Map to MTG colors and exclude others
            all_colors = {'white', 'blue', 'black', 'red', 'green'}
            if desired_color in all_colors:
                exclusions = [c for c in all_colors if c != desired_color]
                positive_query = f"{creature_type} {desired_color}"
                return {
                    "positive_query": positive_query,
                    "exclusions": exclusions,
                    "original_query": query
                }

        # Pattern 2: "X no Y" or "X without Y"
        no_pattern = r'(.+?)\s+(?:no|without)\s+(.+)'
        match = re.search(no_pattern, query, re.IGNORECASE)
        if match:
            positive_query = match.group(1).strip()
            exclusions = [match.group(2).strip()]
            return {
                "positive_query": positive_query,
                "exclusions": exclusions,
                "original_query": query
            }

        # No pattern matched, return as-is
        return None

    def parse_query(self, query: str) -> Dict[str, any]:
        """
        Parse a natural language search query into structured components.

        Args:
            query: Natural language search query

        Returns:
            Dictionary with:
                - positive_query: What to search FOR
                - exclusions: List of terms to EXCLUDE
                - original_query: Original input

        Examples:
            "vampires no black" -> {"positive_query": "vampires", "exclusions": ["black"]}
            "zombies, but only ones in blue" -> {"positive_query": "zombies blue", "exclusions": ["black", "red", "green", "white"]}
        """
        # Try regex-based parsing first (faster and more reliable)
        regex_result = self.parse_query_regex(query)
        if regex_result:
            return regex_result

        # If no pattern matches, use query as-is (LLM is unreliable for this task)
        return {
            "positive_query": query,
            "exclusions": [],
            "original_query": query
        }

    def _parse_query_llm(self, query: str) -> Dict[str, any]:
        """LLM-based query parsing (fallback for complex queries)."""
        prompt = f"""<|system|>You are a query parser for Magic: The Gathering card searches. Parse the user's query and extract what they want to search FOR and what they want to EXCLUDE. Return ONLY valid JSON, no markdown or extra text.<|end|>
<|user|>Parse this MTG search query into JSON format:

Query: "{query}"

Extract:
- positive_query: The main search terms (what to search FOR)
- exclusions: Array of terms to EXCLUDE from results

Rules:
- Words after "not", "no", "without", "exclude" are exclusions
- "but only" or "only ones in" means include ONLY that color and exclude others
- If query is ONLY exclusions, set positive_query to empty string

Examples:
"vampires no black" -> {{"positive_query": "vampires", "exclusions": ["black"]}}
"zombies, but only ones in blue" -> {{"positive_query": "zombies blue", "exclusions": ["black", "red", "green", "white"]}}
"legendary planeswalker blue, no landfall" -> {{"positive_query": "legendary planeswalker blue", "exclusions": ["landfall"]}}
"creatures without flying" -> {{"positive_query": "creatures", "exclusions": ["flying"]}}

Return ONLY the JSON object, nothing else:<|end|>
<|assistant|>"""

        # Generate response
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=150,
                num_beams=1,
                pad_token_id=self.tokenizer.eos_token_id,
                use_cache=False
            )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract JSON from response (remove prompt and find just the JSON)
        # Try to find JSON after the assistant tag
        response_after_prompt = response.split('<|assistant|>')[-1] if '<|assistant|>' in response else response

        # Find the first complete JSON object
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_after_prompt)
        if json_match:
            try:
                json_str = json_match.group(0)
                result = json.loads(json_str)
                result['original_query'] = query
                return result
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}")
                print(f"Extracted JSON: {json_match.group(0)}")
                print(f"Full response: {response}")
        
        # Fallback: return original query as positive
        print(f"Failed to parse LLM response, using fallback")
        return {
            "positive_query": query,
            "exclusions": [],
            "original_query": query
        }


# Global singleton instance
_parser_service = None


def get_query_parser(model_name: str = "microsoft/Phi-3.5-mini-instruct") -> QueryParserService:
    """
    Get or create the global query parser instance.
    Uses singleton pattern to avoid loading the model multiple times.
    
    Args:
        model_name: HuggingFace model name
        
    Returns:
        QueryParserService instance
    """
    global _parser_service
    if _parser_service is None:
        _parser_service = QueryParserService(model_name)
    return _parser_service
