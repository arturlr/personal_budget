## **Implementation Plan - AWS Migration with Vue.js, Cognito, AppSync & PostgreSQL**

### **Problem Statement:**
Migrate the existing Flask-based personal budget application to a production-ready, multi-tenant AWS
architecture using modern serverless technologies while maintaining all existing functionality.

### **Requirements:**
- **Multi-tenant architecture**: Each user has isolated data (user_id on all tables)
- **Production-ready**: Scalable, secure, with proper monitoring and error handling
- **Technology stack**: Vue.js frontend, Amazon Cognito authentication, AWS AppSync GraphQL API, RDS
PostgreSQL database
- **File handling**: Direct S3 uploads with presigned URLs for CSV/OFX imports
- **Infrastructure**: AWS SAM for IaC, Lambda-first approach (minimal containers)
- **Frontend hosting**: S3 + CloudFront for static site delivery
- **Fresh start**: No data migration from existing SQLite database

### **Background:**

Current Architecture (from `.kiro/architecture.md` and `.kiro/technical_context.md`):
- **Framework**: Flask 3.1.2 monolith with SQLAlchemy 2.0.46 ORM
- **Database**: SQLite (file-based at backend/instance/budget.db)
- **Migrations**: Flask-Migrate 4.1.0 (Alembic)
- **Frontend**: Server-side rendered HTML templates with vanilla JavaScript and Chart.js
- **Python Version**: 3.8+ required (developed with Python 3.13)
- **5 main entities**: Account, Category, Transaction, CategoryRule, ForecastItem
- **Business logic services**: 
  - `importer.py` - CSV/OFX parsing with hash-based deduplication
  - `categorizer.py` - Pattern-based rule matching with priority ordering
  - `accrual.py` - Accrual calculation logic (Phase 7)
  - `forecast.py` - Budget forecasting logic (Phase 8)

Current Implementation Status (from `.kiro/project_context.md`):
- **Phase 1**: ✅ Complete - Core foundations (models, database, Flask setup)
- **Phase 2**: ✅ Complete - Import & categorization (CSV/OFX, rules, API)
- **Phase 3**: ✅ Complete - Transactions UI
- **Phase 4**: ✅ Complete - Config area (categories, rules, accounts, forecast)
- **Phase 5**: ✅ Complete - Dashboard & visualizations
- **Phase 6**: 🚧 In Progress - Cash flow reports
- **Phases 7-9**: Planned (Accrual reports, Budget vs Actual, Enhancements)

Target AWS Architecture:
```
┌─────────────┐
│   User      │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│  CloudFront + S3 (Vue.js SPA)       │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Amazon Cognito (Authentication)    │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  AWS AppSync (GraphQL API)          │
│  - Direct RDS resolver (queries)    │
│  - Lambda resolver (mutations)      │
└──────┬──────────────────────────────┘
       │
       ├──────────────┬─────────────┐
       ▼              ▼             ▼
┌──────────┐   ┌──────────┐   ┌──────────┐
│ Lambda   │   │ Lambda   │   │   RDS    │
│ Import   │   │ Business │   │PostgreSQL│
│ Processor│   │  Logic   │   │          │
└────┬─────┘   └──────────┘   └──────────┘
     │
     ▼
┌──────────┐
│    S3    │
│  Uploads │
└──────────┘
```

---

## **Current Database Schema to AWS PostgreSQL Mapping**

Based on `.kiro/database_schema.md`, the following tables need multi-tenant transformation:

### **accounts**
```sql
-- Current SQLite Schema
CREATE TABLE accounts (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    account_number VARCHAR(50),
    starting_balance DECIMAL(10, 2) DEFAULT 0
);

-- Target PostgreSQL Schema (Multi-tenant)
CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,  -- Added for multi-tenancy
    name VARCHAR(100) NOT NULL,
    account_number VARCHAR(50),
    starting_balance DECIMAL(10, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_accounts_user_id ON accounts(user_id);
```

### **categories**
```sql
-- Current SQLite Schema (Hierarchical with self-reference)
CREATE TABLE categories (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    parent_id INTEGER,
    type VARCHAR(20) NOT NULL,  -- 'income', 'expense', or 'transfer'
    color VARCHAR(20),
    CONSTRAINT uq_category_name_parent UNIQUE (name, parent_id),
    FOREIGN KEY(parent_id) REFERENCES categories (id)
);

-- Target PostgreSQL Schema (Multi-tenant)
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,  -- Added for multi-tenancy
    name VARCHAR(100) NOT NULL,
    parent_id INTEGER,
    type VARCHAR(20) NOT NULL CHECK (type IN ('income', 'expense', 'transfer')),
    color VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_category_name_parent_user UNIQUE (user_id, name, parent_id),
    FOREIGN KEY(parent_id) REFERENCES categories (id)
);
CREATE INDEX idx_categories_user_id ON categories(user_id);
CREATE INDEX idx_categories_parent_id ON categories(parent_id);
```

### **transactions**
```sql
-- Current SQLite Schema
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
    hash VARCHAR(64) UNIQUE,  -- SHA-256 for deduplication
    FOREIGN KEY(account_id) REFERENCES accounts (id),
    FOREIGN KEY(category_id) REFERENCES categories (id),
    FOREIGN KEY(suggested_category_id) REFERENCES categories (id)
);

-- Target PostgreSQL Schema (Multi-tenant with accrual fields)
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,  -- Added for multi-tenancy
    account_id INTEGER NOT NULL,
    date DATE NOT NULL,
    memo VARCHAR(200),
    amount DECIMAL(10, 2) NOT NULL,
    category_id INTEGER,
    suggested_category_id INTEGER,
    is_approved BOOLEAN DEFAULT FALSE,
    is_credit_card_payment BOOLEAN DEFAULT FALSE,
    hash VARCHAR(64),
    -- Accrual fields for Phase 7
    accrual_start_date DATE,
    accrual_end_date DATE,
    accrual_method VARCHAR(20),  -- 'straight-line', etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_transaction_hash_user UNIQUE (user_id, hash),
    FOREIGN KEY(account_id) REFERENCES accounts (id),
    FOREIGN KEY(category_id) REFERENCES categories (id),
    FOREIGN KEY(suggested_category_id) REFERENCES categories (id)
);
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_date ON transactions(date);
CREATE INDEX idx_transactions_account_id ON transactions(account_id);
CREATE INDEX idx_transactions_category_id ON transactions(category_id);
```

