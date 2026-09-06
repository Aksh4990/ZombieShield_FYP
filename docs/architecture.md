# Foundation architecture

The project has three runtime services: a React/Vite frontend served by Nginx, a FastAPI backend, and PostgreSQL. Docker Compose provides the local runtime boundary and a named PostgreSQL volume preserves local database data.

The backend is separated into configuration, database session/base, SQLAlchemy models, Pydantic schemas, services, and HTTP routes. `apis` is the only persisted model in this milestone. Future discovery, lifecycle assessment, risk assessment, and remediation modules can be added beside these layers without changing the current API inventory boundary.

The frontend has a small application shell, page components, and a typed HTTP client. It renders only data obtained from the backend; an empty inventory remains empty until a record is created through the API.
