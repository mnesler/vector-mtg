# Schema Walkthrough: Real Card Examples

**Purpose:** Show exactly what data looks like before deployment

---

## Example Cards

We'll walk through 5 different card types to show how the system handles various mechanics:

1. **Pemmin's Aura** - Untapper (combo enabler)
2. **Sol Ring** - Mana rock (resource generation)
3. **Blood Artist** - Death trigger (aristocrats)
4. **Ashnod's Altar** - Sacrifice outlet (combo piece)
5. **Thassa's Oracle** - Win condition

---

## Example 1: Pemmin's Aura

### Card Data
```
Name: Pemmin's Aura
Mana Cost: {1}{U}{U}
Type: Enchantment — Aura
Oracle Text:
  Enchant creature
  {U}: Untap enchanted creature.
  {U}: Enchanted creature gains flying until end of turn.
  {U}: Enchanted creature gains shroud until end of turn.
  {1}: Enchanted creature gets +1/-1 or -1/+1 until end of turn.
```

### LLM Extraction (What we'd get)

**Tags Extracted:**
```json
[
  {
    "tag": "untaps_permanents",
    "confidence": 0.98,
    "reason": "Has activated ability '{U}: Untap enchanted creature'"
  },
  {
    "tag": "grants_abilities",
    "confidence": 0.95,
    "reason": "Grants flying and shroud abilities"
  },
  {
    "tag": "aura",
    "confidence": 1.0,
    "reason": "Type line contains 'Aura'"
  },
  {
    "tag": "enchantment",
    "confidence": 1.0,
    "reason": "Type line contains 'Enchantment'"
  },
  {
    "tag": "grants_flying",
    "confidence": 0.92,
    "reason": "Grants flying ability"
  },
  {
    "tag": "grants_shroud",
    "confidence": 0.92,
    "reason": "Grants shroud ability"
  },
  {
    "tag": "infinite_enabler",
    "confidence": 0.85,
    "reason": "Untap ability commonly used in infinite combos"
  }
]
```

**Abstractions Extracted:**
```json
[
  {
    "abstraction_type": "activated_ability",
    "pattern": {
      "type": "activated_ability",
      "cost": {
        "mana": "{U}",
        "tap": false,
        "other": []
      },
      "effect": {
        "action": "untap",
        "target": "creature",
        "scope": "enchanted",
        "amount": 1
      },
      "repeatable": true,
      "speed": "instant"
    },
    "abstraction_text": "Pay {U}: Untap enchanted creature",
    "confidence": 0.98
  },
  {
    "abstraction_type": "activated_ability",
    "pattern": {
      "type": "activated_ability",
      "cost": {"mana": "{U}"},
      "effect": {
        "action": "grant_keyword",
        "target": "creature",
        "scope": "enchanted",
        "keyword": "flying",
        "duration": "until_eot"
      },
      "repeatable": true
    },
    "abstraction_text": "Pay {U}: Enchanted creature gains flying until end of turn",
    "confidence": 0.95
  }
]
```

### Database Records Created

**card_tags table:**
```sql
card_id                              | tag_id | tag_name           | confidence | source | needs_review
-------------------------------------|--------|--------------------|-----------:|--------|-------------
abc-123-pemmin                       | 15     | untaps_permanents  | 0.98       | llm    | false
abc-123-pemmin                       | 28     | grants_abilities   | 0.95       | llm    | false
abc-123-pemmin                       | 67     | aura               | 1.00       | llm    | false
abc-123-pemmin                       | 65     | enchantment        | 1.00       | llm    | false
abc-123-pemmin                       | 82     | infinite_enabler   | 0.85       | llm    | false
```

**cards table (updated columns):**
```sql
id: abc-123-pemmin
name: "Pemmin's Aura"
tag_cache: ['untaps_permanents', 'grants_abilities', 'aura', 'enchantment', 'infinite_enabler']
tag_confidence_avg: 0.94
needs_tag_review: false  -- High confidence, no review needed
```

