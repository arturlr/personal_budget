#!/usr/bin/env python3
"""Test script for Phase 3 - Transactions UI"""

from app import app, db
from models import Account, Category, Transaction
import webbrowser
import time
from threading import Thread

def test_phase3():
    with app.app_context():
        # Verify data exists
        accounts = Account.query.count()
        categories = Category.query.count()
        transactions = Transaction.query.count()
        pending = Transaction.query.filter_by(is_approved=False).count()
        
        print("=== Phase 3 - Transactions UI Test ===\n")
        print(f"✓ Database connected")
        print(f"✓ Accounts: {accounts}")
        print(f"✓ Categories: {categories}")
        print(f"✓ Transactions: {transactions}")
        print(f"✓ Pending approval: {pending}")
        print()
        
        if transactions == 0:
            print("⚠ No transactions found. Run setup_test_data.py first.")
            return
        
        print("✅ Phase 3 UI Features:")
        print("   - Transaction table with filters")
        print("   - Date range filtering")
        print("   - Account and category filters")
        print("   - Status filtering (pending/approved)")
        print("   - Hide credit card payments option")
        print("   - Category dropdown with subcategories")
        print("   - Single transaction approval")
        print("   - Bulk approval of selected transactions")
        print("   - Visual indicators (pending highlight, CC icon)")
        print("   - Statistics cards (total, pending, income, expenses)")
        print()
        
        print("Starting Flask server...")
        print("Visit: http://localhost:5000")
        print()
        print("Press Ctrl+C to stop the server")
        
        # Open browser after short delay
        def open_browser():
            time.sleep(1.5)
            webbrowser.open('http://localhost:5000')
        
        Thread(target=open_browser, daemon=True).start()
        
        # Run Flask app
        app.run(debug=True, use_reloader=False)

if __name__ == '__main__':
    test_phase3()
