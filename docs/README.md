# Vector MTG Documentation

Complete documentation for the Vector MTG card search system.

## Quick Links

### 🚀 Getting Started
- [Main README](../README.md) - Project overview and quick start
- [Setup Advanced Search](setup/SETUP_ADVANCED_SEARCH.md) - Complete setup guide for advanced search features

### 📖 User Guides
- [Query Examples](guides/QUERY_EXAMPLES.md) - Example queries and API usage
- [Advanced Search Guide](../specs/ADVANCED_SEARCH_GUIDE.md) - Full feature documentation

### 🧪 Testing
- [Testing Summary](testing/TESTING_SUMMARY.md) - Overview of testing tools ⭐ START HERE
- [Embedding Testing Guide](testing/EMBEDDING_TESTING_GUIDE.md) - Comprehensive embedding quality testing
- [Quick Embedding Test](testing/QUICK_EMBEDDING_TEST.md) - Quick reference for embedding tests
- [Embedding Test Results](testing/EMBEDDING_TEST_RESULTS.md) - Latest test results and benchmarks
- [Search Testing Guide](testing/SEARCH_TESTING.md) - Search functionality testing
- [Search Test Cases](../tests/SEARCH_TEST_CASES.md) - Detailed test case documentation

### 📋 Specifications
Located in `/specs/`:
- [Advanced Search Guide](../specs/ADVANCED_SEARCH_GUIDE.md) - Complete feature documentation
- [Rule Engine Architecture](../specs/RULE_ENGINE_ARCHITECTURE.md) - System architecture
- [Implementation Guide](../specs/IMPLEMENTATION_GUIDE.md) - Development guidelines
- [Playability Filter](../specs/PLAYABILITY_FILTER_IMPLEMENTATION.md) - Token/nonplayable card filtering
- [Card Legality Filter Plan](../specs/CARD_LEGALITY_FILTER_PLAN.md) - Format legality filtering
- [Deduplication Strategy](../specs/DEDUPLICATION_STRATEGY.md) - Card deduplication approach
- [Phase 2 Roadmap](../specs/PHASE_2_ROADMAP.md) - Future features
- [Visualization Guide](../specs/VISUALIZATION_GUIDE.md) - Data visualization
- [TDD Methodology](../specs/TDD-METHODOLOGY.md) - Testing approach
- [TDD UI Testing Plan](../specs/TDD_UI_TESTING_PLAN.md) - UI testing strategy
- [Baseline Test Specifications](../specs/BASELINE-TEST-SPECIFICATIONS.md) - Test baselines

### 🔬 Research
Located in `/research/`:
- [Query Parser Fine-tuning](../research/query-parser-finetuning.md) - LLM fine-tuning research

---

## Document Organization

```
docs/
├── README.md (this file)
├── setup/
│   └── SETUP_ADVANCED_SEARCH.md        # Complete setup guide
├── guides/
│   └── QUERY_EXAMPLES.md               # API usage examples
└── testing/
    ├── TESTING_SUMMARY.md              # Testing overview ⭐
    ├── EMBEDDING_TESTING_GUIDE.md      # Full embedding test guide
    ├── QUICK_EMBEDDING_TEST.md         # Quick reference
    ├── EMBEDDING_TEST_RESULTS.md       # Latest results
    └── SEARCH_TESTING.md               # Search testing guide

specs/                                   # Technical specifications
├── ADVANCED_SEARCH_GUIDE.md            # Feature documentation
├── RULE_ENGINE_ARCHITECTURE.md         # Architecture
├── IMPLEMENTATION_GUIDE.md             # Development guide
├── PLAYABILITY_FILTER_IMPLEMENTATION.md
├── CARD_LEGALITY_FILTER_PLAN.md
├── DEDUPLICATION_STRATEGY.md
├── PHASE_2_ROADMAP.md
├── VISUALIZATION_GUIDE.md
├── TDD-METHODOLOGY.md
├── TDD_UI_TESTING_PLAN.md
├── BASELINE-TEST-SPECIFICATIONS.md
└── CLAUDE.md                           # AI assistant guidelines

tests/                                   # Test documentation
└── SEARCH_TEST_CASES.md                # Detailed test cases

research/                                # Research notes
└── query-parser-finetuning.md          # LLM research

sql/migrations/                          # Database migrations
└── README.md                           # Migration documentation
```

---

## Common Tasks

### I want to... → Read this:

#### Setup & Configuration
- **Set up advanced search** → [Setup Guide](setup/SETUP_ADVANCED_SEARCH.md)
- **Understand the query API** → [Query Examples](guides/QUERY_EXAMPLES.md)
- **Learn all features** → [Advanced Search Guide](../specs/ADVANCED_SEARCH_GUIDE.md)

#### Testing
- **Get started with testing** → [Testing Summary](testing/TESTING_SUMMARY.md)
- **Test embedding quality** → [Embedding Testing Guide](testing/EMBEDDING_TESTING_GUIDE.md)
- **Quick embedding check** → [Quick Embedding Test](testing/QUICK_EMBEDDING_TEST.md)
- **See latest test results** → [Embedding Test Results](testing/EMBEDDING_TEST_RESULTS.md)
- **Test search functionality** → [Search Testing Guide](testing/SEARCH_TESTING.md)

#### Development
- **Understand the architecture** → [Rule Engine Architecture](../specs/RULE_ENGINE_ARCHITECTURE.md)
- **Follow development guidelines** → [Implementation Guide](../specs/IMPLEMENTATION_GUIDE.md)
- **Learn TDD approach** → [TDD Methodology](../specs/TDD-METHODOLOGY.md)
- **Plan future features** → [Phase 2 Roadmap](../specs/PHASE_2_ROADMAP.md)

#### Specific Features
- **Filter non-playable cards** → [Playability Filter](../specs/PLAYABILITY_FILTER_IMPLEMENTATION.md)
- **Add format legality** → [Card Legality Filter Plan](../specs/CARD_LEGALITY_FILTER_PLAN.md)
- **Handle duplicate cards** → [Deduplication Strategy](../specs/DEDUPLICATION_STRATEGY.md)
- **Visualize data** → [Visualization Guide](../specs/VISUALIZATION_GUIDE.md)

---

## File Types

### Setup Guides (`/docs/setup/`)
Step-by-step instructions for setting up specific features.

### User Guides (`/docs/guides/`)
Examples and usage patterns for end users and API consumers.

### Testing Documentation (`/docs/testing/`)
Everything related to testing embedding quality and search functionality.

### Technical Specifications (`/specs/`)
Detailed technical documentation, architecture decisions, and implementation plans.

### Test Cases (`/tests/`)
Specific test scenarios and expected results.

### Research (`/research/`)
Experimental features and research notes.

---

## Maintenance

### Adding New Documentation

1. **Setup guides** → `docs/setup/`
2. **User guides/examples** → `docs/guides/`
3. **Testing documentation** → `docs/testing/`
4. **Technical specs** → `specs/`
5. **Test cases** → `tests/`
6. **Research notes** → `research/`

### Update this README when:
- Adding new documentation files
- Reorganizing folder structure
- Adding new features that need documentation

---

## Contributing

When documenting new features:

1. ✅ Use clear, descriptive titles
2. ✅ Include code examples
3. ✅ Add to appropriate directory
4. ✅ Update this README with links
5. ✅ Cross-reference related docs
6. ✅ Include "Quick Start" sections
7. ✅ Add troubleshooting where relevant

---

## Support

For questions or issues:
1. Check the relevant guide in this documentation
2. Review test cases in `/tests/`
3. Check specs for technical details in `/specs/`
