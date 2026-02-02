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

if __name__ == '__main__':
    app.run(debug=True)
