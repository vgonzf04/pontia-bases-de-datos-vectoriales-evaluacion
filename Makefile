SHELL := /bin/bash

# Configuración
PYTHON_VERSION := $(shell tr -d '[:space:]' < .python-version)
KERNEL_NAME := aurum-market
KERNEL_DISPLAY_NAME := Python (Aurum Market)

export PATH := $(HOME)/.local/bin:$(HOME)/.cargo/bin:$(PATH)

.PHONY: setup lab clean

# Preparar el entorno
setup:
	@echo "Preparando el entorno..."

	@if ! command -v uv >/dev/null 2>&1; then \
		echo "Instalando uv..."; \
		set -o pipefail; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	fi

	uv python install "$(PYTHON_VERSION)"
	uv sync --all-extras --python "$(PYTHON_VERSION)"

	@if [ ! -f .env ]; then \
		cp .env.example .env; \
	fi

	uv run python -m ipykernel install --user \
		--name "$(KERNEL_NAME)" \
		--display-name "$(KERNEL_DISPLAY_NAME)"

	@echo "Entorno preparado. Ejecuta 'make lab'."

# Iniciar JupyterLab
lab:
	uv run jupyter lab notebooks

# Eliminar el entorno virtual
clean:
	rm -rf .venv

