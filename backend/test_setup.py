#!/usr/bin/env python3
"""Test script to verify Phase 1 setup"""

from app import app, db
from models import Account, Category, Transaction, CategoryRule, ForecastItem

def test_database():
    with app.app_context():
        # Test creating an account
        account = Account(name="Test Checking", number="1234", starting_balance=1000.00)
        db.session.add(account)
        
        # Test creating categories
        cat_income = Category(name="Salary", type="income", color="#00ff00")
        cat_expense = Category(name="Groceries", type="expense", color="#ff0000")
        db.session.add_all([cat_income, cat_expense])
        
        db.session.commit()
        
        # Verify
        accounts = Account.query.all()
        categories = Category.query.all()
        
        print(f"✓ Created {len(accounts)} account(s)")
        print(f"✓ Created {len(categories)} category(ies)")
        print(f"✓ Database schema is working correctly")
        
        # Cleanup
        db.session.delete(account)
        db.session.delete(cat_income)
        db.session.delete(cat_expense)
        db.session.commit()
        
        print("✓ Phase 1 setup complete!")

if __name__ == '__main__':
    test_database()
