# LLM Provider Abstraction Layer

## Design Philosophy
- Provider-agnostic interface
- Easy swapping between providers
- Support for multiple providers simultaneously
- Graceful fallbacks

## Provider Interface (Stubbed)

```python
class LLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        messages: List[Dict],
        tools: List[Dict],
        temperature: float = 0.7
    ) -> LLMResponse:
        pass
    
    @abstractmethod
    async def stream(
        self,
        messages: List[Dict],
        tools: List[Dict]
    ) -> AsyncGenerator[str, None]:
        pass
```

## Supported Providers (Stubbed)

1. **OpenAIProvider** - GPT-4, GPT-3.5
2. **AnthropicProvider** - Claude 3
3. **LocalProvider** - Llama, Phi-3.5 (already loaded)
4. **HybridProvider** - Routes based on complexity

## Configuration

```python
LLM_CONFIG = {
    'primary': 'openai',  # To be chosen
    'fallback': 'local',
    'routing': {
        'simple': 'local',    # Query parsing, card lookup
        'complex': 'primary'   # Strategic reasoning, conversation
    }
}
```

**Status:** Stubbed - Implementation deferred pending provider choice
