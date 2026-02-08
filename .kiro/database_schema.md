# Database Schema

## Overview
SQLite database with Flask-SQLAlchemy ORM and Flask-Migrate for migrations.

## Tables

### accounts
Stores bank/credit card accounts.

```sql
CREATE TABLE accounts (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    account_number VARCHAR(50),
    starting_balance DECIMAL(10, 2) DEFAULT 0
)
```

### categories
Hierarchical category structure for income/expense classification.

```sql
CREATE TABLE categories (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    parent_id INTEGER,
    type VARCHAR(20) NOT NULL,  -- 'income', 'expense', or 'transfer'
    color VARCHAR(20),
    CONSTRAINT uq_category_name_parent UNIQUE (name, parent_id),
    FOREIGN KEY(parent_id) REFERENCES categories (id)
)
```

**Key Features:**
- Hierarchical: parent_id references same table for subcategories
- Unique constraint on (name, parent_id) allows same name in different parents
- Example: "Home > Utilities" and "Car > Maintenance"

### transactions
Financial transactions with categorization and approval workflow.

```sql
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY,
    account_id INTEGER NOT NULL,
    date DATE NOT NULL,
    memo VARCHAR(200),
    amount DECIMAL(10, 2) NOT NULL,
    category_id INTEGER,
    suggested_category_id INTEGER,
    is_approved BOOLEAN DEFAULT FALSE,
    is_credit_card_payment BOOLEAN DEFAULT FALSE,
    hash VARCHAR(64) UNIQUE,  -- For deduplication
    FOREIGN KEY(account_id) REFERENCES accounts (id),
    FOREIGN KEY(category_id) REFERENCES categories (id),
    FOREIGN KEY(suggested_category_id) REFERENCES categories (id)
)
```

**Key Features:**
- hash: SHA-256 of (date, memo, amount) for duplicate detection
- category_id: User-selected or rule-assigned category
- suggested_category_id: Auto-suggested by rules (deprecated in UI)
- is_credit_card_payment: Auto-detected for CC payments

### category_rules
Pattern-based rules for automatic transaction categorization.

```sql
CREATE TABLE category_rules (
    id INTEGER PRIMARY KEY,
    pattern VARCHAR(200) NOT NULL,
    category_id INTEGER NOT NULL,
    priority INTEGER DEFAULT 5,
    FOREIGN KEY(category_id) REFERENCES categories (id)
)
```

**Key Features:**
- pattern: Case-insensitive substring match on transaction memo
- priority: Higher priority rules checked first
- Applied during import to auto-categorize transactions

### forecast_items
Budget forecast items for planning.

```sql
CREATE TABLE forecast_items (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category_id INTEGER NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    frequency VARCHAR(20) NOT NULL,  -- 'monthly', 'quarterly', 'annual'
    type VARCHAR(20) NOT NULL,       -- 'fixed', 'variable'
    start_date DATE,
    FOREIGN KEY(category_id) REFERENCES categories (id)
)
```

## Relationships

```
accounts (1) ──< (N) transactions
categories (1) ──< (N) transactions (via category_id)
categories (1) ──< (N) categories (via parent_id) [self-referential]
categories (1) ──< (N) category_rules
categories (1) ──< (N) forecast_items
```

## Indexes

Recommended indexes for performance:
- `transactions.date` - For date range queries
- `transactions.account_id` - For account filtering
- `transactions.category_id` - For category reports
- `transactions.hash` - Already unique, used for deduplication
- `category_rules.priority` - For rule ordering

## Migration History

1. Initial schema with basic tables
2. Added hash column for deduplication
3. Added is_credit_card_payment flag
4. Changed category unique constraint from (name) to (name, parent_id)
