import os.path
import shlex

from ..generators.bash_script import ProjectAwareBashScriptBuilder
from .._util import get_appdir_path
from . import BuilderBase


class AutotoolsBuilder(BuilderBase):
    _script_filename = "build-autotools.sh"

    def _get_configure_extra_variables(self) -> list:
        default_params = [
            "--prefix=/usr",
        ]

        configure_config = self._builder_config.get("configure", None)

        if not configure_config:
            configure_config = dict()

        extra_params = configure_config.get("extra_params", [])

        rv = list(default_params)
        rv += extra_params

        return rv

    @staticmethod
    def from_dict(data: dict):
        # TODO!
        raise NotImplementedError()

    def _get_source_dir(self, project_root_dir):
        source_dir = self._builder_config.get("source_dir", None)

        if not source_dir:
            return project_root_dir

        if not os.path.isabs(source_dir):
            source_dir = os.path.join(project_root_dir, source_dir)

        return source_dir

    def _generate_configure_command(self, project_root_dir: str):
        args = [os.path.join(self._get_source_dir(project_root_dir), "configure")]

        for param in self._get_configure_extra_variables():
            escaped_value = shlex.quote(param)

            args.append(escaped_value)

        source_dir = self._get_source_dir(project_root_dir)
        args.append(source_dir)

        return " ".join(args)

    def generate_build_script(self, project_root_dir: str, build_dir: str) -> str:
        script_path = os.path.join(build_dir, self.__class__._script_filename)

        generator = ProjectAwareBashScriptBuilder(script_path, project_root_dir, build_dir)

        generator.add_lines(
            [
                "# make sure we're in the build directory",
                "cd {}".format(shlex.quote(build_dir)),
                "",
                "# build in separate directory to avoid a mess in the build dir",
                "mkdir -p autotools-build",
                "cd autotools-build",
                "",
            ]
        )

        autogen_path = os.path.join(self._get_source_dir(project_root_dir), "autogen.sh")

        if self._builder_config.get("allow_insource"):
            generator.add_lines(
                [
                    "# in case the project uses autogen.sh, we have to call that script to generate the configure script",
                    "[ -f {0} ] && (cd {1} && {0})".format(
                        shlex.quote(autogen_path), shlex.quote(os.path.dirname(autogen_path))
                    ),
                    "",
                ]
            )
        else:
            generator.add_lines(
                [
                    "# the user needs to explicitly allow in source operations in order to be able to auto call autogen.sh",
                    "if [ -f {0} ]; then",
                    '    echo "Warning: autogen.sh found, might have to be called by us"'
                    '    echo "f so please add allow_insource: true to the autotools builder config"',
                    "fi",
                    "",
                ]
            )

        if "configure" in self._builder_config:
            generator.add_lines(
                ["# set up build directory with configure", self._generate_configure_command(project_root_dir), ""]
            )
        else:
            generator.add_lines(
                ["# configure: section not found, not generating configure call (this might be intentional)" ""]
            )

        generator.add_lines(
            [
                "# build project",
                "make -j $(nproc)",
                "",
                "# install binaries into AppDir (requires correct CMake install(...) configuration)",
                "make install DESTDIR={}".format(shlex.quote(get_appdir_path(build_dir))),
            ]
        )

        generator.build_file()

        return os.path.basename(script_path)
