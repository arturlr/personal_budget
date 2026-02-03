"""
Accrual Service - Convert cash-basis transactions to accrual-basis accounting.

Supports:
- Linear spread method: distributes transaction amount evenly across accrual period
- Credit card liability tracking: purchases increase liability, payments decrease it
"""

from datetime import date, timedelta
from decimal import Decimal
from models import Transaction, Account, db


def get_accrual_amount_for_period(transaction, period_start, period_end):
    """
    Calculate the accrued amount of a transaction for a specific date range.
    
    If transaction has accrual dates set:
    - Uses linear spread method to distribute amount across the accrual period
    - Returns the portion of the amount that falls within the given date range
    
    If no accrual dates set:
    - Returns full amount if transaction date falls within the period
    - Returns 0 if transaction date is outside the period
    
    Args:
        transaction: Transaction model instance
        period_start: date - start of the period (inclusive)
        period_end: date - end of the period (inclusive)
    
    Returns:
        Decimal - accrued amount for the period
    """
    txn_amount = Decimal(str(transaction.amount))
    
    # If no accrual method or dates, use cash basis (transaction date)
    if not transaction.accrual_method or not transaction.accrual_start_date or not transaction.accrual_end_date:
        if period_start <= transaction.date <= period_end:
            return txn_amount
        return Decimal('0')
    
    # Linear spread method
    if transaction.accrual_method == 'linear':
        return _calculate_linear_spread(
            txn_amount,
            transaction.accrual_start_date,
            transaction.accrual_end_date,
            period_start,
            period_end
        )
    
    # Unknown method - fall back to cash basis
    if period_start <= transaction.date <= period_end:
        return txn_amount
    return Decimal('0')


def _calculate_linear_spread(amount, accrual_start, accrual_end, period_start, period_end):
    """
    Calculate linear spread of amount over accrual period, returning portion in requested period.
    
    Args:
        amount: Decimal - total transaction amount
        accrual_start: date - start of accrual period
        accrual_end: date - end of accrual period  
        period_start: date - start of reporting period
        period_end: date - end of reporting period
    
    Returns:
        Decimal - portion of amount that falls within the reporting period
    """
    # Calculate total days in accrual period (inclusive)
    total_days = (accrual_end - accrual_start).days + 1
    if total_days <= 0:
        return Decimal('0')
    
    # Calculate daily amount
    daily_amount = amount / Decimal(str(total_days))
    
    # Find overlap between accrual period and reporting period
    overlap_start = max(accrual_start, period_start)
    overlap_end = min(accrual_end, period_end)
    
    if overlap_start > overlap_end:
        # No overlap
        return Decimal('0')
    
    overlap_days = (overlap_end - overlap_start).days + 1
    return daily_amount * Decimal(str(overlap_days))


def calculate_accrual_income_expense(from_date, to_date, account_id=None):
    """
    Calculate accrual-basis income and expenses for a date range.
    
    Args:
        from_date: date - start of reporting period
        to_date: date - end of reporting period
        account_id: int (optional) - filter by specific account
    
    Returns:
        dict with keys:
        - total_income: Decimal
        - total_expenses: Decimal
        - net_income: Decimal
        - by_category: list of dicts with category breakdown
    """
    # Build query for approved transactions
    query = Transaction.query.filter_by(is_approved=True)
    
    if account_id:
        query = query.filter_by(account_id=account_id)
    
    # We need transactions that could have accrual amounts in this period
    # This includes transactions with accrual dates overlapping the period
    # or cash-basis transactions dated in the period
    transactions = query.all()
    
    total_income = Decimal('0')
    total_expenses = Decimal('0')
    category_totals = {}
    
    for txn in transactions:
        # Skip credit card payments for income/expense calculation
        if txn.is_credit_card_payment:
            continue
        
        accrued_amount = get_accrual_amount_for_period(txn, from_date, to_date)
        
        if accrued_amount == 0:
            continue
        
        if accrued_amount > 0:
            total_income += accrued_amount
        else:
            total_expenses += abs(accrued_amount)
        
        # Track by category - handle case where category might be a subcategory
        cat = txn.category
        if cat and cat.parent_id:
            # This is a subcategory, use parent as category
            parent_cat = cat.parent
            cat_id = parent_cat.id
            cat_name = parent_cat.name
            subcat_name = cat.name
            cat_type = parent_cat.type
        else:
            # This is a top-level category
            cat_id = txn.category_id or 0
            cat_name = cat.name if cat else 'Uncategorized'
            subcat_name = txn.subcategory.name if txn.subcategory else None
            cat_type = cat.type if cat else ('income' if accrued_amount > 0 else 'expense')
        
        display_name = f"{cat_name}: {subcat_name}" if subcat_name else cat_name
        
        # Use a unique key combining category and subcategory
        subcat_id = cat.id if (cat and cat.parent_id) else (txn.subcategory_id or 0)
        key = f"{cat_id}_{subcat_id}"
        
        if key not in category_totals:
            category_totals[key] = {
                'category_id': cat_id,
                'category_name': display_name,
                'category_type': cat_type,
                'income': Decimal('0'),
                'expenses': Decimal('0')
            }
        
        if accrued_amount > 0:
            category_totals[key]['income'] += accrued_amount
        else:
            category_totals[key]['expenses'] += abs(accrued_amount)
    
    return {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_income': total_income - total_expenses,
        'by_category': list(category_totals.values())
    }


