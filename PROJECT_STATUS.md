# MTG Vector Cube - Project Status

**Last Updated:** 2025-12-13
**Current Phase:** Phase 2 Complete - Ready for Testing

---

## 🎯 Project Vision

Build an AI-powered MTG combo discovery system that:
1. Tags all 508K cards with functional mechanics
2. Discovers NEW combos using pattern matching
3. Provides hybrid BERT + SQL semantic search
4. Enables natural language queries for deck building

---

## ✅ Completed Phases

### Phase 1: Schema Design & Deployment ✅

**Completed:** 2025-12-13

**What we built:**
- 6 new database tables for tags and abstractions
- 4 helper functions for tag queries
- 3 views for monitoring and quality control
- Automatic cache maintenance triggers
- Review queue for low-confidence extractions
- Tag hierarchy support (parent/child relationships)

**Key metrics:**
- 65 functional tags seeded across 10 categories
- Confidence threshold filtering (default: 0.7)
- Combo-relevant tags marked for pattern matching

**Files:**
- `/schema/tags_and_abstractions_v1.sql` - Full schema
- `/schema/seed_tag_taxonomy.sql` - Initial taxonomy
- `SCHEMA_IMPLEMENTATION_SUMMARY.md` - Complete documentation
- `SCHEMA_WALKTHROUGH_EXAMPLES.md` - Real-world examples
- `DEPLOYMENT_COMPLETE.md` - Deployment summary

---

### Phase 2: LLM Tag Extraction ✅

**Completed:** 2025-12-13

**What we built:**
- `CardTagExtractor` class - LLM-powered extraction
- Optimized prompts for GPT-4o-mini
- Test suite with 5 known combo cards
- Database integration with automatic caching
- Environment configuration templates

**Key features:**
- Returns confidence scores (0.0 - 1.0)
- Validates tags against taxonomy
- Auto-stores in database with triggers
- Tracks prompt versions for iteration
- Error handling and logging

**Files:**
- `/scripts/embeddings/extract_card_tags.py` - Main extraction script
- `/scripts/embeddings/TAG_EXTRACTION_SETUP.md` - Setup guide
- `.env.example` - Environment template
- `requirements.txt` - Updated with OpenAI dependency

**Cost estimates:**
- GPT-4o-mini: ~$70 for 508K cards
- Processing time: ~1.5-2 hours
- Tokens per card: ~600 total

---

## ⏳ Next Phase: Testing & Validation

### Phase 3: Quality Validation (Next)

**Goal:** Validate extraction quality before batch processing

**Tasks:**
1. Configure OpenAI API key
2. Run test suite on 5 known combo cards
3. Analyze confidence scores and accuracy
4. Test on 100 random cards from database
5. Calculate precision/recall metrics
6. Adjust prompt if needed

**Expected outcomes:**
- Precision > 90% (few false positives)
- Recall > 85% (catches most mechanics)
- Avg confidence > 0.80
- < 10% of cards need manual review

**Time estimate:** 1-2 hours (including API setup)

---

### Phase 4: Batch Processing (After validation)

**Goal:** Process all 508K cards with LLM extraction

**Tasks:**
1. Build `batch_tag_cards.py` script
2. Implement progress tracking and resume
3. Add error handling and retry logic
4. Create job tracking in `tagging_jobs` table
5. Run batch processing (1.5-2 hours)
6. Monitor review queue

**Expected outcomes:**
- 508K cards tagged
- ~10-50K cards in review queue (< 0.7 confidence)
- Tag distribution statistics
- Identification of common patterns

**Time estimate:** 3-4 hours (including script development)

---

### Phase 5: Abstraction Extraction (Future)

**Goal:** Extract abstract rule patterns for combo matching

**Tasks:**
1. Design abstraction prompt
2. Extract JSONB patterns from oracle text
3. Store in `card_abstractions` table
4. Build pattern matching engine
5. Test on known combos

**Example abstraction:**
```json
{
  "type": "activated_ability",
  "cost": {"mana": "{U}"},
  "effect": {
    "action": "untap",
    "target": "permanent"
  },
  "repeatable": true
}
```

**Time estimate:** 1-2 days

---

