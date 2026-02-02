import csv
import re
from datetime import datetime
from io import StringIO
import ofxparse
from models import Transaction, Account, db

def detect_csv_format(file_content):
    """Detect if CSV is 3-column or 4-column format"""
    lines = file_content.strip().split('\n')
    if len(lines) < 2:
        return None
    
    header = lines[0].lower()
    if 'credit' in header and 'debit' in header:
        return '4col'
    return '3col'

def parse_date(date_str):
    """Parse date from various formats"""
    # Remove day-of-week suffix (e.g., "20/11/2018 TUE" -> "20/11/2018")
    date_str = re.sub(r'\s+[A-Z]{3}$', '', date_str.strip())
    
    formats = ['%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d', '%Y/%m/%d']
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unable to parse date: {date_str}")

def parse_csv_3col(file_content):
    """Parse 3-column CSV: Date, Description, Amount"""
    reader = csv.DictReader(StringIO(file_content))
    transactions = []
    
    for row in reader:
        amount_str = row.get('Amount', '').strip()
        if not amount_str or float(amount_str) == 0:
            continue
        
        transactions.append({
            'date': parse_date(row['Date']),
            'memo': row['Description'].strip(),
            'amount': float(amount_str)
        })
    
    return transactions

def parse_csv_4col(file_content):
    """Parse 4-column CSV: Date, Description, Credit, Debit"""
    reader = csv.DictReader(StringIO(file_content))
    transactions = []
    
    for row in reader:
        credit = row.get('Credit', '').strip()
        debit = row.get('Debit', '').strip()
        
        if credit:
            amount = float(credit)
        elif debit:
            amount = -float(debit)
        else:
            continue
        
        if amount == 0:
            continue
        
        transactions.append({
            'date': parse_date(row['Date']),
            'memo': row['Description'].strip(),
            'amount': amount
        })
    
    return transactions

def parse_ofx(file_content):
    """Parse OFX file"""
    ofx = ofxparse.OfxParser.parse(StringIO(file_content))
    transactions = []
    
    for account in ofx.accounts:
        account_id = account.account_id
        for txn in account.statement.transactions:
            transactions.append({
                'date': txn.date.date(),
                'memo': txn.memo or txn.payee or '',
                'amount': float(txn.amount),
                'ofx_account_id': account_id
            })
    
    return transactions

def import_transactions(transactions_list, account_id):
    """Import transactions into database with deduplication"""
    imported = 0
    duplicates = 0
    
    for txn_data in transactions_list:
        unique_hash = Transaction.generate_hash(
            account_id,
            txn_data['date'],
            txn_data['memo'],
            txn_data['amount']
        )
        
        # Check for duplicate
        existing = Transaction.query.filter_by(unique_hash=unique_hash).first()
        if existing:
            duplicates += 1
            continue
        
        transaction = Transaction(
            account_id=account_id,
            date=txn_data['date'],
            memo=txn_data['memo'],
            amount=txn_data['amount'],
            unique_hash=unique_hash,
            is_approved=False
        )
        
        db.session.add(transaction)
        imported += 1
    
    db.session.commit()
    return {'imported': imported, 'duplicates_skipped': duplicates}
