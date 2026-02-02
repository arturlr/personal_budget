#!/usr/bin/env python3
"""Setup test data for Phase 3 UI testing"""

from app import app, db
from models import Account, Category, CategoryRule
from services import importer, categorizer

def setup_test_data():
    with app.app_context():
        # Check if data already exists
        if Account.query.count() > 0:
            print("Test data already exists. Skipping setup.")
            return
        
        # Create account
        account = Account(
            name="Main Checking",
            number="1234",
            starting_balance=5000.00
        )
        db.session.add(account)
        db.session.commit()
        print(f"✓ Created account: {account.name} (ID: {account.id})")
        
        # Create categories
        cat_groceries = Category(name="Groceries", type="expense", color="#ff0000")
        cat_shopping = Category(name="Shopping", type="expense", color="#ff9900")
        cat_dining = Category(name="Dining", type="expense", color="#ff6600")
        cat_transport = Category(name="Transportation", type="expense", color="#0066ff")
        cat_utilities = Category(name="Utilities", type="expense", color="#6600ff")
        cat_salary = Category(name="Salary", type="income", color="#00ff00")
        
        db.session.add_all([cat_groceries, cat_shopping, cat_dining, cat_transport, cat_utilities, cat_salary])
        db.session.commit()
        print(f"✓ Created {Category.query.count()} categories")
        
        # Create subcategories
        sub_produce = Category(name="Produce", type="expense", parent_id=cat_groceries.id)
        sub_online = Category(name="Online", type="expense", parent_id=cat_shopping.id)
        db.session.add_all([sub_produce, sub_online])
        db.session.commit()
        print(f"✓ Created subcategories")
        
        # Create category rules
        rules = [
            CategoryRule(pattern="WHOLE FOODS", category_id=cat_groceries.id, priority=10),
            CategoryRule(pattern="TRADER JOE", category_id=cat_groceries.id, priority=10),
            CategoryRule(pattern="AMAZON", category_id=cat_shopping.id, subcategory_id=sub_online.id, priority=8),
            CategoryRule(pattern="RESTAURANT", category_id=cat_dining.id, priority=7),
            CategoryRule(pattern="UBER", category_id=cat_transport.id, priority=7),
            CategoryRule(pattern="STARBUCKS", category_id=cat_dining.id, priority=6),
            CategoryRule(pattern="NETFLIX", category_id=cat_utilities.id, priority=5),
            CategoryRule(pattern="SALARY", category_id=cat_salary.id, priority=10),
        ]
        db.session.add_all(rules)
        db.session.commit()
        print(f"✓ Created {len(rules)} category rules")
        
        # Import sample transactions
        csv_file = "test_data/sample_3col.csv"
        try:
            with open(csv_file, 'r') as f:
                content = f.read()
            
            transactions = importer.parse_csv_3col(content)
            result = importer.import_transactions(transactions, account.id)
            print(f"✓ Imported {result['imported']} transactions")
            
            # Apply categorization
            from models import Transaction
            txns = Transaction.query.filter_by(account_id=account.id).all()
            categorizer.apply_suggestions(txns)
            print(f"✓ Applied categorization suggestions")
            
        except FileNotFoundError:
            print("⚠ Sample CSV not found, skipping import")
        
        print("\n✅ Test data setup complete!")
        print(f"   Visit http://localhost:5000 to view the Transactions UI")

if __name__ == '__main__':
    setup_test_data()
