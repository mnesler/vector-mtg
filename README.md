# Vector MTG - Multi-Project Repository

A comprehensive Magic: The Gathering platform combining game state solving, data collection, LLM-powered deck building, and rules management.

## Quick Navigation

**📖 See [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) for detailed architecture and project organization.**

## Projects

| Project | Purpose | Status | Quick Start |
|---------|---------|--------|-------------|
| [project-rules-engine](./project-rules-engine/) | MTG game state solver & rules engine | In Development | - |
| [project-data-collection](./project-data-collection/) | Scrape & process LLM training data | ✅ Active | `python scrapers/scrape_edhrec_combos_v2.py` |
| [project-llm-deck-builder](./project-llm-deck-builder/) | LoRA-tuned LLM for deck building | Planning | - |
| [project-rules-manager](./project-rules-manager/) | UI to manage rules engine | Basic UI | `npm run dev` in frontend/ |
| [shared](./shared/) | Common infrastructure (DB, Docker) | ✅ Active | `docker-compose up -d` in docker/ |

## Current Data Assets

- **509,000+ MTG cards** (cards.json - 2.3GB from Scryfall)
- **43,544+ combos** from EDHREC across 32 color combinations
- **1.2GB combo database** from Commander Spellbook
- **Vector embeddings** in PostgreSQL with pgVector

## Repository Structure

```
vector-mtg/
├── project-rules-engine/          # Game state solver & rules engine
│   ├── backend/                   # Core rules logic, API
│   ├── tests/                     # Rule validation tests
│   └── docs/                      # Architecture docs
│
├── project-data-collection/       # Data scraping for LLM training
│   ├── scrapers/                  # EDHREC, Commander Spellbook, Scryfall
│   ├── loaders/                   # Bulk data loading, embeddings
│   ├── enrichment/                # Data enrichment scripts
│   ├── output/                    # Scraped datasets
│   └── tests/                     # Scraper validation
│
├── project-llm-deck-builder/      # LoRA training & deck recommendations
│   ├── training/                  # LoRA fine-tuning scripts
│   ├── models/                    # Model checkpoints & adapters
│   ├── inference/                 # Deck recommendation engine
│   └── tests/                     # Model quality tests
│
├── project-rules-manager/         # Rules management application
│   ├── frontend/                  # Next.js UI (reused from /ui)
│   ├── backend/                   # FastAPI for rule CRUD
│   └── tests/                     # E2E and integration tests
│
├── shared/                        # Common infrastructure
│   ├── database/                  # PostgreSQL schemas & migrations
│   ├── docker/                    # Docker Compose configs
│   └── utils/                     # Shared utilities
│
├── cards.json                     # 509K card dataset (2.3GB)
├── venv/                          # Python virtual environment
└── README.md                      # This file
```

## Getting Started

### 1. Start Infrastructure
```bash
cd shared/docker
docker-compose up -d
```

