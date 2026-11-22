# OS detection. Sets DETECTED_OS and the per-OS variables used by the other makefiles.
#   macOS   : Darwin
#   Linux   : Linux (including WSL)
#   Windows : run make from Git Bash (or use WSL). Plain cmd.exe/PowerShell is not supported.

ifeq ($(OS),Windows_NT)
  DETECTED_OS := windows
else
  UNAME_S := $(shell uname -s)
  ifeq ($(UNAME_S),Darwin)
    DETECTED_OS := macos
  else ifeq ($(UNAME_S),Linux)
    DETECTED_OS := linux
  else
    DETECTED_OS := unknown
  endif
endif

# Python 3.12 launcher, location of executables inside a virtualenv, URL opener,
# and a hint for installing each prerequisite.
ifeq ($(DETECTED_OS),macos)
  PY312        ?= python3.12
  VENV_BIN     := bin
  OPEN         := open
  HINT_PYTHON  := brew install python@3.12
  HINT_POETRY  := brew install pipx && pipx install poetry==2.5.2
  HINT_NODE    := brew install nvm, then: nvm install (inside frontend/)
  HINT_DOCKER  := brew install --cask docker   (then start Docker Desktop)
else ifeq ($(DETECTED_OS),linux)
  PY312        ?= python3.12
  VENV_BIN     := bin
  OPEN         := xdg-open
  HINT_PYTHON  := sudo apt install python3.12 python3.12-venv   (or your distro's equivalent)
  HINT_POETRY  := pipx install poetry==2.5.2
  HINT_NODE    := install nvm (https://github.com/nvm-sh/nvm), then: nvm install (inside frontend/)
  HINT_DOCKER  := see https://docs.docker.com/engine/install/
else ifeq ($(DETECTED_OS),windows)
  PY312        ?= py -3.12
  VENV_BIN     := Scripts
  OPEN         := start
  HINT_PYTHON  := winget install Python.Python.3.12
  HINT_POETRY  := pipx install poetry==2.5.2
  HINT_NODE    := install nvm-windows, then: nvm install $$(cat frontend/.nvmrc) and nvm use $$(cat frontend/.nvmrc)
  HINT_DOCKER  := winget install Docker.DockerDesktop
else
  PY312        ?= python3.12
  VENV_BIN     := bin
  OPEN         := echo open this URL:
  HINT_PYTHON  := install Python 3.12
  HINT_POETRY  := pipx install poetry==2.5.2
  HINT_NODE    := install nvm and Node from frontend/.nvmrc
  HINT_DOCKER  := install Docker with Compose v2
endif

# Poetry executable (override with POETRY=/path/to/poetry).
POETRY ?= poetry

# Run npm/node under the version in frontend/.nvmrc when nvm is available (macOS, Linux).
# On Windows nvm-windows needs an elevated shell, so select the version yourself first.
ifeq ($(DETECTED_OS),windows)
  NVM_USE :=
else
  NVM_USE := export NVM_DIR="$${NVM_DIR:-$$HOME/.nvm}"; [ -s "$$NVM_DIR/nvm.sh" ] && . "$$NVM_DIR/nvm.sh" && nvm use >/dev/null 2>&1;
endif
