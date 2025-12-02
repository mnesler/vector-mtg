# Advanced Search Guide

## Overview

The Advanced Search endpoint (`/api/cards/advanced`) provides powerful natural language query parsing with support for complex filters including creature types, colors, mana costs, keywords, and more.

## Quick Start

### Your Example Query

```bash
GET /api/cards/advanced?query=zombies but not black more than 3 mana
```

**What this does:**
1. Finds cards with "zombie" in the type line (creature type)
2. Excludes cards with black mana ({B}) in their mana cost
3. Filters to cards with CMC (Converted Mana Cost) > 3

**Example Results:**
- Gravecrawler (Blue zombie, CMC 4)
- Diregraf Captain (Blue/White zombie, CMC 4)
- Undead Alchemist (Blue zombie, CMC 5)

---

## Supported Filter Types

### 1. Creature Types

Search by creature subtype:

```
zombies
dragons
elves and goblins
vampire lords
```

**How it works:** Searches the `type_line` field for the creature type.

### 2. Color Filters

#### Include Colors
```
blue zombies          → Cards that contain blue mana
red and green wolves  → Cards with red AND green
```

#### Exclude Colors
```
zombies not black        → Zombies without black mana
vampires without red     → Vampires without red mana
dragons no green no blue → Dragons without green or blue
```

#### Only Specific Colors
```
zombies only blue     → ONLY blue zombies (excludes W, B, R, G)
elves but only green  → ONLY green elves
```

**How it works:** Checks the `mana_cost` field for color symbols ({W}, {U}, {B}, {R}, {G}).

### 3. Mana Cost (CMC) Filters

#### Greater Than
```
more than 3 mana
greater than 5 mana
cmc > 4
```

#### Less Than
```
less than 3 mana
fewer than 2 mana
cmc < 4
```

#### Ranges
```
3 mana or more       → CMC >= 3
2 mana or less       → CMC <= 2
4+ mana              → CMC >= 4
1- mana              → CMC <= 1
```

#### Exact Value
```
exactly 3 mana       → CMC = 3
2 mana               → CMC = 2 (defaults to exact)
```

### 4. Card Type Filters

```
creatures            → Type line contains "Creature"
instants             → Type line contains "Instant"
artifacts            → Type line contains "Artifact"
enchantments         → Type line contains "Enchantment"
planeswalkers        → Type line contains "Planeswalker"
```

Can be combined with other filters:
```
blue creatures cmc < 3
rare artifacts
legendary enchantments
```

### 5. Keyword Abilities

#### Include Keywords
```
with flying
has trample
having vigilance and haste
```

#### Exclude Keywords
```
without flying
no haste
creatures no deathtouch
```

**Supported Keywords:**
- flying, trample, haste, vigilance, deathtouch
- lifelink, menace, reach, first strike, double strike
- hexproof, indestructible, flash, defender

### 6. Rarity Filters

```
rare zombies
mythic dragons
uncommon removal
common creatures
mythic rare planeswalkers
```

### 7. Power/Toughness Filters

```
power > 4                → Creatures with power greater than 4
toughness >= 5           → Creatures with toughness 5 or more
3/3 or bigger           → Power >= 3 AND Toughness >= 3
2/2 or smaller          → Power <= 2 AND Toughness <= 2
```

---

## Complex Query Examples

### Example 1: Budget Blue Control Cards
```
GET /api/cards/advanced?query=blue instants or sorceries 3 mana or less uncommon or common
```

**Finds:** Inexpensive blue instant/sorcery spells for budget control decks.

### Example 2: High-Power Red Creatures
```
GET /api/cards/advanced?query=red creatures power >= 5 cmc < 6
```

**Finds:** Efficient big red creatures (high power, reasonable cost).

### Example 3: Non-Black Zombies for Tribal Deck
```
GET /api/cards/advanced?query=zombies but not black more than 3 mana
```

**Finds:** Alternative-color zombies for unique tribal builds.

### Example 4: Small Evasive Creatures
```
GET /api/cards/advanced?query=creatures with flying cmc <= 2 not white
```

**Finds:** Low-cost flying creatures outside of white.

