# One-time setup: check prerequisites, create .env, install all dependencies.

.PHONY: setup check-prereqs check-python check-poetry check-node check-docker env \
        install install-backend install-agent install-frontend hooks

setup: check-prereqs env install hooks ## Check prerequisites, create .env, install everything
	@echo ""
	@echo "Setup complete. Next steps:"
	@echo "  1. Edit .env: set OPENROUTER_API_KEY and replace the change-me values."
	@echo "  2. make dev          (everything in Docker)"
	@echo "     make dev-local    (db + redis in Docker, apps run natively with reload)"

check-prereqs: check-python check-poetry check-node check-docker ## Verify required tools are installed

check-python:
	@$(PY312) --version 2>&1 | grep -q "Python 3\.12" || { \
	  echo "ERROR: Python 3.12 not found (tried: $(PY312))."; \
	  echo "  Install: $(HINT_PYTHON)"; exit 1; }
	@echo "ok   python  $$($(PY312) --version 2>&1)"

check-poetry:
	@$(POETRY) --version 2>/dev/null | grep -Eq "version ([2-9]|[1-9][0-9])\." || { \
	  echo "ERROR: Poetry 2.x required (found: $$($(POETRY) --version 2>&1 | head -1))."; \
	  echo "  Install: $(HINT_POETRY)"; exit 1; }
	@echo "ok   poetry  $$($(POETRY) --version)"

check-node:
	@cd frontend && $(NVM_USE) \
	  want="v$$(tr -d 'v\r\n' < .nvmrc)"; have="$$(node --version 2>/dev/null)"; \
	  [ "$$have" = "$$want" ] || { \
	    echo "ERROR: Node $$want required (found: $${have:-none})."; \
	    echo "  Install: $(HINT_NODE)"; exit 1; }; \
	  echo "ok   node    $$have (npm $$(npm --version))"

check-docker:
	@docker compose version >/dev/null 2>&1 || { \
	  echo "ERROR: docker compose not found."; echo "  Install: $(HINT_DOCKER)"; exit 1; }
	@echo "ok   docker  $$(docker --version)"

env: ## Create .env from .env.example (with a generated Django secret) if missing
	@$(PY312) scripts/init_env.py

install: install-backend install-agent install-frontend ## Install all dependencies

# The venv is created explicitly with Python 3.12 and exported as VIRTUAL_ENV so Poetry
# installs into it instead of picking whatever `python` is first on PATH.
install-backend: export VIRTUAL_ENV := $(CURDIR)/backend/.venv
install-agent: export VIRTUAL_ENV := $(CURDIR)/agent/.venv

install-backend: ## Install backend dependencies into backend/.venv
	@[ -d backend/.venv ] || $(PY312) -m venv backend/.venv
	cd backend && $(POETRY) install

install-agent: ## Install agent dependencies into agent/.venv
	@[ -d agent/.venv ] || $(PY312) -m venv agent/.venv
	cd agent && $(POETRY) install

install-frontend: ## Install frontend dependencies (npm ci)
	cd frontend && $(NVM_USE) npm ci

hooks: ## Install pre-commit hooks (ruff, gitleaks) if pre-commit is available
	@if command -v pre-commit >/dev/null 2>&1; then pre-commit install; \
	else echo "skip pre-commit not installed. Install: pipx install pre-commit, then: make hooks"; fi
