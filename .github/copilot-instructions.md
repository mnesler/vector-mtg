# GitHub Copilot Instructions - MTG Vector Database

## Project Overview

**vector-mtg** is a dual-component MTG (Magic: The Gathering) card search and rule engine application using vector embeddings for semantic search. The project consists of:

1. **Backend**: Python FastAPI server with PostgreSQL (pgvector extension)
2. **Frontend**: Next.js 16 (TypeScript, React 19, Skeleton UI, Tailwind CSS)

**Repository Size**: ~10GB total (2.3GB cards.json, 7.2GB Python venv, 607MB node_modules)
**Dataset**: 509,000+ MTG cards from Scryfall API
**Database**: PostgreSQL 16 with pgvector, running in Docker

---

## Environment Setup

### Python Backend
- **Python Version**: 3.14.0 (uses venv at `/venv/`)
- **Key Dependencies**: sentence-transformers==5.1.2, fastapi==0.121.3, psycopg2-binary==2.9.11, pytest==9.0.1
- **Package Manager**: pip (requirements.txt)

**Setup Commands (always run these in order):**
```bash
# 1. Activate virtual environment (REQUIRED for all Python commands)
source venv/bin/activate

# 2. Install dependencies (if requirements.txt changed)
pip install -r requirements.txt
```

### Frontend (Next.js)
- **Node Version**: v22.21.0
- **NPM Version**: 10.9.4
- **Framework**: Next.js 16.0.4 (App Router), React 19.2.0
- **UI Library**: Skeleton UI 4.5.3 + Tailwind CSS 4.1.17
- **Testing**: Jest 30.2.0 + React Testing Library

**Setup Commands:**
```bash
cd ui
npm install  # Install dependencies
```

### Database
**Start database** (always required before running backend):
```bash
docker compose up -d
# Wait ~5 seconds for database to be ready
```

**Connection Details:**
- Host: localhost:5432
- Database: vector_mtg
- User/Password: postgres/postgres
- Container: vector-mtg-postgres

**Access psql:**
```bash
docker exec -it vector-mtg-postgres psql -U postgres -d vector_mtg
```

---

## Build & Test Commands

### Backend (Python)

**CRITICAL**: Always activate venv before running Python commands:
```bash
source venv/bin/activate
```

**Run Tests** (~5 seconds):
```bash
source venv/bin/activate
python -m pytest tests/ -v
# 13 tests should pass
```

**Run API Server** (requires database running):
```bash
source venv/bin/activate
cd scripts/api
python -m api.api_server_rules
# Server starts on http://localhost:8000
# Takes ~10-15 seconds to load embedding model
```

**Load Cards into Database** (~5-10 minutes for full dataset):
```bash
source venv/bin/activate
python scripts/loaders/load_cards_with_keywords.py
```

**Generate Embeddings** (time-intensive, requires GPU for optimal speed):
```bash
source venv/bin/activate
python scripts/embeddings/generate_embeddings_dual.py
```

### Frontend (Next.js)

**Development Server**:
```bash
cd ui
npm run dev
# Server starts on http://localhost:3000
```

**Build** (~45 seconds, **CURRENTLY FAILS** - TypeScript error in tailwind.config.ts):
```bash
cd ui
npm run build
# ERROR: Type error in tailwind.config.ts line 20 - Miami theme missing required properties
# WORKAROUND: Fix or remove the Miami theme definition before building
```

**Tests** (pass with warnings):
```bash
cd ui
npm test
# Tests pass but show React act() warnings - these are non-blocking
```

**Linting**:
```bash
cd ui
npm run lint
```

---

## Project Structure

### Root Directory
```
/
├── cards.json                    # 2.3GB Scryfall dataset (509K cards)
├── docker-compose.yml            # PostgreSQL + pgAdmin setup
├── requirements.txt              # Python dependencies
├── README.md                     # Main documentation
├── SEARCH_TESTING.md            # Search testing guide
├── scripts/                      # Python backend code
├── sql/                         # Database schemas and migrations
├── specs/                       # Design documentation
├── tests/                       # Python tests (pytest)
├── ui/                          # Next.js frontend
└── venv/                        # Python virtual environment (7.2GB)
```

### Backend Structure (`/scripts/`)
```
scripts/
├── api/
│   ├── api_server_rules.py      # FastAPI server (main entry point)
│   ├── rule_engine.py           # Rule matching engine
│   ├── embedding_service.py     # Sentence-transformer model wrapper
│   └── __init__.py
├── loaders/
│   ├── load_cards.py            # Basic card loader
│   ├── load_cards_with_keywords.py  # Enhanced loader with keyword extraction
│   └── extract_rules.py         # Rule discovery from card clusters
├── embeddings/
│   └── generate_embeddings_dual.py  # Generate card/rule embeddings
└── migrations/
    └── migrate_standard_cards.py    # Data migration utilities
```

### Database Structure (`/sql/`)
```
sql/
├── schemas/
│   ├── schema.sql               # DEPRECATED - use schema_with_rules.sql
│   └── schema_with_rules.sql    # PRIMARY schema (441 lines)
├── seeds/
│   └── seed_rules.sql           # 50+ rule templates (647 lines)
└── migrations/
    ├── README.md                # Migration guidelines
    └── 002_add_is_playable_column.py
```

**IMPORTANT**: Never modify `schema_with_rules.sql` after initial setup. All schema changes MUST use migration scripts in `sql/migrations/`.

