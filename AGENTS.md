# ZombieShield — Project Context and Development Guide

## 1. Project Identity

Project Name:
ZombieShield – Automated Zombie API Discovery & Defence Platform

Project Type:
Final-Year Engineering Project

Primary Domain:
API security, API lifecycle management, automated discovery, risk assessment, threat intelligence, threat simulation, and remediation.

Primary Goal:

ZombieShield is an automated platform designed to continuously discover APIs from multiple sources, maintain a unified API inventory, determine the lifecycle state of APIs, assess security risk, correlate APIs with threat intelligence, simulate security threats, and recommend or execute appropriate defensive actions.

The platform specifically focuses on identifying:

- Active APIs
- Shadow APIs
- Zombie APIs
- Deprecated APIs
- Decommissioned APIs
- Undocumented or unexpectedly exposed APIs
- APIs with elevated security risk

The system should ultimately provide a practical end-to-end workflow:

Discovery → Inventory → Classification → Risk Assessment → Threat Intelligence → Threat Simulation → Decision → Dashboard → Validation


## 2. Current Project Status

Completed milestones:

- Milestone 1 — Foundation
- Milestone 2 — API Discovery
- Milestone 3 — Inventory Normalization, Deduplication and Version Tracking
- Milestone 4 — API Lifecycle Classification

Current milestone:

- Milestone 5 — Risk Assessment + Machine Learning

Pending milestones:

- Milestone 5 — Risk Assessment + Machine Learning
- Milestone 6 — Threat Intelligence
- Milestone 7 — Threat Simulation
- Milestone 8 — Decision Engine
- Milestone 9 — Dashboard improvements
- Milestone 10 — Final Validation

The repository currently represents a working implementation through Milestone 4.

Do not assume that Milestones 5–10 already exist.

Before implementing a new milestone, inspect the current repository and existing implementation rather than recreating existing functionality.


## 3. Core Architecture

The intended architecture is:

React Frontend
        ↓
FastAPI Backend
        ↓
PostgreSQL Database

The backend contains the major logical components:

- Discovery
- API Inventory
- Normalization and Deduplication
- Lifecycle Classification
- Risk Assessment
- Threat Intelligence
- Threat Simulation
- Decision Engine

The high-level future pipeline is:

Infrastructure / API Sources
        ↓
API Discovery
        ↓
Inventory and Normalization
        ↓
Lifecycle Classification
        ↓
Risk Assessment
        ↓
Threat Intelligence Correlation
        ↓
Threat Simulation
        ↓
Decision Engine
        ↓
Dashboard / Remediation / Audit


## 4. Technology Stack

Current core technologies:

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Pydantic
- Docker
- Docker Compose
- React
- TypeScript
- Vite

Additional planned technology:

- scikit-learn for machine-learning-based risk assessment

Do not introduce additional infrastructure unless it provides a concrete feature required by the project.

Avoid unnecessary complexity such as:

- Kafka
- Neo4j
- Kubernetes
- Helm
- Grafana
- Prometheus
- Redis
- Celery
- Elasticsearch
- spaCy

These technologies were considered during the original design but are not part of the current practical MVP unless a later milestone demonstrates a specific reason to add them.

The priority is a complete, working, demonstrable system rather than an unnecessarily large technology stack.


## 5. Project Philosophy

The project should remain:

- Practical
- Demonstrable
- Testable
- Explainable
- Modular
- Easy to run locally
- Suitable for a final-year engineering project

Every major feature should have a clear purpose in the ZombieShield workflow.

Do not add technologies simply because they appear in an academic architecture diagram.

Prefer a smaller working implementation over a large partially implemented architecture.

Do not replace working functionality unnecessarily.

Do not rewrite existing modules unless there is a clear technical reason.


## 6. Current Repository Structure

Important backend files currently include:

backend/app/main.py
backend/app/api/routes.py
backend/app/core/config.py
backend/app/db/base.py
backend/app/db/session.py
backend/app/models/api.py
backend/app/schemas/api.py
backend/app/schemas/classification.py
backend/app/schemas/discovery.py
backend/app/services/api_inventory.py
backend/app/services/discovery.py
backend/app/services/lifecycle.py
backend/app/services/normalization.py

The frontend is under:

frontend/

The repository also contains:

discovery-repositories/

which is used as the controlled source area for repository-based API discovery.

Do not assume that every planned future module already exists.


## 7. Backend Dependencies

Current backend requirements include:

- fastapi==0.115.6
- uvicorn[standard]==0.34.0
- sqlalchemy==2.0.36
- psycopg[binary]==3.2.3
- pydantic-settings==2.7.0
- PyYAML==6.0.2
- pytest==8.3.4
- httpx==0.28.1

scikit-learn is planned for Milestone 5 but has not yet been added to the current implementation.


