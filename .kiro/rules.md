# Development Rules for Personal Budget App

## Code Standards

### Python/Flask
- Use minimal, focused implementations
- Avoid verbose code that doesn't directly contribute to the solution
- Follow PEP 8 naming conventions
- Use type hints where helpful
- Keep functions small and single-purpose

### Database
- Always use SQLAlchemy ORM (no raw SQL unless necessary)
- Create migrations for schema changes: `flask db migrate -m "description"`
- Apply migrations: `flask db upgrade`
- Test migrations before committing

### API Design
- RESTful endpoints with proper HTTP methods
- Return JSON responses
- Use appropriate status codes (200, 201, 400, 404)
- Include error messages in responses
- Support filtering via query parameters

### Services
- Business logic goes in services/ directory
- Keep services stateless
- Services should not directly handle HTTP requests
- Return data structures, not Flask responses

## Testing Requirements

### Before Committing
- Run phase test script: `python test_phase2.py`
- Verify API endpoints work
- Test with sample data files

### Test Coverage
- Test happy path and edge cases
- Test deduplication logic
- Test categorization rules
- Verify database constraints

## File Organization

### Backend Structure
```
backend/
├── app.py              # Flask app + API routes
├── models.py           # Database models only
├── services/           # Business logic
│   ├── importer.py
│   ├── categorizer.py
│   ├── accrual.py
│   └── forecast.py
├── test_*.py           # Test scripts
└── test_data/          # Sample files
```

### Documentation
- Update phase completion docs after each phase
- Keep implementation_plan.md as reference
- Document API changes in phase docs

## Development Workflow

### Starting a New Phase
1. Read phase requirements from implementation_plan.md
2. Identify minimal implementation needed
3. Write code
4. Create test script
5. Verify functionality
6. Document completion

### Making Changes
1. Create migration if schema changes
2. Update affected services
3. Update API endpoints if needed
4. Test changes
5. Update documentation

## Common Patterns

### Adding a New Model
1. Define in models.py
2. Create migration: `flask db migrate -m "Add ModelName"`
3. Apply: `flask db upgrade`
4. Add API endpoints in app.py
5. Test CRUD operations

### Adding a New Service
1. Create file in services/
2. Import in app.py
3. Use in API endpoints
4. Add tests

### Adding API Endpoint
1. Define route in app.py
2. Use appropriate HTTP method
3. Validate input
4. Call service layer
5. Return JSON response
6. Test with curl

## Don't Do This
- ❌ Don't add unnecessary dependencies
- ❌ Don't write verbose implementations
- ❌ Don't skip migrations for schema changes
- ❌ Don't put business logic in app.py routes
- ❌ Don't commit without testing
- ❌ Don't add features not in the current phase
