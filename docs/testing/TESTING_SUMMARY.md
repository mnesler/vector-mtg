# Embedding Testing Tools - Summary

## What I Created For You

I've built a comprehensive testing suite to validate your embedding quality and determine if similarity scores are accurate enough.

### New Files

1. **`scripts/test_embedding_quality.py`** - Main testing tool
   - Comprehensive benchmark suite with 8 test categories
   - Validates precision, recall, and similarity thresholds
   - Interactive mode for custom queries
   - Compares full vs oracle-only embeddings

2. **`scripts/visualize_embedding_quality.py`** - Visual analyzer
   - ASCII histograms of similarity distributions
   - Valid vs invalid result comparison
   - Threshold optimization visualization

3. **`EMBEDDING_TESTING_GUIDE.md`** - Complete documentation
   - Detailed explanation of similarity scores
   - Interpretation guidelines
   - Troubleshooting and optimization tips

4. **`QUICK_EMBEDDING_TEST.md`** - Quick reference
   - TL;DR commands and benchmarks
   - Score interpretation cheat sheet
   - Common fixes

## Quick Start

```bash
# Step 1: Generate embeddings (if not done yet)
python scripts/embeddings/generate_embeddings_dual.py

# Step 2: Run quality benchmark
python scripts/test_embedding_quality.py --benchmark

# Step 3: Check if results are good
# Look for:
#   - Tests Passed: >80%
#   - Average Precision: >70%
#   - Mean Valid Similarity: >0.35
```

## How to Validate Your Embeddings

### The Big Question: Are My Similarity Scores Accurate?

Run this command:
```bash
python scripts/test_embedding_quality.py --benchmark
```

**You'll see:**
- 8 test cases covering different query types
- Precision % (how many results are actually relevant)
- Pass/Fail for each category
- Similarity score distributions

**Good results look like:**
```
BENCHMARK SUMMARY
==========================================
Tests Passed: 7/8 (87.5%)
Average Precision: 76.3%

Valid Results Similarity Distribution:
  Mean: 0.428
  Median: 0.412
```

If you see these numbers, your embeddings are working well!

### Understanding Similarity Scores

Don't worry if scores seem "low" - context matters:

| Query Type | Expected Score | Example |
|------------|---------------|---------|
| Exact card name | 0.85+ | "Lightning Bolt" → Lightning Bolt |
| Direct ability | 0.60-0.80 | "flying" → Flying creatures |
| Semantic archetype | 0.40-0.60 | "counterspells" → Counter magic |
| Natural language | 0.30-0.50 | "cards that remove creatures" |
| Complex queries | 0.25-0.40 | "red instant dealing 3 damage" |

**Key insight**: A score of 0.35 for a complex query like "board wipes" with relevant results is excellent!

## Common Testing Scenarios

### Scenario 1: "I want to know if my embeddings are good enough"
```bash
python scripts/test_embedding_quality.py --benchmark
```
Look for >70% precision and >80% tests passed.

### Scenario 2: "What threshold should I use in my API?"
```bash
python scripts/test_embedding_quality.py --threshold
```
Typical recommendation: 0.30 (good balance) or 0.35 (higher quality)

### Scenario 3: "Are these search results relevant?"
```bash
python scripts/test_embedding_quality.py --query "your search query"
```
Check if top 5-10 results match your expectations.

### Scenario 4: "Should I use full embedding or oracle-only?"
```bash
python scripts/test_embedding_quality.py --compare
```
- Full embedding: General card search
- Oracle-only: Matching specific abilities

### Scenario 5: "Visualize the score distribution"
```bash
python scripts/visualize_embedding_quality.py --query "counterspells"
python scripts/visualize_embedding_quality.py --distribution
```
See ASCII histograms of similarity scores.

## Test Categories Included

The benchmark tests these realistic MTG search scenarios:

1. **Exact Match** - "Lightning Bolt" (should score 0.85+)
2. **Removal** - "destroy target creature" (0.35+ with creatures filtered)
3. **Counterspells** - "counterspells that cost 2 mana" (0.30+ blue instants)
4. **Burn** - "red instant that deals 3 damage" (0.30+ red damage)
5. **Flying** - "creatures with flying" (0.35+ with flying keyword)
6. **Card Draw** - "cards that draw cards" (0.30+ with draw effects)
7. **Ramp** - "ramp spells that search for lands" (0.25+ green ramp)
8. **Planeswalker Removal** - (0.25+ removal that hits planeswalkers)

