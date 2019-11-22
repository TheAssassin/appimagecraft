import os


class BuilderBase:
    def __init__(self, config: dict = None):
        self._logger = None

        self._builder_config = config if config is not None else {}

    # support for different source directories in the project root
    # use this if your project is in a subdirectory of the project root directory
    def _get_source_dir(self, project_root_dir):
        source_dir = self._builder_config.get("source_dir", None)

        if not source_dir:
            return project_root_dir

        if not os.path.isabs(source_dir):
            source_dir = os.path.join(project_root_dir, source_dir)

        return source_dir

    @staticmethod
    def from_dict(data: dict):
        raise NotImplementedError

    def generate_build_script(self, project_root_dir: str, build_dir: str) -> str:
        raise NotImplementedError

    # def build_project(self):
    #     raise NotImplementedError
