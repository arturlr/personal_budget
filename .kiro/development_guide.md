# Development Guide

## Setup

### Prerequisites
- Python 3.8+
- pip
- Virtual environment (recommended)

### Installation

```bash
cd personal_budget/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
flask db upgrade

# Run application
flask run
```

Application runs at `http://localhost:5000`

## Database Migrations

### Create Migration
```bash
flask db migrate -m "description of changes"
```

### Apply Migration
```bash
flask db upgrade
```

### Rollback Migration
```bash
flask db downgrade
```

### View Migration History
```bash
flask db history
```

## Common Development Tasks

### Add New Category
Via API:
```bash
curl -X POST http://localhost:5000/api/categories \
  -H "Content-Type: application/json" \
  -d '{"name": "Groceries", "type": "expense", "color": "#ff0000"}'
```

Via UI:
1. Go to `/config`
2. Edit text in Income or Expense section
3. Click "Save All"

### Add Subcategory
```bash
curl -X POST http://localhost:5000/api/categories \
  -H "Content-Type: application/json" \
  -d '{"name": "Gas", "type": "expense", "color": "#164374", "parent_id": 4}'
```

### Import Transactions
```bash
curl -X POST http://localhost:5000/api/import \
  -F "file=@transactions.csv" \
  -F "account_id=1"
```

### Add Categorization Rule
```bash
curl -X POST http://localhost:5000/api/category-rules \
  -H "Content-Type: application/json" \
  -d '{"pattern": "WHOLE FOODS", "category_id": 1, "priority": 10}'
```

## Testing

### Manual Testing
1. Import sample data: `python setup_test_data.py`
2. Navigate to `http://localhost:5000`
3. Test transaction categorization
4. Test bulk approval
5. Test category management

### API Testing
```bash
# Get all transactions
curl http://localhost:5000/api/transactions

# Filter by date range
curl "http://localhost:5000/api/transactions?from=2026-01-01&to=2026-12-31"

# Filter by account
curl "http://localhost:5000/api/transactions?account_id=1"

# Get unapproved transactions
curl "http://localhost:5000/api/transactions?approved=false"
```

## Debugging

### Enable Debug Mode
```bash
export FLASK_ENV=development
flask run
```

### View Database
```bash
# Using Python
python3 -c "from app import app; from models import db, Category; \
with app.app_context(): \
    cats = Category.query.all(); \
    [print(f'{c.id}: {c.name}') for c in cats]"
```

### Check Logs
Flask logs appear in terminal where `flask run` is executed.

### Browser Console
Open DevTools (F12) to see:
- JavaScript errors
- Network requests
- Console logs

## Code Style

### Python
- Follow PEP 8
- Use type hints where helpful
- Keep functions small and focused
- Document complex logic

### JavaScript
- Use modern ES6+ syntax
- Prefer `const` over `let`
- Use template literals for strings
- Keep functions pure when possible

### SQL
- Use SQLAlchemy ORM (avoid raw SQL)
- Define relationships in models
- Use migrations for schema changes

## Common Issues

### Migration Conflicts
If migrations conflict:
```bash
flask db stamp head  # Mark current state
flask db migrate -m "fix"  # Create new migration
flask db upgrade
```

### Database Locked
SQLite locks on concurrent writes. Restart Flask if stuck.

### Categories Not Loading
1. Check browser console for errors
2. Verify API returns data: `curl http://localhost:5000/api/categories`
3. Hard refresh browser (Ctrl+Shift+R)

### Unique Constraint Errors
Categories must be unique within their parent:
- "Home > Utilities" ✓
- "Home > Utilities" (duplicate) ✗
- "Car > Utilities" ✓ (different parent)

## File Locations

### Configuration
- Database: `backend/instance/budget.db`
- Migrations: `backend/migrations/versions/`
- Templates: `backend/templates/`

### Logs
- Flask logs: Terminal output
- Browser logs: DevTools Console

### Test Data
- Sample CSVs: `backend/test_data/`
- Setup script: `backend/setup_test_data.py`

## Deployment

### Production Considerations
1. Use production WSGI server (gunicorn, waitress)
2. Set `FLASK_ENV=production`
3. Use PostgreSQL instead of SQLite for multi-user
4. Add authentication/authorization
5. Enable HTTPS
6. Set up backups for database

### Example Production Setup
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## Contributing

1. Create feature branch
2. Make changes
3. Test thoroughly
4. Update documentation
5. Submit for review

## Resources

- Flask docs: https://flask.palletsprojects.com/
- SQLAlchemy docs: https://docs.sqlalchemy.org/
- Chart.js docs: https://www.chartjs.org/
