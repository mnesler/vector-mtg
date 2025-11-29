# Baseline Test Specifications

This document provides comprehensive test specifications for all existing components and modules in the Vector-MTG project. Each specification follows strict TDD principles and must be implemented before any changes to production code.

## Table of Contents

1. [Next.js UI Components](#nextjs-ui-components)
2. [API Layer](#api-layer)
3. [Type Definitions](#type-definitions)
4. [UI Prototype Components](#ui-prototype-components)
5. [Utility Functions](#utility-functions)

---

## Next.js UI Components

### 1. `app/page.tsx` - Home Page Component

**File**: `ui/app/page.test.tsx`

**Component Purpose**: Landing page with navigation cards to three main sections (Cards, Rules, Deck)

**Required Test Cases**:

```typescript
describe('Home Page', () => {
  describe('Page Rendering', () => {
    it('renders without crashing', () => {
      render(<Home />);
    });

    it('displays the main heading "MTG Rule Engine"', () => {
      render(<Home />);
      expect(screen.getByRole('heading', { name: /MTG Rule Engine/i, level: 1 })).toBeInTheDocument();
    });
  });

  describe('Navigation Cards', () => {
    it('renders three navigation cards', () => {
      render(<Home />);
      const cards = screen.getAllByRole('link');
      expect(cards).toHaveLength(3);
    });

    it('renders Card Explorer link with correct href', () => {
      render(<Home />);
      const cardExplorer = screen.getByRole('link', { name: /Card Explorer/i });
      expect(cardExplorer).toHaveAttribute('href', '/cards');
    });

    it('renders Card Explorer with description', () => {
      render(<Home />);
      expect(screen.getByText(/Search and browse Magic: The Gathering cards/i)).toBeInTheDocument();
    });

    it('renders Rules Browser link with correct href', () => {
      render(<Home />);
      const rulesBrowser = screen.getByRole('link', { name: /Rules Browser/i });
      expect(rulesBrowser).toHaveAttribute('href', '/rules');
    });

    it('renders Rules Browser with description', () => {
      render(<Home />);
      expect(screen.getByText(/Explore MTG rules and find cards that match specific mechanics/i)).toBeInTheDocument();
    });

    it('renders Deck Analyzer link with correct href', () => {
      render(<Home />);
      const deckAnalyzer = screen.getByRole('link', { name: /Deck Analyzer/i });
      expect(deckAnalyzer).toHaveAttribute('href', '/deck');
    });

    it('renders Deck Analyzer with description', () => {
      render(<Home />);
      expect(screen.getByText(/Analyze deck compositions and discover rule interactions/i)).toBeInTheDocument();
    });
  });

  describe('Features Section', () => {
    it('renders Features heading', () => {
      render(<Home />);
      expect(screen.getByRole('heading', { name: /Features/i, level: 3 })).toBeInTheDocument();
    });

    it('displays all 5 feature items', () => {
      render(<Home />);
      expect(screen.getByText(/Vector-powered semantic search across 500K\+ cards/i)).toBeInTheDocument();
      expect(screen.getByText(/Intelligent rule extraction and matching/i)).toBeInTheDocument();
      expect(screen.getByText(/Latest printing focus with playability filtering/i)).toBeInTheDocument();
      expect(screen.getByText(/Card image optimization via Scryfall/i)).toBeInTheDocument();
      expect(screen.getByText(/Real-time API integration/i)).toBeInTheDocument();
    });
  });

  describe('Styling and Layout', () => {
    it('applies container and padding classes', () => {
      const { container } = render(<Home />);
      const mainDiv = container.firstChild;
      expect(mainDiv).toHaveClass('container', 'mx-auto', 'px-4', 'py-8');
    });

    it('applies grid layout to navigation cards', () => {
      render(<Home />);
      const gridDiv = screen.getByRole('link', { name: /Card Explorer/i }).parentElement;
      expect(gridDiv).toHaveClass('grid', 'grid-cols-1', 'md:grid-cols-3', 'gap-6');
    });
  });

  describe('Accessibility', () => {
    it('has proper heading hierarchy', () => {
      render(<Home />);
      const h1 = screen.getByRole('heading', { level: 1 });
      const h2s = screen.getAllByRole('heading', { level: 2 });
      const h3 = screen.getByRole('heading', { level: 3 });

      expect(h1).toBeInTheDocument();
      expect(h2s).toHaveLength(3);
      expect(h3).toBeInTheDocument();
    });

    it('all links are keyboard accessible', () => {
      render(<Home />);
      const links = screen.getAllByRole('link');
      links.forEach(link => {
        expect(link).toHaveAttribute('href');
      });
    });
  });
});
```

**Coverage Target**: 100%

---

### 2. `app/layout.tsx` - Root Layout Component

**File**: `ui/app/layout.test.tsx`

**Component Purpose**: Root layout wrapper with metadata and global styles

**Required Test Cases**:

```typescript
describe('RootLayout', () => {
  describe('Layout Rendering', () => {
    it('renders children correctly', () => {
      render(
        <RootLayout>
          <div data-testid="test-child">Test Content</div>
        </RootLayout>
      );
      expect(screen.getByTestId('test-child')).toBeInTheDocument();
      expect(screen.getByText('Test Content')).toBeInTheDocument();
    });

    it('renders html element with lang attribute', () => {
      const { container } = render(
        <RootLayout>
          <div>Test</div>
        </RootLayout>
      );
      const html = container.querySelector('html');
      expect(html).toHaveAttribute('lang', 'en');
    });

    it('wraps children in body element', () => {
      const { container } = render(
        <RootLayout>
          <div data-testid="test-child">Test</div>
        </RootLayout>
      );
      const body = container.querySelector('body');
      expect(body).toBeInTheDocument();
      expect(body).toContainElement(screen.getByTestId('test-child'));
    });
  });

  describe('Metadata', () => {
    it('exports correct metadata title', () => {
      expect(metadata.title).toBe('MTG Rule Engine');
    });

    it('exports correct metadata description', () => {
      expect(metadata.description).toBe('Vector-powered Magic: The Gathering rule engine and card explorer');
    });
  });
});
```

**Coverage Target**: 100%

---

## API Layer

### 3. `lib/api.ts` - API Client Functions

**File**: `ui/lib/api.test.ts`

**Module Purpose**: HTTP client for backend API communication

**Required Test Cases**:

```typescript
describe('API Client', () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  describe('searchCards', () => {
    const mockSearchResponse: SearchResponse = {
      search_term: 'Lightning',
      count: 2,
      cards: [
        {
          id: 'card-1',
          name: 'Lightning Bolt',
          type_line: 'Instant',
        },
        {
          id: 'card-2',
          name: 'Lightning Strike',
          type_line: 'Instant',
        },
      ],
    };

    it('makes GET request to correct endpoint with default parameters', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockSearchResponse,
      });

      await searchCards('Lightning');

      expect(fetch).toHaveBeenCalledWith(
        '/api/cards/search?name=Lightning&limit=50&include_nonplayable=false'
      );
    });

    it('makes GET request with custom limit', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockSearchResponse,
      });

      await searchCards('Lightning', 100);

      expect(fetch).toHaveBeenCalledWith(
        '/api/cards/search?name=Lightning&limit=100&include_nonplayable=false'
      );
    });

    it('includes nonplayable cards when flag is true', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockSearchResponse,
      });

      await searchCards('Lightning', 50, true);

      expect(fetch).toHaveBeenCalledWith(
        '/api/cards/search?name=Lightning&limit=50&include_nonplayable=true'
      );
    });

    it('URL encodes card name with special characters', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockSearchResponse,
      });

      await searchCards('Jace, the Mind Sculptor');

      expect(fetch).toHaveBeenCalledWith(
        '/api/cards/search?name=Jace%2C+the+Mind+Sculptor&limit=50&include_nonplayable=false'
      );
    });

    it('returns parsed JSON response', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockSearchResponse,
      });

      const result = await searchCards('Lightning');

      expect(result).toEqual(mockSearchResponse);
    });

    it('throws error when response is not ok', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        statusText: 'Internal Server Error',
      });

      await expect(searchCards('Lightning')).rejects.toThrow('Search failed: Internal Server Error');
    });

    it('throws error when fetch fails', async () => {
      (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));

      await expect(searchCards('Lightning')).rejects.toThrow('Network error');
    });

    it('handles empty search term', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ search_term: '', count: 0, cards: [] }),
      });

      await searchCards('');

      expect(fetch).toHaveBeenCalledWith(
        '/api/cards/search?name=&limit=50&include_nonplayable=false'
      );
    });
  });

  describe('getSimilarCards', () => {
    const mockSimilarResponse: SimilarCardsResponse = {
      card_id: 'card-1',
      card_name: 'Lightning Bolt',
      count: 1,
      similar_cards: [
        {
          id: 'card-2',
          name: 'Lightning Strike',
          type_line: 'Instant',
        },
      ],
    };

    it('makes GET request to correct endpoint with default parameters', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockSimilarResponse,
      });

      await getSimilarCards('card-1');

      expect(fetch).toHaveBeenCalledWith(
        '/api/cards/card-1/similar?limit=20&include_nonplayable=false'
      );
    });

    it('includes rule filter when provided', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockSimilarResponse,
      });

      await getSimilarCards('card-1', 20, 'direct_damage');

      expect(fetch).toHaveBeenCalledWith(
        '/api/cards/card-1/similar?limit=20&include_nonplayable=false&rule_filter=direct_damage'
      );
    });

    it('URL encodes rule filter', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockSimilarResponse,
      });

      await getSimilarCards('card-1', 20, 'creature removal');

      expect(fetch).toHaveBeenCalledWith(
        '/api/cards/card-1/similar?limit=20&include_nonplayable=false&rule_filter=creature+removal'
      );
    });

    it('returns parsed JSON response', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockSimilarResponse,
      });

      const result = await getSimilarCards('card-1');

      expect(result).toEqual(mockSimilarResponse);
    });

    it('throws error when response is not ok', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        statusText: 'Not Found',
      });

      await expect(getSimilarCards('invalid-id')).rejects.toThrow('Failed to get similar cards: Not Found');
    });
  });

  describe('getCardsForRule', () => {
    const mockRuleCardsResponse: RuleCardsResponse = {
      rule_name: 'direct_damage',
      count: 2,
      cards: [
        {
          id: 'card-1',
          name: 'Lightning Bolt',
          type_line: 'Instant',
        },
      ],
    };

    it('makes GET request to correct endpoint with default parameters', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockRuleCardsResponse,
      });

      await getCardsForRule('direct_damage');

      expect(fetch).toHaveBeenCalledWith(
        '/api/rules/direct_damage/cards?limit=50&include_nonplayable=false'
      );
    });

    it('makes GET request with custom limit', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockRuleCardsResponse,
      });

      await getCardsForRule('direct_damage', 100);

      expect(fetch).toHaveBeenCalledWith(
        '/api/rules/direct_damage/cards?limit=100&include_nonplayable=false'
      );
    });

    it('includes nonplayable cards when flag is true', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockRuleCardsResponse,
      });

      await getCardsForRule('direct_damage', 50, true);

      expect(fetch).toHaveBeenCalledWith(
        '/api/rules/direct_damage/cards?limit=50&include_nonplayable=true'
      );
    });

    it('returns parsed JSON response', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockRuleCardsResponse,
      });

      const result = await getCardsForRule('direct_damage');

      expect(result).toEqual(mockRuleCardsResponse);
    });

    it('throws error when response is not ok', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        statusText: 'Bad Request',
      });

      await expect(getCardsForRule('invalid_rule')).rejects.toThrow('Failed to get cards for rule: Bad Request');
    });
  });

  describe('getAllRules', () => {
    const mockRulesResponse: RulesListResponse = {
      rules: [
        {
          id: 1,
          rule_name: 'direct_damage',
          rule_text: 'Deals damage to any target',
        },
        {
          id: 2,
          rule_name: 'creature_removal',
          rule_text: 'Destroys target creature',
        },
      ],
    };

    it('makes GET request to correct endpoint', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockRulesResponse,
      });

      await getAllRules();

      expect(fetch).toHaveBeenCalledWith('/api/rules');
    });

    it('returns parsed JSON response', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockRulesResponse,
      });

      const result = await getAllRules();

      expect(result).toEqual(mockRulesResponse);
    });

    it('throws error when response is not ok', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        statusText: 'Service Unavailable',
      });

      await expect(getAllRules()).rejects.toThrow('Failed to get rules: Service Unavailable');
    });

    it('handles empty rules list', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ rules: [] }),
      });

      const result = await getAllRules();

      expect(result.rules).toHaveLength(0);
    });
  });
});
```

**Coverage Target**: 100%

---

## Type Definitions

### 4. `lib/types.ts` - TypeScript Type Definitions

**File**: `ui/lib/types.test.ts`

**Module Purpose**: Type definitions and type guards

**Required Test Cases**:

```typescript
describe('Type Definitions', () => {
  describe('Card type', () => {
    it('accepts valid card with all required fields', () => {
      const card: Card = {
        id: 'test-id',
        name: 'Test Card',
        type_line: 'Creature - Human',
      };
      expect(card.id).toBe('test-id');
      expect(card.name).toBe('Test Card');
      expect(card.type_line).toBe('Creature - Human');
    });

    it('accepts card with optional fields', () => {
      const card: Card = {
        id: 'test-id',
        name: 'Test Card',
        type_line: 'Instant',
        mana_cost: '{U}',
        cmc: 1,
        oracle_text: 'Draw a card',
        set_code: 'lea',
        released_at: '1993-08-05',
        keywords: ['Flash'],
        image_small: 'http://example.com/small.jpg',
        image_normal: 'http://example.com/normal.jpg',
        image_large: 'http://example.com/large.jpg',
        rules: [],
      };
      expect(card.mana_cost).toBe('{U}');
      expect(card.keywords).toContain('Flash');
    });
  });

  describe('Rule type', () => {
    it('accepts valid rule with required fields', () => {
      const rule: Rule = {
        id: 1,
        rule_name: 'test_rule',
        rule_text: 'Test rule text',
      };
      expect(rule.id).toBe(1);
      expect(rule.rule_name).toBe('test_rule');
    });

    it('accepts rule with optional fields', () => {
      const rule: Rule = {
        id: 1,
        rule_name: 'test_rule',
        rule_text: 'Test rule text',
        pattern: 'test.*pattern',
        confidence: 0.95,
        parameter_bindings: { param1: 'value1' },
      };
      expect(rule.confidence).toBe(0.95);
      expect(rule.parameter_bindings?.param1).toBe('value1');
    });
  });

  describe('Legality type', () => {
    it('accepts valid legality object', () => {
      const legality: Legality = {
        standard: 'legal',
        commander: 'legal',
        modern: 'not_legal',
      };
      expect(legality.standard).toBe('legal');
      expect(legality.commander).toBe('legal');
    });

    it('accepts empty legality object', () => {
      const legality: Legality = {};
      expect(Object.keys(legality)).toHaveLength(0);
    });

    it('accepts custom format keys', () => {
      const legality: Legality = {
        custom_format: 'legal',
      };
      expect(legality.custom_format).toBe('legal');
    });
  });

  describe('SearchResponse type', () => {
    it('accepts valid search response', () => {
      const response: SearchResponse = {
        search_term: 'Lightning',
        count: 1,
        cards: [
          {
            id: 'card-1',
            name: 'Lightning Bolt',
            type_line: 'Instant',
          },
        ],
      };
      expect(response.search_term).toBe('Lightning');
      expect(response.count).toBe(1);
      expect(response.cards).toHaveLength(1);
    });

    it('accepts search response with no results', () => {
      const response: SearchResponse = {
        search_term: 'Nonexistent',
        count: 0,
        cards: [],
      };
      expect(response.count).toBe(0);
      expect(response.cards).toHaveLength(0);
    });
  });

  describe('SimilarCardsResponse type', () => {
    it('accepts valid similar cards response without rule filter', () => {
      const response: SimilarCardsResponse = {
        card_id: 'card-1',
        card_name: 'Lightning Bolt',
        count: 2,
        similar_cards: [],
      };
      expect(response.card_id).toBe('card-1');
      expect(response.rule_filter).toBeUndefined();
    });

    it('accepts similar cards response with rule filter', () => {
      const response: SimilarCardsResponse = {
        card_id: 'card-1',
        card_name: 'Lightning Bolt',
        rule_filter: 'direct_damage',
        count: 2,
        similar_cards: [],
      };
      expect(response.rule_filter).toBe('direct_damage');
    });
  });

  describe('RuleCardsResponse type', () => {
    it('accepts valid rule cards response', () => {
      const response: RuleCardsResponse = {
        rule_name: 'direct_damage',
        count: 5,
        cards: [],
      };
      expect(response.rule_name).toBe('direct_damage');
      expect(response.count).toBe(5);
    });
  });

  describe('RulesListResponse type', () => {
    it('accepts valid rules list response', () => {
      const response: RulesListResponse = {
        rules: [
          {
            id: 1,
            rule_name: 'test_rule',
            rule_text: 'Test',
          },
        ],
      };
      expect(response.rules).toHaveLength(1);
    });

    it('accepts empty rules list', () => {
      const response: RulesListResponse = {
        rules: [],
      };
      expect(response.rules).toHaveLength(0);
    });
  });
});
```

**Coverage Target**: 100%

---

## UI Prototype Components

### 5. `ui-proto/js/api.js` - API Client Class

**File**: `ui-proto/js/api.test.js`

**Module Purpose**: JavaScript class for API communication

**Required Test Cases**:

```javascript
describe('MTGRuleEngineAPI', () => {
  let api;

  beforeEach(() => {
    api = new MTGRuleEngineAPI('http://localhost:8000');
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  describe('constructor', () => {
    it('sets baseURL from parameter', () => {
      expect(api.baseURL).toBe('http://localhost:8000');
    });

    it('uses default baseURL when not provided', () => {
      const defaultApi = new MTGRuleEngineAPI();
      expect(defaultApi.baseURL).toBe('http://localhost:8000');
    });
  });

  describe('request method', () => {
    it('makes fetch request to correct URL', async () => {
      global.fetch.mockResolvedValue({
        ok: true,
        json: async () => ({ success: true }),
      });

      await api.request('/api/test');

      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/api/test', {});
    });

    it('returns parsed JSON response', async () => {
      const mockData = { data: 'test' };
      global.fetch.mockResolvedValue({
        ok: true,
        json: async () => mockData,
      });

      const result = await api.request('/api/test');

      expect(result).toEqual(mockData);
    });

    it('throws error when response is not ok', async () => {
      global.fetch.mockResolvedValue({
        ok: false,
        status: 404,
      });

      await expect(api.request('/api/test')).rejects.toThrow('HTTP error! status: 404');
    });

    it('logs error to console when request fails', async () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      global.fetch.mockRejectedValue(new Error('Network error'));

      await expect(api.request('/api/test')).rejects.toThrow('Network error');
      expect(consoleSpy).toHaveBeenCalledWith('API request failed:', expect.any(Error));

      consoleSpy.mockRestore();
    });

    it('passes options to fetch', async () => {
      global.fetch.mockResolvedValue({
        ok: true,
        json: async () => ({}),
      });

      const options = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      };

      await api.request('/api/test', options);

      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/api/test', options);
    });
  });

  describe('getStats', () => {
    it('calls request with correct endpoint', async () => {
      const spy = jest.spyOn(api, 'request').mockResolvedValue({});
      await api.getStats();
      expect(spy).toHaveBeenCalledWith('/api/stats');
    });
  });

  describe('getRuleStats', () => {
    it('calls request with correct endpoint', async () => {
      const spy = jest.spyOn(api, 'request').mockResolvedValue({});
      await api.getRuleStats();
      expect(spy).toHaveBeenCalledWith('/api/stats/rules');
    });
  });

  describe('searchCard', () => {
    it('calls request with encoded card name', async () => {
      const spy = jest.spyOn(api, 'request').mockResolvedValue({});
      await api.searchCard('Lightning Bolt');
      expect(spy).toHaveBeenCalledWith('/api/cards/search?name=Lightning%20Bolt');
    });

    it('handles special characters in card name', async () => {
      const spy = jest.spyOn(api, 'request').mockResolvedValue({});
      await api.searchCard('Jace, the Mind Sculptor');
      expect(spy).toHaveBeenCalledWith('/api/cards/search?name=Jace%2C%20the%20Mind%20Sculptor');
    });
  });

  describe('getCardsByRule', () => {
    it('calls request with rule name and default limit', async () => {
      const spy = jest.spyOn(api, 'request').mockResolvedValue({});
      await api.getCardsByRule('direct_damage');
      expect(spy).toHaveBeenCalledWith('/api/cards/search?rule=direct_damage&limit=50');
    });

    it('calls request with custom limit', async () => {
      const spy = jest.spyOn(api, 'request').mockResolvedValue({});
      await api.getCardsByRule('direct_damage', 100);
      expect(spy).toHaveBeenCalledWith('/api/cards/search?rule=direct_damage&limit=100');
    });
  });

  describe('getCard', () => {
    it('calls request with card ID', async () => {
      const spy = jest.spyOn(api, 'request').mockResolvedValue({});
      await api.getCard('card-123');
      expect(spy).toHaveBeenCalledWith('/api/cards/card-123');
    });
  });

  describe('getSimilarCards', () => {
    it('calls request with card ID and default limit without rule filter', async () => {
      const spy = jest.spyOn(api, 'request').mockResolvedValue({});
      await api.getSimilarCards('card-123');
      expect(spy).toHaveBeenCalledWith('/api/cards/card-123/similar?limit=20');
    });

    it('calls request with custom limit', async () => {
      const spy = jest.spyOn(api, 'request').mockResolvedValue({});
      await api.getSimilarCards('card-123', 50);
      expect(spy).toHaveBeenCalledWith('/api/cards/card-123/similar?limit=50');
    });

    it('includes rule filter when provided', async () => {
      const spy = jest.spyOn(api, 'request').mockResolvedValue({});
      await api.getSimilarCards('card-123', 20, 'direct_damage');
      expect(spy).toHaveBeenCalledWith('/api/cards/card-123/similar?limit=20&rule_filter=direct_damage');
    });
  });

  describe('listRules', () => {
    it('calls request with default limit and no category', async () => {
      const spy = jest.spyOn(api, 'request').mockResolvedValue({});
      await api.listRules();
      expect(spy).toHaveBeenCalledWith('/api/rules?limit=100');
    });

    it('includes category when provided', async () => {
      const spy = jest.spyOn(api, 'request').mockResolvedValue({});
      await api.listRules('Removal', 100);
      expect(spy).toHaveBeenCalledWith('/api/rules?limit=100&category=Removal');
    });

    it('uses custom limit', async () => {
      const spy = jest.spyOn(api, 'request').mockResolvedValue({});
      await api.listRules(null, 50);
      expect(spy).toHaveBeenCalledWith('/api/rules?limit=50');
    });
  });

  describe('getRuleCards', () => {
    it('calls request with rule name and default limit', async () => {
      const spy = jest.spyOn(api, 'request').mockResolvedValue({});
      await api.getRuleCards('direct_damage');
      expect(spy).toHaveBeenCalledWith('/api/rules/direct_damage/cards?limit=50');
    });

    it('uses custom limit', async () => {
      const spy = jest.spyOn(api, 'request').mockResolvedValue({});
      await api.getRuleCards('direct_damage', 100);
      expect(spy).toHaveBeenCalledWith('/api/rules/direct_damage/cards?limit=100');
    });
  });

  describe('getCategories', () => {
    it('calls request with correct endpoint', async () => {
      const spy = jest.spyOn(api, 'request').mockResolvedValue({});
      await api.getCategories();
      expect(spy).toHaveBeenCalledWith('/api/categories');
    });
  });

  describe('analyzeDeck', () => {
    it('calls request with POST method and card names', async () => {
      const spy = jest.spyOn(api, 'request').mockResolvedValue({});
      const cardNames = ['Lightning Bolt', 'Counterspell'];

      await api.analyzeDeck(cardNames);

      expect(spy).toHaveBeenCalledWith('/api/analyze/deck', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ cards: cardNames }),
      });
    });
  });

  describe('healthCheck', () => {
    it('calls request with correct endpoint', async () => {
      const spy = jest.spyOn(api, 'request').mockResolvedValue({});
      await api.healthCheck();
      expect(spy).toHaveBeenCalledWith('/health');
    });
  });
});
```

**Coverage Target**: 100%

---

## Utility Functions

### 6. Utility Functions - `ui-proto/js/api.js`

**File**: `ui-proto/js/utils.test.js`

**Module Purpose**: Utility functions for formatting and display

**Required Test Cases**:

```javascript
describe('Utility Functions', () => {
  describe('formatNumber', () => {
    it('formats numbers with thousands separator', () => {
      expect(formatNumber(1000)).toBe('1,000');
      expect(formatNumber(1000000)).toBe('1,000,000');
    });

    it('handles numbers less than 1000', () => {
      expect(formatNumber(999)).toBe('999');
      expect(formatNumber(1)).toBe('1');
      expect(formatNumber(0)).toBe('0');
    });

    it('handles negative numbers', () => {
      expect(formatNumber(-1000)).toBe('-1,000');
      expect(formatNumber(-999)).toBe('-999');
    });

    it('handles decimal numbers', () => {
      const result = formatNumber(1234.56);
      expect(result).toContain('1,234');
    });
  });

  describe('formatPercentage', () => {
    it('calculates percentage correctly', () => {
      expect(formatPercentage(50, 100)).toBe('50.0%');
      expect(formatPercentage(1, 4)).toBe('25.0%');
      expect(formatPercentage(1, 3)).toBe('33.3%');
    });

    it('handles zero total', () => {
      const result = formatPercentage(0, 0);
      expect(result).toMatch(/NaN%|Infinity%|0.0%/);
    });

    it('handles zero value', () => {
      expect(formatPercentage(0, 100)).toBe('0.0%');
    });

    it('formats to one decimal place', () => {
      expect(formatPercentage(2, 3)).toBe('66.7%');
    });

    it('handles values greater than total', () => {
      expect(formatPercentage(150, 100)).toBe('150.0%');
    });
  });

  describe('getCategoryColor', () => {
    it('returns correct color for known categories', () => {
      expect(getCategoryColor('Removal')).toBe('#ef4444');
      expect(getCategoryColor('Card Draw')).toBe('#3b82f6');
      expect(getCategoryColor('Mana Production')).toBe('#10b981');
    });

    it('returns default color for unknown category', () => {
      expect(getCategoryColor('Unknown Category')).toBe('#6b7280');
      expect(getCategoryColor('')).toBe('#6b7280');
    });

    it('is case sensitive', () => {
      expect(getCategoryColor('removal')).toBe('#6b7280');
      expect(getCategoryColor('REMOVAL')).toBe('#6b7280');
    });

    it('returns colors for all defined categories', () => {
      const categories = [
        'Removal',
        'Creature Removal',
        'Permanent Removal',
        'Card Draw',
        'Mana Production',
        'Evasion',
        'Token Generation',
        'Life Manipulation',
        'Counterspells',
        'Tutors',
        'Graveyard Recursion',
        'Exile Effects',
        'Protection',
        'Combat Tricks',
        'Triggered Abilities',
        'Activated Abilities',
      ];

      categories.forEach(category => {
        const color = getCategoryColor(category);
        expect(color).toMatch(/^#[0-9a-f]{6}$/);
        expect(color).not.toBe('#6b7280');
      });
    });
  });

  describe('truncate', () => {
    it('returns string unchanged when shorter than max length', () => {
      expect(truncate('Hello', 10)).toBe('Hello');
      expect(truncate('Test', 4)).toBe('Test');
    });

    it('truncates string when longer than max length', () => {
      expect(truncate('Hello World', 5)).toBe('Hello...');
      expect(truncate('This is a long string', 10)).toBe('This is a ...');
    });

    it('handles exact length match', () => {
      expect(truncate('Hello', 5)).toBe('Hello');
    });

    it('handles empty string', () => {
      expect(truncate('', 10)).toBe('');
    });

    it('handles null or undefined', () => {
      expect(truncate(null, 10)).toBe('');
      expect(truncate(undefined, 10)).toBe('');
    });

    it('adds ellipsis when truncating', () => {
      const result = truncate('Hello World', 8);
      expect(result).toContain('...');
      expect(result.length).toBe(11); // 8 chars + '...'
    });
  });
});
```

**Coverage Target**: 100%

---

## Component-Specific Test Patterns

### Pattern for Data Fetching Components

All components that fetch data must test:

1. Loading state display
2. Error state display
3. Empty state display
4. Success state with data
5. Retry mechanisms
6. Proper cleanup on unmount

**Example Template**:

```typescript
describe('DataFetchingComponent', () => {
  describe('Loading State', () => {
    it('displays loading indicator while fetching data', () => {
      // Test loading state
    });
  });

  describe('Error State', () => {
    it('displays error message when fetch fails', () => {
      // Test error state
    });

    it('allows retry after error', () => {
      // Test retry mechanism
    });
  });

  describe('Empty State', () => {
    it('displays empty state message when no data', () => {
      // Test empty state
    });
  });

  describe('Success State', () => {
    it('displays data when fetch succeeds', () => {
      // Test success state
    });
  });

  describe('Cleanup', () => {
    it('cancels pending requests on unmount', () => {
      // Test cleanup
    });
  });
});
```

---

## Integration Test Specifications

### Card Search Flow

**File**: `ui/__tests__/integration/card-search-flow.test.tsx`

**Test Scenarios**:

1. User enters card name and sees results
2. User filters results by rule
3. User clicks on card to see details
4. User views similar cards
5. User handles no results gracefully
6. User handles API errors

---

## E2E Test Specifications

### Complete User Journey

**File**: `ui/__tests__/e2e/user-journey.spec.ts`

**Test Scenarios**:

1. Navigate from home to card explorer
2. Search for a card
3. View card details
4. Navigate to rules browser
5. Find cards matching a rule
6. Navigate to deck analyzer
7. Analyze a deck

---

## Mock Data Repository

### Central Mock Data Files

**File**: `ui/__mocks__/cardData.ts`

```typescript
export const mockCard: Card = {
  id: '550c74d4-1fcb-406a-b02a-639a760a4380',
  name: 'Lightning Bolt',
  mana_cost: '{R}',
  cmc: 1,
  type_line: 'Instant',
  oracle_text: 'Lightning Bolt deals 3 damage to any target.',
  set_code: 'lea',
  released_at: '1993-08-05',
  keywords: [],
  image_normal: 'https://cards.scryfall.io/normal/front/5/5/550c74d4.jpg',
};

export const mockCards: Card[] = [
  mockCard,
  {
    id: 'abc123',
    name: 'Counterspell',
    mana_cost: '{U}{U}',
    cmc: 2,
    type_line: 'Instant',
    oracle_text: 'Counter target spell.',
    set_code: 'lea',
  },
];
```

**File**: `ui/__mocks__/ruleData.ts`

```typescript
export const mockRule: Rule = {
  id: 1,
  rule_name: 'direct_damage',
  rule_text: 'deals {n} damage to any target',
  pattern: 'deals \\d+ damage',
  confidence: 0.95,
};

export const mockRules: Rule[] = [
  mockRule,
  {
    id: 2,
    rule_name: 'counter_spell',
    rule_text: 'counter target spell',
  },
];
```

---

## Test Execution Requirements

### Pre-Commit Checks

All of these must pass before commit:

```bash
npm run type-check  # TypeScript compilation
npm run lint        # ESLint with no errors
npm run test        # All tests pass
npm run test:coverage  # Coverage thresholds met
```

### Coverage Thresholds

**File**: `jest.config.js`

```javascript
module.exports = {
  coverageThreshold: {
    global: {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90,
    },
    './lib/': {
      branches: 100,
      functions: 100,
      lines: 100,
      statements: 100,
    },
  },
};
```

---

## Next Steps

1. Install testing dependencies (Jest, React Testing Library, Playwright)
2. Configure Jest and test environment
3. Create mock data files
4. Implement baseline tests for each component (following RED phase of TDD)
5. Verify all tests fail initially
6. Begin GREEN phase only after all RED tests are written
7. Set up pre-commit hooks
8. Configure CI/CD pipeline

---

## Maintenance

This document should be updated whenever:

- New components are added
- New API endpoints are created
- New utility functions are written
- Testing patterns change
- Coverage requirements change

**Last Updated**: [Current Date]
**Version**: 1.0.0
