#!/bin/bash
# API Test Script for Phase 2
# Make sure Flask app is running: cd backend && source venv/bin/activate && flask run

BASE_URL="http://localhost:5000"

echo "=== Testing Personal Finance API ==="
echo

# Test 1: Health check
echo "1. Health Check"
curl -s $BASE_URL/ | python3 -m json.tool
echo

# Test 2: Create account
echo "2. Create Account"
ACCOUNT_ID=$(curl -s -X POST $BASE_URL/api/accounts \
  -H "Content-Type: application/json" \
  -d '{"name": "Main Checking", "number": "1234", "starting_balance": 1000.00}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Created account ID: $ACCOUNT_ID"
echo

# Test 3: Create categories
echo "3. Create Categories"
CAT_GROCERIES=$(curl -s -X POST $BASE_URL/api/categories \
  -H "Content-Type: application/json" \
  -d '{"name": "Groceries", "type": "expense", "color": "#ff0000"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Created Groceries category ID: $CAT_GROCERIES"

CAT_SHOPPING=$(curl -s -X POST $BASE_URL/api/categories \
  -H "Content-Type: application/json" \
  -d '{"name": "Shopping", "type": "expense", "color": "#ff9900"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Created Shopping category ID: $CAT_SHOPPING"
echo

# Test 4: Create category rules
echo "4. Create Category Rules"
curl -s -X POST $BASE_URL/api/category-rules \
  -H "Content-Type: application/json" \
  -d "{\"pattern\": \"WHOLE FOODS\", \"category_id\": $CAT_GROCERIES, \"priority\": 10}" \
  | python3 -m json.tool

curl -s -X POST $BASE_URL/api/category-rules \
  -H "Content-Type: application/json" \
  -d "{\"pattern\": \"AMAZON\", \"category_id\": $CAT_SHOPPING, \"priority\": 5}" \
  | python3 -m json.tool
echo

# Test 5: Import CSV
echo "5. Import CSV File"
curl -s -X POST $BASE_URL/api/import \
  -F "file=@test_data/sample_3col.csv" \
  -F "account_id=$ACCOUNT_ID" \
  | python3 -m json.tool
echo

# Test 6: Get transactions
echo "6. Get All Transactions"
curl -s "$BASE_URL/api/transactions" | python3 -m json.tool
echo

# Test 7: Get unapproved transactions
echo "7. Get Unapproved Transactions"
curl -s "$BASE_URL/api/transactions?approved=false" | python3 -m json.tool
echo

echo "=== API Tests Complete ==="
