# Playability Filter Implementation

## Summary

Added `is_playable` column to filter out non-playable cards (tokens, planes, schemes, banned cards, etc.) from query results by default. Cards are considered playable if they are legal in Standard OR Commander format.

## Implementation Status

### ✅ Completed

1. **Database Migration** - `migrations/002_add_is_playable_column.py`
   - Adds `is_playable` boolean column
   - Adds `legality_updated_at` timestamp column
   - Populates based on: `standard='legal' OR commander='legal'`
   - Creates partial index on `is_playable` for performance
   - **Status**: Running (processing 508,686 cards)

2. **Rule Engine Updates** - `rule_engine.py`
   - Updated `search_cards_by_name()` with `include_nonplayable` parameter
   - Updated `find_cards_by_rule()` with `include_nonplayable` parameter
   - Updated `find_similar_cards()` with `include_nonplayable` parameter
   - Default: `include_nonplayable=False` (only show playable cards)

3. **API Endpoint Updates** - `api_server_rules.py`
   - Updated `/api/cards/search` with `include_nonplayable` query param
   - Updated `/api/cards/{card_id}/similar` with `include_nonplayable` query param
   - Updated `/api/rules/{rule_name}/cards` with `include_nonplayable` query param
   - Default: `include_nonplayable=false`

## Usage Examples

### API Endpoints

**Search for playable cards only (default)**:
```bash
GET /api/cards/search?name=Lightning
# Returns only cards legal in Standard or Commander
```

**Include non-playable cards**:
```bash
GET /api/cards/search?name=Warrior&include_nonplayable=true
# Returns all cards including token creatures
```

**Filter by rule (playable only)**:
```bash
GET /api/cards/search?rule=flying_keyword
# Returns only playable cards with flying
```

**Similar cards (playable only)**:
```bash
GET /api/cards/{card_id}/similar
# Returns only playable similar cards
```

### Python Rule Engine

```python
from rule_engine import MTGRuleEngine

engine = MTGRuleEngine(conn)

# Search playable cards only (default)
cards = engine.search_cards_by_name("Lightning")

# Include non-playable cards
all_cards = engine.search_cards_by_name("Warrior", include_nonplayable=True)

# Find cards by rule (playable only)
flying_cards = engine.find_cards_by_rule("flying_keyword")

# Find similar cards (playable only)
similar = engine.find_similar_cards(card_id)
```

## Database Statistics

**Expected results after migration**:
- Total cards: 508,686
- Playable cards: ~497,167 (97.7%)
- Non-playable cards: ~11,519 (2.3%)

**Non-playable card types**:
- Token creatures (Warrior, Thopter, etc.)
- Plane cards (Planechase format)
- Scheme cards (Archenemy format)
- Conspiracy cards
- Un-set cards (silver-bordered/acorn)
- Cards banned in BOTH Standard and Commander

## Migration Commands

**Run migration**:
```bash
python migrations/002_add_is_playable_column.py up
```

**Rollback migration**:
```bash
python migrations/002_add_is_playable_column.py down
```

## Performance

- **Indexed column**: Partial index on `is_playable = TRUE` for fast filtering
- **Query impact**: Minimal - simple boolean check with index
- **Storage impact**: 2 bytes per row (~1 MB total for 500K cards)

## Future Enhancements

1. **UI Toggle**: Add checkbox in Card Explorer to show/hide non-playable cards
2. **Legality Updates**: Periodic script to refresh `is_playable` when new sets release
3. **Legality Badges**: Show format-specific legality status on cards
4. **Advanced Filtering**: Filter by specific format (Standard, Commander, Modern, etc.)

## Latest Printing Focus

All queries use `DISTINCT ON (name)` with `ORDER BY released_at DESC` to ensure:
- Only one printing per unique card name is returned
- Latest/most recent printing is selected
- Handles basic lands with multiple art variants correctly
- No price data needed - selection based purely on release date

## Files Modified

1. `migrations/002_add_is_playable_column.py` - New migration script
2. `rule_engine.py` - Updated 3 query methods
3. `api_server_rules.py` - Updated 3 API endpoints
4. `CARD_LEGALITY_FILTER_PLAN.md` - Original planning document
5. `PLAYABILITY_FILTER_IMPLEMENTATION.md` - This document

## Testing Checklist

Once migration completes:

- [ ] Verify playable count matches expected (~497K cards)
- [ ] Test search without filter - should exclude tokens
- [ ] Test search with `include_nonplayable=true` - should include tokens
- [ ] Test basic lands still appear (Island, Plains, etc.)
- [ ] Test banned cards don't appear by default (Black Lotus, etc.)
- [ ] Verify UI card explorer shows only playable cards
- [ ] Check query performance with index
