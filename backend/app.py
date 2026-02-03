from flask import Flask, request, jsonify, render_template
from flask_migrate import Migrate
from models import db, Account, Category, Transaction, CategoryRule, ForecastItem
from services import importer, categorizer
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///budget.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

@app.route('/')
def index():
    return render_template('transactions.html')

@app.route('/config')
def config():
    return render_template('config.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/cashflow')
def cashflow():
    return render_template('cashflow.html')

@app.route('/api')
def api_index():
    return {'status': 'ok', 'message': 'Personal Finance API'}

# Import endpoints
@app.route('/api/import', methods=['POST'])
def import_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    account_id = request.form.get('account_id', type=int)
    
    if not account_id:
        return jsonify({'error': 'account_id required'}), 400
    
    content = file.read().decode('utf-8')
    
    # Detect format and parse
    if file.filename.endswith('.ofx'):
        transactions = importer.parse_ofx(content)
        format_detected = 'ofx'
    else:
        csv_format = importer.detect_csv_format(content)
        if csv_format == '4col':
            transactions = importer.parse_csv_4col(content)
            format_detected = 'csv_4col'
        else:
            transactions = importer.parse_csv_3col(content)
            format_detected = 'csv_3col'
    
    # Import transactions
    result = importer.import_transactions(transactions, account_id)
    
    # Apply categorization suggestions
    new_txns = Transaction.query.filter_by(account_id=account_id, is_approved=False).all()
    categorizer.apply_suggestions(new_txns)
    
    return jsonify({**result, 'format_detected': format_detected})

# Transaction endpoints
@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    query = Transaction.query
    
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
    
    transactions = query.order_by(Transaction.date.desc()).all()
    return jsonify([{
        'id': t.id,
        'account_id': t.account_id,
        'date': t.date.isoformat(),
        'memo': t.memo,
        'amount': float(t.amount),
        'category_id': t.category_id,
        'subcategory_id': t.subcategory_id,
        'suggested_category_id': t.suggested_category_id,
        'suggested_subcategory_id': t.suggested_subcategory_id,
        'is_approved': t.is_approved,
        'is_credit_card_payment': t.is_credit_card_payment
    } for t in transactions])

@app.route('/api/transactions/<int:id>', methods=['PATCH'])
def update_transaction(id):
    txn = Transaction.query.get_or_404(id)
    data = request.json
    
    if 'category_id' in data:
        txn.category_id = data['category_id']
    if 'subcategory_id' in data:
        txn.subcategory_id = data['subcategory_id']
    if 'is_approved' in data:
        txn.is_approved = data['is_approved']
    if 'accrual_start_date' in data:
        txn.accrual_start_date = datetime.fromisoformat(data['accrual_start_date']).date() if data['accrual_start_date'] else None
    if 'accrual_end_date' in data:
        txn.accrual_end_date = datetime.fromisoformat(data['accrual_end_date']).date() if data['accrual_end_date'] else None
    if 'accrual_method' in data:
        txn.accrual_method = data['accrual_method']
    
    db.session.commit()
    return jsonify({'status': 'updated'})

# Category endpoints
@app.route('/api/categories', methods=['GET'])
def get_categories():
    categories = Category.query.filter_by(parent_id=None).all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'type': c.type,
        'color': c.color,
        'subcategories': [{
            'id': s.id,
            'name': s.name,
            'type': s.type,
            'color': s.color
        } for s in c.subcategories]
    } for c in categories])

@app.route('/api/categories', methods=['POST'])
def create_category():
    data = request.json
    category = Category(
        name=data['name'],
        type=data['type'],
        parent_id=data.get('parent_id'),
        color=data.get('color')
    )
    db.session.add(category)
    db.session.commit()
    return jsonify({'id': category.id, 'status': 'created'}), 201

@app.route('/api/categories/<int:id>', methods=['PATCH'])
def update_category(id):
    category = Category.query.get_or_404(id)
    data = request.json
    
    if 'name' in data:
        category.name = data['name']
    if 'type' in data:
        category.type = data['type']
    if 'color' in data:
        category.color = data['color']
    
    db.session.commit()
    return jsonify({'status': 'updated'})

