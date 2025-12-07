# MTG Rules Engine & Game State Solver

## Purpose
Build a backend system that can solve MTG game states and determine next valid states. This is the core rules engine that understands Magic: The Gathering game mechanics.

## Components

### Backend (`/backend`)
- **Game State Representation**: Data structures for board state, stack, zones
- **Rules Processor**: Core rules engine logic
- **State Solver**: Algorithms to determine valid next states
- **Interaction Handler**: Resolve card interactions and priority
- **API**: Expose rules engine via API

### Tests (`/tests`)
- Unit tests for rule processing
- Integration tests for complex game states
- Edge case validation

### Docs (`/docs`)
- Rules engine architecture
- API documentation
- Game state format specifications

## Current Status
- Basic rule classification exists in old `/scripts/api/rule_engine.py`
- Needs: Full game state representation, stack handling, priority system

## Dependencies
- PostgreSQL for card data
- Python rules engine
- Shared database schemas from `/shared`
