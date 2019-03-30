class CommandBase:
    def __init__(self, config: dict, project_root_dir: str, build_dir: str, builder_name: str):
        self._config = config
        self._project_root_dir = project_root_dir
        self._build_dir = build_dir
        self._builder_name = builder_name

    def run(self):
        raise NotImplementedError
