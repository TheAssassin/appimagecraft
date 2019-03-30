class BuilderBase:
    def __init__(self):
        self._logger = None

    @staticmethod
    def from_dict(data: dict):
        raise NotImplementedError

    def generate_build_script(self, project_root_dir: str, build_dir: str) -> str:
        raise NotImplementedError

    # def build_project(self):
    #     raise NotImplementedError
