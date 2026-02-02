# Personal Finance App – Development Plan
## Flask + SQLite with Cash Flow & Accrual Reporting

---

## Phase 1 – Core Foundations

### 1. Project Structure

```text
personal_budget/
  backend/
    app.py
    models.py
    services/
      importer.py
      categorizer.py
      accrual.py
      forecast.py
  migrations/        # optional if using Alembic/Flask-Migrate
  venv/
```

### 2. Environment & Dependencies

```bash
pip install flask sqlalchemy flask_sqlalchemy flask-migrate ofxparse
```

### 3. Database Models (models.py)

**Account**
- `id` (PK)
- `name`
- `number`
- `ofx_account_id` (nullable, for OFX mapping persistence)
- `starting_balance` (decimal, for previous year balance)
- `starting_balance_date` (date, nullable)

**Category**
- `id` (PK)
- `name`
- `parent_id` (FK → Category, nullable, for subcategories)
- `type` (income | expense | transfer)
- `color` (string, nullable, for chart display)

**Transaction**
- `id` (PK)
- `account_id` (FK → Account)
- `date`
- `memo`
- `amount`
- `category_id` (FK → Category, nullable)
- `subcategory_id` (FK → Category, nullable)
- `suggested_category_id` (FK → Category, nullable)
- `suggested_subcategory_id` (FK → Category, nullable)
- `is_approved` (bool)
- `is_credit_card_payment` (bool, to exclude from accrual reports)
- `accrual_start_date` (nullable)
- `accrual_end_date` (nullable)
- `accrual_method` (nullable, e.g. straight_line)
- `unique_hash` (string, for deduplication: hash of account_id + date + memo + amount)

**CategoryRule**
- `id` (PK)
- `pattern` (text)
- `category_id` (FK → Category)
- `subcategory_id` (FK → Category, nullable)
- `priority` (int)

**ForecastItem**
- `id` (PK)
- `name`
- `category_id` (FK → Category)
- `subcategory_id` (FK → Category, nullable)
- `amount` (decimal)
- `frequency` (monthly | annual | quarterly)
- `type` (fixed | variable)
- `start_date` (date)
- `end_date` (date, nullable)

### 4. Flask + SQLite Wiring

- Configure DB URI: `sqlite:///budget.db`
- Initialize SQLAlchemy and (optionally) Flask-Migrate
- Create initial migration and upgrade DB

```bash
flask db init
flask db migrate -m "Initial schema"
flask db upgrade
```

---

## Phase 2 – Import & Categorization (Transactions + Config)

### 5. Import Service (services/importer.py)

**Responsibilities:**
- Accept uploaded file (CSV 3-column, CSV 4-column, or OFX)
- Parse into normalized records: (account_name/number, date, memo, amount)
- Resolve or create Account (persist OFX account ID mapping)
- Deduplicate transactions using unique_hash

**CSV Format Support (QuickBooks-compatible):**

*3-column format:*
```
Date,Description,Amount
1/1/2018,Example of a payment,-100.00
1/1/2018,Example of a deposit,200.00
```

*4-column format:*
```
Date,Description,Credit,Debit
1/1/2018,Example of a payment,,100.00
1/1/2018,Example of a deposit,200.00,
```

**Parsing Rules:**
- Date formats: dd/mm/yyyy, mm/dd/yyyy, yyyy-mm-dd (auto-detect)
- Remove day-of-week suffixes (e.g., "20/11/2018 TUE" → "20/11/2018")
- 3-column: negative amount = expense, positive = income
- 4-column: Credit = income, Debit = expense (convert to signed amount)
- Skip rows with blank amounts or zeroes
- Trim whitespace from Description

**Key Functions:**
- `parse_csv_3col(file)` → list of transaction dicts
- `parse_csv_4col(file)` → list of transaction dicts
- `detect_csv_format(file)` → '3col' | '4col'
- `parse_ofx(file)` → list of transaction dicts
- `import_transactions(transactions_list, account_id)` → insert into DB, return stats
- `generate_unique_hash(account_id, date, memo, amount)` → hash string

### 6. Categorization Service (services/categorizer.py)

**Logic:**
- Load all CategoryRule ordered by priority DESC
- For each transaction:
  - Normalize memo: `memo_norm = memo.lower()`
  - Find first rule where `pattern.lower() in memo_norm`
  - If found, set `suggested_category_id` and `suggested_subcategory_id`
- Initially:
  - `category_id = NULL`, `subcategory_id = NULL`
  - `is_approved = False`