### **category_rules**
```sql
-- Current SQLite Schema
CREATE TABLE category_rules (
    id INTEGER PRIMARY KEY,
    pattern VARCHAR(200) NOT NULL,
    category_id INTEGER NOT NULL,
    priority INTEGER DEFAULT 5,
    FOREIGN KEY(category_id) REFERENCES categories (id)
);

-- Target PostgreSQL Schema (Multi-tenant)
CREATE TABLE category_rules (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,  -- Added for multi-tenancy
    pattern VARCHAR(200) NOT NULL,
    category_id INTEGER NOT NULL,
    priority INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(category_id) REFERENCES categories (id)
);
CREATE INDEX idx_category_rules_user_id ON category_rules(user_id);
CREATE INDEX idx_category_rules_priority ON category_rules(priority);
```

### **forecast_items**
```sql
-- Current SQLite Schema
CREATE TABLE forecast_items (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category_id INTEGER NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    frequency VARCHAR(20) NOT NULL,  -- 'monthly', 'quarterly', 'annual'
    type VARCHAR(20) NOT NULL,       -- 'fixed', 'variable'
    start_date DATE,
    FOREIGN KEY(category_id) REFERENCES categories (id)
);

-- Target PostgreSQL Schema (Multi-tenant)
CREATE TABLE forecast_items (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,  -- Added for multi-tenancy
    name VARCHAR(100) NOT NULL,
    category_id INTEGER NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    frequency VARCHAR(20) NOT NULL CHECK (frequency IN ('monthly', 'quarterly', 'annual')),
    type VARCHAR(20) NOT NULL CHECK (type IN ('fixed', 'variable')),
    start_date DATE,
    end_date DATE,  -- Added for better forecasting
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(category_id) REFERENCES categories (id)
);
CREATE INDEX idx_forecast_items_user_id ON forecast_items(user_id);
```

### **Row Level Security (RLS) Policies**
```sql
-- Enable RLS on all tables
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE category_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE forecast_items ENABLE ROW LEVEL SECURITY;

-- Create policies for user isolation
CREATE POLICY user_isolation_accounts ON accounts 
    FOR ALL USING (user_id = current_setting('app.user_id'));
CREATE POLICY user_isolation_categories ON categories 
    FOR ALL USING (user_id = current_setting('app.user_id'));
CREATE POLICY user_isolation_transactions ON transactions 
    FOR ALL USING (user_id = current_setting('app.user_id'));
CREATE POLICY user_isolation_category_rules ON category_rules 
    FOR ALL USING (user_id = current_setting('app.user_id'));
CREATE POLICY user_isolation_forecast_items ON forecast_items 
    FOR ALL USING (user_id = current_setting('app.user_id'));
```

---

## **Business Logic Service Migration**

### **Service: importer.py → Lambda: import-processor**
Port from `.kiro/architecture.md`:
- **CSV Parsing**: Support 3-column (Date, Description, Amount) and 4-column (Date, Description, Credit, Debit) formats
- **OFX Parsing**: Use Python `ofxparse` library
- **Date Format Detection**: Support dd/mm/yyyy, mm/dd/yyyy, yyyy-mm-dd, with day suffix
- **Hash Generation**: SHA-256 of (date, memo, amount) for deduplication
- **Credit Card Detection**: Auto-detect credit card payments

### **Service: categorizer.py → Lambda: categorizer**
Port from `.kiro/architecture.md`:
- **Pattern Matching**: Case-insensitive substring match on transaction memo
- **Priority Ordering**: Higher priority rules checked first
- **Category Suggestion**: Set suggested_category_id on transactions
- **Credit Card Payment Detection**: Flag transfers between accounts

### **Service: accrual.py → Lambda: accrual-calculator**
Future implementation for Phase 7:
- Calculate monthly accrued amounts based on accrual_method
- Support straight-line method
- Generate accrual reports

### **Service: forecast.py → Lambda: forecast-calculator**
Future implementation for Phase 8:
- Calculate projected amounts based on frequency
- Compare budget vs actual spending

---

## **Current REST API to GraphQL Mapping**

Based on `.kiro/architecture.md` REST API endpoints:

### **Accounts**
| Current REST | GraphQL Query/Mutation |
|--------------|------------------------|
| GET /api/accounts | Query: `listAccounts` |
| POST /api/accounts | Mutation: `createAccount` |
| PATCH /api/accounts/<id> | Mutation: `updateAccount` |
| DELETE /api/accounts/<id> | Mutation: `deleteAccount` |

### **Categories**
| Current REST | GraphQL Query/Mutation |
|--------------|------------------------|
| GET /api/categories | Query: `listCategories` (hierarchical) |
| POST /api/categories | Mutation: `createCategory` |
| PATCH /api/categories/<id> | Mutation: `updateCategory` |
| DELETE /api/categories/<id> | Mutation: `deleteCategory` (with validation) |

### **Category Rules**
| Current REST | GraphQL Query/Mutation |
|--------------|------------------------|
| GET /api/category-rules | Query: `listCategoryRules` |
| POST /api/category-rules | Mutation: `createCategoryRule` |
| PATCH /api/category-rules/<id> | Mutation: `updateCategoryRule` |
| DELETE /api/category-rules/<id> | Mutation: `deleteCategoryRule` |

