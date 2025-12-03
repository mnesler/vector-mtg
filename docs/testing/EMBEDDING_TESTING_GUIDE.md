# Embedding Quality Testing Guide

This guide explains how to test the accuracy of your vector embeddings and determine if the matching percentages (similarity scores) are good enough for your use case.

## Quick Start

```bash
# 1. Make sure embeddings are generated
python scripts/embeddings/generate_embeddings_dual.py

# 2. Run the benchmark suite
python scripts/test_embedding_quality.py --benchmark

# 3. Analyze optimal similarity threshold
python scripts/test_embedding_quality.py --threshold

# 4. Compare different embedding approaches
python scripts/test_embedding_quality.py --compare

# 5. Run all tests
python scripts/test_embedding_quality.py --all
```

## Understanding Similarity Scores

### What is a Similarity Score?

The similarity score is a number between 0 and 1 that represents how semantically similar two pieces of text are:
- **1.0** = Identical meaning
- **0.8-1.0** = Extremely similar (near-exact matches)
- **0.6-0.8** = Very similar (clearly related)
- **0.4-0.6** = Moderately similar (related concepts)
- **0.2-0.4** = Somewhat similar (loosely related)
- **0.0-0.2** = Not similar (unrelated)

### Typical Scores for MTG Cards

Based on testing with the `all-MiniLM-L6-v2` model:

| Query Type | Expected Score | Example |
|------------|---------------|---------|
| Exact card name | 0.85+ | "Lightning Bolt" → Lightning Bolt (0.92) |
| Direct ability match | 0.60-0.80 | "flying" → Birds with flying (0.70) |
| Semantic archetype | 0.40-0.60 | "counterspells" → Counterspell (0.73), Cancel (0.52) |
| Natural language | 0.30-0.50 | "cards that remove creatures" → Murder (0.45) |
| Complex queries | 0.25-0.40 | "red instant that deals 3 damage" → Bolt (0.38) |

**Important**: Lower scores don't always mean bad results! For complex queries, 0.30-0.40 can still be highly relevant.

## Testing Tools

### 1. Benchmark Suite (`--benchmark`)

Runs a comprehensive suite of test cases covering:
- Exact name matching
- Ability matching (flying, counterspells, etc.)
- Archetype matching (burn, ramp, removal)
- Complex natural language queries

```bash
python scripts/test_embedding_quality.py --benchmark
```

**What to look for:**
- **Precision**: What % of results are actually relevant? Target: >70%
- **Recall**: Did we find enough relevant cards? Target: ≥5 per query
- **Similarity scores**: Are valid results scoring higher than invalid ones?

**Example Output:**
```
Test: destroy target creature
Category: Removal
Description: Should find creature removal spells
==========================================

Results: 20 unique cards
Valid: 16 (80.0% precision)
Expected: ≥10 valid results - ✓ PASS

Similarity Scores:
  Mean: 0.412
  Median: 0.405
  Range: 0.298 - 0.556

✓ Valid Results:
  1. Murder                     [1BB] 0.556
  2. Doom Blade                 [1B]  0.524
  3. Go for the Throat          [1B]  0.498
```

### 2. Threshold Analysis (`--threshold`)

Determines the optimal similarity threshold for filtering results.

```bash
python scripts/test_embedding_quality.py --threshold
```

This shows you what % of valid vs invalid results fall above different thresholds:

```
Threshold    Valid %      Invalid %    Precision
------------------------------------------------
0.20         95.2         78.3         54.9
0.25         88.7         52.1         63.0
0.30         76.5         31.2         71.0  ← Recommended
0.35         62.3         18.4         77.3
0.40         45.1         8.7          83.8
```

**Recommendation**:
- **0.30**: Good balance - keeps most valid results, filters most invalid ones
- **0.35**: Higher quality - may miss some valid results
- **0.40**: Very strict - significant loss of valid results

### 3. Embedding Approach Comparison (`--compare`)

Compares two embedding strategies:
1. **Full embedding**: Name + Type + Oracle Text + Keywords
2. **Oracle-only embedding**: Just the card text

```bash
python scripts/test_embedding_quality.py --compare
```

**When to use each:**
- **Full embedding**: General card search, finding similar cards overall
- **Oracle-only**: Matching specific abilities/mechanics regardless of card name

### 4. Custom Query Testing (`--query`)

Test your own queries to see if results are good:

```bash
python scripts/test_embedding_quality.py --query "board wipes that hit everything"
python scripts/test_embedding_quality.py --query "mana dorks"
python scripts/test_embedding_quality.py --query "cards that exile graveyards"
```

### 5. Interactive Mode (`--interactive`)

Drop into an interactive shell to test queries on the fly:

```bash
python scripts/test_embedding_quality.py --interactive
```

```
Query: black creature removal
Results for 'black creature removal':
#   Name                          Type                      Similarity
-------------------------------------------------------------------------
1   Murder                        Instant                   0.556
2   Doom Blade                    Instant                   0.524
3   Go for the Throat             Instant                   0.498
...
```

## Improving Embedding Quality

### If Similarity Scores Are Too Low

**Problem**: Queries return relevant cards but with low similarity scores (e.g., 0.20-0.30)

**Solutions**:

1. **Use a better model**: Upgrade from `all-MiniLM-L6-v2` to `all-mpnet-base-v2`
   ```python
   # In generate_embeddings_dual.py and embedding_service.py
   MODEL_NAME = 'all-mpnet-base-v2'  # Better quality, slower, 768 dims
   ```

