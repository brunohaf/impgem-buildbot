# Neara's Buildbot

## **Overview:**

Buildbot is designed as a modular and scalable job execution system, drawing inspiration from GitHub Actions. It leverages containerized execution with Docker and TaskIQ for background job management, priotizing isolation, scalability, and maintainability.

_NOTE: This project used [s3rius/Fast-API-Template](https://github.com/s3rius/FastAPI-template) as a starting point._

## **Code Structure:**

Buildbot follows a layered architecture to separate concerns and ensure maintainability:

1. **API Layer:** Handles user requests and exposes RESTful endpoints.
2. **Service Layer:** Implements business logic and interacts with repositories.
3. **Repository Layer:** Manages data storage and retrieval.
4. **Core Layer:** Defines shared utilities, settings, and domain models.
5. **Background Layer:** Manages asynchronous job execution and task scheduling.

### **Known Limitations:**

- A routine is needed to reschedule jobs that failed to enqueue. This can be achieved by querying Redis for pending jobs and invoking the Job Manager, similar to the Job Service.
- A cleanup routine could remove stray containers and prevent resource starvation. While containers are purged after artifact collection, a simple `docker container prune` every hour would suffice for an MVP.

### **Trade-offs:**

- The design draws inspiration from GitHub Actions' container-based runners, utilizing [Docker-Py](https://github.com/docker/docker-py) and [TaskIQ](https://taskiq-python.github.io/) for job management. While Python’s `subprocess` + `user namespaces` or `chroot` were considered for job execution, `docker-py` was chosen for its superior isolation, albeit at the cost of additional complexity. This decision was driven by the need to keep the job runner isolated from both the host machine and the API server.

  - Additionally, `docker-py` proved beneficial in streamlining the retrieval of job artifacts and capturing stdout/stderr from containers.
  - The design uses base64-encoded commands passed to a Docker container. The application decodes and formats the command into a `run.sh` script, which is executed and then deleted to avoid residual files.

- Redis was selected as the data store due to its simplicity, the limited number of entities involved, and the straightforward relationship between jobs and tasks.

- TaskIQ was adopted for scheduling and managing background jobs, ensuring API responsiveness while keeping TaskIQ workers isolated from FastAPI’s main thread.

- The design emphasizes adherence to SOLID principles and clean code, particularly through the use of interfaces and constructor dependency injection. This approach ensures cohesion, testability, and scalability while maintaining alignment with the open-closed principle. However, it introduces additional complexity due to the reliance on abstract classes and constructor dependency injection.

  - A microservice architecture was implemented to separate the API, job manager, and storage, enhancing scalability and maintainability. For simplicity, the job manager uses the same image as the API Server.

- Although [Docker-in-Docker (DinD)](https://hub.docker.com/_/docker) offers a viable development environment, its use in production environments, particularly in CI systems, has been discouraged. Jérôme Petazzoni, the tool’s author, highlighted these concerns in [an article](https://jpetazzo.github.io/2015/09/03/do-not-use-docker-in-docker-for-ci/), suggesting that alternative approaches should be considered for production deployments.

## **Improvements:**

- Decorators can reduce verbosity in methods by separating logging from business logic.
- More granular exception handling will improve troubleshooting. While critical methods are covered, exceptions from third-party packages often have vague messages and are caught far from their source. Using specific exceptions and defining clear error messages is recommended.
- `docker-py` supports real-time stdout/stderr capture with `container.logs(stream=True)`, which could enable a WebSocket endpoint indexed by job ID for a CI/CD-like experience. Logs are collected when artifacts are retrieved, but no endpoints currently expose them to users.
