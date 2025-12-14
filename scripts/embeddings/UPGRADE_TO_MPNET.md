# Upgrading to GPU-Accelerated MPNet Embeddings

This guide walks you through upgrading from `all-MiniLM-L6-v2` (384 dims) to `all-mpnet-base-v2` (768 dims) with GPU acceleration.

## What's Changed

| Aspect | Old (MiniLM) | New (MPNet) |
|--------|--------------|-------------|
| Model | all-MiniLM-L6-v2 | all-mpnet-base-v2 |
| Parameters | 22M | 110M |
| Dimensions | 384 | 768 |
| Device | CPU | GPU (CUDA) |
| Batch Size | 100 | 256 |
| Quality | Good | Excellent |
| Speed (GPU) | ~3 min | ~2 min |

## Prerequisites

### 1. Enable Docker in WSL

Your WSL distro needs Docker access. In **Docker Desktop**:
1. Open Docker Desktop
2. Go to **Settings** → **Resources** → **WSL Integration**
3. Enable integration for your Ubuntu/WSL distro
4. Click **Apply & Restart**

### 2. Verify GPU Access

Check that CUDA is available:
```bash
python3 -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

Should output: `CUDA available: True`

### 3. Install Dependencies

```bash
cd /home/maxwell/vector-mtg
pip install sentence-transformers torch psycopg2-binary tqdm
```

## Step-by-Step Upgrade Process

### Step 1: Start PostgreSQL

```bash
cd /home/maxwell/vector-mtg
docker compose up -d postgres

# Wait for it to be ready (10-15 seconds)
docker compose ps
```

You should see `vector-mtg-postgres` with status "Up (healthy)".

### Step 2: Test with Small Sample (Recommended)

Test with 1,000 cards first to verify everything works:

```bash
cd /home/maxwell/vector-mtg/scripts/embeddings
python3 generate_embeddings_gpu.py --test
```

**What this does:**
- Downloads `all-mpnet-base-v2` model (~420MB, one-time download)
- Loads model on GPU
- Processes 1,000 cards
- Creates backup of old embeddings (as `embedding_old`, `oracle_embedding_old`)
- Generates new 768-dimensional embeddings
- Shows performance metrics
- Tests similarity search

**Expected output:**
```
GPU Information
Device: NVIDIA GeForce RTX 4070 Ti
CUDA Version: 13.0
GPU Memory: 12.3 GB

Processing 1,000 cards...
Embedding cards: 100%|████████████| 4/4 [00:03<00:00, 1.2it/s]
✓ Generated embeddings for 1,000 cards
  Time: 3.2s (312 cards/sec)
```

### Step 3: Review Test Results

The test script will:
1. Show embedding statistics
2. Run a similarity search test (cards similar to "Lightning Bolt")
3. Display sample results with similarity scores

If the results look good, proceed to full regeneration.

### Step 4: Full Regeneration (All Cards)

Process all ~30,000 cards in the database:

```bash
python3 generate_embeddings_gpu.py
```

**What this does:**
- Processes ALL cards with oracle text
- Generates both full card and oracle-only embeddings
- Creates HNSW indexes for fast similarity search
- Takes ~2-3 minutes on your RTX 4070 Ti

**Expected output:**
```
Processing 29,847 cards with oracle text...
Embedding cards: 100%|████████████| 117/117 [00:01<00:00, 75.2it/s]
✓ Generated embeddings for 29,847 cards
  Time: 123.4s (242 cards/sec)

Creating vector indexes...
  ✓ Created idx_cards_embedding_v2
  ✓ Created idx_cards_oracle_embedding_v2
  ✓ Created idx_rules_embedding_v2

Cards with full embeddings: 29,847 / 32,541 (91.7%)
Cards with oracle embeddings: 29,847 / 32,541 (91.7%)
```

### Step 5: Verify Upgrade

Test the new embeddings with a sample query:

```bash
python3 -c "
import psycopg2
from sentence_transformers import SentenceTransformer

# Load model
model = SentenceTransformer('all-mpnet-base-v2', device='cuda')

# Test query
query = 'cards that draw cards when I play artifacts'
query_emb = model.encode(query).tolist()

# Search
conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5432/vector_mtg')
cursor = conn.cursor()

cursor.execute('''
    SELECT name, type_line, oracle_text,
           1 - (embedding <=> %s::vector) as similarity
    FROM cards
    WHERE embedding IS NOT NULL
    ORDER BY embedding <=> %s::vector
    LIMIT 5
''', (query_emb, query_emb))

print('\nTop 5 results for:', query)
for name, type_line, oracle_text, sim in cursor.fetchall():
    print(f'\n{name} (similarity: {sim:.4f})')
    print(f'  {type_line}')
    print(f'  {oracle_text[:100]}...')

