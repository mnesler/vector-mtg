# Existing API Architecture Summary

**Date:** December 2, 2024  
**Purpose:** Foundation for building agentic conversational system

---

## Executive Summary

The vector-mtg system is a mature, production-ready MTG card search and rule classification engine with:
- **509,000+ cards** indexed with dual embeddings
- **FastAPI REST server** with 15+ endpoints
- **Hybrid search** combining keyword, semantic, and advanced filtering
- **Rule engine** for card classification and deck analysis
- **PostgreSQL + pgvector** for vector similarity search
- **Phi-3.5 mini LLM** for query parsing (4B parameters)
- **Sentence transformers** for embeddings (all-MiniLM-L6-v2)

---

## 1. Current API Endpoints

### Card Search Endpoints

| Endpoint | Method | Purpose | Key Features |
|----------|--------|---------|--------------|
| `/api/cards/search` | GET | Search by name or rule | Partial matching, rule filtering, playability filter |
| `/api/cards/keyword` | GET | Text-based keyword search | Name and oracle text matching, pagination |
| `/api/cards/semantic` | GET | Vector similarity search | Natural language queries, threshold filtering, exclusions |
| `/api/cards/hybrid` | GET | **Intelligent routing** | Auto-detects query type, 100% accuracy |
| `/api/cards/advanced` | GET | Complex filter queries | CMC, colors, types, power/toughness, keywords |
| `/api/cards/{id}` | GET | Get single card | Returns card with matched rules |
| `/api/cards/{id}/similar` | GET | Find similar cards | Vector similarity, rule filtering |

### Rule Engine Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/rules` | GET | List all rules with stats |
| `/api/rules/{rule_name}/cards` | GET | Get cards matching a rule |
| `/api/categories` | GET | List rule categories |

### Analysis Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/analyze/deck` | POST | Analyze deck composition |
| `/api/stats` | GET | Overall rule engine statistics |
| `/api/stats/rules` | GET | Detailed rule statistics |

### Health Check

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Database connectivity check |
| `/` | GET | API info and endpoint listing |

---

## 2. Query Parser Service (Phi-3.5 Mini)

**File:** `scripts/api/query_parser_service.py`

### Architecture
- **Model:** microsoft/Phi-3.5-mini-instruct (4B parameters)
- **Purpose:** Parse natural language queries into structured search parameters
- **Strategy:** Regex-first with LLM fallback (LLM disabled due to unreliability)

### Key Functionality
```python
class QueryParserService:
    def parse_query(query: str) -> Dict:
        """
        Returns:
        {
            "positive_query": str,      # What to search FOR
            "exclusions": List[str],    # What to EXCLUDE
            "original_query": str
        }
        """
```

### Pattern Detection
- **"X but only Y"** → Include Y, exclude all others
- **"X no Y"** / **"X without Y"** → Include X, exclude Y
- **Fallback:** Return query as-is with no exclusions

### Current Limitations
- LLM-based parsing is **unreliable** (disabled in favor of regex)
- Only handles simple exclusion patterns
- No parameter extraction (damage amounts, CMC, etc.)

### Reusable Components for Agent System
- ✅ Model loading infrastructure (singleton pattern)
- ✅ Prompt engineering foundation
- ❌ Current implementation too limited for conversational AI

**Recommendation:** Keep infrastructure, replace logic with advanced parser + LLM for conversation

---

## 3. Advanced Query Parser

**File:** `scripts/api/advanced_query_parser.py`

### Supported Filters

| Category | Examples | Implementation |
|----------|----------|----------------|
| **CMC** | "cmc > 3", "2 mana or less", "exactly 4 mana" | Regex patterns with operator mapping |
| **Colors** | "blue", "not black", "only red" | Color symbol mapping (W,U,B,R,G) |
| **Types** | "creatures", "instants", "artifacts" | Type line matching |
| **Keywords** | "with flying", "no haste" | Keyword array and oracle text search |
| **Rarity** | "rare", "mythic" | Exact rarity matching |
| **Power/Toughness** | "power > 4", "3/3 or bigger" | Cast to integer with operator |