### Frontend Structure (`/ui/`)
```
ui/
├── app/                         # Next.js App Router
│   ├── layout.tsx               # Root layout (Skeleton UI theme)
│   ├── page.tsx                 # Home/dashboard page
│   ├── globals.css              # Global styles (Skeleton themes)
│   ├── user/                    # User profile page
│   ├── rules/                   # Rules browser page
│   └── deck/                    # Deck analyzer page
├── components/
│   ├── AppBar.tsx               # Top navigation bar
│   ├── NavigationDrawer.tsx     # Side drawer menu
│   ├── SearchBar.tsx            # Card search component
│   └── ThemeSwitcher.tsx        # Theme toggle
├── lib/                         # Utilities (planned)
│   ├── api.ts                   # FastAPI client
│   └── types.ts                 # TypeScript interfaces
├── public/                      # Static assets
├── package.json                 # Dependencies & scripts
├── tsconfig.json                # TypeScript config
├── tailwind.config.ts           # Tailwind + Skeleton config
├── jest.config.js               # Jest test config
└── next.config.ts               # Next.js config
```

---

## Key Configuration Files

### Backend
- `requirements.txt`: Python dependencies
- `docker-compose.yml`: Database services (PostgreSQL + pgAdmin)
- `sql/schemas/schema_with_rules.sql`: Database schema with pgvector
- `scripts/api/api_server_rules.py`: FastAPI server configuration

### Frontend
- `ui/package.json`: NPM dependencies and scripts
- `ui/tsconfig.json`: TypeScript strict mode enabled
- `ui/tailwind.config.ts`: Skeleton UI themes (wintry, modern, crimson, seafoam, vintage)
- `ui/next.config.ts`: Next.js config with API proxy
- `ui/jest.config.js`: Jest with jsdom environment

---

## Development Workflow

### Making Backend Changes

1. **Activate venv**: `source venv/bin/activate`
2. **Ensure database is running**: `docker compose up -d`
3. **Make code changes**
4. **Run tests**: `python -m pytest tests/ -v`
5. **Test manually**: Start API server and use curl/browser

### Making Frontend Changes

1. **Navigate to UI**: `cd ui`
2. **Ensure dependencies installed**: `npm install`
3. **Start dev server**: `npm run dev`
4. **Make changes** (hot reload enabled)
5. **Run tests**: `npm test`
6. **Lint**: `npm run lint`

### Making Database Changes

**CRITICAL**: Use migrations, never modify schema_with_rules.sql directly.

1. Create migration:
   ```bash
   cat > sql/migrations/$(date +%Y%m%d_%H%M)_description.sql << 'EOF'
   BEGIN;
   ALTER TABLE cards ADD COLUMN IF NOT EXISTS new_field TEXT;
   COMMIT;
   EOF
   ```

2. Apply migration:
   ```bash
   docker exec -i vector-mtg-postgres psql -U postgres -d vector_mtg < sql/migrations/20251130_1234_description.sql
   ```

---

## Common Issues & Workarounds

### UI Build Failure (KNOWN ISSUE)
**Error**: TypeScript error in `tailwind.config.ts:20` - Miami theme missing properties
**Workaround**: Remove or fix the Miami theme definition before building for production

### Python Import Errors
**Issue**: `ModuleNotFoundError` when running Python scripts
**Solution**: Always activate venv first: `source venv/bin/activate`

### Database Connection Refused
**Issue**: Backend can't connect to PostgreSQL
**Solution**: Start database: `docker compose up -d` (wait 5-10 seconds)

### Jest act() Warnings
**Issue**: React Testing Library shows act() warnings
**Status**: Non-blocking, tests pass successfully

### Embedding Model Load Time
**Issue**: API server takes 10-15 seconds to start
**Cause**: Loading sentence-transformers model into memory
**Status**: Expected behavior, not an error

---

## Important Notes for AI Agents

### Skeleton UI Components
The UI uses **Skeleton UI components only**. Always use Skeleton UI classes and patterns:
- Cards: `class="card p-6 bg-surface-100-900"`
- Buttons: `class="btn variant-filled-primary"`
- Inputs: `class="input"`
- Theme-aware colors: `bg-surface-100-900`, `text-surface-600-400`

### Theme Consistency
All pages MUST maintain theme consistency using Skeleton UI's reactive color system. Never hardcode colors - always use Skeleton UI's theme tokens.

### Testing Philosophy
- Backend: pytest with database mocking
- Frontend: Jest + React Testing Library
- Integration: Manual testing via test scripts in `tests/`

### Documentation
Key docs in `/specs/`:
- `IMPLEMENTATION_GUIDE.md`: Setup and architecture
- `RULE_ENGINE_ARCHITECTURE.md`: Rule engine design
- `VISUALIZATION_GUIDE.md`: API documentation
- `TDD-METHODOLOGY.md`: Testing approach

### Trust These Instructions
The information in this file has been validated by running commands and examining the codebase. Only search the codebase if:
1. These instructions are incomplete for your task
2. You find contradictions or errors
3. You need specific implementation details not covered here

---

## Validation Checklist

Before submitting changes:

**Backend:**
- [ ] Virtual environment activated
- [ ] Tests pass: `python -m pytest tests/ -v`
- [ ] Database migrations created (if schema changed)
- [ ] API server starts without errors

**Frontend:**
- [ ] `npm install` completed
- [ ] Tests pass: `npm test`
- [ ] Linter passes: `npm run lint`
- [ ] Dev server runs: `npm run dev`
- [ ] Skeleton UI theme maintained

**Database:**
- [ ] Changes use migrations (not direct schema edits)
- [ ] Migration tested with `psql -f migration.sql`
- [ ] Changes are idempotent (use IF EXISTS/IF NOT EXISTS)
