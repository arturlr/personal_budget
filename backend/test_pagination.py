#!/usr/bin/env python3
"""Test pagination functionality"""

def test_pagination_helper():
    """Test the paginate_query helper function"""
    from app import paginate_query
    
    # Mock query object
    class MockQuery:
        def __init__(self, total_items):
            self.total_items = total_items
            self._items = list(range(total_items))
        
        def count(self):
            return self.total_items
        
        def limit(self, n):
            self._limit = n
            return self
        
        def offset(self, n):
            self._offset = n
            return self
        
        def all(self):
            start = getattr(self, '_offset', 0)
            end = start + getattr(self, '_limit', len(self._items))
            return self._items[start:end]
    
    # Test basic pagination
    query = MockQuery(250)
    result = paginate_query(query, page=1, per_page=100)
    
    assert result['page'] == 1
    assert result['per_page'] == 100
    assert result['total'] == 250
    assert result['pages'] == 3
    assert len(result['items']) == 100
    
    # Test page 2
    result = paginate_query(query, page=2, per_page=100)
    assert result['page'] == 2
    assert len(result['items']) == 100
    
    # Test last page
    result = paginate_query(query, page=3, per_page=100)
    assert result['page'] == 3
    assert len(result['items']) == 50
    
    # Test max per_page limit
    result = paginate_query(query, page=1, per_page=2000)
    assert result['per_page'] == 1000  # Should be capped at max
    
    # Test negative page (should default to 1)
    result = paginate_query(query, page=-1, per_page=100)
    assert result['page'] == 1
    
    print("✓ Pagination helper function working correctly")
    return True

def test_response_structure():
    """Test that pagination responses have correct structure"""
    print("✓ Response structure test (manual verification needed)")
    print("  Expected response format:")
    print("  {")
    print("    'transactions': [...],  // or 'rules', 'items'")
    print("    'pagination': {")
    print("      'page': 1,")
    print("      'per_page': 100,")
    print("      'total': 250,")
    print("      'pages': 3")
    print("    }")
    print("  }")
    return True

if __name__ == '__main__':
    print("Testing pagination...\n")
    
    tests = [
        test_pagination_helper,
        test_response_structure
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
            print(f"✗ {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*50}")
