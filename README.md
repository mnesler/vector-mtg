# vector-mtg

A project for working with Magic: The Gathering card data using vector databases and PostgreSQL.

## Dataset

The project contains a Scryfall JSON dataset with approximately 509,000 MTG cards (2.3GB).

- **File**: `cards.json`
- **Format**: JSON array of card objects
- **Source**: [Scryfall Bulk Data API](https://scryfall.com/docs/api/bulk-data)

## Infrastructure

PostgreSQL 16 database running in Docker:

```bash
# Start the database
docker-compose up -d

# Stop the database
docker-compose down

# Access psql
docker exec -it vector-mtg-postgres psql -U postgres -d vector_mtg
```

**Database Connection:**
- Host: localhost:5432
- Database: vector_mtg
- User/Password: postgres/postgres

## Card Schema

Each card in `cards.json` has the following structure:

### Core Identity
- `object`: "card"
- `id`: UUID - Unique Scryfall ID
- `oracle_id`: UUID - Groups functionally identical cards
- `name`: Card name
- `lang`: Language code (e.g., "en")

### Platform IDs
- `multiverse_ids`: number[]
- `mtgo_id`, `mtgo_foil_id`: Magic Online IDs
- `arena_id`: MTG Arena ID
- `tcgplayer_id`, `cardmarket_id`: Marketplace IDs

### Card Properties
- `mana_cost`: Mana symbols (e.g., "{5}{R}")
- `cmc`: number - Converted mana cost
- `type_line`: Full type (e.g., "Creature — Sliver")
- `oracle_text`: Rules text
- `power`, `toughness`: Creature stats (creatures only)
- `flavor_text`: Flavor text (optional)
- `keywords`: string[] - Keyword abilities

### Colors & Identity
- `colors`: string[] - Card colors (W, U, B, R, G)
- `color_identity`: string[] - Commander color identity
- `produced_mana`: string[] - Mana produced (lands)

### Set Information
- `set`: Set code (e.g., "blb", "tsp")
- `set_name`: Full set name
- `set_id`: UUID
- `set_type`: "expansion", "commander", etc.
- `released_at`: Date (YYYY-MM-DD)
- `collector_number`: Card number in set

### Legality
- `legalities`: Object with format legalities
  - Keys: `standard`, `modern`, `legacy`, `vintage`, `commander`, `pauper`, etc.
  - Values: "legal", "not_legal", "restricted", "banned"

### Rarity & Printing
- `rarity`: "common", "uncommon", "rare", "mythic"
- `digital`: boolean
- `foil`, `nonfoil`: boolean
- `finishes`: string[] - ["nonfoil", "foil"]
- `oversized`, `promo`, `reprint`, `variation`: boolean

### Visual Properties
- `layout`: "normal", "transform", "split", etc.
- `frame`: Frame version (e.g., "2003", "2015")
- `border_color`: "black", "white", etc.
- `full_art`, `textless`: boolean
- `highres_image`: boolean
- `image_status`: "highres_scan", "lowres", etc.

### Images
- `image_uris`: Object (single-faced cards)
  - `small`, `normal`, `large`, `png`: Image URLs
  - `art_crop`, `border_crop`: Cropped versions

### Artist & Illustration
- `artist`: Artist name
- `artist_ids`: UUID[]
- `illustration_id`: UUID
- `card_back_id`: UUID

### Prices
- `prices`: Object
  - `usd`, `usd_foil`, `usd_etched`: US Dollar prices
  - `eur`, `eur_foil`: Euro prices
  - `tix`: MTGO ticket price

### Rankings (optional)
- `edhrec_rank`: EDH/Commander popularity
- `penny_rank`: Penny Dreadful ranking

### Metadata
- `reserved`: boolean - Reserved list
- `booster`: boolean - Available in boosters
- `story_spotlight`: boolean
- `games`: string[] - ["paper", "mtgo", "arena"]

### URIs
- `uri`: Scryfall API URL
- `scryfall_uri`: Scryfall website URL
- `rulings_uri`: Card rulings API endpoint
- `prints_search_uri`: All printings search
- `related_uris`: Links to Gatherer, TCGPlayer, EDHREC
- `purchase_uris`: Purchase links

### Example Card

```json
{
  "object": "card",
  "id": "0000579f-7b35-4ed3-b44c-db2a538066fe",
  "name": "Fury Sliver",
  "mana_cost": "{5}{R}",
  "cmc": 6.0,
  "type_line": "Creature — Sliver",
  "oracle_text": "All Sliver creatures have double strike.",
  "power": "3",
  "toughness": "3",
  "colors": ["R"],
  "color_identity": ["R"],
  "set": "tsp",
  "set_name": "Time Spiral",
  "rarity": "uncommon",
  "prices": {
    "usd": "0.43",
    "usd_foil": "3.72"
  }
}
```

**Note:** Cards with special layouts (transform, split, adventure, etc.) may have a `card_faces` array instead of direct card properties.
