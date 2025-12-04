# MTG Planeswalker AI - Project 2.0 Planning

**Status:** 📋 Planning Phase - Ready for Review  
**Last Updated:** December 3, 2024  
**Version:** 1.0

---

## 🎯 Quick Overview

This folder contains comprehensive planning documents for **MTG Planeswalker AI 2.0** - an agentic conversational system that helps players build decks, analyze deck compositions, and evaluate game states through natural language interaction.

**Key Features:**
- 🤖 **Conversational Deck Building** - Chat-based deck creation with AI assistance
- 📊 **Deck Analysis** - Combo detection, synergy identification, weakness analysis
- ♟️ **Game State Solver** - Board evaluation and optimal play suggestions (basic → advanced)
- 🔐 **OAuth Authentication** - Google, Discord, Steam login
- 🔗 **Deck Sharing** - Public links and multiple export formats
- 📱 **Responsive Design** - Mobile, tablet, and desktop support

---

## 📚 Document Index

### Core Planning Documents

| Document | Status | Description |
|----------|--------|-------------|
| **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)** | ✅ Complete | Executive summary, requirements, architecture overview |
| **[TECH_STACK.md](TECH_STACK.md)** | ✅ Complete | Technologies, libraries, infrastructure choices |
| **[IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md)** | ✅ Complete | 6-week development plan with deliverables |
| **[LLM_PROVIDER_DESIGN.md](LLM_PROVIDER_DESIGN.md)** | ⚠️ Stubbed | LLM abstraction layer (provider choice pending) |

### Detailed Specifications (To Be Expanded)

| Document | Status | Description |
|----------|--------|-------------|
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | 📝 Stub | Detailed system architecture, data flows, diagrams |
| **[DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)** | 📝 Stub | Complete SQL schema for new tables, migrations |
| **[API_SPECIFICATION.md](API_SPECIFICATION.md)** | 📝 Stub | REST/WebSocket endpoints, OpenAPI specs |
| **[AUTHENTICATION.md](AUTHENTICATION.md)** | 📝 Stub | OAuth implementation details for 3 providers |
| **[AGENT_SYSTEM.md](AGENT_SYSTEM.md)** | 📝 Stub | Agent architecture, tools, orchestration |
| **[UI_DESIGN.md](UI_DESIGN.md)** | 📝 Stub | Chat interface design, responsive layouts |
| **[DECK_SHARING.md](DECK_SHARING.md)** | 📝 Stub | Public links, privacy, export formats |

**Note on Stubs:** These documents have placeholder content and will be expanded during the detailed planning phase. They outline what needs to be documented.

---

## 🗂️ Document Reading Order

### For Stakeholders / Product Review
1. **PROJECT_OVERVIEW.md** - Start here for the big picture
2. **IMPLEMENTATION_ROADMAP.md** - Timeline and milestones
3. **TECH_STACK.md** - Technical decisions and costs

### For Development Team
1. **PROJECT_OVERVIEW.md** - Context and requirements
2. **ARCHITECTURE.md** - System design (to be expanded)
3. **DATABASE_SCHEMA.md** - Data model (to be expanded)
4. **API_SPECIFICATION.md** - API contracts (to be expanded)
5. **TECH_STACK.md** - Implementation technologies
6. **IMPLEMENTATION_ROADMAP.md** - Development schedule

### For Specific Areas

**Authentication:**
- AUTHENTICATION.md (OAuth implementation)
- DATABASE_SCHEMA.md (user tables)

**Conversational AI:**
- LLM_PROVIDER_DESIGN.md (LLM abstraction)
- AGENT_SYSTEM.md (agent architecture)

**Frontend:**
- UI_DESIGN.md (chat interface)
- Existing: `/ui/` for 1.0 codebase

**Deck Features:**
- DECK_SHARING.md (public links, export)
- AGENT_SYSTEM.md (deck building tools)

---

## ✅ Key Decisions Made

### From User Requirements
1. ✅ **Authentication:** Google + Discord + Steam OAuth
2. ✅ **LLM Strategy:** Stubbed providers (choice deferred)
3. ✅ **Deck Sharing:** Public links with multiple export formats
4. ✅ **Format Priority:** Standard → Commander → Modern (no Legacy)
5. ✅ **Platform:** Web-only with responsive mobile design
6. ✅ **Architecture:** Separate microservice (port 8001)

### Technical Decisions
1. ✅ **Backend:** FastAPI (Python) with WebSockets
2. ✅ **Frontend:** Next.js + React (existing 1.0 stack)
3. ✅ **Database:** PostgreSQL (extend existing schema)
4. ✅ **Agent Framework:** LangChain or LiteLLM (to be decided)
5. ✅ **Deployment:** Separate from 1.0 search API

---

## 🚧 Pending Decisions

### Critical (Before Week 1)
- [ ] **LLM Provider Choice:** GPT-4, Claude, Local, or Hybrid?
- [ ] **OAuth Credentials:** Obtain from Google, Discord, Steam
- [ ] **Agent Framework:** LangChain vs LiteLLM vs custom
- [ ] **Caching Strategy:** Redis vs in-memory

### Important (Before Week 3)
- [ ] **UI Mockups:** Approve chat interface designs
- [ ] **Combo Data Source:** Which combo database to use?
- [ ] **Deployment Target:** VPS, Cloud, or PaaS?

### Nice to Have (Before Launch)
- [ ] **Analytics Platform:** PostHog, Plausible, or none?
- [ ] **Monitoring:** Sentry, DataDog, or self-hosted?
- [ ] **Email Service:** For notifications (optional)

---

## 📈 Project Phases

