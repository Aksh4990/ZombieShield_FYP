# ZombieShield

ZombieShield is an API security platform foundation. This milestone provides a working API inventory service and a small UI for viewing it. It deliberately does not include discovery, lifecycle classification logic, risk scoring, remediation, machine learning, or external security integrations.

## Architecture

- `backend/`: FastAPI service with SQLAlchemy, Pydantic validation, and PostgreSQL persistence.
- `frontend/`: React, TypeScript, and Vite application shell.
- `tests/`: backend endpoint tests, using SQLite only for isolated test execution.
- `docs/architecture.md`: component boundaries and future extension direction.
- `docker-compose.yml`: frontend, backend, and PostgreSQL only.

The backend creates the initial `apis` table on startup. Its inventory identity has a database uniqueness constraint over organization, service, host, method, endpoint path, and version. PostgreSQL indexes support organization/service, lifecycle state, and last-seen queries.

## Run with Docker

1. Create a local environment file: `Copy-Item .env.example .env`
2. Replace `POSTGRES_PASSWORD` and the matching password in `DATABASE_URL` with a local development secret.
3. Start the stack: `docker compose up --build`

Open the UI at http://localhost:5173, the API documentation at http://localhost:8000/docs, and the health endpoint at http://localhost:8000/health.

Stop the stack with `docker compose down`. Add `-v` only if you intentionally want to remove the local PostgreSQL volume.

## API inventory endpoints

- `GET /health` returns `{ "status": "healthy" }`.
- `POST /apis` creates an inventory record.
- `GET /apis` returns all inventory records.
- `GET /apis/{id}` returns one inventory record or a 404 response.

## Discovery (Milestone 2)

- `POST /discovery/openapi` accepts an OpenAPI 3.x JSON or YAML document.
- `POST /discovery/git` scans deterministic FastAPI and Flask route patterns in a repository directory.
- `POST /discovery/runtime-log` parses simple HTTP access-log lines.

Git discovery is intentionally restricted to `discovery-repositories/`, mounted read-only in the backend container at `/workspace/repositories`. Submit paths relative to that directory (for example, `sample-api`); absolute paths and directory traversal are rejected. Copy a local source directory into that project folder when demonstrating discovery. The included `sample-api` directory is demonstration-only source.

Example create request:

```json
{
  "organization": "example-org",
  "service_name": "accounts",
  "http_method": "GET",
  "endpoint_path": "/v1/accounts",
  "host": "api.example.test",
  "version": "v1",
  "source": "manual",
  "owner": "platform@example.test",
  "is_registered": true,
  "is_documented": false
}
```

## Test and local frontend build

Backend tests require Python 3.13+ and can be run from the repository root after installing `backend/requirements.txt` into a project-local virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r backend\requirements.txt
.\.venv\Scripts\python -m pytest -q
```

The tests use SQLite only to keep them isolated; the normal application uses PostgreSQL through `DATABASE_URL`.

To build the frontend outside Docker:

```powershell
Set-Location frontend
npm.cmd install
npm.cmd run build
```
