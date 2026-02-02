from models import CategoryRule, db

CC_PAYMENT_KEYWORDS = ['credit card payment', 'cc payment', 'autopay', 'card payment']

def suggest_category(memo):
    """Find matching category rule for memo"""
    if not memo:
        return None, None
    
    memo_norm = memo.lower()
    
    # Get all rules ordered by priority DESC
    rules = CategoryRule.query.order_by(CategoryRule.priority.desc()).all()
    
    for rule in rules:
        if rule.pattern.lower() in memo_norm:
            return rule.category_id, rule.subcategory_id
    
    return None, None

def detect_credit_card_payment(memo):
    """Detect if transaction is a credit card payment"""
    if not memo:
        return False
    
    memo_lower = memo.lower()
    return any(keyword in memo_lower for keyword in CC_PAYMENT_KEYWORDS)

def apply_suggestions(transactions):
    """Apply category suggestions to list of transactions"""
    for txn in transactions:
        cat_id, subcat_id = suggest_category(txn.memo)
        txn.suggested_category_id = cat_id
        txn.suggested_subcategory_id = subcat_id
        txn.is_credit_card_payment = detect_credit_card_payment(txn.memo)
    
    db.session.commit()
