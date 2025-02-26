# Makefile for setting up the environment and running the app

.ONESHELL:

SHELL := /bin/bash

# Check if Miniconda is installed
MINICONDA_BIN := $(shell which conda)

# Check if Docker is installed
DOCKER_BIN := $(shell which docker)

# Targets
.PHONY: check_miniconda check_docker install_miniconda install_docker setup_env install_deps run

# Activate the conda environment. Usage: @$$(CONDA_ACTIVATE) <env>
CONDA_ACTIVATE = source $$(conda info --base)/etc/profile.d/conda.sh ; conda activate ; conda activate
CONDA_ENV = buildbot

# Check if Miniconda is installed
check_miniconda:
	@if [ ! -f "$(MINICONDA_BIN)" ]; then \
		echo "Conda not found."; \
		read -p "Do you want to install Miniconda? (y/n): " response; \
		if [ "$$response" = "y" ]; then \
			$(MAKE) install_miniconda; \
		else \
			exit 1; \
		fi \
	fi

# Install Miniconda
install_miniconda:
	@echo "Installing Miniconda..."
	@curl -fsSL https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o miniconda.sh
	@bash miniconda.sh -b -p $(HOME)/miniconda3
	@echo "Miniconda installed. Please restart your terminal or source ~/.bashrc to use conda."


# Check if Docker is installed
check_docker:
	@if [ -z "$(DOCKER_BIN)" ]; then \
		echo "Docker not found."; \
		read -p "Do you want to install Docker? (y/n): " response; \
		if [ "$$response" = "y" ]; then \
			$(MAKE) install_docker; \
		else \
			exit 1; \
		fi \
	fi

# Install Docker
install_docker:
	@echo "Installing Docker..."
	@curl -fsSL https://get.docker.com | sh
	@echo "Docker installed. Please start the Docker service."

# Setup conda environment only if not already created
setup_env:
	@echo "Checking if conda environment '${CONDA_ENV}' exists..."
	@if ! conda info --envs | grep -q '${CONDA_ENV}'; then \
		echo "Setting up conda environment '${CONDA_ENV}' with Python 3.11..."; \
		conda create -n ${CONDA_ENV} python==3.11 poetry debugpy python-dotenv -y; \
		echo "Environment '${CONDA_ENV}' created."; \
	else \
		echo "Conda environment 'buildbot' already exists."; \
	fi

# Install dependencies with Poetry
install_deps:
	@$(CONDA_ACTIVATE) $(CONDA_ENV)
	@echo "Installing dependencies using Poetry..."
	@poetry install
	@echo "Dependencies installed."

# Prompt user to choose the app running method
ask_run_method:
	@echo "Choose how to run the app:"
	@select method in "Docker-Compose" "Manual"; do \
		if [ "$$method" = "Docker-Compose" ]; then \
			$(MAKE) run_docker; \
		elif [ "$$method" = "Manual" ]; then \
			$(MAKE) run_local; \
		fi; \
	done

# Run app with Docker Compose
run_docker:
	@$(CONDA_ACTIVATE) $(CONDA_ENV)
	@dotenv -f .env set BUILDBOT_REDIS_SETTINGS__HOST redis > /dev/null
	@echo "Running the app using Docker Compose..."
	@cd $(PWD) && docker-compose up

# Run Redis container only if not already running
run_redis:
	@echo "Checking if Redis container 'redis' is already running..."
	@if ! docker ps --filter "name=redis" --format "{{.Names}}" | grep -q 'redis'; then \
		echo "Starting Redis container..."; \
		docker run -d --name redis -p 6379:6379 redis; \
		echo "Redis container started."; \
	else \
		echo "Redis container 'redis' is already running."; \
	fi

start_scheduler_local:
	@$(CONDA_ACTIVATE) $(CONDA_ENV)
	@echo "Starting TaskIQ scheduler..."
	@nohup conda run -v -n buildbot env PYTHONPATH=buildbot taskiq scheduler app.background.broker:scheduler >> scheduler.log 2>&1 &
	@if [ $$? -eq 0 ]; then \
			echo "Scheduler started successfully"; \
		else \
			echo "Failed to start scheduler" >> scheduler.log; \
		fi


# Run app manually using FastAPI and Debugpy
run_local:
	@$(CONDA_ACTIVATE) $(CONDA_ENV)
	@$(MAKE) run_redis
	@$(MAKE) start_scheduler_local
	@dotenv -f .env set BUILDBOT_REDIS_SETTINGS__HOST localhost > /dev/null
	@dotenv -f $(CURDIR)/.env run python -m debugpy --listen 5678 --wait-for-client buildbot/__main__.py
	@echo "Buildbot API started locally."

# Stop the local app
stop_local:
	@ps -C dotenv -o pid --no-header | sed 's/^[[:space:]]*//' | xargs kill -9 > /dev/null  2>&1
	@ps -C taskiq -o pid --no-header | sed 's/^[[:space:]]*//' | xargs kill -9 > /dev/null  2>&1

# Stop the Docker app
stop_docker:
	@cd $(PWD) && docker-compose down

# Build
build: check_miniconda setup_env check_docker install_deps

# Run the app
run: build ask_run_method

