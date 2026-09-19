# ZombieShield architecture

The project has three runtime services: a React/Vite frontend served by Nginx, a FastAPI backend, and PostgreSQL. Docker Compose provides the local runtime boundary and a named PostgreSQL volume preserves local database data.

The backend is separated into configuration, database session/base, SQLAlchemy models, Pydantic schemas, services, and HTTP routes. `apis` is the central persisted model. Discovery, normalization/reconciliation, lifecycle classification, and risk assessment are separate services sharing this inventory boundary.

The risk layer uses three services: feature extraction, deterministic rules, and synthetic-data ML scoring. The `GradientBoostingClassifier` is trained from controlled synthetic scenarios and complements deterministic findings; it does not represent production incidents or security accuracy. Unknown authentication, TLS, rate-limiting, and PII evidence remains explicit and is not fabricated.

The threat intelligence layer stores source-attributed advisories and creates findings only when an API's explicitly supplied component/version exactly matches an advisory's affected-version list. Findings remain tied to their source and feed a finding-count signal into the next risk assessment; no external feed, CVE, or version-range inference is fabricated.

The frontend has a small application shell, page components, and a typed HTTP client. It renders inventory, lifecycle, and persisted risk scores/findings obtained from the backend; an empty inventory remains empty until a record is created through the API.
