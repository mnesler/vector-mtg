# Component Reusability Matrix for Agentic System

Quick reference for what to reuse vs. build new

---

## Legend
- ✅ **Reuse as-is** - Can be used directly without modification
- 🔄 **Adapt** - Needs minor modifications or wrapper
- 🆕 **Build new** - Must be created from scratch
- 🤔 **Evaluate** - Depends on LLM choice and requirements

---

## Data Layer

| Component | Status | Usage in Agent | Notes |
|-----------|--------|----------------|-------|
| PostgreSQL + pgvector | ✅ | Database backend | Production-ready, well-indexed |
| `cards` table | ✅ | Card data source | 509k cards with dual embeddings |
| `rules` table | ✅ | Rule explanations | Pre-classified mechanics |
| `rule_categories` table | ✅ | Category browsing | Hierarchical organization |
| `card_rules` table | ✅ | Card-to-rule mapping | Confidence scores + parameters |
| `rule_interactions` table | ✅ | Combo detection | Synergies, counters, combos |

**New tables needed:**
- 🆕 `conversations` - Session management
- 🆕 `conversation_messages` - Chat history
- 🆕 `conversation_context` - Working memory (deck, filters)

---

## Search & Retrieval

| Component | Status | Usage in Agent | Notes |
|-----------|--------|----------------|-------|
| Hybrid Search Service | 🔄 | Wrap as tool | Query classification + routing |
| Advanced Query Parser | ✅ | Filter extraction | Use for complex queries |
| Embedding Service | ✅ | Semantic search | Keep for card embeddings |
| Rule Engine | 🔄 | Wrap methods as tools | Card lookup, analysis, stats |

**Implementation:**
```python
# Example tool wrapper
def search_cards_tool(query: str, method: str = "auto") -> List[Dict]:
    """Agent tool for searching cards"""
    service = get_hybrid_search_service(db_conn)
    return service.search(query, limit=10)

def get_card_details_tool(card_name: str) -> Dict:
    """Agent tool for card details + rules"""
    engine = MTGRuleEngine(db_conn)
    card = engine.get_card_by_name(card_name)
    rules = engine.get_card_rules(card['id'])
    return {**card, 'rules': rules}
```

---

## LLM & AI

| Component | Status | Usage in Agent | Notes |
|-----------|--------|----------------|-------|
| Phi-3.5 mini (query parser) | 🤔 | Maybe for intent | Too small for conversation |
| all-MiniLM-L6-v2 (embeddings) | ✅ | Keep for cards | Good for semantic search |
| Conversational LLM | 🆕 | **Required** | Llama 3.1 70B or GPT-4 |
| Agent framework | 🆕 | **Required** | LangChain, LlamaIndex, or custom |
| Tool calling system | 🆕 | **Required** | Function calling interface |
| Prompt templates | 🆕 | **Required** | System prompts for agent |

**Recommendations:**
- **For Local:** Llama 3.1 70B (needs GPU with 24GB+ VRAM)
- **For Cloud:** GPT-4 Turbo or Claude 3.5 Sonnet
- **For Budget:** GPT-3.5 Turbo (good enough for most tasks)

---

## API & Server

| Component | Status | Usage in Agent | Notes |
|-----------|--------|----------------|-------|
| FastAPI app structure | 🔄 | Keep, add endpoints | Solid foundation |
| REST endpoints | ✅ | Keep for backward compat | `/api/cards/*`, `/api/rules/*` |
| CORS middleware | ✅ | Reuse | Already configured |
| Database lifecycle | ✅ | Reuse | Connection pooling works |
| WebSocket support | 🆕 | **Add** | For streaming responses |
| SSE endpoint | 🆕 | **Add** | Alternative to WebSocket |

**New endpoints needed:**
- 🆕 `POST /api/agent/chat` - Send message, get response
- 🆕 `POST /api/agent/session` - Create new session
- 🆕 `GET /api/agent/session/{id}` - Get session history
- 🆕 `WS /api/agent/stream` - WebSocket for streaming

---

## Conversation Management

| Component | Status | Usage in Agent | Notes |
|-----------|--------|----------------|-------|
| Session tracking | 🆕 | **Required** | UUID, created_at, last_active |
| Message persistence | 🆕 | **Required** | User + assistant messages |
| Context window | 🆕 | **Required** | Last N messages + system prompt |
| Working memory | 🆕 | **Required** | Current deck, filters, preferences |
| Long-term memory | 🆕 | Optional | User preferences, deck history |

**Architecture:**
```python
class ConversationManager:
    def create_session() -> str
    def get_messages(session_id: str, limit: int = 10) -> List[Dict]
    def add_message(session_id: str, role: str, content: str)
    def get_context(session_id: str) -> Dict
    def update_context(session_id: str, key: str, value: Any)
```

---

## Agent Tools (Functions)

**Card Search Tools:**
- ✅ `search_cards(query)` - Wrapper around hybrid search
- ✅ `get_card_details(name)` - Get full card info + rules
- ✅ `find_similar_cards(name)` - Vector similarity search
- ✅ `filter_cards(filters)` - Advanced filtering

**Card Analysis Tools:**
- ✅ `explain_card_rules(name)` - Get rule explanations
- ✅ `analyze_deck(cards)` - Deck composition analysis
- ✅ `suggest_synergies(card)` - Find synergistic cards
- ✅ `find_combos(cards)` - Detect combo patterns
- 🆕 `suggest_cuts(deck)` - Recommend cards to remove

