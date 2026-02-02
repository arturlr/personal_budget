# Quick Reference - Personal Budget App

## Start Development

```bash
cd backend
source venv/bin/activate
flask run
```

## Common Commands

### Database
```bash
flask db migrate -m "description"  # Create migration
flask db upgrade                   # Apply migrations
rm instance/budget.db             # Reset database
```

### Testing
```bash
python test_phase2.py    # Run unit tests
./test_api.sh           # Test API endpoints
```

## API Quick Reference

### Import
```bash
POST /api/import
  -F "file=@file.csv"
  -F "account_id=1"
```

### Transactions
```bash
GET /api/transactions?approved=false&exclude_cc_payments=true
PATCH /api/transactions/1 -d '{"category_id": 2, "is_approved": true}'
```

### Categories
```bash
GET /api/categories
POST /api/categories -d '{"name": "Food", "type": "expense"}'
PATCH /api/categories/1 -d '{"name": "Groceries"}'
DELETE /api/categories/1
```

### Rules
```bash
GET /api/category-rules
POST /api/category-rules -d '{"pattern": "AMAZON", "category_id": 1, "priority": 10}'
```

### Accounts
```bash
GET /api/accounts
POST /api/accounts -d '{"name": "Checking", "starting_balance": 1000}'
```

## File Locations

- **Models**: `backend/models.py`
- **API Routes**: `backend/app.py`
- **Services**: `backend/services/`
- **Database**: `backend/instance/budget.db`
- **Migrations**: `backend/migrations/versions/`
- **Test Data**: `backend/test_data/`
- **Docs**: `docs/`

## Key Concepts

### Transaction Hash
SHA256 of: `account_id|date|memo|amount`

### Category Hierarchy
Categories can have parent_id → subcategories

### Auto-Categorization
1. Import transaction
2. Match memo against rules (by priority)
3. Set suggested_category_id
4. User approves → copies to category_id

### Credit Card Payments
Transactions with keywords: "credit card payment", "cc payment", "autopay"
Flagged with is_credit_card_payment=true
Excluded from accrual reports

## Next Phase: Transactions UI

Build frontend to:
- Display transactions in table
- Filter by date, account, category, approval
- Edit category/subcategory
- Approve transactions
- Bulk operations
