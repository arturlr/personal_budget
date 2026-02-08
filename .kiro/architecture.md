# Project Architecture

## Overview
Personal Budget is a Flask-based finance management application with SQLite backend and vanilla JavaScript frontend.

## Technology Stack

### Backend
- **Framework**: Flask 3.x
- **Database**: SQLite with SQLAlchemy ORM
- **Migrations**: Flask-Migrate (Alembic)
- **Import**: ofxparse (OFX), csv (CSV)

### Frontend
- **UI**: Vanilla JavaScript, HTML5, CSS3
- **Charts**: Chart.js for visualizations
- **No framework**: Lightweight, server-rendered templates

## Project Structure

```
personal_budget/
├── backend/
│   ├── app.py                 # Flask app & REST API endpoints
│   ├── models.py              # SQLAlchemy models
│   ├── requirements.txt       # Python dependencies
│   ├── services/
│   │   ├── importer.py       # CSV/OFX import logic
│   │   ├── categorizer.py    # Auto-categorization engine
│   │   ├── accrual.py        # Accrual calculations
│   │   └── forecast.py       # Budget forecasting
│   ├── templates/
│   │   ├── transactions.html # Transaction management UI
│   │   ├── config.html       # Configuration screens
│   │   ├── dashboard.html    # Charts & visualizations
│   │   ├── cashflow.html     # Cash flow reports
│   │   └── accrual.html      # Accrual reports
│   ├── migrations/           # Database migrations
│   ├── instance/
│   │   └── budget.db         # SQLite database
│   └── test_data/            # Sample CSV files
├── docs/                     # Documentation
└── .kiro/                    # Steering files
```

## Key Components

### 1. Import System (services/importer.py)
- Supports CSV (3-col, 4-col) and OFX formats
- Hash-based deduplication using SHA-256
- Auto-detects credit card payments
- Applies categorization rules during import

### 2. Categorization Engine (services/categorizer.py)
- Pattern-based rule matching (case-insensitive)
- Priority-ordered rule evaluation
- Supports hierarchical categories (parent/subcategory)

### 3. REST API (app.py)
All endpoints return JSON and follow RESTful conventions:

**Transactions**
- `GET /api/transactions` - List with filters (date, account, category, status)
- `PATCH /api/transactions/<id>` - Update category, approval status

**Categories**
- `GET /api/categories` - Hierarchical list with subcategories
- `POST /api/categories` - Create category
- `PATCH /api/categories/<id>` - Update category
- `DELETE /api/categories/<id>` - Delete (with validation)

**Category Rules**
- `GET /api/category-rules` - List all rules
- `POST /api/category-rules` - Create rule
- `PATCH /api/category-rules/<id>` - Update rule
- `DELETE /api/category-rules/<id>` - Delete rule

**Accounts**
- `GET /api/accounts` - List all accounts
- `POST /api/accounts` - Create account
- `PATCH /api/accounts/<id>` - Update account
- `DELETE /api/accounts/<id>` - Delete account

**Forecast**
- `GET /api/forecast` - List forecast items
- `POST /api/forecast` - Create forecast item
- `PATCH /api/forecast/<id>` - Update forecast item
- `DELETE /api/forecast/<id>` - Delete forecast item

**Import**
- `POST /api/import` - Upload CSV/OFX file

### 4. Frontend Architecture

**Transactions Page (transactions.html)**
- Dual dropdown system: Category → Subcategory
- Cascading dropdowns (subcategory appears when parent selected)
- Bulk operations (approve multiple transactions)
- Filtering by date, account, category, status
- Checkbox selection for bulk actions

**Configuration Page (config.html)**
- Two view modes:
  1. **Text View**: Edit categories as text (income/expense separated)
  2. **List View**: Visual category tree with edit dialogs
- Change confirmation with diff preview
- Smart update logic (create/update/delete detection)

**Dashboard (dashboard.html)**
- Summary cards (income, expenses, net flow)
- Chart.js visualizations
- Category spending breakdown
- Monthly trends

## Data Flow

### Import Flow
```
CSV/OFX File
    ↓
importer.py (parse, deduplicate)
    ↓
categorizer.py (apply rules)
    ↓
Database (transactions table)
    ↓
UI (transactions page)
```

### Categorization Flow
```
Transaction memo
    ↓
Match against category_rules (by priority)
    ↓
Set suggested_category_id
    ↓
User reviews/approves
    ↓
Set category_id & is_approved=true
```

### Category Management Flow
```
Text Editor (income/expense separated)
    ↓
Parse & validate format
    ↓
Analyze changes (create/update/delete)
    ↓
Show confirmation dialog
    ↓
Execute API calls (POST/PATCH/DELETE)
    ↓
Reload categories
```

## Design Decisions

### 1. Hierarchical Categories
- Two-level hierarchy (parent → subcategory)
- Unique constraint on (name, parent_id) allows name reuse
- Example: "Home > Maintenance" and "Car > Maintenance"

### 2. Dual Dropdown UI
- First dropdown: Parent categories only
- Second dropdown: Subcategories of selected parent
- Appears/hides dynamically based on parent selection
- Cleaner than single dropdown with all options

### 3. Text-Based Category Editor
- Faster for bulk editing than clicking through dialogs
- Separate text areas for income vs expense
- Format: `Category | Subcategory | #color`
- Change preview before saving

### 4. Hash-Based Deduplication
- SHA-256 of (date, memo, amount)
- Prevents duplicate imports
- Unique constraint on hash column

### 5. Approval Workflow
- Transactions start as unapproved
- Must have category before approval
- Bulk approve for efficiency
- Can unapprove if needed

## Security Considerations

- No authentication (single-user desktop app)
- SQLite file-based (local only)
- No sensitive data exposure in API
- Input validation on all endpoints
- SQL injection prevented by SQLAlchemy ORM

## Performance Considerations

- Indexes on frequently queried columns
- Pagination support in API (not yet implemented in UI)
- Client-side filtering for small datasets
- Lazy loading of subcategories in dropdowns

## Future Enhancements

- Cash flow reports (Phase 6)
- Accrual method reporting (Phase 7)
- Budget vs actual comparison (Phase 8)
- Multi-user support with authentication
- Mobile-responsive design
- Export to CSV/Excel
- Recurring transaction templates