@app.route('/api/categories/<int:id>', methods=['DELETE'])
def delete_category(id):
    category = Category.query.get_or_404(id)
    if category.subcategories:
        return jsonify({'error': 'Cannot delete category with subcategories'}), 400
    db.session.delete(category)
    db.session.commit()
    return jsonify({'status': 'deleted'})

# Category Rules endpoints
@app.route('/api/category-rules', methods=['GET'])
def get_rules():
    rules = CategoryRule.query.order_by(CategoryRule.priority.desc()).all()
    return jsonify([{
        'id': r.id,
        'pattern': r.pattern,
        'category_id': r.category_id,
        'subcategory_id': r.subcategory_id,
        'priority': r.priority
    } for r in rules])

@app.route('/api/category-rules', methods=['POST'])
def create_rule():
    data = request.json
    rule = CategoryRule(
        pattern=data['pattern'],
        category_id=data['category_id'],
        subcategory_id=data.get('subcategory_id'),
        priority=data.get('priority', 0)
    )
    db.session.add(rule)
    db.session.commit()
    return jsonify({'id': rule.id, 'status': 'created'}), 201

@app.route('/api/category-rules/<int:id>', methods=['PATCH'])
def update_rule(id):
    rule = CategoryRule.query.get_or_404(id)
    data = request.json
    
    if 'pattern' in data:
        rule.pattern = data['pattern']
    if 'category_id' in data:
        rule.category_id = data['category_id']
    if 'subcategory_id' in data:
        rule.subcategory_id = data['subcategory_id']
    if 'priority' in data:
        rule.priority = data['priority']
    
    db.session.commit()
    return jsonify({'status': 'updated'})

@app.route('/api/category-rules/<int:id>', methods=['DELETE'])
def delete_rule(id):
    rule = CategoryRule.query.get_or_404(id)
    db.session.delete(rule)
    db.session.commit()
    return jsonify({'status': 'deleted'})

# Account endpoints
@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    accounts = Account.query.all()
    return jsonify([{
        'id': a.id,
        'name': a.name,
        'number': a.number,
        'ofx_account_id': a.ofx_account_id,
        'starting_balance': float(a.starting_balance) if a.starting_balance else 0,
        'starting_balance_date': a.starting_balance_date.isoformat() if a.starting_balance_date else None
    } for a in accounts])

@app.route('/api/accounts', methods=['POST'])
def create_account():
    data = request.json
    account = Account(
        name=data['name'],
        number=data.get('number'),
        starting_balance=data.get('starting_balance', 0),
        starting_balance_date=datetime.fromisoformat(data['starting_balance_date']).date() if data.get('starting_balance_date') else None
    )
    db.session.add(account)
    db.session.commit()
    return jsonify({'id': account.id, 'status': 'created'}), 201

@app.route('/api/accounts/<int:id>', methods=['PATCH'])
def update_account(id):
    account = Account.query.get_or_404(id)
    data = request.json
    
    if 'name' in data:
        account.name = data['name']
    if 'number' in data:
        account.number = data['number']
    if 'starting_balance' in data:
        account.starting_balance = data['starting_balance']
    if 'starting_balance_date' in data:
        account.starting_balance_date = datetime.fromisoformat(data['starting_balance_date']).date() if data['starting_balance_date'] else None
    
    db.session.commit()
    return jsonify({'status': 'updated'})

@app.route('/api/accounts/<int:id>', methods=['DELETE'])
def delete_account(id):
    account = Account.query.get_or_404(id)
    db.session.delete(account)
    db.session.commit()
    return jsonify({'status': 'deleted'})

# Forecast endpoints
@app.route('/api/forecast', methods=['GET'])
def get_forecast():
    items = ForecastItem.query.all()
    return jsonify([{
        'id': f.id,
        'name': f.name,
        'category_id': f.category_id,
        'subcategory_id': f.subcategory_id,
        'amount': float(f.amount),
        'frequency': f.frequency,
        'type': f.type,
        'start_date': f.start_date.isoformat(),
        'end_date': f.end_date.isoformat() if f.end_date else None
    } for f in items])

