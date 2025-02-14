from app.repository.schemas import RepositoryBaseModel


class Task(RepositoryBaseModel):
    """Simple Task model."""

    script: str

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Task):
            return self.__super__().__eq__(other) and self.script == other.script
        return False
