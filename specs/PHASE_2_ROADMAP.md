# Phase 2 Roadmap - MTG Rule Engine Enhancements

## Overview

This document outlines the roadmap for Phase 2 enhancements to the MTG Rule Engine. Phase 1 successfully completed the core infrastructure:

- ✅ Database schema with vector embeddings
- ✅ Card and rule data loading (508K+ cards, 45 rules)
- ✅ Vector similarity matching (425K+ card-rule mappings)
- ✅ Rule engine Python library
- ✅ REST API server

Phase 2 focuses on expanding capabilities, improving usability, and adding advanced features.

---

## 1. Web Frontend Development

**Goal**: Create an interactive web interface for exploring cards, rules, and deck analysis.

### Tech Stack Options

**Option A: Simple HTML/JS** (Fast, no build step)
- Vanilla JavaScript + Tailwind CSS
- Direct API calls via Fetch
- Single-page application

**Option B: React** (Modern, component-based)
- React + Vite
- Tailwind CSS or Material-UI
- TypeScript for type safety

**Option C: Next.js** (Full-stack, SEO-friendly)
- Server-side rendering
- API routes for backend logic
- Built-in optimization

**Recommended: Option A** (for rapid prototyping)

### Implementation Steps

#### Step 1.1: Setup Frontend Project Structure

```bash
# Create frontend directory
mkdir frontend
cd frontend

# Create basic structure
mkdir -p {css,js,components,assets}
touch index.html css/styles.css js/app.js
```

#### Step 1.2: Core Pages

**Page 1: Dashboard** (`index.html`)
- Overall statistics display
- Top 10 rules visualization
- Quick search bar
- Recent activity feed

**Page 2: Card Explorer** (`cards.html`)
- Search cards by name
- Filter by rule category
- Display card details with matched rules
- Similar cards viewer

**Page 3: Rule Browser** (`rules.html`)
- List all rules with categories
- Filter and search rules
- Click to see matching cards
- Rule statistics visualization

**Page 4: Deck Analyzer** (`deck.html`)
- Text area for deck list input
- Parse deck list (MTGO format)
- Display rule composition chart
- Category distribution pie chart
- Suggestions for missing categories

**Page 5: Card Similarity Explorer** (`similarity.html`)
- Search for a card
- Display visual similarity graph
- Interactive similarity slider
- Filter by rule overlap

#### Step 1.3: Component Development

**Component: Card Display**
```javascript
// components/CardDisplay.js
class CardDisplay {
  render(card) {
    return `
      <div class="card-container">
        <h3>${card.name}</h3>
        <p class="mana-cost">${card.mana_cost}</p>
        <p class="type">${card.type_line}</p>
        <p class="oracle-text">${card.oracle_text}</p>
        <div class="rules">
          ${card.rules.map(r => `<span class="rule-tag">${r.rule_name}</span>`).join('')}
        </div>
      </div>
    `;
  }
}
```

**Component: Rule Tag**
```javascript
// components/RuleTag.js
class RuleTag {
  render(rule, confidence) {
    const color = this.getCategoryColor(rule.category);
    return `
      <span class="rule-tag" style="background-color: ${color}">
        ${rule.rule_name} (${(confidence * 100).toFixed(1)}%)
      </span>
    `;
  }

  getCategoryColor(category) {
    const colors = {
      'Removal': '#ef4444',
      'Card Draw': '#3b82f6',
      'Mana Production': '#10b981',
      'Evasion': '#8b5cf6',
      'Token Generation': '#f59e0b',
      // ... more categories
    };
    return colors[category] || '#6b7280';
  }
}
```

**Component: Chart Wrapper**
```javascript
// Use Chart.js for visualizations
// components/DeckAnalysisChart.js
class DeckAnalysisChart {
  renderPieChart(categories, elementId) {
    const ctx = document.getElementById(elementId).getContext('2d');
    new Chart(ctx, {
      type: 'pie',
      data: {
        labels: categories.map(c => c.category),
        datasets: [{
          data: categories.map(c => c.unique_cards),
          backgroundColor: categories.map(c => this.getCategoryColor(c.category))
        }]
      }
    });
  }
}
```

#### Step 1.4: API Integration Layer

```javascript
// js/api.js
class MTGRuleEngineAPI {
  constructor(baseURL = 'http://localhost:8000') {
    this.baseURL = baseURL;
  }

  async searchCard(name) {
    const response = await fetch(`${this.baseURL}/api/cards/search?name=${encodeURIComponent(name)}`);
    return response.json();
  }

  async getCardsByRule(ruleName, limit = 50) {
    const response = await fetch(`${this.baseURL}/api/cards/search?rule=${ruleName}&limit=${limit}`);
    return response.json();
  }

  async getSimilarCards(cardId, limit = 20) {
    const response = await fetch(`${this.baseURL}/api/cards/${cardId}/similar?limit=${limit}`);
    return response.json();
  }

  async analyzeDeck(cardNames) {
    const response = await fetch(`${this.baseURL}/api/analyze/deck`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cards: cardNames })
    });
    return response.json();
  }

  async getStats() {
    const response = await fetch(`${this.baseURL}/api/stats`);
    return response.json();
  }

  async listRules(category = null, limit = 100) {
    let url = `${this.baseURL}/api/rules?limit=${limit}`;
    if (category) url += `&category=${encodeURIComponent(category)}`;
    const response = await fetch(url);
    return response.json();
  }

  async getCategories() {
    const response = await fetch(`${this.baseURL}/api/categories`);
    return response.json();
  }
}
```