**Deck Building Tools:**
- 🆕 `add_to_deck(card, session)` - Add card to working deck
- 🆕 `remove_from_deck(card, session)` - Remove card
- 🆕 `get_current_deck(session)` - View working deck
- 🆕 `optimize_mana_base(deck)` - Suggest lands
- 🆕 `check_deck_legality(deck, format)` - Validate deck

**Statistics Tools:**
- ✅ `get_card_count(query)` - How many cards match?
- ✅ `get_rule_stats()` - Overall statistics
- ✅ `get_format_stats(format)` - Format-specific stats

---

## Response Generation

| Component | Status | Usage in Agent | Notes |
|-----------|--------|----------------|-------|
| Natural language generation | 🆕 | **Required** | LLM-based |
| Card formatting | 🆕 | **Required** | Pretty-print cards |
| Result summarization | 🆕 | **Required** | "Found 42 cards, top 5..." |
| Clarification questions | 🆕 | **Required** | "What format?" |
| Proactive suggestions | 🆕 | Optional | "You might also like..." |
| Error messages | 🆕 | **Required** | User-friendly errors |

**Example prompts:**
```python
SYSTEM_PROMPT = """
You are an MTG deck-building assistant with access to a database of 509,000 cards.

Your capabilities:
- Search for cards by name, mechanics, or natural language
- Explain card rules and interactions
- Suggest synergies and combos
- Analyze deck composition
- Help build decks for any format

Guidelines:
- Always confirm format before suggesting cards
- Explain why cards work together
- Ask clarifying questions when query is ambiguous
- Suggest alternatives when original request isn't feasible
- Keep responses concise but informative

Available tools: {tool_list}
"""
```

---

## Testing Strategy

| Component | Status | Notes |
|-----------|--------|-------|
| Existing tests | ✅ | 83% coverage, keep running |
| Tool unit tests | 🆕 | Test each tool function |
| Agent integration tests | 🆕 | Test multi-turn conversations |
| Prompt testing | 🆕 | Validate prompt quality |
| Performance tests | 🆕 | Latency, throughput |

**Test scenarios:**
1. Simple search: "Find me red burn spells"
2. Complex filter: "Zombies not black under 3 mana"
3. Multi-turn: Build a deck over 5-10 exchanges
4. Clarification: Handle ambiguous queries
5. Error handling: Invalid card names, impossible filters
6. Context memory: Reference previous results

---

## Deployment Considerations

### Option 1: Local LLM (Llama 3.1 70B)
- ✅ **Pros:** No API costs, full control, privacy
- ❌ **Cons:** Needs GPU (24GB+ VRAM), ~60GB disk, slower
- 💰 **Cost:** One-time hardware ($2000+ for GPU)
- ⚡ **Speed:** 2-5s per response

### Option 2: Cloud LLM (GPT-4 Turbo)
- ✅ **Pros:** Fast, no GPU needed, latest models
- ❌ **Cons:** API costs, latency, less control
- 💰 **Cost:** ~$0.01-0.03 per conversation turn
- ⚡ **Speed:** 1-3s per response

### Option 3: Hybrid Approach
- Use GPT-4 for complex reasoning
- Use local Phi-3.5 for simple tasks (intent classification)
- Use existing embeddings for card search

### Recommended Stack

```yaml
LLM: GPT-4 Turbo (via OpenAI API)
Framework: LangChain (mature, well-documented)
Database: PostgreSQL + pgvector (existing)
API: FastAPI + WebSocket (add to existing)
Frontend: React + TypeScript (existing, add chat UI)

Estimated costs:
- Development: 2 weeks
- Hosting: $50/month (server) + $50-200/month (API calls)
- Performance: 1-3s per response, 95% uptime
```

---

## Implementation Priority

### Phase 1 (Week 1) - Foundation
1. ✅ Add conversation tables to schema
2. ✅ Choose LLM provider (GPT-4 Turbo recommended)
3. ✅ Set up LangChain + OpenAI
4. ✅ Create basic conversation manager
5. ✅ Implement 3-5 core tools

### Phase 2 (Week 2) - Core Agent
1. ✅ Build agent loop with tool calling
2. ✅ Add prompt engineering (system + user prompts)
3. ✅ Implement message persistence
4. ✅ Add context management
5. ✅ Test basic conversations

### Phase 3 (Week 3) - Features
1. ✅ Add all remaining tools
2. ✅ Implement streaming responses
3. ✅ Add working memory (deck builder)
4. ✅ Implement error handling
5. ✅ Add clarification logic

### Phase 4 (Week 4) - Polish
1. ✅ Comprehensive testing
2. ✅ Performance optimization
3. ✅ Add chat UI
4. ✅ Documentation
5. ✅ Production deployment

---

## Quick Start Checklist

### Prerequisites
- [ ] PostgreSQL + pgvector running
- [ ] API server functional
- [ ] 509k cards loaded with embeddings
- [ ] OpenAI API key (or local LLM setup)

### Setup Steps
1. [ ] Install LangChain: `pip install langchain openai`
2. [ ] Add conversation tables (migration script)
3. [ ] Create `ConversationManager` class
4. [ ] Wrap existing methods as tools
5. [ ] Set up LangChain agent
6. [ ] Add `/api/agent/chat` endpoint
7. [ ] Test with simple queries
8. [ ] Add streaming support
9. [ ] Build chat UI
10. [ ] Deploy and monitor

---

**Summary:** ~75% of existing code is reusable. Main work is adding:
1. Conversation management (new)
2. LLM integration (new)
3. Tool wrappers (adapt existing)
4. Streaming responses (new)
5. Chat UI (new)

**Estimated effort:** 2-4 weeks for full implementation.

---

**Document Version:** 1.0  
**Created:** December 2, 2024
