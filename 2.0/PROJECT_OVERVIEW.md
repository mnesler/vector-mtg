# MTG Planeswalker AI - Project 2.0

**Project Name:** MTG Planeswalker AI (Agentic Deck Building & Game Analysis System)  
**Version:** 2.0  
**Status:** Planning Phase  
**Timeline:** 4-6 weeks to MVP  
**Start Date:** TBD  

---

## 🎯 Vision

Build an **intelligent conversational assistant** that helps Magic: The Gathering players:
1. **Build competitive decks** through natural language conversation
2. **Analyze existing decks** for strengths, weaknesses, and synergies
3. **Evaluate game states** and suggest optimal plays

---

## 📋 Key Requirements (from User)

### Authentication
- ✅ **Google OAuth** (primary)
- ✅ **Discord OAuth** (gaming community)
- ✅ **Steam OAuth** (gaming platform integration)
- Sessions tracked per user
- Anonymous browsing allowed, auth required to save decks

### LLM Strategy
- **Stubbed providers** - Decision deferred
- Options: GPT-4, Claude, Local (Llama, Phi), or Hybrid
- Architecture supports swapping providers easily

### Deck Sharing
- **Public links** for deck sharing
- Format: `https://app.com/decks/{public_id}`
- Optional: Private decks (auth required)
- Export formats: TXT, JSON, MTGO, MTG Arena

### Format Priority
1. **Standard** (top priority)
2. **Commander** (EDH)
3. **Modern** (covered by Standard + Commander card pool)
4. ❌ No Legacy, Vintage, or older formats

### UI/UX
- **Web-only** (no native mobile apps)
- **Responsive design** (mobile, tablet, desktop)
- Mobile-first layout considerations
- Chat interface + existing search UI integration

---

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                        │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  Search UI       │  │  Chat Interface  │  [Responsive]   │
│  │  (Existing 1.0)  │  │  (NEW 2.0)       │                │
│  └──────────────────┘  └──────────────────┘                │
└────────────┬────────────────────┬───────────────────────────┘
             │                    │
             │                    │ WebSocket
             v                    v
┌─────────────────────┐  ┌──────────────────────────────────┐
│  Search API         │  │  Agent Service (NEW 2.0)         │
│  (Port 8000)        │  │  (Port 8001)                     │
│  - Hybrid Search    │  │  - Auth (OAuth)                  │
│  - Rule Engine      │  │  - Conversation Manager          │
│  - 509K Cards       │  │  - LLM Agents (stubbed)          │
│  [NO CHANGES]       │  │  - Tool Registry                 │
└─────────────────────┘  │  - Deck Management               │
                         └──────────────────────────────────┘
                                     │
                                     v
                         ┌──────────────────────────────────┐
                         │  PostgreSQL Database             │
                         │  - Existing: cards, rules, etc.  │
                         │  - NEW: users, sessions, decks   │
                         └──────────────────────────────────┘
```

---

## 📁 Project Structure

```
/home/maxwell/vector-mtg/
├── 1.0/ (existing)
│   ├── scripts/api/          # Existing search API (port 8000)
│   ├── ui/                   # Existing Next.js UI
│   └── sql/                  # Existing database schemas
│
└── 2.0/ (NEW)
    ├── PROJECT_OVERVIEW.md           # This file
    ├── ARCHITECTURE.md               # Detailed system architecture
    ├── DATABASE_SCHEMA.md            # New tables for 2.0
    ├── API_SPECIFICATION.md          # Agent API endpoints
    ├── AUTHENTICATION.md             # OAuth implementation plan
    ├── LLM_PROVIDER_DESIGN.md        # LLM abstraction layer
    ├── AGENT_SYSTEM.md               # Agent architecture & tools
    ├── UI_DESIGN.md                  # Chat interface & responsive design
    ├── DECK_SHARING.md               # Public deck links & export
    ├── IMPLEMENTATION_ROADMAP.md     # Week-by-week plan
    └── TECH_STACK.md                 # Technologies & dependencies
