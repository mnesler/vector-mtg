"""
LLM Prompt Builder for MTG Card Tag Extraction
===============================================
Generates optimized prompts for LLM-based tag extraction.

Extracted from: extract_card_tags.py
Refactoring Phase: 2
"""

from typing import List, Dict


def build_tag_extraction_prompt(
    card_name: str,
    oracle_text: str,
    type_line: str,
    available_tags: List[Dict]
) -> str:
    """
    Build the LLM prompt for tag extraction.

    Args:
        card_name: Name of the card
        oracle_text: Oracle rules text
        type_line: Card type line (e.g., "Creature — Human Wizard")
        available_tags: List of tag dictionaries from database with keys:
                       name, description, category, depth, parent_tag_name

    Returns:
        Formatted prompt string for LLM tag extraction

    Example:
        >>> tags = [
        ...     {"name": "artifact", "description": "Card is an artifact",
        ...      "category": "Card Types", "depth": 0, "parent_tag_name": None}
        ... ]
        >>> prompt = build_tag_extraction_prompt(
        ...     "Sol Ring", "{T}: Add {C}{C}.", "Artifact", tags
        ... )
    """
    # Group tags by category for better prompt organization
    tags_by_category = {}
    for tag in available_tags:
        category = tag['category']
        if category not in tags_by_category:
            tags_by_category[category] = []
        tags_by_category[category].append(tag)

    # Build tag list section
    tag_list_sections = []
    for category, tags in tags_by_category.items():
        tag_list_sections.append(f"\n**{category}:**")
        for tag in tags:
            indent = "  " * tag['depth']
            parent_info = f" (child of {tag['parent_tag_name']})" if tag['parent_tag_name'] else ""
            tag_list_sections.append(
                f"{indent}- `{tag['name']}`: {tag['description']}{parent_info}"
            )

    tag_list = "\n".join(tag_list_sections)

    prompt = f"""You are an expert MTG rules analyst. Your task is to extract functional mechanics tags from a Magic: The Gathering card.

**CARD TO ANALYZE:**
Name: {card_name}
Type: {type_line}
Oracle Text:
{oracle_text or '(No text)'}

---

**AVAILABLE TAGS:**
{tag_list}

---

**INSTRUCTIONS:**

1. **Read the card's oracle text carefully** - Focus on what the card DOES, not flavor
2. **Extract ONLY tags that directly apply** - Don't infer tags from card name or flavor
3. **Use child tags when specific, parent tags when general**
   - If a card generates blue mana specifically → use `generates_blue_mana`
   - If a card generates any color mana → use `generates_mana`
4. **Include card type tags** - Based on the type line
5. **Assign confidence scores (0.0 - 1.0)**:
   - 0.95-1.0: Explicitly stated in oracle text
   - 0.80-0.94: Clearly implied by the mechanics
   - 0.70-0.79: Likely but requires minor interpretation
   - 0.50-0.69: Uncertain, needs review
   - < 0.50: Very uncertain, probably wrong

6. **Return JSON ONLY** - No explanation, just the JSON array

**OUTPUT FORMAT:**
```json
[
  {{"tag": "tag_name", "confidence": 0.95}},
  {{"tag": "another_tag", "confidence": 0.88}}
]
```

**EXAMPLES:**

Card: "Sol Ring" | Type: Artifact | Text: "{{T}}: Add {{C}}{{C}}."
```json
[
  {{"tag": "artifact", "confidence": 1.0}},
  {{"tag": "generates_mana", "confidence": 1.0}},
  {{"tag": "generates_colorless_mana", "confidence": 1.0}}
]
```

Card: "Blood Artist" | Type: Creature — Vampire | Text: "Whenever Blood Artist or another creature dies, target player loses 1 life and you gain 1 life."
```json
[
  {{"tag": "creature", "confidence": 1.0}},
  {{"tag": "triggers_on_death", "confidence": 1.0}},
  {{"tag": "drains_life", "confidence": 0.95}},
  {{"tag": "gains_life", "confidence": 1.0}}
]
```

Now extract tags for the card above. Return ONLY the JSON array.
"""
    return prompt