This starts:
- PostgreSQL 16 with pgVector extension
- pgAdmin web UI (http://localhost:5050)

**Database Connection:**
- Host: localhost:5432
- Database: vector_mtg
- User/Password: postgres/postgres

### 2. Load Card Data
```bash
cd project-data-collection
python loaders/load_cards_with_keywords.py
```

This loads 509,000+ cards from `cards.json` into PostgreSQL (~5-10 min).

### 3. Scrape Combo Data (Optional)
```bash
cd project-data-collection
python scrapers/scrape_edhrec_combos_v2.py --color-identity UG --save-card-data
```

Options:
- `--color-identity`: Filter by colors (e.g., UG for Simic)
- `--save-card-data`: Include full card details from EDHREC API
- `--max-combos`: Limit number of combos to scrape

### 4. Start Rules Manager UI
```bash
cd project-rules-manager/frontend
npm install
npm run dev
```

Visit http://localhost:3000 for the web interface.

## Migration Notice

**This repository was reorganized on December 7, 2025 into a multi-project structure.**

### Old → New File Locations

| Old Path | New Path | Notes |
|----------|----------|-------|
| `/scripts/api/rule_engine.py` | `project-rules-engine/backend/` | Rules engine core |
| `/scripts/scrape_edhrec_combos_v2.py` | `project-data-collection/scrapers/` | Primary scraper |
| `/scripts/loaders/` | `project-data-collection/loaders/` | Data loading |
| `/ui/` | `project-rules-manager/frontend/` | Next.js UI |
| `/docker-compose.yml` | `shared/docker/` | Infrastructure |
| `/sql/schemas/` | `shared/database/schemas/` | DB schemas |
| `/sql/migrations/` | `shared/database/migrations/` | DB migrations |

**Old files remain in place for backwards compatibility.** New development should use the new structure.

### Why the Reorganization?

The repository evolved over time with multiple experiments and shifting focus. The new structure:
1. **Separates concerns**: Each project has a clear, distinct purpose
2. **Enables focused development**: Work on one area without affecting others
3. **Improves discoverability**: Easier to understand what code does what
4. **Facilitates collaboration**: Clear boundaries between projects
5. **Supports independent scaling**: Each project can grow independently

## Development Focus

### Currently Active
1. ✅ **Data Collection**: EDHREC combo scraping (43K+ combos collected)
2. ✅ **Database**: PostgreSQL with 509K cards loaded
3. ✅ **Semantic Search**: Vector embeddings for card similarity
4. 🔨 **Rules Engine**: Basic classification implemented

### Next Steps
1. 🎯 **Game State Solver**: Build state representation and transition logic (project-rules-engine)
2. 🎯 **LLM Training**: Fine-tune model with LoRA on collected data (project-llm-deck-builder)
3. 🎯 **Rules Manager UI**: Add rule editing and coverage stats (project-rules-manager)
4. 🎯 **Integration**: Connect all projects into unified platform

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, PostgreSQL 16, pgVector
- **Frontend**: Next.js 16, React 19, TypeScript, Tailwind CSS
- **Scraping**: Playwright (browser automation)
- **ML/AI**: PyTorch, Hugging Face Transformers, LoRA/PEFT, sentence-transformers
- **Infrastructure**: Docker, Docker Compose

## Data Sources

- **Scryfall**: 509K+ cards with comprehensive metadata
- **EDHREC**: Combo database, popularity stats, deck recommendations
- **Commander Spellbook**: Comprehensive combo catalog (1.2GB)
- **Moxfield**: Deck lists and archetypes

## Project Documentation

Each project has detailed documentation:
- [Rules Engine Guide](./project-rules-engine/README.md) - Game state solver architecture
- [Data Collection Guide](./project-data-collection/README.md) - Scraper documentation
- [LLM Deck Builder Guide](./project-llm-deck-builder/README.md) - Model training guide
- [Rules Manager Guide](./project-rules-manager/README.md) - UI development guide
- [Shared Infrastructure](./shared/README.md) - Database and Docker setup

## Recent Activity

- ✅ **Dec 7, 2025**: Reorganized into multi-project structure
- ✅ **Dec 6, 2025**: EDHREC combo scraper with full card data enrichment
- ✅ **Dec 6, 2025**: Commander Spellbook full scrape (1.2GB data collected)
- ✅ **Dec 5, 2025**: Semantic search improvements and testing
- ✅ **Dec 5, 2025**: Removed large data files from git tracking

## Legacy Documentation

These guides reference the old structure but contain useful information:
- **[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)** - Original setup guide
- **[RULE_ENGINE_ARCHITECTURE.md](RULE_ENGINE_ARCHITECTURE.md)** - Rule engine design
- **[VISUALIZATION_GUIDE.md](VISUALIZATION_GUIDE.md)** - Visualization and API docs

## Contributing

1. Choose the project you want to work on
2. Read that project's README for specific setup
3. Follow the development workflow in [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md)
4. Submit PRs targeting the appropriate project directory

## Questions?

See [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) for comprehensive architecture and design decisions.

## License

See LICENSE file for details.
