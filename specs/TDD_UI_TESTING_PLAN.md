# TDD & UI Testing Plan - MTG Rule Engine UI

## Overview
This document outlines the implementation plan for strict Test-Driven Development (TDD), theme customization, and automated UI testing with headless browsers for the MTG Rule Engine Next.js application.

---

## 1. Strict TDD Implementation

### 1.1 Testing Framework Setup

**Goal**: Establish a comprehensive testing environment following TDD best practices.

**Tasks**:
- [ ] Install testing dependencies
  - Jest (test runner)
  - React Testing Library (component testing)
  - @testing-library/jest-dom (DOM matchers)
  - @testing-library/user-event (user interaction simulation)
  - jest-environment-jsdom (DOM environment)

**Commands**:
```bash
npm install --save-dev jest @testing-library/react @testing-library/jest-dom @testing-library/user-event jest-environment-jsdom
```

- [ ] Configure Jest (`jest.config.js`)
  - Set up Next.js compatibility
  - Configure module path aliases
  - Set up coverage thresholds (80% minimum)
  - Enable watch mode for development

- [ ] Create test setup file (`jest.setup.js`)
  - Import @testing-library/jest-dom matchers
  - Configure global test utilities
  - Mock Next.js router
  - Mock fetch/API calls

- [ ] Update `package.json` scripts
  ```json
  {
    "scripts": {
      "test": "jest",
      "test:watch": "jest --watch",
      "test:coverage": "jest --coverage",
      "test:ci": "jest --ci --coverage --maxWorkers=2"
    }
  }
  ```

### 1.2 TDD Workflow Process

**Red-Green-Refactor Cycle**:

1. **RED**: Write failing test first
   - Define expected behavior
   - Test should fail initially
   - Commit: `test: add failing test for [feature]`

2. **GREEN**: Write minimal code to pass
   - Implement only what's needed
   - Test should pass
   - Commit: `feat: implement [feature] to pass test`

3. **REFACTOR**: Improve code quality
   - Optimize implementation
   - Tests still pass
   - Commit: `refactor: improve [feature] implementation`

**Example TDD Workflow**:
```typescript
// 1. RED - Write test first (tests/components/CardSearch.test.tsx)
describe('CardSearch', () => {
  it('should display search results when user types card name', async () => {
    render(<CardSearch />);
    const input = screen.getByRole('textbox', { name: /search cards/i });

    await userEvent.type(input, 'Lightning Bolt');

    expect(await screen.findByText('Lightning Bolt')).toBeInTheDocument();
  });
});

// 2. GREEN - Implement component (components/CardSearch.tsx)
export function CardSearch() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);

  // Minimal implementation to pass test
  // ...
}

// 3. REFACTOR - Improve implementation
// Add error handling, loading states, debouncing, etc.
```

### 1.3 Test Coverage Requirements

**Coverage Targets**:
- **Statements**: 80% minimum
- **Branches**: 75% minimum
- **Functions**: 80% minimum
- **Lines**: 80% minimum

**What to Test**:
- ✅ Component rendering
- ✅ User interactions (clicks, typing, form submission)
- ✅ Conditional rendering
- ✅ API integration (mocked)
- ✅ Error handling
- ✅ Loading states
- ✅ Accessibility (a11y)

**What NOT to Test**:
- ❌ Implementation details
- ❌ Third-party libraries
- ❌ Next.js internals
- ❌ CSS/styling (use E2E for visual tests)

### 1.4 Test Organization

**Directory Structure**:
```
ui/
├── __tests__/
│   ├── components/
│   │   ├── CardSearch.test.tsx
│   │   ├── RuleExplorer.test.tsx
│   │   └── DeckAnalyzer.test.tsx
│   ├── pages/
│   │   └── index.test.tsx
│   └── utils/
│       └── api.test.ts
├── __mocks__/
│   ├── api.ts
│   └── next/router.ts
└── jest.setup.js
```

---

## 2. Theme Customization Plan

### 2.1 Theme System Architecture

**Goal**: Implement flexible, maintainable theming using Tailwind CSS v4.

**Approach**: CSS Variables + Tailwind Configuration

**Tasks**:
- [ ] Define color palette
- [ ] Create theme configuration
- [ ] Implement dark/light mode toggle
- [ ] Test theme switching

### 2.2 Color Palette Design

**MTG-Inspired Color Scheme**:

