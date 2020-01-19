from .base import BuilderBase
from .cmake import CMakeBuilder
from .autotools import AutotoolsBuilder
from .qmake import QMakeBuilder


def get_builder_by_name(name: str, config: dict) -> BuilderBase:
    if name == "cmake":
        return CMakeBuilder.from_dict(config)

    if name == "qmake":
        return QMakeBuilder.from_dict(config)

    raise ValueError("could not find matching builder for name: {}".format(name))


__all__ = ("CMakeBuilder", "QMakeBuilder", "get_builder_by_name",)
