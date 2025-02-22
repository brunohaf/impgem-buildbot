import docker

_docker = docker.from_env()


class ContainerStatus:
    """Docker container status."""

    RUNNING = "running"
    STOPPED = "stopped"
    EXITED = "exited"


class Labels:
    """Docker container labels."""

    JOB_ID = "job_id"


def get_docker_client() -> docker.DockerClient:
    """Returns a Docker client."""
    return _docker
