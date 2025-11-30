# Search Testing Guide

This document provides test queries and expected results for validating search functionality during development.

## Quick Test Commands

### Run Full Test Suite
```bash
./tests/run_search_tests.sh
```

### Test Individual Queries
```bash
# Keyword search
python tests/test_search_fixtures.py --query "Lightning Bolt" --type keyword

# Semantic search
python tests/test_search_fixtures.py --query "counterspells" --type semantic
```

### Test via API (requires server running)
```bash
# Start the API server in another terminal
cd scripts/api && python -m api.api_server_rules

# Keyword search
curl "http://localhost:8000/api/cards/keyword?query=flying&limit=10" | jq '.cards[].name'

# Semantic search
curl "http://localhost:8000/api/cards/semantic?query=counterspells&limit=10" | jq '.cards[] | {name: .name, similarity: .similarity}'
```

---

## Baseline Test Results

These queries should consistently return good results:

### 1. Counterspells (Semantic)
**Query:** `counterspells`
- **Top Result:** Counterspell
- **Similarity:** ~0.73
- **Why it works:** Direct keyword match in card name and semantic meaning

### 2. Red Damage Spells (Semantic)
**Query:** `red spells that deal damage`
- **Expected:** Red instants/sorceries with damage effects
- **Similarity:** 0.40-0.55
- **Example Results:** Shock, Lightning Bolt, Lava Spike

### 3. Land Search (Semantic)
**Query:** `cards that search for lands`
- **Top Results:** Rampant Growth, Cultivate, land tutors
- **Similarity:** 0.55-0.60
- **Why it works:** Semantic understanding of "search" + "lands"

### 4. Flying Creatures (Semantic)
**Query:** `creatures with flying`
- **Expected:** Creature cards with flying keyword
- **Similarity:** 0.70-0.76
- **Why it works:** Strong semantic match to keyword ability

### 5. Lightning Bolt (Keyword)
**Query:** `Lightning Bolt`
- **Top Result:** Lightning Bolt
- **Why it works:** Exact name match gets highest priority

### 6. Destroy Creature (Keyword)
**Query:** `destroy target creature`
- **Expected:** Removal spells with that exact text
- **Why it works:** Exact phrase matching in oracle text

---

## Similarity Score Interpretation

Based on testing with `all-MiniLM-L6-v2` model:

| Score Range | Quality | Example |
|-------------|---------|---------|
| 0.70+ | Excellent | Query: "counterspells" → Counterspell (0.73) |
| 0.60-0.70 | Very Good | Query: "cards that search for lands" → Slimefoot's Survey (0.60) |
| 0.50-0.60 | Good | Query: "red spells that deal damage" → Chaoslace (0.55) |
| 0.40-0.50 | Moderate | Query: "cards that remove creatures" → Worm Harvest (0.50) |
| 0.30-0.40 | Fair | Loosely related results |
| <0.30 | Poor | Likely not relevant |

**Development Tip:** For semantic search, aim to return results with similarity >0.40 for good user experience.

---

## Test Case Categories

### Exact Match Tests (Keyword)
Use these to verify keyword search finds exact matches:
- `Lightning Bolt` → Should return Lightning Bolt first
- `Counterspell` → Should return Counterspell first
- `flying` → Should return cards with "flying" in text/name

### Phrase Match Tests (Keyword)
Use these to verify multi-word phrase matching:
- `destroy target creature` → Removal spells
- `draw a card` → Card draw effects
- `search your library` → Tutors and fetch effects

### Archetype Tests (Semantic)
Use these to verify semantic understanding of MTG archetypes:
- `counterspells` → Blue counter magic
- `red spells that deal damage` → Red burn/direct damage
- `cards that search for lands` → Green ramp spells
- `cards that remove creatures` → Creature removal
- `mana acceleration` → Ramp and ritual effects

### Natural Language Tests (Semantic)
Use these to verify natural language understanding:
- `creatures with flying` → Flying keyword
- `cards that draw multiple cards` → Card advantage
- `instant speed removal` → Instant-speed destruction/exile
- `big green creatures` → Large green creatures

---

## Regression Testing

After making changes to:
- Embedding generation
- Search algorithms
- Database schema
- API endpoints

Run the full test suite and compare results:

```bash
# Generate baseline
./tests/run_search_tests.sh > baseline_results.txt

# After changes, compare
./tests/run_search_tests.sh > new_results.txt
diff baseline_results.txt new_results.txt
```

---

## Known Issues

### 1. Multiple Printings
**Issue:** Same card appears multiple times (different printings)
**Example:** Lightning Bolt has 10+ printings
**Impact:** Search results show duplicates
**Workaround:** Deduplicate by name in application layer (test script does this)

### 2. Token Cards in Results
**Issue:** Token creatures may appear in semantic searches
**Example:** "creatures with flying" returns Bird tokens
**Impact:** Results may include non-playable cards
**Note:** This is expected behavior; filter tokens in UI if needed

### 3. Model Doesn't Know MTG Slang
**Issue:** Model doesn't understand MTG-specific terminology
**Example:** "board wipe" doesn't work as well as "destroy all creatures"
**Workaround:** Use descriptive phrases instead of slang
**Better Queries:**
  - Use: "destroy all creatures" instead of "board wipe"
  - Use: "counter target spell" instead of "permission"
  - Use: "cards that search for lands" instead of "ramp"

---

## Adding New Test Cases

When you want to test a new query pattern:

1. **Run the query manually:**
   ```bash
   python tests/test_search_fixtures.py --query "YOUR QUERY" --type semantic
   ```

2. **Evaluate the results:**
   - Are top 5 results relevant?
   - What's the similarity score threshold?
   - Do results match your expectations?

3. **Document in tests/SEARCH_TEST_CASES.md:**
   - Add query to appropriate category
   - List expected top results
   - Note similarity threshold
   - Explain what you're testing

4. **Add to run_search_tests.sh** if it's a core test case

---

## Files

- `tests/test_search_fixtures.py` - Python test fixture runner
- `tests/SEARCH_TEST_CASES.md` - Detailed test case documentation
- `tests/run_search_tests.sh` - Quick test suite runner
- `SEARCH_TESTING.md` - This file

---

## Example Output

When tests are working correctly, you should see:

```
SEMANTIC SEARCH TESTS
==================================

Query: counterspells
----------------------------------------
  Counterspell                             [U    ] 0.730  ✓ Excellent

Query: red spells that deal damage
----------------------------------------
  Shock                                    [R    ] 0.542  ✓ Good
  Lightning Bolt                           [R    ] 0.538  ✓ Good
```

If you see low similarity scores (<0.30) or irrelevant results, investigate:
- Is the query too vague?
- Does the embedding model understand the concept?
- Are there better phrasings of the query?
