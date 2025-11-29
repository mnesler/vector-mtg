# Database Migrations

This directory contains all database schema changes after the initial schema creation.

## Migration Naming Convention

Migrations should be named: `YYYYMMDD_HHMM_description.sql`

Example: `20251122_1430_add_card_power_index.sql`

## Migration Template

```sql
-- Migration: [Brief description]
-- Created: YYYY-MM-DD
-- Author: [Your name]

BEGIN;

-- Add your schema changes here
-- Example:
-- ALTER TABLE cards ADD COLUMN IF NOT EXISTS new_field TEXT;
-- CREATE INDEX IF NOT EXISTS idx_cards_new_field ON cards(new_field);

COMMIT;

-- Rollback (optional, document how to undo this migration)
-- BEGIN;
-- DROP INDEX IF EXISTS idx_cards_new_field;
-- ALTER TABLE cards DROP COLUMN IF EXISTS new_field;
-- COMMIT;
```

## Running Migrations

```bash
# Apply a migration
psql -U postgres -d vector_mtg -f migrations/20251122_1430_add_card_power_index.sql

# Or via Docker
docker exec -i vector-mtg-postgres psql -U postgres -d vector_mtg < migrations/20251122_1430_add_card_power_index.sql
```

## Migration Best Practices

1. **Always use IF NOT EXISTS / IF EXISTS** - Makes migrations idempotent (safe to run multiple times)
2. **Use transactions (BEGIN/COMMIT)** - Ensures atomicity
3. **Document rollback steps** - Makes it easy to undo changes
4. **Test migrations** - Test on a copy of production data first
5. **One logical change per migration** - Easier to track and rollback
6. **Never modify existing migrations** - Once applied, create a new migration instead

## Example Migration

See `example_migration.sql` in this directory.
