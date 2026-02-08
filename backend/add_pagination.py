#!/usr/bin/env python3
"""Add pagination to list endpoints"""

import re

with open('app.py', 'r') as f:
    content = f.read()

# Add pagination helper after to_str function
pagination_helper = '''def to_str(value):
    """Convert Decimal/numeric to string for JSON"""
    return str(value) if value is not None else None

def paginate_query(query, page=1, per_page=100, max_per_page=1000):
    """Apply pagination to a query"""
    per_page = min(per_page, max_per_page)
    page = max(1, page)
    
    total = query.count()
    items = query.limit(per_page).offset((page - 1) * per_page).all()
    
    return {
        'items': items,
        'page': page,
        'per_page': per_page,
        'total': total,
        'pages': (total + per_page - 1) // per_page
    }
'''

content = re.sub(
    r'def to_str\(value\):.*?return str\(value\) if value is not None else None',
    pagination_helper.strip(),
    content,
    flags=re.DOTALL
)

# Fix get_transactions with pagination
transactions_paginated = '''# Transaction endpoints
@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    query = Transaction.query.options(
        db.joinedload(Transaction.category),
        db.joinedload(Transaction.subcategory),
        db.joinedload(Transaction.suggested_category),
        db.joinedload(Transaction.suggested_subcategory)
    )
    
    if from_date := request.args.get('from'):
        query = query.filter(Transaction.date >= datetime.fromisoformat(from_date).date())
    if to_date := request.args.get('to'):
        query = query.filter(Transaction.date <= datetime.fromisoformat(to_date).date())
    if account_id := request.args.get('account_id', type=int):
        query = query.filter_by(account_id=account_id)
    if category_id := request.args.get('category_id', type=int):
        query = query.filter_by(category_id=category_id)
    if approved := request.args.get('approved'):
        query = query.filter_by(is_approved=approved.lower() == 'true')
    if request.args.get('exclude_cc_payments', 'false').lower() == 'true':
        query = query.filter_by(is_credit_card_payment=False)
    
    query = query.order_by(Transaction.date.desc())
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 100, type=int)
    result = paginate_query(query, page, per_page)
    
    return jsonify({
        'transactions': [{
            'id': t.id,
            'account_id': t.account_id,
            'date': t.date.isoformat(),
            'memo': t.memo,
            'amount': to_str(t.amount),
            'category_id': t.category_id,
            'subcategory_id': t.subcategory_id,
            'suggested_category_id': t.suggested_category_id,
            'suggested_subcategory_id': t.suggested_subcategory_id,
            'is_approved': t.is_approved,
            'is_credit_card_payment': t.is_credit_card_payment
        } for t in result['items']],
        'pagination': {
            'page': result['page'],
            'per_page': result['per_page'],
            'total': result['total'],
            'pages': result['pages']
        }
    })'''

content = re.sub(
    r'# Transaction endpoints\n@app\.route\(\'/api/transactions\'.*?\'is_credit_card_payment\': t\.is_credit_card_payment\s*\}\s*for t in result\[\'items\'\]\]\)',
    transactions_paginated,
    content,
    flags=re.DOTALL
)

# Fix get_rules with pagination
rules_paginated = '''# Category Rules endpoints
@app.route('/api/category-rules', methods=['GET'])
def get_rules():
    query = CategoryRule.query.order_by(CategoryRule.priority.desc())
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 100, type=int)
    result = paginate_query(query, page, per_page)
    
    return jsonify({
        'rules': [{
            'id': r.id,
            'pattern': r.pattern,
            'category_id': r.category_id,
            'subcategory_id': r.subcategory_id,
            'priority': r.priority
        } for r in result['items']],
        'pagination': {
            'page': result['page'],
            'per_page': result['per_page'],
            'total': result['total'],
            'pages': result['pages']
        }
    })'''

content = re.sub(
    r'# Category Rules endpoints\n@app\.route\(\'/api/category-rules\'.*?\'priority\': r\.priority\s*\}\s*for r in result\[\'items\'\]\]\)',
    rules_paginated,
    content,
    flags=re.DOTALL
)

# Fix get_forecast with pagination
forecast_paginated = '''# Forecast endpoints
@app.route('/api/forecast', methods=['GET'])
def get_forecast():
    query = ForecastItem.query
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 100, type=int)
    result = paginate_query(query, page, per_page)
    
    return jsonify({
        'items': [{
            'id': f.id,
            'name': f.name,
            'category_id': f.category_id,
            'subcategory_id': f.subcategory_id,
            'amount': to_str(f.amount),
            'frequency': f.frequency,
            'type': f.type,
            'start_date': f.start_date.isoformat(),
            'end_date': f.end_date.isoformat() if f.end_date else None
        } for f in result['items']],
        'pagination': {
            'page': result['page'],
            'per_page': result['per_page'],
            'total': result['total'],
            'pages': result['pages']
        }
    })'''

content = re.sub(
    r'# Forecast endpoints\n@app\.route\(\'/api/forecast\', methods=\[\'GET\'\]\)\ndef get_forecast\(\):.*?\'end_date\': f\.end_date\.isoformat\(\) if f\.end_date else None\s*\}\s*for f in result\[\'items\'\]\]\)',
    forecast_paginated,
    content,
    flags=re.DOTALL
)

with open('app.py', 'w') as f:
    f.write(content)

print("✓ Added pagination to:")
print("  - GET /api/transactions")
print("  - GET /api/category-rules")
print("  - GET /api/forecast")
print("\nPagination parameters:")
print("  - page: Page number (default: 1)")
print("  - per_page: Items per page (default: 100, max: 1000)")
