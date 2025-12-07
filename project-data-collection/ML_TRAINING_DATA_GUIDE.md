# Machine Learning Training Data from Commander Spellbook

## Overview

The Commander Spellbook dataset contains rich relational data perfect for training various ML models. This guide outlines different model types, their training data formats, and SQL queries to extract the data.

---

## Table of Contents

1. [Combo Recommendation System](#1-combo-recommendation-system)
2. [Card Synergy Prediction](#2-card-synergy-prediction)
3. [Combo Classification (Win Conditions)](#3-combo-classification)
4. [Price Prediction Model](#4-price-prediction)
5. [Text Generation (Combo Descriptions)](#5-text-generation)
6. [Embedding Models (Semantic Search)](#6-embedding-models)
7. [Graph Neural Networks](#7-graph-neural-networks)

---

## 1. Combo Recommendation System

**Goal**: Given a user's deck or card collection, recommend combos they can build.

### Training Data Format

```csv
user_id,card_ids,combo_id,label
user_001,"sol-ring,hullbreaker-horror",513-5034--46,1
user_001,"thassas-oracle,demonic-consultation",789-1234--56,1
user_001,"lightning-bolt,grizzly-bears",null,0
user_002,"exquisite-blood,sanguine-bond",456-7890--12,1
```

**Features**:
- `card_ids`: Comma-separated card IDs the user owns
- `combo_id`: The combo they might be interested in
- `label`: 1 if combo is viable, 0 if not

### SQL Query to Generate Training Data

```sql
-- Positive examples: Users who can build combos with their cards
SELECT
    u.id AS user_id,
    array_to_string(array_agg(DISTINCT uc.card_id ORDER BY uc.card_id), ',') AS card_ids,
    v.id AS combo_id,
    1 AS label
FROM users u
JOIN user_cards uc ON u.id = uc.user_id  -- Hypothetical user card collection
JOIN variant_cards vc ON uc.card_id = vc.card_id
JOIN variants v ON vc.variant_id = v.id
WHERE v.status = 'OK'
GROUP BY u.id, v.id
HAVING COUNT(DISTINCT vc.card_id) = (
    SELECT COUNT(*) FROM variant_cards WHERE variant_id = v.id
);

-- Negative examples: Random combos user can't build
SELECT
    u.id AS user_id,
    array_to_string(array_agg(DISTINCT uc.card_id ORDER BY uc.card_id), ',') AS card_ids,
    v.id AS combo_id,
    0 AS label
FROM users u
CROSS JOIN variants v
JOIN user_cards uc ON u.id = uc.user_id
WHERE v.id NOT IN (
    SELECT variant_id FROM variant_cards vc
    WHERE vc.card_id IN (SELECT card_id FROM user_cards WHERE user_id = u.id)
)
GROUP BY u.id, v.id
LIMIT 10000;
```

### Model Architecture

**Collaborative Filtering** or **Matrix Factorization**:
- Input: User card embeddings + Combo embeddings
- Output: Probability user would like this combo

---

## 2. Card Synergy Prediction

**Goal**: Predict if two cards work well together.

### Training Data Format

```csv
card_1_id,card_2_id,card_1_name,card_2_name,synergy_score,features
sol-ring,hullbreaker-horror,Sol Ring,Hullbreaker Horror,0.95,"mana_ramp,artifact,bounce"
lightning-bolt,grizzly-bears,Lightning Bolt,Grizzly Bears,0.1,"removal,creature"
exquisite-blood,sanguine-bond,Exquisite Blood,Sanguine Bond,0.98,"lifegain,combo"
```

**Features**:
- `synergy_score`: 0-1 scale (derived from combo popularity)
- `features`: Shared keywords, color identity, card types

### SQL Query to Generate Training Data

```sql
-- Positive examples: Cards that appear together in popular combos
SELECT
    c1.id AS card_1_id,
    c2.id AS card_2_id,
    c1.name AS card_1_name,
    c2.name AS card_2_name,
    AVG(v.popularity) / 1000.0 AS synergy_score,  -- Normalize to 0-1
    array_to_string(
        ARRAY(SELECT unnest(c1.keywords) INTERSECT SELECT unnest(c2.keywords)),
        ','
    ) AS shared_keywords,
    array_to_string(
        ARRAY(SELECT unnest(c1.identity) INTERSECT SELECT unnest(c2.identity)),
        ','
    ) AS shared_colors
FROM variant_cards vc1
JOIN variant_cards vc2 ON vc1.variant_id = vc2.variant_id AND vc1.card_id < vc2.card_id
JOIN cards c1 ON vc1.card_id = c1.id
JOIN cards c2 ON vc2.card_id = c2.id
JOIN variants v ON vc1.variant_id = v.id
WHERE v.status = 'OK'
GROUP BY c1.id, c2.id, c1.name, c2.name, c1.keywords, c2.keywords, c1.identity, c2.identity
HAVING COUNT(DISTINCT vc1.variant_id) >= 5  -- Cards that appear together in 5+ combos
ORDER BY synergy_score DESC;

-- Negative examples: Random card pairs
SELECT
    c1.id AS card_1_id,
    c2.id AS card_2_id,
    c1.name AS card_1_name,
    c2.name AS card_2_name,
    0.0 AS synergy_score,
    '' AS shared_keywords,
    '' AS shared_colors
FROM cards c1
CROSS JOIN cards c2
WHERE c1.id < c2.id
  AND NOT EXISTS (
      SELECT 1 FROM variant_cards vc1
      JOIN variant_cards vc2 ON vc1.variant_id = vc2.variant_id
      WHERE vc1.card_id = c1.id AND vc2.card_id = c2.id
  )
ORDER BY RANDOM()
LIMIT 50000;
```

### Model Architecture

**Graph Neural Network (GNN)** or **Siamese Network**:
- Input: Card embeddings (name, type, keywords, identity)
- Output: Synergy probability

---

## 3. Combo Classification (Win Conditions)

**Goal**: Classify combos by their win condition (infinite mana, infinite damage, mill, etc.)

### Training Data Format

```csv
combo_id,card_names,mana_needed,description,win_condition
513-5034--46,"Hullbreaker Horror,Sol Ring","{1}","Bounce Sol Ring...",infinite_mana
789-1234--56,"Thassa's Oracle,Demonic Consultation","","Exile library...",instant_win
456-7890--12,"Exquisite Blood,Sanguine Bond","","Life loss triggers...",infinite_life
```

**Features**:
- `card_names`: Cards in the combo
- `mana_needed`: Mana cost to execute
- `description`: Step-by-step explanation
- `win_condition`: Multi-label classification (infinite_mana, infinite_damage, etc.)

### SQL Query to Generate Training Data

```sql
SELECT
    v.id AS combo_id,
    array_to_string(array_agg(DISTINCT c.name ORDER BY c.name), ',') AS card_names,
    v.mana_needed,
    v.description,
    array_to_string(array_agg(DISTINCT f.name ORDER BY f.name), '|') AS win_conditions,
    v.popularity,
    array_length(v.identity, 1) AS color_count,
    COUNT(DISTINCT vc.card_id) AS card_count
FROM variants v
JOIN variant_cards vc ON v.id = vc.variant_id
JOIN cards c ON vc.card_id = c.id
JOIN variant_features vf ON v.id = vf.variant_id
JOIN features f ON vf.feature_id = f.id
WHERE v.status = 'OK'
GROUP BY v.id, v.mana_needed, v.description, v.popularity, v.identity;
```

### Model Architecture

**Multi-Label Classifier** (BERT or RoBERTa):
- Input: Combo description + card names
- Output: Probability distribution over win conditions

---

## 4. Price Prediction

**Goal**: Predict combo price based on card composition and market trends.

### Training Data Format

```csv
combo_id,card_count,total_mana_value,color_count,rarity_score,vendor,price_usd,popularity,timestamp
513-5034--46,2,3.0,1,0.8,tcgplayer,45.99,850,2024-01-15
789-1234--56,2,1.0,1,0.9,tcgplayer,125.50,1200,2024-01-15
```

**Features**:
- `card_count`: Number of cards in combo
- `total_mana_value`: Sum of mana costs
- `color_count`: Number of colors required
- `rarity_score`: Average rarity (mythic=1.0, rare=0.75, uncommon=0.5, common=0.25)
- `popularity`: Combo popularity score

### SQL Query to Generate Training Data

```sql
SELECT
    v.id AS combo_id,
    COUNT(DISTINCT vc.card_id) AS card_count,
    SUM(c.mana_value) AS total_mana_value,
    array_length(v.identity, 1) AS color_count,
    v.popularity,
    vp.vendor,
    vp.price_usd,
    vp.updated_at AS timestamp,
    -- Feature: Average card price
    AVG(cp.price_usd) AS avg_card_price,
    -- Feature: Has expensive staples
    CASE WHEN MAX(cp.price_usd) > 50 THEN 1 ELSE 0 END AS has_expensive_cards,
    -- Feature: Format legalities
    COUNT(DISTINCT vl.format) FILTER (WHERE vl.is_legal = TRUE) AS legal_format_count
FROM variants v
JOIN variant_cards vc ON v.id = vc.variant_id
JOIN cards c ON vc.card_id = c.id
JOIN variant_prices vp ON v.id = vp.variant_id
LEFT JOIN card_prices cp ON c.id = cp.card_id AND cp.vendor = vp.vendor
LEFT JOIN variant_legalities vl ON v.id = vl.variant_id
WHERE v.status = 'OK' AND vp.price_usd IS NOT NULL
GROUP BY v.id, v.identity, v.popularity, vp.vendor, vp.price_usd, vp.updated_at;
```

### Model Architecture

**Gradient Boosting (XGBoost/LightGBM)** or **Random Forest**:
- Input: Combo features (card count, mana, rarity, popularity)
- Output: Price prediction (regression)

---

## 5. Text Generation (Combo Descriptions)

**Goal**: Generate step-by-step combo explanations from card lists.

### Training Data Format

```jsonl
{"input": "Cards: Hullbreaker Horror, Sol Ring", "output": "1. With Hullbreaker Horror on the battlefield and Sol Ring in hand, cast Sol Ring by paying {1}. 2. Hullbreaker Horror triggers, return Sol Ring to your hand. 3. Repeat for infinite colorless mana."}
{"input": "Cards: Thassa's Oracle, Demonic Consultation", "output": "1. Cast Demonic Consultation and name a card not in your deck. 2. Exile your entire library. 3. Cast Thassa's Oracle with devotion check, win the game."}
```

### SQL Query to Generate Training Data

```sql
SELECT
    'Cards: ' || array_to_string(array_agg(DISTINCT c.name ORDER BY c.name), ', ') AS input,
    v.description AS output,
    v.id AS combo_id,
    v.popularity AS weight  -- Use for sampling
FROM variants v
JOIN variant_cards vc ON v.id = vc.variant_id
JOIN cards c ON vc.card_id = c.id
WHERE v.status = 'OK' AND v.description IS NOT NULL AND v.description != ''
GROUP BY v.id, v.description, v.popularity
ORDER BY v.popularity DESC;
```

### Model Architecture

**Seq2Seq Transformer** (T5, BART, GPT-based):
- Input: "Generate combo explanation for: [card names]"
- Output: Step-by-step combo description

---

## 6. Embedding Models (Semantic Search)

**Goal**: Create vector embeddings for cards and combos to enable semantic search.

### Training Data Format

**Card Embeddings** (for similarity search):

```csv
card_id,card_name,type_line,oracle_text,keywords,identity,embedding_source
sol-ring,Sol Ring,Artifact,"{T}: Add {C}{C}","",C,"Sol Ring is an Artifact that produces colorless mana"
hullbreaker-horror,Hullbreaker Horror,Creature - Kraken Horror,"Flash, when you cast instant/sorcery, return permanent","Flash",U,"Hullbreaker Horror is a blue creature with flash that bounces permanents"
```

**Combo Embeddings** (for recommendation):

```json
{
  "combo_id": "513-5034--46",
  "text": "Hullbreaker Horror and Sol Ring create infinite colorless mana by casting and bouncing Sol Ring repeatedly",
  "cards": ["Hullbreaker Horror", "Sol Ring"],
  "features": ["Infinite mana", "Infinite colorless mana"],
  "identity": ["U"],
  "popularity": 850
}
```

### SQL Query to Generate Training Data

```sql
-- Card embeddings source text
SELECT
    c.id AS card_id,
    c.name AS card_name,
    c.type_line,
    c.oracle_text,
    array_to_string(c.keywords, ', ') AS keywords,
    array_to_string(c.identity, '') AS identity,
    -- Concatenate all text for embedding
    c.name || ' is a ' || c.type_line ||
    CASE WHEN c.oracle_text != '' THEN '. ' || c.oracle_text ELSE '' END ||
    CASE WHEN array_length(c.keywords, 1) > 0
         THEN '. Keywords: ' || array_to_string(c.keywords, ', ')
         ELSE '' END AS embedding_source
FROM cards c
WHERE c.oracle_text IS NOT NULL;

-- Combo embeddings source text
SELECT
    v.id AS combo_id,
    array_to_string(array_agg(DISTINCT c.name ORDER BY c.name), ' and ') ||
    CASE WHEN array_length(f_names, 1) > 0
         THEN ' creates ' || array_to_string(f_names, ', ')
         ELSE '' END ||
    '. ' || COALESCE(v.description, '') AS embedding_source,
    array_agg(DISTINCT c.name ORDER BY c.name) AS cards,
    f_names AS features,
    v.identity,
    v.popularity
FROM variants v
JOIN variant_cards vc ON v.id = vc.variant_id
JOIN cards c ON vc.card_id = c.id
LEFT JOIN LATERAL (
    SELECT array_agg(DISTINCT f.name ORDER BY f.name) AS f_names
    FROM variant_features vf
    JOIN features f ON vf.feature_id = f.id
    WHERE vf.variant_id = v.id
) features ON TRUE
WHERE v.status = 'OK'
GROUP BY v.id, v.description, v.identity, v.popularity, f_names;
```

### Model Architecture

**Sentence Transformers** (SBERT, MiniLM):
- Input: Card/combo text descriptions
- Output: 384 or 768-dimensional embeddings

**Use Cases**:
- "Find cards similar to Sol Ring"
- "Find combos that create infinite mana"
- Semantic search across all combos

---

## 7. Graph Neural Networks (GNN)

**Goal**: Model the relationship graph between cards, combos, and features.

### Training Data Format

**Node Features** (cards, combos, features):

```csv
node_id,node_type,name,features
sol-ring,card,Sol Ring,"[0.2,0.8,0.1,...]"  # Embedding vector
513-5034--46,combo,Hullbreaker+Sol,"[0.5,0.6,0.9,...]"
infinite-mana,feature,Infinite Mana,"[0.1,0.2,0.7,...]"
```

**Edge List** (relationships):

```csv
source_id,target_id,edge_type,weight
sol-ring,513-5034--46,used_in,1.0
513-5034--46,infinite-mana,produces,0.95
hullbreaker-horror,513-5034--46,used_in,1.0
```

### SQL Query to Generate Training Data

```sql
-- Nodes: Cards
SELECT
    c.id AS node_id,
    'card' AS node_type,
    c.name,
    json_build_object(
        'mana_value', c.mana_value,
        'identity', c.identity,
        'type_line', c.type_line,
        'keywords', c.keywords,
        'variant_count', c.variant_count
    ) AS features
FROM cards c;

-- Nodes: Combos
SELECT
    v.id AS node_id,
    'combo' AS node_type,
    v.id AS name,
    json_build_object(
        'identity', v.identity,
        'popularity', v.popularity,
        'mana_needed', v.mana_needed
    ) AS features
FROM variants v
WHERE v.status = 'OK';

-- Nodes: Features
SELECT
    'feature-' || f.id AS node_id,
    'feature' AS node_type,
    f.name,
    json_build_object(
        'status', f.status,
        'uncountable', f.uncountable
    ) AS features
FROM features f;

-- Edges: Card -> Combo
SELECT
    vc.card_id AS source_id,
    vc.variant_id AS target_id,
    'used_in' AS edge_type,
    1.0 AS weight
FROM variant_cards vc
JOIN variants v ON vc.variant_id = v.id
WHERE v.status = 'OK';

-- Edges: Combo -> Feature
SELECT
    vf.variant_id AS source_id,
    'feature-' || vf.feature_id AS target_id,
    'produces' AS edge_type,
    1.0 AS weight
FROM variant_features vf
JOIN variants v ON vf.variant_id = v.id
WHERE v.status = 'OK';

-- Edges: Card -> Card (co-occurrence)
SELECT
    vc1.card_id AS source_id,
    vc2.card_id AS target_id,
    'synergy' AS edge_type,
    COUNT(*) / 100.0 AS weight  -- Normalize by co-occurrence count
FROM variant_cards vc1
JOIN variant_cards vc2 ON vc1.variant_id = vc2.variant_id AND vc1.card_id < vc2.card_id
JOIN variants v ON vc1.variant_id = v.id
WHERE v.status = 'OK'
GROUP BY vc1.card_id, vc2.card_id;
```

### Model Architecture

**Graph Convolutional Network (GCN)** or **Graph Attention Network (GAT)**:
- Input: Graph structure (nodes + edges)
- Tasks:
  - Link prediction (will card X work with card Y?)
  - Node classification (what features does a card enable?)
  - Graph embedding (combo similarity)

---

## Feature Engineering Examples

### Card-Level Features

```sql
SELECT
    c.id,
    c.name,
    c.mana_value,
    array_length(c.identity, 1) AS color_count,
    array_length(c.keywords, 1) AS keyword_count,
    c.variant_count AS combo_appearances,
    c.game_changer::INT AS is_game_changer,
    c.tutor::INT AS is_tutor,
    c.extra_turn::INT AS is_extra_turn,
    -- Derived features
    CASE
        WHEN c.type_line LIKE '%Creature%' THEN 1
        WHEN c.type_line LIKE '%Artifact%' THEN 2
        WHEN c.type_line LIKE '%Enchantment%' THEN 3
        WHEN c.type_line LIKE '%Instant%' OR c.type_line LIKE '%Sorcery%' THEN 4
        WHEN c.type_line LIKE '%Land%' THEN 5
        ELSE 0
    END AS card_type_category,
    -- Price features
    COALESCE(AVG(cp.price_usd), 0) AS avg_price,
    -- Popularity features
    COALESCE(AVG(v.popularity), 0) AS avg_combo_popularity
FROM cards c
LEFT JOIN card_prices cp ON c.id = cp.card_id
LEFT JOIN variant_cards vc ON c.id = vc.card_id
LEFT JOIN variants v ON vc.variant_id = v.id AND v.status = 'OK'
GROUP BY c.id;
```

### Combo-Level Features

```sql
SELECT
    v.id,
    v.popularity,
    array_length(v.identity, 1) AS color_count,
    COUNT(DISTINCT vc.card_id) AS card_count,
    COUNT(DISTINCT vf.feature_id) AS feature_count,
    COUNT(DISTINCT vl.format) FILTER (WHERE vl.is_legal = TRUE) AS legal_format_count,
    -- Price features
    AVG(vp.price_usd) AS avg_price,
    -- Text features
    LENGTH(v.description) AS description_length,
    -- Mana complexity
    LENGTH(v.mana_needed) AS mana_complexity,
    -- Temporal features
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - v.created_at)) / 86400 AS age_days
FROM variants v
LEFT JOIN variant_cards vc ON v.id = vc.variant_id
LEFT JOIN variant_features vf ON v.id = vf.variant_id
LEFT JOIN variant_legalities vl ON v.id = vl.variant_id
LEFT JOIN variant_prices vp ON v.id = vp.variant_id
WHERE v.status = 'OK'
GROUP BY v.id;
```

---

## Data Export Scripts

### Export to CSV

```python
import psycopg2
import pandas as pd

conn = psycopg2.connect("dbname=commander_spellbook user=postgres")

# Export card synergy training data
query = """
SELECT
    c1.id AS card_1_id,
    c2.id AS card_2_id,
    c1.name AS card_1_name,
    c2.name AS card_2_name,
    AVG(v.popularity) / 1000.0 AS synergy_score
FROM variant_cards vc1
JOIN variant_cards vc2 ON vc1.variant_id = vc2.variant_id AND vc1.card_id < vc2.card_id
JOIN cards c1 ON vc1.card_id = c1.id
JOIN cards c2 ON vc2.card_id = c2.id
JOIN variants v ON vc1.variant_id = v.id
WHERE v.status = 'OK'
GROUP BY c1.id, c2.id, c1.name, c2.name
HAVING COUNT(DISTINCT vc1.variant_id) >= 3
"""

df = pd.read_sql(query, conn)
df.to_csv('card_synergy_training.csv', index=False)
```

### Export to JSON (for embeddings)

```python
import json

query = """
SELECT
    v.id AS combo_id,
    array_to_string(array_agg(DISTINCT c.name), ' and ') || ' creates ' ||
    array_to_string(array_agg(DISTINCT f.name), ', ') AS text,
    v.popularity
FROM variants v
JOIN variant_cards vc ON v.id = vc.variant_id
JOIN cards c ON vc.card_id = c.id
LEFT JOIN variant_features vf ON v.id = vf.variant_id
LEFT JOIN features f ON vf.feature_id = f.id
WHERE v.status = 'OK'
GROUP BY v.id, v.popularity
"""

df = pd.read_sql(query, conn)

# Save as JSONL for sentence transformers
with open('combo_embeddings.jsonl', 'w') as f:
    for _, row in df.iterrows():
        f.write(json.dumps({
            'id': row['combo_id'],
            'text': row['text'],
            'metadata': {'popularity': row['popularity']}
        }) + '\n')
```

---

## Recommended Training Pipeline

### 1. Data Extraction
```bash
python scripts/extract_training_data.py --output-dir data/training/
```

### 2. Train Embeddings First
```python
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader

# Load card/combo text
train_examples = [
    InputExample(texts=['Sol Ring', 'produces colorless mana'], label=0.9),
    # ... more examples
]

model = SentenceTransformer('all-MiniLM-L6-v2')
train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=16)
train_loss = losses.CosineSimilarityLoss(model)

model.fit(train_objectives=[(train_dataloader, train_loss)], epochs=3)
model.save('models/card_embeddings')
```

### 3. Train Downstream Models
```python
import xgboost as xgb

# Load features + labels
X_train, y_train = load_price_features()

model = xgb.XGBRegressor(n_estimators=100, max_depth=6)
model.fit(X_train, y_train)
model.save_model('models/price_prediction.json')
```

---

## Summary

| Model Type | Training Data Size | Features | Use Case |
|------------|-------------------|----------|----------|
| Combo Recommendation | ~500K samples | Card IDs, user history | "Show me combos I can build" |
| Card Synergy | ~100K pairs | Card pairs, co-occurrence | "Do these cards work together?" |
| Win Condition Classifier | ~72K combos | Text, cards, features | "What does this combo do?" |
| Price Prediction | ~300K price points | Card count, rarity, popularity | "How much will this combo cost?" |
| Text Generation | ~72K descriptions | Card names → descriptions | "Explain this combo" |
| Embeddings | ~80K texts | Card/combo descriptions | Semantic search |
| GNN | ~500K nodes+edges | Graph structure | Link prediction, recommendations |

All training data can be extracted from the Commander Spellbook PostgreSQL database using the queries above!