#### Step 1.5: Styling and UX

**Use Tailwind CSS** for rapid styling:

```html
<!-- index.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>MTG Rule Engine</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <link rel="stylesheet" href="css/styles.css">
</head>
<body class="bg-gray-900 text-gray-100">
  <!-- Navigation -->
  <nav class="bg-gray-800 p-4">
    <div class="container mx-auto flex justify-between">
      <h1 class="text-2xl font-bold">MTG Rule Engine</h1>
      <div class="space-x-4">
        <a href="index.html" class="hover:text-blue-400">Dashboard</a>
        <a href="cards.html" class="hover:text-blue-400">Cards</a>
        <a href="rules.html" class="hover:text-blue-400">Rules</a>
        <a href="deck.html" class="hover:text-blue-400">Deck Analyzer</a>
      </div>
    </div>
  </nav>

  <!-- Main Content -->
  <main class="container mx-auto p-8">
    <!-- Content goes here -->
  </main>

  <script src="js/api.js"></script>
  <script src="js/app.js"></script>
</body>
</html>
```

#### Step 1.6: Deployment

**Option A: Serve with Python**
```bash
cd frontend
python -m http.server 3000
# Visit http://localhost:3000
```

**Option B: Use Nginx** (production)
```nginx
server {
  listen 80;
  server_name mtg-rules.example.com;
  root /var/www/frontend;
  index index.html;

  # Proxy API requests
  location /api {
    proxy_pass http://localhost:8000;
  }
}
```

### Deliverables

- [ ] Dashboard with statistics
- [ ] Card search and explorer
- [ ] Rule browser with filtering
- [ ] Deck analyzer with visualizations
- [ ] Similarity explorer with graph view
- [ ] Responsive design for mobile
- [ ] Dark mode theme

---

## 2. Rule Interaction & Combo Detection

**Goal**: Automatically detect card combos, synergies, and counters by analyzing rule relationships.

### Implementation Steps

#### Step 2.1: Define Interaction Types

```sql
-- Already in schema, but populate with data
-- rule_interactions table schema:
-- - rule_a_id, rule_b_id
-- - interaction_type: 'combo', 'synergy', 'counter', 'conflict'
-- - description: Text explanation
-- - strength: 1-10 rating
```

#### Step 2.2: Seed Known Interactions

```sql
-- seed_interactions.sql
BEGIN;

-- Example: Token generation + sacrifice synergy
INSERT INTO rule_interactions (rule_a_id, rule_b_id, interaction_type, description, strength)
SELECT
  r1.id,
  r2.id,
  'synergy',
  'Token generation works well with sacrifice effects for value',
  8
FROM rules r1, rules r2
WHERE r1.rule_name = 'create_creature_tokens'
  AND r2.rule_name = 'sacrifice_creature';

-- Example: Graveyard recursion + mill synergy
INSERT INTO rule_interactions (rule_a_id, rule_b_id, interaction_type, description, strength)
SELECT
  r1.id,
  r2.id,
  'synergy',
  'Milling cards enables graveyard recursion strategies',
  9
FROM rules r1, rules r2
WHERE r1.rule_name = 'return_from_graveyard'
  AND r2.rule_name = 'mill_cards';

-- Example: Counterspells counter everything
INSERT INTO rule_interactions (rule_a_id, rule_b_id, interaction_type, description, strength)
SELECT
  r1.id,
  r2.id,
  'counter',
  'Counterspells can stop this effect',
  7
FROM rules r1
CROSS JOIN rules r2
WHERE r1.rule_name IN ('counter_spell', 'counter_noncreature_spell', 'counter_creature_spell')
  AND r2.category_id != r1.category_id;

COMMIT;
```

#### Step 2.3: Create Combo Detection Script

