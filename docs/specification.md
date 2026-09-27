> **About this file.** This is the specification the project was built from, kept as written apart from minor wording edits. During the build it was the repository's `CLAUDE.md` (the instructions Claude Code loads into every session) and drove the nine-phase workflow described in [ai-development.md](ai-development.md). Once those phases were complete it moved here, and a shorter `CLAUDE.md` for ongoing work replaced it: see [../CLAUDE.md](../CLAUDE.md) and [ai-development.md §12](ai-development.md#12-harness-how-the-repo-is-set-up-for-ai-assisted-work).

# Task Manager - Project Instructions

## Role

Act as a senior software engineer helping me build a production-quality full-stack application.

You should prioritize:

* Clean Architecture
* SOLID principles
* Separation of concerns
* Testability
* Security
* Maintainability
* Type safety
* Idiomatic Python
* Good API design
* Good frontend architecture
* Clear documentation
* Simple solutions over unnecessary complexity

Do not blindly generate code. Before implementing significant functionality, reason about the architecture and verify that the implementation satisfies the requirements.

When making technical decisions, briefly explain the reasoning in the relevant documentation or code comments when appropriate.

---

# Project Goal

Build a full-stack task management application.

Users should be able to:

* Authenticate
* Create tasks
* View tasks
* Update tasks
* Delete tasks
* Assign tasks to users
* Mark tasks as completed
* Filter tasks by status
* Filter tasks by due date
* Paginate task results

The application should demonstrate production-quality backend and frontend engineering practices.

---

# Technology Stack

## Backend

Use:

* Python 3.12+
* FastAPI
* PostgreSQL
* SQLAlchemy 2.x
* Alembic
* Pydantic v2
* JWT authentication
* pytest
* pytest-cov
* Redis
* Celery
* SlowAPI or another appropriate rate-limiting solution
* Ruff
* MyPy where practical

Use asynchronous FastAPI endpoints and SQLAlchemy where appropriate.

## Frontend

Use:

* React
* TypeScript
* Vite
* TanStack Query for server state
* React Router
* A lightweight UI solution such as Tailwind CSS
* React Hook Form where forms are required

The frontend should be responsive and reasonably polished without spending excessive time on visual design.

## Infrastructure

Use:

* Docker
* Docker Compose
* PostgreSQL
* Redis
* Backend container
* Frontend container

---

# Architecture

Use a Clean Architecture-inspired structure.

The backend should not become a collection of route handlers containing business logic.

Prefer a structure similar to:

backend/
app/
main.py

```
    core/
        config.py
        security.py
        database.py
        dependencies.py

    domain/
        entities/
        repositories/
        services/

    application/
        use_cases/
        schemas/

    infrastructure/
        database/
        repositories/
        services/

    presentation/
        api/
            routes/
            dependencies/

    workers/
        celery_app.py
        tasks.py

tests/
    unit/
    integration/
```

Keep framework-specific concerns close to the presentation/infrastructure layers.

Business rules should be independent from FastAPI whenever practical.

Use dependency injection for repositories and services.

---

# Database Design

Create at least the following entities.

## User

Fields:

* id
* email
* password_hash
* is_active
* created_at
* updated_at

## Task

Fields:

* id
* title
* description
* status
* due_date
* completed_at
* assigned_to
* created_at
* updated_at

Use appropriate PostgreSQL types and constraints.

Task status should be an explicit enum, for example:

* TODO
* IN_PROGRESS
* COMPLETED

Add appropriate indexes, particularly for fields commonly used for filtering.

Use foreign keys and proper cascade behavior.

Do not store plaintext passwords.

---

# Authentication

Implement JWT authentication.

Requirements:

* Login endpoint
* Access token
* Secure password hashing
* Protected task endpoints
* Current-user dependency
* Validate token expiration
* Reject invalid or expired tokens
* Do not expose password hashes through API responses

Use a standard password hashing algorithm such as Argon2 or bcrypt.

Authentication should be implemented as reusable dependencies/services rather than duplicated across endpoints.

---

# API

Implement RESTful endpoints.

