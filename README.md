# ZombieShield

ZombieShield is an API security platform that discovers APIs, maintains a unified inventory, classifies lifecycle state, assesses explainable security risk, correlates source-attributed threat intelligence, runs safe evidence-only simulations, and produces explainable security recommendations.

The current implementation covers Milestones 1-9. Milestone 10 (controlled end-to-end validation and measured detection metrics) remains to be completed using a local target such as Sock Shop.

## Architecture

- `backend/`: FastAPI service with SQLAlchemy, Pydantic validation, and PostgreSQL persistence.
- `frontend/`: React, TypeScript, and Vite application shell.
- `tests/`: backend endpoint tests, using SQLite only for isolated test execution.
- `docs/architecture.md`: component boundaries and future extension direction.
- `docker-compose.yml`: frontend, backend, and PostgreSQL only.

The backend maintains the central `apis` inventory together with threat advisories/findings, simulation results, and decision records. Its canonical API identity is based on organization, host, HTTP method, normalized endpoint path, and version.

## Run with Docker

1. Create a local environment file: `Copy-Item .env.example .env`
2. Replace `POSTGRES_PASSWORD` and the matching password in `DATABASE_URL` with a local development secret.
3. Start the stack: `docker compose up --build`

Open the UI at http://localhost:5173, the API documentation at http://localhost:8000/docs, and the health endpoint at http://localhost:8000/health.

Stop the stack with `docker compose down`. Add `-v` only if you intentionally want to remove the local PostgreSQL volume.

## API inventory endpoints

- `GET /health` returns `{ "status": "healthy" }`.
- `POST /apis` creates an inventory record.
- `GET /apis` returns all inventory records and can filter by lifecycle state.
- `GET /apis/{id}` returns one inventory record or a 404 response.

## Implemented milestones

- **Milestone 1 — Foundation:** FastAPI, PostgreSQL, React/Vite, Docker Compose, and API inventory.
- **Milestone 2 — Discovery:** OpenAPI, Git source, and runtime-log discovery.
- **Milestone 3 — Normalization and deduplication:** canonical keys, normalized trailing slashes, version separation, source merging, and observation timestamps.
- **Milestone 4 — Lifecycle classification:** `ACTIVE`, `DEPRECATED`, `ZOMBIE`, and `DECOMMISSIONED` lifecycle states.
- **Milestone 5 — Risk assessment + ML:** explainable deterministic rules plus a synthetic-data Gradient Boosting model.
- **Milestone 6 — Threat intelligence:** source-attributed advisory storage and exact component/version correlation.
- **Milestone 7 — Threat simulation:** safe, evidence-only simulations with no scanning, traffic generation, or exploitation.
- **Milestone 8 — Decision engine:** persisted, recommendation-only security actions.
- **Milestone 9 — Dashboard improvements:** lifecycle, risk, threat, and simulation summary cards.

## Discovery (Milestone 2)

- `POST /discovery/openapi` accepts an OpenAPI 3.x JSON or YAML document.
- `POST /discovery/git` scans deterministic FastAPI and Flask route patterns in a repository directory.
- `POST /discovery/runtime-log` parses simple HTTP access-log lines.

Git discovery is intentionally restricted to `discovery-repositories/`, mounted read-only in the backend container at `/workspace/repositories`. Submit paths relative to that directory (for example, `sample-api`); absolute paths and directory traversal are rejected. Copy a local source directory into that project folder when demonstrating discovery. The included `sample-api` directory is demonstration-only source.

## Lifecycle classification (Milestone 4)

- `POST /classification/run` evaluates every inventory record as `ACTIVE`, `DEPRECATED`, `ZOMBIE`, or `DECOMMISSIONED` using source evidence, flags, and recent runtime activity.

## Risk assessment (Milestone 5)

- `POST /apis/{id}/risk-assessment` assesses one inventory API.
- `POST /risk/assessments/run` assesses all inventory APIs.

Every assessment stores a 0-100 score, `LOW`/`MEDIUM`/`HIGH`/`CRITICAL` level, extracted evidence, findings, explanation, and timestamp. Scores combine explainable inventory rules (60%) with a `GradientBoostingClassifier` result (40%). The model is trained only on reproducible synthetic inventory scenarios; it is not production security data and does not claim real-world accuracy.

Authentication, TLS, rate limiting, and PII evidence are not currently collected. They are stored as explicit `unknown` evidence and are never treated as proof that a security control is missing.

## Threat intelligence (Milestone 6)

- `POST /threat-intelligence/advisories` stores a source-attributed advisory.
- `POST /threat-intelligence/correlate/run` correlates advisories against all APIs.
- `POST /apis/{id}/threat-intelligence/correlate` correlates one API.
- `GET /threat-intelligence/advisories`, `GET /threat-intelligence/findings`, and `GET /apis/{id}/threat-findings` expose evidence and matches.

Correlation requires an explicitly supplied API component name/version and an exact affected version in a source-attributed advisory. ZombieShield does not populate sample CVEs, infer version ranges, or claim external-feed coverage. Correlated findings increment the API threat finding count and are included in the next risk assessment.

## Threat simulation (Milestone 7)

- `POST /simulation/run` runs controlled scenarios for all or selected inventory APIs.
- `POST /apis/{id}/simulation/run` runs scenarios for one API.
- `GET /simulation/results` and `GET /apis/{id}/simulation-results` return stored outcomes.

Simulations evaluate stored inventory evidence only. They do not send HTTP requests, scan hosts, exploit APIs, or generate traffic. Current scenarios review zombie exposure, threat findings, authentication evidence, and rate-limit evidence. Missing security-control evidence remains `unknown` and produces an `INSUFFICIENT_EVIDENCE` result rather than a fabricated finding.

## Decision engine (Milestone 8)

- `POST /decisions/run` evaluates inventory evidence and persists recommendation-only decisions.

The engine returns one of:

- `MONITOR` for low-evidence/low-risk APIs.
- `REMEDIATE` for elevated risk, threat findings, or observed simulation risk.
- `ESCALATE` for critical risk.

No automatic gateway blocking or external remediation action is performed.

## Dashboard (Milestone 9)

The dashboard displays backend health, inventory count, lifecycle distribution, zombie API count, high/critical risk count, risk-assessment coverage, and aggregate threat/simulation findings.

## Remaining work — Milestone 10 validation

The final validation work is intentionally not claimed as complete. Recommended next steps are:

1. Deploy a controlled local target, such as Sock Shop, using Docker Compose.
2. Establish a ground-truth inventory of endpoints and expected lifecycle states.
3. Generate normal, local-only runtime traffic and collect evidence.
4. Introduce controlled cases: an undocumented/debug route, an older API version left active, and documentation removal.
5. Run the complete ZombieShield workflow.
6. Compare detected results with the ground truth and calculate accuracy, precision, recall, F1 score, false positives, and false negatives.

Possible future enhancements after validation include authenticated OpenAPI discovery, reliable dependency/SBOM ingestion, source-backed CVE feed integration, version-range matching, API detail pages and filtering, and a gateway integration that remains recommendation-first and requires explicit operator approval for any enforcement.

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
