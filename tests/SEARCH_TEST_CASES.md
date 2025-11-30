# Search Test Cases

These test cases provide consistent queries you can use during development to verify search functionality works as expected.

## Keyword Search Test Cases

### Test Case 1: Exact Card Name
**Query:** `Lightning Bolt`
- **Expected:** "Lightning Bolt" as top result
- **Why:** Tests exact name matching priority
- **Validation:** Top result should be "Lightning Bolt"

### Test Case 2: Common Keyword
**Query:** `flying`
- **Expected:** 10+ results, all containing "flying" in name or text
- **Why:** Tests partial text matching
- **Validation:** Every result should contain "flying" (case-insensitive)

### Test Case 3: Card Draw
**Query:** `draw a card`
- **Expected:** 10+ results with card draw effects
- **Why:** Tests multi-word phrase matching
- **Validation:** Results should contain "draw" in oracle text

### Test Case 4: Removal Phrase
**Query:** `destroy target creature`
- **Expected:** 10+ creature removal spells
- **Why:** Tests common game mechanic text
- **Validation:** Results should contain "destroy" and "target" and "creature"

---

## Semantic Search Test Cases

### Test Case 1: Red Burn Spells
**Query:** `red spells that deal damage`
- **Expected Top Results:**
  - Lightning Bolt
  - Shock
  - Lava Spike
  - Bolt
- **Why:** Tests semantic understanding of "burn" archetype
- **Similarity Threshold:** >0.3
- **Validation:** Top 10 should include at least 2-3 red damage instants/sorceries

### Test Case 2: Creature Removal
**Query:** `cards that remove creatures`
- **Expected Top Results:**
  - Murder
  - Doom Blade
  - Go for the Throat
  - Path to Exile
  - Swords to Plowshares
- **Why:** Tests semantic understanding without using exact MTG terminology
- **Similarity Threshold:** >0.35
- **Validation:** Top 10 should include creature removal spells (destroy/exile/damage)

### Test Case 3: Flying Creatures
**Query:** `creatures with flying`
- **Expected:** Creature cards with flying keyword
- **Why:** Tests natural language to keyword mapping
- **Similarity Threshold:** >0.4
- **Validation:** Results should be creatures with "Flying" in keywords or oracle text

### Test Case 4: Counterspells
**Query:** `counterspells`
- **Expected Top Results:**
  - Counterspell
  - Cancel
  - Negate
  - Mana Leak
- **Why:** Tests archetype recognition
- **Similarity Threshold:** >0.35
- **Validation:** Top 10 should be blue instants that counter spells

### Test Case 5: Mana Ramp
**Query:** `cards that search for lands`
- **Expected Top Results:**
  - Rampant Growth
  - Cultivate
  - Kodama's Reach
  - Explosive Vegetation
- **Why:** Tests indirect archetype description (ramp without saying "ramp")
- **Similarity Threshold:** >0.3
- **Validation:** Results should put lands onto battlefield or into hand

### Test Case 6: Card Advantage
**Query:** `draw multiple cards`
- **Expected Top Results:**
  - Divination
  - Concentrate
  - Harmonize
  - Jace's Ingenuity
- **Why:** Tests quantitative semantic understanding
- **Similarity Threshold:** >0.35
- **Validation:** Results should draw 2+ cards

---

## Baseline Results (For Regression Testing)

Run these commands to establish baseline results:

```bash
# Keyword search baselines
python tests/test_search_fixtures.py --query "Lightning Bolt" --type keyword
python tests/test_search_fixtures.py --query "flying" --type keyword
python tests/test_search_fixtures.py --query "destroy target creature" --type keyword

# Semantic search baselines
python tests/test_search_fixtures.py --query "red spells that deal damage" --type semantic
python tests/test_search_fixtures.py --query "cards that remove creatures" --type semantic
python tests/test_search_fixtures.py --query "creatures with flying" --type semantic
python tests/test_search_fixtures.py --query "counterspells" --type semantic
python tests/test_search_fixtures.py --query "cards that search for lands" --type semantic
```

---

## API Testing with curl

### Keyword Search
```bash
curl "http://localhost:8000/api/cards/keyword?query=Lightning%20Bolt&limit=5" | jq
curl "http://localhost:8000/api/cards/keyword?query=flying&limit=10" | jq
```

### Semantic Search
```bash
curl "http://localhost:8000/api/cards/semantic?query=red%20spells%20that%20deal%20damage&limit=10" | jq
curl "http://localhost:8000/api/cards/semantic?query=counterspells&limit=10" | jq
```

---

## Expected Similarity Score Ranges

Based on testing with `all-MiniLM-L6-v2`:

- **0.5+** : Excellent match (nearly exact semantic meaning)
- **0.4-0.5** : Very good match (clearly related concepts)
- **0.3-0.4** : Good match (semantically similar)
- **0.2-0.3** : Moderate match (loosely related)
- **<0.2** : Poor match (likely not relevant)

For development, results with similarity >0.3 are generally useful.

---

## Gotchas

1. **Multiple Printings:** Cards like "Lightning Bolt" have 10+ printings. Search returns all printings.
2. **Similarity Scores:** Scores vary based on query phrasing. "red damage spell" ≠ "burn spell" semantically.
3. **Model Limitations:** The model doesn't know MTG slang (e.g., "removal" vs "cards that kill creatures").
4. **Embeddings Quality:** Results depend on the oracle text quality and how well the model understood it during embedding generation.

---

## Adding New Test Cases

When adding test cases:
1. Test the query manually first
2. Document the top 3-5 results
3. Note the similarity threshold
4. Explain what semantic concept you're testing
5. Add to this file for future regression testing