### **Transactions**
| Current REST | GraphQL Query/Mutation |
|--------------|------------------------|
| GET /api/transactions | Query: `listTransactions` (with filters) |
| PATCH /api/transactions/<id> | Mutation: `updateTransaction` |
| N/A | Mutation: `approveTransactions` (bulk) |
| N/A | Mutation: `bulkUpdateTransactions` |

### **Forecast**
| Current REST | GraphQL Query/Mutation |
|--------------|------------------------|
| GET /api/forecast | Query: `listForecastItems` |
| POST /api/forecast | Mutation: `createForecastItem` |
| PATCH /api/forecast/<id> | Mutation: `updateForecastItem` |
| DELETE /api/forecast/<id> | Mutation: `deleteForecastItem` |

### **Import**
| Current REST | GraphQL/Lambda |
|--------------|----------------|
| POST /api/import | Mutation: `requestUploadUrl` → S3 Upload → Lambda trigger |

---

## **Frontend Component Mapping**

Based on `.kiro/architecture.md` current frontend:

| Current Template | Vue.js Component |
|------------------|------------------|
| transactions.html | TransactionsList.vue, TransactionEdit.vue |
| config.html | AccountsList.vue, CategoriesList.vue, CategoryRulesList.vue, ForecastList.vue |
| dashboard.html | Dashboard.vue (Chart.js → vue-chartjs) |
| cashflow.html | CashFlowReport.vue |
| accrual.html | AccrualReport.vue |

### **UI Features to Preserve**
From `.kiro/architecture.md`:
- **Dual dropdown system**: Category → Subcategory (cascading dropdowns)
- **Text-based category editor**: Separate text areas for income vs expense
- **Bulk operations**: Approve multiple transactions, bulk categorize
- **Filtering**: By date, account, category, status
- **Checkbox selection**: For bulk actions

---

## **Development Standards Alignment**

Based on `.kiro/rules.md` and `.kiro/development_guide.md`:

### **Backend Standards (Applied to Lambda)**
- Use minimal, focused implementations
- Follow PEP 8 naming conventions
- Use type hints where helpful
- Keep functions small and single-purpose
- Return data structures, not Flask responses → Return JSON for Lambda responses

### **Testing Strategy**
- Unit tests for Lambda functions (port existing test patterns)
- Integration tests for AppSync API
- End-to-end tests for complete flows
- Test deduplication logic
- Test categorization rules
- Verify database constraints

### **Error Handling**
- Return appropriate HTTP status codes (200, 201, 400, 404)
- Include error messages in responses
- Log errors with context for debugging
- Validate inputs before processing

---

## **Risk Assessment and Mitigation**

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| GraphQL learning curve | Medium | High | Use Amplify libraries, follow AWS examples |
| RLS configuration errors | High | Medium | Thorough testing, multiple test users |
| Lambda cold starts | Low | High | Keep Lambdas warm, optimize package size |
| File import failures | Medium | Medium | Implement retry logic, store status in DynamoDB |
| Cost overruns | Medium | Low | Use reserved capacity, monitor with CloudWatch |
| Data isolation breach | High | Low | RLS policies, code reviews, security testing |

---

## **Timeline Estimates**

### **Phase 1: Foundation (Weeks 1-2)**
- Tasks 1-4: AWS Infrastructure, Database Schema, Cognito, AppSync Foundation

### **Phase 2: Core API (Weeks 3-4)**
- Tasks 5-11: Resolvers, CRUD Operations, S3 Upload, Import Processing

### **Phase 3: Vue.js Frontend (Weeks 5-7)**
- Tasks 12-20: Project Setup, Auth UI, All Management Screens

### **Phase 4: Reports & Dashboard (Weeks 8-9)**
- Tasks 21-24: Dashboard, Cash Flow, Accrual, Budget vs Actual

### **Phase 5: Production Readiness (Weeks 10-12)**
- Tasks 25-30: CloudFront, Monitoring, Security, CI/CD, Documentation

**Total Estimated Duration**: 12 weeks

---

## **Cost Estimation Framework**

### **Monthly AWS Costs (Development)**
- RDS db.t3.micro: ~$15/month
- Lambda (free tier eligible): ~$0-5/month
- AppSync: ~$4/million requests
- S3: ~$0.023/GB
- CloudFront: ~$0.085/GB transfer
- Cognito: Free for first 50k MAUs
- CloudWatch: ~$5/month

**Estimated Dev Environment**: $25-50/month

### **Monthly AWS Costs (Production)**
- RDS db.t3.small: ~$30/month
- Lambda: ~$5-20/month
- AppSync: ~$20-50/month (based on usage)
- S3: ~$5/month
- CloudFront: ~$10-50/month
- Cognito: Free for first 50k MAUs
- CloudWatch: ~$10/month
- WAF: ~$5/month

**Estimated Production**: $100-200/month (scales with usage)

---

Key Design Decisions:
1. AppSync with hybrid resolvers: Direct RDS for simple queries (performance), Lambda for complex
business logic
2. Multi-tenancy via Cognito: User ID from JWT automatically injected into all queries via AppSync
pipeline resolvers
3. S3 presigned URLs: Frontend requests upload URL from Lambda, uploads directly to S3, triggers
processing Lambda
4. PostgreSQL schema: Add user_id column to all tables with RLS (Row Level Security) policies
5. Vue.js composition API: Modern, maintainable frontend with Pinia for state management

### **Proposed Solution:**

Build the AWS infrastructure and application in incremental phases, ensuring each phase is testable
and deployable:

