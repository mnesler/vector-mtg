# Rules Engine Management Application

## Purpose
A web application to help build, maintain, and validate the rules engine. Provides UI for rule creation, tracks statistics on rule coverage, and enables human review/manipulation of game rules and card interactions.

## Components

### Frontend (`/frontend`)
- **Rule Editor**: UI for creating and editing game rules
- **Card Interaction Viewer**: Visualize how cards interact
- **Stats Dashboard**: Show rule coverage, gaps, and metrics
- **Human Review Interface**: Flag and review edge cases
- **Test Case Builder**: Create test scenarios for rules

### Backend (`/backend`)
- **Rule Management API**: CRUD operations for rules
- **Stats Tracking**: Metrics on rule coverage and usage
- **Validation Engine**: Check rule consistency
- **Review Queue**: Manage human review tasks
- **Test Orchestration**: Run rule validation tests

### Tests (`/tests`)
- Frontend component tests
- API integration tests
- E2E tests for workflows

## Key Features

### 1. Rule Coverage Tracking
- Which cards have rules defined
- Which interactions are covered
- Gaps in rule coverage
- Priority ranking for missing rules

### 2. Human Review Queue
- Cards with ambiguous interactions
- New card releases needing rules
- Community-reported edge cases
- Validation of auto-generated rules

### 3. Rule Statistics
- Total rules defined
- Coverage percentage by set/format
- Most complex interactions
- Rule processing performance

### 4. Visual Rule Builder
- Drag-and-drop rule creation
- Template-based rules for common patterns
- Validation and testing within UI

## Tech Stack
- **Frontend**: Next.js (reuse existing `/ui`)
- **Backend**: FastAPI (extend existing API)
- **Database**: PostgreSQL (shared with rules engine)
- **UI Components**: Tailwind + Skeleton UI (already configured)

## Integration
- Reads from `project-rules-engine` database
- Updates rules used by rules engine
- Uses data from `project-data-collection` for card info

## Current Status
- Basic UI exists in `/ui`
- Needs dedicated rule management features
- Should integrate with existing FastAPI backend