```python
# detect_combos.py
"""
Automatically detect card combos using rule embeddings and patterns.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np
from typing import List, Dict, Tuple

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'vector_mtg',
    'user': 'postgres',
    'password': 'postgres'
}

class ComboDetector:
    """Detect card combinations and interactions."""

    def __init__(self, conn):
        self.conn = conn

    def find_two_card_combos(self, min_confidence=0.85) -> List[Dict]:
        """
        Find 2-card combos by looking for cards that share complementary rules.

        Example: Card A creates tokens + Card B sacrifices creatures = combo
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                WITH card_pairs AS (
                    SELECT DISTINCT
                        cr1.card_id as card_a_id,
                        cr2.card_id as card_b_id,
                        cr1.rule_id as rule_a_id,
                        cr2.rule_id as rule_b_id,
                        cr1.confidence as conf_a,
                        cr2.confidence as conf_b
                    FROM card_rules cr1
                    JOIN card_rules cr2 ON cr1.card_id < cr2.card_id
                    WHERE cr1.confidence >= %s
                      AND cr2.confidence >= %s
                )
                SELECT
                    c1.name as card_a,
                    c2.name as card_b,
                    r1.rule_name as rule_a,
                    r2.rule_name as rule_b,
                    ri.interaction_type,
                    ri.description,
                    ri.strength,
                    (cp.conf_a + cp.conf_b) / 2 as avg_confidence
                FROM card_pairs cp
                JOIN cards c1 ON cp.card_a_id = c1.id
                JOIN cards c2 ON cp.card_b_id = c2.id
                JOIN rules r1 ON cp.rule_a_id = r1.id
                JOIN rules r2 ON cp.rule_b_id = r2.id
                JOIN rule_interactions ri ON (
                    (ri.rule_a_id = cp.rule_a_id AND ri.rule_b_id = cp.rule_b_id) OR
                    (ri.rule_a_id = cp.rule_b_id AND ri.rule_b_id = cp.rule_a_id)
                )
                WHERE ri.interaction_type IN ('combo', 'synergy')
                  AND ri.strength >= 7
                ORDER BY ri.strength DESC, avg_confidence DESC
                LIMIT 100
            """, (min_confidence, min_confidence))

            return cursor.fetchall()

    def find_deck_synergies(self, card_ids: List[str]) -> Dict:
        """
        Analyze a deck to find all synergies between cards.
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT
                    c1.name as card_1,
                    c2.name as card_2,
                    ri.interaction_type,
                    ri.description,
                    ri.strength
                FROM card_rules cr1
                JOIN card_rules cr2 ON cr1.card_id < cr2.card_id
                JOIN rule_interactions ri ON (
                    (ri.rule_a_id = cr1.rule_id AND ri.rule_b_id = cr2.rule_id) OR
                    (ri.rule_a_id = cr2.rule_id AND ri.rule_b_id = cr1.rule_id)
                )
                JOIN cards c1 ON cr1.card_id = c1.id
                JOIN cards c2 ON cr2.card_id = c2.id
                WHERE cr1.card_id = ANY(%s::uuid[])
                  AND cr2.card_id = ANY(%s::uuid[])
                ORDER BY ri.strength DESC
            """, (card_ids, card_ids))

            return {
                'synergies': [r for r in cursor.fetchall() if r['interaction_type'] == 'synergy'],
                'combos': [r for r in cursor.fetchall() if r['interaction_type'] == 'combo'],
                'counters': [r for r in cursor.fetchall() if r['interaction_type'] == 'counter']
            }

    def detect_infinite_combos(self) -> List[Dict]:
        """
        Detect potential infinite combos by finding loops in card effects.

        Patterns:
        - Untap + Tap ability
        - Recursion + ETB effect
        - Token generation + Sacrifice + Return
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Look for untap + tap for mana combos
            cursor.execute("""
                SELECT
                    c1.name as untapper,
                    c2.name as mana_source,
                    'Infinite mana combo' as combo_type,
                    'Untap the mana source repeatedly' as description
                FROM card_rules cr1
                JOIN card_rules cr2 ON cr1.card_id != cr2.card_id
                JOIN cards c1 ON cr1.card_id = c1.id
                JOIN cards c2 ON cr2.card_id = c2.id
                JOIN rules r1 ON cr1.rule_id = r1.id
                JOIN rules r2 ON cr2.rule_id = r2.id
                WHERE r1.rule_name = 'untap_permanent'
                  AND r2.rule_name = 'tap_for_mana'
                  AND c1.oracle_text ILIKE '%untap target%'
                  AND c2.cmc >= 3  -- High-value mana sources
                LIMIT 50
            """)

            return cursor.fetchall()


def main():
    """Run combo detection."""
    print("=" * 60)
    print("MTG Combo Detector")
    print("=" * 60)

    conn = psycopg2.connect(**DB_CONFIG)
    detector = ComboDetector(conn)

    # Find 2-card combos
    print("\nFinding 2-card combos...")
    combos = detector.find_two_card_combos()

    print(f"\nFound {len(combos)} potential combos:")
    for combo in combos[:10]:
        print(f"\n{combo['card_a']} + {combo['card_b']}")
        print(f"  Rules: {combo['rule_a']} <-> {combo['rule_b']}")
        print(f"  Type: {combo['interaction_type']}")
        print(f"  Description: {combo['description']}")
        print(f"  Strength: {combo['strength']}/10")

    # Detect infinite combos
    print("\n" + "=" * 60)
    print("Detecting Infinite Combos")
    print("=" * 60)

    infinite = detector.detect_infinite_combos()
    print(f"\nFound {len(infinite)} potential infinite combos:")
    for combo in infinite[:10]:
        print(f"\n{combo['untapper']} + {combo['mana_source']}")
        print(f"  Type: {combo['combo_type']}")
        print(f"  How: {combo['description']}")

    conn.close()


if __name__ == '__main__':
    main()
```

#### Step 2.4: Add Interaction API Endpoints

```python
# Add to api_server_rules.py

@app.get("/api/combos/two-card", tags=["Combos"])
async def get_two_card_combos(
    min_strength: int = Query(7, ge=1, le=10),
    limit: int = Query(50, ge=1, le=200)
):
    """Find 2-card combos with specified minimum strength."""
    # Implementation using ComboDetector
    pass

@app.get("/api/interactions/{card_id}", tags=["Combos"])
async def get_card_interactions(card_id: str):
    """Get all known interactions for a specific card."""
    pass

@app.post("/api/analyze/synergies", tags=["Analysis"])
async def analyze_deck_synergies(request: DeckAnalysisRequest):
    """Analyze a deck for synergies and combos."""
    pass
```

### Deliverables

- [ ] Seed script with known interactions
- [ ] Combo detection algorithm
- [ ] Infinite combo detector
- [ ] API endpoints for combo queries
- [ ] Frontend combo browser page

