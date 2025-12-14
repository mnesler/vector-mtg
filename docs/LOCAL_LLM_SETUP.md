# Local LLM Setup Guide for Tag Extraction

**Cost: $0 (FREE!) vs $185-$250 for API**  
**Hardware Required: RTX 4070 Ti (12GB VRAM) ✅ You have this!**

---

## Why Use Local Models?

### Cost Savings
- **Claude 3.5 Haiku API:** ~$250 for 508K cards
- **GPT-4o-mini API:** ~$185 for 508K cards
- **Local Model:** **$0 (FREE!)**

### Other Benefits
- ✅ **Privacy:** All data stays on your machine
- ✅ **Unlimited re-runs:** Refine prompts without cost
- ✅ **No rate limits:** Process as fast as your GPU allows
- ✅ **Offline capability:** No internet dependency
- ✅ **Experimentation:** Try multiple models for free

---

## Recommended Models (12GB VRAM)

| Model | VRAM | Quality | Speed | Best For |
|-------|------|---------|-------|----------|
| **Qwen2.5-7B-Instruct** ⭐ | 5 GB | ⭐⭐⭐⭐⭐ | ~1 sec/card | **Best overall** - Excellent JSON |
| Llama-3.2-8B-Instruct | 6 GB | ⭐⭐⭐⭐⭐ | ~2 sec/card | Great reasoning |
| Mistral-7B-Instruct | 5 GB | ⭐⭐⭐⭐ | ~1 sec/card | Fast & reliable |

---

## Quick Start (5 Steps)

### 1. Install Ollama

```bash
# Install Ollama (takes ~2 minutes)
curl -fsSL https://ollama.com/install.sh | sh

# Verify installation
ollama --version
```

### 2. Pull Recommended Model

```bash
# Download Qwen2.5 7B (4-bit quantized, ~4.5GB)
ollama pull qwen2.5:7b-instruct-q4_K_M

# This takes ~5 minutes depending on internet speed
```

### 3. Test the Model

```bash
# Quick test to verify it works
ollama run qwen2.5:7b-instruct-q4_K_M "Say hello in JSON format"
```

### 4. Create Ollama Integration for extract_card_tags.py

Create `scripts/embeddings/ollama_client.py`:

```python
"""
Ollama API client for local LLM inference.
Compatible with extract_card_tags.py CardTagExtractor.
"""

import requests
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Ollama API client that mimics Anthropic/OpenAI interface.
    """
    
    def __init__(self, model: str = "qwen2.5:7b-instruct-q4_K_M", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.messages = OllamaMessages(self)
    
    def is_available(self) -> bool:
        """Check if Ollama server is running."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False


class OllamaMessages:
    """Messages API compatible with Anthropic's interface."""
    
    def __init__(self, client):
        self.client = client
    
    def create(
        self,
        model: str,
        max_tokens: int,
        temperature: float,
        system: str,
        messages: list
    ):
        """Create a completion (compatible with Anthropic API)."""
        
        # Build prompt
        prompt = f"{system}\n\n"
        for msg in messages:
            prompt += f"{msg['content']}\n"
        
        # Call Ollama API
        response = requests.post(
            f"{self.client.base_url}/api/generate",
            json={
                "model": self.client.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            },
            timeout=60
        )
        
        if response.status_code != 200:
            raise Exception(f"Ollama API error: {response.text}")
        
        result = response.json()
        
        # Return in Anthropic-compatible format
        return OllamaResponse(result['response'])


class OllamaResponse:
    """Response object compatible with Anthropic's format."""
    
    def __init__(self, text: str):
        self.content = [OllamaContent(text)]


class OllamaContent:
    """Content object compatible with Anthropic's format."""
    
    def __init__(self, text: str):
        self.text = text
```

### 5. Update extract_card_tags.py to Support Ollama

Add to the `CardTagExtractor.__init__()` method:

```python
# In CardTagExtractor.__init__(), add Ollama support
if provider is None:
    if os.getenv('USE_OLLAMA') == 'true':
        provider = 'ollama'
    elif os.getenv('ANTHROPIC_API_KEY'):
        provider = 'anthropic'
    elif os.getenv('OPENAI_API_KEY'):
        provider = 'openai'

# After existing provider setup, add:
elif self.provider == 'ollama':
    from embeddings.ollama_client import OllamaClient
    self.client = OllamaClient(api_key=api_key or llm_model)
    if not self.client.is_available():
        raise RuntimeError("Ollama server is not running. Start it with: ollama serve")
```