**card_abstractions table:**
```sql
id  | card_id        | abstraction_type    | abstraction_text                           | confidence
----|----------------|---------------------|--------------------------------------------|-----------
1   | abc-123-pemmin | activated_ability   | Pay {U}: Untap enchanted creature          | 0.98
2   | abc-123-pemmin | activated_ability   | Pay {U}: Grant flying until EOT            | 0.95
```

**Review Queue:**
```
(No entry - confidence too high)
```

---

## Example 2: Sol Ring

### Card Data
```
Name: Sol Ring
Mana Cost: {1}
Type: Artifact
Oracle Text:
  {T}: Add {C}{C}.
```

### LLM Extraction

**Tags Extracted:**
```json
[
  {
    "tag": "generates_mana",
    "confidence": 1.0,
    "reason": "Produces mana: Add {C}{C}"
  },
  {
    "tag": "generates_colorless_mana",
    "confidence": 1.0,
    "reason": "Specifically generates colorless mana"
  },
  {
    "tag": "artifact",
    "confidence": 1.0,
    "reason": "Type line is 'Artifact'"
  },
  {
    "tag": "taps_permanents",
    "confidence": 0.95,
    "reason": "Has tap symbol in activation cost"
  },
  {
    "tag": "infinite_enabler",
    "confidence": 0.88,
    "reason": "Commonly used in infinite mana combos"
  }
]
```

**Abstractions Extracted:**
```json
[
  {
    "abstraction_type": "activated_ability",
    "pattern": {
      "type": "mana_ability",
      "cost": {
        "tap": true
      },
      "effect": {
        "action": "add_mana",
        "mana_type": "colorless",
        "amount": 2
      },
      "repeatable": false,
      "speed": "mana_ability"
    },
    "abstraction_text": "Tap: Add {C}{C}",
    "confidence": 1.0
  }
]
```

### Database Records Created

**card_tags table:**
```sql
card_id      | tag_id | tag_name                  | confidence | source | needs_review
-------------|--------|---------------------------|-----------:|--------|-------------
def-456-sol  | 1      | generates_mana            | 1.00       | llm    | false
def-456-sol  | 7      | generates_colorless_mana  | 1.00       | llm    | false
def-456-sol  | 64     | artifact                  | 1.00       | llm    | false
def-456-sol  | 82     | infinite_enabler          | 0.88       | llm    | false
```

**cards table:**
```sql
name: "Sol Ring"
tag_cache: ['generates_mana', 'generates_colorless_mana', 'artifact', 'infinite_enabler']
tag_confidence_avg: 0.97
needs_tag_review: false
```

**Review Queue:**
```
(No entry)
```

---

## Example 3: Blood Artist

### Card Data
```
Name: Blood Artist
Mana Cost: {1}{B}
Type: Creature — Vampire
Oracle Text:
  Whenever Blood Artist or another creature dies, target player loses 1 life and you gain 1 life.
Power/Toughness: 0/1
```

### LLM Extraction

**Tags Extracted:**
```json
[
  {
    "tag": "triggers_on_death",
    "confidence": 1.0,
    "reason": "Triggers whenever a creature dies"
  },
  {
    "tag": "drains_life",
    "confidence": 1.0,
    "reason": "Target player loses life"
  },
  {
    "tag": "gains_life",
    "confidence": 1.0,
    "reason": "You gain life"
  },
  {
    "tag": "creature",
    "confidence": 1.0,
    "reason": "Type line contains 'Creature'"
  },
  {
    "tag": "loop_component",
    "confidence": 0.90,
    "reason": "Death trigger commonly used in aristocrats loops"
  }
]
```

**Abstractions Extracted:**
```json
[
  {
    "abstraction_type": "triggered_ability",
    "pattern": {
      "type": "triggered_ability",
      "trigger": {
        "event": "dies",
        "source": ["creature"],
        "scope": "any",
        "includes_self": true
      },
      "effect": {
        "actions": [
          {
            "action": "lose_life",
            "target": "player",
            "targeting": "target_player",
            "amount": 1
          },
          {
            "action": "gain_life",
            "target": "controller",
            "amount": 1
          }
        ]
      }
    },
    "abstraction_text": "Whenever a creature dies: Target player loses 1 life, you gain 1 life",
    "confidence": 1.0
  }
]
```