@app.route('/api/forecast', methods=['POST'])
def create_forecast():
    data = request.json
    item = ForecastItem(
        name=data['name'],
        category_id=data['category_id'],
        subcategory_id=data.get('subcategory_id'),
        amount=data['amount'],
        frequency=data['frequency'],
        type=data['type'],
        start_date=datetime.fromisoformat(data['start_date']).date(),
        end_date=datetime.fromisoformat(data['end_date']).date() if data.get('end_date') else None
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'id': item.id, 'status': 'created'}), 201

@app.route('/api/forecast/<int:id>', methods=['PATCH'])
def update_forecast(id):
    item = ForecastItem.query.get_or_404(id)
    data = request.json
    
    if 'name' in data:
        item.name = data['name']
    if 'category_id' in data:
        item.category_id = data['category_id']
    if 'subcategory_id' in data:
        item.subcategory_id = data['subcategory_id']
    if 'amount' in data:
        item.amount = data['amount']
    if 'frequency' in data:
        item.frequency = data['frequency']
    if 'type' in data:
        item.type = data['type']
    if 'start_date' in data:
        item.start_date = datetime.fromisoformat(data['start_date']).date()
    if 'end_date' in data:
        item.end_date = datetime.fromisoformat(data['end_date']).date() if data['end_date'] else None
    
    db.session.commit()
    return jsonify({'status': 'updated'})

@app.route('/api/forecast/<int:id>', methods=['DELETE'])
def delete_forecast(id):
    item = ForecastItem.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'status': 'deleted'})

# Dashboard API endpoints
@app.route('/api/dashboard/summary', methods=['GET'])
def get_dashboard_summary():
    from_date = request.args.get('from')
    to_date = request.args.get('to')
    account_id = request.args.get('account_id', type=int)
    
    query = Transaction.query.filter_by(is_approved=True)
    
    if from_date:
        query = query.filter(Transaction.date >= datetime.fromisoformat(from_date).date())
    if to_date:
        query = query.filter(Transaction.date <= datetime.fromisoformat(to_date).date())
    if account_id:
        query = query.filter_by(account_id=account_id)
    
    transactions = query.all()
    
    total_income = sum(float(t.amount) for t in transactions if float(t.amount) > 0)
    total_expenses = sum(abs(float(t.amount)) for t in transactions if float(t.amount) < 0)
    net = total_income - total_expenses
    
    return jsonify({
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net': net,
        'budget_variance': 0
    })

# Cash Flow Report API endpoints
@app.route('/api/reports/cashflow/monthly', methods=['GET'])
def get_cashflow_monthly():
    """Monthly Net Cash Flow - Returns net cash flow data with optional date range filters"""
    from_date = request.args.get('from')
    to_date = request.args.get('to')
    account_id = request.args.get('account_id', type=int)
    
    # Build raw SQL query using SQLite strftime for date grouping
    sql = """
        SELECT strftime('%Y-%m', date) AS month,
               SUM(amount) AS net_cash
        FROM transactions
        WHERE is_approved = 1
    """
    params = {}
    
    if from_date:
        sql += " AND date >= :from_date"
        params['from_date'] = from_date
    if to_date:
        sql += " AND date <= :to_date"
        params['to_date'] = to_date
    if account_id:
        sql += " AND account_id = :account_id"
        params['account_id'] = account_id
    
    sql += " GROUP BY month ORDER BY month"
    
    result = db.session.execute(db.text(sql), params)
    rows = result.fetchall()
    
    return jsonify([{
        'month': row[0],
        'net_cash': float(row[1]) if row[1] else 0
    } for row in rows])

