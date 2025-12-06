# Comprehensive EDH Data Scraping Strategy

## Current Status

We now have comprehensive scrapers running that hit:
1. **EDHREC** - 32+ commanders found
2. **TappedOut** - 90+ recent EDH decks
3. **Moxfield** - Deck templates
4. **Scryfall** - 500K+ cards (already have)

## Next Steps: Maximize Data Collection

### Phase 1: EDHREC Full Harvest (Highest Priority)

**Goal:** Get ALL 1000+ commanders and their top cards

**Strategy:**
1. Scrape commanders from multiple EDHREC pages
2. For each commander, fetch:
   - Top 100 cards (with inclusion %, synergy scores)
   - Deck techs
   - Related commanders
   - Archetype information

**Data Points per Commander:**
- Name, colors, image, type
- Top 100 cards
- Card synergy scores (0-100)
- Inclusion percentages
- Budget variants
- Related commanders

**Volume:** 1000 commanders × 100 cards = 100,000+ card-commander relationships

### Phase 2: Deck Mining (Second Priority)

**Sources:**
1. TappedOut API (seems to work)
2. Archidekt.com (has public decks)
3. Deckstats.net (deck statistics)
4. MTGGoldfish (decks of the week)

**Data Points per Deck:**
- Deck name, commander, colors
- All 99 cards + quantities
- Mana curve
- Card types breakdown
- Win conditions
- Ratings/comments
- Upload date

**Volume:** 10,000-100,000+ real decks

### Phase 3: Meta Analysis

**Sources:**
1. EDHREC meta snapshots
2. MTGGoldfish meta reports
3. AetherHub meta data

**Data Tracked:**
- Top commanders by month
- Card popularity trends
- Format shifts
- Ban impacts
- New set effects

### Phase 4: Enrichment Data

**Price Data:**
- Scryfall prices
- TCGPlayer market prices
- CardKingdom prices
- CardMarket (EU) prices

**Card Interactions:**
- Rulings database
- Interaction points (tutors, recursion, etc.)
- Legality across formats

## Implementation Roadmap

### Scraper Improvements Needed

1. **Better EDHREC Scraping**
   - Use pagination or search to find ALL commanders
   - Fetch commander detail pages for full card lists
   - Parse inclusion percentages and synergy scores

2. **Deck Parser**
   - Extract deck list from raw text
   - Identify commander
   - Count cards
   - Calculate mana curve

3. **Meta Tracker**
   - Store snapshots over time
   - Track trends
   - Identify shifts

4. **Price Aggregator**
   - Consolidate prices from multiple sources
   - Track price history
   - Identify buyouts

## Expected Data Volume

```
Current:  ~10K items
Phase 1:  +100K items (commanders + cards)
Phase 2:  +100K items (real decks)
Phase 3:  +10K items (meta data)
Phase 4:  +2.5M items (prices + interactions)
─────────────────────────
Total:    ~2.7M items
```

## Storage Considerations

```
Structure:
data_sources_comprehensive/
├── edhrec_full/           # 1000+ commanders
│   ├── commanders.json    # All commander data
│   ├── cards.json         # All card-commander relationships
│   └── combos.json        # Combo database
├── decks/
│   ├── tappedout.json     # TappedOut decks
│   ├── archidekt.json     # Archidekt decks
│   └── deckstats.json     # DeckStats data
├── meta/
│   ├── monthly/           # Monthly snapshots
│   ├── trends.json        # Trend analysis
│   └── format_shifts.json # Meta changes
├── prices/
│   ├── current.json       # Latest prices
│   └── history/           # Price history
└── interactions/          # Card interactions
```

## Quick Wins (Easy Additions)

1. **EDHREC Combos** - Scrape full combo database
2. **TappedOut Decks** - Already have API, increase scraping
3. **Scryfall Bulk API** - Get all prices/art/rulings
4. **MTGGoldfish Lists** - Fetch popular deck lists

## Implementation Priority

| Priority | Task | Effort | Data Gain | 
|----------|------|--------|-----------|
| 🔴 HIGH | EDHREC all commanders | 2h | 100K items |
| 🔴 HIGH | Deck mining (100K decks) | 3h | 100K items |
| 🟡 MED  | Price aggregation | 2h | 2.5M items |
| 🟡 MED  | Meta snapshots | 1h | 10K items |
| 🟢 LOW  | Interaction mappings | 2h | Varies |

## Next Immediate Actions

1. **Enhance EDHREC Scraper**
   - Get complete commander list from edhrec.com/commanders
   - For each commander, scrape detail page
   - Extract card lists with synergy scores

2. **Expand Deck Sources**
   - Increase TappedOut deck scraping
   - Add Archidekt deck harvesting
   - Parse raw deck lists

3. **Implement Storage**
   - Organize by category
   - Add timestamp tracking
   - Create index files

Would you like me to prioritize Phase 1 (EDHREC commanders) or Phase 2 (Deck mining)?