---

## 3. LLM Integration for Enhanced Descriptions

**Goal**: Use LLMs (GPT-4, Claude) to generate natural language descriptions and improve rule understanding.

### Implementation Steps

#### Step 3.1: Setup LLM Provider

**Option A: OpenAI API**
```bash
pip install openai
export OPENAI_API_KEY="sk-..."
```

**Option B: Anthropic (Claude)**
```bash
pip install anthropic
export ANTHROPIC_API_KEY="sk-ant-..."
```

**Option C: Local LLM (Ollama)**
```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh
ollama pull llama2
```

#### Step 3.2: Create LLM Integration Module

```python
# llm_integration.py
"""
LLM integration for generating rule descriptions and insights.
"""

import openai
import os
from typing import List, Dict, Optional

class RuleDescriptionGenerator:
    """Generate natural language descriptions for rules using LLMs."""

    def __init__(self, provider='openai'):
        self.provider = provider
        if provider == 'openai':
            openai.api_key = os.getenv('OPENAI_API_KEY')

    def generate_rule_description(self, rule_name: str, rule_template: str,
                                  example_cards: List[str]) -> str:
        """
        Generate a natural language description of a rule.

        Args:
            rule_name: Technical rule name (e.g., 'targeted_creature_destruction')
            rule_template: Template pattern (e.g., 'Destroy target creature')
            example_cards: List of card names that match this rule

        Returns:
            Natural language description
        """
        prompt = f"""
You are an expert Magic: The Gathering rules analyst.

Generate a clear, concise description (2-3 sentences) for the following rule:

Rule Name: {rule_name}
Rule Template: {rule_template}

Example cards that match this rule:
{chr(10).join(f'- {card}' for card in example_cards[:5])}

Description should:
1. Explain what the rule represents in MTG gameplay
2. Mention common use cases
3. Be accessible to intermediate players

Description:
"""

        if self.provider == 'openai':
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=200
            )
            return response.choices[0].message.content.strip()

    def classify_custom_card(self, oracle_text: str) -> List[Dict]:
        """
        Classify a custom card's oracle text using LLM.

        Returns list of applicable rules with confidence scores.
        """
        prompt = f"""
You are an MTG rules engine. Analyze this card text and identify applicable rules.

Card Text:
{oracle_text}

Return a JSON array of rules in this format:
[
  {{"rule": "card_draw_fixed", "confidence": 0.95, "reason": "Card explicitly draws cards"}},
  {{"rule": "etb_trigger", "confidence": 0.90, "reason": "When enters the battlefield trigger"}}
]

Focus on mechanical patterns, not flavor.
"""

        if self.provider == 'openai':
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            return eval(response.choices[0].message.content)

    def suggest_deck_improvements(self, deck_analysis: Dict) -> List[str]:
        """
        Suggest improvements for a deck based on rule distribution.

        Args:
            deck_analysis: Output from rule_engine.analyze_deck()

        Returns:
            List of suggestions
        """
        missing_categories = deck_analysis.get('missing_categories', [])
        rule_dist = deck_analysis.get('rule_distribution', [])

        prompt = f"""
You are a competitive MTG deck builder.

Analyze this deck composition:

Missing Categories: {', '.join(missing_categories) if missing_categories else 'None'}

Current Rules:
{chr(10).join(f"- {r['rule_name']} ({r['category']}): {r['card_count']} cards" for r in rule_dist[:10])}

Provide 3-5 specific suggestions to improve this deck:
1. Cards to add (with explanations)
2. Balance issues to address
3. Synergies to strengthen

Suggestions:
"""

        if self.provider == 'openai':
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )
            content = response.choices[0].message.content.strip()
            return content.split('\n')

    def generate_combo_explanation(self, card_a: str, card_b: str,
                                   interaction_type: str) -> str:
        """
        Generate a detailed explanation of how two cards interact.
        """
        prompt = f"""
Explain how these two MTG cards work together:

Card A: {card_a}
Card B: {card_b}
Interaction Type: {interaction_type}

Provide:
1. Step-by-step combo execution
2. Potential outcomes
3. What makes this powerful

Explanation:
"""

        if self.provider == 'openai':
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300
            )
            return response.choices[0].message.content.strip()


# enhance_rules_with_llm.py
"""
Script to enhance all rules with LLM-generated descriptions.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from llm_integration import RuleDescriptionGenerator
from tqdm import tqdm

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'vector_mtg',
    'user': 'postgres',
    'password': 'postgres'
}

def enhance_all_rules():
    """Add LLM-generated descriptions to all rules."""
    conn = psycopg2.connect(**DB_CONFIG)
    generator = RuleDescriptionGenerator(provider='openai')

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        # Get all rules
        cursor.execute("""
            SELECT r.id, r.rule_name, r.rule_template, r.description
            FROM rules r
            ORDER BY r.rule_name
        """)
        rules = cursor.fetchall()

        print(f"Enhancing {len(rules)} rules with LLM descriptions...")

        for rule in tqdm(rules):
            # Get example cards
            cursor.execute("""
                SELECT c.name
                FROM cards c
                JOIN card_rules cr ON c.id = cr.card_id
                WHERE cr.rule_id = %s
                ORDER BY cr.confidence DESC
                LIMIT 5
            """, (rule['id'],))
            example_cards = [r['name'] for r in cursor.fetchall()]

            # Generate description
            description = generator.generate_rule_description(
                rule['rule_name'],
                rule['rule_template'],
                example_cards
            )

            # Update database
            cursor.execute("""
                UPDATE rules
                SET description = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (description, rule['id']))

        conn.commit()

    conn.close()
    print("✓ All rules enhanced!")


if __name__ == '__main__':
    enhance_all_rules()
```