@app.route('/api/reports/cashflow/by-category', methods=['GET'])
def get_cashflow_by_category():
    """Returns spending and income breakdown by category"""
    from_date = request.args.get('from')
    to_date = request.args.get('to')
    account_id = request.args.get('account_id', type=int)
    type_filter = request.args.get('type')  # income or expense
    
    # Build SQL query for spending by category
    spending_sql = """
        SELECT strftime('%Y-%m', t.date) AS month,
               c.id AS category_id,
               c.name AS category,
               sc.id AS subcategory_id,
               sc.name AS subcategory,
               c.type AS category_type,
               SUM(CASE WHEN t.amount < 0 THEN -t.amount ELSE 0 END) AS spending,
               SUM(CASE WHEN t.amount > 0 THEN t.amount ELSE 0 END) AS income
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.id
        LEFT JOIN categories sc ON t.subcategory_id = sc.id
        WHERE t.is_approved = 1 AND t.is_credit_card_payment = 0
    """
    params = {}
    
    if from_date:
        spending_sql += " AND t.date >= :from_date"
        params['from_date'] = from_date
    if to_date:
        spending_sql += " AND t.date <= :to_date"
        params['to_date'] = to_date
    if account_id:
        spending_sql += " AND t.account_id = :account_id"
        params['account_id'] = account_id
    if type_filter:
        spending_sql += " AND c.type = :type_filter"
        params['type_filter'] = type_filter
    
    spending_sql += " GROUP BY month, c.id, sc.id ORDER BY month, category"
    
    result = db.session.execute(db.text(spending_sql), params)
    rows = result.fetchall()
    
    return jsonify([{
        'month': row[0],
        'category_id': row[1],
        'category': row[2] or 'Uncategorized',
        'subcategory_id': row[3],
        'subcategory': row[4],
        'category_type': row[5],
        'spending': float(row[6]) if row[6] else 0,
        'income': float(row[7]) if row[7] else 0
    } for row in rows])

@app.route('/api/reports/cashflow/summary', methods=['GET'])
def get_cashflow_summary():
    """Returns overall cash flow summary statistics"""
    from_date = request.args.get('from')
    to_date = request.args.get('to')
    account_id = request.args.get('account_id', type=int)
    
    # Build SQL query for summary
    sql = """
        SELECT 
            SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) AS total_income,
            SUM(CASE WHEN amount < 0 THEN -amount ELSE 0 END) AS total_expenses,
            SUM(amount) AS net_cash_flow,
            COUNT(*) AS transaction_count
        FROM transactions
        WHERE is_approved = 1 AND is_credit_card_payment = 0
    """
    params = {}
    
    if from_date:
        sql += " AND date >= :from_date"
        params['from_date'] = from_date
    if to_date:
        sql += " AND date <= :to_date"
        params['to_date'] = to_date
    if account_id:
        sql += " AND account_id = :account_id"
        params['account_id'] = account_id
    
    result = db.session.execute(db.text(sql), params)
    row = result.fetchone()
    
    # Get month count for averages
    month_sql = """
        SELECT COUNT(DISTINCT strftime('%Y-%m', date)) AS month_count
        FROM transactions
        WHERE is_approved = 1
    """
    if from_date:
        month_sql += " AND date >= :from_date"
    if to_date:
        month_sql += " AND date <= :to_date"
    if account_id:
        month_sql += " AND account_id = :account_id"
    
    month_result = db.session.execute(db.text(month_sql), params)
    month_count = month_result.fetchone()[0] or 1
    
    total_income = float(row[0]) if row[0] else 0
    total_expenses = float(row[1]) if row[1] else 0
    net_cash_flow = float(row[2]) if row[2] else 0
    transaction_count = row[3] or 0
    
    return jsonify({
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_cash_flow': net_cash_flow,
        'transaction_count': transaction_count,
        'avg_monthly_income': total_income / month_count if month_count > 0 else 0,
        'avg_monthly_expenses': total_expenses / month_count if month_count > 0 else 0,
        'avg_monthly_net': net_cash_flow / month_count if month_count > 0 else 0,
        'month_count': month_count
    })

