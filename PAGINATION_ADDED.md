# Pagination Feature Added

## Summary
Added pagination to all list endpoints to prevent unbounded query results and improve performance.

## Endpoints with Pagination

### 1. GET /api/transactions
**Query Parameters:**
- `page` (optional, default: 1) - Page number
- `per_page` (optional, default: 100, max: 1000) - Items per page
- All existing filters still work (from, to, account_id, category_id, approved, exclude_cc_payments)

**Response Format:**
```json
{
  "transactions": [
    {
      "id": 1,
      "account_id": 1,
      "date": "2026-01-15",
      "memo": "Grocery Store",
      "amount": "-45.67",
      ...
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 100,
    "total": 250,
    "pages": 3
  }
}
```

### 2. GET /api/category-rules
**Query Parameters:**
- `page` (optional, default: 1)
- `per_page` (optional, default: 100, max: 1000)

**Response Format:**
```json
{
  "rules": [
    {
      "id": 1,
      "pattern": "WHOLE FOODS",
      "category_id": 5,
      "subcategory_id": 12,
      "priority": 10
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 100,
    "total": 45,
    "pages": 1
  }
}
```

### 3. GET /api/forecast
**Query Parameters:**
- `page` (optional, default: 1)
- `per_page` (optional, default: 100, max: 1000)

**Response Format:**
```json
{
  "items": [
    {
      "id": 1,
      "name": "Rent",
      "category_id": 3,
      "amount": "1500.00",
      "frequency": "monthly",
      ...
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 100,
    "total": 12,
    "pages": 1
  }
}
```

## Implementation Details

### Pagination Helper Function
```python
def paginate_query(query, page=1, per_page=100, max_per_page=1000):
    """Apply pagination to a query"""
    per_page = min(per_page, max_per_page)  # Enforce max limit
    page = max(1, page)  # Ensure page >= 1
    
    total = query.count()
    items = query.limit(per_page).offset((page - 1) * per_page).all()
    
    return {
        'items': items,
        'page': page,
        'per_page': per_page,
        'total': total,
        'pages': (total + per_page - 1) // per_page
    }
```

### Key Features
- **Default page size**: 100 items
- **Maximum page size**: 1000 items (prevents abuse)
- **Automatic bounds checking**: Negative pages default to 1
- **Total count included**: Clients know how many pages exist
- **Efficient queries**: Uses LIMIT/OFFSET for database-level pagination

## Usage Examples

### Get first page of transactions (default 100 items)
```bash
curl http://localhost:5000/api/transactions
```

### Get second page with 50 items per page
```bash
curl "http://localhost:5000/api/transactions?page=2&per_page=50"
```

### Combine with filters
```bash
curl "http://localhost:5000/api/transactions?approved=false&page=1&per_page=25"
```

### Get all rules (if less than 100)
```bash
curl http://localhost:5000/api/category-rules
```

## Breaking Changes

⚠️ **IMPORTANT**: Response format has changed for these endpoints:

**Before:**
```json
[
  {"id": 1, ...},
  {"id": 2, ...}
]
```

**After:**
```json
{
  "transactions": [  // or "rules", "items"
    {"id": 1, ...},
    {"id": 2, ...}
  ],
  "pagination": {
    "page": 1,
    "per_page": 100,
    "total": 250,
    "pages": 3
  }
}
```

### Frontend Migration Required

Update your frontend code to access the data array:

**Before:**
```javascript
const transactions = await response.json();
transactions.forEach(t => { ... });
```

**After:**
```javascript
const data = await response.json();
data.transactions.forEach(t => { ... });

// Access pagination info
console.log(`Page ${data.pagination.page} of ${data.pagination.pages}`);
console.log(`Total: ${data.pagination.total} items`);
```

## Benefits

1. **Performance**: No more loading thousands of records at once
2. **Memory**: Reduced memory usage on both server and client
3. **UX**: Faster initial page loads
4. **Scalability**: Can handle databases with millions of records
5. **Flexibility**: Clients can choose page size based on their needs

## Testing

Run pagination tests:
```bash
cd backend
python3 test_pagination.py
```

Test with curl:
```bash
# Test basic pagination
curl "http://localhost:5000/api/transactions?page=1&per_page=10"

# Test max limit enforcement
curl "http://localhost:5000/api/transactions?per_page=5000"
# Should return per_page: 1000 (capped at max)

# Test invalid page (should default to 1)
curl "http://localhost:5000/api/transactions?page=-5"
```

## Notes

- Other endpoints (categories, accounts) don't have pagination yet as they typically have small datasets
- Report endpoints are not paginated as they return aggregated data
- Consider adding pagination to report endpoints if they return large result sets
