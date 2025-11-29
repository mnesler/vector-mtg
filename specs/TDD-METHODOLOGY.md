# TDD Methodology - Strict Enforcement Guidelines

## Core Principles

This project enforces **strict Test-Driven Development (TDD)** for all code changes. No exceptions.

### The Red-Green-Refactor Cycle

Every code change MUST follow this cycle:

1. **RED**: Write a failing test first
2. **GREEN**: Write the minimum code to make the test pass
3. **REFACTOR**: Improve the code while keeping tests green

### Enforcement Rules

1. **No Production Code Without Tests**
   - Every function, component, and module MUST have tests written BEFORE implementation
   - Tests MUST fail initially (proving they test something real)
   - Only then can implementation code be written

2. **Test Coverage Requirements**
   - Minimum 90% code coverage for all new code
   - 100% coverage for critical paths (API calls, data transformations, user interactions)
   - Coverage reports MUST be generated before any PR

3. **Test Quality Standards**
   - Tests MUST be independent (no shared state between tests)
   - Tests MUST be deterministic (same input = same output)
   - Tests MUST be fast (< 5ms per unit test)
   - Tests MUST have clear descriptions (AAA pattern: Arrange, Act, Assert)

4. **Prohibited Practices**
   - Writing implementation code before tests
   - Skipping tests for "simple" changes
   - Commenting out failing tests
   - Using `test.skip()` or `it.skip()` without documented reason and timeline
   - Mocking more than necessary (prefer real implementations when fast enough)

## Test Types and When to Use Them

### Unit Tests (Required for Everything)

**When**: For every function, method, hook, utility, and type guard

**What to Test**:
- Pure functions with various inputs
- Component rendering with different props
- Hook state changes and side effects
- Error handling and edge cases
- Type guards and validators

**Tools**: Jest, React Testing Library

**Example Structure**:
```typescript
describe('ComponentName', () => {
  describe('when [condition]', () => {
    it('should [expected behavior]', () => {
      // Arrange: Set up test data
      // Act: Execute the code
      // Assert: Verify the result
    });
  });
});
```

### Integration Tests (Required for Connected Components)

**When**: For components that interact with multiple modules or external systems

**What to Test**:
- API client calls with mocked network responses
- Multi-component interactions
- State management flows
- Data transformation pipelines

**Tools**: Jest, MSW (Mock Service Worker) for API mocking

### End-to-End Tests (Required for Critical User Flows)

**When**: For complete user journeys through the application

**What to Test**:
- Search and filter flows
- Navigation between pages
- Form submissions
- Error states and recovery

**Tools**: Playwright or Cypress

## Testing Standards by Component Type

### React Components

**Required Tests**:
1. Renders without crashing
2. Renders correct content with default props
3. Renders correct content with various prop combinations
4. Handles user interactions correctly
5. Manages internal state correctly
6. Calls callbacks with correct arguments
7. Handles loading states
8. Handles error states
9. Accessibility (a11y) checks

**Example**:
```typescript
describe('CardDisplay', () => {
  it('renders without crashing', () => {
    render(<CardDisplay card={mockCard} />);
  });

  it('displays card name', () => {
    render(<CardDisplay card={mockCard} />);
    expect(screen.getByText(mockCard.name)).toBeInTheDocument();
  });

  it('displays card image when image_normal is provided', () => {
    const card = { ...mockCard, image_normal: 'http://example.com/image.jpg' };
    render(<CardDisplay card={card} />);
    expect(screen.getByAltText(card.name)).toHaveAttribute('src', card.image_normal);
  });

  it('calls onCardClick when card is clicked', () => {
    const onCardClick = jest.fn();
    render(<CardDisplay card={mockCard} onCardClick={onCardClick} />);
    fireEvent.click(screen.getByRole('button'));
    expect(onCardClick).toHaveBeenCalledWith(mockCard.id);
  });
});
```

### API Functions

**Required Tests**:
1. Successful API calls with expected parameters
2. Correct URL construction
3. Correct request headers
4. Correct request body (for POST/PUT)
5. Correct response parsing
6. Network error handling
7. HTTP error status handling (400, 404, 500, etc.)
8. Timeout handling
9. Parameter validation