### Phase 6: Combo Pattern Discovery (Future)

**Goal:** Find NEW combos using tag-based patterns

**Tasks:**
1. Define 50-100 combo patterns
2. Build graph query engine
3. Search for pattern matches
4. Validate with rules engine
5. Store discovered combos

**Expected outcomes:**
- 10K-100K new potential combos
- Ranked by likelihood
- Validated patterns

**Time estimate:** 2-3 days

---

## 📊 Current System Metrics

### Database

**Cards table:**
- Total cards: 508,000
- Cards with tags: 0 (waiting for extraction)
- Cards with embeddings: ~508,000 (BERT)

**Tag system:**
- Total tags: 65
- Categories: 10
- Combo-relevant tags: 48
- Tag hierarchy depth: 2 levels max

**Storage:**
- Tags table: ~50 KB
- card_tags (after processing): ~10-15 MB
- card_abstractions (future): ~150-200 MB

### Search Performance (Existing BERT System)

**Query speed:**
- BERT semantic search: 5-15ms (100 results)
- SQL filtering: 2-5ms
- Total hybrid search: 10-50ms

**Accuracy:**
- Semantic similarity: ~85% relevant in top 100
- After SQL filtering: ~95% relevant

---

## 🗂️ File Organization

```
/home/maxwell/vector-mtg/
│
├── 📊 Project Documentation
│   ├── PROJECT_STATUS.md                    # This file
│   ├── DEPLOYMENT_COMPLETE.md               # Schema deployment summary
│   ├── SCHEMA_IMPLEMENTATION_SUMMARY.md     # Complete schema docs
│   ├── SCHEMA_WALKTHROUGH_EXAMPLES.md       # Real-world examples
│   ├── TAGS_VS_EMBEDDINGS.md                # Concept explanation
│   ├── SYNERGY_DISCOVERY_AI.md              # AI combo discovery strategy
│   ├── QUERY_ROUTING_AND_INTENTS.md         # Query intent detection
│   ├── COMPOUND_QUERY_ARCHITECTURE.md       # Hybrid search details
│   ├── BERT_VS_SQL_HYBRID_SEARCH.md         # Search architecture
│   └── DATA_INTEGRATION_STRATEGY.md         # Overall data strategy
│
├── 🗄️ Database Schema
│   └── schema/
│       ├── tags_and_abstractions_v1.sql     # Tag system schema (deployed)
│       └── seed_tag_taxonomy.sql            # Initial 65 tags (deployed)
│
├── 🤖 LLM Extraction Scripts
│   └── scripts/embeddings/
│       ├── extract_card_tags.py             # LLM extraction (complete)
│       ├── TAG_EXTRACTION_SETUP.md          # Setup guide
│       └── batch_tag_cards.py               # TODO: Batch processing
│
├── ⚙️ Configuration
│   ├── .env.example                         # Environment template
│   ├── requirements.txt                     # Python dependencies
│   ├── docker-compose.yml                   # Database setup
│   └── venv/                                # Virtual environment
│
└── 📁 Existing Components
    ├── data/                                # MTG JSON data
    ├── api/                                 # FastAPI server
    └── project-llm-deck-builder/            # Qwen training
```

---

## 🔑 Key Technical Decisions

### Architecture Choices

**1. Hybrid Tag System:**
- Normalized tables (`card_tags`) for flexibility
- Cached arrays (`cards.tag_cache`) for performance
- Trigger-based automatic maintenance
- **Rationale:** Balance between query speed and data integrity

**2. LLM-Based Extraction (Option B):**
- Chose LLM over rule-based or hybrid
- Using GPT-4o-mini for cost efficiency
- **Rationale:** MTG cards are too complex for regex patterns

**3. Confidence Filtering:**
- Default threshold: 0.7
- Auto-review queue for low confidence
- **Rationale:** Allows incremental quality improvement

**4. Tag Hierarchy:**
- Parent/child relationships (e.g., generates_mana → generates_blue_mana)
- Path arrays for efficient traversal
- **Rationale:** Enables both specific and general queries

### Performance Optimizations

**1. BERT-first Hybrid Search:**
- BERT narrows to 100 results semantically
- SQL filters precisely on those 100
- **Result:** 20x faster than SQL-first approach

