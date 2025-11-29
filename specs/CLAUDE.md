# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Vector-MTG is a project for working with Magic: The Gathering card data using vector databases and PostgreSQL. The project contains a large Scryfall JSON dataset (2.3GB, ~509K cards) that needs to be efficiently loaded and queried.

## Data Source

- **cards.json**: 2.3GB JSON file containing ~509,000 MTG cards from Scryfall API
- **Format**: JSON array of card objects with extensive metadata (id, name, mana_cost, type_line, oracle_text, colors, legalities, prices, image_uris, etc.)
- **Source**: Scryfall bulk data (https://scryfall.com/docs/api/bulk-data)

## Infrastructure

### PostgreSQL Database

The project uses PostgreSQL 16 (Alpine) running in Docker:

```bash
# Start the database
docker-compose up -d

# Stop the database
docker-compose down

# View logs
docker logs vector-mtg-postgres

# Access psql
docker exec -it vector-mtg-postgres psql -U postgres -d vector_mtg
```

**Connection Details:**
- Host: localhost
- Port: 5432
- Database: vector_mtg
- User: postgres
- Password: postgres

The database has a health check configured and data persists in a Docker volume.

## Development Architecture

This is currently a greenfield project without implemented code. The intended architecture will involve:

1. **Data Loading Layer**: Stream processing to load cards.json into PostgreSQL without exhausting memory (2.3GB file requires streaming approach)
2. **Database Schema**: Likely a hybrid approach with extracted columns for common queries + JSONB column for full card data
3. **Vector Integration**: Will use PostgreSQL with pgvector extension for semantic search on card text

### Key Technical Considerations

- **Memory constraints**: The cards.json file is too large to load entirely into memory
- **Batch processing**: Database inserts should be batched (typical batch size: 500-2000 records)
- **JSONB indexing**: PostgreSQL GIN indexes on JSONB columns enable efficient queries on nested JSON data
- **Stream parsing**: Use streaming JSON parsers (Jackson streaming API for Java) to process one card at a time

## Database Schema Recommendations

When implementing the schema, consider:

```sql
CREATE TABLE cards (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    mana_cost VARCHAR(50),
    cmc DECIMAL,
    type_line VARCHAR(255),
    oracle_text TEXT,
    colors TEXT[],
    color_identity TEXT[],
    rarity VARCHAR(20),
    set_code VARCHAR(10),
    released_at DATE,
    data JSONB,  -- Full card JSON for flexibility
    created_at TIMESTAMP DEFAULT NOW()
);

-- Essential indexes
CREATE INDEX idx_cards_name ON cards(name);
CREATE INDEX idx_cards_type ON cards(type_line);
CREATE INDEX idx_cards_set ON cards(set_code);
CREATE INDEX idx_cards_data_gin ON cards USING GIN(data);
```

For vector search (requires pgvector extension):
```sql
CREATE EXTENSION vector;
ALTER TABLE cards ADD COLUMN embedding vector(1536);  -- Adjust dimension as needed
CREATE INDEX ON cards USING ivfflat (embedding vector_cosine_ops);
```

## Common Patterns

### Loading Large JSON Files

Always use streaming approaches:
- **Java**: Jackson JsonParser with streaming API
- **Python**: `ijson` library or line-by-line processing
- **PostgreSQL COPY**: Fastest bulk load option (requires CSV conversion)

### Batch Operations

- Disable autocommit during bulk operations
- Use PreparedStatement.addBatch() and executeBatch()
- Commit every 1000-2000 records
- Drop indexes before bulk load, rebuild after

### Querying Nested JSON

PostgreSQL JSONB operators:
```sql
-- Find cards with specific color
SELECT * FROM cards WHERE data->'colors' ? 'R';

-- Find cards by set
SELECT * FROM cards WHERE data->>'set' = 'blb';

-- Complex queries on legalities
SELECT * FROM cards WHERE data->'legalities'->>'commander' = 'legal';
```
