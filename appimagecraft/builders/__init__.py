from .base import BuilderBase
from .cmake import CMakeBuilder


def get_builder_by_name(name: str, config: dict) -> BuilderBase:
    if name == "cmake":
        return CMakeBuilder.from_dict(config)

    raise ValueError("could not find matching builder for name: {}".format(name))


__all__ = ("CMakeBuilder", "get_builder_by_name",)
