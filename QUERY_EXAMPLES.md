# Query Examples - Quick Reference

## Your Original Query

```
GET /api/cards/advanced?query=zombies but not black more than 3 mana
```

**Parsed as:**
- Creature Type: zombies
- Excluded Color: black ({B})
- CMC Filter: > 3

**SQL Generated:**
```sql
WHERE cmc > 3 
  AND (mana_cost NOT LIKE '%{B}%' OR mana_cost IS NULL)
  AND [semantic search for "zombies"]
```

---

## More Examples

### Creature Type + Color Exclusion
```bash
# Zombies that aren't black
/api/cards/advanced?query=zombies but not black more than 3 mana

# Vampires without red
/api/cards/advanced?query=vampires without red

# Dragons excluding green
/api/cards/advanced?query=dragons not green
```

### Only Specific Colors
```bash
# ONLY blue zombies (no other colors)
/api/cards/advanced?query=zombies only blue

# ONLY red goblins
/api/cards/advanced?query=goblins but only red
```

### CMC Filters
```bash
# Low-cost creatures
/api/cards/advanced?query=creatures 2 mana or less

# Big dragons
/api/cards/advanced?query=dragons more than 6 mana

# Exact cost
/api/cards/advanced?query=exactly 3 mana removal
```

### Multiple Filters Combined
```bash
# Rare, high-power, flying dragons
/api/cards/advanced?query=rare dragons with flying power >= 5

# Budget blue control
/api/cards/advanced?query=blue instants 3 mana or less uncommon or common

# Small evasive creatures
/api/cards/advanced?query=creatures with flying cmc <= 2 not white
```

### Keywords
```bash
# Creatures with flying
/api/cards/advanced?query=blue creatures with flying

# Creatures without haste
/api/cards/advanced?query=red creatures without haste

# Multiple keywords
/api/cards/advanced?query=creatures with flying and vigilance
```

### Power/Toughness
```bash
# Big creatures
/api/cards/advanced?query=creatures power > 5

# Small creatures
/api/cards/advanced?query=creatures toughness <= 1

# 3/3 or bigger
/api/cards/advanced?query=3/3 or bigger zombies
```

---

## Test Your Queries

### Basic Test
```bash
curl "http://localhost:8000/api/cards/advanced?query=zombies%20but%20not%20black%20more%20than%203%20mana"
```

### With Pagination
```bash
# First 10 results
curl "http://localhost:8000/api/cards/advanced?query=dragons&limit=10&offset=0"

# Next 10 results
curl "http://localhost:8000/api/cards/advanced?query=dragons&limit=10&offset=10"
```

### Include Non-Playable Cards
```bash
curl "http://localhost:8000/api/cards/advanced?query=warrior&include_nonplayable=true"
```

---

## Parser Output Examples

### Example 1: Your Query
```python
Input:  "zombies but not black more than 3 mana"
Output: {
    "positive_terms": "zombies",
    "exclusions": ["black"],
    "filters": {
        "cmc_gt": 3,
        "exclude_colors": ["B"]
    }
}
```

### Example 2: Complex Query
```python
Input:  "rare dragons with flying cmc >= 5 not green"
Output: {
    "positive_terms": "dragons",
    "exclusions": ["green"],
    "filters": {
        "cmc_gte": 5,
        "exclude_colors": ["G"],
        "rarity": "rare",
        "include_keywords": ["flying"]
    }
}
```

### Example 3: Only Colors
```python
Input:  "zombies only blue"
Output: {
    "positive_terms": "zombies",
    "exclusions": ["red", "white", "black", "green"],
    "filters": {
        "exclude_colors": ["W", "B", "R", "G"],
        "only_colors": ["U"]
    }
}
```

---

## Supported Filters Summary

| Filter Type | Examples | SQL Column |
|-------------|----------|------------|
| **Creature Type** | zombies, dragons, elves | `type_line` |
| **Colors (Include)** | blue, red and green | `mana_cost` |
| **Colors (Exclude)** | not black, without red | `mana_cost` |
| **Colors (Only)** | only blue, but only red | `mana_cost` |
| **CMC** | more than 3 mana, cmc < 4 | `cmc` |
| **Card Type** | creatures, instants | `type_line` |
| **Keywords** | with flying, no haste | `keywords`, `oracle_text` |
| **Rarity** | rare, mythic | `rarity` |
| **Power** | power > 4 | `power` |
| **Toughness** | toughness >= 3 | `toughness` |

---

## API Endpoints Comparison

| Endpoint | Use When |
|----------|----------|
| `/api/cards/search?name=` | You know the exact card name |
| `/api/cards/keyword?query=` | You want exact text matches |
| `/api/cards/semantic?query=` | You want natural language search |
| **`/api/cards/advanced?query=`** | **You need complex filters (BEST)** |

---

## Next Steps

1. **Start the API server:**
   ```bash
   cd scripts
   python3 api/api_server_rules.py
   ```

2. **Test your query:**
   ```bash
   curl "http://localhost:8000/api/cards/advanced?query=zombies%20but%20not%20black%20more%20than%203%20mana"
   ```

3. **View API docs:**
   Open http://localhost:8000/docs in your browser

4. **Read full guide:**
   See `specs/ADVANCED_SEARCH_GUIDE.md`

---

## Implementation Files

- **Parser:** `scripts/api/advanced_query_parser.py`
- **API Endpoint:** `scripts/api/api_server_rules.py` (line ~457)
- **Tests:** `tests/test_advanced_query_parser.py`
- **Guide:** `specs/ADVANCED_SEARCH_GUIDE.md`