**Credit Card Payment Detection:**
- If memo contains keywords like "CREDIT CARD PAYMENT", "CC PAYMENT", "AUTOPAY"
- Set `is_credit_card_payment = True`
- These transactions excluded from accrual reports (only individual charges shown)

**Key Functions:**
- `suggest_category(memo)` → (category_id, subcategory_id) or (None, None)
- `apply_suggestions(transaction_list)` → updates suggested fields
- `detect_credit_card_payment(memo)` → bool

### 7. Core API Endpoints (Backend)

**Import**
- `POST /api/import`
  - Input: uploaded file (multipart/form-data) + account_id
  - Behavior: detect format, parse, dedupe via hash, apply suggestions, insert into DB
  - Output: `{ "imported": 42, "duplicates_skipped": 3, "format_detected": "csv_4col" }`

**Transactions**
- `GET /api/transactions`
  - Query params: `from`, `to`, `account_id`, `category_id`, `approved`, `exclude_cc_payments`
  - Output: list of transactions with suggested & chosen categories/subcategories
- `PATCH /api/transactions/<id>`
  - Input: JSON with fields to update (category_id, subcategory_id, accrual_start_date, etc.)
  - Output: updated transaction

**Categories**
- `GET /api/categories` – list all (hierarchical: categories with subcategories nested)
- `POST /api/categories` – create new (specify parent_id for subcategory)
- `PATCH /api/categories/<id>` – update
- `DELETE /api/categories/<id>` – delete (cascade to subcategories or prevent if has children)

**Category Rules**
- `GET /api/category-rules` – list all rules
- `POST /api/category-rules` – create new rule (include subcategory_id if applicable)
- `PATCH /api/category-rules/<id>` – update rule
- `DELETE /api/category-rules/<id>` – delete rule

**Accounts**
- `GET /api/accounts` – list all
- `POST /api/accounts` – create new (include starting_balance and starting_balance_date)
- `PATCH /api/accounts/<id>` – update
- `DELETE /api/accounts/<id>` – delete

**Forecast**
- `GET /api/forecast` – list all forecast items
- `POST /api/forecast` – create new forecast item
- `PATCH /api/forecast/<id>` – update
- `DELETE /api/forecast/<id>` – delete
- `GET /api/forecast/projection` – calculate projected expenses/income for date range

---

## Phase 3 – Transactions UI

### 8. Transactions Screen

**Components:**

Table columns:
- Date
- Account
- Memo
- Amount
- Suggested Category (read-only, from rules)
- Suggested Subcategory (read-only, from rules)
- Category (editable dropdown)
- Subcategory (editable dropdown, filtered by selected category)
- Status (Approved/Pending badge)
- CC Payment indicator (icon if is_credit_card_payment = true)

**Interactions:**
- Change category/subcategory via dropdowns
- Approve transaction button (sets category_id, subcategory_id, is_approved = true)
- Bulk approve selected transactions
- Mark/unmark as credit card payment

**Filter controls:**
- Date range picker
- Account selector
- Category selector (with subcategory drill-down)
- Status toggle (All | Pending | Approved)
- Hide CC payments checkbox

**Backend Integration:**
- Load data via `GET /api/transactions?approved=false&exclude_cc_payments=false`
- Apply changes via `PATCH /api/transactions/<id>`
- Refresh list after changes

**Features:**
- Pagination (50-100 rows per page)
- Sort by date, amount, account
- Search by memo text
- Visual indicators for:
  - Suggested vs manually chosen categories
  - Unapproved transactions (highlight)
  - Credit card payments (gray out or icon)

---

## Phase 4 – Config Area

### 9. Config Sections

#### 9.1 Categories Management

**UI Features:**
- Hierarchical tree view: Categories with expandable subcategories
- Table showing: Name, Type (income/expense/transfer), Parent Category
- Add category form (checkbox: "Is this a subcategory?" → shows parent dropdown)
- Edit inline or modal
- Delete with confirmation (prevent if has subcategories or transactions)
- Color picker for chart display
- Drag-and-drop to reorder or change parent (optional enhancement)

**Validation:**
- Enforce unique names across all categories and subcategories
- Prevent circular parent relationships

#### 9.2 Category Rules

**UI Features:**
- Table showing: Pattern, Category, Subcategory, Priority
- Add rule form:
  - Pattern input (e.g., "AMAZON", "UBER *TRIP")
  - Category dropdown
  - Subcategory dropdown (filtered by selected category)
  - Priority number (higher = checked first)
- Edit/delete actions
- Test pattern feature:
  - Input sample memo
  - Shows which rule would match
  - Useful for debugging rules
- Bulk import rules from CSV

