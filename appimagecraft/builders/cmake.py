import os.path
import re
import shlex

from ..generators.bash_script import BashScriptGenerator
from .._util import get_appdir_path, convert_kv_list_to_dict
from . import BuilderBase


class CMakeBuilder(BuilderBase):
    _script_filename = "build-cmake.sh"

    def __init__(self, config: dict = None):
        super().__init__()

        for cmake_arg in self._get_configure_extra_variables().keys():
            self._validate_cmake_arg_name(cmake_arg)

    def _get_configure_extra_variables(self) -> dict:
        default_vars = {
            "CMAKE_INSTALL_PREFIX": "/usr",
            "CMAKE_BUILD_TYPE": "Release",
        }

        data = self._builder_config.get("extra_variables", None) or {}

        # allow for KEY=Value scheme for extra_variables
        if isinstance(data, list):
            data = convert_kv_list_to_dict(data)

        rv = dict()
        rv.update(default_vars)
        rv.update(data)

        return rv

    @staticmethod
    def from_dict(data: dict):
        # TODO!
        raise NotImplementedError()

    @staticmethod
    def _validate_cmake_arg_name(name):
        # TODO
        if " " in name:
            raise ValueError("Spaces are not allowed in CMake argument names")

    def _get_source_dir(self, project_root_dir):
        source_dir = self._builder_config.get("source_dir", None)

        if not source_dir:
            return project_root_dir

        if not os.path.isabs(source_dir):
            source_dir = os.path.join(project_root_dir, source_dir)

        return source_dir

    def _generate_cmake_command(self, project_root_dir: str):
        args = ["cmake"]

        for key, value in self._get_configure_extra_variables().items():
            self._validate_cmake_arg_name(key)

            escaped_value = shlex.quote(value)

            args.append("-D{}={}".format(key, escaped_value))

        source_dir = self._get_source_dir(project_root_dir)
        args.append(source_dir)

        return " ".join(args)

    def generate_build_script(self, project_root_dir: str, build_dir: str) -> str:
        script_path = os.path.join(build_dir, self.__class__._script_filename)

        generator = BashScriptGenerator(script_path)

        generator.add_lines([
            "# make sure we're in the build directory",
            "cd {}".format(shlex.quote(build_dir)),
            "",
            "# build in separate directory to avoid a mess in the build dir",
            "mkdir -p cmake-build",
            "cd cmake-build",
            "",
            "# set up build",
            self._generate_cmake_command(project_root_dir),
            "",
            "# build project",
            # TODO: use cmake --build somehow, also for install call below
            "make -j $(nproc)",
            "",
            "# install binaries into AppDir (requires correct CMake install(...) configuration)",
            "make install DESTDIR={}".format(shlex.quote(get_appdir_path(build_dir))),
        ])

        # optional support for CPack
        # allows projects to also build packages, making use of appimagecraft features like auto-created clean build
        # directories, Docker container builds, ...
        cpack_args: dict = self._builder_config.get("cpack", False)

        # caution: must check for non-None value (like False) explicitly, an empty value is allowed and would be
        # represented as None
        if cpack_args is not False:
            generator.add_lines([
                "",
                "# build packages with cpack",
            ])

            cpack_generators: dict = None

            if cpack_args is not None:
                cpack_generators: dict = cpack_args.get("generators")

            if cpack_generators is not None:
                if not isinstance(cpack_generators, list):
                    raise ValueError("generators: must be list")

                for gen in cpack_generators:
                    # ensure correct format
                    if not re.match(r"^[A-Z]+$", gen):
                        raise ValueError("generator in invalid format: {}".format(gen))

                    generator.add_line("cpack -V {}".format(shlex.quote(gen)))

            else:
                generator.add_line("cpack -V")

        generator.build_file()

        return os.path.basename(script_path)