#### Step 3.3: Add LLM Endpoints to API

```python
# Add to api_server_rules.py

from llm_integration import RuleDescriptionGenerator

llm_generator = RuleDescriptionGenerator()

@app.post("/api/llm/classify-card", tags=["LLM"])
async def classify_custom_card(oracle_text: str):
    """Use LLM to classify custom card text."""
    result = llm_generator.classify_custom_card(oracle_text)
    return {"classifications": result}

@app.post("/api/llm/suggest-improvements", tags=["LLM"])
async def suggest_deck_improvements(request: DeckAnalysisRequest):
    """Get LLM-powered deck improvement suggestions."""
    engine = get_engine()
    analysis = engine.analyze_deck(request.cards)
    suggestions = llm_generator.suggest_deck_improvements(analysis)
    return {"suggestions": suggestions}

@app.get("/api/llm/explain-combo", tags=["LLM"])
async def explain_combo(card_a: str, card_b: str):
    """Get LLM explanation of how two cards combo."""
    explanation = llm_generator.generate_combo_explanation(
        card_a, card_b, "combo"
    )
    return {"explanation": explanation}
```

### Deliverables

- [ ] LLM integration module
- [ ] Rule description generator
- [ ] Custom card classifier
- [ ] Deck improvement suggester
- [ ] Combo explainer
- [ ] API endpoints for LLM features
- [ ] Batch script to enhance all existing rules

---

## 4. Docker Deployment

**Goal**: Containerize the application for easy deployment and distribution.

### Implementation Steps

#### Step 4.1: Create Dockerfiles

**Dockerfile for API Server**
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY *.py ./
COPY *.sql ./

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run API server
CMD ["python", "api_server_rules.py"]
```

**requirements.txt**
```txt
fastapi==0.121.3
uvicorn[standard]==0.38.0
psycopg2-binary==2.9.9
pydantic==2.12.4
sentence-transformers==3.3.1
numpy==2.2.2
tqdm==4.67.1
openai==1.59.7  # Optional: for LLM features
anthropic==0.45.0  # Optional: for Claude
```

**Dockerfile for Frontend**
```dockerfile
# frontend/Dockerfile
FROM nginx:alpine

# Copy frontend files
COPY . /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

#### Step 4.2: Docker Compose Configuration

```yaml
# docker-compose.full.yml
version: '3.8'

services:
  # PostgreSQL database with pgvector
  postgres:
    image: pgvector/pgvector:pg16
    container_name: mtg-postgres
    environment:
      POSTGRES_DB: vector_mtg
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./schema_with_rules.sql:/docker-entrypoint-initdb.d/01-schema.sql
      - ./seed_rules.sql:/docker-entrypoint-initdb.d/02-seed.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - mtg-network

  # API Server
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: mtg-api
    environment:
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=vector_mtg
      - DB_USER=postgres
      - DB_PASSWORD=postgres
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - mtg-network
    restart: unless-stopped

  # Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: mtg-frontend
    ports:
      - "80:80"
    depends_on:
      - api
    networks:
      - mtg-network
    restart: unless-stopped

  # pgAdmin (optional, for database management)
  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: mtg-pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@mtg.local
      PGADMIN_DEFAULT_PASSWORD: admin
    ports:
      - "5050:80"
    depends_on:
      - postgres
    networks:
      - mtg-network
    restart: unless-stopped

volumes:
  postgres_data:

networks:
  mtg-network:
    driver: bridge
```

#### Step 4.3: Deployment Scripts

**deploy.sh**
```bash
#!/bin/bash
# deploy.sh - Deploy the full MTG Rule Engine stack

set -e

echo "Building Docker images..."
docker-compose -f docker-compose.full.yml build

echo "Starting services..."
docker-compose -f docker-compose.full.yml up -d

echo "Waiting for database..."
sleep 10

echo "Loading card data..."
docker-compose -f docker-compose.full.yml exec -T postgres \
  psql -U postgres -d vector_mtg < load_cards.sql

echo "Generating embeddings..."
docker-compose -f docker-compose.full.yml exec api \
  python generate_embeddings_dual.py

echo "Extracting rules..."
docker-compose -f docker-compose.full.yml exec api \
  python extract_rules.py

echo "✓ Deployment complete!"
echo ""
echo "Services:"
echo "  Frontend:  http://localhost"
echo "  API:       http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo "  pgAdmin:   http://localhost:5050"
```

**Makefile**
```makefile
# Makefile for MTG Rule Engine

.PHONY: help build start stop logs clean deploy

help:
	@echo "MTG Rule Engine - Docker Commands"
	@echo ""
	@echo "  make build   - Build all Docker images"
	@echo "  make start   - Start all services"
	@echo "  make stop    - Stop all services"
	@echo "  make logs    - View logs"
	@echo "  make clean   - Remove all containers and volumes"
	@echo "  make deploy  - Full deployment (build + start + load data)"

build:
	docker-compose -f docker-compose.full.yml build

start:
	docker-compose -f docker-compose.full.yml up -d

stop:
	docker-compose -f docker-compose.full.yml down

logs:
	docker-compose -f docker-compose.full.yml logs -f

clean:
	docker-compose -f docker-compose.full.yml down -v
	docker system prune -f

deploy:
	./deploy.sh
```

