import docker

_docker = docker.from_env()


class Labels:
    """Docker container labels."""

    JOB_ID = "job_id"


class ContainerStatus:
    """Docker container status."""

    RUNNING = "running"
    STOPPED = "stopped"
    EXITED = "exited"


def get_docker_client() -> docker.DockerClient:
    """Returns a Docker client."""
    return _docker