### Output Format
```python
@dataclass
class ParsedQuery:
    positive_terms: str              # Semantic search query
    exclusions: List[str]            # Terms to exclude
    filters: Dict[str, Any]          # Structured filters
    original_query: str
```

### SQL Generation
```python
def to_sql_where_clause(parsed: ParsedQuery) -> Tuple[str, List[Any]]:
    """
    Returns: (where_clause, parameters)
    
    Example:
        "zombies not black cmc > 3" →
        ("type_line ILIKE %s AND (mana_cost NOT LIKE %s) AND cmc > %s",
         ["%zombie%", "%{B}%", 3])
    """
```

### Reusable for Agent System
- ✅ **Excellent filter extraction**
- ✅ **SQL generation** (can be used for tool functions)
- ✅ **Comprehensive pattern matching**
- ✅ **Clean dataclass design**

**Recommendation:** Integrate as a tool for the agent to construct filtered searches

---

## 4. Hybrid Search Service

**File:** `scripts/api/hybrid_search_service.py`

### Intelligence Layer

```python
class HybridSearchService:
    def classify_query(query: str) -> str:
        """
        Returns: 'keyword', 'advanced', or 'semantic'
        
        Decision tree:
        1. Looks like card name? → keyword
        2. Contains filters (cmc, colors)? → advanced
        3. Default → semantic
        """
```

### Card Name Detection
- Title-cased words
- 1-5 word limit
- No search operators ("with", "has", "that")
- 50%+ capitalized words

### Name Match Boosting
```python
def _boost_name_matches(query, results) -> List[Dict]:
    """
    Boost algorithm:
    - Exact match: 1.0
    - Starts with: +0.25
    - Contains: +0.15
    - Fuzzy similar (>0.7): +0.10
    """
```

### Performance
- **Exact names:** 0.62 → 1.00 similarity (+61%)
- **Natural language:** +5% improvement
- **100% classification accuracy** on test suite

### Reusable for Agent System
- ✅ Query classification logic
- ✅ Boosting strategies
- ✅ Result deduplication
- ✅ Threshold filtering

**Recommendation:** Use as reference for implementing agent's search tool routing

---

## 5. Embedding Service

**File:** `scripts/api/embedding_service.py`

### Model
- **Name:** all-MiniLM-L6-v2
- **Dimension:** 384 (note: schema shows 1536, likely mismatch)
- **Library:** sentence-transformers

### API
```python
class EmbeddingService:
    def generate_embedding(text: str) -> List[float]
    def generate_embeddings_batch(texts: List[str]) -> List[List[float]]
```

### Usage Pattern
- Singleton instance via `get_embedding_service()`
- Loaded once at server startup
- Used for all semantic searches

### Reusable for Agent System
- ✅ Embedding generation for semantic searches
- ❌ **Not suitable for conversation embedding** (model too small)

**Recommendation:** Keep for card search, add separate conversational embeddings if needed

---

## 6. Database Schema

**File:** `sql/schemas/schema_with_rules.sql`

### Core Tables