Example:

POST   /api/v1/auth/login

GET    /api/v1/tasks
POST   /api/v1/tasks
GET    /api/v1/tasks/{task_id}
PATCH  /api/v1/tasks/{task_id}
DELETE /api/v1/tasks/{task_id}

POST/PATCH operations should validate input using Pydantic schemas.

Use appropriate HTTP status codes.

Use consistent error responses.

Examples:

* 200 for successful reads/updates
* 201 for creation
* 204 for deletion where appropriate
* 400 for invalid requests
* 401 for authentication failures
* 403 for authorization failures
* 404 for missing resources
* 422 for validation errors
* 429 for rate limiting

Do not expose internal exceptions to clients.

---

# Task Filtering

GET /api/v1/tasks should support:

* status
* due_date
* due_date_from
* due_date_to
* pagination

Example:

GET /api/v1/tasks?status=TODO&page=1&page_size=20

GET /api/v1/tasks?due_date_from=2026-09-01&due_date_to=2026-09-30

Support combining filters.

Validate pagination parameters.

Set sensible maximum page sizes.

Return metadata such as:

{
"items": [...],
"page": 1,
"page_size": 20,
"total": 100,
"pages": 5
}

---

# Authorization

Users should only be able to perform actions they are authorized to perform.

At minimum:

* Authenticated users can view tasks.
* Users can create tasks.
* Users can update/delete tasks according to the application's authorization rules.
* A user should not be able to manipulate another user's private resources without authorization.

Document the authorization decisions in the README.

Do not implement unnecessarily complicated RBAC unless it provides clear value.

---

# Rate Limiting

Implement API rate limiting.

Apply stricter limits to authentication endpoints to mitigate brute-force attempts.

Example concept:

* General API: reasonable requests/minute
* Login: significantly stricter requests/minute

Return HTTP 429 when limits are exceeded.

Document the chosen implementation and its limitations, especially in a multi-instance deployment.

---

# Background Processing

Implement background task processing using:

* Celery
* Redis

Create at least one meaningful background task.

Example:

When a task is marked completed, enqueue a background job that records an activity/event or performs another non-critical asynchronous operation.

The background operation must be meaningful enough to demonstrate:

* Celery configuration
* Redis broker
* Task dispatch
* Worker execution
* Error handling

Do not introduce background processing purely for the sake of complexity.

Document why the operation is asynchronous.

---

# Testing

Use pytest.

Follow a test pyramid:

* Unit tests for business logic
* Integration tests for database/repository behavior
* API tests for critical endpoints
* Authentication tests
* Authorization tests

Minimum required coverage:

80%

Aim for higher coverage where practical.

Tests should cover at least:

## Authentication

* Successful login
* Invalid credentials
* Expired/invalid token
* Protected endpoint without authentication

## Tasks

* Create task
* Read task
* Update task
* Delete task
* Mark task completed
* Assign task
* Filter by status
* Filter by due date
* Combined filters
* Pagination
* Non-existent task
* Unauthorized access
* Validation errors

## Rate limiting

Test that excessive requests eventually return HTTP 429.

## Background processing

Test task dispatch without requiring an actual production worker.

Prefer deterministic tests.

Avoid tests that depend on external services.

---

# TDD

Prefer a test-first workflow for important business behavior.

For significant functionality:

1. Write the test.
2. Run the test and confirm it fails.
3. Implement the smallest solution.
4. Run the test again.
5. Refactor.
6. Run the full suite.

Do not create meaningless tests just to increase coverage.

Tests should verify behavior rather than implementation details.

---

# Frontend

Build a React + TypeScript application.

Required screens:

## Login

* Email
* Password
* Validation
* Authentication handling
* Error states

## Task Dashboard

Display:

* Task list
* Status
* Due date
* Assigned user
* Pagination

Provide filters:

* Status
* Due date

Provide actions:

* Create task
* Edit task
* Delete task
* Mark completed
* Assign task

Use proper loading, empty, and error states.

The UI should work on desktop and mobile.

Avoid unnecessary global state.

