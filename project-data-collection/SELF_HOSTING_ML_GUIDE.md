# Self-Hosting ML Models for Commander Spellbook

## Overview

This guide covers ML models suitable for self-hosting, ranked by deployment complexity and resource requirements. All models can run on consumer hardware (CPU/GPU) or cloud instances.

---

## Quick Comparison: Self-Hostable Models

| Model Type | Inference Speed | Memory Usage | GPU Required? | Deployment Complexity | Best For |
|------------|----------------|--------------|---------------|----------------------|----------|
| **Embedding Models** | ⚡⚡⚡ Very Fast | 100-500 MB | No (CPU fine) | ⭐ Easy | Semantic search, similarity |
| **XGBoost/LightGBM** | ⚡⚡⚡ Very Fast | <50 MB | No | ⭐ Very Easy | Price prediction, classification |
| **Random Forest** | ⚡⚡⚡ Very Fast | <100 MB | No | ⭐ Very Easy | Synergy scoring, recommendations |
| **Small Transformers** | ⚡⚡ Fast | 200-800 MB | Optional | ⭐⭐ Moderate | Text classification, embeddings |
| **GNN (GraphSAGE)** | ⚡⚡ Fast | 500 MB-2 GB | Optional | ⭐⭐ Moderate | Graph-based recommendations |
| **Large Transformers** | ⚡ Slow | 2-15 GB | Yes (recommended) | ⭐⭐⭐ Complex | Text generation, Q&A |

---

## 1. Embedding Models (RECOMMENDED FOR STARTING)

### Why These Are Perfect for Self-Hosting

✅ **Small size**: 80-500 MB models
✅ **CPU-friendly**: No GPU needed
✅ **Fast inference**: <50ms per query
✅ **Battle-tested**: Production-ready libraries
✅ **Easy deployment**: Flask/FastAPI + Docker

### Best Models for Self-Hosting

#### Option 1: Sentence-BERT (MiniLM)
```python
# Model: all-MiniLM-L6-v2
# Size: 80 MB
# Speed: ~10ms inference on CPU
# Output: 384-dimensional embeddings

from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

# Encode cards/combos
card_text = "Sol Ring: Artifact that produces colorless mana"
embedding = model.encode(card_text)  # Shape: (384,)

# Find similar cards
query = "mana acceleration artifact"
query_embedding = model.encode(query)
# Use cosine similarity to find matches
```

**Hardware Requirements**:
- CPU: Any modern CPU (2+ cores)
- RAM: 2 GB
- Storage: 500 MB

**Deployment**:
```dockerfile
FROM python:3.10-slim

RUN pip install sentence-transformers fastapi uvicorn

COPY app.py .
COPY models/ ./models/

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Option 2: OpenAI CLIP (for image + text)
```python
# Model: openai/clip-vit-base-patch32
# Size: 350 MB
# Speed: ~20ms on CPU
# Output: 512-dimensional embeddings

from transformers import CLIPModel, CLIPProcessor

model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# Encode card images + text together
inputs = processor(text=["Sol Ring"], images=[card_image], return_tensors="pt")
outputs = model(**inputs)
```

**Use Case**: Visual search for card art + text search combined

### API Endpoint Example

```python
# app.py
from fastapi import FastAPI
from sentence_transformers import SentenceTransformer
import numpy as np

app = FastAPI()
model = SentenceTransformer('all-MiniLM-L6-v2')

# Pre-compute embeddings for all cards (do once at startup)
card_embeddings = np.load('data/card_embeddings.npy')  # (7085, 384)
card_ids = np.load('data/card_ids.npy')  # (7085,)

@app.post("/search")
def semantic_search(query: str, top_k: int = 10):
    """Find similar cards/combos"""
    query_embedding = model.encode(query)

    # Cosine similarity
    similarities = np.dot(card_embeddings, query_embedding)
    top_indices = np.argsort(similarities)[-top_k:][::-1]

    return {
        "results": [
            {"card_id": card_ids[i], "score": float(similarities[i])}
            for i in top_indices
        ]
    }

@app.post("/embed")
def embed_text(text: str):
    """Get embedding for text"""
    embedding = model.encode(text)
    return {"embedding": embedding.tolist()}
```

**Deployment**:
```bash
# Build and run
docker build -t combo-search .
docker run -p 8000:8000 combo-search