#### 9.3 Accounts

**UI Features:**
- Table showing: Name, Account Number, Starting Balance, Starting Balance Date
- Add/edit/delete forms
- OFX Account ID mapping display (read-only, auto-populated on first import)
- Used during import to map OFX/CSV account IDs to friendly names

#### 9.4 Forecast

**UI Features:**
- Table showing: Name, Category, Subcategory, Amount, Frequency, Type (Fixed/Variable)
- Add forecast item form:
  - Name input
  - Category/subcategory dropdowns
  - Amount input
  - Frequency dropdown (Monthly, Quarterly, Annual)
  - Type toggle (Fixed/Variable)
  - Date range (start/end)
- Edit/delete actions
- Summary view: Total fixed vs variable expenses per month

### 10. Config API Endpoints

Already covered in Phase 2:
- `/api/categories*` – CRUD for categories (hierarchical support)
- `/api/category-rules*` – CRUD for rules (with subcategory support)
- `/api/accounts*` – CRUD for accounts (with starting balance)
- `/api/forecast*` – CRUD for forecast items

---

## Phase 5 – Dashboard & Visualizations

### 11. Dashboard Layout

**Top Section – Summary Cards (Month-to-Date):**
- Total Income (blue)
- Total Expenses (red)
- Net Cash Flow (green/red based on positive/negative)
- Budget vs Actual (if forecast exists)


**Main Charts:**

1. **Monthly Spending by Category (Dynamic Dropdown)**
   - Dropdown: Select month
   - Horizontal bar chart
   - Shows spending by category for selected month
   - Percentage labels (% of total spending that month)
   - Click bar to drill down to subcategories

2. **Budget Report (12-month view)**
   - X-axis: months (Jan-Dec)
   - Blue bars: Income
   - Red line: Total expenses (cash method)
   - Orange line: Total expenses (accrual method)
   - Light green/red bars: Net difference (income - cash expenses)
   - Small inset box: Month-to-date summary (3 bars: income, expenses, net)

3. **Monthly Category Report (Dynamic Dropdown)**
   - Dropdown: Select category
   - Line chart with bars
   - X-axis: months
   - Y-axis: amount spent
   - Bars show amount, percentage labels (% of total expenses that month)
   - Helps identify spending trends in specific category

4. **Weekly Expense Report**
   - X-axis: 52 weeks of the year
   - Y-axis: total expenses
   - Bar chart
   - Based on accrual method (excludes credit card payments)
   - Shows spending patterns by week

5. **Year Summary – Stacked Bar**
   - X-axis: months
   - Y-axis: total expenses
   - Stacked bars: each segment = different category
   - Color-coded by category
   - Shows composition of spending each month

6. **Category Expenses (Month-to-Date)**
   - Horizontal bar chart
   - Bar size = amount spent
   - Percentage labels (% of total expenses)
   - Top 10 categories

7. **Income Sources (Month-to-Date)**
   - Horizontal bar chart
   - Bar size = income amount
   - Percentage labels (% of total income)
   - All income categories

### 12. Dashboard API

**Endpoints:**
- `GET /api/dashboard/summary`
  - Query params: `from`, `to`, `account_id`
  - Output: `{ "total_income": 5000, "total_expenses": 3500, "net": 1500, "budget_variance": 200 }`
- `GET /api/dashboard/monthly-spending-by-category`
  - Query params: `month` (YYYY-MM), `account_id`
  - Output: `[ { "category": "Groceries", "amount": 500, "percentage": 15.2 }, ... ]`
- `GET /api/dashboard/budget-report`
  - Query params: `year`, `account_id`
  - Output: `[ { "month": "2026-01", "income": 5000, "cash_expenses": 3500, "accrual_expenses": 3200, "net": 1500 }, ... ]`
- `GET /api/dashboard/monthly-category-trend`
  - Query params: `category_id`, `year`, `account_id`
  - Output: `[ { "month": "2026-01", "amount": 200, "percentage": 8.5 }, ... ]`
- `GET /api/dashboard/weekly-expenses`
  - Query params: `year`, `account_id`
  - Output: `[ { "week": 1, "amount": 450 }, ... ]` (52 weeks)
- `GET /api/dashboard/year-summary-stacked`
  - Query params: `year`, `account_id`
  - Output: `[ { "month": "2026-01", "categories": { "Groceries": 500, "Rent": 1200, ... } }, ... ]`

---

## Phase 6 – Cash Flow Reports

### 13. Cash-Basis Reporting Queries

**Monthly Net Cash Flow (SQLite):**

