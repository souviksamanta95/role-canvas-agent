# The same checks CI runs.

.PHONY: lint test typecheck check build-frontend

lint: ## ruff check + format check for backend and agent
	cd backend && .venv/$(VENV_BIN)/ruff check . && .venv/$(VENV_BIN)/ruff format --check .
	cd agent && .venv/$(VENV_BIN)/ruff check . && .venv/$(VENV_BIN)/ruff format --check .

typecheck: ## mypy for backend and agent
	cd backend && .venv/$(VENV_BIN)/mypy .
	cd agent && .venv/$(VENV_BIN)/mypy .

test: ## pytest for backend and agent
	cd backend && .venv/$(VENV_BIN)/pytest -q
	cd agent && .venv/$(VENV_BIN)/pytest -q

build-frontend: ## Production build of the frontend
	cd frontend && $(NVM_USE) npm run build

check: lint typecheck test build-frontend ## Run everything CI runs
