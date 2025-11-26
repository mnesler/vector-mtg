# Card Legality Filtering Plan

## Problem Statement

The database contains 508,686 cards with these issues:
1. **Multiple printings**: Same card printed many times (e.g., basic lands with different art)
2. **Non-playable cards**: ~11,519 cards (2.3%) are not legal in Standard OR Commander
3. **Target formats**: Focus on Standard and Commander legality only

### Current Statistics
- **Total cards**: 508,686
- **Standard legal**: 66,302 (13%)
- **Commander legal**: 497,167 (97.7%)
- **Playable (Standard OR Commander)**: 497,167 (97.7%)
- **Non-playable**: 11,519 (2.3%)

### Non-playable Card Types
Based on sample data, non-playable cards include:
- **Tokens**: "Token Creature — Warrior", "Token Artifact Creature — Thopter"
- **Planes**: "Plane — Ikoria" (for Planechase format)
- **Schemes**: "Scheme" cards (from Archenemy)
- **Conspiracies**: "Conspiracy" cards
- **Un-set cards**: "Carnivorous Death-Parrot" (silver-bordered/acorn cards)
- **Banned cards**: Cards banned in both formats (e.g., "Hired Heist")
- **Test cards**: Playtest/experimental cards

## Data Structure

Cards have legality data in JSONB `data` field:
```json
{
  "legalities": {
    "standard": "legal" | "not_legal" | "banned" | "restricted",
    "commander": "legal" | "not_legal" | "banned" | "restricted"
  }
}
```

## Solution Options

### Option 1: Add Database Column (RECOMMENDED)
**Pros:**
- Fast queries with indexed column
- Easy to update if legality changes
- Clean separation of concerns
- Can track when legality was last checked

**Cons:**
- Schema migration required
- Need to run one-time update to populate

**Implementation:**
```sql
-- Add column
ALTER TABLE cards ADD COLUMN is_playable BOOLEAN DEFAULT TRUE;

-- Populate column
UPDATE cards
SET is_playable = (
    data->'legalities'->>'standard' = 'legal' OR
    data->'legalities'->>'commander' = 'legal'
);

-- Add index for fast filtering
CREATE INDEX idx_cards_playable ON cards(is_playable) WHERE is_playable = TRUE;

-- Optional: track when last updated
ALTER TABLE cards ADD COLUMN legality_updated_at TIMESTAMP DEFAULT NOW();
```

### Option 2: Query-Time Filtering
**Pros:**
- No schema changes
- Always uses current JSONB data

**Cons:**
- Slower queries (must check JSONB every time)
- More complex WHERE clauses
- Cannot easily index JSONB for this

**Implementation:**
```sql
SELECT * FROM cards
WHERE (
    data->'legalities'->>'standard' = 'legal' OR
    data->'legalities'->>'commander' = 'legal'
)
```

### Option 3: Materialized View
**Pros:**
- No changes to main table
- Fast queries
- Can be refreshed periodically

**Cons:**
- More complex to maintain
- Takes additional storage

## Recommended Approach

**Use Option 1 (Database Column)** for these reasons:
1. Best performance for all queries
2. Simple to implement and maintain
3. Easy to add UI filter toggle ("Show non-playable cards")
4. Can track legality updates separately from main card data

## Implementation Status

✅ Migration script created: `migrations/002_add_is_playable_column.py`
✅ Migration running (processing 508,686 cards)
⏳ Next: Update queries in rule_engine.py to filter by is_playable
⏳ Next: Update API endpoints to support include_nonplayable parameter

## Implementation Plan

### Step 1: Add Database Column
- Add `is_playable` boolean column with default TRUE
- Add `legality_updated_at` timestamp column
- Create index on `is_playable`

### Step 2: Populate Existing Data
- Run UPDATE query to set `is_playable` based on current legalities
- Set `legality_updated_at` to NOW()

### Step 3: Update Data Loading Script
- Modify `load_cards_with_keywords.py` to set `is_playable` during initial load
- Calculate: `is_playable = (legalities.standard == 'legal' OR legalities.commander == 'legal')`

