from abc import ABCMeta
from typing import Any, Dict, Type, TypeVar

T = TypeVar("T", bound="Singleton")


class SingletonMeta(type):
    _instances: Dict[Type["Singleton"], "Singleton"] = {}

    def __call__(cls: Type[T], *args: Any, **kwargs: Any) -> T:
        """Returns the singleton instance of the class."""
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class Singleton(metaclass=SingletonMeta):
    pass


class AbstractSingletonMeta(SingletonMeta, ABCMeta):
    pass
