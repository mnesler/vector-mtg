# AI-Powered Synergy Discovery

**The Question:** Can we discover NEW synergies that the community hasn't documented?

**The Answer:** YES! Multiple approaches are possible.

**Current State:** 36,111 known combos from Commander Spellbook (human-curated)

**Potential:** Likely 100,000+ undiscovered combos in the 508,686 card dataset

---

## Table of Contents

1. [The Problem: Known vs Unknown Synergies](#the-problem-known-vs-unknown-synergies)
2. [Approach 1: Card Tagging + Pattern Matching](#approach-1-card-tagging--pattern-matching)
3. [Approach 2: Embedding-Based Discovery](#approach-2-embedding-based-discovery)
4. [Approach 3: Rules Engine Simulation](#approach-3-rules-engine-simulation)
5. [Approach 4: Graph Mining](#approach-4-graph-mining)
6. [Approach 5: LLM-Based Prediction](#approach-5-llm-based-prediction)
7. [Hybrid Approach (Recommended)](#hybrid-approach-recommended)
8. [Implementation Strategy](#implementation-strategy)

---

## The Problem: Known vs Unknown Synergies

### What We Have (Known Combos)

**Commander Spellbook:** 36,111 combos
- Human-curated
- Primarily popular/well-known combos
- Focused on Commander format
- High confidence (community verified)

**Coverage estimate:** ~5-10% of all possible combos

### What We're Missing (Unknown Combos)

**Undocumented synergies:**
- Budget alternatives using similar cards
- Newly released cards not yet in database
- Obscure/janky combos
- Format-specific combos (Standard, Modern, etc.)
- Multi-card interactions (5+ cards)

**Potential:** 100,000+ undiscovered combos

---

## Approach 1: Card Tagging + Pattern Matching

### The Idea

Tag cards with **functional categories**, then find matching patterns.

### Card Tag Taxonomy

**Mechanic Tags:**
```
Resource Generation:
  - generates_mana
  - draws_cards
  - creates_tokens
  - searches_library
  - reanimates

Resource Costs:
  - sacrifices_creatures
  - sacrifices_artifacts
  - discards_cards
  - pays_life
  - taps_permanents

State Changes:
  - untaps_permanents
  - blinks_creatures
  - bounces_permanents
  - recurs_from_graveyard
  - reduces_costs

Triggers:
  - triggers_on_etb
  - triggers_on_death
  - triggers_on_cast
  - triggers_on_draw
  - triggers_on_attack

Win Conditions:
  - alternate_win_con
  - drains_life
  - mills_library
  - deals_damage
  - creates_emblem
```

### Pattern Recognition

**Example Pattern: Infinite Loop**

```python
# Pattern: Untapper + Mana Producer = Infinite Mana
pattern = {
    "card_1": {
        "tags": ["untaps_permanents"],
        "cost_type": "mana"  # Or "free", "tap", etc.
    },
    "card_2": {
        "tags": ["generates_mana", "taps_for_mana"],
        "produces_more_than": "card_1.cost"  # Produces more than it costs to untap
    }
}

# Find matches
combos = find_matching_pattern(pattern)
```

**Results:**
```
✓ Hullbreaker Horror (untaps when you cast) + Sol Ring (taps for 2, costs 1 to replay)
✓ Aphetto Alchemist (untaps for cost) + Gilded Lotus (taps for 3)
✓ Pemmin's Aura (untaps) + Bloom Tender (taps for multiple)
✓ [NEW!] Umbral Mantle + any creature that taps for 3+ mana
✓ [NEW!] Freed from the Real + Karametra's Acolyte
```

### Tag Extraction Methods

#### Method A: Manual Tagging (High Quality, Slow)

```python
# Human experts tag cards
card_tags = {
    "Sol Ring": ["generates_mana", "taps_for_mana", "artifact"],
    "Hullbreaker Horror": ["untaps_permanents", "triggers_on_cast", "bounce"],
    "Blood Artist": ["triggers_on_death", "drains_life"],
    "Ashnod's Altar": ["sacrifices_creatures", "generates_mana"]
}
```

**Pros:** Accurate, reliable
**Cons:** Slow, doesn't scale, requires expertise

---

#### Method B: NLP Extraction from Oracle Text (Automated)

```python
def extract_tags(oracle_text: str) -> list:
    """Extract mechanic tags from oracle text using NLP"""

    tags = []
    text_lower = oracle_text.lower()

    # Pattern matching
    if re.search(r'untap (target|up to|any number)', text_lower):
        tags.append('untaps_permanents')

    if re.search(r'add.*{[cwubrg]+}', text_lower):
        tags.append('generates_mana')

    if re.search(r'whenever.*dies', text_lower):
        tags.append('triggers_on_death')

    if re.search(r'whenever.*enters the battlefield', text_lower):
        tags.append('triggers_on_etb')

    if re.search(r'sacrifice (a|an|target)', text_lower):
        tags.append('sacrifices_permanents')

    if re.search(r'draw (a card|cards)', text_lower):
        tags.append('draws_cards')

    # ... (100+ more patterns)

    return tags

# Apply to all cards
for card in cards:
    card['tags'] = extract_tags(card['oracle_text'])
```

**Example:**
```python
card = "Blood Artist"
oracle = "Whenever Blood Artist or another creature dies, target player loses 1 life and you gain 1 life."

tags = extract_tags(oracle)
# → ['triggers_on_death', 'drains_life', 'gains_life']
```

**Pros:** Scales to all cards, no manual work
**Cons:** Regex brittle, misses nuances

---

#### Method C: LLM-Based Tag Extraction (Best Quality)

```python
def extract_tags_llm(card_name: str, oracle_text: str) -> list:
    """Use LLM to extract semantic tags"""

    prompt = f"""
    Analyze this Magic card and extract functional tags.

    Card: {card_name}
    Text: {oracle_text}

    Available tags:
    - generates_mana, draws_cards, creates_tokens, searches_library
    - sacrifices_creatures, sacrifices_artifacts, discards_cards
    - untaps_permanents, blinks_creatures, bounces_permanents
    - triggers_on_etb, triggers_on_death, triggers_on_cast
    - alternate_win_con, drains_life, mills_library
    - reduces_costs, cost_reducer, copy_spell, extra_turn

    Return ONLY the applicable tags as a JSON array.
    """

    response = llm.generate(prompt)
    return json.loads(response)

# Example
tags = extract_tags_llm(
    "Ashnod's Altar",
    "Sacrifice a creature: Add {C}{C}."
)
# → ['sacrifices_creatures', 'generates_mana', 'mana_ability']
```

**Pros:** Understands context and nuance, high quality
**Cons:** Requires LLM API calls, slower than regex

---

### Pattern Database

```python
# Define combo patterns
COMBO_PATTERNS = [
    {
        "name": "Infinite Mana (Untap Loop)",
        "cards": [
            {"tags": ["untaps_permanents"], "quantity": 1},
            {"tags": ["generates_mana", "taps_for_mana"], "quantity": 1}
        ],
        "conditions": [
            "card2.mana_produced > card1.activation_cost"
        ],
        "produces": ["Infinite mana"]
    },
    {
        "name": "Infinite Tokens (Blink Loop)",
        "cards": [
            {"tags": ["creates_tokens", "triggers_on_etb"], "quantity": 1},
            {"tags": ["blinks_creatures"], "quantity": 1}
        ],
        "conditions": [
            "card2.can_blink_card1"
        ],
        "produces": ["Infinite creature tokens"]
    },
    {
        "name": "Infinite Life Drain (Aristocrats)",
        "cards": [
            {"tags": ["triggers_on_death", "drains_life"], "quantity": 1},
            {"tags": ["sacrifices_creatures"], "quantity": 1},
            {"tags": ["creates_tokens"], "quantity": 1}
        ],
        "produces": ["Infinite life drain", "Infinite death triggers"]
    },
    {
        "name": "Infinite Storm (Bounce Loop)",
        "cards": [
            {"tags": ["cost_0", "artifact"], "quantity": 1},
            {"tags": ["bounces_permanents", "triggers_on_cast"], "quantity": 1}
        ],
        "produces": ["Infinite storm count", "Infinite cast triggers"]
    },
    {
        "name": "Infinite Mill (Self-Mill + Win Con)",
        "cards": [
            {"tags": ["mills_self"], "quantity": 1},
            {"tags": ["wins_with_empty_library"], "quantity": 1}
        ],
        "produces": ["Win the game"]
    }
    # ... 50+ more patterns
]
```

### Discovery Algorithm

```python
def discover_combos(cards: list, patterns: list) -> list:
    """
    Find new combos by matching card tags to patterns
    """
    discovered_combos = []

    for pattern in patterns:
        # Find all card combinations matching this pattern
        matches = find_matching_combinations(cards, pattern)

        for match in matches:
            # Verify combo isn't already known
            if not combo_exists_in_database(match):
                # Validate combo logic
                if validate_combo(match, pattern['conditions']):
                    discovered_combos.append({
                        'cards': match,
                        'pattern': pattern['name'],
                        'produces': pattern['produces'],
                        'confidence': calculate_confidence(match, pattern)
                    })

    return discovered_combos

def find_matching_combinations(cards, pattern):
    """Find all card combinations matching pattern tags"""
    matching_cards = defaultdict(list)

    # Group cards by pattern requirements
    for i, requirement in enumerate(pattern['cards']):
        for card in cards:
            if all(tag in card['tags'] for tag in requirement['tags']):
                matching_cards[i].append(card)

    # Generate all combinations
    card_lists = [matching_cards[i] for i in range(len(pattern['cards']))]
    combinations = itertools.product(*card_lists)

    return combinations

def validate_combo(cards: list, conditions: list) -> bool:
    """
    Validate that combo actually works based on conditions
    """
    for condition in conditions:
        if not eval_condition(cards, condition):
            return False
    return True

def calculate_confidence(cards: list, pattern: dict) -> float:
    """
    Calculate confidence that this is a real combo
    Based on:
    - Tag match strength
    - Similar known combos
    - Community data (if cards appear together in decks)
    """

    confidence = 0.5  # Base confidence

    # Boost if cards have been seen together in decks
    if cards_seen_together_in_decks(cards):
        confidence += 0.2

    # Boost if similar to known combo
    similar_combo = find_most_similar_combo(cards)
    if similar_combo and similar_combo['verified']:
        confidence += 0.3

    return min(confidence, 1.0)
```

### Example Discovery

```python
# Run discovery
new_combos = discover_combos(all_cards, COMBO_PATTERNS)

# Results
[
    {
        'cards': ['Hullbreaker Horror', 'Mana Crypt'],
        'pattern': 'Infinite Mana (Untap Loop)',
        'produces': ['Infinite mana'],
        'confidence': 0.95  # High confidence, similar to known Sol Ring combo
    },
    {
        'cards': ['Pemmin\'s Aura', 'Karametra\'s Acolyte'],
        'pattern': 'Infinite Mana (Untap Loop)',
        'produces': ['Infinite green mana'],
        'confidence': 0.85  # Known pattern, less popular cards
    },
    {
        'cards': ['Enduring Renewal', 'Goblin Bombardment', 'Ornithopter'],
        'pattern': 'Infinite Damage (Loop)',
        'produces': ['Infinite damage'],
        'confidence': 0.70  # Complex interaction, needs verification
    }
]
```

---

## Approach 2: Embedding-Based Discovery

### The Idea

Use card embeddings to find **functionally similar** cards, then substitute into known combos.

### Algorithm: Combo Substitution

```python
def find_alternative_combos(known_combo: dict) -> list:
    """
    Given a known combo, find similar cards and test if they work
    """
    alternatives = []

    # For each card in the combo
    for i, card in enumerate(known_combo['cards']):
        # Find similar cards by embedding
        similar_cards = find_similar_cards(card, limit=20)

        for similar_card in similar_cards:
            # Create variant combo with substitution
            variant = known_combo.copy()
            variant['cards'][i] = similar_card

            # Validate if variant works
            if validate_combo_variant(variant, known_combo):
                alternatives.append({
                    'original_combo': known_combo,
                    'variant': variant,
                    'substitution': f"{card['name']} → {similar_card['name']}",
                    'similarity': similar_card['similarity']
                })

    return alternatives

def find_similar_cards(card: dict, limit: int = 20) -> list:
    """Find cards with similar oracle text / functionality"""

    query_emb = card['oracle_embedding']  # Use oracle-only embedding

    results = db.query("""
        SELECT
            id, name, oracle_text,
            1 - (oracle_embedding <=> %s::vector) AS similarity
        FROM cards
        WHERE id != %s  -- Exclude the card itself
        ORDER BY oracle_embedding <=> %s::vector
        LIMIT %s
    """, (query_emb, card['id'], query_emb, limit))

    return results

def validate_combo_variant(variant: dict, original: dict) -> bool:
    """
    Check if variant combo actually works
    Could use:
    - Rules engine simulation
    - Pattern matching on tags
    - LLM validation
    """

    # Quick check: Do tags still match the pattern?
    original_tags = get_combo_pattern_tags(original)
    variant_tags = get_combo_pattern_tags(variant)

    if not tags_compatible(original_tags, variant_tags):
        return False

    # Deeper check: Run rules simulation
    # (This requires a rules engine - Phase 6+)

    return True  # For now, assume compatible tags = working combo
```

### Example

```python
# Known combo
original = {
    'cards': ['Demonic Consultation', 'Thassa\'s Oracle'],
    'produces': ['Win the game']
}

# Find alternatives
alternatives = find_alternative_combos(original)

# Results
[
    {
        'variant': {
            'cards': ['Tainted Pact', 'Thassa\'s Oracle'],  # Similar to Demonic Consultation
            'produces': ['Win the game']
        },
        'substitution': 'Demonic Consultation → Tainted Pact',
        'similarity': 0.87
    },
    {
        'variant': {
            'cards': ['Demonic Consultation', 'Jace, Wielder of Mysteries'],  # Similar to Oracle
            'produces': ['Win the game']
        },
        'substitution': 'Thassa\'s Oracle → Jace, Wielder of Mysteries',
        'similarity': 0.82
    },
    {
        'variant': {
            'cards': ['Leveler', 'Thassa\'s Oracle'],  # Different exile method
            'produces': ['Win the game']
        },
        'substitution': 'Demonic Consultation → Leveler',
        'similarity': 0.65
    }
]
```

---

## Approach 3: Rules Engine Simulation

### The Idea

Actually **simulate the game state** to determine if cards combo.

### Implementation (High-Level)

```python
class ComboSimulator:
    def __init__(self, rules_engine):
        self.rules_engine = rules_engine

    def test_combo(self, cards: list, goal: str = "infinite") -> dict:
        """
        Simulate game with these cards to see if they combo

        Args:
            cards: List of card objects
            goal: What we're testing for ("infinite", "win", etc.)

        Returns:
            {
                'works': bool,
                'produces': list,  # What the combo achieves
                'steps': list,     # Sequence of actions
                'mana_needed': str
            }
        """

        # Set up game state
        game = self.rules_engine.create_game()
        game.add_cards_to_battlefield(cards)

        # Try to execute combo
        max_iterations = 1000
        iteration = 0
        state_history = []

        while iteration < max_iterations:
            # Record current state
            state = game.get_state()

            # Check for infinite loop (same state repeats)
            if state in state_history:
                return {
                    'works': True,
                    'produces': self.analyze_loop(state_history),
                    'steps': self.extract_steps(state_history),
                    'mana_needed': self.calculate_mana(state_history)
                }

            state_history.append(state)

            # Try to advance game state
            if not game.has_legal_actions():
                break

            # Use AI to choose best action (or heuristic)
            action = self.choose_action(game, goal)
            game.execute_action(action)

            iteration += 1

        # No infinite loop found
        return {
            'works': False,
            'reason': 'No infinite loop detected'
        }

    def choose_action(self, game, goal):
        """
        Choose next action to test for combo
        Could use:
        - Heuristics (always activate abilities if possible)
        - Search algorithm (A*, MCTS)
        - LLM to choose intelligent moves
        """

        # Simple heuristic: activate first available ability
        abilities = game.get_available_abilities()
        if abilities:
            return abilities[0]

        # Cast cheapest spell
        spells = game.get_castable_spells()
        if spells:
            return min(spells, key=lambda s: s.cmc)

        return None
```

**Pros:**
- Definitive answer (does it work or not?)
- Finds exact sequence of actions
- Calculates mana requirements

**Cons:**
- Requires full rules engine (complex!)
- Computationally expensive
- May miss clever sequences

**Status:** This is Phase 6+ work (you have a rules engine project started!)

---

## Approach 4: Graph Mining

### The Idea

Analyze the **combo graph** to find patterns and predict new edges.

### Graph Structure

```
Nodes = Cards
Edges = "Appears in combo together"

Example:
Sol Ring ─── Hullbreaker Horror
    │              │
    │              │
Mana Crypt ─── Peregrine Drake
    │
    │
Basalt Monolith ─── Rings of Brighthearth
```

### Mining Patterns

#### Pattern 1: Transitive Combos

```
If A combos with B, and B combos with C,
maybe A combos with C?
```

**Example:**
```
Thassa's Oracle ─── Demonic Consultation
                          │
                          │
                    Tainted Pact ─── Plunge into Darkness
```

**Inference:** Thassa's Oracle might combo with Plunge into Darkness?

**Validation:** Check if tags/mechanics match.

---

#### Pattern 2: Card Substitution

```
If card A appears in many combos with similar cards,
find other cards similar to those and test with A
```

**Example:**
```
Hullbreaker Horror combos with:
- Sol Ring (generates 2 mana, costs 1)
- Mana Crypt (generates 2 mana, costs 0)
- Mana Vault (generates 3 mana, costs 1)

Pattern: Small mana rocks that generate 2+ mana

Find similar: Grim Monolith, Mox Diamond, Chrome Mox
Test: Do these combo with Hullbreaker Horror?
```

---

#### Pattern 3: Feature-Based Expansion

```
If many combos with feature F contain cards with tags T,
find other card sets with tags T and test for feature F
```

**Example:**
```
Feature: "Infinite mana"
Common tags: [untaps_permanents, generates_mana]

Known combos:
- Pemmin's Aura + Bloom Tender
- Freed from the Real + Priest of Titania
- Umbral Mantle + Karametra's Acolyte

Pattern: (untap enchantment) + (creature that taps for 3+ mana)

Find new: Any creature that taps for 3+ mana we haven't tested
```

### Implementation

```python
import networkx as nx

def build_combo_graph(combos: list) -> nx.Graph:
    """Build graph where nodes=cards, edges=combo relationships"""

    G = nx.Graph()

    for combo in combos:
        cards = combo['cards']

        # Add all cards as nodes
        for card in cards:
            G.add_node(card['id'], name=card['name'], tags=card['tags'])

        # Add edges between all pairs in this combo
        for i, card1 in enumerate(cards):
            for card2 in cards[i+1:]:
                if G.has_edge(card1['id'], card2['id']):
                    # Increment weight if edge exists
                    G[card1['id']][card2['id']]['weight'] += 1
                    G[card1['id']][card2['id']]['combos'].append(combo['id'])
                else:
                    # Create new edge
                    G.add_edge(
                        card1['id'], card2['id'],
                        weight=1,
                        combos=[combo['id']]
                    )

    return G

def find_transitive_combos(G: nx.Graph, max_distance: int = 2) -> list:
    """Find potential new combos via graph traversal"""

    candidates = []

    for node in G.nodes():
        # Find all nodes within max_distance
        neighbors_at_2 = nx.single_source_shortest_path_length(G, node, cutoff=max_distance)

        for target, distance in neighbors_at_2.items():
            if distance == max_distance:  # Exactly 2 hops away
                # Check if direct edge exists
                if not G.has_edge(node, target):
                    # Potential new combo!
                    candidates.append({
                        'card1': G.nodes[node]['name'],
                        'card2': G.nodes[target]['name'],
                        'confidence': calculate_transitive_confidence(G, node, target)
                    })

    return candidates

def calculate_transitive_confidence(G, node1, node2):
    """
    Calculate how likely node1 and node2 combo
    Based on shared neighbors and path strengths
    """

    # Find common neighbors (cards that combo with both)
    neighbors1 = set(G.neighbors(node1))
    neighbors2 = set(G.neighbors(node2))
    common_neighbors = neighbors1 & neighbors2

    if not common_neighbors:
        return 0.1  # Low confidence

    # More common neighbors = higher confidence
    confidence = min(len(common_neighbors) / 5.0, 0.8)

    # Boost if tags are compatible
    tags1 = set(G.nodes[node1]['tags'])
    tags2 = set(G.nodes[node2]['tags'])

    if tags_form_combo_pattern(tags1, tags2):
        confidence += 0.2

    return min(confidence, 1.0)
```

---

## Approach 5: LLM-Based Prediction

### The Idea

Use your **fine-tuned Qwen model** to predict if cards work together.

### Training Data Enhancement

```python
# Generate training examples for combo prediction
training_examples = []

for combo in known_combos:
    cards = combo['cards']

    # Positive example (real combo)
    training_examples.append({
        "messages": [
            {"role": "system", "content": "You are an expert at identifying MTG combos."},
            {"role": "user", "content": f"Do {cards[0]} and {cards[1]} combo together?"},
            {"role": "assistant", "content": f"Yes! {combo['description']} This produces: {', '.join(combo['features'])}."}
        ]
    })

    # Negative example (non-combo)
    random_card = random.choice(all_cards)
    if random_card not in cards:
        training_examples.append({
            "messages": [
                {"role": "system", "content": "You are an expert at identifying MTG combos."},
                {"role": "user", "content": f"Do {cards[0]} and {random_card} combo together?"},
                {"role": "assistant", "content": "No, these cards do not combo together. They don't have synergistic effects."}
            ]
        })
```

### Inference

```python
def predict_combo_with_llm(card1: str, card2: str) -> dict:
    """Ask LLM if two cards combo"""

    prompt = f"Do {card1} and {card2} combo together? If yes, explain how."

    response = qwen_model.generate(prompt, max_tokens=200)

    # Parse response
    if response.lower().startswith('yes'):
        return {
            'works': True,
            'explanation': response,
            'confidence': 0.7  # LLM predictions are probabilistic
        }
    else:
        return {
            'works': False,
            'explanation': response,
            'confidence': 0.6
        }
```

**Pros:**
- Understands complex interactions
- Can explain reasoning
- Generalizes to new cards

**Cons:**
- Hallucination risk
- Needs validation
- Not deterministic

---

## Hybrid Approach (Recommended)

Combine multiple methods for best results:

```python
class ComboDiscoveryEngine:
    def __init__(self):
        self.tag_matcher = TagBasedMatcher()
        self.embedding_finder = EmbeddingBasedFinder()
        self.graph_miner = GraphMiner()
        self.llm_validator = LLMValidator()

    def discover_new_combos(self, confidence_threshold: float = 0.7) -> list:
        """
        Multi-stage combo discovery pipeline
        """

        candidates = []

        # Stage 1: Pattern matching (high precision, low recall)
        print("Stage 1: Tag-based pattern matching...")
        pattern_combos = self.tag_matcher.find_combos(COMBO_PATTERNS)
        candidates.extend(pattern_combos)

        # Stage 2: Embedding-based substitution (medium precision, medium recall)
        print("Stage 2: Finding similar card substitutions...")
        for known_combo in known_combos[:100]:  # Sample
            variants = self.embedding_finder.find_alternatives(known_combo)
            candidates.extend(variants)

        # Stage 3: Graph mining (low precision, high recall)
        print("Stage 3: Mining combo graph for patterns...")
        graph_combos = self.graph_miner.find_transitive_combos()
        candidates.extend(graph_combos)

        # Stage 4: LLM validation (filter false positives)
        print("Stage 4: Validating with LLM...")
        validated_combos = []

        for candidate in candidates:
            if candidate['confidence'] < confidence_threshold:
                # Use LLM to validate uncertain combos
                llm_result = self.llm_validator.validate(candidate)
                candidate['confidence'] = llm_result['confidence']
                candidate['llm_explanation'] = llm_result['explanation']

            if candidate['confidence'] >= confidence_threshold:
                validated_combos.append(candidate)

        # Stage 5: Deduplicate and rank
        print("Stage 5: Deduplicating and ranking...")
        final_combos = self.deduplicate(validated_combos)
        final_combos.sort(key=lambda x: x['confidence'], reverse=True)

        return final_combos

    def deduplicate(self, combos: list) -> list:
        """Remove duplicate combo discoveries"""
        seen = set()
        unique = []

        for combo in combos:
            # Create signature from card IDs
            sig = tuple(sorted(card['id'] for card in combo['cards']))

            if sig not in seen:
                seen.add(sig)
                unique.append(combo)

        return unique
```

### Expected Results

```python
engine = ComboDiscoveryEngine()
new_combos = engine.discover_new_combos(confidence_threshold=0.75)

# Sample output
[
    {
        'cards': ['Umbral Mantle', 'Karametra\'s Acolyte'],
        'produces': ['Infinite green mana'],
        'confidence': 0.92,
        'discovery_method': 'pattern_matching',
        'pattern': 'Infinite Mana (Untap Loop)',
        'verified': False  # Needs community verification
    },
    {
        'cards': ['Hullbreaker Horror', 'Mana Crypt'],
        'produces': ['Infinite colorless mana', 'Infinite storm'],
        'confidence': 0.88,
        'discovery_method': 'substitution',
        'original_combo': 'Sol Ring + Hullbreaker Horror',
        'substitution': 'Sol Ring → Mana Crypt',
        'verified': False
    },
    {
        'cards': ['Sensei\'s Divining Top', 'Bolas\'s Citadel', 'Aetherflux Reservoir'],
        'produces': ['Infinite life', 'Infinite storm', 'Infinite damage'],
        'confidence': 0.85,
        'discovery_method': 'graph_mining',
        'verified': False
    }
    # ... hundreds more
]
```

---

## Implementation Strategy

### Phase 1: Card Tagging (Foundation)

**Goal:** Tag all 508K cards with functional categories

**Approach:**
1. Define tag taxonomy (100-200 tags)
2. Extract tags using NLP + LLM (hybrid)
3. Store in `card_tags` table
4. Create indexes for fast lookup

**Timeline:** 2-3 weeks

**Output:** All cards tagged with mechanics

---

### Phase 2: Pattern Database (Quick Wins)

**Goal:** Define 50-100 common combo patterns

**Approach:**
1. Analyze known combos to extract patterns
2. Document pattern structures
3. Implement pattern matching algorithm
4. Test on known combos (should find most of them)

**Timeline:** 1-2 weeks

**Output:** Pattern-based combo discovery working

---

### Phase 3: Discovery Pipeline (Integration)

**Goal:** Combine all approaches into unified system

**Approach:**
1. Implement tag-based matching
2. Add embedding-based substitution
3. Add graph mining
4. Add LLM validation
5. Create confidence scoring system

**Timeline:** 3-4 weeks

**Output:** End-to-end discovery pipeline

---

### Phase 4: Validation & Community (Critical!)

**Goal:** Verify discovered combos are real

**Approach:**
1. Manual review of high-confidence discoveries
2. Community voting system (submit discoveries)
3. Integrate with rules engine for simulation
4. Track accuracy metrics

**Timeline:** Ongoing

**Output:** Verified new combos added to database

---

## Open Questions

1. **How to validate discoveries?**
   - Manual review? (slow but accurate)
   - Rules engine simulation? (fast but requires implementation)
   - Community voting? (scales but needs user base)
   - LLM validation? (fast but may hallucinate)

2. **What confidence threshold?**
   - 90%+ = Very conservative, few discoveries
   - 70%+ = Balanced, some false positives
   - 50%+ = Aggressive, many false positives

3. **How to handle multi-card combos (4+ cards)?**
   - Exponential search space
   - May need heuristics or sampling

4. **How to update as new cards release?**
   - Automated tagging of new cards
   - Periodic discovery runs
   - Community submissions

5. **Legal/ethical considerations?**
   - Commander Spellbook data is community-contributed
   - Should we contribute discoveries back?
   - How to attribute AI-discovered combos?

---

## Success Metrics

**Quantitative:**
- Number of new combos discovered: 1,000+ target
- Precision (% of discoveries that actually work): 70%+ target
- Recall (% of real combos we find): Hard to measure
- Discovery per compute hour: Optimize over time

**Qualitative:**
- Community reception (do players find them useful?)
- Novelty (are these truly unknown or just obscure?)
- Practicality (are they playable or just jank?)

---

## Conclusion

**YES, we can discover new synergies!**

**Best Approach:**
1. **Tag all cards** with functional mechanics (NLP + LLM)
2. **Define patterns** for common combo types
3. **Pattern match** to find candidates (high precision)
4. **Substitute similar cards** into known combos (medium precision)
5. **Mine the graph** for transitive combos (high recall)
6. **Validate with LLM** to filter false positives
7. **Verify with community** or rules engine

**Estimated Potential:**
- 36K known combos
- 100K+ potential discoverable combos
- Realistic discovery target: 5-10K new combos with 70%+ accuracy

This would be a **groundbreaking feature** - an AI that discovers Magic combos!

