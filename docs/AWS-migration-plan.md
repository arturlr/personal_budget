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

Current Architecture:
- Flask monolith with SQLAlchemy ORM
- SQLite database (single-tenant)
- Server-side rendered HTML templates
- Direct file uploads to Flask endpoint
- 5 main entities: Account, Category, Transaction, CategoryRule, ForecastItem
- Business logic in services: importer, categorizer, accrual, forecast

Target AWS Architecture:
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
