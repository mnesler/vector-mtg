#!/bin/bash

# Scrape all 32 EDHREC categories one at a time
# This avoids the "broken pipe" issue by running separate processes

source venv/bin/activate

CATEGORIES=(
    "mono-white" "mono-blue" "mono-black" "mono-red" "mono-green"
    "azorius" "dimir" "rakdos" "gruul" "selesnya"
    "orzhov" "izzet" "golgari" "boros" "simic"
    "naya" "bant" "abzan" "sultai" "esper"
    "jeskai" "mardu" "temur" "jund" "five-color"
    "colorless" "partner" "no-blue" "no-white" "no-black"
    "no-red" "no-green"
)

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="edhrec_combos_detailed_${TIMESTAMP}"
mkdir -p "$OUTPUT_DIR"

echo "Starting scrape of all 32 categories"
echo "Output directory: $OUTPUT_DIR"
echo "=================================="

for i in "${!CATEGORIES[@]}"; do
    CATEGORY="${CATEGORIES[$i]}"
    echo ""
    echo "[$((i+1))/32] Scraping: $CATEGORY"
    
    python scripts/scrape_edhrec_combos_v2.py \
        --detailed \
        --categories "$CATEGORY" \
        --no-fetch-card-data \
        --output-dir "$OUTPUT_DIR" \
        --scroll-delay 2.0
    
    if [ $? -eq 0 ]; then
        echo "✓ $CATEGORY completed successfully"
    else
        echo "✗ $CATEGORY failed (will continue with next category)"
    fi
    
    # Small delay between categories
    sleep 2
done

echo ""
echo "=================================="
echo "Scraping complete! Output: $OUTPUT_DIR"
echo ""
echo "Next step: Enrich with card data"
echo "  python scripts/enrich_combos_with_card_data.py $OUTPUT_DIR/*.json --delay=0.5"