### Step 4: Update Rule Engine Queries
Modify all query methods in `rule_engine.py`:
- `search_cards_by_name()` - Add WHERE clause
- `find_cards_by_rule()` - Add WHERE clause
- `find_similar_cards()` - Add WHERE clause

Add WHERE clause: `WHERE is_playable = TRUE`

Optional: Add parameter `include_nonplayable=False` to allow showing all cards when needed

### Step 5: Update API Endpoints
Add optional query parameter to API endpoints:
- `/api/cards/search?name=X&include_nonplayable=false`
- `/api/rules/{rule}/cards?include_nonplayable=false`

Default to `include_nonplayable=false` for normal use

### Step 6: Update UI (Optional)
Add checkbox in Card Explorer:
- "Show non-playable cards" (unchecked by default)
- When checked, passes `include_nonplayable=true` to API

### Step 7: Add Status Indicator
For cards that ARE shown but have legality issues:
- Show badge on card: "Standard" (green), "Commander only" (blue), "Banned" (red)
- Can distinguish between legal, not_legal, banned, restricted

## Special Considerations

### Basic Lands
- All basic lands (Island, Plains, etc.) are legal in all formats
- Still show only one printing per unique name in UI (existing deduplication)
- User can see different art variants if needed

### Banned vs Not Legal
- **"banned"**: Card exists in format but is banned (was legal at some point)
- **"not_legal"**: Card was never legal in that format
- Both should be filtered out by default
- Could show banned cards with warning indicator

### Future Proofing
- Legalities can change with new set releases
- Need process to refresh `is_playable` column periodically
- Consider adding script: `update_legalities.py` that re-checks all cards

## Migration Script Template

```python
#!/usr/bin/env python3
"""
Add playability filtering to cards table
"""
import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'vector_mtg',
    'user': 'postgres',
    'password': 'postgres'
}

def migrate():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    print("Adding is_playable column...")
    cur.execute("""
        ALTER TABLE cards
        ADD COLUMN IF NOT EXISTS is_playable BOOLEAN DEFAULT TRUE,
        ADD COLUMN IF NOT EXISTS legality_updated_at TIMESTAMP DEFAULT NOW()
    """)

    print("Populating is_playable values...")
    cur.execute("""
        UPDATE cards
        SET is_playable = (
            data->'legalities'->>'standard' = 'legal' OR
            data->'legalities'->>'commander' = 'legal'
        ),
        legality_updated_at = NOW()
    """)

    rows_updated = cur.rowcount
    print(f"Updated {rows_updated:,} rows")

    print("Creating index...")
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_cards_playable
        ON cards(is_playable)
        WHERE is_playable = TRUE
    """)

    conn.commit()

    # Verify results
    cur.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE is_playable = TRUE) as playable,
            COUNT(*) FILTER (WHERE is_playable = FALSE) as non_playable
        FROM cards
    """)
    result = cur.fetchone()

    print(f"\nResults:")
    print(f"  Total cards: {result[0]:,}")
    print(f"  Playable: {result[1]:,} ({100*result[1]/result[0]:.1f}%)")
    print(f"  Non-playable: {result[2]:,} ({100*result[2]/result[0]:.1f}%)")

    conn.close()
    print("\n✓ Migration complete!")

if __name__ == '__main__':
    migrate()
```

## Testing Plan

1. **Verify counts**: Ensure playable count matches expected (497,167)
2. **Test queries**: Confirm filtered queries return only playable cards
3. **Test UI**: Search for known non-playable cards, verify they don't appear
4. **Test basic lands**: Verify Island, Plains, etc. still appear
5. **Test banned cards**: Verify "Black Lotus" doesn't appear in results
6. **Performance test**: Compare query speeds before/after

## Rollback Plan

If issues occur:
```sql
-- Remove columns
ALTER TABLE cards
DROP COLUMN IF EXISTS is_playable,
DROP COLUMN IF EXISTS legality_updated_at;

-- Drop index
DROP INDEX IF EXISTS idx_cards_playable;
```
