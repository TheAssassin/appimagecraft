import os.path
import shlex
from collections import OrderedDict

from appimagecraft._util import convert_kv_list_to_dict
from ..generators import BashScriptGenerator, AppImageBuildScriptGenerator, PrePostBuildScriptsGenerator
from . import CommandBase
from ..builders import *
from .. import _logging


# Generates build scripts based on configuration
class GenerateScriptsCommand(CommandBase):
    def __init__(self, config: dict, project_root_dir: str, build_dir: str, builder_name: str):
        super().__init__(config, project_root_dir, build_dir, builder_name)

        self._logger = _logging.get_logger("genscripts")

    def set_build_dir(self, build_dir: str):
        self._build_dir = build_dir

    def _generate_main_script(self, build_scripts: dict):
        project_config = self._config["project"]

        main_script_path = os.path.join(self._build_dir, "build.sh")

        main_script_gen = BashScriptGenerator(main_script_path)

        def export_variable(var_name, var_value):
            main_script_gen.add_line("export {}={}".format(var_name, var_value))

        # export PROJECT_ROOT and BUILD_DIR so they can be used by scripts etc.
        # convenience feature
        main_script_gen.add_line("# convenience variables, may be used in config file")
        export_variable("PROJECT_ROOT", shlex.quote(self._project_root_dir))
        export_variable("BUILD_DIR", shlex.quote(self._build_dir))

        # $VERSION is used by various tools and may also be picked up by the build system of the target app
        project_version = project_config.get("version")
        if project_version is not None:
            export_variable("VERSION", shlex.quote(project_version))
        else:
            project_version_cmd = project_config.get("version_command")
            if project_version_cmd is not None:
                export_variable("VERSION", "$({})".format(project_version_cmd))

        main_script_gen.add_line()

        build_env_vars = self._config.get("environment")
        if build_env_vars is not None:
            main_script_gen.add_line("# user specified environment variables")

            if isinstance(build_env_vars, list):
                build_env_vars = convert_kv_list_to_dict(build_env_vars)

            for k, v in build_env_vars.items():
                export_variable(k, v)

            main_script_gen.add_line()

        # header
        main_script_gen.add_lines([
            "# call pre-build script (if available)",
            "[ -f pre_build.sh ] && bash pre_build.sh",
            "",
            "# make sure to be in the build dir",
            "cd {}".format(shlex.quote(self._build_dir)),
            "",
            "# create AppDir so that tools which are sensitive to that won't complain",
            "mkdir -p AppDir",
            "",
        ])

        # add entry for main builder
        # use subshell to set SHLVL properly, which makes output with -x prettier
        main_script_gen.add_lines([
            "# call script for main builder {}".format(self._builder_name),
            "(source {})".format(build_scripts[self._builder_name]),
        ])
        del build_scripts[self._builder_name]

        # generate commented entries for remaining script
        if build_scripts:
            main_script_gen.add_line(
                "# additional available builders (call appimagecraft with --builder <name> to switch)")
            for builder_name, script in build_scripts.items():
                main_script_gen.add_line("# script for builder {}".format(builder_name))
                main_script_gen.add_line("#source {}\n".format(script))

        main_script_gen.add_lines([
            "",
            "# call post-build script (if available)",
            "[ -f post_build.sh ] && bash post_build.sh",
            "",
        ])

        # set up AppImage build script
        appimage_build_config = self._config.get("appimage", None)

        appimage_script_path = os.path.join(self._build_dir, "build-appimage.sh")

        appimage_script_gen = AppImageBuildScriptGenerator(appimage_build_config)
        appimage_script_gen.build_file(appimage_script_path)

        # call AppImage build script
        main_script_gen.add_line("# build AppImage")
        main_script_gen.add_line("(source {})".format(shlex.quote(appimage_script_path)))

        # (re-)create script file
        main_script_gen.build_file()

    def _generate_builder_scripts(self) -> dict:
        build_config: dict = self._config["build"]

        # generate build configs for every
        builders_map = {
            "cmake": CMakeBuilder,
        }

        build_scripts = {}

        for builder_name in build_config.keys():
            try:
                builder = builders_map[builder_name](build_config[builder_name])
            except KeyError:
                self._logger.error("No builder named {} available, skipping".format(builder_name))
                continue
            else:
                script_filename = builder.generate_build_script(self._project_root_dir, self._build_dir)
                build_scripts[builder_name] = script_filename

        return build_scripts

    def _generate_pre_post_build_scripts(self):
        gen = PrePostBuildScriptsGenerator(self._config.get("scripts", None))
        gen.build_files(self._build_dir)

    def run(self):
        self._logger.info("Generating build scripts in {}".format(self._build_dir))

        if self._build_dir is None:
            raise ValueError("build dir has not been set")

        self._generate_pre_post_build_scripts()

        build_scripts = self._generate_builder_scripts()

        self._generate_main_script(build_scripts)