### Example 5: Big Green Beasts
```
GET /api/cards/advanced?query=beasts only green power > 4 rare or mythic
```

**Finds:** Powerful green-only beast creatures at higher rarities.

### Example 6: Removal on a Budget
```
GET /api/cards/advanced?query=instants or sorceries 2 mana or less common destroy creature
```

**Finds:** Cheap, common creature removal spells.

### Example 7: Commander-Legal Blue Dragons
```
GET /api/cards/advanced?query=dragons blue or blue and red cmc >= 5 legendary
```

**Finds:** Blue dragon commanders or finishers.

### Example 8: Aggressive Red Creatures
```
GET /api/cards/advanced?query=red creatures with haste power >= 3 cmc < 4
```

**Finds:** Efficient hasty red beaters.

---

## API Response Format

### Success Response

```json
{
  "query": "zombies but not black more than 3 mana",
  "parsed": {
    "positive_terms": "zombies",
    "exclusions": ["black"],
    "filters": {
      "type_line_contains": ["zombie"],
      "cmc_gt": 3,
      "exclude_colors": ["B"]
    }
  },
  "search_type": "advanced",
  "count": 15,
  "offset": 0,
  "limit": 20,
  "has_more": false,
  "cards": [
    {
      "id": "abc-123",
      "name": "Undead Alchemist",
      "mana_cost": "{3}{U}",
      "cmc": 4.0,
      "type_line": "Creature — Zombie",
      "oracle_text": "If a Zombie you control would deal combat damage...",
      "keywords": [],
      "colors": ["U"],
      "power": "4",
      "toughness": "2",
      "rarity": "rare",
      "similarity": 0.87
    }
    // ... more cards
  ]
}
```

### Fields Explained

- **query**: Original query string
- **parsed**: Breakdown of how the query was interpreted
  - **positive_terms**: Main search terms (semantic search)
  - **exclusions**: Terms to exclude
  - **filters**: Structured filters applied
- **search_type**: Always "advanced"
- **count**: Number of results returned
- **offset**: Pagination offset
- **limit**: Maximum results per page
- **has_more**: Whether more results exist (for pagination)
- **cards**: Array of matching cards
  - **similarity**: Semantic similarity score (0-1, higher = better match)

---

## Query Parser Logic

### Processing Order

1. **Extract CMC filters** ("more than 3 mana")
2. **Extract Power/Toughness filters** ("power > 4")
3. **Extract Color filters** ("not black", "only blue")
4. **Extract Type filters** ("creatures", "instants")
5. **Extract Rarity filters** ("rare", "mythic")
6. **Extract Keyword filters** ("with flying", "no haste")
7. **Remaining text** → Positive search terms (semantic search)

### Semantic Search Component

After extracting all structured filters, the remaining text is used for **semantic similarity search** using vector embeddings.

**Example:**
```
Query: "zombies but not black more than 3 mana"

After extraction:
- Filters: cmc > 3, exclude black
- Remaining: "zombies"
- Semantic search for "zombies" + apply filters
```

This means you get the **best of both worlds**:
- **Structured filtering** (exact matches on CMC, colors, etc.)
- **Semantic search** (finds relevant cards even with varied wording)

---

## Tips for Best Results

### 1. Be Specific with Creature Types
✅ Good: `zombies`, `dragons`, `elves`  
❌ Less effective: `undead`, `flying lizards`

### 2. Use Standard Color Names
✅ Good: `blue`, `red`, `black`, `green`, `white`  
❌ Won't work: `azure`, `crimson`, `dark`

### 3. CMC Filters Are Smart
All these work:
- `more than 3 mana`
- `cmc > 3`
- `4+ mana`
- `greater than 3 mana`

### 4. Combine Multiple Filters
Complex queries are encouraged!
```
rare blue dragons with flying cmc >= 6 power > 5
```

### 5. Exclusions Work Everywhere
You can exclude colors, keywords, or general terms:
```
zombies not black without haste
```

---

## Pagination

Use `offset` and `limit` parameters:

```bash
# Page 1 (results 1-20)
GET /api/cards/advanced?query=zombies&limit=20&offset=0

# Page 2 (results 21-40)
GET /api/cards/advanced?query=zombies&limit=20&offset=20

# Page 3 (results 41-60)
GET /api/cards/advanced?query=zombies&limit=20&offset=40
```