# Query API
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "infinite mana combo", "top_k": 5}'
```

---

## 2. Gradient Boosting Models (XGBoost/LightGBM)

### Why Perfect for Self-Hosting

✅ **Tiny size**: <50 MB models
✅ **Lightning fast**: <1ms inference
✅ **CPU-only**: No GPU needed
✅ **Production-proven**: Used by Netflix, Uber, etc.

### Use Cases

- **Price prediction**: Predict combo prices
- **Popularity scoring**: Rank combos by predicted popularity
- **Card classification**: Categorize cards by power level

### Training Example

```python
import xgboost as xgb
import pandas as pd
import numpy as np

# Load training data (from SQL queries in ML_TRAINING_DATA_GUIDE.md)
df = pd.read_sql("""
    SELECT
        v.id,
        COUNT(DISTINCT vc.card_id) AS card_count,
        array_length(v.identity, 1) AS color_count,
        v.popularity,
        COALESCE(AVG(vp.price_usd), 0) AS avg_price
    FROM variants v
    LEFT JOIN variant_cards vc ON v.id = vc.variant_id
    LEFT JOIN variant_prices vp ON v.id = vp.variant_id
    WHERE v.status = 'OK'
    GROUP BY v.id
""", conn)

# Features and target
X = df[['card_count', 'color_count', 'avg_price']]
y = df['popularity']

# Train model
model = xgb.XGBRegressor(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    tree_method='hist'  # Faster on CPU
)
model.fit(X, y)

# Save model (tiny file!)
model.save_model('models/popularity_predictor.json')  # ~2 MB
```

### Serving with FastAPI

```python
from fastapi import FastAPI
import xgboost as xgb
import numpy as np

app = FastAPI()
model = xgb.XGBRegressor()
model.load_model('models/popularity_predictor.json')

@app.post("/predict/popularity")
def predict_popularity(card_count: int, color_count: int, avg_price: float):
    """Predict combo popularity"""
    features = np.array([[card_count, color_count, avg_price]])
    prediction = model.predict(features)[0]
    return {"predicted_popularity": float(prediction)}

@app.post("/predict/price")
def predict_price(card_count: int, color_count: int, popularity: int):
    """Predict combo price"""
    # Load price model
    price_model = xgb.XGBRegressor()
    price_model.load_model('models/price_predictor.json')

    features = np.array([[card_count, color_count, popularity]])
    prediction = price_model.predict(features)[0]
    return {"predicted_price_usd": float(prediction)}
```

**Hardware Requirements**:
- CPU: Any modern CPU
- RAM: 1 GB
- Storage: 100 MB

---

## 3. Graph Neural Networks (GNN)

### Why Suitable for Self-Hosting

✅ **Medium size**: 500 MB - 2 GB
✅ **Fast inference**: 10-100ms
✅ **CPU-capable**: GPU optional (3x faster)
✅ **Powerful**: Captures card relationships

### Best GNN Architecture: GraphSAGE

```python
import torch
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv
from torch_geometric.data import Data

class CardComboGNN(torch.nn.Module):
    def __init__(self, num_features, hidden_dim=128, output_dim=64):
        super().__init__()
        self.conv1 = SAGEConv(num_features, hidden_dim)
        self.conv2 = SAGEConv(hidden_dim, output_dim)

    def forward(self, x, edge_index):
        # x: Node features (cards/combos)
        # edge_index: Graph structure
        x = F.relu(self.conv1(x, edge_index))
        x = F.dropout(x, p=0.5, training=self.training)
        x = self.conv2(x, edge_index)
        return x

# Load graph data (from SQL in ML_TRAINING_DATA_GUIDE.md)
edge_index = torch.load('data/graph_edges.pt')  # (2, num_edges)
node_features = torch.load('data/node_features.pt')  # (num_nodes, num_features)

# Create model
model = CardComboGNN(num_features=128, output_dim=64)
model.load_state_dict(torch.load('models/gnn_model.pt', map_location='cpu'))

# Inference: Get card embeddings
with torch.no_grad():
    embeddings = model(node_features, edge_index)

# Find similar cards
card_idx = 0  # Sol Ring
similarities = F.cosine_similarity(embeddings[card_idx].unsqueeze(0), embeddings)
top_similar = torch.argsort(similarities, descending=True)[:10]
```

### Serving GNN Model

```python
from fastapi import FastAPI
import torch
from torch_geometric.data import Data

app = FastAPI()

# Load model and graph once at startup
model = CardComboGNN(128, 64)
model.load_state_dict(torch.load('models/gnn_model.pt', map_location='cpu'))
model.eval()

graph_data = torch.load('data/graph_data.pt')
card_id_to_idx = torch.load('data/card_id_map.pt')

