# MTG Data Collection for LLM Training

## Purpose
Collect, process, and prepare MTG data for LLM training, focusing on Commander and Standard formats. This includes card data, combo data, deck lists, and gameplay patterns.

## Components

### Scrapers (`/scrapers`)
- **EDHREC Scrapers**: Combo data, popularity stats, deck recommendations
- **Commander Spellbook**: Comprehensive combo database
- **Scryfall**: Card data, rulings, legality
- **Moxfield**: Deck lists and archetypes
- **Format-Specific**: Commander and Standard focused scrapers

### Loaders (`/loaders`)
- Card data loading into PostgreSQL
- Bulk data processing
- Embedding generation
- Format filtering (Commander/Standard)

### Enrichment (`/enrichment`)
- Card data enrichment from multiple sources
- Combo validation and expansion
- Price data integration
- Card relationship mapping

### Output (`/output`)
- Scraped data storage
- Processed datasets
- Training data exports

### Tests (`/tests`)
- Scraper validation
- Data quality checks
- API integration tests

## Current Files to Migrate
- `/scripts/scrape_edhrec_combos_v2.py` (primary combo scraper)
- `/scripts/scrape_commander_spellbook.py`
- `/scripts/enrich_combos_with_card_data.py`
- `/scripts/loaders/*`
- All scraper utilities

## Data Sources
- EDHREC (43,544+ combos across 32 color combinations)
- Commander Spellbook (1.2GB combo data)
- Scryfall (509,000+ cards in cards.json)
- Moxfield (deck lists)

## Output Formats
- JSON datasets for training
- Vector embeddings
- Structured combo data
- Deck archetypes