```sql
SELECT strftime('%Y-%m', date) AS month,
       SUM(amount) AS net_cash
FROM transactions
WHERE is_approved = 1
GROUP BY month
ORDER BY month;
```

**Monthly Spending by Category:**

```sql
SELECT strftime('%Y-%m', date) AS month,
       c.name AS category,
       SUM(CASE WHEN amount < 0 THEN -amount ELSE 0 END) AS spending
FROM transactions t
JOIN categories c ON t.category_id = c.id
WHERE is_approved = 1 AND c.type = 'expense'
GROUP BY month, category
ORDER BY month, category;
```

**Monthly Income by Category:**

```sql
SELECT strftime('%Y-%m', date) AS month,
       c.name AS category,
       SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) AS income
FROM transactions t
JOIN categories c ON t.category_id = c.id
WHERE is_approved = 1 AND c.type = 'income'
GROUP BY month, category
ORDER BY month, category;
```

**Account Balances (with starting balance):**

```sql
SELECT a.name,
       a.starting_balance + COALESCE(SUM(t.amount), 0) AS current_balance
FROM accounts a
LEFT JOIN transactions t ON a.id = t.account_id AND t.is_approved = 1
GROUP BY a.id;
```

### 14. Cash Flow API

**Endpoints:**
- `GET /api/reports/cashflow/monthly`
  - Query params: `from`, `to`, `account_id`
  - Output: `[ { "month": "2026-01", "net_cash": 1234.56 }, ... ]`
- `GET /api/reports/cashflow/by-category`
  - Query params: `from`, `to`, `account_id`, `type` (income/expense)
  - Output: `[ { "month": "2026-01", "category": "Groceries", "subcategory": "Produce", "spending": 200.0 }, ... ]`
- `GET /api/reports/cashflow/summary`
  - Returns totals for period: total income, total expenses, net
- `GET /api/reports/cashflow/account-balances`
  - Query params: `as_of_date`
  - Output: `[ { "account": "Checking", "balance": 5432.10 }, ... ]`

### 15. Cash Flow Tab UI

**Layout:**

Top section:
- Account balance cards (each account with current balance)
- Total net worth

Main table:
- Rows: Categories (with subcategories indented)
- Columns: Jan, Feb, Mar, ..., Dec, Total
- Values: Cash-basis amounts
- Footer row: Monthly totals

**Features:**
- Excludes credit card payment transactions
- Shows actual cash movement
- Drill-down: Click cell to see transactions for that category/month
- Export to CSV/Excel

**Credit Card Detail Section:**
- Separate table showing credit card payments by month
- Shows amount and percentage of total expenses
- Helps understand credit card impact on cash flow

---

## Phase 7 – Accrual Method Logic & Reports

### 16. Accrual Fields on Transactions

**Extended Transaction Model:**
- `accrual_start_date` – when accrual period begins
- `accrual_end_date` – when accrual period ends
- `accrual_method` – e.g., straight_line, monthly, one_time

**UI Changes in Transactions Screen:**

Add "Accrual Settings" section when editing a transaction

Form fields:
- Checkbox: "Spread this transaction over time"
- Date pickers: Start date, End date
- Method dropdown (for future: could add weighted methods)

### 17. Accrual Calculation (services/accrual.py)

**Approach A – On-the-Fly Calculation (Recommended for MVP):**

```python
def calculate_accrual_series(from_date, to_date, filters=None):
    """
    For each transaction with accrual dates:
    1. Determine months between accrual_start_date and accrual_end_date
    2. Compute monthly share: amount / n_months
    3. Aggregate by month and (optionally) category

    Returns: [ { "month": "2026-01", "accrual_total": ... }, ... ]
    """
    pass
```

**Algorithm:**
- Query transactions where:
  - `accrual_start_date IS NOT NULL` AND
  - `is_credit_card_payment = FALSE` AND
  - Accrual period overlaps `[from_date, to_date]`
- For each transaction:
  - Calculate months in accrual period
  - Distribute amount evenly (or per method)
  - Add each month's portion to aggregation dict
- Return sorted list by month

**Credit Card Handling:**
- Individual credit card charges: included in accrual (with their categories)
- Credit card payment transactions: excluded (is_credit_card_payment = true)
- This shows true spending pattern, not payment timing

**Approach B – Precomputed Table (Optional, for performance):**

Create `accrual_slices` table:
- `id` (PK)
- `transaction_id` (FK)
- `month` (date, first day of month)
- `amount` (decimal, portion for that month)

Regenerate slices when transaction accrual fields change via trigger or service method.

### 18. Accrual Reports API