## 8. Database and API Inventory

The primary database table is:

apis

The API inventory stores information including:

- id
- organization
- service_name
- HTTP method
- endpoint path
- host
- version
- source
- sources
- canonical key
- owner
- registration status
- documentation status
- deprecation status
- supported-surface removal status
- first_seen
- last_seen
- lifecycle_state
- classification_reason
- classified_at
- created_at
- updated_at

Risk-related fields have not yet been added.

The current lifecycle states are:

ACTIVE
DEPRECATED
ZOMBIE
DECOMMISSIONED


## 9. API Identity and Deduplication

The canonical API identity is based on:

organization
+
host
+
HTTP method
+
normalized endpoint path
+
version

The canonical identity is represented by a SHA-256 canonical key.

Trailing slashes are normalized.

For example:

/users

and

/users/

must resolve to the same normalized endpoint identity.

Different versions must remain distinct.

For example:

/api/v1/users

and

/api/v2/users

must not collapse into one inventory record.

An API observed from multiple sources should remain a single inventory record when its canonical identity matches.

The API record maintains a list of observed sources.

Example sources include:

- openapi
- git
- runtime_log

Repeated observations should:

- preserve first_seen
- update last_seen when appropriate
- merge sources without duplication
- preserve the canonical identity

Runtime observations that do not contain a reliable version must remain:

unversioned

Do not guess an API version from insufficient evidence.


## 10. API Discovery

Milestone 2 implemented discovery from three primary sources:

### OpenAPI

Endpoint:

POST /discovery/openapi

Supports OpenAPI 3 JSON/YAML extraction.

### Git repositories

Endpoint:

POST /discovery/git

Repository discovery is restricted to the configured discovery repository root.

The repository source is mounted read-only.

The current implementation includes deterministic discovery of common FastAPI and Flask route patterns.

### Runtime logs

Endpoint:

POST /discovery/runtime-log

Runtime log discovery:

- parses usable request lines
- ignores malformed lines
- normalizes numeric path segments
- normalizes UUID path segments
- creates inventory observations

Discovered APIs are persisted into PostgreSQL through the inventory/reconciliation service.


## 11. Current Discovery-to-Inventory Flow

The intended flow is:

Source
  ↓
Discovery Service
  ↓
APICreate schema
  ↓
Normalization
  ↓
Canonical identity
  ↓
Existing inventory lookup
  ↓
Create or observe existing API
  ↓
PostgreSQL

The reconciliation logic should be reused by future discovery sources.

Do not create separate duplicate persistence logic for every new discovery source.


## 12. Lifecycle Classification

The lifecycle classifier currently supports:

ACTIVE
DEPRECATED
ZOMBIE
DECOMMISSIONED

The classifier uses source evidence, runtime activity, deprecation flags, removal evidence, and an activity window.

The current default activity window is:

30 days

Configuration:

lifecycle_activity_window_days

Current classification logic:

1. Explicitly deprecated API:
   DEPRECATED

2. API explicitly removed from the supported surface and without recent runtime activity:
   DECOMMISSIONED

3. Recent runtime activity exists without corresponding documentation/source evidence:
   ZOMBIE

4. Supported by documentation/source and recent runtime activity:
   ACTIVE

5. If there is insufficient evidence for a stronger lifecycle transition:
   ACTIVE

The classifier intentionally avoids making aggressive lifecycle changes when evidence is insufficient.

False-positive avoidance is important.

A missing observation must not automatically mean that an API is dead.


## 13. Current Classification API

The classification workflow exposes:

POST /classification/run

The API inventory can also be queried through the existing inventory endpoints.

The frontend displays lifecycle information and classification reasons.


## 14. Current Verification Status

Milestone 1 was fully verified.

Verified:

- PostgreSQL starts successfully
- FastAPI starts successfully
- React frontend starts successfully
- /health returns HTTP 200
- API creation works
- API listing works
- Individual API retrieval works
- Frontend CORS works
- Frontend production build succeeds
- Backend tests pass
- Docker Compose stack works

Milestone 2 was fully verified.

Verified:

- OpenAPI discovery works
- Git discovery works
- Runtime-log discovery works
- Discovered APIs are persisted
- CORS preflight works
- Backend tests pass
- Frontend build succeeds
- Docker stack works

Milestone 3 was fully verified.

Verified:

- canonical identity works
- path normalization works
- duplicate observations are reconciled
- first_seen is preserved
- last_seen is updated
- multiple sources are merged
- API versions remain distinct
- PostgreSQL persistence works
- backend tests pass
- frontend build succeeds
- Docker stack works

Milestone 4 was fully verified.

The classification run produced:

- 10 APIs evaluated
- 8 ACTIVE
- 2 ZOMBIE
- 0 DEPRECATED
- 0 DECOMMISSIONED