@app.post("/recommend/cards")
def recommend_synergies(card_id: str, top_k: int = 10):
    """Find cards that synergize with given card"""
    card_idx = card_id_to_idx[card_id]

    with torch.no_grad():
        embeddings = model(graph_data.x, graph_data.edge_index)
        card_emb = embeddings[card_idx]

        # Cosine similarity
        similarities = F.cosine_similarity(
            card_emb.unsqueeze(0),
            embeddings
        )

        top_indices = torch.argsort(similarities, descending=True)[1:top_k+1]

    return {
        "recommendations": [
            {
                "card_idx": int(idx),
                "similarity": float(similarities[idx])
            }
            for idx in top_indices
        ]
    }
```

**Hardware Requirements**:
- CPU: 4+ cores (8+ recommended)
- RAM: 4 GB
- GPU (optional): Any modern GPU (GTX 1060+)
- Storage: 2 GB

**Performance**:
- CPU inference: 50-100ms per query
- GPU inference: 10-20ms per query

---

## 4. Small Transformer Models (DistilBERT, TinyBERT)

### Why Good for Self-Hosting

✅ **Compact**: 200-800 MB
✅ **Fast on CPU**: 20-100ms inference
✅ **Versatile**: Classification, embeddings, Q&A
✅ **Pre-trained**: Fine-tune on your data

### Use Case: Combo Win Condition Classifier

```python
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch

# Model: distilbert-base-uncased
# Size: 255 MB
# Speed: ~50ms on CPU

model_name = "distilbert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(
    model_name,
    num_labels=10  # 10 win condition types
)

# Fine-tune on combo descriptions
# ... training code ...

# Save fine-tuned model
model.save_pretrained('models/combo_classifier')
tokenizer.save_pretrained('models/combo_classifier')

# Inference
def classify_combo(description: str):
    inputs = tokenizer(description, return_tensors="pt", truncation=True, max_length=512)

    with torch.no_grad():
        outputs = model(**inputs)
        predictions = torch.softmax(outputs.logits, dim=-1)

    labels = ["infinite_mana", "infinite_damage", "infinite_life",
              "mill", "token_generation", "card_draw", "instant_win",
              "lockdown", "value_engine", "other"]

    top_3 = torch.argsort(predictions[0], descending=True)[:3]

    return [
        {"label": labels[idx], "confidence": float(predictions[0][idx])}
        for idx in top_3
    ]

# Example
classify_combo("Cast Sol Ring, bounce it with Hullbreaker Horror, repeat for infinite mana")
# Output: [{"label": "infinite_mana", "confidence": 0.95}, ...]
```

### Serving Transformer Model

```python
from fastapi import FastAPI
from transformers import pipeline

app = FastAPI()

# Load model once (not per request!)
classifier = pipeline(
    "text-classification",
    model="models/combo_classifier",
    device=-1  # CPU (use 0 for GPU)
)

@app.post("/classify/combo")
def classify_combo(description: str):
    """Classify combo win condition"""
    results = classifier(description, top_k=3)
    return {"predictions": results}
```

**Hardware Requirements**:
- CPU: 4+ cores
- RAM: 2-4 GB
- GPU (optional): Any modern GPU
- Storage: 1 GB

**Optimization: ONNX Runtime**

```python
# Convert to ONNX for 2-3x faster inference
from optimum.onnxruntime import ORTModelForSequenceClassification

model = ORTModelForSequenceClassification.from_pretrained(
    "models/combo_classifier",
    export=True
)

# Inference is now 2-3x faster on CPU!
```

---

## 5. Vector Database for Embeddings (Self-Hosted)

### Why Use a Vector DB

✅ **Fast similarity search**: <10ms for millions of vectors
✅ **Persistent storage**: Don't recompute embeddings
✅ **Scalable**: Handle growing datasets
✅ **Easy to deploy**: Docker containers

### Best Self-Hosted Vector DBs

#### Option 1: Qdrant (RECOMMENDED)

```yaml
# docker-compose.yml
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - ./qdrant_storage:/qdrant/storage
```

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Connect to Qdrant
client = QdrantClient(host="localhost", port=6333)

# Create collection
client.create_collection(
    collection_name="cards",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
)

# Insert embeddings
points = [
    PointStruct(
        id=i,
        vector=embedding.tolist(),
        payload={"card_id": card_id, "name": name}
    )
    for i, (card_id, name, embedding) in enumerate(card_data)
]

client.upsert(collection_name="cards", points=points)

# Search
results = client.search(
    collection_name="cards",
    query_vector=query_embedding.tolist(),
    limit=10
)

for result in results:
    print(f"{result.payload['name']}: {result.score}")
```

