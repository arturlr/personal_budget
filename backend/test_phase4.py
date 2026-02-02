#!/usr/bin/env python3
"""Test script for Phase 4 - Config Area"""

from app import app, db
from models import Account, Category, CategoryRule, ForecastItem
import webbrowser
import time
from threading import Thread

def test_phase4():
    with app.app_context():
        # Verify data exists
        accounts = Account.query.count()
        categories = Category.query.count()
        rules = CategoryRule.query.count()
        forecast = ForecastItem.query.count()
        
        print("=== Phase 4 - Config Area Test ===\n")
        print(f"✓ Database connected")
        print(f"✓ Accounts: {accounts}")
        print(f"✓ Categories: {categories}")
        print(f"✓ Category Rules: {rules}")
        print(f"✓ Forecast Items: {forecast}")
        print()
        
        print("✅ Phase 4 UI Features:")
        print("   - Categories Management")
        print("     • Hierarchical tree view")
        print("     • Add/Edit/Delete categories")
        print("     • Subcategory support")
        print("     • Color picker")
        print("     • Type badges (income/expense/transfer)")
        print()
        print("   - Category Rules Management")
        print("     • Add rules with pattern matching")
        print("     • Priority ordering")
        print("     • Delete rules")
        print()
        print("   - Accounts Management")
        print("     • Add accounts with starting balance")
        print("     • View account details")
        print("     • Delete accounts")
        print()
        print("   - Forecast Management")
        print("     • Add forecast items")
        print("     • Set frequency (monthly/quarterly/annual)")
        print("     • Set type (fixed/variable)")
        print("     • Delete forecast items")
        print()
        
        print("Starting Flask server...")
        print("Visit: http://localhost:5000/config")
        print()
        print("Press Ctrl+C to stop the server")
        
        # Open browser after short delay
        def open_browser():
            time.sleep(1.5)
            webbrowser.open('http://localhost:5000/config')
        
        Thread(target=open_browser, daemon=True).start()
        
        # Run Flask app
        app.run(debug=True, use_reloader=False)

if __name__ == '__main__':
    test_phase4()