2. **Adjust threshold expectations**: Lower scores might be normal for complex queries

3. **Improve query phrasing**: Use more descriptive queries
   - ❌ "board wipes"
   - ✅ "destroy all creatures"

### If Getting Irrelevant Results

**Problem**: Top results include cards that don't match the query intent

**Solutions**:

1. **Add post-processing filters**: Filter by type, color, CMC after semantic search
   ```python
   # Example: Only return instants/sorceries
   results = [r for r in results if 'Instant' in r['type_line'] or 'Sorcery' in r['type_line']]
   ```

2. **Use oracle-only embeddings**: Better for matching specific card text
   ```python
   semantic_search(query, use_oracle_embedding=True)
   ```

3. **Increase similarity threshold**: Filter out low-scoring results
   ```python
   results = [r for r in results if r['similarity'] >= 0.35]
   ```

4. **Fine-tune the model**: Train on MTG-specific data (advanced)

### If Results Are Inconsistent

**Problem**: Similar queries return very different results

**Solutions**:

1. **Normalize card data**: Ensure consistent formatting in oracle text

2. **Test with benchmark suite**: Establish baseline performance
   ```bash
   python scripts/test_embedding_quality.py --benchmark > baseline.txt
   # Make changes
   python scripts/test_embedding_quality.py --benchmark > after.txt
   diff baseline.txt after.txt
   ```

3. **Use hybrid search**: Combine semantic search with keyword filters

## Recommended Testing Workflow

### Initial Setup
1. Generate embeddings: `python scripts/embeddings/generate_embeddings_dual.py`
2. Run benchmark: `python scripts/test_embedding_quality.py --benchmark`
3. Analyze thresholds: `python scripts/test_embedding_quality.py --threshold`
4. Document baseline results

### Regular Testing
1. Test new query patterns: `python scripts/test_embedding_quality.py --query "your query"`
2. Check if results meet expectations
3. Adjust thresholds or add filters as needed

### Before Production
1. Run full test suite: `python scripts/test_embedding_quality.py --all`
2. Verify precision >70% across categories
3. Document similarity score thresholds for your UI
4. Add query examples to your documentation

## Advanced: Model Comparison

### Available Models

| Model | Dimensions | Speed | Quality | Use Case |
|-------|-----------|-------|---------|----------|
| all-MiniLM-L6-v2 | 384 | Fast | Good | Development, quick iteration |
| all-mpnet-base-v2 | 768 | Medium | Excellent | Production, best quality |
| all-MiniLM-L12-v2 | 384 | Medium | Very Good | Balance of speed & quality |

### Testing Different Models

1. Edit `generate_embeddings_dual.py`:
   ```python
   MODEL_NAME = 'all-mpnet-base-v2'
   EMBEDDING_DIM = 768
   ```

2. Regenerate embeddings (will take longer)

3. Run benchmarks and compare:
   ```bash
   python scripts/test_embedding_quality.py --benchmark > mpnet-results.txt
   ```

4. Compare similarity scores and precision

**Note**: Changing models requires:
- Altering embedding column dimensions in database
- Regenerating ALL embeddings
- Rebuilding indexes

## Interpreting Benchmark Results

### Good Results ✓
- Precision >70%
- Valid results score 0.05+ higher than invalid results
- Top result is relevant for >80% of queries
- Similarity scores are consistent across similar query types

### Needs Improvement ✗
- Precision <50%
- Valid and invalid results have similar similarity scores
- Top results are frequently irrelevant
- Wide variance in scores for similar queries

### Edge Cases (Expected)
- Token cards appear in "creature" searches (can filter these)
- Multiple printings of same card (deduplicate by name)
- MTG slang doesn't work well (use descriptive phrases instead)
- Very specific queries may have low scores but still good results

## Example Test Session

```bash
# Full workflow
$ python scripts/test_embedding_quality.py --all

# Output includes:
# 1. Benchmark results for 8 test categories
# 2. Precision and recall metrics
# 3. Similarity distribution analysis
# 4. Threshold recommendations
# 5. Embedding approach comparison

# Based on results, might see:
BENCHMARK SUMMARY
==========================================
Tests Passed: 7/8 (87.5%)
Average Precision: 76.3%

Valid Results Similarity Distribution:
  Mean: 0.428
  Median: 0.412
  Range: 0.254 - 0.923

Recommendation:
  - Threshold 0.30+: Good balance of precision and recall
  → Use this for your search API
```

## Troubleshooting

### "No embeddings to test"
Run: `python scripts/embeddings/generate_embeddings_dual.py`

### "Connection refused"
Start PostgreSQL: `docker-compose up -d`

### "Model not found"
First run downloads models (may take a few minutes)

### Very slow execution
- Use smaller model (`all-MiniLM-L6-v2`)
- Reduce batch size in scripts
- Index embeddings with HNSW

## Summary

**Key Takeaways:**

1. **Similarity scores context matters**: 0.30-0.40 can be excellent for complex queries
2. **Use the benchmark suite**: Establishes baseline and catches regressions
3. **Test with real queries**: Your actual use cases matter most
4. **Combine with filters**: Semantic search + filters = best results
5. **Document thresholds**: Know what scores mean for your application

**Quick Validation**:
```bash
# Is my embedding quality good enough?
python scripts/test_embedding_quality.py --benchmark

# If precision >70% and passed tests >80%, you're in good shape!
```
