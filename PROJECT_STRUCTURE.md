# Vector MTG - Multi-Project Repository Structure

This repository contains 4 distinct MTG-related projects with shared infrastructure.

## Project Overview

### 1. **project-rules-engine/** - MTG Game State Solver
Builds a backend system that can represent and solve MTG game states, determine valid next states, and process complex card interactions.

**Status**: In development (basic rule classification exists)
**Tech**: Python, PostgreSQL
**Key Features**: Game state representation, rules processing, interaction resolution

### 2. **project-data-collection/** - LLM Training Data Collection
Scrapes and processes MTG data from multiple sources (EDHREC, Commander Spellbook, Scryfall, Moxfield) with focus on Commander and Standard formats.

**Status**: Active (scrapers working, 43K+ combos collected)
**Tech**: Python, Playwright, PostgreSQL, pgVector
**Key Features**: Web scraping, data enrichment, embedding generation

### 3. **project-llm-deck-builder/** - LLM Deck Building Assistant
Train and deploy an LLM model with LoRA fine-tuning to assist users in building MTG decks.

**Status**: Not started (architecture planning phase)
**Tech**: Python, PyTorch, Hugging Face, LoRA/PEFT
**Key Features**: Model training, deck recommendations, card synergy analysis

### 4. **project-rules-manager/** - Rules Engine Management UI
Web application to build, maintain, and validate the rules engine with human-in-the-loop review and statistics tracking.

**Status**: Basic UI exists (needs rule management features)
**Tech**: Next.js, React, FastAPI
**Key Features**: Rule editor, coverage stats, review queue, test builder

### 5. **shared/** - Common Infrastructure
Shared database schemas, Docker configuration, utilities, and documentation used across all projects.

**Tech**: PostgreSQL 16, pgVector, Docker
**Components**: Database schemas, Docker Compose, common utilities

## Directory Structure

```
vector-mtg/
├── project-rules-engine/          # Game state solver & rules engine
│   ├── backend/                   # Core rules engine logic
│   ├── tests/                     # Rule validation tests
│   └── docs/                      # Architecture documentation
│
├── project-data-collection/       # Data scraping & LLM training data
│   ├── scrapers/                  # EDHREC, Scryfall, Commander Spellbook
│   ├── loaders/                   # Bulk data loading
│   ├── enrichment/                # Data enrichment scripts
│   ├── output/                    # Scraped datasets
│   ├── tests/                     # Scraper validation
│   └── docs/                      # Data source documentation
│
├── project-llm-deck-builder/      # LLM training & inference
│   ├── training/                  # LoRA training scripts
│   ├── models/                    # Model checkpoints & adapters
│   ├── inference/                 # Deck recommendation engine
│   ├── tests/                     # Model quality tests
│   └── docs/                      # Model documentation
│
├── project-rules-manager/         # Rules management application
│   ├── frontend/                  # Next.js UI
│   ├── backend/                   # FastAPI for rule CRUD
│   ├── tests/                     # E2E and integration tests
│   └── docs/                      # User guides
│
├── shared/                        # Common infrastructure
│   ├── database/                  # PostgreSQL schemas & migrations
│   ├── docker/                    # Docker Compose configs
│   ├── utils/                     # Shared utilities
│   └── docs/                      # Architecture docs
│
├── cards.json                     # 509K MTG cards (2.3GB, Scryfall bulk)
├── venv/                          # Python virtual environment
└── PROJECT_STRUCTURE.md           # This file
```

## Project Dependencies

```
┌─────────────────────────────────────────┐
│         shared/database                 │
│   (PostgreSQL schemas, migrations)      │
└─────────────────────────────────────────┘
                  │
                  ▼
    ┌─────────────┬─────────────┬─────────────┐
    │             │             │             │
    ▼             ▼             ▼             ▼
┌─────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ rules-  │ │  data-   │ │   llm-   │ │  rules-  │
│ engine  │ │collection│ │  builder │ │ manager  │
└─────────┘ └──────────┘ └──────────┘ └──────────┘
                  │             │             │
                  └─────────────┴─────────────┘
                         data flows
```

- **shared/database** → Used by all projects
- **data-collection** → Provides training data to **llm-builder**
- **rules-engine** → Managed by **rules-manager** UI
- **llm-builder** → Uses **rules-engine** for validation

## Getting Started

### 1. Setup Shared Infrastructure
```bash
cd shared/docker
docker-compose up -d  # Start PostgreSQL + pgVector + pgAdmin
```

### 2. Load Card Data (Data Collection)
```bash
cd project-data-collection
python scrapers/scrape_edhrec_combos_v2.py  # Scrape combo data
python loaders/load_cards_with_keywords.py  # Load 509K cards into DB
```

### 3. Start Rules Engine (Backend)
```bash
cd project-rules-engine/backend
python api_server.py  # Start FastAPI server
```

### 4. Start Rules Manager (Frontend)
```bash
cd project-rules-manager/frontend
npm install
npm run dev  # Start Next.js UI
```

## Data Assets

- **cards.json** (2.3GB): 509,000+ MTG cards from Scryfall
- **EDHREC combos**: 43,544+ combos across 32 color combinations
- **Commander Spellbook**: 1.2GB combo database
- **Vector embeddings**: Semantic search embeddings in PostgreSQL

## Current Migration Status

- [x] Project structure created
- [ ] Rules engine code migrated
- [ ] Data collection code migrated
- [ ] LLM project initialized
- [ ] Rules manager UI configured
- [ ] Shared infrastructure consolidated
- [ ] Documentation updated

## Development Workflow

1. **Data Collection**: Run scrapers to gather new card/combo data
2. **Rules Development**: Use rules-manager UI to define new rules
3. **LLM Training**: Train models on collected data
4. **Testing**: Validate rules engine against test cases
5. **Deployment**: Deploy API and UI services

## Questions?

See individual project READMEs for detailed information:
- [Rules Engine](./project-rules-engine/README.md)
- [Data Collection](./project-data-collection/README.md)
- [LLM Deck Builder](./project-llm-deck-builder/README.md)
- [Rules Manager](./project-rules-manager/README.md)
- [Shared Infrastructure](./shared/README.md)
