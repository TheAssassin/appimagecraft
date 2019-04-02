from . import CommandBase
from ..generators import AllBuildScriptsGenerator
from .. import _logging


# Generates build scripts based on configuration
class GenerateScriptsCommand(CommandBase):
    def __init__(self, config: dict, project_root_dir: str, build_dir: str, builder_name: str):
        super().__init__(config, project_root_dir, build_dir, builder_name)

        self._logger = _logging.get_logger("genscripts")

    def set_build_dir(self, build_dir: str):
        self._build_dir = build_dir

    def _get_gen(self) -> AllBuildScriptsGenerator:
        gen = AllBuildScriptsGenerator(self._config, self._project_root_dir, self._builder_name)

        return gen

    def run(self):
        self._logger.info("Generating build scripts in {}".format(self._build_dir))

        gen = self._get_gen()

        gen.generate_all_scripts(self._build_dir)