```css
/* app/globals.css */
@layer base {
  :root {
    /* Light mode - Default */
    --color-bg-primary: 250 250 250;      /* Nearly white */
    --color-bg-secondary: 243 244 246;    /* Light gray */
    --color-bg-accent: 255 255 255;       /* Pure white */

    --color-text-primary: 17 24 39;       /* Near black */
    --color-text-secondary: 75 85 99;     /* Medium gray */
    --color-text-muted: 156 163 175;      /* Light gray */

    /* MTG Mana Colors */
    --color-mana-white: 255 251 240;
    --color-mana-blue: 14 116 183;
    --color-mana-black: 21 20 26;
    --color-mana-red: 211 32 42;
    --color-mana-green: 0 115 62;

    /* Accent colors */
    --color-primary: 99 102 241;          /* Indigo */
    --color-success: 34 197 94;           /* Green */
    --color-warning: 251 191 36;          /* Amber */
    --color-error: 239 68 68;             /* Red */
  }

  [data-theme="dark"] {
    --color-bg-primary: 17 24 39;         /* Dark gray */
    --color-bg-secondary: 31 41 55;       /* Medium dark */
    --color-bg-accent: 55 65 81;          /* Lighter dark */

    --color-text-primary: 243 244 246;    /* Light gray */
    --color-text-secondary: 209 213 219;  /* Medium light */
    --color-text-muted: 156 163 175;      /* Medium gray */

    /* Keep mana colors same or adjust slightly for dark mode */
  }
}
```

### 2.3 Tailwind Configuration

**Update `tailwind.config.ts`**:
```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: 'rgb(var(--color-bg-primary) / <alpha-value>)',
          secondary: 'rgb(var(--color-bg-secondary) / <alpha-value>)',
          accent: 'rgb(var(--color-bg-accent) / <alpha-value>)',
        },
        text: {
          primary: 'rgb(var(--color-text-primary) / <alpha-value>)',
          secondary: 'rgb(var(--color-text-secondary) / <alpha-value>)',
          muted: 'rgb(var(--color-text-muted) / <alpha-value>)',
        },
        mana: {
          white: 'rgb(var(--color-mana-white) / <alpha-value>)',
          blue: 'rgb(var(--color-mana-blue) / <alpha-value>)',
          black: 'rgb(var(--color-mana-black) / <alpha-value>)',
          red: 'rgb(var(--color-mana-red) / <alpha-value>)',
          green: 'rgb(var(--color-mana-green) / <alpha-value>)',
        },
        primary: 'rgb(var(--color-primary) / <alpha-value>)',
        success: 'rgb(var(--color-success) / <alpha-value>)',
        warning: 'rgb(var(--color-warning) / <alpha-value>)',
        error: 'rgb(var(--color-error) / <alpha-value>)',
      },
    },
  },
  plugins: [],
};

export default config;
```

### 2.4 Theme Toggle Component (TDD)

**Test First** (`__tests__/components/ThemeToggle.test.tsx`):
```typescript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeToggle } from '@/components/ThemeToggle';

describe('ThemeToggle', () => {
  it('should toggle theme when clicked', async () => {
    render(<ThemeToggle />);
    const toggle = screen.getByRole('button', { name: /toggle theme/i });

    expect(document.documentElement.getAttribute('data-theme')).toBe('light');

    await userEvent.click(toggle);
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark');

    await userEvent.click(toggle);
    expect(document.documentElement.getAttribute('data-theme')).toBe('light');
  });

  it('should persist theme preference in localStorage', async () => {
    render(<ThemeToggle />);
    const toggle = screen.getByRole('button', { name: /toggle theme/i });

    await userEvent.click(toggle);
    expect(localStorage.getItem('theme')).toBe('dark');
  });
});
```

**Implementation** (`components/ThemeToggle.tsx`):
```typescript
'use client';

import { useEffect, useState } from 'react';

export function ThemeToggle() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  useEffect(() => {
    const saved = localStorage.getItem('theme') as 'light' | 'dark' | null;
    const initial = saved || 'light';
    setTheme(initial);
    document.documentElement.setAttribute('data-theme', initial);
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
  };

  return (
    <button
      onClick={toggleTheme}
      aria-label="Toggle theme"
      className="p-2 rounded-lg bg-bg-secondary hover:bg-bg-accent"
    >
      {theme === 'light' ? '🌙' : '☀️'}
    </button>
  );
}
```

### 2.5 Theme Implementation Checklist

