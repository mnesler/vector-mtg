#!/bin/bash
# Run search test cases and display unique results

set -e

cd "$(dirname "$0")/.."
source venv/bin/activate

echo "=================================="
echo "SEARCH TEST SUITE"
echo "=================================="
echo ""

# Function to run semantic search and deduplicate
run_semantic() {
    local query="$1"
    echo "Query: $query"
    echo "----------------------------------------"
    python -c "
import sys
sys.path.insert(0, 'scripts')
from tests.test_search_fixtures import run_semantic_search

results = run_semantic_search('$query', 20)
seen = set()
for r in results:
    if r['name'] not in seen:
        seen.add(r['name'])
        sim = r['similarity']
        colors = r.get('colors', [])
        color_str = ''.join(colors) if colors else 'C'
        print(f\"  {r['name']:40s} [{color_str:5s}] {sim:.3f}\")
        if len(seen) >= 10:
            break
"
    echo ""
}

# Function to run keyword search and deduplicate
run_keyword() {
    local query="$1"
    echo "Query: $query"
    echo "----------------------------------------"
    python -c "
import sys
sys.path.insert(0, 'scripts')
from tests.test_search_fixtures import run_keyword_search

results = run_keyword_search('$query', 20)
seen = set()
for r in results:
    if r['name'] not in seen:
        seen.add(r['name'])
        colors = r.get('colors', [])
        color_str = ''.join(colors) if colors else 'C'
        print(f\"  {r['name']:40s} [{color_str:5s}]\")
        if len(seen) >= 10:
            break
"
    echo ""
}

echo "KEYWORD SEARCH TESTS"
echo "=================================="
echo ""

run_keyword "Lightning Bolt"
run_keyword "destroy target creature"
run_keyword "draw a card"

echo ""
echo "SEMANTIC SEARCH TESTS"
echo "=================================="
echo ""

run_semantic "counterspells"
run_semantic "red spells that deal damage"
run_semantic "cards that search for lands"
run_semantic "creatures with flying"
run_semantic "cards that remove creatures"

echo "=================================="
echo "TESTS COMPLETE"
echo "=================================="