Use TanStack Query for API/server state.

Keep components focused and reusable.

---

# Frontend Architecture

Prefer something similar to:

frontend/
src/
app/
components/
features/
auth/
tasks/
hooks/
lib/
services/
types/
routes/

Do not put all logic into App.tsx.

Separate:

* API calls
* Components
* State management
* Forms
* Types
* Authentication
* Feature-specific logic

Handle API errors consistently.

Do not leave React warnings in the browser console.

---

# API Client

Create a typed API client.

Centralize:

* Base URL
* Authentication token handling
* HTTP errors
* Request configuration

Avoid duplicating fetch/axios logic throughout components.

---

# Docker

Create:

docker-compose.yml

Services should include:

* api
* frontend
* postgres
* redis
* celery-worker

Development should be possible with a single command.

Example:

docker compose up --build

Database migrations should be easy to execute.

Do not hardcode secrets.

Use environment variables.

Provide:

.env.example

Never commit real secrets.

---

# Configuration

Use environment-based configuration.

Example variables:

DATABASE_URL
JWT_SECRET_KEY
JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES
REDIS_URL
CELERY_BROKER_URL
CELERY_RESULT_BACKEND
CORS_ORIGINS

Validate required configuration at startup.

Provide sensible development defaults only where safe.

---

# Seed Data

Provide a seed mechanism.

Create demo users and tasks.

Example demo credentials should be documented in the README.

Never use real credentials or secrets.

The seed data should demonstrate:

* Multiple users
* Different task statuses
* Different due dates
* Assigned/unassigned tasks
* Completed tasks

---

# API Documentation

Use FastAPI's built-in OpenAPI/Swagger documentation.

Ensure the API documentation is useful.

Document:

* Authentication
* Request schemas
* Response schemas
* Query parameters
* Error responses

Swagger should be available during development.

---

# Code Quality

Use:

* Ruff
* Black-compatible formatting
* Type hints
* Meaningful names
* Small focused functions
* Explicit error handling

Avoid:

* `Any` unless justified
* Large functions
* God classes
* Business logic inside routes
* Duplicate validation
* Magic numbers
* Hardcoded configuration
* Unnecessary abstractions

Do not over-engineer the project.

The architecture should be clean but easy to understand and explain.

---

# Git / Commit Structure

Keep commits logical and easy to explain.

Suggested progression:

1. Project scaffolding
2. Database and migrations
3. Authentication
4. Task domain/model
5. Task API
6. Filtering and pagination
7. Tests
8. Rate limiting
9. Celery/background processing
10. Frontend scaffolding
11. Frontend authentication
12. Task dashboard
13. Docker
14. Seed data
15. Documentation
16. Final cleanup

Do not squash everything into one giant implementation if the repository history is being evaluated.

---

# README

Create a professional README containing:

## Overview

Explain the application and its purpose.

## Architecture

Include an architecture diagram using Mermaid if useful.

Explain:

* API
* Database
* Redis
* Celery
* Frontend
* Authentication
* Background processing

## Technology choices

Explain why the main technologies were selected.

## Setup

Explain local setup and Docker setup.

## Environment variables

Document `.env.example`.

## Database

Explain migrations and seeding.

## Running tests

Include commands.

## Coverage

Show how to run coverage.

## API documentation

Explain where Swagger is available.

## Demo credentials

Provide seeded credentials.

## Design decisions

Document important tradeoffs.

## AI-assisted development

Include a section describing:

* Which AI tool was used
* How prompts were structured
* How generated code was validated
* What AI-generated code was changed
* How edge cases were handled
* How security was reviewed
* How performance was evaluated

This section is important because GenAI usage is explicitly evaluated.

---

# AI-Assisted Development Requirements

The project must demonstrate critical use of AI rather than blindly accepting generated code.

Maintain a document:

docs/ai-development.md

Record significant examples of:

1. Prompt used
2. Generated approach
3. What was accepted
4. What was rejected
5. Why it was changed
6. How it was validated

Include examples involving:

* Architecture
* Authentication
* Testing
* Error handling
* Performance
* Security
* Frontend implementation