- [ ] Write tests for ThemeToggle component (RED)
- [ ] Implement ThemeToggle component (GREEN)
- [ ] Refactor and add animations (REFACTOR)
- [ ] Update global CSS with theme variables
- [ ] Update all components to use theme colors
- [ ] Test theme persistence across page reloads
- [ ] Test system preference detection
- [ ] Add smooth theme transition animations

---

## 3. Automated UI Testing with Headless Browser

### 3.1 E2E Testing Framework Setup

**Goal**: Implement comprehensive end-to-end testing using Playwright.

**Why Playwright?**
- ✅ Fast and reliable
- ✅ Multi-browser support (Chromium, Firefox, WebKit)
- ✅ Auto-wait mechanisms
- ✅ Powerful debugging tools
- ✅ Built-in test generator
- ✅ Great TypeScript support

**Installation**:
```bash
npm install --save-dev @playwright/test
npx playwright install
```

### 3.2 Playwright Configuration

**Create `playwright.config.ts`**:
```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results/results.json' }],
  ],
  use: {
    baseURL: 'http://localhost:3002',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    // Mobile viewports
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3002',
    reuseExistingServer: !process.env.CI,
  },
});
```

### 3.3 E2E Test Structure

**Directory Structure**:
```
ui/
├── e2e/
│   ├── card-search.spec.ts
│   ├── rule-explorer.spec.ts
│   ├── deck-analyzer.spec.ts
│   ├── theme-switching.spec.ts
│   └── fixtures/
│       └── mockData.ts
├── playwright.config.ts
└── package.json
```

### 3.4 Example E2E Tests

**Card Search Flow** (`e2e/card-search.spec.ts`):
```typescript
import { test, expect } from '@playwright/test';

test.describe('Card Search', () => {
  test('should search for cards and display results', async ({ page }) => {
    await page.goto('/');

    // Fill search input
    await page.getByPlaceholder('Search for cards...').fill('Lightning Bolt');

    // Wait for results
    await expect(page.getByText('Lightning Bolt')).toBeVisible();

    // Verify card details are shown
    await expect(page.getByText('Instant')).toBeVisible();
    await expect(page.getByText(/deals 3 damage/i)).toBeVisible();
  });

  test('should filter by card type', async ({ page }) => {
    await page.goto('/');

    await page.getByPlaceholder('Search for cards...').fill('bird');
    await page.getByRole('button', { name: 'Creature' }).click();

    // All results should be creatures
    const cards = page.locator('[data-testid="card-result"]');
    await expect(cards.first()).toContainText('Creature');
  });

  test('should handle no results gracefully', async ({ page }) => {
    await page.goto('/');

    await page.getByPlaceholder('Search for cards...').fill('xyzabc123notreal');

    await expect(page.getByText(/no cards found/i)).toBeVisible();
  });
});
```

**Theme Switching** (`e2e/theme-switching.spec.ts`):
```typescript
import { test, expect } from '@playwright/test';

test.describe('Theme Switching', () => {
  test('should toggle between light and dark themes', async ({ page }) => {
    await page.goto('/');

    // Check initial theme (light)
    const html = page.locator('html');
    await expect(html).toHaveAttribute('data-theme', 'light');

    // Toggle to dark
    await page.getByRole('button', { name: /toggle theme/i }).click();
    await expect(html).toHaveAttribute('data-theme', 'dark');

    // Toggle back to light
    await page.getByRole('button', { name: /toggle theme/i }).click();
    await expect(html).toHaveAttribute('data-theme', 'light');
  });

  test('should persist theme preference', async ({ page, context }) => {
    await page.goto('/');

    // Set dark theme
    await page.getByRole('button', { name: /toggle theme/i }).click();

    // Reload page
    await page.reload();

    // Theme should still be dark
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  });
});
```

**Visual Regression Testing** (`e2e/visual.spec.ts`):
```typescript
import { test, expect } from '@playwright/test';

test.describe('Visual Regression', () => {
  test('homepage should match snapshot - light theme', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveScreenshot('homepage-light.png');
  });

  test('homepage should match snapshot - dark theme', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: /toggle theme/i }).click();
    await expect(page).toHaveScreenshot('homepage-dark.png');
  });

  test('card details modal should match snapshot', async ({ page }) => {
    await page.goto('/');
    await page.getByPlaceholder('Search for cards...').fill('Lightning Bolt');
    await page.getByText('Lightning Bolt').first().click();

    await expect(page.locator('[role="dialog"]')).toHaveScreenshot('card-modal.png');
  });
});
```

### 3.5 CI/CD Integration

