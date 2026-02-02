# Glossary - Personal Budget App

## Financial Terms

**Cash Flow Method**
Recording transactions when money actually moves. A $100 expense is recorded on the date paid.

**Accrual Method**
Recording transactions when they're incurred, spread over time. A $1200 annual insurance payment is recorded as $100/month for 12 months.

**Credit Card Payment**
A transaction that pays off a credit card balance. These are excluded from accrual reports because the individual charges are what matter, not the payment timing.

**Starting Balance**
The account balance at the beginning of tracking (e.g., previous year's ending balance).

**Forecast Item**
A budgeted expense or income that hasn't happened yet. Used for planning and budget vs actual comparison.

## Application Terms

**Transaction**
A single financial event: payment, deposit, transfer. Has date, amount, memo, and optional category.

**Category**
A classification for transactions (e.g., "Groceries", "Salary"). Can be income, expense, or transfer type.

**Subcategory**
A child category under a parent category (e.g., "Produce" under "Groceries").

**Category Rule**
A pattern-matching rule that automatically suggests categories for imported transactions based on memo text.

**Unique Hash**
SHA256 hash of account_id + date + memo + amount. Used to detect duplicate transactions during import.

**Suggested Category**
The category automatically assigned by a matching rule. User can accept or change it.

**Approved Transaction**
A transaction where the user has confirmed the category assignment. Unapproved transactions need review.

**OFX**
Open Financial Exchange - a standard file format for financial data exchange used by banks and financial software.

## Technical Terms

**Migration**
A database schema change tracked by Alembic/Flask-Migrate. Allows versioned database updates.

**Service Layer**
Business logic modules (importer, categorizer) that handle operations independent of HTTP/API concerns.

**Deduplication**
Preventing the same transaction from being imported multiple times by checking the unique hash.

**Priority**
Category rules are checked in priority order (highest first). First match wins.

## Workflow Terms

**Import**
Upload and parse a CSV or OFX file, create transactions, apply categorization rules.

**Categorization**
The process of assigning categories to transactions, either automatically via rules or manually.

**Approval**
User confirmation that a transaction's category is correct. Moves suggested_category to category.

**Bulk Approve**
Approving multiple transactions at once (Phase 3 feature).

## Report Types (Future Phases)

**Cash Flow Report**
Shows actual money movement by month/category.

**Accrual Report**
Shows expenses spread over time periods (e.g., annual insurance as monthly amounts).

**Budget vs Actual**
Compares forecasted amounts to actual spending.

**Year Summary**
Stacked bar chart showing spending composition by category over 12 months.