The final document should demonstrate that AI was used as an engineering assistant rather than as an unquestioned code generator.

---

# Validation

After implementation, perform a complete validation pass.

Run:

* Unit tests
* Integration tests
* Coverage
* Ruff
* Type checking where configured
* Frontend lint
* Frontend build
* Docker build
* Docker Compose startup
* Database migrations
* Seed script
* API smoke tests

Fix all errors and warnings that are introduced by the project.

Verify:

* Authentication works
* CRUD works
* Filtering works
* Pagination works
* Authorization works
* Rate limiting works
* Celery worker works
* Frontend communicates with API
* Demo credentials work
* Swagger works
* Docker setup works

Do not claim that something works unless you actually verified it.

---

# Security Review

Before considering the project complete, review:

* Password hashing
* JWT validation
* Token expiration
* Secret management
* CORS
* SQL injection protection
* Input validation
* Authorization
* Rate limiting
* Error information leakage
* Dependency vulnerabilities where practical

Never expose:

* Password hashes
* JWT secrets
* Database credentials
* Internal stack traces

---

# Performance Review

Review:

* Database indexes
* Pagination
* N+1 queries
* Query efficiency
* API response size
* Frontend unnecessary requests
* React unnecessary re-renders where relevant
* Redis/Celery usage

Use realistic seeded data to validate pagination and filtering.

Do not prematurely optimize.

---

# Important Development Rules

1. Do not implement the entire project blindly in one step.
2. Inspect the repository before changing existing files.
3. Keep architecture decisions explicit.
4. Prefer simple, maintainable solutions.
5. Write tests for important behavior.
6. Run tests after meaningful changes.
7. Do not ignore failing tests.
8. Do not suppress warnings without understanding them.
9. Do not add dependencies unless there is a clear reason.
10. Do not introduce unnecessary abstractions.
11. Do not hardcode secrets.
12. Do not leave TODOs for core requirements.
13. Keep API contracts consistent.
14. Keep frontend and backend types aligned.
15. Validate generated code rather than trusting it automatically.

---

# Development Workflow

Start by inspecting the repository.

Then:

### Phase 1 - Architecture

Before coding, produce:

* Proposed directory structure
* Database schema
* API endpoint list
* Authentication flow
* Background processing flow
* Frontend architecture
* Testing strategy
* Docker architecture

Do not implement yet.

### Phase 2 - Backend Foundation

Implement:

* Project configuration
* Database
* SQLAlchemy models
* Alembic
* Configuration
* Health check
* Base API structure

Run tests.

### Phase 3 - Authentication

Implement:

* User model
* Password hashing
* JWT
* Login
* Authentication dependencies

Write tests first where practical.

### Phase 4 - Task Management

Implement:

* Task model
* Repository
* Services/use cases
* CRUD endpoints
* Assignment
* Completion

Write tests.

### Phase 5 - Filtering and Pagination

Implement:

* Status filtering
* Due date filtering
* Pagination
* Database indexes

Add tests.

### Phase 6 - Security and Infrastructure

Implement:

* Rate limiting
* Redis
* Celery
* Background task
* Docker

Test each component.

### Phase 7 - Frontend

Implement:

* React project
* Authentication
* Dashboard
* Task CRUD
* Filters
* Pagination
* Responsive UI

### Phase 8 - Seed and Documentation

Implement:

* Seed data
* Demo credentials
* README
* Architecture documentation
* AI development documentation

### Phase 9 - Final Review

Run the complete validation suite.

Then perform a senior-level code review of the entire project.

Identify:

* Bugs
* Security issues
* Architecture problems
* Poor abstractions
* Missing tests
* Performance issues
* UX issues
* Documentation gaps

Fix the issues found.

---

# Final Deliverable

The final repository should feel like a small production application that a senior engineer could confidently present and defend.

The implementation should be understandable enough that I can explain every important design decision during a code review.

Do not optimize for maximum number of files or maximum complexity.

Optimize for:

**clarity + correctness + testability + maintainability + security + demonstrable engineering judgment.**
