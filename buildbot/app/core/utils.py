import threading
from abc import ABCMeta
from typing import Any, ClassVar, Type, TypeVar
from weakref import WeakValueDictionary

SingletonT = TypeVar("SingletonT", bound="SingletonMeta")


# ? This is a Singleton metaclass with weak reference support
# ? for improved garbage collection. It uses a lock to ensure thread safety.
class SingletonMeta(type):
    """Thread-safe Singleton metaclass with weak reference support."""

    _instances: ClassVar[WeakValueDictionary] = WeakValueDictionary()
    _lock: ClassVar[threading.Lock] = threading.Lock()

    def __call__(cls: Type[SingletonT], *args: Any, **kwargs: Any) -> SingletonT:
        """Returns the singleton instance of the class, ensuring thread safety."""
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


class AbstractSingletonMeta(SingletonMeta, ABCMeta):
    """Thread-safe Singleton/Abstract mix-in metaclass."""