Verified:

- lifecycle classification endpoint
- lifecycle state persistence
- classification reasons
- inventory filtering
- frontend lifecycle display
- backend test suite
- frontend production build
- Docker Compose stack


## 15. Testing Expectations

Every milestone must include appropriate tests.

At minimum:

- unit tests for important service logic
- API/integration tests for new endpoints
- regression tests for existing functionality

After modifying backend functionality:

1. Run backend tests.
2. Rebuild/restart Docker services when necessary.
3. Verify relevant API endpoints.
4. Verify frontend build if frontend code changed.
5. Confirm existing functionality has not regressed.

Do not declare a milestone complete merely because the code compiles.


## 16. Milestone 5 — Risk Assessment + Machine Learning

This is the next major implementation target.

The risk engine should combine:

1. deterministic security rules
2. feature extraction
3. machine-learning risk assessment
4. explainable risk findings

The risk system should be understandable during project demonstration.

Do not build an opaque model that produces a score without explanation.


## 17. Planned Risk Features

Potential risk features include:

- authentication required
- TLS enabled
- TLS certificate age
- rate limiting enabled
- PII exposure
- endpoint age
- version gap
- dependency depth
- lifecycle state
- documentation status
- registration status
- source evidence

Not every feature must be implemented immediately.

Features should be based on information that can actually be obtained reliably.

Do not fabricate security evidence.

If a feature is unavailable, use an explicit unknown/default representation rather than pretending evidence exists.


## 18. Planned Risk Scoring

The risk engine should produce a normalized score, preferably:

0–100

Suggested interpretation:

LOW
MEDIUM
HIGH
CRITICAL

The exact thresholds should be implemented consistently and documented.

The risk result should include explainable findings.

Example:

Risk score: 82

Risk level: HIGH

Findings:

- Authentication not detected
- API exposes potentially sensitive data
- Rate limiting not detected
- Deprecated lifecycle state

The explanation should tell the user why the API received its score.


## 19. Machine Learning Requirement

The project specification calls for machine learning using synthetic training data and a GradientBoostingClassifier.

The ML implementation should therefore be practical and reproducible.

The model should use meaningful security/API features.

The model should not be presented as having been trained on real production security data unless such data actually exists.

Synthetic data should be clearly identified as synthetic.

The ML component should complement deterministic rules rather than make the system impossible to understand.

A practical approach is:

Security features
        ↓
Feature vector
        ↓
GradientBoostingClassifier
        ↓
Risk probability / classification
        ↓
Combined risk score
        ↓
Explainable findings

The final risk engine should remain deterministic enough for repeatable demonstrations.


## 20. Risk Model Design Direction

A reasonable implementation sequence is:

### 5A — Risk data model

Add database fields required to store:

- security feature values
- risk score
- risk level
- risk findings
- risk explanation
- assessment timestamp

### 5B — Feature extraction

Create a dedicated service responsible for transforming API inventory evidence into risk features.

### 5C — Deterministic rules

Create clear rules for obvious security risks.

### 5D — ML scoring

Add scikit-learn and implement the GradientBoostingClassifier using controlled synthetic training data.

### 5E — Risk API

Expose an endpoint for assessing inventory APIs and/or running risk assessment across the inventory.

### 5F — Frontend

Display:

- risk score
- risk level
- important findings
- explanation

### 5G — Integration testing

Verify the complete discovery → classification → risk workflow.


## 21. Threat Intelligence

Milestone 6 should correlate APIs and their technologies/dependencies with known vulnerabilities or threat intelligence.

The implementation should remain practical.

Possible inputs include:

- CVE information
- dependency/version information
- known vulnerable versions
- relevant security indicators

Threat intelligence should enrich the existing inventory/risk model rather than become an independent disconnected subsystem.


## 22. Threat Simulation

Milestone 7 should provide controlled simulation of security scenarios against the discovered API inventory.

The simulation must be safe and intended for the local project environment.

The purpose is to demonstrate how ZombieShield evaluates API exposure and risk.

Do not introduce uncontrolled real-world attack functionality.

The simulation should generate evidence that can be consumed by the risk/decision pipeline.


## 23. Decision Engine

Milestone 8 should convert risk and security evidence into an actionable decision.

Conceptually:

Risk above configured threshold
        ↓
High-risk response
        ↓
Block if gateway permission exists
        OR
Generate remediation/escalation recommendation

Risk below threshold
        ↓
Continue monitoring

The decision engine should be rule-based and explainable.

It should record the reason for a decision.


## 24. Dashboard

The frontend should eventually provide a useful security operations view.

Important dashboard information includes:

- total APIs
- lifecycle distribution
- zombie APIs
- shadow/undocumented APIs where applicable
- risk distribution
- high/critical risk APIs
- recent discoveries
- threat intelligence findings
- remediation/decision status