## Improving Your Results

### If Precision is Low (<50%)

**Problem**: Too many irrelevant results

**Solutions**:
1. Increase similarity threshold: `results = [r for r in results if r['similarity'] >= 0.35]`
2. Add post-processing filters: type, color, CMC
3. Use oracle-only embeddings for ability matching
4. Upgrade to better model (`all-mpnet-base-v2`)

### If Similarity Scores Are Too Low

**Problem**: Relevant cards scoring <0.30

**Solutions**:
1. **This might be normal!** Check if results are still relevant
2. Upgrade embedding model to `all-mpnet-base-v2`
3. Rephrase queries to be more descriptive
4. Lower your threshold expectations for complex queries

### If Results Are Inconsistent

**Problem**: Similar queries return different quality

**Solutions**:
1. Establish baseline: `python scripts/test_embedding_quality.py --benchmark > baseline.txt`
2. Test after changes and compare
3. Use hybrid search (semantic + keyword filters)

## Model Comparison

Current model: **all-MiniLM-L6-v2** (384 dims, fast, good quality)

To upgrade:
1. Edit `scripts/embeddings/generate_embeddings_dual.py`:
   ```python
   MODEL_NAME = 'all-mpnet-base-v2'
   EMBEDDING_DIM = 768
   ```

2. Edit `scripts/api/embedding_service.py`:
   ```python
   def get_embedding_service(model_name: str = 'all-mpnet-base-v2')
   ```

3. Alter database columns (768 dims)

4. Regenerate all embeddings

**Expected improvement**: +0.05 to +0.10 on similarity scores, +5-10% precision

## Example Output

```
$ python scripts/test_embedding_quality.py --benchmark

Test: destroy target creature
Category: Removal
==========================================

Results: 20 unique cards
Valid: 16 (80.0% precision)
Expected: ≥10 valid results - ✓ PASS

✓ Valid Results (Top 10):
  1. Murder              [1BB] 0.556
  2. Doom Blade          [1B]  0.524
  3. Go for the Throat   [1B]  0.498

BENCHMARK SUMMARY
==========================================
Tests Passed: 7/8 (87.5%)
Average Precision: 76.3%

Recommendation:
  - Threshold 0.30+: Good balance of precision and recall
```

## Next Steps

1. **Run the benchmark**: `python scripts/test_embedding_quality.py --benchmark`
2. **Check if results meet your needs** (>70% precision, >80% pass rate)
3. **Determine your threshold**: `python scripts/test_embedding_quality.py --threshold`
4. **Test with your real queries**: `python scripts/test_embedding_quality.py --query "your query"`
5. **Document baseline for future testing**

## Files Reference

- **`EMBEDDING_TESTING_GUIDE.md`** - Full documentation (read this for deep understanding)
- **`QUICK_EMBEDDING_TEST.md`** - Quick reference card (bookmark this)
- **`scripts/test_embedding_quality.py`** - Main testing tool
- **`scripts/visualize_embedding_quality.py`** - Visualization tool

## Questions to Answer

✅ **Are my embeddings accurate enough?**
→ Run benchmark, check if precision >70%

✅ **What threshold should I use?**
→ Run threshold analysis, typically 0.30-0.35

✅ **Why are scores so low?**
→ Check if results are still relevant; low scores can be OK for complex queries

✅ **Should I upgrade my model?**
→ Run comparison, upgrade if you need +5-10% better precision

✅ **How do I test specific queries?**
→ Use `--query` or `--interactive` mode

## Pro Tips

1. **Don't chase high scores** - Focus on relevance of top results
2. **Use hybrid search** - Combine semantic search with filters
3. **Test with real use cases** - Benchmark is baseline, test your actual queries
4. **Document your thresholds** - Know what scores mean for your UI
5. **Regression test** - Re-run benchmark after changes

## Support

For issues or questions:
- Check `EMBEDDING_TESTING_GUIDE.md` for detailed troubleshooting
- Run interactive mode to experiment: `python scripts/test_embedding_quality.py --interactive`
- Compare with existing test cases in the benchmark

Good luck! 🎯