### Phase 0: Planning (Current)
- ✅ Requirements gathering
- ✅ Architecture planning
- ✅ Document creation
- ⏳ Stakeholder review
- ⏳ Technical decisions finalization

### Phase 1: MVP Development (Weeks 1-6)
**Goal:** Functional deck building and analysis system

**Week 1:** Database + Auth  
**Week 2:** Agent framework + LLM  
**Week 3:** Deck Builder agent  
**Week 4:** Deck Analyzer agent  
**Week 5:** Chat UI + integration  
**Week 6:** Testing + polish  

### Phase 2: Enhanced Features (Weeks 7-12)
- Advanced game solver
- Deck versioning
- Social features
- Performance optimization

### Phase 3: Production Ready (Month 4+)
- Comprehensive testing
- Security hardening
- Documentation
- Deployment
- Monitoring setup

---

## 💡 Key Insights from Existing System

### What We Have (Leverage from 1.0)
- ✅ **509K MTG cards** with embeddings
- ✅ **Hybrid search** (keyword + semantic + advanced) - 90% test pass rate
- ✅ **Rule engine** with 45+ rules, 425K+ card-to-rule mappings
- ✅ **PostgreSQL + pgvector** database
- ✅ **FastAPI server** (port 8000) with 15+ endpoints
- ✅ **Next.js UI** with responsive components
- ✅ **Phi-3.5 mini LLM** already loaded (for query parsing)

### What We Need (Build for 2.0)
- ❌ **Conversational AI layer** (agents, memory, orchestration)
- ❌ **Authentication system** (OAuth, sessions, JWT)
- ❌ **Chat interface** (WebSocket, streaming responses)
- ❌ **Deck management** (save, load, share, export)
- ❌ **Combo database** (seed 500-1000 known combos)
- ❌ **Game state modeling** (board evaluation, basic → advanced)

**Estimated Reuse:** 75% of backend logic, 40% of frontend components

---

## 🎯 Success Metrics (from PROJECT_OVERVIEW.md)

### Functional
- [ ] Build complete deck in <10 conversation turns
- [ ] 80%+ card suggestion relevance
- [ ] 100% format legality accuracy
- [ ] Detect all 2-card combos in deck
- [ ] 95%+ lethal calculation accuracy

### Technical
- [ ] <2s response time (or <500ms streaming)
- [ ] 100+ concurrent chat sessions
- [ ] 99.9% API uptime
- [ ] <3s OAuth login flow
- [ ] <1s deck save/load

### User Experience
- [ ] Mobile-friendly (Google mobile test)
- [ ] WCAG 2.1 AA accessible
- [ ] <2s public deck link load
- [ ] 100% Arena export success rate

---

## 📋 Next Steps

### Immediate Actions
1. **Review all planning documents**
   - Read PROJECT_OVERVIEW.md
   - Scan TECH_STACK.md
   - Review IMPLEMENTATION_ROADMAP.md

2. **Make key decisions**
   - Choose LLM provider
   - Approve architecture approach
   - Get OAuth credentials

3. **Expand stub documents**
   - Detail DATABASE_SCHEMA.md with complete SQL
   - Create API_SPECIFICATION.md with OpenAPI
   - Design UI_DESIGN.md with mockups

4. **Prepare development environment**
   - Set up 2.0 project structure
   - Configure OAuth applications
   - Test LLM provider integration

### Before Development Starts
- [ ] All planning docs approved
- [ ] LLM provider chosen and tested
- [ ] OAuth credentials obtained
- [ ] Database schema finalized
- [ ] UI mockups approved
- [ ] Development environment ready

---

## 🔗 Related Resources

### External Documentation
- **FastAPI:** https://fastapi.tiangolo.com/
- **LangChain:** https://python.langchain.com/docs/get_started/introduction
- **OAuth 2.0:** https://oauth.net/2/
- **MTG Comprehensive Rules:** https://magic.wizards.com/en/rules
- **Commander Spellbook:** https://commanderspellbook.com/

### Existing 1.0 Documentation
- **Hybrid Search:** `/docs/HYBRID_SEARCH_IMPLEMENTATION.md`
- **Test Results:** `/docs/testing/HYBRID_SEARCH_TEST_RESULTS_2025-12-02.md`
- **Rule Engine:** `/specs/RULE_ENGINE_ARCHITECTURE.md`
- **Database Schema:** `/sql/schemas/schema_with_rules.sql`

### Planning Documents (This Folder)
- All `.md` files in `/home/maxwell/vector-mtg/2.0/`

---

## 📞 Questions or Feedback?

This is the **planning phase** - your input is crucial!

**Areas needing decision:**
1. LLM provider choice (cost vs quality tradeoffs)
2. UI/UX preferences for chat interface
3. Priority ordering of features
4. Budget constraints
5. Timeline flexibility

**To discuss:**
- Review PROJECT_OVERVIEW.md first
- Identify any concerns or questions
- Provide feedback on approach
- Approve or request changes

---

## 📝 Document Maintenance

### Version History
- **v1.0** (2024-12-03): Initial planning documents created
  - 11 documents created
  - Core requirements documented
  - Technical decisions outlined
  - 6-week roadmap planned

### To Update
When making changes to planning docs:
1. Update the specific document
2. Update version number at bottom
3. Add note to this README if significant
4. Notify team of changes

---

**Project Status:** 📋 Planning Complete - Ready for Review  
**Next Milestone:** ⏳ Approve plans and begin Week 1 development  
**Timeline:** 6 weeks to MVP after approval  
**Confidence Level:** High (75% leverages existing working system)

---

*This planning was created using the existing vector-mtg 1.0 system as a foundation. The hybrid search system (recently completed) provides excellent infrastructure for the agentic system to build upon.*