The dashboard should prioritize useful information over visual complexity.


## 25. Final Validation

The final system should be validated using a controlled real-life-like environment.

The intended validation workflow is:

1. Deploy a target service such as Sock Shop or another suitable multi-service application.
2. Establish the initial ground-truth API inventory.
3. Introduce lifecycle changes.
4. Create a newer API version.
5. Leave an older version running.
6. Remove documentation for an endpoint.
7. Introduce an undocumented/debug endpoint.
8. Run ZombieShield.
9. Compare expected API states against detected states.
10. Calculate:

- Accuracy
- Precision
- Recall
- F1-score
- False positives
- False negatives

The target mentioned in the original project specification is approximately:

90% classification accuracy

The validation should report actual measured results rather than claiming the target was achieved without evidence.


## 26. Important Project Constraints

Do not:

- invent test results
- invent security findings
- claim real-world ML accuracy from synthetic data
- guess API versions
- mark APIs as zombie solely because they were not observed recently
- destroy existing working functionality
- introduce unnecessary infrastructure
- hard-code secrets
- commit real credentials
- expose database passwords or API keys
- modify the architecture without a concrete reason

Do:

- reuse existing services
- preserve backward compatibility
- write tests
- keep changes modular
- document important assumptions
- provide explanations for automated decisions
- verify changes before considering them complete


## 27. Configuration and Secrets

Environment-specific configuration belongs in environment files.

Real secrets must never be committed.

The repository contains:

.env.example

with placeholder local-development configuration.

.env files containing actual secrets must remain ignored by Git.

Never replace a placeholder secret in committed files with a real password, API key, token, or credential.


## 28. Docker

The application is intended to run through Docker Compose.

The primary services are:

- backend
- frontend
- PostgreSQL

The database uses persistent storage.

When making backend or dependency changes, rebuild the relevant Docker image where necessary.

A working local environment should remain easy to start and verify.


## 29. Frontend

The frontend uses:

- React
- TypeScript
- Vite

Frontend changes should consume the existing backend APIs rather than duplicating backend logic.

Types should remain synchronized with backend response models.

The frontend production build must pass after frontend changes.


## 30. Git and Collaboration

The repository uses Git.

The main branch is:

master

The stable implementation currently contains Milestones 1–4.

New work should preferably be performed on a feature branch.

Recommended pattern:

master
  ↓
feature/risk-assessment
  ↓
implementation
  ↓
tests
  ↓
review
  ↓
merge into master

Different contributors should avoid modifying the same files simultaneously when possible.

Before starting work:

1. Pull the latest repository state.
2. Inspect the current implementation.
3. Read this document.
4. Check the current milestone status.
5. Check Git status.
6. Identify files affected by the intended change.

Before committing:

1. Run relevant tests.
2. Verify the application.
3. Review changed files.
4. Confirm no secrets or generated artifacts are included.
5. Commit with a meaningful message.

Do not overwrite another contributor's work without checking the current Git state.


## 31. Current Known Limitations

The current implementation is intentionally an MVP.

Known limitations include:

- Runtime logs may not contain API version information.
- Lifecycle classification depends on available evidence.
- Missing evidence is not equivalent to proof of decommissioning.
- Risk assessment has not yet been implemented.
- Threat intelligence has not yet been implemented.
- Threat simulation has not yet been implemented.
- Decision automation has not yet been implemented.
- Final validation against a controlled target environment has not yet been completed.
- Advanced distributed infrastructure is intentionally not implemented at this stage.


## 32. How Future Work Should Proceed

When continuing the project:

1. Read this file completely.
2. Inspect the actual current repository.
3. Compare the repository against the milestone status above.
4. Do not assume that documentation and implementation are perfectly synchronized.
5. Treat the actual source code and tests as the final authority for current implementation details.
6. Preserve the architecture unless a change is justified.
7. Implement one coherent milestone at a time.
8. Test each milestone before moving to the next.
9. Keep the system runnable after every major change.
10. Update this document whenever a major architectural decision, milestone completion, limitation, or workflow changes.


## 33. Definition of a Successful Final System

The completed ZombieShield system should demonstrate this complete flow:

1. Discover APIs from multiple sources.
2. Normalize and deduplicate discovered APIs.
3. Track versions and source observations.
4. Maintain a centralized API inventory.
5. Classify API lifecycle states.
6. Assess API security risk.
7. Correlate relevant threat intelligence.
8. Simulate controlled security scenarios.
9. Make explainable security decisions.
10. Display the results through a usable dashboard.
11. Validate detection performance using a controlled test environment.
12. Produce measurable accuracy, precision, recall, F1, false-positive, and false-negative results.

The final implementation should be technically credible, demonstrable, explainable, and maintainable.