---

## Usage

### Set Environment Variable

Add to `.env`:
```bash
USE_OLLAMA=true
```

### Run Tag Extraction

```bash
cd /home/maxwell/vector-mtg
source venv/bin/activate

# Test on a few cards first
python scripts/embeddings/extract_card_tags.py

# Process all cards (runs overnight)
nohup python scripts/embeddings/batch_extract_tags.py > tag_extraction.log 2>&1 &
```

---

## Performance Estimates

### Processing Speed
- **Rate:** ~1 card/second (3,600 cards/hour)
- **Total time:** ~141 hours (5.9 days)
- **Can pause/resume:** Yes, saves progress to database

### GPU Usage
- **VRAM:** ~5-6 GB (leaves 6-7 GB free)
- **Power:** ~150-200W
- **Temperature:** Normal gaming temps

### Cost
- **Electricity:** ~$5-10 for 6 days (at $0.12/kWh)
- **API calls:** $0
- **Total cost:** ~$5-10 vs $185-250 for API

**Net savings: $175-245** 💰

---

## Quality Validation

### Test Before Full Run

```bash
# Extract from test_extraction_on_known_cards() in extract_card_tags.py
python -c "
from scripts.embeddings.extract_card_tags import CardTagExtractor

extractor = CardTagExtractor(provider='ollama')
extractor.load_tag_taxonomy()

# Test on Sol Ring
extraction = extractor.extract_tags(
    card_name='Sol Ring',
    oracle_text='{T}: Add {C}{C}.',
    type_line='Artifact'
)

print(f'Success: {extraction.extraction_successful}')
print(f'Tags: {[(t.tag, t.confidence) for t in extraction.tags]}')
"
```

### Expected Quality
- **Accuracy:** 85-95% (vs 95-98% for Claude/GPT-4)
- **JSON parsing:** 99%+ (models are trained for this)
- **Tag relevance:** Very good for explicit mechanics
- **Confidence scores:** Slightly less calibrated

### Quality Improvements
1. **Prompt engineering:** Refine prompts for better results (FREE!)
2. **Multi-model ensemble:** Run 2-3 models and combine results
3. **Human review:** Flag low-confidence tags (<0.7) for review
4. **Iterative refinement:** Re-run problematic cards with adjusted prompts

---

## Alternative Models to Try

If Qwen2.5 doesn't meet quality expectations, try these (all FREE):

```bash
# Meta's Llama 3.2 (8B)
ollama pull llama3.2:8b-instruct-q4_K_M

# Mistral 7B
ollama pull mistral:7b-instruct-q4_K_M

# Google Gemma 2 (9B)
ollama pull gemma2:9b-instruct-q4_K_M
```

Switch models by changing the `model` parameter in `OllamaClient()`.

---

## Troubleshooting

### Ollama server not running
```bash
# Start Ollama server
ollama serve
```

### Out of memory
```bash
# Use smaller 4-bit quantized models (already recommended)
# Or close other GPU applications
```

### Slow performance
```bash
# Check GPU usage
nvidia-smi

# Ensure Ollama is using GPU (not CPU)
ollama ps
```

### Poor quality results
1. Try a different model (llama3.2 or gemma2)
2. Adjust temperature (lower = more deterministic)
3. Refine the prompt in `prompt_builder.py`
4. Add more examples to the prompt

---

## Comparison Summary

| Aspect | Local (Ollama) | Claude API | GPT-4o-mini |
|--------|----------------|------------|-------------|
| **Cost** | ~$10 (electricity) | ~$250 | ~$185 |
| **Quality** | 85-95% | 95-98% | 90-95% |
| **Speed** | ~1 card/sec | ~1 card/sec | ~1 card/sec |
| **Privacy** | ✅ Local | ❌ Cloud | ❌ Cloud |
| **Setup** | 30 min | 5 min | 5 min |
| **Flexibility** | ✅ Unlimited | Rate limited | Rate limited |

---

## Recommendation

✅ **Start with local Ollama + Qwen2.5-7B**

**Why:**
1. **$175-245 cost savings** (98% cheaper)
2. **Good enough quality** for most tags
3. **Free to iterate** and improve prompts
4. **Can always fall back to API** for low-confidence tags

**Workflow:**
1. Run Qwen2.5 on all 508K cards (FREE)
2. Identify low-confidence tags (<0.7)
3. Optionally use Claude API for just those cards (~$10)
4. Total cost: ~$20 vs $250

**This is the best value approach!** 💰
