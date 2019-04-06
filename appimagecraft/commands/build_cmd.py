import glob
import os
import shutil
import subprocess
import sys

from . import CommandBase
from ..generators import AllBuildScriptsGenerator
from ..validators import ValidationError
from .. import _logging


class BuildCommand(CommandBase):
    def __init__(self, config: dict, project_root_dir: str, build_dir: str, builder_name: str):
        super().__init__(config, project_root_dir, build_dir, builder_name)

        self._logger = _logging.get_logger("build")

    def set_build_dir(self, build_dir: str):
        self._build_dir = build_dir

    def _get_gen(self) -> AllBuildScriptsGenerator:
        gen = AllBuildScriptsGenerator(self._config, self._project_root_dir, self._builder_name)

        return gen

    def run(self):
        try:
            self._logger.info("Generating build scripts in {}".format(self._build_dir))

            gen = self._get_gen()

            try:
                build_script = gen.generate_all_scripts(self._build_dir)
            except ValidationError:
                self._logger.critical("validation of shell scripts failed")
                sys.exit(1)

            self._logger.info("Calling main build script {}".format(build_script))

            subprocess.check_call([build_script])

            self._logger.info("Moving artifacts into project root directory")

            artifact_paths = glob.glob("{}/artifacts/*".format(self._build_dir))

            if not artifact_paths:
                self._logger.warning("Could not find any artifacts to move to project root dir")

            else:
                for path in artifact_paths:
                    # need to specify absolute destination path, otherwise move will raise and exception
                    dest = os.path.join(self._project_root_dir, os.path.basename(path))

                    self._logger.debug("Moving artifact {} to {}".format(path, dest))

                    shutil.move(path, dest)

        except subprocess.CalledProcessError as e:
            self._logger.critical("Build script returned non-zero exit status {}".format(e.returncode))

        except Exception as e:
            self._logger.exception(e)

        finally:
            self._logger.info("Cleaning up build directory")
            shutil.rmtree(self._build_dir)