#### Step 4.4: Environment Configuration

**.env.example**
```bash
# Database
DB_HOST=postgres
DB_PORT=5432
DB_NAME=vector_mtg
DB_USER=postgres
DB_PASSWORD=postgres

# API
API_HOST=0.0.0.0
API_PORT=8000

# LLM (Optional)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Frontend
FRONTEND_PORT=80
API_BASE_URL=http://localhost:8000
```

#### Step 4.5: CI/CD Pipeline (GitHub Actions)

**.github/workflows/deploy.yml**
```yaml
name: Deploy MTG Rule Engine

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run tests
        run: |
          pytest tests/

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker images
        run: |
          docker-compose -f docker-compose.full.yml build

      - name: Push to Docker Hub
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker-compose -f docker-compose.full.yml push

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to production
        run: |
          # Add deployment commands here
          echo "Deploy to your server"
```

### Deliverables

- [ ] API server Dockerfile
- [ ] Frontend Dockerfile
- [ ] Full docker-compose.yml
- [ ] Deployment scripts
- [ ] Environment configuration templates
- [ ] CI/CD pipeline
- [ ] Docker Hub images
- [ ] Deployment documentation

---

## 5. Comprehensive Documentation

**Goal**: Create thorough documentation for users, developers, and API consumers.

### Implementation Steps

#### Step 5.1: API Usage Guide

**API_GUIDE.md**
```markdown
# MTG Rule Engine API Guide

## Quick Start

### Installation

bash
# Clone repository
git clone https://github.com/yourusername/vector-mtg.git
cd vector-mtg

# Start with Docker
docker-compose up -d

# Or run locally
pip install -r requirements.txt
python api_server_rules.py


### Basic Usage

python
import requests

# Search for a card
response = requests.get('http://localhost:8000/api/cards/search?name=Lightning Bolt')
card = response.json()

# Find cards by rule
response = requests.get('http://localhost:8000/api/cards/search?rule=flying_keyword&limit=10')
cards = response.json()

# Analyze a deck
deck = ["Sol Ring", "Mana Crypt", "Lightning Bolt"]
response = requests.post('http://localhost:8000/api/analyze/deck',
                        json={"cards": deck})
analysis = response.json()


## Endpoints

### Cards

#### GET /api/cards/search
Search for cards by name or rule.

**Parameters:**
- `name` (string, optional): Exact card name
- `rule` (string, optional): Rule name to filter by
- `limit` (integer, default=50): Maximum results

**Example:**
bash
curl "http://localhost:8000/api/cards/search?name=Lightning%20Bolt"


**Response:**
json
{
  "id": "uuid",
  "name": "Lightning Bolt",
  "mana_cost": "{R}",
  "type_line": "Instant",
  "oracle_text": "Lightning Bolt deals 3 damage to any target.",
  "rules": [
    {
      "rule_name": "direct_damage_fixed",
      "category": "Direct Damage",
      "confidence": 0.95
    }
  ]
}


[Continue with all other endpoints...]

## Code Examples

### Python
[Examples...]

### JavaScript
[Examples...]

### curl
[Examples...]

## Rate Limiting

Currently no rate limiting. Will be added in future versions.

## Error Handling

All errors return standard HTTP status codes:
- 400: Bad Request
- 404: Not Found
- 500: Internal Server Error

## Support

- GitHub Issues: https://github.com/yourusername/vector-mtg/issues
- Email: support@example.com
```

#### Step 5.2: Developer Guide

**DEVELOPER_GUIDE.md**
```markdown
# Developer Guide

## Architecture Overview

[System diagrams...]

## Database Schema

[Schema documentation...]

## Adding New Rules

### Step 1: Define Rule Pattern

sql
INSERT INTO rules (rule_name, rule_template, rule_pattern, category_id)
VALUES (
  'new_rule_name',
  'Rule template with {PLACEHOLDER}',
  'regex pattern here',
  (SELECT id FROM rule_categories WHERE name = 'Category')
);


### Step 2: Generate Embeddings

bash
python generate_embeddings_dual.py


### Step 3: Extract Matches

bash
python extract_rules.py


## Testing

pytest
# tests/test_rule_engine.py
import pytest
from rule_engine import MTGRuleEngine

def test_card_classification():
    engine = MTGRuleEngine(conn)
    rules = engine.get_card_rules('some-card-id')
    assert len(rules) > 0


Run tests:
bash
pytest tests/


## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Submit pull request

## Code Style

- Follow PEP 8
- Use type hints
- Add docstrings
- Comment complex logic
```

#### Step 5.3: User Tutorials

**TUTORIALS.md**
```markdown
# MTG Rule Engine Tutorials

## Tutorial 1: Finding Similar Cards

Learn how to find cards similar to your favorites.

### Step 1: Search for Your Card
...

### Step 2: View Similar Cards
...

### Step 3: Filter by Rules
...

## Tutorial 2: Building a Deck with Synergies

### Step 1: Start with a Theme
...

### Step 2: Analyze Current Deck
...

### Step 3: Add Synergistic Cards
...

## Tutorial 3: Discovering Combos

...

## Tutorial 4: Understanding Rules

...
```