#### `cards` Table
```sql
CREATE TABLE cards (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    mana_cost VARCHAR(100),
    cmc DECIMAL,
    type_line VARCHAR(255),
    oracle_text TEXT,
    colors TEXT[],                  -- Card colors
    color_identity TEXT[],          -- Commander colors
    rarity VARCHAR(20),
    set_code VARCHAR(10),
    released_at DATE,
    power VARCHAR(10),
    toughness VARCHAR(10),
    loyalty VARCHAR(10),
    keywords TEXT[],                -- Extracted keywords
    produced_mana TEXT[],           -- Mana production
    data JSONB,                     -- Full Scryfall JSON
    embedding vector(1536),         -- Full card embedding
    oracle_embedding vector(1536),  -- Oracle text only
    is_playable BOOLEAN,            -- Standard/Commander legal
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Key Indexes:**
- GIN indexes on arrays (colors, keywords)
- IVFFlat indexes on vector columns
- B-tree on name, type_line, cmc
- JSONB GIN index on data column

#### `rules` Table
```sql
CREATE TABLE rules (
    id UUID PRIMARY KEY,
    rule_name VARCHAR(255) UNIQUE,
    rule_template TEXT,             -- "Destroy target [card_type]"
    rule_pattern TEXT,              -- Regex for matching
    category_id UUID,
    parameters JSONB,               -- Parameter schema
    examples TEXT[],
    card_count INTEGER,
    confidence DECIMAL,
    is_manual BOOLEAN,
    embedding vector(1536),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### `rule_categories` Table
```sql
CREATE TABLE rule_categories (
    id UUID PRIMARY KEY,
    name VARCHAR(100) UNIQUE,
    description TEXT,
    parent_category_id UUID,        -- Hierarchical
    icon VARCHAR(50),
    color VARCHAR(7),               -- Hex color
    sort_order INTEGER
);
```

#### `card_rules` Table (Junction)
```sql
CREATE TABLE card_rules (
    id UUID PRIMARY KEY,
    card_id UUID REFERENCES cards(id),
    rule_id UUID REFERENCES rules(id),
    confidence DECIMAL,
    parameter_bindings JSONB,       -- Extracted parameters
    extraction_method VARCHAR(50),  -- 'vector_similarity', 'regex', 'manual'
    extracted_at TIMESTAMP,
    UNIQUE(card_id, rule_id)
);
```

#### `rule_interactions` Table
```sql
CREATE TABLE rule_interactions (
    id UUID PRIMARY KEY,
    rule_a_id UUID,
    rule_b_id UUID,
    interaction_type VARCHAR(50),   -- 'synergy', 'counter', 'combo'
    description TEXT,
    strength DECIMAL,               -- 0-1
    examples JSONB
);
```

### Useful Views

#### `cards_with_rules`
- Cards enriched with rule classifications
- Aggregated rule counts and categories

#### `rules_with_stats`
- Rules with card counts
- Average confidence scores
- Example cards

#### `database_stats`
- Overall statistics dashboard
- Total cards, rules, mappings

### Database Functions

#### `find_similar_cards()`
```sql
find_similar_cards(
    target_card_id UUID,
    similarity_threshold DECIMAL,
    result_limit INTEGER
) RETURNS TABLE (id, name, type_line, similarity)
```

#### `update_rule_card_counts()` (Trigger)
- Auto-updates rule.card_count when card_rules changes

### Reusable for Agent System
- ✅ **Comprehensive card data** (509k+ cards)
- ✅ **Rule classification** (can describe card mechanics)
- ✅ **Interaction detection** (combo suggestions)
- ✅ **JSONB flexibility** (store conversation state)
- ✅ **Vector search** (semantic similarity)

**Recommendation:** 
- Use existing tables as-is for card/rule data
- Add new tables for conversation state:
  - `conversations` (session management)
  - `conversation_messages` (chat history)
  - `conversation_context` (working memory)

---

## 7. Rule Engine

**File:** `scripts/api/rule_engine.py`

### Core Functionality

```python
class MTGRuleEngine:
    def get_card(card_id: str) -> Optional[Dict]
    def get_card_by_name(name: str) -> Optional[Dict]
    def search_cards_by_name(search_term: str) -> List[Dict]
    
    def get_card_rules(card_id: str) -> List[Dict]
    def find_cards_by_rule(rule_name: str) -> List[Dict]
    def find_similar_cards(card_id: str) -> List[Dict]
    
    def analyze_deck(card_names: List[str]) -> Dict
    def get_rule_statistics() -> Dict
```

### Key Features

1. **Fuzzy Name Matching**
   - Exact match → case-insensitive → word tokenization
   - Orders by relevance (starts with > contains)

2. **Deduplication**
   - Returns most recent printing per card name
   - Uses `DISTINCT ON (name) ORDER BY released_at DESC`

3. **Playability Filtering**
   - `include_nonplayable=False` by default
   - Filters tokens, schemes, planechase, vanguard

4. **Deck Analysis**
   - Rule distribution across deck
   - Category summary
   - Card-to-rule mapping statistics

### Reusable for Agent System
- ✅ **Card lookup tools** (name, ID, similarity)
- ✅ **Rule explanation** (get card rules)
- ✅ **Deck analysis** (synergy detection)
- ✅ **Statistics** (answer "how many X" questions)

**Recommendation:** Wrap these methods as agent tools/functions

---

## 8. Conversational Patterns (Current State)

### Existing Patterns
The system currently has **NO conversational capability**. It's a stateless REST API.

### Query Understanding
- **Simple patterns:** Handled by regex (fast but limited)
- **Complex patterns:** Attempted with Phi-3.5 mini (unreliable, disabled)
- **No context:** Each query is independent
- **No multi-turn:** Cannot reference previous results

### User Intent Detection
- **Hybrid search** classifies intent (keyword vs semantic vs advanced)
- **Advanced parser** extracts filters from natural language
- **No clarification:** Cannot ask follow-up questions

### Response Generation
- **Structured JSON only** (no natural language responses)
- **No explanations** (why a card matched)
- **No recommendations** (what to try next)

---

## 9. Reusable Components for Agentic System

### ✅ Highly Reusable (Use As-Is)

| Component | File | Purpose |
|-----------|------|---------|
| **Database Schema** | `schema_with_rules.sql` | Card data, rules, interactions |
| **Rule Engine** | `rule_engine.py` | Card lookups, rule matching, deck analysis |
| **Advanced Parser** | `advanced_query_parser.py` | Filter extraction and SQL generation |
| **Embedding Service** | `embedding_service.py` | Semantic search embeddings |
| **Hybrid Search** | `hybrid_search_service.py` | Query classification and boosting |

### ⚠️ Partially Reusable (Needs Adaptation)

| Component | File | What to Keep | What to Replace |
|-----------|------|--------------|-----------------|
| **Query Parser** | `query_parser_service.py` | Model loading pattern | Regex logic with LLM |
| **API Server** | `api_server_rules.py` | Endpoint structure | Add websocket for streaming |

### ❌ Not Reusable (Build From Scratch)

| Component | Reason |
|-----------|--------|
| **Conversation State** | No existing implementation |
| **Multi-turn Dialog** | System is stateless |
| **LLM Response Generation** | Only structured JSON |
| **Tool Calling** | No agent framework |
| **Memory Management** | No context persistence |

---

## 10. Architecture Gaps for Agent System

### Missing Components

1. **Conversation Management**
   - Session tracking
   - Message history
   - Context window management
   - Memory persistence

2. **LLM Integration**
   - Conversational model (e.g., Llama 3.1 70B, GPT-4)
   - Streaming responses
   - Tool/function calling
   - Prompt engineering

3. **Agent Framework**
   - Tool registry
   - Execution loop
   - Error handling
   - Retry logic

4. **State Management**
   - Working memory (current deck, filters)
   - Long-term memory (user preferences)
   - Conversation context (last N messages)

5. **Response Generation**
   - Natural language explanations
   - Card recommendations
   - Clarification questions
   - Result summarization

### Suggested Architecture

```
┌─────────────────────────────────────────────────────┐
│                   User Input                         │
└──────────────────────┬──────────────────────────────┘
                       │
                       v
┌─────────────────────────────────────────────────────┐
│              Conversation Manager                    │
│  - Load session                                      │
│  - Retrieve message history                          │
│  - Build context window                              │
└──────────────────────┬──────────────────────────────┘
                       │
                       v
┌─────────────────────────────────────────────────────┐
│                LLM Agent (Llama 3.1)                 │
│  - Understand intent                                 │
│  - Decide which tools to use                         │
│  - Generate natural language                         │
└──────────────────────┬──────────────────────────────┘
                       │
                       v
┌─────────────────────────────────────────────────────┐
│                  Tool Registry                       │
│  ┌──────────────────────────────────────────────┐  │
│  │ search_cards()                                │  │
│  │ get_card_details()                            │  │
│  │ find_similar_cards()                          │  │
│  │ analyze_deck()                                │  │
│  │ explain_rules()                               │  │
│  │ suggest_combos()                              │  │
│  │ filter_cards() [uses AdvancedQueryParser]     │  │
│  └──────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────┘
                       │
                       v
┌─────────────────────────────────────────────────────┐
│              Existing Backend (Reused)               │
│  - Rule Engine                                       │
│  - Hybrid Search                                     │
│  - Database (cards, rules, interactions)             │
└─────────────────────────────────────────────────────┘
```

---

## 11. Recommended Next Steps

### Phase 1: Foundation (Week 1)
1. **Add conversation tables** to schema
   - `conversations` (session management)
   - `conversation_messages` (chat history)
   - `conversation_context` (working memory)

2. **Choose LLM backend**
   - Option A: Local Llama 3.1 70B (requires GPU)
   - Option B: OpenAI GPT-4 (easiest)
   - Option C: Anthropic Claude (best reasoning)

3. **Select agent framework**
   - LangChain (most mature)
   - LlamaIndex (specialized for RAG)
   - Custom (most control)

### Phase 2: Core Agent (Week 2)
1. **Implement conversation manager**
   - Session creation/loading
   - Message persistence
   - Context window management

2. **Define tool functions**
   - Wrap existing RuleEngine methods
   - Add search tools (keyword, semantic, advanced)
   - Add analysis tools (deck, combos, synergies)

3. **Build agent loop**
   - Prompt engineering
   - Tool calling
   - Response generation
   - Error handling

### Phase 3: Enhancement (Week 3)
1. **Add memory system**
   - Short-term (conversation context)
   - Long-term (user preferences, deck history)
   - Working memory (current deck being built)

2. **Implement streaming**
   - WebSocket support
   - Server-sent events (SSE)
   - Real-time tool execution feedback

3. **Add advanced features**
   - Multi-step reasoning
   - Clarification questions
   - Proactive suggestions
   - Deck optimization

### Phase 4: Polish (Week 4)
1. **Testing and validation**
   - Unit tests for tools
   - Integration tests for agent
   - User acceptance testing

2. **Performance optimization**
   - Caching layer
   - Parallel tool execution
   - Database query optimization

3. **Documentation**
   - API documentation
   - Agent prompt examples
   - Troubleshooting guide

---

## 12. Key Insights

### Strengths of Current System
1. ✅ **Mature data layer** (509k cards, comprehensive schema)
2. ✅ **Excellent search** (hybrid approach, 100% accuracy)
3. ✅ **Rich metadata** (rules, interactions, categories)
4. ✅ **Clean architecture** (separation of concerns)
5. ✅ **Well-tested** (83% test coverage)

### Weaknesses for Conversational AI
1. ❌ **No state management** (stateless API)
2. ❌ **No natural language generation** (JSON only)
3. ❌ **No multi-turn dialog** (each query independent)
4. ❌ **Limited LLM use** (only query parsing, unreliable)
5. ❌ **No tool orchestration** (no agent framework)

### What Makes This System Unique
1. **Dual embeddings** (full card + oracle text only)
2. **Rule classification** (cards mapped to templates)
3. **Interaction detection** (combos, synergies, counters)
4. **Parameter binding** (extracted values from card text)
5. **Playability filtering** (exclude tokens, banned cards)

### What to Preserve
- **Database schema** (complete and well-designed)
- **Rule engine** (powerful analysis capabilities)
- **Hybrid search** (intelligent query routing)
- **Advanced parser** (excellent filter extraction)
- **Embedding infrastructure** (semantic search)

### What to Build New
- **Conversation management** (session, history, context)
- **LLM integration** (conversational model, streaming)
- **Agent framework** (tool calling, reasoning loop)
- **Memory system** (working memory, preferences)
- **Natural language generation** (responses, explanations)

---

## 13. Example Agent Interactions

### Example 1: Simple Card Search
```
User: "Show me some red burn spells"

Agent: [calls search_cards(query="red burn spells", method="semantic")]
       [receives: Lightning Bolt, Shock, Lava Spike, ...]

Agent: "I found several red burn spells for you:

       1. **Lightning Bolt** - {R} instant, deals 3 damage
       2. **Shock** - {R} instant, deals 2 damage  
       3. **Lava Spike** - {R} sorcery, deals 3 damage to player
       
       Would you like to see more options or filter by mana cost?"
```

### Example 2: Deck Building with Context
```
User: "I'm building a zombie deck"

Agent: [stores context: deck_theme="zombie"]
       "Great! Let me help you build a zombie deck. 
       What format are you building for?"

User: "Commander"

Agent: [updates context: format="commander"]
       [calls search_cards(query="zombie commander", type="creature")]
       
       "Here are some strong zombie commanders:
       
       1. **The Scarab God** - Great reanimation synergy
       2. **Wilhelt, the Rotcleaver** - Token generation
       3. **Varina, Lich Queen** - Card draw and lifegain
       
       Which direction interests you most?"

User: "Scarab God sounds cool"

Agent: [updates context: commander="The Scarab God"]
       [calls analyze_deck_synergies(commander="The Scarab God")]
       
       "The Scarab God works great with:
       - Graveyard recursion (e.g., Gravecrawler)
       - ETB effects (e.g., Gray Merchant)
       - Card draw (e.g., Cryptbreaker)
       
       Should I search for cards in these categories?"
```

### Example 3: Rules Explanation
```
User: "How does The Scarab God work?"

Agent: [calls get_card_details("The Scarab God")]
       [calls get_card_rules("The Scarab God")]
       
       "The Scarab God has several abilities:
       
       1. **At the beginning of your upkeep**: Scry 1, then each opponent 
          loses X life and you gain X life, where X is the number of 
          zombies you control.
          
       2. **{2}{U}{B}**: Exile target creature card from a graveyard, 
          create a 4/4 black Zombie token copy of it.
          
       3. **Returns to hand**: When it dies, it returns to your hand 
          at the next end step instead of going to graveyard.
       
       This card synergizes with graveyard strategies and zombie tribal.
       Would you like card suggestions that work well with it?"
```

### Example 4: Complex Query with Filters
```
User: "Find zombies that cost less than 3 mana but aren't black"

Agent: [calls filter_cards(
           type="creature zombie",
           cmc_lt=3,
           exclude_colors=["B"]
       )]
       [receives: Diregraf Ghoul (Green), Undead Butler (White), ...]
       
       "I found 8 non-black zombie creatures under 3 mana:
       
       1. **Diregraf Ghoul** - {G} 2/2, enters tapped
       2. **Undead Butler** - {1}{W} 1/2, finds zombies
       3. **Shambling Ghoul** - {1}{R} 2/1, haste
       
       These are unusual for zombies (typically black). 
       Are you building a unique zombie tribal deck?"
```

---

## 14. Technical Specifications

### Current Performance
- **Database size:** ~500k cards, ~1GB vector data
- **Query latency:** 
  - Keyword search: ~50ms
  - Semantic search: ~200ms (embedding + vector search)
  - Advanced search: ~100ms (filter + semantic)
  - Hybrid search: ~150ms average
- **Embedding generation:** ~20ms per query
- **LLM query parsing:** ~500ms (disabled due to unreliability)

### Expected Agent Performance
- **Simple queries:** 1-2 seconds (LLM + 1 tool call)
- **Complex queries:** 3-5 seconds (LLM + multiple tool calls)
- **Deck analysis:** 5-10 seconds (multiple database queries)
- **Streaming:** First tokens in ~500ms, full response in 2-3 seconds

### Resource Requirements
- **Current:** 2GB RAM, 1 CPU core, 20GB disk
- **With Agent:**
  - Local LLM: +32GB RAM, +1 GPU (24GB VRAM)
  - Cloud LLM: +500MB RAM, +API costs
  - Agent framework: +1GB RAM
  - **Total:** ~4-36GB RAM depending on LLM choice

---

## Conclusion

The existing vector-mtg system provides an **excellent foundation** for building an agentic conversational system:

1. **Rich data layer** (cards, rules, interactions)
2. **Powerful search** (hybrid, semantic, advanced)
3. **Clean architecture** (modular, well-tested)
4. **Reusable components** (75% can be used as-is)

The main gaps are:
1. **Conversation management** (sessions, history, context)
2. **LLM integration** (conversational model, streaming)
3. **Agent framework** (tool calling, reasoning)

**Next Step:** Review this summary, then proceed to design the agent architecture based on which components to reuse and which to build new.

---

**Document Version:** 1.0  
**Author:** System Analysis  
**Date:** December 2, 2024