1. Foundation: Set up AWS infrastructure (SAM, RDS, Cognito, AppSync schema)
2. Authentication: Implement Cognito user pools and Vue.js auth flow
3. Core API: Build AppSync schema and resolvers for CRUD operations
4. File Import: Implement S3 upload flow and Lambda processing
5. Business Logic: Port categorization, accrual, and forecast services
6. Frontend: Build Vue.js components for all screens
7. Dashboard: Implement charts and visualizations
8. Production: Add monitoring, error handling, and deployment pipeline

### **Task Breakdown:**

Task 1: AWS Infrastructure Foundation
Set up the base AWS infrastructure using SAM template including VPC, RDS PostgreSQL, and basic
networking.

Implementation:
- Create SAM template (template.yaml) with VPC, subnets, security groups
- Define RDS PostgreSQL instance (db.t3.micro for dev, configurable for prod)
- Create Secrets Manager secret for database credentials
- Add SSM parameters for configuration values
- Include outputs for connection strings and resource ARNs

Tests:
- Deploy stack successfully
- Verify RDS instance is accessible from Lambda (test connection)
- Confirm secrets are retrievable

Demo: Successfully deployed AWS infrastructure with accessible PostgreSQL database

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


Task 2: Database Schema with Multi-Tenancy
Create PostgreSQL schema with user_id columns and Row Level Security policies for data isolation.

Implementation:
- Create SQL migration script with all tables (accounts, categories, transactions, category_rules,
forecast_items)
- Add user_id VARCHAR(255) column to all tables (indexed)
- Add composite unique constraints including user_id where needed
- Create RLS policies:
CREATE POLICY user_isolation ON accounts FOR ALL USING (user_id = current_setting('app.user_id'))
- Create Lambda function to run migrations on deployment
- Add database initialization with default categories per user

Tests:
- Run migration successfully
- Verify RLS policies block cross-user queries
- Test default category creation

Demo: Database schema deployed with working RLS policies preventing cross-user data access

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


Task 3: Amazon Cognito User Pool
Set up Cognito for user authentication with email/password sign-up.

Implementation:
- Add Cognito User Pool to SAM template
- Configure password policy, MFA optional, email verification
- Create User Pool Client for Vue.js app (no client secret for SPA)
- Add Cognito Identity Pool for AWS credentials (if needed)
- Configure custom attributes if needed
- Output User Pool ID and Client ID

Tests:
- Create test user via AWS CLI
- Verify email verification flow
- Confirm JWT token generation

Demo: Working Cognito user pool with ability to create users and generate JWT tokens

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


Task 4: AppSync GraphQL API Foundation
Create AppSync API with GraphQL schema for all entities and basic resolvers.

Implementation:
- Add AppSync GraphQL API to SAM template
- Define GraphQL schema with types: Account, Category, Transaction, CategoryRule, ForecastItem
- Add Query type: listAccounts, getAccount, listCategories, listTransactions (with filters), etc.
- Add Mutation type: createAccount, updateAccount, deleteAccount, etc.
- Configure Cognito as authorization provider
- Create RDS data source with connection to PostgreSQL
- Add Lambda data source for complex operations

Tests:
- Deploy AppSync API
- Verify schema is valid
- Test authentication with Cognito JWT

Demo: AppSync API deployed with complete GraphQL schema and authentication

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


Task 5: AppSync Pipeline Resolvers with User Context
Implement pipeline resolvers that inject user_id from Cognito JWT into all database operations.

Implementation:
- Create pipeline resolver functions in VTL (Velocity Template Language)
- Before step: Extract sub (user_id) from $ctx.identity.claims
- Set PostgreSQL session variable: SET LOCAL app.user_id = '<user_id>'
- Create direct RDS resolvers for simple queries (listAccounts, getAccount)
- Use prepared statements with user_id parameter
- Add pagination support (limit, offset)

Tests:
- Query data as different users, verify isolation
- Test pagination
- Verify RLS policies are enforced

Demo: Working queries that automatically filter data by authenticated user

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


Task 6: CRUD Mutations for Core Entities
Implement create, update, delete mutations for accounts, categories, and category rules.

Implementation:
- Create Lambda function for mutation business logic (mutations-handler)
- Implement handlers: createAccount, updateAccount, deleteAccount
- Implement handlers: createCategory, updateCategory, deleteCategory (check for subcategories)
- Implement handlers: createCategoryRule, updateCategoryRule, deleteCategoryRule
- Add user_id injection in all INSERT statements
- Add validation logic (e.g., prevent deleting category with transactions)
- Return proper error messages

