# Personal Budget - Finance Management App

A comprehensive personal finance application built with Flask and SQLite, featuring cash flow and accrual reporting, transaction categorization, and budget forecasting.

## Features

### ✅ Phase 1, 2, 3, 4 & 5 Complete
- **Multi-format Import**: CSV (3-col, 4-col) and OFX file support
- **Smart Categorization**: Rule-based automatic transaction categorization
- **Deduplication**: Hash-based duplicate transaction detection
- **Credit Card Detection**: Automatic identification of CC payments
- **REST API**: Complete CRUD operations for all entities
- **Hierarchical Categories**: Support for categories and subcategories
- **Account Management**: Multiple accounts with starting balances
- **Budget Forecasting**: Forecast items with frequency support
- **Transaction UI**: Web interface for managing and approving transactions
- **Filtering**: Date range, account, category, and status filters
- **Bulk Operations**: Approve multiple transactions at once
- **Configuration Screens**: Manage categories, rules, accounts, and forecast
- **Dashboard**: Interactive charts and visualizations with Chart.js
- **Summary Cards**: Income, expenses, net flow, and averages
- **Charts**: Category spending, monthly trends, expense breakdown

### 🚧 Coming Soon (Phases 6-9)
- Cash flow reports
- Accrual method reporting
- Budget vs actual comparison
- Polish & enhancements

## Project Structure

```
personal_budget/
├── backend/
│   ├── app.py                 # Flask application & API endpoints
│   ├── models.py              # Database models
│   ├── requirements.txt       # Python dependencies
│   ├── services/
│   │   ├── importer.py       # CSV/OFX import service
│   │   ├── categorizer.py    # Auto-categorization service
│   │   ├── accrual.py        # Accrual calculation (Phase 7)
│   │   └── forecast.py       # Budget forecast (Phase 8)
│   ├── migrations/           # Database migrations
│   ├── instance/
│   │   └── budget.db         # SQLite database
│   └── test_data/            # Sample CSV files
├── docs/
│   ├── implementation_plan.md
│   ├── phase1_complete.md
│   ├── phase2_complete.md
│   └── PHASE2_SUMMARY.md
└── .kiro/                    # Kiro AI steering files
```

## Quick Start

### Prerequisites
- Python 3.8+
- pip

### Installation

```bash
# Clone the repository
cd personal_budget

# Set up backend
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Initialize database
flask db upgrade

# (Optional) Set up test data
python setup_test_data.py

# Run the application
flask run
```

The web UI will be available at `http://localhost:5000`  
The API will be available at `http://localhost:5000/api`

## API Endpoints

### Import
- `POST /api/import` - Upload CSV or OFX file

### Transactions
- `GET /api/transactions` - List transactions (with filters)
- `PATCH /api/transactions/<id>` - Update transaction

### Categories
- `GET /api/categories` - List all categories (hierarchical)
- `POST /api/categories` - Create category
- `PATCH /api/categories/<id>` - Update category
- `DELETE /api/categories/<id>` - Delete category

### Category Rules
- `GET /api/category-rules` - List all rules
- `POST /api/category-rules` - Create rule
- `PATCH /api/category-rules/<id>` - Update rule
- `DELETE /api/category-rules/<id>` - Delete rule

### Accounts
- `GET /api/accounts` - List all accounts
- `POST /api/accounts` - Create account
- `PATCH /api/accounts/<id>` - Update account
- `DELETE /api/accounts/<id>` - Delete account

### Forecast
- `GET /api/forecast` - List forecast items
- `POST /api/forecast` - Create forecast item
- `PATCH /api/forecast/<id>` - Update forecast item
- `DELETE /api/forecast/<id>` - Delete forecast item

## Usage Examples

### Import a CSV file
```bash
curl -X POST http://localhost:5000/api/import \
  -F "file=@transactions.csv" \
  -F "account_id=1"
```

### Create a category
```bash
curl -X POST http://localhost:5000/api/categories \
  -H "Content-Type: application/json" \
  -d '{"name": "Groceries", "type": "expense", "color": "#ff0000"}'
```

### Create a categorization rule
```bash
curl -X POST http://localhost:5000/api/category-rules \
  -H "Content-Type: application/json" \
  -d '{"pattern": "WHOLE FOODS", "category_id": 1, "priority": 10}'
```

### Get unapproved transactions
```bash
curl "http://localhost:5000/api/transactions?approved=false"
```

## CSV Format Support

### 3-Column Format (QuickBooks compatible)
```csv
Date,Description,Amount
1/1/2026,Example payment,-100.00
1/1/2026,Example deposit,200.00
```

### 4-Column Format (QuickBooks compatible)
```csv
Date,Description,Credit,Debit
1/1/2026,Example payment,,100.00
1/1/2026,Example deposit,200.00,
```

## Database Models

- **Account**: Bank accounts with starting balances
- **Category**: Hierarchical categories (income/expense/transfer)
- **Transaction**: Financial transactions with categorization
- **CategoryRule**: Pattern-based auto-categorization rules
- **ForecastItem**: Budget forecast items

## Testing

```bash
cd backend
source venv/bin/activate

# Run Phase 2 tests
python test_phase2.py

# Test API endpoints (requires Flask running)
./test_api.sh
```

## Development Roadmap

- [x] **Phase 1**: Core foundations (models, database, Flask setup)
- [x] **Phase 2**: Import & categorization (CSV/OFX, rules, API)
- [x] **Phase 3**: Transactions UI
- [x] **Phase 4**: Config area (categories, rules, accounts, forecast)
- [x] **Phase 5**: Dashboard & visualizations
- [ ] **Phase 6**: Cash flow reports
- [ ] **Phase 7**: Accrual method logic & reports
- [ ] **Phase 8**: Forecast & budget comparison
- [ ] **Phase 9**: Polish & enhancements

## Technology Stack

- **Backend**: Flask, SQLAlchemy, Flask-Migrate
- **Database**: SQLite
- **Import**: ofxparse (OFX), csv (CSV)
- **Frontend**: TBD (Phase 3+)

## License

MIT

## Contributing

This is a personal project following the implementation plan in `docs/implementation_plan.md`.