#### Step 5.4: Video Tutorials

Create screen recordings:
- Quick start (5 min)
- API walkthrough (10 min)
- Building a deck (15 min)
- Advanced queries (20 min)

Upload to YouTube and embed in docs.

### Deliverables

- [ ] API usage guide with examples
- [ ] Developer documentation
- [ ] User tutorials
- [ ] Video walkthroughs
- [ ] FAQ document
- [ ] Troubleshooting guide
- [ ] Contribution guidelines

---

## 6. Advanced Query Features

**Goal**: Add sophisticated query capabilities for power users and advanced analysis.

### Implementation Steps

#### Step 6.1: Complex Search Queries

**Add Advanced Search Endpoint**
```python
# api_server_rules.py

class AdvancedSearchRequest(BaseModel):
    # Card properties
    colors: Optional[List[str]] = None  # ["W", "U", "B", "R", "G"]
    color_identity: Optional[List[str]] = None
    cmc_min: Optional[int] = None
    cmc_max: Optional[int] = None
    types: Optional[List[str]] = None  # ["Creature", "Instant", etc.]

    # Rules
    required_rules: Optional[List[str]] = None  # Must have ALL these
    any_rules: Optional[List[str]] = None  # Must have ANY of these
    exclude_rules: Optional[List[str]] = None  # Must NOT have these

    # Text search
    text_contains: Optional[str] = None
    text_regex: Optional[str] = None

    # Metadata
    sets: Optional[List[str]] = None
    rarity: Optional[List[str]] = None  # ["common", "uncommon", etc.]

    # Sorting & Pagination
    sort_by: Optional[str] = "name"  # "name", "cmc", "power", etc.
    order: Optional[str] = "asc"
    limit: int = 50
    offset: int = 0

@app.post("/api/cards/advanced-search", tags=["Cards"])
async def advanced_card_search(request: AdvancedSearchRequest):
    """
    Advanced card search with multiple filters.

    Example:
    {
      "colors": ["U", "B"],
      "cmc_max": 3,
      "required_rules": ["card_draw_fixed"],
      "exclude_rules": ["exile_card"],
      "text_contains": "draw",
      "rarity": ["rare", "mythic"],
      "sort_by": "cmc",
      "limit": 20
    }
    """
    # Build dynamic query
    query = "SELECT DISTINCT c.* FROM cards c"
    joins = []
    conditions = []
    params = []

    # Color filter
    if request.colors:
        conditions.append("c.colors && %s")
        params.append(request.colors)

    # CMC filter
    if request.cmc_min:
        conditions.append("c.cmc >= %s")
        params.append(request.cmc_min)
    if request.cmc_max:
        conditions.append("c.cmc <= %s")
        params.append(request.cmc_max)

    # Type filter
    if request.types:
        type_conditions = " OR ".join(["c.type_line ILIKE %s"] * len(request.types))
        conditions.append(f"({type_conditions})")
        params.extend([f"%{t}%" for t in request.types])

    # Required rules (must have ALL)
    if request.required_rules:
        for rule in request.required_rules:
            joins.append(f"""
                JOIN card_rules cr_{rule} ON c.id = cr_{rule}.card_id
                JOIN rules r_{rule} ON cr_{rule}.rule_id = r_{rule}.id
                  AND r_{rule}.rule_name = %s
            """)
            params.append(rule)

    # Any rules (must have at least ONE)
    if request.any_rules:
        joins.append("JOIN card_rules cr_any ON c.id = cr_any.card_id")
        joins.append("JOIN rules r_any ON cr_any.rule_id = r_any.id")
        conditions.append("r_any.rule_name = ANY(%s)")
        params.append(request.any_rules)

    # Exclude rules
    if request.exclude_rules:
        for rule in request.exclude_rules:
            conditions.append(f"""
                NOT EXISTS (
                    SELECT 1 FROM card_rules cr_ex
                    JOIN rules r_ex ON cr_ex.rule_id = r_ex.id
                    WHERE cr_ex.card_id = c.id AND r_ex.rule_name = %s
                )
            """)
            params.append(rule)

    # Text search
    if request.text_contains:
        conditions.append("c.oracle_text ILIKE %s")
        params.append(f"%{request.text_contains}%")

    if request.text_regex:
        conditions.append("c.oracle_text ~ %s")
        params.append(request.text_regex)

    # Rarity
    if request.rarity:
        conditions.append("c.rarity = ANY(%s)")
        params.append(request.rarity)

    # Build final query
    query += " ".join(joins)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += f" ORDER BY c.{request.sort_by} {request.order}"
    query += f" LIMIT %s OFFSET %s"
    params.extend([request.limit, request.offset])

    # Execute
    with db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, tuple(params))
        results = cursor.fetchall()

    return {
        "count": len(results),
        "results": [dict(r) for r in results]
    }
```

#### Step 6.2: Bulk Operations

```python
@app.post("/api/cards/bulk-analyze", tags=["Analysis"])
async def bulk_analyze_cards(card_ids: List[str]):
    """
    Analyze multiple cards at once.
    Returns rule distribution across all provided cards.
    """
    pass

@app.post("/api/cards/compare", tags=["Analysis"])
async def compare_cards(card_ids: List[str]):
    """
    Compare multiple cards side-by-side.
    Shows shared and unique rules.
    """
    pass
```

