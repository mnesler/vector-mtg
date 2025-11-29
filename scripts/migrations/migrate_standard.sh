#!/bin/bash

# Migrate Standard cards in batches of 100
BATCH_SIZE=100
TOTAL=$(docker exec vector-mtg-postgres psql -U postgres -d vector_mtg -t -c "SELECT COUNT(*) FROM cards WHERE set_code IN ('woe', 'lci', 'mkm', 'otj', 'blb', 'dsk', 'fdn', 'dft', 'tdm', 'fin', 'eoe', 'spm');" | tr -d ' ')

echo "Found $TOTAL Standard cards to migrate"
echo "Migrating in batches of $BATCH_SIZE..."
echo ""

START_TIME=$(date +%s)
OFFSET=0

while [ $OFFSET -lt $TOTAL ]; do
    BATCH_START=$(date +%s)

    # Insert batch
    docker exec vector-mtg-postgres psql -U postgres -d vector_mtg -c "
        INSERT INTO vector_mtg_standard.cards
        SELECT * FROM cards
        WHERE set_code IN ('woe', 'lci', 'mkm', 'otj', 'blb', 'dsk', 'fdn', 'dft', 'tdm', 'fin', 'eoe', 'spm')
        ORDER BY id
        LIMIT $BATCH_SIZE OFFSET $OFFSET
    " > /dev/null 2>&1

    BATCH_END=$(date +%s)
    BATCH_TIME=$((BATCH_END - BATCH_START))

    OFFSET=$((OFFSET + BATCH_SIZE))
    PROGRESS=$((OFFSET < TOTAL ? OFFSET : TOTAL))

    ELAPSED=$((BATCH_END - START_TIME))
    CARDS_PER_SEC=$((ELAPSED > 0 ? PROGRESS / ELAPSED : 0))
    PERCENT=$((PROGRESS * 100 / TOTAL))

    # Calculate ETA
    if [ $PROGRESS -lt $TOTAL ]; then
        REMAINING=$((TOTAL - PROGRESS))
        ETA=$((CARDS_PER_SEC > 0 ? REMAINING / CARDS_PER_SEC : 0))
        ETA_STR="ETA: ${ETA}s"
    else
        ETA_STR="Complete!"
    fi

    BATCH_NUM=$((OFFSET / BATCH_SIZE))
    TOTAL_BATCHES=$(((TOTAL + BATCH_SIZE - 1) / BATCH_SIZE))

    printf "Batch %d/%d: Inserted %d/%d cards (%d%%) | %d cards/sec | Batch time: %ds | %s\n" \
        $BATCH_NUM $TOTAL_BATCHES $PROGRESS $TOTAL $PERCENT $CARDS_PER_SEC $BATCH_TIME "$ETA_STR"
done

# Verify
FINAL_COUNT=$(docker exec vector-mtg-postgres psql -U postgres -d vector_mtg_standard -t -c "SELECT COUNT(*) FROM cards;" | tr -d ' ')

echo ""
echo "✓ Migration complete!"
echo "  Total cards migrated: $FINAL_COUNT"
END_TIME=$(date +%s)
TOTAL_TIME=$((END_TIME - START_TIME))
echo "  Total time: ${TOTAL_TIME}s"
