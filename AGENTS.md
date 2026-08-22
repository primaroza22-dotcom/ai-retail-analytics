# AI RETAIL ANALYTICS — AGENT RULES

## General

This is a production-oriented computer vision and retail analytics project.

Always inspect the repository before modifying files.

Prefer small, testable changes.

Do not implement future sprint features unless explicitly requested.

Never invent test results.

Never expose secrets.

Never hard-code credentials.

Use type hints.

Keep modules focused on one responsibility.

Prefer readable code over clever code.

## Development Strategy

Work incrementally.

Each task must:

1. Inspect
2. Plan
3. Implement
4. Test
5. Report

Do not silently skip testing.

## Computer Vision

Future computer vision modules must be modular.

Camera input, detection, tracking, zones, analytics, and storage must remain separate components.

Do not couple YOLO directly to the web frontend.

## Backend

FastAPI will eventually provide the API layer.

Business logic must not be embedded directly into route handlers.

## Database

PostgreSQL will eventually be the production database.

Database access must be isolated from business logic.

## Frontend

Next.js will eventually provide the dashboard.

The frontend must communicate through documented APIs/WebSocket rather than directly accessing the database.

## Security

Never commit:

- API keys
- passwords
- tokens
- camera credentials
- database credentials
- .env files

## Testing

Every meaningful feature must have an appropriate test.

Fix failing tests before completing the task.

## Git

Make small logical commits.

Commit messages must clearly describe the change.
