import os.path

from typing import List

from .bash_script import ProjectAwareBashScriptBuilder


class PrePostBuildScriptsGenerator:
    def __init__(self, scripts_config: dict = None):
        if scripts_config is None:
            scripts_config = dict()

        self._config = scripts_config

    def build_files(self, project_root_dir: str, build_dir: str):
        def write_build_script(path: str, lines: List[str]):
            gen = ProjectAwareBashScriptBuilder(path, project_root_dir, build_dir)
            gen.add_lines(lines)
            gen.build_file()

        stages = ["pre_build", "post_build"]

        # validate config
        invalid_stages = set(self._config.keys()) - set(stages)
        if invalid_stages:
            raise ValueError("Invalid script stage: {}".format(list(invalid_stages)[0]))

        for stage in stages:
            try:
                script_lines = self._config["{}".format(stage)]
            except KeyError:
                pass
            else:
                write_build_script(os.path.join(build_dir, "{}.sh".format(stage)), script_lines)
