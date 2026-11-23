# The same checks CI runs.

.PHONY: lint test typecheck check test-frontend build-frontend

lint: ## ruff check + format check for backend and agent
	cd backend && .venv/$(VENV_BIN)/ruff check . && .venv/$(VENV_BIN)/ruff format --check .
	cd agent && .venv/$(VENV_BIN)/ruff check . && .venv/$(VENV_BIN)/ruff format --check .

typecheck: ## mypy for backend and agent
	cd backend && .venv/$(VENV_BIN)/mypy .
	cd agent && .venv/$(VENV_BIN)/mypy .

test: ## pytest for backend and agent
	cd backend && .venv/$(VENV_BIN)/pytest -q
	cd agent && .venv/$(VENV_BIN)/pytest -q

test-frontend: ## Frontend unit tests (vitest)
	cd frontend && $(NVM_USE) npm test

build-frontend: ## Type-check and production build of the frontend
	cd frontend && $(NVM_USE) npm run build

check: lint typecheck test test-frontend build-frontend ## Run everything CI runs