Check `has_more` in the response to know if more results exist.

---

## Playability Filter

By default, only returns **playable cards** (legal in Standard OR Commander).

**Excludes:**
- Token creatures
- Plane cards (Planechase)
- Scheme cards (Archenemy)
- Banned cards in both formats
- Un-set cards (silver-bordered/acorn)

**To include non-playable cards:**
```bash
GET /api/cards/advanced?query=warrior&include_nonplayable=true
```

---

## Error Handling

### Empty Query
```json
{
  "detail": "Query parameter cannot be empty"
}
```

### Only Exclusions (No Positive Terms)
If your query is ONLY exclusions (e.g., "not black not red"), results may be very broad. Consider adding positive search terms.

---

## Comparison with Other Endpoints

| Endpoint | Use Case | Filters | Semantic Search |
|----------|----------|---------|-----------------|
| `/api/cards/search?name=` | Simple name search | ❌ | ❌ |
| `/api/cards/keyword` | Exact text match | ❌ | ❌ |
| `/api/cards/semantic` | Natural language | Basic exclusions | ✅ |
| `/api/cards/advanced` | **Complex queries** | **Full suite** | **✅** |

**Use `/api/cards/advanced` when you need:**
- Multiple filter types (CMC + colors + keywords)
- Complex exclusions
- Natural language creature type search
- Best overall search experience

---

## Implementation Details

### Parser: `advanced_query_parser.py`

The `AdvancedQueryParser` class handles all query parsing logic:

```python
from api.advanced_query_parser import get_advanced_parser

parser = get_advanced_parser()
parsed = parser.parse("zombies but not black more than 3 mana")

# Result:
# ParsedQuery(
#     positive_terms="zombies",
#     exclusions=["black"],
#     filters={
#         "type_line_contains": ["zombie"],
#         "cmc_gt": 3,
#         "exclude_colors": ["B"]
#     }
# )
```

### SQL Generation

The parser automatically generates SQL WHERE clauses:

```python
where_clause, params = parser.to_sql_where_clause(parsed)

# Result:
# where_clause = "cmc > %s AND mana_cost NOT LIKE %s OR mana_cost IS NULL"
# params = [3, '%{B}%']
```

---

## Testing

Run the test suite:

```bash
pytest tests/test_advanced_query_parser.py -v
```

**Test Coverage:**
- CMC filters (all operators)
- Color filters (include, exclude, only)
- Complex multi-filter queries
- Edge cases (empty query, only exclusions)
- SQL generation correctness

---

## Future Enhancements

### Planned Features

1. **Set/Block Filters**
   ```
   dragons from Tarkir
   cards from Zendikar Rising
   ```

2. **Format Filters**
   ```
   legal in modern
   banned in standard
   commander legal zombies
   ```

3. **Artist Filters**
   ```
   illustrated by Seb McKinnon
   art by Rebecca Guay
   ```

4. **Price Filters**
   ```
   under $5
   budget friendly
   less than 2 dollars
   ```

5. **Set Symbol/Rarity Combo**
   ```
   mythics from Eldraine
   rares from recent sets
   ```

---

## Summary

The Advanced Search endpoint provides a **natural language interface** to MTG card search with support for:

✅ **Creature types** - Zombies, dragons, elves, etc.  
✅ **Color filters** - Include, exclude, or "only" specific colors  
✅ **CMC filters** - Greater than, less than, exact, ranges  
✅ **Card types** - Creatures, instants, artifacts, etc.  
✅ **Keywords** - Flying, haste, trample, etc.  
✅ **Rarity** - Common, uncommon, rare, mythic  
✅ **Power/Toughness** - Size-based creature filters  
✅ **Semantic search** - Natural language understanding  
✅ **Playability filter** - Exclude tokens and unplayable cards  

**Your query works perfectly:**
```
GET /api/cards/advanced?query=zombies but not black more than 3 mana
```

This will return zombies that:
- ✅ Are zombie creature types
- ✅ Don't have black mana in their cost
- ✅ Have CMC > 3
