# RoleCanvas developer commands. Run `make help` for the list.
# Works on macOS, Linux and Windows (from Git Bash or WSL). Needs GNU Make 3.81 or newer.

include make/os.mk
include make/setup.mk
include make/dev.mk
include make/quality.mk

.DEFAULT_GOAL := help

.PHONY: help info

help: ## Show this help
	@echo "RoleCanvas ($(DETECTED_OS))"
	@echo ""
	@grep -hE '^[a-zA-Z0-9_-]+:.*## ' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

info: ## Show detected OS and tool settings
	@echo "OS            : $(DETECTED_OS)"
	@echo "Python 3.12   : $(PY312)"
	@echo "venv bin dir  : $(VENV_BIN)"
	@echo "Poetry        : $(POETRY)"
	@echo "Open command  : $(OPEN)"