**GitHub Actions Workflow** (`.github/workflows/ui-tests.yml`):
```yaml
name: UI Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: cd ui && npm ci
      - run: cd ui && npm run test:ci
      - uses: codecov/codecov-action@v3
        with:
          files: ./ui/coverage/coverage-final.json

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: cd ui && npm ci
      - run: cd ui && npx playwright install --with-deps
      - run: cd ui && npm run test:e2e
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: ui/playwright-report/
```

### 3.6 Package.json Scripts

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",

    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:ci": "jest --ci --coverage --maxWorkers=2",

    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui",
    "test:e2e:debug": "playwright test --debug",
    "test:e2e:headed": "playwright test --headed",
    "test:e2e:report": "playwright show-report",

    "test:all": "npm run test:ci && npm run test:e2e"
  }
}
```

---

## 4. Implementation Timeline

### Phase 1: Foundation (Week 1)
- [ ] Day 1-2: Set up Jest and React Testing Library
- [ ] Day 3-4: Write tests for existing components (retrofit TDD)
- [ ] Day 5: Set up Playwright and write first E2E test

### Phase 2: Theme System (Week 2)
- [ ] Day 1-2: TDD - ThemeToggle component
- [ ] Day 3: Define color palette and CSS variables
- [ ] Day 4: Update Tailwind configuration
- [ ] Day 5: Apply theme to all components (TDD approach)

### Phase 3: Comprehensive Testing (Week 3)
- [ ] Day 1-2: Write E2E tests for all main flows
- [ ] Day 3: Add visual regression tests
- [ ] Day 4: Set up CI/CD pipeline
- [ ] Day 5: Documentation and team training

### Phase 4: Refinement (Week 4)
- [ ] Day 1-2: Achieve 80% test coverage
- [ ] Day 3: Performance testing and optimization
- [ ] Day 4: Accessibility testing (a11y)
- [ ] Day 5: Final review and documentation

---

## 5. Best Practices & Guidelines

### 5.1 TDD Guidelines

1. **Always write tests first** - No exceptions
2. **Test behavior, not implementation**
3. **Keep tests simple and readable**
4. **One assertion per test** (when possible)
5. **Use descriptive test names** - `it('should display error when API fails')`
6. **Mock external dependencies** - API calls, timers, etc.
7. **Avoid testing third-party code**

### 5.2 E2E Testing Guidelines

1. **Test user journeys, not pages**
2. **Use data-testid for stable selectors**
3. **Avoid hard-coded waits** - Use Playwright's auto-wait
4. **Run tests in parallel** when possible
5. **Keep tests independent** - No shared state
6. **Use Page Object Model** for complex flows
7. **Take screenshots on failure**

### 5.3 Theme Guidelines

1. **Use semantic color names** - `bg-primary`, not `bg-gray-100`
2. **Support system preference** - Respect `prefers-color-scheme`
3. **Animate transitions** - Smooth theme switching
4. **Test accessibility** - Ensure sufficient contrast ratios
5. **Document color usage** - When to use each color

---

## 6. Success Metrics

### Coverage Goals
- ✅ Unit test coverage: **≥80%**
- ✅ E2E test coverage: **All critical user flows**
- ✅ Visual regression: **All main pages + components**

### Performance Targets
- ✅ Unit tests: **< 10s** total runtime
- ✅ E2E tests: **< 5min** total runtime
- ✅ CI/CD pipeline: **< 10min** end-to-end

### Quality Metrics
- ✅ Zero flaky tests
- ✅ All tests pass in CI before merge
- ✅ WCAG 2.1 AA compliance
- ✅ Lighthouse score: **≥90** across all metrics

---

## 7. Resources & References

### Documentation
- [Jest Documentation](https://jestjs.io/)
- [React Testing Library](https://testing-library.com/react)
- [Playwright Documentation](https://playwright.dev/)
- [Next.js Testing Guide](https://nextjs.org/docs/testing)
- [Tailwind CSS v4](https://tailwindcss.com/docs)

### Learning Resources
- [Testing JavaScript with Kent C. Dodds](https://testingjavascript.com/)
- [Playwright Tutorial Series](https://playwright.dev/docs/intro)
- [TDD Best Practices](https://martinfowler.com/bliki/TestDrivenDevelopment.html)

---

## 8. Next Steps

1. **Review this plan** with the team
2. **Set up development environment** following Phase 1
3. **Create first TDD example** to establish workflow
4. **Schedule weekly check-ins** to track progress
5. **Document learnings** for future reference

---

**Document Version**: 1.0
**Last Updated**: 2025-11-27
**Maintained By**: Development Team
