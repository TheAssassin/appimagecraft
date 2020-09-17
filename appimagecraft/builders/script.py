import os.path

from ..generators.bash_script import BashScriptGenerator
from . import BuilderBase
from .._logging import get_logger


class ScriptBuilder(BuilderBase):
    _script_filename = "build-script.sh"

    def __init__(self, config: dict = None):
        super().__init__(config)

        self._logger = get_logger("script_builder")

    @staticmethod
    def from_dict(data: dict):
        # TODO!
        raise NotImplementedError()

    def generate_build_script(self, project_root_dir: str, build_dir: str) -> str:
        script_path = os.path.join(build_dir, self.__class__._script_filename)

        generator = BashScriptGenerator(script_path)
        generator.add_lines(self._builder_config["commands"])
        generator.build_file()

        return os.path.basename(script_path)