@app.route('/api/reports/cashflow/account-balances', methods=['GET'])
def get_account_balances():
    """Returns current balance for each account"""
    as_of_date = request.args.get('as_of_date')
    
    # Build SQL query for account balances
    sql = """
        SELECT a.id,
               a.name,
               a.number,
               a.starting_balance,
               a.starting_balance_date,
               COALESCE(SUM(t.amount), 0) AS transaction_sum,
               a.starting_balance + COALESCE(SUM(t.amount), 0) AS current_balance
        FROM accounts a
        LEFT JOIN transactions t ON a.id = t.account_id AND t.is_approved = 1
    """
    params = {}
    
    if as_of_date:
        sql += " AND t.date <= :as_of_date"
        params['as_of_date'] = as_of_date
    
    sql += " GROUP BY a.id ORDER BY a.name"
    
    result = db.session.execute(db.text(sql), params)
    rows = result.fetchall()
    
    total_balance = 0
    accounts = []
    
    for row in rows:
        balance = float(row[6]) if row[6] else float(row[3]) if row[3] else 0
        total_balance += balance
        accounts.append({
            'id': row[0],
            'account': row[1],
            'number': row[2],
            'starting_balance': float(row[3]) if row[3] else 0,
            'starting_balance_date': row[4].isoformat() if row[4] else None,
            'transaction_sum': float(row[5]) if row[5] else 0,
            'balance': balance
        })
    
    return jsonify({
        'accounts': accounts,
        'total_balance': total_balance
    })

@app.route('/api/reports/cashflow/credit-card-payments', methods=['GET'])
def get_credit_card_payments():
    """Returns credit card payment transactions by month"""
    from_date = request.args.get('from')
    to_date = request.args.get('to')
    account_id = request.args.get('account_id', type=int)
    
    sql = """
        SELECT strftime('%Y-%m', t.date) AS month,
               a.name AS account,
               SUM(-t.amount) AS amount,
               COUNT(*) AS payment_count
        FROM transactions t
        JOIN accounts a ON t.account_id = a.id
        WHERE t.is_credit_card_payment = 1 AND t.is_approved = 1
    """
    params = {}
    
    if from_date:
        sql += " AND t.date >= :from_date"
        params['from_date'] = from_date
    if to_date:
        sql += " AND t.date <= :to_date"
        params['to_date'] = to_date
    if account_id:
        sql += " AND t.account_id = :account_id"
        params['account_id'] = account_id
    
    sql += " GROUP BY month, a.id ORDER BY month, a.name"
    
    result = db.session.execute(db.text(sql), params)
    rows = result.fetchall()
    
    return jsonify([{
        'month': row[0],
        'account': row[1],
        'amount': float(row[2]) if row[2] else 0,
        'payment_count': row[3]
    } for row in rows])

@app.route('/api/reports/cashflow/transactions', methods=['GET'])
def get_cashflow_transactions():
    """Returns transactions for drill-down functionality (by category/month)"""
    from_date = request.args.get('from')
    to_date = request.args.get('to')
    category_id = request.args.get('category_id', type=int)
    month = request.args.get('month')  # format: YYYY-MM
    
    query = Transaction.query.filter_by(is_approved=True)
    
    if from_date:
        query = query.filter(Transaction.date >= datetime.fromisoformat(from_date).date())
    if to_date:
        query = query.filter(Transaction.date <= datetime.fromisoformat(to_date).date())
    if category_id:
        query = query.filter(
            (Transaction.category_id == category_id) | 
            (Transaction.subcategory_id == category_id)
        )
    if month:
        # Filter by specific month
        year, mon = month.split('-')
        from datetime import date
        import calendar
        first_day = date(int(year), int(mon), 1)
        last_day = date(int(year), int(mon), calendar.monthrange(int(year), int(mon))[1])
        query = query.filter(Transaction.date >= first_day, Transaction.date <= last_day)
    
    transactions = query.order_by(Transaction.date.desc()).all()
    
    return jsonify([{
        'id': t.id,
        'account_id': t.account_id,
        'date': t.date.isoformat(),
        'memo': t.memo,
        'amount': float(t.amount),
        'category_id': t.category_id,
        'subcategory_id': t.subcategory_id,
        'is_credit_card_payment': t.is_credit_card_payment
    } for t in transactions])

if __name__ == '__main__':
    app.run(debug=True)
