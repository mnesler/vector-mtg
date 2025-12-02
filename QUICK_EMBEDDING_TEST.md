# Quick Embedding Test Reference

## TL;DR - Is My Embedding Quality Good?

```bash
# Run this one command:
python scripts/test_embedding_quality.py --benchmark
```

**Look for:**
- ✅ Tests Passed: **>80%** (7/8 or better)
- ✅ Average Precision: **>70%**
- ✅ Valid Results Mean Similarity: **>0.35**

If you see these numbers, your embeddings are working well! 

## Score Quick Reference

| Score Range | Quality | What It Means |
|------------|---------|---------------|
| 0.85+ | Excellent | Nearly exact match |
| 0.60-0.85 | Very Good | Clearly related cards |
| 0.40-0.60 | Good | Related concepts |
| 0.30-0.40 | Acceptable | Loosely related (OK for complex queries) |
| <0.30 | Poor | Likely not relevant |

**Important**: Don't expect all queries to score >0.70! Complex natural language queries scoring 0.30-0.40 with relevant results are perfectly fine.

## Common Commands

```bash
# Test everything
python scripts/test_embedding_quality.py --all

# Just run benchmark
python scripts/test_embedding_quality.py --benchmark

# Find best threshold for filtering
python scripts/test_embedding_quality.py --threshold

# Test your own query
python scripts/test_embedding_quality.py --query "your search here"

# Interactive testing
python scripts/test_embedding_quality.py --interactive
```

## Reading Benchmark Output

```
Test: destroy target creature
Category: Removal
==========================================

Results: 20 unique cards
Valid: 16 (80.0% precision)        ← Want >70%
Expected: ≥10 valid results - ✓ PASS  ← PASS is good

Similarity Scores:
  Mean: 0.412                     ← Want >0.35
  Median: 0.405
  Range: 0.298 - 0.556           ← Check spread

✓ Valid Results (Top 10):
  1. Murder              [1BB] 0.556  ← Top results scoring well
  2. Doom Blade          [1B]  0.524
  3. Go for the Throat   [1B]  0.498

✗ Invalid Results:
  1. Some Card           [2B]  0.312  ← Invalid results scoring lower
     → Missing keywords: destroy
```

**Good signs:**
- Valid results score higher than invalid ones
- Top 5 results are actually relevant
- Precision >70%

**Red flags:**
- Valid and invalid results have similar scores
- Top results are irrelevant
- Precision <50%

## What Threshold Should I Use?

Run: `python scripts/test_embedding_quality.py --threshold`

**Typical recommendation:**
- **0.30**: Balanced (recommended starting point)
- **0.35**: Higher quality, may miss some results
- **0.40**: Very strict, significant recall loss

In your API/UI:
```python
# Filter results by threshold
results = [r for r in results if r['similarity'] >= 0.30]
```

## Quick Fixes

### Scores Too Low
```bash
# Upgrade to better model (edit generate_embeddings_dual.py first)
# Change MODEL_NAME = 'all-mpnet-base-v2'
python scripts/embeddings/generate_embeddings_dual.py
```

### Too Many Irrelevant Results
```python
# 1. Increase threshold
results = [r for r in results if r['similarity'] >= 0.35]

# 2. Add filters
results = [r for r in results if 'Instant' in r['type_line']]

# 3. Use oracle_embedding instead of full embedding
```

### Want to Compare Models
```bash
python scripts/test_embedding_quality.py --compare
```

## Baseline Expectations

### For `all-MiniLM-L6-v2` (default)
- Tests Passed: 7-8/8
- Precision: 70-80%
- Mean Valid Similarity: 0.38-0.45
- Exact name match: >0.85
- Ability match: 0.60-0.75
- Complex queries: 0.30-0.45

### For `all-mpnet-base-v2` (better quality)
- Tests Passed: 8/8
- Precision: 75-85%
- Mean Valid Similarity: 0.42-0.50
- Scores generally 0.05-0.10 higher

## Test Cases Included

The benchmark tests these query types:
1. ✓ Exact name match: "Lightning Bolt"
2. ✓ Removal: "destroy target creature"
3. ✓ Counterspells: "counterspells that cost 2 mana"
4. ✓ Burn: "red instant that deals 3 damage"
5. ✓ Flying: "creatures with flying"
6. ✓ Card draw: "cards that draw cards"
7. ✓ Ramp: "ramp spells that search for lands"
8. ✓ Planeswalker removal: "planeswalker removal"

## Real Example

```bash
$ python scripts/test_embedding_quality.py --query "blue counterspells"

Query: blue counterspells
Results: 15 unique cards

#   Name                          Type                Similarity
------------------------------------------------------------------------
1   Counterspell                  Instant             0.728
2   Cancel                        Instant             0.652
3   Negate                        Instant             0.618
4   Mana Leak                     Instant             0.594
5   Dissolve                      Instant             0.571

Similarity: mean=0.612, median=0.594, range=[0.312, 0.728]
```

**This is good!** Top results are all counterspells, similarity >0.55.

## When to Re-test

- ✓ After changing embedding model
- ✓ After modifying card data
- ✓ Before deploying to production
- ✓ When testing new query patterns
- ✓ Monthly/quarterly as part of QA

## Need More Detail?

See [EMBEDDING_TESTING_GUIDE.md](EMBEDDING_TESTING_GUIDE.md) for:
- Deep dive on similarity scores
- Model comparison guide
- Advanced tuning strategies
- Troubleshooting details