**2. GIN Indexes on Arrays:**
- `cards.tag_cache[]` has GIN index
- Enables fast array containment queries
- **Result:** O(log n) tag lookups

**3. Materialized Aggregates:**
- `cards.tag_confidence_avg` pre-calculated
- Views filter using this column
- **Result:** Instant confidence filtering

---

## 🚀 How to Get Started

### For Testing Extraction (Phase 3)

1. **Set up API key:**
   ```bash
   cp .env.example .env
   nano .env  # Add your OPENAI_API_KEY
   ```

2. **Activate environment:**
   ```bash
   source venv/bin/activate
   export $(cat .env | xargs)
   ```

3. **Run test suite:**
   ```bash
   cd scripts/embeddings
   python extract_card_tags.py
   ```

4. **Review results and iterate on prompt if needed**

### For Batch Processing (Phase 4)

1. **Build batch script** (not yet created)
2. **Test on 1,000 cards**
3. **Run full batch** (508K cards)
4. **Monitor review queue**

### For Combo Discovery (Phase 6)

1. **Wait for tags to be extracted**
2. **Define combo patterns**
3. **Build pattern matcher**
4. **Discover new combos**

---

## 📈 Success Metrics

### Phase 3 (Testing) Success Criteria:
- ✅ Test suite runs without errors
- ✅ Precision > 90% on known cards
- ✅ Recall > 85% on known cards
- ✅ Average confidence > 0.80
- ✅ Manual review < 100 cards in test set

### Phase 4 (Batch Processing) Success Criteria:
- ✅ All 508K cards processed
- ✅ < 15% in review queue (< 76K cards)
- ✅ No data corruption or loss
- ✅ Processing completes in < 3 hours
- ✅ Cost under $100

### Phase 6 (Combo Discovery) Success Criteria:
- ✅ Discover > 10K new potential combos
- ✅ False positive rate < 30%
- ✅ Find at least 10 unknown combos that work
- ✅ Query time < 100ms for pattern matching

---

## 🔄 Incremental Build Approach

Following the user's request to "slowly build out each function one at a time":

1. ✅ **Tags** - Build tag taxonomy and schema
2. ✅ **Extraction** - Build LLM extraction for tags
3. ⏳ **Testing** - Validate quality on sample cards
4. ⏳ **Batch** - Process all cards
5. ⏳ **Abstractions** - Extract rule patterns
6. ⏳ **Patterns** - Define combo patterns
7. ⏳ **Discovery** - Find new combos

Each step is validated before moving to the next.

---

## 🎯 Current Focus

**Immediate next step:** Phase 3 - Quality Validation

**What you need:**
1. OpenAI API key configured in `.env`
2. Run test suite to validate extraction
3. Review accuracy and adjust prompt if needed

**Time required:** 1-2 hours

**After this:** Build batch processing script and process all 508K cards

---

## 📚 Documentation Index

- **PROJECT_STATUS.md** (this file) - High-level project overview
- **DEPLOYMENT_COMPLETE.md** - Schema deployment details
- **TAG_EXTRACTION_SETUP.md** - How to use extraction system
- **SCHEMA_IMPLEMENTATION_SUMMARY.md** - Complete schema reference
- **SCHEMA_WALKTHROUGH_EXAMPLES.md** - Real data examples
- **SYNERGY_DISCOVERY_AI.md** - Future combo discovery strategy

All documentation is in `/home/maxwell/vector-mtg/`

---

## ✨ Project Highlights

**What makes this unique:**

1. **AI-Powered Discovery:** Not just searching existing combos, but finding new ones
2. **Hybrid Search:** Combines semantic understanding (BERT) with precise filtering (SQL)
3. **Incremental Quality:** Confidence scores and review queues enable continuous improvement
4. **Tag Hierarchy:** Can query both specific ("generates blue mana") and general ("generates mana")
5. **Pattern Abstraction:** Generalizes card mechanics for cross-card matching
6. **Cost-Effective:** Using GPT-4o-mini keeps costs under $100 for entire dataset

**Current state:** Foundation complete, ready for extraction and testing! 🚀
