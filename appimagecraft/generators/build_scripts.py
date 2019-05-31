import os.path
import shlex

from appimagecraft.validators import ShellCheckValidator, ValidationError
from ..builders import CMakeBuilder
from .._logging import get_logger
from .._util import convert_kv_list_to_dict
from . import BashScriptGenerator, AppImageBuildScriptGenerator, PrePostBuildScriptsGenerator


class AllBuildScriptsGenerator:
    def __init__(self, config: dict, project_root_dir: str, builder_name: str):
        self._config = config
        
        self._project_root_dir = project_root_dir
        self._builder_name = builder_name

        self._logger = get_logger("script_gen")

    def _generate_main_script(self, build_dir: str, build_scripts: dict) -> str:
        project_config = self._config["project"]

        main_script_path = os.path.join(build_dir, "build.sh")

        main_script_gen = BashScriptGenerator(main_script_path)

        def export_variable(var_name, var_value):
            # fixes shellcheck warning SC2155
            main_script_gen.add_line("{}={}".format(var_name, var_value))
            main_script_gen.add_line("export {}".format(var_name))

        # export PROJECT_ROOT and BUILD_DIR so they can be used by scripts etc.
        # convenience feature
        main_script_gen.add_line("# convenience variables, may be used in config file")
        export_variable("PROJECT_ROOT", shlex.quote(self._project_root_dir))
        export_variable("BUILD_DIR", shlex.quote(build_dir))

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
            "# make sure to be in the build dir",
            "cd {}".format(shlex.quote(build_dir)),
            "",
            "# create artifacts directory (called scripts shall put their build results into this directory)",
            "[ ! -d artifacts ] && mkdir artifacts",
            "",
            "# call pre-build script (if available)",
            "[ -f pre_build.sh ] && bash pre_build.sh",
            "",
            "# create AppDir so that tools which are sensitive to that won't complain",
            "mkdir -p AppDir",
            "",
        ])

        if self._is_null_builder(self._builder_name):
            get_logger().debug("skipping generation of entry for null builder as main builder in main script")
        else:
            # add entry for main builder
            # use subshell to set SHLVL properly, which makes output with -x prettier
            main_script_gen.add_lines([
                "# call script for main builder {}".format(self._builder_name),
                "(source {})".format(build_scripts[self._builder_name]),
            ])

            # handled that one already
            del build_scripts[self._builder_name]

        # generate commented entries for remaining script
        # it doesn't make very much sense to run additional builders, since they most likely create the same artifacts
        # and we don't want to overwrite previously built files in our artifacts directory
        # also, it's much cleaner to build with different builders in separate directory
        if build_scripts:
            main_script_gen.add_line(
                "# additional available builders (call appimagecraft with --builder <name> to switch)")

            for builder_name, script in build_scripts.items():

                if self._is_null_builder(builder_name):
                    get_logger().debug(
                        "skipping generation of entry for null builder as additional builder in main script"
                    )
                    continue

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

        appimage_script_path = os.path.join(build_dir, "build-appimage.sh")

        appimage_script_gen = AppImageBuildScriptGenerator(appimage_build_config)
        appimage_script_gen.build_file(appimage_script_path)

        # call AppImage build script
        main_script_gen.add_line("# build AppImage")
        main_script_gen.add_line("(source {})".format(shlex.quote(appimage_script_path)))

        # (re-)create script file
        main_script_gen.build_file()

        return main_script_path

    def generate_builder_scripts(self, build_dir: str) -> dict:
        build_config: dict = self._config["build"]

        # generate build configs for every
        builders_map = {
            "cmake": CMakeBuilder,
        }

        build_scripts = {}

        for builder_name in build_config.keys():
            # skip null builder
            if self._is_null_builder(builder_name):
                get_logger().debug("skipping generation of build script for null builder")
                continue

            try:
                builder = builders_map[builder_name](build_config[builder_name])
            except KeyError:
                self._logger.error("No builder named {} available, skipping".format(builder_name))
                continue
            else:
                script_filename = builder.generate_build_script(self._project_root_dir, build_dir)
                build_scripts[builder_name] = script_filename

        return build_scripts

    def generate_pre_post_build_scripts(self, build_dir: str):
        gen = PrePostBuildScriptsGenerator(self._config.get("scripts", None))
        gen.build_files(build_dir)

    def generate_all_scripts(self, build_dir) -> str:
        if build_dir is None:
            raise ValueError("build dir has not been set")

        self.generate_pre_post_build_scripts(build_dir)

        build_scripts = self.generate_builder_scripts(build_dir)

        main_script_path = self._generate_main_script(build_dir, build_scripts)

        # validate script(s), if possible
        if ShellCheckValidator.is_available():
            self._logger.debug("validating scripts with shellcheck")
            validator = ShellCheckValidator()

            validator.validate(main_script_path)

        else:
            self._logger.debug("shellcheck validator not available, skipping validation")

        return main_script_path

    @staticmethod
    def _is_null_builder(builder_name):
        return builder_name is None or builder_name.lower() == "null"