```

---

## 🎯 Core Features (MVP)

### 1. Deck Builder Agent
**Goal:** Conversational deck building experience

**Flow:**
```
User: "Build me an aggressive red deck for Standard"
↓
Agent: Asks clarifying questions (budget, key cards, win condition)
↓
Agent: Searches cards using tools
↓
Agent: Proposes deck list with explanations
↓
Agent: Iterates based on user feedback
↓
Save deck → Generate public link
```

**Key Capabilities:**
- Natural language understanding
- Format-aware card suggestions
- Mana curve optimization
- Budget constraints
- Synergy detection

### 2. Deck Analyzer Agent
**Goal:** Evaluate existing decks

**Features:**
- Mana curve analysis
- Combo detection (2-card, 3-card)
- Synergy identification
- Weakness detection
- Upgrade suggestions
- Format legality check

**Input Methods:**
- Paste deck list (text format)
- Import from file
- Link to existing saved deck
- Manual card entry via chat

### 3. Game State Solver Agent (Basic)
**Goal:** Evaluate board positions

**Phase 1 (MVP):**
- Calculate lethal damage
- Board advantage evaluation
- Simple combat math
- Suggest optimal attacks/blocks

**Phase 2 (Future):**
- Stack resolution
- Triggered abilities
- Complex interactions
- Full rules engine

---

## 🔐 Authentication System

### OAuth Providers
1. **Google** - Primary (most users)
2. **Discord** - Gaming community
3. **Steam** - Gaming platform

### User Flow
```
1. Visit site → Browse/search without auth (read-only)
2. Click "Build Deck" → Prompt for login
3. Choose OAuth provider → Redirect to provider
4. Provider authenticates → Redirect back with token
5. Create/link user account → Start conversation
6. Save decks → Associated with user account
```

### Sessions
- JWT tokens for API authentication
- Server-side session storage (PostgreSQL)
- Refresh token rotation
- 30-day expiration (with refresh)

---

## 💬 Conversation System

### Session Management
- Each conversation = unique session ID
- Sessions persist across page reloads
- Context preserved (deck being built, user preferences)
- History stored (past 20 messages + full deck state)

### Multi-Agent Orchestration
```
User Message
    ↓
Conversation Manager
    ↓
Intent Detection → Route to appropriate agent:
    ├─→ Deck Builder Agent (new deck)
    ├─→ Deck Analyzer Agent (analyze existing)
    ├─→ Game Solver Agent (evaluate board state)
    └─→ General Assistant (questions, help)
