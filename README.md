# Neara's Buildbot

## Overview

This project is a containerized setup for a Buildbot-based service with multiple components, including an API server, a job manager, Redis, and a Docker-in-Docker (DinD) service. This project uses `docker-compose` to orchestrate the different services and their configurations, ensuring seamless communication and management. The services run in isolated networks (`frontend` and `backend`) and persistent volumes are used for data and certificates storage.

## Requirements

Before you begin, ensure that you have the following tools installed:

- **Docker** (v20.10 or higher)
- **Docker Compose** (v1.27 or higher)
- **(Optional for devcontainers) GoLang Docker Credential Helper** (v0.6.4 or higher)

Ensure that your system has access to the necessary network and storage configurations.

## How to Build and Run the Project

Follow the steps below to get the project running in your local environment.

### Set Up Environment Variables

Ensure you have a `.env` file in the root of your project directory (the default `.env` is available [here](./.env). This file should contain any necessary environment variables required by the services.

## Building and Running Buildbot

### Makefile

A `Makefile` was created to simplify the setup and execution of the project. Here's how you can use it:

1. **Set Up Environment**:
   To set up the environment, install dependencies, and choose how to run the app, execute:

   ```bash
   make build
   ```

   This will:

   - Check if Miniconda and Docker are installed.
   - Prompts the user to confirm the installation of Miniconda and Docker if not found.
   - Set up a Conda environment (`buildbot`) with Python 3.11 if it doesn’t exist yet.
   - Install dependencies using Poetry.
   - Prompts the user to choose whether to run the app via Docker Compose or manually.
   - If running manually, it starts Redis, the TaskIQ scheduler, and the Buildbot API.

2. **Run**:

   - If you want to run the app using Docker Compose, simply run:

   ```bash
   make run_docker
   ```

   - To run the app locally using FastAPI and Debugpy, run:

   ```bash
   make run_local
   ```

   - To build and choose how to run the app, run:

   ```bash
   make run
   ```

### Docker Compose

With Docker Compose, you can build and run the services as follows:

```bash
docker-compose up --build
```

This will build the images defined in the `Dockerfile`, start all the containers, and set up the services as per the `docker-compose.yml` file. The `--build` flag ensures that the containers are built before starting.

#### Stopping the Services

When you want to stop the services, simply run:

```bash
docker-compose down
```

This will stop and remove the containers. To remove containers and volumes, you can use:

```bash
docker-compose down -v
```

#### Cleanup

To remove unused images, volumes, and networks, run:

```bash
docker system prune -a --volumes
```

This command will remove all unused containers, networks, volumes, and images.

### TaskIQ Dependency

Note that taskIQ must be running for the app to function properly. The scheduler service is started automatically in the background via a vscode pre-launch task (run-scheduler). To start the scheduler manually, run:

```bash
conda run -v --live-stream -n buildbot env PYTHONPATH=buildbot taskiq scheduler app.background.broker:scheduler
```

## Services

The project includes four main services:

1. **API** - Exposes the Buildbot API and manages interactions.
2. **Job Manager** - Handles background tasks and job scheduling.
3. **Redis** - Acts as a message broker between the components.
4. **Docker (DinD)** - Provides Docker-in-Docker functionality for tasks requiring Docker commands.

### Service Breakdown:

- **api**: Exposes a REST API to interact with Buildbot. It connects to both the frontend and backend networks, maps port 8000, and uses environment variables and certificates.
- **job-manager**: Manages background tasks and schedules jobs. It connects to the backend network and relies on Redis for communication.
- **redis**: Redis instance that acts as a broker between services.
- **docker**: Provides Docker-in-Docker (DinD) for containerized Docker tasks. It requires privileged access.