**Example**:
```typescript
describe('searchCards', () => {
  it('makes GET request to correct endpoint', async () => {
    const mockResponse = { search_term: 'Lightning', count: 5, cards: [] };
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    });

    await searchCards('Lightning', 50, false);

    expect(fetch).toHaveBeenCalledWith(
      '/api/cards/search?name=Lightning&limit=50&include_nonplayable=false'
    );
  });

  it('throws error when response is not ok', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      statusText: 'Not Found',
    });

    await expect(searchCards('Invalid')).rejects.toThrow('Search failed: Not Found');
  });
});
```

### Utility Functions

**Required Tests**:
1. Happy path with typical inputs
2. Edge cases (empty, null, undefined, 0, negative numbers)
3. Boundary conditions
4. Type coercion behavior
5. Error cases

**Example**:
```typescript
describe('formatNumber', () => {
  it('formats large numbers with commas', () => {
    expect(formatNumber(1000)).toBe('1,000');
    expect(formatNumber(1000000)).toBe('1,000,000');
  });

  it('handles zero', () => {
    expect(formatNumber(0)).toBe('0');
  });

  it('handles negative numbers', () => {
    expect(formatNumber(-1000)).toBe('-1,000');
  });
});
```

### Custom Hooks

**Required Tests**:
1. Initial state
2. State updates
3. Side effects (API calls, subscriptions)
4. Cleanup functions
5. Dependency changes
6. Error states

**Example**:
```typescript
describe('useCardSearch', () => {
  it('initializes with empty results', () => {
    const { result } = renderHook(() => useCardSearch());
    expect(result.current.cards).toEqual([]);
    expect(result.current.loading).toBe(false);
  });

  it('sets loading state during search', async () => {
    const { result } = renderHook(() => useCardSearch());

    act(() => {
      result.current.search('Lightning');
    });

    expect(result.current.loading).toBe(true);
  });
});
```

## Test File Organization

### Directory Structure

```
ui/
├── app/
│   ├── page.tsx
│   ├── page.test.tsx
│   └── layout.tsx
├── lib/
│   ├── api.ts
│   ├── api.test.ts
│   ├── types.ts
│   └── types.test.ts
├── components/
│   ├── CardDisplay.tsx
│   ├── CardDisplay.test.tsx
│   ├── SearchBar.tsx
│   └── SearchBar.test.tsx
└── __tests__/
    ├── integration/
    │   └── card-search-flow.test.tsx
    └── e2e/
        └── user-journey.spec.ts
```

### Naming Conventions

- Unit tests: `ComponentName.test.tsx` or `functionName.test.ts`
- Integration tests: `feature-name-flow.test.tsx`
- E2E tests: `user-journey.spec.ts`

## Test Data Management

### Mock Data

**Create centralized mock data files**:

```typescript
// __mocks__/cardData.ts
export const mockCard: Card = {
  id: '550c74d4-1fcb-406a-b02a-639a760a4380',
  name: 'Lightning Bolt',
  mana_cost: '{R}',
  cmc: 1,
  type_line: 'Instant',
  oracle_text: 'Lightning Bolt deals 3 damage to any target.',
  set_code: 'lea',
  image_normal: 'https://cards.scryfall.io/normal/front/5/5/550c74d4.jpg',
};

export const mockSearchResponse: SearchResponse = {
  search_term: 'Lightning',
  count: 1,
  cards: [mockCard],
};
```

### Factory Functions

**Use factories for complex test data**:

```typescript
// __mocks__/factories.ts
export const createMockCard = (overrides?: Partial<Card>): Card => ({
  id: 'test-id',
  name: 'Test Card',
  type_line: 'Creature',
  ...overrides,
});

export const createMockRule = (overrides?: Partial<Rule>): Rule => ({
  id: 1,
  rule_name: 'test_rule',
  rule_text: 'Test rule text',
  ...overrides,
});
```

## Pre-Commit Hooks

### Required Checks (Enforced via Git Hooks)

1. **Run all tests**: All tests must pass
2. **Check coverage**: Must meet minimum thresholds
3. **Type checking**: `tsc --noEmit` must pass
4. **Linting**: `eslint` must pass with no errors

### Setup