**Hardware Requirements**:
- CPU: 2+ cores
- RAM: 2-4 GB (+ vector storage)
- Storage: 1 GB + (num_vectors × vector_dim × 4 bytes)

**Storage Calculation**:
- 7,085 cards × 384 dims × 4 bytes = ~11 MB
- 72,226 combos × 384 dims × 4 bytes = ~111 MB
- Total: ~122 MB (very manageable!)

#### Option 2: Milvus Lite

```python
from pymilvus import MilvusClient

# Embedded Milvus (no separate server needed)
client = MilvusClient("milvus_demo.db")

# Create collection
client.create_collection(
    collection_name="cards",
    dimension=384,
    metric_type="COSINE"
)

# Insert data
client.insert(
    collection_name="cards",
    data=[
        {"id": i, "vector": emb.tolist(), "card_id": card_id}
        for i, (card_id, emb) in enumerate(card_embeddings)
    ]
)

# Search
results = client.search(
    collection_name="cards",
    data=[query_embedding.tolist()],
    limit=10
)
```

#### Option 3: Chroma (Simplest)

```python
import chromadb

# Create client (embedded mode)
client = chromadb.Client()

# Create collection
collection = client.create_collection(
    name="cards",
    metadata={"hnsw:space": "cosine"}
)

# Add embeddings
collection.add(
    embeddings=card_embeddings.tolist(),
    metadatas=[{"card_id": cid, "name": name} for cid, name in card_info],
    ids=[str(i) for i in range(len(card_embeddings))]
)

# Query
results = collection.query(
    query_embeddings=[query_embedding.tolist()],
    n_results=10
)
```

---

## 6. Complete Self-Hosted Architecture

### Recommended Stack (All Self-Hosted)

```
┌─────────────────┐
│   PostgreSQL    │ ← Card/Combo data
└────────┬────────┘
         │
┌────────▼────────┐
│  FastAPI Server │ ← API endpoints
└────────┬────────┘
         │
    ┌────┴─────────────────┐
    │                      │
┌───▼────────┐    ┌───────▼──────┐
│   Qdrant   │    │ XGBoost      │
│ (Vectors)  │    │ (Predictions)│
└────────────┘    └──────────────┘
```

### Docker Compose Full Stack

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: commander_spellbook
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - ./postgres_data:/var/lib/postgresql/data
      - ./commander_spellbook_schema_optimized.sql:/docker-entrypoint-initdb.d/schema.sql
    ports:
      - "5432:5432"

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - ./qdrant_storage:/qdrant/storage

  api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - qdrant
    environment:
      DATABASE_URL: postgresql://postgres:password@postgres:5432/commander_spellbook
      QDRANT_HOST: qdrant
      QDRANT_PORT: 6333
    volumes:
      - ./models:/app/models
```

### API Server (app.py)

```python
from fastapi import FastAPI
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import xgboost as xgb
import psycopg2

app = FastAPI()

# Load models at startup
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
price_model = xgb.XGBRegressor()
price_model.load_model('models/price_predictor.json')

# Connect to services
qdrant = QdrantClient(host="qdrant", port=6333)
db = psycopg2.connect(os.getenv("DATABASE_URL"))

@app.post("/search/semantic")
def semantic_search(query: str, top_k: int = 10):
    """Semantic search using embeddings"""
    query_emb = embedding_model.encode(query)

    results = qdrant.search(
        collection_name="combos",
        query_vector=query_emb.tolist(),
        limit=top_k
    )

    return {"results": [r.payload for r in results]}

@app.post("/predict/price")
def predict_combo_price(card_count: int, color_count: int, popularity: int):
    """Predict combo price"""
    import numpy as np
    features = np.array([[card_count, color_count, popularity]])
    price = price_model.predict(features)[0]
    return {"predicted_price": float(price)}

@app.get("/combos/{combo_id}")
def get_combo(combo_id: str):
    """Get combo details from PostgreSQL"""
    cursor = db.cursor()
    cursor.execute("""
        SELECT v.*, array_agg(c.name) AS cards
        FROM variants v
        JOIN variant_cards vc ON v.id = vc.variant_id
        JOIN cards c ON vc.card_id = c.id
        WHERE v.id = %s
        GROUP BY v.id
    """, (combo_id,))

    result = cursor.fetchone()
    return {"combo": result}
