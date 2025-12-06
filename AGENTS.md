# AGENTS.md

**Comprehensive guide for AI agents working in the vector-mtg codebase.**

This document contains essential commands, patterns, conventions, and gotchas discovered from the actual codebase. Everything documented here is based on observed code and configurations.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Essential Commands](#essential-commands)
3. [Environment Setup](#environment-setup)
4. [Code Organization](#code-organization)
5. [Development Workflow](#development-workflow)
6. [Testing Patterns](#testing-patterns)
7. [Code Conventions](#code-conventions)
8. [Database Patterns](#database-patterns)
9. [API Patterns](#api-patterns)
10. [Frontend Patterns](#frontend-patterns)
11. [Important Gotchas](#important-gotchas)
12. [Data Sources](#data-sources)

---

## Project Overview

**vector-mtg** is a dual-component Magic: The Gathering card search and rule engine using vector embeddings for semantic search.

### Technology Stack

**Backend:**
- Python 3.14.0 (virtual environment in `/venv/`)
- FastAPI 0.104.1 + Uvicorn 0.24.0
- PostgreSQL 16 with pgvector extension (Docker)
- sentence-transformers 2.2.2 (ML embeddings)
- pytest 8.3.4 (testing)

**Frontend:**
- Next.js 16.0.4 (App Router)
- React 19.2.0
- TypeScript 5.9.3 (strict mode)
- Skeleton UI 4.5.3 + Tailwind CSS 4.1.17
- Jest 30.2.0 + React Testing Library 16.3.0

**Database:**
- PostgreSQL 16 with pgvector (via Docker)
- 509,000+ MTG cards (2.3GB cards.json)
- Dual embeddings: full card + oracle text only
- Rule extraction and classification system

### Repository Size
- Total: ~10GB
- `cards.json`: 2.3GB
- `venv/`: 7.2GB
- `node_modules/`: 607MB

---

## Essential Commands

### Critical Prerequisite

**ALWAYS activate Python virtual environment before ANY Python command:**

```bash
source venv/bin/activate
```

This is non-negotiable. All Python imports depend on packages in the venv.

### Database Commands

```bash
# Start database (required before running backend)
docker compose up -d
# Wait 5-10 seconds for database to be ready

# Stop database
docker compose down

# Access psql
docker exec -it vector-mtg-postgres psql -U postgres -d vector_mtg

# Apply schema (safe to re-run - uses CREATE IF NOT EXISTS)
docker exec -i vector-mtg-postgres psql -U postgres -d vector_mtg < sql/schemas/schema_with_rules.sql

# Apply migration
docker exec -i vector-mtg-postgres psql -U postgres -d vector_mtg < sql/migrations/YYYYMMDD_HHMM_description.sql

# Seed rules
docker exec -i vector-mtg-postgres psql -U postgres -d vector_mtg < sql/seeds/seed_rules.sql
```

**Database Connection:**
- Host: localhost:5432
- Database: vector_mtg
- User: postgres
- Password: postgres
- Container: vector-mtg-postgres

**pgAdmin (web UI):**
- URL: http://localhost:5050
- Email: admin@admin.com
- Password: admin

### Backend Commands

```bash
# Activate venv (REQUIRED FIRST)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests (~5 seconds, 13 tests)
python -m pytest tests/ -v

# Run API server (requires database running)
cd scripts/api
python -m api.api_server_rules
# Server: http://localhost:8000
# Takes 10-15 seconds to load embedding model

# Load cards into database (~5-10 minutes for 509K cards)
python scripts/loaders/load_cards_with_keywords.py

# Generate embeddings (time-intensive, GPU recommended)
python scripts/embeddings/generate_embeddings_dual.py

# Run search tests
bash tests/run_search_tests.sh
```

### Frontend Commands

```bash
# Navigate to UI directory
cd ui

# Install dependencies
npm install

# Development server
npm run dev
# Server: http://localhost:3000

# Build for production (CURRENTLY FAILS - see Known Issues)
npm run build

# Run tests
npm test

# Run tests in watch mode
npm run test:watch

# Test with coverage
npm run test:coverage

# Lint
npm run lint
```

### Data Collection Scripts

```bash
source venv/bin/activate

# Query data sources
python scripts/query_datasources.py

# Analyze decks
python scripts/deck_analyzer.py

# EDHREC scrapers
python scripts/edhrec_mass_collector.py
python scripts/edhrec_infinite_scroll_scraper.py  # NEW: Optimized infinite scroll
python scripts/edhrec_infinite_scroll_scraper.py --limit=10  # Test with 10 commanders
python scripts/test_edhrec_scraper.py  # Quick test (2 commanders)

# Comprehensive scrapers
python scripts/comprehensive_scrapers.py
python scripts/comprehensive_scrapers_enhanced.py

# Merge data
python scripts/data_merger.py
```

---

## Environment Setup

### Python Setup

1. **Activate venv** (CRITICAL):
   ```bash
   source venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify setup**:
   ```bash
   python --version  # Should show 3.14.0
   which python      # Should point to venv/bin/python
   ```

### Node.js Setup

```bash
cd ui
npm install
```

**Versions:**
- Node: v22.21.0
- NPM: 10.9.4

### Database Setup

```bash
# Start containers
docker compose up -d

# Wait for PostgreSQL to be ready
sleep 10

# Create schema
docker exec -i vector-mtg-postgres psql -U postgres -d vector_mtg < sql/schemas/schema_with_rules.sql

# Seed rules
docker exec -i vector-mtg-postgres psql -U postgres -d vector_mtg < sql/seeds/seed_rules.sql

# Load cards (takes 5-10 minutes)
source venv/bin/activate
python scripts/loaders/load_cards_with_keywords.py
```

---

## Code Organization

### Directory Structure

```
/
├── cards.json                  # 2.3GB Scryfall dataset (509K cards)
├── docker-compose.yml          # PostgreSQL + pgAdmin
├── requirements.txt            # Python dependencies
├── README.md                   # Main docs
├── .github/
│   └── copilot-instructions.md # Comprehensive setup guide
├── sql/
│   ├── schemas/
│   │   ├── schema.sql         # DEPRECATED - DO NOT USE
│   │   └── schema_with_rules.sql  # PRIMARY schema (441 lines)
│   ├── seeds/
│   │   └── seed_rules.sql     # 50+ rule templates (647 lines)
│   └── migrations/
│       ├── README.md          # Migration guidelines
│       └── *.sql              # Migration scripts
├── scripts/                   # Python backend code
│   ├── api/
│   │   ├── api_server_rules.py    # FastAPI server (MAIN ENTRY POINT)
│   │   ├── rule_engine.py         # Rule matching engine
│   │   ├── embedding_service.py   # Sentence-transformer wrapper
│   │   ├── query_parser_service.py
│   │   ├── advanced_query_parser.py
│   │   └── __init__.py
│   ├── loaders/
│   │   ├── load_cards.py          # Basic card loader
│   │   └── load_cards_with_keywords.py  # Enhanced loader (USE THIS)
│   ├── embeddings/
│   │   └── generate_embeddings_dual.py
│   ├── migrations/
│   │   └── migrate_standard_cards.py
│   └── [various scraping scripts]
├── tests/
│   ├── test_api_search.py
│   ├── test_advanced_query_parser.py
│   ├── test_search_fixtures.py
│   ├── run_search_tests.sh
│   └── SEARCH_TEST_CASES.md
├── ui/                        # Next.js frontend
│   ├── app/                   # App Router pages
│   │   ├── layout.tsx         # Root layout (Skeleton UI theme)
│   │   ├── page.tsx           # Home/dashboard
│   │   ├── globals.css        # Global styles + themes
│   │   ├── user/              # User profile page
│   │   ├── rules/             # Rules browser
│   │   └── deck/              # Deck analyzer
│   ├── components/
│   │   ├── AppBar.tsx
│   │   ├── NavigationDrawer.tsx
│   │   ├── SearchBar.tsx      # Main search component
│   │   └── ThemeSwitcher.tsx
│   ├── lib/                   # Utilities
│   │   ├── api.ts             # FastAPI client
│   │   └── types.ts           # TypeScript interfaces
│   ├── package.json
│   ├── tsconfig.json          # Strict mode enabled
│   ├── tailwind.config.ts     # Skeleton UI + Tailwind config
│   ├── jest.config.js
│   └── next.config.ts
├── ui-proto/                  # HTML prototype (for reference)
├── specs/                     # Design documentation
│   ├── IMPLEMENTATION_GUIDE.md
│   ├── RULE_ENGINE_ARCHITECTURE.md
│   ├── VISUALIZATION_GUIDE.md
│   ├── TDD-METHODOLOGY.md
│   └── [other specs]
├── docs/                      # Additional documentation
├── data_sources/              # Collected MTG data
│   ├── manifest.json
│   ├── edhrec/
│   ├── moxfield/
│   ├── scryfall/
│   └── scryfall_commander/
├── data_sources_comprehensive/  # Extended data collection
└── venv/                      # Python virtual environment (7.2GB)
```

### Module Organization

**Python modules use relative imports within scripts/:**
```python
# In scripts/api/api_server_rules.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.rule_engine import MTGRuleEngine
from api.embedding_service import get_embedding_service
```

**Frontend uses path alias `@/`:**
```typescript
// In Next.js components
import SearchBar from "../components/SearchBar"  // Relative
import { apiClient } from "@/lib/api"            // Alias to root
```

---

## Development Workflow

### Backend Development Cycle

1. **Activate venv**:
   ```bash
   source venv/bin/activate
   ```

2. **Ensure database is running**:
   ```bash
   docker compose up -d
   sleep 5
   ```

3. **Make code changes**

4. **Run tests**:
   ```bash
   python -m pytest tests/ -v
   ```

5. **Test manually**:
   ```bash
   cd scripts/api
   python -m api.api_server_rules
   # Test with curl or browser at http://localhost:8000
   ```

### Frontend Development Cycle

1. **Navigate to UI directory**:
   ```bash
   cd ui
   ```

2. **Ensure dependencies installed**:
   ```bash
   npm install
   ```

3. **Start dev server**:
   ```bash
   npm run dev
   # Hot reload enabled - changes appear immediately
   ```

4. **Make changes**

5. **Run tests**:
   ```bash
   npm test
   ```

6. **Lint**:
   ```bash
   npm run lint
   ```

### Database Migration Workflow

**CRITICAL: Never modify `schema_with_rules.sql` after initial setup. Always use migrations.**

1. **Create migration file**:
   ```bash
   cat > sql/migrations/$(date +%Y%m%d_%H%M)_description.sql << 'EOF'
   -- Migration: [Brief description]
   -- Created: $(date +%Y-%m-%d)
   -- Author: [Your name]

   BEGIN;

   -- Add your schema changes here
   ALTER TABLE cards ADD COLUMN IF NOT EXISTS new_field TEXT;
   CREATE INDEX IF NOT EXISTS idx_cards_new_field ON cards(new_field);

   COMMIT;

   -- Rollback (optional)
   -- BEGIN;
   -- DROP INDEX IF EXISTS idx_cards_new_field;
   -- ALTER TABLE cards DROP COLUMN IF EXISTS new_field;
   -- COMMIT;
   EOF
   ```

2. **Test migration locally**:
   ```bash
   docker exec -i vector-mtg-postgres psql -U postgres -d vector_mtg < sql/migrations/YYYYMMDD_HHMM_description.sql
   ```

3. **Verify changes**:
   ```bash
   docker exec -it vector-mtg-postgres psql -U postgres -d vector_mtg
   \d cards  -- Check table structure
   ```

**Migration Best Practices:**
- Always use `IF NOT EXISTS` / `IF EXISTS` (idempotent)
- Use transactions (`BEGIN`/`COMMIT`)
- Document rollback steps
- One logical change per migration
- Never modify existing migrations

---

## Testing Patterns

### Backend Testing (pytest)

**Test File Naming:**
- `test_*.py` in `tests/` directory
- Example: `test_api_search.py`, `test_advanced_query_parser.py`

**Test Structure:**
```python
import pytest
from unittest.mock import Mock, patch, MagicMock

@pytest.fixture
def mock_db_cursor():
    """Mock database cursor for testing."""
    cursor = MagicMock()
    cursor.fetchall = Mock(return_value=[])
    cursor.__enter__ = Mock(return_value=cursor)
    cursor.__exit__ = Mock(return_value=False)
    return cursor

class TestFeatureName:
    """Test suite for feature."""

    def test_specific_behavior(self, mock_db_cursor):
        """Test that specific behavior works correctly."""
        # Arrange
        mock_data = {'id': '123', 'name': 'Test Card'}
        
        # Act
        result = some_function(mock_data)
        
        # Assert
        assert result['name'] == 'Test Card'
```

**Common Patterns:**
- Mock database connections with `patch('api.api_server_rules.psycopg2.connect')`
- Mock FastAPI TestClient for API tests
- Use `RealDictCursor` for dict-like results
- Test both success and error cases

**Running Tests:**
```bash
source venv/bin/activate
python -m pytest tests/ -v                    # All tests
python -m pytest tests/test_api_search.py -v  # Specific file
python -m pytest tests/ -k "keyword_search"   # Filter by name
```

**Expected Output:**
```
13 tests should pass
~5 seconds total runtime
```

### Frontend Testing (Jest + React Testing Library)

**Test File Naming:**
- `*.test.tsx` or `*.test.ts` next to component files
- Example: `SearchBar.test.tsx`

**Test Structure:**
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import SearchBar from './SearchBar';

describe('SearchBar', () => {
  it('should render search input', () => {
    render(<SearchBar />);
    const input = screen.getByLabelText('Search cards');
    expect(input).toBeInTheDocument();
  });

  it('should call onSearchResults when search is triggered', async () => {
    const mockOnSearchResults = jest.fn();
    render(<SearchBar onSearchResults={mockOnSearchResults} />);
    
    const input = screen.getByLabelText('Search cards');
    fireEvent.change(input, { target: { value: 'lightning bolt' } });
    
    await waitFor(() => {
      expect(mockOnSearchResults).toHaveBeenCalled();
    });
  });
});
```

**Running Tests:**
```bash
cd ui
npm test                # Run all tests
npm run test:watch      # Watch mode
npm run test:coverage   # With coverage
```

**Known Issue: React act() warnings**
- Tests pass successfully but show `act()` warnings
- Non-blocking - these warnings don't indicate test failures
- Related to async state updates in React 19

### TDD Philosophy (from specs/TDD-METHODOLOGY.md)

This project enforces **strict Test-Driven Development**:

1. **RED**: Write failing test first
2. **GREEN**: Write minimum code to pass test
3. **REFACTOR**: Improve code while keeping tests green

**Requirements:**
- No production code without tests written first
- Minimum 90% code coverage for new code
- 100% coverage for critical paths
- Tests must be independent, deterministic, fast (<5ms per unit test)

**Prohibited:**
- Writing implementation before tests
- Skipping tests for "simple" changes
- Commenting out failing tests
- Using `test.skip()` without documented reason

---

## Code Conventions

### Python Conventions

**File Headers:**
```python
#!/usr/bin/env python3
"""
Module description.
Brief explanation of purpose.
"""
```

**Database Configuration Pattern:**
```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'vector_mtg',
    'user': 'postgres',
    'password': 'postgres'
}
```

**Import Organization:**
```python
# Standard library
import sys
import os
from typing import List, Dict, Optional

# Third-party
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException

# Local
from api.rule_engine import MTGRuleEngine
```

**Path Setup for Imports:**
```python
# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

**Database Query Pattern:**
```python
with conn.cursor(cursor_factory=RealDictCursor) as cursor:
    cursor.execute("""
        SELECT id, name, oracle_text
        FROM cards
        WHERE name = %s
    """, (card_name,))
    result = cursor.fetchone()
```

**Batch Processing Pattern:**
```python
from psycopg2.extras import execute_batch

BATCH_SIZE = 1000
batch = []

for item in items:
    batch.append((item['id'], item['name']))
    
    if len(batch) >= BATCH_SIZE:
        execute_batch(cursor, "INSERT INTO cards VALUES (%s, %s)", batch)
        batch = []

# Don't forget remaining items
if batch:
    execute_batch(cursor, "INSERT INTO cards VALUES (%s, %s)", batch)
```

**Keyword Extraction Pattern (from load_cards_with_keywords.py):**
```python
EVERGREEN_KEYWORDS = [
    'flying', 'first strike', 'deathtouch', 'haste', ...
]

ABILITY_PATTERNS = [
    (r'enters the battlefield', 'etb'),
    (r'when.*dies', 'dies_trigger'),
    (r'draw.*card', 'card_draw'),
    ...
]

def extract_keywords(oracle_text):
    keywords = []
    text_lower = oracle_text.lower()
    
    for keyword in EVERGREEN_KEYWORDS:
        if keyword in text_lower:
            keywords.append(keyword)
    
    for pattern, tag in ABILITY_PATTERNS:
        if re.search(pattern, text_lower):
            keywords.append(tag)
    
    return keywords
```

### TypeScript/React Conventions

**Component File Structure:**
```typescript
'use client';  // For client components in Next.js

import { useState, useEffect } from 'react';

interface ComponentProps {
  prop1: string;
  prop2?: number;  // Optional
  onEvent?: () => void;
}

export default function ComponentName({
  prop1,
  prop2 = 0,  // Default value
  onEvent
}: ComponentProps) {
  const [state, setState] = useState<string>('');
  
  // Component logic
  
  return (
    <div className="skeleton-class-names">
      {/* JSX */}
    </div>
  );
}
```

**Type Definitions:**
```typescript
interface Card {
  id: string;
  name: string;
  mana_cost: string;
  cmc: number;
  type_line: string;
  oracle_text: string;
  keywords: string[];
  similarity?: number;  // Optional for search results
}

type SearchMode = 'keyword' | 'semantic';
```

**API Call Pattern:**
```typescript
const performSearch = async (query: string, mode: SearchMode) => {
  try {
    const endpoint = mode === 'keyword'
      ? `/api/cards/keyword?query=${encodeURIComponent(query)}&limit=10`
      : `/api/cards/semantic?query=${encodeURIComponent(query)}&limit=10`;

    const response = await fetch(`http://localhost:8000${endpoint}`);

    if (!response.ok) {
      throw new Error(`Search failed: ${response.statusText}`);
    }

    const data = await response.json();
    return data.cards || [];
  } catch (error) {
    console.error('Search error:', error);
    return [];
  }
};
```

**Debounced Search Pattern (from SearchBar.tsx):**
```typescript
useEffect(() => {
  // Only auto-search for keyword mode
  if (searchMode === 'keyword') {
    const debounceTimer = setTimeout(() => {
      if (searchQuery.trim()) {
        performSearch(searchQuery, searchMode);
      }
    }, 300);  // 300ms debounce

    return () => clearTimeout(debounceTimer);
  }
}, [searchQuery, searchMode]);
```

**Infinite Scroll Pattern (from page.tsx):**
```typescript
const observerTarget = useRef<HTMLTableRowElement>(null);

useEffect(() => {
  const observer = new IntersectionObserver(
    entries => {
      if (entries[0].isIntersecting && hasMore && !isLoadingMore) {
        loadMore();
      }
    },
    { threshold: 0.1 }
  );

  if (observerTarget.current) {
    observer.observe(observerTarget.current);
  }

  return () => observer.disconnect();
}, [hasMore, isLoadingMore, loadMore]);
```

### Skeleton UI Patterns

**CRITICAL: All UI components MUST use Skeleton UI classes only. Never hardcode colors.**

**Common Patterns:**
```typescript
// Cards
<div className="card p-6 bg-surface-100-900">

// Buttons
<button className="btn variant-filled-primary">
<button className="btn variant-soft-surface">
<button className="btn btn-icon btn-sm">

// Inputs
<input className="input variant-form-material" />

// Theme-aware colors (light/dark mode)
<div className="bg-surface-100-900">        // Background
<div className="text-surface-600-400">      // Text
<div className="border-surface-300-700">    // Border

// Tables
<table className="table table-hover">

// Navigation
<nav className="list-nav">
  <a href="/" className="hover:variant-soft-primary">
```

**Theme System:**
- Default theme: `wintry` (set in `app/layout.tsx`)
- Available themes: wintry, modern, crimson, seafoam, vintage
- Theme switcher component available
- All colors use reactive tokens (format: `property-light-dark`)

**NEVER do this:**
```typescript
// ❌ WRONG - Hardcoded colors
<div className="bg-blue-500 text-white">

// ✅ CORRECT - Skeleton UI tokens
<div className="variant-filled-primary">
```

---

## Database Patterns

### Schema Structure

**Primary Tables:**
- `cards` - 509K+ MTG cards with dual embeddings
- `rules` - Extracted rule templates
- `rule_categories` - Hierarchical rule organization
- `card_rules` - Card-to-rule mappings with parameters
- `rule_interactions` - Combo/synergy detection
- `keyword_abilities` - Keyword definitions

**Key Columns:**
```sql
-- cards table
id UUID PRIMARY KEY
name VARCHAR(255) NOT NULL
oracle_text TEXT
keywords TEXT[]                    -- Extracted keywords
embedding vector(1536)             -- Full card embedding
oracle_embedding vector(1536)      -- Oracle text only
data JSONB                         -- Full Scryfall JSON

-- rules table
id UUID PRIMARY KEY
rule_name VARCHAR(255) UNIQUE
rule_template TEXT                 -- "Destroy target [card_type]"
rule_pattern TEXT                  -- Regex pattern
parameters JSONB                   -- Parameter schema
embedding vector(1536)             -- Rule embedding
confidence DECIMAL DEFAULT 1.0     -- 0-1 confidence score
is_manual BOOLEAN DEFAULT FALSE    -- Manual vs auto-extracted
```

### Query Patterns

**Semantic Search (vector similarity):**
```python
cursor.execute("""
    SELECT id, name, oracle_text,
           1 - (embedding <=> %s::vector) as similarity
    FROM cards
    WHERE embedding IS NOT NULL
    ORDER BY embedding <=> %s::vector
    LIMIT %s
""", (query_embedding, query_embedding, limit))
```

**Keyword Search (full-text):**
```python
cursor.execute("""
    SELECT id, name, oracle_text, keywords
    FROM cards
    WHERE name ILIKE %s
       OR oracle_text ILIKE %s
    LIMIT %s
""", (f'%{query}%', f'%{query}%', limit))
```

**Array Contains:**
```python
cursor.execute("""
    SELECT * FROM cards
    WHERE %s = ANY(keywords)
""", ('flying',))
```

**JSONB Queries:**
```python
cursor.execute("""
    SELECT * FROM rules
    WHERE parameters @> %s::jsonb
""", ('{"target_type": "creature"}',))
```

### Index Usage

**Existing Indexes:**
```sql
-- Vector similarity (created by pgvector)
CREATE INDEX idx_cards_embedding ON cards 
USING ivfflat (embedding vector_cosine_ops);

CREATE INDEX idx_cards_oracle_embedding ON cards 
USING ivfflat (oracle_embedding vector_cosine_ops);

-- Text search
CREATE INDEX idx_cards_name ON cards(name);
CREATE INDEX idx_cards_type_line ON cards(type_line);

-- Array search
CREATE INDEX idx_cards_keywords ON cards USING GIN(keywords);
CREATE INDEX idx_cards_colors ON cards USING GIN(colors);

-- JSONB
CREATE INDEX idx_rules_parameters ON rules USING GIN(parameters);
```

---

## API Patterns

### FastAPI Server Structure

**Lifespan Management:**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage database connection and embedding service lifecycle."""
    global db_conn
    print("Starting API server...")
    db_conn = psycopg2.connect(**DB_CONFIG)
    print("✓ Database connected")
    
    # Load ML models (takes 10-15 seconds)
    print("Loading embedding model...")
    get_embedding_service()
    print("✓ Embedding service ready")
    
    yield
    
    print("Shutting down API server...")
    if db_conn:
        db_conn.close()
    print("✓ Database disconnected")

app = FastAPI(
    title="MTG Rule Engine API",
    version="1.0.0",
    lifespan=lifespan
)
```

**CORS Configuration:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Pydantic Models:**
```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class CardResponse(BaseModel):
    id: str
    name: str
    mana_cost: Optional[str]
    cmc: Optional[float]
    type_line: str
    oracle_text: Optional[str]
    keywords: Optional[List[str]]

class SearchResponse(BaseModel):
    query: str
    search_type: str
    count: int
    has_more: bool
    cards: List[CardResponse]
```

**Endpoint Pattern:**
```python
@app.get("/api/cards/keyword")
async def keyword_search(
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Keyword-based card search."""
    # Validate
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    # Query database
    with db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("""
            SELECT id, name, oracle_text
            FROM cards
            WHERE name ILIKE %s
            LIMIT %s OFFSET %s
        """, (f'%{query}%', limit, offset))
        results = cursor.fetchall()
    
    # Return response
    return {
        "query": query,
        "search_type": "keyword",
        "count": len(results),
        "has_more": len(results) == limit,
        "cards": results
    }
```

**Error Handling:**
```python
try:
    # Operation
    result = perform_operation()
except psycopg2.Error as e:
    raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
except ValueError as e:
    raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
```

### Embedding Service Pattern

**Singleton Pattern:**
```python
_embedding_service = None

def get_embedding_service():
    """Get or create singleton embedding service."""
    global _embedding_service
    if _embedding_service is None:
        from sentence_transformers import SentenceTransformer
        print("Loading sentence-transformers model...")
        _embedding_service = SentenceTransformer('all-MiniLM-L6-v2')
        print("Model loaded successfully")
    return _embedding_service
```

**Usage:**
```python
service = get_embedding_service()
embedding = service.encode("Lightning Bolt deals 3 damage")
# Returns numpy array of shape (1536,)
```

---

## Frontend Patterns

### Next.js App Router Structure

**Root Layout (app/layout.tsx):**
```typescript
'use client';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" data-theme="wintry">
      <body>
        <AppBar onMenuClick={() => setIsDrawerOpen(true)} />
        <NavigationDrawer isOpen={isDrawerOpen} onClose={() => setIsDrawerOpen(false)} />
        {children}
      </body>
    </html>
  );
}
```

**Page Component (app/page.tsx):**
```typescript
'use client';

export default function Home() {
  const [searchResults, setSearchResults] = useState<Card[]>([]);
  
  return (
    <div className="container mx-auto px-4 py-8">
      <SearchBar onSearchResults={setSearchResults} />
      {/* Display results */}
    </div>
  );
}
```

**Nested Routes:**
- `app/page.tsx` → `/`
- `app/user/page.tsx` → `/user`
- `app/rules/page.tsx` → `/rules`
- `app/deck/page.tsx` → `/deck`

### Component Patterns

**Search Component (from SearchBar.tsx):**
- Dual mode: keyword (auto-search with debounce) vs semantic (on Enter)
- Inline mode toggle buttons
- Floating tooltips using `@floating-ui/dom`
- Loading states

**Card Display Pattern:**
```typescript
<table className="table table-hover">
  <tbody>
    {searchResults.map((card) => (
      <tr key={card.id} className="cursor-pointer hover:variant-soft-primary">
        <td className="font-semibold">{card.name}</td>
        <td>{card.type_line}</td>
        <td className="text-sm opacity-80">{card.oracle_text}</td>
        {card.similarity && (
          <td className="text-right">{(card.similarity * 100).toFixed(1)}%</td>
        )}
      </tr>
    ))}
  </tbody>
</table>
```

### State Management

**Use React hooks for local state:**
```typescript
const [state, setState] = useState<Type>(initialValue);
const [isLoading, setIsLoading] = useState(false);
```

**No global state management library (Redux, Zustand) - keep state local**

### TypeScript Configuration

**Strict mode enabled (tsconfig.json):**
```json
{
  "compilerOptions": {
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noEmit": true
  }
}
```

**Path alias:**
```json
"paths": {
  "@/*": ["./*"]
}
```

Usage:
```typescript
import { apiClient } from "@/lib/api"      // Absolute from ui/
import SearchBar from "../components/SearchBar"  // Relative
```

---

## Important Gotchas

### Critical: Python Virtual Environment

**MUST activate venv before ANY Python command:**
```bash
source venv/bin/activate
```

**Symptoms of forgotten activation:**
- `ModuleNotFoundError: No module named 'sentence_transformers'`
- `ModuleNotFoundError: No module named 'fastapi'`
- Python using system packages instead of project packages

**How to verify:**
```bash
which python
# Should show: /home/maxwell/vector-mtg/venv/bin/python
# NOT: /usr/bin/python
```

### Database Must Be Running

**API server requires database:**
```bash
docker compose up -d
sleep 5  # Wait for PostgreSQL to be ready
```

**Symptoms:**
- `psycopg2.OperationalError: could not connect to server`
- Connection refused on localhost:5432

**How to verify:**
```bash
docker ps | grep vector-mtg-postgres
# Should show container running
```

### Schema Modification Rules

**NEVER modify `sql/schemas/schema_with_rules.sql` after initial setup.**

**Why:**
- It's the initial schema, not a migration
- Changes won't be applied to existing databases
- Creates divergence between fresh installs and migrated databases

**Instead:**
- Create migration in `sql/migrations/`
- Use timestamped filename: `YYYYMMDD_HHMM_description.sql`
- Make idempotent (use `IF NOT EXISTS` / `IF EXISTS`)
- Document rollback

### Deprecated Files

**DO NOT USE:**
- `sql/schemas/schema.sql` - DEPRECATED, use `schema_with_rules.sql`
- `scripts/loaders/load_cards.py` - Use `load_cards_with_keywords.py` instead

**Check comments in files for deprecation warnings.**

### Embedding Model Load Time

**API server takes 10-15 seconds to start.**

**Why:**
- Loading sentence-transformers model into memory
- Model size: ~100MB
- One-time cost per server startup

**This is normal behavior, not an error:**
```
Starting API server...
✓ Database connected
Loading embedding model...
✓ Embedding service ready  # <-- Takes 10-15 seconds
```

### Frontend Build Failure (Known Issue)

**`npm run build` currently fails:**
```
Error: Type error in tailwind.config.ts:20
Miami theme missing required properties
```

**Workaround:**
- Remove or fix Miami theme definition in `tailwind.config.ts`
- Or use `npm run dev` for development (works fine)

**Status:** Known issue, does not affect development server

### Jest act() Warnings

**Frontend tests show act() warnings but PASS:**
```
Warning: An update to Component inside a test was not wrapped in act(...)
```

**Status:**
- Non-blocking warnings
- Tests still pass successfully
- Related to React 19 + React Testing Library
- Can be safely ignored

### Large File Sizes

**Repository contains large files:**
- `cards.json`: 2.3GB (excluded from git)
- `venv/`: 7.2GB (excluded from git)
- `node_modules/`: 607MB (excluded from git)

**Never commit these to git** - check `.gitignore`:
```gitignore
cards.json
venv/
node_modules/
```

### Import Path Patterns

**Python scripts require path setup:**
```python
# At top of script in scripts/ subdirectory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

**Why:**
- Allows `from api.module import Class` imports
- Without this: `ModuleNotFoundError: No module named 'api'`

### Database Connection Pooling

**Current implementation uses single connection:**
```python
db_conn = psycopg2.connect(**DB_CONFIG)
```

**Implications:**
- Not thread-safe for concurrent requests
- For production: use connection pooling (psycopg2.pool)
- For development/testing: current implementation is fine

### Card Data Format

**cards.json is a JSON array, not JSONL:**
```json
[
  {"id": "...", "name": "..."},
  {"id": "...", "name": "..."}
]
```

**Use ijson for streaming:**
```python
import ijson

with open('cards.json', 'rb') as f:
    for card in ijson.items(f, 'item'):
        process_card(card)
```

**Don't use `json.load()` - will try to load 2.3GB into memory**

---

## Data Sources

### Available Data Sources (data_sources/)

```
data_sources/
├── manifest.json          # Data source registry
├── edhrec/               # EDHREC deck data
├── moxfield/             # Moxfield deck data
├── scryfall/             # Scryfall bulk data
└── scryfall_commander/   # Commander-specific Scryfall data
```

### Extended Data (data_sources_comprehensive/)

```
data_sources_comprehensive/
├── comprehensive_decks/
├── tappedout/
├── scryfall_bulk/
├── scryfall/
├── moxfield_decks/
├── merged_data/
├── edhrec_full/
├── edhrec_comprehensive/
├── edhrec/
├── deck_analysis/
└── card_prices/
```

### Data Collection Scripts

**Query existing data:**
```bash
source venv/bin/activate
python scripts/query_datasources.py
```

**Scrape new data:**
```bash
source venv/bin/activate
python scripts/comprehensive_scrapers.py  # Basic scraper
python scripts/comprehensive_scrapers_enhanced.py  # Enhanced scraper
python scripts/edhrec_mass_collector.py  # EDHREC-specific
python scripts/edhrec_selenium_scraper.py  # Browser automation
```

**Analyze decks:**
```bash
source venv/bin/activate
python scripts/deck_analyzer.py
```

**Merge data:**
```bash
source venv/bin/activate
python scripts/data_merger.py
```

### Primary Data Source: Scryfall

**cards.json source:**
- URL: https://scryfall.com/docs/api/bulk-data
- Format: JSON array
- Size: 2.3GB
- Cards: 509,000+
- Updated: Regularly (download fresh for updates)

**Card Object Structure:**
- Core: id, name, oracle_id, lang
- Gameplay: mana_cost, cmc, type_line, oracle_text, keywords
- Colors: colors, color_identity, produced_mana
- Set: set, set_name, released_at, collector_number
- Legality: legalities object (standard, modern, commander, etc.)
- Images: image_uris object

---

## Documentation Files

### Essential Reading

**Setup & Architecture:**
- `.github/copilot-instructions.md` - Comprehensive setup guide (THIS IS THE SOURCE OF TRUTH)
- `README.md` - Quick start and overview
- `specs/IMPLEMENTATION_GUIDE.md` - Detailed implementation walkthrough
- `specs/RULE_ENGINE_ARCHITECTURE.md` - Rule engine design

**Testing:**
- `specs/TDD-METHODOLOGY.md` - Strict TDD guidelines
- `specs/TDD_UI_TESTING_PLAN.md` - UI testing approach
- `tests/SEARCH_TEST_CASES.md` - Search test scenarios

**Database:**
- `sql/migrations/README.md` - Migration best practices
- `specs/VISUALIZATION_GUIDE.md` - API documentation

**Data Sources:**
- `DATASOURCE_IMPLEMENTATION_SUMMARY.md`
- `DATASOURCE_QUERY_README.md`
- `EDH_DATASOURCES_GUIDE.md`
- `EDH_DATASOURCES_FINAL_SUMMARY.md`
- `QUICK_START_DATASOURCES.md`
- `COMPREHENSIVE_SCRAPING_STRATEGY.md`

### Trust But Verify

**The `.github/copilot-instructions.md` file is the most comprehensive and validated source.**

Only search the codebase if:
1. These instructions are incomplete for your task
2. You find contradictions or errors
3. You need specific implementation details not covered

---

## Quick Reference Cheatsheet

### Most Common Commands

```bash
# Start database
docker compose up -d && sleep 5

# Backend
source venv/bin/activate
python -m pytest tests/ -v
cd scripts/api && python -m api.api_server_rules

# Frontend
cd ui && npm run dev
cd ui && npm test

# Database
docker exec -it vector-mtg-postgres psql -U postgres -d vector_mtg
docker exec -i vector-mtg-postgres psql -U postgres -d vector_mtg < sql/migrations/file.sql
```

### Key URLs

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs (FastAPI auto-generated)
- pgAdmin: http://localhost:5050

### Key Directories

- `/scripts/api/` - FastAPI server and rule engine
- `/ui/app/` - Next.js pages (App Router)
- `/ui/components/` - React components
- `/tests/` - Python tests
- `/sql/schemas/` - Database schema
- `/sql/migrations/` - Schema changes
- `/specs/` - Design documentation

### Key Files

- `scripts/api/api_server_rules.py` - API entry point
- `scripts/loaders/load_cards_with_keywords.py` - Card loader
- `ui/app/layout.tsx` - Root layout
- `ui/components/SearchBar.tsx` - Main search component
- `sql/schemas/schema_with_rules.sql` - Primary schema
- `requirements.txt` - Python dependencies
- `ui/package.json` - Node dependencies

---

## Validation Checklist

**Before committing changes:**

**Backend:**
- [ ] Virtual environment activated
- [ ] Tests pass: `python -m pytest tests/ -v`
- [ ] Database migrations created (if schema changed)
- [ ] API server starts without errors
- [ ] No hardcoded credentials or secrets

**Frontend:**
- [ ] `npm install` completed
- [ ] Tests pass: `npm test`
- [ ] Linter passes: `npm run lint`
- [ ] Dev server runs: `npm run dev`
- [ ] Skeleton UI theme maintained (no hardcoded colors)
- [ ] TypeScript strict mode satisfied

**Database:**
- [ ] Changes use migrations (not direct schema edits)
- [ ] Migration tested with `psql -f migration.sql`
- [ ] Changes are idempotent (use IF EXISTS/IF NOT EXISTS)
- [ ] Rollback documented

**General:**
- [ ] No large files (cards.json, venv/, node_modules/) committed
- [ ] Documentation updated if behavior changed
- [ ] No debug print statements left in code

---

## Emergency Troubleshooting

### "Module not found" errors
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "Connection refused" errors
```bash
docker compose down
docker compose up -d
sleep 10
```

### Database is in weird state
```bash
docker compose down -v  # WARNING: Deletes all data
docker compose up -d
sleep 10
docker exec -i vector-mtg-postgres psql -U postgres -d vector_mtg < sql/schemas/schema_with_rules.sql
```

### Frontend won't build
```bash
cd ui
rm -rf .next node_modules
npm install
npm run dev
```

### Tests failing mysteriously
```bash
# Backend
source venv/bin/activate
pip install --upgrade -r requirements.txt
python -m pytest tests/ -v --tb=short

# Frontend
cd ui
rm -rf node_modules package-lock.json
npm install
npm test
```

---

**Last Updated:** 2024-12-04

**Codebase Version:** Main branch (commit 30133d9)

This document is based on actual observed code and should be updated when significant architectural changes occur.