### Database Records Created

**card_tags table:**
```sql
card_id          | tag_id | tag_name           | confidence | source | needs_review
-----------------|--------|--------------------|-----------:|--------|-------------
ghi-789-blood    | 34     | triggers_on_death  | 1.00       | llm    | false
ghi-789-blood    | 41     | drains_life        | 1.00       | llm    | false
ghi-789-blood    | 42     | gains_life         | 1.00       | llm    | false
ghi-789-blood    | 63     | creature           | 1.00       | llm    | false
ghi-789-blood    | 84     | loop_component     | 0.90       | llm    | false
```

**cards table:**
```sql
name: "Blood Artist"
tag_cache: ['triggers_on_death', 'drains_life', 'gains_life', 'creature', 'loop_component']
tag_confidence_avg: 0.98
needs_tag_review: false
```

---

## Example 4: Ashnod's Altar

### Card Data
```
Name: Ashnod's Altar
Mana Cost: {3}
Type: Artifact
Oracle Text:
  Sacrifice a creature: Add {C}{C}.
```

### LLM Extraction

**Tags Extracted:**
```json
[
  {
    "tag": "sacrifices_creatures",
    "confidence": 1.0,
    "reason": "Activation cost requires sacrificing a creature"
  },
  {
    "tag": "generates_mana",
    "confidence": 1.0,
    "reason": "Effect adds mana"
  },
  {
    "tag": "generates_colorless_mana",
    "confidence": 1.0,
    "reason": "Adds {C}{C}"
  },
  {
    "tag": "artifact",
    "confidence": 1.0,
    "reason": "Type line is 'Artifact'"
  },
  {
    "tag": "infinite_enabler",
    "confidence": 0.95,
    "reason": "Commonly used in infinite sacrifice loops"
  },
  {
    "tag": "loop_component",
    "confidence": 0.92,
    "reason": "Key component in aristocrats combos"
  }
]
```

**Abstractions Extracted:**
```json
[
  {
    "abstraction_type": "activated_ability",
    "pattern": {
      "type": "mana_ability",
      "cost": {
        "sacrifice": ["creature"]
      },
      "effect": {
        "action": "add_mana",
        "mana_type": "colorless",
        "amount": 2
      },
      "repeatable": true,
      "speed": "mana_ability"
    },
    "abstraction_text": "Sacrifice a creature: Add {C}{C}",
    "confidence": 1.0
  }
]
```

### Database Records Created

**card_tags table:**
```sql
card_id          | tag_id | tag_name                  | confidence | source
-----------------|--------|---------------------------|-----------:|--------
jkl-012-ashnod   | 8      | sacrifices_creatures      | 1.00       | llm
jkl-012-ashnod   | 1      | generates_mana            | 1.00       | llm
jkl-012-ashnod   | 7      | generates_colorless_mana  | 1.00       | llm
jkl-012-ashnod   | 64     | artifact                  | 1.00       | llm
jkl-012-ashnod   | 82     | infinite_enabler          | 0.95       | llm
jkl-012-ashnod   | 84     | loop_component            | 0.92       | llm
```

**cards table:**
```sql
name: "Ashnod's Altar"
tag_cache: ['sacrifices_creatures', 'generates_mana', 'generates_colorless_mana', 'artifact', 'infinite_enabler', 'loop_component']
tag_confidence_avg: 0.98
needs_tag_review: false
```

---

## Example 5: Thassa's Oracle (Low Confidence Example)

### Card Data
```
Name: Thassa's Oracle
Mana Cost: {U}{U}
Type: Creature — Merfolk Wizard
Oracle Text:
  When Thassa's Oracle enters the battlefield, look at the top X cards of your library, where X is your devotion to blue. Put up to one of them on top of your library and the rest on the bottom of your library in a random order. If X is greater than or equal to the number of cards in your library, you win the game.
Power/Toughness: 1/3
```