**Endpoints:**
- `GET /api/reports/accrual/monthly`
  - Query params: `from`, `to`, `account_id`
  - Uses accrual service to build monthly series
  - Output: `[ { "month": "2026-01", "accrual_total": 1234.56 }, ... ]`
- `GET /api/reports/accrual/by-category`
  - Query params: `from`, `to`, `account_id`, `type`
  - Output: `[ { "month": "2026-01", "category": "Insurance", "accrual_amount": 100.0 }, ... ]`
- `GET /api/reports/accrual/summary`
  - Returns period totals using accrual method

### 19. Year Stats & Accrual Details Tabs

**Year Stats Tab:**

Table layout:
- Rows: Main categories only (no subcategories)
- Columns: Jan, Feb, Mar, ..., Dec, Total, Average
- Values: Accrual-basis amounts
- Separate sections for Income and Expenses
- Footer: Monthly totals and grand total

**Accrual Details Tab:**

Table layout:
- Rows: Categories with subcategories (indented or grouped)
- Columns: Jan, Feb, Mar, ..., Dec, Total, Average
- Values: Accrual-basis amounts
- Shows granular breakdown
- Drill-down: Click cell to see transactions

**Features:**
- Toggle between Cash and Accrual view
- Export to CSV/Excel
- Highlight cells with significant variance
- Comparison mode: Compare current year to previous year

---

## Phase 8 – Forecast & Budget Comparison

### 20. Forecast Service (services/forecast.py)

**Responsibilities:**
- Calculate projected expenses/income for date range
- Apply frequency rules (monthly, quarterly, annual)
- Prorate partial periods
- Compare actual vs forecast

**Key Functions:**
- `calculate_forecast(from_date, to_date)` → dict of monthly projections
- `compare_actual_vs_forecast(from_date, to_date)` → variance report

### 21. Forecast API

**Endpoints:**
- `GET /api/forecast/projection`
  - Query params: `from`, `to`
  - Output: `[ { "month": "2026-01", "category": "Rent", "forecasted": 1200, "actual": 1200, "variance": 0 }, ... ]`
- `GET /api/forecast/summary`
  - Query params: `from`, `to`
  - Output: `{ "total_forecasted": 5000, "total_actual": 4800, "variance": -200, "variance_pct": -4.0 }`

### 22. Forecast UI

**Forecast Tab:**
- Table showing all forecast items
- Add/edit/delete forms (covered in Phase 4)

**Budget vs Actual Chart:**
- X-axis: months
- Y-axis: amount
- Two bars per month: Forecasted (blue), Actual (green/red based on over/under)
- Variance line showing difference

**Variance Report:**
- Table: Category, Forecasted, Actual, Variance ($), Variance (%)
- Highlight over-budget items in red
- Filter by variance threshold (e.g., show only >10% variance)

---

## Phase 9 – Polish & Enhancements

### 23. Additional Features

**Data Export:**
- Export any report to CSV/Excel
- Export transactions with filters applied
- Scheduled email reports (optional)

**Data Backup:**
- Export entire database to JSON
- Import from backup file
- Automatic backups (daily/weekly)

**Multi-Currency Support (Optional):**
- Add currency field to accounts
- Convert to base currency for reports
- Exchange rate table

**Mobile Responsiveness:**
- Responsive design for all screens
- Touch-friendly controls
- Simplified mobile dashboard

**Security:**
- User authentication (if multi-user)
- Encrypted database (SQLCipher)
- Audit log for changes

**Performance:**
- Index on transaction date, account_id, category_id
- Cache dashboard queries
- Pagination for large datasets

### 24. Testing Strategy

**Unit Tests:**
- Import service (CSV/OFX parsing)
- Categorization logic
- Accrual calculation
- Forecast calculation

**Integration Tests:**
- API endpoints
- Database operations
- File upload/download

**UI Tests:**
- Critical user flows (import → categorize → approve)
- Dashboard rendering
- Report generation

---

## Implementation Roadmap

**Sprint 1 (2 weeks):** Phase 1-2 (Core foundations, import, categorization)
**Sprint 2 (2 weeks):** Phase 3-4 (Transactions UI, config area)
**Sprint 3 (2 weeks):** Phase 5 (Dashboard visualizations)
**Sprint 4 (1 week):** Phase 6 (Cash flow reports)
**Sprint 5 (2 weeks):** Phase 7 (Accrual logic and reports)
**Sprint 6 (1 week):** Phase 8 (Forecast and budget comparison)
**Sprint 7 (1 week):** Phase 9 (Polish and testing)

**Total: 11 weeks**
