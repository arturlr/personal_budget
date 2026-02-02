# Personal Budget - Finance Management App

## Project Overview
A comprehensive personal finance application built with Flask and SQLite, featuring cash flow and accrual reporting, transaction categorization, and budget forecasting.

## Current Status
- **Phase 1**: ✅ Complete - Core foundations (models, database, Flask setup)
- **Phase 2**: ✅ Complete - Import & categorization (CSV/OFX, rules, API)
- **Phase 3**: ✅ Complete - Transactions UI
- **Phase 4**: ✅ Complete - Config area (categories, rules, accounts, forecast)
- **Phase 5**: ✅ Complete - Dashboard & visualizations
- **Phase 6**: 🚧 Next - Cash flow reports
- **Phases 7-9**: Planned

## Architecture

### Backend (Flask + SQLite)
- **app.py**: Flask application with REST API endpoints
- **models.py**: SQLAlchemy models (Account, Category, Transaction, CategoryRule, ForecastItem)
- **services/**: Business logic modules
  - importer.py: CSV/OFX parsing and import
  - categorizer.py: Auto-categorization with rules
  - accrual.py: Accrual calculation (Phase 7)
  - forecast.py: Budget forecasting (Phase 8)

### Database Models
- **Account**: Bank accounts with starting balances
- **Category**: Hierarchical categories (parent/child relationships)
- **Transaction**: Financial transactions with categorization and accrual fields
- **CategoryRule**: Pattern-based auto-categorization rules
- **ForecastItem**: Budget forecast items with frequency

### Key Features
- Multi-format import (CSV 3-col, 4-col, OFX)
- Hash-based transaction deduplication
- Priority-based category rule matching
- Credit card payment detection
- Hierarchical category structure
- Complete REST API

## Development Guidelines

### Code Style
- Minimal, focused implementations
- Clear function names and docstrings
- Follow Flask best practices
- Use SQLAlchemy ORM patterns

### Testing
- Test each phase with dedicated test scripts
- Verify API endpoints with curl/test scripts
- Test data in backend/test_data/

### Database Migrations
```bash
flask db migrate -m "Description"
flask db upgrade
```

## Implementation Plan
Follow `docs/implementation_plan.md` for detailed phase-by-phase roadmap.

## Next Steps (Phase 6)
- Build cash flow reports
- Monthly net cash flow view
- Spending by category reports
- Income by category reports
- Account balance tracking
- Drill-down capabilities