### LLM Extraction (Complex Card!)

**Tags Extracted:**
```json
[
  {
    "tag": "triggers_on_etb",
    "confidence": 1.0,
    "reason": "Has 'When ... enters the battlefield' trigger"
  },
  {
    "tag": "wins_with_empty_library",
    "confidence": 0.95,
    "reason": "Wins if X >= cards in library (implies empty library win)"
  },
  {
    "tag": "alternate_win_con",
    "confidence": 0.90,
    "reason": "Can win the game through non-damage means"
  },
  {
    "tag": "creature",
    "confidence": 1.0,
    "reason": "Type line contains 'Creature'"
  },
  {
    "tag": "draws_cards",
    "confidence": 0.60,  // LOW CONFIDENCE - Oracle doesn't draw, it looks!
    "reason": "UNCERTAIN: Card mentions looking at cards, may be similar to drawing"
  },
  {
    "tag": "searches_library",
    "confidence": 0.55,  // LOW CONFIDENCE - Doesn't search!
    "reason": "UNCERTAIN: Looks at top X cards, similar to searching"
  }
]
```

**After Filtering (confidence >= 0.7):**
```json
[
  {"tag": "triggers_on_etb", "confidence": 1.0},
  {"tag": "wins_with_empty_library", "confidence": 0.95},
  {"tag": "alternate_win_con", "confidence": 0.90},
  {"tag": "creature", "confidence": 1.0}
]
// draws_cards and searches_library FILTERED OUT (< 0.7)
```

**Abstractions Extracted:**
```json
[
  {
    "abstraction_type": "etb_effect",
    "pattern": {
      "type": "triggered_ability",
      "trigger": {
        "event": "enters_battlefield",
        "source": "self"
      },
      "effect": {
        "action": "conditional_win",
        "condition": "devotion_comparison",
        "win_condition": "library_size_check"
      }
    },
    "abstraction_text": "ETB: Win if devotion to blue >= library size",
    "confidence": 0.85
  }
]
```

### Database Records Created

**card_tags table:**
```sql
card_id          | tag_id | tag_name                 | confidence | source | needs_review
-----------------|--------|--------------------------|------------|--------|-------------
mno-345-thassa   | 30     | triggers_on_etb          | 1.00       | llm    | false
mno-345-thassa   | 52     | wins_with_empty_library  | 0.95       | llm    | false
mno-345-thassa   | 50     | alternate_win_con        | 0.90       | llm    | false
mno-345-thassa   | 63     | creature                 | 1.00       | llm    | false
```

**cards table:**
```sql
name: "Thassa's Oracle"
tag_cache: ['triggers_on_etb', 'wins_with_empty_library', 'alternate_win_con', 'creature']
tag_confidence_avg: 0.96
needs_tag_review: false  -- Still above threshold!
```

**Review Queue:**
```
(No entry - avg confidence is 0.96, above 0.7 threshold)
```

**Note:** The low-confidence tags (draws_cards: 0.60, searches_library: 0.55) were filtered out automatically!

---

## Example 6: Edge Case - Ambiguous Card

Let's say we have a complex card where LLM struggles:

### Card Data
```
Name: Obscure Jank Card
Oracle Text: (Some complex, unusual interaction)
```

### LLM Extraction (Struggling)
```json
[
  {
    "tag": "some_tag",
    "confidence": 0.65,
    "reason": "Maybe does this?"
  },
  {
    "tag": "another_tag",
    "confidence": 0.55,
    "reason": "Unclear if this applies"
  }
]
```

### Database Records Created

**card_tags table:**
```sql
card_id          | tag_id | tag_name    | confidence | source | needs_review
-----------------|--------|-------------|-----------:|--------|-------------
pqr-678-obscure  | 15     | some_tag    | 0.65       | llm    | true
pqr-678-obscure  | 22     | another_tag | 0.55       | llm    | true
```

