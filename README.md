# CallFairy — Django Multi-Tenant Permission System

CallFairy is a Django-based backend for a voice-AI platform with a multi-tenant RBAC (role-based access control) system. It provides user, organisation and agent management, fine-grained permissions, REST APIs, Celery tasks for async processing, and comprehensive documentation and tests.

## Highlights
- Multi-tenant organisations with 1:1 agent → organisation mapping
- 3 roles: SuperAdmin, Agent (superuser), Regular User
- 24 granular permissions and permission packages for agents
- Auto role sync on agent assignment/revocation
- REST API with JWT auth (DRF + SimpleJWT)
- Celery + Redis for background tasks (calls, CSV imports)
- Docker-ready (see Dockerfile and docker-compose.yml)

## Tech stack
- Python 3.12, Django 5.x, Django REST Framework
- Celery, Redis, django-celery-beat
- PostgreSQL (production), SQLite used in dev
- Frontend integration patterns documented for role/permission checks

## Quick start (development)
1. Create virtualenv and install:
   .venv/bin/python -m venv .venv
   . .venv/bin/activate
   pip install -r requirements.txt

2. Copy environment template:
   cp .env.example .env
   Fill required vars (e.g. BLAND_API_KEY, REDIS_URL).

3. Migrate and seed:
   python manage.py migrate
   python manage.py loaddata initial_permissions.json  # if provided in repo

4. Run dev server:
   python manage.py runserver

Or with Docker:
   docker-compose up --build

See [QUICK_START.md](QUICK_START.md) and [SETUP_COMPLETE.md](SETUP_COMPLETE.md) for full setup details.

## Running tests and validation
- There is an integration test script: [test_permission_system.py](test_permission_system.py). It covers agent assignment, permission granting, utility functions and agent revocation scenarios.
- Validation and summary docs: [VALIDATION_SUMMARY.md](VALIDATION_SUMMARY.md), [CODEBASE_VALIDATION_REPORT.md](CODEBASE_VALIDATION_REPORT.md).

## Key files & references
- Application entry: [manage.py](manage.py)
- Docker: [Dockerfile](Dockerfile), [docker-compose.yml](docker-compose.yml)
- Documentation index: [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)
- Role cheat sheet: [ROLES_QUICK_REFERENCE.md](ROLES_QUICK_REFERENCE.md)
- API testing guide: [API_TESTING_GUIDE.md](API_TESTING_GUIDE.md)
- Implementation notes: [IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md)
- Multi-tenant architecture: [MULTI_TENANT_PERMISSION_SYSTEM.md](MULTI_TENANT_PERMISSION_SYSTEM.md)

## Important models (code references)
- [`callfairy.apps.accounts.models.User`](callfairy/apps/accounts/models.py)
- [`callfairy.apps.accounts.models.Organisation`](callfairy/apps/accounts/models.py)
- [`callfairy.apps.accounts.models.Agent`](callfairy/apps/accounts/models.py)
- [`callfairy.apps.accounts.models.Permission`](callfairy/apps/accounts/models.py)
- [`callfairy.apps.accounts.models.AgentPermissions`](callfairy/apps/accounts/models.py)

## How to contribute
- Follow the docs in [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) for coding standards and testing.
- Add tests for permission edge-cases and API endpoints.
- Update docs any time permission behavior changes.

## Support
- Read the full docs starting at [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md).
- For quick role checks/examples see [ROLES_QUICK_REFERENCE.md](ROLES_QUICK_REFERENCE.md).