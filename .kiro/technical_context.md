# Personal Budget App - Technical Context

## Technology Stack

### Backend
- **Framework**: Flask 3.1.2
- **ORM**: SQLAlchemy 2.0.46 with Flask-SQLAlchemy 3.1.1
- **Migrations**: Flask-Migrate 4.1.0 (Alembic)
- **Database**: SQLite (file-based at backend/instance/budget.db)
- **File Parsing**: ofxparse 0.21 for OFX files, csv (stdlib) for CSV

### Python Version
- Python 3.8+ required
- Developed with Python 3.13

## Database Schema

### Tables
1. **accounts** - Bank/credit card accounts
2. **categories** - Hierarchical categories (self-referential)
3. **transactions** - Financial transactions
4. **category_rules** - Pattern matching rules for auto-categorization
5. **forecast_items** - Budget forecast entries

### Key Relationships
- Transaction → Account (many-to-one)
- Transaction → Category (many-to-one, nullable)
- Transaction → Category (suggested, many-to-one, nullable)
- Category → Category (parent, self-referential)
- CategoryRule → Category (many-to-one)
- ForecastItem → Category (many-to-one)

### Important Fields
- **Transaction.unique_hash**: SHA256 hash for deduplication
- **Transaction.is_credit_card_payment**: Flag to exclude from accrual reports
- **Transaction.accrual_***: Fields for Phase 7 accrual method
- **Category.parent_id**: Self-referential for subcategories

## API Patterns

### Request/Response Format
- All requests/responses use JSON (except file uploads)
- File uploads use multipart/form-data
- Dates in ISO format (YYYY-MM-DD)
- Decimal amounts as floats in JSON

### Query Parameters
- Filtering: `?approved=true&account_id=1`
- Date ranges: `?from=2026-01-01&to=2026-12-31`
- Boolean flags: `?exclude_cc_payments=true`

### Status Codes
- 200: Success (GET, PATCH, DELETE)
- 201: Created (POST)
- 400: Bad request (validation error)
- 404: Not found

## File Formats

### CSV 3-Column
```
Date,Description,Amount
01/15/2026,STORE NAME,-45.67
```
- Negative = expense, Positive = income

### CSV 4-Column
```
Date,Description,Credit,Debit
01/15/2026,STORE NAME,,45.67
```
- Credit = income, Debit = expense

### Date Formats Supported
- dd/mm/yyyy
- mm/dd/yyyy
- yyyy-mm-dd
- With day suffix: "20/11/2018 TUE"

## Service Layer

### importer.py
- Parses CSV (3-col, 4-col) and OFX files
- Generates unique hash for deduplication
- Returns transaction dicts for database insertion

### categorizer.py
- Matches transaction memos against rules
- Priority-based (higher priority checked first)
- Case-insensitive pattern matching
- Detects credit card payments

### accrual.py (Phase 7)
- Placeholder for accrual calculation logic

### forecast.py (Phase 8)
- Placeholder for budget forecasting logic

## Development Environment

### Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
flask db upgrade
```

### Running
```bash
flask run  # Runs on http://localhost:5000
```

### Testing
```bash
python test_phase2.py  # Unit tests
./test_api.sh          # API integration tests
```

## Common Operations

### Create Migration
```bash
flask db migrate -m "Description of change"
flask db upgrade
```

### Reset Database
```bash
rm instance/budget.db
flask db upgrade
```

### Import Test Data
```bash
curl -X POST http://localhost:5000/api/import \
  -F "file=@test_data/sample_3col.csv" \
  -F "account_id=1"
```

## Phase Implementation Status

### ✅ Phase 1 - Core Foundations
- Database models
- Flask setup
- Migrations initialized

### ✅ Phase 2 - Import & Categorization
- CSV/OFX import
- Auto-categorization
- Complete REST API
- Deduplication
- Credit card detection

### 🚧 Phase 3 - Transactions UI
- Not started

### 📋 Phases 4-9
- Planned (see implementation_plan.md)