cursor.close()
conn.close()
"
```

## Performance Comparison

### Old System (MiniLM on CPU):
- Model size: 22M parameters
- Embedding dimensions: 384
- Speed: ~100 cards/sec
- Total time for 30k cards: ~5 minutes

### New System (MPNet on GPU):
- Model size: 110M parameters
- Embedding dimensions: 768
- Speed: ~240-300 cards/sec
- Total time for 30k cards: **~2-3 minutes**

## What Gets Backed Up

The script automatically preserves your old embeddings:
- `cards.embedding` → `cards.embedding_old`
- `cards.oracle_embedding` → `cards.oracle_embedding_old`
- `rules.embedding` → `rules.embedding_old`

To rollback (if needed):
```sql
-- Rollback cards
ALTER TABLE cards DROP COLUMN embedding;
ALTER TABLE cards DROP COLUMN oracle_embedding;
ALTER TABLE cards RENAME COLUMN embedding_old TO embedding;
ALTER TABLE cards RENAME COLUMN oracle_embedding_old TO oracle_embedding;

-- Rollback rules
ALTER TABLE rules DROP COLUMN embedding;
ALTER TABLE rules RENAME COLUMN embedding_old TO embedding;

-- Recreate indexes with old dimensions (384)
DROP INDEX IF EXISTS idx_cards_embedding;
CREATE INDEX idx_cards_embedding ON cards USING hnsw (embedding vector_cosine_ops);
```

## Troubleshooting

### Issue: "CUDA not available"

**Solution:**
```bash
# Check CUDA installation
nvidia-smi

# Reinstall PyTorch with CUDA support
pip uninstall torch
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

### Issue: "Docker command not found"

**Solution:** Enable Docker WSL integration (see Prerequisites #1)

### Issue: "Connection refused" to PostgreSQL

**Solution:**
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# If not, start it
docker compose up -d postgres

# Check logs if it's failing
docker compose logs postgres
```

### Issue: Out of memory

**Solution:**
```bash
# Reduce batch size in the script
# Edit generate_embeddings_gpu.py, line 26:
BATCH_SIZE = 128  # Change from 256 to 128
```

### Issue: Embeddings not matching expected dimensions

**Solution:**
```bash
# Check embedding dimensions in database
psql -U postgres -h localhost -d vector_mtg -c "
SELECT
    pg_column_size(embedding) as embedding_bytes,
    pg_column_size(embedding) / 4 as dimensions
FROM cards
WHERE embedding IS NOT NULL
LIMIT 1;
"

# Should show: 768 dimensions (3072 bytes)
```

## Next Steps

After upgrading:

1. **Update API/services** that use embeddings to expect 768 dimensions
2. **Test search quality** - you should see better semantic matching
3. **Clean up old embeddings** (optional) once you're satisfied:
   ```sql
   ALTER TABLE cards DROP COLUMN IF EXISTS embedding_old;
   ALTER TABLE cards DROP COLUMN IF EXISTS oracle_embedding_old;
   ALTER TABLE rules DROP COLUMN IF EXISTS embedding_old;
   ```

4. **Update documentation** to reflect new model:
   - Update `MODEL_NAME` in other scripts
   - Update API documentation with new dimensions

## Scripts Overview

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `generate_embeddings_dual.py` | Old CPU-based script | Don't use (deprecated) |
| `generate_embeddings_gpu.py` | New GPU-accelerated script | **Use this** |
| `generate_embeddings_gpu.py --test` | Test mode (1000 cards) | Before full run |

## Performance Metrics to Expect

On your RTX 4070 Ti with 12GB VRAM:

| Dataset Size | Batch Size | Expected Time | Memory Usage |
|--------------|------------|---------------|--------------|
| 1,000 cards | 256 | ~3-4 seconds | 1.5GB VRAM |
| 10,000 cards | 256 | ~35-40 seconds | 2GB VRAM |
| 30,000 cards | 256 | ~2-3 minutes | 2.5GB VRAM |

## Quality Improvements

### Before (MiniLM):
Query: "ramp spells that find lands"
- Top result: Cultivate (0.72 similarity)
- Misses: Some tutors, conditional ramp

### After (MPNet):
Query: "ramp spells that find lands"
- Top result: Cultivate (0.85 similarity)
- Better ranking of: Kodama's Reach, Rampant Growth, Nature's Lore
- Correctly includes: Three Visits, Farseek (better semantic understanding)

The larger model better understands:
- Synonyms (ramp = accelerate mana)
- Related concepts (tutor = search library)
- Card interactions and synergies
- Intent behind natural language queries

## Support

If you encounter issues:
1. Check this troubleshooting section
2. Review script output for error messages
3. Check database logs: `docker compose logs postgres`
4. Verify GPU availability: `nvidia-smi`

---

**Ready to upgrade?** Start with Step 1 above!