**cards table:**
```sql
name: "Obscure Jank Card"
tag_cache: []  -- Empty! No tags meet 0.7 threshold
tag_confidence_avg: 0.60
needs_tag_review: true  -- FLAGGED!
```

**tagging_review_queue:**
```sql
id | card_id         | reason           | details                      | priority | status
---|-----------------|------------------|------------------------------|----------|--------
1  | pqr-678-obscure | low_confidence   | {"avg_confidence": 0.60}     | 5        | pending
```

**This card goes into manual review!**

---

## Querying Examples

### Query 1: Get All Tags for Pemmin's Aura

```sql
SELECT * FROM cards_with_quality_tags
WHERE name = 'Pemmin''s Aura';
```

**Result:**
```json
{
  "id": "abc-123-pemmin",
  "name": "Pemmin's Aura",
  "oracle_text": "Enchant creature\n{U}: Untap enchanted creature...",
  "tag_cache": ["untaps_permanents", "grants_abilities", "aura", "enchantment", "infinite_enabler"],
  "tag_confidence_avg": 0.94,
  "needs_tag_review": false,
  "tags_detail": [
    {"tag": "untaps_permanents", "category": "state_change", "confidence": 0.98},
    {"tag": "grants_abilities", "category": "state_change", "confidence": 0.95},
    {"tag": "aura", "category": "card_types", "confidence": 1.0},
    {"tag": "enchantment", "category": "card_types", "confidence": 1.0},
    {"tag": "infinite_enabler", "category": "combo_enablers", "confidence": 0.85}
  ]
}
```

### Query 2: Find All Cards That Untap Permanents

```sql
SELECT * FROM get_cards_by_tag('untaps_permanents', 0.7, false)
LIMIT 5;
```

**Result:**
```
card_id          | card_name           | tag_name           | confidence
-----------------|---------------------|--------------------|-----------
abc-123-pemmin   | Pemmin's Aura       | untaps_permanents  | 0.98
stu-901-freed    | Freed from the Real | untaps_permanents  | 0.97
vwx-234-aphetto  | Aphetto Alchemist   | untaps_permanents  | 0.95
yza-567-umbral   | Umbral Mantle       | untaps_permanents  | 0.92
```

### Query 3: Find Cards for Infinite Mana Combos

```sql
-- Find cards that both untap AND generate mana (combo potential!)
SELECT c.name, c.tag_cache
FROM cards c
WHERE c.tag_cache && ARRAY['untaps_permanents', 'generates_mana']::TEXT[]
  AND c.tag_confidence_avg >= 0.7
LIMIT 10;
```

**Result:**
```
name                | tag_cache
--------------------|--------------------------------------------------
Pemmin's Aura       | [untaps_permanents, grants_abilities, ...]
Freed from the Real | [untaps_permanents, ...]
```

Wait, these don't generate mana themselves! Let's find the combo:

```sql
-- Find untappers
SELECT id, name FROM cards WHERE 'untaps_permanents' = ANY(tag_cache);

-- Find mana generators
SELECT id, name FROM cards WHERE 'generates_mana' = ANY(tag_cache);

-- Combo: Untapper + Mana generator that taps for more than untap costs
-- This is pattern matching (Phase 6!)
```

### Query 4: Review Queue

```sql
SELECT
    c.name,
    c.oracle_text,
    rq.reason,
    rq.priority,
    c.tag_confidence_avg
FROM tagging_review_queue rq
JOIN cards c ON rq.card_id = c.id
WHERE rq.status = 'pending'
ORDER BY rq.priority DESC, rq.created_at
LIMIT 20;
```

**Result:**
```
name                | reason         | priority | tag_confidence_avg
--------------------|----------------|----------|-------------------
Obscure Jank Card   | low_confidence | 5        | 0.60
Complex Interaction | low_confidence | 5        | 0.65
Weird Card Text     | no_tags        | 10       | NULL
```

### Query 5: Tag Usage Statistics

```sql
SELECT * FROM tag_usage_stats
ORDER BY card_count DESC
LIMIT 10;
```