def calculate_account_balances(as_of_date=None):
    """
    Calculate account balances as of a specific date.
    
    Args:
        as_of_date: date (optional) - calculate balances as of this date
                   If None, uses current date
    
    Returns:
        dict with keys:
        - accounts: list of account balance dicts
        - total_assets: Decimal - sum of positive balances
        - total_liabilities: Decimal - sum of negative balances (as positive)
        - net_worth: Decimal - assets minus liabilities
    """
    if as_of_date is None:
        as_of_date = date.today()
    
    accounts = Account.query.all()
    account_balances = []
    total_assets = Decimal('0')
    total_liabilities = Decimal('0')
    
    for account in accounts:
        # Get starting balance
        starting_balance = Decimal(str(account.starting_balance or 0))
        
        # Only count starting balance if it's before or on the as_of_date
        if account.starting_balance_date and account.starting_balance_date > as_of_date:
            starting_balance = Decimal('0')
        
        # Sum transactions up to as_of_date
        txn_query = Transaction.query.filter(
            Transaction.account_id == account.id,
            Transaction.is_approved == True,
            Transaction.date <= as_of_date
        )
        
        txn_sum = Decimal('0')
        for txn in txn_query.all():
            txn_sum += Decimal(str(txn.amount))
        
        balance = starting_balance + txn_sum
        
        account_balances.append({
            'id': account.id,
            'name': account.name,
            'number': account.number,
            'balance': balance,
            'is_liability': balance < 0
        })
        
        if balance >= 0:
            total_assets += balance
        else:
            total_liabilities += abs(balance)
    
    return {
        'accounts': account_balances,
        'total_assets': total_assets,
        'total_liabilities': total_liabilities,
        'net_worth': total_assets - total_liabilities
    }


def calculate_credit_card_liability(as_of_date=None):
    """
    Calculate credit card liability as of a specific date.
    
    Credit card liability is calculated by tracking:
    - Purchases on credit (negative amounts not marked as CC payment) - increases liability
    - Credit card payments (marked as is_credit_card_payment) - decreases liability
    
    Note: This aggregates across all accounts where credit card payment patterns exist.
    
    Args:
        as_of_date: date (optional) - calculate liability as of this date
    
    Returns:
        dict with keys:
        - total_liability: Decimal
        - total_purchases: Decimal 
        - total_payments: Decimal
        - details: list of monthly breakdowns
    """
    if as_of_date is None:
        as_of_date = date.today()
    
    # Get accounts that have negative balances (likely credit card accounts)
    balances = calculate_account_balances(as_of_date)
    
    cc_accounts = []
    total_liability = Decimal('0')
    
    for acc in balances['accounts']:
        if acc['is_liability']:
            cc_accounts.append(acc)
            total_liability += abs(acc['balance'])
    
    # Also get payment flow data
    payments_query = Transaction.query.filter(
        Transaction.is_approved == True,
        Transaction.is_credit_card_payment == True,
        Transaction.date <= as_of_date
    )
    
    total_payments = Decimal('0')
    for txn in payments_query.all():
        # Payments are typically negative (money leaving bank account)
        total_payments += abs(Decimal(str(txn.amount)))
    
    return {
        'total_liability': total_liability,
        'total_payments': total_payments,
        'liability_accounts': cc_accounts
    }


def get_monthly_accrual_breakdown(from_date, to_date, account_id=None):
    """
    Get month-by-month accrual income/expense breakdown.
    
    Args:
        from_date: date - start of reporting period
        to_date: date - end of reporting period
        account_id: int (optional) - filter by account
    
    Returns:
        list of dicts with monthly breakdowns
    """
    results = []
    current = date(from_date.year, from_date.month, 1)
    
    while current <= to_date:
        # Get last day of current month
        if current.month == 12:
            next_month = date(current.year + 1, 1, 1)
        else:
            next_month = date(current.year, current.month + 1, 1)
        month_end = next_month - timedelta(days=1)
        
        # Clip to our date range
        period_start = max(current, from_date)
        period_end = min(month_end, to_date)
        
        month_data = calculate_accrual_income_expense(period_start, period_end, account_id)
        
        results.append({
            'month': current.strftime('%Y-%m'),
            'income': float(month_data['total_income']),
            'expenses': float(month_data['total_expenses']),
            'net_income': float(month_data['net_income'])
        })
        
        current = next_month
    
    return results


def get_monthly_by_parent_category(from_date, to_date, account_id=None):
    """
    Get monthly breakdown by parent category only (no subcategories).
    """
    from models import Transaction, Category
    
    query = Transaction.query.filter(
        Transaction.is_approved == True,
        Transaction.is_credit_card_payment == False
    )
    
    if account_id:
        query = query.filter(Transaction.account_id == account_id)
    
    transactions = query.all()
    
    # Group by month and parent category
    monthly_data = {}
    
    for txn in transactions:
        accrued_amount = get_accrual_amount_for_period(txn, from_date, to_date)
        if accrued_amount == 0:
            continue
        
        month = txn.date.strftime('%Y-%m')
        
        # Get parent category
        cat = txn.category
        if cat and cat.parent_id:
            parent_cat = cat.parent
            cat_id = parent_cat.id
            cat_name = parent_cat.name
        else:
            cat_id = txn.category_id or 0
            cat_name = cat.name if cat else 'Uncategorized'
        
        key = f"{month}_{cat_id}"
        
        if key not in monthly_data:
            monthly_data[key] = {
                'month': month,
                'category_id': cat_id,
                'category_name': cat_name,
                'income': Decimal('0'),
                'expenses': Decimal('0')
            }
        
        if accrued_amount > 0:
            monthly_data[key]['income'] += accrued_amount
        else:
            monthly_data[key]['expenses'] += abs(accrued_amount)
    
    # Convert to list and format
    results = [{
        'month': v['month'],
        'category_id': v['category_id'],
        'category_name': v['category_name'],
        'income': float(v['income']),
        'expenses': float(v['expenses'])
    } for v in monthly_data.values()]
    
    return sorted(results, key=lambda x: (x['month'], x['category_name']))
