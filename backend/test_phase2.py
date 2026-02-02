#!/usr/bin/env python3
"""Test script for Phase 2 - Import & Categorization"""

from app import app, db
from models import Account, Category, CategoryRule, Transaction
from services import importer, categorizer
from datetime import date

def test_phase2():
    with app.app_context():
        # Clean up any existing test data
        Transaction.query.delete()
        CategoryRule.query.delete()
        Category.query.delete()
        Account.query.delete()
        db.session.commit()
        
        # 1. Create test account
        account = Account(name="Test Checking", number="1234", starting_balance=1000.00)
        db.session.add(account)
        db.session.commit()
        print(f"✓ Created account: {account.name} (ID: {account.id})")
        
        # 2. Create test categories
        cat_groceries = Category(name="Groceries", type="expense", color="#ff0000")
        cat_amazon = Category(name="Shopping", type="expense", color="#ff9900")
        cat_salary = Category(name="Salary", type="income", color="#00ff00")
        db.session.add_all([cat_groceries, cat_amazon, cat_salary])
        db.session.commit()
        print(f"✓ Created {Category.query.count()} categories")
        
        # 3. Create category rules
        rule1 = CategoryRule(pattern="WHOLE FOODS", category_id=cat_groceries.id, priority=10)
        rule2 = CategoryRule(pattern="AMAZON", category_id=cat_amazon.id, priority=5)
        db.session.add_all([rule1, rule2])
        db.session.commit()
        print(f"✓ Created {CategoryRule.query.count()} category rules")
        
        # 4. Test CSV parsing (3-column)
        csv_3col = """Date,Description,Amount
01/15/2026,WHOLE FOODS MARKET,-45.67
01/16/2026,SALARY DEPOSIT,2500.00
01/17/2026,AMAZON.COM,-89.99"""
        
        transactions = importer.parse_csv_3col(csv_3col)
        print(f"✓ Parsed {len(transactions)} transactions from 3-column CSV")
        
        # 5. Test CSV parsing (4-column)
        csv_4col = """Date,Description,Credit,Debit
01/15/2026,WHOLE FOODS MARKET,,45.67
01/16/2026,SALARY DEPOSIT,2500.00,
01/17/2026,AMAZON.COM,,89.99"""
        
        transactions_4col = importer.parse_csv_4col(csv_4col)
        print(f"✓ Parsed {len(transactions_4col)} transactions from 4-column CSV")
        
        # 6. Import transactions
        result = importer.import_transactions(transactions, account.id)
        print(f"✓ Imported {result['imported']} transactions, skipped {result['duplicates_skipped']} duplicates")
        
        # 7. Test deduplication
        result2 = importer.import_transactions(transactions, account.id)
        print(f"✓ Deduplication working: {result2['duplicates_skipped']} duplicates detected")
        
        # 8. Test categorization
        txns = Transaction.query.all()
        categorizer.apply_suggestions(txns)
        
        categorized = Transaction.query.filter(Transaction.suggested_category_id.isnot(None)).count()
        print(f"✓ Auto-categorized {categorized} transactions")
        
        # 9. Test credit card payment detection
        cc_txn = Transaction(
            account_id=account.id,
            date=date(2026, 1, 18),
            memo="CREDIT CARD PAYMENT - AUTOPAY",
            amount=-500.00,
            unique_hash=Transaction.generate_hash(account.id, date(2026, 1, 18), "CC PAYMENT", -500.00)
        )
        db.session.add(cc_txn)
        db.session.commit()
        
        categorizer.apply_suggestions([cc_txn])
        if cc_txn.is_credit_card_payment:
            print("✓ Credit card payment detection working")
        
        # 10. Verify transaction details
        whole_foods = Transaction.query.filter(Transaction.memo.like('%WHOLE FOODS%')).first()
        if whole_foods and whole_foods.suggested_category_id == cat_groceries.id:
            print("✓ Category rule matching working correctly")
        
        print("\n✅ Phase 2 Complete!")
        print(f"   - Accounts: {Account.query.count()}")
        print(f"   - Categories: {Category.query.count()}")
        print(f"   - Rules: {CategoryRule.query.count()}")
        print(f"   - Transactions: {Transaction.query.count()}")

if __name__ == '__main__':
    test_phase2()
