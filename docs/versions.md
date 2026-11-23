# Versions

Chosen on 2026-11-22. Versions are pinned so builds are repeatable. Exact resolved
versions for Python packages live in `backend/poetry.lock` and `agent/poetry.lock`; for
the frontend in `frontend/package-lock.json`.

| Component | Version | Why |
|---|---|---|
| Python | 3.12 (`~3.12`) | Required by Django 6.1 (needs 3.12 or newer). Also supported by Django REST Framework, FastAPI, psycopg 3 and redis-py, checked against their PyPI metadata. |
| Django | 6.1.x (locked 6.1.3) | Current release line at scaffold time. |
| Django REST Framework | 3.18.x (locked 3.18.3) | Latest release; declares Python 3.12 support. |
| FastAPI | 0.165.x (locked 0.165.0) | Latest release; requires Python 3.11 or newer. |
| psycopg | 3.3.x (locked 3.3.9) | Psycopg 3 as requested; supports PostgreSQL 17. |
| redis-py | 7.x (locked 7.4.1) | Latest major; requires Python 3.10 or newer. |
| gunicorn | 23.x | Production WSGI server for Django. |
| uvicorn | 0.35.x | ASGI server for FastAPI. |
| djangorestframework-simplejwt | 5.5.x (locked 5.5.1) | JWT issuing and verification. Its metadata lists Django up to 5.2, so it is covered by our own tests on Django 6.1 (all pass). |
| google-auth | 2.x (locked 2.63.1) | Verifies Google ID tokens for sign-in. |
| django-cors-headers | 4.x | Lets the frontend origin call the API. |
| whitenoise | 6.x | Serves the Django admin's static files from gunicorn. |
| PostgreSQL | 17.12 (`postgres:17.12-alpine`) | Newest 17.x patch tag on Docker Hub when checked; psycopg 3.3 supports 17. Pinned tag, never `latest`. |
| Redis | 7.4.9 (`redis:7.4.9-alpine`) | Newest 7.4.x patch tag when checked. Redis 7 as requested. |
| Node.js | 26.13.1 | Current LTS ("Lithium") per nodejs.org when checked. Pinned in `.nvmrc`, `frontend/.nvmrc` and `frontend/Dockerfile`. |
| Poetry | 2.5.2 | Pinned in Dockerfiles (build stage only) and CI. Poetry is not present in the final images. |
| Vite / React / TypeScript | Vite 8.x, React 19.x, TypeScript 7.x | Latest releases at scaffold time; exact versions in `package-lock.json`. |

## Notes

- Upgrading Node when 26 is no longer the newest LTS means editing `.nvmrc`,
  `frontend/.nvmrc` and `frontend/Dockerfile` together.
- The Postgres owner role is the image's bootstrap superuser (`POSTGRES_USER`). Splitting
  out a non-superuser owner for migrations is a hardening step to consider before deployment.
