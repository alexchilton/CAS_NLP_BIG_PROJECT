# Documentation Directory

This directory contains comprehensive documentation for the D&D RAG System.

## 📚 Documentation Index

### System Guides

#### [WORLD_SYSTEM_COMPLETE.md](WORLD_SYSTEM_COMPLETE.md)
Complete guide to the World State & Exploration System:
- Location persistence
- Lazy location generation
- Travel system
- Test results (29 tests passing)
- How persistence works

#### [SHOP_SYSTEM_GUIDE.md](SHOP_SYSTEM_GUIDE.md)
Shop and merchant system documentation:
- How to buy/sell items
- Gold tracking
- Transaction validation
- Location-based shopping
- Reality check integration

#### [ITEM_PERSISTENCE_EXPLAINED.md](ITEM_PERSISTENCE_EXPLAINED.md)
How items work with lazy-generated locations:
- How locations are added to the map
- Item tracking with `location.moved_items`
- What's implemented vs. missing
- Future enhancements

### Development Guides

#### [HUGGINGFACE_DEPLOYMENT.md](HUGGINGFACE_DEPLOYMENT.md)
Deployment guide for Hugging Face Spaces:
- Environment setup
- API vs local modes
- Configuration
- Troubleshooting

#### [DEBUG_LOGGING.md](DEBUG_LOGGING.md)
Debug logging system documentation:
- How to enable/disable debug logs
- What gets logged
- Debug modes
- Performance tips

#### [plan_progress.md](plan_progress.md)
Development progress tracking:
- Feature roadmap
- Implementation status
- Historical progress

## 📂 Other Documentation

### Root Level
- [../README.md](../README.md) - Main project README
- [../TODO.md](../TODO.md) - Current tasks and priorities
- [../DONE.md](../DONE.md) - Completed features

### E2E Tests
- [../e2e_tests/README.md](../e2e_tests/README.md) - E2E testing guide
- [../e2e_tests/README_HALLUCINATION_TEST.md](../e2e_tests/README_HALLUCINATION_TEST.md) - Spell target validation tests
- [../e2e_tests/README_WORLD_EXPLORATION.md](../e2e_tests/README_WORLD_EXPLORATION.md) - World exploration E2E tests

## 🎯 Quick Start

**New to the project?** Start here:
1. Read [../README.md](../README.md) for project overview
2. Check [WORLD_SYSTEM_COMPLETE.md](WORLD_SYSTEM_COMPLETE.md) to understand the world system
3. Review [SHOP_SYSTEM_GUIDE.md](SHOP_SYSTEM_GUIDE.md) for shopping mechanics

**Want to contribute?**
1. Check [../TODO.md](../TODO.md) for current priorities
2. Review [plan_progress.md](plan_progress.md) for feature status
3. Read [DEBUG_LOGGING.md](DEBUG_LOGGING.md) for debugging

**Deploying?**
1. See [HUGGINGFACE_DEPLOYMENT.md](HUGGINGFACE_DEPLOYMENT.md)

## 🧪 Tests

All systems have comprehensive tests:
- `test_world_system.py` - 11 tests for static world
- `test_lazy_generation.py` - 10 tests for procedural generation
- `test_location_items.py` - 8 tests for item persistence
- `test_shop_system.py` - Shop transaction tests
- `test_reality_check.py` - Action validation tests
- `test_mechanics_system.py` - Mechanics extraction/application
- `e2e_tests/` - Selenium end-to-end tests

**Total: 29+ unit tests, all passing ✅**

## 📦 Architecture

```
D&D RAG System
├── Core Systems
│   ├── ChromaDB (RAG retrieval)
│   ├── Ollama (Local LLM)
│   └── GameMaster (Orchestration)
│
├── Game Systems
│   ├── World State (locations, travel, persistence)
│   ├── Shop System (buy/sell, gold)
│   ├── Combat System (initiative, turns)
│   ├── Action Validator (reality check)
│   └── Mechanics Translator (narrative → state)
│
└── UI
    ├── Gradio Web Interface
    └── Character Creation
```

## 🚀 Recent Additions

- ✅ World State & Exploration System (Dec 26, 2025)
- ✅ Lazy Location Generation (Dec 26, 2025)
- ✅ Item Persistence Infrastructure (Dec 26, 2025)
- ✅ GM Contextual Awareness (Dec 26, 2025)
- ✅ Spell Target Validation (Dec 26, 2025)
- ✅ Party Mode UI Fix (Dec 26, 2025)

## 📧 Questions?

See the appropriate guide above or check the test files for examples!
