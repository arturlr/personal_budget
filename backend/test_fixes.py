#!/usr/bin/env python3
"""
Quick tests to verify the fixes are working
"""
import sys

def test_imports():
    """Test that all imports work"""
    try:
        from app import app, validate_category, validate_rule, validate_account, validate_forecast, to_str
        from services.importer import import_transactions
        from sqlalchemy.exc import IntegrityError
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_validation_functions():
    """Test validation functions"""
    from app import validate_category, validate_rule, validate_account, validate_forecast
    
    # Test category validation
    assert validate_category({'name': '', 'type': 'expense'}) is not None, "Should reject empty name"
    assert validate_category({'name': 'Test', 'type': 'invalid'}) is not None, "Should reject invalid type"
    assert validate_category({'name': 'Test', 'type': 'expense'}) is None, "Should accept valid data"
    
    # Test rule validation
    assert validate_rule({'pattern': '', 'category_id': 1}) is not None, "Should reject empty pattern"
    assert validate_rule({'pattern': 'test'}) is not None, "Should reject missing category_id"
    assert validate_rule({'pattern': 'test', 'category_id': 1}) is None, "Should accept valid data"
    
    # Test account validation
    assert validate_account({'name': ''}) is not None, "Should reject empty name"
    assert validate_account({'name': 'Test'}) is None, "Should accept valid data"
    
    # Test forecast validation
    assert validate_forecast({'name': 'Test', 'category_id': 1, 'amount': 100, 'frequency': 'monthly', 'type': 'fixed', 'start_date': '2026-01-01'}) is None
    assert validate_forecast({'name': '', 'category_id': 1, 'amount': 100, 'frequency': 'monthly', 'type': 'fixed', 'start_date': '2026-01-01'}) is not None
    
    print("✓ All validation functions working correctly")
    return True

def test_to_str_function():
    """Test Decimal to string conversion"""
    from app import to_str
    from decimal import Decimal
    
    assert to_str(Decimal('123.45')) == '123.45', "Should convert Decimal to string"
    assert to_str(None) is None, "Should handle None"
    assert to_str(100) == '100', "Should convert int to string"
    
    print("✓ to_str() function working correctly")
    return True

def test_app_config():
    """Test Flask app configuration"""
    from app import app
    
    assert 'MAX_CONTENT_LENGTH' in app.config, "Should have MAX_CONTENT_LENGTH set"
    assert app.config['MAX_CONTENT_LENGTH'] == 10 * 1024 * 1024, "Should be 10MB"
    
    print("✓ Flask configuration correct")
    return True

if __name__ == '__main__':
    print("Running fix verification tests...\n")
    
    tests = [
        test_imports,
        test_validation_functions,
        test_to_str_function,
        test_app_config
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed with exception: {e}")
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*50}")
    
    sys.exit(0 if failed == 0 else 1)