```

---

## 🔧 Tool System

### Categories
1. **Card Tools** (~8 tools)
   - search_cards, find_similar, get_card_details, filter_by_rules

2. **Deck Tools** (~10 tools)
   - add_card, remove_card, suggest_lands, check_legality, calculate_curve

3. **Analysis Tools** (~8 tools)
   - detect_combos, find_synergies, identify_weaknesses, suggest_upgrades

4. **Game State Tools** (~5 tools)
   - evaluate_board, calculate_lethal, suggest_play

**Total:** ~31 tools wrapping existing APIs + new logic

---

## 📊 Data Requirements

### New Data to Collect
1. **Combo Database**
   - Source: CommanderSpellbook.com, MTGSalvation
   - ~500-1000 known combos
   - Store: card IDs, steps, format legality

2. **Meta Deck Lists**
   - Source: MTGGoldfish, MTGTop8
   - Top decks per format
   - Use for archetype classification

3. **Comprehensive Rules**
   - Source: Wizards official CR document
   - Parse keyword definitions
   - Game mechanics reference

### Existing Data (Reuse)
- ✅ 509K cards with embeddings
- ✅ Rule templates (45+)
- ✅ Card-to-rule mappings (425K+)
- ✅ Keyword abilities

---

## 🎨 User Experience

### Chat Interface Design
```
┌─────────────────────────────────────────────────────────┐
│  [Search] [Deck Builder] [Analyzer] [Profile]           │ ← Nav
├─────────────────────────────────────────────────────────┤
│                                                          │
│  💬 Chat Messages                                        │
│  ┌────────────────────────────────────────────────────┐ │
│  │ You: Build me a red aggro deck for Standard        │ │
│  │                                                     │ │
│  │ 🤖 Agent: Great! A few questions:                  │ │
│  │    1. Budget? (budget/moderate/competitive)       │ │
│  │    2. Key cards to include?                       │ │
│  │    3. Preferred win condition?                    │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  [Deck Preview Panel] ─────────────────────────────────┐ │
│  │ Current Deck (24 cards)                            │ │
│  │ Creatures (16) | Spells (8) | Lands (0)           │ │
│  │ Avg CMC: 2.1 | Curve: █████▃▁▁                   │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  [Type message...] [🎤] [📎] [Send]                     │
└─────────────────────────────────────────────────────────┘
```

### Responsive Breakpoints
- **Mobile** (<640px): Single column, collapsible deck panel
- **Tablet** (640-1024px): Side-by-side chat + deck preview
- **Desktop** (>1024px): Three columns (chat, deck, card details)

---

## 🚀 Success Criteria

### Functional
- [ ] Users can build a complete deck in <10 conversation turns
- [ ] Deck analyzer identifies all 2-card combos in deck
- [ ] Format legality check 100% accurate
- [ ] Card suggestions 80%+ relevance (user feedback)
- [ ] Game state solver correctly calculates lethal 95%+ of time

### Technical
- [ ] Response time <2s (or streaming <500ms to first token)
- [ ] Support 100+ concurrent chat sessions
- [ ] 99.9% uptime for API
- [ ] OAuth login <3s end-to-end
- [ ] Deck save/load <1s

### User Experience
- [ ] Mobile-friendly (passes Google mobile test)
- [ ] Accessible (WCAG 2.1 AA)
- [ ] Deck sharing works (public links load <2s)
- [ ] Export to Arena format works 100%

---

## 💰 Cost Projections

### Development (4-6 weeks)
- Developer time: Variable
- OpenAI API (testing): ~$50
- Infrastructure: $0 (local dev)

### Production (Monthly, 1000 users)
**Scenario: GPT-4 Turbo**
- 1000 users × 10 conversations/month × $0.014/interaction = $140/month
- VPS hosting: $20-50/month
- Database: $0 (included with VPS)
- **Total: ~$160-190/month**

**Scenario: Local LLM (Llama 3.1)**
- VPS with GPU: $200-400/month
- OR quantized on CPU: $50/month (slower)
- **Total: $50-400/month**

**Scenario: Hybrid**
- Simple tasks → Local (free)
- Complex reasoning → GPT-4 (~$50-100/month)
- **Total: ~$70-150/month**

---

## ⚠️ Risks & Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| LLM provider downtime | High | Low | Fallback provider, graceful degradation |
| High API costs | Medium | Medium | Caching, rate limiting, local LLM option |
| Poor card suggestions | High | Medium | Validation layer, user feedback loop |
| OAuth provider issues | High | Low | Multiple providers, fallback to email/password |
| Slow response times | Medium | Medium | Streaming responses, tool call optimization |
| Inaccurate combo detection | Medium | Medium | Manual curation, community submissions |

---

## 📈 Future Enhancements (Post-MVP)

### Phase 2 (Month 2-3)
- Advanced game state solver (stack, priority)
- Deck versioning (track changes over time)
- Sideboard suggestions
- Mulligan advice
- Draft/sealed deck builder

### Phase 3 (Month 4-6)
- Tournament preparation mode
- Meta analysis (what decks are popular)
- Deck statistics (win rates, matchups)
- Social features (friends, deck sharing within groups)
- Mobile apps (React Native)

### Phase 4 (Month 7+)
- Deck brewing challenges
- AI vs AI deck battles (simulation)
- Integration with MTGO/Arena
- Deck rental/proxying service integration
- Monetization (premium features)

---

## 🔗 Related Documents

1. **ARCHITECTURE.md** - Detailed technical architecture
2. **DATABASE_SCHEMA.md** - Complete database design
3. **API_SPECIFICATION.md** - All endpoints and schemas
4. **AUTHENTICATION.md** - OAuth implementation details
5. **LLM_PROVIDER_DESIGN.md** - LLM abstraction layer
6. **AGENT_SYSTEM.md** - Agent architecture and tools
7. **UI_DESIGN.md** - Chat interface and components
8. **DECK_SHARING.md** - Public links and export formats
9. **IMPLEMENTATION_ROADMAP.md** - Week-by-week plan
10. **TECH_STACK.md** - Technologies and dependencies

---

## 📝 Next Steps

### Immediate (Before Development)
1. ✅ Review project overview with stakeholders
2. ⏳ Choose LLM provider(s)
3. ⏳ Get OAuth credentials (Google, Discord, Steam)
4. ⏳ Review all planning documents
5. ⏳ Finalize database schema
6. ⏳ Approve UI mockups

### Development Phase
7. Week 1: Database + Auth
8. Week 2: Agent framework + basic tools
9. Week 3: Deck builder agent
10. Week 4: Deck analyzer agent
11. Week 5: Chat UI + integration
12. Week 6: Testing + polish

---

**Document Version:** 1.0  
**Last Updated:** December 3, 2024  
**Status:** Planning - Awaiting Approval