```json
// package.json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "type-check": "tsc --noEmit",
    "lint": "eslint .",
    "pre-commit": "npm run type-check && npm run lint && npm run test:coverage"
  }
}
```

## Code Review Checklist

Every PR must include:

- [ ] All new code has corresponding tests written FIRST
- [ ] All tests pass
- [ ] Coverage meets minimum thresholds (90%+)
- [ ] No `test.skip()` or `it.skip()` unless documented
- [ ] Tests follow AAA pattern
- [ ] Tests are independent and deterministic
- [ ] Integration tests for multi-component features
- [ ] E2E tests for new user flows
- [ ] Test descriptions clearly explain what is being tested
- [ ] Mock data is realistic and comprehensive
- [ ] Error cases are tested
- [ ] Edge cases are tested

## TDD Workflow Example

### Adding a New Feature: "Filter Cards by Color"

#### Step 1: Write the Test (RED)

```typescript
// components/ColorFilter.test.tsx
describe('ColorFilter', () => {
  it('renders all five color options', () => {
    render(<ColorFilter onColorChange={jest.fn()} />);
    expect(screen.getByLabelText('White')).toBeInTheDocument();
    expect(screen.getByLabelText('Blue')).toBeInTheDocument();
    expect(screen.getByLabelText('Black')).toBeInTheDocument();
    expect(screen.getByLabelText('Red')).toBeInTheDocument();
    expect(screen.getByLabelText('Green')).toBeInTheDocument();
  });

  it('calls onColorChange when color is selected', () => {
    const onColorChange = jest.fn();
    render(<ColorFilter onColorChange={onColorChange} />);
    fireEvent.click(screen.getByLabelText('Blue'));
    expect(onColorChange).toHaveBeenCalledWith('U');
  });
});
```

Run test: `npm test` → **Test fails** ✓ (RED phase complete)

#### Step 2: Write Minimal Implementation (GREEN)

```typescript
// components/ColorFilter.tsx
export function ColorFilter({ onColorChange }: { onColorChange: (color: string) => void }) {
  return (
    <div>
      <button aria-label="White" onClick={() => onColorChange('W')}>W</button>
      <button aria-label="Blue" onClick={() => onColorChange('U')}>U</button>
      <button aria-label="Black" onClick={() => onColorChange('B')}>B</button>
      <button aria-label="Red" onClick={() => onColorChange('R')}>R</button>
      <button aria-label="Green" onClick={() => onColorChange('G')}>G</button>
    </div>
  );
}
```

Run test: `npm test` → **Test passes** ✓ (GREEN phase complete)

#### Step 3: Refactor (REFACTOR)

```typescript
// components/ColorFilter.tsx
const COLORS = [
  { label: 'White', code: 'W' },
  { label: 'Blue', code: 'U' },
  { label: 'Black', code: 'B' },
  { label: 'Red', code: 'R' },
  { label: 'Green', code: 'G' },
];

export function ColorFilter({ onColorChange }: { onColorChange: (color: string) => void }) {
  return (
    <div className="flex gap-2">
      {COLORS.map(({ label, code }) => (
        <button
          key={code}
          aria-label={label}
          onClick={() => onColorChange(code)}
          className="px-4 py-2 rounded"
        >
          {code}
        </button>
      ))}
    </div>
  );
}
```

Run test: `npm test` → **Tests still pass** ✓ (REFACTOR phase complete)

## Continuous Improvement

### Metrics to Track

1. **Test Coverage**: Monitor over time, should trend upward
2. **Test Execution Time**: Should remain fast (< 10s for all unit tests)
3. **Flaky Tests**: Track and eliminate immediately
4. **Bug Escape Rate**: Bugs found in production that had no tests

### Regular Reviews

- **Weekly**: Review test coverage reports
- **Per PR**: Enforce test requirements in code review
- **Monthly**: Refactor slow or brittle tests
- **Quarterly**: Update testing standards and tools

## Resources

- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [Testing Best Practices](https://testingjavascript.com/)
- [TDD Principles](https://www.amazon.com/Test-Driven-Development-Kent-Beck/dp/0321146530)

## Enforcement

Violations of TDD methodology will result in:
1. PR rejection
2. Required rework before merge
3. Team discussion of why TDD is critical

**Remember**: Tests are not optional. They are the specification of how the code should work.
