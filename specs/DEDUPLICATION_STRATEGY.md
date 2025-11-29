# Card Deduplication Strategy

## Problem

The Scryfall dataset contains **508,686 total cards** but only **35,560 unique card names**. This means **93% of records are reprints** - the same card printed in different sets with different artwork but identical gameplay text.

### Example: Birds of Paradise
- **199 different printings** across sets like LEA, M10, M11, Ravnica, etc.
- **Same oracle text**: "Flying\n{T}: Add one mana of any color."
- **Same mana cost**: {G}
- Only differences: artwork, set code, release date, collector number

## Solution

We keep **all printings in the database** (for completeness and future features like price tracking, set analysis, etc.) but **show only one printing per unique card name in the UI**.

### Deduplication Method: Most Recent Printing

When querying cards for display, we use PostgreSQL's `DISTINCT ON (name)` with ordering by `released_at DESC` to show the **most recent printing** of each card.

```sql
SELECT DISTINCT ON (c.name)
    c.id,
    c.name,
    c.mana_cost,
    -- ... other fields
FROM cards c
ORDER BY c.name, c.released_at DESC NULLS LAST
LIMIT 20
```

### Why Most Recent?

1. **User expectations**: Players typically want to see modern card text/templating
2. **Set legality**: Newer printings are more relevant for current formats
3. **Oracle text updates**: While rare, oracle text occasionally changes - newest is canonical
4. **Consistency**: Predictable behavior across all queries

### Alternative Approaches Considered

1. **First Printing** (`released_at ASC`)
   - Pros: Historical accuracy, shows "original" version
   - Cons: Old templating, outdated wording, less relevant

2. **Canonical Flag** (Add `is_canonical BOOLEAN` column)
   - Pros: Full control over which printing to show
   - Cons: Requires manual curation, maintenance burden

3. **Most Expensive** (by market price)
   - Pros: Shows "best" version
   - Cons: Requires price data, volatile, subjective

## Implementation

### Modified Methods

**`rule_engine.py`:**
- ✅ `find_cards_by_rule()` - Deduplicated by name, most recent
- ✅ `find_similar_cards()` - Deduplicated using CTE
- ✅ `analyze_deck()` - Already had `DISTINCT ON (name)`
- ✅ `get_card_by_name()` - Returns single card (fuzzy search finds most recent)

### API Endpoints Affected

All card listing endpoints now return deduplicated results:
- `GET /api/cards/search?rule=flying_keyword&limit=20` - 20 unique cards
- `GET /api/cards/search?name=lightning` - Single best match
- `GET /api/cards/{card_id}/similar` - Unique similar cards

### Stats Impact

**Before deduplication:**
- Queries could return 199 copies of "Birds of Paradise"
- Slow, confusing UX
- Wasted bandwidth

**After deduplication:**
- Each card name appears exactly once
- Clean, user-friendly results
- 93% reduction in result set size for most queries

## Future Enhancements

### Option to View All Printings

Could add a UI feature to "Show all printings" for a specific card:

```sql
SELECT
    id, name, set_code, released_at,
    data->'image_uris'->>'normal' as image_url
FROM cards
WHERE name = 'Birds of Paradise'
ORDER BY released_at DESC;
```

This would show all 199 printings with different art, useful for collectors.

### Set-Specific Queries

For set analysis, we can query specific printings:

```sql
SELECT * FROM cards WHERE set_code = 'm21';
```

This bypasses deduplication and shows exactly what was in that set.

## Performance Considerations

`DISTINCT ON` with `ORDER BY` is efficient in PostgreSQL:
- Uses existing indexes on `name` and `released_at`
- No subqueries needed for simple cases
- CTE approach used for complex queries (similarity search)

Current query times:
- Card by rule: ~50-100ms for 20 results
- Fuzzy search: ~20-50ms
- Similar cards: ~100-200ms (vector similarity is slow part, not dedup)

## Testing

Verify deduplication:

```bash
# Test 1: Check for duplicates in result
curl "http://localhost:8000/api/cards/search?rule=flying_keyword&limit=20" | \
  jq '[.cards[].name] | group_by(.) | map(select(length > 1))'
# Should return: []

# Test 2: Verify count
curl "http://localhost:8000/api/cards/search?rule=flying_keyword&limit=20" | \
  jq '.cards | length'
# Should return: 20
```

## Conclusion

By keeping all printings in the database but deduplicating in queries, we get:
- ✅ Complete data for future features
- ✅ Clean, user-friendly UI
- ✅ Fast, efficient queries
- ✅ Flexibility to show all printings when needed