**Result:**
```
name                  | category            | card_count | avg_confidence | low_confidence_count
----------------------|---------------------|------------|----------------|---------------------
creature              | card_types          | 25,432     | 0.99           | 12
artifact              | card_types          | 18,901     | 0.98           | 8
generates_mana        | resource_generation | 12,456     | 0.92           | 234
triggers_on_etb       | triggers            | 8,234      | 0.88           | 412
draws_cards           | resource_generation | 7,123      | 0.85           | 567
```

### Query 6: Get Tag Hierarchy for a Card

```sql
SELECT * FROM get_card_tags_with_hierarchy('def-456-sol');
```

**Result:**
```
tag_id | tag_name                  | depth | confidence
-------|---------------------------|-------|------------
1      | generates_mana            | 0     | 1.00
7      | generates_colorless_mana  | 1     | 1.00
64     | artifact                  | 0     | 1.00
82     | infinite_enabler          | 0     | 0.88
```

Note: `generates_colorless_mana` (depth 1) is a child of `generates_mana` (depth 0)

---

## Review Queue Workflow

### Step 1: Card Gets Low Confidence

```
LLM extracts tags → Avg confidence 0.60 → Auto-added to review queue
```

### Step 2: Manual Review

```sql
-- Get next card to review
SELECT
    c.id,
    c.name,
    c.oracle_text,
    c.tag_cache,
    c.tag_confidence_avg,
    (
        SELECT json_agg(json_build_object('tag', t.name, 'confidence', ct.confidence))
        FROM card_tags ct
        JOIN tags t ON ct.tag_id = t.id
        WHERE ct.card_id = c.id
    ) as current_tags
FROM tagging_review_queue rq
JOIN cards c ON rq.card_id = c.id
WHERE rq.status = 'pending'
ORDER BY rq.priority DESC
LIMIT 1;
```

### Step 3: Human Reviews & Fixes

```sql
-- Add correct tags manually
INSERT INTO card_tags (card_id, tag_id, confidence, source)
VALUES
  ('pqr-678-obscure', (SELECT id FROM tags WHERE name = 'correct_tag'), 1.0, 'manual');

-- Remove incorrect tags
DELETE FROM card_tags
WHERE card_id = 'pqr-678-obscure'
  AND tag_id = (SELECT id FROM tags WHERE name = 'wrong_tag');

-- Mark as reviewed
UPDATE tagging_review_queue
SET
    status = 'completed',
    resolved_at = NOW(),
    resolved_by = 'username',
    resolution_notes = 'Fixed incorrect tag extraction'
WHERE card_id = 'pqr-678-obscure';
```

### Step 4: Trigger Auto-Updates

```
card_tags change → Trigger fires → Updates tag_cache → Recalculates confidence
→ If still low, stays in queue
→ If fixed, removed from queue
```

---

## What Do You Want to Adjust?

Now that you've seen real examples, what would you like to change?

### Common Adjustments:

**1. Confidence Thresholds:**
```sql
-- Current: 0.7
-- Too strict? Lower to 0.6?
-- Too lenient? Raise to 0.8?
```

**2. Add/Remove Tags:**
```sql
-- Want to add specific tags for your use case?
-- Example: 'clones_permanents', 'phases_out', 'mdfc', etc.
```

**3. Tag Hierarchy:**
```sql
-- Want more granular color-specific tags?
-- Example: generates_mana
--            ├─ generates_any_color (new!)
--            ├─ generates_white_mana
--            └─ generates_treasure (new!)
```

**4. Review Queue Priorities:**
```sql
-- Change priority levels?
-- Current: < 0.5 = 10, < 0.6 = 5, < 0.7 = 1
```

**5. Tag Categories:**
```sql
-- Add new categories?
-- Example: 'card_draw_engines', 'ramp_spells', 'board_wipes'
```

**6. Abstraction Structure:**
```jsonb
-- Want different pattern format?
-- More/fewer fields?
-- Different action types?
```

Tell me what you'd like to adjust and I'll update the schema!