```

---

## 7. Hardware Recommendations

### Minimal Setup (CPU-Only)

**Specs**:
- CPU: 4 cores (Intel i5 / AMD Ryzen 5)
- RAM: 8 GB
- Storage: 20 GB SSD
- Network: 100 Mbps

**Can Run**:
- ✅ Embedding models (MiniLM)
- ✅ XGBoost/LightGBM
- ✅ Qdrant vector DB
- ✅ PostgreSQL
- ✅ Small transformers (DistilBERT)

**Cost**: $5-10/month (DigitalOcean, Linode, Hetzner)

### Recommended Setup (CPU + Optional GPU)

**Specs**:
- CPU: 8 cores (Intel i7 / AMD Ryzen 7)
- RAM: 16 GB
- Storage: 50 GB SSD
- GPU (optional): GTX 1660 / RTX 3060 (6-12 GB VRAM)
- Network: 1 Gbps

**Can Run**:
- ✅ Everything in minimal setup
- ✅ GNN models (GraphSAGE)
- ✅ Larger transformers (BERT-base)
- ✅ Multiple models simultaneously

**Cost**: $20-40/month (cloud with GPU) or one-time $500-800 (home server)

### High-Performance Setup (Production)

**Specs**:
- CPU: 16+ cores (Intel Xeon / AMD EPYC)
- RAM: 32-64 GB
- Storage: 100+ GB NVMe SSD
- GPU: RTX 4090 / A6000 (24 GB VRAM)
- Network: 10 Gbps

**Can Run**:
- ✅ All models
- ✅ Large language models (7B-13B parameters)
- ✅ High-throughput inference (1000+ req/s)
- ✅ Real-time training/fine-tuning

**Cost**: $100-500/month (cloud) or one-time $3000-5000 (home server)

---

## 8. Deployment Checklist

### Step 1: Choose Your Models

**Easy Start** (recommended):
- [ ] Embedding model (MiniLM) for semantic search
- [ ] XGBoost for price prediction
- [ ] Qdrant for vector storage

**Advanced**:
- [ ] GNN for card synergy
- [ ] DistilBERT for classification
- [ ] Custom fine-tuned models

### Step 2: Set Up Infrastructure

- [ ] PostgreSQL database (schema applied)
- [ ] Vector database (Qdrant/Milvus/Chroma)
- [ ] API server (FastAPI)
- [ ] Docker Compose setup

### Step 3: Train Models

- [ ] Extract training data (SQL queries)
- [ ] Train embedding model (optional, use pre-trained)
- [ ] Train XGBoost model
- [ ] Train GNN (if using)
- [ ] Fine-tune transformer (if using)

### Step 4: Generate Embeddings

```python
# Generate embeddings for all cards and combos (one-time)
from sentence_transformers import SentenceTransformer
import psycopg2

model = SentenceTransformer('all-MiniLM-L6-v2')
conn = psycopg2.connect("dbname=commander_spellbook")

# Cards
cursor = conn.cursor()
cursor.execute("SELECT id, name, oracle_text FROM cards")

embeddings = []
for card_id, name, oracle_text in cursor.fetchall():
    text = f"{name}: {oracle_text}"
    emb = model.encode(text)
    embeddings.append((card_id, emb))

# Save to vector DB (Qdrant)
# ... upload code ...
```

### Step 5: Deploy

```bash
# Build and start all services
docker-compose up -d

# Check health
curl http://localhost:8000/health

# Test semantic search
curl -X POST http://localhost:8000/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query": "infinite mana", "top_k": 5}'
```

### Step 6: Monitor

- [ ] Set up logging (Prometheus + Grafana)
- [ ] Monitor API latency
- [ ] Track memory usage
- [ ] Set up alerts

---

## Summary: Best Models for Self-Hosting

### Top Recommendations (in order)

1. **Sentence-BERT (MiniLM)** - Embeddings
   - Size: 80 MB
   - Speed: 10ms
   - Use: Semantic search
   - **START HERE**

2. **XGBoost** - Price/Popularity Prediction
   - Size: <50 MB
   - Speed: <1ms
   - Use: Predictions, ranking

3. **Qdrant** - Vector Database
   - Storage: ~200 MB
   - Speed: <10ms search
   - Use: Fast similarity search

4. **GraphSAGE (GNN)** - Card Synergy
   - Size: 500 MB
   - Speed: 50ms (CPU)
   - Use: Recommendation engine

5. **DistilBERT** - Text Classification
   - Size: 255 MB
   - Speed: 50ms (CPU)
   - Use: Win condition classification

All of these can run on a $10/month VPS or a Raspberry Pi 4! 🚀
