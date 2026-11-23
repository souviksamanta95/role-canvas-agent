# Day-to-day development. Two modes:
#   make dev        everything in Docker (same as the quickstart)
#   make dev-local  Postgres and Redis in Docker, backend/agent/frontend run natively with reload

COMPOSE := docker compose

# Host ports published by docker-compose.override.yml (loopback only).
DB_HOST_PORT    ?= 5433
REDIS_HOST_PORT ?= 6380

# Load .env into the environment of every recipe (only the keys it defines).
-include .env
ENV_KEYS := $(shell [ -f .env ] && sed -n 's/^\([A-Z][A-Z0-9_]*\)=.*/\1/p' .env)
export $(ENV_KEYS)

# Native processes reach the containers through the loopback ports, not the Compose hostnames.
# Target-specific exports work the same on every OS (no inline VAR=value shell syntax).
dev-backend dev-agent manage: export POSTGRES_HOST := 127.0.0.1
dev-backend dev-agent manage: export POSTGRES_PORT := $(DB_HOST_PORT)
dev-backend dev-agent manage: export REDIS_URL     := redis://127.0.0.1:$(REDIS_HOST_PORT)/0

# Dependencies of the native targets. dev-local starts them once and then passes DEV_DEPS=
# to the parallel sub-make so they are not started concurrently.
DEV_DEPS ?= db redis

.PHONY: manage migrate seed superuser dev-token dev up down restart logs ps db redis db-stop redis-stop db-shell redis-cli db-reset \
        dev-local dev-backend dev-agent dev-frontend open

# ---- everything in Docker ----------------------------------------------------------------

dev: _need-env ## Run ALL services in Docker (foreground, rebuilds images)
	$(COMPOSE) up --build

up: _need-env ## Run ALL services in Docker (background, wait until healthy)
	$(COMPOSE) up --build -d --wait

down: ## Stop all Docker services (keeps the database volume)
	$(COMPOSE) down

restart: ## Restart all Docker services
	$(COMPOSE) restart

logs: ## Follow logs of all Docker services (make logs S=agent for one)
	$(COMPOSE) logs -f $(S)

ps: ## Show service status
	$(COMPOSE) ps

# ---- data stores -------------------------------------------------------------------------

db: _need-env ## Start Postgres only (wait until healthy)
	$(COMPOSE) up -d --wait postgres

redis: _need-env ## Start Redis only (wait until healthy)
	$(COMPOSE) up -d --wait redis

db-stop: ## Stop Postgres
	$(COMPOSE) stop postgres

redis-stop: ## Stop Redis
	$(COMPOSE) stop redis

db-shell: ## psql shell as the owner role
	$(COMPOSE) exec postgres sh -c 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

redis-cli: ## redis-cli shell
	$(COMPOSE) exec redis redis-cli

db-reset: ## DESTROY the Postgres volume and start fresh (asks first)
	@printf "This deletes ALL local database data. Type 'yes' to continue: "; \
	read answer; [ "$$answer" = "yes" ] || { echo "Aborted."; exit 1; }
	$(COMPOSE) down --volumes
	$(COMPOSE) up -d --wait postgres redis

# ---- native processes (hot reload) -------------------------------------------------------

dev-local: _need-env ## Postgres + Redis in Docker, backend + agent + frontend native with reload
	@$(COMPOSE) stop backend agent frontend >/dev/null 2>&1 || true
	@$(MAKE) --no-print-directory db redis
	@echo "Starting backend (:8000), agent (:8001) and frontend (:3000). Ctrl+C stops them."
	@$(MAKE) --no-print-directory -j3 DEV_DEPS= dev-backend dev-agent dev-frontend

dev-backend: $(DEV_DEPS) ## Run Django natively with autoreload on :8000
	cd backend && $(VENV_BIN_BACKEND)/python manage.py migrate --noinput
	cd backend && $(VENV_BIN_BACKEND)/python manage.py runserver 0.0.0.0:8000

dev-agent: $(DEV_DEPS) ## Run FastAPI natively with autoreload on :8001
	cd agent && $(VENV_BIN_AGENT)/uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

dev-frontend: ## Run the Vite dev server on :3000
	cd frontend && $(NVM_USE) npm run dev

# ---- Django management (run natively against the Docker database) -------------------------

manage: $(DEV_DEPS) ## Run any manage.py command: make manage CMD="showmigrations"
	cd backend && $(VENV_BIN_BACKEND)/python manage.py $(CMD)

migrate: ## Apply database migrations
	@$(MAKE) --no-print-directory manage CMD=migrate

seed: ## Load demo departments, roles, datasets, grants and synthetic demo tables
	@$(MAKE) --no-print-directory manage CMD=migrate
	@$(MAKE) --no-print-directory DEV_DEPS= manage CMD=seed_access
	@$(MAKE) --no-print-directory DEV_DEPS= manage CMD=seed_demo_tables

superuser: ## Create a Django admin user (email + password, for /admin/)
	@$(MAKE) --no-print-directory manage CMD=createsuperuser

dev-token: ## Dev-only JWT for a user without Google: make dev-token EMAIL=you@example.com
	@test -n "$(EMAIL)" || { echo "Usage: make dev-token EMAIL=you@example.com"; exit 1; }
	@$(MAKE) --no-print-directory manage CMD="issue_dev_token $(EMAIL)"

open: ## Open the frontend in your browser
	$(OPEN) http://localhost:3000

VENV_BIN_BACKEND := .venv/$(VENV_BIN)
VENV_BIN_AGENT   := .venv/$(VENV_BIN)

.PHONY: _need-env
_need-env:
	@[ -f .env ] || { echo "ERROR: .env is missing. Run: make env"; exit 1; }
