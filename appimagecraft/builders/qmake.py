import glob
import os.path
import shlex

from ..generators.bash_script import BashScriptGenerator
from .._util import get_appdir_path, convert_kv_list_to_dict
from . import BuilderBase
from .._logging import get_logger


class QMakeBuilder(BuilderBase):
    _script_filename = "build-qmake.sh"

    def __init__(self, config: dict = None):
        super().__init__(config)

        self._logger = get_logger("qmake_builder")

    @staticmethod
    def from_dict(data: dict):
        # TODO!
        raise NotImplementedError()

    def _qenerate_qmake_command(self, project_root_dir: str):
        args = ["qmake"]

        # TODO: support for extra variables

        source_dir = self._get_source_dir(project_root_dir)

        project_file: str = self._builder_config.get("project_file")

        if not project_file:
            try:
                project_file = glob.glob(os.path.join(source_dir, "*.pro"))[0]
            except IndexError:
                raise RuntimeError("Could not find QMake project file in source dir, please specify a different source_dir or a project_file")
            else:
                self._logger.warn("project_file not specified, using first found .pro file: %s" % project_file)

        # make sure we use an absolute path
        if not os.path.isabs(project_file):
            project_file = os.path.join(source_dir, project_file)

        args.append(project_file)

        return " ".join(args)

    def generate_build_script(self, project_root_dir: str, build_dir: str) -> str:
        script_path = os.path.join(build_dir, self.__class__._script_filename)

        generator = BashScriptGenerator(script_path)

        # export environment vars listed in config
        def try_export_env_vars(key_name, raw=False):
            try:
                env_config = self._builder_config[key_name]
            except KeyError:
                pass
            else:
                try:
                    dict(env_config)
                except ValueError:
                    try:
                        iter(env_config)
                    except ValueError:
                        raise ValueError("environment config is in invalid format")
                    else:
                        env_config = convert_kv_list_to_dict(env_config)

                generator.add_line("# environment variables from {}".format(key_name))
                generator.export_env_vars(env_config, raw=raw)

                # add some space between this and the next block
                generator.add_line()

        try_export_env_vars("environment")
        try_export_env_vars("raw_environment", raw=True)

        generator.add_lines([
            "# make sure we're in the build directory",
            "cd {}".format(shlex.quote(build_dir)),
            "",
            "# build in separate directory to avoid a mess in the build dir",
            "mkdir -p qmake-build",
            "cd qmake-build",
            "",
            "# it's always a good idea to print the qmake version in use",
            "qmake --version",
            "",
            "# set up build",
            self._qenerate_qmake_command(project_root_dir),
            "",
            "# build project",
            "make -j $(nproc)",
            "",
            "# install binaries into AppDir (requires correct qmake install(...) configuration)",
            "make install INSTALL_ROOT={}".format(shlex.quote(get_appdir_path(build_dir))),
        ])

        generator.build_file()

        return os.path.basename(script_path)
