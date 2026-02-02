#!/usr/bin/env python3
"""Test script for Phase 5 - Dashboard & Visualizations"""

from app import app, db
from models import Transaction
import webbrowser
import time
from threading import Thread

def test_phase5():
    with app.app_context():
        # Verify data exists
        transactions = Transaction.query.count()
        approved = Transaction.query.filter_by(is_approved=True).count()
        
        print("=== Phase 5 - Dashboard & Visualizations Test ===\n")
        print(f"✓ Database connected")
        print(f"✓ Transactions: {transactions}")
        print(f"✓ Approved: {approved}")
        print()
        
        if transactions == 0:
            print("⚠ No transactions found. Import some data first.")
            return
        
        print("✅ Phase 5 Dashboard Features:")
        print("   - Summary Cards")
        print("     • Total Income")
        print("     • Total Expenses")
        print("     • Net Cash Flow")
        print("     • Average Monthly Expense")
        print()
        print("   - Charts & Visualizations")
        print("     • Monthly Spending by Category (horizontal bar)")
        print("     • Income vs Expenses (monthly bar chart)")
        print("     • Expense Breakdown (pie chart)")
        print()
        print("   - Filters")
        print("     • Year selector")
        print("     • Month selector (all months or specific month)")
        print()
        
        print("Starting Flask server...")
        print("Visit: http://localhost:5000/dashboard")
        print()
        print("Press Ctrl+C to stop the server")
        
        # Open browser after short delay
        def open_browser():
            time.sleep(1.5)
            webbrowser.open('http://localhost:5000/dashboard')
        
        Thread(target=open_browser, daemon=True).start()
        
        # Run Flask app
        app.run(debug=True, use_reloader=False)

if __name__ == '__main__':
    test_phase5()