Tests:
- Create, update, delete each entity type
- Verify user_id is set correctly
- Test validation rules (e.g., can't delete category in use)

Demo: Full CRUD operations working for accounts, categories, and rules with proper validation

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


Task 7: S3 Upload Infrastructure
Set up S3 bucket and Lambda function to generate presigned URLs for file uploads.

Implementation:
- Add S3 bucket to SAM template with encryption, versioning, lifecycle policies
- Create Lambda function generate-upload-url
- Accept parameters: filename, content-type
- Generate presigned POST URL with 15-minute expiration
- Include metadata: user_id, upload timestamp
- Configure S3 event notification to trigger processing Lambda
- Add CORS configuration for Vue.js origin

Tests:
- Generate presigned URL
- Upload file using presigned URL
- Verify S3 event triggers

Demo: Working presigned URL generation and file upload to S3

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


Task 8: File Import Processing Lambda
Create Lambda function to process CSV/OFX files from S3 and import transactions.

Implementation:
- Create Lambda function import-processor triggered by S3 events
- Port CSV parsing logic (3-col and 4-col detection)
- Port OFX parsing logic using Python ofxparse library
- Extract user_id from S3 object metadata
- Generate transaction hash for deduplication
- Insert transactions with user_id
- Apply categorization suggestions (call categorizer)
- Store import results/errors in DynamoDB table for status tracking
- Send notification on completion (optional: SNS/SES)

Tests:
- Upload CSV file, verify transactions imported
- Upload OFX file, verify transactions imported
- Test duplicate detection
- Verify user_id isolation

Demo: End-to-end file upload and transaction import with deduplication

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


Task 9: Categorization Service
Port the categorization logic to Lambda for auto-suggesting categories.

Implementation:
- Create Lambda function categorizer (or integrate into import-processor)
- Port pattern matching logic from categorizer.py
- Query category_rules for user, ordered by priority
- Detect credit card payments
- Update transactions with suggested_category_id and suggested_subcategory_id
- Add mutation: applyCategorySuggestions to approve suggestions in bulk

Tests:
- Create category rule, import transactions, verify suggestions
- Test credit card payment detection
- Test bulk approval

Demo: Automatic category suggestions working based on user-defined rules

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


Task 10: Transaction Mutations
Implement transaction-specific mutations including approval and bulk operations.

Implementation:
- Add mutations: updateTransaction, deleteTransaction
- Add mutation: approveTransactions (bulk, accepts array of IDs)
- Add mutation: bulkUpdateTransactions (update category for multiple)
- Validate user owns transactions before updating
- Update is_approved flag
- Handle accrual fields (accrual_start_date, accrual_end_date, accrual_method)

Tests:
- Update single transaction
- Approve multiple transactions
- Bulk update categories
- Verify user isolation

Demo: Transaction management with bulk operations working

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


Task 11: Forecast CRUD Operations
Implement forecast item management for budget planning.

Implementation:
- Add mutations: createForecastItem, updateForecastItem, deleteForecastItem
- Add query: listForecastItems (filter by date range, category)
- Validate frequency values (monthly, annual, quarterly)
- Validate type values (fixed, variable)
- Include user_id in all operations

Tests:
- Create forecast items with different frequencies
- Query and filter forecast items
- Update and delete forecast items

Demo: Complete forecast management functionality

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


Task 12: Vue.js Project Setup
Initialize Vue.js 3 project with routing, state management, and AWS Amplify libraries.

Implementation:
- Create Vue 3 project with Vite
- Install dependencies: vue-router, pinia, @aws-amplify/ui-vue, aws-amplify, chart.js, vue-chartjs
- Configure Amplify with Cognito and AppSync endpoints
- Set up Pinia stores: auth, accounts, categories, transactions, forecast
- Configure Vue Router with auth guards
- Create base layout component with navigation
- Add Tailwind CSS or Vuetify for UI components

Tests:
- Run dev server
- Verify routing works
- Test Amplify configuration

Demo: Vue.js app running with navigation and Amplify configured

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


Task 13: Authentication UI
Build login, signup, and password reset flows using Amplify UI components.

Implementation:
- Create Login.vue component with Amplify Authenticator
- Create auth store with Pinia (login, logout, getCurrentUser)
- Add auth guards to router (redirect to login if not authenticated)
- Store JWT token and user info in store
- Add logout functionality
- Handle token refresh automatically via Amplify

Tests:
- Sign up new user
- Login with credentials
- Verify protected routes redirect
- Test logout

Demo: Complete authentication flow with protected routes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


Task 14: Accounts Management UI
Build Vue components for managing accounts (list, create, edit, delete).

Implementation:
- Create AccountsList.vue component
- Create AccountForm.vue component (create/edit modal)
- Implement GraphQL queries/mutations using Amplify API
- Add account store in Pinia
- Display starting balance and date
- Add delete confirmation dialog
- Show transaction count per account

Tests:
- Create new account
- Edit account details
- Delete account (verify validation)
- List all accounts

Demo: Full account management interface working

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


Task 15: Categories Management UI
Build hierarchical category management with parent/subcategory support.

Implementation:
- Create CategoriesList.vue component with tree view
- Create CategoryForm.vue component
- Support parent category selection
- Add color picker for category colors
- Implement drag-and-drop reordering (optional)
- Add category type filter (income/expense/transfer)
- Show transaction count per category

Tests:
- Create parent category
- Create subcategory
- Edit category
- Delete category (verify validation)

Demo: Hierarchical category management with visual tree structure

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


Task 16: Category Rules Management UI
Build interface for creating and managing auto-categorization rules.

Implementation:
- Create CategoryRulesList.vue component
- Create CategoryRuleForm.vue component
- Add pattern input with examples
- Add priority slider/input
- Support category and subcategory selection
- Show rule matching preview (test against sample text)
- Add reorder functionality by priority

Tests:
- Create categorization rule
- Edit rule priority
- Delete rule
- Test pattern matching

Demo: Category rules management with pattern testing

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


Task 17: File Import UI
Build file upload interface with progress tracking and import results.

Implementation:
- Create ImportTransactions.vue component
- Add file picker (CSV/OFX)
- Request presigned URL from Lambda
- Upload file directly to S3 with progress bar
- Poll import status from DynamoDB (or use AppSync subscription)
- Display import results: success count, duplicates, errors
- Show imported transactions preview

Tests:
- Upload CSV file
- Upload OFX file
- View import progress
- See import results

Demo: File upload with real-time progress and results display

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


Task 18: Transactions List UI
Build main transactions view with filtering, sorting, and bulk operations.

Implementation:
- Create TransactionsList.vue component
- Add filters: date range, account, category, approval status
- Implement pagination (load more or infinite scroll)
- Add sorting by date, amount
- Show category suggestions with approve button
- Implement bulk selection with checkboxes
- Add bulk approve and bulk categorize actions
- Display transaction details in expandable rows

Tests:
- Filter transactions by date range
- Filter by account and category
- Approve single transaction
- Bulk approve multiple transactions
- Bulk update categories

Demo: Full-featured transaction management interface

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


Task 19: Transaction Edit UI
Build transaction detail/edit modal with category selection and accrual settings.

Implementation:
- Create TransactionEdit.vue component (modal)
- Add category and subcategory dropdowns
- Add accrual method selection (straight-line, etc.)
- Add accrual date range pickers
- Show suggested categories
- Add memo editing
- Add amount editing (with validation)
- Show transaction hash and duplicate info

Tests:
- Edit transaction category
- Set accrual dates
- Update memo and amount
- Apply suggested category

Demo: Transaction editing with all fields functional

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


Task 20: Forecast Management UI
Build budget forecast interface with frequency and type selection.

Implementation:
- Create ForecastList.vue component
- Create ForecastForm.vue component
- Add frequency selector (monthly, quarterly, annual)
- Add type selector (fixed, variable)
- Add date range pickers
- Show projected amounts over time
- Add category selection
- Calculate totals by category and frequency

Tests:
- Create forecast item
- Edit forecast item
- Delete forecast item
- View forecast projections

Demo: Budget forecast management with projections

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


Task 21: Dashboard with Charts
Build dashboard with summary cards and Chart.js visualizations.

Implementation:
- Create Dashboard.vue component
- Add summary cards: total income, total expenses, net flow, average monthly
- Create category spending pie chart
- Create monthly trend line chart
- Create expense breakdown bar chart
- Add date range filter for dashboard
- Implement GraphQL queries for aggregated data
- Add loading states and empty states

Tests:
- View dashboard with data
- Filter by date range
- Verify chart calculations
- Test with no data

Demo: Interactive dashboard with charts and summary metrics

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


Task 22: Reports - Cash Flow
Build cash flow report showing income and expenses over time.

Implementation:
- Create CashFlowReport.vue component
- Add date range selector
- Query approved transactions grouped by month
- Calculate income, expenses, net flow per month
- Display as table and chart
- Add account filter
- Add category breakdown
- Export to CSV functionality

Tests:
- Generate cash flow report
- Filter by date range
- Filter by account
- Export to CSV

Demo: Cash flow report with monthly breakdown and export

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


Task 23: Reports - Accrual Method
Build accrual report showing expenses spread over time periods.

Implementation:
- Create AccrualReport.vue component
- Port accrual calculation logic to Lambda or frontend
- Query transactions with accrual settings
- Calculate monthly accrued amounts
- Display accrued vs cash basis comparison
- Add visualization showing accrual spreading
- Add filters for date range and categories

Tests:
- View accrual report
- Compare cash vs accrual basis
- Verify accrual calculations
- Filter by category

Demo: Accrual report showing expense spreading over time

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


Task 24: Budget vs Actual Comparison
Build report comparing forecast budget to actual spending.

Implementation:
- Create BudgetVsActualReport.vue component
- Query forecast items for selected period
- Query actual transactions for same period
- Calculate variance (budget - actual)
- Display as table with variance highlighting
- Add category-level breakdown
- Show percentage of budget used
- Add visual indicators (over/under budget)

Tests:
- Generate budget vs actual report
- View variance by category
- Filter by date range
- Verify calculations

Demo: Budget comparison report with variance analysis

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


Task 25: CloudFront Distribution & Deployment
Set up S3 bucket and CloudFront distribution for Vue.js app hosting.

Implementation:
- Add S3 bucket for static hosting to SAM template
- Configure bucket policy for CloudFront access
- Create CloudFront distribution with S3 origin
- Configure custom error responses (SPA routing)
- Add SSL certificate (ACM) for custom domain (optional)
- Create deployment script to build and upload Vue.js app
- Add cache invalidation after deployment
- Configure CORS for API calls

Tests:
- Deploy Vue.js build to S3
- Access via CloudFront URL
- Verify SPA routing works
- Test API calls from hosted app

Demo: Production-ready Vue.js app accessible via CloudFront

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


Task 26: Monitoring & Logging
Add CloudWatch dashboards, alarms, and structured logging.

Implementation:
- Add CloudWatch Log Groups for all Lambdas
- Configure log retention (30 days)
- Add structured logging to Lambda functions (JSON format)
- Create CloudWatch dashboard with key metrics: API latency, error rates, Lambda duration
- Add alarms: high error rate, RDS CPU, Lambda throttling
- Configure X-Ray tracing for AppSync and Lambda
- Add SNS topic for alarm notifications

Tests:
- Trigger errors, verify logs
- View CloudWatch dashboard
- Test alarm notifications
- View X-Ray traces

Demo: Comprehensive monitoring with dashboards and alarms

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


Task 27: Error Handling & Validation
Add comprehensive error handling and input validation across the stack.

Implementation:
- Add GraphQL input validation in AppSync resolvers
- Add Lambda error handling with proper HTTP status codes
- Create custom error types in GraphQL schema
- Add frontend error handling with user-friendly messages
- Add form validation in Vue components
- Add retry logic for transient failures
- Log errors with context for debugging
- Add error boundary components in Vue

Tests:
- Test invalid inputs
- Test network failures
- Test permission errors
- Verify error messages are user-friendly

Demo: Robust error handling with clear user feedback

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


Task 28: CI/CD Pipeline
Set up automated deployment pipeline using GitHub Actions or AWS CodePipeline.

Implementation:
- Create GitHub Actions workflow (or CodePipeline)
- Add stages: test, build, deploy
- Run unit tests for Lambda functions
- Build Vue.js app
- Deploy SAM stack to dev environment
- Deploy Vue.js to S3 and invalidate CloudFront
- Add manual approval for production deployment
- Add rollback capability
- Store secrets in GitHub Secrets or Secrets Manager

Tests:
- Trigger pipeline with commit
- Verify automated deployment
- Test rollback
- Verify production approval gate

Demo: Automated CI/CD pipeline deploying to AWS

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


Task 29: Security Hardening
Implement security best practices across the application.

Implementation:
- Enable RDS encryption at rest
- Enable S3 bucket encryption
- Add WAF rules to CloudFront (rate limiting, geo-blocking)
- Configure least-privilege IAM roles for Lambdas
- Add API rate limiting in AppSync
- Enable VPC endpoints for Lambda-RDS communication
- Add secrets rotation for RDS credentials
- Configure security headers in CloudFront
- Add input sanitization for SQL injection prevention
- Enable MFA for Cognito (optional)

Tests:
- Verify encryption enabled
- Test rate limiting
- Verify IAM permissions are minimal
- Test SQL injection attempts

Demo: Hardened security configuration meeting production standards

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


Task 30: Documentation & Deployment Guide
Create comprehensive documentation for deployment and usage.

Implementation:
- Create README.md with architecture overview
- Document SAM template parameters
- Create deployment guide with prerequisites
- Document environment variables and configuration
- Create API documentation (GraphQL schema docs)
- Add troubleshooting guide
- Document cost estimates
- Create user guide for Vue.js app
- Add inline code comments
- Create architecture diagrams

Tests:
- Follow deployment guide on fresh AWS account
- Verify all steps work
- Test troubleshooting procedures

Demo: Complete documentation enabling independent deployment

---

## **GraphQL Schema Definition**

Based on the current data models from `.kiro/database_schema.md`:

```graphql
# Types
type Account {
  id: ID!
  name: String!
  accountNumber: String
  startingBalance: Float
  transactionCount: Int
  createdAt: AWSDateTime
  updatedAt: AWSDateTime
}

type Category {
  id: ID!
  name: String!
  parentId: ID
  parent: Category
  subcategories: [Category]
  type: CategoryType!
  color: String
  transactionCount: Int
  createdAt: AWSDateTime
  updatedAt: AWSDateTime
}

enum CategoryType {
  income
  expense
  transfer
}

type Transaction {
  id: ID!
  accountId: ID!
  account: Account
  date: AWSDate!
  memo: String
  amount: Float!
  categoryId: ID
  category: Category
  suggestedCategoryId: ID
  suggestedCategory: Category
  isApproved: Boolean
  isCreditCardPayment: Boolean
  hash: String
  accrualStartDate: AWSDate
  accrualEndDate: AWSDate
  accrualMethod: String
  createdAt: AWSDateTime
  updatedAt: AWSDateTime
}

type CategoryRule {
  id: ID!
  pattern: String!
  categoryId: ID!
  category: Category
  priority: Int
  createdAt: AWSDateTime
  updatedAt: AWSDateTime
}

type ForecastItem {
  id: ID!
  name: String!
  categoryId: ID!
  category: Category
  amount: Float!
  frequency: Frequency!
  type: ForecastType!
  startDate: AWSDate
  endDate: AWSDate
  createdAt: AWSDateTime
  updatedAt: AWSDateTime
}

enum Frequency {
  monthly
  quarterly
  annual
}

enum ForecastType {
  fixed
  variable
}

type ImportResult {
  success: Boolean!
  importedCount: Int
  duplicateCount: Int
  errorCount: Int
  errors: [String]
}

type UploadUrl {
  url: String!
  key: String!
  expiresAt: AWSDateTime!
}

# Inputs
input AccountInput {
  name: String!
  accountNumber: String
  startingBalance: Float
}

input CategoryInput {
  name: String!
  parentId: ID
  type: CategoryType!
  color: String
}

input TransactionFilter {
  accountId: ID
  categoryId: ID
  fromDate: AWSDate
  toDate: AWSDate
  isApproved: Boolean
  excludeCCPayments: Boolean
}

input TransactionUpdateInput {
  categoryId: ID
  isApproved: Boolean
  memo: String
  accrualStartDate: AWSDate
  accrualEndDate: AWSDate
  accrualMethod: String
}

input CategoryRuleInput {
  pattern: String!
  categoryId: ID!
  priority: Int
}

input ForecastItemInput {
  name: String!
  categoryId: ID!
  amount: Float!
  frequency: Frequency!
  type: ForecastType!
  startDate: AWSDate
  endDate: AWSDate
}

# Queries
type Query {
  # Accounts
  listAccounts: [Account]
  getAccount(id: ID!): Account
  
  # Categories (returns hierarchical structure)
  listCategories(type: CategoryType): [Category]
  getCategory(id: ID!): Category
  
  # Transactions (with pagination and filtering)
  listTransactions(filter: TransactionFilter, limit: Int, offset: Int): [Transaction]
  getTransaction(id: ID!): Transaction
  
  # Category Rules
  listCategoryRules: [CategoryRule]
  getCategoryRule(id: ID!): CategoryRule
  
  # Forecast Items
  listForecastItems(categoryId: ID, fromDate: AWSDate, toDate: AWSDate): [ForecastItem]
  getForecastItem(id: ID!): ForecastItem
  
  # Reports
  getDashboardSummary(fromDate: AWSDate!, toDate: AWSDate!): DashboardSummary
  getCashFlowReport(fromDate: AWSDate!, toDate: AWSDate!, accountId: ID): CashFlowReport
  getAccrualReport(fromDate: AWSDate!, toDate: AWSDate!): AccrualReport
  getBudgetVsActual(fromDate: AWSDate!, toDate: AWSDate!): BudgetVsActualReport
}

# Mutations
type Mutation {
  # Accounts
  createAccount(input: AccountInput!): Account
  updateAccount(id: ID!, input: AccountInput!): Account
  deleteAccount(id: ID!): Boolean
  
  # Categories
  createCategory(input: CategoryInput!): Category
  updateCategory(id: ID!, input: CategoryInput!): Category
  deleteCategory(id: ID!): Boolean
  
  # Transactions
  updateTransaction(id: ID!, input: TransactionUpdateInput!): Transaction
  deleteTransaction(id: ID!): Boolean
  approveTransactions(ids: [ID]!): [Transaction]
  bulkUpdateTransactions(ids: [ID]!, categoryId: ID!): [Transaction]
  
  # Category Rules
  createCategoryRule(input: CategoryRuleInput!): CategoryRule
  updateCategoryRule(id: ID!, input: CategoryRuleInput!): CategoryRule
  deleteCategoryRule(id: ID!): Boolean
  
  # Forecast Items
  createForecastItem(input: ForecastItemInput!): ForecastItem
  updateForecastItem(id: ID!, input: ForecastItemInput!): ForecastItem
  deleteForecastItem(id: ID!): Boolean
  
  # File Import
  requestUploadUrl(filename: String!, contentType: String!): UploadUrl
  applyCategorySuggestions(transactionIds: [ID]!): [Transaction]
}

# Report Types
type DashboardSummary {
  totalIncome: Float!
  totalExpenses: Float!
  netFlow: Float!
  averageMonthly: Float!
  categoryBreakdown: [CategoryAmount]
  monthlyTrends: [MonthlyTrend]
}

type CategoryAmount {
  categoryId: ID!
  categoryName: String!
  amount: Float!
  percentage: Float!
}

type MonthlyTrend {
  month: String!
  income: Float!
  expenses: Float!
  netFlow: Float!
}

type CashFlowReport {
  months: [MonthlyCashFlow]
  totalIncome: Float!
  totalExpenses: Float!
  netFlow: Float!
}

type MonthlyCashFlow {
  month: String!
  income: Float!
  expenses: Float!
  netFlow: Float!
  categoryBreakdown: [CategoryAmount]
}

type AccrualReport {
  cashBasis: [MonthlyAmount]
  accrualBasis: [MonthlyAmount]
  variance: [MonthlyAmount]
}

type MonthlyAmount {
  month: String!
  amount: Float!
}

type BudgetVsActualReport {
  items: [BudgetVsActualItem]
  totalBudget: Float!
  totalActual: Float!
  totalVariance: Float!
}

type BudgetVsActualItem {
  categoryId: ID!
  categoryName: String!
  budget: Float!
  actual: Float!
  variance: Float!
  percentUsed: Float!
}
```

---

## **Rollback and Contingency Plan**

### **Pre-Migration Checklist**
- [ ] All stakeholders informed of migration timeline
- [ ] Current Flask application fully documented
- [ ] All test scripts passing
- [ ] Backup procedures in place

### **Rollback Triggers**
- Critical data loss or corruption
- Security breach detected
- >50% of functionality broken post-deployment
- Performance degradation >5x baseline

### **Rollback Procedures**

#### **Phase 1-4 (Infrastructure/API)**
- Delete CloudFormation/SAM stack
- Verify RDS data is removed (no data migration, fresh start)
- Continue using existing Flask application

#### **Phase 5+ (Frontend Migration)**
- Revert CloudFront distribution to serve Flask templates
- Keep Flask backend running as fallback
- Gradual rollout with feature flags

### **Contingency Options**

| Scenario | Contingency |
|----------|-------------|
| AppSync performance issues | Fall back to API Gateway + Lambda REST API |
| RDS cost too high | Consider Aurora Serverless v2 or DynamoDB |
| Cognito integration complex | Consider Auth0 or Firebase Auth |
| Vue.js team capacity | Continue with server-rendered templates |
| Timeline overrun | Prioritize core features (Phases 1-4, Tasks 1-18) |

### **Feature Parity Checklist**
Before full cutover, verify:
- [ ] Account CRUD operations
- [ ] Category hierarchical management
- [ ] Transaction import (CSV 3-col, 4-col, OFX)
- [ ] Hash-based deduplication
- [ ] Auto-categorization with rules
- [ ] Credit card payment detection
- [ ] Bulk approval workflow
- [ ] Dashboard visualizations
- [ ] Cash flow reports
- [ ] User data isolation (multi-tenancy)

---

## **Success Criteria**

### **Functional Requirements**
- All 5 entity types (Account, Category, Transaction, CategoryRule, ForecastItem) fully operational
- File import processing complete within 30 seconds for 1000 transactions
- All current UI features replicated in Vue.js
- Multi-tenant data isolation verified

### **Non-Functional Requirements**
- API response time < 500ms (p95)
- System availability > 99.9%
- Security audit passed
- Cost within budget estimates

### **User Acceptance**
- Existing workflows preserved
- No data entry regressions
- Dashboard loads within 2 seconds
- File uploads work reliably

---

## **Appendix: File Formats Supported**

Based on `.kiro/technical_context.md`:

### **CSV 3-Column Format**
```csv
Date,Description,Amount
01/15/2026,GROCERY STORE,-45.67
01/16/2026,SALARY DEPOSIT,3500.00
```
- Negative amounts = expenses
- Positive amounts = income

### **CSV 4-Column Format**
```csv
Date,Description,Credit,Debit
01/15/2026,GROCERY STORE,,45.67
01/16/2026,SALARY DEPOSIT,3500.00,
```
- Credit column = income
- Debit column = expenses

### **Date Formats Supported**
- `dd/mm/yyyy` (e.g., 15/01/2026)
- `mm/dd/yyyy` (e.g., 01/15/2026)
- `yyyy-mm-dd` (e.g., 2026-01-15)
- With day suffix: `20/11/2018 TUE`

### **OFX Format**
- Standard Open Financial Exchange format
- Parsed using Python `ofxparse` library
- Automatically extracts transactions from bank exports