#### Step 6.3: Saved Searches & Watchlists

```sql
-- Add tables for user features
CREATE TABLE IF NOT EXISTS saved_searches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID,
    name VARCHAR(255),
    search_query JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS watchlists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID,
    card_id UUID REFERENCES cards(id),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Step 6.4: Export Functionality

```python
@app.get("/api/export/deck/{format}", tags=["Export"])
async def export_deck(
    card_names: List[str],
    format: str = "mtgo"  # "mtgo", "arena", "csv", "json"
):
    """
    Export a deck in various formats:
    - MTGO: Text format for Magic Online
    - Arena: Format for MTG Arena
    - CSV: Spreadsheet format
    - JSON: Full card data
    """
    if format == "mtgo":
        return {"deck": "\n".join([f"1 {name}" for name in card_names])}
    elif format == "json":
        # Return full card data
        pass
```

### Deliverables

- [ ] Advanced search endpoint
- [ ] Bulk operations API
- [ ] Card comparison tool
- [ ] Saved searches feature
- [ ] Watchlist functionality
- [ ] Export in multiple formats
- [ ] Query builder UI component

---

## Timeline & Priorities

### Phase 2A: Immediate Value (Weeks 1-2)
- ✅ Web Frontend (Simple HTML/JS version)
- ✅ Docker Deployment (Basic setup)
- ✅ Basic Documentation

### Phase 2B: Enhanced Features (Weeks 3-4)
- ✅ Combo Detection
- ✅ Advanced Queries
- ✅ Export Functionality

### Phase 2C: AI Integration (Weeks 5-6)
- ✅ LLM Integration (if API keys available)
- ✅ Enhanced Descriptions
- ✅ Deck Suggestions

### Phase 2D: Polish & Production (Weeks 7-8)
- ✅ Complete Documentation
- ✅ Video Tutorials
- ✅ Production Deployment
- ✅ Performance Optimization

---

## Success Metrics

- **Frontend**: 100% of API endpoints accessible via UI
- **Combos**: 500+ identified 2-card combos
- **LLM**: All 45 rules have enhanced descriptions
- **Docker**: One-command deployment working
- **Docs**: Complete API reference with examples
- **Queries**: Support for 10+ advanced filter combinations

---

## Budget Considerations

### Free/Open Source Options
- Frontend: Vanilla JS (no framework license)
- Backend: Python/FastAPI (MIT license)
- Database: PostgreSQL (PostgreSQL license)
- LLM: Ollama with Llama 2 (free, local)

### Paid Options (Optional)
- **OpenAI API**: ~$0.03/1K tokens (GPT-4)
- **Anthropic API**: ~$0.015/1K tokens (Claude)
- **Hosting**: AWS/GCP ~$20-50/month
- **Domain**: ~$12/year

### Cost Estimates
- **Development Only**: $0 (all open source)
- **With LLM Features**: $50-100/month (API costs)
- **With Hosting**: $70-150/month total

---

## Risk Mitigation

### Technical Risks
- **Database performance**: Add indexes, consider caching
- **LLM costs**: Implement rate limiting, use local models
- **Frontend complexity**: Start simple, iterate

### Operational Risks
- **Data updates**: Automate Scryfall updates weekly
- **API availability**: Add retry logic, circuit breakers
- **Security**: Implement rate limiting, input validation

---

## Next Steps After Phase 2

### Phase 3 Ideas
- **Mobile App**: React Native or Flutter
- **Discord Bot**: Search cards in Discord
- **Twitch Integration**: Show card info on stream
- **Tournament Data**: Scrape and analyze metagame
- **Price Tracking**: Integrate TCGPlayer API
- **Card Marketplace**: Buy/sell/trade platform
- **Custom Formats**: Support for custom cube/format rules
- **Machine Learning**: Predict card power level

---

## Questions to Address

Before starting each section:

1. **Frontend**: Which tech stack? (Recommend vanilla JS for now)
2. **LLM**: Which provider? (Recommend Ollama for cost-free start)
3. **Docker**: Self-hosted or cloud? (Start self-hosted)
4. **Documentation**: Video or text focus? (Both, but text first)
5. **Advanced Queries**: Which filters are most important? (Colors, CMC, rules)

---

## Resources

### Learning Materials
- FastAPI docs: https://fastapi.tiangolo.com
- Docker docs: https://docs.docker.com
- Chart.js: https://www.chartjs.org
- Tailwind CSS: https://tailwindcss.com

### MTG Data
- Scryfall API: https://scryfall.com/docs/api
- MTGJSON: https://mtgjson.com
- EDHRec: https://edhrec.com (for combo data)

### Community
- MTG Dev Discord
- Reddit: r/magicTCG, r/EDH
- GitHub: Awesome MTG list

---

## Conclusion

Phase 2 will transform the MTG Rule Engine from a powerful backend system into a complete, user-friendly application. By following this roadmap, we'll create:

1. An intuitive web interface for exploring 500K+ cards
2. Intelligent combo detection across card interactions
3. AI-powered insights and suggestions
4. One-command Docker deployment
5. Comprehensive documentation for users and developers
6. Advanced query capabilities for power users

Each component builds on Phase 1's solid foundation and can be developed incrementally. Start with the frontend for immediate user value, then add combos, LLM features, and polish with deployment and documentation.

**Let's build something amazing! 🎮🃏✨**
