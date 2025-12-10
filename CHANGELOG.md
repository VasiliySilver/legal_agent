## Unreleased

### Feat

- **notebooks**: #6 - update research notebook
- **notebooks**: #6 - add data generation and parsing notebooks
- **scripts**: #6 - add utility scripts for project management
- **api**: #6 - add REST API endpoints and documentation
- **use_cases**: #5 - add tests for answer legal question, manage conversation and search articles use cases
- **use_cases**: #5 - add tests LLMService and VectorService
- **tests**: #5 - update conftest.py - add configure proxy feature for groq api
- **services**: #5 - update llm service for extracting article numbers
- **use_cases**: #4 - add use cases for conversation, search and question answer
- **entities**: #4 - update entitites.py - add new fields, update test_domain for new fields
- **docker**: #3 - update pgvector setup documentation
- **dependencies**: #3 - add asyncpg
- **use_cases**: #3 - add use cases for legal agent
- **services**: #3 - add VectorService for vector search for articles according to the laws  of the Labor Code
- **services**: #3 - add LLMService for answers generation about legal answers
- **tests**: #3 - add tests for services, add use cases tests
- **docker**: #3 - add pgvector, update documents for docker, add PGVECTOR_SETUP.md
- **#2**: add .vscode
- **#2**: add init for src
- **#2**: add database models and repositories
- **#2**: implement domain entities and business logic
- **#2**: add docker comfiguration with postgressql setup
- **#2**: add unit tests for domain and infrastructure layers
- **#1**: update project dependencies and Python version
- **#1**: add research for legal agent by russian laws, update dependencies
- init project

### Fix

- **linting**: #7 - fix linter errors
- **linting**: #7 - fix linter errors (bare except, unused variables, import order)

### Refactor

- **core**: #6 - update use cases, services, domain models
