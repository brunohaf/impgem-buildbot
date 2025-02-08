from typing import Any, ClassVar, Dict, Type


class SingletonMeta(Type):
    """Metaclass for enforcing the Singleton pattern."""

    _instances: ClassVar[Dict[Type, object]] = {}

    def __call__(cls, *args: Any, **kwargs: Dict[str, Any]) -> object:
        """Returns the instance of the class."""
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
